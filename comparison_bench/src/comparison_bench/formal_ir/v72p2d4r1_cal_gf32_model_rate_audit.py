"""V72P2D4R1 CAL GF32 model rate audit — compliant frame-blocked nested CV.

CAL-only, frame-blocked 4-fold nested (outer F0..F3 each 256 frames,
TRAIN 768 / TEST 256; TRAIN inner 3 deterministic folds, no shuffle).
Models M0-M2 closed + M3 direct EXIT. No VAL fit, no decoder call,
no parquet VAL read, single audit output only.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

Q = 1024
Q_SUB = 32
N = 1024
FRAME_PAIRS = 256
CAL_START = 702
CAL_END = 1725
SESSION_ID = "20260123_1M_600k_0dB"
CYCLE_ID = "V72P2D4R1-CAL-GF32-MODEL-RATE"
AUDIT_SCHEMA = "v72p2d4r1_cal_gf32_model_rate_audit_v1"
MANIFEST_SCHEMA = "v72p2d4r1_cal_gf32_model_rate_manifest_v1"
OUT_DIR_NAME = "v72p2d4r1_cal_gf32_model_rate_audit_20260905"
REGISTRY_SCHEMA = "v72p2d3_real_registry_v1"
REQUIRED_PARQUET_COLUMNS = ("frame_id", "pair_idx", "alice_symbol", "bob_symbol")
# Outer frame-blocked folds: each 256 consecutive frames.
F0 = tuple(range(702, 958))
F1 = tuple(range(958, 1214))
F2 = tuple(range(1214, 1470))
F3 = tuple(range(1470, 1726))
OUTER_FOLDS = (F0, F1, F2, F3)
N_FOLDS = 4
N_INNER = 3
# Math contracts (frozen).
FLOOR = 1e-300
NORM_TOL = 1e-12
CHAIN_TOL = 1e-10
# Models (frozen).
M1_LAM = 1.0
LAMBDA_GRID = tuple(float(v) for v in np.logspace(-2.0, 3.0, 30))
M3_STATUS = "M3_EXIT_AMBIGUOUS"
UNIFORM_CE = 10.0
# R5 synthetic fixture repro (same fixture, formula caliber only).
R5_SEED = 20260905
R5_N = 4096
R5_LAM = 1.0
R5_REF_L1 = 6.422161237462124
R5_REF_L2 = 5.083351288530697
R5_REF_JOINT = 11.50551252599282
R5_TOL = 1e-6
# Selection (frozen): mean minimal + delta simple priority + stability.
SELECT_DELTA = 0.02
STABILITY_STD = 0.10
STABILITY_RANGE = 0.20
MODEL_ORDER = ("M0", "M1", "M2")
# Budget (frozen): N symbols/block, f grid, rows=ceil(N*CE*f/5).
F_LIST = (1.0, 1.1, 1.2, 1.3)
H1_BITS = 80
L2_BITS = 1000
TOTAL_BITS = 1080
H1_ROWS = 16
L2_ROWS = 200
TOTAL_ROWS = 216
RATE_BPS = 1080.0 / 1024.0
PREP_LIMIT_S = 300.0
G_LIMIT_S = 300.0
INV_LIMIT_S = 600.0
RSS_LIMIT_BYTES = 2 * 1024**3
# ponytail: scalar-only summary; shapes are frozen scalars, not data.
SUMMARY_BANNED_KEYS = (
    "alice_symbols",
    "bob_symbols",
    "prior_logp",
    "syndrome_target",
    "syndrome_observed",
    "syndrome_bytes",
    "candidate",
    "messages",
    "check_to_variable",
    "alice_bits",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _workspace_root() -> Path:
    return (_repo_root() / "workspace").resolve()


def _production_root() -> Path:
    return (
        _repo_root() / "comparison_bench" / "outputs_comparison" / OUT_DIR_NAME
    ).resolve()


def validate_output_target(out_dir: str | Path) -> Path:
    """R1 output guard: exact pre-registered root or fresh workspace dir only."""
    raw = Path(out_dir)
    if not raw.is_absolute():
        cand = (_repo_root() / raw).resolve()
    else:
        cand = raw.resolve()
    prod = _production_root()
    ws = _workspace_root()
    if cand.exists():
        raise FileExistsError(f"output directory already exists: {cand}")
    if cand.name == "run_01" or "run_01" in cand.parts:
        raise ValueError("audit output must not be run_01")
    if cand == prod:
        return cand
    try:
        cand.relative_to(ws)
    except ValueError as exc:
        raise ValueError(
            "audit output must be the pre-registered root or under workspace/"
        ) from exc
    return cand


def _resolve_parquet(raw: Any, registry_dir: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("registry parquet_path must be a non-empty string")
    cand = Path(raw.strip())
    if not cand.is_absolute():
        cand = (registry_dir / cand).resolve()
        if not cand.exists():
            alt = (_repo_root() / raw.strip()).resolve()
            if alt.exists():
                cand = alt
    return cand.resolve()


def validate_registry(registry: dict[str, Any], registry_path: str | Path | None = None) -> dict[str, Any]:
    """CAL-only registry check: frozen session + CAL702..1725 + parquet exists.

    Extra keys are ignored. Held-out identifiers beyond CAL are never read.
    """
    if not isinstance(registry, dict):
        raise ValueError("registry must be a mapping")
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueError(f"registry schema must be {REGISTRY_SCHEMA}")
    if registry.get("session_id") != SESSION_ID:
        raise ValueError("registry session_id must be the frozen 1M session")
    if registry.get("source_label") != "1M":
        raise ValueError("registry source_label must be 1M")
    if bool(registry.get("used_2m", False)) is not False:
        raise ValueError("registry used_2m must be false")
    if bool(registry.get("used_2M", False)) is not False:
        raise ValueError("registry used_2M must be false")
    cal_ids = [int(v) for v in registry.get("cal_frame_ids", [])]
    if cal_ids != list(range(CAL_START, CAL_END + 1)):
        raise ValueError("CAL must be the frozen 702..1725 sequence (1024 frames)")
    cols = list(registry.get("columns", []))
    if set(cols) != set(REQUIRED_PARQUET_COLUMNS):
        raise ValueError(f"registry columns must be exactly {list(REQUIRED_PARQUET_COLUMNS)}")
    base_dir = Path(registry_path).resolve().parent if registry_path is not None else _repo_root()
    parquet_path = _resolve_parquet(registry.get("parquet_path"), base_dir)
    if not parquet_path.is_file():
        raise ValueError(f"registry parquet_path does not exist: {parquet_path}")
    return {
        "session_id": SESSION_ID,
        "parquet_path": parquet_path,
        "cal_ids": cal_ids,
        "columns": list(REQUIRED_PARQUET_COLUMNS),
    }


def load_cal_arrays(parquet_path: str | Path, cal_ids: list[int] | None = None) -> dict[str, Any]:
    """CAL-only filtered read: 1024 frames x 256 pairs, symbols 0..1023."""
    import pandas as pd

    cal = list(range(CAL_START, CAL_END + 1)) if cal_ids is None else [int(v) for v in cal_ids]
    if cal != list(range(CAL_START, CAL_END + 1)):
        raise ValueError("CAL ids must be the frozen 702..1725 sequence")
    cols = list(REQUIRED_PARQUET_COLUMNS)
    try:
        df = pd.read_parquet(Path(parquet_path), columns=cols)
    except Exception as exc:
        raise ValueError(f"parquet unreadable: {type(exc).__name__}: {exc}") from exc
    n_read = int(len(df))
    if set(df.columns) != set(cols):
        raise ValueError(f"parquet columns must be exactly {cols}")
    if int(df.isna().sum().sum()) != 0:
        raise ValueError("parquet contains NaN")
    for col in cols:
        vals = df[col].to_numpy()
        if not np.all(vals == np.floor(vals.astype(np.float64))):
            raise ValueError(f"parquet column {col} must be integral")
    keep = df[df["frame_id"].isin(cal)]
    n_retained = int(len(keep))
    if n_retained != 1024 * 256:
        raise ValueError(f"CAL retained rows must be 262144, got {n_retained}")
    bundle: dict[int, dict[str, np.ndarray]] = {}
    for fid in cal:
        sub = keep[keep["frame_id"] == fid].sort_values("pair_idx")
        if len(sub) != 256:
            raise ValueError(f"frame {fid} must hold 256 rows")
        pairs = sub["pair_idx"].to_numpy(dtype=np.int64)
        if not np.array_equal(pairs, np.arange(256, dtype=np.int64)):
            raise ValueError(f"frame {fid} pair_idx must be sorted 0..255 with no dup")
        for col in ("alice_symbol", "bob_symbol"):
            syms = sub[col].to_numpy(dtype=np.int64)
            if np.any(syms < 0) or np.any(syms >= Q):
                raise ValueError(f"frame {fid} {col} outside 0..1023")
        bundle[int(fid)] = {
            "alice_symbols": sub["alice_symbol"].to_numpy(dtype=np.int64),
            "bob_symbols": sub["bob_symbol"].to_numpy(dtype=np.int64),
        }
    alice_cal = np.concatenate([bundle[f]["alice_symbols"] for f in cal])
    bob_cal = np.concatenate([bundle[f]["bob_symbols"] for f in cal])
    return {
        "n_read_rows": n_read,
        "n_retained_rows": n_retained,
        "n_cal_frames": len(cal),
        "n_cal_symbols": int(alice_cal.size),
        "alice_cal": alice_cal.astype(np.int64),
        "bob_cal": bob_cal.astype(np.int64),
        "cal_bundle": bundle,
    }


def symbols_to_layers(symbols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """low=u2=bits0..4, high=u1=bits5..9; symbol=low+32*high."""
    arr = np.asarray(symbols, dtype=np.int64).reshape(-1)
    if np.any(arr < 0) or np.any(arr >= Q):
        raise ValueError("symbols outside 0..1023")
    low = (arr & 31).astype(np.int64)
    high = ((arr >> 5) & 31).astype(np.int64)
    return low, high


def build_canonical_counts(alice_symbols: np.ndarray, bob_symbols: np.ndarray, q: int = Q) -> np.ndarray:
    """Canonical counts[a,b]=count(Alice=a,Bob=b), axis0 Alice axis1 Bob."""
    a = np.asarray(alice_symbols, dtype=np.int64).reshape(-1)
    b = np.asarray(bob_symbols, dtype=np.int64).reshape(-1)
    qq = int(q)
    if qq <= 0:
        raise ValueError("q must be positive")
    if a.shape != b.shape or a.size == 0:
        raise ValueError("symbol arrays must be non-empty equal length")
    if np.any(a < 0) or np.any(a >= qq) or np.any(b < 0) or np.any(b >= qq):
        raise ValueError("symbols outside 0..q-1")
    counts = np.zeros((qq, qq), dtype=np.float64)
    np.add.at(counts, (a, b), 1.0)
    if float(counts.sum()) <= 0:
        raise ValueError("counts are all zero")
    return counts


def _check_normalized(rows: np.ndarray, axis: int = 1) -> None:
    arr = np.asarray(rows, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise ValueError("probability table must be finite")
    if np.any(arr < 0):
        raise ValueError("probability table must be nonnegative")
    s = arr.sum(axis=axis)
    if not np.all(np.abs(s - 1.0) <= NORM_TOL):
        raise ValueError(f"probability rows must sum to 1 within {NORM_TOL}")


def build_m0(a_train: np.ndarray) -> dict[str, Any]:
    """M0 pin train marginal: P(a)=count(A=a)/n, no smoothing, floor only for log."""
    a = np.asarray(a_train, dtype=np.int64).reshape(-1)
    if a.size == 0:
        raise ValueError("M0 train must be non-empty")
    if np.any(a < 0) or np.any(a >= Q):
        raise ValueError("M0 symbols outside 0..1023")
    n = int(a.size)
    cnt = np.zeros(Q, dtype=np.float64)
    np.add.at(cnt, a, 1.0)
    p_a = cnt / float(n)
    if abs(float(p_a.sum()) - 1.0) > NORM_TOL:
        raise ValueError("M0 marginal must sum to 1 within 1e-12")
    # Floor-then-derive keeps the chain exact under FLOOR: joint zeros become
    # FLOOR before marginalization, so P(A)=P(U1)*P(U2|U1) holds after flooring.
    p_a = np.maximum(p_a, FLOOR)
    p_a = p_a / float(p_a.sum())
    # Decompose into U1 marginal + U2|U1 for layered budget diagnosis.
    grid = p_a.reshape(Q_SUB, Q_SUB)  # grid[u1,u2] with A=low+32*high
    # Note: p_a index a=low+32*high; reshape(32,32) with C order gives [high,low].
    p_u1 = grid.sum(axis=1)
    if abs(float(p_u1.sum()) - 1.0) > NORM_TOL:
        raise ValueError("M0 P(U1) must sum to 1 within 1e-12")
    p_u2_given_u1 = np.zeros((Q_SUB, Q_SUB), dtype=np.float64)
    for u1 in range(Q_SUB):
        d = float(p_u1[u1])
        if d <= 0:
            p_u2_given_u1[u1] = np.full(Q_SUB, 1.0 / Q_SUB)
        else:
            p_u2_given_u1[u1] = grid[u1] / d
    _check_normalized(p_u2_given_u1, axis=1)
    return {"P_A": p_a, "P_U1": p_u1, "P_U2_given_U1": p_u2_given_u1, "n_train": n}


def build_m1(a_train: np.ndarray, b_train: np.ndarray, lam: float = M1_LAM) -> dict[str, Any]:
    """M1 canonical full P(A|B): column smoothing with frozen lam, then chain split."""
    a = np.asarray(a_train, dtype=np.int64).reshape(-1)
    b = np.asarray(b_train, dtype=np.int64).reshape(-1)
    if a.shape != b.shape or a.size == 0:
        raise ValueError("M1 train must be non-empty equal length")
    lam_f = float(lam)
    if not np.isfinite(lam_f) or lam_f <= 0:
        raise ValueError("lam must be finite positive")
    n = int(a.size)
    counts = build_canonical_counts(a, b, q=Q)  # [A,B]
    n_b = counts.sum(axis=0)  # per B column
    p_global = counts.sum(axis=1) / float(n)  # P(A) marginal
    # Column smoothing: P(a|b)=(counts[a,b]+lam*p_global[a])/(n_b[b]+lam).
    p_a_given_b = (counts + lam_f * p_global[:, None]) / (n_b[None, :] + lam_f)
    col = p_a_given_b.sum(axis=0)
    if not np.all(np.abs(col - 1.0) <= NORM_TOL):
        raise ValueError("M1 P(A|B) columns must sum to 1 within 1e-12")
    # Chain split: P(U1|B) by marginalizing U2; P(U2|U1,B) by conditioning.
    cube = p_a_given_b.reshape(Q_SUB, Q_SUB, Q)  # [high=u1, low=u2, B]
    # reshape order: A=low+32*high -> index a=low+32*high; reshape(32,32,Q) C-order gives [high,low,B]. Verify: a=1 -> high0 low1 -> cube[0,1,b]. Correct.
    p_u1_given_b = cube.sum(axis=1).T  # [B,U1]
    _check_normalized(p_u1_given_b, axis=1)
    p_u2_given_u1_b = np.zeros((Q_SUB, Q, Q_SUB), dtype=np.float64)  # [U1,B,U2]
    for u1 in range(Q_SUB):
        denom = p_u1_given_b[:, u1]  # per B
        num = cube[u1, :, :].T  # [B,U2]
        for bi in range(Q):
            d = float(denom[bi])
            if d <= 0:
                p_u2_given_u1_b[u1, bi] = np.full(Q_SUB, 1.0 / Q_SUB)
            else:
                p_u2_given_u1_b[u1, bi] = num[bi] / d
    for u1 in range(Q_SUB):
        _check_normalized(p_u2_given_u1_b[u1], axis=1)
    return {
        "P_A_given_B": p_a_given_b,
        "P_U1_given_B": p_u1_given_b,
        "P_U2_given_U1_B": p_u2_given_u1_b,
        "lam": float(lam_f),
        "n_train": n,
    }


def build_m2(a_train: np.ndarray, b_train: np.ndarray, lam: float) -> dict[str, Any]:
    """M2 hierarchical P(U1|B)*P(U2|U1,B) with Laplace lam (TRAIN-only)."""
    a = np.asarray(a_train, dtype=np.int64).reshape(-1)
    b = np.asarray(b_train, dtype=np.int64).reshape(-1)
    if a.shape != b.shape or a.size == 0:
        raise ValueError("M2 train must be non-empty equal length")
    lam_f = float(lam)
    if not np.isfinite(lam_f) or lam_f <= 0:
        raise ValueError("lam must be finite positive")
    n = int(a.size)
    a_low, a_high = symbols_to_layers(a)
    # P1: counts [B,U1] smoothed by global U1 marginal.
    cnt1 = np.zeros((Q, Q_SUB), dtype=np.float64)
    np.add.at(cnt1, (b, a_high), 1.0)
    n_b1 = cnt1.sum(axis=1)
    p_g1 = cnt1.sum(axis=0) / float(n)
    p1 = (cnt1 + lam_f * p_g1[None, :]) / (n_b1[:, None] + lam_f)
    _check_normalized(p1, axis=1)
    # P2: counts [U1,B,U2] smoothed by global U2 marginal.
    cnt2 = np.zeros((Q_SUB, Q, Q_SUB), dtype=np.float64)
    np.add.at(cnt2, (a_high, b, a_low), 1.0)
    n_row = cnt2.sum(axis=2, keepdims=True)
    p_g2 = cnt2.sum(axis=(0, 1)) / float(n)
    p2 = (cnt2 + lam_f * p_g2[None, None, :]) / (n_row + lam_f)
    for u1 in range(Q_SUB):
        _check_normalized(p2[u1], axis=1)
    return {"P1": p1, "P2": p2, "lam": float(lam_f), "n_train": n}


def m3_exit_record() -> dict[str, Any]:
    """M3 has no unique definition this round: direct EXIT, excluded."""
    return {"model": "M3", "status": M3_STATUS, "in_selection": False, "in_budget": False, "in_route": False}


def _ce_from_probs(probs: np.ndarray) -> float:
    vals = np.maximum(np.asarray(probs, dtype=np.float64).reshape(-1), FLOOR)
    return float(-np.mean(np.log2(vals)))


def ce_m0(fit: dict[str, Any], a_test: np.ndarray, b_test: np.ndarray) -> dict[str, float]:
    a = np.asarray(a_test, dtype=np.int64).reshape(-1)
    _ = np.asarray(b_test, dtype=np.int64).reshape(-1)
    if a.shape != _.shape or a.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    low, high = symbols_to_layers(a)
    p_joint = np.maximum(np.asarray(fit["P_A"])[a], FLOOR)
    p_l1 = np.maximum(np.asarray(fit["P_U1"])[high], FLOOR)
    p2mat = np.asarray(fit["P_U2_given_U1"])
    p_l2 = np.maximum(p2mat[high, low], FLOOR)
    ce_j = float(-np.mean(np.log2(p_joint)))
    ce_1 = float(-np.mean(np.log2(p_l1)))
    ce_2 = float(-np.mean(np.log2(p_l2)))
    err = abs(ce_j - ce_1 - ce_2)
    if err >= CHAIN_TOL:
        raise ValueError(f"M0 chain error {err} exceeds 1e-10")
    return {"ce_l1": ce_1, "ce_l2_oracle": ce_2, "ce_joint": ce_j, "chain_err": err, "n": int(a.size)}


def ce_m1(fit: dict[str, Any], a_test: np.ndarray, b_test: np.ndarray) -> dict[str, float]:
    a = np.asarray(a_test, dtype=np.int64).reshape(-1)
    b = np.asarray(b_test, dtype=np.int64).reshape(-1)
    if a.shape != b.shape or a.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    low, high = symbols_to_layers(a)
    p_ab = np.asarray(fit["P_A_given_B"])
    p_u1b = np.asarray(fit["P_U1_given_B"])
    p_u2 = np.asarray(fit["P_U2_given_U1_B"])
    ce_j = _ce_from_probs(p_ab[a, b])
    ce_1 = _ce_from_probs(p_u1b[b, high])
    ce_2 = _ce_from_probs(p_u2[high, b, low])
    err = abs(ce_j - ce_1 - ce_2)
    if err >= CHAIN_TOL:
        raise ValueError(f"M1 chain error {err} exceeds 1e-10")
    return {"ce_l1": ce_1, "ce_l2_oracle": ce_2, "ce_joint": ce_j, "chain_err": err, "n": int(a.size)}


def ce_m2(fit: dict[str, Any], a_test: np.ndarray, b_test: np.ndarray) -> dict[str, float]:
    a = np.asarray(a_test, dtype=np.int64).reshape(-1)
    b = np.asarray(b_test, dtype=np.int64).reshape(-1)
    if a.shape != b.shape or a.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    low, high = symbols_to_layers(a)
    p1 = np.asarray(fit["P1"])
    p2 = np.asarray(fit["P2"])
    ce_1 = _ce_from_probs(p1[b, high])
    ce_2 = _ce_from_probs(p2[high, b, low])
    joint = np.maximum(p1[b, high], FLOOR) * np.maximum(p2[high, b, low], FLOOR)
    joint = np.maximum(joint, FLOOR)
    ce_j = float(-np.mean(np.log2(joint)))
    err = abs(ce_j - ce_1 - ce_2)
    if err >= CHAIN_TOL:
        raise ValueError(f"M2 chain error {err} exceeds 1e-10")
    return {"ce_l1": ce_1, "ce_l2_oracle": ce_2, "ce_joint": ce_j, "chain_err": err, "n": int(a.size)}


def outer_folds() -> list[dict[str, Any]]:
    """Deterministic frame-blocked outer folds: TEST 256 / TRAIN 768, no shuffle."""
    folds = []
    for k in range(4):
        test_ids = list(OUTER_FOLDS[k])
        train_ids: list[int] = []
        for j in range(4):
            if j != k:
                train_ids.extend(list(OUTER_FOLDS[j]))
        if len(test_ids) != 256 or len(train_ids) != 768:
            raise ValueError("outer fold must be TEST256/TRAIN768")
        if set(test_ids) & set(train_ids):
            raise ValueError("outer TEST/TRAIN overlap")
        folds.append({"fold": int(k), "train_ids": train_ids, "test_ids": test_ids})
    # Mechanical assertions.
    all_test: list[int] = []
    for f in folds:
        all_test.extend(f["test_ids"])
    if sorted(all_test) != list(range(CAL_START, CAL_END + 1)):
        raise ValueError("four outer TESTs must partition 702..1725")
    return folds


def inner_folds_for_outer(k: int) -> list[dict[str, Any]]:
    """Deterministic inner folds: outer TRAIN split into its 3 frame blocks, no shuffle."""
    outer = outer_folds()
    if not 0 <= int(k) < 4:
        raise ValueError("outer index must be 0..3")
    train_ids = list(outer[int(k)]["train_ids"])
    blocks: list[list[int]] = []
    for j in range(4):
        if j != int(k):
            blocks.append(list(OUTER_FOLDS[j]))
    if sum(len(b) for b in blocks) != 768:
        raise ValueError("inner blocks must cover outer TRAIN 768")
    inners = []
    for t in range(3):
        te = list(blocks[t])
        tr: list[int] = []
        for s in range(3):
            if s != t:
                tr.extend(blocks[s])
        if len(te) != 256 or len(tr) != 512:
            raise ValueError("inner fold must be 512/256")
        if set(te) & set(tr):
            raise ValueError("inner TEST/TRAIN overlap")
        if set(tr) | set(te) != set(train_ids):
            raise ValueError("inner folds must partition outer TRAIN")
        inners.append({"inner_fold": int(t), "inner_train_ids": tr, "inner_test_ids": te})
    # Pairwise disjoint + union check.
    seen: set[int] = set()
    for inn in inners:
        cur = set(inn["inner_test_ids"])
        if cur & seen:
            raise ValueError("inner folds must be pairwise disjoint")
        seen |= cur
    if seen != set(train_ids):
        raise ValueError("inner union must equal outer TRAIN")
    return inners


def _concat_bundle(bundle: dict[int, dict[str, np.ndarray]], ids: list[int]) -> tuple[np.ndarray, np.ndarray]:
    a = np.concatenate([np.asarray(bundle[int(f)]["alice_symbols"], dtype=np.int64) for f in ids])
    b = np.concatenate([np.asarray(bundle[int(f)]["bob_symbols"], dtype=np.int64) for f in ids])
    return a, b


def _seen_split_scores(
    b_train: np.ndarray, b_test: np.ndarray, loss_per_sample: np.ndarray
) -> dict[str, float]:
    train_vals = set(int(v) for v in np.asarray(b_train, dtype=np.int64).reshape(-1))
    bt = np.asarray(b_test, dtype=np.int64).reshape(-1)
    lp = np.asarray(loss_per_sample, dtype=np.float64).reshape(-1)
    mask = np.array([int(v) in train_vals for v in bt], dtype=bool)
    n = int(bt.size)
    n_seen = int(mask.sum())
    return {
        "seen_frac": float(n_seen / n) if n else 0.0,
        "n_seen": n_seen,
        "n_unseen": int(n - n_seen),
        "ce_seen": float(np.mean(lp[mask])) if n_seen else float("nan"),
        "ce_unseen": float(np.mean(lp[~mask])) if n - n_seen else float("nan"),
    }


def evaluate_outer_fold(
    bundle: dict[int, dict[str, np.ndarray]], k: int, selected_lam_m2: float
) -> dict[str, Any]:
    """Fit M0/M1/M2 on outer TRAIN, score on outer TEST (TEST never enters fit)."""
    outer = outer_folds()
    train_ids = list(outer[int(k)]["train_ids"])
    test_ids = list(outer[int(k)]["test_ids"])
    a_tr, b_tr = _concat_bundle(bundle, train_ids)
    a_te, b_te = _concat_bundle(bundle, test_ids)
    out: dict[str, Any] = {"fold": int(k), "n_train": int(a_tr.size), "n_test": int(a_te.size)}
    # M0.
    f0 = build_m0(a_tr)
    c0 = ce_m0(f0, a_te, b_te)
    loss0 = -np.log2(np.maximum(np.asarray(f0["P_A"])[a_te], FLOOR))
    s0 = _seen_split_scores(b_tr, b_te, loss0)
    out["M0"] = {**c0, **s0}
    # M1 canonical frozen lam.
    f1 = build_m1(a_tr, b_tr, M1_LAM)
    c1 = ce_m1(f1, a_te, b_te)
    loss1 = -np.log2(np.maximum(np.asarray(f1["P_A_given_B"])[a_te, b_te], FLOOR))
    s1 = _seen_split_scores(b_tr, b_te, loss1)
    out["M1"] = {**c1, **s1, "lam": float(M1_LAM)}
    # M2 hierarchical with TRAIN-selected lam (passed in, never refit on TEST).
    f2 = build_m2(a_tr, b_tr, float(selected_lam_m2))
    c2 = ce_m2(f2, a_te, b_te)
    p1m = np.asarray(f2["P1"])[b_te, symbols_to_layers(a_te)[1]]
    low_te, high_te = symbols_to_layers(a_te)
    p2m = np.asarray(f2["P2"])[high_te, b_te, low_te]
    loss2 = -np.log2(np.maximum(np.maximum(p1m, FLOOR) * np.maximum(p2m, FLOOR), FLOOR))
    s2 = _seen_split_scores(b_tr, b_te, loss2)
    out["M2"] = {**c2, "lam": float(selected_lam_m2), **s2}
    return out


def inner_select_lambda(
    bundle: dict[int, dict[str, np.ndarray]], k: int, lam_grid: tuple[float, ...] | None = None
) -> dict[str, Any]:
    """Inner 3-fold selection for M2: fit on inner TRAIN, score inner held-out only.

    Never reads outer TEST. Returns selected lam (minimal inner mean joint).
    """
    grid = tuple(float(v) for v in (LAMBDA_GRID if lam_grid is None else lam_grid))
    if len(grid) == 0:
        raise ValueError("lambda grid must be non-empty")
    for v in grid:
        if not np.isfinite(v) or v <= 0:
            raise ValueError("lambda grid must be finite positive")
    inners = inner_folds_for_outer(int(k))
    table = []
    for lam in grid:
        joints = []
        for inn in inners:
            a_tr, b_tr = _concat_bundle(bundle, list(inn["inner_train_ids"]))
            a_te, b_te = _concat_bundle(bundle, list(inn["inner_test_ids"]))
            fit = build_m2(a_tr, b_tr, lam)
            sc = ce_m2(fit, a_te, b_te)
            joints.append(float(sc["ce_joint"]))
        table.append({"lam": float(lam), "inner_mean_ce_joint": float(sum(joints) / len(joints))})
    best = min(table, key=lambda r: (r["inner_mean_ce_joint"], r["lam"]))
    return {"outer_fold": int(k), "selected_lam": float(best["lam"]), "inner_table": table}


def r5_synth_repro() -> dict[str, Any]:
    """Same-fixture formula repro: uniform independent synthetic, R5 shuffle caliber.

    Uses the frozen R5 4-fold shuffled-split caliber (perm[k::4]) only on the
    synthetic fixture. Real CAL never uses this path. REAL_CAL_EXACT_MATCH=false.
    """
    rng_ab = np.random.default_rng(R5_SEED)
    a = rng_ab.integers(0, Q, size=R5_N).astype(np.int64)
    b = rng_ab.integers(0, Q, size=R5_N).astype(np.int64)
    # Frozen R5 caliber: perm uses a fresh RNG with the same seed, not the
    # continued stream (matches D3 cal_4fold_cv_heldout_nll + _r5_synth_cal).
    perm = np.random.default_rng(R5_SEED).permutation(R5_N)
    folds = []
    for kk in range(4):
        te_idx = perm[kk::4]
        tr_idx = np.setdiff1d(perm, te_idx, assume_unique=True)
        a_tr, b_tr = a[tr_idx], b[tr_idx]
        a_te, b_te = a[te_idx], b[te_idx]
        fit = build_m2(a_tr, b_tr, R5_LAM)
        sc = ce_m2(fit, a_te, b_te)
        folds.append({"fold": int(kk), "n_train": int(tr_idx.size), "n_heldout": int(te_idx.size), **sc})
    mean_l1 = float(sum(f["ce_l1"] for f in folds) / 4)
    mean_l2 = float(sum(f["ce_l2_oracle"] for f in folds) / 4)
    mean_j = float(sum(f["ce_joint"] for f in folds) / 4)
    chain = abs(mean_j - mean_l1 - mean_l2)
    d1 = abs(mean_l1 - R5_REF_L1)
    d2 = abs(mean_l2 - R5_REF_L2)
    dj = abs(mean_j - R5_REF_JOINT)
    passed = bool(d1 < R5_TOL and d2 < R5_TOL and dj < R5_TOL and chain < CHAIN_TOL)
    if passed:
        root = "R5_FIXTURE_REPRODUCED"
    else:
        # Root-cause decomposition: caliber vs implementation (same synthetic domain).
        root = "BLOCKED_IMPLEMENTATION_OR_CALIBER_DEVIATION"
    return {
        "seed": int(R5_SEED),
        "n": int(R5_N),
        "lam": float(R5_LAM),
        "mean_ce_l1": mean_l1,
        "mean_ce_l2_oracle": mean_l2,
        "mean_ce_joint": mean_j,
        "ref": {"ce_l1": R5_REF_L1, "ce_l2_oracle": R5_REF_L2, "ce_joint": R5_REF_JOINT},
        "delta": {"ce_l1": d1, "ce_l2_oracle": d2, "ce_joint": dj},
        "chain_err": chain,
        "passed": passed,
        "root_cause": root,
        "real_cal_exact_match": False,
        "folds": folds,
    }


def select_model(outer_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold-mean minimal + delta 0.02 simple priority + stability downgrade."""
    stats: dict[str, Any] = {}
    for m in MODEL_ORDER:
        joints = [float(r[m]["ce_joint"]) for r in outer_results]
        mean = float(sum(joints) / len(joints))
        std = float(np.std(np.asarray(joints, dtype=np.float64), ddof=0))
        rng = float(max(joints) - min(joints))
        unstable = bool(std > STABILITY_STD or rng > STABILITY_RANGE)
        stats[m] = {"joints": joints, "mean": mean, "std": std, "max_min": rng, "unstable": unstable}
    order = sorted(MODEL_ORDER, key=lambda m: stats[m]["mean"])
    best = order[0]
    # Simple priority within delta.
    for cand in MODEL_ORDER:
        if stats[cand]["mean"] - stats[best]["mean"] < SELECT_DELTA and MODEL_ORDER.index(cand) < MODEL_ORDER.index(best):
            # cand is simpler and within delta of the best mean.
            if stats[cand]["mean"] <= stats[best]["mean"] + SELECT_DELTA:
                best = cand
                break
    # Re-evaluate: simplest within delta of global best.
    global_best_mean = min(stats[m]["mean"] for m in MODEL_ORDER)
    candidates = [m for m in MODEL_ORDER if stats[m]["mean"] - global_best_mean < SELECT_DELTA]
    preferred = min(candidates, key=lambda m: MODEL_ORDER.index(m))
    # Stability downgrade: prefer stable among near-best; if preferred unstable, pick best stable.
    stable = [m for m in MODEL_ORDER if not stats[m]["unstable"]]
    downgraded = False
    reason = f"mean-minimal within {SELECT_DELTA}: {preferred}"
    if stats[preferred]["unstable"]:
        if stable:
            stable_best = min(stable, key=lambda m: stats[m]["mean"])
            reason = f"{preferred} unstable (std={stats[preferred]['std']:.4f}, range={stats[preferred]['max_min']:.4f}); downgraded to stable {stable_best}"
            preferred = stable_best
            downgraded = True
        else:
            reason = f"{preferred} unstable but no stable alternative; retained with unstable flag"
    ranking = sorted(MODEL_ORDER, key=lambda m: (stats[m]["mean"], MODEL_ORDER.index(m)))
    return {
        "selected": preferred,
        "ranking": ranking,
        "stats": stats,
        "downgraded": downgraded,
        "reason": reason,
        "delta": float(SELECT_DELTA),
        "stability": {"std_thr": float(STABILITY_STD), "range_thr": float(STABILITY_RANGE)},
    }


