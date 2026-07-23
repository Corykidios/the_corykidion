import pytest

from corykidion.safety import SafetyGate
from corykidion.errors import SafetyViolation


def test_no_scope_configured_allows_any_target():
    gate = SafetyGate()
    gate.assert_allowed_target("any-brain-id")  # should not raise


def test_empty_brain_id_always_rejected():
    gate = SafetyGate()
    with pytest.raises(SafetyViolation):
        gate.assert_allowed_target("")


def test_scoped_gate_allows_listed_brain():
    gate = SafetyGate(allowed_brain_ids=frozenset({"a", "b"}))
    gate.assert_allowed_target("a")  # should not raise


def test_scoped_gate_rejects_unlisted_brain():
    gate = SafetyGate(allowed_brain_ids=frozenset({"a", "b"}))
    with pytest.raises(SafetyViolation):
        gate.assert_allowed_target("c")


def test_read_only_default_blocks_write_hook():
    gate = SafetyGate()
    with pytest.raises(SafetyViolation):
        gate.assert_write_allowed()


def test_read_only_false_still_has_no_implemented_writes():
    # Setting read_only=False only clears this one check. There is no write
    # path in this version of the client regardless — this test documents
    # that the gate change alone does not grant new capability.
    gate = SafetyGate(read_only=False)
    gate.assert_write_allowed()  # should not raise
