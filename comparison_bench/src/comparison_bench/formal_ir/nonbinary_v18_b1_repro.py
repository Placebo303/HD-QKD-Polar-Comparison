"""Route B M0 — small-q DE reproduction harness (diagnostic/gate engineering).

Reuses existing frozen DE/MC-DE assets; does not modify them.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import nonbinary_v10_de as de
from . import nonbinary_v8_mcde as v8

SCHEMA = "nbldpc_v18_b1_repro_v1"
SMOKE_Q = 4
SMOKE_RATE = 0.75
SMOKE_P_GATE = 0.069
SMOKE_SEED = 20260816


def run_smoke(q: int = SMOKE_Q, out_dir: str | Path | None = None,
              seed: int = SMOKE_SEED) -> dict:
    """Run a tiny DE search smoke. Writes a repro JSON if out_dir is given."""
    out = Path(out_dir) if out_dir is not None else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
    result = de.run_de_search(
        q=q, p_gate=SMOKE_P_GATE, rate=SMOKE_RATE, search_seed=seed,
        pop_size=8, max_gen=2, f=0.85, cr=0.7,
        n_samples=2000, max_iter=30, entropy_tol=0.01, streak=20,
        threshold_p_lo=0.01, threshold_p_hi=0.12, threshold_p_tol=0.0025,
        compute_threshold=True,
        out_dir=None if out is None else str(out / "de_search"),
    )
    doc = {
        "schema": SCHEMA,
        "mode": "smoke",
        "q": q,
        "rate": SMOKE_RATE,
        "p_gate": SMOKE_P_GATE,
        "seed": seed,
        "result": result,
    }
    if out is not None:
        (out / "repro.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
