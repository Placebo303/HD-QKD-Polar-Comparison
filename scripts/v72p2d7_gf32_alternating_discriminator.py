"""D7-H minimal two-transfer alternating discriminator runner (R1A1; gate only).

Lazy local-source bind: derives the repository from the resolved ``__file__``,
inserts ``<repo>/comparison_bench/src`` only when absent, then loads the core
module by file path.  Reads only the D7-H authorization state file; refuses
before any work/Model-F read/decoder bind/root creation while
``d7h_execution_authorized`` is false.  ``--dry-run`` prints the frozen
96-slot planned schedule (gated slots included as planned slots);
``--verify <root>`` performs the read-only seven-file recomputation.  The
frozen future command is not run in this task.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1]
# ponytail: runner-local source only, derived from __file__ (no cwd/PYTHONPATH)
_SRC = str(ROOT / "comparison_bench" / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d7_gf32_alternating_discriminator.py")
STATE_PATH = (ROOT / "docs" / "research_cycles"
              / "V72P2D7-GF32-ALTERNATING-DISCRIMINATOR" / "cycle_state.yaml")

_SPEC = importlib.util.spec_from_file_location(
    "d7h_alternating_discriminator_core", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)


def build_parser():
    ap = argparse.ArgumentParser(
        description="D7-H minimal two-transfer alternating cross-layer "
                    "discriminator (authorization-gated).")
    ap.add_argument("--model-f-root", default=None,
                    help="must equal %s for a run" % (_mod.MODEL_F_ROOT,))
    ap.add_argument("--out-root", default=None, help="fresh evidence root")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the frozen 96-slot planned schedule only")
    ap.add_argument("--verify", default=None,
                    help="read-only verify a seven-file root")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.verify:
        report = _mod.verify_root(args.verify)
        print(("VERIFY_OK" if report.get("ok") else "VERIFY_FAIL")
              + " %r" % (report,))
        return 0 if report.get("ok") else 2
    if args.dry_run:
        slots = _mod.frozen_slots()
        print("slots=%d mandatory=%d budget=%d" % (
            len(slots), _mod.MANDATORY_CALLS, _mod.MAX_CALLS))
        for slot in slots:
            print("%d %s %d %s %s %s %s %d" % (
                slot["slot_idx"], slot["f"], slot["seed"],
                slot["stage_name"], slot["role"], slot["condition"],
                slot["layer"], slot["rows"]))
        return 0
    if not args.out_root:
        print("missing --out-root (or use --dry-run / --verify); refusing")
        return 3
    # Pure root-contract refusal first: no state read, no Model-F, no decoder.
    try:
        _mod.validate_production_out_root(args.out_root, repo_root=ROOT)
    except Exception as exc:
        print("D7-H refused: %r" % (exc,))
        return 3
    try:
        state = _mod.read_cycle_state(STATE_PATH)
    except OSError as exc:
        print("cannot read authorization state: %s" % (exc,))
        return 3
    if not _mod.is_authorized(state):
        print("D7-H execution is not authorized; refusing before any work "
              "(%s)" % (_mod.T_PRE_EXEC,))
        return 3
    if not args.model_f_root:
        print("missing --model-f-root; refusing")
        return 3
    if not _mod.model_f_root_matches(args.model_f_root, repo_root=ROOT):
        print("D7-H refused: --model-f-root must equal %s" % (_mod.MODEL_F_ROOT,))
        return 3
    try:
        result = _mod.run_alternating_discriminator(
            out_root=args.out_root, model_f_root=args.model_f_root,
            decoder_fns=None, state=state, command_str=" ".join(sys.argv),
            repo_root=ROOT)
    except Exception as exc:
        print("D7-H refused: %r" % (exc,))
        return 3
    print("terminal=%s out=%s" % (result["terminal"], result["out_root"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
