import numpy as np
import pandas as pd
import pytest
import xarray as xr

from eerie_uk import nao


def _dipole():
    """A north-south pressure see-saw centred on Iceland and the Azores."""
    lat = np.arange(20.0, 81.0, 2.0)
    lon = np.arange(-90.0, 41.0, 2.0)
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    south = np.exp(-(((yy - 38) / 12) ** 2) - ((xx + 25) / 30) ** 2)
    north = np.exp(-(((yy - 65) / 10) ** 2) - ((xx + 20) / 30) ** 2)
    return xr.DataArray(south - north, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"))


def _winters(sign=1.0, years=60, noise=0.2, seed=0):
    rng = np.random.default_rng(seed)
    pattern = _dipole()
    amplitude = rng.normal(0, 1, years)
    data = sign * 5.0 * amplitude[:, None, None] * pattern.values + noise * rng.normal(
        0, 1, (years,) + pattern.shape
    )
    field = xr.DataArray(
        data, coords={"year": np.arange(1951, 1951 + years), **pattern.coords}, dims=("year", "lat", "lon")
    )
    return field, amplitude * sign


def test_leading_eof_recovers_the_planted_mode():
    field, amplitude = _winters()
    eof = nao.leading_eof(field)
    assert eof.explained[0] > 0.8
    assert abs(np.corrcoef(eof.index.values, amplitude)[0, 1]) > 0.99
    assert float(eof.index.std(ddof=1)) == pytest.approx(1.0)
    # pattern is in data units per +1 SD: about 5 units at the Azores centre
    assert float(eof.pattern.sel(**nao.AZORES, method="nearest")) == pytest.approx(5.0 * amplitude.std(ddof=1), rel=0.1)


def test_sign_convention_does_not_depend_on_the_data_sign():
    for sign in (1.0, -1.0):
        field, _ = _winters(sign)
        eof = nao.leading_eof(field)
        assert float(eof.pattern.sel(**nao.AZORES, method="nearest")) > 0
        assert float(eof.pattern.sel(**nao.ICELAND, method="nearest")) < 0
        # a positive index winter has high pressure at the Azores
        azores = field.sel(**nao.AZORES, method="nearest")
        assert np.corrcoef(eof.index.values, azores.values)[0, 1] > 0.9


def test_projection_onto_another_dataset_pattern():
    reference, _ = _winters(seed=1)
    other, amplitude = _winters(seed=2)
    eof = nao.leading_eof(reference)
    projected = nao.project(other, eof.vector)
    assert np.corrcoef(projected.values, amplitude)[0, 1] > 0.99
    half, _ = _winters(seed=2)
    assert float(nao.project(half * 0.5, eof.vector).std()) == pytest.approx(0.5 * float(projected.std()))


def test_mode_overlap():
    field, _ = _winters(seed=3)
    other, _ = _winters(seed=4)
    first, second = nao.mode_vectors(field, 2)
    assert nao.overlap(first, first) == pytest.approx(1.0)
    assert nao.overlap(first, second) == pytest.approx(0.0, abs=1e-9)
    assert nao.overlap(first, nao.leading_eof(other).vector) > 0.99


def test_station_index_follows_the_eof_index():
    field, _ = _winters()
    station = nao.station_index(field)
    assert float(station.std(ddof=1)) == pytest.approx(1.0)
    assert np.corrcoef(station.values, nao.leading_eof(field).index.values)[0, 1] > 0.95


def test_monthly_anomalies_remove_the_seasonal_cycle():
    time = pd.date_range("1950-01-01", "1959-12-01", freq="MS")
    cycle = 10.0 * np.cos(2 * np.pi * (time.month.values - 1) / 12)
    da = xr.DataArray(
        cycle[:, None, None] + np.zeros((time.size, 2, 2)),
        coords={"time": time, "lat": [40.0, 60.0], "lon": [-20.0, 0.0]},
        dims=("time", "lat", "lon"),
    )
    assert float(abs(nao.monthly_anomalies(da, (1950, 1959))).max()) < 1e-9
    winters = nao.winter_anomalies(da, (1950, 1959))
    assert list(winters.year.values) == list(range(1951, 1960))


def test_autocorrelation_trend_and_north():
    assert nao.autocorrelation([1, 2, 3, 4, 5, 6]) == pytest.approx(1.0)
    assert nao.autocorrelation([1, -1, 1, -1, 1, -1]) == pytest.approx(-1.0)
    result = nao.trend(np.arange(1950, 2015), 0.02 * np.arange(65))
    assert result["trend per decade"] == pytest.approx(0.2)
    assert result["low"] <= 0.2 + 1e-9 and result["high"] >= 0.2 - 1e-9
    assert nao.north_spacing([0.5], 50)[0] == pytest.approx(0.1)
