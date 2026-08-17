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


def test_bounded_weight_ml_decode_max5_small_identity():
    field = GF2mField.create(4)
    H = [[1 if i == j else 0 for j in range(5)] for i in range(5)]
    x = [1, 2, 3, 1, 2]
    s = list(x)
    w = np.full(4, 0.01)
    for v in x:
        w[v] = 0.25
    w = w / w.sum()
    e = bounded_weight_ml_decode(field=field, matrix=H, syndrome=s, w=w, max_weight=5)
    assert e == x


def test_bounded_weight_ml_decode_candidates_max5_includes_true():
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v19_bounded_ml import bounded_weight_ml_decode_candidates
    field = GF2mField.create(4)
    H = [[1 if i == j else 0 for j in range(5)] for i in range(5)]
    x = [1, 2, 3, 1, 2]
    s = list(x)
    w = np.full(4, 0.01)
    for v in x:
        w[v] = 0.25
    w = w / w.sum()
    cands = bounded_weight_ml_decode_candidates(
        field=field, matrix=H, syndrome=s, w=w, max_weight=5, top_k=4)
    assert x in cands
