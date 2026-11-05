# Rebuild every notebook from its generator, execute it top to bottom, and refresh the HTML copies.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File scripts\build_all.ps1
$ErrorActionPreference = "Stop"
$py = "python"
foreach ($n in "02", "03", "04", "05", "06", "07", "08", "09", "00") {
    $nb = (Get-ChildItem notebooks -Filter "$n`_*.ipynb").FullName
    $findings = "scripts\findings_$n.md"
    if (Test-Path $findings) { & $py "scripts\build_notebook_$n.py" $nb $findings } else { & $py "scripts\build_notebook_$n.py" $nb }
    jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3000 $nb
    if ($LASTEXITCODE -ne 0) { throw "notebook $n failed" }
}
jupyter nbconvert --to html --output-dir notebooks\html (Get-ChildItem notebooks -Filter "*.ipynb").FullName
