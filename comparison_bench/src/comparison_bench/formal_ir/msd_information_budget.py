"""Conditional information and finite-length MSD budget scenarios.

Counts use rows for Alice symbols and columns for Bob symbols. Bit indices
are numbered from the least significant bit; ``MSB_FIRST`` and ``LSB_FIRST``
select the complete decode order, while an explicit sequence selects any
complete permutation.
"""

from __future__ import annotations

import math
import operator
from statistics import NormalDist
from typing import Sequence

import numpy as np


_CHAIN_TOL = 1e-10


def validate_counts(counts: object) -> np.ndarray:
    """Return a float64 square joint-count table after basic validation."""
    raw = np.asarray(counts)
    if np.iscomplexobj(raw):
        raise ValueError("counts must be real-valued")
    try:
        table = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("counts must be numeric") from exc
    if table.ndim != 2 or table.shape[0] != table.shape[1]:
        raise ValueError("counts must be a square two-dimensional table")
    alphabet_size = int(table.shape[0])
    if alphabet_size < 1 or alphabet_size & (alphabet_size - 1):
        raise ValueError("alphabet size must be a positive power of two")
    if not np.all(np.isfinite(table)):
        raise ValueError("counts must be finite")
    if np.any(table < 0):
        raise ValueError("counts must be nonnegative")
    total = float(np.sum(table, dtype=np.float64))
    if not math.isfinite(total) or total <= 0:
        raise ValueError("counts must have a finite positive total")
    return table


def _normalize_order(order: str | Sequence[int], n_planes: int) -> tuple[tuple[int, ...], str]:
    if isinstance(order, str):
        name = order.strip().upper()
        if name == "MSB_FIRST":
            positions = tuple(range(n_planes - 1, -1, -1))
        elif name == "LSB_FIRST":
            positions = tuple(range(n_planes))
        else:
            raise ValueError("order must be MSB_FIRST, LSB_FIRST, or a complete bit permutation")
    else:
        try:
            raw_positions = tuple(order)
        except TypeError as exc:
            raise ValueError("order must be MSB_FIRST, LSB_FIRST, or a complete bit permutation") from exc
        positions_list = []
        for item in raw_positions:
            if isinstance(item, (bool, np.bool_)):
                raise ValueError("bit positions must be integer indices")
            try:
                positions_list.append(operator.index(item))
            except TypeError as exc:
                raise ValueError("bit positions must be integer indices") from exc
        positions = tuple(positions_list)
        name = "CUSTOM"
    if len(positions) != n_planes or set(positions) != set(range(n_planes)):
        raise ValueError("order must contain each Alice bit position exactly once")
    return positions, name


def _entropy(probabilities: np.ndarray) -> float:
    positive = probabilities > 0
    if not np.any(positive):
        return 0.0
    values = probabilities[positive]
    return float(-np.sum(values * np.log2(values), dtype=np.float64))


def _binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return float(
        -probability * math.log2(probability)
        -(1.0 - probability) * math.log2(1.0 - probability)
    )


