"""Additive correlation-alignment wrapper for the P3 A1 census arm (G-P3).

DECIDE track. Implements ONLY the frozen packet §3A procedure as an additive
module — ``src/`` stays frozen (``git diff -- src/`` must remain empty).

Frozen procedure (packet §3A.2, quote-level):
    corr = compute_cross_correlation_histogram(events, ch_a, ch_b,
             bin_width_ps=100, max_lag_ps=819200)  # 16384 bins
    pk   = int(argmax(counts))
    offset_ps = +lag_center_ps[pk]
Sign: ``_pair_nearest_unique`` ADDS the offset to side A
(``src/qkd_io/ttbin_pipeline.py:219-249``); lag convention ``t_B - t_A``.
No interpolation; bin centre only; once per dataset on the vendor-auto-followed
merged stream (base member only).

Pre-registered heuristics (marked [HEURISTIC] in outputs): 300k-subsample
provenance note (primary here is the FULL windowed histogram), median
background excluding ±2 bins around the peak, crude ±12-bin bg-subtracted
weighted std for sigma.

Frozen acceptance gates (§3A.4, ALL must pass else STOP-BLOCKED):
  (i)   non-empty both channels, non-empty histogram after range filter;
  (ii)  peak_to_bg >= 100;
  (iii) single dominant mode [HEURISTIC frozen rule]: no secondary local
        maximum above 50% of the primary peak height outside ±1000 ps of pk;
  (iv)  crude sigma within 10–500 ps.
On ANY failure: STOP-BLOCKED for that dataset — NEVER fall back to 0, to a
borrowed offset, or to the recorded -50/+50 value; NEVER widen bins post-hoc.

House style follows ``comparison_bench/.../io/ttbin_compat.py`` (plain
functions, no defensive machinery beyond what the gates need — AGENTS.md §5.7).
"""

from __future__ import annotations

from typing import Any

import numpy as np

# Frozen ports (§3A.2 / capability audit D2).
ALIGN_BIN_WIDTH_PS = 100
ALIGN_MAX_LAG_PS = 819200

# Frozen acceptance bars (§3A.4 / D5).
PEAK_TO_BG_MIN = 100.0
SIGMA_MIN_PS = 10.0
SIGMA_MAX_PS = 500.0
SECONDARY_FRAC = 0.5
SECONDARY_EXCLUSION_PS = 1000.0

# Frozen heuristic radii (capability audit B1 items 5 / D8).
BG_EXCL_BINS = 2
SIGMA_HALF_BINS = 12


def _local_maxima(counts: np.ndarray) -> np.ndarray:
    """Indices of strict local maxima (interior bins only). [HEURISTIC]"""
    c = np.asarray(counts)
    if c.size < 3:
        return np.empty((0,), dtype=np.int64)
    mid = np.arange(1, c.size - 1, dtype=np.int64)
    mask = (c[1:-1] > c[:-2]) & (c[1:-1] > c[2:])
    return mid[mask]


def derive_alignment_from_histogram(
    *,
    counts: np.ndarray,
    lag_center_ps: np.ndarray,
    count_a: int,
    count_b: int,
    bin_width_ps: int = ALIGN_BIN_WIDTH_PS,
) -> dict[str, Any]:
    """Pure argmax + acceptance-gate step. No reader, no data access.

    Returns a diagnostics dict with ``align_status`` == ``"ok"`` iff ALL
    frozen gates pass, else ``"blocked_<reason>"``. The caller must NEVER
    adopt ``offset_ps_derived`` unless ``align_status == "ok"`` (enforced
    separately by ``require_alignment_passed``).
    """
    counts = np.asarray(counts, dtype=np.int64)
    centers = np.asarray(lag_center_ps, dtype=np.float64)
    rec: dict[str, Any] = {
        "peak_bin_index": None,
        "peak_center_ps": None,
        "offset_ps_derived": None,
        "peak_to_bg": None,
        "sigma_crude_ps": None,
        "align_status": "blocked_empty_input",
        "single_mode_ok": False,
        "n_local_maxima": 0,
    }
    if int(count_a) <= 0 or int(count_b) <= 0:
        return rec
    if counts.size == 0 or int(np.sum(counts)) <= 0:
        rec["align_status"] = "blocked_empty_histogram"
        return rec

    pk = int(np.argmax(counts))
    peak = float(counts[pk])
    peak_center = float(centers[pk])
    rec["peak_bin_index"] = pk
    rec["peak_center_ps"] = peak_center
    # Sign: offset is ADDED to side A; lag convention t_B - t_A ⇒ offset = +peak.
    rec["offset_ps_derived"] = int(round(peak_center))

    # Background: median excluding ±BG_EXCL_BINS around pk. [HEURISTIC]
    lo = max(0, pk - BG_EXCL_BINS)
    hi = min(counts.size, pk + BG_EXCL_BINS + 1)
    mask = np.ones(counts.size, dtype=bool)
    mask[lo:hi] = False
    rest = counts[mask]
    bg = float(np.median(rest)) if rest.size else 0.0
    peak_to_bg = float(peak / bg) if bg > 0 else float("inf")
    rec["peak_to_bg"] = peak_to_bg

    # Crude local sigma: bg-subtracted weighted std over ±SIGMA_HALF_BINS. [HEURISTIC]
    slo = max(0, pk - SIGMA_HALF_BINS)
    shi = min(counts.size, pk + SIGMA_HALF_BINS + 1)
    w = counts[slo:shi].astype(np.float64) - bg
    w = np.clip(w, 0.0, None)
    wsum = float(np.sum(w))
    if wsum <= 0:
        rec["align_status"] = "blocked_sigma_undefined"
        return rec
    dc = centers[slo:shi] - peak_center
    sigma = float(np.sqrt(np.sum(w * dc * dc) / wsum))
    rec["sigma_crude_ps"] = sigma

    # Single dominant mode: no secondary strict local maximum above
    # SECONDARY_FRAC of peak outside ±SECONDARY_EXCLUSION_PS. [HEURISTIC rule]
    maxima = _local_maxima(counts)
    rec["n_local_maxima"] = int(maxima.size)
    far = maxima[np.abs(centers[maxima] - peak_center) > SECONDARY_EXCLUSION_PS]
    secondaries = far[counts[far] > SECONDARY_FRAC * peak]
    rec["single_mode_ok"] = bool(secondaries.size == 0)
    rec["n_secondary_violations"] = int(secondaries.size)

    if peak_to_bg < PEAK_TO_BG_MIN:
        rec["align_status"] = "blocked_low_peak_to_bg"
    elif not rec["single_mode_ok"]:
        rec["align_status"] = "blocked_multi_mode"
    elif not (SIGMA_MIN_PS <= sigma <= SIGMA_MAX_PS):
        rec["align_status"] = "blocked_sigma_range"
    else:
        rec["align_status"] = "ok"
    return rec


