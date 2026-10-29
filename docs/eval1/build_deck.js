// Rebuild the Eval-1 deck from results:  node build_deck.js <out.pptx> <repo root>
// Needs pptxgenjs and summary.json (results/smoke_mac/summary.csv exported as JSON records) beside this script.
const pptxgen = require("pptxgenjs");
// Optional: a helper that writes THEME colours into the .pptx theme part (path via APPLY_THEME_JS).
const applyTheme = process.env.APPLY_THEME_JS ? require(process.env.APPLY_THEME_JS).applyTheme : null;
const rows = require("./summary.json");
const OUT = process.argv[2];
const ROOT = process.argv[3]; // repo root, for result plot images

// Indigo + saffron: an Indian-flag-adjacent palette without copying the flag.
const THEME = {
  name: "IndicEdgeBench",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F2A", lt1: "FFFFFF", dk2: "1F2A55", lt2: "F3F4F8",
    accent1: "E07A1F", accent2: "1F2A55", accent3: "1B8A7A", accent4: "2A78D6",
    accent5: "6B7280", accent6: "C2410C", hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { ink: "1B1F2A", ink2: "52514E", grid: "E4E3DF", indigo: "1F2A55", saffron: "E07A1F", teal: "1B8A7A", tint: "F3F4F8" };
const LANG = { en: "English", hi: "Hindi", ta: "Tamil" };
const SERIES = ["2A78D6", "EB6834", "1BAF7A"]; // same validated order as the result plots
const r = (q, l) => rows.find((x) => x.quant === q && x.lang === l);
const pct = (v) => `${Math.round(v * 100)}%`;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "IndicEdgeBench: Evaluation 1";
pres.author = "Pammy";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontSize: 48, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.0, w: 11.7, h: 2.2, fontSize: 18, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 32, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "IndicEdgeBench · Evaluation 1", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "6B7280", align: "right" },
});

function content(section, title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function card(s, name, x, y, w, h, fill = C.background2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { type: "none" }, rectRadius: 0.12, objectName: name });
}
function bullets(s, name, items, opts) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { isTextBox: true, fontSize: 16, color: C.text1, paraSpaceAfter: 8, valign: "top", objectName: name, ...opts });
}
const chartBase = (title) => ({
  showTitle: true, title, titleFontSize: 14, titleColor: HEX.ink, titleFontFace: "+mn-lt",
  catAxisLabelColor: HEX.ink2, valAxisLabelColor: HEX.ink2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 11, dataLabelColor: HEX.ink2, dataLabelFontFace: "+mn-lt",
  valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" },
  legendFontSize: 12, legendColor: HEX.ink, legendFontFace: "+mn-lt",
});

// ---------------------------------------------------------------- 1. Title
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  s.addText("IndicEdgeBench", { placeholder: "title" });
  s.addText([
    { text: "How much Indian-language quality do small LLMs lose when compressed to run on a laptop CPU, and what do we gain?", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 10 } },
    { text: "Final-year capstone · Evaluation 1 · Pammy · 31 October 2026", options: { color: C.accent1, fontSize: 16 } },
  ], { placeholder: "body" });
  s.addNotes("Introduce the one question the project answers. Everything that follows is about measuring both halves of the trade-off together.");
}

// ---------------------------------------------------------------- 2. Problem
{
  const s = content("Introduction", "The problem: offline AI in Indian languages has a hidden cost");
  bullets(s, "problem-bullets", [
    "Offline, private AI on the phones and laptops Indians actually own needs small (≤ 8B) models.",
    "To fit, models are quantized (16-bit → 8, 4 or 2 bits) and run on CPU runtimes like llama.cpp.",
    "Indian scripts are low-resource and split into many more tokens, so compression is expected to hurt them most.",
    "Nobody has measured how much quality is lost against how much speed, memory and energy is gained in Indic languages.",
  ], { x: 0.6, y: 1.5, w: 7.2, h: 4.8 });
  card(s, "stat-card", 8.3, 1.6, 4.4, 3.4, C.text2);
  s.addText(`${(r("Q8_0", "en").decode_words_per_s / r("Q8_0", "ta").decode_words_per_s).toFixed(1)}×`,
    { x: 8.6, y: 2.0, w: 3.8, h: 1.5, fontSize: 72, bold: true, color: C.accent1, fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: "stat-number" });
  s.addText("fewer words per second for Tamil than English, from the same model on the same CPU (our pilot)",
    { x: 8.6, y: 3.5, w: 3.8, h: 1.3, fontSize: 18, color: C.background1, valign: "top", margin: 0, isTextBox: true, objectName: "stat-label" });
  s.addNotes("The 5.5x number comes from our own pilot: decode tokens per second divided by tokenizer fertility.");
}

