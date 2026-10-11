# EERIE-UK-NAO-Extremes

**North Atlantic climate variability and regional extremes in high-resolution
Earth-system model simulations.**

Exploratory analysis for a University of Reading FUTURA application.

## Questions

1. **Main.** How do high-resolution coupled Earth-system models represent North
   Atlantic climate variability (the NAO) and extremes over the UK and Ireland,
   and how are the two linked?
2. **Secondary.** Where does that representation differ between model
   configurations?
3. **Optional, if the data support it.** How sensitive is the simulated NAO to
   small-scale sea-surface temperature (SST) variability, as tested by paired
   atmosphere-only EERIE experiments with and without filtered SST?

The original question, "does an eddy-rich ocean change the NAO and extremes",
was demoted to question 3 because both fully usable coupled models have an
eddy-rich ocean. Comparing them shows model differences, not the effect of eddies.
Question 3 is worded as SST sensitivity on purpose: an atmosphere-only run forced
with filtered SST tests the atmosphere's response to a change in SST forcing. It
does not demonstrate a coupled feedback from ocean eddies.

This is an exploratory prototype. With two models and one member each, a shared
result is described as "consistent across the two models examined", never as
robust.

**Rules.** Public data only. No AWI code. Python with xarray, Dask, intake, zarr.
Work proceeds one step at a time; each step ends with an executed notebook.

**Status (11 October 2026).** Notebooks 01 to 06 are executed: inventory,
download plan, validation and baseline, NAO, extremes, and the NAO-to-extremes
link. All data are downloaded except ERA5 *daily* (8 of 30 years of
precipitation, no maximum temperature yet), so notebooks 05 and 06 currently use
E-OBS as the only reference for extremes; they add ERA5 automatically when it is
complete. The repository will be made public on GitHub after version 1.

## Main results so far (exploratory; one member per model)

| Topic | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|
| Mean winter pressure (notebook 03) | north–south dipole bias, down to −14 hPa in the north | close to ERA5 (RMSE 1.8 hPa) |
| NAO pattern (04) | leading EOF is a mixture, not a clean NAO | recognisable NAO, southern centre weak and displaced |
| NAO strength relative to ERA5 (04) | 0.59 | 0.71 |
| Mean state as an NAO anomaly (04) | +2.3 SD | +0.5 SD |
| Wettest day of the year, UK and Ireland, vs E-OBS (05) | +48% | +8% |
| Hottest day of the year, UK and Ireland, vs E-OBS (05) | −3.3 °C | −1.9 °C |
| NAO link to very-wet-day winter rain, UK and Ireland: correlation; E-OBS 0.51 (06) | 0.36 (not significant) | 0.60 |

Each notebook has a "Findings" section in plain words and a "Limitations"
section. HTML copies are in `notebooks/html/`.

---

## 1. Design choices and the reasons for them

### 1.1 Domains

Three nested boxes, so the chain *large-scale circulation → European response →
regional extremes* is visible.

| Domain | Limits | Used for | Why these limits |
|---|---|---|---|
| North Atlantic | 90°W–40°E, 20–80°N | monthly sea-level pressure (NAO) | The standard Euro-Atlantic sector for an EOF-based NAO. It contains both centres of action (Icelandic low, Azores high) with room around them, so the leading pattern is not cut off at an edge. |
| North-west Europe | 20°W–13°E, 40–65°N | temperature, precipitation, extremes | The usual limits of the North-West European Shelf. It spans the NAO rainfall see-saw: wetter Scotland and Norway, drier France and Iberia in a positive-NAO winter. UK and Ireland alone show only part of that. It also adds land points, which gives the extreme statistics a larger sample. |
| UK and Ireland | 11°W–2.5°E, 49–61°N | headline numbers | The region the application is about. It is cut out of the north-west Europe files, so it needs no separate download. |

