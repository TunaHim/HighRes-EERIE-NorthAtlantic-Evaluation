# EERIE-UK-NAO-Extremes

Exploratory analysis for a University of Reading FUTURA application.

**Question.** Does an eddy-rich ocean change the winter North Atlantic
Oscillation (NAO) and extremes over the UK and Ireland (RX1day, TXx, R95p)?

**Rules.** Public EERIE output only. No AWI code and no non-public data.
Python with xarray, Dask, intake, zarr. Work proceeds one step at a time; each
step ends with an executed notebook.

**Status (9 October 2026).** Step 1 (environment, data inventory, loading code)
is finished. No analysis has been done and no analysis period has been chosen.
Nothing has been pushed to GitHub; that happens after the first prototype.

---

## 1. What has been done so far

### 1.1 Project and environment

- Created this folder, `C:\Users\LENOVO\EERIE-UK-NAO-Extremes`, with `git init`.
  Two local commits, no remote.
- Created the conda environment `eerie-uk-nao` from `environment.yml`
  (Python 3.11; xarray, dask, zarr, intake, intake-xarray, intake-esm, aiohttp,
  requests, fsspec, cftime, matplotlib, cartopy, jupyterlab, nbconvert, pytest).
- Later added `gribscan` with pip, on request. It brought `eccodes` 2.49 and
  `cfgrib`. It is recorded in `environment.yml`.
- The laptop has no git on PATH; the copy bundled with GitHub Desktop is used.

### 1.2 Checked which data sources answer

| Source | Result |
|---|---|
| `https://eerie.cloud.dkrz.de/intake.yaml` (the catalogue named in the brief) | `404 Not Found`. The server no longer publishes an intake file. |
| `https://eerie.cloud.dkrz.de/datasets` and `/datasets/<id>/stac` | Works. This is what the inventory is built from. |
| eerie-project `eerie.yaml` on GitHub | Works; lists `jasmin`, `jasmin_badc`, `dkrz`. |
| JASMIN and CEDA catalogue CSVs on GitHub | Work. |
| `https://gws-access.jasmin.ac.uk/public/eerie/` | `401 Unauthorized` (password required). |
| `https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/EERIE/MOHC/` | Works without login. |

### 1.3 Built the inventory

The DKRZ server lists 945 datasets. 234 of them are atmosphere collections of
EERIE coupled models. For each, the STAC metadata was read to get its variables
and period, and each model's own variable names were mapped onto the six fields
the project needs: daily `pr`, `psl`, `tas`, `tasmax` and monthly `psl`, `tas`.

Result on the regular 0.25° grid (`gr025`; `gr1` for HadGEM3):

| Model | Experiment, member, period | Daily pr / psl / tas / tasmax | Monthly psl / tas |
|---|---|---|---|
| ICON-ESM-ER | control, 1950–2050 | all | both |
| ICON-ESM-ER | hist-1950 r1, 1950–2014 | all | both |
| ICON-ESM-ER | hist-1950 r2, 1975–2014 | no tasmax | both |
| ICON-ESM-ER | hist-1950 r3, 1975–2014 | all | both |
| ICON-ESM-ER | SSP2-4.5 r1, 2015–2050 | all | both |
| IFS-FESOM2-SR | control, 1950–2050 | all | both |
| IFS-FESOM2-SR | hist-1950 r1, 1950–2014 | all | both |
| IFS-FESOM2-SR | hist-1950 r2 and r3, 1975–2014 | all | both |
| IFS-FESOM2-SR | SSP2-4.5 r1, 2015–2070 | all | both |
| IFS-FESOM2-SR | SSP2-4.5 r2 and r3, 2015–2030 | all | both |
| IFS-NEMO-ER | hist-1950 1950–2014; SSP2-4.5 2015–2050 | none | both |
| IFS-NEMO-ER | "control", 2015–2030 | pr and tas only | none |
| HadGEM3-GC5E-LL, -HH | historical 1850–2014; SSP2-4.5 2015–2099 | none | tas only, no psl |
| IFS-NEMO (non-ER) | not in the catalogue | – | – |

**Eleven runs have all six fields: four ICON-ESM-ER and seven IFS-FESOM2-SR.**

Native variable names used in the mapping:

| Field | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|
| daily pr | `pr` in `2d_daily_mean` (kg m⁻² s⁻¹) | `tprate` in `2D_daily_avg` (m s⁻¹) |
| daily psl | `psl` in `2d_daily_mean` | `mmsl` in `2D_daily_avg` |
| daily tas | `tas` in `2d_daily_mean` | `mean2t` in `2D_daily_avg` |
| daily tasmax | `tas` in `2d_daily_max` | `mx2t24` in `2D_daily_max` |
| monthly psl, tas | `psl`, `tas` in `2d_monthly_mean` | `mmsl`, `mean2t` in `2D_monthly_avg` |

### 1.4 Met Office HadGEM3-GC5 (JASMIN and CEDA)

- The public JASMIN catalogue lists daily `pr`, `psl`, `tas` (no `tasmax`) for
  the pre-industrial control at three resolutions: N96-ORCA1 1851–2080,
  N216-ORCA025 1851–1980, N640-ORCA12 1851–1900. The files themselves return
  `401 Unauthorized`, so they cannot be used without a JASMIN account.
- The CEDA archive serves HadGEM3-GC5E-LL, -MM and -HH historical runs
  (1850–2014) without login, but monthly only (`psl`, `tas`, `pr`), as netCDF
  on the native grid. Reading them would need `h5netcdf`, which is not installed.

### 1.5 Proved the data can be read

Listing is not access, so one global time step was actually loaded from each
kind of collection:

