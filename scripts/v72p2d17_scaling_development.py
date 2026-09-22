"""D17 current-channel asymptotic-DE runner — readiness + A3 scaling-fit paths.

Frozen DE command (design §4; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch \\
      --execution-authorized \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718

Paths:

- ``--profile-only``: frozen 15-point plan arithmetic (m/R/d/delta, node
  sides, check allocations, seeds, convergence rule, budgets) plus the
  future-root absence proof; no V26 kernel, no decoder, no Model-F content,
  no root;
- ``--de-batch``: the frozen 240-call matrix (3 profiles x 5 m x 8 seeds x
  2 pops; setup <= 12); refuses unless ``--execution-authorized`` is passed
  (default false; refusal happens before any root probe, kernel bind or
  Model-F load) and requires explicitly injected adapters (production bind
  happens inside the orchestrator, after plan validation). R2 binding: a
  production (``None``) channel loads ``(pb, p_f, p1)`` once, builds the L1
  sampler once and the true-conditioned L2 oracle once
  (``conditionalize_f_to_p2`` + ``oracle_l2_prior`` + XOR-centering), then
  dispatches per plan profile before every call (``L045``/``L055`` ← L1,
  ``L2`` ← L2 oracle); an injected ``channel`` must use the same explicit
  per-profile mapping form of layer-tagged callables — a single shared
  callable is forbidden;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip and zero DE calls; exits FAIL on any partial or
  engineering-blocked root. Without an injected ``rho_fn`` the verifier
  checks rho present-and-finite only, so the CLI path never loads the V26
  kernel.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d17_descaling as d17)

EVIDENCE_FILES = d17.EVIDENCE_FILES
FROZEN_COMMAND = d17.FROZEN_COMMAND
A3_FROZEN_COMMAND = d17.A3_FROZEN_COMMAND


def build_parser():
    parser = argparse.ArgumentParser(
        description="D17 current-channel asymptotic-DE runner")
    parser.add_argument("--de-batch", action="store_true",
                        help="run the frozen 240-call DE matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--scaling-fit", action="store_true",
                        help="run the frozen A3 finite-length scaling fit + "
                             "D16 prediction freeze (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--de-batch/--scaling-fit; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="frozen plan/grid arithmetic only (no kernel, "
                             "no decoder, no root)")
    parser.add_argument("--model-f-root", default=d17.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--de-root", default=d17.A3_DE_ROOT,
                        help="reviewed A2 DE root (A3 scaling-fit input)")
    parser.add_argument("--finite-root", dest="finite_roots", action="append",
                        default=None,
                        help="finite input root (repeatable; exactly five in "
                             "frozen §11.2 order for --scaling-fit)")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Frozen plan print + absence proofs; zero scientific calls."""
    return d17.describe_plan()


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--de-batch", args.de_batch),
                                        ("--scaling-fit", args.scaling_fit),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --de-batch, --scaling-fit, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --scaling-fit before output creation and before input reads
    # while --execution-authorized is false (fail-closed, no-write/no-read).
    if args.scaling_fit and not args.execution_authorized:
        print("refusing --scaling-fit: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d17.AUTHORIZATION, file=sys.stderr)
        return 2
    # Refuse --de-batch before the root probe and before any kernel binding
    # or Model-F load while --execution-authorized is false.
    if args.de_batch and not args.execution_authorized:
        print("refusing --de-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d17.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.scaling_fit:
        # Frozen A3 form: exactly five --finite-root in §11.2 order, plus
        # --de-root and --out-root; no glob discovery; never overwrites
        # (probe fail-closed inside the orchestrator, after this refusal).
        if not args.finite_roots or len(args.finite_roots) != 5:
            parser.error("--scaling-fit requires exactly five --finite-root "
                         "in frozen §11.2 order")
        bundle = d17.a3_run(args.out_root, args.de_root,
                            list(args.finite_roots))
        print("SCALING terminal=%s clusters=%d" % (
            bundle["manifest"]["terminal"],
            bundle["manifest"]["cluster_counts"]["total"]))
        return 0
    if args.verify:
        rho_fn = None
        if adapters_override is not None:
            rho_fn = adapters_override.get("rho_fn")
        return 0 if d17.verify_de_root(args.out_root, rho_fn=rho_fn) else 1
    # Authorized true branch: exactly one batch-orchestrator call plus one
    # never-overwrite writer. adapters_override carries test-machinery
    # fakes only (an injected "channel" must be the explicit per-profile
    # mapping of layer-tagged callables; None production-binds inside the
    # orchestrator, after plan validation and the fresh-root probe).
    inj = dict(adapters_override) if adapters_override is not None else {}
    bundle = d17.run_de_batch(
        args.out_root, args.model_f_root,
        channel=inj.get("channel"), de_call=inj.get("de_call"),
        rho_fn=inj.get("rho_fn"), now_fn=inj.get("now_fn"),
        rss_fn=inj.get("rss_fn"))
    summary = d17.write_de_root(bundle)
    print("DE terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
