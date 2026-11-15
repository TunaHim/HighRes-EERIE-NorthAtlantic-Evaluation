"""Generate notebooks/00_summary.ipynb.  Usage: python build_notebook_00.py OUT.ipynb"""
import glob
import os
import sys
import nbformat as nbf

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "era5", "day")
HAVE_ERA5 = all(len(glob.glob(os.path.join(_DATA, f"{v}_nw_europe_*.nc"))) == 30 for v in ("pr", "tasmax"))
REFS = ["e-obs", "era5"] if HAVE_ERA5 else ["e-obs"]

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def step(explain, source):
    cells.append(nbf.v4.new_markdown_cell(explain.strip("\n")))
    cells.append(nbf.v4.new_code_cell(source.strip("\n")))


md("""
# 00 · Summary: North Atlantic circulation and European winter extremes in high-resolution climate models

**Start here.** This notebook is the single entry point to the project: the question, one overview
figure, then three experiments, each with its key figures and tables, and the conclusions. Every
section points to the notebook with the full analysis, the method and the limitations.

## The question

> Which features of the simulated North Atlantic winter circulation and of European winter
> extremes are persistent model characteristics, which arise from internal variability, and how
> do they change across coupled model resolution configurations?

The circulation is the North Atlantic winter pressure field and its leading mode, the North
Atlantic Oscillation (NAO). The extremes are the wettest day (RX1day), the rain on very wet days
(R95p) and the hottest day (TXx), evaluated over north-west Europe; three regions serve as worked
examples: **UK and Ireland** (the headline region), **western Norway** (the wet side of the NAO)
and **north-west France** (its dry side). Every map covers the whole north-west European domain,
so other regions can be examined with the same code.

## Three experiments

| Experiment | Question | Data | Notebooks |
|---|---|---|---|
| **1 · Ensemble robustness: daily extremes and their drivers** | Which biases in circulation, NAO and extremes persist across runs of the same model? | ICON-ESM-ER and IFS-FESOM2-SR, three historical runs each (r1, r2, r3); ERA5, E-OBS | 03–06, 09, 10 |
| **2 · Internal variability** | How much can chance alone change the conclusions from 29 winters? | 100-year control runs of both coupled models; ten-member atmosphere-only ensembles | 07, 11 |
| **3 · Resolution** | How do circulation, NAO and winter rain change with resolution? | HadGEM3-GC5E coupled at about 135, 60 and 20 km (atmosphere and ocean together); IFS atmosphere-only at 28 and 9 km | 08, 12 |

The experiments answer different questions with different data and uncertainty, so their results
are kept separate; they are not combined into one ranking of the models.

## The data

| | What | Period |
|---|---|---|
| **ICON-ESM-ER**, **IFS-FESOM2-SR** | two EERIE coupled models with eddy-rich oceans, historical runs r1, r2, r3 | r1 1950–2014 monthly; r2, r3 1975–2014 monthly; all 1985–2014 daily |
| **Control runs** | both coupled models with constant 1950 forcing | 1950–2049 monthly and daily rain |
| **HadGEM3-GC5E LL, MM, HH** | one coupled model at three resolutions, one run each; daily data not public | 1950–2014 monthly |
| **IFS atmosphere-only** | ten-member ensembles with observed and filtered sea-surface temperature; one run at 9 km and three at 28 km | 1980–2023 monthly; 1985–2014 daily |
| **ERA5** | reanalysis reference for pressure, temperature, rain and wind | 1950–2014 monthly; 1985–2014 daily |
| **E-OBS** | station-based gridded dataset, land only; reference for extremes | 1985–2014 daily |

All data are public. The project began (version 1) with run r1 of each coupled model; version 2
added the extra runs, the control runs and the HadGEM3-GC5E resolution configurations to separate
model properties from chance. Where version 2 changed a version 1 conclusion, this notebook gives
the version 2 result.

## How to read this notebook

Dark grey is ERA5, light grey is E-OBS, blue is ICON-ESM-ER, orange is IFS-FESOM2-SR, violet is
HadGEM3-GC5E. In difference maps, grey means no difference. Every code cell has a note above it;
every figure has a caption. Technical terms are explained in the "Background" section of each
detailed notebook.
""")

step("""
**What this cell does.** Loads the project code and the small result tables saved by the detailed
notebooks.
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
MODELS = ['icon-esm-er', 'ifs-fesom2-sr']
REFS = """ + repr(REFS) + """
""")

md("""
## The project at a glance
""")

