"""Experiment configuration: one YAML file fully describes a sweep."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import LANGUAGES

DEFAULTS = {
    "run_name": "run",
    "seed": 1234,
    "output_dir": None,  # defaults to results/<run_name>
    "models_dir": "models",
    "runtime": {
        "n_threads": None,  # None -> number of physical cores
        "n_ctx": 2048,
        "n_batch": 512,
        "n_gpu_layers": 0,  # 0 = CPU only (headline numbers); -1 = offload all (Metal/CUDA)
        "cooldown_s": 10,  # pause between model configs to limit thermal carry-over
    },
    "data": {
        "source": "auto",  # auto | milu | fallback
        "split": "test",
        "n_per_language": 100,
        "languages": ["hi", "ta", "en"],
        "n_shot": 0,
    },
    "latency": {
        "n_items": 5,  # prompts per language used for generation timing
        "max_new_tokens": 64,
        "repeats": 3,
        "warmup": 1,
    },
    "energy": {
        "tdp_watts": None,  # None -> per-platform default in energy.py
    },
    "bootstrap": {"n_resamples": 1000},
    "models": [],
}


@dataclass
class ModelSpec:
    name: str
    repo: str
    quants: dict[str, str]  # quant label -> GGUF filename
    baseline: str = "F16"  # quant label used as the reference for deltas/flip rates


@dataclass
class Config:
    raw: dict
    path: Path | None = None
    models: list[ModelSpec] = field(default_factory=list)

    def __getitem__(self, key):
        return self.raw[key]

    @property
    def output_dir(self) -> Path:
        return Path(self.raw["output_dir"] or f"results/{self.raw['run_name']}")


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path) -> Config:
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        raw = _merge(DEFAULTS, yaml.safe_load(f) or {})

    unknown = [l for l in raw["data"]["languages"] if l not in LANGUAGES]
    if unknown:
        raise ValueError(f"Unknown language codes {unknown}; choose from {sorted(LANGUAGES)}")
    if raw["data"]["source"] not in ("auto", "milu", "fallback"):
        raise ValueError("data.source must be one of auto | milu | fallback")

    models = [ModelSpec(**m) for m in raw["models"]]
    for m in models:
        if m.baseline not in m.quants:
            raise ValueError(f"Model {m.name}: baseline {m.baseline!r} not in quants {list(m.quants)}")
    return Config(raw=raw, path=path, models=models)
