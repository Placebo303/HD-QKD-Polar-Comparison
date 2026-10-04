"""Fixed saved-call replay for the GF(32) soft-prior kernel hotspot EXPLORE."""
from __future__ import annotations

import argparse
import cProfile
import csv
import io
import json
import pstats
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

BATCH_UUID = "443938ee-da09-4795-a9b2-25bc95047283"
CONTRACT = "NBLDPC-GF32-KERNEL-HOTSPOTS-20261002/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-softprior-replica-v1"
PARENT_UUID = "cbe151fe-25f7-4990-8895-858091467e2b"
PARENT_CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md"
PARENT_ROOT = Path("workspace") / "gf32_softprior_replica_cbe151fe"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_hotspots_443938ee"
SOURCE_EXPECTED = {
    "batch_uuid": "a9352bc1-ae56-443b-ae93-9dcfa85d4229",
    "contract": "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md",
    "seed_namespace": "gf32-degree-admitted-v1",
    "graph_input_kind": "admitted_source",
}
GRAPH_IDS = tuple(range(2026093901, 2026093907))
N, M, Q = 128, 52, 32
MAX_ITER = 90
DAMPING_ALPHA = 1.0
ROLES = ("baseline_valid", "baseline_failed", "selected_rescue")
WALL_CAP_S = 120.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 5 * 1024 * 1024
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_kernel_hotspots --execute "
    "--out-root workspace/gf32_hotspots_443938ee"
)

DIAGNOSTIC_KEYS = (
    "source_batch_uuid", "source_contract", "source_seed_namespace",
    "source_graph_input_kind", "source_graph_id", "H_deep", "original_prior",
    "pair_index", "pair_graph_id", "pair_truth", "pair_syndrome",
    "pair_baseline_call_index", "pair_candidate_selected_call_index",
    "pair_selected_variable", "call_index", "call_pair_index", "call_graph_id",
    "call_role", "call_branch_index", "call_guess_symbol",
    "call_selected_variable", "call_status", "call_decoder_status",
    "call_iterations", "call_syndrome_valid", "call_syndrome_ok_reported",
    "call_syndrome_ok_reported_available", "call_raw_vector_index",
    "raw_vector_call_index", "raw_x_hat", "belief_call_index",
    "baseline_failure_belief_provenance", "baseline_failure_beliefs",
    "selector_call_index", "selector_selected_column",
)

