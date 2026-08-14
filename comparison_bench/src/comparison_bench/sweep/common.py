from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ..config import as_list, load_config
from ..io.dataset_builder import table_to_frame_batches
from ..io.table_store import read_table
from ..utils.paths import default_output_dir, repo_root


REPRESENTATIVE_POINTS = [
    (8, 180),
    (16, 150),
    (64, 120),
    (256, 100),
    (512, 100),
    (1024, 20),
    (1024, 100),
    (1024, 120),
    (2048, 20),
    (4096, 20),
]


def load_cfg(path: Path) -> dict[str, Any]:
    return load_config(Path(path))


def output_dir_from_cfg(cfg: dict[str, Any]) -> Path:
    out_dir = Path((cfg.get("global", {}) or {}).get("output_dir") or default_output_dir())
    if not out_dir.is_absolute():
        out_dir = repo_root() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def load_batches_from_frame_batch(path: str | Path) -> list[Any]:
    return table_to_frame_batches(read_table(Path(path)))


def representative_batches(batches: Iterable[Any], include_all: bool = False) -> list[Any]:
    items = list(batches)
    if include_all:
        return items
    selected: list[Any] = []
    for batch in items:
        point = (int(batch.dimension), int(batch.metadata.get("bin_width_ps", -1)))
        if point in REPRESENTATIVE_POINTS:
            selected.append(batch)
    return selected


def crop_batch(batch: Any, frame_cap: int) -> Any:
    if frame_cap <= 0 or int(batch.alice_symbols.shape[0]) <= frame_cap:
        return batch
    from ..types import FrameBatch

    meta = dict(batch.metadata)
    meta["frames_used_cap"] = int(frame_cap)
    return FrameBatch(
        batch.dataset_id,
        batch.alice_symbols[:frame_cap].copy(),
        batch.bob_symbols[:frame_cap].copy(),
        batch.dimension,
        batch.frame_len_symbols,
        meta,
    )


def expand_grid(grid: dict[str, Any]) -> list[dict[str, Any]]:
    keys = list(grid.keys())
    values = [as_list(grid[key]) for key in keys]
    out: list[dict[str, Any]] = []
    for combo in itertools.product(*values):
        out.append({key: value for key, value in zip(keys, combo)})
    return out


def dataset_row(batch: Any) -> dict[str, Any]:
    return {
        "dataset_id": batch.dataset_id,
        "data_mode": batch.metadata.get("data_mode", "real_data"),
        "dimension": int(batch.dimension),
        "bin_width_ps": batch.metadata.get("bin_width_ps"),
        "loss_db": batch.metadata.get("loss_db"),
        "source_path": batch.metadata.get("source_path"),
        "frame_len_symbols": int(batch.frame_len_symbols),
    }


def point_filter(batch: Any, allowed_dimensions: list[int] | None = None, allowed_bin_widths: list[int] | None = None) -> bool:
    if allowed_dimensions and int(batch.dimension) not in {int(x) for x in allowed_dimensions}:
        return False
    if allowed_bin_widths and int(batch.metadata.get("bin_width_ps", -1)) not in {int(x) for x in allowed_bin_widths}:
        return False
    return True
