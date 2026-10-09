"""Spatial and seasonal subsetting helpers (pure xarray, no network)."""

from __future__ import annotations

import numpy as np
import xarray as xr

# (lon_min, lon_max, lat_min, lat_max), longitudes in degrees east on [-180, 180].
BOXES: dict[str, tuple[float, float, float, float]] = {
    "north_atlantic": (-90.0, 40.0, 20.0, 80.0),
    "nw_europe": (-20.0, 13.0, 40.0, 65.0),
    "uk_ireland": (-11.0, 2.5, 49.0, 61.0),
    "western_norway": (4.5, 8.5, 58.0, 63.0),
    "nw_france": (-5.0, 3.0, 46.0, 50.5),
}

# The three nested analysis domains, largest first, and the sub-regions used
# for headline numbers inside NW Europe.
DOMAINS = ("north_atlantic", "nw_europe", "uk_ireland")
SUBREGIONS = ("uk_ireland", "western_norway", "nw_france")
LABELS = {
    "north_atlantic": "North Atlantic",
    "nw_europe": "North-west Europe",
    "uk_ireland": "UK and Ireland",
    "western_norway": "Western Norway",
    "nw_france": "North-west France",
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


def is_flat(ds, lon="lon", lat="lat") -> bool:
    """True when lon/lat are per-cell coordinates on one shared dimension."""
    return ds[lon].dims == ds[lat].dims and ds[lon].dims != (lon,)


def is_regular_flat(ds, lon="lon", lat="lat") -> bool:
    """True when a flat cell grid is a full lon x lat rectangle in disguise."""
    n_lon = np.unique(np.asarray(ds[lon].values)).size
    n_lat = np.unique(np.asarray(ds[lat].values)).size
    return n_lon * n_lat == ds[lon].size


def select_cells(ds, box, pad: float = 0.0, lon="lon", lat="lat"):
    """Cells of a flat grid inside the box (plus ``pad`` degrees), still flat."""
    lon_min, lon_max, lat_min, lat_max = _resolve_box(box)
    (cell,) = ds[lon].dims
    wrapped = ((np.asarray(ds[lon].values, dtype=float) + 180.0) % 360.0) - 180.0
    lat_values = np.asarray(ds[lat].values, dtype=float)
    keep = np.flatnonzero(
        (wrapped >= lon_min - pad)
        & (wrapped <= lon_max + pad)
        & (lat_values >= lat_min - pad)
        & (lat_values <= lat_max + pad)
    )
    return ds.isel({cell: keep}).assign_coords({lon: (cell, wrapped[keep])})


def cells_to_regular(da: xr.DataArray, box, step: float = 0.25, lon="lon", lat="lat"):
    """Interpolate a reduced Gaussian cut-out (ERA5) onto a regular grid.

    Each latitude row has its own longitudes, so rows are interpolated in
    longitude first and the rows are then interpolated in latitude. Linear in
    both directions. ``da`` must be loaded and should come from
    ``select_cells`` with a pad of about one degree.
    """
    lon_min, lon_max, lat_min, lat_max = _resolve_box(box)
    (cell,) = da[lon].dims
    target_lon = np.arange(lon_min, lon_max + step / 2, step)
    target_lat = np.arange(lat_min, lat_max + step / 2, step)
    cell_lon = np.asarray(da[lon].values, dtype=float)
    cell_lat = np.asarray(da[lat].values, dtype=float)
    values = da.transpose(..., cell).values
    rows = np.unique(cell_lat)

    by_row = np.empty(values.shape[:-1] + (rows.size, target_lon.size))
    for i, row in enumerate(rows):
        members = np.flatnonzero(cell_lat == row)
        members = members[np.argsort(cell_lon[members])]
        x = cell_lon[members]
        y = values[..., members]
        right = np.clip(np.searchsorted(x, target_lon), 1, x.size - 1)
        weight = np.clip((target_lon - x[right - 1]) / (x[right] - x[right - 1]), 0.0, 1.0)
        by_row[..., i, :] = y[..., right - 1] * (1.0 - weight) + y[..., right] * weight

    upper = np.clip(np.searchsorted(rows, target_lat), 1, rows.size - 1)
    weight = np.clip((target_lat - rows[upper - 1]) / (rows[upper] - rows[upper - 1]), 0.0, 1.0)
    weight = weight[:, None]
    regular = by_row[..., upper - 1, :] * (1.0 - weight) + by_row[..., upper, :] * weight

    other = [d for d in da.dims if d != cell]
    coords = {d: da[d] for d in other}
    coords.update({lat: target_lat, lon: target_lon})
    return xr.DataArray(regular, dims=other + [lat, lon], coords=coords, attrs=da.attrs, name=da.name)


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
