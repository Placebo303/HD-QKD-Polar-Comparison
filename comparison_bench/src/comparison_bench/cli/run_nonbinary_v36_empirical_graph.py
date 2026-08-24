"""CLI Runner for V36 Empirical-P Irregular LDPC & Source-Native Graph Development.

Orchestrates:
1. Stage A0: Decoder iteration diagnostic (30 vs 60 iters on 9 blocks of true V31 baseline).
2. Stage A1: GF(32) empirical-P irregular ensemble DE screening (coarse + confirmation).
3. Stage A2: Source-native PEG graph construction (184x1024, 190x1024, 192x1024).
4. Stage A3: Finite paired development screen on 15 blocks (V31 baseline vs DE shortlist).
5. Stage A4: Moderate-degree incremental syndrome hierarchy (conditional).
6. Automatic report & claim ledger generation.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..formal_ir.nonbinary_v36_empirical_graph import (
    A0_SEEDS,
    A3_SEEDS,
    DEFAULT_DAMPING_ALPHA,
    FIELD_ID,
    FIELD_POLY,
    FIELD_Q,
    INCREMENTAL_EXTRA_BITS,
    INCREMENTAL_EXTRA_CHECKS,
    INCREMENTAL_STAGES,
    M2_BY_SOURCE,
    METHOD,
    N_SYMBOLS,
    RATES_BY_SOURCE,
    SOURCES,
    STATUS_DE_SHORTLIST_READY,
    STATUS_FINITE_GRAPH_ADVANCE,
    STATUS_NB_DEVELOPMENT_CANDIDATE_FOUND,
    STATUS_NO_DE_ADVANCE,
    STATUS_NO_FINITE_GRAPH_ADVANCE,
    STATUS_NO_INCREMENTAL_ADVANCE,
    TAG_BITS,
    audit_finite_graph,
    build_v36_incremental_matrix,
    construct_source_native_peg_matrix,
    generate_v36_candidate_grid,
    generate_v36_development_report,
    load_v25_channel_counts,
    load_v31_qc_baseline_matrices,
    run_a0_iteration_diagnostic,
    run_v36_a3_finite_screen,
    run_v36_a4_incremental_evaluation,
    run_v36_de_screening,
)

CSV_COLUMNS = [
    "source",
    "seed",
    "method",
    "graph_id",
    "decoder_schedule",
    "redundancy_stage",
    "exact_l2",
    "syndrome_ok",
    "tag_ok",
    "false_accept",
    "errors_initial",
    "errors_final",
    "iterations",
    "runtime_s",
    "syndrome_leakage_bits",
    "cumulative_leakage_bits",
    "status",
]


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="V36 Empirical-P Irregular LDPC & Source-Native Graph Development Runner"
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v36_empirical_graph_development/run_01",
        help="Root directory for output artifacts",
    )
    parser.add_argument(
        "--stages",
        type=str,
        default="auto",
        choices=["auto", "all", "A0", "A1", "A2", "A3", "A4"],
        help="Stage execution mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run preflight validation without iterative computation",
    )
    parser.add_argument(
        "--fake-runner",
        action="store_true",
        help="Use fast mock execution seam for test suite",
    )
    return parser.parse_args(args)


def run_v36_pipeline(
    output_root: Path,
    stages_mode: str = "auto",
    dry_run: bool = False,
    fake_runner: bool = False,
) -> dict[str, Any]:
    """Execute the full V36 development pipeline."""
    start_wallclock = time.perf_counter()
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[4]

    print("=== Starting V36 Empirical-P Irregular Graph Development Pipeline ===")
    print(f"Output Root: {output_root}")
    print(f"Stages Mode: {stages_mode}")

    # 1. Load V25 Empirical Channel Joint Counts & V31 Baseline Matrices
    print("\n[1/6] Loading V25 empirical channel counts and V31 baseline matrices...")
    channel_counts = load_v25_channel_counts()
    baseline_mats = load_v31_qc_baseline_matrices()
    for src in SOURCES:
        print(f"  Source {src}: counts {channel_counts[src].shape}, baseline H {baseline_mats[src].shape}")

    if dry_run:
        print("\n[DRY RUN] Preflight validation passed.")
        return {"status": "dry_run_completed", "terminal_status": "DRY_RUN"}

    stage_summaries: dict[str, Any] = {}
    all_finite_records: list[Any] = []
    all_incremental_records: list[Any] = []
    terminal_status: str = STATUS_NO_DE_ADVANCE

    # -----------------------------------------------------------------------
    # Stage A0: Decoder Iteration Diagnostic (30 vs 60 iters on V31 baseline)
    # -----------------------------------------------------------------------
    print("\n[Stage A0] Running decoder iteration budget diagnostic (30 vs 60 iters)...")
    a0_result = run_a0_iteration_diagnostic(
        channel_counts=channel_counts,
        baseline_mats=baseline_mats,
        max_iters=(30, 60),
        damping_alpha=1.0,
        fake_runner=fake_runner,
    )
    selected_max_iter = int(a0_result["selected_max_iter"])
    stage_summaries["A0_decoder_iteration_diagnostic"] = a0_result
    print(f"  -> A0 Result: selected unified max_iter = {selected_max_iter} (Drops: {a0_result['median_relative_drops']})")

    # -----------------------------------------------------------------------
    # Stage A1: GF(32) Empirical-P Irregular Ensemble DE Screening
    # -----------------------------------------------------------------------
    print("\n[Stage A1] Generating candidate degree distribution grid and running 2-tier DE screening...")
    candidate_grid = generate_v36_candidate_grid()
    print(f"  -> Generated {len(candidate_grid)} candidate distributions on grid")

    # Write grid CSV
    grid_csv_path = output_root / "de_candidate_grid.csv"
    with open(grid_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "lambda_edge", "dbar_v", "max_check_degree"])
        for c in candidate_grid:
            writer.writerow([c["candidate_id"], str(c["lambda_edge"]), f"{c['dbar_v']:.4f}", c["max_check_degree"]])

    de_screen_result = run_v36_de_screening(
        channel_counts=channel_counts,
        candidates=candidate_grid,
        coarse_samples=1000,
        coarse_max_iter=30,
        conf_samples=4000,
        conf_max_iter=60,
        fake_runner=fake_runner,
    )
    stage_summaries["A1_de_candidate_screening"] = {
        "status": de_screen_result["status"],
        "coarse_evaluated": de_screen_result["coarse_evaluated"],
        "coarse_passed": de_screen_result["coarse_passed"],
        "confirmation_evaluated": de_screen_result["confirmation_evaluated"],
        "top_candidates": de_screen_result["top_candidates"],
        "baseline_de": de_screen_result["baseline_de"],
    }

    # Write coarse results CSV
    coarse_csv_path = output_root / "de_coarse_results.csv"
    with open(coarse_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "dbar_v", "max_check_degree", "worst_source_entropy", "degraded_vs_baseline"])
        for r in de_screen_result["coarse_records"]:
            writer.writerow([r["candidate_id"], f"{r['dbar_v']:.4f}", r["max_check_degree"], f"{r['worst_source_entropy']:.6f}", r["degraded_vs_baseline"]])

    # Write confirmation results CSV
    conf_csv_path = output_root / "de_confirmation_results.csv"
    with open(conf_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "dbar_v", "max_check_degree", "mean_entropy", "std_entropy", "worst_entropy", "all_converged"])
        for r in de_screen_result["confirmation_records"]:
            writer.writerow([r["candidate_id"], f"{r['dbar_v']:.4f}", r["max_check_degree"], f"{r['mean_entropy']:.6f}", f"{r['std_entropy']:.6f}", f"{r['worst_entropy']:.6f}", r["all_converged"]])

    # Write shortlist JSON
    shortlist_json_path = output_root / "de_shortlist.json"
    with open(shortlist_json_path, "w", encoding="utf-8") as f:
        json.dump(de_screen_result["top_candidates"], f, indent=2)

    top_candidates = de_screen_result["top_candidates"]
    de_status = de_screen_result["status"]
    print(f"  -> Stage A1 Status: {de_status} (Shortlist: {len(top_candidates)} candidates)")

    if de_status != STATUS_DE_SHORTLIST_READY or not top_candidates:
        terminal_status = STATUS_NO_DE_ADVANCE
        print("\n>>> Stage A1 did not yield advancing candidates. Stopping pipeline.")
    else:
        # -------------------------------------------------------------------
        # Stage A2: Source-Native Finite Graph Construction & Audit
        # -------------------------------------------------------------------
        print("\n[Stage A2] Constructing source-native PEG finite graphs...")
        candidate_mats_by_id: dict[str, dict[str, np.ndarray]] = {}
        finite_metrics_rows: list[dict[str, Any]] = []

        for cand in top_candidates:
            cid = cand["candidate_id"]
            lam = cand["lambda_edge"]
            candidate_mats_by_id[cid] = {}

            for src in SOURCES:
                dense_H, audit = construct_source_native_peg_matrix(
                    lambda_edge=lam,
                    source=src,
                    n=N_SYMBOLS,
                    graph_seed=363001,
                    coeff_seed=364001,
                    backup_coeff_seed=364002,
                )
                candidate_mats_by_id[cid][src] = dense_H
                finite_metrics_rows.append({
                    "candidate_id": cid,
                    "source": src,
                    "target_m": audit["target_m"],
                    "target_n": audit["target_n"],
                    "rank": audit["rank"],
                    "rank_full": audit["rank_full"],
                    "mean_check_degree": f"{audit['mean_check_degree']:.4f}",
                    "max_check_degree": audit["max_check_degree"],
                    "four_cycles": audit["four_cycles_count"],
                    "degree2_cycles": audit["degree2_cycles_count"],
                    "eliminated": audit["eliminated"],
                })
                print(f"  [{cid} | {src}] Native H: {dense_H.shape}, rank: {audit['rank']}/{audit['target_m']}, max dc: {audit['max_check_degree']}, c4: {audit['four_cycles_count']}")

        # Write finite graph metrics CSV
        metrics_csv_path = output_root / "finite_graph_metrics.csv"
        with open(metrics_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(finite_metrics_rows[0].keys()))
            writer.writeheader()
            for r in finite_metrics_rows:
                writer.writerow(r)

        stage_summaries["A2_source_native_graphs"] = {
            "candidates_constructed": len(candidate_mats_by_id),
            "metrics": finite_metrics_rows,
        }

        # -------------------------------------------------------------------
        # Stage A3: Finite Paired Development Screen (15 Blocks)
        # -----------------------------------------------------------------------
        print(f"\n[Stage A3] Executing paired finite development screen on 15 blocks (max_iter={selected_max_iter})...")
        a3_result = run_v36_a3_finite_screen(
            channel_counts=channel_counts,
            baseline_mats=baseline_mats,
            candidate_mats_by_id=candidate_mats_by_id,
            max_iter=selected_max_iter,
            damping_alpha=1.0,
            fake_runner=fake_runner,
        )
        all_finite_records = a3_result["records"]
        stage_summaries["A3_finite_paired_screen"] = {
            "status": a3_result["status"],
            "best_candidate_id": a3_result["best_candidate_id"],
            "candidate_summaries": a3_result["candidate_summaries"],
            "total_records": len(all_finite_records),
        }

        # Write finite block results CSV
        finite_csv_path = output_root / "finite_block_results.csv"
        with open(finite_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for r in all_finite_records:
                writer.writerow(r.to_csv_dict())

        a3_status = a3_result["status"]
        best_candidate = a3_result["best_candidate_id"]
        print(f"  -> Stage A3 Status: {a3_status} (Advancing candidate: {best_candidate})")

        # -------------------------------------------------------------------
        # Stage A4: Moderate-Degree Incremental Syndrome (Conditional)
        # -------------------------------------------------------------------
        if a3_status == STATUS_FINITE_GRAPH_ADVANCE and best_candidate is not None:
            print(f"\n[Stage A4] Constructing and evaluating moderate-degree incremental syndrome on candidate {best_candidate}...")
            best_mats = candidate_mats_by_id[best_candidate]
            stage_mats_by_src: dict[str, dict[str, np.ndarray]] = {}
            for src in SOURCES:
                _, stage_mats = build_v36_incremental_matrix(
                    H_base=best_mats[src],
                    source=src,
                    target_degree_range=(10, 14),
                    seed=365001,
                )
                stage_mats_by_src[src] = stage_mats

            a4_result = run_v36_a4_incremental_evaluation(
                channel_counts=channel_counts,
                stage_mats_by_src=stage_mats_by_src,
                candidate_id=best_candidate,
                max_iter=selected_max_iter,
                damping_alpha=1.0,
                fake_runner=fake_runner,
            )
            all_incremental_records = a4_result["records"]
            terminal_status = a4_result["status"]
            stage_summaries["A4_incremental_syndrome"] = {
                "executed": True,
                "status": a4_result["status"],
                "exact_by_src_stage": a4_result["exact_by_src_stage"],
                "total_false_accepts": a4_result["total_false_accepts"],
            }

            # Write incremental block results CSV
            inc_csv_path = output_root / "incremental_block_results.csv"
            with open(inc_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                for r in all_incremental_records:
                    writer.writerow(r.to_csv_dict())
            print(f"  -> Stage A4 Status: {terminal_status}")
        else:
            terminal_status = STATUS_NO_FINITE_GRAPH_ADVANCE
            stage_summaries["A4_incremental_syndrome"] = {
                "executed": False,
                "status": "SKIPPED",
            }
            # Write empty incremental CSV header
            inc_csv_path = output_root / "incremental_block_results.csv"
            with open(inc_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
            print("\n>>> Stage A3 did not achieve advance threshold. Stage A4 skipped.")

    # -----------------------------------------------------------------------
    # Final Manifest & Summary Artifacts
    # -----------------------------------------------------------------------
    total_wallclock = time.perf_counter() - start_wallclock
    summary_payload = {
        "schema": "v36_empirical_graph_development_summary_v1",
        "method": METHOD,
        "terminal_status": terminal_status,
        "stages_mode": stages_mode,
        "stage_summaries": stage_summaries,
        "overall_metrics": {
            "total_finite_records": len(all_finite_records),
            "total_incremental_records": len(all_incremental_records),
            "terminal_status": terminal_status,
            "total_wallclock_s": round(total_wallclock, 4),
        },
    }

    summary_json_path = output_root / "summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print(f"\n[Artifact] Wrote JSON summary: {summary_json_path}")

    manifest_payload = {
        "schema": "v36_empirical_graph_manifest_v1",
        "method": METHOD,
        "field_id": FIELD_ID,
        "terminal_status": terminal_status,
        "files": [
            "de_candidate_grid.csv",
            "de_coarse_results.csv",
            "de_confirmation_results.csv",
            "de_shortlist.json",
            "finite_graph_metrics.csv",
            "finite_block_results.csv",
            "incremental_block_results.csv",
            "summary.json",
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest_path = output_root / "RUN_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)
    print(f"[Artifact] Wrote Run Manifest: {manifest_path}")

    # Generate synthesis report and claim ledger
    report_doc_path = repo_root / "docs/nbldpc-v36-empirical-graph-development.md"
    report_copy_path = output_root / "development_report.md"
    report_text = generate_v36_development_report(
        summary=summary_payload,
        all_records=all_finite_records + all_incremental_records,
        output_path=report_doc_path,
    )
    report_copy_path.write_text(report_text, encoding="utf-8")
    print(f"[Artifact] Automatically generated synthesis report: {report_doc_path}")

    print(f"\n=== V36 Pipeline Complete: Terminal Status = {terminal_status} ===")
    return summary_payload


def main() -> None:
    args = parse_args()
    run_v36_pipeline(
        output_root=Path(args.output_root),
        stages_mode=args.stages,
        dry_run=args.dry_run,
        fake_runner=args.fake_runner,
    )


if __name__ == "__main__":
    main()
