import numpy as np
import pytest
import xarray as xr

from eerie_uk import relationships as rel


def _setup(years=40, seed=0, trend=0.0):
    rng = np.random.default_rng(seed)
    year = np.arange(1986, 1986 + years)
    index = xr.DataArray(rng.normal(0, 1, years), coords={"year": year}, dims="year")
    lat = np.array([50.0, 55.0, 60.0])
    lon = np.array([-5.0, 0.0])
    slope = np.array([[2.0, 2.0], [0.0, 0.0], [-3.0, -3.0]])  # linked north and south, unrelated in the middle
    noise = rng.normal(0, 0.5, (years, 3, 2))
    data = index.values[:, None, None] * slope + noise + trend * (year - year[0])[:, None, None]
    field = xr.DataArray(data, coords={"year": year, "lat": lat, "lon": lon}, dims=("year", "lat", "lon"))
    return field, index


def test_correlate_recovers_slope_sign_and_significance():
    field, index = _setup()
    out = rel.correlate(field, index)
    assert float(out.slope.isel(lat=0, lon=0)) == pytest.approx(2.0, abs=0.3)
    assert float(out.slope.isel(lat=2, lon=0)) == pytest.approx(-3.0, abs=0.3)
    assert float(out.r.isel(lat=0, lon=0)) > 0.9 and float(out.r.isel(lat=2, lon=0)) < -0.9
    assert float(out.p.isel(lat=0, lon=0)) < 1e-6
    assert float(out.p.isel(lat=1, lon=0)) > 0.01
    assert out.attrs["dof"] == 40 - 3


def test_detrending_removes_a_spurious_common_trend():
    year = np.arange(1986, 2016)
    ramp = xr.DataArray((year - 1986) * 1.0, coords={"year": year}, dims="year")
    rng = np.random.default_rng(1)
    index = ramp * 0.1 + rng.normal(0, 1, 30)
    field = (ramp * 0.5 + rng.normal(0, 1, 30)).expand_dims(lat=[50.0], lon=[0.0]).transpose("year", "lat", "lon")
    raw = rel.correlate(field, index, detrended=False)
    clean = rel.correlate(field, index, detrended=True)
    assert abs(float(clean.r.squeeze())) < abs(float(raw.r.squeeze()))
    assert float(abs(rel.detrend(ramp)).max()) < 1e-9


def test_align_uses_common_years_only():
    field, index = _setup()
    out = rel.correlate(field.sel(year=slice(1990, 2020)), index.sel(year=slice(1986, 2010)))
    assert out.attrs["n"] == 21


def test_fdr_mask_is_stricter_than_the_plain_test():
    p = xr.DataArray(np.array([[0.001, 0.004, 0.03, 0.04], [0.2, 0.5, 0.8, np.nan]]), dims=("lat", "lon"))
    mask = rel.fdr_mask(p, alpha=0.05)
    # 7 valid tests: limits are 0.05*k/7 = .0071 .0143 .0214 ...; only the two smallest pass
    assert mask.values.tolist() == [[True, True, False, False], [False, False, False, False]]
    assert not rel.fdr_mask(xr.DataArray(np.array([0.5, 0.9]), dims="x")).any()


def test_composite_and_bootstrap_interval():
    field, index = _setup(years=30)
    difference = rel.composite(field, index)
    assert float(difference.isel(lat=0, lon=0)) > 2.0 and float(difference.isel(lat=2, lon=0)) < -3.0
    result = rel.composite_interval(field.isel(lat=0, lon=0).values, index.values)
    assert result["winters per group"] == 10
    assert result["low"] < result["difference"] < result["high"] and result["low"] > 0
    unrelated = rel.composite_interval(field.isel(lat=1, lon=0).values, index.values)
    assert unrelated["low"] < 0 < unrelated["high"]


def test_regress_series_matches_the_map_version():
    field, index = _setup()
    cell = rel.regress_series(field.isel(lat=0, lon=0).values, index.values)
    grid = rel.correlate(field, index)
    assert cell["r"] == pytest.approx(float(grid.r.isel(lat=0, lon=0)))
    assert cell["slope"] == pytest.approx(float(grid.slope.isel(lat=0, lon=0)))
    assert cell["p"] == pytest.approx(float(grid.p.isel(lat=0, lon=0)))
    assert cell["low"] < cell["slope"] < cell["high"]


def test_ensemble_difference_detects_a_shift_larger_than_the_spread():
    rng = np.random.default_rng(5)
    coords = {"realization": np.arange(10), "lat": [50.0, 60.0]}
    a = xr.DataArray(rng.normal(0, 1, (10, 2)), coords=coords, dims=("realization", "lat"))
    b = xr.DataArray(rng.normal(0, 1, (10, 2)), coords=coords, dims=("realization", "lat"))
    b[:, 1] -= 5.0  # a real shift at the second point only
    out = rel.ensemble_difference(a, b)
    assert float(out.difference.isel(lat=1)) == pytest.approx(5.0, abs=1.5)
    assert float(out.p.isel(lat=1)) < 0.001 and float(out.p.isel(lat=0)) > 0.05