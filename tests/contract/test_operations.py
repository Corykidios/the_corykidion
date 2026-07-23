from datetime import datetime, timezone

import pytest

from corykidion.client import LocalBrainClient
from corykidion.config import Config
from corykidion.errors import SafetyViolation
from corykidion.operations import JournalWriter, WriteOperations
from corykidion.safety import SafetyGate

from fixtures.fake_transport import FakeTransport
from fixtures import responses as fx

BRAIN_ID = "11111111-1111-1111-1111-111111111111"
THOUGHT_ID = "33333333-3333-3333-3333-333333333333"


def fixed_clock():
    return datetime(2026, 7, 23, 12, 0, 0, tzinfo=timezone.utc)


def make_client(transport):
    config = Config(endpoint="http://localhost:52341/api", api_key="fixture-key")
    return LocalBrainClient(config, transport=transport)


def make_ops(transport, journal_path, safety=None):
    client = make_client(transport)
    journal = JournalWriter(journal_path)
    return WriteOperations(client, journal, safety=safety, clock=fixed_clock)


# -- planning is always side-effect-free -----------------------------------


def test_planning_does_not_call_the_network():
    transport = FakeTransport()
    ops = make_ops(transport, "unused.jsonl")

    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")

    assert transport.calls == []
    assert plan.operation == "attachment.attach_url"
    assert plan.brain_id == BRAIN_ID


def test_planning_respects_target_scope_even_though_it_is_read_only():
    transport = FakeTransport()
    safety = SafetyGate(allowed_brain_ids=frozenset({"some-other-brain"}))
    ops = make_ops(transport, "unused.jsonl", safety=safety)

    with pytest.raises(SafetyViolation):
        ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")


# -- apply() requires explicit approval and a write-enabled gate ------------


def test_apply_without_approval_raises_and_touches_nothing(tmp_path):
    transport = FakeTransport()
    journal_path = tmp_path / "journal.jsonl"
    ops = make_ops(transport, journal_path)
    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")

    with pytest.raises(SafetyViolation):
        ops.apply(plan, approved=False)

    assert transport.calls == []
    assert not journal_path.exists()


def test_apply_with_default_read_only_gate_refuses_even_if_approved(tmp_path):
    transport = FakeTransport()
    journal_path = tmp_path / "journal.jsonl"
    # No safety gate passed in -> defaults to SafetyGate() -> read_only=True.
    ops = make_ops(transport, journal_path)
    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")

    with pytest.raises(SafetyViolation):
        ops.apply(plan, approved=True)

    assert transport.calls == []


# -- successful apply + verify, per operation --------------------------------


def test_attach_url_apply_journals_and_verifies(tmp_path):
    transport = FakeTransport(
        responses={
            ("POST", f"/attachments/{BRAIN_ID}/{THOUGHT_ID}/url"): fx.ATTACH_URL_RESULT,
            (
                "GET",
                f"/attachments/{BRAIN_ID}/by-location",
            ): fx.ATTACHMENTS_BY_LOCATION_FOUND,
        }
    )
    journal_path = tmp_path / "journal.jsonl"
    safety = SafetyGate(read_only=False)
    ops = make_ops(transport, journal_path, safety=safety)
    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/fixture-page", "Example")

    receipt = ops.apply(plan, approved=True)

    assert receipt.status == "applied"
    assert receipt.verified is True
    assert receipt.result == fx.ATTACH_URL_RESULT

    events = JournalWriter(journal_path).read_all()
    event_names = [e["event"] for e in events]
    assert event_names == ["plan_approved", "applied", "verified"]
    assert all(e["plan_id"] == plan.plan_id for e in events)


def test_attach_url_apply_reports_unverified_when_readback_finds_nothing(tmp_path):
    transport = FakeTransport(
        responses={
            ("POST", f"/attachments/{BRAIN_ID}/{THOUGHT_ID}/url"): fx.ATTACH_URL_RESULT,
            ("GET", f"/attachments/{BRAIN_ID}/by-location"): fx.ATTACHMENTS_BY_LOCATION_EMPTY,
        }
    )
    journal_path = tmp_path / "journal.jsonl"
    ops = make_ops(transport, journal_path, safety=SafetyGate(read_only=False))
    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")

    receipt = ops.apply(plan, approved=True)

    assert receipt.status == "applied"
    assert receipt.verified is False
    events = JournalWriter(journal_path).read_all()
    assert events[-1]["event"] == "verification_inconclusive"


def test_activate_apply_verifies_brain_but_notes_thought_level_limit(tmp_path):
    transport = FakeTransport(
        responses={
            ("POST", f"/app/brain/{BRAIN_ID}/thought/{THOUGHT_ID}/activate"): {},
            ("GET", "/app/state"): fx.APP_STATE_RUNNING,
        }
    )
    journal_path = tmp_path / "journal.jsonl"
    ops = make_ops(transport, journal_path, safety=SafetyGate(read_only=False))
    plan = ops.plan_activate_thought(BRAIN_ID, THOUGHT_ID)

    receipt = ops.apply(plan, approved=True)

    assert receipt.status == "applied"
    assert receipt.verified is True
    assert "not independently verifiable" in receipt.verification_note


def test_create_thought_apply_reads_back_the_new_thought(tmp_path):
    new_id = fx.CREATE_THOUGHT_RESULT["id"]
    transport = FakeTransport(
        responses={
            ("POST", f"/thoughts/{BRAIN_ID}"): fx.CREATE_THOUGHT_RESULT,
            ("GET", f"/thoughts/{BRAIN_ID}/{new_id}"): {"id": new_id, "name": "Fixture Thought"},
        }
    )
    journal_path = tmp_path / "journal.jsonl"
    ops = make_ops(transport, journal_path, safety=SafetyGate(read_only=False))
    plan = ops.plan_create_thought(BRAIN_ID, {"name": "Fixture Thought"})

    receipt = ops.apply(plan, approved=True)

    assert receipt.status == "applied"
    assert receipt.verified is True
    assert receipt.result["id"] == new_id


def test_apply_failure_is_journaled_and_surfaced_in_the_receipt(tmp_path):
    transport = FakeTransport(
        responses={("POST", f"/attachments/{BRAIN_ID}/{THOUGHT_ID}/url"): {"error": "boom"}},
        status_overrides={("POST", f"/attachments/{BRAIN_ID}/{THOUGHT_ID}/url"): 500},
    )
    journal_path = tmp_path / "journal.jsonl"
    ops = make_ops(transport, journal_path, safety=SafetyGate(read_only=False))
    plan = ops.plan_attach_url(BRAIN_ID, THOUGHT_ID, "https://example.invalid/x", "Example")

    receipt = ops.apply(plan, approved=True)

    assert receipt.status == "failed"
    assert receipt.verified is False
    assert receipt.error is not None
    events = JournalWriter(journal_path).read_all()
    assert events[-1]["event"] == "apply_failed"
