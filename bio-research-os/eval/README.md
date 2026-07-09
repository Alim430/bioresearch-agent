# Biomedical Workflow Validation Suite

> An honest **validation suite** (not a marketing "benchmark") that runs the BioResearch Agent
> workflows and records a reproducible Evidence Package for each case.
>
> - **Case 1** runs on **real public data** (GEO:GSE7621, postmortem substantia nigra).
> - **Cases 2 & 4** are **methodology validations** on synthetic-but-ground-truth GWAS. They validate the
>   MR *engine's computation* (sign / magnitude-within-CI / significance recovery), not a real etiological
>   claim, and are graded **C** with an explicit `next_validation` pointing to real GWAS.
> - **Case 3** uses **real PubMed** when reachable (graded **B**) with a built-in corpus fallback for offline
>   reproducibility (graded **C**). It validates the literature-analysis *pipeline* (entity extraction →
>   co-occurrence graph → gap detection → outline).
> - **Case 5** is a **methodology validation** of the causal-evidence *chain* (GWAS → eQTL →
>   colocalization → TWAS → fine-mapping → MR) on synthetic loci with ground-truth labels. It validates
>   the engine's computation (coloc `PP.H4` recovery, TWAS significance, credible-set containment of the
>   true causal SNP, MR consistency), not a real etiological claim, and is graded **C** with `next_validation`
>   pointing to real AD GWAS + eQTL (IGAP + MetaBrain/GTEx).
>
> No synthetic numbers are injected into a "real" pipeline, and no pre-known answers are baked
> in. Every case reports its evidence grade and limitations honestly.

## Why a "Validation Suite" and not a "Benchmark"?

A benchmark implies a leaderboard and a single score to maximize. That framing invites
gaming and overclaiming. This suite instead records, per case:

1. **Known-entity recovery** (Case 1, real data) — do established disease genes / pathways surface? (blind check)
2. **Ground-truth recovery** (Cases 2 & 4, synthetic GWAS) — given data generated from a *known*
   causal effect, does the IVW estimator recover the right **sign**, **magnitude** (within CI),
   and **significance**? A falsifiable engine-correctness test.
3. **Pipeline sanity** (Case 3, offline) — does the literature pipeline produce a non-empty
   summary, a non-trivial co-occurrence graph, identified gaps, and a review outline?
4. **Reproducibility** — commit hash, environment, and (where real) data `sha256` pinned in an
   Evidence Package, so any reviewer can re-run and get the same numbers.

Each case is graded on evidence, not on a vanity metric: **A/B** = real public data;
**C** = synthetic/offline methodology validation. Low recovery is reported honestly
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
| 1 | Parkinson's biomarker discovery | biomarker (DEG → enrichment → ranking) | GSE7621 (GPL570, 25 samples) — **real** | ✅ implemented (grade B) — `case_study_pd.py` |
| 2 | AD causal evidence (educational attainment → AD) | causal-inference (MR) | **synthetic** GWAS, ground-truth known | ✅ implemented (grade C) — `case_study_ad_mr.py` |
| 3 | AD literature gap analysis | literature-analysis | **real PubMed** when reachable (grade B) / **offline** built-in corpus fallback (grade C) | ✅ implemented — `case_study_ad_literature.py` |
| 4 | Exposure → outcome MR exemplar (BMI → T2D) | causal-inference (MR) | **synthetic** GWAS, ground-truth known | ✅ implemented (grade C) — `case_study_mr_exemplar.py` |
| 5 | Causal evidence chain (GWAS→eQTL→coloc→TWAS→fine-map→MR) | causal-evidence | **synthetic** loci, ground-truth labels | ✅ implemented (grade C) — `case_study_causal_evidence.py` |
| 6 | Causal evidence chain on real AD GWAS + GTEx brain eQTL | causal-evidence | **real** public summary-level data (Jansen 2019 + GTEx v8 brain) | ✅ implemented (grade B) — `case_study_realdata_causal.py` |

## Running Case 1 (Parkinson's / GSE7621)

```bash
python bio-research-os/eval/case_study_pd.py \
    --matrix-path downloads/gse7621_matrix.txt.gz \
    --annot-path  downloads/gpl570.annot.gz \
    --output-dir  docs/case-study
```

Outputs land in `docs/case-study/` (see `case_study_pd.py` header for the full list,
including `GSE7621_evidence_package.json`).

## Running Cases 2–4 (methodology validation)

All three wrap the real framework engines (`demo_causal_inference.py`,
`demo_literature_review.py`). They need **no network** and use a fixed seed, so they are
fully reproducible offline.

```bash
# Case 4 — MR exemplar (BMI -> Type 2 Diabetes), synthetic GWAS
python bio-research-os/eval/case_study_mr_exemplar.py --output-dir docs/case-study

# Case 2 — AD MR methodology (educational attainment -> AD), synthetic GWAS
python bio-research-os/eval/case_study_ad_mr.py --output-dir docs/case-study

# Case 3 — AD literature gap (real PubMed when reachable; built-in corpus fallback offline)
python bio-research-os/eval/case_study_ad_literature.py --output-dir docs/case-study

# Case 5 — causal-evidence chain (GWAS -> eQTL -> coloc -> TWAS -> fine-map -> MR), synthetic loci
python bio-research-os/eval/case_study_causal_evidence.py --output-dir docs/case-study
```

## Running Case 6 (real AD GWAS + GTEx brain eQTL summary)

Case 6 runs the same causal-evidence engine as Case 5, but on **real public summary-level**
data. It requires two user-local datasets (never committed to the repo):

* AD GWAS summary: Jansen et al. 2019 (`AD_sumstats_Jansenetal_2019sept.txt.gz`)
* GTEx v8 brain eQTL directory (`GTEx_Analysis_v8_eQTL/`)

Paths default to `$BIORESEARCH_PUBLIC_DATA/raw/...` (set that env var to your local
raw-data root); override explicitly with `--gwas-path` and `--eqtl-dir`. Only summary
statistics are used; individual-level data (MetaBrain, UKB-PPP, ADNI, deCODE) are out of
scope per `DATA_GOVERNANCE.md`.

```bash
export BIORESEARCH_PUBLIC_DATA=/path/to/your/local/raw-data   # contains raw/gwas/..., raw/eqtl/...
python bio-research-os/eval/case_study_realdata_causal.py \
    --gwas-path  $BIORESEARCH_PUBLIC_DATA/raw/gwas/JansenIE_2019/AD_sumstats_Jansenetal_2019sept.txt.gz \
    --eqtl-dir   $BIORESEARCH_PUBLIC_DATA/raw/eqtl/gtex/GTEx_Analysis_v8_eQTL \
    --output-dir docs/case-study
```

This emits `CE_real_evidence_package.json` (grade **B**) and figures under
`docs/case-study/CE_real_*`.

Each emits an Evidence Package JSON (`*_evidence_package.json`) with `evidence_grade: "C"` (Cases 2–5)
or `"B"` (Cases 1 & 6) and explicit limitations / `next_validation`. The MR cases include a
ground-truth recovery sweep CSV (`*_sweep.csv`); the literature case includes a
pipeline-sanity check in its Evidence Package.

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
