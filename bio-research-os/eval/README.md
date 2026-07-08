# Biomedical Workflow Validation Suite

> An honest **validation suite** (not a marketing "benchmark") that runs the BioResearch Agent
> workflows against real public data and records a reproducible Evidence Package for each case.
> Every case proves the framework does real work on real data — no synthetic injection, no
> pre-known answers baked into the pipeline.

## Why a "Validation Suite" and not a "Benchmark"?

A benchmark implies a leaderboard and a single score to maximize. That framing invites
gaming and overclaiming. This suite instead records, per case:

1. **Known-entity recovery** — do established disease genes / pathways surface? (blind check)
2. **Pathway / mechanistic sanity** — do disease-relevant biology pathways enrich?
3. **Reproducibility** — commit hash, environment, and data `sha256` pinned in an Evidence
   Package, so any reviewer can re-run and get the same numbers.

Each case is graded on evidence, not on a vanity metric. Low recovery is reported honestly
(biology is sometimes subtle in bulk tissue) and interpreted, not hidden.

### Benchmark design (Case 1, Parkinson's / GSE7621)

* **Two known-gene tiers, reported separately** (honest about bulk-tissue power):
  * *Mendelian drivers* — `SNCA, LRRK2, PARK7, PINK1, PRKN, GBA`. Subtle expression
    shifts in bulk substantia nigra; typically **not** FDR-significant at n=25.
  * *Dopaminergic signature* — `TH, SLC6A3, SLC18A2, DDC, DRD2, MAOA, COMT`. The
    recoverable, dominant PD signal (dopaminergic-neuron loss). Reported as the primary
    recovery metric.
* **Pathway sanity** on a *nominal* DE set (`p<0.05` & `|log2FC|≥0.3`) in addition to the
  FDR set — field-standard when n is small and FDR is conservative. Expects dopamine /
  mitochondrial / oxidative / immune pathways to enrich.
* **Reproducibility** — commit hash, environment, and data `sha256` pinned in the Evidence
  Package.

## Cases

| Case | Disease / Question | Workflow(s) | Data | Status |
|------|--------------------|-------------|------|--------|
| 1 | Parkinson's biomarker discovery | biomarker (DEG → enrichment → ranking) | GSE7621 (GPL570, 25 samples) | ✅ implemented — `case_study_pd.py` |
| 2 | AD causal evidence (risk factor → AD) | causal-inference (MR) | GWAS summary stats (independent cohorts) | 🟡 planned |
| 3 | AD literature gap analysis | literature-analysis | PubMed / OpenAlex | 🟡 planned |
| 4 | Exposure → outcome MR exemplar | causal-inference (MR) | GWAS summary stats | 🟡 planned |

## Running Case 1 (Parkinson's / GSE7621)

```bash
python bio-research-os/eval/case_study_pd.py \
    --matrix-path /tmp/gse7621_matrix.txt.gz \
    --annot-path  /tmp/gpl570.annot.gz \
    --output-dir  docs/case-study
```

Outputs land in `docs/case-study/` (see `case_study_pd.py` header for the full list,
including `GSE7621_evidence_package.json`).

## Evidence Package schema

Each run emits a JSON Evidence Package:

```json
{
  "metadata":  { "case_study", "dataset", "platform", "date", "mode" },
  "provenance": { "git_commit", "python", "env", "matrix_sha256", "annot_sha256", "seed_policy" },
  "methods":   [ "download_geo", "parse_series_matrix", "probe_to_gene_map", ... ],
  "results":   { "n_samples", "n_genes", "n_significant_deg", ... },
  "benchmark": {
    "known_gene_recovery_mendelian_drivers": {...},
    "known_gene_recovery_dopaminergic_signature": {...},
    "pathway_sanity_nominal": {...}
  },
  "evidence_grade": "B (real public data; bulk microarray; single cohort)",
  "limitations": [ ... ],
  "next_validation": "..."
}
```

## Extending the suite

Add a new case by dropping a `case_study_*.py` in this directory that:
- downloads/loads real public data,
- calls the framework engine (no re-implemented statistics),
- emits a `Evidence Package` JSON with the schema above,
- registers itself in `manifest.json`.
