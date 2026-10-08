"""C-3 M 波 A1/A2 执行循环（OP-M1；EXPLORE 合成-only）.

冻结依据（逐字遵守）：``docs/research_cycles/C-BATCH/C3_MPACKET.md`` §1–§3+§5
（A1/A2 部分）；设计背景见 ``C_BATCH_AMEND.md``（M1/M2）。

Track：EXPLORE。只跑合成参数化信道；不读原始数据（零 ``D:/Data`` 访问）；
不跑真实解码；不做科学判定（只落盘块行 + 汇总，不排序、不关闭路线）。

范围纪律：本模块 + ``tests/test_c3m_a1a2.py`` 为 OP-M1 全部写作用域；
OP-M2 文件（``msd_c3m_driver.py``、``test_c3m_driver.py``）与 ``C3_MLOG.md``
一律不碰（结果经回执消息返回，主线程代记入日志）。

 frozen 要点：
 - kept 口径：``kept = N·H_A_op``（F1→10，F2→9），**由调用方传入**
   （``kept_per_success`` 必填参数；本模块附 ``H_A_OP``/``kept_of`` 供调用方
   显式传递，不做默认估算）。
 - 码率：只读引用 ``bakeoff.compute_rate``（``family="bin"``），不另立公式；
   M 锚点映射同 bakeoff（M∈{2.5,3.0} 只在 N=16384 二选一，其余 N 用 winner）。
 - A1 构造：高码率区（R 0.65–0.8 目标带）二元 LDPC，QC 不规则码（包允许
   “PEG 或 QC”二选一；PEG 在大 N 下构造墙钟过高，本模块冻结 QC，见
   ``build_qc_code`` 注记）。T0 门：N=1024/B=30 成功率门
   （``T0_MIN_SUCC_RATE=0.30``；冻结样本实测 F1=15/30、F2=21/30，均过门），
   不过门不开矩阵（``run_a1_cell`` 在无过门 T0 记录时返回 ``t0-gated``，
   零译码、零落盘）。
 - R 目标带说明（诚实注记）：冻结码率规则下 F1 在小 N 处 R≈0.58（低于
   0.65–0.8 目标带，系 gap 表所致，非构造可改）；R 带只做记录
   （``R_in_target_zone``），**不**作为开门条件（否则 F1 永不开矩阵，
   与包 §2 “F1/F2×6N” 矛盾）。门条件 = 可行 + 成功率 ≥ 阈值。
 - 两级循环：level-A = LSB 平面 LDPC syndrome 协调（A1: QC-BP；
   A2: Polar SC / SCL8，冻结集按 p_op 重算 + hash）；level-B = 符号位
   **明文发送**，``L_B = #{marked}×1 bit`` 精确计数（合成真值：marked 取
   真实 LSB 误码支撑；口径差注记：C-5 真实标记用译码标记位估计，
   含漏检/误标，本模块按理想值记账，行 ``detail`` 注明）。
   失败块 level-B 不发送（无可锚定的重建），``L_EC = m``；
   成功块 ``L_EC = m + L_B``；无 rescue 项。
 - A2：冻结集按 p_op 重算（Bhattacharyya 递归，本地实现）+ hash；
   SC（本地 njit，与 sibling 同 f/g/调度口径）+ SCL8（sibling
   ``polar_core`` 只读调用，缺失则 ``unavailable`` 行透传，不断言失败）。
 - TAG=64；行键 = runner ``ROW_KEYS`` + ``frozen_hash`` + WP/M/seed/R/m/K/
   L_A/L_B 等；逐块落盘 JSONL（append-only，已落盘行数续跑）；
   B=300/格；种子冻结 20261009（逐块 ``seed + block``）；
   **无 per-block 超时**，一律跑到译码 verdict，T_dec 逐块记录
   （cell 附 p50/p95/max）。
 - F1/F2 × N{1024,2048,4096,8192,16384,32768}；F3 二进制两级记
   ``infeasible-by-construction``（F3 p≈0.4741 → R<0，不跑、零行）。
 - 记账：``runner.net_of_cell`` 原样复用（``L_EC_bits`` 取全格平均；
   数学上 ``B·mean = ΣL_EC`` 故 Net_seg/L_total 与逐块精确和一致，
   本模块断言两者一致，差值超限即报错不停跑）。
 - 机器根：``workspace/c3_mtune/mt_a1a2_opm1/``（``mt_a1a2_`` 前缀，
   与 OP-M2 错开）；u 恒 0（合成真值精确对比，TAG 复核建模为理想，
   同 bakeoff 冻结解释 5）。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir import (
    msd_c1_runner as runner,
)

try:  # 只读引用 bakeoff 码率函数（M 锚点映射同源；不拷贝公式）。
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c3_bakeoff as bakeoff,
    )
except Exception:  # pragma: no cover - 缺失时由 rate_bin 报错
    bakeoff = None  # type: ignore[assignment]

__all__ = [
    "SEED", "TAG", "B_FULL", "N_GRID", "M_LADDER", "ANCHOR_N",
    "T0_N", "T0_B", "T0_MIN_SUCC_RATE", "BP_MAX_ITER", "A2_LIST_SIZE",
    "H_A_OP", "R_TARGET_ZONE", "C_TOTAL_PLAN", "DEFAULT_ROOT",
    "BETA_WARNING",
    "h2", "frozen_hash_of", "p_op_of", "kept_of", "rate_bin",
    "bhattacharyya_frozen_set", "build_qc_code", "t0_gate",
    "polar_construction_check", "sc_decode_nb",
    "run_a1_cell", "run_a2_cell", "run_cell_parallel",
    "f3_binary_infeasible",
    "select_M_anchor_m", "run_grid_m", "manifest_from_blocks",
    "default_root",
]

SEED = 20261009
TAG = 64
assert runner.TAG_BITS == 64, "runner TAG_BITS must be 64 (M packet TAG=64)"
BETA_WARNING = runner.BETA_WARNING
B_FULL = 300
N_GRID = (1024, 2048, 4096, 8192, 16384, 32768)
M_LADDER = (2.5, 3.0)
ANCHOR_N = 16384
T0_N = 1024
T0_B = 30
T0_MIN_SUCC_RATE = 0.30
BP_MAX_ITER = 300  # M2 冻结单值（200–500 区间内）
A2_LIST_SIZE = 8
H_A_OP = {"F1": 10.0, "F2": 9.0}
R_TARGET_ZONE = (0.65, 0.80)  # 目标带：只记录，不做开门条件（见模块注记）
C_TOTAL_PLAN = 5_000_000  # 同 bakeoff 冻结规划值（分母口径一致）
DEFAULT_ROOT = Path("workspace/c3_mtune/mt_a1a2_opm1")
QC_Z = 64  # QC 环大小（整除全部网格 N）

# 口径差注记（逐行落盘，合成真值 vs C-5 真实标记）。
CALIBER_NOTE = ("L_B=synthetic-truth marked count x1bit (ideal); "
                "cf C-5 real caliber uses decoder-estimated marking bits")


# ---------------- 基础 ----------------

def h2(p: float) -> float:
    """二进制熵（比特）。"""
    p = float(p)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


def frozen_hash_of(text: str) -> str:
    """冻结标识短 hash（sha256 截断 16 hex，同 bakeoff 口径）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def p_op_of(wp: str) -> float:
    """工作点校准后 p_op（只读 bakeoff WORKPOINTS；F1/F2 仅 M 波用 F3 另见）。"""
    if bakeoff is None:  # pragma: no cover
        raise RuntimeError("msd_c3_bakeoff unavailable for read-only rate ref")
    return float(bakeoff.WORKPOINTS[wp]["p"])


def kept_of(wp: str, N: int) -> float:
    """调用方 kept 装配：``kept = N·H_A_op``（F1→10，F2→9；F3 无二进制 kept）。"""
    if wp not in H_A_OP:
        raise ValueError(f"no binary kept for WP {wp!r} "
                         "(F3 binary is infeasible-by-construction)")
    return float(int(N) * H_A_OP[wp])


def rate_bin(wp: str, N: int, M: float) -> dict:
    """二进制臂冻结码率（只读引用 ``bakeoff.compute_rate``，不另立公式）。

    ``R = 1−h2(p_op)−gap_bin(N)−margin_B−(M−2.5)×0.01``；
    ``K = round-half-up(N·R)``；``m = N − K``。
    """
    if bakeoff is None:  # pragma: no cover
        raise RuntimeError("msd_c3_bakeoff unavailable for read-only rate ref")
    spec = bakeoff.WORKPOINTS[wp]
    return bakeoff.compute_rate(family="bin", p_op=float(spec["p"]),
                                H_q=float(spec["H_q"]), q=int(spec["q"]),
                                N=int(N), M=float(M))


