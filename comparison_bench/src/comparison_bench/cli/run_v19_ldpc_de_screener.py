"""V19 per-plane BSC DE-gated LDPC screener (diagnostic).

For each V17 Gray bit-plane, find regular (dv,dc) LDPC ensembles whose DE
threshold exceeds the plane's BSC crossover and whose rate is close to the
f~1.3 target. Uses the frozen q=2 DE threshold function from nonbinary_v7_r2_de.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ..formal_ir import nonbinary_v7_r2_de as v7de
from ..formal_ir.nonbinary_v18_b2_structured_de import _V17_PER_PLANE_ERROR
from .run_v19_channel_scoping import h2


def candidates_for_target(m_target: int, n: int, dv_range=(2, 6), dc_max: int = 13):
    target_ratio = m_target / n
    out = []
    for dv in range(dv_range[0], dv_range[1] + 1):
        for dc in range(dv + 1, dc_max + 1):
            ratio = dv / dc
            if abs(ratio - target_ratio) / max(target_ratio, 1e-9) > 0.25:
                continue
            m_actual = round(n * ratio)
            out.append((dv, dc, m_actual, ratio))
    # sort by closeness to target m
    out.sort(key=lambda x: abs(x[2] - m_target))
    return out


def run_screener(*, n: int = 2048, overhead: float = 1.3,
                 n_samples: int = 2000, max_iter: int = 300,
                 p_tol: float = 0.002, top_k: int = 6) -> dict:
    min_m = math.ceil(math.log2(n))
    rows = []
    for plane, p in enumerate(_V17_PER_PLANE_ERROR):
        m_target = max(min_m, math.ceil(n * h2(float(p)) * overhead))
        cands = candidates_for_target(m_target, n)
        selected = None
        evaluated = 0
        for dv, dc, m_actual, ratio in cands[:top_k]:
            try:
                thr = v7de.binary_bsc_threshold(dv, dc, n_samples=n_samples,
                                                max_iter=max_iter, p_tol=p_tol)
            except Exception:
                continue
            evaluated += 1
            if thr > float(p):
                selected = {
                    "dv": dv, "dc": dc, "m_actual": m_actual,
                    "threshold": thr, "target_m": m_target, "p": float(p),
                }
                break
        rows.append({
            "plane_id": plane,
            "p": float(p),
            "h2": float(h2(float(p))),
            "target_m": m_target,
            "target_rate": (n - m_target) / n,
            "evaluated_candidates": evaluated,
            "selected": selected,
            "status": "ok" if selected is not None else "no_regular_ensemble_found",
        })
    total_m = sum(r["selected"]["m_actual"] for r in rows if r["selected"] is not None)
    # for missing, count target_m as fallback? We report both.
    total_m_with_fallback = sum((r["selected"] or {"m_actual": r["target_m"]})["m_actual"] for r in rows)
    return {
        "schema": "nbldpc_v19_ldpc_de_screener_v1",
        "n": n,
        "overhead": overhead,
        "h_full_q1024": float(sum(h2(float(p)) for p in _V17_PER_PLANE_ERROR)),
        "rows": rows,
        "total_m_selected": total_m,
        "total_m_with_fallback": total_m_with_fallback,
        "f_selected": total_m / (n * sum(h2(float(p)) for p in _V17_PER_PLANE_ERROR)),
        "f_with_fallback": total_m_with_fallback / (n * sum(h2(float(p)) for p in _V17_PER_PLANE_ERROR)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--overhead", type=float, default=1.3)
    ap.add_argument("--n-samples", type=int, default=2000)
    ap.add_argument("--max-iter", type=int, default=300)
    args = ap.parse_args()
    doc = run_screener(n=args.n, overhead=args.overhead, n_samples=args.n_samples,
                       max_iter=args.max_iter)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ldpc_de_screener.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
