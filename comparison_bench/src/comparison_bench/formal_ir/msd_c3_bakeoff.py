"""C-3 合成调参冻结驱动（EXPLORE，只做合成调参与冻结）.

冻结依据（逐字遵守）：
- ``docs/research_cycles/C-BATCH/C3_PACKET.md``（冻结包，2026-10-08）：
  信道引用（C2 规范表）、符号约定（C3_LAUNCH §1）、A3 归属（C3_LAUNCH §3）、
  工作点（新鲜 ≤3 族 F1/F2/F3，其余映射）、码率规则（§3 二进制/高维相对制 +
  B 级 margin 阶梯 M∈{2.5,3.0} 锚点二选一）、执行矩阵（R7：B_smoke=30 计时、
  外推超预算标 overtime-risk 分片续跑、逐块落盘 ROW_KEYS+code_hash/frozen_hash、
  6h 墙钟预算撞墙保留已完成格）、记账（R16：``net_of_cell`` 唯一口径、
  TAG=64、f_full、FER 点估计、U 隔离、β 附带列+强制警示语）、未定细则
  （任一格 F≤9 或 S≤9 → 未定，不参选）、返回条件（包 §7 结论上限）。
- ``docs/research_cycles/C-BATCH/C3_LAUNCH.md``（启动注记）：
  符号约定 δ*≈−δ̂C、信道规范 F1/F2/F3、A3 执行归属（C-3 驱动自含 A3 执行循环，
  镜像 runner A4 路径；A3 的 m 由冻结规则算出后显式传入 ``channel["m"]``）、
  启动命令（§5，字面）。

Track：EXPLORE。只跑合成参数化信道；不读原始数据（不读 ``D:/Data``）；
不重跑任何 DECIDE 数据（映射层只读历史行摘要 JSON，不存在则 mapped 表空置）；
不做科学判定（只报最优 N/净密钥/同时间 f 分层结果；FER 尾部外推、SKR、
路线关闭不在本包声称）。

冻结解释（操作员冻结口径，审计用）：
1. M 阶梯→R 标度：包冻结 M∈{2.5,3.0} 的集合与"N=16384 锚点按 Net_seg 二选一、
   选定后冻结同行"程序，未冻结 M→R 的数值标度。本驱动冻结标度为
   ``R(M) = R_base − (M − 2.5) × 0.01``（M=2.5 不附加，M=3.0 多退 0.005；
   同一标度用于二进制臂与高维臂，跨 p 可移植；A5 的 M 见 4）。
2. ``margin_B = 0.01`` 按包字面计入 ``R_base``（B≥300）。
3. ``K = round(N·R)`` 为 round-half-up（``floor(N·R + 0.5)``）；``K < 1`` 或
   ``m = N − K`` 不满足 ``0 < m < N`` 时记 ``infeasible``，不参选。
4. A5（layered_lite 原生码本，无冻结 R 函数）：M 映射为译码努力阶梯
   ``max_iter ∈ {50, 100}``（M=2.5→50，M=3.0→100），锚点程序相同；
   F3 只跑 F1/F2（5 元符号无原生二进制帧映射，注记原因）。
5. Undetected：合成真值已知，TAG 复核建模为理想（形状合法的错误码字由真值
   对比判定，u 恒 0；U 列保留恒 0 并注记，不估计 undetected 率）。
6. ``C_total``：合成 B 下分母用规划值 ``C_TOTAL_PLAN = 5_000_000``；
   当 ``B·N > C_TOTAL_PLAN`` 时该格超出规划采集（大 N 格），记
   ``N_valid = False``（floor(C_total/N) < 300），``C_total`` 取
   ``max(PLAN, B·N)`` 以满足 ``net_of_cell`` 前提，并在 ``C_total_note`` 注明；
   最优 N 只在 ``N_valid`` 格中选，另附无约束曲线备查。
7. 相同译码时间 f：``T_ref`` 取该 WP 已定最优格总译码时间的中位；
   ``Net_same_time = Net_seg × (T_ref / T_cell)`` 线性外推，标 ``extrap.``，
   与实测 ``Net_seg`` 区分。
8. R7 实现细节：每格先跑 ``B_smoke = 30``（不足 B 则全跑）计时；先以首
   ``min(3, B_smoke)`` 块做快速探针，外推超 ``cell_budget_s``（默认 1800s）
   则提前记 ``overtime-risk`` 并保留已跑块（short）；完整 smoke 外推超
   ``2 × 运行中位格耗时`` 同样记 ``overtime-risk``，分片（shard=30 块，
   append-only JSONL，按已落盘行数续跑，逐块种子 ``seed + block`` 保证
   续跑确定性）续跑；墙钟超 ``budget_s``（默认 6h）则停新格，保留已完成格，
   未达标格标 ``short`` 不参选。
9. A3 执行循环镜像 runner A4 路径：RNG 三值/q 元信道抽样 → ``mod.disclose``
   → ``mod.decode`` → tag 复核（TAG=64，失败/undetected 口径同 runner）→
   ROW_KEYS 行 → ``net_of_cell`` 汇总；m 由规则显式算出经 ``channel["m"]``
   传入。A3/A4 先验口径同 runner（``_prior_from_channel`` 约定复用 runner
   实现，不另立口径）。
10. 单个数字失败计数（F/S/U ≤ 9）在汇总表一律写「未定」（不写数字），
    逐块 JSONL 保留 ``ver``/``u`` 原始证据链。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as runner
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_kbin as kbin
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbldpc as nbldpc
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbpolar as nbpolar

__all__ = [
    "TAG", "N_GRID", "GAP_BIN", "GAP_NB", "MARGIN_B", "M_LADDER",
    "ANCHOR_N", "C_TOTAL_PLAN", "B_FULL", "B_SMOKE", "BUDGET_S",
    "FRESH_METHODS", "BETA_WARNING",
    "h2", "compute_rate", "frozen_hash_of",
    "channel_prior", "WORKPOINTS",
    "direction_smoke", "select_M_anchor", "run_grid",
]

TAG = 64
assert runner.TAG_BITS == 64, "runner TAG_BITS must be 64 (C3 frozen TAG=64)"
BETA_WARNING = runner.BETA_WARNING

N_GRID = (1024, 2048, 4096, 8192, 16384, 32768, 65536)
GAP_BIN = {1024: 0.08, 2048: 0.06, 4096: 0.05, 8192: 0.04,
           16384: 0.03, 32768: 0.025, 65536: 0.02}
GAP_NB = {1024: 0.10, 2048: 0.08, 4096: 0.07, 8192: 0.06,
          16384: 0.05, 32768: 0.04, 65536: 0.03}
MARGIN_B = 0.01
M_LADDER = (2.5, 3.0)
M_RATE_STEP = 0.01  # R(M) = R_base − (M−2.5)×0.01（冻结解释 1）
ANCHOR_N = 16384
C_TOTAL_PLAN = 5_000_000
B_FULL = 300
B_SMOKE = 30
BUDGET_S = 6 * 3600
CELL_BUDGET_S = 1800
OVERTIME_FLOOR_S = 30.0  # R7 误标下限（见 _run_cell_guarded）
SHARD = 30
SEED_BASE = 20261008
FRESH_METHODS = ("A1", "A2", "A3", "A4")
ROW_KEYS_EXTRA = ("frozen_hash", "undetected", "status", "WP", "M",
                  "seed", "R", "m", "K")


def _gap(table: dict, N: int) -> float:
    """gap 查表；非网格 N（仅测试/冒烟用，不进主表证据）取最近网格档。"""
    N = int(N)
    if N in table:
        return table[N]
    near = min(table, key=lambda k: abs(k - N))
    return table[near]


def h2(p: float) -> float:
    """二进制熵（比特）。"""
    p = float(p)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


def frozen_hash_of(text: str) -> str:
    """冻结标识短 hash（注明截断 16 hex）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---------------- 工作点（C3_LAUNCH §2；数值逐字） ----------------

