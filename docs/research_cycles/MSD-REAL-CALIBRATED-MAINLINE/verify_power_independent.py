"""Independently recalculate P2 power-planning arithmetic from P1_NUMBERS."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
ROUTE = ROOT / "docs" / "research_cycles" / "MSD-REAL-CALIBRATED-MAINLINE"
P1_PATH = ROUTE / "P1_NUMBERS.json"
P2_PATH = ROUTE / "P2_POWER.json"
OUTPUT_PATH = ROUTE / "P2_POWER_INDEPENDENT.json"
SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
ENCODINGS = ("NATURAL", "GRAY")
ORDERS = ("MSB_FIRST", "LSB_FIRST")
BLOCK_LENGTHS = (1024, 16384)
SEED_COUNT = 3
DELTA_F = 0.10
ALPHA = 0.05
POWER = 0.80
FLOAT_TOL = 1e-9


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _index_p1(report: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    rows = report["analysis_rows"]
    expected = {
        (source, encoding, order)
        for source in SOURCES
        for encoding in ENCODINGS
        for order in ORDERS
    }
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["source"], row["encoding"], row["order"])
        if key in indexed:
            raise ValueError(f"duplicate P1 analysis row: {key}")
        if row["source_role"] != "TRAIN":
            raise ValueError(f"P1 row is not labeled TRAIN: {key}")
        indexed[key] = row
    if len(rows) != 12 or set(indexed) != expected:
        raise ValueError("P1_NUMBERS must contain the frozen 12 TRAIN source/encoding/order rows")
    return indexed


def _float(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite P1 input {label}")
    return result


def _ceil_to_seed_multiple(value: int) -> int:
    return value + (-value % SEED_COUNT)


def _bsc_context(
    indexed: dict[tuple[str, str, str], dict[str, Any]], source: str, h_ab: float
) -> dict[str, Any]:
    rows = []
    for encoding in ENCODINGS:
        for order in ORDERS:
            row = indexed[(source, encoding, order)]
            analysis = row["analysis"]
            marginal_sum = _float(
                analysis["sum_h2_marginal_bit_error_bits_per_symbol"],
                f"{source}/{encoding}/{order}/sum_h2",
            )
            conditional = _float(
                analysis["H_A_given_B_bits_per_symbol"],
                f"{source}/{encoding}/{order}/H_AB",
            )
            rows.append(
                {
                    "encoding": encoding,
                    "order": order,
                    "sum_h2_minus_H_A_given_B_bits_per_symbol": marginal_sum - conditional,
                }
            )
    excesses = [row["sum_h2_minus_H_A_given_B_bits_per_symbol"] for row in rows]
    return {
        "meaning": "sum marginal h2(bit-error) minus H(A|B), bits/symbol",
        "not_a_measured_f_gain": True,
        "by_encoding_order": rows,
        "min_bits_per_symbol": min(excesses),
        "max_bits_per_symbol": max(excesses),
        "reference_H_A_given_B_bits_per_symbol": h_ab,
    }


def _workload(n_pairs: int) -> list[dict[str, int]]:
    return [
        {
            "block_length_symbols_per_arm": length,
            "paired_symbol_positions": n_pairs * length,
            "symbol_positions_per_arm": n_pairs * length,
            "two_arm_symbol_positions": 2 * n_pairs * length,
            "paired_block_pairs": n_pairs,
        }
        for length in BLOCK_LENGTHS
    ]


def _calculate_source(
    indexed: dict[tuple[str, str, str], dict[str, Any]], source: str
) -> dict[str, Any]:
    source_rows = [indexed[(source, enc, order)] for enc in ENCODINGS for order in ORDERS]
    reference = indexed[(source, "GRAY", "LSB_FIRST")]
    h_a = _float(reference["analysis"]["H_A_bits_per_symbol"], f"{source}/H_A")
    h_ab = _float(reference["analysis"]["H_A_given_B_bits_per_symbol"], f"{source}/H_AB")
    if h_ab <= 0.0:
        raise ValueError(f"{source}: H(A|B) must be positive for the frozen f-difference bound")
    for row in source_rows:
        analysis = row["analysis"]
        for key, expected in (
            ("H_A_bits_per_symbol", h_a),
            ("H_A_given_B_bits_per_symbol", h_ab),
        ):
            actual = _float(analysis[key], f"{source}/{row['encoding']}/{row['order']}/{key}")
            if abs(actual - expected) > FLOAT_TOL:
                raise ValueError(f"{source}: P1 {key} differs across encoding/order rows")

    ratio_bound = h_a / h_ab
    normal_z_critical = NormalDist().inv_cdf(1.0 - ALPHA / 2.0)
    normal_z_power = NormalDist().inv_cdf(POWER)
    normal_z_sum = normal_z_critical + normal_z_power
    normal_unrounded_n = math.ceil((normal_z_sum * ratio_bound / DELTA_F) ** 2)

    hoeffding_log_sum = math.sqrt(math.log(2.0 / ALPHA)) + math.sqrt(
        math.log(1.0 / (1.0 - POWER))
    )
    hoeffding_tail_coefficient = math.sqrt(2.0) * hoeffding_log_sum
    hoeffding_unrounded_n = math.ceil(
        (hoeffding_tail_coefficient * ratio_bound / DELTA_F) ** 2
    )

    method_specs = (
        {
            "method": "normal_approximation",
            "status": "NORMAL_POWER_PLANNING",
            "interpretation": "normal planning using sigma_upper=R; not an observed-variance estimate",
            "n_required_independent_paired_block_pairs": normal_unrounded_n,
            "mde_at_n": lambda n: normal_z_sum * ratio_bound / math.sqrt(n),
        },
        {
            "method": "hoeffding_distribution_free_bound",
            "status": "BOUNDED_POWER_PLANNING",
            "interpretation": (
                "distribution-free sufficient bound; more conservative here than normal planning; "
                "not based on observed variance"
            ),
            "n_required_independent_paired_block_pairs": hoeffding_unrounded_n,
            "mde_at_n": lambda n: ratio_bound * math.sqrt(2.0 / n) * hoeffding_log_sum,
        },
    )
    methods = []
    for spec in method_specs:
        required = spec["n_required_independent_paired_block_pairs"]
        balanced = _ceil_to_seed_multiple(required)
        mde_at_n = spec["mde_at_n"]
        methods.append(
            {
                "method": spec["method"],
                "status": spec["status"],
                "interpretation": spec["interpretation"],
                "n_required_independent_paired_block_pairs": required,
                "n_pairs_rounded_for_equal_seeds": balanced,
                "pairs_per_seed": balanced // SEED_COUNT,
                "seed_count": SEED_COUNT,
                "seed_count_is_not_the_effective_sample_count": True,
                "mde_at_unrounded_n_required_delta_f": mde_at_n(required),
                "mde_at_rounded_paired_count_delta_f": mde_at_n(balanced),
                "workload_by_block_length": _workload(balanced),
            }
        )

    bsc = _bsc_context(indexed, source, h_ab)
    source_metadata = next(
        item for item in _load_json(P1_PATH)["source_metadata"] if item["source"] == source
    )
    return {
        "source": source,
        "P1_scope": "R1 accepted aggregate TRAIN histogram; descriptive plug-in entropies",
        "P1_source_metadata": source_metadata,
        "H_A_bits_per_symbol": h_a,
        "H_A_given_B_bits_per_symbol": h_ab,
        "R_dimensionless": ratio_bound,
        "paired_f_difference_bound": [-ratio_bound, ratio_bound],
        "sigma_upper_f_units": ratio_bound,
        "target_delta_f": DELTA_F,
        "bsc_proxy_overcount_context_only": bsc,
        "normal_constants": {
            "alpha_two_sided": ALPHA,
            "power": POWER,
            "z_1_minus_alpha_over_2": normal_z_critical,
            "z_power": normal_z_power,
            "z_sum": normal_z_sum,
            "mde_formula": "(z_1-alpha/2 + z_power) * R / sqrt(n)",
            "n_required_formula": "ceil(((z_1-alpha/2 + z_power)*R/delta_f)^2)",
        },
        "hoeffding_constants": {
            "alpha": ALPHA,
            "power": POWER,
            "sum_sqrt_logs": hoeffding_log_sum,
            "tailbound_coefficient_sqrt2_times_sum_sqrt_logs": hoeffding_tail_coefficient,
            "mde_bound_formula": (
                "R*sqrt(2/n)*(sqrt(log(2/alpha))+sqrt(log(1/(1-power))))"
            ),
            "n_required_formula": "ceil((sqrt(2)*sum_sqrt_logs*R/delta_f)^2)",
        },
        "method_plans": methods,
    }


def _numeric_leaves(value: Any, path: str = "") -> dict[str, int | float]:
    found: dict[str, int | float] = {}
    if isinstance(value, bool):
        return found
    if isinstance(value, (int, float)):
        found[path] = value
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            found.update(_numeric_leaves(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            found.update(_numeric_leaves(child, child_path))
    return found


def _compare_tree(
    expected: Any,
    actual: Any,
    path: str,
    numeric_checks: list[dict[str, Any]],
    label_checks: list[dict[str, Any]],
    structural_mismatches: list[str],
) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            structural_mismatches.append(f"{path}: expected object")
            return
        for key, value in expected.items():
            child_path = f"{path}.{key}" if path else key
            if key not in actual:
                structural_mismatches.append(f"{child_path}: missing in P2_POWER")
            else:
                _compare_tree(
                    value,
                    actual[key],
                    child_path,
                    numeric_checks,
                    label_checks,
                    structural_mismatches,
                )
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            structural_mismatches.append(f"{path}: list length/type mismatch")
            return
        for index, (left, right) in enumerate(zip(expected, actual)):
            _compare_tree(
                left,
                right,
                f"{path}[{index}]",
                numeric_checks,
                label_checks,
                structural_mismatches,
            )
        return
    if isinstance(expected, bool):
        passed = isinstance(actual, bool) and actual is expected
        label_checks.append({"path": path, "expected": expected, "reported": actual, "match": passed})
        return
    if isinstance(expected, int):
        passed = isinstance(actual, int) and not isinstance(actual, bool) and actual == expected
        numeric_checks.append(
            {"path": path, "expected_independent": expected, "reported": actual, "absolute_difference": 0 if passed else None, "match": passed, "comparison": "exact_integer"}
        )
        return
    if isinstance(expected, float):
        is_numeric = isinstance(actual, (int, float)) and not isinstance(actual, bool)
        difference = abs(float(actual) - expected) if is_numeric else None
        passed = is_numeric and math.isfinite(float(actual)) and difference <= FLOAT_TOL
        numeric_checks.append(
            {"path": path, "expected_independent": expected, "reported": actual, "absolute_difference": difference, "match": bool(passed), "comparison": f"absolute_tolerance_{FLOAT_TOL:g}"}
        )
        return
    passed = actual == expected
    label_checks.append({"path": path, "expected": expected, "reported": actual, "match": passed})


def _check_top_labels(p2: dict[str, Any], source_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = []
    expected = {
        "status": "POWER_PLANNING",
        "claim_ceiling": (
            "pre-packet power arithmetic only; not a decoder experiment, observed power, "
            "or real-efficiency gain"
        ),
    }
    for key, value in expected.items():
        checks.append({"path": key, "expected": value, "reported": p2.get(key), "match": p2.get(key) == value})
    for item in source_results:
        idx = next(index for index, row in enumerate(p2["source_results"]) if row.get("source") == item["source"])
        source_row = p2["source_results"][idx]
        checks.append(
            {
                "path": f"source_results[{idx}].bsc_proxy_overcount_context_only.not_a_measured_f_gain",
                "expected": True,
                "reported": source_row.get("bsc_proxy_overcount_context_only", {}).get("not_a_measured_f_gain"),
                "match": source_row.get("bsc_proxy_overcount_context_only", {}).get("not_a_measured_f_gain") is True,
            }
        )
        for method in item["method_plans"]:
            p2_method = next(
                (candidate for candidate in source_row.get("method_plans", []) if candidate.get("method") == method["method"]),
                {},
            )
            checks.append(
                {
                    "path": f"source_results[{idx}].method_plans.{method['method']}.status",
                    "expected": method["status"],
                    "reported": p2_method.get("status"),
                    "match": p2_method.get("status") == method["status"],
                }
            )
    return checks


def main() -> int:
    p1 = _load_json(P1_PATH)
    p2 = _load_json(P2_PATH)
    p1_index = _index_p1(p1)
    independent_sources = [_calculate_source(p1_index, source) for source in SOURCES]

    expected_science = {"source_results": []}
    expected_science["source_results"] = [
        {
            key: value
            for key, value in result.items()
            if key not in {"P1_source_metadata", "hoeffding_constants"}
        }
        | {
            "bsc_proxy_overcount_context_only": {
                key: value
                for key, value in result["bsc_proxy_overcount_context_only"].items()
                if key != "reference_H_A_given_B_bits_per_symbol"
            }
        }
        | {
            "hoeffding_constants": {
                key: value
                for key, value in result["hoeffding_constants"].items()
                if key != "tailbound_coefficient_sqrt2_times_sum_sqrt_logs"
            }
        }
        for result in independent_sources
    ]
    numeric_checks: list[dict[str, Any]] = []
    label_checks: list[dict[str, Any]] = []
    structural_mismatches: list[str] = []
    _compare_tree(
        expected_science,
        {"source_results": p2.get("source_results")},
        "",
        numeric_checks,
        label_checks,
        structural_mismatches,
    )
    top_label_checks = _check_top_labels(p2, independent_sources)

    actual_source_numbers = _numeric_leaves(p2.get("source_results", []), "source_results")
    expected_source_numbers = _numeric_leaves(expected_science["source_results"], "source_results")
    numeric_path_mismatches = {
        "missing_from_independent_recalculation": sorted(set(actual_source_numbers) - set(expected_source_numbers)),
        "not_present_in_P2_POWER": sorted(set(expected_source_numbers) - set(actual_source_numbers)),
    }
    provenance = p2.get("p1_a5_acceptance_evidence", {})
    provenance_record = {
        "records_compared": provenance.get("records_compared"),
        "scientific_scalar_fields_compared": provenance.get("scientific_scalar_fields_compared"),
        "float_absolute_tolerance": provenance.get("float_absolute_tolerance"),
        "integer_comparison": provenance.get("integer_comparison"),
        "use_as_power_gate": False,
    }
    all_numeric_match = (
        all(item["match"] for item in numeric_checks)
        and not structural_mismatches
        and not numeric_path_mismatches["missing_from_independent_recalculation"]
        and not numeric_path_mismatches["not_present_in_P2_POWER"]
    )
    all_labels_match = all(item["match"] for item in label_checks + top_label_checks)

    output = {
        "record_kind": "INDEPENDENT_POWER_ARITHMETIC_COMPARISON",
        "inputs": {
            "P1_NUMBERS": P1_PATH.relative_to(ROOT).as_posix(),
            "P2_POWER": P2_PATH.relative_to(ROOT).as_posix(),
            "power_script_read_for_frozen_contract_only": (
                ROUTE / "power_before_decoder.py"
            ).relative_to(ROOT).as_posix(),
            "raw_counts_read": False,
            "decoder_or_DE_called": False,
        },
        "independent_method": {
            "formula_note": (
                "Recomputed from H_A and H(A|B) in P1_NUMBERS using scalar formulas "
                "and statistics.NormalDist; did not import or call power_before_decoder.py."
            ),
            "target_delta_f": DELTA_F,
            "alpha_two_sided": ALPHA,
            "power": POWER,
            "seed_count": SEED_COUNT,
            "block_lengths_symbols_per_arm": list(BLOCK_LENGTHS),
            "normal_quantile_sum_definition": "z_(1-alpha/2) + z_power",
            "normal_n_definition": "ceil((z_sum * (H_A/H(A|B)) / delta_f)^2)",
            "hoeffding_log_sum_definition": "sqrt(log(2/alpha)) + sqrt(log(1/(1-power)))",
            "hoeffding_tailbound_coefficient_definition": "sqrt(2) * hoeffding_log_sum",
            "hoeffding_n_definition": "ceil((tailbound_coefficient * (H_A/H(A|B)) / delta_f)^2)",
        },
        "comparison": {
            "float_absolute_tolerance": FLOAT_TOL,
            "integer_comparison": "exact",
            "scientific_numeric_field_count": len(numeric_checks),
            "scientific_numeric_fields_matching": sum(bool(item["match"]) for item in numeric_checks),
            "all_scientific_numbers_match": all_numeric_match,
            "all_status_and_label_checks_match": all_labels_match,
            "numeric_path_set_matches": not any(numeric_path_mismatches.values()),
            "P1_only_context_excluded_from_P2_comparison": (
                "bsc_proxy_overcount_context_only.reference_H_A_given_B_bits_per_symbol"
            ),
            "structural_mismatches": structural_mismatches,
            "numeric_path_mismatches": numeric_path_mismatches,
            "numeric_mismatches": [item for item in numeric_checks if not item["match"]],
            "status_or_label_mismatches": [
                item for item in label_checks + top_label_checks if not item["match"]
            ],
            "source_acceptance_metadata_provenance_only": provenance_record,
            "p2_numeric_source_result_leaf_count": len(actual_source_numbers),
        },
        "source_results": [
            {
                "source": result["source"],
                "P1_source_metadata": result["P1_source_metadata"],
                "independent_calculation": result,
                "P2_numeric_comparisons": [
                    item for item in numeric_checks if item["path"].startswith(f"source_results[{index}].")
                ],
                "P2_label_checks": [
                    item for item in top_label_checks if f"source_results[{index}]" in item["path"]
                ],
            }
            for index, result in enumerate(independent_sources)
        ],
        "verification_ceiling": (
            "Arithmetic cross-check only. No decoder experiment, observed power, "
            "real-efficiency gain, route acceptance, or authorization is produced."
        ),
    }
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT).as_posix()}")
    print(
        "science_numeric_fields="
        f"{output['comparison']['scientific_numeric_field_count']} "
        f"matching={output['comparison']['scientific_numeric_fields_matching']} "
        f"labels_match={all_labels_match}"
    )
    return 0 if all_numeric_match and all_labels_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
