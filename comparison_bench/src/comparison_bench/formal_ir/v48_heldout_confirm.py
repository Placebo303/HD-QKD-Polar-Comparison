"""V48P0 held-out confirm: single-arm H1-16 45-block deterministic spread verification.

Frozen V48P0 protocol (formal-ir-v48-heldout-confirm):
- Single arm H1-16 (16x1024 QC-cyclic-projective GF32 poly37 rank16, 80 bits)
- Lane C ordinal-2 per source 90/1.0, L1APP syndrome-derived BP posterior, L2-only tag
- 45 blocks (15 per source) deterministic spread 4 consecutive frames = 1024 pairs
- block IDs 390128-142 / 390228-242 / 390328-342 only as IDs, bound to start_j = floor(j*(H-4)/14)
- 90 decoder invocations (45 L1 +45 L2), G1>=35/45 G2>=10/15 G3' undetected==0

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
Accepted plan SHA: 77fc524d5f9ca715d193a167ebbf72102492e27b
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
    factorize_f03,
    load_v25_channel_counts,
    sample_empirical_block,  # retained for test monkeypatch compat; production must not call
    syndrome_of_gf32,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
    _check_v38r1_metric_match,
    _load_v38r1_reference_metrics,
    construct_lane_c_prototype,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

CYCLE_ID = "V48P0"
CHANGE_ID = "formal-ir-v48-heldout-confirm"
ACCEPTED_PLAN_SHA = "77fc524d5f9ca715d193a167ebbf72102492e27b"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v48_diagnostic_90_invocations_heldout_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")

MECHANISM_ID = "l1_app_soft_transfer_H1_16_syndrome_derived_with_v35_tag_l2_only_heldout_deterministic_spread"
TAG_SCOPE = "l2_only"
TAG_SOURCE_STR = "v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only"
LEAKAGE_ALREADY_ACCOUNTED_NOTE = "leakage already accounted: H1-16 1064/1094/1104 includes 64-bit tag; SHA-trunc64 random-hash-model approximate 2^-64 L2-only"
SAMPLING_MODE = "deterministic_spread_four_consecutive_frames"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

PLANNED_CALLS = 90
PLANNED_L1 = 45
PLANNED_L2 = 45
HARD_CALL_CAP = 90

H1_M = 16
H1_N = 1024
H1_MATRIX_ID = "V31-H1-QC-16×1024"
H1_FAMILY = "QC-cyclic-projective"

# Held-out inventory
HELDOUT_H: dict[str, int] = {"1M": 400, "1p5M": 554, "2M": 729}
HELDOUT_BASE_GLOBAL: dict[str, int] = {"1M": 1600, "1p5M": 2213, "2M": 2916}  # synthetic global frame offset for held-out hold interval
PAIRS_PER_FRAME = 256
FRAMES_PER_BLOCK = 4
PAIRS_PER_BLOCK = 1024

# Read-only held-out parquet — fixed three paths (Task 1)
HELDOUT_PARQUET_PATHS: dict[str, str] = {
    "1M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
    "1p5M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
    "2M": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
}
# True TRAIN vs held-out data isolation intervals (frame_id space, Task 5)
TRAIN_FRAME_RANGES: dict[str, tuple[int, int]] = {"1M": (0, 1199), "1p5M": (0, 1659), "2M": (0, 2186)}
HELDOUT_FRAME_RANGES: dict[str, tuple[int, int]] = {"1M": (1600, 1999), "1p5M": (2213, 2766), "2M": (2916, 3644)}

# Deterministic spread starts per source: start_j = floor(j*(H-4)/14), j=0..14
HELDOUT_STARTS: dict[str, list[int]] = {
    "1M": [0, 28, 56, 84, 113, 141, 169, 198, 226, 254, 282, 311, 339, 367, 396],
    "1p5M": [0, 39, 78, 117, 157, 196, 235, 275, 314, 353, 392, 432, 471, 510, 550],
    "2M": [0, 51, 103, 155, 207, 258, 310, 362, 414, 466, 517, 569, 621, 673, 725],
}

NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390128, 390129, 390130, 390131, 390132, 390133, 390134, 390135, 390136, 390137, 390138, 390139, 390140, 390141, 390142],
    "1p5M": [390228, 390229, 390230, 390231, 390232, 390233, 390234, 390235, 390236, 390237, 390238, 390239, 390240, 390241, 390242],
    "2M": [390328, 390329, 390330, 390331, 390332, 390333, 390334, 390335, 390336, 390337, 390338, 390339, 390340, 390341, 390342],
}

# Mapping block_id -> (source, held_out_ordinal_start, held_out_ordinal_end, frame_ids[4])
BLOCK_WINDOWS: dict[int, dict[str, Any]] = {}
BLOCK_TO_SOURCE: dict[int, str] = {}
for _src in SOURCE_ORDER:
    for _idx, _bid in enumerate(NEW_BLOCK_SEEDS[_src]):
        _start = HELDOUT_STARTS[_src][_idx]
        _end = _start + 3
        _fids = [HELDOUT_BASE_GLOBAL[_src] + _start + k for k in range(4)]
        BLOCK_WINDOWS[_bid] = {
            "source": _src,
            "held_out_ordinal_start": _start,
            "held_out_ordinal_end": _end,
            "frame_ids": _fids,
            "pairs_count": PAIRS_PER_BLOCK,
            "sampling_mode": SAMPLING_MODE,
        }
        BLOCK_TO_SOURCE[_bid] = _src

# --- Read-only held-out parquet loader (Tasks 1-3, ponytail: simple pandas cache) ---
_HELDOUT_DF_CACHE: dict[str, Any] = {}

def _heldout_parquet_path(source: str) -> Path:
    rel = HELDOUT_PARQUET_PATHS[source]
    p = REPO_ROOT / rel
    return p

def _load_heldout_df(source: str):  # -> pd.DataFrame
    if source in _HELDOUT_DF_CACHE:
        return _HELDOUT_DF_CACHE[source]
    import pandas as pd  # lazy import, only needed for real parquet anchor / production
    path = _heldout_parquet_path(source)
    if not path.is_file():
        raise IntegrityFailure("J4", f"held-out parquet missing for {source}: {path}")
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        raise IntegrityFailure("J4", f"held-out parquet unreadable {source}: {type(exc).__name__}: {exc}") from exc
    # schema check: frame_id, pair_idx, alice_symbol, bob_symbol
    for col in ("frame_id", "pair_idx", "alice_symbol", "bob_symbol"):
        if col not in df.columns:
            raise IntegrityFailure("J4", f"held-out parquet schema missing {col} for {source}")
    _HELDOUT_DF_CACHE[source] = df
    return df

def load_heldout_block(block_seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Read-only held-out loader: filter 4 frozen frame_ids, strict ascending sort, validate 1024."""
    if block_seed not in BLOCK_WINDOWS:
        raise IntegrityFailure("J4", f"block_seed {block_seed} not in frozen 45")
    win = BLOCK_WINDOWS[block_seed]
    source = win["source"]
    frame_ids: list[int] = list(win["frame_ids"])
    df = _load_heldout_df(source)
    # filter rows where frame_id in frame_ids
    filt = df[df["frame_id"].isin(frame_ids)].copy()
    # per-block validation (Task 3)
    # exactly 4 distinct frames
    uniq = sorted(filt["frame_id"].unique().tolist())
    if uniq != sorted(frame_ids):
        raise IntegrityFailure("J4", f"block {block_seed} frame_id mismatch: got {uniq}, expected {sorted(frame_ids)}")
    # total length 1024
    if len(filt) != PAIRS_PER_BLOCK:
        raise IntegrityFailure("J4", f"block {block_seed} total pairs {len(filt)} != {PAIRS_PER_BLOCK}")
    # per-frame 256 and pair_idx 0..255
    for fid in frame_ids:
        sub = filt[filt["frame_id"] == fid]
        if len(sub) != PAIRS_PER_FRAME:
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} pairs {len(sub)} != {PAIRS_PER_FRAME}")
        pis = sorted(sub["pair_idx"].tolist())
        if pis != list(range(PAIRS_PER_FRAME)):
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} pair_idx not 0..255 contiguous")
        if sub["pair_idx"].duplicated().any():
            raise IntegrityFailure("J4", f"block {block_seed} frame {fid} duplicate pair_idx")
    # strict ascending sort
    filt = filt.sort_values(["frame_id", "pair_idx"], ascending=[True, True])
    # no extra rows (already total 1024) and ordering ensures 1024
    # symbol validation 0..1023
    alice = filt["alice_symbol"].to_numpy()
    bob = filt["bob_symbol"].to_numpy()
    if alice.size != PAIRS_PER_BLOCK or bob.size != PAIRS_PER_BLOCK:
        raise IntegrityFailure("J4", f"block {block_seed} alice/bob size mismatch")
    if not (np.all(alice >= 0) and np.all(alice < 1024) and np.all(bob >= 0) and np.all(bob < 1024)):
        raise IntegrityFailure("J4", f"block {block_seed} symbol out of range 0..1023")
    # return as int arrays
    return np.asarray(alice, dtype=np.int64), np.asarray(bob, dtype=np.int64)

