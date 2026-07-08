---
name: bioresearch-literature
description: Invoke the BioResearch Agent literature workflow (PubMed retrieval, entity co-occurrence knowledge graph, structured review outline) through the bioresearch CLI. Use when the user asks for a biomedical literature review, research-gap analysis, or a synthesized reading of PubMed papers on a disease or mechanism.
---

# BioResearch Literature Skill

Client-side integration wrapper for the BioResearch Agent **literature** workflow.
This skill dispatches to the existing `bioresearch` CLI/SDK — it does not add new
analysis or reasoning capabilities of its own.

## Run
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```

## Outputs
- `lit_review_summary_table.csv`
- `lit_review_knowledge_graph.png`
- `lit_review_knowledge_gaps.txt`
- `lit_review_outline.md`
