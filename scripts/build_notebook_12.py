"""Generate notebooks/12_hadgem_resolution.ipynb.  Usage: python build_notebook_12.py OUT.ipynb [findings.md]"""
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
# 12 · One coupled model at three resolutions: HadGEM3-GC5E

**Question for this notebook.** Notebook 08 compared one atmosphere model (IFS) at 9 km and 28 km
with the same prescribed sea-surface temperature. Here the question is the coupled version: does a
coupled model's winter circulation, NAO and the NAO's rainfall response improve as both its
atmosphere and its ocean get finer? The Met Office ran its EERIE configuration of HadGEM3-GC5E at
three resolutions with the same physics:

| Configuration | Atmosphere | Ocean |
|---|---|---|
| **LL** | about 135 km (N96) | 1° |
| **MM** | about 60 km (N216) | 1/4° |
| **HH** | about 20 km (N640) | 1/12°, eddy-rich |

**Atmosphere and ocean change together.** In these configurations the atmospheric and the oceanic
resolution are refined at the same time. The comparison therefore evaluates three coupled
resolution configurations; it cannot isolate the effect of the atmospheric grid from that of the
ocean grid and of their interaction.

**Data.** Historical runs, one member each, monthly fields from the public CEDA archive, 1950–2014:
sea-level pressure (North Atlantic), precipitation and near-surface temperature (north-west
Europe), and zonal wind at 850 hPa (LL and MM; HH's wind was not downloaded because of its size).
Daily data, and therefore the extreme indices of notebooks 05–06, are not publicly available for
these runs. References: ERA5 (pressure, rain, temperature, wind). ICON-ESM-ER and IFS-FESOM2-SR r1
are shown for context.

**How the grids are compared.** Each model is interpolated bilinearly onto the grid used for the
other datasets: 1° for pressure and wind (as in notebook 04), 0.25° for rain and temperature
(as in notebook 03). LL's grid is coarser than both, so its maps look smoother.

**How chance is judged.** One member per resolution. Notebook 07 showed that ten identical runs of
one atmosphere model give NAO strengths from 0.70 to 1.00 of ERA5's over 43 winters, and notebooks
10 and 11 that three coupled runs and long control runs vary by about ±0.1. Differences between the
three resolutions smaller than that are not attributed to resolution. Each 64-winter record is also
split into two halves to show how much a single run varies with time.

**Sections**
1. Setup
2. Findings
3. Mean winter circulation
4. The NAO at three resolutions
5. Winter rain and temperature over UK and Ireland
6. The NAO's influence on winter rain
7. The jet stream (and the three configurations side by side, 7b)
8. Saved outputs
9. Limitations
10. Open questions
""")

md("""
## Background: the terms used in this notebook

| Term | What it means here |
|---|---|
| **Resolution ladder** | The same model at several grid spacings, so that differences between them can be attributed to resolution (and to everything that changes with it), not to different physics. |
| **Eddy-rich ocean** | An ocean grid fine enough (here 1/12°, about 8 km) to resolve ocean eddies and sharp fronts such as the Gulf Stream. |
| **NAO strength** | Standard deviation of the winter index measured along the ERA5 NAO pattern, relative to ERA5 (notebook 04). |
| **Mean circulation offset** | The model's average winter pressure minus ERA5's, projected onto the ERA5 NAO pattern, in ERA5 SD (notebook 04, section 7). |
| **Eddy-driven jet** | The band of strongest westerly wind in the lower atmosphere (here 850 hPa) over the Atlantic, where storms grow and travel. Its latitude decides where storms, and winter rain, go. |
| **Jet latitude** | Latitude of the strongest 850 hPa westerly wind, averaged over 60°W–0° (after Woollings et al. 2010), each winter. |
""")

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code and defines the datasets.
""", """
import sys, warnings
sys.path.insert(0, '../src')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from eerie_uk import climatology as clim, nao, plotting, regions, relationships as rel, store

pd.set_option('display.width', 220, 'display.float_format', '{:.2f}'.format)
HADGEM = ['hadgem3-gc5e-ll', 'hadgem3-gc5e-mm', 'hadgem3-gc5e-hh']
CONTEXT = ['icon-esm-er', 'ifs-fesom2-sr']
MODELS = HADGEM + CONTEXT
LABEL = plotting.label_of
WINTERS = (1986, 2014)
""")

step("""
**What this cell does.** Loads monthly sea-level pressure for ERA5 and all models, puts the models
on ERA5's 1° grid, and computes the winter anomalies and the ERA5 NAO pattern exactly as in
notebook 04 (64 winters, 1951–2014).
""", """
era5_psl = store.load('era5', 'mon', 'psl', 'north_atlantic')
psl = {'era5': era5_psl, **{s: regions.regrid(store.load(s, 'mon', 'psl', 'north_atlantic'), era5_psl) for s in MODELS}}
winters = {s: nao.winter_anomalies(p) for s, p in psl.items()}
era5_nao = nao.leading_eof(winters['era5'])
print({LABEL(s): winters[s].sizes['year'] for s in winters})
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. Mean winter circulation
""")

