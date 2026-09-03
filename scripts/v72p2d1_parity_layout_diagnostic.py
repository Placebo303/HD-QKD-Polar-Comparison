#!/usr/bin/env python3
"""V72P2D1 parity-layout diagnostic (A/B) — frozen harness.

A=original mother, B=degree-2-parity-column-permuted mother under shared
CAL-only prior and frozen V72P1 decoder/ladder, wrapper scalars D1-D8.
Descriptive diagnosis only; no FER/SKR/qualification/promotion claim.

Frozen CLI:
  python scripts/v72p2d1_parity_layout_diagnostic.py \
    --registry v71_data_registry.json --session 20260123_1M_600k_0dB \
    --out comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab \
    --arm-budget-s 600 --global-budget-s 1800
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---- frozen constants ----
SEED_COLMAP = 20260902
Q = 1024
N = 1024
NBIT = 10240
M = 9036
FRAME_PAIRS = 256
CAL_START = 702
CAL_STOP = 1726  # exclusive; CAL 702..1725
VAL_BLOCK_FRAMES = [1726, 1727, 1728, 1729]
CHECKPOINT_ROWS = tuple(list(range(160, 8993, 128)) + [9032, 9036])
MAX_ITER_PER_CHECKPOINT = 10
MAX_TOTAL_ITERATIONS = 720
LLR_CLIP = 20.0
CONVERGENCE_TOL = 1e-6
PROBABILITY_FLOOR = 1e-300
EXPECTED_LAMBDA = 221.22162910704503
EXPECTED_CE = 7.135005172802673
CE_TOL = 1e-12
# B2 recount (20260903, get_mother_csr 9036x10240, generic check-pair definition):
#   python -c "import importlib.util; ..." -> four_A=four_B=1196 coll_A=coll_B=1194.
# Frozen 8452/8170 did not match the generic definition; corrected to recomputed
# values via this OpenSpec change (never hand-filled). Fake and real paths share
# count_four_cycles/count_collisions, so calibres are identical by construction.
EXPECTED_FOUR = 1196
EXPECTED_COLL = 1194
FROZEN_SESSION = "20260123_1M_600k_0dB"
FROZEN_REGISTRY = "v71_data_registry.json"
FROZEN_OUT = "comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab"
ARM_BUDGET_S = 600.0
GLOBAL_BUDGET_S = 1800.0
INFO_END = 1204  # cols 0..1203 fixed
PARITY_END = 10239  # cols 1204..10238 permuted, 10239 fixed
BLOCK0_BASELINE = {
    "checkpoints": 72,
    "iterations": 334,
    "status": "LADDER_EXHAUSTED",
    "bit_errors": 3100,
    "symbol_errors": 620,
    "syndrome_bits": 9036,
    "tag_bits": 64,
    "control_bits": 71,
    "leak_ir_bits": 9100,
    "total_public_bits": 9171,
}

# F3 literal allowlist (B3): `git status --porcelain` lines must start with one
# of these prefixes. Live-repo grandfathered pre-existing untracked outside this
# list are recorded as exemptions in OpenSpec (freeze-time clean checkout must be
# literal); any NEW line beyond allowlist + recorded grandfathers is FAIL.
ALLOWED_GIT_PREFIXES = (
    "?? openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/",
    "?? scripts/v72p2d1_parity_layout_diagnostic.py",
    "?? scripts/test_v72p2d1_parity_layout_diagnostic.py",
    "?? docs/research_cycles/V72P2D1-PARITY/EXECUTION_PACKET.md",
    "?? docs/research_cycles/V72P2D1-PARITY/REVIEW_VERDICT.md",
    "?? docs/research_cycles/V72P2D1-PARITY/RESULT_SUMMARY.md",
    "?? workspace/v72p2d1_",
)


def check_git_allowlist(status_lines) -> tuple[bool, list[str]]:
    extras: list[str] = []
    for line in status_lines:
        text = line.rstrip("\n")
        if not text.strip():
            continue
        if any(text.startswith(prefix) for prefix in ALLOWED_GIT_PREFIXES):
            continue
        extras.append(text)
    return (len(extras) == 0, extras)


class DataValidationError(ValueError):
    pass


class DecoderNumericError(ValueError):
    pass


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_mother_csr():
    mod = _load_module(
        REPO_ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir"
        / "v72p1_soft_joint_adapter.py",
        "v72p1_adapter_for_v72p2d1",
    )
    return mod.get_mother_csr()


def get_adapter_decoder():
    mod = _load_module(
        REPO_ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir"
        / "v72p1_soft_joint_adapter.py",
        "v72p1_adapter_decode_for_v72p2d1",
    )
    return mod.run_decoder


def _load_v72p2():
    # Ponytail lite reuse: registry/frame/CAL/prior semantics inherit V72P2.
    return _load_module(REPO_ROOT / "scripts" / "v72p2_real_smoke.py",
                        "v72p2_for_v72p2d1")


def check_assigned_v72p2d1(session: dict) -> tuple[list[int], list[int]]:
    cal_ids = [int(x) for x in session.get("stage2_CAL_frame_ids", [])]
    val_ids = [int(x) for x in session.get("stage2_VAL_frame_ids", [])]
    if cal_ids != list(range(CAL_START, CAL_STOP)):
        raise DataValidationError("CAL assignment is not the frozen 702..1725 sequence")
    if val_ids[:4] != list(VAL_BLOCK_FRAMES):
        raise DataValidationError("VAL diagnostic block is not the frozen 1726..1729 prefix")
    return cal_ids, list(VAL_BLOCK_FRAMES)


def _cleanup_tmp_dir(tmp_dir: Path) -> None:
    # Workspace candidate temp holds running snapshots only, never final outputs.
    # Explicit semantics (B5): remove after terminal four files land; keep for
    # debug only when the terminal write itself fails.
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except OSError:
        pass


def build_col_map(n_cols: int = NBIT, seed: int = SEED_COLMAP,
                  info_end: int = INFO_END, parity_end: int = PARITY_END) -> np.ndarray:
    col_map = np.arange(n_cols, dtype=np.int64)
    n_perm = int(parity_end - info_end)
    rng = np.random.default_rng(seed)
    col_map[info_end:parity_end] = info_end + rng.permutation(n_perm)
    return col_map


def build_B_csr(indptr_A: np.ndarray, indices_A: np.ndarray,
                col_map: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    indptr_B = np.array(indptr_A, dtype=np.int32, copy=True)
    indices_B = np.asarray(col_map[np.asarray(indices_A, dtype=np.int64)], dtype=np.int32)
    return indptr_B, indices_B


def col_degrees(indptr: np.ndarray, indices: np.ndarray, n_cols: int) -> np.ndarray:
    deg = np.zeros(n_cols, dtype=np.int64)
    np.add.at(deg, np.asarray(indices, dtype=np.int64), 1)
    return deg


def check_degree_dist(indptr: np.ndarray) -> dict:
    indptr = np.asarray(indptr)
    dist: dict[int, int] = {}
    for r in range(len(indptr) - 1):
        d = int(indptr[r + 1] - indptr[r])
        dist[d] = dist.get(d, 0) + 1
    return dist


def count_four_cycles(indptr: np.ndarray, indices: np.ndarray) -> int:
    """Generic four-cycle count: sum over check pairs C(|N(c1) cap N(c2)|,2)."""
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    n_checks = len(indptr) - 1
    n_cols = int(indices.max()) + 1 if len(indices) else 0
    var_to_checks: list[list[int]] = [[] for _ in range(n_cols)]
    for c in range(n_checks):
        for v in indices[indptr[c]:indptr[c + 1]]:
            var_to_checks[int(v)].append(c)
    pair_count: dict[tuple[int, int], int] = {}
    for checks in var_to_checks:
        d = len(checks)
        for i in range(d):
            for j in range(i + 1, d):
                a, b = checks[i], checks[j]
                if a > b:
                    a, b = b, a
                pair_count[(a, b)] = pair_count.get((a, b), 0) + 1
    return int(sum(k * (k - 1) // 2 for k in pair_count.values()))


def count_collisions(indptr: np.ndarray, indices: np.ndarray) -> int:
    """Generic collision count: number of check pairs sharing >=2 variables."""
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    n_checks = len(indptr) - 1
    n_cols = int(indices.max()) + 1 if len(indices) else 0
    var_to_checks: list[list[int]] = [[] for _ in range(n_cols)]
    for c in range(n_checks):
        for v in indices[indptr[c]:indptr[c + 1]]:
            var_to_checks[int(v)].append(c)
    pair_count: dict[tuple[int, int], int] = {}
    for checks in var_to_checks:
        d = len(checks)
        for i in range(d):
            for j in range(i + 1, d):
                a, b = checks[i], checks[j]
                if a > b:
                    a, b = b, a
                pair_count[(a, b)] = pair_count.get((a, b), 0) + 1
    return int(sum(1 for k in pair_count.values() if k >= 2))


def verify_M1_M7(indptr_A: np.ndarray, indices_A: np.ndarray,
                 indptr_B: np.ndarray, indices_B: np.ndarray,
                 col_map: np.ndarray, n_cols: int = NBIT,
                 expected_four: int = EXPECTED_FOUR,
                 expected_coll: int = EXPECTED_COLL) -> dict:
    indptr_A = np.asarray(indptr_A, dtype=np.int32)
    indices_A = np.asarray(indices_A, dtype=np.int32)
    indptr_B = np.asarray(indptr_B, dtype=np.int32)
    indices_B = np.asarray(indices_B, dtype=np.int32)
    col_map = np.asarray(col_map, dtype=np.int64)
    out: dict = {}
    # M1
    out["M1"] = bool(indptr_A.shape == indptr_B.shape == (M + 1,)
                      and len(indices_A) == len(indices_B) == 49620
                      and len(indptr_A) - 1 == 9036)
    # M2
    dist_B = check_degree_dist(indptr_B)
    out["M2"] = bool(dist_B == {4: 1, 5: 4594, 6: 4441})
    out["check_degree_B"] = {str(k): int(v) for k, v in dist_B.items()}
    # M3
    deg_A = col_degrees(indptr_A, indices_A, n_cols)
    deg_B = col_degrees(indptr_B, indices_B, n_cols)
    deg2_A = int(np.count_nonzero(deg_A == 2))
    deg2_B = int(np.count_nonzero(deg_B == 2))
    out["deg2_A"] = deg2_A
    out["deg2_B"] = deg2_B
    # info cols 0..1203 and 10239 identical (nnz per col; row sets for those cols)
    info_same = bool(np.array_equal(deg_A[:INFO_END], deg_B[:INFO_END])
                     and int(deg_A[PARITY_END]) == int(deg_B[PARITY_END]))
    # row-set equality for fixed cols: build col->rows for fixed cols only
    rows_A: dict[int, set] = {c: set() for c in list(range(INFO_END)) + [PARITY_END]}
    rows_B: dict[int, set] = {c: set() for c in list(range(INFO_END)) + [PARITY_END]}
    for r in range(len(indptr_A) - 1):
        for v in indices_A[indptr_A[r]:indptr_A[r + 1]]:
            v = int(v)
            if v < INFO_END or v == PARITY_END:
                rows_A[v].add(r)
    for r in range(len(indptr_B) - 1):
        for v in indices_B[indptr_B[r]:indptr_B[r + 1]]:
            v = int(v)
            if v < INFO_END or v == PARITY_END:
                rows_B[v].add(r)
    for c in rows_A:
        if rows_A[c] != rows_B[c]:
            info_same = False
            break
    var_dist_same = bool(np.array_equal(np.sort(deg_A), np.sort(deg_B)))
    out["M3"] = bool(deg2_A == 9035 and deg2_B == 9035 and info_same and var_dist_same)
    # M4
    seg = col_map[INFO_END:PARITY_END]
    out["M4"] = bool(len(seg) == PARITY_END - INFO_END
                     and set(seg.tolist()) == set(range(INFO_END, PARITY_END))
                     and np.array_equal(col_map[:INFO_END], np.arange(INFO_END))
                     and int(col_map[PARITY_END]) == PARITY_END
                     and np.array_equal(col_map,
                                        build_col_map(n_cols, SEED_COLMAP, INFO_END, PARITY_END)))
    # M5
    out["M5"] = bool(np.array_equal(indptr_A, indptr_B)
                     and np.array_equal(indices_B, col_map[np.asarray(indices_A, dtype=np.int64)]))
    # M6 (CSR independence; syndrome predicate checked separately per arm)
    out["M6_independent"] = bool(indptr_A is not indptr_B and indices_A is not indices_B)
    # M7
    four_A = count_four_cycles(indptr_A, indices_A)
    coll_A = count_collisions(indptr_A, indices_A)
    four_B = count_four_cycles(indptr_B, indices_B)
    coll_B = count_collisions(indptr_B, indices_B)
    out["four_A"] = int(four_A)
    out["coll_A"] = int(coll_A)
    out["four_B"] = int(four_B)
    out["coll_B"] = int(coll_B)
    out["M7"] = bool(four_A == expected_four and coll_A == expected_coll
                     and four_B == expected_four and coll_B == expected_coll)
    out["pass"] = bool(out["M1"] and out["M2"] and out["M3"] and out["M4"]
                       and out["M5"] and out["M6_independent"] and out["M7"])
    return out


def syndrome_compute(indptr: np.ndarray, indices: np.ndarray,
                     bits: np.ndarray, n_rows: int | None = None) -> np.ndarray:
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)
    bits = np.asarray(bits, dtype=np.uint8)
    total = len(indptr) - 1
    if n_rows is None:
        n_rows = total
    syn = np.zeros(int(n_rows), dtype=np.uint8)
    for r in range(int(n_rows)):
        s = 0
        for v in indices[indptr[r]:indptr[r + 1]]:
            s ^= int(bits[int(v)])
        syn[r] = np.uint8(s & 1)
    return syn


def verify_syndrome(indptr: np.ndarray, indices: np.ndarray,
                    bits: np.ndarray, observed: np.ndarray) -> tuple[bool, int]:
    recomputed = syndrome_compute(indptr, indices, bits, len(observed))
    observed = np.asarray(observed, dtype=np.uint8)
    mismatch = int(np.count_nonzero(recomputed != observed))
    return bool(mismatch == 0), mismatch


def bits_per_symbol_from_Q(n_Q: int) -> int:
    bps = int(round(float(np.log2(int(n_Q)))))
    if 2 ** bps != int(n_Q):
        raise ValueError("Q must be a power of two")
    return bps


def symbols_to_bits(symbols: np.ndarray, bps: int) -> np.ndarray:
    syms = np.asarray(symbols, dtype=np.int32)
    n = len(syms)
    out = np.zeros(n * bps, dtype=np.uint8)
    for i, s in enumerate(syms):
        for b in range(bps):
            out[i * bps + b] = np.uint8((int(s) >> b) & 1)
    return out


def bits_to_symbols(bits: np.ndarray, bps: int) -> np.ndarray:
    bits = np.asarray(bits, dtype=np.uint8)
    n = len(bits) // bps
    out = np.zeros(n, dtype=np.int32)
    for i in range(n):
        s = 0
        for b in range(bps):
            s |= int(bits[i * bps + b]) << b
        out[i] = s
    return out


def candidate_tag(hard_bits: np.ndarray) -> bytes:
    bits = np.asarray(hard_bits, dtype=np.uint8)
    return hashlib.sha256(bits.tobytes()).digest()[:8]


def available_iterations(total_used: int, per_ckpt: int = MAX_ITER_PER_CHECKPOINT,
                         max_total: int = MAX_TOTAL_ITERATIONS) -> int:
    return max(0, min(int(per_ckpt), int(max_total) - int(total_used)))


def _empty_arm(arm: str) -> dict:
    return {
        "arm": arm,
        "status": "NOT_ATTEMPTED",
        "attempted": False,
        "disclosed_rows": 0,
        "syndrome_bits_published": 0,
        "tag_bits_published": 0,
        "control_bits_sent": 0,
        "leak_IR_bits": 0,
        "total_public_bits": 0,
        "iterations_used": 0,
        "protocol_accepted": False,
        "verified_exact_success": False,
        "undetected": False,
        "oracle_exact": None,
        "raw_bit_errors": None,
        "raw_symbol_errors": None,
        "bit_errors": None,
        "symbol_errors": None,
        "elapsed_s": 0.0,
        "deadline_overrun": False,
        "per_checkpoint": [],
        "D": None,
        "error": None,
    }


def run_arm(arm: str, indptr: np.ndarray, indices: np.ndarray,
            alice_bits: np.ndarray, bob_symbols: np.ndarray,
            prior_logp: np.ndarray, syndrome_full: np.ndarray,
            reference_tag: bytes, decoder_fn,
            checkpoint_rows: tuple = CHECKPOINT_ROWS,
            max_iter_per_ckpt: int = MAX_ITER_PER_CHECKPOINT,
            max_total: int = MAX_TOTAL_ITERATIONS,
            deadline_s: float = ARM_BUDGET_S,
            clock=None, ce_ref: float | None = None) -> dict:
    indptr = np.asarray(indptr, dtype=np.int32)
    indices = np.asarray(indices, dtype=np.int32)
    alice_bits = np.asarray(alice_bits, dtype=np.uint8)
    bob_symbols = np.asarray(bob_symbols, dtype=np.int32)
    prior_logp = np.asarray(prior_logp, dtype=np.float64)
    syndrome_full = np.asarray(syndrome_full, dtype=np.uint8)
    nbit = len(alice_bits)
    n_checks = len(syndrome_full)
    n_Q = int(prior_logp.shape[1])
    bps = bits_per_symbol_from_Q(n_Q)
    n_sym = int(prior_logp.shape[0])
    if clock is None:
        clock = time.monotonic
    if nbit != n_sym * bps:
        raise ValueError("alice_bits length inconsistent with prior shape")
    if max(checkpoint_rows) > n_checks:
        raise ValueError("checkpoint ladder exceeds syndrome length")
    # D7 grouping mask from this arm's own CSR
    n_cols = nbit
    deg = col_degrees(indptr, indices, n_cols) if len(indices) else np.zeros(n_cols, dtype=np.int64)
    deg2_mask = (deg == 2)
    bob_bits = symbols_to_bits(bob_symbols, bps)
    alice_symbols = bits_to_symbols(alice_bits, bps)
    raw_bit = int(np.count_nonzero(bob_bits != alice_bits))
    raw_sym = int(np.count_nonzero(bob_symbols != alice_symbols))
    res = _empty_arm(arm)
    res["raw_bit_errors"] = raw_bit
    res["raw_symbol_errors"] = raw_sym
    started = float(clock())
    c2v = np.zeros(0, dtype=np.float64)
    prev_nnz = 0
    disclosed = 0
    total_used = 0
    last_hard = None
    first_f2b_sign = None
    first_app_sign = None
    overrun = False
    for ckpt_index, ckpt in enumerate(checkpoint_rows):
        ckpt = int(ckpt)
        remaining = available_iterations(total_used, max_iter_per_ckpt, max_total)
        elapsed_before = float(clock()) - started
        if remaining <= 0:
            res["status"] = "BUDGET_EXHAUSTED"
            break
        if elapsed_before >= float(deadline_s):
            res["status"] = "TIMEOUT"
            res["error"] = "arm deadline before checkpoint publication"
            break
        if not (ckpt > disclosed and ckpt <= n_checks):
            raise ValueError("checkpoint ladder must be strictly increasing and bounded")
        # D1 prefix recompute BEFORE decoder (M6 linkage: mismatch blocks decoder)
        true_prefix = syndrome_compute(indptr, indices, alice_bits, ckpt)
        d1_match = bool(np.array_equal(true_prefix, syndrome_full[:ckpt]))
        d1_mismatch = int(np.count_nonzero(true_prefix != syndrome_full[:ckpt]))
        if not d1_match:
            if ckpt_index:
                res["control_bits_sent"] += 1
            disclosed = ckpt
            res["disclosed_rows"] = disclosed
            res["syndrome_bits_published"] = disclosed
            if res["tag_bits_published"] == 0:
                res["tag_bits_published"] = 64
            res["attempted"] = True
            elapsed_after = float(clock()) - started
            res["per_checkpoint"].append({
                "checkpoint_rows": ckpt,
                "iterations": 0,
                "total_iterations": int(total_used),
                "residual": None,
                "converged": False,
                "finite": False,
                "max_llr": None,
                "syndrome_ok": False,
                "tag_checked": False,
                "tag_ok": False,
                "protocol_accepted": False,
                "elapsed_s": elapsed_after,
                "deadline_overrun": bool(elapsed_after > float(deadline_s)),
                "D1_match": False,
                "D1_mismatch_rows": d1_mismatch,
                "decoder_called": False,
            })
            res["status"] = "SYNDROME_MISMATCH"
            res["error"] = f"D1/M6 syndrome mismatch rows={d1_mismatch}"
            break
        if ckpt_index:
            res["control_bits_sent"] += 1
        disclosed = ckpt
        res["disclosed_rows"] = disclosed
        res["syndrome_bits_published"] = disclosed
        if res["tag_bits_published"] == 0:
            res["tag_bits_published"] = 64
        res["attempted"] = True
        active_nnz = int(indptr[ckpt])
        warm = np.zeros(active_nnz, dtype=np.float64)
        if prev_nnz:
            warm[:prev_nnz] = c2v[:prev_nnz]
        max_iter = available_iterations(total_used, max_iter_per_ckpt, max_total)
        residuals: list[float] = []
        completed = None
        try:
            got = decoder_fn(prior_logp, syndrome_full[:ckpt],
                             indptr=indptr[:ckpt + 1], indices=indices[:active_nnz],
                             max_iter=max_iter, warm_start_c2v=warm)
            residuals = [float(x) for x in got["residuals"]]
            if not residuals:
                raise ValueError("decoder returned empty residuals")
            completed = len(residuals)
            if completed > max_iter:
                raise ValueError("decoder returned too many iterations")
            if any((not np.isfinite(v)) or v < 0 for v in residuals):
                raise DecoderNumericError("non-finite residual trajectory")
            cand_c2v = np.asarray(got["check_to_variable"], dtype=np.float64)
            if cand_c2v.shape != (active_nnz,):
                raise ValueError("invalid active c2v shape")
            if not np.all(np.isfinite(cand_c2v)):
                raise DecoderNumericError("non-finite c2v")
            hard = np.asarray(got["hard_bits"], dtype=np.uint8)
            if hard.shape != (nbit,):
                raise ValueError("invalid hard_bits shape")
            observed = np.asarray(got["syndrome_observed"], dtype=np.uint8)
            syndrome_ok = bool(observed.shape == (ckpt,)
                               and np.array_equal(observed, syndrome_full[:ckpt]))
            max_llr = float(got.get("max_llr", float("nan")))
            if not np.isfinite(max_llr) or max_llr > LLR_CLIP + 1e-12:
                raise DecoderNumericError("max_llr non-finite or exceeds clip")
            app = np.asarray(got["app_llr"], dtype=np.float64)
            if app.shape != (nbit,) or not np.all(np.isfinite(app)):
                raise DecoderNumericError("app_llr non-finite")
            if float(np.max(np.abs(app))) > LLR_CLIP + 1e-12:
                raise DecoderNumericError("app_llr exceeds clip")
            f2b = np.asarray(got.get("factor_to_bit", np.zeros((n_sym, bps))), dtype=np.float64)
            if f2b.size != nbit:
                f2b = np.zeros(nbit, dtype=np.float64)
            else:
                f2b = f2b.reshape(nbit)
            finite = bool(got["finite"])
            tag_ok = bool(candidate_tag(hard) == reference_tag)
            accepted = bool(finite and syndrome_ok and tag_ok)
            elapsed_after = float(clock()) - started
            overrun = bool(elapsed_after > float(deadline_s))
            if overrun:
                res["deadline_overrun"] = True
            c2v = cand_c2v.copy()
            prev_nnz = active_nnz
            last_hard = hard.copy()
            total_used += completed
            # D scalars (wrapper only, no full arrays)
            hard_syms = bits_to_symbols(hard, bps)
            d2_sym_err = int(np.count_nonzero(hard_syms != bob_symbols))
            d3_bit_err = int(np.count_nonzero(hard != bob_bits))
            d4_finite = True
            d4_max = float(np.max(np.abs(app)))
            d4_mean = float(np.mean(app))
            d5_finite = True
            d5_max = float(np.max(np.abs(c2v))) if c2v.size else 0.0
            d5_resid = float(residuals[-1])
            f2b_finite = bool(np.all(np.isfinite(f2b)))
            if first_f2b_sign is None:
                first_f2b_sign = np.sign(f2b)
                first_app_sign = np.sign(app)
                n_flip_f2b = 0
                n_flip_app = 0
            else:
                n_flip_f2b = int(np.count_nonzero(np.sign(f2b) != first_f2b_sign))
                n_flip_app = int(np.count_nonzero(np.sign(app) != first_app_sign))
            app_abs = np.abs(app)
            if np.any(deg2_mask):
                d7_mean_deg2 = float(np.mean(app_abs[deg2_mask]))
            else:
                d7_mean_deg2 = 0.0
            if np.any(~deg2_mask):
                d7_mean_rest = float(np.mean(app_abs[~deg2_mask]))
            else:
                d7_mean_rest = 0.0
            d7_err_deg2 = int(np.count_nonzero(hard[deg2_mask] != bob_bits[deg2_mask])) if np.any(deg2_mask) else 0
            d7_err_rest = int(np.count_nonzero(hard[~deg2_mask] != bob_bits[~deg2_mask])) if np.any(~deg2_mask) else 0
            # D8 oracle posthoc (does not affect accept)
            oracle_exact = bool(np.array_equal(hard, alice_bits))
            undetected = bool(accepted and not oracle_exact)
            ckpt_log = {
                "checkpoint_rows": ckpt,
                "new_rows": int(ckpt - (checkpoint_rows[ckpt_index - 1] if ckpt_index else 0)),
                "disclosed_rows": int(disclosed),
                "syndrome_bits_published": int(res["syndrome_bits_published"]),
                "tag_bits_published": int(res["tag_bits_published"]),
                "control_bits_sent": int(res["control_bits_sent"]),
                "iterations": int(completed),
                "total_iterations": int(total_used),
                "residuals": residuals,
                "residual": float(residuals[-1]),
                "converged": bool(residuals[-1] < CONVERGENCE_TOL),
                "finite": bool(finite),
                "max_llr": max_llr,
                "syndrome_ok": bool(syndrome_ok),
                "tag_checked": True,
                "tag_ok": bool(tag_ok),
                "protocol_accepted": bool(accepted),
                "elapsed_s": elapsed_after,
                "deadline_overrun": bool(overrun),
                "D1_match": True,
                "D1_mismatch_rows": 0,
                "D2_sym_errors": d2_sym_err,
                "D2_sym_match": bool(d2_sym_err == 0),
                "D3_bit_errors": d3_bit_err,
                "D4_finite": d4_finite,
                "D4_max_abs": d4_max,
                "D4_mean": d4_mean,
                "D5_finite": d5_finite,
                "D5_max_abs": d5_max,
                "D5_residual": d5_resid,
                "D5_iters": int(completed),
                "D6_f2b_finite": f2b_finite,
                "D6_n_flip_f2b": int(n_flip_f2b),
                "D6_n_flip_app": int(n_flip_app),
                "D7_bit_errors_deg2": int(d7_err_deg2),
                "D7_bit_errors_rest": int(d7_err_rest),
                "D7_mean_abs_app_deg2": float(d7_mean_deg2),
                "D7_mean_abs_app_rest": float(d7_mean_rest),
                "D8_alice_vs_bob_bit": int(raw_bit),
                "D8_alice_vs_bob_sym": int(raw_sym),
                "D8_oracle_exact": bool(oracle_exact),
                "D8_undetected": bool(undetected),
                "decoder_called": True,
            }
            res["per_checkpoint"].append(ckpt_log)
            if accepted:
                res["status"] = "VERIFIED_DEADLINE_OVERRUN" if overrun else "VERIFIED"
                res["protocol_accepted"] = True
                break
            if not finite:
                res["status"] = "NUMERIC_FAILURE"
                res["error"] = "decoder returned finite=false"
                break
            if elapsed_after > float(deadline_s):
                res["status"] = "TIMEOUT"
                res["error"] = "arm deadline after checkpoint"
                break
            if total_used >= int(max_total):
                res["status"] = ("LADDER_EXHAUSTED"
                                 if ckpt == int(checkpoint_rows[-1]) else "BUDGET_EXHAUSTED")
                break
        except Exception as exc:  # noqa: BLE001 - terminal status mapping
            elapsed_after = float(clock()) - started
            if isinstance(exc, DecoderNumericError):
                res["status"] = "NUMERIC_FAILURE"
            elif res.get("status") in (None, "NOT_ATTEMPTED"):
                res["status"] = "DECODER_ERROR"
            if res["status"] == "NOT_ATTEMPTED":
                res["status"] = "DECODER_ERROR"
            if elapsed_after > float(deadline_s):
                res["deadline_overrun"] = True
            res["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            res["per_checkpoint"].append({
                "checkpoint_rows": ckpt,
                "new_rows": int(ckpt - (checkpoint_rows[ckpt_index - 1] if ckpt_index else 0)),
                "disclosed_rows": int(disclosed),
                "syndrome_bits_published": int(res["syndrome_bits_published"]),
                "tag_bits_published": int(res["tag_bits_published"]),
                "control_bits_sent": int(res["control_bits_sent"]),
                "iterations": completed,
                "iterations_known": completed is not None,
                "total_iterations": int(total_used),
                "residuals": residuals,
                "residual": residuals[-1] if residuals else None,
                "converged": False,
                "finite": False,
                "max_llr": None,
                "syndrome_ok": False,
                "tag_checked": False,
                "tag_ok": False,
                "protocol_accepted": False,
                "elapsed_s": elapsed_after,
                "deadline_overrun": bool(elapsed_after > float(deadline_s)),
                "D1_match": True,
                "D1_mismatch_rows": 0,
                "decoder_called": True,
            })
            break
    else:
        res["status"] = "LADDER_EXHAUSTED"
    res["iterations_used"] = int(total_used)
    res["elapsed_s"] = float(clock()) - started
    res["deadline_overrun"] = bool(res["deadline_overrun"] or overrun)
    if res["status"] == "NOT_ATTEMPTED":
        res["status"] = "LADDER_EXHAUSTED"
    # leakage accounting (published only, never rolled back)
    res["leak_IR_bits"] = int(res["syndrome_bits_published"] + res["tag_bits_published"])
    res["total_public_bits"] = int(res["leak_IR_bits"] + res["control_bits_sent"])
    # oracle posthoc on last hard only
    if last_hard is not None:
        res["oracle_exact"] = bool(np.array_equal(last_hard, alice_bits))
        res["bit_errors"] = int(np.count_nonzero(last_hard != alice_bits))
        res["symbol_errors"] = int(np.count_nonzero(
            bits_to_symbols(last_hard, bps) != alice_symbols))
        res["verified_exact_success"] = bool(res["protocol_accepted"] and res["oracle_exact"])
        res["undetected"] = bool(res["protocol_accepted"] and not res["oracle_exact"])
    if ce_ref is not None and np.isfinite(ce_ref) and ce_ref > 0 and res["attempted"]:
        denom = float(n_sym * ce_ref)
        res["f_model_relative"] = res["leak_IR_bits"] / denom
        res["f_public_model_relative"] = res["total_public_bits"] / denom
    else:
        res["f_model_relative"] = None
        res["f_public_model_relative"] = None
    # final D rollup (scalars only)
    if res["per_checkpoint"]:
        last = res["per_checkpoint"][-1]
        res["D"] = {k: last.get(k) for k in list(last.keys()) if k.startswith("D")}
    return res


def compare_baseline_A(arm_A: dict, lambda_meas: float, ce_meas: float) -> tuple[bool, dict]:
    diffs: dict = {}
    diffs["checkpoints"] = (len(arm_A.get("per_checkpoint", [])), BLOCK0_BASELINE["checkpoints"])
    diffs["iterations"] = (int(arm_A.get("iterations_used", -1)), BLOCK0_BASELINE["iterations"])
    diffs["status"] = (arm_A.get("status"), BLOCK0_BASELINE["status"])
    diffs["bit_errors"] = (arm_A.get("bit_errors"), BLOCK0_BASELINE["bit_errors"])
    diffs["symbol_errors"] = (arm_A.get("symbol_errors"), BLOCK0_BASELINE["symbol_errors"])
    diffs["syndrome_bits"] = (int(arm_A.get("syndrome_bits_published", -1)), BLOCK0_BASELINE["syndrome_bits"])
    diffs["tag_bits"] = (int(arm_A.get("tag_bits_published", -1)), BLOCK0_BASELINE["tag_bits"])
    diffs["control_bits"] = (int(arm_A.get("control_bits_sent", -1)), BLOCK0_BASELINE["control_bits"])
    lam_ok = bool(lambda_meas == EXPECTED_LAMBDA)
    ce_ok = bool(abs(float(ce_meas) - EXPECTED_CE) <= CE_TOL)
    diffs["lambda_exact"] = (repr(lambda_meas), repr(EXPECTED_LAMBDA), lam_ok)
    diffs["ce_tol"] = (repr(ce_meas), repr(EXPECTED_CE), ce_ok)
    ok = bool(
        diffs["checkpoints"][0] == diffs["checkpoints"][1]
        and diffs["iterations"][0] == diffs["iterations"][1]
        and diffs["status"][0] == diffs["status"][1]
        and diffs["bit_errors"][0] == diffs["bit_errors"][1]
        and diffs["symbol_errors"][0] == diffs["symbol_errors"][1]
        and diffs["syndrome_bits"][0] == diffs["syndrome_bits"][1]
        and diffs["tag_bits"][0] == diffs["tag_bits"][1]
        and diffs["control_bits"][0] == diffs["control_bits"][1]
        and lam_ok and ce_ok
    )
    return ok, diffs


def _git_head() -> str:
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=str(REPO_ROOT), text=True).strip()
    except Exception as exc:
        raise RuntimeError("cannot bind runtime to git HEAD") from exc
    if len(head) != 40:
        raise RuntimeError("git HEAD is not a 40-character commit SHA")
    return head


def _json_default(v):
    if isinstance(v, (np.integer, np.floating, np.bool_)):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, bytes):
        return v.hex()
    raise TypeError(type(v).__name__)


def build_manifest(registry: dict | None, session: dict | None,
                   cal_ids: list[int] | None, model: dict | None,
                   git_head: str | None, command: str,
                   fatal_error: str | None) -> dict:
    return {
        "schema": "v72p2d1_parity_layout_ab_manifest_v1",
        "cycle_id": "V72P2D1-PARITY",
        "git_head": git_head,
        "seed_colmap": SEED_COLMAP,
        "seed_domain": "diagnostic-only col_map; never reused from V72P1/V72P2/CAL",
        "col_map": f"[1204:10239]=1204+permutation(9035) rng=default_rng({SEED_COLMAP})",
        "registry_schema": (registry or {}).get("schema"),
        "data_sha": (registry or {}).get("data_sha"),
        "session_id": (session or {}).get("session_id"),
        "source_label": (session or {}).get("source_label"),
        "cal_frame_ids": cal_ids,
        "val_block_frames": list(VAL_BLOCK_FRAMES),
        "data_roles": {"CAL": "fit_and_select_once_shared", "VAL": "non_fresh_descriptive_block0"},
        "model": {k: v for k, v in (model or {}).items() if k != "Ps_full"},
        "decoder": {
            "checkpoint_rows": list(CHECKPOINT_ROWS),
            "max_iter_per_checkpoint": MAX_ITER_PER_CHECKPOINT,
            "max_total_iterations": MAX_TOTAL_ITERATIONS,
            "llr_clip": LLR_CLIP,
            "convergence_tol": CONVERGENCE_TOL,
            "dtype": "float64",
            "tag_bits": 64,
            "order": "A-then-B serial, zero c2v per arm, in-arm carry only",
        },
        "budgets": {"arm_seconds": ARM_BUDGET_S, "invocation_seconds": GLOBAL_BUDGET_S},
        "command": command,
        "non_fresh": True,
        "no_run_01": True,
        "fatal_error": fatal_error,
    }


def build_results(arm_A: dict, arm_B: dict, mech: dict | None,
                  lambda_meas, ce_meas, baseline_diffs: dict | None,
                  fatal_error: str | None, elapsed: float | None) -> dict:
    return {
        "schema": "v72p2d1_parity_layout_ab_results_v1",
        "lifecycle": "DEVELOPMENT_EXECUTION / DESCRIPTIVE_ONLY",
        "overall": ("COMPLETED" if not fatal_error
                    and arm_A.get("attempted") and arm_B.get("attempted")
                    and arm_A.get("status") not in ("NOT_ATTEMPTED",)
                    and arm_B.get("status") not in ("NOT_ATTEMPTED",) else "INCOMPLETE"),
        "fatal_error": fatal_error,
        "invocation_elapsed_s": elapsed,
        "expected_lambda": EXPECTED_LAMBDA,
        "measured_lambda": lambda_meas,
        "expected_ce_log2": EXPECTED_CE,
        "measured_ce_log2": ce_meas,
        "expected_four_cycles": EXPECTED_FOUR,
        "expected_collisions": EXPECTED_COLL,
        "mechanical": mech,
        "baseline_diffs": baseline_diffs,
        "arms": [arm_A, arm_B],
    }


def write_terminal_outputs(out_dir: Path, manifest: dict, results: dict) -> None:
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError(f"output directory already exists: {out_dir}")
    out_dir.mkdir(parents=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    (out_dir / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    fields = ["arm", "status", "attempted", "disclosed_rows", "syndrome_bits_published",
              "tag_bits_published", "control_bits_sent", "leak_IR_bits", "total_public_bits",
              "iterations_used", "elapsed_s", "protocol_accepted", "verified_exact_success",
              "undetected", "oracle_exact", "raw_bit_errors", "raw_symbol_errors",
              "bit_errors", "symbol_errors", "f_model_relative", "f_public_model_relative", "error"]
    with (out_dir / "table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for arm in results["arms"]:
            writer.writerow({k: arm.get(k) for k in fields})
    arms = results["arms"]
    lines = [
        "# V72P2D1 parity-layout diagnostic (A/B)",
        "",
        "Descriptive only; not FER/SKR/qualification/promotion.",
        "",
        f"- overall: `{results['overall']}`",
        f"- fatal_error: `{results['fatal_error']}`",
        f"- A: `{arms[0]['status']}` iters={arms[0]['iterations_used']} "
        f"bit={arms[0]['bit_errors']} sym={arms[0]['symbol_errors']}",
        f"- B: `{arms[1]['status']}` iters={arms[1]['iterations_used']} "
        f"bit={arms[1]['bit_errors']} sym={arms[1]['symbol_errors']}",
        f"- lambda measured={results['measured_lambda']} expected={EXPECTED_LAMBDA}",
        f"- CE measured={results['measured_ce_log2']} expected={EXPECTED_CE}",
        f"- block0 baseline: 72ckpt/334iter/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71",
    ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    got = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    if got != ["manifest.json", "report.md", "results.json", "table.csv"]:
        raise RuntimeError(f"terminal output must be exactly four files, got {got}")


def execute_diagnostic(registry_path, session_id: str, out_dir,
                       arm_budget_s: float = ARM_BUDGET_S,
                       global_budget_s: float = GLOBAL_BUDGET_S,
                       decoder_fn=None, injected: dict | None = None,
                       clock=None) -> int:
    """Full diagnostic. `injected` supplies fake {mother, cal, val, model} for tests."""
    out_path = Path(out_dir) if Path(out_dir).is_absolute() else REPO_ROOT / out_dir
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    if clock is None:
        clock = time.monotonic
    invocation_started = float(clock())
    command = " ".join(sys.argv)
    fatal_error: str | None = None
    # workspace temp for running candidates (never counted toward final four)
    ws_root = REPO_ROOT / "workspace"
    try:
        ws_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    tmp_dir = Path(tempfile.mkdtemp(prefix="v72p2d1_", dir=str(ws_root)))
    (tmp_dir / "candidate_note.json").write_text(
        json.dumps({"note": "running candidates live here; not final outputs"}), encoding="utf-8")
    try:
        git_head: str | None = None
        try:
            git_head = _git_head()
        except Exception:
            git_head = None
        registry = session = None
        cal_ids: list[int] | None = None
        model = None
        lambda_meas = None
        ce_meas = None
        mech = None
        baseline_diffs = None
        arm_A = _empty_arm("A")
        arm_B = _empty_arm("B")
        decoder_calls = {"n": 0}

        def counting_decoder(prior, target, indptr=None, indices=None,
                             max_iter=10, warm_start_c2v=None):
            decoder_calls["n"] += 1
            fn = decoder_fn or get_adapter_decoder()
            return fn(prior, target, indptr=indptr, indices=indices,
                      max_iter=max_iter, warm_start_c2v=warm_start_c2v)

        if injected is not None:
            # fake path for tests: no real registry/parquet/decoder-default read
            indptr_A = np.asarray(injected["indptr_A"], dtype=np.int32)
            indices_A = np.asarray(injected["indices_A"], dtype=np.int32)
            alice_bits = np.asarray(injected["alice_bits"], dtype=np.uint8)
            bob_symbols = np.asarray(injected["bob_symbols"], dtype=np.int32)
            prior_logp = np.asarray(injected["prior_logp"], dtype=np.float64)
            lambda_meas = injected.get("lambda")
            ce_meas = injected.get("ce")
            cal_ok = bool(injected.get("cal_ok", True))
            registry = injected.get("registry", {"schema": "fake", "data_sha": "fake"})
            session = injected.get("session", {"session_id": session_id, "source_label": "fake"})
            cal_ids = injected.get("cal_ids", list(range(CAL_START, CAL_STOP)))
            model = {"selected_lambda": lambda_meas, "ce_ref_log2": ce_meas}
            # B4: fake path must never fall back to the real decoder.
            fake_decoder = injected.get("decoder_fn")
            if fake_decoder is None:
                raise RuntimeError("fake path requires injected decoder_fn; "
                                   "refusing real-decoder fallback")

            def counting_decoder(prior, target, indptr=None, indices=None,  # noqa: F811
                                 max_iter=10, warm_start_c2v=None):
                decoder_calls["n"] += 1
                return fake_decoder(prior, target, indptr=indptr, indices=indices,
                                    max_iter=max_iter, warm_start_c2v=warm_start_c2v)
            n_cols_fake = int(max(int(indices_A.max()) + 1, len(alice_bits)))
            if n_cols_fake == NBIT:
                col_map = build_col_map(NBIT)
            else:
                # tiny fake permutation: keep first/last fixed, permute middle deterministically
                col_map = np.arange(n_cols_fake, dtype=np.int64)
                if n_cols_fake > 2:
                    rng = np.random.default_rng(SEED_COLMAP)
                    mid = n_cols_fake - 2
                    col_map[1:n_cols_fake - 1] = 1 + rng.permutation(mid)
            indptr_B, indices_B = build_B_csr(indptr_A, indices_A, col_map)
            if not cal_ok:
                arm_A = _empty_arm("A")
                arm_A["error"] = "cal_failed"
                arm_B = _empty_arm("B")
                arm_B["error"] = "cal_failed"
                fatal_error = "CAL_FAILED"
                manifest = build_manifest(registry, session, cal_ids, model, git_head,
                                          command, fatal_error)
                results = build_results(arm_A, arm_B, None, lambda_meas, ce_meas,
                                        None, fatal_error, float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            # mechanical check on fake graphs with recomputed expectations when requested
            exp_four = injected.get("expected_four", EXPECTED_FOUR)
            exp_coll = injected.get("expected_coll", EXPECTED_COLL)
            mech = verify_M1_M7_fake(indptr_A, indices_A, indptr_B, indices_B,
                                     col_map, n_cols_fake, exp_four, exp_coll,
                                     check_degrees=injected.get("check_degrees", False))
            if not mech["pass"]:
                arm_A["error"] = "m_failed"
                arm_B["error"] = "m_failed"
                fatal_error = "M_FAILED"
                manifest = build_manifest(registry, session, cal_ids, model, git_head,
                                          command, fatal_error)
                results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                        None, fatal_error, float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            syn_A = syndrome_compute(indptr_A, indices_A, alice_bits)
            syn_B = syndrome_compute(indptr_B, indices_B, alice_bits)
            if injected.get("cross_syndrome"):
                syn_B = syn_A.copy()
            tag = candidate_tag(alice_bits)
            ckpts = injected.get("checkpoint_rows", (2, 4))
            mt = injected.get("max_total", 8)
            mp = injected.get("max_iter_per_ckpt", 4)
            arm_A = run_arm("A", indptr_A, indices_A, alice_bits, bob_symbols,
                            prior_logp, syn_A, tag, counting_decoder,
                            checkpoint_rows=ckpts, max_iter_per_ckpt=mp, max_total=mt,
                            deadline_s=float(arm_budget_s), clock=clock, ce_ref=ce_meas)
            (tmp_dir / "candidate_arm_A.json").write_text(
                json.dumps({"arm": "A", "status": arm_A["status"]}), encoding="utf-8")
            # A-gate-B: numeric/timeout/syndrome-mismatch or explicit baseline
            # mismatch stops B. Frozen lambda-exact / CE-tol refs gate B only
            # when the caller opts in via enforce_frozen_refs (S8); other fake
            # tests use tiny lambdas and must not be gated on frozen refs.
            enforce_refs = bool(injected.get("enforce_frozen_refs", False))
            lam_ok = True
            ce_ok = True
            if enforce_refs:
                lam_ok = (lambda_meas == EXPECTED_LAMBDA) if isinstance(lambda_meas, float) else False
                try:
                    ce_ok = bool(abs(float(ce_meas) - EXPECTED_CE) <= CE_TOL)
                except Exception:
                    ce_ok = False
            base_ok = bool(injected.get("baseline_ok", True)) and bool(lam_ok) and bool(ce_ok)
            if arm_A["status"] in ("NUMERIC_FAILURE", "DECODER_ERROR", "TIMEOUT",
                                   "BUDGET_EXHAUSTED", "SYNDROME_MISMATCH") or not base_ok:
                arm_B = _empty_arm("B")
                arm_B["error"] = "gate_stopped_by_A"
                fatal_error = f"A_GATE_{arm_A['status']}" if not base_ok or arm_A["status"] != "LADDER_EXHAUSTED" else None
                if not base_ok:
                    fatal_error = "A_BASELINE_MISMATCH"
                elif arm_A["status"] not in ("LADDER_EXHAUSTED", "VERIFIED"):
                    fatal_error = f"A_GATE_{arm_A['status']}"
                else:
                    fatal_error = "A_GATE_BASELINE_MISMATCH"
            else:
                if float(clock()) - invocation_started >= float(global_budget_s):
                    arm_B = _empty_arm("B")
                    arm_B["error"] = "gate_stopped_by_A"
                    fatal_error = "GLOBAL_TIMEOUT_BEFORE_B"
                else:
                    arm_B = run_arm("B", indptr_B, indices_B, alice_bits, bob_symbols,
                                    prior_logp, syn_B, tag, counting_decoder,
                                    checkpoint_rows=ckpts, max_iter_per_ckpt=mp, max_total=mt,
                                    deadline_s=float(arm_budget_s), clock=clock, ce_ref=ce_meas)
                    (tmp_dir / "candidate_arm_B.json").write_text(
                        json.dumps({"arm": "B", "status": arm_B["status"]}), encoding="utf-8")
            manifest = build_manifest(registry, session, cal_ids, model, git_head,
                                      command, fatal_error)
            results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                    None, fatal_error, float(clock()) - invocation_started)
            write_terminal_outputs(out_path, manifest, results)
            _cleanup_tmp_dir(tmp_dir)
            return 0 if not fatal_error else 1
        # ---- real path (B1): CAL702..1725 hierarchical_P/select_lambda once,
        # VAL1726-1729 b -> s_A/s_B, shared natural_log prior, real CSR decoder,
        # compare_baseline_A gate. Out-exists refusal + budgets preserved. ----
        try:
            v72p2 = _load_v72p2()
            registry, registry_file = v72p2.load_registry(registry_path)
            session = v72p2.select_1m_session(registry)
            if session.get("session_id") != session_id:
                raise DataValidationError("session argument does not match frozen 1M session")
            cal_ids, val_block = check_assigned_v72p2d1(session)
            pairs_path = (REPO_ROOT / session["provenance"]
                          if not str(session["provenance"]).startswith("/")
                          else Path(str(session["provenance"])))
            frame, read_mode = v72p2.read_selected_pairs(
                pairs_path, list(cal_ids) + list(val_block))
            cal_frames, cal_errors = v72p2.validate_selected_frames(frame, cal_ids)
            if cal_errors:
                raise DataValidationError(
                    f"invalid CAL frame: {next(iter(cal_errors.values()))}")
            val_frames, val_errors = v72p2.validate_selected_frames(frame, val_block)
            if val_errors or any(fid not in val_frames for fid in val_block):
                arm_A["error"] = "val_invalid"
                arm_B["error"] = "val_invalid"
                fatal_error = "VAL_INVALID"
                manifest = build_manifest(registry, session, cal_ids, None,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, None, None, None, None,
                                        fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            a_cal = np.concatenate([cal_frames[fid]["alice_symbols"] for fid in cal_ids])
            b_cal = np.concatenate([cal_frames[fid]["bob_symbols"] for fid in cal_ids])
            try:
                model_full = v72p2.fit_full_cal_model(a_cal, b_cal)
            except Exception as exc:
                arm_A["error"] = "cal_failed"
                arm_B["error"] = "cal_failed"
                fatal_error = f"CAL_FAILED: {type(exc).__name__}"
                manifest = build_manifest(registry, session, cal_ids, None,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, None, None, None, None,
                                        fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            lambda_meas = float(model_full["selected_lambda"])
            ce_meas = float(model_full["ce_ref_log2"])
            model = {k: v for k, v in model_full.items() if k != "Ps_full"}
            if not (np.isfinite(lambda_meas) and np.isfinite(ce_meas) and ce_meas > 0):
                arm_A["error"] = "cal_failed"
                arm_B["error"] = "cal_failed"
                fatal_error = "CAL_FAILED"
                manifest = build_manifest(registry, session, cal_ids, model,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, None, lambda_meas, ce_meas,
                                        None, fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            _m = get_mother_csr()
            indptr_A = np.asarray(_m[0], dtype=np.int32)
            indices_A = np.asarray(_m[1], dtype=np.int32)
            col_map = build_col_map(NBIT)
            indptr_B, indices_B = build_B_csr(indptr_A, indices_A, col_map)
            mech = verify_M1_M7(indptr_A, indices_A, indptr_B, indices_B, col_map)
            if not mech["pass"]:
                arm_A["error"] = "m_failed"
                arm_B["error"] = "m_failed"
                fatal_error = "M_FAILED"
                manifest = build_manifest(registry, session, cal_ids, model,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                        None, fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
                return 1
            alice_symbols, bob_symbols = v72p2.assemble_frame_group(val_frames, val_block)
            alice_bits = symbols_to_bits(alice_symbols, bits_per_symbol_from_Q(Q))
            if alice_bits.shape != (NBIT,):
                raise DataValidationError("VAL block bits have unexpected shape")
            syn_A = syndrome_compute(indptr_A, indices_A, alice_bits)
            syn_B = syndrome_compute(indptr_B, indices_B, alice_bits)
            prior_logp = v72p2.build_prior_logp(bob_symbols, model_full["Ps_full"])
            tag = candidate_tag(alice_bits)
            real_decoder = decoder_fn or get_adapter_decoder()

            def counting_real(prior, target, indptr=None, indices=None,
                              max_iter=10, warm_start_c2v=None):
                decoder_calls["n"] += 1
                return real_decoder(prior, target, indptr=indptr, indices=indices,
                                    max_iter=max_iter, warm_start_c2v=warm_start_c2v)

            arm_A = run_arm("A", indptr_A, indices_A, alice_bits, bob_symbols,
                            prior_logp, syn_A, tag, counting_real,
                            checkpoint_rows=CHECKPOINT_ROWS,
                            max_iter_per_ckpt=MAX_ITER_PER_CHECKPOINT,
                            max_total=MAX_TOTAL_ITERATIONS,
                            deadline_s=float(arm_budget_s), clock=clock,
                            ce_ref=ce_meas)
            (tmp_dir / "candidate_arm_A.json").write_text(
                json.dumps({"arm": "A", "status": arm_A["status"]}), encoding="utf-8")
            base_ok, baseline_diffs = compare_baseline_A(arm_A, lambda_meas, ce_meas)
            if not base_ok:
                arm_B = _empty_arm("B")
                arm_B["error"] = "gate_stopped_by_A"
                fatal_error = "A_BASELINE_MISMATCH"
            elif float(clock()) - invocation_started >= float(global_budget_s):
                arm_B = _empty_arm("B")
                arm_B["error"] = "gate_stopped_by_A"
                fatal_error = "GLOBAL_TIMEOUT_BEFORE_B"
            else:
                arm_B = run_arm("B", indptr_B, indices_B, alice_bits, bob_symbols,
                                prior_logp, syn_B, tag, counting_real,
                                checkpoint_rows=CHECKPOINT_ROWS,
                                max_iter_per_ckpt=MAX_ITER_PER_CHECKPOINT,
                                max_total=MAX_TOTAL_ITERATIONS,
                                deadline_s=float(arm_budget_s), clock=clock,
                                ce_ref=ce_meas)
                (tmp_dir / "candidate_arm_B.json").write_text(
                    json.dumps({"arm": "B", "status": arm_B["status"]}), encoding="utf-8")
            manifest = build_manifest(registry, session, cal_ids, model, git_head,
                                      command, fatal_error)
            results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                    baseline_diffs,
                                    fatal_error, float(clock()) - invocation_started)
            write_terminal_outputs(out_path, manifest, results)
            _cleanup_tmp_dir(tmp_dir)
            return 0 if not fatal_error else 1
        except (FileExistsError, DataValidationError, DecoderNumericError) as exc:
            # B5: real-path terminal failures land exactly four files.
            if out_path.exists():
                raise
            fatal_error = fatal_error or f"{type(exc).__name__}: {str(exc)[:300]}"
            try:
                manifest = build_manifest(registry, session, cal_ids, model,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                        baseline_diffs, fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
            except Exception:
                pass
            return 1
        except Exception as exc:  # noqa: BLE001 - terminal four-file fallback
            if out_path.exists():
                raise
            fatal_error = f"{type(exc).__name__}: {str(exc)[:300]}"
            try:
                manifest = build_manifest(registry, session, cal_ids, model,
                                          git_head, command, fatal_error)
                results = build_results(arm_A, arm_B, mech, lambda_meas, ce_meas,
                                        baseline_diffs, fatal_error,
                                        float(clock()) - invocation_started)
                write_terminal_outputs(out_path, manifest, results)
                _cleanup_tmp_dir(tmp_dir)
            except Exception:
                pass
            return 1
    except Exception:
        # Outer guard (B5): fake-path programmer errors (incl. B4 missing fake
        # decoder) propagate with no terminal files; workspace temp is removed
        # so candidate snapshots never leak. Real-path terminals already landed
        # inside; this only cleans tmp for propagated errors.
        _cleanup_tmp_dir(tmp_dir)
        raise


# B5: single terminal writer. _write_four is a thin alias so legacy call sites
# keep working; report content is unified in write_terminal_outputs.
def _write_four(out_path: Path, manifest: dict, results: dict) -> None:
    return write_terminal_outputs(Path(out_path), manifest, results)


def verify_M1_M7_fake(indptr_A, indices_A, indptr_B, indices_B, col_map,
                      n_cols: int, expected_four: int, expected_coll: int,
                      check_degrees: bool = False) -> dict:
    """Mechanical verification for arbitrary-size (fake) graphs.

    When check_degrees is False (fake tiny graphs), M2 checks only that A/B
    row-degree distributions agree instead of the frozen 9036 mother values.
    """
    indptr_A = np.asarray(indptr_A, dtype=np.int32)
    indices_A = np.asarray(indices_A, dtype=np.int32)
    indptr_B = np.asarray(indptr_B, dtype=np.int32)
    indices_B = np.asarray(indices_B, dtype=np.int32)
    col_map = np.asarray(col_map, dtype=np.int64)
    out: dict = {}
    out["M1"] = bool(indptr_A.shape == indptr_B.shape
                      and len(indices_A) == len(indices_B)
                      and len(indptr_A) - 1 > 0)
    if check_degrees:
        dist_B = check_degree_dist(indptr_B)
        out["M2"] = bool(dist_B == {4: 1, 5: 4594, 6: 4441})
        out["check_degree_B"] = {str(k): int(v) for k, v in dist_B.items()}
    else:
        out["M2"] = bool(check_degree_dist(indptr_A) == check_degree_dist(indptr_B))
    deg_A = col_degrees(indptr_A, indices_A, n_cols)
    deg_B = col_degrees(indptr_B, indices_B, n_cols)
    out["deg2_A"] = int(np.count_nonzero(deg_A == 2))
    out["deg2_B"] = int(np.count_nonzero(deg_B == 2))
    out["M3"] = bool(np.array_equal(np.sort(deg_A), np.sort(deg_B)))
    # M4: col_map must be a permutation (bijection) of 0..n_cols-1
    out["M4"] = bool(set(col_map.tolist()) == set(range(n_cols)) and len(col_map) == n_cols)
    out["M5"] = bool(np.array_equal(indptr_A, indptr_B)
                     and np.array_equal(indices_B, col_map[np.asarray(indices_A, dtype=np.int64)]))
    out["M6_independent"] = bool(indptr_A is not indptr_B and indices_A is not indices_B)
    four_A = count_four_cycles(indptr_A, indices_A)
    coll_A = count_collisions(indptr_A, indices_A)
    four_B = count_four_cycles(indptr_B, indices_B)
    coll_B = count_collisions(indptr_B, indices_B)
    out["four_A"] = int(four_A)
    out["coll_A"] = int(coll_A)
    out["four_B"] = int(four_B)
    out["coll_B"] = int(coll_B)
    out["M7"] = bool(four_A == expected_four and coll_A == expected_coll
                     and four_B == expected_four and coll_B == expected_coll)
    out["pass"] = bool(out["M1"] and out["M2"] and out["M3"] and out["M4"]
                       and out["M5"] and out["M6_independent"] and out["M7"])
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--out", default=FROZEN_OUT)
    parser.add_argument("--arm-budget-s", type=float, default=ARM_BUDGET_S)
    parser.add_argument("--global-budget-s", type=float, default=GLOBAL_BUDGET_S)
    args = parser.parse_args(argv)
    out_path = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out_path.exists():
        print(f"refused: output directory already exists: {out_path}", file=sys.stderr)
        return 2
    try:
        return execute_diagnostic(args.registry, args.session, args.out,
                                  arm_budget_s=float(args.arm_budget_s),
                                  global_budget_s=float(args.global_budget_s))
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
