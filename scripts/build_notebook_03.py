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
# 03 · Validation and historical baseline

**Question for this notebook.** Before interpreting the NAO or extremes: are the basic fields of
the two EERIE models credible? Each model is compared with ERA5 for sea-level pressure,
2 m temperature and precipitation.

**What is used.** Monthly data only, 1950–2014, from the files described in notebook 02:
ICON-ESM-ER (r1), IFS-FESOM2-SR (r1) and ERA5. Climate maps use **1985–2014**, the same 30 years
as the daily data that the extremes will come from. Time series use the full 1950–2014.

**How to read it.** Every code cell has a note above it. Every figure has a caption. Section 2
has the findings in plain words; the last section lists open questions.

**An important reminder.** A free-running climate model makes its own weather. Its winter of 1990
is not *the* winter of 1990. So a model and ERA5 should agree in their **averages, year-to-year
spread and seasonal cycle**, not year by year.

**Sections**
1. Setup
2. Findings
3. Is the downloaded data complete and consistent?
4. Sea-level pressure over the North Atlantic
5. Temperature over north-west Europe
6. Precipitation over north-west Europe
7. Seasonal cycle in the three regions
8. Year-to-year variability and time series
9. Summary table
10. Limitations
11. Open questions
""")

md("""
## Background: the terms used in this notebook

If you know these already, skip to section 1.

| Term | What it means here |
|---|---|
| **Climate model run (free-running)** | A simulation that starts in 1950 and creates its own weather from then on. It knows the rising greenhouse gases but not the real weather of any particular day or year. |
| **Member (r1)** | One such simulation. Running the same model again from slightly different starting conditions gives another member with different weather. We have one member per model. |
| **Reanalysis (ERA5)** | A reconstruction of the real past weather, made by feeding observations into a weather model. It is the reference here. It is close to observations for pressure and temperature, less so for rainfall. |
| **Climatology** | The long-term average, here over 1985–2014. "Winter climatology" is the average of all winters. |
| **DJF, JJA** | December–January–February (winter) and June–July–August (summer). A winter is named after the year of its January. |
| **Bias** | Model average minus reference average. Positive temperature bias = model too warm. |
| **Year-to-year standard deviation** | How much a seasonal average typically differs from one year to the next. A model with too small a value has winters that are too alike. |
| **RMSE (root-mean-square error)** | The typical size of the difference between two maps, point by point, ignoring its sign. Same units as the data; 0 is perfect. |
| **Pattern correlation** | How similar the *shapes* of two maps are, from −1 to 1. A model can have a pattern correlation of 0.99 and still be too warm everywhere. |
| **Area-weighted mean** | An average over a region that accounts for grid cells being smaller towards the pole. |

**How to read the maps.** Maps of a quantity use one blue scale, light to dark. Maps of a
*difference* use blue–grey–orange: grey means no difference, and the two colours mean the two
directions (stated in each caption). All panels of one figure share the same colour scale.

**How to read the line charts.** Dark grey is always ERA5, blue is always ICON-ESM-ER, orange is
always IFS-FESOM2-SR, in every figure of this project.
""")

md("## 1. Setup")

step("""
**What this cell does.** Loads the project code. `store` reads the downloaded files, `climatology`
computes seasonal means and comparison statistics, `plotting` draws the figures.
""", """
import sys, warnings
sys.path.insert(0, '../src')
warnings.filterwarnings('ignore')

import pandas as pd
from eerie_uk import climatology as clim, plotting, regions, store

pd.set_option('display.width', 220, 'display.float_format', '{:.2f}'.format)

SOURCES = ['era5', 'icon-esm-er', 'ifs-fesom2-sr']      # reference first
MODELS = SOURCES[1:]
NAME = plotting.SOURCE_LABELS
BASELINE = (1985, 2014)
""")

md("## 2. Findings\n\n" + FINDINGS)

md("""
## 3. Is the downloaded data complete and consistent?

