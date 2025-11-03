import json
import os
from collections import defaultdict

import duckdb
import polars as pl

from intermodality_analysis.cleaning import (
    density_cleaning,
    general_cleaning,
    get_all_pt_modes,
    get_density_cats_matrix,
    get_origin_access_pairs,
    get_pt_car_trips,
    intermodality_cleaning,
    local_trips_cleaning,
    modes_cleaning,
    purpose_cleaning,
)
from intermodality_analysis.graphs import (
    density_flows_polar_plot,
    euclidean_distance_densities,
    intermodality_types_bars,
    pt_entry_exit_modes_bars,
    purposes_bar_chart,
    ratio_pt_car_dist_density,
)
from intermodality_analysis.input import (
    read_all_detailed_zones,
    read_all_persons,
    read_all_trips,
)
from intermodality_analysis.mpl import GRAPH_DIR
from intermodality_analysis.stats import (
    UNIMODAL_NON_WALK_TRIPS_EXPR,
    get_cat_matrix_stats,
    get_density_cats_stats,
    get_entry_exit_mode_stats,
    get_nb_transfers_stats,
    get_origin_access_stats,
    get_pt_car_distance_stats,
    get_pt_legs_mode_stats,
    get_purposes_stats,
    get_trips_stats,
    get_trips_stats_by_intermodality_type,
    get_trips_stats_by_intermodality_type_for_groups,
)

duckdb.install_extension("spatial")
duckdb.load_extension("spatial")

# Dictionary to hold all the script results that will be outputed as JSON at the end.
RESULTS = defaultdict(lambda: dict())

# Directory where the standardized surveys are located.
INPUT_DIR = "../MobiSurvStd/output/all/"

# Filename where the result numbers should be stored.
OUTPUT_FILE = "./output/results.json"

# Filename where the French PT stops data are stored.
STOPS_FILENAME = "./data/all_stops.parquet"

# Labels of the socio-professional categories.
PCS_LABELS = {
    1: "Agriculteur",
    2: "Artisan",
    3: "Cadre",
    4: "Prof. interm.",
    5: "Employé",
    6: "Ouvrier",
}

# Map GTFS route type -> PT mode.
STOP_MODES_MAP = {
    "bus": "bus",
    "rail": "rail",
    "regional_coach": "bus",
    "tram": "tram",
    "school_bus": "bus",
    "coach_service": "bus",
    "bus_service": "bus",
    "demand_and_response_bus": "bus",
    "metro": "metro",
    "ferry": "ferry",
    "trolleybus": "bus",
    "funicular": "funicular",
    "aerial_lift": "funicular",
    "express_bus": "bus",
    "railway_service": "rail",
    "air_service": "funicular",
    "cable_tram": "tram",
}

