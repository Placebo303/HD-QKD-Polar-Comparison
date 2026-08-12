from __future__ import annotations

import pandas as pd
import numpy as np
from comparison_bench.src.comparison_bench.metrics.success import classify_real_ir_success_row, add_success_columns

def test_success_classification_scenarios():
    # 1. Executable success (cascade_lite)
    row_success = {
        "method": "cascade_lite",
        "method_status": "ok",
        "n_frames_attempted": 4,
        "n_frames_success": 4,
        "n_frames_failed_decode": 0,
        "n_frames_failed_verify": 0,
        "raw_ber": 0.05,
        "post_ir_ber": 0.0,
        "leak_EC_actual_bits": 128,
        "beta_eff_empirical": 0.85,
    }
    real_success, classification = classify_real_ir_success_row(row_success)
    assert real_success is True
    assert classification == "real_ir_success"

    # 2. Unverified improvement
    row_unverified = {
        "method": "cascade_lite",
        "method_status": "no_verified_success",
        "n_frames_attempted": 4,
        "n_frames_success": 2,
        "n_frames_failed_decode": 2,
        "n_frames_failed_verify": 0,
        "raw_ber": 0.05,
        "post_ir_ber": 0.02, # improved but not all verified
        "leak_EC_actual_bits": 64,
        "beta_eff_empirical": 0.85,
    }
    real_success, classification = classify_real_ir_success_row(row_unverified)
    assert real_success is False
    assert classification == "decode_improved_but_unverified"

    # 3. Decode failure
    row_decode_failed = {
        "method": "layered_ldpc_lite",
        "method_status": "decode_failed",
        "n_frames_attempted": 4,
        "n_frames_success": 0,
        "n_frames_failed_decode": 4,
        "n_frames_failed_verify": 0,
        "raw_ber": 0.1,
        "post_ir_ber": 0.1,
        "leak_EC_actual_bits": 128,
        "beta_eff_empirical": 0.85,
    }
    real_success, classification = classify_real_ir_success_row(row_decode_failed)
    assert real_success is False
    assert classification == "decode_failed"

    # 4. Verification failure
    row_verify_failed = {
        "method": "layered_ldpc_lite",
        "method_status": "no_verified_success",
        "n_frames_attempted": 4,
        "n_frames_success": 3,
        "n_frames_failed_decode": 0,
        "n_frames_failed_verify": 1,
        "raw_ber": 0.05,
        "post_ir_ber": 0.0,
        "leak_EC_actual_bits": 128,
        "beta_eff_empirical": 0.85,
    }
    real_success, classification = classify_real_ir_success_row(row_verify_failed)
    assert real_success is False
    assert classification == "verified_failure"

    # 5. Reference implementation
    row_reference = {
        "method": "qldpc_reference",
        "method_status": "reference",
        "n_frames_attempted": 4,
        "n_frames_success": 4,
        "n_frames_failed_decode": 0,
        "n_frames_failed_verify": 0,
        "raw_ber": 0.05,
        "post_ir_ber": 0.0,
    }
    real_success, classification = classify_real_ir_success_row(row_reference)
    assert real_success is False
    assert classification == "reference_only"

    # 6. Invalid accounting
    row_invalid_leakage = {
        "method": "cascade_lite",
        "method_status": "ok",
        "n_frames_attempted": 4,
        "n_frames_success": 4,
        "n_frames_failed_decode": 0,
        "n_frames_failed_verify": 0,
        "raw_ber": 0.05,
        "post_ir_ber": 0.0,
        "leak_EC_actual_bits": float("nan"),
        "beta_eff_empirical": 0.85,
    }
    real_success, classification = classify_real_ir_success_row(row_invalid_leakage)
    assert real_success is False
    assert classification == "invalid_accounting"

    # 7. Method unavailable
    row_unavailable = {
        "method": "cascade_lite",
        "method_status": "unavailable",
        "n_frames_attempted": 0,
        "n_frames_success": 0,
    }
    real_success, classification = classify_real_ir_success_row(row_unavailable)
    assert real_success is False
    assert classification == "method_unavailable"


def test_add_success_columns_dataframe():
    df = pd.DataFrame([
        {
            "method": "cascade_lite",
            "method_status": "ok",
            "n_frames_attempted": 4,
            "n_frames_success": 4,
            "n_frames_failed_decode": 0,
            "n_frames_failed_verify": 0,
            "raw_ber": 0.05,
            "post_ir_ber": 0.0,
            "leak_EC_actual_bits": 128,
            "beta_eff_empirical": 0.85,
        },
        {
            "method": "qldpc_reference",
            "method_status": "reference",
            "n_frames_attempted": 4,
            "n_frames_success": 4,
            "n_frames_failed_decode": 0,
            "n_frames_failed_verify": 0,
            "raw_ber": 0.05,
            "post_ir_ber": 0.0,
        }
    ])
    res_df = add_success_columns(df)
    assert "real_ir_success" in res_df.columns
    assert "success_classification" in res_df.columns
    assert bool(res_df.iloc[0]["real_ir_success"]) is True
    assert res_df.iloc[0]["success_classification"] == "real_ir_success"
    assert bool(res_df.iloc[1]["real_ir_success"]) is False
    assert res_df.iloc[1]["success_classification"] == "reference_only"