step("""
**What this cell does.** Draws one overview figure from the result tables of notebooks 10, 11 and 12:
(A) the winter very-wet-day rain bias of every historical run over UK and Ireland; (B) the NAO
strength of every run; (C) the NAO link to very-wet-day rain in three regions, with the chance range
from the control runs, the historical runs and the two references with their 95% intervals;
(D–F) HadGEM3-GC5E at three resolutions: winter pressure error, NAO pattern and strength, and UK and
Ireland winter rain.
""", """
from pathlib import Path
assets = Path('../app_assets')
members_uk = pd.read_parquet(assets / 'members_extremes_uk.parquet')
column = [c for c in members_uk.columns if c.startswith('winter very-wet-day rain')][0]
eobs_r95p = float(members_uk.set_index('source').loc['e-obs', column])
members_nao = pd.read_parquet(assets / 'members_nao.parquet').set_index('source')
runs = members_uk[~members_uk.source.isin(['e-obs', 'era5'])].assign(
    r95p_bias=lambda t: 100 * (t[column] / eobs_r95p - 1),
    nao_strength=lambda t: t.source.map(members_nao['NAO strength relative to ERA5']))
link = pd.read_parquet(assets / 'members_nao_link.parquet').query("index == 'R95p'")
windows = pd.read_parquet(assets / 'control_window_link.parquet').query("index == 'R95p'")
control = (windows.groupby(['region', 'model']).r.quantile([0.05, 0.5, 0.95]).unstack()
           .set_axis(['low', 'median', 'high'], axis=1).reset_index().rename(columns={'model': 'source'}))
nao_h = pd.read_parquet(assets / 'hadgem_nao.parquet').set_index('source')
circ_h = pd.read_parquet(assets / 'hadgem_circulation.parquet').set_index('source')
surf_h = pd.read_parquet(assets / 'hadgem_surface_uk.parquet').set_index('dataset')
hadgem = pd.DataFrame([{'source': s, 'km': km, 'rms_error': circ_h.loc[s, 'RMS error (hPa)'],
                        'pattern_r': nao_h.loc[s, 'own pattern vs ERA5'], 'nao_strength': nao_h.loc[s, 'NAO strength relative to ERA5'],
                        'nao_first': nao_h.loc[s, 'first half'], 'nao_second': nao_h.loc[s, 'second half'],
                        'rain_bias': surf_h.loc[plotting.label_of(s), 'rain vs ERA5 (%)']}
                       for s, km in (('hadgem3-gc5e-ll', 135), ('hadgem3-gc5e-mm', 60), ('hadgem3-gc5e-hh', 20))])
plotting.plot_overview(runs, link, control, hadgem,
                       title='Version 2 at a glance: three runs per model (A, B), chance from control runs (C), one coupled model at three resolutions (D-F)');
""")

md("""
**Overview figure.** **A, B (experiment 1):** one dot per run, black bar the mean of three. All three
ICON-ESM-ER runs are 50–62% too wet in very-wet-day rain over UK and Ireland, and both models' NAO is
weaker than ERA5's in every run. **C (experiment 2):** shaded boxes show what each model's control run
produces by chance in 90% of 29-winter periods; dots are the historical runs; diamonds with bars are
E-OBS and ERA5 with their 95% intervals. Over UK and Ireland the runs scatter widely (chance); over
western Norway all runs are weaker than observed, although the observed interval reaches down to the
models' strongest values; over north-west France ICON-ESM-ER's control run is almost always negative,
while the observations are positive. **D–F (experiment 3):** HadGEM3-GC5E at about 135, 60 and 20 km in
the atmosphere, with the ocean refined at the same time (1°, 1/4°, 1/12°). Across the tested coupled
configurations the pressure error falls and the NAO pattern correlation increases; NAO strength does not
follow resolution (pale bars: the two halves of each run); winter-mean rain over UK and Ireland rises
sharply at 20 km.

**Main message.** Evaluating climate models for regional extremes needs three questions kept apart:
is a feature the same in every run (a model property), could chance in a short record produce it
(internal variability), and does it change with resolution? Large mean-state biases, such as
ICON-ESM-ER's shifted circulation and wet bias, are consistent across the three sampled runs. The NAO link to UK and Ireland
rain extremes is dominated by chance in 29 winters. A more realistic large-scale circulation, as at
higher HadGEM3-GC5E resolution, does not guarantee more realistic rain.

**Scope and limits.** Daily extremes are evaluated for ICON-ESM-ER and IFS-FESOM2-SR (three runs each);
HadGEM3-GC5E is evaluated with monthly data only, one run per resolution, and its atmosphere and ocean
resolutions change together. Control-run chance ranges come from overlapping windows and understate
chance. All results are exploratory.
""")

md("""
# Experiment 1 · Ensemble robustness: daily extremes and their drivers

ICON-ESM-ER and IFS-FESOM2-SR against ERA5 and E-OBS, step by step along the chain mean circulation →
NAO → extremes → NAO-to-extremes link → weather behind the extremes. Sections 1.0–1.6 show run r1, as
in version 1; section 1.7 tests every headline result on runs r2 and r3.
""")

md("""
## 1.0 Version 1 baseline: the chain in one figure (single-member evaluation, run r1)

The four columns follow the chain of the project from left to right, for each model: the
average winter circulation, the NAO, the link from the NAO to very-wet-day rain, and the rain bias.
""")