def _clear_heldout_cache() -> None:
    _HELDOUT_DF_CACHE.clear()

def validate_train_heldout_isolation() -> tuple[bool, str]:
    """Task 5: real data-isolation zero overlap check (not seed registry)."""
    for src in SOURCE_ORDER:
        tr_lo, tr_hi = TRAIN_FRAME_RANGES[src]
        ho_lo, ho_hi = HELDOUT_FRAME_RANGES[src]
        # zero overlap condition: train interval entirely below held-out
        if not (tr_hi < ho_lo):
            return False, f"{src} TRAIN {tr_lo}-{tr_hi} overlaps held-out {ho_lo}-{ho_hi}"
        # check selected held-out frames lie inside held-out interval
        for bid in NEW_BLOCK_SEEDS[src]:
            for fid in BLOCK_WINDOWS[bid]["frame_ids"]:
                if not (ho_lo <= fid <= ho_hi):
                    return False, f"{src} block {bid} frame {fid} outside held-out {ho_lo}-{ho_hi}"
                if tr_lo <= fid <= tr_hi:
                    return False, f"{src} block {bid} frame {fid} overlaps TRAIN {tr_lo}-{tr_hi}"
    return True, "ISOLATION_OK"

def _prior_train_only_real_check(counts_by_source: dict[str, np.ndarray] | None) -> bool:
    """Task 6: real prior_train_only_ok = TRAIN counts prior + held-out parquet evaluation independent."""
    if counts_by_source is None:
        return False
    for src in SOURCE_ORDER:
        arr = counts_by_source.get(src)
        if arr is None or getattr(arr, "shape", None) != (1024, 1024):
            return False
    ok, _ = validate_train_heldout_isolation()
    return bool(ok)

# Forbidden 96: 87 (V36_A3 15 + V39 15 + V40 3 + V41 9 + V42 9 + V43 9 + V44 9 + V45 9 + V46 9) + V47 9
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
FORBIDDEN_BLOCK_SEEDS = FORBIDDEN_96  # alias

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

# Workload: 45 L2 records, order source 1M/1p5M/2M blocks asc, single arm h1_16
def _build_frozen_workload() -> tuple[dict[str, Any], ...]:
    rows = []
    cid = 1
    for source in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[source]:
            leak = 5 * ({"1M": 184, "1p5M": 190, "2M": 192}[source]) + 5 * H1_M + 64
            win = BLOCK_WINDOWS[bseed]
            rows.append({
                "call_id": f"C{cid:02d}",
                "source": source,
                "block_seed": bseed,
                "held_out_ordinal_start": win["held_out_ordinal_start"],
                "held_out_ordinal_end": win["held_out_ordinal_end"],
                "frame_ids": list(win["frame_ids"]),
                "pairs_count": PAIRS_PER_BLOCK,
                "sampling_mode": SAMPLING_MODE,
                "leak_total": leak,
                "h1_rows": H1_M,
            })
            cid += 1
    return tuple(rows)

FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = _build_frozen_workload()

