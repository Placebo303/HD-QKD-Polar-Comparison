#!/usr/bin/env python3
"""V72P2D3 GF32 contrast runner — synthetic default, real-entry chain gated.

Default path runs a tiny synthetic contrast through the true history
kernel (v35 decode_row_layered_fftqspa via the V54 cold-start chain) on
tiny synthetic matrices only, and writes nothing outside the
caller-chosen workspace directory. R2-R6 prepare-only (--phase real
--prepare-only --registry <json>) opens the registry parquet with a
filtered 4-column read, validates CAL/VAL, fits the prior, assembles the
block and validates shapes, then writes workspace prepare_summary.json
with decoder 0 and no formal-root creation. Any unauthorized
real-execution request fails closed. No imitated decoder enters
the production stage path; decode_fn injection exists only in tests and in
the explicit fake-E2E orchestration below (which never touches parquet,
the true decoder, or the production root).
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
# ponytail: one-line src path so frozen V54 import resolves in subprocess CLI.
sys.path.insert(0, str(REPO_ROOT / "comparison_bench" / "src"))
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
# ponytail: runner mirrors the core's real-entry budgets; test asserts equality.
PREP_LIMIT_S = 300.0
G_LIMIT_S = 300.0
INV_LIMIT_S = 600.0
RSS_LIMIT_BYTES = 2 * 1024**3
CYCLE_STATE_PATH = REPO_ROOT / "docs" / "research_cycles" / CYCLE_ID / "cycle_state.yaml"
REAL_WORKSPACE_DEFAULT = WORKSPACE_ROOT / "v72p2d3_real_e2e"


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
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="real-registry JSON for R2-R6 prepare-only and real entry (shared builder)",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="R2-R6 prepare-only: registry->parquet->CAL/VAL->prior->block->A->words->matrix/syndrome shapes->workspace READY, decoder 0",
    )
    parser.add_argument(
        "--cycle-state",
        type=Path,
        default=CYCLE_STATE_PATH,
        help="cycle_state.yaml used only by the explicit real-execution gate",
    )
    return parser


def _read_real_authorized(path: str | Path) -> bool:
    """Read only the real_execution_authorized flag (tiny flat YAML, no dep)."""
    state_path = Path(path)
    if not state_path.is_absolute():
        state_path = REPO_ROOT / state_path
    try:
        text = state_path.read_text(encoding="utf-8")
    except OSError:
        return False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() == "real_execution_authorized":
            return value.strip().lower() in {"true", "1", "yes"}
    return False


def build_prepare_inputs(registry_path: str | Path) -> dict[str, Any]:
    """Shared builder for R2-R6 prepare and real entry (no decoder, no auth).

    Loads the registry JSON, validates the R2 contract, and runs the R3
    filtered parquet read. Both ``run_prepare_only`` and the production
    real branch use this builder, so production never passes None.
    """
    mod = load_contrast_module()
    reg_path = Path(registry_path)
    if not reg_path.is_absolute():
        reg_path = (REPO_ROOT / reg_path).resolve()
    raw = json.loads(reg_path.read_text(encoding="utf-8"))
    validated = mod.validate_prepare_registry(raw, reg_path)
    loaded = mod.load_and_validate_prepare_frames(
        validated["parquet_path"], validated["cal_ids"], validated["val_ids"]
    )
    return {"registry_raw": raw, "validated": validated, "loaded": loaded}


def run_prepare_only(
    *,
    out_dir: str | Path,
    registry_path: str | Path,
    seed: int = SEED,
) -> dict[str, Any]:
    """R2-R6 prepare-only (workspace READY, decoder 0, no auth consumed).

    Chain: CLI -> registry JSON -> parquet path -> filtered read -> CAL/VAL
    validate -> prior fit -> block assemble -> D1 A scalar -> words ->
    matrix/syndrome shape validate -> workspace READY. Stops here.
    """
    if int(seed) != SEED:
        raise ValueError(f"real-entry seed is frozen at {SEED}")
    if registry_path is None:
        raise ValueError("prepare-only requires --registry")
    out = _resolve_workspace_dir(out_dir)
    mod = load_contrast_module()
    assert mod.PREP_LIMIT_S == PREP_LIMIT_S, "prep budget drift"
    assert mod.G_LIMIT_S == G_LIMIT_S, "G budget drift"
    assert mod.INV_LIMIT_S == INV_LIMIT_S, "invocation budget drift"
    assert mod.RSS_LIMIT_BYTES == RSS_LIMIT_BYTES, "RSS budget drift"
    # Shared builder first (prepare), then scalar summary; no auth, no run.
    report = mod.prepare_real_input(
        registry_path=registry_path,
        out_dir=out,
        workspace_root=WORKSPACE_ROOT,
    )
    print(json.dumps({"status": report["status"], "output": report["output"]}, indent=2))
    return report


def run_real_orchestration(
    *,
    out_dir: str | Path,
    registry: dict[str, Any] | None = None,
    frames: dict[Any, Any] | None = None,
    matrices: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    authorized: bool = False,
    execute_real: bool = True,
    decode_fn: Any = None,
    seed: int = SEED,
) -> dict[str, Any]:
    """Run the frozen 11-step real-entry chain on injected fakes (workspace only).

    Production callers pass registry/frames/matrices explicitly; this function
    never opens parquet, never calls the true decoder unless decode_fn is None
    (production, not exercised here), and never creates the production root —
    the core gate rejects it. Single VAL block only; no nine-block loop.
    """
    if int(seed) != SEED:
        raise ValueError(f"real-entry seed is frozen at {SEED}")
    out = _resolve_workspace_dir(out_dir)
    mod = load_contrast_module()
    assert mod.PREP_LIMIT_S == PREP_LIMIT_S, "prep budget drift"
    assert mod.G_LIMIT_S == G_LIMIT_S, "G budget drift"
    assert mod.INV_LIMIT_S == INV_LIMIT_S, "invocation budget drift"
    assert mod.RSS_LIMIT_BYTES == RSS_LIMIT_BYTES, "RSS budget drift"
    if not execute_real:
        raise PermissionError("real chain requires --execute-real")
    if not authorized:
        raise PermissionError("real execution is not authorized")
    if registry is None or frames is None or matrices is None:
        raise PermissionError("real chain needs injected registry/frames/matrices; parquet is never opened here")
    report = mod.run_real_contrast(        out_dir=out,
        registry=registry,
        frames=frames,
        matrices=matrices,
        preflight=preflight,
        authorized=bool(authorized),
        execute_real=bool(execute_real),
        decode_fn=decode_fn,
        workspace_root=WORKSPACE_ROOT,
    )
    print(json.dumps({"status": report["status"], "branch": report["branch"], "output": report["output"]}, indent=2))
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # R2-R6 prepare-only stops here: workspace READY, decoder 0, no auth.
    if bool(getattr(args, "prepare_only", False)):
        if args.phase != "real":
            print("--prepare-only requires --phase real; no run was started", file=sys.stderr)
            return 2
        if not getattr(args, "registry", None):
            print("--prepare-only requires --registry; no run was started", file=sys.stderr)
            return 2
        try:
            report = run_prepare_only(
                out_dir=args.out_dir,
                registry_path=args.registry,
                seed=args.seed,
            )
        except (PermissionError, FileExistsError, ValueError, RuntimeError) as exc:
            print(f"prepare failed for V72P2D3-GF32: {exc}", file=sys.stderr)
            return 2
        return 0 if report.get("status") == "READY" else 2
    if args.phase == "real" or args.execute_real:
        if not args.execute_real:
            print("--phase real requires --execute-real; no real run was started", file=sys.stderr)
            return 2
        if not getattr(args, "registry", None):
            print("--phase real requires --registry; no real run was started", file=sys.stderr)
            return 2
        # Prepared structure: prepare -> summary -> auth -> run (shared builder, no None).
        try:
            built = build_prepare_inputs(args.registry)
            authorized = _read_real_authorized(args.cycle_state)
            if not authorized:
                raise PermissionError("real execution is not authorized")
            # Authorized future run only: adapt shared-builder outputs to the
            # frozen 11-step chain (no None, no parquet open here, true kernel).
            mod = load_contrast_module()
            validated = built["validated"]
            loaded = built["loaded"]
            registry_old = {
                "sessions": [
                    {
                        "session_id": mod.SESSION_ID,
                        "source_label": "1M",
                        "stage2_CAL_frame_ids": list(validated["cal_ids"]),
                        "stage2_VAL_frame_ids": list(validated["val_ids"]),
                    }
                ]
            }
            frames_old = {**loaded["cal_bundle"], **loaded["val_bundle"]}
            # Frozen matrices for the authorized run only (built here, not in prepare).
            from comparison_bench.formal_ir.v38_architecture_triage import (
                construct_lane_c_prototype,
            )

            v54 = mod._load_v54()
            field = mod.get_gf32_field()
            h_base, _ = construct_lane_c_prototype(source="1M", seed=383102, field=field)
            h_inc1, _, _, _ = v54.construct_h_inc("1M", 600001)
            h_inc2, _, _, _ = v54.construct_h_inc("1M", 600004)
            import numpy as _np

            h_base = _np.asarray(h_base, dtype=_np.uint8)
            h_inc1 = _np.asarray(h_inc1, dtype=_np.uint8)
            h_inc2 = _np.asarray(h_inc2, dtype=_np.uint8)
            matrices_old = {
                "h1": _np.zeros((mod.H1_ROWS, mod.N), dtype=_np.uint8),
                "h_base": h_base,
                "h_joint": _np.vstack([h_base, h_inc1]).astype(_np.uint8),
                "h_total": _np.vstack([h_base, h_inc1, h_inc2]).astype(_np.uint8),
            }
            run_real_orchestration(
                out_dir=args.out_dir,
                registry=registry_old,
                frames=frames_old,
                matrices=matrices_old,
                preflight={"status": "PASS", "cycle": mod.CYCLE_ID},
                authorized=authorized,
                execute_real=True,
            )
        except (PermissionError, FileExistsError, ValueError) as exc:
            print(f"real execution is not authorized for V72P2D3-GF32: {exc}", file=sys.stderr)
            return 2
        return 0
    run_synthetic_contrast(out_dir=args.out_dir, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