step("""
**What this cell does.** Builds the summary figure from the saved data and the result tables:
(A) each model's average winter sea-level pressure minus ERA5, with that difference expressed as
an NAO state; (B) the model's NAO pattern, measured along the ERA5 pattern, with ERA5's pattern as
black contour lines and the model's NAO strength relative to ERA5; (C) the correlation of winter
very-wet-day rain (R95p) with the model's own NAO, with dots where significant after
false-discovery-rate control, and the UK and Ireland value next to both references; (D) the
model's winter R95p relative to E-OBS.
""", """
def summary_figure():
    WINTERS = (1986, 2014)
    nao_table = pd.read_parquet('../app_assets/nao_index_winter.parquet')

    def nao_index(source, years=None):
        part = nao_table[nao_table.source == source]
        index = xr.DataArray(part.nao_on_era5_pattern.values, coords={'year': part.year.values}, dims='year')
        return index.sel(year=slice(*years)) if years else index

    # A: mean circulation bias and its NAO equivalent
    psl_all = {s: store.load(s, 'mon', 'psl', 'north_atlantic') for s in ['era5'] + MODELS}
    winters_psl = {s: nao.winter_anomalies(psl_all[s]) for s in psl_all}
    era5_eof = nao.leading_eof(winters_psl['era5'])
    mean_psl = {s: clim.season_means(psl_all[s], 'DJF').sel(year=slice(*WINTERS)).mean('year') for s in psl_all}
    offset = {m: nao.project_map(mean_psl[m] - mean_psl['era5'], era5_eof.vector) / era5_eof.amplitude for m in MODELS}

    # B: NAO pattern along the common ERA5 pattern, 1951-2014, and its strength
    pattern = {m: nao.regress(winters_psl[m].sel(year=nao_index(m).year), nao_index(m)) for m in MODELS}
    strength = {m: float(nao_index(m).std(ddof=1)) for m in MODELS}

    # C and D: NAO link to winter R95p and the R95p bias, north-west Europe
    indices = {d: ex.indices_for(d) for d in ['e-obs', 'era5'] + MODELS}
    grid = indices['icon-esm-er']
    indices['e-obs'] = regions.to_grid(indices['e-obs'], grid)
    land = regions.land_mask(grid.lat, grid.lon)
    common = land & indices['e-obs'].r95p_djf.isel(year_djf=0).notnull()
    uk = regions.BOXES['uk_ireland']
    inside = (grid.lon >= uk[0]) & (grid.lon <= uk[1]) & (grid.lat >= uk[2]) & (grid.lat <= uk[3])

    def r95(d):
        return indices[d].r95p_djf.rename(year_djf='year').sel(year=slice(*WINTERS))

    def uk_mean(field):
        return float(regions.area_mean(field.where(common & inside)))

    link = {d: rel.correlate(r95(d), nao_index('era5' if d in ('e-obs', 'era5') else d, WINTERS)) for d in ['e-obs', 'era5'] + MODELS}
    uk_r = {}
    for d in link:
        series = regions.area_mean(r95(d).where(common & inside))
        uk_r[d] = rel.regress_series(series.values, nao_index('era5' if d in ('e-obs', 'era5') else d, WINTERS).sel(year=series.year).values)['r']
    bias = {m: 100 * (r95(m).mean('year') / r95('e-obs').mean('year') - 1) for m in MODELS}
    uk_bias = {m: 100 * (uk_mean(r95(m).mean('year')) / uk_mean(r95('e-obs').mean('year')) - 1) for m in MODELS}

    columns = [
        {'title': 'A  Mean winter circulation', 'units': 'sea-level pressure minus ERA5 (hPa)', 'limit': 12},
        {'title': 'B  NAO pattern (lines: ERA5)', 'units': 'hPa per +1 SD of the NAO', 'limit': 6},
        {'title': 'C  NAO link to very-wet-day rain', 'units': 'correlation with the NAO, winter R95p', 'limit': 0.9},
        {'title': 'D  Very-wet-day rain bias', 'units': 'winter R95p minus E-OBS (%)', 'limit': 100},
    ]
    rows = [NAME[m] for m in MODELS]
    cells = {}
    for m in MODELS:
        row = NAME[m]
        cells[(row, 0)] = {'field': mean_psl[m] - mean_psl['era5'], 'note': f'mean state = {offset[m]:+.1f} SD of NAO'}
        cells[(row, 1)] = {'field': pattern[m], 'contour': era5_eof.pattern, 'note': f'strength {strength[m]:.0%} of ERA5'}
        cells[(row, 2)] = {'field': link[m].r.where(land), 'stipple': rel.fdr_mask(link[m].p) & land,
                           'note': f"UK & Ireland r = {uk_r[m]:.2f} (E-OBS {uk_r['e-obs']:.2f}, ERA5 {uk_r['era5']:.2f})"}
        cells[(row, 3)] = {'field': bias[m].where(common), 'note': f'UK & Ireland {uk_bias[m]:+.0f}%'}
    plotting.plot_chain(columns, rows, cells,
                        title='From North Atlantic circulation to UK and Ireland winter rain extremes, winters 1986-2014 (B: 1951-2014)');

summary_figure()
""")

md("""
**Summary figure.** Read each row from left to right. **ICON-ESM-ER (top):** (A) pressure far too
low in the north and too high in the south, equivalent to a +2.1 SD positive-NAO winter on
average; (B) an NAO only 59% as strong as ERA5's, with its southern centre displaced towards
Europe; (C) a positive link in the north but the wrong sign over France; (D) 62% too much
very-wet-day rain over UK and Ireland, and too wet almost everywhere. **IFS-FESOM2-SR (bottom):**
(A) a mean circulation close to ERA5; (B) a recognisable NAO at 71% of ERA5's strength; (C) a link
with the observed sign and pattern; (D) within about 10% over UK and Ireland. IFS-FESOM2-SR is the more realistic of the two, but not
perfect: its NAO is too weak and its southern centre weak and displaced. Section 1.5 shows that
ICON-ESM-ER's circulation offset accounts for only part of its wet bias.
""")

md("""
## 1.1 Where: three nested domains
""")

step("""
**What this cell does.** Draws the three domains: the North Atlantic (for the NAO), north-west
Europe (for temperature, rainfall and extremes) and the headline region, UK and Ireland.
""", """
plotting.plot_boxes({name: regions.BOXES[name] for name in regions.DOMAINS}, regions.LABELS, title='The three analysis domains');
""")

md("""
**Figure 1.** Large-scale circulation, European response, regional extremes. Details: notebook 02.
""")

md("""
## 1.2 Is the mean winter circulation credible? (notebook 03)
""")

step("""
**What this cell does.** Maps each model's average winter sea-level pressure minus ERA5's, 1985–2014.
""", """
psl = {s: store.load(s, 'mon', 'psl', 'north_atlantic') for s in ['era5'] + MODELS}
mean_winter = {s: clim.climatology(clim.period(psl[s], 1985, 2014), 'DJF') for s in psl}
plotting.plot_field_panels({f'{NAME[m]} minus ERA5': mean_winter[m] - mean_winter['era5'] for m in MODELS},
                           units='hPa', diverging=True, title='Winter-mean sea-level pressure: model minus ERA5, 1985-2014');
""")

