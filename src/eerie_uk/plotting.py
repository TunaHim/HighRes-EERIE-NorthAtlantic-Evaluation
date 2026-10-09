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
