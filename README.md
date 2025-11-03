# Aggregating Mobility Surveys to Understand Intermodality: Evidence from 78 French Surveys

This repository contains the code I use to analyze intermodality trips by aggregating French
mobility surveys.

The [MobiSurvStd](https://mobisurvstd.github.io/MobiSurvStd/) library is used to standardize the
mobility surveys.

## Requirements

- Python environment with the packages listed in `pyproject.toml` (I recommend using uv)
- R with the libraries `arrow` and `icarus`
- A set of mobility surveys standardized with MobiSurvStd (the 78 surveys that I use are not
  open-data)
- INSEE data on the [municipalities' density level](https://www.insee.fr/fr/information/8571524)
  (for survey re-weighting)
- INSEE data on the [census](https://www.insee.fr/fr/statistiques/8647014) (for survey re-weighting)
- A file with the location of public-transit stops in France with column `stop_name`, `slug` (AOM
  code), `modes` (list of modes served by the stop), and `geometry`. This file is only used for the
  last part of the code. Contact me if you need it.
- LaTeX (to generate the paper PDF)
- [Typst](https://typst.app/) (to generate the poster)

## How to run

1. Go through all the Python files and modify the global configuration variables when needed. All
   theses configuration variables are in uppercase. The main configuration variables are in
   `main.py`, `weighting.py`, and `mpl.py`. They are used to specify the path for the input and
   output files and to configure the language, size, format, labels, etc. of the graphs.
2. Run the main script `main.py` with Python. For example, if you use `uv`, use
   `uv run python src/intermodality_analysis/main.py`.
3. You can access the result values in `output/results.json` (default path) and the generated graphs
   in `output/paper_graphs` (for paper) or `output/poster_graphs` (for poster).
4. (Optional) To generate the paper PDF, run LaTeX on the file `docs/wctr/wctr_javaudin.tex`
   to PDF. Note that the result values need to be manually changed.
5. (Optional) To generate the poster PDF, run Typst on the file
   `docs/poster/intermodality_poster.typ`. From the main directory:
   `typst compile docs/poster/main.typ --root .`.
   Note that the result values are automatically updated from the values in `output/results.json`.

## License

The Python and R codes are licensed under the [MIT license](https://mit-license.org/).
Feel free to modify and redistribute them for your cool projects with MobiSurvStd!

The LaTeX and Typst files are copyrighted and all rights are reserved.
You may NOT use, copy, modify, or distribute this code without my explicit permission.
