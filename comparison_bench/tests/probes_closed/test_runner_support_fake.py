"""Fake-only checks for the shared S7 runner helper."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import runner_support as support


def test_fresh_root_validation(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    target = support.validate_out_root("workspace/fresh", root, "workspace/fresh")
    assert target == (root / "workspace/fresh").resolve()
    with pytest.raises(ValueError, match="frozen fresh root"):
        support.validate_out_root("workspace/other", root, "workspace/fresh")
    target.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="refusing existing output root"):
        support.validate_out_root("workspace/fresh", root, "workspace/fresh")


def test_json_conversion_format_and_log_newline(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"
    support.json_write(output, {"z": (1, 2), "a": 3}, convert=lambda x: dict(x))
    text = output.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index('"a"') < text.index('"z"')
    assert json.loads(text) == {"a": 3, "z": [1, 2]}

    log = tmp_path / "run.log"
    support.append_log(log, "first  \n")
    support.append_log(log, "second")
    assert log.read_text(encoding="utf-8") == "first\nsecond\n"


def test_rss_helpers_use_only_fake_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_resource = SimpleNamespace(
        RUSAGE_SELF=object(),
        getrusage=lambda _who: SimpleNamespace(ru_maxrss=23),
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)
    assert support.rss_bytes_optional() == 23 * 1024
    assert support.rss_bytes_required(fake_resource) == 23 * 1024

    monkeypatch.setitem(sys.modules, "resource", None)
    assert support.rss_bytes_optional() is None


def test_wall_and_rss_limits_keep_distinct_boundaries() -> None:
    rss_calls: list[int] = []
    samples: list[int] = []
    common = dict(wall_cap_s=5.0, rss_cap_bytes=10, rss_samples=samples)
    assert support.resource_stop(
        2.0, lambda: 7.0, lambda: rss_calls.append(1) or 9, **common
    ) == ""
    assert rss_calls == [1]
    assert samples == [9]

    assert support.resource_stop(
        2.0, lambda: 7.0001, lambda: pytest.fail("RSS called after wall cap"), **common
    ) == "total_wall_cap"
    assert support.resource_stop(
        2.0, lambda: 7.0, lambda: 10, **common
    ) == "rss_cap"


def test_wall_clamp_and_missing_rss_modes() -> None:
    common = dict(wall_cap_s=1.0, rss_cap_bytes=100)
    assert support.resource_stop(
        10.0, lambda: 9.0, lambda: 1, clamp_elapsed=True, **common
    ) == ""
    assert support.resource_stop(
        0.0, lambda: 0.0, lambda: None, allow_missing_rss=True, **common
    ) == ""
    with pytest.raises(TypeError):
        support.resource_stop(0.0, lambda: 0.0, lambda: None, **common)
