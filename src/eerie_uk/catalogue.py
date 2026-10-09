"""Discover and lazily open public EERIE output on the DKRZ km-scale cloud.

The server (https://eerie.cloud.dkrz.de) lists dataset ids at ``/datasets``,
describes each one with a STAC item at ``/datasets/<id>/stac`` and serves the
data as Zarr at ``/datasets/<id>/kerchunk`` (raw chunks) or ``/zarr``
(rechunked server-side). Functions that touch the network say so; everything
else is pure and unit-tested offline.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

DKRZ_CLOUD = "https://eerie.cloud.dkrz.de"
DKRZ_DATASETS_URL = f"{DKRZ_CLOUD}/datasets"
DKRZ_INTAKE_URL = f"{DKRZ_CLOUD}/intake.yaml"
EERIE_INTAKE_URL = (
    "https://raw.githubusercontent.com/eerie-project/intake_catalogues/main/eerie.yaml"
)

# Coupled EERIE models on the DKRZ cloud, as the lower-cased id prefix.
COUPLED_MODELS = (
    "icon-esm-er",
    "ifs-fesom2-sr",
    "ifs-nemo-er",
    "ifs-nemo",
    "hadgem3-gc5e-ll",
    "hadgem3-gc5e-mm",
    "hadgem3-gc5e-hh",
)

# The six fields the project needs: (frequency, CMIP-style variable name).
TARGETS = (
    ("day", "pr"),
    ("day", "psl"),
    ("day", "tas"),
    ("day", "tasmax"),
    ("mon", "psl"),
    ("mon", "tas"),
)

# Where each target lives per model: (collection, native variable name).
# Models that publish CMOR tables use the "cmor" entry.
_CMOR = {
    ("day", "pr"): ("day", "pr"),
    ("day", "psl"): ("day", "psl"),
    ("day", "tas"): ("day", "tas"),
    ("day", "tasmax"): ("day", "tasmax"),
    ("mon", "psl"): ("Amon", "psl"),
    ("mon", "tas"): ("Amon", "tas"),
}
VARIABLE_MAP = {
    "icon-esm-er": {
        ("day", "pr"): ("2d_daily_mean", "pr"),
        ("day", "psl"): ("2d_daily_mean", "psl"),
        ("day", "tas"): ("2d_daily_mean", "tas"),
        ("day", "tasmax"): ("2d_daily_max", "tas"),
        ("mon", "psl"): ("2d_monthly_mean", "psl"),
        ("mon", "tas"): ("2d_monthly_mean", "tas"),
    },
    "ifs-fesom2-sr": {
        ("day", "pr"): ("2D_daily_avg", "tprate"),
        ("day", "psl"): ("2D_daily_avg", "mmsl"),
        ("day", "tas"): ("2D_daily_avg", "mean2t"),
        ("day", "tasmax"): ("2D_daily_max", "mx2t24"),
        ("mon", "psl"): ("2D_monthly_avg", "mmsl"),
        ("mon", "tas"): ("2D_monthly_avg", "mean2t"),
    },
    "cmor": _CMOR,
}

_VERSION = re.compile(r"^v\d{8}$")
_MEMBER = re.compile(r"^r\d+i\d+p\d+f\d+$")


def target_label(frequency: str, variable: str) -> str:
    return f"{frequency} {variable}"


def variable_map_for(model: str) -> dict:
    return VARIABLE_MAP.get(model.lower(), VARIABLE_MAP["cmor"])


def parse_dataset_id(dataset_id: str) -> dict:
    """Split a DKRZ dataset id into its facets.

    Two layouts exist:
    ``model.experiment.version|member.realm.grid.collection`` and, for the
    HadGEM3 entries, ``model.experiment.version.grid.collection``. A version
    tag in the third slot means the first member, ``r1i1p1f1``.
    """
    parts = dataset_id.split(".")
    if len(parts) == 6:
        model, experiment, tag, realm, grid, collection = parts
    elif len(parts) == 5:
        model, experiment, tag, grid, collection = parts
        realm = "atmos"
    else:
        raise ValueError(f"not an EERIE-style dataset id: {dataset_id!r}")
    if _VERSION.match(tag):
        member, version = "r1i1p1f1", tag
    elif _MEMBER.match(tag):
        member, version = tag, ""
    else:
        raise ValueError(f"cannot read version/member from {dataset_id!r}")
    return {
        "dataset_id": dataset_id,
        "model": model,
        "experiment": experiment,
        "member": member,
        "version": version,
        "realm": realm,
        "grid": grid,
        "collection": collection,
    }


def filter_coupled(dataset_ids, models=COUPLED_MODELS, realm="atmos") -> list[dict]:
    """Parse ids and keep the atmosphere collections of the coupled models."""
    wanted = {m.lower() for m in models}
    out = []
    for dataset_id in dataset_ids:
        try:
            facets = parse_dataset_id(dataset_id)
        except ValueError:
            continue
        if facets["model"].lower() in wanted and facets["realm"] == realm:
            out.append(facets)
    return out


def missing_models(dataset_ids, models=COUPLED_MODELS) -> list[str]:
    """Coupled models we looked for that have no atmosphere dataset at all."""
    present = {f["model"].lower() for f in filter_coupled(dataset_ids, models)}
    return [m for m in models if m.lower() not in present]


def summarise_item(item: dict) -> dict:
    """Reduce a STAC item to what the inventory needs."""
    props = item.get("properties", {})
    return {
        "dataset_id": item.get("id"),
        "variables": list(props.get("variables") or []),
        "start": (props.get("start_datetime") or "")[:10],
        "end": (props.get("end_datetime") or "")[:10],
        "frequency": props.get("frequency"),
    }


def build_inventory(summaries, targets=TARGETS) -> pd.DataFrame:
    """One row per model/experiment/member/grid, one column per target.

    ``summaries`` is an iterable of ``summarise_item`` dicts. A cell holds the
    period as ``"1950-2014"`` when the target is served, else ``""``.
    ``qualifies`` is True when all targets are present.
    """
    rows = {}
    for summary in summaries:
        facets = parse_dataset_id(summary["dataset_id"])
        key = (facets["model"], facets["experiment"], facets["member"], facets["grid"])
        row = rows.setdefault(key, {target_label(*t): "" for t in targets})
        mapping = variable_map_for(facets["model"])
        for target in targets:
            collection, native = mapping[target]
            if facets["collection"] == collection and native in summary["variables"]:
                row[target_label(*target)] = f"{summary['start'][:4]}-{summary['end'][:4]}"
    index = pd.MultiIndex.from_tuples(rows, names=["model", "experiment", "member", "grid"])
    table = pd.DataFrame(list(rows.values()), index=index).sort_index()
    table["qualifies"] = (table != "").all(axis=1)
    return table.reset_index()


def resolve(dataset_ids, model, experiment, frequency, variable, member="r1i1p1f1", grid="gr025"):
    """Return ``(dataset_id, native_variable_name)`` for one target field."""
    collection, native = variable_map_for(model)[(frequency, variable)]
    for facets in filter_coupled(dataset_ids, models=(model,)):
        if (
            facets["experiment"] == experiment
            and facets["member"] == member
            and facets["grid"] == grid
            and facets["collection"] == collection
        ):
            return facets["dataset_id"], native
    raise LookupError(
        f"no dataset for {model} {experiment} {member} {grid} {frequency} {variable}"
    )


# --- network -----------------------------------------------------------------


def check_url(url: str, timeout: float = 60.0) -> dict:
    """GET ``url`` and report the outcome without raising."""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.close()
        return {
            "url": url,
            "ok": response.ok,
            "status": response.status_code,
            "error": "" if response.ok else f"{response.status_code} {response.reason}",
        }
    except requests.RequestException as exc:
        return {"url": url, "ok": False, "status": None, "error": f"{type(exc).__name__}: {exc}"}


def list_datasets(timeout: float = 120.0) -> list[str]:
    """All dataset ids served by the DKRZ cloud (network)."""
    response = requests.get(DKRZ_DATASETS_URL, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_stac_item(dataset_id: str, timeout: float = 180.0) -> dict:
    """STAC item for one dataset (network)."""
    response = requests.get(f"{DKRZ_DATASETS_URL}/{dataset_id}/stac", timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_summaries(dataset_ids, max_workers: int = 8) -> list[dict]:
    """``summarise_item`` for many datasets, fetched concurrently (network)."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return [summarise_item(item) for item in pool.map(fetch_stac_item, dataset_ids)]