def default_root() -> Path:
    """OP-M1 机器根（``mt_a1a2_`` 前缀，与 OP-M2 错开；只读约束由调用方保证）。"""
    return DEFAULT_ROOT


# ---------------- Polar 冻结集（按 p_op 重算，本地实现） ----------------

def bhattacharyya_frozen_set(N: int, K: int, p: float) -> tuple[tuple, tuple]:
    """二进制 BSC 冻结集（按 p_op 重算：Z0 = 2√(p(1−p))，极化递归
    Z−=2Z−Z²、Z+=Z²，可靠度 Z 升序取信息位；并列按下标确定性打破）。

    与 bakeoff 同数学口径，本地实现（A2 分支自持，不跨模块取私函数）。
    """
    N = int(N)
    if N < 1 or (N & (N - 1)) != 0:
        raise ValueError(f"N must be a power of two, got {N}")
    if not (0 <= int(K) <= N):
        raise ValueError(f"require 0 <= K <= N, got K={K}, N={N}")
    z0 = 2.0 * math.sqrt(max(float(p), 0.0) * max(1.0 - float(p), 0.0))
    z = np.array([z0])
    while z.shape[0] < N:
        nxt = np.empty(2 * z.shape[0])
        nxt[0::2] = 2.0 * z - z * z
        nxt[1::2] = z * z
        z = nxt
    order = sorted(range(N), key=lambda i: (float(z[i]), i))
    info = tuple(sorted(order[:int(K)]))
    frozen = tuple(sorted(order[int(K):]))
    return frozen, info


def polar_construction_check(wp: str, N: int, M: float) -> dict:
    """A2 开门检查（绑定项）：码率可行 + 冻结集有效（0 < |F| < N）+ hash。

    Polar 无经验成功率门（包只对 A1 构造立 T0 门）；N=1024/B=30 pilot
    成功率仅记录（advisory），不拦截。返回 ``{"ok":..., "frozen_hash":...}``。
    """
    rr = rate_bin(wp, N, M)
    if not rr["feasible"]:
        return {"ok": False, "reason": rr["reason"], "R": rr["R"],
                "K": rr["K"], "m": rr["m"], "frozen_hash": ""}
    p = p_op_of(wp)
    frozen, info = bhattacharyya_frozen_set(int(N), int(rr["K"]), p)
    if not (0 < len(frozen) < int(N)):
        return {"ok": False, "reason": "degenerate frozen set",
                "R": rr["R"], "K": rr["K"], "m": rr["m"], "frozen_hash": ""}
    fh = frozen_hash_of(f"C3M-A2|wp={wp}|n={N}|K={rr['K']}|p={p}|"
                        f"F={list(frozen)}")
    return {"ok": True, "R": rr["R"], "K": rr["K"], "m": rr["m"],
            "frozen": frozen, "info": info, "frozen_hash": fh,
            "code_hash": fh}


# ---------------- A1 构造：QC 不规则码（冻结） ----------------

def _qc_shifts(*, nb: int, rows_of: list, Z: int, seed: int) -> list:
    """各边环移（确定性种子流；返回与 rows_of 等长的 shift 列表）。"""
    rng = np.random.default_rng(int(seed))
    return [int(rng.integers(0, Z)) for _ in rows_of]


def _qc_four_cycles(*, mb0: int, nb: int, conn: list, shifts: dict,
                    Z: int) -> int:
    """4-环碰撞计数（块列对共享两块行且移位差同余）。"""
    ncol = nb
    cnt = 0
    # 按块行对组织：rowpair -> [(col, s_row1, s_row2)]
    from collections import defaultdict
    buckets: dict = defaultdict(list)
    for j in range(ncol):
        rows = conn[j]
        for a in range(len(rows)):
            for b in range(a + 1, len(rows)):
                r1, r2 = rows[a], rows[b]
                key = (r1, r2) if r1 < r2 else (r2, r1)
                s1 = shifts[(r1 if r1 < r2 else r2, j)]
                s2 = shifts[(r2 if r1 < r2 else r1, j)]
                buckets[key].append((s1 - s2) % Z)
    for _key, diffs in buckets.items():
        seen: dict[int, int] = {}
        for d in diffs:
            if d in seen:
                cnt += 1
            else:
                seen[d] = 1
    return cnt


def build_qc_code(*, N: int, m: int) -> dict:
    """QC 不规则码（冻结构造；包允许“PEG 或 QC”二选一）。

    - 环大小 Z=64（整除全部网格 N）；块列数 nb=N/Z；列重 profile
      ``dv_j = 2 if j%3==2 else 3``（不规则）。
    - 块行数 mb0=ceil(m/Z)；确定性轮转基图 + 确定性种子环移
      （``shift_seed = SEED + 1009·N + m``）；末块行删余至精确 m 行。
    - 有界确定性去 4-环（≤40 次重抽，取最优；只记录，不设门）。
    - 空行断言 + 确定性补边（触发即记录；正常不触发）。
    返回 ``{"H"(csr), "code_hash", "meta"}``。构造本身确定性，
    与信道随机性无关（hash 可复现）。
    """
    N, m = int(N), int(m)
    Z = QC_Z
    if N % Z:
        raise ValueError(f"N must be a multiple of Z={Z}, got {N}")
    if not (0 < m < N):
        raise ValueError(f"require 0 < m < N, got m={m}, N={N}")
    nb = N // Z
    mb0 = (m + Z - 1) // Z
    trim = mb0 * Z - m
    # 确定性轮转基图（每块列 dv_j 条边，步长轮转保证覆盖）。
    conn: list[list[int]] = []
    for j in range(nb):
        dv = 2 if (j % 3 == 2) else 3
        step = max(1, mb0 // dv)
        rows: list[int] = []
        t = 0
        while len(rows) < dv:
            r = (j + t * step) % mb0
            if r not in rows:
                rows.append(r)
            t += 1
            if t > mb0 * (dv + 2):  # 防御性兜底（正常不可达）
                for rr in range(mb0):
                    if len(rows) >= dv:
                        break
                    if rr not in rows:
                        rows.append(rr)
                break
        conn.append(sorted(rows))
    shift_seed = SEED + 1009 * N + m
    best = None
    rng = np.random.default_rng(shift_seed)
    streams = [rng.integers(0, Z, size=sum(len(c) for c in conn))
               for _ in range(41)]
    for trial in range(41):
        flat = streams[trial]
        shifts: dict[tuple[int, int], int] = {}
        it = iter(flat)
        for j in range(nb):
            for r in conn[j]:
                shifts[(r, j)] = int(next(it))
        cyc = _qc_four_cycles(mb0=mb0, nb=nb, conn=conn, shifts=shifts, Z=Z)
        if best is None or cyc < best[0]:
            best = (cyc, shifts)
            if cyc == 0:
                break
    cyc, shifts = best
    rows_l: list[int] = []
    cols_l: list[int] = []
    for j in range(nb):
        for r in conn[j]:
            s = shifts[(r, j)]
            base_r, base_c = r * Z, j * Z
            for a in range(Z):
                rows_l.append(base_r + (a + s) % Z)
                cols_l.append(base_c + a)
    Hfull = sparse.coo_matrix(
        (np.ones(len(rows_l), dtype=np.uint8),
         (np.asarray(rows_l), np.asarray(cols_l))),
        shape=(mb0 * Z, N), dtype=np.uint8).tocsr()
    if trim:
        Hfull = Hfull[:m, :]
    Hfull.sort_indices()
    # 空行断言 + 确定性补边。
    indptr = Hfull.indptr
    n_fixed = 0
    if trim or True:
        Hlil = Hfull.tolil()
        fix_rng = np.random.default_rng(shift_seed + 7)
        for i in range(m):
            if len(Hlil.rows[i]) == 0:
                Hlil.rows[i] = [int(fix_rng.integers(0, N))]
                Hlil.data[i] = [np.uint8(1)]
                n_fixed += 1
        Hfull = Hlil.tocsr()
        Hfull.sort_indices()
    code_hash = frozen_hash_of(
        f"C3M-A1-QC|n={N}|m={m}|Z={Z}|dv=2/3-profile|"
        f"shiftseed={shift_seed}|trim={trim}|cycles={cyc}|fix={n_fixed}")
    col_w = np.asarray((Hfull != 0).sum(axis=0)).ravel()
    return {"H": Hfull, "code_hash": code_hash,
            "meta": {"family": "QC-irregular", "Z": Z, "nb": nb,
                     "mb0": mb0, "trim": trim, "four_cycles": int(cyc),
                     "fixed_empty_rows": int(n_fixed),
                     "shift_seed": int(shift_seed),
                     "col_w_min": int(col_w.min()),
                     "col_w_max": int(col_w.max())}}


# ---------------- T0 门（A1 绑定） ----------------

def _bp_decode_block(*, H, syn: np.ndarray, y: np.ndarray,
                     p: float) -> tuple[np.ndarray, float]:
    """单块 syndrome BP 译码（跑到 verdict；无超时参数）。

    ``delta = syn − H·y``；返回 ``(xhat, T_dec)``。
    """
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
        make_bp_decoder,
    )
    ch = np.full(H.shape[1], float(p))
    t0 = time.perf_counter()
    dec = make_bp_decoder(parity_check_matrix=H, error_channel=ch.copy(),
                          max_iter=BP_MAX_ITER)
    delta = (np.asarray(syn).ravel()
             - (np.asarray((H @ y) % 2).ravel())) % 2
    err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
    xh = np.bitwise_xor(np.asarray(y, dtype=np.uint8),
                        np.asarray(err, dtype=np.uint8))
    return xh, time.perf_counter() - t0


