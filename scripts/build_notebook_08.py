"""Generate notebooks/08_resolution.ipynb.  Usage: python build_notebook_08.py OUT.ipynb [findings.md]"""
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
# 08 · Does higher resolution improve winter precipitation extremes?

**Question for this notebook.** Higher-resolution models cost much more to run. Do they represent
extreme precipitation better? And do the *conclusions* drawn from a model, such as how strongly the
NAO drives rainfall extremes, depend on its resolution?

**Why this pair of runs.** Comparing two different models (ICON-ESM-ER and IFS-FESOM2-SR) mixes
resolution with everything else that differs between them. Here the comparison is clean: the
**same** atmosphere model (IFS), with the **same** observed sea-surface temperature, run at about
**9 km** (tco1279) and about **28 km** (tco399). Only the resolution differs.

**Data.** Daily precipitation over north-west Europe, winters (December–February) 1986–2014,
29 winters:
- IFS at 9 km: one run.
- IFS at 28 km: three members (the first three of the five available, to limit the download).
- References: E-OBS (station-based, land) and ERA5 (reanalysis, about 31 km).

All four are compared on the same 0.25° grid (about 25 km). This matters: the 9 km run has been
averaged onto that grid, so detail finer than about 25 km is not visible here. The question is
therefore whether running at 9 km improves precipitation *at the 25 km scale*, which is the scale
at which the models are usually evaluated and used.

**How chance is judged.** The three 28 km members differ only by chance. A 9 km result counts as a
resolution effect only if it lies **outside the range of the three 28 km members**. With three
members that is a weak test, so only clear differences are reported as such.

**Sections**
1. Setup and data check
2. Findings
3. Winter-mean precipitation
4. The wettest winter day (RX1day)
5. The distribution of daily rainfall
6. Regional numbers
7. Which resolution is closer to the references?
8. Does the NAO-to-extremes conclusion depend on resolution?
9. Limitations
10. What to check
""")

md("""
## Background: the terms used in this notebook

| Term | What it means here |
|---|---|
| **Resolution** | The size of the model's grid boxes. 9 km boxes can represent mountains, coastlines and storms in more detail than 28 km boxes. |
| **tco1279, tco399** | ECMWF's names for the 9 km and 28 km grids of the IFS model. |
| **Atmosphere-only run** | The ocean is not simulated; observed sea-surface temperature is prescribed. Both runs see exactly the same ocean. |
| **Member** | One of several runs of the same experiment that differ only in tiny details of their starting state. Their differences show how large chance is. |
| **Member range** | The lowest to the highest value across the three 28 km members. |
| **RX1day, R95p** | The wettest day of the winter; the rain that falls on very wet days (above the local 95th percentile of wet days). As in notebook 05. |
| **Wet day** | A day with at least 1 mm. |
| **Quantile (percentile)** | The value below which a given share of wet days falls. The 99th percentile is exceeded on 1 wet day in 100. |
| **Pattern correlation, RMSE** | How similar the shape of two maps is (−1 to 1), and the typical size of their local differences. |

**Colours.** Purple: IFS 9 km. Green: IFS 28 km (one line or dot per member). Dark grey: ERA5.
Light grey: E-OBS. In difference maps, grey means no difference.
""")

md("## 1. Setup and data check")

step("""
**What this cell does.** Loads the project code and names the datasets.
""", """
import sys, warnings
sys.path.insert(0, '../src')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xarray as xr
from eerie_uk import climatology as clim, extremes as ex, nao, plotting, regions, relationships as rel, store

pd.set_option('display.width', 220, 'display.float_format', '{:.2f}'.format)
NAME = plotting.SOURCE_LABELS
HI, LO = 'ifs-amip-tco1279.hist', 'ifs-amip-tco399.hist'
REFS = ['e-obs', 'era5']
WINTERS = (1986, 2014)
""")

step("""
**What this cell does.** Loads the daily precipitation of the two IFS runs and keeps the winter
days. Each winter (December–February) is labelled by the year of its January; the first and last
incomplete winters are dropped by the index functions.
""", """
def winter_days(source):
    da = store.load(source, 'day', 'pr', 'nw_europe')
    return da.sel(time=da.time.dt.month.isin([12, 1, 2]))

