"""Fixed-budget GF32 MRB belief-top6 EXPLORE probe."""
from __future__ import annotations

import argparse
import math
import json
import time
from pathlib import Path
from typing import Any, Callable

from comparison_bench.cli import nbldpc_gf32_mrb_rescue_probe as mrb
from comparison_bench.formal_ir import nonbinary_v19_osd

CONTRACT = "NBLDPC-GF32-MRB-TOP6-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "df44e589-370d-4818-b652-2e2cc67de758"
REAGGREGATION_UUID = "e1d549f7-695d-4166-8c4c-e6eaa803a735"
SOURCE_BATCH_UUID = "ebbbe5c2-f53f-4b92-a2ff-3eca358002de"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_mrb_top6_df44e589"
SEED_PREFIX = "gf32-mrb-top6-v1"
MAX_CANDIDATES = mrb.MAX_CANDIDATES
MAX_ITER = mrb.MAX_ITER
DAMPING_ALPHA = mrb.DAMPING_ALPHA
WARM_BELIEFS = mrb.WARM_BELIEFS
FIELD = mrb.FIELD
N = mrb.N
M = mrb.M
EDGE_COUNT = mrb.EDGE_COUNT
GRAPH_SEEDS = mrb.GRAPH_SEEDS
VAR_COUNTS = mrb.VAR_COUNTS
CHECK_COUNTS = mrb.CHECK_COUNTS
SHAPE_COUNTS = mrb.SHAPE_COUNTS
SHAPE_TOTAL = mrb.SHAPE_TOTAL
P0 = mrb.P0
HOLDOUT_STREAMS = mrb.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = mrb.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = mrb.HOLDOUT_PAIRS
MAX_CALLS = mrb.MAX_CALLS
WALL_CAP_S = mrb.WALL_CAP_S
CALL_CAP_S = mrb.CALL_CAP_S
RSS_CAP_BYTES = mrb.RSS_CAP_BYTES
SYNDROME_BITS = mrb.SYNDROME_BITS
SIGNAL_DELTA = mrb.SIGNAL_DELTA
SIGNAL_POSITIVE_GRAPHS = mrb.SIGNAL_POSITIVE_GRAPHS
CONTROL_MIN = mrb.CONTROL_MIN
CONTROL_MAX = mrb.CONTROL_MAX
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_mrb_top6_probe "
    "--execute --out-root workspace/gf32_mrb_top6_df44e589"
)

# This is passed explicitly to the retained runner after its narrow E1 seam is
# available. Keeping it local avoids changing the accepted predecessor's
# module constants or output identity.
BATCH_CONTEXT = {
    "batch_uuid": BATCH_UUID,
    "contract": CONTRACT,
    "out_root_relative": str(OUT_ROOT_RELATIVE),
    "seed_namespace": SEED_PREFIX,
    "title": "GF32 MRB belief-ranked top-6 EXPLORE",
    "source_batch_uuid": SOURCE_BATCH_UUID,
    "reaggregation_uuid": REAGGREGATION_UUID,
    "arm_metadata": {
        "control": {"top_symbols": None},
        "candidate": {"top_symbols": 6},
    },
}


def mrb_adapter(top_symbols: int | None,
                mrb_fn: Callable[..., Any] | None = None
                ) -> Callable[..., Any]:
    """Bind the accepted order-1 MRB helper, overriding only top_symbols."""
    if top_symbols not in (None, 6):
        raise ValueError("the frozen MRB arms allow only top_symbols=None or 6")
    helper = mrb_fn or nonbinary_v19_osd.osd_decode_candidates_mrb

    def enumerate_candidates(**kwargs: Any) -> Any:
        call_kwargs = dict(kwargs)
        call_kwargs["top_symbols"] = top_symbols
        return helper(**call_kwargs)

    return enumerate_candidates