def t0_gate(wp: str, M: float = 2.5, *, B: int = T0_B, N: int = T0_N,
            seed: int = SEED,
            min_succ_rate: float = T0_MIN_SUCC_RATE) -> dict:
    """A1 T0 门（绑定）：N=1024/B=30 成功率门（默认阈值 0.30）。

    冻结样本实测（seed=20261009）：F1=15/30，F2=21/30，均过门。
    R 目标带（0.65–0.8）只记录（``R_in_target_zone``），不拦截
    （F1 小 N 处 R≈0.58 系冻结 gap 表所致）。
    不过门不开矩阵（调用方 ``run_a1_cell`` 凭本记录拦截）。
    """
    rr = rate_bin(wp, N, M)
    if not rr["feasible"]:
        return {"pass": False, "WP": wp, "M": float(M), "N": int(N),
                "B": int(B), "reason": rr["reason"], "R": rr["R"],
                "K": rr["K"], "m": rr["m"]}
    p = p_op_of(wp)
    code = build_qc_code(N=int(N), m=int(rr["m"]))
    H = code["H"]
    succ = 0
    t_list: list[float] = []
    Nn = int(N)
    for b in range(int(B)):
        rng = np.random.default_rng(int(seed) + b)
        x = rng.integers(0, 2, Nn).astype(np.uint8)
        e = (rng.random(Nn) < p).astype(np.uint8)
        y = np.bitwise_xor(x, e)
        syn = (H @ x) % 2
        xh, t_dec = _bp_decode_block(H=H, syn=np.asarray(syn), y=y, p=p)
        t_list.append(t_dec)
        if bool(np.array_equal((H @ xh) % 2, np.asarray(syn).ravel())
                and np.array_equal(xh, x)):
            succ += 1
    rate = succ / max(int(B), 1)
    ok = bool(rate >= float(min_succ_rate))
    return {"pass": ok, "WP": wp, "M": float(M), "N": int(N), "B": int(B),
            "seed": int(seed), "R": rr["R"], "K": int(rr["K"]),
            "m": int(rr["m"]),
            "R_in_target_zone": bool(R_TARGET_ZONE[0] <= rr["R"]
                                     <= R_TARGET_ZONE[1]),
            "success": int(succ), "success_rate": float(rate),
            "min_succ_rate": float(min_succ_rate),
            "code_hash": code["code_hash"], "qc_meta": code["meta"],
            "median_T_dec": float(np.median(t_list)) if t_list else 0.0,
            "reason": "" if ok else (f"T0 success gate FAIL: {succ}/{B} "
                                    f"< {min_succ_rate}")}


# ---------------- 本地 SC（njit；与 sibling 同 f/g/调度口径） ----------------

def _sc_kernels():
    import numba

    @numba.njit(cache=True)
    def _left(alpha, depth, node, S):
        half = S >> 1
        base = node * S
        for j in range(half):
            l = alpha[depth, base + j]
            r = alpha[depth, base + j + half]
            sl = 1.0 if l >= 0.0 else -1.0
            sr = 1.0 if r >= 0.0 else -1.0
            al = l if l >= 0.0 else -l
            ar = r if r >= 0.0 else -r
            alpha[depth + 1, (node << 1) * half + j] = (
                sl * sr * (al if al <= ar else ar))

    @numba.njit(cache=True)
    def _right(alpha, beta, depth, node, S):
        half = S >> 1
        base = node * S
        lb = (node << 1) * half
        rb = ((node << 1) + 1) * half
        for j in range(half):
            l = alpha[depth, base + j]
            r = alpha[depth, base + j + half]
            u = beta[depth + 1, lb + j] & 1
            alpha[depth + 1, rb + j] = r - (2.0 * u - 1.0) * l

    @numba.njit(cache=True)
    def _merge(beta, depth, node, S):
        half = S >> 1
        base = node * S
        for j in range(half):
            beta[depth, base + j] = (
                beta[depth + 1, base + j] ^ beta[depth + 1, base + j + half])
            beta[depth, base + j + half] = beta[depth + 1, base + j + half]

    @numba.njit(cache=True)
    def _sc_nb(llr_ch, is_info, froz_vals, n_log):
        N = llr_ch.shape[0]
        alpha = np.zeros((n_log + 1, N), dtype=np.float32)
        beta = np.zeros((n_log + 1, N), dtype=np.int8)
        for j in range(N):
            alpha[0, j] = np.float32(llr_ch[j])
        stage = np.zeros(n_log + 1, dtype=np.int64)
        depth = 0
        node = 0
        for pos in range(N):
            while depth < n_log:
                s = stage[depth]
                S = N >> depth
                if s == 0:
                    _left(alpha, depth, node, S)
                else:
                    _right(alpha, beta, depth, node, S)
                depth += 1
                node = (node << 1) + s
                stage[depth] = 0
            leaf = alpha[n_log, pos]
            if is_info[pos] != 0:
                bit = 0 if leaf >= 0.0 else 1
            else:
                bit = int(froz_vals[pos] & 1)
            beta[n_log, pos] = np.int8(bit)
            while depth > 0:
                node >>= 1
                depth -= 1
                if stage[depth] == 0:
                    stage[depth] = 1
                    break
                _merge(beta, depth, node, N >> depth)
                stage[depth] = 0
        return beta[n_log, :].copy()

    return _sc_nb


_SC_NB = None


def sc_decode_nb(chan_llr: np.ndarray, is_info: np.ndarray,
                 frozen_vals: np.ndarray, n_log: int) -> np.ndarray:
    """本地 SC 译码（uhat, int8）：f/g/树调度与 sibling ``polar_core``
    逐行同口径（min-sum f，g = r−(2u−1)·l，float32），决策应与
    ``scl_decode_batch(..., 1)`` 比特一致（见测试 oracle）。"""
    global _SC_NB
    if _SC_NB is None:
        _SC_NB = _sc_kernels()
    llr = np.asarray(chan_llr, dtype=np.float64).ravel()
    info = np.asarray(is_info, dtype=np.uint8).ravel()
    fv = np.asarray(frozen_vals, dtype=np.uint8).ravel()
    n = int(n_log)
    if llr.shape[0] != (1 << n) or info.shape[0] != llr.shape[0]:
        raise ValueError("SC shape mismatch")
    return np.asarray(_SC_NB(llr, info, fv, n), dtype=np.int8)


def _sibling_polar():
    import sys as _sys
    if runner.SIBLING_ROOT not in _sys.path:
        _sys.path.insert(0, runner.SIBLING_ROOT)
    import importlib as _il
    return _il.import_module("low_dim_opt.core.polar_core")


# ---------------- 落盘/记账 helpers ----------------

def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def _append_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _sanitize_blocks(path: Path) -> set[int]:
    """Cell 文件自愈：丢弃空行/不可解析行（kill 残留的 torn 尾），
    返回已落盘块号集；重写仅在存在坏行时发生（计数由调用方记录）。"""
    if not path.exists():
        return set()
    good: list[str] = []
    blocks: set[int] = set()
    dirty = False
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                blocks.add(int(json.loads(line).get("block", -1)))
                good.append(line if line.endswith("\n") else line + "\n")
            except Exception:
                dirty = True
    if dirty:
        with path.open("w", encoding="utf-8") as fh:
            fh.writelines(good)
    return blocks