hi = winter_days(HI)                      # (time, lat, lon)
lo = winter_days(LO)                      # (time, realization, lat, lon)
print('9 km :', dict(hi.sizes), hi.attrs.get('units'))
print('28 km:', dict(lo.sizes), 'members', list(lo.realization.values), lo.attrs.get('units'))
""")

step("""
**What this cell does.** Computes the winter indices for the two IFS runs: the winter mean, RX1day,
and R95p with a winter threshold from 1985–2014. For the references the same indices were already
computed in notebook 05 and are read from its cache. E-OBS is put on the model grid, and a land
mask is built: regional numbers use the same land cells (where E-OBS has data) for everyone.
""", """
def winter_indices(pr):
    threshold = ex.wet_day_threshold(pr, period='DJF')
    out = xr.Dataset({'rx1day': ex.rx1day(pr, 'DJF'), 'r95p': ex.r95p(pr, threshold, 'DJF'), 'p95': threshold})
    labels = ex.period_labels(pr.time, 'DJF')
    kept = pr.sel(time=(labels > 0).values)
    out['mean'] = kept.groupby(labels.sel(time=kept.time)).mean('time')
    return out.sel(year=slice(*WINTERS))

ind = {HI: winter_indices(hi), LO: winter_indices(lo)}
for r in REFS:
    cached = ex.indices_for(r)
    daily = winter_days(r)
    labels = ex.period_labels(daily.time, 'DJF')
    kept = daily.sel(time=(labels > 0).values)
    ind[r] = xr.Dataset({'rx1day': cached.rx1day_djf.rename(year_djf='year'), 'r95p': cached.r95p_djf.rename(year_djf='year'),
                         'p95': cached.p95_djf, 'mean': kept.groupby(labels.sel(time=kept.time)).mean('time')}).sel(year=slice(*WINTERS))
grid = ind[HI]
ind['e-obs'] = regions.to_grid(ind['e-obs'], grid)
land = regions.land_mask(grid.lat, grid.lon)
common = land & ind['e-obs'].rx1day.isel(year=0).notnull()
pd.DataFrame([{'dataset': NAME.get(k, k), 'winters': ind[k].sizes['year'], 'members': int(ind[k].sizes.get('realization', 1))} for k in (REFS + [HI, LO])])
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. Winter-mean precipitation
""")

step("""
**What this cell does.** Maps the average winter precipitation, 1986–2014, for the two references,
the 9 km run and the 28 km run (average of its three members).
""", """
def avg(key, var):
    field = ind[key][var].mean('year')
    return field.mean('realization') if 'realization' in field.dims else field
plotting.plot_field_panels({NAME.get(k, k): avg(k, 'mean') for k in REFS + [HI, LO]}, units='mm/day', columns=2,
                           title='Winter (DJF) mean precipitation, 1986-2014');
""")

md("""
**Figure 1.** Average winter precipitation. The 28 km panel is the mean of three members.
""")

step("""
**What this cell does.** Maps the 9 km run minus the 28 km run, as a percentage. Dots mark cells
where the 9 km value lies outside the range of the three 28 km members, that is, where the
difference is larger than what chance produces between 28 km runs.
""", """
def outside(key_hi, var):
    value = ind[key_hi][var].mean('year')
    members = ind[LO][var].mean('year')
    return (value > members.max('realization')) | (value < members.min('realization'))
panels = {f'{var}: 9 km vs 28 km': 100 * (avg(HI, var) - avg(LO, var)) / avg(LO, var) for var in ('mean', 'rx1day')}
plotting.plot_field_panels(panels, units='% difference', diverging=True, columns=2,
                           stipple={f'{var}: 9 km vs 28 km': outside(HI, var) for var in ('mean', 'rx1day')},
                           title='Winter precipitation and wettest winter day: 9 km relative to 28 km');
""")

md("""
**Figure 2.** Orange: wetter at 9 km than at 28 km; blue: drier. Left: winter-mean precipitation.
Right: the wettest winter day. Dots: outside the 28 km member range.
""")

md("""
## 4. The wettest winter day (RX1day)
""")

step("""
**What this cell does.** Maps the average wettest winter day for the references and both
resolutions.
""", """
plotting.plot_field_panels({NAME.get(k, k): avg(k, 'rx1day') for k in REFS + [HI, LO]}, units='mm', columns=2,
                           title='Winter RX1day, mean of 1986-2014');
