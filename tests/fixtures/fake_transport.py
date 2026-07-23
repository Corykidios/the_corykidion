"""A scripted fake transport matching corykidion.client.Transport's signature,
so contract tests never touch a real socket."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from corykidion.client import TransportResponse


@dataclass
class FakeTransport:
    """Maps (method, path-without-query) -> a canned JSON response.

    ``calls`` records every invocation for assertions about what the client
    actually sent (headers, method, URL).
    """

    responses: dict[tuple[str, str], object] = field(default_factory=dict)
    status_overrides: dict[tuple[str, str], int] = field(default_factory=dict)
    calls: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)

    def __call__(self, method, url, headers, body):
        path = url.split("?", 1)[0]
        # Strip everything up through /api for a stable lookup key.
        key_path = path.split("/api", 1)[-1] if "/api" in path else path
        self.calls.append((method, url, dict(headers)))
        status = self.status_overrides.get((method, key_path), 200)
        payload = self.responses.get((method, key_path), {})
        return TransportResponse(status=status, body=json.dumps(payload).encode("utf-8"))
