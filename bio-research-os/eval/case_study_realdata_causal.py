#!/usr/bin/env python3
"""
Case Study 6 (Real-Data Causal Evidence Chain: AD GWAS -> GTEx brain eQTL)
==========================================================================
Biomedical Workflow Validation Suite

REAL PUBLIC SUMMARY DATA (honest grade B).
This case drives the framework's causal-evidence engine (demo_causal_evidence.py)
through the real-data adapter (demo_realdata_loader.py) on:

  * AD GWAS summary stats  : Jansen et al. 2019 (public, hg19)
  * Brain cis-eQTL summary : GTEx v8, 13 brain tissues (public, hg38)

It runs colocalization (PP.H4), TWAS (S-PrediXcan-style Z), Bayesian credible-set
fine-mapping, and single-SNP Wald-ratio MR for AD loci (TREM2/BIN1/CLU/PICALM/APOE).

Why this is honest grade B (not a synthetic C):
  * Inputs are REAL public summary statistics, not constructed ground truth.
  * No individual-level / controlled-access data (MetaBrain/UKB-PPP/ADNI/deCODE
    excluded per DATA_GOVERNANCE.md).
  * Limitations are explicit: lead cis-eQTL only, rsID-matched, SNPs in LD treated
    as independent, single-SNP Wald MR. See the evidence package's limitations[].

This is a METHODOLOGY DEMONSTRATION of the engine on real data, not a definitive
etiological claim. next_validation points to full eQTL weights + LD reference.

Outputs (--output-dir, default <repo>/docs/case-study):
  CE_real_per_gene.csv, CE_real_credible_sets.csv, CE_real_locus_heatmap.png,
  CE_real_summary_report.txt, CE_real_evidence_package.json

Usage:
  python case_study_realdata_causal.py
  python case_study_realdata_causal.py --genes TREM2,BIN1,CLU,PICALM,APOE \
      --gwas-path /path/to/Jansen.txt.gz --eqtl-dir /path/to/GTEx_v8_eQTL \
      --output-dir ../docs/case-study
"""
import os
import sys

import matplotlib  # noqa: E402
matplotlib.use("Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
DEMOS = os.path.join(HERE, "..", "demos")
sys.path.insert(0, os.path.abspath(DEMOS))

import demo_realdata_loader as rda  # noqa: E402

DEFAULT_OUT = os.path.join(HERE, "..", "..", "docs", "case-study")


def main():
    # Reuse the adapter's CLI so behaviour is identical and provenance is recorded.
    rda.main.__doc__ = __doc__
    # Build argv: point at the committed default output dir unless overridden.
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--output-dir", default=DEFAULT_OUT)
    ap.add_argument("--gwas-path", default=rda.DEFAULT_GWAS)
    ap.add_argument("--eqtl-dir", default=rda.DEFAULT_EQTL_DIR)
    ap.add_argument("--genes", default=",".join(rda.DEFAULT_GENES))
    args, _ = ap.parse_known_args()

    genes = [g.strip() for g in args.genes.split(",") if g.strip()]
    rda.run_real_causal_chain(
        gwas_path=args.gwas_path,
        eqtl_dir=args.eqtl_dir,
        genes=genes,
        outdir=args.output_dir,
    )


if __name__ == "__main__":
    main()
