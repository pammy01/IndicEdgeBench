"""Evaluate ONE (model, quant) config in a fresh process.

Running each config in its own process means peak memory is attributable to that config and
no weights or KV cache leak between configs. Invoked by runner.py:

    python -m indicedgebench.worker <run_dir> <model_name> <quant> <gguf_path>
"""

from __future__ import annotations

import ctypes
import json
import sys
import time
from pathlib import Path

import numpy as np
import psutil

from .config import load_config
from .data import LETTERS, MCQItem
from .meters import EnergyMeter, PeakMemorySampler
from .prompts import generation_prompt, mcq_prompt
from . import sysinfo


def read_items(path: Path) -> list[MCQItem]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [MCQItem(**json.loads(line)) for line in f if line.strip()]


class Engine:
    """Thin wrapper over llama-cpp-python exposing exactly what the benchmark needs."""

    def __init__(self, model_path: Path, rt: dict, seed: int):
        from llama_cpp import Llama

        self.n_threads = rt["n_threads"] or psutil.cpu_count(logical=False)
        self.n_ctx = rt["n_ctx"]
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=rt["n_ctx"],
            n_batch=rt["n_batch"],
            n_threads=self.n_threads,
            n_threads_batch=self.n_threads,
            n_gpu_layers=rt["n_gpu_layers"],
            seed=seed,
            verbose=False,
        )
        self.n_vocab = self.llm.n_vocab()
        self.eos = self.llm.token_eos()

    def tokenize(self, text: str, bos: bool = True) -> list[int]:
        return self.llm.tokenize(text.encode("utf-8"), add_bos=bos, special=False)

    def prefill(self, tokens: list[int]) -> None:
        self.llm.reset()
        self.llm.eval(tokens)

    def step(self, token: int) -> None:
        self.llm.eval([token])

    def last_logits(self) -> np.ndarray:
        # Read the newest logits straight from llama.cpp; llama-cpp-python only mirrors
        # them into `scores` when logits_all=True, which would cost n_ctx x n_vocab floats.
        import llama_cpp

        ptr = llama_cpp.llama_get_logits_ith(self.llm._ctx.ctx, -1)
        return np.ctypeslib.as_array(ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float)),
                                     shape=(self.n_vocab,)).copy()

    def answer_token_ids(self) -> list[list[int]]:
        """Token ids that spell each answer letter, with and without a leading space."""
        ids = []
        for letter in LETTERS:
            cands = {t[0] for v in (f" {letter}", letter) if len(t := self.tokenize(v, bos=False)) == 1}
            if not cands:
                raise RuntimeError(f"Tokenizer has no single token for answer letter {letter!r}")
            ids.append(sorted(cands))
        return ids


def score_mcq(eng: Engine, item: MCQItem, fewshot, letter_ids) -> dict:
    tokens = eng.tokenize(mcq_prompt(item, fewshot))
    rec = {"id": item.id, "lang": item.lang, "domain": item.domain, "subject": item.subject,
           "answer": item.answer, "n_prompt_tokens": len(tokens), "truncated": False}
    if len(tokens) >= eng.n_ctx:
        rec.update(truncated=True, pred=-1, correct=0, probs=None, prefill_s=None)
        return rec
    t0 = time.perf_counter()
    eng.prefill(tokens)
    prefill_s = time.perf_counter() - t0
    logits = eng.last_logits()
    scores = np.array([logits[ids].max() for ids in letter_ids], dtype=np.float64)
    probs = np.exp(scores - scores.max())
    probs /= probs.sum()
    pred = int(scores.argmax())
    rec.update(pred=pred, correct=int(pred == item.answer), probs=[round(float(p), 4) for p in probs],
               prefill_s=prefill_s)
    return rec


