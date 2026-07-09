---
name: bioresearch-ld-reference-management
description: Manage ancestry-specific LD reference panels and perform LD clumping for cross-ancestry MR. Use when the user needs to simulate ancestry-aware LD block structures (AFR/EUR/EAS/SAS/AMR), run greedy distance-based clumping (PLINK --clump style), or compute LD scores for stratified LDSC. Mock mode validates the clumping pipeline; live mode wraps PLINK 2.0 + 1000 Genomes reference panels.
---

# BioResearch Agent — LD Reference Panel Management Skill

## Capability

Manages ancestry-specific LD reference panels and performs LD-based instrument clumping:

1. **Ancestry-aware LD simulation** — generates realistic LD block structures for 5 super-populations
   (AFR / EUR / EAS / SAS / AMR) with biologically grounded parameters: AFR has shortest LD blocks
   (older population, more recombination), non-AFR populations have longer blocks (serial founder
   effects). Block lengths and LD decay rates follow 1000 Genomes empirical patterns.
2. **Greedy LD clumping** — PLINK `--clump`-style algorithm: sort SNPs by p-value, greedily select
   lead SNPs, remove proxies within a distance + r² threshold. Returns independent instrument set.
3. **LD score computation** — per-SNP LD scores (sum of r² with neighbors) for stratified LDSC
   heritability partitioning across ancestries.
4. **Cross-ancestry LD comparison** — pairwise LD decay curves and block-length distributions,
   quantifying how LD structure differs across populations (the root cause of ancestry-portability
   failure in MR).

Returns a clumped instrument set + LD score table + ancestry comparison report, not a causal claim.

## Run

```bash
bioresearch run ld-reference-management --ancestry EUR --n-snps 500 --seed 42 --output-dir outputs/ld-reference
```

## Outputs (in `--output-dir`)

- `ld_clumped_instruments.csv` — independent lead SNPs after clumping (SNP, CHR, POS, P, cluster_id)
- `ld_scores.csv` — per-SNP LD scores per ancestry (SNP, ancestry, ld_score)
- `ld_decay_comparison.csv` — pairwise LD decay curves (distance, mean_r2, ancestry_pair)
- `ld_block_summary.csv` — per-ancestry block-length statistics (mean, median, max, n_blocks)
- `ld_ancestry_heatmap.png` — LD decay heatmap across ancestries
- `ld_evidence_package.json` — reproducible Evidence Package (provenance + parameters + grade)

## Note

This skill dispatches to the framework's `ld-reference-management` workflow / `demo_ld_reference.py`.
It adds **no analysis of its own**; all computations run in the workflow modules. By default uses
**simulated LD panels with ancestry-specific parameters** to validate the clumping pipeline —
real-data deployment would use PLINK 2.0 with 1000 Genomes Phase 3 reference panels per ancestry.
Evidence grade is **C** (methodology validation). Part of Phase 3a (cross-ancestry MR, CPU-only).
