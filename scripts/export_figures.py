"""Copy selected figures from the executed notebooks to docs/figures/ for the README and overview pages.

    python scripts/export_figures.py
"""
import base64
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"

# output name -> (notebook, which figure in that notebook, counting from 1)
FIGURES = {
    "domains.png": ("02_download_plan.ipynb", 1),
    "psl_bias.png": ("03_validation_baseline.ipynb", 2),
    "nao_patterns.png": ("04_nao.ipynb", 1),
    "rx1day_bias.png": ("05_extremes.ipynb", 2),
    "nao_r95p.png": ("06_nao_extremes.ipynb", 4),
    "member_spread.png": ("07_paired_experiment.ipynb", 3),
    "resolution.png": ("08_resolution.ipynb", 2),
    "event_composites.png": ("09_event_anatomy.ipynb", 1),
}


def images(notebook):
    nb = nbformat.read(ROOT / "notebooks" / notebook, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            for output in cell.get("outputs", []):
                if "data" in output and "image/png" in output["data"]:
                    yield base64.b64decode(output["data"]["image/png"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (notebook, number) in FIGURES.items():
        figure = list(images(notebook))[number - 1]
        (OUT / name).write_bytes(figure)
        print(f"{name:22s} <- {notebook} figure {number} ({len(figure) // 1024} kB)")


if __name__ == "__main__":
    main()
