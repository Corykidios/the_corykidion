"""The configuration boundary.

Per WORKING_ARCHITECTURE.md's product boundary rules, this repository must
never encode a private deployment (endpoints, API keys, brain IDs). This
module is the one place those facts are allowed to enter the program, and
they enter from outside the repository: environment variables, or a config
file the operator points at explicitly. Nothing here has a hidden default
that reaches across the network.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from corykidion.errors import ConfigurationError, SafetyViolation

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

_ENV_ENDPOINT = "CORYKIDION_ENDPOINT"
_ENV_API_KEY = "CORYKIDION_API_KEY"
_ENV_BRAIN_ID = "CORYKIDION_BRAIN_ID"
_ENV_ALLOW_REMOTE = "CORYKIDION_ALLOW_REMOTE"
_ENV_TIMEOUT = "CORYKIDION_TIMEOUT_SECONDS"


@dataclass(frozen=True)
class Config:
    """Everything the client needs to reach one local TheBrain instance.

    ``default_brain_id`` is optional context, not authority: individual
    calls still take an explicit brain_id (safety invariant 4, "no ambient
    target"). It exists only to save typing at the CLI.
    """

    endpoint: str
    api_key: str
    default_brain_id: str | None = None
    timeout_seconds: float = 10.0
    allow_remote: bool = False

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ConfigurationError("api_key is required and must not be empty")
        _assert_loopback(self.endpoint, allow_remote=self.allow_remote)


def _assert_loopback(endpoint: str, *, allow_remote: bool) -> None:
    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.hostname:
        raise ConfigurationError(f"endpoint is not a valid URL: {endpoint!r}")
    if parsed.hostname not in _LOOPBACK_HOSTS and not allow_remote:
        raise SafetyViolation(
            "endpoint "
            f"{endpoint!r} is not loopback (safety invariant 1). "
            "corykidion talks to the local app by default. If you really "
            "intend a non-loopback endpoint, pass allow_remote=True "
            "explicitly — this package will not infer that for you."
        )


def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"config file is not valid TOML: {path} ({exc})") from exc


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Build a Config from environment variables, optionally overlaid by a TOML file.

    Precedence: explicit TOML file values, then environment variables. Both
    are optional per field except ``endpoint`` and ``api_key``, which must
    come from somewhere. Nothing is read from a fixed default location —
    the caller (typically the CLI) decides whether a file path applies.
    """
    values: dict = {}
    if path is not None:
        values = _load_toml(Path(path))

    endpoint = values.get("endpoint") or os.environ.get(_ENV_ENDPOINT)
    api_key = values.get("api_key") or os.environ.get(_ENV_API_KEY)
    default_brain_id = values.get("default_brain_id") or os.environ.get(_ENV_BRAIN_ID)
    allow_remote = _as_bool(values.get("allow_remote"), os.environ.get(_ENV_ALLOW_REMOTE))
    timeout_raw = values.get("timeout_seconds") or os.environ.get(_ENV_TIMEOUT)

    if not endpoint:
        raise ConfigurationError(
            "no endpoint configured. Set CORYKIDION_ENDPOINT or provide it in "
            "a config file (see examples/config.example.toml). Find yours in "
            "TheBrain's desktop app under Settings > User > Local API."
        )
    if not api_key:
        raise ConfigurationError(
            "no api_key configured. Set CORYKIDION_API_KEY or provide it in "
            "a config file. Never commit this value."
        )

    kwargs = dict(
        endpoint=str(endpoint).rstrip("/"),
        api_key=str(api_key),
        default_brain_id=str(default_brain_id) if default_brain_id else None,
        allow_remote=allow_remote,
    )
    if timeout_raw is not None:
        kwargs["timeout_seconds"] = float(timeout_raw)
    return Config(**kwargs)


def _as_bool(toml_value, env_value: str | None) -> bool:
    if toml_value is not None:
        return bool(toml_value)
    if env_value is None:
        return False
    return env_value.strip().lower() in {"1", "true", "yes", "on"}
