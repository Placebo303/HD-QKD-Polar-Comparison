"""Unit Test Suite for V37-P0 Finite-Length Degree Feasibility Analyzer.

Covers:
- T1: V36 Candidate Distribution Evaluation (N2 ≈ 941, cycle rank lower bounds, exact floor/ceil check allocations)
- T2: Low-Degree-2 Feasible Distribution (N2 <= m - 1, cycle rank lower bound = 0)
- T3: Zero-Degree-2 Distribution (Regular degree-3, N2 = 0)
- T4: Mixed-m Forest Feasibility (one m fails, another passes -> global verdict False, any_source True)
- T5: Invalid Lambda Inputs (Sum != 1, negative, non-finite, degree < 1, empty)
- T6: Invalid Graph Dimensions (n <= 0, m <= 0)
- T7: String-Key and Integer-Key Equivalence
- T8: Largest-Remainder Apportionment Sum Invariant (sum == n)
- T9: Exact Check Degree Floor/Ceil Socket Allocation Function
- T10: Full JSON Report Generation and Schema Validation
- T11: CLI Execution via module entrypoint
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import pytest

from comparison_bench.src.comparison_bench.formal_ir.v37_degree_feasibility import (
    analyze_degree2_subgraph,
    analyze_degree_feasibility,
    calculate_check_degree_allocation,
    calculate_mean_variable_degree,
    calculate_node_degree_counts,
    calculate_total_sockets,
    edge_to_node_distribution,
    generate_degree_feasibility_report,
    largest_remainder_counts,
    parse_and_validate_lambda,
)


def test_v36_distribution_analysis():
    """T1: Verify V36 candidate (lambda_2=0.85, lambda_4=0.15) on n=1024, m=[184, 190, 192]."""
    lambda_v36 = {2: 0.85, 4: 0.15}
    n = 1024
    m_values = [184, 190, 192]

    report = analyze_degree_feasibility(lambda_v36, n=n, m_values=m_values)

    # 1. Harmonic sum and mean variable degree
    # integral = 0.85/2 + 0.15/4 = 0.425 + 0.0375 = 0.4625 = 37/80
    # dbar_v = 1 / 0.4625 = 80 / 37 ≈ 2.162162
    assert math.isclose(report["mean_variable_degree_exact"], 80.0 / 37.0, rel_tol=1e-9)

    # 2. Node perspective distribution
    # L_2 = 0.425 / 0.4625 = 34 / 37 ≈ 0.9189189
    # L_4 = 0.0375 / 0.4625 = 3 / 37 ≈ 0.0810811
    node_dist = report["lambda_node"]
    assert math.isclose(node_dist["2"], 34.0 / 37.0, rel_tol=1e-9)
    assert math.isclose(node_dist["4"], 3.0 / 37.0, rel_tol=1e-9)

    # 3. Integer node degree counts
    # 1024 * (34/37) = 940.97297... -> 941
    # 1024 * (3/37) = 83.02702... -> 83
    counts = report["degree_counts"]
    assert counts["2"] == 941
    assert counts["4"] == 83
    assert counts["2"] + counts["4"] == 1024

    # 4. Total variable sockets
    # E = 2 * 941 + 4 * 83 = 1882 + 332 = 2214
    assert report["total_variable_sockets"] == 2214

    # 5. Check-node degree allocation analysis (R3 exact requirements)
    chk = report["check_node_analysis"]

    # m=184: 178 degree-12 + 6 degree-13 checks, max=13
    chk_184 = chk["184"]
    assert chk_184["dc_floor"] == 12
    assert chk_184["dc_ceil"] == 13
    assert chk_184["n_checks_floor"] == 178
    assert chk_184["n_checks_ceil"] == 6
    assert chk_184["realized_max_check_degree"] == 13
    assert chk_184["check_degree_allocation"] == {"12": 178, "13": 6}
    assert chk_184["n_checks_floor"] * 12 + chk_184["n_checks_ceil"] * 13 == 2214
    assert chk_184["is_socket_allocation_feasible"] is True

    # m=190: 66 degree-11 + 124 degree-12 checks, max=12
    chk_190 = chk["190"]
    assert chk_190["dc_floor"] == 11
    assert chk_190["dc_ceil"] == 12
    assert chk_190["n_checks_floor"] == 66
    assert chk_190["n_checks_ceil"] == 124
    assert chk_190["realized_max_check_degree"] == 12
    assert chk_190["check_degree_allocation"] == {"11": 66, "12": 124}
    assert chk_190["n_checks_floor"] * 11 + chk_190["n_checks_ceil"] * 12 == 2214
    assert chk_190["is_socket_allocation_feasible"] is True

    # m=192: 90 degree-11 + 102 degree-12 checks, max=12
    chk_192 = chk["192"]
    assert chk_192["dc_floor"] == 11
    assert chk_192["dc_ceil"] == 12
    assert chk_192["n_checks_floor"] == 90
    assert chk_192["n_checks_ceil"] == 102
    assert chk_192["realized_max_check_degree"] == 12
    assert chk_192["check_degree_allocation"] == {"11": 90, "12": 102}
    assert chk_192["n_checks_floor"] * 11 + chk_192["n_checks_ceil"] * 12 == 2214
    assert chk_192["is_socket_allocation_feasible"] is True

    # 6. Degree-2 feasibility and cycle rank lower bounds
    d2 = report["degree2_analysis"]
    assert d2["N2"] == 941

    # For m=184: forest bound 183, cycle rank lower bound = 941 - 183 = 758
    assert d2["by_m"]["184"]["forest_bound"] == 183
    assert d2["by_m"]["184"]["cycle_rank_lower_bound"] == 758
    assert d2["by_m"]["184"]["is_forest_feasible"] is False

    # For m=190: forest bound 189, cycle rank lower bound = 941 - 189 = 752
    assert d2["by_m"]["190"]["forest_bound"] == 189
    assert d2["by_m"]["190"]["cycle_rank_lower_bound"] == 752
    assert d2["by_m"]["190"]["is_forest_feasible"] is False

    # For m=192: forest bound 191, cycle rank lower bound = 941 - 191 = 750
    assert d2["by_m"]["192"]["forest_bound"] == 191
    assert d2["by_m"]["192"]["cycle_rank_lower_bound"] == 750
    assert d2["by_m"]["192"]["is_forest_feasible"] is False

    # 7. Global feasibility verdict
    verdict = report["feasibility_verdict"]
    assert verdict["all_forest_feasible"] is False
    assert verdict["structurally_cycle_free_degree2_possible"] is False
    assert verdict["any_source_forest_feasible"] is False
    assert verdict["all_socket_allocations_feasible"] is True


def test_low_degree2_feasible_distribution():
    """T2: Verify a low-degree-2 distribution where N2 <= m - 1 (cycle rank lower bound = 0)."""
    # lambda_2 = 0.10, lambda_3 = 0.50, lambda_4 = 0.40
    lambda_low2 = {2: 0.10, 3: 0.50, 4: 0.40}
    n = 1024
    m_values = [184, 190, 192]

    report = analyze_degree_feasibility(lambda_low2, n=n, m_values=m_values)

    # Harmonic sum = 0.10/2 + 0.50/3 + 0.40/4 = 0.05 + 1/6 + 0.10 = 19/60 ≈ 0.3166667
    # L_2 = 0.05 / (19/60) = 3 / 19 ≈ 0.1578947
    # N_2 = largest_remainder(3/19 * 1024) = 162
    d2 = report["degree2_analysis"]
    assert d2["N2"] == 162

    # For m=184: forest bound 183 >= 162 -> cycle rank lower bound = 0, is_forest_feasible = True
    assert d2["by_m"]["184"]["forest_bound"] == 183
    assert d2["by_m"]["184"]["cycle_rank_lower_bound"] == 0
    assert d2["by_m"]["184"]["is_forest_feasible"] is True

    # For m=190: forest bound 189 >= 162 -> cycle rank lower bound = 0, is_forest_feasible = True
    assert d2["by_m"]["190"]["forest_bound"] == 189
    assert d2["by_m"]["190"]["cycle_rank_lower_bound"] == 0
    assert d2["by_m"]["190"]["is_forest_feasible"] is True

    # For m=192: forest bound 191 >= 162 -> cycle rank lower bound = 0, is_forest_feasible = True
    assert d2["by_m"]["192"]["forest_bound"] == 191
    assert d2["by_m"]["192"]["cycle_rank_lower_bound"] == 0
    assert d2["by_m"]["192"]["is_forest_feasible"] is True

    assert report["feasibility_verdict"]["all_forest_feasible"] is True
    assert report["feasibility_verdict"]["structurally_cycle_free_degree2_possible"] is True
    assert report["feasibility_verdict"]["any_source_forest_feasible"] is True


def test_zero_degree2_regular_distribution():
    """T3: Verify regular degree-3 distribution with N2 = 0."""
    lambda_reg3 = {3: 1.0}
    report = analyze_degree_feasibility(lambda_reg3, n=1024, m_values=[192])

    assert report["degree_counts"] == {"3": 1024}
    assert report["total_variable_sockets"] == 3072
    assert report["degree2_analysis"]["N2"] == 0
    assert report["degree2_analysis"]["by_m"]["192"]["cycle_rank_lower_bound"] == 0
    assert report["degree2_analysis"]["by_m"]["192"]["is_forest_feasible"] is True
    assert report["feasibility_verdict"]["structurally_cycle_free_degree2_possible"] is True


def test_mixed_m_forest_feasibility_semantics():
    """T4: Test mixed-feasibility where N2 passes for larger m but fails for smaller m."""
    # Construct a distribution where N2 is between m1-1 and m2-1.
    # For m=[184, 190, 192], forest bounds are [183, 189, 191].
    # Let N2 = 186 (e.g. lambda_2 = 0.115, lambda_3 = 0.885 with n=1024):
    # L_2 = (0.115 / 2) / (0.115 / 2 + 0.885 / 3) = 0.0575 / (0.0575 + 0.295) = 0.0575 / 0.3525 = 23 / 141
    # n * (23/141) = 1024 * 0.163120567 = 167.03...
    # Let's directly craft a lambda to get N2 = 186:
    # We want L_2 ≈ 186 / 1024 ≈ 0.181640625
    # L_2 = (w2/2) / (w2/2 + (1-w2)/3) = 3*w2 / (w2 + 2) = 0.181640625
    # 3*w2 = 0.181640625 * w2 + 0.36328125 => 2.818359375 * w2 = 0.36328125 => w2 ≈ 0.1288981289
    w2 = 0.1288981288981289
    lambda_mixed = {2: w2, 3: 1.0 - w2}
    report = analyze_degree_feasibility(lambda_mixed, n=1024, m_values=[184, 190, 192])

    N2 = report["degree2_analysis"]["N2"]
    assert N2 == 186

    by_m = report["degree2_analysis"]["by_m"]
    # m=184: forest bound 183 < 186 -> False, cycle rank lower bound = 3
    assert by_m["184"]["forest_bound"] == 183
    assert by_m["184"]["is_forest_feasible"] is False
    assert by_m["184"]["cycle_rank_lower_bound"] == 3

    # m=190: forest bound 189 >= 186 -> True, cycle rank lower bound = 0
    assert by_m["190"]["forest_bound"] == 189
    assert by_m["190"]["is_forest_feasible"] is True
    assert by_m["190"]["cycle_rank_lower_bound"] == 0

    # m=192: forest bound 191 >= 186 -> True, cycle rank lower bound = 0
    assert by_m["192"]["forest_bound"] == 191
    assert by_m["192"]["is_forest_feasible"] is True
    assert by_m["192"]["cycle_rank_lower_bound"] == 0

    # Global verdict MUST be False because m=184 is not feasible (R1 requirement)
    verdict = report["feasibility_verdict"]
    assert verdict["all_forest_feasible"] is False
    assert verdict["structurally_cycle_free_degree2_possible"] is False
    # At-least-one diagnostic is True
    assert verdict["any_source_forest_feasible"] is True


def test_invalid_lambda_inputs():
    """T5: Ensure invalid lambda distributions fail closed with ValueError."""
    # Sum != 1
    with pytest.raises(ValueError, match="must sum to 1.0"):
        parse_and_validate_lambda({2: 0.5, 4: 0.3})

    # Negative weight
    with pytest.raises(ValueError, match="must be positive"):
        parse_and_validate_lambda({2: 1.2, 4: -0.2})

    # Zero weight
    with pytest.raises(ValueError, match="must be positive"):
        parse_and_validate_lambda({2: 1.0, 4: 0.0})

    # Non-finite weight (NaN or Inf)
    with pytest.raises(ValueError, match="must be finite"):
        parse_and_validate_lambda({2: float("nan"), 4: 1.0})
    with pytest.raises(ValueError, match="must be finite"):
        parse_and_validate_lambda({2: float("inf"), 4: 1.0})

    # Non-integer / invalid degree
    with pytest.raises(ValueError, match="Degree must be convertible to integer"):
        parse_and_validate_lambda({"invalid_deg": 1.0})

    # Degree < 1
    with pytest.raises(ValueError, match="less than minimum allowed degree"):
        parse_and_validate_lambda({0: 0.5, 2: 0.5})

    # Boolean degree or weight
    with pytest.raises(ValueError, match="cannot be boolean"):
        parse_and_validate_lambda({True: 1.0})
    with pytest.raises(ValueError, match="cannot be boolean"):
        parse_and_validate_lambda({2: True})

    # Empty mapping
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_and_validate_lambda({})


def test_invalid_dimensions():
    """T6: Ensure invalid n or m values raise ValueError."""
    with pytest.raises(ValueError, match="n must be a positive integer"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=0)

    with pytest.raises(ValueError, match="n must be a positive integer"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=-10)

    with pytest.raises(ValueError, match="Check node count m must be >= 1"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=1024, m_values=[0])

    with pytest.raises(ValueError, match="m must be a positive integer"):
        analyze_degree2_subgraph(N2=10, m=0)

    with pytest.raises(ValueError, match="total_sockets must be a positive integer"):
        calculate_check_degree_allocation(total_sockets=0, m=100)


def test_string_key_equivalence():
    """T7: Verify string-keyed dict and integer-keyed dict produce identical analyses."""
    dict_int = {2: 0.85, 4: 0.15}
    dict_str = {"2": 0.85, "4": 0.15}

    report_int = analyze_degree_feasibility(dict_int, n=1024, m_values=[184, 190, 192])
    report_str = analyze_degree_feasibility(dict_str, n=1024, m_values=[184, 190, 192])

    assert report_int == report_str


def test_largest_remainder_invariants():
    """T8: Test exact sum and apportionment invariants for largest-remainder."""
    props = [0.1, 0.2, 0.3, 0.4]
    for total in [1, 7, 10, 100, 1024, 2048]:
        counts = largest_remainder_counts(props, total)
        assert sum(counts) == total
        assert len(counts) == len(props)


def test_check_degree_allocation_function():
    """T9: Directly test calculate_check_degree_allocation edge cases and exact algebra."""
    # Exact divisible case: E = 2000, m = 100 -> exactly 100 checks of degree 20
    res_exact = calculate_check_degree_allocation(total_sockets=2000, m=100)
    assert res_exact["dc_floor"] == 20
    assert res_exact["dc_ceil"] == 20
    assert res_exact["n_checks_floor"] == 100
    assert res_exact["n_checks_ceil"] == 0
    assert res_exact["realized_max_check_degree"] == 20
    assert res_exact["check_degree_allocation"] == {"20": 100}
    assert res_exact["is_socket_allocation_feasible"] is True

    # Infeasible check degree: E = 150, m = 100 -> dc_floor = 1 < 2 -> is_socket_allocation_feasible False
    res_infeasible = calculate_check_degree_allocation(total_sockets=150, m=100)
    assert res_infeasible["dc_floor"] == 1
    assert res_infeasible["dc_ceil"] == 2
    assert res_infeasible["is_socket_allocation_feasible"] is False


def test_full_json_report_generation():
    """T10: Verify generate_degree_feasibility_report produces valid parseable JSON."""
    json_str = generate_degree_feasibility_report({2: 0.85, 4: 0.15}, n=1024, m_values=[184, 190, 192])
    parsed = json.loads(json_str)

    assert "lambda_edge" in parsed
    assert "lambda_node" in parsed
    assert parsed["n"] == 1024
    assert parsed["m_values"] == [184, 190, 192]
    assert "degree_counts" in parsed
    assert "total_variable_sockets" in parsed
    assert "check_node_analysis" in parsed
    assert "degree2_analysis" in parsed
    assert "feasibility_verdict" in parsed


def test_cli_execution():
    """T11: Verify CLI execution via python -m runner."""
    cmd = [
        sys.executable,
        "-m",
        "comparison_bench.src.comparison_bench.cli.run_v37_degree_feasibility",
        "--lambda",
        json.dumps({"2": 0.85, "4": 0.15}),
        "--n",
        "1024",
        "--m",
        "184,190,192",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"CLI error: {proc.stderr}"
    data = json.loads(proc.stdout)
    assert data["degree_counts"]["2"] == 941
    assert data["degree2_analysis"]["N2"] == 941
    assert data["degree2_analysis"]["by_m"]["184"]["cycle_rank_lower_bound"] == 758
    assert data["check_node_analysis"]["184"]["n_checks_floor"] == 178
    assert data["check_node_analysis"]["184"]["n_checks_ceil"] == 6
