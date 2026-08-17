"""V22 SC-LDPC DE gate using the frozen V11 coupled MC-DE kernel (diagnostic).

This is the paper-faithful SC-LDPC gate: it runs the frozen V11 terminated-chain
MC-DE for the archived V10 winners and frozen geometries.  It uses the QSC
reference first; structured-channel adaptation is a later step.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import nonbinary_v10_common as common
from .nonbinary_v11_mcde import (
    FROZEN_GEOMETRIES,
    V10_WINNER_S1,
    V10_WINNER_S1_RATE,
    V10_WINNER_S3,
    V10_WINNER_S3_RATE,
    run_coupled_mcde,
)

__all__ = ["run_v22_sc_de_gate"]
def _num_or_none(x):
    return None if x is None else float(x)




def _rho_for_rate(rate: float, lambda_edge: Mapping[int, float]) -> dict[int, float]:
    conc = common.concentrated_check_distribution(rate, lambda_edge)
    return {int(conc["dc_lo"]): float(conc["w_lo"]),
            int(conc["dc_hi"]): float(conc["w_hi"])}


def run_v22_sc_de_gate(*, q: int = 1024, p: float, n_samples: int = 200,
                       max_iter: int = 20, seed: int = 2026095001,
                       out_dir: str | Path | None = None) -> dict:
    """Run SC-LDPC DE gate for the two frozen winners and three geometries."""
    candidates = [
        ("S1", V10_WINNER_S1, V10_WINNER_S1_RATE),
        ("S3", V10_WINNER_S3, V10_WINNER_S3_RATE),
    ]
    rows = []
    started = time.monotonic()
    for name, lam, rate in candidates:
        rho = _rho_for_rate(rate, lam)
        for gname, gparams in FROZEN_GEOMETRIES.items():
            try:
                res = run_coupled_mcde(
                    q=q, lambda_edge=lam, rho_edge=rho, p=p,
                    L=gparams["L"], w=gparams["w"], W=gparams["W"],
                    n_samples=n_samples, max_iter=max_iter, seed=seed)
                rows.append({
                    "candidate": name,
                    "geometry": gname,
                    "rate": float(rate),
                    "converged": bool(res.get("converged")),
                    "iterations": int(res.get("iterations")) if res.get("iterations") is not None else None,
                    "final_entropy": _num_or_none(res.get("final_entropy")),
                    "error_prob": _num_or_none(res.get("error_prob")),
                })
            except Exception as exc:  # diagnostic fail-closed
                rows.append({
                    "candidate": name,
                    "geometry": gname,
                    "rate": float(rate),
                    "converged": False,
                    "error": str(exc),
                })
    doc = {
        "schema": "nbldpc_v22_sc_de_gate_v1",
        "q": int(q),
        "p": float(p),
        "n_samples": int(n_samples),
        "max_iter": int(max_iter),
        "seed": int(seed),
        "n_rows": len(rows),
        "rows": rows,
        "gate_passed": any(r.get("converged") for r in rows),
        "wall_seconds": round(time.monotonic() - started, 4),
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "sc_de_gate.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
