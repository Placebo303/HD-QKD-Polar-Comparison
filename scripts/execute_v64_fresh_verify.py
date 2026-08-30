"""V64 fresh 36-block guarded runner — 72-144 calls hard cap 144, single 64-bit dual-tag, additive run_01."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v64_full_symbol_verification import (  # noqa: E402
    ACCEPTED_PLAN_SHA,
    BLOCK_LENGTH,
    HARD_CAP,
    OUTPUT_ROOT,
    PAIRS_PER_BLOCK,
    SCOPED_TRACKED_PATHS,
    V64CallAccounting,
    build_instrumented_record,
    build_v64_fresh_registry,
    classify_fresh_block,
    reconstruct_v64_matrices,
    verify_dual,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/v64_fresh_registry.json"

def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run V64 fresh 36-block verification (72-144 calls hard cap 144, dual-tag single 64b).")
    p.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization flag")
    p.add_argument("--authorized-target-sha", default=None, help="Full 40-char implementation SHA (must equal HEAD, origin, ACCEPTED_PLAN_SHA)")
    p.add_argument("--output-root", default=None, help="Override output root (tests only)")
    p.add_argument("--fake-runner", action="store_true", help="Use fake runner for tests (no real decoder)")
    return p.parse_args(argv)

def _check_git(authorized: str) -> None:
    if authorized != ACCEPTED_PLAN_SHA:
        print(f"BLOCKED: authorized {authorized} != ACCEPTED_PLAN_SHA {ACCEPTED_PLAN_SHA}", file=sys.stderr)
        sys.exit(2)
    if len(authorized) != 40:
        print("BLOCKED: --authorized-target-sha must be 40-char", file=sys.stderr)
        sys.exit(2)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        origin = subprocess.check_output(["git", "rev-parse", "origin/formal-ir-mainline"], text=True).strip()
    except Exception as exc:
        print(f"BLOCKED: git rev-parse failed: {exc}", file=sys.stderr)
        sys.exit(2)
    if head != authorized:
        print(f"BLOCKED: HEAD {head} != authorized {authorized}", file=sys.stderr)
        sys.exit(2)
    if origin != authorized:
        print(f"BLOCKED: origin {origin} != authorized {authorized}", file=sys.stderr)
        sys.exit(2)
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    except Exception as exc:
        print(f"BLOCKED: git status failed: {exc}", file=sys.stderr)
        sys.exit(2)
    dirty = [line for line in out.splitlines() if any(p in line for p in SCOPED_TRACKED_PATHS)]
    if dirty:
        print(f"BLOCKED: SCOPED dirty {dirty}", file=sys.stderr)
        sys.exit(2)

def _preflight(output_root: Path, fake_runner: bool) -> list[dict]:
    # G1-G5 checks: registry K2>=36, matrices, held-out parquet reachable, no synthetic fallback
    try:
        reg = build_v64_fresh_registry()
    except ValueError as exc:
        raise RuntimeError(f"EVIDENCE_INVALID registry: {exc}") from exc
    if len(reg) != 36:
        raise RuntimeError(f"EVIDENCE_INVALID registry len {len(reg)} !=36")
    # matrix frozen check (decoder-free)
    try:
        reconstruct_v64_matrices()
    except Exception as exc:
        raise RuntimeError(f"EVIDENCE_INVALID matrices: {exc}") from exc
    # held-out parquet existence (no synthetic fallback)
    if not fake_runner:
        for src in ("1M", "1p5M", "2M"):
            for key in ["type2_1M_20260121_184040/pairs.parquet", "type2_1p5M_20260121_183806/pairs.parquet", "type2_2M_20260121_183657/pairs.parquet"]:
                p = REPO_ROOT / f"comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/{key}"
                if not p.is_file():
                    raise RuntimeError(f"EVIDENCE_INVALID held-out parquet missing {p}")
    return reg

def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha required", file=sys.stderr)
        return 2
    _check_git(args.authorized_target_sha)
    output_root = Path(args.output_root) if args.output_root else OUTPUT_ROOT
    if output_root.exists():
        print(f"BLOCKED: output root already exists: {output_root}", file=sys.stderr)
        return 2
    # preflight before creating root
    try:
        registry = _preflight(output_root, fake_runner=bool(args.fake_runner))
    except RuntimeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    # create root only after all guards pass, before first decode
    output_root.mkdir(parents=True, exist_ok=False)
    # write registry authoritatively inside run_01 if not already at canonical path
    try:
        (output_root / "v64_fresh_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except Exception:
        pass
    (output_root / "v64_records.json").write_text("[]", encoding="utf-8")
    acct = V64CallAccounting(hard_cap=HARD_CAP)
    records: list[dict] = []
    t0 = time.time()
    try:
        if args.fake_runner:
            # fake: 36 blocks, each 2 calls (L1+base) deterministic fake records, stay within 72
            for ent in registry:
                acct.register_start("l1"); acct.register_complete("l1")
                acct.register_start("base"); acct.register_complete("base")
                import numpy as np
                s_true = np.arange(1024, dtype=np.int64) % 1024
                from comparison_bench.formal_ir.v64_full_symbol_verification import decompose_symbols
                u1_t, u2_t = decompose_symbols(s_true)
                rec = build_instrumented_record(ent["block_id"], ent["source"], ent["frame_ids"], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2)
                rec["decoder_calls"] = 2
                rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
                rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
                rec["pairs_count"] = PAIRS_PER_BLOCK
                rec["sampling_mode"] = ent["sampling_mode"]
                # add missing fields for spec
                rec["block_seed"] = ent["block_id"]
                records.append(rec)
        else:
            # Real decode path would reuse V63 decoder per block (not implemented here for plan phase)
            # For implementation phase, this branch enforces real wiring without extra calls
            raise RuntimeError("real decoder execution requires authorized run; fake_runner not set but guarded path incomplete")
        # validate budget
        errs = acct.validate()
        if errs:
            raise RuntimeError(f"budget validate failed {errs}")
        if acct.completed < 72 or acct.completed > 144:
            raise RuntimeError(f"budget total {acct.completed} not in 72-144")
        # write records
        (output_root / "v64_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        import csv
        if records:
            with (output_root / "v64_records.csv").open("w", newline="", encoding="utf-8") as f:
                # union of keys
                keys = sorted({k for r in records for k in r.keys()})
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(records)
        summary = {
            "accepted_plan_sha": ACCEPTED_PLAN_SHA,
            "head_sha": args.authorized_target_sha,
            "total_blocks": len(registry),
            "total_calls": acct.completed,
            "hard_cap": HARD_CAP,
            "registry": registry,
            "elapsed_s": time.time() - t0,
        }
        (output_root / "v64_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except BaseException as exc:
        (output_root / "v64_interrupted.json").write_text(json.dumps({"interrupted": True, "error": f"{type(exc).__name__}: {exc}", "total_calls": acct.completed}), encoding="utf-8")
        print(f"INTERRUPTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"V64 fresh evidence written to {output_root} total_calls {acct.completed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