def _f3_prior() -> dict:
    """F3（k=2, bw100, exploratory）：T2-1M (σ̂=24.88, δ̂=+46.99, W=200)
    由 cond_dist 生成 P(e)，经 c1_kbin.params_from_stats 得 (q, H_q, ideal)。
    确定性计算，不读原始数据（cond_dist 为自写 Simpson 前向模型）。"""
    from comparison_bench.src.comparison_bench.formal_ir import msd_c2_fit as c2fit
    sig, delta, bw = 24.88, 46.99, 100.0
    probs: dict[int, float] = {}
    cover = 1.0
    for kk in range(-8, 9):
        jk, cover = c2fit.cond_dist(bw, sig, delta, kk)
        probs[kk] = jk / cover
    S2 = [-2, -1, 0, 1, 2]
    p = sum(v for kk, v in probs.items() if kk != 0 and kk in S2)
    pm = probs.get(-1, 0.0)
    rest = max(0.0, 1.0 - sum(probs[kk] for kk in S2))
    q, H_q, _ideal = kbin.params_from_stats(support=S2, p=p, p_minus=pm,
                                             k=2, rest=rest)
    # GF(5) 剩余类序 g[r] = P((b−a) mod 5 = r)：e=−2→3，e=−1→4。
    g = [probs.get(0, 0.0), probs.get(1, 0.0), probs.get(2, 0.0),
         probs.get(-2, 0.0), probs.get(-1, 0.0)]
    return {"q": q, "H_q": H_q, "p": p, "p_minus": pm, "rest": rest,
            "prior_g": g}


_F3 = _f3_prior()


def _k1_H(p: float, p_minus: float, rest: float):
    q, H_q, _ = kbin.params_from_stats(support=[-1, 0, 1], p=p,
                                       p_minus=p_minus, k=1, rest=rest)
    return q, H_q


WORKPOINTS = {
    # F1（k=1, bw200-cal）：三值 (p*, p_minus_abs*, rest)（C3_LAUNCH §2）。
    "F1": {"k": 1, "q": 3, "p": 0.060740, "p_minus": 0.037000,
           "rest": 1.3e-05, "C_total": C_TOTAL_PLAN, "tag": "calibrated",
           "H_q": _k1_H(0.060740, 0.037000, 1.3e-05)[1]},
    # F2（k=1, bw400-cal）。
    "F2": {"k": 1, "q": 3, "p": 0.030413, "p_minus": 0.018564,
           "rest": 0.0, "C_total": C_TOTAL_PLAN, "tag": "calibrated",
           "H_q": _k1_H(0.030413, 0.018564, 0.0)[1]},
    # F3（k=2, bw100, exploratory）。
    "F3": {"k": 2, "q": _F3["q"], "p": _F3["p"], "p_minus": _F3["p_minus"],
           "rest": _F3["rest"], "C_total": C_TOTAL_PLAN,
           "tag": "exploratory", "H_q": _F3["H_q"],
           "prior_g": _F3["prior_g"]},
}


def channel_prior(wp: str):
    """该工作点的 q 元先验 ``prior_g``（与 runner ``_prior_from_channel`` 同约定；
    F3 用 cond_dist 残差序，见 ``_f3_prior``）。"""
    spec = WORKPOINTS[wp]
    if "prior_g" in spec:
        return list(spec["prior_g"])
    _q, g = runner._prior_from_channel(
        {"k": spec["k"], "p": spec["p"], "p_minus": spec["p_minus"]})
    return list(g)


# ---------------- 冻结码率规则（包 §3） ----------------

def compute_rate(*, family: str, p_op: float, H_q: float, q: int,
                 N: int, M: float) -> dict:
    """冻结调参函数 ``R = F_method(p_op, N, M)``。

    二进制臂：``R = 1 − h2(p_op) − gap_bin(N) − margin_B − (M−2.5)×0.01``；
    高维臂：``R = 1 − H_sym(p_op,k)/log2(q) − gap_nb(N) − margin_B − (M−2.5)×0.01``；
    ``K = round-half-up(N·R)``；``m = N − K``；``K < 1`` 或 ``0 < m < N``
    不成立 → ``infeasible``。
    """
    N = int(N)
    if family == "bin":
        R = 1.0 - h2(p_op) - _gap(GAP_BIN, N) - MARGIN_B - (M - 2.5) * M_RATE_STEP
    elif family == "nb":
        R = (1.0 - H_q / math.log2(q) - _gap(GAP_NB, N) - MARGIN_B
             - (M - 2.5) * M_RATE_STEP)
    else:
        raise ValueError(f"unknown family {family!r}")
    K = int(math.floor(N * R + 0.5))
    m = N - K
    feasible = K >= 1 and 0 < m < N
    return {"R": R, "K": K, "m": m, "feasible": feasible,
            "reason": "" if feasible else ("infeasible: "
                                           f"R={R:.4f}, K={K}, m={m}")}


def family_of(method: str) -> str:
    """方法族（二进制臂 A1/A2/A5，高维臂 A3/A4）。"""
    if method in ("A1", "A2", "A5"):
        return "bin"
    if method in ("A3", "A4"):
        return "nb"
    raise ValueError(f"unknown method {method!r}")


def rate_inputs(wp: str) -> dict:
    """该工作点的码率输入（p_op 全方法共用；H_q 高维臂用）。"""
    spec = WORKPOINTS[wp]
    return {"p_op": spec["p"], "H_q": spec["H_q"], "q": spec["q"]}


# ---------------- 方向冒烟（C3_LAUNCH §1：T2-1M δ*=−50 先行） ----------------

def direction_smoke(*, B: int = 10, N: int = 256,
                    seed: int = SEED_BASE) -> dict:
    """方向冒烟：正确符号（F1 校准后 p*=0.060740，即 T2-1M δ*=−50 最优点）
    vs 错误符号代理（标称未校准 p=0.237970，p₋≈0.005，C0_RESULT §1/§4）。

    判定（须同时成立，否则调用方必须停）：
    ``p_ok < p_bad`` 且成功块 ``succ_ok > succ_bad`` 且
    ``Net_seg_ok > Net_seg_bad``。N=256 使单块净贡献为正（小 N 下 TAG=64
    主导会反转 Net 比较，特此注明）；用 A4 小规模（B≤30），只做方向判定，
    不做科学判定。
    """
    ri = rate_inputs("F1")
    rr = compute_rate(family="nb", p_op=ri["p_op"], H_q=ri["H_q"],
                      q=ri["q"], N=N, M=2.5)
    ch_ok = {"k": 1, "p": 0.060740, "p_minus": 0.060740 * 0.609160,
             "m": rr["m"], "R": rr["R"]}
    ch_bad = {"k": 1, "p": 0.237970, "p_minus": 0.237970 * 0.005,
              "m": rr["m"], "R": rr["R"]}
    tmp = Path(f"workspace/c3_probe_smoke_{seed:x}")
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    try:
        s_ok = _run_a4_cell("F1", N, 2.5, ch_ok, B, seed,
                            tmp / "ok.jsonl", drill=True)
        s_bad = _run_a4_cell("F1", N, 2.5, ch_bad, B, seed,
                             tmp / "bad.jsonl", drill=True)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    ok = (s_ok["net"]["Net_seg"] > s_bad["net"]["Net_seg"]
          and s_ok["success"] > s_bad["success"]
          and s_ok["success"] >= 1
          and ch_ok["p"] < ch_bad["p"])
    return {"pass": bool(ok), "delta_star": -50, "source": "T2-1M",
            "p_ok": ch_ok["p"], "p_bad": ch_bad["p"],
            "net_ok": s_ok["net"]["Net_seg"],
            "net_bad": s_bad["net"]["Net_seg"],
            "succ_ok": s_ok["success"], "succ_bad": s_bad["success"],
            "note": "δ*≈−δ̂C 约定冒烟；与 C-0 最优点一致方继续"}


