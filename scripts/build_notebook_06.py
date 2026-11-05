"""Generate notebooks/06_nao_extremes.ipynb.  Usage: python build_notebook_06.py OUT.ipynb [findings.md]"""
import glob
import os
import sys
import nbformat as nbf

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "era5", "day")
HAVE_ERA5 = all(len(glob.glob(os.path.join(_DATA, f"{v}_nw_europe_*.nc"))) == 30 for v in ("pr", "tasmax"))
REFS = ["e-obs", "era5"] if HAVE_ERA5 else ["e-obs"]

ERA5_NOTE = """
> **Note on ERA5 daily data.** When this notebook was last run, the ERA5 *daily* files were not yet
> available, so E-OBS is the only reference here.
> E-OBS is the more direct reference for extremes over land in any case. The notebook picks up
> ERA5 automatically, as a second reference, once `data/era5/day/` holds all 30 years: just run it again.
"""

FINDINGS = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else "_Written after the first run._"

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def step(explain, source):
    cells.append(nbf.v4.new_markdown_cell(explain.strip("\n")))
    cells.append(nbf.v4.new_code_cell(source.strip("\n")))


md("""
# 06 · From the NAO to winter extremes

**Question for this notebook.** In the real world, a positive winter NAO brings stronger westerly
winds: milder and wetter weather to northern Europe, drier weather to the south. Do the two EERIE
models reproduce that link for winter *extremes* (the wettest day, the rain on very wet days, the
mildest day), with the right sign, pattern and strength?

This is the centrepiece of the project: it connects the large-scale circulation (notebook 04) to
the regional extremes (notebook 05).

**Data.** 29 winters, 1986–2014 (the winters that have daily data).
- NAO index per winter, from notebook 04.
- Winter RX1day, winter R95p and winter TXx at every grid cell, from notebook 05.
- Four datasets: ERA5 (reanalysis reference), E-OBS (station-based, land only), ICON-ESM-ER and
  IFS-FESOM2-SR.

**Which NAO goes with which extremes.** Each model's extremes are related to *that model's own* NAO
winters. ERA5 and E-OBS extremes are both related to the ERA5 NAO, because they describe the same
real winters.

**Method** (fixed in `docs/methods.md` before any result was produced):
1. Remove the straight-line trend from both the NAO index and the extreme index, so that a shared
   long-term drift (for example warming) cannot masquerade as an NAO effect.
2. At every grid cell, compute the correlation with the NAO and the regression slope: the change
   in the extreme index per one standard deviation of NAO.
3. Test each cell (two-sided t-test) and then apply false-discovery-rate control across all cells,
   so that the map is not littered with chance "significant" dots.
4. As a simpler cross-check, compare the ten most positive with the ten most negative NAO winters.

**The NAO index used.** Notebook 04 showed that ICON-ESM-ER's own leading pressure pattern is a
mixture and not a clean NAO. So the main analysis measures every dataset along the *same* pattern,
the ERA5 NAO pattern, in units of the ERA5 standard deviation. Section 8 repeats the key numbers
with two other index definitions to show how much the choice matters.

**Sections**
1. Setup
2. Findings
3. The sample: 29 winters
4. Context: the NAO and ordinary winter rainfall
5. NAO and the wettest winter day (RX1day)
6. NAO and rain on very wet winter days (R95p)
7. NAO and the mildest winter day (TXx)
8. Regional numbers for UK and Ireland, and sensitivity to the index definition
9. Positive against negative NAO winters
10. How certain are the regional correlations?
11. How much of ICON-ESM-ER's wet bias does its circulation explain?
12. Saved outputs
13. Limitations
14. Open questions
""")

