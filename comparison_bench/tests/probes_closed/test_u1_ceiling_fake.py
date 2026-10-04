"""Fake-only test for the U1 ceiling probe (Packet F, T-PU02).

Hand-computable 8-row x 2-arm boolean case; zero data contact: reads no M0
JSON, no real file, nothing. Run exactly as:
  .venv/bin/python -m pytest comparison_bench/tests/test_u1_ceiling_fake.py -p no:cacheprovider
"""

from __future__ import annotations

import math
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed.u1_ceiling_probe import (
    count_arm,
    decide,
    gate_paths,
    invert_q,
)

REPO = Path(__file__).resolve().parents[3]

# Hand-built 8-row x 2-arm fake. Arm 197: S=3, D=2 (R=2/3), one undetected
# row excluded from S. Arm 201: S=2, D=0 (R=0).
FAKE_ROWS = [
    {"m": 197, "exact_match": True, "undetected": False, "full10_match": True},
    {"m": 197, "exact_match": True, "undetected": False, "full10_match": False},
    {"m": 197, "exact_match": True, "undetected": False, "full10_match": False},
    {"m": 197, "exact_match": False, "undetected": False, "full10_match": False},
    {"m": 197, "exact_match": True, "undetected": True, "full10_match": False},
    {"m": 201, "exact_match": True, "undetected": False, "full10_match": True},
    {"m": 201, "exact_match": True, "undetected": False, "full10_match": True},
    {"m": 201, "exact_match": False, "undetected": False, "full10_match": False},
]

# 1 - (1/3)^(1/1024), pinned hand constant (both float paths agree to 0.0).
Q_TWO_THIRDS = 0.0010722882508021891


def test_fake_arm_fractions_exact():
    a197 = count_arm(FAKE_ROWS, 197)
    assert (a197["n"], a197["S"], a197["D"], a197["undetected"]) == (5, 3, 2, 1)
    a201 = count_arm(FAKE_ROWS, 201)
    assert (a201["n"], a201["S"], a201["D"], a201["undetected"]) == (3, 2, 0, 0)
    assert a197["S"] / a197["n"] != a197["D"] / a197["S"]  # guard shape only
    assert a197["D"] / a197["S"] == 2 / 3
    assert a201["D"] / a201["S"] == 0.0


def test_fake_q_matches_inversion_to_1e_12():
    r = 2 / 3
    q = invert_q(r)
    via_log = 1.0 - math.exp(math.log1p(-r) / 1024.0)
    assert abs(q - via_log) < 1e-12
    assert abs(q - Q_TWO_THIRDS) < 1e-12
    assert invert_q(0.0) == 0.0
    assert 0.0 < q < r
    with pytest.raises(SystemExit):
        invert_q(1.5)


def test_fake_no_pooling_between_arms():
    a197 = count_arm(FAKE_ROWS, 197)
    a201 = count_arm(FAKE_ROWS, 201)
    assert a197["n"] + a201["n"] == len(FAKE_ROWS) == 8
    assert a197["S"] == 3 and a201["S"] == 2
    per_arm = [{"q": invert_q(a197["D"] / a197["S"]), "q_over_ser": 0.004},
               {"q": invert_q(a201["D"] / a201["S"]), "q_over_ser": 0.0}]
    assert decide(per_arm)["clause"] in ("5.1", "5.2", "5.3")
    assert a197["D"] / a197["S"] != a201["D"] / a201["S"]


def test_fake_path_gate_refuses_before_any_read(tmp_path=None):
    rows = ["workspace/m0_359922a7_1M/rows.json",
            "workspace/m0_642a8fe8_1p5M/rows.json",
            "workspace/m0_b1a9142d_2M/rows.json"]
    sums = ["workspace/m0_359922a7_1M/M0_RESULT_1M.md",
            "workspace/m0_642a8fe8_1p5M/M0_RESULT_1p5M.md",
            "workspace/m0_b1a9142d_2M/M0_RESULT_2M.md"]
    with pytest.raises(SystemExit):
        gate_paths([rows[0], "evil.ttbin", rows[2]], sums, "workspace/u1_probe_x")
    with pytest.raises(SystemExit):
        gate_paths([rows[0], "bundle.npz", rows[2]], sums, "workspace/u1_probe_x")
    with pytest.raises(SystemExit):
        gate_paths(rows, [sums[0], "pairs.parquet", sums[2]],
                   "workspace/u1_probe_x")
    with pytest.raises(SystemExit):
        gate_paths(rows, sums, "workspace/other_x")  # wrong root prefix
    with pytest.raises(SystemExit):
        gate_paths(rows[:2] + ["workspace/elsewhere.json"], sums,
                   "workspace/u1_probe_x")


def test_fake_fresh_pytest_root():
    root = REPO / f"workspace/u1_probe__pytest_{uuid.uuid4().hex[:8]}"
    assert not root.exists()
    root.mkdir(parents=False)
    assert root.is_dir() and list(root.iterdir()) == []
