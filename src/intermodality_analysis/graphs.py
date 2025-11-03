# Copyright 2025 Lucas Javaudin
# SPDX-License-Identifier: MIT
from math import pi

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from scipy.stats import gaussian_kde

from intermodality_analysis.mpl import (
    BLACK,
    BLUE,
    DOC_TYPE,
    GREEN,
    LANGUAGE,
    LIGHTBLUE,
    ORANGE,
    OUTPUT_FORMAT,
    PINK,
    PURPLE,
    RED,
    REDS,
    YELLOW,
    get_figure,
    set_size,
)

# Labels of the purposes.
PURPOSE_LABELS_FR = {
    "work": "Travail",
    "education": "Étude",
    "leisure": "Loisir",
    "task": "Démarche",
    "shopping": "Achat",
    "escort": "Accomp.",
    "other": "Autre",
}
PURPOSE_LABELS_EN = {
    "work": "Work",
    "education": "Education",
    "leisure": "Leisure",
    "task": "Service",
    "shopping": "Shopping",
    "escort": "Escorting",
    "other": "Other",
}

# Labels of the intermodality types.
INTERMODALITY_LABELS_FR = {
    "pt+car_driver": "TC + Voiture (cond.)",
    "pt+car_passenger": "TC + Voiture (pass.)",
    "pt+bicycle": "TC + Vélo",
    "car_driver+car_passenger": "Voiture (cond. + pass.)",
    "other": "Autre",
}
INTERMODALITY_LABELS_EN = {
    "pt+car_driver": "PT + Car driver",
    "pt+car_passenger": "PT + Car passenger",
    "pt+bicycle": "PT + Bicycle",
    "car_driver+car_passenger": "Car driver + Car passenger",
    "other": "Other",
}

# Colors of the intermodality types.
INTERMODALITY_COLORS = {
    "pt+car_driver": ORANGE,
    "pt+car_passenger": YELLOW,
    "pt+bicycle": GREEN,
    "car_driver+car_passenger": PINK,
    "other": BLACK,
}


# Label of the public-transit mode groups.
PT_MODE_LABELS_FR = {
    "metro": "Métro",
    "other": "Autre",
    "bus": "Bus",
    "coach": "Autocar",
    "train": "Train",
    "tram": "Tramway",
}
PT_MODE_LABELS_EN = {
    "metro": "Metro",
    "other": "Other",
    "bus": "Bus",
    "coach": "Coach",
    "train": "Train",
    "tram": "Tram",
}

# Color of the public-transit mode groups.
PT_MODE_COLORS = {
    "metro": ORANGE,
    "other": BLACK,
    "bus": BLUE,
    "coach": LIGHTBLUE,
    "train": RED,
    "tram": YELLOW,
}

# Labels of the density categories.
DENSITY_LABELS_FR = {
    "1_dense_main": "Pôle",
    "2_dense_secondary": "Commune\ndense",
    "3_intermediate": "Commune\nintermédiaire",
    "4_rural": "Commune\nrurale",
}
DENSITY_LABELS_EN = {
    "1_dense_main": "Center",
    "2_dense_secondary": "Dense",
    "3_intermediate": "Intermediate",
    "4_rural": "Rural",
}


def add_extension(filename: str):
    return filename + "." + OUTPUT_FORMAT


# Density chart of euclidean distance distribution (intermodality vs no-intermodality)
def get_density(xs, values, weights, bw_factor: float):
    density = gaussian_kde(values, bw_factor, weights=weights)
    return density(xs)


