"""Route B M2 skeleton — structured-channel DE harness (engineering only).

Imports frozen V14 structured-channel model read-only. No production run yet.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import nonbinary_v14_channel as v14
from . import nonbinary_v10_de as de

SCHEMA = "nbldpc_v18_b2_structured_de_plan_v1"


def build_m2_plan(*, q_small: int = 16, seed: int = 2026081603) -> dict:
    """Draft M2 plan. Not frozen; M1 must pass before this becomes a gate."""
    return {
        "schema": SCHEMA,
        "stage": "m2_structured_de_prep",
        "q_small": q_small,
        "seed": seed,
        "reuse": {
            "v14_channel": "nonbinary_v14_channel",
            "de_search": "nonbinary_v10_de.run_de_search",
        },
        "gate_dependency": "V18-B1 M1 reproduction PASS",
        "execute_policy": "not authorized until M1 replay complete",
    }


def run_smoke(*, q: int = 8, out_dir: str | Path | None = None,
              seed: int = 2026081605, n_samples: int = 1000,
              max_iter: int = 10) -> dict:
    """Small structured-channel MC-DE smoke using a tiny regular config.

    This validates the M2 harness plumbing; it is not a production gate.
    """
    import numpy as np
    from . import nonbinary_v14_mcde as v14mcde
    from . import nonbinary_v9_common as common

    lam = {2: 0.5, 3: 0.5}
    conc = common.concentrated_check_distribution(0.5, lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    w = np.full(q, 0.05)
    w[0] = 0.65
    run = v14mcde.run_mcde(q, lam, rho, n_samples=n_samples, max_iter=max_iter,
                           seed=seed, channel_mode="structured", w=w)
    doc = {
        "schema": "nbldpc_v18_b2_structured_de_smoke_v1",
        "q": q,
        "seed": seed,
        "run": run,
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "smoke.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
