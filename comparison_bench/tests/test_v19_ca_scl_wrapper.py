import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.v19_ca_scl_wrapper import V19CA_SCLDecoder
from src.reconciliation.real_polar_sc_rescue import polar_encode_non_systematic


def test_noiseless_scl_decode_random_info():
    n = 256
    n_log = 8
    k = 64
    rng = np.random.default_rng(123)
    info = np.sort(rng.choice(n, size=k, replace=False))
    mask = np.zeros(n, dtype=np.uint8)
    mask[info] = 1
    u = np.zeros(n, dtype=np.int8)
    u[info] = rng.integers(0, 2, size=k, dtype=np.int8)
    x = polar_encode_non_systematic(u, n_log)
    llrs = np.where(x == 0, 50.0, -50.0).astype(np.float32).reshape(1, n)
    dec = V19CA_SCLDecoder()
    out = dec.decode_batch(n, k, 1, mask, llrs)
    assert np.array_equal(out[0], u[info].astype(np.uint8))
