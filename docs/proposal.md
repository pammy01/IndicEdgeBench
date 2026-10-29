# The AI Systems + Applied-Indic-Language Capstone: A Non-Cybersecurity Final-Year Project Built for Hiring, Publication, and Open-Source Adoption

## TL;DR

- **Build “IndicEdgeBench” — the first open-source benchmark + harness that measures how much quantization and CPU/on-device inference degrade *small* language models on *Indic-language* tasks, jointly plotting quality loss against measured latency/memory/energy on laptops and phones.** It sits exactly at the intersection of AI systems/infrastructure (inference optimization, evaluation infrastructure) and an applied India-specific domain, needs no GPU training, and a dedicated novelty survey confirmed that no existing public benchmark, paper, or repo occupies this triple intersection.
- **The market is shifting decisively from model *training* toward AI *systems, inference efficiency, and evaluation*** — small/on-device models, quantization/serving, and LLM evals are the fastest-growing skill clusters in 2025-2026 job postings, and India’s GCC/startup market is short of exactly this talent. A rigorous evals-and-efficiency artifact is disproportionately impressive for an entry-level candidate.
- **This project can plausibly hit all three of the student’s goals**: a resume-grade open-source tool + Hugging Face dataset (adoption), a NeurIPS/ACL-workshop-style Datasets & Benchmarks paper (MS/PhD), and demonstrable skills (quantization, llama.cpp/ONNX, eval methodology, Indic NLP) that map directly onto real AI-engineering job descriptions.

## Key Findings

### The hiring market rewards systems + evaluation over model-building

- Independent job-market analysis finds the “AI Engineer” title is now distinct and in high demand, with **over 500,000 open AI/ML roles globally in 2026, concentrated in the US, India, and Western Europe** (365 Data Science, citing a World Economic Forum figure). The same source reports PyTorch appears in ~42% of ML-engineer postings and vector databases in a notable share of AI-engineer postings.
- The market has “narrowed in practice”: employers want people who can “operate ML in production, not just describe the theory.” A 2026 US snapshot found ~490 new ML-engineering postings per week, 86% individual-contributor and 70% mid/senior  (Axial Search, via TekRecruiter) — the field rewards demonstrable execution over credentials.
- **Inference-optimization is a named, hot specialization.** NVIDIA’s “AI Inference Performance Engineer — New College Grad 2026” posting asks for “quantization, scheduling, memory management, and distributed inference across TensorRT-LLM, SGLang, and vLLM.”  Together AI, XPENG, and Rakuten postings all list KV-cache, PagedAttention, continuous batching, speculative decoding, GPTQ/AWQ/SmoothQuant, and llama.cpp/ONNX Runtime as core skills. GGUF/AWQ post-training quantization and TTFT/inter-token-latency observability recur across LLM-engineer role descriptions.
- **India specifics:** the EY India GCC Pulse Survey 2025 (released 23 Nov 2025; responses Aug–Oct 2025) found **58% of Indian GCCs currently investing in agentic AI (another 29% planning to scale within a year) and 83% already investing in generative AI, with pilots rising from 37% to 43% year over year.** Bengaluru anchors the largest Indian AI talent pool (Sarvam AI, Krutrim, plus ML platform teams at Razorpay/Swiggy/Flipkart); Hyderabad is second (Microsoft, Amazon, Google). Entry-level AI/ML salaries cluster around ₹6–12 LPA,  with GenAI/LLM/MLOps and production-deployment skills commanding a 25-45% premium, and GCC/AI-native-startup roles paying well above IT-services firms.
- **Saturation signal:** multiple sources warn that “prompt engineer” as a standalone fresher title  is weak, and basic RAG is now commodity. Differentiation comes from production/systems competence and rigorous evaluation.

### Where AI is heading (1-3 years) aligns with a laptops-only team