Sub-regions for headline numbers inside north-west Europe: **UK and Ireland**,
**western Norway** (4.5–8.5°E, 58–63°N) and **north-west France**
(5°W–3°E, 46–50.5°N). Reason: an average over the whole box would cancel the
north–south NAO signal, so a wet northern and a drier southern region are
reported next to the headline region. These two are proposals and can be moved
without downloading anything again.

Why a larger box costs nothing: the server sends whole-globe chunks whatever
region is asked for, so the box only changes the size of the saved file.

Pressure on the North Atlantic box is saved at 1° instead of 0.25°. Reason: the
NAO is a basin-scale pattern, and 1° files are 16 times smaller.

### 1.2 Data

| Source | Role | Why it was chosen |
|---|---|---|
| ICON-ESM-ER, hist-1950, r1 | coupled model 1 | One of only two models on the DKRZ cloud with all six needed fields (daily pr, psl, tas, tasmax; monthly psl, tas) on the common 0.25° grid. |
| IFS-FESOM2-SR, hist-1950, r1 | coupled model 2 | The other one. A second, independent model allows a check of whether the main features are consistent across model configurations. Two models with one member each cannot establish robustness. |
| ERA5 | reanalysis reference | Without a reference, model results cannot be judged. ERA5 sits on the same server, covers the whole period and has every variable. It is a reanalysis, not observations: pressure and temperature are well constrained by observations, precipitation is a model product. |
| IFS-AMIP tco1279 and tco399, `hist` vs `hist-c-0-a-lr20` (and `hist-c-lr20-a-0`) | optional sensitivity experiment | The same atmosphere model forced with observed SST and with filtered ("LR20") SST anomalies. It tests atmospheric sensitivity to small-scale SST variability. It is the only public controlled experiment of this kind. The tco399 runs have 10 members each. Monthly pressure only. Until the LR20 filter is verified, results are not described as an effect of ocean eddies and fronts. |
| E-OBS v33.0e | station-based gridded land dataset (supporting) | A more direct reference for precipitation extremes over land than ERA5. Used where it is easy; ERA5 is the main reference for the prototype. Non-commercial research use only. |

Why other candidates were left out:

- **IFS-NEMO-ER:** monthly fields only for the historical run; no daily pressure
  or maximum temperature.
- **HadGEM3-GC5 at three ocean resolutions (N96-ORCA1, N216-ORCA025,
  N640-ORCA12):** the ideal resolution ladder, listed in the public JASMIN
  catalogue, but the files return `401 Unauthorized` without a JASMIN login.
- **HadGEM3-GC5E on DKRZ and CEDA:** monthly only, and no pressure on DKRZ.
- **Members r2 and r3:** start in 1975 and ICON r2 lacks daily maximum
  temperature. They can be added later for the NAO at small cost.
- **CMIP6:** deliberately not in the first prototype. The code maps every source
  to CMIP-style names so a CMIP6 or CMIP7 backend can be added later.

Why these variables: sea-level pressure defines the NAO; daily precipitation
gives RX1day and R95p; daily maximum temperature gives TXx; monthly temperature
and precipitation give the baseline climate. Daily pressure and daily mean
temperature are not needed for these indices, so they are not downloaded.

### 1.3 Periods

| Data | Period | Reason |
|---|---|---|
| Monthly, coupled models and ERA5 | 1950–2014 | The full historical run. Monthly data are cheap (about 4 hours in total), and 65 winters give a far more stable NAO than 30. |
| Daily, coupled models and ERA5 | 1985–2014 | A standard 30-year climate period, and the last 30 years of the historical run, where the observations are best. Daily data are the expensive part (about 14 hours), so the period is kept to what the indices need. |
| Paired experiments | 1980–2023 | The years they exist. |

All months are downloaded, not winter only. Reason: the general extremes
diagnostics are annual (annual TXx is normally set in summer), while the
NAO-to-extremes analysis uses winter versions of the indices (section 2).

The daily period is shortened to 1995–2014 only if the download genuinely fails.

### 1.4 Storage