Analysis on incomplete files gives wrong answers quietly, so this is checked first.
""")

step("""
**What this cell does.** Lists every downloaded monthly field with its first and last year, the
number of yearly files and any missing years (`gaps` should be empty).
""", """
inventory = store.available()
monthly = inventory[(inventory.frequency == 'mon') & inventory.source.isin(SOURCES)].reset_index(drop=True)
monthly
""")

step("""
**What this cell does.** Loads all nine monthly fields into memory (they are small) and checks the
time axis of each: the number of months, that no month is missing or duplicated, and the value
range. The three sources stamp months differently on the server; `store.load` puts them all on the
first day of the month, and this table confirms that worked.
""", """
FIELDS = {'psl': 'north_atlantic', 'tas': 'nw_europe', 'pr': 'nw_europe'}
data = {(s, v): store.load(s, 'mon', v, box) for s in SOURCES for v, box in FIELDS.items()}

expected = pd.date_range('1950-01-01', '2014-12-01', freq='MS')
checks = pd.DataFrame([{
    'source': NAME[s], 'variable': v, 'months': da.sizes['time'],
    'time axis complete': bool(da.sizes['time'] == len(expected) and (da.time.values == expected.values).all()),
    'grid (lat x lon)': f"{da.sizes['lat']} x {da.sizes['lon']}", 'units': da.attrs.get('units'),
    'min': float(da.min()), 'mean': float(da.mean()), 'max': float(da.max()), 'missing values': int(da.isnull().sum()),
} for (s, v), da in data.items()])
checks
""")

md("""
**What to look for.** 780 months each (65 years × 12), `time axis complete = True`, no missing
values, the same grid for all three sources of a variable, and plausible ranges: pressure roughly
960–1050 hPa, temperature roughly −30 to +32 °C, precipitation from 0 to a few tens of mm/day.
""")

md("""
### Check of the IFS-FESOM2-SR decoding fix

IFS-FESOM2-SR arrives as raw GRIB messages that the current ecCodes library cannot read as they are;
`eerie_uk.grib` removes a bookkeeping section from each message before decoding (see the README).
That fix deserves an independent check before any result depends on it.

**Check A, done outside this notebook.** The same raw message (daily mean sea-level
pressure, 1 January 1950) was decoded twice: once with an older ecCodes (2.28) that reads the
message unmodified, and once with the current ecCodes (2.49) after the fix. Both gave exactly the
same field: 1,038,240 values, minimum 95060.4014 Pa, maximum 104629.0508 Pa.

**Check B, below.** The model publishes daily *and* monthly files. If daily values are decoded
correctly, their average over a month must reproduce the model's own monthly file.
""")

step("""
**What this cell does.** Downloads the 31 daily precipitation fields of January 1990 from
IFS-FESOM2-SR (about 20 seconds), averages them, and compares the result with the January 1990
field in the model's monthly file. The two come from different files on the server, so agreement
means the daily decoding, the box cut-out and the unit conversion are all consistent.
""", """
from eerie_uk import download as dl

daily_request = next(r for r in dl.build_plan() if r.source == 'ifs-fesom2-sr' and r.frequency == 'day' and r.variable == 'pr')
january_from_daily = dl.fetch(daily_request, '1990-01-01', '1990-01-31T23:59:59').mean('time')
january_monthly = data['ifs-fesom2-sr', 'pr'].sel(time='1990-01-01')
difference = january_from_daily - january_monthly
pd.DataFrame([{
    'mean of 31 daily fields (mm/day)': float(january_from_daily.mean()),
    'monthly file (mm/day)': float(january_monthly.mean()),
    'largest local difference (mm/day)': float(abs(difference).max()),
    'pattern correlation': clim.pattern_stats(january_from_daily, january_monthly)['pattern correlation'],
}])
""")

md("""
**What to look for.** The two means should agree closely, the largest local difference should be
tiny compared with the values themselves, and the pattern correlation should be essentially 1.
A wrong decoding would give noise or a different pattern.
""")

md("""
## 4. Sea-level pressure over the North Atlantic

