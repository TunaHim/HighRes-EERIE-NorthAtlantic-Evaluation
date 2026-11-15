HadGEM3-GC5E historical runs at three resolutions, one member each, monthly data. NAO, rain link and jet over 1951–2014 (64 winters); mean state over 1986–2014. ICON-ESM-ER and IFS-FESOM2-SR r1 for context.

| | HadGEM3 LL (~135 km) | HadGEM3 MM (~60 km) | HadGEM3 HH (~20 km) | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|---|---|---|
| Winter pressure error vs ERA5 (RMS, hPa) | 3.2 | 2.7 | **2.6** | 5.7 | 1.8 |
| Mean circulation offset along NAO (SD) | −0.3 | −0.5 | −0.1 | +2.1 | +0.2 |
| NAO strength vs ERA5 (whole period) | 0.78 | 0.92 | 0.76 | 0.59 | 0.71 |
| … first / second half of the record | 0.75 / 0.86 | 1.16 / 0.82 | 0.97 / 0.68 | 0.74 / 0.53 | 0.75 / 0.75 |
| Own NAO pattern vs ERA5 (pattern correlation) | 0.92 | 0.95 | **0.98** | 0.75 | 0.87 |
| Winter rain, UK and Ireland land, vs ERA5 | +7% | +8% | **+25%** | +72% | +19% |
| Winter temperature, UK and Ireland land, vs ERA5 | 0.0 °C | −0.8 °C | −0.1 °C | −0.9 °C | −1.2 °C |
| NAO rainfall response map vs ERA5 (pattern correlation, land) | 0.94 | 0.94 | 0.96 | 0.93 | 0.93 |
| Mean jet latitude, 850 hPa, 60°W–0° (ERA5 46.7°N) | 48.3°N | 46.3°N | not available | – | – |

**What this means, in plain words**

1. **The mean winter circulation improves steadily with coupled resolution.** The typical pressure error falls from 3.2 hPa (LL) to 2.7 (MM) and 2.6 hPa (HH), and the model's own NAO pattern looks more like ERA5's at each step (0.92, 0.95, 0.98). Unlike ICON-ESM-ER, HadGEM3 has no large shift of its mean circulation along the NAO at any resolution (−0.1 to −0.5 SD). Mean-state differences of this kind are much less affected by chance than variability, so this is the clearest resolution effect in the project, with the caveat of one member per resolution.
2. **NAO strength shows no resolution effect.** It is 0.78, 0.92 and 0.76 of ERA5's for LL, MM and HH, and within each run it changes by up to 0.3 between the two halves of the record (MM: 1.16 then 0.82). That variation is as large as the differences between resolutions, and as large as the spread between identical runs in notebooks 07 and 10. A too-weak NAO in most periods is shared by all five coupled configurations examined in this project.
3. **The finest resolution makes UK and Ireland winters wetter.** HH has 25% more winter rain than ERA5 over UK and Ireland land, against +7% to +8% at LL and MM, mostly on west-facing coasts and high ground (Figure 3). This matches notebook 08: in IFS, 9 km gives heavier winter rain extremes than 28 km. Finer grids lift moist Atlantic air more sharply over steep terrain. Whether that is closer to the truth is not settled against ERA5 alone, whose own rain is a smoothed model product.
4. **The NAO's influence on winter rain is well reproduced at every resolution.** The response maps match ERA5's with pattern correlations of 0.94 to 0.96 (wetter north-west, drier south), and the regional correlations are close to ERA5's, slightly better at HH over north-west France (−0.21 against −0.28).
5. **The jet sits about 1.5° too far north at LL and close to ERA5 at MM.** The mean 850 hPa westerly peaks at 47.4°N in LL, 45.4°N in MM and 44.4°N in ERA5; the per-winter jet latitude averages 48.3°N (LL), 46.3°N (MM) and 46.7°N (ERA5). With a year-to-year spread of 5–6° over 64 winters, the LL offset of 1.6° is about 1.6 standard errors: suggestive, not conclusive, that the coarsest grid places the jet and storm track slightly too far poleward.

**Answer to the question.** In this coupled model, finer coupled resolution (atmosphere and ocean refined together) clearly improves the mean winter circulation and the shape of the NAO, probably moves the jet closer to its observed position, and increases winter rain over UK and Ireland (by 25% at 20 km). It does not change the NAO's strength beyond what chance does within a single run. Daily data, not publicly available, would be needed to test whether the extremes follow the mean state.
