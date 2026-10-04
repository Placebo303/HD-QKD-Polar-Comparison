"""Bounded GF(32) stale-edge-state prior-swap EXPLORE probe."""
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
from comparison_bench.formal_ir import nbldpc_gf32_edge_state as edge_state
from comparison_bench.formal_ir import v35_algorithm_development as v35


BATCH_UUID = "3aaa1d95-d9a7-4007-b6e8-7b72254feaf2"
CONTRACT = "NBLDPC-GF32-EDGE-STATE-R2-20261004/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-softprior-edge-state-r2-v1"
PREDECESSOR_NAMESPACE = "gf32-softprior-edge-state-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_edge_state_r2_3aaa1d95"
TOP3_NAMESPACE = mechanism_pair._profile("top3runtime")["seed_namespace"]
N, M, Q = rescue.N, rescue.M, rescue.Q
MAX_ITER, DAMPING_ALPHA = 90, 1.0
GUESSES = rescue.GUESSES
HOLDOUT_PAIRS = rescue.HOLDOUT_PAIRS
MAX_PHYSICAL_CALLS = HOLDOUT_PAIRS * (2 + 2 * len(GUESSES))
MAX_PHYSICAL_ITERATIONS = MAX_PHYSICAL_CALLS * MAX_ITER
WALL_CAP_S = 1200.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 20 * 1024 * 1024
SYNDROME_BITS = 260
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_edge_state_probe --execute "
    "--out-root workspace/gf32_edge_state_r2_3aaa1d95"
)


def _repo_root() -> Path:
    return rescue._repo_root()


def _additional_excluded_plans() -> tuple[tuple[str, Sequence[Sequence[int]]], ...]:
    plans = list(mechanism_pair._additional_excluded_plans("top3runtime"))
    plans.append((f"top3runtime/{TOP3_NAMESPACE}", rescue.build_seed_plan(TOP3_NAMESPACE)))
    plans.append((f"predecessor/{PREDECESSOR_NAMESPACE}",
                  rescue.build_seed_plan(PREDECESSOR_NAMESPACE)))
    return tuple(plans)


def verify_t0() -> dict[str, Any]:
    additional = _additional_excluded_plans()
    base = rescue.verify_t0(
        batch_uuid=BATCH_UUID, contract=CONTRACT,
        seed_namespace=SEED_NAMESPACE,
        additional_excluded_plans=additional)
    if (base["prior_exclusion_plan_count"] != 21
            or base["prior_exclusion_rows"] != 4368):
        raise AssertionError("frozen R2 seed exclusion union must remain 21 plans/4368 seeds")
    return {**base, "additional_seed_plans": 8,
            "source_reads": 0, "sampler_calls": 0,
            "decoder_calls": 0, "writes": 0}


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = rescue.validate_out_root(
        out_root, repo_root=repo_root, official_root=OUT_ROOT_RELATIVE)
    return {"status": "DRY_RUN", "batch_uuid": BATCH_UUID,
            "contract": CONTRACT, "out_root": str(root),
            "source_reads": 0, "sampler_calls": 0,
            "decoder_calls": 0, "writes": 0, "t0": verify_t0()}


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


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               default=_json_default) + "\n", encoding="utf-8")