// ---------------------------------------------------------------- 3. Literature gap
pres.addSection({ title: "Background" });
{
  const s = content("Background", "Literature: each half is studied, never both together");
  const Y = "✓", N = "✗";
  const head = ["Work", "Indic tasks", "Quantization sweep", "Measured CPU latency / RAM / energy"].map((t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.indigo } } }));
  const body = [
    ["MILU, IndicParam, IndicGenBench, IndicRAGSuite", Y, N, N],
    ["Marchisio et al. 2024: Quantization & multilingual LLMs", "partial", Y, N],
    ["Marie & Fujita 2025: PTQ in machine translation", "MT only", Y, N],
    ["Multilingual Quantization Tax 2026 (preprint)", "partial", Y, N],
    ["PalmBench, Song et al. 2025, RooflineBench", N, Y, Y],
  ].map((row) => row.map((t, i) => ({ text: t, options: { align: i ? "center" : "left", color: t === N ? "B91C1C" : HEX.ink } })));
  const ours = ["IndicEdgeBench (this project)", Y, Y, Y].map((t, i) => ({ text: t, options: { bold: true, align: i ? "center" : "left", color: HEX.indigo, fill: { color: "FDEBD9" } } }));
  s.addTable([head, ...body, ours], { x: 0.6, y: 1.5, w: 12.1, colW: [5.5, 1.9, 2.1, 2.6], fontSize: 14, border: { type: "solid", pt: 0.75, color: HEX.grid }, rowH: 0.55, valign: "middle", objectName: "gap-table" });
  s.addText("Key evidence: a 1.7% automatic drop in Japanese hid a 16% drop in human ratings (Marchisio et al.); Indic MT can collapse entirely under PTQ (Marie & Fujita). All 20 references verified on arXiv; see docs/literature_survey.md.",
    { x: 0.6, y: 5.6, w: 12.1, h: 1.0, fontSize: 13, color: C.accent5, italic: true, margin: 0, isTextBox: true, objectName: "gap-note" });
  s.addNotes("Indic benchmarks evaluate only full-precision models; on-device benchmarks evaluate only English. That empty cell is our contribution.");
}

// ---------------------------------------------------------------- 4. Objectives
{
  const s = content("Background", "Objectives");
  const objs = [
    ["1", "Open harness", "Score quantized GGUF models on Indic MCQs and measure CPU efficiency in one run"],
    ["2", "Quality loss", "Per-language accuracy drop at F16 → Q8 → Q4 → Q2, with CIs and flip rates"],
    ["3", "Efficiency gain", "Speed, time-to-first-token, peak RAM and energy per configuration"],
    ["4", "Tokenizer tax", "Fertility (tokens/word) and the words/s a user actually experiences"],
    ["5", "Pareto frontier", "Quality-vs-efficiency curves per language, released on GitHub and Hugging Face"],
  ];
  objs.forEach(([n, h, d], i) => {
    const y = 1.5 + i * 1.05;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.1, w: 0.7, h: 0.7, fill: { color: i === 4 ? C.accent1 : C.text2 }, line: { type: "none" }, objectName: `obj-dot-${n}` });
    s.addText(n, { x: 0.6, y: y + 0.1, w: 0.7, h: 0.7, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `obj-num-${n}` });
    s.addText([{ text: h, options: { bold: true, color: C.text2, fontSize: 18, breakLine: true } }, { text: d, options: { color: C.text1, fontSize: 15 } }],
      { x: 1.6, y, w: 11.1, h: 0.9, valign: "middle", margin: 0, isTextBox: true, objectName: `obj-text-${n}` });
  });
}

