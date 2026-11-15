"""Generate notebooks/10_members.ipynb.  Usage: python build_notebook_10.py OUT.ipynb [findings.md]"""
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
# 10 · Model or chance? Three runs of each coupled model

**Question for this notebook.** Version 1 evaluated one run (member r1) of each coupled model. A
single run carries its own chance weather, so every model result in notebooks 04–06 could be a
property of the model or a lucky or unlucky run. The EERIE archive holds two more historical runs
of each model (r2 and r3). They use the same model and the same external forcing and differ only
in tiny changes to the starting state, so after a few years their weather is independent. This
notebook repeats the key diagnostics of version 1 on all three runs and asks, result by result:
**do all three runs agree?**

**Data.**
- ICON-ESM-ER and IFS-FESOM2-SR, historical runs r1, r2 and r3. The r2 and r3 runs start in 1975,
  so the NAO is compared over the common 39 winters **1976–2014**; extremes over the 29 winters
  **1986–2014**, as in version 1.
- References as in version 1: ERA5 (pressure, rain, temperature) and E-OBS (rain and temperature
  over land).
- IFS-FESOM2-SR r3 has no data for 2–31 October 1999 on the server. October is not part of winter,
  so the winter results are unaffected; the annual indices for 1999 miss those days.

**How to read the results.** Three runs are still a small ensemble: their range shows how much
chance alone can move a number, but it is not a full uncertainty interval. A result that holds in
all three runs is called **robust across the three runs**; one that changes sign or size strongly
between runs is **sensitive to chance**. Notebook 11 adds the long control runs to measure chance
more completely.

**Sections**
1. Setup
2. Findings
3. The NAO in three runs
4. The mean circulation offset
5. Extremes over UK and Ireland
6. The NAO link to winter rain extremes
7. How much of ICON-ESM-ER's wet bias the circulation explains, per run
8. Which version 1 results hold?
9. Saved outputs
10. Limitations
11. Open questions
""")

md("""
## Background: the terms used in this notebook

| Term | What it means here |
|---|---|
| **Member (run) r1, r2, r3** | Three simulations of the same model with the same forcing, started from slightly different states. Their differences are internal variability: chance weather. |
| **Robust across the three runs** | All three runs give the same sign and a similar size. With only three runs this is necessary but not sufficient for a robust model property. |
| **NAO strength** | Standard deviation of the winter pressure index measured along the common ERA5 NAO pattern, divided by the same quantity for ERA5 over the same winters (notebook 04). |
| **Mean circulation offset** | The model's average winter pressure minus ERA5's, projected onto the ERA5 NAO pattern, in ERA5 standard deviations (notebook 04, section 7). |
| **NAO link** | Detrended correlation between the winter NAO index and a winter extreme index, land average of a region (notebook 06). Each run uses its own NAO; E-OBS and ERA5 use the ERA5 NAO. |
| **Bootstrap 95% interval** | The range of the correlation when the winters are resampled 5000 times (notebook 06, section 10). |

**Colours.** Dark grey ERA5, light grey E-OBS, blue ICON-ESM-ER (all runs), orange IFS-FESOM2-SR
(all runs).
""")

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code and defines the runs, windows and regions.
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
RUNS = {'icon-esm-er': ['icon-esm-er', 'icon-esm-er.r2', 'icon-esm-er.r3'],
        'ifs-fesom2-sr': ['ifs-fesom2-sr', 'ifs-fesom2-sr.r2', 'ifs-fesom2-sr.r3']}
ALL_RUNS = RUNS['icon-esm-er'] + RUNS['ifs-fesom2-sr']
REFS = ['e-obs', 'era5']
BASE = (1975, 2014)      # anomaly base period available for every run
NAO_WINTERS = (1976, 2014)
WINTERS = (1986, 2014)
LABEL = plotting.label_of
""")

