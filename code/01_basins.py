"""International river basins from the Transboundary Freshwater Dispute Database (TFDD), with the FAO AQUASTAT
dependency ratio and country areas from Natural Earth.

Inputs: RAWS/tfdd/BasinMaster313_20240807.csv (the 2024 register: 313 basins, riparian lists, area, population),
RAWS/tfdd/Basin310_Master_20180511.geojson and BCU310_Master_20180511.geojson (the 2018 polygons of 310 basins and
their 812 basin country units), RAWS/aquastat/pycon_aquastat.csv.gzip, GEO/ne_10m_admin_0_countries.geojson,
RAWS/ne/ne_10m_land.geojson, WB (World Bank population).
Outputs: WORK/basins.json, WORK/countries.json, data/basins.csv, data/basin_countries.csv, data/countries.csv,
data/basins.geojson, data/bcu.geojson (simplified polygons for the page)."""
import csv
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from pyproj import Geod
from common import *

G84 = Geod(ellps="WGS84")
T = f"{RAWS}/tfdd"

# ---------- countries (Natural Earth) ----------
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
FIX = {"France": "FRA", "Norway": "NOR", "Kosovo": "XKX", "Somaliland": "SOM", "N. Cyprus": "CYP", "Northern Cyprus": "CYP"}
CN, CGEOM = {}, {}
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3"] if p["ISO_A3"] not in ("-99", None) else FIX.get(p["NAME"], p["ADM0_A3"])
    if p["ADM0_A3"] == "SDS": iso = "SSD"
    g = shape(f["geometry"]).buffer(0)
    CGEOM[iso] = unary_union([CGEOM[iso], g]) if iso in CGEOM else g
    CN.setdefault(iso, p["NAME"])
CN.update({"USA": "United States", "COD": "DR Congo", "COG": "Congo", "CAF": "Central African Republic", "TZA": "Tanzania",
           "BIH": "Bosnia and Herzegovina", "MKD": "North Macedonia", "LAO": "Laos", "PRK": "North Korea", "KOR": "South Korea",
           "SSD": "South Sudan", "CIV": "Côte d'Ivoire", "CZE": "Czechia", "RUS": "Russia", "IRN": "Iran", "SYR": "Syria",
           "VNM": "Vietnam", "MDA": "Moldova", "PSE": "Palestine", "SWZ": "Eswatini", "GNQ": "Equatorial Guinea", "DOM": "Dominican Republic",
           "GBR": "United Kingdom", "TLS": "Timor-Leste", "BOL": "Bolivia", "VEN": "Venezuela"})


def geod_area(g):
    a = 0.0
    for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        a += abs(G84.geometry_area_perimeter(poly)[0])
    return a / 1e6


CAREA = {iso: geod_area(g) for iso, g in CGEOM.items()}

# world land area outside Antarctica (Natural Earth land, geodesic)
land = []
for f in jload(f"{RAWS}/ne/ne_10m_land.geojson")["features"]:
    g = shape(f["geometry"])
    land += list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
LAND_ALL = sum(geod_area(g) for g in land)
LAND_X_ANT = sum(geod_area(g) for g in land if g.bounds[3] > -60)   # polygon by polygon: Antarctica lies wholly south of 60 S

# world population (World Bank)
wb = pd.read_csv(WB)
WPOP = {int(y): int(v) for y, v in wb[wb["Country Code"] == "WLD"][["Year", "Value"]].values}
CPOP = {(c, int(y)): int(v) for c, y, v in wb[["Country Code", "Year", "Value"]].values}

