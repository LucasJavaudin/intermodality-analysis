// Copyright 2025 Lucas Javaudin
// This work is copyrighted and all rights are reserved.
// You may not use, copy, modify, or distribute this code
// without explicit permission from the author.
#import "@preview/peace-of-posters:0.5.6" as pop
#import "@preview/zero:0.5.0": num, set-group, zi

#let results = json("../../output/results.json")

#let lvmt-cy = (
  "body-box-args": (
    inset: (x: 0.0em, top: 0.5em, bottom: 0.0em),
    width: 100%,
    stroke: none,
    // fill: rgb("#3182bd"),
  ),
  "body-text-args": (:),
  "heading-box-args": (
    inset: (x: 0.0em, top: 0.1em, bottom: 0.3em),
    width: 100%,
    // fill: rgb("#1112bd"),
    stroke: (
      bottom: 5pt + rgb("#c6dbef"),
      rest: none,
    ),
  ),
  "heading-text-args": (
    fill: rgb("#4D4B49"),
    weight: "bold",
  ),
  "title-box-args": (
    inset: 0.6em,
    width: 100%,
    fill: rgb("#c6dbef"),
    // stroke: rgb(25, 25, 25),
  ),
)

#set page("a0", margin: 1cm)
#pop.set-poster-layout(pop.layout-a0)
#pop.set-theme(lvmt-cy)
#set text(size: pop.layout-a0.at("body-size"), font: "Roboto")
#set par(justify: true)
#let box-spacing = 1.0em
#set columns(gutter: box-spacing)
#set block(spacing: box-spacing)
#pop.update-poster-layout(spacing: box-spacing)

// Custom
#show link: underline
#show figure.caption: emph
#show figure: set figure.caption(position: top)
#show heading: underline
#set par(leading: 0.3em, spacing: 1em)

// Use non-breaking space as digit-grouping separator.
#set-group(separator: sym.space.nobreak.narrow)
// Rounding utils.
#let oned_round = (mode: "places", precision: 1)
#let int_round = (mode: "places", precision: 0)
#let threefigs_round = (mode: "figures", precision: 3)
// Declare units.
#let percent = zi.declare("%")
#let km = zi.declare("km")


#pop.title-box(
  "Analyse des déterminants de l'intermodalité à partir d'une agrégation d'enquêtes de mobilité",
  authors: "Lucas Javaudin",
  institutes: "THEMA, CY Cergy Paris Université\nLVMT, ENPC, Institut Polytechnique de Paris, Univ Gustave Eiffel",
  logo: grid(
    columns: (1fr),
    rows: (auto, auto),
    gutter: 20pt,
    align: center + horizon,
    image("logos/thema_bw.png", width: 100%),
    // image("logos/cyu_bw.png", width: 100%),
    image("logos/lvmt_bw.png", width: 100%),
    // image("logos/enpc.png", width: 100%),
  ),
  text-relative-width: 67%,
  spacing: 10%,
  title-size: 74pt,
  authors-size: 52pt,
  institutes-size: 52pt,
)

