"""
core/state.py
=============
Base types and state definitions for the BioResearch Agent Framework.
All engines import from this module.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class Stage(Enum):
    """Research Lifecycle Stages (Layer 1)."""
    IDEATION = 1
    HYPOTHESIS_GENERATION = 2
    LITERATURE_SURVEY = 3
    DATA_ACQUISITION = 4
    KNOWLEDGE_GRAPH_BUILDING = 5
    STATISTICAL_ANALYSIS = 6
    BIOINFORMATICS_ANALYSIS = 7
    CAUSAL_INFERENCE = 8
    EVIDENCE_INTEGRATION = 9
    NARRATIVE_CONSTRUCTION = 10
    PRE_SUBMISSION_REVIEW = 11
    PUBLICATION = 12


class EvidenceGrade(Enum):
    """Evidence quality grades (A–E scale)."""
    A = "A"  # High quality, low risk of bias
    B = "B"  # Moderate quality
    C = "C"  # Some concerns
    D = "D"  # Major concerns
    E = "E"  # Very low quality / reject


@dataclass
class Hypothesis:
    """Represents a research hypothesis package."""
    primary: str = ""
    alternatives: List[str] = field(default_factory=list)
    null_hypothesis: str = ""
    falsifiability_criteria: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0–1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """A single piece of evidence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = ""  # e.g., PubMed, GEO, user-upload
    evidence_type: str = ""  # e.g., "experimental", "computational", "literature"
    grade: EvidenceGrade = EvidenceGrade.C
    confidence: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class GateResult:
    """Result of a gate check between stages."""
    can_proceed: bool = False
    stage: Stage = Stage.IDEATION
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ResearchState:
    """Central mutable state container for the entire research lifecycle."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_stage: Stage = Stage.IDEATION
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Layer 1 outputs (populated by engines)
    hypothesis: Optional[Hypothesis] = None
    literature: List[Dict[str, Any]] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    qc_report: Optional[Dict[str, Any]] = None
    statistical_results: Optional[Dict[str, Any]] = None
    bioinformatics_results: Optional[Dict[str, Any]] = None
    causal_estimates: Optional[Dict[str, Any]] = None
    integrated_evidence: Optional[Dict[str, Any]] = None
    evidence_grades: Dict[str, EvidenceGrade] = field(default_factory=dict)
    manuscript: Optional[Dict[str, Any]] = None
    figures: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    review_report: Optional[Dict[str, Any]] = None
    accept_probability: float = 0.0
    submission_materials: Optional[Dict[str, Any]] = None

    # Shared infrastructure handles (injected at runtime)
    state_manager: Optional[Any] = None
    evidence_store: Optional[Any] = None
    memory_layer: Optional[Any] = None
    knowledge_graph: Optional[Any] = None
    tool_manager: Optional[Any] = None

    def touch(self) -> None:
        """Update the timestamp."""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "current_stage": self.current_stage.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "hypothesis": self.hypothesis,
            "literature_count": len(self.literature),
            "dataset_count": len(self.datasets),
            "figure_count": len(self.figures),
            "table_count": len(self.tables),
        }
