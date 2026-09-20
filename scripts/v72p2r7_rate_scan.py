"""R7 synthetic DE rate-scan runner — profile / frozen sweep / verify.

Frozen DE command (requires the operator's frozen-scan grant):

    .venv/bin/python scripts/v72p2r7_rate_scan.py --de-sweep \\
      --execution-authorized \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/r7_rate_scan_719f77de-0e69-499f-80b4-397457c8958a

Paths:

- ``--profile-only``: frozen plan/feasibility/budget/absence proofs only;
  zero DE calls, zero decoder calls, zero graphs, no root;
- ``--de-sweep``: the frozen 128-call L020-winner matrix (cap 200, halted
  + partial on cap hit); refuses unless ``--execution-authorized`` is
  passed (default false; refusal happens before any root probe, kernel
  bind or Model-F load) and requires explicitly injected adapters on the
  test path (production bind happens inside the orchestrator, after plan
  validation);
- ``--verify``: read-only recomputation of a completed six-file root with
  zero DE calls.

Additive R8 override (downward micro-extension only): ``--m-grid 88,92,96``
plus ``--de-cap 60`` threads a custom grid/cap through the same frozen
winner/protocol/bar/seeds/pops; omitting both reproduces the R7 default
byte-for-byte. Grid order is kept verbatim; duplicates are refused.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2r7_rate_scan as r7)

EVIDENCE_FILES = r7.EVIDENCE_FILES
FROZEN_COMMAND = r7.FROZEN_COMMAND


def build_parser():
    parser = argparse.ArgumentParser(
        description="R7 synthetic DE rate-scan runner (L020 winner)")
    parser.add_argument("--de-sweep", action="store_true",
                        help="run the frozen 128-call DE matrix (requires "
                             "--execution-authorized under the frozen-scan "
                             "grant)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--de-sweep; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="frozen plan/grid arithmetic only (no kernel, "
                             "no decoder, no graphs, no root)")
    parser.add_argument("--model-f-root", default=None,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    parser.add_argument("--m-grid", default=None,
                        help="additive R8 override: comma-separated m values "
                             "(e.g. 88,92,96); default is the frozen R7 grid")
    parser.add_argument("--de-cap", default=None, type=int,
                        help="additive R8 override: DE call cap; default is "
                             "the frozen R7 cap")
    return parser


def _parse_grid(text):
    try:
        grid = tuple(int(x) for x in str(text).split(",") if x.strip())
    except ValueError:
        raise SystemExit("error: --m-grid must be comma-separated ints")
    if not grid or len(set(grid)) != len(grid):
        raise SystemExit("error: --m-grid must be non-empty with unique m")
    if any(m < 1 or m > 128 for m in grid):
        raise SystemExit("error: --m-grid values must lie in 1..128")
    return grid


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--de-sweep", args.de_sweep),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --de-sweep, --verify or "
                     "--profile-only is required")
    if args.de_cap is not None and args.de_cap <= 0:
        parser.error("--de-cap must be a positive int")
    if args.profile_only:
        grid = _parse_grid(args.m_grid) if args.m_grid else None
        print(json.dumps(r7.describe_plan(grid=grid, cap=args.de_cap),
                         indent=2, sort_keys=True))
        return 0
    # Refuse --de-sweep before the root probe and before any kernel binding
    # or Model-F load while --execution-authorized is false.
    if args.de_sweep and not args.execution_authorized:
        print("refusing --de-sweep: %s (pass --execution-authorized only "
              "under the frozen-scan grant)" % r7.AUTHORIZATION,
              file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        grid = _parse_grid(args.m_grid) if args.m_grid else None
        return 0 if r7.verify_r7_root(args.out_root, grid=grid) else 1
    # Authorized true branch: exactly one sweep-orchestrator call plus one
    # never-overwrite writer. adapters_override carries test-machinery
    # fakes only (an injected "channel" must map 'L2' to the layer-tagged
    # oracle; None production-binds inside the orchestrator, after plan
    # validation and the fresh-root probe).
    inj = dict(adapters_override) if adapters_override is not None else {}
    grid = _parse_grid(args.m_grid) if args.m_grid else None
    bundle = r7.run_r7_sweep(
        args.out_root, args.model_f_root,
        channel=inj.get("channel"), de_call=inj.get("de_call"),
        rho_fn=inj.get("rho_fn"), now_fn=inj.get("now_fn"),
        rss_fn=inj.get("rss_fn"), grid=grid, cap=args.de_cap)
    summary = r7.write_r7_root(bundle)
    print("R7 terminal=%s calls=%d min_m=%s"
          % (summary["terminal"], summary["s7_ledger"]["consumed"],
             summary["s7_min"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