# ---------------- 各方法 cell 执行 ----------------

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


def _count_success(path: Path) -> tuple[int, int]:
    """落盘续跑审计：统计文件内总行数与 ver=1 行数。"""
    n = s = 0
    if not path.exists():
        return 0, 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                s += int(json.loads(line).get("ver", 0))
            except Exception:
                pass
    return n, s


def _a4_prior_and_m(wp: str, N: int, M: float):
    spec = WORKPOINTS[wp]
    ri = rate_inputs(wp)
    rr = compute_rate(family="nb", p_op=ri["p_op"], H_q=ri["H_q"],
                      q=ri["q"], N=N, M=M)
    g = channel_prior(wp)
    return spec, rr, g


def _run_a4_cell(wp: str, N: int, M: float, channel: dict, B: int,
                 seed: int, out: Path, *, drill: bool = False) -> dict:
    """A4 原生路径（镜像 runner：抽样→disclose→decode→tag→行→net_of_cell）。

    ``channel`` 须含显式 ``"m"``（m 由规则算出后传入；drill 冒烟允许直接给）。
    逐块种子 ``seed + block``（分片续跑确定性）。
    """
    spec = WORKPOINTS[wp]
    q = spec["q"]
    # 先验以传入 channel 为准（方向冒烟的错误符号代理靠此区分；网格运行时
    # channel 与规范一致，自洽）。F3 经 channel["prior_g"] 显式传入。
    if "prior_g" in channel:
        prior_g = list(channel["prior_g"])
    else:
        _q, prior_g = runner._prior_from_channel(
            {k: channel[k] for k in ("k", "q", "p", "p_minus")
             if k in channel})
        prior_g = list(prior_g)
    m = int(channel["m"])
    N = int(N)
    if not (0 < m < N):
        raise ValueError(f"channel m must satisfy 0 < m < N, got {m}")
    if N < 2 or (N & (N - 1)) != 0:
        raise ValueError(f"A4 requires N a power of two >= 2, got {N}")
    chf = dict(channel)
    chf.setdefault("q", q)
    code = nbpolar.construct(N, m, q, seed, channel=chf,
                             prior_g=list(prior_g))
    frozen_hash = frozen_hash_of(f"A4|F={list(code.frozen)}")
    k_info = N - m
    kept = k_info * math.log2(q)
    t_list: list[float] = []
    succ = 0
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        a = rng.integers(0, q, N).tolist()
        e = rng.choice(q, size=N,
                       p=np.asarray(prior_g) / sum(prior_g))
        bb = ((np.asarray(a) + np.asarray(e)) % q).tolist()
        syn, lec = code.disclose(a)
        t0 = time.perf_counter()
        a_hat = code.decode(bb, syn, list(prior_g), 50, list_size=1)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = a_hat is not None and list(a_hat) == list(a)
        succ += int(good)
        _append_rows(out, [{
            "method": "A4", "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept) if good else 0.0,
            "L_EC": int(lec), "tag": TAG if good else 0,
            "T_dec": float(t_dec), "code_hash": code.code_hash,
            "frozen_hash": frozen_hash, "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": chf.get("R"),
            "m": m, "K": k_info}])
    C_cell = max(float(spec["C_total"]), float(B * N))
    H = nbpolar.prior_entropy_bits(prior_g)
    _n_rows, succ = _count_success(out)  # 续跑审计：全文件重计
    net = runner.net_of_cell(
        kept_bits=kept, L_EC_bits=code.disclosure_bits, tag_bits=TAG,
        n_fail=B - succ, n_blocks=B, C_total=C_cell, N=N,
        n_undetected=0, h_op=H, I_op=math.log2(q) - H)
    return {"method": "A4", "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": 0,
            "median_T_dec": float(np.median(t_list)) if t_list else 0.0,
            "total_T_dec": float(sum(t_list)),
            "code_hash": code.code_hash, "frozen_hash": frozen_hash,
            "lec_bits": int(code.disclosure_bits), "kept": float(kept),
            "C_total": C_cell, "net": net}


def _run_a3_cell(wp: str, N: int, M: float, channel: dict, B: int,
                 seed: int, out: Path) -> dict:
    """A3 执行循环（C-3 自含，镜像 A4 路径；m 经 ``channel["m"]`` 显式传入）。

    构造器按包 §3.2（PEG 骨架 + 非零元均匀）；失败返回 None（不抛异常），
    口径同 runner A4（tag 复核、ROW_KEYS、net_of_cell）。
    """
    spec = WORKPOINTS[wp]
    q = spec["q"]
    # 先验以传入 channel 为准（同 A4 注释；m 经 channel["m"] 显式传入）。
    if "prior_g" in channel:
        prior_g = list(channel["prior_g"])
    else:
        _q, prior_g = runner._prior_from_channel(
            {k: channel[k] for k in ("k", "q", "p", "p_minus")
             if k in channel})
        prior_g = list(prior_g)
    m = int(channel["m"])
    N = int(N)
    code = nbldpc.construct(N, m, q, seed)
    code_hash = frozen_hash_of(f"A3|n={N}|m={m}|q={q}|seed={seed}|"
                               f"H={code.H.tobytes().hex()[:256]}")
    frozen_hash = frozen_hash_of(f"A3-H|n={N}|m={m}|q={q}|seed={seed}|"
                                 f"H={code.H.tobytes().hex()}")
    k_info = N - m
    kept = k_info * math.log2(q)
    t_list: list[float] = []
    succ = 0
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        a = rng.integers(0, q, N).tolist()
        e = rng.choice(q, size=N,
                       p=np.asarray(prior_g) / sum(prior_g))
        bb = ((np.asarray(a) + np.asarray(e)) % q).tolist()
        syn, lec = nbldpc.disclose(code, a)
        t0 = time.perf_counter()
        a_hat = nbldpc.decode(code, bb, syn, list(prior_g), 50)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = a_hat is not None and list(np.asarray(a_hat).tolist()) == list(a)
        succ += int(good)
        _append_rows(out, [{
            "method": "A3", "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept) if good else 0.0,
            "L_EC": int(lec), "tag": TAG if good else 0,
            "T_dec": float(t_dec), "code_hash": code_hash,
            "frozen_hash": frozen_hash, "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": channel.get("R"),
            "m": m, "K": k_info}])
    C_cell = max(float(spec["C_total"]), float(B * N))
    H = nbpolar.prior_entropy_bits(prior_g)
    _n_rows, succ = _count_success(out)  # 续跑审计：全文件重计
    net = runner.net_of_cell(
        kept_bits=kept, L_EC_bits=int(math.ceil(m * math.log2(q))),
        tag_bits=TAG, n_fail=B - succ, n_blocks=B, C_total=C_cell,
        N=N, n_undetected=0, h_op=H, I_op=math.log2(q) - H)
    return {"method": "A3", "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": 0,
            "median_T_dec": float(np.median(t_list)) if t_list else 0.0,
            "total_T_dec": float(sum(t_list)),
            "code_hash": code_hash, "frozen_hash": frozen_hash,
            "lec_bits": int(math.ceil(m * math.log2(q))),
            "kept": float(kept), "C_total": C_cell, "net": net}


