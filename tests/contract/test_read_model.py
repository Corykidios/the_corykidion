import pytest

from corykidion.client import LocalBrainClient
from corykidion.config import Config
from corykidion.errors import CapabilityUnknown, SafetyViolation
from corykidion.read import ReadModel
from corykidion.safety import SafetyGate

from fixtures.fake_transport import FakeTransport
from fixtures import responses as fx

BRAIN_ID = "11111111-1111-1111-1111-111111111111"
THOUGHT_ID = "33333333-3333-3333-3333-333333333333"


def make_read_model(transport, safety=None):
    config = Config(endpoint="http://localhost:52341/api", api_key="fixture-key")
    client = LocalBrainClient(config, transport=transport)
    return ReadModel(client, safety=safety)


def test_connectivity_reports_running_state_and_brains():
    transport = FakeTransport(
        responses={
            ("GET", "/app/state"): fx.APP_STATE_RUNNING,
            ("GET", "/brains"): fx.BRAINS_LIST,
        }
    )
    read_model = make_read_model(transport)

    status = read_model.connectivity()

    assert status.app_running is True
    assert status.active_brain_id == BRAIN_ID
    assert status.brain_count == 2


def test_get_thought_returns_normalized_model():
    transport = FakeTransport(
        responses={("GET", f"/thoughts/{BRAIN_ID}/{THOUGHT_ID}"): fx.THOUGHT}
    )
    read_model = make_read_model(transport)

    thought = read_model.get_thought(BRAIN_ID, THOUGHT_ID)

    assert thought.id == THOUGHT_ID
    assert thought.name == "Sample Thought"


def test_get_thought_respects_target_scope():
    transport = FakeTransport(
        responses={("GET", f"/thoughts/{BRAIN_ID}/{THOUGHT_ID}"): fx.THOUGHT}
    )
    safety = SafetyGate(allowed_brain_ids=frozenset({"some-other-brain"}))
    read_model = make_read_model(transport, safety=safety)

    with pytest.raises(SafetyViolation):
        read_model.get_thought(BRAIN_ID, THOUGHT_ID)


def test_find_existing_url_wraps_attachment_lookup():
    transport = FakeTransport(
        responses={
            ("GET", f"/attachments/{BRAIN_ID}/by-location"): fx.ATTACHMENTS_BY_LOCATION_FOUND
        }
    )
    read_model = make_read_model(transport)

    matches = read_model.find_existing_url(BRAIN_ID, "https://example.invalid/fixture-page")

    assert len(matches) == 1
    assert matches[0].thought_id == THOUGHT_ID


def test_known_capabilities_splits_evidenced_and_candidate():
    transport = FakeTransport()
    read_model = make_read_model(transport)

    caps = read_model.known_capabilities()

    assert "app.state" in caps["evidenced"]
    assert "thought.search" in caps["candidate"]


def test_unsupported_operation_would_fail_closed():
    # There is no public ReadModel method for search yet — this test
    # documents the underlying mechanism directly, so the intent is visible
    # even though no code path currently calls it.
    transport = FakeTransport()
    read_model = make_read_model(transport)
    with pytest.raises(CapabilityUnknown):
        read_model._capabilities.require("thought.search")
