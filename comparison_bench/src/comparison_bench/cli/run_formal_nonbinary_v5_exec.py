"""CLI for parallel/flush/resume execution of NBLDPC v5 routes.

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v5_exec \
      <lane-module> plan|execute|resume|verify [--workers N] [--flush-every N] [--log PATH]

<lane-module> is the import path of a route lane module exposing CONFIG and
create_plan/run/verify (e.g.
comparison_bench.src.comparison_bench.formal_ir.nonbinary_v5b_ir_qualification).
`execute` uses the deterministic parallel wrapper; `resume` continues an
interrupted package at most once; plan/verify delegate to the frozen runtime.
"""
from __future__ import annotations
import argparse, importlib

from ..formal_ir import nonbinary_v5_exec_wrapper as wrapper
from ..formal_ir import nonbinary_v5_runtime as runtime


def _lane(path):
    return importlib.import_module(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lane")
    parser.add_argument("action", choices=("plan", "execute", "resume", "verify"))
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--flush-every", type=int, default=64)
    parser.add_argument("--log", default=None)
    args = parser.parse_args()
    lane = _lane(args.lane)
    if args.action == "plan":
        lane.create_plan()
    elif args.action == "execute":
        print(wrapper.parallel_run(lane.CONFIG, workers=args.workers,
                                   flush_every=args.flush_every, log_path=args.log))
    elif args.action == "resume":
        print(wrapper.resume_run(lane.CONFIG, workers=args.workers,
                                 flush_every=args.flush_every, log_path=args.log))
    else:
        print(lane.verify())


if __name__ == "__main__":
    main()
