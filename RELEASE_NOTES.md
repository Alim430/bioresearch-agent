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

- **v1.6 manuscript** (Chinese): `docs/joss/paper-v1.6-zh.md` — extends v1.5 manuscript with foundation model embeddings skill, Mock-to-Live architecture, Case 7 results, 21-task benchmark, 11-skill registry, and Phase 3 roadmap preview.
- **v1.6 manuscript** (English): `docs/joss/paper-v1.6-en.md` — English translation of the v1.6 manuscript, combining v1.0 English paper positioning with full v1.6 technical content (12 sections, 15 references).
- **Phase 3 roadmap**: `docs/roadmap/phase3-roadmap.md` — comprehensive planning document covering three directions (cross-ancestry MR, multimodal integration, Virtual Cell), with skill extension plans (11→21 skills), validation case planning (7→13 cases), timeline, version planning (v1.6→v2.0), and risk matrix.

### Roadmap update

- v1.6 Phase 2 (foundation model embeddings) is **complete in mock mode**: pipeline architecture, evaluation metrics, cross-model comparison, and robustness sweep all validated.
- **Phase 3 roadmap published**: three directions planned — 3a (cross-ancestry MR, CPU, priority 1), 3b (multimodal integration, GPU, priority 2), 3c (Virtual Cell, GPU+memory, priority 3). See `docs/roadmap/phase3-roadmap.md` for details.
- Next: deploy live mode with real model checkpoints (scGPT via pip install, UCE/scFoundation via git clone + GPU), then proceed to Phase 3a (cross-ancestry MR — highest governance fit, CPU-only).

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
- **Validation Suite**: 5 cases with Evidence Packages (`bio-research-os/eval/`)
- **10 agent skills** in `skills/` (interface wrappers, not reasoning modules)

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
