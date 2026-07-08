#!/usr/bin/env python3
"""
Demo: Causal Evidence Chain (GWAS -> eQTL -> coloc -> TWAS -> fine-mapping -> MR)
=================================================================================

A *methodology* engine that wires together the standard causal-evidence steps used
in modern integrative genomics, and validates each step against a known ground truth.

IMPORTANT (honesty): the data here are SYNTHETIC. The engine implements the real
math (approximate-Bayes-factor colocalization, S-PrediXcan-style TWAS, credible-set
fine-mapping, IVW MR) but the input GWAS/eQTL summary statistics are simulated with a
known causal structure. This validates that the *computations recover the planted
ground truth* — it is NOT an etiological claim about any real trait. For a real
deployment, swap `simulate_causal_chain` for summary statistics from IEU OpenGWAS /
eQTLGen / GTEx and point `next_validation` at those sources.

Steps demonstrated
------------------
  1. simulate_causal_chain  : build per-gene loci with 4 truth classes
                              (colocalized / eqtl_only / gwas_only / null)
  2. run_coloc              : 5-hypothesis colocalization (PP.H4) via ABF
  3. twas_z                 : S-PrediXcan-style TWAS Z for each gene
  4. fine_map_credible_set  : 95% credible set via per-SNP PIP
  5. wald_ratio_mr         : per-locus MR (Wald ratio) using the causal instrument
  6. causal_evidence_pipeline : orchestrates 2-5 + ground-truth recovery benchmark

Outputs (when run as a script):
  - {output_dir}/ce_per_gene_results.csv
  - {output_dir}/ce_credible_sets.csv
  - {output_dir}/ce_recovery_benchmark.csv
  - {output_dir}/ce_summary_report.txt
  - {output_dir}/ce_locus_heatmap.png   (coloc PP.H4 grid across genes x truth)

Usage:
  python demo_causal_evidence.py --n-genes 8 --snps-per-gene 12 --seed 42 --output-dir outputs/causal-evidence
"""

import argparse
import os
import sys
import textwrap
from typing import Dict, List, Tuple

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

