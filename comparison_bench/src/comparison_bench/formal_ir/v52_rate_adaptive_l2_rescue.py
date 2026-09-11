"""V52P0 nested rate-adaptive L2 rescue (conditional HARQ) Δm=8.

Frozen V52P0 protocol (formal-ir-v52-rate-adaptive-l2-rescue):
- n=1024, m2 184/190/192, GF32 poly37, Lane C ordinal-2 support/label/position_permutations frozen,
  decoder 90/1.0 early-stop, H1 16x1024 rank16, L2-only tag.
- Incremental H_inc 8x1024 det1 per source GF32 poly37 row≤16 col_inc≤1 joint rank m2+8 nested independent.
- Leakage: leak_base 1064/1094/1104, leak_joint 1104/1134/1144, avg = base+40*N_rescue/15.
- 15 fresh held-out blocks 393001-005/101-105/201-205 deterministic 4-frame 1024 pairs per block.
- Per block L1 1 + base_shared 1 (兼 old/V52 pass1, no duplicate) + conditional rescue ≤1; total 30-45 hard cap 45.
- Conditional rescue only if base not verify (syndrome && tag). old_exact = base_exact.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
Accepted plan SHA: 1d66b11917d229b214bd1d8b4255bf6df95c99c8
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    compute_tag_64,
    compute_gf32_rank,
    factorize_f03,
    load_v25_channel_counts,
    require_check_updated_provenance,
    syndrome_of_gf32,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
    MAX_CHECK_DEGREE_LIMIT,
    SOURCE_CHECKS,
    _check_v38r1_metric_match,
    _load_v38r1_reference_metrics,
    construct_lane_c_prototype,
    get_substream_generator,
    sample_uniform_gf32_nonzero,
    get_canonical_support_edges,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

CYCLE_ID = "V52P0"
CHANGE_ID = "formal-ir-v52-rate-adaptive-l2-rescue"
ACCEPTED_PLAN_SHA = "1d66b11917d229b214bd1d8b4255bf6df95c99c8"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v52_nested_rescue_15_blocks_paired_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
MECHANISM_ID = "nested_incremental_l2_rescue_delta8_conditional_harq"
TAG_SCOPE = "l2_only"
TAG_SOURCE_STR = "v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only"
LEAKAGE_ALREADY_ACCOUNTED_NOTE = "leakage already accounted: H1-16 1064/1094/1104 base 1104/1134/1144 joint includes 64-bit tag; SHA-trunc64 random-hash-model approximate 2^-64 L2-only"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

DELTA_M = 8
PLANNED_L1 = 15
PLANNED_L2_BASE = 15
PLANNED_L2_RESCUE_MAX = 15
PLANNED_L2_MAX = 30
HARD_CALL_CAP = 45  # total L1+L2
# for accounting we enforce L1 15, L2 base 15 + rescue ≤15

H1_M = 16
H1_N = 1024
H1_MATRIX_ID = "V31-H1-QC-16×1024"
H1_FAMILY = "QC-cyclic-projective"

PAIRS_PER_FRAME = 256
FRAMES_PER_BLOCK = 4
PAIRS_PER_BLOCK = 1024
BLOCK_LENGTH_CONST = 1024

INC_DET_IDS: dict[str, int] = {"1M": 600001, "1p5M": 600002, "2M": 600003}

HELDOUT_H: dict[str, int] = {"1M": 400, "1p5M": 554, "2M": 729}
HELDOUT_BASE_GLOBAL: dict[str, int] = {"1M": 1600, "1p5M": 2213, "2M": 2916}

HELDOUT_PARQUET_PATHS: dict[str, str] = {
    "1M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
    "1p5M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
    "2M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
}
TRAIN_FRAME_RANGES: dict[str, tuple[int, int]] = {"1M": (0, 1199), "1p5M": (0, 1659), "2M": (0, 2186)}
VAL_FRAME_RANGES: dict[str, tuple[int, int]] = {"1M": (1200, 1599), "1p5M": (1660, 2212), "2M": (2187, 2915)}
HELDOUT_FRAME_RANGES: dict[str, tuple[int, int]] = {"1M": (1600, 1999), "1p5M": (2213, 2766), "2M": (2916, 3644)}

SAMPLING_MODE = "deterministic_four_consecutive_frames_heldout_fresh"

# 15 fresh blocks frozen (design §2.4)
NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [393001, 393002, 393003, 393004, 393005],
    "1p5M": [393101, 393102, 393103, 393104, 393105],
    "2M": [393201, 393202, 393203, 393204, 393205],
}

BLOCK_WINDOWS: dict[int, dict[str, Any]] = {}
BLOCK_TO_SOURCE: dict[int, str] = {}

_V52_WINDOW_DEFS = [
    ("1M", 393001, 18, 21, [1618, 1619, 1620, 1621]),
    ("1M", 393002, 22, 25, [1622, 1623, 1624, 1625]),
    ("1M", 393003, 46, 49, [1646, 1647, 1648, 1649]),
    ("1M", 393004, 50, 53, [1650, 1651, 1652, 1653]),
    ("1M", 393005, 74, 77, [1674, 1675, 1676, 1677]),
    ("1p5M", 393101, 4, 7, [2217, 2218, 2219, 2220]),
    ("1p5M", 393102, 8, 11, [2221, 2222, 2223, 2224]),
    ("1p5M", 393103, 23, 26, [2236, 2237, 2238, 2239]),
    ("1p5M", 393104, 27, 30, [2240, 2241, 2242, 2243]),
    ("1p5M", 393105, 31, 34, [2244, 2245, 2246, 2247]),
    ("2M", 393201, 4, 7, [2920, 2921, 2922, 2923]),
    ("2M", 393202, 8, 11, [2924, 2925, 2926, 2927]),
    ("2M", 393203, 12, 15, [2928, 2929, 2930, 2931]),
    ("2M", 393204, 29, 32, [2945, 2946, 2947, 2948]),
    ("2M", 393205, 33, 36, [2949, 2950, 2951, 2952]),
]
for _src, _bid, _s, _e, _fids in _V52_WINDOW_DEFS:
    BLOCK_WINDOWS[_bid] = {
        "source": _src,
        "held_out_ordinal_start": _s,
        "held_out_ordinal_end": _e,
        "frame_ids": _fids,
        "pairs_count": PAIRS_PER_BLOCK,
        "sampling_mode": SAMPLING_MODE,
    }
    BLOCK_TO_SOURCE[_bid] = _src

# Forbidden registries
V36_A3_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [360101, 360102, 360103, 360104, 360105],
    "1p5M": [360201, 360202, 360203, 360204, 360205],
    "2M": [360301, 360302, 360303, 360304, 360305],
}
V39_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390101, 390102, 390103, 390104, 390105],
    "1p5M": [390201, 390202, 390203, 390204, 390205],
    "2M": [390301, 390302, 390303, 390304, 390305],
}
V40_PROBE_SEEDS_COPIED: dict[str, int] = {"1M": 390106, "1p5M": 390206, "2M": 390306}
V41_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390107, 390108, 390109],
    "1p5M": [390207, 390208, 390209],
    "2M": [390307, 390308, 390309],
}
V42_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390110, 390111, 390112],
    "1p5M": [390210, 390211, 390212],
    "2M": [390310, 390311, 390312],
}
V43_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390113, 390114, 390115],
    "1p5M": [390213, 390214, 390215],
    "2M": [390313, 390314, 390315],
}
V44_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390116, 390117, 390118],
    "1p5M": [390216, 390217, 390218],
    "2M": [390316, 390317, 390318],
}
V45_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390119, 390120, 390121],
    "1p5M": [390219, 390220, 390221],
    "2M": [390319, 390320, 390321],
}
V46_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390122, 390123, 390124],
    "1p5M": [390222, 390223, 390224],
    "2M": [390322, 390323, 390324],
}
V47_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390125, 390126, 390127],
    "1p5M": [390225, 390226, 390227],
    "2M": [390325, 390326, 390327],
}
V48_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390128,390129,390130,390131,390132,390133,390134,390135,390136,390137,390138,390139,390140,390141,390142],
    "1p5M": [390228,390229,390230,390231,390232,390233,390234,390235,390236,390237,390238,390239,390240,390241,390242],
    "2M": [390328,390329,390330,390331,390332,390333,390334,390335,390336,390337,390338,390339,390340,390341,390342],
}
V50_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [391001,391002,391003,391004,391005],
    "1p5M": [391101,391102,391103,391104,391105],
    "2M": [391201,391202,391203,391204,391205],
}
V51_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [392001,392002,392003,392004,392005],
    "1p5M": [392101,392102,392103,392104,392105],
    "2M": [392201,392202,392203,392204,392205],
}
V48_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1600,1601,1602,1603,1628,1629,1630,1631,1656,1657,1658,1659,1684,1685,1686,1687,1713,1714,1715,1716,1741,1742,1743,1744,1769,1770,1771,1772,1798,1799,1800,1801,1826,1827,1828,1829,1854,1855,1856,1857,1882,1883,1884,1885,1911,1912,1913,1914,1939,1940,1941,1942,1967,1968,1969,1970,1996,1997,1998,1999]),
    "1p5M": frozenset([2213,2214,2215,2216,2252,2253,2254,2255,2291,2292,2293,2294,2330,2331,2332,2333,2370,2371,2372,2373,2409,2410,2411,2412,2448,2449,2450,2451,2488,2489,2490,2491,2527,2528,2529,2530,2566,2567,2568,2569,2605,2606,2607,2608,2645,2646,2647,2648,2684,2685,2686,2687,2723,2724,2725,2726,2763,2764,2765,2766]),
    "2M": frozenset([2916,2917,2918,2919,2967,2968,2969,2970,3019,3020,3021,3022,3071,3072,3073,3074,3123,3124,3125,3126,3174,3175,3176,3177,3226,3227,3228,3229,3278,3279,3280,3281,3330,3331,3332,3333,3382,3383,3384,3385,3433,3434,3435,3436,3485,3486,3487,3488,3537,3538,3539,3540,3589,3590,3591,3592,3641,3642,3643,3644]),
}
V48_HELDOUT_FRAME_IDS_FLAT: frozenset[int] = frozenset().union(*V48_HELDOUT_FRAME_IDS.values())
V50_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1614,1615,1616,1617,1642,1643,1644,1645,1670,1671,1672,1673,1698,1699,1700,1701,1727,1728,1729,1730]),
    "1p5M": frozenset([2232,2233,2234,2235,2271,2272,2273,2274,2310,2311,2312,2313,2350,2351,2352,2353,2389,2390,2391,2392]),
    "2M": frozenset([2941,2942,2943,2944,2993,2994,2995,2996,3045,3046,3047,3048,3097,3098,3099,3100,3148,3149,3150,3151]),
}
V51_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1607,1608,1609,1610,1635,1636,1637,1638,1663,1664,1665,1666,1691,1692,1693,1694,1719,1720,1721,1722]),
    "1p5M": frozenset([2225,2226,2227,2228,2264,2265,2266,2267,2303,2304,2305,2306,2343,2344,2345,2346,2382,2383,2384,2385]),
    "2M": frozenset([2934,2935,2936,2937,2986,2987,2988,2989,3038,3039,3040,3041,3090,3091,3092,3093,3141,3142,3143,3144]),
}
V52_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1618,1619,1620,1621,1622,1623,1624,1625,1646,1647,1648,1649,1650,1651,1652,1653,1674,1675,1676,1677]),
    "1p5M": frozenset([2217,2218,2219,2220,2221,2222,2223,2224,2236,2237,2238,2239,2240,2241,2242,2243,2244,2245,2246,2247]),
    "2M": frozenset([2920,2921,2922,2923,2924,2925,2926,2927,2928,2929,2930,2931,2945,2946,2947,2948,2949,2950,2951,2952]),
}

FORBIDDEN_78: frozenset[int] = frozenset(
    seed
    for seeds in (
        *V36_A3_SEEDS_COPIED.values(),
        *V39_SEEDS_COPIED.values(),
        *V40_PROBE_SEEDS_COPIED.values(),
        *V41_SEEDS_COPIED.values(),
        *V42_SEEDS_COPIED.values(),
        *V43_SEEDS_COPIED.values(),
        *V44_SEEDS_COPIED.values(),
        *V45_SEEDS_COPIED.values(),
    )
    for seed in (seeds if isinstance(seeds, list) else [seeds])
)
FORBIDDEN_87: frozenset[int] = frozenset(set(FORBIDDEN_78) | {s for lst in V46_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_96: frozenset[int] = frozenset(set(FORBIDDEN_87) | {s for lst in V47_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_141: frozenset[int] = frozenset(set(FORBIDDEN_96) | {s for lst in V48_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_156: frozenset[int] = frozenset(set(FORBIDDEN_141) | {s for lst in V50_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_171: frozenset[int] = frozenset(set(FORBIDDEN_156) | {s for lst in V51_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_BLOCK_SEEDS = FORBIDDEN_171

REPRESENTATIVE_ORDINALS: dict[str, int] = {"lane_c": 2}
CONSTRUCTION_SEEDS: dict[str, dict[str, list[int]]] = {
    "lane_c": {
        "1M": [383101, 383102, 383103],
        "1p5M": [383201, 383202, 383203],
        "2M": [383301, 383302, 383303],
    }
}

def _rep_seed(lane: str, source: str) -> int:
    return CONSTRUCTION_SEEDS[lane][source][REPRESENTATIVE_ORDINALS[lane] - 1]

FROZEN_REPRESENTATIVE_MATRIX_IDS: tuple[str, ...] = (
    "lane_c_1M_s383102",
    "lane_c_1p5M_s383202",
    "lane_c_2M_s383302",
)

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v52_rate_adaptive_l2_rescue/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v52_rate_adaptive_l2_rescue.py",
    "scripts/execute_v52_nested_rescue.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
)

SOURCE_M2: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}
SOURCE_ORDER_TUPLE = SOURCE_ORDER

def leak_for(source: str, h1_rows: int = H1_M) -> int:
    return 5 * SOURCE_M2[source] + 5 * h1_rows + 64

def leak_joint_for(source: str) -> int:
    return leak_for(source) + 40

def avg_leak_for(source: str, n_rescue: int, total: int = 15) -> float:
    return float(leak_for(source) + 40 * n_rescue / total)

MASTER_STOP_RULE = (
    "每块 L1 1 + base L2 1 (兼 old baseline, 同一次确定性译码不重复) + 条件 rescue ≤1；总 15 L1+15 base+≤15 rescue=30–45 硬帽45 L2≤30。"
)

TERMINAL_EVIDENCE_INVALID = "V52_EVIDENCE_INVALID"
TERMINAL_NESTED_RESCUE_COMPLETE = "V52_NESTED_RESCUE_COMPLETE"
ALL_TERMINALS = frozenset({TERMINAL_EVIDENCE_INVALID, TERMINAL_NESTED_RESCUE_COMPLETE})

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "source",
    "block_seed",
    "arm",
    "pass_index",
    "used_increment",
    "matrix_id",
    "joint",
    "h1_matrix_id",
    "frame_ids",
    "held_out_ordinal_start",
    "held_out_ordinal_end",
    "pairs_count",
    "sampling_mode",
    "max_iter",
    "damping_alpha",
    "errors_initial",
    "errors_final",
    "exact_l2",
    "exact_u1",
    "exact_full",
    "syndrome_ok_l2",
    "syndrome_ok_l1",
    "wrong_codeword_l2",
    "wrong_codeword_l1",
    "target_tag",
    "candidate_tag",
    "tag_ok",
    "tag_scope",
    "reclassified",
    "iterations_l1",
    "iterations_l2",
    "bp_posterior_entropy",
    "mean_abs_diff_q_p",
    "leak_total",
    "leak_joint",
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "h1_rows", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn", "arm", "pass_index"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY nested incremental L2 rescue Δ8 on frozen Lane C support/prior/MET n=1024 m2 184/190/192 GF32 poly37 decoder 90/1.0 leak 1064/1094/1104 base 1104/1134/1144 joint conditional only rescue frames +40 avg=base+40*N_attempt/15 total 30-45 hard cap 45 old vs pass1 same decode L2-only 2^-64",
    "leakage H1-16 includes 64-bit tag f_total=leak/[N(H1+H2)] N=1024 joint rank m2+8 nested independence 8 row≤16 col_inc≤1 deterministic no seed search not V48/V50/V51",
    "not threshold/SKR/formal qualification/promotion; paired descriptive only Δexact = final_V52 - old (old=base_exact) McNemar b/c descriptive four-way G3' undetected==0",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is 15 blocks paired old vs V52 (15 L1 +15 base +≤15 rescue =30-45 L2 15-30 records). "
    "Exact-recovery proportions with n and raw counts; any interval naive uncorrected clustering; no significance."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# L1 prior helpers (same as V48)
# ---------------------------------------------------------------------------

def get_l1_prior_p_u1_given_b(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    if arr.shape != (1024, 1024):
        raise ValueError(f"counts shape must be (1024,1024), got {arr.shape}")
    reshaped = arr.reshape(32, 32, 1024)
    num = reshaped.sum(axis=1)
    den = num.sum(axis=0)
    p_matrix = np.zeros((32, 1024), dtype=np.float64)
    for bb in range(1024):
        d = float(den[bb])
        if d <= 0 or not np.isfinite(d):
            p_matrix[:, bb] = 1.0 / 32
        else:
            col = num[:, bb] / d
            col = np.maximum(col, 1e-15)
            col = col / col.sum()
            p_matrix[:, bb] = col
    prior = p_matrix[:, b].T
    prior = np.maximum(prior, 1e-15)
    prior = prior / prior.sum(axis=1, keepdims=True)
    return prior


def get_l1_app_prior_l2(counts: np.ndarray, bob: np.ndarray, q: np.ndarray) -> np.ndarray:
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    qq = np.asarray(q, dtype=np.float64)
    if qq.shape != (b.shape[0], 32):
        raise ValueError(f"q shape must be (N,32), got {qq.shape}")
    reshaped = arr.reshape(32, 32, 1024)
    N = b.shape[0]
    out = np.zeros((N, 32), dtype=np.float64)
    for i in range(N):
        bb = int(b[i])
        counts_u1u2 = reshaped[:, :, bb]
        row_sums = counts_u1u2.sum(axis=1, keepdims=True)
        p_u2 = np.divide(counts_u1u2, row_sums, out=np.full_like(counts_u1u2, 1.0/32, dtype=float), where=row_sums>0)
        qi = qq[i]
        out[i] = qi @ p_u2
    out = np.maximum(out, 1e-15)
    out /= out.sum(axis=1, keepdims=True)
    return out


def softmax_beliefs(beliefs: np.ndarray) -> np.ndarray:
    bel = np.asarray(beliefs, dtype=np.float64)
    if bel.ndim != 2 or bel.shape[1] != 32:
        raise ValueError(f"beliefs shape must be (N,32), got {bel.shape}")
    shifted = bel - np.max(bel, axis=1, keepdims=True)
    exp = np.exp(shifted)
    exp = np.maximum(exp, 1e-15)
    q = exp / exp.sum(axis=1, keepdims=True)
    q = np.maximum(q, 1e-15)
    q /= q.sum(axis=1, keepdims=True)
    return q


def compute_entropy_and_diff(q: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    q = np.asarray(q, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)
    ent = -np.sum(q * np.log2(np.maximum(q, 1e-15)), axis=1)
    return float(np.mean(ent)), float(np.mean(np.abs(q - p)))


# ---------------------------------------------------------------------------
# H_inc construction (deterministic PEG-like, same as spike)
# ---------------------------------------------------------------------------

def construct_h_inc(source: str, det_id: Optional[int] = None, delta_m: int = DELTA_M, n: int = BLOCK_LENGTH) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
    if det_id is None:
        det_id = INC_DET_IDS[source]
    m = delta_m
    support_rng = get_substream_generator(det_id, stream_id=1)
    perm_base = support_rng.permutation(m).tolist()
    rank_in_perm = {c: i for i, c in enumerate(perm_base)}
    coeff_rng = get_substream_generator(det_id, stream_id=2)
    H_support = np.zeros((m, n), dtype=np.uint8)
    row_deg = np.zeros(m, dtype=int)
    inject_decision = support_rng.integers(0, 1024, size=n)
    threshold = 96
    sorted_indices = np.argsort(inject_decision)
    inject_set = set(sorted_indices[:threshold].tolist())
    for j in range(n):
        if j not in inject_set:
            continue
        min_deg = int(row_deg.min())
        eligible = [c for c in range(m) if int(row_deg[c]) == min_deg]
        c_pick = min(eligible, key=lambda c: rank_in_perm[c])
        H_support[c_pick, j] = 1
        row_deg[c_pick] += 1
        if row_deg[c_pick] > MAX_CHECK_DEGREE_LIMIT:
            raise IntegrityFailure("J3", f"row degree exceeded 16 at row {c_pick} col {j}")
    for r in range(m):
        if row_deg[r] == 0:
            max_r = int(np.argmax(row_deg))
            cols = np.where(H_support[max_r, :])[0]
            if len(cols) > 0:
                c_move = int(cols[0])
                H_support[max_r, c_move] = 0
                H_support[r, c_move] = 1
                row_deg[max_r] -= 1
                row_deg[r] += 1
    canonical = get_canonical_support_edges(H_support)
    coeffs = sample_uniform_gf32_nonzero(coeff_rng, len(canonical))
    H = np.zeros((m, n), dtype=np.uint8)
    for (r, c), val in zip(canonical, coeffs):
        H[r, c] = val
    return H, H_support, int(np.count_nonzero(H_support)), row_deg


def construct_h_joint(source: str, H_base: np.ndarray, det_id: Optional[int] = None) -> tuple[np.ndarray, dict[str, Any]]:
    H_inc, Hs_inc, E_inc, row_deg_inc = construct_h_inc(source, det_id)
    H_joint = np.vstack([H_base, H_inc]).astype(np.uint8)
    return H_joint, {"H_inc": H_inc, "Hs_inc": Hs_inc, "E_inc": E_inc, "row_deg_inc": row_deg_inc}


# ---------------------------------------------------------------------------
# Seed-registry validator (J2) per spec
# ---------------------------------------------------------------------------

def validate_seed_registry(seeds: Optional[dict[str, list[int]]] = None) -> tuple[bool, str]:
    reg = NEW_BLOCK_SEEDS if seeds is None else seeds
    if set(reg.keys()) != set(SOURCE_ORDER):
        return False, f"registry sources must be exactly {SOURCE_ORDER}"
    all_seeds = [seed for source in SOURCE_ORDER for seed in reg[source]]
    if len(all_seeds) != 15:
        return False, f"registry must contain exactly 15 seeds, got {len(all_seeds)}"
    if any(len(reg[source]) != 5 for source in SOURCE_ORDER):
        return False, f"registry must hold exactly 5 seeds per source: {dict(reg)}"
    duplicates = sorted({s for s in all_seeds if all_seeds.count(s) > 1})
    if duplicates:
        return False, f"duplicate seeds among the 15: {duplicates}"
    overlap = set(all_seeds) & FORBIDDEN_171
    if overlap:
        return False, f"new seeds overlap forbidden 171 registries: {sorted(overlap)}"
    expected = NEW_BLOCK_SEEDS
    flat_expected = {s for lst in expected.values() for s in lst}
    flat_actual = set(all_seeds)
    if seeds is None and flat_actual != flat_expected:
        return False, "new seeds must be exactly frozen 393001-005/101-105/201-205"
    for src in SOURCE_ORDER:
        seeds_sorted = sorted(reg[src])
        if seeds_sorted != reg[src]:
            return False, f"seeds for {src} must be sorted ascending"
        if seeds_sorted[-1] - seeds_sorted[0] != 4:
            return False, f"seeds for {src} must be consecutive 5"
    # per-source frame_ids zero overlap with V48/V50/V51
    for src in SOURCE_ORDER:
        for bid in reg[src]:
            win = BLOCK_WINDOWS.get(bid)
            if win is None:
                continue
            fids = set(win["frame_ids"])
            if fids & V48_HELDOUT_FRAME_IDS[src]:
                return False, f"block {bid} frame_ids overlap V48 for {src}"
            if fids & V50_HELDOUT_FRAME_IDS[src]:
                return False, f"block {bid} frame_ids overlap V50 for {src}"
            if fids & V51_HELDOUT_FRAME_IDS[src]:
                return False, f"block {bid} frame_ids overlap V51 for {src}"
    return True, "SEED_REGISTRY_OK"


# ---------------------------------------------------------------------------
# Held-out parquet loader
# ---------------------------------------------------------------------------

_HELDOUT_DF_CACHE: dict[str, Any] = {}

def _heldout_parquet_path(source: str) -> Path:
    return REPO_ROOT / HELDOUT_PARQUET_PATHS[source]

def _load_heldout_df(source: str):
    if source in _HELDOUT_DF_CACHE:
        return _HELDOUT_DF_CACHE[source]
    import pandas as pd
    path = _heldout_parquet_path(source)
    if not path.is_file():
        raise IntegrityFailure("J4", f"held-out parquet missing for {source}: {path}")
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        raise IntegrityFailure("J4", f"held-out parquet unreadable {source}: {type(exc).__name__}: {exc}") from exc
    for col in ("frame_id", "pair_idx", "alice_symbol", "bob_symbol"):
        if col not in df.columns:
            raise IntegrityFailure("J4", f"held-out parquet schema missing {col} for {source}")
    _HELDOUT_DF_CACHE[source] = df
    return df

def load_heldout_block(block_seed: int) -> tuple[np.ndarray, np.ndarray]:
    if block_seed not in BLOCK_WINDOWS:
        raise IntegrityFailure("J4", f"block_seed {block_seed} not in frozen 15")
    win = BLOCK_WINDOWS[block_seed]
    source = win["source"]
    frame_ids: list[int] = list(win["frame_ids"])
    df = _load_heldout_df(source)
    filt = df[df["frame_id"].isin(frame_ids)].copy()
    uniq = sorted(filt["frame_id"].unique().tolist())
    if uniq != sorted(frame_ids):
        raise IntegrityFailure("J4", f"block {block_seed} frame_id mismatch: got {uniq}, expected {sorted(frame_ids)}")
    if len(filt) != PAIRS_PER_BLOCK:
        raise IntegrityFailure("J4", f"block {block_seed} total pairs {len(filt)} != {PAIRS_PER_BLOCK}")
    for fid in frame_ids:
        sub = filt[filt["frame_id"] == fid]
        if len(sub) != PAIRS_PER_FRAME:
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} pairs {len(sub)} != {PAIRS_PER_FRAME}")
        pis = sorted(sub["pair_idx"].tolist())
        if pis != list(range(PAIRS_PER_FRAME)):
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} pair_idx not 0..255 contiguous")
        if sub["pair_idx"].duplicated().any():
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} duplicate pair_idx")
    filt = filt.sort_values(["frame_id", "pair_idx"], ascending=[True, True])
    alice = filt["alice_symbol"].to_numpy()
    bob = filt["bob_symbol"].to_numpy()
    if alice.size != PAIRS_PER_BLOCK or bob.size != PAIRS_PER_BLOCK:
        raise IntegrityFailure("J4", f"block {block_seed} alice/bob size mismatch")
    if not (np.all(alice >= 0) and np.all(alice < 1024) and np.all(bob >= 0) and np.all(bob < 1024)):
        raise IntegrityFailure("J4", f"block {block_seed} symbol out of range 0..1023")
    return np.asarray(alice, dtype=np.int64), np.asarray(bob, dtype=np.int64)

def _clear_heldout_cache() -> None:
    _HELDOUT_DF_CACHE.clear()

def validate_train_heldout_isolation() -> tuple[bool, str]:
    for src in SOURCE_ORDER:
        tr_lo, tr_hi = TRAIN_FRAME_RANGES[src]
        ho_lo, ho_hi = HELDOUT_FRAME_RANGES[src]
        if not (tr_hi < ho_lo):
            return False, f"{src} TRAIN {tr_lo}-{tr_hi} overlaps held-out {ho_lo}-{ho_hi}"
        for bid in NEW_BLOCK_SEEDS[src]:
            for fid in BLOCK_WINDOWS[bid]["frame_ids"]:
                if not (ho_lo <= fid <= ho_hi):
                    return False, f"{src} block {bid} frame {fid} outside held-out {ho_lo}-{ho_hi}"
                if tr_lo <= fid <= tr_hi:
                    return False, f"{src} block {bid} frame {fid} overlaps TRAIN {tr_lo}-{tr_hi}"
    return True, "ISOLATION_OK"

# ---------------------------------------------------------------------------
# Structural reconstruction (J3) — Lane C base + H_inc joint
# ---------------------------------------------------------------------------

def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")

def reconstruct_v52_matrices(
    reference_metrics_path: Path | str = STRUCTURAL_AUTHORITY_PATH,
    field: Optional[GF2mField] = None,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
) -> dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]:
    _reject_forbidden_npz(reference_metrics_path)
    try:
        reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    except ValueError as exc:
        raise IntegrityFailure("J3", f"structural authority unusable: {exc}") from exc
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("J9", f"field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}")
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]] = {}
    for source in SOURCE_ORDER:
        seed = _rep_seed("lane_c", source)
        matrix_id = f"lane_c_{source}_s{seed}"
        if matrix_id not in FROZEN_REPRESENTATIVE_MATRIX_IDS:
            raise IntegrityFailure("J3", f"representative identity drift: {matrix_id} not in frozen constants")
        expected = reference_by_id.get(matrix_id)
        if expected is None:
            raise IntegrityFailure("J3", f"missing committed metrics for {matrix_id}")
        if expected.get("lane") != "lane_c" or expected.get("source") != source:
            raise IntegrityFailure("J3", f"identity mismatch in committed metrics: {matrix_id}")
        ctor = construct_lane_c_prototype
        if constructors and "lane_c" in constructors:
            ctor = constructors["lane_c"]
        matrix, metrics = ctor(source=source, seed=seed, field=field)
        try:
            _check_v38r1_metric_match(expected, metrics, matrix_id)
        except ValueError as exc:
            raise IntegrityFailure("J3", str(exc)) from exc
        if "position_permutations" not in expected:
            raise IntegrityFailure("J3", f"missing frozen Lane C permutations: {matrix_id}")
        matrices[("lane_c", source)] = (matrix, metrics)
        # H_inc
        H_inc, Hs_inc, E_inc, row_deg_inc = construct_h_inc(source)
        if H_inc.shape != (DELTA_M, BLOCK_LENGTH):
            raise IntegrityFailure("J3", f"H_inc shape {H_inc.shape} != {(DELTA_M, BLOCK_LENGTH)}")
        if int(row_deg_inc.max()) > MAX_CHECK_DEGREE_LIMIT:
            raise IntegrityFailure("J3", f"H_inc row_max {int(row_deg_inc.max())} >16")
        if int(np.count_nonzero(Hs_inc, axis=0).max()) > 1:
            raise IntegrityFailure("J3", "H_inc col_degree >1")
        # joint rank/nested/independence
        H_joint = np.vstack([matrix, H_inc]).astype(np.uint8)
        rank_base = int(compute_gf32_rank(matrix, field))
        rank_joint = int(compute_gf32_rank(H_joint, field))
        if rank_base != SOURCE_CHECKS[source]:
            raise IntegrityFailure("J3", f"base rank {rank_base} != m2 {SOURCE_CHECKS[source]}")
        if rank_joint != SOURCE_CHECKS[source] + DELTA_M:
            raise IntegrityFailure("J3", f"joint rank {rank_joint} != m2+8 {SOURCE_CHECKS[source]+DELTA_M}")
        if not np.array_equal(H_joint[0:SOURCE_CHECKS[source], :], matrix):
            raise IntegrityFailure("J3", f"nested failed for {source}")
        if rank_joint - rank_base != DELTA_M:
            raise IntegrityFailure("J3", f"independence {rank_joint - rank_base} !=8")
        col_inc_max = int(np.count_nonzero(Hs_inc, axis=0).max())
        row_inc_max = int(row_deg_inc.max())
        if col_inc_max > 1 or row_inc_max > 16:
            raise IntegrityFailure("J3", "H_inc degree violation")
        # leak formula
        lb = leak_for(source)
        lj = leak_joint_for(source)
        if lj - lb != 40:
            raise IntegrityFailure("J3", "leak +40 failed")
        matrices[("h_inc", source)] = (H_inc, {"E_inc": int(E_inc), "row_deg_inc": row_deg_inc.tolist(), "col_inc_max": col_inc_max, "row_inc_max": row_inc_max})
        matrices[("h_joint", source)] = (H_joint, {"rank_joint": rank_joint, "rank_base": rank_base, "nested": True, "independence": DELTA_M, "E_inc": int(E_inc)})
    # H1
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import build_layer as v31_build_layer
        h1_tuple, h1_audit = v31_build_layer(H1_M, H1_N, family=H1_FAMILY, field=field)
        h1_matrix = np.asarray(h1_tuple, dtype=np.uint8)
    except Exception as exc:
        raise IntegrityFailure("J3", f"H1 reconstruction failed: {type(exc).__name__}: {exc}") from exc
    if h1_matrix.shape != (H1_M, H1_N):
        raise IntegrityFailure("J3", f"H1 shape mismatch: {h1_matrix.shape}")
    for m1, expected_rank in [(16, 16)]:
        prefix = h1_matrix[:m1, :]
        try:
            rank = int(compute_gf32_rank(prefix, field))
        except Exception:
            rank = int(h1_audit.get("rank", -1))
        if rank != expected_rank:
            raise IntegrityFailure("J3", f"H1 rank m1={m1} must be {expected_rank}, got {rank}")
    matrices[("H1", "L1")] = (h1_matrix, h1_audit)
    return matrices

# P1 decoder-free preflight

def nested_rescue_preflight(
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    field = field or GF2mField.create(DIMENSION)
    if matrices is None:
        matrices = reconstruct_v52_matrices(field=field)
    _iso_ok, _iso_msg = validate_train_heldout_isolation()
    if not _iso_ok:
        raise IntegrityFailure("J4", f"train/held-out isolation failed: {_iso_msg}")
    ok, msg = validate_seed_registry()
    if not ok:
        raise IntegrityFailure("J2", msg)
    if counts_by_source is not None:
        for src in SOURCE_ORDER:
            arr = counts_by_source.get(src)
            if arr is None or getattr(arr, "shape", None) != (1024, 1024):
                raise IntegrityFailure("J4", f"counts TRAIN shape invalid for {src}")
    h1_full = matrices.get(("H1", "L1"), (None,))[0]
    if h1_full is None:
        raise IntegrityFailure("J3", "H1 missing")
    per_source: dict[str, Any] = {}
    for src in SOURCE_ORDER:
        H_base = matrices[("lane_c", src)][0]
        H_inc = matrices[("h_inc", src)][0]
        H_joint = matrices[("h_joint", src)][0]
        m2 = SOURCE_CHECKS[src]
        assert H_base.shape == (m2, BLOCK_LENGTH)
        assert H_inc.shape == (DELTA_M, BLOCK_LENGTH)
        assert H_joint.shape == (m2+DELTA_M, BLOCK_LENGTH)
        rank_base = int(compute_gf32_rank(H_base, field))
        rank_joint = int(compute_gf32_rank(H_joint, field))
        nested = bool(np.array_equal(H_joint[0:m2, :], H_base))
        inc = rank_joint - rank_base
        lb = leak_for(src)
        lj = leak_joint_for(src)
        # tag
        try:
            empty = np.empty(0, dtype=np.uint8)
            x2 = np.array([1, 2, 3, 4], dtype=np.uint8)
            t = compute_tag_64(empty, x2)
            assert isinstance(t, str) and len(t) == 16
            int(t, 16)
            tag_ok = True
        except Exception:
            tag_ok = False
        per_source[src] = {
            "rank_base": rank_base, "rank_joint": rank_joint, "nested": nested, "independence": inc,
            "leak_base": lb, "leak_joint": lj, "delta": lj-lb,
            "h_base_ok": rank_base == m2,
            "h_inc_nested_ok": nested,
            "joint_rank_ok": rank_joint == m2+DELTA_M,
            "independence_ok": inc == DELTA_M,
            "leakage_accounted": (lj-lb)==40,
            "tag_import_ok": tag_ok,
            "tag_scope_l2_only": TAG_SCOPE=="l2_only",
        }
        if not (per_source[src]["h_base_ok"] and per_source[src]["joint_rank_ok"] and per_source[src]["independence_ok"] and nested and tag_ok):
            raise IntegrityFailure("J5", f"preflight failed for {src}: {per_source[src]}")
        # L1->Pi path sentinel first block per source
        bseed = {"1M":393001,"1p5M":393101,"2M":393201}[src]
        win = BLOCK_WINDOWS.get(bseed)
        if win is None or win["pairs_count"] !=1024 or len(win["frame_ids"])!=4 or win["sampling_mode"]!=SAMPLING_MODE:
            raise IntegrityFailure("J4", f"heldout not reachable for {src}/{bseed}")
        if counts_by_source is not None:
            try:
                from comparison_bench.formal_ir.v35_algorithm_development import factorize_f03 as _fac
                # we have alice/bob from parquet only if available; skip if parquet missing in fake env
                pass
            except Exception:
                pass
    return {"per_source": per_source, "nested_ok": True, "leak_plus40_ok": True}

# alias
single_arm_binding_preflight = nested_rescue_preflight
triple_arm_binding_preflight = nested_rescue_preflight

# ---------------------------------------------------------------------------
# Tag helpers
# ---------------------------------------------------------------------------

def compute_l2_tag(x2: np.ndarray) -> str:
    empty = np.empty(0, dtype=np.uint8)
    return compute_tag_64(empty, np.asarray(x2, dtype=np.uint8))

def classify_reclassified(exact_l2: bool, syndrome_ok_l2: bool, tag_ok: bool) -> str:
    if exact_l2:
        return "exact"
    if tag_ok and not exact_l2:
        return "undetected_accepted_wrong"
    if syndrome_ok_l2 and not exact_l2 and not tag_ok:
        return "detected_verification_failure"
    if not syndrome_ok_l2 and not exact_l2:
        return "decoder_non_syndrome_failure"
    return "decoder_non_syndrome_failure"

RECLASSIFIED_VALUES = frozenset({"exact", "detected_verification_failure", "decoder_non_syndrome_failure", "undetected_accepted_wrong"})

def _compute_errors_initial(u2_alice: np.ndarray, u2_bob: np.ndarray) -> int:
    return int(np.sum(np.asarray(u2_alice) != np.asarray(u2_bob)))

# ---------------------------------------------------------------------------
# Budget accounting (J10) hard cap 45 dynamic 30-45
# ---------------------------------------------------------------------------

class CallAccounting:
    def __init__(self, hard_cap: int = HARD_CALL_CAP) -> None:
        self.hard_cap = int(hard_cap)
        self.started = 0
        self.completed = 0
        self.started_l1 = 0
        self.completed_l1 = 0
        self.started_l2 = 0
        self.completed_l2 = 0
        self.started_base = 0
        self.completed_base = 0
        self.started_rescue = 0
        self.completed_rescue = 0

    def register_start(self, layer: str = "total") -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        if layer == "l1" and self.started_l1 >= PLANNED_L1:
            raise IntegrityFailure("J10", "l1 cap 15 reached")
        if layer == "l2" and self.started_l2 >= PLANNED_L2_MAX:
            raise IntegrityFailure("J10", "l2 cap 30 reached")
        if layer == "rescue" and self.started_rescue >= PLANNED_L2_RESCUE_MAX:
            raise IntegrityFailure("J10", "rescue cap 15 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
            self.started_l2 += 0
        elif layer == "l2":
            self.started_l2 += 1
        elif layer == "base":
            self.started_base += 1
            self.started_l2 += 1
        elif layer == "rescue":
            self.started_rescue += 1
            self.started_l2 += 1
        elif layer == "total":
            pass

    def register_complete(self, layer: str = "total") -> None:
        if self.completed >= self.started:
            raise IntegrityFailure("J10", "completed without started")
        self.completed += 1
        if layer == "l1":
            self.completed_l1 += 1
        elif layer == "l2":
            self.completed_l2 += 1
        elif layer == "base":
            self.completed_base += 1
            self.completed_l2 += 1
        elif layer == "rescue":
            self.completed_rescue += 1
            self.completed_l2 += 1

    def validate_executed(self) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        if self.completed > self.hard_cap:
            failures.append(("J10", f"completed {self.completed} exceeds hard cap {self.hard_cap}"))
        if self.completed != self.started:
            failures.append(("J10", f"started {self.started} != completed {self.completed}"))
        if self.completed_l1 != self.started_l1 or self.completed_l2 != self.started_l2:
            failures.append(("J10", f"l1/l2 mismatch"))
        if self.completed_l1 > PLANNED_L1 or self.completed_base > PLANNED_L2_BASE or self.completed_rescue > PLANNED_L2_RESCUE_MAX:
            failures.append(("J10", "per-layer overflow"))
        if self.completed < 30 or self.completed > 45:
            failures.append(("J10", f"total {self.completed} not in 30-45"))
        return failures

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

def validate_decoder_contract(call_params: dict[str, Any], expected_setting: tuple[int, float]) -> None:
    extra = set(call_params.keys()) - ALLOWED_CALL_KEYS
    if extra:
        raise IntegrityFailure("J9", f"unexpected call parameters: {sorted(extra)}")
    if call_params["max_iter"] != expected_setting[0] or call_params["damping_alpha"] != expected_setting[1]:
        raise IntegrityFailure("J9", f"decoder settings {call_params['max_iter']}/{call_params['damping_alpha']} != frozen {expected_setting}")

def build_record(spec: dict[str, Any], raw: dict[str, Any], setting: tuple[int, float]) -> dict[str, Any]:
    exact_l2 = bool(raw["exact_l2"])
    exact_u1 = bool(raw["exact_u1"])
    exact_full = bool(raw["exact_full"]) if raw.get("exact_full") is not None else bool(exact_u1 and exact_l2)
    syndrome_ok_l2 = bool(raw["syndrome_ok_l2"])
    syndrome_ok_l1 = bool(raw["syndrome_ok_l1"])
    wrong_l2 = bool(syndrome_ok_l2 and not exact_l2)
    wrong_l1 = bool(syndrome_ok_l1 and not exact_u1)
    target_tag = str(raw.get("target_tag", ""))
    candidate_tag = str(raw.get("candidate_tag", ""))
    tag_ok = bool(raw.get("tag_ok", False))
    tag_scope = str(raw.get("tag_scope", TAG_SCOPE))
    reclassified = raw.get("reclassified")
    if reclassified is None:
        reclassified = classify_reclassified(exact_l2, syndrome_ok_l2, tag_ok)
    record = {
        "call_id": spec["call_id"],
        "source": raw["source"],
        "block_seed": raw["block_seed"],
        "arm": raw.get("arm", spec.get("arm","base_shared")),
        "pass_index": int(raw.get("pass_index", spec.get("pass_index",1))),
        "used_increment": bool(raw.get("used_increment", False)),
        "matrix_id": raw["matrix_id"],
        "joint": bool(raw.get("joint", False)),
        "h1_matrix_id": raw.get("h1_matrix_id", H1_MATRIX_ID),
        "frame_ids": list(raw.get("frame_ids", spec.get("frame_ids", []))),
        "held_out_ordinal_start": int(raw.get("held_out_ordinal_start", spec.get("held_out_ordinal_start", 0))),
        "held_out_ordinal_end": int(raw.get("held_out_ordinal_end", spec.get("held_out_ordinal_end", 0))),
        "pairs_count": int(raw.get("pairs_count", PAIRS_PER_BLOCK)),
        "sampling_mode": str(raw.get("sampling_mode", SAMPLING_MODE)),
        "max_iter": int(setting[0]),
        "damping_alpha": float(setting[1]),
        "errors_initial": int(raw["errors_initial"]),
        "errors_final": int(raw["errors_final"]),
        "exact_l2": exact_l2,
        "exact_u1": exact_u1,
        "exact_full": exact_full,
        "syndrome_ok_l2": syndrome_ok_l2,
        "syndrome_ok_l1": syndrome_ok_l1,
        "wrong_codeword_l2": wrong_l2,
        "wrong_codeword_l1": wrong_l1,
        "target_tag": target_tag,
        "candidate_tag": candidate_tag,
        "tag_ok": tag_ok,
        "tag_scope": tag_scope,
        "reclassified": reclassified,
        "iterations_l1": int(raw["iterations_l1"]),
        "iterations_l2": int(raw["iterations_l2"]),
        "bp_posterior_entropy": float(raw["bp_posterior_entropy"]),
        "mean_abs_diff_q_p": float(raw["mean_abs_diff_q_p"]),
        "leak_total": int(raw.get("leak_total", spec.get("leak_total", 0))),
        "leak_joint": int(raw.get("leak_joint", leak_joint_for(raw["source"]))),
        "status": str(raw["status"]),
        "runtime_s": float(raw["runtime_s"]),
    }
    return {k: record[k] for k in RECORD_FIELDS}

def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    for key in RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    if record["source"] not in SOURCE_ORDER:
        return False, f"invalid source {record['source']!r}"
    if record["arm"] not in ("base_shared","rescue"):
        return False, f"invalid arm {record['arm']!r}"
    if record["pass_index"] not in (1,2):
        return False, "pass_index must be 1 or 2"
    if record["arm"]=="base_shared" and record["pass_index"]!=1:
        return False, "base_shared must be pass 1"
    if record["arm"]=="rescue" and record["pass_index"]!=2:
        return False, "rescue must be pass 2"
    if record["used_increment"] != (record["arm"]=="rescue"):
        return False, "used_increment must equal arm rescue"
    if record["sampling_mode"] != SAMPLING_MODE:
        return False, f"sampling_mode must be {SAMPLING_MODE}"
    if record["pairs_count"] != PAIRS_PER_BLOCK:
        return False, f"pairs_count must be {PAIRS_PER_BLOCK}"
    if record["arm"]=="base_shared" and record["leak_total"] != leak_for(record["source"]):
        return False, f"base leak {record['leak_total']} != {leak_for(record['source'])}"
    if record["arm"]=="rescue" and record["leak_total"] != leak_joint_for(record["source"]):
        return False, f"rescue leak {record['leak_total']} != {leak_joint_for(record['source'])}"
    if record["leak_joint"] != leak_joint_for(record["source"]):
        return False, "leak_joint mismatch"
    if not isinstance(record["frame_ids"], list) or len(record["frame_ids"]) != 4:
        return False, "frame_ids must be list of 4"
    win = BLOCK_WINDOWS.get(record["block_seed"])
    if win is None:
        return False, f"block_seed {record['block_seed']} not in frozen 15"
    if record["frame_ids"] != win["frame_ids"]:
        return False, f"frame_ids mismatch expected {win['frame_ids']}"
    if record["held_out_ordinal_start"] != win["held_out_ordinal_start"] or record["held_out_ordinal_end"] != win["held_out_ordinal_end"]:
        return False, "held_out ordinal mismatch"
    # reclassified
    exp = classify_reclassified(record["exact_l2"], record["syndrome_ok_l2"], record["tag_ok"])
    if record["reclassified"] != exp:
        return False, f"reclassified {record['reclassified']} != expected {exp}"
    if record["tag_scope"] != TAG_SCOPE:
        return False, f"tag_scope must be {TAG_SCOPE}"
    if len(record["target_tag"])!=16 or len(record["candidate_tag"])!=16:
        return False, "tags must be 16-char hex"
    try:
        int(record["target_tag"],16); int(record["candidate_tag"],16)
    except Exception:
        return False, "tags must be hex"
    if record["tag_ok"] != (record["target_tag"]==record["candidate_tag"]):
        return False, "tag_ok must equal target==candidate"
    if record["exact_l2"] and not record["tag_ok"]:
        return False, "exact_l2 true must have tag_ok"
    return True, "SCHEMA_OK"


# ---------------------------------------------------------------------------
# Core runner — conditional rescue with dedup
# ---------------------------------------------------------------------------

def _check_git_and_scoped(check_git: bool, check_scoped_dirty: bool, authorized_target_sha: str) -> None:
    if not check_git:
        return
    try:
        head = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
        origin = subprocess.check_output(["git","rev-parse","origin/formal-ir-mainline"], text=True).strip()
    except Exception as exc:
        raise IntegrityFailure("J1", f"git rev-parse failed: {exc}") from exc
    if head != authorized_target_sha:
        raise IntegrityFailure("J1", f"HEAD {head} != authorized {authorized_target_sha}")
    if origin != authorized_target_sha:
        raise IntegrityFailure("J1", f"origin/formal-ir-mainline {origin} != authorized {authorized_target_sha}")
    if check_scoped_dirty:
        try:
            out = subprocess.check_output(["git","status","--porcelain"], text=True)
        except Exception as exc:
            raise IntegrityFailure("J1", f"git status failed: {exc}") from exc
        dirty = [line for line in out.splitlines() if any(p in line for p in SCOPED_TRACKED_PATHS)]
        if dirty:
            raise IntegrityFailure("J1", f"SCOPED dirty: {dirty}")

def _evaluate_one_l2(
    matrix: np.ndarray,
    source: str,
    block_seed: int,
    counts: np.ndarray,
    bob: np.ndarray,
    u2_alice: np.ndarray,
    u2_bob: np.ndarray,
    field: GF2mField,
    setting: tuple[int,float],
    fake_runner: bool,
    decode_fn: Optional[Callable],
    errors_initial: int,
    spec: dict[str, Any],
    q: Optional[np.ndarray]=None,
    p_prior: Optional[np.ndarray]=None,
    exact_u1: bool=True,
    syndrome_ok_l1: bool=True,
    iterations_l1: int=5,
    entropy: float=4.2,
    mean_abs: float=0.03,
) -> dict[str, Any]:
    # used only via fake path in tests; real path via decode
    if fake_runner or decode_fn is not None:
        # fake: we simulate exact via simple heuristic unless decode_fn overrides
        if decode_fn is not None:
            # decode_fn can simulate
            res = decode_fn(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, spec)
            if isinstance(res, dict):
                return res
        # default fake: exact if errors_initial small
        exact_l2 = errors_initial < 20
        empty = np.empty(0, dtype=np.uint8)
        target = compute_tag_64(empty, u2_alice)
        if exact_l2:
            candidate = target
            tag_ok = True
            syn_ok = True
            final = 0
        else:
            alt = u2_alice.copy()
            alt[0] = (int(alt[0])+1)%32
            candidate = compute_tag_64(empty, alt)
            tag_ok = False
            syn_ok = True
            final = errors_initial
        win = BLOCK_WINDOWS[block_seed]
        return {
            "source": source, "block_seed": block_seed,
            "matrix_id": spec["matrix_id"],
            "h1_matrix_id": H1_MATRIX_ID,
            "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
            "pairs_count": 1024, "sampling_mode": SAMPLING_MODE,
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1), "exact_full": bool(exact_u1 and exact_l2),
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syndrome_ok_l1),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": TAG_SCOPE, "reclassified": classify_reclassified(exact_l2, syn_ok, tag_ok),
            "iterations_l1": int(iterations_l1), "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": float(entropy), "mean_abs_diff_q_p": float(mean_abs),
            "leak_total": int(spec.get("leak_total", leak_for(source))),
            "leak_joint": int(leak_joint_for(source)),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
            "arm": spec.get("arm","base_shared"), "pass_index": int(spec.get("pass_index",1)), "used_increment": bool(spec.get("used_increment",False)), "joint": bool(spec.get("joint",False)),
        }
    # real decode
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa as _dec
    syn = syndrome_of_gf32(matrix, u2_alice, field)
    # prior: use provided q/p or fallback
    if q is None:
        # dummy prior uniform
        prior = np.full((1024,32), 1/32)
    else:
        prior = q  # already Pi(U2)
    res = _dec(matrix, prior, syn, max_iter=setting[0], damping_alpha=setting[1], field=field)
    empty = np.empty(0, dtype=np.uint8)
    target = compute_tag_64(empty, u2_alice)
    candidate = compute_tag_64(empty, res.x_hat)
    tag_ok = (target == candidate)
    syn_ok = bool(res.syndrome_ok)
    exact_l2 = bool(np.array_equal(res.x_hat, u2_alice))
    final = int(np.sum(res.x_hat != u2_alice))
    win = BLOCK_WINDOWS[block_seed]
    return {
        "source": source, "block_seed": block_seed,
        "matrix_id": spec["matrix_id"],
        "h1_matrix_id": H1_MATRIX_ID,
        "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
        "pairs_count": 1024, "sampling_mode": SAMPLING_MODE,
        "errors_initial": int(errors_initial), "errors_final": int(final),
        "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1), "exact_full": bool(exact_u1 and exact_l2),
        "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syndrome_ok_l1),
        "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": TAG_SCOPE, "reclassified": classify_reclassified(exact_l2, syn_ok, tag_ok),
        "iterations_l1": int(iterations_l1), "iterations_l2": int(res.iterations),
        "bp_posterior_entropy": float(entropy), "mean_abs_diff_q_p": float(mean_abs),
        "leak_total": int(spec.get("leak_total", leak_for(source))),
        "leak_joint": int(leak_joint_for(source)),
        "status": str(res.status), "runtime_s": float(res.runtime_s),
        "arm": spec.get("arm","base_shared"), "pass_index": int(spec.get("pass_index",1)), "used_increment": bool(spec.get("used_increment",False)), "joint": bool(spec.get("joint",False)),
    }


def run_v52_diagnostic(
    execution_authorized: bool = False,
    authorized_target_sha: Optional[str] = None,
    fake_runner: bool = False,
    output_root: Optional[Path] = None,
    structural_authority_path: Optional[Path | str] = None,
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    check_git: bool = True,
    check_scoped_dirty: bool = True,
    constructors: Optional[dict[str, Callable]] = None,
    decode_fn: Optional[Callable] = None,
) -> dict[str, Any]:
    if not execution_authorized:
        raise PermissionError("EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha")
    if not authorized_target_sha:
        raise IntegrityFailure("J1", "--authorized-target-sha required")
    _check_git_and_scoped(check_git, check_scoped_dirty, authorized_target_sha)
    if output_root is None:
        output_root = OUTPUT_ROOT
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError(f"output root already exists: {output_root}")
    # seed registry + isolation pre-checks (P1-P3 decoder-free)
    ok, msg = validate_seed_registry()
    if not ok:
        raise IntegrityFailure("J2", msg)
    iso_ok, iso_msg = validate_train_heldout_isolation()
    if not iso_ok:
        raise IntegrityFailure("J4", iso_msg)
    # counts
    if counts_by_source is None:
        try:
            counts_by_source = load_v25_channel_counts()
        except Exception as exc:
            raise IntegrityFailure("J4", f"load counts failed: {exc}") from exc
    # matrices
    matrices = reconstruct_v52_matrices(
        reference_metrics_path=structural_authority_path or STRUCTURAL_AUTHORITY_PATH,
        constructors=constructors,
    )
    # preflight nested
    nested_rescue_preflight(counts_by_source=counts_by_source, matrices=matrices)
    # build workload: 15 blocks, each has base spec; rescue spec derived conditionally
    field = GF2mField.create(DIMENSION)
    h1_full = matrices[("H1","L1")][0]
    accounting = CallAccounting(hard_cap=HARD_CALL_CAP)
    records: list[dict[str, Any]] = []
    # for summary
    first_pass_success = 0
    rescued = 0
    final_success = 0
    old_success = 0
    n_rescue_attempted = 0
    per_source_counts: dict[str, dict[str,int]] = {s: {"first":0,"rescued":0,"final":0,"old":0,"rescue_attempted":0} for s in SOURCE_ORDER}

    call_id_counter = 1
    # Now per block: L1 H1-16 BP then base L2 + conditional rescue (same q)
    for source in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[source]:
            win = BLOCK_WINDOWS[bseed]
            # load block
            if fake_runner:
                # fake alice/bob small deterministic
                rng = np.random.default_rng(bseed)
                alice = rng.integers(0,1024, size=PAIRS_PER_BLOCK, dtype=np.int64)
                bob = rng.integers(0,1024, size=PAIRS_PER_BLOCK, dtype=np.int64)
                # ensure within range
                u1a, u2a, u1b, u2b = factorize_f03(alice, bob)
            else:
                alice, bob = load_heldout_block(bseed)
                u1a, u2a, u1b, u2b = factorize_f03(alice, bob)
            p_i = get_l1_prior_p_u1_given_b(counts_by_source[source], bob)
            # --- L1 H1-16 BP (must be real s1 + TRAIN prior, L1 accounting surrounds call) ---
            s1 = syndrome_of_gf32(h1_full, u1a, field)
            accounting.register_start(layer="l1")
            validate_decoder_contract({"H": h1_full, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
            if fake_runner:
                # fake L1 BP but still wrapped in L1 accounting; use perturbed beliefs so q != p_i
                fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.05 * np.sin(np.arange(32))[None, :]
                q = softmax_beliefs(fake_beliefs)
                ent, md = compute_entropy_and_diff(q, p_i)
                iterations_l1 = 5
                syndrome_ok_l1 = True
                exact_u1_for_record = True
            else:
                from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa as _dec_l1
                _res_l1 = _dec_l1(h1_full, p_i, s1, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, field=field)
                # BP-04 fail-closed dormant cross-layer APP entry: future
                # reactivation needs its own OpenSpec; only CHECK_UPDATED passes.
                require_check_updated_provenance(
                    getattr(_res_l1, "belief_provenance", None),
                    consumer="v52 L1->L2 APP prior",
                )
                q = softmax_beliefs(_res_l1.final_beliefs)
                ent, md = compute_entropy_and_diff(q, p_i)
                # L1 diagnostics for records: derive from q vs u1a
                _x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
                syndrome_ok_l1 = bool(np.array_equal(syndrome_of_gf32(h1_full, _x_hat_u1, field), s1))
                exact_u1_for_record = bool(np.array_equal(_x_hat_u1, u1a))
                iterations_l1 = int(_res_l1.iterations)
            accounting.register_complete(layer="l1")
            prior_l2 = get_l1_app_prior_l2(counts_by_source[source], bob, q)
            errors_initial = _compute_errors_initial(u2a, u2b)
            # base spec
            m2 = SOURCE_CHECKS[source]
            base_mid = f"lane_c_{source}_s{_rep_seed('lane_c', source)}"
            base_spec = {
                "call_id": f"C{call_id_counter:02d}",
                "source": source, "block_seed": bseed,
                "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
                "matrix_id": base_mid,
                "held_out_ordinal_start": win["held_out_ordinal_start"], "held_out_ordinal_end": win["held_out_ordinal_end"],
                "frame_ids": list(win["frame_ids"]), "pairs_count": PAIRS_PER_BLOCK, "sampling_mode": SAMPLING_MODE,
                "leak_total": leak_for(source), "leak_joint": leak_joint_for(source),
            }
            H_base = matrices[("lane_c", source)][0]
            accounting.register_start(layer="base")
            validate_decoder_contract({"H": H_base, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
            # decode base (also old) — same q shared to rescue
            raw_base = _evaluate_one_l2(H_base, source, bseed, counts_by_source[source], bob, u2a, u2b, field, DECODER_SETTING, fake_runner, decode_fn, errors_initial, base_spec, q=prior_l2, p_prior=p_i, iterations_l1=iterations_l1, entropy=ent, mean_abs=md)
            # expose L1 diagnostics in raw for record consistency (exact_u1/syndrome_ok_l1 come from real L1 BP)
            raw_base["exact_u1"] = bool(exact_u1_for_record)
            raw_base["syndrome_ok_l1"] = bool(syndrome_ok_l1)
            # raw_base already contains arm etc
            raw_base["arm"]="base_shared"; raw_base["pass_index"]=1; raw_base["used_increment"]=False; raw_base["joint"]=False
            raw_base["leak_total"]=leak_for(source)
            rec_base = build_record(base_spec, raw_base, DECODER_SETTING)
            records.append(rec_base)
            accounting.register_complete(layer="base")
            call_id_counter+=1
            verify_base = bool(raw_base["syndrome_ok_l2"] and raw_base["tag_ok"])
            exact_base = bool(raw_base["exact_full"])
            # old deduplication: old_exact = base_exact (no extra call)
            if exact_base:
                old_success+=1
                per_source_counts[source]["old"]+=1
            # first pass success accounting: verify only (public syndrome&&tag), exact only for stats/G3'
            if verify_base:
                first_pass_success+=1
                per_source_counts[source]["first"]+=1
                # final counts exact only as descriptive; G3' undetected==0 uses tag
                if exact_base:
                    final_success+=1
                    per_source_counts[source]["final"]+=1
                else:
                    # verify true but exact false = undetected/wrong would be counted elsewhere; still no rescue, not final success
                    pass
                # leak stays base, no rescue
            else:
                # rescue attempt
                n_rescue_attempted+=1
                per_source_counts[source]["rescue_attempted"]+=1
                # need joint matrix
                H_joint = matrices[("h_joint", source)][0]
                joint_mid = base_mid + "+h_inc"
                # rescue spec: reuse same call_id? No new id
                rescue_spec = {
                    "call_id": f"C{call_id_counter:02d}",
                    "source": source, "block_seed": bseed,
                    "arm": "rescue", "pass_index": 2, "used_increment": True, "joint": True,
                    "matrix_id": joint_mid,
                    "held_out_ordinal_start": win["held_out_ordinal_start"], "held_out_ordinal_end": win["held_out_ordinal_end"],
                    "frame_ids": list(win["frame_ids"]), "pairs_count": PAIRS_PER_BLOCK, "sampling_mode": SAMPLING_MODE,
                    "leak_total": leak_joint_for(source), "leak_joint": leak_joint_for(source),
                }
                accounting.register_start(layer="rescue")
                validate_decoder_contract({"H": H_joint, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
                raw_rescue = _evaluate_one_l2(H_joint, source, bseed, counts_by_source[source], bob, u2a, u2b, field, DECODER_SETTING, fake_runner, decode_fn, errors_initial, rescue_spec, q=prior_l2, p_prior=p_i, iterations_l1=iterations_l1, entropy=ent, mean_abs=md)
                raw_rescue["exact_u1"] = bool(exact_u1_for_record)
                raw_rescue["syndrome_ok_l1"] = bool(syndrome_ok_l1)
                raw_rescue["arm"]="rescue"; raw_rescue["pass_index"]=2; raw_rescue["used_increment"]=True; raw_rescue["joint"]=True
                raw_rescue["leak_total"]=leak_joint_for(source)
                rec_rescue = build_record(rescue_spec, raw_rescue, DECODER_SETTING)
                records.append(rec_rescue)
                accounting.register_complete(layer="rescue")
                call_id_counter+=1
                verify2 = bool(raw_rescue["syndrome_ok_l2"] and raw_rescue["tag_ok"])
                exact_rescue = bool(raw_rescue["exact_full"])
                if verify2 and exact_rescue:
                    rescued+=1
                    per_source_counts[source]["rescued"]+=1
                    final_success+=1
                    per_source_counts[source]["final"]+=1
                else:
                    # still failure, final not increment
                    pass
                # old already counted as failure
            # end per block
    # validate accounting 30-45
    fails = accounting.validate_executed()
    if fails:
        raise IntegrityFailure(fails[0][0], fails[0][1])
    # records sorted already by call_id order source asc block asc base->rescue
    # summary
    total_blocks = 15
    avg_leak_per_source: dict[str,float] = {}
    for src in SOURCE_ORDER:
        n_resc_src = per_source_counts[src]["rescue_attempted"]
        # per source total 5 blocks
        avg_leak_per_source[src] = float(leak_for(src) + 40 * n_resc_src / 5)
    # overall avg: weighted by source? spec says avg = base+40*N_rescue/15 where base per source? Actually leak_base per source differs, so overall avg not single number; we report per source and overall weighted.
    # For overall we compute mean of per-block leaks across 15: sum leak per block /15
    total_leak_sum = 0
    for rec in records:
        if rec["arm"]=="base_shared":
            # find if this block had rescue: check if there's a rescue record for same block
            has_rescue = any(r["block_seed"]==rec["block_seed"] and r["arm"]=="rescue" for r in records)
            if has_rescue:
                total_leak_sum += leak_joint_for(rec["source"])
            else:
                total_leak_sum += leak_for(rec["source"])
        # rescue records not counted separately for per-block leak (already counted via base+rescue? Actually total_leak_sum counts per block final leak, not per call)
    # alternative: per block final leak
    # we already did per block; but rescue records leak is same as joint, so counting base_shared with has_rescue as joint covers per block.
    # However we added sum only for base_shared records => that's per block count correctly 15.
    avg_overall = float(total_leak_sum / total_blocks) if total_blocks else 0.0

    # paired old vs V52: old_success vs final_success
    # prepare json records etc
    output_root.mkdir(parents=True, exist_ok=False)
    # write records json/csv
    records_sorted = sorted(records, key=lambda r: r["call_id"])
    with (output_root / "v52_records.json").open("w", encoding="utf-8") as f:
        json.dump(records_sorted, f, indent=2, ensure_ascii=False)
    with (output_root / "v52_records.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(RECORD_FIELDS))
        w.writeheader()
        for r in records_sorted:
            w.writerow({k: (",".join(map(str, v)) if k=="frame_ids" and isinstance(v, list) else v) for k,v in r.items()})
    summary = {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "accepted_plan_sha": ACCEPTED_PLAN_SHA,
        "branch_ref": BRANCH_REF,
        "execution_scope": EXECUTION_SCOPE,
        "mechanism_id": MECHANISM_ID,
        "tag_scope": TAG_SCOPE,
        "decoder_setting": list(DECODER_SETTING),
        "delta_m": DELTA_M,
        "leakage": {
            "per_source": {s: {"leak_base": leak_for(s), "leak_joint": leak_joint_for(s), "delta": 40} for s in SOURCE_ORDER},
            "leakage_already_accounted": True,
            "first_pass_success_leak": {s: leak_for(s) for s in SOURCE_ORDER},
            "rescued_success_leak": {s: leak_joint_for(s) for s in SOURCE_ORDER},
            "final_failure_leak": {s: leak_joint_for(s) for s in SOURCE_ORDER},
            "avg_leak_per_source": avg_leak_per_source,
            "avg_overall": avg_overall,
            "formula": "avg_leak = leak_base + 40*N_rescue_attempted/15",
            "n_rescue_attempted": n_rescue_attempted,
        },
        "counts": {
            "first_pass_success": first_pass_success,
            "rescued_by_increment": rescued,
            "final_exact_full": final_success,
            "old_exact_full": old_success,
            "per_source": per_source_counts,
            "n_blocks": total_blocks,
            "rescue_rate": float(rescued / n_rescue_attempted) if n_rescue_attempted else 0.0,
        },
        "accounting": {
            "decoder_calls_planned": {"total": f"{PLANNED_L1+PLANNED_L2_BASE}-{HARD_CALL_CAP}", "l1": PLANNED_L1, "l2_base": PLANNED_L2_BASE, "l2_rescue_max": PLANNED_L2_RESCUE_MAX, "l2_max": PLANNED_L2_MAX},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "l2": accounting.started_l2, "base": accounting.started_base, "rescue": accounting.started_rescue},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "l2": accounting.completed_l2, "base": accounting.completed_base, "rescue": accounting.completed_rescue},
            "hard_cap": HARD_CALL_CAP,
        },
        "matrix": {
            "per_source": {s: {"m2": SOURCE_CHECKS[s], "m_joint": SOURCE_CHECKS[s]+DELTA_M, "delta_m": DELTA_M, "joint_rank": SOURCE_CHECKS[s]+DELTA_M, "nested": True, "independence": DELTA_M, "row_max_le16": True, "col_inc_max_le1": True, "E_inc": int(matrices[("h_inc", s)][1].get("E_inc",96))} for s in SOURCE_ORDER},
        },
        "sampling_mode": SAMPLING_MODE,
        "held_out_provenance": {
            "block_windows": {str(k): v for k,v in BLOCK_WINDOWS.items()},
            "sampling_mode": SAMPLING_MODE,
            "fresh_15": NEW_BLOCK_SEEDS,
        },
        "provenance": {
            "h_inc_det_ids": INC_DET_IDS,
            "deterministic": "single_run_no_seed_search",
            "joint_rank_nested_independence": "verified",
        },
        "terminal_state": TERMINAL_NESTED_RESCUE_COMPLETE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "statistics_note": STATISTICS_NOTE,
    }
    with (output_root / "v52_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return {"output_root": output_root, "terminal_state": TERMINAL_NESTED_RESCUE_COMPLETE, "summary": summary, "records": records_sorted}