if __name__ == "__main__":
    print("Reading surveyed households and persons")
    persons = read_all_persons(INPUT_DIR)
    nb_households = len(persons.select("household_id", "name").unique())
    nb_persons = len(persons.select("person_id", "name").unique())
    print("Reading survey trips and legs")
    trips = read_all_trips(INPUT_DIR)

    RESULTS["nb_surveys"] = persons["name"].n_unique()
    RESULTS["min_year"] = trips["trip_date"].min().year
    RESULTS["max_year"] = trips["trip_date"].max().year
    survey_types = persons.select("name", "survey_type").unique()["survey_type"].value_counts()
    RESULTS["nb_surveys_egt"] = survey_types.filter(pl.col("survey_type").str.starts_with("EGT"))[
        "count"
    ].sum()
    RESULTS["nb_surveys_cerema"] = survey_types.filter(
        pl.col("survey_type").is_in(("EMC2", "EMD", "EDGT", "EDVM"))
    )["count"].sum()

    counts = {
        "nb_households": nb_households,
        "nb_persons": nb_persons,
        "nb_trips": len(trips),
        "nb_legs": trips["leg_characs"].list.len().sum(),
    }
    RESULTS["global"]["raw_counts"] = counts

    print("General cleaning")
    df = general_cleaning(persons, trips)

    counts = {
        "nb_trips": len(df),
        "nb_legs": df["leg_characs"].list.len().sum(),
        "trip_dist": df["trip_euclidean_distance_km"].sum(),
    }
    RESULTS["global"]["cleaned_counts"] = counts

    print("Density cleaning")
    df = density_cleaning(df)

    print("Local trips cleaning")
    df = local_trips_cleaning(df)

    counts = {
        "nb_trips": len(df),
        "nb_legs": df["leg_characs"].list.len().sum(),
        "trip_dist": df["trip_euclidean_distance_km"].sum(),
    }
    RESULTS["global"]["local_trips_counts"] = counts

    print("Modes cleaning")
    df = modes_cleaning(df)

    counts = {
        "nb_trips": len(df),
        "nb_legs": df["leg_characs"].list.len().sum(),
        "trip_dist": df["trip_euclidean_distance_km"].sum(),
        "mean_dist": df.select(
            pl.col("trip_euclidean_distance_km")
            * pl.col("sample_weight_surveyed")
            / pl.col("sample_weight_surveyed").sum()
        )
        .to_series()
        .sum(),
    }
    RESULTS["global"]["final_counts"] = counts

    print("Intermodality cleaning")
    df = intermodality_cleaning(df)
    print("Purposes cleaning")
    df = purpose_cleaning(df)

    print("Computing trips' stats")
    # Add some statistics on the intermodality trips.
    RESULTS["stats"]["intermodal_trips"] = get_trips_stats(df, pl.col("intermodality"))
    # Add some statistics on the unimodal trips.
    RESULTS["stats"]["unimodal_trips"] = get_trips_stats(df, pl.col("intermodality").not_())
    # Add some statistics on the unimodal trips (excluding walking).
    RESULTS["stats"]["unimodal_trips_no_walk"] = get_trips_stats(df, UNIMODAL_NON_WALK_TRIPS_EXPR)
    # Add some statistics on the unimodal trips (excluding walking).
    RESULTS["stats"]["intermodal_trips_dist_gt_20"] = get_trips_stats(
        df.filter(pl.col("trip_euclidean_distance_km") > 20), pl.col("intermodality")
    )

    print("Graph: Euclidean distance densities")
    euclidean_distance_densities(
        unimodal_dists=df.filter(
            UNIMODAL_NON_WALK_TRIPS_EXPR, pl.col("trip_euclidean_distance_km") > 0
        )["trip_euclidean_distance_km"],
        unimodal_weights=df.filter(
            UNIMODAL_NON_WALK_TRIPS_EXPR, pl.col("trip_euclidean_distance_km") > 0
        )["sample_weight_surveyed"],
        intermodal_dists=df.filter("intermodality", pl.col("trip_euclidean_distance_km") > 0)[
            "trip_euclidean_distance_km"
        ],
        intermodal_weights=df.filter("intermodality", pl.col("trip_euclidean_distance_km") > 0)[
            "sample_weight_surveyed"
        ],
        filename=os.path.join(GRAPH_DIR, "euclidean_dist_densities"),
        max_dist=30,
        bw_factor=0.03,
    )

    print("Computing purposes stats")
    # Add some statistics on trip purposes.
    RESULTS["purposes"]["intermodal_trips"] = get_purposes_stats(df, pl.col("intermodality"))
    RESULTS["purposes"]["unimodal_trips_no_walk"] = get_purposes_stats(
        df, UNIMODAL_NON_WALK_TRIPS_EXPR
    )

    print("Graph: Purposes bar chart")
    purposes_bar_chart(RESULTS["purposes"], os.path.join(GRAPH_DIR, "purposes_bars"))

    print("Computing stats by intermodality type")
    # Build a DataFrame with statistics for each intermodality type.
    nb_trips = len(df)
    tot_weight = df["sample_weight_surveyed"].sum()
    tot_weighted_dist = (
        df.select(pl.col("sample_weight_surveyed") * pl.col("trip_euclidean_distance_km"))
        .to_series()
        .sum()
    )
    types = (
        df.filter("intermodality")
        .group_by("intermodality_type")
        .agg(
            nb_trips=pl.len(),
            weighted_nb_trips=pl.col("sample_weight_surveyed").sum(),
            weighted_dist=(
                pl.col("trip_euclidean_distance_km") * pl.col("sample_weight_surveyed")
            ).sum(),
        )
        .with_columns(
            mean_dist=pl.col("weighted_dist") / pl.col("weighted_nb_trips"),
            share_trips=pl.col("nb_trips") / pl.col("nb_trips").sum(),
            share_trips_all=pl.col("nb_trips") / nb_trips,
            share_weighted_trips=pl.col("weighted_nb_trips") / pl.col("weighted_nb_trips").sum(),
            share_weighted_trips_all=pl.col("weighted_nb_trips") / tot_weight,
            share_weighted_dist=pl.col("weighted_dist") / pl.col("weighted_dist").sum(),
            share_weighted_dist_all=pl.col("weighted_dist") / tot_weighted_dist,
        )
        .sort("weighted_nb_trips")
    )
    RESULTS["intermodality-types"] = types.rows_by_key(
        "intermodality_type", named=True, unique=True
    )

    print("Graph: Intermodality type bars")
    intermodality_types_bars(
        RESULTS["intermodality-types"], os.path.join(GRAPH_DIR, "intermodality_types_bars")
    )

    print("Computing person-level stats")
    RESULTS["person_characs"]["professional_occupation"] = (
        get_trips_stats_by_intermodality_type_for_groups(
            df.filter(pl.col("professional_occupation").is_not_null()), "professional_occupation"
        )
    )
    RESULTS["person_characs"]["pcs_group_code"] = get_trips_stats_by_intermodality_type_for_groups(
        df.filter(pl.col("pcs_group_code").is_not_null()), "pcs_group_code"
    )
    RESULTS["person_characs"]["no_license"] = get_trips_stats_by_intermodality_type(
        df.filter(pl.col("has_driving_license").is_not_null()),
        pl.col("has_driving_license").eq("no"),
    )
    RESULTS["person_characs"]["woman"] = get_trips_stats_by_intermodality_type(
        df.filter(pl.col("woman").is_not_null()), pl.col("woman")
    )
    RESULTS["person_characs"]["student_or_no_license"] = get_trips_stats_by_intermodality_type(
        df.filter(
            pl.col("professional_occupation").is_not_null(),
            pl.col("has_driving_license").is_not_null(),
        ),
        pl.col("professional_occupation").eq("student") | pl.col("has_driving_license").ne("yes"),
    )

    print("Cleaning PT+car trips")
    pt_car_trips = get_pt_car_trips(df)

    print("Computing distance stats")
    RESULTS["pt_car_trips"]["distances"] = get_pt_car_distance_stats(pt_car_trips)

    print("Graph: PT / car dist ratio density")
    values = pt_car_trips.filter(
        pl.col("pt_dist").is_not_null(),
        pl.col("car_dist").is_not_null(),
        (pl.col("pt_dist") > 0) | (pl.col("car_dist") > 0),
    ).select(
        ratio=pl.col("pt_dist") / (pl.col("pt_dist") + pl.col("car_dist")),
        weight="sample_weight_surveyed",
    )
    ratio_pt_car_dist_density(
        values["ratio"], values["weight"], os.path.join(GRAPH_DIR, "pt_dist_ratio_density")
    )

    print("Computing stats on entry / exit modes")
    RESULTS["pt_car_trips"]["entry_exit_mode"] = get_entry_exit_mode_stats(pt_car_trips)

    print("Computing stats on number of transfers")
    RESULTS["pt_car_trips"]["nb_transfers"] = get_nb_transfers_stats(pt_car_trips)

    print("Graph: entry / exit PT modes bars")
    pt_entry_exit_modes_bars(
        RESULTS["pt_car_trips"]["entry_exit_mode"], os.path.join(GRAPH_DIR, "pt_modes_bars")
    )

    print("Cleaning all PT legs")
    pt_legs_mode = get_all_pt_modes(df)

    print("Computing stats on all PT legs")
    RESULTS["pt_legs"]["modes"] = get_pt_legs_mode_stats(pt_legs_mode)

    cat_matrix = get_density_cats_matrix(df, pt_car_trips)

    RESULTS["origin_destination_density"] = get_density_cats_stats(cat_matrix)
    RESULTS["origin_destination_density"]["matrix"] = get_cat_matrix_stats(cat_matrix)

    density_flows_polar_plot(cat_matrix, os.path.join(GRAPH_DIR, "insee_density_flows_polar"))

    print("Reading detailed zones")
    detailed_zones = read_all_detailed_zones(INPUT_DIR)

    print("Generating origin->access pairs")
    pairs = get_origin_access_pairs(pt_car_trips, detailed_zones)

    RESULTS["origin_access_nearest"] = get_origin_access_stats(pairs, STOPS_FILENAME)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(RESULTS, f, indent=2)