def _bhattacharyya_frozen(n: int, k_info: int, p: float):
    """二进制 BSC 冻结集（按 p_op 重算：Z0 = 2√(p(1−p))，极化递归
    Z−=2Z−Z²、Z+=Z²，可靠度 Z 升序取信息位；并列按下标确定性打破）。"""
    z0 = 2.0 * math.sqrt(max(p, 0.0) * max(1.0 - p, 0.0))
    z = np.array([z0])
    while z.shape[0] < n:
        nxt = np.empty(2 * z.shape[0])
        nxt[0::2] = 2.0 * z - z * z
        nxt[1::2] = z * z
        z = nxt
    order = sorted(range(n), key=lambda i: (float(z[i]), i))
    info = tuple(sorted(order[:k_info]))
    frozen = tuple(sorted(order[k_info:]))
    return frozen, info


def _run_a1_cell(wp: str, N: int, M: float, rr: dict, B: int,
                 seed: int, out: Path) -> dict:
    """A1：高码率区 PEG 优先（包 §3；RA 阈值崩先例下 PEG 为冻结构造）。
    BSC(p_op) 合成，BP 译码（max_iter=200，同 G-5），无 rescue（C-3 无此项，
    失败块 L_EC 照计、kept 取 0）。"""
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (
        build_peg_code)
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
        make_bp_decoder)
    spec = WORKPOINTS[wp]
    p = spec["p"]
    N, m, K = int(N), int(rr["m"]), int(rr["K"])
    try:
        pc = build_peg_code(n=N, m=m,
                            variable_degree=min(3, m))
    except Exception as exc:
        return {"method": "A1", "WP": wp, "N": N, "M": M, "B": B,
                "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}"}
    H = pc.parity_check_matrix.tocsr()
    Hd = np.asarray(H.toarray(), dtype=np.uint8)
    code_hash = frozen_hash_of(f"A1-PEG|n={N}|m={m}|seed={seed}")
    t_list: list[float] = []
    succ = 0
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        x = rng.integers(0, 2, N).astype(np.uint8)
        y = np.bitwise_xor(
            x, (rng.random(N) < p).astype(np.uint8))
        syn = (Hd @ x) % 2
        ch = np.full(N, p)
        t0 = time.perf_counter()
        dec = make_bp_decoder(parity_check_matrix=H,
                              error_channel=ch.copy(), max_iter=200)
        delta = (syn - (Hd @ y) % 2) % 2
        err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
        xh = np.bitwise_xor(y, err)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = bool(np.array_equal((Hd @ xh) % 2, syn)
                    and np.array_equal(xh, x))
        succ += int(good)
        _append_rows(out, [{
            "method": "A1", "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(K) if good else 0.0, "L_EC": int(m),
            "tag": TAG if good else 0, "T_dec": float(t_dec),
            "code_hash": code_hash, "frozen_hash": code_hash,
            "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": rr["R"], "m": m, "K": K}])
    C_cell = max(float(spec["C_total"]), float(B * N))
    _n_rows, succ = _count_success(out)  # 续跑审计：全文件重计
    net = runner.net_of_cell(
        kept_bits=float(K), L_EC_bits=float(m), tag_bits=TAG,
        n_fail=B - succ, n_blocks=B, C_total=C_cell, N=N,
        n_undetected=0, h_op=h2(p), I_op=1.0 - h2(p))
    return {"method": "A1", "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": 0,
            "median_T_dec": float(np.median(t_list)) if t_list else 0.0,
            "total_T_dec": float(sum(t_list)),
            "code_hash": code_hash, "frozen_hash": code_hash,
            "lec_bits": int(m), "kept": float(K),
            "C_total": C_cell, "net": net}


def _run_a2_cell(wp: str, N: int, M: float, rr: dict, B: int,
                 seed: int, out: Path) -> dict:
    """A2：冻结集按 p_op 重算（Bhattacharyya 递归，本驱动冻结方法）并记 hash；
    sibling ``polar_core`` 只读调用（SCL L=8，同 G-5）；缺失则 ``unavailable``
    行透传（不断言失败）。"""
    import sys as _sys
    spec = WORKPOINTS[wp]
    p = spec["p"]
    N, m, K = int(N), int(rr["m"]), int(rr["K"])
    try:
        if runner.SIBLING_ROOT not in _sys.path:
            _sys.path.insert(0, runner.SIBLING_ROOT)
        import importlib as _il
        _P = _il.import_module("low_dim_opt.core.polar_core")
    except Exception as exc:
        rows = [{"method": "A2", "WP": wp, "N": N, "block": b,
                 "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
                 "T_dec": 0.0, "code_hash": "", "frozen_hash": "",
                 "undetected": False, "status": "unavailable",
                 "detail": f"sibling polar_core missing: {exc}",
                 "M": M, "seed": seed, "R": rr["R"], "m": m, "K": K}
                for b in range(B)]
        _append_rows(out, rows)
        return {"method": "A2", "WP": wp, "N": N, "M": M, "B": B,
                "rows": B, "success": 0, "undetected": 0,
                "status": "unavailable", "median_T_dec": 0.0,
                "total_T_dec": 0.0,
                "code_hash": "", "frozen_hash": "",
                "lec_bits": 0, "kept": 0.0,
                "C_total": max(float(spec["C_total"]), float(B * N)),
                "net": None}
    frozen, info = _bhattacharyya_frozen(N, K, p)
    frozen_hash = frozen_hash_of(f"A2|n={N}|K={K}|p={p}|F={list(frozen)}")
    code_hash = frozen_hash
    mask = np.zeros(N, dtype=np.uint8)
    mask[np.asarray(info, dtype=np.int64)] = 1
    n_log = int(math.log2(N))
    llr_mag = math.log(max(1.0 - p, 1e-300) / max(p, 1e-300))
    t_list: list[float] = []
    succ = 0
    start = int(_jsonl_count(out))
    for b in range(start, B):
        rng = np.random.default_rng(seed + b)
        xt = rng.integers(0, 2, N).astype(np.int8)
        e = (rng.random(N) < p).astype(np.int8)
        yt = np.bitwise_xor(xt, e)
        ua = _P.polar_encode(xt, n_log)
        frz = np.where(mask == 0)[0]
        fv = np.zeros(N, dtype=np.uint8)
        fv[frz] = np.asarray(ua)[frz]
        llr = np.where(yt == 0, llr_mag, -llr_mag).astype(float)
        t0 = time.perf_counter()
        uh = _P.scl_decode_batch(llr.reshape(1, -1), mask,
                                 fv.reshape(1, -1), n_log, 8)
        xh = np.asarray(
            _P.polar_encode(np.asarray(uh[0]).astype(np.int8),
                            n_log)).astype(np.int8)
        t_dec = time.perf_counter() - t0
        t_list.append(t_dec)
        good = bool(np.array_equal(xh, xt))
        succ += int(good)
        _append_rows(out, [{
            "method": "A2", "WP": wp, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(K) if good else 0.0, "L_EC": int(m),
            "tag": TAG if good else 0, "T_dec": float(t_dec),
            "code_hash": code_hash, "frozen_hash": frozen_hash,
            "undetected": False,
            "status": "ok" if good else "decode_failed",
            "M": M, "seed": seed, "R": rr["R"], "m": m, "K": K}])
    C_cell = max(float(spec["C_total"]), float(B * N))
    _n_rows, succ = _count_success(out)  # 续跑审计：全文件重计
    net = runner.net_of_cell(
        kept_bits=float(K), L_EC_bits=float(m), tag_bits=TAG,
        n_fail=B - succ, n_blocks=B, C_total=C_cell, N=N,
        n_undetected=0, h_op=h2(p), I_op=1.0 - h2(p))
    return {"method": "A2", "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": 0,
            "median_T_dec": float(np.median(t_list)) if t_list else 0.0,
            "total_T_dec": float(sum(t_list)),
            "code_hash": code_hash, "frozen_hash": frozen_hash,
            "lec_bits": int(m), "kept": float(K),
            "C_total": C_cell, "net": net}


