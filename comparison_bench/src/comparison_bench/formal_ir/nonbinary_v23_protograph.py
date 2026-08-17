"""V23 protograph base-matrix DE scan (diagnostic).

Derives edge-perspective degree distributions from a protograph base matrix and
runs the V22b high-degree structured MC-DE at q=1024.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .nonbinary_v18_b2_structured_de import build_folded_w, build_real_w_q1024
from .nonbinary_v22b_mcde import run_mcde_high_degree

__all__ = ["base_matrix_to_distributions", "run_protograph_de_scan"]


def base_matrix_to_distributions(B: Sequence[Sequence[int]]) -> dict:
    """Return {lambda_edge, rho_edge, rate} for a protograph base matrix."""
    B = np.asarray(B, dtype=np.int64)
    if B.ndim != 2:
        raise ValueError("base matrix must be 2-D")
    m_p, n_p = B.shape
    if B.sum() == 0:
        raise ValueError("base matrix must have at least one edge")
    var_deg = B.sum(axis=0)
    chk_deg = B.sum(axis=1)
    E = int(B.sum())
    lambda_edge: dict[int, float] = {}
    for d in set(int(v) for v in var_deg if v > 0):
        cnt = int(np.sum(var_deg == d))
        lambda_edge[d] = float(d * cnt) / E
    rho_edge: dict[int, float] = {}
    for d in set(int(v) for v in chk_deg if v > 0):
        cnt = int(np.sum(chk_deg == d))
        rho_edge[d] = float(d * cnt) / E
    rate = 1.0 - float(m_p) / float(n_p)
    return {"lambda_edge": lambda_edge, "rho_edge": rho_edge,
            "rate": float(rate), "base_matrix": B.tolist(),
            "m_p": int(m_p), "n_p": int(n_p)}


def run_protograph_de_scan(*, q: int = 1024, base_matrices: Sequence[Sequence[Sequence[int]]],
                           n_samples: int = 200, max_iter: int = 50,
                           seed: int = 2026099001, degree_max: int = 512,
                           out_dir: str | Path | None = None) -> dict:
    """Scan protograph base matrices on the structured channel."""
    w = np.asarray(build_real_w_q1024() if int(q) == 1024 else build_folded_w(int(q)),
                  dtype=np.float64)
    rows = []
    started = time.monotonic()
    for idx, B in enumerate(base_matrices):
        try:
            meta = base_matrix_to_distributions(B)
            lam = meta["lambda_edge"]
            rho = meta["rho_edge"]
            res = run_mcde_high_degree(
                q=q, lambda_edge=lam, rho_edge=rho,
                n_samples=n_samples, max_iter=max_iter, seed=seed,
                channel_mode="structured", w=w, degree_max=degree_max)
            rows.append({
                "index": idx,
                "base_matrix": meta["base_matrix"],
                "rate": meta["rate"],
                "lambda_edge": lam,
                "rho_edge": rho,
                "converged": bool(res.get("converged")),
                "iterations": int(res.get("iterations")) if res.get("iterations") is not None else None,
                "final_entropy": None if res.get("final_entropy") is None else float(res["final_entropy"]),
            })
        except Exception as exc:
            rows.append({"index": idx, "base_matrix": [list(r) for r in B],
                         "converged": False, "error": str(exc)})
    doc = {
        "schema": "nbldpc_v23_protograph_de_scan_v1",
        "q": int(q), "n_samples": int(n_samples), "max_iter": int(max_iter),
        "seed": int(seed), "degree_max": int(degree_max),
        "n_matrices": len(rows), "rows": rows,
        "gate_passed": any(r.get("converged") for r in rows),
        "wall_seconds": round(time.monotonic() - started, 4),
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "scan.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
    return doc