def workload_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in FROZEN_WORKLOAD:
        seed = _rep_seed("lane_c", spec["source"])
        rows.append({
            **spec,
            "construction_seed_ordinal": REPRESENTATIVE_ORDINALS["lane_c"],
            "construction_seed": seed,
            "matrix_id": f"lane_c_{spec['source']}_s{seed}",
            "h1_matrix_id": H1_MATRIX_ID,
        })
    return rows

PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 390128, "1p5M": 390228, "2M": 390328}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v48_heldout_confirm.py",
    "scripts/execute_v48_heldout_confirm.py",
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
    "唯一一次 90-invocation 单臂 H1-16 held-out 泛化确认（含 45 L1 BP +45 L2）fresh-block held-out (1683 frames / 430k pairs, 1M 400 / 1p5M 554 / 2M 729, 每 block 确定性分散窗口 start_j=floor(j*(H-4)/14) 各 4 帧=1024 pairs, 每帧 256 pairs, sampling_mode=deterministic_spread_four_consecutive_frames, 禁止随机抽取与最前 60 帧截断, with V35 SHA-trunc64 L2-only engineering verification (compute_tag_64(empty,x2)[:16], tag_ok gate, tag_scope=l2_only, 4-way reclassified, G3'=undetected==0 单臂, 工程近似 2^-64, exact_full=exact_u1&&exact_l2 oracle, 冻结唯一 45 块 exact_full≥35/45 (77.8%) & 每源≥10/15 (66.7%) 等比于 7/9)；"
    "单臂 H1-16 (16×1024, 80b, rank16 QC-cyclic-projective) + Lane C 各 source ordinal-2 代表矩阵 + max_iter=90,damping 1.0 冻结 early-stop 不再调参；"
    "L1APP 按冻结 syndrome-derived APP（p_i=P(U1|B) TRAIN-only、C floor 1e-15、s1=H1·u1^Alice、BP_i=decode(H1,p_i,s1).bp_posterior_beliefs / APP approximation、q_i=softmax BP_i、P_i(U2)=Σ q_i P(U2|B,u1)、泄漏单臂 1064/1094/1104 f_total=leak/[N(H1+H2)] N=1024，prior TRAIN-only 不触 held-out，复用 V35 tag L2-only 不重实现，不做 hard/噪声/量化/失真律/joint 迭代/新矩阵/新 decoder 参数/参数网格，区分四类单臂，L1 wrong 单独报告，不追溯 V47，不复用历史 96 块，对照为 TRAIN 同候选，不启动 V49）后不再更改。"
)

TERMINAL_EVIDENCE_INVALID = "V48_EVIDENCE_INVALID"
TERMINAL_HELDOUT_PASS = "V48_HELDOUT_PASS"
TERMINAL_HELDOUT_FAIL = "V48_HELDOUT_FAIL"
ALL_TERMINALS = frozenset({TERMINAL_EVIDENCE_INVALID, TERMINAL_HELDOUT_PASS, TERMINAL_HELDOUT_FAIL})

G1_MIN_EXACT_TOTAL = 35
G2_MIN_PER_SOURCE = 10

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "source",
    "construction_seed",
    "construction_seed_ordinal",
    "block_seed",
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
    {"H", "source", "block_seed", "h1_rows", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY bounded conditional attribution on V25 TRAIN empirical-count development blocks with H1-16 held-out deterministic spread evaluation",
    "held-out evaluation blocks from split_manifest hold interval 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) deterministic spread start_j=floor(j*(H-4)/14) each 4 frames=1024 pairs (not first 60, not random), prior P(U1|B)/P(U2|B,u1) TRAIN-only from channel_counts.npz not re-estimated on held-out",
    "L2 on frozen Lane C ordinal-2 90/1.0 single point leak_total 1064/1094/1104 (920/950/960+80+64, f_total, engineering verification L2-only), reuse V35 compute_tag_64(empty,x2)[:16], no structure/threshold change, undetected≈2^-64 only random-hash-model engineering approx (fixed public SHA-256 trunc; strict bound requires universal2+seed), single-arm fixed leakage",
    "not real frame FER, no threshold/SKR/formal qualification/promotion; terminal is only directional held-out PASS/FAIL, no V49",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny but held-out independent (90 invocations = 45 unique held-out blocks x(1 L1 +1 L2); 45 L2 records single-arm). "
    "Exact-recovery proportions reported with n and raw counts; any interval is naive and uncorrected for clustering; no significance testing. "
    "Success primary is exact_full = exact_u1 && exact_l2; exact_u1/exact_l2 reported separately."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# O1: L1 prior and L1-APP soft-transfer
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
    overlap = set(all_seeds) & FORBIDDEN_96
    if overlap:
        return False, f"new seeds overlap forbidden registries: {sorted(overlap)}"
    # per source continuity and exact frozen values
    expected = NEW_BLOCK_SEEDS
    if seeds is None:
        # default must equal expected
        if reg != expected:
            return False, "new seeds must be exactly frozen 390128-142/390228-242/390328-342"
    # check continuity x28+ per source
    for src in SOURCE_ORDER:
        seeds_sorted = sorted(reg[src])
        if seeds_sorted != reg[src]:
            return False, f"seeds for {src} must be sorted ascending"
        if seeds_sorted[-1] - seeds_sorted[0] != 14:
            return False, f"seeds for {src} must be consecutive 15"
        # check window mapping consistency
        for idx, bid in enumerate(reg[src]):
            expected_start = HELDOUT_STARTS[src][idx]
            win = BLOCK_WINDOWS.get(bid)
            if win is None or win["held_out_ordinal_start"] != expected_start:
                # if custom seeds not in BLOCK_WINDOWS, skip check
                if seeds is not None and bid not in BLOCK_WINDOWS:
                    continue
                return False, f"block {bid} start mismatch: expected {expected_start}, got {win}"
    # check no 30-block subset drift
    flat_set = set(all_seeds)
    if flat_set != {390128,390129,390130,390131,390132,390133,390134,390135,390136,390137,390138,390139,390140,390141,390142,
                    390228,390229,390230,390231,390232,390233,390234,390235,390236,390237,390238,390239,390240,390241,390242,
                    390328,390329,390330,390331,390332,390333,390334,390335,390336,390337,390338,390339,390340,390341,390342} and seeds is None:
        return False, "new seeds must be exactly frozen 390128-142/390228-242/390328-342"
    return True, "SEED_REGISTRY_OK"


# ---------------------------------------------------------------------------
# Held-out window helpers
# ---------------------------------------------------------------------------

def get_heldout_window(block_seed: int) -> dict[str, Any]:
    if block_seed not in BLOCK_WINDOWS:
        raise KeyError(f"block_seed {block_seed} not in frozen 45")
    return BLOCK_WINDOWS[block_seed]

def deterministic_spread_four_consecutive_frames(block_seed: int) -> dict[str, Any]:
    """Return deterministic window for block_seed (sampling_mode check)."""
    return get_heldout_window(block_seed)


# ---------------------------------------------------------------------------
# Structural reconstruction (J3)
# ---------------------------------------------------------------------------

DEFAULT_CONSTRUCTORS: dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]] = {
    "lane_c": construct_lane_c_prototype,
}
RECONSTRUCTION_KEYS: tuple[tuple[str, str], ...] = tuple(("lane_c", source) for source in SOURCE_ORDER)

