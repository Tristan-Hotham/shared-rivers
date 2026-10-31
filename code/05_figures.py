"""Static figures for the paper (WORK/fig/f_*.png, copied to release/paper) and the blog (release/blog/b_*.png).
All numbers come from data/results.json or the derived tables."""
import shutil
from shapely.geometry import shape, box
from shapely.ops import unary_union
from figlib import *

R = jload(f"{DATA}/results.json"); B = jload(f"{WORK}/basins.json")["basins"]; C = jload(f"{WORK}/countries.json"); S = jload(f"{WORK}/systems.json")
PAPERD = os.path.join(ROOT, "release", "paper"); BLOGD = os.path.join(ROOT, "release", "blog")
for d in (PAPERD, BLOGD):
    os.makedirs(d, exist_ok=True)
CN = lambda i: C[i]["name"] if i in C else i


def out(fig, name, blog=None):
    p = f"{FIG}/{name}.png"
    save(fig, p)
    shutil.copy(p, f"{PAPERD}/{name}.png")
    if blog:
        shutil.copy(p, f"{BLOGD}/{blog}.png")


def legend_boxes(fig, x, y, items, title=None, size=10.5, dx=.105):
    if title:
        fig.text(x, y + .028, title, fontsize=size, color=FG, family=MONO, weight="medium")
    for k, (lab, col) in enumerate(items):
        fig.patches.append(matplotlib.patches.Rectangle((x + k * dx, y), .018, .018, transform=fig.transFigure, fc=col, ec="#00000022", lw=.5))
        fig.text(x + k * dx + .024, y + .009, lab, fontsize=size, color=FG, va="center", family=MONO)


# ---------- 1. world map of shared basins ----------
def world_basins(name, blog):
    fig = plt.figure(figsize=(12, 7.0), facecolor=BG)
    ax = fig.add_axes([0, .11, 1, .89]); ax.set_facecolor(BG)
    draw_world(ax, ec="#FFFFFF", lw=.35)
    for code, g in basins():
        ax.add_patch(poly_patch(g, fc=NCOL(B[code]["n"]), ec="#FFFFFF", lw=.25, zorder=2, alpha=.95))
    draw_world(ax, fill=lambda i: "none", ec="#FFFFFF55", lw=.25, land="none")
    draw_rivers(ax, max_rank=5, scale=.55, alpha=.85)
    legend_boxes(fig, .05, .052, [(b[2], b[3]) for b in NBINS], title="Countries sharing the basin", dx=.1)
    fig.text(.05, .012, "Basins: TFDD (Oregon State University). Rivers and outlines: Natural Earth.", ha="left", fontsize=9, color=MUT)
    out(fig, name, blog)


if not os.environ.get("ONLY") or "world" in os.environ["ONLY"]:
    world_basins("f_world_basins", "b_world_basins")


# ---------- 2. basins shared by most countries, split by area ----------
def share_bars(name, blog, n=16):
    rows = R["basins"]["top"][:n]
    fig = plt.figure(figsize=(11, 7.4), facecolor=BG)
    ax = fig.add_axes([.24, .08, .7, .86]); ax.set_facecolor(BG)
    pal = ["#2D5791", "#3586A3", "#5DABB3", "#97CCC6", "#CFE6DF"]
    for i, r in enumerate(rows):
        x = 0
        for j, (k, p, a) in enumerate([s for s in B[r["code"]]["share"] if s[0] in C]):
            ax.barh(i, p, left=x, color=pal[j % 5], height=.72, edgecolor=BG, lw=.6)
            if p > 7.5:
                ax.text(x + p / 2, i, k, ha="center", va="center", fontsize=8.5, color="#FFFFFF" if j % 5 < 2 else FG)
            x += p
        ax.text(101.5, i, f"{r['n']}", va="center", fontsize=11, color=FG, weight="medium")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"] for r in rows], fontsize=10.5, family=SER)
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("share of basin area (%)", fontsize=10)
    ax.text(101.5, -1.1, "countries", fontsize=9, color=MUT)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(.24, .015, "Labels are ISO country codes. Source: TFDD 2024 register and 2018 basin country units.", fontsize=9, color=MUT)
    out(fig, name, blog)


share_bars("f_share_bars", "b_share_bars")


