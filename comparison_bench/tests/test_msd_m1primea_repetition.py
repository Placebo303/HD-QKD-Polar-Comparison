"""Focused tests for M1'a group codes: exact-ML vs brute force."""

import itertools

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (
    GroupMLDecoder,
    ml_repetition_group,
    ml_spc_group,
    repetition_matrix,
    spc_matrix,
    split_groups,
)


def test_split_groups_covers_all_bits():
    groups = split_groups(1024, 9)
    assert sum(len(g) for g in groups) == 1024
    assert np.array_equal(np.sort(np.concatenate(groups)), np.arange(1024))
    assert len(groups) == 1024 // 9  # tail merged


def test_repetition_codewords_have_zero_syndrome():
    groups = split_groups(24, 5)
    h = repetition_matrix(groups, 24)
    assert h.shape == (24 - len(groups), 24)
    rng = np.random.default_rng(3)
    for _ in range(5):
        cw = np.zeros(24, dtype=np.uint8)
        for g in groups:
            cw[g] = rng.integers(2)
        syn = (np.asarray(h.toarray(), dtype=np.uint8) @ cw) % 2
        assert np.array_equal(syn, np.zeros(h.shape[0], dtype=np.uint8))


def test_spc_codewords_have_zero_syndrome():
    groups = split_groups(64, 32)
    h = spc_matrix(groups, 64)
    assert h.shape == (2, 64)
    cw = np.zeros(64, dtype=np.uint8)
    cw[0] = cw[1] = 1  # even parity in group 0
    syn = (np.asarray(h.toarray(), dtype=np.uint8) @ cw) % 2
    assert np.array_equal(syn, np.zeros(h.shape[0], dtype=np.uint8))


def _brute_rep(w, delta):
    best = None
    for bits in itertools.product((0, 1), repeat=w.size):
        e = np.asarray(bits, dtype=np.uint8)
        if any((e[i] ^ e[i + 1]) != delta[i] for i in range(w.size - 1)):
            continue
        cost = float(np.sum(w[e == 1]))
        if best is None or cost < best[0]:
            best = (cost, e)
    assert best is not None
    return best[1]


def test_ml_repetition_matches_brute_force():
    rng = np.random.default_rng(11)
    for _ in range(30):
        g = int(rng.integers(2, 9))
        w = rng.uniform(-2, 5, size=g)
        delta = (rng.random(g - 1) < 0.5).astype(np.uint8)
        got = ml_repetition_group(w, delta)
        exp = _brute_rep(w, delta)
        assert float(np.sum(w[got == 1])) == float(np.sum(w[exp == 1]))


def _brute_spc(w, parity):
    best = None
    for bits in itertools.product((0, 1), repeat=w.size):
        e = np.asarray(bits, dtype=np.uint8)
        if int(np.sum(e)) % 2 != parity:
            continue
        cost = float(np.sum(w[e == 1]))
        if best is None or cost < best[0]:
            best = (cost, e)
    assert best is not None
    return best[1]


def test_ml_spc_matches_brute_force():
    rng = np.random.default_rng(13)
    for _ in range(30):
        g = int(rng.integers(2, 9))
        w = rng.uniform(-2, 5, size=g)
        for parity in (0, 1):
            got = ml_spc_group(w, parity)
            exp = _brute_spc(w, parity)
            assert float(np.sum(w[got == 1])) == float(np.sum(w[exp == 1]))


def test_group_decoder_end_to_end_tiny():
    groups = [np.array([0, 1, 2]), np.array([3, 4])]
    kinds = [("repetition", 0), ("spc", 2)]
    row = 0
    for kind, _ in kinds:
        pass
    dec = GroupMLDecoder([groups[0]], "repetition", np.full(5, 0.1), 0)
    # truth 000, error on bit 1 -> delta = [1,1]
    e = dec.decode(np.array([1, 1], dtype=np.uint8))
    assert np.array_equal(e[:3], [0, 1, 0])
    dec2 = GroupMLDecoder([np.array([3, 4])], "spc", np.array([0.1, 0.1, 0.1, 0.4, 0.1]), 0)
    e2 = dec2.decode(np.array([1], dtype=np.uint8))
    assert int(np.sum(e2[3:])) == 1  # single flip restores parity