step("""
**What this cell does.** Maps each model's average winter sea-level pressure minus ERA5's over
1986–2014, HadGEM3 at its three resolutions first.
""", """
mean = {s: clim.season_means(p, 'DJF').sel(year=slice(*WINTERS)).mean('year') for s, p in psl.items()}
plotting.plot_field_panels({LABEL(s): mean[s] - mean['era5'] for s in MODELS}, units='hPa', diverging=True, columns=3,
                           title='Winter-mean sea-level pressure minus ERA5, 1986-2014');
""")

md("""
**Figure 1.** Orange: pressure too high; blue: too low. Top row: HadGEM3 LL, MM, HH. Bottom row:
ICON-ESM-ER and IFS-FESOM2-SR r1 for comparison.
""")

step("""
**What this cell does.** Summarises each map: the typical size of the error (root-mean-square,
cosine-weighted), the pattern correlation with ERA5's mean field, and the error expressed as an NAO
state (mean circulation offset).
""", """
weights = np.cos(np.deg2rad(era5_psl.lat))
rows = []
for s in MODELS:
    error = mean[s] - mean['era5']
    rows.append({'model': LABEL(s), 'source': s,
                 'RMS error (hPa)': float(np.sqrt((error ** 2).weighted(weights).mean())),
                 'mean offset along NAO (SD)': nao.project_map(error, era5_nao.vector) / era5_nao.amplitude})
circulation = pd.DataFrame(rows)
circulation.drop(columns='source').set_index('model')
""")

md("""
## 4. The NAO at three resolutions
""")

step("""
**What this cell does.** For each model over 64 winters: NAO strength along the ERA5 pattern, the
variance of its own first two patterns and whether they are separated, and how much its own first
pattern resembles ERA5's. Then the same strength for the first and second half of the record
(1951–1982 and 1983–2014) to show how much one run varies with time.
""", """
rows = []
for s in MODELS:
    e = nao.leading_eof(winters[s])
    spacing = nao.north_spacing(e.explained, winters[s].sizes['year'])
    along = nao.project(winters[s], era5_nao.vector) / era5_nao.amplitude
    era5_along = nao.project(winters['era5'], era5_nao.vector) / era5_nao.amplitude
    halves = [float(along.sel(year=slice(a, b)).std(ddof=1)) / float(era5_along.sel(year=slice(a, b)).std(ddof=1))
              for a, b in ((1951, 1982), (1983, 2014))]
    rows.append({'model': LABEL(s), 'source': s, 'NAO strength relative to ERA5': float(along.std(ddof=1)),
                 'first half': halves[0], 'second half': halves[1],
                 'EOF1 %': 100 * e.explained[0], 'EOF2 %': 100 * e.explained[1],
                 'separated from EOF2': bool(e.explained[0] - spacing[0] > e.explained[1] + spacing[1]),
                 'own pattern vs ERA5': clim.pattern_stats(e.pattern, era5_nao.pattern)['pattern correlation']})
nao_table = pd.DataFrame(rows)
nao_table.drop(columns='source').set_index('model')
""")

step("""
**What this cell does.** Maps the NAO pattern of ERA5 and of HadGEM3 at each resolution.
""", """
plotting.plot_field_panels({LABEL(s): nao.leading_eof(winters[s]).pattern for s in ['era5'] + HADGEM},
                           units='hPa per +1 SD of the index', diverging=True, columns=2,
                           title='The NAO pattern (leading EOF of winter pressure), 1951-2014');
""")

md("""
**Figure 2.** Blue: lower pressure in a positive-NAO winter; orange: higher. ERA5 top left, then
HadGEM3 LL, MM and HH. Look at the position of the southern centre (near the Azores in ERA5) and
the strength of both centres.
""")

md("""
## 5. Winter rain and temperature over UK and Ireland
""")

