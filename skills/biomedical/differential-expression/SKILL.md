---
name: bioresearch-differential-expression
description: Perform differential expression (DEG) analysis via the BioResearch Agent biomarker workflow, which computes DEGs (t-test + Bonferroni correction) as its first stage. Use when the user specifically asks for differential expression, DEGs, fold-change, or a volcano plot for a disease or gene-expression dataset.
---

# BioResearch Agent — Differential Expression Skill

## Capability

Runs differential expression analysis. In the framework this is the first stage of the
`biomarker` workflow: it loads a gene-expression dataset (GEO or synthetic), performs a t-test
with Bonferroni multiple-testing correction, and emits a DEG table and volcano plot.

## Run

```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

(Invokes the biomarker workflow; differential expression is produced in stage 1.)

## Outputs (in `outputs/biomarker/`)

- `biomarker_deg_table.csv` — genes with p-value, adjusted p-value, log2 fold-change
- `biomarker_volcano_plot.png` — volcano plot of DEGs

## Note

There is no standalone `differential-expression` CLI command — DEG is computed inside the
`biomarker` workflow. This skill is a focused entry point that triggers that workflow when the
user's intent is specifically differential expression. It adds **no statistics of its own**.
