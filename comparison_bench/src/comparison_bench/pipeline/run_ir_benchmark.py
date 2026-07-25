from __future__ import annotations

import json
import math
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from .. import __version__
from ..config import as_list, load_config
from ..io.dataset_builder import build_frame_batch, table_to_frame_batch, table_to_frame_batches
from ..io.pairs_loader import load_pairs_table
from ..io.table_store import read_table, write_table
from ..methods.cascade_lite import run_cascade_lite, unavailable_result as cascade_unavailable
from ..methods.layered_ldpc_lite import run_layered_ldpc_lite, unavailable_result as ldpc_unavailable
from ..methods.qldpc_reference import run_qldpc_reference
from ..io.polar_existing_bridge import benchmark_rows_from_polar_output, resolve_polar_output_from_metadata, run_polar_existing
from ..metrics.summary import add_fraction_columns
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate
from ..utils.paths import default_output_dir, repo_root

RESULT_COLUMNS = [
    "dataset_id", "data_mode", "source_path", "loss_db", "dimension", "bin_width_ps", "n_eff_pairs",
    "frame_len_symbols", "frame_len_bits", "method", "method_variant", "method_status",
    "processing_rule_version", "pairing_path_tag", "threshold_ps", "effective_pairing_window_ps",
    "n_frames_total", "n_frames_attempted", "n_frames_success", "n_frames_failed_decode",
    "n_frames_failed_verify", "accepted_frame_fraction", "rejected_frame_fraction", "raw_ser", "raw_ber",
    "post_ir_ser", "post_ir_ber", "leak_EC_actual_bits", "leak_EC_per_frame",
    "leak_EC_per_input_bit", "beta_eff_empirical", "runtime_s", "throughput_input_bits_per_s",
    "throughput_output_bits_per_s", "notes", "backend_status", "error_message",
    "real_ir_success", "success_classification",
]


FRAME_COLUMNS = [
    "dataset_id", "method", "frame_idx", "decode_success", "verify_success", "raw_frame_ser",
    "raw_frame_ber", "post_frame_ser", "post_frame_ber", "leak_bits_frame", "iterations_used", "runtime_ms",
]


def _cfg_from_method(method_cfg: dict[str, Any], dataset_cfg: dict[str, Any], batch: FrameBatch) -> IRRunConfig:
    method = str(method_cfg.get("method") or method_cfg.get("name"))
    variant = str(method_cfg.get("method_variant") or method_cfg.get("variant") or method_cfg.get("mapping") or "default")
    return IRRunConfig(
        method=method,
        method_variant=variant,
        dimension=int(method_cfg.get("dimension") or dataset_cfg.get("dimension") or batch.dimension),
        frame_len_symbols=int(method_cfg.get("frame_len_symbols") or dataset_cfg.get("frame_len_symbols") or batch.frame_len_symbols),
        max_iter=int(method_cfg.get("max_iter", 0)),
        qber_estimate=method_cfg.get("qber_estimate"),
        ser_estimate=method_cfg.get("ser_estimate"),
        verify_mode=str(method_cfg.get("verify_mode", "crc32")),
        notes=method_cfg.get("notes"),
    )


def _load_batches(dataset_cfg: dict[str, Any]) -> list[FrameBatch]:
    if "frame_batch_path" in dataset_cfg:
        batches = table_to_frame_batches(read_table(Path(dataset_cfg["frame_batch_path"])), dataset_cfg.get("dataset_id"))
        max_frames = int(dataset_cfg.get("max_frames_per_dataset") or 0)
        out: list[FrameBatch] = []
        for batch in batches:
            if max_frames > 0 and int(batch.alice_symbols.shape[0]) > max_frames:
                batch = FrameBatch(
                    batch.dataset_id,
                    batch.alice_symbols[:max_frames].copy(),
                    batch.bob_symbols[:max_frames].copy(),
                    batch.dimension,
                    batch.frame_len_symbols,
                    dict(batch.metadata),
                )
                batch.metadata["frames_used_cap"] = max_frames
            batch.metadata.setdefault("source_path", str(dataset_cfg["frame_batch_path"]))
            batch.metadata.setdefault("data_mode", "real_data")
            out.append(batch)
        return out
    return [_load_batch(dataset_cfg)]