""")

md("""
**Figure 3.** The wettest winter day. Look at the mountains (western Norway, Scotland, the Alps,
northern Iberia): this is where resolution should matter most, because higher resolution resolves
steeper terrain that forces air upwards.
""")

md("""
## 5. The distribution of daily rainfall
""")

step("""
**What this cell does.** Pools all winter wet days over the land of each region and computes the
amount below which 50%, 75%, 90%, 95%, 99% and 99.9% of them fall. The curves show the whole
heavy end of the distribution, not just a single index.
""", """
probabilities = np.array([0.5, 0.75, 0.9, 0.95, 0.99, 0.999])
def wet_quantiles(pr, region):
    box = regions.subset_box(pr.where(common), region)
    values = box.values.ravel()
    values = values[np.isfinite(values) & (values >= ex.WET_DAY)]
    return np.quantile(values, probabilities)

daily = {r: winter_days(r).sel(time=slice('1985-12-01', '2014-02-28')) for r in REFS}
daily['e-obs'] = regions.to_grid(daily['e-obs'], grid)
daily[HI] = hi.sel(time=slice('1985-12-01', '2014-02-28'))
quantiles = {}
for region in regions.SUBREGIONS:
    quantiles[region] = {r: wet_quantiles(daily[r], region) for r in REFS + [HI]}
    for m in lo.realization.values:
        quantiles[region][f'{LO}#{m}'] = wet_quantiles(lo.sel(realization=m).sel(time=slice('1985-12-01', '2014-02-28')), region)
x = np.arange(probabilities.size)      # evenly spaced, so the rare extremes are not squashed
plotting.plot_line_panels({regions.LABELS[r]: {k: (x, v) for k, v in quantiles[r].items()} for r in regions.SUBREGIONS},
                          ylabel='mm/day', xlabel='percentile of winter wet days',
                          title='How heavy are heavy winter rain days? Land, 1986-2014',
                          xticks=(list(x), ['50', '75', '90', '95', '99', '99.9']));
""")

md("""
**Figure 4.** Each line shows how heavy the wettest x% of winter wet days are. The three green
lines are the three 28 km members; their spread is chance. The x axis is not to scale: the last
points are the rare extremes.
""")

md("""
## 6. Regional numbers
""")

step("""
**What this cell does.** Averages each winter index over the land of each region (same cells for
all datasets), then over 1986–2014. For the 28 km run it shows the three members' lowest and
highest value. The last column says whether the 9 km value lies outside that range.
""", """
LABEL = {'mean': 'winter mean (mm/day)', 'rx1day': 'wettest winter day (mm)', 'r95p': 'rain on very wet days (mm)', 'p95': 'very-wet-day threshold (mm/day)'}
def regional(key, var, region):
    field = ind[key][var]
    if 'year' in field.dims:
        field = field.mean('year')
    return clim.regional_mean(field.where(common), region)
rows = []
for region in regions.SUBREGIONS:
    for var, label in LABEL.items():
        members = regional(LO, var, region)
        h = float(regional(HI, var, region))
        rows.append({'region': regions.LABELS[region], 'quantity': label,
                     'E-OBS': float(regional('e-obs', var, region)), 'ERA5': float(regional('era5', var, region)),
                     '9 km': h, '28 km lowest': float(members.min()), '28 km highest': float(members.max()),
                     '9 km outside 28 km range': bool(h < float(members.min()) or h > float(members.max())),
                     '9 km vs 28 km mean %': 100 * (h - float(members.mean())) / float(members.mean())})
regional_table = pd.DataFrame(rows)
regional_table
""")

md("""
## 7. Which resolution is closer to the references?
""")

step("""
**What this cell does.** Scores the maps of the winter mean and of RX1day against each reference
over land: RMSE (typical local error, lower is better) and pattern correlation (higher is better).
The 9 km run is scored once; each 28 km member separately, so the spread shows how much the score
itself varies by chance.
""", """
rows = []
for var in ('mean', 'rx1day', 'r95p'):
    for ref in REFS:
        reference = avg(ref, var).where(common)
        candidates = {'9 km': ind[HI][var].mean('year')}
        candidates.update({f'28 km member {int(m)}': ind[LO][var].mean('year').sel(realization=m) for m in ind[LO].realization.values})
        for label, field in candidates.items():
            stats = clim.pattern_stats(field.where(common), reference)
            rows.append({'quantity': LABEL[var], 'reference': NAME[ref], 'run': label,
                         'RMSE': stats['rmse'], 'pattern correlation': stats['pattern correlation'], 'mean bias': stats['bias']})