def _check_row(row: dict) -> dict:
    missing = [k for k in runner.ROW_KEYS if k not in row]
    if missing:
        raise ValueError(f"C3M row missing ROW_KEYS {missing}")
    if row.get("status") not in runner.ALLOWED_STATUSES:
        raise ValueError(f"status {row.get('status')!r} not in "
                         f"{runner.ALLOWED_STATUSES}")
    if "frozen_hash" not in row:
        raise ValueError("C3M row missing frozen_hash")
    return row


def _summarize_cell(*, method: str, variant: str, wp: str, N: int, M: float,
                    B: int, seed: int, R: float, m: int, K: int,
                    kept_per_success: float, code_hash: str,
                    frozen_hash: str, out: Path,
                    t_list: list[float], status: str = "ok",
                    detail: str = "") -> dict:
    """由落盘行汇总 cell（Net_seg 经 ``net_of_cell`` + 逐块精确和双算核对）。"""
    rows = [json.loads(line) for line in out.read_text(
        encoding="utf-8").splitlines() if line.strip()]
    if not t_list and rows:
        # 续跑复用：已满行直接由行重计（T_dec 由行累加，不重译码）。
        t_list = [float(r.get("T_dec", 0.0)) for r in rows]
    succ = sum(int(r.get("ver", 0)) for r in rows)
    fail = int(B) - int(succ)
    total_lec = sum(float(r.get("L_EC", 0)) for r in rows)
    mean_lec = total_lec / max(int(B), 1)
    p = p_op_of(wp)
    C_cell = max(float(C_TOTAL_PLAN), float(int(B) * int(N)))
    net = runner.net_of_cell(
        kept_bits=float(kept_per_success), L_EC_bits=float(mean_lec),
        tag_bits=TAG, n_fail=fail, n_blocks=int(B), C_total=C_cell,
        N=int(N), n_undetected=0, h_op=h2(p), I_op=1.0 - h2(p))
    # 逐块精确和核对（B·mean = ΣL_EC，故须一致；fp 容差内）。
    exact = sum((float(r["kept"]) - float(r["L_EC"]) - float(r["tag"])
                 if int(r["ver"]) == 1 else -float(r["L_EC"]))
                for r in rows)
    if abs(float(exact) - float(net["Net_seg"])) > 1e-6 * max(
            1.0, abs(float(net["Net_seg"]))):
        raise ValueError(f"Net_seg mismatch: exact={exact} vs "
                         f"net_of_cell={net['Net_seg']}")
    t_arr = np.asarray(t_list, dtype=float) if t_list else np.zeros(0)
    lb_tot = sum(int(r.get("L_B", 0)) for r in rows)
    return {"method": method, "variant": variant, "WP": wp, "N": int(N),
            "M": float(M), "B": int(B), "rows": len(rows),
            "success": int(succ), "undetected": 0, "status": status,
            "detail": detail, "R": float(R), "m": int(m), "K": int(K),
            "kept_per_success": float(kept_per_success),
            "lec_mean": float(mean_lec), "lec_total": float(total_lec),
            "L_B_total": int(lb_tot),
            "C_total": float(C_cell),
            "N_valid": bool(math.floor(C_cell / int(N)) >= 300),
            "median_T_dec": float(np.median(t_arr)) if t_arr.size else 0.0,
            "p50_T_dec": float(np.median(t_arr)) if t_arr.size else 0.0,
            "p95_T_dec": float(np.percentile(t_arr, 95)) if t_arr.size else 0.0,
            "max_T_dec": float(t_arr.max()) if t_arr.size else 0.0,
            "total_T_dec": float(t_arr.sum()) if t_arr.size else 0.0,
            "code_hash": code_hash, "frozen_hash": frozen_hash,
            "net": net}


# ---------------- 单块 row 构造器（串行/并行共用，行模式逐字一致） ----------------

def _a1_block(*, H, N: int, m: int, K: int, R: float, p: float,
              code_hash: str, wp: str, M: float, seed: int,
              kept_per_success: float, b: int) -> tuple[dict, float]:
    """A1 单块：抽样→BP→verdict→两级记账行（跑到 verdict，无超时）。"""
    N = int(N)
    rng = np.random.default_rng(int(seed) + int(b))
    x = rng.integers(0, 2, N).astype(np.uint8)
    e = (rng.random(N) < float(p)).astype(np.uint8)
    y = np.bitwise_xor(x, e)
    n_marked = int(np.sum(e))  # 合成真值（见 CALIBER_NOTE）
    syn = (H @ x) % 2
    xh, t_dec = _bp_decode_block(H=H, syn=np.asarray(syn), y=y, p=float(p))
    good = bool(np.array_equal((H @ xh) % 2, np.asarray(syn).ravel())
                and np.array_equal(xh, x))
    lb = n_marked if good else 0
    lec = int(m) + int(lb)
    row = _check_row({
        "method": "A1", "N": N, "block": int(b),
        "ver": int(good), "u": 0,
        "kept": float(kept_per_success) if good else 0.0,
        "L_EC": lec, "tag": TAG if good else 0,
        "T_dec": float(t_dec),
        "code_hash": code_hash, "frozen_hash": code_hash,
        "undetected": False,
        "status": "ok" if good else "decode_failed",
        "WP": wp, "M": float(M), "seed": int(seed),
        "R": float(R), "m": int(m), "K": int(K),
        "L_A": int(m), "L_B": int(lb), "n_marked": int(n_marked),
        "detail": CALIBER_NOTE})
    return row, float(t_dec)


def _a2_block(*, variant: str, N: int, m: int, K: int, R: float,
              p: float, mask: np.ndarray, n_log: int, llr_mag: float,
              frozen_hash: str, wp: str, M: float, seed: int,
              kept_per_success: float, b: int,
              Pmod=None) -> tuple[dict, float]:
    """A2 单块：抽样→冻结披露→SC/SCL8→verdict→两级记账行（无超时）。

    ``Pmod`` 为 sibling 模块（SCL8 必需；SC 时用本地编码）。
    译码器异常按失败块记（verdict 仍落盘）。
    """
    N = int(N)
    rng = np.random.default_rng(int(seed) + int(b))
    xt = rng.integers(0, 2, N).astype(np.int8)
    e = (rng.random(N) < float(p)).astype(np.int8)
    yt = np.bitwise_xor(xt, e)
    n_marked = int(np.sum(e))  # 合成真值（见 CALIBER_NOTE）
    if Pmod is not None:
        ua = np.asarray(Pmod.polar_encode(xt, int(n_log))).ravel()
    else:
        ua = np.asarray(_polar_encode_local(xt, int(n_log))).ravel()
    frz = np.where(np.asarray(mask) == 0)[0]
    fv = np.zeros(N, dtype=np.uint8)
    fv[frz] = np.asarray(ua).ravel()[frz]
    llr = np.where(yt == 0, float(llr_mag), -float(llr_mag)).astype(float)
    try:
        if variant == "SC":
            uh, t_dec = _a2_decode_sc(llr=llr, mask=mask, fv=fv,
                                      n_log=int(n_log))
            xh = _polar_encode_local(np.asarray(uh).astype(np.int8),
                                     int(n_log))
        else:
            uh, t_dec = _a2_decode_scl8(llr=llr, mask=mask, fv=fv,
                                        n_log=int(n_log))
            xh = np.asarray(Pmod.polar_encode(
                np.asarray(uh).astype(np.int8), int(n_log))).astype(np.int8)
    except Exception as exc:  # 译码器异常按失败块记（verdict 仍落盘）
        return _check_row({
            "method": "A2", "N": N, "block": int(b), "ver": 0, "u": 0,
            "kept": 0.0, "L_EC": int(m), "tag": 0, "T_dec": 0.0,
            "code_hash": frozen_hash, "frozen_hash": frozen_hash,
            "undetected": False, "status": "decode_failed",
            "WP": wp, "M": float(M), "seed": int(seed),
            "R": float(R), "m": int(m), "K": int(K),
            "L_A": int(m), "L_B": 0, "n_marked": int(n_marked),
            "variant": variant,
            "detail": f"{CALIBER_NOTE}; decoder-error: "
                      f"{type(exc).__name__}: {exc}"}), 0.0
    good = bool(np.array_equal(np.asarray(xh).astype(np.int8), xt))
    lb = n_marked if good else 0
    lec = int(m) + int(lb)
    row = _check_row({
        "method": "A2", "N": N, "block": int(b),
        "ver": int(good), "u": 0,
        "kept": float(kept_per_success) if good else 0.0,
        "L_EC": lec, "tag": TAG if good else 0,
        "T_dec": float(t_dec),
        "code_hash": frozen_hash, "frozen_hash": frozen_hash,
        "undetected": False,
        "status": "ok" if good else "decode_failed",
        "WP": wp, "M": float(M), "seed": int(seed),
        "R": float(R), "m": int(m), "K": int(K),
        "L_A": int(m), "L_B": int(lb), "n_marked": int(n_marked),
        "variant": variant, "detail": CALIBER_NOTE})
    return row, float(t_dec)


