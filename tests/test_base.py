"""Tests for DiagnosticBase."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from diagnostic_base.base import DiagnosticBase, _SafeDict

# Module-level instance — gc trick works because module dict is a real heap dict
_module_device = DiagnosticBase(device_id="mod", name="module_device")


class TestInstanceNaming:
    def test_explicit_name_wins(self):
        obj = DiagnosticBase(device_id="d", name="my_sensor")
        assert obj.get_name() == "my_sensor"

    def test_gc_trick_finds_module_scope_name(self):
        # gc.get_referrers works for module/class-scope dicts, not CPython fast-locals
        assert _module_device.get_name() == "module_device"

    def test_fallback_when_no_name(self):
        # Function-local vars aren't in a heap dict; falls back to class name
        obj = DiagnosticBase(device_id="d")
        name = obj.get_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_name_hierarchical(self):
        parent = DiagnosticBase(device_id="p", name="parent")
        child = DiagnosticBase(device_id="c", name="child", parent=parent)
        assert child.get_name() == "parent.child"

    def test_str_includes_class_and_name(self):
        obj = DiagnosticBase(device_id="x")
        s = str(obj)
        assert "DiagnosticBase" in s
        assert "name=" in s


class TestSubstitution:
    def test_simple_substitution(self):
        result = DiagnosticBase.resolve_substitutions(
            "{greeting} world", {"greeting": "hello"}
        )
        assert result == "hello world"

    def test_nested_substitution(self):
        ctx = {"a": "{b}", "b": "resolved"}
        result = DiagnosticBase.resolve_substitutions("{a}", ctx)
        assert result == "resolved"

    def test_unknown_key_left_intact(self):
        result = DiagnosticBase.resolve_substitutions("{unknown}", {})
        assert result == "{unknown}"

    def test_safe_dict_missing(self):
        d = _SafeDict({"x": "1"})
        assert d["x"] == "1"
        assert d["missing"] == "{missing}"


class TestApplyKwargs:
    def test_kwargs_become_attributes(self):
        obj = DiagnosticBase(device_id="d", foo="bar", count=42)
        assert obj.foo == "bar"
        assert obj.count == 42


class TestDump:
    def test_dump_returns_public_attrs(self):
        obj = DiagnosticBase(device_id="d", color="blue")
        d = obj.dump()
        assert "color" in d
        # private attrs excluded
        assert "_device_id" not in d

    def test_bannerize_contains_name(self):
        obj = DiagnosticBase(device_id="d")
        banner = obj.bannerize()
        assert "DiagnosticBase" in banner


class TestTimestamp:
    def test_get_timestamp_format(self):
        ts = DiagnosticBase.get_timestamp()
        assert "T" in ts
        assert ts.endswith("Z")

    def test_elapsed_s_increases(self):
        obj = DiagnosticBase(device_id="d")
        time.sleep(0.01)
        assert obj.elapsed_s() >= 0.01

    def test_timeout_remaining_positive(self):
        obj = DiagnosticBase(device_id="d")
        remaining = obj.timeout_remaining(10.0)
        assert 0 < remaining <= 10.0

    def test_timeout_remaining_negative_after_expiry(self):
        obj = DiagnosticBase(device_id="d")
        time.sleep(0.05)
        assert obj.timeout_remaining(0.01) < 0


class TestContextManager:
    def test_context_manager_returns_self(self):
        obj = DiagnosticBase(device_id="d")
        with obj as ctx:
            assert ctx is obj

    def test_context_manager_does_not_suppress_exceptions(self):
        obj = DiagnosticBase(device_id="d")
        with pytest.raises(RuntimeError):
            with obj:
                raise RuntimeError("boom")


class TestLogger:
    def test_logger_is_tagged_logger(self):
        from diagnostic_base.tagged_logger import TaggedLogger

        obj = DiagnosticBase(device_id="d")
        assert isinstance(obj.logger, TaggedLogger)

    def test_convenience_methods_do_not_raise(self):
        obj = DiagnosticBase(device_id="d")
        obj.debug("d")
        obj.info("i")
        obj.warning("w")
        obj.error("e")

    def test_stopwatch_factory(self, tmp_path):
        obj = DiagnosticBase(device_id="mydev")
        obj._log_root = tmp_path
        sw = obj.stopwatch("op", comment="test")
        assert sw.device_id == "mydev"
        assert sw.stopwatch_id == "op"
        assert sw.comment == "test"
