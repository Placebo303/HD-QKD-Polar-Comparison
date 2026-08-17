from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_fftqspa import syndrome_of
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v21_bob_only import (
    decode_bounded4_only,
    run_bob_only_strategy,
)


def _small_setup():
    field = GF2mField.create(4)
    H = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    x = [1, 2, 3, 1]
    w = np.full(4, 0.01)
    for v in x:
        w[v] = 0.25
    w = w / w.sum()
    s_x = list(x)
    # In this identity-code setup, Bob = Alice xor error. Use zero error for simplicity.
    bob = list(x)
    return field, H, bob, s_x, w


def test_decode_bounded4_only_small():
    field, H, bob, s_x, w = _small_setup()
    e = decode_bounded4_only(field=field, matrix=H, bob=bob, s_x=s_x, w=w)
    assert e is not None
    x_hat = [field.add(int(y), int(ee)) for y, ee in zip(bob, e)]
    assert syndrome_of(field, H, x_hat) == list(s_x)


def test_run_s1_small():
    field, H, bob, s_x, w = _small_setup()
    e = run_bob_only_strategy(strategy="S1", field=field, matrix=H,
                              bob=bob, s_x=s_x, w=w)
    assert e is not None


def test_module_source_does_not_contain_alice():
    import ast
    src = Path(__file__).resolve().parents[1] / "src" / "comparison_bench" / "formal_ir" / "nonbinary_v21_bob_only.py"
    text = src.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and node.arg.lower() == "alice":
            raise AssertionError("function parameter named alice found")
        if isinstance(node, ast.Name) and node.id.lower() == "alice":
            raise AssertionError("code references alice")
