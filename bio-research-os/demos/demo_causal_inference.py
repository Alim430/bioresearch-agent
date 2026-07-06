#!/usr/bin/env python3
"""
Demo 3: Causal Inference Workflow (Mendelian Randomization)
============================================================
Demonstrates a two-sample Mendelian Randomization (MR) pipeline:
  1. Simulate realistic GWAS summary statistics for exposure (BMI) and outcome (Type 2 Diabetes)
  2. Select genome-wide significant SNP instruments (p < 5e-8)
  3. Perform Inverse-Variance Weighted (IVW) MR
  4. Sensitivity: leave-one-out analysis
  5. Generate MR scatter plot and funnel plot
  6. Output causal effect estimate with interpretation

Outputs:
  - {output_dir}/causal_ivw_results.csv
  - {output_dir}/causal_loo_results.csv
  - {output_dir}/causal_mr_scatter.png
  - {output_dir}/causal_mr_funnel.png
  - {output_dir}/causal_interpretation.txt

Usage:
  python demo_causal_inference.py --exposure "BMI" --outcome "Type 2 Diabetes" --n_snps 120 --seed 42 --output-dir outputs/causal
"""

import argparse
import os
import sys
import textwrap
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")
GWAS_P_THRESHOLD = 5e-8


def ensure_output_dir(output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    print(f"[PROGRESS] {msg}", file=sys.stderr)


def simulate_gwas_summary(
    n_snps: int = 120,
    true_effect: float = 0.35,
    exposure_h2: float = 0.25,
    outcome_h2: float = 0.15,
    sample_size_exposure: int = 350000,
    sample_size_outcome: int = 900000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simulate GWAS summary statistics for MR.

    Model:
      - Each SNP has an effect on exposure (beta_x) drawn from a normal distribution.
      - A subset of SNPs are 'causal' (affect exposure and, via exposure, affect outcome).
      - Outcome effect (beta_y) = true_effect * beta_x + noise (pleiotropy).
      - SEs are computed from sample size and MAF using approximate formula.

    Returns a DataFrame with columns:
      SNP, beta_exposure, se_exposure, p_exposure,
      beta_outcome, se_outcome, p_outcome, maf, causal
    """
    rng = np.random.default_rng(seed)

    # Minor allele frequencies
    maf = rng.uniform(0.05, 0.50, size=n_snps)

    # Exposure effect sizes (standardized)
    # Under infinitesimal model-ish, but let's make ~15% causal with larger effects
    causal = np.zeros(n_snps, dtype=bool)
    causal_idx = rng.choice(n_snps, size=max(1, int(0.15 * n_snps)), replace=False)
    causal[causal_idx] = True

    beta_x = np.zeros(n_snps)
    # Non-causal: small polygenic background
    beta_x[~causal] = rng.normal(loc=0.0, scale=0.005, size=(~causal).sum())
    # Causal: stronger effects
    beta_x[causal] = rng.normal(loc=0.0, scale=0.08, size=causal.sum())

    # Compute approximate SE for exposure
    # Var(beta_hat) ≈ 1 / (N * 2 * MAF * (1 - MAF))
    var_x = 1.0 / (sample_size_exposure * 2.0 * maf * (1.0 - maf))
    se_x = np.sqrt(var_x)

    # Simulate observed beta_x with sampling error
    obs_beta_x = beta_x + rng.normal(loc=0.0, scale=se_x)
    z_x = obs_beta_x / se_x
    p_x = 2.0 * stats.norm.sf(np.abs(z_x))

    # Outcome effects
    # Direct effect via exposure + pleiotropic noise
    pleiotropy = rng.normal(loc=0.0, scale=0.01, size=n_snps)
    beta_y = true_effect * beta_x + pleiotropy

    var_y = 1.0 / (sample_size_outcome * 2.0 * maf * (1.0 - maf))
    se_y = np.sqrt(var_y)

    obs_beta_y = beta_y + rng.normal(loc=0.0, scale=se_y)
    z_y = obs_beta_y / se_y
    p_y = 2.0 * stats.norm.sf(np.abs(z_y))

    df = pd.DataFrame({
        "SNP": [f"rs{1000000 + i}" for i in range(n_snps)],
        "beta_exposure": obs_beta_x,
        "se_exposure": se_x,
        "p_exposure": p_x,
        "beta_outcome": obs_beta_y,
        "se_outcome": se_y,
        "p_outcome": p_y,
        "maf": maf,
        "causal": causal,
    })
    print_progress(f"Simulated {n_snps} SNPs; {causal.sum()} causal for exposure.")
    return df


def select_instruments(df: pd.DataFrame, p_thresh: float = GWAS_P_THRESHOLD) -> pd.DataFrame:
    """
    Select SNPs that are genome-wide significant for the exposure.
    Apply basic clumping heuristic: sort by p-value, iterate and keep if not too correlated.
    Since we don't have LD here, we just keep the top SNPs by significance as a proxy.
    """
    sig = df[df["p_exposure"] < p_thresh].copy()
    if sig.empty:
        print_progress("No SNPs reached genome-wide significance; relaxing threshold to top 20 by p-value.")
        sig = df.nsmallest(20, "p_exposure").copy()
    sig = sig.sort_values("p_exposure").reset_index(drop=True)
    print_progress(f"Selected {len(sig)} instrument SNPs (p < {p_thresh:.0e} or top 20).")
    return sig


def ivw_mr(instruments: pd.DataFrame) -> Dict[str, float]:
    """
    Inverse-Variance Weighted (IVW) Mendelian Randomization.
    Estimates causal effect of exposure on outcome using Wald ratios.

    Wald ratio for SNP i: beta_y_i / beta_x_i
    IVW estimate = sum(beta_y_i * beta_x_i / se_y_i^2) / sum(beta_x_i^2 / se_y_i^2)
    """
    bx = instruments["beta_exposure"].values
    by = instruments["beta_outcome"].values
    se_y = instruments["se_outcome"].values

    # Avoid division by zero
    weights = (bx ** 2) / (se_y ** 2)
    numerator = (bx * by) / (se_y ** 2)

    beta_ivw = np.sum(numerator) / np.sum(weights)
    se_ivw = np.sqrt(1.0 / np.sum(weights))

    # Cochran's Q for heterogeneity
    wald_ratios = by / bx
    q = np.sum((wald_ratios - beta_ivw) ** 2 * weights)
    df_q = len(instruments) - 1
    p_het = 1.0 - stats.chi2.cdf(q, df_q) if df_q > 0 else 1.0

    z = beta_ivw / se_ivw
    p_value = 2.0 * stats.norm.sf(abs(z))

    # 95% CI
    ci_lower = beta_ivw - 1.96 * se_ivw
    ci_upper = beta_ivw + 1.96 * se_ivw

    return {
        "method": "IVW",
        "n_snps": len(instruments),
        "beta": beta_ivw,
        "se": se_ivw,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_value": p_value,
        "cochrans_q": q,
        "p_het": p_het,
    }


def leave_one_out_mr(instruments: pd.DataFrame) -> pd.DataFrame:
    """
    Perform leave-one-out IVW: drop each SNP in turn and re-estimate the causal effect.
    """
    print_progress("Running leave-one-out sensitivity analysis ...")
    rows = []
    for i in range(len(instruments)):
        subset = instruments.drop(instruments.index[i])
        res = ivw_mr(subset)
        rows.append({
            "excluded_snp": instruments.iloc[i]["SNP"],
            "beta_ivw": res["beta"],
            "se_ivw": res["se"],
            "ci_lower": res["ci_lower"],
            "ci_upper": res["ci_upper"],
            "p_value": res["p_value"],
        })
    return pd.DataFrame(rows)


def plot_mr_scatter(instruments: pd.DataFrame, ivw_result: Dict, outpath: str) -> None:
    """
    MR scatter plot: outcome effect (y) vs exposure effect (x) per SNP,
    with IVW regression line.
    """
    print_progress("Generating MR scatter plot ...")
    plt.figure(figsize=(10, 8))
    bx = instruments["beta_exposure"]
    by = instruments["beta_outcome"]
    # Error bars
    plt.errorbar(bx, by, xerr=instruments["se_exposure"], yerr=instruments["se_outcome"],
                 fmt="o", color="steelblue", ecolor="lightgray", elinewidth=1, capsize=2, alpha=0.7)

    # IVW line
    xlim = plt.xlim()
    x_vals = np.array(xlim)
    y_vals = ivw_result["beta"] * x_vals
    plt.plot(x_vals, y_vals, color="crimson", linewidth=2, label=f"IVW slope = {ivw_result['beta']:.3f}")

    plt.axhline(0, color="black", linestyle="-", linewidth=0.5)
    plt.axvline(0, color="black", linestyle="-", linewidth=0.5)
    plt.xlabel("SNP effect on exposure (BMI)")
    plt.ylabel("SNP effect on outcome (Type 2 Diabetes)")
    plt.title("MR Scatter Plot: BMI → Type 2 Diabetes")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved MR scatter plot to {outpath}")


def plot_funnel(instruments: pd.DataFrame, ivw_result: Dict, outpath: str) -> None:
    """
    Funnel plot of Wald ratio precision vs Wald ratio estimate.
    """
    print_progress("Generating funnel plot ...")
    wald = instruments["beta_outcome"] / instruments["beta_exposure"]
    precision = 1.0 / np.abs(wald)  # approximate; ideally use SE of Wald ratio
    # Better: SE(wald) ≈ |by/bx| * sqrt((se_y/by)^2 + (se_x/bx)^2)
    se_wald = np.abs(wald) * np.sqrt((instruments["se_outcome"] / instruments["beta_outcome"]) ** 2 +
                                      (instruments["se_exposure"] / instruments["beta_exposure"]) ** 2)
    precision = 1.0 / se_wald

    plt.figure(figsize=(9, 7))
    plt.scatter(wald, precision, color="steelblue", alpha=0.7, edgecolors="black", linewidths=0.5)
    plt.axvline(ivw_result["beta"], color="crimson", linestyle="--", linewidth=2, label=f"IVW estimate = {ivw_result['beta']:.3f}")
    plt.xlabel("Wald Ratio (beta_outcome / beta_exposure)")
    plt.ylabel("Precision (1 / SE)")
    plt.title("Funnel Plot: IVW Mendelian Randomization")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved funnel plot to {outpath}")


def generate_interpretation(ivw: Dict, loo_df: pd.DataFrame, outpath: str) -> None:
    """Write a plain-text interpretation of MR results."""
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write("Mendelian Randomization Interpretation Report\n")
        fh.write("=" * 60 + "\n\n")
        fh.write("Study Design\n")
        fh.write("-" * 60 + "\n")
        fh.write("Exposure: Body Mass Index (BMI)\n")
        fh.write("Outcome: Type 2 Diabetes (T2D)\n")
        fh.write(f"Instrument SNPs: {ivw['n_snps']}\n\n")

        fh.write("Primary IVW Result\n")
        fh.write("-" * 60 + "\n")
        fh.write(f"Causal effect estimate (beta): {ivw['beta']:.4f}\n")
        fh.write(f"Standard error               : {ivw['se']:.4f}\n")
        fh.write(f"95% Confidence interval      : [{ivw['ci_lower']:.4f}, {ivw['ci_upper']:.4f}]\n")
        fh.write(f"P-value                      : {ivw['p_value']:.2e}\n")
        fh.write(f"Cochran's Q                  : {ivw['cochrans_q']:.2f}\n")
        fh.write(f"Heterogeneity p-value        : {ivw['p_het']:.3f}\n\n")

        fh.write("Interpretation\n")
        fh.write("-" * 60 + "\n")
        if ivw["p_value"] < 0.05:
            fh.write("The IVW estimate suggests a statistically significant causal effect of BMI on T2D risk.\n")
            if ivw["beta"] > 0:
                fh.write("Direction: Higher genetically predicted BMI is associated with increased T2D risk.\n")
            else:
                fh.write("Direction: Higher genetically predicted BMI is associated with decreased T2D risk.\n")
        else:
            fh.write("The IVW estimate does not reach statistical significance; evidence for a causal effect is weak.\n")

        if ivw["p_het"] < 0.05:
            fh.write("WARNING: Significant heterogeneity detected (Cochran's Q p < 0.05).\n")
            fh.write("This may indicate horizontal pleiotropy or that the NO ME (instrument strength independent of direct effect) assumption is violated.\n")
        else:
            fh.write("No significant heterogeneity detected, supporting the validity of the IVW assumption.\n")

        fh.write("\n")
        fh.write("Leave-One-Out Sensitivity\n")
        fh.write("-" * 60 + "\n")
        # Check if any single SNP drives the result
        loo_range = loo_df["beta_ivw"].max() - loo_df["beta_ivw"].min()
        fh.write(f"Range of LOO estimates: {loo_range:.4f}\n")
        if loo_range < 2 * ivw["se"]:
            fh.write("The estimate is robust to leaving out individual SNPs.\n")
        else:
            fh.write("Caution: Some SNPs may be influential; consider outlier removal or robust MR methods (e.g., MR-Egger, weighted median).\n")

        fh.write("\n")
        fh.write("Limitations\n")
        fh.write("-" * 60 + "\n")
        fh.write("- This demo uses synthetic GWAS data for illustration.\n")
        fh.write("- Real-world MR requires rigorous LD clumping, harmonization, and sensitivity analyses.\n")
        fh.write("- Population stratification, sample overlap, and weak instrument bias should be assessed.\n")

    print_progress(f"Saved interpretation to {outpath}")


def main():
    parser = argparse.ArgumentParser(
        description="Causal Inference Workflow (Mendelian Randomization) Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument(
        "--exposure",
        type=str,
        default="BMI",
        help="Exposure trait name (default: BMI).",
    )
    parser.add_argument(
        "--outcome",
        type=str,
        default="Type 2 Diabetes",
        help="Outcome trait name (default: Type 2 Diabetes).",
    )
    parser.add_argument(
        "--n_snps",
        type=int,
        default=120,
        help="Total number of SNPs to simulate (default: 120).",
    )
    parser.add_argument(
        "--true_effect",
        type=float,
        default=0.35,
        help="True causal effect used in simulation (default: 0.35).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: demo_outputs/).",
    )
    args = parser.parse_args()

    out_dir = ensure_output_dir(args.output_dir)

    # Step 1: Simulate GWAS data
    gwas_df = simulate_gwas_summary(
        n_snps=args.n_snps,
        true_effect=args.true_effect,
        seed=args.seed,
    )

    # Step 2: Select instruments
    instruments = select_instruments(gwas_df, p_thresh=GWAS_P_THRESHOLD)

    # Step 3: IVW MR
    ivw_result = ivw_mr(instruments)
    ivw_df = pd.DataFrame([ivw_result])
    ivw_path = os.path.join(out_dir, "causal_ivw_results.csv")
    ivw_df.to_csv(ivw_path, index=False)
    print_progress(f"Saved IVW results to {ivw_path}")

    # Step 4: Leave-one-out
    loo_df = leave_one_out_mr(instruments)
    loo_path = os.path.join(out_dir, "causal_loo_results.csv")
    loo_df.to_csv(loo_path, index=False)
    print_progress(f"Saved LOO results to {loo_path}")

    # Step 5: Plots
    scatter_path = os.path.join(out_dir, "causal_mr_scatter.png")
    plot_mr_scatter(instruments, ivw_result, scatter_path)

    funnel_path = os.path.join(out_dir, "causal_mr_funnel.png")
    plot_funnel(instruments, ivw_result, funnel_path)

    # Step 6: Interpretation
    interp_path = os.path.join(out_dir, "causal_interpretation.txt")
    generate_interpretation(ivw_result, loo_df, interp_path)

    # Final summary
    print("\n" + "=" * 60)
    print("Causal Inference Workflow (MR) Complete")
    print("=" * 60)
    print(f"Output directory       : {out_dir}")
    print(f"Exposure               : {args.exposure}")
    print(f"Outcome                : {args.outcome}")
    print(f"Instrument SNPs        : {ivw_result['n_snps']}")
    print(f"IVW beta (SE)          : {ivw_result['beta']:.4f} ({ivw_result['se']:.4f})")
    print(f"95% CI                 : [{ivw_result['ci_lower']:.4f}, {ivw_result['ci_upper']:.4f}]")
    print(f"P-value                : {ivw_result['p_value']:.2e}")
    print(f"Heterogeneity p        : {ivw_result['p_het']:.3f}")
    print(f"MR scatter plot        : {scatter_path}")
    print(f"Funnel plot            : {funnel_path}")
    print(f"Interpretation         : {interp_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
