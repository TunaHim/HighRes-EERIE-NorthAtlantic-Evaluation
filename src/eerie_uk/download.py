"""Download regional cut-outs, one compressed netCDF file per year.

The DKRZ server sends whole-globe chunks. Each chunk is cut to the requested
box in memory and only the cut-out is written, so disk use stays small. A year
that already has a file is skipped, which makes every download resumable.

Run from the project root, for example::

    python -m eerie_uk.download --group monthly
    python -m eerie_uk.download --group daily --source icon-esm-er
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from . import regions

log = logging.getLogger("eerie_uk.download")

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Request:
    """One variable from one dataset, cut to one box, for a span of years."""

    source: str  # short label, used as the folder name
    dataset_id: str
    native: str  # variable name on the server
    variable: str  # CMIP-style name used in the saved file
    frequency: str  # "mon" or "day"
    box: str
    start_year: int
    end_year: int
    coarsen: int = 1  # block-average this many grid cells per side before saving

    @property
    def years(self) -> range:
        return range(self.start_year, self.end_year + 1)


_ICON = "icon-esm-er.hist-1950.v20240618.atmos.gr025."
_FESOM = "ifs-fesom2-sr.hist-1950.v20240304.atmos.gr025."
_AMIP = "ifs-amip-{res}.{exp}.v20240901.atmos.gr025.2D_monthly"

MONTHLY_YEARS = (1950, 2014)
DAILY_YEARS = (1985, 2014)
AMIP_YEARS = (1980, 2023)
# The NAO is a basin-scale pattern: 1 degree is ample and 16 times smaller on disk.
NAO_COARSEN = 4


def build_plan() -> list[Request]:
    """Every download the prototype needs, in the order it should run."""
    plan = []
    # Monthly: pressure on the North Atlantic (NAO), tas and pr on NW Europe.
    for source, dataset, names in (
        ("icon-esm-er", _ICON + "2d_monthly_mean", {"psl": "psl", "tas": "tas", "pr": "pr"}),
        ("ifs-fesom2-sr", _FESOM + "2D_monthly_avg", {"psl": "mmsl", "tas": "mean2t", "pr": "tprate"}),
    ):
        plan.append(Request(source, dataset, names["psl"], "psl", "mon", "north_atlantic", *MONTHLY_YEARS, coarsen=NAO_COARSEN))
        plan.append(Request(source, dataset, names["tas"], "tas", "mon", "nw_europe", *MONTHLY_YEARS))
        plan.append(Request(source, dataset, names["pr"], "pr", "mon", "nw_europe", *MONTHLY_YEARS))
    plan.append(Request("era5", "era5-dkrz.surface_analysis_monthly", "psl", "psl", "mon", "north_atlantic", *MONTHLY_YEARS, coarsen=NAO_COARSEN))
    plan.append(Request("era5", "era5-dkrz.surface_analysis_monthly", "tas", "tas", "mon", "nw_europe", *MONTHLY_YEARS))
    plan.append(Request("era5", "era5-dkrz.surface_forecast_monthly", "tp", "pr", "mon", "nw_europe", *MONTHLY_YEARS))
    # Paired atmosphere-only runs: observed SST versus eddy-filtered SST.
    for resolution, experiments in (
        ("tco1279", ("hist", "hist-c-0-a-lr20")),
        ("tco399", ("hist", "hist-c-0-a-lr20", "hist-c-lr20-a-0")),
    ):
        for experiment in experiments:
            plan.append(
                Request(
                    f"ifs-amip-{resolution}.{experiment}",
                    _AMIP.format(res=resolution, exp=experiment),
                    "avg_msl",
                    "psl",
                    "mon",
                    "north_atlantic",
                    *AMIP_YEARS,
                    coarsen=NAO_COARSEN,
                )
            )
    # Daily: precipitation and maximum temperature on NW Europe.
    plan.append(Request("icon-esm-er", _ICON + "2d_daily_mean", "pr", "pr", "day", "nw_europe", *DAILY_YEARS))
    plan.append(Request("icon-esm-er", _ICON + "2d_daily_max", "tas", "tasmax", "day", "nw_europe", *DAILY_YEARS))
    plan.append(Request("ifs-fesom2-sr", _FESOM + "2D_daily_avg", "tprate", "pr", "day", "nw_europe", *DAILY_YEARS))
    plan.append(Request("ifs-fesom2-sr", _FESOM + "2D_daily_max", "mx2t24", "tasmax", "day", "nw_europe", *DAILY_YEARS))
    plan.append(Request("era5", "era5-dkrz.surface_forecast_daily", "tp", "pr", "day", "nw_europe", *DAILY_YEARS))
    plan.append(Request("era5", "era5-dkrz.surface_forecast_daily", "tasmax", "tasmax", "day", "nw_europe", *DAILY_YEARS))
    return plan


# --- pure helpers ------------------------------------------------------------

# Factor that turns a precipitation unit into mm per day.
_PR_TO_MM_DAY = {
    "kg m-2 s-1": 86400.0,  # 1 kg m-2 = 1 mm of water
    "m s**-1": 86400.0 * 1000.0,
    "m s-1": 86400.0 * 1000.0,
    "m": 1000.0,  # ERA5 daily total, or monthly mean of daily totals
}


def convert_units(da: xr.DataArray, variable: str) -> xr.DataArray:
    """Bring a field to the project's common units.

    pr -> mm/day, psl -> hPa, temperatures stay in K.
    """
    units = str(da.attrs.get("units", "")).strip()
    if variable == "pr":
        if units == "mm/day":
            return da
        if units not in _PR_TO_MM_DAY:
            raise ValueError(f"unknown precipitation units {units!r}")
        out = da * _PR_TO_MM_DAY[units]
        new_units = "mm/day"
    elif variable == "psl":
        if units == "hPa":
            return da
        if units != "Pa":
            raise ValueError(f"unknown pressure units {units!r}")
        out, new_units = da / 100.0, "hPa"
    else:
        if units != "K":
            raise ValueError(f"unknown temperature units {units!r}")
        return da
    out.attrs = {**da.attrs, "units": new_units, "original_units": units}
    return out


def year_path(root, request: Request, year: int) -> Path:
    name = f"{request.variable}_{request.box}_{year}.nc"
    return Path(root) / request.source / request.frequency / name


def pending_years(root, request: Request) -> list[int]:
    """Years of a request that have no file yet."""
    return [y for y in request.years if not year_path(root, request, y).exists()]


def cut_to_box(da: xr.DataArray, box: str) -> xr.DataArray:
    """Load ``da`` cut to ``box`` on a regular lat/lon grid.

    Regular grids and flat-but-regular grids (IFS) are cut directly. Reduced
    Gaussian grids (ERA5) are cut with a margin and interpolated to 0.25 deg.
    """
    if regions.is_flat(da) and not regions.is_regular_flat(da):
        cells = regions.select_cells(da, box, pad=1.0).load()
        return regions.cells_to_regular(cells, box)
    return regions.subset_box(da, box).load().sortby("lat")


def save_year(da: xr.DataArray, path: Path) -> None:
    """Write one year as compressed float32 netCDF, atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".part")
    da = da.astype("float32")
    da.to_dataset(name=da.name).to_netcdf(
        partial,
        encoding={da.name: {"zlib": True, "complevel": 4, "dtype": "float32"}},
        unlimited_dims=["time"],
    )
    os.replace(partial, path)