#pop.column-box(heading: "Standardisation des enquêtes de mobilité avec MobiSurvStd")[
  #grid(columns: (1fr, auto, 1fr), column-gutter: 30pt, [
    Cette étude s'appuie sur l'aggrégation de #strong[#results.nb_surveys enquêtes] de mobilité menées en France entre #results.min_year et #results.max_year.
    Ces enquêtes fournissent  des données détaillées sur les déplacements réalisés la veille de l’enquête pour #strong[#num(results.global.raw_counts.nb_persons, math: false, round: threefigs_round) individus], représentant un total de #strong[#num(results.global.raw_counts.nb_trips, math: false, round: threefigs_round) déplacements].

    Enquêtes utilisées :

    - #results.nb_surveys_cerema Enquêtes CEREMA (EMC², EDGT, EDVM, EMD)
    - #results.nb_surveys_egt Enquête Globale Transport (2010)

    Les poids des enquêtes ont été redressés pour être représentatifs de l'ensemble du territoire français, et notamment des milieux ruraux.

    Cette étude s'intéresse à l'*intermodalité*, définie comme le recours à deux modes ou plus (hors marche à pied) pour un même déplacement.
    Les #results.nb_surveys enquêtes contiennent #strong[#num(results.stats.intermodal_trips.nb_trips, math: false) déplacements intermodaux], offrant ainsi une base robuste pour son analyse.
  ],[
    #figure(
      image("../../output/maps/survey_map.jpg", height: 880pt),
      // caption: [Répartition spatiale des 79 enquêtes],
      numbering: none,
    )
  ],[
    *MobiSurvStd* est une bibliothèque Python open-source qui permet, en une ligne de commande, de standardiser les enquêtes de mobilité en France, dans un format Parquet clair et documenté.
    Cet outil constitue ainsi une ressource précieuse pour la communauté scientifique, en facilitant des analyses comparatives et reproductibles à l’échelle nationale.

    #v(50pt)

    #align(center, [
      #image("../../output/qrcode.png", width: 300pt)

      #v(20pt)

      #link("https://mobisurvstd.github.io/MobiSurvStd/")
    ])
  ])
]
#pop.column-box(heading: "Intermodalité : 9 faits stylisés")[
  #columns(3,[
    #pop.column-box(heading: "1. Part faible des déplacements")[
      L'intermodalité représente #strong[#percent(100 * results.stats.intermodal_trips.share_weighted_trips, round: oned_round, math: false) des déplacements locaux] ($<$80 km), pour #strong[#percent(100 * results.stats.intermodal_trips.share_weighted_dist, round: oned_round, math: false) de la distance parcourue].
    ]
    #pop.column-box(heading: "2. Des déplacements longs")[
      Les déplacements intermodaux parcourent en moyenne #strong[#km(results.stats.intermodal_trips.mean_dist, round: oned_round, math: false)], contre #km(results.stats.unimodal_trips_no_walk.mean_dist, round: oned_round, math: false) pour les déplacements unimodaux (hors marche à pied).\
      Parmi les déplacements de plus de 20 km, #percent(100 * results.stats.intermodal_trips_dist_gt_20.share_weighted_trips, round: oned_round, math: false) sont intermodaux.
      #figure(
        image("../../output/poster_graphs/euclidean_dist_densities.png"),
        caption: [Distribution des distances de déplacements],
        numbering: none,
      )
    ]
    #pop.column-box(heading: "3. Déplacements travail ou étude")[
      #let share_work_educ_inter = 100 * results.purposes.intermodal_trips.work.share_weighted_trips + 100 * results.purposes.intermodal_trips.education.share_weighted_trips
      #let share_work_educ_uni = 100 * results.purposes.unimodal_trips_no_walk.work.share_weighted_trips + 100 * results.purposes.unimodal_trips_no_walk.education.share_weighted_trips
      La déplacements intermodaux sont liés #strong[au travail ou à l'éducation dans #percent(share_work_educ_inter, round: int_round, math: false) des cas], contre #percent(share_work_educ_uni, round: int_round, math: false) pour les déplacements unimodaux (hors marche à pied).
      #figure(
        image("../../output/poster_graphs/purposes_bars.png"),
        caption: [Motifs principaux selon le type de déplacement\
          // #text(size: 26pt, [Un unique motif est attribué à chaque déplacement selon la méthodologie de Raux et al. (2018)])
        ],
        numbering: none,
      )
      // La voiture est utilisé pour quitter ou rejoindre le domicile dans 85.6 % des déplacements combinant voiture et TC (avec le domicile comme origine ou destination).
    ]
    #pop.column-box(heading: "4. Profils des usagers")[
      #let share_executives_inter = 100 * results.person_characs.pcs_group_code.at("3").at("pt+car_passenger").share_weighted_trips
      #let share_executives_uni = 100 * results.person_characs.pcs_group_code.at("3").at("unimodal_trips_no_walk").share_weighted_trips
      #let share_women_inter = 100 * results.person_characs.woman.at("pt+car_driver").share_weighted_trips
      #let share_women_uni = 100 * results.person_characs.woman.at("unimodal_trips_no_walk").share_weighted_trips
      Voiture conducteur + TC :
      - #strong[Cadre : #percent(share_executives_inter, round: int_round, math: false)] (vs #percent(share_executives_uni, round: int_round, math: false))
      - #strong[Femme : #percent(share_women_inter, round: int_round, math: false)] (vs #percent(share_women_uni, round: int_round, math: false))

      #let share_students_inter = 100 * results.person_characs.professional_occupation.student.at("pt+car_passenger").share_weighted_trips
      #let share_students_uni = 100 * results.person_characs.professional_occupation.student.at("unimodal_trips_no_walk").share_weighted_trips
      #let share_no_license_inter = 100 * results.person_characs.no_license.at("pt+car_passenger").share_weighted_trips
      #let share_no_license_uni = 100 * results.person_characs.no_license.at("unimodal_trips_no_walk").share_weighted_trips
      Voiture passager + TC :
      - #strong[Étudiant : #percent(share_students_inter, round: int_round, math: false)] (vs #percent(share_students_uni, round: int_round, math: false))
      - #strong[Sans permis de conduire : #percent(share_no_license_inter, round: int_round, math: false)] (vs #percent(share_no_license_uni, round: int_round, math: false))
    ]
    #colbreak()
    #pop.column-box(heading: "5. Duo dominant : voiture et TC")[
      #let share_car_pt = 100 * results.intermodality-types.at("pt+car_driver").share_weighted_trips + 100 * results.intermodality-types.at("pt+car_passenger").share_weighted_trips
      La grande majorité (#percent(share_car_pt, round: oned_round, math: false)) des déplacements intermodaux lie *voiture et transports en commun (TC)*.
      #figure(
        image("../../output/poster_graphs/intermodality_types_bars.png"),
        caption: [Combinaisons de modes principales],
        numbering: none,
      )
    ]
    #pop.column-box(heading: "6. Plus de TC que de voiture")[
      #let pt_dist = results.pt_car_trips.distances.mean_pt_dist
      #let car_dist = results.pt_car_trips.distances.mean_car_dist
      Les individus se déplaçant en combinant voiture et TC parcourent en moyenne #strong[#km(pt_dist, round: oned_round, math: false) en TC] contre #strong[#km(car_dist, round: oned_round, math: false) en voiture].
      #figure(
        image("../../output/poster_graphs/pt_dist_ratio_density.png"),
        caption: [Distribution de la part de la distance parcourue en TC dans la distance totale],
        numbering: none,
      )
    ]
    #pop.column-box(heading: "7. Un moyen d'accéder au train")[
      #let train_share = 100 * results.pt_car_trips.entry_exit_mode.train.share_weighted_trips
      #let train_share_all = 100 * results.pt_legs.modes.train.share_weighted_legs
      Lors des correspondances entre voiture et TC, #strong[le train est utilisé dans #percent(train_share, round: int_round, math: false) des cas], contre seulement #percent(train_share_all, round: int_round, math: false) des trajets TC en général.
      #figure(
        image("../../output/poster_graphs/pt_modes_bars.png"),
        caption: [Distribution des modes TC utilisés dans les correspondances voiture–TC],
        numbering: none,
      )
      #let no_transfer_share = 100 * results.pt_car_trips.nb_transfers.at("0").share_weighted_trips
      La partie TC s'effectue sans aucune correspondance dans #percent(no_transfer_share, round: int_round, math: false) des cas.
    ]
    #colbreak()
    #pop.column-box(heading: "8. Un pont entre rural et urbain")[
      #let non_pole_orig_share = 100 * (results.origin_destination_density.origin_density.at("3_intermediate").share_weighted + results.origin_destination_density.origin_density.at("4_rural").share_weighted)
      #let pole_dest_share = 100 * (results.origin_destination_density.destination_density.at("1_dense_main").share_weighted + results.origin_destination_density.destination_density.at("2_dense_secondary").share_weighted)
      #let rural_to_pole_share = 100 * results.origin_destination_density.matrix.at("4_rural").at("1_dense_main").car_then_pt_share
      Les déplacements Voiture$->$TC partent majoritairement de communes #strong[non denses (#percent(non_pole_orig_share, round: int_round, math: false))] et se terminent dans des communes #strong[denses (#percent(pole_dest_share, round: int_round, math: false))].
      Ils représentent #percent(rural_to_pole_share, round: oned_round, math: false) des déplacements des communes rurales vers les pôles d'AAV.
      #figure(
        image("../../output/poster_graphs/insee_density_flows_polar.png", width: 90%),
        caption: [Flux des déplacements Voiture$->$TC selon la densité\
          #text(size: 26pt, [L'épaisseur des flèches est proportionnelle au nombre de déplacements Voiture$->$TC])],
        numbering: none,
      )
    ]
    #pop.column-box(heading: "9. Choix de la gare de proximité ?")[
      #let share_certainly_valid = 100 * results.origin_access_nearest.rail.share_certainly_valid_trips
      #let share_certainly_invalid = 100 * results.origin_access_nearest.rail.share_certainly_not_valid_trips
      #let share_uncertain = 100 - share_certainly_valid - share_certainly_invalid
      Parmi les déplacements Voiture conducteur$->$TC avec correspondance en train, #strong[#percent(share_certainly_valid, round: int_round, math: false) se rendent à la gare la plus proche du départ], tandis que #strong[#percent(share_certainly_invalid, round: int_round, math: false) choisissent une gare plus éloigné].
      Pour les autres (#percent(share_uncertain, round: int_round, math: false)), on ne peut pas conclure avec certitude.
      #figure(
        image("../../output/maps/nearest_stop_example.jpg", width: 85%),
        caption: [Exemple de déplacement où l'on ne peut pas conclure],
        numbering: none,
      )
      Lecture: Si le point vert est le point de départ, la gare la plus proche est bien située dans la zone d'entrée, mais ce n'est pas le cas pour le point orange.
    ]
  ])
  #align(center, emph[Les codes ayant servi à réaliser ce poster sont disponibles à l'adresse #link("https://github.com/LucasJavaudin/intermodality-analysis")])
]