def euclidean_distance_densities(
    unimodal_dists: pl.Series,
    unimodal_weights: pl.Series,
    intermodal_dists: pl.Series,
    intermodal_weights: pl.Series,
    filename: str,
    max_dist: int = 30,
    bw_factor: float = 0.05,
):
    xs = np.linspace(0, max_dist, 200)
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.5)
    else:
        fig, ax = get_figure(ratio=0.5, fraction=0.6)
    if LANGUAGE == "FR":
        unimodal_str = "Unimodal (hors MàP)"
        intermodal_str = "Intermodal"
        ax.set_xlabel("Distance à vol d'oiseau (km)")
        ax.set_ylabel("Densité")
    elif LANGUAGE == "EN":
        unimodal_str = "Unimodal (ex. walk-only)"
        intermodal_str = "Intermodal trips"
        ax.set_xlabel("Trip euclidean distance (km)")
        ax.set_ylabel("Density")
    # Unimodal trips.
    ys = get_density(xs, unimodal_dists, unimodal_weights, bw_factor)
    ax.plot(xs, ys, color=PURPLE, alpha=0.9)
    ax.fill_between(xs, ys, color=PURPLE, alpha=0.3)
    idx = ys.argmax() + 10
    ax.annotate(unimodal_str, xy=(xs[idx] + 1, ys[idx]), color=PURPLE)
    # Intermodal trips.
    ys = get_density(xs, intermodal_dists, intermodal_weights, bw_factor)
    ax.plot(xs, ys, color=BLUE, alpha=0.9)
    ax.fill_between(xs, ys, color=BLUE, alpha=0.3)
    idx = ys.argmax() + 10
    ax.annotate(intermodal_str, xy=(xs[idx] + 1, ys[idx]), color=BLUE)
    # Figure parameters.
    ax.set_xlim(0, max_dist)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="y", which="both", length=0, labelleft=False)
    sns.despine(top=True, right=True)
    fig.tight_layout(pad=0.5)
    fig.savefig(add_extension(filename))


def age_density_by_type(
    unimodal_ages: pl.Series,
    unimodal_weights: pl.Series,
    driver_ages: pl.Series,
    driver_weights: pl.Series,
    passenger_ages: pl.Series,
    passenger_weights: pl.Series,
    df: pl.DataFrame,
    filename: str,
    bw_factor: float = 0.05,
):
    m = 100
    xs = np.linspace(0, m, 200)
    fig, ax = get_figure()
    # No-intermodality
    ys = get_density(xs, unimodal_ages, unimodal_weights, bw_factor)
    ax.plot(xs, ys, color=PURPLE, alpha=0.9)
    ax.fill_between(xs, ys, color=PURPLE, alpha=0.3)
    idx = ys.argmax() + 10
    ax.annotate("Unimodal (hors MàP)", xy=(xs[idx] + 1, ys[idx]), color=PURPLE)
    # Intermodality car_driver
    ys = get_density(xs, driver_ages, driver_weights, bw_factor)
    ax.fill_between(xs, ys, color=ORANGE, alpha=0.3)
    idx = ys.argmax() + 10
    ax.plot(xs, ys, color=ORANGE, alpha=0.9)
    ax.annotate("Intermodalité (cond.)", xy=(xs[idx] + 1, ys[idx]), color=ORANGE)
    # Intermodality car_passenger
    ys = get_density(xs, passenger_ages, passenger_weights)
    ax.fill_between(xs, ys, color=YELLOW, alpha=0.3)
    idx = ys.argmax() + 10
    ax.plot(xs, ys, color=YELLOW, alpha=0.9)
    ax.annotate("Intermodalité (pass.)", xy=(xs[idx] + 1, ys[idx]), color=YELLOW)
    ax.set_xlabel("Age")
    ax.set_ylabel("Densité")
    ax.set_xlim(0, m)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="y", which="both", length=0, labelleft=False)
    sns.despine(top=True, right=True)
    fig.tight_layout(pad=0.5)
    fig.savefig(add_extension(filename))


