# EERIE-UK-NAO-Extremes

Exploratory analysis: does an eddy-rich ocean change the winter NAO and
UK/Ireland extremes (RX1day, TXx, R95p)? Public EERIE output only.

## Setup

```
conda env create -f environment.yml
conda activate eerie-uk-nao
pytest                      # offline tests
jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_inventory.ipynb
```

## Layout

- `src/eerie_uk/catalogue.py` – list, describe and lazily open DKRZ cloud datasets
- `src/eerie_uk/jasmin.py` – JASMIN/CEDA catalogue summaries and access probes
- `src/eerie_uk/regions.py` – North Atlantic / UK-Ireland box and DJF selection
- `src/eerie_uk/plotting.py` – figure helpers used by the notebooks
- `notebooks/01_data_inventory.ipynb` – step 1: what is available and readable
- `tests/` – pytest, no network needed

## Data sources

- DKRZ km-scale cloud: https://eerie.cloud.dkrz.de (STAC + Zarr)
- eerie-project intake catalogues: https://github.com/eerie-project/intake_catalogues
- CEDA archive (HadGEM3-GC5E monthly): https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/
