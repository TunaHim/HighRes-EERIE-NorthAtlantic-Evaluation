"""Generate notebooks/11_control.ipynb.  Usage: python build_notebook_11.py OUT.ipynb [findings.md]"""
import sys
import nbformat as nbf

FINDINGS = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else "_Written after the first run._"

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def step(explain, source):
    cells.append(nbf.v4.new_markdown_cell(explain.strip("\n")))
    cells.append(nbf.v4.new_code_cell(source.strip("\n")))


md("""
# 11 · How much can chance alone do? 100 years of control runs

**Question for this notebook.** Notebook 10 showed that three runs of one model can disagree on
the NAO link to rain extremes. But how wide is the range that chance alone produces? The EERIE
archive has a **control run** of each coupled model: 100 years (1950–2049) with the external
forcing held at 1950 conditions, so every difference between one stretch of years and another is
internal variability. Cutting it into windows of 29 winters, the length used for extremes in
version 1, gives the **chance range** of each diagnostic for that model. A historical run or an
observed value outside that range is unlikely to be chance.

**Data.**
- ICON-ESM-ER and IFS-FESOM2-SR control runs (`eerie-control-1950`): monthly sea-level pressure,
  1950–2049 (99 complete winters), and daily precipitation over north-west Europe.
- For comparison: ERA5 and E-OBS (notebook 06) and the three historical runs (notebook 10).

**Method.**
1. NAO index of each control winter along the ERA5 pattern, in ERA5 standard deviations
   (anomalies relative to the control run's own 100-year winter mean).
2. Winter RX1day and R95p from the control run's daily rain (the very-wet-day threshold from all
   100 control winters), land average of each region, same land cells as before.
3. Every window of 29 consecutive winters (71 windows, starting 1951 to 2021): NAO strength and the
   detrended correlation between the NAO and each regional rain index.
4. The 5th to 95th percentile of those 71 values is the chance range.

**A caution.** Consecutive windows overlap, so the 71 values are not independent: 99 winters hold
only about three independent 29-winter samples. The range is therefore an estimate, likely a
little too narrow in the tails. It is still far better than the spread of three runs.

**Sections**
1. Setup
2. Findings
3. The control runs at a glance
4. NAO strength: chance range
5. NAO link to rain extremes: chance range
6. Where the historical runs and observations fall
7. Is the control run stable? First against second half
8. Saved outputs
9. Limitations
10. Open questions
""")

md("""
## Background: the terms used in this notebook

| Term | What it means here |
|---|---|
| **Control run** | A simulation with constant 1950 greenhouse gases, aerosols and other forcing. It has weather and year-to-year variability but no climate change, so it shows the model's internal variability alone. |
| **Window** | 29 consecutive winters of the control run, the same length as the 1986–2014 period of version 1. |
| **Chance range** | The 5th to 95th percentile of a diagnostic over all windows: values that the model produces by chance in 90% of 29-winter periods. |
| **Inside / outside the chance range** | A historical run inside the range is consistent with chance; an observed value outside it means the model rarely produces what was observed. |
| **Drift** | A slow trend in a control run as the model adjusts. Series are detrended within each window, as in version 1. |
""")

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code and the ERA5 NAO pattern used throughout the
project, and builds the common land mask.
""", """
import sys, warnings
sys.path.insert(0, '../src')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from eerie_uk import climatology as clim, extremes as ex, nao, plotting, regions, relationships as rel, store

pd.set_option('display.width', 220, 'display.float_format', '{:.2f}'.format)
CONTROLS = {'icon-esm-er': 'icon-esm-er.control', 'ifs-fesom2-sr': 'ifs-fesom2-sr.control'}
WINDOW = 29
LABEL = plotting.label_of

