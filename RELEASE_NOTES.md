# BioResearch Agent Framework v1.0.0

> From structured research inputs to reproducible computational outputs.

## Highlights

- **Unified CLI + SDK interface** — `bioresearch run` and `Agent.run()` execute through the
  exact same safe executor, so behavior never diverges between the two entry points.
- **Three runnable biomedical workflows**
  - **Literature Review** — PubMed synthesis, entity co-occurrence knowledge graph, gap analysis
  - **Biomarker Discovery** — (GEO or synthetic) differential expression, volcano plot, pathway enrichment
  - **Causal Inference** — Mendelian randomization (IVW) with leave-one-out sensitivity plots
- **Reproducible, contract-tested outputs** — every CI run asserts `report_path`, `tables`, and
  `figures` exist on disk; consistent output structure across runs via fixed seeds.
- **CI-tested on Python 3.9 – 3.12** via GitHub Actions (CLI Smoke, SDK Contract, Determinism).
- **Programmatic Python SDK + CLI + LLM tool spec** (`toolspec.json`) for Claude / Cursor / LangChain.
- **Standardized outputs** with validation checks at each execution stage.

## Installation

```bash
# From source (current)
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .
bioresearch doctor
```

## Quickstart

```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```

```python
from bioresearch import Agent

result = Agent().run(workflow="literature", query="microglia Alzheimer's disease")
assert result.success
print(result.report_path, result.figures)
```

## What's in the v1.0.0 history

| Commit | Type | Notes |
|--------|------|-------|
| `v1.0: BioResearch Agent Framework initial release` | feat | Foundation: SDK + CLI + 3 workflows + engines |
| `refactor(sdk): delegate Agent.run to cli._run_safely` | refactor | SDK and CLI share one execution path |
| `refactor(paths): single source of truth` | refactor | `PROJECT_ROOT`/`DEMO_DIR`/`MAIN_PY` centralized |
| `refactor(cli): remove duplicated run_doctor` | refactor | Eliminated copy-paste `run_doctor` |
| `ci: emit full SDK diagnostic` | ci | Actionable CI logs instead of bare `AssertionError` |
| `fix(deps): declare networkx as required dependency` | fix | Root-cause fix for SDK Test figure failure |
| `refactor(sdk): deterministic report_path` | fix | Fixed-priority report selection |
| `test(ci): strengthen SDK assertions` | test | Explicit output contract in CI |

## Breaking changes

**None.** This is the first stable release; the public API (`Agent.run`, `bioresearch` CLI) is stable.

## Known limitations

- LLM adapters (OpenAI / Claude / local) are planned, not yet bundled — demos run on public
  APIs + synthetic fallbacks, no key required.
- Workflow config is currently code-defined; YAML-driven workflows are on the roadmap.