# ---------- 3. longest systems ----------
def lengths(name, blog, n=15):
    rows = R["rivers"]["top"][:n]; pub = {p["sys"]: p for p in R["published"]}
    fig = plt.figure(figsize=(11, 7), facecolor=BG)
    ax = fig.add_axes([.27, .1, .66, .84]); ax.set_facecolor(BG)
    for i, r in enumerate(rows):
        ax.barh(i, r["len"], color=RIVER, height=.66, alpha=.92)
        if r["len50"]:
            ax.plot([r["len50"]] * 2, [i - .42, i + .42], color=FG, lw=2)
        xe = r["len"]
        if r["name"] in pub:
            ax.plot(pub[r["name"]]["km"], i, marker="D", ms=8.5, color=HOT, mec=PAPER, mew=1.2, zorder=5)
            xe = max(xe, pub[r["name"]]["km"])
        ax.text(xe + 90, i, f"{r['len']:,}", va="center", fontsize=10.5, color=FG)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"] for r in rows], fontsize=10.5, family=SER)
    ax.invert_yaxis(); ax.set_xlim(0, 7300); ax.set_xlabel("km", fontsize=10)
    ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    from matplotlib.lines import Line2D
    h = [matplotlib.patches.Patch(color=RIVER, label="Natural Earth 1:10m, mouth to most distant source"), Line2D([], [], color=FG, lw=2, label="same on the 1:50m lines"),
         Line2D([], [], marker="D", ls="", color=HOT, mec=PAPER, ms=8, label="Encyclopaedia Britannica")]
    ax.legend(handles=h, loc="lower right", frameon=False, fontsize=9.5)
    out(fig, name, blog)


lengths("f_lengths", "b_lengths")


