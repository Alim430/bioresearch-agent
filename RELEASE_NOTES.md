## BioResearch Agent v1.8.0

**Phase 3a: Cross-ancestry Mendelian Randomization (mock mode). 14 skills, 9 validation cases, 23 benchmark tasks.**

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
python bio-research-os/demos/demo_ld_reference.py \
    --n-snps 200 --n-blocks 10 --seed 42 \
    --output-dir outputs/ld-reference
python bio-research-os/demos/demo_gwas_harmonization.py \
    --n-snps 500 --seed 42 \
    --output-dir outputs/gwas-harmonization
python bio-research-os/demos/demo_ancestry_aware_mr.py \
    --n-snps 200 --n-instruments 40 --true-effect 0.30 --seed 42 \
    --output-dir outputs/ancestry-aware-mr
```

### What is new in v1.8.0

- **Three new skills** registered in `skills/registry.json` (11 → 14 active skills):
  - `bioresearch-ld-reference-management` — per-ancestry LD block simulation, greedy clumping (PLINK --clump style), LD score computation.
  - `bioresearch-gwas-harmonization` — allele alignment, strand flipping, effect-allele standardisation, palindromic SNP removal, GWAS-SSF schema.
  - `bioresearch-ancestry-aware-mr` — cross-ancestry IVW meta-analysis, CAUSE-like EM (correlated + uncorrelated pleiotropy), MRMix-like mixture model, portability assessment.
- **Three demo scripts** (self-contained, CPU-only, synthetic data with known ground-truth):
  - `bio-research-os/demos/demo_ld_reference.py` (567 lines) — 5 super-populations (AFR/AMR/EAS/SAS/EUR), LD matrix simulation, clumping, LD scores, cross-ancestry comparison.
  - `bio-research-os/demos/demo_gwas_harmonization.py` (847 lines) — cross-ancestry GWAS simulation, allele harmonization, strand resolution, AF difference QC, genome-wide signal extraction.
  - `bio-research-os/demos/demo_ancestry_aware_mr.py` (970 lines) — multi-ancestry MR simulation, per-ancestry IVW, cross-ancestry meta (FE+RE), CAUSE-like LRT, MRMix-like EM, portability metrics.
- **Validation Cases 8 & 9** registered in `eval/manifest.json` (7 → 9 cases): LD reference panel management (Case 8, grade C) and ancestry-aware MR pipeline (Case 9, grade C). Both use synthetic data with planted ground-truth to validate computation correctness.
- **Benchmark-Lite expanded to 23 tasks** — new Group H (Cross-Ancestry MR) with 2 tasks validating LD reference and ancestry-aware MR pipeline outputs. 23/23 passing.
- **Router updated** — 12 new keywords added to `causal` route for cross-ancestry MR intent classification (cross-ancestry, CAUSE, MRMix, pleiotropy, LD reference, GWAS harmonization, portability, etc.).
- **Framework version bumped to 1.8.0** in `skills/registry.json` and `eval/manifest.json`.

### v1.8.0 mock-mode results (seed=42)

**LD Reference Panel** (n_snps=100, n_blocks=5, 3 ancestries):
- EUR: 72 index SNPs (72.0% clumping ratio)
- AFR: 68 index SNPs (68.0%)
- EAS: 69 index SNPs (69.0%)

**Ancestry-Aware MR** (n_snps=100, n_instruments=20, true_effect=0.30):
- Per-ancestry IVW estimates: EUR=0.291, EAS=0.283, SAS=0.301, AFR=0.359, AMR=0.335
- Cross-ancestry meta (FE): β=0.296, p≈0; I²=30.6%, Q p=0.218
- CAUSE-like LRT: theta_h1 recovered; MRMix-like: pi_causal > 0

Evidence grade: **C** (synthetic data validates computation correctness; real deployment requires harmonized GWAS from IEU OpenGWAS / BBJ / FinnGen / TPMI).

### Phase 3a implementation notes

- **Mock-to-Live architecture**: All three pipelines run on synthetic data with known ground-truth. The MR math (IVW, CAUSE-like EM, MRMix-like mixture, cross-ancestry meta) is real — only the input data is simulated.
- **Live mode deployment**: Replace `simulate_multi_ancestry_mr` with harmonized GWAS from IEU OpenGWAS (EUR), BBJ (EAS), FinnGen (EUR), TPMI (SAS). Use 1000G LD panels for ancestry-specific LD reference. See SKILL.md files for deployment guides.
- **Honesty**: Every evidence package includes `data_type: "synthetic"`, `evidence_grade: "C"`, and `limitations` documenting that results validate computation, not etiology.

---

## BioResearch Agent v1.6.0

**Foundation model embeddings (scGPT / UCE / scFoundation). Mock-to-Live pipeline validation. 11 skills, 7 validation cases, 21 benchmark tasks.**

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
python bio-research-os/demos/demo_foundation_embeddings.py \
    --n-cells 1000 --n-genes 2000 --seed 42 \
    --output-dir outputs/foundation-embeddings
```

