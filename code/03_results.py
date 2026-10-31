"""data/results.json: every number quoted on the page, in the paper, the blog post, the collage and the Reddit post.
Facts stated in words are checked here with asserts."""
import csv
from shapely.geometry import shape
from shapely.ops import unary_union, nearest_points
from pyproj import Geod
from common import *

# how far Natural Earth's outline of Moldova stops short of its Danube line
_md = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"] if f["properties"]["ADM0_A3"] == "MDA"][0]
_dn = unary_union([shape(f["geometry"]) for f in jload(f"{RAWS}/ne/ne_10m_rivers_lake_centerlines_scale_rank.geojson")["features"] if f["properties"].get("wikidataid") == "Q1653"])
_a, _b = nearest_points(_md, _dn)
MOLDOVA_GAP = Geod(ellps="WGS84").inv(_a.x, _a.y, _b.x, _b.y)[2] / 1000

B = jload(f"{WORK}/basins.json"); C = jload(f"{WORK}/countries.json"); S = jload(f"{WORK}/systems.json")
bas = B["basins"]; sy = S["systems"]; named = S["named"]
CN = {i: c["name"] for i, c in C.items()}
pub = list(csv.DictReader(open(os.path.join(ROOT, "code", "published_lengths.csv"), encoding="utf-8")))

# ---------- basins ----------
area = sum(b["area"] for b in bas.values())
pop = sum(b["pop"] or 0 for b in bas.values())
wpop = B["wpop"]["2022"]
by_n = {}
for b in bas.values():
    by_n[b["n"]] = by_n.get(b["n"], 0) + 1
order = sorted(bas.values(), key=lambda b: (-b["n"], -b["area"]))
top = [{"code": b["code"], "name": b["display"], "n": b["n"], "area": round(b["area"]), "pop_m": round((b["pop"] or 0) / 1e6, 1),
        "countries": b["iso"], "disputed": b["disputed"], "tfdd_n": b["tfdd_n"]} for b in order[:25]]
most_pop = [{"code": b["code"], "name": b["display"], "n": b["n"], "pop_m": round(b["pop"] / 1e6)} for b in sorted(bas.values(), key=lambda b: -(b["pop"] or 0))[:12]]
largest = [{"code": b["code"], "name": b["display"], "n": b["n"], "area": round(b["area"])} for b in sorted(bas.values(), key=lambda b: -b["area"])[:10]]
share = lambda code, iso: next(p for k, p, a in bas[code]["share"] if k == iso)
cont = {}
for b in bas.values():
    c = cont.setdefault(b["cont"], {"n": 0, "area": 0.0})
    c["n"] += 1; c["area"] += b["area"]
basins = {"n": len(bas), "n_poly": sum(1 for b in bas.values() if b["has_poly"]), "n_bcu": B["n_bcu"], "area": round(area),
          "land_x_ant": round(B["land_x_ant"]), "land_mkm2": B["land_x_ant"] / 1e6, "area_pct": round(100 * area / B["land_x_ant"], 1),
          "pop": round(pop), "pop_bn": pop / 1e9, "wpop2022": wpop, "pop_pct": round(100 * pop / wpop, 1),
          "by_n": {str(k): by_n[k] for k in sorted(by_n)}, "n_2": by_n[2], "n_3plus": sum(v for k, v in by_n.items() if k >= 3), "n_5plus": sum(v for k, v in by_n.items() if k >= 5),
          "pct_2": round(100 * by_n[2] / len(bas)), "top": top, "most_pop": most_pop, "largest": largest,
          "amzn_bra_pct": share("AMZN", "BRA"), "cngo_cod_pct": share("CNGO", "COD"), "danu_rou_pct": share("DANU", "ROU"), "nile_sdn_pct": share("NILE", "SDN"),
          "n_disputed_basins": sum(1 for b in bas.values() if b["disputed"]), "by_cont": {k: {"n": v["n"], "area": round(v["area"])} for k, v in cont.items()},
          "danu_countries": [CN.get(i, i) for i in bas["DANU"]["iso"]], "nile_countries": [CN.get(i, i) for i in bas["NILE"]["iso"]]}
basins["n_nopoly"] = basins["n"] - basins["n_poly"]
basins["gbm_gt_nile_indus"] = most_pop[0]["pop_m"] > most_pop[1]["pop_m"] + most_pop[2]["pop_m"]

