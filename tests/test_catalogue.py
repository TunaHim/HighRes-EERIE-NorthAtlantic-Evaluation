import pandas as pd
import pytest

from eerie_uk import catalogue as cat
from eerie_uk import jasmin

IDS = [
    "icon-esm-er.hist-1950.v20240618.atmos.gr025.2d_daily_mean",
    "icon-esm-er.hist-1950.v20240618.atmos.gr025.2d_daily_max",
    "icon-esm-er.hist-1950.v20240618.atmos.gr025.2d_monthly_mean",
    "icon-esm-er.hist-1950.v20240618.ocean.gr025.2d_daily_mean",
    "icon-esm-er.hist-1950.r2i1p1f1.atmos.gr025.2d_daily_mean",
    "ifs-fesom2-sr.hist-1950.v20240304.atmos.gr025.2D_daily_avg",
    "HadGEM3-GC5E-HH.historical.v20250409.gr1.Amon",
    "ifs-amip-tco1279.hist.v20240901.atmos.gr025.2D_daily_avg",
    "cosmo-rea-day_atmos",
]


def _summary(dataset_id, variables, start="1950-01-01", end="2014-12-31"):
    return {"dataset_id": dataset_id, "variables": variables, "start": start, "end": end}


def test_parse_six_part_id_with_version():
    facets = cat.parse_dataset_id(IDS[0])
    assert facets["model"] == "icon-esm-er"
    assert facets["experiment"] == "hist-1950"
    assert facets["member"] == "r1i1p1f1"
    assert facets["version"] == "v20240618"
    assert (facets["realm"], facets["grid"], facets["collection"]) == (
        "atmos",
        "gr025",
        "2d_daily_mean",
    )


def test_parse_member_tag_and_five_part_id():
    assert cat.parse_dataset_id(IDS[4])["member"] == "r2i1p1f1"
    hadgem = cat.parse_dataset_id(IDS[6])
    assert (hadgem["grid"], hadgem["collection"], hadgem["realm"]) == ("gr1", "Amon", "atmos")


def test_parse_rejects_other_layouts():
    with pytest.raises(ValueError):
        cat.parse_dataset_id("cosmo-rea-day_atmos")


def test_filter_coupled_drops_ocean_amip_and_foreign_ids():
    kept = [f["dataset_id"] for f in cat.filter_coupled(IDS)]
    assert IDS[3] not in kept and IDS[7] not in kept and IDS[8] not in kept
    assert len(kept) == 6


def test_summarise_item():
    item = {
        "id": IDS[0],
        "properties": {
            "variables": ["pr", "psl"],
            "start_datetime": "1950-01-01T23:59:59Z",
            "end_datetime": "2014-12-31T23:59:59Z",
            "frequency": "daily",
        },
    }
    assert cat.summarise_item(item) == {
        "dataset_id": IDS[0],
        "variables": ["pr", "psl"],
        "start": "1950-01-01",
        "end": "2014-12-31",
        "frequency": "daily",
    }


def test_build_inventory_maps_native_names_and_flags_qualifying_runs():
    table = cat.build_inventory(
        [
            _summary(IDS[0], ["pr", "psl", "tas"]),
            _summary(IDS[1], ["tas"]),
            _summary(IDS[2], ["psl", "tas", "tasmax"]),
            _summary(IDS[5], ["tprate", "mmsl", "mean2t"]),
            _summary(IDS[6], ["pr", "tas"], "1850-01-16", "2014-12-16"),
        ]
    ).set_index("model")

    icon = table.loc["icon-esm-er"]
    assert icon["day tasmax"] == "1950-2014"  # daily max of tas
    assert bool(icon["qualifies"])

    ifs = table.loc["ifs-fesom2-sr"]
    assert ifs["day pr"] == "1950-2014" and ifs["day tasmax"] == ""
    assert not ifs["qualifies"]

    hadgem = table.loc["HadGEM3-GC5E-HH"]
    assert hadgem["mon tas"] == "1850-2014" and hadgem["mon psl"] == ""


def test_resolve_returns_dataset_and_native_name():
    assert cat.resolve(IDS, "icon-esm-er", "hist-1950", "day", "tasmax") == (IDS[1], "tas")
    assert cat.resolve(IDS, "ifs-fesom2-sr", "hist-1950", "day", "psl") == (IDS[5], "mmsl")
    assert cat.resolve(IDS, "icon-esm-er", "hist-1950", "day", "psl", member="r2i1p1f1")[0] == IDS[4]
    with pytest.raises(LookupError):
        cat.resolve(IDS, "icon-esm-er", "hist-1950", "day", "psl", grid="gr100")


def test_zarr_url():
    assert cat.zarr_url("a.b") == "https://eerie.cloud.dkrz.de/datasets/a.b/kerchunk"
    with pytest.raises(ValueError):
        cat.zarr_url("a.b", "netcdf")


def test_jasmin_path_to_url_and_summary():
    path = "/gws/nopw/j04/eerie/public/data/EERIE/x/psl_day.nc"
    assert jasmin.path_to_url(path) == "https://gws-access.jasmin.ac.uk/public/eerie/data/EERIE/x/psl_day.nc"
    assert jasmin.path_to_url("/badc/cmip6/a.nc") == "https://dap.ceda.ac.uk/badc/cmip6/a.nc"
    with pytest.raises(ValueError):
        jasmin.path_to_url("/home/users/a.nc")

    df = pd.DataFrame(
        {
            "source_id": ["M"] * 3,
            "experiment_id": ["ctl"] * 3,
            "table_id": ["day", "day", "Omon"],
            "variable_id": ["psl", "psl", "tos"],
            "grid_label": ["gn"] * 3,
            "start_time": ["1851-01-01 12:00:00", "1861-01-01 12:00:00", "1851-01-16 00:00:00"],
            "end_time": ["1860-12-30 12:00:00", "1870-12-30 12:00:00", "1870-12-16 00:00:00"],
            "path": [path, path, path],
        }
    )
    out = jasmin.summarise(df)
    assert len(out) == 1
    assert (out.loc[0, "start"], out.loc[0, "end"], out.loc[0, "files"]) == ("1851", "1870", 2)
