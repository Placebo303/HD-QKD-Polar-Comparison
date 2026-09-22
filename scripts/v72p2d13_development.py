"""D13 L055 failure decoder ladder runner — readiness paths.

Frozen command (design §5; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d13_development.py --d13-batch \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e

Paths:

- ``--plan-only``: read-only reconstruction metadata for the frozen 56
  (selection + 224-entry plan summary + future-root absence) on stdout;
  zero decoder calls, no decoder binding, no Model-F load, no root;
- ``--d13-batch``: strict RL90 replay (56) then exactly three ladder arms
  on every selected failure (<=224 scientific calls, <=8 setup units);
  refuses unless ``--execution-authorized`` is passed (default false;
  refusal happens before any root creation, decoder binding or Model-F
  load) and requires the injected production decoder entry points, which
  only this entrypoint constructs from the accepted binders;
- ``--verify``: read-only fail-closed recomputation of a completed
  six-file root with zero decoder calls.

One fresh root per run; refuses overwrite (single process, no retry, no
resume, no repair, no seed search, no tuning). Successes never enter the
ladder; exact/syndrome/undetected stay separate; CHECK_UPDATED mandatory.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d13_l055_decoder_ladder as d13)

_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # Reuse: prior-chain, block, CSV/JSON and parse helpers live in the R2
    # runner; import them read-only instead of copying (R2 files untouched).
    spec = importlib.util.spec_from_file_location(
        "v72p2d10_r2_runner_reuse_d13", str(_R2_RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v72p2d10_r2_runner_reuse_d13"] = module
    spec.loader.exec_module(module)
    return module


_r2run = _load_r2_runner()

EVIDENCE_FILES = d13.EVIDENCE_FILES
FROZEN_COMMAND = d13.FROZEN_COMMAND


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


# --------------------------------------------------------------------------- #
# production entry points (constructed ONLY under --execution-authorized)
# --------------------------------------------------------------------------- #
def build_production_fns(model_f_root, identities, *,
                         build_graph_fn=None, load_prior_fn=None,
                         sample_fn=None, floor_fn=None):
    """Wire the accepted binders + D12 reconstruction into identity-level
    decoder entry points (import, not copy). Returns
    ``(replay_fn, ladder_fns, setup_units)``. Never called without
    explicit execution authorization (see ``main`` refusal order)."""
    from comparison_bench.formal_ir import (  # lazy production adapter
        v35_algorithm_development as v35)
    binds = d13.bind_production()
    syndrome_fn = v35.syndrome_of_gf32
    build_graph_fn = build_graph_fn or d13.build_graph
    load_prior_fn = load_prior_fn or _r2run.load_prior_chain

    widths = sorted({int(i["width"]) for i in identities})
    wanted_blocks = {w: sorted({int(i["block_seed"]) for i in identities
                                if int(i["width"]) == w}) for w in widths}
    p_b, p_f, p1 = load_prior_fn(model_f_root)
    blocks: dict[int, dict[int, dict]] = {}
    for width in widths:
        prepared = load_blocks(load_prior_fn, p_b, p_f, p1, width,
                               wanted_blocks[width], sample_fn=sample_fn,
                               floor_fn=floor_fn)
        blocks[width] = prepared
    graphs: dict[tuple[int, int], dict] = {}
    for width in widths:
        for graph_seed in sorted({int(i["graph_seed"]) for i in identities
                                  if int(i["width"]) == width}):
            graphs[(width, graph_seed)] = build_graph_fn(
                d13.SELECT_ARM, width, graph_seed)
    setup_units = d13.SETUP_FIXED_UNITS

    def call_once(identity, decode_fn, max_iter):
        width = int(identity["width"])
        graph = graphs[(width, int(identity["graph_seed"]))]
        block = blocks[width][int(identity["block_seed"])]
        if graph.get("dense") is None or not bool(graph.get("admitted")):
            raise ValueError("refusing decoder binding for non-admitted "
                             "graph %r" % ((width,
                                            identity["graph_seed"]),))
        H = np.asarray(graph["dense"], dtype=np.uint8)
        u1 = np.asarray(block["u1"], dtype=np.int64)
        prior = np.asarray(block["prior"], dtype=np.float64)
        t0 = time.perf_counter()
        syn = np.asarray(syndrome_fn(H, u1), dtype=np.uint8)
        result = decode_fn(H, prior, syn)
        x_hat = np.asarray(result.x_hat)
        reported = bool(result.syndrome_ok)
        residual = int(np.count_nonzero(
            np.asarray(syndrome_fn(H, x_hat)) != syn))
        exact = bool(reported and residual == 0
                     and x_hat.shape == u1.shape
                     and np.array_equal(x_hat, u1))
        return {"width": width, "arm": d13.SELECT_ARM,
                "graph_seed": int(identity["graph_seed"]),
                "block_seed": int(identity["block_seed"]),
                "call_idx": int(identity["call_idx"]),
                "exact": exact, "syndrome_ok": reported and residual == 0,
                "iterations": int(result.iterations),
                "belief_provenance": getattr(result, "belief_provenance",
                                             None),
                "wall_s": time.perf_counter() - t0}

    def replay_fn(identity):
        return call_once(identity, binds[d13.REPLAY_ARM_ID], 90)

    ladder_fns = {
        arm: (lambda identity, _arm=arm: call_once(
            identity, binds[_arm],
            d13.LADDER_CONFIG[_arm]["max_iter"]))
        for arm in d13.LADDER_ARMS}
    return replay_fn, ladder_fns, setup_units


def load_blocks(load_prior_fn, p_b, p_f, p1, width, block_seeds, *,
                sample_fn=None, floor_fn=None):
    prepared = _r2run.prepare_blocks(
        p_b, p_f, p1, width, tuple(block_seeds), sample_fn=sample_fn,
        floor_fn=floor_fn)
    if isinstance(prepared, dict):
        return dict(prepared)
    indexed: dict[int, dict] = {}
    for block, seed in zip(prepared, block_seeds):
        indexed[int(seed)] = block
    return indexed


# --------------------------------------------------------------------------- #
# batch (strict replay gate, then exactly three arms per failure)
# --------------------------------------------------------------------------- #
def run_d13_batch(out_root, model_f_root, input_root, *,
                  replay_fn=None, ladder_fns=None, setup_units=None,
                  now_fn=None, rss_fn=None):
    """Execute and persist one authorized D13 batch (injected decoder entry).

    ``replay_fn``/``ladder_fns`` are explicit injections supplied by the
    caller (the ``--d13-batch`` entrypoint constructs the production
    wiring). The frozen 224-entry plan is built before any injected
    callable runs; the first replay mismatch blocks all ladder calls.
    """
    from comparison_bench.formal_ir import (  # noqa: F401  (anchor: D12 root
        v72p2d12_finite_l1_degree as _d12_anchor)  # stays read-only context
    out_resolved = d13.d12.refuse_out_root(out_root)
    rows = _r2run._read_csv(Path(input_root) / "decoder_records.csv")
    selected = d13.select_l055_failures(rows)
    selection_violations = d13.validate_selection(selected)
    if selection_violations:
        raise RuntimeError("frozen selection violated: %s"
                           % selection_violations[0])
    if replay_fn is None or ladder_fns is None:
        raise ValueError("decoder entry points must be explicitly injected")
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _r2run._log_line(message)
        log_lines.append(line)
        print(line)

    log("selected %d frozen L055 failures (n128=%d n256=%d)" % (
        len(selected),
        sum(1 for r in selected if int(r["width"]) == 128),
        sum(1 for r in selected if int(r["width"]) == 256)))
    outcome = d13.run_readiness(selected, replay_fn, ladder_fns,
                                now_fn=now, rss_fn=rss_fn)
    setup_calls = d13.SETUP_FIXED_UNITS if setup_units is None \
        else int(setup_units)
    log("replay=%d ladder=%d terminal=%s" % (
        outcome["replay_calls"], outcome["ladder_calls"],
        outcome["terminal"]))
    summary = d13.write_root(out_resolved, selection=selected,
                             outcome=outcome, model_f_root=model_f_root,
                             setup_calls=setup_calls, log_lines=log_lines)
    wall_s = float(now()) - t0
    log("D13 terminal=%s calls=%d setup=%d wall_s=%.3f" % (
        summary["terminal"], summary["scientific_calls"],
        summary["setup_calls"], wall_s))
    return summary


# --------------------------------------------------------------------------- #
# CLI (D1305: --d13-batch requires explicit --execution-authorized)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D13 L055 failure decoder ladder runner")
    parser.add_argument("--d13-batch", action="store_true",
                        help="run the frozen 56+168 decoder ladder (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--d13-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--plan-only", action="store_true",
                        help="read-only reconstruction metadata for the "
                             "frozen 56 (no decoder, no root)")
    parser.add_argument("--model-f-root",
                        default=d13.d12.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--input-root", default=d13.INPUT_ROOT,
                        help="frozen read-only D12 input root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def plan_only(input_root=None):
    """D1309 helper: metadata only, zero decoder calls, no root."""
    meta = d13.plan_only_metadata(input_root or d13.INPUT_ROOT)
    return meta


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--d13-batch", args.d13_batch),
                                        ("--verify", args.verify),
                                        ("--plan-only", args.plan_only))
                if flag]
    if len(selected) != 1:
        parser.error("exactly one of --d13-batch, --verify or "
                     "--plan-only is required")
    if args.plan_only:
        print(json.dumps(plan_only(args.input_root), indent=2,
                         sort_keys=True))
        return 0
    # D1305: refuse --d13-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.d13_batch and not args.execution_authorized:
        print("refusing --d13-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d13.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if d13.verify_root(args.out_root) else 1
    replay_fn, ladder_fns, setup_units = build_production_fns(
        args.model_f_root, d13.select_l055_failures(
            _r2run._read_csv(Path(args.input_root) / "decoder_records.csv")))
    summary = run_d13_batch(args.out_root, args.model_f_root,
                            args.input_root, replay_fn=replay_fn,
                            ladder_fns=ladder_fns,
                            setup_units=setup_units)
    print("D13 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