def _append_log(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(line.rstrip("\n") + "\n")


def _exact(result: Mapping[str, Any], truth: np.ndarray) -> bool:
    return bool(result["syndrome_valid"] and np.array_equal(result["x_hat"], truth))


def _compare_reference(reference: Any, auxiliary: Any,
                       h_matrix: np.ndarray, syndrome: np.ndarray) -> dict[str, bool]:
    ref_x = np.asarray(reference.x_hat)
    aux_x = np.asarray(auxiliary.x_hat)
    ref_beliefs = np.asarray(reference.final_beliefs, dtype=np.float64)
    aux_beliefs = np.asarray(auxiliary.final_beliefs, dtype=np.float64)
    ref_own = rescue.layout.gf32_syndrome(h_matrix, ref_x)
    aux_own = rescue.layout.gf32_syndrome(h_matrix, aux_x)
    return {
        "x_hat": bool(np.array_equal(ref_x, aux_x)),
        "status": str(reference.status) == str(auxiliary.status),
        "iterations": int(reference.iterations) == int(auxiliary.iterations),
        "own_syndrome": bool(np.array_equal(ref_own, aux_own)),
        "final_beliefs": bool(
            ref_beliefs.shape == aux_beliefs.shape
            and np.allclose(ref_beliefs, aux_beliefs, rtol=0.0, atol=1e-12)),
        "syndrome_ok_reported": bool(
            getattr(reference, "syndrome_ok", None)
            == getattr(auxiliary, "syndrome_ok", None)),
    }


def _empty_summary() -> dict[str, Any]:
    return {
        "status": "RUNNING", "classification": None,
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE,
        "planned_pairs": HOLDOUT_PAIRS, "sampled_pairs": 0,
        "completed_pairs": 0, "branched_baseline_failures": 0,
        "baseline_calls": 0, "zero_state_calls": 0,
        "zero_state_equivalence_passes": 0,
        "auxiliary_decoder_iterations": 0, "no_active_pairs": 0,
        "control_branch_calls": 0, "candidate_branch_calls": 0,
        "branch_calls": 0, "attempted_physical_calls": 0,
        "physical_decoder_iterations": 0,
        "logical_control_calls": 0, "logical_candidate_calls": 0,
        "logical_control_iterations": 0, "logical_candidate_iterations": 0,
        "baseline_exact": None, "control_exact": None, "candidate_exact": None,
        "delta_exact": None, "syndrome_valid_wrong_control": None,
        "syndrome_valid_wrong_candidate": None,
        "raw_branch_valid_wrong_control": None,
        "raw_branch_valid_wrong_candidate": None,
        "syndrome_failed_control": None, "syndrome_failed_candidate": None,
        "paired": None, "per_graph": None,
        "syndrome_bits_per_method_frame": SYNDROME_BITS,
        "physical_disclosure_bits_shared": 0,
        "logical_control_disclosure_bits": 0,
        "logical_candidate_disclosure_bits": 0,
        "internal_branch_disclosure_bits": 0, "tag_bits": 0,
        "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "max_physical_calls": MAX_PHYSICAL_CALLS,
        "max_physical_iterations": MAX_PHYSICAL_ITERATIONS,
        "wall_cap_s": WALL_CAP_S, "rss_cap_bytes": RSS_CAP_BYTES,
        "artifact_cap_bytes": ARTIFACT_CAP_BYTES,
        "peak_rss_bytes": None, "resource_checkpoint_wall_s": None,
        "output_bytes_at_checkpoint": None, "diagnostics_bytes": None,
        "stop_reasons": [], "integrity_violations": 0,
        "resource_violations": 0, "data_violations": 0,
        "authorization_violations": 0,
    }


def _null_comparisons(summary: dict[str, Any]) -> None:
    for key in (
        "baseline_exact", "control_exact", "candidate_exact", "delta_exact",
        "syndrome_valid_wrong_control", "syndrome_valid_wrong_candidate",
        "raw_branch_valid_wrong_control", "raw_branch_valid_wrong_candidate",
        "syndrome_failed_control", "syndrome_failed_candidate", "paired", "per_graph",
    ):
        summary[key] = None


def _full_comparisons(summary: dict[str, Any], pairs: Sequence[Mapping[str, Any]],
                      calls: Sequence[Mapping[str, Any]]) -> None:
    summary["baseline_exact"] = sum(bool(row["baseline_exact"]) for row in pairs)
    summary["control_exact"] = sum(bool(row["control_exact"]) for row in pairs)
    summary["candidate_exact"] = sum(bool(row["candidate_exact"]) for row in pairs)
    summary["delta_exact"] = int(summary["candidate_exact"] - summary["control_exact"])
    summary["syndrome_valid_wrong_control"] = sum(
        bool(row["control_syndrome_valid_wrong"]) for row in pairs)
    summary["syndrome_valid_wrong_candidate"] = sum(
        bool(row["candidate_syndrome_valid_wrong"]) for row in pairs)
    summary["raw_branch_valid_wrong_control"] = sum(
        bool(row.get("syndrome_valid_wrong")) for row in calls
        if row["role"] == "onehot_control")
    summary["raw_branch_valid_wrong_candidate"] = sum(
        bool(row.get("syndrome_valid_wrong")) for row in calls
        if row["role"] == "edge_state_candidate")
    summary["syndrome_failed_control"] = sum(
        not bool(row["control_syndrome_valid"]) for row in pairs)
    summary["syndrome_failed_candidate"] = sum(
        not bool(row["candidate_syndrome_valid"]) for row in pairs)
    both = candidate_only = control_only = neither = 0
    per_graph: dict[str, dict[str, int]] = {}
    for row in pairs:
        control, candidate = bool(row["control_exact"]), bool(row["candidate_exact"])
        if control and candidate:
            both += 1
        elif candidate:
            candidate_only += 1
        elif control:
            control_only += 1
        else:
            neither += 1
        graph = str(row["graph_id"])
        counts = per_graph.setdefault(graph, {
            "baseline_exact": 0, "control_exact": 0, "candidate_exact": 0,
            "control_syndrome_valid_wrong": 0,
            "candidate_syndrome_valid_wrong": 0,
        })
        counts["baseline_exact"] += int(bool(row["baseline_exact"]))
        counts["control_exact"] += int(control)
        counts["candidate_exact"] += int(candidate)
        counts["control_syndrome_valid_wrong"] += int(bool(row["control_syndrome_valid_wrong"]))
        counts["candidate_syndrome_valid_wrong"] += int(bool(row["candidate_syndrome_valid_wrong"]))
    for counts in per_graph.values():
        counts["delta_exact"] = counts["candidate_exact"] - counts["control_exact"]
    summary["paired"] = {
        "both_exact": both, "candidate_only": candidate_only,
        "control_only": control_only, "neither": neither,
    }
    summary["per_graph"] = per_graph


def _classification(summary: Mapping[str, Any]) -> str:
    baseline = int(summary["baseline_exact"])
    control = int(summary["control_exact"])
    candidate = int(summary["candidate_exact"])
    graph_deltas = [int(row["delta_exact"]) for row in summary["per_graph"].values()]
    if not 39 <= baseline <= 153 or control - baseline <= 0:
        return "INCREMENT_SCREEN_UNINFORMATIVE"
    if (candidate - control >= 6
            and sum(delta > 0 for delta in graph_deltas) >= 4
            and int(summary["syndrome_valid_wrong_candidate"])
            <= int(summary["syndrome_valid_wrong_control"])
            and int(summary["raw_branch_valid_wrong_candidate"])
            <= int(summary["raw_branch_valid_wrong_control"])):
        return "INCREMENT_SCREEN_MET"
    return "INCREMENT_SCREEN_NOT_MET"


def _csv_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return json.dumps(value.tolist(), separators=(",", ":"))
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, separators=(",", ":"), default=_json_default)
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return _json_default(value)
    return value


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def _diagnostics_arrays(
        selected_sources: Sequence[Mapping[str, Any]], pairs: Sequence[Mapping[str, Any]],
        original_prior: np.ndarray,
        raw_call_ids: Sequence[int], raw_vectors: Sequence[np.ndarray],
        baseline_belief_call_ids: Sequence[int], baseline_beliefs: Sequence[np.ndarray],
        failure_call_ids: Sequence[int], failure_c2v_rows: Sequence[np.ndarray],
        failure_c2v_columns: Sequence[np.ndarray], failure_c2v_messages: Sequence[np.ndarray],
        failure_c2v_captured: Sequence[bool]
        ) -> dict[str, np.ndarray]:
    truth_rows = [row["truth"] for row in pairs if row.get("truth") is not None]
    syndrome_rows = [row["syndrome"] for row in pairs if row.get("syndrome") is not None]
    sampled = [row for row in pairs if row.get("truth") is not None]
    arrays = {
        "source_H": (np.stack([row["H"] for row in selected_sources]).astype(np.uint8)
                     if selected_sources else np.empty((0, M, N), dtype=np.uint8)),
        "source_graph_id": np.asarray([row["graph_id"] for row in selected_sources], dtype=np.int64),
        "source_deep_row_index": np.asarray(
            [row["deep_row_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_row_index": np.asarray(
            [row["constructor_row_index"] for row in selected_sources], dtype=np.int64),
        "source_profile_index": np.asarray(
            [row["profile_index"] for row in selected_sources], dtype=np.int64),
        "source_graph_index": np.asarray(
            [row["graph_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_uuid": np.asarray(
            [row["source_lineage"]["source_uuid"] for row in selected_sources], dtype="<U36"),
        "source_constructor_path": np.asarray(
            [row["source_lineage"]["source_path"] for row in selected_sources], dtype="<U160"),
        "source_constructor_matrix_index": np.asarray(
            [row["source_lineage"]["source_matrix_index"] for row in selected_sources], dtype=np.int64),
        "source_constructor_attempt_j": np.asarray(
            [row["source_lineage"]["source_attempt_j"] for row in selected_sources], dtype=np.int64),
        "source_constructor_seed": np.asarray(
            [row["source_lineage"]["source_construction_seed"] for row in selected_sources], dtype=np.int64),
        "source_constructor_graph_id": np.asarray(
            [row["source_lineage"]["source_graph_id"] for row in selected_sources], dtype=np.int64),
        "original_prior": np.asarray(original_prior, dtype=np.float64),
        "pair_index": np.asarray([row["pair_index"] for row in sampled], dtype=np.int64),
        "pair_graph_id": np.asarray([row["graph_id"] for row in sampled], dtype=np.int64),
        "pair_stream": np.asarray([row["stream"] for row in sampled], dtype=np.int64),
        "pair_frame": np.asarray([row["frame"] for row in sampled], dtype=np.int64),
        "pair_seed": np.asarray([row["seed"] for row in sampled], dtype=np.int64),
        "pair_truth": (np.stack(truth_rows).astype(np.uint8) if truth_rows
                       else np.empty((0, N), dtype=np.uint8)),
        "pair_syndrome": (np.stack(syndrome_rows).astype(np.uint8) if syndrome_rows
                          else np.empty((0, M), dtype=np.uint8)),
        "raw_vector_call_index": np.asarray(raw_call_ids, dtype=np.int64),
        "raw_x_hat": (np.stack(raw_vectors).astype(np.uint8) if raw_vectors
                      else np.empty((0, N), dtype=np.uint8)),
        "baseline_belief_call_index": np.asarray(baseline_belief_call_ids, dtype=np.int64),
        "baseline_beliefs": (np.stack(baseline_beliefs).astype(np.float64) if baseline_beliefs
                             else np.empty((0, N, Q), dtype=np.float64)),
        "baseline_failure_call_index": np.asarray(failure_call_ids, dtype=np.int64),
        "baseline_failure_c2v_row": (np.concatenate(failure_c2v_rows).astype(np.int64)
                                     if failure_c2v_rows else np.empty(0, dtype=np.int64)),
        "baseline_failure_c2v_column": (np.concatenate(failure_c2v_columns).astype(np.int64)
                                        if failure_c2v_columns else np.empty(0, dtype=np.int64)),
        "baseline_failure_c2v_message": (np.concatenate(failure_c2v_messages).astype(np.float64)
                                         if failure_c2v_messages else
                                         np.empty((0, Q), dtype=np.float64)),
        "baseline_failure_c2v_captured": np.asarray(
            failure_c2v_captured, dtype=np.bool_),
    }
    offsets = [0]
    for rows in failure_c2v_rows:
        offsets.append(offsets[-1] + len(rows))
    arrays["baseline_failure_c2v_offsets"] = np.asarray(offsets, dtype=np.int64)
    return arrays


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        sampler: Callable[..., Any], decode_fns: Mapping[str, Callable[..., Any]],
        out_root: str | Path, repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        additional_excluded_plans: Sequence[tuple[str, Sequence[Sequence[int]]]] | None = None,
        official_root: str | Path = OUT_ROOT_RELATIVE) -> dict[str, Any]:
    root = rescue.validate_out_root(out_root, repo_root=repo_root,
                                    official_root=official_root)
    if not callable(source_reader) or not callable(sampler):
        raise ValueError("explicit source_reader and sampler callbacks are required")
    required_decoders = {"reference", "control", "edge_state"}
    if (not isinstance(decode_fns, Mapping) or set(decode_fns) != required_decoders
            or any(not callable(decode_fns[name]) for name in required_decoders)):
        raise ValueError("decode_fns must explicitly provide reference, control and edge_state")
    additional = (tuple(_additional_excluded_plans()) if additional_excluded_plans is None
                  else tuple(additional_excluded_plans))
    plan, exclusion_records = rescue.validate_seed_plan(
        seed_namespace=SEED_NAMESPACE, additional_excluded_plans=additional)
    rss_fn = rescue._rss_bytes if rss_fn is None else rss_fn
    start = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    _append_log(log_path, f"EXPLORE batch {BATCH_UUID} started; track=EXPLORE.")

    summary = _empty_summary()
    calls: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    selected_sources: list[dict[str, Any]] = []
    source_identity: dict[str, str] | None = None
    raw_call_ids: list[int] = []
    raw_vectors: list[np.ndarray] = []
    baseline_belief_call_ids: list[int] = []
    baseline_beliefs: list[np.ndarray] = []
    failure_call_ids: list[int] = []
    failure_c2v_rows: list[np.ndarray] = []
    failure_c2v_columns: list[np.ndarray] = []
    failure_c2v_messages: list[np.ndarray] = []
    failure_c2v_captured: list[bool] = []
    original_pmf = rescue.pmf()
    original_prior = np.tile(original_pmf, (N, 1))
    prior_eff = rescue.effective_prior(original_prior)
    resource_events: list[str] = []
    run_status = "RUNNING"
    stop_reasons: list[str] = []
    peak_rss: int | None = None

    def stop(status: str, reason: str, category: str) -> None:
        nonlocal run_status
        run_status = status
        if reason not in stop_reasons:
            stop_reasons.append(reason)
        key = {"resource": "resource_violations", "integrity": "integrity_violations",
               "data": "data_violations", "authorization": "authorization_violations"}[category]
        summary[key] += 1

    def check_resources(phase: str, call_wall: float | None = None) -> list[str]:
        nonlocal peak_rss
        elapsed = max(float(now()) - start, 0.0)
        current_rss = rss_fn()
        if current_rss is not None:
            current_rss = int(current_rss)
            peak_rss = current_rss if peak_rss is None else max(peak_rss, current_rss)
        reasons = []
        if elapsed > WALL_CAP_S:
            reasons.append("total_wall_cap")
        if current_rss is not None and current_rss > RSS_CAP_BYTES:
            reasons.append("peak_rss_cap")
        if summary["physical_decoder_iterations"] > MAX_PHYSICAL_ITERATIONS:
            reasons.append("physical_iteration_cap")
        if call_wall is not None and call_wall < 0.0:
            reasons.append("invalid_call_wall")
        if reasons:
            resource_events.extend(f"{phase}:{reason}" for reason in reasons)
        return reasons

    def make_call(pair: dict[str, Any], role: str, prior: np.ndarray, *,
                  branch_index: int = -1, guess_symbol: int = -1,
                  selected_variable: int = -1, state: edge_state.EdgeState | None = None,
                  state_source_call_index: int = -1,
                  state_source_iterations: int = 0) -> dict[str, Any] | None:
        nonlocal peak_rss
        if run_status != "RUNNING":
            return None
        before = check_resources("before_decoder_call")
        if before:
            stop("INCOMPLETE", ";".join(before), "resource")
            return None
        if len(calls) >= MAX_PHYSICAL_CALLS:
            stop("INCOMPLETE", "physical_call_cap_before_next_call", "resource")
            return None

        index = len(calls)
        row = {
            "call_index": index, "pair_index": int(pair["pair_index"]),
            "graph_id": int(pair["graph_id"]), "graph_seed": int(pair["graph_seed"]),
            "stream": int(pair["stream"]), "frame": int(pair["frame"]),
            "seed": int(pair["seed"]), "role": role,
            "branch_index": int(branch_index), "guess_symbol": int(guess_symbol),
            "selected_variable": int(selected_variable),
            "state_initialization": ("EDGE_STATE_SEEDED_PRIOR_SWAP" if state is not None
                                     else "ZERO_STATE"),
            "state_source_call_index": int(state_source_call_index),
            "state_source_iterations": int(state_source_iterations),
            "status": "RUNNING", "decoder_status": None,
            "iterations": None, "iterations_this_call": None,
            "decoder_runtime_s": None, "wall_s": None, "rss_bytes": None,
            "syndrome_valid": None, "syndrome_ok_reported": None,
            "exact": None, "syndrome_valid_wrong": None,
            "raw_vector_index": None, "belief_provenance": None,
            "extrinsic_provenance": None, "score_original_prior": None,
            "state_capture_status": "MISSING",
            "failure_reason": "",
        }
        calls.append(row)
        summary["attempted_physical_calls"] += 1
        if role == "baseline_reference":
            summary["baseline_calls"] += 1
            summary["logical_control_calls"] += 1
            summary["logical_candidate_calls"] += 1
        elif role == "baseline_zero_state":
            summary["zero_state_calls"] += 1
        elif role == "onehot_control":
            summary["control_branch_calls"] += 1
            summary["branch_calls"] += 1
            summary["logical_control_calls"] += 1
        elif role == "edge_state_candidate":
            summary["candidate_branch_calls"] += 1
            summary["branch_calls"] += 1
            summary["logical_candidate_calls"] += 1

        call_start = float(now())
        try:
            if role == "baseline_reference":
                returned = decode_fns["reference"](
                    pair["H"], prior.copy(), pair["syndrome"], max_iter=MAX_ITER,
                    damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
                if not isinstance(returned, tuple) or len(returned) != 2:
                    raise ValueError("reference callback must return (DecoderResult, EdgeState)")
                raw, captured_state = returned
            elif role in ("baseline_zero_state", "edge_state_candidate"):
                raw = decode_fns["edge_state"](
                    pair["H"], prior.copy(), pair["syndrome"], max_iter=MAX_ITER,
                    damping_alpha=DAMPING_ALPHA, state=state, field=None)
                captured_state = getattr(raw, "state", None)
            else:
                raw = decode_fns["control"](
                    pair["H"], prior.copy(), pair["syndrome"], max_iter=MAX_ITER,
                    damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
                captured_state = None
        except Exception as exc:
            wall = max(float(now()) - call_start, 0.0)
            row.update({"status": "FAILED", "wall_s": wall,
                        "failure_reason": f"decoder_error:{type(exc).__name__}:{exc}"})
            stop("STOP", row["failure_reason"], "integrity")
            return None

        wall = max(float(now()) - call_start, 0.0)
        try:
            vector = np.asarray(raw.x_hat)
            if (vector.shape != (N,) or not np.issubdtype(vector.dtype, np.integer)
                    or np.any(vector < 0) or np.any(vector >= Q)):
                raise ValueError("decoder x_hat must be an integer GF(32) vector of length 128")
            vector = vector.astype(np.uint8, copy=True)
            reported_iterations = int(raw.iterations)
            this_iterations = (int(getattr(raw, "iterations_this_call", reported_iterations))
                               if role in ("baseline_zero_state", "edge_state_candidate")
                               else reported_iterations)
            if not (0 <= this_iterations <= MAX_ITER and reported_iterations >= this_iterations):
                raise ValueError("decoder iterations are outside the frozen range")
            own_valid = bool(np.array_equal(
                rescue.layout.gf32_syndrome(pair["H"], vector), pair["syndrome"]))
            reported_valid = getattr(raw, "syndrome_ok", None)
            if reported_valid is not None and bool(reported_valid) != own_valid:
                raise ValueError("decoder syndrome_ok disagrees with independent own-syndrome")
            beliefs = np.asarray(raw.final_beliefs, dtype=np.float64)
            if beliefs.shape != (N, Q) or not np.all(np.isfinite(beliefs)):
                raise ValueError("decoder final_beliefs must be finite shape (128,32)")
        except Exception as exc:
            row.update({"status": "FAILED", "wall_s": wall,
                        "failure_reason": f"decoder_result_invalid:{type(exc).__name__}:{exc}"})
            stop("STOP", row["failure_reason"], "integrity")
            return None

        vector_index = len(raw_vectors)
        raw_vectors.append(vector)
        raw_call_ids.append(index)
        row.update({
            "status": "COMPLETE", "decoder_status": str(raw.status),
            "iterations": reported_iterations, "iterations_this_call": this_iterations,
            "decoder_runtime_s": float(getattr(raw, "runtime_s", wall)),
            "wall_s": wall, "syndrome_valid": own_valid,
            "syndrome_ok_reported": None if reported_valid is None else bool(reported_valid),
            "raw_vector_index": vector_index,
            "belief_provenance": getattr(raw, "belief_provenance", None),
            "extrinsic_provenance": getattr(raw, "extrinsic_provenance", None),
            "state_capture_status": "CAPTURED" if isinstance(
                captured_state, edge_state.EdgeState) else "MISSING",
            "x_hat": vector, "_raw_result": raw,
            "_captured_state": captured_state, "_beliefs": beliefs.copy(),
        })
        summary["physical_decoder_iterations"] += this_iterations
        if role in ("baseline_reference", "onehot_control"):
            summary["logical_control_iterations"] += this_iterations
        if role in ("baseline_reference", "edge_state_candidate"):
            summary["logical_candidate_iterations"] += this_iterations
        if role == "baseline_zero_state":
            summary["auxiliary_decoder_iterations"] += this_iterations
        if role in ("baseline_reference", "baseline_zero_state"):
            baseline_belief_call_ids.append(index)
            baseline_beliefs.append(beliefs.copy())
        rss_value = rss_fn()
        if rss_value is not None:
            rss_value = int(rss_value)
            peak_rss = rss_value if peak_rss is None else max(peak_rss, rss_value)
        row["rss_bytes"] = rss_value
        over = check_resources("after_decoder_call", wall)
        if over:
            stop("INCOMPLETE", ";".join(over), "resource")
        return row

    try:
        source = source_reader()
        source_identity, selected_sources = rescue.select_sources(source)
    except Exception as exc:
        stop("STOP", f"source_preflight:{type(exc).__name__}:{exc}", "data")
        selected_sources = []

    if run_status == "RUNNING":
        for pair_index, (graph_id, stream, frame, seed) in enumerate(plan):
            if run_status != "RUNNING":
                break
            source_row = selected_sources[(pair_index // (2 * rescue.HOLDOUT_FRAMES_PER_STREAM))]
            try:
                truth = np.asarray(sampler(seed, original_pmf.copy(), width=N))
                if (truth.shape != (N,) or not np.issubdtype(truth.dtype, np.integer)
                        or np.any(truth < 0) or np.any(truth >= Q)):
                    raise ValueError("sampler must return an integer GF(32) vector of length 128")
                truth = truth.astype(np.uint8, copy=True)
                syndrome = np.asarray(
                    rescue.layout.gf32_syndrome(source_row["H"], truth), dtype=np.uint8)
            except Exception as exc:
                stop("STOP", f"sample_or_syndrome:{type(exc).__name__}:{exc}", "data")
                break
            pair = {
                "pair_index": pair_index, "graph_id": int(graph_id),
                "graph_seed": int(graph_id), "stream": int(stream),
                "frame": int(frame), "seed": int(seed), "truth": truth,
                "syndrome": syndrome, "H": source_row["H"].copy(),
                "reference_call_index": None, "zero_state_call_index": None,
                "selector_metadata": None, "selected_variable": None,
                "control_selected_call_index": None,
                "candidate_selected_call_index": None,
                "control_branch_scores": [], "candidate_branch_scores": [],
                "control_fallback": None, "candidate_fallback": None,
                "equivalence": None, "equivalence_pass": None,
                "baseline_syndrome_valid": None, "baseline_exact": None,
                "control_syndrome_valid": None, "candidate_syndrome_valid": None,
                "control_exact": None, "candidate_exact": None,
                "control_syndrome_valid_wrong": None,
                "candidate_syndrome_valid_wrong": None,
                "no_active": False, "completed": False, "failure_reason": "",
            }
            pairs.append(pair)
            summary["sampled_pairs"] += 1

            ref_call = make_call(pair, "baseline_reference", original_prior)
            if ref_call is None:
                break
            pair["reference_call_index"] = ref_call["call_index"]
            raw_ref = ref_call["_raw_result"]
            baseline_valid = bool(ref_call["syndrome_valid"])
            pair["baseline_syndrome_valid"] = baseline_valid
            pair["baseline_exact"] = _exact(ref_call, truth)
            if not baseline_valid:
                baseline_state = ref_call.get("_captured_state")
                failure_call_ids.append(ref_call["call_index"])
                if isinstance(baseline_state, edge_state.EdgeState):
                    edge_rows, edge_columns, edge_messages = [], [], []
                    for row_index, row_messages in enumerate(baseline_state.check_to_var):
                        columns = np.flatnonzero(baseline_state.h_matrix[row_index] != 0)
                        for column, message in zip(columns, row_messages):
                            edge_rows.append(row_index)
                            edge_columns.append(int(column))
                            edge_messages.append(np.asarray(message, dtype=np.float64).copy())
                    failure_c2v_rows.append(np.asarray(edge_rows, dtype=np.int64))
                    failure_c2v_columns.append(np.asarray(edge_columns, dtype=np.int64))
                    failure_c2v_messages.append(
                        np.stack(edge_messages) if edge_messages
                        else np.empty((0, Q), dtype=np.float64))
                    failure_c2v_captured.append(True)
                else:
                    # Retain an explicit missing marker; never synthesize messages.
                    failure_c2v_rows.append(np.empty(0, dtype=np.int64))
                    failure_c2v_columns.append(np.empty(0, dtype=np.int64))
                    failure_c2v_messages.append(np.empty((0, Q), dtype=np.float64))
                    failure_c2v_captured.append(False)
            if ref_call["state_capture_status"] != "CAPTURED":
                pair["failure_reason"] = "reference_edge_state_missing"
                stop("STOP", f"pair{pair_index}:reference_edge_state_missing", "integrity")
                break
            if run_status != "RUNNING":
                break
            zero_call = make_call(pair, "baseline_zero_state", original_prior)
            if zero_call is None:
                break
            pair["zero_state_call_index"] = zero_call["call_index"]
            raw_zero = zero_call["_raw_result"]
            pair["equivalence"] = _compare_reference(raw_ref, raw_zero, pair["H"], syndrome)
            pair["equivalence_pass"] = all(pair["equivalence"].values())
            if not pair["equivalence_pass"]:
                pair["failure_reason"] = "zero_state_reference_mismatch"
                stop("STOP", f"pair{pair_index}:zero_state_reference_mismatch", "integrity")
                break
            summary["zero_state_equivalence_passes"] += 1
            if run_status != "RUNNING":
                break

            control_branches: list[dict[str, Any]] = []
            candidate_branches: list[dict[str, Any]] = []
            control_selected = ref_call
            # The auxiliary zero-state loop only gates exact readiness; the
            # captured v35 reference is the sole shared baseline for selection.
            candidate_selected = ref_call

            if not baseline_valid:
                try:
                    selected, selector_metadata = rescue.select_uncertain_variable(
                        pair["H"], raw_ref.x_hat, raw_ref.final_beliefs, syndrome,
                        belief_provenance=str(getattr(raw_ref, "belief_provenance", "")))
                except ValueError as exc:
                    observed = rescue.layout.gf32_syndrome(pair["H"], raw_ref.x_hat)
                    violated = np.flatnonzero(observed != syndrome)
                    active = (np.flatnonzero(np.any(pair["H"][violated] != 0, axis=0))
                              if len(violated) else np.asarray([], dtype=np.int64))
                    if len(active) == 0 and "no variables adjacent" in str(exc):
                        pair["no_active"] = True
                        pair["control_fallback"] = True
                        pair["candidate_fallback"] = True
                    else:
                        pair["failure_reason"] = f"selector:{type(exc).__name__}:{exc}"
                        stop("STOP", f"pair{pair_index}:{pair['failure_reason']}", "integrity")
                        break
                if run_status != "RUNNING":
                    break
                if not pair["no_active"]:
                    pair["selector_metadata"] = selector_metadata
                    pair["selected_variable"] = int(selected)
                    baseline_state = ref_call["_captured_state"]
                    if not isinstance(baseline_state, edge_state.EdgeState):
                        stop("STOP", f"pair{pair_index}:reference_edge_state_missing", "integrity")
                        break
                    summary["branched_baseline_failures"] += 1
                    for branch_index, guess in enumerate(GUESSES):
                        branch_prior = original_prior.copy()
                        branch_prior[selected] = 0.0
                        branch_prior[selected, guess] = 1.0
                        if pair_index % 2 == 0:
                            role_order = ("onehot_control", "edge_state_candidate")
                        else:
                            role_order = ("edge_state_candidate", "onehot_control")
                        for role in role_order:
                            if role == "onehot_control":
                                branch = make_call(
                                    pair, role, branch_prior,
                                    branch_index=branch_index, guess_symbol=guess,
                                    selected_variable=selected)
                                if branch is None:
                                    break
                                control_branches.append(branch)
                            else:
                                try:
                                    rebased = edge_state.rebase_edge_state(
                                        baseline_state, branch_prior)
                                except Exception as exc:
                                    stop("STOP", f"pair{pair_index}:rebase:{type(exc).__name__}:{exc}",
                                         "integrity")
                                    break
                                branch = make_call(
                                    pair, role, branch_prior,
                                    branch_index=branch_index, guess_symbol=guess,
                                    selected_variable=selected, state=rebased,
                                    state_source_call_index=ref_call["call_index"],
                                    state_source_iterations=int(raw_ref.iterations))
                                if branch is None:
                                    break
                                candidate_branches.append(branch)
                            if run_status != "RUNNING":
                                break
                        if run_status != "RUNNING":
                            break
                    if run_status != "RUNNING":
                        break
                    if len(control_branches) != len(GUESSES) or len(candidate_branches) != len(GUESSES):
                        stop("INCOMPLETE", f"pair{pair_index}:branch_set_incomplete", "resource")
                        break
                    control_idx, control_scores = rescue.select_soft_prior_branch(
                        control_branches, original_prior)
                    candidate_idx, candidate_scores = rescue.select_soft_prior_branch(
                        candidate_branches, original_prior)
                    pair["control_branch_scores"] = control_scores
                    pair["candidate_branch_scores"] = candidate_scores
                    if control_idx is not None:
                        control_selected = next(row for row in control_branches
                                                if row["call_index"] == control_idx)
                    if candidate_idx is not None:
                        candidate_selected = next(row for row in candidate_branches
                                                  if row["call_index"] == candidate_idx)
                    pair["control_fallback"] = control_idx is None
                    pair["candidate_fallback"] = candidate_idx is None
                    pair["control_selected_call_index"] = control_selected["call_index"]
                    pair["candidate_selected_call_index"] = candidate_selected["call_index"]
                    for call in control_branches:
                        score = next(row["score"] for row in control_scores
                                     if row["call_index"] == call["call_index"])
                        call["score_original_prior"] = score
                    for call in candidate_branches:
                        score = next(row["score"] for row in candidate_scores
                                     if row["call_index"] == call["call_index"])
                        call["score_original_prior"] = score
            else:
                pair["control_selected_call_index"] = ref_call["call_index"]
                pair["candidate_selected_call_index"] = ref_call["call_index"]
                pair["control_fallback"] = False
                pair["candidate_fallback"] = False

            if run_status != "RUNNING":
                break
            if pair["no_active"]:
                summary["no_active_pairs"] += 1
            pair["control_syndrome_valid"] = bool(control_selected["syndrome_valid"])
            pair["candidate_syndrome_valid"] = bool(candidate_selected["syndrome_valid"])
            pair["control_exact"] = _exact(control_selected, truth)
            pair["candidate_exact"] = _exact(candidate_selected, truth)
            pair["control_syndrome_valid_wrong"] = bool(
                control_selected["syndrome_valid"] and not pair["control_exact"])
            pair["candidate_syndrome_valid_wrong"] = bool(
                candidate_selected["syndrome_valid"] and not pair["candidate_exact"])
            pair["control_selected_call_index"] = control_selected["call_index"]
            pair["candidate_selected_call_index"] = candidate_selected["call_index"]
            for branch in control_branches + candidate_branches:
                branch["exact"] = _exact(branch, truth)
                branch["syndrome_valid_wrong"] = bool(
                    branch["syndrome_valid"] and not branch["exact"])
            pair["completed"] = True
            summary["completed_pairs"] += 1

    if run_status == "RUNNING":
        run_status = "COMPLETE" if summary["completed_pairs"] == HOLDOUT_PAIRS else "INCOMPLETE"
        if run_status == "INCOMPLETE":
            stop_reasons.append("batch_ended_before_192_completed_pairs")

    summary["status"] = run_status
    summary["peak_rss_bytes"] = peak_rss
    summary["physical_disclosure_bits_shared"] = SYNDROME_BITS * summary["sampled_pairs"]
    summary["logical_control_disclosure_bits"] = SYNDROME_BITS * summary["sampled_pairs"]
    summary["logical_candidate_disclosure_bits"] = SYNDROME_BITS * summary["sampled_pairs"]
    summary["stop_reasons"] = stop_reasons
    if run_status == "COMPLETE" and summary["completed_pairs"] == HOLDOUT_PAIRS:
        _full_comparisons(summary, pairs, calls)
        summary["classification"] = _classification(summary)
    else:
        _null_comparisons(summary)
        summary["classification"] = "STOP" if run_status == "STOP" else "INCOMPLETE"

    pair_fields = (
        "pair_index", "graph_id", "graph_seed", "stream", "frame", "seed",
        "reference_call_index", "zero_state_call_index", "equivalence_pass",
        "equivalence", "baseline_syndrome_valid", "baseline_exact", "no_active",
        "selected_variable", "selector_metadata", "control_selected_call_index",
        "candidate_selected_call_index", "control_fallback", "candidate_fallback",
        "control_branch_scores", "candidate_branch_scores", "control_syndrome_valid",
        "candidate_syndrome_valid", "control_exact", "candidate_exact",
        "control_syndrome_valid_wrong", "candidate_syndrome_valid_wrong",
        "completed", "failure_reason",
    )
    call_fields = (
        "call_index", "pair_index", "graph_id", "graph_seed", "stream", "frame", "seed",
        "role", "branch_index", "guess_symbol", "selected_variable",
        "state_initialization", "state_source_call_index", "state_source_iterations",
        "state_capture_status",
        "status", "decoder_status", "iterations", "iterations_this_call",
        "decoder_runtime_s", "wall_s", "rss_bytes", "syndrome_valid",
        "syndrome_ok_reported", "exact", "syndrome_valid_wrong", "raw_vector_index",
        "belief_provenance", "extrinsic_provenance", "score_original_prior", "failure_reason",
    )

    def persist_first_pass() -> None:
        arrays = _diagnostics_arrays(
            selected_sources, pairs, original_prior, raw_call_ids, raw_vectors,
            baseline_belief_call_ids, baseline_beliefs,
            failure_call_ids, failure_c2v_rows, failure_c2v_columns,
            failure_c2v_messages, failure_c2v_captured)
        diagnostics_path = root / "diagnostics.npz"
        np.savez_compressed(diagnostics_path, **arrays)
        _write_csv(root / "calls.csv", calls, call_fields)
        _write_csv(root / "frames.csv", pairs, pair_fields)
        _write_json(root / "summary.json", summary)
        manifest = {
            "batch_uuid": BATCH_UUID, "contract": CONTRACT,
            "track": "EXPLORE", "status": summary["status"],
            "command": command, "source_identity": source_identity,
            "source_graph_maps": [
                {key: value for key, value in row.items() if key != "H"}
                for row in selected_sources
            ],
            "seed_namespace": SEED_NAMESPACE, "seed_plan": plan,
            "seed_exclusions": exclusion_records,
            "artifacts": ["manifest.json", "summary.json", "calls.csv",
                          "frames.csv", "diagnostics.npz", "EXPLORATION_LOG.md"],
        }
        _write_json(root / "manifest.json", manifest)
        return diagnostics_path

    diagnostics_path = persist_first_pass()
    checkpoint_wall = max(float(now()) - start, 0.0)
    checkpoint_rss = rss_fn()
    if checkpoint_rss is not None:
        checkpoint_rss = int(checkpoint_rss)
        peak_rss = checkpoint_rss if peak_rss is None else max(peak_rss, checkpoint_rss)
    output_size = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
    postwrite_reasons = []
    if checkpoint_wall > WALL_CAP_S:
        postwrite_reasons.append("total_wall_cap_after_first_pass_artifacts")
    if checkpoint_rss is not None and checkpoint_rss > RSS_CAP_BYTES:
        postwrite_reasons.append("peak_rss_cap_after_first_pass_artifacts")
    if output_size > ARTIFACT_CAP_BYTES:
        postwrite_reasons.append("output_cap_after_first_pass_artifacts")
    if postwrite_reasons:
        if run_status == "COMPLETE":
            run_status = "INCOMPLETE"
        summary["status"] = run_status
        summary["resource_violations"] += len(postwrite_reasons)
        stop_reasons.extend(reason for reason in postwrite_reasons if reason not in stop_reasons)
        summary["stop_reasons"] = stop_reasons
        _null_comparisons(summary)
        summary["classification"] = "INCOMPLETE" if run_status != "STOP" else "STOP"

    summary["peak_rss_bytes"] = peak_rss
    summary["resource_checkpoint_wall_s"] = checkpoint_wall
    summary["output_bytes_at_checkpoint"] = output_size
    summary["diagnostics_bytes"] = diagnostics_path.stat().st_size
    _write_json(root / "summary.json", summary)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = summary["status"]
    manifest["classification"] = summary["classification"]
    manifest["physical_calls"] = summary["attempted_physical_calls"]
    manifest["physical_iterations"] = summary["physical_decoder_iterations"]
    manifest["resource_checkpoint_wall_s"] = checkpoint_wall
    manifest["peak_rss_bytes"] = peak_rss
    _write_json(manifest_path, manifest)
    _append_log(log_path, (
        f"FINAL_STATUS={summary['status']}; classification={summary['classification']}; "
        f"completed_pairs={summary['completed_pairs']}; "
        f"physical_calls={summary['attempted_physical_calls']}; "
        f"physical_iterations={summary['physical_decoder_iterations']}; "
        f"resource_checkpoint_wall_s={checkpoint_wall:.6f}; "
        f"peak_rss_bytes={peak_rss}; stop_reasons={stop_reasons}"))

    public_calls = [{key: value for key, value in row.items()
                     if not key.startswith("_")} for row in calls]
    public_pairs = [{key: value for key, value in row.items()
                     if key not in ("truth", "syndrome", "H")} for row in pairs]
    result = dict(summary)
    result.update({
        "summary": summary, "calls": public_calls, "pairs": public_pairs,
        "source_identity": source_identity,
        "source_maps": [{key: value for key, value in row.items() if key != "H"}
                        for row in selected_sources],
        "artifacts": {
            "manifest": str(manifest_path), "summary": str(root / "summary.json"),
            "calls": str(root / "calls.csv"), "frames": str(root / "frames.csv"),
            "diagnostics": str(diagnostics_path), "exploration_log": str(log_path),
        },
    })
    return result


def _bind_production() -> dict[str, Any]:
    """Bind local source/sampler/decoder only under explicit --execute."""
    from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as sampler_module

    def reference(h, prior, syndrome, *, max_iter, damping_alpha, warm_beliefs, field):
        if warm_beliefs is not None or field is not None:
            raise ValueError("reference baseline must be cold with field=None")
        return edge_state.capture_reference_state(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha)

    def control(h, prior, syndrome, *, max_iter, damping_alpha, warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha,
            warm_beliefs=warm_beliefs, field=field)

    def explicit_state_loop(h, prior, syndrome, *, max_iter, damping_alpha, state, field):
        return edge_state.decode_row_layered_edge_state(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha,
            state=state, field=field)

    return {
        "source_reader": rescue._default_source_reader(),
        "sampler": sampler_module.sample_error,
        "decode_fns": {
            "reference": reference, "control": control,
            "edge_state": explicit_state_loop,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GF32 explicit edge-state prior-swap EXPLORE")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true", help="source-free seed/contract checks")
    mode.add_argument("--dry-run", action="store_true", help="fresh-root check without reads/writes")
    mode.add_argument("--execute", action="store_true", help="run the one frozen synthetic batch")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.dry_run:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(**_bind_production(), out_root=args.out_root, command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
