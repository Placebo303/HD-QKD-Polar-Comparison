"""R1 histogram re-run — corrected conditional-MM + bundle materialization (G-R1).

DECIDE track, Acceptance ID G-R1. Frozen contract:
``docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PACKET.md``
(§§1–8) + ``R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md`` (authorization of record).
Implementation only — importing this module executes nothing.

This module is an ADDITIVE executor (new file; ``p3_census_a1.py`` untouched).
It reuses the frozen A1 read → §3A-alignment → pairing/framing → TRAIN-split
→ ``h_full_f03`` path byte-identically BY IMPORT (same function objects, same
arguments — no copied arithmetic):

- trio/member parsing: ``p3_census_a1.parse_bases`` / ``parse_datasets``
  (base ``X.ttbin`` only; ``.1.ttbin`` rejected; never both members);
- frozen constants: ``CH_A``/``CH_B``, ``COIN_WINDOW_PS``, ``BIN_WIDTH_PS``,
  ``FRAME_BINS``, ``ALIGN_MODE_FRAMING``, ``POSTSELECT``,
  ``PAIRING_THRESHOLD_PS``, ``FILENAME_DURATION_TAG``,
  ``PER_DATASET_CEILING_S``, ``DATASET_IDS``, ``PRIOR_OFFSET_PS``,
  ``PRIOR_BIN``;
- frozen estimator: ``p3_census_a1.h_full_f03`` (conditional ``H_L1+H_L2``,
  F03 ``u1=a>>5``, ``u2=a&31``);
- frozen alignment: ``align_wrapper.derive_alignment`` /
  ``require_alignment_passed`` / ``offsets_agree_one_bin``
  (``compute_cross_correlation_histogram`` 100 ps / ±819200 ps → argmax →
  ``offset_ps = +lag_center_ps[pk]``);
- frozen loader arithmetic: ``src.qkd_io.ttbin_pipeline.read_ttbin_events``,
  ``compute_ttbin_metrics``, ``_pair_nearest_unique``, ``_frame_global``
  (same call signatures as A1, including the series==aggregate
  ``n_symbols`` assertion and the 60/20/20 consecutive-time split).

ADD ONLY (packet §2.5–2.6 — everything below is new, nothing frozen changed):

- (i) ``K_B_train`` = occupied marginal-B columns of TRAIN ``N_ab``;
- (ii) ``p_b_train`` (1024,) float64 sum=1;
- (iii) sparse COO persistence of TRAIN ``N_ab`` (npz keys ``row``/``col``/
  ``count`` int64, ``shape=(1024,1024)``, ``N_train``);
- (iv) corrected ``H_corr = H_plug + (K_AB−K_B)/(2·N·ln2)`` alongside the
  defective ``H_MM_old = H_plug + (K_AB−1)/(2·N·ln2)`` and ``Δ``;
- (v) bootstrap CI on the CORRECTED statistic (frame-level, ≥200 resamples,
  frozen seed 20260921 — REQUIRED, no waiver);
- (vi) per-source JSON + shared design-point/delta tables (packet §2.9).

Skipped by design (histogram-only cost; packet §2.8/X1-T4): A1's per-frame
weight/ACF/block-drift/hold-NLL diagnostics are not recomputed here.

Gates (packet §4, binary per gate; per-source STOP-BLOCKED ⇒ continue other
sources, never fall back): (a) §3A alignment; (b) span-continuity
(span>0 AND |span−mtime_gap|≤tol); (c) both-or-neither artifact atomicity;
(d) ``K_B`` sanity (1≤K_B≤1024 AND K_B<K_AB); (e) 2M consistency
(report-only FINDING, never refit/substitute); (f) determinism vs the A1
census root (read-only; mismatch ⇒ STOP-BLOCKED).

Budget enforcement BY CONSTRUCTION: monotonic-clock checks per read, per
dataset (≤1800 s, reused ``PER_DATASET_CEILING_S``) and trio (``--budget-s``,
default 5400 s); wall-partial ⇒ INCOMPLETE, retained, never continued.
Trio order 1M → 1.5M → 2M enforced. Wall + peak-RSS telemetry persisted to
``telemetry.json``. Root creation REFUSES a pre-existing root.

House style follows ``p3_census_a1.py``: ``main() -> int`` +
``if __name__ == "__main__": raise SystemExit(main())``. Research code
(AGENTS.md §5.7): plain functions, no defensive machinery beyond what the
frozen gates need.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
from comparison_bench.src.comparison_bench.io import align_wrapper as aw

# Frozen A1 path reused BY IMPORT (byte-identical arithmetic; nothing copied).
from comparison_bench.src.comparison_bench.cli.p3_census_a1 import (
    ALIGN_MODE_FRAMING,
    BIN_WIDTH_PS,
    CH_A,
    CH_B,
    COIN_WINDOW_PS,
    DATASET_IDS,
    FILENAME_DURATION_TAG,
    FRAME_BINS,
    PAIRING_THRESHOLD_PS,
    PER_DATASET_CEILING_S,
    POSTSELECT,
    PRIOR_BIN,
    PRIOR_OFFSET_PS,
    h_full_f03,
    parse_bases,
    parse_datasets,
)

# R1-only frozen constants (packet §§2.5–2.8, prereg §§2–3).
LN2 = math.log(2.0)
SLOPE_FROZEN = 4.785675
M_CAP = 208
BOOTSTRAP_SEED_FROZEN = 20260921
BOOTSTRAP_MIN_RESAMPLES = 200
BUDGET_TRIO_S = 5400.0
PER_READ_TIMEOUT_S = 300.0
SPAN_TOL_S_DEFAULT = 0.5
A1_ROOT_DEFAULT = "workspace/p3_census_3954637c"
GAMMA_DEFAULT = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
PB_SIDECAR_NAME = "gamma_f03_pb.npz"
BUNDLE_SRC_2M = "2M"
FROZEN_2M_TRAIN_N = 559872.0  # packet §2.7 (cross-checked vs sidecar 2M_N)
DH_MATERIAL = 0.01  # |ΔH| per plane materiality bar (packet §2.7)
PB_MATERIAL = 1e-3  # p_b L_inf materiality bar (packet §2.7)
PB_NORM_TOL = 1e-9  # p_b sum=1 gate (bundle convention)

# Baseline §3 frozen verdicts (reference strings for delta_vs_baseline_S3.md;
# arithmetic comparison itself is recomputed from A1 H_full_MM at runtime).
BASELINE_VERDICT = {
    "T2-1M": "OUT@208 / IN@200 (m_max 201)",
    "T2-1.5M": "INDETERMINATE@208 (m_max 207)",
    "T2-2M": "IN@208 (m_max 209→cap 208)",
}


def shard_path(base: str) -> str:
    """Shard companion path (mtime-gap only; never opened here)."""
    return base[: -len(".ttbin")] + ".1.ttbin"


# --------------------------------------------------------------------------
# R1 pure additions (packet §2.5): K_B / p_b / Miller–Madow terms.
# --------------------------------------------------------------------------

def k_b_of_nab(N_ab: np.ndarray) -> int:
    """Occupied marginal-B columns: #{b : N_ab[:,b].sum() > 0}."""
    N = np.asarray(N_ab)
    return int((N.sum(axis=0) > 0).sum())