step("""
**What this cell does.** Loads monthly sea-level pressure for ERA5 and the six runs, and computes the
ERA5 NAO pattern exactly as in notebook 04 (1951–2014). Every run is then measured along that one
pattern.
""", """
psl = {s: store.load(s, 'mon', 'psl', 'north_atlantic') for s in ['era5'] + ALL_RUNS}
era5_nao = nao.leading_eof(nao.winter_anomalies(psl['era5']))
winters = {s: nao.winter_anomalies(clim.period(p, *BASE), BASE).sel(year=slice(*NAO_WINTERS)) for s, p in psl.items()}

def nao_index(source, years=NAO_WINTERS):
    \"\"\"Winter NAO index along the ERA5 pattern, in ERA5 standard deviations (as in notebook 04).\"\"\"
    w = nao.winter_anomalies(clim.period(psl[source], *BASE), BASE)
    return (nao.project(w, era5_nao.vector) / era5_nao.amplitude).sel(year=slice(*years))

print({s: winters[s].sizes['year'] for s in winters})
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. The NAO in three runs
""")

step("""
**What this cell does.** For ERA5 and each run, over the same 39 winters: the NAO strength along
the ERA5 pattern relative to ERA5, the variance of the first two patterns of the run's own EOF
analysis, whether they are separated (North et al. 1982, as in notebook 04) and how closely the
run's own first pattern resembles ERA5's.
""", """
era5_own = nao.leading_eof(winters['era5'])
era5_spread = float(nao.project(winters['era5'], era5_nao.vector).std(ddof=1))
rows = []
for s in ['era5'] + ALL_RUNS:
    e = nao.leading_eof(winters[s])
    spacing = nao.north_spacing(e.explained, winters[s].sizes['year'])
    rows.append({'run': LABEL(s), 'source': s,
                 'NAO strength relative to ERA5': float(nao.project(winters[s], era5_nao.vector).std(ddof=1)) / era5_spread,
                 'EOF1 %': 100 * e.explained[0], 'EOF2 %': 100 * e.explained[1],
                 'separated from EOF2': bool(e.explained[0] - spacing[0] > e.explained[1] + spacing[1]),
                 'own pattern vs ERA5 (pattern correlation)': clim.pattern_stats(e.pattern, era5_own.pattern)['pattern correlation']})
nao_table = pd.DataFrame(rows)
nao_table.drop(columns='source').set_index('run')
""")

step("""
**What this cell does.** Shows the NAO strength of every run as one dot per run, with ERA5 as the
dashed line at 1.
""", """
groups = {m: nao_table[nao_table.source.isin(r)]['NAO strength relative to ERA5'].values for m, r in RUNS.items()}
plotting.plot_member_dots(groups, xlabel='NAO strength along the ERA5 pattern, relative to ERA5 (winters 1976-2014)',
                          title='NAO strength of each historical run', reference=1.0, reference_label='ERA5');
""")

md("""
**Figure 1.** One dot per run; black bar: mean of the three runs; dashed line: ERA5. If the three
dots of a model lie well below the line, a weak NAO is a property of that model, not of one run.
""")

step("""
**What this cell does.** Maps each run's own leading pattern, to see whether the "mixed" pattern of
ICON-ESM-ER r1 (notebook 04) appears in its other runs too.
""", """
plotting.plot_field_panels({LABEL(s): nao.leading_eof(winters[s]).pattern for s in ['era5'] + ALL_RUNS},
                           units='hPa per +1 SD of the index', diverging=True, columns=3,
                           title='Leading pattern of winter sea-level pressure (EOF 1), each run, winters 1976-2014');
""")

md("""
**Figure 2.** The first pattern of each run's own EOF analysis. Top left ERA5; then the three
ICON-ESM-ER runs and the three IFS-FESOM2-SR runs. Blue: low pressure in a positive-NAO winter;
orange: high.
""")

md("""
## 4. The mean circulation offset
""")

