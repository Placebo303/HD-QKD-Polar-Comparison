"""Bounded common-seed GF32 degree-profile construction canary."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_degree_probe as degree_probe
from comparison_bench.formal_ir import nonbinary_v10_common as common

CONTRACT = "NBLDPC-GF32-CONSTRUCTION-CANARY-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_construct_a9a18abe"
SEED_NAMESPACE = "gf32-construct-v1"
GRAPH_IDS = tuple(range(2026093901, 2026093907))
PROFILE_ORDER = ("control", "candidate")
PROFILES = degree_probe.PROFILES
ATTEMPTS_PER_GROUP = 8
MAX_GRAPH_CALLS = len(GRAPH_IDS) * ATTEMPTS_PER_GROUP * len(PROFILE_ORDER)
WALL_CAP_S = 180.0
RSS_CAP_BYTES = 4 * 1024 ** 3
RESULT_CAP_BYTES = 10 * 1024 * 1024

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_construction_probe --execute "
    "--out-root workspace/gf32_construct_a9a18abe"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def seed_for(graph_id: int, attempt_j: int) -> int:
    """Return the shared, ordered construction seed for one paired attempt."""
    graph_id, attempt_j = int(graph_id), int(attempt_j)
    if graph_id not in GRAPH_IDS or not 0 <= attempt_j < ATTEMPTS_PER_GROUP:
        raise ValueError("graph ID or paired attempt index is outside the frozen plan")
    if attempt_j == 0:
        return graph_id
    return int(common.v10_seed(
        f"{SEED_NAMESPACE}:{graph_id}:{attempt_j}"))


def attempt_seed_plan() -> list[tuple[int, int, int]]:
    return [(graph_id, attempt_j, seed_for(graph_id, attempt_j))
            for graph_id in GRAPH_IDS
            for attempt_j in range(ATTEMPTS_PER_GROUP)]


def verify_t0() -> dict[str, bool]:
    expected = {
        "control": {
            "n": 128, "m": 52, "edge_count": 256,
            "variable_counts": {2: 128}, "check_counts": {4: 4, 5: 48},
        },
        "candidate": {
            "n": 128, "m": 52, "edge_count": 384,
            "variable_counts": {3: 128}, "check_counts": {7: 32, 8: 20},
        },
    }
    if PROFILE_ORDER != ("control", "candidate"):
        raise AssertionError("frozen profile order changed")
    for profile_id in PROFILE_ORDER:
        profile = PROFILES[profile_id]
        for key, value in expected[profile_id].items():
            if profile.get(key) != value:
                raise AssertionError(f"frozen {profile_id} {key} changed")
        variable_sockets = sum(
            int(degree) * int(count)
            for degree, count in profile["variable_counts"].items())
        check_sockets = sum(
            int(degree) * int(count)
            for degree, count in profile["check_counts"].items())
        if variable_sockets != check_sockets or variable_sockets != int(profile["edge_count"]):
            raise AssertionError(f"frozen {profile_id} socket balance changed")
    plan = attempt_seed_plan()
    if len(plan) != len(GRAPH_IDS) * ATTEMPTS_PER_GROUP or len({x[2] for x in plan}) != len(plan):
        raise AssertionError("construction-seed plan is not fixed and unique")
    if MAX_GRAPH_CALLS != 96:
        raise AssertionError("frozen graph-call cap changed")
    return {"profiles_fixed": True, "socket_balance": True,
            "paired_seed_plan": True, "graph_call_cap": True,
            "no_graph_calls": True}


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError(f"out-root must equal frozen fresh root {expected}")
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    return {
        "status": "DRY_RUN", "out_root": str(root), "t0": verify_t0(),
        "writes": 0, "input_reads": 0, "graph_calls": 0,
        "decoder_calls": 0, "graph_ids": list(GRAPH_IDS),
        "attempts_per_group": ATTEMPTS_PER_GROUP,
        "maximum_graph_calls": MAX_GRAPH_CALLS,
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot write {type(value).__name__} to JSON")


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n"


def _write_json(path: Path, value: Any) -> int:
    payload = _json_text(value).encode("utf-8")
    path.write_bytes(payload)
    return len(payload)


def execute_batch(
        *, out_root: str | Path,
        graph_builder: Callable[[Mapping[str, Any], int], Mapping[str, Any]],
        profile_preflight_fn: Callable[
            [Mapping[str, Any], Mapping[str, Any], int], tuple[bool, Mapping[str, Any]]],
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    """Run paired seed attempts; only a common admitted pair selects a group."""
    if not callable(graph_builder) or not callable(profile_preflight_fn):
        raise ValueError("explicit graph builder and profile preflight callbacks are required")
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    if rss_fn is None:
        rss_fn = degree_probe.d5._rss_bytes

    started = float(now())
    resource_stop_markers: list[str] = []
    rss_samples: list[int] = []
    stop_reason = ""
    terminal_status = "INCOMPLETE"
    attempts: list[dict[str, Any]] = []
    matrices: list[dict[str, Any]] = []
    groups = [{"graph_id": graph_id, "status": "PENDING",
               "attempt_record_indices": [], "selected_attempt_j": None,
               "selected_seed": None, "selected_matrix_indices": None}
              for graph_id in GRAPH_IDS]
    identity = {"batch_uuid": BATCH_UUID, "contract": CONTRACT,
                "seed_namespace": SEED_NAMESPACE}
    manifest: dict[str, Any] = {
        **identity, "track": "EXPLORE", "status": "RUNNING",
        "classification": "INCOMPLETE", "complete_all_groups": None,
        "profile_order": list(PROFILE_ORDER),
        "profiles": [dict(PROFILES[name]) for name in PROFILE_ORDER],
        "graph_ids": list(GRAPH_IDS), "attempts_per_group": ATTEMPTS_PER_GROUP,
        "maximum_graph_calls": MAX_GRAPH_CALLS,
        "wall_cap_s": WALL_CAP_S, "sampled_rss_cap_bytes": RSS_CAP_BYTES,
        "result_cap_bytes": RESULT_CAP_BYTES, "exact_command": command,
        "graph_calls": 0, "matrix_count": 0, "selected_group_count": 0,
        "exhausted_group_count": 0, "resource_stop_markers": [],
        "stop_reason": None, "t0": t0,
    }
    construction_data: dict[str, Any] = {
        **identity, "terminal_status": "RUNNING", "classification": "INCOMPLETE",
        "complete_all_groups": None, "attempt_count": 0,
        "groups": groups, "attempts": attempts, "matrices": matrices,
        "resource_stop_markers": resource_stop_markers, "stop_reason": None,
    }
    log_lines = [
        "# GF32 common-paired construction canary",
        f"Batch UUID: `{BATCH_UUID}`. Contract: `{CONTRACT}`. Seed namespace: `{SEED_NAMESPACE}`.",
        "Construction-only: no labels, decoder calls, or performance screen.",
    ]

    def add_stop(reason: str, *, resource: bool = False) -> None:
        nonlocal stop_reason, terminal_status
        if resource and reason not in resource_stop_markers:
            resource_stop_markers.append(reason)
        if not stop_reason:
            stop_reason = reason
        terminal_status = "STOP"

    def resource_check(stage: str) -> tuple[str, int | None]:
        try:
            elapsed = max(float(now()) - started, 0.0)
        except Exception as exc:
            reason = f"clock_monitor_exception_{stage}:{type(exc).__name__}:{exc}"
            add_stop(reason, resource=True)
            return reason, None
        if elapsed >= WALL_CAP_S:
            reason = f"total_wall_cap_{stage}:{elapsed}"
            add_stop(reason, resource=True)
            return reason, None
        try:
            rss = rss_fn()
        except Exception as exc:
            reason = f"rss_monitor_exception_{stage}:{type(exc).__name__}:{exc}"
            add_stop(reason, resource=True)
            return reason, None
        if rss is not None:
            rss = int(rss)
            rss_samples.append(rss)
        if rss is not None and int(rss) >= RSS_CAP_BYTES:
            reason = f"rss_cap_{stage}:{int(rss)}"
            add_stop(reason, resource=True)
            return reason, rss
        return "", rss

    def save_attempt(profile_id: str, graph_id: int, attempt_j: int,
                     construction_seed: int, record: Mapping[str, Any],
                     elapsed_s: float | None, rss_b: int | None,
                     status: str, admitted: bool,
                     preflight: Any, failure_reason: str) -> int:
        matrix_index: int | None = None
        raw_h = record.get("H")
        if raw_h is not None:
            h = np.asarray(raw_h)
            matrix_index = len(matrices)
            matrices.append({
                "matrix_index": matrix_index, "graph_id": graph_id,
                "attempt_j": attempt_j, "construction_seed": construction_seed,
                "profile_id": profile_id, "H": h,
                "structure": record.get("structure"),
            })
        row = {
            "attempt_index": len(attempts), "graph_id": graph_id,
            "attempt_j": attempt_j, "construction_seed": construction_seed,
            "profile_id": profile_id, "status": status,
            "admitted": admitted, "elapsed_s": elapsed_s, "rss_b": rss_b,
            "failure_reason": failure_reason,
            "preflight": preflight, "matrix_index": matrix_index,
            "constructor_record": {key: value for key, value in record.items()
                                   if key != "H"},
        }
        attempts.append(row)
        groups[GRAPH_IDS.index(graph_id)]["attempt_record_indices"].append(
            row["attempt_index"])
        return matrix_index if matrix_index is not None else -1

    def write_outputs() -> dict[str, Any]:
        try:
            elapsed = max(float(now()) - started, 0.0)
        except Exception as exc:
            elapsed = None
            add_stop(f"clock_monitor_exception_after_attempts:{type(exc).__name__}:{exc}",
                     resource=True)
        selected = sum(group["status"] == "SELECTED" for group in groups)
        exhausted = sum(group["status"] == "EXHAUSTED" for group in groups)
        complete = terminal_status != "STOP" and all(
            group["status"] in ("SELECTED", "EXHAUSTED") for group in groups)
        classification = (
            "INCOMPLETE" if not complete else
            "CONSTRUCTION_EXHAUSTED" if exhausted else "CONSTRUCTION_FEASIBLE")
        manifest.update({
            "status": terminal_status, "classification": classification,
            "complete_all_groups": complete if complete else None,
            "graph_calls": len(attempts), "matrix_count": len(matrices),
            "selected_group_count": selected, "exhausted_group_count": exhausted,
            "batch_wall_s": elapsed, "resource_stop_markers": list(resource_stop_markers),
            "sampled_rss_max_bytes": max(rss_samples, default=None),
            "sampled_rss_count": len(rss_samples),
            "stop_reason": stop_reason or None,
        })
        construction_data.update({
            "terminal_status": terminal_status, "classification": classification,
            "complete_all_groups": complete if complete else None,
            "attempt_count": len(attempts), "matrix_count": len(matrices),
            "groups": groups, "attempts": attempts, "matrices": matrices,
            "resource_stop_markers": list(resource_stop_markers),
            "stop_reason": stop_reason or None,
        })
        log_lines.append(
            f"terminal={terminal_status} classification={classification} "
            f"calls={len(attempts)} selected={selected} exhausted={exhausted} "
            f"stop_reason={stop_reason or 'none'}")
        log_text = "\n\n".join(log_lines) + "\n"
        result_bytes = (len(_json_text(manifest).encode("utf-8"))
                        + len(_json_text(construction_data).encode("utf-8"))
                        + len(log_text.encode("utf-8")))
        if result_bytes > RESULT_CAP_BYTES and not stop_reason:
            add_stop(f"result_size_cap:{result_bytes}", resource=True)
            classification, complete = "INCOMPLETE", False
            manifest.update({"status": terminal_status, "classification": "INCOMPLETE",
                             "complete_all_groups": None,
                             "resource_stop_markers": list(resource_stop_markers),
                             "stop_reason": stop_reason})
            construction_data.update({"terminal_status": terminal_status,
                                      "classification": "INCOMPLETE",
                                      "complete_all_groups": None,
                                      "resource_stop_markers": list(resource_stop_markers),
                                      "stop_reason": stop_reason})
            log_lines.append(f"resource_stop={stop_reason}")
            log_text = "\n\n".join(log_lines) + "\n"
        _write_json(root / "constructions.json", construction_data)
        _write_json(root / "manifest.json", manifest)
        (root / "EXPLORATION_LOG.md").write_text(log_text, encoding="utf-8")
        return {
            **identity, "status": terminal_status, "classification": classification,
            "complete_all_groups": complete if complete else None,
            "graph_calls": len(attempts), "matrix_count": len(matrices),
            "selected_group_count": selected, "exhausted_group_count": exhausted,
            "batch_wall_s": elapsed, "resource_stop_markers": resource_stop_markers,
            "sampled_rss_max_bytes": max(rss_samples, default=None),
            "sampled_rss_count": len(rss_samples),
            "stop_reason": stop_reason or None,
        }

    root.mkdir(parents=True)
    _write_json(root / "manifest.json", manifest)
    _write_json(root / "constructions.json", construction_data)
    (root / "EXPLORATION_LOG.md").write_text("\n\n".join(log_lines) + "\n",
                                             encoding="utf-8")

    try:
        for group in groups:
            graph_id = int(group["graph_id"])
            for attempt_j in range(ATTEMPTS_PER_GROUP):
                construction_seed = seed_for(graph_id, attempt_j)
                pair_results: dict[str, tuple[bool, int]] = {}
                for profile_id in PROFILE_ORDER:
                    reason, _ = resource_check(
                        f"before_graph_{graph_id}_j{attempt_j}_{profile_id}")
                    if reason:
                        group["status"] = "INCOMPLETE"
                        raise StopBatch(reason)
                    before = float(now())
                    record: Any = {}
                    try:
                        record = graph_builder(
                            dict(PROFILES[profile_id]), construction_seed)
                        if not isinstance(record, Mapping):
                            raise TypeError("graph_builder must return a mapping")
                        raw_status = record.get("status")
                        matrix = record.get("H")
                        preflight: Any = None
                        admitted = False
                        failure_reason = str(record.get("failure_reason", ""))
                        if raw_status == "construction_failed":
                            status = "construction_failed"
                            failure_reason = failure_reason or "construction_failed"
                        elif raw_status == "ok":
                            ok, preflight = profile_preflight_fn(
                                PROFILES[profile_id], record, construction_seed)
                            admitted = ok is True
                            status = "admitted" if admitted else "admission_failed"
                            if not admitted:
                                failure_reason = failure_reason or "profile_preflight_failed"
                        else:
                            raise ValueError(f"unexpected constructor status {raw_status!r}")
                        elapsed_s = max(float(now()) - before, 0.0)
                        # Store the real matrix/record before the post-call resource gate.
                        matrix_index = save_attempt(
                            profile_id, graph_id, attempt_j, construction_seed,
                            record, elapsed_s, None, status, admitted,
                            preflight, failure_reason)
                        pair_results[profile_id] = (admitted, matrix_index)
                        log_lines.append(
                            f"graph_id={graph_id} attempt_j={attempt_j} "
                            f"seed={construction_seed} profile={profile_id} "
                            f"status={status} admitted={admitted} "
                            f"failure={failure_reason or 'none'}")
                    except Exception as exc:
                        elapsed_s = None
                        try:
                            elapsed_s = max(float(now()) - before, 0.0)
                        except Exception:
                            pass
                        error_record = record if isinstance(record, Mapping) else {}
                        save_attempt(
                            profile_id, graph_id, attempt_j, construction_seed,
                            error_record, elapsed_s, None, "unexpected_error", False,
                            None, f"{type(exc).__name__}:{exc}")
                        reason = f"unexpected_constructor_error:{profile_id}:{type(exc).__name__}:{exc}"
                        add_stop(reason)
                        group["status"] = "INCOMPLETE"
                        log_lines.append(reason)
                        _, rss_b = resource_check(
                            f"after_error_{graph_id}_j{attempt_j}_{profile_id}")
                        attempts[-1]["rss_b"] = rss_b
                        raise StopBatch(reason)

                    reason, rss_b = resource_check(
                        f"after_graph_{graph_id}_j{attempt_j}_{profile_id}")
                    attempts[-1]["rss_b"] = rss_b
                    if reason:
                        group["status"] = "INCOMPLETE"
                        raise StopBatch(reason)
                if all(pair_results[name][0] for name in PROFILE_ORDER):
                    group.update({
                        "status": "SELECTED", "selected_attempt_j": attempt_j,
                        "selected_seed": construction_seed,
                        "selected_matrix_indices": {
                            name: pair_results[name][1] for name in PROFILE_ORDER},
                    })
                    break
            else:
                group["status"] = "EXHAUSTED"
        terminal_status = "COMPLETE"
    except StopBatch:
        pass
    except Exception as exc:
        reason = f"unexpected_probe_error:{type(exc).__name__}:{exc}"
        add_stop(reason)
        log_lines.append(reason)
    return write_outputs()


class StopBatch(Exception):
    pass


def _bind_production() -> dict[str, Any]:
    """Reuse the accepted D10 graph builder and degree-profile preflight only."""
    bindings = degree_probe._bind_production()
    return {"graph_builder": bindings["graph_builder"],
            "profile_preflight_fn": degree_probe.profile_preflight}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF32 common-paired degree-profile construction canary")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true",
                       help="run the frozen bounded constructor canary")
    modes.add_argument("--dry-run", action="store_true",
                       help="check constants and fresh output root without writes")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(out_root=args.out_root, command=COMMAND,
                               **_bind_production())
    print(json.dumps(result, sort_keys=True, default=_json_default))
    return result


if __name__ == "__main__":
    main()
