"""Event-based diagnostics: the weather around the heaviest rain days.

- ``top_events``: the n largest values of a daily series, at least ``separation``
  days apart, so one storm is not counted several times.
- ``lagged_composite``: the average map on the days before and after the events.
- ``day_to_day_change``: standard deviation of the 24-hour change of a field, a
  simple measure of how active the passing storms are (storminess).
- ``persistent_episodes``: runs of consecutive days above a threshold, used for
  long-lasting high-pressure spells (a simple blocking and stagnation proxy).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


def top_events(series: xr.DataArray, n: int = 30, separation: int = 5) -> pd.DatetimeIndex:
    """Dates of the ``n`` largest values, at least ``separation`` days apart."""
    values = series.to_series().dropna().sort_values(ascending=False)
    chosen: list[pd.Timestamp] = []
    for date in values.index:
        if all(abs((date - c).days) >= separation for c in chosen):
            chosen.append(date)
            if len(chosen) == n:
                break
    return pd.DatetimeIndex(sorted(chosen))


def lagged_composite(field: xr.DataArray, dates, lags=(-3, -2, -1, 0)) -> xr.DataArray:
    """Average of ``field`` on each event date shifted by each lag (in days)."""
    out = []
    available = pd.DatetimeIndex(field.time.values)
    for lag in lags:
        shifted = pd.DatetimeIndex(dates) + pd.Timedelta(days=lag)
        shifted = shifted[shifted.isin(available)]
        out.append(field.sel(time=shifted).mean("time"))
    return xr.concat(out, pd.Index(list(lags), name="lag"))


def day_to_day_change(field: xr.DataArray) -> xr.DataArray:
    """Standard deviation of the change from one day to the next.

    Only pairs of consecutive calendar days are used, so gaps between winters
    do not create spurious jumps.
    """
    time = pd.DatetimeIndex(field.time.values)
    consecutive = np.flatnonzero((time[1:] - time[:-1]) == pd.Timedelta(days=1))
    change = field.isel(time=consecutive + 1).values - field.isel(time=consecutive).values
    out = field.isel(time=0, drop=True).copy(data=np.nanstd(change, axis=0))
    out.attrs = {"units": field.attrs.get("units", ""), "long_name": "standard deviation of the 24-hour change"}
    return out


def persistent_episodes(series, threshold: float, min_length: int = 5) -> list[int]:
    """Lengths of runs of consecutive values above ``threshold`` lasting ``min_length`` or more."""
    above = np.asarray(series, dtype=float) > threshold
    lengths, run = [], 0
    for flag in above:
        if flag:
            run += 1
        else:
            if run >= min_length:
                lengths.append(run)
            run = 0
    if run >= min_length:
        lengths.append(run)
    return lengths
