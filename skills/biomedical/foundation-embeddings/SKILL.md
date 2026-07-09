---
name: bioresearch-foundation-embeddings
description: Generate and evaluate single-cell foundation model embeddings (scGPT / UCE / scFoundation). Runs mock-mode pipeline validation by default — simulated embeddings that recover planted cell-type structure. Live mode stubs (pip install scgpt, UCE eval_single_anndata.py, scFoundation get_embedding.py) are documented for real deployment. Use when the user wants to embed scRNA-seq data with foundation models, compare embedding quality across models, or benchmark cell-type recovery.
---

# BioResearch Agent — Foundation Model Embeddings Skill

## Capability

Generates cell-level embeddings from three single-cell foundation models and
evaluates them on a standardized cell-type recovery benchmark:

1. **scGPT** (Cui et al. 2024, Nature Methods) — 512-dim, pretrained on 33M
   human cells, CPU-compatible. Input: normalized + log1p AnnData.
   Live API: `scgpt.tasks.embed_data(adata, model_dir, gene_col)`.
2. **UCE** (Rosen et al. 2023, bioRxiv) — 1280-dim, pretrained on 36M
   multi-species cells, GPU required. Input: raw counts h5ad.
   Live API: `AnndataProcessor` from `evaluate.py`.
3. **scFoundation** (Hao et al. 2024, Nature Methods) — 512-dim, pretrained on
   50M+ human cells, GPU required. Input: CSV aligned to 19,264-gene list.
   Live API: `get_embedding.py --input_type singlecell`.

Evaluation metrics (all custom implementations, no sklearn dependency for
core metrics):
- **Silhouette score** — cluster cohesion vs separation
- **ARI** (Adjusted Rand Index) — agreement with ground-truth labels
- **NMI** (Normalized Mutual Information) — information-theoretic agreement
- **Cross-model kNN overlap** — neighborhood consistency between model pairs
- **Robustness sweep** — metrics across noise levels [0.1–0.6]

Returns per-model metrics CSV, cross-model consistency table, robustness sweep
results, UMAP/PCA visualization, clustering heatmap, summary report with
evidence grade, and a JSON evidence package.

## Run

```bash
bioresearch run foundation-embeddings --n-cells 1000 --n-genes 2000 --seed 42 \
  --output-dir outputs/foundation-embeddings
```

## Outputs (in `--output-dir`)

- `fe_per_model_metrics.csv` — per-model silhouette, ARI, NMI
- `fe_cross_model_consistency.csv` — pairwise kNN overlap between models
- `fe_robustness_sweep.csv` — metrics across 6 noise levels for each model
- `fe_embedding_umap.png` — side-by-side 2D projection for all 3 models
- `fe_clustering_heatmap.png` — ARI/NMI/silhouette heatmap across noise levels
- `fe_summary_report.txt` — human-readable summary with evidence grade
- `fe_evidence_package.json` — reproducible Evidence Package (provenance + metrics + grade)

## Note

This skill dispatches to the framework's `foundation-embeddings` workflow /
`demo_foundation_embeddings.py`. By default it runs in **MOCK mode**: embeddings
are simulated with cluster centroids + Gaussian noise + L2 normalization,
matching the output dimensions of each real model. This validates that the
evaluation pipeline (silhouette, ARI, NMI, kNN overlap, robustness sweep)
recovers planted cell-type structure — it does NOT measure real model
performance.

**Evidence grade: B** (mock mode validates pipeline correctness; real model
benchmarks require GPU and model checkpoints).

### Live Mode Deployment

To switch from mock to real model inference:

```python
# scGPT (easiest — PyPI + CPU)
pip install scgpt
from scgpt.tasks import embed_data
embeddings = embed_data(adata, model_dir, gene_col="Gene Symbol", device="cpu")

# UCE (git clone + GPU)
git clone https://github.com/snap-stanford/UCE.git
python eval_single_anndata.py --model_path ./model_uce_65m.pt \
  --adata_path input.h5ad --output_path output.h5ad

# scFoundation (git clone + GPU + gene alignment)
git clone https://github.com/biomap-labs/scFoundation.git
python get_embedding.py --input_type singlecell --output_type cell \
  --input_file input.csv --model_path ./models/
```
