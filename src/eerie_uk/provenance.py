"""Provenance for saved result tables.

Every Parquet table in ``app_assets/`` is written together with a JSON file of
the same name that records how it was made: the code version (git commit), the
time, the input datasets with their server versions, and the analysis period.
The same record is also stored inside the Parquet file's metadata.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .download import DATA_ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def git_commit(root=PROJECT_ROOT) -> str:
    """The current commit hash, read from the .git folder (no git executable needed)."""
    git = Path(root) / ".git"
    try:
        head = (git / "HEAD").read_text().strip()
        if not head.startswith("ref:"):
            return head
        ref = head.split(" ", 1)[1]
        loose = git / ref
        if loose.exists():
            return loose.read_text().strip()
        for line in (git / "packed-refs").read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split(" ", 1)[0]
    except OSError:
        pass
    return "unknown"


def dataset_ids(source: str, frequency: str, variable: str, box: str, root=DATA_ROOT) -> list[str]:
    """Server dataset ids (which include their version tag) behind one saved field."""
    import xarray as xr

    folder = Path(root) / source / frequency
    files = sorted(folder.glob(f"{variable}_{box}_*.nc"))
    if not files:
        return []
    with xr.open_dataset(files[0]) as ds:
        found = ds[variable].attrs.get("dataset_id") or ds[variable].attrs.get("source", source)
    return [str(found)]


def record(description: str, inputs: dict | None = None, **details) -> dict:
    """A provenance record for one output."""
    import xarray

    return {
        "description": description,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "code": "eerie_uk (this repository)",
        "python": platform.python_version(),
        "xarray": xarray.__version__,
        "pandas": pd.__version__,
        "inputs": inputs or {},
        **details,
    }


def write_table(table: pd.DataFrame, path, description: str, inputs: dict | None = None, **details) -> dict:
    """Save ``table`` as Parquet with a provenance record inside and in a sidecar JSON file."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = record(description, inputs, rows=len(table), columns=list(map(str, table.columns)), **details)
    arrow = pa.Table.from_pandas(table, preserve_index=False)
    arrow = arrow.replace_schema_metadata({**(arrow.schema.metadata or {}), b"provenance": json.dumps(meta).encode()})
    pq.write_table(arrow, path)
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def read_provenance(path) -> dict:
    """The provenance record stored inside a Parquet file written by ``write_table``."""
    import pyarrow.parquet as pq

    metadata = pq.read_schema(path).metadata or {}
    return json.loads(metadata.get(b"provenance", b"{}"))
