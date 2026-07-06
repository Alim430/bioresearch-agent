"""
engines/evidence_engine.py
==========================
Layer-2 Engine: Evidence Integration & Grading (Stage 9)

Sub-agents
----------
- **EvidenceGradingAgent**: Applies GRADE-inspired or custom rubrics to each
  evidence source; outputs A–E grades with confidence intervals.
- **ConflictDetectionAgent**: Identifies contradictory findings across sources,
  flags p-hacking signals, and proposes reconciliation strategies.

Input
-----
All evidence sources: literature, statistical results, bioinformatics results,
causal estimates, and any user-supplied evidence.

Output
------
- `integrated_evidence`: unified evidence table with provenance.
- `evidence_grades`: per-source A–E mapping.
- `confidence_score`: aggregate confidence (0–1).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from core.state import Evidence, EvidenceGrade, GateResult, ResearchState, Stage


class EvidenceEngine:
    """Orchestrates evidence grading, conflict detection, and integration."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self.name = "EvidenceEngine"
        self.stage_range = (Stage.EVIDENCE_INTEGRATION, Stage.EVIDENCE_INTEGRATION)

    # --------------------------------------------------------------------- #
    #  Sub-agent stubs
    # --------------------------------------------------------------------- #
    def _evidence_grading_agent(self, sources: List[Dict[str, Any]]) -> Dict[str, EvidenceGrade]:
        """Grade each evidence source."""
        if self.mock_mode:
            grades = {}
            for src in sources:
                sid = src.get("id", str(random.randint(1000, 9999)))
                # Bias toward middle grades in mock
                grades[sid] = random.choice([
                    EvidenceGrade.A, EvidenceGrade.B, EvidenceGrade.B,
                    EvidenceGrade.C, EvidenceGrade.C, EvidenceGrade.D,
                ])
            return grades
        raise NotImplementedError("EvidenceGradingAgent real implementation not wired.")

    def _conflict_detection_agent(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect contradictions and p-hacking signals."""
        if self.mock_mode:
            conflicts = []
            if len(sources) > 1 and random.random() < 0.3:
                conflicts.append({
                    "type": "directional_conflict",
                    "description": "Two sources report opposite effect directions.",
                    "severity": "moderate",
                })
            if random.random() < 0.15:
                conflicts.append({
                    "type": "p_hacking_signal",
                    "description": "Suspicious clustering of p-values near 0.05 threshold.",
                    "severity": "high",
                })
            return {
                "conflicts_detected": len(conflicts),
                "conflicts": conflicts,
                "recommendation": "Sensitivity analysis recommended" if conflicts else "No action needed",
            }
        raise NotImplementedError("ConflictDetectionAgent real implementation not wired.")

    # --------------------------------------------------------------------- #
    #  Helpers
    # --------------------------------------------------------------------- #
    def _collect_sources(self, state: ResearchState) -> List[Dict[str, Any]]:
        """Normalize all available evidence into a flat source list."""
        sources: List[Dict[str, Any]] = []
        for i, paper in enumerate(state.literature):
            sources.append({"id": f"lit_{i}", "type": "literature", "data": paper})
        if state.statistical_results:
            sources.append({"id": "stats_0", "type": "statistical", "data": state.statistical_results})
        if state.bioinformatics_results:
            sources.append({"id": "bio_0", "type": "bioinformatics", "data": state.bioinformatics_results})
        if state.causal_estimates:
            sources.append({"id": "causal_0", "type": "causal", "data": state.causal_estimates})
        return sources

    def _aggregate_confidence(self, grades: Dict[str, EvidenceGrade]) -> float:
        """Compute aggregate confidence from grade distribution."""
        if not grades:
            return 0.0
        mapping = {EvidenceGrade.A: 1.0, EvidenceGrade.B: 0.8, EvidenceGrade.C: 0.6, EvidenceGrade.D: 0.4, EvidenceGrade.E: 0.2}
        scores = [mapping.get(g, 0.5) for g in grades.values()]
        return round(sum(scores) / len(scores), 3)

    # --------------------------------------------------------------------- #
    #  Engine interface
    # --------------------------------------------------------------------- #
    def validate(self, state: ResearchState) -> GateResult:
        """Require upstream analysis results."""
        errors: List[str] = []
        if not state.statistical_results and not state.bioinformatics_results and not state.causal_estimates:
            errors.append("No analysis results found; run AnalysisEngine first.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.EVIDENCE_INTEGRATION,
            messages=["EvidenceEngine validation complete."],
            errors=errors,
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Grade, detect conflicts, and integrate evidence."""
        sources = self._collect_sources(state)
        grades = self._evidence_grading_agent(sources)
        conflict_report = self._conflict_detection_agent(sources)
        confidence = self._aggregate_confidence(grades)

        # Store structured evidence objects in EvidenceStore if available
        for src in sources:
            ev = Evidence(
                source=src["type"],
                evidence_type=src["type"],
                grade=grades.get(src["id"], EvidenceGrade.C),
                confidence=confidence,
                data=src["data"],
                tags=[src["type"], "stage_9"],
            )
            if state.evidence_store:
                state.evidence_store.deposit(ev)

        state.evidence_grades = grades
        state.integrated_evidence = {
            "sources": sources,
            "grades": {k: v.value for k, v in grades.items()},
            "conflict_report": conflict_report,
            "aggregate_confidence": confidence,
        }
        state.current_stage = Stage.EVIDENCE_INTEGRATION
        state.touch()
        return state

    def gate(self, state: ResearchState) -> GateResult:
        """Gate check: require integrated evidence and minimum confidence."""
        errors: List[str] = []
        if not state.integrated_evidence:
            errors.append("Integrated evidence report missing.")
        else:
            conf = state.integrated_evidence.get("aggregate_confidence", 0.0)
            if conf < 0.5:
                errors.append(f"Aggregate confidence too low ({conf} < 0.5).")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.EVIDENCE_INTEGRATION,
            messages=["EvidenceEngine gate check completed."],
            errors=errors,
        )
