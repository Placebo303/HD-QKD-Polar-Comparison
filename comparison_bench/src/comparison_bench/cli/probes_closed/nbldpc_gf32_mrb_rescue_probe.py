"""Bounded GF(32) MRB rescue EXPLORE probe.

The runner reuses the accepted deep-graph, PMF, seed, pairing and admission
helpers. Its only scientific delta is a bounded order-0/1 MRB postprocessor
for candidate-arm BP outputs that fail an independently recomputed syndrome.
Import and dry-run paths never bind or invoke the production decoder/OSD.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_damping_probe as prior_runner
from comparison_bench.cli.probes_closed import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import nonbinary_field
from comparison_bench.formal_ir import nonbinary_v19_osd
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-MRB-RESCUE-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "ebbbe5c2-f53f-4b92-a2ff-3eca358002de"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_mrb_rescue_ebbbe5c2"
SEED_PREFIX = "gf32-mrb-rescue-v1"
MAX_CANDIDATES = 256
MAX_ITER = 90
DAMPING_ALPHA = 1.0
WARM_BELIEFS = None
FIELD = None
N = prior_runner.N
M = prior_runner.M
EDGE_COUNT = prior_runner.EDGE_COUNT
GRAPH_SEEDS = prior_runner.GRAPH_SEEDS
VAR_COUNTS = prior_runner.VAR_COUNTS
CHECK_COUNTS = prior_runner.CHECK_COUNTS
SHAPE_COUNTS = prior_runner.SHAPE_COUNTS
SHAPE_TOTAL = prior_runner.SHAPE_TOTAL
P0 = prior_runner.P0
HOLDOUT_STREAMS = prior_runner.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = prior_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = prior_runner.HOLDOUT_PAIRS
MAX_CALLS = 2 * HOLDOUT_PAIRS
WALL_CAP_S = prior_runner.WALL_CAP_S
CALL_CAP_S = prior_runner.CALL_CAP_S
RSS_CAP_BYTES = prior_runner.RSS_CAP_BYTES
SYNDROME_BITS = prior_runner.SYNDROME_BITS
SIGNAL_DELTA = prior_runner.SIGNAL_DELTA
SIGNAL_POSITIVE_GRAPHS = prior_runner.SIGNAL_POSITIVE_GRAPHS
CONTROL_MIN = prior_runner.CONTROL_MIN
CONTROL_MAX = prior_runner.CONTROL_MAX
FRAME_FIELDS = tuple(search_runner.FRAME_FIELDS) + (
    "decoder_branch", "damping_alpha", "max_iter",
    "raw_status", "raw_iterations", "raw_syndrome_ok_reported",
    "raw_syndrome_accept", "belief_provenance", "rescue_attempted",
    "rescue_status", "candidate_count", "selected_prior_score",
    "rescue_wall_s", "mrb_helper_wall_s", "bp_runtime_s",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_mrb_rescue_probe "
    "--execute --out-root workspace/gf32_mrb_rescue_ebbbe5c2"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def holdout_seed(graph_seed: int, stream: int, frame: int,
                 seed_namespace: str | None = None) -> int:
    namespace = SEED_PREFIX if seed_namespace is None else str(seed_namespace)
    return int(common.v10_seed(
        "%s:holdout:%d:%d:%d"
        % (namespace, int(graph_seed), int(stream), int(frame))))


def seed_plan(seed_namespace: str | None = None
              ) -> list[tuple[int, int, int, int]]:
    return [
        (graph_seed, stream, frame,
         holdout_seed(graph_seed, stream, frame, seed_namespace))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def arm_order(frame: int) -> tuple[str, str]:
    return prior_runner.arm_order(frame)


def shape_pmf_grid() -> list[dict[str, Any]]:
    return prior_runner.shape_pmf_grid()


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None,
                      batch_context: Mapping[str, Any] | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected_relative = (OUT_ROOT_RELATIVE if batch_context is None else
                         Path(str(batch_context["out_root_relative"])))
    expected = (root / expected_relative).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen fresh root %s" % expected)
    if resolved.exists():
        raise FileExistsError("refusing existing output root %s" % resolved)
    return resolved


def _prior_seed_sets() -> list[set[int]]:
    old_plans = (
        prior_runner.prior_runner._seed_plan(),
        search_runner.fine_runner.predecessor.seed_plan(),
        search_runner.fine_runner.seed_plan(),
        search_runner.replica_runner.seed_plan(),
        search_runner.seed_plan(),
        prior_runner.seed_plan(),
    )
    sets = []
    for plan in old_plans:
        sets.append({int(row[3]) for rows in plan for row in rows})
    return sets


def _validate_seed_plan(seed_namespace: str | None = None
                        ) -> list[tuple[int, int, int, int]]:
    holdouts = seed_plan(seed_namespace)
    seeds = [row[3] for row in holdouts]
    if len(holdouts) != HOLDOUT_PAIRS or len(set(seeds)) != len(seeds):
        raise AssertionError("MRB seed plan is incomplete or duplicated")
    for old in _prior_seed_sets():
        if set(seeds) & old:
            raise AssertionError("MRB seed namespace overlaps a prior batch")
    return holdouts


def _effective_log_prior(prior: Any) -> np.ndarray:
    """Use the v35 input-prior floor, row normalization and log exactly."""
    values = np.asarray(prior, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 32:
        raise ValueError("prior must have shape (n, 32)")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("prior must be finite and non-negative")
    cleaned = np.maximum(values, 1e-15)
    sums = cleaned.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(sums)) or np.any(sums <= 0.0):
        raise ValueError("prior rows must have a finite positive sum")
    cleaned /= sums
    return np.log(cleaned)


def _syndrome_ok(h: Any, vector: Any, syndrome: Any) -> bool:
    return bool(prior_runner.prior_runner.layout.syndrome_ok(
        np.asarray(h, dtype=np.int64), np.asarray(vector, dtype=np.int64),
        np.asarray(syndrome, dtype=np.int64)))


def _candidate_vectors(raw: Any, h: Any, prior: Any, syndrome: Any, *,
                       now: Callable[[], float],
                       rss_fn: Callable[[], int | None],
                       started: float,
                       arm_started: float,
                       mrb_fn: Callable[..., Any] | None = None,
                       field: Any = None
                       ) -> tuple[Any, dict[str, Any], str]:
    """Return an immutable selected result and rescue metadata, never truth."""
    raw_x = np.asarray(raw.x_hat, dtype=np.int64).ravel()
    h_array = np.asarray(h, dtype=np.int64)
    syn = np.asarray(syndrome, dtype=np.int64).ravel()
    if raw_x.shape != (N,) or np.any(raw_x < 0) or np.any(raw_x >= 32):
        return raw, {"raw_syndrome_accept": False,
                     "raw_syndrome_ok_reported": None,
                     "rescue_attempted": False, "rescue_status": "raw_output_invalid",
                     "candidate_count": None, "selected_prior_score": None,
                     "rescue_wall_s": 0.0, "mrb_helper_wall_s": 0.0}, \
            "integrity_error:raw_decoder_output_invalid"
    raw_accept = _syndrome_ok(h_array, raw_x, syn)
    raw_reported = bool(raw.syndrome_ok)
    metadata = {
        "raw_syndrome_accept": raw_accept,
        "raw_syndrome_ok_reported": raw_reported,
        "rescue_attempted": False,
        "rescue_status": "not_needed",
        "candidate_count": 0,
        "selected_prior_score": None,
        "rescue_wall_s": 0.0,
        "mrb_helper_wall_s": 0.0,
    }
    if raw_accept:
        return raw, metadata, ""

    metadata["rescue_attempted"] = True
    rescue_start = float(now())

    def finish_rescue(result: Any, issue: str
                      ) -> tuple[Any, dict[str, Any], str]:
        metadata["rescue_wall_s"] = max(float(now()) - rescue_start, 0.0)
        return result, metadata, issue

    rss_before = rss_fn()
    before_reasons = _resource_reasons(
        started=started, now=now, rss_value=rss_before,
        call_wall=max(float(now()) - float(arm_started), 0.0))
    if before_reasons:
        metadata["rescue_status"] = "resource_stop_before_mrb"
        return finish_rescue(
            raw, "resource_abort:" + ",".join(before_reasons))

    try:
        if field is None:
            field = nonbinary_field.GF2mField.create(32)
        if mrb_fn is None:
            mrb_fn = nonbinary_v19_osd.osd_decode_candidates_mrb
        beliefs = np.asarray(raw.final_beliefs, dtype=np.float64)
        if beliefs.shape != (N, 32) or not np.all(np.isfinite(beliefs)):
            raise ValueError("raw final_beliefs must be finite shape (128,32)")
        log_prior = _effective_log_prior(prior)
        if log_prior.shape != (N, 32):
            raise ValueError("effective prior shape does not match the frozen graph")
    except Exception as exc:
        metadata["rescue_status"] = "integrity_error:rescue_input:%s" % type(exc).__name__
        return finish_rescue(
            raw, "integrity_error:rescue_input:%s:%s" % (
                type(exc).__name__, str(exc)))

    helper_started = float(now())
    helper_rss_before = rss_fn()
    helper_pre_reasons = _resource_reasons(
        started=started, now=now, rss_value=helper_rss_before,
        call_wall=max(float(now()) - float(arm_started), 0.0))
    if helper_pre_reasons:
        metadata["rescue_status"] = "resource_stop_before_mrb"
        return finish_rescue(
            raw, "resource_abort:" + ",".join(helper_pre_reasons))

    candidates: Any = None
    helper_exception: Exception | None = None
    try:
        candidates = mrb_fn(
            field=field, matrix=h_array, syndrome=syn, beliefs=beliefs,
            e_hat=raw_x, order=1, top_info=None, top_symbols=None,
            max_candidates=MAX_CANDIDATES)
    except Exception as exc:  # retain the attempted rescue and stop
        helper_exception = exc
    helper_wall = max(float(now()) - helper_started, 0.0)
    helper_rss_after = rss_fn()
    metadata["mrb_helper_wall_s"] = helper_wall
    helper_resource = _resource_reasons(
        started=started, now=now, rss_value=helper_rss_after,
        call_wall=max(float(now()) - float(arm_started), 0.0))
    if helper_exception is not None:
        metadata["rescue_status"] = "integrity_error:mrb_exception:%s" % type(helper_exception).__name__
        issue = "integrity_error:mrb_exception:%s:%s" % (
            type(helper_exception).__name__, str(helper_exception))
        if helper_resource:
            issue += "|resource_abort:" + ",".join(helper_resource)
        return finish_rescue(raw, issue)
    if helper_resource:
        metadata["rescue_status"] = "resource_stop_after_mrb"
        return finish_rescue(
            raw, "resource_abort:" + ",".join(helper_resource))

    if not isinstance(candidates, (list, tuple)):
        metadata["rescue_status"] = "integrity_error:mrb_output_type"
        return finish_rescue(raw, "integrity_error:mrb_output_type")
    metadata["candidate_count"] = len(candidates)
    if len(candidates) > MAX_CANDIDATES:
        metadata["rescue_status"] = "integrity_error:candidate_cap_exceeded"
        return finish_rescue(raw, "integrity_error:candidate_cap_exceeded")
    if not candidates:
        metadata["rescue_status"] = "empty_candidate_list_raw_retained"
        return finish_rescue(raw, "")

    scored: list[tuple[float, tuple[int, ...]]] = []
    for candidate in candidates:
        try:
            vector = np.asarray(candidate, dtype=np.int64).ravel()
            if vector.shape != (N,) or np.any(vector < 0) or np.any(vector >= 32):
                raise ValueError("candidate must be a GF32 vector of length 128")
            if not _syndrome_ok(h_array, vector, syn):
                raise ValueError("candidate failed original H*x=s check")
            score = math.fsum(
                float(log_prior[index, int(symbol)])
                for index, symbol in enumerate(vector))
            scored.append((score, tuple(int(x) for x in vector)))
        except Exception as exc:
            metadata["rescue_status"] = "integrity_error:invalid_candidate"
            return finish_rescue(
                raw, "integrity_error:invalid_candidate:%s:%s" % (
                    type(exc).__name__, str(exc)))

    best_score = max(score for score, _ in scored)
    best_vector = min(vector for score, vector in scored if score == best_score)
    if not _syndrome_ok(h_array, best_vector, syn):
        metadata["rescue_status"] = "integrity_error:selected_syndrome"
        return finish_rescue(
            raw, "integrity_error:selected_candidate_failed_syndrome")
    metadata["rescue_status"] = "rescued"
    metadata["selected_prior_score"] = float(best_score)
    selected = replace(
        raw, x_hat=np.asarray(best_vector, dtype=np.uint8), syndrome_ok=True,
        status="mrb_rescued_order1")
    return finish_rescue(selected, "")


def _resource_reasons(*, started: float, now: Callable[[], float],
                      rss_value: int | None,
                      call_wall: float | None = None) -> list[str]:
    reasons: list[str] = []
    if call_wall is not None and float(call_wall) >= CALL_CAP_S:
        reasons.append("decoder_call_wall_cap_after_return")
    if max(float(now()) - float(started), 0.0) >= WALL_CAP_S:
        reasons.append("total_wall_cap_after_call")
    if rss_value is not None and int(rss_value) >= RSS_CAP_BYTES:
        reasons.append("rss_cap_after_call")
    return reasons


def verify_t0(batch_context: Mapping[str, Any] | None = None) -> dict[str, bool]:
    """Pure field/PMF/seed checks; no graph, decoder, OSD or file access."""
    checks = prior_runner.verify_t0()
    pmf = np.asarray(shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    if pmf.shape != (32,) or np.flatnonzero(pmf).tolist() != [0, 1, 3, 7, 15, 31]:
        raise AssertionError("MRB probe source PMF support changed")
    if not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12):
        raise AssertionError("MRB probe source PMF is not normalized")
    field = nonbinary_field.GF2mField.create(32)
    if field.primitive_polynomial != 37 or field.q != 32:
        raise AssertionError("MRB probe field is not the frozen GF32 polynomial-37")
    if MAX_CANDIDATES != 256 or MAX_ITER != 90 or DAMPING_ALPHA != 1.0:
        raise AssertionError("MRB cap/decoder parameters changed")
    seed_namespace = (None if batch_context is None else
                      str(batch_context["seed_namespace"]))
    if len(_validate_seed_plan(seed_namespace)) != HOLDOUT_PAIRS or MAX_CALLS != 384:
        raise AssertionError("MRB paired seed plan or call budget changed")
    checks["mrb_gf32_field_source_seed_and_caps"] = True
    return checks


def _serialized_pmf() -> dict[str, Any]:
    return {key: value for key, value in shape_pmf_grid()[0].items()
            if key != "pmf"}


def _initial_manifest(command: str,
                      batch_context: Mapping[str, Any] | None = None,
                      mrb_fns_by_arm: Mapping[str, Callable[..., Any]] | None = None
                      ) -> dict[str, Any]:
    seed_namespace = (SEED_PREFIX if batch_context is None else
                      str(batch_context["seed_namespace"]))
    batch_uuid = (BATCH_UUID if batch_context is None else
                  str(batch_context["batch_uuid"]))
    contract = CONTRACT if batch_context is None else str(batch_context["contract"])
    holdouts = _validate_seed_plan(None if batch_context is None else seed_namespace)
    max_mrb_invocations = HOLDOUT_PAIRS * (
        1 if mrb_fns_by_arm is None else len(mrb_fns_by_arm))
    manifest = {
        "track": "EXPLORE", "batch_uuid": batch_uuid,
        "contract": contract, "status": "RUNNING",
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "variable_degrees": VAR_COUNTS,
            "check_degrees": CHECK_COUNTS,
            "field": "GF(32)/polynomial-37",
            "graph_seeds": list(GRAPH_SEEDS),
            "cross_batch_baseline": False,
            "matrix_source": (
                "accepted SEARCH-DEPTH deep H0D reconstruction; one common "
                "matrix per paired arms"),
        },
        "source_shape_proxy": {
            "source": "accepted historical 2M aggregate summary only",
            "counts": {str(e): count for e, count in SHAPE_COUNTS},
            "total": SHAPE_TOTAL,
            "role": "synthetic iid marginal shape proxy",
            "not_conditional_channel_reconstruction": True,
            "no_empirical_input_reads": True,
        },
        "pmf": _serialized_pmf(), "fixed_p0": P0,
        "pilot": "NOT_RUN_FIXED_PMF", "seed_namespace": seed_namespace,
        "seed_plan_counts": {"pilot": 0, "holdout_pairs": len(holdouts)},
        "seed_plan_disjoint_from_prior_batches": True,
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "schedule": "row_layered", "max_iter": MAX_ITER,
            "damping_alpha": DAMPING_ALPHA,
            "warm_beliefs": WARM_BELIEFS, "field": FIELD,
            "same_bp_decoder_both_arms": True,
            "candidate_postprocessor": (
                "nonbinary_v19_osd.osd_decode_candidates_mrb; order=1; "
                "max_candidates=256 including OSD0 base"),
        },
        "rescue_contract": {
            "trigger": (
                "each arm's raw BP fails independently recomputed H*x=s"
                if mrb_fns_by_arm is not None else
                "candidate arm only, raw BP fails independently recomputed H*x=s"),
            "syndrome_argument": "original syndrome; solve H*x=s, not residual",
            "effective_prior_score": (
                "floor probability at 1e-15, row normalize, log, then math.fsum"),
            "tie_break": "highest score; exact tie chooses lexicographically smallest original-coordinate vector",
            "truth_or_exact_access_during_selection": False,
            "candidate_cap": MAX_CANDIDATES,
        },
        "pairing": (
            "same immutable deep H0D, sampled iid error, repeated prior and "
            "resulting syndrome within each pair"),
        "arm_order": "control first on even frame, candidate first on odd",
        "frame_stream": (
            "v10_seed('%s:holdout:{graph_seed}:{stream}:{frame}')" % seed_namespace),
        "error_sampling": "numpy.default_rng(seed).choice(32,size=128,p=pmf)",
        "budgets": {
            "total_wall_s": WALL_CAP_S,
            "per_synchronous_bp_plus_rescue_arm_s": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES,
            "pilot_calls": 0,
            "max_holdout_calls": MAX_CALLS,
            "max_mrb_invocations": max_mrb_invocations,
            "max_candidates_per_mrb_invocation": MAX_CANDIDATES,
        },
        "resource_measurement": {
            "batch_wall_s": "measured with time.perf_counter",
            "max_call_wall_s": "measured around synchronous BP plus candidate rescue",
            "max_rss_bytes": (
                "sampled process high-water RSS via accepted d5 helper; "
                "Windows fallback is current process working set"),
            "mrb_rss_sampling": "before and after every rescue invocation, including exceptions",
        },
        "accounting": {
            "syndrome_bits_per_attempt": SYNDROME_BITS,
            "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
            "undetected_status": "NOT_MEASURED",
            "success": "exact AND independently recomputed syndrome_accept",
            "wrong": "syndrome_accept AND NOT exact; separately recorded failure",
            "truth_prior_and_conditional_arrays_saved": False,
        },
        "exact_command": command or COMMAND,
        "attempted_decoder_calls": 0,
        "attempted_call_counts": {"pilot": 0, "holdout": 0, "total": 0},
        "stop_reason": "", "graph_diagnostics": [],
        "candidate_diagnostics": [], "dirty_tree_reference_uuid": batch_uuid,
    }
    if batch_context is not None:
        manifest.update({
            "batch_title": str(batch_context["title"]),
            "source_batch_uuid": str(batch_context["source_batch_uuid"]),
            "reaggregation_uuid": str(batch_context["reaggregation_uuid"]),
            "arm_metadata": dict(batch_context["arm_metadata"]),
            "top_symbols_by_arm": {
                arm: dict(metadata)["top_symbols"]
                for arm, metadata in batch_context["arm_metadata"].items()},
        })
    return manifest


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("- %s\n" % message)


def _start_outputs(root: Path, manifest: dict[str, Any],
                   batch_context: Mapping[str, Any] | None = None,
                   frame_fields: tuple[str, ...] | None = None) -> None:
    fields = FRAME_FIELDS if frame_fields is None else frame_fields
    root.mkdir(parents=False, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields).writeheader()
    _write_json(root / "summary.json", {"status": "RUNNING"})
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        title = ("GF32 bounded MRB rescue EXPLORE" if batch_context is None
                 else str(batch_context["title"]))
        batch_uuid = (BATCH_UUID if batch_context is None
                      else str(batch_context["batch_uuid"]))
        stream.write("# %s log\n\n" % title)
        stream.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                     % batch_uuid)
        if batch_context is not None:
            stream.write("Contract: `%s`; seed namespace: `%s`; source batch: `%s`; "
                         "reaggregation: `%s`.\n"
                         % (batch_context["contract"], batch_context["seed_namespace"],
                            batch_context["source_batch_uuid"],
                            batch_context["reaggregation_uuid"]))
            arms = batch_context["arm_metadata"]
            stream.write("Arm enum: control top_symbols=%s; candidate top_symbols=%s.\n"
                         % (arms["control"]["top_symbols"],
                            arms["candidate"]["top_symbols"]))


def _append_row(root: Path, row: Mapping[str, Any],
                frame_fields: tuple[str, ...] | None = None) -> None:
    fields = FRAME_FIELDS if frame_fields is None else frame_fields
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields).writerow(
            {field: row.get(field) for field in fields})
    _append_log(
        root,
        "call=%s %s/%s graph=%s stream=%s frame=%s exact=%s syn=%s "
        "raw_syn=%s rescue=%s candidates=%s score=%s status=%s "
        "top_symbols=%s wall_s=%s rss_b=%s"
        % (row["call_index"], row["phase"], row["arm"], row["graph_seed"],
           row["stream"], row["frame"], row["exact"], row["syndrome_accept"],
           row.get("raw_syndrome_accept"), row.get("rescue_status"),
           row.get("candidate_count"), row.get("selected_prior_score"),
           row["status"], row.get("top_symbols"), row["wall_s"], row["rss_b"]))


def _summarize(rows: list[dict[str, Any]],
               completed_pairs: list[dict[str, Any]],
               stop_reason: str) -> dict[str, Any]:
    summary = prior_runner._summarize(rows, completed_pairs, stop_reason)
    candidate_rows = [row for row in rows if row.get("arm") == "candidate"]
    rescues = [row for row in candidate_rows if row.get("rescue_attempted")]
    successful = [row for row in rescues if row.get("rescue_status") == "rescued"]
    selected_scores = [float(row["selected_prior_score"]) for row in successful
                       if row.get("selected_prior_score") is not None]
    summary.update({
        # The delegated damping summary supplies the common observation
        # aggregation, but its batch identity belongs to the damping probe.
        # Override all three identity fields before persisting an MRB summary.
        "batch_uuid": BATCH_UUID,
        "contract": CONTRACT,
        "seed_namespace": SEED_PREFIX,
        "rescue_attempts": len(rescues),
        "rescues_selected": len(successful),
        "empty_candidate_lists": sum(
            row.get("rescue_status") == "empty_candidate_list_raw_retained"
            for row in rescues),
        "candidate_vectors_examined": sum(
            int(row["candidate_count"] or 0) for row in rescues
            if row.get("candidate_count") is not None),
        "selected_prior_score_count": len(selected_scores),
        "selected_prior_score_min": min(selected_scores) if selected_scores else None,
        "selected_prior_score_max": max(selected_scores) if selected_scores else None,
        "selected_prior_scores": selected_scores,
        "rescue_wall_s_total": float(sum(
            float(row.get("rescue_wall_s") or 0.0) for row in rescues)),
        "bp_runtime_s_by_arm": {
            arm: float(sum(float(row.get("bp_runtime_s") or 0.0)
                           for row in rows if row.get("arm") == arm))
            for arm in ("control", "candidate")},
        "raw_syndrome_failures": sum(
            row.get("raw_syndrome_accept") is False for row in rows),
        "claim_ceiling": (
            "bounded order-0/1 MRB syndrome rescue versus raw BP on six fixed "
            "deep H0D graphs under a synthetic iid marginal-shape proxy; no "
            "cross-batch pooling, conditional channel, FER, f_eff, SKR, "
            "throughput, qualification, publication, or route claim"),
    })
    return summary


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "writes": 0, "empirical_input_reads": 0,
        "graph_construction_calls": 0, "candidate_construction_calls": 0,
        "decoder_calls": 0, "mrb_calls": 0, "artifact_reads": 0,
        "t0": t0, "fixed_p0": P0,
        "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA,
        "max_candidates_per_rescue": MAX_CANDIDATES,
        "pilot_calls": 0, "holdout_pair_count": HOLDOUT_PAIRS,
        "holdout_call_count": MAX_CALLS,
        "mrb_invocation_ceiling": HOLDOUT_PAIRS,
        "holdout_seeds_disjoint_from_prior_batches": True,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT},
    }


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None], calls: int) -> str:
    if int(calls) >= MAX_CALLS:
        return "decoder_call_count_cap_before_next_call"
    if max(float(now()) - float(started), 0.0) >= WALL_CAP_S:
        return "total_wall_cap_before_next_call"
    rss = rss_fn()
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_call"
    return ""


def _record_row(*, call_index: int, graph_seed: int, stream: int,
                frame: int, seed: int, arm: str,
                observed: Mapping[str, Any]) -> dict[str, Any]:
    row = search_runner.fine_runner.predecessor._record_row(
        call_index=call_index, phase="holdout", pmf=shape_pmf_grid()[0],
        graph_seed=graph_seed, stream=stream, frame=frame, seed=seed,
        arm=arm, observed=observed)
    row.update({"decoder_branch": arm, "damping_alpha": DAMPING_ALPHA,
                "max_iter": MAX_ITER})
    for field in FRAME_FIELDS:
        row.setdefault(field, None)
    return row


def execute_batch(*, out_root: str | Path, decode_fn: Callable[..., Any],
                  graph_builder: Callable[[int], Mapping[str, Any]],
                  candidate_builder: Callable[[np.ndarray, np.ndarray, int],
                                              tuple[np.ndarray | None, np.ndarray | None,
                                                    dict[str, Any]]] | None = None,
                  mrb_fn: Callable[..., Any] | None = None,
                  mrb_fns_by_arm: Mapping[str, Callable[..., Any]] | None = None,
                  batch_context: Mapping[str, Any] | None = None,
                  summary_fn: Callable[[list[dict[str, Any]],
                                       list[dict[str, Any]], str],
                                       dict[str, Any]] | None = None,
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None) -> dict[str, Any]:
    """Execute only with explicit decoder and graph callbacks (fake in tests)."""
    if not callable(decode_fn):
        raise ValueError("an explicit decoder callback is required")
    if not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    if mrb_fns_by_arm is not None:
        if mrb_fn is not None:
            raise ValueError("mrb_fn and mrb_fns_by_arm are mutually exclusive")
        if set(mrb_fns_by_arm) != {"control", "candidate"} or not all(
                callable(mrb_fns_by_arm[arm]) for arm in ("control", "candidate")):
            raise ValueError("mrb_fns_by_arm must contain control and candidate callables")
        mrb_fns_by_arm = dict(mrb_fns_by_arm)
    if batch_context is not None:
        required_context = {
            "batch_uuid", "contract", "out_root_relative", "seed_namespace",
            "title", "source_batch_uuid", "reaggregation_uuid", "arm_metadata",
        }
        if not required_context.issubset(batch_context):
            raise ValueError("batch_context is missing required identity fields")
        arm_metadata = batch_context["arm_metadata"]
        arm_metadata_valid = (
            isinstance(arm_metadata, Mapping)
            and set(arm_metadata) == {"control", "candidate"}
            and all(isinstance(arm_metadata[arm], Mapping)
                    and set(arm_metadata[arm]) == {"top_symbols"}
                    for arm in ("control", "candidate"))
            and arm_metadata["control"]["top_symbols"] is None
            and arm_metadata["candidate"]["top_symbols"] == 6)
        if not arm_metadata_valid:
            raise ValueError("batch_context arm_metadata must freeze None versus top_symbols=6")
        if mrb_fns_by_arm is None or summary_fn is None:
            raise ValueError("batch_context requires explicit two-arm MRB and summary callbacks")
    elif mrb_fns_by_arm is not None:
        raise ValueError("mrb_fns_by_arm requires its frozen batch_context")
    build_candidates = candidate_builder or search_runner._candidate_pair_for_graph
    root = validate_out_root(out_root, repo_root=repo_root,
                             batch_context=batch_context)
    seed_namespace = None if batch_context is None else str(batch_context["seed_namespace"])
    frame_fields = FRAME_FIELDS + ("top_symbols",) if batch_context is not None else FRAME_FIELDS
    if rss_fn is None:
        rss_fn = d5._rss_bytes

    started = float(now())
    rss_samples: list[int] = []

    def sample_rss() -> int | None:
        value = rss_fn()
        if value is not None:
            rss_samples.append(int(value))
        return value

    sample_rss()
    manifest = _initial_manifest(command, batch_context, mrb_fns_by_arm)
    _start_outputs(root, manifest, batch_context, frame_fields)
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    graphs: dict[int, np.ndarray] = {}
    deep_matrices: dict[int, np.ndarray] = {}
    calls = 0
    rescue_field = nonbinary_field.GF2mField.create(32)
    stop_reason = ""
    terminal = "INCOMPLETE"

    def measured_cost() -> dict[str, Any]:
        return {
            "batch_wall_s": max(float(now()) - started, 0.0),
            "max_call_wall_s": max(
                (float(row["wall_s"]) for row in rows), default=None),
            "max_rss_bytes": max(rss_samples) if rss_samples else None,
            "rss_sample_count": len(rss_samples),
        }

    def finish() -> dict[str, Any]:
        sample_rss()
        cost = measured_cost()
        summarize = _summarize if summary_fn is None else summary_fn
        summary = summarize(rows, completed_pairs, stop_reason)
        summary.update({
            "terminal_status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": {
                "pilot": 0, "holdout": len(rows), "total": calls},
            "attempted_frame_rows": len(rows),
            "resource_measurement": {
                "batch_wall_s": cost["batch_wall_s"],
                "max_call_wall_s": cost["max_call_wall_s"],
                "max_rss_bytes": cost["max_rss_bytes"],
                "rss_sample_count": cost["rss_sample_count"],
                "rss_scope": (
                    "process high-water RSS from d5._rss_bytes; Windows "
                    "fallback reports current process working set"),
            },
        })
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal, "attempted_decoder_calls": calls,
            "attempted_call_counts": summary["attempted_call_counts"],
            "attempted_frame_rows": len(rows), "stop_reason": stop_reason,
            "resource_measurement": summary["resource_measurement"],
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
            "rescue_attempts": summary["rescue_attempts"],
            "rescues_selected": summary["rescues_selected"],
            "candidate_vectors_examined": summary["candidate_vectors_examined"],
        })
        if "rescue_metrics_by_arm" in summary:
            manifest["rescue_metrics_by_arm"] = summary["rescue_metrics_by_arm"]
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s calls=%d rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def dispatch(graph_seed: int, stream: int, frame: int, seed: int,
                 arm: str, dense: np.ndarray, prior: np.ndarray,
                 truth: np.ndarray, syndrome: np.ndarray
                 ) -> tuple[dict[str, Any] | None, str]:
        nonlocal calls
        resource = _resource_stop(started, now, sample_rss, calls)
        if resource:
            return None, resource
        calls += 1
        arm_started = float(now())
        rss_before = sample_rss()
        meta = {
            "raw_status": None, "raw_iterations": None,
            "raw_syndrome_ok_reported": None, "raw_syndrome_accept": None,
            "belief_provenance": None, "rescue_attempted": False,
            "rescue_status": (
                "not_started" if (mrb_fns_by_arm is not None or arm == "candidate")
                else "not_candidate_arm"),
            "candidate_count": (
                None if (mrb_fns_by_arm is not None or arm == "candidate") else 0),
            "selected_prior_score": None, "rescue_wall_s": 0.0,
            "mrb_helper_wall_s": 0.0, "bp_runtime_s": None,
        }
        decode_issue = ""
        estimate: np.ndarray | None = None
        reported_final_syn = False
        iterations = 0
        status = ""
        try:
            raw = decode_fn(dense, prior, syndrome)
            meta["raw_status"] = str(raw.status)
            meta["raw_iterations"] = int(raw.iterations)
            meta["raw_syndrome_ok_reported"] = bool(raw.syndrome_ok)
            meta["belief_provenance"] = getattr(raw, "belief_provenance", None)
            runtime = getattr(raw, "runtime_s", None)
            meta["bp_runtime_s"] = None if runtime is None else float(runtime)
            raw_x = np.asarray(raw.x_hat, dtype=np.int64).ravel()
            if raw_x.shape != (N,) or np.any(raw_x < 0) or np.any(raw_x >= 32):
                raise ValueError("raw v35 x_hat must be a GF32 vector of length 128")
            meta["raw_syndrome_accept"] = _syndrome_ok(dense, raw_x, syndrome)
            final = raw
            rescue_enabled = (arm in mrb_fns_by_arm if mrb_fns_by_arm is not None
                              else arm == "candidate")
            selected_mrb_fn = (mrb_fns_by_arm[arm] if mrb_fns_by_arm is not None
                               else mrb_fn)
            if rescue_enabled and not meta["raw_syndrome_accept"]:
                final, rescue_meta, decode_issue = _candidate_vectors(
                    raw, dense, prior, syndrome, now=now, rss_fn=sample_rss,
                    started=started, arm_started=arm_started,
                    mrb_fn=selected_mrb_fn, field=rescue_field)
                meta.update(rescue_meta)
            elif rescue_enabled:
                meta["rescue_status"] = "not_needed_raw_syndrome_pass"
                meta["candidate_count"] = 0
            if (meta["raw_syndrome_accept"] !=
                    meta["raw_syndrome_ok_reported"]):
                decode_issue = ";".join(x for x in (
                    decode_issue, "integrity_error:raw_syndrome_flag_mismatch") if x)
            estimate = np.asarray(final.x_hat, dtype=np.int64).ravel()
            if estimate.shape != (N,) or np.any(estimate < 0) or np.any(estimate >= 32):
                raise ValueError("final x_hat must be a GF32 vector of length 128")
            iterations = int(final.iterations)
            status = str(final.status)
            reported_final_syn = bool(final.syndrome_ok)
        except Exception as exc:
            status = "decoder_exception:%s:%s" % (type(exc).__name__, str(exc))
            decode_issue = decode_issue or "decoder_exception"
        arm_wall = max(float(now()) - arm_started, 0.0)
        rss_after = sample_rss()
        final_syn = bool(estimate is not None and _syndrome_ok(dense, estimate, syndrome))
        if estimate is not None and final_syn != reported_final_syn:
            decode_issue = ";".join(x for x in (
                decode_issue, "integrity_error:final_syndrome_flag_mismatch") if x)
            status = "integrity_error:final_syndrome_flag_mismatch"
        if not 0 <= iterations <= MAX_ITER:
            decode_issue = ";".join(x for x in (
                decode_issue, "integrity_error:iteration_count_out_of_range") if x)
            status = "integrity_error:iteration_count_out_of_range"
        resource_reasons = _resource_reasons(
            started=started, now=now,
            rss_value=rss_after, call_wall=arm_wall)
        if resource_reasons:
            status += "|resource_abort:" + ",".join(resource_reasons)
            decode_issue = ";".join(x for x in (
                decode_issue, *resource_reasons) if x)
        elif "resource_abort" in decode_issue:
            status += "|resource_abort:pre_rescue_guard"
        if "integrity_error" in decode_issue:
            status = "integrity_error:" + decode_issue.split("integrity_error:", 1)[1]
        exact = bool(estimate is not None and np.array_equal(estimate, truth))
        observed = {
            "exact": exact, "syndrome_accept": final_syn,
            "syndrome_consistent_wrong": bool(final_syn and not exact),
            "status": status, "iterations": iterations,
            "wall_s": arm_wall, "rss_b": rss_after,
        }
        row = _record_row(
            call_index=calls, graph_seed=graph_seed, stream=stream,
            frame=frame, seed=seed, arm=arm, observed=observed)
        row.update(meta)
        if batch_context is not None:
            row.update(dict(batch_context["arm_metadata"][arm]))
        rows.append(row)
        _append_row(root, row, frame_fields)
        return row, decode_issue

    try:
        _append_log(root, "T0 started; no graph, decoder or OSD call has occurred")
        try:
            t0 = verify_t0(batch_context)
        except Exception as exc:
            stop_reason = "MATH_OR_MAPPING_FAILURE:%s:%s" % (
                type(exc).__name__, str(exc))
            terminal = "MATH_OR_MAPPING_FAILURE"
            return finish()
        manifest["t0"] = t0
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS; field, PMF, seed plan and bounded cap verified")

        graph_failure = False
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                graph_diagnostics.append({
                    "graph_seed": int(graph_seed), "status": "not_started",
                    "admitted": False, "failure_reason": resource,
                })
                graph_failure = True
                break
            graph = graph_builder(int(graph_seed))
            admitted, diagnostic = search_runner.graph_preflight(graph, graph_seed)
            graph_diagnostics.append(diagnostic)
            if admitted:
                graphs[int(graph_seed)] = np.asarray(graph["dense"], dtype=np.int64)
            else:
                graph_failure = True
            _append_log(root, "graph preflight seed=%d admitted=%s reason=%s"
                        % (graph_seed, admitted, diagnostic.get("failure_reason", "")))
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                graph_failure = True
                break
        if graph_failure or len(graphs) != len(GRAPH_SEEDS):
            if not stop_reason:
                stop_reason, terminal = "GRAPH_PREFLIGHT_FAILED", "GRAPH_PREFLIGHT_FAILED"
            return finish()

        pmf = np.asarray(shape_pmf_grid()[0]["pmf"], dtype=np.float64)
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                return finish()
            onepass, deep, diagnostic = build_candidates(
                graphs[int(graph_seed)], pmf, int(graph_seed))
            candidate_diagnostics.append(diagnostic)
            _append_log(root, "accepted deep H0D seed=%d admitted=%s stop=%s"
                        % (graph_seed,
                           diagnostic.get("deep_candidate_admitted", deep is not None),
                           diagnostic.get("construction_stop", False)))
            admitted = bool(diagnostic.get("candidate_admitted", onepass is not None))
            deep_admitted = bool(diagnostic.get("deep_candidate_admitted", deep is not None))
            if (diagnostic.get("construction_stop") or not admitted
                    or not deep_admitted or onepass is None or deep is None):
                stop_reason = str(diagnostic.get(
                    "failure_reason", "DEEP_CANDIDATE_ADMISSION_STOP"))
                terminal = "DEEP_CANDIDATE_ADMISSION_STOP"
                return finish()
            deep_matrices[int(graph_seed)] = np.asarray(deep, dtype=np.int64)
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                return finish()

        prior = np.tile(pmf, (N, 1))
        for graph_seed, stream, frame, seed in _validate_seed_plan(seed_namespace):
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                return finish()
            truth = prior_runner.prior_runner.sample_error(seed, pmf, width=N)
            common_h = deep_matrices[int(graph_seed)]
            paired = prior_runner.prior_runner.paired_arm_data(
                common_h, common_h, truth, prior)
            arm_results: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                arm_input = paired[arm]
                row, issue = dispatch(
                    int(graph_seed), int(stream), int(frame), int(seed), arm,
                    arm_input["dense"], arm_input["prior"],
                    arm_input["truth"], arm_input["syndrome"])
                if row is not None:
                    arm_results[arm] = row
                if issue:
                    stop_reason = issue
                    terminal = ("RESOURCE_STOP" if any(
                        marker in issue for marker in
                        ("cap", "wall", "rss", "resource_abort"))
                                else "INTEGRITY_STOP")
                    return finish()
            if set(arm_results) == {"control", "candidate"}:
                completed_pairs.append({
                    "graph_seed": int(graph_seed), "stream": int(stream),
                    "frame": int(frame),
                    "control_success": bool(arm_results["control"]["exact"]
                                            and arm_results["control"]["syndrome_accept"]),
                    "candidate_success": bool(arm_results["candidate"]["exact"]
                                               and arm_results["candidate"]["syndrome_accept"]),
                })
        summary = _summarize(rows, completed_pairs, "")
        terminal = str(summary["classification"])
        return finish()
    except Exception as exc:
        stop_reason = "implementation_exception:%s:%s" % (
            type(exc).__name__, str(exc))
        terminal = "IMPLEMENTATION_STOP"
        _append_log(root, stop_reason)
        finish()
        raise


def _bind_production_decoder() -> Callable[..., Any]:
    """Bind the fixed v35 decoder only when execute is explicitly requested."""
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def decode(h, prior, syndrome):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=WARM_BELIEFS,
            field=FIELD)

    return decode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded GF32 MRB rescue EXPLORE")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check pure math and output path only")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            out_root=args.out_root, decode_fn=_bind_production_decoder(),
            graph_builder=search_runner.build_profile_graph,
            command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
