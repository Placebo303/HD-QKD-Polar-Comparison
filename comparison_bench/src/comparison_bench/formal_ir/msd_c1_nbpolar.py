"""C-1 A4: GF(q) Polar（OP2, C1_PACKET.md §3.3）.

主路径为本仓库新代码（Arıkan 核 + SC/SCL 译码），不依赖 sibling。
sibling ``polar_core`` 只允许只读交叉核对（见 ``sibling_polar_core_status``），
主编解码路径永不调用它。

方法写死并注明（§3.3 要求）：
- 有限域 F_q 要求 q 为素数（本批 q=3,5,7，即 k=1,2,3 的 2k+1）；q=3 先行，
  q=5/7 走同一代码路径（同一批 T0 往返测试锁定）。
- Arıkan 核 F=[[1,0],[1,1]] 在 F_q 上，G = F^{⊗m}，n=2^m。
- 冻结集方法（写死）：q 元对称初始 Bhattacharyya 系数由 ``prior_g`` 精确计算，
  极化递归采用 BEC 代理 Z- = 2Z−Z²、Z+ = Z²（保守近似，非精确 q 元密度演化，
  特此注明）；可靠度（Z 升序）取信息位；并列用 seed 确定性打破。
- 默认 SC（list_size=1）；SCL（list_size=8）为同一递归的可选分支。
- API 形状与 A3 对齐：``construct / disclose / decode`` 同名，
  前四个位置参数同参序（``decode(b, syndrome, prior_g, max_iter, ...)``），
  ``max_iter`` 保留仅为 API 对齐（Polar SC 无迭代，接受后忽略，特此注明）。

失败语义（与 A3 对齐）：``decode`` 失败返回 None，不抛异常。注意 Polar 无校验子
自检能力：形状合法时的"译码错误码字"只能由 runner 的 tag 复核判定，
本模块仅在输入形状/取值非法、内部异常或缺 code 时返回 None。
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

__all__ = [
    "NBPolarCode",
    "construct",
    "disclose",
    "decode",
    "frozen_set",
    "syndrome_bits",
    "prior_entropy_bits",
    "is_prime",
    "polar_forward",
    "polar_inverse",
    "sibling_polar_core_status",
    "SUPPORTED_Q",
    "DEFAULT_LIST_SIZE",
    "SCL_LIST_SIZE",
]

SUPPORTED_Q = (3, 5, 7)
DEFAULT_LIST_SIZE = 1
SCL_LIST_SIZE = 8
_SIBLING_ROOT = "D:/Code/HD-QKD_Polar_Release"
_LLFLOOR = 1e-300


def is_prime(q: int) -> bool:
    """素数判定（F_q 算术良定的前提）。"""
    q = int(q)
    if q < 2:
        return False
    if q % 2 == 0:
        return q == 2
    r = int(math.isqrt(q))
    for d in range(3, r + 1, 2):
        if q % d == 0:
            return False
    return True


def _require_pow2(n: int) -> int:
    n = int(n)
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError(f"polar block length n must be a power of two >= 2, got {n}")
    return n


def polar_forward(u, q: int) -> list[int]:
    """u @ G (mod q)，G=F^{⊗m} 自然序迭代蝴蝶。"""
    q = int(q)
    x = [int(v) % q for v in list(u)]
    n = len(x)
    _require_pow2(n)
    step = 1
    while step < n:
        for j in range(0, n, 2 * step):
            for i in range(j, j + step):
                x[i] = (x[i] + x[i + step]) % q
        step *= 2
    return x


def polar_inverse(a, q: int) -> list[int]:
    """G^{-1} 变换（Finv=[[1,0],[q−1,1]] 的 Kronecker 幂），为 forward 的逆。"""
    q = int(q)
    y = [int(v) % q for v in list(a)]
    n = len(y)
    _require_pow2(n)
    step = n // 2
    while step >= 1:
        for j in range(0, n, 2 * step):
            for i in range(j, j + step):
                y[i] = (y[i] - y[i + step]) % q
        step //= 2
    return y


def prior_entropy_bits(prior_g) -> float:
    """先验分布 g 的熵（比特/符号）。"""
    g = np.asarray(list(prior_g), dtype=np.float64)
    g = g / g.sum()
    nz = g[g > 0]
    return float(-np.sum(nz * np.log2(nz)))


def _initial_bhattacharyya(prior_g, q: int) -> float:
    """q 元对称信道初始 Bhattacharyya 系数（由 prior_g 精确计算平均）。"""
    g = np.asarray(list(prior_g), dtype=np.float64)
    g = g / g.sum()
    acc = 0.0
    for shift in range(1, q):
        acc += float(np.sum(np.sqrt(g * np.roll(g, shift))))
    return acc / (q - 1)


def frozen_set(n, k_info, channel=None, prior_g=None, seed: int = 0):
    """冻结集（方法写死，见模块 docstring）。

    返回 ``(frozen, info)``，均为升序元组，``len(frozen) == n - k_info``。
    ``prior_g`` 给定时用它算初始 Z；否则由 ``channel`` 的 ``p`` 按 q 元对称
    构造（缺省标称 p=0.10，特此注明）；两者都缺省则用该标称先验。
    ``seed`` 仅用于并列位置的确定性打破（排序键第二关键字）。
    """
    n = _require_pow2(int(n))
    k_info = int(k_info)
    if not (0 < k_info < n):
        raise ValueError(f"require 0 < k_info < n, got k_info={k_info}, n={n}")
    q = 3
    if channel is not None and "q" in dict(channel):
        q = int(dict(channel)["q"])
    if prior_g is not None:
        q = len(list(prior_g))
    if prior_g is None:
        p = 0.10
        if channel is not None and "p" in dict(channel):
            p = float(dict(channel)["p"])
        if not (0.0 <= p < 1.0):
            raise ValueError(f"design p must be in [0,1), got {p}")
        rest = p / (q - 1) if q > 1 else 0.0
        pg = [rest] * q
        pg[0] = 1.0 - p
        prior_g = pg
    z0 = _initial_bhattacharyya(prior_g, q)
    z = np.array([z0], dtype=np.float64)
    while z.shape[0] < n:
        z_minus = 2.0 * z - z * z
        z_plus = z * z
        nxt = np.empty(2 * z.shape[0], dtype=np.float64)
        nxt[0::2] = z_minus
        nxt[1::2] = z_plus
        z = nxt
    rng = np.random.default_rng(int(seed))
    tie = rng.random(n)
    order = list(np.lexsort((tie, z)))
    info = tuple(sorted(order[:k_info]))
    frozen = tuple(sorted(order[k_info:]))
    return frozen, info


def syndrome_bits(m: int, q: int) -> int:
    """披露比特数 ceil(m*log2(q))。m*log2(q) 非整数时向上取整（特此注明）。"""
    return int(math.ceil(int(m) * math.log2(int(q))))


def _code_hash(n: int, m: int, q: int, seed: int, frozen) -> str:
    # packet §3.4 要求 code_hash 列；冻结构造的短标识（注明截断）。
    s = f"C1-A4|n={n}|m={m}|q={q}|seed={seed}|F={list(frozen)}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _combine_minus(l0: np.ndarray, l1: np.ndarray, q: int) -> np.ndarray:
    h = l0.shape[0]
    out = np.zeros((h, q), dtype=np.float64)
    for a in range(q):
        acc = np.zeros(h, dtype=np.float64)
        for b in range(q):
            acc += l0[:, (a + b) % q] * l1[:, b]
        out[:, a] = acc
    s = out.sum(axis=1, keepdims=True)
    out /= np.where(s > 0, s, 1.0)
    return out


def _combine_plus(l0: np.ndarray, l1: np.ndarray, A: np.ndarray, q: int) -> np.ndarray:
    """plus 合并。``A`` 必须是左分支判决重编码后的码字向量 E_h(û_a)
    （h=1 时退化为消息符号本身；h>1 时用消息符号代替是错的，特此注明）。"""
    h = l0.shape[0]
    out = np.zeros((h, q), dtype=np.float64)
    off = np.asarray(A, dtype=np.int64).reshape(-1) % q
    for b in range(q):
        out[:, b] = l0[np.arange(h), (off + b) % q] * l1[:, b]
    s = out.sum(axis=1, keepdims=True)
    out /= np.where(s > 0, s, 1.0)
    return out


def _scl_decode(liks: np.ndarray, frozen: dict, q: int, n: int, L: int):
    """SC/SCL 统一递归（L=1 即 SC）。返回 u_hat 列表。

    注：右分支似然必须用本层 segment 计算；SCL 修剪/分支后路径与输入的归属
    用 ``src`` 下标显式绑定（返回项 ``[metric, seg, dec, src]``，src 为本层
    输入 ``cur`` 的下标），不得复用深层返回的中间矩阵。
    """
    # item = [metric, seg_liks, decisions(全长 list, None 占位)]
    items = [[0.0, liks, [None] * n]]

    def rec(offset: int, size: int, cur: list):
        # 返回 [metric, seg, dec, src]，src 为 cur 的下标。
        if size == 1:
            out = []
            if offset in frozen:
                v = int(frozen[offset])
                for k, (met, seg, dec) in enumerate(cur):
                    dec2 = list(dec)
                    dec2[offset] = v
                    out.append([met + math.log(max(float(seg[0, v]), _LLFLOOR)),
                                seg, dec2, k])
                return out
            for k, (met, seg, dec) in enumerate(cur):
                for v in range(q):
                    dec2 = list(dec)
                    dec2[offset] = v
                    out.append([met + math.log(max(float(seg[0, v]), _LLFLOOR)),
                                seg, dec2, k])
            out.sort(key=lambda t: t[0], reverse=True)
            return out[:L]
        h = size // 2
        left = []
        for met, seg, dec in cur:
            left.append([met, _combine_minus(seg[:h], seg[h:], q), dec])
        left_res = rec(offset, h, left)
        right = []
        right_src = []
        for met, _mseg, dec, k in left_res:
            seg_node = cur[k][1]
            ua = [int(v) % q for v in dec[offset:offset + h]]
            A = ua if h == 1 else polar_forward(ua, q)
            plus = _combine_plus(seg_node[:h], seg_node[h:], A, q)
            right.append([met, plus, dec])
            right_src.append(k)
        right_res = rec(offset + h, h, right)
        return [[met, seg, dec, right_src[j]] for met, seg, dec, j in right_res]

    best = rec(0, n, items)
    best.sort(key=lambda t: t[0], reverse=True)
    return list(best[0][2])


class NBPolarCode:
    """A4 GF(q) Polar 码对象（construct 的返回类型）。"""

    method = "A4-GFq-Polar-SC"

    def __init__(self, n: int, m: int, q: int, seed: int, frozen, info):
        self.n = int(n)
        self.m = int(m)
        self.q = int(q)
        self.seed = int(seed)
        self.frozen = tuple(int(i) for i in frozen)
        self.info = tuple(int(i) for i in info)
        self.k_info = self.n - self.m
        self.disclosure_bits = syndrome_bits(self.m, self.q)
        self.code_hash = _code_hash(self.n, self.m, self.q, self.seed, self.frozen)

    def disclose(self, a_symbols):
        """Alice 披露：u=inv(a)，syndrome=u[F]（冻结序），bits=ceil(m log2 q)。"""
        a = list(a_symbols)
        if len(a) != self.n or any(int(v) < 0 or int(v) >= self.q for v in a):
            raise ValueError("a_symbols length/values mismatch code parameters")
        u = polar_inverse([int(v) % self.q for v in a], self.q)
        syn = [int(u[f]) for f in self.frozen]
        return syn, int(self.disclosure_bits)

    def decode(self, b_symbols, syndrome, prior_g, max_iter: int = 50, list_size: int = 1):
        """Bob 译码。``max_iter`` 仅为 A3-API 对齐保留（SC 无迭代，忽略）。

        成功返回候选 ``a_hat`` 列表；失败（形状/取值非法、缺失、内部异常）
        返回 None，不抛异常。注意：形状合法但码字错误的情况本模块无法自检，
        由 runner 的 tag 复核判定（packet §3.2/§3.4）。
        """
        try:
            return self._decode_inner(b_symbols, syndrome, prior_g, list_size=list_size)
        except Exception:
            return None

    def _decode_inner(self, b_symbols, syndrome, prior_g, list_size: int = 1):
        b = list(b_symbols)
        syn = list(syndrome)
        g = list(prior_g)
        if len(b) != self.n or len(syn) != self.m or len(g) != self.q:
            return None
        if any(int(v) < 0 or int(v) >= self.q for v in b + syn):
            return None
        gf = np.asarray(g, dtype=np.float64)
        if np.any(gf < 0) or float(gf.sum()) <= 0:
            return None
        gf = gf / float(gf.sum())
        L = int(list_size)
        if L < 1 or L > 32:
            return None
        bi = np.asarray([int(v) % self.q for v in b], dtype=np.int64)
        liks = np.zeros((self.n, self.q), dtype=np.float64)
        for x in range(self.q):
            liks[:, x] = gf[(bi - x) % self.q]
        s = liks.sum(axis=1, keepdims=True)
        liks /= np.where(s > 0, s, 1.0)
        frozen = {int(f): int(v) % self.q for f, v in zip(self.frozen, syn)}
        u_hat = _scl_decode(liks, frozen, self.q, self.n, L)
        return [int(v) % self.q for v in polar_forward(u_hat, self.q)]


def construct(n, m, q, seed: int = 0, *, frozen=None, channel=None, prior_g=None) -> NBPolarCode:
    """构造 A4 码。``m`` = 冻结符号数（披露符号数），k_info = n−m。

    ``frozen`` 未给定时按 ``frozen_set(n, n−m, channel, prior_g, seed)`` 计算；
    ``channel`` 可携带 ``q``（无则用 ``q`` 参数，q=3 先行默认值）。
    非素数 q、非 2 的幂 n、m 越界时抛 ValueError（构造期参数错误，非译码失败）。
    """
    n = _require_pow2(int(n))
    m = int(m)
    q = int(q)
    if not is_prime(q):
        raise ValueError(f"q must be prime for F_q arithmetic, got {q}")
    if q not in SUPPORTED_Q:
        raise ValueError(f"this batch supports q in {SUPPORTED_Q}, got {q}")
    if not (0 < m < n):
        raise ValueError(f"require 0 < m < n, got m={m}, n={n}")
    if frozen is None:
        ch = dict(channel) if channel is not None else {}
        ch.setdefault("q", q)
        frozen, info = frozen_set(n, n - m, ch, prior_g, seed=int(seed))
    else:
        frozen = tuple(sorted(int(i) for i in frozen))
        if len(frozen) != m or any(i < 0 or i >= n for i in frozen):
            raise ValueError("frozen set length/range mismatch")
        info = tuple(sorted(set(range(n)) - set(frozen)))
    return NBPolarCode(n, m, q, int(seed), frozen, info)


def disclose(a_symbols, code: NBPolarCode):
    """模块级 disclose（首参 a_symbols，与 A3 同参序；code 为本码对象）。"""
    return code.disclose(a_symbols)


def decode(b_symbols, syndrome, prior_g, max_iter: int = 50, code=None, list_size: int = 1):
    """模块级 decode（前四参 b/syndrome/prior_g/max_iter 与 A3 同参序）。

    ``code`` 缺失时无法译码，返回 None（不抛异常）。
    """
    if code is None:
        return None
    return code.decode(b_symbols, syndrome, prior_g, max_iter, list_size=list_size)


def sibling_polar_core_status() -> dict:
    """sibling polar_core 只读可用性查询（交叉核对用，主路径永不调用）。

    缺失返回 ``available=False``（不断言失败、不抛异常）。
    """
    import importlib
    import sys

    try:
        if _SIBLING_ROOT not in sys.path:
            sys.path.insert(0, _SIBLING_ROOT)
        mod = importlib.import_module("low_dim_opt.core.polar_core")
        return {"available": True, "detail": f"sibling module: {getattr(mod, '__name__', '?')}"}
    except Exception as exc:
        return {"available": False, "detail": f"{type(exc).__name__}: {exc}"}
