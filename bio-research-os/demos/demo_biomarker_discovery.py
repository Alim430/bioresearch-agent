#!/usr/bin/env python3
"""
Demo 2: Biomarker Discovery Pipeline
====================================
End-to-end biomarker discovery for Parkinson's disease using public GEO data
or realistic synthetic data as fallback.

Workflow:
  1. Download GEO dataset GSE7621 (Parkinson's substantia nigra) or generate synthetic data
  2. Differential expression analysis (t-test, case vs control)
  3. Pathway enrichment (hypergeometric test with built-in KEGG/GO mappings)
  4. Rank top biomarker candidates
  5. Generate volcano plot and summary report

Outputs:
  - {output_dir}/biomarker_deg_table.csv
  - {output_dir}/biomarker_top_candidates.csv
  - {output_dir}/biomarker_pathway_enrichment.csv
  - {output_dir}/biomarker_volcano_plot.png
  - {output_dir}/biomarker_report.txt

Usage:
  python demo_biomarker_discovery.py --disease "Parkinson's disease" --geo_id GSE7621 --alpha 0.05 --output-dir outputs/biomarker
"""

import argparse
import gzip
import os
import sys
import textwrap
from typing import List, Dict, Tuple

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
GEO_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE7nnn/GSE7621/matrix/"
GEO_FILENAME = "GSE7621_series_matrix.txt.gz"

# Built-in pathway gene sets (simplified for demo)
KEGG_PATHWAYS = {
    "Parkinson disease": ["SNCA", "LRRK2", "PARK7", "PINK1", "PRKN", "DJ1", "UCHL1", "GBA", "MAPT", "CYP2D6"],
    "Oxidative phosphorylation": ["MT-ND1", "MT-ND2", "MT-CO1", "MT-CO2", "MT-ATP6", "NDUFS1", "NDUFS2", "NDUFS3", "UQCRC1", "UQCRC2", "COX5B", "ATP5F1A"],
    "MAPK signaling pathway": ["MAPK1", "MAPK3", "MAPK8", "MAPK9", "MAPK14", "RAS", "RAF1", "MEK1", "ERK1", "JNK", "P38"],
    "Dopaminergic synapse": ["TH", "DDC", "SLC6A3", "DRD2", "DRD1", "SLC18A2", "COMT", "MAOA", "MAOB"],
    "Neurotrophin signaling pathway": ["NGF", "BDNF", "NTF3", "TRKA", "TRKB", "PIK3CA", "AKT1", "MAPK1", "RAS", "RAF1"],
    "Autophagy - animal": ["ATG5", "ATG7", "ATG12", "LC3B", "SQSTM1", "BECN1", "ULK1", "mTOR", "RPTOR", "RICTOR"],
    "Mitophagy - animal": ["PINK1", "PRKN", "OPTN", "TBK1", "NDP52", "CALCOCO2", "TAX1BP1", "SQSTM1", "BECN1"],
    "Glutathione metabolism": ["GSTM1", "GSTT1", "GSTP1", "GCLC", "GCLM", "GPX1", "GPX4", "GSR", "GSTO1"],
    "Citrate cycle (TCA cycle)": ["IDH1", "IDH2", "IDH3A", "OGDH", "SDHA", "SDHB", "SDHC", "SDHD", "FH", "MDH1", "MDH2", "CS"],
    "Amyotrophic lateral sclerosis": ["SOD1", "TARDBP", "FUS", "C9orf72", "VCP", "UBQLN2", "TBK1", "CCNF"],
}