def purposes_bar_chart(results: dict, filename: str):
    """Creates a horizontal bar chart of purposes."""
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.6)
    else:
        fig, ax = get_figure(ratio=0.7, fraction=0.6)
    # Find the purposes in order of increasing share for intermodal trips.
    purposes_order = list(
        map(
            lambda i: i[0],
            sorted(results["intermodal_trips"].items(), key=lambda i: i[1]["share_weighted_trips"]),
        )
    )
    # Remove "other" purpose (only few trips).
    purposes_order.pop(purposes_order.index("other"))
    if LANGUAGE == "FR":
        labels = [PURPOSE_LABELS_FR[p] for p in purposes_order]
        intermodal_str = "Intermodal"
        # unimodal_str = "Unimodal (hors MàP)"
        unimodal_str = "Unimodal"
        xlabel = "Part des déplacements"
    elif LANGUAGE == "EN":
        labels = [PURPOSE_LABELS_EN[p] for p in purposes_order]
        intermodal_str = "Intermodal"
        unimodal_str = "Unimodal (ex. walk-only)"
        xlabel = "Share of trips"
    bars_data = [
        (results["intermodal_trips"], 0.45, BLUE, intermodal_str),
        (results["unimodal_trips_no_walk"], -0.45, PURPLE, unimodal_str),
    ]
    for r, height, color, label in bars_data:
        widths = [r[p]["share_weighted_trips"] for p in purposes_order]

        # Add some transparency for non-work / education purpose to highlight these two.
        def alpha_fn(p):
            if p in ("work", "education"):
                return 0.9
            else:
                return 0.6

        colors = [mcolors.to_rgba(color, alpha=alpha_fn(p)) for p in purposes_order]
        bars = ax.barh(
            y=labels,
            width=widths,
            height=height,
            color=colors,
            align="edge",
            label=label,
        )
        ax.bar_label(bars, fmt="{:.0%}", padding=5, color=color)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlim(left=0)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_xlabel(xlabel)
    ax.legend(loc="lower right", handletextpad=0.3)
    ax.grid(which="major", axis="x")
    sns.despine(top=True, right=True)
    fig.tight_layout(pad=0.3)
    fig.savefig(add_extension(filename))


def intermodality_types_bars(results: dict, filename: str):
    """Creates a horizontal bar chart of intermodality type shares."""
    # Sort the results in order of increasing share.
    results = dict(sorted(results.items(), key=lambda i: i[1]["share_weighted_trips"]))
    widths = [v["share_weighted_trips"] for v in results.values()]
    colors = [INTERMODALITY_COLORS[k] for k in results.keys()]
    if LANGUAGE == "FR":
        labels = [INTERMODALITY_LABELS_FR[k] for k in results.keys()]
        xlabel = "Part des déplacements"
    elif LANGUAGE == "EN":
        labels = [INTERMODALITY_LABELS_EN[k] for k in results.keys()]
        xlabel = "Share of trips"
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.4)
    else:
        fig, ax = get_figure(ratio=0.5, fraction=0.6)
    bars = ax.barh(y=labels, width=widths, height=0.9, color=colors)
    ax.bar_label(bars, fmt="{:.1%}", padding=5)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlim(0, 0.5)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_xlabel(xlabel)
    ax.grid(which="major", axis="x")
    sns.despine(top=True, right=True)
    fig.tight_layout(pad=0.5)
    fig.savefig(add_extension(filename))


def ratio_pt_car_dist_density(
    ratios: pl.Series, weights: pl.Series, filename: str, bw_factor: float = 0.05
):
    """Creates a line plot of the density of the ratio PT dist / total dist."""
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.5)
    else:
        fig, ax = get_figure(ratio=0.6, fraction=0.6)
    if LANGUAGE == "FR":
        more_car_str = "Plus de voiture"
        more_pt_str = "Plus de TC"
        xlabel = "Ratio dist. TC / dist. totale"
        ylabel = "Densité"
    elif LANGUAGE == "EN":
        more_car_str = "More car than PT"
        more_pt_str = "More PT than car"
        xlabel = "Share of distance by public transit (PT)"
        ylabel = "Density"
    xs = np.linspace(0.0, 1.0, 200)
    ys = get_density(xs, ratios, weights, bw_factor)
    ax.plot(xs, ys, color=BLUE)
    ax.fill_between(xs, ys, color=BLUE, alpha=0.5)
    ax.axvline(0.5, color=BLACK)
    ax.annotate(
        more_car_str,
        xy=(0.18, 0.75),
        xytext=(0.25, 0.75),
        xycoords="figure fraction",
        textcoords="figure fraction",
        color=BLACK,
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "->"},
    )
    ax.annotate(
        more_pt_str,
        xy=(0.82, 0.75),
        xytext=(0.75, 0.75),
        xycoords="figure fraction",
        textcoords="figure fraction",
        color=BLACK,
        ha="right",
        va="center",
        arrowprops={"arrowstyle": "->"},
    )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="y", which="both", length=0, labelleft=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    sns.despine(top=True, right=True)
    fig.tight_layout()
    fig.savefig(add_extension(filename))


