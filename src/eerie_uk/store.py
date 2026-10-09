"""Read the downloaded cut-outs back from ``data/``.

Files are ``data/<source>/<mon|day>/<variable>_<box>_<year>.nc``. Every source
comes back with the same time convention, so sources can be compared directly:
monthly data are stamped on the first day of their month, daily data at 00:00
of their day. Temperatures are converted from K to degrees Celsius on loading.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import xarray as xr

from .download import DATA_ROOT


def files(source, frequency, variable, box, root=DATA_ROOT) -> dict[int, Path]:
    """Saved files of one field, keyed by year."""
    folder = Path(root) / source / frequency
    found = {}
    for path in sorted(folder.glob(f"{variable}_{box}_*.nc")):
        found[int(path.stem.rsplit("_", 1)[1])] = path
    return found


def available(root=DATA_ROOT) -> pd.DataFrame:
    """One row per saved field: years present, gaps, size on disk."""
    rows = []
    for folder in sorted(Path(root).glob("*/*")):
        if folder.name not in ("mon", "day") or folder.parent.name in ("sample", "raw"):
            continue
        groups = {}
        for path in folder.glob("*.nc"):
            stem, year = path.stem.rsplit("_", 1)
            groups.setdefault(stem, []).append((int(year), path.stat().st_size))
        for stem, items in sorted(groups.items()):
            variable, box = stem.split("_", 1)
            years = sorted(y for y, _ in items)
            gaps = sorted(set(range(years[0], years[-1] + 1)) - set(years))
            rows.append(
                {
                    "source": folder.parent.name,
                    "frequency": folder.name,
                    "variable": variable,
                    "box": box,
                    "first": years[0],
                    "last": years[-1],
                    "years": len(years),
                    "gaps": ", ".join(map(str, gaps)),
                    "MB": sum(size for _, size in items) / 1e6,
                }
            )
    return pd.DataFrame(rows)


def standard_time(time: xr.DataArray, frequency: str) -> pd.DatetimeIndex:
    """Common time stamps: first of the month (monthly) or midnight (daily).

    Sources stamp a month at its end (ICON), middle (IFS) or start (ERA5); the
    calendar month of the stamp is the month the value describes in all three.
    """
    index = pd.DatetimeIndex(time.values)
    if frequency == "mon":
        return pd.to_datetime({"year": index.year, "month": index.month, "day": 1})
    return index.normalize()


def load(source, frequency, variable, box, years=None, root=DATA_ROOT) -> xr.DataArray:
    """One field over all saved years (or the given ones), in memory."""
    found = files(source, frequency, variable, box, root)
    if years is not None:
        found = {y: p for y, p in found.items() if y in set(years)}
    if not found:
        raise FileNotFoundError(f"no files for {source} {frequency} {variable} {box} under {root}")
    parts = []
    for year in sorted(found):
        with xr.open_dataset(found[year]) as ds:
            parts.append(ds[variable].load())
    out = xr.concat(parts, "time")
    out = out.assign_coords(time=pd.DatetimeIndex(standard_time(out.time, frequency)))
    if out.attrs.get("units") == "K":  # files are in K; analysis and figures use Celsius
        attrs = {**out.attrs, "units": "°C"}
        out = out - 273.15
        out.attrs = attrs
    out.attrs["source"] = source
    return out
