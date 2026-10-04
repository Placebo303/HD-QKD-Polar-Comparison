"""Compare uniform and variance-dependent normal budgets from saved P1 scalars."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any
import uuid

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from comparison_bench.src.comparison_bench.formal_ir.msd_error_allocation import (
    allocate_normal_error_budget,
    normal_stage_budgets,
)


EPSILON_TOTAL = 0.01
TAG_BITS = 64.0
PROJECTION_FORMULA = "1040*N_symbols/1024 + 64 shared tag bits"
PROJECTION_STATUS = "planning projection; not an observed long-block baseline"
EXPECTED_SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
EXPECTED_ENCODINGS = ("NATURAL", "GRAY")
EXPECTED_ORDERS = ("LSB_FIRST", "MSB_FIRST")
EXPECTED_LENGTHS = (1024, 16384)
P1_NUMBERS_RELATIVE = Path(
    "docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P1_NUMBERS.json"
)


def _close(actual: float, expected: float, label: str) -> None:
    if not math.isfinite(actual) or not math.isfinite(expected):
        raise ValueError(f"{label}: expected finite numbers")
    if abs(actual - expected) > 1e-9:
        raise ValueError(
            f"{label}: saved P1 value {expected:.17g} != recomputed {actual:.17g}"
        )


def _number(record: dict[str, Any], key: str) -> float:
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"saved P1 field {key} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"saved P1 field {key} must be finite")
    return result


def _join_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (str(record["source"]), str(record["encoding"]), str(record["order"]))


def _scenario_key(record: dict[str, Any]) -> tuple[str, str, str, int]:
    return (*_join_key(record), int(record["N_symbols"]))


def _expected_join_keys() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (source, encoding, order)
        for source in EXPECTED_SOURCES
        for encoding in EXPECTED_ENCODINGS
        for order in EXPECTED_ORDERS
    )


def _load_saved_summary(repo_root: Path) -> tuple[dict, dict]:
    input_path = repo_root / P1_NUMBERS_RELATIVE
    data = json.loads(input_path.read_text(encoding="utf-8"))
    analysis_rows = data.get("analysis_rows")
    scenarios = data.get("scenarios")
    if not isinstance(analysis_rows, list) or not isinstance(scenarios, list):
        raise ValueError("P1_NUMBERS.json must contain analysis_rows and scenarios lists")
    if len(analysis_rows) != 12 or len(scenarios) != 24:
        raise ValueError(
            f"expected 12 P1 analysis rows and 24 scenarios; got "
            f"{len(analysis_rows)} and {len(scenarios)}"
        )

    analysis_by_key: dict[tuple[str, str, str], dict] = {}
    for row in analysis_rows:
        key = _join_key(row)
        if key in analysis_by_key:
            raise ValueError(f"duplicate P1 analysis row for {key}")
        if key not in _expected_join_keys():
            raise ValueError(f"unexpected P1 analysis row {key}")
        if row.get("source_role") != "TRAIN":
            raise ValueError(f"P1 row {key} does not have source_role TRAIN")
        analysis_by_key[key] = row
    if set(analysis_by_key) != set(_expected_join_keys()):
        raise ValueError("P1 analysis rows do not cover the frozen source/encoding/order set")

    scenario_by_key: dict[tuple[str, str, str, int], dict] = {}
    for row in scenarios:
        key = _scenario_key(row)
        if key in scenario_by_key:
            raise ValueError(f"duplicate P1 scenario {key}")
        if key[:3] not in analysis_by_key or key[3] not in EXPECTED_LENGTHS:
            raise ValueError(f"unexpected P1 scenario {key}")
        if row.get("source_role") != "TRAIN":
            raise ValueError(f"P1 scenario {key} does not have source_role TRAIN")
        scenario_by_key[key] = row
    expected_scenario_keys = {
        (*join_key, N) for join_key in _expected_join_keys() for N in EXPECTED_LENGTHS
    }
    if set(scenario_by_key) != expected_scenario_keys:
        raise ValueError("P1 scenarios do not cover the frozen 12 by 2 matrix")
    return analysis_by_key, scenario_by_key


def _validate_source_metadata(analysis_row: dict, scenario: dict, key: tuple) -> None:
    for field in ("source", "encoding", "order", "source_role", "input_path", "primary_json_path"):
        if analysis_row.get(field) != scenario.get(field):
            raise ValueError(f"P1 metadata mismatch for {key}: {field}")
    if analysis_row.get("source_role") != "TRAIN":
        raise ValueError(f"P1 analysis row {key} is outside TRAIN scope")


def _verify_projection(scenario: dict, N: int, key: tuple) -> float:
    if scenario.get("joint_failure_assumption") != EPSILON_TOTAL:
        raise ValueError(f"P1 scenario {key} does not use the frozen 0.01 joint assumption")
    if scenario.get("tag_bits") != TAG_BITS:
        raise ValueError(f"P1 scenario {key} does not use the frozen 64-bit tag")
    projection = scenario.get("budget_projection")
    if not isinstance(projection, dict):
        raise ValueError(f"P1 scenario {key} has no budget_projection")
    if projection.get("formula") != PROJECTION_FORMULA:
        raise ValueError(f"P1 scenario {key} has an unexpected projection formula")
    if projection.get("status") != PROJECTION_STATUS:
        raise ValueError(f"P1 scenario {key} has an unexpected projection status")
    if projection.get("shared_tag_bits") != 64:
        raise ValueError(f"P1 scenario {key} has an unexpected projected shared tag")
    ec_projection = 1040.0 * N / 1024.0
    budget_projection = ec_projection + TAG_BITS
    _close(_number(projection, "ec_bits_assumed"), ec_projection, f"{key} projected EC bits")
    _close(_number(projection, "bits"), budget_projection, f"{key} projected budget bits")
    _close(_number(scenario, "budget_bits"), budget_projection, f"{key} scenario budget bits")
    return budget_projection


def _ledger(
    N: int,
    H_A: float,
    H_A_given_B: float,
    L_EC: int,
    tag_bits: float,
    p_fail: float,
    budget_bits: float,
) -> dict[str, Any]:
    H_A_total = N * H_A
    kept = H_A_total - L_EC
    failure_penalty = kept * p_fail
    expected_numerator = L_EC + tag_bits + failure_penalty
    Y_expected = kept - tag_bits - failure_penalty
    denominator = N * H_A_given_B
    valid_yield = kept >= 0.0
    f_expected = (
        expected_numerator / denominator
        if valid_yield and denominator > 0.0
        else None
    )
    return {
        "H_A_total_bits": H_A_total,
        "L_EC_bits": L_EC,
        "tag_bits": tag_bits,
        "kept_bits": kept,
        "failure_assumption": p_fail,
        "expected_failure_penalty_bits": failure_penalty,
        "Y_expected_bits": Y_expected,
        "H_A_given_B_total_bits": denominator,
        "expected_f_numerator_bits": expected_numerator,
        "f_expected_dimensionless": f_expected,
        "budget_bits": budget_bits,
        "budget_slack_after_L_and_tag_bits": budget_bits - L_EC - tag_bits,
        "budget_slack_expected_numerator_bits": budget_bits - expected_numerator,
        "within_budget_after_L_and_tag": L_EC + tag_bits <= budget_bits,
        "valid_yield": valid_yield,
    }


def _verify_uniform_ledger(saved: dict, recomputed: dict, key: tuple) -> None:
    if not isinstance(saved.get("L_EC_bits"), int) or isinstance(saved.get("L_EC_bits"), bool):
        raise ValueError(f"P1 scenario {key} L_EC_bits must be an integer")
    if recomputed["L_EC_bits"] != saved["L_EC_bits"]:
        raise ValueError(
            f"uniform baseline mismatch for {key}: L_EC_bits saved="
            f"{saved['L_EC_bits']} recomputed={recomputed['L_EC_bits']}"
        )
    numeric_fields = (
        "expected_failure_penalty_bits",
        "Y_expected_bits",
        "expected_f_numerator_bits",
        "budget_slack_after_L_and_tag_bits",
        "budget_slack_expected_numerator_bits",
    )
    for field in numeric_fields:
        _close(
            recomputed[field],
            _number(saved, field),
            f"uniform baseline {key} {field}",
        )
    if recomputed["f_expected_dimensionless"] is None:
        if saved.get("f_expected_dimensionless") is not None:
            raise ValueError(f"uniform baseline {key} has an unexpected defined f")
    else:
        _close(
            recomputed["f_expected_dimensionless"],
            _number(saved, "f_expected_dimensionless"),
            f"uniform baseline {key} f_expected_dimensionless",
        )
    if recomputed["within_budget_after_L_and_tag"] is not saved.get("within_budget"):
        raise ValueError(f"uniform baseline {key} within_budget flag mismatch")


def _stage_rows(
    planes: list[dict], budgets, epsilons: tuple[float, ...]
) -> list[dict[str, Any]]:
    rows = []
    for plane, epsilon, z, continuous, raw_ceil, clipped in zip(
        planes,
        epsilons,
        budgets.z_values,
        budgets.continuous_bits_per_stage,
        budgets.raw_ceil_bits_per_stage,
        budgets.clipped_bits_per_stage,
    ):
        rows.append(
            {
                "alice_bit_index_from_lsb": int(plane["alice_bit_index_from_lsb"]),
                "H_bits_per_symbol": float(
                    plane["H_bit_given_B_prefix_bits_per_symbol"]
                ),
                "V_bits_squared_per_symbol": float(
                    plane["V_bit_given_B_prefix_bits_squared_per_symbol"]
                ),
                "epsilon": epsilon,
                "z": z,
                "continuous_bits_per_stage": continuous,
                "raw_ceil_bits_per_stage": raw_ceil,
                "clipped_bits_per_stage": clipped,
            }
        )
    return rows


def _process_scenario(
    analysis_row: dict, saved: dict, key: tuple[str, str, str, int]
) -> dict[str, Any]:
    join_key = key[:3]
    N = key[3]
    _validate_source_metadata(analysis_row, saved, key)
    if int(analysis_row.get("N_train", 0)) != int(saved.get("N_train", -1)):
        raise ValueError(f"P1 N_train mismatch for {key}")
    analysis = analysis_row.get("analysis")
    if not isinstance(analysis, dict):
        raise ValueError(f"P1 analysis row {join_key} has no analysis object")
    order = join_key[2]
    expected_indices = list(range(10)) if order == "LSB_FIRST" else list(range(9, -1, -1))
    planes_by_index = {
        int(plane["alice_bit_index_from_lsb"]): plane for plane in analysis["planes"]
    }
    if len(planes_by_index) != 10 or set(planes_by_index) != set(range(10)):
        raise ValueError(f"P1 analysis row {join_key} must have ten unique bit planes")
    if analysis.get("order_name") != order or analysis.get("bit_order_from_lsb") != expected_indices:
        raise ValueError(f"P1 analysis row {join_key} has inconsistent declared bit order")
    planes = [planes_by_index[index] for index in expected_indices]
    entropies = tuple(float(p["H_bit_given_B_prefix_bits_per_symbol"]) for p in planes)
    variances = tuple(
        float(p["V_bit_given_B_prefix_bits_squared_per_symbol"]) for p in planes
    )
    H_A = float(analysis["H_A_bits_per_symbol"])
    H_A_given_B = float(analysis["H_A_given_B_bits_per_symbol"])
    if not math.isfinite(H_A) or not math.isfinite(H_A_given_B):
        raise ValueError(f"P1 analysis row {join_key} has non-finite entropy fields")

    budget_bits = _verify_projection(saved, N, key)
    p_fail = float(saved["joint_failure_assumption"])
    epsilon_each = float(saved["per_plane_failure_probability"])
    if epsilon_each != p_fail / len(planes):
        raise ValueError(f"P1 scenario {key} has an inconsistent uniform per-plane epsilon")

    uniform_epsilons = (epsilon_each,) * len(planes)
    uniform_budgets = normal_stage_budgets(entropies, variances, N, uniform_epsilons)
    uniform_L = sum(uniform_budgets.clipped_bits_per_stage)
    uniform_ledger = _ledger(
        N, H_A, H_A_given_B, uniform_L, TAG_BITS, p_fail, budget_bits
    )
    _verify_uniform_ledger(saved, uniform_ledger, key)

    allocation = allocate_normal_error_budget(variances, EPSILON_TOTAL)
    allocated_budgets = normal_stage_budgets(
        entropies, variances, N, allocation.epsilons
    )
    allocated_L = sum(allocated_budgets.clipped_bits_per_stage)
    allocated_ledger = _ledger(
        N, H_A, H_A_given_B, allocated_L, TAG_BITS, p_fail, budget_bits
    )
    uniform_continuous = math.fsum(uniform_budgets.continuous_bits_per_stage)
    allocated_continuous = math.fsum(allocated_budgets.continuous_bits_per_stage)
    if not math.isclose(
        sum(allocation.epsilons), EPSILON_TOTAL, rel_tol=0.0, abs_tol=1e-14
    ):
        raise ArithmeticError(f"optimized allocation for {key} misses total epsilon")

    return {
        "record_kind": "NORMAL_APPROX_ALLOCATION_DIAGNOSTIC",
        "source": saved["source"],
        "source_role": saved["source_role"],
        "input_path_provenance_only": saved["input_path"],
        "primary_json_path_provenance": saved["primary_json_path"],
        "N_train": int(saved["N_train"]),
        "encoding": saved["encoding"],
        "order": saved["order"],
        "N_symbols": N,
        "P1_acceptance_scope": (
            "P1 arithmetic accepted within RESULT.md source/scenario scope; "
            "the numeric index itself is marked DRAFT"
        ),
        "allocation_method": "continuous KKT upper-tail normal approximation",
        "joint_failure_assumption": EPSILON_TOTAL,
        "zero_variance_treatment": (
            "zero epsilon if positive variances exist; all-zero variance uses "
            "uniform epsilon by convention; zero variance does not imply zero disclosure"
        ),
        "stage_units": {
            "H": "bits/symbol",
            "V": "bits^2/symbol",
            "continuous_and_integer_cost": "bits/stage per block",
            "epsilon": "dimensionless one-sided normal-tail allocation",
            "tag": "bits/block, charged once",
            "failure_penalty": "expected bits/block under the saved 0.01 assumption",
            "f": "dimensionless",
        },
        "allocation": {
            "epsilons_by_stage": list(allocation.epsilons),
            "z_by_stage": list(allocation.z_values),
            "continuous_objective_bits_per_sqrt_symbol": (
                allocation.continuous_objective_bits_per_sqrt_symbol
            ),
            "epsilon_sum": sum(allocation.epsilons),
        },
        "uniform_baseline": {
            "per_stage_epsilon": epsilon_each,
            "stages": _stage_rows(planes, uniform_budgets, uniform_epsilons),
            "continuous_L_EC_bits": uniform_continuous,
            "raw_ceil_sum_bits": sum(uniform_budgets.raw_ceil_bits_per_stage),
            "L_EC_bits": uniform_L,
            "ledger": uniform_ledger,
        },
        "variance_allocated": {
            "stages": _stage_rows(planes, allocated_budgets, allocation.epsilons),
            "continuous_L_EC_bits": allocated_continuous,
            "raw_ceil_sum_bits": sum(allocated_budgets.raw_ceil_bits_per_stage),
            "L_EC_bits": allocated_L,
            "ledger": allocated_ledger,
        },
        "comparison": {
            "uniform_minus_allocated_continuous_L_EC_bits": (
                uniform_continuous - allocated_continuous
            ),
            "uniform_minus_allocated_clipped_L_EC_bits": uniform_L - allocated_L,
            "uniform_minus_allocated_expected_f": (
                uniform_ledger["f_expected_dimensionless"]
                - allocated_ledger["f_expected_dimensionless"]
                if uniform_ledger["f_expected_dimensionless"] is not None
                and allocated_ledger["f_expected_dimensionless"] is not None
                else None
            ),
            "negative_rounded_improvement_is_retained": allocated_L > uniform_L,
        },
        "budget_projection": {
            "formula": PROJECTION_FORMULA,
            "bits": budget_bits,
            "status": PROJECTION_STATUS,
            "scope": "planning projection only; not an observed long-block baseline",
        },
        "practical_code_gap": "UNKNOWN",
        "claim_ceiling": (
            "saved TRAIN scalar summaries under the stated normal approximation; "
            "not empirical FER, measured f gain, achievable-code rate, OOS guarantee, "
            "route closure, qualification, or decoder authorization"
        ),
    }


def _fresh_output_root(repo_root: Path, output_root: str) -> Path:
    candidate = Path(output_root)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    candidate = candidate.resolve()
    expected_parent = (repo_root / "workspace" / "msd_error_allocation").resolve()
    if candidate.parent != expected_parent:
        raise ValueError("output root must be workspace/msd_error_allocation/<uuid>")
    try:
        uuid.UUID(candidate.name)
    except ValueError as exc:
        raise ValueError("output root leaf must be a UUID") from exc
    if candidate.exists():
        raise FileExistsError(f"output root already exists: {candidate}")
    candidate.mkdir(parents=True)
    return candidate


def _write_json(path: Path, record: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _summary_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Normal-approximation allocation diagnostic",
        "",
        "These rows use only the accepted P1 scalar summary and its TRAIN scope.",
        "They are not empirical FER, achieved code rates, OOS guarantees, or a decoder result.",
        "The 1040*N/1024 + 64-bit value is a planning projection, not an observed long-block baseline.",
        "Negative rounded improvement is retained when clipped integer leakage rises.",
        "",
        "| Source | Encoding | Order | N (symbols) | Uniform L (bits) | Allocated continuous L (bits) | Allocated clipped L (bits) | Uniform minus allocated clipped (bits) | Uniform minus allocated f |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        baseline = row["uniform_baseline"]
        allocated = row["variance_allocated"]
        compare = row["comparison"]
        values = (
            row["source"],
            row["encoding"],
            row["order"],
            str(row["N_symbols"]),
            str(baseline["L_EC_bits"]),
            f"{allocated['continuous_L_EC_bits']:.9f}",
            str(allocated["L_EC_bits"]),
            str(compare["uniform_minus_allocated_clipped_L_EC_bits"]),
            (
                "null"
                if compare["uniform_minus_allocated_expected_f"] is None
                else f"{compare['uniform_minus_allocated_expected_f']:.12g}"
            ),
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            "All failure penalties, tags, expected yields, f values, and budget slacks are present in the per-scenario JSON files.",
            "Same-source practical code gap remains UNKNOWN; no experiment or route decision follows from this diagnostic.",
            "",
        ]
    )
    return "\n".join(lines)


def run(output_root: str, smoke: bool = False) -> Path:
    analysis_by_key, scenario_by_key = _load_saved_summary(REPO_ROOT)
    out = _fresh_output_root(REPO_ROOT, output_root)

    keys = [
        (*join_key, N)
        for join_key in _expected_join_keys()
        for N in EXPECTED_LENGTHS
    ]
    if smoke:
        keys = [("T2-2M", "NATURAL", "LSB_FIRST", 16384)]

    compact_rows = []
    result_rows = []
    for index, key in enumerate(keys, start=1):
        result = _process_scenario(
            analysis_by_key[key[:3]], scenario_by_key[key], key
        )
        filename = (
            f"scenario_{index:02d}_{key[0]}_{key[1]}_{key[2]}_N{key[3]}.json"
        )
        _write_json(out / filename, result)
        result_rows.append(result)
        compact_rows.append(
            {
                "file": filename,
                "source": result["source"],
                "source_role": result["source_role"],
                "encoding": result["encoding"],
                "order": result["order"],
                "N_symbols": result["N_symbols"],
                "uniform_L_EC_bits": result["uniform_baseline"]["L_EC_bits"],
                "allocated_continuous_L_EC_bits": result["variance_allocated"][
                    "continuous_L_EC_bits"
                ],
                "allocated_clipped_L_EC_bits": result["variance_allocated"][
                    "L_EC_bits"
                ],
                "uniform_minus_allocated_clipped_L_EC_bits": result["comparison"][
                    "uniform_minus_allocated_clipped_L_EC_bits"
                ],
                "practical_code_gap": "UNKNOWN",
            }
        )

    summary = {
        "record_kind": "NORMAL_APPROX_ALLOCATION_DIAGNOSTIC_SUMMARY",
        "input": str(P1_NUMBERS_RELATIVE).replace("\\", "/"),
        "input_read_scope": "P1_NUMBERS.json only; input_path values are provenance, not opened",
        "P1_acceptance_scope": (
            "arithmetic accepted within RESULT.md source/scenario scope; "
            "the numeric index itself is marked DRAFT"
        ),
        "rows_written": len(compact_rows),
        "mode": "single frozen timing smoke" if smoke else "full 24-scenario matrix",
        "rows": compact_rows,
        "claim_ceiling": (
            "normal approximation over saved TRAIN scalars only; not empirical FER, "
            "measured f gain, achievable-code rate, OOS guarantee, route closure, "
            "qualification, or decoder authorization"
        ),
        "practical_code_gap": "UNKNOWN",
    }
    _write_json(out / "summary.json", summary)
    (out / "summary.md").write_text(_summary_markdown(result_rows), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "mode": summary["mode"],
                "rows_written": len(compact_rows),
                "output_root": out.relative_to(REPO_ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run(args.output_root, smoke=args.smoke)


if __name__ == "__main__":
    main()
