"""T0/T1 tests for S-5c GF5 runner (synthetic only, no real data)."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s5c_gf5 import (
    priors_of,
)


def test_priors_shape_and_norm():
    from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
        DoubleGauss,
    )
    law = DoubleGauss(20.0, 100.0, 0.01)
    v = np.array([0.0, 100.0, 199.0, 50.0])
    p = priors_of(v, law, 4)
    assert p.shape == (4, 5)
    assert np.allclose(p.sum(axis=1), 1.0)
    assert (p >= 0).all()


def test_symbol_fold_roundtrip():
    e = np.array([-2, -1, 0, 1, 2, 3])
    s = (e % 5).astype(np.int64)
    assert s.tolist() == [3, 4, 0, 1, 2, 3]
    ehat = np.where(s[:5] <= 2, s[:5], s[:5] - 5)
    assert ehat.tolist() == [-2, -1, 0, 1, 2]
