"""Selected Stage-1 iteration-cap diagnostic on frozen M3-b synthetic frames.

The execution core is injection-only. Production source binding and decoder
wiring exist only in ``main`` behind both explicit execution flags.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.cli import m3b_paired_synth as m3b
from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_field,
)

__all__ = [
    "M3D_ROOT_PREFIX", "ARMS", "MAX_ITER", "validate_comparator",
    "load_base_graph", "run_m3d_arm", "main",
]

M3D_ROOT_PREFIX = "workspace/m3d_iter250_synth_20260927/"
MAX_ITER = 250
MAX_ARM_WALL_S = 1200
MAX_CALL_WALL_S = 90
MAX_RSS_GIB = 2
SEED_BASE = 2026096401
N_BLOCKS = 240
N = 1024
M_BASE = 200
NONEXACT_WALL_LIMIT = 0.90

ARMS: dict[str, dict[str, Any]] = {
    "M3D-R1": {
        "m3b_arm": "M3B-R1",
        "root": M3D_ROOT_PREFIX + "R1_17b6c2e9",
        "graph": m3b.ARMS["M3B-R1"]["graph"],
        "comparator": Path(
            "workspace/m3b_nested_paired_20260926/"
            "P1S1-R1_73d2f40a/rows.json"),
        "exact_indices": (0, 1, 2, 3, 4, 5, 6, 7),
        "nonexact_indices": (127, 158, 186, 192, 193, 204, 210, 217),
        "baseline_exact_wall_s": 29.0487699548248,
        "baseline_nonexact_wall_s": 516.273374667042,
        "baseline_stage1_failures": 10,
    },
    "M3D-R2": {
        "m3b_arm": "M3B-R2",
        "root": M3D_ROOT_PREFIX + "R2_45ad8f31",
        "graph": m3b.ARMS["M3B-R2"]["graph"],
        "comparator": Path(
            "workspace/m3b_nested_paired_20260926/"
            "P1S1-R2_89ae671c/rows.json"),
        "exact_indices": (0, 1, 3, 4, 5, 6, 7, 8),
        "nonexact_indices": (2, 23, 30, 94, 95, 129, 130, 137),
        "baseline_exact_wall_s": 24.642091246089,
        "baseline_nonexact_wall_s": 573.172282627085,
        "baseline_stage1_failures": 15,
    },
}


class M3DError(ValueError):
    """A frozen M3D input, identity, root, or accounting pin failed."""


class _DecodeDeadline(BaseException):
    """Internal hard stop raised when a single decoder call exceeds its cap."""

    def __init__(self, elapsed_s: float):
        super().__init__("decode")
        self.elapsed_s = elapsed_s


def _require_hard_timeout_support() -> None:
    if (not hasattr(signal, "setitimer")
            or not hasattr(signal, "ITIMER_REAL")
            or threading.current_thread() is not threading.main_thread()):
        raise M3DError(
            "hard decoder timeout requires POSIX signal.setitimer on the main thread")
    delay, interval = signal.getitimer(signal.ITIMER_REAL)
    if delay > 0 or interval > 0:
        raise M3DError(
            "an existing ITIMER_REAL timer prevents a bounded decoder call")


def _call_with_deadline(decode_fn: Callable, construction: dict[str, Any],
                        seed: int, max_iter: int) -> tuple[Any, float]:
    """Run a decoder call under a hard SIGALRM deadline on the WSL CLI thread."""
    _require_hard_timeout_support()
    old_handler = signal.getsignal(signal.SIGALRM)
    old_delay, old_interval = signal.getitimer(signal.ITIMER_REAL)
    call_started = time.monotonic()

    def on_alarm(_signum, _frame):
        raise _DecodeDeadline(max(0.0, time.monotonic() - call_started))

    signal.signal(signal.SIGALRM, on_alarm)
    try:
        signal.setitimer(signal.ITIMER_REAL, MAX_CALL_WALL_S)
        result = decode_fn(construction, seed, max_iter)
        return result, max(0.0, time.monotonic() - call_started)
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.setitimer(signal.ITIMER_REAL, old_delay, old_interval)


def read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def _arm_spec(arm: str) -> dict[str, Any]:
    if arm not in ARMS:
        raise M3DError(f"arm must be exactly M3D-R1 or M3D-R2 (got {arm!r})")
    return ARMS[arm]


def _int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise M3DError(f"{name} must be an integer")
    return value


def _finite_nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise M3DError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise M3DError(f"{name} must be finite and nonnegative")
    return result


def _check_root(root: str, arm: str,
                root_prefix: str = M3D_ROOT_PREFIX) -> None:
    spec = _arm_spec(arm)
    if not root or not root.startswith(root_prefix):
        raise M3DError(f"root must be under the fresh M3D family {root_prefix!r}")
    path = Path(root)
    if path.resolve().parent != Path(root_prefix).resolve():
        raise M3DError("resolved root must be a direct child of the M3D family")
    root_tag = arm.split("-")[-1] + "_"
    if not path.name.startswith(root_tag):
        raise M3DError(f"root name must start with {root_tag!r}")
    if any(part in p1.FORBIDDEN_ROOT_PARTS for part in path.parts):
        raise M3DError(f"root is under a forbidden output tree: {root}")
    if path.exists():
        raise M3DError(f"root already exists; M3D does not overwrite or resume: {root}")
    if root_prefix == M3D_ROOT_PREFIX and root.replace("\\", "/") != spec["root"]:
        raise M3DError(f"root must match the frozen M3D path {spec['root']!r}")


def _selected_indices(spec: dict[str, Any]) -> tuple[tuple[int, str], ...]:
    selected = tuple((idx, "exact") for idx in spec["exact_indices"]) + tuple(
        (idx, "nonexact") for idx in spec["nonexact_indices"])
    if len(selected) != 16 or len({idx for idx, _ in selected}) != 16:
        raise M3DError("frozen selection must contain 16 distinct block indices")
    return selected


def validate_comparator(data: dict[str, Any], arm: str) -> dict[str, Any]:
    """Validate the selected read-only M3-b rows and their pinned wall sums."""
    spec = _arm_spec(arm)
    summary = data.get("summary", {})
    rows = data.get("rows")
    if summary.get("verdict") != "COMPLETE":
        raise M3DError("M3-b comparator is not COMPLETE")
    if summary.get("arm") != spec["m3b_arm"]:
        raise M3DError("M3-b comparator arm identity mismatch")
    if not isinstance(rows, list):
        raise M3DError("M3-b comparator lacks rows")

    stage1: dict[int, dict[str, Any]] = {}
    for row in rows:
        if row.get("stage") != "stage1":
            continue
        idx = _int(row.get("block_idx"), "M3-b block_idx")
        seed = _int(row.get("seed"), "M3-b seed")
        failed = _int(row.get("failed"), "M3-b failed")
        undetected = _int(row.get("undetected"), "M3-b undetected")
        iters = _int(row.get("iters"), "M3-b iterations")
        wall = _finite_nonnegative(row.get("wall_s"), "M3-b wall_s")
        if idx in stage1:
            raise M3DError(f"duplicate M3-b Stage-1 block index {idx}")
        if seed != SEED_BASE + idx:
            raise M3DError(f"M3-b seed does not match block index {idx}")
        if failed not in (0, 1) or undetected not in (0, 1) or iters < 0:
            raise M3DError(f"invalid M3-b Stage-1 row at index {idx}")
        stage1[idx] = {
            "block_idx": idx, "seed": seed,
            "status": row.get("status"), "exact": failed == 0,
            "undetected": undetected, "iterations": iters,
            "wall_s": wall,
        }

    if set(stage1) != set(range(N_BLOCKS)):
        raise M3DError("M3-b comparator must contain all 240 Stage-1 indices")
    failures = sum(not row["exact"] for row in stage1.values())
    if failures != spec["baseline_stage1_failures"]:
        raise M3DError("M3-b Stage-1 failure count differs from frozen baseline")
    for idx in spec["exact_indices"]:
        if not stage1[idx]["exact"]:
            raise M3DError(f"selected exact baseline block {idx} is nonexact")
    for idx in spec["nonexact_indices"]:
        if stage1[idx]["exact"]:
            raise M3DError(f"selected nonexact baseline block {idx} is exact")

    exact_wall = sum(stage1[idx]["wall_s"] for idx in spec["exact_indices"])
    nonexact_wall = sum(stage1[idx]["wall_s"]
                        for idx in spec["nonexact_indices"])
    if not math.isclose(exact_wall, spec["baseline_exact_wall_s"],
                        rel_tol=0.0, abs_tol=1e-6):
        raise M3DError("selected exact baseline wall sum differs from PACKET.md")
    if not math.isclose(nonexact_wall, spec["baseline_nonexact_wall_s"],
                        rel_tol=0.0, abs_tol=1e-6):
        raise M3DError("selected nonexact baseline wall sum differs from PACKET.md")
    return stage1


def load_base_graph(arm: str, read: Callable[[str | Path], dict[str, Any]] = read_json,
                    rank_fn: Callable | None = None
                    ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and validate the stored M3-a graph; return its cold m=200 prefix."""
    spec = _arm_spec(arm)
    graph_spec = m3b.ARMS[spec["m3b_arm"]]
    artifact = read(graph_spec["graph"])
    graph = m3b.validate_graph_artifact(artifact, spec["m3b_arm"])
    field = nonbinary_field.GF2mField.create(p1.s2.Q)
    triples = m3b._triples(artifact["triples"], "triples")
    dense = p1.peg.sparse_to_dense(triples, N, 208, field)
    rank_fn = rank_fn or p1.peg.rank_GF1024
    full_rank = int(rank_fn(field, dense))
    base_rank = int(rank_fn(field, dense[:M_BASE]))
    if full_rank != 208 or base_rank != M_BASE:
        raise M3DError(
            f"stored graph rank mismatch: full={full_rank}, base={base_rank}")
    construction = {
        "n": N,
        "m": M_BASE,
        "triples": m3b._triples(artifact["base_triples"], "base_triples"),
        "status": "ok",
        "rank": base_rank,
        "four_cycles": graph["base_four_cycles"],
    }
    return construction, {**graph, "full_rank_recomputed": full_rank,
                          "base_rank_recomputed": base_rank}


