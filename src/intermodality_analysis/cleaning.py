# Copyright 2025 Lucas Javaudin
# SPDX-License-Identifier: MIT
import duckdb
import geopandas as gpd
import polars as pl

from intermodality_analysis.weighting import reweight

# Polars Expression to filter PT legs (inc. employer transport and reduced-mobility transport).
PT_LEGS_FILTER_EXPR = pl.element().struct.field("mode_group").eq(
    "public_transit"
) | pl.element().struct.field("mode").is_in(("employer_transport", "reduced_mobility_transport"))

# Modes to be considered as car.
CAR_MODES = (
    "car:driver",
    "car:passenger",
    "taxi",
    "VTC",
    "taxi_or_VTC",
    "truck:driver",
    "truck:passenger",
)

# Public-transit mode groups.
PT_MODE_GROUPS = {
    "public_transit:urban": "other",
    "public_transit:urban:bus": "bus",
    "public_transit:urban:coach": "coach",
    "public_transit:urban:tram": "tram",
    "public_transit:urban:metro": "metro",
    "public_transit:urban:funicular": "other",
    "public_transit:urban:rail": "train",
    "public_transit:urban:TER": "train",
    "public_transit:urban:demand_responsive": "other",
    "public_transit:interurban:coach": "coach",
    "public_transit:interurban:TGV": "train",
    "public_transit:interurban:intercités": "train",
    "public_transit:interurban:other_train": "train",
    "public_transit:school": "other",
    "reduced_mobility_transport": "other",
    "employer_transport": "other",
}

# Map public-transit mode (from MobiSurvStd) -> PT mode.
PT_MODE_MAP = {
    "public_transit:urban": None,
    "public_transit:urban:bus": "bus",
    "public_transit:urban:coach": "bus",
    "public_transit:urban:tram": "tram",
    "public_transit:urban:metro": "metro",
    "public_transit:urban:funicular": "funicular",
    "public_transit:urban:rail": "rail",
    "public_transit:urban:TER": "rail",
    "public_transit:urban:demand_responsive": None,
    "public_transit:interurban:coach": "bus",
    "public_transit:interurban:TGV": "rail",
    "public_transit:interurban:intercités": "rail",
    "public_transit:interurban:other_train": "rail",
    "public_transit:school": "bus",
    "reduced_mobility_transport": None,
    "employer_transport": None,
}


def general_cleaning(persons: pl.DataFrame, trips: pl.DataFrame):
    """General cleaning operations."""
    # Drop persons that were not surveyed for trips.
    persons = persons.filter("is_surveyed")
    # Drop persons with unknown weight (none).
    persons = persons.filter(pl.col("sample_weight_surveyed").is_not_null())
    # Drop persons with unknown age (only 6).
    persons = persons.filter(pl.col("age").is_not_null())
    # Drop persons with unknown gender (none).
    persons = persons.filter(pl.col("woman").is_not_null())
    # Drop persons with unknown home insee density (only 23).
    persons = persons.filter(pl.col("home_insee_density").is_not_null())
    # Drop persons with home density = 7 (very rural areas).
    persons = persons.filter(pl.col("home_insee_density") != 7)

    # Re-weight persons.
    persons = reweight(persons)

    # Drop trips with unknown modes (there should be only one).
    trips = trips.filter(pl.col("main_mode_group").is_not_null())
    # Drop trips with unknown distance (1434).
    trips = trips.filter(pl.col("trip_euclidean_distance_km").is_not_null())

    # Join the two DataFrames
    df = trips.join(persons, on=["person_id", "name"], how="inner", coalesce=True)
    return persons, df


def local_trips_cleaning(df):
    # Restrict to "local" trips (< 80 km).
    df = df.filter(pl.col("trip_euclidean_distance_km") < 80)
    return df


