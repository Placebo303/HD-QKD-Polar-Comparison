from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any, Iterable


_file_lock = threading.Lock()

import pandas as pd

from ..utils.paths import repo_root


ERROR_COLUMNS = [
    "timestamp",
    "stage",
    "dataset_id",
    "dimension",
    "bin_width_ps",
    "method",
    "method_variant",
    "frame_cap",
    "param_hash",
    "error_type",
    "error_message",
    "traceback_short",
    "status",
]


@dataclass(frozen=True)
class SweepPaths:
    output_dir: Path
    error_csv: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_param_hash(params: dict[str, Any]) -> str:
    text = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_existing_keys(path: Path, key_cols: Iterable[str]) -> set[tuple[str, ...]]:
    if not path.exists():
        return set()
    try:
        df = pd.read_csv(path, usecols=lambda c: c in set(key_cols))
    except Exception:
        return set()
    keys = set()
    for _, row in df.iterrows():
        keys.add(tuple("" if pd.isna(row.get(c)) else str(row.get(c)) for c in key_cols))
    return keys


def append_rows(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if not rows:
        return
    with _file_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            df = df[columns]
        header = not path.exists()
        df.to_csv(path, mode="a", header=header, index=False)


def append_frame_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with _file_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        df_new = pd.DataFrame(rows)
        if path.exists():
            try:
                df_old = pd.read_parquet(path)
            except Exception:
                df_old = pd.read_pickle(path)
            df_new = pd.concat([df_old, df_new], ignore_index=True)
        try:
            df_new.to_parquet(path, index=False)
        except Exception:
            df_new.to_pickle(path)


def append_error(paths: SweepPaths, *, stage: str, dataset_id: str = "", dimension: Any = None,
                 bin_width_ps: Any = None, method: str = "", method_variant: str = "",
                 frame_cap: Any = None, param_hash: str = "", exc: BaseException,
                 status: str = "failed") -> None:
    row = {
        "timestamp": utc_now(),
        "stage": stage,
        "dataset_id": dataset_id,
        "dimension": dimension,
        "bin_width_ps": bin_width_ps,
        "method": method,
        "method_variant": method_variant,
        "frame_cap": frame_cap,
        "param_hash": param_hash,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback_short": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=4))[-2000:],
        "status": status,
    }
    append_rows(paths.error_csv, [row], ERROR_COLUMNS)


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root()), text=True).strip()
    except Exception:
        return "unknown"


def write_manifest(path: Path, *, config: dict[str, Any], completed_stages: list[str],
                   failed_stages: list[str], output_files: dict[str, str],
                   runtime_total_s: float, notes: str = "",
                   stage_name: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _file_lock:
        completed = list(completed_stages)
        failed = list(failed_stages)
        outputs = dict(output_files)
        elapsed_time = float(runtime_total_s)
        combined_notes = str(notes)
        per_stage_configs: dict[str, Any] = {}
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
                completed = list(sorted(set(old.get("completed_stages", []) + completed)))
                failed = list(sorted(set(old.get("failed_stages", []) + failed)))
                old_outputs = old.get("output_files", {})
                old_outputs.update(outputs)
                outputs = old_outputs
                elapsed_time += float(old.get("runtime_total_s", 0.0))
                if old.get("notes") and old["notes"] != combined_notes:
                    combined_notes = f"{old['notes']}; {combined_notes}"
                # Preserve per-stage config snapshots from old manifest
                old_per_stage = old.get("per_stage_config_snapshots", {})
                if old_per_stage:
                    per_stage_configs.update(old_per_stage)
                # Also preserve the old top-level snapshot under its inferred stage name
                old_snapshot = old.get("benchmark_config_snapshot")
                old_stages = old.get("completed_stages", [])
                if old_snapshot and old_stages:
                    # Infer stage name from the stages that were completed when old snapshot was written
                    for s in reversed(old_stages):
                        if s not in per_stage_configs and s != stage_name:
                            per_stage_configs[s] = old_snapshot
                            break
            except Exception:
                pass

        # Store current config under stage_name if provided
        if stage_name:
            per_stage_configs[stage_name] = config

        manifest = {
            "timestamp": utc_now(),
            "git_commit": git_commit(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "benchmark_config_snapshot": config,
            "per_stage_config_snapshots": per_stage_configs,
            "completed_stages": completed,
            "failed_stages": failed,
            "output_files": outputs,
            "runtime_total_s": elapsed_time,
            "notes": combined_notes,
        }
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")


def sweep_paths(output_dir: Path) -> SweepPaths:
    return SweepPaths(output_dir=output_dir, error_csv=output_dir / "run_errors_ir_v3.csv")


def elapsed(start: float) -> float:
    return float(time.perf_counter() - start)
