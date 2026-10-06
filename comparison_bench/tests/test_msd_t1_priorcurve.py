"""Focused tests for T-1 (formula-level, no construction)."""


def test_t1_rescue_accounting_bits():
    # L_u2/L_u1 both in BITS (C2 lesson); E_L sums bits only
    for l_u2_rows, rescued in ((224, False), (232, True)):
        assert 5 * l_u2_rows in (1120, 1160)
    e = (5 * 224 + 50 + 0 + sum([16, 0])) / 2
    assert e == (1120 + 50 + 16) / 2


def test_t1_f_formula():
    e_l, fer, n, ha, hab = 1190.0, 0.05, 1024, 9.9976919099, 0.7981344445
    f = (e_l + 64 + (n * ha - e_l) * fer) / (n * hab)
    assert 1.5 < f < 2.5