md("""
**Figure 2.** Orange: pressure too high; blue: too low. **IFS-FESOM2-SR is close to ERA5**
(typical difference 1.8 hPa). **ICON-ESM-ER has a strong north–south dipole bias**: pressure up to
14 hPa too low in the north and up to 8 hPa too high in the subtropics, which means westerly winds
that are too strong on average. ICON-ESM-ER is also about 30% too wet in winter over north-west
Europe, and both models are about 0.8 °C too cold.

**What it means physically.** A stronger-than-observed pressure drop from the subtropics to
Iceland drives stronger westerly winds. Those carry more moist Atlantic air onto the windward
coasts and mountains of western Scotland, Ireland and Norway, so a wet bias there is expected.
The bias projects onto the NAO pattern: ICON-ESM-ER's *average* winter looks like a strongly
positive NAO winter of the real world. Whether the wet bias follows from this alone is tested in
section 1.5.
""")

md("""
## 1.3 Is the NAO realistic? (notebook 04)
""")

step("""
**What this cell does.** Computes the leading pattern of winter pressure variability (the NAO) for
ERA5 and both models over 64 winters, 1951–2014, and maps it.
""", """
winters = {s: nao.winter_anomalies(psl[s]) for s in psl}
eofs = {s: nao.leading_eof(winters[s]) for s in psl}
plotting.plot_field_panels({NAME[s]: eofs[s].pattern for s in psl}, units='hPa per +1 SD of the index', diverging=True,
                           title='The NAO pattern (leading EOF of winter pressure), 1951-2014');
""")

md("""
**Figure 3.** Blue: lower pressure in a positive-NAO winter; orange: higher. ERA5 shows the
textbook pattern. IFS-FESOM2-SR is recognisably the same, with a weak southern centre displaced
towards the Mediterranean. ICON-ESM-ER's southern centre sits over the North Sea: its leading
pattern is a mixture and not a clean NAO.

**Why ICON-ESM-ER's pattern is "mixed".** The leading pattern is the one that explains the most
variance. In ICON-ESM-ER the first two patterns explain 29% and 21%, and the sampling error of each
share is about ±5% (North et al. 1982). Two patterns that close cannot be told apart reliably:
the computation then returns two arbitrary blends of them. The real NAO pattern is indeed split
between ICON-ESM-ER's first and second patterns (overlaps 0.76 and 0.58). In this model the NAO
and a second mode of similar strength share the variability. This is why every model in this
project is measured along the *same* ERA5 pattern rather than along its own leading pattern.
**Version 2 update (notebook 10):** in ICON-ESM-ER's runs r2 and r3 the leading pattern resembles
ERA5's much more closely (pattern correlation 0.90 and 0.94, against 0.59 for r1 over the same
winters), so the mixing seen here was largely the chance of run r1.
Notebook 04 (section 8) shows the mixing persists in all five domains tested, while the NAO
strengths along ERA5's pattern barely change (0.56–0.61 and 0.68–0.72).
""")

step("""
**What this cell does.** The key NAO numbers in one table: variance explained, similarity to the
ERA5 pattern, strength of the NAO measured along the ERA5 pattern, and the model's mean-pressure
bias expressed as an NAO state.
""", """
rows = []
for s in psl:
    projected = nao.project(winters[s], eofs['era5'].vector)
    bias = nao.project_map(clim.climatology(psl[s], 'DJF') - clim.climatology(psl['era5'], 'DJF'), eofs['era5'].vector) / eofs['era5'].amplitude
    rows.append({'': NAME[s], 'variance explained %': 100 * eofs[s].explained[0],
                 'pattern correlation with ERA5': clim.pattern_stats(eofs[s].pattern, eofs['era5'].pattern)['pattern correlation'],
                 'NAO strength relative to ERA5': float(projected.std(ddof=1)) / eofs['era5'].amplitude,
                 'mean-state bias as an NAO anomaly (SD)': bias})
pd.DataFrame(rows).set_index('')
""")

md("""
**Reading the table.** Both models have a **weaker NAO than ERA5** (59% and 71% of its strength).
*Strength* here is the standard deviation of the winter index measured along the common ERA5
pattern, relative to ERA5's own: the same pattern and scale for every dataset.
ICON-ESM-ER's *average* winter resembles a +2.3 SD positive-NAO winter of the real world.
Notebook 07 adds an important caution: ten runs of one atmosphere model give NAO strengths anywhere
from 0.70 to 1.00, so a single member's 0.71 may be partly chance; 0.59 lies below that whole range.
""")

md("""
## 1.4 Are the extremes realistic? (notebook 05)
""")

step("""
**What this cell does.** Shows the headline numbers for UK and Ireland (land average, 1985–2014):
the wettest day of the year (RX1day), the rain on very wet days (R95p) and the hottest day of the
year (TXx), for the reference data and both models.
""", """
regional = pd.read_parquet('../app_assets/extremes_regional.parquet')
labels = {'rx1day': 'wettest day, RX1day (mm)', 'r95p': 'rain on very wet days, R95p (mm)', 'txx': 'hottest day, TXx (°C)'}
part = regional[(regional.region == 'uk_ireland') & (regional.period == 'annual') & regional['index'].isin(labels)]
table = part.groupby(['index', 'source']).value.mean().unstack('source')[REFS + MODELS]
for m in MODELS:
    table[f'{NAME[m]} vs E-OBS'] = np.where(table.index == 'txx', table[m] - table['e-obs'], 100 * (table[m] - table['e-obs']) / table['e-obs'])
table = table.rename(columns=NAME).rename(index=labels)
table
""")

