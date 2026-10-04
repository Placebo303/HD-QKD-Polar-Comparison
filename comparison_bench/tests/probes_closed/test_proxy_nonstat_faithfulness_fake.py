"""Fake-only tests for proxy nonstationary faithfulness (packet P-3).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no data file, no doc JSON, no bundle, nothing. Temporary
directories live under fresh additive workspace/proxy_nonstat__pytest_<uuid8>
roots.
"""

from __future__ import annotations

import math
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import proxy_nonstat_sampler as px


def _fresh_root() -> Path:
    root = Path(f"workspace/proxy_nonstat__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def test_z_hand_sequence():
    # halves [1..6] mean 3.5 var 3.5; [10..15] mean 12.5 var 3.5;
    # SE = sqrt(3.5/6 + 3.5/6), z = 9 / SE.
    x = [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15]
    assert px.compute_z(x) == pytest.approx(9.0 / math.sqrt(7.0 / 6.0))


def test_r1_hand_sequence():
    # alternating 0/10 (n=12): mean 5, lag products -25 x 11, denom 300.
    x = [0, 10] * 6
    assert px.compute_r1(x) == pytest.approx(-11.0 / 12.0)


def test_D_hand_sequence():
    # [10,11,9] x 4: mean 10, sum-sq 8, s^2 = 8/11, D = 8/110.
    x = [10, 11, 9] * 4
    assert px.compute_D(x) == pytest.approx(8.0 / 110.0)


def test_median_aggregation():
    assert px.median_of([3, 1, 2]) == 2.0
    assert px.median_of([1, 2, 3, 4]) == 2.5


def test_cost_block_cap():
    assert px.cost_block_cap(1800.0, 40, 10800.0, 240) == 45.0
    assert px.cost_extrapolation(51.0, 240) == 12240.0


def _quiet():
    return 0.5, 0.01, 0.8


def test_verdict_c1_priority_over_c2_c3():
    # control breaks z, cost also exceeded, flag also true -> C1 wins.
    w, clause = px.decide_word(5.0, 0.01, 0.8,
                               5.0, 0.01, 0.8,
                               px.P_BASE - 0.01, 50.0)
    assert w == "UNFAITHFUL_PROXY_KILL"
    assert "K-C1a" in clause


def test_verdict_c2_priority_over_c3():
    # all quiet control, sensitive drift, cost exceeded + flag true -> C2.
    zc, rc, dc = _quiet()
    w, clause = px.decide_word(zc, rc, dc,
                               5.0, 0.01, 0.8,
                               px.P_BASE - 0.01, 50.0)
    assert w == "STRUCTURALLY_INCOMPLETE_KILL"
    assert "K-C2" in clause


def test_verdict_c3_flag():
    # cost feasible (40/block) but proxy beautifies error scale -> C3.
    zc, rc, dc = _quiet()
    w, clause = px.decide_word(zc, rc, dc,
                               5.0, 0.01, 0.8,
                               px.P_BASE - 0.01, 40.0)
    assert w == "OPTIMISTIC_PROXY_KILL"
    assert "K-C3" in clause


def test_verdict_pass():
    # quiet control, sensitive drift, feasible cost, honest scale -> PASS.
    zc, rc, dc = _quiet()
    w, clause = px.decide_word(zc, rc, dc,
                               5.0, 0.01, 0.8,
                               px.P_BASE, 40.0)
    assert w == "FAITHFUL_AND_COST_FEASIBLE"
    assert "S5.4" in clause


def test_path_gate_refuses_data_paths():
    root = str(_fresh_root())
    for bad in ("workspace/other/x.npz",
                "data/y.ttbin",
                "a/b.parquet",
                f"{root}/rows.json",
                f"{root}/sub/x.npz"):
        with pytest.raises(px.Refusal):
            px.check_input_path(bad, root)
    with pytest.raises(px.Refusal):
        px.check_input_path("/abs/outside/x.json", root)
    px.check_input_path(f"{root}/out.json", root)


def test_root_gate_pattern():
    px.check_root_format("workspace/proxy_nonstat_77e84924")
    for bad in ("results/x", "comparison_bench/outputs_comparison/x",
                "workspace/other_root", "workspace/proxy_nonstat_ZZZ"):
        with pytest.raises(px.Refusal):
            px.check_root_format(bad)


def test_flags_refused_without_both():
    with pytest.raises(px.Refusal):
        px.parse_args(["--root", "workspace/proxy_nonstat_77e84924"])
    with pytest.raises(px.Refusal):
        px.parse_args(["--root", "workspace/proxy_nonstat_77e84924",
                       "--execute-synthetic", "--decode"])
