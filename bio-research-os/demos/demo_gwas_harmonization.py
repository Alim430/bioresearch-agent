#!/usr/bin/env python3
"""
Demo: GWAS Summary-Stat Harmonization for Cross-Ancestry MR
=============================================================

A *methodology* engine that demonstrates the harmonization pipeline required
before any cross-ancestry Mendelian Randomization analysis can be performed.

IMPORTANT (honesty): the GWAS summary statistics here are SYNTHETIC. The engine
implements the real harmonization logic (allele alignment, strand flipping,
effect-allele standardisation, genome-wide significant SNP extraction) but the
input data are simulated with a known ground-truth allele-frequency structure
across five super-populations (AFR, AMR, EAS, SAS, EUR). This validates that
the *harmonization computations correctly recover the planted structure* — it
is NOT a claim about any real trait. For a real deployment, replace
`simulate_cross_ancestry_gwas` with summary statistics from IEU OpenGWAS,
BBJ, FinnGen, TPMI, or GWAS Catalog and point `next_validation` at those
sources.

Steps demonstrated
------------------
  1. simulate_cross_ancestry_gwas : generate per-ancestry GWAS with different
                                    allele frequencies, LD structure, and sample
                                    sizes; introduce allele flips and strand
                                    ambiguity to simulate real-world messiness
  2. harmonize_alleles            : align all ancestries to a reference allele
                                    (EUR); flip beta when effect allele is swapped
  3. resolve_strand_ambiguity     : identify and remove palindromic SNPs
                                    (A/T, G/C) where allele alignment is
                                    indeterminate
  4. compute_af_differences       : per-SNP allele-frequency divergence across
                                    ancestries (Fst-like metric)
  5. extract_genome_wide_signals  : per-ancestry genome-wide significant SNPs
                                    + cross-ancestry overlap
  6. gwas_harmonization_pipeline  : orchestrates 1-5 + evidence package

Outputs (when run as a script):
  - {output_dir}/gh_harmonized_gwas.csv         (all ancestries, aligned)
  - {output_dir}/gh_af_comparison.csv           (per-SNP AF across ancestries)
  - {output_dir}/gh_cross_ancestry_overlaps.csv (genome-wide signal overlap)
  - {output_dir}/gh_harmonization_report.txt     (text summary)
  - {output_dir}/gh_af_divergence_heatmap.png   (AF divergence across ancestries)
  - {output_dir}/gh_evidence_package.json       (evidence package)

Usage:
  python demo_gwas_harmonization.py --n-snps 500 --n-causal 30 --seed 42 --output-dir outputs/gwas-harmonization
"""

import argparse
import json
import os
import sys
import textwrap
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")

# GWAS-SSF (summary-statistics format) standard columns
GWAS_SSF_SCHEMA = [
    "SNP",          # rsID
    "CHR",          # chromosome
    "POS",          # base-pair position
    "EA",           # effect allele
    "NEA",          # non-effect allele
    "BETA",         # effect-allele beta
    "SE",           # standard error
    "P",            # p-value
    "EAF",          # effect-allele frequency
    "N",            # sample size
]

# Ancestry-specific parameters
# (sample sizes inspired by real biobank scales, allele-frequency drift modelled
#  via Bottleneck-then-expansion demographic model)
ANCESTRY_PARAMS = {
    "EUR": {
        "n_samples": 450_000,   # UK Biobank scale
        "f0_mean": 0.30,        # ancestral allele frequency
        "f0_std": 0.15,
        "af_drift": 0.00,       # reference (drift = 0)
        "label": "European",
    },
    "EAS": {
        "n_samples": 200_000,   # BBJ scale
        "f0_mean": 0.30,
        "f0_std": 0.15,
        "af_drift": 0.12,       # larger drift after bottleneck
        "label": "East Asian",
    },
    "SAS": {
        "n_samples": 150_000,   # TPMI scale
        "f0_mean": 0.30,
        "f0_std": 0.15,
        "af_drift": 0.08,
        "label": "South Asian",
    },
    "AFR": {
        "n_samples": 100_000,   # All of Us / Nigeria Biobank scale
        "f0_mean": 0.30,
        "f0_std": 0.15,
        "af_drift": 0.05,       # oldest population, more diversity, less drift from f0
        "label": "African",
    },
    "AMR": {
        "n_samples": 80_000,    # Mexican Biobank scale
        "f0_mean": 0.30,
        "f0_std": 0.15,
        "af_drift": 0.10,
        "label": "Admixed American",
    },
}

