"""D18 current-channel L2 ensemble DE runner — readiness + frozen sweep paths.

Frozen DE command (design §8; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d18_ensemble_development.py --de-sweep \\
      --execution-authorized \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901

Paths:

- ``--profile-only``: frozen plan/candidate arithmetic (21 feasibility +
  Stage-S/C plans + selection dry-run inputs) plus the future-root absence
  proof; no V26 kernel, no decoder, no Model-F content, no root;
- ``--de-sweep``: the frozen two-stage matrix (Stage S ≤168 + mechanical
  Stage C ≤288 new, 456 total; setup <= 16); refuses unless
  ``--execution-authorized`` is passed (default false; refusal happens
  before any root probe, kernel bind or Model-F load) and requires
  explicitly injected adapters on the test path (production bind happens
  inside the orchestrator, after plan validation);
- ``--verify``: read-only recomputation of a completed six-file root with
  zero DE calls; exits FAIL on any partial or engineering-blocked root.
  Without an injected ``rho_fn`` the verifier checks stored traces only,
  so the CLI path never loads the V26 kernel.

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
    v72p2d18_l2_ensemble_de as d18)

EVIDENCE_FILES = d18.EVIDENCE_FILES
FROZEN_COMMAND = d18.FROZEN_COMMAND


def build_parser():
    parser = argparse.ArgumentParser(
        description="D18 current-channel L2 ensemble DE runner")
    parser.add_argument("--de-sweep", action="store_true",
                        help="run the frozen two-stage DE matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--de-sweep; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="frozen plan/grid arithmetic only (no kernel, "
                             "no decoder, no root)")
    parser.add_argument("--model-f-root", default=d18.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Frozen plan print + absence proofs; zero scientific calls."""
    return d18.describe_plan()


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--de-sweep", args.de_sweep),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --de-sweep, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --de-sweep before the root probe and before any kernel binding
    # or Model-F load while --execution-authorized is false.
    if args.de_sweep and not args.execution_authorized:
        print("refusing --de-sweep: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d18.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        rho_fn = None
        if adapters_override is not None:
            rho_fn = adapters_override.get("rho_fn")
        return 0 if d18.verify_de_root(args.out_root, rho_fn=rho_fn) else 1
    # Authorized true branch: exactly one sweep-orchestrator call plus one
    # never-overwrite writer. adapters_override carries test-machinery
    # fakes only (an injected "channel" must map 'L2' to the layer-tagged
    # oracle; None production-binds inside the orchestrator, after plan
    # validation and the fresh-root probe).
    inj = dict(adapters_override) if adapters_override is not None else {}
    bundle = d18.run_de_sweep(
        args.out_root, args.model_f_root,
        channel=inj.get("channel"), de_call=inj.get("de_call"),
        rho_fn=inj.get("rho_fn"), now_fn=inj.get("now_fn"),
        rss_fn=inj.get("rss_fn"))
    summary = d18.write_de_root(bundle)
    print("DE terminal=%s calls=%d setup=%d winner=%s"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"], summary.get("winner_candidate_id")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