md("""
**Reading the table.** The last two columns are the difference from E-OBS: in % for the two
rainfall rows, in °C for the hottest day.
""")

step("""
**What this cell does.** Maps each model's annual wettest day as a percent difference from E-OBS.
""", """
indices = {s: ex.indices_for(s) for s in ['e-obs'] + MODELS}
indices['e-obs'] = regions.to_grid(indices['e-obs'], indices['icon-esm-er'])
mean_rx = {s: indices[s].rx1day_ann.mean('year_ann') for s in indices}
plotting.plot_field_panels({f'{NAME[m]} vs E-OBS': 100 * (mean_rx[m] - mean_rx['e-obs']) / mean_rx['e-obs'] for m in MODELS},
                           units='% difference', diverging=True, title='Wettest day of the year (RX1day): model relative to E-OBS, 1985-2014');
""")

md("""
**Figure 4.** Orange: the model's wettest day is wetter than in E-OBS. **IFS-FESOM2-SR is within
about 10%** over most of the region. **ICON-ESM-ER is roughly 50% too wet** almost everywhere.
Against ERA5 the excess is larger still (+60% and +17%). For the hottest day, ICON-ESM-ER is about
2 °C too cool against ERA5 as well as E-OBS. IFS-FESOM2-SR is only 0.6 °C cooler than ERA5, so most
of its 2 °C gap to E-OBS comes from comparing 25 km grid cells with low-lying stations.

**What it means physically.** ICON-ESM-ER's wet bias is not confined to windward coasts and
mountains, where a too-strong westerly flow would put it; it covers inland France and Iberia too.
It is also far larger than chance: in notebook 08, identical runs of one model differ by only 1–3%
in these 30-year averages. Section 1.5 splits it into what the circulation explains and what it
does not. ERA5 gives slightly lower rainfall extremes than E-OBS over UK and Ireland, so every model
bias looks larger against ERA5; for rain extremes over land, E-OBS is the more direct reference,
though it too smooths the most intense local rain.
""")

md("""
## 1.5 Do the models link the NAO to extremes as the real world does? (notebook 06)

This is the centrepiece. In the real world, positive-NAO winters bring heavier rainfall extremes
to the north-west of Europe.
""")

step("""
**What this cell does.** For the 29 winters 1986–2014, correlates winter very-wet-day rainfall
(R95p) with the winter NAO at every grid cell, after removing trends. E-OBS is paired with the
ERA5 NAO; each model with its own NAO. Dots mark cells that are statistically significant after
false-discovery-rate control.
""", """
nao_table = pd.read_parquet('../app_assets/nao_index_winter.parquet')
def nao_index(source):
    rows = nao_table[(nao_table.source == source) & nao_table.year.between(1986, 2014)]
    return xr.DataArray(rows.nao_on_era5_pattern.values, coords={'year': rows.year.values}, dims='year')
results = {}
for d, source in (('e-obs', 'era5'), ('icon-esm-er', 'icon-esm-er'), ('ifs-fesom2-sr', 'ifs-fesom2-sr')):
    results[d] = rel.correlate(indices[d].r95p_djf.rename(year_djf='year'), nao_index(source))
plotting.plot_field_panels({NAME[d]: results[d].r for d in results}, units='correlation with the NAO', diverging=True, limit=1.0,
                           stipple={NAME[d]: rel.fdr_mask(results[d].p) for d in results},
                           title='Winter very-wet-day rainfall (R95p) and the NAO: correlation, 1986-2014');
""")

md("""
**Figure 5.** Orange: more very-wet-day rain in positive-NAO winters; blue: less. E-OBS shows the
real-world pattern: a strong positive link over Scotland and Norway, negative over Iberia.
IFS-FESOM2-SR reproduces it. ICON-ESM-ER has the positive link in the north, but its negative
(dry) side reaches up across France.
""")

step("""
**What this cell does.** The same link as numbers for UK and Ireland (land average): the
correlation with the NAO, the change per one standard deviation of NAO with its 95% range, and
the p value.
""", """
link = pd.read_parquet('../app_assets/nao_extremes_regional_link.parquet')
link[link.region == 'UK and Ireland'].drop(columns='region').set_index(['index', 'dataset'])
""")

md("""
**Reading the table.** Where the range from `low` to `high` excludes zero, the link is
distinguishable from chance in 29 winters. The two references agree on the sign but not on the
strength over UK and Ireland: about 0.5 in E-OBS, about 0.33 in ERA5. **IFS-FESOM2-SR** (0.57 and
0.60) sits at the E-OBS end. **ICON-ESM-ER** (0.28 and 0.36) is close to ERA5 here, but it has the
wrong sign over north-west France and a weak link in western Norway. The mildest winter day (TXx)
has only a weak link over UK and Ireland in both references.
""")

step("""
**What this cell does.** Shows how certain those UK and Ireland correlations are (notebook 06,
section 10): the bootstrap 95% interval, the range when any one winter is left out, and the
effective number of independent winters.
""", """
certainty = pd.read_parquet('../app_assets/nao_extremes_correlation_uncertainty.parquet')
columns = ['r', 'low', 'high', 'r without one winter, min', 'r without one winter, max', 'effective winters']
certainty[certainty.region == 'UK and Ireland'].set_index(['index', 'dataset'])[columns]
""")

md("""
**Reading the table.** The intervals are wide and overlap: **over UK and Ireland, 29 winters cannot
tell any dataset's NAO link from another's**, including the two references (0.51 and 0.35). No
single winter drives any value, and memory between winters is negligible. The model differences
that do pass formal tests lie elsewhere: ICON-ESM-ER's link is too weak in western Norway and has
the wrong sign in north-west France. IFS-FESOM2-SR is consistent with both references in all three
regions.
""")