# ---------- TFDD ----------
B18 = jload(f"{T}/Basin310_Master_20180511.geojson")
U18 = jload(f"{T}/BCU310_Master_20180511.geojson")
M24 = pd.read_csv(f"{T}/BasinMaster313_20240807.csv", encoding="utf-8-sig")
DISPUTED = {"Abyei", "Aksai Chin", "Arunachal Pradesh", "China/India", "Hala'ib triangle", "Ilemi triangle", "Jammu and Kashmir", "Ma'tan al-Sarra"}
CC2ISO = {"ROM": "ROU", "ZAR": "COD", "MFD": "MKD", "PAL": "PSE", "GUF": "FRA"}   # TFDD codes that are not ISO 3166 alpha-3
NAME2ISO = {}
for f in U18["features"]:
    p = f["properties"]
    NAME2ISO[p["adm0_name"]] = CC2ISO.get(p["CCODE"], p["CCODE"])
NAME2ISO.update({"Cote d'Ivoire": "CIV", "Eswatini": "SWZ", "Moldova, Republic of": "MDA", "Republic of North Macedonia": "MKD",
                 "French Guiana": "FRA", "West Bank": "PSE"})


def split_riparians(s):
    s = s.replace("Moldova, Republic of", "Moldova; Republic of")
    out = []
    for x in s.split(","):
        x = x.strip().replace("Moldova; Republic of", "Moldova, Republic of")
        if x:
            out.append(x)
    return out


basins = {}
for r in M24.to_dict("records"):
    names = split_riparians(r["Riparian_C"])
    assert len(names) == r["NumberRipa"], (r["BCODE"], names, r["NumberRipa"])
    iso, disp = [], []
    for nm in names:
        if nm in DISPUTED:
            disp.append(nm)
            continue
        i = NAME2ISO[nm]
        if i == "PSE" or nm == "West Bank":
            i = "PSE"
        if i not in iso:
            iso.append(i)
    basins[r["BCODE"]] = {"code": r["BCODE"], "name": r["Basin_Name"], "cont": r["Continent_"], "area": float(r["Area_km2"]),
                          "pop": float(r["Pop_2022"]) if r["Pop_2022"] == r["Pop_2022"] else None,
                          "tfdd_n": int(r["NumberRipa"]), "iso": sorted(iso, key=lambda i: CN.get(i, i)), "n": len(iso), "disputed": disp,
                          "dams": int(r["Dams_Exist"]) if r["Dams_Exist"] == r["Dams_Exist"] else None,
                          "treaties": int(r["Count_of_T"]) if r["Count_of_T"] == r["Count_of_T"] else 0,
                          "has_poly": False, "share": []}
DISPLAY = {"CNGO": "Congo", "TIGR": "Tigris-Euphrates", "GANG": "Ganges-Brahmaputra-Meghna", "RHIN": "Rhine-Meuse", "LKCH": "Lake Chad",
           "ARAL": "Aral Sea (Amu Darya and Syr Darya)", "LPLA": "La Plata (Paraná)", "AMUR": "Amur", "OBXX": "Ob", "JORD": "Jordan"}
for k, v in DISPLAY.items():
    if k in basins:
        basins[k]["display"] = v
for b in basins.values():
    b.setdefault("display", b["name"])

# 2018 polygons and basin country units
BPOLY = {}
for f in B18["features"]:
    c = f["properties"]["BCODE"]
    BPOLY[c] = shape(f["geometry"]).buffer(0)
    basins[c]["has_poly"] = True
bcu = []
for f in U18["features"]:
    p = f["properties"]
    c, nm = p["BCODE"], p["adm0_name"]
    iso = "DISPUTED" if nm in DISPUTED else NAME2ISO[nm]
    bcu.append({"code": c, "basin": basins[c]["display"], "unit": nm, "iso": iso, "status": p["FIRST_stat"], "area": float(p["Area_km2"]),
                "pop2020": float(p["Pop_2020"]) if p["Pop_2020"] is not None else None, "geom": shape(f["geometry"]).buffer(0)})
for b in basins.values():
    us = [u for u in bcu if u["code"] == b["code"]]
    tot = sum(u["area"] for u in us)
    agg = {}
    for u in us:
        k = u["unit"] if u["iso"] == "DISPUTED" else u["iso"]
        agg[k] = agg.get(k, 0) + u["area"]
    b["share"] = sorted([[k, round(100 * a / tot, 2), round(a)] for k, a in agg.items()], key=lambda x: -x[1]) if tot else []

