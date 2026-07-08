---
name: bioresearch-causal-evidence
description: Run the causal-evidence chain (GWAS → eQTL → colocalization → TWAS → fine-mapping → MR) via the BioResearch Agent causal-evidence workflow. Use when the user wants to test whether a GWAS risk locus acts through a candidate gene's expression, identify the credible set, and check MR consistency. Synthetic loci by default; methodology validation, not a real etiological claim.
---

# BioResearch Agent — Causal Evidence Chain Skill

## Capability

Runs the full causal-evidence chain for a set of loci:

1. **GWAS → eQTL** — per-SNP association in both trait and expression.
2. **Colocalization** — full 5-hypothesis coloc (Giambartolomei 2014), reporting `PP.H4`
   (shared causal variant) vs `PP.H3` (distinct variants). Numerically stable (log-space ABF).
3. **TWAS** — S-PrediXcan-style expression-trait association (Z, p).
4. **Fine-mapping** — Bayesian credible set via per-SNP posterior inclusion probability (PIP),
   normalized over the locus.
5. **MR** — Wald-ratio causal estimate for the colocalized gene's lead SNP.

Returns a per-gene evidence table + credible-set CSV + locus heatmap, not a biological claim.

## Run

```bash
bioresearch run causal-evidence --seed 42 --output-dir outputs/causal-evidence
```

## Outputs (in `--output-dir`)

- `CE_per_gene_results.csv` — per-gene: truth class, `PP.H4`, TWAS Z/p, MR β/p, n credible
- `CE_credible_sets.csv` — per-SNP PIP + credible-set membership
- `CE_locus_heatmap.png` — GWAS / eQTL / coloc association heatmap
- `CE_recovery_benchmark.csv` — ground-truth recovery across effect sizes
- `CE_summary_report.txt` — human-readable summary
- `CE_evidence_package.json` — reproducible Evidence Package (provenance + benchmark + grade)

## Note

This skill dispatches to the framework's `causal-evidence` workflow / `demo_causal_evidence.py`.
It adds **no analysis of its own**; all statistics run in the workflow modules. By default uses
**synthetic loci with ground-truth labels** to validate the engine — real-data AD reference loci
(TREM2 / BIN1 / APOE / CLU / PICALM) are listed as the target for a real-data version. Evidence
grade is **C** (methodology validation).