skill = pd.DataFrame(rows)
skill.pivot_table(index=['quantity', 'reference'], columns='run', values='RMSE')
""")

md("""
**How to read this table.** RMSE in the units of each quantity. The 9 km run is better than 28 km
only if its RMSE is lower than **all three** member values for that row.
""")

step("""
**What this cell does.** The same scores as pattern correlations.
""", """
skill.pivot_table(index=['quantity', 'reference'], columns='run', values='pattern correlation')
""")

md("""
## 8. Does the NAO-to-extremes conclusion depend on resolution?

Notebook 06 asked whether models reproduce the observed link between the winter NAO and winter
rainfall extremes. Here the same question is asked of both resolutions: would a scientist using
the 9 km run reach a different conclusion from one using the 28 km run?
""")

step("""
**What this cell does.** Builds the winter NAO index of each run and member from monthly pressure,
measured along the ERA5 NAO pattern (as in notebooks 04 and 07), and correlates it with the land
average of winter R95p in each region, after removing trends. ERA5 and E-OBS use the ERA5 NAO.
""", """
era5_eof = nao.leading_eof(nao.winter_anomalies(store.load('era5', 'mon', 'psl', 'north_atlantic')))
def nao_of(source):
    winters = nao.winter_anomalies(store.load(source, 'mon', 'psl', 'north_atlantic'), (1980, 2023))
    return (nao.project(winters, era5_eof.vector) / era5_eof.amplitude).sel(year=slice(*WINTERS))
era5_nao = (nao.project(nao.winter_anomalies(store.load('era5', 'mon', 'psl', 'north_atlantic')), era5_eof.vector) / era5_eof.amplitude).sel(year=slice(*WINTERS))
nao_hi, nao_lo = nao_of(HI), nao_of(LO)

def r95_series(key, region, member=None):
    field = ind[key]['r95p']
    if member is not None:
        field = field.sel(realization=member)
    return clim.regional_mean(field.where(common), region)

rows = []
for region in regions.SUBREGIONS:
    row = {'region': regions.LABELS[region]}
    for r in REFS:
        row[NAME[r]] = rel.regress_series(r95_series(r, region).values, era5_nao.sel(year=r95_series(r, region).year).values)['r']
    row['9 km'] = rel.regress_series(r95_series(HI, region).values, nao_hi.sel(year=r95_series(HI, region).year).values)['r']
    for m in ind[LO].realization.values:
        series = r95_series(LO, region, m)
        row[f'28 km member {int(m)}'] = rel.regress_series(series.values, nao_lo.sel(realization=m, year=series.year).values)['r']
    rows.append(row)
print('29 winters, detrended; a correlation above about 0.38 is significant at the 5% level')
link = pd.DataFrame(rows).set_index('region')
link
""")

md("""
**How to read this table.** If the 9 km value sits within the spread of the three 28 km members,
the conclusion about the NAO link does not depend on resolution in this model.
""")

md("""
## 9. Limitations

- **Three 28 km members, one 9 km run.** Only differences that clearly exceed the member range can
  be attributed to resolution. Smaller real effects would be missed.
- **Winter only.** The 28 km download was limited to winter to save network traffic.
- **Compared at 0.25°.** Both runs were regridded to about 25 km by the data provider, so any benefit
  of 9 km below that scale (for example in narrow valleys or convective cells) is not visible.
- **One model, one pair of resolutions.** The result is for IFS with prescribed SST, not for coupled
  models or for other modelling systems.
- **Complexity is not tested.** Only resolution changes between these runs.
- **References disagree somewhat** (notebook 05): E-OBS smooths station data, ERA5 is itself a
  model product at about 31 km.
""")

md("""
## 10. What to check

1. **Figure 2 and the regional table:** where does 9 km differ from 28 km by more than chance?
2. **Section 7:** is 9 km closer to both references, to one, or to neither?
3. **Section 8:** does the NAO-to-extremes conclusion change with resolution?
4. **Wording of the findings:** is the answer to "does resolution help" stated with the right caution?
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
