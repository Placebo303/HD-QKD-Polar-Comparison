"""Seed-namespace tests for the 37xx rename (implementation-only, T0/T1).

Verifies the frozen 12-seed set, per-subfamily disjointness against the
full integer-domain prior set, the L2 rotation map, and that a D16
collision (4001) fails closed at import time with ValueError.

No decoder, no benchmark, no scientific execution, no production writes.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.formal_ir.nbldpc_l1_degree2_layout as layout  # noqa: E402

MOD_PATH = (SRC / "comparison_bench" / "formal_ir"
            / "nbldpc_l1_degree2_layout.py")

EXPECT_128 = (2026093701, 2026093702, 2026093703,
              2026093704, 2026093705, 2026093706)
EXPECT_256 = (2026093711, 2026093712, 2026093713,
              2026093714, 2026093715, 2026093716)

# (inclusive 4-digit ranges, single 4-digit suffixes) per prior subfamily.
FAMILIES: dict[str, tuple[list[tuple[int, int]], list[int]]] = {
    "R2_graph": ([(2201, 2209)], []),
    "R2_block": ([(2301, 2308), (2311, 2318), (2321, 2328)], []),
    "R3_graph": ([(2401, 2406), (2501, 2506)], []),
    "R3_block": ([(2601, 2612), (2701, 2712)], []),
    "D11_L2": ([(2801, 2806), (2901, 2906)], []),
    "D12_graph": ([(3001, 3006), (3101, 3106)], []),
    "D12_block": ([(3201, 3212), (3301, 3312)], []),
    "D14N": ([(3401, 3406), (3501, 3506), (3601, 3612)], []),
    "D15": ([(3801, 3836), (3901, 3908)], []),
    "D16": ([(4001, 4012), (4101, 4108)], []),
    "D17": ([(4201, 4208)], [4200]),
    "D18": ([(4301, 4308)], []),
    "D19": ([(4401, 4412), (4501, 4508), (4511, 4518)], []),
    "R23": ([(4801, 4816), (4831, 4884), (4885, 4948)], []),
    "G6R7": ([(4601, 4602), (4701, 4708), (4711, 4723)], []),
    "S1": ([(4951, 4952)], []),
    "CLI": ([], [5001, 8001, 9001]),
    "V80": ([(5501, 5560), (5601, 5840), (6401, 6640),
             (7001, 7440), (7501, 7564)],
            [2001, 2011, 6801, 6811]),
    "early": ([(501, 502), (510, 517), (1300, 1315),
               (1601, 1603), (1801, 1805)],
              [1401, 1501, 1727]),
}


def _expand(ranges, singles) -> set[int]:
    out: set[int] = set()
    for lo, hi in ranges:
        out |= {2026090000 + s for s in range(lo, hi + 1)}
    out |= {2026090000 + s for s in singles}
    return out


def _mine() -> set[int]:
    return {s for seeds in layout.GRAPH_SEEDS.values() for s in seeds}


def test_graph_seeds_are_frozen_37xx_twelve():
    assert layout.GRAPH_SEEDS[128] == EXPECT_128
    assert layout.GRAPH_SEEDS[256] == EXPECT_256
    assert len(_mine()) == 12


def test_mine_disjoint_from_each_prior_subfamily():
    mine = _mine()
    for name, (ranges, singles) in FAMILIES.items():
        prior = _expand(ranges, singles)
        assert mine.isdisjoint(prior), name


def test_d16_collision_fails_closed_at_import():
    original = MOD_PATH.read_text()
    tampered = original.replace("2026093701", "2026094001", 1)
    assert tampered != original
    MOD_PATH.write_text(tampered)
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-c",
             "import comparison_bench.formal_ir.nbldpc_l1_degree2_layout"],
            capture_output=True, text=True, env=env, timeout=120)
    finally:
        MOD_PATH.write_text(original)
    assert proc.returncode != 0
    assert "ValueError" in proc.stderr


def test_l2_map_keys_equal_graph_seeds_values_in_d11_l2():
    assert set(layout.L2_GRAPH_SEED_MAP) == _mine()
    allowed = ({2026090000 + s for s in range(2801, 2807)}
               | {2026090000 + s for s in range(2901, 2907)})
    assert set(layout.L2_GRAPH_SEED_MAP.values()) <= allowed
    assert layout.L2_GRAPH_SEED_MAP == {
        2026093701: 2026092801, 2026093702: 2026092802,
        2026093703: 2026092803, 2026093704: 2026092804,
        2026093705: 2026092805, 2026093706: 2026092806,
        2026093711: 2026092901, 2026093712: 2026092902,
        2026093713: 2026092903, 2026093714: 2026092904,
        2026093715: 2026092905, 2026093716: 2026092906,
    }