def _plane_moments(
    cell_a: np.ndarray,
    cell_b: np.ndarray,
    cell_mass: np.ndarray,
    bit_values: np.ndarray,
    prefix_values: np.ndarray,
    alphabet_size: int,
) -> tuple[float, float]:
    group_codes = prefix_values[cell_a] * alphabet_size + cell_b
    bit_group_codes = 2 * group_codes + bit_values[cell_a].astype(np.int64)
    bit_masses = np.bincount(
        bit_group_codes,
        weights=cell_mass,
        minlength=2 * alphabet_size * alphabet_size,
    )
    active_codes = np.flatnonzero(bit_masses > 0.0)
    group_masses = bit_masses.reshape(-1, 2).sum(axis=1, dtype=np.float64)
    active_masses = bit_masses[active_codes]
    conditional_probabilities = active_masses / group_masses[active_codes // 2]
    information_bits = -np.log2(conditional_probabilities)
    entropy_bits_per_symbol = float(
        np.sum(active_masses * information_bits, dtype=np.float64)
    )
    variance_bits_squared_per_symbol = float(
        np.sum(
            active_masses * (information_bits - entropy_bits_per_symbol) ** 2,
            dtype=np.float64,
        )
    )
    return entropy_bits_per_symbol, variance_bits_squared_per_symbol


def analyze_joint_counts(
    counts: object,
    order: str | Sequence[int] = "MSB_FIRST",
) -> dict[str, object]:
    """Compute joint, chain, and per-plane information quantities.

    ``H(A|B)`` and its information-density variance are computed directly
    from ``P(A|B)``. Each ordered plane uses grouped masses for
    ``P(A_k|B,A_<k)``. Zero-mass cells and groups contribute nothing.
    """
    table = validate_counts(counts)
    alphabet_size = int(table.shape[0])
    n_planes = alphabet_size.bit_length() - 1
    bit_order, order_name = _normalize_order(order, n_planes)
    probabilities = table / float(np.sum(table, dtype=np.float64))
    alice_symbols = np.arange(alphabet_size, dtype=np.int64)
    bob_symbols = np.arange(alphabet_size, dtype=np.int64)
    p_b = np.sum(probabilities, axis=0, dtype=np.float64)
    p_a = np.sum(probabilities, axis=1, dtype=np.float64)
    h_a_bits_per_symbol = _entropy(p_a)

    h_a_given_b_bits_per_symbol = 0.0
    for bob_symbol, bob_mass in enumerate(p_b):
        if bob_mass > 0.0:
            h_a_given_b_bits_per_symbol += float(bob_mass) * _entropy(
                probabilities[:, bob_symbol] / bob_mass
            )

    positive_a, positive_b = np.nonzero(probabilities > 0.0)
    cell_mass = probabilities[positive_a, positive_b]
    conditional_a_given_b = cell_mass / p_b[positive_b]
    joint_information_bits = -np.log2(conditional_a_given_b)
    joint_information_mean_bits_per_symbol = float(
        np.sum(cell_mass * joint_information_bits, dtype=np.float64)
    )
    if abs(joint_information_mean_bits_per_symbol - h_a_given_b_bits_per_symbol) > _CHAIN_TOL:
        raise ArithmeticError("direct H(A|B) and information-density mean disagree")
    v_a_given_b_bits_squared_per_symbol = math.fsum(
        float(mass) * (float(info) - joint_information_mean_bits_per_symbol) ** 2
        for mass, info in zip(cell_mass, joint_information_bits)
    )

    planes: list[dict[str, float | int]] = []
    prior_bit_indices: list[int] = []
    sum_h2_marginal_error_bits_per_symbol = 0.0
    sum_h_bit_given_b_bits_per_symbol = 0.0
    for bit_index in bit_order:
        alice_bit = ((alice_symbols >> bit_index) & 1).astype(bool)
        bob_bit = ((bob_symbols >> bit_index) & 1).astype(bool)
        prefix_codes = np.zeros(alphabet_size, dtype=np.int64)
        for prefix_position, prefix_bit_index in enumerate(prior_bit_indices):
            prefix_codes |= (
                ((alice_symbols >> prefix_bit_index) & 1).astype(np.int64)
                << prefix_position
            )
        chain_entropy, plane_variance = _plane_moments(
            positive_a,
            positive_b,
            cell_mass,
            alice_bit,
            prefix_codes,
            alphabet_size,
        )

        full_b_entropy = 0.0
        for bob_symbol, bob_mass in enumerate(p_b):
            if bob_mass == 0.0:
                continue
            bit_masses = [
                float(np.sum(probabilities[alice_bit == bit, bob_symbol]))
                for bit in (False, True)
            ]
            full_b_entropy += float(bob_mass) * _binary_entropy(bit_masses[1] / float(bob_mass))

        error_mask = alice_bit[:, None] != bob_bit[None, :]
        marginal_bit_error_probability = float(
            np.sum(probabilities[error_mask], dtype=np.float64)
        )
        h2_marginal_error_bits_per_symbol = _binary_entropy(marginal_bit_error_probability)
        sum_h2_marginal_error_bits_per_symbol += h2_marginal_error_bits_per_symbol
        sum_h_bit_given_b_bits_per_symbol += full_b_entropy
        planes.append(
            {
                "alice_bit_index_from_lsb": int(bit_index),
                "H_bit_given_B_prefix_bits_per_symbol": float(chain_entropy),
                "V_bit_given_B_prefix_bits_squared_per_symbol": float(plane_variance),
                "H_bit_given_B_bits_per_symbol": float(full_b_entropy),
                "marginal_bit_error_probability": marginal_bit_error_probability,
                "h2_marginal_bit_error_bits_per_symbol": h2_marginal_error_bits_per_symbol,
            }
        )
        prior_bit_indices.append(bit_index)

    sum_chain_bits_per_symbol = math.fsum(
        float(plane["H_bit_given_B_prefix_bits_per_symbol"]) for plane in planes
    )
    chain_closure_error_bits_per_symbol = (
        sum_chain_bits_per_symbol - h_a_given_b_bits_per_symbol
    )
    if abs(chain_closure_error_bits_per_symbol) > _CHAIN_TOL:
        raise ArithmeticError(
            "ordered conditional entropies do not close to H(A|B) within 1e-10 bits/symbol"
        )

    return {
        "alphabet_size": alphabet_size,
        "n_planes": n_planes,
        "order_name": order_name,
        "bit_order_from_lsb": list(bit_order),
        "H_A_bits_per_symbol": h_a_bits_per_symbol,
        "H_A_given_B_bits_per_symbol": h_a_given_b_bits_per_symbol,
        "V_A_given_B_bits_squared_per_symbol": float(v_a_given_b_bits_squared_per_symbol),
        "sum_chain_H_bit_given_B_prefix_bits_per_symbol": sum_chain_bits_per_symbol,
        "sum_H_bit_given_B_bits_per_symbol": sum_h_bit_given_b_bits_per_symbol,
        "sum_h2_marginal_bit_error_bits_per_symbol": sum_h2_marginal_error_bits_per_symbol,
        "chain_closure_error_bits_per_symbol": chain_closure_error_bits_per_symbol,
        "planes": planes,
    }


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite nonnegative number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite nonnegative number") from exc
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return result


def finite_length_scenario(
    counts: object,
    order: str | Sequence[int],
    N: int,
    joint_failure_assumption: float,
    tag_bits: float,
    budget_bits: float,
) -> dict[str, object]:
    """Return a normal-approximation MSD scenario, not a code-rate guarantee."""
    if isinstance(N, (bool, np.bool_)):
        raise ValueError("N must be a positive integer symbol count")
    try:
        n_symbols = operator.index(N)
    except TypeError as exc:
        raise ValueError("N must be a positive integer symbol count") from exc
    if n_symbols <= 0:
        raise ValueError("N must be a positive integer symbol count")

    epsilon = _finite_nonnegative(joint_failure_assumption, "joint_failure_assumption")
    if epsilon <= 0.0 or epsilon >= 1.0:
        raise ValueError("joint_failure_assumption must lie strictly between 0 and 1")
    tag = _finite_nonnegative(tag_bits, "tag_bits")
    budget = _finite_nonnegative(budget_bits, "budget_bits")

    analysis = analyze_joint_counts(counts, order)
    n_planes = int(analysis["n_planes"])
    if n_planes == 0:
        raise ValueError("finite-length scenario requires at least one Alice bit plane")
    per_plane_epsilon = epsilon / n_planes
    quantile_probability = 1.0 - per_plane_epsilon
    if not 0.0 < quantile_probability < 1.0:
        raise ValueError("failure probability is outside NormalDist floating-point resolution")
    z = NormalDist().inv_cdf(quantile_probability)

    plane_scenarios: list[dict[str, object]] = []
    for plane in analysis["planes"]:
        h_k = float(plane["H_bit_given_B_prefix_bits_per_symbol"])
        v_k = float(plane["V_bit_given_B_prefix_bits_squared_per_symbol"])
        unbounded_m_bits = math.ceil(
            n_symbols * h_k + math.sqrt(n_symbols * v_k) * z
        )
        m_bits = min(n_symbols, max(0, unbounded_m_bits))
        plane_scenarios.append(
            {
                "alice_bit_index_from_lsb": int(plane["alice_bit_index_from_lsb"]),
                "H_bits_per_symbol": h_k,
                "V_bits_squared_per_symbol": v_k,
                "m_unclipped_bits": int(unbounded_m_bits),
                "m_bits": int(m_bits),
                "clipped": bool(m_bits != unbounded_m_bits),
            }
        )

    total_leakage_bits = sum(int(plane["m_bits"]) for plane in plane_scenarios)
    alice_entropy_bits = n_symbols * float(analysis["H_A_bits_per_symbol"])
    kept_bits = alice_entropy_bits - total_leakage_bits
    valid_yield = kept_bits >= 0.0
    failure_penalty_bits = kept_bits * epsilon
    expected_yield_bits = kept_bits - tag - failure_penalty_bits
    expected_f_numerator_bits = total_leakage_bits + tag + failure_penalty_bits
    entropy_denominator_bits = n_symbols * float(analysis["H_A_given_B_bits_per_symbol"])
    if valid_yield and entropy_denominator_bits > 0.0:
        f_expected = expected_f_numerator_bits / entropy_denominator_bits
    else:
        f_expected = None

    return {
        "scenario_kind": "NORMAL_APPROX_SCENARIO",
        "claim_ceiling": "normal approximation only; not an achievable-code rate guarantee",
        "m_k_formula": "ceil(N*H_k + sqrt(N*V_k)*z), clipped to [0,N]",
        "N_symbols": int(n_symbols),
        "order_name": analysis["order_name"],
        "bit_order_from_lsb": analysis["bit_order_from_lsb"],
        "joint_failure_assumption": epsilon,
        "per_plane_failure_probability": per_plane_epsilon,
        "normal_quantile_probability": quantile_probability,
        "normal_quantile_z": float(z),
        "planes": plane_scenarios,
        "L_EC_bits": int(total_leakage_bits),
        "tag_bits": tag,
        "budget_bits": budget,
        "budget_slack_after_L_and_tag_bits": budget - total_leakage_bits - tag,
        "within_budget": total_leakage_bits + tag <= budget,
        "H_A_total_bits": alice_entropy_bits,
        "kept_bits": kept_bits,
        "valid_yield": bool(valid_yield),
        "expected_failure_penalty_bits": failure_penalty_bits,
        "Y_expected_bits": expected_yield_bits,
        "expected_f_numerator_bits": expected_f_numerator_bits,
        "budget_slack_expected_numerator_bits": budget - expected_f_numerator_bits,
        "H_A_given_B_total_bits": entropy_denominator_bits,
        "f_expected_dimensionless": f_expected,
    }
