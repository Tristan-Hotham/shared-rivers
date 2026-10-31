"""River systems, their longest paths and the countries they cross, measured on the Natural Earth 1:10m river and
lake centrelines (the 'scale rank' edition: 4,224 lines with stroke weights and Wikidata IDs), with the same
measurement repeated on the coarser 1:50m centrelines and on simplified lines to show how map scale changes length.

Method
1. Every line becomes edges of a graph. A line is split where another line's end touches its interior, and line
   ends closer than 0.02 degrees (about 2 km) are joined. Canals are left out, as are the Casiquiare (the natural
   channel that links the Orinoco to the Amazon, so the two stay separate systems), the Ferenc csatorna (a canal
   between the Danube and the Tisza that Natural Earth does not class as one) and the Kovzha, which Natural
   Earth draws along the Volga-Baltic waterway so that it joins the upper Volga to Lake Onega.
2. Mouths are line ends within 3 km of the sea (the Natural Earth land outline, which leaves the Caspian as sea) or
   of five terminal lakes (the two Aral Seas, Lake Chad, Lake Balkhash, Lake Eyre). Each node is given to its nearest
   mouth along the network (multi-source Dijkstra on geodesic length); mouths of one delta (catchments that touch
   less than 400 km from both mouths) are merged into one system, measured through its shortest channel to the sea.
3. A system's length is the network distance from its mouth to its most distant source: the usual definition of a
   river's length, measured at map scale.
4. Countries along a path or a named river come from points every 1 km: a country counts if at least 1 km of points
   lie inside it, or at least 5 km lie within about 1.5 km of its border (so a border river counts for both banks).
Outputs: WORK/systems.json, data/river_systems.csv, data/named_rivers.csv, data/rivers.geojson, data/mainstems.geojson."""
import csv, collections
import numpy as np, networkx as nx, shapely
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point, LineString, mapping
from shapely.strtree import STRtree
from shapely.ops import substring, linemerge
from pyproj import Geod
from common import *

G84 = Geod(ellps="WGS84")
TOL = 0.02
CUT = {"Casiquiare", "Kovzha River"}
SKIP = lambda p: p["featurecla"] == "Canal" or (p.get("name") or "").endswith(("Canal", "Csatorna")) or p.get("name") in CUT
DISTRIB = ("Branch", "Bayou", "Protoka", "Bratul", "Braţul", " Pass", "Distributary", "Delta", "Estuary")
NAMEFIX = {"Amazonas": "Amazon", "Chang Jiang": "Yangtze", "Huang": "Yellow River", "Yenisey": "Yenisei", "Shatt al Arab": "Shatt al-Arab",
           "Donau": "Danube", "Rhein": "Rhine", "Maas": "Rhine", "Godävari": "Godavari", "Olenëk": "Olenek", "Dnipro": "Dnieper", "Sénégal": "Senegal"}
SYSFIX = {"Mississippi": "Mississippi-Missouri", "Shatt al-Arab": "Tigris-Euphrates (Shatt al-Arab)", "Brahmaputra": "Ganges-Brahmaputra",
          "Yenisei": "Yenisei-Angara", "Ob": "Ob-Irtysh", "Paraná": "Paraná (Río de la Plata)", "Rhine": "Rhine-Meuse"}


def glen(ln):
    xy = np.asarray(ln.coords)
    return G84.line_length(xy[:, 0], xy[:, 1]) / 1000


def chunks(ring, n=48):
    """Split a long ring into short lines so that distance queries stay fast."""
    c = np.asarray(ring.coords)
    return [LineString(c[i:i + n + 1]) for i in range(0, len(c) - 1, n)]


land = []
for f in jload(f"{RAWS}/ne/ne_10m_land.geojson")["features"]:
    g = shape(f["geometry"])
    land += list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
LAKES = {"North Aral Sea", "South Aral Sea", "Lake Chad", "Lake Balkhash", "Lake Eyre North"}
lakes = [shape(f["geometry"]) for f in jload(f"{RAWS}/ne/ne_10m_lakes.geojson")["features"] if f["properties"]["name"] in LAKES]
targets = [c for p in land for r in [p.exterior] + list(p.interiors) for c in chunks(r)]
targets += [c for g in lakes for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]) for c in chunks(p.exterior)]
TTREE, LTREE = STRtree(targets), STRtree(land)