# ---------- countries ----------
withb = [c for c in C.values() if c["basins"]]
mb = sorted(withb, key=lambda c: (-len(c["basins"]), c["name"]))
dep = sorted([c for c in C.values() if c.get("dep") is not None], key=lambda c: -c["dep"])
full = sorted([c for c in C.values() if c["pct_in"] >= 99], key=lambda c: c["name"])
countries = {"n_with_basin": len(withb), "most_basins": [{"iso": c["iso"], "name": c["name"], "n": len(c["basins"])} for c in mb[:12]],
             "n_full": len(full), "full": [c["name"] for c in full],
             "dep_n": len(dep), "dep_top": [{"iso": c["iso"], "name": c["name"], "dep": round(c["dep"], 1), "period": c["dep_period"]} for c in dep[:25]],
             "dep_n_over50": sum(1 for c in dep if c["dep"] > 50), "dep_n_over75": sum(1 for c in dep if c["dep"] > 75),
             "dep_n_zero": sum(1 for c in dep if c["dep"] == 0)}
for iso in ("EGY", "SDN", "TKM", "UZB", "BGD", "HUN", "ROU", "NLD", "KWT", "BHR", "PAK", "IRQ", "SYR", "NER", "MRT", "MDA", "KHM", "VNM"):
    countries["dep_" + iso.lower()] = round(C[iso]["dep"], 1)
for iso in ("HUN", "PRY", "RWA", "LAO", "EGY", "NLD"):
    countries["pct_in_" + iso.lower()] = C[iso]["pct_in"]

# ---------- rivers ----------
ps = {p["system"]: p for p in pub}
uniq = lambda xs: [x for i, x in enumerate(xs) if x not in xs[:i]]
topr = []
for i, s in enumerate(sy[:25]):
    topr.append({"rank": i + 1, "name": s["name"], "len": round(s["len"]), "len50": round(s["len50"]) if s.get("len50") else None, "chain": uniq(s["chain"]),
                 "n": s.get("n_countries"), "countries": sorted(s.get("countries", {})), "basin": s.get("basin"), "src": s["src"], "mouth": s["mxy"], "src_iso": s.get("src_iso")})
byname = {s["name"]: s for s in sy}
nm_top = sorted([r for r in named if r["n_countries"] >= 4], key=lambda r: (-r["n_countries"], -r["len"]))
named_top = [{"name": r["name"], "n": r["n_countries"], "len": round(r["len"]), "countries": sorted(r["countries"], key=lambda k: -r["countries"][k])} for r in nm_top[:20]]
scale = []
for nmx in ("Nile", "Amazon", "Yangtze", "Danube"):
    s = byname[nmx]
    scale.append({"name": nmx, "v": [round(v) for v in s["simplified"]]})
ratio = lambda nmx: round(100 * byname[nmx]["len"] / float(ps[nmx]["length_km"]), 1)
published = [{"river": p["river"], "sys": p["system"], "km": int(p["length_km"]), "src": p["source"], "url": p["url"], "quote": p["quote"], "map": round(byname[p["system"]]["len"]),
              "ratio": ratio(p["system"])} for p in pub]
amazon, nile, yang, miss, dan = byname["Amazon"], byname["Nile"], byname["Yangtze"], byname["Mississippi-Missouri"], byname["Danube"]
rivers = {"n_lines": S["n_lines_in"], "n_skipped": S["n_skipped"], "n_pieces": S["n_pieces"], "n_mouths": S["n_mouths"], "n_systems": S["n_systems"],
          "net_km": round(S["net_km"]), "n50_lines": S["n50_lines"], "top": topr, "tols": S["tols"], "scale": scale, "named_top": named_top,
          "nile": {"len": round(nile["len"]), "len50": round(nile["len50"]), "src": nile["src"], "src_country": CN.get(nile["src_iso"], nile["src_iso"]), "ratio": ratio("Nile")},
          "amazon": {"len": round(amazon["len"]), "len50": round(amazon["len50"]), "src": amazon["src"], "src_lat_abs": abs(amazon["src"][1]), "src_lon_abs": abs(amazon["src"][0]),
                     "mouth_lon_abs": abs(amazon["mxy"][0]), "ratio": ratio("Amazon")},
          "yangtze": {"len": round(yang["len"]), "len50": round(yang["len50"]), "ratio": ratio("Yangtze")},
          "miss": {"len": round(miss["len"])}, "nile_blue": {"len": round(S["alts"]["nile_blue"]["len"]), "chain": S["alts"]["nile_blue"]["chain"]},
          "miss_own": {"len": round(S["alts"]["miss_own"]["len"]), "chain": S["alts"]["miss_own"]["chain"]},
          "danube": {"len": round(dan["len"]), "n": dan["n_countries"]}, "moldova_gap_km": round(MOLDOVA_GAP, 1),
          "nile_minus_amazon": round(nile["len"] - amazon["len"]), "pub_nile_minus_amazon": int(ps["Nile"]["length_km"]) - int(ps["Amazon"]["length_km"]),
          "shrink_pct": {s["name"]: round(100 - 100 * s["v"][-1] / s["v"][0]) for s in scale},
          "len50_pct": {nmx: round(100 * byname[nmx]["len50"] / byname[nmx]["len"], 1) for nmx in ("Nile", "Amazon", "Yangtze", "Danube")}}