- **Small language models + on-device/edge is a genuine structural trend, not hype.** Gartner (press release, 1 May 2025) projected that **“by 2027, organizations will implement small, task-specific AI models, with usage volume at least three times more than those of general-purpose large language models.”** NVIDIA Research made the case explicitly in “Small Language Models are the Future of Agentic AI” (Belcak, Heinrich, Diao, Fu, Dong, Muralidharan, Lin & Molchanov, arXiv:2506.02153, 2 June 2025), arguing SLMs are “sufficiently powerful, inherently more suitable, and necessarily more economical for many invocations in agentic systems.” Runtimes like llama.cpp, Ollama, MLC-LLM, and ExecuTorch (v1.0, late 2025) make CPU/consumer-hardware inference practical. **The student’s hard constraint (laptops, no GPU) therefore coincides with one of the hottest research/product frontiers.**
- **Evaluation (“evals”) is a discipline in crisis and in demand.** 2025-2026 arXiv literature documents benchmark contamination (levels reaching ~45% on popular benchmarks per Li et al.), saturation of medical and knowledge benchmarks, and LLM-as-judge unreliability — a December 2025 study (cited by LangChain) found even top judges (Gemini-2.5-Pro, GPT-5) flip preferences in roughly a quarter of hard cases, alongside documented verbosity, self-enhancement, and position biases. Domain- and language-specific, contamination-resistant benchmarks with human validation are explicitly called for.
- **RAG has matured into agentic/GraphRAG/late-interaction (ColBERT/ColPali) territory**, so a “basic RAG chatbot” is derivative — but retrieval *evaluation* for under-served languages remains open.
- **Regulation is creating demand for measurement/governance artifacts:** India’s DPDP Act (Phase 1 enforcement live since 14 Nov 2025), the RBI FREE-AI framework (13 Aug 2025; 7 Sutras, 6 Pillars, 26 recommendations), MeitY’s India AI Governance Guidelines (Nov 2025),  and the EU AI Act globally all push toward documented evaluation, model cards/datasheets, and reproducibility (ISO/IEC 42001 as the management-system standard).

### The India-language + efficiency gap is real and under-served

- Indic languages are low-resource and **disproportionately hurt by the exact compression techniques required to run on laptops.** Cohere/Cohere For AI’s “How Does Quantization Affect Multilingual LLMs?” (Marchisio et al., arXiv:2407.03211, Findings of EMNLP 2024) found non-Latin scripts are “impacted worst,” that automatic metrics *severely underestimate* the damage — **“a 1.7% average drop in Japanese across automatic tasks corresponds to a 16.0% drop reported by human evaluators on realistic prompts”** — and that hard tasks like math reasoning degrade fastest (up to -13.1%).
- “The Uneven Impact of Post-Training Quantization in Machine Translation” (Marie & Fujita, NICT, arXiv:2508.20893) found quantization “substantially degrades performance for these lower-resource languages, especially Indic languages, and in some cases eliminates their ability to translate them into English”  — but only for MT, and with no on-device efficiency measurement.
- **Indic tokenizer inefficiency directly inflates on-device latency.** Reported fertility scores reach ~10.5 for Oriya under the LLaMA-4 tokenizer (IndicSuperTokenizer); IndicGenBench reports Indic fertility from 4.1 (Pashto) to 19.9 (Tibetan); and BHARATI (arXiv 2607.23319) shows an improved Indic tokenizer cuts a 100-word Tamil response from ~890 to ~205 generation steps (a 4.3× latency reduction, median 12.4s → 2.9s). This is a systems problem an edge benchmark should quantify.
- AI4Bharat’s MILU (Verma, Khan et al., Nilekani Centre at AI4Bharat + IBM Research India; NAACL 2025; arXiv:2411.02538) provides **~85,000 MCQs across 11 Indic languages plus an 8,933-sample validation set, spanning 8 domains and 41 subjects; of 45 LLMs evaluated, GPT-4o scored highest at 72% average accuracy.** Alongside IndicParam (arXiv 2512.00333), IndicRAGSuite (arXiv 2506.01615), Hindi-BEIR (arXiv 2409.05401), and IndicGenBench, these are strong *quality* benchmarks — but all evaluate in full precision (bf16) and report **no efficiency and no quantization study.**

## Details

### The recommended project — “IndicEdgeBench”