def network(path):
    """Build the river graph from one Natural Earth file and return its systems (longest first)."""
    J = jload(path)
    segs = []
    for f in J["features"]:
        p = f["properties"]
        if SKIP(p):
            continue
        g = shape(f["geometry"])
        for ln in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            if len(ln.coords) >= 2:
                segs.append((ln, {"name": p.get("name"), "wd": p.get("wikidataid"), "rank": p.get("scalerank"), "w": p.get("strokeweig"), "cla": p["featurecla"]}))
    lines = [s[0] for s in segs]
    tree = STRtree(lines)
    cuts = collections.defaultdict(list)
    for i, ln in enumerate(lines):
        for pt in (Point(ln.coords[0]), Point(ln.coords[-1])):
            for k in tree.query(pt.buffer(TOL)):
                if k != i and lines[k].distance(pt) < TOL:
                    t = lines[k].project(pt)
                    if 1e-9 < t < lines[k].length - 1e-9:
                        cuts[k].append(t)
    pieces = []
    for i, ln in enumerate(lines):
        ts = sorted(set([0.0] + cuts.get(i, []) + [ln.length]))
        for a, b in zip(ts[:-1], ts[1:]):
            if b - a > 1e-9:
                pc = substring(ln, a, b)
                if pc.geom_type == "LineString" and len(pc.coords) >= 2:
                    pieces.append((pc, i))
    E = np.array([c for pc, _ in pieces for c in (pc.coords[0][:2], pc.coords[-1][:2])])
    uf = list(range(len(E)))

    def find(a):
        while uf[a] != a:
            uf[a] = uf[uf[a]]
            a = uf[a]
        return a
    for a, b in cKDTree(E).query_pairs(TOL):
        ra, rb = find(a), find(b)
        if ra != rb:
            uf[ra] = rb
    G = nx.Graph()
    PLEN = [glen(pc) for pc, _ in pieces]
    for n, (pc, i) in enumerate(pieces):
        a, b = find(2 * n), find(2 * n + 1)
        if a != b and not (G.has_edge(a, b) and G[a][b]["w"] <= PLEN[n]):
            G.add_edge(a, b, w=PLEN[n], piece=n)
    XY = {nd: E[nd] for nd in G.nodes}
    # mouths
    deg1 = [nd for nd in G.nodes if G.degree(nd) == 1]
    P = shapely.points(np.array([XY[n] for n in deg1]))
    dmin = np.full(len(deg1), 1e9)
    pi, ti = TTREE.query(P, predicate="dwithin", distance=0.06)
    for a, t in zip(pi.tolist(), ti.tolist()):
        lon, lat = XY[deg1[a]]
        q = targets[t].interpolate(targets[t].project(P[a]))
        dmin[a] = min(dmin[a], G84.inv(lon, lat, q.x, q.y)[2] / 1000)
    on_land = set(LTREE.query(P, predicate="intersects")[0].tolist())
    mouths = {deg1[a] for a in range(len(deg1)) if dmin[a] <= 3 or a not in on_land}
    dist, paths = nx.multi_source_dijkstra(G, mouths, weight="w")
    owner = {nd: p[0] for nd, p in paths.items()}
    muf = {m: m for m in mouths}

    def mfind(a):
        while muf[a] != a:
            a = muf[a]
        return a
    for u, v in G.edges():
        if u in owner and v in owner and owner[u] != owner[v] and dist[u] < 400 and dist[v] < 400:
            a, b = mfind(owner[u]), mfind(owner[v])
            if a != b:
                muf[a] = b
    groups = collections.defaultdict(set)
    for nd, m in owner.items():
        groups[mfind(m)].add(nd)
    pname = lambda n: segs[pieces[n][1]][1]["name"]
    systems = []
    for m, nodes in groups.items():
        tot = sum(d["w"] for _, _, d in G.subgraph(nodes).edges(data=True))
        if tot < 300:
            continue
        far = max(nodes, key=lambda n: dist[n])
        pth = paths[far]                                      # mouth to source
        ps = [G[a][b]["piece"] for a, b in zip(pth[:-1], pth[1:])]
        ch = []
        for n in ps:
            nm = pname(n)
            if nm and nm not in ch:
                ch.append(nm)
        named_ch = [c for c in ch if not any(w in c for w in DISTRIB)]
        mn = named_ch[0] if named_ch else (ch[0] if ch else None)
        nm = NAMEFIX.get(mn, mn)
        systems.append({"group": m, "len": dist[far], "net": tot, "chain": [NAMEFIX.get(c, c) if c in ("Amazonas", "Chang Jiang", "Huang", "Yenisey", "Donau", "Rhein") else c for c in ch],
                        "river": nm, "name": SYSFIX.get(nm, nm), "pieces": ps, "src": [float(x) for x in XY[far]], "mxy": [float(x) for x in XY[pth[0]]],
                        "edges": [d["piece"] for _, _, d in G.subgraph(nodes).edges(data=True)]})
    systems.sort(key=lambda s: -s["len"])
    return {"segs": segs, "pieces": pieces, "PLEN": PLEN, "G": G, "systems": systems, "mouths": mouths, "n_in": len(J["features"]), "dist": dist, "paths": paths,
            "n_skip": sum(1 for f in J["features"] if SKIP(f["properties"]))}


