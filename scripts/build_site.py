"""Assemble the project website in docs/ for GitHub Pages.

    python scripts/build_site.py

- docs/index.html               home page (the project overview)
- docs/engineering_overview.html how the data pipeline works
- docs/methods.html             the methods, rendered from docs/methods.md
- docs/explorer/index.html      the interactive explorer (data from build_explorer_data.py)
- docs/notebooks/               every executed notebook as a web page, plus an index
- docs/404.html, sitemap.xml, robots.txt, .nojekyll

Every page gets the same navigation bar, a footer (author, licence, data credits,
how to cite), a page title and description, and preview tags for search engines and
social media. Run scripts/build_all.ps1 (or nbconvert --to html) first, so
notebooks/html/ is current, and scripts/make_social_card.py for the preview image.
"""
import datetime as dt
import html as htmllib
import json
import re
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPO = "https://github.com/TunaHim/HighRes-EERIE-NorthAtlantic-Evaluation"
SITE = "https://tunahim.github.io/HighRes-EERIE-NorthAtlantic-Evaluation/"
NAME = "HighRes-EERIE-NorthAtlantic-Evaluation"
AUTHOR = "Himansu Kesari Pradhan"
YEAR = 2026
SUMMARY = ("How well do high-resolution climate models (EERIE: ICON-ESM-ER, IFS-FESOM2-SR) represent winter "
           "extremes over the UK and Ireland and their driver, the North Atlantic Oscillation? An evaluation "
           "against ERA5 and E-OBS, with resolution (9 km vs 28 km) and internal-variability tests.")

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

PAGES = {  # path relative to docs/ -> (title, description)
    "index.html": (f"{NAME}: winter extremes, the NAO and high-resolution climate models", SUMMARY),
    "engineering_overview.html": (
        f"How it is built · {NAME}",
        "How public climate-model output travels from the DKRZ data centre to the analysis: discovery, "
        "streaming, GRIB decoding, regridding, a tested regional archive and a reusable analysis library."),
    "methods.html": (
        f"Methods · {NAME}",
        "Methods fixed before any result: preprocessing, NAO definition, ETCCDI extreme indices, "
        "statistics with false-discovery-rate control, event composites and resolution tests."),
    "explorer/index.html": (
        f"Extremes explorer · {NAME}",
        "Interactive maps and yearly series of winter and annual extremes (RX1day, R95p, TXx) for E-OBS, "
        "ERA5, ICON-ESM-ER and IFS-FESOM2-SR over north-west Europe, with their link to the NAO."),
    "notebooks/index.html": (
        f"Notebooks · {NAME}",
        "Every analysis step as an executed Jupyter notebook: data inventory, mean climate, NAO, extremes, "
        "NAO-extremes link, SST experiment, resolution and event anatomy."),
    "404.html": (f"Page not found · {NAME}", SUMMARY),
}
for _key, _title in NOTEBOOKS.items():
    PAGES[f"notebooks/{_key}.html"] = (f"{_key[:2]} · {_title} · {NAME}",
                                       f"Executed notebook {_key[:2]} of {NAME}: {_title}")

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='7' fill='%232a78d6'/%3E"
           "%3Cpath d='M5 20c4-8 8-8 11 0s7 8 11 0' stroke='white' stroke-width='3' fill='none'/%3E%3C/svg%3E")

SITE_STYLE = """<style>
.sitenav{position:sticky;top:0;z-index:10;background:var(--surface,#fcfcfb);border-bottom:1px solid var(--line,#e1e0d9)}
.sitenav div{max-width:1100px;margin:0 auto;padding:10px 16px;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;font:14px system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.sitenav b{margin-right:8px;color:var(--ink,#0b0b0b)}
.sitenav a{color:var(--ink2,#52514e);text-decoration:none}
.sitenav a:hover,.sitenav a.here{color:var(--blue,#2a78d6)}
.sitefoot{border-top:1px solid var(--line,#e1e0d9);margin-top:32px;background:var(--surface,#fcfcfb);color:var(--ink2,#52514e)}
.sitefoot div.in{max-width:1100px;margin:0 auto;padding:18px 16px 26px;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px 28px;font:13px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.sitefoot b{display:block;color:var(--ink,#0b0b0b);margin-bottom:3px}
.sitefoot a{color:var(--blue,#2a78d6)}
.sitefoot p{margin:0}
</style>"""

MARKS = [("<!-- site:head -->", "<!-- /site:head -->"),
         ("<!-- site:nav -->", "<!-- /site:nav -->"),
         ("<!-- site:foot -->", "<!-- /site:foot -->")]


def prefix_for(path: str) -> str:
    return "../" * path.count("/")


def url_for(path: str) -> str:
    return SITE + ("" if path == "index.html" else path.removesuffix("index.html"))