# ---------- countries: share of land in international basins ----------
carea_in = {}
for u in bcu:
    if u["iso"] != "DISPUTED":
        carea_in[u["iso"]] = carea_in.get(u["iso"], 0) + u["area"]
cbasins = {}
for b in basins.values():
    for i in b["iso"]:
        cbasins.setdefault(i, []).append(b["code"])

# ---------- AQUASTAT dependency ratio ----------
AQ = pd.read_csv(f"{RAWS}/aquastat/pycon_aquastat.csv.gzip", compression="gzip")
aq = AQ[AQ.variable_full == "Dependency ratio (%)"].dropna(subset=["value"]).sort_values("time_period").groupby("country").last()
AQN = {norm(v): k for k, v in CN.items()}
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3"] if p["ISO_A3"] not in ("-99", None) else FIX.get(p["NAME"], p["ADM0_A3"])
    for fld in ("NAME", "NAME_LONG", "ADMIN", "FORMAL_EN", "NAME_SORT"):
        if p.get(fld):
            AQN.setdefault(norm(p[fld]), iso)
AQN.update({norm(k): v for k, v in {"Bolivia (Plurinational State of)": "BOL", "Venezuela (Bolivarian Republic of)": "VEN", "Iran (Islamic Republic of)": "IRN",
            "Republic of Moldova": "MDA", "United Republic of Tanzania": "TZA", "Democratic Republic of the Congo": "COD", "Congo": "COG",
            "Lao People's Democratic Republic": "LAO", "Viet Nam": "VNM", "Syrian Arab Republic": "SYR", "Russian Federation": "RUS",
            "Republic of Korea": "KOR", "Democratic People's Republic of Korea": "PRK", "The former Yugoslav Republic of Macedonia": "MKD",
            "Côte d'Ivoire": "CIV", "Cabo Verde": "CPV", "Swaziland": "SWZ", "Czech Republic": "CZE", "Sudan (former)": None, "South Sudan": "SSD",
            "West Bank and Gaza Strip": "PSE", "Occupied Palestinian Territory": "PSE", "United Kingdom": "GBR", "United States of America": "USA",
            "Micronesia (Federated States of)": "FSM", "Brunei Darussalam": "BRN", "Gambia": "GMB", "Bahamas": "BHS", "Timor-Leste": "TLS"}.items()})
dep, dep_unmatched = {}, []
for name, row in aq.iterrows():
    iso = AQN.get(norm(name))
    if iso is None:
        dep_unmatched.append(name)
        continue
    dep[iso] = {"dep": float(row["value"]), "period": row["time_period"], "year": int(row["year_measured"]) if row["year_measured"] == row["year_measured"] else None, "aq_name": name}
irwr = AQ[AQ.variable_full == "Total renewable water resources (10^9 m3/year)"].dropna(subset=["value"]).sort_values("time_period").groupby("country").last()
for name, row in irwr.iterrows():
    iso = AQN.get(norm(name))
    if iso in dep:
        dep[iso]["trwr"] = float(row["value"])
ext = AQ[AQ.variable_full == "Water resources: total external renewable (10^9 m3/year)"].dropna(subset=["value"]).sort_values("time_period").groupby("country").last()
for name, row in ext.iterrows():
    iso = AQN.get(norm(name))
    if iso in dep:
        dep[iso]["ext"] = float(row["value"])

