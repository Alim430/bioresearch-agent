#!/usr/bin/env python3
"""
Case Study 5 (Causal Evidence Chain: GWAS -> eQTL -> coloc -> TWAS -> fine-mapping -> MR)
=========================================================================================
Biomedical Workflow Validation Suite

METHODOLOGY VALIDATION (synthetic data; ground-truth known by construction).
Honest grade C.

This case wraps the framework's REAL causal-evidence engine
(demo_causal_evidence.py: simulate_causal_chain / run_coloc / twas_z /
fine_map_credible_set / wald_ratio_mr / causal_evidence_pipeline / sweep_benchmark)
and runs it on SYNTHETIC per-gene loci whose causal structure is planted.

Why synthetic, and why is this still honest validation?
-------------------------------------------------------
* A real causal-evidence chain (e.g., for Alzheimer's disease) needs GWAS summary
  stats (IGAP/GR@P, UKBB), eQTL weights (eQTLGen, GTEx), and LD reference panels.
  Downloading + harmonizing + LD-clumping those is out of scope for this offline
  validation environment (no reliable GWAS access; network is proxied/blocked).
* The point of THIS case is to prove the *computations* recover a planted ground
  truth: does colocalization flag the colocalized genes (PP.H4 high)? does TWAS
  detect trait-associated expression? does fine-mapping place the true causal SNP
  in the 95% credible set? That is a ground-truth-recovery benchmark — falsifiable
  and reproducible.
* Evidence grade C: synthetic loci; validates the causal-evidence engine, not a
  real etiological claim. next_validation points to real summary statistics.

For a real deployment, swap `simulate_causal_chain` for IEU OpenGWAS + eQTLGen/GTEx
and point `next_validation` at those sources. Reference loci for an AD real-data
version: APOE, TREM2, BIN1, CLU (all show eQTL<->GWAS colocalization in the literature).

Outputs (--output-dir, default github/docs/case-study/):
  CE_per_gene_results.csv, CE_credible_sets.csv, CE_recovery_benchmark.csv,
  CE_summary_report.txt, CE_locus_heatmap.png, CE_evidence_package.json

Usage:
  python case_study_causal_evidence.py --output-dir ../docs/case-study
  python case_study_causal_evidence.py --n-genes 10 --snps-per-gene 14 --seed 7 \
      --output-dir ../docs/case-study
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

# Configure matplotlib before engine import.
MPLCONFIGDIR = "/tmp/matplotlib_ce"
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import demo_causal_evidence as ce_engine  # noqa: E402

DOMAIN = "Alzheimer's disease (methodology exemplar)"
REFERENCE_LOCI = ["APOE", "TREM2", "BIN1", "CLU"]


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


def main():
    ap = argparse.ArgumentParser(description="Causal evidence chain methodology case study (Case 5)")
    ap.add_argument("--n-genes", type=int, default=8, help="Genes (loci) simulated (default 8).")
    ap.add_argument("--snps-per-gene", type=int, default=12, help="SNPs per locus (default 12).")
    ap.add_argument("--true-effect", type=float, default=0.35, help="Planted causal effect (default 0.35).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    ap.add_argument("--no-sweep", action="store_true", help="skip the robustness sweep")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Main run at the requested seed / effect
    # ------------------------------------------------------------------
    print("[PROGRESS] Simulating causal chain ...", file=sys.stderr)
    sim = ce_engine.simulate_causal_chain(
        n_genes=args.n_genes, snps_per_gene=args.snps_per_gene,
        true_effect=args.true_effect, seed=args.seed,
    )
    res = ce_engine.causal_evidence_pipeline(sim)
    per_gene = res["per_gene"]
    cred = res["credible"]
    benchmark = res["benchmark"]

    per_gene_path = os.path.join(args.output_dir, "CE_per_gene_results.csv")
    per_gene.to_csv(per_gene_path, index=False)
    cred_path = os.path.join(args.output_dir, "CE_credible_sets.csv")
    cred.to_csv(cred_path, index=False)

    heatmap_path = os.path.join(args.output_dir, "CE_locus_heatmap.png")
    ce_engine.plot_coloc_grid(per_gene, sim["truth"], heatmap_path)

    # ------------------------------------------------------------------
    # Ground-truth recovery sweep (robustness benchmark)
    # ------------------------------------------------------------------
    if not args.no_sweep:
        print("[PROGRESS] Running recovery sweep ...", file=sys.stderr)
        sweep_df = ce_engine.sweep_benchmark(
            n_genes=args.n_genes, snps_per_gene=args.snps_per_gene)
        sweep_path = os.path.join(args.output_dir, "CE_recovery_benchmark.csv")
        sweep_df.to_csv(sweep_path, index=False)
        sweep_means = {
            "coloc_rate": float(sweep_df["coloc_rate"].mean()),
            "twas_rate": float(sweep_df["twas_rate"].mean()),
            "finemap_rate": float(sweep_df["finemap_rate"].mean()),
        }
    else:
        sweep_df = None
        sweep_means = {"coloc_rate": benchmark["coloc_recovered_rate"],
                       "twas_rate": benchmark["twas_recovered_rate"],
                       "finemap_rate": benchmark["finemap_true_in_cs_rate"]}

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    report_path = os.path.join(args.output_dir, "CE_summary_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("Causal Evidence Chain — Methodology Case Study (Case 5)\n")
        fh.write("=" * 64 + "\n\n")
        fh.write("EVIDENCE GRADE: C (synthetic loci; validates causal-evidence engine, not a real claim)\n\n")
        fh.write(f"Domain (exemplar)   : {DOMAIN}\n")
        fh.write(f"Genes simulated     : {benchmark['n_genes']} ({benchmark['n_colocalized']} colocalized)\n")
        fh.write(f"Reference loci (AD) : {', '.join(REFERENCE_LOCI)}\n\n")
        fh.write("Per-gene results\n")
        fh.write("-" * 64 + "\n")
        fh.write(per_gene.to_string(index=False))
        fh.write("\n\n")
        fh.write("Ground-truth recovery (main run)\n")
        fh.write("-" * 64 + "\n")
        fh.write(f"Coloc recovery  (PP.H4 correctly called) : {benchmark['coloc_recovered_rate']:.2f}\n")
        fh.write(f"TWAS recovery   (sig for colocalized)     : {benchmark['twas_recovered_rate']:.2f}\n")
        fh.write(f"Fine-map recovery (true SNP in 95% CS)    : {benchmark['finemap_true_in_cs_rate']:.2f}\n\n")
        if sweep_df is not None:
            fh.write("Sweep means (effects 0.2/0.35/0.5 x seeds 1/2/3/42)\n")
            fh.write("-" * 64 + "\n")
            fh.write(f"Coloc  : {sweep_means['coloc_rate']:.2f}\n")
            fh.write(f"TWAS   : {sweep_means['twas_rate']:.2f}\n")
            fh.write(f"Fine-map: {sweep_means['finemap_rate']:.2f}\n\n")
        fh.write("Limitations\n")
        fh.write("-" * 64 + "\n")
        fh.write("- Synthetic loci; no real GWAS/eQTL summary statistics or population structure.\n")
        fh.write("- No LD structure modelled (SNPs treated independent); real fine-mapping needs LD.\n")
        fh.write("- One causal variant per trait assumed (standard coloc model).\n")
        fh.write("- Single simulated realization per (effect, seed) in the sweep.\n")

    # ------------------------------------------------------------------
    # Evidence package
    # ------------------------------------------------------------------
    pkg = {
        "metadata": {
            "case_study": "Causal Evidence Chain (GWAS -> eQTL -> coloc -> TWAS -> fine-mapping -> MR)",
            "workflow": "causal-evidence",
            "domain": DOMAIN,
            "reference_loci": REFERENCE_LOCI,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.1.0 + case-study-causal-evidence",
            "mode": "synthetic loci (ground-truth causal structure known by construction)",
        },
        "provenance": {
            "git_commit": git_commit(os.path.join(HERE, "..", "..")),
            "python": sys.version.split()[0],
            "env": "managed venv (python3.13 + numpy/pandas/scipy/matplotlib)",
            "seed": args.seed,
            "seed_policy": "numpy default_rng(seed); deterministic given seed",
            "engine": "demo_causal_evidence.py (run_coloc, twas_z, fine_map_credible_set, wald_ratio_mr, causal_evidence_pipeline)",
        },
        "methods": ["simulate_causal_chain", "run_coloc", "twas_z",
                     "fine_map_credible_set", "wald_ratio_mr", "causal_evidence_pipeline"],
        "results": {
            "n_genes": int(benchmark["n_genes"]),
            "n_colocalized": int(benchmark["n_colocalized"]),
            "coloc_recovered_rate": benchmark["coloc_recovered_rate"],
            "twas_recovered_rate": benchmark["twas_recovered_rate"],
            "finemap_true_in_cs_rate": benchmark["finemap_true_in_cs_rate"],
            "per_gene": per_gene.to_dict(orient="records"),
        },
        "benchmark": {
            "type": "ground_truth_recovery",
            "coloc_recovered_rate": benchmark["coloc_recovered_rate"],
            "twas_recovered_rate": benchmark["twas_recovered_rate"],
            "finemap_true_in_cs_rate": benchmark["finemap_true_in_cs_rate"],
            "sweep_means": sweep_means,
            "sweep_table": sweep_df.to_dict(orient="records") if sweep_df is not None else None,
        },
        "evidence_grade": "C (synthetic loci; methodology validation of causal-evidence engine; not a real etiological claim)",
        "limitations": [
            "Synthetic loci; no real GWAS/eQTL summary statistics or population structure",
            "No LD structure modelled (SNPs treated independent); real fine-mapping needs LD reference panels",
            "One causal variant per trait assumed (standard coloc model)",
            "Single simulated realization per (effect, seed)",
        ],
        "next_validation": "Real causal-evidence chain: IEU OpenGWAS (trait) + eQTLGen/GTEx (expression weights) + LD reference, for AD loci (APOE/TREM2/BIN1/CLU)",
    }
    pkg_path = os.path.join(args.output_dir, "CE_evidence_package.json")
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 64)
    print("CAUSAL EVIDENCE CHAIN CASE STUDY COMPLETE (SYNTHETIC)")
    print("=" * 64)
    print(f"Genes              : {benchmark['n_genes']} ({benchmark['n_colocalized']} colocalized)")
    print(f"Coloc recovery     : {benchmark['coloc_recovered_rate']:.2f}")
    print(f"TWAS recovery      : {benchmark['twas_recovered_rate']:.2f}")
    print(f"Fine-map recovery  : {benchmark['finemap_true_in_cs_rate']:.2f}")
    print(f"Sweep means        : coloc {sweep_means['coloc_rate']:.2f} / "
          f"TWAS {sweep_means['twas_rate']:.2f} / finemap {sweep_means['finemap_rate']:.2f}")
    print(f"Evidence grade     : C (synthetic loci; engine validation)")
    print(f"Evidence package   -> {pkg_path}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
