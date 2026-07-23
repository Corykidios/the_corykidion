"""The local API client: a minimal typed wrapper over the loopback API.

Uses only the standard library on purpose — this package should not need a
dependency resolver to answer "is the app running." A ``transport`` callable
can be injected (see tests/contract/) so the whole client is testable
without ever touching a socket.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional

from corykidion.config import Config
from corykidion.errors import AuthenticationError, ConnectionRefused, UpstreamError

Transport = Callable[[str, str, dict[str, str], Optional[bytes]], "TransportResponse"]


@dataclass(frozen=True)
class TransportResponse:
    status: int
    body: bytes


def _default_transport(
    method: str, url: str, headers: dict[str, str], body: Optional[bytes]
) -> TransportResponse:
    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_HOLDER.get()) as response:
            return TransportResponse(status=response.status, body=response.read())
    except urllib.error.HTTPError as exc:
        return TransportResponse(status=exc.code, body=exc.read())
    except (urllib.error.URLError, ConnectionError, OSError) as exc:
        raise ConnectionRefused(
            "could not reach the local API. Is TheBrain's desktop app "
            f"running, and is the endpoint still correct? ({exc})"
        ) from exc


class _TimeoutHolder:
    """Tiny indirection so the default transport can see the configured timeout
    without changing the Transport call signature that tests rely on."""

    def __init__(self) -> None:
        self._value = 10.0

    def set(self, value: float) -> None:
        self._value = value

    def get(self) -> float:
        return self._value


_TIMEOUT_HOLDER = _TimeoutHolder()


class LocalBrainClient:
    """Speaks the four evidenced endpoints documented in capabilities.py.

    This class deliberately does not expose a generic ``request(path)``
    escape hatch. Every method here corresponds to one entry in
    EVIDENCED_CAPABILITIES, so the set of things this client can do is
    always exactly the set of things it has been verified to do.
    """

    def __init__(self, config: Config, transport: Transport = _default_transport) -> None:
        self._config = config
        self._transport = transport
        _TIMEOUT_HOLDER.set(config.timeout_seconds)

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self._request("GET", path, params=params, body=None)

    def _post(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self._request("POST", path, params=params, body=b"")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None,
        body: Optional[bytes],
    ) -> Any:
        url = f"{self._config.endpoint}{path}"
        if params:
            query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
            url = f"{url}?{query}"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Accept": "application/json",
        }
        response = self._transport(method, url, headers, body)
        if response.status == 401 or response.status == 403:
            raise AuthenticationError(
                "the local API rejected this API key. It may be invalid, "
                "revoked, or belong to a different user. Check Settings > "
                "User > Local API in TheBrain's desktop app."
            )
        if response.status >= 400:
            raise UpstreamError(response.status, path, body=response.body.decode("utf-8", "replace"))
        if not response.body:
            return {}
        return json.loads(response.body)

    # -- evidenced operations -------------------------------------------------

    def get_app_state(self) -> dict[str, Any]:
        """GET /app/state"""
        return self._get("/app/state")

    def list_brains(self) -> list[dict[str, Any]]:
        """GET /brains"""
        data = self._get("/brains")
        if isinstance(data, dict):
            return data.get("brains", [])
        return data

    def get_thought(self, brain_id: str, thought_id: str) -> dict[str, Any]:
        """GET /thoughts/{brainId}/{thoughtId}"""
        return self._get(f"/thoughts/{brain_id}/{thought_id}")

    def find_attachments_by_location(
        self, brain_id: str, location: str, attachment_type: int = 3
    ) -> list[dict[str, Any]]:
        """GET /attachments/{brainId}/by-location?location=...&type=..."""
        data = self._get(
            f"/attachments/{brain_id}/by-location",
            params={"location": location, "type": str(attachment_type)},
        )
        if isinstance(data, dict):
            return data.get("attachments", [])
        return data