def _run_a5_cell(wp: str, N: int, M: float, B: int, seed: int,
                 out: Path) -> dict:
    """A5：``layered_lite`` 新鲜 wrap（合成帧；M→max_iter 阶梯见冻结解释 4；
    单格超时标 ``overtime-risk`` 分片续跑；原生异常则 ``unavailable`` 行如实
    空缺）。记账经 runner ``adapt_layered_lite_result`` + ``net_of_cell``。"""
    spec = WORKPOINTS[wp]
    if wp == "F3":
        return {"method": "A5", "WP": wp, "N": N, "M": M, "B": B,
                "status": "unavailable",
                "detail": "A5 wrap only F1/F2 (no native binary-frame map "
                          "for 5-ary symbols)",
                "rows": 0, "success": 0, "undetected": 0,
                "median_T_dec": 0.0, "total_T_dec": 0.0,
                "code_hash": "", "frozen_hash": "",
                "lec_bits": 0, "kept": 0.0,
                "C_total": max(float(spec["C_total"]), float(B * N)),
                "net": None}
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import (
        FrameBatch, IRRunConfig, run_layered_ldpc_lite)
    max_iter = 50 if M == 2.5 else 100
    rng = np.random.default_rng(seed)
    p = spec["p"]
    alice = (rng.random((B, N)) < 0.5).astype(np.uint8)
    flips = (rng.random((B, N)) < p)
    bob = np.bitwise_xor(alice, flips.astype(np.uint8))
    cfg = IRRunConfig(method="layered_ldpc_lite",
                      method_variant=f"c3-M{M}", dimension=2,
                      frame_len_symbols=N, max_iter=max_iter,
                      qber_estimate=p)
    batch = FrameBatch(dataset_id=f"c3-{wp}-synth", alice_symbols=alice,
                       bob_symbols=bob, dimension=2,
                       frame_len_symbols=N, metadata={"c3": True})
    t0 = time.perf_counter()
    try:
        res = run_layered_ldpc_lite(batch, cfg)
    except Exception as exc:
        rows = [{"method": "A5", "WP": wp, "N": N, "block": b,
                 "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
                 "T_dec": 0.0, "code_hash": "", "frozen_hash": "",
                 "undetected": False, "status": "unavailable",
                 "detail": f"layered_lite native error: "
                           f"{type(exc).__name__}: {exc}",
                 "M": M, "seed": seed, "R": None, "m": None, "K": None}
                for b in range(B)]
        _append_rows(out, rows)
        return {"method": "A5", "WP": wp, "N": N, "M": M, "B": B,
                "rows": B, "success": 0, "undetected": 0,
                "status": "unavailable", "median_T_dec": 0.0,
                "total_T_dec": 0.0, "code_hash": "", "frozen_hash": "",
                "lec_bits": 0, "kept": 0.0,
                "C_total": max(float(spec["C_total"]), float(B * N)),
                "net": None}
    wall = time.perf_counter() - t0
    rows = runner.adapt_layered_lite_result(res, method="A5",
                                            tag_bits=TAG,
                                            code_hash=f"A5-lite-{wp}-N{N}"
                                                      f"-M{M}")
    for i, r in enumerate(rows):
        r.update({"WP": wp, "frozen_hash": r.get("code_hash", ""),
                  "M": M, "seed": seed})
    _append_rows(out, rows)
    succ = sum(1 for r in rows if r["ver"] == 1 and not r["u"])
    fail = B - succ
    ok_rows = [r for r in rows if r["ver"] == 1 and not r["u"]]
    kept0 = float(ok_rows[0]["kept"]) if ok_rows else 0.0
    lec0 = int(rows[0]["L_EC"]) if rows else 0
    C_cell = max(float(spec["C_total"]), float(B * N))
    net = runner.net_of_cell(
        kept_bits=kept0, L_EC_bits=float(lec0), tag_bits=TAG,
        n_fail=fail, n_blocks=B, C_total=C_cell, N=N,
        n_undetected=0, h_op=h2(p), I_op=1.0 - h2(p))
    per = wall / max(B, 1)
    return {"method": "A5", "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": 0,
            "median_T_dec": per, "total_T_dec": wall,
            "code_hash": f"A5-lite-{wp}-N{N}-M{M}",
            "frozen_hash": f"A5-lite-{wp}-N{N}-M{M}",
            "lec_bits": lec0, "kept": kept0,
            "C_total": C_cell, "net": net}


# ---------------- M 锚点 ----------------