def _rss_bytes() -> int:
    return p1._default_rss()


def _new_row(baseline: dict[str, Any], idx: int, stratum: str,
             out: dict[str, Any], dt: float) -> dict[str, Any]:
    if not isinstance(out, dict):
        raise M3DError("decoder must return a result mapping")
    iterations = out.get("iterations")
    if (isinstance(iterations, bool)
            or not isinstance(iterations, (int, np.integer))
            or iterations < 0 or iterations > MAX_ITER):
        raise M3DError("decoder returned invalid iterations for max_iter=250")
    actual_cap = out.get("max_iter")
    if actual_cap != MAX_ITER:
        raise M3DError("decoder output did not attest max_iter=250")
    exact = out.get("exact_match") is True
    undetected = int(not exact and bool(out.get("reconstruction_ok", False)))
    seed = SEED_BASE + idx
    if seed != baseline["seed"]:
        raise M3DError(f"paired seed identity mismatch at block {idx}")
    return {
        "block_idx": idx,
        "seed": seed,
        "selection_stratum": stratum,
        "baseline_status": baseline["status"],
        "baseline_exact": baseline["exact"],
        "baseline_undetected": baseline["undetected"],
        "baseline_iterations": baseline["iterations"],
        "baseline_wall_s": baseline["wall_s"],
        "new_status": out.get("status"),
        "new_exact": exact,
        "new_undetected": undetected,
        "new_iterations": int(iterations),
        "new_wall_s": dt,
        "max_iter": actual_cap,
    }


