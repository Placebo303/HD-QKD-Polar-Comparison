"""V22b high-degree structured DE gate (diagnostic).

Uses the V22b wrapper around V14 MC-DE with a raised degree cap so q=1024
high-rate ensembles (check degree >64) can be evaluated on the structured
channel.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .nonbinary_v10_common import concentrated_check_distribution
from .nonbinary_v22b_mcde import run_mcde_high_degree

__all__ = ["run_v22b_de_gate"]


def _rho_for_rate(rate: float, lam: Mapping[int, float]) -> dict[int, float]:
    conc = concentrated_check_distribution(rate, lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    return {d: w for d, w in rho.items() if w > 0.0}


def run_v22b_de_gate(*, q: int, w: Any, rate: float,
                     candidates: Sequence[Mapping[int, float]],
                     n_samples: int = 100, max_iter: int = 10,
                     seed: int = 2026099001, degree_max: int = 128,
                     out_dir: str | Path | None = None) -> dict:
    w = np.asarray(w, dtype=np.float64)
    rows = []
    started = time.monotonic()
    for lam in candidates:
        lam = {int(k): float(v) for k, v in lam.items()}
        # Normalize sum exactly for the frozen structural checks.
        key = max(lam, key=lambda k: lam[k])
        lam[key] += 1.0 - sum(lam.values())
        rho = _rho_for_rate(rate, lam)
        try:
            res = run_mcde_high_degree(
                q=q, lambda_edge=lam, rho_edge=rho,
                n_samples=n_samples, max_iter=max_iter, seed=seed,
                channel_mode="structured", w=w, degree_max=degree_max)
            rows.append({
                "lambda_edge": lam,
                "rho_edge": rho,
                "converged": bool(res.get("converged")),
                "iterations": int(res.get("iterations")) if res.get("iterations") is not None else None,
                "final_entropy": None if res.get("final_entropy") is None else float(res["final_entropy"]),
            })
        except Exception as exc:
            rows.append({
                "lambda_edge": lam,
                "rho_edge": rho,
                "converged": False,
                "error": str(exc),
            })
    doc = {
        "schema": "nbldpc_v22b_de_gate_v1",
        "q": int(q),
        "rate": float(rate),
        "n_samples": int(n_samples),
        "max_iter": int(max_iter),
        "seed": int(seed),
        "degree_max": int(degree_max),
        "n_candidates": len(rows),
        "candidates": rows,
        "gate_passed": any(r.get("converged") for r in rows),
        "wall_seconds": round(time.monotonic() - started, 4),
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "de_gate.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
