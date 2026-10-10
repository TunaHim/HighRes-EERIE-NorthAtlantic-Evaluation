"""Extreme indices from daily data (docs/methods.md, section 4).

RX1day  largest daily precipitation in a period
TXx     highest daily maximum temperature in a period
R95p    ETCCDI R95pTOT: total precipitation on days above the 95th percentile
        of wet-day precipitation (wet day: at least 1 mm), threshold per grid
        cell from the base period

A period is a calendar year ("ANN") or a winter ("DJF"). A winter is labelled
by the year of its January and incomplete winters are dropped.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

WET_DAY = 1.0  # mm/day
PERCENTILE = 95.0
BASE = (1985, 2014)


def period_labels(time: xr.DataArray, period: str) -> xr.DataArray:
    """Label each day with its year or winter; days outside the period get -1."""
    year = time.dt.year
    if period == "ANN":
        return year.rename("year")
    if period != "DJF":
        raise ValueError("period must be 'ANN' or 'DJF'")
    month = time.dt.month
    label = xr.where(month == 12, year + 1, year)
    label = xr.where(month.isin([12, 1, 2]), label, -1)
    # a winter is complete only if its December, January and February are all present
    months_present = {}
    for winter, m in zip(label.values, month.values):
        if winter > 0:
            months_present.setdefault(int(winter), set()).add(int(m))
    complete = [w for w, months in months_present.items() if months == {12, 1, 2}]
    return xr.where(label.isin(complete), label, -1).rename("year")


def _by_period(da: xr.DataArray, period: str):
    labels = period_labels(da.time, period)
    kept = da.sel(time=(labels > 0).values)
    return kept.groupby(labels.sel(time=kept.time))


def rx1day(pr: xr.DataArray, period: str = "ANN") -> xr.DataArray:
    """Largest one-day precipitation total in each period (mm)."""
    out = _by_period(pr, period).max("time")
    out.attrs = {"units": "mm", "long_name": f"RX1day ({period})"}
    return out


def txx(tasmax: xr.DataArray, period: str = "ANN") -> xr.DataArray:
    """Highest daily maximum temperature in each period."""
    out = _by_period(tasmax, period).max("time")
    out.attrs = {"units": tasmax.attrs.get("units", "°C"), "long_name": f"TXx ({period})"}
    return out


def wet_day_threshold(pr: xr.DataArray, base=BASE, period: str = "ANN") -> xr.DataArray:
    """95th percentile of wet-day precipitation at each cell over the base period.

    For ``period="DJF"`` only winter days are used, so the threshold describes
    what is heavy for a winter day.
    """
    days = pr.sel(time=slice(f"{base[0]}-01-01", f"{base[1]}-12-31"))
    if period == "DJF":
        days = days.sel(time=days.time.dt.month.isin([12, 1, 2]))
    out = days.where(days >= WET_DAY).quantile(PERCENTILE / 100.0, "time", skipna=True).drop_vars("quantile")
    out.attrs = {"units": "mm/day", "long_name": f"95th percentile of wet days ({period})"}
    return out


def r95p(pr: xr.DataArray, threshold: xr.DataArray, period: str = "ANN") -> xr.DataArray:
    """Total precipitation on days wetter than the threshold, per period (mm)."""
    out = _by_period(pr.where(pr > threshold, 0.0), period).sum("time")
    out = out.where(threshold.notnull())
    out.attrs = {"units": "mm", "long_name": f"R95p ({period})"}
    return out


def wet_day_total(pr: xr.DataArray, period: str = "ANN") -> xr.DataArray:
    """Total precipitation on wet days, per period (mm). ETCCDI PRCPTOT."""
    out = _by_period(pr.where(pr >= WET_DAY, 0.0), period).sum("time")
    out.attrs = {"units": "mm", "long_name": f"wet-day total ({period})"}
    return out


def r95p_share(pr: xr.DataArray, threshold: xr.DataArray, period: str = "ANN") -> xr.DataArray:
    """R95p as a percentage of the wet-day total, per period."""
    total = wet_day_total(pr, period)
    out = 100.0 * r95p(pr, threshold, period) / total.where(total > 0)
    out.attrs = {"units": "%", "long_name": f"R95p share of wet-day total ({period})"}
    return out


def all_indices(pr: xr.DataArray, tasmax: xr.DataArray, base=BASE) -> xr.Dataset:
    """Every index of the project for one data source, annual and winter."""
    out = {}
    for period, tag in (("ANN", "ann"), ("DJF", "djf")):
        threshold = wet_day_threshold(pr, base, period)
        out[f"p95_{tag}"] = threshold
        out[f"rx1day_{tag}"] = rx1day(pr, period).rename(year=f"year_{tag}")
        out[f"r95p_{tag}"] = r95p(pr, threshold, period).rename(year=f"year_{tag}")
        out[f"r95p_share_{tag}"] = r95p_share(pr, threshold, period).rename(year=f"year_{tag}")
        out[f"txx_{tag}"] = txx(tasmax, period).rename(year=f"year_{tag}")
    return xr.Dataset(out)
