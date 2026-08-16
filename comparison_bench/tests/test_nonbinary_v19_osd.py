from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v19_osd import gf_rref, solve_with_free, osd_decode


def test_solve_small_system():
    field = GF2mField.create(4)
    # H = [[1,1,0],[0,1,1]] over GF(4), syndrome [a,b] chosen from a known x.
    x = [1, 2, 3]
    H = [[1, 1, 0], [0, 1, 1]]
    s = []
    for row in H:
        acc = 0
        for coeff, val in zip(row, x):
            acc = field.add(acc, field.mul(coeff, val))
        s.append(acc)
    rref, pivots = gf_rref(field, H, s)
    free_cols = [j for j in range(3) if j not in set(pivots)]
    assign = {j: x[j] for j in free_cols}
    sol = solve_with_free(field, rref, pivots, assign, 3)
    assert sol == x


def test_osd_decode_returns_solution():
    field = GF2mField.create(4)
    H = [[1, 1, 0], [0, 1, 1]]
    x = [1, 2, 3]
    s = []
    for row in H:
        acc = 0
        for coeff, val in zip(row, x):
            acc = field.add(acc, field.mul(coeff, val))
        s.append(acc)
    sol = osd_decode(field=field, matrix=H, syndrome=s, e_hat=x)
    assert sol == x
