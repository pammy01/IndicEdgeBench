"""Fast tests that need no model weights or network."""

import json
from pathlib import Path

import numpy as np
import pytest

from indicedgebench.config import load_config
from indicedgebench.data import LETTERS, MCQItem, _parse_target, load_fallback, load_items
from indicedgebench.metrics import bootstrap_ci, flip_rate, paired_delta
from indicedgebench.prompts import mcq_prompt

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("raw,expected", [("option1", 0), ("option4", 3), ("B", 1), ("3", 2), (2, 1)])
def test_parse_milu_target(raw, expected):
    assert _parse_target(raw, 4) == expected


def test_parse_milu_target_rejects_out_of_range():
    with pytest.raises(ValueError):
        _parse_target(7, 4)


@pytest.mark.parametrize("lang", ["en", "hi", "ta"])
def test_fallback_files_are_well_formed(lang):
    items = load_fallback(lang)
    assert len(items) == 30
    for it in items:
        assert len(it.options) == 4 and 0 <= it.answer < 4 and it.question


def test_fallback_is_parallel_across_languages():
    sets = {lang: [(i.id, i.answer) for i in load_fallback(lang)] for lang in ("en", "hi", "ta")}
    assert sets["en"] == sets["hi"] == sets["ta"]


def test_fallback_answers_are_balanced():
    counts = np.bincount([i.answer for i in load_fallback("en")], minlength=4)
    assert counts.max() - counts.min() <= 1


def test_sampling_is_deterministic():
    a = load_items("hi", "fallback", "test", 10, seed=7)
    b = load_items("hi", "fallback", "test", 10, seed=7)
    c = load_items("hi", "fallback", "test", 10, seed=8)
    assert [i.id for i in a] == [i.id for i in b] != [i.id for i in c]


def test_prompt_ends_with_answer_cue():
    item = MCQItem(id="x", lang="en", question="2+2?", options=["3", "4", "5", "6"], answer=1)
    p = mcq_prompt(item, [item])
    assert p.endswith("Answer:") and "Answer: B" in p and all(f"{l}. " in p for l in LETTERS)


def test_bootstrap_ci_brackets_mean():
    x = np.array([1] * 70 + [0] * 30)
    lo, hi = bootstrap_ci(x, 2000, seed=0)
    assert lo < 0.7 < hi and 0.55 < lo and hi < 0.85


def test_paired_delta_and_flip_rate():
    a, b = np.array([1, 1, 0, 0]), np.array([1, 0, 0, 1])
    d, lo, hi = paired_delta(a, b, 500, 0)
    assert d == 0.0 and lo <= 0 <= hi
    assert flip_rate([0, 1, 2, 3], [0, 1, 3, 2]) == 0.5


@pytest.mark.parametrize("name", ["smoke_mac.yaml", "pilot.yaml"])
def test_shipped_configs_load(name):
    cfg = load_config(ROOT / "configs" / name)
    assert cfg.models and all(m.baseline in m.quants for m in cfg.models)
