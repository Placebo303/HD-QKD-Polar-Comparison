"""V72P2D5 Model-F input preparation — comparison-only, implement-only.

Cycle ``V72P2D5-GF32-RATE-MOTHER``. Canonical full-CAL refit input for
Model-F after the frozen D4R2 lambda selection. Injected arrays only;
no file read in the builder, no VAL, no decoder, no G0-toy reuse.

Frozen contract (see ``openspec/changes/
formal-ir-v72p2d5-model-f-input-preparation/``):
``counts_ab[a,b]=#CAL pairs Alice=a Bob=b``, ``axis0=Alice``,
``bob_counts[b]=sum_a counts_ab``, ``p_b=bob/262144``,
``symbol=low+32*high, U1=high, U2=low``, ``q32 poly37``,
``lambda*=137.3823795883264`` (D4R2 nested-CV, refit only),
``CAL702..1725`` 1024 frames x 256 pairs = 262144 symbols,
session ``20260123_1M_600k_0dB``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    from comparison_bench.formal_ir.v72p2d3_gf32_contrast import (
        build_canonical_counts,
    )
except ImportError:  # pragma: no cover
    from comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast import (  # type: ignore[no-redef]
        build_canonical_counts,
    )

Q = 1024
Q_SUB = 32
CAL_START = 702
CAL_END = 1725
N_CAL_FRAMES = 1024
PAIRS_PER_FRAME = 256
N_CAL_SYMBOLS = 262144
SESSION_ID = "20260123_1M_600k_0dB"
SOURCE_LABEL = "1M"
CYCLE_ID = "V72P2D5-GF32-RATE-MOTHER"
INPUT_SCHEMA = "v72p2d5_model_f_input_v1"
LAMBDA_STAR = 137.3823795883264
GF_Q = 32
GF_POLY = 37
MODEL_F_FORMAL_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
NPZ_NAME = "model_f_input.npz"
JSON_NAME = "model_f_input_summary.json"
STATUS_CANDIDATE = "MODEL_F_INPUT_CANDIDATE"
STATUS_ACCEPTED = "MODEL_F_INPUT_ACCEPTED"


def _as_int_vector(name, values, low, high):
    arr = np.asarray(values)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1-D array")
    if arr.dtype.kind in ("O", "U", "S", "V", "M", "m"):
        raise ValueError(f"{name} must hold integers 0..{high}")
    if arr.dtype.kind == "b":
        raise ValueError(f"{name} must hold integers 0..{high}")
    if arr.dtype.kind == "f":
        vals = np.asarray(arr, dtype=np.float64)
        if not np.all(np.isfinite(vals)):
            raise ValueError(f"{name} must be finite integers")
        if not np.all(vals == np.floor(vals)):
            raise ValueError(f"{name} must hold integers 0..{high}")
        out = vals.astype(np.int64)
    elif arr.dtype.kind in ("i", "u"):
        out = np.asarray(arr, dtype=np.int64)
    else:
        raise ValueError(f"{name} must hold integers 0..{high}")
    if np.any(out < low) or np.any(out > high):
        raise ValueError(f"{name} values must lie in {low}..{high}")
    return out


def build_model_f_input(alice_symbols, bob_symbols, frame_ids):
    """Build canonical full-CAL counts + P(B) from injected arrays only.

    No file read, no VAL, no decoder. Reuses ``build_canonical_counts``
    with axis ``(Alice, Bob)`` and derives ``p_b`` from ``axis0``.
    External ``p_b`` is not accepted (no such parameter).
    """
    alice = _as_int_vector("alice_symbols", alice_symbols, 0, Q - 1)
    bob = _as_int_vector("bob_symbols", bob_symbols, 0, Q - 1)
    frames = _as_int_vector("frame_ids", frame_ids, CAL_START, CAL_END)
    if not (alice.shape == bob.shape == frames.shape):
        raise ValueError("alice/bob/frame_ids must share length")
    if alice.size != N_CAL_SYMBOLS:
        raise ValueError(
            f"full CAL input must hold {N_CAL_SYMBOLS} rows, got {alice.size}"
        )
    uniq, counts = np.unique(frames, return_counts=True)
    want = np.arange(CAL_START, CAL_END + 1, dtype=np.int64)
    if uniq.shape != want.shape or not np.array_equal(uniq, want):
        raise ValueError("frame_ids must be exactly 702..1725")
    if not np.all(counts == PAIRS_PER_FRAME):
        raise ValueError("every CAL frame must hold exactly 256 rows")
    counts_f = build_canonical_counts(alice, bob, q=Q)
    counts_ab = np.asarray(counts_f, dtype=np.float64).astype(np.int64)
    if counts_ab.shape != (Q, Q):
        raise ValueError("counts_ab must have shape (1024, 1024)")
    if np.any(counts_ab < 0):
        raise ValueError("counts_ab must be nonnegative")
    if int(counts_ab.sum()) != N_CAL_SYMBOLS:
        raise ValueError("counts_ab must sum to 262144")
    bob_counts = counts_ab.sum(axis=0).astype(np.int64)
    if bob_counts.shape != (Q,):
        raise ValueError("bob marginal must have shape (1024,)")
    p_b = bob_counts.astype(np.float64) / float(N_CAL_SYMBOLS)
    if not np.all(np.isfinite(p_b)) or np.any(p_b < 0):
        raise ValueError("p_b must be finite and nonnegative")
    if abs(float(p_b.sum()) - 1.0) > 1e-8:
        raise ValueError("p_b must sum to 1")
    return {
        "counts_ab": counts_ab,
        "p_b": p_b,
        "n_frames": int(N_CAL_FRAMES),
        "n_symbols": int(N_CAL_SYMBOLS),
        "cal_start": int(CAL_START),
        "cal_end": int(CAL_END),
        "session": str(SESSION_ID),
        "lambda_star": float(LAMBDA_STAR),
    }


def _check_counts_p_b(counts_ab, p_b):
    counts = np.asarray(counts_ab)
    pb = np.asarray(p_b, dtype=np.float64)
    if counts.shape != (Q, Q):
        raise ValueError("counts_ab must have shape (1024, 1024)")
    if counts.dtype.kind not in ("i", "u"):
        raise ValueError("counts_ab must hold integers")
    if np.any(counts < 0):
        raise ValueError("counts_ab must be nonnegative")
    if int(counts.sum()) != N_CAL_SYMBOLS:
        raise ValueError("counts_ab must sum to 262144")
    if pb.shape != (Q,):
        raise ValueError("p_b must have shape (1024,)")
    if pb.dtype.kind != "f":
        raise ValueError("p_b must be float64")
    if not np.all(np.isfinite(pb)) or np.any(pb < 0):
        raise ValueError("p_b must be finite and nonnegative")
    if abs(float(pb.sum()) - 1.0) > 1e-8:
        raise ValueError("p_b must sum to 1")
    expect = counts.sum(axis=0).astype(np.float64) / float(N_CAL_SYMBOLS)
    if not np.allclose(pb, expect, atol=1e-12):
        raise ValueError("p_b must equal counts marginal/262144")
    return counts.astype(np.int64), pb.astype(np.float64)


def _build_summary():
    return {
        "schema": str(INPUT_SCHEMA),
        "cycle": str(CYCLE_ID),
        "session": str(SESSION_ID),
        "source": str(SOURCE_LABEL),
        "cal_start": int(CAL_START),
        "cal_end": int(CAL_END),
        "n_frames": int(N_CAL_FRAMES),
        "pairs_per_frame": int(PAIRS_PER_FRAME),
        "n_symbols": int(N_CAL_SYMBOLS),
        "axis": ["Alice", "Bob"],
        "dims": [int(Q), int(Q)],
        "mapping": "symbol=low+32*high;high=U1;low=U2",
        "field": {"q": int(GF_Q), "poly": int(GF_POLY)},
        "lambda_star": float(LAMBDA_STAR),
        "selection": "D4R2 nested-CV refit",
        "cal_only": True,
        "val_rows_read": 0,
        "decoder_calls": 0,
        "p0_calls": 0,
        "formal": False,
        "status": str(STATUS_CANDIDATE),
        "artifact_files": [str(NPZ_NAME), str(JSON_NAME)],
    }


def _check_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError("summary must be a mapping")
    if summary.get("schema") != INPUT_SCHEMA:
        raise ValueError("summary schema must be v72p2d5_model_f_input_v1")
    if summary.get("cycle") != CYCLE_ID:
        raise ValueError("summary belongs to another cycle")
    if summary.get("session") != SESSION_ID:
        raise ValueError("summary session must be 20260123_1M_600k_0dB")
    if summary.get("source") != SOURCE_LABEL:
        raise ValueError("summary source must be 1M")
    if int(summary.get("cal_start", -1)) != CAL_START:
        raise ValueError("summary cal_start must be 702")
    if int(summary.get("cal_end", -1)) != CAL_END:
        raise ValueError("summary cal_end must be 1725")
    if int(summary.get("n_frames", -1)) != N_CAL_FRAMES:
        raise ValueError("summary n_frames must be 1024")
    if int(summary.get("pairs_per_frame", -1)) != PAIRS_PER_FRAME:
        raise ValueError("summary pairs_per_frame must be 256")
    if int(summary.get("n_symbols", -1)) != N_CAL_SYMBOLS:
        raise ValueError("summary n_symbols must be 262144")
    if list(summary.get("axis", [])) != ["Alice", "Bob"]:
        raise ValueError("summary axis must be [Alice, Bob]")
    if list(summary.get("dims", [])) != [Q, Q]:
        raise ValueError("summary dims must be [1024, 1024]")
    if summary.get("mapping") != "symbol=low+32*high;high=U1;low=U2":
        raise ValueError("summary mapping mismatch")
    field = summary.get("field", {})
    if not isinstance(field, dict) or int(field.get("q", -1)) != GF_Q:
        raise ValueError("summary field.q must be 32")
    if int(field.get("poly", -1)) != GF_POLY:
        raise ValueError("summary field.poly must be 37")
    if float(summary.get("lambda_star", float("nan"))) != float(LAMBDA_STAR):
        raise ValueError("summary lambda_star mismatch")
    if summary.get("selection") != "D4R2 nested-CV refit":
        raise ValueError("summary selection mismatch")
    if summary.get("cal_only") is not True:
        raise ValueError("summary cal_only must be true")
    if int(summary.get("val_rows_read", -1)) != 0:
        raise ValueError("summary val_rows_read must be 0")
    if int(summary.get("decoder_calls", -1)) != 0:
        raise ValueError("summary decoder_calls must be 0")
    if int(summary.get("p0_calls", -1)) != 0:
        raise ValueError("summary p0_calls must be 0")
    if summary.get("formal") is not False:
        raise ValueError("summary formal must be false")
    if summary.get("status") not in (STATUS_CANDIDATE, STATUS_ACCEPTED):
        raise ValueError("summary status must be CANDIDATE or ACCEPTED")
    if list(summary.get("artifact_files", [])) != [NPZ_NAME, JSON_NAME]:
        raise ValueError("summary artifact_files must list the 2 files")


def write_model_f_input(out_dir, counts_ab, p_b):
    """Write exactly the 2 frozen files to a fresh directory."""
    counts, pb = _check_counts_p_b(counts_ab, p_b)
    summary = _build_summary()
    _check_summary(summary)
    d = Path(out_dir)
    if d.exists():
        raise FileExistsError(f"refusing to overwrite model-F input dir: {d}")
    d.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(str(d / NPZ_NAME), counts_ab=counts, p_b=pb)
    with open(str(d / JSON_NAME), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    names = {item.name for item in d.iterdir()}
    if names != {NPZ_NAME, JSON_NAME}:
        raise RuntimeError("model-F input root must contain exactly 2 files")
    return d


def load_model_f_input(in_dir):
    """Reload and revalidate the 2 frozen files (read-only, no decoder)."""
    d = Path(in_dir)
    names = {item.name for item in d.iterdir()}
    if names != {NPZ_NAME, JSON_NAME}:
        raise ValueError("model-F input root must contain exactly 2 files")
    with open(str(d / JSON_NAME), "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    _check_summary(summary)
    data = np.load(str(d / NPZ_NAME), allow_pickle=False)
    keys = set(str(k) for k in data.files)
    if keys != {"counts_ab", "p_b"}:
        raise ValueError("model_f_input.npz keys must be exactly counts_ab/p_b")
    counts = np.asarray(data["counts_ab"])
    pb = np.asarray(data["p_b"], dtype=np.float64)
    if counts.dtype.kind == "O" or pb.dtype.kind == "O":
        raise ValueError("model-F arrays must not be objects")
    counts, pb = _check_counts_p_b(counts, pb)
    return {"counts_ab": counts, "p_b": pb, "summary": summary}
