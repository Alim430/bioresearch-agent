#!/usr/bin/env python3
"""
Case Study 3 (Alzheimer's disease literature gap analysis)
===========================================================
Biomedical Workflow Validation Suite

LITERATURE-ANALYSIS METHODOLOGY CASE.

Wraps the framework's literature-review engine (demo_literature_review.py:
fetch_pubmed_ids / fetch_pubmed_details / extract_entities / build_cooccurrence_graph
/ identify_knowledge_gaps / generate_review_outline) and runs it on an
Alzheimer's-topic corpus.

Honesty notes (do NOT overclaim)
--------------------------------
* This environment has NO usable PubMed access (network is proxied/blocked), so
  the engine falls back to its built-in ILLUSTRATIVE corpus (10 AD/microglia
  abstracts). The case records data_mode honestly.
* The point is to validate the LITERATURE-ANALYSIS PIPELINE (entity extraction ->
  co-occurrence graph -> knowledge-gap detection -> review outline), not to make
  a real bibliometric claim about the AD field.
* Evidence grade C: offline methodology demonstration on a built-in corpus.
  next_validation points to a real PubMed/OpenAlex run.

Outputs (--output-dir, default github/docs/case-study/):
  AD_lit_summary_table.csv, AD_lit_knowledge_gaps.txt,
  AD_lit_outline.md, AD_lit_knowledge_graph.png,
  AD_lit_report.txt, AD_lit_evidence_package.json

Usage:
  python case_study_ad_literature.py --output-dir ../docs/case-study
  python case_study_ad_literature.py --topic "microglia in Alzheimer's disease" \
      --max-results 10 --use-mock --output-dir ../docs/case-study
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

# Make the framework engine importable
HERE = os.path.dirname(os.path.abspath(__file__))
DEMOS = os.path.join(HERE, "..", "demos")
sys.path.insert(0, os.path.abspath(DEMOS))

MPLCONFIGDIR = "/tmp/matplotlib_ad_lit"
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = MPLCONFIGDIR
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import demo_literature_review as lit_engine  # noqa: E402

DEFAULT_TOPIC = "microglia in Alzheimer's disease"

# AD-relevant terms we expect an AD/microglia corpus to contain (sanity check).
EXPECTED_AD_TERMS = ["microglia", "alzheimer", "trem2", "amyloid", "tau",
                     "neuroinflammation", "lipid", "synapse", "astrocyte"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo_dir):
    try:
        return subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def print_progress(msg):
    print(f"[PROGRESS] {msg}", file=sys.stderr)


def get_articles(topic, max_results, use_mock):
    """Attempt real PubMed; fall back to built-in illustrative corpus.

    Returns (articles, data_mode).
    """
    if use_mock:
        print_progress("Using built-in illustrative corpus (forced).")
        return lit_engine.MOCK_CORPUS[:max_results], "built-in illustrative corpus (forced)"
    # Remove dead proxy so requests go direct (will fail fast if no internet).
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    pmids = lit_engine.fetch_pubmed_ids(topic, max_results)
    if pmids:
        articles = lit_engine.fetch_pubmed_details(pmids)
        if articles:
            return articles, "real PubMed E-utilities"
    print_progress("PubMed unavailable; falling back to built-in illustrative corpus.")
    return lit_engine.MOCK_CORPUS[:max_results], "built-in illustrative corpus (PubMed API unreachable)"


def top_entities(G, k=15):
    if G is None or not getattr(lit_engine, "HAS_NETWORKX", False):
        return []
    return sorted(G.nodes(data=True), key=lambda x: x[1].get("freq", 0), reverse=True)[:k]


def main():
    ap = argparse.ArgumentParser(description="AD literature gap methodology case study")
    ap.add_argument("--topic", type=str, default=DEFAULT_TOPIC)
    ap.add_argument("--max-results", type=int, default=10)
    ap.add_argument("--use-mock", action="store_true",
                    help="Force built-in illustrative corpus (skip PubMed attempt).")
    ap.add_argument("--output-dir", default=os.path.join(HERE, "..", "..", "docs", "case-study"))
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    articles, data_mode = get_articles(args.topic, args.max_results, args.use_mock)
    if not articles:
        print("[ERROR] no articles; abort.", file=sys.stderr)
        sys.exit(1)
    is_real = data_mode.startswith("real PubMed")

    # Pipeline
    summary_path = os.path.join(args.output_dir, "AD_lit_summary_table.csv")
    lit_engine.save_summary_table(articles, summary_path)

    G = lit_engine.build_cooccurrence_graph(articles, top_n=40)
    graph_path = os.path.join(args.output_dir, "AD_lit_knowledge_graph.png")
    lit_engine.plot_knowledge_graph(G, args.topic, graph_path)

    gaps = lit_engine.identify_knowledge_gaps(articles, args.topic)
    gaps_path = os.path.join(args.output_dir, "AD_lit_knowledge_gaps.txt")
    lit_engine.save_knowledge_gaps(gaps, gaps_path)

    outline = lit_engine.generate_review_outline(args.topic, articles, gaps)
    outline_path = os.path.join(args.output_dir, "AD_lit_outline.md")
    with open(outline_path, "w", encoding="utf-8") as fh:
        fh.write(outline)

    # ---- Benchmark (pipeline sanity) ----
    n_articles = len(articles)
    summary_df = pd.read_csv(summary_path) if os.path.exists(summary_path) else pd.DataFrame()
    n_summary_rows = len(summary_df)
    n_nodes = G.number_of_nodes() if G is not None else 0
    n_edges = G.number_of_edges() if G is not None else 0
    n_gaps = len(gaps)
    outline_nonempty = bool(outline.strip())
    top = top_entities(G, k=40)
    top_terms = [n for n, _ in top]

    # AD-term sanity: how many expected AD terms appear in the combined corpus text?
    combined = " ".join(
        (a.get("title", "") + " " + a.get("abstract", "")).lower() for a in articles
    )
    ad_term_hits = [t for t in EXPECTED_AD_TERMS if t in combined]
    ad_term_coverage = len(ad_term_hits) / len(EXPECTED_AD_TERMS)

    pipeline_ok = (n_summary_rows == n_articles and n_nodes >= 5 and n_edges >= 5
                   and n_gaps >= 1 and outline_nonempty)

    # Report
    report_path = os.path.join(args.output_dir, "AD_lit_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("AD Literature Gap Analysis — Methodology Case Study\n")
        fh.write("=" * 64 + "\n\n")
        grade_label = ("B (real public data; PubMed E-utilities)"
                       if is_real else "C (offline methodology; built-in corpus)")
        fh.write(f"EVIDENCE GRADE: {grade_label}\n")
        fh.write(f"Topic            : {args.topic}\n")
        fh.write(f"Data mode        : {data_mode}\n")
        fh.write(f"Articles         : {n_articles}\n")
        fh.write(f"Summary rows     : {n_summary_rows}\n")
        fh.write(f"Graph nodes/edges: {n_nodes} / {n_edges}\n")
        fh.write(f"Knowledge gaps   : {n_gaps}\n")
        fh.write(f"Outline non-empty: {outline_nonempty}\n")
        fh.write(f"AD-term coverage : {ad_term_coverage:.2f} ({len(ad_term_hits)}/{len(EXPECTED_AD_TERMS)})\n")
        fh.write(f"Pipeline sanity  : {'PASS' if pipeline_ok else 'FAIL'}\n\n")
        fh.write("Top entities (by frequency):\n")
        for name, data in top:
            fh.write(f"  - {name}: {data.get('freq', 0)}\n")
        fh.write("\nIdentified knowledge gaps:\n")
        for i, g in enumerate(gaps, 1):
            fh.write(f"  {i}. {g}\n")

    # Evidence package
    pkg = {
        "metadata": {
            "case_study": "AD literature gap analysis",
            "workflow": "literature-analysis",
            "topic": args.topic,
            "date": "2026-07-08",
            "agent_version": "bioresearch-agent v1.1.0 + case-study-ad-literature",
            "mode": data_mode,
        },
        "provenance": {
            "git_commit": git_commit(os.path.join(HERE, "..", "..")),
            "python": sys.version.split()[0],
            "env": "managed venv (python3.13 + numpy/pandas/matplotlib/networkx)",
            "engine": "demo_literature_review.py (extract_entities, build_cooccurrence_graph, identify_knowledge_gaps, generate_review_outline)",
        },
        "methods": ["fetch_pubmed_or_fallback", "extract_entities", "build_cooccurrence_graph",
                     "plot_knowledge_graph", "identify_knowledge_gaps", "generate_review_outline"],
        "results": {
            "n_articles": n_articles,
            "n_summary_rows": n_summary_rows,
            "graph_nodes": n_nodes,
            "graph_edges": n_edges,
            "n_knowledge_gaps": n_gaps,
            "outline_nonempty": outline_nonempty,
            "ad_term_coverage": ad_term_coverage,
            "top_entities": top_terms[:15],
        },
        "benchmark": {
            "type": "pipeline_sanity",
            "checks": {
                "summary_rows_match_articles": n_summary_rows == n_articles,
                "graph_nodes_ge_5": n_nodes >= 5,
                "graph_edges_ge_5": n_edges >= 5,
                "gaps_ge_1": n_gaps >= 1,
                "outline_nonempty": outline_nonempty,
            },
            "pipeline_ok": pipeline_ok,
            "expected_ad_terms": EXPECTED_AD_TERMS,
            "ad_term_hits": ad_term_hits,
            "ad_term_coverage": ad_term_coverage,
        },
        "evidence_grade": ("B (real public data via PubMed E-utilities; literature-analysis pipeline)"
                            if is_real else
                            "C (offline methodology; built-in illustrative corpus; not a real bibliometric claim)"),
        "limitations": ([
            "Real PubMed corpus is a single-topic top-N snapshot (no deduplication / recency ranking)",
            "Naive entity extraction (stop-word + heuristic), not NER-model based",
            "Knowledge-gap detection is heuristic, not expert-curated",
        ] if is_real else [
            "Built-in illustrative corpus (10 AD/microglia abstracts); PubMed API unreachable here",
            "Naive entity extraction (stop-word + heuristic), not NER-model based",
            "Knowledge-gap detection is heuristic, not expert-curated",
            "No deduplication / recency ranking against a real citation graph",
        ]),
        "next_validation": (
            "Broader PubMed/OpenAlex query with date-range + deduplication; NER-based entity extraction; comparison against a curated AD knowledge graph"
            if is_real else
            "Run with network access to pull real PubMed abstracts; then broaden + NER-based extraction"),
    }
    pkg_path = os.path.join(args.output_dir, "AD_lit_evidence_package.json")
    with open(pkg_path, "w", encoding="utf-8") as fh:
        json.dump(pkg, fh, indent=2)

    print("\n" + "=" * 64)
    print("AD LITERATURE GAP CASE COMPLETE")
    print("=" * 64)
    print(f"Topic      : {args.topic}")
    print(f"Data mode  : {data_mode}")
    print(f"Articles   : {n_articles} | Graph: {n_nodes}n/{n_edges}e | Gaps: {n_gaps}")
    print(f"AD-term cov: {ad_term_coverage:.2f} | Pipeline: {'PASS' if pipeline_ok else 'FAIL'}")
    print(f"Evidence   : {'B (real public data)' if is_real else 'C (offline methodology)'}")
    print(f"Evidence pkg -> {pkg_path}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