**Problem statement.** To run useful AI on the devices most Indians actually own — mid-range laptops and phones, offline, in Hindi/Tamil/Telugu/Bengali/Marathi and more — developers must use small (1B-8B) models compressed via quantization (GGUF Q4/Q8, ONNX INT8) and CPU runtimes (llama.cpp, ONNX Runtime, MLC-LLM). But nobody has systematically measured **how much quality you lose in Indic languages when you compress and run on-device, versus how much speed/memory/energy you gain.** Existing Indic benchmarks ignore efficiency; existing on-device benchmarks ignore Indic languages; the one Indic-relevant quantization study covers only machine translation with no efficiency numbers.

**The precise novel contribution.** IndicEdgeBench is the first artifact to occupy the *triple intersection* of (a) Indic-language task quality, (b) quantization sweeps including GGUF Q2/Q4/Q8 and ONNX INT8, and (c) *measured* on-device CPU/laptop/phone latency, memory, and energy — reported as a **quality-efficiency Pareto frontier per language and per task.** A dedicated novelty survey (checking arXiv, GitHub, and Hugging Face) confirmed no existing work hits all three axes. The closest existing works and how IndicEdgeBench differs:

- vs **MILU / IndicParam / IndicRAGSuite / Hindi-BEIR** (AI4Bharat and others): those measure Indic quality at full precision only, with no quantization and no efficiency; IndicEdgeBench adds the compression and on-device systems dimension and reuses their questions as the quality substrate.
- vs **“How Does Quantization Affect Multilingual LLMs?” (arXiv 2407.03211)**: that is multilingual (not Indic-focused), uses 8-103B models, and measures no latency/memory/energy; IndicEdgeBench is Indic-first, small-model, and on-device with real hardware measurement.
- vs **“Uneven Impact of PTQ in MT” (arXiv 2508.20893)**: that covers Indic + GGUF but only machine translation and reports no measured efficiency; IndicEdgeBench covers knowledge/reasoning/retrieval tasks and adds the efficiency axis.
- vs **PalmBench (arXiv 2410.05315) and “Systematic Evaluation of On-Device LLMs” (arXiv 2505.15030)**: those measure on-device quantized quality+efficiency but only for English/general tasks; IndicEdgeBench swaps in Indic evaluation.
- vs concurrent **“Multilingual Quantization Tax” (arXiv 2608.09941)**: that frames “edge SLMs” and non-Latin fragility but reports accuracy only (no measured efficiency) over 8 mixed languages; IndicEdgeBench is Indic-specific and measures real device efficiency. Also useful methodological templates: “Which Quantization Should I Use? … llama.cpp Quantization” (arXiv 2601.14277) and RooflineBench (arXiv 2602.11506), both English-only.

**Why it matters (evidence of real-world need).** Alternative-data credit, agricultural voice advisories, and rural health/education tools in India increasingly need offline, vernacular, low-cost inference. Agri-advisory field reports (Gates Foundation/GIZ/CLEAR Global AIEP, arXiv 2601.11537) name latency — “especially for voice” — as a top problem, mitigated via in-country/on-device hosting; agri teams document 5,000+ previously-undocumented vernacular terms. A benchmark that tells builders “for Telugu QA, Q4 costs you X% quality for a Y× speedup, but Q8 is the sweet spot” is directly actionable and aligns with DPDP/FREE-AI pressure toward on-device, privacy-preserving, documented systems.

**System architecture.**

1. **Task/data layer:** curate a compact Indic evaluation suite by sampling and re-validating from MILU (knowledge MCQ, 11 languages), IndicRAGSuite/Hindi-BEIR (retrieval), and a small human-authored open-ended set with rubric grading; add a contamination-resistant slice (freshly authored items) to address the contamination problem documented in 2025 literature.
1. **Model layer:** 6-10 small open models (e.g., Gemma 3n, Qwen3 small variants, Llama 3.2 1B/3B, Sarvam/Indic-tuned small models) in FP16 baseline vs GGUF Q8/Q4/Q2 (llama.cpp) and ONNX INT8 (ONNX Runtime); optionally MLC-LLM.
1. **Runtime/measurement layer:** a harness wrapping llama.cpp/ONNX Runtime that records tokens/sec (prefill + decode), time-to-first-token, peak RAM, and energy (via psutil / platform power counters / phone battery drain), plus tokenizer fertility per language.
1. **Evaluation layer:** integrate with EleutherAI’s lm-evaluation-harness (MILU already has a port)  for quality; use a *calibrated, human-validated* LLM-as-judge for open-ended items with reported inter-annotator agreement, explicitly guarding against the judge-reliability failures documented in 2025.
1. **Release layer:** dataset + results on Hugging Face (with Croissant metadata, now required by the NeurIPS D&B track — 85.7% of 2025 accepted D&B papers included a Croissant document, and 321 of 497 hosted on Hugging Face), harness on GitHub, and an interactive Pareto-frontier leaderboard on a Hugging Face Space.