# --- network -----------------------------------------------------------------


def fetch_year(request: Request, year: int, opener=None) -> xr.DataArray:
    """One year of one request, cut, converted and loaded (network)."""
    return fetch(request, f"{year}-01-01", f"{year}-12-31T23:59:59", opener)


def fetch(request: Request, start: str, end: str, opener=None) -> xr.DataArray:
    """Any time span of one request, cut, converted and loaded (network)."""
    if opener is None:
        from .catalogue import open_dataset as opener
    source = opener(request.dataset_id)[request.native]
    source = source.sel(time=slice(start, end))
    if source.sizes["time"] == 0:
        raise LookupError(f"{request.dataset_id} has no data for {start} to {end}")
    out = convert_units(cut_to_box(source, request.box), request.variable).rename(request.variable)
    if request.coarsen > 1:
        out = out.coarsen(lat=request.coarsen, lon=request.coarsen, boundary="trim").mean(keep_attrs=True)
    extra = [d for d in out.dims if d not in ("time", "lat", "lon") and out.sizes[d] == 1]
    out = out.squeeze(extra, drop=True)  # e.g. ICON's single 2 m height level
    out = out.drop_vars([c for c in out.coords if c not in out.dims])
    out.attrs.update(
        dataset_id=request.dataset_id, native_name=request.native, source=request.source, box=request.box
    )
    return out


