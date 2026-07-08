# Example — Alzheimer's Disease Literature Review

**Goal:** Ask your AI assistant for a structured reading of recent microglia research in Alzheimer's disease, and get a real co-occurrence knowledge graph instead of a prose summary.

## Via AI assistant (after installing the `literature` skill)

> **You:** Run a literature review on microglia in Alzheimer's disease and identify research gaps.

> **Assistant:** Running the `bioresearch` literature workflow…
> - Retrieved 30 abstracts from PubMed (query: *microglia Alzheimer's disease*)
> - Extracted entities and built a co-occurrence network
> - Surfaced 3 under-explored gaps
>
> Outputs written to `outputs/literature/`:
> - `lit_review_summary_table.csv`
> - `lit_review_knowledge_graph.png`
> - `lit_review_knowledge_gaps.txt`
> - `lit_review_outline.md`

## Via CLI (same engine)

```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```

## What it actually does

PubMed E-utilities retrieval → abstract parsing → entity extraction → co-occurrence graph →
gap identification → structured outline. No LLM key required; runs on public APIs with a
synthetic fallback if PubMed is unreachable.

See a sample knowledge graph: `assets/figure3_output_gallery.png` (left panel) or
`outputs/literature/lit_review_knowledge_graph.png`.