def pt_vs_car_dist_scatter(
    pt_dists: pl.Series,
    car_dists: pl.Series,
    weights: pl.Series,
    max_dist: int = 30,
    bw_factor: float = 0.1,
):
    """Creates a scatter plot of PT dist vs car dist (for PT+car trips), with the marginal
    densities.
    """
    fig, axs = plt.subplot_mosaic(
        [["histx", "."], ["scatter", "histy"]],
        figsize=set_size(ratio=1.0),
        width_ratios=(5, 2),
        height_ratios=(2, 5),
        layout="constrained",
    )
    axs["scatter"].hist2d(
        x=pt_dists,
        y=car_dists,
        bins=30,
        range=((0, max_dist), (0, max_dist)),
        density=True,
        weights="sample_weight_surveyed",
    )
    xs = np.linspace(0, max_dist, 200)
    ys = get_density(xs, pt_dists, weights, bw_factor)
    axs["histx"].fill_between(xs, ys, color=ORANGE)
    ys = get_density(xs, car_dists, weights)
    axs["histy"].fill_betweenx(xs, ys, color=PINK)
    axs["scatter"].set_xlabel("Distance TC (km)")
    axs["scatter"].set_ylabel("Distance Voiture (km)")
    axs["scatter"].set_xlim(0, max_dist)
    axs["histx"].set_xlim(0, max_dist)
    axs["histx"].set_ylim(bottom=0)
    axs["scatter"].set_ylim(0, max_dist)
    axs["histy"].set_xlim(left=0)
    axs["histy"].set_ylim(0, max_dist)
    axs["histx"].tick_params(axis="x", labelbottom=False)
    axs["histy"].tick_params(axis="y", labelleft=False)
    axs["histx"].tick_params(axis="y", which="both", length=0, labelleft=False)
    axs["histy"].tick_params(axis="x", which="both", length=0, labelbottom=False)
    axs["scatter"].set_yticks(axs["scatter"].get_xticks())
    sns.despine(ax=axs["histx"], top=True, right=True)
    sns.despine(ax=axs["histy"], top=True, right=True)
    # fig.tight_layout()
    fig.savefig("./output/graphs/pt_vs_car_dist.png")


def pt_entry_exit_modes_bars(results: dict, filename: str):
    # Horizontal bar chart of PT modes.
    results = dict(sorted(results.items(), key=lambda i: i[1]["share_weighted_trips"]))
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.4)
    else:
        fig, ax = get_figure(ratio=0.5, fraction=0.6)
    if LANGUAGE == "FR":
        labels = [PT_MODE_LABELS_FR[k] for k in results.keys()]
        xlabel = "Part"
    elif LANGUAGE == "EN":
        labels = [PT_MODE_LABELS_EN[k] for k in results.keys()]
        xlabel = "Share"
    widths = [v["share_weighted_trips"] for v in results.values()]
    colors = [PT_MODE_COLORS[k] for k in results.keys()]
    bars_inter = ax.barh(
        y=labels,
        width=widths,
        height=0.9,
        color=colors,
        align="center",
        zorder=1,
    )
    ax.bar_label(bars_inter, fmt="{:.0%}", padding=5, zorder=3)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlim(left=0)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_xlabel(xlabel)
    ax.grid(which="major", axis="x", zorder=2)
    sns.despine(top=True, right=True)
    fig.tight_layout(pad=0.5)
    fig.savefig(add_extension(filename))


