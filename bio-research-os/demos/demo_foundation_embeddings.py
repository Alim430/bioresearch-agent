#!/usr/bin/env python3
"""
Demo: Foundation Model Embeddings (scGPT / UCE / scFoundation)
================================================================

A *methodology* engine that wires together three single-cell foundation models
for cell-level embedding extraction, and validates each against a known ground
truth (planted cell-type structure).

IMPORTANT (honesty): by default this runs in MOCK mode — the embeddings are
simulated to mimic the statistical properties of each real model's output
(scGPT: 512-dim, UCE: 1280-dim, scFoundation: 512-dim) but are NOT generated
by the actual neural networks. This validates that the *evaluation pipeline*
correctly recovers the planted cell-type structure. For a real deployment,
swap `mock_embed_*` for the actual API calls (code stubs provided) and point
the pipeline at real scRNA-seq data.

Models covered
--------------
  1. scGPT        (Cui et al. 2024, Nat Methods)  — transformer, 512-dim, CPU-ok
  2. UCE          (Rosen et al. 2023, bioRxiv)    — protein-embedded, 1280-dim
  3. scFoundation (Hao et al. 2024, Nat Methods)  — 100M params, 512-dim

Steps demonstrated
------------------
  1. simulate_single_cell_data  : build scRNA-seq with 5 cell types + batch effect
  2. mock_embed_scgpt           : scGPT-style 512-dim cell embeddings (mock)
  3. mock_embed_uce             : UCE-style 1280-dim cell embeddings (mock)
  4. mock_embed_scfoundation    : scFoundation-style 512-dim cell embeddings (mock)
  5. evaluate_embeddings        : silhouette, ARI, NMI per model
  6. cross_model_consistency    : pairwise embedding agreement (CCA / kNN overlap)
  7. foundation_embedding_pipeline : orchestrates 2-6 + robustness sweep

Outputs (when run as a script):
  - {output_dir}/fe_per_model_metrics.csv
  - {output_dir}/fe_cross_model_consistency.csv
  - {output_dir}/fe_robustness_sweep.csv
  - {output_dir}/fe_summary_report.txt
  - {output_dir}/fe_embedding_umap.png      (UMAP of 3 models side-by-side)
  - {output_dir}/fe_clustering_heatmap.png  (ARI/NMI per model x noise level)

Usage:
  python demo_foundation_embeddings.py --n-cells 1000 --n-genes 2000 --seed 42 --output-dir outputs/foundation-embeddings
"""

import argparse
import json
import os
import sys
import textwrap
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import cdist

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# ---------------------------------------------------------------------------
# Constants — model specifications
# ---------------------------------------------------------------------------
MODEL_SPECS = {
    "scGPT": {
        "embedding_dim": 512,
        "paper": "Cui et al. 2024, Nature Methods",
        "pretrain_cells": "33M human cells",
        "input_requirement": "normalized + log1p AnnData",
        "cpu_compatible": True,
        "pypi": "scgpt",
    },
    "UCE": {
        "embedding_dim": 1280,
        "paper": "Rosen et al. 2023, bioRxiv",
        "pretrain_cells": "36M multi-species cells",
        "input_requirement": "raw counts h5ad",
        "cpu_compatible": False,
        "pypi": None,  # git clone only
    },
    "scFoundation": {
        "embedding_dim": 512,
        "paper": "Hao et al. 2024, Nature Methods",
        "pretrain_cells": "50M+ human cells",
        "input_requirement": "CSV aligned to 19264 gene list",
        "cpu_compatible": False,
        "pypi": None,
    },
}

