from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def comparison_root() -> Path:
    return repo_root() / "comparison_bench"


def default_output_dir() -> Path:
    return comparison_root() / "outputs_comparison"


def ensure_under_comparison(path: Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = (repo_root() / p).resolve()
    root = comparison_root().resolve()
    try:
        p.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError(f"comparison outputs must stay under {root}: {p}") from exc
    return p
