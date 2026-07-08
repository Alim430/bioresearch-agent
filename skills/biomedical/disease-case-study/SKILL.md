---
name: bioresearch-disease-case-study
description: Run a reproducible, real-public-data disease case study that composes the literature → biomarker → causal workflows end-to-end and emits a blind benchmark evaluation (known-gene recovery, pathway sanity, reproducibility hash). Use when the user wants to prove the framework on a real disease (e.g. Parkinson's GSE7621) or asks for a "case study", "validation run", or "benchmark" of the biomedical workflows.
---

# BioResearch Agent — Disease Case Study Skill

## Capability

A **workflow-composition + validation** skill. It runs a real, public GEO dataset through the
framework's analysis engine (differential expression → pathway enrichment → candidate ranking,
with optional literature and causal-inference stages) and produces a **blind benchmark
evaluation**:

- **Known-gene recovery** — how many established disease genes surface in the top-ranked
  candidates (e.g. SNCA / LRRK2 / PARK7 / PINK1 / PRKN / GBA for Parkinson's).
- **Pathway sanity** — whether disease-relevant pathways (dopamine / mitochondrial / oxidative /
  immune) are enriched.
- **Reproducibility** — commit hash, environment, and data `sha256` recorded in an Evidence
  Package.

Case Study 1 ships with the suite: **Parkinson's disease / GSE7621** (GPL570, 25 samples).
See `bio-research-os/eval/case_study_pd.py` and the Biomedical Workflow Validation Suite README.

## Run

```bash
python bio-research-os/eval/case_study_pd.py \
    --matrix-path /tmp/gse7621_matrix.txt.gz \
    --annot-path  /tmp/gpl570.annot.gz \
    --output-dir  docs/case-study
```

(If paths are omitted the runner downloads the real GSE7621 matrix + GPL570 annotation itself.)

## Outputs (in `docs/case-study/`)

- `GSE7621_deg.csv` — differential expression results
- `GSE7621_top_candidates.csv` — ranked biomarker candidates
- `GSE7621_pathway_enrichment.csv` — enriched KEGG / GO terms
- `GSE7621_volcano.png` — volcano plot
- `GSE7621_report.txt` — structured report incl. blind benchmark
- `GSE7621_evidence_package.json` — provenance + benchmark + limitations

## Note

This skill is a **composition & validation interface**. It adds no statistics of its own — every
number comes from the framework's workflow modules. It is the honest way to demonstrate the
framework works on real data (not synthetic injection). Requires no LLM key.
