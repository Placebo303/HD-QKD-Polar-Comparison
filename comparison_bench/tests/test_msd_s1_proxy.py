"""Focused tests for S-1 proxy (no ttbin reads, no real data)."""

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (
    _decode_msd_block,
    counts_of,
    load_tier,
)


def test_counts_halves_partition():
    rng = np.random.default_rng(3)
    n = 5000
    a = rng.integers(0, 1024, size=n)
    b = rng.integers(0, 1024, size=n)
    f = np.sort(rng.integers(0, 10000, size=n))
    mid = (f.min() + f.max()) // 2
    ta = counts_of(a[f <= mid], b[f <= mid])
    tb = counts_of(a[f > mid], b[f > mid])
    assert ta.sum() + tb.sum() == n
    assert ta.shape == (1024, 1024)
    # halves are different objects with different mass (R10 separation shape)
    assert not np.array_equal(ta, tb)


def test_load_tier_fail_closed():
    from pathlib import Path

    try:
        load_tier(Path("no_such_dir_xyz_123"), "T2-1M", "half_a")
    except (FileNotFoundError, OSError):
        pass
    else:
        raise AssertionError("expected fail-closed on missing tier files")


def test_decode_block_valid_wrong_tracking():
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
        load_train_table,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (
        build_mixed_point,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
        plane_conditional_entropies,
    )

    table = load_train_table("T2-1M")
    model = build_conditional_prior_model(table, encoding="NATURAL", order="LSB_FIRST")
    h = plane_conditional_entropies(table)
    matrices, factories, _, _ = build_mixed_point(1024, h, 160, 32, 64)
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(11)
    pick = rng.choice(nnz.size, size=1024, p=probs)
    alice = rows[pick].astype(np.int64)
    bob = cols[pick].astype(np.int64)
    r = _decode_msd_block(alice, bob, model, matrices, factories, 100, None)
    assert set(r) >= {"exact_ok", "undetected", "rescued", "extra",
                      "stages_passed", "valid_wrong_stages", "plane1_failed"}
    assert isinstance(r["valid_wrong_stages"], int) and r["valid_wrong_stages"] >= 0
    assert isinstance(r["plane1_failed"], bool)
    # cross-check: valid-wrong implies syndrome pass somewhere mismatched;
    # exact_ok False with all-passed implies undetected True
    if all(r["stages_passed"]) and len(r["stages_passed"]) == 10:
        assert r["undetected"] == (not r["exact_ok"])
