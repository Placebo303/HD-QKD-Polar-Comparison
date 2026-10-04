"""Render compact P1 tables from the frozen primary JSON rows only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
ENCODINGS = ("GRAY", "NATURAL")
ORDERS = ("LSB_FIRST", "MSB_FIRST")
BLOCK_LENGTHS = (1024, 16384)
ANALYSIS_KEYS = (
    "H_A_bits_per_symbol",
    "H_A_given_B_bits_per_symbol",
    "V_A_given_B_bits_squared_per_symbol",
    "sum_h2_marginal_bit_error_bits_per_symbol",
    "sum_H_bit_given_B_bits_per_symbol",
    "sum_chain_H_bit_given_B_prefix_bits_per_symbol",
    "chain_closure_error_bits_per_symbol",
)
PLANE_KEYS = (
    "alice_bit_index_from_lsb",
    "H_bit_given_B_prefix_bits_per_symbol",
    "V_bit_given_B_prefix_bits_squared_per_symbol",
    "H_bit_given_B_bits_per_symbol",
    "marginal_bit_error_probability",
    "h2_marginal_bit_error_bits_per_symbol",
)
SCENARIO_KEYS = (
    "scenario_kind",
    "N_symbols",
    "joint_failure_assumption",
    "per_plane_failure_probability",
    "L_EC_bits",
    "tag_bits",
    "expected_failure_penalty_bits",
    "Y_expected_bits",
    "expected_f_numerator_bits",
    "f_expected_dimensionless",
    "budget_bits",
    "budget_slack_after_L_and_tag_bits",
    "budget_slack_expected_numerator_bits",
    "within_budget",
    "budget_projection",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(_repo_root()).as_posix()
    except ValueError:
        return str(path.resolve())


def _load_primary_rows(input_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        for encoding in ENCODINGS:
            for order in ORDERS:
                path = input_root / f"{source}_{encoding}_{order}.json"
                with path.open("r", encoding="utf-8") as stream:
                    record = json.load(stream)
                if record["source"] != source or record["encoding"] != encoding:
                    raise ValueError(f"primary JSON identity mismatch: {path}")
                if record["source_role"] != "TRAIN":
                    raise ValueError(f"primary JSON is not labeled TRAIN: {path}")
                analysis = record["analysis"]
                if analysis["order_name"] != order:
                    raise ValueError(f"primary JSON bit order mismatch: {path}")
                scenarios = record["scenarios"]
                if tuple(scenario["N_symbols"] for scenario in scenarios) != BLOCK_LENGTHS:
                    raise ValueError(f"primary JSON scenario lengths mismatch: {path}")
                if any(scenario["scenario_kind"] != "NORMAL_APPROX_SCENARIO" for scenario in scenarios):
                    raise ValueError(f"primary JSON scenario kind mismatch: {path}")
                rows.append(
                    {
                        "primary_json_path": _relative(path),
                        "record": record,
                    }
                )
    return rows


def _compact_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    compact = {key: analysis[key] for key in ANALYSIS_KEYS}
    compact["planes"] = [
        {key: plane[key] for key in PLANE_KEYS} for plane in analysis["planes"]
    ]
    compact["order_name"] = analysis["order_name"]
    compact["bit_order_from_lsb"] = analysis["bit_order_from_lsb"]
    return compact


def _compact_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    return {key: scenario[key] for key in SCENARIO_KEYS}


def _numbers_document(
    rows: list[dict[str, Any]], input_root: Path, *, overwrite: bool
) -> dict[str, Any]:
    metadata: list[dict[str, Any]] = []
    analyses: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str]] = set()
    for item in rows:
        record = item["record"]
        source_input = (record["source"], record["input_path"])
        if source_input not in seen_sources:
            metadata.append(
                {
                    "source": record["source"],
                    "input_path": record["input_path"],
                    "source_role": record["source_role"],
                    "N_train": record["N_train"],
                }
            )
            seen_sources.add(source_input)
        analyses.append(
            {
                "primary_json_path": item["primary_json_path"],
                "source": record["source"],
                "input_path": record["input_path"],
                "source_role": record["source_role"],
                "N_train": record["N_train"],
                "encoding": record["encoding"],
                "encoding_definition": record["encoding_definition"],
                "order": record["analysis"]["order_name"],
                "analysis": _compact_analysis(record["analysis"]),
            }
        )
        for scenario in record["scenarios"]:
            scenarios.append(
                {
                    "primary_json_path": item["primary_json_path"],
                    "source": record["source"],
                    "input_path": record["input_path"],
                    "source_role": record["source_role"],
                    "N_train": record["N_train"],
                    "encoding": record["encoding"],
                    "order": record["analysis"]["order_name"],
                    **_compact_scenario(scenario),
                }
            )

    command = (
        "timeout 120s env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "
        "docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/"
        "summarize_p1.py --input-root "
        f"{_relative(input_root)} --output-dir "
        "docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE"
    )
    if overwrite:
        command += " --overwrite"
    return {
        "record_kind": "P1_NUMERIC_INDEX_DRAFT",
        "reproduction_command": command,
        "input_root": _relative(input_root),
        "primary_json_inputs": [item["primary_json_path"] for item in rows],
        "source_metadata": metadata,
        "analysis_rows": analyses,
        "scenarios": scenarios,
        "same_source_practical_code_gap": "UNKNOWN",
        "scope_note": (
            "Mechanical summary of primary JSON only. No scientific acceptance, "
            "route decision, or practical decoder conclusion is encoded here."
        ),
    }


def _format(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _integer_cell(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return _format(value)


def _bits_cell(value: Any) -> str:
    return f"{float(value):.2f}"


def _entropy_cell(value: Any) -> str:
    return f"{float(value):.10g}"


def _f_cell(value: Any) -> str:
    return "null" if value is None else f"{float(value):.4f}"


def _scenario_table_row(record: dict[str, Any], scenario: dict[str, Any]) -> str:
    cells = (
        record["source"],
        record["analysis"]["order_name"],
        _integer_cell(scenario["N_symbols"]),
        _integer_cell(scenario["L_EC_bits"]),
        _integer_cell(scenario["tag_bits"]),
        _bits_cell(scenario["expected_failure_penalty_bits"]),
        _f_cell(scenario["f_expected_dimensionless"]),
        _bits_cell(scenario["budget_slack_after_L_and_tag_bits"]),
        _bits_cell(scenario["budget_slack_expected_numerator_bits"]),
    )
    return "| " + " | ".join(cells) + " |"


TABLE_HEADER = (
    "| Source | Order | N (symbols/block) | L_EC (bits/block) | "
    "Tag (bits/block) | Failure penalty (bits/block) | "
    "f_expected (dimensionless) | Nominal slack (bits/block) | "
    "Expected-numerator slack (bits/block) |"
)
TABLE_SEPARATOR = "|---|---|---:|---:|---:|---:|---:|---:|---:|"

ENTROPY_HEADER = (
    "| Source | Encoding | H(A given B) (bits/symbol) | "
    "Σh₂(marginal bit error) (bits/symbol) | "
    "ΣH(bit given full B) (bits/symbol) |"
)
ENTROPY_SEPARATOR = "|---|---|---:|---:|---:|"


def _entropy_table_row(record: dict[str, Any]) -> str:
    analysis = record["analysis"]
    cells = (
        record["source"],
        record["encoding"],
        _entropy_cell(analysis["H_A_given_B_bits_per_symbol"]),
        _entropy_cell(analysis["sum_h2_marginal_bit_error_bits_per_symbol"]),
        _entropy_cell(analysis["sum_H_bit_given_B_bits_per_symbol"]),
    )
    return "| " + " | ".join(cells) + " |"


def _render_table(rows: list[dict[str, Any]], input_root: Path) -> str:
    by_encoding: dict[str, list[str]] = {encoding: [] for encoding in ENCODINGS}
    entropy_rows: list[str] = []
    for item in rows:
        record = item["record"]
        for scenario in record["scenarios"]:
            by_encoding[record["encoding"]].append(
                _scenario_table_row(record, scenario)
            )
        if record["analysis"]["order_name"] == "LSB_FIRST":
            entropy_rows.append(_entropy_table_row(record))

    sample_scenario = rows[0]["record"]["scenarios"][0]
    budget_formula = sample_scenario["budget_projection"]["formula"]
    epsilon = sample_scenario["joint_failure_assumption"]
    per_plane_epsilon = sample_scenario["per_plane_failure_probability"]
    tag_bits = sample_scenario["tag_bits"]
    header = [
        "# P1 numeric table draft",
        "",
        f"Primary JSON source: `{_relative(input_root)}`; source role is TRAIN.",
        f"All rows are `{sample_scenario['scenario_kind']}` planning scenarios; "
        f"joint failure assumption ε={_format(epsilon)} "
        f"(per-plane ε={_format(per_plane_epsilon)}), one shared verification tag "
        f"of {_format(tag_bits)} bits per block.",
        f"The budget is the explicit projection `{budget_formula}`; it is an assumption, "
        "not an observed long-block baseline. Entropies use the primary unsmoothed "
        "plug-in results. Same-source practical-code gap: UNKNOWN. No route verdict "
        "or scientific acceptance is included.",
        "",
        "## Entropy summary",
        "",
        "One row per source and encoding uses the LSB_FIRST primary JSON row; both "
        "orders remain available at full precision in P1_NUMBERS.json.",
        "",
        ENTROPY_HEADER,
        ENTROPY_SEPARATOR,
        *entropy_rows,
        "",
        "## Gray encoding (primary)",
        "",
        TABLE_HEADER,
        TABLE_SEPARATOR,
        *by_encoding["GRAY"],
        "",
        "## Natural encoding sensitivity rows",
        "",
        TABLE_HEADER,
        TABLE_SEPARATOR,
        *by_encoding["NATURAL"],
        "",
    ]
    return "\n".join(header)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("workspace/msd_p1/e76e3e7aa8bb453a885a5fca0c69333a"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="regenerate these two derived draft outputs",
    )
    args = parser.parse_args(argv)
    repo = _repo_root()
    input_root = args.input_root if args.input_root.is_absolute() else repo / args.input_root
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    rows = _load_primary_rows(input_root)
    if len(rows) != 12:
        raise ValueError(f"expected 12 primary JSON rows, got {len(rows)}")
    numbers = _numbers_document(rows, input_root, overwrite=args.overwrite)
    table = _render_table(rows, input_root)
    numbers_path = output_dir / "P1_NUMBERS.json"
    table_path = output_dir / "P1_TABLE.md"
    if (numbers_path.exists() or table_path.exists()) and not args.overwrite:
        raise FileExistsError("refusing to overwrite an existing P1 draft output")
    write_mode = "w" if args.overwrite else "x"
    with numbers_path.open(write_mode, encoding="utf-8", newline="\n") as stream:
        json.dump(numbers, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    with table_path.open(write_mode, encoding="utf-8", newline="\n") as stream:
        stream.write(table)
    print(_relative(numbers_path))
    print(_relative(table_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
