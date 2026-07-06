"""
Orchestrator — Coordinates 6 Core Engines across the 12-Stage Research Lifecycle.

Three-Layer Architecture:
    Research Lifecycle (12 Stages) → Research Engines (6) → Specialized Agents (23)
"""

from typing import Dict, List
from core.state import ResearchState, Stage, GateResult
from engines.question_engine import QuestionEngine
from engines.retrieval_engine import RetrievalEngine
from engines.analysis_engine import AnalysisEngine
from engines.evidence_engine import EvidenceEngine
from engines.narrative_engine import NarrativeEngine
from engines.execution_engine import ExecutionEngine

class Orchestrator:
    """
    Orchestrator
    ============
    Routes the ResearchState through the 6 Core Engines in sequence,
    managing gates, backward iteration, and workflow templates.
    
    Engines:
        1. QuestionEngine     → Stages 1–2 (Ideation & Hypothesis)
        2. RetrievalEngine    → Stages 3–5 (Literature & Data)
        3. AnalysisEngine     → Stages 6–8 (Stats, Bioinfo, Causal)
        4. EvidenceEngine     → Stage 9  (Integration & Grading)
        5. NarrativeEngine    → Stage 10 (Writing & Narrative)
        6. ExecutionEngine    → Stages 11–12 (Review & Publication)
    """
    
    def __init__(self, mock: bool = True):
        self.engines = {
            Stage.IDEATION: QuestionEngine(mock=mock),
            Stage.HYPOTHESIS: QuestionEngine(mock=mock),
            Stage.LITERATURE: RetrievalEngine(mock=mock),
            Stage.EXPERIMENTAL_DESIGN: RetrievalEngine(mock=mock),
            Stage.DATA_ACQUISITION: RetrievalEngine(mock=mock),
            Stage.STATISTICAL_ANALYSIS: AnalysisEngine(mock=mock),
            Stage.BIOINFORMATICS: AnalysisEngine(mock=mock),
            Stage.CAUSAL_INFERENCE: AnalysisEngine(mock=mock),
            Stage.EVIDENCE_INTEGRATION: EvidenceEngine(mock=mock),
            Stage.NARRATIVE: NarrativeEngine(mock=mock),
            Stage.PRE_SUBMISSION_REVIEW: ExecutionEngine(mock=mock),
            Stage.PUBLICATION: ExecutionEngine(mock=mock),
        }
        
        self.stage_order = [
            Stage.IDEATION,
            Stage.HYPOTHESIS,
            Stage.LITERATURE,
            Stage.EXPERIMENTAL_DESIGN,
            Stage.DATA_ACQUISITION,
            Stage.STATISTICAL_ANALYSIS,
            Stage.BIOINFORMATICS,
            Stage.CAUSAL_INFERENCE,
            Stage.EVIDENCE_INTEGRATION,
            Stage.NARRATIVE,
            Stage.PRE_SUBMISSION_REVIEW,
            Stage.PUBLICATION,
        ]
        
        # Engine → fallback stage mapping for gate failures
        self.fallback_map = {
            Stage.HYPOTHESIS: Stage.IDEATION,
            Stage.LITERATURE: Stage.HYPOTHESIS,
            Stage.EXPERIMENTAL_DESIGN: Stage.HYPOTHESIS,
            Stage.DATA_ACQUISITION: Stage.EXPERIMENTAL_DESIGN,
            Stage.STATISTICAL_ANALYSIS: Stage.DATA_ACQUISITION,
            Stage.BIOINFORMATICS: Stage.STATISTICAL_ANALYSIS,
            Stage.CAUSAL_INFERENCE: Stage.BIOINFORMATICS,
            Stage.EVIDENCE_INTEGRATION: Stage.CAUSAL_INFERENCE,
            Stage.NARRATIVE: Stage.EVIDENCE_INTEGRATION,
            Stage.PRE_SUBMISSION_REVIEW: Stage.NARRATIVE,
            Stage.PUBLICATION: Stage.PRE_SUBMISSION_REVIEW,
        }
    
    def run(self, state: ResearchState, max_iterations: int = 10) -> ResearchState:
        """Execute the full 12-stage research lifecycle."""
        for iteration in range(max_iterations):
            state.iteration = iteration + 1
            
            for stage in self.stage_order:
                if self._should_skip(state, stage):
                    continue
                
                state.current_stage = stage
                engine = self.engines[stage]
                
                # Validate
                if not engine.validate(state):
                    state.log(f"Stage {stage.value} validation failed")
                    continue
                
                # Execute
                state = engine.run(state)
                state.log(f"Stage {stage.value} executed")
                
                # Gate
                gate_result = engine.gate(state)
                state.log(f"Gate {stage.value}: {gate_result.value}")
                
                if gate_result == GateResult.FAIL:
                    fallback = self.fallback_map.get(stage)
                    if fallback:
                        state.log(f"Fallback to {fallback.value}")
                        state.current_stage = fallback
                    else:
                        break
                elif gate_result == GateResult.REVISE:
                    state = engine.run(state)
                    gate_result = engine.gate(state)
                    if gate_result != GateResult.PASS:
                        break
            
            if state.current_stage == Stage.PUBLICATION and state.archived:
                state.log("Research lifecycle completed")
                break
        
        return state
    
    def _should_skip(self, state: ResearchState, stage: Stage) -> bool:
        """Skip data/analysis stages for review/grant workflows."""
        if state.question and "review" in state.question.lower():
            skip = {Stage.EXPERIMENTAL_DESIGN, Stage.DATA_ACQUISITION,
                    Stage.STATISTICAL_ANALYSIS, Stage.BIOINFORMATICS, Stage.CAUSAL_INFERENCE}
            return stage in skip
        return False