The NAO is the see-saw between the Icelandic low and the Azores high. If the *average* winter
pressure field or its year-to-year variability is wrong, the NAO built on it will be too.
""")

step("""
**What this cell does.** Computes the average winter (December–February) sea-level pressure for
1985–2014 for each source and maps them side by side on one colour scale.
""", """
psl_djf = {s: clim.climatology(clim.period(data[s, 'psl'], *BASELINE), 'DJF') for s in SOURCES}
plotting.plot_field_panels({NAME[s]: f for s, f in psl_djf.items()}, units='hPa',
                           title='Winter (DJF) mean sea-level pressure, 1985-2014');
""")

md("""
**Figure 1.** Average winter pressure. All three show the Icelandic low and the Azores high; the
question is how well their position and depth agree, which the next figure isolates.
""")

step("""
**What this cell does.** Subtracts ERA5 from each model to show the *bias*: orange where the model's
pressure is too high, blue where it is too low, grey where they agree.
""", """
psl_bias = {f'{NAME[m]} minus ERA5': psl_djf[m] - psl_djf['era5'] for m in MODELS}
plotting.plot_field_panels(psl_bias, units='hPa', title='Winter mean sea-level pressure: model minus ERA5', diverging=True);
""")

md("""
**Figure 2.** Winter pressure bias. A dipole of opposite colours north and south means the model's
average westerly flow is too strong or too weak; a single colour means a pressure offset.
""")

step("""
**What this cell does.** Maps the year-to-year standard deviation of winter-mean pressure: how
much one winter differs from the next. This is the variability the NAO analysis will decompose.
""", """
psl_std = {s: clim.interannual_std(clim.period(data[s, 'psl'], *BASELINE), 'DJF') for s in SOURCES}
plotting.plot_field_panels({NAME[s]: f for s, f in psl_std.items()}, units='hPa',
                           title='Year-to-year standard deviation of winter mean pressure, 1985-2014');
""")

md("""
**Figure 3.** Winter pressure variability. In ERA5 it peaks near Iceland and Greenland. With only
29 winters this field is itself uncertain, so moderate differences between panels are expected
even from a perfect model.
""")

md("""
## 5. Temperature over north-west Europe
""")

step("""
**What this cell does.** Computes the 1985–2014 mean 2 m temperature for winter and summer and maps
each model's difference from ERA5. Winter and summer are shown together because a model can be too
cold in one season and too warm in the other.
""", """
tas_clim = {(s, season): clim.climatology(clim.period(data[s, 'tas'], *BASELINE), season)
            for s in SOURCES for season in ('DJF', 'JJA')}
tas_bias = {f'{NAME[m]}, {season}': tas_clim[m, season] - tas_clim['era5', season]
            for season in ('DJF', 'JJA') for m in MODELS}
plotting.plot_field_panels(tas_bias, units='°C', title='2 m temperature: model minus ERA5, 1985-2014', columns=2, diverging=True);
""")

md("""
**Figure 4.** Temperature bias, winter (top) and summer (bottom). Orange is too warm, blue too cold.
Sharp spots over mountains mostly reflect different model terrain height, not a climate error.
""")

md("""
## 6. Precipitation over north-west Europe
""")

step("""
**What this cell does.** Maps the 1985–2014 winter mean precipitation for each source, to see
whether the models put the rain in the right places (west-facing coasts and mountains).
""", """
pr_clim = {(s, season): clim.climatology(clim.period(data[s, 'pr'], *BASELINE), season)
           for s in SOURCES for season in ('DJF', 'JJA')}
plotting.plot_field_panels({NAME[s]: pr_clim[s, 'DJF'] for s in SOURCES}, units='mm/day',
                           title='Winter (DJF) mean precipitation, 1985-2014');
