"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
Placeholders https://doi.org/10.5281/zenodo.23848927 and https://blog.tristanhotham.com/2026/10/31/shared-rivers/ are left for the publisher unless DOI= / BLOG_URL= are set in the environment.
Zenodo copies of files that also live elsewhere in the repo are hard links, so they take no extra disk."""
import re, zipfile
from common import *

R = jload(f"{DATA}/results.json"); B = jload(f"{WORK}/basins.json")["basins"]; C = jload(f"{WORK}/countries.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Who_Shares_the_Worlds_Rivers"

# facts stated in words or numbers in the blog alt text (the rest are tokens)
dsh = {k: p for k, p, a in B["DANU"]["share"]}; nsh = {k: p for k, p, a in B["NILE"]["share"]}
assert (round(dsh["ROU"]), round(dsh["HUN"]), round(dsh["SRB"]), round(dsh["AUT"]), round(dsh["DEU"])) == (29, 12, 10, 10, 7)
assert (round(nsh["SDN"]), round(nsh["SSD"]), round(nsh["ETH"]), round(nsh["EGY"]), round(nsh["UGA"])) == (43, 21, 12, 8, 8)
assert R["rivers"]["top"][0]["len"] == 6151 and R["rivers"]["top"][14]["name"] == "Volga"
assert R["rivers"]["scale"][0]["v"][-1] == 5175 and round(100 * R["rivers"]["scale"][1]["v"][-1] / R["rivers"]["scale"][1]["v"][0]) == 76
assert all(85 <= v <= 93 for v in R["rivers"]["len50_pct"].values())          # "about a tenth" shorter on the 1:50m lines
assert all(C[i]["dep"] >= 90 for i in ("EGY", "SDN", "MRT", "TKM", "HUN", "BGD"))
assert all(C[i]["dep"] < 10 for i in ("RUS", "CAN", "USA", "CHN", "AUS")) and C["ARG"]["dep"] > 50
assert R["rivers"]["nile"]["src_country"] == "Burundi"
assert C["KWT"]["dep"] > C["TKM"]["dep"] and C["BHR"]["dep"] > 96

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
if os.environ.get("DOI"):
    post = post.replace("https://doi.org/10.5281/zenodo.23848927", "https://doi.org/" + os.environ["DOI"])
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert all(re.fullmatch(r"\{\{IMG\|[^}]*\}\}", ln) for ln in post.splitlines() if "{{IMG|" in ln)   # each image token on its own line
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}|BLOG_URL\})", post)
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
b, r = R["basins"], R["rivers"]
meta = {"title": "Who shares the world's rivers? 313 basins, 19 countries on the Danube, and why nobody agrees on the longest river",
        "slug": "shared-rivers",
        "excerpt": f"{b['n']} river basins cross a border. They drain {b['area_pct']:.0f}% of the world's land outside Antarctica and hold {b['pop_pct']:.0f}% of its people. I mapped them, measured the great rivers on one map, and found the longest river depends on who holds the ruler.",
        "seo_description": f"A map of the world's {b['n']} shared river basins and the countries in each, the longest rivers measured on one map, and who depends on water from upstream.",
        "tags": ["rivers", "river basins", "water", "transboundary", "Danube", "Nile", "maps", "data visualisation"],
        "header_alt": f"Title card reading 'Who shares the world's rivers?' in dark ink on pale paper, with the number {b['n']} in blue and the line: river basins cross a border; they drain {b['area_pct']:.0f}% of the land outside Antarctica and hold {b['pop_pct']:.0f}% of the world's people. Beside it, a world map of the shared basins shaded from pale green to deep indigo by the number of countries sharing each, darkest over the Danube, Nile, Niger and Congo, with blue rivers."}
assert str(b["n"]) in meta["title"] and str(b["top"][0]["n"]) in meta["title"]
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# ---------- Zenodo ----------
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
for f in ("basins.csv", "basin_countries.csv", "countries.csv", "river_systems.csv", "named_rivers.csv", "results.json"):
    link(f"{DATA}/{f}", f"{Z}/{f}")
zp = f"{Z}/shared-rivers_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"shared-rivers/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"shared-rivers/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "Who Shares the World's Rivers? International River Basins, River Lengths Measured on One Map, and the Countries that Depend on Water from Upstream",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/shared-rivers/. Data and code: https://github.com/Tristan-Hotham/shared-rivers.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["rivers", "international river basins", "transboundary water", "river length", "map scale", "water dependency", "Natural Earth", "TFDD", "AQUASTAT"],
         "license": "cc-by-4.0",
         "notes": "Derived TFDD tables are shared for non-commercial research with credit to the Transboundary Freshwater Dispute Database, Oregon State University; the AQUASTAT column is FAO data under CC BY-NC-SA 3.0 IGO. Code is MIT.",
         "related_identifiers": [{"identifier": "https://github.com/Tristan-Hotham/shared-rivers", "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": "https://maps.tristanhotham.com/shared-rivers/", "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://transboundarywaters.ceoas.oregonstate.edu/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.fao.org/aquastat/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = json.dumps(zmeta, ensure_ascii=False) + json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