def modes_cleaning(df):
    # Remove trips with invalid modes.
    # These are mostly trips with mode "other" which we don't know what it represents.
    df = df.with_columns(
        has_invalid_mode=pl.col("leg_characs")
        .list.eval(
            pl.element().struct.field("mode").is_in(("airplane", "water_transport", "other"))
        )
        .list.any()
    )
    df = df.filter(pl.col("has_invalid_mode").not_())

    # Move "personal_transporter:*" and "wheelchair" modes to "walking".
    df = df.with_columns(
        nb_legs_personal_transporter=pl.col("leg_characs")
        .list.eval(
            pl.element()
            .struct.field("mode")
            .is_in(
                (
                    "personal_transporter:non_motorized",
                    "personal_transporter:motorized",
                    "personal_transporter:unspecified",
                )
            )
        )
        .list.sum(),
        nb_legs_wheelchair=pl.col("leg_characs")
        .list.eval(pl.element().struct.field("mode").eq("wheelchair"))
        .list.sum(),
    ).with_columns(
        nb_legs_walking=pl.col("nb_legs_walking")
        + pl.col("nb_legs_personal_transporter")
        + pl.col("nb_legs_wheelchair"),
        nb_legs_other=pl.col("nb_legs_other")
        - pl.col("nb_legs_personal_transporter")
        - pl.col("nb_legs_wheelchair"),
    )

    # Move "truck:*" modes to "car_driver" or "car_passenger".
    df = df.with_columns(
        nb_legs_truck_driver=pl.col("leg_characs")
        .list.eval(pl.element().struct.field("mode").eq("truck:driver"))
        .list.sum(),
        nb_legs_truck_passenger=pl.col("leg_characs")
        .list.eval(pl.element().struct.field("mode").eq("truck:passenger"))
        .list.sum(),
    ).with_columns(
        nb_legs_car_driver=pl.col("nb_legs_car_driver") + pl.col("nb_legs_truck_driver"),
        nb_legs_car_passenger=pl.col("nb_legs_car_passenger") + pl.col("nb_legs_truck_passenger"),
        nb_legs_other=pl.col("nb_legs_other")
        - pl.col("nb_legs_truck_driver")
        - pl.col("nb_legs_truck_passenger"),
    )

    # Move "employer_transport" and "reduced_mobility_transport" modes to "public_transit".
    df = df.with_columns(
        nb_legs_employer_transport=pl.col("leg_characs")
        .list.eval(pl.element().struct.field("mode").eq("employer_transport"))
        .list.sum(),
        nb_legs_reduced_mobility_transport=pl.col("leg_characs")
        .list.eval(pl.element().struct.field("mode").eq("reduced_mobility_transport"))
        .list.sum(),
    ).with_columns(
        nb_legs_public_transit=pl.col("nb_legs_public_transit")
        + pl.col("nb_legs_employer_transport")
        + pl.col("nb_legs_reduced_mobility_transport"),
        nb_legs_other=pl.col("nb_legs_other")
        - pl.col("nb_legs_employer_transport")
        - pl.col("nb_legs_reduced_mobility_transport"),
    )

    assert df["nb_legs_other"].eq(0).all()

    df = df.with_columns(
        # Recompute intermodality as it was invalidated with the previous changes.
        intermodality=(
            pl.col("nb_legs_public_transit").gt(0)
            + pl.col("nb_legs_car_driver").gt(0)
            + pl.col("nb_legs_car_passenger").gt(0)
            + pl.col("nb_legs_bicycle").gt(0)
            + pl.col("nb_legs_motorcycle").gt(0)
        )
        >= 2
    )
    return df


def intermodality_cleaning(df):
    """Add `intermodality_type` column representing the type of intermodality for intermodal trips."""
    df = df.with_columns(
        intermodality_type=pl.when(pl.col("intermodality").not_())
        .then(pl.lit(None))
        .when(
            pl.col("nb_legs")
            == pl.col("nb_legs_car_driver")
            + pl.col("nb_legs_public_transit")
            + pl.col("nb_legs_walking")
        )
        .then(pl.lit("pt+car_driver"))
        .when(
            pl.col("nb_legs")
            == pl.col("nb_legs_car_passenger")
            + pl.col("nb_legs_public_transit")
            + pl.col("nb_legs_walking")
        )
        .then(pl.lit("pt+car_passenger"))
        .when(
            pl.col("nb_legs")
            == pl.col("nb_legs_bicycle")
            + pl.col("nb_legs_public_transit")
            + pl.col("nb_legs_walking")
        )
        .then(pl.lit("pt+bicycle"))
        .when(
            pl.col("nb_legs")
            == pl.col("nb_legs_car_driver")
            + pl.col("nb_legs_car_passenger")
            + pl.col("nb_legs_walking")
        )
        .then(pl.lit("car_driver+car_passenger"))
        .otherwise(pl.lit("other"))
    )
    return df