**Phased plan (5-8 months, team of 3-4).**

- *Month 1:* literature lock-in; reproduce a baseline (run MILU on one small model FP16 vs Q4 on a laptop); finalize task subset and metrics.
- *Month 2:* build the measurement harness (llama.cpp + ONNX Runtime wrappers; latency/memory/energy logging); validate on 2 models × 2 languages.
- *Month 3:* human-annotation protocol design + pilot (rubrics, inter-annotator agreement targets ≥0.6 Krippendorff/Cohen); author the contamination-resistant slice.
- *Months 4-5:* full sweep — models × quant levels × languages × tasks × devices; collect quality and efficiency; run ablations (calibration-data effect, tokenizer fertility vs latency).
- *Month 6:* analysis (per-language degradation curves, Pareto frontiers, bootstrap confidence intervals); build leaderboard Space; write the paper.
- *Months 7-8:* Hugging Face + GitHub release; community outreach (AI4Bharat/EleutherAI channels); workshop submission; buffer for revisions.

**Technologies/libraries.** Python, llama.cpp (GGUF), ONNX Runtime, MLC-LLM, Hugging Face `transformers`/`datasets`, EleutherAI lm-evaluation-harness, psutil, matplotlib/plotly, Streamlit/Gradio (Space). Optional free-tier Kaggle (30 hrs/week GPU) or Colab only to produce an FP16 GPU reference point — not required for the core.

**Evaluation methodology (publishable rigor).** Multiple models and quant levels (not one), FP16 baselines, per-language and per-task breakdowns, bootstrap confidence intervals, human validation with reported agreement, a contamination-resistant subset, and full reproducibility (pinned configs, seeds, hardware specs). This directly answers the “credible, publishable numbers” bar and the D&B track’s reproducibility/Croissant requirements.

**Risks and de-risking.**

- *Scope creep* → fix a small language set (4-6) and model set (6-8) early; every added axis multiplies runs.
- *On-device measurement noise* → control for thermal throttling (the edge literature, e.g. arXiv 2603.23640, shows thermal rather than compute is often the mobile bottleneck), fix context length, average over repeated runs, and report variance.
- *Judge unreliability* → prefer MCQ/retrieval tasks (objective) for headline numbers; use judges only for a validated open-ended slice.
- *“Someone publishes first”* → the space is closing (see concurrent 2026 preprints); ship a v0.1 dataset + harness on Hugging Face early to establish precedence, then iterate.
- *Model licensing/tokenizer quirks* → verify licenses; document tokenizer fertility as a first-class result rather than a nuisance.

**Resume / interview framing.** Resume bullet: “Created IndicEdgeBench, an open-source benchmark and measurement harness quantifying the quality-vs-latency/energy tradeoff of quantized small LLMs across 6 Indian languages on llama.cpp/ONNX (CPU); released dataset (Hugging Face) + harness (GitHub), N★ stars, workshop paper.” Interview talking points: quantization internals (GGUF K-quants, INT8), why non-Latin scripts degrade under compression, KV-cache and decode-vs-prefill dynamics, LLM-as-judge calibration, and reproducible evaluation design. These map directly onto inference-optimization and AI-evaluation job descriptions.

### Runner-up alternatives (briefly)

