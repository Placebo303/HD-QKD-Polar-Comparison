from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..io.dataset_builder import build_frame_batch
from ..methods.qldpc_reference import run_qldpc_reference
from ..sweep.common import crop_batch, expand_grid, load_batches_from_frame_batch, load_cfg, output_dir_from_cfg, point_filter
from ..sweep.rows import method_frame_rows, method_result_row
from ..sweep.runtime import append_error, append_frame_rows, append_rows, elapsed, read_existing_keys, stable_param_hash, sweep_paths, write_manifest
from ..types import FrameBatch, IRRunConfig


RESULT_COLUMNS = [
    "dataset_id", "data_mode", "dimension", "bin_width_ps", "q", "frame_len_symbols", "frame_cap", "frames_used_actual",
    "decoder", "channel_model", "check_fraction", "row_weight", "max_iter", "method", "method_status", "backend_status",
    "n_frames_attempted", "n_frames_success", "n_frames_failed_decode", "n_frames_failed_verify", "accepted_frame_fraction",
    "raw_ser", "post_ir_ser", "leak_EC_actual_bits", "leak_EC_per_input_bit", "beta_eff_empirical", "runtime_s", "notes", "param_hash",
    "real_ir_success", "success_classification",
]



def _synthetic_batch(q: int, ser: float, frame_len_symbols: int, n_frames: int, seed: int) -> FrameBatch:
    rng = np.random.default_rng(seed)
    n = int(frame_len_symbols) * int(n_frames)
    alice = rng.integers(0, q, size=n, dtype=np.int64)
    bob = alice.copy()
    flip = rng.random(n) < float(ser)
    if np.any(flip):
        offsets = rng.integers(1, q, size=int(np.count_nonzero(flip)), dtype=np.int64)
        bob[flip] = (bob[flip] + offsets) % q
    df = pd.DataFrame({
        "frame_id": np.repeat(np.arange(n_frames), frame_len_symbols),
        "pair_idx": np.tile(np.arange(frame_len_symbols), n_frames),
        "alice_symbol": alice,
        "bob_symbol": bob,
        "dimension": q,
        "n_eff_pairs": n,
        "processing_rule_version": "synthetic_qary_symmetric_v3",
        "pairing_path_tag": "synthetic",
        "data_mode": "synthetic",
    })
    batch = build_frame_batch(df, f"qldpc_synth_q{q}_ser{str(ser).replace('.', 'p')}_flen{frame_len_symbols}", q, frame_len_symbols)
    batch.metadata["data_mode"] = "synthetic"
    batch.metadata["source_path"] = "synthetic_generator"
    return batch