step("""
**What this cell does.** Tests the chain "circulation bias, therefore wet bias" (notebook 06,
section 11). The observed change in rain extremes per standard deviation of NAO, multiplied by the
model's mean circulation offset, gives the bias the offset alone would produce. The table compares
it with the actual bias over UK and Ireland land, and adds wet-day frequency and rain per wet day.
""", """
explained = pd.read_parquet('../app_assets/circulation_explained_bias.parquet')
wet = pd.read_parquet('../app_assets/wet_day_frequency_intensity.parquet').set_index('dataset')
display(explained.set_index(['index', 'reference', 'model']))
wet
""")

md("""
**What it means physically.** ICON-ESM-ER's average winter sits 2.1 SD along the NAO over these
winters. With the observed NAO response, that offset accounts for **38–74% of its very-wet-day
rain bias and 18–39% of its wettest-day bias** over UK and Ireland (the range spans the two
references; with the model's own response the shares are higher, about 100% and 40–50%). The
offset explains the extra rain on windward coasts and mountains, but not the wet bias inland and in
the south, where a positive-NAO-like flow should make the model *drier*. The second table shows
why: **ICON-ESM-ER rains too often (+34% to +43% wet days) and too hard (+21% to +28% rain per wet
day)**. Too many wet days fits a too-strong, too-persistent westerly flow; too much rain on each wet
day points to how the model produces rain. Both contribute. This is an association supported by
diagnostics, not a demonstrated cause, and it relies on a linear response extended to an offset
beyond most ordinary NAO winters.
""")

md("""
## 1.6 What weather brings the heaviest rain? (notebook 09)
""")

step("""
**What this cell does.** Finds the 30 wettest winter days over UK and Ireland land in ERA5 and in
each model, and maps the average pressure anomaly on those days.
""", """
from eerie_uk import events as ev
land_cells = regions.land_mask(indices['icon-esm-er'].lat, indices['icon-esm-er'].lon) & indices['e-obs'].rx1day_ann.isel(year_ann=0).notnull()
def winter_days(da):
    da = da.sel(time=slice('1985-12-01', '2014-02-28'))
    return da.sel(time=da.time.dt.month.isin([12, 1, 2]))
composite = {}
for s in ['era5'] + MODELS:
    rain = winter_days(store.load(s, 'day', 'pr', 'nw_europe'))
    uk = clim.regional_mean(rain.where(land_cells), 'uk_ireland')
    pressure = winter_days(store.load(s, 'day', 'psl', 'north_atlantic'))
    composite[NAME[s]] = ev.lagged_composite(pressure - pressure.mean('time'), ev.top_events(uk, 30, 5), lags=(0,)).sel(lag=0)
plotting.plot_field_panels(composite, units='hPa', diverging=True,
                           title='Pressure anomaly on the 30 wettest winter days over UK and Ireland, 1986-2014');
""")

md("""
**Figure 7.** In the real world (left) heavy UK winter rain comes with a deep low just north-west of
the islands and higher pressure to the south. **Both models produce their heaviest rain days
through the same weather** (pattern correlation 0.94–0.95 with ERA5). The difference is in the
build-up: two days earlier, IFS-FESOM2-SR's pattern still resembles ERA5's (0.85), ICON-ESM-ER's
much less (0.72). Both models also show 13–17% higher day-to-day pressure variability over the UK
than ERA5, indicating enhanced synoptic storminess (a proxy; individual cyclones are not tracked).
""")

md("""
## 1.7 Three runs per model: model property or chance? (notebook 10)

Version 1 rests on one run of each coupled model. Version 2 repeats the key diagnostics on two more
historical runs of each model (r2 and r3) and measures chance with 100-year control runs.
""")

step("""
**What this cell does.** Shows, for each headline result of version 1, the value in run r1 and the
range over the three runs (notebook 10).
""", """
pd.read_parquet('../app_assets/members_verdict.parquet')
""")

md("""
**Reading the table.** Where the three runs agree, the result is a property of the model: the mean
circulation offset, the wet bias, a too-weak NAO. Where they scatter widely, as for the NAO link to
UK and Ireland rain (ICON-ESM-ER 0.06 to 0.49, IFS-FESOM2-SR 0.21 to 0.60), a single run cannot pin
the number down.
""")

md("""
# Experiment 2 · Internal variability

How far chance alone can move the diagnostics of experiment 1: identical atmosphere-only runs (2.1)
and 100-year control runs of the coupled models (2.2).
""")

md("""
## 2.1 Ten identical atmosphere-only runs, and filtered sea-surface temperature (notebook 07)
""")

step("""
**What this cell does.** Uses the paired atmosphere-only experiments. For each of the ten members
of each experiment it measures the NAO strength (43 winters, 1981–2023) along the ERA5 pattern and
plots one dot per member.
""", """
runs = ['hist', 'hist-c-0-a-lr20', 'hist-c-lr20-a-0']
strength = {}
for run in runs:
    w = nao.winter_anomalies(store.load(f'ifs-amip-tco399.{run}', 'mon', 'psl', 'north_atlantic'), (1980, 2023))
    strength[run] = (nao.project(w, eofs['era5'].vector) / eofs['era5'].amplitude).std('year', ddof=1).values
plotting.plot_member_dots(strength, xlabel='NAO strength (ERA5 units)', title='NAO strength of each ensemble member, 1981-2023');
""")

md("""
**Figure 6.** Green: observed sea-surface temperature. Yellow and pink: two versions with the
small-scale detail filtered out. The three rows overlap almost completely: **filtering changes the
NAO strength by −1% and +4%, far less than the spread between members of one experiment.**
No change in NAO strength is detectable. This is an atmosphere-only test of sea-surface-temperature forcing;
it says nothing about a coupled effect of ocean eddies, and the exact filter is not verified.
""")

