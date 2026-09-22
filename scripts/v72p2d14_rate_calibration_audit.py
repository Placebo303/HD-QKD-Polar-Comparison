"""Thin runner for the D14 Phase R no-decoder rate-calibration audit.

Frozen command (requires no execution gate; EXPLORE synthetic diagnostic):

    .venv/bin/python scripts/v72p2d14_rate_calibration_audit.py \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --d12-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450 \\
      --d11-root workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64 \\
      --out-root workspace/v72p2d14_rate_audit/20260914_r1 \\
      --hyp-l1 4.2867 --hyp-l2 3.2227 --hyp-factors 0.890,0.979,1.068

The ``--hyp-*`` values are hypotheses under test (recorded, never constants).
Zero decoder calls, zero new blocks, zero seed search; refuses overwrite and
non-allowlisted inputs before any work. No commit/push.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.formal_ir import v72p2d14_rate_calibration_audit as audit


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-f-root", required=True)
    p.add_argument("--d12-root", required=True)
    p.add_argument("--d11-root", required=True)
    p.add_argument("--out-root", required=True)
    p.add_argument("--hyp-l1", required=True, type=float)
    p.add_argument("--hyp-l2", required=True, type=float)
    p.add_argument("--hyp-factors", required=True)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    hypotheses = {
        "h_l1": float(args.hyp_l1),
        "h_l2": float(args.hyp_l2),
        "factors": [float(v) for v in str(args.hyp_factors).split(",")],
    }
    manifest = audit.run_audit(
        args.model_f_root, args.d12_root, args.d11_root, args.out_root,
        hypotheses, command=" ".join(sys.argv))
    print("audit DONE root=%s wall=%.1fs decoder_calls=%d" % (
        args.out_root, manifest["wall_s"], manifest["decoder_calls"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
