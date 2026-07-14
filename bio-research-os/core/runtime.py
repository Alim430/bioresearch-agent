"""
core/runtime.py
===============
Resumable research runtime.

Wraps the deterministic engine sequence (question -> data -> analysis -> causal ->
narrative -> review) with JSON-based state persistence so a run can be interrupted
and resumed from the last completed stage. This is pure progress bookkeeping — it
introduces no autonomous reasoning and never self-modifies framework code.
"""

from __future__ import annotations

from .state import ResearchState, Stage
from .router import route_module
from .persistence import StateStore

# Linear engine sequence (deterministic, rule-based — not a model).
_STAGE_ORDER = ["question", "data", "analysis", "causal", "narrative", "review"]

# Maps each step to the lifecycle Stage it completes (for resume bookkeeping).
_STEP_TO_STAGE = {
    "question": Stage.HYPOTHESIS_GENERATION,
    "data": Stage.DATA_ACQUISITION,
    "analysis": Stage.BIOINFORMATICS_ANALYSIS,
    "causal": Stage.CAUSAL_INFERENCE,
    "narrative": Stage.NARRATIVE_CONSTRUCTION,
    "review": Stage.PRE_SUBMISSION_REVIEW,
}


class ResearchRuntime:
    """Runs the engine sequence with optional JSON state persistence + resume."""

    def __init__(self, state_path: str = None) -> None:
        self.state_path = state_path
        self.store = StateStore(state_path) if state_path else None
        self.state = self.store.load() if self.store else ResearchState()

    def _resume_index(self) -> int:
        """Index of the first step not yet completed (0 = start fresh)."""
        if not self.store:
            return 0
        saved = self.store.load()
        if saved is None:
            return 0
        for i, (key, stg) in enumerate(_STEP_TO_STAGE.items()):
            if stg == saved.current_stage:
                return i + 1
        return 0

    def run(self, query: str):
        """Execute the engine sequence from the resume point.

        Args:
            query: the research question / intent.

        Returns:
            The final output produced by the last engine (``state.final_output``).
        """
        self.state.question = query
        for key in _STAGE_ORDER[self._resume_index():]:
            self.state = route_module(key, self.state)
            self.state.current_stage = _STEP_TO_STAGE[key]
            self.state.touch()
            if self.store:
                self.store.save(self.state)
        return self.state.final_output