era5_nao = nao.leading_eof(nao.winter_anomalies(store.load('era5', 'mon', 'psl', 'north_atlantic')))
grid = ex.indices_for('icon-esm-er')
eobs = regions.to_grid(ex.indices_for('e-obs'), grid)
land = regions.land_mask(grid.lat, grid.lon)
common = land & eobs.rx1day_djf.isel(year_djf=0).notnull()
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. The control runs at a glance
""")

step("""
**What this cell does.** Computes the winter NAO index of each control run and its winter RX1day and
R95p from daily rain, and shows the NAO index through the 100 years.
""", """
control_nao, control_rain = {}, {}
for model, run in CONTROLS.items():
    winters = nao.winter_anomalies(store.load(run, 'mon', 'psl', 'north_atlantic'), (1950, 2049))
    control_nao[model] = nao.project(winters, era5_nao.vector) / era5_nao.amplitude
    daily = store.load(run, 'day', 'pr', 'nw_europe')
    threshold = ex.wet_day_threshold(daily, base=(1950, 2049), period='DJF')
    control_rain[model] = {'R95p': ex.r95p(daily, threshold, 'DJF'), 'RX1day': ex.rx1day(daily, 'DJF')}
panels = {LABEL(m).split()[0] + ' control': {m: (control_nao[m].year.values, control_nao[m].values)} for m in CONTROLS}
plotting.plot_line_panels(panels, ylabel='NAO index (ERA5 SD)', title='Winter NAO index in the control runs, 1951-2049', columns=2, sharey=True);
""")

md("""
**Figure 1.** The winter NAO index of each control run along the ERA5 pattern. There is no
climate change in these runs, so any slow change is drift or long-term internal variability.
""")

step("""
**What this cell does.** Checks the size of drift: the linear trend of the NAO index and of UK and
Ireland winter R95p over the 100 control years.
""", """
rows = []
for m in CONTROLS:
    uk = clim.regional_mean(control_rain[m]['R95p'].where(common), 'uk_ireland')
    rows.append({'model': LABEL(m).split()[0], 'NAO trend (SD per decade)': nao.trend(control_nao[m].year, control_nao[m])['trend per decade'],
                 'UK R95p trend (% of mean per decade)': 100 * nao.trend(uk.year, uk)['trend per decade'] / float(uk.mean())})
pd.DataFrame(rows).set_index('model')
""")

md("""
## 4. NAO strength: chance range
""")

step("""
**What this cell does.** For every 29-winter window of each control run, the NAO strength
(standard deviation of the index along the ERA5 pattern, in ERA5 units). Then the chance range,
and for comparison the strength of the three historical runs over 1986–2014 in the same units.
""", """
def windows(series):
    years = series.year.values
    return [np.arange(start, start + WINDOW) for start in range(years[0], years[-1] - WINDOW + 2)]

historical = {m: [m, f'{m}.r2', f'{m}.r3'] for m in CONTROLS}

def historical_nao(run):
    psl = store.load(run, 'mon', 'psl', 'north_atlantic')
    w = nao.winter_anomalies(clim.period(psl, 1975, 2014), (1975, 2014))
    return (nao.project(w, era5_nao.vector) / era5_nao.amplitude).sel(year=slice(1986, 2014))

era5_window = (nao.project(nao.winter_anomalies(store.load('era5', 'mon', 'psl', 'north_atlantic')), era5_nao.vector)
               / era5_nao.amplitude).sel(year=slice(1986, 2014))
rows = []
for m in CONTROLS:
    values = [float(control_nao[m].sel(year=y).std(ddof=1)) for y in windows(control_nao[m])]
    runs = [float(historical_nao(r).std(ddof=1)) for r in historical[m]]
    rows.append({'model': LABEL(m).split()[0], 'windows': len(values), 'chance range 5%': np.percentile(values, 5),
                 'median': np.median(values), 'chance range 95%': np.percentile(values, 95), 'highest window': max(values),
                 'historical runs 1986-2014': ', '.join(f'{v:.2f}' for v in runs)})
