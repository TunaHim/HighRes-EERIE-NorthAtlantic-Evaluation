# Posters

Two complementary A0 landscape posters (1189 × 841 mm), print-ready PDF:

| File | Poster | Theme |
|---|---|---|
| [`poster_science.pdf`](poster_science.pdf) | North Atlantic Circulation and European Winter Extremes in High-Resolution Climate Models: model biases, internal variability and resolution sensitivity | scientific results (navy, blue, orange) |
| [`poster_engineering.pdf`](poster_engineering.pdf) | From Global Climate Archives to Reproducible Climate Diagnostics: an automated data processing and evaluation pipeline | research software and data engineering (navy, teal, green) |

Also on the website: <https://tunahim.github.io/HighRes-EERIE-NorthAtlantic-Evaluation/posters/>
(`scripts/build_site.py` copies the PDFs and previews to `docs/posters/`). `*_preview.png` are small previews. The posters are HTML pages (`poster_*.html`, shared `poster.css`)
printed to PDF by a headless Chromium browser.

## Rebuild

```bash
python scripts/build_poster_figures.py   # vector (SVG) figures from the notebooks into posters/figures/ (needs data/)
python scripts/build_site.py             # refreshes docs/figures/pipeline.svg, used by the engineering poster
python scripts/build_posters.py          # PDF and preview of both posters (Edge or Chrome; internet for the QR code library)
python scripts/build_site.py             # again, to copy the new PDFs to the website (docs/posters/)
```

`posters/figures/explorer_crop.png` is a screenshot of the interactive explorer (2× resolution), cropped
to the toolbar, map and NAO panel. The SVG figures are generated and not kept in git.
