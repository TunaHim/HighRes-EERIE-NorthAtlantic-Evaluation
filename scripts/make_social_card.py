"""Draw the 1200 x 630 preview image used when the website or repository is shared.

    python scripts/make_social_card.py

Writes docs/figures/social_card.png (also suitable for GitHub's "Social preview" setting).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figures"


def main():
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#f9f9f7")
    fig.text(0.05, 0.86, "HighRes-EERIE-NorthAtlantic-Evaluation", fontsize=30, weight="bold", color="#0b0b0b")
    fig.text(0.05, 0.77, "Winter extremes over the UK and Ireland, their atmospheric drivers,\n"
             "and how far high-resolution climate models can be trusted", fontsize=17, color="#52514e", va="top")
    fig.text(0.05, 0.08, "ICON-ESM-ER · IFS-FESOM2-SR · ERA5 · E-OBS  |  NAO · RX1day · TXx · R95p · 9 km vs 28 km",
             fontsize=13, color="#2a78d6")
    image = mpimg.imread(FIGURES / "nao_patterns.png")
    ax = fig.add_axes([0.05, 0.14, 0.9, 0.52])
    ax.imshow(image)
    ax.set_axis_off()
    target = FIGURES / "social_card.png"
    fig.savefig(target, facecolor=fig.get_facecolor())
    print("wrote", target)


if __name__ == "__main__":
    main()