def derive_alignment(
    *,
    events: Any,
    ch_a: int,
    ch_b: int,
    bin_width_ps: int = ALIGN_BIN_WIDTH_PS,
    max_lag_ps: int = ALIGN_MAX_LAG_PS,
) -> dict[str, Any]:
    """Frozen §3A.2 call: full windowed histogram + argmax + gates.

    ``events`` is a frozen ``TTBinEvents`` (caller reads via frozen
    ``read_ttbin_events`` on the base member only). The histogram call below
    is the frozen ``compute_cross_correlation_histogram`` — unmodified.
    """
    from src.qkd_io.ttbin_pipeline import compute_cross_correlation_histogram

    corr = compute_cross_correlation_histogram(
        events=events,
        ch_a=int(ch_a),
        ch_b=int(ch_b),
        bin_width_ps=int(bin_width_ps),
        max_lag_ps=int(max_lag_ps),
    )
    rec = derive_alignment_from_histogram(
        counts=np.asarray(corr["counts"]),
        lag_center_ps=np.asarray(corr["lag_center_ps"]),
        count_a=int(corr["summary"]["count_A"]),
        count_b=int(corr["summary"]["count_B"]),
        bin_width_ps=int(bin_width_ps),
    )
    rec["bin_width_ps"] = int(bin_width_ps)
    rec["max_lag_ps"] = int(max_lag_ps)
    rec["n_bins"] = int(np.asarray(corr["counts"]).size)
    rec["count_A"] = int(corr["summary"]["count_A"])
    rec["count_B"] = int(corr["summary"]["count_B"])
    rec["total_pairs_in_window"] = int(corr["summary"]["total_pairs_in_window"])
    return rec


def offsets_agree_one_bin(
    *,
    derived_offset_ps: int,
    derived_bin: int,
    prior_offset_ps: int,
    prior_bin: int,
    bin_width_ps: int = ALIGN_BIN_WIDTH_PS,
) -> dict[str, Any]:
    """A1 estimator-calibration check: agreement within ONE bin (100 ps).

    Agreement ⇒ estimator calibration supported. Disagreement beyond one bin
    ⇒ FINDING, not failure: report, adjust nothing.
    """
    ps_ok = abs(int(derived_offset_ps) - int(prior_offset_ps)) <= int(bin_width_ps)
    bin_ok = abs(int(derived_bin) - int(prior_bin)) <= 1
    return {
        "agree_ps": bool(ps_ok),
        "agree_bin": bool(bin_ok),
        "agree_one_bin": bool(ps_ok and bin_ok),
        "delta_ps": int(derived_offset_ps) - int(prior_offset_ps),
        "delta_bin": int(derived_bin) - int(prior_bin),
    }


def require_alignment_passed(align_rec: dict[str, Any]) -> int:
    """Gate: pairing/histogram/entropy may run ONLY after alignment passed.

    Returns the adopted derived offset. Raises ``RuntimeError`` otherwise —
    this is the mechanical prohibition against running pairing or entropy
    with a frozen/default offset when alignment has not passed acceptance.
    """
    if not isinstance(align_rec, dict) or align_rec.get("align_status") != "ok":
        raise RuntimeError(
            "STOP-BLOCKED: alignment has not passed acceptance; "
            "pairing/histogram/entropy must not run (no fallback permitted)."
        )
    off = align_rec.get("offset_ps_derived")
    if off is None:
        raise RuntimeError("STOP-BLOCKED: alignment ok but no derived offset recorded.")
    return int(off)
