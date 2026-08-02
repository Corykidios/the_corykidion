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
    mutates: bool = False


# Verified against docs/README for TheBrainTech/send-to-thebrain (repo #14
# in WORKING_ARCHITECTURE.md's donor ledger), the official reference
# implementation for the local API.
_SEND_TO_THEBRAIN = "TheBrainTech/send-to-thebrain README, 'Endpoints used' table"

# Verified 2026-07-23 by direct GET requests against a running local API
# instance (see docs/decisions/0002-live-verified-read-capabilities.md).
# Response shapes were captured and turned into fabricated fixtures under
# tests/fixtures/ — no real Brain content is stored in this repository.
_LIVE_VERIFIED_READ = "observed directly against a running local API instance, 2026-07-23"

EVIDENCED_CAPABILITIES: dict[str, CapabilityInfo] = {
    "app.state": CapabilityInfo(
        name="app.state",
        method="GET",
        path_template="/app/state",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
    ),
    "brains.list": CapabilityInfo(
        name="brains.list",
        method="GET",
        path_template="/brains",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
    ),
    "thought.get": CapabilityInfo(
        name="thought.get",
        method="GET",
        path_template="/thoughts/{brain_id}/{thought_id}",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
    ),
    "attachment.by_location": CapabilityInfo(
        name="attachment.by_location",
        method="GET",
        path_template="/attachments/{brain_id}/by-location",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
    ),
    "thought.search": CapabilityInfo(
        name="thought.search",
        method="GET",
        path_template="/search/{brain_id}",
        evidence="evidence",
        source=_LIVE_VERIFIED_READ,
    ),
    "thought.graph": CapabilityInfo(
        name="thought.graph",
        method="GET",
        path_template="/thoughts/{brain_id}/{thought_id}/graph",
        evidence="evidence",
        source=_LIVE_VERIFIED_READ,
    ),
    "thought.notes": CapabilityInfo(
        name="thought.notes",
        method="GET",
        path_template="/notes/{brain_id}/{thought_id}",
        evidence="evidence",
        source=_LIVE_VERIFIED_READ,
    ),
    "activity.recent": CapabilityInfo(
        name="activity.recent",
        method="GET",
        path_template="/brains/{brain_id}/modifications",
        evidence="evidence",
        source=_LIVE_VERIFIED_READ,
    ),
    # Path and method are documented by send-to-thebrain's own working
    # implementation, so the *route* is evidence-grade. The request body
    # schema for thought.create is not: an attempt to verify it by sending
    # an intentionally invalid body (to trigger a 400 validation error
    # without side effects, the same technique that worked for the read
    # endpoints' query parameters) was blocked before execution, correctly,
    # as an unreviewed write against a live personal Brain. See ADR 0002.
    # This capability is registered as evidence for routing purposes but
    # its write pipeline (operations.py) treats the body as unverified and
    # requires the caller to supply every field explicitly.
    "thought.create": CapabilityInfo(
        name="thought.create",
        method="POST",
        path_template="/thoughts/{brain_id}",
        evidence="evidence (route only — request body unverified)",
        source=_SEND_TO_THEBRAIN,
        mutates=True,
    ),
    "attachment.attach_url": CapabilityInfo(
        name="attachment.attach_url",
        method="POST",
        path_template="/attachments/{brain_id}/{thought_id}/url",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
        mutates=True,
    ),
    "thought.activate": CapabilityInfo(
        name="thought.activate",
        method="POST",
        path_template="/app/brain/{brain_id}/thought/{thought_id}/activate",
        evidence="evidence",
        source=_SEND_TO_THEBRAIN,
        mutates=True,
    ),
}

# Plausible or partially explored, but not implemented: either no source
# available to this codebase has a verified shape, or verifying the shape
# would require a write this codebase declines to make without explicit,
# per-call operator authorization (see ADR 0002).
CANDIDATE_CAPABILITIES: dict[str, str] = {
    "thought.links": "superseded — use thought.graph, whose 'links' array covers this",
    "thought.neighbors": "superseded — use thought.graph, whose parents/children/jumps cover this",
    "note.append": (
        "write; no verified request shape. Probing it live (an intentionally "
        "invalid PUT/POST to trigger a 400 without a real write) was not "
        "attempted after thought.create's probe was blocked by policy — see ADR 0002"
    ),
    "link.create": (
        "write; OPTIONS /links/{brain_id} returns 200 so a route exists, but "
        "the method and body are unverified — same reasoning as note.append"
    ),
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
