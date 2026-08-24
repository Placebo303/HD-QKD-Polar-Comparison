"""V37-P0 Finite-Length Degree Feasibility Analyzer.

This module provides read-only scientific tooling to evaluate the finite-length
topological realizability of candidate variable-node degree distributions
before attempting graph construction or decoder execution.

Key Theoretical Quantities:
1. Edge-to-Node Perspective Conversion:
   L_i = (lambda_i / i) / sum_j (lambda_j / j)
   Average variable degree: dbar_v = 1 / sum_j (lambda_j / j)

2. Exact Node Degree Apportionment (Hamilton / Largest Remainder):
   sum_i N_i = n, where N_i approx n * L_i

3. Variable Sockets & Implied Check Degree:
   Total sockets: E = sum_i i * N_i
   Average check degree: dbar_c(m) = E / m

4. Degree-2 Subgraph Feasibility (Forest Bound & Cycle Rank):
   A degree-2 variable node corresponds to an edge in the check-node multigraph.
   For m check nodes, any cycle-free subgraph (forest) has at most m - 1 edges.
   Therefore, the unavoidable degree-2 cycle rank lower bound is:
       gamma_2 >= max(0, N_2 - (m - 1))
   When N_2 > m - 1, a cycle-free degree-2 subgraph is mathematically impossible.
"""
from __future__ import annotations

import argparse
import json
import math
from numbers import Integral
from typing import Any, Mapping, Sequence, Tuple, Union


def parse_and_validate_lambda(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    tol: float = 1e-6,
    min_degree: int = 1,
) -> dict[int, float]:
    """Parse, validate, and normalize edge-perspective lambda distribution.

    Args:
        lambda_edge: Mapping or sequence of (degree, weight) pairs.
        tol: Absolute tolerance for the sum of weights to equal 1.0.
        min_degree: Minimum allowed integer degree (default 1).

    Returns:
        Canonical sorted dict {degree (int): weight (float)}.

    Raises:
        ValueError: If input format, degrees, or weights are invalid, or if
            weights do not sum to 1.0 within tolerance.
    """
    if isinstance(lambda_edge, Mapping):
        items = list(lambda_edge.items())
    elif isinstance(lambda_edge, (list, tuple)):
        items = list(lambda_edge)
    else:
        raise ValueError(f"lambda_edge must be a mapping or sequence of pairs, got {type(lambda_edge).__name__}")

    if not items:
        raise ValueError("lambda_edge cannot be empty")

    clean_dict: dict[int, float] = {}
    for item in items:
        if not (isinstance(item, (tuple, list)) and len(item) == 2):
            raise ValueError(f"Expected (degree, weight) pair, got {item!r}")
        raw_d, raw_w = item

        # Validate degree
        if isinstance(raw_d, bool):
            raise ValueError(f"Degree cannot be boolean: {raw_d!r}")
        try:
            d = int(raw_d)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Degree must be convertible to integer: {raw_d!r}") from exc

        if d < min_degree:
            raise ValueError(f"Degree {d} is less than minimum allowed degree {min_degree}")

        # Validate weight
        if isinstance(raw_w, bool):
            raise ValueError(f"Weight cannot be boolean: {raw_w!r}")
        try:
            w = float(raw_w)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Weight must be convertible to float: {raw_w!r}") from exc

        if not math.isfinite(w):
            raise ValueError(f"Weight for degree {d} must be finite, got {w}")
        if w <= 0.0:
            raise ValueError(f"Weight for degree {d} must be positive, got {w}")

        if d in clean_dict:
            clean_dict[d] += w
        else:
            clean_dict[d] = w

    total_weight = sum(clean_dict.values())
    if not math.isfinite(total_weight):
        raise ValueError("Sum of lambda weights is not finite")
    if abs(total_weight - 1.0) > tol:
        raise ValueError(
            f"lambda weights must sum to 1.0 within tolerance {tol:g} (got {total_weight:.8f})"
        )

    # Return normalized canonical dictionary sorted by degree
    return {d: clean_dict[d] / total_weight for d in sorted(clean_dict)}


def edge_to_node_distribution(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    tol: float = 1e-6,
) -> dict[int, float]:
    """Convert edge-perspective lambda to node-perspective L_i distribution.

    Formula:
        L_i = (lambda_i / i) / sum_j (lambda_j / j)

    Args:
        lambda_edge: Edge-perspective degree distribution.
        tol: Tolerance for lambda validation.

    Returns:
        Dict {degree (int): node_fraction (float)} where fractions sum to 1.0.
    """
    clean_lambda = parse_and_validate_lambda(lambda_edge, tol=tol)
    harmonic_sum = sum(w / d for d, w in clean_lambda.items())
    if harmonic_sum <= 0.0 or not math.isfinite(harmonic_sum):
        raise ValueError("Harmonic sum of edge distribution must be positive and finite")

    return {d: (w / d) / harmonic_sum for d, w in clean_lambda.items()}