# ---------- 4. map scale ----------
def scale(name, blog):
    sc, tols = R["rivers"]["scale"], R["rivers"]["tols"]
    fig = plt.figure(figsize=(10, 5.6), facecolor=BG)
    ax = fig.add_axes([.09, .13, .72, .8]); ax.set_facecolor(BG)
    cols = [RIVER, HOT, "#3A8AA6", GOLD]
    ends = []
    for s, c in zip(sc, cols):
        ax.plot(range(len(tols)), s["v"], "-o", color=c, lw=2.4, ms=5)
        ends.append([s["v"][-1], f"{s['name']}  {s['v'][-1]:,} km ({100 * s['v'][-1] / s['v'][0]:.0f}%)", c])
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 170)   # keep end labels apart
    for y, t, c in ends:
        ax.text(len(tols) - .85, y, t, va="center", fontsize=10, color=c, weight="medium")
    ax.set_xticks(range(len(tols))); ax.set_xticklabels([str(t) for t in tols])
    ax.set_xlabel("simplification tolerance (degrees; 0 is the 1:10m line as drawn)", fontsize=10); ax.set_ylabel("length, km", fontsize=10)
    ax.grid(color=RULE, lw=.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    out(fig, name, blog)


scale("f_scale", "b_scale")


# ---------- 5. dependency map ----------
def dep_map(name, blog):
    fig = plt.figure(figsize=(12, 7.0), facecolor=BG)
    ax = fig.add_axes([0, .11, 1, .89]); ax.set_facecolor(BG)
    draw_world(ax, fill=lambda i: DCOL(C[i]["dep"]) if i in C and C[i].get("dep") is not None else None, ec="#FFFFFF", lw=.35)
    draw_rivers(ax, max_rank=4, scale=.45, alpha=.7)
    for iso, lab, (lx, ly), (tx, ty) in [("EGY", "Egypt", (24, 34.6), (30.5, 27)), ("TKM", "Turkmenistan", (63, 21.5), (59, 39)), ("BGD", "Bangladesh", (88.5, 14), (90, 23.5)),
                                         ("HUN", "Hungary", (-24, 44), (19.4, 47.2)), ("NLD", "Netherlands", (-22, 55), (5.5, 52.2))]:
        x, y = xy(lx, ly); x1, y1 = xy(tx, ty)
        ax.annotate(f"{lab} {C[iso]['dep']:.0f}%", xy=(x1, y1), xytext=(x, y), fontsize=10.5, color=FG, ha="center", va="center", zorder=8, family=SER,
                    path_effects=halo(3), arrowprops=dict(arrowstyle="-", color=FG, lw=.7, shrinkA=6, shrinkB=1))
    legend_boxes(fig, .05, .052, [(b[2], b[3]) for b in DBINS] + [("no value", LAND)], title="Share of renewable water from outside the country (AQUASTAT)", dx=.115)
    fig.text(.05, .012, "FAO AQUASTAT, 2013 to 2017. Outlines: Natural Earth.", ha="left", fontsize=9, color=MUT)
    out(fig, name, blog)


dep_map("f_dependency", "b_dependency")


# ---------- 6. share of land in shared basins (paper) ----------
def share_map(name):
    PB = [(0, 25, "under 25%", "#EEF1E6"), (25, 50, "25 to 50%", "#CFE6DF"), (50, 75, "50 to 75%", "#7CBDBD"), (75, 99, "75 to 99%", "#3586A3"), (99, 101, "99% or more", "#2D5791")]
    pc = lambda v: next(c for a, b, _, c in PB if a <= v < b)
    fig = plt.figure(figsize=(12, 7.0), facecolor=BG)
    ax = fig.add_axes([0, .11, 1, .89]); ax.set_facecolor(BG)
    draw_world(ax, fill=lambda i: pc(C[i]["pct_in"]) if i in C else None, ec="#FFFFFF", lw=.35)
    legend_boxes(fig, .05, .052, [(b[2], b[3]) for b in PB], title="Share of each country's land in international basins", dx=.11)
    out(fig, name)


share_map("f_share_map")


# ---------- regional maps: Danube and Nile ----------
from pyproj import Transformer


def regional(name, blog, code, lon0, lat0, ext, labels, river_ids=(), paths=(), title="", legend=None, fs=(10, 7.4)):
    tr = Transformer.from_crs(4326, f"+proj=laea +lon_0={lon0} +lat_0={lat0} +datum=WGS84", always_xy=True)

    def patch(g, **kw):
        verts, codes = [], []
        for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            for ring in [poly.exterior] + list(poly.interiors):
                c = np.asarray(ring.coords); x, y = tr.transform(c[:, 0], c[:, 1]); v = np.column_stack([x, y])
                verts.append(v); codes += [Path.MOVETO] + [Path.LINETO] * (len(v) - 2) + [Path.CLOSEPOLY]
        return PathPatch(Path(np.concatenate(verts), codes), **kw)
    bl = np.linspace(0, 1, 50)
    bx = np.concatenate([ext[0] + (ext[1] - ext[0]) * bl, np.full(50, ext[1]), ext[0] + (ext[1] - ext[0]) * bl, np.full(50, ext[0])])
    by = np.concatenate([np.full(50, ext[2]), ext[2] + (ext[3] - ext[2]) * bl, np.full(50, ext[3]), ext[2] + (ext[3] - ext[2]) * bl])
    px, py = tr.transform(bx, by)
    W = fs[0]; band = 1.0 if legend else .75
    H = W * (py.max() - py.min()) / (px.max() - px.min()) + band
    fig = plt.figure(figsize=(W, H), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1 - band / H]); ax.set_facecolor(SEA)
    fig.text(.03, 1 - .38 / H, title, fontsize=17, family=SER, weight="semibold", color=FG, va="center")
    win = box(ext[0] - 8, ext[2] - 8, ext[1] + 8, ext[3] + 8)   # ext: lon0, lon1, lat0, lat1
    NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
    for f in NE["features"]:
        g = shape(f["geometry"]).buffer(0)
        if g.intersects(win):
            ax.add_patch(patch(g.intersection(win), fc=LAND, ec="#FFFFFF", lw=.8, zorder=1))
    U = jload(f"{RAWS}/tfdd/BCU310_Master_20180511.geojson")
    units = [(f["properties"], shape(f["geometry"]).buffer(0)) for f in U["features"] if f["properties"]["BCODE"] == code]
    pal = ["#2D5791", "#3586A3", "#5DABB3", "#97CCC6", "#CFE6DF", "#3A2C6E", "#7CBDBD", "#A9C7E8", "#2C7A7B", "#B9D7D2"]
    units.sort(key=lambda u: -u[0]["Area_km2"])
    for k, (p, g) in enumerate(units):
        ax.add_patch(patch(g, fc=pal[k % len(pal)], ec="#FFFFFF", lw=.9, zorder=2, alpha=.9))
    for f in jload(f"{RAWS}/ne/ne_10m_lakes.geojson")["features"]:
        g = shape(f["geometry"])
        if g.intersects(win) and f["properties"]["scalerank"] <= 4:
            ax.add_patch(patch(g.intersection(win), fc=SEA, ec="none", zorder=3))
    for f in jload(f"{RAWS}/ne/ne_10m_rivers_lake_centerlines_scale_rank.geojson")["features"]:
        p = f["properties"]
        g = shape(f["geometry"])
        if p["featurecla"] == "Canal" or not g.intersects(win) or p["scalerank"] > 8:
            continue
        for ln in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            c = np.asarray(ln.coords); x, y = tr.transform(c[:, 0], c[:, 1])
            ax.plot(x, y, color="#0B3D78", lw=.5 + 1.6 * min(p["strokeweig"] or .2, 2), alpha=.9, zorder=4, solid_capstyle="round")
    for (pth, col, lw) in paths:
        for ln in pth:
            c = np.asarray(ln); x, y = tr.transform(c[:, 0], c[:, 1])
            ax.plot(x, y, color=col, lw=lw, zorder=5, solid_capstyle="round", alpha=.95)
    for lab, lon, lat, kw in labels:
        x, y = tr.transform(lon, lat)
        k = dict(fontsize=10.5, color=FG, ha="center", va="center", zorder=8, family=SER, path_effects=halo(2.6, "#FFFFFFDD")); k.update(kw)
        ax.text(x, y, lab, **k)
    ax.set_xlim(px.min(), px.max()); ax.set_ylim(py.min(), py.max()); ax.set_aspect("equal"); ax.axis("off")
    if legend:
        legend(fig, ax)
    out(fig, name, blog)