md("""
## Background: the terms used in this notebook

If you know these already, skip to section 1.

| Term | What it means here |
|---|---|
| **Correlation (r)** | How consistently two things vary together from winter to winter, from −1 to +1. r = +0.6 between NAO and RX1day at a place means wet-extreme winters there tend to be positive-NAO winters. It says nothing about how big the effect is. |
| **Regression slope** | How big the effect is: the change in the extreme index for a one-standard-deviation increase in the NAO. For example "+4 mm per SD". |
| **Per 1 SD of NAO** | One standard deviation of the ERA5 winter NAO index, the same yardstick for every dataset. A typical positive winter is about +1 SD. |
| **Detrending** | Subtracting the best-fit straight line over 1986–2014 from each series before correlating them. |
| **p value** | The probability of seeing a correlation at least this strong purely by chance if there were no real link. Small is convincing; below 0.05 is the usual threshold. |
| **Multiple testing** | A map has thousands of grid cells. Testing each at the 5% level would flag about 5% of them even if the NAO had no effect anywhere. |
| **False-discovery-rate (FDR) control** | A standard correction for that problem (Benjamini–Hochberg; recommended for climate maps by Wilks 2016). It raises the bar so that, among the cells finally marked, only a small expected share (here 10%) are false alarms. Dots on the maps mark cells that pass it. |
| **Composite** | The average over a group of winters. "NAO+ minus NAO−" is the average of the ten most positive winters minus the average of the ten most negative. |
| **Bootstrap interval** | An uncertainty range obtained by re-drawing the winters many times at random. If the range excludes zero, the difference is unlikely to be chance. |
| **Pattern correlation** | How similar the shapes of two maps are, from −1 to 1. Used here to ask: does the model's NAO-response map look like the reference's? |

**How to read the maps.** All maps in this notebook show a *response to the NAO*. Orange means the
index goes **up** in positive-NAO winters, blue means it goes **down**, grey means no link.
Small dots mark grid cells where the link passes the significance test with FDR control.
All panels of one figure share one colour scale. E-OBS is blank over sea.

**Colours of the points and lines.** Dark grey ERA5, light grey E-OBS, blue ICON-ESM-ER, orange
IFS-FESOM2-SR.
""")

if not HAVE_ERA5:
    md(ERA5_NOTE)

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code. The statistics are in `eerie_uk/relationships.py`;
each function has a unit test on synthetic data where the true answer is known.
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
MODELS = ['icon-esm-er', 'ifs-fesom2-sr']
""" + f"REFS = {REFS!r}" + """      # reference datasets
DATASETS = REFS + MODELS
NAO_OF = {'e-obs': 'era5', 'era5': 'era5', 'icon-esm-er': 'icon-esm-er', 'ifs-fesom2-sr': 'ifs-fesom2-sr'}
NAME = plotting.SOURCE_LABELS
WINTERS = (1986, 2014)
""")

step("""
**What this cell does.** Loads the two inputs: the winter NAO indices saved by notebook 04 and the
gridded winter extreme indices cached by notebook 05. E-OBS is put on the model grid, and a land
mask is built for land-only statistics.
""", """
nao_table = pd.read_parquet('../app_assets/nao_index_winter.parquet')

def nao_index(source, column='nao_on_era5_pattern'):
    part = nao_table[(nao_table.source == source) & nao_table.year.between(*WINTERS)]
    return xr.DataArray(part[column].values, coords={'year': part.year.values}, dims='year')

indices = {d: ex.indices_for(d) for d in DATASETS}
grid = indices['icon-esm-er']
indices['e-obs'] = regions.to_grid(indices['e-obs'], grid)
land = regions.land_mask(grid.lat, grid.lon)

def winter_field(dataset, name):
    return indices[dataset][f'{name}_djf'].rename(year_djf='year')

print('winters:', WINTERS[0], 'to', WINTERS[1], '=', nao_index('era5').size)
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. The sample: 29 winters

Everything below rests on 29 winters per dataset. That is a small sample for a noisy link, and it
is stated here once: with 29 winters and detrended series, a correlation needs to exceed about
±0.38 to pass an ordinary 5% test at a single place, and more than that after FDR control.
""")

step("""
**What this cell does.** Describes the NAO sample of each dataset over these 29 winters: the spread
of the index (in ERA5 standard deviations), and the index range of the ten most positive and ten
most negative winters used later for composites.
""", """
rows = []
for s in ('era5',) + tuple(MODELS):
    series = nao_index(s).to_series()
    rows.append({'NAO from': NAME[s], 'winters': series.size, 'standard deviation': series.std(),
                 'most positive': series.max(), 'most negative': series.min(),
                 'mean of top 10': series.nlargest(10).mean(), 'mean of bottom 10': series.nsmallest(10).mean()})
pd.DataFrame(rows)
""")

md("""
**Why the standard deviations differ.** The index is in ERA5 units. A model whose NAO is weaker
than ERA5's (notebook 04) has a standard deviation below 1 here. Its NAO winters are therefore
less extreme, and the *same* slope per SD produces smaller winter-to-winter swings in that model.
""")

md("""
## 4. Context: the NAO and ordinary winter rainfall

