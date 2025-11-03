# Copyright 2025 Lucas Javaudin
# SPDX-License-Identifier: MIT
import os

import matplotlib as mpl
import matplotlib.pyplot as plt

# poster or paper
DOC_TYPE = "poster"

# Define a color palette from Okabe and Ito.
ORANGE = "#E69F00"
LIGHTBLUE = "#56B4E9"
GREEN = "#009E73"
YELLOW = "#F0E442"
BLUE = "#0072B2"
RED = "#D55E00"
PINK = "#CC79A7"
BLACK = "#000000"
COLORS = [ORANGE, LIGHTBLUE, GREEN, YELLOW, BLUE, RED, PINK, BLACK]

PURPLE = "#9932CC"
TEAL = "#008080"

# Sequential colorscales with 4 colors.
BLUES = mpl.colormaps["tab20c"].colors[:4]
REDS = mpl.colormaps["tab20c"].colors[4:8]

# Width of the output document (in pixel), required to define graph size.
if DOC_TYPE == "poster":
    # Directory where the generated graphs should be stored.
    GRAPH_DIR = "./output/poster_graphs/"
    # Width of the text on the poster.
    WIDTH = 750
    # Define font parameters for matplotlib.
    PARAMETERS = {
        "figure.dpi": 300,
        "font.size": 26,
        "font.serif": ["Times New Roman"],
        "font.sans-serif": ["Roboto", "DejaVu Sans"],
        "font.monospace": [],
        "axes.labelsize": 33,
        "axes.titlesize": 40,
        "axes.linewidth": 1.0,
        "legend.fontsize": 26,
        "xtick.labelsize": 26,
        "ytick.labelsize": 26,
        "font.family": "sans-serif",
    }
    plt.rcParams.update(PARAMETERS)
    OUTPUT_FORMAT = "png"
    LANGUAGE = "FR"
elif DOC_TYPE == "paper":
    # Directory where the generated graphs should be stored.
    GRAPH_DIR = "./output/paper_graphs/"
    # Width of the text on the paper.
    WIDTH = 468
    # Define font parameters for matplotlib.
    PARAMETERS = {
        "figure.dpi": 300,
        "font.size": 8,
        "font.serif": ["Liberation"],
        "font.sans-serif": ["Roboto", "DejaVu Sans"],
        "font.monospace": [],
        "axes.labelsize": 8,
        "axes.titlesize": 10,
        "axes.linewidth": 1.0,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "font.family": "Times New Roman",
    }
    plt.rcParams.update(PARAMETERS)
    OUTPUT_FORMAT = "pdf"
    LANGUAGE = "EN"

if not os.path.isdir(GRAPH_DIR):
    os.makedirs(GRAPH_DIR)


def set_size(ratio: str | float = "golden", fraction=1.0):
    """Returns the dimension (width, height) in inches of a figure given its ratio (height / width)
    and the farction of the document width that it should take.
    """
    # Width of figure (in pts)
    fig_width_pt = WIDTH * fraction
    # Convert from pt to inches
    inches_per_pt = 1 / 72.27
    if ratio == "golden":
        ratio = (5**0.5 - 1) / 2
    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    fig_height_in = fig_width_in * float(ratio)
    fig_dim = (fig_width_in, fig_height_in)
    return fig_dim


def get_figure(ratio="golden", fraction=1.0, subplot_kw=None):
    """Returns a matplotlib Figure and Axes with the correct size."""
    fig, ax = plt.subplots(figsize=set_size(ratio, fraction), subplot_kw=subplot_kw)
    return fig, ax