- Gridded cut-outs: compressed netCDF, one file per year, under `data/`
  (git-ignored). One file per year means a failed download costs one year and a
  rerun continues where it stopped.
- Derived tables (NAO index, regional index series, summaries): Parquet,
  committed later for the dashboard.
- Estimated total: about 3 GB.

### 1.5 Common units

| Quantity | On the server | Saved as | Conversion |
|---|---|---|---|
| Precipitation, ICON-ESM-ER | kg m⁻² s⁻¹ | mm/day | × 86 400 |
| Precipitation, IFS | m s⁻¹ | mm/day | × 86 400 × 1000 |
| Precipitation, ERA5 | m per day | mm/day | × 1000 |
| Pressure | Pa | hPa | ÷ 100 |
| Temperature | K | K | none |

---

## 2. Methods

These definitions are fixed before any result is produced. This section is a
summary; the full specification, including the significance tests and the
cross-checks, is in [`docs/methods.md`](docs/methods.md).

Analysis units: precipitation mm/day, temperature °C (files hold K and are
converted on loading), pressure hPa. ERA5 and E-OBS are regridded to the 0.25°
model grid, bilinearly; conservative regridding of precipitation would be
better and is not used in the prototype.

### 2.1 Seasons

Winter is December–February. December belongs to the following year's winter:
DJF 1986 is December 1985 plus January and February 1986. Incomplete first and
last winters are dropped.

### 2.2 NAO (notebook 04)

| Step | Choice | Reason |
|---|---|---|
| Anomalies | Monthly sea-level pressure minus the 1950–2014 mean of each calendar month, then DJF months selected | Keeps a monthly NAO series as well as one value per winter. |
| Domain | 20–80°N, 90°W–40°E | The standard Euro-Atlantic sector. |
| Weighting | Each grid point multiplied by √cos(latitude) before the EOF | Otherwise the many small high-latitude cells are over-represented. |
| Pattern | Leading EOF of winter anomalies, computed separately for each dataset; explained variance reported | |
| Sign | Fixed so a positive NAO has low pressure near Iceland and high pressure near the Azores | The sign of an EOF is arbitrary. A flipped sign between two datasets means nothing and must be removed before comparing. |
| Index | Leading principal component, divided by its standard deviation | |
| Comparison | Pattern correlation of each model's EOF with the ERA5 EOF; year-to-year spread; winter-to-winter persistence | Model and ERA5 indices are not compared year by year: a free-running model has its own sequence of winters. |
| Common basis | Each model's winter anomalies are also projected onto the ERA5 leading EOF; pattern correlation and amplitude reported | Separates "is the pattern different" from "is the variability different". |
| Cross-check | Station-style index: normalised pressure difference, Azores minus Iceland, at the nearest grid points; its correlation with the EOF index is reported | An EOF can mix patterns; the station index is a simple independent definition. |

### 2.3 Extreme indices (notebook 05)

All per grid cell, base period 1985–2014.

| Index | Definition |
|---|---|
| RX1day | Largest daily precipitation total in the period (year or winter). |
| TXx | Highest daily maximum temperature in the period (year or winter). |
| R95p | ETCCDI R95pTOT. A wet day has at least 1 mm of precipitation. The threshold is the 95th percentile of wet-day precipitation at that grid cell over 1985–2014. R95p is the total precipitation that fell on days above the threshold, per year or per winter. |

Two sets are computed and kept apart:

| Purpose | Indices | Period |
|---|---|---|
| General extremes diagnostics | RX1day, TXx, R95p | annual |
| NAO relationship | winter RX1day, winter R95p, winter TXx (highest daily maximum within DJF) | DJF |

Annual TXx is normally set in summer, so it is not related to the winter NAO.

### 2.4 NAO-to-extremes link (notebook 06)

The winter NAO index is related only to the winter indices, over the 30 winters
that have daily data. Maps of correlation and of regression per standard
deviation of NAO are the main result. Both series are linearly detrended first.
Significance is a two-sided t-test at 5% with false-discovery-rate control across
grid points (Wilks 2016; the control level is stated in the notebook). Composites
of positive-NAO minus negative-NAO winters (upper and lower thirds) with bootstrap
confidence intervals are supporting evidence. The
question is whether each model reproduces the sign, pattern and strength of the
link seen in the reference data.

