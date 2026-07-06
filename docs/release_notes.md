# 🚀 BioResearch Agent Framework v1.0

### 🧬 A runnable LLM-agnostic agent system for biomedical research automation

We are excited to announce the first **release candidate (v1.0)** of the BioResearch Agent Framework — a fully runnable, LLM-agnostic system for end-to-end biomedical research workflows.

This release marks the transition from **framework design → production-ready system**.

---

# ✨ Highlights

### ⚡ Core capabilities

* 🧠 Biomedical literature reasoning and synthesis
* 🧬 Omics data interpretation and analysis
* 🔬 Statistical and causal inference for biological systems
* 📊 Structured scientific report generation
* 🧾 Knowledge graph + evidence graph outputs
* 🔗 Multi-modal biomedical evidence integration

---

### 🧩 System architecture

* 6 modular research engines (Question → Retrieval → Analysis → Evidence → Narrative → Execution)
* 12-stage biomedical research lifecycle with gated transitions
* Plugin-based biomedical data access layer
* LLM-agnostic tool execution layer
* Safe execution wrapper with deterministic fallbacks

---

### 🖥️ Interfaces

* **CLI** (`bioresearch run`) — primary user interface
* **Python SDK** (`Agent.run()`) — programmatic access
* **LLM Tool interface** (`toolspec.json`) — Claude / Cursor / LangChain compatible
* **Health check** (`bioresearch doctor`) — environment verification

---

### 🛠️ Example usage

```bash
# Literature review
bioresearch run literature \
  --query "microglia Alzheimer's disease"

# Biomarker discovery
bioresearch run biomarker \
  --disease "Parkinson's disease"

# Causal inference (Mendelian Randomization)
bioresearch run causal \
  --exposure BMI --outcome "Type 2 Diabetes"
```

---

### 🧪 Python API

```python
from bioresearch import Agent

agent = Agent()

result = agent.run(
    workflow="literature",
    query="microglia Alzheimer's disease",
    output_dir="outputs/literature"
)

print(result.success)      # True
print(result.report_path)  # path to generated report
print(result.figures)      # ["knowledge_graph.png"]
```

---

# 📦 Output types

Each workflow produces structured scientific artifacts:

| Workflow | Outputs |
|:---|:---|
| **Literature** | `summary_table.csv`, `knowledge_graph.png`, `outline.md`, `gaps.txt` |
| **Biomarker** | `volcano_plot.png`, `deg_table.csv`, `top_candidates.csv`, `pathway_enrichment.csv`, `report.txt` |
| **Causal** | `mr_scatter.png`, `mr_funnel.png`, `ivw_results.csv`, `loo_results.csv`, `interpretation.txt` |

---

# 🔌 LLM Tool Integration

Supports direct integration with:

* Claude Desktop (via `toolspec.json`)
* Cursor (via MCP / tool calling)
* LangChain (via tool definition)
* OpenAI Assistants API (via function calling)

---

# 🧠 Design principle

> The LLM is the reasoning engine.
> The framework is the execution layer.

BioResearch Agent does not embed an LLM. It provides **structured tool execution** that any LLM can call — making it model-agnostic and future-proof.

---

# 📊 System status

| Component | Status |
|:---|:---:|
| CLI workflows | ✅ Stable |
| Python SDK | ✅ Stable |
| Tool interface (`toolspec.json`) | ✅ Ready |
| Demo pipelines (3 workflows) | ✅ Verified |
| Output generation | ✅ Reproducible |
| Safe execution wrapper | ✅ Active |
| Environment health check (`doctor`) | ✅ Active |

---

# 🚀 Release status

> **v1.0 — Production ready for GitHub + arXiv submission**

---

# 📄 Citation

If you use this framework in your research:

```bibtex
@software{bioresearch_agent_2026,
  title = {BioResearch Agent Framework},
  year = {2026},
  note = {A runnable LLM-agnostic agent system for biomedical research automation}
}
```

---

*Released July 2026*
