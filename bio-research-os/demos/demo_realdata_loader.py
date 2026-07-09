#!/usr/bin/env python3
"""
Real-Data Adapter for the Causal-Evidence Engine (supports Case 6)
=================================================================

Loads REAL PUBLIC summary-level data and feeds it into the framework's
causal-evidence engine (demo_causal_evidence.py): run_coloc / twas_z /
fine_map_credible_set / wald_ratio_mr.

DATA (user-local PUBLIC summary files; NEVER committed to the repo)
-------------------------------------------------------------------
  * AD GWAS summary stats : Jansen et al. 2019 (IGAP-style), hg19, ~9.6M SNPs.
        columns: uniqID.a1a2 CHR BP A1 A2 SNP Z P Nsum ... BETA SE
  * Brain eQTL summary    : GTEx v8, 13 brain tissues, hg38.
        columns: gene_name rs_id_dbSNP151_GRCh38p7 ref alt slope slope_se pval_nominal ...

MATCHING STRATEGY (build-agnostic)
----------------------------------
  * GTEx variant_id is hg38 (chr_pos_ref_alt_b38); Jansen is hg19.
  * We match by dbSNP rsID (GTEx rs_id_dbSNP151_GRCh38p7 <-> Jansen SNP) -- build independent.
  * Alleles harmonized: align Jansen (A1,A2) to GTEx (ref,alt); ambiguous / strand-flipped
    SNPs are dropped (flagged in limitations).

HONEST EVIDENCE GRADE: B (real public data), with explicit limitations (see run output
and the evidence package). This is a METHODOLOGY DEMONSTRATION of the engine on real
summary data, NOT a definitive etiological claim. A definitive TWAS / fine-mapping needs
full eQTL weights + an LD reference panel (eQTLGen / MetaBrain where governed, 1000G LD).

GOVERNANCE: MetaBrain / UKB-PPP / ADNI / deCODE are DUA-bound and OUT OF SCOPE
(DATA_GOVERNANCE.md). Only public summary files are read here; raw data never enters the repo.
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

# Configure matplotlib before any plotting import.
MPLCONFIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".matplotlib_cache")
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import demo_causal_evidence as ce  # noqa: E402

# User-local PUBLIC summary-file defaults (supply via --gwas-path / --eqtl-dir).
# These point at already-downloaded PUBLIC data on YOUR machine; they are NOT in
# the repo. Set BIORESEARCH_PUBLIC_DATA to your local raw-data root (the dir that
# contains raw/gwas/... and raw/eqtl/...), or pass the explicit --gwas-path /
# --eqtl-dir flags. Left empty when the env var is unset so the CLI fails loudly
# with a clear hint instead of shipping a developer-specific absolute path.
_DATA_ROOT = os.environ.get("BIORESEARCH_PUBLIC_DATA", "")
DEFAULT_GWAS = os.path.join(_DATA_ROOT, "raw/gwas/JansenIE_2019/AD_sumstats_Jansenetal_2019sept.txt.gz") if _DATA_ROOT else ""
DEFAULT_EQTL_DIR = os.path.join(_DATA_ROOT, "raw/eqtl/gtex/GTEx_Analysis_v8_eQTL") if _DATA_ROOT else ""

BRAIN_TISSUES = [
    "Brain_Amygdala", "Brain_Anterior_cingulate_cortex_BA24", "Brain_Caudate_basal_ganglia",
    "Brain_Cerebellar_Hemisphere", "Brain_Cerebellum", "Brain_Cortex", "Brain_Frontal_Cortex_BA9",
    "Brain_Hippocampus", "Brain_Hypothalamus", "Brain_Nucleus_accumbens_basal_ganglia",
    "Brain_Putamen_basal_ganglia", "Brain_Spinal_cord_cervical_c-1", "Brain_Substantia_nigra",
]
DEFAULT_GENES = ["TREM2", "BIN1", "CLU", "PICALM", "APOE"]


# ---------------------------------------------------------------------------
# 1. Load GTEx cis-eQTL lead SNPs for target genes across brain tissues
# ---------------------------------------------------------------------------
def load_gtex_eqtl_leads(genes, eqtl_dir, tissues=None):
    """Return {gene: {rsid: {ref, alt, slope, slope_se, pval, tissue}}}.

    For each gene we collect the lead cis-eQTL SNP reported in every brain tissue
    (GTEx egenes = one lead SNP per gene per tissue). Deduplicated by rsID so each
    SNP appears once. This yields the gene's cross-tissue cis-eQTL signal.
    """
    tissues = tissues or BRAIN_TISSUES
    out = {g: {} for g in genes}
    for t in tissues:
        fp = os.path.join(eqtl_dir, f"{t}.v8.egenes.txt.gz")
        if not os.path.exists(fp):
            print(f"[WARN] missing tissue file: {fp}", file=sys.stderr)
            continue
        df = pd.read_csv(
            fp, sep="\t", compression="gzip",
            usecols=["gene_name", "rs_id_dbSNP151_GRCh38p7", "ref", "alt",
                     "slope", "slope_se", "pval_nominal"],
        )
        for g in genes:
            sub = df[df["gene_name"] == g]
            for _, r in sub.iterrows():
                rs = r["rs_id_dbSNP151_GRCh38p7"]
                if not isinstance(rs, str) or rs == "":
                    continue
                if rs not in out[g]:
                    out[g][rs] = dict(
                        ref=r["ref"], alt=r["alt"], slope=float(r["slope"]),
                        slope_se=float(r["slope_se"]), pval=float(r["pval_nominal"]),
                        tissue=t,
                    )
    return out


# ---------------------------------------------------------------------------
# 2. Stream Jansen AD GWAS, keep only target rsIDs
# ---------------------------------------------------------------------------
def stream_jansen_gwas(target_rsids, gwas_path):
    """Return {rsid: {beta, se, a1, a2, chr, bp, eaf, n}} for matched SNPs only."""
    matched = {}
    target = set(target_rsids)
    with gzip.open(gwas_path, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in fh:
            p = line.rstrip("\n").split("\t")
            snp = p[idx["SNP"]]
            if snp in target:
                matched[snp] = dict(
                    beta=float(p[idx["BETA"]]), se=float(p[idx["SE"]]),
                    a1=p[idx["A1"]], a2=p[idx["A2"]],
                    chr=p[idx["CHR"]], bp=p[idx["BP"]],
                    eaf=p[idx["EAF"]], n=p[idx["Nsum"]],
                )
    return matched


# ---------------------------------------------------------------------------
# 3. Allele harmonization + array assembly
# ---------------------------------------------------------------------------
def harmonize(eqtl_map, gwas_map):
    """Per gene, align GWAS allele to GTEx (ref, alt); drop ambiguous SNPs.

    Returns {gene: {snps, beta_expr, se_expr, beta_trait, se_trait, n_match,
                    n_eqtl, tissues, best_tissue}}.
    """
    res = {}
    for g, snps in eqtl_map.items():
        rows = []
        tissues = set()
        best_tissue, best_p = None, np.inf
        for rs, d in snps.items():
            gm = gwas_map.get(rs)
            if gm is None:
                continue
            ref, alt = d["ref"], d["alt"]
            a1, a2 = gm["a1"], gm["a2"]
            if a1 == ref and a2 == alt:
                b_gwas = gm["beta"]  # effect of ALT (== GTEx alt) on AD log-odds
                aligned = True
            elif a1 == alt and a2 == ref:
                b_gwas = -gm["beta"]  # flip: now effect of GTEx alt on AD
                aligned = True
            else:
                aligned = False  # strand/ambiguous -> drop
            if not aligned:
                continue
            rows.append(dict(rs=rs, slope=d["slope"], slope_se=d["slope_se"],
                             gwas_beta=b_gwas, gwas_se=gm["se"], pval=d["pval"]))
            tissues.add(d["tissue"])
            if d["pval"] < best_p:
                best_p, best_tissue = d["pval"], d["tissue"]
        if not rows:
            res[g] = dict(snps=[], beta_expr=np.array([]), se_expr=np.array([]),
                          beta_trait=np.array([]), se_trait=np.array([]),
                          n_match=0, n_eqtl=len(snps), tissues=[], best_tissue=None)
            continue
        h = pd.DataFrame(rows)
        res[g] = dict(
            snps=list(h["rs"]),
            beta_expr=h["slope"].values.astype(float),
            se_expr=h["slope_se"].values.astype(float),
            beta_trait=h["gwas_beta"].values.astype(float),
            se_trait=h["gwas_se"].values.astype(float),
            pvals=h["pval"].values.astype(float),
            n_match=len(rows), n_eqtl=len(snps),
            tissues=sorted(tissues), best_tissue=best_tissue,
        )
    return res


# ---------------------------------------------------------------------------
# 4. Per-gene causal evidence (engine calls)
# ---------------------------------------------------------------------------
def analyze_gene(g, gd):
    if gd["n_match"] == 0:
        return None, []
    be, se_e = gd["beta_expr"], gd["se_expr"]
    bt, se_t = gd["beta_trait"], gd["se_trait"]
    coloc = ce.run_coloc(be, se_e, bt, se_t)
    twas = ce.twas_z(be, bt, se_t)
    fm = ce.fine_map_credible_set(bt, se_t)
    li = int(np.argmin(gd["pvals"]))  # lead eQTL SNP as MR instrument
    mr = ce.wald_ratio_mr(be, se_e, bt, se_t, li)
    rec = {
        "gene": g,
        "n_eqtl_leads": gd["n_eqtl"],
        "n_matched": gd["n_match"],
        "best_tissue": gd["best_tissue"],
        "PP.H4": coloc["PP.H4"],
        "PP.H3": coloc["PP.H3"],
        "PP.H1": coloc["PP.H1"],
        "PP.H2": coloc["PP.H2"],
        "twas_z": twas["z"],
        "twas_p": twas["p_value"],
        "twas_significant": bool(twas["p_value"] < 0.05),
        "mr_beta": mr["beta"],
        "mr_se": mr["se"],
        "mr_p": mr["p_value"],
        "mr_ci_lower": mr["ci_lower"],
        "mr_ci_upper": mr["ci_upper"],
        "n_credible": fm["n_cs"],
        "mr_instrument": gd["snps"][li],
    }
    cred_rows = []
    for j, rs in enumerate(gd["snps"]):
        cred_rows.append(dict(gene=g, rs=rs, pip=float(fm["pip"][j]),
                              in_credible_set=bool(fm["credible_set_mask"][j])))
    return rec, cred_rows


# ---------------------------------------------------------------------------
# 5. Plot PP.H4 per gene (real-data heatmap)
# ---------------------------------------------------------------------------
def plot_real_pph4(per_gene_df, outpath):
    df = per_gene_df.sort_values("gene")
    h4 = df["PP.H4"].values.reshape(-1, 1)
    sig = df["twas_significant"].values
    fig, ax = plt.subplots(figsize=(4, max(3, 0.5 * len(df) + 1)))
    im = ax.imshow(h4, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_yticks(range(len(df)))
    labels = [f"{g}  (TWAS{'*' if s else ''})" for g, s in zip(df["gene"], sig)]
    ax.set_yticklabels(labels)
    ax.set_xticks([0])
    ax.set_xticklabels(["PP.H4"])
    for i, v in enumerate(h4[:, 0]):
        ax.text(0, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v < 0.5 else "black", fontsize=8)
    ax.set_title("Real-data colocalization PP.H4 (Jansen AD GWAS x GTEx brain eQTL)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# 6. Orchestration
# ---------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_real_causal_chain(gwas_path, eqtl_dir, genes=None, tissues=None, outdir="."):
    genes = genes or DEFAULT_GENES
    tissues = tissues or BRAIN_TISSUES
    os.makedirs(outdir, exist_ok=True)

    print("[1/4] Loading GTEx brain cis-eQTL leads ...", file=sys.stderr)
    eqtl_map = load_gtex_eqtl_leads(genes, eqtl_dir, tissues)
    all_rs = set()
    for g in genes:
        all_rs |= set(eqtl_map[g].keys())
    print(f"      unique eQTL rsIDs (genes x tissues): {len(all_rs)}", file=sys.stderr)

    print("[2/4] Streaming Jansen 2019 AD GWAS (single pass) ...", file=sys.stderr)
    gwas_map = stream_jansen_gwas(all_rs, gwas_path)
    print(f"      rsIDs matched in GWAS: {len(gwas_map)}", file=sys.stderr)

    print("[3/4] Harmonizing alleles + running engine ...", file=sys.stderr)
    harm = harmonize(eqtl_map, gwas_map)
    per_gene, cred_rows = [], []
    for g in genes:
        rec, cr = analyze_gene(g, harm[g])
        if rec is not None:
            per_gene.append(rec)
            cred_rows.extend(cr)
    per_gene_df = pd.DataFrame(per_gene)
    cred_df = pd.DataFrame(cred_rows)

    print("[4/4] Writing outputs ...", file=sys.stderr)
    per_gene_path = os.path.join(outdir, "CE_real_per_gene.csv")
    cred_path = os.path.join(outdir, "CE_real_credible_sets.csv")
    heatmap_path = os.path.join(outdir, "CE_real_locus_heatmap.png")
    report_path = os.path.join(outdir, "CE_real_summary_report.txt")
    pkg_path = os.path.join(outdir, "CE_real_evidence_package.json")

    per_gene_df.to_csv(per_gene_path, index=False)
    cred_df.to_csv(cred_path, index=False)
    plot_real_pph4(per_gene_df, heatmap_path)

    n_coloc = int((per_gene_df["PP.H4"] > 0.8).sum())
    n_mr_sig = int((per_gene_df["mr_p"] < 0.05).sum())

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("Real-Data Causal Evidence Chain (Case 6) -- Jansen AD GWAS x GTEx brain eQTL\n")
        fh.write("=" * 72 + "\n\n")
        fh.write("EVIDENCE GRADE: B (real public summary data; lead cis-eQTL only; rsID-matched; no LD)\n\n")
        fh.write(f"Target genes : {', '.join(genes)}\n")
        fh.write(f"GWAS         : Jansen et al. 2019 (AD case/control, hg19)\n")
        fh.write(f"eQTL         : GTEx v8, {len(tissues)} brain tissues (hg38)\n")
        fh.write(f"Genes w/ >=1 matched SNP : {len(per_gene_df)}/{len(genes)}\n")
        fh.write(f"Genes colocalized (PP.H4>0.8): {n_coloc}\n")
        fh.write(f"Genes w/ significant MR (p<0.05): {n_mr_sig}\n\n")
        fh.write("Per-gene results\n" + "-" * 72 + "\n")
        fh.write(per_gene_df.to_string(index=False))
        fh.write("\n\nLimitations\n" + "-" * 72 + "\n")
        fh.write("- Lead cis-eQTL only (GTEx egenes = 1 lead SNP/gene/tissue, aggregated across 13 brain tissues); full eQTL weights (all genic SNPs) NOT used -> simplified TWAS/Multi-SNP MR.\n")
        fh.write("- SNPs within a gene locus are in LD; coloc/TWAS treat them as independent (no LD reference). Real fine-mapping needs 1000G/reference LD.\n")
        fh.write("- Matching is by dbSNP rsID (build-independent); SNPs without rsID or strand-ambiguous alleles were dropped.\n")
        fh.write("- Wald-ratio MR uses the single lead eQTL SNP as instrument (no horizontal-pleiotropy/LD adjustment).\n")
        fh.write("- GTEx eQTL are from mostly non-diseased tissue; AD GWAS is case/control. Cross-tissue cis signal aggregated as a simplification.\n")
        fh.write("- No individual-level / controlled-access data used (MetaBrain/UKB-PPP/ADNI/deCODE excluded per DATA_GOVERNANCE.md).\n")

    pkg = {
        "metadata": {
            "case_study": "Real-Data Causal Evidence Chain (AD GWAS -> brain eQTL -> coloc -> TWAS -> fine-map -> MR)",
            "workflow": "causal-evidence",
            "domain": "Alzheimer's disease (real public summary data)",
            "target_genes": genes,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.5 + causal-evidence engine + realdata adapter",
            "mode": "real public summary-level data (no individual-level, no controlled-access)",
        },
        "provenance": {
            "git_commit": _git_commit(os.path.join(HERE, "..")),
            "python": sys.version.split()[0],
            "env": "managed venv (python3.13 + numpy/pandas/scipy/matplotlib)",
            "gwas_source": "Jansen et al. 2019 AD GWAS summary stats (local public file)",
            "gwas_path": gwas_path,
            "gwas_sha256": sha256_of(gwas_path),
            "eqtl_source": "GTEx v8 brain eQTL (local public files)",
            "eqtl_dir": eqtl_dir,
            "eqtl_tissues": tissues,
            "engine": "demo_causal_evidence.py (run_coloc, twas_z, fine_map_credible_set, wald_ratio_mr)",
            "raw_data_in_repo": False,
        },
        "methods": ["load_gtex_eqtl_leads", "stream_jansen_gwas", "harmonize",
                    "run_coloc", "twas_z", "fine_map_credible_set", "wald_ratio_mr"],
        "results": {
            "n_target_genes": len(genes),
            "n_genes_with_match": int(len(per_gene_df)),
            "n_colocalized_PP.H4_gt_0.8": n_coloc,
            "n_significant_MR_p_lt_0.05": n_mr_sig,
            "per_gene": per_gene_df.to_dict(orient="records"),
            "credible_sets_rows": len(cred_df),
        },
        "evidence_grade": "B (real public summary data: Jansen 2019 AD GWAS + GTEx v8 brain eQTL; lead cis-eQTL only, rsID-matched, no LD)",
        "limitations": [
            "Lead cis-eQTL only (GTEx egenes aggregated across 13 brain tissues); full eQTL weights not used",
            "SNPs in LD treated as independent (no LD reference panel)",
            "Matched by dbSNP rsID; SNPs lacking rsID or strand-ambiguous dropped",
            "Wald-ratio MR uses single lead eQTL SNP as instrument (no pleiotropy/LD adjustment)",
            "GTEx eQTL from non-diseased tissue; AD GWAS case/control; cross-tissue cis signal aggregated",
            "No individual-level / controlled-access data (MetaBrain/UKB-PPP/ADNI/deCODE excluded)",
        ],
        "next_validation": "Definitive TWAS (S-PrediXcan/FUSION with full eQTL weights) + LD-clumped coloc + fine-mapping with 1000G LD; eQTLGen or governed MetaBrain weights; replicate in independent AD GWAS (Wightman 2021 / Bellenguez 2022 / FinnGen).",
    }
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 72)
    print("REAL-DATA CAUSAL EVIDENCE CHAIN COMPLETE (Case 6)")
    print("=" * 72)
    print(f"Genes w/ match : {len(per_gene_df)}/{len(genes)}")
    print(f"Colocalized    : {n_coloc} (PP.H4>0.8)")
    print(f"Sig MR         : {n_mr_sig} (p<0.05)")
    print(f"Evidence grade : B (real public summary data)")
    print(f"Evidence pkg   -> {pkg_path}")
    print("=" * 72 + "\n")
    return pkg


def _git_commit(repo_dir):
    import subprocess
    try:
        return subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser(description="Real-data causal-evidence adapter (Case 6)")
    ap.add_argument("--gwas-path", default=DEFAULT_GWAS,
                    help="Local path to Jansen 2019 AD GWAS summary stats (.txt.gz, public).")
    ap.add_argument("--eqtl-dir", default=DEFAULT_EQTL_DIR,
                    help="Local dir of GTEx v8 *.v8.egenes.txt.gz (public).")
    ap.add_argument("--genes", default=",".join(DEFAULT_GENES),
                    help="Comma-separated target genes.")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    args = ap.parse_args()

    genes = [g.strip() for g in args.genes.split(",") if g.strip()]
    if not os.path.exists(args.gwas_path):
        sys.exit(f"[ERROR] GWAS file not found: {args.gwas_path!r}\n"
                 f"        Set BIORESEARCH_PUBLIC_DATA to your local raw-data root, or pass\n"
                 f"        --gwas-path <path> (Jansen 2019 AD sumstats .txt.gz, public).")
    if not os.path.isdir(args.eqtl_dir):
        sys.exit(f"[ERROR] eQTL dir not found: {args.eqtl_dir!r}\n"
                 f"        Set BIORESEARCH_PUBLIC_DATA to your local raw-data root, or pass\n"
                 f"        --eqtl-dir <dir> (GTEx v8 *.v8.egenes.txt.gz, public).")
    run_real_causal_chain(args.gwas_path, args.eqtl_dir, genes=genes,
                          outdir=args.output_dir)


if __name__ == "__main__":
    main()
