---
name: bioresearch-causal
description: Invoke the BioResearch Agent causal (Mendelian randomization) workflow through the bioresearch CLI.
---

# BioResearch Causal Skill

Client-side integration wrapper for the BioResearch Agent **causal** workflow.
This skill dispatches to the existing `bioresearch` CLI/SDK — it does not add new
analysis or reasoning capabilities of its own.

## Run
```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```

## Outputs
- `causal_ivw_results.csv`
- `causal_loo_results.csv`
- `causal_mr_scatter.png`
- `causal_mr_funnel.png`
- `causal_interpretation.txt`
