import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk.regions import BOXES, area_mean, select_winter, subset_box


def _grid(lon, lat):
    data = np.arange(len(lat) * len(lon), dtype=float).reshape(len(lat), len(lon))
    return xr.DataArray(data, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"))


def test_subset_box_on_0_360_grid_straddles_greenwich():
    da = _grid(np.arange(0.0, 360.0, 1.0), np.arange(-90.0, 91.0, 1.0))
    out = subset_box(da, "uk_ireland")
    assert out.lon.values[0] == -11.0 and out.lon.values[-1] == 2.0
    assert np.all(np.diff(out.lon.values) > 0)
    assert out.lat.min() == 49.0 and out.lat.max() == 61.0
    # values travel with their coordinates
    assert float(out.sel(lon=-11.0, lat=50.0)) == float(da.sel(lon=349.0, lat=50.0))


def test_subset_box_on_minus180_grid_and_descending_lat():
    da = _grid(np.arange(-180.0, 180.0, 1.0), np.arange(90.0, -91.0, -1.0))
    out = subset_box(da, (-11.0, 2.5, 49.0, 61.0))
    assert out.sizes == {"lat": 13, "lon": 14}
    assert out.lat.values[0] == 61.0  # original order kept


def test_subset_box_on_flat_cell_grid_matches_regular_grid():
    regular = _grid(np.arange(0.0, 360.0, 1.0), np.arange(90.0, -91.0, -1.0))
    flat = regular.stack(value=("lat", "lon")).reset_index("value")
    out = subset_box(flat, "uk_ireland")
    expected = subset_box(regular, "uk_ireland").sortby("lat")
    assert out.dims == ("lat", "lon")
    np.testing.assert_array_equal(out.values, expected.values)
    np.testing.assert_array_equal(out.lon.values, expected.lon.values)


def test_subset_box_unknown_name():
    with pytest.raises(KeyError):
        subset_box(_grid(np.arange(0.0, 10.0), np.arange(0.0, 10.0)), "atlantis")


def test_boxes_are_well_formed():
    for lon_min, lon_max, lat_min, lat_max in BOXES.values():
        assert -180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90


def test_select_winter_is_dec_to_feb():
    time = pd.date_range("1979-01-01", "1980-12-31", freq="D")
    da = xr.DataArray(np.zeros(time.size), coords={"time": time}, dims="time")
    out = select_winter(da, 1980)
    assert str(out.time.values[0])[:10] == "1979-12-01"
    assert str(out.time.values[-1])[:10] == "1980-02-29"
    assert out.sizes["time"] == 31 + 31 + 29


def test_select_winter_360_day_calendar():
    time = xr.date_range("1979-01-01", periods=720, freq="D", calendar="360_day", use_cftime=True)
    da = xr.DataArray(np.zeros(720), coords={"time": time}, dims="time")
    assert select_winter(da, 1980).sizes["time"] == 90


def test_area_mean_weights_by_cos_lat():
    da = _grid(np.array([0.0, 1.0]), np.array([0.0, 60.0]))
    da[:] = [[1.0, 1.0], [4.0, 4.0]]
    assert float(area_mean(da)) == pytest.approx((1.0 * 1.0 + 4.0 * 0.5) / 1.5)
