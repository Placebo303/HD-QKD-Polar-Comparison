"""T0/T1 tests for the A5 soft-rate tool (synthetic only, no real data)."""

from comparison_bench.src.comparison_bench.formal_ir.msd_a5_soft_rate import (
    cond_pmf_given_fine,
    rate_pair,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    Gauss,
)


def test_fine_symmetry_at_zero_offset():
    pmf = cond_pmf_given_fine(Gauss(25.0), 200.0, 0.0, 100.0)
    assert abs(pmf[1] - pmf[-1]) < 1e-9


def test_soft_never_hurts():
    for bw, mu in ((100.0, 47.0), (200.0, 47.0), (400.0, 47.0), (200.0, 0.0)):
        r = rate_pair(sig=25.0, mu=mu, bw=bw)
        assert r["gain"] >= -1e-9


def test_uniform_phase_limit():
    r = rate_pair(sig=100000.0, mu=0.0, bw=200.0)
    assert r["gain"] < 0.01


def test_b2_crosscheck_mixture():
    r = rate_pair(sig=17.3, mu=47.33, bw=200.0, wide=(17.3, 100.0, 0.0141))
    assert abs(r["R_hard"] - 0.8040) < 0.01
    assert abs(r["R_soft"] - 0.2407) < 0.03
