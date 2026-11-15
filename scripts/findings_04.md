64 winters, 1951–2014. One member per model, so every model number carries sampling uncertainty.

| | ERA5 | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|---|
| Variance explained by the leading pattern | 47% (±8) | 29% (±5) | 35% (±6) |
| Cleanly separated from the second pattern | yes | **no** (second pattern 21%) | yes |
| Pattern correlation with ERA5 | – | 0.75 | 0.87 |
| Northern centre | 71°N 11°W, −5.4 hPa | 67°N 32°W, −3.5 hPa | 63°N 20°W, −4.9 hPa |
| Southern centre | 44°N 16°W, +4.0 hPa | 51°N 2°E, +3.8 hPa | 41°N 12°E, +2.1 hPa |
| Correlation with the station-style index | 0.92 | 0.46 | 0.85 |
| NAO strength along the ERA5 pattern, relative to ERA5 | 1.00 | **0.59** | **0.71** |
| Winter-to-winter memory (lag-1 autocorrelation) | 0.22 | −0.15 | 0.04 |
| Trend, SD per decade (95% range) | +0.13 (0.00 to 0.27) | +0.07 (−0.07 to 0.20) | +0.03 (−0.11 to 0.17) |
| Mean pressure bias expressed as an NAO state | – | **+2.3 SD** | +0.5 SD |

**What this means, in plain words**

1. **The method works on ERA5.** The leading pattern is the textbook NAO, it explains nearly half of the winter variance, it agrees with the simple station-style index (correlation 0.92), and it picks out well-known winters: 1989 is the most positive and 2010 the most negative, with 1969 second most negative. 1963 and 1995 rank sixth from each end, strong but not in the top five in this definition.
2. **IFS-FESOM2-SR has a recognisable NAO.** The pattern is clearly the same mode as in ERA5 (pattern correlation 0.87, station-style correlation 0.85). Its northern centre is realistic. Its southern centre is about half as strong and sits over the Mediterranean, not the Atlantic.
3. **ICON-ESM-ER's leading pattern is not a clean NAO.** Its southern centre lies over the North Sea, not near the Azores; it barely correlates with the station-style index (0.46); and it is not statistically separated from its second pattern. The real NAO pattern is split between ICON-ESM-ER's first and second EOFs (overlaps 0.76 and 0.58). So in this member the NAO exists but is shared between two patterns.
4. **Both models have a weaker NAO than ERA5.** Measured along the same (ERA5) pattern, winter-to-winter NAO swings are 59% of ERA5's in ICON-ESM-ER and 71% in IFS-FESOM2-SR. The sampling uncertainty of such a ratio is about ±13%, so ICON-ESM-ER is roughly three standard errors below 1 and IFS-FESOM2-SR about two. The deficit is larger than the models' general shortfall in winter pressure variability (68% and 79% of ERA5's variance over the box), and it appears in both halves of the record. Weak NAO variability is consistent across the two models examined.
5. **ICON-ESM-ER lives in a permanently positive-NAO-like state.** Its average winter pressure differs from ERA5 by the equivalent of a +2.3 SD NAO winter. This puts a number on the dipole bias seen in notebook 03. IFS-FESOM2-SR is at +0.5 SD.
6. **No model shows the weak upward trend or the slight winter-to-winter memory seen in ERA5.** Both ERA5 values are at the edge of significance (trend p = 0.05; memory 0.22 against a ±0.24 noise range), so their absence in a single model member is not evidence of a model fault.

7. **The mixing in ICON-ESM-ER does not depend on the domain** (section 8). In all five boxes tested, ICON-ESM-ER's first two patterns are not statistically separated, and its first pattern's resemblance to ERA5's jumps between 0.29 and 0.93 from box to box: the sign of an arbitrary blend of two modes of similar strength. IFS-FESOM2-SR is separated only marginally in the standard box and not in the four others; ERA5 is clearly separated in every box. So both models share variance more evenly between their first two patterns than the real atmosphere does, ICON-ESM-ER most. The NAO strengths along ERA5's pattern are robust to the box: 0.56–0.61 for ICON-ESM-ER and 0.68–0.72 for IFS-FESOM2-SR.

**Consequence for the next notebooks.** Because ICON-ESM-ER's own leading EOF is a mixture, the NAO-to-extremes analysis should use the index measured along the **common ERA5 pattern** for all three sources, with each model's own-pattern index as a sensitivity check. Both are saved.

**Bottom line.** IFS-FESOM2-SR reproduces the NAO pattern credibly but too weakly. ICON-ESM-ER has NAO-like variability that is weaker still, split across two patterns, and superimposed on a mean state that already resembles a strong positive NAO. These are exploratory results from one member each.

**Version 2 update (notebooks 10 and 12).** With three runs per model, the weak NAO holds in every run (ICON-ESM-ER 0.55–0.63, IFS-FESOM2-SR 0.68–0.81 of ERA5 over 1976–2014), and ICON-ESM-ER's mean-state offset (+1.9 to +2.1 SD) too. ICON-ESM-ER's mixed leading pattern, however, was largely the chance of run r1: in r2 and r3 its own pattern resembles ERA5's closely (0.90 and 0.94). HadGEM3-GC5E at three resolutions has no comparable mean-state offset and a pattern that sharpens with resolution.