def purpose_cleaning(df):
    """Add `from_or_to_home`, `purpose_pair` and `main_purpose` variables."""
    o = pl.col("origin_purpose_group")
    d = pl.col("destination_purpose_group")
    # `from_or_to_home` is True if either origin or destination is at home.
    df = df.with_columns(from_or_to_home=o.eq("home") | d.eq("home"))
    # `purpose_pair` is a String variable representing the origin / destination purpose pair.
    df = df.with_columns(
        purpose_pair=pl.when(pl.col("from_or_to_home").not_())
        .then(pl.lit("other"))
        .when(o.eq("work") | d.eq("work"))
        .then(pl.lit("home<->work"))
        .when(o.eq("education") | d.eq("education"))
        .then(pl.lit("home<->education"))
        .when(o.eq("shopping") | d.eq("shopping"))
        .then(pl.lit("home<->shopping"))
        .when(o.eq("task") | d.eq("task"))
        .then(pl.lit("home<->task"))
        .when(o.eq("leisure") | d.eq("leisure"))
        .then(pl.lit("home<->leisure"))
        .when(o.eq("escort") | d.eq("escort"))
        .then(pl.lit("home<->escort"))
        .when(o.eq("other") | d.eq("other"))
        .then(pl.lit("home<->other"))
    )
    # `main_purpose` is the most important purpose of the trip.
    # This is based on the hierarchy from C. Raux:
    # https://hal-lara.archives-ouvertes.fr/halshs-03109300/
    # Travail > Ecole > Accompagnement > Service > Achats > Loisirs.
    df = df.with_columns(
        main_purpose=pl.when(o.eq("work") | d.eq("work"))
        .then(pl.lit("work"))
        .when(o.eq("education") | d.eq("education"))
        .then(pl.lit("education"))
        .when(o.eq("escort") | d.eq("escort"))
        .then(pl.lit("escort"))
        .when(o.eq("task") | d.eq("task"))
        .then(pl.lit("task"))
        .when(o.eq("shopping") | d.eq("shopping"))
        .then(pl.lit("shopping"))
        .when(o.eq("leisure") | d.eq("leisure"))
        .then(pl.lit("leisure"))
        .otherwise(pl.lit("other")),
    )
    return df


def density_cleaning(df):
    """Add `home_cat`, `origin_cat` and `destination_cat` columns representing the INSEE density of
    the origin / destination municipality.

    The INSEE density has three modalities: rural, intermediate and dense.
    The dense category is here split between "2_dense_secondary" and "1_dense_main".
    Only municipalities which are AAV pole or secondary pole are in category "1_dense_main".
    """
    for prefix in ("home", "origin", "destination"):
        df = df.with_columns(
            pl.when(pl.col(f"{prefix}_insee_density").is_in((5, 6, 7)))
            .then(pl.lit("4_rural"))
            .when(pl.col(f"{prefix}_insee_density").is_in((2, 3, 4)))
            .then(pl.lit("3_intermediate"))
            .when(pl.col(f"{prefix}_insee_density") == 1)
            .then(
                pl.when(pl.col(f"{prefix}_insee_aav_type") == 11)
                .then(pl.lit("1_dense_main"))
                .when(pl.col(f"{prefix}_insee_aav_type").is_not_null())
                .then(pl.lit("2_dense_secondary"))
            )
            .alias(f"{prefix}_cat")
        )
    return df


