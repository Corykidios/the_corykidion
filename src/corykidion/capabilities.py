"""The capability registry: corykidion's fail-closed contract with reality.

WORKING_ARCHITECTURE.md draws a hard line between what has been *observed*
against a real, documented local-API response (maturity: evidence) and what
is merely *plausible* because the cloud API at api.bra.in is known to expose
it and TheBrain's own announcement states the local API "speaks the same
shape" (maturity: candidate).

This module is where that distinction becomes executable. Every operation
the client can perform is registered here with its evidence source. Calling
an operation that isn't registered as evidenced raises
:class:`corykidion.errors.CapabilityUnknown` instead of silently guessing at
an endpoint shape — see safety invariant 3 ("Supported API before private
storage") and the donor-repository note on repo #6, whose described
implementation was absent from its own source.

To promote a candidate to evidenced: verify it against a running local
API response, add a fixture under tests/fixtures/, add a contract test, and
move its entry from CANDIDATE_CAPABILITIES to EVIDENCED_CAPABILITIES with a
comment noting how it was verified and on what TheBrain version.
"""

from __future__ import annotations

from dataclasses import dataclass

from corykidion.errors import CapabilityUnknown


@dataclass(frozen=True)
class CapabilityInfo:
    name: str
    method: str
    path_template: str
    evidence: str
    source: str


# Verified against docs/README for TheBrainTech/send-to-thebrain (repo #14
# in WORKING_ARCHITECTURE.md's donor ledger), the official reference
# implementation for the local API.
EVIDENCED_CAPABILITIES: dict[str, CapabilityInfo] = {
    "app.state": CapabilityInfo(
        name="app.state",
        method="GET",
        path_template="/app/state",
        evidence="evidence",
        source="TheBrainTech/send-to-thebrain README, 'Endpoints used' table",
    ),
    "brains.list": CapabilityInfo(
        name="brains.list",
        method="GET",
        path_template="/brains",
        evidence="evidence",
        source="TheBrainTech/send-to-thebrain README, 'Endpoints used' table",
    ),
    "thought.get": CapabilityInfo(
        name="thought.get",
        method="GET",
        path_template="/thoughts/{brain_id}/{thought_id}",
        evidence="evidence",
        source="TheBrainTech/send-to-thebrain README, 'Endpoints used' table",
    ),
    "attachment.by_location": CapabilityInfo(
        name="attachment.by_location",
        method="GET",
        path_template="/attachments/{brain_id}/by-location",
        evidence="evidence",
        source="TheBrainTech/send-to-thebrain README, 'Endpoints used' table",
    ),
}

# Plausible because the local API is documented to mirror the cloud API's
# shape (see TheBrain's "TheBrain API: Now Fully Local and Unrestrained"
# blog post) and several donor repos exercise equivalents against
# api.bra.in. Not independently verified by this package against a running
# local instance, so calling these raises CapabilityUnknown until promoted.
CANDIDATE_CAPABILITIES: dict[str, str] = {
    "thought.search": "search Thoughts by name/label; shape unverified locally",
    "thought.notes": "note content read/write; shape unverified locally",
    "thought.links": "outbound/inbound link enumeration; shape unverified locally",
    "thought.neighbors": "bounded neighbor traversal; shape unverified locally",
    "activity.recent": "recent modifications/activity feed; shape unverified locally",
    "thought.create": "Phase 2 (bounded constructive writes); not attempted yet",
    "attachment.attach_url": "Phase 2 (bounded constructive writes); not attempted yet",
    "thought.activate": "Phase 2 (bounded constructive writes); not attempted yet",
}


class CapabilityRegistry:
    """Looks up capabilities and enforces the fail-closed boundary."""

    def __init__(
        self,
        evidenced: dict[str, CapabilityInfo] | None = None,
        candidates: dict[str, str] | None = None,
    ) -> None:
        self._evidenced = dict(EVIDENCED_CAPABILITIES if evidenced is None else evidenced)
        self._candidates = dict(CANDIDATE_CAPABILITIES if candidates is None else candidates)

    def require(self, name: str) -> CapabilityInfo:
        """Return the evidenced capability, or raise CapabilityUnknown."""
        info = self._evidenced.get(name)
        if info is not None:
            return info
        note = self._candidates.get(name, "not registered at all")
        raise CapabilityUnknown(name, note=note)

    def is_evidenced(self, name: str) -> bool:
        return name in self._evidenced

    def known_capabilities(self) -> list[str]:
        return sorted(self._evidenced) + sorted(self._candidates)