# ---------------- A1 cell ----------------

def run_a1_cell(wp: str, N: int, M: float, kept_per_success: float, B: int,
                seed: int, out: Path, *, t0_result: dict | None = None,
                ) -> dict:
    """A1 两级 cell（QC-BP level-A + 明文 level-B；无超时，跑到 verdict）。

    ``t0_result`` 为 ``t0_gate(wp, M)`` 记录（同 wp/M）；缺省则现场执行；
    未过门 → ``{"status": "t0-gated", "rows": 0}``（不开矩阵，零译码）。
    ``kept_per_success`` 由调用方按 ``N·H_A_op`` 传入（必填）。
    """
    N, B = int(N), int(B)
    if float(kept_per_success) < 0:
        raise ValueError("kept_per_success must be >= 0")
    t0 = t0_gate(wp, float(M)) if t0_result is None else dict(t0_result)
    if not t0.get("pass"):
        return {"method": "A1", "variant": "QC-BP", "WP": wp, "N": N,
                "M": float(M), "B": B, "rows": 0, "success": 0,
                "undetected": 0, "status": "t0-gated",
                "detail": f"T0 gate not passed: {t0.get('reason', '')}",
                "t0": t0, "net": None}
    rr = rate_bin(wp, N, float(M))
    if not rr["feasible"]:
        return {"method": "A1", "variant": "QC-BP", "WP": wp, "N": N,
                "M": float(M), "B": B, "rows": 0, "success": 0,
                "undetected": 0, "status": "infeasible",
                "detail": rr["reason"], "t0": t0, "net": None}
    p = p_op_of(wp)
    code = build_qc_code(N=N, m=int(rr["m"]))
    H = code["H"]
    code_hash = code["code_hash"]
    t_list: list[float] = []
    start = _jsonl_count(out)
    for b in range(start, B):
        rng = np.random.default_rng(int(seed) + b)
        x = rng.integers(0, 2, N).astype(np.uint8)
        e = (rng.random(N) < p).astype(np.uint8)
        y = np.bitwise_xor(x, e)
        n_marked = int(np.sum(e))  # 合成真值（见 CALIBER_NOTE）
        syn = (H @ x) % 2
        xh, t_dec = _bp_decode_block(H=H, syn=np.asarray(syn), y=y, p=p)
        t_list.append(t_dec)
        good = bool(np.array_equal((H @ xh) % 2, np.asarray(syn).ravel())
                    and np.array_equal(xh, x))
        lb = n_marked if good else 0
        lec = int(rr["m"]) + int(lb)
        _append_rows(out, [_check_row({
            "method": "A1", "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept_per_success) if good else 0.0,
            "L_EC": lec, "tag": TAG if good else 0,
            "T_dec": float(t_dec),
            "code_hash": code_hash, "frozen_hash": code_hash,
            "undetected": False,
            "status": "ok" if good else "decode_failed",
            "WP": wp, "M": float(M), "seed": int(seed),
            "R": float(rr["R"]), "m": int(rr["m"]), "K": int(rr["K"]),
            "L_A": int(rr["m"]), "L_B": int(lb), "n_marked": int(n_marked),
            "detail": CALIBER_NOTE})])
    cell = _summarize_cell(method="A1", variant="QC-BP", wp=wp, N=N,
                           M=float(M), B=B, seed=int(seed), R=rr["R"],
                           m=int(rr["m"]), K=int(rr["K"]),
                           kept_per_success=float(kept_per_success),
                           code_hash=code_hash, frozen_hash=code_hash,
                           out=out, t_list=t_list)
    cell["t0"] = {"pass": True, "success": t0.get("success"),
                  "success_rate": t0.get("success_rate"),
                  "code_hash": t0.get("code_hash")}
    cell["qc_meta"] = code["meta"]
    return cell


# ---------------- A2 cell ----------------

def _a2_decode_sc(*, llr: np.ndarray, mask: np.ndarray,
                  fv: np.ndarray, n_log: int) -> tuple[np.ndarray, float]:
    """SC 变体（本地 njit；跑到 verdict，无超时）。"""
    t0 = time.perf_counter()
    uh = sc_decode_nb(np.asarray(llr, dtype=float), np.asarray(mask),
                      np.asarray(fv), int(n_log))
    return np.asarray(uh).astype(np.int8), time.perf_counter() - t0


def _a2_decode_scl8(*, llr: np.ndarray, mask: np.ndarray,
                    fv: np.ndarray, n_log: int) -> tuple[np.ndarray, float]:
    """SCL8 变体（sibling ``polar_core`` 只读调用）。"""
    P = _sibling_polar()
    t0 = time.perf_counter()
    uh = P.scl_decode_batch(np.asarray(llr, dtype=float).reshape(1, -1),
                            np.asarray(mask, dtype=np.uint8),
                            np.asarray(fv, dtype=np.uint8).reshape(1, -1),
                            int(n_log), int(A2_LIST_SIZE))
    return np.asarray(uh[0]).astype(np.int8), time.perf_counter() - t0


def run_a2_cell(wp: str, N: int, M: float, variant: str,
                kept_per_success: float, B: int, seed: int, out: Path,
                *, construction: dict | None = None) -> dict:
    """A2 两级 cell（``variant`` ∈ {"SC","SCL8"}；冻结集按 p_op 重算 + hash）。

    开门检查 = ``polar_construction_check``（绑定）；SCL8 的 sibling 缺失 →
    ``unavailable`` 行透传（不断言失败）。level-B 明文口径同 A1。
    无超时，跑到 verdict。
    """
    if variant not in ("SC", "SCL8"):
        raise ValueError(f"variant must be SC/SCL8, got {variant!r}")
    N, B = int(N), int(B)
    chk = polar_construction_check(wp, N, float(M)) \
        if construction is None else dict(construction)
    if not chk.get("ok"):
        return {"method": "A2", "variant": variant, "WP": wp, "N": N,
                "M": float(M), "B": B, "rows": 0, "success": 0,
                "undetected": 0, "status": "construction-gated",
                "detail": str(chk.get("reason", "")), "net": None}
    K, m = int(chk["K"]), int(chk["m"])
    frozen, info = (tuple(chk["frozen"]), tuple(chk["info"])) \
        if "frozen" in chk else bhattacharyya_frozen_set(N, K, p_op_of(wp))
    frozen_hash = str(chk.get("frozen_hash") or frozen_hash_of(
        f"C3M-A2|wp={wp}|n={N}|K={K}|p={p_op_of(wp)}|F={list(frozen)}"))
    p = p_op_of(wp)
    mask = np.zeros(N, dtype=np.uint8)
    mask[np.asarray(info, dtype=np.int64)] = 1
    n_log = int(math.log2(N))
    if (1 << n_log) != N:
        raise ValueError(f"A2 requires power-of-two N, got {N}")
    llr_mag = math.log(max(1.0 - p, 1e-300) / max(p, 1e-300))
    try:
        Pmod = _sibling_polar() if variant == "SCL8" else None
    except Exception as exc:
        if variant == "SCL8":
            start0 = _jsonl_count(out)
            rows = [{"method": "A2", "N": N, "block": b,
                     "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
                     "T_dec": 0.0, "code_hash": "", "frozen_hash": "",
                     "undetected": False, "status": "unavailable",
                     "detail": f"sibling polar_core missing: {exc}",
                     "WP": wp, "M": float(M), "seed": int(seed),
                     "R": float(chk.get("R", 0.0)), "m": m, "K": K,
                     "L_A": m, "L_B": 0, "n_marked": 0,
                     "variant": variant} for b in range(start0, B)]
            _append_rows(out, [_check_row(r) for r in rows])
            return {"method": "A2", "variant": variant, "WP": wp, "N": N,
                    "M": float(M), "B": B, "rows": _jsonl_count(out),
                    "success": 0,
                    "undetected": 0, "status": "unavailable",
                    "detail": f"sibling polar_core missing: {exc}",
                    "code_hash": "", "frozen_hash": "",
                    "median_T_dec": 0.0, "total_T_dec": 0.0, "net": None}
        raise
    t_list: list[float] = []
    start = _jsonl_count(out)
    for b in range(start, B):
        rng = np.random.default_rng(int(seed) + b)
        xt = rng.integers(0, 2, N).astype(np.int8)
        e = (rng.random(N) < p).astype(np.int8)
        yt = np.bitwise_xor(xt, e)
        n_marked = int(np.sum(e))  # 合成真值（见 CALIBER_NOTE）
        ua = np.asarray(Pmod.polar_encode(xt, n_log)
                        if Pmod is not None else _polar_encode_local(
                            xt, n_log)).ravel()
        frz = np.where(mask == 0)[0]
        fv = np.zeros(N, dtype=np.uint8)
        fv[frz] = np.asarray(ua).ravel()[frz]
        llr = np.where(yt == 0, llr_mag, -llr_mag).astype(float)
        try:
            if variant == "SC":
                uh, t_dec = _a2_decode_sc(llr=llr, mask=mask, fv=fv,
                                          n_log=n_log)
                xh = _polar_encode_local(np.asarray(uh).astype(np.int8),
                                         n_log)
            else:
                uh, t_dec = _a2_decode_scl8(llr=llr, mask=mask, fv=fv,
                                            n_log=n_log)
                xh = np.asarray(Pmod.polar_encode(
                    np.asarray(uh).astype(np.int8), n_log)).astype(np.int8)
        except Exception as exc:  # 译码器异常按失败块记（verdict 仍落盘）
            t_dec = 0.0
            xh = np.full(N, -1, dtype=np.int8)
            good = False
            lb, lec = 0, m
            _append_rows(out, [_check_row({
                "method": "A2", "N": N, "block": b, "ver": 0, "u": 0,
                "kept": 0.0, "L_EC": lec, "tag": 0, "T_dec": 0.0,
                "code_hash": frozen_hash, "frozen_hash": frozen_hash,
                "undetected": False, "status": "decode_failed",
                "WP": wp, "M": float(M), "seed": int(seed),
                "R": float(chk.get("R", 0.0)), "m": m, "K": K,
                "L_A": m, "L_B": 0, "n_marked": int(n_marked),
                "variant": variant,
                "detail": f"{CALIBER_NOTE}; decoder-error: "
                          f"{type(exc).__name__}: {exc}"})])
            t_list.append(float(t_dec))
            continue
        t_list.append(float(t_dec))
        good = bool(np.array_equal(np.asarray(xh).astype(np.int8), xt))
        lb = n_marked if good else 0
        lec = m + int(lb)
        _append_rows(out, [_check_row({
            "method": "A2", "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept_per_success) if good else 0.0,
            "L_EC": lec, "tag": TAG if good else 0,
            "T_dec": float(t_dec),
            "code_hash": frozen_hash, "frozen_hash": frozen_hash,
            "undetected": False,
            "status": "ok" if good else "decode_failed",
            "WP": wp, "M": float(M), "seed": int(seed),
            "R": float(chk.get("R", 0.0)), "m": m, "K": K,
            "L_A": m, "L_B": int(lb), "n_marked": int(n_marked),
            "variant": variant, "detail": CALIBER_NOTE})])
    cell = _summarize_cell(method="A2", variant=variant, wp=wp, N=N,
                           M=float(M), B=B, seed=int(seed),
                           R=float(chk.get("R", 0.0)), m=m, K=K,
                           kept_per_success=float(kept_per_success),
                           code_hash=frozen_hash, frozen_hash=frozen_hash,
                           out=out, t_list=t_list)
    return cell


