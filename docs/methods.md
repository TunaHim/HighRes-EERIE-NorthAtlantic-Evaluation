# Methods

Adopted on 9 October 2026, before any result was produced. Everything in this
project is exploratory.

## 1. Wording

- **ERA5** is a reanalysis reference, not observations.
- **E-OBS** is a station-based gridded dataset.
- Two models with one member each: a shared result is "consistent across the two
  models examined", never "robust".
- The paired atmosphere-only runs test "atmospheric sensitivity to small-scale
  SST variability (LR20-filtered SST forcing)". They are not described as the
  effect of ocean eddies and fronts unless the LR20 filter is verified, and even
  then they test SST forcing, not a coupled feedback.

## 2. Preprocessing

| Item | Choice |
|---|---|
| Units | precipitation mm/day, temperature °C, pressure hPa |
| Calendars | checked per source and aligned by date |
| Grid | common 0.25° model grid; ERA5 and E-OBS are regridded to it |
| Regridding | temperature and pressure bilinear. Precipitation should be conservative; the prototype uses bilinear because conservative regridding needs an extra package. This slightly smooths precipitation maxima and is stated wherever it matters. |
| Winter | December belongs to the following year's winter: DJF 1986 = December 1985 + January and February 1986. Incomplete first and last winters are dropped. |

Files on disk hold temperature in K; it is converted to °C when loaded.

## 3. NAO (notebook 04)

1. Monthly sea-level pressure minus the 1950–2014 mean of each calendar month
   gives anomalies.
2. Select December–February and average per winter (65 winters). The monthly
   winter series is kept as well.
3. Domain 20–80°N, 90°W–40°E. Multiply by √cos(latitude) before the EOF.
4. Leading EOF per dataset; report explained variance and pattern correlation
   with the ERA5 leading EOF.
5. Sign: a positive NAO has negative loading near Iceland (about 65°N, 20°W) and
   positive loading near the Azores (about 38°N, 25°W). Flip the EOF and its
   principal component if needed.
6. Index: leading principal component divided by its 1950–2014 standard
   deviation.
7. Also project each model's anomalies onto the ERA5 leading EOF, to compare on
   a common basis.
8. Cross-check against a station-style index, Azores minus Iceland pressure;
   report the correlation with the EOF index.
9. Diagnostics: year-to-year standard deviation, lag-1 winter autocorrelation,
   linear trend with confidence interval. Spectrum optional.

## 4. Extremes (notebook 05)

Per grid cell on the 0.25° grid, base period 1985–2014.

| Index | Definition | Computed for |
|---|---|---|
| RX1day | largest daily precipitation | year and DJF |
| TXx | highest daily maximum temperature | year (usually summer) and DJF |
| R95p (ETCCDI R95pTOT) | A wet day has at least 1 mm. The threshold is the 95th percentile of wet-day precipitation at the cell over 1985–2014. R95p is the total precipitation on days above the threshold (the whole daily total, not the excess). Also reported as a percentage of total wet-day precipitation. | year and DJF |

The threshold is estimated from the same years it is applied to, which biases
exceedance counts slightly inside the base period (Zhang et al. 2005). This is
stated once and not corrected.

Model against reference: climatology and difference maps, and land-only regional
means. UK and Ireland is mandatory; western Norway and north-west France are
supporting.

## 5. NAO to extremes (notebook 06)

- The winter NAO is related only to winter indices: DJF RX1day, DJF R95p,
  DJF TXx. Annual TXx stays in notebook 05.
- Primary method: grid-point correlation, and regression per one standard
  deviation of NAO, over 1985–2014 (30 winters), with both series linearly
  detrended.
- Significance: two-sided t-test at 5%, with false-discovery-rate control across
  grid points (Wilks 2016).
- Supporting method: composites of positive-NAO minus negative-NAO winters
  (upper and lower thirds, about ten winters each) with bootstrap confidence
  intervals.
- Key question: does each model reproduce the sign, pattern and strength of the
  link in ERA5 and E-OBS (pattern correlation, regional regression)?
- The sample size is stated once.

## 6. Paired experiment (notebook 07, optional, NAO only)

The same NAO method over 1980–2023, per member. Differences are judged against
the spread across members (10 members at 28 km). At most half a day is spent
verifying LR20.

## 7. Checks before claims

The IFS-FESOM2-SR GRIB decoding fix is checked in notebook 03:

1. decode the same message with a plain reader where possible and compare;
2. compare the monthly mean of decoded daily data with the model's monthly file;
3. check minimum, maximum, mean and the spatial pattern.

## 8. Priorities

Notebooks 03 → 04 → 05 → 06 first. Notebook 07 and the interactive explorer are
optional and are never built at the expense of clean notebooks and the README.

## 9. Additions after the first results (notebook 06, sections 10 and 11)

Added on 5 November 2026, after the results above were produced, to test how far they hold.
They do not change any earlier choice.

| Check | Method |
|---|---|
| Uncertainty of a regional correlation | Bootstrap: 5000 resamples of the 29 winters with replacement, NAO and extreme value kept together; the 2.5th and 97.5th percentiles give the 95% interval. Series detrended first. |
| Influence of single winters | Correlation recomputed 29 times, each time without one winter; the range and the most influential winter are reported. |
| Memory between winters | Effective sample size n(1 − a·b)/(1 + a·b), with a and b the lag-1 autocorrelations of the two series (Bretherton et al. 1999), never above n; p value recomputed with it. |
| Model against reference | Fisher z test for two correlations from independent samples (29 winters each). Not applied between E-OBS and ERA5, which describe the same winters. |
| Circulation part of a mean bias | Observed regression of the index on the NAO (per +1 SD of the ERA5 NAO, from E-OBS or ERA5) × the model's mean winter sea-level-pressure bias projected onto the ERA5 NAO pattern (in ERA5 SD, 1986–2014). Compared with the actual mean bias over UK and Ireland land and as a land pattern correlation. Repeated with the model's own regression as a sensitivity test. Linear; a consistency diagnostic, not an attribution. |
| Wet-day frequency and intensity | Winter wet days (at least 1 mm; ETCCDI R1mm) and rain per wet day (ETCCDI SDII), UK and Ireland land, 1986–2014. |

## References

- Bretherton, C. S., et al. (1999). The effective number of spatial degrees of freedom of a
  time-varying field. *J. Climate*, 12, 1990–2009.
- Cornes, R. C., et al. (2018). An ensemble version of the E-OBS temperature and
  precipitation data sets. *J. Geophys. Res. Atmos.*, 123. doi:10.1029/2017JD028200
- North, G. R., et al. (1982). Sampling errors in the estimation of empirical orthogonal
  functions. *Mon. Wea. Rev.*, 110, 699–706.
- Wilks, D. S. (2016). "The stippling shows statistically significant grid
  points". *Bull. Amer. Meteor. Soc.*, 97, 2263–2273.
- Zhang, X., et al. (2005). Avoiding inhomogeneity in percentile-based indices of
  temperature extremes. *J. Climate*, 18, 1641–1651.