// ---------------------------------------------------------------- 5. Architecture
pres.addSection({ title: "Design" });
{
  const s = content("Design", "System architecture: five layers, one command");
  const layers = [
    ["Data", "MILU (11 langs) or bundled 30-item parallel set → frozen, seeded sample"],
    ["Models", "GGUF from Hugging Face: F16 · Q8_0 · Q4_K_M · Q2_K"],
    ["Runtime & meters", "llama.cpp on CPU, one fresh process per config; RAM, energy, timing"],
    ["Evaluation", "Letter log-likelihood scoring; bootstrap CI, paired Δ, flip rate, words/s"],
    ["Release", "summary.csv, REPORT.md, plots; later HF dataset + leaderboard"],
  ];
  const w = 2.25, gap = 0.21;
  layers.forEach(([h, d], i) => {
    const x = 0.6 + i * (w + gap);
    card(s, `layer-${i + 1}`, x, 1.7, w, 3.3, i === 2 ? "FDEBD9" : C.background2);
    s.addText(String(i + 1), { x: x + 0.2, y: 1.85, w: 0.6, h: 0.6, fontSize: 28, bold: true, color: C.accent1, fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: `layer-num-${i + 1}` });
    s.addText([{ text: h, options: { bold: true, fontSize: 17, color: C.text2, breakLine: true } }, { text: d, options: { fontSize: 13, color: C.text1 } }],
      { x: x + 0.2, y: 2.5, w: w - 0.4, h: 2.4, valign: "top", margin: 0, isTextBox: true, objectName: `layer-text-${i + 1}` });
    if (i < layers.length - 1)
      s.addShape(pres.shapes.CHEVRON, { x: x + w + 0.03, y: 3.2, w: 0.15, h: 0.3, fill: { color: C.accent5 }, line: { type: "none" }, objectName: `layer-arrow-${i + 1}` });
  });
  s.addText("python -m indicedgebench run configs/pilot.yaml", { x: 0.6, y: 5.4, w: 12.1, h: 0.6, fontSize: 16, fontFace: "Courier New", color: C.text2, fill: { color: C.background2 }, align: "center", valign: "middle", isTextBox: true, objectName: "cli" });
  s.addText("Resumable · config-driven · cross-platform (macOS dev, Windows 11 laptop runs) · 17 unit tests",
    { x: 0.6, y: 6.15, w: 12.1, h: 0.4, fontSize: 13, color: C.accent5, align: "center", margin: 0, isTextBox: true, objectName: "cli-note" });
}

// ---------------------------------------------------------------- 6. Methodology
{
  const s = content("Design", "Methodology");
  const cols = [
    ["Quality", ["Prompt ends in “Answer:”; pick the A–D letter with the highest next-token logit (lm-eval-harness style)", "Deterministic, no answer parsing: robust for small models in Indic languages", "Identical frozen items for every config"]],
    ["Statistics", ["95% bootstrap CIs (1,000 resamples, fixed seed)", "Paired bootstrap Δ vs. baseline on the same items", "Flip rate: share of answers that change under quantization"]],
    ["Efficiency", ["Fresh process per config; warm-up before timing", "Fixed 64-token greedy decode, 3 repeats, median ± std", "Peak RSS sampled every 20 ms; energy = RAPL or labelled estimate"]],
  ];
  cols.forEach(([h, items], i) => {
    const x = 0.6 + i * 4.1;
    card(s, `method-${h}`, x, 1.5, 3.9, 3.6);
    s.addText(h, { x: x + 0.25, y: 1.7, w: 3.4, h: 0.5, fontSize: 20, bold: true, color: C.text2, margin: 0, isTextBox: true, objectName: `method-h-${h}` });
    bullets(s, `method-b-${h}`, items, { x: x + 0.25, y: 2.3, w: 3.4, h: 2.7, fontSize: 14 });
  });
}

// ---------------------------------------------------------------- 7. Implementation status
{
  const s = content("Design", "Implementation status (v0.1)");
  const done = ["Config-driven sweep runner (resumable)", "MILU loader + 30-item parallel en/hi/ta set", "llama.cpp engine: MCQ scoring + generation timing", "Memory, energy and fertility meters", "Statistics: bootstrap CI, paired Δ, flip rate", "Report: CSV, Markdown, 4 plots", "Windows + macOS setup scripts, 17 tests"];
  const next = ["Pilot on Windows laptop: Qwen2.5-1.5B + Llama-3.2-1B", "MILU with 200 items per language (HF token)", "Native-speaker validation of the item set", "More languages (Telugu, Bengali, Marathi)", "ONNX INT8 runtime, Android phone measurements"];
  card(s, "done-card", 0.6, 1.5, 6.0, 4.0);
  card(s, "next-card", 6.9, 1.5, 5.8, 4.0, "FDEBD9");
  s.addText("Done for Evaluation 1", { x: 0.85, y: 1.65, w: 5.5, h: 0.5, fontSize: 20, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "done-h" });
  bullets(s, "done-list", done, { x: 0.85, y: 2.2, w: 5.5, h: 3.2, fontSize: 15, paraSpaceAfter: 6 });
  s.addText("Next", { x: 7.15, y: 1.65, w: 5.3, h: 0.5, fontSize: 20, bold: true, color: C.accent6, margin: 0, isTextBox: true, objectName: "next-h" });
  bullets(s, "next-list", next, { x: 7.15, y: 2.2, w: 5.3, h: 3.2, fontSize: 15, paraSpaceAfter: 6 });
}