step("""
**What this cell does.** Puts monthly precipitation and temperature of every model on the 0.25° grid
used in notebook 03 and compares the winter means over UK and Ireland land with ERA5, 1986–2014.
""", """
grid = store.load('icon-esm-er', 'mon', 'pr', 'nw_europe')
land = regions.land_mask(grid.lat, grid.lon)

def winter_mean(source, variable):
    field = store.load(source, 'mon', variable, 'nw_europe')
    field = regions.regrid(field, grid)
    return clim.season_means(field, 'DJF')

pr = {s: winter_mean(s, 'pr') for s in ['era5'] + MODELS}
tas = {s: winter_mean(s, 'tas') for s in ['era5'] + MODELS}
def uk(field):
    return float(clim.regional_mean(field.sel(year=slice(*WINTERS)).mean('year').where(land), 'uk_ireland'))
rows = []
for s in ['era5'] + MODELS:
    rows.append({'dataset': LABEL(s), 'winter rain (mm/day)': uk(pr[s]), 'winter temperature (°C)': uk(tas[s])})
surface = pd.DataFrame(rows).set_index('dataset')
surface['rain vs ERA5 (%)'] = 100 * (surface['winter rain (mm/day)'] / surface.loc['ERA5', 'winter rain (mm/day)'] - 1)
surface['temperature vs ERA5 (°C)'] = surface['winter temperature (°C)'] - surface.loc['ERA5', 'winter temperature (°C)']
surface
""")

step("""
**What this cell does.** Maps the winter rain of HadGEM3 at each resolution relative to ERA5.
""", """
reference = pr['era5'].sel(year=slice(*WINTERS)).mean('year')
plotting.plot_field_panels({LABEL(s): 100 * (pr[s].sel(year=slice(*WINTERS)).mean('year') / reference - 1) for s in HADGEM},
                           units='% difference from ERA5', diverging=True, limit=60, columns=3,
                           title='Winter-mean precipitation relative to ERA5, 1986-2014');
""")

md("""
**Figure 3.** Orange: wetter than ERA5; blue: drier. Mountains and west-facing coasts are where finer
grids are expected to add rain.
""")

md("""
## 6. The NAO's influence on winter rain
""")

step("""
**What this cell does.** Regresses winter-mean precipitation on each dataset's own NAO index (along
the ERA5 pattern) at every grid cell, 1951–2014, both series detrended. Dots mark cells that pass
the false-discovery-rate test.
""", """
index = {s: nao.project(winters[s], era5_nao.vector) / era5_nao.amplitude for s in ['era5'] + MODELS}
response, mask = {}, {}
for s in ['era5'] + HADGEM:
    result = rel.correlate(pr[s].sel(year=slice(1951, 2014)), index[s])
    response[LABEL(s)] = result.slope
    mask[LABEL(s)] = rel.fdr_mask(result.p)
plotting.plot_field_panels(response, units='mm/day per +1 SD of NAO', diverging=True, stipple=mask, columns=2,
                           title='Change in winter-mean precipitation per +1 SD of NAO, 1951-2014');
""")

md("""
**Figure 4.** Orange: wetter in positive-NAO winters; blue: drier. ERA5 top left. The real pattern is
wetter in the north-west (Scotland, Norway) and drier in the south (France, Iberia).
""")

step("""
**What this cell does.** Summarises the response maps: pattern correlation with ERA5's response
over land, and the correlation between the NAO and winter rain averaged over each region.
""", """
era5_response = response['ERA5']
rows = []
for s in ['era5'] + MODELS:
    result = rel.correlate(pr[s].sel(year=slice(1951, 2014)), index[s])
    both = land & result.slope.notnull() & era5_response.notnull()
    row = {'dataset': LABEL(s), 'pattern correlation with ERA5 (land)': clim.pattern_stats(result.slope.where(both), era5_response.where(both))['pattern correlation']}
    for region in regions.SUBREGIONS:
        series = clim.regional_mean(pr[s].sel(year=slice(1951, 2014)).where(land), region)
        row[f'r, {regions.LABELS[region]}'] = rel.regress_series(series.values, index[s].sel(year=series.year).values)['r']
    rows.append(row)
rain_link = pd.DataFrame(rows).set_index('dataset')
rain_link
""")

md("""
## 7. The jet stream
""")

step("""
**What this cell does.** Loads the monthly 850 hPa zonal wind of ERA5 and HadGEM3 LL and MM, takes
the winter mean and the average over 60°W–0°, and finds the latitude of the strongest wind in each
winter (the eddy-driven jet). HH is not included (its wind was not downloaded: about 25 GB).
""", """
JET_MODELS = ['era5', 'hadgem3-gc5e-ll', 'hadgem3-gc5e-mm']
profile, latitude = {}, {}
for s in JET_MODELS:
    ua = store.load(s, 'mon', 'ua', 'north_atlantic').sel(plev=85000)
    if s != 'era5':
        ua = regions.regrid(ua, store.load('era5', 'mon', 'ua', 'north_atlantic').sel(plev=85000))
    u = clim.season_means(ua.sel(lon=slice(-60, 0)), 'DJF').sel(year=slice(1951, 2014)).mean('lon')
    u = u.sortby('lat').sel(lat=slice(15, 75))
    profile[s] = u.mean('year')
    latitude[s] = u.lat[u.argmax('lat')].rename('jet latitude')
rows = []
for s in JET_MODELS:
    rows.append({'dataset': LABEL(s), 'mean jet latitude (°N)': float(latitude[s].mean()),
                 'year-to-year SD (°)': float(latitude[s].std(ddof=1)),
                 'peak wind of the mean profile (m/s)': float(profile[s].max()),
                 'latitude of the mean-profile peak (°N)': float(profile[s].lat[profile[s].argmax()])})
jet = pd.DataFrame(rows).set_index('dataset')
jet
""")

