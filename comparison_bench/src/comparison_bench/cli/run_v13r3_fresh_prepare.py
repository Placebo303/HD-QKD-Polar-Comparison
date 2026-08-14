"""CLI for the V13 R3 fresh-acquisition prepare lane
(``formal-nonbinary-ldpc-v13-r3-fresh-acquisition``).

Prepare-stage tooling ONLY.  Two actions:

- ``prepare`` — decoder-free, array-free prepare of a fresh-data source scan,
  identity ledger, exclusion verification, role pre-registration and the frozen
  plan / failure package.  Production output requires the explicit
  ``--production-prepare-authorized`` flag (main-thread authorization), which
  defaults to **False** and refuses production writes without it.  The fake test
  lane (``--test-only``) writes test schemas into a caller-owned fresh root.
- ``self-check`` — read-only structural checks (import, frozen constants,
  no-decoder invariant, ``scan_fresh_sources([])`` zero-eligible) that write
  nothing outside a caller-provided fresh output root (or nothing at all).

No decoder is imported or called anywhere in the prepare path; no production
output is written without authorization; no existing evidence file is ever
overwritten (per-file existence check via exclusive-create writes).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..formal_ir import nonbinary_v13r3_fresh as core


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def _emit(result: dict) -> None:
    print(json.dumps(result, sort_keys=True))


def _run_prepare(args: argparse.Namespace) -> int:
    if not args.test_only and not args.production_prepare_authorized:
        print("V13 R3 fresh production prepare requires the explicit "
              "--production-prepare-authorized flag (main-thread authorization)",
              file=sys.stderr)
        return 2
    if args.output is None:
        print("--output DIR is required", file=sys.stderr)
        return 2
    out = Path(args.output)
    if out.exists():
        print("fresh additive output directory required", file=sys.stderr)
        return 2
    declared = [p for p in (args.declared or [])]
    discovery_root = Path(args.discovery_root) if args.discovery_root else None
    run_id = args.run_id or (core.TEST_RUN_ID if args.test_only else core.RUN_ID)
    try:
        result = core.prepare(out, declared_paths=declared,
                              discovery_root=discovery_root,
                              seed=args.seed, run_id=run_id,
                              _test_only=args.test_only,
                              production_prepare_authorized=args.production_prepare_authorized)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    _emit({"output_directory": str(out), "state": result["state"],
           "package_file": result["package_file"], "run_id": run_id})
    return 0


def _run_self_check(args: argparse.Namespace) -> int:
    checks: dict = {}
    # Import/structural: module imports without a decoder.
    checks["import_ok"] = True
    checks["method"] = core.METHOD
    checks["identity_namespace"] = core.IDENTITY_PREFIX
    checks["required_exec_frames"] = core.REQUIRED_EXEC_FRAMES
    checks["canary_count"] = core.CANARY_COUNT
    checks["confirmation_count"] = core.CONFIRMATION_COUNT
    # Frozen invariant: the prepare path never imports a decoder.
    decoder_modules = [n for n in sys.modules
                       if "r3_candidate" in n or "nonbinary_v13_r3" in n
                       or "v7_r1a_long" in n or "v13_diagnostics" in n]
    checks["decoder_imported"] = bool(decoder_modules)
    # Frozen no-data path: empty declared list → zero eligible rows.
    scan = core.scan_fresh_sources([])
    checks["no_data_eligible_rows"] = scan["eligible_row_count"]
    checks["no_data_ok"] = scan["eligible_row_count"] == 0
    # Identity determinism smoke.
    row = {"stratum": "d1024_bw200", "frame_id": 0,
           "source_record_sha256": "0" * 64}
    ident_a = core.derive_identity("d1024_bw200", row)
    ident_b = core.derive_identity("d1024_bw200", row)
    checks["identity_deterministic"] = ident_a == ident_b
    checks["identity_prefix_ok"] = ident_a.startswith(core.IDENTITY_PREFIX + "-")
    if args.output is not None:
        out = Path(args.output)
        if out.exists():
            print("fresh additive output directory required", file=sys.stderr)
            return 2
        out.mkdir(parents=True)
        core._put(out / "self_check.json", {"schema": "nbldpc_v13r3_fresh_self_check_v1",
                                            "checks": checks})
    _emit(checks)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="V13 R3 fresh-acquisition prepare (prepare / self-check)")
    parser.add_argument("action", nargs="?", default="self-check",
                        choices=("prepare", "self-check"))
    parser.add_argument("--output", default=None,
                        help="fresh additive output directory")
    parser.add_argument("--declared", action="append", default=None,
                        help="declared fresh data source path (repeatable)")
    parser.add_argument("--discovery-root", default=None,
                        help="formal_ir_methods discovery root for exclusion locks")
    parser.add_argument("--seed", type=int, default=core.PLAN_SEED_DEFAULT,
                        help="frozen plan seed (default 20260815)")
    parser.add_argument("--run-id", default=None, help="run id (default per-lane)")
    parser.add_argument("--production-prepare-authorized", action="store_true",
                        help="explicit main-thread authorization for production prepare")
    parser.add_argument("--test-only", action="store_true",
                        help="fake test lane (test schemas, test-owned root)")
    args = parser.parse_args()
    if args.action == "prepare":
        return _run_prepare(args)
    return _run_self_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
