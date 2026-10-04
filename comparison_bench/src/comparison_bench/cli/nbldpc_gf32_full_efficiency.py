"""Complete paired replay of the frozen GF(32) soft-prior source batch."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_gf32_kernel_hotspots as hotspots
from comparison_bench.cli import nbldpc_gf32_softprior_rescue as rescue
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

BATCH_UUID = "dcaa868f-b094-4551-8458-0511003a4405"
CONTRACT = "NBLDPC-GF32-FULL-SOFTPRIOR-EFFICIENCY-20261002/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-softprior-replica-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_full_eff_dcaa868f"
PARENT_ROOT = Path("workspace") / "gf32_softprior_replica_cbe151fe"
GUESSES = (0, 1, 3, 7, 15, 31)
N, M, Q = 128, 52, 32
MAX_ITER = 90
DAMPING_ALPHA = 1.0
TIE_TOL = 1e-12
WALL_CAP_S = 600.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 10 * 1024 * 1024
PUBLIC_SYNDROME_BITS_PER_FRAME = 260
EXPECTED_BASELINE_EXACT = 142
EXPECTED_SELECTED_EXACT = 156

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_full_efficiency --execute "
    "--out-root workspace/gf32_full_eff_dcaa868f"
)

BRANCH_SCORE_KEYS = (
    "branch_score_call_index", "branch_score_branch_index",
    "branch_score_guess_symbol", "branch_score_original_prior",
    "branch_score_available", "branch_score_syndrome_valid",
)
SOURCE_DIAGNOSTIC_KEYS = tuple(hotspots.DIAGNOSTIC_KEYS) + BRANCH_SCORE_KEYS
PATHS = ("reference", "candidate")
PATH_CODE = {"reference": 0, "candidate": 1}

CALL_FIELDS = (
    "path", "path_code", "source_call_index", "pair_index", "graph_id",
    "call_role", "branch_index", "guess_symbol", "selected_variable",
    "raw_vector_index", "iterations", "decoder_status", "reported_syndrome_ok",
    "computed_syndrome_valid", "decoder_runtime_s", "outer_wall_s", "rss_after_call_bytes",
    "source_vector_match", "source_iterations_match", "source_status_match",
    "source_reported_match", "source_syndrome_match", "source_belief_match",
    "source_belief_max_abs_diff", "final_belief_finite", "pair_vector_match",
    "pair_iterations_match", "pair_status_match", "pair_reported_match",
    "pair_syndrome_match", "pair_belief_match", "pair_belief_max_abs_diff",
    "branch_score_original_prior", "source_branch_score_original_prior",
    "branch_score_match", "exact", "valid_wrong", "failure_reason",
)

FRAME_FIELDS = (
    "pair_index", "graph_id", "baseline_call_index", "source_candidate_call_index",
    "reference_selected_call_index", "candidate_selected_call_index",
    "reference_selected_branch_index", "candidate_selected_branch_index",
    "reference_pointer_match_source", "candidate_pointer_match_source",
    "paths_select_same_call", "baseline_syndrome_valid", "source_score_match",
    "baseline_exact_reference", "baseline_exact_candidate", "selected_exact_reference",
    "selected_exact_candidate", "selected_valid_wrong_reference",
    "selected_valid_wrong_candidate", "raw_branch_valid_wrong_reference",
    "raw_branch_valid_wrong_candidate", "paired_class_reference",
    "paired_class_candidate",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve(path: str | Path, repo_root: str | Path | None = None) -> Path:
    base = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(path)
    return requested.resolve() if requested.is_absolute() else (base / requested).resolve()


def _require_frozen_root(out_root: str | Path) -> None:
    if Path(out_root) != OUT_ROOT_RELATIVE:
        raise ValueError(f"out_root must be the frozen relative path {OUT_ROOT_RELATIVE}")


def _preflight_root(out_root: str | Path, repo_root: str | Path | None = None) -> Path:
    _require_frozen_root(out_root)
    root = _resolve(out_root, repo_root)
    if root.exists():
        raise FileExistsError(f"refusing existing output root {root}")
    return root


def verify_t0(*, out_root: str | Path = OUT_ROOT_RELATIVE,
              repo_root: str | Path | None = None) -> dict[str, Any]:
    root = _preflight_root(out_root, repo_root)
    return {
        "status": "PASS", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE, "source_reads": 0,
        "decoder_calls": 0, "sampler_calls": 0, "writes": 0,
        "out_root": str(root),
    }


def dry_run(*, out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    result = verify_t0(out_root=out_root, repo_root=repo_root)
    result["status"] = "DRY_RUN"
    return result


def _rss_bytes() -> int | None:
    try:
        import resource
    except ImportError:
        return None
    # Linux / WSL reports ru_maxrss in KiB.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _read_parent(root: Path) -> dict[str, Any]:
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        summary = json.load(stream)
    with np.load(root / "diagnostics.npz", allow_pickle=False) as archive:
        diagnostics = {key: archive[key] for key in SOURCE_DIAGNOSTIC_KEYS}
    return {"manifest": manifest, "summary": summary, "diagnostics": diagnostics}


def _source_reader(repo_root: str | Path | None = None) -> Callable[[], Mapping[str, Any]]:
    root = _resolve(PARENT_ROOT, repo_root)
    return lambda: _read_parent(root)


def _validate_source(loaded: Mapping[str, Any]) -> dict[str, Any]:
    validated = hotspots._validate_source(loaded)
    diagnostics = loaded["diagnostics"]
    if not set(BRANCH_SCORE_KEYS).issubset(diagnostics):
        raise ValueError("source_branch_score_diagnostics_missing")

    values = validated["values"]
    pair_rows = validated["pair_rows"]
    call_by_id = validated["call_by_id"]
    pair_index = np.asarray(diagnostics["pair_index"], dtype=np.int64)
    pair_graph = np.asarray(diagnostics["pair_graph_id"], dtype=np.int64)
    pair_selected = np.asarray(diagnostics["pair_selected_variable"], dtype=np.int64)
    pair_truth = np.asarray(diagnostics["pair_truth"], dtype=np.int64)
    pair_syndrome = np.asarray(diagnostics["pair_syndrome"], dtype=np.int64)
    if len(pair_rows) != 192 or len(call_by_id) != 492:
        raise ValueError("source_must_contain_192_pairs_and_492_calls")
    if pair_truth.shape != (192, N) or pair_syndrome.shape != (192, M):
        raise ValueError("source_pair_truth_or_syndrome_shape_mismatch")
    if any(int(np.count_nonzero(pair_graph == graph)) != 32 for graph in hotspots.GRAPH_IDS):
        raise ValueError("source_graph_pair_count_mismatch")

    call_ids_by_pair: dict[int, list[int]] = {int(pair): [] for pair in pair_index}
    for call_id, off in call_by_id.items():
        pair_id = int(values["pair"][off])
        if pair_id not in call_ids_by_pair:
            raise ValueError("source_call_pair_missing")
        call_ids_by_pair[pair_id].append(int(call_id))
    baseline_calls = [call_id for call_id, off in call_by_id.items()
                      if str(values["role"][off]) == "baseline"]
    branch_calls = [call_id for call_id, off in call_by_id.items()
                    if str(values["role"][off]) == "soft_prior"]
    failed_pairs = []
    for pair_id in sorted(call_ids_by_pair):
        pair = pair_rows[pair_id]
        baseline_id = int(pair["baseline"])
        baseline_off = call_by_id[baseline_id]
        branch_ids = [cid for cid in call_ids_by_pair[pair_id]
                      if str(values["role"][call_by_id[cid]]) == "soft_prior"]
        if bool(values["valid"][baseline_off]):
            if branch_ids or int(pair["candidate"]) != baseline_id:
                raise ValueError("source_valid_baseline_must_be_unbranched_pass_through")
            continue
        failed_pairs.append(pair_id)
        if len(branch_ids) != len(GUESSES):
            raise ValueError("source_failed_baseline_must_have_six_branches")
        selected = int(pair_selected[int(pair["offset"])])
        if not 0 <= selected < N or int(values["selected"][baseline_off]) != selected:
            raise ValueError("source_selected_variable_map_mismatch")
        for branch_id in branch_ids:
            off = call_by_id[branch_id]
            branch = int(values["branch"][off])
            if (branch not in range(6) or int(values["guess"][off]) != GUESSES[branch]
                    or int(values["selected"][off]) != selected):
                raise ValueError("source_branch_identity_or_selected_variable_mismatch")
    if (len(baseline_calls) != 192 or len(branch_calls) != 300
            or len(failed_pairs) != 50):
        raise ValueError("source_baseline_failure_or_branch_count_mismatch")

    selector_call = np.asarray(diagnostics["selector_call_index"], dtype=np.int64)
    selector_var = np.asarray(diagnostics["selector_selected_column"], dtype=np.int64)
    selector_by_call = {int(call): int(var) for call, var in zip(selector_call, selector_var)}
    pair_pos = {int(pair): pos for pos, pair in enumerate(pair_index)}
    h_by_graph = {
        int(graph): np.asarray(matrix, dtype=np.int64)
        for graph, matrix in zip(diagnostics["source_graph_id"], diagnostics["H_deep"])
    }
    for pair_id in failed_pairs:
        pair = pair_rows[pair_id]
        baseline_id = int(pair["baseline"])
        off = call_by_id[baseline_id]
        selected = int(pair_selected[int(pair["offset"])])
        stored = validated["belief_by_call"].get(baseline_id)
        if stored is None or stored[1] != "CHECK_UPDATED":
            raise ValueError("source_failed_baseline_belief_provenance_mismatch")
        if selector_by_call.get(baseline_id) != selected:
            raise ValueError("source_selector_map_mismatch")
        selected_again, _ = rescue.select_uncertain_variable(
            h_by_graph[int(values["graph"][off])], validated["raw_by_call"][baseline_id],
            stored[0], pair_syndrome[pair_pos[pair_id]], belief_provenance=stored[1])
        if selected_again != selected:
            raise ValueError("source_selected_variable_recomputation_mismatch")

    score_arrays = {
        "call": np.asarray(diagnostics["branch_score_call_index"], dtype=np.int64),
        "branch": np.asarray(diagnostics["branch_score_branch_index"], dtype=np.int64),
        "guess": np.asarray(diagnostics["branch_score_guess_symbol"], dtype=np.int64),
        "score": np.asarray(diagnostics["branch_score_original_prior"], dtype=np.float64),
        "available": np.asarray(diagnostics["branch_score_available"], dtype=np.bool_),
        "valid": np.asarray(diagnostics["branch_score_syndrome_valid"], dtype=np.bool_),
    }
    n_scores = len(score_arrays["call"])
    if any(array.shape != (n_scores,) for array in score_arrays.values()) or n_scores != 300:
        raise ValueError("source_branch_score_arrays_mismatch")
    score_by_call: dict[int, dict[str, Any]] = {}
    for i, call_id_value in enumerate(score_arrays["call"]):
        call_id = int(call_id_value)
        if call_id in score_by_call or call_id not in branch_calls:
            raise ValueError("source_branch_score_call_map_mismatch")
        off = call_by_id[call_id]
        if (int(values["branch"][off]) != int(score_arrays["branch"][i])
                or int(values["guess"][off]) != int(score_arrays["guess"][i])
                or bool(values["valid"][off]) != bool(score_arrays["valid"][i])
                or bool(score_arrays["available"][i]) != bool(score_arrays["valid"][i])):
            raise ValueError("source_branch_score_identity_or_validity_mismatch")
        score = float(score_arrays["score"][i])
        if bool(score_arrays["available"][i]):
            if not math.isfinite(score):
                raise ValueError("source_available_branch_score_not_finite")
        elif not math.isnan(score):
            raise ValueError("source_unavailable_branch_score_not_nan")
        score_by_call[call_id] = {
            "branch_index": int(score_arrays["branch"][i]),
            "guess_symbol": int(score_arrays["guess"][i]),
            "score": score if bool(score_arrays["available"][i]) else None,
            "syndrome_valid": bool(score_arrays["valid"][i]),
        }
    if set(score_by_call) != set(branch_calls):
        raise ValueError("source_branch_score_call_coverage_mismatch")

    h_arrays = np.asarray(diagnostics["H_deep"], dtype=np.int64)
    graph_ids = np.asarray(diagnostics["source_graph_id"], dtype=np.int64)
    prior = np.asarray(diagnostics["original_prior"], dtype=np.float64)
    return {
        **validated,
        "pair_ids": [int(x) for x in pair_index],
        "pair_graph": {int(pair): int(graph) for pair, graph in zip(pair_index, pair_graph)},
        "pair_pos": pair_pos,
        "pair_truth": pair_truth,
        "pair_syndrome": pair_syndrome,
        "pair_selected": pair_selected,
        "call_ids_by_pair": call_ids_by_pair,
        "branch_calls": set(branch_calls),
        "failed_pairs": set(failed_pairs),
        "h_by_graph": {int(graph): h_arrays[i] for i, graph in enumerate(graph_ids)},
        "score_by_call": score_by_call,
        "prior": prior,
    }


def _call_input(source: Mapping[str, Any], call_id: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = source["values"]
    diagnostics = source["diagnostics"]
    off = source["call_by_id"][int(call_id)]
    pair_id = int(values["pair"][off])
    pair = source["pair_rows"][pair_id]
    pair_off = int(pair["offset"])
    graph = int(values["graph"][off])
    prior = source["prior"].copy()
    if str(values["role"][off]) == "soft_prior":
        selected = int(values["selected"][off])
        guess = int(values["guess"][off])
        prior[selected, :] = 0.0
        prior[selected, guess] = 1.0
    return source["h_by_graph"][graph], prior, np.asarray(
        diagnostics["pair_syndrome"][pair_off], dtype=np.int64)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
                    encoding="utf-8")


def _write_csv(path: Path, fields: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _null_complete_totals(summary: dict[str, Any]) -> None:
    for key in (
        "baseline_calls_per_path", "branch_calls_per_path", "iterations_by_path",
        "decoder_runtime_s_by_path", "outer_wall_s_by_path", "control_wall_s",
        "candidate_pipeline_wall_s", "candidate_pipeline_to_control_wall_ratio",
        "paired_observed_wall_s", "baseline_exact_by_path", "selected_exact_by_path",
        "selected_valid_wrong_by_path", "raw_branch_valid_wrong_by_path",
        "selected_pointer_matches_source_by_path", "source_roundtrip_matches",
        "paired_matches", "max_final_belief_abs_diff", "per_graph",
        "paired_class_counts", "delta_exact_by_path",
    ):
        summary[key] = None


def _paired_class(baseline_exact: bool, selected_exact: bool) -> str:
    if baseline_exact and selected_exact:
        return "both_exact"
    if selected_exact:
        return "candidate_only_exact"
    if baseline_exact:
        return "control_only_exact"
    return "neither_exact"


def _summary_template() -> dict[str, Any]:
    return {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT, "track": "EXPLORE",
        "status": "STOP", "classification": None, "source_reads": 0,
        "source_pairs": 0, "source_calls": 0, "decoder_calls": 0,
        "calls_complete": 0, "paired_call_ids_complete": 0,
        "baseline_calls_per_path": None, "branch_calls_per_path": None,
        "iterations_by_path": None, "decoder_runtime_s_by_path": None,
        "outer_wall_s_by_path": None, "control_wall_s": None,
        "candidate_pipeline_wall_s": None,
        "candidate_pipeline_to_control_wall_ratio": None,
        "paired_observed_wall_s": None, "baseline_exact_by_path": None,
        "selected_exact_by_path": None, "selected_valid_wrong_by_path": None,
        "raw_branch_valid_wrong_by_path": None,
        "selected_pointer_matches_source_by_path": None,
        "source_roundtrip_matches": None, "paired_matches": None,
        "max_final_belief_abs_diff": None, "per_graph": None,
        "paired_class_counts": None, "delta_exact_by_path": None,
        "stop_reasons": [], "resource_events": [], "elapsed_wall_s": 0.0,
        "peak_rss_bytes": None, "first_pass_output_bytes": None,
        "terminal_artifact_bytes": None,
        "public_syndrome_bits_per_method": 192 * PUBLIC_SYNDROME_BITS_PER_FRAME,
        "internal_branch_disclosure_bits": 0, "replay_new_disclosure_bits": 0,
        "verification_status": "NOT_IMPLEMENTED", "undetected_status": "NOT_MEASURED",
        "sampler_calls": 0, "search_calls": 0, "graph_build_calls": 0,
    }


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        reference_decoder: Callable[..., Any], candidate_decoder: Callable[..., Any],
        out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    root = _preflight_root(out_root, repo_root)
    if not all(callable(fn) for fn in (source_reader, reference_decoder, candidate_decoder)):
        raise ValueError("source_reader, reference_decoder, and candidate_decoder callbacks are required")
    rss_fn = _rss_bytes if rss_fn is None else rss_fn
    root.mkdir(parents=True)
    started = float(now())
    summary = _summary_template()
    call_records: list[dict[str, Any]] = []
    frame_records: list[dict[str, Any]] = []
    outcomes: dict[str, dict[int, dict[str, Any]]] = {path: {} for path in PATHS}
    stop_reasons: list[str] = []
    resource_events: list[dict[str, Any]] = []
    peak_rss: int | None = None
    source: dict[str, Any] | None = None
    source_meta: dict[str, Any] | None = None
    decoder_calls = source_reads = paired_call_ids = source_match_count = 0
    iterations_run = 0
    pair_match_count = 0
    max_belief_diff = 0.0
    call_record_by_key: dict[tuple[str, int], dict[str, Any]] = {}

    def check_resources(event: str) -> bool:
        nonlocal peak_rss
        elapsed = max(float(now()) - started, 0.0)
        rss = rss_fn()
        if rss is not None:
            rss = int(rss)
            peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        over = False
        if elapsed > WALL_CAP_S:
            resource_events.append({"event": event, "kind": "wall_cap", "elapsed_wall_s": elapsed})
            over = True
        if rss is not None and rss > RSS_CAP_BYTES:
            resource_events.append({"event": event, "kind": "rss_cap", "rss_bytes": rss})
            over = True
        return over

    def stop(reason: str, *, incomplete: bool = False) -> None:
        if reason not in stop_reasons:
            stop_reasons.append(reason)
        summary["status"] = "INCOMPLETE" if incomplete else "STOP"

    try:
        source_reads += 1
        source = _validate_source(source_reader())
        source_meta = dict(source["manifest"].get("source_identity", {}))
        summary["source_pairs"] = len(source["pair_ids"])
        summary["source_calls"] = len(source["call_by_id"])
        if check_resources("after_source_read"):
            stop("resource_cap_after_source_read", incomplete=True)
    except Exception as exc:
        stop(f"source_validation:{type(exc).__name__}:{exc}")

    if source is not None and not stop_reasons:
        values = source["values"]
        call_by_id = source["call_by_id"]
        diagnostics = source["diagnostics"]
        belief_by_call = source["belief_by_call"]
        raw_by_call = source["raw_by_call"]
        pair_rows = source["pair_rows"]
        for call_id in sorted(call_by_id):
            off = call_by_id[call_id]
            pair_id = int(values["pair"][off])
            pair_row = pair_rows[pair_id]
            pair_off = int(pair_row["offset"])
            role = str(values["role"][off])
            path_order = PATHS if call_id % 2 == 0 else tuple(reversed(PATHS))
            current: dict[str, dict[str, Any]] = {}
            for path in path_order:
                decoder = reference_decoder if path == "reference" else candidate_decoder
                h, prior, syndrome = _call_input(source, call_id)
                record: dict[str, Any] = {
                    "path": path, "path_code": PATH_CODE[path],
                    "source_call_index": call_id, "pair_index": pair_id,
                    "graph_id": int(values["graph"][off]), "call_role": role,
                    "branch_index": int(values["branch"][off]),
                    "guess_symbol": int(values["guess"][off]),
                    "selected_variable": int(values["selected"][off]),
                    "raw_vector_index": int(values["vector"][off]),
                    "iterations": None, "decoder_status": None,
                    "reported_syndrome_ok": None, "computed_syndrome_valid": None,
                    "decoder_runtime_s": None, "outer_wall_s": None,
                    "rss_after_call_bytes": None, "source_vector_match": False,
                    "source_iterations_match": False, "source_status_match": False,
                    "source_reported_match": None, "source_syndrome_match": False,
                    "source_belief_match": None, "source_belief_max_abs_diff": None,
                    "final_belief_finite": False, "pair_vector_match": None,
                    "pair_iterations_match": None, "pair_status_match": None,
                    "pair_reported_match": None, "pair_syndrome_match": None,
                    "pair_belief_match": None, "pair_belief_max_abs_diff": None,
                    "branch_score_original_prior": None,
                    "source_branch_score_original_prior": None,
                    "branch_score_match": None, "exact": None, "valid_wrong": None,
                    "failure_reason": "",
                }
                call_records.append(record)
                call_record_by_key[(path, call_id)] = record
                before = float(now())
                result = None
                error = None
                try:
                    result = decoder(
                        h, prior, syndrome, max_iter=MAX_ITER,
                        damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                after = float(now())
                record["outer_wall_s"] = max(after - before, 0.0)
                decoder_calls += 1
                if error is not None or result is None:
                    record["failure_reason"] = error or "decoder_returned_none"
                    record["rss_after_call_bytes"] = rss_fn()
                    if check_resources(f"after_call_{decoder_calls}"):
                        stop("resource_cap_after_call", incomplete=True)
                    else:
                        stop("decoder_call_failed")
                    break
                try:
                    vector = np.asarray(result.x_hat, dtype=np.int64).reshape(-1)
                    if (vector.shape != (N,) or np.any(vector < 0) or np.any(vector >= Q)):
                        raise ValueError("returned_vector_shape_or_symbol_mismatch")
                    record["_x_hat"] = vector.astype(np.uint8, copy=True)
                    iterations = int(result.iterations)
                    if iterations < 0 or iterations > MAX_ITER:
                        raise ValueError("returned_iteration_count_out_of_range")
                    status = str(result.status)
                    reported = bool(result.syndrome_ok)
                    runtime_s = float(result.runtime_s)
                    beliefs = np.asarray(result.final_beliefs, dtype=np.float64)
                    if beliefs.shape != (N, Q) or not np.all(np.isfinite(beliefs)):
                        raise ValueError("final_beliefs_shape_or_finiteness_mismatch")
                    computed = np.asarray(layout.gf32_syndrome(h, vector), dtype=np.int64)
                    valid = computed.shape == (M,) and np.array_equal(computed, syndrome)
                    record.update({
                        "iterations": iterations, "decoder_status": status,
                        "reported_syndrome_ok": reported,
                        "computed_syndrome_valid": bool(valid),
                        "decoder_runtime_s": runtime_s,
                        "final_belief_finite": True,
                    })
                    saved_vector = np.asarray(raw_by_call[call_id], dtype=np.int64)
                    vector_match = np.array_equal(vector, saved_vector)
                    iter_match = iterations == int(values["iterations"][off])
                    status_match = status == str(values["decoder_status"][off])
                    source_valid_match = valid == bool(values["valid"][off])
                    reported_available = bool(values["reported_available"][off])
                    reported_match = (reported == bool(values["reported"][off])
                                      if reported_available else None)
                    if reported != bool(valid):
                        raise ValueError("decoder_reported_syndrome_disagrees_with_computed")
                    if reported_match is False:
                        raise ValueError("source_reported_syndrome_mismatch")
                    source_belief_match: bool | None = None
                    source_belief_diff: float | None = None
                    if role == "baseline" and not bool(values["valid"][off]):
                        stored = belief_by_call.get(call_id)
                        if stored is None or stored[1] != "CHECK_UPDATED":
                            raise ValueError("source_failed_baseline_belief_missing_or_wrong_provenance")
                        source_belief_diff = float(np.max(np.abs(beliefs - stored[0])))
                        source_belief_match = bool(np.allclose(
                            beliefs, stored[0], rtol=0.0, atol=1e-12))
                        if not source_belief_match:
                            raise ValueError("source_failed_baseline_belief_mismatch")
                    record.update({
                        "source_vector_match": bool(vector_match),
                        "source_iterations_match": bool(iter_match),
                        "source_status_match": bool(status_match),
                        "source_reported_match": reported_match,
                        "source_syndrome_match": bool(source_valid_match),
                        "source_belief_match": source_belief_match,
                        "source_belief_max_abs_diff": source_belief_diff,
                        "rss_after_call_bytes": rss_fn(),
                    })
                    if source_belief_diff is not None:
                        record["source_belief_max_abs_diff"] = source_belief_diff
                    if not (vector_match and iter_match and status_match and source_valid_match):
                        raise ValueError("saved_call_roundtrip_mismatch")
                    if iterations_run + iterations > 88560:
                        record["failure_reason"] = "total_iteration_cap_exceeded"
                        stop("iteration_cap_after_call", incomplete=True)
                        break
                    iterations_run += iterations
                    current[path] = {
                        "x_hat": vector.astype(np.uint8, copy=True),
                        "beliefs": beliefs.copy(), "iterations": iterations,
                        "status": status, "reported": reported, "valid": bool(valid),
                        "runtime_s": runtime_s, "wall_s": float(record["outer_wall_s"]),
                    }
                    outcomes[path][call_id] = {key: value for key, value in current[path].items()
                                               if key != "beliefs"}
                    source_match_count += 1
                except Exception as exc:
                    record["failure_reason"] = f"{type(exc).__name__}: {exc}"
                    stop("source_or_result_gate_mismatch")
                    if check_resources(f"after_call_{decoder_calls}"):
                        stop("resource_cap_after_call", incomplete=True)
                    break

                # Preserve the actual returned vector immediately for the partial artifact.
                record["_x_hat"] = current[path]["x_hat"]
                if check_resources(f"after_call_{decoder_calls}"):
                    stop("resource_cap_after_call", incomplete=True)
                    break

            if stop_reasons:
                break
            if len(current) != 2:
                stop("paired_call_missing")
                break
            ref, fast = current["reference"], current["candidate"]
            vector_match = bool(np.array_equal(ref["x_hat"], fast["x_hat"]))
            iterations_match = ref["iterations"] == fast["iterations"]
            status_match = ref["status"] == fast["status"]
            report_match = ref["reported"] == fast["reported"]
            syndrome_match = ref["valid"] == fast["valid"]
            belief_diff = float(np.max(np.abs(ref["beliefs"] - fast["beliefs"])))
            belief_match = bool(np.allclose(ref["beliefs"], fast["beliefs"], rtol=0.0, atol=1e-12))
            max_belief_diff = max(max_belief_diff, belief_diff)
            for path in PATHS:
                row = call_record_by_key[(path, call_id)]
                row.update({
                    "pair_vector_match": vector_match,
                    "pair_iterations_match": bool(iterations_match),
                    "pair_status_match": bool(status_match),
                    "pair_reported_match": bool(report_match),
                    "pair_syndrome_match": bool(syndrome_match),
                    "pair_belief_match": belief_match,
                    "pair_belief_max_abs_diff": belief_diff,
                })
            paired_call_ids += 1
            if not all((vector_match, iterations_match, status_match, report_match,
                        syndrome_match, belief_match)):
                stop("paired_reference_candidate_mismatch")
                break
            pair_match_count += 1
            if check_resources(f"after_pair_{paired_call_ids}"):
                stop("resource_cap_after_pair", incomplete=True)
                break

    if source is not None and not stop_reasons and len(outcomes["reference"]) == 492:
        try:
            frame_records = _select_all(source, outcomes, call_record_by_key)
            score_gate = all(bool(frame["source_score_match"]) for frame in frame_records)
            pointer_gate = all(bool(frame["reference_pointer_match_source"])
                               and bool(frame["candidate_pointer_match_source"])
                               for frame in frame_records)
            same_path_gate = all(bool(frame["paths_select_same_call"]) for frame in frame_records)
            if not (score_gate and pointer_gate and same_path_gate):
                stop("candidate_score_or_pointer_gate_mismatch")
            else:
                _evaluate_truth(source, outcomes, frame_records, call_record_by_key)
                summary.update(_complete_totals(
                    source, outcomes, frame_records, call_record_by_key,
                    source_match_count, pair_match_count, max_belief_diff))
                if (summary["baseline_exact_by_path"] != {"reference": EXPECTED_BASELINE_EXACT,
                                                            "candidate": EXPECTED_BASELINE_EXACT}
                        or summary["selected_exact_by_path"] != {"reference": EXPECTED_SELECTED_EXACT,
                                                                  "candidate": EXPECTED_SELECTED_EXACT}):
                    stop("frozen_C142_K156_anchor_mismatch")
                else:
                    summary["status"] = "FULL_SOFTPRIOR_IMPLEMENTATION_MATCH"
                    summary["classification"] = "IMPLEMENTATION_MATCH_ONLY"
        except Exception as exc:
            stop(f"selection_or_outcome_gate:{type(exc).__name__}:{exc}")

    if stop_reasons:
        summary["status"] = "INCOMPLETE" if any(
            row.get("kind") in ("wall_cap", "rss_cap") for row in resource_events) else "STOP"
        _null_complete_totals(summary)
    summary["source_reads"] = source_reads
    summary["decoder_calls"] = decoder_calls
    summary["calls_complete"] = len(outcomes["reference"]) + len(outcomes["candidate"])
    summary["paired_call_ids_complete"] = paired_call_ids
    summary["stop_reasons"] = stop_reasons
    summary["resource_events"] = resource_events
    summary["peak_rss_bytes"] = peak_rss
    summary["elapsed_wall_s"] = max(float(now()) - started, 0.0)

    vector_rows = [row for row in call_records if "_x_hat" in row]
    vectors = np.stack([row.pop("_x_hat") for row in vector_rows]).astype(np.uint8, copy=False) \
        if vector_rows else np.empty((0, N), dtype=np.uint8)
    source_call_ids = np.asarray([row["source_call_index"] for row in vector_rows], dtype=np.int64)
    pair_ids = np.asarray([row["pair_index"] for row in vector_rows], dtype=np.int64)
    path_codes = np.asarray([row["path_code"] for row in vector_rows], dtype=np.uint8)

    manifest = {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "seed_namespace": SEED_NAMESPACE, "status": summary["status"],
        "classification": summary["classification"], "exact_command": command,
        "parent_root": str(PARENT_ROOT), "parent_batch_uuid": hotspots.PARENT_UUID,
        "parent_contract": hotspots.PARENT_CONTRACT, "source_identity": source_meta,
        "settings": {"max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA,
                     "warm_beliefs": None, "field": None, "branch_guesses": list(GUESSES),
                     "tie_tolerance": TIE_TOL},
        "budgets": {"wall_s": WALL_CAP_S, "rss_bytes": RSS_CAP_BYTES,
                    "artifact_bytes": ARTIFACT_CAP_BYTES, "decoder_calls_max": 984,
                    "iterations_max": 88560},
        "source_reads": source_reads, "decoder_calls": decoder_calls,
        "sampler_calls": 0, "stop_reasons": stop_reasons,
    }
    artifact_paths = {
        name: root / name for name in (
            "manifest.json", "summary.json", "call_records.csv",
            "frame_records.csv", "outputs.npz", "EXPLORATION_LOG.md")
    }
    np.savez_compressed(
        artifact_paths["outputs.npz"], x_hat=vectors,
        source_call_index=source_call_ids, pair_index=pair_ids, path_code=path_codes)
    _write_csv(artifact_paths["call_records.csv"], CALL_FIELDS, call_records)
    _write_csv(artifact_paths["frame_records.csv"], FRAME_FIELDS, frame_records)
    summary["first_pass_output_bytes"] = sum(
        path.stat().st_size for key, path in artifact_paths.items()
        if key not in ("summary.json", "manifest.json", "EXPLORATION_LOG.md") and path.exists())
    _write_json(artifact_paths["summary.json"], summary)
    _write_json(artifact_paths["manifest.json"], manifest)
    artifact_bytes = sum(path.stat().st_size for path in artifact_paths.values()
                         if path.exists() and path.name != "EXPLORATION_LOG.md")
    over_resource = check_resources("after_first_pass_artifacts")
    if artifact_bytes > ARTIFACT_CAP_BYTES:
        stop("artifact_cap", incomplete=True)
    if over_resource:
        stop("resource_cap_after_first_pass_artifacts", incomplete=True)
    summary["first_pass_output_bytes"] = artifact_bytes
    summary["terminal_artifact_bytes"] = artifact_bytes
    if stop_reasons:
        _null_complete_totals(summary)
        summary["source_reads"] = source_reads
        summary["decoder_calls"] = decoder_calls
        summary["calls_complete"] = len(outcomes["reference"]) + len(outcomes["candidate"])
        summary["paired_call_ids_complete"] = paired_call_ids
        summary["stop_reasons"] = stop_reasons
        summary["resource_events"] = resource_events
        summary["peak_rss_bytes"] = peak_rss
        if any(event.get("kind") in ("wall_cap", "rss_cap") for event in resource_events) \
                or "artifact_cap" in stop_reasons:
            summary["status"] = "INCOMPLETE"
        else:
            summary["status"] = "STOP"
        manifest["status"] = summary["status"]
        manifest["stop_reasons"] = stop_reasons
    _write_json(artifact_paths["summary.json"], summary)
    _write_json(artifact_paths["manifest.json"], manifest)
    artifact_bytes = sum(path.stat().st_size for path in artifact_paths.values() if path.exists())
    summary["terminal_artifact_bytes"] = artifact_bytes
    _write_json(artifact_paths["summary.json"], summary)
    artifact_paths["EXPLORATION_LOG.md"].write_text(
        f"EXPLORE {BATCH_UUID}\nstatus: {summary['status']}\nsource reads: {source_reads}\n"
        f"decoder calls: {decoder_calls}; sampler/search/graph-build: 0/0/0\n"
        f"paired source call IDs: {paired_call_ids}\nstop reasons: {json.dumps(stop_reasons)}\n"
        f"first-pass artifact bytes: {summary['first_pass_output_bytes']}\n"
        f"terminal artifact bytes: {artifact_bytes}\n",
        encoding="utf-8")
    terminal_bytes = sum(path.stat().st_size for path in artifact_paths.values() if path.exists())
    return {
        "status": summary["status"], "summary": summary, "root": str(root),
        "source_reads": source_reads, "decoder_calls": decoder_calls,
        "call_records": call_records, "frame_records": frame_records,
        "first_pass_output_bytes": summary["first_pass_output_bytes"],
        "terminal_artifact_bytes": terminal_bytes,
        "artifacts": {name: str(path) for name, path in artifact_paths.items()},
    }


def _select_all(
        source: Mapping[str, Any], outcomes: Mapping[str, Mapping[int, Mapping[str, Any]]],
        call_record_by_key: Mapping[tuple[str, int], dict[str, Any]],
        ) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    values = source["values"]
    call_by_id = source["call_by_id"]
    for pair_id in sorted(source["pair_ids"]):
        pair = source["pair_rows"][pair_id]
        baseline_id = int(pair["baseline"])
        source_candidate = int(pair["candidate"])
        baseline_off = call_by_id[baseline_id]
        branch_ids = sorted(
            (call_id for call_id in source["call_ids_by_pair"][pair_id]
             if str(values["role"][call_by_id[call_id]]) == "soft_prior"),
            key=lambda call_id: int(values["branch"][call_by_id[call_id]]))
        selections: dict[str, tuple[int, int | None, bool]] = {}
        all_score_match = True
        for path in PATHS:
            baseline = outcomes[path][baseline_id]
            if baseline["valid"]:
                chosen_id, chosen_branch = baseline_id, None
            else:
                branch_rows = []
                for branch_id in branch_ids:
                    off = call_by_id[branch_id]
                    outcome = outcomes[path][branch_id]
                    branch_rows.append({
                        "call_index": branch_id,
                        "branch_index": int(values["branch"][off]),
                        "syndrome_valid": bool(outcome["valid"]),
                        "x_hat": outcome["x_hat"],
                    })
                chosen, score_rows = rescue.select_soft_prior_branch(branch_rows, source["prior"])
                score_match_for_pair = True
                score_by_call = {int(row["call_index"]): row for row in score_rows}
                for branch_id in branch_ids:
                    actual_score = score_by_call[branch_id]["score"]
                    expected = source["score_by_call"][branch_id]
                    if (bool(score_by_call[branch_id]["syndrome_valid"]) != expected["syndrome_valid"]
                            or score_by_call[branch_id]["branch_index"] != expected["branch_index"]):
                        score_match_for_pair = False
                    if actual_score is None:
                        score_match = expected["score"] is None
                    else:
                        score_match = expected["score"] is not None and math.isclose(
                            float(actual_score), float(expected["score"]), rel_tol=0.0, abs_tol=1e-12)
                    record = call_record_by_key[(path, branch_id)]
                    record["branch_score_original_prior"] = actual_score
                    record["source_branch_score_original_prior"] = expected["score"]
                    record["branch_score_match"] = bool(score_match)
                    score_match_for_pair &= bool(score_match)
                if chosen is None:
                    chosen_id, chosen_branch = baseline_id, None
                else:
                    chosen_id = int(chosen)
                    chosen_branch = int(values["branch"][call_by_id[chosen_id]])
                all_score_match &= score_match_for_pair
            source_pointer_match = chosen_id == source_candidate
            selections[path] = (chosen_id, chosen_branch, source_pointer_match)
        ref_id, ref_branch, ref_pointer = selections["reference"]
        candidate_id, candidate_branch, candidate_pointer = selections["candidate"]
        frames.append({
            "pair_index": pair_id,
            "graph_id": int(source["pair_graph"][pair_id]),
            "baseline_call_index": baseline_id,
            "source_candidate_call_index": source_candidate,
            "reference_selected_call_index": ref_id,
            "candidate_selected_call_index": candidate_id,
            "reference_selected_branch_index": ref_branch,
            "candidate_selected_branch_index": candidate_branch,
            "reference_pointer_match_source": bool(ref_pointer),
            "candidate_pointer_match_source": bool(candidate_pointer),
            "paths_select_same_call": ref_id == candidate_id,
            "baseline_syndrome_valid": bool(values["valid"][baseline_off]),
            "source_score_match": bool(all_score_match),
            "baseline_exact_reference": None,
            "baseline_exact_candidate": None,
            "selected_exact_reference": None,
            "selected_exact_candidate": None,
            "selected_valid_wrong_reference": None,
            "selected_valid_wrong_candidate": None,
            "raw_branch_valid_wrong_reference": None,
            "raw_branch_valid_wrong_candidate": None,
            "paired_class_reference": None, "paired_class_candidate": None,
        })
    return frames


def _evaluate_truth(
        source: Mapping[str, Any], outcomes: Mapping[str, Mapping[int, Mapping[str, Any]]],
        frames: list[dict[str, Any]], call_record_by_key: Mapping[tuple[str, int], dict[str, Any]],
        ) -> None:
    pair_pos = source["pair_pos"]
    for call_id in source["call_by_id"]:
        off = source["call_by_id"][call_id]
        pair_id = int(source["values"]["pair"][off])
        truth = source["pair_truth"][pair_pos[pair_id]]
        for path in PATHS:
            outcome = outcomes[path][call_id]
            exact = bool(outcome["valid"] and np.array_equal(outcome["x_hat"], truth))
            record = call_record_by_key[(path, call_id)]
            record["exact"] = exact
            record["valid_wrong"] = bool(outcome["valid"] and not exact)
    by_pair = {int(frame["pair_index"]): frame for frame in frames}
    for pair_id, frame in by_pair.items():
        pair = source["pair_rows"][pair_id]
        baseline_id = int(pair["baseline"])
        pair_off = int(pair["offset"])
        truth = source["pair_truth"][source["pair_pos"][pair_id]]
        for path, prefix, selected_id in (
                ("reference", "reference", int(frame["reference_selected_call_index"])),
                ("candidate", "candidate", int(frame["candidate_selected_call_index"]))):
            baseline = outcomes[path][baseline_id]
            selected = outcomes[path][selected_id]
            baseline_exact = bool(baseline["valid"] and np.array_equal(baseline["x_hat"], truth))
            selected_exact = bool(selected["valid"] and np.array_equal(selected["x_hat"], truth))
            frame[f"baseline_exact_{prefix}"] = baseline_exact
            frame[f"selected_exact_{prefix}"] = selected_exact
            frame[f"selected_valid_wrong_{prefix}"] = bool(selected["valid"] and not selected_exact)
            frame[f"paired_class_{prefix}"] = _paired_class(baseline_exact, selected_exact)
            branch_ids = [
                cid for cid in source["call_ids_by_pair"][pair_id]
                if cid in source["branch_calls"]]
            frame[f"raw_branch_valid_wrong_{prefix}"] = sum(
                bool(outcomes[path][cid]["valid"] and
                     not np.array_equal(outcomes[path][cid]["x_hat"], truth))
                for cid in branch_ids)


def _complete_totals(
        source: Mapping[str, Any], outcomes: Mapping[str, Mapping[int, Mapping[str, Any]]],
        frames: Sequence[Mapping[str, Any]], call_record_by_key: Mapping[tuple[str, int], dict[str, Any]],
        source_match_count: int, pair_match_count: int, max_belief_diff: float,
        ) -> dict[str, Any]:
    by_path: dict[str, dict[str, Any]] = {}
    per_graph: dict[str, Any] = {}
    baseline_exact: dict[str, int] = {}
    selected_exact: dict[str, int] = {}
    selected_wrong: dict[str, int] = {}
    raw_wrong: dict[str, int] = {}
    pointers: dict[str, int] = {}
    class_counts: dict[str, dict[str, int]] = {}
    for path in PATHS:
        values = source["values"]
        calls = list(outcomes[path].items())
        role_totals: dict[str, dict[str, float | int]] = {}
        for role in ("baseline", "soft_prior"):
            selected = [(call_id, result) for call_id, result in calls
                        if str(values["role"][source["call_by_id"][call_id]]) == role]
            role_totals[role] = {
                "calls": len(selected),
                "iterations": sum(int(result["iterations"]) for _, result in selected),
                "decoder_runtime_s": sum(float(result["runtime_s"]) for _, result in selected),
                "outer_wall_s": sum(float(result["wall_s"]) for _, result in selected),
            }
        by_path[path] = {
            "calls": len(calls),
            "iterations": sum(int(result["iterations"]) for _, result in calls),
            "decoder_runtime_s": sum(float(result["runtime_s"]) for _, result in calls),
            "outer_wall_s": sum(float(result["wall_s"]) for _, result in calls),
            "by_role": role_totals,
        }
        these = [frame for frame in frames]
        baseline_exact[path] = sum(bool(frame[f"baseline_exact_{path}"]) for frame in these)
        selected_exact[path] = sum(bool(frame[f"selected_exact_{path}"]) for frame in these)
        selected_wrong[path] = sum(bool(frame[f"selected_valid_wrong_{path}"]) for frame in these)
        raw_wrong[path] = sum(int(frame[f"raw_branch_valid_wrong_{path}"]) for frame in these)
        pointer_key = f"{path}_pointer_match_source"
        pointers[path] = sum(bool(frame[pointer_key]) for frame in these)
        class_counts[path] = {
            name: sum(frame[f"paired_class_{path}"] == name for frame in these)
            for name in ("both_exact", "candidate_only_exact", "control_only_exact", "neither_exact")
        }

    for graph in hotspots.GRAPH_IDS:
        graph_frames = [frame for frame in frames if int(frame["graph_id"]) == int(graph)]
        per_graph[str(graph)] = {}
        for path in PATHS:
            role_costs: dict[str, Any] = {}
            for role in ("baseline", "soft_prior"):
                selected_calls = [
                    result for call_id, result in outcomes[path].items()
                    if (int(source["values"]["graph"][source["call_by_id"][call_id]]) == int(graph)
                        and str(source["values"]["role"][source["call_by_id"][call_id]]) == role)
                ]
                role_costs[role] = {
                    "calls": len(selected_calls),
                    "iterations": sum(int(row["iterations"]) for row in selected_calls),
                    "decoder_runtime_s": sum(float(row["runtime_s"]) for row in selected_calls),
                    "outer_wall_s": sum(float(row["wall_s"]) for row in selected_calls),
                }
            baseline = sum(bool(frame[f"baseline_exact_{path}"]) for frame in graph_frames)
            selected = sum(bool(frame[f"selected_exact_{path}"]) for frame in graph_frames)
            per_graph[str(graph)][path] = {
                "pairs": len(graph_frames), "baseline_exact": baseline,
                "selected_exact": selected, "delta_exact": selected - baseline,
                "cost_by_role": role_costs,
                "selected_valid_wrong": sum(bool(frame[f"selected_valid_wrong_{path}"])
                                              for frame in graph_frames),
                "raw_branch_valid_wrong": sum(int(frame[f"raw_branch_valid_wrong_{path}"])
                                               for frame in graph_frames),
            }
    return {
        "baseline_calls_per_path": {path: by_path[path]["by_role"]["baseline"]["calls"]
                                    for path in PATHS},
        "branch_calls_per_path": {path: by_path[path]["by_role"]["soft_prior"]["calls"]
                                  for path in PATHS},
        "iterations_by_path": {path: by_path[path]["iterations"] for path in PATHS},
        "decoder_runtime_s_by_path": {path: by_path[path]["decoder_runtime_s"] for path in PATHS},
        "outer_wall_s_by_path": {path: by_path[path]["outer_wall_s"] for path in PATHS},
        "control_wall_s": by_path["reference"]["by_role"]["baseline"]["outer_wall_s"],
        "candidate_pipeline_wall_s": by_path["candidate"]["outer_wall_s"],
        "candidate_pipeline_to_control_wall_ratio": (
            by_path["candidate"]["outer_wall_s"] /
            by_path["reference"]["by_role"]["baseline"]["outer_wall_s"]
            if by_path["reference"]["by_role"]["baseline"]["outer_wall_s"] > 0.0 else None),
        "paired_observed_wall_s": by_path["reference"]["outer_wall_s"]
        + by_path["candidate"]["outer_wall_s"],
        "timing_by_path": by_path,
        "baseline_exact_by_path": baseline_exact,
        "selected_exact_by_path": selected_exact,
        "delta_exact_by_path": {path: selected_exact[path] - baseline_exact[path] for path in PATHS},
        "selected_valid_wrong_by_path": selected_wrong,
        "raw_branch_valid_wrong_by_path": raw_wrong,
        "selected_pointer_matches_source_by_path": pointers,
        "source_roundtrip_matches": source_match_count,
        "paired_matches": pair_match_count,
        "max_final_belief_abs_diff": max_belief_diff,
        "per_graph": per_graph, "paired_class_counts": class_counts,
        "resource_events": [],
    }


def _bind_production(repo_root: str | Path | None = None) -> dict[str, Any]:
    from comparison_bench.formal_ir import (
        nbldpc_gf32_batched_check as batched_check,
        v35_algorithm_development as v35,
    )

    def reference_decoder(h, prior, syndrome, *, max_iter, damping_alpha, warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha,
            warm_beliefs=warm_beliefs, field=field)

    def candidate_decoder(h, prior, syndrome, *, max_iter, damping_alpha, warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha,
            warm_beliefs=warm_beliefs, field=field,
            check_update_fn=batched_check.batched_check_update_log_batch)

    return {"source_reader": _source_reader(repo_root),
            "reference_decoder": reference_decoder,
            "candidate_decoder": candidate_decoder}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Complete saved GF(32) soft-prior efficiency replay")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0(out_root=args.out_root)
    elif args.dry_run:
        result = dry_run(out_root=args.out_root)
    else:
        # Check absence before importing/binding the production decoder.
        _preflight_root(args.out_root)
        result = execute_batch(**_bind_production(), out_root=args.out_root, command=COMMAND)
    printable = result.get("summary", result)
    print(json.dumps(printable, sort_keys=True, default=_json_default))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "FULL_SOFTPRIOR_IMPLEMENTATION_MATCH") else 2


if __name__ == "__main__":
    raise SystemExit(main())
