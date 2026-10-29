"""Aggregate a run directory into summary tables and plots."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import LANGUAGES
from .config import load_config
from .metrics import bootstrap_ci, flip_rate, paired_delta

QUANT_ORDER = ["F16", "BF16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q4_0", "Q3_K_M", "Q2_K"]

# Validated categorical palette (dataviz skill reference instance), fixed order; text stays neutral ink.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def _quant_key(q: str) -> int:
    return QUANT_ORDER.index(q) if q in QUANT_ORDER else len(QUANT_ORDER)


def load_run(run_dir: Path):
    raw = pd.concat([pd.read_json(p, lines=True) for p in sorted((run_dir / "raw").glob("*.jsonl"))],
                    ignore_index=True)
    eff = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / "efficiency").glob("*.json"))]
    return raw, eff


def summarize(run_dir: Path) -> pd.DataFrame:
    cfg = load_config(run_dir / "config.yaml")
    n_boot, seed = cfg["bootstrap"]["n_resamples"], cfg["seed"]
    baselines = {m.name: m.baseline for m in cfg.models}
    raw, eff = load_run(run_dir)
    eff_by = {(e["model"], e["quant"]): e for e in eff}

    rows = []
    for (model, quant, lang), g in raw.groupby(["model", "quant", "lang"]):
        if (model, quant) not in eff_by:  # worker crashed mid-way; no efficiency record
            continue
        g = g.sort_values("id")
        e = eff_by[(model, quant)]
        le = e["languages"][lang]
        lo, hi = bootstrap_ci(g["correct"], n_boot, seed)
        row = {
            "model": model, "quant": quant, "lang": lang, "n": len(g),
            "accuracy": g["correct"].mean(), "acc_ci_lo": lo, "acc_ci_hi": hi,
            "truncated": int(g["truncated"].sum()),
            "prefill_tps": (le["prefill_tps"] or {}).get("median"),
            "decode_tps": (le["decode_tps"] or {}).get("median"),
            "decode_tps_std": (le["decode_tps"] or {}).get("std"),
            "ttft_ms": 1000 * (le["ttft_s"] or {}).get("median", float("nan")),
            "peak_rss_mb": e["peak_rss_mb"], "model_file_mb": e["model_file_mb"],
            "mcq_s_per_item": le["mcq_wall_s"] / max(le["n_items"], 1),
            "mcq_j_per_item": le["mcq_energy_j"] / max(le["n_items"], 1),
            "gen_j_per_token": le["gen_energy_j_per_token"],
            "energy_method": e["energy_method"],
            "tokens_per_word": le["fertility"]["tokens_per_word"],
        }
        base = raw[(raw.model == model) & (raw.quant == baselines.get(model)) & (raw.lang == lang)]
        base = base.sort_values("id")
        if len(base) == len(g) and quant != baselines.get(model):
            d, dlo, dhi = paired_delta(g["correct"].values, base["correct"].values, n_boot, seed)
            row.update(delta_vs_base=d, delta_ci_lo=dlo, delta_ci_hi=dhi,
                       flip_rate=flip_rate(g["pred"].values, base["pred"].values))
        rows.append(row)

    df = pd.DataFrame(rows)
    df["_q"] = df["quant"].map(_quant_key)
    df = df.sort_values(["model", "_q", "lang"]).drop(columns="_q").reset_index(drop=True)
    # Words/s is what a user feels: token speed divided by how many tokens the language needs per word.
    df["decode_words_per_s"] = df["decode_tps"] / df["tokens_per_word"]
    return df


def _style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, color=INK_2)
    ax.set_ylabel(ylabel, color=INK_2)
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_2)


def plot(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    langs = list(dict.fromkeys(df["lang"]))[: len(SERIES)]  # all-pairs scatter: max 3 hues
    color = {l: SERIES[i] for i, l in enumerate(langs)}
    paths = []

    for model, gm in df.groupby("model"):
        quants = sorted(gm["quant"].unique(), key=_quant_key)

        # 1. Quality vs. size per language: the Pareto view (file size is deterministic, unlike timing).
        fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor=SURFACE)
        for lang in langs:
            g = gm[gm.lang == lang].set_index("quant").reindex(quants).dropna(subset=["accuracy"])
            ax.plot(g["model_file_mb"], 100 * g["accuracy"], color=color[lang], linewidth=2, marker="o",
                    markersize=8, markeredgecolor=SURFACE, markeredgewidth=2, label=LANGUAGES[lang], zorder=3)
            for q, r in g.iterrows():
                ax.annotate(q, (r["model_file_mb"], 100 * r["accuracy"]), textcoords="offset points",
                            xytext=(6, 5), fontsize=8, color=INK_2)
        ax.axhline(25, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.annotate("chance (4 options)", (sum(ax.get_xlim()) / 2, 25), textcoords="offset points",
                    xytext=(0, 4), fontsize=8, color=INK_2, ha="center")
        _style(ax, f"{model}: accuracy vs. model size", "Model file size (MB)", "Accuracy (%)")
        ax.set_ylim(0, 100)
        ax.legend(frameon=False, labelcolor=INK)
        fig.tight_layout()
        paths.append(out_dir / f"pareto_{model}.png")
        fig.savefig(paths[-1], dpi=200)
        plt.close(fig)

        # 2. Accuracy per quant level with 95% bootstrap CIs, grouped by language.
        fig, ax = plt.subplots(figsize=(7.5, 4.2), facecolor=SURFACE)
        width = 0.8 / len(langs)
        for i, lang in enumerate(langs):
            g = gm[gm.lang == lang].set_index("quant").reindex(quants)
            xs = [j + (i - (len(langs) - 1) / 2) * width for j in range(len(quants))]
            err = [100 * (g["accuracy"] - g["acc_ci_lo"]), 100 * (g["acc_ci_hi"] - g["accuracy"])]
            ax.bar(xs, 100 * g["accuracy"], width=width - 0.03, color=color[lang], label=LANGUAGES[lang],
                   yerr=err, ecolor=INK_2, capsize=3, error_kw={"linewidth": 1})
        ax.axhline(25, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_xticks(range(len(quants)), quants)
        ax.set_ylim(0, 105)
        _style(ax, f"{model}: accuracy by quantization level (95% CI)", "Quantization", "Accuracy (%)")
        ax.grid(False, axis="x")
        ax.legend(frameon=False, labelcolor=INK, ncols=len(langs))
        fig.tight_layout()
        paths.append(out_dir / f"accuracy_{model}.png")
        fig.savefig(paths[-1], dpi=200)
        plt.close(fig)

    # 3. Tokenizer fertility: the hidden Indic latency tax.
    fert = df.groupby(["model", "lang"], as_index=False)["tokens_per_word"].first()
    models = list(dict.fromkeys(fert["model"]))[: len(SERIES)]
    fig, ax = plt.subplots(figsize=(7.5, 3.8), facecolor=SURFACE)
    width = 0.8 / len(models)
    for i, model in enumerate(models):
        g = fert[fert.model == model].set_index("lang").reindex(langs)
        xs = [j + (i - (len(models) - 1) / 2) * width for j in range(len(langs))]
        bars = ax.bar(xs, g["tokens_per_word"], width=width - 0.03, color=SERIES[i], label=model)
        ax.bar_label(bars, fmt="%.1f", color=INK_2, fontsize=8, padding=2)
    ax.set_xticks(range(len(langs)), [LANGUAGES[l] for l in langs])
    _style(ax, "Tokenizer fertility (tokens per word)", "", "Tokens per word")
    if len(models) > 1:
        ax.legend(frameon=False, labelcolor=INK)
    fig.tight_layout()
    ax.grid(False, axis="x")
    paths.append(out_dir / "fertility.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    # 4. What the user feels: words per second (decode tokens/s / fertility), at each model's baseline.
    fig, ax = plt.subplots(figsize=(7.5, 3.8), facecolor=SURFACE)
    for i, model in enumerate(models):
        gm = df[df.model == model]
        base = gm[gm["delta_vs_base"].isna()] if "delta_vs_base" in gm else gm
        g = base.groupby("lang")["decode_words_per_s"].first().reindex(langs)
        xs = [j + (i - (len(models) - 1) / 2) * width for j in range(len(langs))]
        bars = ax.bar(xs, g.values, width=width - 0.03, color=SERIES[i], label=model)
        ax.bar_label(bars, fmt="%.0f", color=INK_2, fontsize=8, padding=2)
    ax.set_xticks(range(len(langs)), [LANGUAGES[l] for l in langs])
    _style(ax, "Generation speed users feel (words per second, CPU)", "", "Words / s")
    ax.grid(False, axis="x")
    if len(models) > 1:
        ax.legend(frameon=False, labelcolor=INK)
    fig.tight_layout()
    paths.append(out_dir / "words_per_s.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)
    return paths


def _fmt(df: pd.DataFrame) -> str:
    cols = ["model", "quant", "lang", "n", "accuracy", "acc_ci_lo", "acc_ci_hi", "delta_vs_base",
            "flip_rate", "decode_tps", "decode_words_per_s", "prefill_tps", "ttft_ms", "peak_rss_mb",
            "model_file_mb", "mcq_j_per_item", "tokens_per_word"]
    t = df[[c for c in cols if c in df]].copy()
    for c in t.columns:
        if t[c].dtype.kind == "f":
            t[c] = t[c].map(lambda v: "" if pd.isna(v) else f"{v:.3f}" if abs(v) < 10 else f"{v:.0f}")
    head = "| " + " | ".join(t.columns) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in t.itertuples(index=False))


def report(run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    df = summarize(run_dir)
    df.to_csv(run_dir / "summary.csv", index=False)
    plots = plot(df, run_dir / "plots")
    info = json.loads((run_dir / "run_info.json").read_text(encoding="utf-8"))
    sysd = info["system"]
    md = [f"# IndicEdgeBench results: `{run_dir.name}`", "",
          f"- Data source: **{info['data_source']}**",
          f"- Hardware: {sysd['cpu']}, {sysd['physical_cores']} cores, {sysd['ram_gb']} GB RAM, {sysd['os']}",
          f"- llama-cpp-python {sysd['llama_cpp_python']}, Python {sysd['python']}",
          f"- Energy method: {df['energy_method'].iloc[0]} (see indicedgebench/meters.py)", "",
          "Accuracy CIs are 95% percentile bootstrap; `delta_vs_base` is a paired difference vs. the "
          "model's baseline quant; `flip_rate` is the share of items whose answer changed vs. baseline.", "",
          _fmt(df), ""]
    md += [f"![{p.stem}](plots/{p.name})" for p in plots]
    out = run_dir / "REPORT.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out
