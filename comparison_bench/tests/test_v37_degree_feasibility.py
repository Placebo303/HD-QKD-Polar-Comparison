"""Unit Test Suite for V37-P0 Finite-Length Degree Feasibility Analyzer.

Covers:
- T1: V36 Candidate Distribution Evaluation (N2 ≈ 941, cycle rank lower bound hundreds)
- T2: Low-Degree-2 Feasible Distribution (N2 <= m - 1, cycle rank lower bound = 0)
- T3: Zero-Degree-2 Distribution (Regular degree-3, N2 = 0)
- T4: Invalid Lambda Inputs (Sum != 1, negative, non-finite, degree < 1, empty)
- T5: Invalid Graph Dimensions (n <= 0, m <= 0)
- T6: String-Key and Integer-Key Equivalence
- T7: Largest-Remainder Apportionment Sum Invariant (sum == n)
- T8: Full JSON Report Generation and Schema Validation
- T9: CLI Execution via module entrypoint
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

    # 5. Check-node degree analysis
    chk = report["check_node_analysis"]
    assert math.isclose(chk["184"]["mean_check_degree_exact"], 2214.0 / 184.0, rel_tol=1e-9)
    assert math.isclose(chk["190"]["mean_check_degree_exact"], 2214.0 / 190.0, rel_tol=1e-9)
    assert math.isclose(chk["192"]["mean_check_degree_exact"], 2214.0 / 192.0, rel_tol=1e-9)

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
    assert verdict["all_check_degrees_feasible"] is True


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


def test_zero_degree2_regular_distribution():
    """T3: Verify regular degree-3 distribution with N2 = 0."""
    lambda_reg3 = {3: 1.0}
    report = analyze_degree_feasibility(lambda_reg3, n=1024, m_values=[192])

    assert report["degree_counts"] == {"3": 1024}
    assert report["total_variable_sockets"] == 3072
    assert report["degree2_analysis"]["N2"] == 0
    assert report["degree2_analysis"]["by_m"]["192"]["cycle_rank_lower_bound"] == 0
    assert report["degree2_analysis"]["by_m"]["192"]["is_forest_feasible"] is True


def test_invalid_lambda_inputs():
    """T4: Ensure invalid lambda distributions fail closed with ValueError."""
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
    """T5: Ensure invalid n or m values raise ValueError."""
    with pytest.raises(ValueError, match="n must be a positive integer"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=0)

    with pytest.raises(ValueError, match="n must be a positive integer"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=-10)

    with pytest.raises(ValueError, match="Check node count m must be >= 1"):
        analyze_degree_feasibility({2: 0.85, 4: 0.15}, n=1024, m_values=[0])

    with pytest.raises(ValueError, match="m must be a positive integer"):
        analyze_degree2_subgraph(N2=10, m=0)


def test_string_key_equivalence():
    """T6: Verify string-keyed dict and integer-keyed dict produce identical analyses."""
    dict_int = {2: 0.85, 4: 0.15}
    dict_str = {"2": 0.85, "4": 0.15}

    report_int = analyze_degree_feasibility(dict_int, n=1024, m_values=[184, 190, 192])
    report_str = analyze_degree_feasibility(dict_str, n=1024, m_values=[184, 190, 192])

    assert report_int == report_str


def test_largest_remainder_invariants():
    """T7: Test exact sum and apportionment invariants for largest-remainder."""
    props = [0.1, 0.2, 0.3, 0.4]
    for total in [1, 7, 10, 100, 1024, 2048]:
        counts = largest_remainder_counts(props, total)
        assert sum(counts) == total
        assert len(counts) == len(props)


def test_full_json_report_generation():
    """T8: Verify generate_degree_feasibility_report produces valid parseable JSON."""
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
    """T9: Verify CLI execution via python -m runner."""
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