def density_flows_polar_plot(cat_matrix: pl.DataFrame, filename: str):
    cats = cat_matrix["origin_cat"].unique().sort()
    cat_coords = {cat: i for i, cat in enumerate(cats)}
    cat_matrix = cat_matrix.with_columns(
        origin_y=pl.col("origin_cat").replace_strict(cat_coords),
        destination_y=pl.col("destination_cat").replace_strict(cat_coords),
    )
    if DOC_TYPE == "poster":
        fig, ax = get_figure(ratio=0.9, subplot_kw={"projection": "polar"})
        width = 30
    else:
        fig, ax = get_figure(ratio=1.0, fraction=0.6, subplot_kw={"projection": "polar"})
        width = 12
    if LANGUAGE == "FR":
        label_dict = DENSITY_LABELS_FR
    elif LANGUAGE == "EN":
        label_dict = DENSITY_LABELS_EN
    vmax = cat_matrix["car_then_pt_weight"].max()
    margin = 0.1
    # Add circles.
    for i, cat in enumerate(cats):
        ax.fill_between(
            np.linspace(0, 2 * pi, 200),
            np.repeat(i, 200),
            np.repeat(i + 1 - margin, 200),
            color=REDS[i],
        )
        ax.text(pi / 2, i + 0.4, label_dict[cat], ha="center", va="center", color=BLACK, alpha=0.9)
    for row in cat_matrix.sort("car_then_pt_weight", descending=True).iter_rows(named=True):
        if row["origin_cat"] == row["destination_cat"]:
            # Skip self flows.
            continue
        v = row["car_then_pt_weight"] / vmax
        d = abs(row["origin_y"] - row["destination_y"]) - 1
        if row["origin_y"] > row["destination_y"]:
            theta = pi + d * pi / 8
            pad = margin / 2
        else:
            theta = 0 - d * pi / 8
            pad = -margin / 2
        linewidth = width * v
        curve = 0.3 * d
        ax.annotate(
            "",
            xy=(theta, row["destination_y"] + 0.5 + pad),
            xytext=(theta, row["origin_y"] + 0.5 - pad),
            arrowprops=dict(
                arrowstyle="-|>",
                connectionstyle=f"arc3,rad={curve}",
                color=BLUE,
                capstyle="butt",
                joinstyle="miter",
                linewidth=linewidth,
                shrinkA=0,
                shrinkB=0,
            ),
        )
    ax.set_rmax(4)
    ax.set_xticks([])
    ax.set_rticks([1, 2, 3, 4])
    # ax.set_rlabel_position(90)
    ax.tick_params(labelleft=False)
    ax.grid(False)
    ax.axis("off")
    # sns.despine(top=True)
    fig.tight_layout()
    fig.savefig(add_extension(filename))


# def insee_density_matrix():
#     cats = x["start_cat"].unique().sort(descending=True)
#     cat_coords = {cat: i for i, cat in enumerate(cats)}
#     circle_size = 15000

#     fig, ax = get_figure(ratio=1.0)
#     ax.arrow(x=0, y=len(cats), dx=0, dy=-len(cats) + 0.5, width=0.05, color=COLORS[3])
#     ax.arrow(x=len(cats), y=0, dx=-len(cats) + 0.5, dy=0, width=0.05, color=COLORS[3])
#     ax.annotate("Plus dense", (0, len(cats) / 2), color=COLORS[3], rotation=90, ha="right", va="center")
#     ax.annotate("Plus dense", (len(cats) / 2, 0), color=COLORS[3], ha="center", va="bottom")
#     ax.scatter(
#         x["end_cat"].replace_strict(cat_coords) + 1,
#         x["start_cat"].replace_strict(cat_coords) + 1,
#         s=circle_size * x["tot_weight"] / x["tot_weight"].max(),
#         color="w",
#         # cmap="Blues",
#         # vmin=0,
#         edgecolor=COLORS[5],
#     )
#     vmax = x["inter_share"].max()
#     ax.set_aspect("equal")
#     ticks = np.arange(len(cats) + 1)
#     labels = [""] + cats.replace_strict(DENSITY_LABELS).to_list()
#     ax.set_xticks(ticks, labels=labels)
#     ax.set_yticks(ticks, labels=labels)
#     ax.tick_params(bottom=False, left=False, labeltop=True, labelbottom=False)
#     ax.set_xlabel("Vers")
#     ax.xaxis.set_label_position("top")
#     ax.set_ylabel("Depuis")
#     ax.set_xlim(-0.5, len(cats) + 0.5)
#     ax.set_ylim(-0.5, len(cats) + 0.5)
#     ax.tick_params(axis="x", rotation=70)
#     ax.yaxis.set_inverted(True)
#     sns.despine(bottom=True, left=True)
#     fig.tight_layout()
#     fig.savefig("./output/graphs/insee_density_matrix.png")


