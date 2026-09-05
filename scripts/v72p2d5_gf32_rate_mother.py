"""V72P2D5 GF32 rate-mother CLI — explicit phase only, no execution this round.

Only ``--phase structure|g0|p0-cost|g1|g2`` is supported. ``--phase`` is
required. Every phase refuses before any work because the frozen
``cycle_state.yaml`` authorizes none of them. The single file read here is
the authorization state itself; no data tables are read and no output is
created. Authorization logic lives in exactly one place
(:func:`is_phase_authorized` in the core module).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1]
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d5_gf32_rate_mother.py")
STATE_PATH = (ROOT / "docs" / "research_cycles" / "V72P2D5-GF32-RATE-MOTHER"
              / "cycle_state.yaml")
STRUCTURE_OUT_DIR = (ROOT / "workspace" / "v72p2d5_structure"
                     / "20260905_r2")

_SPEC = importlib.util.spec_from_file_location(
    "v72p2d5_gf32_rate_mother_core", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)

_RUNNERS = {
    "structure": _mod.run_structure_sequence,
    "g0": _mod.run_g0_synthetic,
    "p0-cost": _mod.run_p0_cost_phase,
    "g1": _mod.run_g1_phase,
    "g2": _mod.run_g2_phase,
}


def _load_state(path):
    """Parse the flat ``cycle_state.yaml`` into a plain dict (booleans kept)."""
    state = {}
    with open(str(path), "r", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip().strip("'\"").lower()
            if val in ("true", "false"):
                state[key] = val == "true"
            else:
                state[key] = val
    return state


def build_parser():
    ap = argparse.ArgumentParser(
        description="V72P2D5 GF32 rate-mother phases (authorization-gated).")
    ap.add_argument("--phase", required=True, choices=sorted(_RUNNERS),
                    help="explicit phase to enter")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        state = _load_state(STATE_PATH)
    except OSError as exc:
        print(f"cannot read authorization state: {exc}")
        return 3
    if not _mod.is_phase_authorized(state, args.phase):
        print(f"phase '{args.phase}' is not authorized; refusing before any work")
        return 3
    try:
        if args.phase == "structure":
            _RUNNERS["structure"](authorized=True,
                                   out_dir=STRUCTURE_OUT_DIR)
        else:
            _RUNNERS[args.phase](authorized=True)
    except Exception as exc:
        print(f"phase '{args.phase}' refused: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
