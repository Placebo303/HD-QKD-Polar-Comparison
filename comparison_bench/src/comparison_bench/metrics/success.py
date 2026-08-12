from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def classify_real_ir_success_row(row: Any) -> tuple[bool, str]:
    """Classifies a single benchmark run result row.
    
    Returns a tuple: (real_ir_success: bool, success_classification: str)
    """
    method = row.get("method")
    status = row.get("method_status")
    
    if pd.isna(method) or method is None:
        return False, "method_unavailable"

    # 1. Check if method is unavailable or stub
    if status in ("unavailable", "stub"):
        return False, "method_unavailable"

    # 2. Check reference status
    # Reference-grade methods (like qldpc_reference) should be marked reference_only
    if method == "qldpc_reference" or status == "reference":
        return False, "reference_only"

    # 3. Retrieve frame metrics
    try:
        attempted = int(row.get("n_frames_attempted") or 0)
        success = int(row.get("n_frames_success") or 0)
        failed_decode = int(row.get("n_frames_failed_decode") or 0)
        failed_verify = int(row.get("n_frames_failed_verify") or 0)
    except (TypeError, ValueError):
        attempted = 0
        success = 0
        failed_decode = 0
        failed_verify = 0

    if attempted <= 0:
        return False, "decode_failed"

    # 4. Check for invalid or missing leakage accounting on executable methods
    if method in ("cascade_lite", "layered_ldpc_lite"):
        leak_bits = row.get("leak_EC_actual_bits")
        if pd.isna(leak_bits) or leak_bits is None or float(leak_bits) < 0:
            return False, "invalid_accounting"
        
        # Verify beta_eff_empirical is present if raw_ber is positive
        beta_eff = row.get("beta_eff_empirical")
        raw_ber = row.get("raw_ber")
        try:
            if raw_ber is not None and float(raw_ber) > 0:
                if pd.isna(beta_eff) or beta_eff is None:
                    return False, "invalid_accounting"
        except (TypeError, ValueError):
            pass


    # 5. Check if all attempted frames were successfully decoded and verified
    if failed_verify > 0:
        return False, "verified_failure"

    if success == attempted and attempted > 0:
        return True, "real_ir_success"

    # 6. Check for decode improvement but verification failure
    try:
        raw_ber = float(row.get("raw_ber") or 0.0)
        post_ber = float(row.get("post_ir_ber") or 0.0)
        improved = post_ber < raw_ber
    except (TypeError, ValueError):
        improved = False

    if improved and success < attempted:
        return False, "decode_improved_but_unverified"

    if failed_decode >= attempted or success == 0:
        return False, "decode_failed"

    return False, "verified_failure"


def add_success_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Adds real_ir_success and success_classification columns to a DataFrame."""
    out = df.copy()
    if out.empty:
        out["real_ir_success"] = pd.Series(dtype=bool)
        out["success_classification"] = pd.Series(dtype=str)
        return out

    # Drop if already exist to prevent duplicate columns during concat
    to_drop = [c for c in ["real_ir_success", "success_classification"] if c in out.columns]
    if to_drop:
        out = out.drop(columns=to_drop)

    results = []
    for _, row in out.iterrows():
        real_success, classification = classify_real_ir_success_row(row)
        results.append({"real_ir_success": real_success, "success_classification": classification})
        
    res_df = pd.DataFrame(results, index=out.index)
    return pd.concat([out, res_df], axis=1)
