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
# 04 · The winter North Atlantic Oscillation

**Question for this notebook.** Do the two EERIE models produce a realistic winter NAO: the right
pattern, the right strength, and realistic behaviour in time?

**What the NAO is.** The NAO is the leading see-saw of winter sea-level pressure over the North
Atlantic. In a *positive* NAO winter, pressure is lower than usual near Iceland and higher than
usual near the Azores; the westerly winds are stronger and northern Europe is mild and wet.
A *negative* winter is the reverse.

**Data.** Monthly sea-level pressure, 1950–2014, on the North Atlantic box (20–80°N, 90°W–40°E, 1° grid):
ERA5 (reanalysis reference), ICON-ESM-ER r1 and IFS-FESOM2-SR r1.

**Method** (fixed in `docs/methods.md` before any result was produced):
1. Subtract the 1950–2014 mean of each calendar month, giving anomalies.
2. Average December–February into one map per winter. December belongs to the following year's
   winter, so the first complete winter is 1951 and there are **64 winters**, 1951–2014.
3. Weight each grid point by √cos(latitude), so the many small high-latitude cells do not dominate.
4. Take the leading EOF: the single pattern that explains the most winter-to-winter variance.
5. Fix the sign so that positive means low pressure near Iceland and high pressure near the Azores.
6. The NAO index is the strength of that pattern each winter, in standard deviations.

**An important reminder.** A free-running model has its own sequence of winters. The model index is
*not* expected to match the ERA5 index year by year. Patterns, strength and statistics are compared.

**Sections**
1. Setup
2. Findings
3. The NAO pattern
4. The NAO index
5. Cross-checks: a station-style index and a common pattern
6. Behaviour in time: persistence and trend
7. Does the mean-state bias look like the NAO?
8. Saved outputs
9. Limitations
10. Open questions
""")

md("""
## Background: the terms used in this notebook

If you know these already, skip to section 1.

| Term | What it means here |
|---|---|
| **Anomaly** | The difference from normal. Here: a month's pressure minus the 1950–2014 average for that calendar month. A winter anomaly map shows where pressure was higher or lower than usual that winter. |
| **EOF (empirical orthogonal function)** | A way to find the dominant pattern in a set of maps. The leading EOF is the single map that, made stronger or weaker and flipped in sign from winter to winter, reproduces as much of the winter-to-winter variation as one pattern can. It is the same mathematics as principal component analysis (PCA). |
| **Index (principal component)** | One number per winter saying how strongly, and with which sign, that winter resembled the pattern. This is the NAO index. |
| **Explained variance** | The share of all winter-to-winter variation that the pattern accounts for. For the real NAO this is roughly 40–50% in winter. |
| **SD (standard deviation)** | The typical size of the swings of the index. An index of +1 SD is a moderately positive winter; ±2 SD is rare, about one winter in twenty. |
| **Sign convention** | The mathematics does not decide which way round the pattern is. We fix it: positive = low pressure near Iceland, high pressure near the Azores. |
| **Station-style index** | The traditional NAO definition used long before EOFs: pressure at a southern station (Azores, Lisbon or Gibraltar) minus pressure in Iceland. Used here as an independent check. |
| **Projection onto a pattern** | Measuring how strongly a map resembles a *given* pattern. Projecting a model's winters onto the ERA5 pattern measures the model with ERA5's ruler. |
| **Autocorrelation at lag 1** | Whether a positive winter tends to be followed by another positive winter (value above 0) or not (near 0). |
| **Trend and 95% range** | The best-fit straight-line change per decade, with the range the true value plausibly lies in. If the range includes 0, there is no clear trend. |
| **Standard error** | The uncertainty of an estimate that comes purely from having a limited number of winters. |
| **Pattern correlation** | How similar the shapes of two maps are, from −1 to 1. |

**How to read the maps.** All maps here show pressure *anomalies*: blue = lower pressure than
usual, orange = higher, grey = no change. All panels of one figure share the same colour scale.

**Colours of the lines.** Dark grey is always ERA5, blue is always ICON-ESM-ER, orange is always
IFS-FESOM2-SR.
""")

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code. The NAO calculations are in `eerie_uk/nao.py`;
each function there has a unit test on synthetic data with a known answer.
""", """
import sys, warnings
sys.path.insert(0, '../src')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path
from eerie_uk import climatology as clim, nao, plotting, store

pd.set_option('display.width', 220, 'display.float_format', '{:.2f}'.format)
SOURCES = ['era5', 'icon-esm-er', 'ifs-fesom2-sr']
MODELS = SOURCES[1:]
NAME = plotting.SOURCE_LABELS
""")

