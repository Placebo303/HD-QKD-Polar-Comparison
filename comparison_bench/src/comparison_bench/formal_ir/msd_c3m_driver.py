"""C-3 M 波驱动（OP-M2, EXPLORE 合成-only）.

冻结依据（逐字遵守）: ``docs/research_cycles/C-BATCH/C3_MPACKET.md``
(2026-10-08) + 背景 ``C_BATCH_AMEND.md`` (M2/M4). Track: EXPLORE.
合成校准信道 only；不读原始数据（零 ``D:/Data`` 访问）；不跑真实解码；
不做科学判定（只报最优 N/净密钥/同时间分层结果；排序效力、C-0 前缀稳定性、
C-5 真实矩阵均不在本包声称）.

OP-M2 写作用域（包 §5）: 本文件 + ``tests/test_c3m_driver.py`` +
机器根 ``workspace/c3_mtune/mt_20261008/`` + 单一日志
``docs/research_cycles/C-BATCH/C3_MLOG.md`` (OP-M2 唯一写者).
OP-M1 文件（``msd_c3m_a1a2.py`` / ``test_c3m_a1a2.py`` /
``mt_a1a2_*`` 前缀根）不在本文件写作用域，互不覆盖.

冻结实现要点（包 §2/§4）:
1. A3: QSPA ``max_iter=300`` 冻结单值（用户区间 200–500 内；本驱动唯一
   effort 值，无低 cap 混杂）.
2. A4: 以列表深度为 effort（SC ``list_size=1`` + SCL8 ``list_size=8``
   双变体保留）.
3. ``kept = N·H_A_op`` /成功块（F1→10, F2→9, F3→11；驱动传入
   ``net_of_cell`` 的 ``kept_bits`` 参数；``net_of_cell`` 原样复用）.
4. 码率规则只读引用：``gap_nb`` 表与 M 锚点映射一律取自
   ``msd_c3_bakeoff``（``compute_rate`` / ``GAP_NB`` / ``M_LADDER`` /
   ``ANCHOR_N``），本驱动不重写 R 公式、不重建 gap 表（别名恒等，
   测试锁定 ``is`` 关系）.
5. TAG=64；ROW_KEYS + hash 逐块落盘；B=300；种子冻结 20261009.
6. 无 per-block 超时（一律跑到译码 verdict；超时参数不存在于本驱动）；
   T_dec 逐块记录，汇总单列 p50/p95/max；overtime-risk 只用于调度标记
   （探针外推超格预算则零块 short；墙钟撞墙则 short，均如实）.
7. 网格 A3/A4: F1/F2 × 6N + F3 × {1024, 4096} exploratory；
   A6: F1/F2 × {1024, 4096, 16384}.
8. A6 合成桥（M4，最高风险项）: NB-GF32 超帧机制 + 由 (p*, pm*) 拟合的
   差分 bundle，喂合成校准三值对；T0/T1 桥过不了即返回 BLOCKED
   （失败命令 + traceback + 已试补救 + 需主线程的一个决定），
   不得无声降级为 stub.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as RU
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbldpc as A3M
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbpolar as A4M
from comparison_bench.src.comparison_bench.formal_ir import msd_c3_bakeoff as C3R

__all__ = [
    "TAG", "B_FULL", "SEED_M", "A3_MAX_ITER", "A4_VARIANTS",
    "H_A_OP", "D_OF", "GRID_N6", "GRID_F3", "A6_NS",
    "GAP_NB", "M_LADDER", "ANCHOR_N", "C_TOTAL_PLAN",
    "MLOG_PATH", "NO_TIMEOUT",
    "rate_of", "family_prior", "kept_of",
    "run_a3_cell", "run_a4_cell",
    "a6_fit_bundle", "a6_bridge_t0", "a6_bridge_t1", "run_a6_cell",
    "select_m_anchor", "run_grid", "build_tables", "recount_grid",
    "append_mlog", "main",
]

TAG = 64
assert RU.TAG_BITS == 64, "runner TAG_BITS must be 64 (M frozen TAG=64)"
B_FULL = 300
SEED_M = 20261009
A3_MAX_ITER = 300
assert 200 <= A3_MAX_ITER <= 500, "A3 max_iter must stay in user interval 200-500"
A4_VARIANTS = {"SC": 1, "SCL8": 8}
# H_A_op = log2(d) 均匀帧假设（包 §1；G-5 T2-1M H_A=9.9977 自洽注记）.
H_A_OP = {"F1": 10.0, "F2": 9.0, "F3": 11.0}
D_OF = {"F1": 1024, "F2": 512, "F3": 2048}
GRID_N6 = (1024, 2048, 4096, 8192, 16384, 32768)
GRID_F3 = (1024, 4096)
A6_NS = (1024, 4096, 16384)
# 码率规则只读引用（别名恒等；本驱动无自有 gap 表 / R 公式 / M 标度）.
GAP_NB = C3R.GAP_NB
M_LADDER = C3R.M_LADDER
ANCHOR_N = C3R.ANCHOR_N
C_TOTAL_PLAN = C3R.C_TOTAL_PLAN
MLOG_PATH = Path("docs/research_cycles/C-BATCH/C3_MLOG.md")
# 无 per-block 超时：本驱动不存在任何超时参数；此旗为审计哨兵.
NO_TIMEOUT = True
BUDGET_S = 6 * 3600
CELL_BUDGET_S = 1800
SHARD = 30
A6_Q = 32
A6_BASE_N = 1024
# A6 冻结合成选择：v28 最大 m2 源（"2M", m2=202）为合成上限披露口径.
A6_SOURCE = "2M"


def _now() -> str:
    return _dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")


# ---------------- 冻结输入（只读引用 + M 口径） ----------------

def rate_of(wp: str, N: int, M: float) -> dict:
    """M 波码率（只读引用 bakeoff 冻结函数；高维臂；不另立公式）."""
    spec = C3R.WORKPOINTS[wp]
    return C3R.compute_rate(family="nb", p_op=spec["p"], H_q=spec["H_q"],
                            q=spec["q"], N=int(N), M=float(M))


def family_prior(wp: str):
    """该工作点的 q 元先验（复用 bakeoff 约定；F3 经 cond_dist 残差序）."""
    return C3R.channel_prior(wp)


def kept_of(wp: str, N: int) -> float:
    """M 波统一 kept 口径：kept = N·H_A_op（包 §1）."""
    return float(int(N) * H_A_OP[wp])


def _frozen_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _read_rows_tolerant(path: Path) -> tuple[list[dict], int]:
    """读块行；撕裂尾（kill 残留半行）跳过并计数 n_torn（续跑自动覆盖该 block）."""
    rows: list[dict] = []
    torn = 0
    if not path.exists():
        return rows, torn
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                torn += 1
    return rows, torn


def _jsonl_count(path: Path) -> int:
    # 只计可解析行（撕裂尾不占 block 位，续跑覆盖该 block）.
    rows, _ = _read_rows_tolerant(path)
    return len(rows)


def _append_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _count_success(path: Path) -> tuple[int, int]:
    rows, _ = _read_rows_tolerant(path)
    return len(rows), sum(int(r.get("ver", 0)) for r in rows)


def _tstats(t_list: list[float]) -> dict:
    if not t_list:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0, "total": 0.0}
    arr = np.asarray(t_list, dtype=float)
    return {"p50": float(np.median(arr)),
            "p95": float(np.percentile(arr, 95)),
            "max": float(np.max(arr)),
            "total": float(np.sum(arr))}


def _cell_net(*, kept: float, lec_bits: float, B: int, succ: int,
              N: int, C_total: float, h_op: float, i_op) -> dict:
    return RU.net_of_cell(
        kept_bits=kept, L_EC_bits=float(lec_bits), tag_bits=TAG,
        n_fail=B - succ, n_blocks=B, C_total=float(C_total), N=int(N),
        n_undetected=0, h_op=h_op, I_op=i_op)


# ---------------- A3 执行循环（QSPA max_iter=300 冻结单值） ----------------

def run_a3_cell(wp: str, N: int, M: float, rr: dict, B: int,
                seed: int, out: Path) -> dict:
    """A3 执行循环：RNG q 元抽样 → disclose → QSPA(300) → tag 复核 → 落盘.

    无 per-block 超时：decode 一律跑到 verdict（None 或精确 syndrome 匹配）.
    m 由冻结规则显式算出（调用方 ``rr``），kept 由驱动按 N·H_A_op 传入汇总.
    """
    assert A3_MAX_ITER == 300
    spec = C3R.WORKPOINTS[wp]
    q = spec["q"]
    g = family_prior(wp)
    N, m, K = int(N), int(rr["m"]), int(rr["K"])
    try:
        code = A3M.construct(N, m, q, seed)
    except Exception as exc:
        return {"method": "A3", "variant": "", "WP": wp, "N": N, "M": M,
                "B": B, "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": 0, "success": 0, "net": None}
    code_hash = _frozen_hash(
        f"M-A3|n={N}|m={m}|q={q}|seed={seed}|H={code.H.tobytes().hex()[:256]}")
    frozen_hash = _frozen_hash(
        f"M-A3-H|n={N}|m={m}|q={q}|seed={seed}|H={code.H.tobytes().hex()}")
    kept = kept_of(wp, N)
    lec = int(math.ceil(m * math.log2(q)))
    Hc = A4M.prior_entropy_bits(g)
    t_list: list[float] = []
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        a = rng.integers(0, q, N).tolist()
        e = rng.choice(q, size=N, p=np.asarray(g) / sum(g))
        bb = ((np.asarray(a) + np.asarray(e)) % q).tolist()
        syn, _lec = A3M.disclose(code, a)
        t0 = time.perf_counter()
        # 冻结单值 300；无超时包装，跑到 verdict.
        a_hat = A3M.decode(code, bb, syn, list(g), A3_MAX_ITER)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = a_hat is not None and list(np.asarray(a_hat).tolist()) == list(a)
        _append_rows(out, [{
            "method": "A3", "variant": "", "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept) if good else 0.0,
            "L_EC": int(_lec), "tag": TAG if good else 0,
            "T_dec": float(t_dec), "code_hash": code_hash,
            "frozen_hash": frozen_hash, "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": rr["R"], "m": m, "K": K,
            "max_iter": A3_MAX_ITER}])
    _n_rows, succ = _count_success(out)
    C_cell = max(float(C_TOTAL_PLAN), float(B * N))
    net = _cell_net(kept=kept, lec_bits=lec, B=B, succ=succ, N=N,
                    C_total=C_cell, h_op=H_A_OP[wp],
                    i_op=math.log2(q) - Hc)
    ts = _tstats(t_list)
    return {"method": "A3", "variant": "", "WP": wp, "N": N, "M": M,
            "B": B, "rows": B, "success": succ, "undetected": 0,
            "status": "ok", "detail": "",
            "T_p50": ts["p50"], "T_p95": ts["p95"], "T_max": ts["max"],
            "total_T_dec": ts["total"],
            "code_hash": code_hash, "frozen_hash": frozen_hash,
            "lec_bits": lec, "kept": kept, "C_total": C_cell,
            "net": net, "max_iter": A3_MAX_ITER}


# ---------------- A4 执行循环（SC + SCL8 双变体） ----------------

def run_a4_cell(wp: str, N: int, M: float, rr: dict, B: int,
                seed: int, out: Path, *, variant: str) -> dict:
    """A4 执行循环：effort knob 为列表深度（SC=1, SCL8=8）；无 per-block 超时."""
    if variant not in A4_VARIANTS:
        raise ValueError(f"unknown A4 variant {variant!r}")
    L = int(A4_VARIANTS[variant])
    spec = C3R.WORKPOINTS[wp]
    q = spec["q"]
    g = family_prior(wp)
    N, m, K = int(N), int(rr["m"]), int(rr["K"])
    if N < 2 or (N & (N - 1)) != 0:
        return {"method": "A4", "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "infeasible",
                "detail": f"A4 requires N a power of two >= 2, got {N}",
                "rows": 0, "success": 0, "net": None}
    chf = {"k": spec.get("k"), "q": q, "p": spec["p"],
           "p_minus": spec.get("p_minus"), "m": m, "R": rr["R"]}
    try:
        code = A4M.construct(N, m, q, seed, channel=chf, prior_g=list(g))
    except Exception as exc:
        return {"method": "A4", "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": 0, "success": 0, "net": None}
    frozen_hash = _frozen_hash(f"M-A4|F={list(code.frozen)}|L={L}")
    kept = kept_of(wp, N)
    Hc = A4M.prior_entropy_bits(g)
    t_list: list[float] = []
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        a = rng.integers(0, q, N).tolist()
        e = rng.choice(q, size=N, p=np.asarray(g) / sum(g))
        bb = ((np.asarray(a) + np.asarray(e)) % q).tolist()
        syn, lec = code.disclose(a)
        t0 = time.perf_counter()
        # Polar SC 无迭代；max_iter 仅 API 对齐；无超时包装，跑到 verdict.
        a_hat = code.decode(bb, syn, list(g), 50, list_size=L)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = a_hat is not None and list(a_hat) == list(a)
        _append_rows(out, [{
            "method": "A4", "variant": variant, "list_size": L,
            "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept) if good else 0.0,
            "L_EC": int(lec), "tag": TAG if good else 0,
            "T_dec": float(t_dec), "code_hash": code.code_hash,
            "frozen_hash": frozen_hash, "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": rr["R"], "m": m, "K": K}])
    _n_rows, succ = _count_success(out)
    C_cell = max(float(C_TOTAL_PLAN), float(B * N))
    net = _cell_net(kept=kept, lec_bits=code.disclosure_bits, B=B,
                    succ=succ, N=N, C_total=C_cell, h_op=H_A_OP[wp],
                    i_op=math.log2(q) - Hc)
    ts = _tstats(t_list)
    return {"method": "A4", "variant": variant, "list_size": L,
            "WP": wp, "N": N, "M": M, "B": B, "rows": B,
            "success": succ, "undetected": 0, "status": "ok", "detail": "",
            "T_p50": ts["p50"], "T_p95": ts["p95"], "T_max": ts["max"],
            "total_T_dec": ts["total"],
            "code_hash": code.code_hash, "frozen_hash": frozen_hash,
            "lec_bits": int(code.disclosure_bits), "kept": kept,
            "C_total": C_cell, "net": net}


# ---------------- A6 合成桥 ----------------

def a6_fit_bundle(wp: str) -> dict:
    """由 (p*, pm*) 拟合差分 bundle：q=32 先验（runner 对称分配约定复用）.

    ``g[0] = 1−p*``；``g[31] = pm*``（runner ``_prior_from_channel``
    q 分支约定：``g[q−1] = p_minus``，其余非零元均分；三值 −1 在 GF32
    无典范像，桥接沿用该复用约定，特此注明）；其余 30 个非零元均分
    ``p* − pm*``. 要求 ``0 ≤ pm* ≤ p*``（工作点字面值满足）.
    """
    if wp not in ("F1", "F2"):
        raise ValueError(f"A6 bridge only for F1/F2, got {wp!r}")
    spec = C3R.WORKPOINTS[wp]
    p, pm = float(spec["p"]), float(spec["p_minus"])
    _q, g = RU._prior_from_channel({"q": A6_Q, "p": p, "p_minus": pm})
    g = list(g)
    H = A4M.prior_entropy_bits(g)
    return {"wp": wp, "q": A6_Q, "p_star": p, "pm_star": pm,
            "prior_g": g, "H_bundle": H,
            "convention": "g[0]=1-p*; g[31]=pm* (runner _prior_from_channel "
                          "q-branch: g[q-1]=p_minus); rest uniform over other "
                          "30 nonzero symbols"}


def _a6_stacked_matrices():
    """v28 L1 + 合成源 L2 叠矩阵（冻结合成选择 A6_SOURCE；只读复用 v28）."""
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v28 as V28)
    cfg = V28.frozen_v28_config()
    h1, h2map = V28.build_matrices(cfg)
    h2 = V28.layer_matrix(h2map, A6_SOURCE, cfg)
    stacked = tuple(list(h1) + [list(r) for r in h2])
    m_total = len(h1) + len(h2)
    return {"h1": h1, "h2": h2, "stacked": stacked,
            "m_total": int(m_total),
            "lec_bits": int(m_total * round(math.log2(A6_Q))),
            "source": A6_SOURCE, "n_base": A6_BASE_N}


def a6_bridge_t0(*, max_iter_probe: int = 100) -> dict:
    """A6 T0 门：NB-GF32 超帧机制自检（不过即 BLOCKED，不得降级）.

    T0.1 域钉定（GF(32) spec）→ T0.2 超帧整除/拼包恒等 →
    T0.3 syndrome 往返 → T0.4 无噪声单子帧译码探针（FFT-QSPA；
    max_iter 100 失败后已试 30/200 各一次，见 remedies_tried）.
    """
    cmd = ("a6_bridge_t0: GF2mField.create(32) + build_matrices + "
           "stacked syndrome roundtrip + noiseless FFT-QSPA probe")
    remedies: list[str] = []
    try:
        from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
            GF2mField)
        from comparison_bench.src.comparison_bench.formal_ir import (
            nonbinary_v28 as V28)
        field = GF2mField.create(A6_Q)
        remedies.append("field spec pinned q=32 verified: "
                        f"{field.spec.field_id[:16]}")
        mats = _a6_stacked_matrices()
        stacked = mats["stacked"]
        assert len(stacked) == mats["m_total"] and len(stacked[0]) == A6_BASE_N
        # T0.2 超帧整除 + 拼包恒等.
        for N in A6_NS:
            assert N % A6_BASE_N == 0, f"N={N} not a multiple of {A6_BASE_N}"
        rng = np.random.default_rng(SEED_M)
        # T0.3 syndrome 往返（单子帧）.
        a0 = rng.integers(0, A6_Q, A6_BASE_N).tolist()
        s0 = V28.compute_syndrome(field, stacked, a0)
        assert len(s0) == mats["m_total"], "syndrome length mismatch"
        # T0.4 无噪声探针（e=0 必须 reconstruction_ok，否则桥无意义）.
        prior0 = np.zeros((A6_BASE_N, A6_Q))
        prior0[:, 0] = 1.0
        last_err = ""
        for it in (max_iter_probe, 30, 200):
            r = V28.decode_error_domain_posterior(
                field, a0, stacked, s0, prior0, int(it))
            if bool(r.get("reconstruction_ok")):
                remedies.append(f"noiseless probe ok at max_iter={it}")
                break
            last_err = f"max_iter={it}: status={r.get('status')}"
        else:
            raise RuntimeError(f"noiseless single-frame probe failed "
                               f"({last_err})")
        tg = V28.tag64(a0, a0)
        assert len(tg) == 16
        return {"status": "ok", "gate": "T0",
                "field_id": field.spec.field_id,
                "m_total": mats["m_total"], "lec_bits": mats["lec_bits"],
                "source": A6_SOURCE, "tag64_probe": tg,
                "remedies_tried": remedies, "command": cmd}
    except Exception:
        return {"status": "BLOCKED", "gate": "T0", "command": cmd,
                "traceback": traceback.format_exc(),
                "remedies_tried": remedies or ["(none completed before throw)"],
                "decision_needed": "主线程裁决 A6 回退（A6 映射行 fallback） "
                                   "或授权桥接修复后重测 T0"}


def a6_bridge_t1(wp: str, *, n_symbols: int = 307200,
                 rel_tol: float = 0.25, abs_tol: float = 0.005) -> dict:
    """A6 T1 门：差分 bundle 喂合成校准三值对（不过即 BLOCKED）.

    由拟合 bundle 抽 (a, b=a⊕e, e) 三值对（GF(2^5) 加法 = XOR；
    e=0 恒等）；经验 (p̂, p̂m) 与 (p*, pm*) 比对，任一项超
    ``rel_tol``（小分母时 ``abs_tol`` 兜底）即 BLOCKED.
    """
    cmd = (f"a6_bridge_t1[{wp}]: sample {n_symbols} GF32 triplets from "
           f"fitted bundle, check empirical (p, pm) vs (p*, pm*)")
    try:
        bun = a6_fit_bundle(wp)
        g = np.asarray(bun["prior_g"], dtype=float)
        g = g / g.sum()
        rng = np.random.default_rng(SEED_M + 77)
        a = rng.integers(0, A6_Q, n_symbols)
        e = rng.choice(A6_Q, size=n_symbols, p=g)
        b = np.bitwise_xor(a, e)
        p_hat = float(np.mean(e != 0))
        pm_hat = float(np.mean(e == (A6_Q - 1)))
        p_s, pm_s = bun["p_star"], bun["pm_star"]

        def _ok(h, s):
            return abs(h - s) <= max(abs(s) * rel_tol, abs_tol)

        ok = _ok(p_hat, p_s) and _ok(pm_hat, pm_s)
        if not ok:
            raise RuntimeError(
                f"bundle misfit: empirical (p={p_hat:.6f}, pm={pm_hat:.6f}) "
                f"vs target (p*={p_s:.6f}, pm*={pm_s:.6f}) beyond "
                f"rel_tol={rel_tol}/abs_tol={abs_tol}")
        return {"status": "ok", "gate": "T1", "wp": wp,
                "p_hat": p_hat, "pm_hat": pm_hat,
                "p_star": p_s, "pm_star": pm_s,
                "n_symbols": n_symbols, "command": cmd,
                "bundle": {k: v for k, v in bun.items()
                           if k != "prior_g"},
                "triplet_note": "(a_truth, b_obs=a^e, e); GF(2^5) addition=XOR"}
    except Exception:
        return {"status": "BLOCKED", "gate": "T1", "wp": wp,
                "command": cmd, "traceback": traceback.format_exc(),
                "remedies_tried": ["bundle convention is frozen "
                                   "(g[1]=pm* pin); no silent refit attempted"],
                "decision_needed": "主线程裁决是否放宽 T1 容差 / 重议 bundle "
                                   "约定，或 A6 回退为映射行"}


def run_a6_cell(wp: str, N: int, bundle: dict, mats: dict, B: int,
                seed: int, out: Path) -> dict:
    """A6 合成矩阵格：超帧 = K_sub 个 v28 基帧；i.i.d. bundle 噪声；FFT-QSPA.

    成功定义：全子帧 ``reconstruction_ok``；kept = N·H_A_op；
    L_EC = K_sub × m_total × 5（tag 另计 64/成功块；v28 原生 tag 含义差异
    在此分解注记）. 无 per-block 超时.
    """
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
        GF2mField)
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v28 as V28)
    N = int(N)
    assert N % A6_BASE_N == 0
    K_sub = N // A6_BASE_N
    field = GF2mField.create(A6_Q)
    stacked = mats["stacked"]
    g = np.asarray(bundle["prior_g"], dtype=float)
    g = g / g.sum()
    prior_rows = np.tile(g, (A6_BASE_N, 1))
    kept = kept_of(wp, N)
    lec = int(K_sub * mats["lec_bits"])
    frozen_hash = _frozen_hash(
        f"M-A6|src={mats['source']}|m={mats['m_total']}|K={K_sub}|seed={seed}")
    t_list: list[float] = []
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        ok_all = True
        t0 = time.perf_counter()
        for _s in range(K_sub):
            a = rng.integers(0, A6_Q, A6_BASE_N).tolist()
            e = rng.choice(A6_Q, size=A6_BASE_N, p=g)
            y = np.bitwise_xor(np.asarray(a), np.asarray(e)).tolist()
            s_x = V28.compute_syndrome(field, stacked, a)
            r = V28.decode_error_domain_posterior(
                field, y, stacked, s_x, prior_rows, 30)
            if not bool(r.get("reconstruction_ok")):
                ok_all = False
                break
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        _append_rows(out, [{
            "method": "A6", "variant": f"x{K_sub}", "WP": wp, "N": N,
            "block": b, "ver": int(ok_all), "u": 0,
            "kept": float(kept) if ok_all else 0.0,
            "L_EC": lec, "tag": TAG if ok_all else 0,
            "T_dec": float(t_dec), "code_hash": frozen_hash,
            "frozen_hash": frozen_hash, "undetected": False,
            "status": "ok" if ok_all else "decode_failed",
            "M": "", "seed": seed, "R": None, "m": mats["m_total"],
            "K": K_sub}])
    _n_rows, succ = _count_success(out)
    C_cell = max(float(C_TOTAL_PLAN), float(B * N))
    Hc = float(bundle["H_bundle"])
    net = _cell_net(kept=kept, lec_bits=lec, B=B, succ=succ, N=N,
                    C_total=C_cell, h_op=H_A_OP[wp],
                    i_op=math.log2(A6_Q) - Hc)
    ts = _tstats(t_list)
    return {"method": "A6", "variant": f"x{K_sub}", "WP": wp, "N": N,
            "M": "", "B": B, "rows": B, "success": succ,
            "undetected": 0, "status": "ok", "detail": "",
            "T_p50": ts["p50"], "T_p95": ts["p95"], "T_max": ts["max"],
            "total_T_dec": ts["total"],
            "code_hash": frozen_hash, "frozen_hash": frozen_hash,
            "lec_bits": lec, "kept": kept, "C_total": C_cell, "net": net}


# ---------------- M 锚点 / 调度 / 网格 ----------------

def _decided(cell: dict) -> bool:
    net = cell.get("net")
    if net is None:
        return False
    B = int(cell.get("B", 0))
    F = int(net.get("F", B))
    S = int(net.get("S_main", 0))
    return F >= 10 and S >= 10


def _run_guarded(kind: str, wp: str, N: int, M: float, rr: dict, B: int,
                 seed: int, out: Path, *, variant: str = "",
                 cell_budget_s: float = CELL_BUDGET_S,
                 deadline: float | None = None) -> dict:
    """单格调度守卫：单块探针外推超格预算 → overtime-risk 零块 short（调度标记，
    非超时中断）；墙钟撞墙 → short 保留已完成块. 探针块计入正式 RNG 流
    （seed+block），落盘即正式行，不重跑."""
    if _jsonl_count(out) >= B:
        return _recount_cell(kind, wp, N, M, rr, B=B, seed=seed, out=out,
                             variant=variant)
    if kind == "A3":
        # 内存墙预检（调度标记，非译码超时）：稠密 H = m·N int64；
        # 超 128MB 则不开构造/探针，直接 overtime-risk short（如实注记）.
        # N=1024（~3MB）/2048（~10MB）/4096（~43MB）仍走真实探针.
        est_bytes = int(rr["m"]) * int(N) * 8
        if est_bytes > 128 * 1024 * 1024:
            return {"method": kind, "variant": variant, "WP": wp, "N": N,
                    "M": M, "B": B, "status": "overtime-risk",
                    "detail": (f"scheduling mark (no timeout imposed): "
                               f"dense-H estimate {est_bytes / 1e6:.0f}MB > "
                               f"128MB wall; 0 blocks run (short)"),
                    "rows": 0, "success": 0, "net": None,
                    "T_p50": 0.0, "total_T_dec": 0.0,
                    "C_total": max(float(C_TOTAL_PLAN), float(B * N))}
    # 探针：第 0 块真实执行（含一次性构造），外推剩余块. 探针写独立
    # throwaway 文件（续跑部分文件时正式文件不可按 B=1 重算 net；
    # seed+block 确定性流保证探针与正式 block 0 同分布）.
    probe_out = out.with_name(out.stem + ".probe.jsonl")
    if probe_out.exists():
        probe_out.unlink()
    t0 = time.perf_counter()
    try:
        if kind == "A3":
            probe = run_a3_cell(wp, N, M, rr, 1, seed, probe_out)
        else:
            probe = run_a4_cell(wp, N, M, rr, 1, seed, probe_out,
                                variant=variant)
    except Exception as exc:
        try:
            probe_out.unlink()
        except OSError:
            pass
        return {"method": kind, "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": _jsonl_count(out), "success": 0, "net": None}
    if probe.get("status") in ("infeasible", "construction-fail"):
        try:
            probe_out.unlink()
        except OSError:
            pass
        probe["rows"] = _jsonl_count(out)
        return probe
    probe_wall = time.perf_counter() - t0
    per_block = probe.get("T_p50") or probe_wall
    extrap = probe_wall + per_block * max(B - 1, 0)
    if extrap > cell_budget_s:
        # 调度标记：此格本预算跑不进 B=300，不开正式循环；
        # 已落盘行保留（如实 short，非清零）.
        try:
            probe_out.unlink()
        except OSError:
            pass
        kept_rows = _jsonl_count(out)
        return {"method": kind, "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "overtime-risk",
                "detail": (f"scheduling mark (no timeout imposed): probe "
                           f"extrap {extrap:.0f}s > cell_budget "
                           f"{cell_budget_s:.0f}s; {kept_rows}/{B} blocks "
                           f"retained (short)"),
                "rows": kept_rows, "success": 0, "net": None,
                "T_p50": per_block, "total_T_dec": 0.0,
                "C_total": max(float(C_TOTAL_PLAN), float(B * N))}
    try:
        probe_out.unlink()
    except OSError:
        pass
    # 正式循环（分片，片间查墙钟；无 per-block 超时）.
    cell: dict = {}
    try:
        while _jsonl_count(out) < B:
            if deadline is not None and time.perf_counter() > deadline:
                break
            if kind == "A3":
                cell = run_a3_cell(wp, N, M, rr, B, seed, out)
            else:
                cell = run_a4_cell(wp, N, M, rr, B, seed, out,
                                   variant=variant)
            if cell.get("status") in ("infeasible", "construction-fail"):
                break
            if _jsonl_count(out) < B and cell.get("status") == "ok":
                break
    except Exception as exc:
        cell = {"method": kind, "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": _jsonl_count(out), "success": 0, "net": None}
    if not cell:
        cell = {"method": kind, "variant": variant, "WP": wp, "N": N,
                "M": M, "B": B, "status": "short",
                "detail": "wall-budget-hit before start",
                "rows": 0, "success": 0, "net": None}
    if _jsonl_count(out) < B and cell.get("status") == "ok":
        cell["status"] = "short"
        cell["detail"] = ((cell.get("detail", "") + "; ") if cell.get(
            "detail") else "") + (f"wall-budget-hit: "
                                   f"{_jsonl_count(out)}/{B} blocks retained")
    return cell


def _recount_cell(kind: str, wp: str, N: int, M, rr: dict, *, B: int,
                  seed: int, out: Path, variant: str = "") -> dict:
    """续跑复用：满 B 行不重译码，由行重计汇总（kept 取行值；口径一致）."""
    rows, n_torn = _read_rows_tolerant(out)
    succ = sum(int(r.get("ver", 0)) for r in rows)
    und = sum(int(r.get("u", 0)) for r in rows)
    ok_rows = [r for r in rows if r.get("ver") == 1 and not r.get("u")]
    kept = float(ok_rows[0]["kept"]) if ok_rows else kept_of(wp, N)
    lec = float(rows[0]["L_EC"]) if rows else 0.0
    q = C3R.WORKPOINTS[wp]["q"]
    Hc = A4M.prior_entropy_bits(family_prior(wp))
    C_cell = max(float(C_TOTAL_PLAN), float(B * N))
    net = _cell_net(kept=kept, lec_bits=lec, B=B, succ=succ, N=N,
                    C_total=C_cell, h_op=H_A_OP[wp],
                    i_op=math.log2(q) - Hc)
    tdecs = [float(r.get("T_dec", 0.0)) for r in rows]
    ts = _tstats(tdecs)
    return {"method": kind, "variant": variant, "WP": wp, "N": int(N),
            "M": M, "B": B, "rows": B, "success": succ,
            "undetected": und, "status": "ok",
            "detail": ("resumed-recount from full rows (no re-decode)"
                       + (f"; {n_torn} torn lines skipped" if n_torn else "")),
            "T_p50": ts["p50"], "T_p95": ts["p95"], "T_max": ts["max"],
            "total_T_dec": ts["total"],
            "code_hash": rows[0].get("code_hash", "") if rows else "",
            "frozen_hash": rows[0].get("frozen_hash", "") if rows else "",
            "lec_bits": int(lec), "kept": kept, "C_total": C_cell,
            "net": net}


def select_m_anchor(wp: str, kind: str, *, variant: str, B: int,
                    seed: int, out_dir: Path,
                    cell_budget_s: float = CELL_BUDGET_S,
                    deadline: float | None = None) -> dict:
    """M 锚点：只在 N=16384 对 M∈{2.5,3.0} 二选一（按 Net_seg），选定后冻结
    该（WP, 方法[, 变体]）行其余 N（同 bakeoff 冻结映射；规则只读引用）."""
    results: dict[float, dict] = {}
    for M in M_LADDER:
        tag = f"{kind}{'-' + variant if variant else ''}"
        out = out_dir / f"{wp}_{tag}_N{ANCHOR_N}_M{M}.jsonl"
        if _jsonl_count(out) >= B:
            rr = rate_of(wp, ANCHOR_N, M)
            results[M] = _recount_cell(kind, wp, ANCHOR_N, M, rr, B=B,
                                       seed=seed, out=out, variant=variant)
            continue
        rr = rate_of(wp, ANCHOR_N, M)
        if not rr["feasible"]:
            results[M] = {"method": kind, "variant": variant, "WP": wp,
                          "N": ANCHOR_N, "M": M, "B": B,
                          "status": "infeasible", "detail": rr["reason"],
                          "rows": 0, "success": 0, "net": None}
            continue
        results[M] = _run_guarded(kind, wp, ANCHOR_N, M, rr, B, seed, out,
                                  variant=variant,
                                  cell_budget_s=cell_budget_s,
                                  deadline=deadline)
    nets = {M: (r.get("net") or {}).get("Net_seg", float("-inf"))
            for M, r in results.items()}
    decided = {M: _decided(results[M]) for M in M_LADDER}
    if decided[2.5] and not decided[3.0]:
        winner = 2.5
    elif decided[3.0] and not decided[2.5]:
        winner = 3.0
    elif nets[3.0] > nets[2.5]:
        winner = 3.0
    else:
        winner = 2.5
    note = ""
    if not decided[2.5] and not decided[3.0]:
        note = "both-undecided→freeze-M2.5"
    elif abs(nets[3.0] - nets[2.5]) < 1e-12:
        note = "tie→M2.5"
    return {"WP": wp, "method": kind, "variant": variant, "N": ANCHOR_N,
            "B": B, "M_winner": winner, "nets": nets, "decided": decided,
            "note": note, "cells": results}


def _n_valid(wp: str, N: int) -> bool:
    return math.floor(float(C_TOTAL_PLAN) / int(N)) >= 300


def _arms_for(wp: str) -> list[tuple[str, str]]:
    arms = [("A3", ""), ("A4", "SC"), ("A4", "SCL8")]
    return arms


def _ns_for(wp: str, Ns: tuple | None) -> tuple:
    if Ns is not None:
        return tuple(Ns)
    if wp == "F3":
        return GRID_F3
    return GRID_N6


def run_grid(*, root: Path, B: int, seed: int,
             workpoints: tuple = ("F1", "F2", "F3"),
             Ns: tuple | None = None,
             budget_s: float = BUDGET_S,
             cell_budget_s: float = CELL_BUDGET_S,
             cells_filter: str = "",
             write_tables: bool = True) -> dict:
    """M 波 A3/A4 网格执行（fresh-root 由调用方保证；落盘 blocks/*.jsonl、
    cells.json、anchor.json、manifest.json；汇总表由 build_tables 落盘）.

    ``write_tables=False``（分片执行）：只 append 块行，不写 manifest/表；
    最终由 ``--recount`` 统一重建（避免分片互相覆盖 manifest）."""
    t_start = time.perf_counter()
    deadline = t_start + budget_s
    blocks = root / "blocks"
    blocks.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"mode": f"B={B}", "B": B, "seed": seed,
                      "workpoints": list(workpoints),
                      "A3_max_iter": A3_MAX_ITER,
                      "A4_variants": {k: v for k, v in A4_VARIANTS.items()},
                      "kept_rule": "kept=N*H_A_op",
                      "H_A_op": dict(H_A_OP),
                      "per_block_timeout": None,
                      "cells": [], "anchors": {}, "events": []}

    def _wanted(wp: str, kind: str, variant: str, N: int) -> bool:
        if not cells_filter:
            return True
        tag = f"{kind}{'-' + variant if variant else ''}"
        for token in cells_filter.split(","):
            token = token.strip()
            if not token:
                continue
            parts = token.split("/")
            if len(parts) == 2 and parts[0] in ("", wp) and \
                    parts[1] in ("", tag, kind):
                return True
            if len(parts) == 3 and parts[0] in ("", wp) and \
                    parts[1] in ("", tag, kind) and \
                    (parts[2] in ("", str(N))):
                return True
        return False

    for wp in workpoints:
        for (kind, variant) in _arms_for(wp):
            tag = f"{kind}{'-' + variant if variant else ''}"
            nlist = _ns_for(wp, Ns)
            # M 锚点（F1/F2 在 ANCHOR_N；F3 无 16384 格 → 冻结 M2.5 并注记；
            # --cells 分片时锚点同样受门控，避免分片并发同文件写）.
            if wp in ("F1", "F2") and ANCHOR_N in nlist and _wanted(
                    wp, kind, variant, ANCHOR_N):
                anchor = select_m_anchor(
                    wp, kind, variant=variant, B=B, seed=seed,
                    out_dir=blocks, cell_budget_s=cell_budget_s,
                    deadline=deadline)
                manifest["anchors"][f"{wp}/{tag}"] = {
                    k: v for k, v in anchor.items() if k != "cells"}
                for M, cell in anchor["cells"].items():
                    manifest["cells"].append(_cell_record(
                        cell, anchor=True,
                        winner=(M == anchor["M_winner"])))
                Mwin: float = anchor["M_winner"]
            else:
                Mwin = 2.5
                manifest["anchors"][f"{wp}/{tag}"] = {
                    "WP": wp, "method": kind, "variant": variant,
                    "M_winner": Mwin,
                    "note": ("F3: no-16384-cell → freeze-M2.5 "
                             "(same-map-as-bakeoff-dry-grid)") if wp == "F3"
                    else ("anchor filtered out by --cells → freeze-M2.5 "
                          "(shard note; anchor owned by shard covering "
                          "N16384)") if cells_filter
                    else "anchor skipped (custom Ns) → freeze-M2.5"}
            for N in nlist:
                if N == ANCHOR_N and ANCHOR_N in nlist and wp in ("F1", "F2"):
                    continue
                if not _wanted(wp, kind, variant, N):
                    continue
                if time.perf_counter() > deadline:
                    manifest["events"].append(
                        f"wall-budget-hit: stop before {wp}/{tag}/N{N}; "
                        "completed cells retained")
                    break
                rr = rate_of(wp, N, Mwin)
                out = blocks / f"{wp}_{tag}_N{N}_M{Mwin}.jsonl"
                if not rr["feasible"]:
                    cell = {"method": kind, "variant": variant, "WP": wp,
                            "N": N, "M": Mwin, "B": B,
                            "status": "infeasible", "detail": rr["reason"],
                            "rows": 0, "success": 0, "net": None}
                elif _jsonl_count(out) >= B:
                    cell = _recount_cell(kind, wp, N, Mwin, rr, B=B,
                                         seed=seed, out=out, variant=variant)
                else:
                    cell = _run_guarded(kind, wp, N, Mwin, rr, B, seed,
                                        out, variant=variant,
                                        cell_budget_s=cell_budget_s,
                                        deadline=deadline)
                manifest["cells"].append(_cell_record(cell))
            if time.perf_counter() > deadline:
                manifest["events"].append("wall-budget-hit: outer stop")
                break
    manifest["wall_s"] = time.perf_counter() - t_start
    if write_tables:
        (root / "cells.json").write_text(json.dumps(manifest["cells"],
                                                     indent=2),
                                         encoding="utf-8")
        (root / "anchor.json").write_text(json.dumps(manifest["anchors"],
                                                     indent=2),
                                          encoding="utf-8")
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                            encoding="utf-8")
    return manifest


def _cell_record(cell: dict, *, anchor: bool = False,
                 winner: bool = True) -> dict:
    net = cell.get("net") or {}
    return {
        "WP": cell.get("WP"), "method": cell.get("method"),
        "variant": cell.get("variant", ""),
        "N": cell.get("N"), "M": cell.get("M"), "B": cell.get("B"),
        "anchor": anchor, "anchor_winner": winner,
        "status": cell.get("status", "ok"),
        "detail": cell.get("detail", ""),
        "rows": cell.get("rows", 0), "success": cell.get("success", 0),
        "F": net.get("F"), "S_main": net.get("S_main"),
        "U": net.get("U", 0),
        "Net_seg": net.get("Net_seg"), "Net_per_coin": net.get(
            "Net_per_coin"),
        "Net_per_used": net.get("Net_per_used"),
        "L_total": net.get("L_total"), "f_full": net.get("f_full"),
        "f_noTAG": net.get("f_noTAG"), "FER_hat": net.get("FER_hat"),
        "U_rate": net.get("U_rate"),
        "FER_wilson_hi": net.get("FER_wilson_hi"),
        "net_seg_wilson_hi": net.get("net_seg_wilson_hi"),
        "beta_side": net.get("beta_side"),
        "beta_warning": net.get("beta_warning") or RU.BETA_WARNING,
        "w_tail": net.get("w_tail"), "C_used": net.get("C_used"),
        "C_total": cell.get("C_total"), "N_valid": _n_valid(
            cell["WP"], cell["N"]) if cell.get("WP") else None,
        "T_p50": cell.get("T_p50"), "T_p95": cell.get("T_p95"),
        "T_max": cell.get("T_max"),
        "total_T_dec": cell.get("total_T_dec"),
        "code_hash": cell.get("code_hash"),
        "frozen_hash": cell.get("frozen_hash"),
        "decided": _decided(cell),
    }


def _mask_count(x) -> str:
    return "未定" if (x is None or int(x) <= 9) else str(int(x))


def build_tables(manifest: dict, root: Path) -> dict:
    """由 manifest cells 建明细表 + 主表（每 WP×方法[×变体]一行最优 N）.

    未定：F≤9 或 S≤9 的格 FER/计数写「未定」，不参选；N_valid≤16384；
    最优 N 只在 decided 且 N_valid 格中按 Net_seg 最大选.
    """
    cells = [c for c in manifest["cells"]
             if not c.get("anchor") or c.get("anchor_winner")]
    detail_rows: list[dict] = []
    for c in cells:
        undecided = (c.get("F") is None or c.get("S_main") is None
                     or int(c["F"]) <= 9 or int(c["S_main"]) <= 9)
        fer_disp = "未定" if undecided else f"{c['FER_hat']:.6f}"
        detail_rows.append({
            "WP": c["WP"], "method": c["method"],
            "variant": c.get("variant", ""),
            "N": c["N"], "M": c["M"], "B": c["B"],
            "status": c["status"],
            "N_valid": c["N_valid"], "decided": c["decided"],
            "S_main": _mask_count(c["S_main"]), "F": _mask_count(c["F"]),
            "U": _mask_count(c["U"]) if c.get("U") else "0",
            "Net_seg": c["Net_seg"],
            "Net_per_coin": c["Net_per_coin"],
            "Net_per_used": c["Net_per_used"],
            "L_total": c["L_total"], "f_full": c["f_full"],
            "f_noTAG": c["f_noTAG"], "FER_hat": fer_disp,
            "FER_wilson_hi": c["FER_wilson_hi"],
            "net_seg_wilson_hi": c["net_seg_wilson_hi"],
            "beta_side": c["beta_side"],
            "beta_warning": c["beta_warning"] or RU.BETA_WARNING,
            "w_tail": c["w_tail"], "C_total": c["C_total"],
            "T_p50": c["T_p50"], "T_p95": c["T_p95"], "T_max": c["T_max"],
            "total_T_dec": c["total_T_dec"],
            "code_hash": c["code_hash"],
            "frozen_hash": c["frozen_hash"],
            "detail": c["detail"]})
    main_rows: list[dict] = []
    pairs = sorted({(c["WP"], c["method"], c.get("variant", ""))
                    for c in cells})
    for wp, method, variant in pairs:
        cand = [c for c in cells
                if c["WP"] == wp and c["method"] == method
                and c.get("variant", "") == variant
                and c["decided"] and c["N_valid"]
                and c["status"] == "ok" and c["Net_seg"] is not None]
        n_valid_list = sorted({c["N"] for c in cells
                               if c["WP"] == wp and c["method"] == method
                               and c.get("variant", "") == variant
                               and c["N_valid"]})
        if not cand:
            main_rows.append({
                "WP": wp, "method": method, "variant": variant,
                "N_valid": n_valid_list,
                "N_opt": "无有效最优（全未定）", "B": "", "M": "",
                "Net_seg": "", "Net_per_coin": "", "f_full": "",
                "f_same_time": "", "FER_hat": "未定",
                "beta_side": "", "beta_warning": RU.BETA_WARNING,
                "w_tail": "", "note": "无有效最优（全未定）"})
            continue
        best = max(cand, key=lambda c: c["Net_seg"])
        top = best["Net_seg"]
        near = [c for c in cand if abs(top - c["Net_seg"]) < 0.01 * abs(top)
                or (top == 0 and c["Net_seg"] == 0)]
        note = ""
        if len(near) > 1:
            best = min(near, key=lambda c: c["N"])
            note = "tie→smallerN"
        main_rows.append({
            "WP": wp, "method": method, "variant": variant,
            "N_valid": n_valid_list,
            "N_opt": best["N"], "B": best["B"], "M": best["M"],
            "Net_seg": best["Net_seg"],
            "Net_per_coin": best["Net_per_coin"], "f_full": best["f_full"],
            "f_same_time": "extrap.-pending", "FER_hat": best["FER_hat"],
            "beta_side": best["beta_side"],
            "beta_warning": RU.BETA_WARNING, "w_tail": best["w_tail"],
            "note": note})
    t_opts = [c["total_T_dec"] for c in cells
              if c["decided"] and c["total_T_dec"]]
    t_ref = float(np.median(t_opts)) if t_opts else 0.0
    for m in main_rows:
        if m["N_opt"] == "无有效最优（全未定）":
            continue
        src = next(c for c in cells
                   if c["WP"] == m["WP"] and c["method"] == m["method"]
                   and c.get("variant", "") == m["variant"]
                   and c["N"] == m["N_opt"])
        t_cell = src["total_T_dec"] or 0.0
        if t_cell > 0 and t_ref > 0:
            m["f_same_time"] = (
                f"{m['Net_seg'] * (t_ref / t_cell):.1f} (extrap., "
                f"T_ref={t_ref:.1f}s)")
        else:
            m["f_same_time"] = "extrap.-n/a"
    _write_csv(root / "net_detail_m.csv", detail_rows)
    _write_csv(root / "net_main_m.csv", main_rows)
    return {"detail": detail_rows, "main": main_rows, "T_ref": t_ref}


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


# ---------------- recount（分片执行统一重建） ----------------

def _blank_record(*, wp: str, kind: str, variant: str, N: int, Mv,
                  B: int, status: str, detail: str, rows: int,
                  anchor: bool) -> dict:
    """未定/缺行格的完整键记录（build_tables 所需键齐全；数值为 None/未定）."""
    return {
        "WP": wp, "method": kind, "variant": variant, "N": N, "M": Mv,
        "B": B, "anchor": anchor, "anchor_winner": True,
        "status": status, "detail": detail, "rows": rows, "success": 0,
        "F": None, "S_main": None, "U": 0, "Net_seg": None,
        "Net_per_coin": None, "Net_per_used": None, "L_total": None,
        "f_full": None, "f_noTAG": None, "FER_hat": None, "U_rate": None,
        "FER_wilson_hi": None, "net_seg_wilson_hi": None,
        "beta_side": None, "beta_warning": RU.BETA_WARNING,
        "w_tail": None, "C_used": None, "C_total": None,
        "N_valid": _n_valid(wp, N),
        "T_p50": None, "T_p95": None, "T_max": None, "total_T_dec": None,
        "code_hash": "", "frozen_hash": "", "decided": False}


def recount_grid(*, root: Path, B: int, seed: int) -> dict:
    """由 ``blocks/*.jsonl`` 重建 manifest + 汇总表（不译码；分片执行终点）.

    满 B 行 → ``_recount_cell`` 重计；不足 B → short 如实保留；
    N=16384 的 F1/F2 双 M 文件按 Net_seg 重裁 winner（同锚点规则）.
    A6 文件（``{WP}_A6_N{N}.jsonl``）同表重建进 ``a6_cells.json``.
    """
    import re
    blocks = root / "blocks"
    cell_list: list[dict] = []
    anchors: dict = {}
    anchor_pair: dict = {}
    a6_cells: list[dict] = []
    pat = re.compile(r"^(F\d+)_(A3|A4-SC|A4-SCL8)_N(\d+)_M(2\.5|3\.0)\.jsonl$")
    pat6 = re.compile(r"^(F\d+)_A6_N(\d+)\.jsonl$")
    for jf in sorted(blocks.glob("*.jsonl")):
        m = pat.match(jf.name)
        m6 = pat6.match(jf.name)
        if m is None and m6 is None:
            continue
        n_rows = _jsonl_count(jf)
        if m6 is not None:
            wp, N = m6.group(1), int(m6.group(2))
            K_sub = N // A6_BASE_N
            rows6, n_torn6 = _read_rows_tolerant(jf)
            if n_rows >= B:
                rows = rows6
                succ = sum(int(r.get("ver", 0)) for r in rows)
                ok_rows = [r for r in rows
                            if r.get("ver") == 1 and not r.get("u")]
                kept = float(ok_rows[0]["kept"]) if ok_rows else kept_of(wp, N)
                lec = float(rows[0]["L_EC"]) if rows else 0.0
                bun = a6_fit_bundle(wp)
                C_cell = max(float(C_TOTAL_PLAN), float(B * N))
                net = _cell_net(
                    kept=kept, lec_bits=lec, B=B, succ=succ, N=N,
                    C_total=C_cell, h_op=H_A_OP[wp],
                    i_op=math.log2(A6_Q) - float(bun["H_bundle"]))
                tdecs = [float(r.get("T_dec", 0.0)) for r in rows]
                ts = _tstats(tdecs)
                a6_cells.append({
                    "WP": wp, "method": "A6", "variant": f"x{K_sub}",
                    "N": N, "M": "", "B": B, "anchor": False,
                    "anchor_winner": True, "status": "ok", "detail":
                    ("recount from full rows (no re-decode)"
                     + (f"; {n_torn6} torn lines skipped" if n_torn6 else "")),
                    "rows": B, "success": succ, "F": net["F"],
                    "S_main": net["S_main"], "U": 0,
                    "Net_seg": net["Net_seg"],
                    "Net_per_coin": net["Net_per_coin"],
                    "Net_per_used": net["Net_per_used"],
                    "L_total": net["L_total"], "f_full": net["f_full"],
                    "f_noTAG": net["f_noTAG"], "FER_hat": net["FER_hat"],
                    "U_rate": net["U_rate"],
                    "FER_wilson_hi": net["FER_wilson_hi"],
                    "net_seg_wilson_hi": net["net_seg_wilson_hi"],
                    "beta_side": net["beta_side"],
                    "beta_warning": net["beta_warning"] or RU.BETA_WARNING,
                    "w_tail": net["w_tail"], "C_used": net["C_used"],
                    "C_total": C_cell, "N_valid": _n_valid(wp, N),
                    "T_p50": ts["p50"], "T_p95": ts["p95"],
                    "T_max": ts["max"], "total_T_dec": ts["total"],
                    "code_hash": rows[0].get("code_hash", ""),
                    "frozen_hash": rows[0].get("frozen_hash", ""),
                    "decided": bool(net["F"] >= 10 and
                                    net["S_main"] >= 10)})
            else:
                a6_cells.append({
                    "WP": wp, "method": "A6", "variant": f"x{K_sub}",
                    "N": N, "M": "", "B": B, "anchor": False,
                    "anchor_winner": True, "status": "short",
                    "detail": f"recount: {n_rows}/{B} blocks retained",
                    "rows": n_rows, "success": 0, "decided": False})
            continue
        assert m is not None
        wp, tag, N, Ms = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        Mv = float(Ms)
        kind = "A3" if tag == "A3" else "A4"
        variant = "" if tag == "A3" else tag.split("-", 1)[1]
        rr = rate_of(wp, N, Mv)
        if n_rows >= B:
            cell = _recount_cell(kind, wp, N, Mv, rr, B=B, seed=seed,
                                 out=jf, variant=variant)
            rec = _cell_record(cell)
        else:
            rec = _blank_record(
                wp=wp, kind=kind, variant=variant, N=N, Mv=Mv, B=B,
                status="short",
                detail=f"recount: {n_rows}/{B} blocks retained",
                rows=n_rows, anchor=False)
        is_anchor = (wp in ("F1", "F2") and N == ANCHOR_N)
        rec["anchor"] = is_anchor
        if is_anchor:
            anchor_pair.setdefault((wp, tag), {})[Mv] = rec
        cell_list.append(rec)
    # 期望网格补全：无落盘文件的格（探针调度未留痕 / 未及跑）补 no-rows
    # 记录，矩阵无暗格；锚点缺 M 边同样补（重裁按同规则，双方无 decided
    # 则冻 M2.5 并注记）.
    seen = set()
    for c in cell_list:
        tag0 = (c["method"] + "-" + c["variant"]) if c.get("variant") else c["method"]
        seen.add((c["WP"], tag0, c["N"], c.get("M")))

    def _have(wp: str, tag: str, N: int, Mv) -> bool:
        if N == ANCHOR_N and wp in ("F1", "F2"):
            return (wp, tag, N, Mv) in seen
        return any(s[0] == wp and s[1] == tag and s[2] == N for s in seen)

    for wp in ("F1", "F2", "F3"):
        for tag in ("A3", "A4-SC", "A4-SCL8"):
            kind = "A3" if tag == "A3" else "A4"
            variant = "" if tag == "A3" else tag.split("-", 1)[1]
            for N in (GRID_N6 if wp in ("F1", "F2") else GRID_F3):
                Ms: tuple = (2.5, 3.0) if (
                    N == ANCHOR_N and wp in ("F1", "F2")) else ("",)
                for Mv in Ms:
                    if _have(wp, tag, N, Mv):
                        continue
                    is_anchor = (wp in ("F1", "F2") and N == ANCHOR_N)
                    rec = _blank_record(
                        wp=wp, kind=kind, variant=variant, N=N, Mv=Mv,
                        B=B, status="no-rows",
                        detail=("recount: no rows landed (probe scheduling "
                                "mark left no rows, or cell never "
                                "attempted); not decided"),
                        rows=0, anchor=is_anchor)
                    if is_anchor:
                        anchor_pair.setdefault((wp, tag), {})[Mv] = rec
                    cell_list.append(rec)
    # 锚点 winner 重裁（同 select_m_anchor 规则）.
    for (wp, tag), pair in anchor_pair.items():
        # _cell_record 的 Net_seg 在 net 缺失时为 None → 按 -inf.
        nets = {Mv: (r["Net_seg"] if isinstance(r.get("Net_seg"),
                                                (int, float))
                     else float("-inf")) for Mv, r in pair.items()}
        dec = {Mv: bool(r.get("decided")) for Mv, r in pair.items()}
        if dec.get(2.5) and not dec.get(3.0):
            winner = 2.5
        elif dec.get(3.0) and not dec.get(2.5):
            winner = 3.0
        elif nets.get(3.0, float("-inf")) > nets.get(2.5, float("-inf")):
            winner = 3.0
        else:
            winner = 2.5
        for Mv, r in pair.items():
            r["anchor_winner"] = (Mv == winner)
        kind = "A3" if tag == "A3" else "A4"
        variant = "" if tag == "A3" else tag.split("-", 1)[1]
        if not dec.get(2.5) and not dec.get(3.0):
            note = "both-undecided→freeze-M2.5"
        elif abs(nets.get(3.0, float("-inf"))
                 - nets.get(2.5, float("-inf"))) < 1e-12:
            note = "tie→M2.5"
        else:
            note = "recount re-arbitrated (same anchor rule)"
        anchors[f"{wp}/{tag}"] = {
            "WP": wp, "method": kind, "variant": variant, "N": ANCHOR_N,
            "B": B, "M_winner": winner, "nets": nets, "decided": dec,
            "note": note}
    manifest = {"mode": f"B={B}", "B": B, "seed": seed,
                "recount": True, "cells": cell_list, "anchors": anchors,
                "events": ["recount from blocks/*.jsonl (no re-decode)"]}
    manifest["wall_s"] = 0.0
    (root / "cells.json").write_text(json.dumps(cell_list, indent=2),
                                     encoding="utf-8")
    (root / "anchor.json").write_text(json.dumps(anchors, indent=2),
                                      encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                        encoding="utf-8")
    tables = build_tables(manifest, root)
    # A6 合并：块重建优先；块无行时保留 --a6-full 已落盘的调度记录（不丢）.
    prev6: list[dict] = []
    if (root / "a6_cells.json").exists():
        try:
            prev6 = json.loads((root / "a6_cells.json").read_text(
                encoding="utf-8"))
        except Exception:
            prev6 = []
    seen6 = {(c.get("WP"), c.get("N")) for c in a6_cells}
    for c in prev6:
        if (c.get("WP"), c.get("N")) not in seen6:
            a6_cells.append(c)
    if a6_cells:
        (root / "a6_cells.json").write_text(json.dumps(a6_cells, indent=2),
                                            encoding="utf-8")
    return {"cells": len(cell_list), "a6_cells": len(a6_cells),
            "main": len(tables["main"])}


# ---------------- MLOG 写者（OP-M2 唯一写者） ----------------

def append_mlog(lines: list[str], *, path: Path | None = None,
                header: str = "") -> Path:
    """单一日志 append-only 写者（OP-M2 唯一写者；OP-M1 回执由主线程 append）.

    ``path`` 仅测试注入；生产路径恒为 ``MLOG_PATH``.
    """
    lp = Path(path) if path is not None else MLOG_PATH
    if lp.parent and str(lp.parent) not in ("", "."):
        lp.parent.mkdir(parents=True, exist_ok=True)
    if not lp.exists():
        lp.write_text(
            "# C-3 M 波执行日志（单一 append-only，OP-M2 唯一写者）\n\n"
            "> Track：EXPLORE（合成校准信道；B=300/格；块级落盘 + 汇总）.\n"
            "> 冻结包 `C3_MPACKET.md` 全文逐字遵守；背景 `C_BATCH_AMEND.md`.\n"
            "> OP-M2 写作用域：A3/A4 循环 + A6 桥 + 汇总；"
            "OP-M1 经回执由主线程 append（标记来源）.\n",
            encoding="utf-8")
    stamp = _now()
    with lp.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {stamp} OP-M2 {header}\n")
        for ln in lines:
            fh.write(f"- {ln}\n")
    return lp


# ---------------- CLI ----------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="C-3 M 波驱动（OP-M2）")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--a6-bridge", action="store_true",
                    help="只跑 A6 T0/T1 桥门并打印 ok/BLOCKED")
    ap.add_argument("--a6-full", action="store_true",
                    help="A6 桥通过后跑 3 点矩阵（F1/F2 x 1024/4096/16384）")
    ap.add_argument("--output-root", default="workspace/c3_mtune/mt_20261008")
    ap.add_argument("--cells", default="",
                    help="子集过滤，如 F1/A3/1024,F2/A4-SCL8/8192")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--no-tables", action="store_true",
                    help="分片执行：只 append 块行，不写 manifest/表 "
                         "(终点 --recount 统一重建)")
    ap.add_argument("--recount", action="store_true",
                    help="由 blocks/*.jsonl 重建 manifest + 汇总表（不译码）")
    ap.add_argument("--budget-s", type=float, default=BUDGET_S)
    ap.add_argument("--cell-budget-s", type=float, default=CELL_BUDGET_S)
    ap.add_argument("--seed", type=int, default=SEED_M)
    args = ap.parse_args(argv)
    root = Path(args.output_root)

    if args.a6_bridge:
        t0 = a6_bridge_t0()
        print(json.dumps(t0, indent=2, default=str))
        if t0["status"] != "ok":
            return 4
        for wp in ("F1", "F2"):
            t1 = a6_bridge_t1(wp)
            print(json.dumps(t1, indent=2, default=str))
            if t1["status"] != "ok":
                return 4
        return 0

    if args.a6_full:
        if root.exists() and not args.resume:
            print(f"refuse: output root exists (fresh-root): {root}",
                  file=sys.stderr)
            return 2
        root.mkdir(parents=True, exist_ok=True)
        t0 = a6_bridge_t0()
        (root / "a6_t0.json").write_text(json.dumps(t0, indent=2,
                                                    default=str),
                                         encoding="utf-8")
        if t0["status"] != "ok":
            (root / "a6_BLOCKED.json").write_text(json.dumps(t0, indent=2,
                                                             default=str),
                                                  encoding="utf-8")
            print(json.dumps(t0, indent=2, default=str))
            return 4
        mats = _a6_stacked_matrices()
        only = [t.strip() for t in (args.cells or "").split(",")
                if t.strip()]
        prev = []
        if (root / "a6_cells.json").exists():
            try:
                prev = json.loads((root / "a6_cells.json").read_text(
                    encoding="utf-8"))
            except Exception:
                prev = []
        if only:
            # 分片续跑：保留不在本次 only 子集中的旧格，其余重跑后替换.
            cells = [c for c in prev
                     if f"{c.get('WP')}/A6/{c.get('N')}" not in only]
        else:
            cells = []
        for wp in ("F1", "F2"):
            t1 = a6_bridge_t1(wp)
            (root / f"a6_t1_{wp}.json").write_text(
                json.dumps(t1, indent=2, default=str), encoding="utf-8")
            if t1["status"] != "ok":
                (root / "a6_BLOCKED.json").write_text(
                    json.dumps(t1, indent=2, default=str), encoding="utf-8")
                print(json.dumps(t1, indent=2, default=str))
                return 4
            bun = a6_fit_bundle(wp)
            for N in A6_NS:
                if only and f"{wp}/A6/{N}" not in only:
                    continue
                out = root / "blocks" / f"{wp}_A6_N{N}.jsonl"
                if _jsonl_count(out) >= B_FULL:
                    rows = [json.loads(x) for x in out.read_text(
                        encoding="utf-8").splitlines() if x.strip()]
                    succ = sum(int(r.get("ver", 0)) for r in rows)
                    kept = kept_of(wp, N)
                    net = _cell_net(
                        kept=kept, lec_bits=mats["lec_bits"] * (N // 1024),
                        B=B_FULL, succ=succ, N=N,
                        C_total=max(float(C_TOTAL_PLAN), float(B_FULL * N)),
                        h_op=H_A_OP[wp],
                        i_op=math.log2(A6_Q) - float(bun["H_bundle"]))
                    cells.append({"WP": wp, "method": "A6",
                                  "variant": f"x{N // 1024}", "N": N,
                                  "status": "ok", "success": succ,
                                  "Net_seg": net["Net_seg"]})
                    continue
                # 探针守卫：B=1 真实试跑，外推超格预算则 overtime-risk
                # short（调度标记，非超时中断）.
                probe_out = out.with_name(out.stem + ".probe.jsonl")
                if probe_out.exists():
                    probe_out.unlink()
                t_pr = time.perf_counter()
                try:
                    run_a6_cell(wp, N, bun, mats, 1, args.seed,
                                probe_out)
                    probe_wall = time.perf_counter() - t_pr
                    prows = [json.loads(x) for x in probe_out.read_text(
                        encoding="utf-8").splitlines() if x.strip()]
                    per_block = (float(prows[0].get("T_dec", probe_wall))
                                 if prows else probe_wall)
                finally:
                    if probe_out.exists():
                        probe_out.unlink()
                extrap = probe_wall + per_block * (B_FULL - 1)
                if extrap > args.cell_budget_s:
                    cells.append({
                        "WP": wp, "method": "A6",
                        "variant": f"x{N // 1024}", "N": N,
                        "status": "overtime-risk",
                        "detail": (f"scheduling mark (no timeout imposed): "
                                   f"probe extrap {extrap:.0f}s > "
                                   f"cell_budget {args.cell_budget_s:.0f}s; "
                                   f"0 blocks run (short)"),
                        "rows": 0, "success": 0})
                    continue
                c = run_a6_cell(wp, N, bun, mats, B_FULL, args.seed,
                                out)
                cells.append(_cell_record(c))
        (root / "a6_cells.json").write_text(json.dumps(cells, indent=2),
                                            encoding="utf-8")
        print(json.dumps({"cells": len(cells),
                          "ok": sum(1 for c in cells
                                    if c.get("status") == "ok")}, indent=2))
        return 0

    if args.recount:
        if not root.exists():
            print(f"refuse: output root absent: {root}", file=sys.stderr)
            return 2
        res = recount_grid(root=root, B=B_FULL, seed=args.seed)
        print(json.dumps(res, indent=2))
        return 0

    if args.dry_run:
        if root.exists() and not args.resume:
            print(f"refuse: output root exists: {root}", file=sys.stderr)
            return 2
        try:
            manifest = run_grid(
                root=root, B=8, seed=args.seed,
                workpoints=("F1",), Ns=(32, 64),
                budget_s=args.budget_s,
                cell_budget_s=args.cell_budget_s,
                cells_filter=args.cells,
                write_tables=not args.no_tables)
        except SystemExit as exc:
            print(f"STOP: {exc}", file=sys.stderr)
            return 3
        if args.no_tables:
            print(json.dumps({"cells": len(manifest["cells"]),
                              "tables": "skipped"}, indent=2))
            return 0
        tables = build_tables(manifest, root)
        print(json.dumps({"cells": len(manifest["cells"]),
                          "main": len(tables["main"])}, indent=2))
        return 0
    if args.full:
        if root.exists() and not args.resume:
            print(f"refuse: output root exists (fresh-root): {root}",
                  file=sys.stderr)
            return 2
        try:
            manifest = run_grid(root=root, B=B_FULL, seed=args.seed,
                                budget_s=args.budget_s,
                                cell_budget_s=args.cell_budget_s,
                                cells_filter=args.cells,
                                write_tables=not args.no_tables)
        except SystemExit as exc:
            print(f"STOP: {exc}", file=sys.stderr)
            return 3
        if args.no_tables:
            print(json.dumps({"cells": len(manifest["cells"]),
                              "tables": "skipped"}, indent=2))
            return 0
        tables = build_tables(manifest, root)
        append_mlog([
            f"--full 落盘：cells={len(manifest['cells'])} "
            f"main={len(tables['main'])} wall={manifest.get('wall_s', 0):.0f}s",
            f"events={manifest.get('events', [])}",
        ], header="--full 汇总")
        print(json.dumps({"cells": len(manifest["cells"]),
                          "main": len(tables["main"]),
                          "wall_s": manifest.get("wall_s")}, indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
