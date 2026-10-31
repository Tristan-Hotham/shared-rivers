"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
The DOI is not known until Zenodo reserves it: run with DOI=10.5281/zenodo.NNN to print it; without it the PDF shows
the placeholder 10.5281/zenodo.23848927."""
import re, subprocess
from common import *

R = jload(f"{DATA}/results.json"); B = jload(f"{WORK}/basins.json")["basins"]; C = jload(f"{WORK}/countries.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Who_Shares_the_Worlds_Rivers"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
DOI_ENV = os.environ.get("DOI")
DOI_URL = f"https://doi.org/{DOI_ENV}" if DOI_ENV else None


def tfmt(v, f):
    s = fmt(v, f)
    return s.replace("%", "\\%") if f in ("pc", "pc1") else tex(s) if f in (None, "raw") else s


b, r, c = R["basins"], R["rivers"], R["countries"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was used and licences.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.4cm}>{\\raggedright\\arraybackslash}p{6.9cm}>{\\raggedright\\arraybackslash}p{3.6cm}}\\toprule Source & Used & Licence\\\\\\midrule\n"
      f"TFDD 2024 register & {b['n']} international basins: riparian countries, area, population 2022 & Free for research, with credit\\\\\n"
      f"TFDD 2018 spatial data & {b['n_poly']} basin polygons, {b['n_bcu']} basin country units & Free for research, with credit\\\\\n"
      f"Natural Earth 1:10m, 1:50m & {r['n_lines']:,} and {r['n50_lines']} river centrelines; lakes, land, countries & Public domain\\\\\n"
      f"FAO AQUASTAT (2017 download) & Dependency ratio, {c['dep_n']} countries, 2013 to 2017 & CC BY-NC-SA 3.0 IGO\\\\\n"
      "World Bank WDI & World population 2022 & CC BY 4.0\\\\\n"
      "Encyclopaedia Britannica & Published lengths of three rivers & Quoted\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for t in b["top"][:16]:
    bb = B[t["code"]]
    big = ", ".join(f"{tex(C[k]['name'])} {p:.0f}\\%" for k, p, a in bb["share"][:3] if k in C)
    rows += f"{tex(t['name'])} & {t['n']} & {t['area']:,} & {t['pop_m']:,.1f} & {big}\\\\\n"
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The international basins shared by most countries. Area and population (2022) from the TFDD; largest shares from the basin country units.}\\label{tab:top}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.6cm}rrr>{\\raggedright\\arraybackslash}p{5.4cm}}\\toprule Basin & Countries & Area km\\textsuperscript{2} & People (m) & Largest shares\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for t in r["top"][:15]:
    rows += f"{t['rank']} & {tex(t['name'])} & {t['len']:,} & {t['len50']:,} & {t['n']} & {tex(' < '.join(t['chain'][:4]))}\\\\\n" if t["len50"] else \
            f"{t['rank']} & {tex(t['name'])} & {t['len']:,} & n/a & {t['n']} & {tex(' < '.join(t['chain'][:4]))}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{The longest river systems on the Natural Earth lines: mouth to most distant source (km), countries along that path, and the first rivers on the path from the mouth. n/a: no matching system on the 1:50m lines.}\\label{tab:rivers}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{rlrrr>{\\raggedright\\arraybackslash}p{6.2cm}}\\toprule & System & 1:10m & 1:50m & Countries & Path from the mouth\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for t in c["dep_top"][:16]:
    rows += f"{tex(t['name'])} & {t['dep']:.1f}\\\\\n"
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{The highest AQUASTAT dependency ratios (\\% of total renewable water resources originating outside the country), 2013 to 2017.}\\label{tab:dep}\\label{fig:depbars}"
      "\\begin{tabular}{lr}\\toprule Country & Dependency ratio (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/10.5281/zenodo.23848927}{https://doi.org/10.5281/zenodo.23848927}", f"\\href{https://doi.org/10.5281/zenodo.23848927}{https://doi.org/10.5281/zenodo.23848927}" if DOI_URL else "\\texttt{\\{\\{DOI\\}\\}}")
t = re.sub(r"\{\{(?!TABLE_|DOI_URL\})([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3)), t)
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_TOP}}", TT).replace("{{TABLE_RIVERS}}", TR).replace("{{TABLE_DEP}}", TD)
assert "{{" not in t.replace("\\{\\{DOI\\}\\}", ""), re.findall(r"\{\{[^}]*\}\}", t)[:5]
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q):
        os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", p.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
