"""
engines/question_engine.py
==========================
Layer-2 Engine: Question & Hypothesis Generation (Stages 1–2)

Sub-agents
----------
- **IdeaAgent**: Extracts core research intent from free-text user queries.
- **NoveltyAgent**: Scans current literature to flag novelty gaps.
- **BrainstormAgent**: Generates divergent research angles and variations.
- **HypothesisAgent**: Formalizes primary / alternative / null hypotheses with
  falsifiability criteria.

Input
-----
User query (free text or structured).

Output
------
HypothesisPackage: primary hypothesis, ranked alternatives, null hypothesis,
and explicit falsifiability criteria.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from core.state import GateResult, Hypothesis, ResearchState, Stage


class QuestionEngine:
    """Orchestrates ideation and hypothesis generation."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self.name = "QuestionEngine"
        self.stage_range = (Stage.IDEATION, Stage.HYPOTHESIS_GENERATION)

    # --------------------------------------------------------------------- #
    #  Sub-agent stubs
    # --------------------------------------------------------------------- #
    def _idea_agent(self, query: str) -> Dict[str, Any]:
        """Parse user intent into structured research vectors."""
        if self.mock_mode:
            return {
                "intent": f"Investigate relationship in: {query}",
                "entities": [f"Entity_{i}" for i in range(random.randint(2, 5))],
                "research_vectors": [f"Vector_{i}" for i in range(random.randint(2, 4))],
            }
        raise NotImplementedError("IdeaAgent real implementation not wired.")

    def _novelty_agent(self, vectors: List[str]) -> Dict[str, Any]:
        """Assess novelty by comparing vectors to known literature landmarks."""
        if self.mock_mode:
            return {
                "novelty_score": round(random.uniform(0.3, 0.95), 3),
                "gaps": [f"Gap_{i}" for i in range(random.randint(1, 4))],
                "similar_papers": random.randint(0, 15),
            }
        raise NotImplementedError("NoveltyAgent real implementation not wired.")

    def _brainstorm_agent(self, vectors: List[str], gaps: List[str]) -> List[str]:
        """Generate divergent research angles."""
        if self.mock_mode:
            angles = [f"Angle: explore {v} via {random.choice(['CRISPR', 'scRNA-seq', 'metabolomics', 'clinical cohort'])}" for v in vectors]
            angles += [f"Angle: fill gap '{g}'" for g in gaps]
            return angles
        raise NotImplementedError("BrainstormAgent real implementation not wired.")

    def _hypothesis_agent(self, angles: List[str]) -> Hypothesis:
        """Formalize hypotheses."""
        if self.mock_mode:
            primary = f"{random.choice(angles)} leads to significant phenotypic change."
            alternatives = [f"Alt-{i}: {a} has no effect" for i, a in enumerate(angles[1:3], 1)]
            null_h = f"{primary.split(' leads to')[0]} does not lead to significant change."
            falsifiability = [
                "p < 0.05 under two-sided t-test",
                "Effect size Cohen's d > 0.5",
                "Replication in n ≥ 2 independent cohorts",
            ]
            return Hypothesis(
                primary=primary,
                alternatives=alternatives,
                null_hypothesis=null_h,
                falsifiability_criteria=falsifiability,
                confidence=round(random.uniform(0.6, 0.95), 3),
            )
        raise NotImplementedError("HypothesisAgent real implementation not wired.")

    # --------------------------------------------------------------------- #
    #  Engine interface
    # --------------------------------------------------------------------- #
    def validate(self, state: ResearchState) -> GateResult:
        """Validate that the engine can run given current state.

        Requires: non-empty user query in state.metadata or stdin fallback.
        """
        messages: List[str] = []
        errors: List[str] = []
        query = state.hypothesis.primary if state.hypothesis else ""
        if not query and not self.mock_mode:
            errors.append("No user query found in state.hypothesis.primary.")
        else:
            messages.append("Validation passed (mock mode allows empty query).")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.IDEATION,
            messages=messages,
            errors=errors,
        )

    def run(self, state: ResearchState, query: Optional[str] = None) -> ResearchState:
        """Execute the full ideation → hypothesis pipeline."""
        if state.hypothesis and state.hypothesis.primary:
            query = state.hypothesis.primary
        if not query:
            query = "user research interest"

        idea = self._idea_agent(query)
        novelty = self._novelty_agent(idea["research_vectors"])
        angles = self._brainstorm_agent(idea["research_vectors"], novelty["gaps"])
        hypothesis = self._hypothesis_agent(angles)

        # Attach novelty metadata
        hypothesis.metadata = {
            "novelty_score": novelty["novelty_score"],
            "similar_papers": novelty["similar_papers"],
            "gaps": novelty["gaps"],
            "research_vectors": idea["research_vectors"],
        }

        state.hypothesis = hypothesis
        state.current_stage = Stage.HYPOTHESIS_GENERATION
        state.touch()
        return state

    def gate(self, state: ResearchState) -> GateResult:
        """Gate check: ensure hypothesis package is complete before downstream."""
        errors: List[str] = []
        if not state.hypothesis:
            errors.append("Hypothesis object missing.")
        else:
            if not state.hypothesis.primary:
                errors.append("Primary hypothesis empty.")
            if not state.hypothesis.null_hypothesis:
                errors.append("Null hypothesis empty.")
            if not state.hypothesis.falsifiability_criteria:
                errors.append("Falsifiability criteria missing.")
        return GateResult(
            can_proceed=len(errors) == 0,
            stage=Stage.HYPOTHESIS_GENERATION,
            messages=["Gate check completed."],
            errors=errors,
        )
