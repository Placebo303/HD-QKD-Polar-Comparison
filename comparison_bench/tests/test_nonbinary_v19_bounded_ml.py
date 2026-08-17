import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v19_bounded_ml import bounded_weight_ml_decode


def test_bounded_weight_ml_decode_small_identity():
    field = GF2mField.create(4)
    H = [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 1]]
    x = [1, 2, 3, 1]
    s = list(x)
    # Use a prior that strongly favors the true symbols.
    w = np.full(4, 0.01)
    for v in x:
        w[v] = 0.25
    w = w / w.sum()
    e = bounded_weight_ml_decode(field=field, matrix=H, syndrome=s, w=w, max_weight=4)
    assert e == x
