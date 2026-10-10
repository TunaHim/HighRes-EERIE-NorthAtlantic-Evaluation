Numbers are for 1985–2014 unless stated, each model against the ERA5 reanalysis reference. One member per model, so every difference mixes model bias with chance.

| | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|
| **Data** | 780 months, complete, no missing values | 780 months, complete, no missing values |
| **Winter pressure, North Atlantic** | Clear north–south dipole bias: too low across the subpolar and Arctic North Atlantic (down to −14 hPa over the Nordic and Barents Seas), too high in the subtropics (up to +8 hPa). RMSE 5.7 hPa, pattern correlation 0.94 | Close to ERA5: mean bias +1.4 hPa, RMSE 1.8 hPa, pattern correlation 0.99 |
| **Year-to-year spread of winter pressure** (box average) | 2.3 hPa, against 3.0 hPa in ERA5 (77%) | 2.6 hPa, against 3.0 hPa in ERA5 (87%) |
| **Winter temperature, NW Europe** | 0.8 °C too cold on average; pattern correlation 0.98 | 0.8 °C too cold on average; pattern correlation 0.99; coldest bias over Norway |
| **Summer temperature** | +0.2 °C | −0.6 °C |
| **Winter precipitation, NW Europe** | Too wet: +1.0 mm/day (+29%); UK and Ireland +1.3 mm/day (+39%); pattern correlation 0.84 | Slightly too wet: +0.4 mm/day (+11%); UK and Ireland +0.5 mm/day (+14%); pattern correlation 0.96 |
| **Year-to-year spread of winter temperature, 1950–2014, UK and Ireland** | 0.69 of ERA5's | 0.99 of ERA5's |
| **Year-to-year spread of winter precipitation, UK and Ireland** | 0.86 of ERA5's | 0.91 of ERA5's |

**What this means, in plain words**

1. **The data are sound.** All nine monthly fields are complete, and the check of the IFS-FESOM2-SR decoding fix passed: a month of decoded daily precipitation averages to the same field as the model's own monthly file (pattern correlation 1.00, no visible local difference).
2. **IFS-FESOM2-SR has a credible mean winter circulation.** Its pressure field is close to ERA5 in both pattern and level.
3. **ICON-ESM-ER has too strong a north–south pressure contrast in winter.** Pressure is too low in the subpolar north and too high in the subtropics. That means westerly winds across the North Atlantic that are too strong on average, and it is the most important caveat to carry into the NAO notebook, because this bias has the same shape as the NAO itself.
4. **ICON-ESM-ER's wet bias fits that picture.** Stronger westerlies bring more rain to west-facing coasts, and the excess is largest exactly there (western Norway, western Britain and Ireland). This is a physically consistent pair of biases, not two unrelated ones. ERA5 precipitation is itself a model product and tends to be smooth over mountains, so part of the difference there may not be model error.
5. **ICON-ESM-ER winters vary too little from year to year,** in pressure (77% of ERA5's spread over 30 winters) and in temperature (60–70% of ERA5's spread in all three regions over 65 winters). IFS-FESOM2-SR is close to ERA5 in two of the three regions. Whether this is a weaker NAO, a weaker link from the NAO to temperature, or chance in one member is a question for the next two notebooks.
6. **Both models are cold in winter by a similar amount.** This is consistent across the two models examined; with one member each it is not a robust result.

**Bottom line.** Both models are credible enough to go on to the NAO. IFS-FESOM2-SR is the closer of the two to ERA5 in the mean winter state. For ICON-ESM-ER, the mean-pressure dipole bias and the low winter variability must be kept in view when its NAO is interpreted.
