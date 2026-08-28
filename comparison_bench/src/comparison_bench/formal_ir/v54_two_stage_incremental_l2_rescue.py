"""V54P0 two-stage incremental L2 rescue Δ8+8 nested HARQ conditional 45 blocks.

Frozen V52/V53 complete method (H1-16 + syndrome-derived L1-APP via BP_i + Lane C ordinal-2 support/label/position_permutations + m2 184/190/192 + H_inc1 8×1024 det1 + H_joint1 192/198/200 + decoder 90/1.0 poly37 + L2-only tag + TRAIN-only prior + verification-only) plus second increment H_inc2 8×1024 det2 second stage.

Budget 45 L1 +45 base +≤45 stage1 +≤45 stage2 =90-180 hard cap 180 (L2 45-135). Leakage base 1064/1094/1104 stage1 +40 stage2 +80. Verification-only base→stage1→stage2; exact only oracle. Per-block L1 q reused.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
Accepted plan SHA: bf5dd1686049156540328bac264296b17fee546c
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

CYCLE_ID = "V54P0"
CHANGE_ID = "formal-ir-v54-two-stage-incremental-l2-rescue"
ACCEPTED_PLAN_SHA = "bf5dd1686049156540328bac264296b17fee546c"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v54_two_stage_rescue_45_blocks_triple_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
MECHANISM_ID = "nested_two_stage_incremental_l2_rescue_delta8_plus8_45blocks_v54"
TAG_SCOPE = "l2_only"
TAG_SOURCE_STR = "v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only"
LEAKAGE_ALREADY_ACCOUNTED_NOTE = "leakage already accounted: H1-16 1064/1094/1104 base 1104/1134/1144 stage1 1144/1174/1184 stage2 includes 64-bit tag; SHA-trunc64 random-hash-model approximate 2^-64 L2-only"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

DELTA_M = 8
DELTA_M_TOTAL = 16
PLANNED_L1 = 45
PLANNED_L2_BASE = 45
PLANNED_L2_STAGE1_MAX = 45
PLANNED_L2_STAGE2_MAX = 45
PLANNED_L2_MAX = 135
HARD_CALL_CAP = 180

H1_M = 16
H1_N = 1024
H1_MATRIX_ID = "V31-H1-QC-16×1024"
H1_FAMILY = "QC-cyclic-projective"

PAIRS_PER_FRAME = 256
FRAMES_PER_BLOCK = 4
PAIRS_PER_BLOCK = 1024
BLOCK_LENGTH_CONST = 1024

INC1_DET_IDS: dict[str, int] = {"1M": 600001, "1p5M": 600002, "2M": 600003}
INC2_DET_IDS: dict[str, int] = {"1M": 600004, "1p5M": 600005, "2M": 600006}

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

SAMPLING_MODE = "deterministic_four_consecutive_frames_heldout_fresh_v54"

NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [395001,395002,395003,395004,395005,395006,395007,395008,395009,395010,395011,395012,395013,395014,395015],
    "1p5M": [395101,395102,395103,395104,395105,395106,395107,395108,395109,395110,395111,395112,395113,395114,395115],
    "2M": [395201,395202,395203,395204,395205,395206,395207,395208,395209,395210,395211,395212,395213,395214,395215],
}

# Frozen 45 windows — dispersed selection avoiding frozen V53 394xxx (K2 128/268/456)
_V54_WINDOW_DEFS = [
    ("1M", 395001, 18, 21, [1618,1619,1620,1621]),
    ("1M", 395002, 48, 51, [1648,1649,1650,1651]),
    ("1M", 395003, 105, 108, [1705,1706,1707,1708]),
    ("1M", 395004, 160, 163, [1760,1761,1762,1763]),
    ("1M", 395005, 183, 186, [1783,1784,1785,1786]),
    ("1M", 395006, 204, 207, [1804,1805,1806,1807]),
    ("1M", 395007, 220, 223, [1820,1821,1822,1823]),
    ("1M", 395008, 243, 246, [1843,1844,1845,1846]),
    ("1M", 395009, 264, 267, [1864,1865,1866,1867]),
    ("1M", 395010, 287, 290, [1887,1888,1889,1890]),
    ("1M", 395011, 303, 306, [1903,1904,1905,1906]),
    ("1M", 395012, 326, 329, [1926,1927,1928,1929]),
    ("1M", 395013, 348, 351, [1948,1949,1950,1951]),
    ("1M", 395014, 371, 374, [1971,1972,1973,1974]),
    ("1M", 395015, 388, 391, [1988,1989,1990,1991]),
    ("1p5M", 395101, 4, 7, [2217,2218,2219,2220]),
    ("1p5M", 395102, 67, 70, [2280,2281,2282,2283]),
    ("1p5M", 395103, 144, 147, [2357,2358,2359,2360]),
    ("1p5M", 395104, 211, 214, [2424,2425,2426,2427]),
    ("1p5M", 395105, 242, 245, [2455,2456,2457,2458]),
    ("1p5M", 395106, 268, 271, [2481,2482,2483,2484]),
    ("1p5M", 395107, 301, 304, [2514,2515,2516,2517]),
    ("1p5M", 395108, 334, 337, [2547,2548,2549,2550]),
    ("1p5M", 395109, 367, 370, [2580,2581,2582,2583]),
    ("1p5M", 395110, 397, 400, [2610,2611,2612,2613]),
    ("1p5M", 395111, 416, 419, [2629,2630,2631,2632]),
    ("1p5M", 395112, 449, 452, [2662,2663,2664,2665]),
    ("1p5M", 395113, 482, 485, [2695,2696,2697,2698]),
    ("1p5M", 395114, 515, 518, [2728,2729,2730,2731]),
    ("1p5M", 395115, 542, 545, [2755,2756,2757,2758]),
    ("2M", 395201, 4, 7, [2920,2921,2922,2923]),
    ("2M", 395202, 66, 69, [2982,2983,2984,2985]),
    ("2M", 395203, 142, 145, [3058,3059,3060,3061]),
    ("2M", 395204, 202, 205, [3118,3119,3120,3121]),
    ("2M", 395205, 269, 272, [3185,3186,3187,3188]),
    ("2M", 395206, 315, 318, [3231,3232,3233,3234]),
    ("2M", 395207, 355, 358, [3271,3272,3273,3274]),
    ("2M", 395208, 401, 404, [3317,3318,3319,3320]),
    ("2M", 395209, 445, 448, [3361,3362,3363,3364]),
    ("2M", 395210, 491, 494, [3407,3408,3409,3410]),
    ("2M", 395211, 538, 541, [3454,3455,3456,3457]),
    ("2M", 395212, 584, 587, [3500,3501,3502,3503]),
    ("2M", 395213, 631, 634, [3547,3548,3549,3550]),
    ("2M", 395214, 677, 680, [3593,3594,3595,3596]),
    ("2M", 395215, 717, 720, [3633,3634,3635,3636]),
]
BLOCK_WINDOWS: dict[int, dict[str, Any]] = {}
BLOCK_TO_SOURCE: dict[int, str] = {}
for _src, _bid, _s, _e, _fids in _V54_WINDOW_DEFS:
    BLOCK_WINDOWS[_bid] = {
        "source": _src,
        "held_out_ordinal_start": _s,
        "held_out_ordinal_end": _e,
        "frame_ids": _fids,
        "pairs_count": PAIRS_PER_BLOCK,
        "sampling_mode": SAMPLING_MODE,
    }
    BLOCK_TO_SOURCE[_bid] = _src

# Forbidden registries (copied from V53)
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
V52_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [393001,393002,393003,393004,393005],
    "1p5M": [393101,393102,393103,393104,393105],
    "2M": [393201,393202,393203,393204,393205],
}
V53_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [394001,394002,394003,394004,394005,394006,394007,394008,394009,394010,394011,394012,394013,394014,394015],
    "1p5M": [394101,394102,394103,394104,394105,394106,394107,394108,394109,394110,394111,394112,394113,394114,394115],
    "2M": [394201,394202,394203,394204,394205,394206,394207,394208,394209,394210,394211,394212,394213,394214,394215],
}
V48_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1600,1601,1602,1603,1628,1629,1630,1631,1656,1657,1658,1659,1684,1685,1686,1687,1713,1714,1715,1716,1741,1742,1743,1744,1769,1770,1771,1772,1798,1799,1800,1801,1826,1827,1828,1829,1854,1855,1856,1857,1882,1883,1884,1885,1911,1912,1913,1914,1939,1940,1941,1942,1967,1968,1969,1970,1996,1997,1998,1999]),
    "1p5M": frozenset([2213,2214,2215,2216,2252,2253,2254,2255,2291,2292,2293,2294,2330,2331,2332,2333,2370,2371,2372,2373,2409,2410,2411,2412,2448,2449,2450,2451,2488,2489,2490,2491,2527,2528,2529,2530,2566,2567,2568,2569,2605,2606,2607,2608,2645,2646,2647,2648,2684,2685,2686,2687,2723,2724,2725,2726,2763,2764,2765,2766]),
    "2M": frozenset([2916,2917,2918,2919,2967,2968,2969,2970,3019,3020,3021,3022,3071,3072,3073,3074,3123,3124,3125,3126,3174,3175,3176,3177,3226,3227,3228,3229,3278,3279,3280,3281,3330,3331,3332,3333,3382,3383,3384,3385,3433,3434,3435,3436,3485,3486,3487,3488,3537,3538,3539,3540,3589,3590,3591,3592,3641,3642,3643,3644]),
}
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
    "1M": frozenset([1633,1634,1635,1636,1661,1662,1663,1664,1689,1690,1691,1692,1717,1718,1719,1720,1746,1747,1748,1749]),
    "1p5M": frozenset([2257,2258,2259,2260,2296,2297,2298,2299,2335,2336,2337,2338,2375,2376,2377,2378,2414,2415,2416,2417]),
    "2M": frozenset([2969,2970,2971,2972,3020,3021,3022,3023,3071,3072,3073,3074,3122,3123,3124,3125,3173,3174,3175,3176]),
}
V53_HELDOUT_FRAME_IDS: dict[str, frozenset[int]] = {
    "1M": frozenset([1678,1679,1680,1681,1734,1735,1736,1737,1756,1757,1758,1759,1778,1779,1780,1781,1793,1794,1795,1796,1815,1816,1817,1818,1837,1838,1839,1840,1859,1860,1861,1862,1874,1875,1876,1877,1896,1897,1898,1899,1918,1919,1920,1921,1933,1934,1935,1936,1955,1956,1957,1958,1977,1978,1979,1980,1992,1993,1994,1995]),
    "1p5M": frozenset([2248,2249,2250,2251,2316,2317,2318,2319,2363,2364,2365,2366,2417,2418,2419,2420,2443,2444,2445,2446,2476,2477,2478,2479,2509,2510,2511,2512,2542,2543,2544,2545,2575,2576,2577,2578,2601,2602,2603,2604,2634,2635,2636,2637,2667,2668,2669,2670,2700,2701,2702,2703,2733,2734,2735,2736,2759,2760,2761,2762]),
    "2M": frozenset([2953,2954,2955,2956,3012,3013,3014,3015,3078,3079,3080,3081,3152,3153,3154,3155,3197,3198,3199,3200,3242,3243,3244,3245,3288,3289,3290,3291,3326,3327,3328,3329,3371,3372,3373,3374,3417,3418,3419,3420,3462,3463,3464,3465,3507,3508,3509,3510,3553,3554,3555,3556,3598,3599,3600,3601,3637,3638,3639,3640]),
}

FORBIDDEN_78: frozenset[int] = frozenset(seed for seeds in (*V36_A3_SEEDS_COPIED.values(), *V39_SEEDS_COPIED.values(), *V40_PROBE_SEEDS_COPIED.values(), *V41_SEEDS_COPIED.values(), *V42_SEEDS_COPIED.values(), *V43_SEEDS_COPIED.values(), *V44_SEEDS_COPIED.values(), *V45_SEEDS_COPIED.values()) for seed in (seeds if isinstance(seeds, list) else [seeds]))
FORBIDDEN_87: frozenset[int] = frozenset(set(FORBIDDEN_78) | {s for lst in V46_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_96: frozenset[int] = frozenset(set(FORBIDDEN_87) | {s for lst in V47_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_141: frozenset[int] = frozenset(set(FORBIDDEN_96) | {s for lst in V48_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_156: frozenset[int] = frozenset(set(FORBIDDEN_141) | {s for lst in V50_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_171: frozenset[int] = frozenset(set(FORBIDDEN_156) | {s for lst in V51_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_186: frozenset[int] = frozenset(set(FORBIDDEN_171) | {s for lst in V52_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_231: frozenset[int] = frozenset(set(FORBIDDEN_186) | {s for lst in V53_SEEDS_COPIED.values() for s in lst})
FORBIDDEN_BLOCK_SEEDS = FORBIDDEN_231

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
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v54_two_stage_incremental_l2_rescue/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v54_two_stage_incremental_l2_rescue.py",
    "scripts/execute_v54_two_stage_rescue.py",
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

def leak_stage1_for(source: str) -> int:
    return leak_for(source) + 40

def leak_stage2_for(source: str) -> int:
    return leak_for(source) + 80

def avg_leak_per_source(n_stage1: int, n_stage2: int, source: str) -> float:
    return float(leak_for(source) + 40 * n_stage1 / 15 + 40 * n_stage2 / 15)

MASTER_STOP_RULE = (
    "每块 L1 1+base L2 1+条件 stage1 ≤1+条件 stage2 ≤1；总 45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180 L2 45-135。"
)

TERMINAL_EVIDENCE_INVALID = "V54_EVIDENCE_INVALID"
TERMINAL_DELTA8_ALREADY_SUFFICIENT = "V54_DELTA8_ALREADY_SUFFICIENT"
TERMINAL_DELTA16_ADDED_VALUE_SIGNAL = "V54_DELTA16_ADDED_VALUE_SIGNAL"
TERMINAL_DELTA16_INSUFFICIENT = "V54_DELTA16_INSUFFICIENT"
TERMINAL_EVIDENCE_INVALID_INTERRUPTED = "V54_EVIDENCE_INVALID_INTERRUPTED"
ALL_TERMINALS = frozenset({TERMINAL_EVIDENCE_INVALID, TERMINAL_DELTA8_ALREADY_SUFFICIENT, TERMINAL_DELTA16_ADDED_VALUE_SIGNAL, TERMINAL_DELTA16_INSUFFICIENT, TERMINAL_EVIDENCE_INVALID_INTERRUPTED})

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "source",
    "block_seed",
    "arm",
    "pass_index",
    "used_inc1",
    "used_inc2",
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
    "leak_stage1",
    "leak_stage2",
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "h1_rows", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn", "arm", "pass_index"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY nested two-stage incremental L2 rescue Δ8+8 on frozen Lane C support/prior/MET n=1024 m2 184/190/192 GF32 poly37 decoder 90/1.0 leak 1064/1094/1104 base 1104/1134/1144 stage1 1144/1174/1184 stage2 conditional only rescue frames +40 each stage avg per_source[s]=leak_base[s]+40*N1[s]/15+40*N2[s]/15 overall=(Σ base+40*N1+40*N2)/45",
    "leakage H1-16 includes 64-bit tag L2-only random-hash-model approximate 2^-64 row≤16 col_inc≤1 deterministic no seed search nested rank m2+8 m2+16",
    "not threshold/SKR/formal qualification/promotion; paired descriptive only Δexact_stage1 Δexact_stage2 McNemar descriptive four-way G3' undetected==0 45 blocks development confirmation",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is 45 blocks three-stage conditional base vs stage1 vs final (45 L1 +45 base +≤45 stage1 +≤45 stage2 =90-180 L2 45-135). "
    "Exact-recovery proportions with n and raw counts; any interval naive uncorrected clustering; no significance."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# L1 prior helpers (same as V53)
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
# H_inc construction deterministic PEG-like (det1 and det2)
# ---------------------------------------------------------------------------

def construct_h_inc(source: str, det_id: Optional[int] = None, delta_m: int = DELTA_M, n: int = BLOCK_LENGTH) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
    if det_id is None:
        det_id = INC1_DET_IDS[source]
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


def construct_h_joint1(source: str, H_base: np.ndarray, det_id: Optional[int] = None) -> tuple[np.ndarray, dict[str, Any]]:
    H_inc, Hs_inc, E_inc, row_deg_inc = construct_h_inc(source, det_id or INC1_DET_IDS[source])
    H_joint = np.vstack([H_base, H_inc]).astype(np.uint8)
    return H_joint, {"H_inc": H_inc, "Hs_inc": Hs_inc, "E_inc": E_inc, "row_deg_inc": row_deg_inc}


def construct_h_total(source: str, H_base: np.ndarray, det1: Optional[int] = None, det2: Optional[int] = None) -> tuple[np.ndarray, dict[str, Any]]:
    H_inc1, _, _, _ = construct_h_inc(source, det1 or INC1_DET_IDS[source])
    H_inc2, Hs_inc2, E_inc2, row_deg2 = construct_h_inc(source, det2 or INC2_DET_IDS[source])
    H_total = np.vstack([H_base, H_inc1, H_inc2]).astype(np.uint8)
    return H_total, {"H_inc1": H_inc1, "H_inc2": H_inc2, "Hs_inc2": Hs_inc2, "E_inc2": E_inc2, "row_deg2": row_deg2}


# ---------------------------------------------------------------------------
# Seed-registry validator (J2)
# ---------------------------------------------------------------------------

def validate_seed_registry(seeds: Optional[dict[str, list[int]]] = None) -> tuple[bool, str]:
    reg = NEW_BLOCK_SEEDS if seeds is None else seeds
    if set(reg.keys()) != set(SOURCE_ORDER):
        return False, f"registry sources must be exactly {SOURCE_ORDER}"
    all_seeds = [seed for source in SOURCE_ORDER for seed in reg[source]]
    if len(all_seeds) != 45:
        return False, f"registry must contain exactly 45 seeds, got {len(all_seeds)}"
    if any(len(reg[source]) != 15 for source in SOURCE_ORDER):
        return False, f"registry must hold exactly 15 seeds per source: {dict(reg)}"
    duplicates = sorted({s for s in all_seeds if all_seeds.count(s) > 1})
    if duplicates:
        return False, f"duplicate seeds among the 45: {duplicates}"
    overlap = set(all_seeds) & FORBIDDEN_231
    if overlap:
        return False, f"new seeds overlap forbidden 231 registries: {sorted(overlap)}"
    # check overlap with prior block IDs already covered by FORBIDDEN but keep
    expected = NEW_BLOCK_SEEDS
    flat_expected = {s for lst in expected.values() for s in lst}
    flat_actual = set(all_seeds)
    if seeds is None and flat_actual != flat_expected:
        return False, "new seeds must be exactly frozen 395001-015/101-115/201-215"
    for src in SOURCE_ORDER:
        seeds_sorted = sorted(reg[src])
        if seeds_sorted != reg[src]:
            return False, f"seeds for {src} must be sorted ascending"
    # per-source frame_ids zero overlap with prior held-out
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
            if fids & V52_HELDOUT_FRAME_IDS[src]:
                return False, f"block {bid} frame_ids overlap V52 for {src}"
            if fids & V53_HELDOUT_FRAME_IDS[src]:
                return False, f"block {bid} frame_ids overlap V53 for {src}"
    # also check final 45 intervals pairwise non-overlap (gap≥4) — ordinal windows within source already guaranteed but also cross-check
    for src in SOURCE_ORDER:
        windows = [(BLOCK_WINDOWS[bid]["held_out_ordinal_start"], BLOCK_WINDOWS[bid]["held_out_ordinal_end"]) for bid in reg[src]]
        for i in range(len(windows)):
            for j in range(i+1, len(windows)):
                if not (windows[i][1] < windows[j][0] - 3 and windows[j][1] < windows[i][0] - 3 or abs(windows[i][0]-windows[j][0])>3):
                    # simpler: intervals [s,s+3] overlap if abs diff <=3
                    if abs(windows[i][0]-windows[j][0]) <=3:
                        return False, f"block intervals overlap within {src}: {windows[i]} vs {windows[j]}"
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
        raise IntegrityFailure("J4", f"block_seed {block_seed} not in frozen 45")
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
# Structural reconstruction (J3) — Lane C base + H_inc1 + H_inc2
# ---------------------------------------------------------------------------

def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")

def reconstruct_v54_matrices(
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
        # H_inc1
        H_inc1, Hs_inc1, E_inc1, row_deg1 = construct_h_inc(source, INC1_DET_IDS[source])
        if H_inc1.shape != (DELTA_M, BLOCK_LENGTH):
            raise IntegrityFailure("J3", f"H_inc1 shape {H_inc1.shape} != {(DELTA_M, BLOCK_LENGTH)}")
        if int(row_deg1.max()) > MAX_CHECK_DEGREE_LIMIT:
            raise IntegrityFailure("J3", f"H_inc1 row_max {int(row_deg1.max())} >16")
        if int(np.count_nonzero(Hs_inc1, axis=0).max()) > 1:
            raise IntegrityFailure("J3", "H_inc1 col_degree >1")
        H_joint1 = np.vstack([matrix, H_inc1]).astype(np.uint8)
        rank_base = int(compute_gf32_rank(matrix, field))
        rank_joint1 = int(compute_gf32_rank(H_joint1, field))
        if rank_base != SOURCE_CHECKS[source]:
            raise IntegrityFailure("J3", f"base rank {rank_base} != m2 {SOURCE_CHECKS[source]}")
        if rank_joint1 != SOURCE_CHECKS[source] + DELTA_M:
            raise IntegrityFailure("J3", f"joint1 rank {rank_joint1} != m2+8 {SOURCE_CHECKS[source]+DELTA_M}")
        if not np.array_equal(H_joint1[0:SOURCE_CHECKS[source], :], matrix):
            raise IntegrityFailure("J3", f"nested1 failed for {source}")
        if rank_joint1 - rank_base != DELTA_M:
            raise IntegrityFailure("J3", f"independence1 {rank_joint1 - rank_base} !=8")
        # H_inc2 second stage
        H_inc2, Hs_inc2, E_inc2, row_deg2 = construct_h_inc(source, INC2_DET_IDS[source])
        if H_inc2.shape != (DELTA_M, BLOCK_LENGTH):
            raise IntegrityFailure("J3", f"H_inc2 shape {H_inc2.shape} != {(DELTA_M, BLOCK_LENGTH)}")
        if int(row_deg2.max()) > MAX_CHECK_DEGREE_LIMIT:
            raise IntegrityFailure("J3", f"H_inc2 row_max {int(row_deg2.max())} >16")
        if int(np.count_nonzero(Hs_inc2, axis=0).max()) > 1:
            raise IntegrityFailure("J3", "H_inc2 col_degree >1")
        H_total = np.vstack([matrix, H_inc1, H_inc2]).astype(np.uint8)
        rank_total = int(compute_gf32_rank(H_total, field))
        if rank_total != SOURCE_CHECKS[source] + DELTA_M_TOTAL:
            raise IntegrityFailure("J3", f"total rank {rank_total} != m2+16 {SOURCE_CHECKS[source]+DELTA_M_TOTAL}")
        if not np.array_equal(H_total[0:SOURCE_CHECKS[source], :], matrix):
            raise IntegrityFailure("J3", f"nested_total_base failed for {source}")
        if not np.array_equal(H_total[0:SOURCE_CHECKS[source]+DELTA_M, :], H_joint1):
            raise IntegrityFailure("J3", f"nested_total_joint1 failed for {source}")
        if rank_total - rank_joint1 != DELTA_M:
            raise IntegrityFailure("J3", f"independence2 {rank_total - rank_joint1} !=8")
        # leak
        lb = leak_for(source)
        l1 = leak_stage1_for(source)
        l2 = leak_stage2_for(source)
        if l1 - lb != 40 or l2 - l1 != 40 or l2 - lb != 80:
            raise IntegrityFailure("J3", "leak +40+40 failed")
        col_inc1_max = int(np.count_nonzero(Hs_inc1, axis=0).max())
        col_inc2_max = int(np.count_nonzero(Hs_inc2, axis=0).max())
        matrices[("h_inc1", source)] = (H_inc1, {"E_inc": int(E_inc1), "row_deg": row_deg1.tolist(), "col_max": col_inc1_max, "row_max": int(row_deg1.max())})
        matrices[("h_inc2", source)] = (H_inc2, {"E_inc": int(E_inc2), "row_deg": row_deg2.tolist(), "col_max": col_inc2_max, "row_max": int(row_deg2.max())})
        matrices[("h_joint1", source)] = (H_joint1, {"rank_joint1": rank_joint1, "rank_base": rank_base, "nested": True, "independence": DELTA_M, "E_inc": int(E_inc1)})
        matrices[("h_total", source)] = (H_total, {"rank_total": rank_total, "rank_joint1": rank_joint1, "rank_base": rank_base, "nested_stage1": True, "nested_stage2": True, "independence1": DELTA_M, "independence2": DELTA_M, "E_inc1": int(E_inc1), "E_inc2": int(E_inc2)})
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

# alias for preflight compat
reconstruct_v53_matrices = reconstruct_v54_matrices

def v54_nested_preflight(
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, Any]:
    field = field or GF2mField.create(DIMENSION)
    if matrices is None:
        matrices = reconstruct_v54_matrices(field=field)
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
        H_joint1 = matrices[("h_joint1", src)][0]
        H_total = matrices[("h_total", src)][0]
        m2 = SOURCE_CHECKS[src]
        assert H_base.shape == (m2, BLOCK_LENGTH)
        assert H_joint1.shape == (m2+DELTA_M, BLOCK_LENGTH)
        assert H_total.shape == (m2+DELTA_M_TOTAL, BLOCK_LENGTH)
        rank_base = int(compute_gf32_rank(H_base, field))
        rank_joint1 = int(compute_gf32_rank(H_joint1, field))
        rank_total = int(compute_gf32_rank(H_total, field))
        nested1 = bool(np.array_equal(H_joint1[0:m2, :], H_base))
        nested2a = bool(np.array_equal(H_total[0:m2, :], H_base))
        nested2b = bool(np.array_equal(H_total[0:m2+DELTA_M, :], H_joint1))
        lb = leak_for(src)
        l1 = leak_stage1_for(src)
        l2 = leak_stage2_for(src)
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
            "rank_base": rank_base, "rank_joint1": rank_joint1, "rank_total": rank_total,
            "nested1": nested1, "nested_total_base": nested2a, "nested_total_joint1": nested2b,
            "independence1": rank_joint1 - rank_base, "independence2": rank_total - rank_joint1,
            "leak_base": lb, "leak_stage1": l1, "leak_stage2": l2, "delta1": l1-lb, "delta2": l2-l1,
            "h_base_ok": rank_base == m2,
            "h_inc1_nested_ok": nested1,
            "h_inc2_nested_ok": nested2a and nested2b,
            "joint1_rank_ok": rank_joint1 == m2+DELTA_M,
            "total_rank_ok": rank_total == m2+DELTA_M_TOTAL,
            "independence_1_ok": (rank_joint1 - rank_base)==DELTA_M,
            "independence_2_ok": (rank_total - rank_joint1)==DELTA_M,
            "leakage_accounted": (l1-lb)==40 and (l2-l1)==40,
            "tag_import_ok": tag_ok,
            "tag_scope_l2_only": TAG_SCOPE=="l2_only",
        }
        if not (per_source[src]["h_base_ok"] and per_source[src]["joint1_rank_ok"] and per_source[src]["total_rank_ok"] and per_source[src]["independence_1_ok"] and per_source[src]["independence_2_ok"] and nested1 and nested2a and nested2b and tag_ok):
            raise IntegrityFailure("J5", f"preflight failed for {src}: {per_source[src]}")
        bseed = {"1M":395001,"1p5M":395101,"2M":395201}[src]
        win = BLOCK_WINDOWS.get(bseed)
        if win is None or win["pairs_count"] !=1024 or len(win["frame_ids"])!=4 or win["sampling_mode"]!=SAMPLING_MODE:
            raise IntegrityFailure("J4", f"heldout not reachable for {src}/{bseed}")
    return {"per_source": per_source, "nested_ok": True, "leak_plus40_ok": True}

# aliases
nested_rescue_preflight = v54_nested_preflight
single_arm_binding_preflight = v54_nested_preflight
triple_arm_binding_preflight = v54_nested_preflight

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
# Budget accounting J10 hard cap 180
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
        self.started_stage1 = 0
        self.completed_stage1 = 0
        self.started_stage2 = 0
        self.completed_stage2 = 0

    def register_start(self, layer: str = "total") -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        if layer == "l1" and self.started_l1 >= PLANNED_L1:
            raise IntegrityFailure("J10", "l1 cap 45 reached")
        if layer == "l2" and self.started_l2 >= PLANNED_L2_MAX:
            raise IntegrityFailure("J10", "l2 cap 135 reached")
        if layer == "base" and self.started_base >= PLANNED_L2_BASE:
            raise IntegrityFailure("J10", "base cap 45 reached")
        if layer == "stage1" and self.started_stage1 >= PLANNED_L2_STAGE1_MAX:
            raise IntegrityFailure("J10", "stage1 cap 45 reached")
        if layer == "stage2" and self.started_stage2 >= PLANNED_L2_STAGE2_MAX:
            raise IntegrityFailure("J10", "stage2 cap 45 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
            self.started_l2 += 0
        elif layer == "l2":
            self.started_l2 += 1
        elif layer == "base":
            self.started_base += 1
            self.started_l2 += 1
        elif layer == "stage1":
            self.started_stage1 += 1
            self.started_l2 += 1
        elif layer == "stage2":
            self.started_stage2 += 1
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
        elif layer == "stage1":
            self.completed_stage1 += 1
            self.completed_l2 += 1
        elif layer == "stage2":
            self.completed_stage2 += 1
            self.completed_l2 += 1

    def validate_executed(self) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        if self.completed > self.hard_cap:
            failures.append(("J10", f"completed {self.completed} exceeds hard cap {self.hard_cap}"))
        if self.completed != self.started:
            failures.append(("J10", f"started {self.started} != completed {self.completed}"))
        if self.completed_l1 != self.started_l1 or self.completed_l2 != self.started_l2:
            failures.append(("J10", f"l1/l2 mismatch"))
        if self.completed_l1 > PLANNED_L1 or self.completed_base > PLANNED_L2_BASE or self.completed_stage1 > PLANNED_L2_STAGE1_MAX or self.completed_stage2 > PLANNED_L2_STAGE2_MAX:
            failures.append(("J10", "per-layer overflow"))
        if self.completed < 90 or self.completed > 180:
            failures.append(("J10", f"total {self.completed} not in 90-180"))
        if self.completed_l2 < 45 or self.completed_l2 > 135:
            failures.append(("J10", f"l2 {self.completed_l2} not in 45-135"))
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
        "arm": raw.get("arm", spec.get("arm","base")),
        "pass_index": int(raw.get("pass_index", spec.get("pass_index",1))),
        "used_inc1": bool(raw.get("used_inc1", False)),
        "used_inc2": bool(raw.get("used_inc2", False)),
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
        "leak_stage1": int(raw.get("leak_stage1", leak_stage1_for(raw["source"]))),
        "leak_stage2": int(raw.get("leak_stage2", leak_stage2_for(raw["source"]))),
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
    if record["arm"] not in ("base","stage1","stage2"):
        return False, f"invalid arm {record['arm']!r}"
    if record["arm"]=="base" and record["pass_index"]!=1:
        return False, "base must be pass 1"
    if record["arm"]=="stage1" and record["pass_index"]!=2:
        return False, "stage1 must be pass 2"
    if record["arm"]=="stage2" and record["pass_index"]!=3:
        return False, "stage2 must be pass 3"
    if record["used_inc1"] != (record["arm"] in ("stage1","stage2")):
        return False, "used_inc1 must be true for stage1/stage2"
    if record["used_inc2"] != (record["arm"]=="stage2"):
        return False, "used_inc2 must be true only for stage2"
    if record["joint"] != (record["arm"] in ("stage1","stage2")):
        return False, "joint must be true for stage1/stage2"
    if record["sampling_mode"] != SAMPLING_MODE:
        return False, f"sampling_mode must be {SAMPLING_MODE}"
    if record["pairs_count"] != PAIRS_PER_BLOCK:
        return False, f"pairs_count must be {PAIRS_PER_BLOCK}"
    # leak checks
    src = record["source"]
    if record["leak_total"] not in (leak_for(src), leak_stage1_for(src), leak_stage2_for(src)):
        return False, f"leak_total {record['leak_total']} not in valid set for {src}"
    if record["arm"]=="base" and record["leak_total"] != leak_for(src):
        return False, f"base leak {record['leak_total']} != {leak_for(src)}"
    if record["arm"]=="stage1" and record["leak_total"] != leak_stage1_for(src):
        return False, f"stage1 leak {record['leak_total']} != {leak_stage1_for(src)}"
    if record["arm"]=="stage2" and record["leak_total"] != leak_stage2_for(src):
        return False, f"stage2 leak {record['leak_total']} != {leak_stage2_for(src)}"
    if record["leak_stage1"] != leak_stage1_for(src):
        return False, "leak_stage1 mismatch"
    if record["leak_stage2"] != leak_stage2_for(src):
        return False, "leak_stage2 mismatch"
    if not isinstance(record["frame_ids"], list) or len(record["frame_ids"]) != 4:
        return False, "frame_ids must be list of 4"
    win = BLOCK_WINDOWS.get(record["block_seed"])
    if win is None:
        return False, f"block_seed {record['block_seed']} not in frozen 45"
    if record["frame_ids"] != win["frame_ids"]:
        return False, f"frame_ids mismatch expected {win['frame_ids']}"
    if record["held_out_ordinal_start"] != win["held_out_ordinal_start"] or record["held_out_ordinal_end"] != win["held_out_ordinal_end"]:
        return False, "held_out ordinal mismatch"
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
# Guards
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
    if fake_runner or decode_fn is not None:
        if decode_fn is not None:
            res = decode_fn(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, spec)
            if isinstance(res, dict):
                return res
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
            "leak_stage1": int(leak_stage1_for(source)), "leak_stage2": int(leak_stage2_for(source)),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
            "arm": spec.get("arm","base"), "pass_index": int(spec.get("pass_index",1)), "used_inc1": bool(spec.get("used_inc1",False)), "used_inc2": bool(spec.get("used_inc2",False)), "joint": bool(spec.get("joint",False)),
        }
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa as _dec
    syn = syndrome_of_gf32(matrix, u2_alice, field)
    if q is None:
        prior = np.full((1024,32), 1/32)
    else:
        prior = q
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
        "leak_stage1": int(leak_stage1_for(source)), "leak_stage2": int(leak_stage2_for(source)),
        "status": str(res.status), "runtime_s": float(res.runtime_s),
        "arm": spec.get("arm","base"), "pass_index": int(spec.get("pass_index",1)), "used_inc1": bool(spec.get("used_inc1",False)), "used_inc2": bool(spec.get("used_inc2",False)), "joint": bool(spec.get("joint",False)),
    }


def run_v54_diagnostic(
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
    ok, msg = validate_seed_registry()
    if not ok:
        raise IntegrityFailure("J2", msg)
    iso_ok, iso_msg = validate_train_heldout_isolation()
    if not iso_ok:
        raise IntegrityFailure("J4", iso_msg)
    if counts_by_source is None:
        try:
            counts_by_source = load_v25_channel_counts()
        except Exception as exc:
            raise IntegrityFailure("J4", f"load counts failed: {exc}") from exc
    matrices = reconstruct_v54_matrices(
        reference_metrics_path=structural_authority_path or STRUCTURAL_AUTHORITY_PATH,
        constructors=constructors,
    )
    v54_nested_preflight(counts_by_source=counts_by_source, matrices=matrices)
    field = GF2mField.create(DIMENSION)
    h1_full = matrices[("H1","L1")][0]
    # create empty root after preflight before first decoder call (partial retention semantics)
    output_root.mkdir(parents=True, exist_ok=False)
    # seed empty records for interrupt partial retention visibility
    (output_root / "v54_records.json").write_text("[]", encoding="utf-8")
    accounting = CallAccounting(hard_cap=HARD_CALL_CAP)
    records: list[dict[str, Any]] = []
    # summary accumulators
    base_exact_full = 0
    verify_base = 0
    stage1_call_exact = 0  # only inc1 call records
    verify_stage1_call = 0
    stage1_rescued = 0
    stage2_call_exact = 0
    verify_stage2_call = 0
    stage2_rescued = 0
    n_stage1_attempted = 0
    n_stage2_attempted = 0
    undetected = 0
    per_source: dict[str, dict[str,int]] = {s: {"base_exact":0,"verify_base":0,"stage1_call_exact":0,"verify_stage1_call":0,"stage1_final":0,"verify_after_stage1":0,"final":0,"verify_final":0,"rescued_stage1":0,"rescued_stage2":0,"n_stage1":0,"n_stage2":0,"undetected":0} for s in SOURCE_ORDER}
    # track per-block final leaks for total
    per_block_final_leak: dict[int, int] = {}
    call_id_counter = 1
    try:
        for source in SOURCE_ORDER:
            for bseed in NEW_BLOCK_SEEDS[source]:
                win = BLOCK_WINDOWS[bseed]
                if fake_runner:
                    rng = np.random.default_rng(bseed)
                    alice = rng.integers(0,1024, size=PAIRS_PER_BLOCK, dtype=np.int64)
                    bob = rng.integers(0,1024, size=PAIRS_PER_BLOCK, dtype=np.int64)
                    u1a, u2a, u1b, u2b = factorize_f03(alice, bob)
                else:
                    alice, bob = load_heldout_block(bseed)
                    u1a, u2a, u1b, u2b = factorize_f03(alice, bob)
                p_i = get_l1_prior_p_u1_given_b(counts_by_source[source], bob)
                s1 = syndrome_of_gf32(h1_full, u1a, field)
                accounting.register_start(layer="l1")
                validate_decoder_contract({"H": h1_full, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
                if fake_runner:
                    fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.05 * np.sin(np.arange(32))[None, :]
                    q = softmax_beliefs(fake_beliefs)
                    ent, md = compute_entropy_and_diff(q, p_i)
                    iterations_l1 = 5
                    syndrome_ok_l1 = True
                    exact_u1_for_record = True
                else:
                    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa as _dec_l1
                    _res_l1 = _dec_l1(h1_full, p_i, s1, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, field=field)
                    q = softmax_beliefs(_res_l1.final_beliefs)
                    ent, md = compute_entropy_and_diff(q, p_i)
                    _x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
                    syndrome_ok_l1 = bool(np.array_equal(syndrome_of_gf32(h1_full, _x_hat_u1, field), s1))
                    exact_u1_for_record = bool(np.array_equal(_x_hat_u1, u1a))
                    iterations_l1 = int(_res_l1.iterations)
                accounting.register_complete(layer="l1")
                prior_l2 = get_l1_app_prior_l2(counts_by_source[source], bob, q)
                errors_initial = _compute_errors_initial(u2a, u2b)
                # base
                m2 = SOURCE_CHECKS[source]
                base_mid = f"lane_c_{source}_s{_rep_seed('lane_c', source)}"
                base_spec = {
                    "call_id": f"C{call_id_counter:03d}",
                    "source": source, "block_seed": bseed,
                    "arm": "base", "pass_index": 1, "used_inc1": False, "used_inc2": False, "joint": False,
                    "matrix_id": base_mid,
                    "held_out_ordinal_start": win["held_out_ordinal_start"], "held_out_ordinal_end": win["held_out_ordinal_end"],
                    "frame_ids": list(win["frame_ids"]), "pairs_count": PAIRS_PER_BLOCK, "sampling_mode": SAMPLING_MODE,
                    "leak_total": leak_for(source), "leak_stage1": leak_stage1_for(source), "leak_stage2": leak_stage2_for(source),
                }
                H_base = matrices[("lane_c", source)][0]
                accounting.register_start(layer="base")
                validate_decoder_contract({"H": H_base, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
                raw_base = _evaluate_one_l2(H_base, source, bseed, counts_by_source[source], bob, u2a, u2b, field, DECODER_SETTING, fake_runner, decode_fn, errors_initial, base_spec, q=prior_l2, p_prior=p_i, iterations_l1=iterations_l1, entropy=ent, mean_abs=md)
                raw_base["exact_u1"] = bool(exact_u1_for_record)
                raw_base["syndrome_ok_l1"] = bool(syndrome_ok_l1)
                raw_base["arm"]="base"; raw_base["pass_index"]=1; raw_base["used_inc1"]=False; raw_base["used_inc2"]=False; raw_base["leak_total"]=leak_for(source)
                rec_base = build_record(base_spec, raw_base, DECODER_SETTING)
                records.append(rec_base)
                accounting.register_complete(layer="base")
                call_id_counter+=1
                verify_base_flag = bool(raw_base["syndrome_ok_l2"] and raw_base["tag_ok"])
                exact_base_flag = bool(raw_base["exact_full"])
                if exact_base_flag:
                    base_exact_full+=1
                    per_source[source]["base_exact"]+=1
                if verify_base_flag:
                    verify_base+=1
                    per_source[source]["verify_base"]+=1
                if verify_base_flag and not exact_base_flag:
                    undetected+=1
                    per_source[source]["undetected"]+=1
                # determine leak per block later; for now set base leak if verified
                if verify_base_flag:
                    per_block_final_leak[bseed] = leak_for(source)
                    # stage counts not incremented for this block
                    # compute stage1_final cumulative later
                else:
                    # stage1 attempt
                    n_stage1_attempted+=1
                    per_source[source]["n_stage1"]+=1
                    H_joint1 = matrices[("h_joint1", source)][0]
                    joint1_mid = base_mid + "+h_inc1"
                    stage1_spec = {
                        "call_id": f"C{call_id_counter:03d}",
                        "source": source, "block_seed": bseed,
                        "arm": "stage1", "pass_index": 2, "used_inc1": True, "used_inc2": False, "joint": True,
                        "matrix_id": joint1_mid,
                        "held_out_ordinal_start": win["held_out_ordinal_start"], "held_out_ordinal_end": win["held_out_ordinal_end"],
                        "frame_ids": list(win["frame_ids"]), "pairs_count": PAIRS_PER_BLOCK, "sampling_mode": SAMPLING_MODE,
                        "leak_total": leak_stage1_for(source), "leak_stage1": leak_stage1_for(source), "leak_stage2": leak_stage2_for(source),
                    }
                    accounting.register_start(layer="stage1")
                    validate_decoder_contract({"H": H_joint1, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
                    raw_s1 = _evaluate_one_l2(H_joint1, source, bseed, counts_by_source[source], bob, u2a, u2b, field, DECODER_SETTING, fake_runner, decode_fn, errors_initial, stage1_spec, q=prior_l2, p_prior=p_i, iterations_l1=iterations_l1, entropy=ent, mean_abs=md)
                    raw_s1["exact_u1"]=bool(exact_u1_for_record); raw_s1["syndrome_ok_l1"]=bool(syndrome_ok_l1)
                    raw_s1["arm"]="stage1"; raw_s1["pass_index"]=2; raw_s1["used_inc1"]=True; raw_s1["used_inc2"]=False; raw_s1["leak_total"]=leak_stage1_for(source)
                    rec_s1 = build_record(stage1_spec, raw_s1, DECODER_SETTING)
                    records.append(rec_s1)
                    accounting.register_complete(layer="stage1")
                    call_id_counter+=1
                    verify_s1 = bool(raw_s1["syndrome_ok_l2"] and raw_s1["tag_ok"])
                    exact_s1 = bool(raw_s1["exact_full"])
                    if verify_s1:
                        verify_stage1_call+=1
                        per_source[source]["verify_stage1_call"]+=1
                    if exact_s1 and verify_s1:
                        stage1_call_exact+=1
                        per_source[source]["stage1_call_exact"]+=1
                    if verify_s1 and not exact_s1:
                        undetected+=1
                        per_source[source]["undetected"]+=1
                    # rescued stage1 defined as verify_s1 && exact_s1 && !verify_base_flag
                    if verify_s1 and exact_s1:
                        stage1_rescued+=1
                        per_source[source]["rescued_stage1"]+=1
                    if verify_s1:
                        per_block_final_leak[bseed] = leak_stage1_for(source)
                    else:
                        n_stage2_attempted+=1
                        per_source[source]["n_stage2"]+=1
                        H_total = matrices[("h_total", source)][0]
                        total_mid = base_mid + "+h_inc1+h_inc2"
                        stage2_spec = {
                            "call_id": f"C{call_id_counter:03d}",
                            "source": source, "block_seed": bseed,
                            "arm": "stage2", "pass_index": 3, "used_inc1": True, "used_inc2": True, "joint": True,
                            "matrix_id": total_mid,
                            "held_out_ordinal_start": win["held_out_ordinal_start"], "held_out_ordinal_end": win["held_out_ordinal_end"],
                            "frame_ids": list(win["frame_ids"]), "pairs_count": PAIRS_PER_BLOCK, "sampling_mode": SAMPLING_MODE,
                            "leak_total": leak_stage2_for(source), "leak_stage1": leak_stage1_for(source), "leak_stage2": leak_stage2_for(source),
                        }
                        accounting.register_start(layer="stage2")
                        validate_decoder_contract({"H": H_total, "source": source, "block_seed": bseed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": _rep_seed("lane_c", source), "counts": counts_by_source[source], "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA}, DECODER_SETTING)
                        raw_s2 = _evaluate_one_l2(H_total, source, bseed, counts_by_source[source], bob, u2a, u2b, field, DECODER_SETTING, fake_runner, decode_fn, errors_initial, stage2_spec, q=prior_l2, p_prior=p_i, iterations_l1=iterations_l1, entropy=ent, mean_abs=md)
                        raw_s2["exact_u1"]=bool(exact_u1_for_record); raw_s2["syndrome_ok_l1"]=bool(syndrome_ok_l1)
                        raw_s2["arm"]="stage2"; raw_s2["pass_index"]=3; raw_s2["used_inc1"]=True; raw_s2["used_inc2"]=True; raw_s2["leak_total"]=leak_stage2_for(source)
                        rec_s2 = build_record(stage2_spec, raw_s2, DECODER_SETTING)
                        records.append(rec_s2)
                        accounting.register_complete(layer="stage2")
                        call_id_counter+=1
                        verify_s2 = bool(raw_s2["syndrome_ok_l2"] and raw_s2["tag_ok"])
                        exact_s2 = bool(raw_s2["exact_full"])
                        if verify_s2:
                            verify_stage2_call+=1
                        if exact_s2 and verify_s2:
                            stage2_call_exact+=1
                        if verify_s2 and not exact_s2:
                            undetected+=1
                            per_source[source]["undetected"]+=1
                        if verify_s2 and exact_s2:
                            stage2_rescued+=1
                            per_source[source]["rescued_stage2"]+=1
                        # leak stage2 regardless success/failure per spec
                        per_block_final_leak[bseed] = leak_stage2_for(source)
                # end per block
        # fill per-block leak for any missing (should be all 45)
        for bseed in BLOCK_WINDOWS:
            if bseed not in per_block_final_leak:
                per_block_final_leak[bseed] = leak_for(BLOCK_TO_SOURCE[bseed])
    except BaseException as _exc:
        records_sorted = sorted(records, key=lambda r: r["call_id"])
        with (output_root / "v54_records.json").open("w", encoding="utf-8") as f:
            json.dump(records_sorted, f, indent=2, ensure_ascii=False)
        with (output_root / "v54_records.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(RECORD_FIELDS))
            w.writeheader()
            for r in records_sorted:
                w.writerow({k: (",".join(map(str, v)) if k=="frame_ids" and isinstance(v, list) else v) for k,v in r.items()})
        notice = {
            "interrupted": True,
            "exception_type": type(_exc).__name__,
            "exception_message": str(_exc),
            "planned": {"total": f"{PLANNED_L1+PLANNED_L2_BASE}-{HARD_CALL_CAP}", "l1": PLANNED_L1, "l2_base": PLANNED_L2_BASE, "l2_stage1_max": PLANNED_L2_STAGE1_MAX, "l2_stage2_max": PLANNED_L2_STAGE2_MAX, "l2_max": PLANNED_L2_MAX, "hard_cap": HARD_CALL_CAP},
            "started": {"total": accounting.started, "l1": accounting.started_l1, "l2": accounting.started_l2, "base": accounting.started_base, "stage1": accounting.started_stage1, "stage2": accounting.started_stage2},
            "completed": {"total": accounting.completed, "l1": accounting.completed_l1, "l2": accounting.completed_l2, "base": accounting.completed_base, "stage1": accounting.completed_stage1, "stage2": accounting.completed_stage2},
            "records_completed": len(records_sorted),
        }
        with (output_root / "v54_interrupted_notice.json").open("w", encoding="utf-8") as f:
            json.dump(notice, f, indent=2, ensure_ascii=False)
        raise
    fails = accounting.validate_executed()
    if fails:
        raise IntegrityFailure(fails[0][0], fails[0][1])
    total_blocks = 45
    # cumulative counts
    stage1_final_exact = base_exact_full + stage1_rescued
    verify_after_stage1 = verify_base + verify_stage1_call  # because stage1 only attempted when !verify_base
    final_exact = stage1_final_exact + stage2_rescued
    verify_final = verify_after_stage1 + verify_stage2_call
    # per source cumulative
    for src in SOURCE_ORDER:
        ps = per_source[src]
        ps["stage1_final"] = ps["base_exact"] + ps["rescued_stage1"]
        ps["verify_after_stage1"] = ps["verify_base"] + ps["verify_stage1_call"]
        ps["final"] = ps["stage1_final"] + ps["rescued_stage2"]
        ps["verify_final"] = ps["verify_after_stage1"] + (ps.get("rescued_stage2",0) if False else 0)  # approximate; actual verify_final per source needs stage2 verify count
        # correct verify_final per source: we tracked verify_stage2_call globally; per source we need stage2 verify count. We stored stage2_call exact but not verify stage2 per source separately. Use stage2_rescued verify; stage2 verify without exact also counted as undetected but for verify_final we count all stage2 verifies (rescued plus undetected stage2)
        # For simplicity, maintain verify_stage2 per source via undetected distinction: per_source verify_stage2 = rescued_stage2 + undetected_stage2 where undetected stage2 is part of undetected counting; we didn't separate per source stage2 verifies beyond rescued. Use stage2_rescued as proxy for stage2 verify when fake (exact -> tag_ok). In real, exact implies tag_ok, so stage2 verify==stage2 exact for fake path; difference is undetected stage2 (verify true but not exact) which we already counted in undetected but not separately.
        # We'll store verify_stage2_call per source as rescued_stage2 + (undetected stage2 part). Since we didn't split per source stage2 undetected, approximate with same as rescued for gate (undetected will fail gate anyway).
        # Instead explicitly track verify_stage2 per source:
    # To correctly compute verify_final per source we need separate counter; we have global verify_stage2_call but per source we lost breakdown. Let's recompute from records for summary accuracy.
    # Recompute per source verify counters from records for correctness
    rec_by_block: dict[int, list] = {}
    for r in records:
        rec_by_block.setdefault(r["block_seed"], []).append(r)
    per_source_recalc: dict[str, dict[str,int]] = {s: {"verify_stage2":0} for s in SOURCE_ORDER}
    for bseed, recs in rec_by_block.items():
        src = BLOCK_TO_SOURCE[bseed]
        for r in recs:
            if r["arm"]=="stage2" and r["tag_ok"] and r["syndrome_ok_l2"]:
                per_source_recalc[src]["verify_stage2"]+=1
    for src in SOURCE_ORDER:
        per_source[src]["verify_stage2_call"] = per_source_recalc[src]["verify_stage2"]
        per_source[src]["verify_final"] = per_source[src]["verify_after_stage1"] + per_source[src]["verify_stage2_call"]
    # leakage totals
    total_disclosed = sum(per_block_final_leak.values())
    overall_avg = float(total_disclosed / 45) if 45 else 0.0
    per_source_avg: dict[str,float] = {}
    per_source_total: dict[str,int] = {s:0 for s in SOURCE_ORDER}
    per_source_n: dict[str,int] = {s:0 for s in SOURCE_ORDER}
    for bseed, leak in per_block_final_leak.items():
        src = BLOCK_TO_SOURCE[bseed]
        per_source_total[src]+=leak
        per_source_n[src]+=1
    for src in SOURCE_ORDER:
        per_source_avg[src] = float(per_source_total[src]/ per_source_n[src]) if per_source_n[src] else 0.0
        # also formula check: leak_base +40*N1/15+40*N2/15
        formula_avg = float(leak_for(src) + 40*per_source[src]["n_stage1"]/15 + 40*per_source[src]["n_stage2"]/15)
        # keep computed avg as per_block average (should match formula)
    avg_disclosure = float(overall_avg/1024)
    disclosure_per_final = float(total_disclosed / final_exact) if final_exact else None
    # four-way reclassified counts
    reclassified_counts = {"exact":0, "detected_verification_failure":0, "decoder_non_syndrome_failure":0, "undetected_accepted_wrong": undetected}
    for r in records:
        rc = r.get("reclassified")
        if rc in reclassified_counts and rc != "undetected_accepted_wrong":
            reclassified_counts[rc]+=1
    # gate
    # stage1_final gate and final gate
    stage1_per_source_ok = all(per_source[s]["stage1_final"] >=10 for s in SOURCE_ORDER) and all(per_source[s]["verify_after_stage1"] >=10 for s in SOURCE_ORDER)
    stage1_overall_ok = stage1_final_exact >=35 and verify_after_stage1 >=35
    stage1_gate = bool(stage1_overall_ok and stage1_per_source_ok and undetected==0)  # undetected same for stage1? spec undetected==0 overall at stage1? Use global undetected (any stage) but gate for stage1 should consider undetected overall? Keep undetected==0
    final_per_source_ok = all(per_source[s]["final"] >=10 for s in SOURCE_ORDER) and all(per_source[s]["verify_final"] >=10 for s in SOURCE_ORDER)
    final_overall_ok = final_exact >=35 and verify_final >=35
    final_gate = bool(final_overall_ok and final_per_source_ok and undetected==0)
    # additional rank/nested checks already passed in preflight; but also need to ensure integrity for summary
    if stage1_gate and final_gate:
        terminal = TERMINAL_DELTA8_ALREADY_SUFFICIENT
    elif (not stage1_gate) and final_gate:
        terminal = TERMINAL_DELTA16_ADDED_VALUE_SIGNAL
    elif not final_gate:
        # if we reached here without integrity failure, it's insufficient
        terminal = TERMINAL_DELTA16_INSUFFICIENT
    else:
        terminal = TERMINAL_DELTA16_INSUFFICIENT
    # if any integrity would have raised earlier, we would be in EVIDENCE_INVALID; here we return PASS/FAIL per spec
    # write records
    records_sorted = sorted(records, key=lambda r: r["call_id"])
    with (output_root / "v54_records.json").open("w", encoding="utf-8") as f:
        json.dump(records_sorted, f, indent=2, ensure_ascii=False)
    with (output_root / "v54_records.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(RECORD_FIELDS))
        w.writeheader()
        for r in records_sorted:
            w.writerow({k: (",".join(map(str, v)) if k=="frame_ids" and isinstance(v, list) else v) for k,v in r.items()})
    # paired deltas descriptive
    rescued_total = stage1_rescued + stage2_rescued
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
        "delta_m_total": DELTA_M_TOTAL,
        "leakage": {
            "per_source": {s: {"leak_base": leak_for(s), "leak_stage1": leak_stage1_for(s), "leak_stage2": leak_stage2_for(s), "delta": 40} for s in SOURCE_ORDER},
            "leakage_already_accounted": True,
            "first_pass_success_leak": {s: leak_for(s) for s in SOURCE_ORDER},
            "stage1_success_leak": {s: leak_stage1_for(s) for s in SOURCE_ORDER},
            "stage2_leak": {s: leak_stage2_for(s) for s in SOURCE_ORDER},
            "per_source_avg": per_source_avg,
            "overall_avg": overall_avg,
            "formula": "per_source_avg[s]=leak_base[s]+40*N_stage1[s]/15+40*N_stage2[s]/15 overall_avg=(Σ leak_base[source(block)]+40*N_stage1_total+40*N_stage2_total)/45",
            "n_stage1_attempted": n_stage1_attempted,
            "n_stage2_attempted": n_stage2_attempted,
            "total_disclosed_bits": int(total_disclosed),
            "avg_disclosure_per_attempted_frame": avg_disclosure,
            "disclosure_per_final_exact_block": disclosure_per_final,
            "total_formula": "Σ leak_base[source(block)]+40*N_stage1+40*N_stage2",
        },
        "counts": {
            "base_exact_full": base_exact_full,
            "verify_base": verify_base,
            "stage1_call_exact_full": stage1_call_exact,
            "verify_stage1_call": verify_stage1_call,
            "stage1_final_exact_full_count": stage1_final_exact,
            "verify_after_stage1": verify_after_stage1,
            "stage1_rescued": stage1_rescued,
            "stage2_call_exact_full": stage2_call_exact,
            "verify_stage2_call": verify_stage2_call,
            "stage2_rescued": stage2_rescued,
            "final_exact_full_count": final_exact,
            "verify_final": verify_final,
            "n_blocks": total_blocks,
            "n_stage1_attempted": n_stage1_attempted,
            "n_stage2_attempted": n_stage2_attempted,
            "rescue_rate_stage1": float(stage1_rescued / n_stage1_attempted) if n_stage1_attempted else 0.0,
            "rescue_rate_stage2": float(stage2_rescued / n_stage2_attempted) if n_stage2_attempted else 0.0,
            "per_source": per_source,
            "undetected_accepted_wrong": undetected,
            "reclassified": reclassified_counts,
            "stage1_final_gate": stage1_gate,
            "final_gate": final_gate,
        },
        "accounting": {
            "decoder_calls_planned": {"total": f"{PLANNED_L1+PLANNED_L2_BASE}-{HARD_CALL_CAP}", "l1": PLANNED_L1, "l2_base": PLANNED_L2_BASE, "l2_stage1_max": PLANNED_L2_STAGE1_MAX, "l2_stage2_max": PLANNED_L2_STAGE2_MAX, "l2_max": PLANNED_L2_MAX},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "l2": accounting.started_l2, "base": accounting.started_base, "stage1": accounting.started_stage1, "stage2": accounting.started_stage2},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "l2": accounting.completed_l2, "base": accounting.completed_base, "stage1": accounting.completed_stage1, "stage2": accounting.completed_stage2},
            "hard_cap": HARD_CALL_CAP,
        },
        "matrix": {
            "per_source": {s: {"m2": SOURCE_CHECKS[s], "m_joint1": SOURCE_CHECKS[s]+DELTA_M, "m_total": SOURCE_CHECKS[s]+DELTA_M_TOTAL, "delta_m": DELTA_M, "joint1_rank": SOURCE_CHECKS[s]+DELTA_M, "total_rank": SOURCE_CHECKS[s]+DELTA_M_TOTAL, "nested_stage1": True, "nested_stage2": True, "independence1": DELTA_M, "independence2": DELTA_M, "row_max_le16": True, "col_inc_max_le1": True, "E_inc1": int(matrices[("h_inc1", s)][1].get("E_inc",96)), "E_inc2": int(matrices[("h_inc2", s)][1].get("E_inc",96))} for s in SOURCE_ORDER},
        },
        "sampling_mode": SAMPLING_MODE,
        "held_out_provenance": {
            "block_windows": {str(k): v for k,v in BLOCK_WINDOWS.items()},
            "sampling_mode": SAMPLING_MODE,
            "fresh_45": NEW_BLOCK_SEEDS,
            "K2_per_source": {"1M":135,"1p5M":260,"2M":461},
            "index_formula": "floor(j*(K2-1)/14)",
        },
        "provenance": {
            "h_inc1_det_ids": INC1_DET_IDS,
            "h_inc2_det_ids": INC2_DET_IDS,
            "deterministic": "single_run_no_seed_search",
            "joint_rank_nested_independence": "verified",
            "tag_scope": TAG_SCOPE,
        },
        "terminal_state": terminal,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "statistics_note": STATISTICS_NOTE,
    }
    with (output_root / "v54_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return {"output_root": output_root, "terminal_state": terminal, "summary": summary, "records": records_sorted}
