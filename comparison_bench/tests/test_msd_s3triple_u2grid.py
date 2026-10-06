"""Focused tests for S-3''' (no construction; formula-level)."""

import numpy as np


def test_nested_rescue_accounting():
    # C2 lesson: rescue disclosure = ACTUAL appended rows x 5, never (208-m)x5
    for m_base, n_res, blocks in ((184, 100, 100), (192, 92, 100), (200, 53, 100)):
        e_u2 = 5 * m_base + (m_base + 8 - m_base) * 5 * n_res / blocks
        assert e_u2 == 5 * m_base + 40 * n_res / blocks
    assert 5 * 184 + 40 * 100 / 100 == 960.0
    assert 5 * 192 + 40 * 92 / 100 == 996.8


def test_full_symbol_f_formula():
    e_l, fer, n, ha, hab = 1090.0, 0.05, 1024, 9.9976919099, 0.7981344445
    f = (e_l + 64 + (n * ha - e_l) * fer) / (n * hab)
    assert abs(f - 1.972) < 0.005


def test_triples_nesting_rule():
    triples = [(r, c, 1) for r in range(248) for c in (r % 7, (r + 1) % 7)]
    for m_base in (184, 192, 200):
        base = [(r, c, v) for r, c, v in triples if r < m_base]
        ext = [(r, c, v) for r, c, v in triples if m_base <= r < m_base + 8]
        assert max(r for r, _, _ in base) == m_base - 1
        assert len(ext) == 8 * 2
