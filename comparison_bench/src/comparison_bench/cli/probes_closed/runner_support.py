"""Shared stdlib census runner plumbing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def validate_out_root(
    out_root: str | Path,
    repo_root: str | Path,
    expected_relative: str | Path,
    error_qualifier: str = "",
) -> Path:
    root = Path(repo_root).resolve()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    expected = (root / expected_relative).resolve()
    if resolved != expected:
        raise ValueError(
            f"out-root must equal {error_qualifier}frozen fresh root {expected}"
        )
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def json_write(
    path: str | Path,
    value: Any,
    convert: Callable[[Any], Any] | None = None,
) -> None:
    if convert is not None:
        value = convert(value)
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def append_log(path: str | Path, line: str) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def rss_bytes_optional() -> int | None:
    try:
        import resource
    except ImportError:
        return None
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def rss_bytes_required(resource_module: Any) -> int:
    return int(
        resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss
    ) * 1024


def resource_stop(
    started: float,
    now: Callable[[], float],
    rss_fn: Callable[[], int | None],
    *,
    wall_cap_s: float,
    rss_cap_bytes: int,
    rss_samples: list[int] | None = None,
    clamp_elapsed: bool = False,
    allow_missing_rss: bool = False,
) -> str:
    elapsed = float(now()) - float(started)
    if clamp_elapsed:
        elapsed = max(elapsed, 0.0)
    if elapsed > wall_cap_s:
        return "total_wall_cap"
    rss = rss_fn()
    if rss is None and allow_missing_rss:
        return ""
    rss = int(rss)  # required-RSS caller retains the prior TypeError on None
    if rss_samples is not None:
        rss_samples.append(rss)
    if rss >= rss_cap_bytes:
        return "rss_cap"
    return ""
