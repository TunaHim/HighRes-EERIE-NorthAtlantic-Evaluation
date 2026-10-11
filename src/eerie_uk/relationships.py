"""Link between a winter index (the NAO) and winter fields (docs/methods.md, section 5).

Primary method: correlation and regression at every grid point, both series
linearly detrended, two-sided t-test, false-discovery-rate control across grid
points (Wilks 2016). Supporting method: composites of high-index minus
low-index winters with bootstrap confidence intervals.
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


def ensemble_difference(a: xr.DataArray, b: xr.DataArray, dim: str = "realization") -> xr.Dataset:
    """Mean of ``a`` minus mean of ``b`` across ensemble members, with a Welch t-test.

    The p value says whether the difference between the two experiments is
    large compared with the spread across members of each.
    """
    test = stats.ttest_ind(a.transpose(dim, ...).values, b.transpose(dim, ...).values, axis=0, equal_var=False)
    difference = a.mean(dim) - b.mean(dim)
    p = xr.DataArray(np.asarray(test.pvalue), coords=difference.coords, dims=difference.dims)
    return xr.Dataset({"difference": difference, "p": p})