rivers["shared_top10"] = sum(1 for r in topr[:10] if r["basin"])
rivers["shared_top25"] = sum(1 for r in topr if r["basin"])

R = {"meta": {"page": PAGE, "repo": REPO, "year": 2026, "slug": SLUG}, "basins": basins, "countries": countries, "rivers": rivers, "published": published}

# ---------- facts stated in words ----------
assert basins["n"] == 313 and basins["n_poly"] == 310 and basins["n_nopoly"] == 3
assert [t["code"] for t in top[:5]] == ["DANU", "NILE", "NGER", "CNGO", "RHIN"], [t["code"] for t in top[:5]]
assert top[0]["n"] == 19 and top[1]["n"] == 11 and top[2]["n"] == 11 and top[3]["n"] == 10 and top[4]["n"] == 9
assert set(bas["NILE"]["disputed"]) == {"Abyei", "Hala'ib triangle", "Ma'tan al-Sarra"} and set(bas["GANG"]["disputed"]) == {"Arunachal Pradesh", "China/India"}
assert all(not b["disputed"] for k, b in bas.items() if k in [t["code"] for t in top[:16]] and k not in ("NILE", "GANG", "INDU", "TRIM"))
assert "MDA" in bas["DANU"]["iso"] and "UKR" in bas["DANU"]["iso"] and "DEU" in bas["DANU"]["iso"] and "AUT" in bas["DANU"]["iso"]
assert bas["DANU"]["share"][0][0] == "ROU" and bas["AMZN"]["share"][0][0] == "BRA" and bas["CNGO"]["share"][0][0] == "COD"
assert max(p for k, p, a in bas["DANU"]["share"]) < 30
assert [m["code"] for m in most_pop[:3]] == ["GANG", "NILE", "INDU"] and basins["gbm_gt_nile_indus"]
assert countries["most_basins"][0]["iso"] == "RUS" and countries["most_basins"][1]["iso"] == "USA" and countries["most_basins"][2]["iso"] == "CHL"
assert all(C[i]["pct_in"] >= 99 for i in ("HUN", "PRY", "RWA", "LAO"))
assert [c["iso"] for c in dep[:2]] == ["KWT", "TKM"] and dep[2]["iso"] == "EGY"
for iso in ("EGY", "SDN", "TKM", "UZB", "BGD", "HUN", "ROU", "NLD"):
    assert C[iso]["dep"] > 75, iso
assert sy[0]["name"] == "Nile" and [s["name"] for s in sy[:4]] == ["Nile", "Yangtze", "Amazon", "Mississippi-Missouri"]
assert amazon["chain"][:2] == ["Amazon", "Ucayali"] and amazon["src"][1] < -15 and amazon["mxy"][0] < -52
assert "Kagera" in nile["chain"] and "Victoria Nile" in nile["chain"] and nile["src_iso"] in ("BDI", "RWA")
assert S["alts"]["nile_blue"]["len"] < nile["len"] and S["alts"]["miss_own"]["len"] < miss["len"]
assert named_top[0]["name"] == "Danube" and named_top[0]["n"] == 9 and "MDA" not in named_top[0]["countries"]
assert named_top[1]["n"] == named_top[2]["n"] == 6 and {named_top[1]["name"], named_top[2]["name"]} == {"Mekong", "Rhine"}
assert all(s["len50"] < s["len"] for s in sy[:12] if s.get("len50"))
assert all(s["v"] == sorted(s["v"], reverse=True) for s in scale)
assert all(p["map"] < p["km"] for p in published)
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: v for k, v in basins.items() if k not in ("top", "most_pop", "largest", "by_cont")}, ensure_ascii=False)[:1500])
print(countries["most_basins"][:4], countries["n_full"], countries["dep_n"], countries["dep_n_over50"])
print([(t["name"], t["len"], t["len50"]) for t in topr[:12]])
print(rivers["nile"], rivers["amazon"], rivers["nile_blue"]["len"], rivers["miss_own"]["len"], rivers["miss"])
print([(r["name"], r["n"]) for r in named_top[:8]], rivers["shrink_pct"], rivers["len50_pct"], published)