def budget_rows(ce: float, f: float) -> int:
    return int(math.ceil(N * float(ce) * float(f) / 5.0))


def budget_for_model(mean_l1: float, mean_l2: float, mean_joint: float) -> dict[str, Any]:
    """Four-f budget grid rows=ceil(N*CE*f/5) vs 16/200/216 rows."""
    layers = {"L1": (float(mean_l1), H1_BITS, H1_ROWS), "L2": (float(mean_l2), L2_BITS, L2_ROWS), "Total": (float(mean_joint), TOTAL_BITS, TOTAL_ROWS)}
    grid: dict[str, Any] = {}
    for f in F_LIST:
        per_f: dict[str, Any] = {}
        for name, (ce, avail_bits, avail_rows) in layers.items():
            req_bits = N * ce * f
            req_rows = budget_rows(ce, f)
            per_f[name] = {
                "ce": float(ce),
                "f": float(f),
                "required_bits": float(req_bits),
                "required_rows": int(req_rows),
                "available_bits": int(avail_bits),
                "available_rows": int(avail_rows),
                "fit": bool(req_rows <= avail_rows),
                "margin_rows": int(avail_rows - req_rows),
            }
        grid[str(f)] = per_f
    return {"N": int(N), "grid": grid}


def route_from_selection(mean_l1: float, mean_l2: float, mean_joint: float) -> dict[str, Any]:
    """A/B/C mutually exclusive on selected-model mean, same caliber."""
    b10 = budget_for_model(mean_l1, mean_l2, mean_joint)["grid"]["1.0"]
    b13 = budget_for_model(mean_l1, mean_l2, mean_joint)["grid"]["1.3"]
    fit10 = bool(b10["L1"]["fit"] and b10["L2"]["fit"] and b10["Total"]["fit"])
    fit13 = bool(b13["L1"]["fit"] and b13["L2"]["fit"] and b13["Total"]["fit"])
    if fit13:
        route = "A"
        why = "fit@1.3 all layers"
    elif not fit10:
        route = "C"
        why = "mismatch@1.0 some layer"
    else:
        route = "B"
        why = "fit@1.0 but mismatch@1.3"
    return {"route": route, "why": why, "fit_at_1_0": fit10, "fit_at_1_3": fit13}


