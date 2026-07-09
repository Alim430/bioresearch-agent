---
name: bioresearch-ancestry-aware-mr
description: Run cross-ancestry Mendelian randomization with correlated-pleiotropy modeling (CAUSE-like) and mixture-model pleiotropy detection (MRMix-like), plus per-ancestry IVW, cross-ancestry meta-analysis (FE/RE), and portability assessment. Use when the user needs to test whether a causal effect estimated in one ancestry transfers to others, or to distinguish true causation from correlated horizontal pleiotropy. Mock mode validates the MR + pleiotropy pipeline; live mode would use BBJ/FinnGen/TPMI/UKB summary statistics.
---

# BioResearch Agent — Ancestry-Aware MR Skill

## Capability

Runs cross-ancestry Mendelian randomization with pleiotropy-aware methods:

1. **Per-ancestry IVW** — inverse-variance-weighted MR per ancestry with Cochran's Q heterogeneity
   test, producing ancestry-specific causal effect estimates and confidence intervals.
2. **Cross-ancestry meta-analysis** — fixed-effects (FE) and random-effects (RE, DerSimonian-Laird)
   meta-analysis across ancestries, with Cochran's Q and I² statistics to quantify cross-ancestry
   heterogeneity.
3. **CAUSE-like model** — (Morrison et al. 2020) EM algorithm modeling both correlated and
   uncorrelated horizontal pleiotropy. Tests H0 (no causal effect, pleiotropy free to vary) vs
   H1 (causal effect + pleiotropy) via likelihood-ratio test. Distinguishes true causation from
   correlated pleiotropy — the key confound in standard MR.
4. **MRMix-like model** — (Wang et al. 2020) three-component mixture model (causal / pleiotropic /
   null) via EM, estimating the proportion of pleiotropic instruments and adjusting the causal
   estimate accordingly.
5. **Portability assessment** — evaluates whether the causal effect estimated in a reference ancestry
   (e.g., EUR) transfers to others: direction consistency, significance consistency, heterogeneity
   (I²), EUR-centric bias, and a composite transferability score (0–1).

Returns per-ancestry MR + meta-analysis + CAUSE/MRMix + portability report, not a definitive causal claim.

## Run

```bash
bioresearch run ancestry-aware-mr --n-snps 200 --n-instruments 40 --true-effect 0.30 --seed 42 --output-dir outputs/ancestry-mr
```

## Outputs (in `--output-dir`)

- `amr_per_ancestry_results.csv` — per-ancestry IVW results (ancestry, beta, se, CI, p, Q, p_het)
- `amr_cross_ancestry_meta.csv` — FE + RE meta-analysis (method, beta, se, CI, p, Q, I², tau²)
- `amr_cause_results.csv` — CAUSE-like model per ancestry (theta, eta, sigma, LRT_stat, p_value)
- `amr_mrmix_results.csv` — MRMix-like model per ancestry (theta, pi_causal, pi_pleiotropic, pi_null)
- `amr_portability.csv` — portability assessment (direction_consistency, I², transferability_score)
- `amr_forest_plot.png` — forest plot of per-ancestry + meta-analysis causal estimates
- `amr_evidence_package.json` — reproducible Evidence Package (provenance + parameters + grade)

## Note

This skill dispatches to the framework's `ancestry-aware-mr` workflow / `demo_ancestry_aware_mr.py`.
It adds **no analysis of its own**; all computations run in the workflow modules. By default uses
**simulated multi-ancestry GWAS** with known causal effect and controlled pleiotropy rates to
validate the MR + pleiotropy detection pipeline — real-data deployment would use BBJ (EAS),
FinnGen (EUR), TPMI (SAS), and All of Us (AMR/AFR) summary statistics with ancestry-matched LD panels.
Evidence grade is **C** (methodology validation). Part of Phase 3a (cross-ancestry MR, CPU-only).
