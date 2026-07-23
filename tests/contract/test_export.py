import json
from datetime import datetime, timezone

from corykidion.client import LocalBrainClient
from corykidion.config import Config
from corykidion.export import export_thought, write_export
from corykidion.read import ReadModel

from fixtures.fake_transport import FakeTransport
from fixtures import responses as fx

BRAIN_ID = "11111111-1111-1111-1111-111111111111"
THOUGHT_ID = "33333333-3333-3333-3333-333333333333"


def fixed_clock():
    return datetime(2026, 7, 23, 12, 0, 0, tzinfo=timezone.utc)


def test_export_thought_is_deterministic_given_a_fixed_clock():
    transport = FakeTransport(
        responses={("GET", f"/thoughts/{BRAIN_ID}/{THOUGHT_ID}"): fx.THOUGHT}
    )
    config = Config(endpoint="http://localhost:52341/api", api_key="fixture-key")
    read_model = ReadModel(LocalBrainClient(config, transport=transport))

    doc_one = export_thought(read_model, BRAIN_ID, THOUGHT_ID, clock=fixed_clock)
    doc_two = export_thought(read_model, BRAIN_ID, THOUGHT_ID, clock=fixed_clock)

    assert doc_one == doc_two
    assert doc_one["generated_at"] == "2026-07-23T12:00:00+00:00"
    assert doc_one["thought"]["name"] == "Sample Thought"
    assert doc_one["provenance"]["kind"] == "read-only projection"


def test_write_export_produces_valid_sorted_json(tmp_path):
    document = {"b": 1, "a": 2, "nested": {"z": 1, "y": 2}}
    out_path = tmp_path / "nested" / "export.json"

    written_path = write_export(document, out_path)

    assert written_path == out_path
    text = out_path.read_text(encoding="utf-8")
    assert list(json.loads(text).keys()) == ["a", "b", "nested"]
    # sort_keys should also apply to nested dicts
    assert text.index('"y"') < text.index('"z"')
