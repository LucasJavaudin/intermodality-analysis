# Copyright 2025 Lucas Javaudin
# SPDX-License-Identifier: MIT
library("arrow")
library("icarus")
library("rjson")

df <- read_parquet("output/data/persons.parquet")

totals <- fromJSON(file="output/data/rp_totals.json")

mar1 <- c("woman", 2, totals$man, totals$woman, 0, 0, 0, 0, 0, 0, 0)
mar2 <- c(
  "age_cat",
  8,
  totals$age6to10,
  totals$age11to17,
  totals$age18to24,
  totals$age25to39,
  totals$age40to54,
  totals$age55to64,
  totals$age65to79,
  totals$age80plus,
  0
)
mar3 <- c(
  "pcs",
  9,
  totals$pcs1,
  totals$pcs2,
  totals$pcs3,
  totals$pcs4,
  totals$pcs5,
  totals$pcs6,
  totals$pcs7,
  totals$pcs8,
  totals$pcs9
)
mar4 <- c(
  "density_cat",
  3,
  totals$density_cat_1,
  totals$density_cat_2,
  totals$density_cat_3,
  0,
  0,
  0,
  0,
  0,
  0
)
marges <- rbind(mar1, mar2, mar3, mar4)

newWeights <- calibration(
  data=df,
  marginMatrix=marges,
  colWeights="init_weight",
  method="logit",
  bounds=c(0.2, 5.0),
  description=FALSE,
  # calibTolerance=1e-3,
  # precisionBounds=1e-3,
)

weights_df <- as.data.frame(newWeights)
write_parquet(weights_df, "output/data/new_weights.parquet")
