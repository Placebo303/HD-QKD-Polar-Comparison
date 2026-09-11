"""V51P0 Lane C label-only NB-ACE (custom check_extrinsic) deterministic optimizer.

Frozen V51P0 protocol (formal-ir-v51-lane-c-label-nbace):
- n=1024, m2 184/190/192, GF32 poly37, Lane C ordinal-2 support/position_permutations frozen,
  decoder 90/1.0 early-stop, leak 1064/1094/1104 (5*m2+80+64), H1 16x1024 rank16, L2-only tag.
- Deterministic label optimizer: primary lexicographic (deg4,deg6,deg8,cand) deg4-first,
  custom check_extrinsic_score = ACE-100 if degenerate else ACE (secondary report only,
  explicitly NOT literature-standard NB-ACE). Greedy canonical edge order 1..31 up to 2 sweeps,
  incremental via edge_to_cycle_ids, no seed search, decoder-free single run.
- 15 new unused held-out blocks 392001-005/101-105/201-205 deterministic 4-frame windows 1024 pairs
  per block, total 45 calls (L1 15 + L2 30 old/new paired per block, same bob/Pi(U2) per block).
- Master gate label_improved = (forall source lex non-worsening) and (exists strict improvement);
  otherwise V51_LABEL_NO_IMPROVEMENT blocker, no decoder.
- Paired primary exact_full with McNemar b/c/discordance, residual/runtime, four-way, G3' undetected==0.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
Accepted plan SHA: 2b7ce522827a0b48aa776d5451d2b6005797816d
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from collections import Counter
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
    enumerate_canonical_simple_cycles,
    classify_cycle_algebraic_degeneracy,
    get_canonical_support_edges,
    get_substream_generator,
    sample_uniform_gf32_nonzero,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

CYCLE_ID = "V51P0"
CHANGE_ID = "formal-ir-v51-lane-c-label-nbace"
ACCEPTED_PLAN_SHA = "2b7ce522827a0b48aa776d5451d2b6005797816d"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v51_lane_c_label_nbace_45_calls_paired_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
LABEL_ORDER: tuple[str, ...] = ("old", "new")

MECHANISM_ID = "lane_c_label_only_check_extrinsic_deterministic_single_run_deg4_first"
TAG_SCOPE = "l2_only"
TAG_SOURCE_STR = "v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only"
LEAKAGE_ALREADY_ACCOUNTED_NOTE = "leakage already accounted: H1-16 1064/1094/1104 includes 64-bit tag; SHA-trunc64 random-hash-model approximate 2^-64 L2-only"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

PLANNED_CALLS = 45
PLANNED_L1 = 15
PLANNED_L2 = 30
HARD_CALL_CAP = 45

H1_M = 16
H1_N = 1024
H1_MATRIX_ID = "V31-H1-QC-16×1024"
H1_FAMILY = "QC-cyclic-projective"

PAIRS_PER_FRAME = 256
FRAMES_PER_BLOCK = 4
PAIRS_PER_BLOCK = 1024
BLOCK_LENGTH_CONST = 1024

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

SAMPLING_MODE = "deterministic_four_consecutive_frames_heldout_unused_new"

# 15 held-out blocks frozen (design §2.4)
NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [392001, 392002, 392003, 392004, 392005],
    "1p5M": [392101, 392102, 392103, 392104, 392105],
    "2M": [392201, 392202, 392203, 392204, 392205],
}

BLOCK_WINDOWS: dict[int, dict[str, Any]] = {}
BLOCK_TO_SOURCE: dict[int, str] = {}

_V51_WINDOW_DEFS = [
    ("1M", 392001, 7, 10, [1607, 1608, 1609, 1610]),
    ("1M", 392002, 35, 38, [1635, 1636, 1637, 1638]),
    ("1M", 392003, 63, 66, [1663, 1664, 1665, 1666]),
    ("1M", 392004, 91, 94, [1691, 1692, 1693, 1694]),
    ("1M", 392005, 119, 122, [1719, 1720, 1721, 1722]),
    ("1p5M", 392101, 12, 15, [2225, 2226, 2227, 2228]),
    ("1p5M", 392102, 51, 54, [2264, 2265, 2266, 2267]),
    ("1p5M", 392103, 90, 93, [2303, 2304, 2305, 2306]),
    ("1p5M", 392104, 130, 133, [2343, 2344, 2345, 2346]),
    ("1p5M", 392105, 169, 172, [2382, 2383, 2384, 2385]),
    ("2M", 392201, 18, 21, [2934, 2935, 2936, 2937]),
    ("2M", 392202, 70, 73, [2986, 2987, 2988, 2989]),
    ("2M", 392203, 122, 125, [3038, 3039, 3040, 3041]),
    ("2M", 392204, 174, 177, [3090, 3091, 3092, 3093]),
    ("2M", 392205, 225, 228, [3141, 3142, 3143, 3144]),
]
for _src, _bid, _s, _e, _fids in _V51_WINDOW_DEFS:
    BLOCK_WINDOWS[_bid] = {
        "source": _src,
        "held_out_ordinal_start": _s,
        "held_out_ordinal_end": _e,
        "frame_ids": _fids,
        "pairs_count": PAIRS_PER_BLOCK,
        "sampling_mode": SAMPLING_MODE,
    }
    BLOCK_TO_SOURCE[_bid] = _src

# Forbidden registries (FORBIDDEN 156 = 141 +15 V50 391xxx)
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
FORBIDDEN_BLOCK_SEEDS = FORBIDDEN_156

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
FROZEN_REPRESENTATIVE_MATRIX_IDS_NEW: tuple[str, ...] = (
    "lane_c_1M_s383102_check_extrinsic",
    "lane_c_1p5M_s383202_check_extrinsic",
    "lane_c_2M_s383302_check_extrinsic",
)

def _build_frozen_workload() -> tuple[dict[str, Any], ...]:
    rows = []
    cid = 1
    for source in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[source]:
            win = BLOCK_WINDOWS[bseed]
            leak = 5 * SOURCE_CHECKS[source] + 5 * H1_M + 64
            for label_id in LABEL_ORDER:
                matrix_id = f"lane_c_{source}_s{_rep_seed('lane_c', source)}" if label_id == "old" else f"lane_c_{source}_s{_rep_seed('lane_c', source)}_check_extrinsic"
                rows.append({
                    "call_id": f"C{cid:02d}",
                    "source": source,
                    "block_seed": bseed,
                    "label_id": label_id,
                    "matrix_id": matrix_id,
                    "h1_matrix_id": H1_MATRIX_ID,
                    "held_out_ordinal_start": win["held_out_ordinal_start"],
                    "held_out_ordinal_end": win["held_out_ordinal_end"],
                    "frame_ids": list(win["frame_ids"]),
                    "pairs_count": PAIRS_PER_BLOCK,
                    "sampling_mode": SAMPLING_MODE,
                    "leak_total": leak,
                    "max_iter": MAX_ITER,
                    "damping_alpha": DAMPING_ALPHA,
                })
                cid += 1
    return tuple(rows)

FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = _build_frozen_workload()

def workload_rows() -> list[dict[str, Any]]:
    return list(FROZEN_WORKLOAD)

PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 392001, "1p5M": 392101, "2M": 392201}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v51_lane_c_label_nbace/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v51_lane_c_label_nbace.py",
    "scripts/execute_v51_lane_c_label_nbace.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
)

SOURCE_M2: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}
SOURCE_L2_SYNDROME_BITS: dict[str, int] = {s: 5 * m for s, m in SOURCE_M2.items()}

def leak_for(source: str, h1_rows: int = H1_M) -> int:
    return 5 * SOURCE_M2[source] + 5 * h1_rows + 64

MASTER_STOP_RULE = (
    "唯一一次 45-call paired (15 blocks 392001-005/101-105/201-205 deterministic 4-frame 1024 pairs per block, per block 1 L1 shared +2 L2 old/new same bob/Pi(U2) same m2/decoder 90/1.0 poly37) "
    "Lane C support frozen only labels 1..31 optimized deterministically primary lex (deg4,deg6,deg8,cand) deg4-first, custom check_extrinsic_score=ACE-100 if deg else ACE secondary NOT literature NB-ACE; "
    "label_improved = (forall lex non-worsening) and (exists strict) else V51_LABEL_NO_IMPROVEMENT blocker; paired exact_full primary McNemar b/c/discordance residual/runtime four-way G3' undetected==0; L2-only tag 2^-64; no TRAIN+VAL."
)

TERMINAL_EVIDENCE_INVALID = "V51_EVIDENCE_INVALID"
TERMINAL_LABEL_NO_IMPROVEMENT = "V51_LABEL_NO_IMPROVEMENT"
TERMINAL_PAIRED_COMPLETE = "V51_PAIRED_COMPLETE"
ALL_TERMINALS = frozenset({TERMINAL_EVIDENCE_INVALID, TERMINAL_LABEL_NO_IMPROVEMENT, TERMINAL_PAIRED_COMPLETE})

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "source",
    "block_seed",
    "label_id",
    "matrix_id",
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
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "label_id", "h1_rows", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY single deterministic label-only optimization on frozen Lane C support/position_permutations/m2 184/190/192 n=1024 GF32 poly37 decoder 90/1.0 leak 1064/1094/1104, primary lex (deg4,deg6,deg8,cand) deg4-first, custom check_extrinsic_score=ACE-100 if deg else ACE secondary report NOT literature NB-ACE, no decoder-driven seed search, 15 new unused held-out blocks 392001-005/101-105/201-205 paired old vs new exact_full oracle not via tag L2-only 2^-64",
    "leakage H1-16 1064/1094/1104 already accounted f_total=leak/[N(H1+H2)] N=1024, verification L2-only SHA-trunc64 random-hash-model approximate 2^-64",
    "not threshold/SKR/formal qualification/promotion; paired only descriptive McNemar discordance residual/runtime four-way; no TRAIN+VAL arm",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is 15 blocks paired old vs new (45 invocations = 15 L1 +30 L2; 30 L2 records paired). "
    "Exact-recovery proportions reported with n and raw counts; any interval is naive and uncorrected for clustering; no significance testing. "
    "Primary is exact_full = exact_u1 && exact_l2 via paired McNemar."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# L1 prior helpers (same as V50, TRAIN only)
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
# Label spectrum helpers (decoder-free, deg4-first, custom check_extrinsic)
# ---------------------------------------------------------------------------

def _ace_for_cycle(cycle, row_deg: np.ndarray) -> int:
    return int(sum(int(row_deg[c]) - 2 for c in cycle.checks))


def compute_spectrum(H: np.ndarray, field: Optional[GF2mField] = None) -> dict[str, Any]:
    """Decoder-free spectrum for one H: support cycles, degenerate counts, custom check_extrinsic secondary."""
    field = field or GF2mField.create(32)
    m, n = H.shape
    binary = (H != 0).astype(np.uint8)
    row_deg = np.count_nonzero(binary, axis=1)
    c4, c6, c8, edge_to_ids = enumerate_canonical_simple_cycles(binary)
    deg4 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c4)
    deg6 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c6)
    deg8 = sum(classify_cycle_algebraic_degeneracy(c, H, field) for c in c8)

    def _score_list(cycles):
        vals = []
        for cyc in cycles:
            ace = _ace_for_cycle(cyc, row_deg)
            is_deg = classify_cycle_algebraic_degeneracy(cyc, H, field)
            score = ace - 100 if is_deg else ace  # custom, NOT literature NB-ACE
            vals.append((ace, is_deg, score))
        return vals

    vals4 = _score_list(c4)
    vals6 = _score_list(c6)
    vals8 = _score_list(c8)
    min_check_extrinsic4 = min(v[2] for v in vals4) if vals4 else None
    min_check_extrinsic6 = min(v[2] for v in vals6) if vals6 else None
    min_check_extrinsic8 = min(v[2] for v in vals8) if vals8 else None
    deg_aces4 = [v[0] for v in vals4 if v[1]]
    min_deg_ace4 = min(deg_aces4) if deg_aces4 else None
    deg_aces6 = [v[0] for v in vals6 if v[1]]
    min_deg_ace6 = min(deg_aces6) if deg_aces6 else None
    deg_aces8 = [v[0] for v in vals8 if v[1]]
    min_deg_ace8 = min(deg_aces8) if deg_aces8 else None
    if deg4 > 0:
        gg = 4
    elif deg6 > 0:
        gg = 6
    elif deg8 > 0:
        gg = 8
    else:
        gg = None
    rank = compute_gf32_rank(H, field)
    return {
        "rank": int(rank),
        "E": int(np.count_nonzero(binary)),
        "row_deg_min": int(row_deg.min()), "row_deg_max": int(row_deg.max()), "row_deg_mean": float(row_deg.mean()),
        "col_deg_min": int(np.count_nonzero(binary, axis=0).min()), "col_deg_max": int(np.count_nonzero(binary, axis=0).max()),
        "support_cycles_4": len(c4), "support_cycles_6": len(c6), "support_cycles_8": len(c8),
        "degenerate_4": int(deg4), "degenerate_6": int(deg6), "degenerate_8": int(deg8),
        "min_check_extrinsic4": min_check_extrinsic4, "min_check_extrinsic6": min_check_extrinsic6, "min_check_extrinsic8": min_check_extrinsic8,
        "min_deg_ace4": min_deg_ace4, "min_deg_ace6": min_deg_ace6, "min_deg_ace8": min_deg_ace8,
        "generalized_girth": gg,
        "nondeg_frac4": (len(c4)-deg4)/len(c4) if len(c4) > 0 else 1.0,
        "nondeg_frac6": (len(c6)-deg6)/len(c6) if len(c6) > 0 else 1.0,
        "nondeg_frac8": (len(c8)-deg8)/len(c8) if len(c8) > 0 else 1.0,
        "cycles4": c4, "cycles6": c6, "cycles8": c8, "edge_to_ids": edge_to_ids, "row_deg": row_deg,
        "binary": binary,
    }


def deterministic_label_optimize(H_init: np.ndarray, max_sweeps: int = 2, field: Optional[GF2mField] = None) -> tuple[np.ndarray, int, int, int]:
    """Greedy deterministic label optimizer primary lex (deg4,deg6,deg8,cand), custom check_extrinsic secondary only.
    Efficient incremental via edge_to_cycle_ids.
    """
    field = field or GF2mField.create(32)
    H = H_init.copy()
    binary = (H != 0).astype(np.uint8)
    c4, c6, c8, edge_to_ids = enumerate_canonical_simple_cycles(binary)
    all_cycles = c4 + c6 + c8
    n4 = len(c4); n6 = len(c6)
    num_cycles = len(all_cycles)
    is_deg = [classify_cycle_algebraic_degeneracy(cyc, H, field) for cyc in all_cycles]

    def _count():
        d4 = sum(is_deg[i] for i in range(n4))
        d6 = sum(is_deg[i] for i in range(n4, n4+n6))
        d8 = sum(is_deg[i] for i in range(n4+n6, num_cycles))
        return d4, d6, d8
    curr_d4, curr_d6, curr_d8 = _count()
    canonical = get_canonical_support_edges(binary)
    total_updates = 0
    sweeps = 0
    for sweep in range(1, max_sweeps+1):
        updates = 0
        for edge in canonical:
            r, c = edge
            old_val = int(H[r, c])
            incident_ids = edge_to_ids.get(edge, [])
            if not incident_ids:
                if old_val != 1:
                    H[r, c] = 1
                    updates += 1
                continue
            old_inc_4 = sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length == 4)
            old_inc_6 = sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length == 6)
            old_inc_8 = sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length == 8)
            best_key = None
            best_val = old_val
            best_states = None
            for cand in range(1, 32):
                if cand == old_val:
                    cand_states = [is_deg[idx] for idx in incident_ids]
                    cand_d4, cand_d6, cand_d8 = curr_d4, curr_d6, curr_d8
                else:
                    H[r, c] = cand
                    cand_states = [classify_cycle_algebraic_degeneracy(all_cycles[idx], H, field) for idx in incident_ids]
                    cand_inc_4 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 4)
                    cand_inc_6 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 6)
                    cand_inc_8 = sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length == 8)
                    cand_d4 = curr_d4 - old_inc_4 + cand_inc_4
                    cand_d6 = curr_d6 - old_inc_6 + cand_inc_6
                    cand_d8 = curr_d8 - old_inc_8 + cand_inc_8
                cand_key = (cand_d4, cand_d6, cand_d8, cand)
                if best_key is None or cand_key < best_key:
                    best_key = cand_key
                    best_val = cand
                    best_states = cand_states
                if cand != old_val:
                    H[r, c] = old_val
            if best_val != old_val:
                H[r, c] = best_val
                curr_d4, curr_d6, curr_d8, _ = best_key  # type: ignore
                for k, idx in enumerate(incident_ids):
                    is_deg[idx] = best_states[k]  # type: ignore
                updates += 1
            else:
                H[r, c] = old_val
        total_updates += updates
        sweeps = sweep
        if updates == 0:
            break
    final_rank = compute_gf32_rank(H, field)
    return H, sweeps, total_updates, int(final_rank)

# backward compat alias
def deterministic_nbace_label_optimize(H_init, max_sweeps=2):
    return deterministic_label_optimize(H_init, max_sweeps)


def build_label_spectrum(
    matrices_old: dict[str, np.ndarray],
    matrices_new: dict[str, np.ndarray],
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    """Per-source original vs new verifiable primary + custom secondary, and overall gate."""
    field = field or GF2mField.create(32)
    per_source: dict[str, Any] = {}
    all_not_worse = True
    any_strict = False
    for src in SOURCE_ORDER:
        H_old = matrices_old[src]
        H_new = matrices_new[src]
        spec_old = compute_spectrum(H_old, field)
        spec_new = compute_spectrum(H_new, field)
        binary_old = (H_old != 0).astype(np.uint8)
        binary_new = (H_new != 0).astype(np.uint8)
        support_equal = bool(np.array_equal(binary_old, binary_new))
        rank_ok = bool(spec_old["rank"] == spec_new["rank"] == SOURCE_CHECKS[src])
        cycles_equal = bool(spec_old["support_cycles_4"] == spec_new["support_cycles_4"] and spec_old["support_cycles_6"] == spec_new["support_cycles_6"] and spec_old["support_cycles_8"] == spec_new["support_cycles_8"])
        old_key = (spec_old["degenerate_4"], spec_old["degenerate_6"], spec_old["degenerate_8"])
        new_key = (spec_new["degenerate_4"], spec_new["degenerate_6"], spec_new["degenerate_8"])
        not_worse = new_key <= old_key
        strictly_better = new_key < old_key
        if not not_worse:
            all_not_worse = False
        if strictly_better:
            any_strict = True
        per_source[src] = {
            "support_exact_equal": support_equal,
            "rank_old": int(spec_old["rank"]), "rank_new": int(spec_new["rank"]), "rank_ok": rank_ok,
            "support_cycles_4_old": int(spec_old["support_cycles_4"]), "support_cycles_4_new": int(spec_new["support_cycles_4"]),
            "support_cycles_6_old": int(spec_old["support_cycles_6"]), "support_cycles_6_new": int(spec_new["support_cycles_6"]),
            "support_cycles_8_old": int(spec_old["support_cycles_8"]), "support_cycles_8_new": int(spec_new["support_cycles_8"]),
            "cycles_equal": cycles_equal,
            "degenerate_4_old": int(spec_old["degenerate_4"]), "degenerate_4_new": int(spec_new["degenerate_4"]), "delta_deg4": int(spec_new["degenerate_4"] - spec_old["degenerate_4"]),
            "degenerate_6_old": int(spec_old["degenerate_6"]), "degenerate_6_new": int(spec_new["degenerate_6"]), "delta_deg6": int(spec_new["degenerate_6"] - spec_old["degenerate_6"]),
            "degenerate_8_old": int(spec_old["degenerate_8"]), "degenerate_8_new": int(spec_new["degenerate_8"]), "delta_deg8": int(spec_new["degenerate_8"] - spec_old["degenerate_8"]),
            "generalized_girth_old": spec_old["generalized_girth"], "generalized_girth_new": spec_new["generalized_girth"],
            "nondeg_frac6_old": float(spec_old["nondeg_frac6"]), "nondeg_frac6_new": float(spec_new["nondeg_frac6"]),
            "nondeg_frac8_old": float(spec_old["nondeg_frac8"]), "nondeg_frac8_new": float(spec_new["nondeg_frac8"]),
            "min_check_extrinsic6_old": spec_old["min_check_extrinsic6"], "min_check_extrinsic6_new": spec_new["min_check_extrinsic6"],
            "min_check_extrinsic8_old": spec_old["min_check_extrinsic8"], "min_check_extrinsic8_new": spec_new["min_check_extrinsic8"],
            "min_deg_ace6_old": spec_old["min_deg_ace6"], "min_deg_ace6_new": spec_new["min_deg_ace6"],
            "min_deg_ace8_old": spec_old["min_deg_ace8"], "min_deg_ace8_new": spec_new["min_deg_ace8"],
            "lex_old": list(old_key), "lex_new": list(new_key),
            "not_worse": bool(not_worse), "strictly_better": bool(strictly_better),
        }
    label_improved = bool(all_not_worse and any_strict)
    return {"per_source": per_source, "all_not_worse": bool(all_not_worse), "any_strictly_better": bool(any_strict), "label_improved": bool(label_improved),
            "custom_definition": "check_extrinsic_score(C)=ACE(C)-100 if is_deg else ACE(C) where ACE(C)=sum(row_deg-2); custom secondary report only, NOT literature-standard NB-ACE"}


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
    overlap = set(all_seeds) & FORBIDDEN_156
    if overlap:
        return False, f"new seeds overlap forbidden 156 registries: {sorted(overlap)}"
    expected = NEW_BLOCK_SEEDS
    flat_expected = {s for lst in expected.values() for s in lst}
    flat_actual = set(all_seeds)
    if seeds is None and flat_actual != flat_expected:
        return False, "new seeds must be exactly frozen 392001-005/101-105/201-205"
    for src in SOURCE_ORDER:
        seeds_sorted = sorted(reg[src])
        if seeds_sorted != reg[src]:
            return False, f"seeds for {src} must be sorted ascending"
        if seeds_sorted[-1] - seeds_sorted[0] != 4:
            return False, f"seeds for {src} must be consecutive 5"
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
# Structural reconstruction (J3)
# ---------------------------------------------------------------------------

def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")

def reconstruct_v51_matrices(
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
        matrices[("lane_c_old", source)] = (matrix, metrics)
        # deterministic new: single-run optimizer
        H_new, _, _, _ = deterministic_label_optimize(matrix, max_sweeps=2, field=field)
        # verify support exact equal, rank etc will be checked in spectrum; also verify cycles unchanged
        spec_old = compute_spectrum(matrix, field)
        spec_new = compute_spectrum(H_new, field)
        if spec_old["support_cycles_4"] != spec_new["support_cycles_4"] or spec_old["support_cycles_6"] != spec_new["support_cycles_6"] or spec_old["support_cycles_8"] != spec_new["support_cycles_8"]:
            raise IntegrityFailure("J3", f"Lane C new support cycles changed for {source}")
        if not np.array_equal((matrix != 0).astype(np.uint8), (H_new != 0).astype(np.uint8)):
            raise IntegrityFailure("J3", f"Lane C new support not exact equal for {source}")
        metrics_new = dict(metrics)
        metrics_new["matrix_id"] = f"lane_c_{source}_s{seed}_check_extrinsic"
        metrics_new["degenerate_cycles_4"] = int(spec_new["degenerate_4"])
        metrics_new["degenerate_cycles_6"] = int(spec_new["degenerate_6"])
        metrics_new["degenerate_cycles_8"] = int(spec_new["degenerate_8"])
        matrices[("lane_c_new", source)] = (H_new, metrics_new)
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


def compute_label_spectrum_for_matrices(matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]], field: Optional[GF2mField] = None) -> dict[str, Any]:
    field = field or GF2mField.create(DIMENSION)
    old = {src: matrices[("lane_c_old", src)][0] for src in SOURCE_ORDER}
    new = {src: matrices[("lane_c_new", src)][0] for src in SOURCE_ORDER}
    return build_label_spectrum(old, new, field)

# ---------------------------------------------------------------------------
# Sentinel preflight (J5) label spectrum + support/rank + L1->Pi
# ---------------------------------------------------------------------------

def label_spectrum_preflight(
    counts_by_source: dict[str, np.ndarray],
    matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    field = field or GF2mField.create(DIMENSION)
    if matrices is None:
        matrices = reconstruct_v51_matrices(field=field)
    # isolation
    _iso_ok, _iso_msg = validate_train_heldout_isolation()
    if not _iso_ok:
        raise IntegrityFailure("J4", f"train/held-out isolation failed: {_iso_msg}")
    for src in SOURCE_ORDER:
        arr = counts_by_source.get(src)
        if arr is None or getattr(arr, "shape", None) != (1024, 1024):
            raise IntegrityFailure("J4", f"counts TRAIN shape invalid for {src}")
    h1_full = matrices.get(("H1", "L1"), (None,))[0]
    if h1_full is None:
        raise IntegrityFailure("J3", "H1 missing")
    spectrum = compute_label_spectrum_for_matrices(matrices, field)
    # per-source checks
    for src in SOURCE_ORDER:
        per = spectrum["per_source"][src]
        if not per["support_exact_equal"]:
            raise IntegrityFailure("J3", f"support not exact equal for {src}")
        if not per["rank_ok"]:
            raise IntegrityFailure("J3", f"rank not ok for {src}")
        if not per["cycles_equal"]:
            raise IntegrityFailure("J3", f"cycles not equal for {src}")
        # held-out reachable + sampling
        bseed = PREFLIGHT_BLOCK_SEEDS[src]
        win = BLOCK_WINDOWS.get(bseed)
        if win is None or win["pairs_count"] != 1024 or len(win["frame_ids"]) != 4 or win["sampling_mode"] != SAMPLING_MODE:
            raise IntegrityFailure("J4", f"heldout not reachable for {src}/{bseed}")
        # L1 -> Pi(U2) path
        alice, bob = load_heldout_block(bseed)
        p_i = get_l1_prior_p_u1_given_b(counts_by_source[src], bob)
        if p_i.shape != (1024, 32) or not np.allclose(p_i.sum(axis=1), 1.0):
            raise IntegrityFailure("J5", f"L1 prior failed for {src}")
        # prior -> Pi via q
        fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.07 * np.sin(np.arange(32))[None, :]
        q = softmax_beliefs(fake_beliefs)
        prior_l2 = get_l1_app_prior_l2(counts_by_source[src], bob, q)
        if prior_l2.shape != (1024, 32) or not np.allclose(prior_l2.sum(axis=1), 1.0):
            raise IntegrityFailure("J5", f"L1 APP prior failed for {src}")
        # leakage & tag
        leak_ok = bool(leak_for(src, H1_M) == (1064 if src == "1M" else 1094 if src == "1p5M" else 1104))
        if not leak_ok:
            raise IntegrityFailure("J5", f"leakage not accounted for {src}")
        try:
            empty = np.empty(0, dtype=np.uint8)
            x2 = np.array([1, 2, 3, 4], dtype=np.uint8)
            t = compute_tag_64(empty, x2)
            assert isinstance(t, str) and len(t) == 16
            int(t, 16)
        except Exception as exc:
            raise IntegrityFailure("J5", f"v35 tag import failed: {exc}") from exc
    return {"spectrum": spectrum, "label_improved": bool(spectrum["label_improved"]), "support_equal_ok": True, "rank_ok": True, "label_spectrum_ok": True, "l1_to_pi_ok": True, "tag_import_ok": True, "leakage_accounted": True}

# alias
single_arm_binding_preflight = label_spectrum_preflight

# ---------------------------------------------------------------------------
# V51 L2-only tag helpers
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
# Budget accounting (J10) hard cap 45
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

    def register_start(self, layer: str = "total") -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        if layer == "l1" and self.started_l1 >= PLANNED_L1:
            raise IntegrityFailure("J10", "l1 cap 15 reached")
        if layer == "l2" and self.started_l2 >= PLANNED_L2:
            raise IntegrityFailure("J10", "l2 cap 30 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
        elif layer == "l2":
            self.started_l2 += 1

    def register_complete(self, layer: str = "total") -> None:
        if self.completed >= self.started:
            raise IntegrityFailure("J10", "completed without started")
        self.completed += 1
        if layer == "l1":
            self.completed_l1 += 1
        elif layer == "l2":
            self.completed_l2 += 1

    def validate_executed(self) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        if self.completed > self.hard_cap:
            failures.append(("J10", f"completed {self.completed} exceeds hard cap {self.hard_cap}"))
        if self.completed != self.started:
            failures.append(("J10", f"started {self.started} != completed {self.completed}"))
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
        "label_id": spec["label_id"],
        "matrix_id": raw["matrix_id"],
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
        "status": str(raw["status"]),
        "runtime_s": float(raw["runtime_s"]),
    }
    return {k: record[k] for k in RECORD_FIELDS}

def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    for key in RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    valid_call_ids = {spec["call_id"] for spec in FROZEN_WORKLOAD}
    if record["call_id"] not in valid_call_ids:
        return False, f"invalid call_id {record['call_id']!r}"
    if record["source"] not in SOURCE_ORDER:
        return False, f"invalid source {record['source']!r}"
    if record["label_id"] not in LABEL_ORDER:
        return False, f"invalid label_id {record['label_id']!r}"
    spec = next(s for s in FROZEN_WORKLOAD if s["call_id"] == record["call_id"])
    if record["block_seed"] != spec["block_seed"] or record["source"] != spec["source"] or record["label_id"] != spec["label_id"]:
        return False, "record source/block_seed/label_id mismatch frozen workload"
    if record["sampling_mode"] != SAMPLING_MODE:
        return False, f"sampling_mode must be {SAMPLING_MODE}"
    if record["pairs_count"] != PAIRS_PER_BLOCK:
        return False, f"pairs_count must be {PAIRS_PER_BLOCK}"
    if not isinstance(record["frame_ids"], list) or len(record["frame_ids"]) != 4:
        return False, "frame_ids must be list of 4"
    if record["held_out_ordinal_end"] - record["held_out_ordinal_start"] != 3:
        return False, "held_out window must be 4 frames"
    if record["pairs_count"] != FRAMES_PER_BLOCK * PAIRS_PER_FRAME:
        return False, "pairs_count must be 1024 = 4*256"
    for key in ("exact_l2", "exact_u1", "exact_full", "syndrome_ok_l2", "syndrome_ok_l1", "wrong_codeword_l2", "wrong_codeword_l1"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations_l1", "iterations_l2", "max_iter", "block_seed", "held_out_ordinal_start", "held_out_ordinal_end", "pairs_count", "leak_total"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    if record["max_iter"] != MAX_ITER or record["damping_alpha"] != DAMPING_ALPHA:
        return False, f"record setting {record['max_iter']}/{record['damping_alpha']} != frozen {DECODER_SETTING} (J9)"
    if record["wrong_codeword_l2"] != (record["syndrome_ok_l2"] and not record["exact_l2"]):
        return False, "wrong_codeword_l2 must equal syndrome_ok_l2 and not exact_l2"
    if record["wrong_codeword_l1"] != (record["syndrome_ok_l1"] and not record["exact_u1"]):
        return False, "wrong_codeword_l1 must equal syndrome_ok_l1 and not exact_u1"
    if record["exact_full"] != (record["exact_u1"] and record["exact_l2"]):
        return False, "exact_full must equal exact_u1 and exact_l2"
    if not isinstance(record["target_tag"], str) or len(record["target_tag"]) != 16:
        return False, "target_tag must be 16-char hex"
    if not isinstance(record["candidate_tag"], str) or len(record["candidate_tag"]) != 16:
        return False, "candidate_tag must be 16-char hex"
    try:
        int(record["target_tag"], 16)
        int(record["candidate_tag"], 16)
    except Exception:
        return False, "tags must be hex"
    if not isinstance(record["tag_ok"], bool):
        return False, "tag_ok must be bool"
    if record["tag_scope"] != TAG_SCOPE:
        return False, f"tag_scope must be {TAG_SCOPE}"
    if record["reclassified"] not in RECLASSIFIED_VALUES:
        return False, f"reclassified must be one of {RECLASSIFIED_VALUES}"
    expected = classify_reclassified(record["exact_l2"], record["syndrome_ok_l2"], record["tag_ok"])
    if record["reclassified"] != expected:
        return False, f"reclassified {record['reclassified']} != expected {expected}"
    if record["exact_l2"] and not record["tag_ok"]:
        return False, "exact_l2 true must have tag_ok true"
    if record["tag_ok"] != (record["target_tag"] == record["candidate_tag"]):
        return False, "tag_ok must equal target==candidate"
    expected_leak = leak_for(record["source"], H1_M)
    if record["leak_total"] != expected_leak:
        return False, f"leak_total {record['leak_total']} != expected {expected_leak} for {record['source']}"
    win = BLOCK_WINDOWS.get(record["block_seed"])
    if win is None:
        return False, f"block_seed {record['block_seed']} not in frozen 15"
    if record["held_out_ordinal_start"] != win["held_out_ordinal_start"] or record["held_out_ordinal_end"] != win["held_out_ordinal_end"]:
        return False, "held_out ordinal mismatch BLOCK_WINDOWS"
    if record["frame_ids"] != win["frame_ids"]:
        return False, f"frame_ids mismatch expected {win['frame_ids']}"
    return True, "SCHEMA_OK"

def validate_post_evaluation(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for rec in records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("J11", f"record {rec.get('call_id')}: {msg}"))
    expected_order = [
        (row["call_id"], row["source"], row["block_seed"], row["label_id"], row["matrix_id"])
        for row in workload_rows()
    ]
    actual_order = [
        (rec["call_id"], rec["source"], rec["block_seed"], rec["label_id"], rec["matrix_id"])
        for rec in records
    ]
    if actual_order != expected_order[: len(actual_order)]:
        failures.append(("J12", f"workload membership/order drift: {actual_order} != frozen C01-C30"))
    from collections import Counter as _Counter
    pair_keys = [(rec["source"], rec["block_seed"], rec["label_id"]) for rec in records]
    cnt = _Counter(pair_keys)
    for key, n in cnt.items():
        if n != 1:
            failures.append(("J6", f"duplicate block-label {key}: {n}"))
    expected_pairs = {(spec["source"], spec["block_seed"], spec["label_id"]) for spec in FROZEN_WORKLOAD}
    actual_pairs = set(pair_keys)
    missing = expected_pairs - actual_pairs
    if records and missing:
        failures.append(("J12", f"missing block-label combinations: {missing}"))
    for src in SOURCE_ORDER:
        recs_src = [r for r in records if r["source"] == src]
        seen_blocks = set()
        windows = []
        for r in recs_src:
            bs = r["block_seed"]
            if bs in seen_blocks:
                continue
            seen_blocks.add(bs)
            windows.append((r["held_out_ordinal_start"], r["held_out_ordinal_end"]))
        windows = sorted(windows)
        for i in range(len(windows) - 1):
            if windows[i][1] >= windows[i+1][0]:
                failures.append(("J6", f"source {src} windows overlap {windows[i]} vs {windows[i+1]}"))
        for r in recs_src:
            if r["pairs_count"] != 1024:
                failures.append(("J6", f"pairs_count !=1024 for {r['call_id']}"))
        # per block old->new order
        for bid in NEW_BLOCK_SEEDS[src]:
            rows = [r for r in recs_src if r["block_seed"] == bid]
            if rows:
                if [r["label_id"] for r in rows] != ["old", "new"]:
                    failures.append(("J12", f"block {bid} order must be old->new, got {[r['label_id'] for r in rows]}"))
    return failures


# ---------------------------------------------------------------------------
# Aggregates, paired, terminal
# ---------------------------------------------------------------------------

def aggregate_results(records: list[dict[str, Any]], spectrum: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    # paired old vs new per block on exact_full
    per_block_paired: list[dict[str, Any]] = []
    b_cnt = c_cnt = 0
    a_cnt = d_cnt = 0
    for src in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[src]:
            old_rec = next((r for r in records if r["block_seed"] == bseed and r["label_id"] == "old"), None)
            new_rec = next((r for r in records if r["block_seed"] == bseed and r["label_id"] == "new"), None)
            if old_rec is None or new_rec is None:
                continue
            old_exact = bool(old_rec["exact_full"])
            new_exact = bool(new_rec["exact_full"])
            if old_exact and new_exact:
                a_cnt += 1
            elif old_exact and not new_exact:
                b_cnt += 1
            elif not old_exact and new_exact:
                c_cnt += 1
            else:
                d_cnt += 1
            per_block_paired.append({
                "block_seed": int(bseed), "source": src,
                "old_exact_full": bool(old_exact), "new_exact_full": bool(new_exact),
                "old_errors_final": int(old_rec["errors_final"]), "new_errors_final": int(new_rec["errors_final"]),
                "old_iterations_l2": int(old_rec["iterations_l2"]), "new_iterations_l2": int(new_rec["iterations_l2"]),
                "old_runtime_s": float(old_rec["runtime_s"]), "new_runtime_s": float(new_rec["runtime_s"]),
            })
    discordance = int(b_cnt + c_cnt)
    gain = int(c_cnt - b_cnt)
    per_source: dict[str, Any] = {}
    for src in SOURCE_ORDER:
        recs = [r for r in records if r["source"] == src]
        per_source[src] = {
            "calls": len(recs),
            "exact_full": sum(1 for r in recs if r["exact_full"]),
            "exact_l2": sum(1 for r in recs if r["exact_l2"]),
            "exact_u1": sum(1 for r in recs if r["exact_u1"]),
            "old_exact_full": sum(1 for r in recs if r["label_id"] == "old" and r["exact_full"]),
            "new_exact_full": sum(1 for r in recs if r["label_id"] == "new" and r["exact_full"]),
            "detected": sum(1 for r in recs if r["reclassified"] == "detected_verification_failure"),
            "decoder_non_syndrome": sum(1 for r in recs if r["reclassified"] == "decoder_non_syndrome_failure"),
            "undetected": sum(1 for r in recs if r["reclassified"] == "undetected_accepted_wrong"),
            "exact": sum(1 for r in recs if r["reclassified"] == "exact"),
        }
    # residual/runtime distributions
    all_errors = [r["errors_final"] for r in records]
    all_iters = [r["iterations_l2"] for r in records]
    all_runtime = [r["runtime_s"] for r in records]
    return {
        "exact_full_total": sum(1 for r in records if r["exact_full"]),
        "exact_l2_total": sum(1 for r in records if r["exact_l2"]),
        "exact_u1_total": sum(1 for r in records if r["exact_u1"]),
        "paired_table": {"a_both_exact": int(a_cnt), "b_old_only": int(b_cnt), "c_new_only": int(c_cnt), "d_both_fail": int(d_cnt)},
        "discordance": int(discordance), "gain_new_minus_old": int(gain),
        "per_block_paired": per_block_paired,
        "per_source": per_source,
        "detected_total": sum(1 for r in records if r["reclassified"] == "detected_verification_failure"),
        "decoder_non_syndrome_total": sum(1 for r in records if r["reclassified"] == "decoder_non_syndrome_failure"),
        "undetected_total": sum(1 for r in records if r["reclassified"] == "undetected_accepted_wrong"),
        "exact_total": sum(1 for r in records if r["reclassified"] == "exact"),
        "wrong_total_l2": sum(1 for r in records if r["wrong_codeword_l2"]),
        "wrong_total_l1": sum(1 for r in records if r["wrong_codeword_l1"]),
        "mean_bp_entropy": float(np.mean([r["bp_posterior_entropy"] for r in records])) if records else 0.0,
        "mean_abs_diff": float(np.mean([r["mean_abs_diff_q_p"] for r in records])) if records else 0.0,
        "errors_final_dist": {"mean": float(np.mean(all_errors)) if all_errors else 0.0, "median": float(np.median(all_errors)) if all_errors else 0.0, "max": int(max(all_errors)) if all_errors else 0},
        "iterations_dist": {"mean": float(np.mean(all_iters)) if all_iters else 0.0, "median": float(np.median(all_iters)) if all_iters else 0.0},
        "runtime_dist": {"mean": float(np.mean(all_runtime)) if all_runtime else 0.0, "median": float(np.median(all_runtime)) if all_runtime else 0.0, "sum": float(sum(all_runtime)) if all_runtime else 0.0},
        "label_spectrum": spectrum,
    }

def determine_v51_terminal(integrity_ok: bool, label_improved: Optional[bool]) -> tuple[str, Optional[str], list[str]]:
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V51_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    if label_improved is False:
        trace.append("rule_1_label_not_improved -> V51_LABEL_NO_IMPROVEMENT")
        return TERMINAL_LABEL_NO_IMPROVEMENT, "label_improved false: exists worsening or no strict improvement", trace
    trace.append("rule_2_paired_complete -> V51_PAIRED_COMPLETE")
    return TERMINAL_PAIRED_COMPLETE, None, trace

# ---------------------------------------------------------------------------
# Environment loaders and git binding
# ---------------------------------------------------------------------------

def describe_v25_counts_provenance() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[4] / V25_COUNTS_RELATIVE_PATH
    base = {"path": str(path), "loader": "comparison_bench.formal_ir.v35_algorithm_development.load_v25_channel_counts", "role": "source-specific V25 TRAIN empirical counts (read-only)", "exists": path.is_file(),
            "counts_source": "TRAIN only (no TRAIN+VAL)", "held_out_pool": "split_manifest hold interval 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) deterministic 4-frame windows 392xxx"}
    return base

def git_rev_parse(repo_root: Path, ref: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), "rev-parse", ref], capture_output=True, text=True, check=True)
    return completed.stdout.strip()

def verify_scoped_clean(repo_root: Path, relative_paths: tuple[str, ...] = SCOPED_TRACKED_PATHS) -> None:
    completed = subprocess.run(["git", "-C", str(repo_root), "diff", "HEAD", "--quiet", "--", *relative_paths], capture_output=True, text=True)
    if completed.returncode != 0:
        raise IntegrityFailure("J1_TRACKED_DIRTY", f"scoped tracked files differ from HEAD; commit or revert before execution: {list(relative_paths)}")

def verify_execution_sha_binding(repo_root: Path, authorized_target_sha: str) -> dict[str, str]:
    head = git_rev_parse(repo_root, "HEAD")
    branch = git_rev_parse(repo_root, BRANCH_REF)
    if head != authorized_target_sha or branch != authorized_target_sha:
        raise IntegrityFailure("J1_SHA_BINDING_MISMATCH", f"authorized_target_sha={authorized_target_sha} but HEAD={head} and {BRANCH_REF}={branch}")
    return {"HEAD": head, BRANCH_REF: branch}


# ---------------------------------------------------------------------------
# Guarded diagnostic runner (exactly 45 calls conditional)
# ---------------------------------------------------------------------------

def _run_workload_calls(
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    setting: tuple[int, float],
    accounting: CallAccounting,
    sink: list[dict[str, Any]],
    decode_fn: Optional[Callable[..., Any]] = None,
    heldout_blocks: Optional[dict[int, tuple[np.ndarray, np.ndarray]]] = None,
) -> None:
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa
    decode = decode_fn if decode_fn is not None else decode_row_layered_fftqspa
    h1_full = matrices.get(("H1", "L1"), (None,))[0]
    if h1_full is None:
        raise IntegrityFailure("J3", "H1 missing")
    for src in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[src]:
            block_id = bseed
            if heldout_blocks is None or block_id not in heldout_blocks:
                raise IntegrityFailure("J4", f"held-out block {block_id} not preloaded before accounting")
            alice, bob = heldout_blocks[block_id]
            u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
            errors_initial = _compute_errors_initial(u2_alice, u2_bob)
            # single L1 per block TRAIN only
            counts = counts_by_source[src]
            p_i = get_l1_prior_p_u1_given_b(counts, bob)
            s1 = syndrome_of_gf32(h1_full, u1_alice, field)
            accounting.register_start(layer="l1")
            validate_decoder_contract({"H": h1_full, "source": src, "block_seed": block_id, "label_id": "old", "h1_rows": H1_M, "lane": "lane_c", "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": field, "decode_fn": decode_fn}, setting)
            if fake_runner:
                fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.07 * np.sin(np.arange(32))[None, :]
                q = softmax_beliefs(fake_beliefs)
                ent, mdiff = compute_entropy_and_diff(q, p_i)
                l1_iterations = 5
                syndrome_ok_l1 = True
                exact_u1 = True
                runtime_l1 = 0.001
            else:
                t0 = time.perf_counter()
                res = decode(h1_full, p_i, s1, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, field=field)
                # BP-04 fail-closed dormant cross-layer APP entry: future
                # reactivation needs its own OpenSpec; only CHECK_UPDATED passes.
                require_check_updated_provenance(
                    getattr(res, "belief_provenance", None),
                    consumer="v51 L1->L2 APP prior",
                )
                q = softmax_beliefs(res.final_beliefs)
                ent, mdiff = compute_entropy_and_diff(q, p_i)
                x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
                syndrome_ok_l1 = bool(np.array_equal(syndrome_of_gf32(h1_full, x_hat_u1, field), s1))
                exact_u1 = bool(np.array_equal(x_hat_u1, u1_alice))
                l1_iterations = int(res.iterations)
                runtime_l1 = float(getattr(res, "runtime_s", time.perf_counter() - t0))
            accounting.register_complete(layer="l1")
            # two L2 old/new same bob/q/pi
            for label_id in LABEL_ORDER:
                spec = next(s for s in workload_rows() if s["block_seed"] == block_id and s["label_id"] == label_id)
                matrix = matrices[("lane_c_old" if label_id == "old" else "lane_c_new", src)][0]
                accounting.register_start(layer="l2")
                validate_decoder_contract({"H": matrix, "source": src, "block_seed": block_id, "label_id": label_id, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": field, "decode_fn": decode_fn}, setting)
                raw_l2 = _evaluate_one_l2(
                    matrix=matrix, source=src, block_seed=block_id,
                    counts=counts, bob=bob, u2_alice=u2_alice, u2_bob=u2_bob,
                    field=field, setting=setting, fake_runner=fake_runner, decode=decode,
                    errors_initial=errors_initial, spec=spec, q=q,
                    exact_u1=exact_u1, syndrome_ok_l1=syndrome_ok_l1, iterations_l1=l1_iterations,
                    entropy=ent, mean_abs=mdiff, runtime_l1=runtime_l1,
                )
                rec = build_record(spec, raw_l2, setting)
                accounting.register_complete(layer="l2")
                sink.append(rec)

def _validate_before_decode(*args, **kwargs):
    pass

def _evaluate_one_l2(
    matrix: np.ndarray, source: str, block_seed: int,
    counts: np.ndarray, bob: np.ndarray, u2_alice: np.ndarray,
    u2_bob: np.ndarray, field: GF2mField, setting: tuple[int, float], fake_runner: bool, decode, errors_initial: int, spec: dict[str, Any],
    q: np.ndarray, exact_u1: bool, syndrome_ok_l1: bool, iterations_l1: int,
    entropy: float, mean_abs: float, runtime_l1: float,
) -> dict[str, Any]:
    max_iter, damping_alpha = setting
    prior = get_l1_app_prior_l2(counts, bob, q)
    synd = syndrome_of_gf32(matrix, u2_alice, field)
    if fake_runner:
        final_errors = 0
        exact_l2 = True
        syn_ok = True
        iters_l2 = 5
        runtime = 0.001
        status = "converged_exact"
        x_hat_l2 = np.asarray(u2_alice, dtype=np.uint8).copy()
    else:
        t0 = time.perf_counter()
        res = decode(matrix, prior, synd, max_iter=max_iter, damping_alpha=damping_alpha, field=field)
        final_errors = int(np.sum(res.x_hat != u2_alice))
        iters_l2 = int(res.iterations)
        runtime = float(getattr(res, "runtime_s", time.perf_counter() - t0))
        syn_ok = bool(res.syndrome_ok)
        exact_l2 = bool(np.array_equal(res.x_hat, u2_alice))
        status = res.status
        x_hat_l2 = np.asarray(res.x_hat, dtype=np.uint8)
    exact_full = bool(exact_u1 and exact_l2)
    empty = np.empty(0, dtype=np.uint8)
    target_tag = compute_tag_64(empty, np.asarray(u2_alice, dtype=np.uint8))
    candidate_tag = compute_tag_64(empty, x_hat_l2)
    tag_ok = bool(candidate_tag == target_tag)
    tag_scope = TAG_SCOPE
    reclassified = classify_reclassified(exact_l2, syn_ok, tag_ok)
    win = BLOCK_WINDOWS[block_seed]
    return {
        "source": source,
        "block_seed": block_seed,
        "matrix_id": spec["matrix_id"],
        "h1_matrix_id": H1_MATRIX_ID,
        "frame_ids": list(win["frame_ids"]),
        "held_out_ordinal_start": int(win["held_out_ordinal_start"]),
        "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
        "pairs_count": PAIRS_PER_BLOCK,
        "sampling_mode": SAMPLING_MODE,
        "errors_initial": int(errors_initial),
        "errors_final": int(final_errors),
        "exact_l2": bool(exact_l2),
        "exact_u1": bool(exact_u1),
        "exact_full": bool(exact_full),
        "syndrome_ok_l2": bool(syn_ok),
        "syndrome_ok_l1": bool(syndrome_ok_l1),
        "target_tag": target_tag,
        "candidate_tag": candidate_tag,
        "tag_ok": tag_ok,
        "tag_scope": tag_scope,
        "reclassified": reclassified,
        "iterations_l1": int(iterations_l1),
        "iterations_l2": int(iters_l2),
        "bp_posterior_entropy": float(entropy),
        "mean_abs_diff_q_p": float(mean_abs),
        "leak_total": int(spec.get("leak_total", leak_for(source, H1_M))),
        "status": str(status),
        "runtime_s": float(runtime),
    }


def build_v51_summary(
    *,
    lifecycle_state: str,
    fake_runner: bool,
    authorized_target_sha: Optional[str],
    sha_binding: Optional[dict[str, str]],
    counts_provenance: dict[str, Any],
    accounting: CallAccounting,
    aggregates: Optional[dict[str, Any]],
    spectrum: Optional[dict[str, Any]],
    routing_trace: list[str],
    integrity_failures: Optional[list[tuple[str, str]]],
    terminal_state: str,
    terminal_reason: Optional[str],
    structural_matrices_count: int,
    undetected_anomaly: bool = False,
) -> dict[str, Any]:
    agg = aggregates if aggregates is not None else {}
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import SOURCE_H as V31_H
        f_totals = {}
        for s in SOURCE_ORDER:
            h1 = float(V31_H[s]["L1"])
            h2 = float(V31_H[s]["L2"])
            f_totals[s] = float(leak_for(s, H1_M) / (1024 * (h1 + h2)))
    except Exception:
        f_totals = {}
    return {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "lifecycle_state": lifecycle_state,
        "execution_scope": EXECUTION_SCOPE,
        "fake_runner": fake_runner,
        "mechanism_id": MECHANISM_ID,
        "tag_scope": TAG_SCOPE,
        "tag_source": TAG_SOURCE_STR,
        "tag_bits": 64,
        "sampling_mode": SAMPLING_MODE,
        "provenance": {
            "authorized_target_sha": authorized_target_sha,
            "sha_binding": sha_binding,
            "structural_authority": str(STRUCTURAL_AUTHORITY_PATH),
            "structural_records_strict_match": structural_matrices_count,
            "h1_material": H1_MATRIX_ID + " rank16 QC-cyclic-projective poly37",
            "h1_rank": H1_M,
            "tag_material": TAG_SOURCE_STR,
            "tag_scope": TAG_SCOPE,
            "label_optimization": "deterministic single-run greedy canonical edge order 1..31 up to 2 sweeps, primary lex (deg4,deg6,deg8,cand) deg4-first, custom check_extrinsic_score=ACE-100 if degenerate else ACE secondary only NOT literature NB-ACE",
            "custom_definition": "check_extrinsic_score(C)=ACE(C)-100 if is_deg else ACE(C) where ACE(C)=sum(row_deg-2); custom secondary report NOT literature-standard NB-ACE",
            "deterministic_relabel_id": "single_run_no_seed_search",
        },
        "v25_counts_provenance": counts_provenance,
        "held_out_provenance": {
            "frames": HELDOUT_H,
            "total_frames": sum(HELDOUT_H.values()),
            "total_pairs": sum(HELDOUT_H.values()) * PAIRS_PER_FRAME,
            "block_windows": {str(k): v for k, v in BLOCK_WINDOWS.items()},
            "pairs_per_frame": PAIRS_PER_FRAME,
            "pairs_per_block": PAIRS_PER_BLOCK,
            "sampling_mode": SAMPLING_MODE,
            "held_out_ordinal_windows": {str(k): [v["held_out_ordinal_start"], v["held_out_ordinal_end"]] for k, v in BLOCK_WINDOWS.items()},
            "frame_ids": {str(k): v["frame_ids"] for k, v in BLOCK_WINDOWS.items()},
            "forbidden_156": len(FORBIDDEN_156),
            "forbidden_141": len(FORBIDDEN_141),
        },
        "accounting": {
            "decoder_calls_planned": {"total": PLANNED_CALLS, "l1": PLANNED_L1, "l2": PLANNED_L2},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "l2": accounting.started_l2},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "l2": accounting.completed_l2},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "label_spectrum": spectrum,
        "leakage": {
            "per_source": {
                s: {
                    "m2": SOURCE_M2[s],
                    "l2_syndrome_bits": SOURCE_L2_SYNDROME_BITS[s],
                    "leak_total": leak_for(s, H1_M),
                    "f_total": f_totals.get(s),
                } for s in SOURCE_ORDER
            },
            "H1_16_1064_1094_1104": True,
            "note": "H1-16 1064/1094/1104 (syndrome 920/950/960 +80+64 tag f_total; leakage already accounted; custom check_extrinsic secondary NOT literature NB-ACE)",
            "leakage_already_accounted": True,
            "tag_approx_note": "SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only",
            "tag_scope": TAG_SCOPE,
        },
        "npz_policy": {"forbidden_winner_npz_read": False, "any_npz_output_written": False, "v25_channel_counts_npz_read_only_allowed": True},
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "undetected_anomaly": undetected_anomaly,
        "aggregates": agg,
        "paired_effect": {"table": agg.get("paired_table") if isinstance(agg, dict) else {}, "discordance": agg.get("discordance"), "gain": agg.get("gain_new_minus_old")},
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": ([{"check": cid, "message": msg} for cid, msg in integrity_failures] if integrity_failures else []),
        "performance_interpretation_presented": not invalid,
    }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value

def write_records_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: _csv_value(row[col]) for col in columns})

def write_v51_outputs(output_root: Path | str, records: list[dict[str, Any]], summary: dict[str, Any], spectrum: dict[str, Any]) -> Path:
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)
    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
    dump("v51_records.json", records)
    write_records_csv(root / "v51_records.csv", records, list(RECORD_FIELDS))
    dump("v51_summary.json", summary)
    dump("v51_label_spectrum.json", spectrum)
    return root

def write_invalid_notice(output_root: Path | str, integrity_failures: list[tuple[str, str]], partial_records_retained: bool, terminal_state: str = TERMINAL_EVIDENCE_INVALID) -> Path:
    root = Path(output_root)
    notice = {"cycle_id": CYCLE_ID, "terminal_state": terminal_state, "integrity_failures": [{"check": cid, "message": msg} for cid, msg in integrity_failures], "partial_records_retained_byte_for_byte": partial_records_retained, "performance_interpretation": "none"}
    path = root / "v51_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path

def _persist_invalid_evidence(root: Path, *, records: list[dict[str, Any]], accounting: CallAccounting, summary_ctx: dict[str, Any], failures: list[tuple[str, str]], partial_records_retained: bool, terminal_state: str = TERMINAL_EVIDENCE_INVALID, spectrum: Optional[dict[str, Any]] = None) -> None:
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v51_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v51_records.csv", records, list(RECORD_FIELDS))
        summary = build_v51_summary(
            lifecycle_state="IMPLEMENTATION_CANDIDATE",
            fake_runner=summary_ctx.get("fake_runner", False),
            authorized_target_sha=summary_ctx.get("authorized_target_sha"),
            sha_binding=summary_ctx.get("sha_binding"),
            counts_provenance=summary_ctx.get("counts_provenance", {}),
            accounting=accounting,
            aggregates=None,
            spectrum=spectrum,
            routing_trace=[],
            integrity_failures=failures,
            terminal_state=terminal_state,
            terminal_reason=None,
            structural_matrices_count=int(summary_ctx.get("structural_matrices_count", 0)),
            undetected_anomaly=False,
        )
        with (root / "v51_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        if spectrum is not None:
            with (root / "v51_label_spectrum.json").open("w", encoding="utf-8") as handle:
                json.dump(spectrum, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained, terminal_state=terminal_state)
    except Exception:
        pass

def run_v51_diagnostic(
    execution_authorized: bool = False,
    authorized_target_sha: Optional[str] = None,
    fake_runner: bool = False,
    output_root: Optional[Path | str] = None,
    structural_authority_path: Optional[Path | str] = None,
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    field: Optional[GF2mField] = None,
    check_git: bool = True,
    check_scoped_dirty: bool = True,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    decode_fn: Optional[Callable[..., Any]] = None,
) -> dict[str, Any]:
    if not execution_authorized:
        raise PermissionError(f"EXECUTE_NOT_AUTHORIZED: pass --execution-authorized bound to an explicit user EXECUTE_AUTH for scope {EXECUTION_SCOPE}")
    root_arg = output_root if output_root is not None else OUTPUT_ROOT
    root = Path(root_arg)
    if root.exists():
        raise FileExistsError(f"J7: refusing to overwrite existing output root: {root}")
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("J9", f"polynomial mismatch: {field.primitive_polynomial}")
    sha_binding: Optional[dict[str, str]] = None
    if check_git:
        if not authorized_target_sha:
            raise IntegrityFailure("J1_SHA_BINDING_MISSING", "authorized_target_sha is required for the authorized run")
        sha_binding = verify_execution_sha_binding(REPO_ROOT, authorized_target_sha)
    if check_scoped_dirty:
        verify_scoped_clean(REPO_ROOT)
    summary_ctx: dict[str, Any] = {"fake_runner": fake_runner, "authorized_target_sha": authorized_target_sha, "sha_binding": sha_binding, "counts_provenance": {}, "structural_matrices_count": 0}
    spectrum: Optional[dict[str, Any]] = None
    try:
        ok, msg = validate_seed_registry()
        if not ok:
            raise IntegrityFailure("J2", msg)
        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v51_matrices(reference_metrics_path=spath, field=field, constructors=constructors)
        summary_ctx["structural_matrices_count"] = len(matrices)
        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure("J4", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance
        # spectrum gate
        spectrum = compute_label_spectrum_for_matrices(matrices, field)
        label_improved = bool(spectrum["label_improved"])
        # sentinel preflight
        label_spectrum_preflight(counts, matrices, field)
        # held-out windows validation
        for src in SOURCE_ORDER:
            starts = [BLOCK_WINDOWS[bid]["held_out_ordinal_start"] for bid in NEW_BLOCK_SEEDS[src]]
            if len(starts) != 5:
                raise IntegrityFailure("J4", f"held-out starts for {src} must be 5")
            windows = [(BLOCK_WINDOWS[bid]["held_out_ordinal_start"], BLOCK_WINDOWS[bid]["held_out_ordinal_end"]) for bid in NEW_BLOCK_SEEDS[src]]
            for i in range(len(windows)-1):
                if windows[i][1] >= windows[i+1][0]:
                    raise IntegrityFailure("J4", f"held-out windows overlap for {src}")
        # if label not improved -> blocker terminal without decoder calls
        if not label_improved:
            root.mkdir(parents=True)
            accounting = CallAccounting()
            summary = build_v51_summary(
                lifecycle_state="IMPLEMENTATION_CANDIDATE",
                fake_runner=fake_runner,
                authorized_target_sha=authorized_target_sha,
                sha_binding=sha_binding,
                counts_provenance=counts_provenance,
                accounting=accounting,
                aggregates=None,
                spectrum=spectrum,
                routing_trace=["rule_1_label_not_improved"],
                integrity_failures=None,
                terminal_state=TERMINAL_LABEL_NO_IMPROVEMENT,
                terminal_reason="label_improved false",
                structural_matrices_count=len(matrices),
            )
            with (root / "v51_records.json").open("w", encoding="utf-8") as h:
                json.dump([], h, indent=2)
            write_records_csv(root / "v51_records.csv", [], list(RECORD_FIELDS))
            with (root / "v51_summary.json").open("w", encoding="utf-8") as h:
                json.dump(summary, h, indent=2)
            with (root / "v51_label_spectrum.json").open("w", encoding="utf-8") as h:
                json.dump(spectrum, h, indent=2)
            write_invalid_notice(root, [("LABEL_NO_IMPROVEMENT", "label_improved false")], partial_records_retained=False, terminal_state=TERMINAL_LABEL_NO_IMPROVEMENT)
            return {"output_root": str(root), "terminal_state": TERMINAL_LABEL_NO_IMPROVEMENT, "terminal_reason": "label_improved false", "spectrum": spectrum, "label_improved": False}
    except IntegrityFailure as exc:
        _persist_invalid_evidence(root, records=[], accounting=CallAccounting(), summary_ctx=summary_ctx, failures=[(exc.check_id, exc.message)], partial_records_retained=False, terminal_state=TERMINAL_EVIDENCE_INVALID, spectrum=spectrum)
        return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(exc.check_id, exc.message)]}
    root.mkdir(parents=True)
    all_15_block_ids = [bid for src in SOURCE_ORDER for bid in NEW_BLOCK_SEEDS[src]]
    try:
        heldout_blocks = {block_id: load_heldout_block(block_id) for block_id in all_15_block_ids}
        for block_id in all_15_block_ids:
            win = BLOCK_WINDOWS[block_id]
            src = win["source"]
            tr_lo, tr_hi = TRAIN_FRAME_RANGES[src]
            for fid in win["frame_ids"]:
                if tr_lo <= fid <= tr_hi:
                    raise IntegrityFailure("J4", f"block {block_id} frame {fid} overlaps TRAIN {tr_lo}-{tr_hi}")
        _all_fids = [fid for bid in all_15_block_ids for fid in BLOCK_WINDOWS[bid]["frame_ids"]]
        if len(set(_all_fids)) != 60:
            raise IntegrityFailure("J4", f"held-out preload unique frame_ids {len(set(_all_fids))} != 60")
        _total_pairs = sum(len(v[0]) for v in heldout_blocks.values())
        if _total_pairs != 15360:
            raise IntegrityFailure("J4", f"held-out preload total pairs {_total_pairs} != 15360")
        for src in SOURCE_ORDER:
            v51_src_fids = V51_HELDOUT_FRAME_IDS[src]
            v48_src_fids = V48_HELDOUT_FRAME_IDS[src]
            inter = v51_src_fids & v48_src_fids
            if inter:
                raise IntegrityFailure("J4", f"V51 {src} frame_ids overlap V48 {sorted(inter)}")
            v50_src_fids = V50_HELDOUT_FRAME_IDS[src]
            inter2 = v51_src_fids & v50_src_fids
            if inter2:
                raise IntegrityFailure("J4", f"V51 {src} frame_ids overlap V50 {sorted(inter2)}")
        if len(V48_HELDOUT_FRAME_IDS_FLAT) != 180:
            raise IntegrityFailure("J4", f"V48 authoritative frame_ids size {len(V48_HELDOUT_FRAME_IDS_FLAT)} !=180")
    except IntegrityFailure as preload_exc:
        _persist_invalid_evidence(root, records=[], accounting=CallAccounting(), summary_ctx=summary_ctx, failures=[(preload_exc.check_id, preload_exc.message)], partial_records_retained=False, spectrum=spectrum)
        return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(preload_exc.check_id, preload_exc.message)]}
    accounting = CallAccounting()
    records: list[dict[str, Any]] = []
    try:
        try:
            _run_workload_calls(matrices, counts, field, fake_runner, DECODER_SETTING, accounting, records, decode_fn=decode_fn, heldout_blocks=heldout_blocks)
        except IntegrityFailure as wf_exc:
            if accounting.started == 0 and accounting.completed == 0:
                _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[(wf_exc.check_id, wf_exc.message)], partial_records_retained=False, spectrum=spectrum)
                return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(wf_exc.check_id, wf_exc.message)]}
            raise
        failures = validate_post_evaluation(records) + accounting.validate_executed()
        if failures:
            _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=failures, partial_records_retained=True, spectrum=spectrum)
            return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": failures}
        aggregates = aggregate_results(records, spectrum)
        undetected_anomaly = bool(aggregates["undetected_total"] > 0)
        terminal_state, terminal_reason, routing_trace = determine_v51_terminal(True, bool(spectrum["label_improved"]) if spectrum else None)
        summary = build_v51_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=fake_runner,
            authorized_target_sha=authorized_target_sha,
            sha_binding=sha_binding,
            counts_provenance=summary_ctx["counts_provenance"],
            accounting=accounting,
            aggregates=aggregates,
            spectrum=spectrum,
            routing_trace=routing_trace,
            integrity_failures=None,
            terminal_state=terminal_state,
            terminal_reason=terminal_reason,
            structural_matrices_count=len(matrices),
            undetected_anomaly=undetected_anomaly,
        )
        write_v51_outputs(root, records, summary, spectrum)
        return {"output_root": str(root), "terminal_state": terminal_state, "terminal_reason": terminal_reason, "routing_trace": routing_trace, "decoder_calls_completed": accounting.completed, "aggregates": aggregates, "summary": summary, "spectrum": spectrum, "label_improved": bool(spectrum["label_improved"]) if spectrum else None}
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")], partial_records_retained=True, spectrum=spectrum)
        raise

# compat
run_v51_lane_c_label_nbace_diagnostic = run_v51_diagnostic
