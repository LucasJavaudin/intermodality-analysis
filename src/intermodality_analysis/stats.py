import duckdb
import polars as pl

# Polars Expression to filter non-walking unimodal trips (excluding personal transporter and
# wheelchair).
UNIMODAL_NON_WALK_TRIPS_EXPR = pl.col("intermodality").not_() & pl.col("nb_legs").gt(
    pl.col("nb_legs_walking")
)


def get_trips_stats(df: pl.DataFrame, mask: pl.Expr) -> dict:
    """Returns a dictionary with some statistics on the number of trips and trips' distance in the
    given DataFrame, for the given mark.
    """
    x = df.filter(mask).select(
        pl.len(),
        w=pl.col("sample_weight_surveyed").sum(),
        wdist=(pl.col("trip_euclidean_distance_km") * pl.col("sample_weight_surveyed")).sum(),
    )
    n = x["len"].item()
    weight = x["w"].item()
    weighted_dist = x["wdist"].item()
    totweight = df["sample_weight_surveyed"].sum()
    tot_weighted_dist = (
        df.select(pl.col("trip_euclidean_distance_km") * pl.col("sample_weight_surveyed"))
        .to_series()
        .sum()
    )
    results = dict()
    results["nb_trips"] = n
    results["share_trips"] = n / len(df)
    results["weighted_nb_trips"] = weight
    results["share_weighted_trips"] = weight / totweight
    results["weighted_dist"] = weighted_dist
    results["share_weighted_dist"] = weighted_dist / tot_weighted_dist
    results["mean_dist"] = weighted_dist / weight
    return results


def get_trips_stats_by_intermodality_type(df: pl.DataFrame, cond: pl.Expr) -> dict:
    """Returns a dictionary with, for each intermodality type, some statistics on the number of
    trips and trips' distance where the condition `cond` is True.
    """
    results = get_trips_stats_by_intermodality_type_impl(df.filter("intermodality"), cond)
    results.update(
        {"unimodal_trips_no_walk": get_trips_stats(df.filter(UNIMODAL_NON_WALK_TRIPS_EXPR), cond)}
    )
    return results


def get_trips_stats_by_intermodality_type_impl(df: pl.DataFrame, cond: pl.Expr) -> dict:
    """Returns a dictionary with, for each intermodality type, some statistics on the number of
    trips and trips' distance where the condition `cond` is True.
    """
    x = (
        df.group_by("intermodality_type")
        .agg(
            nb_trips=cond.sum(),
            weighted_nb_trips=pl.col("sample_weight_surveyed").filter(cond).sum(),
            weighted_dist=pl.col("sample_weight_surveyed").filter(cond).sum(),
            tot_nb_trips=pl.len(),
            totweight=pl.col("sample_weight_surveyed").sum(),
            tot_weighted_dist=(
                pl.col("trip_euclidean_distance_km") * pl.col("sample_weight_surveyed")
            ).sum(),
        )
        .select(
            "intermodality_type",
            "nb_trips",
            "weighted_nb_trips",
            "weighted_dist",
            share_trips=pl.col("nb_trips") / pl.col("tot_nb_trips"),
            share_weighted_trips=pl.col("weighted_nb_trips") / pl.col("totweight"),
            share_weighted_dist=pl.col("weighted_dist") / pl.col("tot_weighted_dist"),
            mean_dist=(pl.col("weighted_dist") / pl.col("weighted_nb_trips")).fill_nan(0.0),
        )
    )
    return x.rows_by_key("intermodality_type", named=True, unique=True)


def get_trips_stats_by_intermodality_type_for_groups(df: pl.DataFrame, var: str) -> dict:
    """Returns a dictionary with, for each modality of the given variable and for each intermodality
    type, some statistics on the number of trips and trips' distance.
    """
    results = dict()
    for modality in df[var].unique().sort():
        results[modality] = get_trips_stats_by_intermodality_type_impl(
            df.filter("intermodality"), pl.col(var) == modality
        )
        results[modality].update(
            {
                "unimodal_trips_no_walk": get_trips_stats(
                    df.filter(UNIMODAL_NON_WALK_TRIPS_EXPR), pl.col(var) == modality
                )
            }
        )
    return results