step("""
**What this cell does.** Loads monthly pressure for the three sources, turns it into one anomaly
map per winter, and computes the leading EOF of each. This is the whole NAO calculation; the rest
of the notebook looks at its results.
""", """
psl = {s: store.load(s, 'mon', 'psl', 'north_atlantic') for s in SOURCES}
winters = {s: nao.winter_anomalies(psl[s]) for s in SOURCES}
eofs = {s: nao.leading_eof(winters[s]) for s in SOURCES}

n = winters['era5'].sizes['year']
print(n, 'winters:', int(winters['era5'].year[0]), 'to', int(winters['era5'].year[-1]))
print('grid:', winters['era5'].sizes['lat'], 'x', winters['era5'].sizes['lon'], 'points at 1 degree')
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. The NAO pattern
""")

step("""
**What this cell does.** Maps the leading pattern of each source. Colours show the pressure anomaly,
in hPa, of a winter whose NAO index is +1 standard deviation: blue is lower pressure than usual,
orange higher.
""", """
plotting.plot_field_panels({NAME[s]: eofs[s].pattern for s in SOURCES}, units='hPa per +1 SD of the index',
                           title='Leading pattern of winter sea-level pressure (EOF 1), 1951-2014', diverging=True);
""")

md("""
**Figure 1.** The NAO pattern in each source. A realistic NAO has a blue centre near Iceland and
southern Greenland and an orange band from the Azores towards Europe, with the zero line between
them around 50–55°N.
""")

step("""
**What this cell does.** Puts the patterns into numbers: how much of the winter-to-winter variance
the NAO explains, how separate it is from the second pattern, where its two centres sit and how
strong they are, and how closely each model pattern matches ERA5's (pattern correlation, 1 = same).
The `±` column is the sampling uncertainty of the explained variance (North et al. 1982): if the
first and second patterns overlap within it, they are not cleanly separated.
""", """
rows = []
for s in SOURCES:
    e = eofs[s]
    spacing = nao.north_spacing(e.explained, n)
    rows.append({'source': NAME[s],
                 'EOF1 variance %': 100 * e.explained[0], '± %': 100 * spacing[0],
                 'EOF2 variance %': 100 * e.explained[1],
                 'separated from EOF2': bool(e.explained[0] - spacing[0] > e.explained[1] + spacing[1]),
                 **nao.centres(e.pattern),
                 'pattern correlation with ERA5': clim.pattern_stats(e.pattern, eofs['era5'].pattern)['pattern correlation']})
pattern_table = pd.DataFrame(rows)
pattern_table
""")

step("""
**What this cell does.** Subtracts the ERA5 pattern from each model pattern, to show where a
model's NAO is displaced or too weak.
""", """
plotting.plot_field_panels({f'{NAME[m]} minus ERA5': eofs[m].pattern - eofs['era5'].pattern for m in MODELS},
                           units='hPa per +1 SD', title='NAO pattern: model minus ERA5', diverging=True);
""")

md("""
**Figure 2.** Difference between each model's NAO pattern and ERA5's. Both patterns are per one
standard deviation of their own index, so this also shows if a model's NAO swings are weaker.
""")

md("""
## 4. The NAO index
""")

step("""
**What this cell does.** Plots the NAO index of every winter, one panel per source. Each index is
in units of its own standard deviation.
""", """
index_panels = {NAME[s]: {s: (eofs[s].index.year.values, eofs[s].index.values)} for s in SOURCES}
plotting.plot_line_panels(index_panels, ylabel='NAO index (SD)', xlabel='winter (year of January)',
                          title='Winter NAO index, 1951-2014', sharey=True);
""")

md("""
**Figure 3.** The NAO index. The ERA5 panel is the real history. The model panels are each model's
own history and should not line up with ERA5 winter by winter.
""")

