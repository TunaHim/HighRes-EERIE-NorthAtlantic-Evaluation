import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk import events as ev


def _series(values, start="2000-01-01"):
    time = pd.date_range(start, periods=len(values), freq="D")
    return xr.DataArray(np.asarray(values, dtype=float), coords={"time": time}, dims="time")


def test_top_events_respects_the_separation():
    values = np.zeros(40)
    values[[5, 6, 7]] = [10, 12, 11]  # one storm lasting three days
    values[20] = 9
    values[30] = 8
    dates = ev.top_events(_series(values), n=3, separation=5)
    assert [d.day for d in dates] == [7, 21, 31]  # 7 Jan (12 mm), not also 6 or 8 Jan


def test_lagged_composite_averages_the_days_before_each_event():
    time = pd.date_range("2000-01-01", periods=10, freq="D")
    field = xr.DataArray(np.arange(10.0)[:, None] * np.ones((1, 2)), coords={"time": time, "x": [0, 1]}, dims=("time", "x"))
    out = ev.lagged_composite(field, pd.DatetimeIndex(["2000-01-05", "2000-01-09"]), lags=(-2, 0))
    assert float(out.sel(lag=0).mean()) == pytest.approx((4 + 8) / 2)
    assert float(out.sel(lag=-2).mean()) == pytest.approx((2 + 6) / 2)
    # a lag that falls outside the record is skipped, not filled with zeros
    late = ev.lagged_composite(field, pd.DatetimeIndex(["2000-01-01"]), lags=(-1,))
    assert bool(late.isnull().all())


def test_day_to_day_change_ignores_gaps_between_seasons():
    winter1 = pd.date_range("2000-01-01", periods=3, freq="D")
    winter2 = pd.date_range("2000-12-01", periods=3, freq="D")
    time = winter1.append(winter2)
    values = np.array([0.0, 1.0, 0.0, 100.0, 101.0, 100.0])
    field = xr.DataArray(values[:, None], coords={"time": time, "x": [0]}, dims=("time", "x"))
    assert float(ev.day_to_day_change(field).squeeze()) == pytest.approx(1.0)  # the jump of 100 is not used


def test_persistent_episodes():
    series = [0, 2, 2, 2, 2, 2, 0, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2]
    assert ev.persistent_episodes(series, threshold=1, min_length=5) == [5, 7]
    assert ev.persistent_episodes([0, 0, 0], threshold=1) == []