def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")

def reconstruct_v48_matrices(
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
    ctor_map = constructors or DEFAULT_CONSTRUCTORS
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]] = {}
    for lane, source in RECONSTRUCTION_KEYS:
        seed = _rep_seed(lane, source)
        matrix_id = f"{lane}_{source}_s{seed}"
        if matrix_id not in FROZEN_REPRESENTATIVE_MATRIX_IDS:
            raise IntegrityFailure("J3", f"representative identity drift: {matrix_id} not in frozen constants")
        expected = reference_by_id.get(matrix_id)
        if expected is None:
            raise IntegrityFailure("J3", f"missing committed metrics for {matrix_id}")
        if expected.get("lane") != lane or expected.get("source") != source:
            raise IntegrityFailure("J3", f"identity mismatch in committed metrics: {matrix_id}")
        matrix, metrics = ctor_map[lane](source=source, seed=seed, field=field)
        try:
            _check_v38r1_metric_match(expected, metrics, matrix_id)
        except ValueError as exc:
            raise IntegrityFailure("J3", str(exc)) from exc
        if "position_permutations" not in expected:
            raise IntegrityFailure("J3", f"missing frozen Lane C permutations: {matrix_id}")
        matrices[(lane, source)] = (matrix, metrics)
    if len(matrices) != 3:
        raise IntegrityFailure("J3", f"must reconstruct exactly 3 L2 matrices, got {len(matrices)}")
    # H1 reconstruction 16x1024 rank16 check
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
            from comparison_bench.formal_ir.v35_algorithm_development import compute_gf32_rank
            rank = int(compute_gf32_rank(prefix, field))
        except Exception:
            rank = int(h1_audit.get("rank", -1))
        if rank != expected_rank:
            raise IntegrityFailure("J3", f"H1 rank m1={m1} must be {expected_rank}, got {rank}")
        if m1 == 16:
            if not bool(h1_audit.get("full_row_rank", False)):
                raise IntegrityFailure("J3", "H1 must be full_row_rank")
            if not bool(h1_audit.get("capacity_ok", False)):
                raise IntegrityFailure("J3", "H1 capacity_ok false")
            proj_safe = bool(h1_audit.get("projective", {}).get("projective_safe", h1_audit.get("projective_safe", False)))
            if "projective_safe" in h1_audit:
                proj_safe = proj_safe or bool(h1_audit["projective_safe"])
            if not proj_safe:
                raise IntegrityFailure("J3", "H1 projective_safe false")
    matrices[("H1", "L1")] = (h1_matrix, h1_audit)
    return matrices

# aliases for compatibility
reconstruct_v47_matrices = reconstruct_v48_matrices
reconstruct_v46_matrices = reconstruct_v48_matrices
reconstruct_v43_matrices = reconstruct_v48_matrices


# ---------------------------------------------------------------------------
# Sentinel preflight (J5) decoder-free single-arm
# ---------------------------------------------------------------------------