countries = {}
for iso in sorted(set(CAREA) | set(dep) | set(cbasins)):
    if iso not in CAREA:
        continue
    a_in = carea_in.get(iso, 0.0)
    countries[iso] = {"iso": iso, "name": CN.get(iso, iso), "area": round(CAREA[iso]), "area_in": round(a_in),
                      "pct_in": round(min(100.0, 100 * a_in / CAREA[iso]), 1) if CAREA[iso] > 0 else 0.0,
                      "basins": sorted(cbasins.get(iso, []), key=lambda c: -basins[c]["area"]),
                      "pop2022": CPOP.get((iso if iso != "XKX" else "XKX", 2022))}
    if iso in dep:
        countries[iso].update({"dep": dep[iso]["dep"], "dep_period": dep[iso]["period"], "trwr": dep[iso].get("trwr"), "ext": dep[iso].get("ext")})

out_b = {c: {k: v for k, v in b.items()} for c, b in basins.items()}
jsave({"basins": out_b, "land_all": LAND_ALL, "land_x_ant": LAND_X_ANT, "wpop": WPOP, "dep_unmatched": dep_unmatched,
       "n_bcu": len(bcu)}, f"{WORK}/basins.json")
jsave(countries, f"{WORK}/countries.json")

# ---------- reusable tables ----------
with open(f"{DATA}/basins.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["bcode", "basin", "continent", "area_km2", "population_2022", "n_countries", "countries_iso3", "disputed_areas", "tfdd_riparian_count", "polygon_2018"])
    for b in sorted(basins.values(), key=lambda b: (-b["n"], -b["area"])):
        w.writerow([b["code"], b["display"], b["cont"], round(b["area"]), round(b["pop"]) if b["pop"] else "", b["n"], " ".join(b["iso"]),
                    "; ".join(b["disputed"]), b["tfdd_n"], "yes" if b["has_poly"] else "no"])
with open(f"{DATA}/basin_countries.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["bcode", "basin", "unit", "iso3", "status", "area_km2", "pct_of_basin", "pct_of_country", "population_2020"])
    for u in sorted(bcu, key=lambda u: (u["basin"], -u["area"])):
        tot = sum(x["area"] for x in bcu if x["code"] == u["code"])
        pc = 100 * u["area"] / CAREA[u["iso"]] if u["iso"] in CAREA and CAREA[u["iso"]] else ""
        w.writerow([u["code"], u["basin"], u["unit"], u["iso"], u["status"], round(u["area"]), round(100 * u["area"] / tot, 2),
                    round(min(pc, 100), 2) if pc != "" else "", round(u["pop2020"]) if u["pop2020"] else ""])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["iso3", "country", "area_km2_natural_earth", "area_km2_in_international_basins", "pct_in_international_basins",
                "n_international_basins", "aquastat_dependency_ratio_pct", "aquastat_period", "aquastat_total_renewable_water_km3"])
    for c in sorted(countries.values(), key=lambda c: c["name"]):
        w.writerow([c["iso"], c["name"], c["area"], c["area_in"], c["pct_in"], len(c["basins"]), c.get("dep", ""), c.get("dep_period", ""), c.get("trwr", "")])


# ---------- simplified polygons for the page ----------
def simp(g, tol):
    s = g.simplify(tol, preserve_topology=True)
    return s if not s.is_empty else g


def rnd(geom, nd=3):
    m = mapping(geom)
    def r(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], (int, float)) else [r(x) for x in c]
    m["coordinates"] = r(m["coordinates"])
    return m


feats = []
for c, g in BPOLY.items():
    b = basins[c]
    feats.append({"type": "Feature", "properties": {"c": c, "n": b["n"]}, "geometry": rnd(simp(g, 0.025))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/basins.geojson")
feats = []
for u in bcu:
    feats.append({"type": "Feature", "properties": {"c": u["code"], "u": u["unit"], "i": u["iso"]}, "geometry": rnd(simp(u["geom"], 0.03))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/bcu.geojson")
print("basins", len(basins), "with polygons", len(BPOLY), "bcu", len(bcu), "countries", len(countries), "dep", len(dep), "unmatched", dep_unmatched)
print("land (excl. Antarctica) km2", round(LAND_X_ANT), "sum basin area", round(sum(b["area"] for b in basins.values())))
for f in ("basins.geojson", "bcu.geojson"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
