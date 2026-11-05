import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk import extremes as ex


def _daily(values, start="1985-01-01"):
    time = pd.date_range(start, periods=len(values), freq="D")
    data = np.asarray(values, dtype=float)[:, None, None] * np.ones((1, 1, 2))
    return xr.DataArray(
        data, coords={"time": time, "lat": [50.0], "lon": [0.0, 1.0]}, dims=("time", "lat", "lon"),
        attrs={"units": "mm/day"},
    )


def test_r95p_on_a_toy_series():
    # 100 days: 60 dry (0.5 mm, below the wet-day limit), 40 wet with 1..40 mm
    values = [0.5] * 60 + list(range(1, 41))
    pr = _daily(values)
    threshold = ex.wet_day_threshold(pr, base=(1985, 1985))
    # 95th percentile of 1..40 (linear interpolation) = 38.05
    assert float(threshold.isel(lat=0, lon=0)) == pytest.approx(38.05)
    total = ex.r95p(pr, threshold)
    # days above 38.05 mm are 39 and 40: the WHOLE daily totals are summed, not the excess
    assert float(total.isel(year=0, lat=0, lon=0)) == pytest.approx(79.0)
    assert float(ex.wet_day_total(pr).isel(year=0, lat=0, lon=0)) == pytest.approx(sum(range(1, 41)))
    assert float(ex.r95p_share(pr, threshold).isel(year=0, lat=0, lon=0)) == pytest.approx(100 * 79 / 820)


def test_dry_days_do_not_enter_the_threshold():
    pr = _daily([0.0] * 300 + [10.0] * 20)
    assert float(ex.wet_day_threshold(pr, base=(1985, 1985)).max()) == pytest.approx(10.0)
    never_wet = _daily([0.2] * 365)
    threshold = ex.wet_day_threshold(never_wet, base=(1985, 1985))
    assert bool(threshold.isnull().all())
    assert bool(ex.r95p(never_wet, threshold).isnull().all())


def test_winter_labels_follow_the_january_year_and_drop_incomplete_winters():
    time = xr.DataArray(pd.date_range("1985-01-01", "1987-12-31", freq="D"), dims="time", name="time")
    time = time.assign_coords(time=time)
    labels = ex.period_labels(time, "DJF").to_series()
    assert labels["1985-01-15"] == -1  # winter 1985 lacks December 1984
    assert labels["1985-12-01"] == 1986 and labels["1986-02-28"] == 1986
    assert labels["1986-07-01"] == -1
    assert labels["1987-12-31"] == -1  # winter 1988 lacks January and February 1988
    assert sorted(set(labels[labels > 0])) == [1986, 1987]
    assert ex.period_labels(time, "ANN").to_series()["1986-07-01"] == 1986


def test_rx1day_and_txx_annual_and_winter():
    n = 365 * 2 + 59  # 1 Jan 1985 to 28 Feb 1987
    values = np.zeros(n)
    values[200] = 30.0  # 20 July 1985
    values[349] = 12.0  # 16 December 1985 -> winter 1986
    values[400] = 25.0  # 5 February 1986 -> winter 1986
    pr = _daily(values)
    annual = ex.rx1day(pr, "ANN")
    assert float(annual.sel(year=1985).max()) == 30.0 and float(annual.sel(year=1986).max()) == 25.0
    winter = ex.rx1day(pr, "DJF")
    assert list(winter.year.values) == [1986, 1987]
    assert float(winter.sel(year=1986).max()) == 25.0
    tasmax = (pr * 0 + 5.0).assign_attrs(units="°C")
    tasmax[200] = 31.0
    assert float(ex.txx(tasmax, "ANN").sel(year=1985).max()) == 31.0
    assert float(ex.txx(tasmax, "DJF").sel(year=1986).max()) == 5.0


def test_all_indices_has_every_index_for_both_periods():
    rng = np.random.default_rng(0)
    pr = _daily(rng.gamma(0.6, 6.0, 365 * 3 + 59))
    tasmax = (pr * 0 + rng.normal(10, 5, pr.sizes["time"])[:, None, None]).assign_attrs(units="°C")
    out = ex.all_indices(pr, tasmax, base=(1985, 1987))
    for tag in ("ann", "djf"):
        for name in ("p95", "rx1day", "r95p", "r95p_share", "txx"):
            assert f"{name}_{tag}" in out
    assert out.sizes["year_ann"] == 4 and out.sizes["year_djf"] == 3
    assert float(out.r95p_share_ann.max()) <= 100.0


def test_wet_days_and_intensity():
    # one year: 300 days of 0.5 mm (dry), 65 wet days of 4 mm
    pr = _daily([0.5] * 300 + [4.0] * 65)
    assert float(ex.wet_days(pr).isel(year=0, lat=0, lon=0)) == 65
    assert float(ex.wet_day_intensity(pr).isel(year=0, lat=0, lon=0)) == pytest.approx(4.0)
