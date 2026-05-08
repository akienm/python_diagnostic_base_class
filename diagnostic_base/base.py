"""DiagnosticBase — merged SWADL + ADC base class.

From SWADL: instance naming via gc.get_referrers, hierarchical get_name,
            substitution engine, dump/bannerize, apply_kwargs, context manager,
            timeout_remaining, lazy per-class logger.
From ADC:   device_id stamping, datacenter_logs path convention.
Logging:    loguru backend via TaggedLogger.
"""

from __future__ import annotations

import gc
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger as _root_logger

from .tagged_logger import TaggedLogger
from .perf import Stopwatch

# Per-class logger cache so subclasses see their own class name in log records
_logger_cache: dict[type, TaggedLogger] = {}


class _SafeDict(dict):
    """dict subclass that leaves unknown keys un-substituted rather than raising."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class DiagnosticBase:
    """Logging + perf + instance-naming base.

    Subclass and call super().__init__(**kwargs) from your __init__.

        class MyDevice(DiagnosticBase):
            def __init__(self, **kwargs):
                super().__init__(device_id="my_device", **kwargs)
    """

    # Subclasses may override to redirect log files
    _log_root: Path = Path("datacenter_logs")

    def __init__(
        self,
        *,
        name: str = "",
        device_id: str = "",
        parent: "DiagnosticBase | None" = None,
        **kwargs: Any,
    ):
        self._device_id = device_id or type(self).__name__.lower()
        self._parent = parent
        # Explicit name wins; gc lookup is a best-effort fallback for module/class-scope vars
        self._instance_name: str | None = name or None
        self._start_time = time.monotonic()
        self.apply_kwargs(**kwargs)

    # ── Instance naming (SWADL gc trick) ─────────────────────────────────────

    def _get_instance_names(self) -> list[str]:
        """Return variable names this instance is bound to in dict-backed scopes.

        CPython fast-locals (function frames) are NOT heap dicts — gc.get_referrers
        won't find them. This reliably finds names in module, class, and instance
        __dict__ scopes. Pass name= explicitly for function-local variables.
        """
        names: list[str] = []
        for ref in gc.get_referrers(self):
            if isinstance(ref, dict):
                for k, v in ref.items():
                    if v is self and isinstance(k, str) and not k.startswith("_"):
                        names.append(k)
        return names

    @property
    def _own_name(self) -> str:
        if self._instance_name is None:
            names = self._get_instance_names()
            self._instance_name = names[0] if names else type(self).__name__.lower()
        return self._instance_name

    def get_name(self) -> str:
        """Return hierarchical name: parent.name.own_name (no test prefix here)."""
        if self._parent is not None:
            return f"{self._parent.get_name()}.{self._own_name}"
        return self._own_name

    def __str__(self) -> str:
        return f"<{type(self).__name__} name={self.get_name()}>"

    # ── Logging ──────────────────────────────────────────────────────────────

    @property
    def logger(self) -> TaggedLogger:
        """Lazy per-class TaggedLogger bound with class and device context."""
        cls = type(self)
        if cls not in _logger_cache:
            bound = _root_logger.bind(
                class_name=cls.__name__,
                device_id=self._device_id,
            )
            _logger_cache[cls] = TaggedLogger(bound)
        return _logger_cache[cls]

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    # ── Performance stopwatch factory ─────────────────────────────────────────

    def stopwatch(self, stopwatch_id: str, *, comment: str = "") -> Stopwatch:
        """Return a Stopwatch pre-bound to this instance's device_id and class."""
        return Stopwatch(
            stopwatch_id,
            device_id=self._device_id,
            class_name=type(self).__name__,
            comment=comment,
            log_root=self._log_root,
        )

    # ── Substitution engine (SWADL _SafeDict) ────────────────────────────────

    @staticmethod
    def resolve_substitutions(template: str, context: dict, max_iter: int = 20) -> str:
        """Repeatedly expand {key} substitutions until stable or max_iter reached."""
        safe = _SafeDict(context)
        result = template
        for _ in range(max_iter):
            expanded = result.format_map(safe)
            if expanded == result:
                break
            result = expanded
        return result

    # ── kwargs absorption ────────────────────────────────────────────────────

    def apply_kwargs(self, **kwargs: Any) -> None:
        """Set any keyword arguments as instance attributes.

        Lets subclasses accept arbitrary config without enumerating every param.
        Unknown keys become attributes; no exception is raised.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    # ── Dump / bannerize ─────────────────────────────────────────────────────

    def dump(self) -> dict:
        """Return a dict of public instance attributes (useful for logging state)."""
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

    def bannerize(self, width: int = 60) -> str:
        """Return a readable banner of this instance's public state."""
        lines = [f"{'─' * width}", f"  {self}", f"{'─' * width}"]
        for k, v in self.dump().items():
            lines.append(f"  {k}: {v!r}")
        lines.append(f"{'─' * width}")
        return "\n".join(lines)

    # ── Timestamps ───────────────────────────────────────────────────────────

    @staticmethod
    def get_timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def elapsed_s(self) -> float:
        """Seconds since this instance was constructed."""
        return time.monotonic() - self._start_time

    def timeout_remaining(self, timeout_s: float) -> float:
        """Seconds remaining before timeout_s is exhausted. Negative if expired."""
        return timeout_s - self.elapsed_s()

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "DiagnosticBase":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
