#!/usr/bin/env python3
"""
Case Study 1 (Parkinson's disease / GSE7621) — Biomedical Workflow Validation Suite
=====================================================================================

End-to-end REAL-data run of the biomarker-discovery engine on public GEO data,
with a blind benchmark evaluation.

All statistics run in the framework engine (demo_biomarker_discovery): this script
only (a) loads real data through the engine's microarray loader, (b) runs the
engine's differential_expression / pathway_enrichment / rank_biomarkers, and
(c) computes the blind benchmark. No analysis is reimplemented here.

Design notes (honesty)
----------------------
* GSE7621 is a bulk-substantia-nigra microarray (25 samples, Affymetrix HG-U133_Plus_2).
  Bulk tissue + modest n means Mendelian PD driver genes (SNCA/LRRK2/PINK1/PRKN/GBA)
  show only subtle expression shifts and are typically NOT FDR-significant. The dominant,
  recoverable signal is the **dopaminergic-neuron loss signature** (TH, SLC6A3, SLC18A2,
  DDC, DRD2). The benchmark therefore reports TWO known-gene tiers separately, and tests
  pathway enrichment on a nominal-p + fold-change DE set (field-standard for underpowered
  studies) in addition to the FDR set.
* This is a single-cohort sanity/validation run, not a replication study.

Steps:
  1. Load GSE7621 series matrix (GPL570) + GPL570 probe->gene annotation (real public data).
  2. Parse, infer case/control groups, map probes -> genes (engine functions).
  3. Differential expression (Welch t-test + Bonferroni + Benjamini-Hochberg) via engine.
  4. Pathway enrichment (hypergeometric) via engine, on FDR and nominal DE sets.
  5. Rank biomarker candidates via engine.
  6. BLIND BENCHMARK:
       - Known-gene recovery, two tiers (Mendelian drivers / dopaminergic signature).
       - Pathway sanity: dopamine / mitochondrial / oxidative / immune.
       - Reproducibility: commit hash + env + data sha256 + seed policy.

Outputs (--output-dir, default github/docs/case-study/):
  GSE7621_deg.csv, GSE7621_top_candidates.csv, GSE7621_pathway_enrichment.csv,
  GSE7621_volcano.png, GSE7621_report.txt, GSE7621_evidence_package.json

Usage:
  python case_study_pd.py \
      --matrix-path /tmp/gse7621_matrix.txt.gz \
      --annot-path  /tmp/gpl570.annot.gz \
      --output-dir  ../docs/case-study
  # or auto-download:
  python case_study_pd.py --output-dir ../docs/case-study
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
import demo_biomarker_discovery as engine  # noqa: E402

MPLCONFIGDIR = "/tmp/matplotlib"
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GEO_ID = "GSE7621"
PLATFORM = "GPL570"

# Known PD biology, split into two tiers (see Design notes above).
MENDELIAN_DRIVERS = ["SNCA", "LRRK2", "PARK7", "PINK1", "PRKN", "GBA"]
DOPAMINERGIC_SIGNATURE = ["TH", "SLC6A3", "SLC18A2", "DDC", "DRD2", "MAOA", "COMT"]

# Pathway-sanity gene-set labels the benchmark expects to light up.
PATHWAY_SANITY_KEYS = {
    "dopamine metabolism": ["KEGG:Dopaminergic synapse", "GO_BP:dopamine metabolic process",
                             "GO_BP:synaptic transmission, dopaminergic"],
    "mitochondrial dysfunction": ["KEGG:Oxidative phosphorylation", "GO_BP:mitochondrial electron transport",
                                  "KEGG:Mitophagy - animal"],
    "oxidative stress": ["GO_BP:response to oxidative stress", "KEGG:Glutathione metabolism"],
    "immune response": ["GO_BP:inflammatory response"],
}

# Nominal DE filter for enrichment when FDR is underpowered (n small).
NOMINAL_P = 0.05
NOMINAL_LFC = 0.3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def to_grouped_df(expr_genes, groups, sample_ids):
    cols = pd.MultiIndex.from_arrays([groups, sample_ids], names=["group", "sample"])
    expr_genes.columns = cols
    return expr_genes


def git_commit(repo_dir):
    try:
        return subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Blind benchmark evaluation
# ---------------------------------------------------------------------------
def evaluate_recovery(deg_df, known_genes, top_n=100):
    # Volcano-style ranking uses nominal p-value (standard biologist-facing ranking).
    score = -np.log10(np.clip(deg_df["p_value"], 1e-300, 1.0)) * np.abs(deg_df["log2FoldChange"])
    ranked = deg_df.assign(score=score).sort_values("score", ascending=False)
    total = len(ranked)
    details = []
    for g in known_genes:
        if g in ranked.index:
            rank = int(ranked.index.get_loc(g)) + 1
            details.append({
                "gene": g, "present": True, "rank": rank,
                "rank_percentile": round(rank / total * 100, 2),
                "log2FoldChange": round(float(ranked.loc[g, "log2FoldChange"]), 4),
                "p_value": float(ranked.loc[g, "p_value"]),
                "q_value": float(ranked.loc[g, "q_value"]),
                "in_top100": rank <= top_n,
            })
        else:
            details.append({"gene": g, "present": False, "rank": None,
                            "rank_percentile": None, "log2FoldChange": None,
                            "p_value": None, "q_value": None, "in_top100": False})
    in_top100 = [d for d in details if d["in_top100"]]
    fdr_sig = set(deg_df[deg_df["significant_fdr"]].index.tolist())
    bonf_sig = set(deg_df[deg_df["significant"]].index.tolist())
    recovered_in_fdr = [g for g in known_genes if g in fdr_sig]
    recovered_in_bonf = [g for g in known_genes if g in bonf_sig]
    return {
        "total_genes_ranked": total,
        "ranking_metric": "volcano score = -log10(p_value) * |log2FC| (nominal p)",
        "known_genes": known_genes,
        "n_known_present": sum(d["present"] for d in details),
        "n_in_top100": len(in_top100),
        "n_recovered_in_fdr_significant": len(recovered_in_fdr),
        "recovered_in_fdr_significant": recovered_in_fdr,
        "n_recovered_in_bonferroni_significant": len(recovered_in_bonf),
        "recovered_in_bonferroni_significant": recovered_in_bonf,
        "details": details,
    }


def evaluate_pathway_sanity(enrich_df):
    out = {}
    for label, keys in PATHWAY_SANITY_KEYS.items():
        hits = enrich_df[enrich_df["pathway"].isin(keys)]
        sig_hits = hits[hits["significant"]]
        out[label] = {
            "tested_pathways": keys,
            "any_significant": len(sig_hits) > 0,
            "significant_pathways": sig_hits["pathway"].tolist(),
            "min_p": float(hits["p_value"].min()) if not hits.empty else 1.0,
        }
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="GSE7621 Parkinson's disease real-data case study")
    ap.add_argument("--matrix-path", default=None, help="Pre-downloaded GSE7621 series matrix .gz")
    ap.add_argument("--annot-path", default=None, help="Pre-downloaded GPL570.annot.gz")
    ap.add_argument("--data-dir", default=os.path.join(HERE, "data"), help="Cache dir for auto-download")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--top_n", type=int, default=20)
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.data_dir, exist_ok=True)

    # ---- 1. obtain data (real public data) ----
    matrix_path = args.matrix_path or os.path.join(args.data_dir, f"{GEO_ID}_series_matrix.txt.gz")
    annot_path = args.annot_path or os.path.join(args.data_dir, f"{PLATFORM}.annot.gz")

    if args.matrix_path and os.path.exists(matrix_path) and args.annot_path and os.path.exists(annot_path):
        expr_probes, groups, sample_ids = engine.parse_series_matrix(matrix_path)
        annot = engine.parse_annotation(annot_path)
        expr_genes = engine.map_probes_to_genes(expr_probes, annot)
        expr_grouped = to_grouped_df(expr_genes, groups, sample_ids)
        matrix_hash = sha256_of(matrix_path)
        annot_hash = sha256_of(annot_path)
        data_mode = "real_public_data (pre-downloaded)"
    else:
        expr_grouped = engine.download_geo_dataset(GEO_ID, args.data_dir, platform_id=PLATFORM)
        if expr_grouped is None:
            print("[warn] real download failed; using synthetic fallback", file=sys.stderr)
            expr_grouped = engine.generate_synthetic_expression(n_genes=2000, n_samples=40, seed=42)
            matrix_hash = annot_hash = "n/a (synthetic fallback)"
            data_mode = "synthetic_fallback"
        else:
            matrix_path = os.path.join(args.data_dir, f"{GEO_ID}_series_matrix.txt.gz")
            annot_path = os.path.join(args.data_dir, f"{PLATFORM}.annot.gz")
            matrix_hash = sha256_of(matrix_path) if os.path.exists(matrix_path) else "n/a"
            annot_hash = sha256_of(annot_path) if os.path.exists(annot_path) else "n/a"
            data_mode = "real_public_data (auto-downloaded)"

    groups = list(expr_grouped.columns.get_level_values("group"))
    if expr_grouped.columns.nlevels == 2:
        sample_ids = list(expr_grouped.columns.get_level_values("sample"))
    else:
        sample_ids = list(expr_grouped.columns)

    # ---- 2-4. framework engine ----
    deg_df = engine.differential_expression(expr_grouped, alpha=args.alpha)
    # Enrichment on two DE definitions (FDR set + nominal-p/fold-change set).
    fdr_genes = deg_df[deg_df["significant_fdr"]].index.tolist()
    nominal_genes = deg_df[(deg_df["p_value"] < NOMINAL_P) &
                           (deg_df["log2FoldChange"].abs() >= NOMINAL_LFC)].index.tolist()
    enrich_fdr = engine.pathway_enrichment(deg_df, alpha=args.alpha, de_gene_set=fdr_genes)
    enrich_nominal = engine.pathway_enrichment(deg_df, alpha=args.alpha, de_gene_set=nominal_genes)
    top_df = engine.rank_biomarkers(deg_df, top_n=args.top_n)

    # ---- 5. blind benchmark ----
    rec_mendel = evaluate_recovery(deg_df, MENDELIAN_DRIVERS, top_n=100)
    rec_dopa = evaluate_recovery(deg_df, DOPAMINERGIC_SIGNATURE, top_n=100)
    # Pathway sanity is most informative on the nominal DE set (FDR is underpowered at n=25).
    sanity = evaluate_pathway_sanity(enrich_nominal)

    # ---- outputs ----
    deg_path = os.path.join(args.output_dir, "GSE7621_deg.csv")
    top_path = os.path.join(args.output_dir, "GSE7621_top_candidates.csv")
    enrich_path = os.path.join(args.output_dir, "GSE7621_pathway_enrichment.csv")
    volcano_path = os.path.join(args.output_dir, "GSE7621_volcano.png")
    report_path = os.path.join(args.output_dir, "GSE7621_report.txt")
    pkg_path = os.path.join(args.output_dir, "GSE7621_evidence_package.json")

    deg_df.to_csv(deg_path)
    top_df.to_csv(top_path)
    # combine both enrichment tables with a tag
    enrich_fdr = enrich_fdr.copy(); enrich_fdr["de_set"] = "FDR"
    enrich_nominal = enrich_nominal.copy(); enrich_nominal["de_set"] = "nominal"
    pd.concat([enrich_fdr, enrich_nominal], ignore_index=True).to_csv(enrich_path, index=False)
    engine.plot_volcano(deg_df, alpha=args.alpha, outpath=volcano_path)

    def fmt_rec(rec):
        s = ""
        s += f"  In top 100 (volcano)  : {rec['n_in_top100']} / {len(rec['known_genes'])}\n"
        s += f"  Present (of {len(rec['known_genes'])})  : {rec['n_known_present']} / {len(rec['known_genes'])}\n"
        s += f"  In FDR-sig DEGs       : {rec['n_recovered_in_fdr_significant']} / {len(rec['known_genes'])} " \
             f"{rec['recovered_in_fdr_significant']}\n"
        for d in rec["details"]:
            if d["present"]:
                s += f"  {d['gene']:8s} rank={d['rank']:5d} ({d['rank_percentile']:.2f}%) " \
                     f"log2FC={d['log2FoldChange']:+.3f} p={d['p_value']:.2e} q={d['q_value']:.2e}\n"
            else:
                s += f"  {d['gene']:8s} NOT PRESENT in dataset (no probe mapped / not on array)\n"
        return s

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("GSE7621 Parkinson's Disease — Real-Data Case Study\n")
        fh.write("=" * 64 + "\n\n")
        fh.write(f"Data mode                : {data_mode}\n")
        fh.write(f"Platform                 : {PLATFORM} (Affymetrix HG-U133_Plus_2)\n")
        fh.write(f"Samples                  : {expr_grouped.shape[1]} "
                 f"({groups.count('control')} control / {groups.count('case')} case)\n")
        fh.write(f"Genes analyzed           : {deg_df.shape[0]}\n")
        fh.write(f"Bonferroni-significant    : {deg_df['significant'].sum()}\n")
        fh.write(f"FDR(q<{args.alpha})-significant: {deg_df['significant_fdr'].sum()}\n")
        fh.write(f"Nominal DE (p<{NOMINAL_P}, |lfc|>={NOMINAL_LFC}): {len(nominal_genes)}\n\n")
        fh.write("KNOWN PD GENE RECOVERY — Mendelian drivers (subtle in bulk SN)\n")
        fh.write("-" * 64 + "\n")
        fh.write(fmt_rec(rec_mendel))
        fh.write("\nKNOWN PD GENE RECOVERY — Dopaminergic signature (recoverable)\n")
        fh.write("-" * 64 + "\n")
        fh.write(fmt_rec(rec_dopa))
        fh.write("\nPATHWAY SANITY (nominal DE set)\n")
        fh.write("-" * 64 + "\n")
        for label, s in sanity.items():
            fh.write(f"  {label:24s} significant={s['any_significant']}  min_p={s['min_p']:.3g}\n")
        fh.write("\nTOP 15 CANDIDATES (volcano rank)\n")
        fh.write("-" * 64 + "\n")
        for gene, row in top_df.head(15).iterrows():
            direction = "UP" if row["log2FoldChange"] > 0 else "DOWN"
            fh.write(f"  {gene:12s} {direction:4s} log2FC={row['log2FoldChange']:+.3f} "
                     f"p={row['p_value']:.2e} q={row['q_value']:.2e}\n")

    pkg = {
        "metadata": {
            "case_study": "GSE7621 Parkinson's disease",
            "dataset": f"GEO:{GEO_ID}",
            "platform": PLATFORM,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.1.0 + case-study-pd",
            "mode": data_mode,
        },
        "provenance": {
            "git_commit": git_commit(os.path.join(HERE, "..", "..")),
            "python": sys.version.split()[0],
            "env": "managed venv (python3.13 + pandas/numpy/scipy/matplotlib/requests)",
            "matrix_sha256": matrix_hash,
            "annot_sha256": annot_hash,
            "seed_policy": "N/A (real data; DE is deterministic Welch t-test + Bonferroni + BH)",
        },
        "methods": ["download_geo", "parse_series_matrix", "probe_to_gene_map", "log2_transform_if_linear",
                     "welch_ttest", "bonferroni", "benjamini_hochberg", "hypergeometric_enrichment",
                     "candidate_ranking"],
        "results": {
            "n_samples": int(expr_grouped.shape[1]),
            "n_control": int(groups.count("control")),
            "n_case": int(groups.count("case")),
            "n_genes": int(deg_df.shape[0]),
            "n_significant_bonferroni": int(deg_df["significant"].sum()),
            "n_significant_fdr": int(deg_df["significant_fdr"].sum()),
            "n_nominal_de": len(nominal_genes),
            "n_significant_pathways_fdr": int(enrich_fdr["significant"].sum()) if not enrich_fdr.empty else 0,
            "n_significant_pathways_nominal": int(enrich_nominal["significant"].sum()) if not enrich_nominal.empty else 0,
        },
        "benchmark": {
            "known_gene_recovery_mendelian_drivers": rec_mendel,
            "known_gene_recovery_dopaminergic_signature": rec_dopa,
            "pathway_sanity_nominal": sanity,
        },
        "evidence_grade": "B (real public data; bulk microarray; single cohort)",
        "limitations": [
            "Bulk tissue (substantia nigra) masks cell-type-specific signal",
            "Small cohort (n=25, 9 control / 16 case); Mendelian PD driver genes are underpowered for FDR",
            "Single cohort, no independent replication within this case study",
            "Probe->gene mapping collapses multiple probes per gene by mean",
            "Built-in pathway gene sets are illustrative (KEGG/GO subsets), not a full MSigDB run",
        ],
        "next_validation": "Independent cohort replication (e.g., GSE49036, ROSMAP) + scRNA-seq deconvolution + full MSigDB/KEGG enrichment",
    }
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 64)
    print("GSE7621 CASE STUDY COMPLETE")
    print("=" * 64)
    print(f"Data mode : {data_mode}")
    print(f"Samples: {expr_grouped.shape[1]} | Genes: {deg_df.shape[0]} | "
          f"FDR-DEGs: {deg_df['significant_fdr'].sum()} | Nominal-DEGs: {len(nominal_genes)}")
    print(f"Mendelian drivers top100 : {rec_mendel['n_in_top100']} / {len(MENDELIAN_DRIVERS)}  "
          f"FDR-sig: {rec_mendel['n_recovered_in_fdr_significant']}")
    print(f"Dopaminergic sig top100  : {rec_dopa['n_in_top100']} / {len(DOPAMINERGIC_SIGNATURE)}  "
          f"FDR-sig: {rec_dopa['n_recovered_in_fdr_significant']}")
    print("Pathway sanity (nominal):")
    for label, s in sanity.items():
        print(f"  {label:24s} significant={s['any_significant']} min_p={s['min_p']:.3g}")
    print(f"Evidence package -> {pkg_path}")


if __name__ == "__main__":
    main()