step("""
**What this cell does.** For each run: its average winter sea-level pressure over 1986–2014 minus
ERA5's, projected onto the ERA5 NAO pattern, in ERA5 standard deviations (notebook 04, section 7;
notebook 06, section 11).
""", """
mean_psl = {s: clim.season_means(psl[s], 'DJF').sel(year=slice(*WINTERS)).mean('year') for s in psl}
offset = {s: nao.project_map(mean_psl[s] - mean_psl['era5'], era5_nao.vector) / era5_nao.amplitude for s in ALL_RUNS}
pd.Series({LABEL(s): v for s, v in offset.items()}, name='mean circulation offset (ERA5 NAO SD), winters 1986-2014').to_frame()
""")

md("""
## 5. Extremes over UK and Ireland
""")

step("""
**What this cell does.** Computes the extreme indices for the new runs (cached under `data/derived`
after the first run) and the land-average values over the three regions, using the same land cells
for every dataset (land where E-OBS has data), as in notebook 05.
""", """
indices = {s: ex.indices_for(s) for s in REFS + ALL_RUNS}
grid = indices['icon-esm-er']
indices['e-obs'] = regions.to_grid(indices['e-obs'], grid)
land = regions.land_mask(grid.lat, grid.lon)
common = land & indices['e-obs'].rx1day_djf.isel(year_djf=0).notnull()

def regional(source, key, tag, region):
    field = indices[source][f'{key}_{tag}'].where(common).rename({f'year_{tag}': 'year'})
    years = WINTERS if tag == 'djf' else (1985, 2014)
    return clim.regional_mean(field, region).sel(year=slice(*years))

INDEX = {('rx1day', 'ann'): 'wettest day of the year (mm)', ('rx1day', 'djf'): 'wettest winter day (mm)',
         ('r95p', 'djf'): 'winter very-wet-day rain, R95p (mm)', ('txx', 'ann'): 'hottest day of the year (°C)'}
rows = []
for s in REFS + ALL_RUNS:
    rows.append({'dataset': LABEL(s), 'source': s, **{label: float(regional(s, k, t, 'uk_ireland').mean()) for (k, t), label in INDEX.items()}})
uk = pd.DataFrame(rows).set_index('dataset')
uk.drop(columns='source')
""")

step("""
**What this cell does.** The same numbers as differences from E-OBS: percent for the rain indices,
°C for the hottest day.
""", """
reference = uk.loc[LABEL('e-obs')]
difference = uk.drop(columns='source').copy()
for column in difference.columns:
    difference[column] = (uk[column] - reference[column]) if '°C' in column else 100 * (uk[column] / reference[column] - 1)
difference.columns = [c + (' vs E-OBS (°C)' if '°C' in c else ' vs E-OBS (%)') for c in difference.columns]
difference
""")

step("""
**What this cell does.** Shows the winter R95p bias of every run as one dot per run, against the
two references.
""", """
column = 'winter very-wet-day rain, R95p (mm) vs E-OBS (%)'
groups = {m: difference.loc[[LABEL(s) for s in r], column].values for m, r in RUNS.items()}
plotting.plot_member_dots(groups, xlabel='winter R95p over UK and Ireland, relative to E-OBS (%), winters 1986-2014',
                          title='Very-wet-day rain bias of each run', reference=0.0, reference_label='E-OBS');
""")

md("""
**Figure 3.** One dot per run; dashed line: E-OBS (0%). ERA5 lies at about −12% on this scale.
""")

md("""
## 6. The NAO link to winter rain extremes
""")

step("""
**What this cell does.** For each region, rain index and dataset: the detrended correlation of the
land-average winter index with the winter NAO and its bootstrap 95% interval (notebook 06, section 10).
Each run uses its own NAO index; E-OBS and ERA5 use ERA5's.
""", """
rows = []
for region in regions.SUBREGIONS:
    for key in ('r95p', 'rx1day'):
        for s in REFS + ALL_RUNS:
            series = regional(s, key, 'djf', region)
            index = nao_index('era5' if s in REFS else s, WINTERS)
            years = np.intersect1d(series.year, index.year)
            check = rel.correlation_uncertainty(series.sel(year=years).values, index.sel(year=years).values, years=years)
            rows.append({'region': regions.LABELS[region], 'index': key.upper().replace('R95P', 'R95p').replace('RX1DAY', 'RX1day'),
                         'dataset': LABEL(s), 'source': s, 'r': check['r'], 'low': check['low'], 'high': check['high']})
link = pd.DataFrame(rows)
link.pivot_table(index=['region', 'index'], columns='dataset', values='r', sort=False)
""")

