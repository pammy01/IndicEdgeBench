"""GGUF model files: local layout and Hugging Face download."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import ModelSpec

log = logging.getLogger(__name__)


def local_path(spec: ModelSpec, quant: str, models_dir: str | Path) -> Path:
    # models/<repo name>/<file>, the same layout hf_hub_download(local_dir=...) produces
    return Path(models_dir) / spec.repo.split("/")[-1] / spec.quants[quant]


def ensure_model(spec: ModelSpec, quant: str, models_dir: str | Path) -> Path:
    path = local_path(spec, quant, models_dir)
    if path.exists():
        return path
    from huggingface_hub import hf_hub_download

    log.info("Downloading %s/%s (%s) ...", spec.repo, spec.quants[quant], quant)
    hf_hub_download(repo_id=spec.repo, filename=spec.quants[quant], local_dir=path.parent)
    return path
