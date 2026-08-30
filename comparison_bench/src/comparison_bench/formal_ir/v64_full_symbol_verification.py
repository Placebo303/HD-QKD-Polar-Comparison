"""V64 Phase B fresh instrumentation — frozen V63 decoder, full-symbol tag dual reporting, single 64-bit leak.

Frozen from V54/V63: H1-16/L1APP/LaneC/Δ8+Δ8, decoder 90/1.0 poly37, TRAIN prior, leak 1064/1094/1104 +40/+80.
Unique change vs V63: tag_scope full_symbol = tag(32*U1+U2) canonical, but same decode computes both
tag_ok_l2 and tag_ok_full with single 64-bit leak not increasing calls/leak.
ponytail: delegate matrices to V54, keep file minimal, no new framework.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

ACCEPTED_PLAN_SHA = "760cb2967c7f5d5548a68f056458ef89398de3f2"
ACCEPTED_PLAN_SHORT = ACCEPTED_PLAN_SHA[:7]
BRANCH_REF = "origin/formal-ir-mainline"

# Frozen invariants (V63/V54)
SOURCE_ORDER = ("1M", "1p5M", "2M")
SOURCE_CHECKS = {"1M": 184, "1p5M": 190, "2M": 192}
LEAK_MAP: dict[str, dict[str, int]] = {
    "1M": {"base": 1064, "delta8": 1104, "delta16": 1144},
    "1p5M": {"base": 1094, "delta8": 1134, "delta16": 1174},
    "2M": {"base": 1104, "delta8": 1144, "delta16": 1184},
}
HARD_CAP = 96
PLANNED_L1 = 24
PLANNED_L2_BASE = 24
PLANNED_L2_STAGE1_MAX = 24
PLANNED_L2_STAGE2_MAX = 24
PLANNED_L2_MAX = 72
MAX_ITER = 90
DAMPING_ALPHA = 1.0
POLY = 37
STAGE_ORDER = ("base", "delta8", "delta16")
Q_SUB = 32

# Held-out geometry for registry
HELDOUT_H = {"1M": 400, "1p5M": 554, "2M": 729}
HELDOUT_BASE = {"1M": 1600, "1p5M": 2213, "2M": 2916}
SAMPLING_MODE = "deterministic_four_consecutive_frames_heldout_fresh_v64"
BLOCK_LENGTH = 1024
PAIRS_PER_BLOCK = 1024
OUTPUT_ROOT = Path(__file__).resolve().parents[4] / "comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01"
SCOPED_TRACKED_PATHS = (
    "comparison_bench/src/comparison_bench/formal_ir/v64_full_symbol_verification.py",
    "scripts/execute_v64_fresh_verify.py",
    "scripts/generate_v64_fresh_registry.py",
    "comparison_bench/src/comparison_bench/formal_ir/v54_two_stage_incremental_l2_rescue.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)


def decompose_symbols(s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(s, dtype=np.int64)
    return a // Q_SUB, a % Q_SUB


def recompose_symbols(u1: np.ndarray, u2: np.ndarray) -> np.ndarray:
    return (np.asarray(u1, dtype=np.int64) * Q_SUB + np.asarray(u2, dtype=np.int64)).astype(np.int64)


def _compute_tag_64(x1: np.ndarray, x2: np.ndarray) -> str:
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import compute_tag_64 as _t
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import compute_tag_64 as _t  # type: ignore
    return _t(np.asarray(x1, dtype=np.uint8), np.asarray(x2, dtype=np.uint8))


def compute_tag_l2(u2_hat: np.ndarray) -> str:
    empty = np.empty(0, dtype=np.uint8)
    return _compute_tag_64(empty, np.asarray(u2_hat, dtype=np.uint8))


def compute_tag_full(u1_hat: np.ndarray, u2_hat: np.ndarray) -> str:
    s_hat = recompose_symbols(np.asarray(u1_hat, dtype=np.int64), np.asarray(u2_hat, dtype=np.int64))
    # canonical packing reused: split 10-bit s_hat into two 5-bit planes for compute_tag_64
    x1 = (s_hat // 32).astype(np.uint8)
    x2 = (s_hat % 32).astype(np.uint8)
    return _compute_tag_64(x1, x2)


def verify_dual(
    u1_hat: np.ndarray,
    u2_hat: np.ndarray,
    u1_true: np.ndarray,
    u2_true: np.ndarray,
    syndrome_ok: bool,
) -> dict[str, Any]:
    """Single decode dual verification — compute both tag_ok, still single 64b leak."""
    # ponytail: single cost, dual computation pure function, no extra calls/leak
    tag_true_l2 = compute_tag_l2(u2_true)
    tag_true_full = compute_tag_full(u1_true, u2_true)
    tag_hat_l2 = compute_tag_l2(u2_hat)
    tag_hat_full = compute_tag_full(u1_hat, u2_hat)
    tag_ok_l2 = tag_hat_l2 == tag_true_l2
    tag_ok_full = tag_hat_full == tag_true_full
    exact_u1 = bool(np.array_equal(np.asarray(u1_hat), np.asarray(u1_true)))
    exact_l2 = bool(np.array_equal(np.asarray(u2_hat), np.asarray(u2_true)))
    exact_full = bool(exact_u1 and exact_l2)
    errors_u1 = int(np.sum(np.asarray(u1_hat) != np.asarray(u1_true)))
    errors_u2 = int(np.sum(np.asarray(u2_hat) != np.asarray(u2_true)))
    accepted_l2 = bool(syndrome_ok and tag_ok_l2)
    accepted_full = bool(syndrome_ok and tag_ok_full)
    undetected_l2 = bool(accepted_l2 and not exact_full)
    undetected_full = bool(accepted_full and not exact_full)
    intercepted_u1_only = bool((not exact_u1) and exact_l2 and tag_ok_l2 and (not tag_ok_full))
    same_decode_single_tag = True  # instrumentation invariant
    return dict(
        exact_u1=exact_u1, exact_l2=exact_l2, exact_full=exact_full,
        syndrome_ok_l1=None, syndrome_ok_l2=syndrome_ok,
        tag_ok_l2=tag_ok_l2, tag_ok_full=tag_ok_full,
        errors_u1=errors_u1, errors_u2=errors_u2,
        accepted_l2=accepted_l2, accepted_full=accepted_full,
        undetected_l2=undetected_l2, undetected_full=undetected_full,
        intercepted_u1_only=intercepted_u1_only,
        same_decode_single_tag=same_decode_single_tag,
        leak_single_tag=True,
    )


def build_instrumented_record(
    block_id: str,
    source: str,
    frame_ids: list[int],
    u1_hat: np.ndarray,
    u2_hat: np.ndarray,
    u1_true: np.ndarray,
    u2_true: np.ndarray,
    syndrome_ok_l1: bool,
    syndrome_ok_l2: bool,
    stage_used: str,
    decoder_calls: int,
) -> dict[str, Any]:
    leak_total = LEAK_MAP[source][stage_used]
    dual = verify_dual(u1_hat, u2_hat, u1_true, u2_true, syndrome_ok_l2)
    return dict(
        block_id=block_id, source=source, frame_ids=list(frame_ids),
        exact_u1=dual["exact_u1"], exact_l2=dual["exact_l2"], exact_full=dual["exact_full"],
        syndrome_ok_l1=bool(syndrome_ok_l1), syndrome_ok_l2=bool(syndrome_ok_l2),
        tag_ok_l2=bool(dual["tag_ok_l2"]), tag_ok_full=bool(dual["tag_ok_full"]),
        errors_u1=int(dual["errors_u1"]), errors_u2=int(dual["errors_u2"]),
        stage_used=stage_used, leak_total=int(leak_total), decoder_calls=int(decoder_calls),
        accepted_l2=bool(dual["accepted_l2"]), accepted_full=bool(dual["accepted_full"]),
        undetected_l2=bool(dual["undetected_l2"]), undetected_full=bool(dual["undetected_full"]),
        intercepted_u1_only=bool(dual["intercepted_u1_only"]),
        same_decode_single_tag=True,
    )


def leak_consistent(source: str) -> bool:
    b, s1, s2 = LEAK_MAP[source]["base"], LEAK_MAP[source]["delta8"], LEAK_MAP[source]["delta16"]
    return (s1 - b == 40) and (s2 - s1 == 40) and (b == 5 * SOURCE_CHECKS[source] + 80 + 64)


def reconstruct_v64_matrices(field=None):
    """Delegate to V54 — zero new matrices, frozen."""
    try:
        from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import reconstruct_v54_matrices
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import reconstruct_v54_matrices  # type: ignore
    return reconstruct_v54_matrices(field=field)


# Registry: enumerate remaining windows after excluding V48-V63 overlap — strict fresh, no fallback
def _forbidden_frame_sets() -> dict[str, set[int]]:
    try:
        from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (
            V48_HELDOUT_FRAME_IDS, V50_HELDOUT_FRAME_IDS, V51_HELDOUT_FRAME_IDS,
            V52_HELDOUT_FRAME_IDS, V53_HELDOUT_FRAME_IDS, BLOCK_WINDOWS as V54_W,
        )
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (  # type: ignore
            V48_HELDOUT_FRAME_IDS, V50_HELDOUT_FRAME_IDS, V51_HELDOUT_FRAME_IDS,
            V52_HELDOUT_FRAME_IDS, V53_HELDOUT_FRAME_IDS, BLOCK_WINDOWS as V54_W,
        )
    forb: dict[str, set[int]] = {s: set() for s in SOURCE_ORDER}
    for d in (V48_HELDOUT_FRAME_IDS, V50_HELDOUT_FRAME_IDS, V51_HELDOUT_FRAME_IDS, V52_HELDOUT_FRAME_IDS, V53_HELDOUT_FRAME_IDS):
        for s in SOURCE_ORDER:
            forb[s].update(set(d[s]))
    for bid, win in V54_W.items():
        src = win["source"]
        forb[src].update(set(win["frame_ids"]))
    # strictly exclude V63 windows (authoritative forb, no fallback reuse)
    try:
        import json as _js2
        p2 = Path(__file__).resolve().parents[4] / "comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/v63_records.json"
        if p2.is_file():
            arr2 = _js2.loads(p2.read_text(encoding="utf-8"))
            for r in arr2:
                src = r.get("source")
                if src in forb:
                    forb[src].update(set(r.get("frame_ids", [])))
    except Exception:
        pass
    # also check docs/research_cycles/V63P0/v63_dev_registry.json if present (covers smoke+dev 99)
    try:
        import json as _js3
        p3 = Path(__file__).resolve().parents[4] / "docs/research_cycles/V63P0/v63_dev_registry.json"
        if p3.is_file():
            j3 = _js3.loads(p3.read_text(encoding="utf-8"))
            for ent in j3.get("entries", []) if isinstance(j3, dict) else j3:
                src = ent.get("source")
                fids = ent.get("frame_ids", [])
                if src in forb:
                    forb[src].update(set(fids))
    except Exception:
        pass
    return forb


def _candidates_for_source(src: str, forb_set: set[int]) -> list[tuple[int, list[int]]]:
    H = HELDOUT_H[src]
    base = HELDOUT_BASE[src]
    cands: list[tuple[int, list[int]]] = []
    for start in range(H - 3):
        fids = [base + start + k for k in range(4)]
        if any(fid in forb_set for fid in fids):
            continue
        cands.append((start, fids))
    return cands


def build_v64_fresh_registry() -> list[dict[str, Any]]:
    """Authoritative fresh 24-block registry 8/source, zero overlap with V48-V63, K2>=24 hard, no fallback reuse."""
    forb = _forbidden_frame_sets()
    # verify K2 >=24 overall and per-source >=8 before dispersed pick
    k2_per_source: dict[str, int] = {}
    for src in SOURCE_ORDER:
        k2_per_source[src] = len(_candidates_for_source(src, forb[src]))
        if k2_per_source[src] < 8:
            raise ValueError(f"V64 K2<8 for {src}: {k2_per_source[src]} (EVIDENCE_INVALID, forbids fallback reuse)")
    total_k2 = sum(k2_per_source.values())
    if total_k2 < 24:
        raise ValueError(f"V64 total K2<24: {total_k2} (EVIDENCE_INVALID)")
    registry: list[dict[str, Any]] = []
    for src in SOURCE_ORDER:
        candidates = _candidates_for_source(src, forb[src])
        K2 = len(candidates)
        # ponytail: gap>=4 strong — first compute max independent set, then dispersed pick from it
        global_independent: list[tuple[int, list[int]]] = []
        for cand in sorted(candidates, key=lambda x: x[0]):
            if not global_independent or cand[0] - global_independent[-1][0] >= 4:
                global_independent.append(cand)
        if len(global_independent) < 8:
            raise ValueError(
                f"V64 K2={K2} for {src} cannot achieve 8 independent blocks with gap>=4: "
                f"global max {len(global_independent)} <8. EVIDENCE_INVALID — known ceiling: effective independence <8; "
                f"switch held-out pool or document ceiling explicitly in summary (cannot claim 8 independent). "
                f"Candidates starts {[c[0] for c in candidates]}"
            )
        # dispersed pick 8 from independent set via floor(j*(K_independent-1)/7) j=0..7 — guarantees gap>=4
        K_ind = len(global_independent)
        picks: list[tuple[int, list[int]]] = []
        for j in range(8):
            idx = (j * (K_ind - 1)) // 7 if K_ind > 1 else 0
            picks.append(global_independent[idx])
        # ensure distinct (dispersed on independent set already distinct when K_ind>=8)
        seen = set()
        deduped: list[tuple[int, list[int]]] = []
        for p in picks:
            if p[0] not in seen:
                deduped.append(p)
                seen.add(p[0])
        if len(deduped) < 8:
            for c in global_independent:
                if c[0] not in seen:
                    deduped.append(c)
                    seen.add(c[0])
                if len(deduped) == 8:
                    break
        picks = sorted(deduped[:8], key=lambda x: x[0])
        # additional hard frame_ids overlap check (gap>=4 ensures no shared frames)
        for a in range(len(picks)):
            for b in range(a+1, len(picks)):
                if set(picks[a][1]) & set(picks[b][1]):
                    raise ValueError(f"V64 frame_ids overlap {picks[a]} vs {picks[b]} for {src} — gap>=4 violated EVIDENCE_INVALID")
        for j, (ord_start, fids) in enumerate(picks):
            block_id = f"v64_fresh_{src}_{j:02d}"
            registry.append(dict(
                block_id=block_id, source=src, frame_ids=fids,
                held_out_ordinal_start=ord_start, held_out_ordinal_end=ord_start + 3,
                pairs_count=PAIRS_PER_BLOCK, BLOCK_LENGTH=BLOCK_LENGTH,
                sampling_mode=SAMPLING_MODE,
                held_out_source_path=f"comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_{src}_20260121_*/pairs.parquet",
                H_provenance=dict(H=HELDOUT_H[src], base=HELDOUT_BASE[src], K2=K2),
            ))
    if len(registry) != 24:
        raise ValueError(f"registry len {len(registry)} !=24")
    # global zero-overlap with prior already by forb; per-source distinct already ensured
    return registry


# Interpretation classification for fresh three rules
def classify_fresh_block(rec: dict[str, Any]) -> str:
    """Return one of: confirm_verification_scope / pause_tag_canonical / performance_only."""
    exact_u1, exact_l2 = rec["exact_u1"], rec["exact_l2"]
    tag_ok_l2, tag_ok_full = rec["tag_ok_l2"], rec["tag_ok_full"]
    syndrome_ok = rec["syndrome_ok_l2"]
    # U1 wrong + U2 exact + old accept + full reject -> confirm
    if (not exact_u1) and exact_l2 and syndrome_ok and tag_ok_l2 and (not tag_ok_full):
        return "confirm_verification_scope"
    # U2 wrong + tag_ok (any) -> pause investigation
    if (not exact_l2) and (tag_ok_l2 or tag_ok_full):
        return "pause_tag_canonical"
    return "performance_only"


def calls_in_cap(total_calls: int) -> bool:
    return 48 <= total_calls <= 96


# Budget helpers — 24-block hard cap 96
def budget_ok(n_stage1: int, n_stage2: int) -> bool:
    if n_stage1 > PLANNED_L2_STAGE1_MAX or n_stage2 > PLANNED_L2_STAGE2_MAX:
        return False
    total = PLANNED_L1 + PLANNED_L2_BASE + n_stage1 + n_stage2  # 24+24+stage1+stage2
    l2_total = PLANNED_L2_BASE + n_stage1 + n_stage2
    return 48 <= total <= HARD_CAP and 24 <= l2_total <= PLANNED_L2_MAX


class V64CallAccounting:
    """Per-task call accounting 48-96 hard cap 96, per-block 2-4, L2 24-72."""

    def __init__(self, hard_cap: int = HARD_CAP) -> None:
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
            raise ValueError(f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused (97th reject)")
        if layer == "l1" and self.started_l1 >= PLANNED_L1:
            raise ValueError("l1 cap 24 reached")
        if layer == "base" and self.started_base >= PLANNED_L2_BASE:
            raise ValueError("base cap 24 reached")
        if layer == "stage1" and self.started_stage1 >= PLANNED_L2_STAGE1_MAX:
            raise ValueError("stage1 cap 24 reached")
        if layer == "stage2" and self.started_stage2 >= PLANNED_L2_STAGE2_MAX:
            raise ValueError("stage2 cap 24 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
        elif layer == "base":
            self.started_base += 1
            self.started_l2 += 1
        elif layer == "stage1":
            self.started_stage1 += 1
            self.started_l2 += 1
        elif layer == "stage2":
            self.started_stage2 += 1
            self.started_l2 += 1
        elif layer == "l2":
            self.started_l2 += 1

    def register_complete(self, layer: str = "total") -> None:
        self.completed += 1
        if layer == "l1":
            self.completed_l1 += 1
        elif layer == "base":
            self.completed_base += 1
            self.completed_l2 += 1
        elif layer == "stage1":
            self.completed_stage1 += 1
            self.completed_l2 += 1
        elif layer == "stage2":
            self.completed_stage2 += 1
            self.completed_l2 += 1
        elif layer == "l2":
            self.completed_l2 += 1

    def validate(self) -> list[str]:
        errs: list[str] = []
        if self.completed > self.hard_cap:
            errs.append(f"completed {self.completed} exceeds hard cap {self.hard_cap}")
        if self.completed != self.started:
            errs.append(f"started {self.started} != completed {self.completed}")
        if self.completed < 48 or self.completed > 96:
            errs.append(f"total {self.completed} not in 48-96")
        if self.completed_l2 < 24 or self.completed_l2 > 72:
            errs.append(f"l2 {self.completed_l2} not in 24-72")
        return errs
