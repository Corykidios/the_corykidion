"""The Phase 2 write pipeline: plan, approve, journal, apply, verify.

WORKING_ARCHITECTURE.md requires every mutating workflow to follow:

    request -> resolve target -> plan -> preview -> scoped approval
            -> journal -> apply bounded steps -> read-back verification -> receipt

This module is that pattern, applied to the three write operations this
codebase has route-level evidence for: attaching a URL, activating a
Thought, and creating a Thought (see capabilities.py — thought.create's
request *body* is explicitly unverified; see ADR 0002).

Nothing here defaults to permissive. Constructing a ``WriteOperations``
without an explicit, write-enabled ``SafetyGate`` leaves writes blocked
(invariant 2, read-only by default). Calling :meth:`WriteOperations.apply`
without ``approved=True`` raises before anything is journaled or sent
(invariant 6, scoped approval).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from corykidion.capabilities import CapabilityRegistry
from corykidion.client import LocalBrainClient
from corykidion.errors import SafetyViolation
from corykidion.safety import SafetyGate

Clock = Callable[[], datetime]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class OperationPlan:
    """A deterministic, side-effect-free description of one proposed write.

    Producing a plan never touches the network. Only :meth:`WriteOperations.apply`
    does, and only after approval.
    """

    plan_id: str
    operation: str
    brain_id: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class OperationReceipt:
    """What actually happened, per invariant 8 ("verify after mutation")."""

    plan: OperationPlan
    status: str  # "applied" or "failed"
    result: dict[str, Any] | None
    verified: bool
    verification_note: str
    error: str | None = None


class JournalWriter:
    """Append-only JSON-lines journal — one line per event, never rewritten.

    Per invariant 12 ("secrets stay local"), nothing written here includes
    the API key or endpoint; only plan/result data, which is the operator's
    own Brain content, not a credential.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]