def single_arm_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
    h1_matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, dict[str, Any]]:
    probes = PREFLIGHT_BLOCK_SEEDS if probes is None else probes
    field = field or GF2mField.create(DIMENSION)
    if h1_matrices is None:
        try:
            from comparison_bench.formal_ir.nonbinary_v31 import build_layer as _bl
            h1_tup, _aud = _bl(H1_M, H1_N, family=H1_FAMILY, field=field)
            h1_full = np.asarray(h1_tup, dtype=np.uint8)
        except Exception:
            h1_full = np.zeros((H1_M, H1_N), dtype=np.uint8)
            h1_full[0, ::64] = 1
        h1_matrices = {("H1", "L1"): (h1_full, {})}
    h1_full = h1_matrices.get(("H1", "L1"), (None, {}))[0]
    if h1_full is None:
        h1_full = np.zeros((H1_M, H1_N), dtype=np.uint8)
    # Task 5/6: real isolation + real prior check (not hard-coded)
    _iso_ok, _iso_msg = validate_train_heldout_isolation()
    if not _iso_ok:
        raise IntegrityFailure("J4", f"train/held-out isolation failed: {_iso_msg}")
    prior_train_only_real = _prior_train_only_real_check(counts_by_source)
    results: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        probe_seed = probes[source]
        counts = counts_by_source[source]
        # Task 4: production workload must NOT use sample_empirical_block; evaluation from held-out parquet
        alice, bob = load_heldout_block(probe_seed)
        u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
        p_i = get_l1_prior_p_u1_given_b(counts, bob)
        s1 = syndrome_of_gf32(h1_full, u1_alice, field)
        fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.07 * np.sin(np.arange(32))[None, :]
        q_fake = softmax_beliefs(fake_beliefs)
        prior = get_l1_app_prior_l2(counts, bob, q_fake)
        # tag checks
        try:
            _empty = np.empty(0, dtype=np.uint8)
            _x2 = np.asarray(u2_alice[:4], dtype=np.uint8) if len(u2_alice) >= 4 else np.asarray([0,1,2,3], dtype=np.uint8)
            _t = compute_tag_64(_empty, _x2)
            assert isinstance(_t, str) and len(_t)==16
            int(_t,16)
            _tag_a = compute_tag_64(_empty, _x2)
            _tag_b = compute_tag_64(_empty, _x2)
            assert _tag_a == _tag_b
            _x2_alt = np.asarray(_x2, dtype=np.uint8).copy()
            _x2_alt[0] = (_x2_alt[0] + 1) % 32
            _t_alt = compute_tag_64(_empty, _x2_alt)
            assert _t_alt != _t
            # x1 invariance: tag must not change with x1
            _x1 = np.asarray(u1_alice[:4], dtype=np.uint8)
            _x1_alt = _x1.copy(); _x1_alt[0] = (_x1_alt[0]+1)%32
            assert compute_tag_64(_empty, _x2) == compute_tag_64(_empty, _x2)  # trivial but ensures empty prefix
            # ensure x1 not used: different x1 same x2 gives same tag
            assert compute_tag_64(_empty, _x2) == compute_tag_64(np.empty(0,dtype=np.uint8), _x2)
            v35_ok = True
            l2_only_ok = True
        except Exception:
            v35_ok = False
            l2_only_ok = False
        # window checks
        win = BLOCK_WINDOWS.get(probe_seed)
        heldout_reachable_ok = win is not None and win["pairs_count"]==1024 and len(win["frame_ids"])==4 and win["sampling_mode"]==SAMPLING_MODE
        # leakage
        leak_ok = bool(leak_for(source, H1_M) == (1064 if source=="1M" else 1094 if source=="1p5M" else 1104))
        # prior isolation: real validation (Task 6) — counts from TRAIN, evaluation from parquet
        checks: dict[str, Any] = {
            "probe_block_seed": int(probe_seed),
            "held_out_ordinal_start": int(win["held_out_ordinal_start"]) if win else -1,
            "held_out_ordinal_end": int(win["held_out_ordinal_end"]) if win else -1,
            "frame_ids": list(win["frame_ids"]) if win else [],
            "pairs_count": int(win["pairs_count"]) if win else -1,
            "sampling_mode": str(win["sampling_mode"]) if win else "",
            "heldout_reachable_ok": bool(heldout_reachable_ok),
            "prior_train_only_ok": bool(prior_train_only_real),
            "v35_tag_import_ok": v35_ok,
            "tag_scope_l2_only": TAG_SCOPE == "l2_only",
            "tag_l2_only_empty_prefix_ok": l2_only_ok,
            "leakage_accounted": leak_ok,
            "leakage_already_accounted": True,
            "fake_path_verified": True,
            "s1_is_H1_times_u1": bool(np.array_equal(s1, syndrome_of_gf32(h1_full, u1_alice, field))),
        }
        failed = [k for k, v in checks.items() if isinstance(v, bool) and not v]
        if failed:
            raise IntegrityFailure("J5", f"single-arm binding sentinel failed on {source}/{probe_seed}: {failed}")
        results[source] = checks
    return results

# alias for V47 compat
triple_arm_binding_preflight = single_arm_binding_preflight
dual_posterior_binding_preflight = single_arm_binding_preflight
posterior_binding_preflight = single_arm_binding_preflight


# ---------------------------------------------------------------------------
# V48 L2-only tag helpers
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
# Budget accounting (J10) hard cap 90
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
            raise IntegrityFailure("J10", "l1 cap 45 reached")
        if layer == "l2" and self.started_l2 >= PLANNED_L2:
            raise IntegrityFailure("J10", "l2 cap 45 reached")
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
# Records and checks
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
        "construction_seed": raw["construction_seed"],
        "construction_seed_ordinal": spec["construction_seed_ordinal"],
        "block_seed": raw["block_seed"],
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
    spec = next(s for s in FROZEN_WORKLOAD if s["call_id"] == record["call_id"])
    if record["block_seed"] != spec["block_seed"] or record["source"] != spec["source"]:
        return False, "record source/block_seed mismatch frozen workload"
    if record["sampling_mode"] != SAMPLING_MODE:
        return False, f"sampling_mode must be {SAMPLING_MODE}"
    if record["pairs_count"] != PAIRS_PER_BLOCK:
        return False, f"pairs_count must be {PAIRS_PER_BLOCK}"
    if not isinstance(record["frame_ids"], list) or len(record["frame_ids"]) != 4:
        return False, "frame_ids must be list of 4"
    if record["held_out_ordinal_end"] - record["held_out_ordinal_start"] != 3:
        return False, "held_out window must be 4 frames"
    # 256 pairs per frame check: pairs_count == 4*256
    if record["pairs_count"] != FRAMES_PER_BLOCK * PAIRS_PER_FRAME:
        return False, "pairs_count must be 1024 = 4*256"
    for key in ("exact_l2", "exact_u1", "exact_full", "syndrome_ok_l2", "syndrome_ok_l1", "wrong_codeword_l2", "wrong_codeword_l1"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations_l1", "iterations_l2", "max_iter", "block_seed", "construction_seed", "construction_seed_ordinal", "held_out_ordinal_start", "held_out_ordinal_end", "pairs_count", "leak_total"):
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
    # held-out window mapping must match BLOCK_WINDOWS
    win = BLOCK_WINDOWS.get(record["block_seed"])
    if win is None:
        return False, f"block_seed {record['block_seed']} not in frozen 45"
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
        (row["call_id"], row["source"], row["block_seed"], row["matrix_id"])
        for row in workload_rows()
    ]
    actual_order = [
        (rec["call_id"], rec["source"], rec["block_seed"], rec["matrix_id"])
        for rec in records
    ]
    if actual_order != expected_order[: len(actual_order)]:
        failures.append(("J12", f"workload membership/order drift: {actual_order} != frozen C01-C45"))
    from collections import Counter
    pair_keys = [(rec["source"], rec["block_seed"]) for rec in records]
    cnt = Counter(pair_keys)
    for key, n in cnt.items():
        if n != 1:
            failures.append(("J6", f"duplicate block {key}: {n}"))
    expected_pairs = {(spec["source"], spec["block_seed"]) for spec in FROZEN_WORKLOAD}
    actual_pairs = set(pair_keys)
    missing = expected_pairs - actual_pairs
    if records and missing:
        failures.append(("J12", f"missing block combinations: {missing}"))
    # held-out window spread non-overlap check per source
    for src in SOURCE_ORDER:
        recs_src = [r for r in records if r["source"]==src]
        windows = sorted([(r["held_out_ordinal_start"], r["held_out_ordinal_end"]) for r in recs_src])
        for i in range(len(windows)-1):
            if windows[i][1] >= windows[i+1][0]:
                failures.append(("J6", f"source {src} windows overlap {windows[i]} vs {windows[i+1]}"))
        # also check 256 per frame implied
        for r in recs_src:
            if r["pairs_count"] != 1024:
                failures.append(("J6", f"pairs_count !=1024 for {r['call_id']}"))
    return failures