def time_generation(eng: Engine, items: list[MCQItem], lat: dict) -> dict:
    """Greedy decode a fixed number of tokens (EOS ignored, as in llama-bench) and time it."""
    n_new = lat["max_new_tokens"]
    ttft, prefill_tps, decode_tps, samples = [], [], [], []
    for item in items:
        tokens = eng.tokenize(generation_prompt(item))
        if len(tokens) + n_new >= eng.n_ctx:
            continue
        for r in range(lat["warmup"] + lat["repeats"]):
            t0 = time.perf_counter()
            eng.prefill(tokens)
            tok = int(eng.last_logits().argmax())
            t1 = time.perf_counter()
            out = [tok]
            for _ in range(n_new - 1):
                eng.step(tok)
                tok = int(eng.last_logits().argmax())
                out.append(tok)
            t2 = time.perf_counter()
            if r < lat["warmup"]:
                continue
            ttft.append(t1 - t0)
            prefill_tps.append(len(tokens) / (t1 - t0))
            decode_tps.append((n_new - 1) / (t2 - t1))
        stop = out.index(eng.eos) if eng.eos in out else len(out)
        samples.append({"id": item.id, "n_prompt_tokens": len(tokens),
                        "text": eng.llm.detokenize(out[:stop]).decode("utf-8", errors="replace")})

    def stats(xs):
        return {"median": float(np.median(xs)), "std": float(np.std(xs)), "n": len(xs)} if xs else None

    return {"ttft_s": stats(ttft), "prefill_tps": stats(prefill_tps),
            "decode_tps": stats(decode_tps), "samples": samples}


def fertility(eng: Engine, items: list[MCQItem]) -> dict:
    """Tokenizer cost of the language: tokens per whitespace word and characters per token."""
    n_tok = n_words = n_chars = 0
    for it in items:
        text = " ".join([it.question, *it.options])
        n_tok += len(eng.tokenize(text, bos=False))
        n_words += len(text.split())
        n_chars += len(text)
    return {"tokens_per_word": n_tok / max(n_words, 1), "chars_per_token": n_chars / max(n_tok, 1),
            "n_tokens": n_tok, "n_words": n_words}


def main(run_dir: str, model_name: str, quant: str, model_path: str) -> None:
    run_dir = Path(run_dir)
    cfg = load_config(run_dir / "config.yaml")
    tag = f"{model_name}__{quant}"
    raw_path = run_dir / "raw" / f"{tag}.jsonl"
    eff_path = run_dir / "efficiency" / f"{tag}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    eff_path.parent.mkdir(parents=True, exist_ok=True)

    with PeakMemorySampler() as mem:
        t0 = time.perf_counter()
        eng = Engine(Path(model_path), cfg["runtime"], cfg["seed"])
        load_s = time.perf_counter() - t0
        letter_ids = eng.answer_token_ids()
        eng.prefill(eng.tokenize("warm up"))  # page in mmapped weights before timing anything

        per_lang = {}
        with open(raw_path, "w", encoding="utf-8") as raw:
            for lang in cfg["data"]["languages"]:
                items = read_items(run_dir / "items" / f"{lang}.jsonl")
                fewshot = read_items(run_dir / "items" / f"{lang}.fewshot.jsonl")
                with EnergyMeter(cfg["energy"]["tdp_watts"], eng.n_threads) as e_mcq:
                    for i, item in enumerate(items):
                        rec = score_mcq(eng, item, fewshot, letter_ids)
                        raw.write(json.dumps({"model": model_name, "quant": quant, **rec},
                                             ensure_ascii=False) + "\n")
                        if sys.stdout.isatty():
                            print(f"\r[{tag}] {lang} {i + 1}/{len(items)}", end="", flush=True)
                print(f"\r[{tag}] {lang} done: {len(items)} items", flush=True)
                with EnergyMeter(cfg["energy"]["tdp_watts"], eng.n_threads) as e_gen:
                    gen = time_generation(eng, items[: cfg["latency"]["n_items"]], cfg["latency"])
                n_gen_tokens = (gen["decode_tps"] or {}).get("n", 0) * cfg["latency"]["max_new_tokens"]
                per_lang[lang] = {
                    "n_items": len(items),
                    "fertility": fertility(eng, items),
                    "mcq_wall_s": e_mcq.wall_s,
                    "mcq_energy_j": e_mcq.joules,
                    "gen_energy_j_per_token": e_gen.joules / n_gen_tokens if n_gen_tokens else None,
                    **gen,
                }

    summary = {
        "model": model_name, "quant": quant, "model_path": str(model_path),
        "model_file_mb": Path(model_path).stat().st_size / 2**20,
        "load_s": load_s, "peak_rss_mb": mem.peak_mb, "n_threads": eng.n_threads,
        "n_gpu_layers": cfg["runtime"]["n_gpu_layers"], "energy_method": e_mcq.method,
        "tdp_watts": e_mcq.tdp, "system": sysinfo.collect(), "languages": per_lang,
    }
    eff_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