def _load_batch(dataset_cfg: dict[str, Any]) -> FrameBatch:
    if "frame_batch_path" in dataset_cfg:
        batch = table_to_frame_batch(read_table(Path(dataset_cfg["frame_batch_path"])), dataset_cfg.get("dataset_id"))
        batch.metadata.setdefault("source_path", str(dataset_cfg["frame_batch_path"]))
        batch.metadata.setdefault("data_mode", "real_data")
        return batch
    path = Path(dataset_cfg["path"])
    df = load_pairs_table(path)
    batch = build_frame_batch(
        df,
        dataset_id=str(dataset_cfg.get("dataset_id") or path.stem),
        dimension=int(dataset_cfg["dimension"]),
        frame_len_symbols=int(dataset_cfg["frame_len_symbols"]),
    )
    batch.metadata["source_path"] = str(path)
    return batch


def _run_method(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
    try:
        if cfg.method == "polar_existing":
            return run_polar_existing(batch, cfg)
        if cfg.method == "cascade_lite":
            return run_cascade_lite(batch, cfg)
        if cfg.method == "layered_ldpc_lite":
            return run_layered_ldpc_lite(batch, cfg)
        if cfg.method == "qldpc_reference":
            return run_qldpc_reference(batch, cfg)
        raise ValueError(f"unknown method: {cfg.method}")
    except NotImplementedError as exc:
        if cfg.method == "cascade_lite":
            return cascade_unavailable(batch, cfg, str(exc))
        if cfg.method == "layered_ldpc_lite":
            return ldpc_unavailable(batch, cfg, str(exc))
        raise


def _correct_execution_status(result: IRRunResult, proposed_status: str) -> str:
    if result.method == "polar_existing":
        return proposed_status
    if result.method == "qldpc_reference" and proposed_status == "reference":
        return "reference"
    if proposed_status in {"unavailable", "stub"}:
        return proposed_status
    if result.method not in {"cascade_lite", "layered_ldpc_lite", "qldpc_reference"}:
        return proposed_status
    attempted = int(result.n_frames_attempted or 0)
    success = int(result.n_frames_success or 0)
    failed_decode = int(result.n_frames_failed_decode or 0)
    try:
        raw_ser = float(result.raw_ser)
        post_ser = float(result.post_ir_ser)
    except Exception:
        raw_ser = float("nan")
        post_ser = float("nan")
    worsened = math.isfinite(raw_ser) and math.isfinite(post_ser) and post_ser > raw_ser
    if attempted > 0 and worsened:
        return "experimental_failed"
    if attempted > 0 and success > 0 and (not math.isfinite(raw_ser) or not math.isfinite(post_ser) or post_ser <= raw_ser):
        return "ok" if result.method != "qldpc_reference" else proposed_status
    if attempted > 0 and success == 0 and failed_decode >= attempted:
        return "decode_failed" if result.method != "qldpc_reference" else proposed_status
    if attempted > 0 and success == 0:
        return "no_verified_success" if result.method != "qldpc_reference" else proposed_status
    if proposed_status == "ok":
        return "experimental_failed"
    return proposed_status


def _result_row(result: IRRunResult, batch: FrameBatch) -> dict[str, Any]:
    row = asdict(result)
    meta = dict(row.pop("metadata", {}) or {})
    out = {c: None for c in RESULT_COLUMNS}
    out.update(row)
    out.update({k: batch.metadata.get(k) for k in [
        "data_mode", "source_path", "loss_db", "bin_width_ps", "n_eff_pairs", "processing_rule_version",
        "pairing_path_tag", "threshold_ps", "effective_pairing_window_ps",
    ]})
    if not out.get("data_mode"):
        out["data_mode"] = "real_data" if ("polar_results_root" in batch.metadata or "polar_existing_output" in batch.metadata or "polar_results_file" in batch.metadata) else "synthetic"
    out["dimension"] = int(batch.dimension)
    out["source_path"] = meta.get("source_path", out.get("source_path"))
    out["method_status"] = _correct_execution_status(result, meta.get("method_status", "ok"))
    out["notes"] = meta.get("notes") or meta.get("error_message") or ""
    out["backend_status"] = meta.get("backend_status", "")
    out["error_message"] = meta.get("error_message", "")

    # Classify success
    from ..metrics.success import classify_real_ir_success_row
    real_success, classification = classify_real_ir_success_row(out)
    out["real_ir_success"] = real_success
    out["success_classification"] = classification

    return {c: out.get(c) for c in RESULT_COLUMNS}



def _frame_rows(batch: FrameBatch, result: IRRunResult) -> list[dict[str, Any]]:
    explicit = result.metadata.get("frame_results") if isinstance(result.metadata, dict) else None
    if isinstance(explicit, list):
        return [{c: row.get(c) for c in FRAME_COLUMNS} for row in explicit if isinstance(row, dict)]
    rows = []
    leak_per_frame = result.leak_EC_per_frame if result.n_frames_attempted else 0.0
    for i in range(int(batch.alice_symbols.shape[0])):
        a = batch.alice_symbols[i]
        b = batch.bob_symbols[i]
        raw_ser = frame_symbol_error_rate(a, b)
        raw_ber = bit_error_rate(flatten_bits(a, batch.dimension), flatten_bits(b, batch.dimension))
        rows.append({
            "dataset_id": batch.dataset_id,
            "method": result.method,
            "frame_idx": i,
            "decode_success": bool(i < result.n_frames_success),
            "verify_success": bool(i < result.n_frames_success),
            "raw_frame_ser": raw_ser,
            "raw_frame_ber": raw_ber,
            "post_frame_ser": 0.0 if i < result.n_frames_success else raw_ser,
            "post_frame_ber": 0.0 if i < result.n_frames_success else raw_ber,
            "leak_bits_frame": leak_per_frame,
            "iterations_used": 0,
            "runtime_ms": (1000.0 * result.runtime_s / max(1, result.n_frames_attempted)) if result.n_frames_attempted else 0.0,
        })
    return rows


def benchmark_one_dataset(dataset_cfg: dict, method_cfg: dict, global_cfg: dict) -> pd.DataFrame:
    batch = _load_batch(dataset_cfg)
    batch.metadata.update({k: v for k, v in dataset_cfg.items() if k not in {"path", "frame_batch_path"}})
    batch.metadata.update({f"method_cfg_{k}": v for k, v in method_cfg.items()})
    for key, value in method_cfg.items():
        batch.metadata[key] = value
    cfg = _cfg_from_method(method_cfg, dataset_cfg, batch)
    result = _run_method(batch, cfg)
    return pd.DataFrame([_result_row(result, batch)])


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root()), text=True).strip()
    except Exception:
        return "unknown"


