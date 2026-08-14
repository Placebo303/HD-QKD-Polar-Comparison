"""CLI for the separately authorized formal NBLDPC v5d post lane."""
from __future__ import annotations
import argparse
from ..formal_ir import nonbinary_v5d_ir_qualification as lane
from ..formal_ir import nonbinary_v5_exec_wrapper as wrapper

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "execute", "resume", "verify"))
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--flush-every", type=int, default=64)
    parser.add_argument("--log", default=None)
    args = parser.parse_args()
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
