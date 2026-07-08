---
name: bioresearch-literature-analysis
description: Run a reproducible biomedical literature review via the BioResearch Agent literature workflow (PubMed retrieval, entity co-occurrence knowledge graph, structured review outline). Use when the user asks for a literature review, research-gap analysis, or a synthesized reading of PubMed papers on a biomedical topic.
---

# BioResearch Agent — Literature Analysis Skill

## Capability

Performs a structured literature review over PubMed: retrieval → abstract parsing → biomedical
entity extraction → co-occurrence knowledge graph → research-gap identification → structured
outline. Produces data-derived artifacts instead of free-text summary only.

## Run

```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```

## Outputs (in `outputs/literature/`)

- `lit_review_summary_table.csv` — extracted entities per paper
- `lit_review_knowledge_graph.png` — entity co-occurrence network
- `lit_review_knowledge_gaps.txt` — identified gaps
- `lit_review_outline.md` — structured review outline

## Note

This skill dispatches to the framework's `literature` workflow. It adds **no reasoning of its
own**; all computation runs in the workflow modules. Requires no LLM key — runs on public PubMed
APIs with synthetic fallback.
