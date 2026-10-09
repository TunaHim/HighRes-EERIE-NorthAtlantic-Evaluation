import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk import climatology as clim
from eerie_uk import download, store


def _monthly(start="1989-01-01", periods=36, stamp="start"):
    time = pd.date_range(start, periods=periods, freq="MS")
    values = time.month.values.astype(float)  # value = calendar month
    if stamp == "end":
        time = time + pd.offsets.MonthEnd(0) + pd.Timedelta("23:59:59")
    lat = np.array([50.0, 55.0])
    lon = np.array([-5.0, 0.0])
    data = values[:, None, None] * np.ones((1, 2, 2))
    return xr.DataArray(data, coords={"time": time, "lat": lat, "lon": lon}, dims=("time", "lat", "lon"), name="tas")


def test_season_means_label_winter_by_january_and_drop_incomplete():
    out = clim.season_means(_monthly(), "DJF")
    assert list(out.year.values) == [1990, 1991]  # 1989 lacks its December, 1992 its Jan/Feb
    assert float(out.isel(year=0, lat=0, lon=0)) == pytest.approx((12 + 1 + 2) / 3)


def test_season_means_summer_and_climatology():
    da = _monthly()
    assert list(clim.season_means(da, "JJA").year.values) == [1989, 1990, 1991]
    assert float(clim.climatology(da, "JJA").mean()) == pytest.approx(7.0)
    assert float(clim.interannual_std(da, "JJA").max()) == pytest.approx(0.0)


def test_monthly_cycle_and_period():
    da = _monthly()
    cycle = clim.monthly_cycle(da)
    assert list(cycle.month.values) == list(range(1, 13))
    assert float(cycle.sel(month=4).mean()) == 4.0
    assert clim.period(da, 1990, 1990).sizes["time"] == 12


def test_regional_mean_and_pattern_stats():
    da = _monthly().isel(time=0)
    assert float(clim.regional_mean(da, (-6.0, 1.0, 49.0, 56.0))) == pytest.approx(1.0)
    stats = clim.pattern_stats(da + 2.0, da)
    assert stats["bias"] == pytest.approx(2.0) and stats["rmse"] == pytest.approx(2.0)
    ramp = da + xr.DataArray([0.0, 1.0], coords={"lat": da.lat}, dims="lat")
    assert clim.pattern_stats(ramp, ramp)["pattern correlation"] == pytest.approx(1.0)


def test_store_round_trip_standardises_month_stamps(tmp_path):
    request = download.Request("fake", "", "tas", "tas", "mon", "uk_ireland", 1989, 1991)
    da = _monthly(stamp="end")
    for year in request.years:
        download.save_year(da.sel(time=str(year)), download.year_path(tmp_path, request, year))
    table = store.available(tmp_path)
    assert table.loc[0, ["source", "variable", "box", "first", "last", "years", "gaps"]].tolist() == [
        "fake", "tas", "uk_ireland", 1989, 1991, 3, ""]
    loaded = store.load("fake", "mon", "tas", "uk_ireland", root=tmp_path)
    assert str(loaded.time.values[0])[:10] == "1989-01-01" and loaded.sizes["time"] == 36
    assert float(loaded.sel(time="1990-07-01").mean()) == 7.0
    assert store.load("fake", "mon", "tas", "uk_ireland", years=[1990], root=tmp_path).sizes["time"] == 12
    with pytest.raises(FileNotFoundError):
        store.load("fake", "mon", "pr", "uk_ireland", root=tmp_path)


def test_store_reports_gaps(tmp_path):
    request = download.Request("fake", "", "tas", "tas", "mon", "uk_ireland", 1989, 1991)
    da = _monthly()
    for year in (1989, 1991):
        download.save_year(da.sel(time=str(year)), download.year_path(tmp_path, request, year))
    assert store.available(tmp_path).loc[0, "gaps"] == "1990"