Before extremes, the textbook link: a positive NAO makes the whole winter wetter in the north and
drier in the south. If a model does not show this, there is little point asking about extremes.
""")

step("""
**What this cell does.** Regresses winter-mean precipitation (from the monthly data) on the NAO at
every grid cell, for ERA5 and the two models. Dots mark cells that pass the FDR-controlled test.
""", """
context, context_mask = {}, {}
for s in ('era5',) + tuple(MODELS):
    winter_pr = clim.season_means(store.load(s, 'mon', 'pr', 'nw_europe'), 'DJF').sel(year=slice(*WINTERS))
    result = rel.correlate(winter_pr, nao_index(s))
    context[NAME[s]] = result.slope
    context_mask[NAME[s]] = rel.fdr_mask(result.p)
plotting.plot_field_panels(context, units='mm/day per +1 SD of NAO', diverging=True, stipple=context_mask,
                           title='Change in winter-mean precipitation per +1 SD of NAO, 1986-2014');
""")

md("""
**Figure 1.** The response of ordinary winter rainfall to the NAO. Orange: wetter in positive-NAO
winters; blue: drier. The expected picture is orange over Scotland, Norway and the northern seas
and blue over Iberia and the Mediterranean, with the dividing line near 50°N.
""")

step("""
**What this cell does.** Defines the function used for the three extreme indices below. For one
index it computes, for each of the four datasets, the correlation map, the slope map and the
FDR-significant cells, and collects summary numbers: the share of land cells that are significant
and how closely each model's response map resembles each reference's (pattern correlation, land).
""", """
def analyse(name):
    out = {}
    for d in DATASETS:
        result = rel.correlate(winter_field(d, name), nao_index(NAO_OF[d]))
        result['significant'] = rel.fdr_mask(result.p)
        out[d] = result
    return out

def summarise(results):
    rows = []
    for d in DATASETS:
        r = results[d]
        row = {'dataset': NAME[d], 'land cells significant %': 100 * float(r.significant.where(land).mean()),
               'mean |r| over land': float(abs(r.r).where(land).mean())}
        for ref in REFS:
            both = land & r.slope.notnull() & results[ref].slope.notnull()
            row[f'pattern correlation with {NAME[ref]}'] = clim.pattern_stats(r.slope.where(both), results[ref].slope.where(both))['pattern correlation']
        rows.append(row)
    return pd.DataFrame(rows)

def maps(results, variable, units, title, limit=None):
    plotting.plot_field_panels({NAME[d]: results[d][variable] for d in DATASETS}, units=units, title=title, columns=2,
                               diverging=True, stipple={NAME[d]: results[d].significant for d in DATASETS}, limit=limit)
""")

md("""
## 5. NAO and the wettest winter day (RX1day)
""")

step("""
**What this cell does.** Maps the correlation between the winter NAO and winter RX1day for the four
datasets. The colour scale is fixed at ±1.
""", """
rx = analyse('rx1day')
maps(rx, 'r', 'correlation with the NAO', 'Winter RX1day and the NAO: correlation, 1986-2014', limit=1.0)
""")

md("""
**Figure 2.** Correlation of the wettest winter day with the NAO. Orange: the wettest day tends to
be wetter in positive-NAO winters. Dots: significant after FDR control. Reference dataset(s) first, then the two models.
""")

step("""
**What this cell does.** Maps the size of the effect: the change in winter RX1day, in mm, per +1 SD
of NAO.
""", """
maps(rx, 'slope', 'mm per +1 SD of NAO', 'Winter RX1day: change per +1 SD of NAO')
""")

md("""
**Figure 3.** Size of the NAO effect on the wettest winter day. Compare the model panels with the
reference: same places, same sign, similar strength?
""")

step("""
**What this cell does.** Summarises the four maps in numbers.
""", """
rx_summary = summarise(rx)
rx_summary
""")

md("""
## 6. NAO and rain on very wet winter days (R95p)
""")

step("""
**What this cell does.** The same correlation map for winter R95p: the rain that falls on days
above the local very-wet-day threshold.
""", """
r95 = analyse('r95p')
maps(r95, 'r', 'correlation with the NAO', 'Winter R95p and the NAO: correlation, 1986-2014', limit=1.0)
""")

md("""
**Figure 4.** Correlation of very-wet-day rainfall with the NAO. R95p adds up several days per
winter, so it is less noisy than the single wettest day and usually shows the NAO more clearly.
""")

step("""
**What this cell does.** The size of the effect, in mm of very-wet-day rain per winter per +1 SD of
NAO, and the summary numbers.
""", """
maps(r95, 'slope', 'mm per winter per +1 SD of NAO', 'Winter R95p: change per +1 SD of NAO')
r95_summary = summarise(r95)
r95_summary
""")

md("""
**Figure 5.** Size of the NAO effect on very-wet-day rainfall.
""")

md("""
## 7. NAO and the mildest winter day (TXx)
""")

step("""
**What this cell does.** The correlation map for winter TXx: the highest daily maximum temperature
of the winter.
""", """
tx = analyse('txx')
maps(tx, 'r', 'correlation with the NAO', 'Winter TXx and the NAO: correlation, 1986-2014', limit=1.0)
""")

md("""
**Figure 6.** Correlation of the mildest winter day with the NAO. A positive NAO brings mild
Atlantic air into northern Europe, so orange is expected there.
""")

step("""
**What this cell does.** The size of the effect, in °C per +1 SD of NAO, and the summary numbers.
""", """
maps(tx, 'slope', '°C per +1 SD of NAO', 'Winter TXx: change per +1 SD of NAO')
tx_summary = summarise(tx)
tx_summary
""")

md("""
**Figure 7.** Size of the NAO effect on the mildest winter day.
""")

md("""
## 8. Regional numbers for UK and Ireland, and sensitivity to the index definition
""")

step("""
**What this cell does.** Moves from maps to the headline region. It takes the land-average winter
series saved by notebook 05 and, for each dataset and index, computes the correlation with the NAO,
the slope per SD with its 95% range, and the p value. Western Norway and north-west France are
included as supporting regions on the wet and dry sides of the NAO.
""", """
regional = pd.read_parquet('../app_assets/extremes_regional.parquet')
regional = regional[(regional.period == 'winter') & regional.year.between(*WINTERS)]
INDEX_LABELS = {'rx1day': 'RX1day (mm)', 'r95p': 'R95p (mm)', 'txx': 'TXx (°C)'}

