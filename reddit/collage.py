"""r/dataisbeautiful collage for shared-rivers: 2400 x 3000 px on a light background. Numbers from data/results.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

R = jload(f"{DATA}/results.json"); B = jload(f"{WORK}/basins.json")["basins"]
b, r = R["basins"], R["rivers"]
PAPERC = "#F7F5F0"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=PAPERC)
fig.text(.045, .972, "Who shares the world's rivers?", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .918, f"{b['n']} river basins cross a national border. Together they drain {b['area_pct']:.0f}% of the world's land outside\n"
         f"Antarctica and were home to {b['pop_bn']:.1f} billion people in 2022, {b['pop_pct']:.0f}% of humanity.",
         family=SER, fontsize=16, color=FG, va="top", linespacing=1.4)

# ---------- hero map ----------
ax = fig.add_axes([0, .475, 1, .392]); ax.set_facecolor(PAPERC)
EXT = (-12.0e6, 15.6e6, -5.4e6, 8.3e6)
draw_world(ax, ec="#FFFFFF", lw=.3, extent=EXT, land="#E4DFD3")
for code, g in basins():
    ax.add_patch(poly_patch(g, fc=NCOL(B[code]["n"]), ec="#FFFFFF", lw=.25, zorder=2))
draw_rivers(ax, max_rank=4, scale=.55, alpha=.9)
# labels on open sea, with short leaders to the basin
LAB = [("DANU", "Danube\n19 countries", (-30, 46), (19, 47.5)), ("NILE", "Nile, 11 countries", (21, 35.4), (31.2, 26)),
       ("NGER", "Niger\n11 countries", (-15, 0), (-1, 13)), ("CNGO", "Congo\n10 countries", (-3, -27), (20, -4)),
       ("RHIN", "Rhine-Meuse\n9 countries", (-28, 58), (6.5, 50.5)), ("ZAMB", "Zambezi\n8 countries", (60, -31), (31, -16.5)),
       ("LKCH", "Lake Chad\n8 countries", (-38, 21), (14.5, 15)), ("AMZN", "Amazon\n7 countries", (-27, -8), (-55, -4)),
       ("GANG", "Ganges-Brahmaputra-\nMeghna, 6 countries", (84, 4), (88.5, 23.5)), ("MEKO", "Mekong\n6 countries", (119, 11), (106, 14)),
       ("LPTA", "La Plata\n5 countries", (-30, -38), (-55, -27))]
for code, text, (lx, ly), (tx, ty) in LAB:
    assert str(B[code]["n"]) in text, code
    x, y = xy(lx, ly); x1, y1 = xy(tx, ty)
    ax.annotate(text, xy=(x1, y1), xytext=(x, y), fontsize=11.5, family=SER, color=FG, ha="center", va="center", zorder=9, linespacing=1.15,
                path_effects=halo(4, PAPERC), arrowprops=dict(arrowstyle="-", color=FG, lw=.8, shrinkA=13, shrinkB=1))
    ax.plot([x1], [y1], "o", ms=3.2, color=FG, zorder=10)
LEGP = {"family": MONO, "size": 12}
h = [Rectangle((0, 0), 1, 1, fc=c, ec="none") for _, _, _, c in NBINS] + [Line2D([], [], color=RIVER, lw=2.4)]
labs = [f"{l} countries" for _, _, l, _ in NBINS] + ["river (Natural Earth)"]
fig.legend(h, labs, loc="upper left", bbox_to_anchor=(.04, .478), ncol=4, frameon=False, prop=LEGP, title="Basin shared by", title_fontproperties={"family": MONO, "size": 12, "weight": "medium"},
           alignment="left", handlelength=1.3, columnspacing=1.6)

# ---------- ranked panel: basins by number of countries ----------
a1 = fig.add_axes([.17, .1, .3, .265]); a1.set_facecolor(PAPERC)
rows = b["top"][:14]
for i, t in enumerate(rows):
    a1.barh(i, t["n"], color=NCOL(t["n"]), height=.7)
    a1.text(t["n"] + .3, i, str(t["n"]), va="center", fontsize=11.5, color=FG, family=MONO)
a1.set_yticks(range(len(rows))); a1.set_yticklabels([t["name"].replace("Ganges-Brahmaputra-Meghna", "Ganges-Brahmaputra").replace("Aral Sea (Amu Darya and Syr Darya)", "Aral Sea") for t in rows], fontsize=11.5, family=SER)
a1.invert_yaxis(); a1.set_xlim(0, 22); a1.set_xticks([])
for s in ("top", "right", "bottom", "left"):
    a1.spines[s].set_visible(False)
a1.tick_params(axis="y", length=0)
fig.text(.045, .392, "Countries sharing each basin", family=SER, fontsize=17, weight="semibold", color=FG)
fig.text(.045, .377, "Disputed areas such as Abyei are not counted", family=MONO, fontsize=10.5, color=MUT)

# ---------- length comparison ----------
a2 = fig.add_axes([.69, .1, .25, .265]); a2.set_facecolor(PAPERC)
pub = {p["sys"]: p for p in R["published"]}
rows = r["top"][:10]
for i, t in enumerate(rows):
    a2.barh(i, t["len"], color=RIVER, height=.66, alpha=.92)
    if t["len50"]:
        a2.plot([t["len50"]] * 2, [i - .4, i + .4], color=FG, lw=2)
    if t["name"] in pub:
        a2.plot(pub[t["name"]]["km"], i, marker="D", ms=8, color=HOT, mec=PAPERC, mew=1.2, zorder=5)
    a2.text(max(t["len"], pub[t["name"]]["km"] if t["name"] in pub else 0) + 330, i, f"{t['len']:,}", va="center", fontsize=10.5, family=MONO)
a2.set_yticks(range(len(rows))); a2.set_yticklabels([t["name"].replace("Mississippi-Missouri", "Mississippi-\nMissouri").replace("Yenisei-Angara", "Yenisei") for t in rows], fontsize=11, family=SER)
a2.invert_yaxis(); a2.set_xlim(0, 8200); a2.set_xticks([0, 2000, 4000, 6000]); a2.set_xticklabels(["0", "2,000", "4,000", "6,000 km"], fontsize=9.5)
for s in ("top", "right", "left"):
    a2.spines[s].set_visible(False)
a2.tick_params(axis="y", length=0)
fig.text(.53, .392, "How long? It depends on the map", family=SER, fontsize=17, weight="semibold", color=FG)
fig.text(.53, .363, "Mouth to farthest source on one map (bars), on a\ncoarser map (ticks) and per Britannica (diamonds)", family=MONO, fontsize=10.5, color=MUT, linespacing=1.4)

fig.text(.045, .018, "Sources: Transboundary Freshwater Dispute Database, Oregon State University (2024 register, 2018 basin outlines); Natural Earth 1:10m and 1:50m\n"
         "river lines (public domain), lengths measured by me through a network of the lines; Encyclopaedia Britannica; World Bank population.\n"
         "Analysis and chart: Tristan Hotham, Python and matplotlib  ·  maps.tristanhotham.com/shared-rivers", family=MONO, fontsize=9.3, color=MUT, linespacing=1.55, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "who_shares_the_worlds_rivers.png")
fig.savefig(out, facecolor=PAPERC, dpi=200)
print("ok", out)
