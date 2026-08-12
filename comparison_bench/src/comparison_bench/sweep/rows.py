from __future__ import annotations

from typing import Any

import pandas as pd

from ..metrics.summary import add_fraction_columns
from ..types import FrameBatch, IRRunResult


def method_result_row(batch: FrameBatch, result: IRRunResult, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = dict(result.metadata or {})
    row = {
        "dataset_id": batch.dataset_id,
        "data_mode": batch.metadata.get("data_mode", "real_data"),
        "source_path": batch.metadata.get("source_path"),
        "loss_db": batch.metadata.get("loss_db"),
        "dimension": int(batch.dimension),
        "bin_width_ps": batch.metadata.get("bin_width_ps"),
        "frame_len_symbols": int(batch.frame_len_symbols),
        "frame_len_bits": int(result.frame_len_bits),
        "method": result.method,
        "method_variant": result.method_variant,
        "method_status": meta.get("method_status", "ok"),
        "backend_status": meta.get("backend_status", ""),
        "n_frames_total": int(result.n_frames_total),
        "n_frames_attempted": int(result.n_frames_attempted),
        "n_frames_success": int(result.n_frames_success),
        "n_frames_failed_decode": int(result.n_frames_failed_decode),
        "n_frames_failed_verify": int(result.n_frames_failed_verify),
        "raw_ser": result.raw_ser,
        "raw_ber": result.raw_ber,
        "post_ir_ser": result.post_ir_ser,
        "post_ir_ber": result.post_ir_ber,
        "leak_EC_actual_bits": result.leak_EC_actual_bits,
        "leak_EC_per_frame": result.leak_EC_per_frame,
        "leak_EC_per_input_bit": result.leak_EC_per_input_bit,
        "beta_eff_empirical": result.beta_eff_empirical,
        "runtime_s": result.runtime_s,
        "notes": meta.get("notes", ""),
    }

    # Classify success for parameter sweep result row
    from ..metrics.success import classify_real_ir_success_row
    real_success, classification = classify_real_ir_success_row(row)
    row["real_ir_success"] = real_success
    row["success_classification"] = classification

    if extra:
        row.update(extra)
    return add_fraction_columns(pd.DataFrame([row])).iloc[0].to_dict()



def method_frame_rows(batch: FrameBatch, result: IRRunResult, extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = []
    for row in list(result.metadata.get("frame_results", [])) if isinstance(result.metadata, dict) else []:
        merged = dict(row)
        merged.setdefault("dataset_id", batch.dataset_id)
        merged.setdefault("method", result.method)
        merged.setdefault("dimension", int(batch.dimension))
        merged.setdefault("bin_width_ps", batch.metadata.get("bin_width_ps"))
        merged.setdefault("data_mode", batch.metadata.get("data_mode", "real_data"))
        if extra:
            merged.update(extra)
        rows.append(merged)
    return rows
