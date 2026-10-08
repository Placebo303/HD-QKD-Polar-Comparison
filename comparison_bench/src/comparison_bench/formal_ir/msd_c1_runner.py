"""C-1 统一 runner + R16 记账 + A1/A2/A5/A6/A7 适配（OP2, C1_PACKET.md §3.4）.

记账公式依据 ``C3_DESIGN.md`` §1（R16），逐字实现，不另立口径：
- 逐块净贡献 ``net_i = ver_i·(1−u_i)·(kept_i − L_EC,i − TAG) − (1−ver_i)·L_EC,i``
- ``Net_seg = Σ net_i``；``L_total = Σ L_EC,i + S_main·TAG``
- ``Net_per_coin = Net_seg / C_total``（主分母含尾部，不得换 C_used）
- ``Net_per_used = Net_seg / C_used``（诊断列）
- ``FER_hat = F/B``（点估计主用）；``U_rate = U/B`` 独立列，永不并入 FER
- ``FER_wilson_hi`` 只作敏感性列；``w_tail`` 必报
- ``f_full = L_total / (B·N·h_op)``；β 为附带列，随表强制附警示语。

``run_cell`` 只跑合成参数化信道（``(p, p_minus, k)`` 或 ``(q, p)`` 或 BSC 退化），
不重跑任何 DECIDE 数据（A1/A2/A5/A6 一律走纯映射适配器，不在本函数内执行）。
A7 为 sibling 只读 import，缺失则行状态 ``unavailable`` 透传（不断言失败）。

先验口径说明：本模块的合成先验由 ``_prior_from_channel`` 本地构造
（(p,p_minus) 对称分配，rest 质量单独列），与 OP1 k-bin 的 ``params_from_stats``
为各自独立实现；runner 内生成与译码使用同一先验（自洽），不跨模块对口径。
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbpolar as nbpolar

__all__ = [
    "TAG_BITS",
    "ALLOWED_STATUSES",
    "ROW_KEYS",
    "BETA_WARNING",
    "SIBLING_ROOT",
    "wilson_upper",
    "net_of_cell",
    "run_cell",
    "adapt_g5_block",
    "adapt_layered_lite_result",
    "adapt_m4_block",
    "sibling_polar_core_available",
    "adapt_a7_row",
]

TAG_BITS = 64
ALLOWED_STATUSES = ("ok", "reference", "stub", "unavailable", "decode_failed")
ROW_KEYS = ("method", "N", "block", "ver", "u", "kept", "L_EC", "tag",
            "T_dec", "code_hash")
BETA_WARNING = ("β为附带列，不作为主度量；β对p估计敏感、跨k/D不可比，"
                "且失败惩罚与TAG处理不同即不可比。方法排序以Net_seg / "
                "Net_per_coin为准，β仅供一致性检查。")
SIBLING_ROOT = "D:/Code/HD-QKD_Polar_Release"


def wilson_upper(n_fail: int, n_blocks: int, z: float = 1.96) -> float:
    """Wilson 95% 上界（敏感性列专用；n_blocks<=0 时返回 1.0 保守值并注明）。"""
    n = int(n_blocks)
    if n <= 0:
        return 1.0
    f = max(0, int(n_fail))
    p = min(1.0, f / n)
    z2 = float(z) ** 2
    denom = 1.0 + z2 / n
    center = p + z2 / (2.0 * n)
    half = float(z) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))
    return min(1.0, (center + half) / denom)


def net_of_cell(*, kept_bits, L_EC_bits, tag_bits=TAG_BITS, n_fail,
                n_blocks, C_total, N, n_undetected=0, h_op=None,
                I_op=None) -> dict:
    """R16 格记账纯函数（C3_DESIGN.md §1）。

    ``kept_bits`` = 每成功块保留比特；``L_EC_bits`` = 每块披露比特（含失败块
    已公开部分，不清零）；``tag_bits`` = 每成功块标签开销（默认 64，失败块不扣）。
    ``n_fail`` F（u 不计入 F）；``n_undetected`` U（主记账 kept 取 0，
    其 net_i 按冻结公式取 0，即 ver=1,u=1 时两项皆零，特此注明）。
    ``C_total`` = 该段采集对数（分母，尾部浪费自动受罚）；``N`` = 块长。
    ``h_op`` 给定时算 ``f_full``/``f_noTAG``；``I_op`` 给定时算 ``beta_side``
    （附带列，输出含强制警示语 ``beta_warning``）。
    """
    kept = float(kept_bits)
    lec = float(L_EC_bits)
    tag = float(tag_bits)
    F = int(n_fail)
    B = int(n_blocks)
    U = int(n_undetected)
    N = int(N)
    C_total = float(C_total)
    if B < 1 or N < 1:
        raise ValueError("n_blocks and N must be >= 1")
    if F < 0 or U < 0 or F + U > B:
        raise ValueError("require 0 <= F, 0 <= U, F+U <= B")
    if not (math.isfinite(kept) and math.isfinite(lec) and kept >= 0 and lec >= 0):
        raise ValueError("kept_bits/L_EC_bits must be finite and >= 0")
    C_used = float(B * N)
    if not math.isfinite(C_total) or C_total < C_used:
        raise ValueError("C_total must be finite and >= B*N")
    S_main = B - F - U
    net_seg = S_main * (kept - lec - tag) - F * lec  # U 项按冻结公式为 0
    L_total = B * lec + S_main * tag
    C_tail = C_total - C_used
    w_tail = C_tail / C_total if C_total > 0 else 0.0
    fer = F / B
    u_rate = U / B
    fer_w_hi = wilson_upper(F, B)
    F_w = fer_w_hi * B
    S_w = B - F_w - U
    net_seg_wilson_hi = S_w * (kept - lec - tag) - F_w * lec
    f_full = f_noTAG = None
    if h_op is not None:
        h = float(h_op)
        if h > 0:
            denom = B * N * h
            f_full = L_total / denom
            f_noTAG = (B * lec) / denom
    beta_side = beta_warning = None
    if I_op is not None:
        iop = float(I_op)
        if iop > 0:
            beta_side = net_seg / (C_used * iop)
            beta_warning = BETA_WARNING
    return {
        "S_main": S_main, "F": F, "U": U, "B": B,
        "Net_seg": net_seg, "L_total": L_total,
        "C_used": C_used, "C_tail": C_tail, "w_tail": w_tail,
        "Net_per_coin": net_seg / C_total if C_total > 0 else 0.0,
        "Net_per_used": net_seg / C_used,
        "FER_hat": fer, "U_rate": u_rate,
        "FER_wilson_hi": fer_w_hi, "net_seg_wilson_hi": net_seg_wilson_hi,
        "f_full": f_full, "f_noTAG": f_noTAG,
        "beta_side": beta_side, "beta_warning": beta_warning,
        "tag_bits": tag,
    }


def _prior_from_channel(channel: dict):
    """合成先验本地构造（见模块 docstring 口径说明）。

    接受 ``{"k":k,"p":p,"p_minus":pm}``（q=2k+1）或 ``{"q":q,"p":p,...}``；
    ``p_minus`` 缺省时剩余质量在 q−1 个非零元上均匀分；给出时
    ``g[q−1] = p_minus``（e=−1 位置），其余非零元均分 ``p − p_minus``
    （要求 0 ≤ p_minus ≤ p）。BSC 退化：``{"bsc_p": p}`` 视为 q=2（仅记账
    用；A4 要求素数 q，run_cell 内另行校验）。
    返回 ``(q, prior_g list)``，``prior_g[e] = P((b−a) mod q = e)``。
    """
    ch = dict(channel)
    if "bsc_p" in ch and "k" not in ch and "q" not in ch:
        p = float(ch["bsc_p"])
        if not (0.0 <= p < 1.0):
            raise ValueError(f"bsc_p must be in [0,1), got {p}")
        return 2, [1.0 - p, p]
    if "k" in ch:
        k = int(ch["k"])
        q = 2 * k + 1
    elif "q" in ch:
        q = int(ch["q"])
    else:
        raise ValueError("channel must carry 'k' or 'q' (or 'bsc_p')")
    p = float(ch.get("p", 0.0))
    if not (0.0 <= p < 1.0):
        raise ValueError(f"p must be in [0,1), got {p}")
    g = [0.0] * q
    g[0] = 1.0 - p
    if "p_minus" in ch and ch["p_minus"] is not None:
        pm = float(ch["p_minus"])
        if not (0.0 <= pm <= p):
            raise ValueError(f"require 0 <= p_minus <= p, got {pm} vs {p}")
        rest = (p - pm) / (q - 2) if q > 2 else 0.0
        for e in range(1, q - 1):
            g[e] = rest
        g[q - 1] = pm
    else:
        rest = p / (q - 1) if q > 1 else 0.0
        for e in range(1, q):
            g[e] = rest
    return q, g


def _choose_m(N: int, q: int, prior_g, gap: float = 0.15) -> int:
    """C-1 合成码率规则（非 C-3 冻结函数，特此注明）。

    ``m = clip(ceil(N·(H/log2(q) + gap)), 1, N−1)``，H 为先验熵（比特）。
    ``channel`` 可带 ``"m"`` 直接覆盖（测试用保守码率），或带 ``"rate"`` R
    则 ``m = N − round(N·R)``。
    """
    H = nbpolar.prior_entropy_bits(prior_g)
    rate_gap = H / math.log2(q) + float(gap)
    m = int(math.ceil(N * rate_gap))
    return max(1, min(int(N) - 1, m))


def _unavailable_row(*, method, N, block, code_hash="", detail="") -> dict:
    return {"method": method, "N": int(N), "block": int(block),
            "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
            "T_dec": 0.0, "code_hash": code_hash,
            "undetected": False, "status": "unavailable", "detail": detail}


def run_cell(method, N, channel, B, seed, out_jsonl, *, tag_bits=TAG_BITS,
             gap=0.15, C_total=None, list_size=1) -> dict:
    """合成 cell 执行（只跑合成参数化信道，B 由调用方定；本批测试用 B≤30）。

    ``method="A4"``：本仓库 NB-Polar 全链路（构造→披露→译码→tag 复核→落盘）。
    ``method="A3"``：OP1 模块存在则同形试跑，缺失则 ``unavailable`` 行透传。
    ``method="A7"``：sibling 只读试探，缺失则 ``unavailable`` 行透传。
    ``A1/A2/A5/A6`` 在此函数内不执行（其 DECIDE 数据不得重跑），一律
    ``ValueError`` 并指引对应适配器；未知 method 同样 ``ValueError``。
    行键冻结：``ROW_KEYS`` + ``undetected`` 单列 + ``status``（值域见
    ``ALLOWED_STATUSES``，永不把失败私自转 ``ok``）。JSONL 追加写（不覆盖）。
    返回 ``summary``（含 ``net`` = ``net_of_cell`` 结果）。
    """
    N = int(N)
    B = int(B)
    seed = int(seed)
    if B < 1:
        raise ValueError("B must be >= 1")
    out_path = Path(out_jsonl)
    if out_path.parent and str(out_path.parent) not in ("", "."):
        out_path.parent.mkdir(parents=True, exist_ok=True)

    if method in ("A1", "A2", "A5", "A6"):
        raise ValueError(
            f"run_cell does not execute {method}: use adapt_g5_block / "
            "adapt_layered_lite_result / adapt_m4_block on existing rows, "
            "DECIDE data must not be re-run")
    if method not in ("A3", "A4", "A7"):
        raise ValueError(f"unknown method {method!r}")

    if method == "A7":
        avail = sibling_polar_core_available()
        rows = [_unavailable_row(method="A7", N=N, block=b,
                                 detail="sibling polar_core missing"
                                 if not avail["available"] else "A7 synthetic not executed")
                for b in range(B)]
        if avail["available"]:
            for r in rows:
                r["status"] = "stub"
                r["detail"] = "sibling present; A7 MLC-Polar call not in C-1 scope"
        with out_path.open("a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return {"method": "A7", "N": N, "B": B, "rows": B,
                "success": 0, "undetected": 0, "status": rows[0]["status"]}

    if method == "A3":
        try:
            mod = importlib.import_module(
                "comparison_bench.src.comparison_bench.formal_ir.msd_c1_nbldpc")
            _ = (mod.construct, mod.disclose, mod.decode)
        except Exception as exc:
            rows = [_unavailable_row(method="A3", N=N, block=b,
                                     detail=f"A3 module missing: {type(exc).__name__}")
                    for b in range(B)]
            with out_path.open("a", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            return {"method": "A3", "N": N, "B": B, "rows": B,
                    "success": 0, "undetected": 0, "status": "unavailable"}
        raise ValueError("A3 module present but C-1 OP2 does not own its call convention; "
                         "OP1 owns A3 execution")

    # ---- A4 native path ----
    ch = dict(channel)
    q, prior_g = _prior_from_channel(ch)
    if q not in nbpolar.SUPPORTED_Q:
        raise ValueError(f"A4 requires prime q in {nbpolar.SUPPORTED_Q}, got {q}")
    if N < 2 or (N & (N - 1)) != 0:
        raise ValueError(f"A4 requires N a power of two >= 2, got {N}")
    if "m" in ch and ch["m"] is not None:
        m = int(ch["m"])
        if not (0 < m < N):
            raise ValueError(f"channel m must satisfy 0 < m < N, got {m}")
    elif "rate" in ch and ch["rate"] is not None:
        R = float(ch["rate"])
        m = N - int(round(N * R))
        if not (0 < m < N):
            raise ValueError(f"channel rate {R} infeasible at N={N}")
    else:
        m = _choose_m(N, q, prior_g, gap=gap)
    k_info = N - m
    ch_for_frozen = dict(ch)
    ch_for_frozen.setdefault("q", q)
    code = nbpolar.construct(N, m, q, seed, channel=ch_for_frozen,
                             prior_g=list(prior_g))
    kept_per_success = k_info * math.log2(q)
    rng = np.random.default_rng(seed)
    rows = []
    n_succ = 0
    t_dec_list = []
    for b in range(B):
        a = rng.integers(0, q, N).tolist()
        e = rng.choice(q, size=N, p=np.asarray(prior_g) / sum(prior_g))
        bb = ((np.asarray(a) + np.asarray(e)) % q).tolist()
        syn, lec_bits = code.disclose(a)
        t0 = time.perf_counter()
        a_hat = code.decode(bb, syn, list(prior_g), 50, list_size=int(list_size))
        t_dec = time.perf_counter() - t0
        t_dec_list.append(t_dec)
        good = a_hat is not None and list(a_hat) == list(a)
        n_succ += int(good)
        rows.append({
            "method": "A4", "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept_per_success) if good else 0.0,
            "L_EC": int(lec_bits), "tag": int(tag_bits) if good else 0,
            "T_dec": float(t_dec), "code_hash": code.code_hash,
            "undetected": False, "status": "ok" if good else "decode_failed",
        })
    with out_path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    C_tot = float(C_total) if C_total is not None else float(B * N)
    H = nbpolar.prior_entropy_bits(prior_g)
    net = net_of_cell(kept_bits=kept_per_success, L_EC_bits=rows[0]["L_EC"],
                      tag_bits=tag_bits, n_fail=B - n_succ, n_blocks=B,
                      C_total=C_tot, N=N, n_undetected=0, h_op=H,
                      I_op=math.log2(q) - H)
    return {"method": "A4", "N": N, "B": B, "q": q, "m": m,
            "k_info": k_info, "code_hash": code.code_hash,
            "rows": B, "success": n_succ, "undetected": 0,
            "median_T_dec": float(np.median(t_dec_list)),
            "net": net}


def _check_row(row: dict) -> dict:
    missing = [k for k in ROW_KEYS if k not in row]
    if missing:
        raise ValueError(f"unified row missing keys {missing}")
    if row.get("status") not in ALLOWED_STATUSES:
        raise ValueError(f"status {row.get('status')!r} not in {ALLOWED_STATUSES}")
    return row


def adapt_g5_block(rec: dict, *, method, N, kept_bits, tag_bits=TAG_BITS,
                   code_hash="", T_dec=0.0) -> dict:
    """A1/A2 适配：G-5/G-2 per-block 口径转统一行（纯映射，不重跑 DECIDE 数据）。

    输入 ``rec`` 键：``{block, a_ok, exact_full, undetected, L_A, L_B, extra}``
    （C1_INVENTORY.md §1）。映射：``ver = exact_full ∨ undetected``
   （两者皆为"声称成功过验证"）；``u = undetected``；``kept`` 仅当
    ``exact_full ∧ ¬undetected`` 时计入（undetected 永隔离，kept 取 0）；
    ``L_EC = L_A + L_B + extra``；``tag`` 仅 ver 块扣；exact→``ok``，
    undetected→``ok``（验证通过但 kept 隔离，特此注明锁定），其余→
    ``decode_failed``。``kept_bits`` 由调用方按该 N/工作点理论值传入，
    本函数不估算信息量。
    """
    und = bool(rec.get("undetected"))
    exact = bool(rec.get("exact_full"))
    ver = int(exact or und)
    lec = int(rec.get("L_A", 0)) + int(rec.get("L_B", 0)) + int(rec.get("extra", 0))
    kept = float(kept_bits) if (exact and not und) else 0.0
    status = "ok" if (exact or und) else "decode_failed"
    if method not in ("A1", "A2"):
        raise ValueError(f"adapt_g5_block only for A1/A2, got {method!r}")
    return _check_row({
        "method": method, "N": int(N), "block": int(rec.get("block", 0)),
        "ver": ver, "u": int(und), "kept": kept, "L_EC": lec,
        "tag": int(tag_bits) if ver else 0, "T_dec": float(T_dec),
        "code_hash": code_hash or f"{method}-N{int(N)}-g5-adapted",
        "undetected": und, "status": status,
    })


def adapt_layered_lite_result(result, *, method="A5", tag_bits=TAG_BITS,
                              code_hash="") -> list:
    """A5 适配：``run_layered_ldpc_lite`` 结果转统一行（纯映射，不执行译码）。

    接受 ``IRRunResult`` 对象或等效 dict（须含 ``frame_results`` 列表与
    ``metadata.method_status``）。映射：``ver = decode_success ∧ verify_success``；
    ``u = 0``（该方法无 undetected 概念，恒 0 并注明）；``L_EC =
    syndrome_bits_frame``；``tag = verification_bits_frame``（成功块；该方法
    原生 32bit 校验，与 R16 TAG=64 的差异由调用方 ``tag_bits`` 覆盖，默认取
    R16 64 并在 detail 注明）；``kept`` 由调用方 ``kept_bits`` 传入
    （frame_len_bits）。``method_status != "ok"`` 的行永不转 ``ok``：
    ``unavailable`` 保持，其余→``decode_failed``。
    """
    if method != "A5":
        raise ValueError(f"adapt_layered_lite_result only for A5, got {method!r}")
    if isinstance(result, dict):
        frames = result.get("frame_results") or result.get("metadata", {}).get("frame_results", [])
        mstatus = result.get("method_status") or result.get("metadata", {}).get("method_status", "")
        dsid = result.get("dataset_id", "")
    else:
        meta = getattr(result, "metadata", None) or {}
        frames = meta.get("frame_results", []) if isinstance(meta, dict) else []
        mstatus = meta.get("method_status", "") if isinstance(meta, dict) else ""
        dsid = getattr(result, "dataset_id", "")
    rows = []
    for fr in frames:
        ok = bool(fr.get("decode_success")) and bool(fr.get("verify_success"))
        # 锁定规则：仅当 method_status == "ok" 且本帧成功才记 ok；
        # unavailable 透传；其余一律 decode_failed（永不把非 ok 转 ok）。
        if mstatus == "unavailable":
            status = "unavailable"
        elif mstatus == "ok" and ok:
            status = "ok"
        else:
            status = "decode_failed"
        nbits = int(fr.get("syndrome_bits_frame", 0))
        vbits = int(fr.get("verification_bits_frame", 0))
        flen = int(fr.get("frame_len_bits", 0) or 0)
        kept = float(flen) if ok else 0.0
        rows.append(_check_row({
            "method": "A5", "N": int(fr.get("frame_len_symbols", fr.get("h_cols", 0)) or 0),
            "block": int(fr.get("frame_idx", 0)),
            "ver": int(ok), "u": 0, "kept": kept, "L_EC": nbits,
            "tag": int(tag_bits) if ok else 0,
            "T_dec": float(fr.get("runtime_ms", 0.0)) / 1000.0,
            "code_hash": code_hash or f"A5-layered-lite-{dsid}-adapted",
            "undetected": False, "status": status,
            "detail": f"native_verify_bits={vbits}; tag_bits={int(tag_bits) if ok else 0}",
        }))
    return rows


def adapt_m4_block(rec: dict, *, method="A6", kept_bits, tag_bits=TAG_BITS,
                   code_hash="", T_dec=None) -> dict:
    """A6 适配：``msd_m4_nbldpc`` 行口径转统一行（frozen v28 不动，纯映射）。

    输入行键：``{source, N, block, m_total, L_EC, exact_ok, undetected, ...}``
    （``run_nb_point``/``_decode_one`` 落盘口径）。``ver = exact_ok ∨
    undetected``；``undetected`` 永单列隔离（kept 取 0）；exact→``ok``，
    undetected→``ok``（验证通过但 kept 隔离，锁定），其余→``decode_failed``；
    ``overrun`` 真的行视为失败（``decode_failed``，ver 取 0）并在 detail 注明。
    """
    if method != "A6":
        raise ValueError(f"adapt_m4_block only for A6, got {method!r}")
    und = bool(rec.get("undetected"))
    exact = bool(rec.get("exact_ok"))
    over = bool(rec.get("overrun"))
    ver = int((exact or und) and not over)
    kept = float(kept_bits) if (exact and not und and not over) else 0.0
    if over:
        status = "decode_failed"
    else:
        status = "ok" if (exact or und) else "decode_failed"
    t = float(rec.get("wall_s", 0.0)) if T_dec is None else float(T_dec)
    row = {
        "method": "A6", "N": int(rec.get("N", 1024)), "block": int(rec.get("block", 0)),
        "ver": ver, "u": int(und), "kept": kept, "L_EC": int(rec.get("L_EC", 0)),
        "tag": int(tag_bits) if ver else 0, "T_dec": t,
        "code_hash": code_hash or "A6-nbldpc-v28-frozen-adapted",
        "undetected": und, "status": status,
    }
    if over:
        row["detail"] = "block overrun: counted as failure"
    return _check_row(row)


def sibling_polar_core_available() -> dict:
    """sibling ``low_dim_opt.core.polar_core`` 只读可用性（缺失不断言失败）。"""
    try:
        if SIBLING_ROOT not in sys.path:
            sys.path.insert(0, SIBLING_ROOT)
        mod = importlib.import_module("low_dim_opt.core.polar_core")
        return {"available": True, "detail": getattr(mod, "__name__", "?")}
    except Exception as exc:
        return {"available": False, "detail": f"{type(exc).__name__}: {exc}"}


def adapt_a7_row(*, N, block, available=None, kept_bits=0.0,
                 code_hash="") -> dict:
    """A7 适配行。sibling 缺失（或 ``available=False``）→ ``unavailable`` 透传；
    存在也只记 ``stub``（C-1 不执行 MLC-Polar 只读调用，特此注明）。"""
    if available is None:
        available = bool(sibling_polar_core_available().get("available"))
    if not available:
        return _check_row({**_unavailable_row(method="A7", N=N, block=block,
                                              code_hash=code_hash,
                                              detail="sibling polar_core missing"),
                           "detail": "sibling polar_core missing"})
    return _check_row({
        "method": "A7", "N": int(N), "block": int(block),
        "ver": 0, "u": 0, "kept": 0.0, "L_EC": 0, "tag": 0,
        "T_dec": 0.0, "code_hash": code_hash or "A7-sibling-stub",
        "undetected": False, "status": "stub",
        "detail": "sibling present; MLC-Polar call not in C-1 scope",
    })


def _sha_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
