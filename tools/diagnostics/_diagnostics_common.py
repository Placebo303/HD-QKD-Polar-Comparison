from __future__ import annotations

import math
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))

from src.runtime_paths import default_project_results_root, map_data_path

ABS_EPS = 1e-9
REL_EPS = 1e-6

LOSS_CONFIGS: dict[int, dict[str, Any]] = {
    6: {
        "loss_db": 6,
        "candidate_dir": default_project_results_root(REPO_ROOT) / "e2e_6dB_fullgrid_pairing_v2_candidate",
        "ttbin": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\Type2_5s_6dB_2026-01-30_224719.ttbin"),
        "grid_table": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\e2e_pipeline_20260303_105145\_tmp_grid_table.csv"),
    },
    10: {
        "loss_db": 10,
        "candidate_dir": default_project_results_root(REPO_ROOT) / "e2e_10dB_fullgrid_pairing_v2_candidate",
        "ttbin": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\Type2_5s_10dB_2026-01-30_224808.ttbin"),
        "grid_table": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv"),
    },
    16: {
        "loss_db": 16,
        "candidate_dir": default_project_results_root(REPO_ROOT) / "e2e_16dB_fullgrid_pairing_v2_candidate",
        "ttbin": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\Type2_5s_16dB_2026-01-30_224900.ttbin"),
        "grid_table": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv"),
    },
    20: {
        "loss_db": 20,
        "candidate_dir": default_project_results_root(REPO_ROOT) / "e2e_20dB_fullgrid_pairing_v2_candidate_t15",
        "ttbin": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\Type2_5s_20dB_2026-01-30_224943.ttbin"),
        "grid_table": map_data_path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv"),
    },
}


def parse_int_csv(text: str, *, name: str) -> list[int]:
    out: list[int] = []
    for item in str(text or "").split(","):
        s = item.strip()
        if not s:
            continue
        try:
            out.append(int(float(s)))
        except Exception as e:
            raise SystemExit(f"invalid {name} item: {s}") from e
    if not out:
        raise SystemExit(f"{name} must not be empty")
    return out


def infer_loss_db_from_dir(path: Path) -> int:
    m = re.search(r"(\d+)dB", path.name, flags=re.IGNORECASE)
    if not m:
        raise SystemExit(f"cannot infer loss_db from input dir: {path}")
    return int(m.group(1))


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


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"input file not found: {path}")
    return pd.read_csv(path)


def normalize_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def candidate_main_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_e2e_results.csv"


def candidate_diag_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_diag_summary.csv"


def bw_bucket(bw: int | float | None) -> str:
    if bw is None:
        return "unknown"
    try:
        bw_i = int(bw)
    except Exception:
        return "unknown"
    if bw_i in {20, 30, 40, 50}:
        return "bw_small"
    if bw_i in {60, 80, 100}:
        return "bw_mid"
    if bw_i in {120, 150, 180, 200}:
        return "bw_large"
    return "unknown"


def tol_for_values(*vals: Any) -> float:
    mags = [1.0]
    for v in vals:
        if v is None:
            continue
        try:
            fv = float(v)
        except Exception:
            continue
        if math.isnan(fv):
            continue
        mags.append(abs(fv))
    return max(ABS_EPS, REL_EPS * max(mags))


def monotonic_increasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    for prev, cur in zip(values, values[1:]):
        if float(cur) - float(prev) < -tol_for_values(prev, cur):
            return False
    return True


def monotonic_decreasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    for prev, cur in zip(values, values[1:]):
        if float(cur) - float(prev) > tol_for_values(prev, cur):
            return False
    return True


def has_interior_peak(sorted_keys: list[int], values: list[float]) -> bool:
    if len(values) < 3:
        return False
    arr = np.asarray(values, dtype=float)
    if np.isnan(arr).all():
        return False
    best_idx = int(np.nanargmax(arr))
    if best_idx == 0 or best_idx == len(values) - 1:
        return False
    best_val = float(values[best_idx])
    if monotonic_increasing(values):
        return False
    if best_val - float(values[0]) <= tol_for_values(best_val, values[0]):
        return False
    if best_val - float(values[-1]) <= tol_for_values(best_val, values[-1]):
        return False
    return True


def write_summary(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
