"""Typed errors for corykidion.

Every failure mode an agent or a human operator can hit is represented by a
distinct exception here rather than a bare string or a generic ``Exception``,
so callers (especially agents) can branch on *what kind* of thing went wrong
instead of parsing prose.
"""

from __future__ import annotations


class CorykidionError(Exception):
    """Base class for every error this package raises on purpose."""


class ConfigurationError(CorykidionError):
    """The operator's configuration is missing, malformed, or unsafe.

    Raised for things like a missing API key, an endpoint that isn't
    loopback when loopback is required, or a config file that can't be
    parsed. This is a configuration-time failure, not a runtime one.
    """


class ConnectionRefused(CorykidionError):
    """Could not reach the local API.

    Almost always means: TheBrain's desktop app isn't running, or the
    endpoint/port in your configuration is stale. See WORKING_ARCHITECTURE.md
    safety invariant 1 (loopback by default) for why this package never
    tries to fall back to a remote host on its own.
    """


class AuthenticationError(CorykidionError):
    """The local API rejected the configured API key."""


class CapabilityUnknown(CorykidionError):
    """The requested operation is not in the evidenced capability set.

    corykidion fails closed: rather than guess at an endpoint shape that
    hasn't been verified against a real response, it refuses and tells you
    so. See src/corykidion/capabilities.py and the "Access routes found in
    the surveyed repositories" section of WORKING_ARCHITECTURE.md.
    """

    def __init__(self, capability: str, note: str = ""):
        self.capability = capability
        message = f"capability not yet supported: {capability!r}"
        if note:
            message = f"{message} ({note})"
        super().__init__(message)


class SafetyViolation(CorykidionError):
    """A requested operation was blocked by the safety gate.

    Raised for out-of-scope targets, disabled write access, or any other
    violation of the invariants in WORKING_ARCHITECTURE.md's "Safety
    invariants already earned" section. This is not a bug to work around;
    it is the point of the package.
    """


class UpstreamError(CorykidionError):
    """The local API reached TheBrain but returned an error response."""

    def __init__(self, status: int, path: str, body: str = ""):
        self.status = status
        self.path = path
        self.body = body
        super().__init__(f"local API returned HTTP {status} for {path}")
