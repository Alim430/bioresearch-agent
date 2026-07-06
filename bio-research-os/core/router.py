"""
Router — Entry point for all workflows.

Three-Layer Architecture:
    Research Lifecycle (12 Stages) → Research Engines (6) → Specialized Agents (23)
"""

from core.state import ResearchState, Stage
from core.orchestrator import Orchestrator

class Router:
    """Routes user requests to the appropriate workflow or engine."""
    
    def __init__(self, mock: bool = True):
        self.orchestrator = Orchestrator(mock=mock)
    
    def run_full_lifecycle(self, question: str, max_iterations: int = 10) -> ResearchState:
        """Run the complete 12-stage research lifecycle through 6 Engines."""
        state = ResearchState(question=question)
        return self.orchestrator.run(state, max_iterations=max_iterations)
    
    def run_stage(self, question: str, target_stage: Stage) -> ResearchState:
        """Run only up to a specific stage."""
        state = ResearchState(question=question)
        for stage in self.orchestrator.stage_order:
            if self.orchestrator._should_skip(state, stage):
                continue
            state.current_stage = stage
            engine = self.orchestrator.engines[stage]
            if engine.validate(state):
                state = engine.run(state)
            if stage == target_stage:
                break
        return state
    
    def run_workflow(self, question: str, workflow_type: str) -> ResearchState:
        """Run a specific workflow template."""
        state = ResearchState(question=question)
        
        workflow_map = {
            "discovery": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                         Stage.DATA_ACQUISITION, Stage.STATISTICAL_ANALYSIS,
                         Stage.BIOINFORMATICS, Stage.EVIDENCE_INTEGRATION,
                         Stage.NARRATIVE, Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION],
            "mechanism": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                         Stage.EXPERIMENTAL_DESIGN, Stage.DATA_ACQUISITION,
                         Stage.STATISTICAL_ANALYSIS, Stage.BIOINFORMATICS,
                         Stage.CAUSAL_INFERENCE, Stage.EVIDENCE_INTEGRATION,
                         Stage.NARRATIVE, Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION],
            "clinical": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                        Stage.EXPERIMENTAL_DESIGN, Stage.DATA_ACQUISITION,
                        Stage.STATISTICAL_ANALYSIS, Stage.BIOINFORMATICS,
                        Stage.CAUSAL_INFERENCE, Stage.EVIDENCE_INTEGRATION,
                        Stage.NARRATIVE, Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION],
            "methodology": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                           Stage.EXPERIMENTAL_DESIGN, Stage.DATA_ACQUISITION,
                           Stage.STATISTICAL_ANALYSIS, Stage.BIOINFORMATICS,
                           Stage.EVIDENCE_INTEGRATION, Stage.NARRATIVE,
                           Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION],
            "review": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                      Stage.NARRATIVE, Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION],
            "grant": [Stage.IDEATION, Stage.HYPOTHESIS, Stage.LITERATURE,
                     Stage.EXPERIMENTAL_DESIGN, Stage.NARRATIVE,
                     Stage.PRE_SUBMISSION_REVIEW, Stage.PUBLICATION]
        }
        
        stages = workflow_map.get(workflow_type, self.orchestrator.stage_order)
        for stage in stages:
            if self.orchestrator._should_skip(state, stage):
                continue
            state.current_stage = stage
            engine = self.orchestrator.engines[stage]
            if engine.validate(state):
                state = engine.run(state)
        return state
