$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python -m pip install --upgrade "pip<23.2"
& .\.venv\Scripts\python -m pip install -r requirements_test.txt
& .\.venv\Scripts\python -m pytest -q
