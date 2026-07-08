---
name: bioresearch-agent-router
description: Classify a free-text research intent into the right BioResearch Agent workflow (literature / biomarker / causal / case-study / doctor) using a deterministic, rule-based router. Use when an AI client receives an open-ended biomedical research request and must pick which workflow or skill to invoke — NOT to generate or evaluate hypotheses. No LLM, no network.
---

# BioResearch Agent — Agent Router Skill

## Capability

A **rule-based intent classifier** that translates a free-text research request into one of the
framework's workflows/skills:

| Route | Workflow / skill |
|:---|:---|
| `literature` | Literature review + co-occurrence graph (`bioresearch-literature-analysis`) |
| `biomarker` | Biomarker discovery — DEG + enrichment (`bioresearch-biomarker-discovery`) |
| `causal` | Mendelian randomization (`bioresearch-causal-inference`) |
| `case-study` | Disease case study / validation run (`bioresearch-disease-case-study`) |
| `doctor` | Environment & reproducibility check (`bioresearch-environment-check`) |

It is **intent translation, not reasoning**: it maps a request to an *existing* workflow and emits
the matching CLI command. It does **not** generate, rank, or evaluate hypotheses, and uses **no
model and no network** — the same input always yields the same route (deterministic).

## Run

```bash
bioresearch route "find biomarkers for Parkinson's disease using GSE7621"
bioresearch route "test the causal effect of BMI on type 2 diabetes with Mendelian randomization"
```

Output is JSON: `{route, confidence, matched_keywords, scores, rationale, suggestion}` plus a
suggested CLI command. `confidence` is the share of all matched keywords belonging to the winning
route; an unmatched intent returns `route: "unknown"` with a suggestion list of available routes.

## When to invoke

An agent should call this router *first* when it gets an ambiguous or free-form biomedical request,
to decide which specialized skill/workflow to dispatch to. It is the entry funnel of the skill
system — not a replacement for the analysis skills themselves.

## Note

Honest scope: keyword-substring matching only. It will not understand paraphrases that contain
none of the known keywords (it then returns `unknown` rather than guessing). Extend
`bioresearch/router.py:ROUTE_KEYWORDS` to cover new phrasing.