def _summarize(arm: str, rows: list[dict[str, Any]], verdict: str,
               baseline_rows: dict[int, dict[str, Any]],
               graph: dict[str, Any] | None, elapsed_s: float,
               rss_gib: float) -> dict[str, Any]:
    spec = _arm_spec(arm)
    exact_rows = [r for r in rows if r["selection_stratum"] == "exact"]
    nonexact_rows = [r for r in rows if r["selection_stratum"] == "nonexact"]
    baseline_exact_wall = spec["baseline_exact_wall_s"]
    baseline_nonexact_wall = spec["baseline_nonexact_wall_s"]
    exact_wall = sum(r["new_wall_s"] for r in exact_rows)
    nonexact_wall = sum(r["new_wall_s"] for r in nonexact_rows)
    complete = verdict == "COMPLETE" and len(rows) == 16
    paired = all(r["seed"] == baseline_rows[r["block_idx"]]["seed"]
                 for r in rows)
    same_outcomes = all(r["new_exact"] is not None
                        and r["new_exact"] == r["baseline_exact"] for r in rows)
    no_undetected = all(r["new_undetected"] == 0 for r in rows)
    identity_pass = len(rows) == 16 and paired
    accuracy_pass = complete and same_outcomes and no_undetected
    resource_pass = verdict == "COMPLETE"
    runtime_pass = (complete and len(nonexact_rows) == 8
                    and nonexact_wall <= NONEXACT_WALL_LIMIT * baseline_nonexact_wall)
    new_iteration_values = [int(r["new_iterations"]) for r in rows
                            if isinstance(r.get("new_iterations"),
                                          (int, np.integer))
                            and not isinstance(r.get("new_iterations"), bool)]
    baseline_iteration_total = sum(
        baseline_rows[idx]["iterations"]
        for idx, _ in _selected_indices(spec))
    return {
        "arm": arm,
        "m3b_arm": spec["m3b_arm"],
        "verdict": verdict,
        "max_iter": MAX_ITER,
        "n": N,
        "m": M_BASE,
        "field": "GF(32)",
        "seed_base": SEED_BASE,
        "seed_stream": "o1_blk:{seed}",
        "channel_npz": p1.CHANNEL_NPZ,
        "channel_source": p1.CHANNEL_SOURCE,
        "blocks_target": 16,
        "blocks_done": len(rows),
        "exact_stratum_done": len(exact_rows),
        "nonexact_stratum_done": len(nonexact_rows),
        "stage2_calls": 0,
        "identity_pass": identity_pass,
        "accuracy_pass": accuracy_pass,
        "resource_pass": resource_pass,
        "runtime_pass": runtime_pass,
        "arm_pass": all((identity_pass, accuracy_pass, resource_pass,
                         runtime_pass)),
        "baseline_exact_wall_s": baseline_exact_wall,
        "new_exact_wall_s": exact_wall,
        "baseline_nonexact_wall_s": baseline_nonexact_wall,
        "new_nonexact_wall_s": nonexact_wall,
        "nonexact_wall_limit_s": NONEXACT_WALL_LIMIT * baseline_nonexact_wall,
        "nonexact_wall_ratio": (nonexact_wall / baseline_nonexact_wall
                                if baseline_nonexact_wall else None),
        "baseline_iterations_total": baseline_iteration_total,
        "new_iterations_total": sum(new_iteration_values),
        "new_iterations_exact_stratum": sum(
            r["new_iterations"] for r in exact_rows
            if isinstance(r.get("new_iterations"), (int, np.integer))
            and not isinstance(r.get("new_iterations"), bool)),
        "new_iterations_nonexact_stratum": sum(
            r["new_iterations"] for r in nonexact_rows
            if isinstance(r.get("new_iterations"), (int, np.integer))
            and not isinstance(r.get("new_iterations"), bool)),
        "new_undetected": sum(r["new_undetected"] for r in rows
                               if isinstance(r.get("new_undetected"), int)
                               and not isinstance(r.get("new_undetected"), bool)),
        "new_undetected_unknown": sum(
            r.get("new_undetected") is None for r in rows),
        "elapsed_s": elapsed_s,
        "rss_gib": rss_gib,
        "graph": graph,
        "claim_ceiling": (
            "selected Stage-1 decoder-call cost on 16 preselected M3-b paired "
            "synthetic seeds per fixed graph instance; not a 240-frame FER, "
            "overall throughput, real-data advantage, leakage/f, SKR, or "
            "graph-family claim"),
    }


