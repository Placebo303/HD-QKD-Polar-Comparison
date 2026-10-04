"""Calculate bounded paired-f MDE planning from the accepted P1 result."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
P1_RESULT = Path(
    "workspace/msd_p1/a24c800020d943e48d590f803157a775/independent.json"
)
OUTPUT = Path(__file__).with_name("P2_POWER.json")
SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
ENCODING_ORDER_ROWS = 4
TARGET_DELTA_F = 0.10
ALPHA = 0.05
POWER = 0.80
BLOCK_LENGTHS = (1024, 16384)
SEED_COUNT = 3
FLOAT_TOL = 1e-9


def _ceil_multiple(value: int, multiple: int) -> int:
    return ((value + multiple - 1) // multiple) * multiple


def _load_p1(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        report = json.load(stream)
    if report.get("comparison", {}).get("records_compared") != 12:
        raise ValueError(f"{path}: expected the independently checked 12-record P1 output")
    rows = report.get("results", [])
    expected = {
        (source, encoding, order)
        for source in SOURCES
        for encoding in ("NATURAL", "GRAY")
        for order in ("MSB_FIRST", "LSB_FIRST")
    }
    observed = {
        (row.get("source"), row.get("encoding"), row.get("order"))
        for row in rows
        if isinstance(row, dict)
    }
    if len(rows) != 12 or len(observed) != 12 or observed != expected:
        raise ValueError(f"{path}: expected 12 P1 result rows")
    return report


def _source_metrics(rows: list[dict[str, Any]], source: str) -> dict[str, Any]:
    selected = [row for row in rows if row.get("source") == source]
    if len(selected) != ENCODING_ORDER_ROWS:
        raise ValueError(f"{source}: expected four P1 encoding/order rows, got {len(selected)}")

    first = selected[0]["analysis"]
    h_a = float(first["H_A_bits_per_symbol"])
    h_a_given_b = float(first["H_A_given_B_bits_per_symbol"])
    if not math.isfinite(h_a) or not math.isfinite(h_a_given_b) or h_a_given_b <= 0.0:
        raise ValueError(f"{source}: invalid P1 entropy inputs")
    for row in selected[1:]:
        analysis = row["analysis"]
        for name, expected in (
            ("H_A_bits_per_symbol", h_a),
            ("H_A_given_B_bits_per_symbol", h_a_given_b),
        ):
            value = float(analysis[name])
            if not math.isfinite(value) or abs(value - expected) > FLOAT_TOL:
                raise ValueError(f"{source}: P1 {name} varies across encoding/order rows")

    r_bound = h_a / h_a_given_b
    z_alpha = NormalDist().inv_cdf(1.0 - ALPHA / 2.0)
    z_power = NormalDist().inv_cdf(POWER)
    z_sum = z_alpha + z_power
    n_normal = math.ceil((z_sum * r_bound / TARGET_DELTA_F) ** 2)

    hoeffding_sum = math.sqrt(math.log(2.0 / ALPHA)) + math.sqrt(
        math.log(1.0 / (1.0 - POWER))
    )
    hoeffding_coefficient = math.sqrt(2.0) * hoeffding_sum
    n_hoeffding = math.ceil(
        (hoeffding_coefficient * r_bound / TARGET_DELTA_F) ** 2
    )

    bsc_excess_rows = []
    for row in selected:
        analysis = row["analysis"]
        excess = (
            float(analysis["sum_h2_marginal_bit_error_bits_per_symbol"])
            - float(analysis["H_A_given_B_bits_per_symbol"])
        )
        bsc_excess_rows.append(
            {
                "encoding": row["encoding"],
                "order": row["order"],
                "sum_h2_minus_H_A_given_B_bits_per_symbol": excess,
            }
        )

    method_plans = []
    for method, status, interpretation, n_required, mde_at_n in (
        (
            "normal_approximation",
            "NORMAL_POWER_PLANNING",
            "normal planning using sigma_upper=R; not an observed-variance estimate",
            n_normal,
            lambda n: z_sum * r_bound / math.sqrt(n),
        ),
        (
            "hoeffding_distribution_free_bound",
            "BOUNDED_POWER_PLANNING",
            "distribution-free sufficient bound; more conservative here than normal planning; not based on observed variance",
            n_hoeffding,
            lambda n: r_bound * math.sqrt(2.0 / n) * hoeffding_sum,
        ),
    ):
        n_balanced = _ceil_multiple(n_required, SEED_COUNT)
        method_plans.append(
            {
                "method": method,
                "status": status,
                "interpretation": interpretation,
                "n_required_independent_paired_block_pairs": n_required,
                "n_pairs_rounded_for_equal_seeds": n_balanced,
                "pairs_per_seed": n_balanced // SEED_COUNT,
                "seed_count": SEED_COUNT,
                "seed_count_is_not_the_effective_sample_count": True,
                "mde_at_unrounded_n_required_delta_f": mde_at_n(n_required),
                "mde_at_rounded_paired_count_delta_f": mde_at_n(n_balanced),
                "workload_by_block_length": [
                    {
                        "block_length_symbols_per_arm": block_length,
                        "paired_symbol_positions": n_balanced * block_length,
                        "symbol_positions_per_arm": n_balanced * block_length,
                        "two_arm_symbol_positions": 2 * n_balanced * block_length,
                        "paired_block_pairs": n_balanced,
                    }
                    for block_length in BLOCK_LENGTHS
                ],
            }
        )

    return {
        "source": source,
        "P1_scope": "R1 accepted aggregate TRAIN histogram; descriptive plug-in entropies",
        "H_A_bits_per_symbol": h_a,
        "H_A_given_B_bits_per_symbol": h_a_given_b,
        "R_dimensionless": r_bound,
        "paired_f_difference_bound": [-r_bound, r_bound],
        "sigma_upper_f_units": r_bound,
        "target_delta_f": TARGET_DELTA_F,
        "bsc_proxy_overcount_context_only": {
            "meaning": "sum marginal h2(bit-error) minus H(A|B), bits/symbol",
            "not_a_measured_f_gain": True,
            "by_encoding_order": bsc_excess_rows,
            "min_bits_per_symbol": min(
                item["sum_h2_minus_H_A_given_B_bits_per_symbol"]
                for item in bsc_excess_rows
            ),
            "max_bits_per_symbol": max(
                item["sum_h2_minus_H_A_given_B_bits_per_symbol"]
                for item in bsc_excess_rows
            ),
        },
        "normal_constants": {
            "alpha_two_sided": ALPHA,
            "power": POWER,
            "z_1_minus_alpha_over_2": z_alpha,
            "z_power": z_power,
            "z_sum": z_sum,
            "mde_formula": "(z_1-alpha/2 + z_power) * R / sqrt(n)",
            "n_required_formula": "ceil(((z_1-alpha/2 + z_power)*R/delta_f)^2)",
        },
        "hoeffding_constants": {
            "alpha": ALPHA,
            "power": POWER,
            "sum_sqrt_logs": hoeffding_sum,
            "mde_bound_formula": (
                "R*sqrt(2/n)*(sqrt(log(2/alpha))+sqrt(log(1/(1-power))))"
            ),
            "n_required_formula": "ceil((sqrt(2)*sum_sqrt_logs*R/delta_f)^2)",
        },
        "method_plans": method_plans,
    }


def build_report() -> dict[str, Any]:
    p1_path = ROOT / P1_RESULT
    p1 = _load_p1(p1_path)
    source_rows = [
        _source_metrics(p1["results"], source)
        for source in SOURCES
    ]
    return {
        "status": "POWER_PLANNING",
        "calculation_note": "metadata and source-row guard correction only; formulas, inputs, and scientific numbers unchanged",
        "claim_ceiling": (
            "pre-packet power arithmetic only; not a decoder experiment, observed power, "
            "or real-efficiency gain"
        ),
        "p1_independent_input": P1_RESULT.as_posix(),
        "p1_a5_acceptance_evidence": {
            "records_compared": p1["comparison"]["records_compared"],
            "scientific_scalar_fields_compared": p1["comparison"]["scientific_scalar_fields_compared"],
            "float_absolute_tolerance": p1["comparison"]["float_absolute_tolerance"],
            "integer_comparison": p1["comparison"]["integer_comparison"],
        },
        "paired_observation_unit": (
            "one matched block pair: control and candidate use the same source, block length, "
            "and one shared 64-bit tag"
        ),
        "sampling_assumption": (
            "independent paired block differences for the planning formula; actual failure "
            "and discordance variance is unknown and is not estimated here; P1 aggregate "
            "histograms do not provide an available independent paired-block count"
        ),
        "effect_size_status": (
            "delta_f=0.10 is a proposed minimum comparison effect, not a P1-measured gain; "
            "the P1 marginal-BSC proxy excess is context only"
        ),
        "failure_and_bound_note": (
            "Use the frozen paired-gap bound [-R,R] from L_EC in [0,N*H_A], nonnegative kept, "
            "and matched shared tag; sigma_upper=R. Recheck this bound if later arm-specific "
            "failure accounting changes the paired-f range."
        ),
        "source_results": source_rows,
    }


def main() -> int:
    report = build_report()
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