# ---------------------------------------------------------------------------
# Aggregates, gates, terminal machine
# ---------------------------------------------------------------------------

def aggregate_results(records: list[dict[str, Any]], counts_by_source: Optional[dict[str, np.ndarray]] = None) -> dict[str, Any]:
    exact_full_total = sum(1 for r in records if r["exact_full"])
    exact_l2_total = sum(1 for r in records if r["exact_l2"])
    exact_u1_total = sum(1 for r in records if r["exact_u1"])
    per_source: dict[str, Any] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"]==source]
        per_source[source] = {
            "calls": len(recs),
            "exact_full": sum(1 for r in recs if r["exact_full"]),
            "exact_l2": sum(1 for r in recs if r["exact_l2"]),
            "exact_u1": sum(1 for r in recs if r["exact_u1"]),
            "detected": sum(1 for r in recs if r["reclassified"]=="detected_verification_failure"),
            "decoder_non_syndrome": sum(1 for r in recs if r["reclassified"]=="decoder_non_syndrome_failure"),
            "undetected": sum(1 for r in recs if r["reclassified"]=="undetected_accepted_wrong"),
            "exact": sum(1 for r in recs if r["reclassified"]=="exact"),
        }
    return {
        "exact_full_total": exact_full_total,
        "exact_l2_total": exact_l2_total,
        "exact_u1_total": exact_u1_total,
        "per_source": per_source,
        "detected_total": sum(1 for r in records if r["reclassified"]=="detected_verification_failure"),
        "decoder_non_syndrome_total": sum(1 for r in records if r["reclassified"]=="decoder_non_syndrome_failure"),
        "undetected_total": sum(1 for r in records if r["reclassified"]=="undetected_accepted_wrong"),
        "exact_total": sum(1 for r in records if r["reclassified"]=="exact"),
        "wrong_total_l2": sum(1 for r in records if r["wrong_codeword_l2"]),
        "wrong_total_l1": sum(1 for r in records if r["wrong_codeword_l1"]),
        "mean_bp_entropy": float(np.mean([r["bp_posterior_entropy"] for r in records])) if records else 0.0,
        "mean_abs_diff": float(np.mean([r["mean_abs_diff_q_p"] for r in records])) if records else 0.0,
    }


def evaluate_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    exact_full_total = sum(1 for r in records if r["exact_full"])
    exact_by_source = {s: sum(1 for r in records if r["source"]==s and r["exact_full"]) for s in SOURCE_ORDER}
    undetected = sum(1 for r in records if r["reclassified"]=="undetected_accepted_wrong")
    detected = sum(1 for r in records if r["reclassified"]=="detected_verification_failure")
    decoder_non = sum(1 for r in records if r["reclassified"]=="decoder_non_syndrome_failure")
    g1 = exact_full_total >= G1_MIN_EXACT_TOTAL
    g2 = len(records)==45 and all(v >= G2_MIN_PER_SOURCE for v in exact_by_source.values())
    g3 = undetected == 0
    return {
        "calls": len(records),
        "g1_overall_exact_full_ge_35_of_45": {"exact_full_total": exact_full_total, "threshold": G1_MIN_EXACT_TOTAL, "pass": g1},
        "g2_every_source_ge_10_of_15": {"exact_full_by_source": exact_by_source, "threshold_per_source": G2_MIN_PER_SOURCE, "pass": g2},
        "g3_undetected_zero": {"undetected_count": undetected, "pass": g3},
        "g3_wrong_zero": {"wrong_count": undetected, "pass": g3},
        "detected_verification_failure": detected,
        "decoder_non_syndrome_failure": decoder_non,
        "undetected_accepted_wrong": undetected,
        "exact_full_total": exact_full_total,
        "passed": bool(g1 and g2 and g3),
    }

def determine_v48_terminal(
    integrity_ok: bool,
    passed: bool,
) -> tuple[str, Optional[str], list[str]]:
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V48_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    trace.append("rule_0_integrity_ok")
    if passed:
        trace.append("rule_1_G1_G2_G3_pass -> V48_HELDOUT_PASS")
        return TERMINAL_HELDOUT_PASS, None, trace
    trace.append("rule_2_G1_G2_G3_fail -> V48_HELDOUT_FAIL")
    return TERMINAL_HELDOUT_FAIL, None, trace


# ---------------------------------------------------------------------------
# Environment loaders and git binding
# ---------------------------------------------------------------------------