def _backend_availability() -> dict[str, str]:
    import importlib.util
    names = ["cascade", "cascade_cpp", "cascade_python", "ldpc", "sim_ldpc", "quantumgizmos_ldpc", "yaml", "pyarrow"]
    return {name: "available" if importlib.util.find_spec(name) else "missing" for name in names}


def _is_polar_results_only_dataset(dataset_cfg: dict[str, Any], methods: list[Any]) -> bool:
    if not ("polar_results_root" in dataset_cfg or "polar_existing_output" in dataset_cfg or "polar_results_file" in dataset_cfg):
        return False
    if "path" in dataset_cfg or "frame_batch_path" in dataset_cfg:
        return False
    method_names = {str(m.get("method") or m.get("name")) for m in methods if isinstance(m, dict)}
    return method_names == {"polar_existing"}


def _benchmark_polar_results_only(dataset_cfg: dict[str, Any], method_cfg: dict[str, Any]) -> pd.DataFrame:
    metadata = dict(dataset_cfg)
    metadata.update({k: v for k, v in method_cfg.items() if k.startswith("polar_")})
    selected = resolve_polar_output_from_metadata(metadata)
    if selected is None:
        raise FileNotFoundError(f"No readable polar output found for {metadata.get('polar_results_root') or metadata.get('polar_existing_output')}")
    variant = str(method_cfg.get("method_variant") or "read_existing")
    dataset_id = dataset_cfg.get("dataset_id")
    rows = benchmark_rows_from_polar_output(selected, dataset_id=dataset_id, method_variant=variant)
    return rows


