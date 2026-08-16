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
