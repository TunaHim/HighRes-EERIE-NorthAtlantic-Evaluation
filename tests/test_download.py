import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk import download as dl
from eerie_uk import regions


def _global(units, name="pr", start="2000-01-01", periods=730, flat=False):
    time = pd.date_range(start, periods=periods, freq="D")
    lat = np.arange(-90.0, 90.1, 1.0)
    lon = np.arange(0.0, 360.0, 1.0)
    data = np.ones((time.size, lat.size, lon.size)) * np.arange(time.size)[:, None, None]
    da = xr.DataArray(
        data, coords={"time": time, "lat": lat, "lon": lon}, dims=("time", "lat", "lon"),
        name=name, attrs={"units": units},
    )
    if flat:
        da = da.stack(value=("lat", "lon")).reset_index("value")
    return da.to_dataset()


REQUEST = dl.Request("fake", "fake.dataset", "pr", "pr", "day", "uk_ireland", 2000, 2001)


def test_convert_units_precipitation_to_mm_per_day():
    one = xr.DataArray([1.0], attrs={"units": "kg m-2 s-1"})
    assert float(dl.convert_units(one, "pr")[0]) == 86400.0
    one.attrs["units"] = "m s**-1"
    assert float(dl.convert_units(one, "pr")[0]) == 86400.0 * 1000.0
    one.attrs["units"] = "m"
    out = dl.convert_units(one, "pr")
    assert float(out[0]) == 1000.0
    assert out.attrs["units"] == "mm/day" and out.attrs["original_units"] == "m"


def test_convert_units_pressure_and_temperature():
    psl = dl.convert_units(xr.DataArray([101325.0], attrs={"units": "Pa"}), "psl")
    assert float(psl[0]) == pytest.approx(1013.25) and psl.attrs["units"] == "hPa"
    tas = xr.DataArray([280.0], attrs={"units": "K"})
    assert dl.convert_units(tas, "tasmax") is tas


def test_convert_units_refuses_unknown_units():
    with pytest.raises(ValueError):
        dl.convert_units(xr.DataArray([1.0], attrs={"units": "furlongs"}), "pr")
    with pytest.raises(ValueError):
        dl.convert_units(xr.DataArray([1.0], attrs={"units": "degC"}), "tas")


def test_year_path_and_pending_years(tmp_path):
    path = dl.year_path(tmp_path, REQUEST, 2000)
    assert path == tmp_path / "fake" / "day" / "pr_uk_ireland_2000.nc"
    assert dl.pending_years(tmp_path, REQUEST) == [2000, 2001]
    path.parent.mkdir(parents=True)
    path.touch()
    assert dl.pending_years(tmp_path, REQUEST) == [2001]


@pytest.mark.parametrize("flat", [False, True])
def test_run_writes_one_file_per_year_and_resumes(tmp_path, flat):
    calls = []

    def opener(dataset_id):
        calls.append(dataset_id)
        return _global("kg m-2 s-1", flat=flat)

    assert dl.run(REQUEST, tmp_path, opener) == []
    saved = xr.open_dataset(dl.year_path(tmp_path, REQUEST, 2001))
    assert saved.pr.dims == ("time", "lat", "lon")
    assert saved.pr.sizes == {"time": 364, "lat": 13, "lon": 14}
    assert saved.pr.dtype == "float32" and saved.pr.attrs["units"] == "mm/day"
    assert float(saved.lon.min()) == -11.0 and float(saved.lat.max()) == 61.0
    assert float(saved.pr.isel(time=0, lat=0, lon=0)) == 366 * 86400.0
    saved.close()

    assert len(calls) == 2
    assert dl.run(REQUEST, tmp_path, opener) == []  # nothing left to do
    assert len(calls) == 2


def test_run_reports_failed_years_and_leaves_no_partial_file(tmp_path):
    def opener(dataset_id):
        raise OSError("server down")

    assert dl.run(REQUEST, tmp_path, opener, retries=2, pause=0) == [2000, 2001]
    assert not list(tmp_path.rglob("*.nc")) and not list(tmp_path.rglob("*.part"))


def test_coarsen_block_averages_before_saving():
    request = dl.Request("fake", "fake.dataset", "pr", "pr", "day", "north_atlantic", 2000, 2000, coarsen=4)
    out = dl.fetch_year(request, 2000, lambda dataset_id: _global("kg m-2 s-1"))
    assert out.sizes["lat"] == 61 // 4 and out.sizes["lon"] == 131 // 4
    assert float(out.lat[0]) == pytest.approx(21.5)  # mean of 20, 21, 22, 23


