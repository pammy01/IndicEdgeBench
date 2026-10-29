# IndicEdgeBench setup for Windows 10/11 (CPU). Run from the repo root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Requires Python 3.10-3.13 from python.org (tick "Add python.exe to PATH").
$ErrorActionPreference = "Stop"

$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $python = "py" } else { $python = "python" }

Write-Host "Creating virtual environment in .venv ..."
& $python -m venv .venv
$venvPy = ".\.venv\Scripts\python.exe"
& $venvPy -m pip install --upgrade pip

# Prebuilt CPU wheel: no Visual Studio / CMake needed.
Write-Host "Installing llama-cpp-python 0.3.19 (prebuilt CPU wheel) ..."
& $venvPy -m pip install llama-cpp-python==0.3.19 --only-binary=llama-cpp-python `
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

& $venvPy -m pip install -r requirements.txt
& $venvPy -m pip install -e . --no-deps

if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env (add HF_TOKEN to enable MILU)" }

& $venvPy -m pytest -q
& $venvPy -m indicedgebench info
Write-Host "`nDone. Activate with:  .\.venv\Scripts\Activate.ps1"
Write-Host "Then run:            python -m indicedgebench run configs\pilot.yaml"