strength = pd.DataFrame(rows).set_index('model')
print(f'ERA5 1986-2014: {float(era5_window.std(ddof=1)):.2f}')
strength
""")

md("""
**How to read this table.** All values are standard deviations of the winter NAO index in ERA5
units; ERA5 itself has 1.00 over 1951–2014 and the value printed above over 1986–2014. If ERA5's
value lies above the highest control window, no 29-winter period of the model reaches the observed
NAO strength.
""")

md("""
## 5. NAO link to rain extremes: chance range
""")

step("""
**What this cell does.** For every window, region and rain index: the detrended correlation between
the control run's winter NAO and the land-average winter index. Summarised as the chance range.
""", """
rows = []
for m in CONTROLS:
    for region in regions.SUBREGIONS:
        for key, field in control_rain[m].items():
            series = clim.regional_mean(field.where(common), region)
            for years in windows(control_nao[m]):
                fit = rel.regress_series(series.sel(year=years).values, control_nao[m].sel(year=years).values)
                rows.append({'model': m, 'region': regions.LABELS[region], 'index': key, 'start': int(years[0]), 'r': fit['r']})
window_link = pd.DataFrame(rows)
chance = (window_link.groupby(['region', 'index', 'model']).r
          .describe(percentiles=[0.05, 0.5, 0.95])[['5%', '50%', '95%', 'min', 'max']].unstack('model'))
chance
""")

md("""
## 6. Where the historical runs and observations fall
""")

step("""
**What this cell does.** Puts the chance range of each model next to the correlations of its three
historical runs and of the two references (from notebook 10), for each region and rain index.
""", """
members = pd.read_parquet('../app_assets/members_nao_link.parquet')
rows = []
for region in regions.SUBREGIONS:
    for key in ('R95p', 'RX1day'):
        part = members[(members.region == regions.LABELS[region]) & (members['index'] == key)].set_index('source')
        for m in CONTROLS:
            values = window_link[(window_link.model == m) & (window_link.region == regions.LABELS[region]) & (window_link['index'] == key)].r
            low, high = np.percentile(values, [5, 95])
            runs = [part.r[s] for s in historical[m]]
            rows.append({'region': regions.LABELS[region], 'index': key, 'model': LABEL(m).split()[0],
                         'chance range': f'{low:.2f} to {high:.2f}', 'historical runs': ', '.join(f'{v:.2f}' for v in runs),
                         'runs inside': sum(low <= v <= high for v in runs),
                         'E-OBS': part.r['e-obs'], 'ERA5': part.r['era5'],
                         'E-OBS inside': bool(low <= part.r['e-obs'] <= high), 'ERA5 inside': bool(low <= part.r['era5'] <= high)})
placement = pd.DataFrame(rows)
placement
""")

step("""
**What this cell does.** Draws the same comparison for winter R95p: for each region and model, a
box from the 5th to the 95th percentile of the control windows, the three historical runs as dots,
and the two references as vertical lines.
""", """
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 3, figsize=(11, 2.9), facecolor=plotting.SURFACE, sharex=True)
for ax, region in zip(axes, regions.SUBREGIONS):
    part = members[(members.region == regions.LABELS[region]) & (members['index'] == 'R95p')].set_index('source')
    for row, m in enumerate(CONTROLS):
        values = window_link[(window_link.model == m) & (window_link.region == regions.LABELS[region]) & (window_link['index'] == 'R95p')].r
        low, mid, high = np.percentile(values, [5, 50, 95])
        ax.add_patch(plt.Rectangle((low, row - 0.25), high - low, 0.5, color=plotting.colour_of(m), alpha=0.25, linewidth=0))
        ax.plot([mid, mid], [row - 0.25, row + 0.25], color=plotting.colour_of(m), linewidth=1.5)
        ax.scatter([part.r[s] for s in historical[m]], [row] * 3, color=plotting.colour_of(m), edgecolors=plotting.SURFACE, s=40, zorder=3)
    for ref in ('e-obs', 'era5'):
        ax.axvline(part.r[ref], color=plotting.colour_of(ref), linewidth=1.6, linestyle='--')
    ax.axvline(0, color=plotting.AXIS, linewidth=0.8)
    ax.set_yticks([0, 1], [LABEL(m).split()[0] for m in CONTROLS])
    ax.set_ylim(1.6, -0.6)
    ax.set_title(regions.LABELS[region], loc='left', fontsize=9, color=plotting.INK_SECONDARY)
    plotting._style(ax)