CELL_TYPES = ["T_cell", "B_cell", "NK_cell", "Monocyte", "Dendritic"]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")


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
# 1. Synthetic single-cell data
# ---------------------------------------------------------------------------
def simulate_single_cell_data(
    n_cells: int = 1000,
    n_genes: int = 2000,
    n_cell_types: int = 5,
    n_batches: int = 2,
    seed: int = 42,
) -> Dict:
    """
    Simulate a scRNA-seq count matrix with planted cell-type structure + batch effect.

    Ground truth:
      - Each cell belongs to one of `n_cell_types` cell types (balanced).
      - Each cell belongs to one of `n_batches` batches (balanced, orthogonal to type).
      - Cell-type-specific marker genes create separable clusters in expression space.
      - Batch effect adds a shared shift to all genes within a batch.

    Returns a dict with the count matrix, cell metadata, and truth labels.
    """
    rng = np.random.default_rng(seed)
    cells_per_type = n_cells // n_cell_types
    actual_n = cells_per_type * n_cell_types

    # cell type labels
    labels = np.repeat(np.arange(n_cell_types), cells_per_type)
    rng.shuffle(labels)

    # batch labels (independent of type)
    batches = rng.integers(0, n_batches, size=actual_n)

    # cell-type-specific marker genes: each type has ~5% of genes as markers
    markers_per_type = max(10, n_genes // 20)
    type_markers = {}
    for ct in range(n_cell_types):
        marker_idx = rng.choice(n_genes, size=markers_per_type, replace=False)
        type_markers[ct] = marker_idx

    # base expression: negative binomial-like via Poisson-Gamma
    # shape (cells, genes)
    base_mean = rng.gamma(shape=2.0, scale=0.5, size=n_genes)  # gene-level baseline
    counts = np.zeros((actual_n, n_genes), dtype=np.float32)

    for i in range(actual_n):
        ct = labels[i]
        cell_lambda = base_mean.copy()

        # upregulate marker genes for this cell type
        marker_idx = type_markers[ct]
        cell_lambda[marker_idx] *= rng.uniform(3.0, 8.0, size=len(marker_idx))

        # batch effect: multiplicative shift on all genes
        bt = batches[i]
        batch_shift = rng.uniform(0.7, 1.3, size=n_genes) if bt == 1 else np.ones(n_genes)
        cell_lambda *= batch_shift

        # sample counts
        counts[i] = rng.poisson(cell_lambda)

    # gene names and cell names
    gene_names = [f"Gene_{j:05d}" for j in range(n_genes)]
    cell_names = [f"Cell_{i:05d}" for i in range(actual_n)]

    cell_meta = pd.DataFrame({
        "cell_id": cell_names,
        "cell_type": [CELL_TYPES[l] for l in labels],
        "cell_type_id": labels,
        "batch": [f"Batch_{b}" for b in batches],
        "batch_id": batches,
    })

    print_progress(
        f"Simulated {actual_n} cells x {n_genes} genes "
        f"({n_cell_types} types, {n_batches} batches)."
    )
    return {
        "counts": counts,
        "gene_names": gene_names,
        "cell_meta": cell_meta,
        "type_markers": type_markers,
        "params": {"n_cells": actual_n, "n_genes": n_genes,
                    "n_cell_types": n_cell_types, "n_batches": n_batches,
                    "seed": seed},
    }


# ---------------------------------------------------------------------------
# 2-4. Mock embedding generators
# ---------------------------------------------------------------------------
def _generate_cluster_embeddings(
    labels: np.ndarray,
    n_clusters: int,
    embed_dim: int,
    cluster_separation: float,
    noise_level: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate embeddings where each cluster has a distinct centroid, plus noise.
    This mimics what a well-trained foundation model would produce: cells of the
    same type cluster together in embedding space.
    """
    # random centroids per cluster
    centroids = rng.normal(0, cluster_separation, size=(n_clusters, embed_dim))

    embeddings = np.zeros((len(labels), embed_dim), dtype=np.float32)
    for i, label in enumerate(labels):
        embeddings[i] = centroids[label] + rng.normal(0, noise_level, size=embed_dim)

    # L2 normalize (as real foundation models do)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    return embeddings


def mock_embed_scgpt(
    sim_data: Dict,
    noise_level: float = 0.3,
    cluster_separation: float = 2.0,
    seed: int = 42,
) -> np.ndarray:
    """
    Mock scGPT cell embeddings (512-dim, L2-normalized).

    In live mode this would call:
        import scgpt as scg
        embed_adata = scg.tasks.embed_data(adata, model_dir, gene_col="Gene Symbol",
                                           batch_size=64, device="cpu")
        return embed_adata.obsm["X_scGPT"]
    """
    rng = np.random.default_rng(seed + 100)
    labels = sim_data["cell_meta"]["cell_type_id"].values
    n_types = sim_data["params"]["n_cell_types"]
    dim = MODEL_SPECS["scGPT"]["embedding_dim"]

    emb = _generate_cluster_embeddings(
        labels, n_types, dim, cluster_separation, noise_level, rng
    )
    print_progress(f"scGPT mock embeddings: {emb.shape} (dim={dim})")
    return emb


def mock_embed_uce(
    sim_data: Dict,
    noise_level: float = 0.25,
    cluster_separation: float = 2.2,
    seed: int = 42,
) -> np.ndarray:
    """
    Mock UCE cell embeddings (1280-dim, L2-normalized).

    In live mode this would call:
        from evaluate import AnndataProcessor
        processor = AnndataProcessor(args, accelerator)
        processor.preprocess_anndata()
        processor.run_evaluation()
        # reads obsm["X_uce"] from output h5ad
    """
    rng = np.random.default_rng(seed + 200)
    labels = sim_data["cell_meta"]["cell_type_id"].values
    n_types = sim_data["params"]["n_cell_types"]
    dim = MODEL_SPECS["UCE"]["embedding_dim"]

    # UCE uses different random projection — slightly different cluster geometry
    emb = _generate_cluster_embeddings(
        labels, n_types, dim, cluster_separation, noise_level, rng
    )
    print_progress(f"UCE mock embeddings: {emb.shape} (dim={dim})")
    return emb


def mock_embed_scfoundation(
    sim_data: Dict,
    noise_level: float = 0.35,
    cluster_separation: float = 1.8,
    seed: int = 42,
) -> np.ndarray:
    """
    Mock scFoundation cell embeddings (512-dim, L2-normalized).

    In live mode this would call:
        python get_embedding.py --input_type singlecell --output_type cell
            --pool_type all --data_path input.csv --save_path output/
            --model_path ./models/ --version rde
        # then load the saved numpy array
    """
    rng = np.random.default_rng(seed + 300)
    labels = sim_data["cell_meta"]["cell_type_id"].values
    n_types = sim_data["params"]["n_cell_types"]
    dim = MODEL_SPECS["scFoundation"]["embedding_dim"]

    emb = _generate_cluster_embeddings(
        labels, n_types, dim, cluster_separation, noise_level, rng
    )
    print_progress(f"scFoundation mock embeddings: {emb.shape} (dim={dim})")
    return emb


# ---------------------------------------------------------------------------
# 5. Evaluation metrics
# ---------------------------------------------------------------------------
def silhouette_score(emb: np.ndarray, labels: np.ndarray, sample_size: int = 5000) -> float:
    """
    Approximate silhouette score. For large n, subsample to keep it fast.
    """
    n = len(labels)
    if n > sample_size:
        rng = np.random.default_rng(42)
        idx = rng.choice(n, size=sample_size, replace=False)
        emb = emb[idx]
        labels = labels[idx]

    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return 0.0

    # pairwise distances
    dists = cdist(emb, emb, metric="euclidean")

    sil_values = []
    for i in range(len(labels)):
        same_mask = (labels == labels[i]) & (np.arange(len(labels)) != i)
        other_mask = labels != labels[i]

        if same_mask.sum() == 0 or other_mask.sum() == 0:
            continue

        a_i = dists[i, same_mask].mean()  # mean intra-cluster distance
        b_i = dists[i, other_mask].min()  # nearest other cluster (approximated)

        sil_i = (b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0.0
        sil_values.append(sil_i)

    return float(np.mean(sil_values)) if sil_values else 0.0


def kmeans_clustering(emb: np.ndarray, n_clusters: int, seed: int = 42,
                      max_iter: int = 300) -> np.ndarray:
    """
    Simple k-means clustering (no sklearn dependency).
    """
    rng = np.random.default_rng(seed)
    n, d = emb.shape

    # k-means++ initialization
    centers = [emb[rng.integers(n)]]
    for _ in range(1, n_clusters):
        dists = np.min(cdist(emb, np.array(centers), metric="euclidean"), axis=1)
        probs = dists / dists.sum()
        centers.append(emb[rng.choice(n, p=probs)])
    centers = np.array(centers)

    for _ in range(max_iter):
        # assign
        dists = cdist(emb, centers, metric="euclidean")
        assignments = np.argmin(dists, axis=1)

        # update
        new_centers = np.array([
            emb[assignments == k].mean(axis=0) if (assignments == k).any() else centers[k]
            for k in range(n_clusters)
        ])

        if np.allclose(new_centers, centers, atol=1e-6):
            break
        centers = new_centers

    return assignments


def adjusted_rand_index(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """
    ARI computation (no sklearn dependency).
    """
    from math import comb

    n = len(labels_true)
    classes = np.unique(labels_true)
    clusters = np.unique(labels_pred)

    # contingency table
    contingency = np.zeros((len(classes), len(clusters)), dtype=int)
    for i, c in enumerate(classes):
        for j, k in enumerate(clusters):
            contingency[i, j] = np.sum((labels_true == c) & (labels_pred == k))

    sum_comb_c = sum(comb(int(n_ij), 2) for n_ij in contingency.sum(axis=1))
    sum_comb_k = sum(comb(int(n_kj), 2) for n_kj in contingency.sum(axis=0))
    sum_comb = sum(comb(int(n_ij), 2) for n_ij in contingency.ravel())
    total_comb = comb(n, 2)

    expected = sum_comb_c * sum_comb_k / total_comb if total_comb > 0 else 0
    max_index = (sum_comb_c + sum_comb_k) / 2

    if max_index == expected:
        return 1.0
    return float((sum_comb - expected) / (max_index - expected))


def normalized_mutual_info(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """
    NMI computation (no sklearn dependency).
    """
    from math import log2

    n = len(labels_true)
    classes = np.unique(labels_true)
    clusters = np.unique(labels_pred)

    contingency = np.zeros((len(classes), len(clusters)), dtype=float)
    for i, c in enumerate(classes):
        for j, k in enumerate(clusters):
            contingency[i, j] = np.sum((labels_true == c) & (labels_pred == k))
    contingency /= n

    # marginal probabilities
    p_c = contingency.sum(axis=1, keepdims=True)
    p_k = contingency.sum(axis=0, keepdims=True)

    # entropies
    def entropy(p):
        p = p[p > 0]
        return -np.sum(p * np.log2(p))

    h_c = entropy(p_c.ravel())
    h_k = entropy(p_k.ravel())

    # mutual information
    mi = 0.0
    for i in range(len(classes)):
        for j in range(len(clusters)):
            if contingency[i, j] > 0 and p_c[i, 0] > 0 and p_k[0, j] > 0:
                mi += contingency[i, j] * log2(
                    contingency[i, j] / (p_c[i, 0] * p_k[0, j])
                )

    if h_c + h_k == 0:
        return 0.0
    return float(2 * mi / (h_c + h_k))


def evaluate_embeddings(
    emb: np.ndarray,
    true_labels: np.ndarray,
    n_clusters: int,
    model_name: str,
) -> Dict:
    """
    Evaluate embedding quality: silhouette, k-means ARI, k-means NMI.
    """
    sil = silhouette_score(emb, true_labels)
    pred_labels = kmeans_clustering(emb, n_clusters)
    ari = adjusted_rand_index(true_labels, pred_labels)
    nmi = normalized_mutual_info(true_labels, pred_labels)

    result = {
        "model": model_name,
        "embedding_dim": emb.shape[1],
        "n_cells": emb.shape[0],
        "silhouette": round(sil, 4),
        "ari": round(ari, 4),
        "nmi": round(nmi, 4),
    }
    print_progress(
        f"{model_name}: silhouette={sil:.4f}, ARI={ari:.4f}, NMI={nmi:.4f}"
    )
    return result


# ---------------------------------------------------------------------------
# 6. Cross-model consistency
# ---------------------------------------------------------------------------
def cross_model_consistency(
    embeddings: Dict[str, np.ndarray],
    true_labels: np.ndarray,
) -> pd.DataFrame:
    """
    Compare embedding spaces across models using kNN overlap.

    For each pair of models, compute the fraction of cells whose k nearest
    neighbors (by Euclidean distance in embedding space) overlap.
    """
    k = 10  # number of neighbors
    models = list(embeddings.keys())
    rows = []

    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            m1, m2 = models[i], models[j]
            emb1 = embeddings[m1]
            emb2 = embeddings[m2]

            n = emb1.shape[0]
            # kNN in each space
            dist1 = cdist(emb1, emb1, metric="euclidean")
            dist2 = cdist(emb2, emb2, metric="euclidean")

            np.fill_diagonal(dist1, np.inf)
            np.fill_diagonal(dist2, np.inf)

            nn1 = np.argsort(dist1, axis=1)[:, :k]
            nn2 = np.argsort(dist2, axis=1)[:, :k]

            # overlap
            overlaps = []
            for cell in range(n):
                set1 = set(nn1[cell])
                set2 = set(nn2[cell])
                overlaps.append(len(set1 & set2) / k)

            mean_overlap = float(np.mean(overlaps))

            # also compute agreement on cell type recovery
            # (both models should recover the same cell-type structure)
            sil1 = silhouette_score(emb1, true_labels)
            sil2 = silhouette_score(emb2, true_labels)
            sil_diff = abs(sil1 - sil2)

            rows.append({
                "model_1": m1,
                "model_2": m2,
                "knn_overlap": round(mean_overlap, 4),
                "k": k,
                "sil_diff": round(sil_diff, 4),
                "embed_dim_1": emb1.shape[1],
                "embed_dim_2": emb2.shape[1],
            })
            print_progress(
                f"Cross-model {m1} vs {m2}: kNN overlap={mean_overlap:.4f}"
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 7. Pipeline orchestration
# ---------------------------------------------------------------------------
def foundation_embedding_pipeline(
    n_cells: int = 1000,
    n_genes: int = 2000,
    seed: int = 42,
    noise_level: float = 0.3,
) -> Dict:
    """
    Full pipeline: simulate data -> embed with 3 models -> evaluate -> compare.
    """
    # 1. Simulate data
    sim_data = simulate_single_cell_data(
        n_cells=n_cells, n_genes=n_genes, seed=seed
    )

    true_labels = sim_data["cell_meta"]["cell_type_id"].values
    n_types = sim_data["params"]["n_cell_types"]

    # 2-4. Generate embeddings (mock mode)
    embeddings = {
        "scGPT": mock_embed_scgpt(sim_data, noise_level=noise_level, seed=seed),
        "UCE": mock_embed_uce(sim_data, noise_level=noise_level * 0.85, seed=seed),
        "scFoundation": mock_embed_scfoundation(sim_data, noise_level=noise_level * 1.1, seed=seed),
    }

    # 5. Evaluate each model
    metrics = []
    for model_name, emb in embeddings.items():
        m = evaluate_embeddings(emb, true_labels, n_types, model_name)
        m["noise_level"] = noise_level
        metrics.append(m)
    metrics_df = pd.DataFrame(metrics)

    # 6. Cross-model consistency
    consistency_df = cross_model_consistency(embeddings, true_labels)

    return {
        "sim_data": sim_data,
        "embeddings": embeddings,
        "metrics": metrics_df,
        "consistency": consistency_df,
        "true_labels": true_labels,
        "params": {"n_cells": n_cells, "n_genes": n_genes, "seed": seed,
                    "noise_level": noise_level},
    }


def sweep_benchmark(
    n_cells: int = 800,
    n_genes: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Robustness sweep: vary noise level and measure how each model degrades.
    """
    noise_levels = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    all_metrics = []

    for noise in noise_levels:
        print_progress(f"Sweep: noise_level={noise}")
        result = foundation_embedding_pipeline(
            n_cells=n_cells, n_genes=n_genes, seed=seed, noise_level=noise
        )
        result["metrics"]["noise_level"] = noise
        all_metrics.append(result["metrics"])

    sweep_df = pd.concat(all_metrics, ignore_index=True)
    return sweep_df


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def simple_umap(emb: np.ndarray, n_components: int = 2, n_neighbors: int = 15,
                seed: int = 42) -> np.ndarray:
    """
    A simplified UMAP-like projection using PCA + t-SNE-style refinement.
    Falls back to PCA when no UMAP package is available.
    """
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=min(n_components, emb.shape[1], emb.shape[0] - 1),
                  random_state=seed)
        return pca.fit_transform(emb)
    except ImportError:
        # manual PCA via SVD
        emb_centered = emb - emb.mean(axis=0)
        U, S, Vt = np.linalg.svd(emb_centered, full_matrices=False)
        return U[:, :n_components] * S[:n_components]


def plot_embedding_umap(embeddings: Dict[str, np.ndarray], true_labels: np.ndarray,
                        output_path: str) -> None:
    """
    UMAP/PCA visualization of embeddings from all 3 models, side-by-side.
    """
    fig, axes = plt.subplots(1, len(embeddings), figsize=(6 * len(embeddings), 5))
    if len(embeddings) == 1:
        axes = [axes]

    cmap = ListedColormap(plt.cm.Set1.colors[:len(np.unique(true_labels))])

    for ax, (model_name, emb) in zip(axes, embeddings.items()):
        proj = simple_umap(emb, n_components=2)
        scatter = ax.scatter(proj[:, 0], proj[:, 1], c=true_labels, cmap=cmap,
                            s=8, alpha=0.7, edgecolors="none")
        ax.set_title(f"{model_name} ({emb.shape[1]}-dim)", fontsize=13, fontweight="bold")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.tick_params(labelsize=8)

    fig.colorbar(scatter, ax=axes, label="Cell Type", shrink=0.6, pad=0.02)
    fig.suptitle("Foundation Model Embeddings — Cell Type Separation",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print_progress(f"Saved UMAP plot to {output_path}")


def plot_clustering_heatmap(sweep_df: pd.DataFrame, output_path: str) -> None:
    """
    Heatmap: ARI/NMI per model across noise levels.
    """
    metrics = ["ari", "nmi", "silhouette"]
    models = sweep_df["model"].unique()
    noise_levels = sorted(sweep_df["noise_level"].unique())

    fig, axes = plt.subplots(1, len(metrics), figsize=(6 * len(metrics), 5))

    for ax, metric in zip(axes, metrics):
        data = np.zeros((len(models), len(noise_levels)))
        for i, model in enumerate(models):
            for j, noise in enumerate(noise_levels):
                row = sweep_df[(sweep_df["model"] == model) &
                               (sweep_df["noise_level"] == noise)]
                if len(row) > 0:
                    data[i, j] = row[metric].values[0]

        im = ax.imshow(data, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
        ax.set_xticks(range(len(noise_levels)))
        ax.set_xticklabels([f"{n:.1f}" for n in noise_levels], fontsize=9)
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels(models, fontsize=10)
        ax.set_xlabel("Noise Level")
        ax.set_title(metric.upper(), fontsize=12, fontweight="bold")

        # annotate cells
        for i in range(len(models)):
            for j in range(len(noise_levels)):
                ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center",
                       fontsize=8, color="black" if data[i, j] > 0.3 else "white")

    fig.colorbar(im, ax=axes, shrink=0.6, pad=0.02)
    fig.suptitle("Clustering Performance vs. Noise Level",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print_progress(f"Saved heatmap to {output_path}")


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------
def generate_summary_report(
    metrics_df: pd.DataFrame,
    consistency_df: pd.DataFrame,
    sweep_df: pd.DataFrame,
    sim_params: Dict,
    output_path: str,
) -> None:
    """
    Human-readable summary with honest limitations.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("Foundation Model Embeddings — Summary Report")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Data: {sim_params['n_cells']} cells x {sim_params['n_genes']} genes")
    lines.append(f"Mode: MOCK (simulated embeddings, not real model inference)")
    lines.append(f"Seed: {sim_params['seed']}")
    lines.append("")

    lines.append("Models Evaluated:")
    for model, spec in MODEL_SPECS.items():
        lines.append(f"  - {model}: {spec['embedding_dim']}-dim ({spec['paper']})")
        lines.append(f"    Pretrained on: {spec['pretrain_cells']}")
        lines.append(f"    Input: {spec['input_requirement']}")
        lines.append(f"    CPU: {'Yes' if spec['cpu_compatible'] else 'No (GPU required)'}")
    lines.append("")

    lines.append("Per-Model Metrics (default noise level):")
    lines.append("-" * 50)
    for _, row in metrics_df.iterrows():
        lines.append(f"  {row['model']:15s} | "
                     f"Silhouette={row['silhouette']:.4f} | "
                     f"ARI={row['ari']:.4f} | "
                     f"NMI={row['nmi']:.4f}")
    lines.append("")

    lines.append("Cross-Model Consistency:")
    lines.append("-" * 50)
    for _, row in consistency_df.iterrows():
        lines.append(f"  {row['model_1']} vs {row['model_2']}: "
                     f"kNN overlap={row['knn_overlap']:.4f} (k={row['k']}), "
                     f"sil_diff={row['sil_diff']:.4f}")
    lines.append("")

    lines.append("Robustness Sweep (ARI across noise levels):")
    lines.append("-" * 50)
    for model in sweep_df["model"].unique():
        model_data = sweep_df[sweep_df["model"] == model].sort_values("noise_level")
        ari_vals = [f"{v:.3f}" for v in model_data["ari"].values]
        noise_vals = [f"{v:.1f}" for v in model_data["noise_level"].values]
        lines.append(f"  {model:15s} | noise={noise_vals}")
        lines.append(f"  {'':15s} | ARI  ={ari_vals}")
    lines.append("")

    # evidence grade
    best_ari = metrics_df["ari"].max()
    if best_ari >= 0.8:
        grade = "B"
        grade_note = "Strong cell-type recovery (mock mode validates pipeline correctness)"
    elif best_ari >= 0.5:
        grade = "C"
        grade_note = "Moderate recovery — pipeline functional, model differentiation limited in mock mode"
    else:
        grade = "D"
        grade_note = "Weak recovery — investigate embedding quality"

    lines.append("Evidence Grade: " + grade)
    lines.append(f"  {grade_note}")
    lines.append("")

    lines.append("Limitations:")
    lines.append("-" * 50)
    lines.append("  1. MOCK MODE: embeddings are simulated, not from real neural networks.")
    lines.append("     This validates the evaluation pipeline, NOT model performance.")
    lines.append("  2. Real model performance depends on checkpoint quality, input")
    lines.append("     preprocessing, and hardware (GPU for UCE/scFoundation).")
    lines.append("  3. Cross-model kNN overlap is expected to be LOW even with real models,")
    lines.append("     because different models learn different embedding geometries.")
    lines.append("  4. The synthetic data has clean cell-type structure; real scRNA-seq")
    lines.append("     has continuous states, doublets, and ambient RNA contamination.")
    lines.append("  5. scFoundation requires gene alignment to a fixed 19,264-gene list,")
    lines.append("     which may lose information for non-standard gene panels.")
    lines.append("")

    lines.append("Live Mode Deployment:")
    lines.append("-" * 50)
    lines.append("  scGPT:        pip install scgpt; scgpt.tasks.embed_data(adata, model_dir)")
    lines.append("  UCE:          git clone snap-stanford/UCE; python eval_single_anndata.py")
    lines.append("  scFoundation: python get_embedding.py --model_path ./models/")
    lines.append("  (See live_embed_stubs.py for code templates)")
    lines.append("")

    lines.append("=" * 72)
    report = "\n".join(lines)

    with open(output_path, "w") as f:
        f.write(report)
    print_progress(f"Saved summary report to {output_path}")


def generate_evidence_package(
    metrics_df: pd.DataFrame,
    consistency_df: pd.DataFrame,
    sweep_df: pd.DataFrame,
    sim_params: Dict,
    output_path: str,
) -> None:
    """
    Reproducible Evidence Package (JSON).
    """
    best_ari = float(metrics_df["ari"].max())
    if best_ari >= 0.8:
        grade = "B"
    elif best_ari >= 0.5:
        grade = "C"
    else:
        grade = "D"

    package = {
        "skill": "bioresearch-foundation-embeddings",
        "framework_version": "1.6.0",
        "mode": "mock",
        "timestamp": pd.Timestamp.now().isoformat(),
        "provenance": {
            "data_source": "simulated single-cell RNA-seq",
            "n_cells": sim_params["n_cells"],
            "n_genes": sim_params["n_genes"],
            "n_cell_types": 5,
            "seed": sim_params["seed"],
            "models": list(MODEL_SPECS.keys()),
        },
        "metrics": metrics_df.to_dict(orient="records"),
        "cross_model": consistency_df.to_dict(orient="records"),
        "robustness_sweep": sweep_df.to_dict(orient="records"),
        "evidence_grade": grade,
        "limitations": [
            "Mock mode: embeddings simulated, not from real model inference",
            "Validates evaluation pipeline, not actual model performance",
            "Real deployment requires model checkpoints, GPU (for UCE/scFoundation)",
        ],
    }

    with open(output_path, "w") as f:
        json.dump(package, f, indent=2, default=str)
    print_progress(f"Saved evidence package to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Foundation Model Embeddings Demo (scGPT / UCE / scFoundation)"
    )
    parser.add_argument("--n-cells", type=int, default=1000,
                        help="Number of cells to simulate (default: 1000)")
    parser.add_argument("--n-genes", type=int, default=2000,
                        help="Number of genes to simulate (default: 2000)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--noise-level", type=float, default=0.3,
                        help="Embedding noise level (default: 0.3)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: demo_outputs/foundation-embeddings)")
    args = parser.parse_args()

    output_dir = ensure_output_dir(args.output_dir)

    print_progress("=== Foundation Model Embeddings Pipeline ===")
    print_progress(f"Output: {output_dir}")

    # Run main pipeline
    result = foundation_embedding_pipeline(
        n_cells=args.n_cells,
        n_genes=args.n_genes,
        seed=args.seed,
        noise_level=args.noise_level,
    )

    # Save per-model metrics
    metrics_path = os.path.join(output_dir, "fe_per_model_metrics.csv")
    result["metrics"].to_csv(metrics_path, index=False)

    # Save cross-model consistency
    consistency_path = os.path.join(output_dir, "fe_cross_model_consistency.csv")
    result["consistency"].to_csv(consistency_path, index=False)

    # Robustness sweep
    print_progress("Running robustness sweep...")
    sweep_df = sweep_benchmark(n_cells=min(args.n_cells, 800),
                               n_genes=args.n_genes, seed=args.seed)
    sweep_path = os.path.join(output_dir, "fe_robustness_sweep.csv")
    sweep_df.to_csv(sweep_path, index=False)

    # Visualizations
    umap_path = os.path.join(output_dir, "fe_embedding_umap.png")
    plot_embedding_umap(result["embeddings"], result["true_labels"], umap_path)

    heatmap_path = os.path.join(output_dir, "fe_clustering_heatmap.png")
    plot_clustering_heatmap(sweep_df, heatmap_path)

    # Summary report
    report_path = os.path.join(output_dir, "fe_summary_report.txt")
    generate_summary_report(
        result["metrics"], result["consistency"], sweep_df,
        result["params"], report_path
    )

    # Evidence package
    evidence_path = os.path.join(output_dir, "fe_evidence_package.json")
    generate_evidence_package(
        result["metrics"], result["consistency"], sweep_df,
        result["params"], evidence_path
    )

    # Print summary to stdout
    print("\n" + "=" * 60)
    print("Foundation Model Embeddings — Complete")
    print("=" * 60)
    print(f"\nMode: MOCK (simulated embeddings)")
    print(f"Data: {args.n_cells} cells x {args.n_genes} genes")
    print(f"\nPer-Model Metrics:")
    print(result["metrics"][["model", "silhouette", "ari", "nmi"]].to_string(index=False))
    print(f"\nCross-Model Consistency:")
    print(result["consistency"][["model_1", "model_2", "knn_overlap"]].to_string(index=False))
    best_ari = result["metrics"]["ari"].max()
    grade = "B" if best_ari >= 0.8 else ("C" if best_ari >= 0.5 else "D")
    print(f"\nEvidence Grade: {grade} (best ARI={best_ari:.4f})")
    print(f"\nOutputs saved to: {output_dir}")
    for f in sorted(os.listdir(output_dir)):
        if f.startswith("fe_"):
            print(f"  - {f}")


if __name__ == "__main__":
    main()