N10 = network(f"{RAWS}/ne/ne_10m_rivers_lake_centerlines_scale_rank.geojson")
segs, pieces, PLEN, systems = N10["segs"], N10["pieces"], N10["PLEN"], N10["systems"]
seen = collections.Counter(s["name"] for s in systems)
for s in systems:   # two Colorados
    if seen[s["name"]] > 1 and s["name"] == "Colorado":
        s["name"] = "Colorado (Argentina)" if s["mxy"][1] < 0 else "Colorado (United States)"

# ---------- countries along lines ----------
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
CPOLY, CISO = [], []
NOISO = {"SOL": "SOM", "KOS": "XKX", "CYN": "CYP"}   # other unassigned slivers (Siachen, Bir Tawil, bases) are left out
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else NOISO.get(p["ADM0_A3"])
    if iso is not None:
        CPOLY.append(shape(f["geometry"]).buffer(0)); CISO.append(iso)
CB, CBI = [], []
for g, iso in zip(CPOLY, CISO):
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        for r in [p.exterior] + list(p.interiors):
            for c in chunks(r):
                CB.append(c); CBI.append(iso)
BTREE, CTREE = STRtree(CB), STRtree(CPOLY)


def sample(geoms, step_km=1.0):
    pts, wts = [], []
    for ln in geoms:
        L = glen(ln)
        n = max(2, int(L / step_km) + 1)
        pts.append(shapely.line_interpolate_point(ln, np.linspace(0, 1, n), normalized=True))
        wts.append(np.full(n, L / n))
    return np.concatenate(pts), np.concatenate(wts)


def countries_along(geoms, buf=0.0135, min_in=1.0, min_edge=5.0):
    """{iso: km} along a list of LineStrings (see the method note at the top)."""
    pts, wts = sample(geoms)
    inside = collections.defaultdict(set)
    for a, c in zip(*[x.tolist() for x in CTREE.query(pts, predicate="intersects")]):
        inside[CISO[c]].add(a)
    near = collections.defaultdict(set, {k: set(v) for k, v in inside.items()})
    for a, c in zip(*[x.tolist() for x in BTREE.query(pts, predicate="dwithin", distance=buf)]):
        near[CBI[c]].add(a)
    km = lambda s: float(wts[list(s)].sum()) if s else 0.0
    return {k: round(km(v), 1) for k, v in near.items() if km(inside.get(k, set())) >= min_in or km(v) >= min_edge}


# ---------- TFDD basin of each system ----------
BAS = [(f["properties"]["BCODE"], shape(f["geometry"]).buffer(0)) for f in jload(f"{RAWS}/tfdd/Basin310_Master_20180511.geojson")["features"]]
BTR = STRtree([g for _, g in BAS])


