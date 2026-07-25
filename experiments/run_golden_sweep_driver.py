#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.runtime_paths import default_project_results_root, resolve_repo_path


def _pump_binary_stream(stream, console, log_file) -> None:
    while True:
        chunk = stream.read(4096)
        if not chunk:
            break
        text = chunk.decode("utf-8", errors="replace")
        console.write(text)
        console.flush()
        log_file.write(text)
        log_file.flush()


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full Golden Sweep with live tee logging.")
    ap.add_argument("--extract-workers", type=int, default=8)
    ap.add_argument("--jobs", type=int, default=15)
    ap.add_argument(
        "--force-align",
        action="store_true",
        help="Accepted for compatibility; alignment is always forced in this driver.",
    )
    ap.add_argument("--log-file", default="results/golden_sweep_execution.log")
    ap.add_argument("--out-root", default="", help="Optional explicit out-root for run_e2e_pipeline.py")
    args = ap.parse_args()

    dims = "4,8,16,32,64,128,256,512,1024,2048,4096"
    bws = "20,30,40,50,60,80,100,120,150,180,200"

    cmd = [
        sys.executable,
        str(REPO_ROOT / "experiments" / "run_e2e_pipeline.py"),
        "--dims",
        dims,
        "--bws",
        bws,
        "--force-align",
        "--extract-workers",
        str(max(1, int(args.extract_workers))),
        "--jobs",
        str(max(1, int(args.jobs))),
    ]
    if str(args.out_root).strip():
        cmd.extend(["--out-root", str(args.out_root).strip()])

    if str(args.log_file).strip():
        log_path = resolve_repo_path(REPO_ROOT, args.log_file)
    else:
        log_path = default_project_results_root(REPO_ROOT) / "golden_sweep_execution.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    start_ts = datetime.now().isoformat()
    print(f"[GOLDEN] start={start_ts}")
    print(f"[GOLDEN] cmd={' '.join(cmd)}")
    print(f"[GOLDEN] log_file={log_path}")

    with log_path.open("w", encoding="utf-8", newline="") as logf:
        logf.write(f"[GOLDEN] start={start_ts}\n")
        logf.write(f"[GOLDEN] cmd={' '.join(cmd)}\n")
        logf.write(f"[GOLDEN] cwd={REPO_ROOT}\n")
        logf.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        assert proc.stdout is not None
        assert proc.stderr is not None
        t_out = threading.Thread(target=_pump_binary_stream, args=(proc.stdout, sys.stdout, logf), daemon=True)
        t_err = threading.Thread(target=_pump_binary_stream, args=(proc.stderr, sys.stderr, logf), daemon=True)
        t_out.start()
        t_err.start()

        rc = proc.wait()
        t_out.join()
        t_err.join()

    elapsed_s = time.perf_counter() - start
    elapsed_min = elapsed_s / 60.0
    end_ts = datetime.now().isoformat()
    print(f"[GOLDEN] end={end_ts} rc={rc}")
    print(f"Total Golden Sweep Time: {elapsed_min:.2f} minutes")
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
