"""CLI Runner for V37-P1 Finite-Feasible Empirical-P DE Candidate Screening.

Usage:
    # Dry-run candidate enumeration check (no DE executed):
    python -m comparison_bench.src.comparison_bench.cli.run_v37_de_screening --dry-run

    # Test/fake-runner execution (synthetic DE for testing orchestration/reporting):
    python -m comparison_bench.src.comparison_bench.cli.run_v37_de_screening --fake-runner --output-dir <path>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..formal_ir.v37_de_screening import (
    ACCEPTED_PLAN_SHA,
    CYCLE_ID,
    DE_MAX_ITER,
    DE_N_SAMPLES,
    EFFECT_SIZE_THRESHOLD,
    export_candidate_summary_csv,
    export_summary_json,
    export_trajectories_csv,
    generate_v37_candidate_grid,
    get_reference_controls,
    run_v37_p1_pipeline,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="V37-P1 Finite-Feasible Empirical-P DE Candidate Screening Runner"
    )
    parser.add_argument(
        "--dry-run", "--enumerate-only",
        action="store_true",
        dest="dry_run",
        help="Enumerate and validate candidate distributions without running DE.",
    )
    parser.add_argument(
        "--fake-runner",
        action="store_true",
        help="Run pipeline with deterministic synthetic DE traces for test/smoke purposes.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v37_de_screening/run_01"),
        help="Directory to save output artifacts.",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=DE_N_SAMPLES,
        help=f"Monte Carlo samples per DE iteration (default: {DE_N_SAMPLES}).",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=DE_MAX_ITER,
        help=f"Maximum DE iterations (default: {DE_MAX_ITER}).",
    )

    args = parser.parse_args()

    print(f"=== V37-P1 Empirical-P DE Candidate Screening ===")
    print(f"Cycle ID: {CYCLE_ID}")
    print(f"Accepted Plan SHA: {ACCEPTED_PLAN_SHA}")

    raw_cands, n2_cands, final_cands = generate_v37_candidate_grid()
    baseline, pos_control = get_reference_controls()

    print(f"\n--- Candidate Enumeration & P0 Feasibility ---")
    print(f"Raw Simplex Candidates (degrees {{2,3,4,5}}, step=0.05): {len(raw_cands)}")
    print(f"P0 Necessary Forest Gate (N2 <= 183):                 {len(n2_cands)}")
    print(f"Final Pre-Registered Set (N2 <= 183 & max_dc <= 20):  {len(final_cands)}")
    print(f"Total Evaluated Configurations (259 + 2 controls):   {len(final_cands) + 2}")

    if args.dry_run:
        print("\n[DRY RUN] Candidate enumeration complete. No DE executed.")
        return 0

    if not args.fake_runner:
        print(
            "\n[ABORT] Full production DE execution is NOT AUTHORIZED in this mode.\n"
            "Pass --dry-run for configuration validation or --fake-runner for test-only orchestration.",
            file=sys.stderr,
        )
        return 1

    print(f"\n[FAKE RUNNER] Running synthetic pipeline for test/reporting validation...")
    report = run_v37_p1_pipeline(
        n_samples=args.n_samples,
        max_iter=args.max_iter,
        effect_size_threshold=EFFECT_SIZE_THRESHOLD,
        fake_runner=True,
    )

    print(f"\n--- Execution Summary ---")
    print(f"Terminal State:             {report.terminal_state}")
    print(f"Screening DE Runs:          {report.screening_de_runs}")
    print(f"Confirmation Executed:      {report.confirmation_executed}")
    print(f"Confirmation DE Runs:        {report.confirmation_de_runs}")
    print(f"Total DE Runs:              {report.total_de_runs}")
    print(f"Passing Screening Count:    {len(report.passing_screening_candidates)}")
    if report.selected_winner:
        print(f"Selected Winner:            {report.selected_winner.candidate.candidate_id}")
    print(f"Runtime:                    {report.runtime_s:.3f} s")

    if args.output_dir:
        out_dir = args.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        summary_csv = out_dir / "v37_p1_candidate_summary.csv"
        traj_csv = out_dir / "v37_p1_trajectories.csv"
        summary_json = out_dir / "v37_p1_summary.json"

        export_candidate_summary_csv(report, summary_csv)
        export_trajectories_csv(report, traj_csv)
        export_summary_json(report, summary_json)

        print(f"\nArtifacts exported to: {out_dir}")
        print(f"  - {summary_csv.name}")
        print(f"  - {traj_csv.name}")
        print(f"  - {summary_json.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