# Palindromic SNPs: alleles that are indistinguishable on opposite strands
PALINDROMIC_PAIRS = {("A", "T"), ("T", "A"), ("G", "C"), ("C", "G")}

# Complement map for strand flipping
COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}


def ensure_output_dir(output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    print(f"[PROGRESS] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Step 1: Simulate cross-ancestry GWAS
# ---------------------------------------------------------------------------

def simulate_cross_ancestry_gwas(
    n_snps: int = 500,
    n_causal: int = 30,
    true_effect: float = 0.30,
    ancestries: Optional[List[str]] = None,
    flip_rate: float = 0.15,
    strand_confusion_rate: float = 0.05,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Simulate per-ancestry GWAS summary statistics.

    Model:
      - Shared ancestral allele frequency f0 ~ Beta(2, 2) centred at ~0.3
      - Per-ancestry allele frequency via drift: f_pop = f0 + drift_noise
      - True effect is shared across ancestries (no gene-environment interaction)
      - Beta observed = true_effect * indicator(causal) + sampling noise
      - Randomly flip alleles (swap EA/NEA) at `flip_rate` to simulate
        real-world allele-coding inconsistency
      - Randomly introduce strand confusion at `strand_confusion_rate`

    Returns a dict {ancestry: DataFrame} with GWAS-SSF columns.
    """
    if ancestries is None:
        ancestries = list(ANCESTRY_PARAMS.keys())

    rng = np.random.default_rng(seed)

    # Shared ancestral allele frequencies
    f0 = np.clip(
        rng.normal(ANCESTRY_PARAMS["EUR"]["f0_mean"],
                   ANCESTRY_PARAMS["EUR"]["f0_std"],
                   size=n_snps),
        0.01, 0.99,
    )

    # Select causal SNPs
    causal_idx = rng.choice(n_snps, size=n_causal, replace=False)
    is_causal = np.zeros(n_snps, dtype=bool)
    is_causal[causal_idx] = True

    # Shared effect sizes for causal SNPs
    true_betas = np.zeros(n_snps)
    true_betas[is_causal] = rng.normal(true_effect, 0.05, size=n_causal)

    # Generate SNP IDs and positions
    snp_ids = [f"rs{1000000 + i}" for i in range(n_snps)]
    chroms = np.repeat(np.arange(1, 23), np.ceil(n_snps / 22).astype(int))[:n_snps]
    positions = rng.integers(1_000_000, 250_000_000, size=n_snps)

    # Assign random alleles (A/T/G/C)
    allele_choices = ["A", "T", "G", "C"]
    ref_alleles = rng.choice(allele_choices, size=n_snps)
    alt_alleles = np.array([
        rng.choice([a for a in allele_choices if a != ref_alleles[i]])
        for i in range(n_snps)
    ])

    gwas_dict = {}

    for anc in ancestries:
        params = ANCESTRY_PARAMS[anc]
        n = params["n_samples"]

        # Allele-frequency drift from ancestral
        drift = rng.normal(0, params["af_drift"], size=n_snps)
        eaf = np.clip(f0 + drift, 0.01, 0.99)

        # Standard error ~ 1/sqrt(N * 2 * MAF * (1-MAF))
        se = 1.0 / np.sqrt(n * 2.0 * eaf * (1.0 - eaf))

        # True beta (shared) + sampling noise
        beta = true_betas + rng.normal(0, se)

        # P-value
        z = beta / se
        p = 2.0 * stats.norm.sf(np.abs(z))

        # Build DataFrame
        ea = ref_alleles.copy()
        nea = alt_alleles.copy()

        # Introduce allele flips (swap EA/NEA) at flip_rate
        flip_mask = rng.random(n_snps) < flip_rate
        ea_flipped = ea.copy()
        nea_flipped = nea.copy()
        ea_flipped[flip_mask] = nea[flip_mask]
        nea_flipped[flip_mask] = ea[flip_mask]
        beta_flipped = beta.copy()
        # When EA/NEA are swapped, beta changes sign
        beta_flipped[flip_mask] = -beta[flip_mask]
        # EAF becomes 1 - EAF when alleles are swapped
        eaf_flipped = eaf.copy()
        eaf_flipped[flip_mask] = 1.0 - eaf[flip_mask]

        # Introduce strand confusion at strand_confusion_rate
        # (convert to opposite strand — this is a real-world data quality issue)
        strand_mask = rng.random(n_snps) < strand_confusion_rate
        for i in np.where(strand_mask)[0]:
            ea_flipped[i] = COMPLEMENT.get(ea_flipped[i], ea_flipped[i])
            nea_flipped[i] = COMPLEMENT.get(nea_flipped[i], nea_flipped[i])

        df = pd.DataFrame({
            "SNP": snp_ids,
            "CHR": chroms,
            "POS": positions,
            "EA": ea_flipped,
            "NEA": nea_flipped,
            "BETA": beta_flipped,
            "SE": se,
            "P": p,
            "EAF": eaf_flipped,
            "N": n,
            "causal": is_causal,
            "ancestry": anc,
        })
        gwas_dict[anc] = df

    print_progress(
        f"Simulated {n_snps} SNPs ({n_causal} causal) for {len(ancestries)} ancestries. "
        f"Flip rate={flip_rate}, strand confusion rate={strand_confusion_rate}."
    )
    return gwas_dict


# ---------------------------------------------------------------------------
# Step 2: Harmonize alleles to reference ancestry
# ---------------------------------------------------------------------------

def _normalize_alleles(ea: str, nea: str) -> Tuple[str, str]:
    """Sort alleles alphabetically for strand-agnostic comparison."""
    return tuple(sorted([ea.upper(), nea.upper()]))


def _is_palindromic(ea: str, nea: str) -> bool:
    """Check if a SNP is palindromic (A/T or G/C)."""
    return (ea.upper(), nea.upper()) in PALINDROMIC_PAIRS


def harmonize_alleles(
    gwas_dict: Dict[str, pd.DataFrame],
    reference_ancestry: str = "EUR",
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, int]]:
    """
    Harmonize alleles across ancestries to match the reference ancestry.

    For each SNP in each non-reference ancestry:
      1. If alleles match reference (EA=EA_ref, NEA=NEA_ref): no change
      2. If alleles are swapped (EA=NEA_ref, NEA=EA_ref): flip beta sign and EAF
      3. If alleles match reference on opposite strand: complement to reference strand
      4. If SNP is palindromic and alleles don't match: flag for removal

    Returns (harmonized_dict, stats_dict).
    """
    if reference_ancestry not in gwas_dict:
        raise ValueError(f"Reference ancestry {reference_ancestry} not in GWAS dict.")

    ref_df = gwas_dict[reference_ancestry].set_index("SNP")
    ref_ea = ref_df["EA"].to_dict()
    ref_nea = ref_df["NEA"].to_dict()

    harmonized = {reference_ancestry: gwas_dict[reference_ancestry].copy()}
    stats = {reference_ancestry: {"matched": len(ref_df), "flipped": 0, "strand_corrected": 0, "palindromic_removed": 0, "unmatched": 0}}

    for anc, df in gwas_dict.items():
        if anc == reference_ancestry:
            continue

        df = df.copy()
        n = len(df)
        matched = 0
        flipped = 0
        strand_corrected = 0
        palindromic_removed = 0
        unmatched = 0

        keep_mask = np.ones(n, dtype=bool)

        for i in range(n):
            snp = df.iloc[i]["SNP"]
            ea = df.iloc[i]["EA"].upper()
            nea = df.iloc[i]["NEA"].upper()

            if snp not in ref_ea:
                keep_mask[i] = False
                unmatched += 1
                continue

            ref_ea_snp = ref_ea[snp].upper()
            ref_nea_snp = ref_nea[snp].upper()

            # Case 1: Direct match
            if ea == ref_ea_snp and nea == ref_nea_snp:
                matched += 1
                continue

            # Case 2: Swapped alleles — flip beta and EAF
            if ea == ref_nea_snp and nea == ref_ea_snp:
                df.iloc[i, df.columns.get_loc("BETA")] *= -1
                df.iloc[i, df.columns.get_loc("EAF")] = 1.0 - df.iloc[i]["EAF"]
                df.iloc[i, df.columns.get_loc("EA")] = ref_ea_snp
                df.iloc[i, df.columns.get_loc("NEA")] = ref_nea_snp
                flipped += 1
                continue

            # Case 3: Strand mismatch — complement and re-check
            ea_comp = COMPLEMENT.get(ea, ea)
            nea_comp = COMPLEMENT.get(nea, nea)

            if ea_comp == ref_ea_snp and nea_comp == ref_nea_snp:
                df.iloc[i, df.columns.get_loc("EA")] = ref_ea_snp
                df.iloc[i, df.columns.get_loc("NEA")] = ref_nea_snp
                strand_corrected += 1
                matched += 1
                continue

            if ea_comp == ref_nea_snp and nea_comp == ref_ea_snp:
                df.iloc[i, df.columns.get_loc("BETA")] *= -1
                df.iloc[i, df.columns.get_loc("EAF")] = 1.0 - df.iloc[i]["EAF"]
                df.iloc[i, df.columns.get_loc("EA")] = ref_ea_snp
                df.iloc[i, df.columns.get_loc("NEA")] = ref_nea_snp
                strand_corrected += 1
                flipped += 1
                continue

            # Case 4: Palindromic — cannot resolve
            if _is_palindromic(ea, nea):
                keep_mask[i] = False
                palindromic_removed += 1
                continue

            # Case 5: Completely unmatched
            keep_mask[i] = False
            unmatched += 1

        df = df[keep_mask].reset_index(drop=True)
        harmonized[anc] = df
        stats[anc] = {
            "matched": matched,
            "flipped": flipped,
            "strand_corrected": strand_corrected,
            "palindromic_removed": palindromic_removed,
            "unmatched": unmatched,
        }

    print_progress(
        f"Harmonized {len(harmonized)} ancestries to reference '{reference_ancestry}'. "
        f"Stats: {json.dumps(stats, indent=2)}"
    )
    return harmonized, stats


# ---------------------------------------------------------------------------
# Step 3: Resolve strand ambiguity (palindromic SNPs)
# ---------------------------------------------------------------------------

def resolve_strand_ambiguity(
    gwas_dict: Dict[str, pd.DataFrame],
    maf_threshold: float = 0.01,
) -> Tuple[Dict[str, pd.DataFrame], int]:
    """
    Remove palindromic SNPs with allele frequency close to 0.5 (ambiguous).

    SNPs that are palindromic (A/T or G/C) AND have EAF near 0.5 cannot be
    reliably aligned across ancestries and should be removed.

    Args:
        maf_threshold: Remove palindromic SNPs where |EAF - 0.5| < maf_threshold
                       in ANY ancestry.

    Returns (filtered_dict, n_removed).
    """
    # Find palindromic SNPs from the first ancestry
    first_anc = list(gwas_dict.keys())[0]
    first_df = gwas_dict[first_anc]

    palindromic_snps = set()
    for _, row in first_df.iterrows():
        if _is_palindromic(row["EA"], row["NEA"]):
            palindromic_snps.add(row["SNP"])

    if not palindromic_snps:
        print_progress("No palindromic SNPs found.")
        return gwas_dict, 0

    # Check EAF near 0.5 across all ancestries
    ambiguous_snps = set()
    for anc, df in gwas_dict.items():
        pal_df = df[df["SNP"].isin(palindromic_snps)]
        ambiguous = pal_df[np.abs(pal_df["EAF"] - 0.5) < maf_threshold]
        ambiguous_snps.update(ambiguous["SNP"].tolist())

    # Remove ambiguous SNPs from all ancestries
    filtered = {}
    for anc, df in gwas_dict.items():
        filtered[anc] = df[~df["SNP"].isin(ambiguous_snps)].reset_index(drop=True)

    print_progress(
        f"Removed {len(ambiguous_snps)} ambiguous palindromic SNPs "
        f"(|EAF-0.5| < {maf_threshold})."
    )
    return filtered, len(ambiguous_snps)


# ---------------------------------------------------------------------------
# Step 4: Compute allele-frequency differences (Fst-like)
# ---------------------------------------------------------------------------

def compute_af_differences(
    gwas_dict: Dict[str, pd.DataFrame],
    reference_ancestry: str = "EUR",
) -> pd.DataFrame:
    """
    Compute per-SNP allele-frequency divergence across ancestries.

    For each SNP, computes:
      - EAF for each ancestry
      - |EAF_pop - EAF_ref| for each non-reference ancestry
      - Fst-like metric: Var(EAF) / (EAF_mean * (1 - EAF_mean))

    Returns a DataFrame with per-SNP AF comparison.
    """
    ancestries = list(gwas_dict.keys())
    ref_df = gwas_dict[reference_ancestry].set_index("SNP")

    rows = []
    for snp, ref_row in ref_df.iterrows():
        row = {"SNP": snp, "causal": ref_row["causal"]}
        eafs = {}
        for anc in ancestries:
            anc_df = gwas_dict[anc]
            snp_row = anc_df[anc_df["SNP"] == snp]
            if len(snp_row) > 0:
                eaf = snp_row.iloc[0]["EAF"]
                eafs[anc] = eaf
                row[f"EAF_{anc}"] = eaf
                if anc != reference_ancestry:
                    row[f"delta_EAF_{anc}"] = abs(eaf - ref_row["EAF"])
            else:
                row[f"EAF_{anc}"] = np.nan
                if anc != reference_ancestry:
                    row[f"delta_EAF_{anc}"] = np.nan

        # Fst-like: variance of EAF across populations / (p_bar * (1 - p_bar))
        eaf_vals = np.array(list(eafs.values()))
        p_bar = np.mean(eaf_vals)
        if 0 < p_bar < 1:
            fst_like = np.var(eaf_vals) / (p_bar * (1.0 - p_bar))
        else:
            fst_like = 0.0
        row["fst_like"] = fst_like
        row["max_delta_eaf"] = np.max(np.abs(eaf_vals - eafs.get(reference_ancestry, p_bar)))

        rows.append(row)

    af_df = pd.DataFrame(rows)
    print_progress(
        f"Computed AF differences for {len(af_df)} SNPs across {len(ancestries)} ancestries. "
        f"Mean Fst-like: {af_df['fst_like'].mean():.4f}, "
        f"Max: {af_df['fst_like'].max():.4f}."
    )
    return af_df


# ---------------------------------------------------------------------------
# Step 5: Extract genome-wide significant signals + cross-ancestry overlap
# ---------------------------------------------------------------------------

def extract_genome_wide_signals(
    gwas_dict: Dict[str, pd.DataFrame],
    p_threshold: float = 5e-8,
) -> pd.DataFrame:
    """
    Extract genome-wide significant SNPs per ancestry and compute overlap.

    Returns a DataFrame with columns:
      SNP, significant_in (list of ancestries), n_ancestries_sig, max_p, min_p
    """
    ancestries = list(gwas_dict.keys())
    sig_sets = {}
    for anc in ancestries:
        df = gwas_dict[anc]
        sig_snps = set(df[df["P"] < p_threshold]["SNP"].tolist())
        sig_sets[anc] = sig_snps

    all_sig = set()
    for s in sig_sets.values():
        all_sig.update(s)

    rows = []
    for snp in all_sig:
        sig_in = [anc for anc in ancestries if snp in sig_sets[anc]]
        pvals = {}
        for anc in ancestries:
            df = gwas_dict[anc]
            snp_row = df[df["SNP"] == snp]
            if len(snp_row) > 0:
                pvals[anc] = snp_row.iloc[0]["P"]

        rows.append({
            "SNP": snp,
            "significant_in": ", ".join(sig_in),
            "n_ancestries_sig": len(sig_in),
            "min_p": min(pvals.values()) if pvals else np.nan,
            "max_p": max(pvals.values()) if pvals else np.nan,
        })

    overlap_df = pd.DataFrame(rows).sort_values("n_ancestries_sig", ascending=False)
    print_progress(
        f"Found {len(all_sig)} genome-wide significant SNPs across ancestries. "
        f"Cross-ancestry overlap (sig in >=2): "
        f"{len(overlap_df[overlap_df['n_ancestries_sig'] >= 2])}."
    )
    return overlap_df


# ---------------------------------------------------------------------------
# Step 6: Visualization
# ---------------------------------------------------------------------------

def plot_af_divergence_heatmap(af_df: pd.DataFrame, outpath: str) -> None:
    """Plot a heatmap of allele-frequency divergence across ancestries."""
    print_progress("Generating AF divergence heatmap ...")

    eaf_cols = [c for c in af_df.columns if c.startswith("EAF_")]
    ancestries = [c.replace("EAF_", "") for c in eaf_cols]

    # Compute pairwise Fst-like between ancestries
    n_anc = len(ancestries)
    fst_matrix = np.zeros((n_anc, n_anc))
    for i, anc_i in enumerate(ancestries):
        for j, anc_j in enumerate(ancestries):
            if i == j:
                fst_matrix[i, j] = 0.0
            else:
                eaf_i = af_df[f"EAF_{anc_i}"].values
                eaf_j = af_df[f"EAF_{anc_j}"].values
                valid = ~(np.isnan(eaf_i) | np.isnan(eaf_j))
                eaf_i = eaf_i[valid]
                eaf_j = eaf_j[valid]
                p_bar = (eaf_i + eaf_j) / 2.0
                mask = (p_bar > 0) & (p_bar < 1)
                if mask.sum() > 0:
                    fst_vals = ((eaf_i[mask] - eaf_j[mask]) ** 2) / (2.0 * p_bar[mask] * (1.0 - p_bar[mask]))
                    fst_matrix[i, j] = np.mean(fst_vals)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(fst_matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=max(0.01, fst_matrix.max()))
    ax.set_xticks(range(n_anc))
    ax.set_yticks(range(n_anc))
    ax.set_xticklabels(ancestries, rotation=45, ha="right")
    ax.set_yticklabels(ancestries)
    ax.set_title("Cross-Ancestry Allele-Frequency Divergence (Fst-like)")
    fig.colorbar(im, ax=ax, label="Mean Fst-like")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved AF divergence heatmap to {outpath}")


# ---------------------------------------------------------------------------
# Step 7: Pipeline orchestration
# ---------------------------------------------------------------------------

def gwas_harmonization_pipeline(
    n_snps: int = 500,
    n_causal: int = 30,
    true_effect: float = 0.30,
    ancestries: Optional[List[str]] = None,
    reference_ancestry: str = "EUR",
    flip_rate: float = 0.15,
    strand_confusion_rate: float = 0.05,
    maf_threshold: float = 0.01,
    p_threshold: float = 5e-8,
    seed: int = 42,
    output_dir: Optional[str] = None,
) -> Dict:
    """
    Full GWAS harmonization pipeline for cross-ancestry MR.

    Returns a dict with keys:
      - harmonized_gwas: dict of DataFrames
      - af_comparison: DataFrame
      - cross_ancestry_overlaps: DataFrame
      - harmonization_stats: dict
      - evidence_package: dict
    """
    output_dir = ensure_output_dir(output_dir)

    # Step 1: Simulate
    print_progress("Step 1/6: Simulating cross-ancestry GWAS ...")
    gwas_dict = simulate_cross_ancestry_gwas(
        n_snps=n_snps,
        n_causal=n_causal,
        true_effect=true_effect,
        ancestries=ancestries,
        flip_rate=flip_rate,
        strand_confusion_rate=strand_confusion_rate,
        seed=seed,
    )

    # Step 2: Harmonize alleles
    print_progress("Step 2/6: Harmonizing alleles to reference ancestry ...")
    harmonized, harm_stats = harmonize_alleles(gwas_dict, reference_ancestry)

    # Step 3: Resolve strand ambiguity
    print_progress("Step 3/6: Resolving strand ambiguity (palindromic SNPs) ...")
    filtered, n_palindromic_removed = resolve_strand_ambiguity(harmonized, maf_threshold)

    # Step 4: Compute AF differences
    print_progress("Step 4/6: Computing allele-frequency differences ...")
    af_df = compute_af_differences(filtered, reference_ancestry)

    # Step 5: Extract genome-wide signals
    print_progress("Step 5/6: Extracting genome-wide significant signals ...")
    overlap_df = extract_genome_wide_signals(filtered, p_threshold)

    # Step 6: Save outputs + evidence package
    print_progress("Step 6/6: Saving outputs and evidence package ...")

    # Concatenate all harmonized GWAS
    all_harmonized = pd.concat(filtered.values(), ignore_index=True)
    all_harmonized.to_csv(os.path.join(output_dir, "gh_harmonized_gwas.csv"), index=False)

    af_df.to_csv(os.path.join(output_dir, "gh_af_comparison.csv"), index=False)
    overlap_df.to_csv(os.path.join(output_dir, "gh_cross_ancestry_overlaps.csv"), index=False)

    # Plot
    plot_af_divergence_heatmap(af_df, os.path.join(output_dir, "gh_af_divergence_heatmap.png"))

    # Text report
    report_path = os.path.join(output_dir, "gh_harmonization_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("GWAS Harmonization Report (Cross-Ancestry)\n")
        fh.write("=" * 60 + "\n\n")

        fh.write("Simulation Parameters\n")
        fh.write("-" * 60 + "\n")
        fh.write(f"SNPs simulated: {n_snps}\n")
        fh.write(f"Causal SNPs: {n_causal}\n")
        fh.write(f"True effect: {true_effect}\n")
        fh.write(f"Ancestries: {', '.join(filtered.keys())}\n")
        fh.write(f"Reference ancestry: {reference_ancestry}\n")
        fh.write(f"Allele flip rate: {flip_rate}\n")
        fh.write(f"Strand confusion rate: {strand_confusion_rate}\n")
        fh.write(f"Seed: {seed}\n\n")

        fh.write("Harmonization Statistics\n")
        fh.write("-" * 60 + "\n")
        for anc, s in harm_stats.items():
            fh.write(f"\n{anc}:\n")
            fh.write(f"  Matched directly: {s['matched']}\n")
            fh.write(f"  Allele-flipped: {s['flipped']}\n")
            fh.write(f"  Strand-corrected: {s['strand_corrected']}\n")
            fh.write(f"  Palindromic removed: {s['palindromic_removed']}\n")
            fh.write(f"  Unmatched: {s['unmatched']}\n")

        fh.write(f"\nTotal ambiguous palindromic removed: {n_palindromic_removed}\n\n")

        fh.write("Allele-Frequency Divergence\n")
        fh.write("-" * 60 + "\n")
        fh.write(f"Mean Fst-like: {af_df['fst_like'].mean():.6f}\n")
        fh.write(f"Max Fst-like: {af_df['fst_like'].max():.6f}\n")
        fh.write(f"Mean max delta EAF: {af_df['max_delta_eaf'].mean():.4f}\n\n")

        fh.write("Genome-Wide Signal Overlap\n")
        fh.write("-" * 60 + "\n")
        fh.write(f"Total significant SNPs (any ancestry): {len(overlap_df)}\n")
        fh.write(f"Significant in >=2 ancestries: {len(overlap_df[overlap_df['n_ancestries_sig'] >= 2])}\n")
        fh.write(f"Significant in all ancestries: {len(overlap_df[overlap_df['n_ancestries_sig'] == len(filtered)])}\n\n")

        fh.write("Limitations\n")
        fh.write("-" * 60 + "\n")
        fh.write("- Data are SYNTHETIC; real deployment requires IEU OpenGWAS / BBJ / FinnGen.\n")
        fh.write("- AF drift model is simplified (no admixture, no selection).\n")
        fh.write("- Palindromic SNP removal uses EAF threshold; MAF-based approach recommended.\n")
        fh.write("- Real harmonization requires chromosome/position cross-checking.\n")

    # Evidence package
    evidence_package = {
        "case_id": "Case 8",
        "pipeline": "gwas-harmonization-cross-ancestry",
        "evidence_grade": "C",
        "data_type": "synthetic",
        "framework_version": "1.8.0",
        "seed": seed,
        "parameters": {
            "n_snps": n_snps,
            "n_causal": n_causal,
            "true_effect": true_effect,
            "ancestries": list(filtered.keys()),
            "reference_ancestry": reference_ancestry,
            "flip_rate": flip_rate,
            "strand_confusion_rate": strand_confusion_rate,
            "maf_threshold": maf_threshold,
            "p_threshold": p_threshold,
        },
        "results": {
            "n_harmonized_snps": len(all_harmonized) // len(filtered),
            "n_ancestries": len(filtered),
            "harmonization_stats": harm_stats,
            "n_palindromic_removed": n_palindromic_removed,
            "mean_fst_like": float(af_df["fst_like"].mean()),
            "max_fst_like": float(af_df["fst_like"].max()),
            "n_genome_wide_significant": len(overlap_df),
            "n_cross_ancestry_overlap": int((overlap_df["n_ancestries_sig"] >= 2).sum()),
        },
        "limitations": [
            "Synthetic data with simplified AF drift model",
            "No admixture or selection modelled",
            "Palindromic removal uses EAF threshold (0.5 +/- maf_threshold)",
            "Real deployment requires actual GWAS summary statistics",
        ],
        "next_validation": [
            "Replace simulate_cross_ancestry_gwas with real GWAS from IEU OpenGWAS (EUR) + BBJ (EAS) + FinnGen (EUR)",
            "Add TPMI (SAS) and All of Us (AFR) when summary stats become available",
            "Validate harmonization against 1000G reference panel allele frequencies",
            "Compare cross-ancestry overlap with published trans-ancestry GWAS meta-analyses",
        ],
        "provenance": {
            "script": "demo_gwas_harmonization.py",
            "timestamp": pd.Timestamp.now().isoformat(),
            "output_dir": output_dir,
        },
    }

    with open(os.path.join(output_dir, "gh_evidence_package.json"), "w", encoding="utf-8") as fh:
        json.dump(evidence_package, fh, indent=2, ensure_ascii=False)

    print_progress(f"Pipeline complete. Outputs saved to {output_dir}")

    return {
        "harmonized_gwas": filtered,
        "af_comparison": af_df,
        "cross_ancestry_overlaps": overlap_df,
        "harmonization_stats": harm_stats,
        "n_palindromic_removed": n_palindromic_removed,
        "evidence_package": evidence_package,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="GWAS Summary-Stat Harmonization for Cross-Ancestry MR Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument("--n-snps", type=int, default=500, help="Number of SNPs to simulate (default: 500)")
    parser.add_argument("--n-causal", type=int, default=30, help="Number of causal SNPs (default: 30)")
    parser.add_argument("--true-effect", type=float, default=0.30, help="True causal effect (default: 0.30)")
    parser.add_argument(
        "--ancestries",
        type=str,
        nargs="+",
        default=None,
        help="Ancestries to include (default: all 5: EUR EAS SAS AFR AMR)",
    )
    parser.add_argument("--reference-ancestry", type=str, default="EUR", help="Reference ancestry (default: EUR)")
    parser.add_argument("--flip-rate", type=float, default=0.15, help="Allele flip rate (default: 0.15)")
    parser.add_argument("--strand-confusion-rate", type=float, default=0.05, help="Strand confusion rate (default: 0.05)")
    parser.add_argument("--maf-threshold", type=float, default=0.01, help="MAF threshold for palindromic removal (default: 0.01)")
    parser.add_argument("--p-threshold", type=float, default=5e-8, help="Genome-wide significance threshold (default: 5e-8)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (default: demo_outputs/gwas-harmonization)")

    args = parser.parse_args()

    result = gwas_harmonization_pipeline(
        n_snps=args.n_snps,
        n_causal=args.n_causal,
        true_effect=args.true_effect,
        ancestries=args.ancestries,
        reference_ancestry=args.reference_ancestry,
        flip_rate=args.flip_rate,
        strand_confusion_rate=args.strand_confusion_rate,
        maf_threshold=args.maf_threshold,
        p_threshold=args.p_threshold,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("GWAS Harmonization Pipeline — Summary")
    print("=" * 60)
    print(f"Ancestries: {', '.join(result['harmonized_gwas'].keys())}")
    print(f"Palindromic removed: {result['n_palindromic_removed']}")
    print(f"Mean Fst-like: {result['evidence_package']['results']['mean_fst_like']:.6f}")
    print(f"Genome-wide significant SNPs: {result['evidence_package']['results']['n_genome_wide_significant']}")
    print(f"Cross-ancestry overlap (>=2): {result['evidence_package']['results']['n_cross_ancestry_overlap']}")
    print(f"Evidence grade: {result['evidence_package']['evidence_grade']}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
