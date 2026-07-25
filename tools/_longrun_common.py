from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, infer_loss_db_from_path

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.runtime_paths import default_project_results_root, map_data_path

DEFAULT_FRANSON_VISIBILITY = 0.95
DEFAULT_EPS_SEC = 1e-10
DEFAULT_EPS_COR = 1e-10
DEFAULT_BETA_BASELINE = 0.90
DEFAULT_WORKERS = 15
REPRESENTATIVE_DIMS = [256, 512, 1024, 2048, 4096]
REPRESENTATIVE_BWS = [20, 30, 40, 60, 80, 100, 150, 200]
FULLGRID_DIMS = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
FULLGRID_BWS = [20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 200]

LOSS_INPUT_CONFIGS: dict[int, dict[str, str | int]] = {
    6: {
        "ttbin": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\Type2_5s_6dB_2026-01-30_224719.ttbin",
        "grid_table": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\e2e_pipeline_20260303_105145\_tmp_grid_table.csv",
        "ch_a": 1,
        "ch_b": 5,
    },
    10: {
        "ttbin": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\Type2_5s_10dB_2026-01-30_224808.ttbin",
        "grid_table": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv",
        "ch_a": 1,
        "ch_b": 5,
    },
    16: {
        "ttbin": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\Type2_5s_16dB_2026-01-30_224900.ttbin",
        "grid_table": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv",
        "ch_a": 1,
        "ch_b": 5,
    },
    20: {
        "ttbin": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\Type2_5s_20dB_2026-01-30_224943.ttbin",
        "grid_table": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\e2e_new_ttbin_fullgrid\_tmp_grid_table_rawdata_fix.csv",
        "ch_a": 1,
        "ch_b": 5,
    },
}


for _cfg in LOSS_INPUT_CONFIGS.values():
    _cfg["ttbin"] = str(map_data_path(str(_cfg["ttbin"])))
    _cfg["grid_table"] = str(map_data_path(str(_cfg["grid_table"])))


def candidate_dir_for_loss(loss_db: int) -> Path:
    stem = f"e2e_{int(loss_db)}dB_fullgrid_pairing_v2_candidate"
    if int(loss_db) == 20:
        stem += "_t15"
    return default_project_results_root(REPO_ROOT) / stem


def point_table_sort(df: pd.DataFrame) -> pd.DataFrame:
    order_cols = [c for c in ("loss_db", "dimension", "bin_width_ps", "layer_id", "block_index") if c in df.columns]
    if not order_cols:
        return df
    return df.sort_values(order_cols).reset_index(drop=True)


def csv_read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def subprocess_run(cmd: list[str], *, cwd: Path | None = None, timeout_s: int | None = None) -> None:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command failed rc={proc.returncode}: {' '.join(cmd)}")


def python_tool(tool_name: str, *args: str, timeout_s: int | None = None) -> None:
    cmd = [sys.executable, str(REPO_ROOT / "tools" / tool_name), *args]
    subprocess_run(cmd, cwd=REPO_ROOT, timeout_s=timeout_s)


def ensure_stage_dir(path: Path, *, overwrite: bool) -> None:
    ensure_output_dir(path, overwrite=overwrite)
    (path / "_shards").mkdir(parents=True, exist_ok=True)


def shard_dataframe(df: pd.DataFrame, n_shards: int) -> list[pd.DataFrame]:
    if df.empty:
        return [df.copy()]
    shards: list[pd.DataFrame] = []
    n_shards = max(1, int(n_shards))
    chunk = int(math.ceil(len(df) / float(n_shards)))
    for idx in range(0, len(df), chunk):
        shards.append(df.iloc[idx : idx + chunk].copy())
    return shards or [df.copy()]


def dims_arg(dims: Iterable[int]) -> str:
    return ",".join(str(int(x)) for x in dims)


def bws_arg(bws: Iterable[int]) -> str:
    return ",".join(str(int(x)) for x in bws)


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def infer_loss_from_candidate_dir(path: Path) -> int:
    return infer_loss_db_from_path(path)