def select_M_anchor(wp: str, method: str, *, B: int, seed: int,
                    out_dir: Path, cell_budget_s: float = CELL_BUDGET_S,
                    deadline: float | None = None) -> dict:
    """M 锚点程序：只在 N=16384 对 M∈{2.5,3.0} 二选一（按 Net_seg），
    选定后冻结用于该（WP,方法）行其余 N。落选 M 的块保留为锚点选择证据
    （文件名带 M，不进主表）。"""
    N = ANCHOR_N
    results: dict[float, dict] = {}
    for M in M_LADDER:
        out = out_dir / f"{wp}_{method}_N{N}_M{M}.jsonl"
        if _jsonl_count(out) >= B:
            # 续跑复用：锚点已满行则直接重计，不重跑探针/构造。
            results[M] = _recount_cell(wp, method, N, M, B=B, seed=seed,
                                       out=out)
            continue
        # 锚点格同样走 R7 守卫（探针/分片/预算），与网格同口径。
        results[M] = _run_cell_guarded(wp, method, N, M, B=B,
                                       seed=seed, out=out, med_times=[],
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
    return {"WP": wp, "method": method, "N": N, "B": B,
            "M_winner": winner, "nets": nets, "decided": decided,
            "note": note, "cells": results}


def _decided(cell: dict) -> bool:
    """该格是否满足参选门（F≥10 且 S≥10；B 不足/无 net 亦视为未定）。"""
    net = cell.get("net")
    if net is None:
        return False
    B = int(cell.get("B", 0))
    F = int(net.get("F", B))
    S = int(net.get("S_main", 0))
    return F >= 10 and S >= 10


# ---------------- 单格调度（含 smoke/分片/续跑） ----------------

def _run_one_cell(wp: str, method: str, N: int, M: float, *, B: int,
                  seed: int, out: Path, cell_budget_s: float = CELL_BUDGET_S,
                  deadline: float | None = None) -> dict:
    """单格执行：已落盘行数续跑（append-only）；失败/不可行如实返回。"""
    spec = WORKPOINTS[wp]
    ri = rate_inputs(wp)
    fam = family_of(method)
    if method == "A5":
        return _run_a5_cell(wp, N, M, B, seed, out)
    rr = compute_rate(family=fam, p_op=ri["p_op"], H_q=ri["H_q"],
                      q=ri["q"], N=N, M=M)
    if not rr["feasible"]:
        return {"method": method, "WP": wp, "N": N, "M": M, "B": B,
                "status": "infeasible", "detail": rr["reason"],
                "rows": 0, "success": 0, "net": None}
    if method in ("A3", "A4"):
        g = channel_prior(wp)
        channel = {"k": spec["k"], "p": spec["p"],
                   "p_minus": spec.get("p_minus"), "q": spec["q"],
                   "prior_g": g, "m": rr["m"], "R": rr["R"]}
        if method == "A3":
            return _run_a3_cell(wp, N, M, channel, B, seed, out)
        ch4 = dict(channel)
        if wp == "F3":
            ch4 = {"q": spec["q"], "prior_g": g, "m": rr["m"],
                   "R": rr["R"]}
        return _run_a4_cell(wp, N, M, ch4, B, seed, out)
    if method == "A1":
        return _run_a1_cell(wp, N, M, rr, B, seed, out)
    if method == "A2":
        return _run_a2_cell(wp, N, M, rr, B, seed, out)
    raise ValueError(f"unknown method {method!r}")


# ---------------- 网格 ----------------

def _n_valid(wp: str, N: int) -> bool:
    C_total = float(WORKPOINTS[wp]["C_total"])
    return math.floor(C_total / N) >= 300


def run_grid(*, root: Path, B: int, seed: int,
             methods: tuple = FRESH_METHODS,
             workpoints: tuple = ("F1", "F2", "F3"),
             Ns: tuple = N_GRID,
             budget_s: float = BUDGET_S,
             cell_budget_s: float = CELL_BUDGET_S,
             resume: bool = False) -> dict:
    """新鲜层网格执行（含方向冒烟先行、M 锚点、R7 smoke/分片/预算墙）。

    返回 manifest 字典；同时落盘 ``blocks/*.jsonl``、``cells.json``、
    ``anchor.json``、``manifest.json``。
    """
    t_start = time.perf_counter()
    deadline = t_start + budget_s
    blocks = root / "blocks"
    blocks.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"mode": f"B={B}", "B": B, "seed": seed,
                      "methods": list(methods),
                      "workpoints": list(workpoints), "Ns": list(Ns),
                      "cells": [], "anchors": {}, "events": [],
                      "repairs": 0}
    # 方向冒烟先行（不一致则停）。
    smoke = direction_smoke()
    manifest["direction_smoke"] = smoke
    if not smoke["pass"]:
        manifest["events"].append("direction-smoke-FAIL: stop")
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
        raise SystemExit("direction smoke FAIL (T2-1M δ*=-50 不一致）：停")
    manifest["events"].append("direction-smoke-PASS")
    med_times: list[float] = []
    wall_hit = False
    for wp in workpoints:
        for method in methods:
            if method == "A5" and wp == "F3":
                continue
            # M 锚点（N=16384；干跑/小网格锚点取该方法最大 N，由调用方保证）。
            anchor_N = ANCHOR_N if ANCHOR_N in Ns else max(Ns)
            if anchor_N == ANCHOR_N:
                anchor = select_M_anchor(
                    wp, method, B=B, seed=seed, out_dir=blocks,
                    cell_budget_s=cell_budget_s, deadline=deadline)
                manifest["anchors"][f"{wp}/{method}"] = {
                    k: v for k, v in anchor.items() if k != "cells"}
                for M, cell in anchor["cells"].items():
                    manifest["cells"].append(_cell_record(cell, anchor=True,
                                                          winner=(M == anchor[
                                                              "M_winner"])))
                    if cell.get("total_T_dec"):
                        med_times.append(float(cell["total_T_dec"]))
                Mwin = anchor["M_winner"]
            else:
                Mwin = 2.5
                manifest["anchors"][f"{wp}/{method}"] = {
                    "WP": wp, "method": method, "N": anchor_N,
                    "M_winner": Mwin, "note": "dry-grid: anchor skipped, "
                                              "freeze-M2.5"}
            for N in Ns:
                if N == ANCHOR_N and ANCHOR_N in Ns:
                    continue  # 锚点格已跑（winner 行复用，不重跑）。
                if time.perf_counter() > deadline:
                    manifest["events"].append(
                        f"wall-budget-hit: stop before {wp}/{method}/N{N}; "
                        "completed cells retained")
                    break
                out = blocks / f"{wp}_{method}_N{N}_M{Mwin}.jsonl"
                if _jsonl_count(out) >= B:
                    # 续跑复用：已满行直接重计。
                    cell = _recount_cell(wp, method, N, Mwin, B=B,
                                         seed=seed, out=out)
                else:
                    cell = _run_cell_guarded(wp, method, N, Mwin, B=B,
                                             seed=seed, out=out,
                                             med_times=med_times,
                                             cell_budget_s=cell_budget_s,
                                             deadline=deadline)
                manifest["cells"].append(_cell_record(cell))
                if cell.get("total_T_dec"):
                    med_times.append(float(cell["total_T_dec"]))
            if time.perf_counter() > deadline:
                manifest["events"].append("wall-budget-hit: outer stop")
                wall_hit = True
                break
        if wall_hit:
            manifest["events"].append("wall-budget-hit: WP loop stop")
            break
    manifest["wall_s"] = time.perf_counter() - t_start
    (root / "cells.json").write_text(json.dumps(manifest["cells"], indent=2),
                                     encoding="utf-8")
    (root / "anchor.json").write_text(json.dumps(manifest["anchors"], indent=2),
                                      encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                        encoding="utf-8")
    return manifest


def _cell_record(cell: dict, *, anchor: bool = False,
                 winner: bool = True) -> dict:
    net = cell.get("net") or {}
    return {
        "WP": cell.get("WP"), "method": cell.get("method"),
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
        "beta_warning": net.get("beta_warning"),
        "w_tail": net.get("w_tail"), "C_used": net.get("C_used"),
        "C_total": cell.get("C_total"), "N_valid": _n_valid(
            cell["WP"], cell["N"]) if cell.get("WP") else None,
        "median_T_dec": cell.get("median_T_dec"),
        "total_T_dec": cell.get("total_T_dec"),
        "code_hash": cell.get("code_hash"),
        "frozen_hash": cell.get("frozen_hash"),
        "decided": _decided(cell),
    }


