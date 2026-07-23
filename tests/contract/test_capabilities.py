import pytest

from corykidion.capabilities import CapabilityRegistry
from corykidion.errors import CapabilityUnknown


def test_evidenced_capability_resolves():
    registry = CapabilityRegistry()
    info = registry.require("app.state")
    assert info.method == "GET"
    assert info.evidence == "evidence"


def test_candidate_capability_fails_closed_with_helpful_note():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityUnknown) as excinfo:
        registry.require("thought.search")
    assert "thought.search" in str(excinfo.value)
    assert "unverified" in str(excinfo.value)


def test_totally_unregistered_name_also_fails_closed():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityUnknown):
        registry.require("thought.delete_everything")


def test_known_capabilities_lists_both_tiers():
    registry = CapabilityRegistry()
    names = registry.known_capabilities()
    assert "app.state" in names
    assert "thought.search" in names
