"""
core/persistence.py
===================
Deterministic run-state persistence for the research runtime.

Serializes ``ResearchState`` to JSON so a run can be interrupted and resumed from
the last completed stage. This is pure progress bookkeeping — it introduces no
autonomous reasoning and never mutates framework code. The on-disk format is plain
JSON (human-auditable) and the only state written is the lifecycle stage + the
data containers the engines already populate.
"""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .state import EvidenceGrade, ResearchState, Stage


class StateStore:
    """Persist / restore a ``ResearchState`` as JSON (deterministic, resumable)."""

    def __init__(self, path) -> None:
        self.path = Path(path)

    def save(self, state: ResearchState) -> None:
        """Write the current state to disk (parent dirs auto-created)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._to_jsonable(state), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> Optional[ResearchState]:
        """Read a previously saved state, or ``None`` if absent / corrupt."""
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return self._from_jsonable(data)

    @staticmethod
    def _to_jsonable(state: ResearchState) -> Dict[str, Any]:
        d = asdict(state)
        # Enums serialize as their name (stable string) rather than the enum object.
        d["current_stage"] = state.current_stage.name
        d["evidence_grades"] = {k: v.name for k, v in state.evidence_grades.items()}
        # datetimes -> ISO strings (JSON-safe)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        if isinstance(d.get("updated_at"), datetime):
            d["updated_at"] = d["updated_at"].isoformat()
        return d

    @staticmethod
    def _from_jsonable(data: Dict[str, Any]) -> ResearchState:
        data = dict(data)
        data["current_stage"] = Stage[data.get("current_stage", "IDEATION")]
        eg = data.get("evidence_grades", {})
        data["evidence_grades"] = {k: EvidenceGrade[v] for k, v in eg.items()}
        # ISO strings -> datetimes
        for key in ("created_at", "updated_at"):
            if isinstance(data.get(key), str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except ValueError:
                    pass
        known = {f.name for f in fields(ResearchState)}
        return ResearchState(**{k: v for k, v in data.items() if k in known})
