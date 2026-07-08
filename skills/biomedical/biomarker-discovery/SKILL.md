---
name: bioresearch-biomarker-discovery
description: Run reproducible biomarker discovery via the BioResearch Agent biomarker workflow (differential expression, pathway enrichment, candidate ranking, volcano plot) over a GEO dataset or synthetic data. Use when the user asks to find gene biomarkers or candidate genes for a disease.
---

# BioResearch Agent — Biomarker Discovery Skill

## Capability

End-to-end biomarker discovery: dataset loading (GEO GSE7621 or synthetic) → differential
expression (t-test + Bonferroni) → hypergeometric pathway enrichment (KEGG/GO) → candidate
ranking → volcano plot. Returns ranked candidate biomarkers, not just a narrative.

## Run

```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

## Outputs (in `outputs/biomarker/`)

- `biomarker_deg_table.csv` — differentially expressed genes
- `biomarker_top_candidates.csv` — ranked candidates
- `biomarker_pathway_enrichment.csv` — enriched pathways / GO terms
- `biomarker_volcano_plot.png` — volcano plot
- `biomarker_report.txt` — structured report

## Note

This skill dispatches to the framework's `biomarker` workflow. It adds **no analysis of its
own**; all statistics run in the workflow modules. Requires no LLM key.