def test_measure_reports_speed_size_and_failures(tmp_path):
    row = dl.measure(REQUEST, "2000-01-01", "2000-01-10", tmp_path, lambda d: _global("kg m-2 s-1"))
    assert row["ok"] and row["steps"] == 10 and row["grid"] == "13 x 14"
    assert row["units"] == "mm/day" and row["server_units"] == "kg m-2 s-1"
    assert row["mb_per_step"] > 0 and row["missing"] == 0

    def broken(dataset_id):
        raise OSError("server down")

    bad = dl.measure(REQUEST, "2000-01-01", "2000-01-10", tmp_path, broken)
    assert not bad["ok"] and "server down" in bad["error"]


def test_estimate_scales_with_period():
    cost = dl.estimate(REQUEST, seconds_per_step=1.0, mb_per_step=0.5)
    assert cost["steps"] == 730
    assert cost["hours"] == pytest.approx(730.5 / 3600) and cost["gb"] == pytest.approx(0.36525)


def test_build_plan_is_consistent():
    plan = dl.build_plan()
    assert len({(r.source, r.frequency, r.variable, r.box) for r in plan}) == len(plan)
    assert all(r.box in regions.BOXES and r.start_year <= r.end_year for r in plan)
    daily = [r for r in plan if r.frequency == "day"]
    assert {r.variable for r in daily} == {"pr", "tasmax"}
    assert {(r.start_year, r.end_year) for r in daily} == {(1985, 2014)}
    assert plan.index(daily[0]) > max(i for i, r in enumerate(plan) if r.frequency == "mon")


def test_cells_to_regular_recovers_a_linear_field():
    # reduced grid: each latitude row has its own number of longitudes
    lats, lons = [], []
    for lat, n in ((48.1, 40), (49.3, 36), (50.6, 30), (51.9, 24), (53.2, 20)):
        row = np.linspace(-13.0, 4.0, n)
        lats += [lat] * n
        lons += list(row)
    lats, lons = np.array(lats), np.array(lons)
    field = xr.DataArray(
        (2.0 * lons + 3.0 * lats)[None, :],
        dims=("time", "cell"),
        coords={"time": [0], "lat": ("cell", lats), "lon": ("cell", lons)},
    )
    assert regions.is_flat(field) and not regions.is_regular_flat(field)
    out = regions.cells_to_regular(field, (-11.0, 2.5, 49.5, 52.5))
    assert out.dims == ("time", "lat", "lon")
    expected = 2.0 * out.lon + 3.0 * out.lat
    np.testing.assert_allclose(out.isel(time=0).values, expected.transpose("lat", "lon").values, atol=1e-9)


def test_select_cells_pads_the_box():
    ds = _global("K", name="tas", periods=1, flat=True)
    tight = regions.select_cells(ds, "uk_ireland")
    padded = regions.select_cells(ds, "uk_ireland", pad=1.0)
    assert padded.sizes["value"] > tight.sizes["value"]
    assert float(padded.lon.min()) == -12.0


def test_extension_plan_is_consistent():
    plan = dl.build_extension_plan()
    assert all(r.frequency == "day" and (r.start_year, r.end_year) == (1985, 2014) for r in plan)
    assert {r.source for r in plan if r.variable == "pr"} == {"ifs-amip-tco1279.hist", "ifs-amip-tco399.hist"}
    assert all(r.box == "north_atlantic" and r.coarsen == 4 for r in plan if r.variable == "psl")
    assert not {(r.source, r.frequency, r.variable, r.box) for r in plan} & {
        (r.source, r.frequency, r.variable, r.box) for r in dl.build_plan()
    }


def test_months_and_members_limit_a_request():
    plan = {r.source: r for r in dl.build_extension_plan() if r.variable == "pr"}
    assert plan["ifs-amip-tco399.hist"].months == (12, 1, 2) and plan["ifs-amip-tco399.hist"].members == 3
    assert plan["ifs-amip-tco1279.hist"].months is None

    def opener(dataset_id):
        return xr.concat([_global("kg m-2 s-1", periods=366)] * 5, "realization").assign_coords(realization=range(5))

    request = dl.Request("fake", "fake", "pr", "pr", "day", "uk_ireland", 2000, 2000, months=(12, 1, 2), members=3)
    out = dl.fetch_year(request, 2000, opener)
    assert out.sizes["realization"] == 3
    assert set(out.time.dt.month.values) == {12, 1, 2} and out.sizes["time"] == 31 + 29 + 31
