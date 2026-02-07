$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python -m pip install --upgrade "pip<23.2"
& .\.venv\Scripts\python -m pip install -r requirements_test.txt
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
& .\.venv\Scripts\python -m pytest -q -p pytest_asyncio -p pytest_homeassistant_custom_component