# coloc default priors (Wallace 2013 / Giambartolomei 2014)
COLOC_P1 = 1e-4          # prior prob a SNP is associated with trait 1 (eQTL)
COLOC_P2 = 1e-4          # prior prob a SNP is associated with trait 2 (GWAS)
COLOC_P12 = 1e-5         # prior prob both traits share the same causal variant
# prior variance on the standardized effect under association
COLOC_PRIOR_VAR = 0.2 ** 2 / 0.3 ** 2   # ~0.444, standard coloc default


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
# 1. Synthetic causal chain
# ---------------------------------------------------------------------------
def simulate_causal_chain(
    n_genes: int = 8,
    snps_per_gene: int = 12,
    true_effect: float = 0.35,
    sample_size_eqtl: int = 35000,
    sample_size_gwas: int = 350000,
    seed: int = 42,
) -> Dict:
    """
    Simulate per-gene loci with a planted causal structure.

    Each gene owns a locus of `snps_per_gene` SNPs. We assign every gene one of four
    truth classes:
      - 'colocalized' : a SINGLE causal SNP drives BOTH eQTL and GWAS (same variant) ->
                        the two signals should colocalize (PP.H4 high), TWAS significant,
                        and the causal SNP should fall in the fine-mapping credible set.
      - 'eqtl_only'   : a causal SNP drives eQTL but NOT GWAS -> PP.H4 low, TWAS null,
                        credible set on GWAS should miss it.
      - 'gwas_only'   : a (different) causal SNP drives GWAS but NOT eQTL -> PP.H4 low,
                        TWAS null (weights uncorrelated with trait), credible set catches
                        the GWAS causal SNP.
      - 'null'        : pure polygenic background, no real signal.

    Returns a dict with per-gene DataFrames and a truth table.
    """
    rng = np.random.default_rng(seed)

    # truth class assignment: at least a few colocalized genes for a meaningful benchmark
    n_coloc = max(2, n_genes // 3)
    n_eqtl_only = max(1, n_genes // 5)
    n_gwas_only = max(1, n_genes // 5)
    n_null = n_genes - n_coloc - n_eqtl_only - n_gwas_only
    if n_null < 0:  # guard against small n_genes
        n_coloc = max(1, n_genes - 3)
        n_eqtl_only = 1
        n_gwas_only = 1
        n_null = n_genes - n_coloc - n_eqtl_only - n_gwas_only

    classes = (["colocalized"] * n_coloc +
               ["eqtl_only"] * n_eqtl_only +
               ["gwas_only"] * n_gwas_only +
               ["null"] * max(0, n_null))
    rng.shuffle(classes)

    gene_dfs = []
    truth_rows = []

    for gi, cls in enumerate(classes):
        n = snps_per_gene
        maf = rng.uniform(0.05, 0.50, size=n)

        # background: ZERO under the coloc "one causal variant per trait" model.
        # (Sampling error is captured entirely by se_expr/se_trait, so the TWAS
        #  denominator stays calibrated. Polygenic background can be added later
        #  by inflating se instead of adding independent noise.)
        beta_expr = np.zeros(n)
        beta_trait = np.zeros(n)

        causal_eqtl = rng.integers(n)        # SNP driving eQTL (if any)
        causal_gwas = rng.integers(n)        # SNP driving GWAS (if any)

        if cls in ("colocalized", "eqtl_only"):
            # guarantee a strong, detectable eQTL at the causal SNP (random sign)
            s_eq = rng.choice([-1, 1])
            eql_mag = 0.15 + abs(rng.normal(loc=0.0, scale=0.05))
            beta_expr[causal_eqtl] += s_eq * eql_mag
        if cls in ("colocalized", "gwas_only"):
            if cls == "colocalized":
                # SAME SNP drives the trait, linked to expression by true_effect (MR chain)
                beta_trait[causal_eqtl] += true_effect * beta_expr[causal_eqtl]
                causal_gwas = causal_eqtl
            else:
                s_gw = rng.choice([-1, 1])
                beta_trait[causal_gwas] += s_gw * (0.15 + abs(rng.normal(loc=0.0, scale=0.05)))

        # sampling error
        se_expr = np.sqrt(1.0 / (sample_size_eqtl * 2.0 * maf * (1.0 - maf)))
        se_trait = np.sqrt(1.0 / (sample_size_gwas * 2.0 * maf * (1.0 - maf)))

        obs_expr = beta_expr + rng.normal(loc=0.0, scale=se_expr)
        obs_trait = beta_trait + rng.normal(loc=0.0, scale=se_trait)

        gene_id = f"GENE{gi:02d}"
        df = pd.DataFrame({
            "gene": gene_id,
            "snp": [f"{gene_id}_rs{j}" for j in range(n)],
            "beta_expr": obs_expr,
            "se_expr": se_expr,
            "beta_trait": obs_trait,
            "se_trait": se_trait,
            "maf": maf,
        })
        gene_dfs.append(df)
        truth_rows.append({
            "gene": gene_id,
            "truth_class": cls,
            "causal_eqtl_snp": f"{gene_id}_rs{causal_eqtl}",
            "causal_gwas_snp": f"{gene_id}_rs{causal_gwas}",
            "true_effect": true_effect if cls in ("colocalized", "gwas_only") else 0.0,
        })

    truth = pd.DataFrame(truth_rows)
    print_progress(
        f"Simulated {n_genes} genes ({n_coloc} colocalized, {n_eqtl_only} eQTL-only, "
        f"{n_gwas_only} GWAS-only, {max(0, n_null)} null)."
    )
    return {"gene_dfs": gene_dfs, "truth": truth,
            "params": {"n_genes": n_genes, "snps_per_gene": snps_per_gene,
                       "true_effect": true_effect,
                       "sample_size_eqtl": sample_size_eqtl,
                       "sample_size_gwas": sample_size_gwas, "seed": seed}}


# ---------------------------------------------------------------------------
# 2. Colocalization (5-hypothesis ABF)
# ---------------------------------------------------------------------------
def coloc_abf(beta1, se1, beta2, se2, prior_var: float = COLOC_PRIOR_VAR):
    """
    Per-SNP approximate Bayes factors (natural log) for association with each trait.

    lbf1_j = 0.5*(log(V) - log(V + se1^2)) + beta1^2 * V / (2*se1^2*(V + se1^2))
    """
    V = prior_var
    lbf1 = (0.5 * (np.log(V) - np.log(V + se1 ** 2))
            + (beta1 ** 2 * V) / (2 * se1 ** 2 * (V + se1 ** 2)))
    lbf2 = (0.5 * (np.log(V) - np.log(V + se2 ** 2))
            + (beta2 ** 2 * V) / (2 * se2 ** 2 * (V + se2 ** 2)))
    return lbf1, lbf2


def run_coloc(beta_expr, se_expr, beta_trait, se_trait,
              p1: float = COLOC_P1, p2: float = COLOC_P2, p12: float = COLOC_P12,
              prior_var: float = COLOC_PRIOR_VAR) -> Dict[str, float]:
    """
    Full 5-hypothesis colocalization (Giambartolomei 2014 / Wallace 2013).

    H0: neither associated
    H1: trait1 (eQTL) associated only
    H2: trait2 (GWAS) associated only
    H3: both associated, distinct causal variants
    H4: both associated, SAME causal variant  -> the colocalization signal

    Under the "one causal variant per trait" model:
      E0 = 1
      E1 = sum_j exp(a1_j)
      E2 = sum_j exp(a2_j)
      E3 = (sum_j exp(a1_j))*(sum_j exp(a2_j)) - sum_j exp(a1_j + a2_j)
      E4 = sum_j exp(a1_j + a2_j)
    Posteriors = E_h * prior_h / normalizer.
    """
    from scipy.special import logsumexp

    a1, a2 = coloc_abf(beta_expr, se_expr, beta_trait, se_trait, prior_var)

    logE0 = 0.0
    logE1 = float(logsumexp(a1))
    logE2 = float(logsumexp(a2))
    logE4 = float(logsumexp(a1 + a2))
    # E3 = E1*E2 - E4, kept in log-space (raw products overflow to inf for strong
    # signals, turning inf-inf into NaN). Since E1*E2 >= E4 always:
    logE12 = logE1 + logE2
    diff_log = logE4 - logE12          # <= 0
    # E3 = E1*E2 - E4; when E4 ~= E1*E2 (strong colocalization) E3 -> 0 and
    # log1p(-1) -> -inf is the correct limit; guard to avoid the RuntimeWarning.
    exp_diff = float(np.exp(diff_log))  # in (0, 1]
    if exp_diff >= 1.0 - 1e-15:
        logE3 = -np.inf
    else:
        logE3 = logE12 + float(np.log1p(-exp_diff))  # = log(E1*E2 - E4)

    lp0 = np.log((1 - p1) * (1 - p2))
    lp1 = np.log(p1) + np.log(1 - p2)
    lp2 = np.log(p2) + np.log(1 - p1)
    lp3 = np.log(p1) + np.log(p2)
    lp4 = np.log(p12)

    logpost = np.array([logE0 + lp0, logE1 + lp1, logE2 + lp2, logE3 + lp3, logE4 + lp4])
    post = np.exp(logpost - logsumexp(logpost))

    return {
        "PP.H0": float(post[0]),
        "PP.H1": float(post[1]),
        "PP.H2": float(post[2]),
        "PP.H3": float(post[3]),
        "PP.H4": float(post[4]),
    }


# ---------------------------------------------------------------------------
# 3. TWAS (S-PrediXcan style)
# ---------------------------------------------------------------------------
def twas_z(weights, beta_trait, se_trait) -> Dict[str, float]:
    """
    S-PrediXcan-style TWAS Z-test for association between genetically regulated
    expression (weights w_j) and the trait.

    Under independence of SNPs:
      numerator   = sum_j w_j * beta_trait_j
      denominator = sqrt(sum_j (w_j * se_trait_j)^2)
      Z           = numerator / denominator
    """
    w = np.asarray(weights, dtype=float)
    bt = np.asarray(beta_trait, dtype=float)
    st = np.asarray(se_trait, dtype=float)

    numerator = float(np.sum(w * bt))
    denom = float(np.sqrt(np.sum((w * st) ** 2)))
    if denom <= 0:
        z = 0.0
    else:
        z = numerator / denom
    p = 2.0 * stats.norm.sf(abs(z))
    return {"z": z, "p_value": p, "n_effect": len(w)}


# ---------------------------------------------------------------------------
# 4. Fine-mapping (credible set)
# ---------------------------------------------------------------------------
def fine_map_credible_set(beta, se, prior_var: float = COLOC_PRIOR_VAR,
                          coverage: float = 0.95) -> Dict:
    """
    Per-SNP posterior inclusion probability (PIP) under association via ABF, then a
    95% credible set (SNPs ordered by PIP until cumulative coverage reached).

    PIP_j = BF_j / (1 + BF_j), BF_j = exp(lbf_j); normalized to sum to 1 over the locus.
    """
    from scipy.special import expit

    V = prior_var
    lbf = (0.5 * (np.log(V) - np.log(V + se ** 2))
           + (beta ** 2 * V) / (2 * se ** 2 * (V + se ** 2)))
    # PIP = BF / (1 + BF) = sigmoid(lbf), numerically stable for large |lbf|
    pip = expit(lbf)
    # normalize (so credible set covers the locus's total association mass)
    pip = pip / pip.sum()

    order = np.argsort(-pip)
    cum = np.cumsum(pip[order])
    n_cs = int(np.searchsorted(cum, coverage) + 1)
    n_cs = min(n_cs, len(pip))
    cs_mask = np.zeros(len(pip), dtype=bool)
    cs_mask[order[:n_cs]] = True

    return {"pip": pip, "credible_set_mask": cs_mask, "n_cs": int(n_cs)}


# ---------------------------------------------------------------------------
# 5. Per-locus MR (Wald ratio)
# ---------------------------------------------------------------------------
def wald_ratio_mr(beta_expr, se_expr, beta_trait, se_trait,
                  instrument_idx: int) -> Dict[str, float]:
    """
    Two-stage / Wald-ratio MR at a single locus using the planted causal instrument.
    Estimate = beta_trait[instr] / beta_expr[instr].
    """
    bx = beta_expr[instrument_idx]
    by = beta_trait[instrument_idx]
    se_x = se_expr[instrument_idx]
    se_y = se_trait[instrument_idx]
    if abs(bx) < 1e-12:
        return {"beta": float("nan"), "se": float("nan"), "p_value": float("nan"),
                "ci_lower": float("nan"), "ci_upper": float("nan")}
    beta = by / bx
    se = abs(beta) * np.sqrt((se_y / by) ** 2 + (se_x / bx) ** 2)
    z = beta / se
    p = 2.0 * stats.norm.sf(abs(z))
    return {"beta": float(beta), "se": float(se),
            "ci_lower": float(beta - 1.96 * se), "ci_upper": float(beta + 1.96 * se),
            "p_value": float(p)}


# ---------------------------------------------------------------------------
# 6. Pipeline + ground-truth recovery benchmark
# ---------------------------------------------------------------------------
def causal_evidence_pipeline(sim: Dict, coloc_threshold: float = 0.8,
                             twas_alpha: float = 0.05) -> Dict:
    """
    Run coloc + TWAS + fine-mapping + MR for every gene, then score how well the
    planted ground truth is recovered.
    """
    gene_dfs = sim["gene_dfs"]
    truth = sim["truth"]

    per_gene = []
    credible_rows = []
    true_in_cs = []
    twas_recovered = []
    coloc_recovered = []

    for df in gene_dfs:
        gene = df["gene"].iloc[0]
        be, se_e = df["beta_expr"].values, df["se_expr"].values
        bt, se_t = df["beta_trait"].values, df["se_trait"].values

        # coloc
        coloc = run_coloc(be, se_e, bt, se_t)
        # TWAS (weights = eQTL effects)
        twas = twas_z(be, bt, se_t)
        # fine-map on the GWAS trait
        fm = fine_map_credible_set(bt, se_t)
        # MR using the eQTL causal SNP as instrument (works best for colocalized)
        trow = truth[truth["gene"] == gene].iloc[0]
        instr_label = trow["causal_eqtl_snp"]
        instr_idx = df.index[df["snp"] == instr_label][0]
        mr = wald_ratio_mr(be, se_e, bt, se_t, instr_idx)

        per_gene.append({
            "gene": gene,
            "truth_class": trow["truth_class"],
            "PP.H4": coloc["PP.H4"],
            "PP.H3": coloc["PP.H3"],
            "twas_z": twas["z"],
            "twas_p": twas["p_value"],
            "twas_significant": bool(twas["p_value"] < twas_alpha),
            "mr_beta": mr["beta"],
            "mr_p": mr["p_value"],
            "n_credible": fm["n_cs"],
        })

        # credible set rows
        for j, snp in enumerate(df["snp"].values):
            credible_rows.append({
                "gene": gene,
                "snp": snp,
                "pip": fm["pip"][j],
                "in_credible_set": bool(fm["credible_set_mask"][j]),
            })

        # ground-truth checks
        truth_snp = trow["causal_gwas_snp"] if trow["truth_class"] in ("colocalized", "gwas_only") \
            else trow["causal_eqtl_snp"]
        truth_idx = df.index[df["snp"] == truth_snp][0]
        true_in_cs.append(bool(fm["credible_set_mask"][truth_idx]))

        # coloc recovery: truth==colocalized -> PP.H4 > threshold
        if trow["truth_class"] == "colocalized":
            coloc_recovered.append(bool(coloc["PP.H4"] > coloc_threshold))
        else:
            coloc_recovered.append(bool(coloc["PP.H4"] <= coloc_threshold))

        # TWAS recovery: truth in (colocalized, gwas_only via expression proxy?) ->
        # Only colocalized genes have expression causally linked to trait.
        if trow["truth_class"] == "colocalized":
            twas_recovered.append(bool(twas["p_value"] < twas_alpha))
        else:
            twas_recovered.append(bool(twas["p_value"] >= twas_alpha))

    per_gene_df = pd.DataFrame(per_gene)
    cred_df = pd.DataFrame(credible_rows)

    # aggregate benchmark
    n_coloc = int((per_gene_df["truth_class"] == "colocalized").sum())
    benchmark = {
        "coloc_recovered_rate": float(np.mean(coloc_recovered)) if coloc_recovered else 0.0,
        "twas_recovered_rate": float(np.mean(twas_recovered)) if twas_recovered else 0.0,
        "finemap_true_in_cs_rate": float(np.mean(true_in_cs)) if true_in_cs else 0.0,
        "n_genes": len(per_gene_df),
        "n_colocalized": n_coloc,
    }
    return {"per_gene": per_gene_df, "credible": cred_df, "benchmark": benchmark}


def sweep_benchmark(n_genes: int = 8, snps_per_gene: int = 12,
                    effects=(0.2, 0.35, 0.5), seeds=(1, 2, 3, 42),
                    sample_size_gwas: int = 350000, sample_size_eqtl: int = 35000) -> pd.DataFrame:
    """
    Sweep over true effect sizes and seeds to confirm the engine recovers ground truth
    robustly (not a single lucky draw).
    """
    rows = []
    for eff in effects:
        for sd in seeds:
            sim = simulate_causal_chain(n_genes=n_genes, snps_per_gene=snps_per_gene,
                                        true_effect=eff, seed=sd,
                                        sample_size_gwas=sample_size_gwas,
                                        sample_size_eqtl=sample_size_eqtl)
            res = causal_evidence_pipeline(sim)
            b = res["benchmark"]
            rows.append({
                "true_effect": eff,
                "seed": sd,
                "coloc_rate": b["coloc_recovered_rate"],
                "twas_rate": b["twas_recovered_rate"],
                "finemap_rate": b["finemap_true_in_cs_rate"],
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def plot_coloc_grid(per_gene_df: pd.DataFrame, truth: pd.DataFrame, outpath: str) -> None:
    """Heatmap of PP.H4 by gene, colored by truth class (sanity visual)."""
    df = per_gene_df.sort_values("gene")
    classes = df["truth_class"].values
    h4 = df["PP.H4"].values.reshape(-1, 1)

    fig, ax = plt.subplots(figsize=(4, max(3, 0.5 * len(df) + 1)))
    im = ax.imshow(h4, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([f"{g} ({c})" for g, c in zip(df["gene"], classes)])
    ax.set_xticks([0])
    ax.set_xticklabels(["PP.H4"])
    for i, v in enumerate(h4[:, 0]):
        ax.text(0, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v < 0.5 else "black", fontsize=8)
    ax.set_title("Colocalization PP.H4 by gene (truth class in label)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print_progress(f"Saved coloc grid to {outpath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Causal Evidence Chain (coloc + TWAS + fine-mapping + MR) — methodology demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument("--n-genes", type=int, default=8)
    parser.add_argument("--snps-per-gene", type=int, default=12)
    parser.add_argument("--true-effect", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-sweep", action="store_true", help="skip the robustness sweep")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    out_dir = ensure_output_dir(args.output_dir)
    sim = simulate_causal_chain(
        n_genes=args.n_genes, snps_per_gene=args.snps_per_gene,
        true_effect=args.true_effect, seed=args.seed,
    )
    res = causal_evidence_pipeline(sim)
    per_gene_df = res["per_gene"]
    cred_df = res["credible"]
    benchmark = res["benchmark"]

    per_gene_df.to_csv(os.path.join(out_dir, "ce_per_gene_results.csv"), index=False)
    cred_df.to_csv(os.path.join(out_dir, "ce_credible_sets.csv"), index=False)

    # sweep
    if not args.no_sweep:
        sweep_df = sweep_benchmark(n_genes=args.n_genes, snps_per_gene=args.snps_per_gene)
        sweep_df.to_csv(os.path.join(out_dir, "ce_recovery_benchmark.csv"), index=False)
    else:
        sweep_df = None

    plot_coloc_grid(per_gene_df, sim["truth"], os.path.join(out_dir, "ce_locus_heatmap.png"))

    # summary report
    report_path = os.path.join(out_dir, "ce_summary_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("Causal Evidence Chain — Synthetic Validation Report\n")
        fh.write("=" * 64 + "\n\n")
        fh.write(f"Genes simulated : {benchmark['n_genes']} ({benchmark['n_colocalized']} colocalized)\n")
        fh.write(f"Coloc recovery  : {benchmark['coloc_recovered_rate']:.2f} "
                 f"(fraction of genes with correct PP.H4 call)\n")
        fh.write(f"TWAS recovery   : {benchmark['twas_recovered_rate']:.2f}\n")
        fh.write(f"Fine-map (true SNP in 95% CS): {benchmark['finemap_true_in_cs_rate']:.2f}\n\n")
        fh.write("Per-gene results:\n")
        fh.write(per_gene_df.to_string(index=False))
        fh.write("\n\nLIMITATIONS\n")
        fh.write("- Synthetic data; validates computation, not real etiological claims.\n")
        fh.write("- No LD structure modelled (SNPs treated independent); real fine-mapping needs LD.\n")
        fh.write("- Single causal variant per trait assumed (standard coloc model).\n")
        fh.write("- next_validation: IEU OpenGWAS + eQTLGen/GTEx real summary stats.\n")
    print_progress(f"Saved summary to {report_path}")

    print("\n" + "=" * 64)
    print("Causal Evidence Chain Complete (SYNTHETIC validation)")
    print("=" * 64)
    print(f"Genes              : {benchmark['n_genes']} ({benchmark['n_colocalized']} colocalized)")
    print(f"Coloc recovery     : {benchmark['coloc_recovered_rate']:.2f}")
    print(f"TWAS recovery      : {benchmark['twas_recovered_rate']:.2f}")
    print(f"Fine-map recovery  : {benchmark['finemap_true_in_cs_rate']:.2f}")
    print(f"Per-gene CSV       : {os.path.join(out_dir, 'ce_per_gene_results.csv')}")
    print(f"Credible sets CSV  : {os.path.join(out_dir, 'ce_credible_sets.csv')}")
    print(f"Coloc heatmap      : {os.path.join(out_dir, 'ce_locus_heatmap.png')}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
