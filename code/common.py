"""Shared paths and helpers for the shared-rivers study.

Raw inputs (read in place, never copied into the repo):
  RAWS/ne/       Natural Earth 1:10m vectors from github.com/nvkelso/natural-earth-vector (public domain):
                 ne_10m_rivers_lake_centerlines_scale_rank.geojson, ne_10m_lakes.geojson, ne_10m_land.geojson,
                 ne_10m_coastline.geojson, ne_10m_geography_marine_polys.geojson
  RAWS/tfdd/     Transboundary Freshwater Dispute Database (Oregon State University):
                 Basin310_Master_20180511.geojson and BCU310_Master_20180511.geojson (the 2018 spatial update, as
                 published in github.com/hannahkfriedrich/tfdd/assets) and BasinMaster313_20240807.csv (the 2024
                 basin master table, from github.com/SharedWatersLab/geography/notebooks)
  RAWS/aquastat/ pycon_aquastat.csv.gzip: FAO AQUASTAT country table (all variables, five-year periods to 2013-2017),
                 as downloaded from AQUASTAT in 2017 and published in github.com/cmawer/pycon-2017-eda-tutorial/data
  GEO/           Natural Earth 1:10m and 1:50m countries (public domain), supplied with the brief
  WB             World Bank World Development Indicators, total population SP.POP.TOTL (CC BY 4.0)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWS = "/home/claude/newdata/raw3/shared-rivers"
GEO = "/home/claude/newdata/raw/geo"
WB = "/home/claude/newdata/raw/wb/population.csv"
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("RIVERTMP", "/dev/shm/shared-rivers")   # intermediates live in memory, not in the repo
FIG = os.path.join(WORK, "fig")
FONTS = "/home/claude/ref/fonts"
for d in (DATA, WORK, FIG):
    os.makedirs(d, exist_ok=True)

SLUG = "shared-rivers"
PAGE = "https://maps.tristanhotham.com/shared-rivers/"
REPO = "https://github.com/Tristan-Hotham/shared-rivers"
DOI = "10.5281/zenodo.23848927"
BLOG = "https://blog.tristanhotham.com/2026/10/31/shared-rivers/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")


# number of countries sharing a basin: [low, high, label, colour]; AQUASTAT dependency ratio bins (same on page and figures)
NBINS = [(2, 2, "2", "#CFE6DF"), (3, 3, "3", "#97CCC6"), (4, 4, "4", "#5DABB3"), (5, 6, "5 to 6", "#3586A3"), (7, 9, "7 to 9", "#2D5791"), (10, 99, "10 or more", "#3A2C6E")]
DBINS = [(0, 10, "under 10%", "#F1E8D8"), (10, 25, "10 to 25%", "#EACB9C"), (25, 50, "25 to 50%", "#DDA063"), (50, 75, "50 to 75%", "#C66F3C"), (75, 90, "75 to 90%", "#A2462A"), (90, 101, "90% or more", "#6B271C")]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    """Number formats used by the {{path|format}} tokens in every template."""
    if f is None or f == "raw":
        return str(v)
    if f == "int":
        return f"{round(float(v)):,}"
    if f == "pc":
        return f"{round(float(v))}%"
    if f == "pc1":
        return f"{float(v):.1f}%"
    if f == "f1":
        return f"{float(v):.1f}"
    if f == "m":      # millions, no decimals
        return f"{round(float(v) / 1e6):,} million"
    if f == "bn":     # billions, one decimal
        return f"{float(v) / 1e9:.1f} billion"
    if f == "mkm2":   # million km2, one decimal
        return f"{float(v) / 1e6:.1f} million"
    raise ValueError(f)


def fill(text, R, esc=None):
    """Replace {{path|format}} tokens (but not {{IMG|...}}, 10.5281/zenodo.23848927, https://blog.tristanhotham.com/2026/10/31/shared-rivers/, https://doi.org/10.5281/zenodo.23848927 or {{TABLE_...}})."""
    def rep(m):
        s = fmt(get(R, m.group(1)), m.group(3))
        return esc(s) if esc else s
    return re.sub(r"\{\{(?!IMG\||DOI\}|BLOG_URL\}|DOI_URL\}|TABLE_)([^}|]+)(\|(\w+))?\}\}", rep, text)
