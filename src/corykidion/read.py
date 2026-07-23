"""The read model: compact, agent-useful reads over the evidenced client.

This is the layer an agent (or a human at the CLI) actually talks to. It
composes LocalBrainClient calls with the safety gate and the capability
registry so callers get one coherent surface instead of juggling three
objects, and so every read passes through the same target-scope check.
"""

from __future__ import annotations

from dataclasses import dataclass

from corykidion.capabilities import CapabilityRegistry
from corykidion.client import LocalBrainClient
from corykidion.models import AppState, Attachment, Brain, Thought
from corykidion.safety import SafetyGate


@dataclass(frozen=True)
class ConnectivityStatus:
    """Result of :meth:`ReadModel.connectivity`."""

    app_running: bool
    active_brain_id: str | None
    brain_count: int
    brains: tuple[Brain, ...]


class ReadModel:
    def __init__(
        self,
        client: LocalBrainClient,
        safety: SafetyGate | None = None,
        capabilities: CapabilityRegistry | None = None,
    ) -> None:
        self._client = client
        self._safety = safety or SafetyGate()
        self._capabilities = capabilities or CapabilityRegistry()

    def connectivity(self) -> ConnectivityStatus:
        """Confirm the app is running and report what brains are visible.

        This is deliberately the first thing any caller should run — it
        matches the four failure cases send-to-thebrain surfaces explicitly:
        app not running, bad key, no brain open, brain read-only. We don't
        yet distinguish all four (that needs thought.get's error body shape
        verified first), but connectivity() gives a caller enough to stop
        and ask a human before doing anything else.
        """
        self._capabilities.require("app.state")
        self._capabilities.require("brains.list")
        state_raw = self._client.get_app_state()
        state = AppState.from_json(state_raw)
        brains_raw = self._client.list_brains()
        brains = tuple(Brain.from_json(b) for b in brains_raw)
        return ConnectivityStatus(
            app_running=state.is_running,
            active_brain_id=state.active_brain_id,
            brain_count=len(brains),
            brains=brains,
        )

    def get_thought(self, brain_id: str, thought_id: str) -> Thought:
        """Retrieve one Thought by ID. See invariant 4: the target is always explicit."""
        self._capabilities.require("thought.get")
        self._safety.assert_allowed_target(brain_id)
        raw = self._client.get_thought(brain_id, thought_id)
        return Thought.from_json(brain_id, raw)

    def find_existing_url(self, brain_id: str, url: str) -> list[Attachment]:
        """Dedup helper: does this URL already exist as an attachment anywhere in the brain?

        Mirrors the pattern send-to-thebrain uses to avoid creating duplicate
        thoughts for a URL that's already there — see donor repo #14.
        """
        self._capabilities.require("attachment.by_location")
        self._safety.assert_allowed_target(brain_id)
        raw = self._client.find_attachments_by_location(brain_id, url)
        return [Attachment.from_json(a) for a in raw]

    def known_capabilities(self) -> dict[str, list[str]]:
        """What this ReadModel can and can't do right now, for introspection
        by a caller (human or agent) deciding what to attempt."""
        names = self._capabilities.known_capabilities()
        evidenced = [n for n in names if self._capabilities.is_evidenced(n)]
        candidate = [n for n in names if n not in evidenced]
        return {"evidenced": evidenced, "candidate": candidate}