""")

md("""
**Figure 5.** Winter precipitation. The wettest areas should be western Scotland, western Norway,
north-west Iberia and the Alps.
""")

step("""
**What this cell does.** Maps each model's precipitation difference from ERA5 in winter and summer.
""", """
pr_bias = {f'{NAME[m]}, {season}': pr_clim[m, season] - pr_clim['era5', season]
           for season in ('DJF', 'JJA') for m in MODELS}
plotting.plot_field_panels(pr_bias, units='mm/day', title='Precipitation: model minus ERA5, 1985-2014', columns=2, diverging=True);
""")

md("""
**Figure 6.** Precipitation bias, winter (top) and summer (bottom). Orange is too wet, blue too dry.
ERA5 precipitation is itself a model product, so over land this compares two models; E-OBS will
give a firmer answer in the extremes notebook.
""")

md("""
## 7. Seasonal cycle in the three regions
""")

step("""
**What this cell does.** Averages temperature over each sub-region (UK and Ireland, western Norway,
north-west France) and plots the mean of each calendar month, 1985–2014: one line per source.
""", """
months = (list(range(1, 13)), list('JFMAMJJASOND'))
def cycle_panels(variable):
    return {regions.LABELS[r]: {s: (list(range(1, 13)),
                                    clim.monthly_cycle(clim.regional_mean(clim.period(data[s, variable], *BASELINE), r)).values)
                                for s in SOURCES} for r in regions.SUBREGIONS}
plotting.plot_line_panels(cycle_panels('tas'), ylabel='°C', title='Seasonal cycle of 2 m temperature, 1985-2014', xticks=months);
""")

md("""
**Figure 7.** Seasonal cycle of temperature. The lines should have the same shape and timing; a
constant gap is a mean bias, a gap that opens in one season is a seasonal bias.
Region averages include sea points inside each box.
""")

step("""
**What this cell does.** The same for precipitation.
""", """
plotting.plot_line_panels(cycle_panels('pr'), ylabel='mm/day', title='Seasonal cycle of precipitation, 1985-2014', xticks=months);
""")

md("""
**Figure 8.** Seasonal cycle of precipitation. The UK and western Norway are wettest in autumn and
winter; a model that gets the cycle right has the storm track in roughly the right place through
the year.
""")

md("""
## 8. Year-to-year variability and time series
""")

step("""
**What this cell does.** Plots winter-mean temperature for every year 1950–2014 in each region.
The model lines are **not** expected to follow ERA5 year by year; compare their level, their spread
and their long-term drift.
""", """
def series_panels(variable, season):
    panels = {}
    for r in regions.SUBREGIONS:
        panels[regions.LABELS[r]] = {}
        for s in SOURCES:
            means = clim.season_means(clim.regional_mean(data[s, variable], r), season)
            panels[regions.LABELS[r]][s] = (means.year.values, means.values)
    return panels
tas_series = series_panels('tas', 'DJF')
plotting.plot_line_panels(tas_series, ylabel='°C', xlabel='winter (year of January)', title='Winter (DJF) mean 2 m temperature, 1950-2014');
""")

md("""
**Figure 9.** Winter temperature, 1950–2014. Each source has its own sequence of cold and mild
winters. What matters is that the size of the swings is similar.
""")

step("""
**What this cell does.** The same for winter-mean precipitation.
""", """
pr_series = series_panels('pr', 'DJF')
plotting.plot_line_panels(pr_series, ylabel='mm/day', xlabel='winter (year of January)', title='Winter (DJF) mean precipitation, 1950-2014');
""")

md("""
**Figure 10.** Winter precipitation, 1950–2014. Again compare level and spread, not individual years.
""")

step("""
**What this cell does.** Turns the 64 winters (1951–2014) into distributions: how often each winter-mean
temperature occurs in each source. Overlapping outlines mean the model produces the same range of
winters as ERA5.
""", """
plotting.plot_histogram_panels({k: {s: xy[1] for s, xy in v.items()} for k, v in tas_series.items()},
                               xlabel='winter mean temperature (°C)', bins=12,
                               title='Distribution of winter mean temperature, 64 winters');