def _polar_encode_local(u: np.ndarray, n_log: int) -> np.ndarray:
    """本地 Polar 编码（``x = u·F^{⊗n}``；SC 变体自持，免 sibling 依赖）。"""
    x = np.asarray(u, dtype=np.int8).copy()
    n = int(n_log)
    N = 1 << n
    if x.shape[0] != N:
        raise ValueError("encode length mismatch")
    step = 1
    for _ in range(n):
        for i in range(0, N, 2 * step):
            x[i:i + step] = np.bitwise_xor(x[i:i + step],
                                           x[i + step:i + 2 * step])
        step *= 2
    return x


# ---------------- F3（二进制两级不可行） ----------------

def f3_binary_infeasible(*, N: int, M: float = 2.5) -> dict:
    """F3 二进制两级：``infeasible-by-construction``（不跑、零行、非 missing）。

    F3（k=2 exploratory）LSB 面 p≈0.4741 → ``R = 1−h2(p)−gap−margin < 0``，
    ``K<1``，冻结码率函数直接 infeasible。记录原因，不执行任何译码。
    """
    p = float(bakeoff.WORKPOINTS["F3"]["p"]) if bakeoff else 0.4741
    rr = rate_bin("F3", int(N), float(M)) if bakeoff else {"R": -0.08,
                                                          "K": -90,
                                                          "m": int(N) + 90,
                                                          "feasible": False,
                                                          "reason": ""}
    return {"method": "A1/A2-bin", "variant": "two-level",
            "WP": "F3", "N": int(N), "M": float(M),
            "B": 0, "rows": 0, "success": 0, "undetected": 0,
            "status": "infeasible-by-construction",
            "detail": (f"F3 binary two-level infeasible-by-construction: "
                       f"LSB-plane p≈{p:.4f}, R={rr['R']:.4f} < 0 "
                       f"(K={rr['K']}); no decode attempted, not missing"),
            "R": float(rr["R"]), "K": int(rr["K"]), "m": int(rr["m"]),
            "code_hash": "", "frozen_hash": "", "net": None}


# ---------------- 并行分片（同科学输入；纯工程加速） ----------------

_WPAR: dict = {}


def _par_init(spec: dict) -> None:
    """Worker 初始化：按标量 spec 重建码（确定性冻结构造；每 worker 每格一次）。

    ``spec`` 只含标量（方法/变体/WP/N/m/K/R/p/seed/kept/hash），无大对象
    传递；QC/冻结集在 worker 内重建（与串行同构造，hash 一致）。
    """
    _WPAR.clear()
    _WPAR["spec"] = dict(spec)
    if spec["method"] == "A1":
        _WPAR["H"] = build_qc_code(N=int(spec["N"]),
                                   m=int(spec["m"]))["H"]
    else:
        frozen, info = bhattacharyya_frozen_set(int(spec["N"]),
                                                int(spec["K"]),
                                                float(spec["p"]))
        mask = np.zeros(int(spec["N"]), dtype=np.uint8)
        mask[np.asarray(info, dtype=np.int64)] = 1
        _WPAR["mask"] = mask
        _WPAR["P"] = _sibling_polar() if spec["variant"] == "SCL8" else None


def _par_block(b: int) -> dict:
    """Worker 单块：与串行同 ``_a1_block``/``_a2_block``（行模式一致）。"""
    spec = _WPAR["spec"]
    b = int(b)
    if spec["method"] == "A1":
        row, _t = _a1_block(
            H=_WPAR["H"], N=int(spec["N"]), m=int(spec["m"]),
            K=int(spec["K"]), R=float(spec["R"]), p=float(spec["p"]),
            code_hash=str(spec["code_hash"]), wp=str(spec["wp"]),
            M=float(spec["M"]), seed=int(spec["seed"]),
            kept_per_success=float(spec["kept"]), b=b)
    else:
        row, _t = _a2_block(
            variant=str(spec["variant"]), N=int(spec["N"]),
            m=int(spec["m"]), K=int(spec["K"]), R=float(spec["R"]),
            p=float(spec["p"]), mask=_WPAR["mask"],
            n_log=int(spec["n_log"]), llr_mag=float(spec["llr_mag"]),
            frozen_hash=str(spec["frozen_hash"]), wp=str(spec["wp"]),
            M=float(spec["M"]), seed=int(spec["seed"]),
            kept_per_success=float(spec["kept"]), b=b,
            Pmod=_WPAR["P"])
    return row