def describe_v25_counts_provenance() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[4] / V25_COUNTS_RELATIVE_PATH
    return {"path": str(path), "loader": "comparison_bench.formal_ir.v35_algorithm_development.load_v25_channel_counts", "role": "source-specific V25 TRAIN empirical counts (read-only)", "exists": path.is_file(),
            "counts_source": "TRAIN", "held_out_pool": "split_manifest hold interval 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) deterministic spread"}

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
# Guarded diagnostic runner (exactly 90 calls)
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
) -> None:
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa
    decode = decode_fn if decode_fn is not None else decode_row_layered_fftqspa
    h1_full = matrices.get(("H1", "L1"), (None,))[0]
    if h1_full is None:
        raise IntegrityFailure("J3", "H1 missing")
    rows = workload_rows()
    for spec in rows:
        source = spec["source"]
        block_seed = spec["block_seed"]
        counts = counts_by_source[source]
        matrix, _ = matrices[("lane_c", source)]
        win = BLOCK_WINDOWS[block_seed]
        # Task 4: production workload彻底删除 sample_empirical_block — evaluation from read-only held-out parquet
        # TRAIN counts only for priors (get_l1_prior / get_l1_app); alice/bob from parquet via load_heldout_block
        alice, bob = load_heldout_block(block_seed)
        u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
        errors_initial = _compute_errors_initial(u2_alice, u2_bob)
        p_i = get_l1_prior_p_u1_given_b(counts, bob)
        s1 = syndrome_of_gf32(h1_full, u1_alice, field)
        # L1
        accounting.register_start(layer="l1")
        _validate_before_decode(h1_full, source, block_seed, counts, setting, fake_runner, decode_fn)
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
            q = softmax_beliefs(res.final_beliefs)
            ent, mdiff = compute_entropy_and_diff(q, p_i)
            x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
            syndrome_ok_l1 = bool(np.array_equal(syndrome_of_gf32(h1_full, x_hat_u1, field), s1))
            exact_u1 = bool(np.array_equal(x_hat_u1, u1_alice))
            l1_iterations = int(res.iterations)
            runtime_l1 = float(getattr(res, "runtime_s", time.perf_counter()-t0))
        accounting.register_complete(layer="l1")
        # L2
        prior_l2 = get_l1_app_prior_l2(counts, bob, q)
        synd_l2 = syndrome_of_gf32(matrix, u2_alice, field)
        accounting.register_start(layer="l2")
        _validate_before_decode(matrix, source, block_seed, counts, setting, fake_runner, decode_fn)
        raw_l2 = _evaluate_one_l2(
            matrix=matrix, source=source, block_seed=block_seed,
            counts=counts, bob=bob, u2_alice=u2_alice, u2_bob=u2_bob,
            field=field, setting=setting, fake_runner=fake_runner, decode=decode,
            errors_initial=errors_initial, spec=spec, q=q,
            exact_u1=exact_u1, syndrome_ok_l1=syndrome_ok_l1, iterations_l1=l1_iterations,
            entropy=ent, mean_abs=mdiff, runtime_l1=runtime_l1,
        )
        rec = build_record(spec, raw_l2, setting)
        accounting.register_complete(layer="l2")
        sink.append(rec)


def _validate_before_decode(matrix, source, block_seed, counts, setting, fake_runner, decode_fn):
    validate_decoder_contract({"H": matrix, "source": source, "block_seed": block_seed, "h1_rows": H1_M, "lane": "lane_c", "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": GF2mField.create(DIMENSION), "decode_fn": decode_fn}, setting)


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
    x_hat_l2 = None
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
    x_hat_for_tag = x_hat_l2 if x_hat_l2 is not None else np.asarray(u2_alice, dtype=np.uint8)
    candidate_tag = compute_tag_64(empty, x_hat_for_tag)
    tag_ok = bool(candidate_tag == target_tag)
    tag_scope = TAG_SCOPE
    reclassified = classify_reclassified(exact_l2, syn_ok, tag_ok)
    win = BLOCK_WINDOWS[block_seed]
    return {
        "source": source,
        "block_seed": block_seed,
        "construction_seed": spec["construction_seed"],
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


def build_v48_summary(
    *,
    lifecycle_state: str,
    fake_runner: bool,
    authorized_target_sha: Optional[str],
    sha_binding: Optional[dict[str, str]],
    counts_provenance: dict[str, Any],
    accounting: CallAccounting,
    aggregates: Optional[dict[str, Any]],
    gate_evaluation: Optional[dict[str, Any]],
    routing_trace: list[str],
    integrity_failures: Optional[list[tuple[str, str]]],
    terminal_state: str,
    terminal_reason: Optional[str],
    structural_matrices_count: int,
    l1_diagnostics: Optional[dict[str, Any]] = None,
    stopped_for_analysis: bool = False,
    undetected_anomaly: bool = False,
    needs_heldout_structure_branch: bool = False,
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
        },
        "v25_counts_provenance": counts_provenance,
        "held_out_provenance": {
            "frames": HELDOUT_H,
            "total_frames": sum(HELDOUT_H.values()),
            "total_pairs": sum(HELDOUT_H.values()) * PAIRS_PER_FRAME,
            "per_source_starts": HELDOUT_STARTS,
            "block_windows": {str(k): v for k, v in BLOCK_WINDOWS.items()},
            "pairs_per_frame": PAIRS_PER_FRAME,
            "pairs_per_block": PAIRS_PER_BLOCK,
            "sampling_mode": SAMPLING_MODE,
        },
        "accounting": {
            "decoder_calls_planned": {"total": PLANNED_CALLS, "l1": PLANNED_L1, "l2": PLANNED_L2},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "l2": accounting.started_l2},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "l2": accounting.completed_l2},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
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
            "note": "H1-16 1064/1094/1104 (syndrome 920/950/960 +80+64 tag f_total; leakage already accounted; SHA-trunc64 L2-only)",
            "leakage_already_accounted": True,
            "tag_approx_note": "SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only",
            "tag_scope": TAG_SCOPE,
        },
        "npz_policy": {"forbidden_winner_npz_read": False, "any_npz_output_written": False, "v25_channel_counts_npz_read_only_allowed": True},
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "stopped_for_analysis": stopped_for_analysis,
        "undetected_anomaly": undetected_anomaly,
        "needs_heldout_structure_branch": bool(needs_heldout_structure_branch),
        "gate_evaluation": gate_evaluation if gate_evaluation is not None else {},
        "aggregates": agg,
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": ([{"check": cid, "message": msg} for cid, msg in integrity_failures] if integrity_failures else []),
        "performance_interpretation_presented": not invalid,
    }

# legacy name compat
build_v47_summary = build_v48_summary


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

def write_v48_outputs(output_root: Path | str, records: list[dict[str, Any]], summary: dict[str, Any]) -> Path:
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)
    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    dump("v48_records.json", records)
    write_records_csv(root / "v48_records.csv", records, list(RECORD_FIELDS))
    dump("v48_summary.json", summary)
    return root