CALL_FIELDS = (
    "round", "profile_mode", "selection_role", "graph_id", "pair_index",
    "call_index", "call_role", "branch_index", "guess_symbol",
    "selected_variable", "raw_vector_index", "iterations", "decoder_status",
    "syndrome_ok_reported", "syndrome_valid", "exact", "valid_wrong",
    "replay_match_vector", "replay_match_iterations", "replay_match_status", "wall_s",
    "failure_reason",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _resolve(path: str | Path, repo_root: str | Path | None) -> Path:
    base = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(path)
    return requested.resolve() if requested.is_absolute() else (base / requested).resolve()


def _require_frozen_out_root(out_root: str | Path) -> None:
    if Path(out_root) != OUT_ROOT_RELATIVE:
        raise ValueError(f"out_root must be the frozen relative path {OUT_ROOT_RELATIVE}")


def _preflight_root(out_root: str | Path, repo_root: str | Path | None) -> Path:
    root = _resolve(out_root, repo_root)
    if root.exists():
        raise FileExistsError(f"refusing existing output root {root}")
    return root


def verify_t0(*, out_root: str | Path = OUT_ROOT_RELATIVE,
              repo_root: str | Path | None = None) -> dict[str, Any]:
    _require_frozen_out_root(out_root)
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
    # WSL/Linux ru_maxrss is a process high-water mark in KiB.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _read_parent(root: Path) -> dict[str, Any]:
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        summary = json.load(stream)
    with np.load(root / "diagnostics.npz", allow_pickle=False) as archive:
        diagnostics = {key: archive[key] for key in DIAGNOSTIC_KEYS}
    return {"manifest": manifest, "summary": summary, "diagnostics": diagnostics}


def _scalar_text(value: Any) -> str:
    values = np.asarray(value).reshape(-1)
    if values.size != 1:
        raise ValueError("source identity must be scalar")
    return str(values[0])


def _validate_source(loaded: Mapping[str, Any]) -> dict[str, Any]:
    manifest, summary = loaded["manifest"], loaded["summary"]
    diagnostics = loaded["diagnostics"]
    for label, row in (("manifest", manifest), ("summary", summary)):
        expected = {
            "batch_uuid": PARENT_UUID, "contract": PARENT_CONTRACT,
            "seed_namespace": SEED_NAMESPACE, "status": "COMPLETE",
            "classification": "MECHANISM_SIGNAL",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f"{label}_{key}_mismatch")
    if not set(DIAGNOSTIC_KEYS).issubset(diagnostics):
        raise ValueError("parent_diagnostic_keys_mismatch")
    source_identity = manifest.get("source_identity")
    if not isinstance(source_identity, Mapping):
        raise ValueError("manifest_source_identity_missing")
    for key, expected in SOURCE_EXPECTED.items():
        if source_identity.get(key) != expected:
            raise ValueError(f"manifest_source_{key}_mismatch")
        if _scalar_text(diagnostics[f"source_{key}"]) != expected:
            raise ValueError(f"diagnostic_source_{key}_mismatch")

    source_ids = np.asarray(diagnostics["source_graph_id"], dtype=np.int64)
    h_all = np.asarray(diagnostics["H_deep"], dtype=np.int64)
    prior = np.asarray(diagnostics["original_prior"], dtype=np.float64)
    if (source_ids.shape != (6,) or tuple(sorted(source_ids.tolist())) != GRAPH_IDS
            or h_all.shape != (6, M, N) or prior.shape != (N, Q)
            or not np.all(np.isfinite(prior)) or np.any(prior < 0.0)):
        raise ValueError("source_matrix_or_prior_shape_mismatch")
    if not np.allclose(prior.sum(axis=1), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("source_prior_not_normalized")
    h_by_graph = {int(graph_id): h_all[i] for i, graph_id in enumerate(source_ids)}

    pair_index = np.asarray(diagnostics["pair_index"], dtype=np.int64)
    pair_graph = np.asarray(diagnostics["pair_graph_id"], dtype=np.int64)
    truth = np.asarray(diagnostics["pair_truth"], dtype=np.int64)
    syndrome = np.asarray(diagnostics["pair_syndrome"], dtype=np.int64)
    baseline_indices = np.asarray(diagnostics["pair_baseline_call_index"], dtype=np.int64)
    candidate_indices = np.asarray(diagnostics["pair_candidate_selected_call_index"], dtype=np.int64)
    selected_variables = np.asarray(diagnostics["pair_selected_variable"], dtype=np.int64)
    n_pairs = len(pair_index)
    if (pair_index.shape != (n_pairs,) or pair_graph.shape != (n_pairs,)
            or truth.shape != (n_pairs, N) or syndrome.shape != (n_pairs, M)
            or baseline_indices.shape != (n_pairs,) or candidate_indices.shape != (n_pairs,)
            or selected_variables.shape != (n_pairs,) or n_pairs == 0
            or len(set(map(int, pair_index))) != n_pairs
            or set(map(int, pair_graph)) != set(GRAPH_IDS)):
        raise ValueError("parent_pair_arrays_mismatch")
    if "completed_pairs" in summary and int(summary["completed_pairs"]) != n_pairs:
        raise ValueError("parent_completed_pair_count_mismatch")

    names = {
        "index": ("call_index", np.int64), "pair": ("call_pair_index", np.int64),
        "graph": ("call_graph_id", np.int64), "role": ("call_role", str),
        "branch": ("call_branch_index", np.int64), "guess": ("call_guess_symbol", np.int64),
        "selected": ("call_selected_variable", np.int64),
        "status": ("call_status", str), "decoder_status": ("call_decoder_status", str),
        "iterations": ("call_iterations", np.int64),
        "valid": ("call_syndrome_valid", np.bool_),
        "reported": ("call_syndrome_ok_reported", np.bool_),
        "reported_available": ("call_syndrome_ok_reported_available", np.bool_),
        "vector": ("call_raw_vector_index", np.int64),
    }
    values = {name: np.asarray(diagnostics[key], dtype=dtype) for name, (key, dtype) in names.items()}
    n_calls = len(values["index"])
    if any(arr.shape != (n_calls,) for arr in values.values()) or n_calls == 0:
        raise ValueError("parent_call_arrays_mismatch")
    call_by_id = {int(v): i for i, v in enumerate(values["index"])}
    if len(call_by_id) != n_calls:
        raise ValueError("duplicate_source_call_index")
    raw_call_ids = np.asarray(diagnostics["raw_vector_call_index"], dtype=np.int64)
    raw_vectors = np.asarray(diagnostics["raw_x_hat"], dtype=np.int64)
    if raw_vectors.shape != (len(raw_call_ids), N) or len(set(map(int, raw_call_ids))) != len(raw_call_ids):
        raise ValueError("parent_raw_vector_arrays_mismatch")
    raw_by_call = {int(call_id): raw_vectors[i] for i, call_id in enumerate(raw_call_ids)}
    for i, call_id in enumerate(values["index"]):
        if values["status"][i] != "COMPLETE" or values["iterations"][i] < 0:
            raise ValueError("parent_incomplete_call")
        vector_index = int(values["vector"][i])
        if vector_index < 0 or vector_index >= len(raw_call_ids) or int(raw_call_ids[vector_index]) != int(call_id):
            raise ValueError("parent_raw_vector_map_mismatch")
        if values["decoder_status"][i] == "":
            raise ValueError("parent_decoder_status_missing")

    baseline = np.asarray(baseline_indices, dtype=np.int64)
    candidate = np.asarray(candidate_indices, dtype=np.int64)
    pair_rows: dict[int, dict[str, int]] = {}
    pair_pos = {int(value): i for i, value in enumerate(pair_index)}
    for i, pair_id in enumerate(pair_index):
        b = int(baseline[i])
        off = call_by_id.get(b)
        if (off is None or values["pair"][off] != int(pair_id)
                or values["graph"][off] != int(pair_graph[i]) or values["role"][off] != "baseline"):
            raise ValueError("baseline_call_map_mismatch")
        c = int(candidate[i])
        coff = call_by_id.get(c)
        if (coff is None or values["pair"][coff] != int(pair_id)
                or values["graph"][coff] != int(pair_graph[i])):
            raise ValueError("accepted_candidate_call_map_mismatch")
        if c != b and values["role"][coff] != "soft_prior":
            raise ValueError("accepted_candidate_call_role_mismatch")
        pair_rows[int(pair_id)] = {"offset": i, "baseline": b, "candidate": c}

    selector_call = np.asarray(diagnostics["selector_call_index"], dtype=np.int64)
    selector_var = np.asarray(diagnostics["selector_selected_column"], dtype=np.int64)
    if selector_call.shape != selector_var.shape or len(set(map(int, selector_call))) != len(selector_call):
        raise ValueError("selector_map_mismatch")
    selector_by_call = {int(k): int(v) for k, v in zip(selector_call, selector_var)}
    beliefs_call = np.asarray(diagnostics["belief_call_index"], dtype=np.int64)
    beliefs_prov = np.asarray(diagnostics["baseline_failure_belief_provenance"]).astype(str)
    beliefs = np.asarray(diagnostics["baseline_failure_beliefs"], dtype=np.float64)
    if (beliefs.shape != (len(beliefs_call), N, Q) or beliefs_prov.shape != beliefs_call.shape
            or len(set(map(int, beliefs_call))) != len(beliefs_call)):
        raise ValueError("baseline_belief_map_mismatch")
    belief_by_call = {int(k): (beliefs[i], str(beliefs_prov[i])) for i, k in enumerate(beliefs_call)}

    cases: list[dict[str, Any]] = []
    for graph_id in GRAPH_IDS:
        graph_pairs = sorted(
            (int(pair_id) for pair_id, graph in zip(pair_index, pair_graph) if int(graph) == graph_id))
        valid_pair = failed_pair = rescued_pair = None
        for pair_id in graph_pairs:
            p = pair_rows[pair_id]
            b_off = call_by_id[p["baseline"]]
            valid = bool(values["valid"][b_off])
            if valid and valid_pair is None:
                valid_pair = pair_id
            if not valid:
                if failed_pair is None:
                    failed_pair = pair_id
                c_off = call_by_id[p["candidate"]]
                if bool(values["valid"][c_off]) and rescued_pair is None:
                    rescued_pair = pair_id
        if valid_pair is None or failed_pair is None or rescued_pair is None:
            raise ValueError(f"required_case_missing_for_graph_{graph_id}")
        for selection_role, pair_id in zip(ROLES, (valid_pair, failed_pair, rescued_pair)):
            pair = pair_rows[pair_id]
            baseline_id = pair["baseline"]
            if selection_role == "selected_rescue":
                call_id = pair["candidate"]
            else:
                call_id = baseline_id
            off = call_by_id[call_id]
            pair_off = pair["offset"]
            selected_variable = int(selected_variables[pair_off])
            if selection_role != "baseline_valid":
                if not 0 <= selected_variable < N or selector_by_call.get(baseline_id) != selected_variable:
                    raise ValueError("selected_variable_selector_map_mismatch")
                if int(values["selected"][call_by_id[baseline_id]]) != selected_variable:
                    raise ValueError("baseline_selected_variable_mismatch")
            if selection_role == "selected_rescue":
                if values["role"][off] != "soft_prior" or not bool(values["valid"][off]):
                    raise ValueError("selected_rescue_pointer_not_valid_restart")
                if int(values["selected"][off]) != selected_variable:
                    raise ValueError("restart_selected_variable_mismatch")
                if int(values["guess"][off]) not in (0, 1, 3, 7, 15, 31):
                    raise ValueError("restart_guess_missing")
            if selection_role == "baseline_failed":
                stored = belief_by_call.get(baseline_id)
                if stored is None or stored[1] != "CHECK_UPDATED":
                    raise ValueError("baseline_failure_beliefs_missing_or_wrong_provenance")
            cases.append({
                "selection_role": selection_role, "graph_id": graph_id,
                "pair_index": pair_id, "pair_offset": pair_off,
                "call_index": call_id, "call_offset": off,
                "baseline_call_index": baseline_id, "selected_variable": selected_variable,
                "h": h_by_graph[graph_id], "truth": truth[pair_off],
                "syndrome": syndrome[pair_off], "belief": belief_by_call.get(call_id),
                "raw_vector_index": int(values["vector"][off]),
            })
    if len(cases) != 18:
        raise ValueError("selected_call_count_mismatch")
    return {
        "manifest": manifest, "summary": summary, "diagnostics": diagnostics,
        "cases": cases, "prior": prior, "values": values, "call_by_id": call_by_id,
        "raw_by_call": raw_by_call, "pair_rows": pair_rows, "belief_by_call": belief_by_call,
    }


def select_cases(diagnostics: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Select frozen 18 source-observed calls from a complete parent mapping."""
    if not isinstance(diagnostics, Mapping) or not {"manifest", "summary", "diagnostics"}.issubset(diagnostics):
        raise ValueError("select_cases expects {manifest, summary, diagnostics}")
    return _validate_source(diagnostics)["cases"]


def _source_reader(repo_root: str | Path | None = None) -> Callable[[], Mapping[str, Any]]:
    root = _resolve(PARENT_ROOT, repo_root)
    return lambda: _read_parent(root)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_calls(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CALL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _profile_text(profile: cProfile.Profile | None) -> str:
    if profile is None:
        return "No cProfile calls completed.\n"
    chunks = []
    for title, sort in (("Top 30 by self time", pstats.SortKey.TIME),
                        ("Top 30 by cumulative time", pstats.SortKey.CUMULATIVE)):
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream).strip_dirs().sort_stats(sort)
        stream.write(title + "\n")
        stats.print_stats(30)
        chunks.append(stream.getvalue())
    return "\n".join(chunks)


def _null_complete_totals(summary: dict[str, Any]) -> None:
    for key in ("rounds", "roundtrip_checks", "roundtrip_match_count", "exact_count",
                "valid_wrong_count", "mean_call_wall_s", "profiled_call_wall_s"):
        summary[key] = None


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        decoder: Callable[..., Any], out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    root = _preflight_root(out_root, repo_root)
    if not callable(source_reader) or not callable(decoder):
        raise ValueError("explicit source_reader and decoder callbacks are required")
    rss_fn = _rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    log_path.write_text(f"EXPLORE {BATCH_UUID}; fixed replay only; no new sampling.\n", encoding="utf-8")
    source_reads = decoder_calls = 0
    rows: list[dict[str, Any]] = []
    stop_reasons: list[str] = []
    resource_events: list[dict[str, Any]] = []
    peak_rss: int | None = None
    profile = cProfile.Profile()
    profile_calls = 0
    validated: dict[str, Any] | None = None

    def resource_check(phase: str) -> bool:
        nonlocal peak_rss
        elapsed = max(float(now()) - started, 0.0)
        rss = rss_fn()
        if rss is not None:
            rss = int(rss)
            peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        reasons = []
        if elapsed > WALL_CAP_S:
            reasons.append("wall_cap")
        if rss is not None and rss > RSS_CAP_BYTES:
            reasons.append("rss_cap")
        for reason in reasons:
            resource_events.append({"phase": phase, "reason": reason, "elapsed_wall_s": elapsed,
                                    "rss_bytes": rss})
            if reason not in stop_reasons:
                stop_reasons.append(reason)
        return bool(reasons)

    def write_outputs(status: str, source_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
        elapsed = max(float(now()) - started, 0.0)
        completed = len(rows)
        summary: dict[str, Any] = {
            "status": status, "selected_call_count": 18, "decoder_calls": decoder_calls,
            "sampler_calls": 0, "search_calls": 0, "graph_build_calls": 0,
            "roundtrip_checks": completed, "roundtrip_match_count": sum(bool(r["replay_match_vector"]
                and r["replay_match_iterations"] and r["replay_match_status"]) for r in rows),
            "calls_complete": completed, "source_reads": source_reads,
            "profiled_decoder_calls": profile_calls, "profile_mode_order": ["unprofiled", "unprofiled", "cProfile"],
            "resource_events": resource_events, "stop_reasons": stop_reasons,
            "elapsed_wall_s": elapsed, "peak_rss_bytes": peak_rss,
            "output_bytes": None, "first_pass_output_bytes": None,
            "output_bytes_scope": "first-pass artifacts before final status/manifest/log rewrites",
        }
        if source_meta:
            summary["source_identity"] = source_meta
        if status == "KERNEL_HOTSPOT_PROFILE_COMPLETE":
            summary["exact_count"] = sum(bool(row["exact"]) for row in rows)
            summary["valid_wrong_count"] = sum(bool(row["valid_wrong"]) for row in rows)
            summary["rounds"] = {
                str(i): {"calls": sum(int(row["round"]) == i for row in rows),
                         "wall_s": sum(float(row["wall_s"]) for row in rows if int(row["round"]) == i)}
                for i in (1, 2, 3)}
            summary["mean_call_wall_s"] = float(np.mean([r["wall_s"] for r in rows])) if rows else None
            summary["profiled_call_wall_s"] = sum(float(r["wall_s"]) for r in rows if r["round"] == 3)
        else:
            _null_complete_totals(summary)
        manifest = {
            "batch_uuid": BATCH_UUID, "contract": CONTRACT,
            "seed_namespace": SEED_NAMESPACE, "parent_batch_uuid": PARENT_UUID,
            "parent_contract": PARENT_CONTRACT, "status": status,
            "command": command, "classification": "KERNEL_HOTSPOT_PROFILE_ONLY",
            "source_identity": source_meta, "source_reads": source_reads,
            "decoder_calls": decoder_calls, "sampler_calls": 0,
            "stop_reasons": stop_reasons,
        }
        _write_calls(root / "call_records.csv", rows)
        (root / "profile.txt").write_text(_profile_text(profile if profile_calls else None), encoding="utf-8")
        _write_json(root / "summary.json", summary)
        _write_json(root / "manifest.json", manifest)
        return summary

    source_meta = None
    try:
        source_reads += 1
        loaded = source_reader()
        validated = _validate_source(loaded)
        source_meta = dict(loaded["manifest"].get("source_identity", {}))
        if resource_check("after_source_read"):
            stop_reasons.append("resource_cap_after_source_read")
        else:
            diagnostics = validated["diagnostics"]
            values = validated["values"]
            call_by_id = validated["call_by_id"]
            prior_original = validated["prior"]
            cases = validated["cases"]
            belief_by_call = validated["belief_by_call"]
            pair_rows = validated["pair_rows"]
            for round_index in (1, 2, 3):
                mode = "cProfile" if round_index == 3 else "unprofiled"
                for case in cases:
                    off = int(case["call_offset"])
                    pair_off = int(case["pair_offset"])
                    role = str(case["selection_role"])
                    call_id = int(case["call_index"])
                    branch = int(values["branch"][off])
                    guess = int(values["guess"][off])
                    selected = int(case["selected_variable"])
                    prior = prior_original.copy()
                    if role == "selected_rescue":
                        prior[selected, :] = 0.0
                        prior[selected, guess] = 1.0
                    before = float(now())
                    result = None
                    error = None
                    try:
                        if round_index == 3:
                            profile.enable()
                        result = decoder(
                            case["h"], prior, case["syndrome"], max_iter=MAX_ITER,
                            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
                    except Exception as exc:  # retained as an explicit failed call
                        error = f"{type(exc).__name__}: {exc}"
                    finally:
                        if round_index == 3:
                            profile.disable()
                    after = float(now())
                    wall_s = max(after - before, 0.0)
                    decoder_calls += 1
                    if round_index == 3:
                        profile_calls += 1
                    record = {
                        "round": round_index, "profile_mode": mode,
                        "selection_role": role, "graph_id": int(case["graph_id"]),
                        "pair_index": int(case["pair_index"]), "call_index": call_id,
                        "call_role": str(values["role"][off]), "branch_index": branch,
                        "guess_symbol": guess, "selected_variable": selected,
                        "raw_vector_index": int(values["vector"][off]),
                        "iterations": None, "decoder_status": None,
                        "syndrome_ok_reported": None, "syndrome_valid": None,
                        "exact": None, "valid_wrong": None,
                        "replay_match_vector": False, "replay_match_iterations": False,
                        "replay_match_status": False, "wall_s": wall_s,
                    }
                    rows.append(record)
                    call_failure = False
                    if error is not None or result is None:
                        record["failure_reason"] = error or "decoder_returned_none"
                        stop_reasons.append("decoder_call_failed")
                        call_failure = True
                    try:
                        if call_failure:
                            raise ValueError("decoder_call_failed")
                        x_hat = np.asarray(result.x_hat, dtype=np.int64).reshape(-1)
                        iterations = int(result.iterations)
                        status = str(result.status)
                        reported = bool(result.syndrome_ok)
                        record.update({"iterations": iterations, "decoder_status": status,
                                       "syndrome_ok_reported": reported})
                        saved = np.asarray(validated["raw_by_call"][call_id], dtype=np.int64)
                        vector_match = x_hat.shape == (N,) and np.array_equal(x_hat, saved)
                        iter_match = iterations == int(values["iterations"][off])
                        status_match = status == str(values["decoder_status"][off])
                        record.update({"replay_match_vector": bool(vector_match),
                                       "replay_match_iterations": bool(iter_match),
                                       "replay_match_status": bool(status_match)})
                        if bool(values["reported_available"][off]) and reported != bool(values["reported"][off]):
                            raise ValueError("syndrome_ok_reported_mismatch")
                        computed_syndrome = np.asarray(layout.gf32_syndrome(case["h"], x_hat), dtype=np.int64)
                        syndrome_valid = computed_syndrome.shape == (M,) and np.array_equal(
                            computed_syndrome, np.asarray(case["syndrome"], dtype=np.int64))
                        record["syndrome_valid"] = bool(syndrome_valid)
                        if role == "baseline_failed":
                            stored = belief_by_call.get(call_id)
                            final_beliefs = getattr(result, "final_beliefs", None)
                            if stored is None or final_beliefs is None:
                                raise ValueError("baseline_failure_beliefs_unavailable")
                            actual_beliefs = np.asarray(final_beliefs, dtype=np.float64)
                            if (str(stored[1]) != "CHECK_UPDATED" or actual_beliefs.shape != (N, Q)
                                    or not np.allclose(actual_beliefs, stored[0], rtol=0.0, atol=1e-12)):
                                raise ValueError("baseline_failure_beliefs_mismatch")
                        if not (vector_match and iter_match and status_match and
                                syndrome_valid == bool(values["valid"][off])):
                            raise ValueError("saved_call_roundtrip_mismatch")
                        # Exact/wrong is evaluated only after all replay checks pass.
                        exact = bool(syndrome_valid and np.array_equal(
                            x_hat, np.asarray(case["truth"], dtype=np.int64)))
                        record["exact"] = exact
                        record["valid_wrong"] = bool(syndrome_valid and not exact)
                    except Exception as exc:
                        if not call_failure:
                            record["failure_reason"] = f"{type(exc).__name__}: {exc}"
                            stop_reasons.append("roundtrip_mismatch")
                            call_failure = True
                    over_cap = resource_check(f"round_{round_index}_call_{len(rows)}")
                    if over_cap:
                        stop_reasons.append("resource_cap_after_call")
                        call_failure = True
                    if call_failure:
                        break
                if stop_reasons:
                    break
    except Exception as exc:
        stop_reasons.append(f"source_or_selection_error:{type(exc).__name__}:{exc}")

    if len(rows) == 54 and not stop_reasons:
        status = "KERNEL_HOTSPOT_PROFILE_COMPLETE"
    elif resource_events:
        status = "INCOMPLETE"
    else:
        status = "STOP"
    summary = write_outputs(status, source_meta)
    output_paths = [root / name for name in (
        "manifest.json", "summary.json", "call_records.csv", "profile.txt", "EXPLORATION_LOG.md")]
    first_pass_bytes = sum(path.stat().st_size for path in output_paths if path.exists())
    cap_rss = resource_check("after_first_pass_artifacts")
    if first_pass_bytes > ARTIFACT_CAP_BYTES:
        stop_reasons.append("artifact_cap")
    if cap_rss or first_pass_bytes > ARTIFACT_CAP_BYTES:
        status = "INCOMPLETE"
        summary = write_outputs(status, source_meta)
    summary["elapsed_wall_s"] = max(float(now()) - started, 0.0)
    summary["peak_rss_bytes"] = peak_rss
    summary["first_pass_output_bytes"] = first_pass_bytes
    summary["output_bytes"] = first_pass_bytes
    _write_json(root / "summary.json", summary)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = status
    manifest["stop_reasons"] = stop_reasons
    _write_json(manifest_path, manifest)
    log_path.write_text(
        f"EXPLORE {BATCH_UUID}\nstatus: {status}\nsource reads: {source_reads}\n"
        f"decoder calls: {decoder_calls}; sampler/search/graph builds: 0/0/0\n"
        f"stop reasons: {json.dumps(stop_reasons)}\nfirst-pass output bytes: {first_pass_bytes}\n",
        encoding="utf-8")
    return {
        "status": status, "summary": summary, "root": str(root),
        "source_reads": source_reads, "decoder_calls": decoder_calls,
        "sampler_calls": 0, "call_records": rows,
        "terminal_artifact_bytes": sum(path.stat().st_size for path in output_paths if path.exists()),
        "artifacts": {name: str(root / name) for name in (
            "manifest.json", "summary.json", "call_records.csv", "profile.txt", "EXPLORATION_LOG.md")},
    }


def _bind_production(repo_root: str | Path | None = None) -> dict[str, Any]:
    from comparison_bench.formal_ir import v35_algorithm_development as v35
    def decoder(h, prior, syndrome, *, max_iter, damping_alpha, warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter, damping_alpha=damping_alpha,
            warm_beliefs=warm_beliefs, field=field)
    return {"source_reader": _source_reader(repo_root), "decoder": decoder}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixed saved-call GF(32) kernel hotspot profile")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.dry_run:
        result = dry_run(out_root=args.out_root)
    else:
        _preflight_root(args.out_root, None)
        bound = _bind_production()
        result = execute_batch(**bound, out_root=args.out_root, command=COMMAND)
    printable = result.get("summary", result)
    print(json.dumps(printable, sort_keys=True, default=str))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "KERNEL_HOTSPOT_PROFILE_COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
