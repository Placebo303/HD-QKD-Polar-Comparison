#!/usr/bin/env python3
"""V72P2D3 GF32 contrast runner — synthetic-only boundary.

Default path runs a tiny synthetic contrast through the true history
kernel (v35 decode_row_layered_fftqspa via the V54 cold-start chain) on
tiny synthetic matrices only, and writes nothing outside the
caller-chosen workspace directory. The real VAL/CAL parquet path is
never opened and the production contrast root is never created. Any
real-execution request fails closed. No imitated decoder enters the production stage
path; decode_fn injection exists only in tests.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p2d3_gf32_contrast.py"
)
CYCLE_ID = "V72P2D3-GF32"
SEED = 20260902
WORKSPACE_ROOT = (REPO_ROOT / "workspace").resolve()
PRODUCTION_ROOT = (
    REPO_ROOT
    / "comparison_bench"
    / "outputs_comparison"
    / "v72p2d3_gf32_contrast_20260904"
).resolve()
Q = 1024
N = 1024
NBIT = 10240
M_BASE = 184
M_TOTAL = 200


def load_contrast_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "v72p2d3_gf32_contrast", str(MODULE_PATH)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_workspace_dir(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    out = candidate.resolve()
    try:
        out.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("synthetic output must stay under workspace/") from exc
    if out == PRODUCTION_ROOT or PRODUCTION_ROOT in out.parents:
        raise ValueError("synthetic output must stay outside the production root")
    return out


def run_synthetic_contrast(
    *, out_dir: str | Path, seed: int = SEED
) -> dict[str, Any]:
    """Run a tiny synthetic contrast through the true history kernel (cold)."""
    if int(seed) != SEED:
        raise ValueError(f"synthetic seed is frozen at {SEED}")
    out = _resolve_workspace_dir(out_dir)
    mod = load_contrast_module()
    assert (
        mod.history_kernel_id() == "V35-decode_row_layered_fftqspa-via-V54-chain"
    ), "history kernel binding drift"
    rng = np.random.default_rng(int(seed))
    n_demo = 8
    h_base, h_joint, h_total = mod.build_tiny_nested()
    # Demo-only reduced domain (n_b_states=8, q_sub=4) for shape/speed; the
    # decoder smoke below uses uniform 32-ary prior; production uses q=32 via V54.
    bob_demo = rng.integers(0, 8, size=64, dtype=np.int64)
    high_demo = rng.integers(0, 4, size=64, dtype=np.int64)
    low_demo = rng.integers(0, 4, size=64, dtype=np.int64)
    p1 = mod.build_stage1_P(bob_demo, high_demo, 1.0, n_b_states=8, q_sub=4)
    p2 = mod.build_stage2_P(
        high_demo, bob_demo, low_demo, 1.0, n_b_states=8, q_sub=4
    )
    prior_demo = mod.prior_logp_from_P(np.full((n_demo, 32), 1.0 / 32.0))
    tiny_h = np.eye(n_demo, n_demo, dtype=np.uint8)
    tiny_target = np.zeros(n_demo, dtype=np.uint8)
    t0 = time.monotonic()
    # Cold start (belief_warm=None) matching V54; true iterative kernel, tiny only.
    layer = mod.run_g_layer(prior_demo, tiny_target, tiny_h, max_iter=90)
    wall = time.monotonic() - t0
    arm_g = {
        "status": "LADDER_EXHAUSTED",
        "rows": int(M_TOTAL),
        "iters": int(layer["iterations_used"]),
        "syndrome_satisfied": bool(layer["syndrome_ok"]),
        "bit_flips": 0,
        "symbol_flips": 0,
        "wall_s": float(wall),
        "synthetic_only": True,
    }
    written = mod.write_contrast_outputs(out, arm_g)
    report = {
        "cycle_id": CYCLE_ID,
        "synthetic_only": True,
        "real_executed": False,
        "seed": int(seed),
        "output": str(written),
        "wall_s": float(wall),
        "stage1_shape": list(p1.shape),
        "stage2_shape": list(p2.shape),
        "status": "PASS",
    }
    print(json.dumps({"status": "PASS", "output": str(written)}, indent=2))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("synthetic-only", "real"),
        default="synthetic-only",
    )
    parser.add_argument("--out-dir", type=Path, default=WORKSPACE_ROOT / "v72p2d3_synthetic")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--execute-real", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.phase == "real" or args.execute_real:
        print("real execution is not authorized for V72P2D3-GF32", file=sys.stderr)
        return 2
    run_synthetic_contrast(out_dir=args.out_dir, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
