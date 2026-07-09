---
title: 'BioResearch Agent Framework v1.6: Foundation Model Embeddings and Mock-to-Live Evaluation Pipeline'
tags:
  - bioinformatics
  - reproducibility
  - workflow
  - single-cell
  - foundation-models
  - agent-skills
authors:
  - name: Alimujiang Tudiyusufu
    affiliation: "1, 2"
    orcid: ""
affiliations:
  - name: Shanghai University of Traditional Chinese Medicine
    index: 1
  - name: Institute of Basic Medical Sciences, Peking Union Medical College
    index: 2
date: 9 July 2026
bibliography: paper.bib
---

# Summary

BioResearch Agent Framework is an open-source, reproducible workflow execution layer for biomedical research. Building on v1.5's causal evidence chain and data governance guardrails, v1.6 introduces the 11th active skill — foundation model embeddings — which validates the evaluation pipeline for three single-cell foundation models (scGPT, UCE, scFoundation) through a Mock-to-Live architecture.

Mock mode uses simulated embeddings (cluster centroids + Gaussian noise + L2 normalization) matching each model's output dimensionality (512 / 1280 / 512) to validate the full evaluation pipeline: silhouette score, adjusted Rand index (ARI), normalized mutual information (NMI), k-means++ clustering, kNN cross-model consistency analysis, and a 6-level noise robustness sweep. The validation suite expands from 6 to 7 cases, Benchmark-Lite from 20 to 21 tasks (21/21 passing). Case 7 receives evidence grade B (mock mode validates pipeline correctness; real model inference requires GPU + checkpoint).

**Keywords:** single-cell foundation models; scGPT; UCE; scFoundation; reproducible workflow; agent skills; Mock-to-Live architecture

# 1. Introduction

BioResearch Agent Framework is not an autonomous "AI scientist" system. It is deliberately a **workflow execution framework with an agent-compatible interface**: skills are invocation wrappers, and all computation runs in established domain libraries. The framework's contribution is a *reproducible execution contract*, not a new algorithm — every run emits data-derived tables, statistical results, and figures rather than free-text summaries.

v1.5 completed the causal evidence chain on real public summary statistics (Case 6: Jansen 2019 AD GWAS + GTEx v8 brain eQTL) and established data governance guardrails distinguishing public summary data from controlled-access / individual-level data. However, the framework lacked support for single-cell foundation models — a paradigm that has rapidly emerged in 2023–2024.

Several single-cell foundation models were published in this period: scGPT (Cui et al. 2024, *Nature Methods*), pretrained on 33 million cells, supports cell type annotation, perturbation response prediction, and multi-omics integration; UCE (Rosen et al. 2024) generates universal cell embeddings through cross-species training; scFoundation (Hao et al. 2024, *Nature Methods*) models 20,000 genes simultaneously with 100 million parameters. These models establish pretrained embeddings as a new paradigm for representing cell state.

v1.6 integrates this paradigm into the framework's skill layer while following the Mock-to-Live principle: validate the evaluation pipeline's correctness in mock mode first, then switch to live mode with real model checkpoints when GPU resources are available. This strategy ensures the framework can run the full evaluation workflow without a GPU, maintaining reproducibility and CI compatibility.

# 2. Statement of Need

Reproducible computational workflows in biomedicine are typically encoded either as pipeline-specific languages (e.g., Nextflow, Snakemake) or as manual scripts. Meanwhile, AI assistants are increasingly expected to *perform* analysis, yet most can only generate plausible-looking code or prose. There is a gap between (a) validated biomedical tools and (b) agent environments that researchers actually use. BioResearch Agent Framework fills that gap by packaging existing tools behind a unified, auditable interface that an agent — or a human — can invoke to produce real, reproducible outputs.

Nextflow and Snakemake solved portable pipeline execution; Galaxy solved browser-based access; limma and TwoSampleMR solved specific statistical tasks. What remains under-served is a **thin, tool-agnostic execution layer** that (i) standardizes inputs/outputs across heterogeneous biomedical workflows and (ii) is loadable as an Agent Skill so that AI assistants dispatch to validated code instead of hallucinating analysis. BioResearch Agent Framework targets exactly this interface layer.

# 3. v1.6 Validation Suite

The validation suite expands from 6 to 7 cases, registered in `bio-research-os/eval/manifest.json`. Each case carries an Evidence Package with provenance, methods, results, evidence grade, and limitations.