def _result_markdown(summary: dict[str, Any]) -> str:
    return "\n".join([
        f"# M3D selected Stage-1 call-cost diagnostic — {summary['arm']}",
        "",
        f"- calls: {summary['blocks_done']}/16; max_iter={summary['max_iter']}; "
        f"Stage-2 calls={summary['stage2_calls']}",
        f"- selected exact-stratum wall: baseline "
        f"{summary['baseline_exact_wall_s']:.6f}s; new "
        f"{summary['new_exact_wall_s']:.6f}s (descriptive)",
        f"- selected nonexact-stratum wall: baseline "
        f"{summary['baseline_nonexact_wall_s']:.6f}s; new "
        f"{summary['new_nonexact_wall_s']:.6f}s; limit "
        f"{summary['nonexact_wall_limit_s']:.6f}s; ratio "
        f"{summary['nonexact_wall_ratio'] if summary['nonexact_wall_ratio'] is not None else 'incomplete'}",
        f"- iterations: baseline selected {summary['baseline_iterations_total']}; "
        f"new selected {summary['new_iterations_total']}",
        f"- new undetected={summary['new_undetected']}; "
        f"unknown timeout rows={summary['new_undetected_unknown']}; "
        f"identity/accuracy/resource/runtime gates="
        f"{summary['identity_pass']}/{summary['accuracy_pass']}/"
        f"{summary['resource_pass']}/{summary['runtime_pass']}",
        f"- arm verdict={summary['verdict']}; arm_pass={summary['arm_pass']}; "
        f"wall={summary['elapsed_s']:.3f}s; RSS={summary['rss_gib']:.6f} GiB",
        f"- claim ceiling: {summary['claim_ceiling']}.",
        "",
    ])


