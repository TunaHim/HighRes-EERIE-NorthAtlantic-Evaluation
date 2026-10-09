"""Figure helpers. Notebooks call these; they hold no plotting code themselves."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
EMPTY = "#f0efec"
# Single-hue ramp, light to dark, for magnitudes.
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "eerie_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)


def plot_availability(inventory, targets, title="", ax=None):
    """Grid of runs (rows) against target fields (columns).

    A filled cell means the field is served; the period is written in it.
    """
    labels = [
        f"{r.model}  {r.experiment}  {r.member}  {r.grid}" for r in inventory.itertuples()
    ]
    n_rows, n_cols = len(inventory), len(targets)
    if ax is None:
        fig, ax = plt.subplots(figsize=(9.5, 0.36 * n_rows + 1.4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for i, (_, row) in enumerate(inventory.iterrows()):
        for j, target in enumerate(targets):
            period = row[target]
            ax.add_patch(
                plt.Rectangle(
                    (j + 0.04, i + 0.08), 0.92, 0.84, color=BLUE if period else EMPTY, lw=0
                )
            )
            ax.text(
                j + 0.5,
                i + 0.5,
                period or "–",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if period else MUTED,
            )
    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)
    ax.set_xticks(np.arange(n_cols) + 0.5, targets)
    ax.set_yticks(np.arange(n_rows) + 0.5, labels)
    ax.xaxis.tick_top()
    ax.tick_params(length=0, labelsize=9, colors=INK_SECONDARY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, pad=22)
    return ax


def plot_field_map(field, title="", units="", ax=None, lon="lon", lat="lat"):
    """Map of a 2-D lon/lat field. Draws coastlines when cartopy is installed."""
    try:
        import cartopy.crs as ccrs

        projection = ccrs.PlateCarree()
    except ImportError:
        projection = None

    if ax is None:
        kwargs = {"projection": projection} if projection is not None else {}
        fig, ax = plt.subplots(figsize=(6.4, 4.6), facecolor=SURFACE, subplot_kw=kwargs)
    extra = {"transform": projection} if projection is not None else {}
    mesh = ax.pcolormesh(
        field[lon], field[lat], field.transpose(lat, lon), cmap=SEQUENTIAL, shading="auto", **extra
    )
    if projection is not None:
        ax.coastlines(resolution="50m", color=INK, linewidth=0.6)
        grid = ax.gridlines(draw_labels=True, color=GRID, linewidth=0.5)
        grid.top_labels = grid.right_labels = False
        grid.xlabel_style = grid.ylabel_style = {"size": 8, "color": MUTED}
    else:
        _style(ax)
        ax.set_xlabel("longitude (°E)", color=INK_SECONDARY, fontsize=9)
        ax.set_ylabel("latitude (°N)", color=INK_SECONDARY, fontsize=9)
    bar = ax.figure.colorbar(mesh, ax=ax, shrink=0.8, pad=0.03)
    bar.set_label(units, color=INK_SECONDARY, fontsize=9)
    bar.ax.tick_params(labelsize=8, colors=MUTED)
    bar.outline.set_visible(False)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    return ax


CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
# Two hues around a neutral grey midpoint, for differences.
DIVERGING = LinearSegmentedColormap.from_list(
    "eerie_diverging", ["#104281", "#3987e5", "#9ec5f4", "#f0efec", "#f4b59b", "#eb6834", "#9c3a12"]
)
# One fixed colour per data source, everywhere. Observations are dark grey.
SOURCE_COLOURS = {
    "era5": "#52514e",
    "e-obs": "#898781",
    "icon-esm-er": "#2a78d6",
    "ifs-fesom2-sr": "#eb6834",
}
SOURCE_LABELS = {
    "era5": "ERA5",
    "e-obs": "E-OBS",
    "icon-esm-er": "ICON-ESM-ER",
    "ifs-fesom2-sr": "IFS-FESOM2-SR",
}


def plot_line_panels(panels, ylabel="", xlabel="", title="", xticks=None, columns=3, sharey=False):
    """Small multiples of line charts, one line per data source.

    ``panels`` maps a panel title to ``{source: (x, y)}``. Colours follow the
    source, the same in every figure, and one legend serves all panels.
    """
    names = list(panels)
    columns = min(columns, len(names))
    rows = int(np.ceil(len(names) / columns))
    fig, axes = plt.subplots(
        rows, columns, figsize=(4.3 * columns, 3.0 * rows + 0.6), facecolor=SURFACE, squeeze=False, sharey=sharey
    )
    handles = {}
    for ax, name in zip(axes.flat, names):
        _style(ax)
        for source, (x, y) in panels[name].items():
            (line,) = ax.plot(
                x, y, color=SOURCE_COLOURS.get(source, MUTED), linewidth=2, label=SOURCE_LABELS.get(source, source)
            )
            handles[line.get_label()] = line
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.set_title(name, loc="left", fontsize=9, color=INK_SECONDARY)
        if xticks is not None:
            ax.set_xticks(*xticks)
        ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=9)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    fig.legend(
        handles.values(), handles.keys(), loc="lower center", ncol=len(handles), frameon=False,
        fontsize=9, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.5, -0.02),
    )
    if title:
        fig.suptitle(title, x=0.02, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    return axes


def plot_histogram_panels(panels, xlabel="", title="", bins=30, columns=3):
    """Small multiples of distributions, drawn as outlines so sources overlap legibly.

    ``panels`` maps a panel title to ``{source: 1-D values}``.
    """
    curves = {}
    for name, sources in panels.items():
        everything = np.concatenate([np.asarray(v).ravel() for v in sources.values()])
        edges = np.linspace(np.nanmin(everything), np.nanmax(everything), bins + 1)
        centres = 0.5 * (edges[:-1] + edges[1:])
        curves[name] = {
            source: (centres, np.histogram(np.asarray(v).ravel(), edges, density=True)[0])
            for source, v in sources.items()
        }
    return plot_line_panels(curves, ylabel="relative frequency", xlabel=xlabel, title=title, columns=columns)


def plot_boxes(boxes, labels=None, extent=None, title="", ax=None):
    """Outline named lon/lat boxes on a map, one colour per box, with a legend.

    ``boxes`` maps a name to (lon_min, lon_max, lat_min, lat_max).
    """
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    labels = labels or {}
    projection = ccrs.PlateCarree()
    if ax is None:
        fig, ax = plt.subplots(figsize=(9.0, 5.2), facecolor=SURFACE, subplot_kw={"projection": projection})
    ax.add_feature(cfeature.LAND, facecolor=EMPTY)
    ax.coastlines(resolution="50m", color=MUTED, linewidth=0.5)
    for (name, (lon_min, lon_max, lat_min, lat_max)), colour in zip(boxes.items(), CATEGORICAL):
        text = f"{labels.get(name, name)}: {_degrees(lon_min, 'WE')}–{_degrees(lon_max, 'WE')}, {_degrees(lat_min, 'SN')}–{_degrees(lat_max, 'SN')}"
        ax.add_patch(
            plt.Rectangle(
                (lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
                fill=False, edgecolor=colour, linewidth=2, transform=projection, label=text, zorder=3,
            )
        )
    if extent is None:
        lon_lo = min(b[0] for b in boxes.values()) - 6
        lon_hi = max(b[1] for b in boxes.values()) + 6
        lat_lo = min(b[2] for b in boxes.values()) - 4
        lat_hi = max(b[3] for b in boxes.values()) + 4
        extent = (lon_lo, lon_hi, max(lat_lo, -89), min(lat_hi, 89))
    ax.set_extent(extent, crs=projection)
    grid = ax.gridlines(draw_labels=True, color=GRID, linewidth=0.5)
    grid.top_labels = grid.right_labels = False
    grid.xlabel_style = grid.ylabel_style = {"size": 8, "color": MUTED}
    ax.legend(loc="lower left", fontsize=8, frameon=True, facecolor=SURFACE, edgecolor=GRID, labelcolor=INK_SECONDARY)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    return ax


def _degrees(value, letters):
    return f"{abs(value):g}°{letters[0] if value < 0 else letters[1]}"


def plot_field_panels(fields, units="", title="", columns=3, diverging=False):
    """Maps of several 2-D fields side by side on one shared colour scale.

    ``fields`` maps a panel label to a lat/lon DataArray. ``diverging=True``
    is for differences: the scale is centred on zero, grey in the middle.
    """
    import cartopy.crs as ccrs

    projection = ccrs.PlateCarree()
    names = list(fields)
    columns = min(columns, len(names))
    rows = int(np.ceil(len(names) / columns))
    first = fields[names[0]]
    aspect = (float(first.lat.max() - first.lat.min()) or 1.0) / (float(first.lon.max() - first.lon.min()) or 1.0)
    width = 4.2
    fig, axes = plt.subplots(
        rows, columns, figsize=(width * columns, width * aspect * 1.25 * rows + 1.0),
        facecolor=SURFACE, subplot_kw={"projection": projection}, squeeze=False,
    )
    low = min(float(f.min()) for f in fields.values())
    high = max(float(f.max()) for f in fields.values())
    cmap = SEQUENTIAL
    if diverging:
        # robust limit so one extreme cell does not wash out the map
        high = max(float(np.nanpercentile(np.abs(f.values), 99)) for f in fields.values())
        low, cmap = -high, DIVERGING
    mesh = None
    for ax, name in zip(axes.flat, names):
        field = fields[name]
        mesh = ax.pcolormesh(
            field.lon, field.lat, field.transpose("lat", "lon"), cmap=cmap, vmin=low, vmax=high,
            shading="auto", transform=projection,
        )
        ax.coastlines(resolution="50m", color=INK, linewidth=0.5)
        ax.set_title(name, loc="left", fontsize=9, color=INK_SECONDARY)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    bar = fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.6, pad=0.06, aspect=40)
    bar.set_label(units, color=INK_SECONDARY, fontsize=9)
    bar.ax.tick_params(labelsize=8, colors=MUTED)
    bar.outline.set_visible(False)
    if title:
        fig.suptitle(title, x=0.02, ha="left", fontsize=11, color=INK)
    return axes


def plot_bars(values, xlabel="", title="", ax=None):
    """Horizontal bars for a small labelled series (label -> value), value written at the bar end."""
    names = list(values)
    numbers = [values[n] for n in names]
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 0.34 * len(names) + 1.0), facecolor=SURFACE)
    _style(ax)
    ax.barh(names, numbers, color=BLUE, height=0.62)
    ax.invert_yaxis()
    for i, number in enumerate(numbers):
        ax.text(number, i, f"  {number:.1f}", va="center", fontsize=8, color=INK_SECONDARY)
    ax.set_xlim(0, max(numbers) * 1.15 if numbers else 1)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    return ax


def plot_series(series, title="", ylabel="", ax=None, time="time"):
    """Single time series as a thin line."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, 3.0), facecolor=SURFACE)
    _style(ax)
    ax.plot(series[time].values, series.values, color=BLUE, linewidth=2)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=9)
    ax.figure.autofmt_xdate()
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    return ax