### What is new in v1.6.0

- **Foundation model embeddings skill** (`bioresearch-foundation-embeddings`) — 11th active skill, registered in `skills/registry.json`.
- **Mock-to-Live architecture** for scGPT (512-dim), UCE (1280-dim), scFoundation (512-dim):
  - Mock mode: simulated embeddings via cluster centroids + Gaussian noise + L2 normalization, matching each model's output dimensionality. Validates the full evaluation pipeline (silhouette, ARI, NMI, kNN overlap, robustness sweep).
  - Live mode: API stubs documented in each mock function's docstring — `scgpt.tasks.embed_data()` (PyPI, CPU), `AnndataProcessor` from UCE (GPU), `get_embedding.py` from scFoundation (GPU + gene alignment).
- **Custom metric implementations** — silhouette score, k-means++ clustering, adjusted Rand index (ARI), normalized mutual information (NMI) — all without sklearn dependency for core metrics.
- **Validation Case 7** registered in `eval/manifest.json`: synthetic single-cell data (1000 cells x 2000 genes, 5 cell types, 2 batches), evidence grade **B** (mock mode validates pipeline correctness).
- **Demo script**: `bio-research-os/demos/demo_foundation_embeddings.py` (951 lines) — self-contained, produces 7 output files (3 CSVs, 2 PNGs, 1 TXT report, 1 JSON evidence package).
- **SKILL.md**: `skills/biomedical/foundation-embeddings/SKILL.md` with live mode deployment instructions.
- **Benchmark-Lite expanded to 21 tasks** — new Group G (Foundation) validates mock pipeline output structure, metric ranges, and model spec dimensions. 21/21 passing.
- **Framework version bumped to 1.6.0** in `skills/registry.json` and `eval/manifest.json`.

### v1.6.0 mock-mode results (seed=42, n_cells=1000)

| Model | Silhouette | ARI | NMI |
|:---|:---|:---|:---|
| scGPT | 0.847 | 1.000 | 1.000 |
| UCE | 0.883 | 0.780 | 0.910 |
| scFoundation | 0.810 | 1.000 | 1.000 |

Cross-model kNN overlap: 0.09–0.10 (low overlap expected — different dimensionality and noise profiles simulate model-specific embedding geometries).

Evidence grade: **B** (mock mode validates pipeline; real model benchmarks require GPU + checkpoints).

### Documentation

- **v1.8 manuscript** (Chinese): `docs/joss/paper-v1.8-zh.md` — extends v1.6 manuscript with cross-ancestry MR skills (LD reference / GWAS harmonization / ancestry-aware MR), Cases 8–9, 23-task benchmark, 14-skill registry.
- **v1.8 manuscript** (English): `docs/joss/paper-v1.8-en.md` — English version of the v1.8 manuscript, combining v1.0 English paper positioning with full v1.8 technical content.

---

## BioResearch Agent v1.5.0

**Real-data causal-evidence chain. Six validation cases. Data governance guardrails.**

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
bioresearch doctor
python bio-research-os/eval/case_study_realdata_causal.py \
    --gwas-path  /path/to/AD_sumstats_Jansenetal_2019sept.txt.gz \
    --eqtl-dir   /path/to/GTEx_Analysis_v8_eQTL \
    --output-dir docs/case-study