# def insee_density_flows():
#     start_shares = (
#         x.group_by("start_cat")
#         .agg(w=pl.col("inter_weight").sum())
#         .with_columns(share=pl.col("w") / pl.col("w").sum())
#         .sort("start_cat", descending=True)
#     )
#     end_shares = (
#         x.group_by("end_cat")
#         .agg(w=pl.col("inter_weight").sum())
#         .with_columns(share=pl.col("w") / pl.col("w").sum())
#         .sort("end_cat", descending=True)
#     )

#     def draw_flow(x0, y0, x1, y1, width, color):
#         """Draw a Bezier curve with given thickness and color."""
#         Path = mpath.Path
#         verts = [
#             (x0, y0 - width / 2),  # bottom-left
#             (x0 + 0.3, y0 - width / 2),  # curve control
#             (x1 - 0.3, y1 - width / 2),
#             (x1, y1 - width / 2),
#             (x1, y1 + width / 2),  # top-right
#             (x1 - 0.3, y1 + width / 2),
#             (x0 + 0.3, y0 + width / 2),
#             (x0, y0 + width / 2),
#             (x0, y0 - width / 2),  # close path
#         ]
#         codes = [
#             Path.MOVETO,
#             Path.CURVE4,
#             Path.CURVE4,
#             Path.CURVE4,
#             Path.LINETO,
#             Path.CURVE4,
#             Path.CURVE4,
#             Path.CURVE4,
#             Path.CLOSEPOLY,
#         ]
#         path = Path(verts, codes)
#         patch = mpatches.PathPatch(path, facecolor=color, edgecolor="none", alpha=0.9)
#         ax.add_patch(patch)

#     fig, ax = get_figure(ratio=0.8)
#     # Scale factor for flow thickness
#     scale = 0.236 / x["inter_weight"].max()
#     # Draw flows
#     x = (
#         x.sort("end_cat", "start_cat", descending=[True, True])
#         .with_columns(
#             y_right=(pl.col("inter_weight").cum_sum() - pl.col("inter_weight"))
#             / pl.col("inter_weight").sum(),
#         )
#         .sort("start_cat", "end_cat", descending=[True, True])
#         .with_columns(
#             y_left=(pl.col("inter_weight").cum_sum() - pl.col("inter_weight"))
#             / pl.col("inter_weight").sum(),
#         )
#     )
#     for row in x.sort("inter_weight").iter_rows(named=True):
#         s = row["start_cat"]
#         t = row["end_cat"]
#         y0 = row["y_left"]
#         y1 = row["y_right"]
#         w = row["inter_weight"]
#         i = cat_coords[s]
#         j = cat_coords[t]
#         color = COLORS[i]
#         # color = "black"
#         width = w * scale
#         draw_flow(0, y0 + width / 2, 1, y1 + width / 2, width, color)
#     # Draw nodes as rectangles
#     for i, (y, s) in enumerate(zip(ys0, start_shares["share"])):
#         color = COLORS[i]
#         ax.add_patch(plt.Rectangle((-0.05, y - s / 2), 0.05, s, facecolor=color, edgecolor="black"))
#         label = "{}\n{:.0%}".format(DENSITY_LABELS[cats[i]], s)
#         ax.text(
#             -0.06,
#             y,
#             label,
#             ha="right",
#             va="center",
#             color=color,
#             fontweight="bold",
#             path_effects=[pe.withStroke(linewidth=1, foreground="black")],
#         )
#     for i, (y, s) in enumerate(zip(ys1, end_shares["share"])):
#         color = COLORS[i]
#         ax.add_patch(plt.Rectangle((1, y - s / 2), 0.05, s, facecolor=color, edgecolor="black"))
#         label = "{}\n{:.0%}".format(DENSITY_LABELS[cats[i]], s)
#         ax.text(
#             1.06,
#             y,
#             label,
#             ha="left",
#             va="center",
#             color=color,
#             fontweight="bold",
#             path_effects=[pe.withStroke(linewidth=1, foreground="black")],
#         )
#     ax.set_xlim(-0.1, 1.1)
#     ax.set_ylim(0.0, 1.05)
#     ax.set_xticks([0, 1], labels=["Origine", "Destination"], fontweight="bold")
#     ax.tick_params(bottom=False, left=False, labelleft=False, labeltop=True, labelbottom=False)
#     sns.despine(bottom=True, left=True)
#     fig.tight_layout()
#     fig.savefig("./output/graphs/insee_density_flows.png")