def open_intake(url: str = EERIE_INTAKE_URL):
    """Open an intake YAML catalogue (network)."""
    import intake

    return intake.open_catalog(url)


def check_open(dataset_ids) -> pd.DataFrame:
    """Open each dataset lazily and record success or the exact error (network)."""
    rows = []
    for dataset_id in dataset_ids:
        try:
            ds = open_dataset(dataset_id)
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "ok": True,
                    "shape": "x".join(f"{k}={v}" for k, v in ds.sizes.items() if k in ("time", "lat", "lon")),
                    "error": "",
                }
            )
        except Exception as exc:  # report, do not hide, any access failure
            rows.append(
                {"dataset_id": dataset_id, "ok": False, "shape": "", "error": f"{type(exc).__name__}: {exc}"}
            )
    return pd.DataFrame(rows)


def check_read(dataset_id: str, variable: str, flavour: str = "kerchunk") -> dict:
    """Open a dataset and load one time step of one variable (network).

    Opening only reads metadata; this also proves the chunks can be decoded.
    """
    row = {"dataset_id": dataset_id, "variable": variable, "flavour": flavour}
    try:
        field = open_dataset(dataset_id, flavour)[variable].isel(time=0).load()
        return {**row, "ok": True, "error": "", "mean": float(field.mean())}
    except Exception as exc:  # report, do not hide, any access failure
        return {**row, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:300], "mean": None}


