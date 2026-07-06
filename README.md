# BioResearch Agent Framework

> **A biomedical LLM tool framework that executes structured research workflows via modular agents and engines.**

[![CI](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```bash
pip install bioresearch-agent
bioresearch run literature --query "microglia Alzheimer's disease"
```

---

## ⚡ 10-Second Start

```bash
# 1. Clone & install
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .

# 2. Check your environment
bioresearch doctor

# 3. Run a workflow
bioresearch run literature --query "microglia Alzheimer's disease"

# 4. See outputs
ls outputs/literature/
# lit_review_summary_table.csv
# lit_review_knowledge_graph.png
# lit_review_outline.md
```

**No LLM key required for demos** — they run with public APIs + synthetic fallbacks.

---

## 🎯 What This Is

**BioResearch Agent Framework** is a **runnable AI system** that automates end-to-end biomedical research through structured reasoning workflows.

### System Capabilities (Reasoning Layer)

| Capability | Description |
|:---|:---|
| **Biomedical literature reasoning** | Systematic synthesis of scientific literature with entity extraction, knowledge graph construction, and gap identification |
| **Omics data interpretation** | Statistical analysis of gene expression, variant, and molecular profiling data with biological contextualization |
| **Causal inference in biological systems** | Mendelian randomization and causal discovery methods for exposure-outcome relationships |
| **Multi-modal evidence integration** | Combining literature, statistical, and mechanistic evidence into unified confidence assessments |
| **Hypothesis generation & validation** | Novel hypothesis construction from cross-domain evidence with falsifiability testing |
| **Scientific narrative synthesis** | Structured report generation with evidence grading, citation management, and figure production |

### Research Workflows (Execution Layer)

These capabilities are exposed through concrete, runnable workflows:

| Your Input | Workflow Executed | What You Get |
|:---|:---|:---|
| "Review microglia in Alzheimer's" | Literature synthesis pipeline | Structured review + knowledge graph + gap analysis |
| "Find biomarkers for Parkinson's" | Omics analysis pipeline | Volcano plot + candidate ranking + pathway enrichment |
| "Does BMI cause Type 2 Diabetes?" | Causal inference pipeline | MR estimate + sensitivity plots + interpretation |

**Key difference:** We don't just generate text. We run the **full pipeline** — data retrieval, statistical analysis, evidence grading, and publication-ready outputs.

---

## 🚀 Three Commands, Three Real Workflows

### 1. Literature Review

```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```

**What happens:**
1. Queries PubMed via NCBI E-utilities
2. Extracts & summarizes abstracts
3. Builds entity co-occurrence knowledge graph
4. Identifies knowledge gaps heuristically
5. Generates structured review outline

**Output:**
- `lit_review_summary_table.csv` — article summaries
- `lit_review_knowledge_graph.png` — entity network
- `lit_review_knowledge_gaps.txt` — identified gaps
- `lit_review_outline.md` — structured outline

### 2. Biomarker Discovery

```bash
bioresearch run biomarker --disease "Parkinson's disease"
```

**What happens:**
1. Downloads GEO dataset (GSE7621) or generates synthetic data
2. Runs differential expression (t-test + Bonferroni)
3. Hypergeometric pathway enrichment (KEGG/GO)
4. Ranks candidates by effect size × significance
5. Generates volcano plot + report

**Output:**
- `biomarker_deg_table.csv` — all genes with fold-change & p-values
- `biomarker_top_candidates.csv` — ranked top candidates
- `biomarker_pathway_enrichment.csv` — enriched pathways
- `biomarker_volcano_plot.png` — publication-quality figure
- `biomarker_report.txt` — plain-text summary

### 3. Causal Inference (Mendelian Randomization)

```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```

**What happens:**
1. Simulates realistic GWAS summary statistics
2. Selects genome-wide significant SNP instruments
3. Runs Inverse-Variance Weighted (IVW) MR
4. Leave-one-out sensitivity analysis
5. Generates MR scatter + funnel plots

**Output:**
- `causal_ivw_results.csv` — causal effect estimate
- `causal_loo_results.csv` — sensitivity analysis
- `causal_mr_scatter.png` — MR scatter plot
- `causal_mr_funnel.png` — funnel plot
- `causal_interpretation.txt` — full interpretation report

---

## 📊 Why This vs. Existing Tools

| Task | Manual | ChatGPT / Claude | BioResearch Agent |
|:---|:---:|:---:|:---:|
| Literature review (20 papers) | 4–6 hours | 5 min (text summary only) | **1.5 min** (full report + graph + gaps) |
| Biomarker discovery | 1–2 days | Can't access GEO / run stats | **3 min** (end-to-end pipeline) |
| Causal inference (MR) | 1–2 hours | No MR capability | **2 min** (full analysis + plots) |

**Every output is evidence-graded (A–E).** Every stage has gate checks. Every claim is traceable to data.

---

## 🏗️ Architecture: Abstraction Layers

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERFACE LAYER                                        │
│  CLI  │  Python SDK  │  LLM Tool (Claude/Cursor/LangChain)  │
├─────────────────────────────────────────────────────────────┤
│  WORKFLOW LAYER                                              │
│  literature  │  biomarker  │  causal  │  [extensible]        │
├─────────────────────────────────────────────────────────────┤
│  REASONING LAYER — 6 Engines                                 │
│  Question → Retrieval → Analysis → Evidence → Narrative      │
│  → Execution                                                 │
├─────────────────────────────────────────────────────────────┤
│  LIFECYCLE LAYER — 12 Stages                                 │
│  Ideation → Hypothesis → Literature → Data → Analysis →      │
│  Evidence → Synthesis → Manuscript → Review → Revision →     │
│  Submission → Publication                                    │
├─────────────────────────────────────────────────────────────┤
│  PLUGIN LAYER — Methods & Data Sources                       │
│  PubMed │ GEO │ KEGG │ GO │ GWAS │ DESeq2 │ IVW-MR          │
└─────────────────────────────────────────────────────────────┘
```

**Design principle:** Capabilities live at the **reasoning layer** (abstract, model-agnostic). Methods live at the **plugin layer** (swappable, domain-specific). Workflows bridge the two.

Each of the 12 lifecycle stages has a **gate**: PASS → advance, REVISE → loop back, FAIL → abort with reason.

---

## 📦 Installation

### Option 1: pip (when published)
```bash
pip install bioresearch-agent
```

### Option 2: From source (now)
```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
```

**Requirements:** Python 3.9+, pandas, numpy, scipy, matplotlib, requests, networkx

### Health Check
```bash
bioresearch doctor
```

Verifies Python version, dependencies, demo files, network connectivity, and output directory permissions.

---

## 🎮 Usage: Three Layers

### Layer 1: CLI (80% of users)

```bash
# Run pre-built workflows
bioresearch run literature --query "microglia Alzheimer's disease"
bioresearch run biomarker --disease "Parkinson's disease"
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"

# Check environment
bioresearch doctor
```

### Layer 2: Python SDK

```python
from bioresearch import Agent

agent = Agent()

result = agent.run(
    workflow="literature",
    query="microglia Alzheimer's disease",
    output_dir="outputs/literature"
)

print(result.success)      # True
print(result.report_path)  # path to outline.md
print(result.figures)      # ["knowledge_graph.png"]
```

### Layer 3: LLM Tool Integration

BioResearch Agent can be registered as an **LLM tool** for Claude Desktop, Cursor, LangChain, or any OpenAI-compatible function-calling system:

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

See `bioresearch/toolspec.json` for the full tool specification.

---

## 📂 Project Structure

```
bioresearch-agent/
├── bioresearch/              # SDK + CLI package
│   ├── __init__.py           # Agent class
│   ├── cli.py                # bioresearch CLI
│   ├── __main__.py           # python -m bioresearch
│   └── toolspec.json         # LLM tool spec
├── bio-research-os/          # Core framework
│   ├── core/                 # Router, state, orchestrator
│   ├── engines/              # 6 research engines (reasoning layer)
│   ├── demos/                # 3 runnable workflows
│   └── examples/             # SDK usage examples
├── outputs/                  # Generated outputs (gitignored)
├── assets/                   # Documentation figures
├── README.md                 # This file
├── RELEASE_NOTES.md          # v1.0 release notes
├── arxiv-abstract.md         # Paper abstract
├── setup.py                  # Package install config
├── pyproject.toml
└── Makefile                  # Quick commands
```

---

## 🖼️ Output Gallery

**Literature Review:**
- Co-occurrence knowledge graph of 40 entities from 30 PubMed abstracts
- Structured markdown outline with identified knowledge gaps
- CSV summary table with one-sentence summaries per article

**Biomarker Discovery:**
- Publication-quality volcano plot (DEG analysis)
- Ranked candidate table with fold-change & adjusted p-values
- Pathway enrichment results (KEGG/GO)

**Causal Inference:**
- MR scatter plot with IVW regression line
- Funnel plot for publication bias assessment
- Full interpretation report with heterogeneity check

---

## 📄 Paper

- **Title:** *BioResearch Agent: A Tool-First Multi-Agent Framework for Biomedical Research Automation*
- **Abstract:** See `arxiv-abstract.md`
- **Target:** arXiv (cs.AI, q-bio.QM) → NeurIPS / ICML AI for Science Workshop

---

## 🛣️ Roadmap

| Phase | Feature | Status |
|:---|:---|:---:|
| **Now** | 3 runnable workflows (literature / biomarker / causal) | ✅ |
| **Now** | Unified CLI (`bioresearch run`) | ✅ |
| **Now** | SDK (`Agent.run()`) | ✅ |
| **Now** | Health check (`bioresearch doctor`) | ✅ |
| **Now** | LLM tool spec (`toolspec.json`) | ✅ |
| **Next** | LLM adapter (OpenAI / Claude / local) | 🔜 |
| **Next** | Workflow YAML config | 🔜 |
| **Future** | Plugin ecosystem (new data sources & analysis methods) | 📋 |
| **Future** | Multi-agent collaboration (reviewer agent, editor agent) | 📋 |

---

## 📜 License

MIT

---

> **BioResearch Agent Framework** — *From hypothesis to publication, one command.*
