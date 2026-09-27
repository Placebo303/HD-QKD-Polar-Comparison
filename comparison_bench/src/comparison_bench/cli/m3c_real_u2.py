"""M3-c real 2M u2 diagnostic (one frozen graph arm per invocation)."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.cli import m0_realframe_runner as m0
from comparison_bench.src.comparison_bench.cli import m3b_paired_synth as m3b

SOURCE = "2M"
DATASET = "T2-2M"
N = 1024
N_FRAMES = 383
N_PAIRS_TOTAL = 982182
N_PAIRS_EVAL = 392721
EVAL_FIRST_FRAME = 8771980
EVAL_REMAINDER = 529
WALL_CAP_S = 5400.0
INTERNAL_STOP_S = 5280.0
WALL_RESERVE_S = WALL_CAP_S - INTERNAL_STOP_S
PER_DECODE_CAP_S = 300.0
RSS_CAP_GIB = 4.0
ROOT_PREFIX = "workspace/m3c_real_u2_20260926/"
EXECUTION_LOG_NAME = "execution.jsonl"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
THREAD_ENV = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
              "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")
PRIOR_PATH = Path(m0.BUNDLE_ROOT, m0.SOURCES[SOURCE]["bundle"])

ARMS: dict[str, dict[str, Any]] = {
    "M3C-R1": {
        "graph_arm": "M3B-R1",
        "graph": Path("workspace/m3a_nested_200p8_20260926/arm1.json"),
        "base_seed": 2026092001,
        "extension_seed": 2026096801,
        "root": "workspace/m3c_real_u2_20260926/R1_5af1c76e",
    },
    "M3C-R2": {
        "graph_arm": "M3B-R2",
        "graph": Path("workspace/m3a_nested_200p8_20260926/arm2.json"),
        "base_seed": 2026092011,
        "extension_seed": 2026096811,
        "root": "workspace/m3c_real_u2_20260926/R2_4e8bc319",
    },
}

CSV_COLUMNS = [
    "arm", "superframe", "stage1_exact", "stage1_undetected",
    "stage1_status", "stage1_iterations", "stage1_wall_s", "stage1_over_cap",
    "stage2_attempted", "stage2_exact", "stage2_undetected",
    "stage2_status", "stage2_iterations", "stage2_wall_s", "stage2_over_cap",
    "final_u2_exact", "full10_match", "raw_symbol_errors",
    "u2_symbol_errors",
]


class M3CError(ValueError):
    """Frozen M3-c input, output-root or decoder-contract violation."""


class _DecodeDeadline(BaseException):
    """Internal hard-stop signal for one decoder call or the arm wall cap."""

    def __init__(self, kind: str, elapsed_s: float):
        super().__init__(kind)
        self.kind = kind
        self.elapsed_s = elapsed_s


def _append_execution_event(path: str | Path, event: str,
                            **fields: Any) -> None:
    record = {"time_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
              "event": event, **fields}
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def _prepare_execution_log(arm: str, root_prefix: str = ROOT_PREFIX) -> Path:
    """Create the fresh family log for R1 or append R2 to its existing log."""
    _arm_spec(arm)
    family_root = Path(root_prefix)
    log_path = family_root / EXECUTION_LOG_NAME
    if arm == "M3C-R1":
        family_root.mkdir(parents=True, exist_ok=False)
        with log_path.open("x", encoding="utf-8"):
            pass
    elif not family_root.is_dir() or not log_path.is_file():
        raise M3CError("M3C-R2 requires the existing M3C family execution log")
    _append_execution_event(log_path, "ARM_START", arm=arm,
                            wall_cap_s=WALL_CAP_S,
                            internal_stop_s=INTERNAL_STOP_S,
                            wall_reserve_s=WALL_RESERVE_S)
    return log_path


def _call_with_deadline(decode_fn: Callable[..., dict[str, Any]],
                        code: dict[str, Any], a: np.ndarray, b: np.ndarray,
                        bundle: dict[str, Any], m: int, *,
                        remaining_wall_s: float) -> tuple[dict[str, Any], float]:
    """Run one decode with a SIGALRM cap; intended for the WSL CLI main thread."""
    if not hasattr(signal, "setitimer") or not hasattr(signal, "ITIMER_REAL"):
        raise M3CError("hard decoder timeout requires POSIX signal.setitimer")
    old_delay, old_interval = signal.getitimer(signal.ITIMER_REAL)
    if old_delay > 0 or old_interval > 0:
        raise M3CError("an existing ITIMER_REAL timer prevents a bounded decoder call")
    if remaining_wall_s <= 0:
        raise _DecodeDeadline("wall", 0.0)
    timeout_s = min(PER_DECODE_CAP_S, remaining_wall_s)
    kind = "wall" if remaining_wall_s <= PER_DECODE_CAP_S else "decode"
    call_started = time.monotonic()

    def on_alarm(_signum, _frame):
        raise _DecodeDeadline(kind, max(0.0, time.monotonic() - call_started))

    old_handler = signal.signal(signal.SIGALRM, on_alarm)
    try:
        signal.setitimer(signal.ITIMER_REAL, timeout_s)
        result = decode_fn(code, a, b, bundle, m)
        return result, max(0.0, time.monotonic() - call_started)
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
        finally:
            signal.signal(signal.SIGALRM, old_handler)


def _require_hard_timeout_support() -> None:
    if (not hasattr(signal, "setitimer") or not hasattr(signal, "ITIMER_REAL")
            or threading.current_thread() is not threading.main_thread()):
        raise M3CError("hard decoder timeout requires POSIX setitimer on the main thread")
    delay, interval = signal.getitimer(signal.ITIMER_REAL)
    if delay > 0 or interval > 0:
        raise M3CError("an existing ITIMER_REAL timer prevents a bounded decoder call")


def _arm_spec(arm: str) -> dict[str, Any]:
    if arm not in ARMS:
        raise M3CError(f"arm must be exactly M3C-R1 or M3C-R2 (got {arm!r})")
    return ARMS[arm]


def _check_root(root: str, arm: str, root_prefix: str = ROOT_PREFIX) -> None:
    spec = _arm_spec(arm)
    norm_root = str(root).replace("\\", "/")
    norm_prefix = str(root_prefix).replace("\\", "/")
    if not norm_root.startswith(norm_prefix):
        raise M3CError(f"root must start with {norm_prefix!r}")
    if Path(str(root)).resolve().parent != Path(root_prefix).resolve():
        raise M3CError(f"resolved root must be a direct child of {norm_prefix!r}")
    expected_arm_prefix = "R1_" if arm == "M3C-R1" else "R2_"
    if not Path(str(root)).name.startswith(expected_arm_prefix):
        raise M3CError(f"root name must start with {expected_arm_prefix}")
    if any(part in FORBIDDEN_ROOT_PARTS for part in Path(norm_root).parts):
        raise M3CError(f"root is under a protected output tree: {root}")
    if root_prefix == ROOT_PREFIX and str(root).replace("\\", "/") != spec["root"]:
        raise M3CError(f"root must equal the frozen per-arm root {spec['root']}")
    if os.path.exists(root):
        raise M3CError(f"root is not fresh: {root}")


def _file_identity(path: str | Path) -> dict[str, Any]:
    st = Path(path).stat()
    mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
    return {"path": str(path), "size_bytes": int(st.st_size),
            "mtime_utc": mtime.isoformat().replace("+00:00", "Z")}


def _series_frames(series: dict[str, Any]) -> tuple[np.ndarray, np.ndarray,
                                                    list[tuple[np.ndarray, np.ndarray]]]:
    if series.get("dataset") != DATASET:
        raise M3CError(f"real-series dataset must be {DATASET} (got {series.get('dataset')!r})")
    if series.get("ttbin") is None:
        raise M3CError("M0 real-series result lacks its base ttbin member path")
    if Path(str(series["ttbin"])).name != "Type2_2M_3s_2026-01-21_183657.ttbin":
        raise M3CError("M0 real-series base member is not the frozen 2M ttbin")
    if int(series.get("offset_ps", -1)) != 50:
        raise M3CError("M0 real-series 2M alignment offset differs from the frozen +50 ps")
    if int(series.get("n_pairs_total", -1)) != N_PAIRS_TOTAL:
        raise M3CError("M0 2M total pair count differs from the frozen 982182")
    if int(series.get("n_pairs_eval", -1)) != N_PAIRS_EVAL:
        raise M3CError("M0 2M eval pair count differs from the frozen 392721")
    if int(series.get("eval_first_frame", -1)) != EVAL_FIRST_FRAME:
        raise M3CError("M0 2M first eval frame differs from the frozen 8771980")
    a = np.asarray(series.get("a"))
    b = np.asarray(series.get("b"))
    if a.ndim != 1 or b.ndim != 1 or a.size != b.size or a.size != N_PAIRS_EVAL:
        raise M3CError("M0 2M eval arrays must each contain the frozen 392721 symbols")
    if not np.issubdtype(a.dtype, np.integer) or not np.issubdtype(b.dtype, np.integer):
        raise M3CError("M0 2M eval symbols must be integer arrays")
    if (np.any(a < 0) or np.any(a > 1023)
            or np.any(b < 0) or np.any(b > 1023)):
        raise M3CError("M0 2M symbols must remain in the frozen 10-bit range")
    blocks = m0.superframes(a, b, N)
    remainder = int(a.size - N * len(blocks))
    if len(blocks) != N_FRAMES or remainder != EVAL_REMAINDER:
        raise M3CError("M0 2M VAL+HOLD frame count/remainder differs from 383 + 529")
    return a, b, blocks


def _validate_bundle(bundle: dict[str, Any]) -> str:
    if bundle.get("source") != SOURCE:
        raise M3CError("prior bundle source must be the same-source 2M R1-TRAIN bundle")
    if Path(str(bundle.get("path", ""))) != PRIOR_PATH:
        raise M3CError(f"prior bundle path differs from frozen M0 2M bundle {PRIOR_PATH}")
    expected_shapes = {"g1": (32, 1024), "g2": (32, 32, 1024), "p_b": (1024,)}
    for name, expected in expected_shapes.items():
        if np.asarray(bundle.get(name)).shape != expected:
            raise M3CError(f"same-source prior {name} shape differs from {expected}")
    return "same-source R1-TRAIN 2M prior; no eval refit"


def _graph_codes(data: dict[str, Any], arm: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    spec = _arm_spec(arm)
    graph_arm = spec["graph_arm"]
    pins = m3b.validate_graph_artifact(data, graph_arm)
    if (pins["construction_seed"] != spec["base_seed"]
            or pins["extension_seed"] != spec["extension_seed"]):
        raise M3CError("saved graph seeds differ from the M3-c arm pins")
    base = [(int(r), int(c), int(v)) for r, c, v in data["base_triples"]]
    full = [(int(r), int(c), int(v)) for r, c, v in data["triples"]]
    if full[:len(base)] != base or len(base) != 2048 or len(full) != 2128:
        raise M3CError("saved graph does not have the frozen 200-row prefix and 208-row full code")
    base_code = {"n": N, "m": 200, "triples": base,
                 "graph_source": "accepted M3-a stored nested graph"}
    full_code = {"n": N, "m": 208, "triples": full,
                 "graph_source": "accepted M3-a stored nested graph"}
    return base_code, full_code, pins


def _resource_stop(*, started: float, clock: Callable[[], float],
                   rss_fn: Callable[[], float], peak: list[float]) -> str | None:
    current = float(rss_fn())
    peak[0] = max(peak[0], current)
    if current >= RSS_CAP_GIB:
        return "FAIL(budget-rss)"
    if clock() - started >= INTERNAL_STOP_S:
        return "INCOMPLETE-wall"
    return None


def _as_bool(out: dict[str, Any], key: str) -> bool:
    value = out.get(key)
    if not isinstance(value, (bool, np.bool_)):
        raise M3CError(f"decoder output lacks boolean {key}")
    return bool(value)


def _final_exact(row: dict[str, Any]) -> bool | None:
    stage1 = row.get("stage1_exact")
    if stage1 is True:
        return True
    if stage1 is False and row.get("stage2_attempted") is True:
        stage2 = row.get("stage2_exact")
        return bool(stage2) if isinstance(stage2, (bool, np.bool_)) else None
    return None


def _summary(*, arm: str, verdict: str, stop_reason: str | None,
             rows: list[dict[str, Any]], provenance: dict[str, Any],
             t_start: float, clock: Callable[[], float], rss_peak: float,
             decoder_calls: int) -> dict[str, Any]:
    stage1_successes = sum(row.get("stage1_exact") is True for row in rows)
    stage1_failures = sum(row.get("stage1_exact") is False for row in rows)
    stage1_undetected = sum(row.get("stage1_undetected") is True for row in rows)
    stage2_rows = [row for row in rows if row.get("stage2_attempted") is True]
    attempted = len(stage2_rows)
    rescued = sum(row.get("stage2_exact") is True for row in stage2_rows)
    stage2_undetected = sum(row.get("stage2_undetected") is True for row in stage2_rows)
    final = [_final_exact(row) for row in rows]
    processed_n = sum(value is not None for value in final)
    final_successes = sum(value is True for value in final)
    final_failures_observed = sum(value is False for value in final)
    final_unknown = sum(value is None for value in final)
    complete = verdict == "COMPLETE"
    out: dict[str, Any] = {
        "arm": arm,
        "source": SOURCE,
        "verdict": verdict,
        "stop_reason": stop_reason,
        "processed_n": processed_n,
        "denominator_target": N_FRAMES,
        "stage1_successes_observed": stage1_successes,
        "stage1_failures_observed": stage1_failures,
        "undetected_stage1": stage1_undetected,
        "attempted": attempted,
        "rescued": rescued,
        "undetected_stage2": stage2_undetected,
        "final_u2_successes_observed": final_successes,
        "final_u2_failures_observed": final_failures_observed,
        "final_u2_outcomes_unknown": final_unknown,
        "full10_evaluated": sum(
            row.get("full10_match") is not None and _final_exact(row) is True
            for row in rows),
        "full10_mismatches": sum(
            row.get("full10_match") is False and _final_exact(row) is True
            for row in rows),
        "oracle_assisted": True,
        "oracle_trigger": "Stage-1 u2 exact_match is false against Alice a&31",
        "graph_provenance": provenance["graph"],
        "data_provenance": provenance["data"],
        "prior_provenance": provenance["prior"],
        "decoder": {"procedure": "M0/b2f decode_real; cold per stage",
                    "field": "GF(32)", "m_stage1": 200, "m_stage2": 208,
                    "max_iter": 300, "streak": 3,
                    "success": "u2 exact match only"},
        "resource": {"elapsed_s": max(0.0, float(clock() - t_start)),
                     "rss_peak_gib": rss_peak,
                     "wall_cap_s": WALL_CAP_S,
                     "internal_stop_s": INTERNAL_STOP_S,
                     "wall_reserve_s": WALL_RESERVE_S,
                     "per_decode_cap_s": PER_DECODE_CAP_S,
                     "rss_cap_gib": RSS_CAP_GIB,
                     "cpus": 1,
                     "thread_env": {name: os.environ.get(name) for name in THREAD_ENV},
                     "decoder_calls": decoder_calls},
        "m0_context_only": "Historical M0 m=204/208 used different rates and graphs; not a matched comparator.",
        "claim_ceiling": "Two separate absolute u2 diagnostics on the frozen 2M eval frames and these accepted graph instances; oracle-assisted rescue is not deployable verification.",
    }
    if complete:
        if (len(rows) != N_FRAMES or any(row.get("stage1_exact") is None for row in rows)
                or any(row.get("stage2_exact") is None
                       for row in rows if row.get("stage2_attempted") is True)
                or [row.get("superframe") for row in rows] != list(range(N_FRAMES))):
            raise M3CError("COMPLETE result has missing frame or decoder outcomes")
        expected_stage2 = {row["superframe"] for row in rows
                           if row["stage1_exact"] is False}
        attempted_stage2 = {row["superframe"] for row in stage2_rows}
        if attempted_stage2 != expected_stage2:
            raise M3CError("COMPLETE Stage-2 set is not exactly Stage-1 non-exact frames")
        stage1_fer = stage1_failures / N_FRAMES
        final_failures = N_FRAMES - final_successes
        final_fer = final_failures / N_FRAMES
        out.update({
            "denominator": N_FRAMES,
            "stage1_failures": stage1_failures,
            "stage1_wilson95": list(m0.wilson(stage1_failures, N_FRAMES)),
            "stage1_fer": stage1_fer,
            "final_failures": final_failures,
            "final_wilson95": list(m0.wilson(final_failures, N_FRAMES)),
            "final_fer": final_fer,
            "stage2_set_exact": True,
        })
    return out


def _rows_csv(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS,
                            extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _result_markdown(summary: dict[str, Any]) -> str:
    graph = summary["graph_provenance"]
    data = summary["data_provenance"]
    prior = summary["prior_provenance"]
    lines = [
        f"# M3-c oracle-assisted real 2M u2 diagnostic — {summary['arm']}",
        "",
        f"- Verdict: `{summary['verdict']}`; processed {summary['processed_n']}/383 frames; "
        f"stop reason: `{summary['stop_reason']}`.",
        f"- Graph: `{graph['path']}`; seeds {graph['base_seed']} + {graph['extension_seed']}; "
        "accepted stored M3-a graph, 200-row prefix and 208-row full matrix; zero new PEG builds.",
        f"- Data: source 2M, dataset {data['dataset']}, ttbin `{data['ttbin']['path']}`, "
        f"pairs {data['n_pairs_total']} total / {data['n_pairs_eval']} eval; first eval frame "
        f"{data['eval_first_frame']}; 383 complete frames + {data['remainder_symbols']} remainder symbols.",
        f"- Prior: `{prior['file']['path']}`; {prior['role']}.",
        "- Stage-2 is oracle-assisted: attempted only after the Stage-1 u2 output is compared "
        "with Alice's a&31. This is not a deployable verification protocol.",
    ]
    if summary["verdict"] == "COMPLETE":
        lines += [
            f"- Stage-1: failures {summary['stage1_failures']}/383; u2 FER "
            f"{summary['stage1_fer']:.6f}, Wilson 95% {summary['stage1_wilson95']}.",
            f"- Stage-2: attempted {summary['attempted']}, rescued {summary['rescued']}; "
            f"final failures {summary['final_failures']}/383; final u2 FER "
            f"{summary['final_fer']:.6f}, Wilson 95% {summary['final_wilson95']}.",
            f"- Undetected: Stage-1 {summary['undetected_stage1']}; Stage-2 "
            f"{summary['undetected_stage2']}; each remains a failure.",
            f"- Report-only full10 mismatches among final u2 successes: "
            f"{summary['full10_mismatches']}/{summary['full10_evaluated']}; full10 does not alter u2 success.",
        ]
    else:
        lines += [
            f"- Progress only: {summary['processed_n']}/383 rows retained; no accepted FER/Wilson point "
            "or complete Stage-2-set assertion is emitted for this incomplete arm.",
        ]
    lines += [
        f"- Resource: wall {summary['resource']['elapsed_s']:.3f}s / 5400s official cap; "
        f"internal stop {INTERNAL_STOP_S:.0f}s with {WALL_RESERVE_S:.0f}s reserve; peak RSS "
        f"{summary['resource']['rss_peak_gib']:.3f} GiB (cap <4 GiB); decoder calls "
        f"{summary['resource']['decoder_calls']}; one CPU.",
        "- M0 m=204/208 values are provenance context only; they are different-rate, different-graph records.",
        "- Claim ceiling: two separate absolute u2 diagnostics on these graph instances and this 2M eval set; "
        "no cross-arm decision, deployable protocol or broader route claim.",
        "",
    ]
    return "\n".join(lines)


def _write(root: str, files: dict[str, str]) -> None:
    os.makedirs(root, exist_ok=True)
    for name, text in files.items():
        Path(root, name).write_text(text, encoding="utf-8")


def _require_r1_complete(root: str | Path | None = None) -> None:
    """Keep R2 behind the completed R1 arm without reading any source data."""
    result_path = Path(root if root is not None else ARMS["M3C-R1"]["root"]) / "rows.json"
    try:
        saved = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise M3CError(f"R2 requires a readable completed R1 rows.json: {result_path}") from exc
    if not isinstance(saved, dict):
        raise M3CError("R2 requires a valid M3C-R1 result object")
    summary = saved.get("summary", {})
    rows = saved.get("rows", [])
    if not isinstance(summary, dict) or not isinstance(rows, list) \
            or any(not isinstance(row, dict) for row in rows):
        raise M3CError("R2 requires a valid M3C-R1 summary and frame rows")
    if (summary.get("arm") != "M3C-R1" or summary.get("verdict") != "COMPLETE"
            or summary.get("processed_n") != N_FRAMES
            or summary.get("denominator") != N_FRAMES
            or summary.get("stage2_set_exact") is not True
            or len(rows) != N_FRAMES
            or [row.get("superframe") for row in rows] != list(range(N_FRAMES))
            or any(row.get("arm") != "M3C-R1"
                   or not isinstance(row.get("stage1_exact"), bool)
                   or not isinstance(row.get("final_u2_exact"), bool)
                   or row.get("final_u2_exact") is not _final_exact(row)
                   for row in rows)):
        raise M3CError("R2 requires M3C-R1 COMPLETE with 383 final frame dispositions")
    expected_stage2 = {row["superframe"] for row in rows
                       if row["stage1_exact"] is False}
    attempted_stage2 = {row["superframe"] for row in rows
                        if row.get("stage2_attempted") is True}
    if (expected_stage2 != attempted_stage2
            or any(row.get("stage2_exact") is None
                   for row in rows if row.get("stage2_attempted") is True)):
        raise M3CError("R2 requires a COMPLETE R1 result with the exact Stage-2 set")


def run_m3c_arm(*, arm: str, root: str,
                series_fn: Callable[[str], dict[str, Any]],
                bundle_fn: Callable[[str], dict[str, Any]],
                graph_fn: Callable[[str | Path], dict[str, Any]],
                decode_fn: Callable[[dict[str, Any], np.ndarray, np.ndarray,
                                     dict[str, Any], int], dict[str, Any]],
                stat_fn: Callable[[str | Path], dict[str, Any]],
                rss_fn: Callable[[], float],
                writer: Callable[[str, dict[str, str]], None],
                clock: Callable[[], float],
                root_prefix: str = ROOT_PREFIX,
                event_fn: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Injected execution core; the production CLI supplies M0 I/O and decoder."""
    spec = _arm_spec(arm)
    _check_root(root, arm, root_prefix)
    started = clock()

    series = series_fn(SOURCE)
    a_all, b_all, blocks = _series_frames(series)
    bundle = bundle_fn(SOURCE)
    prior_role = _validate_bundle(bundle)
    graph_data = graph_fn(spec["graph"])
    base_code, full_code, graph_pins = _graph_codes(graph_data, arm)

    data_provenance = {
        "source": SOURCE,
        "dataset": series["dataset"],
        "ttbin": stat_fn(series["ttbin"]),
        "offset_ps": int(series["offset_ps"]),
        "n_pairs_total": int(series["n_pairs_total"]),
        "n_pairs_eval": int(series["n_pairs_eval"]),
        "eval_first_frame": int(series["eval_first_frame"]),
        "n_frames": len(blocks),
        "remainder_symbols": int(a_all.size - N * len(blocks)),
        "eval_order": "M0 VAL+HOLD loader order; consecutive non-overlapping 1024-symbol frames",
    }
    prior_provenance = {
        "source": bundle["source"],
        "role": prior_role,
        "file": stat_fn(bundle["path"]),
        "shapes": {key: list(np.asarray(bundle[key]).shape)
                   for key in ("g1", "g2", "p_b")},
    }
    graph_provenance = {
        **graph_pins,
        "base_seed": graph_pins["construction_seed"],
        "path": stat_fn(spec["graph"])["path"],
        "file_size_bytes": stat_fn(spec["graph"])["size_bytes"],
        "mtime_utc": stat_fn(spec["graph"])["mtime_utc"],
        "source": "accepted M3-a stored artifact; no new construction",
    }
    provenance = {"graph": graph_provenance, "data": data_provenance,
                  "prior": prior_provenance}

    rows: list[dict[str, Any]] = []
    verdict = "RUNNING"
    stop_reason: str | None = None
    rss_peak = [0.0]
    decoder_calls = [0]

    def emit(event: str, **fields: Any) -> None:
        if event_fn is not None:
            event_fn({"time_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                      "event": event, "arm": arm, **fields})

    def current_summary() -> dict[str, Any]:
        return _summary(arm=arm, verdict=verdict, stop_reason=stop_reason,
                        rows=rows, provenance=provenance, t_start=started,
                        clock=clock, rss_peak=rss_peak[0],
                        decoder_calls=decoder_calls[0])

    def flush() -> None:
        summary = current_summary()
        files = {
            f"M3C_RESULT_{arm}.md": _result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": _rows_csv(rows),
            "stdout_resource.json": json.dumps({
                "arm": arm, "verdict": verdict,
                "resource": summary["resource"],
            }, indent=1, sort_keys=True),
        }
        writer(root, files)
        if verdict != "RUNNING":
            emit("TERMINAL", verdict=verdict, stop_reason=stop_reason,
                 processed_n=summary["processed_n"],
                 decoder_calls=decoder_calls[0], wall_cap_s=WALL_CAP_S,
                 internal_stop_s=INTERNAL_STOP_S,
                 wall_reserve_s=WALL_RESERVE_S)

    def stop_for_resources() -> str | None:
        return _resource_stop(started=started, clock=clock, rss_fn=rss_fn,
                              peak=rss_peak)

    emit("INPUTS_VALIDATED", frame_count=len(blocks), graph_arm=spec["graph_arm"])

    # Stage-1: all 383 frames, cold, on the exact stored 200-row prefix.
    for index, (a, b) in enumerate(blocks):
        stop = stop_for_resources()
        if stop:
            verdict, stop_reason = stop, stop
            flush()
            return current_summary()
        t0 = clock()
        decoder_calls[0] += 1
        emit("DECODE_START", stage=1, superframe=index, m=200,
             call_number=decoder_calls[0])
        try:
            remaining = INTERNAL_STOP_S - max(0.0, clock() - started)
            out, actual_dt = _call_with_deadline(
                decode_fn, base_code, a, b, bundle, 200,
                remaining_wall_s=remaining)
            exact = _as_bool(out, "exact_match")
            reconstruction_ok = bool(out.get("reconstruction_ok", False))
            undetected = bool(not exact and reconstruction_ok)
            full10 = _as_bool(out, "full10_match") if exact else None
            status = out.get("status", "ok")
            iterations = out.get("iterations")
        except _DecodeDeadline as exc:
            dt = max(0.0, clock() - t0, exc.elapsed_s)
            overrun = exc.kind == "decode"
            rows.append({"arm": arm, "superframe": index,
                         "stage1_exact": None, "stage1_undetected": False,
                         "stage1_status": "timeout", "stage1_error":
                         f"hard {exc.kind} deadline after {dt:.6f} s",
                         "stage1_iterations": None, "stage1_wall_s": dt,
                         "stage1_over_cap": overrun,
                         "stage2_attempted": False, "stage2_exact": None,
                         "stage2_undetected": False, "stage2_status": None,
                         "stage2_iterations": None, "stage2_wall_s": None,
                         "stage2_over_cap": False,
                         "final_u2_exact": None, "full10_match": None,
                         "raw_symbol_errors": int(np.count_nonzero(a != b)),
                         "u2_symbol_errors": int(np.count_nonzero((a & 31) != (b & 31)))})
            verdict = "INCOMPLETE-wall" if exc.kind == "wall" else "INCOMPLETE-decode-cap"
            stop_reason = f"Stage-1 hard {exc.kind} deadline after {dt:.6f} s"
            emit("DECODE_TIMEOUT", stage=1, superframe=index, elapsed_s=dt,
                 deadline=exc.kind)
            flush()
            return current_summary()
        except Exception as exc:
            dt = max(0.0, clock() - t0)
            rows.append({"arm": arm, "superframe": index,
                         "stage1_exact": None, "stage1_undetected": False,
            "stage1_status": "error", "stage1_error":
                         f"{type(exc).__name__}: {exc}",
                         "stage1_iterations": None, "stage1_wall_s": dt,
                         "stage1_over_cap": dt > PER_DECODE_CAP_S,
                         "stage2_attempted": False, "stage2_exact": None,
                         "stage2_undetected": False, "stage2_status": None,
                         "stage2_iterations": None, "stage2_wall_s": None,
                         "stage2_over_cap": False,
                         "final_u2_exact": None, "full10_match": None,
                         "raw_symbol_errors": int(np.count_nonzero(a != b)),
                         "u2_symbol_errors": int(np.count_nonzero((a & 31) != (b & 31)))})
            overrun = dt > PER_DECODE_CAP_S
            resource_stop = stop_for_resources()
            verdict = "INCOMPLETE-decode-cap" if overrun else (resource_stop or "INCOMPLETE-error")
            stop_reason = ("Stage-1 decoder call exceeded 300 s" if overrun else
                           (resource_stop or "stage1 decoder/output error"))
            emit("DECODE_ERROR", stage=1, superframe=index, elapsed_s=dt,
                 error=f"{type(exc).__name__}: {exc}")
            flush()
            return current_summary()
        dt = max(0.0, clock() - t0, actual_dt)
        overrun = dt > PER_DECODE_CAP_S
        row = {
            "arm": arm,
            "superframe": index,
            "stage1_exact": exact,
            "stage1_undetected": undetected,
            "stage1_status": status,
            "stage1_iterations": iterations,
            "stage1_wall_s": dt,
            "stage1_over_cap": overrun,
            "stage2_attempted": False,
            "stage2_exact": None,
            "stage2_undetected": False,
            "stage2_status": None,
            "stage2_iterations": None,
            "stage2_wall_s": None,
            "stage2_over_cap": False,
            "final_u2_exact": exact if exact else None,
            "full10_match": full10,
            "raw_symbol_errors": int(np.count_nonzero(a != b)),
            "u2_symbol_errors": int(np.count_nonzero((a & 31) != (b & 31))),
        }
        rows.append(row)
        emit("DECODE_RESULT", stage=1, superframe=index, exact=exact,
             elapsed_s=dt, over_cap=overrun)
        resource_stop = stop_for_resources()
        if overrun:
            verdict, stop_reason = "INCOMPLETE-decode-cap", "Stage-1 decoder call exceeded 300 s"
            flush()
            return current_summary()
        if resource_stop:
            verdict, stop_reason = resource_stop, resource_stop
            flush()
            return current_summary()
        flush()

    # Stage-2: exactly the Stage-1 non-exact set, cold, on the full 208 rows.
    stage2_indices = [row["superframe"] for row in rows
                      if row["stage1_exact"] is False]
    for index in stage2_indices:
        row = rows[index]
        a, b = blocks[index]
        stop = stop_for_resources()
        if stop:
            verdict, stop_reason = stop, stop
            flush()
            return current_summary()
        t0 = clock()
        decoder_calls[0] += 1
        row["stage2_attempted"] = True
        emit("DECODE_START", stage=2, superframe=index, m=208,
             call_number=decoder_calls[0])
        try:
            remaining = INTERNAL_STOP_S - max(0.0, clock() - started)
            out, actual_dt = _call_with_deadline(
                decode_fn, full_code, a, b, bundle, 208,
                remaining_wall_s=remaining)
            exact = _as_bool(out, "exact_match")
            reconstruction_ok = bool(out.get("reconstruction_ok", False))
            undetected = bool(not exact and reconstruction_ok)
            full10 = _as_bool(out, "full10_match") if exact else None
            status = out.get("status", "ok")
            iterations = out.get("iterations")
        except _DecodeDeadline as exc:
            dt = max(0.0, clock() - t0, exc.elapsed_s)
            overrun = exc.kind == "decode"
            row.update({"stage2_exact": None, "stage2_undetected": False,
                        "stage2_status": "timeout",
                        "stage2_error": f"hard {exc.kind} deadline after {dt:.6f} s",
                        "stage2_iterations": None, "stage2_wall_s": dt,
                        "stage2_over_cap": overrun, "final_u2_exact": None,
                        "full10_match": None})
            verdict = "INCOMPLETE-wall" if exc.kind == "wall" else "INCOMPLETE-decode-cap"
            stop_reason = f"Stage-2 hard {exc.kind} deadline after {dt:.6f} s"
            emit("DECODE_TIMEOUT", stage=2, superframe=index, elapsed_s=dt,
                 deadline=exc.kind)
            flush()
            return current_summary()
        except Exception as exc:
            dt = max(0.0, clock() - t0)
            overrun = dt > PER_DECODE_CAP_S
            row.update({"stage2_exact": None, "stage2_undetected": False,
                        "stage2_status": "error",
                        "stage2_error": f"{type(exc).__name__}: {exc}",
                        "stage2_iterations": None,
                        "stage2_wall_s": dt, "stage2_over_cap": overrun,
                        "final_u2_exact": None, "full10_match": None})
            resource_stop = stop_for_resources()
            verdict = "INCOMPLETE-decode-cap" if overrun else (resource_stop or "INCOMPLETE-error")
            stop_reason = ("Stage-2 decoder call exceeded 300 s" if overrun else
                           (resource_stop or "stage2 decoder/output error"))
            emit("DECODE_ERROR", stage=2, superframe=index, elapsed_s=dt,
                 error=f"{type(exc).__name__}: {exc}")
            flush()
            return current_summary()
        dt = max(0.0, clock() - t0, actual_dt)
        overrun = dt > PER_DECODE_CAP_S
        row.update({"stage2_exact": exact,
                    "stage2_undetected": undetected,
                    "stage2_status": status,
                    "stage2_iterations": iterations,
                    "stage2_wall_s": dt,
                    "stage2_over_cap": overrun,
                    "final_u2_exact": exact,
                    "full10_match": full10 if exact else None})
        emit("DECODE_RESULT", stage=2, superframe=index, exact=exact,
             elapsed_s=dt, over_cap=overrun)
        resource_stop = stop_for_resources()
        if overrun:
            verdict, stop_reason = "INCOMPLETE-decode-cap", "Stage-2 decoder call exceeded 300 s"
            flush()
            return current_summary()
        if resource_stop:
            verdict, stop_reason = resource_stop, resource_stop
            flush()
            return current_summary()
        flush()

    verdict, stop_reason = "COMPLETE", None
    flush()
    return current_summary()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arm", required=True, choices=tuple(ARMS))
    parser.add_argument("--root", required=True)
    parser.add_argument("--execute-real", action="store_true")
    parser.add_argument("--execution-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not (args.execute_real and args.execution_authorized):
        print("M3C refusal: require both --execute-real and --execution-authorized before any input reads",
              file=sys.stderr)
        return 2
    log_path: Path | None = None
    try:
        _check_root(args.root, args.arm)
        bad_env = [name for name in THREAD_ENV if os.environ.get(name) != "1"]
        if bad_env:
            raise M3CError(f"thread limits must be 1 before reads: {bad_env}")
        _require_hard_timeout_support()
        if args.arm == "M3C-R2":
            _require_r1_complete()
        log_path = _prepare_execution_log(args.arm)
        summary = run_m3c_arm(
            arm=args.arm,
            root=args.root,
            series_fn=m0.load_real_series,
            bundle_fn=m0.load_bundle,
            graph_fn=m3b.read_json,
            decode_fn=m0.decode_real,
            stat_fn=_file_identity,
            rss_fn=m0._rss_gib,
            writer=_write,
            clock=time.monotonic,
            event_fn=lambda record: _append_execution_event(
                log_path, str(record.pop("event")), **record),
        )
        print(json.dumps(summary, indent=1, sort_keys=True, default=str))
        return 0 if summary["verdict"] == "COMPLETE" else 1
    except (M3CError, m0.Refusal, m3b.M3BError, OSError) as exc:
        if log_path is not None:
            _append_execution_event(log_path, "TERMINAL", arm=args.arm,
                                    verdict="REFUSED", stop_reason=str(exc))
        print(f"M3C refusal: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
