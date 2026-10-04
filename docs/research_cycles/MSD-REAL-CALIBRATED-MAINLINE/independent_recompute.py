"""Independent A5 recomputation for the frozen R1 TRAIN histogram scope.

This module intentionally does not import the primary MSD implementation.  It
loads only the three named COO aggregate histograms when invoked, recomputes the
entropy, information-density, and expected-yield quantities, then compares the
scientific fields in the primary JSON files.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HISTOGRAM_ROOT = Path("workspace/r1_histogram_5e2a91c4")
SOURCES = ("T2-1M", "T2-1.5M", "T2-2M")
ENCODINGS = ("NATURAL", "GRAY")
ORDERS = ("MSB_FIRST", "LSB_FIRST")
BLOCK_LENGTHS = (1024, 16384)
FAILURE_ASSUMPTION = 0.01
TAG_BITS = 64.0
ABS_TOL = 1e-9
BIT_ORDER = {
    "MSB_FIRST": tuple(range(9, -1, -1)),
    "LSB_FIRST": tuple(range(10)),
}
def _entropy_counts(values: np.ndarray) -> float:
    flat = np.asarray(values, dtype=np.float64).ravel()
    total = float(np.sum(flat, dtype=np.float64))
    if total <= 0.0:
        return 0.0
    probabilities = flat[flat > 0.0] / total
    return float(-np.sum(probabilities * np.log2(probabilities), dtype=np.float64))


def _binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def _load_coo(path: Path) -> tuple[np.ndarray, int]:
    with np.load(path, allow_pickle=False) as bundle:
        required = {"row", "col", "count", "shape", "N_train"}
        missing = required.difference(bundle.files)
        if missing:
            raise ValueError(f"{path}: missing COO fields {sorted(missing)}")
        row = np.asarray(bundle["row"])
        col = np.asarray(bundle["col"])
        count = np.asarray(bundle["count"])
        shape = tuple(int(value) for value in np.asarray(bundle["shape"]).tolist())
        n_train_array = np.asarray(bundle["N_train"])
        if n_train_array.size != 1:
            raise ValueError(f"{path}: N_train must be a scalar")
        n_train = int(n_train_array.item())

    if shape != (1024, 1024):
        raise ValueError(f"{path}: expected shape (1024, 1024), got {shape}")
    if row.ndim != 1 or col.ndim != 1 or count.ndim != 1:
        raise ValueError(f"{path}: row, col and count must be one-dimensional")
    if not (row.size == col.size == count.size):
        raise ValueError(f"{path}: COO arrays have different lengths")
    if not np.issubdtype(row.dtype, np.integer) or not np.issubdtype(col.dtype, np.integer):
        raise ValueError(f"{path}: COO row and col must be integer arrays")
    if not np.issubdtype(count.dtype, np.integer):
        raise ValueError(f"{path}: COO count must be an integer array")
    if np.any(row < 0) or np.any(row >= 1024) or np.any(col < 0) or np.any(col >= 1024):
        raise ValueError(f"{path}: COO indices fall outside the 1024-symbol alphabet")
    if np.any(count < 0):
        raise ValueError(f"{path}: COO counts must be nonnegative")
    count_total = int(np.sum(count, dtype=np.int64))
    if count_total <= 0 or count_total != n_train:
        raise ValueError(f"{path}: sum(count)={count_total} does not equal N_train={n_train}")

    dense = np.zeros((1024, 1024), dtype=np.int64)
    np.add.at(dense, (row.astype(np.int64), col.astype(np.int64)), count.astype(np.int64))
    return dense, n_train


def _encoded_counts(counts: np.ndarray, encoding: str) -> np.ndarray:
    if encoding == "NATURAL":
        return counts
    symbols = np.arange(1024, dtype=np.int64)
    gray = symbols ^ (symbols >> 1)
    encoded = np.zeros_like(counts)
    encoded[np.ix_(gray, gray)] = counts
    return encoded


def _joint_entropy_and_variance(counts: np.ndarray) -> tuple[float, float, float, float]:
    total = float(np.sum(counts, dtype=np.float64))
    p_ab = counts.astype(np.float64) / total
    p_b = np.sum(p_ab, axis=0, dtype=np.float64)
    h_ab = _entropy_counts(counts)
    h_b = _entropy_counts(np.sum(counts, axis=0, dtype=np.int64))
    h_a_given_b = h_ab - h_b

    a_index, b_index = np.nonzero(counts)
    cell_mass = p_ab[a_index, b_index]
    conditional = cell_mass / p_b[b_index]
    information = -np.log2(conditional)
    mean = math.fsum(float(mass) * float(info) for mass, info in zip(cell_mass, information))
    variance = math.fsum(
        float(mass) * (float(info) - mean) ** 2
        for mass, info in zip(cell_mass, information)
    )
    return h_ab, h_b, h_a_given_b, variance


def _analyze(counts: np.ndarray, order: str) -> tuple[dict[str, Any], dict[str, float]]:
    total = float(np.sum(counts, dtype=np.float64))
    p_b_counts = np.sum(counts, axis=0, dtype=np.float64)
    p_b = p_b_counts / total
    h_a = _entropy_counts(np.sum(counts, axis=1, dtype=np.int64))
    h_ab, h_b, h_a_given_b, v_a_given_b = _joint_entropy_and_variance(counts)
    alphabet_size = int(counts.shape[0])
    symbols = np.arange(alphabet_size, dtype=np.int64)
    cell_a, cell_b = np.nonzero(counts)
    cell_counts = counts[cell_a, cell_b].astype(np.float64)
    cell_mass = cell_counts / total

    planes: list[dict[str, Any]] = []
    prior: list[int] = []
    sum_h2_error = 0.0
    sum_h_given_b = 0.0
    prefix_by_symbol = np.zeros(alphabet_size, dtype=np.int64)

    for bit_index in BIT_ORDER[order]:
        a_bits = ((symbols >> bit_index) & 1).astype(np.int64)
        b_bits = ((symbols >> bit_index) & 1).astype(np.int64)
        group_count = 1 << len(prior)
        if prior:
            prefix_by_symbol = np.zeros(alphabet_size, dtype=np.int64)
            for prefix_position, prefix_index in enumerate(prior):
                prefix_by_symbol |= ((symbols >> prefix_index) & 1) << prefix_position
        group_code = prefix_by_symbol[cell_a] * alphabet_size + cell_b
        group_bit_code = group_code * 2 + a_bits[cell_a]
        group_masses = np.bincount(
            group_code,
            weights=cell_counts,
            minlength=group_count * alphabet_size,
        )
        group_bit_masses = np.bincount(
            group_bit_code,
            weights=cell_counts,
            minlength=group_count * alphabet_size * 2,
        )
        h_prefix_b = _entropy_counts(group_masses)
        h_prefix_bit_b = _entropy_counts(group_bit_masses)
        h_k = h_prefix_bit_b - h_prefix_b

        local_probability = (
            group_bit_masses[group_bit_code] / group_masses[group_code]
        )
        info_k = -np.log2(local_probability)
        if np.all(local_probability == 1.0):
            if abs(h_k) >= 1e-10:
                raise ArithmeticError(
                    f"bit {bit_index}: deterministic conditional groups have entropy difference {h_k:.17g}"
                )
            h_k = 0.0
            v_k = 0.0
        else:
            v_k = math.fsum(
                float(mass) * (float(info) - h_k) ** 2
                for mass, info in zip(cell_mass, info_k)
            )

        h_bit_b = 0.0
        for bob_symbol, bob_mass in enumerate(p_b):
            if bob_mass == 0.0:
                continue
            bit_joint_mass = float(np.sum(counts[a_bits == 1, bob_symbol], dtype=np.float64))
            p_one = bit_joint_mass / total / float(bob_mass)
            h_bit_b += float(bob_mass) * _binary_entropy(p_one)

        error_mask = a_bits[:, None] != b_bits[None, :]
        error_probability = float(np.sum(counts[error_mask], dtype=np.float64) / total)
        h2_error = _binary_entropy(error_probability)
        sum_h2_error += h2_error
        sum_h_given_b += h_bit_b
        planes.append(
            {
                "alice_bit_index_from_lsb": int(bit_index),
                "H_bit_given_B_prefix_bits_per_symbol": float(h_k),
                "V_bit_given_B_prefix_bits_squared_per_symbol": float(v_k),
                "H_bit_given_B_bits_per_symbol": float(h_bit_b),
                "marginal_bit_error_probability": float(error_probability),
                "h2_marginal_bit_error_bits_per_symbol": float(h2_error),
            }
        )
        prior.append(bit_index)

    sum_chain = math.fsum(float(plane["H_bit_given_B_prefix_bits_per_symbol"]) for plane in planes)
    closure = sum_chain - h_a_given_b
    if abs(closure) > 1e-10:
        raise ArithmeticError(f"chain entropy closure error is {closure:.17g} bits/symbol")

    analysis = {
        "alphabet_size": alphabet_size,
        "n_planes": 10,
        "order_name": order,
        "bit_order_from_lsb": list(BIT_ORDER[order]),
        "H_A_bits_per_symbol": float(h_a),
        "H_A_given_B_bits_per_symbol": float(h_a_given_b),
        "V_A_given_B_bits_squared_per_symbol": float(v_a_given_b),
        "sum_chain_H_bit_given_B_prefix_bits_per_symbol": float(sum_chain),
        "sum_H_bit_given_B_bits_per_symbol": float(sum_h_given_b),
        "sum_h2_marginal_bit_error_bits_per_symbol": float(sum_h2_error),
        "chain_closure_error_bits_per_symbol": float(closure),
        "planes": planes,
    }
    audit = {
        "H_AB_bits_per_symbol_direct": float(h_ab),
        "H_B_bits_per_symbol_direct": float(h_b),
        "H_A_given_B_from_H_AB_minus_H_B_bits_per_symbol": float(h_ab - h_b),
        "V_A_given_B_bits_squared_per_symbol_direct": float(v_a_given_b),
    }
    return analysis, audit


def _scenario(
    analysis: dict[str, Any], order: str, n_symbols: int, budget_bits: float
) -> dict[str, Any]:
    planes = analysis["planes"]
    plane_failure = FAILURE_ASSUMPTION / len(planes)
    z = NormalDist().inv_cdf(1.0 - plane_failure)
    plane_scenarios = []
    for plane in planes:
        h_k = float(plane["H_bit_given_B_prefix_bits_per_symbol"])
        v_k = float(plane["V_bit_given_B_prefix_bits_squared_per_symbol"])
        unclipped = math.ceil(n_symbols * h_k + math.sqrt(n_symbols * v_k) * z)
        clipped = min(n_symbols, max(0, unclipped))
        plane_scenarios.append(
            {
                "alice_bit_index_from_lsb": int(plane["alice_bit_index_from_lsb"]),
                "H_bits_per_symbol": h_k,
                "V_bits_squared_per_symbol": v_k,
                "m_unclipped_bits": int(unclipped),
                "m_bits": int(clipped),
                "clipped": bool(clipped != unclipped),
            }
        )

    leak_bits = sum(int(plane["m_bits"]) for plane in plane_scenarios)
    h_a_total = n_symbols * float(analysis["H_A_bits_per_symbol"])
    kept_bits = h_a_total - leak_bits
    valid_yield = kept_bits >= 0.0
    failure_penalty = kept_bits * FAILURE_ASSUMPTION
    expected_numerator = leak_bits + TAG_BITS + failure_penalty
    expected_yield = kept_bits - TAG_BITS - failure_penalty
    denominator = n_symbols * float(analysis["H_A_given_B_bits_per_symbol"])
    f_expected = expected_numerator / denominator if valid_yield and denominator > 0.0 else None
    return {
        "scenario_kind": "NORMAL_APPROX_SCENARIO",
        "claim_ceiling": "normal approximation only; not an achievable-code rate guarantee",
        "m_k_formula": "ceil(N*H_k + sqrt(N*V_k)*z), clipped to [0,N]",
        "N_symbols": int(n_symbols),
        "order_name": order,
        "bit_order_from_lsb": list(BIT_ORDER[order]),
        "joint_failure_assumption": FAILURE_ASSUMPTION,
        "per_plane_failure_probability": plane_failure,
        "normal_quantile_probability": 1.0 - plane_failure,
        "normal_quantile_z": float(z),
        "planes": plane_scenarios,
        "L_EC_bits": int(leak_bits),
        "tag_bits": TAG_BITS,
        "budget_bits": float(budget_bits),
        "budget_slack_after_L_and_tag_bits": float(budget_bits - leak_bits - TAG_BITS),
        "within_budget": bool(leak_bits + TAG_BITS <= budget_bits),
        "H_A_total_bits": float(h_a_total),
        "kept_bits": float(kept_bits),
        "valid_yield": bool(valid_yield),
        "expected_failure_penalty_bits": float(failure_penalty),
        "Y_expected_bits": float(expected_yield),
        "H_A_given_B_total_bits": float(denominator),
        "expected_f_numerator_bits": float(expected_numerator),
        "budget_slack_expected_numerator_bits": float(budget_bits - expected_numerator),
        "f_expected_dimensionless": float(f_expected) if f_expected is not None else None,
        "budget_projection": {
            "formula": "1040*N_symbols/1024 + 64 shared tag bits",
            "bits": float(budget_bits),
            "ec_bits_assumed": 1040.0 * n_symbols / 1024.0,
            "shared_tag_bits": 64,
            "status": "planning projection; not an observed long-block baseline",
        },
    }


def _same_science(expected: Any, actual: Any, path: str) -> int:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ValueError(f"{path}: expected JSON object")
        expected_keys = set(expected)
        actual_keys = set(actual)
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        if missing or extra:
            raise ValueError(f"{path}: field mismatch; missing={missing}, extra={extra}")
        return sum(_same_science(expected[key], actual[key], f"{path}.{key}") for key in expected)
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError(f"{path}: array length/type mismatch")
        return sum(_same_science(left, right, f"{path}[{index}]") for index, (left, right) in enumerate(zip(expected, actual)))
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if type(expected) is not type(actual) or expected != actual:
            raise ValueError(f"{path}: expected {expected!r}, got {actual!r}")
        return 0
    if isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or expected != actual:
            raise ValueError(f"{path}: integer mismatch; expected {expected!r}, got {actual!r}")
        return 1
    if isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            raise ValueError(f"{path}: expected numeric value, got {actual!r}")
        actual_float = float(actual)
        if not math.isfinite(actual_float) or abs(expected - actual_float) > ABS_TOL:
            raise ValueError(
                f"{path}: absolute error {abs(expected - actual_float):.17g} exceeds {ABS_TOL:g}; "
                f"expected {expected:.17g}, got {actual_float:.17g}"
            )
        return 1
    raise TypeError(f"{path}: unsupported expected value type {type(expected).__name__}")


def _check_envelope(
    path: Path, source: str, encoding: str, order: str, n_train: int
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"primary result is missing: {path}")
    with path.open("r", encoding="utf-8") as stream:
        primary = json.load(stream)
    if not isinstance(primary, dict):
        raise ValueError(f"{path}: primary result must be a JSON object")
    required = {"source", "input_path", "source_role", "N_train", "encoding", "analysis", "scenarios"}
    missing = sorted(required.difference(primary))
    if missing:
        raise ValueError(f"{path}: missing envelope fields {missing}")
    if primary["source"] != source or primary["source_role"] != "TRAIN":
        raise ValueError(f"{path}: source/source_role do not match the frozen TRAIN scope")
    if primary["encoding"] != encoding:
        raise ValueError(f"{path}: encoding mismatch")
    if type(primary["N_train"]) is not int or primary["N_train"] != n_train:
        raise ValueError(f"{path}: N_train mismatch; expected {n_train}, got {primary['N_train']!r}")
    rel_input = (HISTOGRAM_ROOT / f"{source}_N_ab_train_sparse.npz").as_posix()
    actual_input = str(primary["input_path"]).replace("\\", "/")
    if not actual_input.endswith(rel_input):
        raise ValueError(f"{path}: input_path does not identify {rel_input}")

    for key, expected in (("Q", 1024), ("alphabet_size", 1024), ("n_planes", 10)):
        if key in primary and (type(primary[key]) is not int or primary[key] != expected):
            raise ValueError(f"{path}: metadata {key} expected {expected}, got {primary[key]!r}")
    if "shape" in primary and primary["shape"] != [1024, 1024]:
        raise ValueError(f"{path}: count matrix shape metadata mismatch")
    if "order" in primary and primary["order"] != order:
        raise ValueError(f"{path}: order metadata mismatch")
    if "bit_order_from_lsb" in primary and primary["bit_order_from_lsb"] != list(BIT_ORDER[order]):
        raise ValueError(f"{path}: bit_order_from_lsb metadata mismatch")
    return primary


def recompute(primary_root: Path) -> dict[str, Any]:
    results = []
    audits = []
    comparisons = 0
    for source in SOURCES:
        rel_input = HISTOGRAM_ROOT / f"{source}_N_ab_train_sparse.npz"
        counts_natural, n_train = _load_coo(ROOT / rel_input)
        if n_train <= 0:
            raise ValueError(f"{rel_input}: N_train must be positive")
        for encoding in ENCODINGS:
            counts = _encoded_counts(counts_natural, encoding)
            for order in ORDERS:
                analysis, audit = _analyze(counts, order)
                scenarios = [
                    _scenario(
                        analysis,
                        order,
                        n_symbols,
                        1040.0 * n_symbols / 1024.0 + 64.0,
                    )
                    for n_symbols in BLOCK_LENGTHS
                ]
                primary_path = primary_root / f"{source}_{encoding}_{order}.json"
                primary = _check_envelope(primary_path, source, encoding, order, n_train)
                comparisons += _same_science(analysis, primary["analysis"], f"{primary_path}.analysis")
                if not isinstance(primary["scenarios"], list) or len(primary["scenarios"]) != len(scenarios):
                    raise ValueError(f"{primary_path}: expected two scenarios for N=1024 and N=16384")
                for index, (expected_scenario, actual_scenario) in enumerate(zip(scenarios, primary["scenarios"])):
                    comparisons += _same_science(
                        expected_scenario,
                        actual_scenario,
                        f"{primary_path}.scenarios[{index}]",
                    )
                results.append(
                    {
                        "source": source,
                        "source_role": "TRAIN",
                        "N_train": n_train,
                        "encoding": encoding,
                        "order": order,
                        "analysis": analysis,
                        "scenarios": scenarios,
                    }
                )
                audits.append({"source": source, "encoding": encoding, "order": order, **audit})
    if len(results) != 12:
        raise ArithmeticError(f"expected 12 source/encoding/order records, found {len(results)}")
    return {
        "scope": "R1 accepted materialized TRAIN COO aggregates only",
        "claim_ceiling": "independent arithmetic check; no CQ, VAL/HOLD, decoder, FER, or route-acceptance claim",
        "comparison": {
            "primary_root": str(primary_root),
            "records_compared": len(results),
            "scientific_scalar_fields_compared": comparisons,
            "float_absolute_tolerance": ABS_TOL,
            "integer_comparison": "exact",
            "runtime_fields_compared": False,
        },
        "direct_entropy_variance_audit": audits,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.primary_root.is_dir():
        raise FileNotFoundError(f"primary root does not exist: {args.primary_root}")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite independent result: {args.output}")
    report = recompute(args.primary_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(
        f"A5 PASS: {report['comparison']['records_compared']} records, "
        f"{report['comparison']['scientific_scalar_fields_compared']} scientific scalar fields"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
