import pytest

from corykidion.capabilities import CapabilityRegistry
from corykidion.errors import CapabilityUnknown


def test_evidenced_capability_resolves():
    registry = CapabilityRegistry()
    info = registry.require("app.state")
    assert info.method == "GET"
    assert info.evidence == "evidence"


def test_live_verified_read_capabilities_resolve():
    registry = CapabilityRegistry()
    for name in ("thought.search", "thought.graph", "thought.notes", "activity.recent"):
        info = registry.require(name)
        assert info.method == "GET"
        assert "2026-07-23" in info.source


def test_write_capabilities_resolve_and_are_flagged_as_mutating():
    registry = CapabilityRegistry()
    for name in ("thought.create", "attachment.attach_url", "thought.activate"):
        info = registry.require(name)
        assert info.method == "POST"
        assert info.mutates is True


def test_superseded_neighbor_capability_fails_closed_and_points_to_graph():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityUnknown) as excinfo:
        registry.require("thought.neighbors")
    assert "thought.graph" in str(excinfo.value)


def test_unverified_write_capability_fails_closed_with_helpful_note():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityUnknown) as excinfo:
        registry.require("note.append")
    assert "note.append" in str(excinfo.value)
    assert "no verified request shape" in str(excinfo.value)


def test_totally_unregistered_name_also_fails_closed():
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityUnknown):
        registry.require("thought.delete_everything")


def test_known_capabilities_lists_both_tiers():
    registry = CapabilityRegistry()
    names = registry.known_capabilities()
    assert "app.state" in names
    assert "thought.search" in names
    assert "note.append" in names