step("""
**What this cell does.** A sanity check of the method against well-known winters. It lists the five
most positive and five most negative NAO winters in ERA5, and prints the index for a few winters
that are well known in the literature: strongly positive 1989 and 1995, strongly negative 1963,
1969 and 2010.
""", """
era5_index = eofs['era5'].index.to_series()
print('well-known winters:', {int(y): round(float(era5_index[y]), 2) for y in (1963, 1969, 1989, 1995, 2010)})
pd.DataFrame({'most positive winters': era5_index.nlargest(5).index.values,
              'index (SD)': era5_index.nlargest(5).values,
              'most negative winters': era5_index.nsmallest(5).index.values,
              'index (SD) ': era5_index.nsmallest(5).values})
""")

md("""
## 5. Cross-checks: a station-style index and a common pattern

Two independent checks that the EOF index really is the NAO, and a fairer way to compare strength.
""")

step("""
**What this cell does.** Computes the classic station-style NAO, which needs no EOF at all:
normalised pressure near the Azores minus normalised pressure near Iceland (nearest grid points to
38°N 25°W and 65°N 20°W). It then correlates that with the EOF index. A high correlation means the
leading EOF is the NAO and not some other pattern.
""", """
station = {s: nao.station_index(winters[s]) for s in SOURCES}
pd.DataFrame([{'source': NAME[s],
               'correlation of EOF index with station-style index': float(np.corrcoef(eofs[s].index, station[s])[0, 1])}
              for s in SOURCES])
""")

step("""
**What this cell does.** Compares the models with ERA5 on a common basis. Each model's winter maps
are projected onto the **ERA5** pattern. That answers two separate questions: (1) is the model's own
leading pattern the same mode as ERA5's NAO (correlation of the two model series), and (2) how
strongly does the model swing along the real NAO pattern (amplitude relative to ERA5, 1.00 = same).
""", """
rows = []
for s in SOURCES:
    projected = nao.project(winters[s], eofs['era5'].vector)
    rows.append({'source': NAME[s],
                 'own-pattern amplitude / ERA5': eofs[s].amplitude / eofs['era5'].amplitude,
                 'amplitude along the ERA5 pattern / ERA5': float(projected.std(ddof=1)) / eofs['era5'].amplitude,
                 'correlation: own index vs index on ERA5 pattern': float(np.corrcoef(eofs[s].index, projected)[0, 1])})
common = pd.DataFrame(rows)
projected_index = {s: nao.project(winters[s], eofs['era5'].vector) / eofs['era5'].amplitude for s in SOURCES}
common
""")

step("""
**What this cell does.** Checks whether a model spreads the real NAO over more than one of its own
patterns. It measures how much of the ERA5 NAO pattern each of a model's first three EOFs contains
(1 = identical pattern, 0 = unrelated). If the second EOF also has a large share, the model's
leading EOF is a mixture and is not a clean NAO.
""", """
rows = []
for m in MODELS:
    shares = [nao.overlap(v, eofs['era5'].vector) for v in nao.mode_vectors(winters[m], 3)]
    rows.append({'model': NAME[m], 'EOF1 overlap with ERA5 NAO': shares[0], 'EOF2 overlap': shares[1], 'EOF3 overlap': shares[2]})
pd.DataFrame(rows)
""")

md("""
**How to read this.** An amplitude ratio below 1 means the model's NAO swings are weaker than
observed. With 64 winters, the sampling uncertainty of a standard deviation is roughly ±9%
(one standard error), and a ratio of two of them about ±13%. Ratios between about 0.75 and 1.25
are therefore not clearly different from 1.
""")

md("""
## 6. Behaviour in time: persistence and trend
""")

step("""
**What this cell does.** Measures two properties of each index: its memory from one winter to the
next (lag-1 autocorrelation; near 0 means each winter is almost independent) and its linear trend
over 1951–2014 with a 95% confidence interval.
""", """
rows = []
for s in SOURCES:
    series = eofs[s].index
    t = nao.trend(series.year.values, series.values)
    rows.append({'source': NAME[s], 'lag-1 autocorrelation': nao.autocorrelation(series.values, 1),
                 'trend (SD per decade)': t['trend per decade'], '95% low': t['low'], '95% high': t['high'], 'p value': t['p value']})
print('95% range of lag-1 autocorrelation for', n, 'independent winters: about ±', round(1.96 / np.sqrt(n), 2))
pd.DataFrame(rows)
""")

