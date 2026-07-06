"""
engines/retrieval_engine.py
===========================
Layer-2 Engine: Literature Survey & Data Acquisition (Stages 3–5)

Sub-agents
----------
- **LiteratureAgent**: Queries PubMed, arXiv, bioRxiv, and patent DBs;
  ranks by relevance and citation velocity.
- **DataAcquisitionAgent**: Discovers GEO, TCGA, SRA, UK Biobank, FinnGen,
  and proprietary datasets; downloads and caches metadata.
- **KnowledgeGraphAgent**: Builds an entity-relation graph from extracted
  entities (genes, proteins, chemicals, phenotypes).

Input
-----
HypothesisPackage from QuestionEngine.

Output
------
- `literature`: ranked list of articles with relevance scores.
- `datasets`: list of acquired datasets with QC flags.
- `qc_report`: data-quality summary (completeness, batch effects, outliers).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from core.state import GateResult, ResearchState, Stage


class RetrievalEngine:
    """Orchestrates literature retrieval, data acquisition, and knowledge-graph seeding."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self.name = "RetrievalEngine"
        self.stage_range = (Stage.LITERATURE_SURVEY, Stage.KNOWLEDGE_GRAPH_BUILDING)

    # --------------------------------------------------------------------- #
    #  Sub-agent stubs
    # --------------------------------------------------------------------- #
    def _literature_agent(self, hypothesis_text: str) -> List[Dict[str, Any]]:
        """Retrieve and rank literature."""
        if self.mock_mode:
            n = random.randint(8, 20)
            return [
                {
                    "pmid": f"{random.randint(10000000, 39999999)}",
                    "title": f"Mock paper on {hypothesis_text[:30]}... (#{i})",
                    "journal": random.choice(["Nature", "Science", "Cell", "PLOS ONE", "BMJ"]),
                    "year": random.randint(2015, 2024),
                    "relevance_score": round(random.uniform(0.55, 0.99), 3),
                    "cited_by": random.randint(0, 500),
                }
                for i in range(n)
            ]
        raise NotImplementedError("LiteratureAgent real implementation not wired.")

    def _data_acquisition_agent(self, hypothesis_text: str) -> List[Dict[str, Any]]:
        """Discover and acquire datasets."""
        if self.mock_mode:
            n = random.randint(1, 4)
            return [
                {
                    "accession": f"GSE{random.randint(100000, 999999)}",
                    "source": random.choice(["GEO", "TCGA", "SRA", "UKB", "FinnGen"]),
                    "samples": random.randint(50, 500),
                    "features": random.randint(1000, 50000),
                    "size_mb": random.randint(50, 5000),
                    "qc_flag": random.choice(["PASS", "PASS", "PASS", "WARN"]),
                }
                for i in range(n)
            ]
        raise NotImplementedError("DataAcquisitionAgent real implementation not wired.")

    def _knowledge_graph_agent(self, literature: List[Dict[str, Any]], datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Seed a knowledge graph from retrieved artifacts."""
        if self.mock_mode:
            nodes = [f"Gene_{i}" for i in range(random.randint(5, 15))]
            nodes += [f"Protein_{i}" for i in range(random.randint(3, 8))]
            edges = []
            for _ in range(random.randint(10, 30)):
                s, t = random.sample(nodes, 2)
                edges.append({
                    "source": s,
                    "target": t,
                    "relation": random.choice(["activates", "inhibits", "associates_with", "regulates"]),
                    "weight": round(random.uniform(0.1, 1.0), 2),
                })
            return {"nodes": nodes, "edges": edges}
        raise NotImplementedError("KnowledgeGraphAgent real implementation not wired.")

    # --------------------------------------------------------------------- #
    #  Engine interface
    # --------------------------------------------------------------------- #
    def validate(self, state: ResearchState) -> GateResult:
        """Ensure a hypothesis exists to drive retrieval."""
        errors: List[str] = []
        if not state.hypothesis or not state.hypothesis.primary:
            errors.append("Missing hypothesis; run QuestionEngine first.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.LITERATURE_SURVEY,
            messages=["RetrievalEngine validation complete."],
            errors=errors,
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Execute retrieval pipeline."""
        hypo_text = state.hypothesis.primary if state.hypothesis else ""
        literature = self._literature_agent(hypo_text)
        datasets = self._data_acquisition_agent(hypo_text)
        kg = self._knowledge_graph_agent(literature, datasets)

        state.literature = literature
        state.datasets = datasets

        # Wire KG into infrastructure if available
        if state.knowledge_graph:
            for n in kg["nodes"]:
                state.knowledge_graph.add_node(n, node_type="entity")
            for e in kg["edges"]:
                state.knowledge_graph.add_edge(e["source"], e["target"], e["relation"], e["weight"])

        # Simple QC report
        state.qc_report = {
            "literature_count": len(literature),
            "dataset_count": len(datasets),
            "avg_relevance": round(sum(p["relevance_score"] for p in literature) / max(len(literature), 1), 3),
            "qc_warnings": sum(1 for d in datasets if d["qc_flag"] == "WARN"),
            "kg_nodes": len(kg["nodes"]),
            "kg_edges": len(kg["edges"]),
        }
        state.current_stage = Stage.KNOWLEDGE_GRAPH_BUILDING
        state.touch()
        return state

    def gate(self, state: ResearchState) -> GateResult:
        """Gate check: require ≥1 dataset and ≥5 papers."""
        errors: List[str] = []
        if len(state.literature) < 5:
            errors.append(f"Insufficient literature ({len(state.literature)} < 5).")
        if len(state.datasets) == 0:
            errors.append("No datasets acquired.")
        if not state.qc_report:
            errors.append("QC report missing.")
        return GateResult(
            can_proceed=len(errors) == 0 or self.mock_mode,
            stage=Stage.KNOWLEDGE_GRAPH_BUILDING,
            messages=["RetrievalEngine gate check completed."],
            errors=errors,
        )
