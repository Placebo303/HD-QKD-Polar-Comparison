from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ..methods.cascade_lite import run_cascade_lite
from ..sweep.common import crop_batch, dataset_row, expand_grid, load_batches_from_frame_batch, load_cfg, output_dir_from_cfg, representative_batches
from ..sweep.rows import method_frame_rows, method_result_row
from ..sweep.runtime import append_error, append_frame_rows, append_rows, elapsed, read_existing_keys, stable_param_hash, sweep_paths, write_manifest
from ..types import IRRunConfig, FrameBatch


RESULT_COLUMNS = [
    "dataset_id", "dimension", "bin_width_ps", "frame_cap", "frames_used_actual", "method", "method_status",
    "backend_status", "block_size_schedule", "num_passes", "permutation_mode", "seed",
    "n_frames_attempted", "n_frames_success", "n_frames_failed_decode", "n_frames_failed_verify",
    "accepted_frame_fraction", "raw_ser", "post_ir_ser", "leak_EC_actual_bits", "leak_EC_per_input_bit",
    "beta_eff_empirical", "runtime_s", "notes", "param_hash", "real_ir_success", "success_classification",
]



def _job(batch: FrameBatch, params: dict[str, Any], frame_cap: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    local = crop_batch(batch, frame_cap)
    local.metadata.update(params)
    local.metadata["mapping"] = str(params.get("mapping", "gray"))
    local.metadata["block_size_schedule"] = params["block_size_schedule"]
    cfg = IRRunConfig(
        method="cascade_lite",
        method_variant=str(params.get("mapping", "gray")),
        dimension=int(local.dimension),
        frame_len_symbols=int(local.frame_len_symbols),
        max_iter=0,
        verify_mode=str(params.get("verify_mode", "crc32")),
    )
    result = run_cascade_lite(local, cfg)
    param_hash = stable_param_hash({"method": "cascade_lite", "frame_cap": frame_cap, **params})
    row = method_result_row(local, result, {
        "frame_cap": frame_cap,
        "frames_used_actual": int(local.alice_symbols.shape[0]),
        "block_size_schedule": ",".join(str(x) for x in params["block_size_schedule"]),
        "num_passes": params["num_passes"],
        "permutation_mode": params["permutation_mode"],
        "seed": params["seed"],
        "param_hash": param_hash,
    })
    frames = method_frame_rows(local, result, {
        "frame_cap": frame_cap,
        "block_size_schedule": ",".join(str(x) for x in params["block_size_schedule"]),
        "num_passes": params["num_passes"],
        "permutation_mode": params["permutation_mode"],
        "seed": params["seed"],
        "param_hash": param_hash,
    })
    leakage_diag = [dict(frame) for frame in frames]
    return row, frames, leakage_diag


def main() -> int:
    ap = argparse.ArgumentParser(description="Run resumable cascade parameter sweep.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    start = time.perf_counter()
    cfg = load_cfg(Path(args.config))
    out_dir = output_dir_from_cfg(cfg)
    paths = sweep_paths(out_dir)
    sweep_cfg = dict(cfg.get("cascade", {}) or {})
    batches = load_batches_from_frame_batch(cfg["dataset"]["frame_batch_path"])
    batches = representative_batches(batches, include_all=bool(sweep_cfg.get("include_all_points", False)))
    grid = expand_grid({
        "block_size_schedule": sweep_cfg.get("block_size_schedule", [[8, 16, 32, 64]]),
        "num_passes": sweep_cfg.get("num_passes", [4]),
        "permutation_mode": sweep_cfg.get("permutation_mode", ["seeded_random"]),
        "seed": sweep_cfg.get("seed", [0]),
        "mapping": sweep_cfg.get("mapping", ["gray"]),
        "bisection_mode": sweep_cfg.get("bisection_mode", ["recursive_binary"]),
        "verify_mode": sweep_cfg.get("verify_mode", ["crc32"]),
    })
    frame_caps = [int(x) for x in sweep_cfg.get("frame_caps", [4])]
    result_path = out_dir / "cascade_param_sweep_results.csv"
    frame_path = out_dir / "cascade_param_sweep_frame_results.parquet"
    diag_path = out_dir / "cascade_leakage_diagnostics.csv"
    existing = read_existing_keys(result_path, ["dataset_id", "method", "param_hash", "frame_cap"])
    tasks = []
    for batch in batches:
        for frame_cap in frame_caps:
            for params in grid:
                param_hash = stable_param_hash({"method": "cascade_lite", "frame_cap": frame_cap, **params})
                key = (str(batch.dataset_id), "cascade_lite", param_hash, str(frame_cap))
                if not bool(sweep_cfg.get("force", False)) and key in existing:
                    continue
                tasks.append((batch, params, frame_cap, param_hash))

    completed = []
    failed = []
    max_workers = int(sweep_cfg.get("max_workers", 16))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_job, batch, params, frame_cap): (batch, params, frame_cap, param_hash) for batch, params, frame_cap, param_hash in tasks}
        for future in as_completed(future_map):
            batch, params, frame_cap, param_hash = future_map[future]
            try:
                row, frames, leakage_diag = future.result()
                append_rows(result_path, [row], RESULT_COLUMNS)
                append_frame_rows(frame_path, frames)
                append_rows(diag_path, leakage_diag)
                completed.append(f"{batch.dataset_id}:{param_hash}")
            except Exception as exc:
                append_error(paths, stage="cascade_param_sweep", dataset_id=batch.dataset_id, dimension=batch.dimension,
                             bin_width_ps=batch.metadata.get("bin_width_ps"), method="cascade_lite",
                             method_variant="cascade_v3", frame_cap=frame_cap, param_hash=param_hash, exc=exc, status="failed")
                failed.append(f"{batch.dataset_id}:{param_hash}")
    write_manifest(
        out_dir / "ir_v3_run_manifest.json",
        config=cfg,
        completed_stages=["cascade_param_sweep"] if completed else [],
        failed_stages=["cascade_param_sweep"] if failed else [],
        output_files={
            "cascade_param_sweep_results.csv": str(result_path),
            "cascade_param_sweep_frame_results.parquet": str(frame_path),
            "cascade_leakage_diagnostics.csv": str(diag_path),
            "run_errors_ir_v3.csv": str(paths.error_csv),
        },
        runtime_total_s=elapsed(start),
        notes=f"cascade tasks={len(tasks)} representative_points={len(batches)}",
        stage_name="cascade_param_sweep",
    )
    print(f"cascade sweep complete: tasks={len(tasks)} completed={len(completed)} failed={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
