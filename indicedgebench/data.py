"""Task data: MILU (ai4bharat/MILU, gated, CC-BY-4.0) with a bundled hand-authored fallback.

Every item is normalised to `MCQItem` so the rest of the harness is source-agnostic.
"""

from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from . import LANGUAGES

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
FALLBACK_DIR = ROOT / "data" / "fallback"
CACHE_DIR = ROOT / "data" / "cache"
MILU_REPO = "ai4bharat/MILU"
LETTERS = "ABCD"


@dataclass
class MCQItem:
    id: str
    lang: str
    question: str
    options: list[str]
    answer: int  # 0-based index into options
    domain: str = ""
    subject: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def load_env_file(path: Path = ROOT / ".env") -> None:
    """Minimal .env reader so users need no extra dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            if val.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = val.strip().strip('"').strip("'")


def get_hf_token() -> str | None:
    load_env_file()
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token
    try:  # token saved by `hf auth login` / `huggingface-cli login`
        from huggingface_hub import get_token

        return get_token()
    except Exception:
        return None


# ---------------------------------------------------------------- MILU

def _parse_target(target, n_options: int) -> int:
    """MILU stores the answer as e.g. 'option2'; accept letters and ints too."""
    if isinstance(target, str):
        t = target.strip()
        if t.lower().startswith("option"):
            return int(t[len("option"):]) - 1
        if len(t) == 1 and t.upper() in LETTERS:
            return LETTERS.index(t.upper())
        target = int(t)
    target = int(target)
    if 1 <= target <= n_options:  # MILU numbering is 1-based
        return target - 1
    raise ValueError(f"Unrecognised MILU target {target!r}")


def _milu_row_to_item(row: dict, lang: str, idx: int, split: str) -> MCQItem:
    options = [str(row[f"option{i}"]) for i in range(1, 5)]
    return MCQItem(
        id=f"milu-{lang}-{split}-{idx:05d}",
        lang=lang,
        question=str(row["question"]),
        options=options,
        answer=_parse_target(row["target"], len(options)),
        domain=str(row.get("domain", "") or ""),
        subject=str(row.get("subject", "") or ""),
        source="milu",
    )


def load_milu(lang: str, split: str, token: str | None) -> list[MCQItem]:
    from datasets import load_dataset

    ds = load_dataset(MILU_REPO, name=LANGUAGES[lang], split=split, token=token,
                      cache_dir=str(CACHE_DIR))
    missing = {"question", "option1", "option2", "option3", "option4", "target"} - set(ds.column_names)
    if missing:
        raise RuntimeError(f"MILU schema changed; missing columns {missing}. Found {ds.column_names}")
    return [_milu_row_to_item(row, lang, i, split) for i, row in enumerate(ds)]


# ---------------------------------------------------------------- fallback

def load_fallback(lang: str) -> list[MCQItem]:
    path = FALLBACK_DIR / f"{lang}.jsonl"
    if not path.exists():
        raise FileNotFoundError(
            f"No fallback data for '{lang}' ({path}). Fallback covers: "
            f"{sorted(p.stem for p in FALLBACK_DIR.glob('*.jsonl'))}. Set HF_TOKEN to use MILU."
        )
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                items.append(MCQItem(source="fallback", **d))
    return items


# ---------------------------------------------------------------- public API

def resolve_source(requested: str) -> str:
    if requested != "auto":
        return requested
    return "milu" if get_hf_token() else "fallback"


def load_items(lang: str, source: str, split: str, n: int | None, seed: int) -> list[MCQItem]:
    """Load and deterministically subsample items for one language."""
    if source == "milu":
        items = load_milu(lang, split, get_hf_token())
    else:
        items = load_fallback(lang)
    if n and n < len(items):
        rng = random.Random(f"{seed}-{lang}")  # string seed: stable across Python versions
        items = sorted(rng.sample(items, n), key=lambda it: it.id)
    return items


def load_fewshot(lang: str, source: str, k: int, seed: int, exclude: set[str]) -> list[MCQItem]:
    """Few-shot exemplars: MILU validation split, or held-out fallback items."""
    if k <= 0:
        return []
    pool = load_milu(lang, "validation", get_hf_token()) if source == "milu" else load_fallback(lang)
    pool = [it for it in pool if it.id not in exclude]
    return random.Random(f"{seed}-{lang}-fewshot").sample(pool, min(k, len(pool)))