def get_pt_car_trips(df):
    """Returns a DataFrame with only the PT+car trips (driver or passenger), with additional
    variables already computed.
    """
    # Select PT+car trips.
    pt_car_trips = df.filter(
        pl.col("intermodality_type").is_in(("pt+car_passenger", "pt+car_driver"))
    )
    # Shortcut for modes and mode groups.
    pt_car_trips = pt_car_trips.with_columns(
        modes=pl.col("leg_characs").list.eval(pl.element().struct.field("mode")),
        mode_groups=pl.col("leg_characs").list.eval(pl.element().struct.field("mode_group")),
    )
    # Identify whether the car trip is from / to home or from / to other location.
    non_walk_legs = pl.col("leg_characs").list.filter(
        pl.element().struct.field("mode_group").ne("walking")
    )
    pt_car_trips = pt_car_trips.with_columns(
        start_with_car=non_walk_legs.list.first().struct.field("mode").is_in(CAR_MODES),
        end_with_car=non_walk_legs.list.last().struct.field("mode").is_in(CAR_MODES),
    ).with_columns(
        car_from_to_home=pl.col("start_with_car").and_(pl.col("origin_purpose_group").eq("home"))
        | pl.col("end_with_car").and_(pl.col("destination_purpose_group").eq("home")),
        start_xor_end_with_car=pl.col("start_with_car") ^ pl.col("end_with_car"),
    )
    # Add some variables on the car / PT legs.
    pt_car_trips = pt_car_trips.with_columns(
        car_legs=pl.col("leg_characs").list.filter(
            pl.element().struct.field("mode").is_in(CAR_MODES)
        ),
        pt_legs=pl.col("leg_characs").list.filter(PT_LEGS_FILTER_EXPR),
    ).with_columns(
        nb_car_legs=pl.col("car_legs").list.len(),
        nb_pt_legs=pl.col("pt_legs").list.len(),
        first_car_type=pl.col("car_legs").list.first().struct.field("car_type"),
    )
    # Whether the trip has at least one car passenger leg.
    pt_car_trips = pt_car_trips.with_columns(
        is_passenger=pl.col("car_legs")
        .list.eval(
            pl.element()
            .struct.field("mode")
            .is_in(("car:passenger", "taxi", "VTC", "taxi_or_VTC", "truck:passenger"))
        )
        .list.all(),
    )
    # Identify how / where the car leg happens.
    # - "no_home_purpose": home is not a purpose at either origin or destination (so there is no
    #    logic to be expected for the car leg).
    # - "car_from_to_home": car is taken from home (at the start of the trip) or to home (at the end
    #   of the trip).
    # - "is_passenger": person is not a driver (so car can be taken not from / to home).
    # - "not_household_car": person is a driver but the car taken is not belonging to the household
    #   (e.g., a person that go near work with PT then finish the trip with employer car).
    # - "suspicious": car is not taken from / to home although it is a household car and the person
    #   is driving it.
    pt_car_trips = pt_car_trips.with_columns(
        type=pl.when(pl.col("from_or_to_home").not_())
        .then(pl.lit("no_home_purpose"))
        .when("car_from_to_home")
        .then(pl.lit("car_from_to_home"))
        .when("is_passenger")
        .then(pl.lit("is_passenger"))
        .when(pl.col("first_car_type").is_in(("household", "other_household")).not_())
        .then(pl.lit("not_household_car"))
        .otherwise(pl.lit("suspicious"))
    )
    # Add car distance and PT distance (dist is set to NULL when at least one leg has NULL dist).
    pt_car_trips = pt_car_trips.with_columns(
        pt_dists=pl.col("pt_legs").list.eval(
            pl.element().struct.field("leg_euclidean_distance_km")
        ),
        car_dists=pl.col("car_legs").list.eval(
            pl.element().struct.field("leg_euclidean_distance_km")
        ),
    ).with_columns(
        pt_dist=pl.when(pl.col("pt_dists").list.eval(pl.element().is_not_null()).list.all()).then(
            pl.col("pt_dists").list.sum()
        ),
        car_dist=pl.when(pl.col("car_dists").list.eval(pl.element().is_not_null()).list.all()).then(
            pl.col("car_dists").list.sum()
        ),
    )
    pt_car_trips = pt_car_trips.with_columns(
        first_pt_mode=pl.col("pt_legs")
        .list.first()
        .struct.field("mode")
        .replace_strict(PT_MODE_GROUPS),
        last_pt_mode=pl.col("pt_legs")
        .list.last()
        .struct.field("mode")
        .replace_strict(PT_MODE_GROUPS),
    ).with_columns(
        pt_entry_exit_mode=pl.when("start_with_car").then("first_pt_mode").otherwise("last_pt_mode")
    )
    return pt_car_trips


def get_all_pt_modes(df: pl.DataFrame):
    """Returns a DataFrame with the PT mode group and trip weight for all PT legs."""
    return (
        df.lazy()
        .with_columns(
            pt_modes=pl.col("leg_characs")
            .list.filter(PT_LEGS_FILTER_EXPR)
            .list.eval(pl.element().struct.field("mode"))
            .list.drop_nulls()
        )
        .filter(pl.col("pt_modes").list.len() > 0)
        .explode("pt_modes")
        .select(
            name="name",
            trip_id="trip_id",
            pt_mode_group=pl.col("pt_modes").replace_strict(PT_MODE_GROUPS),
            weight="sample_weight_surveyed",
        )
        .collect()
    )


