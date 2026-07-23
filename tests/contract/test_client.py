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
