"""Assemble the project website in docs/ for GitHub Pages.

    python scripts/build_site.py

- docs/index.html               home page (the project overview) with a navigation bar
- docs/engineering_overview.html with the same navigation bar
- docs/notebooks/               every executed notebook as a web page, plus an index
- docs/.nojekyll                serve files as they are

Run scripts/build_all.ps1 (or nbconvert --to html) first, so notebooks/html/ is current.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPO = "https://github.com/TunaHim/HighRes-EERIE-NorthAtlantic-Evaluation"

NOTEBOOKS = {
    "00_summary": "Summary: the whole story in seven figures",
    "01_data_inventory": "Which public EERIE data exist and can be read",
    "02_download_plan": "Data plan: domains, datasets, periods and cost",
    "03_validation_baseline": "Is the mean winter climate credible?",
    "04_nao": "Is the NAO realistic in pattern and strength?",
    "05_extremes": "Extremes: RX1day, TXx and R95p",
    "06_nao_extremes": "Do the models link the NAO to extremes as the real world does?",
    "07_paired_experiment": "Is the NAO sensitive to small-scale sea-surface temperature?",
    "08_resolution": "Does 9 km resolution improve winter rain extremes over 28 km?",
    "09_event_anatomy": "What weather brings the heaviest winter rain?",
}

NAV_STYLE = """
<style>
.sitenav{position:sticky;top:0;z-index:10;background:var(--surface,#fcfcfb);border-bottom:1px solid var(--line,#e1e0d9)}
.sitenav div{max-width:1100px;margin:0 auto;padding:10px 16px;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;font:14px system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.sitenav b{margin-right:8px;color:var(--ink,#0b0b0b)}
.sitenav a{color:var(--ink2,#52514e);text-decoration:none}
.sitenav a:hover,.sitenav a.here{color:var(--blue,#2a78d6)}
</style>"""


def nav(here: str, prefix: str = "") -> str:
    links = [
        ("index.html", "What was found"),
        ("engineering_overview.html", "How it is built"),
        ("notebooks/index.html", "Notebooks"),
    ]
    if (DOCS / "explorer" / "index.html").exists():
        links.append(("explorer/index.html", "Explorer"))
    current = ' class="here"'
    items = "".join(
        f'<a href="{prefix}{href}"{current if href == here else ""}>{label}</a>' for href, label in links
    )
    return f'<nav class="sitenav"><div><b>HighRes-EERIE-NorthAtlantic-Evaluation</b>{items}<a href="{REPO}">Code on GitHub</a></div></nav>'


def with_nav(html: str, here: str, prefix: str = "") -> str:
    html = html.replace("</head>", NAV_STYLE + "\n</head>", 1)
    return re.sub(r"<body([^>]*)>", lambda m: f"<body{m.group(1)}>\n{nav(here, prefix)}", html, count=1)


def link_notebook_mentions(html: str) -> str:
    """Turn 'Notebook 05' and 'Notebooks 07, 08' in the overview into links."""
    names = {key[:2]: key for key in NOTEBOOKS}

    def one(number):
        key = names.get(number)
        return f'<a href="notebooks/{key}.html">{number}</a>' if key else number

    def repl(match):
        numbers = re.sub(r"\d{2}", lambda m: one(m.group(0)), match.group(2))
        return match.group(1) + numbers

    return re.sub(r'(<div class="nb">Notebooks? )([0-9, ]+)', repl, html)


def main():
    overview = (DOCS / "project_overview.html").read_text(encoding="utf-8")
    (DOCS / "index.html").write_text(with_nav(link_notebook_mentions(overview), "index.html"), encoding="utf-8")

    engineering = (DOCS / "engineering_overview.html").read_text(encoding="utf-8")
    engineering = re.sub(r'<nav class="sitenav">.*?</nav>\n?', "", engineering, flags=re.S)
    engineering = engineering.replace(NAV_STYLE + "\n", "")
    (DOCS / "engineering_overview.html").write_text(with_nav(engineering, "engineering_overview.html"), encoding="utf-8")

    target = DOCS / "notebooks"
    target.mkdir(exist_ok=True)
    rows = []
    for key, title in NOTEBOOKS.items():
        source = ROOT / "notebooks" / "html" / f"{key}.html"
        if not source.exists():
            raise SystemExit(f"missing {source}: export the notebooks to HTML first")
        shutil.copyfile(source, target / f"{key}.html")
        rows.append(f'<tr><td><a href="{key}.html">{key}</a></td><td>{title}</td>'
                    f'<td><a href="{REPO}/blob/main/notebooks/{key}.ipynb">.ipynb</a></td></tr>')
    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notebooks</title>
<style>
:root{{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e1e0d9;--blue:#2a78d6}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--blue:#3987e5}}}}
:root[data-theme="dark"]{{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--blue:#3987e5}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 64px}}
table{{border-collapse:collapse;width:100%;background:var(--surface)}} td,th{{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left}}
a{{color:var(--blue)}}
</style></head><body>
<main><h1>Notebooks</h1>
<p>Every analysis step as an executed notebook. Each opens with a plain-language explanation of its terms,
has a note above every code cell and a caption under every figure, and ends with findings, limitations
and open questions. Start with 00.</p>
<table><thead><tr><th>Notebook</th><th>Question</th><th>Source</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table></main></body></html>"""
    (target / "index.html").write_text(with_nav(index, "notebooks/index.html", "../"), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print("site written to", DOCS)


if __name__ == "__main__":
    main()
