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


def colour_of(source: str) -> str:
    """Colour of a data source; extra members ("model.r2") and control runs share the model's colour."""
    return SOURCE_COLOURS.get(source, SOURCE_COLOURS.get(source.split(".")[0], MUTED))


def label_of(source: str) -> str:
    """Readable name: "icon-esm-er.r2" -> "ICON-ESM-ER r2", "icon-esm-er" -> "ICON-ESM-ER r1"."""
    if source in SOURCE_LABELS and source not in ("icon-esm-er", "ifs-fesom2-sr"):
        return SOURCE_LABELS[source]
    base, _, tag = source.partition(".")
    if base in ("icon-esm-er", "ifs-fesom2-sr"):
        return f"{SOURCE_LABELS[base]} {tag or 'r1'}"
    return SOURCE_LABELS.get(source, source)


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)


def _lonlat_labels(ax, left=True, bottom=True):
    """Light longitude/latitude grid lines, labelled on the left and bottom edges only."""
    grid = ax.gridlines(draw_labels=True, color=GRID, linewidth=0.4, alpha=0.8)
    grid.top_labels = grid.right_labels = False
    grid.left_labels, grid.bottom_labels = left, bottom
    grid.xlabel_style = grid.ylabel_style = {"size": 7, "color": MUTED}
    return grid


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
    "e-obs": "#b5b3aa",
    "icon-esm-er": "#2a78d6",
    "ifs-fesom2-sr": "#eb6834",
    # paired atmosphere-only runs (notebook 07)
    "hist": "#1baf7a",
    "hist-c-0-a-lr20": "#eda100",
    "hist-c-lr20-a-0": "#e87ba4",
    # resolution pair (notebook 08)
    "ifs-amip-tco1279.hist": "#4a3aa7",
    "ifs-amip-tco399.hist": "#1baf7a",
    # HadGEM3-GC5 resolution ladder (notebook 12), light to dark with resolution
    "hadgem3-gc5e-ll": "#b8acf0",
    "hadgem3-gc5e-mm": "#7b6be0",
    "hadgem3-gc5e-hh": "#3d2b9e",
}
SOURCE_LABELS = {
    "era5": "ERA5",
    "e-obs": "E-OBS",
    "icon-esm-er": "ICON-ESM-ER",
    "ifs-fesom2-sr": "IFS-FESOM2-SR",
    "hist": "observed SST (hist)",
    "hist-c-0-a-lr20": "filtered SST anomalies (c-0-a-lr20)",
    "hist-c-lr20-a-0": "third variant (c-lr20-a-0)",
    "ifs-amip-tco1279.hist": "IFS 9 km",
    "ifs-amip-tco399.hist": "IFS 28 km",
    "hadgem3-gc5e-ll": "HadGEM3 LL (~135 km)",
    "hadgem3-gc5e-mm": "HadGEM3 MM (~60 km)",
    "hadgem3-gc5e-hh": "HadGEM3 HH (~20 km)",
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
        rows, columns, figsize=(max(4.3 * columns, 8.0), 3.0 * rows + 0.6), facecolor=SURFACE, squeeze=False, sharey=sharey
    )
    handles = {}
    for ax, name in zip(axes.flat, names):
        _style(ax)
        for source, (x, y) in panels[name].items():
            base = source.split("#")[0]  # "name#2" = member 2 of a source: same colour and label
            (line,) = ax.plot(
                x, y, color=SOURCE_COLOURS.get(base, MUTED), linewidth=2, label=SOURCE_LABELS.get(base, base)
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


def plot_scatter_panels(panels, xlabel="", ylabel="", title="", columns=4):
    """Small multiples of scatter plots with a least-squares line, one source per panel.

    ``panels`` maps a panel title to ``(source, x, y)``. The colour follows the source.
    """
    names = list(panels)
    columns = min(columns, len(names))
    rows = int(np.ceil(len(names) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(3.3 * columns, 3.1 * rows + 0.4), facecolor=SURFACE, squeeze=False)
    for ax, name in zip(axes.flat, names):
        source, x, y = panels[name]
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        colour = SOURCE_COLOURS.get(source, MUTED)
        _style(ax)
        ax.scatter(x, y, s=30, color=colour, edgecolors=SURFACE, linewidths=1.0, zorder=3)
        slope, intercept = np.polyfit(x, y, 1)
        line = np.array([x.min(), x.max()])
        ax.plot(line, slope * line + intercept, color=colour, linewidth=2)
        ax.axvline(0, color=AXIS, linewidth=0.8)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.set_title(name, loc="left", fontsize=9, color=INK_SECONDARY)
        ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=9)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    if title:
        fig.suptitle(title, x=0.02, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
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


def plot_field_panels(fields, units="", title="", columns=3, diverging=False, stipple=None, limit=None):
    """Maps of several 2-D fields side by side on one shared colour scale.

    ``fields`` maps a panel label to a lat/lon DataArray. ``diverging=True``
    is for differences: the scale is centred on zero, grey in the middle.
    `stipple` maps a panel label to a boolean lat/lon mask; dots are drawn
    where it is True (used to mark statistically significant grid points).
    `limit` fixes the colour range to +-limit (diverging) instead of the data.
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
        if limit is not None:
            high = limit
        low, cmap = -high, DIVERGING
    mesh = None
    for ax, name in zip(axes.flat, names):
        field = fields[name]
        mesh = ax.pcolormesh(
            field.lon, field.lat, field.transpose("lat", "lon"), cmap=cmap, vmin=low, vmax=high,
            shading="auto", transform=projection,
        )
        ax.coastlines(resolution="50m", color=INK, linewidth=0.5)
        k = names.index(name)
        _lonlat_labels(ax, left=(k % columns == 0), bottom=(k // columns == rows - 1 or k + columns >= len(names)))
        if stipple and name in stipple:
            marked = stipple[name].isel(lat=slice(1, None, 3), lon=slice(1, None, 3))
            yy, xx = np.meshgrid(marked.lat, marked.lon, indexing="ij")
            ax.scatter(xx[marked.values], yy[marked.values], s=1.6, color=INK, linewidths=0, transform=projection)
        ax.set_title(name, loc="left", fontsize=9, color=INK_SECONDARY)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    bar = fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.6, pad=0.09, aspect=40)
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


def plot_member_dots(groups, xlabel="", title="", reference=None, reference_label="", ax=None):
    """One row per experiment, one dot per ensemble member, a bar at the ensemble mean.

    ``groups`` maps an experiment key to a 1-D array of member values.
    ``reference`` draws a vertical line (for example the ERA5 value).
    """
    names = list(groups)
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.6, 0.75 * len(names) + 1.3), facecolor=SURFACE)
    _style(ax)
    for row, name in enumerate(names):
        values = np.asarray(groups[name], dtype=float)
        colour = colour_of(name)
        ax.scatter(values, np.full(values.size, row), s=42, color=colour, edgecolors=SURFACE, linewidths=1.0, zorder=3)
        ax.plot([values.mean()] * 2, [row - 0.3, row + 0.3], color=INK, linewidth=2, zorder=4)
        ax.text(values.max(), row + 0.32, f"mean {values.mean():.2f}", fontsize=8, color=INK_SECONDARY, ha="right")
    if reference is not None:
        ax.axvline(reference, color=SOURCE_COLOURS["era5"], linewidth=1.2, linestyle="--")
        ax.text(reference, -0.75, reference_label, fontsize=8, color=INK_SECONDARY, ha="center")
    ax.set_yticks(range(len(names)), [label_of(n) if n in SOURCE_COLOURS or "." in n else SOURCE_LABELS.get(n, n) for n in names])
    ax.set_ylim(len(names) - 0.4, -1.0)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    return ax

def plot_intervals(groups, xlabel="", title="", reference_line=0.0):
    """Estimates with 95% intervals, one panel per group (a "forest plot").

    ``groups`` maps a panel title to a list of ``(source, estimate, low, high)``.
    The dot colour follows the source; the grey line marks ``reference_line``.
    """
    names = list(groups)
    height = max(2.6, 0.3 * max(len(rows) for rows in groups.values()) + 1.3)
    fig, axes = plt.subplots(1, len(names), figsize=(3.4 * len(names), height), facecolor=SURFACE,
                             sharex=True, squeeze=False)
    for ax, name in zip(axes.flat, names):
        rows = groups[name]
        for k, (source, estimate, low, high) in enumerate(rows):
            colour = colour_of(source)
            ax.plot([low, high], [k, k], color=colour, linewidth=2.2, solid_capstyle="round")
            ax.plot(estimate, k, "o", color=colour, markersize=6, markeredgecolor=SURFACE)
        ax.axvline(reference_line, color=AXIS, linewidth=1)
        ax.set_yticks(range(len(rows)), [label_of(r[0]) for r in rows])
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.set_title(name, loc="left", fontsize=9, color=INK_SECONDARY)
        ax.grid(axis="x", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        _style(ax)
    for ax in axes.flat[1:]:
        ax.tick_params(labelleft=False)
    fig.supxlabel(xlabel, fontsize=9, color=INK_SECONDARY)
    if title:
        fig.suptitle(title, x=0.02, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    return axes


def plot_chain(columns, rows, cells, title=""):
    """A grid of maps that reads as a chain: one column per step, one row per model.

    ``columns`` is a list of ``{"title", "units", "limit"}`` (one colour scale per
    column, diverging, +-limit). ``rows`` is a list of row labels. ``cells`` maps
    ``(row, column number)`` to ``{"field", "note", "stipple", "contour"}``: the
    map, a one-line result written above it, an optional boolean mask drawn as
    dots, and an optional field drawn as black contour lines (a reference).
    Every panel has the same size, so maps of different regions line up.
    """
    import cartopy.crs as ccrs

    projection = ccrs.PlateCarree()
    width, height, gap, top, left = 3.3, 2.15, 0.4, 0.55, 0.8
    head, note, bar = 0.32, 0.42, 1.05
    total_w = left + len(columns) * width + (len(columns) - 1) * gap + 0.1
    total_h = top + head + len(rows) * (height + note) + bar + 0.15
    fig = plt.figure(figsize=(total_w, total_h), facecolor=SURFACE)
    axes = np.empty((len(rows), len(columns)), dtype=object)
    for j, column in enumerate(columns):
        x0 = (left + j * (width + gap)) / total_w
        fig.text(x0, 1 - (top + head * 0.55) / total_h, column["title"], fontsize=10, color=INK, weight="bold", va="center")
        mesh = None
        for i, row in enumerate(rows):
            y0 = 1 - (top + head + (i + 1) * (height + note) - 0.0) / total_h
            ax = fig.add_axes([x0, y0, width / total_w, height / total_h], projection=projection)
            axes[i, j] = ax
            cell = cells[(row, j)]
            field = cell["field"]
            ax.set_extent([float(field.lon.min()), float(field.lon.max()), float(field.lat.min()), float(field.lat.max())],
                          crs=projection)
            ax.set_aspect("auto")
            mesh = ax.pcolormesh(field.lon, field.lat, field.transpose("lat", "lon"), cmap=DIVERGING,
                                 vmin=-column["limit"], vmax=column["limit"], shading="auto", transform=projection)
            if cell.get("contour") is not None:
                ref = cell["contour"]
                levels = [v for v in np.linspace(-column["limit"], column["limit"], 9) if abs(v) > 1e-9]
                ax.contour(ref.lon, ref.lat, ref.transpose("lat", "lon"), levels=levels, colors=INK,
                           linewidths=0.6, transform=projection)
            if cell.get("stipple") is not None:
                marked = cell["stipple"].isel(lat=slice(1, None, 3), lon=slice(1, None, 3))
                yy, xx = np.meshgrid(marked.lat, marked.lon, indexing="ij")
                ax.scatter(xx[marked.values], yy[marked.values], s=1.4, color=INK, linewidths=0, transform=projection)
            ax.coastlines(resolution="50m", color=INK, linewidth=0.45)
            _lonlat_labels(ax, left=True, bottom=(i == len(rows) - 1))
            ax.set_title(cell.get("note", ""), loc="left", fontsize=8.5, color=INK, pad=3)
            if j == 0:
                ax.text(-0.17, 0.5, row, transform=ax.transAxes, rotation=90, ha="right", va="center",
                        fontsize=10, color=INK, weight="bold")
        cax = fig.add_axes([x0 + 0.08 * width / total_w, 0.42 * bar / total_h, 0.84 * width / total_w, 0.12 / total_h])
        colorbar = fig.colorbar(mesh, cax=cax, orientation="horizontal")
        colorbar.set_label(column["units"], color=INK_SECONDARY, fontsize=8)
        colorbar.ax.tick_params(labelsize=7.5, colors=MUTED)
        colorbar.outline.set_visible(False)
    if title:
        fig.text(0.01, 1 - 0.28 / total_h, title, fontsize=12, color=INK, va="center")
    return axes


def plot_overview(runs, link, control, hadgem, title=""):
    """Six-panel overview of the three version 2 experiments.

    ``runs``: one row per run and reference with columns ``source``, ``r95p_bias`` (% vs E-OBS) and
    ``nao_strength`` (relative to ERA5; NaN for E-OBS).
    ``link``: one row per region and dataset with ``region``, ``source``, ``r``, ``low``, ``high``
    (winter R95p-NAO correlation and its 95% interval).
    ``control``: one row per region and model with ``region``, ``source``, ``low``, ``median``, ``high``
    (chance range from the control runs).
    ``hadgem``: one row per HadGEM3 resolution with ``source``, ``km``, ``rms_error``, ``pattern_r``,
    ``nao_strength``, ``nao_first``, ``nao_second``, ``rain_bias``.
    """
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 7.6), facecolor=SURFACE)
    models = ["icon-esm-er", "ifs-fesom2-sr"]

    def dots(ax, column, xlabel, reference=None, reference_label=""):
        for row, model in enumerate(models):
            part = runs[runs.source.str.split(".").str[0] == model]
            ax.scatter(part[column], [row] * len(part), s=55, color=colour_of(model), edgecolors=SURFACE, zorder=3)
            ax.plot([part[column].mean()] * 2, [row - 0.25, row + 0.25], color=INK, linewidth=1.8)
        if reference is not None:
            ax.axvline(reference, color=SOURCE_COLOURS["era5"], linestyle="--", linewidth=1.2)
            ax.text(reference, -0.62, reference_label, fontsize=8, color=INK_SECONDARY, ha="center")
        ax.set_yticks([0, 1], [SOURCE_LABELS[m] for m in models])
        ax.set_ylim(1.6, -0.9)
        ax.set_xlabel(xlabel, fontsize=8.5, color=INK_SECONDARY)
        ax.grid(axis="x", color=GRID, linewidth=0.6)
        _style(ax)

    dots(axes[0, 0], "r95p_bias", "winter R95p, UK and Ireland, vs E-OBS (%)", 0.0, "E-OBS")
    dots(axes[0, 1], "nao_strength", "NAO strength relative to ERA5 (1976-2014)", 1.0, "ERA5")

    ax = axes[0, 2]
    regions_order = list(dict.fromkeys(link.region))
    ticks, labels = [], []
    y = 0
    for region in regions_order:
        for model in models:
            c = control[(control.region == region) & (control.source == model)].iloc[0]
            ax.add_patch(plt.Rectangle((c.low, y - 0.3), c.high - c.low, 0.6, color=colour_of(model), alpha=0.22, linewidth=0))
            part = link[(link.region == region) & (link.source.str.split(".").str[0] == model)]
            ax.scatter(part.r, [y] * len(part), s=30, color=colour_of(model), edgecolors=SURFACE, zorder=3)
            ticks.append(y)
            labels.append(f"{region}: {SOURCE_LABELS[model].split('-')[0]}")
            y += 1
        for ref, shift in (("e-obs", -0.15), ("era5", 0.15)):
            r = link[(link.region == region) & (link.source == ref)].iloc[0]
            ax.errorbar(r.r, y - 1.5 + shift, xerr=[[r.r - r.low], [r.high - r.r]], fmt="D", ms=4,
                        color=colour_of(ref), capsize=0, linewidth=1.2, zorder=4)
        y += 0.6
    ax.axvline(0, color=AXIS, linewidth=0.8)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=MUTED, alpha=0.3, label="control runs, 5-95%"),
                       Line2D([], [], marker="o", linestyle="", color=MUTED, label="historical runs"),
                       Line2D([], [], marker="D", color=SOURCE_COLOURS["e-obs"], label="E-OBS (95% interval)"),
                       Line2D([], [], marker="D", color=SOURCE_COLOURS["era5"], label="ERA5 (95% interval)")],
              frameon=False, fontsize=7, loc="lower right", ncol=2)
    ax.set_yticks(ticks, labels, fontsize=7.5)
    ax.set_ylim(y + 1.3, -0.7)
    ax.set_xlabel("winter R95p-NAO correlation (29 winters)", fontsize=8.5, color=INK_SECONDARY)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    _style(ax)

    hadgem = hadgem.sort_values("km", ascending=False)
    x = range(len(hadgem))
    xticks = [f"{int(k)} km" for k in hadgem.km]
    panels = (
        (axes[1, 0], [("rms_error", "pressure error (RMS, hPa)", INK)], "winter sea-level pressure error vs ERA5"),
        (axes[1, 1], [("pattern_r", "NAO pattern vs ERA5", colour_of("hadgem3-gc5e-hh")),
                      ("nao_strength", "NAO strength vs ERA5", colour_of("hadgem3-gc5e-mm"))], "NAO pattern and strength"),
        (axes[1, 2], [("rain_bias", "winter rain vs ERA5 (%)", colour_of("hadgem3-gc5e-hh"))], "winter rain, UK and Ireland"),
    )
    for ax, series, label in panels:
        for column, name, colour in series:
            ax.plot(list(x), hadgem[column], "o-", color=colour, linewidth=2, markersize=7, label=name)
            if column == "nao_strength":
                for i, (_, row) in enumerate(hadgem.iterrows()):
                    ax.plot([i, i], [min(row.nao_first, row.nao_second), max(row.nao_first, row.nao_second)],
                            color=colour, linewidth=5, alpha=0.3, solid_capstyle="round")
        if len(series) > 1:
            ax.axhline(1.0, color=SOURCE_COLOURS["era5"], linestyle="--", linewidth=1)
            ax.legend(frameon=False, fontsize=8, loc="lower left")
        if column in ("rms_error", "rain_bias"):
            ax.set_ylim(0, max(hadgem[column]) * 1.15)
        ax.set_xticks(list(x), xticks)
        ax.set_xlabel("HadGEM3-GC5E atmosphere resolution (ocean 1°, 1/4°, 1/12°)", fontsize=8.5, color=INK_SECONDARY)
        ax.set_ylabel(series[0][1] if len(series) == 1 else "relative to ERA5", fontsize=8.5, color=INK_SECONDARY)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        _style(ax)

    heads = ["A  Ensemble: wet bias in every run", "B  Ensemble: NAO strength in every run",
             "C  Chance: NAO link to very-wet-day rain",
             "D  Resolution: mean circulation", "E  Resolution: NAO pattern and strength", "F  Resolution: winter rain"]
    for ax, head in zip(axes.flat, heads):
        ax.set_title(head, loc="left", fontsize=10, color=INK, fontweight="bold")
    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=12.5, color=INK)
    fig.tight_layout()
    return axes


def _box(ax, x, y, w, h, colour, fill=None, lw=1.5):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                linewidth=lw, edgecolor=colour, facecolor=fill or SURFACE))


def plot_experiment_design():
    """Diagram of the three experiments: data, frequency, period, question and notebooks."""
    fig = plt.figure(figsize=(13, 5.0), facecolor=SURFACE)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.88])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    experiments = [
        ("1  Historical ensemble evaluation", BLUE,
         "Which biases persist across runs?",
         ["ICON-ESM-ER  r1 r2 r3", "IFS-FESOM2-SR  r1 r2 r3", "daily extremes and their drivers"],
         "daily and monthly, 1975/1985-2014", "notebooks 03-06, 09, 10"),
        ("2  Internal variability", "#1baf7a",
         "What can chance do in 29 winters?",
         ["ICON-ESM-ER control, 99 winters", "IFS-FESOM2-SR control, 99 winters", "IFS atmosphere-only, 10 members"],
         "constant 1950 forcing, 71 overlapping windows", "notebooks 07, 11"),
        ("3  Resolution", "#4a3aa7",
         "What changes with resolution?",
         ["HadGEM3-GC5E  LL 135, MM 60, HH 20 km", "ocean 1, 1/4, 1/12 degree, refined together",
          "IFS atmosphere-only  28 km vs 9 km"],
         "monthly (HadGEM3) and daily (IFS), 1950-2014", "notebooks 08, 12"),
    ]
    width, gap = 0.305, 0.0375
    for k, (title, colour, question, data, frequency, notebooks) in enumerate(experiments):
        x = k * (width + gap)
        _box(ax, x, 0.30, width, 0.62, colour, lw=2)
        ax.add_patch(plt.Rectangle((x, 0.84), width, 0.08, color=colour, alpha=0.15, linewidth=0))
        ax.text(x + 0.015, 0.88, title, fontsize=11, fontweight="bold", color=colour, va="center")
        ax.text(x + 0.015, 0.78, question, fontsize=10, style="italic", color=INK, va="center")
        for i, line in enumerate(data):
            ax.text(x + 0.015, 0.68 - i * 0.075, line, fontsize=9.5, color=INK, va="center")
        ax.text(x + 0.015, 0.40, frequency, fontsize=8.8, color=INK_SECONDARY, va="center")
        ax.text(x + 0.015, 0.34, notebooks, fontsize=8.8, color=MUTED, va="center")
        ax.plot([x + width / 2] * 2, [0.21, 0.30], color=AXIS, linewidth=1)
    _box(ax, 0.0, 0.04, 1.0, 0.17, AXIS, fill=EMPTY, lw=1)
    ax.text(0.5, 0.155, "References: ERA5 (reanalysis; pressure, rain, temperature, wind)   |   E-OBS (stations, land; daily rain and temperature)",
            fontsize=9.5, ha="center", va="center", color=INK)
    ax.text(0.5, 0.085, "Domains: North Atlantic (NAO), north-west Europe (extremes)   |   worked examples: UK and Ireland, western Norway, north-west France",
            fontsize=9.5, ha="center", va="center", color=INK_SECONDARY)
    fig.suptitle("Experimental design: three complementary experiments, the same diagnostics and references",
                 x=0.01, ha="left", fontsize=12.5, color=INK)
    return ax


def plot_control_windows(start=1951, end=2049, window=29, historical=(1986, 2014), examples=(1951, 1971, 1990, 2000, 2021)):
    """Timeline of a control run and how overlapping 29-winter windows are cut from it."""
    fig, ax = plt.subplots(figsize=(12, 3.8), facecolor=SURFACE)
    _style(ax)
    ax.add_patch(plt.Rectangle((start, 0.0), end - start + 1, 0.6, color="#1baf7a", alpha=0.18, linewidth=0))
    ax.text(start + 0.5, 0.3, f"control run: {end - start + 1} winters, constant 1950 forcing", va="center", fontsize=10, color=INK)
    middle = (start + end) / 2
    ax.axvline(middle + 0.5, color=AXIS, linestyle=":", linewidth=1)
    ax.text(middle - 25, -0.25, "first half", ha="center", fontsize=8.5, color=MUTED)
    ax.text(middle + 25, -0.25, "second half", ha="center", fontsize=8.5, color=MUTED)
    for i, s in enumerate(examples):
        y = 0.9 + i * 0.32
        ax.add_patch(plt.Rectangle((s, y), window, 0.22, color="#1baf7a", alpha=0.55, linewidth=0))
        ax.text(s + window + 0.8, y + 0.11, f"window {s}-{s + window - 1}", va="center", fontsize=8.5, color=INK_SECONDARY)
    y = 0.9 + len(examples) * 0.32 + 0.15
    ax.add_patch(plt.Rectangle((historical[0], y), historical[1] - historical[0] + 1, 0.26, color=BLUE, alpha=0.75, linewidth=0))
    ax.text(historical[1] + 1.8, y + 0.13, f"historical runs and observations: {historical[0]}-{historical[1]} (29 winters)",
            va="center", fontsize=9, color=BLUE)
    n = end - start + 1 - window + 1
    ax.text(start, y + 0.95, f"{n} overlapping windows (starting {start} to {end - window + 1}). The 5th-95th percentile of a diagnostic"
            "\n"
            "across them is the empirical chance range; with this much overlap there are only about 3 independent windows.",
            fontsize=9, color=INK, va="center")
    ax.set_xlim(start - 1, end + 24)
    ax.set_ylim(-0.45, y + 1.3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("winter (year of January)", fontsize=9, color=INK_SECONDARY)
    ax.set_title("How chance ranges are built from a control run", loc="left", fontsize=11.5, color=INK)
    fig.tight_layout()
    return ax


def plot_resolution_ladder(table):
    """HadGEM3-GC5E LL / MM / HH: grid spacing and the main diagnostics.

    ``table`` has one row per configuration with ``source``, ``atmosphere_km``, ``ocean`` (text),
    ``rms_error``, ``pattern_r`` and ``rain_bias``.
    """
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.9), facecolor=SURFACE, gridspec_kw={"width_ratios": [1.6, 1, 1, 1]})
    ax = axes[0]
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 1.25)
    ax.axis("off")
    for i, row in enumerate(table.itertuples()):
        colour = colour_of(row.source)
        cells = {135: 2, 60: 4, 20: 10}.get(int(row.atmosphere_km), 4)
        x0, size = i + 0.12, 0.76
        for c in range(cells + 1):
            ax.plot([x0 + c * size / cells] * 2, [0.25, 0.25 + size], color=colour, linewidth=0.8)
            ax.plot([x0, x0 + size], [0.25 + c * size / cells] * 2, color=colour, linewidth=0.8)
        ax.text(x0 + size / 2, 1.13, row.source.split("-")[-1].upper(), ha="center", fontsize=12, fontweight="bold", color=colour)
        ax.text(x0 + size / 2, 0.15, f"atmosphere ~{int(row.atmosphere_km)} km", ha="center", fontsize=8.5, color=INK)
        ax.text(x0 + size / 2, 0.05, f"ocean {row.ocean}", ha="center", fontsize=8.5, color=INK_SECONDARY)
    ax.set_title("Same model, atmosphere and ocean refined together", loc="left", fontsize=10, color=INK)
    metrics = (("rms_error", "winter pressure error\nvs ERA5 (hPa)"),
               ("pattern_r", "NAO pattern correlation\nwith ERA5"),
               ("rain_bias", "UK and Ireland winter-mean\nrain vs ERA5 (%)"))
    for ax, (column, label) in zip(axes[1:], metrics):
        names = [s.split("-")[-1].upper() for s in table.source]
        ax.bar(names, table[column], color=[colour_of(s) for s in table.source], width=0.6)
        for x, v in enumerate(table[column]):
            ax.text(x, v, f"{v:.1f}" if column == "rain_bias" else f"{v:.2f}", ha="center", va="bottom", fontsize=9, color=INK)
        if column == "pattern_r":
            ax.set_ylim(0.85, 1.0)
        ax.set_title(label, loc="left", fontsize=9.5, color=INK)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        _style(ax)
    fig.suptitle("HadGEM3-GC5E coupled resolution configurations (one run each, monthly data)", x=0.01, ha="left",
                 fontsize=11.5, color=INK)
    fig.tight_layout()
    return axes
