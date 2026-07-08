---
name: bioresearch-causal-inference
description: Run two-sample Mendelian randomization via the BioResearch Agent causal workflow (IVW estimation, leave-one-out sensitivity, scatter / funnel plots). Use when the user asks to test a causal effect between an exposure and an outcome (e.g., BMI → Type 2 Diabetes) using genetic instruments.
---

# BioResearch Agent — Causal Inference (MR) Skill

## Capability

Runs a reproducible two-sample Mendelian randomization: GWAS summary statistics (simulated by
default) → genome-wide significant SNP instruments → IVW causal estimate → leave-one-out
sensitivity → scatter / funnel plots. Returns a quantitative causal estimate, not a claim.

## Run

```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```

## Outputs (in `outputs/causal/`)

- `causal_ivw_results.csv` — IVW estimate, SE, p-value
- `causal_loo_results.csv` — leave-one-out sensitivity
- `causal_mr_scatter.png` — MR scatter plot (IVW slope labeled)
- `causal_mr_funnel.png` — funnel plot
- `causal_interpretation.txt` — interpretation notes

## Note

This skill dispatches to the framework's `causal` workflow. It adds **no analysis of its own**;
all MR statistics run in the workflow modules. By default uses simulated GWAS data (no external
credentials required).
