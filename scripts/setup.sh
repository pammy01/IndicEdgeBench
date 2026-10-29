#!/usr/bin/env bash
# IndicEdgeBench setup for macOS / Linux. Run from the repo root:  bash scripts/setup.sh
set -euo pipefail

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
  # Metal build (still runs CPU-only unless runtime.n_gpu_layers != 0)
  CMAKE_ARGS="-DGGML_METAL=on" .venv/bin/pip install llama-cpp-python==0.3.19
else
  .venv/bin/pip install llama-cpp-python==0.3.19 --only-binary=llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
  || .venv/bin/pip install llama-cpp-python==0.3.19   # build from source if no wheel
fi
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e . --no-deps
[[ -f .env ]] || { cp .env.example .env; echo "Created .env (add HF_TOKEN to enable MILU)"; }

.venv/bin/python -m pytest -q
.venv/bin/python -m indicedgebench info
echo "Done. Activate with: source .venv/bin/activate"