def regional_link(column='nao_on_era5_pattern'):
    rows = []
    for region in regions.SUBREGIONS:
        for key, label in INDEX_LABELS.items():
            for d in DATASETS:
                part = regional[(regional.region == region) & (regional['index'] == key) & (regional.source == d)].sort_values('year')
                fit = rel.regress_series(part.value.values, nao_index(NAO_OF[d], column).sel(year=part.year.values).values)
                rows.append({'region': regions.LABELS[region], 'index': label, 'dataset': NAME[d], **fit})
    return pd.DataFrame(rows)

link = regional_link()
link[link.region == 'UK and Ireland'].drop(columns='region').reset_index(drop=True)
""")

md("""
**How to read this table.** `r` is the correlation, `slope` the change per +1 SD of NAO, `low` and
`high` its 95% range, `p` the p value. If the range from `low` to `high` includes 0, the link is
not distinguishable from chance in 29 winters.
""")

step("""
**What this cell does.** Shows the same thing as pictures for UK and Ireland winter R95p: one dot
per winter, NAO on the horizontal axis, with the fitted line. A steep, tight cloud means a strong,
consistent link.
""", """
panels = {}
for d in DATASETS:
    part = regional[(regional.region == 'uk_ireland') & (regional['index'] == 'r95p') & (regional.source == d)].sort_values('year')
    panels[NAME[d]] = (d, nao_index(NAO_OF[d]).sel(year=part.year.values).values, part.value.values)
plotting.plot_scatter_panels(panels, xlabel='winter NAO (ERA5 SD)', ylabel='winter R95p (mm)',
                             title='UK and Ireland, land average: winter R95p against the NAO, 1986-2014');
""")

md("""
**Figure 8.** Each dot is one winter. The lines are fitted without detrending, for display only;
the table above uses detrended series.
""")

step("""
**What this cell does.** The supporting regions.
""", """
link[link.region != 'UK and Ireland'].reset_index(drop=True)
""")

step("""
**What this cell does.** A sensitivity test. It repeats the UK and Ireland correlations with two
other definitions of the NAO index: each dataset's *own* leading pattern, and the simple
station-style index (Azores minus Iceland pressure). If a conclusion holds under all three
definitions it does not depend on the choice made in this notebook.
""", """
alternatives = {'along the ERA5 pattern (main)': 'nao_on_era5_pattern', 'own leading pattern': 'nao_own_pattern', 'station-style': 'nao_station_style'}
table = pd.concat({label: regional_link(column).query("region == 'UK and Ireland'").set_index(['index', 'dataset']).r
                   for label, column in alternatives.items()}, axis=1)
table
""")

md("""
## 9. Positive against negative NAO winters