SYS = {s["name"]: s for s in S["systems"]}
RJ = jload(f"{DATA}/rivers.geojson")


def stem_lines(sysname):
    i = next(k for k, s in enumerate(S["systems"]) if s["name"] == sysname)
    for f in jload(f"{DATA}/mainstems.geojson")["features"]:
        if f["properties"]["s"] == i:
            g = shape(f["geometry"])
            return [np.asarray(l.coords) for l in (g.geoms if g.geom_type == "MultiLineString" else [g])]
    return []


dsh = {k: p for k, p, a in B["DANU"]["share"]}
regional("f_danube", "b_danube", "DANU", 19, 46, (5.5, 33.5, 41.0, 52.6),
         [          ("Black Sea", 32.5, 43.4, dict(fontsize=11, color=MUT, style="italic")), ("Adriatic Sea", 15.2, 42.9, dict(fontsize=11, color=MUT, style="italic")),
          (f"Romania {dsh['ROU']:.0f}%", 24.6, 45.65, {}), (f"Hungary {dsh['HUN']:.0f}%", 19.6, 47.15, {}), (f"Serbia {dsh['SRB']:.0f}%", 21.0, 43.9, {}),
          (f"Austria {dsh['AUT']:.0f}%", 14.6, 47.55, {}), (f"Germany {dsh['DEU']:.0f}%", 11.2, 48.75, {}), (f"Bulgaria {dsh['BGR']:.0f}%", 25.3, 43.45, {}),
          (f"Slovakia {dsh['SVK']:.0f}%", 19.4, 48.75, {}), (f"Croatia {dsh['HRV']:.0f}%", 16.5, 45.45, {}), (f"Bosnia and\nHerzegovina {dsh['BIH']:.0f}%", 18.0, 44.25, dict(fontsize=9)),
          (f"Ukraine {dsh['UKR']:.0f}%", 25.6, 48.2, {}), (f"Czechia {dsh['CZE']:.0f}%", 16.9, 49.55, dict(fontsize=9)), (f"Moldova {dsh['MDA']:.0f}%", 28.6, 46.6, dict(fontsize=9)),
          (f"Slovenia {dsh['SVN']:.0f}%", 14.2, 46.25, dict(fontsize=8.5)), (f"Montenegro {dsh['MNE']:.1f}%", 19.25, 42.65, dict(fontsize=8.5)),
          ("Also small parts of Switzerland, Italy,\nPoland, Albania and North Macedonia", 6.6, 43.6, dict(fontsize=9, color=MUT, ha="left"))],
         paths=[(stem_lines("Danube"), "#0B3D78", 2.6)], title=f"The Danube basin is shared by {B['DANU']['n']} countries", fs=(11, 7))

