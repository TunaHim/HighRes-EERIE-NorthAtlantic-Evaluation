43 winters, 1981–2023; ten members per experiment at 28 km. "Strength" is the standard deviation of the winter NAO index along the ERA5 pattern, in ERA5 units.

| | Observed SST (`hist`) | Filtered SST anomalies | Third variant |
|---|---|---|---|
| Mean winter pressure, change from `hist` | – | at most 0.5 hPa, typically 0.13 hPa; significant nowhere | at most 0.4 hPa, typically 0.14 hPa; significant nowhere |
| … expressed as a shift along the NAO | – | +0.03 SD (p = 0.75) | +0.02 SD (p = 0.78) |
| NAO pattern correlation with ERA5 | 0.99 | 0.99 | 0.99 |
| Variance explained by the NAO pattern | 41% | 42% | 42% |
| NAO strength, ensemble mean | 0.87 | 0.86 | 0.91 |
| NAO strength, range across the ten members | 0.70 to 1.00 | 0.78 to 0.94 | 0.84 to 0.97 |
| Difference in strength from `hist` | – | −0.01 (p = 0.73) | +0.04 (p = 0.24) |
| Correlation of the ensemble-mean NAO with ERA5 | 0.27 | 0.09 | 0.25 |

**What this means, in plain words**

1. **Filtering the small-scale SST makes no detectable difference to the winter NAO in these runs.** The mean winter pressure changes by a few tenths of a hectopascal at most, against NAO swings of 4–5 hPa, and the change is not significant anywhere in the North Atlantic box. The NAO pattern is the same (pattern correlation 1.00 between experiments). The NAO strength differs by −1% and +4%, well inside the spread between members of a single experiment.
2. **This is a null result with a stated resolution.** Ten members can detect a change in NAO strength of roughly 10%. A smaller effect, or an effect on something other than the seasonal-mean NAO (storm tracks, local rainfall near ocean fronts, daily extremes), cannot be ruled out with this data.
3. **Chance alone moves NAO strength a lot.** Ten runs of the *same* model with the *same* SST give NAO strengths from 0.70 to 1.00 over 43 winters. This matters for the earlier notebooks: the coupled IFS-FESOM2-SR value of 0.71 (one member) sits at the lower edge of that range, so its "weak NAO" may be partly chance. ICON-ESM-ER's 0.59 lies below the whole range.
4. **The atmosphere-only model has a realistic NAO pattern** (pattern correlation 0.99 with ERA5, far better than either single-member coupled run in notebook 04, helped by pooling 430 winters) and a strength of about 0.87 of ERA5's, with ERA5's own 1981–2014 value (1.02) just above the highest member.
5. **Only a small part of the winter NAO follows the observed sequence of winters.** The ensemble-mean NAO correlates with ERA5 at 0.27 for observed SST, below the 0.34 needed for significance with 34 winters. The value for filtered anomalies is lower (0.09), but with these sample sizes that difference cannot be distinguished from chance and I draw no conclusion from it.

**Answer to the question.** In this atmosphere-only model at 28 km, the seasonal-mean winter NAO is not measurably sensitive to small-scale SST variability. This says nothing about a coupled ocean–atmosphere effect, and the exact meaning of the filter remains unverified.