def _run_cell_guarded(wp: str, method: str, N: int, M: float, *, B: int,
                      seed: int, out: Path, med_times: list,
                      cell_budget_s: float, deadline: float | None) -> dict:
    """R7 单格守卫：快速探针（首 3 块）→ smoke 30 → 分片续跑；超时/墙钟如实标记。"""
    import math as _m
    probe_B = min(3, B)
    probe_out = out.with_name(out.stem + ".probe.jsonl")
    if probe_out.exists():
        probe_out.unlink()
    t0 = time.perf_counter()
    try:
        probe = _run_one_cell(wp, method, N, M, B=probe_B, seed=seed,
                              out=probe_out,
                              cell_budget_s=cell_budget_s,
                              deadline=deadline)
    except Exception as exc:
        return {"method": method, "WP": wp, "N": N, "M": M, "B": B,
                "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": 0, "success": 0, "net": None}
    finally:
        if probe_out.exists():
            probe_out.unlink()
    probe_t = time.perf_counter() - t0
    if probe.get("status") in ("infeasible", "construction-fail"):
        # 探针已证不可行/构造失败：直接返回全尺寸记录（不重复 heavy 工作）。
        full = _run_one_cell(wp, method, N, M, B=B, seed=seed, out=out)
        return full
    per_block = probe_t / max(probe_B, 1)
    # 摊销模型（预注册工程修复①：探针墙钟含一次性构造/编译成本，
    # 不得按每块均摊；外推 = 探针实耗 + 解码中位×剩余块；科学输入/规则未变）。
    med_dec = probe.get("median_T_dec") or per_block
    extrap = probe_t + med_dec * max(B - probe_B, 0)
    med = float(np.median(med_times)) if med_times else extrap
    if extrap > cell_budget_s:
        return {"method": method, "WP": wp, "N": N, "M": M, "B": B,
                "status": "overtime-risk",
                "detail": f"probe-extrap {extrap:.0f}s > cell_budget "
                          f"{cell_budget_s:.0f}s; 0 blocks run (short)",
                "rows": 0, "success": 0, "net": None,
                "median_T_dec": per_block, "total_T_dec": 0.0,
                "C_total": max(float(WORKPOINTS[wp]["C_total"]),
                               float(B * N))}
    # R7 实现细节：overtime-risk 阈值 = max(2×运行中位, OVERTIME_FLOOR_S)，
    # 下限 30s 避免计时器粒度下小格误标（包"超预算>2×中位"针对全尺寸格）。
    status_note = ""
    if med_times and extrap > max(2 * med, OVERTIME_FLOOR_S):
        status_note = (f"overtime-risk: smoke-extrap {extrap:.0f}s > "
                       f"2×median {med:.0f}s; sharded")
    cell = _run_shards(wp, method, N, M, B=B, seed=seed, out=out,
                       deadline=deadline)
    if status_note and cell.get("status", "ok") == "ok":
        cell["status"] = "overtime-risk"
        cell["detail"] = status_note + "; completed full B"
    if _jsonl_count(out) < B:
        cell["status"] = "short" if cell.get(
            "status", "ok") == "ok" else cell.get("status")
        cell["detail"] = (cell.get("detail", "") +
                          f"; short: { _jsonl_count(out)}/{B} blocks").strip(
                              "; ")
    return cell


def _recount_cell(wp: str, method: str, N: int, M: float, *, B: int,
                  seed: int, out: Path) -> dict:
    """续跑复用：已落盘满 B 行时不重译码，直接由行重计汇总（T_dec 由行累加，
    R7 历史标记见 C3_LOG；科学口径与正常路径一致）。"""
    rows = [json.loads(line) for line in out.read_text(
        encoding="utf-8").splitlines() if line.strip()]
    succ = sum(int(r.get("ver", 0)) for r in rows)
    und = sum(int(r.get("u", 0)) for r in rows)
    spec = WORKPOINTS[wp]
    ok_rows = [r for r in rows if r.get("ver") == 1 and not r.get("u")]
    kept = float(ok_rows[0]["kept"]) if ok_rows else 0.0
    lec = float(rows[0]["L_EC"]) if rows else 0.0
    if family_of(method) == "bin":
        h_op, i_op = h2(spec["p"]), 1.0 - h2(spec["p"])
    else:
        H = nbpolar.prior_entropy_bits(channel_prior(wp))
        h_op, i_op = H, math.log2(spec["q"]) - H
    C_cell = max(float(spec["C_total"]), float(B * N))
    net = runner.net_of_cell(
        kept_bits=kept, L_EC_bits=lec, tag_bits=TAG,
        n_fail=B - succ, n_blocks=B, C_total=C_cell, N=N,
        n_undetected=und, h_op=h_op, I_op=i_op)
    tdecs = [float(r.get("T_dec", 0.0)) for r in rows]
    return {"method": method, "WP": wp, "N": N, "M": M, "B": B,
            "rows": B, "success": succ, "undetected": und,
            "status": "ok",
            "detail": "resumed-recount from full rows (no re-decode)",
            "median_T_dec": float(np.median(tdecs)) if tdecs else 0.0,
            "total_T_dec": float(sum(tdecs)),
            "code_hash": rows[0].get("code_hash", "") if rows else "",
            "frozen_hash": rows[0].get("frozen_hash", "") if rows else "",
            "lec_bits": int(lec), "kept": kept,
            "C_total": C_cell, "net": net}


def _run_shards(wp: str, method: str, N: int, M: float, *, B: int,
                seed: int, out: Path,
                deadline: float | None) -> dict:
    """分片续跑：按已落盘行数续跑，每 SHARD 检查墙钟；撞墙保留已完成块。"""
    if _jsonl_count(out) >= B:
        return _recount_cell(wp, method, N, M, B=B, seed=seed, out=out)
    cell: dict = {}
    try:
        while _jsonl_count(out) < B:
            if deadline is not None and time.perf_counter() > deadline:
                break
            # 单次推进至多 SHARD 块：复用整格执行（其内部按已落盘续跑）。
            cell = _run_one_cell(wp, method, N, M, B=B, seed=seed,
                                 out=out)
            if cell.get("status") in ("infeasible", "construction-fail",
                                      "unavailable"):
                break
            if _jsonl_count(out) < B and cell.get("status") == "ok":
                # 无进展保护：整格执行一次即跑满；若未满则标 short 退出。
                break
    except Exception as exc:
        cell = {"method": method, "WP": wp, "N": N, "M": M, "B": B,
                "status": "construction-fail",
                "detail": f"{type(exc).__name__}: {exc}",
                "rows": _jsonl_count(out), "success": 0, "net": None}
    if not cell:
        cell = {"method": method, "WP": wp, "N": N, "M": M, "B": B,
                "status": "short", "detail": "wall-budget-hit before start",
                "rows": 0, "success": 0, "net": None}
    return cell


# ---------------- 汇总表（主表/明细/未定/最优 N） ----------------

def _mask_count(x) -> str:
    return "未定" if (x is None or int(x) <= 9) else str(int(x))


