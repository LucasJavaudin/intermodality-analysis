import json
import subprocess

import polars as pl

RP_FILENAME = "./data/base-ic-evol-struct-pop-2022.CSV"

DENSITY_FILENAME = "./data/fichier_diffusion_2024.xlsx"


def reweight(persons: pl.DataFrame):
    save_totals()
    save_persons(persons)
    print("Running R script to compute new sample weights")
    subprocess.run(["Rscript", "R/weighting.R"])
    new_weights = pl.read_parquet("output/data/new_weights.parquet")["newWeights"]
    persons = persons.with_columns(sample_weight_surveyed=new_weights)
    return persons


def save_persons(persons: pl.DataFrame):
    persons = (
        persons.with_columns(
            # Set PCS group code to 7 for retirees, to 9 for persons < 15 y.o., to 8 for other
            # non-workers (except unemployed) and to 8 for remaining NULL values.
            pcs=pl.when(pl.col("age") < 15)
            .then(9)
            .when(detailed_professional_occupation="other:retired")
            .then(7)
            .when(
                pl.col("professional_occupation").ne_missing("worker")
                & pl.col("detailed_professional_occupation").ne_missing("other:unemployed")
            )
            .then(8)
            .otherwise(pl.col("pcs_group_code").fill_null(8))
        )
        .select(
            "name",
            "person_id",
            "pcs",
            init_weight="sample_weight_surveyed",
            woman=pl.col("woman").cast(pl.Int64),
            age_cat=pl.col("age")
            .cut(
                [11, 18, 25, 40, 55, 65, 80],
                labels=["1", "2", "3", "4", "5", "6", "7", "8"],
                left_closed=True,
            )
            .cast(pl.String)
            .cast(pl.Int64),
            # Convert density from 7 levels to 3 levels.
            density_cat=pl.col("home_insee_density").replace_strict(
                {1: 1, 2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3}
            ),
        )
        .unique(subset=["name", "person_id"])
    )
    persons.write_parquet("output/data/persons.parquet")


def save_totals():
    df = (
        pl.scan_csv(RP_FILENAME, separator=";", schema_overrides={"COM": pl.String})
        .with_columns(
            # Population <= 5 y.o.
            age0to5=pl.col("P22_POP0002") + pl.col("P22_POP0305"),
        )
        .select(
            insee="COM",
            # Population > 5 y.o.
            pop=pl.col("P22_POP") - pl.col("age0to5"),
            # Nb women > 5 y.o.
            woman="P22_POPF" - pl.col("age0to5") / 2,
            # Nb men > 5 y.o.
            man="P22_POPH" - pl.col("age0to5") / 2,
            age6to10="P22_POP0610",
            age11to17="P22_POP1117",
            age18to24="P22_POP1824",
            age25to39="P22_POP2539",
            age40to54="P22_POP4054",
            age55to64="P22_POP5564",
            age65to79="P22_POP6579",
            age80plus="P22_POP80P",
            # Age >= 15, 6 PCS
            pcs1="C22_POP15P_STAT_GSEC11_21",
            pcs2="C22_POP15P_STAT_GSEC12_22",
            pcs3="C22_POP15P_STAT_GSEC13_23",
            pcs4="C22_POP15P_STAT_GSEC14_24",
            pcs5="C22_POP15P_STAT_GSEC15_25",
            pcs6="C22_POP15P_STAT_GSEC16_26",
            # Age >= 15 retired
            pcs7="C22_POP15P_STAT_GSEC32",
            # Age >= 15 no prof. activity
            pcs8="C22_POP15P_STAT_GSEC40",
            # Age 6 to 14.
            pcs9=pl.col("P22_POP") - pl.col("age0to5") - pl.col("C22_POP15P"),
        )
        .collect()
    )

    densities = pl.read_excel(
        DENSITY_FILENAME,
        read_options={"header_row": 4},
        columns=["CODGEO", "DENS"],
        schema_overrides={"CODGEO": pl.String, "DENS": pl.UInt8},
    ).rename({"CODGEO": "insee", "DENS": "density_cat"})

    df = df.join(densities, on="insee", how="left")

    # Fix for Paris, Lyon and Marseille (density is 1).
    is_arrondissement = pl.col("insee").str.slice(0, 3).is_in(("132", "693", "751"))
    df = df.with_columns(density_cat=pl.when(is_arrondissement).then(1).otherwise("density_cat"))

    assert df["density_cat"].null_count() == 0

    # Multiply dummy variable density cat with population size.
    df = df.to_dummies("density_cat").with_columns(pl.col("^density_cat_.*$") * pl.col("pop"))

    df = df.select(
        woman=pl.col("woman").sum(),
        man=pl.col("man").sum(),
        age6to10=pl.col("age6to10").sum(),
        age11to17=pl.col("age11to17").sum(),
        age18to24=pl.col("age18to24").sum(),
        age25to39=pl.col("age25to39").sum(),
        age40to54=pl.col("age40to54").sum(),
        age55to64=pl.col("age55to64").sum(),
        age65to79=pl.col("age65to79").sum(),
        age80plus=pl.col("age80plus").sum(),
        pcs1=pl.col("pcs1").sum(),
        pcs2=pl.col("pcs2").sum(),
        pcs3=pl.col("pcs3").sum(),
        pcs4=pl.col("pcs4").sum(),
        pcs5=pl.col("pcs5").sum(),
        pcs6=pl.col("pcs6").sum(),
        pcs7=pl.col("pcs7").sum(),
        pcs8=pl.col("pcs8").sum(),
        pcs9=pl.col("pcs9").sum(),
        density_cat_1=pl.col("density_cat_1").sum(),
        density_cat_2=pl.col("density_cat_2").sum(),
        density_cat_3=pl.col("density_cat_3").sum(),
    )
    totals = next(df.iter_rows(named=True))
    with open("output/data/rp_totals.json", "w") as f:
        json.dump(totals, f)
