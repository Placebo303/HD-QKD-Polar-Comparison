"""V38R1 decoder-only successor runner and additive evidence writer."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v38_architecture_triage import (  # noqa: E402
    V38R1_RUN01_METRICS_PATH,
    V38R1_RUN02_ROOT,
    run_v38r1_development,
)


def _write_records_csv(path: Path, records: list[dict[str, Any]]) -> None:
    keys: list[str] = []
    for record in records:
        for key in record:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for record in records:
            row = {
                key: json.dumps(value, sort_keys=True)
                if isinstance(value, (list, dict))
                else value
                for key, value in record.items()
            }
            writer.writerow(row)


def write_v38r1_run02(
    results: dict[str, Any],
    output_root: Path | str = V38R1_RUN02_ROOT,
) -> Path:
    """Write the fixed additive V38R1 run_02 evidence; never overwrite."""
    root = Path(output_root)
    if root.exists():
        raise FileExistsError(f"Refusing to overwrite existing V38R1 output: {root}")

    winner_metrics = results.get("winner_metrics", [])
    block_records = results.get("all_block_records", [])
    if len(winner_metrics) != 9:
        raise ValueError(f"V38R1 output requires 9 winner metrics, got {len(winner_metrics)}")
    if len(block_records) != 45 or results.get("decoder_runs_count") != 45:
        raise ValueError("V38R1 output requires exactly 45 decoder records/calls")

    root.mkdir(parents=True)
    with (root / "v38r1_winning_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(winner_metrics, handle, indent=2)
    _write_records_csv(root / "v38r1_winning_metrics.csv", winner_metrics)

    with (root / "v38r1_development_block_records.json").open("w", encoding="utf-8") as handle:
        json.dump(block_records, handle, indent=2)
    _write_records_csv(root / "v38r1_development_block_records.csv", block_records)

    summary = {
        "cycle_id": results.get("cycle_id", "V38R1"),
        "predecessor_cycle": results.get("predecessor_cycle", "V38P0"),
        "lifecycle_state": "DEVELOPMENT_RESULT_CANDIDATE",
        "execution_status": "DEVELOPMENT_RESULT_CANDIDATE",
        "winners_reconstructed_count": results["winners_reconstructed_count"],
        "decoder_runs_count": results["decoder_runs_count"],
        "lane_statuses": results["lane_statuses"],
        "lane_aggregates": results["lane_aggregates"],
        "triage_gate_details": results["triage_gate_details"],
        "terminal_state": results["terminal_state"],
        "fake_runner": results.get("fake_runner", False),
        "run_01_immutable_invalid_evidence": True,
        "npz_input_used": False,
    }
    with (root / "v38r1_triage_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return root


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guarded V38R1 decoder-only successor.")
    parser.add_argument(
        "--development-execution-authorized",
        action="store_true",
        help="Required explicit authorization for the 45-call development run.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.development_execution_authorized:
        # Keep the module-level guard authoritative for the default path.
        run_v38r1_development(development_execution_authorized=False)

    if V38R1_RUN02_ROOT.exists():
        raise FileExistsError(f"Refusing to overwrite existing V38R1 output: {V38R1_RUN02_ROOT}")

    results = run_v38r1_development(
        development_execution_authorized=True,
        fake_runner=False,
        reference_metrics_path=V38R1_RUN01_METRICS_PATH,
    )
    output_root = write_v38r1_run02(results, V38R1_RUN02_ROOT)
    print(f"V38R1 additive evidence written to {output_root}")
    print(f"Terminal state: {results['terminal_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