def zarr_url(dataset_id: str, flavour: str = "kerchunk") -> str:
    """Zarr endpoint: ``kerchunk`` = raw chunks, ``zarr`` = rechunked server-side."""
    if flavour not in ("kerchunk", "zarr"):
        raise ValueError("flavour must be 'kerchunk' or 'zarr'")
    return f"{DKRZ_DATASETS_URL}/{dataset_id}/{flavour}"


def open_dataset(dataset_id: str, flavour: str = "kerchunk", **kwargs):
    """Open one dataset lazily with xarray + dask (network, metadata only).

    ``kerchunk`` is Zarr v2 over the original chunks; ``zarr`` is Zarr v3.
    """
    import xarray as xr

    from . import grib

    grib.register()  # IFS chunks are raw GRIB
    options = {
        "engine": "zarr",
        "chunks": {},
        "consolidated": True,
        "zarr_format": 2 if flavour == "kerchunk" else 3,
    }
    options.update(kwargs)
    return xr.open_dataset(zarr_url(dataset_id, flavour), **options)


def open_variable(
    model,
    experiment,
    frequency,
    variable,
    member="r1i1p1f1",
    grid="gr025",
    dataset_ids=None,
    **kwargs,
):
    """Lazy DataArray for one target field, renamed to its CMIP-style name."""
    ids = list_datasets() if dataset_ids is None else dataset_ids
    dataset_id, native = resolve(ids, model, experiment, frequency, variable, member, grid)
    data = open_dataset(dataset_id, **kwargs)[native].rename(variable)
    data.attrs["dataset_id"] = dataset_id
    data.attrs["native_name"] = native
    return data
