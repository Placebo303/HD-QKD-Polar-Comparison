"""Fake-only tests for the P3 A1 alignment wrapper + estimator identity.

FAKE-ONLY: every histogram/events object here is synthetic and in-test. The
real ``read_ttbin_events``/``compute_cross_correlation_histogram`` on real
data are never touched (AGENTS.md §10.1 clause 8). Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import math
import subprocess

import numpy as np

from comparison_bench.src.comparison_bench.io import align_wrapper as w


def _fake_corr(n_bins=64, bw=100.0, peak_bin=32, peak=10000.0, bg=10.0, sigma_bins=1.0):
    """Synthetic Gaussian-ish peak on flat background. FAKE ONLY."""
    centers = (np.arange(n_bins, dtype=np.float64) - n_bins // 2) * bw + bw / 2.0
    idx = np.arange(n_bins, dtype=np.float64)
    counts = bg + (peak - bg) * np.exp(-0.5 * ((idx - peak_bin) / sigma_bins) ** 2)
    return np.floor(counts).astype(np.int64), centers


def test_argmax_index_to_centre_and_sign():
    counts, centers = _fake_corr(n_bins=64, peak_bin=40)
    rec = w.derive_alignment_from_histogram(
        counts=counts, lag_center_ps=centers, count_a=1000, count_b=1000)
    assert rec["peak_bin_index"] == 40
    assert rec["peak_center_ps"] == float(centers[40])
    # Sign: offset ADDED to side A; lag convention t_B - t_A ⇒ offset = +centre.
    assert rec["offset_ps_derived"] == int(round(float(centers[40])))
    assert rec["align_status"] == "ok"


def test_negative_peak_sign():
    # Trio 1M shape: peak centre -50 ps ⇒ derived offset must be -50 (not +50).
    n = 16384
    edges = -819200 + np.arange(n + 1, dtype=np.int64) * 100
    centers = (edges[:-1].astype(np.float64) + edges[1:].astype(np.float64)) / 2.0
    counts = np.full((n,), 5, dtype=np.int64)
    idx = np.arange(n, dtype=np.float64)
    bump = 20000.0 * np.exp(-0.5 * ((idx - 8191) / 1.0) ** 2)
    counts = np.floor(counts + bump).astype(np.int64)  # physical-width peak at bin 8191
    assert counts[8191] == int(counts.max())
    assert centers[8191] == -50.0
    rec = w.derive_alignment_from_histogram(
        counts=counts, lag_center_ps=centers, count_a=500, count_b=500)
    assert rec["peak_bin_index"] == 8191
    assert rec["offset_ps_derived"] == -50
    assert rec["align_status"] == "ok"


def test_one_bin_a1_comparison_agree_and_finding():
    agree = w.offsets_agree_one_bin(derived_offset_ps=-50, derived_bin=8191,
                                    prior_offset_ps=-50, prior_bin=8191)
    assert agree["agree_one_bin"] is True
    flip = w.offsets_agree_one_bin(derived_offset_ps=50, derived_bin=8192,
                                   prior_offset_ps=-50, prior_bin=8191)
    # ±1-bin flip is physically ~0 but still within one bin ⇒ agree.
    assert flip["agree_one_bin"] is True
    finding = w.offsets_agree_one_bin(derived_offset_ps=250, derived_bin=8194,
                                      prior_offset_ps=-50, prior_bin=8191)
    # Disagreement beyond one bin ⇒ FINDING flag, reported — not an exception.
    assert finding["agree_one_bin"] is False
    assert finding["delta_ps"] == 300 and finding["delta_bin"] == 3


def test_gate_low_peak_to_bg_blocks():
    counts, centers = _fake_corr(peak=150.0, bg=10.0)  # p2bg ~15 < 100
    rec = w.derive_alignment_from_histogram(
        counts=counts, lag_center_ps=centers, count_a=500, count_b=500)
    assert rec["peak_to_bg"] < 100.0
    assert rec["align_status"] == "blocked_low_peak_to_bg"


def test_gate_multi_mode_blocks():
    counts, centers = _fake_corr(n_bins=256, peak_bin=64, peak=20000.0, bg=5.0)
    counts[200] = 15000  # secondary >50% of primary, far outside ±1000 ps
    rec = w.derive_alignment_from_histogram(
        counts=counts, lag_center_ps=centers, count_a=500, count_b=500)
    assert rec["single_mode_ok"] is False
    assert rec["align_status"] == "blocked_multi_mode"


def test_gate_sigma_range_blocks_both_sides():
    # Too narrow: single-bin spike ⇒ sigma < 10 ps.
    counts = np.full((256,), 5, dtype=np.int64)
    counts[128] = 50000
    centers = (np.arange(256, dtype=np.float64) - 128) * 100.0 + 50.0
    rec = w.derive_alignment_from_histogram(
        counts=counts, lag_center_ps=centers, count_a=500, count_b=500)
    assert rec["align_status"] == "blocked_sigma_range"
    # Too wide: flat plateau ⇒ sigma > 500 ps.
    wide = np.full((256,), 8000, dtype=np.int64)
    wide[:100] = 5
    wide[200:] = 5
    rec2 = w.derive_alignment_from_histogram(
        counts=wide, lag_center_ps=centers, count_a=500, count_b=500)
    assert rec2["align_status"] in ("blocked_sigma_range", "blocked_multi_mode")


def test_empty_inputs_block():
    c = np.zeros((32,), dtype=np.int64)
    centers = np.arange(32, dtype=np.float64) * 100.0
    assert w.derive_alignment_from_histogram(
        counts=c, lag_center_ps=centers, count_a=0, count_b=5)["align_status"] == "blocked_empty_input"
    assert w.derive_alignment_from_histogram(
        counts=c, lag_center_ps=centers, count_a=5, count_b=5)["align_status"] == "blocked_empty_histogram"


def test_stop_blocked_no_fallback():
    blocked = {"align_status": "blocked_low_peak_to_bg", "offset_ps_derived": -50}
    try:
        w.require_alignment_passed(blocked)
    except RuntimeError:
        pass
    else:
        raise AssertionError("blocked alignment must raise; no fallback permitted")
    try:
        w.require_alignment_passed({"align_status": "ok"})  # ok but no offset
    except RuntimeError:
        pass
    else:
        raise AssertionError("ok without offset must raise")
    assert w.require_alignment_passed({"align_status": "ok", "offset_ps_derived": 50}) == 50


def test_pairing_entropy_gated_before_alignment():
    # Pairing/entropy entry must call the gate first: anything but ok raises.
    for bad in ({}, {"align_status": None}, {"align_status": "blocked_multi_mode",
                                             "offset_ps_derived": 0}):
        try:
            w.require_alignment_passed(bad)
        except RuntimeError:
            continue
        raise AssertionError(f"gate must refuse {bad!r}")


def test_f03_estimator_identity_against_brute_force():
    """Frozen estimator H_full = H_L1 + H_L2 (F03, u1=a>>5, u2=a&31), plug-in."""
    rng = np.random.default_rng(7)
    a = rng.integers(0, 1024, size=20000)
    b = rng.integers(0, 1024, size=20000)
    N = np.bincount(a * 1024 + b, minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
    tot = N.sum()
    p_b = N.sum(axis=0) / tot
    P_agb = np.divide(N, N.sum(axis=0, keepdims=True),
                      out=np.zeros_like(N), where=N.sum(axis=0, keepdims=True) > 0)
    u1 = np.arange(1024) >> 5
    u2 = np.arange(1024) & 31
    H1 = 0.0
    for bb in range(1024):
        if p_b[bb] <= 0:
            continue
        pu1 = np.bincount(u1, weights=P_agb[:, bb], minlength=32)
        pu1 = pu1[pu1 > 0]
        H1 += p_b[bb] * float(-np.sum(pu1 * np.log2(pu1)))
    H2 = 0.0
    for bb in range(1024):
        if p_b[bb] <= 0:
            continue
        for uu in range(32):
            sel = u1 == uu
            pbu = P_agb[sel, bb].sum() * p_b[bb]
            if pbu <= 0:
                continue
            row = P_agb[sel, bb] / P_agb[sel, bb].sum()
            pu2 = np.bincount(u2[sel], weights=row, minlength=32)
            pu2 = pu2[pu2 > 0]
            H2 += pbu * float(-np.sum(pu2 * np.log2(pu2)))
    # Independent brute-force via joint (b,u1,u2) counts.
    joint = np.zeros((1024, 32, 32))
    np.add.at(joint, (b, u1[a], u2[a]), 1)
    Hb = joint.sum(axis=(1, 2))
    e1 = 0.0
    for bb in range(1024):
        if Hb[bb] <= 0:
            continue
        p = joint[bb].sum(axis=1) / Hb[bb]
        p = p[p > 0]
        e1 += (Hb[bb] / tot) * float(-np.sum(p * np.log2(p)))
    e2 = 0.0
    for bb in range(1024):
        for uu in range(32):
            n = joint[bb, uu].sum()
            if n <= 0:
                continue
            p = joint[bb, uu] / n
            p = p[p > 0]
            e2 += (n / tot) * float(-np.sum(p * np.log2(p)))
    assert H1 == e1 and H2 == e2  # exact same arithmetic, two independent codings
    assert 0.0 < H1 + H2 <= 10.0
    # Miller-Madow frozen formula.
    K = int(np.count_nonzero(N))
    Ntot = int(tot)
    mm = (K - 1) / (2 * Ntot * math.log(2))
    assert mm > 0 and math.isfinite(mm)


def test_src_frozen():
    out = subprocess.run(["git", "diff", "--name-only", "--", "src/"],
                         capture_output=True, text=True, cwd="/mnt/d/Code/HD-QKD_Polar_Comparison")
    assert out.returncode == 0
    assert out.stdout.strip() == "", f"src/ must stay frozen, got: {out.stdout.strip()}"