def _write_result(root: str, summary: dict[str, Any],
                  rows: list[dict[str, Any]],
                  writer: Callable[[str, dict[str, str]], None] | None) -> None:
    write = writer or p1.default_writer
    write(root, {
        "rows.json": json.dumps({"summary": summary, "rows": rows},
                                 indent=1, sort_keys=True, default=str),
        "M3D_RESULT.md": _result_markdown(summary),
    })


def run_m3d_arm(*, arm: str, root: str, decode_fn: Callable | None,
                read: Callable[[str | Path], dict[str, Any]] = read_json,
                writer: Callable[[str, dict[str, str]], None] | None = None,
                clock: Callable | None = None,
                rss_fn: Callable | None = None,
                root_prefix: str = M3D_ROOT_PREFIX,
                graph_loader: Callable | None = None,
                prior_summary: dict[str, Any] | None = None
                ) -> dict[str, Any]:
    """Run exactly the selected 16 injected Stage-1 calls for one graph."""
    spec = _arm_spec(arm)
    _check_root(root, arm, root_prefix)
    if decode_fn is None:
        raise M3DError("decode_fn requires explicit injection")
    if arm == "M3D-R2" and not _arm_passed(prior_summary):
        raise M3DError("M3D-R2 requires a complete, passing M3D-R1 result")
    _require_hard_timeout_support()

    clock = clock or time.monotonic
    rss_fn = rss_fn or _rss_bytes
    t_start = clock()
    baseline_rows = validate_comparator(read(spec["comparator"]), arm)
    load_graph = graph_loader or load_base_graph
    construction, graph = load_graph(arm, read=read)
    rows: list[dict[str, Any]] = []
    rss_peak_gib = 0.0
    verdict = "COMPLETE"

    def _resource_stop(*, check_wall: bool = True) -> str | None:
        nonlocal rss_peak_gib
        rss_gib = float(rss_fn()) / (1024 ** 3)
        rss_peak_gib = max(rss_peak_gib, rss_gib)
        if rss_gib >= MAX_RSS_GIB:
            return "INCOMPLETE-budget"
        if check_wall and clock() - t_start >= MAX_ARM_WALL_S:
            return "INCOMPLETE-wall"
        return None

    def _flush(current_verdict: str) -> dict[str, Any]:
        summary = _summarize(arm, rows, current_verdict, baseline_rows,
                             graph, float(clock() - t_start), rss_peak_gib)
        _write_result(root, summary, rows, writer)
        return summary

    for idx, stratum in _selected_indices(spec):
        stop = _resource_stop()
        if stop:
            verdict = stop
            break
        baseline = baseline_rows[idx]
        seed = SEED_BASE + idx
        t0 = clock()
        try:
            out, actual_dt = _call_with_deadline(
                decode_fn, construction, seed, MAX_ITER)
        except _DecodeDeadline as exc:
            dt = max(float(clock() - t0), exc.elapsed_s)
            rows.append({
                "block_idx": idx, "seed": seed,
                "selection_stratum": stratum,
                "baseline_status": baseline["status"],
                "baseline_exact": baseline["exact"],
                "baseline_undetected": baseline["undetected"],
                "baseline_iterations": baseline["iterations"],
                "baseline_wall_s": baseline["wall_s"],
                "new_status": "timeout", "new_exact": None,
                "new_undetected": None, "new_iterations": None,
                "new_wall_s": dt, "max_iter": MAX_ITER,
                "timeout_kind": "decode",
                "error": ("hard decoder deadline exceeded after "
                          f"{dt:.6f}s"),
            })
            verdict = "INCOMPLETE-decode-cap"
            break
        except Exception as exc:  # one-shot diagnostic: retain and stop
            dt = float(clock() - t0)
            rows.append({
                "block_idx": idx, "seed": seed,
                "selection_stratum": stratum,
                "baseline_status": baseline["status"],
                "baseline_exact": baseline["exact"],
                "baseline_undetected": baseline["undetected"],
                "baseline_iterations": baseline["iterations"],
                "baseline_wall_s": baseline["wall_s"],
                "new_status": "error", "new_exact": False,
                "new_undetected": 0, "new_iterations": None,
                "new_wall_s": dt, "max_iter": None,
                "error": f"{type(exc).__name__}: {exc}",
            })
            verdict = "INCOMPLETE-error"
            break
        dt = max(float(clock() - t0), actual_dt)
        try:
            row = _new_row(baseline, idx, stratum, out, dt)
        except M3DError as exc:
            out_fields = out if isinstance(out, dict) else {}
            row = {
                "block_idx": idx, "seed": seed,
                "selection_stratum": stratum,
                "baseline_status": baseline["status"],
                "baseline_exact": baseline["exact"],
                "baseline_undetected": baseline["undetected"],
                "baseline_iterations": baseline["iterations"],
                "baseline_wall_s": baseline["wall_s"],
                "new_status": out_fields.get("status"),
                "new_exact": out_fields.get("exact_match") is True,
                "new_undetected": int(
                    out_fields.get("exact_match") is not True
                    and bool(out_fields.get("reconstruction_ok", False))),
                "new_iterations": out_fields.get("iterations"),
                "new_wall_s": dt, "max_iter": out_fields.get("max_iter"),
                "error": str(exc),
            }
            rows.append(row)
            verdict = "INCOMPLETE-schema"
            break
        rows.append(row)
        stop = _resource_stop(check_wall=False)
        _write_result(root, _summarize(
            arm, rows, "INCOMPLETE-running", baseline_rows, graph,
            float(clock() - t_start), rss_peak_gib), rows, writer)
        if dt > MAX_CALL_WALL_S:
            verdict = "INCOMPLETE-decode-cap"
            break
        if stop:
            verdict = stop
            break
        if clock() - t_start > MAX_ARM_WALL_S:
            verdict = "INCOMPLETE-wall"
            break

    summary = _flush(verdict)
    return summary


