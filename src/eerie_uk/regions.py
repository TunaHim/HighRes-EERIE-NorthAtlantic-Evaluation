"""Spatial and seasonal subsetting helpers (pure xarray, no network)."""

from __future__ import annotations

import numpy as np
import xarray as xr

# (lon_min, lon_max, lat_min, lat_max), longitudes in degrees east on [-180, 180].
BOXES: dict[str, tuple[float, float, float, float]] = {
    "north_atlantic": (-90.0, 40.0, 20.0, 80.0),
    "uk_ireland": (-11.0, 2.5, 49.0, 61.0),
}


def _resolve_box(box) -> tuple[float, float, float, float]:
    if isinstance(box, str):
        try:
            return BOXES[box]
        except KeyError:
            raise KeyError(f"unknown box {box!r}; choose from {sorted(BOXES)}") from None
    lon_min, lon_max, lat_min, lat_max = box
    return float(lon_min), float(lon_max), float(lat_min), float(lat_max)


def subset_box(ds, box="uk_ireland", lon="lon", lat="lat"):
    """Cut a lon/lat box out of a regular-grid Dataset or DataArray.

    Works for longitudes stored on 0..360 or -180..180 and for latitude in
    either order. The result always has longitudes on -180..180, ascending,
    so boxes that straddle Greenwich come back contiguous. Stays lazy.
    """
    lon_min, lon_max, lat_min, lat_max = _resolve_box(box)

    if ds[lon].dims == ds[lat].dims and ds[lon].dims != (lon,):
        return _subset_cells(ds, (lon_min, lon_max, lat_min, lat_max), lon, lat)

    lon_values = np.asarray(ds[lon].values, dtype=float)
    wrapped = ((lon_values + 180.0) % 360.0) - 180.0
    keep = np.flatnonzero((wrapped >= lon_min) & (wrapped <= lon_max))
    keep = keep[np.argsort(wrapped[keep], kind="stable")]
    out = ds.isel({lon: keep}).assign_coords(
        {lon: (lon, wrapped[keep], dict(ds[lon].attrs))}
    )

    lat_values = np.asarray(ds[lat].values, dtype=float)
    keep_lat = np.flatnonzero((lat_values >= lat_min) & (lat_values <= lat_max))
    return out.isel({lat: keep_lat})


def _subset_cells(ds, box, lon, lat):
    """Box subset for grids stored as one flat cell dimension (IFS ``value``).

    Picks the cells inside the box, then unfolds them onto lat/lon axes.
    """
    lon_min, lon_max, lat_min, lat_max = box
    (cell,) = ds[lon].dims
    wrapped = ((np.asarray(ds[lon].values, dtype=float) + 180.0) % 360.0) - 180.0
    lat_values = np.asarray(ds[lat].values, dtype=float)
    keep = np.flatnonzero(
        (wrapped >= lon_min) & (wrapped <= lon_max) & (lat_values >= lat_min) & (lat_values <= lat_max)
    )
    out = ds.isel({cell: keep}).assign_coords({lon: (cell, wrapped[keep])})
    return out.set_index({cell: (lat, lon)}).unstack(cell).sortby([lat, lon])


def select_winter(ds, year: int, time="time"):
    """Select one DJF winter, labelled by the year of its January.

    ``year=1980`` returns 1 Dec 1979 to the end of Feb 1980.
    """
    return ds.sel({time: slice(f"{year - 1}-12-01", f"{year}-02-{_feb_end(ds, year, time)}")})


def _feb_end(ds, year: int, time: str) -> int:
    calendar = ds[time].dt.calendar if ds[time].size else "standard"
    if calendar == "360_day":
        return 30
    if calendar in ("noleap", "365_day"):
        return 28
    if calendar in ("all_leap", "366_day"):
        return 29
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 29 if leap else 28


def area_mean(da: xr.DataArray, lon="lon", lat="lat") -> xr.DataArray:
    """Cosine-latitude weighted mean over the horizontal dimensions."""
    weights = np.cos(np.deg2rad(da[lat]))
    return da.weighted(weights).mean([lon, lat])