```

### What is new in v1.5.0

- ✅ **Data governance policy** (`DATA_GOVERNANCE.md`) and hardened `.gitignore` distinguish public/summary data from controlled/individual-level data (MetaBrain, UKB-PPP, ADNI, deCODE are out of scope).
- ✅ **Validation Suite expanded to 6 cases**; Case 6 is registered in `bio-research-os/eval/manifest.json` with evidence grade **B**.
- ✅ **Causal-evidence chain on real public summary data** — Jansen 2019 AD GWAS + GTEx v8 brain eQTL for TREM2 / BIN1 / CLU / PICALM / APOE.
  - 5/5 genes matched to brain eQTL.
  - 4/5 genes showed strong colocalization (PP.H4 > 0.8).
  - **BIN1** replicated with significant Wald-ratio MR (β = 0.037, SE = 0.006, p = 9.0 × 10⁻¹⁰).
- ✅ **Honest Evidence Package** for Case 6 lists limitations: lead-eQTL-only TWAS proxy, no LD reference panel, single-SNP MR, non-diseased GTEx tissue.
- ✅ **Case 5 vs Case 6 comparison** documented in `docs/case-study/CE_Case5_vs_Case6_comparison.md`.
- ✅ **v1.5 manuscript** in Chinese: `docs/joss/paper-v1.5-zh.md`.
- ✅ **Benchmark-Lite: 20-task regression suite** (`tests/benchmark_lite.py`) — covers router (8), core state (3), all 6 engines (6), full pipeline (1), skills registry (1), manifest + governance (1). Runs without network or pytest. 20/20 passing.
- ✅ **Framework version bumped to 1.5.0** in `skills/registry.json` and `eval/manifest.json`.

### v1.5.0 evidence grades

| Grade | Cases | Meaning |
|:---|:---|:---|
| **B** | Case 1 (PD biomarker on GEO), Case 6 (AD causal evidence on real GWAS+eQTL summary) | Real public data / summary statistics |
| **C** | Cases 2, 4, 5 | Synthetic or methodology validation on real statistical engines |
| **B / C** | Case 3 | Real PubMed when reachable; offline corpus fallback |

### Roadmap update

- v1.5 Phase 1 is **fully complete**: Agent Router, Causal Evidence chain (real data), 10 skills, Benchmark-Lite (20 tasks), data governance, and version bump to 1.5.0.
- Next: integrate full eQTL weights (S-PrediXcan / FUSION) and LD reference panels (1000 Genomes) while staying within public-summary data boundaries.

---

## BioResearch Agent v1.1.0

**One framework. Executable workflows. Zero API keys.**

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
./skills/install.sh        # Installs framework + workflow skills
```

---

### What is it?

A **runnable, reproducible workflow framework** for biomedical research. Not a text generator. Not a chat wrapper. An actual pipeline that downloads public data, runs real statistics, and produces figures — wired for AI assistants to invoke through a standardized skill interface.

### Workflows, all included

| Workflow | One-liner | What you get |
|:---|:---|:---|
| **Literature** | `bioresearch run literature --query "microglia Alzheimer's disease"` | PubMed retrieval → knowledge graph → gap report |
| **Biomarker** | `bioresearch run biomarker --disease "Parkinson's disease"` | GEO analysis → DEG table → volcano plot |
| **Causal** | `bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"` | MR estimation (IVW) → scatter/funnel plots |
| **Case study** | `python bio-research-os/eval/case_study_pd.py` | End-to-end validated case with Evidence Package |

All run **without an LLM API key**. Public data + synthetic fallbacks.

### Why it's different

Most "AI for science" projects generate text summaries. This one **runs the actual analysis**:

- Downloads real GEO datasets (e.g., GSE7621, postmortem substantia nigra)
- Runs differential expression (t-test + Benjamini–Hochberg FDR)
- Performs Mendelian randomization (IVW + leave-one-out)
- Produces publication-quality figures

And it's **fully reproducible**: fixed seeds, deterministic outputs, and a per-case Evidence Package (provenance + benchmark + honest evidence grade).

### Honest evidence grading

Every validation case carries an evidence grade:

