Three historical runs per model (r1, r2, r3). NAO over the 39 winters 1976–2014, extremes over the 29 winters 1986–2014. "Robust across the three runs" means all three agree in sign and roughly in size; three runs cannot exclude a different answer in a fourth.

| Result of version 1 (r1 only) | ICON-ESM-ER, three runs | IFS-FESOM2-SR, three runs | Verdict |
|---|---|---|---|
| NAO weaker than ERA5 | 0.55 to 0.63 of ERA5 | 0.68 to 0.81 of ERA5 | **robust** in both models |
| Mean circulation like a strong positive NAO | +1.9 to +2.1 SD | +0.1 to +0.5 SD | **robust**: a property of ICON-ESM-ER |
| Very-wet-day rain (R95p) over UK and Ireland vs E-OBS | +50% to +62% | +9% to +17% | **robust** |
| Wettest day of the year vs E-OBS | +42% to +48% | +4% to +8% | **robust** |
| Hottest day of the year vs E-OBS | −2.9 to −3.6 °C | −1.4 to −1.9 °C | **robust** |
| Too many wet days / too much rain per wet day (vs E-OBS) | +32% to +34% / +15% to +21% | +3% to +7% / +5% to +7% | **robust** |
| Share of the R95p bias consistent with the circulation offset (E-OBS / ERA5) | 74–82% / 38–41% | small offset | **robust** for ICON-ESM-ER |
| ICON-ESM-ER's leading pattern "mixed" | own pattern vs ERA5: 0.59, 0.90, 0.94 | 0.84 to 0.95 | **partly chance**: r1 is the outlier |
| NAO link to R95p, UK and Ireland (obs 0.35–0.51) | 0.06 to 0.49 | 0.21 to 0.60 | **sensitive to chance** in both models |
| NAO link to R95p, western Norway (obs 0.81) | 0.52 to 0.71 | 0.60 to 0.69 | **robust**: weaker than observed in all six runs |
| NAO link to R95p, north-west France (obs 0.28–0.34) | −0.46 to +0.18 | −0.02 to +0.25 | ICON-ESM-ER negative in 2 of 3 runs; IFS-FESOM2-SR near zero in 2 of 3 |

**What this means, in plain words**

1. **The large biases are model properties, not bad luck.** ICON-ESM-ER's shifted mean circulation (about +2 SD along the NAO), its 50–60% excess in very-wet-day rain over UK and Ireland, its too many and too heavy wet days and its 3 °C too-cool hottest day appear in all three runs with similar size. The same holds for IFS-FESOM2-SR's much smaller biases. Version 1's single-run diagnosis of the mean state and of extremes stands.
2. **A weak NAO is a property of both models.** All six runs have an NAO weaker than ERA5's over the same winters: ICON-ESM-ER 0.55–0.63, IFS-FESOM2-SR 0.68–0.81. The ranking between the models is also the same in every run.
3. **ICON-ESM-ER's "mixed" leading pattern was mostly r1's chance.** In r2 and r3 its own leading pattern resembles ERA5's well (pattern correlation 0.90 and 0.94, against 0.59 in r1 over these winters), although its first two patterns remain close in variance. Version 1's emphasis on the mixing should be softened; measuring every run along the common ERA5 pattern was the right safeguard.
4. **The NAO link over UK and Ireland cannot be pinned down with single runs.** Three runs of one model span 0.06 to 0.49 (ICON-ESM-ER) and 0.21 to 0.60 (IFS-FESOM2-SR): as wide as the difference between the two references. Version 1's statement that IFS-FESOM2-SR reproduces the UK link better than ICON-ESM-ER does not hold; both are consistent with the observations and with each other.
5. **Over western Norway both models are robustly too weak.** All six runs have a weaker NAO link (0.52–0.71) than both references (0.81). This is the clearest model–observation difference in the NAO-to-extremes link, and it was underplayed in version 1.
6. **The wrong-sign link over north-west France is partly a model property and partly chance.** ICON-ESM-ER is negative in two of three runs (−0.46, −0.32) and weakly positive in the third (+0.18); IFS-FESOM2-SR is near zero in two runs. Notebook 11 tests this against the control runs.
7. **The circulation share of ICON-ESM-ER's wet bias is stable** across runs (74–82% of the R95p bias against E-OBS, 38–41% against ERA5), so the decomposition in notebook 06 was not a single-run artefact.

**Answer to the question.** Version 1's results on the mean circulation, NAO strength, rainfall and temperature extremes and the wet-day statistics are properties of the models: all three runs agree. Its results on the NAO-to-extremes link are only partly robust: over UK and Ireland the link varies between runs as much as between models and references, over western Norway both models are robustly too weak, and ICON-ESM-ER's wrong sign over north-west France appears in two of three runs. ICON-ESM-ER's mixed leading NAO pattern was largely the chance of run r1.
