"""Export compact data for the interactive explorer (docs/explorer/data.json).

    python scripts/build_explorer_data.py

For E-OBS, ERA5 and the three historical runs (r1, r2, r3) of ICON-ESM-ER and
IFS-FESOM2-SR: maps of every extreme index (mean over the period, 0.5 degree),
maps of the winter correlation with the NAO, land-average regional series and
each dataset's winter NAO index. For each model also the mean of its three runs
(maps and correlation maps). Plus a coastline. Needs the downloaded data (data/)
and app_assets/nao_index_winter.parquet.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eerie_uk import climatology as clim, extremes as ex, nao, provenance, regions  # noqa: E402
from eerie_uk import relationships as rel, store  # noqa: E402

MODELS = {"icon-esm-er": ["icon-esm-er", "icon-esm-er.r2", "icon-esm-er.r3"],
          "ifs-fesom2-sr": ["ifs-fesom2-sr", "ifs-fesom2-sr.r2", "ifs-fesom2-sr.r3"]}
REFS = ["e-obs", "era5"]
RUNS = [r for runs in MODELS.values() for r in runs]
SOURCES = REFS + RUNS
INDICES = ["rx1day", "r95p", "r95p_share", "txx"]
COARSEN = 2  # 0.25 degree -> 0.5 degree
WINTERS = (1986, 2014)
YEARS = (1985, 2014)
BASE = (1975, 2014)  # anomaly base period available for every run (notebook 10)


def rounded(field, digits):
    values = np.round(field.values.astype(float), digits)
    return [[None if np.isnan(v) else float(v) for v in row] for row in values]


def coastline(box):
    """Natural Earth coastline segments inside the box, as lon/lat lists separated by nulls."""
    import cartopy.io.shapereader as shapereader
    import shapely

    lon_min, lon_max, lat_min, lat_max = regions.BOXES[box]
    window = shapely.box(lon_min, lat_min, lon_max, lat_max)
    path = shapereader.natural_earth(resolution="50m", category="physical", name="coastline")
    lons, lats = [], []
    for geometry in shapereader.Reader(path).geometries():
        clipped = geometry.intersection(window)
        if clipped.is_empty:
            continue
        for part in getattr(clipped, "geoms", [clipped]):
            if part.geom_type != "LineString":
                continue
            x, y = part.simplify(0.05).xy
            lons += [round(v, 2) for v in x] + [None]
            lats += [round(v, 2) for v in y] + [None]
    return {"lon": lons, "lat": lats}


def nao_indices():
    """Winter NAO along the ERA5 pattern, in ERA5 standard deviations, winters 1986-2014.

    ERA5 and r1 come from notebook 04's table. Runs r2 and r3 start in 1975, so their anomalies
    are taken relative to 1975-2014, exactly as in notebook 10.
    """
    table = pd.read_parquet(ROOT / "app_assets" / "nao_index_winter.parquet")
    out = {}
    for source, part in table.groupby("source"):
        part = part[part.year.between(*WINTERS)].sort_values("year")
        out[source] = xr.DataArray(part.nao_on_era5_pattern.values, coords={"year": part.year.values}, dims="year")
    era5_nao = nao.leading_eof(nao.winter_anomalies(store.load("era5", "mon", "psl", "north_atlantic")))
    for runs in MODELS.values():
        for run in runs[1:]:
            psl = clim.period(store.load(run, "mon", "psl", "north_atlantic"), *BASE)
            index = nao.project(nao.winter_anomalies(psl, BASE), era5_nao.vector) / era5_nao.amplitude
            out[run] = index.sel(year=slice(*WINTERS))
    return out


def main():
    indices = {s: ex.indices_for(s) for s in SOURCES}
    grid = indices["era5"]
    indices["e-obs"] = regions.to_grid(indices["e-obs"], grid)
    land = regions.land_mask(grid.lat, grid.lon)
    common = land & indices["e-obs"].rx1day_ann.isel(year_ann=0).notnull()
    naos = nao_indices()
    nao_of = {s: ("era5" if s in REFS else s) for s in SOURCES}

    maps, correlation, regional = {}, {}, {}
    lat = lon = None
    for s in SOURCES:
        for key in INDICES:
            for tag, period in (("ann", "annual"), ("djf", "winter")):
                field = indices[s][f"{key}_{tag}"]
                years = WINTERS if tag == "djf" else YEARS
                field = field.sel({f"year_{tag}": slice(*years)})
                coarse = field.mean(f"year_{tag}").coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
                lat, lon = coarse.lat.values, coarse.lon.values
                maps[f"{s}|{key}|{tag}"] = coarse
                series_field = field.where(common).rename({f"year_{tag}": "year"})
                for region in regions.SUBREGIONS:
                    values = clim.regional_mean(series_field, region)
                    regional[f"{s}|{region}|{period}|{key}"] = {
                        "year": values.year.values.astype(int).tolist(),
                        "value": [round(float(v), 2) for v in values.values],
                    }
            winter = indices[s][f"{key}_djf"].rename(year_djf="year").sel(year=slice(*WINTERS))
            result = rel.correlate(winter, naos[nao_of[s]])
            correlation[f"{s}|{key}"] = result.r.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
    # mean of the three runs of each model (maps and correlation maps)
    for model, runs in MODELS.items():
        for key in INDICES:
            for tag in ("ann", "djf"):
                maps[f"{model}.mean|{key}|{tag}"] = sum(maps[f"{r}|{key}|{tag}"] for r in runs) / len(runs)
            correlation[f"{model}.mean|{key}"] = sum(correlation[f"{r}|{key}"] for r in runs) / len(runs)

    out = {
        "lat": [round(float(v), 3) for v in lat],
        "lon": [round(float(v), 3) for v in lon],
        "maps": {k: rounded(v, 2 if "|r95p_share|" in k else 1) for k, v in maps.items()},
        "nao_correlation": {k: rounded(v, 2) for k, v in correlation.items()},
        "regional": regional,
        "nao": {s: {"year": v.year.values.astype(int).tolist(), "value": [round(float(x), 3) for x in v.values]}
                for s, v in naos.items() if s in SOURCES},
        "nao_of": nao_of,
        "models": MODELS,
        "coastline": coastline("nw_europe"),
        "regions": {r: regions.BOXES[r] for r in regions.SUBREGIONS},
        "provenance": provenance.record(
            "Explorer data: period-mean extreme indices (0.5 degree), winter correlation with the NAO, land-average "
            "regional series and winter NAO index for E-OBS, ERA5 and runs r1-r3 of ICON-ESM-ER and IFS-FESOM2-SR; "
            "three-run means of the maps",
            inputs={"indices": "data/derived (notebooks 05, 10)",
                    "nao": "app_assets/nao_index_winter.parquet (r1, ERA5); r2 and r3 projected onto the ERA5 "
                           "pattern with a 1975-2014 base (notebook 10)"},
            period="1985-2014 (winters 1986-2014)",
        ),
    }
    target = ROOT / "docs" / "explorer" / "data.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size / 1e6:.1f} MB), {len(out['maps'])} maps, {len(regional)} series")


if __name__ == "__main__":
    main()
