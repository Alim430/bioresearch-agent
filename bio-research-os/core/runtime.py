from core.state import ResearchState
from core.router import route_module

class ResearchRuntime:
    def __init__(self):
        self.state = ResearchState()

    def run(self, query: str):
        self.state.question = query

        # Step 1: Question Engine
        self.state = route_module("question", self.state)

        # Step 2: Data Intelligence
        self.state = route_module("data", self.state)

        # Step 3: Bioinformatics Analysis
        self.state = route_module("analysis", self.state)

        # Step 4: Causal Inference
        self.state = route_module("causal", self.state)

        # Step 5: Narrative Construction
        self.state = route_module("narrative", self.state)

        # Step 6: Review Simulation
        self.state = route_module("review", self.state)

        return self.state.final_output
