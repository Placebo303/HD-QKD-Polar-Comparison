"""CLI for the evaluation-only (retrospective) V5-C2 cross-loss transfer
evaluation.  Non-qualification; writes only under the user-supplied output
directory (additive) and never touches frozen or official outputs.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..formal_ir.ldpc_v5_transfer_evaluation import evaluate_all, PUBLIC_STRATA


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(
        description="evaluation-only V5-C2 cross-loss transfer evaluation")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--losses", default="16,20",
                   help="comma-separated loss values to evaluate "
                        "(6,16,20 decoded; 10 referenced from official CSV)")
    p.add_argument("--append", action="store_true",
                   help="merge into an existing output directory: losses already "
                        "present in the previous report are preserved, requested "
                        "losses are appended (default: fresh empty directory)")
    p.add_argument("--sidecar-root", type=Path, default=None,
                   help="override the sidecar root for the decoded losses of this "
                        "run (default: keep the per-loss fixed sidecar paths; "
                        "e.g. for the 20 dB pairing_v2 re-evaluation)")
    p.add_argument("--report-name", default="evaluation_report.json",
                   help="report file name written under --output-dir "
                        "(default: evaluation_report.json)")
    p.add_argument("--summary-name", default="evaluation_summary.csv",
                   help="summary CSV file name written under --output-dir "
                        "(default: evaluation_summary.csv)")
    p.add_argument("--pairing-version", default=None,
                   help="pairing version tag recorded in the outputs "
                        "(e.g. pairing_v2)")
    a = p.parse_args()
    losses = [x.strip() for x in a.losses.split(",") if x.strip()]
    if not losses:
        p.error("--losses must name at least one loss")
    report = evaluate_all(a.output_dir, losses, PUBLIC_STRATA,
                          allow_existing=a.append,
                          sidecar_root=a.sidecar_root,
                          pairing_version=a.pairing_version,
                          report_name=a.report_name,
                          summary_name=a.summary_name)
    print(f"evaluation_only completed: {a.output_dir}")
    print(f"declaration: {report['declaration']}")
    for loss_db, res in report["losses"].items():
        for stratum, st in res["per_stratum"].items():
            print(f"loss={loss_db} stratum={stratum} "
                  f"successes={st['successes']}/{st['denominator']} "
                  f"rate={st['rate']:.4f} ci=[{st['ci_low']:.4f},{st['ci_high']:.4f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