fig.supxlabel('correlation of winter R95p with the winter NAO (29 winters)', fontsize=9, color=plotting.INK_SECONDARY)
fig.suptitle('Chance range from the control runs (shaded, 5-95%), historical runs (dots), E-OBS and ERA5 (dashed)',
             x=0.02, ha='left', fontsize=11)
fig.tight_layout();
""")

md("""
**Figure 2.** Shaded box: the range of the NAO–R95p correlation over 90% of 29-winter windows of
the control run (line: median). Dots: the three historical runs (1986–2014). Dashed lines: E-OBS
(light grey) and ERA5 (dark grey). A reference line far outside a model's box means the model
rarely produces the observed link.
""")

md("""
## 7. Is the control run stable? First against second half

A control run is useful for chance ranges only if its statistics do not drift. This section
compares windows that lie entirely in the first half of the run (1951–1999, window starts up to
1971) with windows entirely in the second half (2000–2049). Similar medians mean no drift; the
difference between the halves also shows how much the range itself depends on which 50 years are
sampled.
""")

step("""
**What this cell does.** For NAO strength and for each region and rain index: the median and the
range over the windows of each half of each control run.
""", """
half = lambda start: 'first half' if start <= 1971 else ('second half' if start >= 2000 else None)
rows = []
for m in CONTROLS:
    for years in windows(control_nao[m]):
        h = half(int(years[0]))
        if h:
            rows.append({'model': LABEL(m).split()[0], 'quantity': 'NAO strength', 'half': h,
                         'value': float(control_nao[m].sel(year=years).std(ddof=1))})
part = window_link.assign(half=window_link.start.map(half)).dropna(subset=['half'])
for _, row in part.iterrows():
    rows.append({'model': LABEL(row.model).split()[0], 'quantity': f'NAO link to {row["index"]}, {row.region}',
                 'half': row.half, 'value': row.r})
halves = (pd.DataFrame(rows).groupby(['model', 'quantity', 'half']).value
          .agg(['min', 'median', 'max']).unstack('half'))
halves
""")

md("""
**How to read this table.** For each model and quantity, the smallest, median and largest value over
the windows of the first and of the second half. Medians that agree within about 0.1 show no drift;
larger differences between halves show that 50 years hold only one or two independent 29-winter
samples.
""")

md("""
## 8. Saved outputs
""")

step("""
**What this cell does.** Saves the window-by-window correlations and the placement table to
`app_assets/`, with provenance.
""", """
from eerie_uk import provenance
out = Path('../app_assets')
meta = dict(inputs={'control runs': 'data/<model>.control/', 'members': 'app_assets/members_nao_link.parquet'},
            window_winters=WINDOW, control_years='1950-2049')
provenance.write_table(window_link, out / 'control_window_link.parquet', 'NAO-rain-extremes correlation in every 29-winter window of the control runs', **meta)
provenance.write_table(placement, out / 'control_placement.parquet', 'Chance range from control runs and where historical runs and references fall', **meta)
provenance.write_table(strength.reset_index(), out / 'control_nao_strength.parquet', 'NAO strength chance range from control-run windows', **meta)
provenance.write_table(halves.reset_index().set_axis(['model', 'quantity'] + [f'{a} {b}' for a, b in halves.columns], axis=1),
                       out / 'control_halves.parquet', 'Control-run stability: window statistics in the first and second half', **meta)
print('saved 4 tables')
""")

md("""
## 9. Limitations

- **Overlapping windows.** 99 winters contain only about three independent 29-winter samples, so the
  chance range is an estimate and probably slightly too narrow at the tails.
- **1950 forcing.** The control runs have no climate change; the historical runs do. Where forcing
  itself changes the NAO link, the comparison mixes the two. Within 1986–2014 this effect is
  expected to be small compared with internal variability.
- **Model chance, not observational chance.** The range shows what *this model* does by chance; it
  is used to ask whether the observed value is unusual *for the model*.
- **Daily rain only.** The control runs were downloaded with daily precipitation only, so TXx is not
  tested here.
""")

md("""
## 10. Open questions

1. Is the observed link over western Norway (0.81) outside the chance range of both models because
   of their weak NAO, or because of how rain responds to a given NAO swing?
2. Would a longer control run, or several, widen the ranges enough to include the observations?
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