def _sample_rss(rss_reader: Any = None) -> int | None:
    if rss_reader is not None:
        try:
            return int(rss_reader())
        except Exception:
            return None
    try:
        import psutil as _psutil
        import os as _os

        return int(_psutil.Process(_os.getpid()).memory_info().rss)
    except Exception:
        return None


def build_audit_summary(
    *,
    registry_path: str | Path,
    loaded: dict[str, Any],
    r5: dict[str, Any],
    outer_results: list[dict[str, Any]],
    inner_selections: list[dict[str, Any]],
    selection: dict[str, Any],
    budgets: dict[str, Any],
    route: dict[str, Any],
    prep_wall_s: float,
    g_wall_s: float,
    inv_wall_s: float,
    peak_rss: int | None,
) -> dict[str, Any]:
    sel = str(selection["selected"])
    sel_stats = selection["stats"][sel]
    # Root-cause decomposition (descriptive, same caliber).
    m0m = float(selection["stats"]["M0"]["mean"])
    m1m = float(selection["stats"]["M1"]["mean"])
    m2m = float(selection["stats"]["M2"]["mean"])
    return {
        "schema": AUDIT_SCHEMA,
        "status": "READY",
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "registry": str(Path(registry_path).resolve()),
        "cal": [int(CAL_START), int(CAL_END)],
        "outer_folds": ["702..957", "958..1213", "1214..1469", "1470..1725"],
        "rows": {
            "n_cal_frames": int(loaded["n_cal_frames"]),
            "n_cal_symbols": int(loaded["n_cal_symbols"]),
            "n_read_rows": int(loaded["n_read_rows"]),
            "n_retained_rows": int(loaded["n_retained_rows"]),
        },
        "contracts": {"normalization": NORM_TOL, "chain": CHAIN_TOL, "floor": FLOOR},
        "m1_lam": float(M1_LAM),
        "lambda_grid": [float(v) for v in LAMBDA_GRID],
        "m3": m3_exit_record(),
        "uniform_lower_bound_descriptive": {"ce_joint": float(UNIFORM_CE), "in_selection": False},
        "r5_repro": {
            "passed": bool(r5["passed"]),
            "mean_ce_l1": float(r5["mean_ce_l1"]),
            "mean_ce_l2_oracle": float(r5["mean_ce_l2_oracle"]),
            "mean_ce_joint": float(r5["mean_ce_joint"]),
            "delta": {k: float(v) for k, v in r5["delta"].items()},
            "chain_err": float(r5["chain_err"]),
            "root_cause": str(r5["root_cause"]),
            "real_cal_exact_match": False,
        },
        "outer_results": [
            {
                "fold": int(r["fold"]),
                "n_train": int(r["n_train"]),
                "n_test": int(r["n_test"]),
                "M0": {"ce_l1": float(r["M0"]["ce_l1"]), "ce_l2_oracle": float(r["M0"]["ce_l2_oracle"]), "ce_joint": float(r["M0"]["ce_joint"]), "chain_err": float(r["M0"]["chain_err"]), "seen_frac": float(r["M0"]["seen_frac"])},
                "M1": {"ce_l1": float(r["M1"]["ce_l1"]), "ce_l2_oracle": float(r["M1"]["ce_l2_oracle"]), "ce_joint": float(r["M1"]["ce_joint"]), "chain_err": float(r["M1"]["chain_err"]), "lam": float(r["M1"]["lam"]), "seen_frac": float(r["M1"]["seen_frac"])},
                "M2": {"ce_l1": float(r["M2"]["ce_l1"]), "ce_l2_oracle": float(r["M2"]["ce_l2_oracle"]), "ce_joint": float(r["M2"]["ce_joint"]), "chain_err": float(r["M2"]["chain_err"]), "lam": float(r["M2"]["lam"]), "seen_frac": float(r["M2"]["seen_frac"])},
            }
            for r in outer_results
        ],
        "inner_selections": [
            {"outer_fold": int(s["outer_fold"]), "selected_lam": float(s["selected_lam"])} for s in inner_selections
        ],
        "selection": {
            "selected": sel,
            "ranking": list(selection["ranking"]),
            "reason": str(selection["reason"]),
            "downgraded": bool(selection["downgraded"]),
            "stats": {m: {"mean": float(selection["stats"][m]["mean"]), "std": float(selection["stats"][m]["std"]), "max_min": float(selection["stats"][m]["max_min"]), "unstable": bool(selection["stats"][m]["unstable"])} for m in MODEL_ORDER},
        },
        "root_cause_decomposition": {
            "b_dependence_gain_M0_to_M1": float(m0m - m1m),
            "hierarchy_gain_M1_to_M2": float(m1m - m2m),
            "total_gain_M0_to_selected": float(m0m - float(sel_stats["mean"])),
            "synthetic_vs_real_note": "R5 synthetic uniform-independent worst case vs real CAL702..1725 correlated domain; gap is data-domain, not caliber",
        },
        "budgets": budgets,
        "route": route,
        "rate_status": str(route["route"]),
        "wall": {"prep_s": float(prep_wall_s), "g_s": float(g_wall_s), "inv_s": float(inv_wall_s)},
        "rss": {"peak_bytes": None if peak_rss is None else int(peak_rss)},
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
        "cal_only": True,
    }