def run(request: Request, root=DATA_ROOT, opener=None, retries: int = 3, pause: float = 30.0) -> list[int]:
    """Download the missing years of one request. Returns the years that failed."""
    failed = []
    for year in pending_years(root, request):
        started = time.time()
        for attempt in range(1, retries + 1):
            try:
                save_year(fetch_year(request, year, opener), year_path(root, request, year))
                log.info(
                    "saved %s %s %s %s %d in %.0f s",
                    request.source, request.frequency, request.variable, request.box, year, time.time() - started,
                )
                break
            except Exception as exc:
                log.warning(
                    "attempt %d/%d failed for %s %s %d: %s: %s",
                    attempt, retries, request.source, request.variable, year, type(exc).__name__, exc,
                )
                if attempt == retries:
                    failed.append(year)
                else:
                    time.sleep(pause * attempt)
    return failed


def measure(request: Request, start: str, end: str, root, opener=None) -> dict:
    """Download a short sample and time it (network).

    Saves the sample under ``root/sample`` and returns one table row with the
    speed, the size on disk and basic statistics, so the full download can be
    costed before it is started. Failures are reported in the row, not raised.
    """
    row = {
        "source": request.source,
        "frequency": request.frequency,
        "variable": request.variable,
        "box": request.box,
    }
    path = Path(root) / "sample" / f"{request.source}_{request.frequency}_{request.variable}_{request.box}.nc"
    started = time.time()
    try:
        sample = fetch(request, start, end, opener)
        seconds = time.time() - started
        save_year(sample, path)
    except Exception as exc:
        return {**row, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
    steps = sample.sizes["time"]
    return {
        **row,
        "ok": True,
        "error": "",
        "steps": steps,
        "seconds_per_step": seconds / steps,
        "mb_per_step": path.stat().st_size / 1e6 / steps,
        "grid": f"{sample.sizes['lat']} x {sample.sizes['lon']}",
        "members": int(sample.sizes.get("realization", 1)),
        "units": sample.attrs.get("units", ""),
        "server_units": sample.attrs.get("original_units", sample.attrs.get("units", "")),
        "min": float(sample.min()),
        "mean": float(sample.mean()),
        "max": float(sample.max()),
        "missing": int(sample.isnull().sum()),
        "path": str(path),
    }


def estimate(request: Request, seconds_per_step: float, mb_per_step: float) -> dict:
    """Cost of the full request, extrapolated from a measured sample."""
    steps = len(request.years) * (12 if request.frequency == "mon" else 365.25)
    return {"steps": int(steps), "hours": steps * seconds_per_step / 3600.0, "gb": steps * mb_per_step / 1000.0}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--group", choices=["monthly", "daily", "all"], default="all")
    parser.add_argument("--source", help="only sources whose name starts with this")
    parser.add_argument("--root", default=str(DATA_ROOT))
    parser.add_argument("--keep-awake", action="store_true", help="stop Windows idle-sleeping while this runs")
    args = parser.parse_args(argv)
    if args.keep_awake and os.name == "nt":
        import ctypes

        # ES_CONTINUOUS | ES_SYSTEM_REQUIRED: lasts only as long as this process.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)

    Path(args.root).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(Path(args.root) / "download.log"), logging.StreamHandler()],
    )
    wanted = {"monthly": ("mon",), "daily": ("day",), "all": ("mon", "day")}[args.group]
    failures = 0
    for request in build_plan():
        if request.frequency not in wanted:
            continue
        if args.source and not request.source.startswith(args.source):
            continue
        failed = run(request, args.root)
        if failed:
            failures += len(failed)
            log.error("gave up on %s %s years %s", request.source, request.variable, failed)
    log.info("finished group=%s with %d failed years", args.group, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