GO_BP_TERMS = {
    "response to oxidative stress": ["SOD1", "SOD2", "CAT", "GPX1", "GPX4", "PRDX1", "PRDX2", "TXN", "TXNRD1", "NFE2L2"],
    "mitochondrial electron transport": ["MT-ND1", "MT-ND2", "MT-CO1", "MT-CO2", "NDUFS1", "NDUFS2", "NDUFS3", "UQCRC1", "COX5B", "ATP5F1A"],
    "protein ubiquitination": ["PRKN", "UBB", "UBC", "UBE2D1", "UBE2L3", "UCHL1", "PSMA1", "PSMB1", "UBQLN1", "UBQLN2"],
    "dopamine metabolic process": ["TH", "DDC", "MAOA", "MAOB", "COMT", "SLC6A3", "SLC18A2", "DRD2"],
    "neuron death": ["BAX", "BAK1", "CASP3", "CASP9", "PARP1", "AIFM1", "ENDOG", "CYCS", "APAF1", "BCL2", "BCL2L1"],
    "autophagosome assembly": ["ATG5", "ATG7", "ATG12", "MAP1LC3A", "MAP1LC3B", "SQSTM1", "BECN1", "ULK1", "ATG16L1"],
    "inflammatory response": ["TNF", "IL6", "IL1B", "NLRP3", "NFKB1", "RELA", "COX2", "PTGS2", "ICAM1", "VCAM1"],
    "synaptic transmission, dopaminergic": ["TH", "DDC", "SLC6A3", "DRD2", "DRD1", "SLC18A2", "VMAT2", "DAT", "COMT"],
}