def _run_one_benchmark_task(dataset_cfg: dict[str, Any], batch: FrameBatch, method_cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    local_batch = FrameBatch(batch.dataset_id, batch.alice_symbols, batch.bob_symbols, batch.dimension, batch.frame_len_symbols, dict(batch.metadata))
    for key, value in method_cfg.items():
        local_batch.metadata[key] = value
    ir_cfg = _cfg_from_method(method_cfg, dataset_cfg, local_batch)
    result = _run_method(local_batch, ir_cfg)
    return _result_row(result, local_batch), _frame_rows(local_batch, result)


def benchmark_from_yaml(config_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = load_config(Path(config_path))
    global_cfg = dict(cfg.get("global", {}) or {})
    out_dir = Path(global_cfg.get("output_dir") or default_output_dir())
    if not out_dir.is_absolute():
        out_dir = repo_root() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    result_rows = []
    frame_rows_all = []
    methods = as_list(cfg.get("methods"))
    tasks: list[tuple[dict[str, Any], FrameBatch, dict[str, Any]]] = []
    for dataset_cfg in as_list(cfg.get("datasets")):
        if _is_polar_results_only_dataset(dataset_cfg, methods):
            result_rows.extend(_benchmark_polar_results_only(dataset_cfg, methods[0]).to_dict("records"))
            continue
        for batch in _load_batches(dataset_cfg):
            batch.metadata.update({k: v for k, v in dataset_cfg.items() if k not in {"path", "frame_batch_path"} and v is not None})
            for method_cfg in methods:
                tasks.append((dataset_cfg, batch, method_cfg))
    max_workers = int(global_cfg.get("max_workers") or 1)
    if max_workers > 1 and len(tasks) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_one_benchmark_task, dataset_cfg, batch, method_cfg) for dataset_cfg, batch, method_cfg in tasks]
            for future in as_completed(futures):
                row, frames = future.result()
                result_rows.append(row)
                frame_rows_all.extend(frames)
    else:
        for dataset_cfg, batch, method_cfg in tasks:
            row, frames = _run_one_benchmark_task(dataset_cfg, batch, method_cfg)
            result_rows.append(row)
            frame_rows_all.extend(frames)
    result_df = add_fraction_columns(pd.DataFrame(result_rows, columns=RESULT_COLUMNS))
    from ..metrics.success import add_success_columns
    result_df = add_success_columns(result_df)
    result_df = result_df[RESULT_COLUMNS]

    frame_df = pd.DataFrame(frame_rows_all, columns=FRAME_COLUMNS)
    result_csv = out_dir / "ir_benchmark_results.csv"
    frame_path = out_dir / "ir_frame_results.parquet"
    write_table(result_df, result_csv)
    write_table(frame_df, frame_path)
    manifest = {
        "git_commit": _git_commit(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "comparison_bench_version": __version__,
        "benchmark_config_path": str(config_path),
        "benchmark_config_snapshot": cfg,
        "third_party_backend_availability": _backend_availability(),
        "outputs": {"results_csv": str(result_csv), "frame_results": str(frame_path)},
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return result_df, frame_df