def strip_site(html: str) -> str:
    """Remove everything this script added before, so pages edited in place can be rebuilt."""
    for start, end in MARKS:
        html = re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", html, flags=re.S)
    # blocks written by the earlier version of this script
    html = re.sub(r'<nav class="sitenav">.*?</nav>\n?', "", html, flags=re.S)
    html = re.sub(r"\n?<style>\n\.sitenav\{.*?</style>", "", html, flags=re.S)
    return html


def head(path: str) -> str:
    title, description = PAGES[path]
    title, description = htmllib.escape(title), htmllib.escape(description)
    tags = [
        f'<meta name="description" content="{description}">',
        f'<meta name="author" content="{AUTHOR}">',
        f'<link rel="canonical" href="{url_for(path)}">',
        f'<link rel="icon" href="{FAVICON}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{NAME}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{description}">',
        f'<meta property="og:url" content="{url_for(path)}">',
        f'<meta property="og:image" content="{SITE}figures/social_card.png">',
        '<meta name="twitter:card" content="summary_large_image">',
        SITE_STYLE,
    ]
    if path == "index.html":
        data = {
            "@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": NAME,
            "description": SUMMARY, "url": SITE, "codeRepository": REPO, "license": f"{REPO}/blob/main/LICENSE",
            "programmingLanguage": "Python", "author": {"@type": "Person", "name": AUTHOR},
            "keywords": ["climate model evaluation", "North Atlantic Oscillation", "precipitation extremes",
                         "EERIE", "high resolution", "ERA5", "E-OBS", "UK", "Ireland"],
        }
        tags.append(f'<script type="application/ld+json">{json.dumps(data)}</script>')
    start, end = MARKS[0]
    return start + "\n" + "\n".join(tags) + "\n" + end + "\n"


def nav(path: str) -> str:
    prefix = prefix_for(path)
    links = [
        ("index.html", "What was found"),
        ("engineering_overview.html", "How it is built"),
        ("methods.html", "Methods"),
        ("notebooks/index.html", "Notebooks"),
        ("explorer/index.html", "Explorer"),
    ]
    section = "notebooks/index.html" if path.startswith("notebooks/") else path
    here = ' class="here"'
    items = "".join(f'<a href="{prefix}{href}"{here if href == section else ""}>{label}</a>' for href, label in links)
    start, end = MARKS[1]
    return f'{start}<nav class="sitenav"><div><b>{NAME}</b>{items}<a href="{REPO}">Code on GitHub</a></div></nav>{end}\n'


def footer(path: str) -> str:
    prefix = prefix_for(path)
    today = dt.date.today()
    start, end = MARKS[2]
    return f"""{start}<footer class="sitefoot"><div class="in">
<div><b>{NAME}</b><p>An exploratory evaluation by {AUTHOR}, {YEAR}. Code under the
<a href="{REPO}/blob/main/LICENSE">MIT licence</a>; source, tests and notebooks on
<a href="{REPO}">GitHub</a>. Page built {today.day} {today:%B %Y}.</p></div>
<div><b>Data credits</b><p>EERIE model output: EERIE consortium (MPI-M, ECMWF, AWI and partners), served by DKRZ.
ERA5: Hersbach et al. (2020), Copernicus Climate Change Service. E-OBS: Cornes et al. (2018); we acknowledge the
E-OBS dataset and the data providers in the ECA&amp;D project.</p></div>
<div><b>How to cite</b><p>{AUTHOR} ({YEAR}). {NAME}: winter extremes, the NAO and high-resolution climate
models. {REPO} (<a href="{REPO}/blob/main/CITATION.cff">CITATION.cff</a>).<br>
<a href="{prefix}methods.html">Methods</a> · <a href="{REPO}/issues">Questions and comments</a></p></div>
</div></footer>{end}
"""


def decorate(html: str, path: str) -> str:
    html = strip_site(html)
    title = htmllib.escape(PAGES[path][0])
    if re.search(r"<title>.*?</title>", html, flags=re.S):
        html = re.sub(r"<title>.*?</title>", lambda m: f"<title>{title}</title>", html, count=1, flags=re.S)
    else:
        html = html.replace("</head>", f"<title>{title}</title>\n</head>", 1)
    html = html.replace("</head>", head(path) + "</head>", 1)
    html = re.sub(r"<body([^>]*)>\n?", lambda m: f"<body{m.group(1)}>\n{nav(path)}", html, count=1)
    return html.replace("</body>", footer(path) + "</body>", 1)


def notebook_key(number: str):
    return next((key for key in NOTEBOOKS if key.startswith(number)), None)


def link_notebook_mentions(html: str) -> str:
    """Turn 'Notebook 05' and 'Notebooks 07, 08' in the overview into links."""
    def one(number):
        key = notebook_key(number)
        return f'<a href="notebooks/{key}.html">{number}</a>' if key else number

    def repl(match):
        return match.group(1) + re.sub(r"\d{2}", lambda m: one(m.group(0)), match.group(2))

    return re.sub(r'(<div class="nb">Notebooks? )([0-9, ]+)', repl, html)


