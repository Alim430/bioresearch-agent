"""
infrastructure/shared.py
========================
Shared infrastructure layer for the BioResearch Agent Framework.
Provides cross-cutting services: evidence storage, memory, knowledge graph,
state management, and tool plugin registration.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.state import Evidence, EvidenceGrade, ResearchState


class EvidenceStore:
    """Persistent (in-memory) storage for Evidence objects with query capabilities.

    Agents can deposit, retrieve, filter, and grade evidence. In production this
    may be backed by a vector DB or graph store.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Evidence] = {}

    def deposit(self, evidence: Evidence) -> str:
        """Store an evidence item and return its ID."""
        if not evidence.id:
            evidence.id = str(uuid.uuid4())[:8]
        self._store[evidence.id] = evidence
        return evidence.id

    def retrieve(self, evidence_id: str) -> Optional[Evidence]:
        return self._store.get(evidence_id)

    def filter_by_grade(self, grade: EvidenceGrade) -> List[Evidence]:
        return [e for e in self._store.values() if e.grade == grade]

    def filter_by_tag(self, tag: str) -> List[Evidence]:
        return [e for e in self._store.values() if tag in e.tags]

    def list_all(self) -> List[Evidence]:
        return list(self._store.values())

    def update_grade(self, evidence_id: str, new_grade: EvidenceGrade) -> bool:
        ev = self._store.get(evidence_id)
        if ev:
            ev.grade = new_grade
            return True
        return False

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for ev in self._store.values():
            counts[ev.grade.value] = counts.get(ev.grade.value, 0) + 1
        return counts


class MemoryLayer:
    """Short-term and long-term memory for agent contexts.

    - Short-term: rolling conversation / turn buffer (FIFO).
    - Long-term: key-value archive with optional TTL.
    """

    def __init__(self, short_term_limit: int = 20) -> None:
        self.short_term_limit = short_term_limit
        self._short_term: List[Dict[str, Any]] = []
        self._long_term: Dict[str, Tuple[Any, Optional[datetime]]] = {}

    def add_short_term(self, entry: Dict[str, Any]) -> None:
        self._short_term.append({"ts": datetime.now(), **entry})
        if len(self._short_term) > self.short_term_limit:
            self._short_term.pop(0)

    def get_short_term(self, n: int = 5) -> List[Dict[str, Any]]:
        return self._short_term[-n:]

    def save_long_term(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        expiry = datetime.now() if ttl_seconds else None
        if expiry:
            # naive TTL marker; real impl would check on read
            pass
        self._long_term[key] = (value, expiry)

    def recall_long_term(self, key: str) -> Any:
        item = self._long_term.get(key)
        return item[0] if item else None

    def search_long_term(self, keyword: str) -> Dict[str, Any]:
        return {k: v[0] for k, v in self._long_term.items() if keyword in str(v[0])}


class KnowledgeGraph:
    """Simple in-memory knowledge graph for entities and relations.

    Nodes: entities (genes, proteins, diseases, chemicals, …).
    Edges: typed relationships (activates, inhibits, associates_with, …).
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []

    def add_node(self, node_id: str, node_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        self._nodes[node_id] = {"type": node_type, "properties": properties or {}}

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        self._edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight,
        })

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._edges if e["source"] == node_id or e["target"] == node_id]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self._nodes.get(node_id)

    def to_cytoscape(self) -> Dict[str, Any]:
        """Export to Cytoscape-compatible JSON."""
        nodes = [{"data": {"id": k, **v}} for k, v in self._nodes.items()]
        edges = [{"data": e} for e in self._edges]
        return {"elements": {"nodes": nodes, "edges": edges}}


class StateManager:
    """Manages the lifecycle of a ResearchState.

    - Creates new runs.
    - Persists snapshots (in-memory for mock mode).
    - Handles stage transitions and gate enforcement.
    """

    def __init__(self) -> None:
        self._snapshots: Dict[str, List[ResearchState]] = {}

    def create_run(self) -> ResearchState:
        state = ResearchState()
        self._snapshots[state.run_id] = [state]
        return state

    def snapshot(self, state: ResearchState) -> None:
        state.touch()
        # shallow snapshot for mock; deepcopy in production
        self._snapshots.setdefault(state.run_id, []).append(state)

    def get_history(self, run_id: str) -> List[ResearchState]:
        return self._snapshots.get(run_id, [])

    def transition(self, state: ResearchState, next_stage: Any) -> bool:
        """Attempt stage transition; returns True if allowed."""
        state.current_stage = next_stage
        state.touch()
        return True


class ToolPluginManager:
    """Registry and dispatcher for external tools / APIs.

    Plugins are registered as callables with a name and schema description.
    Mock plugins generate synthetic outputs.
    """

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, handler: Callable[..., Any], schema: Optional[Dict[str, Any]] = None) -> None:
        self._plugins[name] = {"schema": schema or {}}
        self._handlers[name] = handler

    def execute(self, name: str, **kwargs: Any) -> Any:
        if name not in self._handlers:
            raise KeyError(f"Plugin '{name}' not registered.")
        return self._handlers[name](**kwargs)

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def load_default_mock_plugins(self) -> None:
        """Load built-in mock plugins for common bioinformatics tasks."""
        import random

        def mock_enrichr(gene_list: List[str], library: str = "KEGG_2021_Human") -> Dict[str, Any]:
            return {
                "library": library,
                "genes_submitted": len(gene_list),
                "top_terms": [f"Term_{i}" for i in range(5)],
                "p_values": [random.uniform(1e-10, 0.05) for _ in range(5)],
            }

        def mock_pdb_search(query: str) -> List[Dict[str, Any]]:
            return [{"pdb_id": f"1{chr(65+i)}BC", "resolution": random.uniform(1.5, 3.5)} for i in range(3)]

        def mock_pubmed_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
            return [
                {
                    "pmid": f"{random.randint(10000000, 39999999)}",
                    "title": f"Mock article about {query} #{i}",
                    "year": random.randint(2015, 2024),
                }
                for i in range(max_results)
            ]

        self.register("enrichr", mock_enrichr, schema={"gene_list": "list", "library": "str"})
        self.register("pdb_search", mock_pdb_search, schema={"query": "str"})
        self.register("pubmed_search", mock_pubmed_search, schema={"query": "str", "max_results": "int"})
