# BioResearch Agent Framework

> Run biomedical literature review, biomarker discovery, and Mendelian randomization in one reproducible workflow.

[![CI](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![v1.0.0](https://img.shields.io/badge/release-v1.0.0-green.svg)](https://github.com/Alim430/bioresearch-agent/releases/tag/v1.0.0)

---

<div align="center">

<img src="assets/system_overview_v1.png" alt="System Overview" width="720"/>

*Reproducible biomedical workflow framework: 3 analysis pipelines &middot; 6 processing modules &middot; standardized execution outputs*

</div>

---

## 🖼️ What It Produces

One image shows the real outputs of all three workflows — understand what this is in 3 seconds, no reading required:

<div align="center">

<img src="assets/figure3_output_gallery.png" alt="BioResearch Agent Output Gallery" width="880"/>

*Left: literature co-occurrence knowledge graph &middot; Middle: differential-expression volcano plot &middot; Right: MR scatter plot — covering Literature / Biomarker / Causal scenarios.*

</div>

---

## ⚡ Quick Start

### 1. Clone and install
```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
```

### 2. Verify installation
```bash
bioresearch doctor
```

### 3. Run the three workflows
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
bioresearch run biomarker --disease "Parkinson's disease"
bioresearch run causal   --exposure BMI --outcome "Type 2 Diabetes"
```

### 4. Inspect outputs
```bash
ls outputs/literature/ outputs/biomarker/ outputs/causal/
```

**Demos require no LLM key** — they run on public APIs + synthetic fallback data.

### 5. Load into AI clients (optional)
BioResearch Agent ships an optional client-integration package for compatible AI environments. It exposes the existing workflows through a standardized schema — it adds **no new computational methods**; all analysis runs in the framework's workflow modules.

The recommended way is to run the installer (installs framework + skills + verifies):
```bash
./skills/install.sh
```

Or manually copy the tool specification and skill definitions:
```bash
cp bioresearch/toolspec.json ~/.config/bioresearch/toolspec.json
cp -r skills/literature skills/biomarker skills/causal ~/Library/Application\ Support/Claude/skills/
```
Restart the client after importing. See [External Client Integration](#external-client-integration-skills--tool-interface).

---

## 🔄 Workflow Overview

From structured research inputs to reproducible computational outputs:

<div align="center">

<img src="assets/bioresearch_pipeline.png" alt="BioResearch Agent Workflow" width="880"/>

</div>

**Core design:** Workflows provide standardized execution interfaces over existing biomedical analysis tools. Computational methods remain delegated to domain-specific libraries (limma, GSEA, TwoSampleMR). The framework defines explicit execution stages and standardized outputs for reproducible workflow organization.

## 🔁 12-Stage Execution Diagram

Stages 1&ndash;8 (Question &rarr; Hypothesis &rarr; Literature &rarr; Design &rarr; Data &rarr; Stats &rarr; Bioinfo &rarr; Output) are implemented in the current release. Stages 9&ndash;12 (Writing &rarr; Review &rarr; Critique &rarr; Publication) represent conceptual extensions toward end-to-end research organization and are not automated.

<div align="center">

<img src="assets/figure2_lifecycle.png" alt="12-Stage Execution Diagram" width="940"/>

*Execution diagram across 12 stages. Stages 1&ndash;8 are implemented; stages 9&ndash;12 are conceptual and not automated.*

</div>

---

## 🏗️ Architecture

<div align="center">

<img src="assets/figure1_framework.png" alt="Architecture" width="900"/>

</div>

| Layer | Responsibility |
|:---|:---|
| **User Interface** | CLI &middot; Python SDK &middot; API contract (tool spec) |
| **Workflow** | literature / biomarker / causal (extensible) |
| **Processing Modules &middot; 6 Components** | Question &rarr; Retrieval &rarr; Analysis &rarr; Evidence &rarr; Narrative &rarr; Execution |
| **Execution Stages &middot; 12-Stage Diagram** | Question &rarr; … &rarr; Output; 8 implemented / 4 conceptual |
| **External Tool Interfaces** | PubMed &middot; GEO &middot; KEGG &middot; GO &middot; GWAS &middot; DESeq2 &middot; IVW-MR |

---

## 🎯 What It Does

**BioResearch Agent Framework** is a runnable biomedical workflow framework that integrates existing analysis tools through standardized execution interfaces.

| Capability | Description |
|:---|:---|
| Literature analysis | PubMed retrieval, entity extraction, co-occurrence analysis |
| Omics analysis | Differential expression and pathway enrichment workflows |
| Causal analysis | Mendelian randomization workflows |
| Structured reporting | Standardized tables, figures, and workflow outputs |

**Key difference:** The framework executes reproducible computational workflows rather than generating text-only summaries. Outputs include data-derived tables, statistical results, and formatted figures.

---

## 🚀 Three Commands, Three Workflows

### 1. Literature Review
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```
PubMed retrieval &rarr; abstract extraction &rarr; entity co-occurrence knowledge graph &rarr; research-gap identification &rarr; structured review outline.
**Outputs:** `lit_review_summary_table.csv` &middot; `lit_review_knowledge_graph.png` &middot; `lit_review_knowledge_gaps.txt` &middot; `lit_review_outline.md`

### 2. Biomarker Discovery
```bash
bioresearch run biomarker --disease "Parkinson's disease"
```
GEO dataset (GSE7621) or synthetic &rarr; differential expression (t-test + Bonferroni) &rarr; hypergeometric pathway enrichment (KEGG/GO) &rarr; candidate ranking &rarr; volcano plot.
**Outputs:** `biomarker_deg_table.csv` &middot; `biomarker_top_candidates.csv` &middot; `biomarker_pathway_enrichment.csv` &middot; `biomarker_volcano_plot.png` &middot; `biomarker_report.txt`

### 3. Causal Inference (MR)
```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```
Simulated GWAS summary stats &rarr; genome-wide significant SNP instruments &rarr; IVW estimation &rarr; leave-one-out sensitivity &rarr; MR scatter / funnel plots.
**Outputs:** `causal_ivw_results.csv` &middot; `causal_loo_results.csv` &middot; `causal_mr_scatter.png` &middot; `causal_mr_funnel.png` &middot; `causal_interpretation.txt`

---

## 📊 Example Workflow Outputs

| Workflow | Representative Figure | Size |
|:---|:---|:---:|
| Literature | entity co-occurrence knowledge graph (40 entities / 30 abstracts) | varies |
| Biomarker | formatted volcano plot (DEG analysis) | 86 KB |
| Causal | MR scatter plot (IVW slope labeled) + funnel | 127 KB |

> The knowledge graph is a high-resolution network graph — view it locally in `outputs/literature/`. The other figures are all < 1 MB and preview directly.

---

## 📦 Installation

```bash
# Option 1: source install (recommended)
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .

# Option 2: pip install (coming after v1.0 validation phase)
# pip install bioresearch-agent
```
**Dependencies:** Python 3.9+, pandas &middot; numpy &middot; scipy &middot; matplotlib &middot; requests &middot; networkx

### Environment check
```bash
bioresearch doctor
```
Validates Python version, dependencies, demo files, network connectivity, and output-directory permissions.

---

## 🎮 Interfaces

### CLI
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
bioresearch run biomarker --disease "Parkinson's disease"
bioresearch run causal   --exposure BMI --outcome "Type 2 Diabetes"
bioresearch doctor
```

### Python SDK
```python
from bioresearch import Agent

agent = Agent()
result = agent.run(
    workflow="literature",
    query="microglia Alzheimer's disease",
    output_dir="outputs/literature",
)

print(result.success)      # True
print(result.report_path)  # outline.md path
print(result.figures)      # ["knowledge_graph.png"]
```

### API Contract (Tool Spec)
Register as a tool for Claude Desktop / Cursor / LangChain / any OpenAI-compatible function-calling system:
```json
{
  "name": "bioresearch_run",
  "description": "Execute biomedical research workflows",
  "parameters": {
    "workflow": "literature | biomarker | causal",
    "query": "research topic (for literature)",
    "disease": "disease name (for biomarker)",
    "exposure": "exposure trait (for causal)",
    "outcome": "outcome trait (for causal)"
  }
}
```
Full tool spec in `bioresearch/toolspec.json`.

### External Client Integration (Skills / Tool Interface)
BioResearch Agent provides a lightweight **client-integration layer** that lets external AI clients and developer environments invoke the biomedical workflows through a standardized schema. This is an *interface layer, not an autonomous capability layer*: it dispatches to the underlying workflow modules and introduces no reasoning or analysis of its own.

Supported clients:
- Claude Desktop
- Cursor
- LangChain-compatible agents
- OpenAI-compatible function-calling systems

The integration package ships as:
- `bioresearch/toolspec.json` — the full tool specification
- `skills/` — optional client-side skill definitions for Claude/Cursor-style loading

These files carry invocation instructions and parameter schemas only. All computation is executed by the framework's workflow modules.

---

## 📂 Project Structure

```
bioresearch-agent/
├── bioresearch/         # SDK + CLI package
├── bio-research-os/      # core framework (modules, demos, examples)
├── skills/              # optional client-side skill definitions (Claude/Cursor)
├── outputs/              # generated outputs (gitignored)
├── assets/               # documentation figures
├── README.md
├── RELEASE_NOTES.md      # v1.0.0 release notes
├── pyproject.toml
└── Makefile
```

---

## 🛣️ Roadmap

### Planned

- Declarative workflow configuration
- Pluggable model-agnostic backend interface
- Additional research workflows
- Expanded data source integrations

---

## 📜 License

MIT

---

> **BioResearch Agent Framework** — *From structured research inputs to reproducible computational outputs.*