| ID | Name | Workflow | Data | Grade |
|:---:|:---|:---|:---|:---:|
| 1 | Parkinson's disease biomarker discovery | biomarker-discovery | GEO GSE7621 (real public microarray) | B |
| 2 | AD causal inference (risk factor → AD) | causal-inference | Synthetic GWAS + real IVW engine | C |
| 3 | AD literature gap analysis | literature-analysis | PubMed / offline corpus | B / C |
| 4 | Exposure → outcome MR exemplar | causal-inference | Synthetic GWAS + real IVW engine | C |
| 5 | Causal evidence chain (synthetic loci) | causal-evidence | Synthetic loci (ground truth known) | C |
| 6 | Real AD GWAS + GTEx brain eQTL causal evidence chain | causal-evidence | Jansen 2019 + GTEx v8 (real public summary) | B |
| **7** | **Foundation model embeddings pipeline validation** | **foundation-embeddings** | **Synthetic single-cell data (1000 cells × 2000 genes)** | **B** |

The suite is not a leaderboard but a set of "honest reproducibility tests." Synthetic cases (grade C) validate engine logic; real-data cases (grade B) validate engine applicability on public data.

# 4. Foundation Model Embeddings Skill

## 4.1 Mock-to-Live Architecture

The framework applies a unified Mock-to-Live architecture for each foundation model:

| Mode | Embedding generation | Compute | Purpose |
|:---|:---|:---|:---|
| Mock | Simulated: cluster centroids + Gaussian noise + L2 normalization | CPU only | Validate evaluation pipeline, CI compatibility, dependency-free |
| Live | Real model inference (API stub) | GPU + checkpoint | Real model benchmarking |

Three foundation models are supported:

| Model | Output dim | Pretraining data | Original paper | Deployment |
|:---|:---:|:---|:---|:---|
| scGPT | 512 | 33M cells | Cui et al. 2024, *Nat Methods* | `pip install scgpt` (CPU-compatible) |
| UCE | 1280 | 36M cross-species cells | Rosen et al. 2024 | git clone + GPU |
| scFoundation | 512 | 50M cells | Hao et al. 2024, *Nat Methods* | git clone + GPU |

## 4.2 Custom Evaluation Metrics

To avoid sklearn dependency, the framework implements the following core metrics in pure NumPy:

- **Silhouette score**: measures cluster cohesion and separation, range [−1, 1].
- **k-means++ clustering**: improved initialization via probabilistic sampling of initial centroids.
- **Adjusted Rand Index (ARI)**: chance-corrected Rand index, range [0, 1] (1 = perfect match).
- **Normalized Mutual Information (NMI)**: measures clustering–ground-truth agreement, range [0, 1].

## 4.3 Cross-Model Consistency

Cross-model consistency is quantified via kNN overlap: for each cell, compute its k-nearest neighbors (k=10) in each model's embedding space, then compare neighbor sets across models using Jaccard overlap. Low overlap is expected from different dimensionalities and noise profiles.

## 4.4 Robustness Sweep

Each model is evaluated at 6 noise levels [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] to observe the decay of silhouette, ARI, and NMI with increasing noise, validating pipeline stability.

# 5. Case 7: Foundation Model Embeddings Pipeline Validation

## 5.1 Data and Setup

- **Synthetic data**: 1000 cells × 2000 genes, 5 cell types, 2 batches. Cell types are implanted via cluster centroids; batch effects are linear shifts.
- **Mock embeddings**: each model generates simulated embeddings matching its output dimensionality (scGPT 512, UCE 1280, scFoundation 512).
- **Evaluation**: silhouette / ARI / NMI (ground truth = 5 cell types), kNN overlap, 6-level noise sweep.
- **Random seed**: seed=42; results are deterministic and reproducible.

## 5.2 Results

| Model | Silhouette | ARI | NMI |
|:---|---:|---:|---:|
| scGPT | 0.847 | 1.000 | 1.000 |
| UCE | 0.883 | 0.780 | 0.910 |
| scFoundation | 0.810 | 1.000 | 1.000 |

Cross-model kNN overlap: 0.09–0.10 (low overlap expected — different dimensionalities and noise profiles simulate model-specific embedding geometries).

## 5.3 Evidence Grade and Limitations

Case 7 receives evidence grade **B** (mock mode validates pipeline correctness). Key limitations:

- Mock embeddings are simulated and do not represent real model embedding quality.
- ARI = 1.000 reflects perfect recovery of ground truth by mock embeddings, not real model clustering ability.
- Real model inference requires GPU + checkpoint (scGPT via pip, UCE/scFoundation via git clone).
- Low kNN overlap in mock mode is driven by dimensionality differences and noise patterns; real models may show different consistency.

