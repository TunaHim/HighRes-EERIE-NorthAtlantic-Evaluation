import subprocess
import sys
from pathlib import Path

import nbformat
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
GENERATORS = sorted(SCRIPTS.glob("build_notebook_*.py"))


@pytest.mark.parametrize("script", GENERATORS, ids=lambda p: p.stem)
def test_generator_writes_a_valid_notebook(script, tmp_path):
    out = tmp_path / "out.ipynb"
    subprocess.run([sys.executable, str(script), str(out)], check=True, capture_output=True)
    nb = nbformat.read(out, as_version=4)
    nbformat.validate(nb)
    code = [c for c in nb.cells if c.cell_type == "code"]
    assert code, "a notebook without code cells"
    # every code cell has an explanatory markdown cell directly above it
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            assert i > 0 and nb.cells[i - 1].cell_type == "markdown"
