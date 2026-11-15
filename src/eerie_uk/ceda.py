"""Download HadGEM3-GC5E EERIE historical runs (monthly) from the public CEDA archive.

The Met Office EERIE runs at three resolutions of one coupled model are public
on CEDA as CMIP-style netCDF files (whole globe, many years per file):

    LL  atmosphere about 135 km (N96),  ocean 1 degree
    MM  atmosphere about 60 km  (N216), ocean 1/4 degree
    HH  atmosphere about 20 km  (N640), ocean 1/12 degree (eddy-rich)

Only monthly fields are public. Each file is downloaded to ``data/raw``, cut to
the project's boxes year by year, saved in the same layout as the DKRZ
downloads (``data/<source>/mon/<variable>_<box>_<year>.nc``) and then deleted,
so disk use stays small. Existing years are skipped, so runs are resumable.

    python -m eerie_uk.ceda --resolution LL MM HH --variable psl pr tas
    python -m eerie_uk.ceda --resolution LL MM --variable ua
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from pathlib import Path

import xarray as xr

from .download import DATA_ROOT, Request, convert_units, cut_to_box, pending_years, save_year, year_path

log = logging.getLogger("eerie_uk.ceda")

BASE = "https://dap.ceda.ac.uk/badc/cmip6/data/EERIE/EERIE/MOHC/HadGEM3-GC5E-{res}/historical/r1i1p1f1/Amon/{var}/gn/v20250409/"
YEARS = (1950, 2014)
# variable -> boxes it is saved for (pressure levels for the wind, in Pa)
TARGETS = {
    "psl": ("north_atlantic",),
    "pr": ("nw_europe",),
    "tas": ("nw_europe",),
    "ua": ("north_atlantic",),
}
WIND_LEVELS = (85000.0, 25000.0)  # 850 hPa (eddy-driven jet) and 250 hPa (upper jet)


def source_name(resolution: str) -> str:
    return f"hadgem3-gc5e-{resolution.lower()}"


def list_files(resolution: str, variable: str, years=YEARS) -> list[str]:
    """URLs of the files that overlap ``years`` (network)."""
    import requests

    url = BASE.format(res=resolution, var=variable)
    names = sorted(set(re.findall(r'href="([^"/]+\.nc)"', requests.get(url, timeout=120).text)))
    keep = []
    for name in names:
        span = re.search(r"_(\d{4})\d\d-(\d{4})\d\d\.nc$", name)
        if span and int(span.group(2)) >= years[0] and int(span.group(1)) <= years[1]:
            keep.append(url + name)
    return keep


def file_years(url: str, years=YEARS) -> range:
    span = re.search(r"_(\d{4})\d\d-(\d{4})\d\d\.nc$", url)
    return range(max(int(span.group(1)), years[0]), min(int(span.group(2)), years[1]) + 1)


def download_file(url: str, folder: Path, retries: int = 8) -> Path:
    """Stream one file to disk with retries, resuming a broken transfer where it stopped (network)."""
    import requests

    folder.mkdir(parents=True, exist_ok=True)
    target = folder / url.rsplit("/", 1)[1]
    if target.exists():
        return target
    partial = target.with_suffix(".part")
    for attempt in range(1, retries + 1):
        try:
            done = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={done}-"} if done else {}
            with requests.get(url, stream=True, timeout=300, headers=headers) as response:
                response.raise_for_status()
                if done and response.status_code != 206:  # server ignored the range: start again
                    done = 0
                with open(partial, "ab" if done else "wb") as out:
                    for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                        out.write(chunk)
                expected = response.headers.get("Content-Range", "").rsplit("/", 1)[-1]
            if expected.isdigit() and partial.stat().st_size != int(expected):
                raise IOError(f"incomplete: {partial.stat().st_size} of {expected} bytes")
            os.replace(partial, target)
            return target
        except Exception as exc:  # network errors: wait and resume
            log.warning("attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt == retries:
                raise
            time.sleep(30 * attempt)
    return target


def cut_year(ds: xr.Dataset, variable: str, box: str, year: int) -> xr.DataArray:
    """One year of one variable, cut to a box, in project units and names."""
    da = ds[variable].sel(time=ds.time.dt.year == year)
    if variable == "ua":
        da = da.sel(plev=list(WIND_LEVELS), method="nearest")
    da = cut_to_box(da, box)
    if variable == "ua":
        out = da
    else:
        out = convert_units(da, variable)
    out = out.rename(variable)
    drop = [c for c in out.coords if c not in out.dims]
    out = out.drop_vars(drop)
    return out


def run(resolution: str, variable: str, root=DATA_ROOT, years=YEARS) -> list[int]:
    """Fetch every missing year of one variable at one resolution. Returns failed years."""
    source = source_name(resolution)
    failed = []
    for url in list_files(resolution, variable, years):
        span = file_years(url, years)
        missing = [
            (box, y)
            for box in TARGETS[variable]
            for y in span
            if y in pending_years(root, Request(source, url, variable, variable, "mon", box, y, y))
        ]
        if not missing:
            continue
        started = time.time()
        try:
            path = download_file(url, Path(root) / "raw" / source)
        except Exception as exc:
            log.error("gave up on %s: %s", url, exc)
            failed += sorted({y for _, y in missing})
            continue
        with xr.open_dataset(path, use_cftime=True) as ds:
            for box, year in missing:
                request = Request(source, url, variable, variable, "mon", box, year, year)
                out = cut_year(ds, variable, box, year)
                out.attrs.update(source=source, box=box, url=url, model=f"HadGEM3-GC5E-{resolution}",
                                 experiment="historical", member="r1i1p1f1")
                save_year(out, year_path(root, request, year))
        path.unlink()
        log.info("saved %s mon %s years %d-%d from %s in %.0f s",
                 source, variable, span[0], span[-1], url.rsplit("/", 1)[1], time.time() - started)
    return failed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--resolution", nargs="+", default=["LL", "MM", "HH"], choices=["LL", "MM", "HH"])
    parser.add_argument("--variable", nargs="+", default=["psl", "pr", "tas"], choices=list(TARGETS))
    parser.add_argument("--root", default=str(DATA_ROOT))
    parser.add_argument("--keep-awake", action="store_true", help="stop Windows idle-sleeping while this runs")
    args = parser.parse_args(argv)
    if args.keep_awake and os.name == "nt":
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    Path(args.root).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(Path(args.root) / "download.log"), logging.StreamHandler()],
    )
    failures = 0
    for resolution in args.resolution:
        for variable in args.variable:
            failed = run(resolution, variable, args.root)
            failures += len(failed)
    log.info("finished HadGEM3 %s %s with %d failed years", args.resolution, args.variable, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
