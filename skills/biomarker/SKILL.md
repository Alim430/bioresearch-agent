---
name: bioresearch-biomarker
description: Invoke the BioResearch Agent biomarker workflow (differential expression + pathway enrichment) through the bioresearch CLI. Use when the user asks to discover candidate biomarkers, run differential-expression analysis, or enrich pathways for a disease from public omics data.
---

# BioResearch Biomarker Skill

Client-side integration wrapper for the BioResearch Agent **biomarker** workflow.
This skill dispatches to the existing `bioresearch` CLI/SDK — it does not add new
analysis or reasoning capabilities of its own.

## Run
```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

## Outputs
- `biomarker_deg_table.csv`
- `biomarker_top_candidates.csv`
- `biomarker_pathway_enrichment.csv`
- `biomarker_volcano_plot.png`
- `biomarker_report.txt`