def basin_of(geoms):
    pts, wts = sample(geoms, 5.0)
    acc = collections.Counter()
    for a, b in zip(*[x.tolist() for x in BTR.query(pts, predicate="intersects")]):
        acc[BAS[b][0]] += wts[a]
    tot = wts.sum()
    if not acc:
        return None, 0.0
    k, v = acc.most_common(1)[0]
    return k, round(100 * v / tot, 1)


def path_geoms(ps):
    g = linemerge([pieces[n][0] for n in ps])
    return list(g.geoms) if g.geom_type == "MultiLineString" else [g]


for s in systems[:80]:
    s["countries"] = countries_along(path_geoms(s["pieces"]))
    s["n_countries"] = len(s["countries"])
    s["basin"], s["basin_pct"] = basin_of(path_geoms(s["pieces"]))
    s["net_countries"] = countries_along([pieces[n][0] for n in s["edges"]], min_in=20, min_edge=20)

# ---------- other sources for the same systems: the farthest point on a chosen headwater ----------
def alt_source(sysname, headnames):
    s = next(x for x in systems if x["name"] == sysname)
    G, dist, paths = N10["G"], N10["dist"], N10["paths"]
    edges = set(s["edges"])
    best = None
    for u, v, d in G.edges(data=True):
        if d["piece"] in edges and segs[pieces[d["piece"]][1]][1]["name"] in headnames:
            for nd in (u, v):
                if best is None or dist[nd] > dist[best]:
                    best = nd
    pth = paths[best]
    ch = []
    for a, b in zip(pth[:-1], pth[1:]):
        nm = segs[pieces[G[a][b]["piece"]][1]][1]["name"]
        if nm and nm not in ch:
            ch.append(nm)
    return {"system": sysname, "len": dist[best], "chain": ch, "src": [float(x) for x in N10["G"].nodes and XYOF(best)]}


XYOF = lambda nd: [float(c) for c in shapely.get_coordinates(pieces[next(d["piece"] for _, _, d in N10["G"].edges(nd, data=True))][0])[0]]
ALTS = {"nile_blue": alt_source("Nile", {"El Bahr el Azraq", "Abay"}), "miss_own": alt_source("Mississippi-Missouri", {"Mississippi"})}


def country_at(lon, lat):
    hits = CTREE.query(Point(lon, lat), predicate="intersects")
    return CISO[hits[0]] if len(hits) else None


for s in systems[:80]:
    s["src_iso"] = country_at(*s["src"])

# ---------- named rivers (by Wikidata ID, else name) ----------
piece_sys = {}
for si, s in enumerate(systems):
    for n in s["edges"]:
        piece_sys[n] = si
byname = collections.defaultdict(list)
for n, (pc, i) in enumerate(pieces):
    p = segs[i][1]
    if p["name"]:
        byname[p["wd"] or ("name:" + p["name"])].append(n)
named = []
for k, ps in byname.items():
    L = sum(PLEN[n] for n in ps)
    if L < 250:
        continue
    names = collections.Counter(segs[pieces[n][1]][1]["name"] for n in ps)
    top = names.most_common(1)[0][0]
    sy = collections.Counter(piece_sys.get(n, -1) for n in ps).most_common(1)[0][0]
    named.append({"key": k, "name": NAMEFIX.get(top, top) if top != "Maas" else "Meuse (Maas)", "names": sorted(names), "len": L, "pieces": ps,
                  "rank": min(segs[pieces[n][1]][1]["rank"] for n in ps), "sys": sy})
named.sort(key=lambda r: -r["len"])
for r in named:
    r["countries"] = countries_along([pieces[n][0] for n in r["pieces"]])
    r["n_countries"] = len(r["countries"])

