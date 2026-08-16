"""V19 channel-aware scoping: per-bit-plane binary-MLC ideal leakage vs folded q-ary DE.

This is a draft diagnostic that quantifies why Route B M2 plain NB-LDPC struggled:
per-plane binary coding can in principle approach channel entropy (f~1), while a
single q-ary syndrome over all 10 Gray bit-planes pays a much larger cost.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from ..formal_ir import codebook_v4
from ..formal_ir import nonbinary_v18_b2_structured_de as v18


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def compute_scoping() -> dict:
    per_plane = list(v18._V17_PER_PLANE_ERROR)
    per_plane_h2 = [h2(float(x)) for x in per_plane]
    w = v18.build_real_w_q1024()
    with np.errstate(divide="ignore"):
        h_full = float(-np.sum(w * np.log2(np.where(w > 0.0, w, 1.0))))
    ideal_sum_h2 = float(sum(per_plane_h2))
    n = codebook_v4.BLOCK_LENGTH
    h1_rows = list(codebook_v4.ROW_COUNTS)
    h2_rows = [16, 16, 16, 24, 24, 32, 48, 80, 88, 48]
    existing_v4_h1_f = float(sum(h1_rows) / n / h_full)
    existing_v5_h1_h2_f = float((sum(h1_rows) + sum(h2_rows)) / n / h_full)
    return {
        "schema": "nbldpc_v19_channel_scoping_v1",
        "per_plane_error": per_plane,
        "per_plane_h2": per_plane_h2,
        "h_full_q1024": h_full,
        "sum_h2_per_plane": ideal_sum_h2,
        "ideal_binary_mlc_f": ideal_sum_h2 / h_full if h_full else None,
        "existing_binary_v4_h1_f": existing_v4_h1_f,
        "existing_binary_v5_h1_h2_f": existing_v5_h1_h2_f,
        "note": "Per-plane binary MLC ideal leakage equals channel entropy when V17 independent bit-plane model holds; this is the target direction for f~1.3.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    doc = compute_scoping()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "channel_scoping.json"
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