step("""
**What this cell does.** Draws the R95p correlations with their intervals for the three regions:
references first, then the three runs of each model.
""", """
for key in ('R95p', 'RX1day'):
    groups = {}
    for region in regions.SUBREGIONS:
        part = link[(link.region == regions.LABELS[region]) & (link['index'] == key)]
        groups[regions.LABELS[region]] = list(part[['source', 'r', 'low', 'high']].itertuples(index=False, name=None))
    plotting.plot_intervals(groups, xlabel='correlation with the winter NAO (bootstrap 95% interval)',
                            title=f'Winter {key} and the NAO in every run, 1986-2014');
""")

md("""
**Figures 4 and 5.** Dots: correlation over 29 winters; bars: bootstrap 95% interval; grey line:
zero. Upper figure R95p, lower RX1day. Compare the three dots of one model: if they scatter as
widely as their bars, the single-run result of version 1 was partly chance.
""")

md("""
## 7. How much of ICON-ESM-ER's wet bias the circulation explains, per run
""")

step("""
**What this cell does.** Repeats the decomposition test of notebook 06 (section 11) for every run:
observed change in winter R95p and RX1day per +1 SD of NAO (from E-OBS and from ERA5) times the
run's own mean circulation offset, compared with the run's actual bias over UK and Ireland land.
It also counts wet days and rain per wet day per run, as in notebook 06.
""", """
uk_box = regions.BOXES['uk_ireland']
inside = (grid.lon >= uk_box[0]) & (grid.lon <= uk_box[1]) & (grid.lat >= uk_box[2]) & (grid.lat <= uk_box[3])
def uk_mean(field):
    return float(regions.area_mean(field.where(common & inside)))

def winter_field(source, key):
    return indices[source][f'{key}_djf'].rename(year_djf='year').sel(year=slice(*WINTERS))

rows = []
for key in ('r95p', 'rx1day'):
    for ref in REFS:
        slope = rel.correlate(winter_field(ref, key), nao_index('era5', WINTERS)).slope
        for s in ALL_RUNS:
            bias = uk_mean(winter_field(s, key).mean('year') - winter_field(ref, key).mean('year'))
            expected = uk_mean(rel.circulation_part(slope, offset[s]))
            rows.append({'index': key, 'reference': LABEL(ref), 'run': LABEL(s), 'bias': bias,
                         'expected from circulation': expected, 'share %': 100 * expected / bias})
explained = pd.DataFrame(rows)
explained.pivot_table(index=['index', 'reference'], columns='run', values='share %', sort=False)
""")

step("""
**What this cell does.** Wet days per winter and rain per wet day over UK and Ireland land, for the
references and every run (1986–2014).
""", """
rows = []
for s in REFS + ALL_RUNS:
    daily = store.load(s, 'day', 'pr', 'nw_europe')
    daily = daily.sel(time=daily.time.dt.month.isin([12, 1, 2]))
    count, intensity = ex.wet_days(daily, 'DJF'), ex.wet_day_intensity(daily, 'DJF')
    if s == 'e-obs':
        count, intensity = regions.to_grid(count, grid), regions.to_grid(intensity, grid)
    rows.append({'dataset': LABEL(s), 'wet days per winter': uk_mean(count.sel(year=slice(*WINTERS)).mean('year')),
                 'rain per wet day (mm)': uk_mean(intensity.sel(year=slice(*WINTERS)).mean('year'))})
wet = pd.DataFrame(rows).set_index('dataset')
for ref in REFS:
    wet[f'wet days vs {LABEL(ref)} %'] = 100 * (wet['wet days per winter'] / wet.loc[LABEL(ref), 'wet days per winter'] - 1)
    wet[f'rain per wet day vs {LABEL(ref)} %'] = 100 * (wet['rain per wet day (mm)'] / wet.loc[LABEL(ref), 'rain per wet day (mm)'] - 1)
wet
""")

