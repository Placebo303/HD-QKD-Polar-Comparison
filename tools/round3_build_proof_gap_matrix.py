#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


ROWS = [
    ("zhang_2013_compatible", "global_franson_visibility_calibration", "available", "global_visibility=0.95", "", "yes", "no", "no", "Global calibration input only, not per-point PE."),
    ("zhang_2013_compatible", "actual_polar_ir_leak", "partial", "round1b_actual_ir_replay", "full verification transcript on all points", "yes", "yes", "no", "Syndrome replay can be actual; CRC-style verification may remain configured on some SCL points."),
    ("zhang_2013_compatible", "finite_key_penalty", "available", "round2_finite_key_audit_table", "", "yes", "no", "no", "Calibrated Zhong-like finite-key penalty, not composable proof."),
    ("zhong_2015_strict", "per_point_franson_pe_chain", "missing", "", "per-point/per-loss measured Franson PE chain", "no", "yes", "yes", "Current pipeline only has one global visibility value."),
    ("zhong_2015_strict", "frame_level_post_selection_observables", "partial", "clean_pair_fraction", "rigorous accepted/rejected frame accounting", "yes", "yes", "no", "Current accepted-frame fraction may fall back to surrogate clean-pair fraction."),
    ("niu_2016_composable", "decoy_state_PE", "missing", "", "decoy_state_PE", "no", "no", "yes", "Requires new protocol observables."),
    ("niu_2016_composable", "conjugate_basis_stats", "missing", "", "conjugate_basis_stats", "no", "no", "yes", "Current data path does not record basis-resolved security observables."),
    ("niu_2016_composable", "protocol_specific_composable_constants", "missing", "", "composable constants", "no", "no", "yes", "Not recoverable from current outputs alone."),
    ("niu_2016_composable", "single_pair_fraction_or_multipair_reduction", "missing", "", "single-pair fraction / multipair reduction inputs", "no", "yes", "yes", "Would need new modeling and likely new observables."),
    ("niu_2016_composable", "proof_required_basis_sifting_post_selection", "missing", "", "basis-sifting/post-selection observables", "no", "yes", "yes", "Current candidate tables do not expose proof-grade sifting statistics."),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build strict-proof gap matrix for current security pipeline.")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    cols = [
        "target_model_tag",
        "requirement_name",
        "current_status",
        "available_source",
        "missing_observable",
        "can_be_recovered_from_existing_data",
        "requires_new_rerun",
        "requires_new_experiment",
        "notes",
    ]
    df = pd.DataFrame(ROWS, columns=cols)
    df.to_csv(output_dir / "proof_gap_matrix.csv", index=False)
    write_summary(
        output_dir / "round3_summary.txt",
        [
            "1. current mainline model layer: zhang_2013_compatible_with_actual_ir_finite_key_calibrated_shadow",
            "2. fields still missing for strict Zhong-like: per-point/per-loss Franson PE chain, rigorous frame-level post-selection observables, fully actual verification transcript on all replayed points",
            "3. observables still missing for Niu 2016: decoy_state_PE, conjugate_basis_stats, protocol-specific composable constants, single-pair/multipair reduction inputs, proof-grade basis-sifting/post-selection observables",
            "4. rerun-recoverable gaps: explicit replay verification logs and stricter frame-level accounting",
            "5. gaps requiring new experiment or new acquisition observables: decoy-state PE, conjugate-basis stats, measured Franson PE chain, composable constants",
            "6. reporting guidance: report actual-IR finite-key calibrated shadow as main result; keep strict Zhong-like and Niu 2016 claims in future work only",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
