"""DEPRECATED — diagnostic_base has moved into agent_datacenter.

Install agent_datacenter instead:
    pip install -e ~/dev/src/agent_datacenter

This copy is frozen. The canonical version lives at:
    agent_datacenter/diagnostic_base/ in the agent_datacenter repo.
"""

import warnings

warnings.warn(
    "python_diagnostic_base_class is deprecated. "
    "Install agent_datacenter instead — diagnostic_base is now part of that package.",
    DeprecationWarning,
    stacklevel=2,
)

from .base import DiagnosticBase, prune_json_logs
from .perf import Stopwatch
from .tagged_logger import TaggedLogger

__all__ = ["DiagnosticBase", "Stopwatch", "TaggedLogger", "prune_json_logs"]
__version__ = "0.1.0"