def _check_summary_allowed(summary: dict[str, Any]) -> None:
    payload = json.dumps(summary, ensure_ascii=False)
    lowered = payload.lower()
    for banned in SUMMARY_BANNED_KEYS:
        if banned.lower() in lowered:
            raise ValueError(f"audit summary must not store {banned}")
    if '"protocol"' in lowered:
        raise ValueError("audit summary must not define protocol")


def write_audit_outputs(out_dir: str | Path, summary: dict[str, Any]) -> Path:
    """Write exactly manifest.json, audit.json, table.csv, report.md."""
    import csv

    out = validate_output_target(out_dir)
    if not isinstance(summary, dict):
        raise ValueError("summary must be a mapping")
    if summary.get("schema") != AUDIT_SCHEMA:
        raise ValueError(f"summary schema must be {AUDIT_SCHEMA}")
    if summary.get("cycle") != CYCLE_ID:
        raise ValueError("summary belongs to another cycle")
    _check_summary_allowed(summary)
    out.mkdir(parents=True, exist_ok=False)
    sel = str(summary["selection"]["selected"])
    budgets = summary["budgets"]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "cal": [int(CAL_START), int(CAL_END)],
        "outer_folds": list(summary["outer_folds"]),
        "models": ["M0(train-marginal)", "M1(canonical,lam=1.0)", "M2(hierarchical,grid30-inner)", "M3_EXIT_AMBIGUOUS"],
        "selected": sel,
        "route": str(summary["route"]["route"]),
        "mapping": "low=bits0..4/high=bits5..9/bit0=LSB/symbol=low+32*high",
        "field": {"q": int(Q_SUB), "poly": 37},
        "budget_rows": {"L1": int(H1_ROWS), "L2": int(L2_ROWS), "Total": int(TOTAL_ROWS)},
        "cal_only": True,
        "decoder_calls": 0,
        "formal": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ["model", "layer", "ce_mean", "f", "required_bits", "required_rows", "available_rows", "fit"]
    with (out / "table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for m in MODEL_ORDER:
            st = summary["selection"]["stats"][m]
            # Recompute per-model budget means from outer means is stored in budgets per model.
            for layer in ("L1", "L2", "Total"):
                for f in F_LIST:
                    cell = budgets[m]["grid"][str(float(f))][layer]
                    writer.writerow(
                        {
                            "model": m,
                            "layer": layer,
                            "ce_mean": cell["ce"],
                            "f": float(f),
                            "required_bits": cell["required_bits"],
                            "required_rows": cell["required_rows"],
                            "available_rows": cell["available_rows"],
                            "fit": cell["fit"],
                        }
                    )
    sel_stats = summary["selection"]["stats"][sel]
    lines = [
        "# V72P2D4R1 CAL GF32 model rate audit (CAL-only, frame-blocked nested)",
        "",
        "Descriptive only; not a lower bound; not a failure verdict.",
        "",
        f"- cycle: `{CYCLE_ID}`",
        f"- session: `{SESSION_ID}`",
        "- outer: `702..957 / 958..1213 / 1214..1469 / 1470..1725` (TEST256/TRAIN768)",
        "- inner: `3 deterministic folds, no shuffle`",
        f"- r5_repro_passed: `{summary['r5_repro']['passed']}` (REAL_CAL_EXACT_MATCH=false)",
        f"- selected: `{sel}` (ranking {summary['selection']['ranking']})",
        f"- reason: `{summary['selection']['reason']}`",
        f"- route: `{summary['route']['route']}` ({summary['route']['why']})",
    ]
    for m in MODEL_ORDER:
        st = summary["selection"]["stats"][m]
        lines.append(f"- {m} mean_joint `{st['mean']:.6f}` std `{st['std']:.6f}` range `{st['max_min']:.6f}` unstable `{st['unstable']}`")
    lines.append(f"- M3: `{M3_STATUS}` (excluded)")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    names = {item.name for item in out.iterdir()}
    if names != {"manifest.json", "audit.json", "table.csv", "report.md"}:
        raise RuntimeError("audit output root must contain exactly four files")
    return out


def run_cal_audit(
    *,
    registry_path: str | Path,
    out_dir: str | Path,
    lam_grid: tuple[float, ...] | None = None,
    clock: Any = None,
    rss_reader: Any = None,
) -> dict[str, Any]:
    """CAL-only compliant audit: guard -> registry -> CAL -> R5 gate -> nested CV -> files."""
    now = clock if clock is not None else time.monotonic
    inv_start = float(now())
    rss_peak: list[int] = []

    def _sample() -> None:
        value = _sample_rss(rss_reader)
        if value is not None:
            rss_peak.append(int(value))

    _sample()
    prep_start = float(now())
    out = validate_output_target(out_dir)
    try:
        reg_raw = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"registry file is missing: {registry_path}") from exc
    validated = validate_registry(reg_raw, registry_path)
    loaded = load_cal_arrays(validated["parquet_path"], validated["cal_ids"])
    bundle = loaded["cal_bundle"]
    # Mechanical frame assertions are enforced inside outer/inner builders.
    prep_wall = float(now()) - prep_start
    _sample()
    if prep_wall > float(PREP_LIMIT_S):
        raise TimeoutError(f"prep wall {prep_wall:.3f}s exceeds {PREP_LIMIT_S}s")
    g_start = float(now())
    r5 = r5_synth_repro()
    if not bool(r5["passed"]):
        raise RuntimeError(f"R5 repro BLOCKED: {r5['root_cause']} {r5['delta']}")
    grid = tuple(float(v) for v in (LAMBDA_GRID if lam_grid is None else lam_grid))
    inner_selections = [inner_select_lambda(bundle, k, grid) for k in range(4)]
    sel_map = {s["outer_fold"]: float(s["selected_lam"]) for s in inner_selections}
    outer_results = [evaluate_outer_fold(bundle, k, sel_map[int(k)]) for k in range(4)]
    selection = select_model(outer_results)
    # Per-model budgets from outer means.
    budgets: dict[str, Any] = {}
    for m in MODEL_ORDER:
        joints = [float(r[m]["ce_joint"]) for r in outer_results]
        l1s = [float(r[m]["ce_l1"]) for r in outer_results]
        l2s = [float(r[m]["ce_l2_oracle"]) for r in outer_results]
        mean_j = float(sum(joints) / len(joints))
        mean_1 = float(sum(l1s) / len(l1s))
        mean_2 = float(sum(l2s) / len(l2s))
        budgets[m] = budget_for_model(mean_1, mean_2, mean_j)
    sel = str(selection["selected"])
    sel_means = {
        "l1": float(sum(float(r[sel]["ce_l1"]) for r in outer_results) / 4),
        "l2": float(sum(float(r[sel]["ce_l2_oracle"]) for r in outer_results) / 4),
        "j": float(sum(float(r[sel]["ce_joint"]) for r in outer_results) / 4),
    }
    route = route_from_selection(sel_means["l1"], sel_means["l2"], sel_means["j"])
    g_wall = float(now()) - g_start
    _sample()
    if g_wall > float(G_LIMIT_S):
        raise TimeoutError(f"audit wall {g_wall:.3f}s exceeds {G_LIMIT_S}s")
    peak = max(rss_peak) if rss_peak else None
    inv_wall = float(now()) - inv_start
    if inv_wall > float(INV_LIMIT_S):
        raise TimeoutError(f"invocation wall {inv_wall:.3f}s exceeds {INV_LIMIT_S}s")
    if peak is not None and peak >= int(RSS_LIMIT_BYTES):
        raise MemoryError("peak RSS exceeds 2GiB")
    summary = build_audit_summary(
        registry_path=registry_path,
        loaded=loaded,
        r5=r5,
        outer_results=outer_results,
        inner_selections=inner_selections,
        selection=selection,
        budgets=budgets,
        route=route,
        prep_wall_s=prep_wall,
        g_wall_s=g_wall,
        inv_wall_s=inv_wall,
        peak_rss=peak,
    )
    written = write_audit_outputs(out, summary)
    _sample()
    return {
        "status": "READY",
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "selected": sel,
        "ranking": list(selection["ranking"]),
        "reason": str(selection["reason"]),
        "route": str(route["route"]),
        "r5_passed": bool(r5["passed"]),
        "n_cal_frames": int(loaded["n_cal_frames"]),
        "n_cal_symbols": int(loaded["n_cal_symbols"]),
        "n_read_rows": int(loaded["n_read_rows"]),
        "n_retained_rows": int(loaded["n_retained_rows"]),
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
        "cal_only": True,
        "prep_wall_s": float(prep_wall),
        "g_wall_s": float(g_wall),
        "inv_wall_s": float(inv_wall),
        "peak_rss_bytes": peak,
        "output": str(written.resolve()),
    }