md("""
## 2.2 How much can chance alone do? 100-year control runs (notebook 11)
""")

step("""
**What this cell does.** Shows where the three historical runs and the two references fall relative
to the chance range of each model's control run: the 5th to 95th percentile of the NAO–rain
correlation over all 29-winter windows of 99 control winters (notebook 11).
""", """
pd.read_parquet('../app_assets/control_placement.parquet')
""")

md("""
**Reading the table.** Over **western Norway** the observed link (0.81) lies above every control
window of both models and above all six historical runs. The observed value has its own uncertainty
(95% interval about 0.71–0.91), which overlaps the models' strongest windows, so this is a consistent
but modest discrepancy rather than a proven model error.
Over **north-west France** ICON-ESM-ER's control run almost never produces the observed positive
link: its wrong sign is consistent across its control run. Over **UK and Ireland** the references fall inside or at
the edge of the chance ranges. Several historical runs fall outside their control range, so these
ranges understate chance and are lower bounds.
""")

md("""
# Experiment 3 · Resolution

The same atmosphere model at two resolutions with the same prescribed sea-surface temperature (3.1),
and one coupled model at three resolutions in which atmosphere and ocean are refined together (3.2).
The second therefore compares coupled resolution configurations; it does not isolate the effect of
the atmospheric grid.
""")

md("""
## 3.1 One atmosphere model at 28 km and 9 km (notebook 08)

The cleanest test available: the **same** atmosphere model (IFS) with the **same** observed
sea-surface temperature, run at about 9 km and at about 28 km (three members), winters 1986–2014.
""")

step("""
**What this cell does.** Averages the wettest winter day (RX1day) over the land of each region for
the two references, the 9 km run and each of the three 28 km members.
""", """
def winter_rx1day(source):
    daily = store.load(source, 'day', 'pr', 'nw_europe')
    daily = daily.sel(time=daily.time.dt.month.isin([12, 1, 2]))
    return ex.rx1day(daily, 'DJF').sel(year=slice(1986, 2014)).mean('year')
res = {'IFS 9 km': winter_rx1day('ifs-amip-tco1279.hist')}
lo = winter_rx1day('ifs-amip-tco399.hist')
res.update({f'IFS 28 km, member {int(m)}': lo.sel(realization=m) for m in lo.realization.values})
res['E-OBS'] = regions.to_grid(ex.indices_for('e-obs').rx1day_djf.mean('year_djf'), lo)
res['ERA5'] = ex.indices_for('era5').rx1day_djf.mean('year_djf')
land_cells = regions.land_mask(lo.lat, lo.lon) & res['E-OBS'].notnull()
pd.DataFrame({regions.LABELS[r]: {k: float(clim.regional_mean(v.where(land_cells), r)) for k, v in res.items()}
              for r in regions.SUBREGIONS}).round(1)
""")

md("""
**Reading the table** (mm, wettest winter day, land average). At 9 km the wettest winter day is
5–12% heavier than at 28 km. Over western Norway, where 28 km falls short, that brings 9 km closer
to both references; over UK and Ireland, where 28 km is already about right, 9 km overshoots.
Across the whole region 9 km brings no overall improvement at the 25 km scale compared here.
The NAO-to-extremes correlation over UK and Ireland ranges from 0.04 to 0.33 between the three
identical 28 km runs, and 9 km (0.19) falls inside that range: **the conclusion depends more on
internal variability than on resolution.**
""")

md("""
## 3.2 One coupled model at three resolutions: HadGEM3-GC5E (notebook 12)

HadGEM3-GC5E was run at about 135 km (LL), 60 km (MM) and 20 km (HH) in the atmosphere, with the
ocean going from 1° to an eddy-rich 1/12°. Only monthly data are public, so the comparison covers
the circulation, the NAO, winter-mean rain and the jet.
""")

step("""
**What this cell does.** Combines the circulation, NAO and surface tables of notebook 12.
""", """
circulation = pd.read_parquet('../app_assets/hadgem_circulation.parquet').set_index('model').drop(columns='source')
nao_v2 = pd.read_parquet('../app_assets/hadgem_nao.parquet').set_index('model')[['NAO strength relative to ERA5', 'first half', 'second half', 'own pattern vs ERA5']]
surface = pd.read_parquet('../app_assets/hadgem_surface_uk.parquet').set_index('dataset')[['rain vs ERA5 (%)', 'temperature vs ERA5 (°C)']]
circulation.join(nao_v2).join(surface)
""")

md("""
**Reading the table.** Across the tested coupled configurations the winter pressure error shrinks
(3.2, 2.7, 2.6 hPa) and the NAO pattern correlation with ERA5 increases (0.92, 0.95, 0.98). NAO strength does not follow
resolution: it changes as much between the two halves of one run as between resolutions. At 20 km
UK and Ireland winter-mean precipitation (not daily extremes) is 25% above ERA5, against +7% to +8% at the coarser grids, the same
direction as IFS's 9 km run in section 3.1. The 850 hPa jet sits about 1.5° too far north at LL and
close to ERA5 at MM.
""")