def largest_remainder_counts(proportions: Sequence[float], total: int) -> list[int]:
    """Integer counts summing exactly to total using largest-remainder apportionment.

    Args:
        proportions: Sequence of non-negative fractions summing to 1.0.
        total: Total integer count to allocate (must be positive integer).

    Returns:
        List of integer counts summing exactly to total.
    """
    if isinstance(total, bool) or not isinstance(total, Integral) or int(total) < 1:
        raise ValueError(f"Total must be a positive integer, got {total!r}")
    total = int(total)

    floors = [int(math.floor(p * total)) for p in proportions]
    remainder = total - sum(floors)
    fractions = [p * total - math.floor(p * total) for p in proportions]

    # Order indices by descending fractional part, stable tie-break by index
    order = sorted(range(len(proportions)), key=lambda idx: (-fractions[idx], idx))
    counts = list(floors)
    for i in range(remainder):
        counts[order[i % len(order)]] += 1
    return counts


def calculate_node_degree_counts(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    n: int = 1024,
    tol: float = 1e-6,
) -> dict[int, int]:
    """Calculate integer variable-node counts by degree summing to exactly n.

    Args:
        lambda_edge: Edge-perspective degree distribution.
        n: Total number of variable nodes.
        tol: Tolerance for lambda validation.

    Returns:
        Dict {degree (int): count (int)} such that sum(counts.values()) == n.
    """
    node_dist = edge_to_node_distribution(lambda_edge, tol=tol)
    degrees = sorted(node_dist.keys())
    proportions = [node_dist[d] for d in degrees]
    counts = largest_remainder_counts(proportions, n)
    return {d: count for d, count in zip(degrees, counts)}


def calculate_total_sockets(degree_counts: Mapping[int, int]) -> int:
    """Calculate total variable-node edge sockets E = sum_d (d * N_d)."""
    return sum(int(d) * int(count) for d, count in degree_counts.items())


def calculate_mean_variable_degree(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    tol: float = 1e-6,
) -> float:
    """Calculate mean variable-node degree dbar_v = 1 / sum_j (lambda_j / j)."""
    clean_lambda = parse_and_validate_lambda(lambda_edge, tol=tol)
    harmonic_sum = sum(w / d for d, w in clean_lambda.items())
    return 1.0 / harmonic_sum


def analyze_degree2_subgraph(N2: int, m: int) -> dict[str, Any]:
    """Analyze cycle feasibility of the degree-2 check-node subgraph.

    In a Tanner graph, each degree-2 variable node forms an edge in the
    check-node graph. For m check nodes:
    - Forest upper bound: A cycle-free graph on m vertices can have at most m - 1 edges.
    - Unavoidable cycle rank lower bound: max(0, N2 - (m - 1)).

    Args:
        N2: Number of degree-2 variable nodes.
        m: Number of check nodes.

    Returns:
        Dictionary with forest bound, cycle rank lower bound, and feasibility flag.
    """
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError(f"m must be a positive integer, got {m!r}")
    if isinstance(N2, bool) or not isinstance(N2, Integral) or int(N2) < 0:
        raise ValueError(f"N2 must be a non-negative integer, got {N2!r}")

    m_int = int(m)
    n2_int = int(N2)
    forest_bound = m_int - 1
    cycle_rank_lower_bound = max(0, n2_int - forest_bound)
    is_feasible = n2_int <= forest_bound

    return {
        "m": m_int,
        "N2": n2_int,
        "forest_bound": forest_bound,
        "cycle_rank_lower_bound": cycle_rank_lower_bound,
        "excess_degree2_nodes": cycle_rank_lower_bound,
        "is_forest_feasible": is_feasible,
    }


