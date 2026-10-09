"""E-OBS station-based daily observations over European land.

E-OBS comes as one netCDF file per variable for the whole of Europe and the
whole record. The file is downloaded once, cut to the project box and period,
saved one file per year like every other source, and then deleted.

Terms of use: non-commercial research and education only (ECA&D data policy).
Cite Cornes et al. (2018), doi:10.1029/2017JD028200.

    python -m eerie_uk.eobs
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
import xarray as xr

from . import download, regions

log = logging.getLogger("eerie_uk.eobs")

VERSION = "v33.0e"
_BASE = "https://knmi-ecad-assets-prd.s3.amazonaws.com/ensembles/data/Grid_0.25deg_reg_ensemble"
# E-OBS name -> (our name, file)
FILES = {
    "rr": ("pr", f"{_BASE}/rr_ens_mean_0.25deg_reg_{VERSION}.nc"),
    "tx": ("tasmax", f"{_BASE}/tx_ens_mean_0.25deg_reg_{VERSION}.nc"),
}
SOURCE = "e-obs"
BOX = "nw_europe"


def to_common(da: xr.DataArray, variable: str) -> xr.DataArray:
    """E-OBS field in project conventions: lat/lon names, mm/day or K."""
    da = da.rename({"latitude": "lat", "longitude": "lon"})
    attrs = {"source": SOURCE, "version": VERSION}
    if variable == "pr":
        out = da  # already mm per day
        attrs.update(units="mm/day", original_units="mm")
    else:
        out = da + 273.15
        attrs.update(units="K", original_units="Celsius")
    out = out.rename(variable)
    out.attrs = attrs
    return out


def cut_years(path, eobs_name: str, root, years=range(*download.DAILY_YEARS[:1], download.DAILY_YEARS[1] + 1)) -> list[int]:
    """Cut a downloaded E-OBS file to the box, one saved file per year."""
    variable = FILES[eobs_name][0]
    request = download.Request(SOURCE, Path(path).name, eobs_name, variable, "day", BOX, min(years), max(years))
    done = []
    with xr.open_dataset(path) as ds:
        field = to_common(ds[eobs_name], variable)
        for year in download.pending_years(root, request):
            one = regions.subset_box(field.sel(time=str(year)), BOX).load().sortby("lat")
            one.attrs["box"] = BOX
            download.save_year(one, download.year_path(root, request, year))
            done.append(year)
    return done


def fetch_file(url: str, path: Path, chunk: int = 1 << 20) -> Path:
    """Download one file, resuming a partial download if there is one (network)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".part")
    have = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={have}-"} if have else {}
    with requests.get(url, stream=True, timeout=120, headers=headers) as response:
        if response.status_code == 416:  # already complete
            os.replace(partial, path)
            return path
        response.raise_for_status()
        mode = "ab" if response.status_code == 206 else "wb"
        with open(partial, mode) as handle:
            for block in response.iter_content(chunk):
                handle.write(block)
    os.replace(partial, path)
    return path


def main() -> int:
    root = download.DATA_ROOT
    root.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(root / "download.log"), logging.StreamHandler()],
    )
    for eobs_name, (variable, url) in FILES.items():
        request = download.Request(SOURCE, "", eobs_name, variable, "day", BOX, *download.DAILY_YEARS)
        if not download.pending_years(root, request):
            log.info("e-obs %s already complete", variable)
            continue
        raw = root / "raw" / Path(url).name
        if not raw.exists():
            log.info("downloading %s", url)
            fetch_file(url, raw)
        years = cut_years(raw, eobs_name, root)
        log.info("saved e-obs day %s %s for %d years", variable, BOX, len(years))
        raw.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
