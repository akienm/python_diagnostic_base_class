"""python_diagnostic_base_class — merged logging + perf + instance-naming base."""

from .base import DiagnosticBase
from .perf import Stopwatch
from .tagged_logger import TaggedLogger

__all__ = ["DiagnosticBase", "Stopwatch", "TaggedLogger"]
__version__ = "0.1.0"
