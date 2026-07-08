# BioResearch Skill — Examples

All examples are grounded in the real `bioresearch.Agent.run` interface.

## A. LLM tool call (unified tool `bioresearch_run`)

```json
[
  {
    "name": "bioresearch_run",
    "arguments": { "workflow": "literature", "query": "microglia in Alzheimer disease" }
  },
  {
    "name": "bioresearch_run",
    "arguments": { "workflow": "biomarker", "disease": "Parkinson disease", "use_synthetic": true }
  },
  {
    "name": "bioresearch_run",
    "arguments": { "workflow": "causal", "exposure": "BMI", "outcome": "Type 2 Diabetes", "seed": 42 }
  }
]
```

## B. Auto-routing (omit `workflow`, let the router pick)

```json
[
  { "name": "bioresearch_run", "arguments": { "task": "find genes expressed in Parkinson disease" } }
]
```
> The router maps "gene / expression / biomarker" -> `biomarker`,
> "causal / mr / mendelian" -> `causal`, otherwise -> `literature`.

## C. Python SDK

```python
from bioresearch import Agent

agent = Agent()

r1 = agent.run("literature", query="microglia Alzheimer disease", use_mock=True)
r2 = agent.run("biomarker", disease="Parkinson disease", use_synthetic=True)
r3 = agent.run("causal", exposure="BMI", outcome="Type 2 Diabetes", seed=42)

for r in (r1, r2, r3):
    print(r.success, r.report_path, r.tables, r.figures)
```

## D. Skill runtime wrapper (entry.py)

```python
from skills.bioresearch.entry import (
    run, literature_review, biomarker_discovery, causal_inference
)

run("literature", query="microglia Alzheimer disease", use_mock=True)
literature_review("microglia Alzheimer disease")
biomarker_discovery("Parkinson disease", use_synthetic=True)
causal_inference("BMI", "Type 2 Diabetes", seed=42)
```

## E. CLI

```bash
bioresearch run literature --query "microglia Alzheimer disease" --use-mock
bioresearch run biomarker --disease "Parkinson disease" --use-synthetic
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes" --seed 42
```

## F. Cursor / Claude Desktop (drop-in)

Point the client at this directory (`skills/bioresearch/`) and let it ingest
`tools.json` + `instructions.md`. The client auto-generates the
`bioresearch_run` tool. No `pip install` required for the tool definition itself
(the Python runtime is needed only at execution time).