def _arm_passed(summary: dict[str, Any] | None) -> bool:
    return bool(summary and summary.get("arm") == "M3D-R1"
                and summary.get("verdict") == "COMPLETE"
                and summary.get("arm_pass") is True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="M3D selected Stage-1 iteration-cap diagnostic")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--arm", choices=tuple(ARMS))
    ap.add_argument("--root", default="")
    ap.add_argument("--execute-synthetic", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)

    if args.dry:
        if args.execute_synthetic or args.execution_authorized or args.arm or args.root:
            print("M3D refusal: --dry takes no arm, root or execution flags",
                  file=sys.stderr)
            return 2
        print(json.dumps({"mode": "dry-zero-decoder", "reads": 0,
                          "decoder_calls": 0, "stage2_calls": 0,
                          "arms": list(ARMS), "max_iter": MAX_ITER,
                          "root_family": M3D_ROOT_PREFIX}, indent=2))
        return 0

    if not args.execute_synthetic or not args.execution_authorized:
        print("M3D refusal: require both --execute-synthetic and "
              "--execution-authorized before any reads", file=sys.stderr)
        return 2
    if args.arm is None or not args.root:
        print("M3D refusal: --arm and --root are required", file=sys.stderr)
        return 2

    try:
        _arm_spec(args.arm)
        _check_root(args.root, args.arm)
        _require_hard_timeout_support()
        prior_summary = None
        if args.arm == "M3D-R2":
            r1_path = Path(ARMS["M3D-R1"]["root"]) / "rows.json"
            r1_payload = read_json(r1_path)
            prior_summary = r1_payload.get("summary")
            if not _arm_passed(prior_summary):
                raise M3DError("M3D-R1 did not complete and pass; refusing R2")

        bound = p1.s2c.bind_empirical_bundle(
            p1.CHANNEL_NPZ, p1.CHANNEL_SOURCE)
        if bound.get("source") != p1.CHANNEL_SOURCE:
            raise M3DError("bound M3-b synthetic source label mismatch")

        def decode_fn(construction: dict[str, Any], seed: int,
                      max_iter: int, _bundle=bound) -> dict[str, Any]:
            return p1.b2f.decode_block_marginal(
                construction, seed, _bundle, N, M_BASE,
                max_iter=max_iter)

        summary = run_m3d_arm(
            arm=args.arm, root=args.root, decode_fn=decode_fn,
            read=read_json,
            prior_summary=prior_summary)
        print(json.dumps(summary, indent=1, sort_keys=True, default=str))
        return 0 if summary["arm_pass"] else 1
    except (M3DError, p1.Refusal) as exc:
        print(f"M3D refusal: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