def get_purposes_stats(df: pl.DataFrame, mask: pl.Expr) -> dict:
    """Returns a dictionary of dictionary with some statistics on the trips for each purpose."""
    x = (
        df.lazy()
        .filter(mask)
        .group_by("main_purpose")
        .agg(
            nb_trips=pl.len(),
            weighted_nb_trips=pl.col("sample_weight_surveyed").sum(),
            weighted_dist=(
                pl.col("sample_weight_surveyed") * pl.col("trip_euclidean_distance_km")
            ).sum(),
        )
        .with_columns(
            share_weighted_trips=pl.col("weighted_nb_trips") / pl.col("weighted_nb_trips").sum(),
            share_weighted_dist=pl.col("weighted_dist") / pl.col("weighted_dist").sum(),
        )
        .sort("main_purpose")
        .collect()
    )
    return x.rows_by_key("main_purpose", named=True, unique=True)


def get_pt_car_distance_stats(df: pl.DataFrame) -> dict:
    """Returns stats of the trips / legs distances for PT+car trips."""
    df = df.filter(pl.col("pt_dist").is_not_null(), pl.col("car_dist").is_not_null())
    results = dict()
    results["mean_pt_dist"] = (
        df.select(pl.col("sample_weight_surveyed") * pl.col("pt_dist")).to_series().sum()
        / df["sample_weight_surveyed"].sum()
    )
    results["mean_car_dist"] = (
        df.select(pl.col("sample_weight_surveyed") * pl.col("car_dist")).to_series().sum()
        / df["sample_weight_surveyed"].sum()
    )
    return results


def get_entry_exit_mode_stats(df: pl.DataFrame):
    """Returns stats of the entry / exit modes used for car - PT correspondance."""
    x = (
        df.group_by("pt_entry_exit_mode")
        .agg(nb_trips=pl.len(), weighted_nb_trips=pl.col("sample_weight_surveyed").sum())
        .with_columns(
            share=pl.col("nb_trips") / len(df),
            share_weighted_trips=pl.col("weighted_nb_trips") / df["sample_weight_surveyed"].sum(),
        )
    )
    return x.rows_by_key("pt_entry_exit_mode", named=True, unique=True)


def get_pt_legs_mode_stats(df: pl.DataFrame) -> dict:
    """Returns stats on the share of legs for each PT mode (over all PT legs)."""
    x = (
        df.group_by("pt_mode_group")
        .agg(weighted_nb_legs=pl.col("weight").sum())
        .with_columns(
            share_weighted_legs=pl.col("weighted_nb_legs") / pl.col("weighted_nb_legs").sum()
        )
        .sort("share_weighted_legs")
    )
    return x.rows_by_key("pt_mode_group", named=True, unique=True)


def get_nb_transfers_stats(df: pl.DataFrame) -> dict:
    """Returns stats on the number of transfers for PT + car trips."""
    x = (
        df.group_by(nb_transfers=pl.col("nb_pt_legs") - 1)
        .agg(nb_trips=pl.len(), weighted_nb_trips=pl.col("sample_weight_surveyed").sum())
        .with_columns(
            share=pl.col("nb_trips") / pl.col("nb_trips").sum(),
            share_weighted_trips=pl.col("weighted_nb_trips") / pl.col("weighted_nb_trips").sum(),
        )
        .sort("nb_transfers")
    )
    return x.rows_by_key("nb_transfers", named=True, unique=True)


def get_density_cats_stats(df: pl.DataFrame) -> dict:
    """Returns stats on the number of trips and share of trips for each origin density category and
    each destination density category.
    """
    results = dict()
    results["origin_density"] = (
        df.group_by("origin_cat")
        .agg(car_then_pt_weighted_nb_trips=pl.col("car_then_pt_weight").sum())
        .with_columns(
            share_weighted=pl.col("car_then_pt_weighted_nb_trips")
            / pl.col("car_then_pt_weighted_nb_trips").sum()
        )
        .rows_by_key("origin_cat", named=True, unique=True)
    )
    results["destination_density"] = (
        df.group_by("destination_cat")
        .agg(car_then_pt_weighted_nb_trips=pl.col("car_then_pt_weight").sum())
        .with_columns(
            share_weighted=pl.col("car_then_pt_weighted_nb_trips")
            / pl.col("car_then_pt_weighted_nb_trips").sum()
        )
        .rows_by_key("destination_cat", named=True, unique=True)
    )
    return results