nb = S["alts"]["nile_blue"]


def nile_legend(fig, ax):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=HOT, lw=3, label=f"Longest path on the map, {R['rivers']['nile']['len']:,} km (White Nile, Kagera)"),
         Line2D([], [], color=GOLD, lw=3, label=f"Mouth to the Blue Nile's source, {R['rivers']['nile_blue']['len']:,} km")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.02, 1 - .62 / fig.get_figheight()), frameon=False, fontsize=10, ncol=1)


def blue_path():
    # the Blue Nile alternative: rebuild from rivers.geojson names along the alternative chain upstream of Khartoum
    out_l = []
    for f in RJ["features"]:
        if f["properties"]["n"] in ("El Bahr el Azraq", "Abay"):
            g = shape(f["geometry"])
            out_l += [np.asarray(l.coords) for l in (g.geoms if g.geom_type == "MultiLineString" else [g])]
    return out_l


nsh = {k: p for k, p, a in B["NILE"]["share"]}
regional("f_nile", "b_nile", "NILE", 31, 13, (19.0, 43.0, -6.8, 33.2),
         [          ("Mediterranean Sea", 26.0, 32.55, dict(fontsize=11, color=MUT, style="italic")), ("Red\nSea", 38.6, 20.0, dict(fontsize=11, color=MUT, style="italic")),
          (f"Egypt {nsh['EGY']:.0f}%", 28.0, 26.0, {}), (f"Sudan {nsh['SDN']:.0f}%", 29.2, 16.2, {}), (f"South Sudan {nsh['SSD']:.0f}%", 28.6, 8.0, {}),
          (f"Ethiopia {nsh['ETH']:.0f}%", 38.6, 10.0, {}), (f"Uganda {nsh['UGA']:.0f}%", 32.6, 2.2, {}), (f"Tanzania {nsh['TZA']:.0f}%", 34.6, -4.6, {}),
          (f"Kenya {nsh['KEN']:.0f}%", 35.6, .2, dict(fontsize=9)), (f"Eritrea {nsh['ERI']:.1f}%", 38.4, 16.6, dict(fontsize=9)),
          (f"DR Congo {nsh['COD']:.1f}%", 28.3, 2.0, dict(fontsize=9)), (f"Rwanda {nsh['RWA']:.1f}%\nBurundi {nsh['BDI']:.1f}%", 27.4, -2.4, dict(fontsize=9, ha="right")),
          ("Lake Victoria", 33.0, -1.0, dict(fontsize=8.5, color=MUT, style="italic")), ("Lake Tana", 37.3, 12.0, dict(fontsize=8.5, color=MUT, style="italic", ha="left")),
          ("Khartoum", 32.53, 15.3, dict(fontsize=9, ha="left"))],
         paths=[(stem_lines("Nile"), HOT, 3.0), (blue_path(), GOLD, 3.0)], legend=nile_legend, title=f"The Nile basin is shared by {B['NILE']['n']} countries", fs=(8.6, 11))


# ---------- 7. population ----------
def pop_bars(name, blog):
    rows = R["basins"]["most_pop"][:10]
    fig = plt.figure(figsize=(10, 5.4), facecolor=BG)
    ax = fig.add_axes([.3, .12, .62, .84]); ax.set_facecolor(BG)
    for i, r in enumerate(rows):
        ax.barh(i, r["pop_m"], color=NCOL(r["n"]), height=.66)
        ax.text(r["pop_m"] + 8, i, f"{r['pop_m']:,} m · {r['n']} countries", va="center", fontsize=10)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"] for r in rows], fontsize=10.5, family=SER)
    ax.invert_yaxis(); ax.set_xlim(0, max(r["pop_m"] for r in rows) * 1.32); ax.set_xlabel("people, millions (2022, TFDD)", fontsize=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    out(fig, name, blog)


pop_bars("f_population", None)
print("figures", sorted(os.listdir(FIG)))
