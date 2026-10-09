"""T0/T1 tests for the S-3 soft-decode runner (synthetic only, no real data)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    build_ra,
    decode,
    gen_block,
    llr,
    mcnemar,
    p_of_v,
    rate_of,
    run_cell,
)


def test_ra_shape_and_syndrome():
    H = build_ra(64, 32, 3, seed=7)
    assert H.shape == (32, 64) and H.nnz > 0
    rng = np.random.default_rng(0)
    x = (rng.random(64) < 0.1).astype(np.uint8)
    syn = np.asarray((H @ x) % 2, dtype=np.uint8).ravel()
    assert syn.shape == (32,)


def test_llr_calibration_direction():
    assert p_of_v(10.0, 25.0, 0.0) > p_of_v(100.0, 25.0, 0.0)  # edge vs centre
    assert llr(0.1) > llr(0.4) > 0


def test_mcnemar_extreme():
    assert mcnemar(167, 0) < 1e-30
    assert mcnemar(5, 5) > 0.5


def test_run_cell_synthetic_tiny():
    rng = np.random.default_rng(20261009)
    N = 128
    H = build_ra(N, 64, 3, seed=7)
    HB = build_ra(N, 32, 3, seed=8)
    HR = build_ra(N, 8, 3, seed=9)
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
        synth_blocks,
    )
    blks = synth_blocks(rng, 4, N, 25.0, 0.0, 0.0)
    for arm in ("hard", "soft"):
        r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=0.1,
                     sig=25.0, mu=0.0, p_minus=0.6, arm=arm)
        assert r["S"] + r["F"] + r["U"] == 4
        assert r["FER_CP95"][0] <= r["FER"] <= r["FER_CP95"][1]
        assert len(r["rows"]) == 4


def test_rate_gap_monotone():
    assert rate_of(0.06, 0.08) > rate_of(0.06, 0.18)


def test_exact_full_success_easy_point():
    """Regression: reconstruction mapping must yield S>0 on an easy channel
    (caught inverted b-/+1 mapping that hid all successes in U)."""
    rng = np.random.default_rng(1)
    N = 256
    H = build_ra(N, int(N * 0.4), 5, seed=7)
    HB = build_ra(N, int(N * 0.15), 5, seed=8)
    HR = build_ra(N, 8, 5, seed=9)
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
        synth_blocks,
    )
    blks = synth_blocks(rng, 10, N, 13.0, 0.0, 0.007)
    r = run_cell(H_A=H, H_B=HB, H_R=HR, blocks=blks, p_bar=0.05,
                 sig=13.0, mu=0.0, p_minus=0.6, arm="soft", nproc=1)
    assert r["S"] > 0, r
