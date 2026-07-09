#!/usr/bin/env python3
"""
Case Study 4 (Exposure -> Outcome MR exemplar, BMI -> Type 2 Diabetes)
=======================================================================
Biomedical Workflow Validation Suite

METHODOLOGY EXEMPLAR (not a real etiological claim).

This case wraps the framework's REAL causal-inference engine
(demo_causal_inference.py: simulate_gwas_summary / select_instruments / ivw_mr /
leave_one_out_mr / plot_mr_scatter / plot_funnel / generate_interpretation) and
runs it on SYNTHETIC GWAS summary statistics whose ground-truth causal effect is
known by construction.

Why synthetic, and why is this still honest validation?
-------------------------------------------------------
* Two-sample MR on REAL traits (e.g., BMI from GLGC/UKBB -> T2D from DIAGRAM)
  requires downloading + harmonizing large GWAS summary files, LD clumping, and
  outlier/pleiotropy sensitivity analyses that are out of scope for this offline
  validation environment (no reliable GWAS access; network is proxied/blocked).
* The point of THIS case is to prove the MR *computation* is correct: given data
  generated from a known effect, does the IVW estimator recover (a) the right sign,
  (b) the right magnitude within tolerance, and (c) reach significance at adequate
  power? That is a ground-truth-recovery benchmark — falsifiable and reproducible.
* Evidence grade C: synthetic GWAS; validates the MR engine, not a real
  exposure->outcome causal claim. next_validation points to real GWAS.

Outputs (--output-dir, default github/docs/case-study/):
  MR_exemplar_ivw_results.csv, MR_exemplar_loo_results.csv,
  MR_exemplar_scatter.png, MR_exemplar_funnel.png,
  MR_exemplar_sweep.csv, MR_exemplar_report.txt,
  MR_exemplar_evidence_package.json

Usage:
  python case_study_mr_exemplar.py --output-dir ../docs/case-study
  python case_study_mr_exemplar.py --true-effect 0.35 --n-snps 120 --seed 42 \
      --sweep 0.1 0.35 0.6 --output-dir ../docs/case-study
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

# Configure matplotlib BEFORE any engine import that touches it.
MPLCONFIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".matplotlib_cache")
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import demo_causal_inference as mr_engine  # noqa: E402

EXPOSURE = "BMI"
OUTCOME = "Type 2 Diabetes"


# ---------------------------------------------------------------------------
# Helpers
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


def run_one_mr(true_effect, n_snps, seed, sample_size_exposure, sample_size_outcome):
    """Run the full IVW MR pipeline for one ground-truth effect; return dict."""
    gwas = mr_engine.simulate_gwas_summary(
        n_snps=n_snps,
        true_effect=true_effect,
        sample_size_exposure=sample_size_exposure,
        sample_size_outcome=sample_size_outcome,
        seed=seed,
    )
    instruments = mr_engine.select_instruments(gwas, p_thresh=mr_engine.GWAS_P_THRESHOLD)
    ivw = mr_engine.ivw_mr(instruments)
    n_causal = int(gwas["causal"].sum())
    return {
        "true_effect": true_effect,
        "seed": seed,
        "n_snps_simulated": n_snps,
        "n_causal_in_dgp": n_causal,
        "n_instruments": ivw["n_snps"],
        "beta_ivw": ivw["beta"],
        "se_ivw": ivw["se"],
        "ci_lower": ivw["ci_lower"],
        "ci_upper": ivw["ci_upper"],
        "p_value": ivw["p_value"],
        "cochrans_q": ivw["cochrans_q"],
        "p_het": ivw["p_het"],
        "sign_correct": np.sign(ivw["beta"]) == np.sign(true_effect),
        "significant": ivw["p_value"] < 0.05,
        "abs_bias": abs(ivw["beta"] - true_effect),
        "within_ci": (ivw["ci_lower"] <= true_effect <= ivw["ci_upper"]),
    }


def main():
    ap = argparse.ArgumentParser(description="MR exemplar (BMI -> T2D) methodology case study")
    ap.add_argument("--true-effect", type=float, default=0.35,
                    help="Ground-truth causal effect used in the main exemplar run (default 0.35).")
    ap.add_argument("--n-snps", type=int, default=120, help="SNPs simulated (default 120).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    ap.add_argument("--n-exp", type=int, default=350000, help="Exposure GWAS sample size.")
    ap.add_argument("--n-out", type=int, default=900000, help="Outcome GWAS sample size.")
    ap.add_argument("--sweep", type=float, nargs="*", default=[0.1, 0.35, 0.6],
                    help="Effect sizes for the ground-truth recovery sweep (default 0.1 0.35 0.6).")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Ground-truth recovery sweep (the benchmark)
    # ------------------------------------------------------------------
    print("[PROGRESS] Running ground-truth recovery sweep ...", file=sys.stderr)
    sweep_rows = []
    for te in args.sweep:
        sweep_rows.append(run_one_mr(te, args.n_snps, args.seed, args.n_exp, args.n_out))
    sweep_df = pd.DataFrame(sweep_rows)
    sweep_path = os.path.join(args.output_dir, "MR_exemplar_sweep.csv")
    sweep_df.to_csv(sweep_path, index=False)

    sweep_sign_rate = float(sweep_df["sign_correct"].mean())
    sweep_sig_rate = float(sweep_df["significant"].mean())
    sweep_within_ci_rate = float(sweep_df["within_ci"].mean())
    sweep_mean_abs_bias = float(sweep_df["abs_bias"].mean())

    # ------------------------------------------------------------------
    # Main exemplar run at the requested true effect
    # ------------------------------------------------------------------
    print("[PROGRESS] Running main exemplar (BMI -> T2D) ...", file=sys.stderr)
    gwas = mr_engine.simulate_gwas_summary(
        n_snps=args.n_snps,
        true_effect=args.true_effect,
        sample_size_exposure=args.n_exp,
        sample_size_outcome=args.n_out,
        seed=args.seed,
    )
    instruments = mr_engine.select_instruments(gwas, p_thresh=mr_engine.GWAS_P_THRESHOLD)
    ivw = mr_engine.ivw_mr(instruments)
    loo_df = mr_engine.leave_one_out_mr(instruments)

    ivw_df = pd.DataFrame([ivw])
    ivw_path = os.path.join(args.output_dir, "MR_exemplar_ivw_results.csv")
    ivw_df.to_csv(ivw_path, index=False)
    loo_path = os.path.join(args.output_dir, "MR_exemplar_loo_results.csv")
    loo_df.to_csv(loo_path, index=False)

    scatter_path = os.path.join(args.output_dir, "MR_exemplar_scatter.png")
    mr_engine.plot_mr_scatter(instruments, ivw, scatter_path)
    funnel_path = os.path.join(args.output_dir, "MR_exemplar_funnel.png")
    mr_engine.plot_funnel(instruments, ivw, funnel_path)

    interp_path = os.path.join(args.output_dir, "MR_exemplar_interpretation.txt")
    mr_engine.generate_interpretation(ivw, loo_df, interp_path)

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    report_path = os.path.join(args.output_dir, "MR_exemplar_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("MR Exemplar (BMI -> Type 2 Diabetes) — Methodology Case Study\n")
        fh.write("=" * 64 + "\n\n")
        fh.write("EVIDENCE GRADE: C (synthetic GWAS; validates MR engine, not a real claim)\n\n")
        fh.write("Main exemplar run\n")
        fh.write("-" * 64 + "\n")
        fh.write(f"Exposure / Outcome      : {EXPOSURE} -> {OUTCOME}\n")
        fh.write(f"Ground-truth effect     : {args.true_effect:.3f}\n")
        fh.write(f"SNPs simulated          : {args.n_snps} ({int(gwas['causal'].sum())} causal in DGP)\n")
        fh.write(f"Instrument SNPs         : {ivw['n_snps']}\n")
        fh.write(f"IVW beta (SE)           : {ivw['beta']:.4f} ({ivw['se']:.4f})\n")
        fh.write(f"95% CI                  : [{ivw['ci_lower']:.4f}, {ivw['ci_upper']:.4f}]\n")
        fh.write(f"P-value                 : {ivw['p_value']:.2e}\n")
        fh.write(f"Cochran's Q / p_het     : {ivw['cochrans_q']:.2f} / {ivw['p_het']:.3f}\n")
        fh.write(f"Sign recovered          : {np.sign(ivw['beta']) == np.sign(args.true_effect)}\n")
        fh.write(f"Truth within 95% CI     : "
                 f"{ivw['ci_lower'] <= args.true_effect <= ivw['ci_upper']}\n\n")
        fh.write("Ground-truth recovery sweep (benchmark)\n")
        fh.write("-" * 64 + "\n")
        fh.write(sweep_df.to_string(index=False))
        fh.write("\n\n")
        fh.write(f"Sign recovery rate      : {sweep_sign_rate:.2f}\n")
        fh.write(f"Significance rate       : {sweep_sig_rate:.2f}\n")
        fh.write(f"Truth-in-CI rate        : {sweep_within_ci_rate:.2f}\n")
        fh.write(f"Mean |bias| (est-truth) : {sweep_mean_abs_bias:.4f}\n\n")
        fh.write("Limitations\n")
        fh.write("-" * 64 + "\n")
        fh.write("- Synthetic GWAS; no real genetic instruments or population structure.\n")
        fh.write("- No LD clumping / harmonization / horizontal-pleiotropy robustness (MR-Egger, weighted median).\n")
        fh.write("- Single simulated realization per effect size (no Monte-Carlo over seeds here).\n")

    # ------------------------------------------------------------------
    # Evidence package
    # ------------------------------------------------------------------
    pkg = {
        "metadata": {
            "case_study": "MR exemplar (BMI -> Type 2 Diabetes)",
            "workflow": "causal-inference",
            "exposure": EXPOSURE,
            "outcome": OUTCOME,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.1.0 + case-study-mr-exemplar",
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
            "beta_ivw": ivw["beta"],
            "se_ivw": ivw["se"],
            "ci_lower": ivw["ci_lower"],
            "ci_upper": ivw["ci_upper"],
            "p_value": ivw["p_value"],
            "cochrans_q": ivw["cochrans_q"],
            "p_het": ivw["p_het"],
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
        "evidence_grade": "C (synthetic GWAS; methodology validation of MR engine; not a real etiological claim)",
        "limitations": [
            "Synthetic GWAS; no real genetic instruments or population structure",
            "No LD clumping / harmonization / horizontal-pleiotropy robustness (MR-Egger, weighted median)",
            "Single simulated realization per effect size",
        ],
        "next_validation": "Real two-sample MR: GLGC/UKBB BMI -> DIAGRAM/UKBB T2D summary stats, with LD clumping, harmonization, and pleiotropy-robust methods",
    }
    pkg_path = os.path.join(args.output_dir, "MR_exemplar_evidence_package.json")
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 64)
    print("MR EXEMPLAR CASE STUDY COMPLETE")
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
