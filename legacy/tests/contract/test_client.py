import pytest

from corykidion.config import Config
from corykidion.errors import AuthenticationError, ConnectionRefused, UpstreamError
from corykidion.client import LocalBrainClient

from fixtures.fake_transport import FakeTransport
from fixtures import responses as fx


def make_config(**overrides):
    kwargs = dict(endpoint="http://localhost:52341/api", api_key="fixture-key")
    kwargs.update(overrides)
    return Config(**kwargs)


def test_get_app_state_parses_response():
    transport = FakeTransport(responses={("GET", "/app/state"): fx.APP_STATE_RUNNING})
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.get_app_state()

    assert result == fx.APP_STATE_RUNNING
    assert transport.calls[0][0] == "GET"
    assert transport.calls[0][2]["Authorization"] == "Bearer fixture-key"


def test_list_brains_unwraps_envelope():
    transport = FakeTransport(responses={("GET", "/brains"): fx.BRAINS_LIST})
    client = LocalBrainClient(make_config(), transport=transport)

    brains = client.list_brains()

    assert brains == fx.BRAINS_LIST["brains"]


def test_get_thought_builds_correct_path():
    transport = FakeTransport(
        responses={
            (
                "GET",
                "/thoughts/11111111-1111-1111-1111-111111111111/33333333-3333-3333-3333-333333333333",
            ): fx.THOUGHT
        }
    )
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.get_thought(
        "11111111-1111-1111-1111-111111111111", "33333333-3333-3333-3333-333333333333"
    )

    assert result == fx.THOUGHT


def test_find_attachments_by_location_sends_query_params():
    transport = FakeTransport(
        responses={
            ("GET", "/attachments/11111111-1111-1111-1111-111111111111/by-location"): fx.ATTACHMENTS_BY_LOCATION_FOUND
        }
    )
    client = LocalBrainClient(make_config(), transport=transport)

    attachments = client.find_attachments_by_location(
        "11111111-1111-1111-1111-111111111111", "https://example.invalid/fixture-page"
    )

    assert attachments == fx.ATTACHMENTS_BY_LOCATION_FOUND["attachments"]
    called_url = transport.calls[0][1]
    assert "location=" in called_url
    assert "type=3" in called_url


def test_401_raises_authentication_error():
    transport = FakeTransport(
        responses={("GET", "/app/state"): {}},
        status_overrides={("GET", "/app/state"): 401},
    )
    client = LocalBrainClient(make_config(), transport=transport)

    with pytest.raises(AuthenticationError):
        client.get_app_state()


def test_500_raises_upstream_error():
    transport = FakeTransport(
        responses={("GET", "/app/state"): {"error": "boom"}},
        status_overrides={("GET", "/app/state"): 500},
    )
    client = LocalBrainClient(make_config(), transport=transport)

    with pytest.raises(UpstreamError) as excinfo:
        client.get_app_state()
    assert excinfo.value.status == 500


def test_connection_error_becomes_connection_refused():
    def broken_transport(method, url, headers, body):
        raise ConnectionRefused("simulated: app not running")

    client = LocalBrainClient(make_config(), transport=broken_transport)

    with pytest.raises(ConnectionRefused):
        client.get_app_state()


BRAIN = "11111111-1111-1111-1111-111111111111"
THOUGHT_ID = "33333333-3333-3333-3333-333333333333"


def test_search_sends_query_text_and_max_results():
    transport = FakeTransport(responses={("GET", f"/search/{BRAIN}"): fx.SEARCH_RESULTS})
    client = LocalBrainClient(make_config(), transport=transport)

    results = client.search(BRAIN, "fixture", max_results=5)

    assert results == fx.SEARCH_RESULTS
    called_url = transport.calls[0][1]
    assert "queryText=fixture" in called_url
    assert "maxResults=5" in called_url


def test_search_returns_empty_list_for_no_matches():
    transport = FakeTransport(responses={("GET", f"/search/{BRAIN}"): fx.SEARCH_RESULTS_EMPTY})
    client = LocalBrainClient(make_config(), transport=transport)

    assert client.search(BRAIN, "nothing") == []


def test_get_graph_builds_correct_path():
    transport = FakeTransport(
        responses={("GET", f"/thoughts/{BRAIN}/{THOUGHT_ID}/graph"): fx.THOUGHT_GRAPH}
    )
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.get_graph(BRAIN, THOUGHT_ID)

    assert result == fx.THOUGHT_GRAPH


def test_get_notes_builds_correct_path():
    transport = FakeTransport(responses={("GET", f"/notes/{BRAIN}/{THOUGHT_ID}"): fx.NOTE_EMPTY})
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.get_notes(BRAIN, THOUGHT_ID)

    assert result == fx.NOTE_EMPTY


def test_get_modifications_sends_max_logs():
    transport = FakeTransport(
        responses={("GET", f"/brains/{BRAIN}/modifications"): fx.MODIFICATIONS}
    )
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.get_modifications(BRAIN, max_logs=7)

    assert result == fx.MODIFICATIONS
    assert "maxLogs=7" in transport.calls[0][1]


def test_attach_url_is_a_post_with_query_params():
    transport = FakeTransport(
        responses={
            ("POST", f"/attachments/{BRAIN}/{THOUGHT_ID}/url"): fx.ATTACH_URL_RESULT
        }
    )
    client = LocalBrainClient(make_config(), transport=transport)

    result = client.attach_url(BRAIN, THOUGHT_ID, "https://example.invalid/x", "Example")

    assert result == fx.ATTACH_URL_RESULT
    method, url, headers = transport.calls[0]
    assert method == "POST"
    assert "url=" in url
    assert "name=Example" in url


def test_activate_thought_is_a_post_with_no_body():
    transport = FakeTransport(
        responses={("POST", f"/app/brain/{BRAIN}/thought/{THOUGHT_ID}/activate"): {}}
    )
    client = LocalBrainClient(make_config(), transport=transport)

    client.activate_thought(BRAIN, THOUGHT_ID)

    assert transport.calls[0][0] == "POST"


def test_create_thought_sends_caller_supplied_body_verbatim():
    transport = FakeTransport(
        responses={("POST", f"/thoughts/{BRAIN}"): fx.CREATE_THOUGHT_RESULT}
    )
    client = LocalBrainClient(make_config(), transport=transport)
    body = {"name": "Fixture Thought", "sourceThoughtId": THOUGHT_ID}

    result = client.create_thought(BRAIN, body)

    assert result == fx.CREATE_THOUGHT_RESULT
    method, url, headers = transport.calls[0]
    assert method == "POST"
    assert headers["Content-Type"] == "application/json"
