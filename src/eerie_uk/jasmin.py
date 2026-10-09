"""Public metadata for the Met Office HadGEM3-GC5 EERIE runs held at JASMIN/CEDA.

The eerie-project GitHub repository publishes two intake-esm catalogues as
CSV: ``jasmin`` (the EERIE group workspace) and ``badc`` (the CEDA archive).
The CSVs are public; whether the files they point at can be downloaded
anonymously is a separate question, answered by ``probe_access``.
"""

from __future__ import annotations

import pandas as pd

from .catalogue import check_url

_RAW = "https://raw.githubusercontent.com/eerie-project/intake_catalogues/main/jasmin"
CATALOGUE_CSV = {
    "jasmin": f"{_RAW}/jasmin-catalogue.csv",
    "badc": f"{_RAW}/badc-catalogue.csv",
}

# Filesystem prefix in the catalogue -> the HTTPS address that serves it.
HTTP_ROOTS = {
    "/gws/nopw/j04/eerie/public/": "https://gws-access.jasmin.ac.uk/public/eerie/",
    "/badc/": "https://dap.ceda.ac.uk/badc/",
}

TARGET_VARIABLES = ("pr", "psl", "tas", "tasmax")
TARGET_TABLES = ("day", "Amon")


def load_catalogue(name: str = "jasmin") -> pd.DataFrame:
    """Read one of the public intake-esm CSVs (network)."""
    return pd.read_csv(CATALOGUE_CSV[name], low_memory=False)


def path_to_url(path: str) -> str:
    """Translate a JASMIN filesystem path into its HTTPS address."""
    for prefix, root in HTTP_ROOTS.items():
        if path.startswith(prefix):
            return root + path[len(prefix):]
    raise ValueError(f"no public HTTPS root known for {path!r}")


def summarise(df: pd.DataFrame, variables=TARGET_VARIABLES, tables=TARGET_TABLES) -> pd.DataFrame:
    """Period and file count per model/experiment/table/variable/grid."""
    keep = df[df["variable_id"].isin(variables) & df["table_id"].isin(tables)]
    groups = ["source_id", "experiment_id", "table_id", "variable_id", "grid_label"]
    out = keep.groupby(groups).agg(
        start=("start_time", "min"),
        end=("end_time", "max"),
        files=("path", "count"),
        example_path=("path", "first"),
    )
    out["start"] = out["start"].str[:4]
    out["end"] = out["end"].str[:4]
    return out.reset_index()


def probe_access(summary: pd.DataFrame) -> pd.DataFrame:
    """Try one file per distinct HTTPS root and record the outcome (network)."""
    rows = []
    seen = set()
    for path in summary["example_path"]:
        url = path_to_url(path)
        root = next(r for r in HTTP_ROOTS.values() if url.startswith(r))
        if root in seen:
            continue
        seen.add(root)
        rows.append({"root": root, **check_url(url)})
    return pd.DataFrame(rows)
