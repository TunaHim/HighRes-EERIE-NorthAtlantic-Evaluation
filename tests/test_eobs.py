import numpy as np
import pandas as pd
import xarray as xr

from eerie_uk import download, eobs


def _eobs_file(path, name, value):
    time = pd.date_range("1985-01-01", "1986-12-31", freq="D")
    lat = np.arange(35.125, 70.0, 0.25)
    lon = np.arange(-25.125, 20.0, 0.25)
    data = np.full((time.size, lat.size, lon.size), value, dtype="float32")
    xr.Dataset(
        {name: (("time", "latitude", "longitude"), data)},
        coords={"time": time, "latitude": lat, "longitude": lon},
    ).to_netcdf(path)
    return path


def test_cut_years_converts_and_saves_per_year(tmp_path):
    raw = _eobs_file(tmp_path / "tx.nc", "tx", 10.0)
    assert eobs.cut_years(raw, "tx", tmp_path, years=range(1985, 1987)) == [1985, 1986]
    request = download.Request("e-obs", "", "tx", "tasmax", "day", "nw_europe", 1985, 1986)
    saved = xr.open_dataset(download.year_path(tmp_path, request, 1986))
    assert saved.tasmax.dims == ("time", "lat", "lon") and saved.tasmax.sizes["time"] == 365
    assert abs(float(saved.tasmax.isel(time=0, lat=0, lon=0)) - 283.15) < 1e-3
    assert saved.tasmax.attrs["units"] == "K"
    assert float(saved.lon.min()) >= -20 and float(saved.lat.max()) <= 65
    saved.close()
    assert eobs.cut_years(raw, "tx", tmp_path, years=range(1985, 1987)) == []  # resumable


def test_precipitation_is_kept_in_mm_per_day(tmp_path):
    raw = _eobs_file(tmp_path / "rr.nc", "rr", 2.5)
    eobs.cut_years(raw, "rr", tmp_path, years=range(1985, 1986))
    request = download.Request("e-obs", "", "rr", "pr", "day", "nw_europe", 1985, 1985)
    saved = xr.open_dataset(download.year_path(tmp_path, request, 1985))
    assert float(saved.pr.max()) == 2.5 and saved.pr.attrs["units"] == "mm/day"
    saved.close()
