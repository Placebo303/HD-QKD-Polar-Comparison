"""T0/T1 tests for S-5 tune (synthetic only, no real data)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s5_tune import (
    decode_3,
    gen_blocks,
    p_soft_vec,
    sub_of,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    QA,
    build_ra,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
)


def test_gen_random_b0():
    rng = np.random.default_rng(0)
    law = DoubleGauss(13.0, 100.0, 0.007)
    blks = gen_blocks(rng, 4, 128, law)
    b0s = np.concatenate([b["b0"] for b in blks])
    assert 0.3 < b0s.mean() < 0.7  # random Bob bits (regression: b0=0 hides bugs)
    assert all(len(b["x"]) == 128 for b in blks)


def test_soft_llr_direction():
    law = DoubleGauss(25.0, 100.0, 0.0)
    p = p_soft_vec(np.array([0.0, 100.0, 199.0]), law)
    assert p[0] > 0.4 and p[1] < 0.05 and p[2] > 0.4


def test_decode_3_catches_wide():
    rng = np.random.default_rng(1)
    N = 128
    H3 = build_ra(N, 32, QA, seed=3)
    law = DoubleGauss(13.0, 100.0, 0.007)
    blks = gen_blocks(rng, 4, N, law)
    n = 0
    for blk in blks:
        marked = blk["x"] == 1
        yhat = blk["a1"][marked]  # genie sign (tests third level alone)
        ok, _what = decode_3(H3, blk, yhat, marked)
        n += ok
    assert n >= 3


def test_fullchain_recon_general_b():
    """Regression: full reconstruction must start from b.copy() (not zeros).
    Zero-init scores every nonzero-b block as exact-fail (U=100% artifact)."""
    import numpy as _np
    from comparison_bench.src.comparison_bench.formal_ir.msd_s5_tune import (
        decode_A,
        decode_B,
    )
    rng = _np.random.default_rng(3)
    law = DoubleGauss(13.0, 100.0, 0.007)
    N = 256
    H = build_ra(N, int(N * 0.5), QA, seed=11)
    HB = build_ra(N, int(N * 0.15), QA, seed=12)
    HR = build_ra(N, 8, QA, seed=13)
    curve = [0.02, 0.05, 0.2, 0.5, 0.8, 0.95, 0.98, 0.98]
    blks = gen_blocks(rng, 6, N, law)
    nS = 0
    for blk in blks:
        syn, xa, okA = decode_A(H, blk, 0.06, "soft", law)
        if not okA:
            continue
        yhat, okB, _lb, _r = decode_B(HB, HR, blk, xa, _np.array(curve))
        if not okB:
            continue
        marked = (xa == 1)
        a0hat = (xa ^ blk["b0"]).astype(_np.uint8)
        ahat = blk["b"].copy()
        sgn = (yhat ^ blk["b1"][marked] ^ a0hat[marked]).astype(bool)
        ahat[marked] = _np.where(sgn, (blk["b"][marked] + 1) % 1024,
                                 (blk["b"][marked] - 1) % 1024)
        nS += bool(_np.array_equal(ahat, blk["a"]))
    assert nS > 0


def test_modular_recon_beats_or_patch():
    """Regression: bits0-2 OR-patch ignores borrows crossing bit3 (fails ~12%
    of narrow positions at b&7==0); modular e_est reconstruction is exact for
    |e|<=3. Genie planes isolate the assembly (no decoder involved)."""
    import numpy as _np
    from comparison_bench.src.comparison_bench.formal_ir.msd_s5_tune import (
        gen_blocks,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
        DoubleGauss,
    )
    rng = _np.random.default_rng(11)
    law = DoubleGauss(13.0, 100.0, 0.007)
    blks = gen_blocks(rng, 4, 512, law)
    n_or = 0
    n_mod = 0
    for b in blks:
        narrow = _np.abs(b["e"]) <= 3
        a0 = (b["a"] % 2).astype(_np.uint8)
        a1 = ((b["a"] >> 1) & 1).astype(_np.uint8)
        a2 = ((b["a"] >> 2) & 1).astype(_np.uint8)
        or_patch = (b["b"] & ~0b111) | a0.astype(_np.int64) | \
            (a1.astype(_np.int64) << 1) | (a2.astype(_np.int64) << 2)
        n_or += bool(_np.array_equal(or_patch[narrow], b["a"][narrow]))
        plo = (a0.astype(_np.int64) | (a1.astype(_np.int64) << 1) |
               (a2.astype(_np.int64) << 2))
        blo = (b["b"] & 0b111).astype(_np.int64)
        e_est = (blo - plo) % 8
        e_est = _np.where(e_est <= 3, e_est, e_est - 8)
        n_mod += bool(_np.array_equal(((b["b"] - e_est) % 1024)[narrow], b["a"][narrow]))
    assert n_mod == 4
    assert n_or < 4  # OR-patch demonstrably lossy on borrow positions
