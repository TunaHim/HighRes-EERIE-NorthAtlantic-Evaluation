"""Link between a winter index (the NAO) and winter fields (docs/methods.md, section 5).

Primary method: correlation and regression at every grid point, both series
linearly detrended, two-sided t-test, false-discovery-rate control across grid
points (Wilks 2016). Supporting methods: composites of high-index minus
low-index winters with bootstrap confidence intervals; bootstrap, leave-one-out
and effective-sample-size checks on regional correlations; and the part of a
mean bias that a shifted mean circulation alone would produce.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
from scipy import stats

ALPHA_FDR = 0.10  # Wilks (2016): about twice the 5% test level for spatially correlated fields


def detrend(da: xr.DataArray, dim: str = "year") -> xr.DataArray:
    """Remove the least-squares straight line along ``dim`` (keeps NaN cells NaN)."""
    x = da[dim] - da[dim].mean()
    slope = (x * (da - da.mean(dim))).sum(dim) / (x**2).sum()
    return da - da.mean(dim) - slope * x


def align(field: xr.DataArray, index: xr.DataArray):
    """Keep the years present in both, in the same order."""
    years = np.intersect1d(field.year.values, index.year.values)
    return field.sel(year=years), index.sel(year=years)


def correlate(field: xr.DataArray, index: xr.DataArray, detrended: bool = True) -> xr.Dataset:
    """Correlation, regression slope and p value of ``field`` on ``index`` per grid point.

    ``slope`` is the change in the field per one unit of the index.
    """
    field, index = align(field, index)
    if detrended:
        field, index = detrend(field), detrend(index)
    n = field.sizes["year"]
    x = index - index.mean("year")
    y = field - field.mean("year")
    sxx = float((x**2).sum())
    r = (x * y).sum("year") / np.sqrt(sxx * (y**2).sum("year"))
    slope = (x * y).sum("year") / sxx
    dof = n - 2 - (1 if detrended else 0)  # one more degree of freedom is spent on the trend
    t = r * np.sqrt(dof / (1.0 - r**2))
    p = xr.apply_ufunc(lambda v: 2.0 * stats.t.sf(np.abs(v), dof), t)
    return xr.Dataset({"r": r, "slope": slope, "p": p}, attrs={"n": n, "dof": dof})


def fdr_mask(p: xr.DataArray, alpha: float = ALPHA_FDR) -> xr.DataArray:
    """Grid points that stay significant under false-discovery-rate control.

    Benjamini-Hochberg: sort the p values, find the largest k with
    p(k) <= alpha * k / N, and keep every point with p <= p(k).
    """
    values = p.values.ravel()
    valid = np.isfinite(values)
    ranked = np.sort(values[valid])
    limits = alpha * np.arange(1, ranked.size + 1) / ranked.size
    passing = np.flatnonzero(ranked <= limits)
    cutoff = ranked[passing[-1]] if passing.size else -1.0
    return (p <= cutoff) & p.notnull()


def composite(field: xr.DataArray, index: xr.DataArray, fraction: float = 1 / 3) -> xr.DataArray:
    """Mean of the field in the highest-index winters minus the lowest-index winters."""
    field, index = align(field, index)
    count = max(1, int(round(index.size * fraction)))
    order = np.argsort(index.values)
    return field.isel(year=order[-count:]).mean("year") - field.isel(year=order[:count]).mean("year")


def composite_interval(series, index, fraction: float = 1 / 3, draws: int = 5000, seed: int = 0) -> dict:
    """High-minus-low composite of a 1-D series with a bootstrap 95% interval.

    Winters are resampled with replacement within the high and the low group.
    """
    series = np.asarray(series, dtype=float)
    index = np.asarray(index, dtype=float)
    count = max(1, int(round(index.size * fraction)))
    order = np.argsort(index)
    low, high = series[order[:count]], series[order[-count:]]
    rng = np.random.default_rng(seed)
    samples = (
        rng.choice(high, (draws, count)).mean(axis=1) - rng.choice(low, (draws, count)).mean(axis=1)
    )
    return {
        "difference": float(high.mean() - low.mean()),
        "low": float(np.percentile(samples, 2.5)),
        "high": float(np.percentile(samples, 97.5)),
        "winters per group": count,
    }


def regress_series(series, index, detrended: bool = True) -> dict:
    """Correlation and slope of a 1-D series on an index, with a 95% interval on the slope."""
    y = np.asarray(series, dtype=float)
    x = np.asarray(index, dtype=float)
    if detrended:
        t = np.arange(x.size, dtype=float)
        y = y - np.polyval(np.polyfit(t, y, 1), t)
        x = x - np.polyval(np.polyfit(t, x, 1), t)
    fit = stats.linregress(x, y)
    dof = x.size - 2 - (1 if detrended else 0)
    half = stats.t.ppf(0.975, dof) * fit.stderr
    t_value = fit.rvalue * np.sqrt(dof / (1 - fit.rvalue**2))
    return {
        "r": float(fit.rvalue),
        "slope": float(fit.slope),
        "low": float(fit.slope - half),
        "high": float(fit.slope + half),
        "p": float(2 * stats.t.sf(abs(t_value), dof)),
    }


def _detrended(values) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    t = np.arange(values.size, dtype=float)
    return values - np.polyval(np.polyfit(t, values, 1), t)


def lag1(values) -> float:
    """Lag-1 autocorrelation of a 1-D series."""
    values = np.asarray(values, dtype=float) - np.mean(values)
    return float(np.sum(values[:-1] * values[1:]) / np.sum(values**2))


def effective_sample_size(x, y) -> float:
    """Number of independent winters behind a correlation of two autocorrelated series.

    Bretherton et al. (1999): n (1 - a b) / (1 + a b), with a and b the lag-1
    autocorrelations. Only positive memory reduces the sample; it is never
    allowed to exceed n.
    """
    product = lag1(x) * lag1(y)
    n = len(x)
    return float(min(n, n * (1 - product) / (1 + product)))


def correlation_uncertainty(series, index, years=None, detrended: bool = True,
                            draws: int = 5000, seed: int = 0) -> dict:
    """How certain is one correlation between a winter series and the NAO?

    Returns the correlation with
    - a bootstrap 95% interval (winters resampled in pairs, with replacement),
    - the smallest and largest correlation when any single winter is left out,
      and the winter whose removal changes it most,
    - the effective sample size after year-to-year memory, and the p value
      that uses it (one degree of freedom less if the series were detrended).
    """
    y = np.asarray(series, dtype=float)
    x = np.asarray(index, dtype=float)
    years = np.arange(x.size) if years is None else np.asarray(years)
    if detrended:
        x, y = _detrended(x), _detrended(y)
    n = x.size
    r = float(np.corrcoef(x, y)[0, 1])

    rng = np.random.default_rng(seed)
    picks = rng.integers(0, n, (draws, n))
    xs, ys = x[picks], y[picks]
    xs = xs - xs.mean(axis=1, keepdims=True)
    ys = ys - ys.mean(axis=1, keepdims=True)
    boot = (xs * ys).sum(axis=1) / np.sqrt((xs**2).sum(axis=1) * (ys**2).sum(axis=1))

    left_out = np.array([np.corrcoef(np.delete(x, k), np.delete(y, k))[0, 1] for k in range(n)])
    most = int(np.argmax(np.abs(left_out - r)))

    n_eff = effective_sample_size(x, y)
    dof = max(n_eff - 2 - (1 if detrended else 0), 1.0)
    t_value = r * np.sqrt(dof / (1 - r**2))
    return {
        "r": r,
        "low": float(np.percentile(boot, 2.5)),
        "high": float(np.percentile(boot, 97.5)),
        "r without one winter, min": float(left_out.min()),
        "r without one winter, max": float(left_out.max()),
        "most influential winter": int(years[most]),
        "r without it": float(left_out[most]),
        "lag-1 NAO": lag1(x),
        "lag-1 series": lag1(y),
        "effective winters": n_eff,
        "p (effective)": float(2 * stats.t.sf(abs(t_value), dof)),
    }


def correlation_difference(r1: float, n1: float, r2: float, n2: float) -> float:
    """Two-sided p value for the difference of two correlations from independent samples (Fisher z)."""
    z = (np.arctanh(r1) - np.arctanh(r2)) / np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    return float(2 * stats.norm.sf(abs(z)))


def circulation_part(slope: xr.DataArray, offset: float) -> xr.DataArray:
    """Part of a mean bias that a shifted mean circulation would produce on its own.

    ``slope`` is the observed change in a field per +1 SD of the NAO (from a
    reference), ``offset`` the model's mean circulation bias expressed in the
    same NAO units. The product is the bias expected if the model's only error
    were that its average winter sits ``offset`` SD along the NAO. It assumes a
    linear response, applied beyond the range of ordinary NAO winters when the
    offset is large, so it is a diagnostic of consistency, not an attribution.
    """
    return slope * offset


def ensemble_difference(a: xr.DataArray, b: xr.DataArray, dim: str = "realization") -> xr.Dataset:
    """Mean of ``a`` minus mean of ``b`` across ensemble members, with a Welch t-test.

    The p value says whether the difference between the two experiments is
    large compared with the spread across members of each.
    """
    test = stats.ttest_ind(a.transpose(dim, ...).values, b.transpose(dim, ...).values, axis=0, equal_var=False)
    difference = a.mean(dim) - b.mean(dim)
    p = xr.DataArray(np.asarray(test.pvalue), coords=difference.coords, dims=difference.dims)
    return xr.Dataset({"difference": difference, "p": p})