md("""
## 8. Which version 1 results hold?
""")

step("""
**What this cell does.** Collects, for each headline result of version 1, the value in r1 and the
range over the three runs, so that each can be classed as robust across the three runs or
sensitive to chance.
""", """
def span(values):
    return f'{min(values):.2f} to {max(values):.2f}'

def link_values(model, region, key):
    part = link[(link.region == regions.LABELS[region]) & (link['index'] == key)].set_index('source')
    return [part.r[s] for s in RUNS[model]]

rows = []
for m, runs in RUNS.items():
    strength = nao_table.set_index('source').loc[runs, 'NAO strength relative to ERA5'].tolist()
    rows += [
        {'model': LABEL(m).split()[0], 'result': 'NAO strength relative to ERA5', 'r1': strength[0], 'three runs': span(strength)},
        {'model': LABEL(m).split()[0], 'result': 'mean circulation offset (SD)', 'r1': offset[runs[0]], 'three runs': span([offset[s] for s in runs])},
        {'model': LABEL(m).split()[0], 'result': 'winter R95p bias vs E-OBS (%)', 'r1': difference.loc[LABEL(runs[0]), column],
         'three runs': span(difference.loc[[LABEL(s) for s in runs], column])},
    ]
    for region in regions.SUBREGIONS:
        values = link_values(m, region, 'R95p')
        rows.append({'model': LABEL(m).split()[0], 'result': f'NAO link to R95p, {regions.LABELS[region]}', 'r1': values[0], 'three runs': span(values)})
verdict = pd.DataFrame(rows)
verdict
""")

md("""
## 9. Saved outputs
""")

step("""
**What this cell does.** Saves the NAO table, the extremes table, the link table and the verdict
table to `app_assets/`, each with a JSON provenance file.
""", """
from eerie_uk import provenance
out = Path('../app_assets')
common_meta = dict(inputs={'pressure': 'data/<run>/mon/psl', 'extremes': 'data/derived/<run>_extremes_nw_europe.nc'},
                   runs=ALL_RUNS, nao_winters='1976-2014', extreme_winters='1986-2014')
provenance.write_table(nao_table, out / 'members_nao.parquet', 'NAO strength, EOF variance and pattern per historical run, winters 1976-2014', **common_meta)
provenance.write_table(uk.reset_index(), out / 'members_extremes_uk.parquet', 'UK and Ireland land-average extremes per run and reference', **common_meta)
provenance.write_table(link, out / 'members_nao_link.parquet', 'Detrended correlation of winter rain extremes with the NAO per run and region, bootstrap 95% interval', **common_meta)
provenance.write_table(verdict, out / 'members_verdict.parquet', 'Version 1 headline results: r1 value and range over three runs', **common_meta)
print('saved 4 tables')
""")

md("""
## 10. Limitations

- **Three runs are few.** Their range shows that chance can move a result; it does not give a full
  probability distribution. A result that agrees in three runs can still differ in a fourth.
  Notebook 11 uses the 100-year control runs for a fuller estimate of chance.
- **The r2 and r3 runs start in 1975,** so the NAO window here (39 winters) is shorter than in
  notebook 04 (64 winters); r1's numbers differ slightly from version 1 for that reason alone.
- **IFS-FESOM2-SR r3 misses 2–31 October 1999** (server data gap); winter results are unaffected.
- All other limitations of notebooks 04–06 apply (references, regridding, linear methods).
""")

md("""
## 11. Open questions

1. Is the spread between three runs representative of chance, or are the extra runs systematically
   different (for example because they start from a different ocean state)? Notebook 11 compares
   it with the control runs.
2. With ten or more runs per model, would the NAO link over UK and Ireland settle on one value, and
   would it match the observations?
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