# ---------- map scale: the same systems on the 1:50m lines, and simplified ----------
N50 = network(f"{RAWS}/ne/ne_50m_rivers_lake_centerlines.geojson")
for s in systems[:40]:
    best = None
    for t in N50["systems"]:
        d = G84.inv(s["mxy"][0], s["mxy"][1], t["mxy"][0], t["mxy"][1])[2] / 1000
        # the coarser map's system with its mouth within 150 km, no longer than this one, and closest in length
        if d < 150 and t["len"] <= 1.02 * s["len"] and (best is None or abs(t["len"] - s["len"]) < abs(best["len"] - s["len"])):
            best = t
    s["len50"] = best["len"] if best else None
TOLS = [0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
for s in systems[:40]:
    gs = path_geoms(s["pieces"])
    s["simplified"] = [round(sum(glen(g.simplify(t)) for g in gs), 1) for t in TOLS]

jsave({"systems": systems, "named": named, "tols": TOLS, "alts": ALTS, "n_lines_in": N10["n_in"], "n_skipped": N10["n_skip"], "n_pieces": len(pieces),
       "n_nodes": N10["G"].number_of_nodes(), "n_mouths": len(N10["mouths"]), "net_km": sum(PLEN), "n_systems": len(systems),
       "n50_lines": N50["n_in"]}, f"{WORK}/systems.json")

# ---------- reusable tables ----------
with open(f"{DATA}/river_systems.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["rank", "system", "longest_path_km_ne10m", "longest_path_km_ne50m", "network_km_ne10m", "path_names_mouth_to_source",
                "countries_along_longest_path", "tfdd_basin", "mouth_lon", "mouth_lat", "source_lon", "source_lat"])
    for i, s in enumerate(systems[:80], 1):
        w.writerow([i, s["name"], round(s["len"]), round(s["len50"]) if s.get("len50") else "", round(s["net"]), " < ".join(s["chain"]),
                    " ".join(sorted(s["countries"])), s["basin"] or "", round(s["mxy"][0], 3), round(s["mxy"][1], 3), round(s["src"][0], 3), round(s["src"][1], 3)])
with open(f"{DATA}/named_rivers.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["river", "wikidata", "natural_earth_names", "length_km_ne10m", "n_countries", "countries_km"])
    for r in named:
        w.writerow([r["name"], r["key"] if r["key"].startswith("Q") else "", "; ".join(r["names"]), round(r["len"]), r["n_countries"],
                    "; ".join(f"{k} {v:.0f}" for k, v in sorted(r["countries"].items(), key=lambda x: -x[1]))])


# ---------- page layers ----------
def rnd(geom, nd=3):
    m = mapping(geom)
    def r(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], (int, float)) else [r(x) for x in c]
    m["coordinates"] = r(m["coordinates"])
    return m


feats = []
for n, (pc, i) in enumerate(pieces):
    p = segs[i][1]
    feats.append({"type": "Feature", "properties": {"n": p["name"] or "", "r": p["rank"], "w": p["w"], "s": piece_sys.get(n, -1)},
                  "geometry": rnd(pc.simplify(0.008))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/rivers.geojson")
feats = []
for si, s in enumerate(systems[:40]):
    g = linemerge([pieces[n][0] for n in s["pieces"]]).simplify(0.005)
    feats.append({"type": "Feature", "properties": {"s": si, "name": s["name"], "len": round(s["len"])}, "geometry": rnd(g)})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/mainstems.geojson")

print("lines", N10["n_in"], "skipped", N10["n_skip"], "pieces", len(pieces), "mouths", len(N10["mouths"]), "systems>=300km", len(systems))
for s in systems[:40]:
    print(f"{s['name']:32s} {s['len']:6.0f} {s.get('len50') or 0:6.0f} {s['n_countries']:2d} {s['basin']} {s['basin_pct']} {' < '.join(s['chain'][:6])[:70]}  {sorted(s['countries'])}  {s['simplified']}")
print("alts", {k: (round(v["len"]), v["chain"]) for k, v in ALTS.items()})
print("--- named rivers by countries")
for r in sorted(named, key=lambda r: (-r["n_countries"], -r["len"]))[:16]:
    print(f"{r['name']:24s} {r['len']:6.0f} {r['n_countries']} {sorted(r['countries'])}")
for f in ("rivers.geojson", "mainstems.geojson"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