// ---------------------------------------------------------------- 8. Results: accuracy
pres.addSection({ title: "Pilot results" });
{
  const s = content("Pilot results", "Pilot: Indic accuracy sits near chance; English degrades steadily");
  s.addImage({ path: `${ROOT}/results/smoke_mac/plots/accuracy_qwen2.5-0.5b-instruct.png`, x: 0.6, y: 1.5, w: 7.6, h: 4.26, altText: "Accuracy by quantization level for English, Hindi and Tamil with 95% confidence intervals", objectName: "acc-chart" });
  card(s, "acc-takeaways", 8.5, 1.5, 4.2, 4.26);
  bullets(s, "acc-bullets", [
    `English: ${pct(r("Q8_0", "en").accuracy)} → ${pct(r("Q2_K", "en").accuracy)} from Q8 to Q2`,
    `Hindi ${pct(r("Q8_0", "hi").accuracy)} and Tamil ${pct(r("Q8_0", "ta").accuracy)} are already near chance (25%) at Q8: a 0.5B model barely understands them`,
    `Flip rate at Q4: ${pct(r("Q4_K_M", "hi").flip_rate)} of Hindi and ${pct(r("Q4_K_M", "ta").flip_rate)} of Tamil answers change vs. ${pct(r("Q4_K_M", "en").flip_rate)} in English`,
    "Flat accuracy can hide unstable answers; flip rate exposes it",
  ], { x: 8.75, y: 1.7, w: 3.75, h: 3.9, fontSize: 14 });
  s.addNotes("Qwen2.5-0.5B on Apple M3 CPU; Q8_0 is the baseline because the F16 download was paused. 30 items gives wide CIs (about ±17 points), which is why the laptop pilot uses 200 MILU items.");
}

// ---------------------------------------------------------------- 9. Results: tokenizer tax
{
  const s = content("Pilot results", "The tokenizer tax: same speed in tokens, 5× slower in words");
  const langs = ["en", "hi", "ta"];
  s.addImage({ path: `${ROOT}/results/smoke_mac/plots/fertility.png`, x: 0.6, y: 1.5, w: 5.9, h: 2.99, altText: "Tokenizer fertility: English 1.6, Hindi 4.7, Tamil 8.3 tokens per word", objectName: "fert-chart" });
  s.addImage({ path: `${ROOT}/results/smoke_mac/plots/words_per_s.png`, x: 6.8, y: 1.5, w: 5.9, h: 2.99, altText: "Words per second: English 85, Hindi 29, Tamil 15", objectName: "wps-chart" });
  const stats = [
    [`${Math.round(Math.min(...langs.map((l) => r("Q8_0", l).decode_tps)))}–${Math.round(Math.max(...langs.map((l) => r("Q8_0", l).decode_tps)))}`, "tokens/s decode in every language: the CPU is not the difference"],
    [`${(r("Q8_0", "ta").mcq_j_per_item / r("Q8_0", "en").mcq_j_per_item).toFixed(1)}×`, "energy per Tamil question vs. English (estimated)"],
    [`${Math.round(r("Q8_0", "ta").ttft_ms)} vs ${Math.round(r("Q8_0", "en").ttft_ms)} ms`, "time to first token, Tamil vs. English"],
  ];
  stats.forEach(([n, l], i) => {
    const x = 0.6 + i * 4.1;
    card(s, `tax-stat-${i}`, x, 4.85, 3.9, 1.45);
    s.addText(n, { x: x + 0.2, y: 4.9, w: 3.5, h: 0.65, fontSize: 26, bold: true, color: C.accent1, fontFace: THEME.headFontFace, margin: 0, valign: "middle", isTextBox: true, objectName: `tax-n-${i}` });
    s.addText(l, { x: x + 0.2, y: 5.55, w: 3.5, h: 0.7, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: `tax-l-${i}` });
  });
}

