"""CLI for the V11 Stage X scientific executor
(``formal-nonbinary-ldpc-v11-sc-de-gate``, design.md §5 Stage X / §6 gate,
V11-40.2).

AUTHORIZATION BOUNDARY: ``--execute`` runs the GF(1024) scientific matrix and
REFUSES to start unless the caller passes ``--v11-40-2-authorized`` — the
explicit V11-40.2 main-thread authorization that follows the formal-plan
review (V11-40.1).  ``--self-check`` and ``--dry-run`` execute no scientific
runs (structure-only).

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_execute \
      --self-check
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_execute \
      --dry-run [--out-dir DIR]
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_execute \
      --status EXEC_ROOT
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_execute \
      --execute [--workers N] [--out-root DIR] [--no-warmup] [--serial] \
      [--resume] [--background] [--replay-ok] [--structured-ok] [--semantic-ok] \
      --v11-40-2-authorized
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid

from ..formal_ir import nonbinary_v11_execute as execute
from ..formal_ir.nonbinary_v11_parallel import DEFAULT_WORKERS

#: Default structural dry-run evidence root (referenced by the formal plan's
#: executor segment; a workspace scratch artifact, not a production root).
DRY_RUN_ROOT = os.path.join("workspace", "nbldpc_v11_execute_dryrun")


def _repo_root() -> str:
    """Repository root (parent of the top-level ``comparison_bench/`` dir),
    used as the detached child's working directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true",
                        help="structural self-check (no scientific run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="structural dry-run evidence (no scientific run)")
    parser.add_argument("--execute", action="store_true",
                        help="run the frozen 60-run scientific matrix "
                             "(requires --v11-40-2-authorized)")
    parser.add_argument("--v11-40-2-authorized", dest="v11_40_2_authorized",
                        action="store_true",
                        help="explicit V11-40.2 main-thread authorization")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"worker count (default: {DEFAULT_WORKERS})")
    parser.add_argument("--out-dir", default=None,
                        help="dry-run evidence dir, or the execution root for "
                             "--execute/--background (alias of --out-root; "
                             "default: workspace/nbldpc_v11_execute_<short-uuid>/)")
    parser.add_argument("--out-root", default=None,
                        help="execute evidence root (alias of --out-dir; "
                             "default: workspace/nbldpc_v11_execute_<short-uuid>/)")
    parser.add_argument("--no-warmup", action="store_true",
                        help="skip the numba warmup pass (debug)")
    parser.add_argument("--serial", action="store_true",
                        help="execute in-process without a worker pool (debug/test)")
    parser.add_argument("--resume", action="store_true",
                        help="resume: skip runs whose per-run evidence is "
                             "complete and parseable under the execution root "
                             "(interrupted runs without valid evidence are "
                             "re-executed; completed evidence is never re-run)")
    parser.add_argument("--background", action="store_true",
                        help="launch --execute in a detached process and "
                             "return immediately (log: <exec_root>/execute.log; "
                             "monitor with --status <exec_root>)")
    parser.add_argument("--status", metavar="EXEC_ROOT", default=None,
                        help="print the progress/status summary for an "
                             "execution root and exit (read-only)")
    parser.add_argument("--replay-ok", action="store_true",
                        help="declare V11-40.3 replay passed (V11-50.1 use)")
    parser.add_argument("--structured-ok", action="store_true",
                        help="declare structured-field validation passed")
    parser.add_argument("--semantic-ok", action="store_true",
                        help="declare semantic recomputation passed")
    args = parser.parse_args()

    if args.self_check:
        execute._self_check()
        raise SystemExit(0)

    if args.dry_run:
        out_dir = args.out_dir if args.out_dir is not None else DRY_RUN_ROOT
        summary = execute._dry_run(out_dir)
        print(json.dumps({key: summary[key] for key in
                          ("schema", "scientific_executed", "n_specs", "n_seeds",
                           "probe_counts", "evidence_path")},
                         indent=2, sort_keys=True))
        raise SystemExit(0)

    if args.status:
        status = execute.summarize_status(args.status)
        n_terminal, n_total = status["n_terminal"], status["n_total"]
        print(f"progress: {n_terminal}/{n_total} terminal "
              f"(done/invalid/not_converged)")
        for cell, counts in status["per_cell"].items():
            print(f"  {cell}: {counts['done']}/{counts['total']} done")
        running = status["currently_running"]
        print("running: " + (", ".join(running) if running else "none"))
        if status["stale_running"]:
            print("STALE running entries (heartbeat older than 2x interval): "
                  + ", ".join(status["stale_running"]))
        heartbeat = status["heartbeat"]
        if heartbeat:
            print(f"heartbeat: {heartbeat.get('last_active_utc')} "
                  f"(runs_done={heartbeat.get('runs_done')}, "
                  f"runs_running={heartbeat.get('runs_running')})")
        print(json.dumps(status, indent=2, sort_keys=True))
        raise SystemExit(0)

    if args.execute:
        if not args.v11_40_2_authorized:
            print(
                "REFUSED: V11-40.2 scientific execution requires the explicit\n"
                "main-thread authorization after the formal-plan review (V11-40.1).\n"
                "This run did not execute any scientific matrix.",
                file=sys.stderr)
            raise SystemExit(1)
        exec_root = args.out_root or args.out_dir
        if exec_root is None:
            exec_root = os.path.join(
                "workspace", f"nbldpc_v11_execute_{uuid.uuid4().hex[:8]}")
        exec_root = os.path.abspath(exec_root)

        if args.background:
            _launch_background(args, exec_root)
            raise SystemExit(0)

        summary = execute.execute_formal_matrix(
            out_root=exec_root,
            workers=args.workers,
            warmup=not args.no_warmup,
            serial=args.serial,
            resume=args.resume,
            replay_ok=args.replay_ok,
            structured_ok=args.structured_ok,
            semantic_ok=args.semantic_ok)
        _write_json(os.path.join(exec_root, "formal_matrix_results.json"), summary)
        compact = {
            "status": summary["status"],
            "n_runs_total": summary["n_runs_total"],
            "n_runs_completed": summary["n_runs_completed"],
            "gate": summary["gate"]["state"] if "gate" in summary else None,
            "selected_geometry": summary["gate"].get("selected_geometry")
                                 if "gate" in summary else None,
            "batch_wall_seconds": summary["resource"]["batch_wall_seconds"],
            "evidence_root": exec_root,
            "bookkeeping": summary["bookkeeping"],
        }
        print(json.dumps(compact, indent=2, sort_keys=True))
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(1)