def _job(batch: FrameBatch, params: dict[str, Any], frame_cap: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    local = crop_batch(batch, frame_cap)
    local.metadata.update(params)
    local.metadata["qldpc_mode"] = "reference"
    cfg = IRRunConfig(
        method="qldpc_reference",
        method_variant="qary_ldpc_v3",
        dimension=int(local.dimension),
        frame_len_symbols=int(local.frame_len_symbols),
        max_iter=int(params["max_iter"]),
        verify_mode="crc32",
    )
    result = run_qldpc_reference(local, cfg)
    param_hash = stable_param_hash({"method": "qldpc_reference", "frame_cap": frame_cap, **params})
    row = method_result_row(local, result, {
        "q": int(local.dimension),
        "frame_cap": frame_cap,
        "frames_used_actual": int(local.alice_symbols.shape[0]),
        "decoder": params["decoder"],
        "channel_model": params["channel_model"],
        "check_fraction": params["check_fraction"],
        "row_weight": params["row_weight"],
        "max_iter": params["max_iter"],
        "param_hash": param_hash,
    })
    frames = method_frame_rows(local, result, {
        "q": int(local.dimension),
        "frame_cap": frame_cap,
        "decoder": params["decoder"],
        "channel_model": params["channel_model"],
        "check_fraction": params["check_fraction"],
        "row_weight": params["row_weight"],
        "max_iter": params["max_iter"],
        "param_hash": param_hash,
    })
    diagnostics = [dict(frame) for frame in frames]
    return row, frames, diagnostics


def main() -> int:
    ap = argparse.ArgumentParser(description="Run resumable qLDPC parameter sweep.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    start = time.perf_counter()
    cfg = load_cfg(Path(args.config))
    out_dir = output_dir_from_cfg(cfg)
    paths = sweep_paths(out_dir)
    sweep_cfg = dict(cfg.get("qldpc", {}) or {})
    result_path = out_dir / "qldpc_param_sweep_results.csv"
    frame_path = out_dir / "qldpc_param_sweep_frame_results.parquet"
    diag_path = out_dir / "qldpc_decoder_diagnostics.csv"
    existing = read_existing_keys(result_path, ["dataset_id", "method", "param_hash", "frame_cap"])
    grid = expand_grid({
        "check_fraction": sweep_cfg.get("check_fraction", [0.50]),
        "row_weight": sweep_cfg.get("row_weight", [4]),
        "max_iter": sweep_cfg.get("max_iter", [20]),
        "decoder": sweep_cfg.get("decoder", ["qary_hard_syndrome_bf"]),
        "channel_model": sweep_cfg.get("channel_model", ["qary_symmetric"]),
        "seed": sweep_cfg.get("seed", [0]),
    })
    frame_caps = [int(x) for x in sweep_cfg.get("frame_caps", [4])]

    batches: list[FrameBatch] = []
    synth = dict(cfg.get("synthetic", {}) or {})
    for q in [int(x) for x in synth.get("q_values", [4, 8, 16, 32])]:
        for ser in [float(x) for x in synth.get("ser_values", [0.01, 0.03, 0.05, 0.08])]:
            for frame_len in [int(x) for x in synth.get("frame_len_symbols", [64, 128])]:
                batches.append(_synthetic_batch(q, ser, frame_len, int(synth.get("n_frames", 8)), int(synth.get("seed", 1234))))

    if "realdata" in cfg:
        real_cfg = dict(cfg.get("realdata", {}) or {})
        real_batches = load_batches_from_frame_batch(real_cfg["frame_batch_path"])
        allowed_dims = [int(x) for x in real_cfg.get("dimensions", [4, 8, 16, 32, 64])]
        allowed_bw = [int(x) for x in real_cfg.get("bin_width_ps", [100, 120, 150, 180])]
        for batch in real_batches:
            if point_filter(batch, allowed_dims, allowed_bw):
                batches.append(batch)

    tasks = []
    for batch in batches:
        for frame_cap in frame_caps:
            for params in grid:
                if int(batch.dimension) > int(sweep_cfg.get("max_q_for_realdata", 256)) and batch.metadata.get("data_mode") == "real_data":
                    continue
                param_hash = stable_param_hash({"method": "qldpc_reference", "frame_cap": frame_cap, **params})
                key = (str(batch.dataset_id), "qldpc_reference", param_hash, str(frame_cap))
                if not bool(sweep_cfg.get("force", False)) and key in existing:
                    continue
                tasks.append((batch, params, frame_cap, param_hash))

    completed = []
    failed = []
    max_workers = int(sweep_cfg.get("max_workers", 8))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_job, batch, params, frame_cap): (batch, params, frame_cap, param_hash) for batch, params, frame_cap, param_hash in tasks}
        for future in as_completed(future_map):
            batch, params, frame_cap, param_hash = future_map[future]
            try:
                row, frames, diagnostics = future.result()
                append_rows(result_path, [row], RESULT_COLUMNS)
                append_frame_rows(frame_path, frames)
                append_rows(diag_path, diagnostics)
                completed.append(f"{batch.dataset_id}:{param_hash}")
            except Exception as exc:
                append_error(paths, stage="qldpc_param_sweep", dataset_id=batch.dataset_id, dimension=batch.dimension,
                             bin_width_ps=batch.metadata.get("bin_width_ps"), method="qldpc_reference",
                             method_variant="qary_ldpc_v3", frame_cap=frame_cap, param_hash=param_hash, exc=exc, status="failed")
                failed.append(f"{batch.dataset_id}:{param_hash}")
    write_manifest(
        out_dir / "ir_v3_run_manifest.json",
        config=cfg,
        completed_stages=["qldpc_param_sweep"] if completed else [],
        failed_stages=["qldpc_param_sweep"] if failed else [],
        output_files={
            "qldpc_param_sweep_results.csv": str(result_path),
            "qldpc_param_sweep_frame_results.parquet": str(frame_path),
            "qldpc_decoder_diagnostics.csv": str(diag_path),
            "run_errors_ir_v3.csv": str(paths.error_csv),
        },
        runtime_total_s=elapsed(start),
        notes=f"qldpc tasks={len(tasks)} batches={len(batches)}",
        stage_name="qldpc_param_sweep",
    )
    print(f"qldpc sweep complete: tasks={len(tasks)} completed={len(completed)} failed={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