class WriteOperations:
    def __init__(
        self,
        client: LocalBrainClient,
        journal: JournalWriter,
        safety: SafetyGate | None = None,
        capabilities: CapabilityRegistry | None = None,
        clock: Clock = _default_clock,
    ) -> None:
        self._client = client
        self._journal = journal
        # Deliberately NOT defaulting to a write-enabled gate. A caller who
        # wants writes must construct SafetyGate(read_only=False, ...)
        # themselves and hand it in explicitly.
        self._safety = safety if safety is not None else SafetyGate()
        self._capabilities = capabilities or CapabilityRegistry()
        self._clock = clock

    # -- planning (no network calls, no side effects) -------------------------

    def plan_attach_url(self, brain_id: str, thought_id: str, url: str, name: str) -> OperationPlan:
        self._capabilities.require("attachment.attach_url")
        self._safety.assert_allowed_target(brain_id)
        return OperationPlan(
            plan_id=str(uuid.uuid4()),
            operation="attachment.attach_url",
            brain_id=brain_id,
            description=f"Attach URL {url!r} (name={name!r}) to Thought {thought_id} in Brain {brain_id}",
            parameters={"thought_id": thought_id, "url": url, "name": name},
        )

    def plan_activate_thought(self, brain_id: str, thought_id: str) -> OperationPlan:
        self._capabilities.require("thought.activate")
        self._safety.assert_allowed_target(brain_id)
        return OperationPlan(
            plan_id=str(uuid.uuid4()),
            operation="thought.activate",
            brain_id=brain_id,
            description=f"Activate Thought {thought_id} in Brain {brain_id}",
            parameters={"thought_id": thought_id},
        )

    def plan_create_thought(self, brain_id: str, body: dict[str, Any]) -> OperationPlan:
        """The caller supplies the complete request body. This method does
        not add, rename, or default any field — the body schema is
        unverified (see ADR 0002), so guessing here would be exactly the
        failure mode this codebase exists to avoid."""
        self._capabilities.require("thought.create")
        self._safety.assert_allowed_target(brain_id)
        return OperationPlan(
            plan_id=str(uuid.uuid4()),
            operation="thought.create",
            brain_id=brain_id,
            description=f"Create Thought in Brain {brain_id} with body {body!r}",
            parameters={"body": body},
        )

    # -- apply (the only method that touches the network) ---------------------

    def apply(self, plan: OperationPlan, *, approved: bool) -> OperationReceipt:
        if not approved:
            raise SafetyViolation(
                f"plan {plan.plan_id} ({plan.operation}) was not approved — "
                "nothing was journaled or sent. Approval must be explicit "
                "per invariant 6 (scoped approval)."
            )
        self._safety.assert_write_allowed()

        self._journal.write(
            {
                "event": "plan_approved",
                "plan_id": plan.plan_id,
                "operation": plan.operation,
                "brain_id": plan.brain_id,
                "parameters": plan.parameters,
                "timestamp": self._clock().isoformat(),
            }
        )

        try:
            result = self._dispatch(plan)
        except Exception as exc:  # noqa: BLE001 - deliberately broad: journal, then re-surface
            self._journal.write(
                {
                    "event": "apply_failed",
                    "plan_id": plan.plan_id,
                    "error": repr(exc),
                    "timestamp": self._clock().isoformat(),
                }
            )
            return OperationReceipt(
                plan=plan,
                status="failed",
                result=None,
                verified=False,
                verification_note="apply raised before a result was produced; nothing to verify",
                error=repr(exc),
            )

        self._journal.write(
            {
                "event": "applied",
                "plan_id": plan.plan_id,
                "result": result,
                "timestamp": self._clock().isoformat(),
            }
        )

        verified, note = self._verify(plan, result)
        self._journal.write(
            {
                "event": "verified" if verified else "verification_inconclusive",
                "plan_id": plan.plan_id,
                "note": note,
                "timestamp": self._clock().isoformat(),
            }
        )
        return OperationReceipt(
            plan=plan, status="applied", result=result, verified=verified, verification_note=note
        )

    def _dispatch(self, plan: OperationPlan) -> dict[str, Any]:
        if plan.operation == "attachment.attach_url":
            p = plan.parameters
            return self._client.attach_url(plan.brain_id, p["thought_id"], p["url"], p["name"])
        if plan.operation == "thought.activate":
            p = plan.parameters
            return self._client.activate_thought(plan.brain_id, p["thought_id"])
        if plan.operation == "thought.create":
            return self._client.create_thought(plan.brain_id, plan.parameters["body"])
        raise SafetyViolation(f"no dispatcher registered for operation {plan.operation!r}")

    def _verify(self, plan: OperationPlan, result: dict[str, Any]) -> tuple[bool, str]:
        """Read-back verification per invariant 8. Returns (verified, note) —
        the note explains what was actually checked, since "verified" alone
        can overstate confidence."""
        if plan.operation == "attachment.attach_url":
            p = plan.parameters
            matches = self._client.find_attachments_by_location(plan.brain_id, p["url"])
            found = len(matches) > 0
            return found, "checked attachment.by_location for the attached URL"
        if plan.operation == "thought.activate":
            state = self._client.get_app_state()
            active_brain = (state.get("brain") or {}).get("id")
            brain_matches = active_brain == plan.brain_id
            return brain_matches, (
                "app.state confirms the target Brain is open, but app.state does not "
                "expose which Thought is active, so the specific Thought activation "
                "is not independently verifiable with currently evidenced endpoints"
            )
        if plan.operation == "thought.create":
            new_id = result.get("id") if isinstance(result, dict) else None
            if not new_id:
                return False, "create response had no 'id' field to verify against"
            try:
                self._client.get_thought(plan.brain_id, new_id)
                return True, f"read back the new Thought {new_id} via thought.get"
            except Exception as exc:  # noqa: BLE001
                return False, f"read-back of new Thought {new_id} failed: {exc!r}"
        return False, "no verification strategy registered for this operation"