| Collection | Result |
|---|---|
| ICON-ESM-ER daily `psl`, daily max `tas` | read |
| IFS-FESOM2-SR daily `mmsl`, `tprate`, `mx2t24`, monthly `mean2t` | read (after the fix below) |
| IFS-NEMO-ER monthly `psl` | read |
| HadGEM3-GC5E-HH monthly `tas` | read |
| IFS-FESOM2-SR through the server-decoded `/zarr` endpoint | `500 Internal Server Error` on every data chunk; not used |

As an end-to-end sample, one winter of ICON-ESM-ER hist-1950 daily `psl`
(1 Dec 1979 – 29 Feb 1980) was loaded for the UK/Ireland box: 91 days × 49 × 55
grid points, about 1 MB, mean 1001.4 hPa. **This is the only real data
downloaded so far, and it was not saved to disk.**

### 1.6 The IFS-FESOM2-SR decoding problem and its fix

IFS-FESOM2-SR chunks are raw GRIB2 messages. Three things went wrong in turn:

1. Without `gribscan`: `UnknownCodecError: codec not available: 'gribscan.rawgrib'`.
2. With `gribscan` and current ecCodes (2.49):
   `ECCODES ERROR: Invalid size 52 found for section_2, assuming 57`, then
   `KeyValueNotFoundError`. The files carry an ECMWF local section written with
   an older layout than current ecCodes expects.
3. Pinning an older ecCodes with conda: the solver ran for 30 minutes without
   finishing and was stopped. The environment was not changed by that attempt.

The fix is in `src/eerie_uk/grib.py`: the local section (MARS bookkeeping only)
is removed from each message before decoding. Field values are not touched.
The decoded values look physical, but they have not been compared against an
independent reader.

---

## 2. What is in this folder

```
environment.yml              conda environment (name: eerie-uk-nao)
pyproject.toml               pytest settings
src/eerie_uk/
    catalogue.py             list datasets, read STAC metadata, build the inventory,
                             resolve a field to a dataset, open it lazily
    grib.py                  GRIB decoder for the IFS chunks (section 1.6)
    jasmin.py                JASMIN / CEDA catalogue summaries and access probes
    regions.py               lon/lat box subsetting, DJF selection, area mean
    plotting.py              figure helpers (availability grid, map, time series)
notebooks/
    01_data_inventory.ipynb  step 1, executed, with tables and three figures
tests/                       19 pytest tests, none need the network
data/                        empty; for downloaded subsets later (git-ignored)
```

Main functions:

| Function | Purpose |
|---|---|
| `catalogue.list_datasets()` | all dataset ids on the DKRZ server |
| `catalogue.fetch_summaries(ids)` | variables and period for each id |
| `catalogue.build_inventory(summaries)` | the table in section 1.3 |
| `catalogue.open_variable(model, experiment, frequency, variable)` | lazy array of one field, renamed to its CMIP-style name |
| `catalogue.check_read(dataset_id, variable)` | load one time step and report success or the exact error |
| `regions.subset_box(ds, box)` | cut a box; handles 0–360 and −180–180 longitudes, either latitude order, and the IFS flat cell layout |
| `regions.select_winter(ds, year)` | one December–February season |
| `jasmin.summarise(df)`, `jasmin.probe_access(summary)` | HadGEM3 listings and whether files download |

Boxes currently defined: `uk_ireland` (11°W–2.5°E, 49–61°N) and
`north_atlantic` (90°W–40°E, 20–80°N).

---

## 3. How to look at it and run it

```
conda activate eerie-uk-nao
cd C:\Users\LENOVO\EERIE-UK-NAO-Extremes
jupyter lab                      # open notebooks/01_data_inventory.ipynb
pytest                           # 19 offline tests
conda run -n eerie-uk-nao jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_inventory.ipynb
```

Re-executing the notebook needs internet and takes about four minutes.

---

## 4. Known limitations

- **No eddy / no-eddy contrast yet.** Both fully usable models (ICON-ESM-ER and
  IFS-FESOM2-SR) have an eddy-rich ocean. Comparing them shows model
  differences, not the effect of eddies.
- The inventory is from metadata; only the collections in section 1.5 were
  actually read.
- The server stores each day as one whole-globe chunk (2–4 MB). A regional box
  still downloads global fields: about 1.7 s per day, so roughly 11 hours for
  one daily variable over 1950–2014 from one run.
- Precipitation units differ between the two models (section 1.3).
- The variable mapping is hand-written and should be re-checked when used.
- The catalogue is live; this is a snapshot of 9 October 2026.

---

## 5. Open decisions (under discussion, nothing implemented)

1. **Contrast experiment.** The DKRZ server also holds EERIE atmosphere-only
   runs (`ifs-amip-tco1279`, `ifs-amip-tco399`; experiments `hist`,
   `hist-c-0-a-lr20`, `hist-c-lr20-a-0`). From their names these appear to be
   paired runs with and without the ocean-eddy signal in the sea-surface
   temperature. Their variables and periods have not been checked.
2. **Period.** Proposed for the prototype: monthly `psl` 1950–2014 for the NAO;
   daily `pr` and `tasmax` 1985–2014 for the extremes; all months.
3. **Region.** Proposed: save the North-West European Shelf box
   (20°W–13°E, 40–65°N), show maps over it, and report UK/Ireland as a named
   sub-region.
4. **JASMIN account** for the HadGEM3-GC5 resolution ladder, and whether to add
   `h5netcdf` for the CEDA monthly files.

---

## 6. Data sources

- DKRZ km-scale cloud: https://eerie.cloud.dkrz.de
- eerie-project intake catalogues: https://github.com/eerie-project/intake_catalogues
- CEDA archive: https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/
- EERIE project: https://eerie-project.eu
