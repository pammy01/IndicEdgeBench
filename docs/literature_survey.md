# IndicEdgeBench: Literature Survey

*Evaluation 1. All arXiv identifiers below were checked against the arXiv API on 27 Oct 2026; 2026 preprints are not yet peer-reviewed and are cited as such.*

## 1. The question

Small language models (0.5B to 8B parameters) are now practical on laptops and phones, but only after **post-training quantization** (FP16 to 8, 4 or 2 bits) and on **CPU runtimes** such as llama.cpp. Indian languages are exactly where compression is most likely to hurt: their scripts are non-Latin, they are under-represented in pre-training data, and tokenizers split them into many more tokens per word. Running models offline in Indian languages therefore raises two linked questions: how much quality is lost, and how much speed, memory and energy is gained? The literature answers each half separately and never both together.

## 2. Indic-language quality benchmarks

| Work | What it measures | Precision / efficiency |
|---|---|---|
| **MILU**, Verma et al., NAACL 2025 ([arXiv:2411.02538](https://arxiv.org/abs/2411.02538)) | ~85k culturally grounded MCQs in 11 Indic languages + English, 8 domains, 41 subjects; 45 LLMs evaluated, GPT-4o best at ~72% | Full precision only; no latency or memory |
| **IndicParam**, Maheshwari et al. ([arXiv:2512.00333](https://arxiv.org/abs/2512.00333)) | Low-resource Indic language benchmark | Full precision only |
| **IndicGenBench**, Singh et al., 2024 ([arXiv:2404.16816](https://arxiv.org/abs/2404.16816)) | Generation tasks (summarisation, translation, QA) in 29 Indic languages; reports tokenizer fertility | Full precision only |
| **IndicRAGSuite**, Prasanjith et al. ([arXiv:2506.01615](https://arxiv.org/abs/2506.01615)) | Retrieval/RAG datasets for Indian languages | No quantization study |
| **Hindi-BEIR**, Acharya et al. ([arXiv:2409.05401](https://arxiv.org/abs/2409.05401)) | Zero-shot Hindi retrieval | No quantization study |

**Gap:** these benchmarks are the quality substrate IndicEdgeBench reuses, but every one of them evaluates uncompressed models on server hardware.

## 3. Quantization methods and their multilingual cost

- **LLM.int8()** (Dettmers et al., [arXiv:2208.07339](https://arxiv.org/abs/2208.07339)), **GPTQ** (Frantar et al., [arXiv:2210.17323](https://arxiv.org/abs/2210.17323)) and **AWQ** (Lin et al., [arXiv:2306.00978](https://arxiv.org/abs/2306.00978)) established that weights can be stored in 8 or 4 bits with small *English* perplexity loss. llama.cpp's GGUF K-quants (Q8_0, Q4_K_M, Q2_K) are the de-facto format for CPU inference.
- **How Does Quantization Affect Multilingual LLMs?** (Marchisio et al., Findings of EMNLP 2024, [arXiv:2407.03211](https://arxiv.org/abs/2407.03211)): non-Latin scripts are hurt most, and automatic metrics **under-estimate** the damage. A 1.7% automatic drop in Japanese corresponded to a 16% drop in human evaluation, and math reasoning degraded fastest. The study used 8B to 103B models and did not measure efficiency.
- **The Uneven Impact of PTQ in Machine Translation** (Marie & Fujita, [arXiv:2508.20893](https://arxiv.org/abs/2508.20893)): quantization "substantially degrades" lower-resource languages, *especially Indic ones*, sometimes eliminating their ability to translate into English. It is limited to MT and gives no efficiency numbers.
- **The Multilingual Quantization Tax** (Soualhi, 2026 preprint, [arXiv:2608.09941](https://arxiv.org/abs/2608.09941)): reports structural collapse of edge SLMs in typologically distant languages. It measures accuracy only, across 8 mixed languages.
- **Which Quantization Should I Use?** (Kurt, 2026 preprint, [arXiv:2601.14277](https://arxiv.org/abs/2601.14277)): a unified llama.cpp quant-level comparison on Llama-3.1-8B. English only, but a useful methodological template.

## 4. On-device / edge LLM benchmarks

| Work | Measures | Languages |
|---|---|---|
| **PalmBench**, Li et al. ([arXiv:2410.05315](https://arxiv.org/abs/2410.05315)) | Compressed LLMs on mobile: quality, latency, memory, energy | English / general |
| **Systematic Evaluation of On-Device LLMs**, Song et al. ([arXiv:2505.15030](https://arxiv.org/abs/2505.15030)) | Quantization vs. performance vs. resources | English / general |
| **RooflineBench**, Bi et al., 2026 preprint ([arXiv:2602.11506](https://arxiv.org/abs/2602.11506)) | Roofline analysis of on-device inference | English |
| **LLM Inference at the Edge**, Tummalapalli et al., 2026 preprint ([arXiv:2603.23640](https://arxiv.org/abs/2603.23640)) | Mobile/NPU/GPU trade-offs under *sustained* load; thermal throttling dominates | English |

**Gap:** these benchmarks have the systems rigour IndicEdgeBench needs (repeated runs, thermal control, memory/energy logging), but none evaluates Indian languages.

## 5. Tokenization: the hidden latency tax

Decode cost scales with the number of *tokens* produced, not words. IndicGenBench reports Indic fertility (tokens per word) ranging from about 4 to 20. **BHARATI** (Kumaresan et al., 2026 preprint, [arXiv:2607.23319](https://arxiv.org/abs/2607.23319)) shows that a morphology-aware tokenizer reduces generation steps several-fold for Indian languages. The same tokens/s therefore delivers far fewer *words* per second in Tamil than in English. IndicEdgeBench reports **words/s** (tokens/s ÷ fertility) as a first-class metric for this reason.

## 6. Evaluation methodology

- **lm-evaluation-harness** (Biderman et al., [arXiv:2405.14782](https://arxiv.org/abs/2405.14782)): argues for log-likelihood scoring of MCQ options, fixed prompts, and reporting uncertainty. IndicEdgeBench follows these practices (next-token letter scoring, bootstrap CIs, pinned configs).
- **Flip rate:** the share of answers that change between FP16 and a quantized model. It exposes instability that an unchanged accuracy can hide, because quantization can fix and break different items in roughly equal numbers.
- **Motivation for small models:** *Small Language Models are the Future of Agentic AI* (Belcak et al., NVIDIA, [arXiv:2506.02153](https://arxiv.org/abs/2506.02153)).
- **Real-world need:** the AIEP agri-advisory report (Collis et al., [arXiv:2601.11537](https://arxiv.org/abs/2601.11537)) names latency, especially for voice, as a top deployment problem in rural India.

## 7. Positioning

| | Indic tasks | Quantization sweep | Measured CPU latency / memory / energy |
|---|:-:|:-:|:-:|
| MILU, IndicParam, IndicGenBench, IndicRAGSuite | ✅ | ❌ | ❌ |
| Marchisio et al. 2024 | partial (multilingual) | ✅ | ❌ |
| Marie & Fujita 2025 | ✅ (MT only) | ✅ | ❌ |
| Multilingual Quantization Tax 2026 | partial | ✅ | ❌ |
| PalmBench, Song et al., RooflineBench | ❌ | ✅ | ✅ |
| **IndicEdgeBench (this project)** | ✅ | ✅ | ✅ |

**Research gap:** no public benchmark jointly reports Indic-language task quality and measured on-device efficiency across quantization levels. IndicEdgeBench fills this gap with a per-language, per-task quality-vs-efficiency Pareto frontier.

## References

1. Verma et al. *MILU: A Multi-task Indic Language Understanding Benchmark.* NAACL 2025. arXiv:2411.02538
2. Maheshwari et al. *IndicParam: Benchmark to evaluate LLMs on low-resource Indic Languages.* arXiv:2512.00333
3. Singh et al. *IndicGenBench: A Multilingual Benchmark to Evaluate Generation Capabilities of LLMs on Indic Languages.* ACL 2024. arXiv:2404.16816
4. Prasanjith et al. *IndicRAGSuite: Large-Scale Datasets and a Benchmark for Indian Language RAG Systems.* arXiv:2506.01615
5. Acharya et al. *Benchmarking and Building Zero-Shot Hindi Retrieval Model with Hindi-BEIR and NLLB-E5.* arXiv:2409.05401
6. Dettmers et al. *LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale.* NeurIPS 2022. arXiv:2208.07339
7. Frantar et al. *GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers.* ICLR 2023. arXiv:2210.17323
8. Lin et al. *AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration.* MLSys 2024. arXiv:2306.00978
9. Marchisio et al. *How Does Quantization Affect Multilingual LLMs?* Findings of EMNLP 2024. arXiv:2407.03211
10. Marie & Fujita. *The Uneven Impact of Post-Training Quantization in Machine Translation.* arXiv:2508.20893
11. Soualhi. *The Multilingual Quantization Tax: Structural Collapse and Typological Fragility in Edge SLMs.* 2026 preprint. arXiv:2608.09941
12. Kurt. *Which Quantization Should I Use? A Unified Evaluation of llama.cpp Quantization on Llama-3.1-8B-Instruct.* 2026 preprint. arXiv:2601.14277
13. Li et al. *PalmBench: A Comprehensive Benchmark of Compressed Large Language Models on Mobile Platforms.* arXiv:2410.05315
14. Song et al. *A Systematic Evaluation of On-Device LLMs: Quantization, Performance, and Resources.* arXiv:2505.15030
15. Bi et al. *RooflineBench: A Benchmarking Framework for On-Device LLMs via Roofline Analysis.* 2026 preprint. arXiv:2602.11506
16. Tummalapalli et al. *LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load.* 2026 preprint. arXiv:2603.23640
17. Kumaresan et al. *BHARATI: Morphology-Aware Tokenizers for Classical Indian Languages with Subword Fertility Analysis.* 2026 preprint. arXiv:2607.23319
18. Biderman et al. *Lessons from the Trenches on Reproducible Evaluation of Language Models.* arXiv:2405.14782
19. Belcak et al. *Small Language Models are the Future of Agentic AI.* arXiv:2506.02153
20. Collis et al. *Building AI-based advisory services for smallholder farmers: Technical learnings from the AIEP Initiative.* arXiv:2601.11537
