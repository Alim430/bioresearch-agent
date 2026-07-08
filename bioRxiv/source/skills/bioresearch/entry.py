"""BioResearch Skill v1 — runtime entry (thin binding over bioresearch.Agent).

Design rule (architecture review):
    Skill -> WorkflowRouter -> Agent.run
This module is the ONLY thing an LLM / agent runtime needs to import. It is a
semantic wrapper, not a new system layer: it does not re-implement any workflow
logic, it only routes and forwards to the existing Agent runtime.

Compatible with: Claude Desktop tool import, Cursor agent tool, OpenAI function
calling, LangChain tool.

Status: v1.1 design. Part of feat/skills-layer ONLY; not in the frozen v1.0.0 main.
"""

from __future__ import annotations

from typing import Any, Optional

from bioresearch import Agent
from bioresearch import AgentResult  # the real output contract: success/error/report_path/tables/figures


# Lightweight router: maps a free-form task to a workflow when `workflow` is omitted.
def _auto_route(task: str) -> str:
    t = (task or "").lower()
    if any(k in t for k in ("gene", "expression", "biomarker", "deg", "volcano")):
        return "biomarker"
    if any(k in t for k in ("causal", "mr", "mendelian", "instrument", "exposure")):
        return "causal"
    return "literature"


def run(workflow: Optional[str] = None, **kwargs: Any) -> AgentResult:
    """Unified skill entry.

    Args:
        workflow: one of literature | biomarker | causal. If None, auto-routed
                  from `query` / `task`.
        **kwargs: workflow-specific params (query, disease, exposure, outcome,
                  output_dir, use_mock, use_synthetic, geo_id, n_snps, seed,
                  max_results, alpha).
    Returns:
        AgentResult with success / error / report_path / tables / figures.
    """
    if not workflow:
        workflow = _auto_route(kwargs.get("query") or kwargs.get("task") or "")
    agent = Agent()
    return agent.run(workflow=workflow, **kwargs)


# Explicit, precision skills (recommended for agent chaining / prompt control)
def literature_review(query: str, **kw: Any) -> AgentResult:
    return run("literature", query=query, **kw)


def biomarker_discovery(disease: str, **kw: Any) -> AgentResult:
    return run("biomarker", disease=disease, **kw)


def causal_inference(exposure: str, outcome: str, **kw: Any) -> AgentResult:
    return run("causal", exposure=exposure, outcome=outcome, **kw)


if __name__ == "__main__":
    # Quick self-check (deterministic mock).
    r = run("literature", query="microglia Alzheimer disease", use_mock=True)
    print("success:", r.success)
    print("report_path:", r.report_path)
    print("tables:", r.tables)
    print("figures:", r.figures)
