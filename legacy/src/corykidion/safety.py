"""The safety gate: independent of transport, per invariant 15.

Nothing in this module talks to the network. It exists to be called *before*
client operations, so the same checks apply whether the caller is the CLI,
a future stdio MCP adapter, or a script importing this package directly. No
transport is allowed to grant itself more authority than this gate allows.

Phase 1 is read-only, so today this mostly enforces target scope. It is
written now, and tested now, so Phase 2 (bounded constructive writes) has a
gate to plug into rather than inventing one under pressure later.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from corykidion.errors import SafetyViolation


@dataclass
class SafetyGate:
    """Enforces read-only-by-default and explicit target scope.

    ``allowed_brain_ids``: if non-empty, every operation must name a
    brain_id in this set. Empty means "no scope configured" — which is
    permissive for reads today, but Phase 2 write paths should not be built
    to trust an empty scope; they should require it non-empty explicitly.
    """

    read_only: bool = True
    allowed_brain_ids: frozenset[str] = field(default_factory=frozenset)

    def assert_allowed_target(self, brain_id: str) -> None:
        if not brain_id:
            raise SafetyViolation("no target Brain ID given (invariant 4: no ambient target)")
        if self.allowed_brain_ids and brain_id not in self.allowed_brain_ids:
            raise SafetyViolation(
                f"brain_id {brain_id!r} is outside the configured target scope "
                f"{sorted(self.allowed_brain_ids)!r}"
            )

    def assert_write_allowed(self) -> None:
        """Phase 2 hook. Nothing in this codebase calls this yet — Phase 1
        performs no mutations. It's here so the write path, when it exists,
        cannot forget to check."""
        if self.read_only:
            raise SafetyViolation(
                "write attempted while the safety gate is read-only "
                "(invariant 2: read-only by default). No write capability "
                "is implemented in this version regardless."
            )