def mrb_adapter_for_arm(arm: str,
                        mrb_fn: Callable[..., Any] | None = None
                        ) -> Callable[..., Any]:
    if arm == "control":
        return mrb_adapter(None, mrb_fn)
    if arm == "candidate":
        return mrb_adapter(6, mrb_fn)
    raise ValueError("arm must be control or candidate")


def mrb_fns_by_arm(mrb_fn: Callable[..., Any] | None = None
                   ) -> dict[str, Callable[..., Any]]:
    """Return explicit wrappers whose sole difference is top_symbols."""
    return {
        "control": mrb_adapter_for_arm("control", mrb_fn),
        "candidate": mrb_adapter_for_arm("candidate", mrb_fn),
    }


def holdout_seed(graph_seed: int, stream: int, frame: int) -> int:
    return int(mrb.common.v10_seed(
        "%s:holdout:%d:%d:%d"
        % (SEED_PREFIX, int(graph_seed), int(stream), int(frame))))


def seed_plan() -> list[tuple[int, int, int, int]]:
    return [
        (graph_seed, stream, frame, holdout_seed(graph_seed, stream, frame))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def _validate_seed_plan() -> list[tuple[int, int, int, int]]:
    rows = seed_plan()
    seeds = [row[3] for row in rows]
    if len(rows) != HOLDOUT_PAIRS or len(set(seeds)) != len(rows):
        raise AssertionError("top6 holdout seed plan is incomplete or duplicated")
    if any(set(seeds) & previous for previous in mrb._prior_seed_sets()):
        raise AssertionError("top6 seed namespace overlaps an earlier batch")
    return rows


def verify_t0() -> dict[str, bool]:
    checks = mrb.verify_t0()
    rows = _validate_seed_plan()
    if len(rows) != 192 or MAX_CALLS != 384 or MAX_CANDIDATES != 256:
        raise AssertionError("top6 batch dimensions or caps changed")
    if BATCH_CONTEXT["arm_metadata"] != {
            "control": {"top_symbols": None},
            "candidate": {"top_symbols": 6}}:
        raise AssertionError("top6 arm enum settings changed")
    checks["top6_identity_seed_namespace_and_arm_settings"] = True
    return checks


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen fresh root %s" % expected)
    if resolved.exists():
        raise FileExistsError("refusing existing output root %s" % resolved)
    return resolved


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    return {
        "status": "DRY_RUN", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "out_root": str(root),
        "seed_namespace": SEED_PREFIX, "writes": 0,
        "empirical_input_reads": 0, "artifact_reads": 0,
        "graph_construction_calls": 0, "candidate_construction_calls": 0,
        "decoder_calls": 0, "mrb_calls": 0,
        "pilot_calls": 0, "holdout_pair_count": HOLDOUT_PAIRS,
        "holdout_call_count": MAX_CALLS,
        "mrb_invocation_ceiling": MAX_CALLS,
        "max_candidates_per_rescue": MAX_CANDIDATES,
        "arm_metadata": BATCH_CONTEXT["arm_metadata"], "t0": t0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GF32 MRB top-6 EXPLORE")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check pure math and frozen output path only")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def _rescue_metrics(rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    attempts = [row for row in rows
                if row.get("arm") == arm and row.get("rescue_attempted")]
    selected = [row for row in attempts if row.get("rescue_status") == "rescued"]
    scores = [float(row["selected_prior_score"]) for row in selected
              if row.get("selected_prior_score") is not None]
    return {
        "rescue_attempts": len(attempts),
        "rescues_selected": len(selected),
        "candidate_vectors_examined": sum(
            int(row.get("candidate_count") or 0) for row in attempts
            if row.get("candidate_count") is not None),
        "empty_candidate_lists": sum(
            row.get("rescue_status") == "empty_candidate_list_raw_retained"
            for row in attempts),
        "selected_prior_score_count": len(scores),
        "selected_prior_score_min": min(scores) if scores else None,
        "selected_prior_score_max": max(scores) if scores else None,
        "selected_prior_scores": scores,
        "mrb_helper_wall_s_total": math.fsum(
            float(row.get("mrb_helper_wall_s") or 0.0) for row in attempts),
        "rescue_wall_s_total": math.fsum(
            float(row.get("rescue_wall_s") or 0.0) for row in attempts),
    }


def summarize_top6(rows: list[dict[str, Any]],
                   completed_pairs: list[dict[str, Any]],
                   stop_reason: str) -> dict[str, Any]:
    """Use the accepted paired summary and add actual two-arm MRB costs."""
    summary = mrb._summarize(rows, completed_pairs, stop_reason)
    metrics_by_arm = {
        arm: _rescue_metrics(rows, arm)
        for arm in ("control", "candidate")}
    scores = [score for arm in ("control", "candidate")
              for score in metrics_by_arm[arm]["selected_prior_scores"]]
    summary.update({
        "batch_uuid": BATCH_CONTEXT["batch_uuid"],
        "contract": BATCH_CONTEXT["contract"],
        "seed_namespace": BATCH_CONTEXT["seed_namespace"],
        "out_root_relative": BATCH_CONTEXT["out_root_relative"],
        "source_batch_uuid": BATCH_CONTEXT["source_batch_uuid"],
        "reaggregation_uuid": BATCH_CONTEXT["reaggregation_uuid"],
        "top_symbols_by_arm": {
            arm: metadata["top_symbols"]
            for arm, metadata in BATCH_CONTEXT["arm_metadata"].items()},
        "rescue_metrics_by_arm": metrics_by_arm,
        "rescue_attempts": sum(
            item["rescue_attempts"] for item in metrics_by_arm.values()),
        "rescues_selected": sum(
            item["rescues_selected"] for item in metrics_by_arm.values()),
        "candidate_vectors_examined": sum(
            item["candidate_vectors_examined"] for item in metrics_by_arm.values()),
        "empty_candidate_lists": sum(
            item["empty_candidate_lists"] for item in metrics_by_arm.values()),
        "selected_prior_score_count": len(scores),
        "selected_prior_score_min": min(scores) if scores else None,
        "selected_prior_score_max": max(scores) if scores else None,
        "selected_prior_scores": scores,
        "mrb_helper_wall_s_total": math.fsum(
            item["mrb_helper_wall_s_total"] for item in metrics_by_arm.values()),
        "rescue_wall_s_total": math.fsum(
            item["rescue_wall_s_total"] for item in metrics_by_arm.values()),
        "claim_ceiling": (
            "paired order-1 GF32 MRB comparison differing only in the existing "
            "helper's top_symbols argument (None versus 6), on six fixed deep "
            "H0D graphs under a synthetic iid marginal-shape proxy; no hard "
            "source-support, cross-batch pooling, conditional channel, FER, "
            "f_eff, SKR, throughput, qualification, publication, or route claim"),
    })
    return summary


def execute_batch(*, out_root: str | Path,
                  decode_fn: Callable[..., Any],
                  graph_builder: Callable[[int], dict[str, Any]],
                  candidate_builder: Callable[..., Any] | None = None,
                  mrb_fn: Callable[..., Any] | None = None,
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None) -> dict[str, Any]:
    """Use the accepted paired runner with only the frozen MRB enum delta."""
    return mrb.execute_batch(
        out_root=out_root, decode_fn=decode_fn, graph_builder=graph_builder,
        candidate_builder=candidate_builder,
        mrb_fns_by_arm=mrb_fns_by_arm(mrb_fn), batch_context=BATCH_CONTEXT,
        summary_fn=summarize_top6, command=command, repo_root=repo_root,
        now=now, rss_fn=rss_fn)


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if args.execute:
        result = execute_batch(
            out_root=args.out_root,
            decode_fn=mrb._bind_production_decoder(),
            graph_builder=mrb.search_runner.build_profile_graph,
            command=COMMAND)
    else:
        result = dry_run(args.out_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
