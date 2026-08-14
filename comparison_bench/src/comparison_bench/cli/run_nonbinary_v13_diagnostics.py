"""CLI for the V13 existing-data nonbinary LDPC diagnostics lane
(``formal-nonbinary-ldpc-v13-existing-data-diagnostics``).

Main-thread-authorized Phase-D entrypoints (2026-08-14):

- ``ledger`` — build the data-role ledger from the locally discoverable 10 dB
  identity locks (V4 v1/v2 transfer locks + V5 partition lock) and write
  ``data_role_ledger.json`` into one fresh additive root;
- ``characterize`` — run the D01 no-decode channel characterization over the
  characterization-role bw200 frames and write the six-file diagnostic package
  into one fresh additive root under
  ``comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/``;
- ``d04`` — run the frozen D04 baseline probe (unchanged V7 R1A ``p=.20``,
  exactly once, on the 32 pre-registered bw200 development frames).  Requires
  the explicit ``--authorized`` (main-thread authorization) and ``--production``
  flags and a fresh additive ``--output`` root;
- ``d05`` — emit the root-cause report (frozen decision table applied to the
  corrected D01 aggregates, the D04 outcomes, the offline graph analysis and
  the structural ceiling) into one fresh additive package.  Requires
  ``--authorized --production`` and fresh ``--output``; consumes the D01/D04
  package directories via ``--d01-dir``/``--d04-dir`` (canonical defaults
  under ``nonbinary_diagnostics/``).
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from ..formal_ir import nonbinary_v13_diagnostics as core


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    diag_root = root / "comparison_bench/outputs_comparison/nonbinary_diagnostics"
    parser = argparse.ArgumentParser(
        description="V13 nonbinary LDPC existing-data diagnostics "
                    "(ledger / D01 characterize / D04 probe / D05 report)")
    parser.add_argument("action", nargs="?", default="ledger",
                        choices=("ledger", "characterize", "d04", "d05", "e01",
                                 "a01", "a02"))
    parser.add_argument("--output", default=None,
                        help="fresh additive output root (required for ledger/characterize/d04/d05)")
    parser.add_argument("--run-id", default=None,
                        help="diagnostic run id (default v13_d01/d04/d05_<8-hex>)")
    parser.add_argument("--formal-ir-root", default=None,
                        help="formal_ir_methods discovery root "
                             "(default comparison_bench/outputs_comparison/formal_ir_methods)")
    parser.add_argument("--d01-dir", default=str(diag_root / "v13_d01_20260814"),
                        help="D01 package directory (D05 input)")
    parser.add_argument("--d04-dir", default=str(diag_root / "v13_d04_20260814"),
                        help="D04 package directory (D05 input)")
    parser.add_argument("--production", action="store_true",
                        help="explicit production-lane authorization for D01/D04/D05")
    parser.add_argument("--authorized", action="store_true",
                        help="explicit main-thread authorization for the D04/D05 lanes")
    parser.add_argument("--test-only", action="store_true",
                        help="test-only lane flag (module API, not this CLI)")
    args = parser.parse_args()

    formal_ir_root = Path(args.formal_ir_root) if args.formal_ir_root \
        else root / "comparison_bench/outputs_comparison/formal_ir_methods"

    if args.action == "a02":
        try:
            core.v13_d04_d05_guard("a02", args.authorized)
        except SystemExit:
            print("V13-A02 cross-stratum check requires the explicit --authorized "
                  "flag (main-thread authorization)", file=sys.stderr)
            return 2
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        if not args.production:
            print("production A02 check requires the explicit --production flag",
                  file=sys.stderr)
            return 2
        out = Path(args.output)
        if out.exists():
            print("fresh additive output root required", file=sys.stderr)
            return 2
        run_id = args.run_id or f"v13_a02_{uuid.uuid4().hex[:8]}"
        try:
            result = core.run_a02(out, run_id=run_id,
                                  discovery_root=formal_ir_root,
                                  production_authorized=True,
                                  command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.action == "a01":
        try:
            core.v13_d04_d05_guard("a01", args.authorized)
        except SystemExit:
            print("V13-A01 retrospective audit requires the explicit --authorized "
                  "flag (main-thread authorization)", file=sys.stderr)
            return 2
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        if not args.production:
            print("production A01 audit requires the explicit --production flag",
                  file=sys.stderr)
            return 2
        out = Path(args.output)
        if out.exists():
            print("fresh additive output root required", file=sys.stderr)
            return 2
        run_id = args.run_id or f"v13_a01_{uuid.uuid4().hex[:8]}"
        try:
            result = core.run_a01(out, run_id=run_id,
                                  discovery_root=formal_ir_root,
                                  production_authorized=True,
                                  command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.action == "e01":
        try:
            core.v13_d04_d05_guard("e01", args.authorized)
        except SystemExit:
            print("V13-E01 development screen requires the explicit --authorized "
                  "flag (main-thread authorization)", file=sys.stderr)
            return 2
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        if not args.production:
            print("production E01 screen requires the explicit --production flag",
                  file=sys.stderr)
            return 2
        out = Path(args.output)
        if out.exists():
            print("fresh additive output root required", file=sys.stderr)
            return 2
        run_id = args.run_id or f"v13_e01_{uuid.uuid4().hex[:8]}"
        try:
            result = core.run_e01(out, run_id=run_id,
                                  discovery_root=formal_ir_root,
                                  production_authorized=True,
                                  command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.action == "d05":
        try:
            core.v13_d04_d05_guard("d05", args.authorized)
        except SystemExit:
            print("V13-D05 root-cause report requires the explicit --authorized "
                  "flag (main-thread authorization)", file=sys.stderr)
            return 2
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        if not args.production:
            print("production D05 report requires the explicit --production flag",
                  file=sys.stderr)
            return 2
        out = Path(args.output)
        if out.exists():
            print("fresh additive output root required", file=sys.stderr)
            return 2
        run_id = args.run_id or f"v13_d05_{uuid.uuid4().hex[:8]}"
        try:
            result = core.run_d05(out, run_id=run_id, d01_dir=Path(args.d01_dir),
                                  d04_dir=Path(args.d04_dir),
                                  discovery_root=formal_ir_root,
                                  production_authorized=True,
                                  command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.action == "d04":
        try:
            core.v13_d04_d05_guard("d04", args.authorized)
        except SystemExit:
            print("V13-D04 baseline probe requires the explicit --authorized "
                  "flag (main-thread authorization)", file=sys.stderr)
            return 2
        if args.output is None:
            print("--output DIR is required", file=sys.stderr)
            return 2
        if not args.production:
            print("production D04 baseline probe requires the explicit "
                  "--production flag", file=sys.stderr)
            return 2
        out = Path(args.output)
        if out.exists():
            print("fresh additive output root required", file=sys.stderr)
            return 2
        run_id = args.run_id or f"v13_d04_{uuid.uuid4().hex[:8]}"
        try:
            result = core.run_d04(out, run_id=run_id, discovery_root=formal_ir_root,
                                  production_authorized=True,
                                  command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.output is None:
        print("--output DIR is required", file=sys.stderr)
        return 2
    if not args.production and not args.test_only:
        print("production D01 work requires the explicit --production flag "
              "(or use the module API with _test_only=True)", file=sys.stderr)
        return 2
    run_id = args.run_id or f"v13_d01_{uuid.uuid4().hex[:8]}"
    out = Path(args.output)
    if out.exists():
        print("fresh additive output root required", file=sys.stderr)
        return 2
    if args.action == "ledger":
        out.mkdir(parents=True)
    if args.action == "ledger":
        try:
            ledger = core.build_production_ledger(formal_ir_root, run_id=run_id)
            core.write_role_ledger(out / "data_role_ledger.json", ledger)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"run_id": run_id, "ledger_state": ledger["ledger_state"],
                          "counts": ledger["counts"]}, sort_keys=True))
        return 0
    try:
        result = core.run_d01(out, run_id=run_id, discovery_root=formal_ir_root,
                              production_authorized=bool(args.production),
                              command=" ".join(sys.argv))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
