"""
engines/execution_engine.py
===========================
Layer-2 Engine: Pre-submission Review & Publication (Stages 11–12)

Sub-agents
----------
- **ReviewerSimulationAgent**: Simulates 2–3 independent peer reviewers
  (methodologist, subject expert, statistician) and generates structured
  review reports with Major / Minor / Optional comments.
- **PublicationAgent**: Matches the manuscript to target journals via
  scope/impact analysis, generates cover letters, and packages submission
  materials (main text, figures, tables, supplementary files).

Input
-----
Manuscript draft + figures + tables (from NarrativeEngine).

Output
------
- `review_report`: simulated peer review with decision recommendation.
- `accept_probability`: estimated acceptance likelihood (0–1).
- `submission_materials`: journal match, cover letter, file manifest.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from core.state import GateResult, ResearchState, Stage


class ExecutionEngine:
    """Orchestrates pre-submission review simulation and publication packaging."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self.name = "ExecutionEngine"
        self.stage_range = (Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION)

    # --------------------------------------------------------------------- #
    #  Sub-agent stubs
    # --------------------------------------------------------------------- #
    def _reviewer_simulation_agent(self, manuscript: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate multi-reviewer peer review."""
        if self.mock_mode:
            reviewers = [
                {"role": "methodologist", "expertise": "experimental design"},
                {"role": "subject_expert", "expertise": manuscript.get("title", "topic")},
                {"role": "statistician", "expertise": "biostatistics"},
            ]
            reviews = []
            for rev in reviewers:
                n_major = random.randint(0, 2)
                n_minor = random.randint(1, 4)
                reviews.append({
                    "reviewer_role": rev["role"],
                    "overall_assessment": random.choice(["Accept", "Minor Revision", "Major Revision", "Reject"]),
                    "confidence": random.choice(["High", "Medium", "Low"]),
                    "comments_major": [f"Major comment {i+1} from {rev['role']}" for i in range(n_major)],
                    "comments_minor": [f"Minor comment {i+1} from {rev['role']}" for i in range(n_minor)],
                    "score_innovation": random.randint(1, 5),
                    "score_rigor": random.randint(1, 5),
                    "score_significance": random.randint(1, 5),
                })
            # Consensus decision
            decisions = [r["overall_assessment"] for r in reviews]
            consensus = max(set(decisions), key=decisions.count)
            return {
                "reviews": reviews,
                "consensus": consensus,
                "avg_innovation": round(sum(r["score_innovation"] for r in reviews) / len(reviews), 2),
                "avg_rigor": round(sum(r["score_rigor"] for r in reviews) / len(reviews), 2),
                "avg_significance": round(sum(r["score_significance"] for r in reviews) / len(reviews), 2),
            }
        raise NotImplementedError("ReviewerSimulationAgent real implementation not wired.")

    def _publication_agent(self, manuscript: Dict[str, Any], review_report: Dict[str, Any]) -> Dict[str, Any]:
        """Match journal and prepare submission package."""
        if self.mock_mode:
            journals = ["Nature Medicine", "Cell Metabolism", "PLOS Biology", "eLife", "BMC Medicine", "Frontiers in Immunology"]
            # Heuristic: higher rigor → higher tier
            rigor = review_report.get("avg_rigor", 3)
            tier = 0 if rigor >= 4.2 else 2 if rigor >= 3.0 else 4
            target_journal = journals[min(tier, len(journals) - 1)]
            return {
                "target_journal": target_journal,
                "impact_factor": round(random.uniform(3.0, 45.0), 1),
                "scope_match": round(random.uniform(0.7, 0.99), 2),
                "cover_letter": f"Dear Editor, we submit our work on {manuscript.get('title', 'our research')}...",
                "file_manifest": [
                    "manuscript.docx",
                    "figures.pdf",
                    "tables.xlsx",
                    "supplementary_materials.pdf",
                    "data_availability_statement.txt",
                ],
                "open_access_preference": random.choice([True, False]),
            }
        raise NotImplementedError("PublicationAgent real implementation not wired.")

    # --------------------------------------------------------------------- #
    #  Helpers
    # --------------------------------------------------------------------- #
    def _estimate_accept_probability(self, review_report: Dict[str, Any]) -> float:
        """Map review scores to accept probability."""
        if self.mock_mode:
            base = random.uniform(0.2, 0.85)
            consensus = review_report.get("consensus", "")
            if consensus == "Accept":
                base += 0.1
            elif consensus == "Major Revision":
                base -= 0.15
            elif consensus == "Reject":
                base -= 0.3
            return round(min(max(base, 0.0), 1.0), 3)
        raise NotImplementedError("Accept probability model not wired.")

    # --------------------------------------------------------------------- #
    #  Engine interface
    # --------------------------------------------------------------------- #
    def validate(self, state: ResearchState) -> GateResult:
        """Require manuscript draft."""
        errors: List[str] = []
        if not state.manuscript:
            errors.append("Manuscript missing; run NarrativeEngine first.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.PRE_SUBMISSION_REVIEW,
            messages=["ExecutionEngine validation complete."],
            errors=errors,
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Run reviewer simulation and publication packaging."""
        manuscript = state.manuscript or {}
        review_report = self._reviewer_simulation_agent(manuscript)
        accept_prob = self._estimate_accept_probability(review_report)
        submission = self._publication_agent(manuscript, review_report)

        state.review_report = review_report
        state.accept_probability = accept_prob
        state.submission_materials = submission
        state.current_stage = Stage.PUBLICATION
        state.touch()
        return state

    def gate(self, state: ResearchState) -> GateResult:
        """Gate check: require submission materials and non-zero accept probability."""
        errors: List[str] = []
        if not state.submission_materials:
            errors.append("Submission materials missing.")
        if state.accept_probability <= 0.0:
            errors.append("Accept probability not calculated.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.PUBLICATION,
            messages=["ExecutionEngine gate check completed."],
            errors=errors,
        )