def run_cell_parallel(method: str, variant: str, wp: str, N: int, M: float,
                      kept_per_success: float, B: int, seed: int, out: Path,
                      *, workers: int = 8,
                      t0_cache: dict | None = None) -> dict:
    """并行分片 cell（与串行同科学输入/种子/行模式；纯工程加速）。

    开门条件与串行逐字一致（A1: T0；A2: 构造检查 + SCL8 缺失透传）；
    缺块由 worker 池补算，主进程串行落盘（无并发写）；已落盘块跳过
    （自愈 + 续跑）。无超时。
    """
    N, B = int(N), int(B)
    if float(kept_per_success) < 0:
        raise ValueError("kept_per_success must be >= 0")
    if method == "A1":
        t0 = None
        if t0_cache is not None and (wp, float(M)) in t0_cache:
            t0 = dict(t0_cache[(wp, float(M))])
        else:
            t0 = t0_gate(wp, float(M))
            if t0_cache is not None:
                t0_cache[(wp, float(M))] = t0
        if not t0.get("pass"):
            return {"method": "A1", "variant": "QC-BP", "WP": wp, "N": N,
                    "M": float(M), "B": B, "rows": 0, "success": 0,
                    "undetected": 0, "status": "t0-gated",
                    "detail": f"T0 gate not passed: {t0.get('reason', '')}",
                    "t0": t0, "net": None}
        rr = rate_bin(wp, N, float(M))
        if not rr["feasible"]:
            return {"method": "A1", "variant": "QC-BP", "WP": wp, "N": N,
                    "M": float(M), "B": B, "rows": 0, "success": 0,
                    "undetected": 0, "status": "infeasible",
                    "detail": rr["reason"], "t0": t0, "net": None}
        code = build_qc_code(N=N, m=int(rr["m"]))
        spec = {"method": "A1", "variant": "QC-BP", "wp": wp, "N": N,
                "m": int(rr["m"]), "K": int(rr["K"]), "R": float(rr["R"]),
                "p": p_op_of(wp), "M": float(M), "seed": int(seed),
                "kept": float(kept_per_success),
                "code_hash": code["code_hash"],
                "frozen_hash": code["code_hash"]}
        extra = {"t0": {"pass": True, "success": t0.get("success"),
                        "success_rate": t0.get("success_rate"),
                        "code_hash": t0.get("code_hash")},
                 "qc_meta": code["meta"]}
    elif method == "A2":
        if variant not in ("SC", "SCL8"):
            raise ValueError(f"variant must be SC/SCL8, got {variant!r}")
        chk = polar_construction_check(wp, N, float(M))
        if not chk.get("ok"):
            return {"method": "A2", "variant": variant, "WP": wp, "N": N,
                    "M": float(M), "B": B, "rows": 0, "success": 0,
                    "undetected": 0, "status": "construction-gated",
                    "detail": str(chk.get("reason", "")), "net": None}
        try:
            _sibling_polar() if variant == "SCL8" else None
        except Exception as exc:
            present = _sanitize_blocks(out)
            rows = [{"method": "A2", "N": N, "block": b,
                     "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
                     "T_dec": 0.0, "code_hash": "", "frozen_hash": "",
                     "undetected": False, "status": "unavailable",
                     "detail": f"sibling polar_core missing: {exc}",
                     "WP": wp, "M": float(M), "seed": int(seed),
                     "R": float(chk.get("R", 0.0)), "m": int(chk["m"]),
                     "K": int(chk["K"]), "L_A": int(chk["m"]), "L_B": 0,
                     "n_marked": 0, "variant": variant}
                    for b in range(B) if b not in present]
            _append_rows(out, [_check_row(r) for r in rows])
            return {"method": "A2", "variant": variant, "WP": wp, "N": N,
                    "M": float(M), "B": B, "rows": _jsonl_count(out),
                    "success": 0, "undetected": 0, "status": "unavailable",
                    "detail": f"sibling polar_core missing: {exc}",
                    "code_hash": "", "frozen_hash": "",
                    "median_T_dec": 0.0, "total_T_dec": 0.0, "net": None}
        p = p_op_of(wp)
        n_log = int(math.log2(N))
        if (1 << n_log) != N:
            raise ValueError(f"A2 requires power-of-two N, got {N}")
        spec = {"method": "A2", "variant": variant, "wp": wp, "N": N,
                "m": int(chk["m"]), "K": int(chk["K"]),
                "R": float(chk.get("R", 0.0)), "p": p, "M": float(M),
                "seed": int(seed), "kept": float(kept_per_success),
                "code_hash": str(chk["frozen_hash"]),
                "frozen_hash": str(chk["frozen_hash"]),
                "n_log": n_log,
                "llr_mag": math.log(max(1.0 - p, 1e-300)
                                    / max(p, 1e-300))}
        extra = {}
    else:
        raise ValueError(f"unknown M-wave method {method!r}")
    present = _sanitize_blocks(out)
    missing = [b for b in range(B) if b not in present]
    if missing:
        with cf.ProcessPoolExecutor(
                max_workers=int(workers), initializer=_par_init,
                initargs=(spec,)) as ex:
            for row in ex.map(_par_block, missing):
                _append_rows(out, [row])
    cell = _summarize_cell(method=method, variant=spec["variant"], wp=wp,
                           N=N, M=float(M), B=B, seed=int(seed),
                           R=spec["R"], m=spec["m"], K=spec["K"],
                           kept_per_success=float(kept_per_success),
                           code_hash=spec["code_hash"],
                           frozen_hash=spec["frozen_hash"], out=out,
                           t_list=[])
    cell.update(extra)
    return cell


# ---------------- M 锚点 + 网格 ----------------

def _decided(cell: dict) -> bool:
    net = cell.get("net")
    if net is None:
        return False
    B = int(cell.get("B", 0))
    F = int(net.get("F", B))
    S = int(net.get("S_main", 0))
    return F >= 10 and S >= 10


def _cell_out(blocks: Path, wp: str, method: str, variant: str,
              N: int, M: float) -> Path:
    tag = f"{wp}_{method}" + (f"-{variant}" if variant else "") \
        + f"_N{N}_M{M}.jsonl"
    return blocks / tag


def manifest_from_blocks(root: Path, *, B: int = B_FULL,
                         seed: int = SEED,
                         anchor_N: int = ANCHOR_N) -> dict:
    """由已落盘块行重建 manifest（只汇总、不补算；缺行格记 ``short`` 如实）。

    用于长网格的终态/中态盘点：满 B 行格走 ``_summarize_cell``（T_dec 由行
    累加）；不足 B 行记 short（含已跑行汇总 + 缺行数），不触发任何译码。
    """
    from collections import defaultdict
    root = Path(root)
    blocks = root / "blocks"
    cells: list[dict] = []
    anchors: dict = {}
    if blocks.exists():
        for path in sorted(blocks.glob("*.jsonl")):
            stem = path.stem  # {WP}_{method}[-{variant}]_N{N}_M{M}
            try:
                nstr, mstr = stem.rsplit("_N", 1)[1].split("_M")
                N, M = int(nstr), float(mstr)
                if "-A2-" in stem or "_A2-" in stem or stem.split("_")[1] == "A2":
                    method = "A2"
                    rest = stem.split("_A2-")[1] if "_A2-" in stem else ""
                    variant = rest.split("_N")[0] if rest else ""
                else:
                    method = stem.split("_")[1]
                    variant = ""
                    if method == "A1":
                        variant = "QC-BP"
                wp = stem.split("_")[0]
            except Exception:
                continue
            rows = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
            by_block = {}
            for r in rows:
                by_block[int(r.get("block", -1))] = r
            n_rows = len(by_block)
            first = rows[0] if rows else {}
            kept = float(first.get("kept", 0.0) or 0.0)
            if kept <= 0.0:
                okk = [r for r in rows if int(r.get("ver", 0)) == 1]
                kept = float(okk[0]["kept"]) if okk else 0.0
            succ = sum(int(r.get("ver", 0)) for r in by_block.values())
            if method == "A1" and not variant:
                variant = "QC-BP"
            if n_rows >= B:
                try:
                    cell = _summarize_cell(
                        method=method, variant=variant, wp=wp, N=N,
                        M=M, B=B, seed=seed, R=float(first.get("R", 0.0)),
                        m=int(first.get("m", 0)), K=int(first.get("K", 0)),
                        kept_per_success=kept,
                        code_hash=str(first.get("code_hash", "")),
                        frozen_hash=str(first.get("frozen_hash", "")),
                        out=path, t_list=[])
                    rec = dict(cell)
                    rec["manifest_note"] = "full-B recount (no re-decode)"
                except Exception as exc:
                    rec = {"method": method, "variant": variant, "WP": wp,
                           "N": N, "M": M, "B": B, "rows": n_rows,
                           "success": succ, "status": "recount-fail",
                           "detail": f"{type(exc).__name__}: {exc}",
                           "net": None}
            else:
                total_lec = sum(float(r.get("L_EC", 0))
                                for r in by_block.values())
                rec = {"method": method, "variant": variant, "WP": wp,
                       "N": N, "M": M, "B": B, "rows": n_rows,
                       "success": succ, "status": "short",
                       "detail": f"short: {n_rows}/{B} blocks; "
                                 f"missing={B - n_rows} (runnable resume)",
                       "lec_total": total_lec, "net": None}
            cells.append(rec)
    # 锚点 winner 复算（同规则；仅锚点 N 上满 B 双 M 格可决，否则无记录）。
    groups: dict[tuple, dict] = {}
    for c in cells:
        if (c.get("status") != "ok" or c.get("net") is None
                or int(c.get("N", -1)) != int(anchor_N)):
            continue
        key = (c["WP"], c["method"], c.get("variant", ""), int(c["N"]))
        groups.setdefault(key, {})[float(c["M"])] = c
    for (wp, method, variant, _N), grp in groups.items():
        if set(grp) != {2.5, 3.0}:
            continue
        n0, n1 = grp[2.5], grp[3.0]
        nets = {2.5: n0["net"]["Net_seg"], 3.0: n1["net"]["Net_seg"]}
        d25, d30 = _decided(n0), _decided(n1)
        if d25 and not d30:
            winner = 2.5
        elif d30 and not d25:
            winner = 3.0
        elif nets[3.0] > nets[2.5]:
            winner = 3.0
        else:
            winner = 2.5
        note = ""
        if not d25 and not d30:
            note = "both-undecided→freeze-M2.5"
        elif abs(nets[3.0] - nets[2.5]) < 1e-12:
            note = "tie→M2.5"
        anchors[f"{wp}/{method}" + (f"/{variant}" if variant else "")] = {
            "WP": wp, "method": method, "variant": variant,
            "M_winner": winner, "nets": nets,
            "decided": {"2.5": d25, "3.0": d30}, "note": note}
    manifest = {"mode": f"M-wave A1/A2 recount B={B}", "B": B,
                "seed": seed, "cells": cells, "anchors": anchors,
                "events": ["recount-from-blocks (no decode)"]}
    (root / "cells.json").write_text(json.dumps(cells, indent=2),
                                     encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(
        {k: v for k, v in manifest.items() if k != "cells"}, indent=2),
        encoding="utf-8")
    return manifest


