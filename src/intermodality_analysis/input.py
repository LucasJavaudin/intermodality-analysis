import polars as pl
from mobisurvstd import SurveyDataReader, read_many

# Surveys from oversea territories.
OVERSEA_SURVEYS = ["guadeloupe_2021", "fortdefrance_2014", "la_reunion_2016"]


def valid_survey(data: SurveyDataReader):
    # Exclude the national survey and the EGT2020.
    return data.metadata["name"] not in ("EMP2019", "EGT2020")


def get_trips(data: SurveyDataReader) -> pl.DataFrame:
    """Given a SurveyDataReader, returns a DataFrame of trips, with some legs' characteristics."""
    name = data.metadata["name"]
    if not valid_survey(data):
        return None
    print(name)
    df = data.trips.join(
        data.legs.group_by("trip_id").agg(
            leg_characs=pl.struct(
                "mode",
                "mode_group",
                "leg_euclidean_distance_km",
                "car_type",
                "car_id",
                "start_detailed_zone",
                "start_lng",
                "start_lat",
            )
        ),
        on="trip_id",
        how="left",
    )
    df = df.with_columns(name=pl.lit(name)).drop("original_trip_id")
    return df


def read_all_trips(dir: str) -> pl.DataFrame:
    """Aggregate all trips from the surveys in the input directory."""
    df = read_many(dir, get_trips, lambda x, y: pl.concat((x, y)))
    # Assert that the same survey (= same name) was not read twice.
    assert len(df.select("trip_id", "name").unique()) == len(df), "Duplicate surveys found!"
    return df


def get_persons(data: SurveyDataReader) -> pl.DataFrame:
    """Given a SurveyDataReader, returns a DataFrame of persons, with household-level data."""
    name = data.metadata["name"]
    survey_type = data.metadata["type"]
    if not valid_survey(data):
        return None
    print(name)
    df = data.persons.join(
        data.households.select(
            "household_id", "home_insee_density", "home_insee_aav_type", "nb_persons", "nb_cars"
        ),
        on="household_id",
        how="left",
    )
    df = df.with_columns(name=pl.lit(name), survey_type=pl.lit(survey_type)).drop(
        "original_person_id"
    )
    return df


def read_all_persons(dir: str) -> pl.DataFrame:
    """Aggregate all persons from the surveys in the input directory."""
    df = read_many(dir, get_persons, lambda x, y: pl.concat((x, y)))
    # Assert that the same survey (= same name) was not read twice.
    assert len(df.select("person_id", "name").unique()) == len(df), "Duplicate surveys found!"
    return df


def get_detailed_zones(data: SurveyDataReader):
    name = data.metadata["name"]
    if name in ("EGT2010", "EGT2020", "EMP2019"):
        return
    if name in OVERSEA_SURVEYS:
        return
    if data.detailed_zones is not None:
        gdf = data.detailed_zones
        gdf["binary_geom"] = gdf.geometry.to_crs("EPSG:2154").to_wkb()
        return pl.from_pandas(gdf.loc[:, ["binary_geom", "detailed_zone_id"]]).with_columns(
            name=pl.lit(name)
        )


def read_all_detailed_zones(dir: str):
    """Read all detailed zones over surveys in the given directory."""
    return read_many(
        "../MobiSurvStd/output/all/", get_detailed_zones, lambda x, y: pl.concat((x, y))
    )
