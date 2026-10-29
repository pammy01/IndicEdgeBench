"""Prompt construction for MCQ scoring and generation timing."""

from __future__ import annotations

from .data import LETTERS, MCQItem

MCQ_INSTRUCTION = (
    "The following is a multiple choice question. "
    "Answer with the letter (A, B, C or D) of the correct option."
)
GEN_INSTRUCTION = "Answer the following question and briefly explain your reasoning."


def format_question(item: MCQItem) -> str:
    lines = [f"Question: {item.question}"]
    lines += [f"{LETTERS[i]}. {opt}" for i, opt in enumerate(item.options)]
    return "\n".join(lines)


def mcq_prompt(item: MCQItem, fewshot: list[MCQItem] = ()) -> str:
    """Zero/few-shot prompt ending in 'Answer:' so the next token is the answer letter."""
    parts = [MCQ_INSTRUCTION, ""]
    for ex in fewshot:
        parts += [format_question(ex), f"Answer: {LETTERS[ex.answer]}", ""]
    parts += [format_question(item), "Answer:"]
    return "\n".join(parts)


def generation_prompt(item: MCQItem) -> str:
    return "\n".join([GEN_INSTRUCTION, "", format_question(item), "Answer:"])
