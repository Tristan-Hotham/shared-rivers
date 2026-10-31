"""header.png: the 1200 x 630 social card (title, one headline number, world map of shared basins)."""
from figlib import *

R = jload(f"{DATA}/results.json"); B = jload(f"{WORK}/basins.json")["basins"]
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.37, .02, .63, .74]); ax.set_facecolor(BG)
draw_world(ax, ec="#FFFFFF", lw=.3, extent=(-11.5e6, 15.9e6, -5.6e6, 8.3e6))
for code, g in basins():
    ax.add_patch(poly_patch(g, fc=NCOL(B[code]["n"]), ec="#FFFFFF", lw=.2, zorder=2))
draw_rivers(ax, max_rank=4, scale=.5, alpha=.85)
fig.text(.04, .92, "Who shares the\nworld's rivers?", fontproperties=DISP, fontsize=46, color=FG, va="top", linespacing=.95)
b = R["basins"]
fig.text(.04, .52, f"{b['n']}", fontproperties=DISP, fontsize=40, color=RIVER, va="top")
fig.text(.04, .41, f"river basins cross a border.\nThey drain {b['area_pct']:.0f}% of the land\noutside Antarctica and hold\n{b['pop_pct']:.0f}% of the world's people.", family=SER, fontsize=15, color=FG, va="top", linespacing=1.35)
fig.text(.04, .15, f"Danube basin: {b['top'][0]['n']} countries", family=MONO, fontsize=12.5, color="#3A2C6E", va="top")
fig.text(.04, .05, "maps.tristanhotham.com/shared-rivers", family=MONO, fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
print("header.png")