def ensure_output_dir(output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    print(f"[PROGRESS] {msg}", file=sys.stderr)


def generate_synthetic_expression(n_genes: int = 2000, n_samples: int = 40, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic expression matrix mimicking PD vs control microarray data.
    Rows = genes, columns = samples. First half = control, second half = case.
    Some genes are differentially expressed.
    """
    rng = np.random.default_rng(seed)
    # Sample labels
    half = n_samples // 2
    labels = ["control"] * half + ["case"] * half

    gene_names = [f"GENE_{i:04d}" for i in range(n_genes)]
    # Override some with realistic names
    realistic = (
        list(KEGG_PATHWAYS["Parkinson disease"]) +
        list(GO_BP_TERMS["response to oxidative stress"]) +
        list(GO_BP_TERMS["mitochondrial electron transport"]) +
        list(GO_BP_TERMS["dopamine metabolic process"])
    )
    for i, name in enumerate(realistic[:n_genes]):
        gene_names[i] = name

    # Base expression log2-scale ~ N(6, 1.5)
    base = rng.normal(loc=6.0, scale=1.5, size=(n_genes, n_samples))

    # Introduce DE for ~10% genes (some up, some down in case)
    de_indices = rng.choice(n_genes, size=int(0.10 * n_genes), replace=False)
    for idx in de_indices:
        direction = rng.choice([-1, 1])
        effect_size = rng.uniform(0.8, 2.0)
        base[idx, half:] += direction * effect_size

    df = pd.DataFrame(base, index=gene_names, columns=[f"SAMPLE_{j:02d}" for j in range(n_samples)])
    df.columns = pd.MultiIndex.from_arrays([labels, df.columns], names=["group", "sample"])
    return df


def download_geo_dataset(geo_id: str, out_dir: str, timeout: int = 60) -> pd.DataFrame:
    """
    Attempt to download GSE7621 series matrix from GEO FTP.
    On failure, return None so caller can use synthetic data.
    """
    import requests
    url = f"{GEO_BASE_URL}{GEO_FILENAME}"
    print_progress(f"Attempting to download {geo_id} from {url} ...")
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 404:
            print_progress("Dataset not found at expected URL (404).")
            return None
        resp.raise_for_status()
        # Save to temp file and parse
        temp_path = os.path.join(out_dir, f"{geo_id}_series_matrix.txt.gz")
        with open(temp_path, "wb") as f:
            f.write(resp.content)
        print_progress(f"Downloaded {len(resp.content)} bytes to {temp_path}")
        # Parse series matrix
        with gzip.open(temp_path, "rt", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
        # Extract sample characteristics and expression table
        # This is a simplified parser; real GEO files have headers, platform info, etc.
        header_lines = [l for l in lines if l.startswith("!")]
        table_lines = [l for l in lines if not l.startswith("!") and l.strip()]
        if len(table_lines) < 2:
            print_progress("Downloaded file appears empty or malformed.")
            return None
        # First table line is header
        header = table_lines[0].strip().split("\t")
        data = [l.strip().split("\t") for l in table_lines[1:]]
        df = pd.DataFrame(data, columns=header)
        # First column is ID_REF; rest are expression values
        df = df.set_index(df.columns[0])
        # Attempt to infer sample groups from header lines
        group_map = {}
        for hl in header_lines:
            if "Sample_source_name_ch1" in hl or "Sample_characteristics_ch1" in hl:
                # e.g., !Sample_source_name_ch1\t substantia nigra, control\t substantia nigra, Parkinson's disease\t...
                parts = hl.strip().split("\t")
                key = parts[0].replace("!", "").strip()
                for i, val in enumerate(parts[1:], start=1):
                    if i - 1 < len(df.columns):
                        col = df.columns[i - 1]
                        group_map[col] = val.strip().lower()
        if group_map:
            labels = [group_map.get(c, "unknown") for c in df.columns]
            df.columns = pd.MultiIndex.from_arrays([labels, df.columns], names=["group", "sample"])
        else:
            # Fallback: assume first half control, second half case
            half = len(df.columns) // 2
            labels = ["control"] * half + ["case"] * (len(df.columns) - half)
            df.columns = pd.MultiIndex.from_arrays([labels, df.columns], names=["group", "sample"])
        # Convert to numeric
        df = df.apply(pd.to_numeric, errors="coerce")
        print_progress(f"Parsed GEO dataset: {df.shape[0]} genes x {df.shape[1]} samples.")
        return df
    except Exception as exc:
        print_progress(f"GEO download/parse failed ({exc}); will use synthetic data.")
        return None


def differential_expression(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Perform two-sample t-test for each gene (row) between case and control.
    Returns dataframe with log2 fold-change, t-statistic, p-value, and adjusted p-value (Bonferroni).
    """
    print_progress("Running differential expression analysis (t-test) ...")
    # Extract groups
    groups = df.columns.get_level_values("group").unique().tolist()
    if len(groups) != 2:
        raise ValueError(f"Expected exactly 2 groups, found: {groups}")
    g0, g1 = groups[0], groups[1]
    vals0 = df.loc[:, g0].values
    vals1 = df.loc[:, g1].values

    # Compute per-gene statistics
    n_genes = df.shape[0]
    log2fc = np.mean(vals1, axis=1) - np.mean(vals0, axis=1)
    tstats, pvals = stats.ttest_ind(vals1, vals0, axis=1, equal_var=False, nan_policy="omit")
    # Bonferroni correction
    pvals_adj = np.minimum(pvals * n_genes, 1.0)

    result = pd.DataFrame({
        "gene": df.index,
        "log2FoldChange": log2fc,
        "t_statistic": tstats,
        "p_value": pvals,
        "p_adjusted": pvals_adj,
        "significant": pvals_adj < alpha,
    })
    result = result.set_index("gene")
    print_progress(f"DEG analysis complete: {result['significant'].sum()} significant genes at alpha={alpha}.")
    return result


def hypergeometric_test(de_genes: set, pathway_genes: set, background: int) -> Tuple[float, float]:
    """
    One-sided hypergeometric test for enrichment.
    Returns (odds_ratio, p_value).
    """
    overlap = len(de_genes & pathway_genes)
    if overlap == 0 or background == 0:
        return 0.0, 1.0
    # scipy fisher exact is 2x2 contingency; we can use it as approximation for hypergeometric
    # contingency table:
    #                in pathway   not in pathway
    #   DE               a             b
    #   not DE           c             d
    a = overlap
    b = len(de_genes) - a
    c = len(pathway_genes) - a
    d = background - len(de_genes) - c
    # scipy.stats.fisher_exact with alternative='greater'
    try:
        odds_ratio, p_value = stats.fisher_exact([[a, b], [c, d]], alternative="greater")
    except ValueError:
        return 0.0, 1.0
    return odds_ratio, p_value


def pathway_enrichment(deg_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Run hypergeometric enrichment on built-in KEGG and GO pathways.
    """
    print_progress("Running pathway enrichment analysis ...")
    significant_genes = set(deg_df[deg_df["significant"]].index.tolist())
    background = deg_df.shape[0]
    all_pathways = {}
    all_pathways.update({f"KEGG:{k}": v for k, v in KEGG_PATHWAYS.items()})
    all_pathways.update({f"GO_BP:{k}": v for k, v in GO_BP_TERMS.items()})

    rows = []
    for pathway_name, gene_list in all_pathways.items():
        pathway_set = set(gene_list)
        # Only consider genes present in the dataset
        pathway_set = pathway_set & set(deg_df.index)
        if len(pathway_set) < 2:
            continue
        odds_ratio, pval = hypergeometric_test(significant_genes, pathway_set, background)
        rows.append({
            "pathway": pathway_name,
            "genes_in_pathway": len(pathway_set),
            "DE_genes_in_pathway": len(significant_genes & pathway_set),
            "odds_ratio": odds_ratio,
            "p_value": pval,
            "significant": pval < alpha,
            "gene_list": ",".join(sorted(pathway_set)),
        })

    enrich_df = pd.DataFrame(rows)
    if not enrich_df.empty:
        enrich_df = enrich_df.sort_values("p_value").reset_index(drop=True)
        print_progress(f"Pathway enrichment complete: {enrich_df['significant'].sum()} significant pathways.")
    else:
        print_progress("Pathway enrichment complete: 0 significant pathways.")
    return enrich_df
    if not enrich_df.empty:
        enrich_df = enrich_df.sort_values("p_value").reset_index(drop=True)
    print_progress(f"Pathway enrichment complete: {enrich_df['significant'].sum()} significant pathways.")
    return enrich_df


def rank_biomarkers(deg_df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Rank biomarker candidates by fold-change magnitude and significance.
    """
    print_progress("Ranking top biomarker candidates ...")
    df = deg_df.copy()
    # Ranking score: combination of -log10(p_adjusted) and abs(log2FC)
    df["score"] = -np.log10(np.clip(df["p_adjusted"], a_min=1e-300, a_max=1.0)) * np.abs(df["log2FoldChange"])
    df = df.sort_values("score", ascending=False).head(top_n)
    return df[["log2FoldChange", "p_value", "p_adjusted", "significant", "score"]]


def plot_volcano(deg_df: pd.DataFrame, alpha: float, outpath: str) -> None:
    """Generate a volcano plot of differential expression results."""
    print_progress("Generating volcano plot ...")
    plt.figure(figsize=(10, 8))
    x = deg_df["log2FoldChange"]
    y = -np.log10(np.clip(deg_df["p_adjusted"], a_min=1e-300, a_max=1.0))
    sig = deg_df["significant"]
    plt.scatter(x[~sig], y[~sig], c="gray", s=15, alpha=0.5, label="Not significant")
    plt.scatter(x[sig], y[sig], c="red", s=25, alpha=0.7, label="Significant")
    plt.axhline(-np.log10(alpha), color="blue", linestyle="--", linewidth=1)
    plt.axvline(0, color="black", linestyle="-", linewidth=0.5)
    plt.xlabel("Log2 Fold Change")
    plt.ylabel("-Log10 Adjusted P-value")
    plt.title("Volcano Plot: Differential Expression")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved volcano plot to {outpath}")


def save_report(deg_df: pd.DataFrame, top_df: pd.DataFrame, enrich_df: pd.DataFrame, outpath: str) -> None:
    """Save a plain-text summary report."""
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write("Biomarker Discovery Pipeline Report\n")
        fh.write("=" * 60 + "\n\n")
        fh.write(f"Total genes analyzed      : {deg_df.shape[0]}\n")
        fh.write(f"Significant DEGs          : {deg_df['significant'].sum()}\n")
        fh.write(f"Up-regulated (log2FC>0)   : {(deg_df['significant'] & (deg_df['log2FoldChange'] > 0)).sum()}\n")
        fh.write(f"Down-regulated (log2FC<0) : {(deg_df['significant'] & (deg_df['log2FoldChange'] < 0)).sum()}\n\n")
        fh.write("Top 10 Biomarker Candidates:\n")
        fh.write("-" * 60 + "\n")
        for gene, row in top_df.head(10).iterrows():
            direction = "UP" if row["log2FoldChange"] > 0 else "DOWN"
            fh.write(f"  {gene:15s} {direction:4s}  log2FC={row['log2FoldChange']:6.2f}  p_adj={row['p_adjusted']:.2e}\n")
        fh.write("\n")
        if not enrich_df.empty:
            fh.write("Top 5 Enriched Pathways:\n")
            fh.write("-" * 60 + "\n")
            for _, row in enrich_df.head(5).iterrows():
                fh.write(f"  {row['pathway']:40s} OR={row['odds_ratio']:.2f}  p={row['p_value']:.3f}  sig={row['significant']}\n")
    print_progress(f"Saved report to {outpath}")


def main():
    parser = argparse.ArgumentParser(
        description="Biomarker Discovery Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument(
        "--disease",
        type=str,
        default="Parkinson's disease",
        help="Disease name for context (default: Parkinson's disease).",
    )
    parser.add_argument(
        "--geo_id",
        type=str,
        default="GSE7621",
        help="GEO dataset ID to attempt download (default: GSE7621).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05).",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=20,
        help="Number of top biomarker candidates to report (default: 20).",
    )
    parser.add_argument(
        "--use_synthetic",
        action="store_true",
        help="Force usage of synthetic data instead of downloading GEO.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: demo_outputs/).",
    )
    args = parser.parse_args()

    out_dir = ensure_output_dir(args.output_dir)

    # Step 1: Load data
    if args.use_synthetic:
        print_progress("Using synthetic expression data as requested.")
        expr_df = generate_synthetic_expression(n_genes=2000, n_samples=40, seed=42)
    else:
        expr_df = download_geo_dataset(args.geo_id, out_dir)
        if expr_df is None:
            print_progress("Switching to synthetic data due to download failure.")
            expr_df = generate_synthetic_expression(n_genes=2000, n_samples=40, seed=42)

    print_progress(f"Expression matrix shape: {expr_df.shape}")

    # Step 2: Differential expression
    deg_df = differential_expression(expr_df, alpha=args.alpha)
    deg_path = os.path.join(out_dir, "biomarker_deg_table.csv")
    deg_df.to_csv(deg_path)
    print_progress(f"Saved DEG table to {deg_path}")

    # Step 3: Pathway enrichment
    enrich_df = pathway_enrichment(deg_df, alpha=args.alpha)
    enrich_path = os.path.join(out_dir, "biomarker_pathway_enrichment.csv")
    enrich_df.to_csv(enrich_path, index=False)
    print_progress(f"Saved pathway enrichment to {enrich_path}")

    # Step 4: Rank biomarkers
    top_df = rank_biomarkers(deg_df, top_n=args.top_n)
    top_path = os.path.join(out_dir, "biomarker_top_candidates.csv")
    top_df.to_csv(top_path)
    print_progress(f"Saved top candidates to {top_path}")

    # Step 5: Visualizations
    volcano_path = os.path.join(out_dir, "biomarker_volcano_plot.png")
    plot_volcano(deg_df, alpha=args.alpha, outpath=volcano_path)

    # Step 6: Report
    report_path = os.path.join(out_dir, "biomarker_report.txt")
    save_report(deg_df, top_df, enrich_df, report_path)

    # Final summary
    print("\n" + "=" * 60)
    print("Biomarker Discovery Pipeline Complete")
    print("=" * 60)
    print(f"Output directory       : {out_dir}")
    print(f"Disease                : {args.disease}")
    print(f"Genes analyzed         : {deg_df.shape[0]}")
    print(f"Significant DEGs       : {deg_df['significant'].sum()}")
    print(f"Top candidates saved   : {top_path}")
    print(f"Volcano plot           : {volcano_path}")
    print(f"Pathway enrichment     : {enrich_path}")
    print(f"Summary report         : {report_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
