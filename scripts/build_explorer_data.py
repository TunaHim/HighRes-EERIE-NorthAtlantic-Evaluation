"""Export compact data for the interactive explorer (docs/explorer/data.json).

    python scripts/build_explorer_data.py

Maps of every extreme index (mean over the period, 0.5 degree), maps of the
winter correlation with the NAO, land-average regional series, the winter NAO
index, and a coastline, all in one JSON file the browser can read. Needs the
downloaded data (data/) and the result tables in app_assets/.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eerie_uk import extremes as ex, provenance, regions, relationships as rel  # noqa: E402

SOURCES = ["e-obs", "era5", "icon-esm-er", "ifs-fesom2-sr"]
NAO_OF = {"e-obs": "era5", "era5": "era5", "icon-esm-er": "icon-esm-er", "ifs-fesom2-sr": "ifs-fesom2-sr"}
INDICES = ["rx1day", "r95p", "r95p_share", "txx"]
COARSEN = 2  # 0.25 degree -> 0.5 degree


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
        parts = getattr(clipped, "geoms", [clipped])
        for part in parts:
            if part.geom_type != "LineString":
                continue
            part = part.simplify(0.05)
            x, y = part.xy
            lons += [round(v, 2) for v in x] + [None]
            lats += [round(v, 2) for v in y] + [None]
    return {"lon": lons, "lat": lats}


def main():
    indices = {s: ex.indices_for(s) for s in SOURCES}
    grid = indices["era5"]
    indices["e-obs"] = regions.to_grid(indices["e-obs"], grid)
    land = regions.land_mask(grid.lat, grid.lon)
    common = land & indices["e-obs"].rx1day_ann.isel(year_ann=0).notnull()

    nao_table = pd.read_parquet(ROOT / "app_assets" / "nao_index_winter.parquet")

    def nao_index(source):
        part = nao_table[(nao_table.source == source) & nao_table.year.between(1986, 2014)]
        import xarray as xr

        return xr.DataArray(part.nao_on_era5_pattern.values, coords={"year": part.year.values}, dims="year")

    maps, correlation = {}, {}
    lat = lon = None
    for s in SOURCES:
        for key in INDICES:
            for tag in ("ann", "djf"):
                field = indices[s][f"{key}_{tag}"]
                mean = field.mean(f"year_{tag}")
                coarse = mean.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
                lat, lon = coarse.lat.values, coarse.lon.values
                maps[f"{s}|{key}|{tag}"] = rounded(coarse, 2 if key == "r95p_share" else 1)
            result = rel.correlate(indices[s][f"{key}_djf"].rename(year_djf="year"), nao_index(NAO_OF[s]))
            r = result.r.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()
            correlation[f"{s}|{key}"] = rounded(r, 2)

    series = pd.read_parquet(ROOT / "app_assets" / "extremes_regional.parquet")
    regional = {}
    for (source, region, period, index), part in series.groupby(["source", "region", "period", "index"]):
        part = part.sort_values("year")
        regional[f"{source}|{region}|{period}|{index}"] = {
            "year": part.year.astype(int).tolist(),
            "value": [round(float(v), 2) for v in part.value],
        }
    nao = {
        s: {"year": part.year.astype(int).tolist(), "value": [round(float(v), 3) for v in part.nao_on_era5_pattern]}
        for s, part in nao_table.groupby("source")
    }

    out = {
        "lat": [round(float(v), 3) for v in lat],
        "lon": [round(float(v), 3) for v in lon],
        "maps": maps,
        "nao_correlation": correlation,
        "regional": regional,
        "nao": nao,
        "nao_of": NAO_OF,
        "coastline": coastline("nw_europe"),
        "regions": {r: regions.BOXES[r] for r in regions.SUBREGIONS},
        "provenance": provenance.record(
            "Explorer data: period-mean extreme indices (0.5 degree), winter correlation with the NAO, "
            "land-average regional series, winter NAO index",
            inputs={"indices": "data/derived (notebook 05)", "tables": "app_assets/*.parquet (notebooks 04-06)"},
            period="1985-2014 (winters 1986-2014)",
        ),
    }
    target = ROOT / "docs" / "explorer" / "data.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size / 1e6:.1f} MB), {len(maps)} maps, {len(regional)} series")


if __name__ == "__main__":
    main()