def p_b_of_nab(N_ab: np.ndarray) -> np.ndarray:
    """B marginal (1024,) float64, sum=1."""
    N = np.asarray(N_ab, dtype=np.float64)
    tot = float(N.sum())
    if tot <= 0:
        return np.zeros((1024,), dtype=np.float64)
    return (N.sum(axis=0) / tot).astype(np.float64)


def mm_corrected(K_AB: int, K_B: int, N: int) -> float:
    """Correct first-order conditional-MM term (K_AB−K_B)/(2·N·ln2)."""
    return (int(K_AB) - int(K_B)) / (2.0 * int(N) * LN2)


def mm_defective(K_AB: int, N: int) -> float:
    """A1 defective joint-MM term (K_AB−1)/(2·N·ln2), persisted for audit."""
    return (int(K_AB) - 1) / (2.0 * int(N) * LN2)


def delta_mm(K_B: int, N: int) -> float:
    """Over-correction identity: H_MM_old − H_corr = (K_B−1)/(2·N·ln2) ≥ 0."""
    return (int(K_B) - 1) / (2.0 * int(N) * LN2)


# --------------------------------------------------------------------------
# R1 pure additions (packet §2.5): design-point arithmetic (full precision).
# --------------------------------------------------------------------------

def content_of(H: float) -> float:
    return 1024.0 * float(H)


def f_of_m(m: int, content: float) -> float:
    return (5 * int(m) + 64) / float(content)


def m_max_raw_of_H(H: float) -> int:
    return int(math.floor((1.3 * 1024.0 * float(H) - 64.0) / 5.0))


def n_req_of_f(f: float) -> int | None:
    """N_req = ceil(3·slope/(1.3−f)); None renders as inf (f ≥ 1.3)."""
    if float(f) >= 1.3:
        return None
    return int(math.ceil(3.0 * SLOPE_FROZEN / (1.3 - float(f))))


def threshold_H(m: int) -> float:
    """H threshold for f(m) ≤ 1.3: (5m+64)/(1024·1.3)."""
    return (5 * int(m) + 64) / (1024.0 * 1.3)


def design_point(H_corr: float) -> dict[str, Any]:
    """Full-precision design-point row for one corrected H (frozen rules)."""
    H = float(H_corr)
    content = content_of(H)
    m_raw = m_max_raw_of_H(H)
    m = min(m_raw, M_CAP)
    row: dict[str, Any] = {
        "H_corr": H,
        "content": content,
        "m_max_raw": m_raw,
        "m_max_capped": m,
    }
    for _m in (208, 200, 199):
        _f = f_of_m(_m, content)
        row[f"f_at_{_m}"] = _f
        row[f"N_req_at_{_m}"] = n_req_of_f(_f)
    _fm = f_of_m(m, content)
    row["f_at_mmax"] = _fm
    row["N_req_at_mmax"] = n_req_of_f(_fm)
    return row


# --------------------------------------------------------------------------
# R1 gate predicates (packet §4 — binary per gate).
# --------------------------------------------------------------------------

def span_gate_pass(span_s: float | None, gap_s: float | None, tol_s: float) -> bool:
    """Gate (b): span > 0 AND |span − mtime_gap| ≤ tol (gap None ⇒ FAIL)."""
    if span_s is None or gap_s is None:
        return False
    return bool(span_s > 0 and abs(span_s - gap_s) <= tol_s)


def k_b_gate_pass(K_B: int, K_AB: int) -> bool:
    """Gate (d): 1 ≤ K_B ≤ 1024 AND K_B < K_AB."""
    return bool(1 <= int(K_B) <= 1024 and int(K_B) < int(K_AB))


def determinism_check(
    *,
    n_pairs_N: int,
    n_frames: int,
    split_counts: tuple[int, int, int],
    split_ranges: tuple[list[int] | None, list[int] | None, list[int] | None],
    offset_ps_derived: int | None,
    peak_bin_index: int | None,
    duration_measured_s: float | None,
    a1_row: dict[str, Any] | None,
    a1_split: dict[str, Any] | None,
) -> dict[str, Any]:
    """Gate (f): exact reproduction of the A1 census realization.

    Compares frame counts, split boundaries/counts and derived alignment
    against the read-only A1 reference. Missing reference ⇒ FAIL (fail
    closed — gate (f) is unverifiable without it).
    """
    fields: dict[str, bool] = {}
    if a1_row is None or a1_split is None:
        return {"pass": False, "fields": {"a1_reference_present": False},
                "reason": "A1 reference unavailable (fail closed)"}
    fields["a1_reference_present"] = True
    fields["n_pairs_N"] = (int(n_pairs_N) == int(a1_row["n_pairs_N"]))
    fields["n_frames"] = (int(n_frames) == int(a1_row["n_frames"]))
    for key, got in zip(("split_train_frames", "split_val_frames",
                         "split_hold_frames"), split_counts):
        fields[key] = (int(got) == int(a1_row[key]))
    for key, got in zip(("train_frames", "val_frames", "hold_frames"),
                        split_ranges):
        want = a1_split.get(key)
        fields[key] = (got is not None and want is not None
                       and [int(v) for v in got] == [int(v) for v in want])
    fields["offset_ps_derived"] = (offset_ps_derived is not None
                                   and int(offset_ps_derived)
                                   == int(a1_row["offset_ps_derived"]))
    fields["peak_bin_index"] = (peak_bin_index is not None
                                and int(peak_bin_index)
                                == int(a1_row["peak_bin_index"]))
    want_dur = a1_row.get("duration_measured_s")
    fields["duration_measured_s"] = (
        duration_measured_s is not None and want_dur is not None
        and float(duration_measured_s) == float(want_dur))
    ok = bool(all(fields.values()))
    return {"pass": ok, "fields": fields,
            "reason": None if ok else "determinism mismatch vs A1 (see fields)"}


