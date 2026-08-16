import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.v19_polar_ga import ga_info_mask, ga_llr_means


def test_ga_mask_shape_and_popcount():
    n = 256
    k = 128
    mask = ga_info_mask(0.02, n, k)
    assert mask.shape == (n,)
    assert mask.dtype == np.uint8
    assert int(mask.sum()) == k
    assert set(np.unique(mask)).issubset({0, 1})


def test_ga_means_length_power_two():
    means = ga_llr_means(0.03, 1024)
    assert means.shape == (1024,)
    assert np.all(np.isfinite(means))