def build_tables(manifest: dict, root: Path) -> dict:
    """由 manifest cells 建明细表 + 主表（每 WP×方法一行最优 N）。

    未定：F≤9 或 S≤9 的格 FER/计数写「未定」，不参选；全行未定 →
    「无有效最优（全未定）」。最优 N 只在 decided 且 N_valid 格中按 Net_seg
    最大选；并列差 <1% 取小 N 注 ``tie→smallerN``。fresh/mapped 永不混排
    （本函数只处理 fresh；mapped 另表）。
    """
    cells = [c for c in manifest["cells"]
             if not c.get("anchor") or c.get("anchor_winner")]
    detail_rows: list[dict] = []
    for c in cells:
        undecided = (c.get("F") is None or c.get("S_main") is None
                     or int(c["F"]) <= 9 or int(c["S_main"]) <= 9)
        fer_disp = "未定" if undecided else f"{c['FER_hat']:.6f}"
        detail_rows.append({
            "WP": c["WP"], "method": c["method"], "N": c["N"],
            "M": c["M"], "B": c["B"], "status": c["status"],
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
            "beta_warning": c["beta_warning"] or BETA_WARNING,
            "w_tail": c["w_tail"], "C_total": c["C_total"],
            "median_T_dec": c["median_T_dec"],
            "total_T_dec": c["total_T_dec"],
            "code_hash": c["code_hash"],
            "frozen_hash": c["frozen_hash"],
            "detail": c["detail"]})
    # 主表：每 (WP, 方法) 一行。
    main_rows: list[dict] = []
    pairs = sorted({(c["WP"], c["method"]) for c in cells})
    for wp, method in pairs:
        cand = [c for c in cells
                if c["WP"] == wp and c["method"] == method
                and c["decided"] and c["N_valid"]
                and c["status"] == "ok" and c["Net_seg"] is not None]
        n_valid_list = sorted({c["N"] for c in cells
                               if c["WP"] == wp and c["method"] == method
                               and c["N_valid"]})
        if not cand:
            main_rows.append({
                "WP": wp, "method": method, "N_valid": n_valid_list,
                "N_opt": "无有效最优（全未定）", "B": "", "M": "",
                "Net_seg": "", "Net_per_coin": "", "f_full": "",
                "f_same_time": "", "FER_hat": "未定",
                "beta_side": "", "beta_warning": BETA_WARNING,
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
            "WP": wp, "method": method, "N_valid": n_valid_list,
            "N_opt": best["N"], "B": best["B"], "M": best["M"],
            "Net_seg": best["Net_seg"],
            "Net_per_coin": best["Net_per_coin"], "f_full": best["f_full"],
            "f_same_time": "extrap.-pending", "FER_hat": best["FER_hat"],
            "beta_side": best["beta_side"],
            "beta_warning": BETA_WARNING, "w_tail": best["w_tail"],
            "note": note})
    # 相同译码时间 f：T_ref 取已定最优格总时间中位，线性外推。
    t_opts = [c["total_T_dec"] for c in cells
              if c["decided"] and c["total_T_dec"]]
    t_ref = float(np.median(t_opts)) if t_opts else 0.0
    for m in main_rows:
        if m["N_opt"] == "无有效最优（全未定）":
            continue
        src = next(c for c in cells
                   if c["WP"] == m["WP"] and c["method"] == m["method"]
                   and c["N"] == m["N_opt"])
        t_cell = src["total_T_dec"] or 0.0
        if t_cell > 0 and t_ref > 0:
            m["f_same_time"] = (
                f"{m['Net_seg'] * (t_ref / t_cell):.1f} (extrap., "
                f"T_ref={t_ref:.1f}s)")
        else:
            m["f_same_time"] = "extrap.-n/a"
    _write_csv(root / "net_detail_fresh.csv", detail_rows)
    _write_csv(root / "net_main_fresh.csv", main_rows)
    # 映射层（分表，永不混排）：历史行摘要 JSON 缺位则空置并注记。
    mapped = _build_mapped(root)
    return {"detail": detail_rows, "main": main_rows, "mapped": mapped,
            "T_ref": t_ref}


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


def _build_mapped(root: Path) -> dict:
    """映射层：A1/A2 的 G-5/Z-1/Z-3 历史行、A6 的 F-1/S-5/D-4 行经
    ``net_of_cell`` 按 R16 重算后进入明细表（证据类型 ``mapped``）。

    本 checkout 内无上述历史行摘要 JSON（C1_INVENTORY 仅代码指针，未给
    数据路径；workspace 全盘查找无 G-5/Z-1/Z-3/F-1/S-5/D-4 摘要 JSON），
    故 mapped 表空置并附注记；适配器（runner.adapt_*）保持可用待历史行到位。
    fresh/mapped 分表，永不混排。
    """
    note = ("mapped 空置：未发现 G-5/Z-1/Z-3（A1/A2）与 F-1/S-5/D-4（A6）"
            "历史行摘要 JSON（C1_INVENTORY 仅代码指针）；适配器 "
            "runner.adapt_g5_block/adapt_layered_lite_result/adapt_m4_block "
            "就绪，历史行到位后按 R16 net_of_cell 重算。读摘要 JSON，不重跑 "
            "DECIDE。")
    (root / "mapped_NOTE.txt").write_text(note + "\n", encoding="utf-8")
    _write_csv(root / "net_detail_mapped.csv", [])
    _write_csv(root / "net_main_mapped.csv", [])
    # A7 unavailable 列位（无 runner 即如实空缺，不得伪造）。
    a7_rows = []
    for wp in ("F1", "F2", "F3"):
        for N in N_GRID:
            r = runner.adapt_a7_row(N=N, block=0)
            r.update({"WP": wp, "M": "", "evidence": "mapped",
                      "detail": "A7 MLC-Polar 只读调用不在本批范围，"
                                "unavailable 列位"})
            a7_rows.append(r)
    _write_csv(root / "a7_column.csv", a7_rows)
    return {"note": note, "a7_rows": len(a7_rows)}


# ---------------- CLI ----------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="C-3 合成调参冻结驱动")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--direction-smoke", action="store_true")
    ap.add_argument("--output-root", default="workspace/c3_tune/c3_20261008")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--budget-s", type=float, default=BUDGET_S)
    ap.add_argument("--cell-budget-s", type=float, default=CELL_BUDGET_S)
    ap.add_argument("--seed", type=int, default=SEED_BASE)
    args = ap.parse_args(argv)
    root = Path(args.output_root)
    if args.direction_smoke:
        res = direction_smoke()
        print(json.dumps(res, indent=2))
        return 0 if res["pass"] else 1
    if args.dry_run:
        if root.exists() and not args.resume:
            print(f"refuse: output root exists: {root}",
                  file=sys.stderr)
            return 2
        try:
            manifest = run_grid(
                root=root, B=8, seed=args.seed,
                methods=("A1", "A2", "A3", "A4"),
                workpoints=("F1",), Ns=(32, 64),
                budget_s=args.budget_s,
                cell_budget_s=args.cell_budget_s, resume=args.resume)
        except SystemExit as exc:
            print(f"STOP: {exc}", file=sys.stderr)
            return 3
        tables = build_tables(manifest, root)
        print(json.dumps({"cells": len(manifest["cells"]),
                          "main": len(tables["main"])}, indent=2))
        return 0
    if args.full:
        # 输出根执行前须不存在（fresh-root 纪律；--resume 除外用于分片续跑）。
        if root.exists() and not args.resume:
            print(f"refuse: output root exists (fresh-root): {root}",
                  file=sys.stderr)
            return 2
        try:
            manifest = run_grid(root=root, B=B_FULL, seed=args.seed,
                                budget_s=args.budget_s,
                                cell_budget_s=args.cell_budget_s,
                                resume=args.resume)
        except SystemExit as exc:
            print(f"STOP: {exc}", file=sys.stderr)
            return 3
        tables = build_tables(manifest, root)
        print(json.dumps({"cells": len(manifest["cells"]),
                          "main": len(tables["main"]),
                          "wall_s": manifest.get("wall_s")}, indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
