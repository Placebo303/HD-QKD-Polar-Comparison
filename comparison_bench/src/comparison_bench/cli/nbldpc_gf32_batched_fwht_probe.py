"""Paired fixed-call timing for the GF(32) batched outgoing-FWHT variant."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_gf32_kernel_hotspots as hotspots
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

BATCH_UUID = "7d45396d-a8ca-4a21-adef-74adacc5e9ec"
CONTRACT = "NBLDPC-GF32-BATCHED-FWHT-20261002/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_batchedfwht_7d45396d"
PARENT_ROOT = Path("workspace") / "gf32_softprior_replica_cbe151fe"
WALL_CAP_S = 120.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 5 * 1024 * 1024
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_batched_fwht_probe --execute "
    "--out-root workspace/gf32_batchedfwht_7d45396d"
)

CALL_FIELDS = (
    "round", "order_position", "path", "selection_role", "graph_id",
    "pair_index", "call_index", "call_role", "branch_index", "guess_symbol",
    "selected_variable", "raw_vector_index", "iterations", "decoder_status",
    "syndrome_ok_reported", "own_syndrome_valid", "runtime_s", "wall_s",
    "is_first_decoder_call", "is_first_for_path", "source_vector_match",
    "source_iterations_match", "source_status_match", "source_report_match",
    "source_syndrome_label_match", "source_beliefs_match",
    "source_beliefs_max_abs_diff", "source_replay_match",
    "exact", "valid_wrong", "paired_vector_match", "paired_iterations_match",
    "paired_status_match", "paired_report_match", "paired_beliefs_match",
    "paired_beliefs_max_abs_diff", "failure_reason",
)


def _require_frozen_out_root(out_root: str | Path) -> None:
    if Path(out_root) != OUT_ROOT_RELATIVE:
        raise ValueError(f"out_root must be the frozen relative path {OUT_ROOT_RELATIVE}")


def _preflight_root(out_root: str | Path, repo_root: str | Path | None) -> Path:
    _require_frozen_out_root(out_root)
    return hotspots._preflight_root(out_root, repo_root)


def verify_t0(*, out_root: str | Path = OUT_ROOT_RELATIVE,
              repo_root: str | Path | None = None) -> dict[str, Any]:
    root = _preflight_root(out_root, repo_root)
    return {
        "status": "PASS", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "source_reads": 0, "decoder_calls": 0, "writes": 0,
        "out_root": str(root),
    }


def dry_run(*, out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    result = verify_t0(out_root=out_root, repo_root=repo_root)
    result["status"] = "DRY_RUN"
    return result


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_calls(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CALL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _null_complete_totals(summary: dict[str, Any]) -> None:
    for key in ("rounds", "paired_totals", "exact_counts", "valid_wrong_counts",
                "paired_wall_ratio_candidate_over_reference"):
        summary[key] = None


def _prior_for_case(validated: Mapping[str, Any], case: Mapping[str, Any]) -> np.ndarray:
    prior = np.asarray(validated["prior"], dtype=np.float64).copy()
    if case["selection_role"] == "selected_rescue":
        off = int(case["call_offset"])
        selected = int(case["selected_variable"])
        guess = int(validated["values"]["guess"][off])
        prior[selected, :] = 0.0
        prior[selected, guess] = 1.0
    return prior


def _decoder_input(case: Mapping[str, Any], prior: np.ndarray) -> dict[str, Any]:
    return {
        "args": (case["h"], prior, case["syndrome"]),
        "kwargs": {
            "max_iter": hotspots.MAX_ITER, "damping_alpha": hotspots.DAMPING_ALPHA,
            "warm_beliefs": None, "field": None,
        },
    }


def _source_matches(
        result: Any, case: Mapping[str, Any], validated: Mapping[str, Any],
        *, x_hat: np.ndarray, iterations: int, status: str, reported: bool,
        ) -> tuple[dict[str, Any], np.ndarray | None, list[str]]:
    values = validated["values"]
    off = int(case["call_offset"])
    call_id = int(case["call_index"])
    saved = np.asarray(validated["raw_by_call"][call_id], dtype=np.int64)
    vector_match = x_hat.shape == (hotspots.N,) and np.array_equal(x_hat, saved)
    iterations_match = iterations == int(values["iterations"][off])
    status_match = status == str(values["decoder_status"][off])
    report_match = (not bool(values["reported_available"][off])
                    or reported == bool(values["reported"][off]))
    reasons: list[str] = []
    beliefs = getattr(result, "final_beliefs", None)
    final_beliefs = None if beliefs is None else np.asarray(beliefs, dtype=np.float64)
    if (final_beliefs is None or final_beliefs.shape != (hotspots.N, hotspots.Q)
            or not np.all(np.isfinite(final_beliefs))):
        reasons.append("final_beliefs_invalid")
    computed = np.asarray(layout.gf32_syndrome(case["h"], x_hat), dtype=np.int64)
    own_syndrome_valid = (computed.shape == (hotspots.M,) and np.array_equal(
        computed, np.asarray(case["syndrome"], dtype=np.int64)))
    syndrome_label_match = own_syndrome_valid == bool(values["valid"][off])

    source_beliefs_match: bool | None = None
    source_beliefs_max_abs_diff: float | None = None
    if case["selection_role"] == "baseline_failed":
        stored = validated["belief_by_call"].get(call_id)
        if stored is None or final_beliefs is None:
            source_beliefs_match = False
        else:
            source_beliefs_max_abs_diff = float(np.max(np.abs(final_beliefs - stored[0])))
            source_beliefs_match = (str(stored[1]) == "CHECK_UPDATED"
                                    and np.allclose(final_beliefs, stored[0], rtol=0.0, atol=1e-12))

    checks = {
        "source_vector_match": bool(vector_match),
        "source_iterations_match": bool(iterations_match),
        "source_status_match": bool(status_match),
        "source_report_match": bool(report_match),
        "own_syndrome_valid": bool(own_syndrome_valid),
        "source_syndrome_label_match": bool(syndrome_label_match),
        "source_beliefs_match": source_beliefs_match,
        "source_beliefs_max_abs_diff": source_beliefs_max_abs_diff,
    }
    if not vector_match:
        reasons.append("saved_vector_mismatch")
    if not iterations_match:
        reasons.append("saved_iterations_mismatch")
    if not status_match:
        reasons.append("saved_status_mismatch")
    if not report_match:
        reasons.append("saved_syndrome_report_mismatch")
    if not syndrome_label_match:
        reasons.append("saved_syndrome_validity_mismatch")
    if source_beliefs_match is False:
        reasons.append("saved_failure_beliefs_mismatch")
    return checks, final_beliefs, reasons


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        reference_decoder: Callable[..., Any],
        candidate_decoder: Callable[..., Any],
        out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    root = _preflight_root(out_root, repo_root)
    callbacks = (source_reader, reference_decoder, candidate_decoder)
    if not all(callable(callback) for callback in callbacks):
        raise ValueError("explicit source_reader, reference_decoder, candidate_decoder callbacks are required")
    rss_fn = hotspots._rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    log_path.write_text(f"EXPLORE {BATCH_UUID}; fixed paired replay only.\n", encoding="utf-8")

    source_reads = decoder_calls = 0
    rows: list[dict[str, Any]] = []
    stop_reasons: list[str] = []
    resource_events: list[dict[str, Any]] = []
    peak_rss: int | None = None
    source_setup_wall_s: float | None = None
    source_meta: dict[str, Any] | None = None
    first_path_call: dict[str, bool] = {"reference": False, "candidate": False}

    def add_stop(reason: str) -> None:
        if reason not in stop_reasons:
            stop_reasons.append(reason)

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
            resource_events.append({"phase": phase, "reason": reason,
                                    "elapsed_wall_s": elapsed, "rss_bytes": rss})
            add_stop(reason)
        return bool(reasons)

    def build_summary(status: str) -> dict[str, Any]:
        elapsed = max(float(now()) - started, 0.0)
        summary: dict[str, Any] = {
            "status": status, "selected_case_count": 18, "decoder_calls": decoder_calls,
            "sampler_calls": 0, "search_calls": 0, "graph_build_calls": 0,
            "source_reads": source_reads, "source_load_and_case_setup_wall_s": source_setup_wall_s,
            "recorded_call_count": len(rows), "resource_events": resource_events,
            "stop_reasons": stop_reasons, "elapsed_wall_s": elapsed,
            "peak_rss_bytes": peak_rss, "output_bytes": None,
            "first_pass_output_bytes": None,
            "output_bytes_scope": "first-pass artifacts before terminal rewrites",
            "source_identity": source_meta,
        }
        if status == "BATCHED_FWHT_FIXED_CASES_MATCH":
            summary["rounds"] = {}
            summary["exact_counts"] = {}
            summary["valid_wrong_counts"] = {}
            for round_index in (1, 2):
                round_rows = [row for row in rows if int(row["round"]) == round_index]
                round_info: dict[str, Any] = {"calls": len(round_rows), "groups": {}}
                summary["exact_counts"][str(round_index)] = {
                    path: sum(bool(row["exact"]) for row in round_rows if row["path"] == path)
                    for path in ("reference", "candidate")
                }
                summary["valid_wrong_counts"][str(round_index)] = {
                    path: sum(bool(row["valid_wrong"]) for row in round_rows if row["path"] == path)
                    for path in ("reference", "candidate")
                }
                path_totals = {}
                for path in ("reference", "candidate"):
                    selected = [row for row in round_rows if row["path"] == path]
                    path_totals[path] = {
                        "calls": len(selected),
                        "wall_s": float(sum(float(row["wall_s"]) for row in selected)),
                        "decoder_runtime_s": float(sum(float(row["runtime_s"]) for row in selected)),
                    }
                round_info["paths"] = path_totals
                ref_wall = path_totals["reference"]["wall_s"]
                ref_runtime = path_totals["reference"]["decoder_runtime_s"]
                round_info["paired_wall_ratio_candidate_over_reference"] = (
                    path_totals["candidate"]["wall_s"] / ref_wall if ref_wall > 0.0 else None)
                round_info["paired_decoder_runtime_ratio_candidate_over_reference"] = (
                    path_totals["candidate"]["decoder_runtime_s"] / ref_runtime
                    if ref_runtime > 0.0 else None)
                for role in hotspots.ROLES:
                    group = [row for row in round_rows if row["selection_role"] == role]
                    group_info = {}
                    for path in ("reference", "candidate"):
                        selected = [row for row in group if row["path"] == path]
                        group_info[path] = {
                            "calls": len(selected),
                            "wall_s": float(sum(float(row["wall_s"]) for row in selected)),
                            "decoder_runtime_s": float(sum(float(row["runtime_s"]) for row in selected)),
                        }
                    group_ref_wall = group_info["reference"]["wall_s"]
                    group_info["paired_wall_ratio_candidate_over_reference"] = (
                        group_info["candidate"]["wall_s"] / group_ref_wall
                        if group_ref_wall > 0.0 else None)
                    round_info["groups"][role] = group_info
                summary["rounds"][str(round_index)] = round_info
            summary["paired_totals"] = {
                path: {
                    "calls": sum(row["path"] == path for row in rows),
                    "wall_s": float(sum(float(row["wall_s"]) for row in rows if row["path"] == path)),
                    "decoder_runtime_s": float(sum(float(row["runtime_s"]) for row in rows
                                                    if row["path"] == path)),
                }
                for path in ("reference", "candidate")
            }
            reference_wall = summary["paired_totals"]["reference"]["wall_s"]
            summary["paired_wall_ratio_candidate_over_reference"] = (
                summary["paired_totals"]["candidate"]["wall_s"] / reference_wall
                if reference_wall > 0.0 else None)
            summary["first_calls"] = {
                path: next(({
                    "wall_s": row["wall_s"], "decoder_runtime_s": row["runtime_s"],
                    "round": row["round"], "selection_role": row["selection_role"],
                } for row in rows if row["path"] == path and row["is_first_for_path"]), None)
                for path in ("reference", "candidate")
            }
            summary["first_decoder_call"] = next(({
                "path": row["path"], "wall_s": row["wall_s"],
                "decoder_runtime_s": row["runtime_s"], "round": row["round"],
                "selection_role": row["selection_role"],
            } for row in rows if row["is_first_decoder_call"]), None)
        else:
            _null_complete_totals(summary)
        return summary

    def write_outputs(status: str) -> dict[str, Any]:
        summary = build_summary(status)
        manifest = {
            "batch_uuid": BATCH_UUID, "contract": CONTRACT, "status": status,
            "command": command, "classification": "BATCHED_FWHT_FIXED_CALL_TIMING_ONLY",
            "parent_batch_uuid": hotspots.PARENT_UUID,
            "hotspot_batch_uuid": hotspots.BATCH_UUID,
            "source_identity": source_meta, "source_reads": source_reads,
            "decoder_calls": decoder_calls, "stop_reasons": stop_reasons,
        }
        _write_calls(root / "call_records.csv", rows)
        _write_json(root / "summary.json", summary)
        _write_json(root / "manifest.json", manifest)
        return summary

    validated: dict[str, Any] | None = None
    try:
        read_started = float(now())
        source_reads += 1
        loaded = source_reader()
        validated = hotspots._validate_source(loaded)
        source_setup_wall_s = max(float(now()) - read_started, 0.0)
        source_meta = dict(loaded["manifest"].get("source_identity", {}))
        if resource_check("after_source_read_and_case_setup"):
            add_stop("resource_cap_after_source_setup")
    except Exception as exc:
        source_setup_wall_s = max(float(now()) - started, 0.0)
        add_stop(f"source_or_selection_error:{type(exc).__name__}:{exc}")

    if validated is not None and not stop_reasons:
        decoders = {"reference": reference_decoder, "candidate": candidate_decoder}
        values = validated["values"]
        cases = validated["cases"]
        for round_index, order in ((1, ("reference", "candidate")),
                                   (2, ("candidate", "reference"))):
            if stop_reasons:
                break
            for case in cases:
                call_items: dict[str, tuple[Any, np.ndarray, np.ndarray]] = {}
                case_rows: dict[str, dict[str, Any]] = {}
                for order_position, path in enumerate(order, start=1):
                    off = int(case["call_offset"])
                    prior = _prior_for_case(validated, case)
                    record: dict[str, Any] = {
                        "round": round_index, "order_position": order_position, "path": path,
                        "selection_role": str(case["selection_role"]),
                        "graph_id": int(case["graph_id"]), "pair_index": int(case["pair_index"]),
                        "call_index": int(case["call_index"]), "call_role": str(values["role"][off]),
                        "branch_index": int(values["branch"][off]),
                        "guess_symbol": int(values["guess"][off]),
                        "selected_variable": int(case["selected_variable"]),
                        "raw_vector_index": int(values["vector"][off]),
                        "iterations": None, "decoder_status": None,
                        "syndrome_ok_reported": None, "own_syndrome_valid": None,
                        "runtime_s": None, "wall_s": None,
                        "is_first_decoder_call": decoder_calls == 0,
                        "is_first_for_path": not first_path_call[path],
                        "source_vector_match": None, "source_iterations_match": None,
                        "source_status_match": None, "source_report_match": None,
                        "source_beliefs_match": None, "source_beliefs_max_abs_diff": None,
                        "source_replay_match": None, "exact": None, "valid_wrong": None,
                        "paired_vector_match": None, "paired_iterations_match": None,
                        "paired_status_match": None, "paired_report_match": None,
                        "paired_beliefs_match": None, "paired_beliefs_max_abs_diff": None,
                        "failure_reason": None,
                    }
                    rows.append(record)
                    case_rows[path] = record
                    started_call = float(now())
                    result = None
                    try:
                        decoder_call = _decoder_input(case, prior)
                        result = decoders[path](*decoder_call["args"], **decoder_call["kwargs"])
                    except Exception as exc:
                        record["failure_reason"] = f"{type(exc).__name__}: {exc}"
                        add_stop(f"decoder_call_failed:{round_index}:{case['call_index']}:{path}")
                    ended_call = float(now())
                    record["wall_s"] = max(ended_call - started_call, 0.0)
                    decoder_calls += 1
                    first_path_call[path] = True
                    if result is not None:
                        try:
                            x_hat = np.asarray(result.x_hat, dtype=np.int64).reshape(-1)
                            iterations = int(result.iterations)
                            status = str(result.status)
                            reported = bool(result.syndrome_ok)
                            runtime_s = float(result.runtime_s)
                            if not np.isfinite(runtime_s) or runtime_s < 0.0:
                                raise ValueError("decoder_runtime_invalid")
                            record.update({
                                "iterations": iterations, "decoder_status": status,
                                "syndrome_ok_reported": reported, "runtime_s": runtime_s,
                            })
                            checks, final_beliefs, reasons = _source_matches(
                                result, case, validated, x_hat=x_hat, iterations=iterations,
                                status=status, reported=reported)
                            record.update(checks)
                            record["source_replay_match"] = not reasons
                            if reasons:
                                record["failure_reason"] = ";".join(reasons)
                                add_stop(f"source_roundtrip_mismatch:{round_index}:{case['call_index']}:{path}")
                            elif final_beliefs is not None:
                                call_items[path] = (result, x_hat, final_beliefs)
                        except Exception as exc:
                            record["failure_reason"] = f"{type(exc).__name__}: {exc}"
                            add_stop(f"result_validation_failed:{round_index}:{case['call_index']}:{path}")
                    elif record["failure_reason"] is None:
                        record["failure_reason"] = "decoder_returned_none"
                        add_stop(f"decoder_returned_none:{round_index}:{case['call_index']}:{path}")

                    if resource_check(f"round_{round_index}_call_{decoder_calls}"):
                        add_stop("resource_cap_after_call")
                    if stop_reasons:
                        break

                if stop_reasons:
                    break
                if len(call_items) != 2:
                    add_stop(f"paired_call_missing:{round_index}:{case['call_index']}")
                    break
                ref_result, ref_x, ref_beliefs = call_items["reference"]
                cand_result, cand_x, cand_beliefs = call_items["candidate"]
                ref_report = bool(ref_result.syndrome_ok)
                cand_report = bool(cand_result.syndrome_ok)
                vector_match = ref_x.shape == cand_x.shape and np.array_equal(ref_x, cand_x)
                iterations_match = int(ref_result.iterations) == int(cand_result.iterations)
                status_match = str(ref_result.status) == str(cand_result.status)
                report_match = ref_report == cand_report
                belief_max_abs_diff = float(np.max(np.abs(ref_beliefs - cand_beliefs)))
                beliefs_match = np.allclose(ref_beliefs, cand_beliefs, rtol=0.0, atol=1e-12)
                pair_checks = {
                    "paired_vector_match": bool(vector_match),
                    "paired_iterations_match": bool(iterations_match),
                    "paired_status_match": bool(status_match),
                    "paired_report_match": bool(report_match),
                    "paired_beliefs_match": bool(beliefs_match),
                    "paired_beliefs_max_abs_diff": belief_max_abs_diff,
                }
                for record in case_rows.values():
                    record.update(pair_checks)
                if not all((vector_match, iterations_match, status_match, report_match, beliefs_match)):
                    for record in case_rows.values():
                        record["failure_reason"] = "paired_reference_candidate_mismatch"
                    add_stop(f"paired_mismatch:{round_index}:{case['call_index']}")
                    break
                for path, (_, x_hat, _) in call_items.items():
                    exact = bool(np.array_equal(x_hat, np.asarray(case["truth"], dtype=np.int64))
                                 and case_rows[path]["own_syndrome_valid"])
                    case_rows[path]["exact"] = exact
                    case_rows[path]["valid_wrong"] = bool(case_rows[path]["own_syndrome_valid"] and not exact)

    complete = decoder_calls == 72 and not stop_reasons and len(rows) == 72
    status = "BATCHED_FWHT_FIXED_CASES_MATCH" if complete else (
        "INCOMPLETE" if resource_events else "STOP")
    summary = write_outputs(status)
    artifacts = ("manifest.json", "summary.json", "call_records.csv", "EXPLORATION_LOG.md")
    paths = [root / name for name in artifacts]
    first_pass_bytes = sum(path.stat().st_size for path in paths if path.exists())
    if resource_check("after_first_pass_artifacts"):
        add_stop("resource_cap_after_first_pass_artifacts")
    if first_pass_bytes > ARTIFACT_CAP_BYTES:
        add_stop("artifact_cap")
    if any(reason in ("wall_cap", "rss_cap", "artifact_cap") for reason in stop_reasons):
        status = "INCOMPLETE"
        summary = write_outputs(status)
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
        f"stop reasons: {json.dumps(stop_reasons)}\n"
        f"first-pass output bytes: {first_pass_bytes}\n", encoding="utf-8")
    return {
        "status": status, "summary": summary, "root": str(root),
        "source_reads": source_reads, "decoder_calls": decoder_calls,
        "sampler_calls": 0, "call_records": rows,
        "terminal_artifact_bytes": sum(path.stat().st_size for path in paths if path.exists()),
        "artifacts": {name: str(root / name) for name in artifacts},
    }


def _bind_production(repo_root: str | Path | None = None) -> dict[str, Any]:
    from comparison_bench.formal_ir import v35_algorithm_development as v35
    from comparison_bench.formal_ir.nbldpc_gf32_batched_check import batched_check_update_log_batch

    def reference_decoder(h, prior, syndrome, **kwargs):
        return v35.decode_row_layered_fftqspa(h, prior, syndrome, **kwargs)

    def candidate_decoder(h, prior, syndrome, **kwargs):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, check_update_fn=batched_check_update_log_batch, **kwargs)

    return {
        "source_reader": hotspots._source_reader(repo_root),
        "reference_decoder": reference_decoder,
        "candidate_decoder": candidate_decoder,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paired fixed-call GF(32) batched outgoing FWHT probe")
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
        _preflight_root(args.out_root, None)
        result = execute_batch(**_bind_production(), out_root=args.out_root, command=COMMAND)
    printable = result.get("summary", result)
    print(json.dumps(printable, sort_keys=True, default=str))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "BATCHED_FWHT_FIXED_CASES_MATCH") else 2


if __name__ == "__main__":
    raise SystemExit(main())
