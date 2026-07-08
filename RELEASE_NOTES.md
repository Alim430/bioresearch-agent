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

- **Reproducible workflow engine** (literature / biomarker / causal-inference / case-study)
- **Multi-interface access**: CLI · Python SDK · API Contract / Tool Spec · Agent Skills
- **Validation Suite**: 4 cases with Evidence Packages (`bio-research-os/eval/`)
- **9 agent skills** in `skills/` (interface wrappers, not reasoning modules)

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

### Roadmap (honest, near-term)

- **v1.5 (Phase 1 target):** complete the causal-evidence chain (GWAS → eQTL → TWAS → coloc → MR → fine-mapping), expand to 10 skills, grow the benchmark to ~20 tasks.

### Get started in 30 seconds

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
bioresearch doctor
bioresearch run literature --query "microglia Alzheimer's disease"
```

See `README.md` for full documentation.