def _launch_background(args: argparse.Namespace, exec_root: str) -> None:
    """Spawn a detached child that runs the scientific matrix, then return.

    The child is ``sys.executable -m ...run_formal_nonbinary_v11_execute
    --execute --v11-40-2-authorized --resume --out-dir <exec_root>`` with
    stdout/stderr redirected to ``<exec_root>/execute.log`` and its own
    process group, so it survives this parent (and opencode) exiting.
    """
    os.makedirs(exec_root, exist_ok=True)
    log_path = os.path.join(exec_root, "execute.log")
    child = [sys.executable, "-m",
             "comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_execute",
             "--execute", "--v11-40-2-authorized", "--resume",
             "--out-dir", exec_root, "--workers", str(args.workers)]
    if args.no_warmup:
        child.append("--no-warmup")
    if args.serial:
        child.append("--serial")
    if args.replay_ok:
        child.append("--replay-ok")
    if args.structured_ok:
        child.append("--structured-ok")
    if args.semantic_ok:
        child.append("--semantic-ok")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    child_env = dict(os.environ)
    child_env["PYTHONUNBUFFERED"] = "1"  # stream execute.log in real time
    with open(log_path, "w", encoding="utf-8", buffering=1) as log_fh:
        process = subprocess.Popen(
            child, cwd=_repo_root(), env=child_env, stdout=log_fh,
            stderr=subprocess.STDOUT, close_fds=True, creationflags=creationflags)
    print(json.dumps({
        "background_pid": process.pid,
        "execution_root": exec_root,
        "log_path": log_path,
        "progress_file": os.path.join(exec_root, "progress.json"),
        "status_command": (
            f"python -m comparison_bench.src.comparison_bench.cli."
            f"run_formal_nonbinary_v11_execute --status {exec_root}"),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
