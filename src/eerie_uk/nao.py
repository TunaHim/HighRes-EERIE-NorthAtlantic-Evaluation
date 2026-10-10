"""Winter North Atlantic Oscillation from monthly sea-level pressure.

Method (docs/methods.md, section 3): monthly anomalies from the monthly
climatology, winter (DJF) means, sqrt(cos latitude) weighting, leading EOF,
sign fixed so a positive NAO has low pressure near Iceland and high pressure
near the Azores, index = leading principal component in standard deviations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
from scipy import stats

from . import climatology as clim

# Reference points for the sign convention and the station-style index.
ICELAND = {"lat": 65.0, "lon": -20.0}
AZORES = {"lat": 38.0, "lon": -25.0}


def monthly_anomalies(psl: xr.DataArray, base=(1950, 2014)) -> xr.DataArray:
    """Remove the mean of each calendar month over the base period."""
    reference = clim.period(psl, *base).groupby("time.month").mean("time")
    return (psl.groupby("time.month") - reference).drop_vars("month")


def winter_anomalies(psl: xr.DataArray, base=(1950, 2014)) -> xr.DataArray:
    """One pressure-anomaly map per winter (dimension ``year``, year of January)."""
    return clim.season_means(monthly_anomalies(psl, base), "DJF")


@dataclass
class Eof:
    """Leading mode of a set of winter anomaly maps.

    ``pattern`` is in the units of the data per one standard deviation of the
    index, so it reads directly as "hPa in a +1 SD NAO winter".
    """

    pattern: xr.DataArray  # (lat, lon)
    index: xr.DataArray  # (year), standard deviations
    explained: np.ndarray  # fraction of variance of the first modes
    vector: xr.DataArray  # unit-length weighted EOF, used for projections
    amplitude: float  # standard deviation of the unstandardised index


def _weights(field: xr.DataArray) -> xr.DataArray:
    return np.sqrt(np.cos(np.deg2rad(field.lat)))


def nao_sign(pattern: xr.DataArray) -> float:
    """+1 if the pattern already has the positive-NAO sign, else -1."""
    azores = float(pattern.sel(**AZORES, method="nearest"))
    iceland = float(pattern.sel(**ICELAND, method="nearest"))
    return 1.0 if azores - iceland >= 0 else -1.0


def leading_eof(winters: xr.DataArray, modes: int = 3) -> Eof:
    """Leading EOF of winter anomaly maps, with the NAO sign convention."""
    weighted = (winters * _weights(winters)).stack(cell=("lat", "lon"))
    matrix = weighted.transpose("year", "cell").values
    matrix = matrix - matrix.mean(axis=0)
    _, singular, rows = np.linalg.svd(matrix, full_matrices=False)
    explained = singular**2 / np.sum(singular**2)

    vector = xr.DataArray(rows[0], coords={"cell": weighted.cell}, dims="cell").unstack("cell")
    vector = vector * nao_sign(vector / _weights(winters))
    raw = project(winters, vector)
    amplitude = float(raw.std(ddof=1))
    index = raw / amplitude
    pattern = regress(winters, index)
    pattern.attrs = {"units": winters.attrs.get("units", "hPa"), "long_name": "anomaly per +1 SD of the index"}
    return Eof(pattern, index, explained[:modes], vector, amplitude)


def mode_vectors(winters: xr.DataArray, count: int = 3) -> list[xr.DataArray]:
    """The first ``count`` unit-length weighted EOFs (arbitrary sign)."""
    weighted = (winters * _weights(winters)).stack(cell=("lat", "lon"))
    matrix = weighted.transpose("year", "cell").values
    _, _, rows = np.linalg.svd(matrix - matrix.mean(axis=0), full_matrices=False)
    return [
        xr.DataArray(rows[k], coords={"cell": weighted.cell}, dims="cell").unstack("cell") for k in range(count)
    ]


def overlap(vector: xr.DataArray, reference: xr.DataArray) -> float:
    """|cosine| between two unit-length EOFs: 1 = same pattern, 0 = unrelated."""
    return abs(float((vector * reference).sum()))


def project(winters: xr.DataArray, vector: xr.DataArray) -> xr.DataArray:
    """Project anomaly maps onto a unit-length weighted EOF (same grid)."""
    centred = winters - winters.mean("year")
    return (centred * _weights(winters) * vector).sum(["lat", "lon"])


def project_map(field: xr.DataArray, vector: xr.DataArray) -> float:
    """Project a single map (for example a mean-state bias) onto an EOF."""
    return float((field * _weights(field) * vector).sum(["lat", "lon"]))


def centres(pattern: xr.DataArray) -> dict:
    """Location and strength of the northern and southern centres of action."""
    out = {}
    for name, point in (("north", pattern.where(pattern == pattern.min(), drop=True)),
                        ("south", pattern.where(pattern == pattern.max(), drop=True))):
        out[f"{name} lat"] = float(point.lat[0])
        out[f"{name} lon"] = float(point.lon[0])
        out[f"{name} hPa"] = float(point.values.ravel()[0])
    return out


def regress(field: xr.DataArray, index: xr.DataArray) -> xr.DataArray:
    """Least-squares slope of ``field`` on ``index`` at every grid point."""
    x = index - index.mean("year")
    y = field - field.mean("year")
    return (y * x).sum("year") / (x**2).sum("year")


def station_index(winters: xr.DataArray) -> xr.DataArray:
    """Station-style NAO: normalised Azores minus normalised Iceland pressure."""
    azores = winters.sel(**AZORES, method="nearest")
    iceland = winters.sel(**ICELAND, method="nearest")
    difference = azores / azores.std("year", ddof=1) - iceland / iceland.std("year", ddof=1)
    out = (difference - difference.mean("year")) / difference.std("year", ddof=1)
    return out.drop_vars(["lat", "lon"], errors="ignore")


def autocorrelation(series, lag: int = 1) -> float:
    """Correlation of a series with itself ``lag`` steps later."""
    values = np.asarray(series, dtype=float)
    return float(np.corrcoef(values[:-lag], values[lag:])[0, 1])


def trend(years, series, confidence: float = 0.95) -> dict:
    """Linear trend per decade with a confidence interval (ordinary least squares)."""
    years = np.asarray(years, dtype=float)
    fit = stats.linregress(years, np.asarray(series, dtype=float))
    half = stats.t.ppf(0.5 + confidence / 2, years.size - 2) * fit.stderr
    return {
        "trend per decade": fit.slope * 10,
        "low": (fit.slope - half) * 10,
        "high": (fit.slope + half) * 10,
        "p value": fit.pvalue,
    }


def north_spacing(explained, samples: int) -> np.ndarray:
    """Sampling error of each explained-variance fraction (North et al. 1982)."""
    return np.asarray(explained) * np.sqrt(2.0 / samples)