A simpler view that needs no straight-line assumption: the ten most positive NAO winters minus the
ten most negative.
""")

step("""
**What this cell does.** For UK and Ireland (land average), computes the difference in each winter
extreme index between the ten most positive and the ten most negative NAO winters of each dataset,
with a bootstrap 95% range.
""", """
rows = []
for key, label in INDEX_LABELS.items():
    for d in DATASETS:
        part = regional[(regional.region == 'uk_ireland') & (regional['index'] == key) & (regional.source == d)].sort_values('year')
        result = rel.composite_interval(part.value.values, nao_index(NAO_OF[d]).sel(year=part.year.values).values)
        rows.append({'index': label, 'dataset': NAME[d], 'NAO+ minus NAO-': result['difference'], 'low': result['low'], 'high': result['high'],
                     'range excludes zero': bool(result['low'] > 0 or result['high'] < 0)})
composites = pd.DataFrame(rows)
composites
""")

step("""
**What this cell does.** Maps the same composite difference for winter R95p at every grid cell, to
check that the composite picture agrees with the regression maps of section 6.
""", """
plotting.plot_field_panels({NAME[d]: rel.composite(winter_field(d, 'r95p'), nao_index(NAO_OF[d])) for d in DATASETS},
                           units='mm per winter', columns=2, diverging=True,
                           title='Winter R95p: ten most positive minus ten most negative NAO winters');
""")

md("""
**Figure 9.** Composite difference in very-wet-day rainfall. Each model's composite uses that
model's own ten most positive and ten most negative winters, which are less extreme than ERA5's
if its NAO is weaker.
""")

md("""
## 10. How certain are the regional correlations?

The comparisons above rest on correlations from 29 winters: for example 0.60 in IFS-FESOM2-SR
against 0.51 in E-OBS and 0.35 in ERA5 for UK and Ireland R95p. Before reading anything into such
differences, three checks:

1. **Bootstrap interval.** Draw 29 winters at random with replacement, keeping each winter's NAO
   and extreme value together, recompute the correlation, and repeat 5000 times. The middle 95% of
   the results is the interval.
2. **Leave one winter out.** Recompute the correlation 29 times, each time without one winter. If
   one exceptional winter (for example 2010 or 1989) carried the result, this shows it.
3. **Memory between winters.** If both series had year-to-year memory, the 29 winters would not be
   29 independent pieces of information. The effective number of winters (Bretherton et al. 1999)
   uses the lag-1 autocorrelations of both series; the p value is recomputed with it.

All series are detrended, as before.
""")

step("""
**What this cell does.** Runs the three checks for every region, rainfall index and dataset, and
shows the UK and Ireland rows.
""", """
rows = []
for region in regions.SUBREGIONS:
    for key in ('rx1day', 'r95p'):
        for d in DATASETS:
            part = regional[(regional.region == region) & (regional['index'] == key) & (regional.source == d)].sort_values('year')
            check = rel.correlation_uncertainty(part.value.values, nao_index(NAO_OF[d]).sel(year=part.year.values).values,
                                                years=part.year.values)
            rows.append({'region': regions.LABELS[region], 'index': INDEX_LABELS[key], 'dataset': NAME[d], 'source': d, **check})
certainty = pd.DataFrame(rows)
certainty[certainty.region == 'UK and Ireland'].drop(columns=['region', 'source']).reset_index(drop=True)
""")

md("""
**How to read this table.** `low` and `high` bound the bootstrap 95% interval of the correlation
`r`. The next two columns give the range of `r` when any one winter is left out, then the single
most influential winter and the correlation without it. `effective winters` is the sample size
after allowing for memory between winters, and `p (effective)` the p value that uses it.
""")

step("""
**What this cell does.** Draws the correlations and their intervals for the three regions, R95p
first. Where two intervals overlap widely, 29 winters cannot tell the two values apart.
""", """
for key in ('r95p', 'rx1day'):
    groups = {}
    for region in regions.SUBREGIONS:
        part = certainty[(certainty.region == regions.LABELS[region]) & (certainty['index'] == INDEX_LABELS[key])]
        groups[regions.LABELS[region]] = list(part[['source', 'r', 'low', 'high']].itertuples(index=False, name=None))
    plotting.plot_intervals(groups, xlabel='correlation with the winter NAO (bootstrap 95% interval)',
                            title=f'Winter {INDEX_LABELS[key].split()[0]} and the NAO: correlation and its uncertainty, 1986-2014');
