"""Seasonal means, climatologies and simple comparison statistics (pure xarray)."""

from __future__ import annotations

import numpy as np
import xarray as xr

from . import regions

SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}


def period(da: xr.DataArray, start: int, end: int) -> xr.DataArray:
    """Keep the years ``start``..``end`` inclusive."""
    return da.sel(time=slice(f"{start}-01-01", f"{end}-12-31"))


def season_means(da: xr.DataArray, season: str = "DJF") -> xr.DataArray:
    """One mean per year for a season, from monthly data.

    A winter is labelled by the year of its January (DJF 1990 = Dec 1989 to
    Feb 1990). Seasons with a month missing are dropped. Months are weighted
    equally, not by their length.
    """
    months = SEASONS[season]
    picked = da.sel(time=da.time.dt.month.isin(months))
    year = picked.time.dt.year + (picked.time.dt.month == 12) * (season == "DJF")
    picked = picked.assign_coords(year=("time", year.values))
    count = picked.time.groupby(picked.year).count()
    means = picked.groupby("year").mean("time")
    return means.sel(year=count.year[count.values == len(months)].values)


def climatology(da: xr.DataArray, season: str = "DJF") -> xr.DataArray:
    """Long-term mean of a season."""
    return season_means(da, season).mean("year", keep_attrs=True)


def interannual_std(da: xr.DataArray, season: str = "DJF") -> xr.DataArray:
    """Year-to-year standard deviation of the seasonal mean."""
    return season_means(da, season).std("year", ddof=1, keep_attrs=True)


def monthly_cycle(da: xr.DataArray) -> xr.DataArray:
    """Mean of each calendar month (the seasonal cycle)."""
    return da.groupby("time.month").mean("time", keep_attrs=True)


def regional_mean(da: xr.DataArray, box) -> xr.DataArray:
    """Area-weighted mean over a named box."""
    return regions.area_mean(regions.subset_box(da, box))


def pattern_stats(model: xr.DataArray, reference: xr.DataArray) -> dict:
    """Area-weighted bias, RMSE and pattern correlation of two maps on one grid."""
    weights = np.cos(np.deg2rad(model.lat))
    difference = model - reference
    bias = float(difference.weighted(weights).mean())
    rmse = float(np.sqrt((difference**2).weighted(weights).mean()))
    m = model - model.weighted(weights).mean()
    r = reference - reference.weighted(weights).mean()
    correlation = float(
        (m * r).weighted(weights).mean()
        / np.sqrt((m**2).weighted(weights).mean() * (r**2).weighted(weights).mean())
    )
    return {"bias": bias, "rmse": rmse, "pattern correlation": correlation}