# --------------------------------------------------------------------------
# R1 sparse COO persistence (packet §2.6 item 3).
# --------------------------------------------------------------------------

def save_sparse_nab(path: str | Path, N_ab_int: np.ndarray) -> dict[str, Any]:
    """Persist TRAIN N_ab as int64 COO triplets (+ shape, N_train)."""
    N = np.asarray(N_ab_int, dtype=np.int64)
    rows, cols = np.nonzero(N)
    np.savez(str(path),
             row=rows.astype(np.int64),
             col=cols.astype(np.int64),
             count=N[rows, cols].astype(np.int64),
             shape=np.array([1024, 1024], dtype=np.int64),
             N_train=np.int64(int(N.sum())))
    return {"sparse_sum": int(N.sum()), "sparse_nnz": int(rows.size)}


def load_sparse_nab(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    """Reload COO npz → (dense int64 (1024,1024), meta). Read-only load."""
    z = np.load(str(path), allow_pickle=False)
    try:
        shape = tuple(int(v) for v in np.asarray(z["shape"]).tolist())
        n_train = int(z["N_train"])
        row = np.asarray(z["row"], dtype=np.int64)
        col = np.asarray(z["col"], dtype=np.int64)
        count = np.asarray(z["count"], dtype=np.int64)
    finally:
        z.close()
    if shape != (1024, 1024):
        raise ValueError(f"sparse shape {shape} != (1024, 1024)")
    dense = np.zeros((1024, 1024), dtype=np.int64)
    dense[row, col] = count
    return dense, {"N_train": n_train, "nnz": int(row.size),
                   "sum": int(dense.sum())}


def trio_paths(root: Path, dataset_id: str) -> tuple[Path, Path, Path]:
    return (root / f"{dataset_id}.json",
            root / f"{dataset_id}_N_ab_train_sparse.npz",
            root / f"{dataset_id}_p_b_train.npy")


def trio_complete(paths: tuple[Path, Path, Path]) -> bool:
    return all(p.exists() for p in paths)


def remove_trio(paths: tuple[Path, Path, Path]) -> None:
    """Best-effort removal of a partially written trio (gate (c))."""
    for p in paths:
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


# --------------------------------------------------------------------------
# Deliverable 2 (packet §2.7): 2M consistency reporter — READ-ONLY.
# --------------------------------------------------------------------------

def compare_2m_bundle(
    *,
    N_train: int,
    H_L1: float,
    H_L2: float,
    p_b: np.ndarray,
    gamma_path: str,
    pb_name: str = PB_SIDECAR_NAME,
) -> dict[str, Any]:
    """Compare re-derived 2M inputs vs the frozen bundle lineage (report-only).

    Opens the frozen ``gamma_f03.npz`` lineage READ-ONLY (``np.load`` only —
    this function contains NO refit/overwrite/substitution path and MUST NEVER
    gain one; the re-derived bundle is NEVER substituted into any decoder
    path). Reports ΔN_train (a delta is EXPECTED — different pairing vintage,
    never a discrepancy finding by itself), per-plane ΔH_L1/ΔH_L2 and the p_b
    max-abs-diff. Materiality bar: |ΔH|>0.01 b/sym per plane OR p_b L_inf>1e-3
    ⇒ FINDING escalated in the result record.
    """
    rec: dict[str, Any] = {"ran": False, "source": BUNDLE_SRC_2M,
                           "gamma_path": str(gamma_path)}
    try:
        z = np.load(str(gamma_path), allow_pickle=False)
        try:
            fH1 = float(z[f"{BUNDLE_SRC_2M}_H_L1"])
            fH2 = float(z[f"{BUNDLE_SRC_2M}_H_L2"])
        finally:
            z.close()
        side = Path(str(gamma_path)).parent / pb_name
        sp = np.load(str(side), allow_pickle=False)
        try:
            fpb = np.asarray(sp[f"{BUNDLE_SRC_2M}_p_b"], dtype=np.float64)
            side_N = float(sp[f"{BUNDLE_SRC_2M}_N"]) \
                if f"{BUNDLE_SRC_2M}_N" in sp.files else None
        finally:
            sp.close()
    except Exception as exc:
        rec["ran"] = False
        rec["reason"] = (f"frozen lineage unreadable "
                         f"({type(exc).__name__}: {exc}); report-only, not gated")
        rec["finding"] = False
        return rec
    pb = np.asarray(p_b, dtype=np.float64)
    dH1 = float(H_L1) - fH1
    dH2 = float(H_L2) - fH2
    linf = float(np.max(np.abs(pb - fpb)))
    material = bool(abs(dH1) > DH_MATERIAL or abs(dH2) > DH_MATERIAL
                    or linf > PB_MATERIAL)
    rec.update({
        "ran": True,
        "N_train_r1": int(N_train),
        "N_train_frozen_packet": FROZEN_2M_TRAIN_N,
        "N_train_frozen_sidecar": side_N,
        "delta_N_train_vs_frozen": int(N_train) - FROZEN_2M_TRAIN_N,
        "delta_N_expected_note": ("delta EXPECTED — different pairing "
                                  "vintage/scope; N alone is never a "
                                  "discrepancy finding"),
        "H_L1_r1": float(H_L1), "H_L1_frozen": fH1, "delta_H_L1": dH1,
        "H_L2_r1": float(H_L2), "H_L2_frozen": fH2, "delta_H_L2": dH2,
        "p_b_max_abs_diff": linf,
        "materiality_bar": (f"|ΔH|>{DH_MATERIAL}/plane OR "
                            f"p_b L_inf>{PB_MATERIAL}"),
        "material": material,
        "finding": material,
    })
    return rec


# --------------------------------------------------------------------------
# Per-dataset executor.
# --------------------------------------------------------------------------

def _write_json(path: Path, rec: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)


def run_dataset(
    dataset_id: str,
    base: str,
    root: Path,
    *,
    per_read_timeout_s: float,
    global_deadline: float,
    bootstrap_seed: int,
    bootstrap_resamples: int,
    span_tol_s: float,
    splits_so_far: dict[str, Any],
    a1_rows: dict[str, Any] | None,
    a1_splits: dict[str, Any] | None,
    gamma_path: str,
) -> dict[str, Any]:
    """Execute ONE R1 dataset arm. Returns the per-dataset record (always)."""
    t_ds = time.monotonic()
    rec: dict[str, Any] = {
        "dataset_id": dataset_id,
        "family": "R1",
        "ttbin_path": base,
        "ttbin_member_used": None,
        "duration_measured_s": None,
        "filename_duration_tag": FILENAME_DURATION_TAG,
        "tag_disputed": None,
        "mtime_base": None,
        "mtime_shard": None,
        "mtime_gap_s": None,
        "span_tol_s": float(span_tol_s),
        "span_gate_pass": None,
        "alignment_mode": "CONFIGURED",
        "channels_A": CH_A,
        "channels_B": CH_B,
        "offset_ps": None,
        "coin_window_ps": COIN_WINDOW_PS,
        "pairing_threshold_ps": PAIRING_THRESHOLD_PS,
        "bin_width_ps": BIN_WIDTH_PS,
        "frame_bins": FRAME_BINS,
        "align": ALIGN_MODE_FRAMING,
        "postselect": POSTSELECT,
        "framing_provenance": "MEASURED",
        "offset_ps_prior_recorded": PRIOR_OFFSET_PS[dataset_id],
        "prior_bin_index": PRIOR_BIN[dataset_id],
        "status": "BLOCKED",
    }
    trio = trio_paths(root, dataset_id)

    def wall_left(ds_elapsed: float) -> bool:
        return ds_elapsed <= PER_DATASET_CEILING_S and time.monotonic() <= global_deadline

    def blocked(reason: str) -> dict[str, Any]:
        rec["status"] = "BLOCKED"
        rec["block_reason"] = reason
        _write_json(trio[0], rec)
        return rec

    def incomplete(reason: str) -> dict[str, Any]:
        rec["status"] = "INCOMPLETE"
        rec["block_reason"] = reason
        _write_json(trio[0], rec)
        return rec

    # (0) mtime stat for the span-continuity gate (read-only; shard stat may
    # be absent ⇒ gap None ⇒ gate (b) FAILs closed).
    try:
        st_b = os.stat(base)
        rec["mtime_base"] = st_b.st_mtime
        try:
            st_s = os.stat(shard_path(base))
            rec["mtime_shard"] = st_s.st_mtime
            rec["mtime_gap_s"] = st_s.st_mtime - st_b.st_mtime
        except OSError:
            pass
    except OSError as exc:
        return blocked(f"stat failed (single member only, never both): {exc}")

    # (1) Open base member ONLY (frozen A1 path — no .1 fallback: R1 is
    # base-only; vendor auto-follow covers .1 inside the read).
    from TimeTagger import FileReader  # noqa: E402  (alias installed in main)

    try:
        reader = FileReader(base)
    except Exception as exc:
        return blocked(f"base open failed (single member only, never both): {exc}")
    rec["ttbin_member_used"] = base
    # (1b) Read events via the frozen loader (full vendor-auto-followed stream).
    from src.qkd_io.ttbin_pipeline import (  # noqa: E402  (frozen, read-only)
        _frame_global,
        _pair_nearest_unique,
        compute_ttbin_metrics,
        read_ttbin_events,
    )

    t_read = time.monotonic()
    try:
        events = read_ttbin_events(base)
    except Exception as exc:
        return blocked(f"frozen read_ttbin_events failed: {exc}")
    finally:
        try:
            reader.close()
        except Exception:
            pass
    read_s = time.monotonic() - t_read
    rec["read_wall_s"] = read_s
    if read_s > per_read_timeout_s:
        return incomplete(f"per-read wall {read_s:.1f}s exceeded {per_read_timeout_s:.0f}s")
    t = np.asarray(events.time_ps, dtype=np.int64)
    if t.size:
        rec["duration_measured_s"] = float(t.max() - t.min()) * 1e-12
        rec["tag_disputed"] = bool(abs(rec["duration_measured_s"] - 3.0) > 0.5)

    # (R1-b) Span-continuity gate BEFORE the alignment compute (fail fast).
    rec["span_gate_pass"] = span_gate_pass(
        rec["duration_measured_s"], rec["mtime_gap_s"], float(span_tol_s))
    if not rec["span_gate_pass"]:
        return blocked(
            f"span-continuity FAIL (span={rec['duration_measured_s']}, "
            f"mtime_gap={rec['mtime_gap_s']}, tol={span_tol_s})")

    # (2) Derive alignment per §3A (frozen histogram + gates).
    t_align = time.monotonic()
    align = aw.derive_alignment(events=events, ch_a=CH_A, ch_b=CH_B)
    align["align_wall_s"] = time.monotonic() - t_align
    for k in ("offset_ps_derived", "peak_bin_index", "peak_center_ps",
              "peak_to_bg", "sigma_crude_ps", "align_status"):
        rec[k] = align[k]
    rec["alignment"] = {k: v for k, v in align.items()
                        if k in ("bin_width_ps", "max_lag_ps", "n_bins", "count_A",
                                 "count_B", "total_pairs_in_window", "single_mode_ok",
                                 "n_local_maxima", "n_secondary_violations", "align_wall_s")}
    rec["one_bin_check"] = aw.offsets_agree_one_bin(
        derived_offset_ps=align["offset_ps_derived"] if align["offset_ps_derived"] is not None else -10**12,
        derived_bin=align["peak_bin_index"] if align["peak_bin_index"] is not None else -10**12,
        prior_offset_ps=PRIOR_OFFSET_PS[dataset_id], prior_bin=PRIOR_BIN[dataset_id])

    # (3) Alignment FAIL ⇒ STOP-BLOCKED for this dataset (no fallback).
    if align["align_status"] != "ok":
        return blocked(f"alignment {align['align_status']}; no pairing/entropy (no fallback)")

    # (4) Passed only: adopt the DERIVED offset (gate raises otherwise).
    offset = aw.require_alignment_passed(align)
    rec["offset_ps"] = offset
    cfg = {
        "channels": {"A": CH_A, "B": CH_B},
        "pairing": {"coin_window_ps": COIN_WINDOW_PS, "offset_ps": offset,
                    "policy": "nearest_unique"},
        "framing": {"bin_width_ps": BIN_WIDTH_PS, "frame_bins": FRAME_BINS,
                    "align": ALIGN_MODE_FRAMING, "postselect": POSTSELECT},
    }
    metrics = compute_ttbin_metrics(events=events, cfg=cfg)
    rec["ttbin_config"] = cfg
    rec["qber"] = metrics["framed"]["qber"]
    rec["mutual_information_bits"] = metrics["framed"]["mutual_information_bits"]

    # Per-pair series from the SAME frozen arithmetic (read-only reuse).
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
        if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a = t[valid & (ch == CH_A)]
    t_b = t[valid & (ch == CH_B)]
    tmin = int(t.min()) if t.size else 0
    del events  # raw stream no longer needed; bound RSS
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                  window_ps=COIN_WINDOW_PS, offset_ps=offset)
    del t_a, t_b
    if ALIGN_MODE_FRAMING == "global":
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=BIN_WIDTH_PS,
                               frame_bins=FRAME_BINS, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=BIN_WIDTH_PS,
                               frame_bins=FRAME_BINS, t0_ps=tmin)
    else:  # pragma: no cover — frozen R1 choice is global
        raise SystemExit("R1 framing is frozen to global")
    keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
    frame, sa, sb = fa[keep], sa[keep], sb[keep]
    del pa, pb, fa, fb
    # Control-arm equality assertion vs the frozen aggregates.
    assert int(frame.size) == int(metrics["framed"]["n_symbols"]), \
        f"series/aggregate n_symbols mismatch: {frame.size} vs {metrics['framed']['n_symbols']}"
    rec["n_pairs_N"] = int(frame.size)
    rec["n_frames"] = int(np.unique(frame).size) if frame.size else 0

    # Split 60/20/20 consecutive-time by ascending frame index — decided AND
    # written BEFORE any statistic is computed (packet §2.4).
    uframes = np.unique(frame)
    nfr = int(uframes.size)
    n_tr = int(nfr * 0.6)
    n_va = int(nfr * 0.2)
    split = {
        "rule": "60/20/20 consecutive-time by ascending frame index (V49 convention)",
        "train_frames": [int(uframes[0]), int(uframes[n_tr - 1])] if n_tr else None,
        "val_frames": [int(uframes[n_tr]), int(uframes[n_tr + n_va - 1])] if n_va else None,
        "hold_frames": [int(uframes[n_tr + n_va]), int(uframes[-1])] if nfr - n_tr - n_va else None,
        "split_train_frames": n_tr,
        "split_val_frames": n_va,
        "split_hold_frames": int(nfr - n_tr - n_va),
    }
    rec["split_train_frames"] = n_tr
    rec["split_val_frames"] = n_va
    rec["split_hold_frames"] = int(nfr - n_tr - n_va)
    splits_so_far[dataset_id] = split
    with open(root / "split_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(splits_so_far, fh, indent=2)

    # (R1-f) Determinism vs A1 (fail closed; before any statistic).
    det = determinism_check(
        n_pairs_N=rec["n_pairs_N"], n_frames=rec["n_frames"],
        split_counts=(n_tr, n_va, int(nfr - n_tr - n_va)),
        split_ranges=(split["train_frames"], split["val_frames"],
                      split["hold_frames"]),
        offset_ps_derived=rec["offset_ps_derived"],
        peak_bin_index=rec["peak_bin_index"],
        duration_measured_s=rec["duration_measured_s"],
        a1_row=(a1_rows or {}).get(dataset_id),
        a1_split=(a1_splits or {}).get(dataset_id))
    rec["determinism_vs_a1"] = det
    if not det["pass"]:
        return blocked(f"determinism gate (f) FAIL: {det.get('reason')} "
                       f"fields={det.get('fields')}")

    # TRAIN-pool histogram (same bincount call as A1; int64 retained for the
    # sparse persistence, float64 view feeds the frozen estimator).
    order = np.argsort(frame, kind="stable")
    fs = frame[order]
    as_ = sa[order]
    bs = sb[order]
    uniq, inv, cnt = np.unique(fs, return_inverse=True, return_counts=True)
    tr_mask = inv < n_tr
    tr_idx = order[tr_mask]
    N_ab_int = np.bincount(as_[tr_idx] * 1024 + bs[tr_idx],
                           minlength=1024 * 1024).reshape(1024, 1024)
    N_train = int(N_ab_int.sum())
    K_AB = int(np.count_nonzero(N_ab_int))
    N_ab = N_ab_int.astype(np.float64)
    K_B = k_b_of_nab(N_ab)
    p_b = p_b_of_nab(N_ab)
    rec["N_train"] = N_train
    rec["K_AB_train"] = K_AB
    rec["K_B_train"] = K_B
    rec["occupancy_train"] = K_AB / (1024 * 1024)

    # (R1-d) K_B sanity.
    rec["k_b_gate_pass"] = k_b_gate_pass(K_B, K_AB)
    if not rec["k_b_gate_pass"]:
        return blocked(f"K_B sanity FAIL (K_B={K_B}, K_AB={K_AB})")

    # Estimator: frozen plug-in + corrected/defective MM + delta (§2.5).
    H1, H2, Hf = h_full_f03(N_ab)
    mm_c = mm_corrected(K_AB, K_B, N_train) if N_train > 0 else None
    mm_o = mm_defective(K_AB, N_train) if N_train > 0 else None
    rec["H_L1"] = H1
    rec["H_L2"] = H2
    rec["H_full_plug"] = Hf
    rec["H_corr"] = (Hf + mm_c) if mm_c is not None else None
    rec["H_MM_old"] = (Hf + mm_o) if mm_o is not None else None
    rec["Delta_MM"] = (rec["H_MM_old"] - rec["H_corr"]) \
        if (mm_c is not None and mm_o is not None) else None
    rec["MM_correction_corr"] = mm_c
    rec["MM_correction_old"] = mm_o
    rec["split_side"] = ("TRAIN plug-in + TRAIN-side MM (corrected and "
                         "defective persisted side by side; never quoted as held-out)")

    # Frame-level bootstrap CI on the CORRECTED statistic (REQUIRED — the
    # per-replicate statistic is H_plug + its own (K_AB−K_B)/(2N ln2)).
    rng = np.random.default_rng(int(bootstrap_seed))
    tr_inv = inv[tr_mask]
    tr_order = np.argsort(tr_inv, kind="stable")
    bounds = np.searchsorted(tr_inv[tr_order], np.arange(n_tr + 1))
    flat = tr_idx[tr_order]
    boots = np.empty(int(bootstrap_resamples))
    for r in range(int(bootstrap_resamples)):
        pick = rng.integers(0, n_tr, size=n_tr)
        idx = np.concatenate([flat[bounds[p]:bounds[p + 1]] for p in pick.tolist()])
        Nb = np.bincount(as_[idx] * 1024 + bs[idx],
                         minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
        _, _, Hfb = h_full_f03(Nb)
        Nb_sum = int(Nb.sum())
        if Nb_sum > 0:
            Kb_AB = int(np.count_nonzero(Nb))
            Kb_B = k_b_of_nab(Nb)
            boots[r] = Hfb + mm_corrected(Kb_AB, Kb_B, Nb_sum)
        else:  # unreachable in practice (every frame is non-empty); keep defined
            boots[r] = Hfb
    rec["bootstrap_resamples"] = int(bootstrap_resamples)
    rec["bootstrap_seed"] = int(bootstrap_seed)
    rec["bootstrap_statistic"] = ("H_corr per replicate (frame-level resample; "
                                  "frozen seed; REQUIRED, no waiver path)")
    rec["bootstrap_CI_halfwidth"] = float((np.percentile(boots, 97.5) - np.percentile(boots, 2.5)) / 2)
    rec["bootstrap_CI_lo"] = float(np.percentile(boots, 2.5))
    rec["bootstrap_CI_hi"] = float(np.percentile(boots, 97.5))

    # Design-point row (frozen arithmetic, full precision).
    rec["design_point"] = design_point(float(rec["H_corr"]))

    # (R1-c) Both-or-neither persistence + reload verification. ALL three
    # artifacts persist or NONE does; partial writes are removed.
    try:
        sparse_sums = save_sparse_nab(trio[1], N_ab_int)
        np.save(str(trio[2]), p_b)
        dense_chk, meta = load_sparse_nab(trio[1])
        if not np.array_equal(dense_chk, N_ab_int):
            raise ValueError("sparse round-trip mismatch")
        if meta["N_train"] != N_train or meta["nnz"] != K_AB:
            raise ValueError("sparse checksum mismatch")
        del dense_chk
        pb_chk = np.load(str(trio[2]))
        try:
            if pb_chk.shape != (1024,):
                raise ValueError("p_b shape mismatch")
            if not (np.all(np.isfinite(pb_chk)) and
                    abs(float(pb_chk.sum()) - 1.0) <= PB_NORM_TOL):
                raise ValueError("p_b normalization mismatch")
        finally:
            del pb_chk
        rec["sparse_artifact"] = str(trio[1].name)
        rec["sparse_sum"] = sparse_sums["sparse_sum"]
        rec["sparse_nnz"] = sparse_sums["sparse_nnz"]
        rec["sparse_shape"] = [1024, 1024]
        rec["p_b_artifact"] = str(trio[2].name)
        rec["p_b_sum"] = float(p_b.sum())
        rec["p_b_min"] = float(p_b.min())
        if dataset_id == "T2-2M":
            rec["consistency_2m"] = compare_2m_bundle(
                N_train=N_train, H_L1=H1, H_L2=H2, p_b=p_b,
                gamma_path=gamma_path)
        rec["status"] = "OK"
        _write_json(trio[0], rec)
        if not trio_complete(trio):
            raise ValueError("trio incomplete after write")
    except Exception as exc:
        remove_trio(trio)
        return incomplete(f"artifact persistence failed (both-or-neither, "
                          f"trio removed): {type(exc).__name__}: {exc}")

    ds_wall = time.monotonic() - t_ds
    rec["dataset_wall_s"] = ds_wall
    _write_json(trio[0], rec)
    if not wall_left(ds_wall):
        rec["status"] = "INCOMPLETE"
        rec["block_reason"] = f"dataset wall {ds_wall:.1f}s exceeded ceiling"
        _write_json(trio[0], rec)
    return rec


# --------------------------------------------------------------------------
# Shared tables (packet §2.9).
# --------------------------------------------------------------------------

def write_shared_tables(
    records: list[dict[str, Any]],
    root: Path,
    *,
    a1_rows: dict[str, Any] | None,
    trio_wall_s: float,
    peak_rss_kb: int,
    budget_s: float,
) -> None:
    align_lines = ["# R1 alignment + span table", "",
                   "| id | duration_measured_s | mtime_gap_s | span_pass | "
                   "offset_ps_derived | peak_bin_index | peak_center_ps | "
                   "peak_to_bg | sigma_crude_ps | align_status | "
                   "prior | one_bin_agree | finding | status |",
                   "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        ob = r.get("one_bin_check") or {}
        agree = ob.get("agree_one_bin")
        finding = "FINDING" if agree is False else ""
        align_lines.append(
            f"| {r['dataset_id']} | {r.get('duration_measured_s')} | "
            f"{r.get('mtime_gap_s')} | {r.get('span_gate_pass')} | "
            f"{r.get('offset_ps_derived')} | {r.get('peak_bin_index')} | "
            f"{r.get('peak_center_ps')} | {r.get('peak_to_bg')} | "
            f"{r.get('sigma_crude_ps')} | {r.get('align_status')} | "
            f"{r.get('offset_ps_prior_recorded')} | {agree} | {finding} | "
            f"{r.get('status')} |")
    (root / "alignment_table.md").write_text("\n".join(align_lines) + "\n", encoding="utf-8")

    dp_rows: list[dict[str, Any]] = []
    for r in records:
        dp = r.get("design_point") or {}
        dp_rows.append({
            "dataset_id": r["dataset_id"],
            "H_corr": r.get("H_corr"),
            "content": dp.get("content"),
            "m_max_raw": dp.get("m_max_raw"),
            "m_max_capped": dp.get("m_max_capped"),
            "f_at_208": dp.get("f_at_208"),
            "f_at_200": dp.get("f_at_200"),
            "f_at_199": dp.get("f_at_199"),
            "N_req_at_208": dp.get("N_req_at_208"),
            "N_req_at_200": dp.get("N_req_at_200"),
            "N_req_at_199": dp.get("N_req_at_199"),
            "f_at_mmax": dp.get("f_at_mmax"),
            "N_req_at_mmax": dp.get("N_req_at_mmax"),
            "CI_lo": r.get("bootstrap_CI_lo"),
            "CI_hi": r.get("bootstrap_CI_hi"),
            "CI_hw": r.get("bootstrap_CI_halfwidth"),
            "status": r.get("status"),
        })
    with open(root / "corrected_design_points.json", "w", encoding="utf-8") as fh:
        json.dump(dp_rows, fh, indent=2)
    with open(root / "corrected_design_points.csv", "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(list(dp_rows[0].keys()) if dp_rows else [])
        for row in dp_rows:
            wr.writerow([("inf" if v is None and k.startswith("N_req") else v)
                         for k, v in row.items()])

    # Delta vs Baseline §3 (defective-basis side recomputed from the frozen
    # A1 H_full_MM at full precision — never rounded substitution).
    d_lines = ["# R1 delta vs Baseline §3 (defective MM basis → corrected)", "",
               "Defective-basis H_MM values are the full-precision A1 census "
               "values (recompute doc §1); corrected H_corr values are the "
               "R1 TRAIN measurements in this root. Design-point rules are "
               "frozen (packet §2.5): content=1024·H, f(m)=(5m+64)/content, "
               "m_max=⌊(1.3·1024·H−64)/5⌋ capped at 208, "
               "N_req=⌈3·4.785675/(1.3−f)⌉ (inf if f≥1.3).",
               "Statistical INDETERMINATE status is a main-thread judgment; "
               "the movement rows below are arithmetic only.", ""]
    for r in records:
        did = r["dataset_id"]
        d_lines.append(f"## {did} (status={r.get('status')})")
        d_lines.append(f"- Baseline verdict (frozen reference): {BASELINE_VERDICT[did]}")
        a1h = (a1_rows or {}).get(did, {}).get("H_full_MM") \
            if a1_rows else None
        Hc = r.get("H_corr")
        if a1h is None or Hc is None:
            d_lines.append("- delta: unavailable (baseline H or corrected H "
                           "missing for this source)")
            d_lines.append("")
            continue
        base = design_point(float(a1h))
        corr = design_point(float(Hc))
        dH = float(Hc) - float(a1h)
        d_lines.append(f"- H: {a1h!r} → {Hc!r} (ΔH={dH!r})")
        d_lines.append(f"- content: {base['content']!r} → {corr['content']!r} "
                       f"(Δ={corr['content'] - base['content']!r})")
        for m in (208, 200, 199):
            bf, cf = base[f"f_at_{m}"], corr[f"f_at_{m}"]
            bn, cn = base[f"N_req_at_{m}"], corr[f"N_req_at_{m}"]
            bs = "inf" if bn is None else str(bn)
            cs = "inf" if cn is None else str(cn)
            d_lines.append(f"- m={m}: f {bf!r} → {cf!r} "
                           f"(Δf={cf - bf!r}); N_req {bs} → {cs}")
        d_lines.append(f"- m_max: raw {base['m_max_raw']} → {corr['m_max_raw']} "
                       f"(capped {base['m_max_capped']} → {corr['m_max_capped']}); "
                       f"N_req@mmax {base['N_req_at_mmax']} → {corr['N_req_at_mmax']}")
        for m in (208, 200):
            cf = corr[f"f_at_{m}"]
            mech = "OUT" if cf >= 1.3 else "IN-on-count"
            d_lines.append(f"- mechanical @{m}: f={cf!r} ⇒ {mech} "
                           f"(vs baseline {BASELINE_VERDICT[did]})")
        d_lines.append("")
    (root / "delta_vs_baseline_S3.md").write_text("\n".join(d_lines) + "\n", encoding="utf-8")

    # R1_RESULT.md — the result record shell (numbers filled from records).
    findings = [r for r in records
                if isinstance(r.get("consistency_2m"), dict)
                and r["consistency_2m"].get("finding") is True]
    res = ["# R1 Histogram Re-run — RESULT (G-R1)", "",
           "Frozen contract: `R1_HISTOGRAM_RERUN_PACKET.md` (§§1–8). "
           "Corrected per-source design points + materialized channel-bundle "
           "inputs ONLY — no FER/SKR/route/qualification/publication claim "
           "(packet §6). Corrected points do NOT authorize X1 by themselves.",
           "",
           "## Per-source estimator rows (TRAIN side)",
           "",
           "| id | N_train | K_AB | K_B | H_plug | H_corr | H_MM_old | Δ | "
           "CI_lo | CI_hi | CI_hw | status |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        res.append(
            f"| {r['dataset_id']} | {r.get('N_train')} | {r.get('K_AB_train')} | "
            f"{r.get('K_B_train')} | {r.get('H_full_plug')} | {r.get('H_corr')} | "
            f"{r.get('H_MM_old')} | {r.get('Delta_MM')} | "
            f"{r.get('bootstrap_CI_lo')} | {r.get('bootstrap_CI_hi')} | "
            f"{r.get('bootstrap_CI_halfwidth')} | {r.get('status')} |")
    res += ["",
            "Bootstrap: frame-level resamples of the CORRECTED statistic "
            "(per-replicate H_plug + own (K_AB−K_B)/(2N ln2)), frozen seed "
            "20260921, ≥200 resamples — REQUIRED, no waiver path. "
            "Every design-point row above carries its CI.",
            "",
            "## Gates",
            "",
            "| id | align | span | atomicity | K_B | determinism | status |",
            "|---|---|---|---|---|---|---|"]
    for r in records:
        det = (r.get("determinism_vs_a1") or {}).get("pass")
        atomic = (trio_complete(trio_paths(root, r["dataset_id"]))
                  if r.get("status") == "OK"
                  else (not (root / f"{r['dataset_id']}_N_ab_train_sparse.npz").exists()
                        and not (root / f"{r['dataset_id']}_p_b_train.npy").exists()))
        res.append(
            f"| {r['dataset_id']} | {r.get('align_status')} | "
            f"{r.get('span_gate_pass')} | {atomic} | {r.get('k_b_gate_pass')} | "
            f"{det} | {r.get('status')} |")
    res += ["",
            "## 2M consistency (§2.7, report-only)"]
    r2 = next((r for r in records if r["dataset_id"] == "T2-2M"), None)
    c2 = (r2 or {}).get("consistency_2m")
    if not isinstance(c2, dict) or not c2.get("ran"):
        res.append("- 2M reporter: NOT RUN "
                   f"({(c2 or {}).get('reason', 'T2-2M not completed')})")
    else:
        res += [
            f"- ΔN_train (R1 vs frozen 559872): {c2['delta_N_train_vs_frozen']} "
            f"(EXPECTED vintage delta — never a finding by itself)",
            f"- ΔH_L1={c2['delta_H_L1']!r} ΔH_L2={c2['delta_H_L2']!r}; "
            f"p_b max-abs-diff={c2['p_b_max_abs_diff']!r}",
            f"- materiality: {c2['materiality_bar']} ⇒ "
            f"{'FINDING ESCALATED' if c2['finding'] else 'no finding'}"]
    if findings:
        res += ["", "## FINDINGS (require main-thread adjudication)",
                *[f"- {r['dataset_id']}: 2M material discrepancy — "
                  f"{r['consistency_2m']}" for r in findings]]
    res += ["",
            "## Budget / telemetry",
            "",
            f"- trio wall: {trio_wall_s:.1f} s (ceiling {budget_s:.0f} s); "
            f"peak RSS: {peak_rss_kb} KiB ({peak_rss_kb / 1024 ** 2:.2f} GiB)",
            "- decoder/DE/graph calls: 0",
            ""]
    (root / "R1_RESULT.md").write_text("\n".join(res) + "\n", encoding="utf-8")

    telemetry = {
        "trio_wall_s": trio_wall_s,
        "peak_rss_kb": peak_rss_kb,
        "peak_rss_gib": peak_rss_kb / 1024 ** 2,
        "budget_s": budget_s,
        "per_dataset_wall_s": {r["dataset_id"]: r.get("dataset_wall_s")
                               for r in records},
        "per_dataset_status": {r["dataset_id"]: r.get("status")
                               for r in records},
    }
    with open(root / "telemetry.json", "w", encoding="utf-8") as fh:
        json.dump(telemetry, fh, indent=2)


def load_a1_reference(a1_root: str) -> tuple[dict[str, Any] | None,
                                            dict[str, Any] | None, str | None]:
    """Load the read-only A1 determinism reference (gate (f) input)."""
    try:
        with open(Path(a1_root) / "census_table.json", encoding="utf-8") as fh:
            rows = {r["dataset_id"]: r for r in json.load(fh)}
        with open(Path(a1_root) / "split_manifest.json", encoding="utf-8") as fh:
            splits = json.load(fh)
        return rows, splits, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser(description="R1 histogram re-run (G-R1).")
    ap.add_argument("--bases", required=True,
                    help="semicolon-separated base X.ttbin paths, exactly 3 (trio order)")
    ap.add_argument("--datasets", default=";".join(DATASET_IDS),
                    help="semicolon-separated dataset ids (must be exactly the trio)")
    ap.add_argument("--root", required=True, help="fresh additive output root")
    ap.add_argument("--per-read-timeout-s", type=float, default=PER_READ_TIMEOUT_S)
    ap.add_argument("--budget-s", type=float, default=BUDGET_TRIO_S)
    ap.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED_FROZEN)
    ap.add_argument("--bootstrap-resamples", type=int, default=BOOTSTRAP_MIN_RESAMPLES)
    ap.add_argument("--span-tol-s", type=float, default=SPAN_TOL_S_DEFAULT,
                    help="span-continuity |span-mtime_gap| tolerance in s")
    ap.add_argument("--a1-root", default=A1_ROOT_DEFAULT,
                    help="read-only A1 census root for determinism gate (f)")
    ap.add_argument("--gamma", default=GAMMA_DEFAULT,
                    help="read-only frozen bundle lineage for the 2M reporter")
    args = ap.parse_args()

    if args.per_read_timeout_s <= 0:
        raise SystemExit("--per-read-timeout-s must be > 0")
    if args.budget_s <= 0:
        raise SystemExit("--budget-s must be > 0")
    if args.span_tol_s <= 0:
        raise SystemExit("--span-tol-s must be > 0")
    if args.bootstrap_seed != BOOTSTRAP_SEED_FROZEN:
        raise SystemExit(f"--bootstrap-seed is frozen to {BOOTSTRAP_SEED_FROZEN}")
    if args.bootstrap_resamples < BOOTSTRAP_MIN_RESAMPLES:
        raise SystemExit("--bootstrap-resamples must be >= 200 (frozen minimum)")
    bases = parse_bases(args.bases)
    ids = parse_datasets(args.datasets)
    if ids != list(DATASET_IDS):
        raise SystemExit(f"trio order is frozen to 1M → 1.5M → 2M, got: {ids}")
    root = Path(args.root)
    if root.exists():
        raise SystemExit(f"output root already exists (refusing to overwrite): {root}")
    root.mkdir(parents=True, exist_ok=False)

    install_timetagger_alias()
    import TimeTagger  # noqa: F401,E402  (resolves via alias; proves availability)

    a1_rows, a1_splits, a1_err = load_a1_reference(args.a1_root)
    if a1_err is not None:
        print(f"gate-(f) reference unavailable ({args.a1_root}: {a1_err}); "
              f"all datasets will STOP-BLOCKED (fail closed).", flush=True)

    wall0 = time.monotonic()
    global_deadline = wall0 + float(args.budget_s)
    records: list[dict[str, Any]] = []
    splits: dict[str, Any] = {}
    for did, base in zip(ids, bases, strict=True):
        if time.monotonic() > global_deadline:
            records.append({"dataset_id": did, "family": "R1", "ttbin_path": base,
                            "status": "INCOMPLETE", "block_reason": "global budget exhausted",
                            "filename_duration_tag": FILENAME_DURATION_TAG})
            continue
        rec = run_dataset(did, base, root,
                          per_read_timeout_s=args.per_read_timeout_s,
                          global_deadline=global_deadline,
                          bootstrap_seed=args.bootstrap_seed,
                          bootstrap_resamples=args.bootstrap_resamples,
                          span_tol_s=args.span_tol_s,
                          splits_so_far=splits,
                          a1_rows=a1_rows, a1_splits=a1_splits,
                          gamma_path=args.gamma)
        records.append(rec)
        print(f"{did}: status={rec['status']} align={rec.get('align_status')} "
              f"offset={rec.get('offset_ps_derived')} K_B={rec.get('K_B_train')} "
              f"H_corr={rec.get('H_corr')} wall={rec.get('dataset_wall_s')}", flush=True)
        if rec.get("status") == "INCOMPLETE":
            print("wall hit: STOPPING batch, retaining everything (never continued).", flush=True)
            break
    write_shared_tables(records, root, a1_rows=a1_rows,
                        trio_wall_s=time.monotonic() - wall0,
                        peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                        budget_s=float(args.budget_s))
    wall_dt = time.monotonic() - wall0
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"done: n={len(records)} wall_s={wall_dt:.1f} peak_rss_kb={peak_kb}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
