---
name: bioresearch-gwas-harmonization
description: Harmonize GWAS summary statistics across ancestries for cross-ancestry MR. Use when the user needs to align alleles, flip strands, resolve palindromic SNPs, compute allele-frequency divergence (Fst-like), or identify cross-ancestry genome-wide signal overlap. Supports GWAS-SSF schema; mock mode validates the harmonization pipeline with simulated cross-ancestry GWAS including strand confusion and allele flips.
---

# BioResearch Agent — GWAS Harmonization Skill

## Capability

Harmonizes GWAS summary statistics across multiple ancestries for cross-ancestry MR:

1. **Cross-ancestry GWAS simulation** — generates per-ancestry GWAS summary statistics with
   realistic allele-frequency drift (AFR < EUR < EAS/SAS/AMR), effect-size heterogeneity, and
   deliberately injected data-quality issues (allele swaps, strand confusion, palindromic SNPs).
2. **Allele harmonization** — 5-case alignment: direct match, effect-allele swap, strand flip,
   palindromic SNP removal, and unmatched SNP exclusion. Standardizes all ancestries to a common
   effect-allele / non-effect-allele convention.
3. **Strand ambiguity resolution** — removes palindromic SNPs (A/T, G/C) near EAF = 0.5 where
   strand orientation cannot be inferred, using a MAF-distance threshold (default ±0.01).
4. **Allele-frequency divergence** — computes pairwise Fst-like statistics across ancestries to
   quantify genetic divergence and flag SNPs with extreme AF differences (a source of MR bias).
5. **Cross-ancestry signal overlap** — identifies genome-wide significant SNPs shared across
   ancestries vs ancestry-specific, informing instrument selection and portability assessment.

Returns harmonized per-ancestry GWAS + AF comparison + overlap report, not a causal claim.

## Run

```bash
bioresearch run gwas-harmonization --n-snps 500 --n-causal 30 --seed 42 --output-dir outputs/gwas-harmonization
```

## Outputs (in `--output-dir`)

- `gh_harmonized_gwas.csv` — per-ancestry harmonized GWAS (SNP, CHR, POS, EA, NEA, BETA, SE, P, EAF, N)
- `gh_af_comparison.csv` — pairwise allele-frequency differences (SNP, ancestry_pair, af_diff, fst_like)
- `gh_cross_ancestry_overlaps.csv` — genome-wide significant SNPs per ancestry + overlap count
- `gh_harmonization_report.txt` — human-readable summary (n_harmonized, n_removed, n_palindromic)
- `gh_af_divergence_heatmap.png` — pairwise Fst-like matrix across ancestries
- `gh_evidence_package.json` — reproducible Evidence Package (provenance + parameters + grade)

## Note

This skill dispatches to the framework's `gwas-harmonization` workflow / `demo_gwas_harmonization.py`.
It adds **no analysis of its own**; all computations run in the workflow modules. By default uses
**simulated cross-ancestry GWAS** with injected quality issues to validate the harmonization pipeline —
real-data deployment would use IEU OpenGWAS / GWAS Catalog summary statistics with GWAS-SSF schema.
Evidence grade is **C** (methodology validation). Part of Phase 3a (cross-ancestry MR, CPU-only).
