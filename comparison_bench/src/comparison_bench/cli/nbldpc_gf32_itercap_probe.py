"""Bounded GF(32) BP iteration-cap comparison on accepted deep H0D graphs."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_gf32_damping_probe as resource_runner
from comparison_bench.cli import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-ITER-CAP-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "eb0eb231-b295-4c1c-9ddd-4d775bc74352"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_itercap_eb0eb231"
SEED_PREFIX = "gf32-itercap-v1"

CONTROL_ALPHA = 1.0
ARM_MAX_ITER = {"control": 90, "candidate": 250}
WARM_BELIEFS = None
FIELD = None

N = search_runner.N
M = search_runner.M
EDGE_COUNT = search_runner.EDGE_COUNT
GRAPH_SEEDS = tuple(range(2026093901, 2026093907))
SHAPE_COUNTS = search_runner.SHAPE_COUNTS
SHAPE_TOTAL = search_runner.SHAPE_TOTAL
P0 = 0.550
HOLDOUT_STREAMS = tuple(search_runner.HOLDOUT_STREAMS)
HOLDOUT_FRAMES_PER_STREAM = search_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = len(GRAPH_SEEDS) * len(HOLDOUT_STREAMS) * HOLDOUT_FRAMES_PER_STREAM
MAX_CALLS = 2 * HOLDOUT_PAIRS
WALL_CAP_S = 1800.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
SYNDROME_BITS = 5 * M
CONTROL_MIN = 39
CONTROL_MAX = 153
SIGNAL_DELTA = 12
SIGNAL_POSITIVE_GRAPHS = 4
ARTIFACT_LIMIT_BYTES = 20 * 1024 * 1024
ARM_CODE = {"control": 0, "candidate": 1}

FRAME_FIELDS = (
    "call_index", "pair_index", "phase", "graph_seed", "stream", "frame",
    "seed", "arm", "max_iter", "decoder_status", "status", "iterations",
    "raw_vector_saved", "raw_symbols_equal", "syndrome_accept", "exact",
    "syndrome_consistent_wrong", "prefix_check", "wall_s", "rss_b",
    "syndrome_bits", "failure_reason",
)

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_itercap_probe --execute "
    "--out-root workspace/gf32_itercap_eb0eb231"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def seed_for(graph_seed: int, stream: int, frame: int) -> int:
    return int(common.v10_seed(
        f"{SEED_PREFIX}:holdout:{int(graph_seed)}:{int(stream)}:{int(frame)}"))


def seed_plan() -> list[tuple[int, int, int, int]]:
    return [
        (int(graph_seed), int(stream), int(frame),
         seed_for(graph_seed, stream, frame))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def arm_order(frame: int) -> tuple[str, str]:
    return prior_runner.arm_order(frame)


def _validate_seed_plan() -> list[tuple[int, int, int, int]]:
    plan = seed_plan()
    seeds = [row[3] for row in plan]
    old_seed_plans = (
        prior_runner._seed_plan(),
        search_runner.fine_runner.predecessor.seed_plan(),
        search_runner.fine_runner.seed_plan(),
        search_runner.replica_runner.seed_plan(),
        search_runner.seed_plan(),
        resource_runner.seed_plan(),
    )
    old_seeds = {
        int(row[3]) for old_plan in old_seed_plans
        for plan_part in old_plan for row in plan_part
    }
    if (len(plan) != HOLDOUT_PAIRS or len(set(seeds)) != len(seeds)
            or len({(row[0], row[1], row[2]) for row in plan}) != HOLDOUT_PAIRS
            or set(seeds) & old_seeds):
        raise AssertionError(
            "iter-cap seed plan must contain 192 unique, prior-disjoint pairs/seeds")
    if SEED_PREFIX != "gf32-itercap-v1":
        raise AssertionError("iter-cap seed namespace changed")
    return plan


def verify_t0() -> dict[str, bool]:
    """Pure checks only: no source reads, graph construction, sampling or BP."""
    pmf_grid = search_runner.shape_pmf_grid()
    pmf_entry = pmf_grid[0]
    pmf = np.asarray(pmf_entry["pmf"], dtype=np.float64)
    expected_pmf = np.zeros(32, dtype=np.float64)
    expected_pmf[0] = 0.550
    for symbol, count in ((1, 2295), (3, 1126), (7, 557),
                          (15, 304), (31, 146)):
        expected_pmf[symbol] = 0.450 * count / 4428
    if (len(pmf_grid) != 1
            or P0 != 0.550
            or float(pmf_entry["p0"]) != 0.550
            or pmf.shape != (32,)
            or not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12)
            or not np.allclose(pmf, expected_pmf, rtol=0.0, atol=1e-15)
            or not np.all(np.isfinite(pmf))
            or any(pmf[i] != 0 for i in range(32)
                   if i not in (0, 1, 3, 7, 15, 31))):
        raise AssertionError("fixed synthetic PMF weights check failed")
    if ARM_MAX_ITER != {"control": 90, "candidate": 250}:
        raise AssertionError("arm iteration caps changed")
    if CONTROL_ALPHA != 1.0 or WARM_BELIEFS is not None or FIELD is not None:
        raise AssertionError("frozen decoder settings changed")
    if (N, M, EDGE_COUNT, GRAPH_SEEDS) != (
            128, 52, 256, tuple(range(2026093901, 2026093907))):
        raise AssertionError("accepted deep H0D graph profile changed")
    plan = _validate_seed_plan()
    if any(arm_order(frame) not in (
            ("control", "candidate"), ("candidate", "control"))
           for _, _, frame, _ in plan):
        raise AssertionError("paired arm order is invalid")
    return {
        "fixed_graph_profile": True,
        "fixed_pmf_p0_0550": True,
        "fixed_decoder_settings": True,
        "explicit_caps_90_vs_250": True,
        "fresh_seed_namespace_and_unique_pairs": True,
        "192_pairs_384_calls": len(plan) == HOLDOUT_PAIRS
                               and MAX_CALLS == 384,
        "no_production_binding_or_scientific_calls": True,
    }


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError(f"out-root must be the frozen path {expected}")
    from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
    return layout.refuse_out_root(resolved)


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    checks = verify_t0()
    root = validate_out_root(out_root, repo_root=repo_root)
    return {
        "track": "EXPLORE",
        "status": "DRY_RUN",
        "batch_uuid": BATCH_UUID,
        "contract": CONTRACT,
        "out_root": str(root),
        "exists": root.exists(),
        "t0": checks,
        "attempted_decoder_calls": 0,
        "science_calls": 0,
        "artifact_reads": 0,
        "graph_calls": 0,
        "decoder_calls": 0,
        "osd_calls": 0,
        "writes": 0,
    }


def _decoder_adapter(v35_decode: Callable[..., Any],
                     max_iter: int) -> Callable[..., Any]:
    cap = int(max_iter)
    if cap not in (ARM_MAX_ITER["control"], ARM_MAX_ITER["candidate"]):
        raise ValueError("decoder cap must be one of the frozen arm values")

    def decode(h, prior, syndrome):
        return v35_decode(
            h, prior, syndrome, max_iter=cap,
            damping_alpha=CONTROL_ALPHA, warm_beliefs=WARM_BELIEFS,
            field=FIELD)

    return decode


def _bind_production_decoders(
        v35_decode: Callable[..., Any] | None = None
        ) -> dict[str, Callable[..., Any]]:
    if v35_decode is None:
        from comparison_bench.formal_ir import v35_algorithm_development as v35
        v35_decode = v35.decode_row_layered_fftqspa
    return {
        "control": _decoder_adapter(v35_decode, ARM_MAX_ITER["control"]),
        "candidate": _decoder_adapter(v35_decode, ARM_MAX_ITER["candidate"]),
    }


def _initial_manifest(command: str) -> dict[str, Any]:
    pmf_entry = search_runner.shape_pmf_grid()[0]
    plan = _validate_seed_plan()
    return {
        "track": "EXPLORE",
        "batch_uuid": BATCH_UUID,
        "contract": CONTRACT,
        "status": "RUNNING",
        "classification": "INCOMPLETE",
        "command": command,
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "variable_degrees": list(search_runner.VAR_COUNTS),
            "check_degrees": list(search_runner.CHECK_COUNTS),
            "field": "GF(32)/polynomial-37",
            "graph_seeds": list(GRAPH_SEEDS),
            "matrix_source": "accepted deep H0D from SEARCH-DEPTH21cc2d44",
            "same_deep_matrix_for_both_arms": True,
        },
        "source_shape_proxy": {
            "role": "synthetic iid marginal-shape proxy",
            "p0": P0,
            "counts": {str(e): int(count) for e, count in SHAPE_COUNTS},
            "total": int(SHAPE_TOTAL),
            "no_empirical_input_reads": True,
            "not_conditional_channel_reconstruction": True,
        },
        "pmf": {
            key: value for key, value in pmf_entry.items() if key != "pmf"
        },
        "seed_namespace": SEED_PREFIX,
        "seed_plan": {
            "pair_count": len(plan),
            "decoder_call_count": 2 * len(plan),
            "streams": list(HOLDOUT_STREAMS),
            "frames_per_stream": HOLDOUT_FRAMES_PER_STREAM,
            "arm_order": "even control-first; odd candidate-first",
        },
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "schedule": "row_layered",
            "damping_alpha": CONTROL_ALPHA,
            "warm_beliefs": WARM_BELIEFS,
            "field": FIELD,
            "arm_max_iter": dict(ARM_MAX_ITER),
            "only_arm_difference": "max_iter",
            "probability_floor": 1e-15,
            "normalization": "existing v35 normalized/log symbol metrics",
            "raw_result": "capture the same DecoderResult returned by each call",
        },
        "paired_inputs": {
            "same_truth_prior_syndrome_and_deep_H": True,
            "truth_passed_to_decoder": False,
            "truth_used_for_observation_after_decoder_only": True,
        },
        "screen": {
            "control_exact_range_inclusive": [CONTROL_MIN, CONTROL_MAX],
            "delta_min": SIGNAL_DELTA,
            "positive_graphs_min": SIGNAL_POSITIVE_GRAPHS,
            "zero_integrity_resource_authorization_violations": True,
        },
        "budget": {
            "batch_wall_cap_s": WALL_CAP_S,
            "max_arm_wall_s_after_return": CALL_CAP_S,
            "sampled_rss_cap_bytes": RSS_CAP_BYTES,
            "max_decoder_calls": MAX_CALLS,
            "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
            "tag_bits": 0,
            "verification": "NOT_IMPLEMENTED",
            "undetected": "NOT_MEASURED",
            "artifact_payload_cap_bytes": ARTIFACT_LIMIT_BYTES,
        },
        "claim_ceiling": (
            "finite synthetic screen only; no FER, f_eff, SKR, throughput, "
            "security, qualification, publication, real-channel, route, or "
            "cross-batch pooled/ranking claim"),
        "t0": verify_t0(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8")


def _start_outputs(root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FRAME_FIELDS).writeheader()
    (root / "EXPLORATION_LOG.md").write_text(
        "# GF32 BP iteration-cap EXPLORE log\n\n"
        f"Batch UUID: {BATCH_UUID}\n\n"
        f"Contract: {CONTRACT}\n\n"
        "Frozen arms: control max_iter=90; candidate max_iter=250.\n",
        encoding="utf-8")


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {message}\n")


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FRAME_FIELDS).writerow(
            {key: row.get(key) for key in FRAME_FIELDS})


def _classification_counts(rows: Sequence[Mapping[str, Any]],
                           arm: str) -> dict[str, int]:
    selected = [row for row in rows if row.get("arm") == arm]
    walls = [float(row["wall_s"]) for row in selected
             if row.get("wall_s") is not None]
    rss = [int(row["rss_b"]) for row in selected
           if row.get("rss_b") is not None]
    return {
        "attempted": len(selected),
        "exact_and_syndrome": sum(row.get("exact") is True for row in selected),
        "syndrome_valid_wrong": sum(
            row.get("syndrome_consistent_wrong") is True for row in selected),
        "raw_syndrome_fail": sum(row.get("syndrome_accept") is False
                                 for row in selected),
        "unclassified": sum(row.get("exact") is None for row in selected),
        "iterations_sum": sum(int(row["iterations"]) for row in selected),
        "wall_s_sum": float(sum(walls)),
        "max_arm_wall_s": max(walls, default=None),
        "max_sampled_rss_bytes": max(rss, default=None),
    }


def _complete_pairs(rows: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        pair_index = int(row["pair_index"])
        arm = str(row["arm"])
        grouped.setdefault(pair_index, {})[arm] = row
    return grouped


def _summarize(
        rows: Sequence[Mapping[str, Any]], *,
        complete: bool,
        terminal_status: str,
        stop_reason: str | None,
        resource_measurement: Mapping[str, Any],
        resource_stop_markers: Sequence[str] = (),
        integrity_violations: int = 0,
        authorization_violations: int = 0,
        ) -> dict[str, Any]:
    """Reduce retained call rows; a partial batch never gets complete totals."""
    rows = list(rows)
    grouped = _complete_pairs(rows)
    pair_shape_ok = (
        len(grouped) == HOLDOUT_PAIRS
        and all(set(item) == {"control", "candidate"}
                for item in grouped.values())
        and all(row.get("exact") is not None and row.get("syndrome_accept") is not None
                for item in grouped.values() for row in item.values())
    )
    complete = bool(complete and pair_shape_ok and len(rows) == MAX_CALLS)
    result: dict[str, Any] = {
        "track": "EXPLORE",
        "batch_uuid": BATCH_UUID,
        "contract": CONTRACT,
        "complete": complete,
        "terminal_status": terminal_status,
        "classification": "INCOMPLETE",
        "stop_reason": stop_reason,
        "stop_reasons": [stop_reason] if stop_reason else [],
        "attempted_decoder_calls": len(rows),
        "attempted_frame_rows": len(rows),
        "attempted_pairs": len(grouped),
        "completed_pairs": sum(
            set(item) == {"control", "candidate"} for item in grouped.values()),
        "seed_namespace": SEED_PREFIX,
        "fixed_p0": P0,
        "arm_max_iter": dict(ARM_MAX_ITER),
        "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
        "disclosed_syndrome_bits": len(rows) * SYNDROME_BITS,
        "tag_bits": 0,
        "verification": "NOT_IMPLEMENTED",
        "undetected": "NOT_MEASURED",
        "integrity_violations": int(integrity_violations),
        "resource_violations": len(resource_stop_markers),
        "resource_stop_markers": list(resource_stop_markers),
        "authorization_violations": int(authorization_violations),
        "per_arm_attempts": {
            arm: len([row for row in rows if row.get("arm") == arm])
            for arm in ("control", "candidate")
        },
        "resource_measurement": dict(resource_measurement),
        "control_exact": None,
        "candidate_exact": None,
        "delta": None,
        "positive_graphs": None,
        "per_graph": None,
        "paired": None,
        "transitions": None,
        "per_arm_outcomes": None,
    }
    if not complete:
        return result

    control = _classification_counts(rows, "control")
    candidate = _classification_counts(rows, "candidate")
    grouped = _complete_pairs(rows)
    control_exact = int(control["exact_and_syndrome"])
    candidate_exact = int(candidate["exact_and_syndrome"])
    delta = candidate_exact - control_exact
    per_graph: dict[str, dict[str, int]] = {}
    for graph_seed in GRAPH_SEEDS:
        graph_rows = [item for item in grouped.values()
                      if int(item["control"]["graph_seed"]) == int(graph_seed)]
        c = sum(item["control"].get("exact") is True for item in graph_rows)
        k = sum(item["candidate"].get("exact") is True for item in graph_rows)
        per_graph[str(graph_seed)] = {
            "pairs": len(graph_rows),
            "control_exact": int(c),
            "candidate_exact": int(k),
            "delta_g": int(k - c),
        }
    positive = sum(value["delta_g"] > 0 for value in per_graph.values())
    paired = {
        "both": 0, "control_only": 0, "candidate_only": 0, "neither": 0,
    }
    transitions = {
        "control_raw_fail_to_candidate_exact": 0,
        "control_raw_fail_to_candidate_valid_wrong": 0,
        "control_raw_fail_to_candidate_still_fail": 0,
        "control_syndrome_pass_prefix_consistent": 0,
    }
    for item in grouped.values():
        c_row = item["control"]
        k_row = item["candidate"]
        c_ok = c_row.get("exact") is True
        k_ok = k_row.get("exact") is True
        pair_state = {
            (True, True): "both",
            (True, False): "control_only",
            (False, True): "candidate_only",
            (False, False): "neither",
        }[(c_ok, k_ok)]
        paired[pair_state] += 1
        if c_row.get("syndrome_accept") is False:
            if k_row.get("exact") is True:
                transitions["control_raw_fail_to_candidate_exact"] += 1
            elif k_row.get("syndrome_consistent_wrong") is True:
                transitions["control_raw_fail_to_candidate_valid_wrong"] += 1
            elif k_row.get("syndrome_accept") is False:
                transitions["control_raw_fail_to_candidate_still_fail"] += 1
        elif c_row.get("syndrome_accept") is True:
            if k_row.get("prefix_check") == "PASS_CONTROL_SYNDROME_PASS":
                transitions["control_syndrome_pass_prefix_consistent"] += 1

    if not CONTROL_MIN <= control_exact <= CONTROL_MAX:
        classification = "CONTROL_RANGE_UNINFORMATIVE"
    elif (delta >= SIGNAL_DELTA and positive >= SIGNAL_POSITIVE_GRAPHS
          and integrity_violations == 0
          and not resource_stop_markers
          and authorization_violations == 0):
        classification = "MECHANISM_SIGNAL"
    else:
        classification = "NO_SUFFICIENT_SIGNAL"

    result.update({
        "classification": classification,
        "control_exact": control_exact,
        "candidate_exact": candidate_exact,
        "delta": int(delta),
        "positive_graphs": int(positive),
        "per_graph": per_graph,
        "paired": paired,
        "transitions": transitions,
        "per_arm_outcomes": {"control": control, "candidate": candidate},
    })
    return result


def _validated_raw_vector(raw_result: Any) -> np.ndarray | None:
    try:
        raw = np.asarray(raw_result.x_hat)
        if raw.shape != (N,) or not np.issubdtype(raw.dtype, np.integer):
            return None
        if np.any(raw < 0) or np.any(raw >= 32):
            return None
        return raw.astype(np.uint8, copy=True)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _diagnostics_arrays(
        graph_matrices: Mapping[int, np.ndarray],
        pair_inputs: Sequence[Mapping[str, Any]],
        rows: Sequence[Mapping[str, Any]],
        vectors: Sequence[Mapping[str, Any]],
        ) -> dict[str, np.ndarray]:
    graph_seeds = [seed for seed in GRAPH_SEEDS if seed in graph_matrices]
    graph_index = {seed: index for index, seed in enumerate(graph_seeds)}
    matrices = [np.asarray(graph_matrices[seed], dtype=np.uint8)
                for seed in graph_seeds]
    h_stack = (np.stack(matrices) if matrices else
               np.empty((0, M, N), dtype=np.uint8))
    pair_map = {int(pair["pair_index"]): pair for pair in pair_inputs}
    pair_values = list(pair_inputs)
    call_to_vector = {int(value["call_index"]): i
                      for i, value in enumerate(vectors)}
    return {
        "graph_seed": np.asarray(graph_seeds, dtype=np.int64),
        "H": h_stack,
        "pair_index": np.asarray([int(p["pair_index"]) for p in pair_values],
                                 dtype=np.int64),
        "pair_graph_index": np.asarray([
            graph_index[int(p["graph_seed"])] for p in pair_values],
            dtype=np.int64),
        "pair_graph_seed": np.asarray([int(p["graph_seed"]) for p in pair_values],
                                      dtype=np.int64),
        "pair_stream": np.asarray([int(p["stream"]) for p in pair_values],
                                  dtype=np.int64),
        "pair_frame": np.asarray([int(p["frame"]) for p in pair_values],
                                 dtype=np.int64),
        "pair_seed": np.asarray([int(p["seed"]) for p in pair_values],
                                dtype=np.int64),
        "pair_truth": (np.stack([p["truth"] for p in pair_values]).astype(
            np.uint8, copy=False) if pair_values else
            np.empty((0, N), dtype=np.uint8)),
        "pair_syndrome": (np.stack([p["syndrome"] for p in pair_values]).astype(
            np.uint8, copy=False) if pair_values else
            np.empty((0, M), dtype=np.uint8)),
        "call_index": np.asarray([int(row["call_index"]) for row in rows],
                                 dtype=np.int64),
        "call_pair_index": np.asarray([int(row["pair_index"]) for row in rows],
                                      dtype=np.int64),
        "call_arm": np.asarray([str(row["arm"]) for row in rows], dtype="<U9"),
        "call_cap": np.asarray([int(row["max_iter"]) for row in rows],
                               dtype=np.int16),
        "call_vector_index": np.asarray([
            call_to_vector.get(int(row["call_index"]), -1) for row in rows],
            dtype=np.int64),
        "vector_call_index": np.asarray(
            [int(v["call_index"]) for v in vectors], dtype=np.int64),
        "vector_pair_index": np.asarray(
            [int(v["pair_index"]) for v in vectors], dtype=np.int64),
        "vector_arm": np.asarray([str(v["arm"]) for v in vectors], dtype="<U9"),
        "vector_cap": np.asarray([int(v["max_iter"]) for v in vectors],
                                 dtype=np.int16),
        "vector_graph_seed": np.asarray(
            [int(v["graph_seed"]) for v in vectors], dtype=np.int64),
        "vector_stream": np.asarray([int(v["stream"]) for v in vectors],
                                    dtype=np.int64),
        "vector_frame": np.asarray([int(v["frame"]) for v in vectors],
                                   dtype=np.int64),
        "vector_seed": np.asarray([int(v["seed"]) for v in vectors],
                                  dtype=np.int64),
        "raw_x_hat": (np.stack([v["raw_x_hat"] for v in vectors]).astype(
            np.uint8, copy=False) if vectors else
            np.empty((0, N), dtype=np.uint8)),
    }


def _write_diagnostics(root: Path,
                       arrays: Mapping[str, np.ndarray]) -> int:
    payload_bytes = sum(int(value.nbytes) for value in arrays.values())
    if payload_bytes > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz payload exceeds the frozen 20 MiB cap")
    path = root / "diagnostics.npz"
    np.savez_compressed(path, **arrays)
    return int(path.stat().st_size)


def execute_batch(
        *,
        out_root: str | Path,
        decode_fns: Mapping[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]],
        graph_builder: Callable[[int], Mapping[str, Any]],
        candidate_builder: Callable[
            [np.ndarray, np.ndarray, int],
            tuple[np.ndarray | None, np.ndarray | None, Mapping[str, Any]]],
        preflight_fn: Callable[
            [Mapping[str, Any], int], tuple[bool, Mapping[str, Any]]],
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        ) -> dict[str, Any]:
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"control", "candidate"}
            or any(not callable(decode_fns[k]) for k in ("control", "candidate"))):
        raise ValueError("explicit control and candidate decoder callbacks are required")
    if not callable(graph_builder) or not callable(candidate_builder) \
            or not callable(preflight_fn):
        raise ValueError("explicit graph, candidate, and preflight callbacks are required")
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = d5._rss_bytes

    started = float(now())
    rss_samples: list[int] = []

    def sample_rss() -> int | None:
        if rss_monitor_errors:
            return None
        try:
            value = rss_fn()
        except Exception as exc:
            rss_monitor_errors.append(
                f"rss_monitor_exception:{type(exc).__name__}:{exc}")
            return None
        if value is not None:
            rss_samples.append(int(value))
        return value

    rows: list[dict[str, Any]] = []
    pair_inputs: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    graph_matrices: dict[int, np.ndarray] = {}
    candidate_matrices: dict[int, np.ndarray] = {}
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    resource_stop_markers: list[str] = []
    stop_reasons: list[str] = []
    rss_monitor_errors: list[str] = []
    calls = 0
    terminal = "INCOMPLETE"
    manifest = _initial_manifest(COMMAND)
    _start_outputs(root, manifest)
    _append_log(root, "T0 started; no source-data or decoder call has occurred")

    def add_stop(reason: str, *, resource: bool = False,
                 integrity: bool = False) -> None:
        is_new = bool(reason and reason not in stop_reasons)
        if is_new:
            stop_reasons.append(reason)
        if resource and reason and reason not in resource_stop_markers:
            resource_stop_markers.append(reason)
        if integrity and is_new:
            manifest["integrity_violations"] = int(
                manifest.get("integrity_violations", 0)) + 1

    def check_resources(stage: str) -> list[str]:
        reasons: list[str] = []
        # Reuse the accepted pre-call gate while a call remains in the plan.
        # At the final frozen call there is no next-call cap to report.
        helper_reason = (resource_runner._resource_stop(
            started, now, sample_rss, calls) if calls < MAX_CALLS else None)
        if helper_reason == "decoder_call_count_cap_before_next_call":
            reasons.append(f"{helper_reason}:{stage}")
        elif calls >= MAX_CALLS:
            sample_rss()
        elapsed = max(float(now()) - started, 0.0)
        latest_rss = rss_samples[-1] if rss_samples else None
        if elapsed >= WALL_CAP_S:
            reasons.append(f"total_wall_cap:{stage}")
        if latest_rss is not None and latest_rss >= RSS_CAP_BYTES:
            reasons.append(f"rss_cap:{stage}")
        reasons.extend(rss_monitor_errors)
        unique = list(dict.fromkeys(reasons))
        for reason in unique:
            add_stop(reason, resource=True)
        return unique

    def is_resource_reason(reason: str) -> bool:
        return any(token in reason for token in (
            "decoder_call_wall_cap", "total_wall_cap", "rss_cap",
            "resource_abort", "decoder_call_count_cap",
            "rss_monitor_exception",
        ))

    def stop(reason: str, kind: str) -> None:
        nonlocal terminal
        add_stop(reason, resource=(kind == "RESOURCE_STOP"),
                 integrity=(kind == "INTEGRITY_STOP"))
        terminal = kind

    def append_pair_rows(pair_rows: Sequence[dict[str, Any]]) -> None:
        for row in pair_rows:
            rows.append(row)
            _append_row(root, row)

    def make_row(pair: Mapping[str, Any], arm: str, observed: Mapping[str, Any],
                 raw_result: Any, raw_vector: np.ndarray | None,
                 failure_reason: str | None) -> dict[str, Any]:
        cap = int(ARM_MAX_ITER[arm])
        iterations = int(observed.get("iterations", 0))
        raw_equal = (bool(observed["exact"]) if raw_vector is not None else None)
        syndrome_ok = (bool(observed["syndrome_accept"])
                       if raw_vector is not None else None)
        exact = bool(raw_equal and syndrome_ok) \
            if raw_equal is not None and syndrome_ok is not None else None
        wrong = bool(syndrome_ok and not raw_equal) \
            if raw_equal is not None and syndrome_ok is not None else None
        decoder_status = None
        try:
            decoder_status = str(raw_result.status)
        except (AttributeError, TypeError, ValueError):
            pass
        return {
            "call_index": calls - 1,
            "pair_index": int(pair["pair_index"]),
            "phase": "holdout",
            "graph_seed": int(pair["graph_seed"]),
            "stream": int(pair["stream"]),
            "frame": int(pair["frame"]),
            "seed": int(pair["seed"]),
            "arm": arm,
            "max_iter": cap,
            "decoder_status": decoder_status,
            "status": str(observed.get("status", "unknown")),
            "iterations": iterations,
            "raw_vector_saved": raw_vector is not None,
            "raw_symbols_equal": raw_equal,
            "syndrome_accept": syndrome_ok,
            "exact": exact,
            "syndrome_consistent_wrong": wrong,
            "prefix_check": None,
            "wall_s": float(observed.get("wall_s", 0.0)),
            "rss_b": observed.get("rss_b"),
            "syndrome_bits": SYNDROME_BITS,
            "failure_reason": failure_reason,
            "_raw_x_hat": raw_vector,
            "_decoder_status": decoder_status,
        }

    def dispatch(pair: Mapping[str, Any], arm: str,
                 arm_input: Mapping[str, Any]
                 ) -> tuple[dict[str, Any] | None, str | None]:
        nonlocal calls
        resource_reasons = check_resources(f"before_call_{calls}")
        if resource_reasons:
            return None, ";".join(resource_reasons)
        cap = int(ARM_MAX_ITER[arm])
        returned: dict[str, Any] = {}

        def capture_same_return(h, prior, syndrome):
            result = decode_fns[arm](h, prior, syndrome)
            returned["result"] = result
            return result

        calls += 1
        observer_error = None
        try:
            observed, issue = prior_runner.decode_observation(
                capture_same_return,
                np.asarray(arm_input["dense"], dtype=np.int64).copy(),
                np.asarray(arm_input["prior"], dtype=np.float64).copy(),
                np.asarray(arm_input["truth"], dtype=np.int64).copy(),
                np.asarray(arm_input["syndrome"], dtype=np.int64).copy(),
                now=now, rss_fn=sample_rss)
        except Exception as exc:
            observer_error = f"observation_exception:{type(exc).__name__}:{exc}"
            observed = {
                "exact": False, "syndrome_accept": False,
                "syndrome_consistent_wrong": False,
                "status": "observation_exception", "iterations": 0,
                "wall_s": 0.0, "rss_b": sample_rss(),
            }
            issue = observer_error
        raw_result = returned.get("result")
        raw_vector = _validated_raw_vector(raw_result) \
            if raw_result is not None else None
        failure_parts = [str(issue)] if issue else []
        if raw_result is not None and raw_vector is None:
            failure_parts.append("raw_vector_not_validated_for_evidence")
        try:
            iterations = int(observed.get("iterations", -1))
        except (TypeError, ValueError, OverflowError):
            iterations = -1
        call_wall = float(observed.get("wall_s", 0.0))
        latest_rss = observed.get("rss_b")
        if not 0 <= iterations <= cap:
            failure_parts.append("decoder_iteration_count_out_of_arm_cap")
        if raw_vector is not None and observed.get("syndrome_accept") is False \
                and iterations != cap:
            failure_parts.append("raw_syndrome_fail_iterations_not_at_arm_cap")
        if call_wall >= CALL_CAP_S:
            failure_parts.append("decoder_call_wall_cap_after_return")
            add_stop("decoder_call_wall_cap_after_return", resource=True)
        if latest_rss is not None and int(latest_rss) >= RSS_CAP_BYTES:
            failure_parts.append("rss_cap_after_call")
            add_stop("rss_cap_after_call", resource=True)
        after_reasons = check_resources(f"after_call_{calls - 1}")
        failure_parts.extend(after_reasons)

        reason = ";".join(dict.fromkeys(failure_parts)) or None
        row = make_row(pair, arm, observed, raw_result, raw_vector, reason)
        if raw_vector is not None:
            vectors.append({
                "call_index": int(row["call_index"]),
                "pair_index": int(row["pair_index"]),
                "graph_seed": int(row["graph_seed"]),
                "stream": int(row["stream"]),
                "frame": int(row["frame"]),
                "seed": int(row["seed"]),
                "arm": arm,
                "max_iter": cap,
                "raw_x_hat": raw_vector.copy(),
            })
        if reason:
            integrity_markers = (
                "integrity", "iteration_count", "raw_vector",
                "prefix", "pair_input", "observation_exception",
                "decoder_exception", "iterations_not_at_arm_cap",
            )
            is_resource = is_resource_reason(reason)
            is_integrity = any(token in reason for token in integrity_markers)
            stop(reason, "RESOURCE_STOP" if is_resource else "INTEGRITY_STOP")
        return row, reason

    try:
        t0 = verify_t0()
        manifest["t0"] = t0
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS")
        resource = check_resources("before_graph_construction")
        if resource:
            stop(";".join(resource), "RESOURCE_STOP")

        pmf_entry = search_runner.shape_pmf_grid()[0]
        pmf = np.asarray(pmf_entry["pmf"], dtype=np.float64)
        for graph_seed in GRAPH_SEEDS:
            if terminal == "RESOURCE_STOP":
                break
            resource = check_resources(f"before_graph_{graph_seed}")
            if resource:
                stop(";".join(resource), "RESOURCE_STOP")
                break
            graph = graph_builder(int(graph_seed))
            admitted, diagnostic = preflight_fn(graph, int(graph_seed))
            diagnostic_row = dict(diagnostic)
            diagnostic_row["graph_seed"] = int(graph_seed)
            diagnostic_row["admitted"] = bool(admitted)
            graph_diagnostics.append(diagnostic_row)
            dense = graph.get("dense")
            if admitted and dense is not None:
                matrix = np.asarray(dense, dtype=np.int64)
                if matrix.shape == (M, N):
                    graph_matrices[int(graph_seed)] = matrix.copy()
                else:
                    stop(f"graph_shape_invalid:{graph_seed}:{matrix.shape}",
                         "INTEGRITY_STOP")
            else:
                stop(f"graph_preflight_failed:{graph_seed}", "GRAPH_PREFLIGHT_STOP")
            resource = check_resources(f"after_graph_{graph_seed}")
            if resource:
                stop(";".join(resource), "RESOURCE_STOP")
            if terminal != "INCOMPLETE":
                break
        if terminal == "INCOMPLETE":
            for graph_seed in GRAPH_SEEDS:
                if graph_seed not in graph_matrices:
                    continue
                resource = check_resources(f"before_deep_candidate_{graph_seed}")
                if resource:
                    stop(";".join(resource), "RESOURCE_STOP")
                    break
                onepass, deep, diagnostic = candidate_builder(
                    graph_matrices[int(graph_seed)], pmf.copy(), int(graph_seed))
                diagnostic_row = dict(diagnostic)
                diagnostic_row["graph_seed"] = int(graph_seed)
                candidate_diagnostics.append(diagnostic_row)
                construction_stop = bool(
                    diagnostic_row.get("construction_stop", False))
                candidate_admitted = bool(diagnostic_row.get(
                    "candidate_admitted", onepass is not None))
                deep_candidate_admitted = bool(diagnostic_row.get(
                    "deep_candidate_admitted", deep is not None))
                if construction_stop:
                    stop(f"candidate_construction_stop:{graph_seed}",
                         "DEEP_ADMISSION_STOP")
                elif not candidate_admitted:
                    stop(f"candidate_admission_failed:{graph_seed}",
                         "DEEP_ADMISSION_STOP")
                elif onepass is None or deep is None or not deep_candidate_admitted:
                    stop(f"deep_candidate_admission_failed:{graph_seed}",
                         "DEEP_ADMISSION_STOP")
                else:
                    matrix = np.asarray(deep, dtype=np.int64)
                    if matrix.shape != (M, N):
                        stop(f"deep_candidate_shape_invalid:{graph_seed}:{matrix.shape}",
                             "INTEGRITY_STOP")
                    else:
                        candidate_matrices[int(graph_seed)] = matrix.copy()
                resource = check_resources(f"after_deep_candidate_{graph_seed}")
                if resource:
                    stop(";".join(resource), "RESOURCE_STOP")
                if terminal != "INCOMPLETE":
                    break

        if terminal == "INCOMPLETE" and (
                len(graph_matrices) != len(GRAPH_SEEDS)
                or len(candidate_matrices) != len(GRAPH_SEEDS)):
            stop("accepted_graph_or_deep_candidate_set_incomplete",
                 "DEEP_ADMISSION_STOP")

        if terminal == "INCOMPLETE":
            prior = np.tile(pmf, (N, 1))
            for pair_index, (graph_seed, stream, frame, seed) in enumerate(
                    _validate_seed_plan()):
                resource = check_resources(f"before_pair_{pair_index}")
                if resource:
                    stop(";".join(resource), "RESOURCE_STOP")
                    break
                truth = prior_runner.sample_error(seed, pmf, width=N)
                deep = candidate_matrices[int(graph_seed)]
                paired = prior_runner.paired_arm_data(
                    deep, deep, truth, prior)
                control_input = paired["control"]
                candidate_input = paired["candidate"]
                same_inputs = all(
                    np.array_equal(control_input[key], candidate_input[key])
                    for key in ("dense", "prior", "truth", "syndrome"))
                pair_record = {
                    "pair_index": pair_index,
                    "graph_seed": int(graph_seed),
                    "stream": int(stream),
                    "frame": int(frame),
                    "seed": int(seed),
                    "truth": np.asarray(truth, dtype=np.uint8).copy(),
                    "syndrome": np.asarray(
                        control_input["syndrome"], dtype=np.uint8).copy(),
                }
                pair_inputs.append(pair_record)
                if not same_inputs:
                    stop(f"pair_input_mismatch:{pair_index}", "INTEGRITY_STOP")
                    break
                pair_rows: list[dict[str, Any]] = []
                arm_rows: dict[str, dict[str, Any]] = {}
                pair_issue: str | None = None
                for arm in arm_order(frame):
                    row, issue = dispatch(pair_record, arm, paired[arm])
                    if row is not None:
                        arm_rows[arm] = row
                        pair_rows.append(row)
                    if issue:
                        pair_issue = issue
                        break
                if pair_issue is None and set(arm_rows) == {
                        "control", "candidate"}:
                    c_row = arm_rows["control"]
                    k_row = arm_rows["candidate"]
                    if c_row.get("syndrome_accept") is True:
                        consistent = (
                            c_row.get("_raw_x_hat") is not None
                            and k_row.get("_raw_x_hat") is not None
                            and np.array_equal(c_row["_raw_x_hat"],
                                               k_row["_raw_x_hat"])
                            and c_row.get("_decoder_status")
                            == k_row.get("_decoder_status")
                            and c_row.get("iterations") == k_row.get("iterations"))
                        k_row["prefix_check"] = (
                            "PASS_CONTROL_SYNDROME_PASS" if consistent
                            else "FAIL_CONTROL_SYNDROME_PASS")
                        if not consistent:
                            k_row["failure_reason"] = ";".join(
                                part for part in
                                (k_row.get("failure_reason"),
                                 "prefix_control_pass_result_mismatch") if part)
                            pair_issue = "prefix_control_pass_result_mismatch"
                    elif c_row.get("syndrome_accept") is False:
                        violates = (
                            k_row.get("syndrome_accept") is True
                            and int(k_row.get("iterations", -1)) <=
                            ARM_MAX_ITER["control"])
                        k_row["prefix_check"] = (
                            "FAIL_CONTROL_SYNDROME_FAIL" if violates
                            else "PASS_CONTROL_SYNDROME_FAIL")
                        if violates:
                            k_row["failure_reason"] = ";".join(
                                part for part in
                                (k_row.get("failure_reason"),
                                 "prefix_candidate_passed_by_control_cap") if part)
                            pair_issue = "prefix_candidate_passed_by_control_cap"
                append_pair_rows(pair_rows)
                if pair_issue:
                    is_resource = is_resource_reason(pair_issue)
                    stop(pair_issue, "RESOURCE_STOP" if is_resource
                         else "INTEGRITY_STOP")
                    break
                if terminal != "INCOMPLETE":
                    break

        if terminal == "INCOMPLETE" and len(rows) == MAX_CALLS:
            terminal = "COMPLETE"
        elif terminal == "INCOMPLETE":
            stop("batch_ended_before_all_frozen_calls", "INCOMPLETE")

    except Exception as exc:
        primary = f"implementation_exception:{type(exc).__name__}:{exc}"
        add_stop(primary)
        if terminal == "INCOMPLETE":
            terminal = "IMPLEMENTATION_STOP"
        _append_log(root, primary)
        check_resources("after_exception")

    # Retain any resource marker reached at the final evidence boundary.
    final_boundary_resource = check_resources("before_diagnostics_write")
    if final_boundary_resource:
        terminal = "RESOURCE_STOP"
    resource_measurement = {
        "batch_wall_s": max(float(now()) - started, 0.0),
        "max_arm_wall_s": max((float(row["wall_s"]) for row in rows),
                              default=None),
        "max_rss_bytes": max(rss_samples) if rss_samples else None,
        "rss_sample_count": len(rss_samples),
        "rss_scope": "sampled process RSS; not a continuous peak",
        "wall_scope": (
            "includes graph/deep construction, source generation, BP and "
            "diagnostics.npz; excludes compact summary/manifest/log writes"),
    }
    complete = terminal == "COMPLETE" and len(rows) == MAX_CALLS \
        and not stop_reasons
    arrays = _diagnostics_arrays(candidate_matrices, pair_inputs, rows, vectors)
    diagnostics_size = None
    try:
        diagnostics_size = _write_diagnostics(root, arrays)
    except Exception as exc:
        add_stop(f"diagnostics_write:{type(exc).__name__}:{exc}")
        terminal = "ARTIFACT_STOP"
        complete = False
    post_diagnostics_resource = check_resources("after_diagnostics_write")
    if post_diagnostics_resource:
        terminal = "RESOURCE_STOP"
        complete = False
    resource_measurement.update({
        "batch_wall_s": max(float(now()) - started, 0.0),
        "max_rss_bytes": max(rss_samples) if rss_samples else None,
        "rss_sample_count": len(rss_samples),
        "diagnostics_npz_bytes": diagnostics_size,
        "artifact_payload_bytes": sum(int(value.nbytes)
                                      for value in arrays.values()),
    })
    stop_reason = ";".join(stop_reasons) if stop_reasons else None
    integrity_count = int(manifest.get("integrity_violations", 0))
    summary = _summarize(
        rows, complete=complete, terminal_status=terminal,
        stop_reason=stop_reason,
        resource_measurement=resource_measurement,
        resource_stop_markers=resource_stop_markers,
        integrity_violations=integrity_count,
        authorization_violations=0)
    summary["stop_reasons"] = list(stop_reasons)
    summary["attempted_call_counts"] = {
        "control": sum(row.get("arm") == "control" for row in rows),
        "candidate": sum(row.get("arm") == "candidate" for row in rows),
        "total": len(rows),
    }
    summary["diagnostics_npz_bytes"] = diagnostics_size
    summary["diagnostics_vector_count"] = len(vectors)
    summary["graph_diagnostics"] = graph_diagnostics
    summary["candidate_diagnostics"] = candidate_diagnostics
    manifest.update({
        "status": terminal,
        "classification": summary["classification"],
        "stop_reason": stop_reason,
        "stop_reasons": list(stop_reasons),
        "resource_stop_markers": list(resource_stop_markers),
        "integrity_violations": integrity_count,
        "authorization_violations": 0,
        "attempted_decoder_calls": len(rows),
        "attempted_pairs": len(pair_inputs),
        "diagnostics_vector_count": len(vectors),
        "diagnostics_npz_bytes": diagnostics_size,
        "resource_measurement": resource_measurement,
        "graph_diagnostics": graph_diagnostics,
        "candidate_diagnostics": candidate_diagnostics,
    })
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)
    _append_log(
        root,
        f"terminal={terminal}; classification={summary['classification']}; "
        f"calls={len(rows)}; pairs={summary['completed_pairs']}; "
        f"stop_reasons={stop_reason or 'none'}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF(32) BP max_iter 90 versus 250 EXPLORE")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check fixed math, seeds, and fresh output root")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            out_root=args.out_root,
            decode_fns=_bind_production_decoders(),
            graph_builder=search_runner.build_profile_graph,
            candidate_builder=search_runner._candidate_pair_for_graph,
            preflight_fn=search_runner.graph_preflight)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
