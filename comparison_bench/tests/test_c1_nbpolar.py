"""C1-A4-01: A4 GF(q) Polar 构造/披露/译码 API + T0/T1（OP2 scope）.

只覆盖 OP2 自有模块；不读 D:/Data，不跑 B≥300，临时文件只写
``workspace/c1_op2_<uuid>/``（本文件不落盘，落盘由 runner 测试做）。
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbpolar as P

WS = Path("workspace") / "c1_op2_placeholder_never_written"


# ---------------- T0 ----------------

def test_t0_import_and_constants():
    assert P.SUPPORTED_Q == (3, 5, 7)
    assert P.DEFAULT_LIST_SIZE == 1 and P.SCL_LIST_SIZE == 8
    for name in ("construct", "disclose", "decode", "frozen_set"):
        assert callable(getattr(P, name))


def test_t0_syndrome_bits_exact():
    # ceil(4*log2(3)) = ceil(6.3398) = 7；ceil(2*log2(5)) = ceil(4.6438) = 5
    assert P.syndrome_bits(4, 3) == 7
    assert P.syndrome_bits(2, 5) == 5
    assert P.syndrome_bits(1, 7) == math.ceil(math.log2(7)) == 3


def test_t0_frozen_set_shape_and_determinism():
    f1, i1 = P.frozen_set(32, 16, {"q": 3, "p": 0.05}, seed=11)
    f2, i2 = P.frozen_set(32, 16, {"q": 3, "p": 0.05}, seed=11)
    assert (f1, i1) == (f2, i2)
    assert len(f1) == 16 and len(i1) == 16
    assert set(f1) | set(i1) == set(range(32)) and not (set(f1) & set(i1))
    with pytest.raises(ValueError):
        P.frozen_set(30, 10)  # 非 2 的幂
    with pytest.raises(ValueError):
        P.frozen_set(32, 32)  # k_info 越界


def test_t0_construct_validation():
    with pytest.raises(ValueError):
        P.construct(32, 16, 4)  # q 非素数
    with pytest.raises(ValueError):
        P.construct(32, 16, 9)  # q 非素数
    with pytest.raises(ValueError):
        P.construct(30, 10, 3)  # n 非 2 的幂
    with pytest.raises(ValueError):
        P.construct(32, 0, 3)  # m 越界
    with pytest.raises(ValueError):
        P.construct(32, 32, 3)  # m 越界
    c = P.construct(32, 16, 3, seed=0)
    assert c.k_info == 16 and c.disclosure_bits == P.syndrome_bits(16, 3)
    assert len(c.code_hash) == 16


@pytest.mark.parametrize("q", [3, 5, 7])
def test_t0_noiseless_roundtrip_same_path(q):
    # q=3 先行，5/7 同代码路径：无噪声编解码往返精确成功（固定种子）。
    c = P.construct(32, 16, q, seed=0)
    rng = np.random.default_rng(20261008)
    a = rng.integers(0, q, 32).tolist()
    syn, bits = P.disclose(a, c)
    assert bits == P.syndrome_bits(16, q) and len(syn) == 16
    prior = [1.0] + [0.0] * (q - 1)
    a_hat = P.decode(a, syn, prior, 50, code=c)
    assert a_hat == a


def test_t0_decode_failure_returns_none():
    c = P.construct(8, 4, 3, seed=0)
    rng = np.random.default_rng(1)
    a = rng.integers(0, 3, 8).tolist()
    syn, _ = P.disclose(a, c)
    g = [0.9, 0.05, 0.05]
    assert c.decode(a[:7], syn, g, 50) is None  # 长度错：None，不抛异常
    assert c.decode(a, syn[:3], g, 50) is None  # syndrome 长度错
    assert c.decode(a, syn, [0.5, 0.5], 50) is None  # 先验长度错
    assert P.decode(a, syn, g, 50, code=None) is None  # 缺 code
    assert P.decode(a, syn, g, 50, code=c, list_size=0) is None  # 非法 L


def test_t0_sibling_status_never_raises():
    st = P.sibling_polar_core_status()
    assert isinstance(st, dict) and isinstance(st.get("available"), bool)


# ---------------- T1 ----------------

def test_t1_small_noise_success_nonzero():
    # q=3 小噪声 p≈0.05，N=128 ≤ 256，固定种子：运行无异常且成功块非零。
    n, m, q = 128, 48, 3
    pg = [0.95, 0.025, 0.025]
    code = P.construct(n, m, q, seed=1,
                       channel={"q": q, "p": 0.05}, prior_g=list(pg))
    rng = np.random.default_rng(0)
    ok = 0
    for _ in range(5):
        a = rng.integers(0, q, n).tolist()
        e = rng.choice(q, size=n, p=pg)
        b = ((np.asarray(a) + e) % q).tolist()
        syn, _ = code.disclose(a)
        a_hat = code.decode(b, syn, list(pg), 50)
        assert a_hat is None or len(a_hat) == n
        ok += int(a_hat == a)
    assert ok >= 1


def test_t1_scl8_runs():
    c = P.construct(32, 12, 3, seed=4)
    rng = np.random.default_rng(5)
    pg = [0.95, 0.025, 0.025]
    a = rng.integers(0, 3, 32).tolist()
    e = rng.choice(3, size=32, p=pg)
    b = ((np.asarray(a) + e) % 3).tolist()
    syn, _ = c.disclose(a)
    a_hat = c.decode(b, syn, list(pg), 50, list_size=8)
    assert a_hat is not None and len(a_hat) == 32