def _run_family_cell(wp: str, method: str, variant: str, N: int, M: float,
                     *, B: int, seed: int, out: Path,
                     t0_cache: dict, workers: int = 1) -> dict:
    # 续跑复用：各 run_*_cell 内部按已落盘行数续跑；已满 B 行则零重算汇总。
    # workers>1 走并行分片（同科学输入；纯工程加速）。
    kept = kept_of(wp, N)
    if workers and int(workers) > 1:
        return run_cell_parallel(method, variant, wp, N, float(M), kept,
                                 B, seed, out, workers=int(workers),
                                 t0_cache=t0_cache)
    if method == "A1":
        key = (wp, float(M))
        if key not in t0_cache:
            t0_cache[key] = t0_gate(wp, float(M))
        return run_a1_cell(wp, N, float(M), kept, B, seed, out,
                           t0_result=t0_cache[key])
    if method == "A2":
        return run_a2_cell(wp, N, float(M), variant, kept, B, seed, out)
    raise ValueError(f"unknown M-wave method {method!r}")


def select_M_anchor_m(wp: str, method: str, variant: str = "", *,
                      B: int = B_FULL, seed: int = SEED,
                      out_dir: Path, workers: int = 1) -> dict:
    """M 锚点（M 波）：只在 N=16384 对 M∈{2.5,3.0} 二选一（按 Net_seg），
    选定后冻结用于该（WP,方法[,变体]）行其余 N（同 bakeoff 冻结映射）。

    两格均未定 → freeze-M2.5（注记）；Net 并列（差 <1e-12）→ M2.5。
    """
    out_dir = Path(out_dir)
    t0_cache: dict = {}
    results: dict[float, dict] = {}
    for M in M_LADDER:
        out = _cell_out(out_dir, wp, method, variant, ANCHOR_N, M)
        cell = _run_family_cell(wp, method, variant, ANCHOR_N, M,
                                B=B, seed=seed, out=out,
                                t0_cache=t0_cache, workers=workers)
        results[M] = cell
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
    return {"WP": wp, "method": method, "variant": variant, "N": ANCHOR_N,
            "B": B, "M_winner": winner, "nets": nets, "decided": decided,
            "note": note, "cells": results}


def run_grid_m(*, root: Path, B: int = B_FULL, seed: int = SEED,
               methods: tuple = ("A1", "A2"),
               variants: tuple = ("SC", "SCL8"),
               workpoints: tuple = ("F1", "F2"),
               Ns: tuple = N_GRID, workers: int = 1) -> dict:
    """M 波 A1/A2 网格执行（F1/F2×N；F3 记 infeasible-by-construction 不跑）。

    落盘 ``blocks/*.jsonl`` + ``cells.json`` + ``anchors.json`` +
    ``manifest.json``；append-only，已满 B 行格直接汇总复用。
    无 per-block 超时；撞墙（异常）如实记 ``short``/原状态。
    """
    root = Path(root)
    blocks = root / "blocks"
    blocks.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"mode": f"M-wave A1/A2 B={B}", "B": B, "seed": seed,
                      "methods": list(methods), "variants": list(variants),
                      "workpoints": list(workpoints), "Ns": list(Ns),
                      "cells": [], "anchors": {}, "events": []}
    t0_cache: dict = {}
    for wp in workpoints:
        if wp == "F3":
            for N in Ns:
                for method in methods:
                    vlist = (list(variants) if method == "A2" else ["", ])
                    for v in vlist:
                        manifest["cells"].append(
                            {**f3_binary_infeasible(N=N), "method": method,
                             "variant": v, "anchor": False})
            manifest["events"].append(
                "F3 binary two-level: infeasible-by-construction (no run)")
            continue
        fams: list[tuple[str, str]] = []
        for method in methods:
            if method == "A2":
                fams.extend([(method, v) for v in variants])
            else:
                fams.append((method, ""))
        for method, variant in fams:
            anchor_N = ANCHOR_N if ANCHOR_N in Ns else max(Ns)
            if anchor_N == ANCHOR_N:
                anchor = select_M_anchor_m(wp, method, variant, B=B,
                                           seed=seed, out_dir=blocks,
                                           workers=workers)
                manifest["anchors"][f"{wp}/{method}"
                                    + (f"/{variant}" if variant else "")] = {
                                        k: v for k, v in anchor.items()
                                        if k != "cells"}
                for M, cell in anchor["cells"].items():
                    rec = dict(cell)
                    rec["anchor"] = True
                    rec["anchor_winner"] = (M == anchor["M_winner"])
                    manifest["cells"].append(rec)
                Mwin = anchor["M_winner"]
            else:
                Mwin = 2.5
                manifest["anchors"][f"{wp}/{method}"
                                    + (f"/{variant}" if variant else "")] = {
                                        "WP": wp, "method": method,
                                        "variant": variant, "N": anchor_N,
                                        "M_winner": Mwin,
                                        "note": "dry-grid: anchor skipped, "
                                                "freeze-M2.5"}
            for N in Ns:
                if N == ANCHOR_N and ANCHOR_N in Ns:
                    continue
                out = _cell_out(blocks, wp, method, variant, N, Mwin)
                try:
                    cell = _run_family_cell(wp, method, variant, N,
                                            Mwin, B=B, seed=seed,
                                            out=out, t0_cache=t0_cache,
                                            workers=workers)
                except Exception as exc:
                    cell = {"method": method, "variant": variant, "WP": wp,
                            "N": N, "M": Mwin, "B": B, "rows": 0,
                            "success": 0, "status": "short",
                            "detail": f"{type(exc).__name__}: {exc}",
                            "net": None}
                rec = dict(cell)
                rec["anchor"] = False
                manifest["cells"].append(rec)
    (root / "cells.json").write_text(json.dumps(manifest["cells"], indent=2),
                                     encoding="utf-8")
    (root / "anchors.json").write_text(json.dumps(manifest["anchors"],
                                                  indent=2),
                                       encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(
        {k: v for k, v in manifest.items() if k != "cells"}, indent=2),
        encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """CLI（证据网格执行；默认写 OP-M1 机器根）。"""
    ap = argparse.ArgumentParser(description="C-3 M-wave A1/A2 grid (OP-M1)")
    ap.add_argument("--root", type=str, default=str(DEFAULT_ROOT))
    ap.add_argument("--B", type=int, default=B_FULL)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--methods", type=str, default="A1,A2")
    ap.add_argument("--variants", type=str, default="SC,SCL8")
    ap.add_argument("--wps", type=str, default="F1,F2")
    ap.add_argument("--Ns", type=str,
                    default=",".join(str(n) for n in N_GRID))
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args(argv)
    root = Path(args.root)
    manifest = run_grid_m(
        root=root, B=int(args.B), seed=int(args.seed),
        methods=tuple(s for s in args.methods.split(",") if s),
        variants=tuple(s for s in args.variants.split(",") if s),
        workpoints=tuple(s for s in args.wps.split(",") if s),
        Ns=tuple(int(s) for s in args.Ns.split(",") if s),
        workers=int(args.workers))
    print(json.dumps({k: (v if k != "cells" else f"{len(v)} cells")
                      for k, v in manifest.items()}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
