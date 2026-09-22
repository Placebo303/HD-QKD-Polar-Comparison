"""D7 R1 consistency / multi-graph / X1–X4 CLI (authorization-gated).

Lazy local-source bind: derives the repository from the resolved ``__file__``
and loads the consistency/multi-graph module by file path. Reads only the
V72P2D7-ROOT-CAUSE-RESET authorization state (and the D5 state for ``--g2``);
refuses before any Model-F read, decoder bind, or root creation while the
relevant key is false.

- ``--dry-run``: prints the frozen 384-slot matrix (no state read needed).
- ``--historical-provenance-probe``: X1 one-call historical decoder
  provenance probe (no write, no root); requires
  ``x1_consistency_probe_authorized``.
- ``--consistency``: same-input synthetic consistency comparison on the
  accepted Model-F priors with a deterministic synthetic stub (not X1; no
  decoder call, no write); requires ``x1_consistency_probe_authorized``.
- ``--reference-ladder --x2-root <exact> --out-root <exact>``: X3
  failed-record reference ladder over the immutable X2 root; requires
  ``x3_reference_ladder_authorized``.
- ``--g2``: X4 one-call bridge to the frozen n=256 G2 discriminator; requires
  ``x4_g2_execution_authorized`` and all D5 execution flags false.
- default run: X2 multi-graph diagnostic into a fresh ``workspace`` root;
  requires ``x2_multigraph_execution_authorized`` and ``--model-f-root``
  equal to the accepted Model-F root.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1]
_SRC = str(ROOT / "comparison_bench" / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d7_consistency_multigraph.py")
STATE_PATH = (ROOT / "docs" / "research_cycles" / "V72P2D7-ROOT-CAUSE-RESET"
              / "cycle_state.yaml")
D5_STATE_PATH = (ROOT / "docs" / "research_cycles"
                 / "V72P2D5-GF32-RATE-MOTHER" / "cycle_state.yaml")

_SPEC = importlib.util.spec_from_file_location(
    "d7_r1_consistency_multigraph_core", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)


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
        description="D7 R1 consistency / multi-graph exploratory runner "
                    "(authorization-gated).")
    ap.add_argument("--out-root", default=None, help="fresh evidence root")
    ap.add_argument("--model-f-root", default=None,
                    help="must equal %s for a run" % (_mod.MODEL_F_ROOT,))
    ap.add_argument("--wall-budget-s", type=float, default=None,
                    help="optional stored-wall budget; exceeds -> resource stop")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the frozen 384-slot matrix only")
    ap.add_argument("--historical-provenance-probe", action="store_true",
                    help="X1 one-call historical decoder provenance probe "
                         "(no write, no root)")
    ap.add_argument("--consistency", action="store_true",
                    help="same-input synthetic consistency comparison "
                         "(not X1; no decoder call, no write)")
    ap.add_argument("--reference-ladder", action="store_true",
                    help="X3 failed-record reference ladder over the frozen "
                         "X2 root")
    ap.add_argument("--x2-root", default=None,
                    help="exact read-only X2 root for --reference-ladder")
    ap.add_argument("--g2", action="store_true",
                    help="X4 one-call bridge to the frozen n=256 G2 "
                         "discriminator root")
    return ap


def _historical_provenance_probe():
    """X1: exactly one no-injection probe call; one JSON record; no writes."""
    report = _mod.d5.probe_historical_decoder_provenance(decode_fn=None)
    record = _mod.historical_provenance_probe_record(report)
    print(json.dumps(record, sort_keys=True))
    if not record["ok"]:
        print(_mod.X1_PROBE_FAILED_LABEL, file=sys.stderr)
        return 2
    return 0


def _consistency_record(report):
    """Relabel the synthetic same-input report; never call it X1."""
    record = dict(report)
    record["mode"] = "same_input_synthetic_consistency"
    record["label"] = ("same-input synthetic consistency (not X1 historical "
                       "provenance)")
    return record


def _consistency_probe():
    """Read-only same-input comparison on accepted priors, no decoder."""
    import numpy as np

    counts_ab, p_b_cal = _mod.d5._load_model_f_input_or_blocked()
    p_b, p_f = _mod.d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)
    seed = int(_mod.BLOCK_SEEDS[0])
    block = _mod.d5.sample_matched_block(p_b, p_f, _mod.N_BLOCK, seed)
    beliefs = np.zeros((_mod.N_BLOCK, _mod.Q), dtype=np.float64)
    stub_state = {"n": 0}

    def synthetic_stub(h, prior, syndrome, layer=None):
        # Deterministic stand-in, not a decoder: the comparison call order is
        # G1-L1, G1-L2, D7-L1, D7-L2, so calls 1/3 return the L1 truth and
        # calls 2/4 the L2 truth. No decoder is bound or invoked.
        stub_state["n"] += 1
        truth = block["u1"] if stub_state["n"] in (1, 3) else block["u2"]
        return {"x_hat": np.asarray(truth, dtype=np.int64),
                "syndrome_ok": True, "iterations": 1,
                "final_beliefs": np.asarray(prior, dtype=np.float64).copy(),
                "belief_provenance": "CHECK_UPDATED"}

    h1 = _mod.d5.build_dv3_nested_support(
        _mod.N_BLOCK, _mod.N_BLOCK, _mod.L1_K_MIN, int(_mod.GRAPH_PAIRS[0][0]))
    h1 = _mod.d5.assign_gf32_coefficients(h1, int(_mod.GRAPH_PAIRS[0][0]),
                                          None, _mod.N_BLOCK)
    h2 = _mod.d5.build_dv3_nested_support(
        _mod.N_BLOCK, _mod.N_BLOCK, _mod.L2_K_MIN, int(_mod.GRAPH_PAIRS[0][1]))
    h2 = _mod.d5.assign_gf32_coefficients(h2, int(_mod.GRAPH_PAIRS[0][1]),
                                          None, _mod.N_BLOCK)
    report = _mod.compare_same_input(
        p_f=p_f, block=block, h1=h1, h2=h2, beliefs=beliefs,
        decode_fn=synthetic_stub)
    print(json.dumps(_consistency_record(report), sort_keys=True))
    return 0 if report.get("ok") else 2


def main(argv=None):
    args = build_parser().parse_args(argv)
    modes = (bool(args.dry_run), bool(args.historical_provenance_probe),
             bool(args.consistency), bool(args.reference_ladder),
             bool(args.g2))
    if sum(modes) > 1:
        print("choose exactly one mode; refusing")
        return 3
    if args.dry_run:
        slots = _mod.frozen_slots()
        print("slots=%d max_calls=%d" % (len(slots), _mod.MAX_CALLS))
        print("graph_pairs=%r" % (_mod.GRAPH_PAIRS,))
        print("block_seeds=%d..%d" % (_mod.BLOCK_SEEDS[0],
                                      _mod.BLOCK_SEEDS[-1]))
        print("f=%r rows=%r" % (_mod.F_VALUES, _mod.F_ROWS))
        for slot in slots[:8]:
            print("%d g%d f=%s seed=%d %s %s rows=%d" % (
                slot["slot_idx"], slot["graph_idx"], slot["f"],
                slot["seed"], slot["arm"], slot["role"], slot["rows"]))
        print("... (%d more)" % (len(slots) - 8,))
        return 0
    if args.historical_provenance_probe:
        try:
            state = _load_state(STATE_PATH)
        except OSError as exc:
            print("cannot read authorization state: %s" % (exc,))
            return 3
        if not state.get("x1_consistency_probe_authorized", False):
            print("X1 historical provenance probe is not authorized; refusing")
            return 3
        try:
            return _historical_provenance_probe()
        except Exception as exc:
            print("historical provenance probe refused: %r" % (exc,))
            return 3
    if args.reference_ladder:
        try:
            state = _load_state(STATE_PATH)
        except OSError as exc:
            print("cannot read authorization state: %s" % (exc,))
            return 3
        if not state.get("x3_reference_ladder_authorized", False):
            print("X3 reference ladder is not authorized; refusing before "
                  "any work")
            return 3
        if not args.x2_root or not args.out_root:
            print("missing --x2-root/--out-root; refusing")
            return 3
        try:
            result = _mod.run_reference_ladder_selected(
                x2_root=args.x2_root, out_root=args.out_root, authorized=True,
                repo_root=ROOT, wall_budget_s=args.wall_budget_s,
                command_str=" ".join(sys.argv))
        except Exception as exc:
            print("reference ladder refused: %r" % (exc,))
            return 3
        print("terminal=%s out=%s selected=%d ladder_calls=%d "
              "reconstruction_calls=%d" % (
                  result["terminal"], result["out_root"],
                  result["selected_records"], result["ladder_calls"],
                  result["reconstruction_calls"]))
        if result["terminal"] == _mod.X3_TERMINAL_MISMATCH:
            return 1
        return 0
    if args.g2:
        try:
            state = _load_state(STATE_PATH)
            d5_state = _load_state(D5_STATE_PATH)
        except OSError as exc:
            print("cannot read authorization state: %s" % (exc,))
            return 3
        if not state.get("x4_g2_execution_authorized", False):
            print("X4 G2 execution is not authorized; refusing before any "
                  "work")
            return 3
        try:
            result = _mod.run_g2_bridge(
                d7_state=state, d5_state=d5_state, repo_root=ROOT)
        except Exception as exc:
            print("G2 bridge refused: %r" % (exc,))
            return 3
        print("grade=%s out=%s decoder_calls=%d" % (
            result["grade"], result["out_root"], result["decoder_calls"]))
        return 0
    try:
        state = _load_state(STATE_PATH)
    except OSError as exc:
        print("cannot read authorization state: %s" % (exc,))
        return 3
    if args.consistency:
        if not state.get("x1_consistency_probe_authorized", False):
            print("same-input synthetic consistency is not authorized; "
                  "refusing")
            return 3
        try:
            return _consistency_probe()
        except Exception as exc:
            print("consistency probe refused: %r" % (exc,))
            return 3
    if not args.out_root:
        print("missing --out-root (or use --dry-run / --consistency); refusing")
        return 3
    if not state.get("x2_multigraph_execution_authorized", False):
        print("X2 multi-graph execution is not authorized; refusing before "
              "any work")
        return 3
    if not args.model_f_root:
        print("missing --model-f-root; refusing")
        return 3
    if not _mod.d7c.model_f_root_matches(args.model_f_root, repo_root=ROOT):
        print("refused: --model-f-root must equal %s" % (_mod.MODEL_F_ROOT,))
        return 3
    try:
        result = _mod.run_multigraph_diagnostic(
            out_root=args.out_root, authorized=True, decoder_fns=None,
            model_f_root=args.model_f_root, repo_root=ROOT,
            wall_budget_s=args.wall_budget_s,
            command_str=" ".join(sys.argv))
    except Exception as exc:
        print("multi-graph run refused: %r" % (exc,))
        return 3
    print("terminal=%s out=%s calls=%d" % (
        result["terminal"], result["out_root"], result["decoder_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