def get_cat_matrix_stats(df: pl.DataFrame) -> dict:
    """Returns stats on the number of car->PT trips and share of car->PT trips for each origin /
    destination density category pairs.
    """
    return dict(
        map(
            lambda i: (i[0][0], i[1].rows_by_key("destination_cat", named=True, unique=True)),
            df.partition_by("origin_cat", include_key=False, as_dict=True).items(),
        )
    )


def get_origin_access_stats(pairs: pl.DataFrame, stops_filename: str):
    results = dict()
    for mode in ("metro", "tram", "rail"):
        print(f"Mode: {mode}")
        results[mode] = dict()
        mode_pairs = pairs.filter(access_mode=mode)
        results[mode]["nb_trips"] = len(mode_pairs)
        # Get stop geometries by mode.
        stops = duckdb.sql(f"""
            WITH stops AS (
                SELECT
                    slug,
                    stop_name,
                    ST_Transform(geometry, 'EPSG:4326', 'EPSG:2154', TRUE) AS stop_point
                FROM read_parquet('{stops_filename}')
                WHERE (
                    NOT ST_IsEmpty(stop_point)
                    AND ST_IsValid(stop_point)
                    AND list_contains(modes, '{mode}')
                )
            )
            SELECT slug, stop_name, ST_AsWKB(stop_point) AS stop_point FROM stops
        """).pl()
        results[mode]["nb_stops"] = len(stops)
        # Check whether the access zone contains a valid stop (within x meters).
        access_stops = duckdb.sql("""
            SELECT index, stop_name, stop_point
            FROM mode_pairs
            JOIN stops
            ON ST_DWithin(ST_GeomFromWKB(access_geom), ST_GeomFromWKB(stop_point), 50.0)
        """).pl()
        n = access_stops["index"].n_unique()
        results[mode]["nb_valid_access_zones"] = n
        results[mode]["mean_nb_valid_stops_by_access_zone"] = len(access_stops) / n
        mode_pairs = mode_pairs.filter(pl.col("index").is_in(access_stops["index"].implode()))
        global_dists = duckdb.sql("""
            SELECT
                index,
                MIN(ST_Distance(ST_Centroid(ST_GeomFromWKB(origin_geom)), ST_GeomFromWKB(stop_point))) AS min_global_dist_centroid
            FROM mode_pairs
            CROSS JOIN stops
            GROUP BY index
        """).pl()
        access_dists = duckdb.sql("""
            SELECT
                index,
                MIN(ST_Distance(ST_Centroid(ST_GeomFromWKB(origin_geom)), ST_GeomFromWKB(stop_point))) AS min_access_dist_centroid
            FROM mode_pairs
            JOIN stops
            ON ST_DWithin(ST_GeomFromWKB(access_geom), ST_GeomFromWKB(stop_point), 50.0)
            GROUP BY index
        """).pl()
        dists = global_dists.join(access_dists, on="index").with_columns(
            detour_ratio=pl.col("min_access_dist_centroid") / pl.col("min_global_dist_centroid")
        )
        v = dists["detour_ratio"].mean() - 1.0
        results[mode]["mean_detour"] = v
        v = (dists["detour_ratio"] < 1.1).mean()
        results[mode]["share_trips_detour_lt_10pt"] = v

        # Get all vertices coords for each origin zone.
        vertices = duckdb.sql("""
            WITH origins AS (
                SELECT
                    index,
                    UNNEST(ST_Dump(ST_Points(ST_GeomFromWKB(origin_geom)))) AS vertice
                FROM mode_pairs
            )
            SELECT index, vertice.path[1] AS k, ST_AsWKB(vertice.geom) AS vertice
            FROM origins
        """).pl()
        # For each vertice, compute distance to nearest valid access stop.
        vert_access_dists = duckdb.sql("""
            SELECT
                v.index,
                k,
                MIN(ST_Distance(ST_GeomFromWKB(vertice), ST_GeomFromWKB(stop_point))) AS min_access_dist
            FROM vertices v
            JOIN access_stops s
            ON v.index = s.index
            GROUP BY v.index, k
        """).pl()
        # For each vertice, compute the distance to the nearest valid stop (not within access zone).
        thresholds = vert_access_dists.group_by("index").agg(pl.col("min_access_dist").max())
        vert_global_dists = duckdb.sql("""
            WITH v AS (
                SELECT index, k, ST_GeomFromWKB(vertice) AS vertice FROM vertices
            ),
            s AS (
                SELECT ST_GeomFromWKB(stop_point) AS stop_point FROM stops
            )
            SELECT
                v.index,
                k,
                MIN(ST_Distance(vertice, stop_point)) AS min_stop_dist
            FROM v
            JOIN thresholds t
            ON v.index = t.index
            JOIN s
            ON ST_DWithin(vertice, stop_point, t.min_access_dist)
            GROUP BY v.index, k
        """).pl()
        res = (
            vert_access_dists.join(vert_global_dists, on=["index", "k"])
            .group_by("index")
            .agg(
                valid_possible=(pl.col("min_access_dist") <= pl.col("min_stop_dist") + 50).any(),
                valid_certain=(pl.col("min_access_dist") <= pl.col("min_stop_dist") + 50).all(),
            )
        )
        v1 = 1.0 - res["valid_possible"].mean()
        results[mode]["share_certainly_not_valid_trips"] = v1
        v2 = res["valid_certain"].mean()
        results[mode]["share_certainly_valid_trips"] = v2
        results[mode]["share_possibly_valid_trips"] = 1.0 - v1 - v2
    return results

    # myid = 2646
    # pair = pairs.filter(index=myid)
    # origin = gpd.GeoSeries.from_wkb(pair["origin_geom"], crs="EPSG:2154")
    # access = gpd.GeoSeries.from_wkb(pair["access_geom"], crs="EPSG:2154")
    # my_stops = gpd.GeoDataFrame(
    #     data={"name": stops["stop_name"]},
    #     geometry=gpd.GeoSeries.from_wkb(stops["stop_point"], crs="EPSG:2154"),
    # )
    # output_dir = os.path.join("output", "access", str(myid))
    # if not os.path.isdir(output_dir):
    #     os.makedirs(output_dir)
    # origin.to_file(os.path.join(output_dir, "origin.geojson"), driver="GeoJSON")
    # access.to_file(os.path.join(output_dir, "access.geojson"), driver="GeoJSON")
    # my_stops.to_parquet(os.path.join(output_dir, "stops.parquet"))
    # my_vertices = (
    #     vert_global_dists.filter(index=myid)
    #     .join(vert_access_dists.filter(index=myid), on="k")
    #     .select("k", "min_access_dist", diff=pl.col("min_access_dist") - pl.col("min_stop_dist"))
    # )
    # worst_k = my_vertices.sort("diff", descending=True)["k"][0]
    # worst_vertice_coords = origin.loc[0].exterior.coords[worst_k]
    # worst_vertice = Point(worst_vertice_coords)
    # worst_stop = my_stops.loc[my_stops.distance(worst_vertice).idxmin(), "geometry"]
    # best_k = my_vertices.sort("diff", "min_access_dist")["k"][0]
    # best_vertice_coords = origin.loc[0].exterior.coords[best_k]
    # best_vertice = Point(best_vertice_coords)
    # best_stop = my_stops.loc[my_stops.distance(best_vertice).idxmin(), "geometry"]
    # d1 = best_vertice.distance(best_stop)
    # d2 = best_vertice.distance(worst_stop)
    # best_lines = gpd.GeoDataFrame(
    #     data={"dist": [d1, d2]},
    #     geometry=[LineString((best_vertice, best_stop)), LineString((best_vertice, worst_stop))],
    #     crs="EPSG:2154",
    # )
    # d1 = worst_vertice.distance(best_stop)
    # d2 = worst_vertice.distance(worst_stop)
    # worst_lines = gpd.GeoDataFrame(
    #     data={"dist": [d1, d2]},
    #     geometry=[LineString((worst_vertice, best_stop)), LineString((worst_vertice, worst_stop))],
    #     crs="EPSG:2154",
    # )
    # best_lines.to_file(os.path.join(output_dir, "best_line.geojson"), driver="GeoJSON")
    # worst_lines.to_file(os.path.join(output_dir, "worst_line.geojson"), driver="GeoJSON")