step("""
**What this cell does.** Draws the mean winter 850 hPa wind against latitude for ERA5 and the two
HadGEM3 resolutions.
""", """
plotting.plot_line_panels({'Winter 850 hPa zonal wind, 60°W-0°, 1951-2014': {s: (profile[s].lat.values, profile[s].values) for s in JET_MODELS}},
                          xlabel='latitude (°N)', ylabel='m/s', columns=1);
""")

md("""
**Figure 5.** The peak of each curve is the average position of the eddy-driven jet. A peak too far
north or south moves the storm track, and the winter rain, with it.
""")

md("""
## 7b. The three configurations side by side
""")

step("""
**What this cell does.** Summarises the configurations in one figure: a sketch of the grid spacing
(atmosphere and ocean refined together) and three diagnostics from the tables above.
""", """
ladder = pd.DataFrame([{'source': s, 'atmosphere_km': km, 'ocean': ocean,
                        'rms_error': circulation.set_index('source').loc[s, 'RMS error (hPa)'],
                        'pattern_r': nao_table.set_index('source').loc[s, 'own pattern vs ERA5'],
                        'rain_bias': surface.loc[LABEL(s), 'rain vs ERA5 (%)']}
                       for s, km, ocean in (('hadgem3-gc5e-ll', 135, '1°'), ('hadgem3-gc5e-mm', 60, '1/4°'),
                                            ('hadgem3-gc5e-hh', 20, '1/12°'))])
plotting.plot_resolution_ladder(ladder);
""")

md("""
**Figure 6.** Left: the grid spacing of each configuration (schematic; atmosphere and ocean refined
together). Right: winter pressure error and NAO pattern correlation improve across the tested coupled
configurations, while winter-mean rain over UK and Ireland rises sharply at the finest one. NAO strength,
not shown, does not follow resolution (section 4).
""")

md("""
## 8. Saved outputs
""")

step("""
**What this cell does.** Saves the circulation, NAO, surface, rain-link and jet tables with provenance.
""", """
from eerie_uk import provenance
out = Path('../app_assets')
meta = dict(inputs={'HadGEM3-GC5E': 'CEDA EERIE archive, historical r1i1p1f1, Amon', 'ERA5': 'DKRZ'},
            period='1951-2014 (NAO, rain link, jet), 1986-2014 (means)')
provenance.write_table(circulation, out / 'hadgem_circulation.parquet', 'Winter mean pressure error per model', **meta)
provenance.write_table(nao_table, out / 'hadgem_nao.parquet', 'NAO strength, EOF variance and pattern per model', **meta)
provenance.write_table(surface.reset_index(), out / 'hadgem_surface_uk.parquet', 'UK and Ireland winter rain and temperature vs ERA5', **meta)
provenance.write_table(rain_link.reset_index(), out / 'hadgem_rain_link.parquet', 'NAO influence on winter-mean rain per model', **meta)
provenance.write_table(jet.reset_index(), out / 'hadgem_jet.parquet', 'Winter 850 hPa jet latitude and strength', **meta)
print('saved 5 tables')
""")

md("""
## 9. Limitations

- **One member per resolution.** Differences between LL, MM and HH mix resolution with chance. Only
  differences larger than the chance ranges of notebooks 07, 10 and 11, and consistent across the
  two halves of the record, are attributed to resolution.
- **Monthly data only.** Extremes (RX1day, R95p, TXx), the event composites and the storminess
  diagnostics cannot be computed; they need daily data, which are not publicly available.
- **Compared on common grids.** Interpolation onto the 1° and 0.25° grids smooths HH's detail and
  invents none for LL.
- **Rain compared with ERA5 only** (E-OBS was downloaded as daily data for 1985–2014 only);
  ERA5 rain is itself a model product.
- **No HH wind.** The jet comparison covers LL and MM only.
""")

md("""
## 10. Open questions

1. Does the improvement of the mean circulation with resolution continue into extremes? Daily
   HadGEM3 data (JASMIN) would answer it with the code of notebooks 05, 06 and 09 unchanged.
2. Is the eddy-rich ocean or the finer atmosphere responsible? Runs that change one at a time
   would separate them.
3. With more members at each resolution, would a resolution effect on NAO strength appear?
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
