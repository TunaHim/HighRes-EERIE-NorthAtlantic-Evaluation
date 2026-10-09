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
3. **Optional, if the data support it.** Can paired EERIE experiments isolate the
   influence of small-scale ocean features (eddies and fronts) on the NAO?

The original question, "does an eddy-rich ocean change the NAO and extremes",
was demoted to question 3 because both fully usable coupled models have an
eddy-rich ocean. Comparing them shows model differences, not the effect of eddies.

**Rules.** Public data only. No AWI code. Python with xarray, Dask, intake, zarr.
Work proceeds one step at a time; each step ends with an executed notebook.

**Status (9 October 2026).** Step 1 (inventory and loading code) and day 1
(download plan, downloader, samples) are finished. The full downloads are
running or about to run; see `data/download.log`. No analysis has been done yet.
The repository will be made public on GitHub after version 1.

---

## 1. Design choices and the reasons for them

### 1.1 Domains

Three nested boxes, so the chain *large-scale circulation → European response →
regional extremes* is visible.

| Domain | Limits | Used for | Why these limits |
|---|---|---|---|
| North Atlantic | 90°W–40°E, 20–80°N | monthly sea-level pressure (NAO) | The standard Euro-Atlantic sector for an EOF-based NAO. It contains both centres of action (Icelandic low, Azores high) with room around them, so the leading pattern is not cut off at an edge. |
| North-west Europe | 20°W–13°E, 40–65°N | temperature, precipitation, extremes | The usual limits of the North-West European Shelf. It spans the NAO rainfall see-saw: wetter Scotland and Norway, drier France and Iberia in a positive-NAO winter. UK and Ireland alone show only part of that. It also adds land points, which makes extreme statistics more robust. |
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
| IFS-FESOM2-SR, hist-1950, r1 | coupled model 2 | The other one. A second, independent model shows which results are robust. |
| ERA5 | observation-based reference | Without a reference, model results cannot be judged. ERA5 sits on the same server, covers the whole period and has every variable. |
| IFS-AMIP tco1279 and tco399, `hist` vs `hist-c-0-a-lr20` (and `hist-c-lr20-a-0`) | optional process experiment | The same atmosphere model forced with observed sea-surface temperature and with filtered ("LR20") anomalies. This is the only public controlled test of small-scale ocean influence. The tco399 runs have 10 members each. Monthly pressure only. |
| E-OBS v33.0e | land observations (not downloaded yet) | Station-based, so a more direct reference for precipitation extremes than ERA5. Waiting for a decision on its non-commercial terms of use. |

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

All months are downloaded, not winter only. Reason: TXx is set in summer, and
winter can still be selected afterwards for the NAO link. The NAO-to-extremes
analysis itself will use winter quantities.

Fallback if the server proves too slow: shorten the daily period to 1995–2014.

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

## 2. Roadmap

| Stage | Content | Notebook | State |
|---|---|---|---|
| 1 | Data discovery and access | `01_data_inventory` | done |
| 1b | Domains, download plan, samples | `02_download_plan` | done |
| 2 | Validation and historical baseline against ERA5 | `03_validation_baseline` | next |
| 3 | NAO: EOF pattern, index, variability | `04_nao` | |
| 4 | Extremes: RX1day, TXx, R95p | `05_extremes` | |
| 5 | NAO-to-extremes link | `06_nao_extremes` | |
| 6 | Paired experiment (monthly NAO) | `07_paired_experiment` | optional |
| 7 | Streamlit dashboard, public GitHub repository | | |

Not in version 1, but designed for: future scenario (SSP2-4.5), CMIP6, CMIP7.

---

## 3. What has been done so far

### 3.1 Step 1: inventory and access

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

### 3.2 Day 1: download plan

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

## 4. What is in this folder

```
environment.yml              conda environment (name: eerie-uk-nao)
pyproject.toml               pytest settings
src/eerie_uk/
    catalogue.py             list datasets, read metadata, build the inventory, open lazily
    grib.py                  GRIB decoder for the IFS and ERA5 chunks
    jasmin.py                JASMIN / CEDA catalogue summaries and access probes
    regions.py               boxes, box subsetting, DJF selection, area mean, ERA5 regridding
    download.py              the download plan and the resumable year-by-year downloader
    plotting.py              figure helpers
notebooks/
    01_data_inventory.ipynb  what exists and what can be read
    02_download_plan.ipynb   domains, plan, measured cost, sample maps
    html/                    HTML copies for easy reading (git-ignored)
tests/                       32 pytest tests, none need the network
data/                        downloaded cut-outs and download.log (git-ignored)
```

Saved files are named `data/<source>/<mon|day>/<variable>_<box>_<year>.nc`.

---

## 5. How to look at it and run it

```
conda activate eerie-uk-nao
cd C:\Users\LENOVO\EERIE-UK-NAO-Extremes
jupyter lab                                   # open the notebooks
pytest                                        # 32 offline tests
python -m eerie_uk.download --group monthly   # run from src/, or with PYTHONPATH=src
python -m eerie_uk.download --group daily
```

The downloader skips years that already have a file, so it can be stopped and
restarted at any time. Progress is written to `data/download.log`.

---

## 6. Known limitations

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

## 7. Data sources

- DKRZ km-scale cloud: https://eerie.cloud.dkrz.de
- eerie-project intake catalogues: https://github.com/eerie-project/intake_catalogues
- CEDA archive: https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/
- E-OBS: https://surfobs.climate.copernicus.eu/dataaccess/access_eobs.php
- EERIE project: https://eerie-project.eu
