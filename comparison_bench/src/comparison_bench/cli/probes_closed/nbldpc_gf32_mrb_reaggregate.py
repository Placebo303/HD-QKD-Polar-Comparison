"""Recompute the aggregate of retained GF32 MRB rows; perform no new science."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable

from comparison_bench.cli.probes_closed import nbldpc_gf32_mrb_rescue_probe as mrb
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-MRB-REAGGREGATE-20261001/PREREG_AND_AUTH.md"
REAGGREGATION_UUID = "e1d549f7-695d-4166-8c4c-e6eaa803a735"
SOURCE_BATCH_UUID = "ebbbe5c2-f53f-4b92-a2ff-3eca358002de"
SOURCE_CONTRACT = "NBLDPC-GF32-MRB-RESCUE-20261001/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_mrb_reaggregate_e1d549f7"
SOURCE_ROOT_RELATIVE = Path("workspace") / "gf32_mrb_rescue_ebbbe5c2"
SOURCE_FILES = ("manifest.json", "frame_records.csv", "summary.json",
                "EXPLORATION_LOG.md")
OUTPUT_FILES = ("manifest.json", "summary.json", "EXPLORATION_LOG.md")
MAX_ROWS = 384
MAX_WALL_S = 600.0
MAX_RSS_BYTES = 4 * 1024**3


class SourceError(ValueError):
    def __init__(self, message: str, rows_read: int = 0):
        super().__init__(message)
        self.rows_read = rows_read


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _resolve(path: str | Path, repo_root: Path) -> Path:
    requested = Path(path)
    return requested.resolve() if requested.is_absolute() else (repo_root / requested).resolve()


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    repo = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    root = _resolve(out_root, repo)
    expected = (repo / OUT_ROOT_RELATIVE).resolve()
    if root != expected:
        raise ValueError("out-root must equal the frozen fresh root %s" % expected)
    if root.exists():
        raise FileExistsError("refusing existing output root %s" % root)
    return root


def _as_bool(raw: str | None, field: str, optional: bool = False) -> bool | None:
    if raw in ("True", "true", "1"):
        return True
    if raw in ("False", "false", "0"):
        return False
    if optional and raw in (None, ""):
        return None
    raise SourceError("invalid/missing boolean %s=%r" % (field, raw))


def _as_int(raw: str | None, field: str, optional: bool = False) -> int | None:
    if optional and raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise SourceError("invalid/missing integer %s=%r" % (field, raw)) from exc


def _as_float(raw: str | None, field: str, optional: bool = False) -> float | None:
    if optional and raw in (None, ""):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise SourceError("invalid/missing number %s=%r" % (field, raw)) from exc
    if not math.isfinite(value):
        raise SourceError("non-finite number %s" % field)
    return value


def _read_rows(path: Path) -> list[dict[str, Any]]:
    required = {
        "call_index", "phase", "graph_seed", "stream", "frame", "seed", "arm",
        "exact", "syndrome_accept", "syndrome_consistent_wrong", "status",
        "iterations", "wall_s", "rss_b", "raw_syndrome_accept",
        "rescue_attempted", "rescue_status", "candidate_count",
        "selected_prior_score", "rescue_wall_s", "bp_runtime_s",
        "damping_alpha", "max_iter",
    }
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise SourceError("source CSV is missing required MRB columns")
        for raw in reader:
            rows_read = len(rows) + 1
            try:
                row = dict(raw)
                for name in ("call_index", "graph_seed", "stream", "frame", "seed",
                             "iterations", "max_iter"):
                    row[name] = _as_int(raw.get(name), name)
                row["rss_b"] = _as_int(raw.get("rss_b"), "rss_b", optional=True)
                row["candidate_count"] = _as_int(
                    raw.get("candidate_count"), "candidate_count", optional=True)
                for name in ("exact", "syndrome_accept", "syndrome_consistent_wrong",
                             "rescue_attempted"):
                    row[name] = _as_bool(raw.get(name), name)
                row["raw_syndrome_accept"] = _as_bool(
                    raw.get("raw_syndrome_accept"), "raw_syndrome_accept", optional=True)
                for name in ("wall_s", "damping_alpha"):
                    row[name] = _as_float(raw.get(name), name)
                for name in ("selected_prior_score", "rescue_wall_s", "bp_runtime_s"):
                    row[name] = _as_float(raw.get(name), name, optional=True)
            except SourceError as exc:
                raise SourceError(str(exc), rows_read=rows_read) from exc
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise SourceError("source row cap exceeded", rows_read=len(rows))
    return rows


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if (manifest.get("batch_uuid") != SOURCE_BATCH_UUID
            or manifest.get("contract") != SOURCE_CONTRACT
            or manifest.get("seed_namespace") != mrb.SEED_PREFIX):
        raise SourceError("source manifest MRB identity mismatch")
    if manifest.get("status") not in {
            "CONTROL_RANGE_UNINFORMATIVE", "NO_SUFFICIENT_SIGNAL", "MECHANISM_SIGNAL"}:
        raise SourceError("source manifest does not mark a complete scientific batch")
    profile = manifest.get("graph_profile", {})
    seeds = [int(seed) for seed in mrb.GRAPH_SEEDS]
    if ((profile.get("n"), profile.get("m"), profile.get("E")) != (128, 52, 256)
            or profile.get("graph_seeds") != seeds
            or profile.get("field") != "GF(32)/polynomial-37"):
        raise SourceError("source graph profile/seeds differ from the frozen MRB profile")
    decoder = manifest.get("decoder", {})
    if (decoder.get("implementation") != "v35.decode_row_layered_fftqspa"
            or decoder.get("max_iter") != 90 or decoder.get("damping_alpha") != 1.0
            or decoder.get("same_bp_decoder_both_arms") is not True):
        raise SourceError("source BP settings differ from frozen MRB settings")
    if manifest.get("pilot") != "NOT_RUN_FIXED_PMF" or manifest.get("fixed_p0") != 0.55:
        raise SourceError("source marginal PMF/no-pilot metadata mismatch")
    rescue = manifest.get("rescue_contract", {})
    if rescue.get("candidate_cap") != 256:
        raise SourceError("source MRB candidate cap mismatch")
    graphs = manifest.get("graph_diagnostics")
    candidates = manifest.get("candidate_diagnostics")
    if (not isinstance(graphs, list) or len(graphs) != 6
            or [row.get("graph_seed") for row in graphs] != seeds
            or not all(row.get("admitted") is True for row in graphs)):
        raise SourceError("source graph admission metadata incomplete/failed")
    if (not isinstance(candidates, list) or len(candidates) != 6
            or [row.get("graph_seed") for row in candidates] != seeds
            or not all(row.get("candidate_admitted") is True
                       and row.get("deep_candidate_admitted") is True
                       and row.get("construction_stop") is False for row in candidates)):
        raise SourceError("source deep-candidate admission metadata incomplete/failed")
    if int(manifest.get("attempted_decoder_calls", -1)) != 384:
        raise SourceError("source manifest call count is not the frozen 384")


def _validate_rows(rows: list[dict[str, Any]]) -> bool:
    expected = []
    for graph_seed, stream, frame, seed in mrb.seed_plan():
        expected.extend((graph_seed, stream, frame, seed, arm)
                        for arm in mrb.arm_order(frame))
    observed = []
    seen = set()
    for index, row in enumerate(rows, 1):
        if row["call_index"] != index or row["phase"] != "holdout":
            raise SourceError("source call order/phase is inconsistent")
        if row["arm"] not in ("control", "candidate"):
            raise SourceError("source contains an unknown arm")
        key = (row["graph_seed"], row["stream"], row["frame"], row["arm"])
        if key in seen:
            raise SourceError("source contains a duplicate pair/arm row")
        seen.add(key)
        if row["damping_alpha"] != 1.0 or row["max_iter"] != 90:
            raise SourceError("source row decoder parameters mismatch")
        if row["syndrome_consistent_wrong"] != (
                row["syndrome_accept"] and not row["exact"]):
            raise SourceError("stored wrong flag disagrees with exact/syndrome fields")
        if row["raw_syndrome_accept"] is None:
            raise SourceError("source row is missing its raw syndrome result")
        if row["arm"] == "candidate" and row["candidate_count"] is None:
            raise SourceError("candidate row is missing its MRB candidate count")
        observed.append((row["graph_seed"], row["stream"], row["frame"],
                         row["seed"], row["arm"]))
    if len(rows) > MAX_ROWS:
        raise SourceError("source row cap exceeded", rows_read=len(rows))
    return len(rows) == len(expected) and observed == expected


def _completed_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, int, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (row["graph_seed"], row["stream"], row["frame"])
        groups.setdefault(key, {})[row["arm"]] = row
    result = []
    for graph_seed, stream, frame, seed in mrb.seed_plan():
        pair = groups.get((graph_seed, stream, frame), {})
        if set(pair) == {"control", "candidate"}:
            control, candidate = pair["control"], pair["candidate"]
            result.append({
                "graph_seed": graph_seed, "stream": stream, "frame": frame,
                "control_success": bool(control["exact"] and control["syndrome_accept"]),
                "candidate_success": bool(candidate["exact"] and candidate["syndrome_accept"]),
            })
    return result


def _reduce(rows: list[dict[str, Any]], manifest: dict[str, Any],
            complete: bool) -> dict[str, Any]:
    summary = mrb._summarize(
        rows, _completed_pairs(rows), "" if complete else "source_rows_incomplete_or_unpaired")
    for arm in ("control", "candidate"):
        arm_rows = [row for row in rows if row["arm"] == arm]
        summary.setdefault("raw_syndrome_failures_by_arm", {})[arm] = sum(
            row["raw_syndrome_accept"] is False for row in arm_rows)
        summary.setdefault("final_syndrome_accepts_by_arm", {})[arm] = sum(
            row["syndrome_accept"] for row in arm_rows)
    summary["raw_syndrome_failures"] = sum(
        values for values in summary["raw_syndrome_failures_by_arm"].values())
    source_cost = manifest.get("resource_measurement", {})
    row_call_max = max((row["wall_s"] for row in rows), default=None)
    row_rss_max = max((row["rss_b"] for row in rows if row["rss_b"] is not None), default=None)
    if complete:
        if (source_cost.get("max_call_wall_s") is None
                or not math.isclose(float(source_cost["max_call_wall_s"]),
                                    float(row_call_max), rel_tol=1e-8, abs_tol=1e-8)):
            raise SourceError("manifest max-call cost disagrees with frame rows")
        if (source_cost.get("max_rss_bytes") is None
                or (row_rss_max is not None and int(source_cost["max_rss_bytes"]) < row_rss_max)):
            raise SourceError("manifest RSS cost disagrees with frame rows")
        for field in ("batch_wall_s", "max_call_wall_s", "max_rss_bytes", "rss_sample_count"):
            if source_cost.get(field) is None:
                raise SourceError("manifest is missing inherited science cost %s" % field)
        if (float(source_cost["batch_wall_s"]) > 1800.0
                or float(source_cost["max_call_wall_s"]) >= 120.0
                or int(source_cost["max_rss_bytes"]) >= 4 * 1024**3):
            raise SourceError("original science cost exceeded the frozen caps")
        row_wall_sum = sum(float(row["wall_s"]) for row in rows)
        tolerance = max(1e-6, abs(row_wall_sum) * 1e-8)
        if float(source_cost["batch_wall_s"]) + tolerance < row_wall_sum:
            raise SourceError("manifest batch wall cost is below summed retained call wall")
        summary["source_science_cost_inherited"] = {
            "batch_wall_s": source_cost["batch_wall_s"],
            "max_call_wall_s": source_cost["max_call_wall_s"],
            "max_rss_bytes": source_cost["max_rss_bytes"],
            "rss_sample_count": source_cost["rss_sample_count"],
            "measurement_scope": source_cost.get("rss_scope"),
        }
        summary["final_syndrome_accepts_by_arm"] = {
            arm: summary["final_syndrome_accepts_by_arm"][arm]
            for arm in ("control", "candidate")}
    else:
        # Attempt counts and sampled disclosure remain observable; partial
        # performance, wrong, raw/final syndrome and rescue totals do not.
        for field in (
            "control_exact", "candidate_exact", "delta", "paired_states",
            "syndrome_consistent_wrong_rows", "syndrome_consistent_wrong_by_arm",
            "raw_syndrome_failures", "raw_syndrome_failures_by_arm",
            "final_syndrome_accepts_by_arm", "rescue_attempts", "rescues_selected",
            "empty_candidate_lists", "candidate_vectors_examined",
            "selected_prior_score_count", "selected_prior_score_min",
            "selected_prior_score_max", "selected_prior_scores",
            "decoder_iterations_by_arm", "decoder_wall_s_by_arm",
            "bp_runtime_s_by_arm", "rescue_wall_s_total", "delta_by_graph",
        ):
            summary[field] = None
    summary.update({
        "batch_uuid": SOURCE_BATCH_UUID,
        "contract": SOURCE_CONTRACT,
        "seed_namespace": mrb.SEED_PREFIX,
        "reaggregation_uuid": REAGGREGATION_UUID,
        "reaggregation_contract": CONTRACT,
        "terminal_status": "REAGGREGATION_COMPLETE" if complete else "SOURCE_INCOMPLETE",
        "attempted_decoder_calls": len(rows),
        "attempted_frame_rows": len(rows),
        "attempted_call_counts": {"pilot": 0, "holdout": len(rows),
                                  "total": len(rows)},
        "source_science_terminal_status": manifest.get("status"),
        "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "tag_bits": 0,
        "FER": None, "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "Mechanical reaggregation of stored exact/syndrome/status/cost fields from "
            "one retained synthetic MRB batch; no vector replay or redecoding, and no "
            "cross-batch pooling, conditional channel, FER, f_eff, SKR, throughput, "
            "qualification, publication, or route claim"),
    })
    return summary


def _write_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def execute_reaggregation(*, out_root: str | Path,
                          source_root: str | Path | None = None,
                          repo_root: str | Path | None = None,
                          now: Callable[[], float] = time.perf_counter,
                          rss_fn: Callable[[], int | None] | None = None) -> dict[str, Any]:
    repo = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    root = validate_out_root(out_root, repo_root=repo)
    source = _resolve(SOURCE_ROOT_RELATIVE if source_root is None else source_root, repo)
    rss_fn = d5._rss_bytes if rss_fn is None else rss_fn
    root.mkdir(parents=False, exist_ok=False)
    manifest: dict[str, Any] = {
        "track": "EXPLORE", "status": "RUNNING",
        "reaggregation_uuid": REAGGREGATION_UUID,
        "reaggregation_contract": CONTRACT,
        "source_batch_uuid": SOURCE_BATCH_UUID,
        "source_contract": SOURCE_CONTRACT, "source_root": str(source),
        "source_artifacts": list(SOURCE_FILES), "output_artifacts": list(OUTPUT_FILES),
        "scientific_calls": 0, "new_sample_calls": 0,
        "graph_construction_calls": 0, "decoder_calls": 0, "osd_calls": 0,
        "artifact_reads": 0, "source_rows_read": 0, "stop_reason": "",
    }
    summary: dict[str, Any] = {
        "batch_uuid": SOURCE_BATCH_UUID, "contract": SOURCE_CONTRACT,
        "seed_namespace": mrb.SEED_PREFIX,
        "reaggregation_uuid": REAGGREGATION_UUID,
        "reaggregation_contract": CONTRACT,
        "terminal_status": "RUNNING", "holdout_complete": False,
        "control_exact": None, "candidate_exact": None, "delta": None,
        "paired_states": None,
    }
    _write_json(root / "manifest.json", manifest)
    _write_json(root / "summary.json", summary)
    (root / "EXPLORATION_LOG.md").write_text(
        "# MRB additive reaggregation EXPLORE log\n\n"
        "Reaggregation UUID: `%s`; scientific source batch UUID: `%s`.\n\n"
        "Reaggregation contract: `%s`; source scientific contract: `%s`.\n\n"
        "The source batch identity remains attached to the scientific rows; the new UUID "
        "identifies only this derived reader pass. No graph, decoder, OSD, or new sample "
        "calls are permitted.\n" % (REAGGREGATION_UUID, SOURCE_BATCH_UUID,
                                      CONTRACT, SOURCE_CONTRACT),
        encoding="utf-8")

    started = float(now())
    rss_samples: list[int] = []
    rows: list[dict[str, Any]] = []
    source_manifest: dict[str, Any] = {}
    source_manifest_valid = False
    source_rows = 0
    terminal = "SOURCE_STOP"
    stop_reason = ""
    aggregate: dict[str, Any] | None = None

    def checkpoint() -> str:
        value = rss_fn()
        if value is not None:
            rss_samples.append(int(value))
        reasons = []
        if max(float(now()) - started, 0.0) >= MAX_WALL_S:
            reasons.append("reader_wall_cap")
        if value is not None and int(value) >= MAX_RSS_BYTES:
            reasons.append("reader_rss_cap")
        if source_rows > MAX_ROWS:
            reasons.append("source_row_cap")
        return ",".join(reasons)

    def cost() -> dict[str, Any]:
        return {
            "wall_s": max(float(now()) - started, 0.0),
            "max_sampled_rss_bytes": max(rss_samples) if rss_samples else None,
            "rss_sample_count": len(rss_samples),
            "measurement_scope": (
                "time.perf_counter and sampled process RSS during source manifest/CSV "
                "read and reduction; excludes writing the three derived artifacts"),
        }

    try:
        reason = checkpoint()
        missing = [name for name in SOURCE_FILES if not (source / name).is_file()]
        if reason:
            terminal, stop_reason = "RESOURCE_STOP", reason
        elif missing:
            stop_reason = "missing_source_artifacts:" + ",".join(missing)
        else:
            with (source / "manifest.json").open("r", encoding="utf-8") as stream:
                source_manifest = json.load(stream)
            manifest["artifact_reads"] += 1
            _validate_manifest(source_manifest)
            source_manifest_valid = True
            rows = _read_rows(source / "frame_records.csv")
            source_rows = len(rows)
            manifest["artifact_reads"] += 1
            reason = checkpoint()
            if reason:
                terminal, stop_reason = "RESOURCE_STOP", reason
            else:
                complete = _validate_rows(rows)
                aggregate = _reduce(rows, source_manifest, complete)
                reason = checkpoint()
                if reason:
                    terminal, stop_reason = "RESOURCE_STOP", reason
                    aggregate = None
                elif complete:
                    terminal = "REAGGREGATION_COMPLETE"
                else:
                    terminal = "SOURCE_INCOMPLETE"
                    stop_reason = "source_rows_incomplete_or_unpaired"
    except (SourceError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        source_rows = max(source_rows, int(getattr(exc, "rows_read", 0)))
        stop_reason = "%s:%s" % (type(exc).__name__, str(exc))
    except Exception as exc:
        stop_reason = "reader_exception:%s:%s" % (type(exc).__name__, str(exc))

    try:
        error_reason = checkpoint()
    except Exception as exc:
        error_reason = "resource_sample_error:%s" % type(exc).__name__
    if error_reason:
        terminal = "RESOURCE_STOP"
        stop_reason = (stop_reason + "|resource_abort:" + error_reason).strip("|")

    if aggregate is None:
        summary.update({
            "terminal_status": terminal, "classification": "INCOMPLETE",
            "stop_reason": stop_reason, "holdout_complete": False,
            "attempted_decoder_calls": source_rows, "attempted_frame_rows": source_rows,
            "attempted_call_counts": {"pilot": 0, "holdout": source_rows,
                                      "total": source_rows},
            "control_exact": None, "candidate_exact": None, "delta": None,
            "delta_by_graph": None, "paired_states": None,
            "syndrome_consistent_wrong_rows": None,
            "syndrome_consistent_wrong_by_arm": None,
            "actual_syndrome_disclosure_bits": None,
        })
    else:
        summary = aggregate
        summary["stop_reason"] = stop_reason
    measured = cost()
    summary["terminal_status"] = terminal
    summary["reaggregation_cost"] = measured
    summary["source_artifact_provenance"] = {
        "source_root": str(source), "source_batch_uuid": SOURCE_BATCH_UUID,
        "source_contract": SOURCE_CONTRACT,
        "source_manifest_identity_valid": source_manifest_valid,
        "source_csv_used_for_aggregate": source_rows > 0,
        "source_summary_used_for_aggregate": False,
        "source_summary_identity_note": (
            "The retained summary has known inherited damping identity and was not used "
            "for this aggregate"),
        "source_vector_arrays_saved": False, "vector_replay_or_redecoding": False,
    }
    manifest.update({
        "status": terminal, "stop_reason": stop_reason,
        "source_rows_read": source_rows,
        "source_manifest_identity": {
            key: source_manifest.get(key)
            for key in ("batch_uuid", "contract", "seed_namespace")},
        "source_scientific_terminal_status": source_manifest.get("status"),
        "source_science_cost_inherited": summary.get("source_science_cost_inherited"),
        "reaggregation_cost": measured,
    })
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("\nTerminal: `%s`; stop: `%s`; source rows: %d; scientific calls: 0.\n"
                     % (terminal, stop_reason or "none", source_rows))
    return summary


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    if len(mrb.seed_plan()) != 192 or mrb.MAX_CALLS != 384:
        raise AssertionError("retained MRB seed/call plan changed")
    repo = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "source_root": str(repo / SOURCE_ROOT_RELATIVE),
        "writes": 0, "artifact_reads": 0, "source_rows_read": 0,
        "scientific_calls": 0, "graph_construction_calls": 0,
        "decoder_calls": 0, "osd_calls": 0,
        "max_source_rows": MAX_ROWS, "max_wall_s": MAX_WALL_S,
        "max_rss_bytes": MAX_RSS_BYTES,
        "source_batch_uuid": SOURCE_BATCH_UUID,
        "reaggregation_uuid": REAGGREGATION_UUID,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reaggregate retained GF32 MRB rows")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="read retained manifest/CSV and write a derived aggregate")
    mode.add_argument("--dry-run", action="store_true",
                      help="check the fresh output root and frozen limits only")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    result = execute_reaggregation(out_root=args.out_root) if args.execute else dry_run(args.out_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
