"""Focused no-data tests for the P3 Stage 0.5 thin probe (G-P3-STAGE05).

FAKE-ONLY: every FileReader here is an explicit in-test fake. The real
``FileReader`` and real ``.ttbin`` data are never touched (AGENTS.md §10.1
clause 8). Run per-file ONLY:
.venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import json
import sys

import pytest

from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
from comparison_bench.src.comparison_bench.cli import p3_stage05_probe as m


class _FakeBuf:
    def __init__(self, ts):
        self._ts = list(ts)

    def getTimestamps(self):
        return self._ts


class _FakeReader:
    """Fake FileReader: records opens; serves scripted timestamp chunks."""

    opens: list[str] = []

    def __init__(self, path, chunks=None, config=None, channels=None, marker=""):
        type(self).opens.append(path)
        self.path = path
        self._chunks = [list(c) for c in (chunks or [])]
        self._config = config if config is not None else {"k": 1}
        self._channels = channels if channels is not None else [1, 5]
        self._marker = marker
        self.closed = False

    def getConfiguration(self):
        return self._config

    def getChannelList(self):
        return self._channels

    def getLastMarker(self):
        return self._marker

    def hasData(self):
        return bool(self._chunks)

    def getData(self, n):
        return _FakeBuf(self._chunks.pop(0))

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_opens():
    _FakeReader.opens = []
    yield
    _FakeReader.opens = []


def test_alias_install_idempotent():
    a = install_timetagger_alias()
    b = install_timetagger_alias()
    assert a is b
    assert sys.modules["TimeTagger"] is a
    from TimeTagger import FileReader  # noqa: F401  (resolves via alias)


def test_both_member_open_refused_by_construction():
    # Base succeeds -> shard opener must never be called.
    calls: list[str] = []

    def opener(path):
        calls.append(path)
        if path.endswith(".1.ttbin"):
            raise AssertionError("shard must not be opened when base succeeds")
        return _FakeReader(path, chunks=[[0, 3_000_000_000_000]])

    member, reader, fallback = m.open_single_member("X.ttbin", opener, 2)
    assert member == "X.ttbin" and fallback is False
    assert calls == ["X.ttbin"]
    # Base fails -> exactly one shard-only open, never both live.
    calls.clear()

    def opener2(path):
        calls.append(path)
        if path == "X.ttbin":
            raise RuntimeError("no such file")
        return _FakeReader(path, chunks=[[0, 1_000_000_000_000]])

    member, reader, fallback = m.open_single_member("X.ttbin", opener2, 2)
    assert member == "X.1.ttbin" and fallback is True
    assert calls == ["X.ttbin", "X.1.ttbin"]  # sequential attempts, one live reader
    # Base fails + no budget -> shard never attempted.
    with pytest.raises(RuntimeError):
        m.open_single_member("X.ttbin", opener2, 1)


def test_gate_arithmetic():
    g = m.evaluate_gates(True, 3.0, 3.01, True)
    assert g == {"G1": True, "G2": True, "G3": True, "G4": True}
    assert m.evaluate_gates(False, 3.0, 3.0, True)["G1"] is False
    assert m.evaluate_gates(True, 0.0, 0.0, True)["G2"] is False
    assert m.evaluate_gates(True, None, 3.0, True)["G2"] is False
    assert m.evaluate_gates(True, 30.0, 3.0, True)["G3"] is False  # doubling-size mismatch
    assert m.evaluate_gates(True, 3.0, 3.4, True)["G3"] is True  # within 0.5 s tol
    assert m.evaluate_gates(True, 3.0, 3.6, True)["G3"] is False  # beyond 0.5 s tol
    assert m.evaluate_gates(True, 3.0, 3.0, False)["G4"] is False


def test_tag_disputed():
    assert m.tag_disputed(3.0) is False
    assert m.tag_disputed(29.9999524) is True  # Jan-12 known-disputed shape
    assert m.tag_disputed(None) is None


def test_config_type_resolution():
    t, v, ok = m.config_type_and_verbatim({"a": 1})
    assert t == "dict" and v == {"a": 1} and ok is True
    t, v, ok = m.config_type_and_verbatim(json.dumps({"b": 2}))
    assert t == "str" and v == {"b": 2} and ok is True
    t, v, ok = m.config_type_and_verbatim("not-json{{{")
    assert t == "str" and ok is False


def test_span_drain_keeps_first_last_only():
    r = _FakeReader("X", chunks=[[10, 20, 30], [40], [], [50, 60]])
    f, l, n, timed_out = m.span_drain_deadline(r, 10**6, lambda: False)
    assert (f, l, timed_out) == (10, 60, False)
    assert n == 4
    r = _FakeReader("X", chunks=[[1, 2]])
    f, l, n, timed_out = m.span_drain_deadline(r, 10**6, lambda: True)
    assert timed_out is True and f is None


def test_cli_arg_parsing_rejects_bad_bases(tmp_path):
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--bases", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--per-read-timeout-s", type=float, default=300.0)
    ap.add_argument("--max-reads-per-dataset", type=int, default=2)
    a = ap.parse_args(["--bases", "a;b", "--root", str(tmp_path)])
    with pytest.raises(SystemExit):
        m.parse_bases(a.bases)
    with pytest.raises(SystemExit):
        m.parse_bases("X.1.ttbin;" * 10)