step("""
**What this cell does.** Plots the autocorrelation at lags of 1 to 10 winters, to see if any source
has slow, multi-year swings in its NAO.
""", """
lags = list(range(1, 11))
plotting.plot_line_panels({'Autocorrelation of the winter NAO index': {s: (lags, [nao.autocorrelation(eofs[s].index.values, k) for k in lags]) for s in SOURCES}},
                          ylabel='autocorrelation', xlabel='lag (winters)', columns=1);
""")

md("""
**Figure 4.** Autocorrelation of the NAO index. Values inside roughly ±0.25 cannot be told apart
from zero with 64 winters.
""")

md("""
## 7. Does the mean-state bias look like the NAO?

Notebook 03 found that ICON-ESM-ER's *average* winter pressure is too low in the north and too
high in the subtropics. That has the same shape as a positive NAO. This section measures it.
""")

step("""
**What this cell does.** Takes each model's average winter pressure minus ERA5's (the mean bias,
1951–2014) and projects it onto the ERA5 NAO pattern. The result is expressed in NAO standard
deviations: a value of +2 would mean the model's *average* winter looks like a +2 SD NAO winter
in the real world.
""", """
mean_winter = {s: clim.climatology(psl[s], 'DJF') for s in SOURCES}
pd.DataFrame([{'model': NAME[m],
               'mean pressure bias projected on the ERA5 NAO (SD)':
                   nao.project_map(mean_winter[m] - mean_winter['era5'], eofs['era5'].vector) / eofs['era5'].amplitude}
              for m in MODELS])
""")

md("""
**Why this matters.** A model can have a realistic NAO *variability* around an unrealistic *mean*.
Extremes depend on the actual flow (mean plus anomaly), so a model that sits permanently in a
positive-NAO-like state may have biased storm-track rainfall even if its NAO index looks fine.
""")

md("""
## 8. Saved outputs
""")

step("""
**What this cell does.** Saves the winter NAO indices as a small Parquet table in `app_assets/`,
for the NAO-to-extremes notebook and the dashboard. Three versions are kept per source: the index
from the source's own pattern, the index on the common ERA5 pattern, and the station-style index.
A JSON file of the same name records how the table was made: code version (git commit), date,
input datasets with their server versions, and period.
""", """
table = pd.concat([pd.DataFrame({'year': eofs[s].index.year.values, 'source': s,
                                 'nao_own_pattern': eofs[s].index.values,
                                 'nao_on_era5_pattern': projected_index[s].values,
                                 'nao_station_style': station[s].values}) for s in SOURCES], ignore_index=True)
out = Path('../app_assets'); out.mkdir(exist_ok=True)
from eerie_uk import provenance
inputs = {s: provenance.dataset_ids(s, 'mon', 'psl', 'north_atlantic') for s in SOURCES}
provenance.write_table(table, out / 'nao_index_winter.parquet', 'Winter (DJF) NAO index per source: own leading EOF, projection on the ERA5 EOF (ERA5 SD units), station-style index', inputs=inputs, period='winters 1951-2014', method='docs/methods.md section 3')
print(len(table), 'rows saved to app_assets/nao_index_winter.parquet')
table.groupby('source')[['nao_own_pattern', 'nao_on_era5_pattern', 'nao_station_style']].agg(['mean', 'std']).round(2)
""")

md("""
## 9. Limitations

- **One member per model, 64 winters.** The NAO is noisy. Differences in strength of 10–20% and in
  explained variance of several percentage points are within sampling uncertainty.
- **ERA5 before about 1979** has fewer observations over the ocean; its early NAO is less certain
  but pressure is one of the best-observed quantities.
- **The pattern depends on the domain and the period.** A different box or different years would
  shift the centres slightly. The same box and years are used for all three sources.
- **Winter means only.** Month-to-month NAO behaviour within a winter is not examined here.
- **Different forcing.** The models follow the HighResMIP `hist-1950` protocol, ERA5 the real world,
  so trends need not agree.
- **The mean-state projection (section 7)** describes the bias; it does not explain its cause.
""")

md("""
## 10. Open questions

1. Is the weak NAO of both models a property of the models or of single members? Notebook 07 shows
   that identical atmosphere-only runs give NAO strengths from 0.70 to 1.00 of ERA5's.
2. Would a different domain or period give ICON-ESM-ER a cleaner leading pattern?
3. Does ICON-ESM-ER's positive-NAO-like mean state alter how its extremes respond to the NAO?
   Notebook 06 addresses this.
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
