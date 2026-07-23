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
    """One entry from ``GET /attachments/{brainId}/by-location``, or one
    entry of the ``attachments`` list embedded in a ThoughtGraph response."""

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


@dataclass(frozen=True)
class Link:
    """One entry from the ``links`` array of a ThoughtGraph response.

    Verified 2026-07-23 against a running local API instance (see
    docs/decisions/0002-live-verified-read-capabilities.md). ``relation``,
    ``direction``, and ``meaning`` are TheBrain's internal link-type
    integers; this package does not yet interpret them beyond passing them
    through, since no documented mapping was available to verify against.
    """

    id: str
    brain_id: str
    thought_id_a: str
    thought_id_b: str
    relation: int | None
    direction: int | None
    meaning: int | None
    name: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Link":
        return cls(
            id=str(data.get("id", "")),
            brain_id=str(data.get("brainId", "")),
            thought_id_a=str(data.get("thoughtIdA", "")),
            thought_id_b=str(data.get("thoughtIdB", "")),
            relation=data.get("relation"),
            direction=data.get("direction"),
            meaning=data.get("meaning"),
            name=data.get("name"),
            raw=data,
        )


@dataclass(frozen=True)
class ThoughtGraph:
    """Response shape of ``GET /thoughts/{brainId}/{thoughtId}/graph``.

    This single endpoint covers what the design ledger originally split
    into three separate aspirations (compound Thought context, bounded
    neighbor exploration, and link enumeration) — TheBrain's own link model
    is parent/child/jump, so "links" and "neighbors" are the same data
    viewed two ways, not two endpoints. See ADR 0002.
    """

    active_thought: Thought
    parents: tuple[Thought, ...]
    children: tuple[Thought, ...]
    jumps: tuple[Thought, ...]
    links: tuple[Link, ...]
    attachments: tuple[Attachment, ...]
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, brain_id: str, data: dict[str, Any]) -> "ThoughtGraph":
        def thoughts(key: str) -> tuple[Thought, ...]:
            return tuple(Thought.from_json(brain_id, t) for t in (data.get(key) or []))

        return cls(
            active_thought=Thought.from_json(brain_id, data.get("activeThought") or {}),
            parents=thoughts("parents"),
            children=thoughts("children"),
            jumps=thoughts("jumps"),
            links=tuple(Link.from_json(link) for link in (data.get("links") or [])),
            attachments=tuple(
                Attachment.from_json(a) for a in (data.get("attachments") or [])
            ),
            raw=data,
        )


@dataclass(frozen=True)
class Note:
    """Response shape of ``GET /notes/{brainId}/{thoughtId}``.

    Verified 2026-07-23 against a running local API instance. An empty
    Thought note comes back as ``markdown=""``, not a 404 — there is no
    distinct "no note" state to detect separately from "empty note".
    """

    brain_id: str
    thought_id: str
    markdown: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Note":
        return cls(
            brain_id=str(data.get("brainId", "")),
            thought_id=str(data.get("sourceId", "")),
            markdown=str(data.get("markdown") or ""),
            raw=data,
        )


@dataclass(frozen=True)
class SearchResult:
    """One entry from ``GET /search/{brainId}?queryText=...``."""

    thought: Thought
    name: str
    is_from_other_brain: bool
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, brain_id: str, data: dict[str, Any]) -> "SearchResult":
        return cls(
            thought=Thought.from_json(brain_id, data.get("sourceThought") or {}),
            name=str(data.get("name", "")),
            is_from_other_brain=bool(data.get("isFromOtherBrain", False)),
            raw=data,
        )


@dataclass(frozen=True)
class ModificationEntry:
    """One entry from ``GET /brains/{brainId}/modifications?maxLogs=...``.

    ``mod_type`` is an internal TheBrain integer code (e.g. 301 observed for
    a Thought-related change); no documented mapping was available to
    verify a human-readable translation against, so it is passed through
    as-is rather than guessed at.
    """

    brain_id: str
    source_id: str
    source_type: int | None
    mod_type: int | None
    creation_datetime: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ModificationEntry":
        return cls(
            brain_id=str(data.get("brainId", "")),
            source_id=str(data.get("sourceId", "")),
            source_type=data.get("sourceType"),
            mod_type=data.get("modType"),
            creation_datetime=data.get("creationDateTime"),
            raw=data,
        )
