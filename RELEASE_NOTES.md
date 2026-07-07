## BioResearch Agent v1.0.0

**One command. Three workflows. Zero API keys.**

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
./skills/install.sh        # Installs framework + workflow skills
```

---

### What is it?

A **runnable, reproducible workflow framework** for biomedical research. Not a text generator. Not a chat wrapper. An actual pipeline that downloads data, runs statistics, and produces figures.

### Three workflows, all included

| Workflow | One-liner | What you get |
|:---|:---|:---|
| **Literature** | `bioresearch run literature --query "microglia Alzheimer's disease"` | PubMed retrieval → knowledge graph → gap report |
| **Biomarker** | `bioresearch run biomarker --disease "Parkinson's disease"` | GEO analysis → DEG table → volcano plot |
| **Causal** | `bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"` | MR estimation → scatter/funnel plots |

All three run **without an LLM API key**. Public data + synthetic fallbacks.

### Why it's different

Most "AI for science" projects generate text summaries. This one **runs the actual analysis**:

- Downloads GEO datasets
- Runs differential expression (t-test + Bonferroni)
- Performs Mendelian randomization (IVW)
- Produces publication-quality figures

And it's **fully reproducible**: fixed seeds, CI-tested on Python 3.9–3.12, deterministic outputs.

### Install as agent skills (Claude / Cursor / LangChain)

```bash
./skills/install.sh        # Auto-detects your agent client
```

After install, your AI agent can invoke these workflows directly:

> "Run a literature review on microglia in Alzheimer's disease"

The agent routes it to `bioresearch run literature` and returns structured outputs.

### Architecture

- **6 processing modules** (Question → Retrieval → Analysis → Evidence → Narrative → Execution)
- **12-stage execution diagram** (8 implemented, 4 conceptual)
- **3 access layers** (CLI · Python SDK · API Contract / Tool Spec)
- **3 skill manifests** for agent integration

### Paper

Accompanying paper submitted to arXiv (cs.SE + q-bio.QM):

> *"BioResearch Agent: A Tool-First Framework for Structured Biomedical Research Workflows"*

Paper: [arXiv link coming]
Code: [github.com/Alim430/bioresearch-agent](https://github.com/Alim430/bioresearch-agent)

### What's in this release

- ✅ CLI (`bioresearch run` / `bioresearch doctor`)
- ✅ Python SDK (`Agent.run()`)
- ✅ 3 reproducible demo workflows
- ✅ CI green (Python 3.9–3.12)
- ✅ Determinism check (seed-42 verified)
- ✅ Agent skill manifests (Claude / Cursor compatible)
- ✅ Tool spec JSON for LangChain / OpenAI function calling

### Get started in 30 seconds

```bash
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
bioresearch doctor
bioresearch run literature --query "microglia Alzheimer's disease"
```

See `README.md` for full documentation.
