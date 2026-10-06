"""Focused tests for S-3 u1 probe (synthetic-shaped inputs, no channel data)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (
    GroupMLDecoder,
    spc_matrix,
    split_groups,
)


def test_u1_ladder_group_counts():
    for g, m_exp in ((8, 128), (16, 64), (32, 32)):
        groups = split_groups(1024, g)
        mat = spc_matrix(groups, 1024)
        assert mat.shape[0] == m_exp
        assert sum(len(x) for x in groups) == 1024


def test_u1_exact_ml_single_error():
    groups = split_groups(32, 8)
    mat = spc_matrix(groups, 32)
    Hd = np.asarray(mat.toarray(), dtype=np.uint8)
    rng = np.random.default_rng(9)
    llr = rng.normal(0, 2, size=32)
    truth = (rng.random(32) < 0.5).astype(np.uint8)
    syn = (Hd @ truth) % 2
    base = (llr < 0).astype(np.uint8)
    delta = np.bitwise_xor(syn, (Hd @ base) % 2)
    w = np.abs(llr)
    dec = GroupMLDecoder(groups, "spc", 0.5 - 0.5 * np.tanh(w / 2), 0)
    rec = np.bitwise_xor(base, dec.decode(delta))
    assert bool(np.array_equal((Hd @ rec) % 2, syn))
