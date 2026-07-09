#!/usr/bin/env python3
"""
Demo: LD Reference Panel Management (Mock LD blocks + LD clumping)
==================================================================

A *methodology* engine that simulates ancestry-specific LD reference panels
and performs LD-based clumping of GWAS summary statistics — the foundational
step for cross-ancestry Mendelian randomization.

IMPORTANT (honesty): the LD panels here are SYNTHETIC block-structured
correlation matrices, not real 1000 Genomes phased data. The engine implements
the real clumping algorithm (greedy significance-ordered index-SNP selection
with r² pruning) used by PLINK --clump / MR-Base, but the input LD structure
is simulated. For real deployment, swap `simulate_ld_panel` for `.npz` files
from 1000 Genomes phased data (EUR/AFR/EAS/SAS/AMR super-populations) and
point `next_validation` at real LD reference panels.

Steps demonstrated
------------------
  1. simulate_ld_panel   : ancestry-specific block LD correlation matrix
  2. ld_clump            : greedy significance-ordered clumping (r² threshold)
  3. compute_ld_scores   : per-SNP LD score (sum of r²)
  4. ld_reference_pipeline : orchestrates 1-3 + benchmark

Outputs (when run as a script):
  - {output_dir}/ld_panel_summary.csv       (per-ancestry LD block stats)
  - {output_dir}/ld_clumping_results.csv    (index SNPs + clumps)
  - {output_dir}/ld_scores.csv              (per-SNP LD scores)
  - {output_dir}/ld_heatmap.png             (LD matrix heatmap for one ancestry)
  - {output_dir}/ld_summary_report.txt      (human-readable summary)
  - {output_dir}/ld_evidence_package.json   (provenance + evidence grade)

Usage:
  python demo_ld_reference.py --n-snps 200 --n-blocks 10 --seed 42 --output-dir outputs/ld-reference
"""

import argparse
import json
import os
import sys
import textwrap
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")

