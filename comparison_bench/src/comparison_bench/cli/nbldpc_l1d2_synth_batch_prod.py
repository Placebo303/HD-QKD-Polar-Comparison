"""Thin Stage-2 production entrypoint: bind the adapter, run the batch.

Change: ``T5-BLOCKER-7`` scheme B. Implementation-only assembly: this module
binds ``production_decode_fn`` and delegates plan/execute/write to
``nbldpc_l1d2_synth_batch.run``. The frozen runner is untouched (no CLI
change, no contract change); fake-only default stays in the runner.

Intended only for explicitly authorized DECIDE execution. ``--dry-run``
validates the plan and exits 0 with no writes and no decoder call; without
``--execute`` the CLI validates the plan and exits nonzero. ``--execute``
runs the full production chain and writes additively under one fresh
``--out-root``. ``--fake-decoder`` is refused here (production binding is
the sole purpose of this entrypoint), as is any ``--max-iter`` /
``--damping`` outside the frozen档 (the adapter fixes 90/1.0; a divergent
manifest must never be written).
"""
from __future__ import annotations

import sys
from typing import Sequence

from comparison_bench.cli import nbldpc_l1d2_synth_batch as batch
from comparison_bench.formal_ir import (
    nbldpc_l1d2_production_decode as prod,
)

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Production CLI entrypoint. Returns the process exit code."""
    parser = batch.build_parser()
    args = parser.parse_args(argv)
    try:
        args.graph_seeds = batch.parse_seed_list(args.graph_seed_raw)
        args.data_seeds = batch.parse_seed_list(args.data_seed_raw)
        args.frames = batch.parse_frames(args.frames)
        args.rss_cap_bytes = batch.parse_bytes(args.rss_cap_bytes) \
            if not isinstance(args.rss_cap_bytes, int) \
            else int(args.rss_cap_bytes)
    except (ValueError, TypeError) as exc:
        print("invalid argument: %s" % (exc,), file=sys.stderr)
        return 2
    if bool(args.fake_decoder):
        print("refusing: this production entrypoint always binds the "
              "production decoder; --fake-decoder belongs to the "
              "fake-only runner", file=sys.stderr)
        return 2
    if int(args.max_iter) != prod.MAX_ITER \
            or float(args.damping) != prod.DAMPING_ALPHA:
        print("refusing: frozen decoder档 is max_iter=%d damping=%s "
              "(adapter-fixed; divergent manifest refused)"
              % (prod.MAX_ITER, prod.DAMPING_ALPHA), file=sys.stderr)
        return 2
    command = " ".join(sys.argv) if argv is None else " ".join(
        [sys.executable or "python", "-m",
         "comparison_bench.cli.nbldpc_l1d2_synth_batch_prod"]
        + [str(a) for a in argv])
    try:
        plan = batch.build_plan(int(args.width), list(args.graph_seeds),
                                list(args.data_seeds), list(args.frames),
                                canary=bool(args.canary))
        batch.refuse_out_root(args.out_root, args.model_f_root)
    except (ValueError, KeyError, FileExistsError) as exc:
        print("plan refused: %s" % (exc,), file=sys.stderr)
        return 2
    print("plan: width=%d graphs=%d data=%d frames=%d pairs=%d arms=2 "
          "oracle=False production-decoder" % (int(args.width),
                                               len(set(args.graph_seeds)),
                                               len(set(args.data_seeds)),
                                               len(args.frames),
                                               len(plan)))
    if bool(args.dry_run):
        print("dry-run: plan validated, no execution, no writes")
        return 0
    if not bool(args.execute):
        print("refusing: scientific execution requires --execute "
              "(plan validated, no writes)", file=sys.stderr)
        return 2
    batch.run(args, decode_fn=prod.production_decode_fn, command=command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