UK and Ireland is the mandatory region. Western Norway and north-west France are
supporting statistics, not a separate analysis.

### 2.5 Paired experiment (notebook 07, optional)

The same NAO method over 1980–2023. Differences between the runs are judged
against the spread across the ten members, never from single runs. Results are described as sensitivity
to small-scale SST variability.

### 2.6 Check of the GRIB decoding fix

Before IFS-FESOM2-SR results are interpreted, the fix in `grib.py` is checked in
notebook 03: the same message decoded with an older ecCodes that needs no fix
gives identical values, and the average of decoded daily fields over a month
reproduces the model's own monthly file.

---

## 3. Roadmap

| Stage | Content | Notebook | State |
|---|---|---|---|
| 1 | Data discovery and access | `01_data_inventory` | done |
| 1b | Domains, download plan, samples | `02_download_plan` | done |
| 2 | Validation and historical baseline against ERA5 | `03_validation_baseline` | done |
| 3 | NAO: EOF pattern, index, variability | `04_nao` | done |
| 4 | Extremes: RX1day, TXx, R95p | `05_extremes` | done (E-OBS reference; ERA5 daily pending) |
| 5 | NAO-to-extremes link | `06_nao_extremes` | done (E-OBS reference; ERA5 daily pending) |
| 6 | Paired experiment (monthly NAO) | `07_paired_experiment` | optional |
| 7 | Public GitHub repository; Streamlit dashboard if time allows | | |

The notebooks and this README come first. The dashboard is a demonstration and is
not built at their expense.

Not in version 1, but designed for: future scenario (SSP2-4.5), CMIP6, CMIP7.

---

## 4. What has been done so far

### 4.1 Step 1: inventory and access

- Environment `eerie-uk-nao` from `environment.yml` (Python 3.11; xarray, dask,
  zarr, intake, cartopy, jupyterlab, pytest; `gribscan` added with pip, which
  brings `eccodes`).
- `https://eerie.cloud.dkrz.de/intake.yaml` returns `404 Not Found`; the server
  now publishes STAC, so the inventory is built from `/datasets` and each
  dataset's `/stac` item.
- 945 datasets on the server, 234 atmosphere collections of coupled models.
  **Eleven runs have all six fields: four ICON-ESM-ER and seven IFS-FESOM2-SR.**

| Model | Experiment, member, period | Daily pr / psl / tas / tasmax | Monthly psl / tas |
|---|---|---|---|
| ICON-ESM-ER | control 1950–2050; hist-1950 r1 1950–2014, r3 1975–2014; SSP2-4.5 2015–2050 | all | both |
| ICON-ESM-ER | hist-1950 r2, 1975–2014 | no tasmax | both |
| IFS-FESOM2-SR | control 1950–2050; hist-1950 r1 1950–2014, r2–r3 1975–2014; SSP2-4.5 r1 2015–2070, r2–r3 2015–2030 | all | both |
| IFS-NEMO-ER | hist-1950 1950–2014; SSP2-4.5 2015–2050 | none | both |
| HadGEM3-GC5E-LL, -HH | historical 1850–2014; SSP2-4.5 2015–2099 | none | tas only |

- IFS chunks are raw GRIB whose ECMWF local section current ecCodes cannot parse
  (`Invalid size 52 found for section_2`). `src/eerie_uk/grib.py` drops that
  bookkeeping section before decoding; field values are untouched. A lock stops
  ecCodes crashing when several threads decode at once.

### 4.2 Day 1: download plan

- Confirmed from the public EERIE catalogue what the paired experiments are
  (section 1.2). Not yet verified: the exact definition of the LR20 filter, and
  what `hist-c-lr20-a-0` changes.
