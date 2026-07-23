"""Deterministic subtree export: a projection, not a backup.

See safety invariant 14 ("projection is not authority") and invariant 13
("backups are external truth") — this module produces inspectable, typed
JSON with provenance attached. It never claims to be, or substitute for,
TheBrain's own dated whole-Brain backups.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from corykidion.models import Thought
from corykidion.read import ReadModel

SCHEMA_VERSION = 1

Clock = Callable[[], datetime]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def export_thought(
    read_model: ReadModel,
    brain_id: str,
    thought_id: str,
    *,
    clock: Clock = _default_clock,
) -> dict:
    """Build a deterministic export document for one Thought.

    Deterministic here means: same input Thought -> same document shape and
    same key ordering, with only ``generated_at`` varying. That's what makes
    the export testable and diffable, and it's why the clock is injectable.
    """
    thought = read_model.get_thought(brain_id, thought_id)
    return _document(thought, clock())


def _document(thought: Thought, generated_at: datetime) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(),
        "provenance": {
            "tool": "corykidion",
            "kind": "read-only projection",
            "note": "derived from a live read; not a backup and not canonical",
        },
        "source": {
            "brain_id": thought.brain_id,
            "thought_id": thought.id,
        },
        "thought": {
            "id": thought.id,
            "name": thought.name,
            "label": thought.label,
        },
    }


def write_export(document: dict, out_path: str | Path) -> Path:
    """Write an export document as pretty, sorted-key JSON for stable diffs."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