PLAIN_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e1e0d9;--blue:#2a78d6}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--blue:#3987e5}}}}
:root[data-theme="dark"]{{--bg:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--blue:#3987e5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:{width}px;margin:0 auto;padding:28px 16px 40px}}
h1{{font-size:26px;margin:0 0 8px}} h2{{font-size:19px;margin:34px 0 8px}} h3{{font-size:16px;margin:22px 0 6px}}
table{{border-collapse:collapse;width:100%;background:var(--surface);font-size:14px}}
.tw{{overflow-x:auto}}
td,th{{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}}
th{{color:var(--ink2)}}
code{{background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:13px}}
pre{{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;overflow-x:auto}}
pre code{{border:0;padding:0}}
a{{color:var(--blue)}}
.lead{{color:var(--ink2)}}
</style></head><body>
<main>
{body}
</main></body></html>"""


def plain_page(title: str, body: str, width: int = 900) -> str:
    body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    return PLAIN_PAGE.format(title=title, body=body, width=width)


def build_methods():
    body = mistune.create_markdown(plugins=["table"])((DOCS / "methods.md").read_text(encoding="utf-8"))
    body = re.sub(r"\b([Nn]otebooks?) (\d{2})\b", lambda m: (
        f'<a href="notebooks/{notebook_key(m.group(2))}.html">{m.group(1)} {m.group(2)}</a>'
        if notebook_key(m.group(2)) else m.group(0)), body)
    body += (f'<p class="lead">Source of this page: <a href="{REPO}/blob/main/docs/methods.md">docs/methods.md</a>. '
             "The code that implements each choice is in <code>src/eerie_uk/</code>.</p>")
    (DOCS / "methods.html").write_text(decorate(plain_page("Methods", body), "methods.html"), encoding="utf-8")


def build_notebooks():
    target = DOCS / "notebooks"
    target.mkdir(exist_ok=True)
    rows = []
    for key, title in NOTEBOOKS.items():
        source = ROOT / "notebooks" / "html" / f"{key}.html"
        if not source.exists():
            raise SystemExit(f"missing {source}: export the notebooks to HTML first")
        page = decorate(source.read_text(encoding="utf-8"), f"notebooks/{key}.html")
        (target / f"{key}.html").write_text(page, encoding="utf-8")
        rows.append(f'<tr><td><a href="{key}.html">{key}</a></td><td>{title}</td>'
                    f'<td><a href="{REPO}/blob/main/notebooks/{key}.ipynb">.ipynb</a></td></tr>')
    body = f"""<h1>Notebooks</h1>
<p class="lead">Every analysis step as an executed notebook. Each opens with a plain-language explanation of its
terms, has a note above every code cell and a caption under every figure, and ends with findings, limitations and
open questions. Start with 00.</p>
<table><thead><tr><th>Notebook</th><th>Question</th><th>Source</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table>
<p class="lead">To rerun them: clone the repository, create the conda environment from <code>environment.yml</code>,
download the regional data with <code>python -m eerie_uk.download</code> and run <code>scripts/build_all.ps1</code>.
Step-by-step instructions are in the <a href="{REPO}#reproduce">README</a>.</p>"""
    page = plain_page("Notebooks", body, width=1100)
    (target / "index.html").write_text(decorate(page, "notebooks/index.html"), encoding="utf-8")


def build_extras():
    body = ('<h1>Page not found</h1><p class="lead">This page does not exist. '
            f'Start from the <a href="{SITE}">home page</a>.</p>')
    page = decorate(plain_page("Page not found", body), "404.html")
    # the 404 page is served at any depth, so its links must be absolute
    page = re.sub(r'href="(?!https?:|#|data:)([^"]+)"', lambda m: f'href="{SITE}{m.group(1)}"', page)
    (DOCS / "404.html").write_text(page, encoding="utf-8")

    today = dt.date.today().isoformat()
    entries = "\n".join(f"  <url><loc>{url_for(p)}</loc><lastmod>{today}</lastmod></url>"
                        for p in PAGES if p != "404.html")
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n', encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")


def main():
    overview = (DOCS / "project_overview.html").read_text(encoding="utf-8")
    (DOCS / "index.html").write_text(decorate(link_notebook_mentions(overview), "index.html"), encoding="utf-8")
    for path in ("engineering_overview.html", "explorer/index.html"):
        page = DOCS / path
        page.write_text(decorate(page.read_text(encoding="utf-8"), path), encoding="utf-8")
    build_methods()
    build_notebooks()
    build_extras()
    print("site written to", DOCS)


if __name__ == "__main__":
    main()
