# Bio-Research-OS Demos

This directory contains three end-to-end, runnable demo scripts that showcase core workflows of the **Bio-Research-OS** framework. All demos use **publicly available or synthetic data** and require only standard Python scientific libraries.

## Requirements

- Python >= 3.8
- `pandas`
- `numpy`
- `matplotlib`
- `scipy`
- `networkx` (optional; needed for Demo 1 knowledge graph visualization)

Install dependencies:

```bash
pip install pandas numpy matplotlib scipy networkx
```

## Directory Layout

```
demos/
├── demo_literature_review.py      # Demo 1: Literature Review Automation
├── demo_biomarker_discovery.py    # Demo 2: Biomarker Discovery Pipeline
├── demo_causal_inference.py       # Demo 3: Causal Inference (MR) Workflow
├── README.md                      # This file
└── demo_outputs/                  # Generated automatically on first run
```

---

## Demo 1: Literature Review Automation

**File:** `demo_literature_review.py`

### What it demonstrates
- Automated PubMed search via NCBI E-utilities API (with offline mock-corpus fallback)
- Extractive summarization of abstracts
- Entity co-occurrence knowledge graph construction
- Heuristic knowledge-gap identification
- Structured review outline generation

### How to run

```bash
# Default topic: "microglia in Alzheimer's disease"
python demo_literature_review.py

# Custom topic
python demo_literature_review.py --topic "gut microbiome obesity"

# Force offline mock corpus (no network calls)
python demo_literature_review.py --use_mock
```

### Outputs (in `demo_outputs/`)
- `lit_review_summary_table.csv` — Article metadata + 2-sentence abstract summaries
- `lit_review_knowledge_graph.png` — Entity co-occurrence network visualization
- `lit_review_knowledge_gaps.txt` — List of identified research gaps
- `lit_review_outline.md` — Structured markdown review outline

---

## Demo 2: Biomarker Discovery Pipeline

**File:** `demo_biomarker_discovery.py`

### What it demonstrates
- Acquisition (or synthesis) of gene-expression data
- Two-group differential expression analysis (Welch's t-test + Bonferroni correction)
- Hypergeometric pathway enrichment on built-in KEGG/GO gene sets
- Biomarker candidate ranking by effect size and significance
- Volcano plot generation

### How to run

```bash
# Default: attempts GEO GSE7621 download, falls back to synthetic data
python demo_biomarker_discovery.py

# Force synthetic data (no network calls)
python demo_biomarker_discovery.py --use_synthetic

# Adjust significance threshold
python demo_biomarker_discovery.py --alpha 0.01
```

### Outputs (in `demo_outputs/`)
- `biomarker_deg_table.csv` — All genes with log2FC, p-values, and significance flags
- `biomarker_top_candidates.csv` — Top-ranked biomarker candidates
- `biomarker_pathway_enrichment.csv` — Pathway enrichment results (KEGG + GO BP)
- `biomarker_volcano_plot.png` — Publication-quality volcano plot
- `biomarker_report.txt` — Human-readable summary of findings

---

## Demo 3: Causal Inference Workflow (Mendelian Randomization)

**File:** `demo_causal_inference.py`

### What it demonstrates
- Simulation of realistic GWAS summary statistics (SNP → exposure, SNP → outcome)
- Instrument selection (genome-wide significance threshold)
- Inverse-Variance Weighted (IVW) Mendelian Randomization
- Leave-one-out sensitivity analysis
- MR scatter plot and funnel plot generation
- Automated causal interpretation report

### How to run

```bash
# Default: BMI → Type 2 Diabetes with 120 SNPs
python demo_causal_inference.py

# Custom parameters
python demo_causal_inference.py --exposure "LDL cholesterol" --outcome "CAD" --n_snps 200 --seed 123
```

### Outputs (in `demo_outputs/`)
- `causal_ivw_results.csv` — Primary IVW causal estimate, SE, CI, p-value, heterogeneity statistics
- `causal_loo_results.csv` — Leave-one-out sensitivity table
- `causal_mr_scatter.png` — SNP-effect scatter plot with IVW regression line
- `causal_mr_funnel.png` — Funnel plot for visualizing precision and bias
- `causal_interpretation.txt` — Detailed interpretation, limitations, and caveats

---

## Notes

- **Network resilience:** Each demo gracefully handles API/network failures by falling back to built-in synthetic or mock data.
- **Reproducibility:** Demos accept `--seed` (where applicable) and use deterministic defaults.
- **Extensibility:** The scripts are heavily commented and modular; individual functions can be extracted for reuse in production pipelines.

## License

These demos are provided as educational examples within the Bio-Research-OS project.
