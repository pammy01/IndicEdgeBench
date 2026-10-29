# IndicEdgeBench

**How much Indic-language quality do small LLMs lose when you quantize them to run on a laptop CPU, and how much speed, memory and energy do you gain?**

IndicEdgeBench is an open benchmark harness that answers both halves in a single run. It scores quantized GGUF models (F16 → Q8 → Q4 → Q2) on Indian-language multiple-choice tasks and, in the same process, measures CPU latency, peak memory, energy and tokenizer fertility. The output is a **quality-vs-efficiency Pareto frontier per language**.

> Status: **v0.1 (Evaluation 1)**. Harness complete, pilot results on Apple M3; the laptop pilot with MILU is next.
> Docs: [design](docs/design.md) · [literature survey](docs/literature_survey.md) · [original proposal](docs/proposal.md)

## What it measures

| Axis | Metric |
|---|---|
| Quality | MCQ accuracy (next-token letter log-likelihood), 95% bootstrap CI, paired Δ vs. FP16, **flip rate** |
| Speed | Time-to-first-token, prefill tokens/s, decode tokens/s, **words/s** (decode ÷ fertility) |
| Memory | Peak resident memory per config (fresh process each), model file size |
| Energy | Joules per MCQ item and per generated token (RAPL on Linux, labelled estimate elsewhere) |
| Tokenizer | Fertility (tokens/word) per language and model |

## Quick start: Windows 11 laptop (main experiment machine)

1. Install **Python 3.12** from python.org (tick *Add python.exe to PATH*) and **Git for Windows**.
2. Clone the repo and run the setup script:
   ```powershell
   git clone https://github.com/pammy01/IndicEdgeBench.git
   cd IndicEdgeBench
   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
   .\.venv\Scripts\Activate.ps1
   ```
   This installs a prebuilt CPU wheel of llama-cpp-python, so no Visual Studio is needed. It then runs the tests and prints your hardware fingerprint.
3. *(Optional, recommended)* Enable **MILU**:
   - Create a free Hugging Face account.
   - Click **Agree** on <https://huggingface.co/datasets/ai4bharat/MILU>; approval is instant.
   - Create a *Read* token (Settings → Access Tokens) and put it in `.env` as `HF_TOKEN=hf_...`.

   Without a token, the harness uses the bundled 30-item fallback set.
4. Run the pilot. This downloads the models (~11 GB), runs every config, and writes the report:
   ```powershell
   python -m indicedgebench run configs\pilot.yaml
   ```
   Results go to `results/pilot/`. Open `REPORT.md` there. If the run is interrupted, re-run the same command; finished configs are skipped.

Plug the laptop in, close other apps, and keep the power mode on *Best performance* while benchmarking.

## Quick start: macOS / Linux

```bash
bash scripts/setup.sh && source .venv/bin/activate
python -m indicedgebench run configs/smoke_mac.yaml     # ~2 GB of models, a few minutes
```

## Commands

```text
python -m indicedgebench info                  # hardware fingerprint + whether MILU is enabled
python -m indicedgebench download <config>     # fetch GGUF files only
python -m indicedgebench prepare  <config>     # freeze the sampled items only
python -m indicedgebench run      <config> [--models NAME ...] [--quants Q4_K_M ...] [--force]
python -m indicedgebench report   <run_dir>    # rebuild summary.csv, plots, REPORT.md
```

## Repository layout

```text
configs/         sweep definitions (smoke_mac.yaml, pilot.yaml)
data/fallback/   30 parallel hand-authored MCQs (en, hi, ta)
docs/            proposal, literature survey, design, Eval-1 slides
indicedgebench/  the harness (see docs/design.md for the module map)
results/<run>/   config snapshot, frozen items, per-item raw results, efficiency JSON, plots, REPORT.md
scripts/         setup.ps1 (Windows), setup.sh (macOS/Linux)
tests/           unit tests (no model or network needed): python -m pytest
```

## Data and licences

- **MILU** © AI4Bharat, CC-BY-4.0. It is downloaded at run time and not redistributed here.
- **Models** are fetched from the `bartowski/*-GGUF` repositories and keep their original licences: Qwen2.5 under Apache-2.0, Llama 3.2 under the Llama 3.2 Community License, Gemma under the Gemma Terms.
- **Fallback set** and code: MIT.
