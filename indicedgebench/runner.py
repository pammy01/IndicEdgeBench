"""Sweep orchestration: freeze the item set once, then run every (model, quant) in its own process."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .config import Config
from .data import load_fewshot, load_items, resolve_source
from .models import ensure_model, local_path
from . import sysinfo

log = logging.getLogger(__name__)


def prepare(cfg: Config) -> Path:
    """Snapshot config, sampled items and system info into the run directory.

    Every worker reads items from here, so all configs are scored on identical questions
    and workers never need network access or an HF token.
    """
    run_dir = cfg.output_dir
    (run_dir / "items").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cfg.path, run_dir / "config.yaml")

    data = cfg["data"]
    source = resolve_source(data["source"])
    if source == "milu" and data["source"] == "auto":
        log.info("HF token found: using MILU")
    elif source == "fallback":
        log.warning("Using bundled fallback set (no HF token or data.source=fallback)")

    for lang in data["languages"]:
        try:
            items = load_items(lang, source, data["split"], data["n_per_language"], cfg["seed"])
        except Exception as e:
            if data["source"] != "auto":
                raise
            log.warning("MILU load failed for %s (%s); falling back to bundled set", lang, e)
            source = "fallback"
            items = load_items(lang, source, data["split"], data["n_per_language"], cfg["seed"])
        fewshot = load_fewshot(lang, source, data["n_shot"], cfg["seed"], {it.id for it in items})
        for name, rows in ((f"{lang}.jsonl", items), (f"{lang}.fewshot.jsonl", fewshot)):
            with open(run_dir / "items" / name, "w", encoding="utf-8") as f:
                for it in rows:
                    f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")
        log.info("%s: %d items (%s)", lang, len(items), source)

    (run_dir / "run_info.json").write_text(json.dumps(
        {"data_source": source, "system": sysinfo.collect()}, indent=2), encoding="utf-8")
    return run_dir


def download(cfg: Config) -> None:
    for spec in cfg.models:
        for quant in spec.quants:
            print("ok  " if local_path(spec, quant, cfg["models_dir"]).exists() else "get ",
                  spec.name, quant, flush=True)
            ensure_model(spec, quant, cfg["models_dir"])


def run(cfg: Config, force: bool = False, only_models=None, only_quants=None) -> Path:
    run_dir = prepare(cfg)
    (run_dir / "logs").mkdir(exist_ok=True)
    todo = [(s, q) for s in cfg.models for q in s.quants
            if (not only_models or s.name in only_models) and (not only_quants or q in only_quants)]
    for i, (spec, quant) in enumerate(todo):
        tag = f"{spec.name}__{quant}"
        if (run_dir / "efficiency" / f"{tag}.json").exists() and not force:
            log.info("[%d/%d] %s already done, skipping (use --force to redo)", i + 1, len(todo), tag)
            continue
        path = ensure_model(spec, quant, cfg["models_dir"])
        log.info("[%d/%d] %s", i + 1, len(todo), tag)
        t0 = time.perf_counter()
        with open(run_dir / "logs" / f"{tag}.log", "w", encoding="utf-8") as logf:
            proc = subprocess.run(
                [sys.executable, "-m", "indicedgebench.worker", str(run_dir), spec.name, quant, str(path)],
                stderr=logf)
        if proc.returncode != 0:
            log.error("%s failed (exit %d); see %s", tag, proc.returncode, run_dir / "logs" / f"{tag}.log")
            continue
        log.info("%s finished in %.0fs", tag, time.perf_counter() - t0)
        if i < len(todo) - 1 and cfg["runtime"]["cooldown_s"]:
            time.sleep(cfg["runtime"]["cooldown_s"])  # let the CPU cool so configs don't inherit throttling
    return run_dir
