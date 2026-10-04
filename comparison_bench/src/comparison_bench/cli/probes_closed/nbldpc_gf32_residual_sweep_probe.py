"""One bounded paired GF(32) residual-ranked row-sweep EXPLORE probe."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_mechanism_pair as mechanism_pair
from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_gf32_residual_sweep as residual_sweep
from comparison_bench.formal_ir import v35_algorithm_development as v35


BATCH_UUID = "c6a0e400-0be5-4043-9fe8-344a33b3addb"
CONTRACT = "NBLDPC-GF32-RESIDUAL-SWEEP-20261004/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-residual-ranked-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_residual_sweep_c6a0e400"
N, M, Q = rescue.N, rescue.M, rescue.Q
MAX_ITER, DAMPING_ALPHA = 90, 1.0
HOLDOUT_PAIRS = rescue.HOLDOUT_PAIRS
MAX_PHYSICAL_CALLS = 385
MAX_PHYSICAL_SWEEPS = 34650
MAX_REFERENCE_APPLIED_KERNELS = 903240
MAX_CANDIDATE_SCORE_KERNELS = 898560
MAX_CANDIDATE_APPLIED_KERNELS = 898560
MAX_KERNEL_EVALUATIONS = 2700360
MAX_SCORE_EDGE_UPDATES = 4423680
MAX_APPLIED_EDGE_UPDATES = 8870400
MAX_EDGE_UPDATES = 13294080
CANARY_CAP_S = 30.0
WALL_CAP_S = 1200.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 20 * 1024 * 1024
SYNDROME_BITS = 260
CONTROL_MIN, CONTROL_MAX = 39, 182
MIN_INCREMENT = 6
MIN_POSITIVE_GRAPHS = 4
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_residual_sweep_probe --execute "
    "--out-root workspace/gf32_residual_sweep_c6a0e400"
)

CALL_FIELDS = (
    "call_index", "pair_index", "graph_id", "graph_seed", "stream", "frame",
    "seed", "role", "status", "decoder_status", "iterations", "wall_s",
    "rss_bytes", "own_syndrome_ok", "syndrome_ok_reported", "exact",
    "syndrome_valid_wrong", "syndrome_failed", "raw_vector_index",
    "belief_call_index", "belief_provenance", "extrinsic_provenance",
    "score_check_updates", "applied_check_updates", "score_edge_updates",
    "applied_edge_updates", "row_order_offset_start", "row_order_offset_end",
    "first_sweep_score_offset_start", "first_sweep_score_offset_end",
    "canary_reference_call_index", "canary_aux_call_index", "failure_reason",
)
FRAME_FIELDS = (
    "pair_index", "graph_id", "graph_seed", "stream", "frame", "seed",
    "completed", "control_call_index", "candidate_call_index", "arm_order",
    "control_exact", "candidate_exact", "control_syndrome_failed",
    "candidate_syndrome_failed", "control_syndrome_valid_wrong",
    "candidate_syndrome_valid_wrong",
)


def _repo_root() -> Path:
    return rescue._repo_root()


def _additional_excluded_plans() -> tuple[
        tuple[str, Sequence[Sequence[int]]], ...]:
    # Existing rescue exclusions (13), joint-top3's frozen 9 inherited
    # exclusions, and the joint-top3 namespace itself give 23 total plans.
    plans = list(mechanism_pair._additional_excluded_plans("jointtop3"))
    top3 = mechanism_pair._profile("jointtop3")
    plans.append((f"jointtop3/{top3['seed_namespace']}",
                  mechanism_pair.build_seed_plan("jointtop3")))
    return tuple(plans)


def validate_seed_plan(
        plan: Sequence[Sequence[int]] | None = None
        ) -> tuple[list[tuple[int, int, int, int]], list[dict[str, Any]]]:
    """Validate this namespace against the inherited frozen exclusion union."""
    return rescue.validate_seed_plan(
        plan, seed_namespace=SEED_NAMESPACE,
        additional_excluded_plans=_additional_excluded_plans())


def verify_t0() -> dict[str, Any]:
    rows, exclusions = validate_seed_plan()
    if (len(rows) != HOLDOUT_PAIRS or len(rows) != 192
            or len({row[3] for row in rows}) != HOLDOUT_PAIRS
            or len(exclusions) != 23
            or sum(int(row["rows"]) for row in exclusions) != 4752
            or not np.isclose(rescue.pmf().sum(), 1.0, atol=1e-15)):
        raise AssertionError("frozen residual sweep seed plan or PMF is invalid")
    return {
        "status": "PASS", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE, "holdout_pairs": HOLDOUT_PAIRS,
        "prior_exclusion_plan_count": len(exclusions),
        "prior_exclusion_rows": sum(int(row["rows"]) for row in exclusions),
        "source_reads": 0, "sampler_calls": 0, "decoder_calls": 0,
        "writes": 0,
    }


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None, *,
            official_root: str | Path = OUT_ROOT_RELATIVE) -> dict[str, Any]:
    root = rescue.validate_out_root(
        out_root, repo_root=repo_root, official_root=official_root)
    return {
        "status": "DRY_RUN", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "out_root": str(root), "source_reads": 0, "sampler_calls": 0,
        "decoder_calls": 0, "writes": 0, "t0": verify_t0(),
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               default=_json_default) + "\n", encoding="utf-8")


def _append_log(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def _csv_cell(value: Any) -> Any:
    if isinstance(value, (list, tuple, dict, np.ndarray)):
        return json.dumps(value, separators=(",", ":"), default=_json_default)
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return _json_default(value)
    return value


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_cell(row.get(key)) for key in fields})


def _result_fields(
        calls: Sequence[Mapping[str, Any]], frames: Sequence[Mapping[str, Any]],
        selected_sources: Sequence[Mapping[str, Any]], original_prior: np.ndarray,
        raw_vectors: Sequence[np.ndarray], raw_vector_call_indices: Sequence[int],
        final_beliefs: Sequence[np.ndarray], belief_call_indices: Sequence[int],
        row_order_call_indices: Sequence[int], row_order_sweeps: Sequence[int],
        row_order_offsets: Sequence[int], row_order_values: Sequence[int],
        score_call_indices: Sequence[int], score_values: Sequence[Sequence[float]],
        canary: Mapping[str, Any]) -> dict[str, np.ndarray]:
    sampled = [row for row in frames if row.get("truth") is not None]
    arrays: dict[str, np.ndarray] = {
        "source_H": (np.stack([row["H"] for row in selected_sources]).astype(np.uint8)
                     if selected_sources else np.empty((0, M, N), dtype=np.uint8)),
        "source_graph_id": np.asarray(
            [row["graph_id"] for row in selected_sources], dtype=np.int64),
        "source_deep_row_index": np.asarray(
            [row["deep_row_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_row_index": np.asarray(
            [row["constructor_row_index"] for row in selected_sources], dtype=np.int64),
        "source_profile_index": np.asarray(
            [row["profile_index"] for row in selected_sources], dtype=np.int64),
        "source_graph_index": np.asarray(
            [row["graph_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_uuid": np.asarray([
            row["source_lineage"]["source_uuid"] for row in selected_sources], dtype="<U36"),
        "source_constructor_path": np.asarray([
            row["source_lineage"]["source_path"] for row in selected_sources], dtype="<U160"),
        "source_constructor_matrix_index": np.asarray([
            row["source_lineage"]["source_matrix_index"] for row in selected_sources],
            dtype=np.int64),
        "source_constructor_attempt_j": np.asarray([
            row["source_lineage"]["source_attempt_j"] for row in selected_sources],
            dtype=np.int64),
        "source_constructor_seed": np.asarray([
            row["source_lineage"]["source_construction_seed"]
            for row in selected_sources], dtype=np.int64),
        "source_constructor_graph_id": np.asarray([
            row["source_lineage"]["source_graph_id"]
            for row in selected_sources], dtype=np.int64),
        "original_prior": np.asarray(original_prior, dtype=np.float64),
        "pair_index": np.asarray([row["pair_index"] for row in sampled], dtype=np.int64),
        "pair_graph_id": np.asarray([row["graph_id"] for row in sampled], dtype=np.int64),
        "pair_stream": np.asarray([row["stream"] for row in sampled], dtype=np.int8),
        "pair_frame": np.asarray([row["frame"] for row in sampled], dtype=np.int8),
        "pair_seed": np.asarray([row["seed"] for row in sampled], dtype=np.int64),
        "pair_truth": (np.stack([row["truth"] for row in sampled]).astype(np.uint8)
                       if sampled else np.empty((0, N), dtype=np.uint8)),
        "pair_syndrome": (np.stack([row["syndrome"] for row in sampled]).astype(np.uint8)
                          if sampled else np.empty((0, M), dtype=np.uint8)),
        "call_index": np.asarray([row["call_index"] for row in calls], dtype=np.int64),
        "call_pair_index": np.asarray([row["pair_index"] for row in calls], dtype=np.int64),
        "call_role": np.asarray([row["role"] for row in calls], dtype="<U24"),
        "raw_vector_call_index": np.asarray(raw_vector_call_indices, dtype=np.int64),
        "raw_x_hat": (np.stack(raw_vectors).astype(np.uint8) if raw_vectors
                      else np.empty((0, N), dtype=np.uint8)),
        "belief_call_index": np.asarray(belief_call_indices, dtype=np.int64),
        "final_beliefs": (np.stack(final_beliefs).astype(np.float64) if final_beliefs
                          else np.empty((0, N, Q), dtype=np.float64)),
        "row_order_call_index": np.asarray(row_order_call_indices, dtype=np.int64),
        "row_order_sweep": np.asarray(row_order_sweeps, dtype=np.int16),
        "row_order_offsets": np.asarray(row_order_offsets, dtype=np.int64),
        "row_order_values": np.asarray(row_order_values, dtype=np.uint8),
        "first_sweep_score_call_index": np.asarray(score_call_indices, dtype=np.int64),
        "first_sweep_residuals": (np.asarray(score_values, dtype=np.float64).reshape((-1, M))
                                   if score_values else np.empty((0, M), dtype=np.float64)),
        "canary_reference_call_index": np.asarray(
            [-1 if canary.get("reference_call_index") is None
             else canary["reference_call_index"]], dtype=np.int64),
        "canary_aux_call_index": np.asarray(
            [-1 if canary.get("aux_call_index") is None
             else canary["aux_call_index"]], dtype=np.int64),
        "canary_max_abs_belief_diff": np.asarray(
            [np.nan if canary.get("max_abs_belief_diff") is None
             else canary["max_abs_belief_diff"]], dtype=np.float64),
    }
    return arrays


def _classify(summary: Mapping[str, Any]) -> str:
    control = int(summary["control_exact"])
    candidate = int(summary["candidate_exact"])
    if not CONTROL_MIN <= control <= CONTROL_MAX:
        return "CONTROL_RANGE_UNINFORMATIVE"
    if (candidate - control >= MIN_INCREMENT
            and int(summary["positive_graph_deltas"]) >= MIN_POSITIVE_GRAPHS
            and int(summary["candidate_syndrome_valid_wrong"])
            <= int(summary["control_syndrome_valid_wrong"])
            and int(summary["integrity_violations"]) == 0
            and int(summary["resource_violations"]) == 0
            and int(summary["authorization_violations"]) == 0):
        return "EXPLORATORY_INCREMENT_SIGNAL"
    return "INCREMENT_NOT_ESTABLISHED"


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]], sampler: Callable[..., Any],
        decode_fns: Mapping[str, Callable[..., Any]], out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        official_root: str | Path = OUT_ROOT_RELATIVE) -> dict[str, Any]:
    """Run the frozen paired screen using only explicit source/sampler/decoder seams."""
    root = rescue.validate_out_root(out_root, repo_root=repo_root,
                                    official_root=official_root)
    if not callable(source_reader) or not callable(sampler):
        raise ValueError("explicit source_reader and sampler callbacks are required")
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"reference", "natural", "residual"}
            or any(not callable(decode_fns[key]) for key in decode_fns)):
        raise ValueError("decode_fns must provide reference, natural, and residual callbacks")
    rss_read = rescue._rss_bytes if rss_fn is None else rss_fn
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    log_path.write_text(
        f"EXPLORE {BATCH_UUID} started; R1-R5 frozen; one-shot root.\n",
        encoding="utf-8")
    started = float(now())

    summary: dict[str, Any] = {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE, "run_status": "RUNNING",
        "classification": None, "stop_reasons": [],
        "integrity_violations": 0, "resource_violations": 0,
        "authorization_violations": 0, "data_violations": 0,
        "planned_pairs": HOLDOUT_PAIRS, "completed_pairs": 0,
        "attempted_physical_calls": 0, "completed_physical_calls": 0,
        "physical_calls": 0, "physical_sweeps": 0,
        "control_calls": 0, "candidate_calls": 0, "auxiliary_calls": 0,
        "control_iterations": 0, "candidate_iterations": 0,
        "auxiliary_iterations": 0, "score_check_updates": 0,
        "applied_check_updates": 0, "score_edge_updates": 0,
        "applied_edge_updates": 0, "kernel_evaluations": 0,
        "edge_updates": 0, "peak_rss_bytes": None,
        "reference_applied_kernel_updates": 0,
        "candidate_score_kernel_updates": 0,
        "candidate_applied_kernel_updates": 0,
        "reference_applied_edge_updates": 0,
        "candidate_score_edge_updates": 0,
        "candidate_applied_edge_updates": 0,
        "batch_wall_s": None, "output_bytes": None,
        "sampled_pairs": 0, "shared_public_syndrome_bits": 0,
        "control_public_syndrome_bits": 0,
        "candidate_public_syndrome_bits": 0,
        "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
        "undetected": "NOT_MEASURED",
        "caps": {
            "max_physical_calls": MAX_PHYSICAL_CALLS,
            "max_physical_sweeps": MAX_PHYSICAL_SWEEPS,
            "max_kernel_evaluations": MAX_KERNEL_EVALUATIONS,
            "max_edge_updates": MAX_EDGE_UPDATES,
            "canary_wall_s": CANARY_CAP_S, "total_wall_s": WALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES, "artifact_bytes": ARTIFACT_CAP_BYTES,
        },
    }
    plan: list[tuple[int, int, int, int]] = []
    exclusions: list[dict[str, Any]] = []
    source_identity: dict[str, str] | None = None
    selected_sources: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    raw_vectors: list[np.ndarray] = []
    raw_vector_call_indices: list[int] = []
    own_syndromes: list[np.ndarray] = []
    own_syndrome_call_indices: list[int] = []
    final_beliefs: list[np.ndarray] = []
    belief_call_indices: list[int] = []
    row_order_call_indices: list[int] = []
    row_order_sweeps: list[int] = []
    row_order_offsets = [0]
    row_order_values: list[int] = []
    score_call_indices: list[int] = []
    score_values: list[Sequence[float]] = []
    canary: dict[str, Any] = {
        "reference_call_index": None, "aux_call_index": None,
        "passed": None, "checks": {}, "max_abs_belief_diff": None,
        "total_wall_s": None,
    }
    resource_events: list[str] = []
    run_status = "RUNNING"
    original_pmf = rescue.pmf()
    original_prior = np.tile(original_pmf, (N, 1))

    def stop(status: str, reason: str, kind: str) -> None:
        nonlocal run_status
        if run_status != "RUNNING":
            return
        run_status = status
        summary["run_status"] = status
        if reason not in summary["stop_reasons"]:
            summary["stop_reasons"].append(reason)
        key = f"{kind}_violations"
        if key in summary:
            summary[key] += 1

    def check_resources(phase: str, *, call_wall: float | None = None) -> bool:
        elapsed = max(float(now()) - started, 0.0)
        rss_value = rss_read()
        if rss_value is not None:
            rss_value = int(rss_value)
            current = summary["peak_rss_bytes"]
            summary["peak_rss_bytes"] = rss_value if current is None else max(current, rss_value)
        reasons = []
        if elapsed > WALL_CAP_S:
            reasons.append("total_wall_cap")
        if rss_value is not None and rss_value > RSS_CAP_BYTES:
            reasons.append("rss_cap")
        if summary["attempted_physical_calls"] > MAX_PHYSICAL_CALLS:
            reasons.append("physical_call_cap")
        if summary["physical_sweeps"] > MAX_PHYSICAL_SWEEPS:
            reasons.append("physical_sweep_cap")
        if summary["kernel_evaluations"] > MAX_KERNEL_EVALUATIONS:
            reasons.append("kernel_evaluation_cap")
        if summary["edge_updates"] > MAX_EDGE_UPDATES:
            reasons.append("edge_update_cap")
        if summary["reference_applied_kernel_updates"] > MAX_REFERENCE_APPLIED_KERNELS:
            reasons.append("reference_kernel_cap")
        if summary["candidate_score_kernel_updates"] > MAX_CANDIDATE_SCORE_KERNELS:
            reasons.append("candidate_score_kernel_cap")
        if summary["candidate_applied_kernel_updates"] > MAX_CANDIDATE_APPLIED_KERNELS:
            reasons.append("candidate_applied_kernel_cap")
        if summary["candidate_score_edge_updates"] > MAX_SCORE_EDGE_UPDATES:
            reasons.append("candidate_score_edge_cap")
        if summary["candidate_applied_edge_updates"] + \
                summary["reference_applied_edge_updates"] > MAX_APPLIED_EDGE_UPDATES:
            reasons.append("applied_edge_cap")
        if reasons:
            resource_events.extend(f"{phase}:{reason}" for reason in reasons)
            stop("INCOMPLETE", ";".join(reasons), "resource")
            return False
        return True

    def call_decoder(pair: dict[str, Any], role: str, key: str) -> dict[str, Any] | None:
        if run_status != "RUNNING":
            return None
        if summary["attempted_physical_calls"] >= MAX_PHYSICAL_CALLS:
            stop("INCOMPLETE", "physical_call_cap", "resource")
            return None
        if not check_resources(f"before_{role}"):
            return None
        index = len(calls)
        row: dict[str, Any] = {
            "call_index": index, "pair_index": int(pair["pair_index"]),
            "graph_id": int(pair["graph_id"]), "graph_seed": int(pair["graph_id"]),
            "stream": int(pair["stream"]), "frame": int(pair["frame"]),
            "seed": int(pair["seed"]), "role": role, "status": "RUNNING",
            "decoder_status": None, "iterations": None, "wall_s": None,
            "rss_bytes": None, "own_syndrome_ok": None,
            "syndrome_ok_reported": None, "exact": None,
            "syndrome_valid_wrong": None, "syndrome_failed": None,
            "raw_vector_index": None, "belief_call_index": None,
            "belief_provenance": None, "extrinsic_provenance": None,
            "score_check_updates": 0, "applied_check_updates": 0,
            "score_edge_updates": 0, "applied_edge_updates": 0,
            "row_order_offset_start": len(row_order_values),
            "row_order_offset_end": len(row_order_values),
            "first_sweep_score_offset_start": len(score_values),
            "first_sweep_score_offset_end": len(score_values),
            "canary_reference_call_index": canary.get("reference_call_index"),
            "canary_aux_call_index": canary.get("aux_call_index"),
            "failure_reason": "",
            "_x_hat": None, "_beliefs": None, "_own_syndrome": None,
            "_row_orders": (), "_first_scores": (),
        }
        calls.append(row)
        summary["attempted_physical_calls"] += 1
        call_started = float(now())
        try:
            raw = decode_fns[key](
                pair["H"], original_prior.copy(), pair["syndrome"],
                max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA,
                warm_beliefs=None, field=None)
        except Exception as exc:
            row["wall_s"] = max(float(now()) - call_started, 0.0)
            row["status"] = "FAILED"
            row["failure_reason"] = f"decoder_error:{type(exc).__name__}:{exc}"
            stop("STOP", row["failure_reason"], "integrity")
            check_resources(f"after_failed_{role}", call_wall=row["wall_s"])
            return None

        wall = max(float(now()) - call_started, 0.0)
        row["wall_s"] = wall
        try:
            vector = np.asarray(raw.x_hat)
            if (vector.shape != (N,) or not np.issubdtype(vector.dtype, np.integer)
                    or np.any(vector < 0) or np.any(vector >= Q)):
                raise ValueError("x_hat must be an integer GF(32) vector of length 128")
            vector = vector.astype(np.uint8, copy=True)
            iterations = int(raw.iterations)
            if not 0 <= iterations <= MAX_ITER:
                raise ValueError("iterations must be in [0,90]")
            row["iterations"] = iterations
            summary["physical_sweeps"] += iterations
            beliefs = np.asarray(raw.final_beliefs, dtype=np.float64)
            if beliefs.shape != (N, Q) or not np.all(np.isfinite(beliefs)):
                raise ValueError("final_beliefs must be finite shape (128,32)")
            own_syndrome = np.asarray(
                rescue.layout.gf32_syndrome(pair["H"], vector), dtype=np.uint8).ravel()
            own_valid = bool(np.array_equal(own_syndrome, pair["syndrome"]))
            reported = getattr(raw, "syndrome_ok", None)
            if reported is not None and bool(reported) != own_valid:
                raise ValueError("reported syndrome_ok disagrees with recomputed syndrome")
            graph_edges = int(np.count_nonzero(pair["H"]))
            if role == "control_reference":
                score_checks, applied_checks = 0, iterations * M
                score_edges, applied_edges = 0, iterations * graph_edges
            else:
                score_checks = int(getattr(raw, "score_check_updates", 0))
                applied_checks = int(getattr(raw, "applied_check_updates", -1))
                score_edges = int(getattr(raw, "score_edge_updates", 0))
                applied_edges = int(getattr(raw, "applied_edge_updates", -1))
                if (min(score_checks, applied_checks, score_edges, applied_edges) < 0
                        or applied_checks != iterations * M
                        or applied_edges != iterations * graph_edges):
                    raise ValueError("helper work counters disagree with complete sweeps")
                if role == "canary_aux_natural" and (
                        score_checks != 0 or score_edges != 0):
                    raise ValueError("natural canary must not perform residual scoring")
                if role == "residual_candidate" and (
                        score_checks != iterations * M
                        or score_edges != iterations * graph_edges):
                    raise ValueError("residual score work differs from complete sweeps")

            row_orders = tuple(tuple(int(index) for index in order)
                               for order in getattr(raw, "row_orders", ()))
            first_scores = tuple(float(value) for value in
                                 getattr(raw, "first_sweep_residuals", ()))
            if role != "control_reference":
                if len(row_orders) != iterations:
                    raise ValueError("helper row-order trace must contain every complete sweep")
                expected_order = tuple(range(M))
                if any(len(order) != M or tuple(sorted(order)) != expected_order
                       for order in row_orders):
                    raise ValueError("helper row order is not a permutation of all checks")
                if role == "canary_aux_natural":
                    if first_scores or any(order != expected_order for order in row_orders):
                        raise ValueError("natural canary must have natural order and no scores")
                elif ((iterations == 0 and first_scores)
                      or (iterations > 0 and (len(first_scores) != M
                                              or not np.all(np.isfinite(first_scores))))):
                    raise ValueError("residual first-sweep score row is incomplete/nonfinite")

            row.update({
                "status": "COMPLETE", "decoder_status": str(raw.status),
                "iterations": iterations, "own_syndrome_ok": own_valid,
                "syndrome_ok_reported": None if reported is None else bool(reported),
                "exact": bool(own_valid and np.array_equal(vector, pair["truth"])),
                "syndrome_valid_wrong": bool(own_valid and not np.array_equal(
                    vector, pair["truth"])),
                "syndrome_failed": not own_valid,
                "raw_vector_index": len(raw_vectors),
                "belief_call_index": index,
                "belief_provenance": getattr(raw, "belief_provenance", None),
                "extrinsic_provenance": getattr(raw, "extrinsic_provenance", None),
                "score_check_updates": score_checks,
                "applied_check_updates": applied_checks,
                "score_edge_updates": score_edges,
                "applied_edge_updates": applied_edges,
                "_x_hat": vector, "_beliefs": beliefs.copy(),
                "_own_syndrome": own_syndrome.copy(),
                "_row_orders": row_orders, "_first_scores": first_scores,
            })
            row["failure_reason"] = ""
            raw_vectors.append(vector)
            raw_vector_call_indices.append(index)
            own_syndromes.append(own_syndrome.copy())
            own_syndrome_call_indices.append(index)
            final_beliefs.append(beliefs.copy())
            belief_call_indices.append(index)
            row_order_start = len(row_order_values)
            for sweep_idx, order in enumerate(row_orders, start=1):
                row_order_call_indices.append(index)
                row_order_sweeps.append(sweep_idx)
                row_order_values.extend(order)
                row_order_offsets.append(len(row_order_values))
            row["row_order_offset_start"] = row_order_start
            row["row_order_offset_end"] = len(row_order_values)
            if first_scores:
                score_call_indices.append(index)
                score_values.append(first_scores)
            row["first_sweep_score_offset_end"] = len(score_values)
            summary["completed_physical_calls"] += 1
            summary["score_check_updates"] += score_checks
            summary["applied_check_updates"] += applied_checks
            summary["score_edge_updates"] += score_edges
            summary["applied_edge_updates"] += applied_edges
            summary["kernel_evaluations"] += score_checks + applied_checks
            summary["edge_updates"] += score_edges + applied_edges
            if role == "control_reference":
                summary["control_calls"] += 1
                summary["control_iterations"] += iterations
                summary["control_public_syndrome_bits"] += SYNDROME_BITS
                summary["reference_applied_kernel_updates"] += applied_checks
                summary["reference_applied_edge_updates"] += applied_edges
            elif role == "residual_candidate":
                summary["candidate_calls"] += 1
                summary["candidate_iterations"] += iterations
                summary["candidate_public_syndrome_bits"] += SYNDROME_BITS
                summary["candidate_score_kernel_updates"] += score_checks
                summary["candidate_applied_kernel_updates"] += applied_checks
                summary["candidate_score_edge_updates"] += score_edges
                summary["candidate_applied_edge_updates"] += applied_edges
            else:
                summary["auxiliary_calls"] += 1
                summary["auxiliary_iterations"] += iterations
                summary["reference_applied_kernel_updates"] += applied_checks
                summary["reference_applied_edge_updates"] += applied_edges
        except Exception as exc:
            row["status"] = "FAILED"
            row["failure_reason"] = f"decoder_result_invalid:{type(exc).__name__}:{exc}"
            stop("STOP", row["failure_reason"], "integrity")
            return None

        if not check_resources(f"after_{role}", call_wall=wall):
            row["status"] = "RESOURCE_STOP_AFTER_RETURN"
            row["failure_reason"] = summary["stop_reasons"][-1]
            return None
        return row

    def finish_frame(frame: dict[str, Any], control: Mapping[str, Any],
                     candidate: Mapping[str, Any]) -> None:
        control_exact = bool(control["exact"])
        candidate_exact = bool(candidate["exact"])
        frame.update({
            "completed": True,
            "control_call_index": int(control["call_index"]),
            "candidate_call_index": int(candidate["call_index"]),
            "control_exact": control_exact, "candidate_exact": candidate_exact,
            "control_syndrome_failed": bool(control["syndrome_failed"]),
            "candidate_syndrome_failed": bool(candidate["syndrome_failed"]),
            "control_syndrome_valid_wrong": bool(control["syndrome_valid_wrong"]),
            "candidate_syndrome_valid_wrong": bool(candidate["syndrome_valid_wrong"]),
        })
        summary["completed_pairs"] += 1

    try:
        plan, exclusions = rescue.validate_seed_plan(
            seed_namespace=SEED_NAMESPACE,
            additional_excluded_plans=_additional_excluded_plans())
        summary["prior_exclusion_plan_count"] = len(exclusions)
        summary["prior_exclusion_rows"] = sum(int(row["rows"]) for row in exclusions)
        if len(plan) != HOLDOUT_PAIRS or len(exclusions) != 23 \
                or summary["prior_exclusion_rows"] != 4752:
            raise ValueError("frozen seed/exclusion counts changed")
    except Exception as exc:
        stop("STOP", f"seed_plan:{type(exc).__name__}:{exc}", "authorization")

    if run_status == "RUNNING":
        try:
            source_identity, selected_sources = rescue.select_sources(source_reader())
            if len(selected_sources) != len(rescue.GRAPH_IDS):
                raise ValueError("source selection did not return all six frozen graphs")
        except Exception as exc:
            stop("STOP", f"source:{type(exc).__name__}:{exc}", "data")

    source_by_graph = {int(row["graph_id"]): row for row in selected_sources}
    plan_by_key = {(graph, stream, frame): seed
                   for graph, stream, frame, seed in plan}
    planned_map = []
    for pair_index, (graph_id, stream, frame, seed) in enumerate(plan):
        planned_map.append({"pair_index": pair_index, "graph_id": graph_id,
                            "stream": stream, "frame": frame, "seed": seed})
    canary_start: float | None = None

    for graph_id in rescue.GRAPH_IDS:
        for stream in rescue.HOLDOUT_STREAMS:
            for frame_idx in range(rescue.HOLDOUT_FRAMES_PER_STREAM):
                if run_status != "RUNNING":
                    break
                if not check_resources("before_sample"):
                    break
                pair_index = len(frames)
                seed = int(plan_by_key[(graph_id, stream, frame_idx)])
                graph = source_by_graph.get(int(graph_id))
                if graph is None:
                    stop("STOP", f"missing_selected_graph:{graph_id}", "data")
                    break
                try:
                    truth = np.asarray(sampler(seed, original_pmf.copy(), width=N))
                    if (truth.shape != (N,) or not np.issubdtype(truth.dtype, np.integer)
                            or np.any(truth < 0) or np.any(truth >= Q)):
                        raise ValueError("sampler must return an integer GF(32) vector of length 128")
                    truth = truth.astype(np.uint8, copy=True)
                    h_matrix = np.asarray(graph["H"], dtype=np.uint8).copy()
                    syndrome = np.asarray(
                        rescue.layout.gf32_syndrome(h_matrix, truth), dtype=np.uint8).ravel()
                    if syndrome.shape != (M,):
                        raise ValueError("sampled truth produced an invalid syndrome shape")
                except Exception as exc:
                    stop("STOP", f"sampler:{type(exc).__name__}:{exc}", "data")
                    break
                pair: dict[str, Any] = {
                    "pair_index": pair_index, "graph_id": int(graph_id),
                    "stream": int(stream), "frame": int(frame_idx),
                    "seed": seed, "truth": truth, "syndrome": syndrome,
                    "H": h_matrix,
                }
                frame_row: dict[str, Any] = {
                    "pair_index": pair_index, "graph_id": int(graph_id),
                    "graph_seed": int(graph_id), "stream": int(stream),
                    "frame": int(frame_idx), "seed": seed,
                    "truth": truth, "syndrome": syndrome,
                    "completed": False, "control_call_index": -1,
                    "candidate_call_index": -1,
                    "arm_order": "canary_C_aux_T" if pair_index == 0 else
                        ("C_first" if frame_idx % 2 == 0 else "T_first"),
                    "control_exact": None, "candidate_exact": None,
                    "control_syndrome_failed": None,
                    "candidate_syndrome_failed": None,
                    "control_syndrome_valid_wrong": None,
                    "candidate_syndrome_valid_wrong": None,
                }
                frames.append(frame_row)
                summary["sampled_pairs"] += 1
                summary["shared_public_syndrome_bits"] += SYNDROME_BITS

                control_call: dict[str, Any] | None = None
                candidate_call: dict[str, Any] | None = None
                if pair_index == 0:
                    canary_start = float(now())
                    control_call = call_decoder(pair, "control_reference", "reference")
                    if control_call is None or run_status != "RUNNING":
                        break
                    canary["reference_call_index"] = int(control_call["call_index"])
                    auxiliary = call_decoder(pair, "canary_aux_natural", "natural")
                    if auxiliary is None or run_status != "RUNNING":
                        break
                    canary["aux_call_index"] = int(auxiliary["call_index"])
                    ref_syndrome = np.asarray(control_call["_own_syndrome"])
                    aux_syndrome = np.asarray(auxiliary["_own_syndrome"])
                    belief_diff = np.asarray(control_call["_beliefs"]) - np.asarray(
                        auxiliary["_beliefs"])
                    max_abs = float(np.max(np.abs(belief_diff)))
                    canary_wall = max(float(now()) - canary_start, 0.0)
                    checks = {
                        "x_hat_equal": bool(np.array_equal(control_call["_x_hat"],
                                                            auxiliary["_x_hat"])),
                        "status_equal": control_call["decoder_status"] == auxiliary["decoder_status"],
                        "iterations_equal": control_call["iterations"] == auxiliary["iterations"],
                        "own_syndrome_equal": bool(np.array_equal(ref_syndrome, aux_syndrome)),
                        "final_beliefs_atol_1e12_rtol_0": bool(np.allclose(
                            control_call["_beliefs"], auxiliary["_beliefs"],
                            atol=1e-12, rtol=0.0)),
                        "within_30s": canary_wall <= CANARY_CAP_S,
                    }
                    canary.update({
                        "passed": bool(all(checks.values())), "checks": checks,
                        "max_abs_belief_diff": max_abs,
                        "total_wall_s": canary_wall,
                    })
                    summary["canary"] = canary
                    control_call["canary_reference_call_index"] = int(control_call["call_index"])
                    control_call["canary_aux_call_index"] = int(auxiliary["call_index"])
                    auxiliary["canary_reference_call_index"] = int(control_call["call_index"])
                    auxiliary["canary_aux_call_index"] = int(auxiliary["call_index"])
                    if not canary["passed"]:
                        if canary_wall > CANARY_CAP_S:
                            stop("INCOMPLETE", "canary_wall_cap", "resource")
                        else:
                            stop("STOP", "natural_mode_canary_failed", "integrity")
                        break
                    control_call = control_call
                    candidate_call = call_decoder(pair, "residual_candidate", "residual")
                    if candidate_call is None or run_status != "RUNNING":
                        break
                else:
                    order = (("control_reference", "reference"),
                             ("residual_candidate", "residual"))
                    if frame_idx % 2 == 1:
                        order = tuple(reversed(order))
                    for role, key in order:
                        returned = call_decoder(pair, role, key)
                        if returned is None or run_status != "RUNNING":
                            break
                        if role == "control_reference":
                            control_call = returned
                        else:
                            candidate_call = returned
                    if run_status != "RUNNING":
                        break

                if control_call is None or candidate_call is None:
                    break
                frame_row["control_call_index"] = int(control_call["call_index"])
                frame_row["candidate_call_index"] = int(candidate_call["call_index"])
                finish_frame(frame_row, control_call, candidate_call)
            if run_status != "RUNNING":
                break
        if run_status != "RUNNING":
            break

    if run_status == "RUNNING":
        summary["run_status"] = "COMPLETE"
        run_status = "COMPLETE"
        if summary["completed_pairs"] != HOLDOUT_PAIRS:
            run_status = "INCOMPLETE"
            summary["run_status"] = "INCOMPLETE"
            summary["resource_violations"] += 1
            summary["stop_reasons"].append("completed_pair_count_mismatch")

    complete = (run_status == "COMPLETE"
                and summary["completed_pairs"] == HOLDOUT_PAIRS
                and canary.get("passed") is True)
    if complete:
        complete_frames = [row for row in frames if row.get("completed")]
        control_exact = sum(bool(row["control_exact"]) for row in complete_frames)
        candidate_exact = sum(bool(row["candidate_exact"]) for row in complete_frames)
        both = control_only = candidate_only = neither = 0
        control_wrong = candidate_wrong = 0
        graph_deltas = []
        for row in complete_frames:
            c = bool(row["control_exact"])
            t = bool(row["candidate_exact"])
            both += int(c and t)
            control_only += int(c and not t)
            candidate_only += int(t and not c)
            neither += int(not c and not t)
            control_wrong += int(bool(row["control_syndrome_valid_wrong"]))
            candidate_wrong += int(bool(row["candidate_syndrome_valid_wrong"]))
        for graph_id in rescue.GRAPH_IDS:
            graph_rows = [row for row in complete_frames if row["graph_id"] == graph_id]
            graph_deltas.append({
                "graph_id": int(graph_id),
                "control_exact": sum(bool(row["control_exact"]) for row in graph_rows),
                "candidate_exact": sum(bool(row["candidate_exact"]) for row in graph_rows),
                "delta": (sum(bool(row["candidate_exact"]) for row in graph_rows)
                          - sum(bool(row["control_exact"]) for row in graph_rows)),
            })
        summary.update({
            "control_exact": control_exact, "candidate_exact": candidate_exact,
            "delta": candidate_exact - control_exact,
            "paired_both": both, "paired_control_only": control_only,
            "paired_candidate_only": candidate_only, "paired_neither": neither,
            "control_syndrome_valid_wrong": control_wrong,
            "candidate_syndrome_valid_wrong": candidate_wrong,
            "positive_graph_deltas": sum(item["delta"] > 0 for item in graph_deltas),
            "per_graph": graph_deltas,
        })
        summary["classification"] = _classify(summary)
    else:
        for key in ("control_exact", "candidate_exact", "delta", "paired_both",
                    "paired_control_only", "paired_candidate_only", "paired_neither",
                    "control_syndrome_valid_wrong", "candidate_syndrome_valid_wrong",
                    "positive_graph_deltas", "per_graph"):
            summary[key] = None
        summary["classification"] = None

    summary["run_status"] = run_status
    summary["physical_calls"] = summary["attempted_physical_calls"]
    summary["batch_wall_s"] = max(float(now()) - started, 0.0)
    summary["artifacts"] = {
        "manifest": str(root / "manifest.json"),
        "summary": str(root / "summary.json"),
        "calls": str(root / "calls.csv"),
        "frames": str(root / "frames.csv"),
        "diagnostics": str(root / "diagnostics.npz"),
        "exploration_log": str(log_path),
    }

    source_manifest = {
        key: value for key, value in (source_identity or {}).items()
    }
    selected_manifest = [
        {key: value for key, value in row.items() if key != "H"}
        for row in selected_sources
    ]
    manifest = {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE, "run_status": run_status,
        "command": command, "out_root": str(root),
        "source_identity": source_manifest, "selected_sources": selected_manifest,
        "planned_pairs": planned_map, "prior_exclusion_plan_count": summary.get(
            "prior_exclusion_plan_count"),
        "prior_exclusion_rows": summary.get("prior_exclusion_rows"),
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "candidate_loop": "decode_row_layered_residual_sweep",
            "field": "GF(32), polynomial 37", "max_iter": MAX_ITER,
            "damping_alpha": DAMPING_ALPHA, "warm_beliefs": None,
            "prior_floor": 1e-15, "schedule_control": "natural",
            "schedule_candidate": "residual-ranked whole sweep",
            "stop": "initial prior-only syndrome or completed-sweep syndrome; max 90",
        },
        "fixed_inputs": {
            "n": N, "m": M, "edge_count": 256,
            "graph_ids": list(rescue.GRAPH_IDS), "p0": rescue.P0,
            "error_symbols": {str(symbol): count for symbol, count in rescue.SHAPE_COUNTS},
            "syndrome_bits_per_sample": SYNDROME_BITS,
            "no_prior_or_graph_search": True,
        },
        "cost_caps": summary["caps"],
        "canary": canary,
        "authorization_consumed": bool(summary["attempted_physical_calls"] > 0),
        "resource_events": resource_events,
    }

    arrays = _result_fields(
        calls, frames, selected_sources, original_prior, raw_vectors,
        raw_vector_call_indices, final_beliefs, belief_call_indices,
        row_order_call_indices, row_order_sweeps, row_order_offsets,
        row_order_values, score_call_indices, score_values, canary)
    arrays["own_syndrome_call_index"] = np.asarray(
        own_syndrome_call_indices, dtype=np.int64)
    arrays["call_own_syndrome"] = (np.stack(own_syndromes).astype(np.uint8)
                                   if own_syndromes
                                   else np.empty((0, M), dtype=np.uint8))
    diagnostics_path = root / "diagnostics.npz"
    np.savez_compressed(diagnostics_path, **arrays)
    _write_csv(root / "calls.csv", calls, CALL_FIELDS)
    public_frames = [{key: value for key, value in row.items()
                      if key not in ("truth", "syndrome", "H")}
                     for row in frames]
    _write_csv(root / "frames.csv", public_frames, FRAME_FIELDS)
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)
    checkpoint_sizes = {path.name: int(path.stat().st_size) for path in root.iterdir()
                        if path.is_file() and path.name != "EXPLORATION_LOG.md"}
    checkpoint_bytes = sum(checkpoint_sizes.values()) + int(log_path.stat().st_size)
    checkpoint_wall_s = max(float(now()) - started, 0.0)
    checkpoint_rss_bytes = rss_read()
    if checkpoint_rss_bytes is not None:
        checkpoint_rss_bytes = int(checkpoint_rss_bytes)
        peak_rss = summary["peak_rss_bytes"]
        summary["peak_rss_bytes"] = (
            checkpoint_rss_bytes if peak_rss is None
            else max(int(peak_rss), checkpoint_rss_bytes))
    summary["batch_wall_s"] = checkpoint_wall_s
    summary["output_bytes"] = checkpoint_bytes
    summary["artifact_checkpoint_wall_s"] = checkpoint_wall_s
    summary["artifact_checkpoint_rss_bytes"] = checkpoint_rss_bytes
    summary["artifact_checkpoint_output_bytes"] = checkpoint_bytes
    manifest["artifact_checkpoint"] = {
        "wall_s": checkpoint_wall_s,
        "rss_bytes": checkpoint_rss_bytes,
        "output_bytes": checkpoint_bytes,
    }

    post_persist_reasons = []
    if checkpoint_wall_s > WALL_CAP_S:
        post_persist_reasons.append("total_wall_cap")
    if (checkpoint_rss_bytes is not None
            and checkpoint_rss_bytes > RSS_CAP_BYTES):
        post_persist_reasons.append("rss_cap")
    if checkpoint_bytes > ARTIFACT_CAP_BYTES:
        post_persist_reasons.append("artifact_bytes_cap")
    if post_persist_reasons:
        resource_events.extend(
            f"after_first_pass:{reason}" for reason in post_persist_reasons)
        run_status = "INCOMPLETE"
        summary["run_status"] = run_status
        summary["resource_violations"] += 1
        for reason in post_persist_reasons:
            if reason not in summary["stop_reasons"]:
                summary["stop_reasons"].append(reason)
        summary["classification"] = None
        for key in ("control_exact", "candidate_exact", "delta", "paired_both",
                    "paired_control_only", "paired_candidate_only", "paired_neither",
                    "control_syndrome_valid_wrong", "candidate_syndrome_valid_wrong",
                    "positive_graph_deltas", "per_graph"):
            summary[key] = None
        _append_log(log_path,
                    "INCOMPLETE after first-pass artifacts: "
                    + ",".join(post_persist_reasons))
    else:
        _append_log(log_path,
                    f"Attempt ended: {run_status}; classification={summary['classification']}")

    summary["run_status"] = run_status
    summary["resource_events"] = resource_events
    manifest["run_status"] = run_status
    manifest["resource_events"] = resource_events
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)

    final_output_bytes_observed = sum(
        int(path.stat().st_size) for path in root.iterdir() if path.is_file())
    summary["final_observed_output_bytes"] = final_output_bytes_observed
    summary["final_observed_output_bytes_delta"] = (
        final_output_bytes_observed - checkpoint_bytes)
    manifest["final_observed_output_bytes"] = final_output_bytes_observed
    manifest["final_observed_output_bytes_delta"] = (
        final_output_bytes_observed - checkpoint_bytes)
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)
    return {
        **summary, "summary": summary, "calls": [
            {key: value for key, value in row.items() if not key.startswith("_")}
            for row in calls],
        "frames": public_frames, "source_identity": source_identity,
        "source_maps": selected_manifest, "artifacts": summary["artifacts"],
    }


def _bind_production() -> dict[str, Any]:
    """Bind the source, sampler and decoders only for explicit --execute."""
    from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as sampler_module

    def reference(h, prior, syndrome, *, max_iter, damping_alpha,
                  warm_beliefs, field):
        if warm_beliefs is not None or field is not None:
            raise ValueError("reference must use a cold v35 call with field=None")
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter,
            damping_alpha=damping_alpha, warm_beliefs=None, field=None)

    def helper(schedule: str):
        def decode(h, prior, syndrome, *, max_iter, damping_alpha,
                   warm_beliefs, field):
            if warm_beliefs is not None or field is not None:
                raise ValueError("research loop must be cold with field=None")
            return residual_sweep.decode_row_layered_residual_sweep(
                h, prior, syndrome, max_iter=max_iter, schedule=schedule,
                damping_alpha=damping_alpha, field=None)
        return decode

    return {
        "source_reader": rescue._default_source_reader(),
        "sampler": sampler_module.sample_error,
        "decode_fns": {
            "reference": reference, "natural": helper("natural"),
            "residual": helper("residual"),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF(32) residual-ranked row-layered EXPLORE probe")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true", help="source-free frozen checks")
    mode.add_argument("--dry-run", action="store_true", help="no-read/no-write root check")
    mode.add_argument("--execute", action="store_true", help="one authorized frozen attempt")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.dry_run:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(**_bind_production(), out_root=args.out_root,
                               command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0 if result.get("status", result.get("run_status")) in (
        "PASS", "DRY_RUN", "COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