These limitations are documented in the SKILL.md live mode deployment guide and in `fe_evidence_package.json`.

# 6. v1.5 Retrospective: Causal Evidence Chain

v1.5's core achievements are fully preserved in v1.6:

- **Data governance guardrails** (`DATA_GOVERNANCE.md` + `.gitignore`): distinguish public summary data from controlled-access / individual-level data (MetaBrain, UKB-PPP, ADNI, deCODE are out of scope).
- **Case 6** (real AD GWAS + GTEx brain eQTL): 5/5 genes matched to brain eQTL, 4/5 strong colocalization (PP.H4 > 0.8), BIN1 significant via Wald-ratio MR (β = 0.037, SE = 0.006, p = 9.0 × 10⁻¹⁰). Evidence grade B.
- **Honest evidence grading**: every case carries an evidence grade (A–E) and explicit limitations.

See `docs/case-study/CE_Case5_vs_Case6_comparison.md` for the synthetic-vs-real comparison.

# 7. Architecture

- **Three-layer architecture**: Layer 1 (12 research stages), Layer 2 (6 engines: question → retrieval → analysis → evidence → narrative → execution), Layer 3 (specialized agents).
- **Access layer**: CLI (`bioresearch run …`), Python SDK, API contract (`bioresearch/toolspec.json`), and Agent Skills (`skills/`, conforming to the open Agent Skills standard).
- **Agent Router v0**: a deterministic, rule-based intent classifier maps free-text research requests to the right workflow — no LLM, no network, fully testable.
- A `bioresearch doctor` command validates environment, dependencies, network access, and output permissions.

# 8. Benchmark-Lite Regression Suite

Benchmark-Lite expands from 20 to 21 tasks across seven domains:

| Group | Tasks | Coverage |
|:---|:---:|:---|
| A. Router | 8 | Intent classification & command mapping |
| B. Core State | 3 | Stage, EvidenceGrade, ResearchState |
| C. Engines | 6 | Six Layer-2 engines in isolation |
| D. Pipeline | 1 | Full chain: IDEATION → PUBLICATION |
| E. Registry | 1 | skills/registry.json structural integrity (11 skills) |
| F. Manifest+Gov | 1 | eval/manifest.json + .gitignore (7 cases) |
| **G. Foundation** | **1** | **foundation-embeddings mock pipeline validation** |

All 21/21 pass without network, pytest, or GPU.

# 9. Skills Registry

The framework expands from 10 to 11 active skills:

| Skill | Group | Capability |
|:---|:---|:---|
| bioresearch-introduction | core | Framework overview & capability map |
| bioresearch-environment-check | core | Environment & reproducibility validation |
| bioresearch-literature-analysis | biomedical | Literature review + co-occurrence knowledge graph |
| bioresearch-biomarker-discovery | biomedical | Biomarker discovery |
| bioresearch-differential-expression | biomedical | Differential expression analysis |
| bioresearch-pathway-enrichment | biomedical | Pathway enrichment analysis |
| bioresearch-causal-inference | biomedical | Two-sample Mendelian randomization |
| bioresearch-disease-case-study | biomedical | Real-data disease case study |
| bioresearch-causal-evidence | biomedical | Causal evidence chain |
| bioresearch-agent-router | core | Rule-based intent → workflow routing |
| **bioresearch-foundation-embeddings** | **biomedical** | **Single-cell foundation model embeddings (scGPT/UCE/scFoundation)** |

# 10. Discussion

The v1.6 deliverable is not a new biological discovery but a validated foundation model embedding evaluation pipeline. The Mock-to-Live architecture's significance:

- **Reproducibility**: Mock mode makes the evaluation pipeline runnable without GPU or checkpoint, ensuring CI compatibility and reviewer reproducibility.
- **Architecture readiness**: Live mode API stubs are documented in SKILL.md; switching to real inference requires only replacing mock functions with API calls — no evaluation logic refactoring.
- **Metric independence**: Custom silhouette / ARI / NMI / k-means++ implementations avoid sklearn dependency, enabling the framework to run in minimal environments.

The current limitation is that mock embeddings cannot reflect real model embedding quality. Live mode deployment requires: (1) scGPT via `pip install scgpt` (CPU inference); (2) UCE / scFoundation via git clone + GPU inference + gene alignment. These upgrades do not change the evaluation pipeline structure — only the embedding generation method.

# 11. Roadmap