# Ancestry-specific LD block parameters.
# Key biological insight: AFR populations have shorter LD blocks (faster decay)
# due to older population age; non-AFR populations have longer LD blocks
# due to serial founder effects during out-of-Africa migration.
# Reference: Gabriel et al. 2002, Science 296:2225-2229
ANCESTRY_SPECS = {
    "AFR": {
        "description": "African — shortest LD blocks, fastest r² decay",
        "mean_block_size": 8,      # SNPs per LD block
        "within_block_r2": 0.45,   # mean r² within blocks
        "between_block_r2": 0.02,  # background r² between blocks
        "reference": "1000G AFR super-population (mock)",
    },
    "AMR": {
        "description": "Admixed American — intermediate LD, admixture decay",
        "mean_block_size": 14,
        "within_block_r2": 0.55,
        "between_block_r2": 0.03,
        "reference": "1000G AMR super-population (mock)",
    },
    "EAS": {
        "description": "East Asian — long LD blocks, founder effect",
        "mean_block_size": 18,
        "within_block_r2": 0.65,
        "between_block_r2": 0.04,
        "reference": "1000G EAS super-population (mock)",
    },
    "SAS": {
        "description": "South Asian — long LD blocks, founder effect",
        "mean_block_size": 16,
        "within_block_r2": 0.60,
        "between_block_r2": 0.035,
        "reference": "1000G SAS super-population (mock)",
    },
    "EUR": {
        "description": "European — long LD blocks, serial founder",
        "mean_block_size": 20,
        "within_block_r2": 0.70,
        "between_block_r2": 0.05,
        "reference": "1000G EUR super-population (mock)",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_output_dir(output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    print(f"[PROGRESS] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 1. Simulate ancestry-specific LD reference panel
# ---------------------------------------------------------------------------
def simulate_ld_panel(
    ancestry: str = "EUR",
    n_snps: int = 200,
    n_blocks: int = 10,
    seed: int = 42,
) -> Tuple[np.ndarray, List[str], List[int]]:
    """Simulate an ancestry-specific LD correlation matrix with block structure.

    The matrix has n_blocks contiguous LD blocks. Within each block, pairwise
    r² decays exponentially with genomic distance. Between blocks, a small
    background correlation is added. The result is a valid correlation matrix
    (diagonal = 1, off-diagonal in [-1, 1], positive semi-definite).

    Parameters
    ----------
    ancestry : str
        One of AFR / AMR / EAS / SAS / EUR. Controls block size and r² strength.
    n_snps : int
        Total number of SNPs.
    n_blocks : int
        Number of LD blocks.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    ld_matrix : np.ndarray, shape (n_snps, n_snps)
        Correlation matrix (r values, not r²).
    snp_ids : list of str
        SNP identifiers (rs001, rs002, ...).
    block_assignments : list of int
        Block ID for each SNP.
    """
    if ancestry not in ANCESTRY_SPECS:
        raise ValueError(f"Unknown ancestry: {ancestry}. Choose from {list(ANCESTRY_SPECS)}")

    rng = np.random.default_rng(seed)
    spec = ANCESTRY_SPECS[ancestry]

    snp_ids = [f"rs{i+1:04d}" for i in range(n_snps)]

    # Assign SNPs to blocks (roughly equal size)
    snps_per_block = max(1, n_snps // n_blocks)
    block_assignments = []
    for b in range(n_blocks):
        start = b * snps_per_block
        end = min(start + snps_per_block, n_snps)
        block_assignments.extend([b] * (end - start))
    # Handle remainder
    while len(block_assignments) < n_snps:
        block_assignments.append(n_blocks - 1)

    # Build correlation matrix
    ld_matrix = np.zeros((n_snps, n_snps), dtype=np.float64)

    within_r2 = spec["within_block_r2"]
    between_r2 = spec["between_block_r2"]
    decay_rate = 0.15  # exponential decay of r² with distance within block

    for i in range(n_snps):
        for j in range(i, n_snps):
            if i == j:
                ld_matrix[i, j] = 1.0
            elif block_assignments[i] == block_assignments[j]:
                # Within-block: exponential decay
                dist = abs(i - j)
                r2 = within_r2 * np.exp(-decay_rate * dist)
                # Add noise
                r2 = max(0.0, r2 + rng.normal(0, 0.05))
                r = np.sqrt(r2) * (1 if rng.random() > 0.5 else -1)
                ld_matrix[i, j] = r
                ld_matrix[j, i] = r
            else:
                # Between-block: small background
                r2 = between_r2 + rng.normal(0, 0.01)
                r2 = max(0.0, r2)
                r = np.sqrt(r2) * (1 if rng.random() > 0.5 else -1)
                ld_matrix[i, j] = r
                ld_matrix[j, i] = r

    # Ensure positive semi-definite via nearest correlation matrix
    # (simple approach: clip eigenvalues)
    eigvals, eigvecs = np.linalg.eigh(ld_matrix)
    eigvals = np.maximum(eigvals, 0)
    ld_matrix = eigvecs @ np.diag(eigvals) @ eigvecs.T
    # Re-normalize diagonal to 1
    d = np.sqrt(np.diag(ld_matrix))
    ld_matrix = ld_matrix / np.outer(d, d)
    np.fill_diagonal(ld_matrix, 1.0)

    return ld_matrix, snp_ids, block_assignments


# ---------------------------------------------------------------------------
# 2. LD clumping (greedy significance-ordered)
# ---------------------------------------------------------------------------
def ld_clump(
    snp_ids: List[str],
    pvals: np.ndarray,
    ld_matrix: np.ndarray,
    r2_threshold: float = 0.1,
    distance_threshold: int = 500,
) -> pd.DataFrame:
    """Perform greedy LD-based clumping of GWAS summary statistics.

    Algorithm (mirrors PLINK --clump):
      1. Sort SNPs by ascending p-value (most significant first).
      2. Pick the most significant SNP as an index SNP.
      3. Remove all SNPs with r² > threshold to the index SNP.
      4. Repeat with the next most significant remaining SNP.

    Parameters
    ----------
    snp_ids : list of str
        SNP identifiers.
    pvals : np.ndarray
        GWAS p-values for each SNP.
    ld_matrix : np.ndarray
        Correlation matrix (r values). r² = r².
    r2_threshold : float
        r² threshold for clumping (default 0.1, standard for MR).
    distance_threshold : int
        Maximum distance (in SNP index units) for clumping.

    Returns
    -------
    pd.DataFrame with columns:
        index_snp, clump_size, clump_members, min_pval, mean_r2_in_clump
    """
    n = len(snp_ids)
    available = set(range(n))
    r2_matrix = ld_matrix ** 2

    # Sort by p-value (ascending = most significant first)
    order = np.argsort(pvals)

    results = []
    for idx in order:
        if idx not in available:
            continue

        # This SNP becomes an index SNP
        clump_members = [idx]

        # Find all available SNPs in LD with this index
        for j in list(available):
            if j == idx:
                continue
            dist = abs(j - idx)
            if dist <= distance_threshold and r2_matrix[idx, j] >= r2_threshold:
                clump_members.append(j)

        # Remove clumped SNPs from available pool
        for m in clump_members:
            available.discard(m)

        # Compute clump statistics
        clump_r2s = [r2_matrix[idx, m] for m in clump_members if m != idx]
        results.append({
            "index_snp": snp_ids[idx],
            "index_pval": float(pvals[idx]),
            "clump_size": len(clump_members),
            "clump_members": ";".join(snp_ids[m] for m in clump_members),
            "mean_r2_in_clump": float(np.mean(clump_r2s)) if clump_r2s else 0.0,
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# 3. Compute LD scores
# ---------------------------------------------------------------------------
def compute_ld_scores(ld_matrix: np.ndarray, snp_ids: List[str]) -> pd.DataFrame:
    """Compute per-SNP LD scores (sum of r² with all other SNPs).

    LD score is a key quantity in LD score regression (LDSC) for estimating
    SNP heritability and genetic correlation. Here we compute the simple
    univariate LD score: l_j = sum_{k != j} r²_{jk}.

    Returns
    -------
    pd.DataFrame with columns: snp_id, ld_score, mean_r2, max_r2
    """
    r2_matrix = ld_matrix ** 2
    n = len(snp_ids)

    # Zero out diagonal
    np.fill_diagonal(r2_matrix, 0)

    ld_scores = r2_matrix.sum(axis=1)
    mean_r2 = r2_matrix.mean(axis=1)
    max_r2 = r2_matrix.max(axis=1)

    # Restore diagonal
    np.fill_diagonal(r2_matrix, 1.0)

    return pd.DataFrame({
        "snp_id": snp_ids,
        "ld_score": ld_scores,
        "mean_r2": mean_r2,
        "max_r2": max_r2,
    })


# ---------------------------------------------------------------------------
# 4. Pipeline orchestration
# ---------------------------------------------------------------------------
def ld_reference_pipeline(
    n_snps: int = 200,
    n_blocks: int = 10,
    ancestries: List[str] = None,
    r2_threshold: float = 0.1,
    seed: int = 42,
    output_dir: str = None,
) -> Dict:
    """Run the full LD reference pipeline across multiple ancestries.

    Steps:
      1. Simulate LD panels for each ancestry
      2. Simulate GWAS p-values
      3. Perform LD clumping for each ancestry
      4. Compute LD scores
      5. Compare clumping results across ancestries

    Returns a dict with all results and writes output files.
    """
    if ancestries is None:
        ancestries = ["EUR", "AFR", "EAS"]

    output_dir = ensure_output_dir(output_dir)
    rng = np.random.default_rng(seed)

    print_progress(f"Simulating LD panels for {len(ancestries)} ancestries")

    # --- Step 1: Simulate LD panels ---
    ld_panels = {}
    panel_stats = []

    for anc in ancestries:
        ld_matrix, snp_ids, block_assignments = simulate_ld_panel(
            ancestry=anc, n_snps=n_snps, n_blocks=n_blocks, seed=seed
        )
        ld_panels[anc] = {
            "matrix": ld_matrix,
            "snp_ids": snp_ids,
            "blocks": block_assignments,
        }

        # Compute panel-level stats
        r2_matrix = ld_matrix ** 2
        np.fill_diagonal(r2_matrix, 0)
        panel_stats.append({
            "ancestry": anc,
            "n_snps": n_snps,
            "n_blocks": n_blocks,
            "mean_block_size": n_snps / n_blocks,
            "mean_r2_within": float(np.mean([
                r2_matrix[i, j] for i in range(n_snps) for j in range(i+1, n_snps)
                if block_assignments[i] == block_assignments[j]
            ])),
            "mean_r2_between": float(np.mean([
                r2_matrix[i, j] for i in range(n_snps) for j in range(i+1, n_snps)
                if block_assignments[i] != block_assignments[j]
            ])),
            "mean_ld_score": float(np.mean(r2_matrix.sum(axis=1))),
            "description": ANCESTRY_SPECS[anc]["description"],
        })

    panel_df = pd.DataFrame(panel_stats)
    panel_df.to_csv(os.path.join(output_dir, "ld_panel_summary.csv"), index=False)
    print_progress(f"  Panel summary saved: {len(panel_df)} ancestries")

    # --- Step 2: Simulate GWAS p-values ---
    # Plant a few "significant" SNPs to test clumping
    n_significant = max(5, n_snps // 20)
    pvals = rng.uniform(0.1, 1.0, size=n_snps)
    significant_indices = rng.choice(n_snps, size=n_significant, replace=False)
    pvals[significant_indices] = rng.uniform(1e-8, 1e-3, size=n_significant)

    # --- Step 3: LD clumping for each ancestry ---
    clumping_results = []
    for anc in ancestries:
        panel = ld_panels[anc]
        clump_df = ld_clump(
            snp_ids=panel["snp_ids"],
            pvals=pvals,
            ld_matrix=panel["matrix"],
            r2_threshold=r2_threshold,
            distance_threshold=n_snps,  # no distance limit in mock
        )
        clump_df["ancestry"] = anc
        clumping_results.append(clump_df)

        print_progress(
            f"  {anc}: {len(clump_df)} index SNPs from {n_snps} total "
            f"(clumping ratio: {len(clump_df)/n_snps:.2%})"
        )

    clump_all = pd.concat(clumping_results, ignore_index=True)
    clump_all.to_csv(os.path.join(output_dir, "ld_clumping_results.csv"), index=False)

    # --- Step 4: LD scores (for EUR as reference) ---
    ref_anc = ancestries[0]
    ref_panel = ld_panels[ref_anc]
    ld_scores_df = compute_ld_scores(ref_panel["matrix"], ref_panel["snp_ids"])
    ld_scores_df.to_csv(os.path.join(output_dir, "ld_scores.csv"), index=False)

    # --- Step 5: Cross-ancestry comparison ---
    cross_anc = clump_all.groupby("ancestry").agg(
        n_index_snps=("index_snp", "count"),
        mean_clump_size=("clump_size", "mean"),
        max_clump_size=("clump_size", "max"),
        mean_r2_in_clump=("mean_r2_in_clump", "mean"),
    ).reset_index()

    # --- Step 6: LD heatmap for reference ancestry ---
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(ref_panel["matrix"], cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_title(f"LD Matrix — {ref_anc} (mock, {n_snps} SNPs, {n_blocks} blocks)")
    ax.set_xlabel("SNP index")
    ax.set_ylabel("SNP index")
    plt.colorbar(im, ax=ax, label="r (correlation)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "ld_heatmap.png"), dpi=150)
    plt.close(fig)
    print_progress(f"  LD heatmap saved for {ref_anc}")

    # --- Summary report ---
    report_lines = [
        "LD Reference Panel Pipeline — Summary Report",
        "=" * 60,
        f"Seed: {seed}",
        f"SNPs: {n_snps}, Blocks: {n_blocks}",
        f"r² threshold for clumping: {r2_threshold}",
        f"Ancestries: {', '.join(ancestries)}",
        "",
        "Per-ancestry LD panel statistics:",
    ]
    for _, row in panel_df.iterrows():
        report_lines.append(
            f"  {row['ancestry']}: mean r² within-block = {row['mean_r2_within']:.3f}, "
            f"mean r² between-block = {row['mean_r2_between']:.3f}, "
            f"mean LD score = {row['mean_ld_score']:.3f}"
        )
    report_lines.append("")
    report_lines.append("Clumping results (cross-ancestry comparison):")
    for _, row in cross_anc.iterrows():
        report_lines.append(
            f"  {row['ancestry']}: {row['n_index_snps']} index SNPs, "
            f"mean clump size = {row['mean_clump_size']:.1f}, "
            f"max clump size = {row['max_clump_size']}"
        )
    report_lines.append("")
    report_lines.append("Key insight:")
    report_lines.append(
        "  AFR has fewer SNPs per clump (shorter LD blocks) → more independent "
        "instruments for MR. EUR/EAS have more SNPs per clump (longer LD) → fewer "
        "instruments but each tags a larger region. This is the biological basis "
        "for ancestry-specific LD reference panels in cross-ancestry MR."
    )
    report_lines.append("")
    report_lines.append("Evidence grade: C (mock LD panels, not real 1000G data)")
    report_lines.append(
        "Next validation: replace mock LD panels with real 1000 Genomes "
        "stratified LD matrices (PLINK --r2 or ldstore)."
    )

    report_text = "\n".join(report_lines)
    with open(os.path.join(output_dir, "ld_summary_report.txt"), "w") as f:
        f.write(report_text)

    # --- Evidence package ---
    evidence_package = {
        "case_id": "ld-reference-mock",
        "pipeline": "LD reference panel simulation + clumping",
        "evidence_grade": "C",
        "data_type": "SYNTHETIC",
        "seed": seed,
        "parameters": {
            "n_snps": n_snps,
            "n_blocks": n_blocks,
            "r2_threshold": r2_threshold,
            "ancestries": ancestries,
        },
        "results": {
            "panel_stats": panel_df.to_dict(orient="records"),
            "clumping_comparison": cross_anc.to_dict(orient="records"),
        },
        "limitations": [
            "Mock LD panels use block-structured correlation matrices, not real 1000G phased data.",
            "LD decay model is exponential, not based on real recombination maps.",
            "No allele frequency differences between ancestries are modeled (only LD structure).",
            "Clumping distance threshold is in SNP-index units, not base pairs.",
        ],
        "next_validation": "Replace with real 1000 Genomes stratified LD matrices.",
        "provenance": {
            "script": "demo_ld_reference.py",
            "framework_version": "1.8.0",
        },
    }
    with open(os.path.join(output_dir, "ld_evidence_package.json"), "w") as f:
        json.dump(evidence_package, f, indent=2, ensure_ascii=False)

    print_progress("Pipeline complete. All outputs saved.")

    return {
        "panel_summary": panel_df,
        "clumping_results": clump_all,
        "cross_ancestry": cross_anc,
        "ld_scores": ld_scores_df,
        "evidence_package": evidence_package,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="LD reference panel simulation + LD clumping demo."
    )
    ap.add_argument("--n-snps", type=int, default=200, help="Number of SNPs (default 200)")
    ap.add_argument("--n-blocks", type=int, default=10, help="Number of LD blocks (default 10)")
    ap.add_argument(
        "--ancestries", nargs="+", default=["EUR", "AFR", "EAS"],
        help="Ancestries to simulate (default EUR AFR EAS)"
    )
    ap.add_argument("--r2-threshold", type=float, default=0.1, help="r² clumping threshold (default 0.1)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--output-dir", type=str, default=None, help="Output directory")
    args = ap.parse_args(argv)

    result = ld_reference_pipeline(
        n_snps=args.n_snps,
        n_blocks=args.n_blocks,
        ancestries=args.ancestries,
        r2_threshold=args.r2_threshold,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print("\n" + "=" * 60)
    print("LD Reference Pipeline — Results Summary")
    print("=" * 60)
    print(result["cross_ancestry"].to_string(index=False))
    print(f"\nEvidence grade: {result['evidence_package']['evidence_grade']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
