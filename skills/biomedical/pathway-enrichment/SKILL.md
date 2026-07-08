---
name: bioresearch-pathway-enrichment
description: Run pathway enrichment (hypergeometric KEGG / GO) via the BioResearch Agent biomarker workflow, which performs enrichment after differential expression. Use when the user asks for pathway, GO, or KEGG enrichment analysis for a disease or a gene set.
---

# BioResearch Agent — Pathway Enrichment Skill

## Capability

Runs pathway / GO / KEGG enrichment. In the framework this is stage 2 of the `biomarker`
workflow: it takes the differentially expressed genes and tests them against KEGG pathways and GO
terms with a hypergeometric test.

## Run

```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

(Invokes the biomarker workflow; enrichment is produced in stage 2.)

## Outputs (in `outputs/biomarker/`)

- `biomarker_pathway_enrichment.csv` — enriched pathways / GO terms with p-values

## Note

There is no standalone `pathway-enrichment` CLI command — enrichment is computed inside the
`biomarker` workflow. This skill is a focused entry point that triggers that workflow when the
user's intent is specifically pathway / GO / KEGG enrichment. It adds **no statistics of its
own**.
