"""corykidion: a small, local-first, read-only-first bridge between AI agents and TheBrain.

See WORKING_ARCHITECTURE.md at the repository root for the design ledger this
package implements against, including the maturity labels ("evidence",
"direction", "candidate", "deferred", "rejected", "unresolved") referenced
throughout this codebase's docstrings and comments.

Not affiliated with or endorsed by TheBrain Technologies.
"""

from corykidion.errors import (
    CapabilityUnknown,
    ConfigurationError,
    ConnectionRefused,
    CorykidionError,
    SafetyViolation,
    UpstreamError,
)
from corykidion.models import Attachment, Brain, Thought

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CorykidionError",
    "ConfigurationError",
    "ConnectionRefused",
    "CapabilityUnknown",
    "SafetyViolation",
    "UpstreamError",
    "Brain",
    "Thought",
    "Attachment",
]
