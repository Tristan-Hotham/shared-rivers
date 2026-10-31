"""Shared drawing helpers for the static figures, the header and the collage: fonts, the study palette (the same
colours as the page), and Natural Earth countries, TFDD basins and rivers in the Equal Earth projection."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, PathPatch
from matplotlib.path import Path
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib import patheffects as pe
from pyproj import Transformer
from shapely.geometry import shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FONTS, f))
DISP = fm.FontProperties(fname=os.path.join(FONTS, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#5E6873", "axes.labelcolor": "#14202B",
                     "xtick.color": "#5E6873", "ytick.color": "#5E6873", "svg.fonttype": "none"})
BG, FG, MUT, RULE, PAPER = "#F5F3EE", "#14202B", "#5E6873", "#DDD7CB", "#FCFBF8"
LAND, SEA, RIVER, HOT, GOLD = "#E7E2D6", "#E4ECEE", "#2563A6", "#B5442E", "#D19A1C"
NCOL = lambda n: next(c for a, b, _, c in NBINS if a <= n <= b)
DCOL = lambda v: next(c for a, b, _, c in DBINS if a <= v < b)

TR = Transformer.from_crs(4326, 8857, always_xy=True)   # Equal Earth
WORLD_EXT = (-12.6e6, 15.9e6, -6.25e6, 8.45e6)


def proj_rings(geom):
    out = []
    for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
        for ring in [poly.exterior] + list(poly.interiors):
            c = np.asarray(ring.coords)
            x, y = TR.transform(np.clip(c[:, 0], -179.99, 179.99), c[:, 1])
            out.append(np.column_stack([x, y]))
    return out


def poly_patch(geom, **kw):
    """One PathPatch per (multi)polygon, holes included."""
    verts, codes = [], []
    for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
        for ring in [poly.exterior] + list(poly.interiors):
            c = np.asarray(ring.coords)
            x, y = TR.transform(np.clip(c[:, 0], -179.99, 179.99), c[:, 1])
            v = np.column_stack([x, y])
            verts.append(v); codes += [Path.MOVETO] + [Path.LINETO] * (len(v) - 2) + [Path.CLOSEPOLY]
    return PathPatch(Path(np.concatenate(verts), codes), **kw)


_C = None


def countries():
    global _C
    if _C is None:
        NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
        _C = []
        for f in NE["features"]:
            p = f["properties"]
            iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else {"SOL": "SOM", "KOS": "XKX", "CYN": "CYP"}.get(p["ADM0_A3"], p["ADM0_A3"])
            if p["ADM0_A3"] == "ATA":
                continue
            _C.append((iso, shape(f["geometry"]).buffer(0)))
    return _C


_B = None


def basins():
    global _B
    if _B is None:
        _B = [(f["properties"]["BCODE"], shape(f["geometry"]).buffer(0)) for f in jload(f"{RAWS}/tfdd/Basin310_Master_20180511.geojson")["features"]]
    return _B


_R = None


def rivers(max_rank=6):
    """Projected river lines and their Natural Earth stroke weights."""
    global _R
    if _R is None:
        _R = []
        for f in jload(f"{RAWS}/ne/ne_10m_rivers_lake_centerlines_scale_rank.geojson")["features"]:
            p = f["properties"]
            if p["featurecla"] == "Canal":
                continue
            g = shape(f["geometry"])
            for ln in (g.geoms if g.geom_type == "MultiLineString" else [g]):
                c = np.asarray(ln.coords)
                x, y = TR.transform(np.clip(c[:, 0], -179.99, 179.99), c[:, 1])
                _R.append((p["scalerank"], p["strokeweig"] or .2, np.column_stack([x, y])))
    return [r for r in _R if r[0] <= max_rank]


def draw_world(ax, fill=lambda iso: None, ec="#FFFFFF", lw=.3, extent=WORLD_EXT, land=LAND):
    for iso, g in countries():
        ax.add_patch(poly_patch(g, fc=fill(iso) or land, ec=ec, lw=lw, zorder=1))
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); ax.set_aspect("equal"); ax.axis("off")


def draw_rivers(ax, max_rank=6, colour=RIVER, scale=1.0, alpha=.9, z=4):
    segs, lws = [], []
    for rk, w, xy in rivers(max_rank):
        segs.append(xy); lws.append(scale * (0.25 + 1.6 * min(w, 2.0)) * (1.25 if rk <= 2 else 1.0))
    ax.add_collection(LineCollection(segs, linewidths=lws, colors=colour, alpha=alpha, zorder=z, capstyle="round", joinstyle="round"))


def halo(w=3, c=None):
    return [pe.withStroke(linewidth=w, foreground=c or BG)]


def xy(lon, lat):
    return TR.transform(lon, lat)


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