md("""
## 4. What was learned

| Step | ICON-ESM-ER | IFS-FESOM2-SR |
|---|---|---|
| Mean winter circulation | too-strong north–south pressure contrast | close to ERA5 |
| NAO pattern | mixed in r1; close to ERA5 in r2 and r3 | recognisable, southern centre weak |
| NAO strength (three runs, 1976–2014) | 0.55–0.63 of ERA5 | 0.68–0.81 of ERA5 |
| Rainfall extremes, UK and Ireland (three runs) | 42–62% too heavy; too many wet days and too much rain per wet day | within 4–17% of E-OBS |
| Share of the wet bias consistent with the circulation offset | 38–74% (very wet days), 18–39% (wettest day) | offset small (0.2 SD) |
| Hottest day of the year | about 2 °C too cool against ERA5 | within 1 °C of ERA5 |
| NAO link to winter rainfall extremes | UK: varies by chance (0.06–0.49); Norway: below the observed estimate in all runs; France: wrong sign in control run and 2 of 3 runs | UK: varies by chance (0.21–0.60); Norway: too weak in all runs; France: near zero to observed |
| Weather behind the heaviest rain days | same pattern, weaker build-up | same pattern and build-up |
| Storminess over the UK (day-to-day pressure variability) | 17% higher than ERA5 | 13% higher than ERA5 |

1. **Each step depends on the one before, but only partly.** ICON-ESM-ER's circulation bias shows
   up again as a mean state that resembles a permanent positive NAO and as a misplaced NAO rainfall
   response. That offset is consistent with a large part of its very-wet-day rain bias over UK and
   Ireland, but less than half of its wettest-day bias: the model also rains too hard on each wet
   day. Checking the chain in order, and then putting a number on each link, made that visible.
2. **Mean-state biases are consistent across the three sampled runs; the NAO link over UK and Ireland is mostly chance.**
   Version 2's extra runs confirm every mean-state and extreme-index bias of version 1, and a
   too-weak NAO in both models. But three runs of one model span correlations from 0.06 to 0.49 for
   the NAO link to UK and Ireland rain extremes, so version 1's single-run comparison of that link
   between the models does not hold.
3. **The clearest model discrepancy in the link is over western Norway.** All six historical runs
   and every 29-winter window of both control runs have a weaker NAO link than observed (0.81),
   although the observed value's own uncertainty (about 0.71–0.91) reaches the models' strongest
   windows. ICON-ESM-ER's wrong-sign link over north-west France appears in its control run and two of three historical runs.
4. **Finer coupled resolution improves the circulation, not the NAO's strength, and raises winter
   rain.** Across HadGEM3-GC5E's tested configurations the mean pressure error falls and the NAO
   pattern correlation increases from 135 to 20 km; NAO strength does not change beyond chance;
   winter-mean rain over UK and Ireland rises by a quarter at 20 km (atmosphere and ocean refined
   together; monthly data, so no extremes). In IFS, 9 km gives heavier rain extremes, which helps over mountains and
   overshoots elsewhere.
5. **Two good references can disagree, and 29 winters are few.** E-OBS and ERA5 agree on patterns
   but not always on numbers (for example the strength of the NAO link over UK and Ireland, 0.51
   against 0.35). Over UK and Ireland, no correlation can be told apart from another within its
   sampling uncertainty; the clear model differences are in western Norway and north-west France.
6. **In one atmosphere model, NAO strength shows no detectable change under the tested
   small-scale SST filtering**; other aspects of the atmosphere, and coupled feedbacks, are not tested.

## 5. Main limitations

- Three runs per coupled model (version 2); 29 winters for the link to extremes. Control-run
  chance ranges come from overlapping windows of one run and understate chance.
- Two coupled models for extremes, plus HadGEM3 for the monthly diagnostics; HadGEM3 daily data
  are not public.
- ERA5 is a reanalysis; its precipitation is a model product. E-OBS smooths intense rain and
  covers land only.
- Precipitation was regridded bilinearly, not conservatively.
- The decoding fix for IFS-FESOM2-SR data was checked against an older decoder and against the
  model's own monthly files, not against an independent tool.
- The paired experiment is atmosphere-only and its filter definition is unverified.
- The resolution comparison uses one 9 km run and three 28 km members, winter only, compared at 25 km.
- Model complexity and air quality are not tested.

## 6. Status and what would come next

This project is a **research prototype**: a complete, tested chain from public data to
conclusions, built to be scaled up rather than a final evaluation of the EERIE models.

The analysis code takes any dataset that provides monthly sea-level pressure and daily
precipitation and maximum temperature under CMIP-style names. The same notebooks could therefore
be run on more EERIE members, on CMIP6 models, and on CMIP7 output when it becomes available.
Version 2 has started that with three runs per model, control runs and a resolution ladder. The
next steps are larger ensembles, HadGEM3's daily data (which needs JASMIN access) to bring its
extremes into the comparison, and process diagnostics for the wet bias. A natural extension is physical climate storylines: using the event composites of
notebook 09 to ask how a given type of heavy-rain winter would look under further warming, with
control runs to separate forced change from internal variability.

## Where to find the details

| Notebook | Content |
|---|---|
| `01_data_inventory` | what public EERIE data exist and can be read |
| `02_download_plan` | domains, datasets, periods, measured download cost |
| `03_validation_baseline` | data checks, mean climate and variability against ERA5 |
| `04_nao` | NAO pattern, index, strength, cross-checks |
| `05_extremes` | RX1day, TXx, R95p, annual and winter |
| `06_nao_extremes` | the NAO-to-extremes link |
| `07_paired_experiment` | NAO sensitivity to filtered sea-surface temperature |
| `08_resolution` | winter precipitation extremes at 9 km and 28 km |
| `09_event_anatomy` | the weather behind the heaviest winter rain days, storminess, persistent highs |
| `10_members` | version 2: three runs per coupled model, model or chance? |
| `11_control` | version 2: chance ranges from the 100-year control runs |
| `12_hadgem_resolution` | version 2: HadGEM3-GC5E at three resolutions |

Methods: `docs/methods.md`. Code: `src/eerie_uk/`, with offline tests in `tests/`.
The summary figure is also saved as `docs/figures/summary_chain.png`.
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
