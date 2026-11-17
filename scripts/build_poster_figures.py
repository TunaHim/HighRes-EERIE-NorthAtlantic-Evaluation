"""Vector (SVG) versions of the figures used on the A0 posters (posters/figures/).

    python scripts/build_poster_figures.py

The website figures are PNG at screen resolution, too coarse for A0 print. This script executes
temporary copies of the notebooks with matplotlib's inline output switched to SVG and saves the
selected figures. The notebooks in notebooks/ are not changed. Needs the downloaded data (data/).
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "posters" / "figures"

# output name -> (notebook, which figure in that notebook, counting from 1); same numbering as export_figures.py
FIGURES = {
    "experiment_design.svg": ("00_summary.ipynb", 1),
    "overview.svg": ("00_summary.ipynb", 2),
    "summary_chain.svg": ("00_summary.ipynb", 3),
    "members_link.svg": ("10_members.ipynb", 4),
    "control_windows.svg": ("11_control.ipynb", 1),
    "control_placement.svg": ("11_control.ipynb", 3),
    "hadgem_psl_bias.svg": ("12_hadgem_resolution.ipynb", 1),
    "resolution_ladder.svg": ("12_hadgem_resolution.ipynb", 6),
}


def svg_figures(notebook: str) -> list[str]:
    nb = nbformat.read(ROOT / "notebooks" / notebook, as_version=4)
    nb.cells.insert(0, nbformat.v4.new_code_cell("%config InlineBackend.figure_formats = ['svg']"))
    NotebookClient(nb, timeout=6000, kernel_name="python3",
                   resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
    found = []
    for cell in nb.cells:
        for output in cell.get("outputs", []):
            if "data" in output and "image/svg+xml" in output["data"]:
                found.append(output["data"]["image/svg+xml"])
    return found


def main(selected=None):
    OUT.mkdir(parents=True, exist_ok=True)
    notebooks = sorted({nb for nb, _ in FIGURES.values()})
    for notebook in notebooks:
        if selected and not any(notebook.startswith(s) for s in selected):
            continue
        print("running", notebook, flush=True)
        figures = svg_figures(notebook)
        for name, (nb, number) in FIGURES.items():
            if nb == notebook:
                (OUT / name).write_text(figures[number - 1], encoding="utf-8")
                print(f"  {name:24s} <- figure {number} ({len(figures[number - 1]) // 1024} kB)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
