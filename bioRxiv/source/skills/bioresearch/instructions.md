# BioResearch Skill — Instructions

> **Status:** v1.1 design. Lives on `feat/skills-layer` only. **Not** part of the
> v1.0.0 submission artifact (the `main` branch is frozen). Do not merge to `main`
> until the arXiv submission is cut.

## What this skill does

BioResearch is a reproducible workflow engine for end-to-end biomedical analysis.
As a skill, it exposes three research workflows as a single callable capability
unit that an LLM / agent can invoke:

| Workflow     | Required argument        | What it produces                                            |
| ------------ | ------------------------ | ----------------------------------------------------------- |
| `literature` | `query`                  | Literature review report (`.md`), knowledge-graph figure    |
| `biomarker`  | `disease`                | Biomarker ranking table (`.csv`), volcano / DEG figures     |
| `causal`     | `exposure`, `outcome`    | Mendelian-randomization result table (`.csv`), forest figure |

All workflows return a **stable output contract**: `success`, `error`,
`report_path`, `tables`, `figures` (absolute paths). That stable contract is what
makes the skill chainable by an agent.

## When to use it

- The user asks for a **literature review** on a biomedical topic.
- The user wants **biomarker / gene-expression** analysis for a disease.
- The user asks about **causal relationships** between a risk factor (exposure)
  and a disease/outcome (causal inference via Mendelian randomization).
- The user wants **reproducible, file-backed** scientific outputs (figures +
  tables + report) rather than a chat answer.

## When NOT to use it

- Pure factual QA that does not need a workflow run.
- Tasks outside biomedicine (this skill is domain-scoped).
- When the user only wants a plain explanation — prefer answering directly.

## How to call it

### 1. As an LLM tool (recommended)

Pass `tools.json` to any tool-calling client. Call `bioresearch_run` with
`workflow` + the required args for that workflow. See `INTEGRATION.md` for
Claude / OpenAI / Cursor / MCP wiring.

### 2. From Python (SDK)

```python
from bioresearch import Agent

agent = Agent()  # llm="mock" by default — deterministic, no network
result = agent.run(workflow="literature", query="microglia Alzheimer disease")
print(result.success, result.report_path, result.figures)
```

### 3. From the skill runtime wrapper (entry.py)

```python
from skills.bioresearch.entry import run, literature_review, biomarker_discovery, causal_inference

run("literature", query="microglia Alzheimer disease", use_mock=True)
literature_review("microglia Alzheimer disease")
biomarker_discovery("Parkinson disease", use_synthetic=True)
causal_inference("BMI", "Type 2 Diabetes", seed=42)
```

### 4. From the CLI

```bash
bioresearch run literature --query "microglia Alzheimer disease" --use-mock
bioresearch run biomarker --disease "Parkinson disease" --use-synthetic
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes" --seed 42
```

## Sample prompts that should trigger this skill

- "Review the literature on microglia in Alzheimer's disease and give me a summary with figures."
- "Find differentially expressed genes and candidate biomarkers for Parkinson's disease."
- "Is BMI causally linked to Type 2 Diabetes? Run a Mendelian randomization analysis."

## Wiring rules (important)

- **This skill is a packaging/abstraction layer, not a runtime rewrite.** It binds
  to the existing `bioresearch.Agent.run`; it does not re-implement any engine.
- **Output contract is fixed.** Do not add or rename fields — agents depend on it.
- **Deterministic by default.** Mock mode needs no network or API key; this is the
  recommended default for reproducible demos.
- **Model-agnostic.** No vendor is hard-coded; see `INTEGRATION.md`.