// ---------------------------------------------------------------- 10. Results: memory
{
  const s = content("Pilot results", "What compression buys at 0.5B: memory, not speed");
  s.addImage({ path: `${ROOT}/docs/eval1/memory.png`, x: 0.6, y: 1.5, w: 7.6, h: 4.26, altText: "Model file size and peak RAM for Q8_0, Q4_K_M and Q2_K", objectName: "mem-chart" });
  card(s, "mem-takeaways", 8.5, 1.5, 4.2, 4.26);
  const saved = 1 - r("Q4_K_M", "en").peak_rss_mb / r("Q8_0", "en").peak_rss_mb;
  bullets(s, "mem-bullets", [
    `Q4_K_M cuts peak RAM by ${pct(saved)} vs. Q8_0`,
    "Q2_K saves almost nothing more: runtime buffers dominate at this size",
    "Decode speed barely moves (~130–140 tokens/s): a 0.5B model is not memory-bandwidth bound on the M3",
    "Larger 1–1.5B models on the Intel laptop should show the speed gain; that is the next run",
  ], { x: 8.75, y: 1.7, w: 3.75, h: 3.9, fontSize: 14 });
}

// ---------------------------------------------------------------- 11. Limitations
pres.addSection({ title: "Plan" });
{
  const s = content("Plan", "Honest limitations of the pilot");
  const lim = [
    ["30 items", "Wide confidence intervals (about ±17 points). Fix: MILU, 200+ items per language."],
    ["0.5B model", "Too small for Indic: near-chance accuracy hides quantization effects. Fix: 1–1.5B models next."],
    ["Q8 baseline", "F16 download paused on the dev Mac. Fix: F16 baseline in the laptop pilot."],
    ["Energy", "Estimated from CPU time × TDP on macOS/Windows. Fix: RAPL on Linux, battery drain on phone."],
    ["Item validity", "Hindi/Tamil items not yet native-speaker validated. Fix: annotation protocol, IAA ≥ 0.6."],
  ];
  lim.forEach(([h, d], i) => {
    const y = 1.5 + i * 1.02;
    card(s, `lim-${i}`, 0.6, y, 12.1, 0.88, i % 2 ? C.background1 : C.background2);
    s.addText(h, { x: 0.85, y, w: 2.6, h: 0.88, fontSize: 17, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: `lim-h-${i}` });
    s.addText(d, { x: 3.5, y, w: 9.0, h: 0.88, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `lim-d-${i}` });
  });
}

// ---------------------------------------------------------------- 12. Timeline
{
  const s = content("Plan", "Plan to the final evaluation");
  const steps = [
    ["Weeks 1–4", "Literature, design, harness v0.1, Mac pilot", true],
    ["Weeks 5–6", "Laptop pilot: 2 models × 3–4 quants, MILU", false],
    ["Weeks 7–10", "Native-speaker validation, fresh contamination-resistant slice", false],
    ["Weeks 11–18", "Full sweep: 6–8 models, 4–6 languages, ONNX INT8, phone", false],
    ["Weeks 19–24", "Pareto analysis, leaderboard, paper, HF release", false],
  ];
  s.addShape(pres.shapes.LINE, { x: 0.9, y: 3.05, w: 11.5, h: 0, line: { color: HEX.grid, width: 3 }, objectName: "timeline-line" });
  steps.forEach(([when, what, done], i) => {
    const x = 0.6 + i * 2.45;
    s.addShape(pres.shapes.OVAL, { x: x + 0.05, y: 2.8, w: 0.5, h: 0.5, fill: { color: done ? C.accent3 : C.accent1 }, line: { color: "FFFFFF", width: 2 }, objectName: `tl-dot-${i}` });
    s.addText(when, { x, y: 2.0, w: 2.3, h: 0.6, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true, objectName: `tl-when-${i}` });
    s.addText(what, { x, y: 3.5, w: 2.25, h: 1.8, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: `tl-what-${i}` });
  });
  s.addText([{ text: "Done ", options: { bold: true, color: C.accent3 } }, { text: "= Evaluation 1 scope.  Target venues: ACL/EMNLP/NeurIPS workshop (D&B, efficiency, ML4D) + arXiv preprint.", options: { color: C.accent5 } }],
    { x: 0.6, y: 5.8, w: 12.1, h: 0.6, fontSize: 14, margin: 0, isTextBox: true, objectName: "tl-note" });
}

// ---------------------------------------------------------------- 13. Close
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Plan" });
  s.addText("Thank you", { placeholder: "title" });
  s.addText([
    { text: "Code, data and results: github.com/pammy01/IndicEdgeBench", options: { breakLine: true } },
    { text: "Live demo: python -m indicedgebench run configs/smoke_mac.yaml (≈ 2 minutes)", options: { color: C.accent1 } },
  ], { placeholder: "body" });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (applyTheme) await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