""")

md("""
**Figure 11.** Distribution of winter-mean temperature. With 65 values per line the outlines are
rough; look at where the bulk sits and how wide it is.
""")

step("""
**What this cell does.** The same distributions for winter-mean precipitation.
""", """
plotting.plot_histogram_panels({k: {s: xy[1] for s, xy in v.items()} for k, v in pr_series.items()},
                               xlabel='winter mean precipitation (mm/day)', bins=12,
                               title='Distribution of winter mean precipitation, 64 winters');
""")

md("""
**Figure 12.** Distribution of winter-mean precipitation in the three regions.
""")

md("""
## 9. Summary table
""")

step("""
**What this cell does.** Puts the map comparisons into numbers. For each model, variable and season
over the whole downloaded box (1985–2014): the area-average bias, the root-mean-square error (the
typical size of the local difference) and the pattern correlation (1 = identical pattern).
""", """
rows = []
for variable, fields in (('psl', {(s, 'DJF'): psl_djf[s] for s in SOURCES}), ('tas', tas_clim), ('pr', pr_clim)):
    for season in ('DJF', 'JJA'):
        if ('era5', season) not in fields:
            continue
        for m in MODELS:
            rows.append({'variable': variable, 'season': season, 'model': NAME[m],
                         'ERA5 mean': float(clim.regions.area_mean(fields['era5', season])),
                         **clim.pattern_stats(fields[m, season], fields['era5', season])})
summary = pd.DataFrame(rows)
summary
""")

step("""
**What this cell does.** The same idea per sub-region, for the quantities the later notebooks rely
on: the regional mean and the year-to-year standard deviation of the winter mean, 1950–2014.
A ratio of 1.0 in the last column means the model has the same year-to-year spread as ERA5.
""", """
rows = []
for variable, panels in (('tas (°C)', tas_series), ('pr (mm/day)', pr_series)):
    for region, by_source in panels.items():
        reference = by_source['era5'][1]
        for m in MODELS:
            values = by_source[m][1]
            rows.append({'variable': variable, 'region': region, 'model': NAME[m],
                         'ERA5 mean': reference.mean(), 'model mean': values.mean(), 'bias': values.mean() - reference.mean(),
                         'ERA5 std': reference.std(ddof=1), 'model std': values.std(ddof=1),
                         'std ratio': values.std(ddof=1) / reference.std(ddof=1)})
regional = pd.DataFrame(rows)
regional
""")

md("""
## 10. Limitations

- **One member per model.** Differences from ERA5 mix real model bias with chance, especially for
  variability over 29 winters.
- **ERA5 is the yardstick, not the truth.** Its pressure and temperature are well constrained by
  observations; its precipitation is a model product.
- **ERA5 was interpolated** from its own grid to the model grid, which smooths it slightly.
- **Terrain is not accounted for.** Temperature differences over mountains partly reflect different
  surface heights in each model.
- **Region averages include sea points.**
- **Seasonal means weight months equally,** not by their number of days.
- **Different forcing history.** The models follow the HighResMIP `hist-1950` protocol; ERA5 follows
  the real world. Trends need not match.
""")

md("""
## 11. Open questions

1. How much of ICON-ESM-ER's pressure dipole bias would remain in other members of the same model?
2. Is the cold winter bias shared by both models a feature of the 2 m temperature diagnostic, of the
   land surface, or of the circulation?
3. How much of the wet bias over mountains is a limitation of ERA5 precipitation rather than of the
   models? Notebook 05 adds the station-based E-OBS data to test this.
""")

nb.cells = cells
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, sys.argv[1])