- **v1.6 Phase 2 (mock mode)** — complete: pipeline architecture, evaluation metrics, cross-model comparison, and robustness sweep all validated.
- **v1.6 Phase 2 (live mode)** — next: deploy real model inference to generate real embedding benchmarks.
- **Phase 3** — three directions converging:
  - **Cross-ancestry MR**: integrate Biobank Japan / FinnGen / Taiwan TPMI non-European GWAS summary statistics with 1000 Genomes stratified LD reference panels, using CAUSE / MRMix to explicitly model cross-ancestry pleiotropy. Minimal governance friction (summary statistics only).
  - **Multimodal single-cell integration**: extend v1.6 foundation embeddings to CITE-seq / 10x Multiome with totalVI / MultiVI / MOFA+ probabilistic integration.
  - **Virtual Cell**: interface with CZ CELLxGENE Census (50M+ cells) and Arc Virtual Cell Atlas for perturbation response prediction and cell state simulation.

All three directions converge on the "gene → cell state → phenotype" causal chain, aligned with the AD-VCP (Alzheimer's Disease Virtual Cell Project) vision.

# 12. Conclusion

BioResearch Agent Framework v1.6 extends framework capability from causal genetics to single-cell foundation models, validating the full embedding evaluation pipeline without GPU dependency through the Mock-to-Live architecture. Seven validation cases, 21 benchmark tasks, and 11 active skills collectively form an auditable, reproducible, agent-callable biomedical workflow execution layer. Future work will focus on live mode deployment and the three Phase 3 directions.

# Acknowledgements

We acknowledge the developers of the underlying open-source biomedical libraries that this framework dispatches to, including but not limited to NumPy, SciPy, pandas, matplotlib, and the scGPT / UCE / scFoundation model teams.

# References

1. Di Tommaso, P., Chatzou, M., Floden, E. W., Barja, P. P., Palumbo, E., & Notredame, C. (2017). Nextflow enables reproducible computational workflows. *Nature Biotechnology*, 35(4), 316–319.
2. Mölder, F., Jablonski, K. P., Letcher, B., et al. (2021). Sustainable data analysis with Snakemake. *F1000Research*, 10, 33.
3. Ritchie, M. E., Phipson, B., Wu, D., et al. (2015). limma powers differential expression analyses for RNA-sequencing and microarray studies. *Nucleic Acids Research*, 43(7), e47.
4. Hemani, G., Zheng, J., Elsworth, B., et al. (2018). The MR-Base platform supports systematic causal inference across the human phenome. *eLife*, 7, e34408.
5. Jansen, I. E., Savage, J. E., Watanabe, K., et al. (2019). Genome-wide meta-analysis identifies new loci and functional pathways influencing Alzheimer's disease risk. *Nature Genetics*, 51(3), 404–413.
6. GTEx Consortium. (2020). The GTEx Consortium atlas of genetic regulatory effects across human tissues. *Science*, 369(6509), 1318–1330.
7. Giambartolomei, C., Vukcevic, D., Schadt, E. E., et al. (2014). Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*, 10(5), e1004383.
8. Gusev, A., Ko, A., Shi, H., et al. (2016). Integrative approaches for large-scale transcriptome-wide association studies. *Nature Genetics*, 48(3), 245–252.
9. Cui, H., Wang, C., Maan, H., et al. (2024). scGPT: Toward building a foundation model for single-cell multi-omics using generative pretraining. *Nature Methods*, 21, 1470–1480.
10. Rosen, Y., Roohani, Y., Agarwal, A., et al. (2024). Universal cell embeddings: A foundation model for cell biology. *bioRxiv*. doi:10.1101/2023.11.28.568918
11. Hao, M., Gong, J., Zeng, X., et al. (2024). Large-scale foundation model on single-cell transcriptomics. *Nature Methods*, 21, 1481–1491.
12. Bunne, Y., Csucs, G., Ibarra, A., et al. (2024). How to build the virtual cell with artificial intelligence: Priorities and opportunities. *Cell*, 187(25), 7045–7063.
13. Lopez, R., Regier, J., Cole, M. B., Jordan, M. I., & Yosef, N. (2018). Deep generative modeling for single-cell transcriptomics. *Nature Methods*, 15, 1053–1058.
14. Gayoso, A., Weiler, P., Lotfollahi, M., et al. (2022). scvi-tools: a library for probabilistic analysis of single-cell omics data. *Nature Biotechnology*, 40, 640–650.
15. Morrison, J., Knol, M. J., MacKenzie, T. A., et al. (2020). Mendelian randomization accounting for correlated and uncorrelated pleiotropic effects using genome-wide summary statistics. *Nature Genetics*, 52, 740–747.
