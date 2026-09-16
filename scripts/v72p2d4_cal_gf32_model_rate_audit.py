#!/usr/bin/env python3
"""V72P2D4 CAL GF32 model rate audit runner — CAL-only.

Reads a registry JSON, runs the CAL-only descriptive audit, writes the
four-file audit output to a fresh directory. Default output is the
pre-registered audit root; test runs use workspace directories.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "comparison_bench" / "src"))
MODULE_PATH = (
    REPO_ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p2d4_cal_gf32_model_rate_audit.py"
)
CYCLE_ID = "V72P2D4-CAL-GF32-MODEL-RATE"
WORKSPACE_ROOT = (REPO_ROOT / "workspace").resolve()
PRODUCTION_ROOT = (
    REPO_ROOT
    / "comparison_bench"
    / "outputs_comparison"
    / "v72p2d4_cal_gf32_model_rate_audit_20260905"
).resolve()
DEFAULT_LAM = 1.0
PREP_LIMIT_S = 300.0
G_LIMIT_S = 300.0
INV_LIMIT_S = 600.0
RSS_LIMIT_BYTES = 2 * 1024**3


def load_audit_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "v72p2d4_cal_gf32_model_rate_audit", str(MODULE_PATH)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--lam", type=float, default=DEFAULT_LAM)
    return parser


def run_audit(
    *, out_dir: str | Path, registry_path: str | Path, lam: float = DEFAULT_LAM
) -> dict[str, Any]:
    mod = load_audit_module()
    assert mod.CYCLE_ID == CYCLE_ID, "cycle binding drift"
    assert mod.PREP_LIMIT_S == PREP_LIMIT_S, "prep budget drift"
    assert mod.G_LIMIT_S == G_LIMIT_S, "audit budget drift"
    assert mod.INV_LIMIT_S == INV_LIMIT_S, "invocation budget drift"
    assert mod.RSS_LIMIT_BYTES == RSS_LIMIT_BYTES, "RSS budget drift"
    report = mod.run_cal_audit(
        registry_path=registry_path, out_dir=out_dir, lam=float(lam)
    )
    print(json.dumps({"status": report["status"], "output": report["output"]}, indent=2))
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        guard = load_audit_module()
        guard.validate_output_target(args.out_dir)
    except (ValueError, FileExistsError) as exc:
        print(f"output guard rejected for {CYCLE_ID}: {exc}", file=sys.stderr)
        return 2
    if not args.registry:
        print("--registry is required; no run was started", file=sys.stderr)
        return 2
    try:
        report = run_audit(
            out_dir=args.out_dir, registry_path=args.registry, lam=float(args.lam)
        )
    except (FileExistsError, ValueError, RuntimeError, TimeoutError, MemoryError) as exc:
        print(f"audit failed for {CYCLE_ID}: {exc}", file=sys.stderr)
        return 2
    return 0 if report.get("status") == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
