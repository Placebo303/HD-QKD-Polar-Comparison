"""Focused pre-execution tests for M5 (no real-data reads)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m5_realframe import (
    decode_block_msd,
    group_blocks,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
    load_train_table,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (
    build_mixed_point,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
    make_bp_decoder,
)
import functools


def test_group_blocks_sixteen_and_remainder():
    rng = np.random.default_rng(7)
    supers = [(rng.integers(0, 1024, size=1024), rng.integers(0, 1024, size=1024))
              for _ in range(38)]
    blocks, dropped = group_blocks(supers)
    assert len(blocks) == 2 and dropped == 6
    assert blocks[0][0].size == 16384
    assert np.array_equal(blocks[0][0][:1024], supers[0][0])
    assert np.array_equal(blocks[1][1][-1024:], supers[31][1])


def test_decode_block_msd_synthetic_n1024():
    table = load_train_table("T2-1M")
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
        plane_conditional_entropies,
    )

    h = plane_conditional_entropies(table)
    matrices, factories, _, _ = build_mixed_point(1024, h, 160, 32, 64)
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(99)
    pick = rng.choice(nnz.size, size=1024, p=probs)
    alice = rows[pick].astype(np.int64)
    bob = cols[pick].astype(np.int64)
    r = decode_block_msd(alice, bob, model, matrices, factories, 100)
    assert set(r) == {"exact_ok", "undetected", "rescued", "extra", "stages_passed"}
    assert len(r["stages_passed"]) >= 1
    assert r["extra"] == (100 if r["rescued"] else 0)


def test_consistency_band_arithmetic():
    # pre-registered band: PASS iff observed FER <= synthetic Wilson-upper95
    import math

    def wilson_up(k, n, z=1.96):
        p = k / n
        d = 1 + z * z / n
        return min(1.0, (p + z * z / (2 * n)) / d
                   + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d)

    assert abs(wilson_up(0, 300) - 0.012643) < 1e-4
    assert wilson_up(0, 12) > 0.2  # real-frame bands are wide by construction