1. **“Indic Speculative Decoding on CPU”** — implement and benchmark draft-model speculative decoding (a small Indic draft model + larger verifier) for CPU-only vernacular inference, measuring speedup vs quality on Indic tasks. Systems-heavy and novel for Indic + CPU, but higher implementation risk.
1. **“AgriEvalKit” — a golden-QA benchmark + agentic-RAG evaluation harness for Indian smallholder agri-advisory**, extending the golden Q&A sets  referenced in the Gates/GIZ AIEP work into an open, multilingual, contamination-controlled benchmark with retrieval + factuality metrics. Strong applied-domain and ML4D-workshop fit; the main risk is agronomic ground-truth curation.
1. **“ThinFile-Bench” — an open, reproducible benchmark and fairness/explainability harness for alternative-data credit scoring on tabular Indian data** (UPI/utility/telecom-style synthetic or open data), aligned to RBI FREE-AI (SHAP explainability, disparate-impact ratio).  Classical-ML + governance angle, laptop-friendly; the main risk is realistic data access (may require synthetic data).

### Overused / saturated final-year AI ideas to avoid (and why)

- **Basic RAG chatbot / “chatbot for college FAQs”** — commodity; no novelty, thousands of clones.
- **Plant-disease-detection CNN, crop-yield prediction** — the cliché of agri projects; datasets saturated, no systems depth.
- **Generic medical-image classifier / diabetes prediction** — solved to death; knowledge benchmarks are saturating (top models exceed 90% on MedQA/MedMCQA).
- **Stock-price-prediction LSTM** — not credibly predictive; a red flag to interviewers.
- **Fake-news / sentiment-analysis / resume-screener / movie-recommender** — tutorial-tier, no differentiation, sometimes ethically fraught.
- **A bare fine-tune of an LLM on a small dataset with no evaluation** — everyone does it; without rigorous evals it signals nothing to a hiring manager.

## Recommendations

1. **Commit to IndicEdgeBench as the primary project.** It is the single option that plausibly delivers all three goals (job, publication, adoption) under the laptops-only constraint, and its novelty is verifiable against named prior work.
1. **Stage-gate by month 2:** if the measurement harness cannot reliably log latency/memory on your laptops, narrow to quality-vs-quantization only (drop energy) — still publishable. *Threshold to continue full scope:* stable, low-variance timing across repeated runs on ≥2 devices.
1. **Ship early for precedence:** release a v0.1 dataset + harness on Hugging Face by ~month 4, given concurrent 2026 preprints in adjacent space. *Trigger to accelerate:* if a new preprint covering Indic + on-device quantization appears, pivot framing to a distinct language/task set and emphasize the efficiency-measurement depth.
1. **Target venue:** an ACL/EMNLP/NeurIPS workshop (Datasets & Benchmarks, an efficiency workshop, or ML4D / Machine Learning for Development) plus an arXiv preprint; regional venues (ACM COMPASS, ICTD) and a Hugging Face community release are strong complements. The NeurIPS D&B track and Hugging Face are the standard homes for this artifact type.
1. **Divide labor:** one member owns the runtime/measurement harness, one owns data curation + human annotation, one owns quality-eval integration + statistics, and one owns the leaderboard Space + paper.
1. **Fallback:** if the team prefers an applied-domain flavor over pure systems, choose AgriEvalKit (runner-up 2), which reuses much of the same evaluation methodology in a domain with strong social-good workshop fit.

## Caveats

- Several supporting market/salary figures come from recruiting-firm and vendor blogs (Taggd, Scaler, TekRecruiter, Futurense, and vendor “trends” posts) rather than primary labor statistics; treat specific salary bands and percentages as indicative, not audited. The WEF “500,000 roles” and Gartner “3× by 2027” figures are widely cited but are forecasts/estimates, and the Gartner figure is a projection (“at least three times more”), not a measured outcome.
- The novelty claim is as of August 2026 and the space is moving fast; concurrent preprints (e.g., arXiv 2608.09941, and vendor blog content describing similar pipelines) are closing in on adjacent territory, so early release matters.
- Some 2026-dated arXiv identifiers surfaced during research are very recent, single-author, or not yet peer-reviewed; verify each before citing as an established result.
- Free-tier GPU (Kaggle 30 hrs/week, Colab) is a supplement only; the design deliberately does not depend on sustained GPU access, satisfying the laptops-only constraint.