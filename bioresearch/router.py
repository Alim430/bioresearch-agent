"""Agent Router v0 — rule-based intent classification (no LLM).

Given a free-text research *intent* (what a user or agent asks for), classify it to one
of the framework's workflows/skills:

    literature   - literature review, research-gap analysis, PubMed synthesis
    biomarker    - differential expression, pathway enrichment, biomarker/candidate genes, GEO data
    causal       - Mendelian randomization / causal effect between exposure and outcome
    case-study   - disease case study / validation run / benchmark on real data
    doctor       - environment check, troubleshooting, validate installation

Design constraints (per project policy):
* **Rule-based, deterministic.** No model, no network, no randomness. Same input -> same output.
* **Intent translation, not reasoning.** It maps a request to an *existing* workflow/skill;
  it does not generate, rank, or evaluate hypotheses.
* **Honest confidence.** Confidence = share of all matched keywords that belong to the
  winning route; if no keyword matches, the route is ``unknown`` with a suggestion list.

Usage:
    from bioresearch.router import classify_intent
    classify_intent("find biomarkers for Parkinson's disease using GSE7621")
    # -> {"route": "biomarker", "confidence": 0.66, "matched_keywords": [...], ...}
"""
from __future__ import annotations

import json
from typing import Dict, List

# Keyword patterns (substring match, case-insensitive). Ordered by specificity:
# more specific workflows (case-study, causal) are listed before broader ones so
# tie-breaking favours the narrower intent.
ROUTE_KEYWORDS: Dict[str, List[str]] = {
    "case-study": [
        "case study", "case studies", "validation run", "benchmark",
        "real data", "real dataset", "validate the framework", "validation suite",
        "blind benchmark", "known-gene recovery",
    ],
    "causal": [
        "mendelian randomization", "two-sample mr", "mr ", "causal", "causality",
        "instrumental variable", "genetic instrument", "exposure", "outcome", "ivw",
        "cause and effect", "causal effect",
    ],
    "biomarker": [
        "biomarker", "biomarkers", "differential expression", "deg", "gene expression",
        "geo dataset", "geo data", "rna-seq", "rnaseq", "microarray", "candidate gene",
        "candidate genes", "volcano", "upregulated", "downregulated", "expression data",
        "transcriptom",
    ],
    "literature": [
        "literature review", "literature", "pubmed", "paper", "papers", "publication",
        "research gap", "research gaps", "knowledge gap", "co-occurrence",
        "systematic review", "abstract", "citation", "bibliography", "survey of literature",
        "what has been published", "related work",
    ],
    "doctor": [
        "environment", "doctor", "troubleshoot", "validate install", "check dependencies",
        "reproducibility check", "installation", "dependency",
    ],
}

# Tie-break priority (higher = preferred when scores tie). More specific first.
ROUTE_PRIORITY = {
    "case-study": 5,
    "causal": 4,
    "biomarker": 3,
    "literature": 2,
    "doctor": 1,
}

AVAILABLE_ROUTES = list(ROUTE_KEYWORDS.keys())


def _matched_for(route: str, text: str) -> List[str]:
    """Return the keyword patterns from `route` that occur in `text`."""
    hits = []
    for kw in ROUTE_KEYWORDS[route]:
        if kw in text:
            hits.append(kw.strip())
    return hits


def classify_intent(intent: str) -> Dict:
    """Classify a free-text research intent into a workflow route.

    Returns a dict with keys: route, confidence, matched_keywords, scores, rationale.
    ``route`` is one of AVAILABLE_ROUTES or ``"unknown"``.
    """
    text = (intent or "").lower().strip()
    scores: Dict[str, int] = {}
    matched: Dict[str, List[str]] = {}
    for route in AVAILABLE_ROUTES:
        hits = _matched_for(route, text)
        matched[route] = hits
        scores[route] = len(hits)

    total_hits = sum(scores.values())

    if total_hits == 0:
        return {
            "route": "unknown",
            "confidence": 0.0,
            "matched_keywords": [],
            "scores": scores,
            "rationale": "No known workflow keyword matched. Try naming a workflow "
                         "(literature / biomarker / causal / case-study) or 'doctor' for env check.",
            "suggestion": AVAILABLE_ROUTES,
        }

    # Pick the winning route: highest score, tie-break by ROUTE_PRIORITY.
    best_route = max(
        AVAILABLE_ROUTES,
        key=lambda r: (scores[r], ROUTE_PRIORITY[r]),
    )
    winner_hits = scores[best_route]
    confidence = round(winner_hits / total_hits, 4)

    other = {r: scores[r] for r in AVAILABLE_ROUTES if scores[r] > 0 and r != best_route}
    rationale = (
        f"Matched {winner_hits} keyword(s) for '{best_route}' "
        f"({', '.join(matched[best_route])}); "
        f"total keyword hits across routes = {total_hits}."
    )
    if other:
        rationale += f" Also matched: {other}."

    return {
        "route": best_route,
        "confidence": confidence,
        "matched_keywords": matched[best_route],
        "scores": scores,
        "rationale": rationale,
        "suggestion": None,
    }


def route_to_command(route: str, intent: str = "") -> str:
    """Map a route to the corresponding CLI command (for agent/copilot use)."""
    if route == "literature":
        return 'bioresearch run literature --query "<topic>"'
    if route == "biomarker":
        return 'bioresearch run biomarker --disease "<disease>" [--geo-id GSExxxx]'
    if route == "causal":
        return 'bioresearch run causal --exposure "<exposure>" --outcome "<outcome>"'
    if route == "case-study":
        return "python bio-research-os/eval/case_study_pd.py --output-dir docs/case-study"
    if route == "doctor":
        return "bioresearch doctor"
    return "bioresearch --help"


def main(argv: List[str] | None = None) -> int:
    """CLI entry: `bioresearch route "<intent>"`."""
    import argparse

    ap = argparse.ArgumentParser(description="Classify a research intent into a workflow (rule-based).")
    ap.add_argument("intent", nargs="+", help="Free-text research intent / request")
    args = ap.parse_args(argv)
    result = classify_intent(" ".join(args.intent))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nSuggested command: {route_to_command(result['route'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
