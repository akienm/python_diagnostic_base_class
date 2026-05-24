"""DEPRECATED — diagnostic_base has moved into unseen_university.

Install unseen_university instead:
    pip install -e ~/dev/src/UnseenUniversity

This copy is frozen. The canonical version lives at:
    unseen_university/diagnostic_base/ in the UnseenUniversity repo.
"""

import warnings

warnings.warn(
    "python_diagnostic_base_class is deprecated. "
    "Install unseen_university instead — diagnostic_base is now part of that package.",
    DeprecationWarning,
    stacklevel=2,
)

from .base import DiagnosticBase, prune_json_logs
from .perf import Stopwatch
from .tagged_logger import TaggedLogger

__all__ = ["DiagnosticBase", "Stopwatch", "TaggedLogger", "prune_json_logs"]
__version__ = "0.1.0"
