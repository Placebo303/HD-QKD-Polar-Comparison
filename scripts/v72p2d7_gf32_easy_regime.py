"""D7-B easy-regime runner (frozen R1+A1; authorization-gated, no execution here).

Reads only the authorization state file; refuses before any work/root bind
when unauthorized. ``--dry-run`` prints the frozen 64-cell matrix and exits
with no root and no decoder bind. ``--verify <root>`` read-only checks a
five-file root.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1]
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d7_gf32_easy_regime.py")
STATE_PATH = (ROOT / "docs" / "research_cycles" / "V72P2D7-GF32-EASY-REGIME"
              / "cycle_state.yaml")

_SPEC = importlib.util.spec_from_file_location("d7b_easy_regime_core", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)


def _load_state(path):
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
    ap = argparse.ArgumentParser(description="D7-B easy-regime (authorization-gated).")
    ap.add_argument("--out-root", default=None, help="fresh evidence root")
    ap.add_argument("--dry-run", action="store_true", help="print frozen matrix only")
    ap.add_argument("--verify", default=None, help="read-only verify a five-file root")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.verify:
        rep = _mod.verify_root(args.verify)
        print(("VERIFY_OK" if rep.get("ok") else "VERIFY_FAIL") + " %r" % (rep,))
        return 0 if rep.get("ok") else 2
    if args.dry_run:
        cells = _mod.cell_list()
        print("cells=%d caps=%r budget=%d" % (len(cells), list(_mod.CAPS), _mod.CALL_BUDGET))
        for tier, fam, seed in cells:
            print("%s %s %d" % (tier, fam, seed))
        return 0
    if not args.out_root:
        print("missing --out-root (or use --dry-run / --verify); refusing")
        return 3
    try:
        state = _load_state(STATE_PATH)
    except OSError as exc:
        print("cannot read authorization state: %s" % (exc,))
        return 3
    if not _mod.is_authorized(state):
        print("D7-B execution is not authorized; refusing before any work")
        return 3
    try:
        out = _mod.run_easy_regime(out_root=args.out_root, decode_fn=None,
                                   authorized=True,
                                   command_str=" ".join(sys.argv),
                                   repo_root=ROOT)
    except Exception as exc:
        print("D7-B refused: %r" % (exc,))
        return 3
    print("terminal=%s out=%s" % (out["terminal"], out["out_root"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
