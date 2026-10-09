"""T0/T1 tests for the S-4d rerun (synthetic only, no real data)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s4d_rerun import (
    aggregate,
    block_2B,
    sub_of,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    QA,
    build_ra,
    synth_blocks,
)


def test_sub_of_bins():
    v = np.array([0.0, 24.9, 25.0, 199.9])
    assert sub_of(v).tolist() == [0, 0, 1, 7]


def test_block_2B_dual_arm_shapes():
    rng = np.random.default_rng(0)
    N = 128
    H = build_ra(N, 64, QA, seed=7)
    HB = build_ra(N, 32, QA, seed=8)
    HR = build_ra(N, 8, QA, seed=9)
    blks = synth_blocks(rng, 3, N, 13.0, 0.0, 0.007)
    curve = [0.02, 0.05, 0.2, 0.5, 0.8, 0.95, 0.98, 0.98]
    ctx = {"p_bar": 0.06, "sig": 13.0, "w": 0.007, "curve": curve}
    n = 0
    for blk in blks:
        r = block_2B(H, HB, HR, blk, ctx, "soft")
        assert set(r["arms"]) == {"plain", "fixed"}
        assert r["arms"]["plain"]["L_B"] == r["mk"]
        n += 1
    assert n == 3


def test_random_b0_levelB_exact():
    """Regression for the xa-as-a0 bug: with RANDOM Bob bits (not zeros),
    level-B priors + reconstruction must use a0hat=xa^b0. Old code (xa as a0)
    flips ~50% of prior signs and fails exact systematically; fixed code must
    show S>0 on this easy point (R=0.5 below 1-h2(0.06)=0.67 capacity)."""
    rng = np.random.default_rng(7)
    N = 256
    H = build_ra(N, int(N * 0.5), QA, seed=7)
    HB = build_ra(N, int(N * 0.2), QA, seed=8)
    HR = build_ra(N, 8, QA, seed=9)
    curve = [0.02, 0.05, 0.2, 0.5, 0.8, 0.95, 0.98, 0.98]
    nS = 0
    for _ in range(6):
        v = rng.uniform(0.0, 200, size=N)
        sub = np.minimum((v // 25).astype(int), 7)
        mk = rng.random(N) < 0.06
        sgn = (rng.random(N) < np.array(curve)[sub]).astype(np.uint8)
        x = np.zeros(N, dtype=np.uint8)
        x[mk] = 1
        b0 = rng.integers(0, 2, size=N).astype(np.uint8)
        b1 = rng.integers(0, 2, size=N).astype(np.uint8)
        a0 = (x ^ b0).astype(np.uint8)
        a1 = (b1 ^ a0 ^ sgn).astype(np.uint8)
        aa = np.zeros(N, dtype=np.int64)
        aa[mk] = np.where(sgn[mk] == 1, 1, 1023)
        blk = {"x": x, "b0": b0, "a1": a1, "b1": b1, "v": v,
               "a": aa, "b": np.zeros(N, dtype=np.int64)}
        r = block_2B(H, HB, HR, blk,
                     {"p_bar": 0.06, "sig": 13.0, "w": 0.007, "curve": curve},
                     "soft")
        fx = r["arms"]["fixed"]
        if r["okA"] and fx["ok"] and fx.get("exact", False):
            nS += 1
    assert nS > 0


def test_aggregate_counts_close():
    items = [
        {"okA": True, "T_tot": 0.1, "mA": 64,
         "arms": {"plain": {"ok": True, "L_B": 10, "L_R": 0, "exact": True},
                  "fixed": {"ok": True, "L_B": 64, "L_R": 0, "exact": True}}},
        {"okA": False, "T_tot": 0.1, "mA": 64,
         "arms": {"plain": {"ok": False}, "fixed": {"ok": False}}},
    ]
    c = aggregate(items, "soft", "plain", 128, 0.8, 0.25)
    assert (c["S"], c["F"], c["U"]) == (1, 1, 0)
    assert c["L_tot"] == 64 + 10
    assert c["f_ref"] == round(74 / (2 * 128 * 0.25), 4)
