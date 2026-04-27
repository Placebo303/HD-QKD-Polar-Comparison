#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _security_round_common import ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build protocol observables plan for strict Zhong/Niu upgrades.")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    lines = [
        "# Protocol Observables Plan",
        "",
        "## Current model layer",
        "- Mainline: Zhang-compatible / strict-Zhong-like calibrated security with global Franson visibility and actual-IR replay where available.",
        "- Not a strict Zhong 2015 proof.",
        "- Not a Niu 2016 composable proof.",
        "",
        "## Rerun-recoverable gaps",
        "- Emit rigorous frame-level accepted/rejected counts from the actual replay chain.",
        "- Emit explicit verification transcripts when SCL/CRC verification is actually executed, instead of counting configured CRC bits only.",
        "- Extend current summaries to preserve accepted-rate factorization and post-selection observables per point.",
        "",
        "## New processing support required",
        "- Per-point or per-loss measured Franson PE chain derived from raw or archived interferometric data products.",
        "- Single-pair / multipair reduction inputs derived from raw event statistics and proof-specific modeling.",
        "- Proof-grade basis-sifting/post-selection observables instead of engineering clean-pair surrogates.",
        "",
        "## New experiment / acquisition required",
        "- Decoy-state parameter-estimation observables.",
        "- Conjugate-basis statistics for composable security proof inputs.",
        "- Protocol-specific composable constants and basis-choice observables that are not present in current raw products.",
        "",
        "## Reporting guidance",
        "- Main result: actual-IR finite-key calibrated Zhong-like shadow.",
        "- Comparison only: literature-beta baseline.",
        "- Future work: strict Zhong-like PE chain and Niu 2016 composable observables.",
    ]
    write_summary(output_dir / "protocol_observables_plan.md", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
