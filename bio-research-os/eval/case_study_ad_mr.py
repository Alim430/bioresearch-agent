#!/usr/bin/env python3
"""
Case Study 2 (Alzheimer's disease causal evidence, risk factor -> AD)
=====================================================================
Biomedical Workflow Validation Suite

AD-DOMAIN MR METHODOLOGY CASE (synthetic data; real IVW engine).

This case demonstrates the framework's causal-inference workflow applied to an
Alzheimer's-relevant question: does higher EDUCATIONAL ATTAINMENT causally
reduce Alzheimer's disease (AD) risk? In the real literature, MR using
SSGAC educational-attainment GWAS instruments vs IGAP/GR@P AD GWAS has suggested
a protective causal effect (negative beta). Here we validate the ENGINE on a
synthetic scenario whose ground-truth effect is known.

Honesty notes (do NOT overclaim)
--------------------------------
* The GWAS data are SIMULATED with a known true effect. No real genetic
  instruments (APOE/TREM2/BIN1/CLU etc.) are used. Those loci are listed as
  REFERENCE loci for the real-data version only.
* The purpose is to prove the IVW estimator recovers a known negative causal
  effect (sign, magnitude, significance) — a ground-truth-recovery benchmark.
* Evidence grade C: methodology validation of the MR engine in an AD context,
  not a real etiological claim. next_validation points to real GWAS.

Outputs (--output-dir, default github/docs/case-study/):
  AD_MR_ivw_results.csv, AD_MR_loo_results.csv,
  AD_MR_scatter.png, AD_MR_funnel.png,
  AD_MR_sweep.csv, AD_MR_report.txt, AD_MR_evidence_package.json

Usage:
  python case_study_ad_mr.py --output-dir ../docs/case-study
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

# Make the framework engine importable
HERE = os.path.dirname(os.path.abspath(__file__))
DEMOS = os.path.join(HERE, "..", "demos")
sys.path.insert(0, os.path.abspath(DEMOS))

MPLCONFIGDIR = "/tmp/matplotlib_ad_mr"
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import demo_causal_inference as mr_engine  # noqa: E402

EXPOSURE = "Educational attainment (years)"
OUTCOME = "Alzheimer's disease"

# Reference AD GWAS loci for the REAL-data version (NOT used in synthetic run).
REFERENCE_AD_LOCI = ["APOE", "TREM2", "BIN1", "CLU"]

# Pathway-sanity labels that a REAL AD MR would be expected to touch.
PATHWAY_SANITY = ["lipid metabolism", "immune/inflammatory response", "amyloid/tau"]


# ---------------------------------------------------------------------------
# Helpers (matplotlib plotting with AD-correct axis labels)
# ---------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo_dir):
    try:
        return subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def plot_mr_scatter_ad(instruments, ivw_result, outpath):
    bx = instruments["beta_exposure"]
    by = instruments["beta_outcome"]
    plt.figure(figsize=(10, 8))
    plt.errorbar(bx, by, xerr=instruments["se_exposure"], yerr=instruments["se_outcome"],
                 fmt="o", color="steelblue", ecolor="lightgray", elinewidth=1, capsize=2, alpha=0.7)
    xlim = plt.xlim()
    x_vals = np.array(xlim)
    y_vals = ivw_result["beta"] * x_vals
    plt.plot(x_vals, y_vals, color="crimson", linewidth=2,
             label=f"IVW slope = {ivw_result['beta']:.3f}")
    plt.axhline(0, color="black", linestyle="-", linewidth=0.5)
    plt.axvline(0, color="black", linestyle="-", linewidth=0.5)
    plt.xlabel(f"SNP effect on exposure ({EXPOSURE})")
    plt.ylabel(f"SNP effect on outcome ({OUTCOME})")
    plt.title(f"MR Scatter Plot: {EXPOSURE} → {OUTCOME}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved MR scatter plot to {outpath}")


def plot_funnel_ad(instruments, ivw_result, outpath):
    wald = instruments["beta_outcome"] / instruments["beta_exposure"]
    se_wald = np.abs(wald) * np.sqrt((instruments["se_outcome"] / instruments["beta_outcome"]) ** 2 +
                                     (instruments["se_exposure"] / instruments["beta_exposure"]) ** 2)
    precision = 1.0 / se_wald
    plt.figure(figsize=(9, 7))
    plt.scatter(wald, precision, color="steelblue", alpha=0.7, edgecolors="black", linewidths=0.5)
    plt.axvline(ivw_result["beta"], color="crimson", linestyle="--", linewidth=2,
                label=f"IVW estimate = {ivw_result['beta']:.3f}")
    plt.xlabel("Wald Ratio (beta_outcome / beta_exposure)")
    plt.ylabel("Precision (1 / SE)")
    plt.title(f"Funnel Plot: IVW MR ({EXPOSURE} → {OUTCOME})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved funnel plot to {outpath}")


def print_progress(msg):
    print(f"[PROGRESS] {msg}", file=sys.stderr)


def run_one_mr(true_effect, n_snps, seed, n_exp, n_out):
    gwas = mr_engine.simulate_gwas_summary(
        n_snps=n_snps, true_effect=true_effect,
        sample_size_exposure=n_exp, sample_size_outcome=n_out, seed=seed,
    )
    instruments = mr_engine.select_instruments(gwas, p_thresh=mr_engine.GWAS_P_THRESHOLD)
    ivw = mr_engine.ivw_mr(instruments)
    return {
        "true_effect": true_effect,
        "n_causal_in_dgp": int(gwas["causal"].sum()),
        "n_instruments": ivw["n_snps"],
        "beta_ivw": ivw["beta"], "se_ivw": ivw["se"],
        "ci_lower": ivw["ci_lower"], "ci_upper": ivw["ci_upper"],
        "p_value": ivw["p_value"],
        "sign_correct": np.sign(ivw["beta"]) == np.sign(true_effect),
        "significant": ivw["p_value"] < 0.05,
        "abs_bias": abs(ivw["beta"] - true_effect),
        "within_ci": (ivw["ci_lower"] <= true_effect <= ivw["ci_upper"]),
    }


def main():
    ap = argparse.ArgumentParser(description="AD causal MR methodology case study (synthetic)")
    ap.add_argument("--true-effect", type=float, default=-0.30,
                    help="Ground-truth causal effect (default -0.30 = protective).")
    ap.add_argument("--n-snps", type=int, default=120, help="SNPs simulated (default 120).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    ap.add_argument("--n-exp", type=int, default=350000, help="Exposure GWAS sample size.")
    ap.add_argument("--n-out", type=int, default=900000, help="Outcome GWAS sample size.")
    ap.add_argument("--sweep", type=float, nargs="*", default=[-0.10, -0.30, -0.60],
                    help="Effect sizes for the ground-truth recovery sweep (default -0.1 -0.3 -0.6).")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Ground-truth recovery sweep
    print_progress("Running ground-truth recovery sweep ...")
    sweep_rows = [run_one_mr(te, args.n_snps, args.seed, args.n_exp, args.n_out) for te in args.sweep]
    sweep_df = pd.DataFrame(sweep_rows)
    sweep_path = os.path.join(args.output_dir, "AD_MR_sweep.csv")
    sweep_df.to_csv(sweep_path, index=False)
    sweep_sign_rate = float(sweep_df["sign_correct"].mean())
    sweep_sig_rate = float(sweep_df["significant"].mean())
    sweep_within_ci_rate = float(sweep_df["within_ci"].mean())
    sweep_mean_abs_bias = float(sweep_df["abs_bias"].mean())

    # Main run
    print_progress(f"Running main AD MR ({EXPOSURE} -> {OUTCOME}) ...")
    gwas = mr_engine.simulate_gwas_summary(
        n_snps=args.n_snps, true_effect=args.true_effect,
        sample_size_exposure=args.n_exp, sample_size_outcome=args.n_out, seed=args.seed,
    )
    instruments = mr_engine.select_instruments(gwas, p_thresh=mr_engine.GWAS_P_THRESHOLD)
    ivw = mr_engine.ivw_mr(instruments)
    loo_df = mr_engine.leave_one_out_mr(instruments)

    ivw_df = pd.DataFrame([ivw])
    ivw_path = os.path.join(args.output_dir, "AD_MR_ivw_results.csv")
    ivw_df.to_csv(ivw_path, index=False)
    loo_path = os.path.join(args.output_dir, "AD_MR_loo_results.csv")
    loo_df.to_csv(loo_path, index=False)

    scatter_path = os.path.join(args.output_dir, "AD_MR_scatter.png")
    plot_mr_scatter_ad(instruments, ivw, scatter_path)
    funnel_path = os.path.join(args.output_dir, "AD_MR_funnel.png")
    plot_funnel_ad(instruments, ivw, funnel_path)

    # Interpretation (AD-correct)
    interp_path = os.path.join(args.output_dir, "AD_MR_interpretation.txt")
    with open(interp_path, "w", encoding="utf-8") as fh:
        fh.write("Alzheimer's Disease MR Interpretation (METHODOLOGY CASE, synthetic data)\n")
        fh.write("=" * 70 + "\n\n")
        fh.write(f"Exposure : {EXPOSURE}\n")
        fh.write(f"Outcome  : {OUTCOME}\n")
        fh.write(f"Instrument SNPs : {ivw['n_snps']}\n\n")
        fh.write("Primary IVW Result\n")
        fh.write("-" * 70 + "\n")
        fh.write(f"Causal effect estimate (beta) : {ivw['beta']:.4f}\n")
        fh.write(f"Standard error                : {ivw['se']:.4f}\n")
        fh.write(f"95% CI                       : [{ivw['ci_lower']:.4f}, {ivw['ci_upper']:.4f}]\n")
        fh.write(f"P-value                      : {ivw['p_value']:.2e}\n")
        fh.write(f"Cochran's Q / p_het          : {ivw['cochrans_q']:.2f} / {ivw['p_het']:.3f}\n\n")
        fh.write("Interpretation\n")
        fh.write("-" * 70 + "\n")
        if ivw["p_value"] < 0.05:
            direction = "reduced" if ivw["beta"] < 0 else "increased"
            fh.write(f"IVW suggests a significant causal effect: higher genetically predicted "
                     f"{EXPOSURE.lower()} is associated with {direction} {OUTCOME.lower()} risk.\n")
        else:
            fh.write("IVW estimate not significant in this synthetic realization.\n")
        if ivw["p_het"] < 0.05:
            fh.write("WARNING: heterogeneity (Cochran's Q p<0.05) — possible pleiotropy in real data.\n")
        else:
            fh.write("No significant heterogeneity in this synthetic realization.\n")
        fh.write("\nLimitations\n")
        fh.write("-" * 70 + "\n")
        fh.write("- SYNTHETIC GWAS; no real genetic instruments (APOE/TREM2/BIN1/CLU etc.).\n")
        fh.write("- No LD clumping / harmonization / pleiotropy-robust methods (MR-Egger, weighted median).\n")
        fh.write("- This is engine validation, not a real AD etiological claim.\n")

    # Report
    report_path = os.path.join(args.output_dir, "AD_MR_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("AD Causal MR — Methodology Case Study (synthetic)\n")
        fh.write("=" * 64 + "\n\n")
        fh.write("EVIDENCE GRADE: C (synthetic GWAS; validates MR engine in AD context)\n\n")
        fh.write("Question : Does higher educational attainment causally reduce AD risk?\n")
        fh.write(f"Exposure : {EXPOSURE}\n")
        fh.write(f"Outcome  : {OUTCOME}\n\n")
        fh.write("Main run\n")
        fh.write("-" * 64 + "\n")
        fh.write(f"Ground-truth effect     : {args.true_effect:.3f}\n")
        fh.write(f"SNPs simulated          : {args.n_snps} ({int(gwas['causal'].sum())} causal in DGP)\n")
        fh.write(f"Instrument SNPs         : {ivw['n_snps']}\n")
        fh.write(f"IVW beta (SE)           : {ivw['beta']:.4f} ({ivw['se']:.4f})\n")
        fh.write(f"95% CI                  : [{ivw['ci_lower']:.4f}, {ivw['ci_upper']:.4f}]\n")
        fh.write(f"P-value                 : {ivw['p_value']:.2e}\n")
        fh.write(f"Sign recovered          : {np.sign(ivw['beta']) == np.sign(args.true_effect)}\n")
        fh.write(f"Truth within 95% CI     : {ivw['ci_lower'] <= args.true_effect <= ivw['ci_upper']}\n\n")
        fh.write("Ground-truth recovery sweep (benchmark)\n")
        fh.write("-" * 64 + "\n")
        fh.write(sweep_df.to_string(index=False))
        fh.write("\n\n")
        fh.write(f"Sign recovery rate      : {sweep_sign_rate:.2f}\n")
        fh.write(f"Significance rate       : {sweep_sig_rate:.2f}\n")
        fh.write(f"Truth-in-CI rate        : {sweep_within_ci_rate:.2f}\n")
        fh.write(f"Mean |bias|             : {sweep_mean_abs_bias:.4f}\n\n")
        fh.write("Reference AD GWAS loci (real-data version only, NOT used here):\n")
        fh.write("  " + ", ".join(REFERENCE_AD_LOCI) + "\n")
        fh.write("Expected pathway sanity for real AD MR: " + ", ".join(PATHWAY_SANITY) + "\n")

    # Evidence package
    pkg = {
        "metadata": {
            "case_study": "AD causal MR (educational attainment -> AD)",
            "workflow": "causal-inference",
            "exposure": EXPOSURE, "outcome": OUTCOME,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.1.0 + case-study-ad-mr",
            "mode": "synthetic GWAS (ground-truth known by construction)",
        },
        "provenance": {
            "git_commit": git_commit(os.path.join(HERE, "..", "..")),
            "python": sys.version.split()[0],
            "env": "managed venv (python3.13 + numpy/pandas/scipy/matplotlib)",
            "seed": args.seed,
            "seed_policy": "numpy default_rng(seed); deterministic given seed",
            "engine": "demo_causal_inference.py (ivw_mr, leave_one_out_mr, select_instruments)",
        },
        "methods": ["simulate_gwas_summary", "select_instruments", "ivw_mr",
                     "leave_one_out_mr", "plot_mr_scatter", "plot_funnel"],
        "results": {
            "n_snps_simulated": args.n_snps,
            "n_causal_in_dgp": int(gwas["causal"].sum()),
            "n_instruments": ivw["n_snps"],
            "beta_ivw": ivw["beta"], "se_ivw": ivw["se"],
            "ci_lower": ivw["ci_lower"], "ci_upper": ivw["ci_upper"],
            "p_value": ivw["p_value"],
            "sign_correct": bool(np.sign(ivw["beta"]) == np.sign(args.true_effect)),
            "truth_within_ci": bool(ivw["ci_lower"] <= args.true_effect <= ivw["ci_upper"]),
        },
        "benchmark": {
            "type": "ground_truth_recovery",
            "sweep_effects": [float(x) for x in args.sweep],
            "sign_recovery_rate": sweep_sign_rate,
            "significance_rate": sweep_sig_rate,
            "truth_in_ci_rate": sweep_within_ci_rate,
            "mean_abs_bias": sweep_mean_abs_bias,
            "sweep_table": sweep_df.to_dict(orient="records"),
        },
        "evidence_grade": "C (synthetic GWAS; MR-engine validation in AD context; not a real claim)",
        "reference_ad_loci": REFERENCE_AD_LOCI,
        "expected_pathway_sanity_real": PATHWAY_SANITY,
        "limitations": [
            "Synthetic GWAS; reference AD loci (APOE/TREM2/BIN1/CLU) not used",
            "No LD clumping / harmonization / pleiotropy-robust methods",
            "Single simulated realization per effect size",
        ],
        "next_validation": "Real two-sample MR: SSGAC educational attainment -> IGAP/GR@P AD summary stats, with LD clumping, harmonization, and MR-Egger/weighted-median sensitivity",
    }
    pkg_path = os.path.join(args.output_dir, "AD_MR_evidence_package.json")
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 64)
    print("AD MR METHODOLOGY CASE COMPLETE")
    print("=" * 64)
    print(f"Exposure->Outcome : {EXPOSURE} -> {OUTCOME}")
    print(f"True effect       : {args.true_effect:.3f}")
    print(f"IVW beta (SE)     : {ivw['beta']:.4f} ({ivw['se']:.4f})  p={ivw['p_value']:.2e}")
    print(f"Sign recovered    : {pkg['results']['sign_correct']}  Truth-in-CI: {pkg['results']['truth_within_ci']}")
    print(f"Sweep sign/sig/CI : {sweep_sign_rate:.2f} / {sweep_sig_rate:.2f} / {sweep_within_ci_rate:.2f}")
    print(f"Evidence grade    : C (synthetic GWAS; engine validation)")
    print(f"Evidence package  -> {pkg_path}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