- **B — real public data**: GSE7621 Parkinson's biomarker discovery (real GEO), and the AD literature case (real PubMed queries when reachable).
- **C — synthetic / offline methodology**: the MR cases use a *real IVW engine* on synthetic GWAS with known ground truth, to validate the computation (not a real etiological claim). Offline literature mode falls back to a built-in corpus. Both clearly flag `next_validation` pointing to real GWAS (IGAP/GLGC) and real bibliographic APIs.

No case claims a result it does not have. See `bio-research-os/eval/README.md`.

### Agent Router v0

A deterministic, rule-based intent classifier (`bioresearch route "<intent>"`) maps free-text research requests to the right workflow — no LLM, no network, fully testable (10/10 unit tests). It *translates intents into executable workflows*; it does not perform autonomous discovery.

### Install as agent skills (Claude / Cursor / LangChain)

```bash
./skills/install.sh        # Auto-detects your agent client
```

After install, your AI agent can invoke these workflows directly:

> "Run a literature review on microglia in Alzheimer's disease"

The agent routes it to `bioresearch run literature` and returns structured outputs.

### Architecture

- **Reproducible workflow engine** (literature / biomarker / causal-inference / causal-evidence / case-study)
- **Multi-interface access**: CLI · Python SDK · API Contract / Tool Spec · Agent Skills
- **Validation Suite**: 9 cases with Evidence Packages (`bio-research-os/eval/`)
- **14 agent skills** in `skills/` (interface wrappers, not reasoning modules)

### Paper & preprint

An accompanying methods/software paper is **in preparation** (target: cs.SE primary + q-bio.QM/GN secondary on arXiv; this account requires a human endorser for all archives). Until endorsement is secured, the preprint will be posted to **bioRxiv** (free, DOI, biomedical audience), with JOSS as an alternative peer-reviewed venue. Links will be added here once they actually exist.

> No paper ID or preprint link is claimed here until it is real.

### What's new in v1.1.0 (since v1.0.0)

- ✅ Agent Router v0 (rule-based intent → workflow, 10/10 tests)
- ✅ Validation Suite expanded to 4 cases (PD real GEO, AD MR, AD literature, BMI→T2D MR)
- ✅ Skill set expanded to 9 active agent skills
- ✅ Benjamini–Hochberg FDR + auto log2-scale handling for real microarray data
- ✅ CLI `route` subcommand
- ✅ CI workflow configured (Python 3.9–3.12)
- ✅ Determinism (fixed seed-42; Evidence Packages pin provenance)

### v1.5 progress (completed in v1.5.0)

- ✅ **Causal-evidence chain implemented** — `demo_causal_evidence.py` (real coloc PP.H4 + TWAS z-score proxy + fine-mapping credible sets + Wald-ratio MR, numerically stable log-space) + **Case 5** in the Validation Suite (synthetic loci, ground-truth recovery: coloc 1.00 / TWAS 1.00 / fine-map 1.00; sweep TWAS 0.91). Honest grade **C** (methodology validation).
- ✅ **Skill set expanded to 10 active agent skills** (added `bioresearch-causal-evidence`).
- ✅ **Real-data integration completed**: Case 6 runs on Jansen 2019 AD GWAS + GTEx v8 brain eQTL for TREM2 / BIN1 / APOE / CLU / PICALM, achieving grade **B**.
- ✅ **Benchmark-Lite**: 20-task regression suite (`tests/benchmark_lite.py`), 20/20 passing.
- ✅ **Framework version bumped to 1.5.0** across registry and manifest.

### Roadmap (honest, near-term)

- **v1.5 Phase 1 — COMPLETE.** All four roadmap items delivered: Agent Router, Causal Evidence hardening (Case 6 real data), Skills expanded to 10, Benchmark-Lite (20 tasks).
- **Phase 2**: Foundation-model embeddings (scGPT / UCE / scFoundation) — deferred from Phase 1.
- **Phase 3**: Virtual Cell / multimodal / cross-ancestry MR, converging with AD-VCP.

### Get started in 30 seconds

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
bioresearch doctor
bioresearch run literature --query "microglia Alzheimer's disease"
```

See `README.md` for full documentation.
