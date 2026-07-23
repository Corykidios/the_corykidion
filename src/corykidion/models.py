"""Normalized internal types.

These are deliberately small and tolerant. TheBrain's API returns richer
objects than we model here; each type keeps ``raw`` around so callers who
need a field we haven't promoted yet can still get at it, without the
client having to guess at a full schema it hasn't verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppState:
    """Response shape of ``GET /app/state``."""

    is_running: bool
    active_brain_id: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "AppState":
        brain = data.get("brain") or {}
        active_id = brain.get("id") if isinstance(brain, dict) else data.get("brainId")
        return cls(is_running=True, active_brain_id=active_id, raw=data)


@dataclass(frozen=True)
class Brain:
    """One entry from ``GET /brains``."""

    id: str
    name: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Brain":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            raw=data,
        )


@dataclass(frozen=True)
class Thought:
    """Response shape of ``GET /thoughts/{brainId}/{thoughtId}``.

    TheBrain's full Thought object carries many more fields (kind, color,
    ACType, foreground color, and so on) than are promoted here. Anything
    not modeled explicitly is still reachable through ``raw``.
    """

    id: str
    brain_id: str
    name: str
    label: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, brain_id: str, data: dict[str, Any]) -> "Thought":
        return cls(
            id=str(data.get("id", "")),
            brain_id=brain_id,
            name=str(data.get("name", "")),
            label=data.get("label"),
            raw=data,
        )


@dataclass(frozen=True)
class Attachment:
    """One entry from ``GET /attachments/{brainId}/by-location``."""

    id: str
    thought_id: str
    location: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Attachment":
        return cls(
            id=str(data.get("id", "")),
            thought_id=str(data.get("thoughtId", data.get("sourceThoughtId", ""))),
            location=str(data.get("location", "")),
            raw=data,
        )
