"""Download ERA5 monthly zonal wind at 850 and 250 hPa over the North Atlantic (reference for the jet).

    python scripts/fetch_era5_wind.py

Saves data/era5/mon/ua_north_atlantic_<year>.nc, 1950-2014, at 1 degree, with the pressure levels in
Pa (as in the HadGEM3 files written by eerie_uk.ceda). Resumable: existing years are skipped.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eerie_uk import catalogue, download  # noqa: E402

DATASET = "era5-dkrz.pressure-level_analysis_monthly"
LEVELS_HPA = [850, 250]
YEARS = range(1950, 2015)


def main():
    request = download.Request("era5", DATASET, "ua", "ua", "mon", "north_atlantic", YEARS[0], YEARS[-1],
                               coarsen=download.NAO_COARSEN)
    source = catalogue.open_dataset(DATASET)["ua"].sel(level=LEVELS_HPA)
    for year in download.pending_years(download.DATA_ROOT, request):
        started = time.time()
        for attempt in range(1, 4):
            try:
                part = source.sel(time=slice(f"{year}-01-01", f"{year}-12-31T23:59:59"))
                out = download.cut_to_box(part, "north_atlantic")
                out = out.coarsen(lat=download.NAO_COARSEN, lon=download.NAO_COARSEN, boundary="trim").mean(keep_attrs=True)
                out = out.rename(level="plev").assign_coords(plev=[100.0 * p for p in LEVELS_HPA]).rename("ua")
                out = out.drop_vars([c for c in out.coords if c not in out.dims])
                out.attrs.update(dataset_id=DATASET, source="era5", box="north_atlantic", units="m s-1")
                download.save_year(out, download.year_path(download.DATA_ROOT, request, year))
                print(f"saved era5 ua {year} in {time.time() - started:.0f} s", flush=True)
                break
            except Exception as exc:  # network errors: retry
                print(f"attempt {attempt} failed for {year}: {type(exc).__name__}: {exc}", flush=True)
                time.sleep(30 * attempt)


if __name__ == "__main__":
    main()
