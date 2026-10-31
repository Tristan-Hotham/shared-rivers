"""README.md and LICENSE, numbers from data/results.json; also checks the numbers in reddit/post.md."""
import re
from common import *

R = jload(f"{DATA}/results.json")
b, r, c = R["basins"], R["rivers"], R["countries"]
size = lambda f: f"{os.path.getsize(os.path.join(ROOT, f)) / 1e6:.1f} MB"

post = open(os.path.join(ROOT, "reddit", "post.md"), encoding="utf-8").read()
for s in (f"{b['n']} river basins", f"{b['area_pct']:.0f}% of the world's land", f"{b['pop_pct']:.0f}% of its people", f"shared by {b['top'][0]['n']} countries",
          f"just two neighbours", f"({b['n_2']})", f"Nile and the Niger {b['top'][1]['n']} each", f"Congo {b['top'][3]['n']}",
          f"Nile comes out at {r['top'][0]['len']:,} km", f"Yangtze {r['top'][1]['len']:,}", f"Amazon {r['top'][2]['len']:,}", "Nile 6,650 km"):
    assert s in post, s
for bad in ("—", "–", "--"):
    assert bad not in post

readme = f"""# Who shares the world's rivers?

A world map of the {b['n']} river basins shared by two or more countries, the share of each basin in each country, the rivers that drain them measured end to end on one map, and the countries that depend most on water from upstream. Built from the Transboundary Freshwater Dispute Database (Oregon State University), Natural Earth and FAO AQUASTAT.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.23848927}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/shared-rivers/}}

![Who shares the world's rivers?](header.png)

## Headline results

- Shared basins: {b['n']} international basins drain {b['area_pct']:.1f}% of the world's land outside Antarctica and held {b['pop_bn']:.1f} billion people in 2022 ({b['pop_pct']:.1f}% of the world). {b['n_2']} are shared by two countries and {b['n_5plus']} by five or more.
- Most shared: the Danube basin ({b['top'][0]['n']} countries), the Nile and the Niger ({b['top'][1]['n']} each), the Congo ({b['top'][3]['n']}) and the Rhine and Meuse ({b['top'][4]['n']}). Disputed areas listed by the TFDD (such as Abyei or Aksai Chin) are not counted as countries.
- Most populous: the Ganges, Brahmaputra and Meghna basin ({b['most_pop'][0]['pop_m']:,} million people), then the Nile ({b['most_pop'][1]['pop_m']:,} million) and the Indus ({b['most_pop'][2]['pop_m']:,} million). {c['n_full']} countries have at least 99% of their land in shared basins.
- Longest rivers on one map: measured mouth to most distant source on the Natural Earth 1:10m lines, the Nile ({r['top'][0]['len']:,} km), the {r['top'][1]['name']} ({r['top'][1]['len']:,} km) and the {r['top'][2]['name']} ({r['top'][2]['len']:,} km). These are {r['amazon']['ratio']:.0f}% to {r['nile']['ratio']:.0f}% of Britannica's lengths and shrink further on coarser lines: the choice of source, mouth and map scale decides the ranking.
- Rivers across borders: the Danube flows through or along {r['named_top'][0]['n']} countries on the map (the usual count is ten; Moldova's short bank does not register at this scale), the {r['named_top'][1]['name']} and the {r['named_top'][2]['name']} {r['named_top'][1]['n']} each.
- Water from abroad (AQUASTAT dependency ratio, 2013 to 2017): more than half of the renewable water comes from outside the country for {c['dep_n_over50']} of {c['dep_n']} countries, including Egypt ({c['dep_egy']:.0f}%), Turkmenistan ({c['dep_tkm']:.0f}%), Hungary ({c['dep_hun']:.0f}%), Bangladesh ({c['dep_bgd']:.0f}%) and the Netherlands ({c['dep_nld']:.0f}%).

## Files

| Path | What |
|---|---|
| `index.html` | The interactive page (Leaflet; static, no build step) |
| `data/basins.csv` | {b['n']} international basins: countries (ISO3), disputed areas, area, population 2022 |
| `data/basin_countries.csv` | {b['n_bcu']} basin country units: each country's area and share of each basin |
| `data/countries.csv` | Each country's land in shared basins, number of basins, AQUASTAT dependency ratio |
| `data/river_systems.csv` | The 80 longest river systems on the Natural Earth lines: length at 1:10m and 1:50m, path, countries, basin |
| `data/named_rivers.csv` | Named rivers of at least 250 km: map length and countries along the course |
| `data/basins.geojson`, `data/bcu.geojson` | Simplified basin and basin country unit outlines ({size('data/basins.geojson')}, {size('data/bcu.geojson')}) |
| `data/rivers.geojson`, `data/mainstems.geojson` | River network as used on the page, and the longest path of the 40 longest systems |
| `data/results.json` | Every number quoted on the page, in the paper, blog and Reddit post |
| `code/` | Numbered scripts from the raw files to everything here |
| `release/paper/` | Paper (PDF and LaTeX) and its figures |
| `release/blog/` | Blog post (WordPress block markup), figures and metadata |
| `release/zenodo/` | Files and metadata for the Zenodo record |
| `reddit/` | Collage, the script that draws it, and the post |

## Method

Basins are the TFDD's 2024 register of international basins (countries, area, population) with the 2018 polygons of {b['n_poly']} of them and their basin country units. Countries are sovereign states; the West Bank is counted as Palestine and French Guiana as France. The share of world land is the TFDD basin area over the Natural Earth land outside Antarctica.

Rivers: the {r['n_lines']:,} Natural Earth 1:10m river and lake centrelines are split and joined (tolerance 0.02 degrees) into a network; canals, the Casiquiare, the Ferenc csatorna and the Kovzha are left out so that separate rivers stay separate. Mouths are line ends within 3 km of the sea or of five terminal lakes. Each node is assigned to its nearest mouth (multi-source Dijkstra on geodesic length), delta mouths are merged, and a system's length is the network distance to its most distant source. The same is measured on the 1:50m lines, and on the 1:10m paths simplified at tolerances up to 0.5 degrees. Countries along a river come from points every kilometre (at least 1 km inside, or 5 km within about 1.5 km of a border).

The paper in `release/paper/` sets out every step and limitation.

## Sources and licences

- Transboundary Freshwater Dispute Database, Oregon State University: International River Basins, 2024 basin master table (as published in github.com/SharedWatersLab/geography) and 2018 basins and basin country units (as published in github.com/hannahkfriedrich/tfdd). McCracken, M. and Wolf, A. T. (2019) Updating the Register of International River Basins of the world, International Journal of Water Resources Development 35(5). The TFDD makes its data freely available for research with credit; the derived tables here are shared on the same terms (non-commercial research, credit the TFDD).
- Natural Earth 1:10m and 1:50m rivers and lake centrelines, lakes, land and countries, populated places. Public domain.
- FAO AQUASTAT, as downloaded in 2017 and published in github.com/cmawer/pycon-2017-eda-tutorial. CC BY-NC-SA 3.0 IGO; the dependency ratio column in `data/countries.csv` is under that licence.
- World Bank, World Development Indicators, SP.POP.TOTL. CC BY 4.0.
- Encyclopaedia Britannica, for three published river lengths quoted for comparison (`code/published_lengths.csv`).
- Base map tiles on the page: Esri.

Code: MIT. Text, figures and the remaining derived data: CC BY 4.0. See LICENSE.

## How to rerun

The raw files are read in place from the paths in `code/common.py`. With Python 3, geopandas/shapely 2, networkx, pyproj, scipy, matplotlib and xelatex:

```
cd code
python3 01_basins.py && python3 02_rivers.py && python3 03_results.py && python3 04_site.py
python3 05_figures.py && python3 06_header.py && python3 07_paper.py && python3 08_release.py && python3 09_readme.py
python3 ../reddit/collage.py
```

Set `DOI=10.5281/zenodo.NNN` when running `07_paper.py` and `08_release.py` to print the DOI. `node code/qa.js http://localhost:PORT/` takes screenshots at desktop and phone widths.

## Citation

Hotham, T. (2026) Who shares the world's rivers? International river basins, river lengths measured on one map, and the countries that depend on water from upstream. Zenodo. {{https://doi.org/10.5281/zenodo.23848927}}

Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("|---|---|", ""), bad   # the markdown table rule is not visible text
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
LIC = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and data

Text, figures and derived data are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/, with these exceptions:
- Tables derived from the Transboundary Freshwater Dispute Database (data/basins.csv, data/basin_countries.csv,
  data/basins.geojson, data/bcu.geojson and the basin columns elsewhere) are shared for non-commercial research with
  credit to the TFDD, Oregon State University, as the TFDD asks.
- The AQUASTAT dependency ratio and renewable water columns in data/countries.csv are FAO data under CC BY-NC-SA 3.0 IGO.
- Natural Earth data are in the public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)
print("README.md", len(readme.split()), "words")