def get_density_cats_matrix(df: pl.DataFrame, pt_car_trips: pl.DataFrame):
    """Returns a DataFrame of intermodality weight and share for each pair of density categories.

    Intermodality is here defined only as the car->PT trips."""
    inter = (
        pt_car_trips.filter(
            "start_with_car",
            pl.col("end_with_car").not_(),
            pl.col("origin_cat").is_not_null(),
            pl.col("destination_cat").is_not_null(),
        )
        .group_by("origin_cat", "destination_cat")
        .agg(car_then_pt_weight=pl.col("sample_weight_surveyed").sum())
    )
    uni = (
        df.filter(pl.col("origin_cat").is_not_null(), pl.col("destination_cat").is_not_null())
        .group_by("origin_cat", "destination_cat")
        .agg(
            total_weight=pl.col("sample_weight_surveyed").sum(),
        )
    )
    cat_matrix = (
        inter.join(uni, on=["origin_cat", "destination_cat"], how="full", coalesce=True)
        .with_columns(
            car_then_pt_weight=pl.col("car_then_pt_weight").fill_null(0.0),
            global_share=pl.col("car_then_pt_weight") / pl.col("car_then_pt_weight").sum(),
        )
        .with_columns(car_then_pt_share=pl.col("car_then_pt_weight") / pl.col("total_weight"))
        .sort("origin_cat", "destination_cat")
    )
    return cat_matrix


def get_origin_access_pairs(pt_car_trips: pl.DataFrame, detailed_zones: gpd.GeoDataFrame):
    valid_trips = pt_car_trips.filter(
        "start_with_car",
        pl.col("end_with_car").not_(),
        pl.col("nb_legs_car_driver") == 1,
        origin_purpose_group="home",
        intermodality_type="pt+car_driver",
    )
    valid_trips = (
        valid_trips.with_columns(
            first_pt_leg=pl.col("leg_characs").list.filter(PT_LEGS_FILTER_EXPR).list.first()
        )
        .with_columns(
            access_mode=pl.col("first_pt_leg").struct.field("mode").replace_strict(PT_MODE_MAP),
            access_detailed_zone=pl.col("first_pt_leg").struct.field("start_detailed_zone"),
            access_lng=pl.col("first_pt_leg").struct.field("start_lng"),
            access_lat=pl.col("first_pt_leg").struct.field("start_lat"),
        )
        .filter(pl.col("access_mode").is_in(("tram", "metro", "rail")))
        .with_row_index()
    )

    cerema_pairs = (
        valid_trips.filter(pl.col("name").is_in(("EGT2010", "EGT2020")).not_())
        .select(
            "index",
            "name",
            "origin_detailed_zone",
            "access_detailed_zone",
            "access_mode",
            "sample_weight_surveyed",
        )
        .drop_nulls()
    )
    egt_pairs = (
        valid_trips.filter(pl.col("name").is_in(("EGT2010", "EGT2020")))
        .select(
            "index",
            "name",
            "origin_lng",
            "origin_lat",
            "access_lng",
            "access_lat",
            "access_mode",
            "sample_weight_surveyed",
        )
        .drop_nulls()
    )

    # Find origin / access detailed zone of the CEREMA trips.
    cerema_pairs = cerema_pairs.join(
        detailed_zones,
        left_on=["name", "origin_detailed_zone"],
        right_on=["name", "detailed_zone_id"],
        how="left",
    ).rename({"binary_geom": "origin_geom"})
    cerema_pairs = cerema_pairs.join(
        detailed_zones,
        left_on=["name", "access_detailed_zone"],
        right_on=["name", "detailed_zone_id"],
        how="left",
    ).rename({"binary_geom": "access_geom"})

    n0 = len(cerema_pairs)
    cerema_pairs = cerema_pairs.drop_nulls()
    n1 = len(cerema_pairs)
    if n1 < n0:
        print(f"Origin / access zone cannot be read for {n0 - n1:,} CEREMA trips")

    # Create origin / access zones for EGT trips.
    egt_geoms = duckdb.sql("""
        SELECT
            index,
            ST_AsWKB(ST_Buffer(
                ST_Transform(ST_Point(origin_lng, origin_lat), 'EPSG:4326', 'EPSG:2154', TRUE),
                50.0,
                0,
                'CAP_SQUARE',
                'JOIN_MITRE',
                1.0
            )) AS origin_geom,
            ST_AsWKB(ST_Buffer(
                ST_Transform(ST_Point(access_lng, access_lat), 'EPSG:4326', 'EPSG:2154', TRUE),
                50.0,
                0,
                'CAP_SQUARE',
                'JOIN_MITRE',
                1.0
            )) AS access_geom,
        FROM egt_pairs
    """).pl()
    egt_pairs = egt_pairs.join(egt_geoms, on="index")

    # Merge pairs.
    columns = [
        "index",
        "name",
        "access_mode",
        "sample_weight_surveyed",
        "origin_geom",
        "access_geom",
    ]
    pairs = pl.concat((cerema_pairs.select(columns), egt_pairs.select(columns)), how="vertical")
    return pairs