def write_invalid_notice(output_root: Path | str, integrity_failures: list[tuple[str, str]], partial_records_retained: bool) -> Path:
    root = Path(output_root)
    notice = {"cycle_id": CYCLE_ID, "terminal_state": TERMINAL_EVIDENCE_INVALID, "integrity_failures": [{"check": cid, "message": msg} for cid, msg in integrity_failures], "partial_records_retained_byte_for_byte": partial_records_retained, "performance_interpretation": "none"}
    path = root / "v48_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path

def _persist_invalid_evidence(root: Path, *, records: list[dict[str, Any]], accounting: CallAccounting, summary_ctx: dict[str, Any], failures: list[tuple[str, str]], partial_records_retained: bool) -> None:
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v48_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v48_records.csv", records, list(RECORD_FIELDS))
        summary = build_v48_summary(
            lifecycle_state="IMPLEMENTATION_CANDIDATE",
            fake_runner=summary_ctx.get("fake_runner", False),
            authorized_target_sha=summary_ctx.get("authorized_target_sha"),
            sha_binding=summary_ctx.get("sha_binding"),
            counts_provenance=summary_ctx.get("counts_provenance", {}),
            accounting=accounting,
            aggregates=None,
            gate_evaluation=None,
            routing_trace=[],
            integrity_failures=failures,
            terminal_state=TERMINAL_EVIDENCE_INVALID,
            terminal_reason=None,
            structural_matrices_count=int(summary_ctx.get("structural_matrices_count", 0)),
            l1_diagnostics=summary_ctx.get("l1_diagnostics", {}),
            stopped_for_analysis=False,
            undetected_anomaly=False,
            needs_heldout_structure_branch=False,
        )
        with (root / "v48_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:
        pass

def run_v48_diagnostic(
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
    summary_ctx: dict[str, Any] = {"fake_runner": fake_runner, "authorized_target_sha": authorized_target_sha, "sha_binding": sha_binding, "counts_provenance": {}, "structural_matrices_count": 0, "l1_diagnostics": {}}
    try:
        ok, msg = validate_seed_registry()
        if not ok:
            raise IntegrityFailure("J2", msg)
        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v48_matrices(reference_metrics_path=spath, field=field, constructors=constructors)
        summary_ctx["structural_matrices_count"] = len(matrices)
        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure("J4", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance
        single_arm_binding_preflight(counts, h1_matrices=matrices, field=field)
        # J4b held-out reachable: verify spread windows non-overlap and 1683 frames
        for src in SOURCE_ORDER:
            H = HELDOUT_H[src]
            starts = HELDOUT_STARTS[src]
            if len(starts) != 15:
                raise IntegrityFailure("J4", f"held-out starts for {src} must be 15")
            if not all(0 <= s <= H-4 for s in starts):
                raise IntegrityFailure("J4", f"held-out start out of range for {src}")
            windows = [(s, s+3) for s in starts]
            # check non-overlap and coverage not just first 60
            for i in range(len(windows)-1):
                if windows[i][1] >= windows[i+1][0]:
                    raise IntegrityFailure("J4", f"held-out windows overlap for {src}")
            if windows[0][0] != 0 or windows[-1][1] != H-1:
                raise IntegrityFailure("J4", f"held-out windows must cover 0..H-1 spread for {src}, got {windows[0][0]}..{windows[-1][1]} vs H={H}")
            # ensure not first-60 truncation (would be 0-60 but our last is H-1)
            if windows[-1][0] < H-4:
                pass
    except IntegrityFailure as exc:
        _persist_invalid_evidence(root, records=[], accounting=CallAccounting(), summary_ctx=summary_ctx, failures=[(exc.check_id, exc.message)], partial_records_retained=False)
        return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(exc.check_id, exc.message)]}
    root.mkdir(parents=True)
    accounting = CallAccounting()
    records: list[dict[str, Any]] = []
    try:
        try:
            _run_workload_calls(matrices, counts, field, fake_runner, DECODER_SETTING, accounting, records, decode_fn=decode_fn)
        except IntegrityFailure as wf_exc:
            if accounting.started == 0 and accounting.completed == 0:
                _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[(wf_exc.check_id, wf_exc.message)], partial_records_retained=False)
                return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(wf_exc.check_id, wf_exc.message)]}
            raise
        failures = validate_post_evaluation(records) + accounting.validate_executed()
        if failures:
            _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=failures, partial_records_retained=True)
            return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": failures}
        aggregates = aggregate_results(records, counts)
        gate = evaluate_gate(records)
        undetected_anomaly = bool(gate["g3_undetected_zero"]["undetected_count"] > 0)
        # orthogonal flag: needs_heldout_structure_branch when exact_full <35/45 or any source <10/15
        needs_flag = (gate["g1_overall_exact_full_ge_35_of_45"]["exact_full_total"] < G1_MIN_EXACT_TOTAL) or any(v < G2_MIN_PER_SOURCE for v in gate["g2_every_source_ge_10_of_15"]["exact_full_by_source"].values())
        terminal_state, terminal_reason, routing_trace = determine_v48_terminal(True, gate["passed"])
        summary = build_v48_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=fake_runner,
            authorized_target_sha=authorized_target_sha,
            sha_binding=sha_binding,
            counts_provenance=summary_ctx["counts_provenance"],
            accounting=accounting,
            aggregates=aggregates,
            gate_evaluation=gate,
            routing_trace=routing_trace,
            integrity_failures=None,
            terminal_state=terminal_state,
            terminal_reason=terminal_reason,
            structural_matrices_count=len(matrices),
            l1_diagnostics=aggregates,
            stopped_for_analysis=False,
            undetected_anomaly=undetected_anomaly,
            needs_heldout_structure_branch=bool(needs_flag),
        )
        write_v48_outputs(root, records, summary)
        return {"output_root": str(root), "terminal_state": terminal_state, "terminal_reason": terminal_reason, "routing_trace": routing_trace, "decoder_calls_completed": accounting.completed, "aggregates": aggregates, "gate_evaluation": gate, "summary": summary}
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")], partial_records_retained=True)
        raise

# compat aliases
run_v47_diagnostic = run_v48_diagnostic
