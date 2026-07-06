"""
engines/narrative_engine.py
===========================
Layer-2 Engine: Scientific Writing & Narrative Construction (Stage 10)

Sub-agents
----------
- **WritingAgent**: Drafts IMRAD sections (Intro, Methods, Results, Discussion)
  with citation placeholders and structured argumentation.
- **FigureAgent**: Generates figure specifications, captions, and mock
  visualizations (e.g., volcano plots, PCA, DAGs, forest plots).
- **StorylineAgent**: Ensures logical flow, transitions, and alignment with
  the central hypothesis; flags tangents or weak links.

Input
-----
Integrated evidence report (from EvidenceEngine).

Output
------
- `manuscript`: structured draft with sections and word counts.
- `figures`: list of figure objects with metadata.
- `tables`: list of table objects with metadata.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from core.state import GateResult, ResearchState, Stage


class NarrativeEngine:
    """Orchestrates manuscript drafting, figure generation, and storyline coherence."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self.name = "NarrativeEngine"
        self.stage_range = (Stage.NARRATIVE_CONSTRUCTION, Stage.NARRATIVE_CONSTRUCTION)

    # --------------------------------------------------------------------- #
    #  Sub-agent stubs
    # --------------------------------------------------------------------- #
    def _writing_agent(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Draft IMRAD sections."""
        if self.mock_mode:
            sections = {}
            for sec in ["Introduction", "Methods", "Results", "Discussion"]:
                paragraphs = random.randint(3, 6)
                sections[sec] = {
                    "paragraphs": paragraphs,
                    "word_count": paragraphs * random.randint(120, 220),
                    "key_claims": [f"Claim_{sec}_{i}" for i in range(random.randint(2, 4))],
                    "citation_placeholders": [f"[CITE-{random.randint(1, 50)}]" for _ in range(random.randint(3, 8))],
                }
            sections["Abstract"] = {
                "paragraphs": 1,
                "word_count": random.randint(200, 300),
                "structured": True,
            }
            return {
                "title": f"Mock Manuscript on {random.choice(['Obesity', 'Inflammation', 'Metabolism', 'Single-Cell'])}",
                "sections": sections,
                "total_words": sum(s["word_count"] for s in sections.values()),
            }
        raise NotImplementedError("WritingAgent real implementation not wired.")

    def _figure_agent(self, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate figure specifications."""
        if self.mock_mode:
            figures = []
            figure_types = ["volcano_plot", "pca", "heatmap", "forest_plot", "dag", "bar_chart"]
            for i, ftype in enumerate(random.sample(figure_types, k=random.randint(3, 5)), 1):
                figures.append({
                    "figure_number": i,
                    "type": ftype,
                    "caption": f"Figure {i}: Mock {ftype.replace('_', ' ').title()} showing key findings.",
                    "panels": random.randint(1, 3),
                    "data_source": random.choice(["bioinformatics", "statistical", "causal"]),
                })
            return figures
        raise NotImplementedError("FigureAgent real implementation not wired.")

    def _storyline_agent(self, manuscript: Dict[str, Any], hypothesis: Any) -> Dict[str, Any]:
        """Check logical flow and hypothesis alignment."""
        if self.mock_mode:
            issues = []
            if random.random() < 0.2:
                issues.append({"severity": "minor", "message": "Transition between Methods and Results could be smoother."})
            if random.random() < 0.1:
                issues.append({"severity": "major", "message": "Discussion does not directly address null hypothesis."})
            return {
                "coherence_score": round(random.uniform(0.75, 0.98), 3),
                "hypothesis_aligned": random.random() > 0.15,
                "issues": issues,
                "suggestions": ["Strengthen linkage to central hypothesis in Discussion."] if issues else [],
            }
        raise NotImplementedError("StorylineAgent real implementation not wired.")

    # --------------------------------------------------------------------- #
    #  Engine interface
    # --------------------------------------------------------------------- #
    def validate(self, state: ResearchState) -> GateResult:
        """Require integrated evidence."""
        errors: List[str] = []
        if not state.integrated_evidence:
            errors.append("Integrated evidence missing; run EvidenceEngine first.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.NARRATIVE_CONSTRUCTION,
            messages=["NarrativeEngine validation complete."],
            errors=errors,
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Draft manuscript, figures, and storyline audit."""
        evidence = state.integrated_evidence or {}
        manuscript = self._writing_agent(evidence)
        figures = self._figure_agent(evidence)
        storyline = self._storyline_agent(manuscript, state.hypothesis)

        # Derive tables from results
        tables = []
        if state.statistical_results:
            tables.append({"table_number": 1, "type": "statistical_summary", "caption": "Table 1: Statistical test summaries."})
        if state.bioinformatics_results:
            tables.append({"table_number": 2, "type": "deg_list", "caption": "Table 2: Top differentially expressed molecules."})
        if state.causal_estimates:
            tables.append({"table_number": 3, "type": "causal_estimates", "caption": "Table 3: Causal effect estimates."})

        state.manuscript = manuscript
        state.figures = figures
        state.tables = tables
        state.current_stage = Stage.NARRATIVE_CONSTRUCTION
        state.touch()
        return state

    def gate(self, state: ResearchState) -> GateResult:
        """Gate check: require manuscript and minimum coherence."""
        errors: List[str] = []
        if not state.manuscript:
            errors.append("Manuscript draft missing.")
        if not state.figures:
            errors.append("No figures generated.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.NARRATIVE_CONSTRUCTION,
            messages=["NarrativeEngine gate check completed."],
            errors=errors,
        )