def analyze_degree_feasibility(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    n: int = 1024,
    m_values: Sequence[int] = (184, 190, 192),
    tol: float = 1e-6,
) -> dict[str, Any]:
    """Perform full finite-length degree feasibility analysis.

    Args:
        lambda_edge: Edge-perspective degree distribution.
        n: Block length (number of variable nodes). Default 1024.
        m_values: Sequence of target check node counts. Default (184, 190, 192).
        tol: Tolerance for lambda validation.

    Returns:
        JSON-serializable analysis report dictionary.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")
    n_int = int(n)

    m_list = [int(m) for m in m_values]
    for m in m_list:
        if m < 1:
            raise ValueError(f"Check node count m must be >= 1, got {m}")

    clean_lambda = parse_and_validate_lambda(lambda_edge, tol=tol)
    node_dist = edge_to_node_distribution(clean_lambda, tol=tol)
    degree_counts = calculate_node_degree_counts(clean_lambda, n=n_int, tol=tol)
    total_sockets = calculate_total_sockets(degree_counts)
    dbar_v = calculate_mean_variable_degree(clean_lambda, tol=tol)

    N2 = degree_counts.get(2, 0)
    L2 = node_dist.get(2, 0.0)

    # Check node degree analysis
    check_analysis: dict[str, Any] = {}
    for m in m_list:
        mean_dc = total_sockets / m
        check_analysis[str(m)] = {
            "m": m,
            "mean_check_degree": round(mean_dc, 6),
            "mean_check_degree_exact": mean_dc,
            "dc_floor": math.floor(mean_dc),
            "dc_ceil": math.ceil(mean_dc),
            "rate": 1.0 - (m / n_int),
            "is_check_degree_feasible": mean_dc >= 2.0,
        }

    # Degree-2 feasibility per m
    degree2_by_m: dict[str, Any] = {}
    for m in m_list:
        degree2_by_m[str(m)] = analyze_degree2_subgraph(N2, m)

    forest_bounds = {str(m): m - 1 for m in m_list}
    cycle_rank_lower_bounds = {str(m): max(0, N2 - (m - 1)) for m in m_list}

    # Structured result
    report: dict[str, Any] = {
        "lambda_edge": {str(d): float(w) for d, w in clean_lambda.items()},
        "lambda_node": {str(d): float(w) for d, w in node_dist.items()},
        "n": n_int,
        "m_values": m_list,
        "mean_variable_degree": round(dbar_v, 6),
        "mean_variable_degree_exact": dbar_v,
        "degree_counts": {str(d): count for d, count in degree_counts.items()},
        "total_variable_sockets": total_sockets,
        "check_node_analysis": check_analysis,
        "degree2_analysis": {
            "N2": N2,
            "N2_fraction": round(L2, 6),
            "N2_fraction_exact": L2,
            "by_m": degree2_by_m,
            "forest_bounds": forest_bounds,
            "cycle_rank_lower_bounds": cycle_rank_lower_bounds,
            # Top-level field convenience:
            "forest_bound": (m_list[0] - 1) if len(m_list) == 1 else forest_bounds,
            "cycle_rank_lower_bound": max(0, N2 - (m_list[0] - 1)) if len(m_list) == 1 else cycle_rank_lower_bounds,
        },
        "feasibility_verdict": {
            "all_forest_feasible": all(N2 <= (m - 1) for m in m_list),
            "all_check_degrees_feasible": all((total_sockets / m) >= 2.0 for m in m_list),
            "structurally_cycle_free_degree2_possible": any(N2 <= (m - 1) for m in m_list),
        },
    }
    return report


def generate_degree_feasibility_report(
    lambda_edge: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]],
    n: int = 1024,
    m_values: Sequence[int] = (184, 190, 192),
    indent: int = 2,
) -> str:
    """Generate a formatted JSON string report of degree feasibility analysis."""
    report = analyze_degree_feasibility(lambda_edge, n=n, m_values=m_values)
    return json.dumps(report, indent=indent)


def main() -> None:
    """CLI entrypoint for standalone degree feasibility analysis."""
    parser = argparse.ArgumentParser(
        description="V37-P0 Finite-Length Degree Feasibility Analyzer for NB-LDPC Candidates"
    )
    parser.add_argument(
        "--lambda",
        dest="lambda_json",
        type=str,
        required=True,
        help="JSON string of edge-perspective lambda distribution, e.g. '{\"2\": 0.85, \"4\": 0.15}'",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1024,
        help="Block length n (default: 1024)",
    )
    parser.add_argument(
        "--m",
        dest="m_str",
        type=str,
        default="184,190,192",
        help="Comma-separated check node counts m (default: '184,190,192')",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Optional output path to write JSON report",
    )

    args = parser.parse_args()
    lambda_raw = json.loads(args.lambda_json)
    m_values = [int(x.strip()) for x in args.m_str.split(",") if x.strip()]

    report = analyze_degree_feasibility(lambda_raw, n=args.n, m_values=m_values)
    report_json = json.dumps(report, indent=2)

    if args.out:
        out_path = args.out
        import pathlib
        pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_json)
        print(f"Feasibility report written to {out_path}")
    else:
        print(report_json)


if __name__ == "__main__":
    main()
