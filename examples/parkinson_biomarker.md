# Example — Parkinson's Disease Biomarker Discovery

**Goal:** Have your AI assistant find candidate biomarkers for Parkinson's disease from public omics data and return a real volcano plot.

## Via AI assistant (after installing the `biomarker` skill)

> **You:** Find biomarker candidates for Parkinson's disease and show me the differential-expression result.

> **Assistant:** Running the `bioresearch` biomarker workflow…
> - Loaded GEO dataset (GSE7621) or synthetic fallback
> - Differential expression (t-test + Bonferroni correction)
> - Pathway enrichment (KEGG / GO, hypergeometric)
> - Ranked top candidates
>
> Outputs written to `outputs/biomarker/`:
> - `biomarker_deg_table.csv`
> - `biomarker_top_candidates.csv`
> - `biomarker_pathway_enrichment.csv`
> - `biomarker_volcano_plot.png`
> - `biomarker_report.txt`

## Via CLI (same engine)

```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

## What it actually does

GEO retrieval → differential expression (t-test + Bonferroni) → pathway enrichment → candidate
ranking → volcano plot. The statistical methods are delegated to established domain libraries
(limma-style t-test, hypergeometric enrichment); the framework standardizes the execution and
output contract.

See a sample volcano plot: `assets/figure3_output_gallery.png` (middle panel) or
`outputs/biomarker/biomarker_volcano_plot.png`.
