"""V22 structured-construction DE gate (diagnostic).

This is the first V22 gate: it evaluates candidate degree distributions on the
V17 structured channel using the existing structured MC-DE backend.  It is not
yet a full MET/protograph/SC-LDPC DE; it establishes the gate harness and
pre-registered candidates.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .nonbinary_v18_b2_structured_de import evaluate_candidate_structured

__all__ = ["run_v22_de_gate"]


def _normalize_lambda(lam: Mapping[int, float]) -> dict[int, float]:
    """Force floating sum to exactly 1.0 by adjusting the largest weight."""
    out = {int(k): float(v) for k, v in lam.items()}
    if not out:
        return out
    key = max(out, key=lambda k: out[k])
    out[key] += 1.0 - sum(out.values())
    return out


def _candidate_doc(lam: Mapping[int, float], rec: Any) -> dict:
    return {
        "lambda_edge": {int(k): float(v) for k, v in lam.items()},
        "entropy_converged": bool(getattr(rec, "entropy_converged", False)),
        "converged_iter": int(getattr(rec, "converged_iter", -1)),
        "final_entropy": float(getattr(rec, "final_entropy", -1.0)),
        "penalty": float(getattr(rec, "penalty", 0.0)),
    }


def run_v22_de_gate(*, q: int, w: Any, rate: float,
                    candidates: Sequence[Mapping[int, float]],
                    n_samples: int = 800, max_iter: int = 30,
                    seed: int = 2026092001,
                    out_dir: str | Path | None = None) -> dict:
    """Run V22 DE gate over a fixed candidate list."""
    w = np.asarray(w, dtype=np.float64)
    rows = []
    started = time.monotonic()
    for lam in candidates:
        lam_norm = _normalize_lambda(lam)
        rec = evaluate_candidate_structured(
            lam_norm,
            q=q, rate=rate, w=w, seed=seed,
            n_samples=n_samples, max_iter=max_iter)
        rows.append(_candidate_doc(lam_norm, rec))
    doc = {
        "schema": "nbldpc_v22_de_gate_v1",
        "q": int(q),
        "rate": float(rate),
        "n_samples": int(n_samples),
        "max_iter": int(max_iter),
        "seed": int(seed),
        "n_candidates": len(rows),
        "candidates": rows,
        "gate_passed": any(r["entropy_converged"] for r in rows),
        "wall_seconds": round(time.monotonic() - started, 4),
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "de_gate.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
