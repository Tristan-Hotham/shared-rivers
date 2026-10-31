"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; the page data (SITE: basins, countries, river systems and named rivers; WORLD: simplified Natural
Earth 1:50m countries; CITIES: Natural Earth populated places) is embedded, and data/basins.geojson,
data/rivers.geojson, data/mainstems.geojson and data/bcu.geojson are loaded by the page. The full-screen map snippet
(code/fullscreen_snippet.html, copied from the reference study) is pasted before </body>."""
import re, shutil
from shapely.geometry import shape, mapping
from common import *

R = jload(f"{DATA}/results.json")
B = jload(f"{WORK}/basins.json")["basins"]; C = jload(f"{WORK}/countries.json"); S = jload(f"{WORK}/systems.json")
sy, named = S["systems"], S["named"]


def bbox(g):
    b = g.bounds
    return [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]


def main_poly(g):
    return max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g


# ---------- countries: outlines, names, label points, bounds ----------
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
NOISO = {"SOL": "SOM", "KOS": "XKX", "CYN": "CYP"}
feats, cbb, cpos = [], {}, {}
cname = {i: c["name"] for i, c in C.items()}
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else NOISO.get(p["ADM0_A3"], p["ADM0_A3"])
    if p["ADM0_A3"] == "ATA":
        continue
    g = shape(f["geometry"]).buffer(0)
    s = g.simplify(0.07, preserve_topology=True)
    m = mapping(s)
    r = lambda c: [round(c[0], 2), round(c[1], 2)] if isinstance(c[0], (int, float)) else [r(x) for x in c]
    m["coordinates"] = r(m["coordinates"])
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": m})
    mp = main_poly(g)
    cbb[iso] = bbox(mp)
    rp = mp.representative_point()
    if p["ADM0_A3"] in ("SOL", "CYN"):
        continue
    cpos[iso] = [round(rp.x, 2), round(rp.y, 2), round(C[iso]["area"]) if iso in C else 0]
    cname.setdefault(iso, p["NAME"])
WORLD = {"type": "FeatureCollection", "features": feats}

# ---------- basins ----------
bpoly = {f["properties"]["c"]: shape(f["geometry"]) for f in jload(f"{DATA}/basins.geojson")["features"]}
bsys = {}
for i, s in enumerate(sy):
    if s.get("basin"):
        bsys.setdefault(s["basin"], []).append(i)
SB = {}
for c, b in B.items():
    SB[c] = {"nm": b["display"], "n": b["n"], "i": b["iso"], "d": b["disputed"], "a": round(b["area"]), "pop": round(b["pop"]) if b["pop"] else None,
             "sh": [[k, round(p, 1), a] for k, p, a in b["share"]], "bb": bbox(bpoly[c]) if c in bpoly else None, "sy": bsys.get(c, [])[:4]}
    if not SB[c]["bb"]:
        bbs = [cbb[i] for i in b["iso"] if i in cbb]
        SB[c]["bb"] = [min(x[0] for x in bbs), min(x[1] for x in bbs), max(x[2] for x in bbs), max(x[3] for x in bbs)]
SC = {i: {"p": c["pct_in"], "d": round(c["dep"], 1) if c.get("dep") is not None else None, "b": c["basins"]} for i, c in C.items()}

# ---------- river systems and named rivers ----------
canon = {}
for r in named:
    for n in r["names"]:
        if n not in canon or canon[n]["len"] < r["len"]:
            canon[n] = r
pieces_bb = {}
RV = {}
rj = jload(f"{DATA}/rivers.geojson")
lines_by_name = {}
for f in rj["features"]:
    lines_by_name.setdefault(f["properties"]["n"], []).append(shape(f["geometry"]))
for n, r in canon.items():
    gs = lines_by_name.get(n, [])
    bb = [min(g.bounds[0] for g in gs), min(g.bounds[1] for g in gs), max(g.bounds[2] for g in gs), max(g.bounds[3] for g in gs)] if gs else None
    RV[n] = {"k": r["name"], "l": round(r["len"]), "c": [[k, round(v)] for k, v in sorted(r["countries"].items(), key=lambda x: -x[1])], "s": r["sys"],
             "bb": [round(x, 2) for x in bb] if bb else None}
# one entry per canonical name for search; extra keys are aliases (e.g. Donau for Danube)
for r in named:
    if r["name"] not in RV:
        RV[r["name"]] = dict(RV[r["names"][0]])
SS = []
stems = {f["properties"]["s"]: shape(f["geometry"]) for f in jload(f"{DATA}/mainstems.geojson")["features"]}
for i, s in enumerate(sy):
    rv = s["river"] if s["river"] in RV else None
    e = {"nm": s["name"] or "Unnamed river", "l": round(s["len"]), "ch": [x for k, x in enumerate(s["chain"]) if x not in s["chain"][:k]], "rv": rv}
    if i < 80:
        e.update({"l50": round(s["len50"]) if s.get("len50") else None, "c": sorted(s.get("countries", {}), key=lambda k: -s["countries"][k]), "b": s.get("basin")})
    if i in stems:
        e["bb"] = bbox(stems[i])
    elif rv and RV[rv]["bb"]:
        e["bb"] = RV[rv]["bb"]
    SS.append(e)
# river labels: named rivers of at least 300 km, at the middle of their longest line
RLAB = []
for r in sorted(named, key=lambda r: -r["len"]):
    if r["len"] < 300 or r["rank"] > 7:
        continue
    gs = [g for n in r["names"] for g in lines_by_name.get(n, [])]
    if not gs:
        continue
    g = max(gs, key=lambda g: g.length)
    pt = g.interpolate(.5, normalized=True)
    RLAB.append([r["name"], round(pt.y, 2), round(pt.x, 2), 3 if r["rank"] <= 2 else 4 if r["rank"] <= 4 else 5 if r["rank"] <= 6 else 6])

SITE = {"cname": cname, "cpos": cpos, "cbb": cbb, "b": SB, "c": SC, "s": SS, "rv": RV, "rlab": RLAB,
        "nbins": [list(x) for x in NBINS], "dbins": [list(x) for x in DBINS]}
pp = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
CITIES = sorted([[p["properties"]["name"], round(p["properties"]["latitude"], 2), round(p["properties"]["longitude"], 2), int(p["properties"]["pop_max"])]
                 for p in pp["features"] if (p["properties"]["pop_max"] or 0) >= 250000], key=lambda c: -c[3])
jsave(SITE, f"{WORK}/site.json")


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI_URL\}|BLOG_URL\}|DOI\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(dash(o), ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE)).replace("/*WORLD*/", J(WORLD)).replace("/*CITIES*/", J(CITIES))
    snip = os.path.join(ROOT, "code", "fullscreen_snippet.html")
    if not os.path.exists(snip):
        shutil.copy("/home/claude/ref/drinks-map/code/fullscreen_snippet.html", snip)
    html = html.replace("/*FULLSCREEN*/", open(snip, encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB; site", len(J(SITE)) // 1024, "KB; world", len(J(WORLD)) // 1024, "KB; cities", len(CITIES))


if __name__ == "__main__":
    build()
