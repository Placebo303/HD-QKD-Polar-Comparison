"""Focused tests for M4 NB-marginal arm: bundle exactness + E[L] accounting."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (
    derive_bundle,
    summarize_nbm,
)


def _toy_counts():
    rng = np.random.default_rng(41)
    t = np.zeros((1024, 1024))
    for a in range(0, 1024, 7):
        for b in range(0, 1024, 11):
            t[a, b] = float(rng.integers(1, 9))
    return t


def test_bundle_reproduces_joint_exactly():
    t = _toy_counts()
    b = derive_bundle(t)
    assert b["g1"].shape == (32, 1024) and b["g2"].shape == (32, 32, 1024)
    assert abs(b["p_b"].sum() - 1.0) < 1e-12
    joint = t / t.sum()
    recon = np.zeros_like(joint)
    for a in range(1024):
        u1, u2 = (a >> 5) & 31, a & 31
        recon[a, :] = b["p_b"] * b["g1"][u1, :] * b["g2"][u1, u2, :]
    sup = joint > 0
    assert np.allclose(recon[sup], joint[sup], rtol=1e-9, atol=1e-15)
    # g2 rows over u2 sum to 0/1 (conditional or unsupported-zero)
    s = b["g2"].sum(axis=1)
    assert bool(((s == 0) | (abs(s - 1) < 1e-9)).all())


def test_nbm_expected_leak_formula():
    pts = [{"source": "S", "arm": "P1S1-R1", "N": 1024, "blocks": 100,
            "failures": 5, "undetected": 0, "n_rescue": 20, "u1_mm_total": 3,
            "wall_s": 600.0, "s_per_block": 6.0, "backend": "nb-marginal-P1",
            "seed": 1, "workers": 12}]
    scalars = {"S": {"H_A": 10.0, "H_AB": 0.8}}
    r = summarize_nbm(pts, scalars)[0]
    assert abs(r["E_L"] - (1000 + 40 * 0.2)) < 1e-9
    fer = 0.05
    denom = 1024 * 0.8
    kept = 1024 * 10.0 - r["E_L"]
    assert abs(r["f_expected"] - (r["E_L"] + 64 + kept * fer) / denom) < 1e-9