""")

md("""
**Figures 10 and 11.** Dots: correlation over 29 winters. Bars: bootstrap 95% interval. The grey
line is zero. Upper figure R95p, lower figure RX1day.
""")

step("""
**What this cell does.** Tests whether each model's correlation differs from each reference's by
more than chance (Fisher z test for two independent samples of 29 winters). The two references
describe the *same* winters, so they are not independent of each other and are not tested against
each other this way.
""", """
rows = []
for region in regions.SUBREGIONS:
    for key in ('rx1day', 'r95p'):
        part = certainty[(certainty.region == regions.LABELS[region]) & (certainty['index'] == INDEX_LABELS[key])].set_index('source')
        for m in MODELS:
            row = {'region': regions.LABELS[region], 'index': INDEX_LABELS[key], 'model': NAME[m], 'model r': part.r[m]}
            for ref in REFS:
                row[f'{NAME[ref]} r'] = part.r[ref]
                row[f'p, model vs {NAME[ref]}'] = rel.correlation_difference(part.r[m], 29, part.r[ref], 29)
            rows.append(row)
differences = pd.DataFrame(rows)
differences
""")

md("""
**How to read this table.** A small p value (below 0.05) means the model's correlation is
distinguishable from that reference's in 29 winters. A large p value means the two correlations
are consistent with each other within sampling uncertainty, not that they are equal.
""")

md("""
## 11. How much of ICON-ESM-ER's wet bias does its circulation explain?

Notebooks 03 to 05 suggested a chain for ICON-ESM-ER: its average winter circulation looks like a
permanently positive NAO (notebook 04: +2.3 SD over 1951–2014), and positive-NAO winters are wet
winters over UK and Ireland, so the shifted circulation should make the model too wet. Until now
that chain is an argument. This section puts a number on it.

**The test.** The observed regression maps of sections 5 and 6 say how much RX1day and R95p change
per +1 SD of NAO in the real world. Multiplying them by the model's mean circulation offset (in
the same NAO units) gives the bias the model *would* have if its only error were that offset:

> expected bias from circulation = observed change per SD of NAO × model's mean NAO offset

Comparing that with the actual bias shows how much of the bias the circulation can account for.
The same is done for IFS-FESOM2-SR as a control: its offset is small, so little should be
explained.

**What this is not.** The response is assumed to be linear, and ICON-ESM-ER's offset lies beyond
most ordinary NAO winters, so the number is an extrapolation. A match shows that the bias is
*consistent with* the circulation offset; it does not prove the offset causes it, and a shortfall
points to other causes (how the model makes rain, its resolution, its orography).
""")

step("""
**What this cell does.** Computes each model's mean circulation offset for the winters used here
(1986–2014): the difference between its average winter sea-level pressure and ERA5's, projected
onto the ERA5 NAO pattern and expressed in ERA5 standard deviations, exactly as in notebook 04.
""", """
psl = {s: store.load(s, 'mon', 'psl', 'north_atlantic') for s in ('era5',) + tuple(MODELS)}
era5_nao = nao.leading_eof(nao.winter_anomalies(psl['era5']))
mean_psl = {s: clim.season_means(psl[s], 'DJF').sel(year=slice(*WINTERS)).mean('year') for s in psl}
offset = {m: nao.project_map(mean_psl[m] - mean_psl['era5'], era5_nao.vector) / era5_nao.amplitude for m in MODELS}
pd.Series({NAME[m]: v for m, v in offset.items()}, name='mean circulation offset, 1986-2014 (ERA5 NAO SD)').to_frame()
""")

step("""
**What this cell does.** For winter RX1day and R95p and each reference, computes the actual mean
bias of each model and the part expected from its circulation offset. It then summarises them over
UK and Ireland land (the same land cells for every dataset) and compares their maps over the land
of north-west Europe.
""", """
common = land & winter_field('e-obs', 'rx1day').isel(year=0).notnull()
uk = regions.BOXES['uk_ireland']

def uk_mean(field):
    inside = (field.lon >= uk[0]) & (field.lon <= uk[1]) & (field.lat >= uk[2]) & (field.lat <= uk[3])
    return float(regions.area_mean(field.where(common & inside)))

