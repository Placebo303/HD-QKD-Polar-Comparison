from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ABS_EPS = 1e-9


def ensure_output_dir(path: Path, *, overwrite: bool) -> None:
    if path.exists():
        has_contents = any(path.iterdir()) if path.is_dir() else True
        if has_contents and not overwrite:
            raise SystemExit(f"output already exists: {path} (use --overwrite)")
        if overwrite:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    path.mkdir(parents=True, exist_ok=True)


def write_summary(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def infer_loss_db_from_path(path: Path) -> int:
    name = str(path).lower()
    for loss_db in (20, 16, 10, 6):
        if f"{loss_db}db" in name:
            return int(loss_db)
    raise SystemExit(f"cannot infer loss_db from path: {path}")


def point_id(*, loss_db: int, dimension: int, bin_width_ps: int) -> str:
    return f"loss{int(loss_db)}_d{int(dimension)}_bw{int(bin_width_ps)}"


def safe_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def safe_load_npy(path: Path) -> np.ndarray | None:
    try:
        return np.load(path, mmap_mode="r")
    except Exception:
        return None


def candidate_sidecar_root(candidate_dir: Path, dimension: int, bin_width_ps: int) -> Path:
    return candidate_dir / "sidecars" / f"d{int(dimension)}_bw{int(bin_width_ps)}" / "blk0"


def load_candidate_bundle(candidate_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    main = pd.read_csv(candidate_dir / "polar_e2e_results.csv")
    diag = pd.read_csv(candidate_dir / "polar_diag_summary.csv")
    layer = pd.read_csv(candidate_dir / "polar_layer_metrics.csv")
    for frame in (main, diag, layer):
        for col in ("dimension", "bin_width_ps"):
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("Int64")
    if "layer_idx" in layer.columns:
        layer["layer_idx"] = pd.to_numeric(layer["layer_idx"], errors="coerce").astype("Int64")
    return main, diag, layer


def merged_candidate_point_frame(candidate_dir: Path) -> pd.DataFrame:
    main, diag, _ = load_candidate_bundle(candidate_dir)
    diag_keep = [c for c in diag.columns if c in {"dimension", "bin_width_ps", "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"}]
    merged = main.merge(diag[diag_keep].drop_duplicates(["dimension", "bin_width_ps"]), on=["dimension", "bin_width_ps"], how="left", suffixes=("", "_diag"))
    for col in ("raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"):
        diag_col = f"{col}_diag"
        if diag_col in merged.columns:
            if col not in merged.columns:
                merged[col] = merged[diag_col]
            else:
                merged[col] = merged[col].where(pd.notna(merged[col]), merged[diag_col])
            merged = merged.drop(columns=[diag_col])
    return merged


def bit_layer_from_symbols(symbols: np.ndarray, *, dimension: int, layer_idx: int) -> np.ndarray:
    bits = int(round(math.log2(int(dimension))))
    shift = bits - 1 - int(layer_idx)
    arr = np.asarray(symbols, dtype=np.int64)
    return ((arr >> shift) & 1).astype(np.uint8, copy=False)


def chunk_count(total: int, block_symbols: int) -> int:
    if block_symbols <= 0:
        return 0
    return int(total // block_symbols)


def monotonic_increasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    for prev, cur in zip(values, values[1:]):
        if float(cur) - float(prev) < -ABS_EPS:
            return False
    return True


def interior_peak(keys: list[int], values: list[float]) -> bool:
    if len(values) < 3:
        return False
    arr = np.asarray(values, dtype=float)
    if np.isnan(arr).all():
        return False
    best_idx = int(np.nanargmax(arr))
    if best_idx == 0 or best_idx == len(values) - 1:
        return False
    if monotonic_increasing(values):
        return False
    best_val = float(values[best_idx])
    return (best_val - float(values[0]) > ABS_EPS) and (best_val - float(values[-1]) > ABS_EPS)