# v = (
#     pt_car_trips.filter(pl.col("type").ne("no_home_purpose"))
#     .select(
#         pl.col("sample_weight_surveyed").filter(pl.col("type").eq("car_from_to_home")).sum()
#         / pl.col("sample_weight_surveyed").sum()
#     )
#     .item()
# )
# print(f"Car is taken from / to home in {v:.2%} of car + pt trips when home is a purpose")

# # Type of bicycle intermodal trips : shared bike, in vehicle, stationned near station.
# bicycle_trips = df.filter(intermodality_type="pt+bicycle")
# bicycle_trips = bicycle_trips.with_columns(
#     has_walking=pl.col("leg_characs")
#     .list.eval(pl.element().struct.field("mode").eq("walking"))
#     .list.any(),
#     has_shared_bicycle=pl.col("leg_characs")
#     .list.eval(pl.element().struct.field("mode").cast(pl.String).str.contains("bicycle.*shared"))
#     .list.any(),
#     start_with_walking=pl.col("leg_characs").list.first().struct.field("mode").eq("walking"),
#     end_with_walking=pl.col("leg_characs").list.last().struct.field("mode").eq("walking"),
# ).with_columns(
#     bicycle_type=pl.when("has_shared_bicycle")
#     .then(pl.lit("shared"))
#     # .when("has_walking", "start_with_walking", "end_with_walking", nb_legs_bicycle=1)
#     # .then(pl.lit("shared"))
#     .when("has_walking", nb_legs_bicycle=1)
#     .then(pl.lit("stationned"))
#     .when(pl.col("nb_legs_bicycle") > 1)
#     .then(pl.lit("in_vehicle"))
#     .otherwise(pl.lit("stationned"))
# )
# bicycle_types = (
#     bicycle_trips.filter(pl.col("name") != "EMP2019")
#     .group_by("bicycle_type")
#     .agg(w=pl.col("sample_weight_surveyed").sum())
#     .with_columns(share=pl.col("w") / pl.col("w").sum())
# )


# Is the passenger being escorted for car_passenger + pt?

# Is the car driver alone for car_driver + pt?

# Car passenger can be taxi (how many?)

# Is there a trip back and forth? -> In majority yes for drivers, no for passengers.