explained_rows, explained_maps = [], {}
for key in ('rx1day', 'r95p'):
    for ref in REFS:
        slope = (rx if key == 'rx1day' else r95)[ref].slope
        reference_mean = winter_field(ref, key).sel(year=slice(*WINTERS)).mean('year')
        for m in MODELS:
            bias = winter_field(m, key).sel(year=slice(*WINTERS)).mean('year') - reference_mean
            expected = rel.circulation_part(slope, offset[m])
            both = common & bias.notnull() & expected.notnull()
            explained_maps[(key, ref, m)] = (bias.where(common), expected.where(common))
            explained_rows.append({
                'index': INDEX_LABELS[key], 'reference': NAME[ref], 'model': NAME[m],
                'UK and Ireland bias': uk_mean(bias), 'expected from circulation': uk_mean(expected),
                'share explained %': 100 * uk_mean(expected) / uk_mean(bias),
                'pattern correlation (land)': clim.pattern_stats(expected.where(both), bias.where(both))['pattern correlation'],
            })
explained = pd.DataFrame(explained_rows)
explained
""")

md("""
**How to read this table.** `UK and Ireland bias` is the model's average winter value minus the
reference's (mm), `expected from circulation` the part its circulation offset would produce, and
`share explained` the ratio of the two. `pattern correlation` says whether the expected bias has
the same *geography* as the actual bias across north-west European land (1 = same shape).
""")

step("""
**What this cell does.** Maps the actual winter R95p bias of ICON-ESM-ER against E-OBS next to the
part expected from its circulation offset, and the remainder (actual minus expected), all on one
colour scale.
""", """
bias, expected = explained_maps[('r95p', 'e-obs', 'icon-esm-er')]
plotting.plot_field_panels({'actual bias': bias, 'expected from circulation offset': expected, 'remainder': bias - expected},
                           units='mm per winter', diverging=True,
                           title='ICON-ESM-ER winter R95p bias against E-OBS: actual, expected from its circulation, remainder');
""")

md("""
**Figure 12.** Left: ICON-ESM-ER's winter very-wet-day rain minus E-OBS. Middle: the bias its mean
circulation offset alone would produce, using the observed NAO response. Right: what is left. Where
the right panel is still strongly orange, something other than the large-scale circulation makes
the model too wet.
""")

step("""
**What this cell does.** A sensitivity test: repeats the UK and Ireland estimate with the
*model's own* NAO response instead of the observed one. If the two estimates agree, the answer does
not depend on which response is assumed.
""", """
rows = []
for key in ('rx1day', 'r95p'):
    own = (rx if key == 'rx1day' else r95)['icon-esm-er'].slope
    for ref in REFS:
        actual = explained[(explained.model == NAME['icon-esm-er']) & (explained.reference == NAME[ref]) & (explained['index'] == INDEX_LABELS[key])]
        rows.append({'index': INDEX_LABELS[key], 'reference': NAME[ref], 'UK and Ireland bias': float(actual['UK and Ireland bias'].iloc[0]),
                     'expected, observed response': float(actual['expected from circulation'].iloc[0]),
                     'expected, ICON-ESM-ER own response': uk_mean(rel.circulation_part(own, offset['icon-esm-er']))})
pd.DataFrame(rows)
""")

step("""
**What this cell does.** Asks where the remaining wet bias comes from. Winter rain on wet days is
the number of wet days (at least 1 mm) times the average rain per wet day. The cell computes both,
for every dataset, over UK and Ireland land, 1986–2014: a model that rains too *often* has too
many wet days; a model that rains too *hard* has too much rain per wet day.
""", """
rows = []
for d in DATASETS:
    daily = store.load(d, 'day', 'pr', 'nw_europe')
    daily = daily.sel(time=daily.time.dt.month.isin([12, 1, 2]))
    count, intensity = ex.wet_days(daily, 'DJF'), ex.wet_day_intensity(daily, 'DJF')
    if d == 'e-obs':
        count, intensity = regions.to_grid(count, grid), regions.to_grid(intensity, grid)
    rows.append({'dataset': NAME[d],
                 'wet days per winter': uk_mean(count.sel(year=slice(*WINTERS)).mean('year')),
                 'rain per wet day (mm)': uk_mean(intensity.sel(year=slice(*WINTERS)).mean('year'))})
wet = pd.DataFrame(rows).set_index('dataset')
for ref in REFS:
    wet[f'wet days vs {NAME[ref]} %'] = 100 * (wet['wet days per winter'] / wet.loc[NAME[ref], 'wet days per winter'] - 1)
    wet[f'rain per wet day vs {NAME[ref]} %'] = 100 * (wet['rain per wet day (mm)'] / wet.loc[NAME[ref], 'rain per wet day (mm)'] - 1)
