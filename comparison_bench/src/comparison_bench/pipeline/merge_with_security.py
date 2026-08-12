from __future__ import annotations

from pathlib import Path

import pandas as pd


def merge_ir_with_security(ir_csv: Path, security_csv: Path, out_csv: Path) -> pd.DataFrame:
    ir = pd.read_csv(ir_csv)
    sec = pd.read_csv(security_csv)
    candidates = ["dataset_id", "loss_db", "dimension", "bin_width_ps", "threshold_ps", "effective_pairing_window_ps"]
    keys = [c for c in candidates if c in ir.columns and c in sec.columns]
    if not keys:
        raise ValueError("No common join keys between IR and security CSV")
    merged = ir.merge(sec, on=keys, how="left", suffixes=("", "_security"))
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, index=False)
    return merged
