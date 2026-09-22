"""V38-P0 Single Authorized Development Run Execution Script."""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, "comparison_bench/src")

from comparison_bench.formal_ir.v38_architecture_triage import (
    run_v38_development,
)


def main():
    print("============================================================")
    print("Starting V38-P0 Development Execution")
    print("============================================================")
    t0 = time.time()

    out_dir = Path("comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Execute the single authorized development run
    results = run_v38_development(
        development_execution_authorized=True,
        fake_runner=False,
    )
    t1 = time.time()
    print(f"Development execution completed in {t1 - t0:.2f}s")

    # 1. Save all 27 structural prototype metrics
    flat_prototypes = []
    for lane_name, src_dict in results["all_prototype_metrics"].items():
        for src, proto_list in src_dict.items():
            for m in proto_list:
                flat_prototypes.append(m)

    proto_csv_path = out_dir / "v38_structural_prototypes.csv"
    if flat_prototypes:
        all_keys: list[str] = []
        for p in flat_prototypes:
            for k in p.keys():
                if k not in all_keys and k != "position_permutations":
                    all_keys.append(k)
        with open(proto_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            for p in flat_prototypes:
                row = {k: p.get(k, "") for k in all_keys}
                writer.writerow(row)

    proto_json_path = out_dir / "v38_structural_prototypes.json"
    with open(proto_json_path, "w", encoding="utf-8") as f:
        json.dump(flat_prototypes, f, indent=2)

    # 2. Save all block evaluation records
    block_records = results["all_block_records"]
    block_csv_path = out_dir / "v38_development_block_records.csv"
    if block_records:
        b_all_keys: list[str] = []
        for r in block_records:
            for k in r.keys():
                if k not in b_all_keys:
                    b_all_keys.append(k)
        with open(block_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=b_all_keys)
            writer.writeheader()
            for r in block_records:
                writer.writerow({k: r.get(k, "") for k in b_all_keys})

    block_json_path = out_dir / "v38_development_block_records.json"
    with open(block_json_path, "w", encoding="utf-8") as f:
        json.dump(block_records, f, indent=2)

    # 3. Save lane aggregates and triage summary
    summary_path = out_dir / "v38_triage_summary.json"
    summary_data = {
        "cycle_id": "V38P0",
        "lifecycle_state": "DEVELOPMENT_RESULT_CANDIDATE",
        "terminal_state": results["terminal_state"],
        "prototypes_generated_count": results["prototypes_generated_count"],
        "decoder_runs_count": results["decoder_runs_count"],
        "lane_statuses": results["lane_statuses"],
        "lane_aggregates": results["lane_aggregates"],
        "execution_runtime_s": float(t1 - t0),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # 4. Save winning prototype matrices
    winning_matrices = {}
    for lane_name, src_dict in results["lane_winners"].items():
        for src, (H_win, win_m) in src_dict.items():
            key = f"{lane_name}_{src}_s{win_m['construction_seed']}"
            winning_matrices[key] = H_win
    np.savez_compressed(out_dir / "v38_winning_matrices.npz", **winning_matrices)

    print(f"Artifacts successfully saved to {out_dir}")
    print(f"Terminal State: {results['terminal_state']}")
    print(f"Lane Statuses: {results['lane_statuses']}")
    for lane, agg in results["lane_aggregates"].items():
        print(
            f"Lane {lane} summary: records={agg.get('records_count')}, "
            f"exact={agg.get('exact_recovery_count')}, "
            f"mean_errs={agg.get('overall_mean_errors'):.2f}, "
            f"median_errs={agg.get('overall_median_errors')}, "
            f"improve={agg.get('improve_count')}, "
            f"equal={agg.get('equal_count')}, "
            f"worsen={agg.get('worsen_count')}"
        )


if __name__ == "__main__":
    main()