wet
""")

md("""
**How to read this table.** The percentage columns compare each dataset with each reference.
Positive values in both "wet days" and "rain per wet day" mean the dataset rains both too often
and too hard.
""")

md("""
## 12. Saved outputs
""")

step("""
**What this cell does.** Saves the regional link table, the composite table, the uncertainty table and the circulation table to `app_assets/`
for the dashboard and the summary notebook, each with a JSON provenance file (code version, date,
inputs, period).
""", """
out = Path('../app_assets')
from eerie_uk import provenance
inputs = {'nao_index': 'app_assets/nao_index_winter.parquet', 'extremes': 'app_assets/extremes_regional.parquet'}
common = dict(inputs=inputs, period='winters 1986-2014', method='docs/methods.md section 5', nao_index='nao_on_era5_pattern')
provenance.write_table(link, out / 'nao_extremes_regional_link.parquet', 'Detrended correlation and regression of land-average winter extremes on the winter NAO, per region and dataset', **common)
provenance.write_table(composites, out / 'nao_extremes_composites.parquet', 'UK and Ireland winter extremes: ten most positive minus ten most negative NAO winters, bootstrap 95% range', **common)
summary = pd.concat({'RX1day': rx_summary, 'R95p': r95_summary, 'TXx': tx_summary}, names=['index']).reset_index(level=0)
provenance.write_table(certainty.drop(columns='source'), out / 'nao_extremes_correlation_uncertainty.parquet', 'Regional correlations of winter rainfall extremes with the NAO: bootstrap 95% interval, leave-one-winter-out range, effective sample size', **common)
provenance.write_table(wet.reset_index(), out / 'wet_day_frequency_intensity.parquet', 'UK and Ireland land, winters 1986-2014: wet days per winter and rain per wet day, with differences from each reference', **common)
provenance.write_table(explained, out / 'circulation_explained_bias.parquet', 'Winter rainfall-extreme bias over UK and Ireland and the part expected from the mean circulation offset (observed NAO response x offset)', **common, offsets={NAME[m]: round(v, 3) for m, v in offset.items()})
provenance.write_table(summary, out / 'nao_extremes_map_summary.parquet', 'Map summaries of the NAO link per index and dataset: share of significant land cells (FDR), mean |r|, pattern correlation with references', **common)
print('saved', len(link), 'regional rows,', len(composites), 'composite rows,', len(summary), 'map-summary rows,',
      len(certainty), 'uncertainty rows,', len(explained), 'circulation rows')
summary.reset_index(drop=True)
""")

md("""
## 13. Limitations

- **29 winters and one member per model.** This is the main limitation. A real but moderate link
  can easily fail to reach significance, and a model can differ from the reference by chance alone.
  Absence of dots is not evidence of absence of a link.
- **The models have a weaker NAO** (notebook 04). Slopes are per ERA5 standard deviation, so they
  are comparable, but the model slopes are estimated from a narrower range of NAO values and are
  therefore less certain.
- **ICON-ESM-ER's mean state** already resembles a strong positive NAO. Its response to further NAO
  swings is measured around that biased state.
- **Linear and simultaneous.** The method assumes the response is proportional to the NAO and has
  the same size for positive and negative winters, and it looks only at the same winter.
- **Other drivers are ignored.** Other circulation patterns (for example the East Atlantic pattern)
  also affect these extremes and can strengthen or mask the NAO signal.
- **RX1day is one day per winter,** so it is the noisiest of the three indices.
- **FDR level 10%.** A common choice for spatially correlated climate fields (Wilks 2016); a
  stricter level would mark fewer cells.
- **References.** E-OBS smooths intense rain and covers land only; ERA5 rain is a model product.
- **The circulation test is linear and uses one index.** It applies the response of ordinary NAO
  winters to a mean offset of about 2 SD, and it ignores other parts of the circulation bias that
  do not project onto the NAO pattern. It measures consistency, not cause.
""")

md("""
## 14. Open questions

1. Over UK and Ireland the two references give different strengths of the link (correlation 0.51 in
   E-OBS, 0.35 in ERA5). Section 10 shows the difference is within sampling noise; a longer record
   (E-OBS goes back to 1950) would show whether it is real.
2. Is ICON-ESM-ER's wrong-sign response over north-west France a consequence of its displaced NAO
   pattern (notebook 04)?
3. ICON-ESM-ER rains too hard on wet days (section 11). Is that how its convection and cloud
   processes make rain, or a trace of its finer native grid that survives regridding to 0.25°?
   Conservative regridding, and comparison with a denser national station dataset, would help
   separate the two.
4. With more members, would the models' links become significant over UK and Ireland?
   Notebook 08 shows how widely the link varies between identical runs.
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
