import json

import pandas as pd

from eerie_uk import provenance


def test_write_table_stores_provenance_inside_and_beside(tmp_path):
    table = pd.DataFrame({"year": [1990, 1991], "value": [1.0, 2.0]})
    path = tmp_path / "result.parquet"
    meta = provenance.write_table(table, path, "test table", inputs={"era5": ["era5-dkrz.surface_analysis_monthly"]},
                                  period="1990-1991")
    assert pd.read_parquet(path).equals(table)
    inside = provenance.read_provenance(path)
    beside = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert inside == beside == meta
    assert inside["description"] == "test table" and inside["period"] == "1990-1991"
    assert inside["rows"] == 2 and inside["inputs"]["era5"] == ["era5-dkrz.surface_analysis_monthly"]
    assert inside["git_commit"]


def test_git_commit_reads_loose_and_packed_refs(tmp_path):
    git = tmp_path / ".git"
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n")
    (git / "refs" / "heads" / "main").write_text("abc123\n")
    assert provenance.git_commit(tmp_path) == "abc123"
    (git / "refs" / "heads" / "main").unlink()
    (git / "packed-refs").write_text("# pack-refs\ndef456 refs/heads/main\n")
    assert provenance.git_commit(tmp_path) == "def456"
    assert provenance.git_commit(tmp_path / "missing") == "unknown"