- Confirmed ERA5 on the DKRZ server has monthly pressure and temperature and
  daily precipitation and maximum temperature. ERA5 is on a reduced Gaussian
  grid and is interpolated linearly to the 0.25° model grid.
- Wrote the resumable downloader (`src/eerie_uk/download.py`).
- Ran a short real sample of all 20 downloads in the plan: all succeeded, values
  sensible, units consistent.
- Measured cost of the full plan: about 19 hours and about 3 GB.

---

## 5. What is in this folder

```
environment.yml              conda environment (name: eerie-uk-nao)
pyproject.toml               pytest settings
src/eerie_uk/
    catalogue.py             list datasets, read metadata, build the inventory, open lazily
    grib.py                  GRIB decoder for the IFS and ERA5 chunks
    jasmin.py                JASMIN / CEDA catalogue summaries and access probes
    regions.py               boxes, box subsetting, DJF selection, area mean, ERA5 regridding
    download.py              the download plan and the resumable year-by-year downloader
    eobs.py                  E-OBS download and cut-out
    store.py                 read the saved files back with common time stamps and units
    climatology.py           seasonal means, climatologies, comparison statistics
    nao.py                   winter NAO: anomalies, EOF, sign convention, indices, diagnostics
    extremes.py              RX1day, TXx, R95p per year and per winter
    relationships.py         detrended correlation and regression maps, FDR control, composites
    plotting.py              figure helpers
notebooks/
    01_data_inventory.ipynb  what exists and what can be read
    02_download_plan.ipynb   domains, plan, measured cost, sample maps
    03_validation_baseline.ipynb  data checks, GRIB check, mean climate and variability against ERA5
    04_nao.ipynb             winter NAO: pattern, index, strength, cross-checks
    05_extremes.ipynb        RX1day, TXx, R95p (annual and winter) against E-OBS
    06_nao_extremes.ipynb    link between the winter NAO and winter extremes
    html/                    HTML copies for easy reading (git-ignored)
docs/methods.md              the full methods specification
scripts/                     notebook generators (build_notebook_NN.py) and findings text
app_assets/                  small derived tables (Parquet) for later notebooks and the dashboard
tests/                       59 pytest tests, none need the network
data/                        downloaded cut-outs and download.log (git-ignored)
```

Saved files are named `data/<source>/<mon|day>/<variable>_<box>_<year>.nc`.

---

## 6. How to look at it and run it

```
conda activate eerie-uk-nao
cd C:\Users\LENOVO\EERIE-UK-NAO-Extremes
jupyter lab                                   # open the notebooks
pytest                                        # 59 offline tests
python -m eerie_uk.download --group monthly   # run from src/, or with PYTHONPATH=src
python -m eerie_uk.download --group daily
```

The downloader skips years that already have a file, so it can be stopped and
restarted at any time. Progress is written to `data/download.log`.

---

## 7. Known limitations

- No same-model eddy-rich versus coarse-ocean coupled pair is publicly
  downloadable at daily frequency. The paired atmosphere-only runs are the
  substitute, for monthly pressure only.
- One member per coupled model and 30 years of daily data: about ten strongly
  positive and ten strongly negative NAO winters. Results on the NAO-to-extremes
  link will be shown as regression and correlation maps with significance, not
  as firm claims.
- ERA5 precipitation is a model product, and ERA5 is interpolated to the model
  grid, which slightly smooths sharp maxima.
- Time stamps differ between sources (end of month, mid-month, first of month).
- The GRIB decoding fix has not been compared against an independent reader.
- Download times are estimates from short samples; the server speed varies.
- The catalogue is live; this is a snapshot of 9 October 2026.

---

## 8. Data sources

- DKRZ km-scale cloud: https://eerie.cloud.dkrz.de
- eerie-project intake catalogues: https://github.com/eerie-project/intake_catalogues
- CEDA archive: https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/
- E-OBS: https://surfobs.climate.copernicus.eu/dataaccess/access_eobs.php
- EERIE project: https://eerie-project.eu
