"""D7-G code-factor extrinsic contract certification tests.

Tiny in-memory synthetic fixtures only. No Model-F, CAL/VAL, real/raw,
formal roots, VOID contents, --phase, R1d, G1, or G2. No D7-G/H production
or scientific execution beyond explicit tiny synthetic decoder unit calls.
No multi-round alternating execution anywhere in this file.

Frozen contract: ``openspec/changes/v72p2d7-code-factor-extrinsic-contract/``
(proposal/design/tasks/spec) and
``docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/D7_G_PREREG_R1.md``.
Formula ``L_code_ext = L_post - log(p_in)``, stored row-normalized by
subtracting log-sum-exp. Tolerances: max-abs 1e-10 (D7-A/BP precedent).
Frozen seeds: 2026091401 (check priors), 2026091402 (tree priors),
2026091403 (loopy priors), 2026091404 (two-layer channel).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v35_algorithm_development as v35,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v72p2d7_gf32_extrinsic_oracle as ext_oracle,
)
from comparison_bench.src.comparison_bench.formal_ir.v72p2d7_gf32_decoder_certification import (
    row_layered_reference,
)

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir"
METHODS = ROOT / "comparison_bench" / "src" / "comparison_bench" / "methods"
SCRIPTS = ROOT / "scripts"

TOL = 1e-10
SEED_CHECK = 2026091401
SEED_TREE = 2026091402
SEED_LOOPY = 2026091403
SEED_CHANNEL = 2026091404
Q = 32

OLD_FIELDS = ("x_hat", "syndrome_ok", "iterations", "runtime_s", "status",
              "final_beliefs")
NEW_FIELDS = ("extrinsic_log_beliefs", "extrinsic_provenance")

# Negative-control / double-count gap floors (observed values carry >=6x
# margin; fixtures are seed-frozen and deterministic).
GAP_DIRECTION = 1e-2      # observed 0.897
GAP_TRANSFER = 1e-3       # observed forward 0.066, backward >= 0.006
GAP_FEEDBACK_MSG = 1e-2   # observed >= 0.36
GAP_BACK_POSTERIOR = 1e-3  # observed ~0.019 (asserted in-run)


def _peaked_prior(peaks, mass=0.9):
    if np.isscalar(mass):
        masses = [float(mass)] * len(peaks)
    else:
        masses = [float(m) for m in mass]
    rows = []
    for k, ms in zip(peaks, masses):
        row = np.full(Q, (1.0 - ms) / (Q - 1))
        row[k] = ms
        rows.append(row / row.sum())
    return np.array(rows)


def _ordinary_prior(n, offset=0):
    base = 1.0 + (np.arange(Q) + offset) % 7
    row = base / base.sum()
    return np.tile(row, (n, 1))


def _softmax_rows(z):
    m = np.max(z, axis=1, keepdims=True)
    e = np.exp(z - m)
    return e / e.sum(axis=1, keepdims=True)


def _clean(priors):
    c = np.maximum(np.asarray(priors, dtype=np.float64), 1e-15)
    return c / c.sum(axis=1, keepdims=True)


# Tiny single-check fixtures (in-memory only).
_TINY_H = np.array([[1, 1]], dtype=np.uint8)
IT0_PRIOR = _peaked_prior([0, 0])
IT0_SYN = np.array([0], dtype=np.uint8)
SWEEP_PRIOR = _peaked_prior([0, 24])
SWEEP_SYN = np.array([1], dtype=np.uint8)


# ---------------------------------------------------------------------------
# EXT-05a: tokens, fields, positional compatibility, flooding DEFERRED
# ---------------------------------------------------------------------------
def test_ext_05a_tokens_fields_and_positional_compat():
    assert v35.EXTRINSIC_NO_CHECK_EVIDENCE == "NO_CHECK_EVIDENCE"
    assert v35.EXTRINSIC_CHECK_EXTRINSIC == "CHECK_EXTRINSIC"
    assert v35.EXTRINSIC_WARM_START_UNSPECIFIED == "WARM_START_UNSPECIFIED"
    assert tuple(v35.EXTRINSIC_PROVENANCE_TOKENS) == (
        "NO_CHECK_EVIDENCE", "CHECK_EXTRINSIC", "WARM_START_UNSPECIFIED")
    # Own namespace: never inferred from belief_provenance or iterations.
    assert "NO_CHECK_EVIDENCE" not in v35.BELIEF_PROVENANCE_TOKENS
    assert "CHECK_EXTRINSIC" not in v35.BELIEF_PROVENANCE_TOKENS
    fields = dataclasses.fields(v35.DecoderResult)
    assert [f.name for f in fields] == list(OLD_FIELDS) + [
        "belief_provenance"] + list(NEW_FIELDS)
    assert fields[-1].default is None and fields[-2].default is None
    legacy6 = v35.DecoderResult(
        np.zeros(2, dtype=np.uint8), True, 0, 0.0, "legacy",
        np.zeros((2, 32)))
    assert legacy6.belief_provenance is None
    assert legacy6.extrinsic_log_beliefs is None
    assert legacy6.extrinsic_provenance is None
    legacy7 = v35.DecoderResult(
        np.zeros(2, dtype=np.uint8), True, 0, 0.0, "legacy",
        np.zeros((2, 32)), "PRIOR_ONLY")
    assert legacy7.belief_provenance == "PRIOR_ONLY"
    assert legacy7.extrinsic_log_beliefs is None
    assert legacy7.extrinsic_provenance is None


def test_ext_05a_flooding_extrinsic_deferred_outputs_unchanged():
    res = v35.decode_flooding_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                     max_iter=1)
    assert res.iterations >= 1
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    # FLOODING_EXTRINSIC_DEFERRED: same additive fields via defaults only.
    assert res.extrinsic_log_beliefs is None
    assert res.extrinsic_provenance is None
    res_max = v35.decode_flooding_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                         max_iter=5)
    assert res_max.extrinsic_log_beliefs is None
    assert res_max.extrinsic_provenance is None


# ---------------------------------------------------------------------------
# EXT-05b: producer paths (cold it0 / cold >=1 / max-iter / nonfinite / warm)
# ---------------------------------------------------------------------------
def test_ext_05b_cold_it0_neutral_ineligible():
    res = v35.decode_row_layered_fftqspa(_TINY_H, IT0_PRIOR, IT0_SYN,
                                        max_iter=5)
    assert res.iterations == 0
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_PRIOR_ONLY
    assert res.extrinsic_provenance == v35.EXTRINSIC_NO_CHECK_EVIDENCE
    assert np.array_equal(np.asarray(res.extrinsic_log_beliefs),
                          np.zeros((2, 32)))
    # Neutral zeros transport to uniform and are ineligible for transfer.
    assert np.array_equal(_softmax_rows(res.extrinsic_log_beliefs),
                          np.full((2, 32), 1.0 / 32))
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(
            res.extrinsic_log_beliefs, res.extrinsic_provenance,
            consumer="test")


def test_ext_05b_cold_sweep_check_extrinsic_and_reconstruction():
    res = v35.decode_row_layered_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                        max_iter=1)
    assert res.iterations == 1
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
    ext = np.asarray(res.extrinsic_log_beliefs, dtype=np.float64)
    assert ext.shape == (2, 32) and bool(np.all(np.isfinite(ext)))
    # Stored rows are exactly log-normalized (log-sum-exp == 0).
    assert float(np.max(np.abs(ext_oracle.normalize_log_rows(ext) - ext))) == 0.0
    # Reconstruction identity: softmax(log(p_in) + L_code_ext) == softmax(L_post).
    log_pin = np.log(_clean(SWEEP_PRIOR))
    got = _softmax_rows(log_pin + ext)
    ref = _softmax_rows(res.final_beliefs)
    assert float(np.max(np.abs(got - ref))) <= TOL


def test_ext_05b_max_iter_path_carries_check_extrinsic():
    peaks = sorted(np.random.default_rng(SEED_LOOPY).integers(0, 32, size=3))
    assert peaks == [12, 29, 30]
    h = np.array([[1, 2, 3], [1, 5, 9]], dtype=np.uint8)
    syn = np.array([7, 13], dtype=np.uint8)
    res = v35.decode_row_layered_fftqspa(h, _peaked_prior(peaks), syn,
                                        max_iter=3)
    assert res.iterations == 3 and res.syndrome_ok is False
    assert res.status == "converged_no_syndrome"
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
    assert bool(np.all(np.isfinite(res.extrinsic_log_beliefs)))


def test_ext_05b_max_iter_zero_cold_has_no_check_evidence():
    h = np.array([[1, 7]], dtype=np.uint8)
    pr = _peaked_prior([3, 20])
    syn = np.array([17], dtype=np.uint8)
    assert not np.array_equal(
        ext_oracle.syndrome_of(h, np.argmax(pr, axis=1)), syn)
    res = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=0)
    assert res.iterations == 0
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_PRIOR_ONLY
    assert res.extrinsic_provenance == v35.EXTRINSIC_NO_CHECK_EVIDENCE
    assert np.array_equal(np.asarray(res.extrinsic_log_beliefs),
                          np.zeros((2, 32)))


def test_ext_05b_nonfinite_fails_loud_never_repaired():
    h = np.array([[1, 7]], dtype=np.uint8)
    syn = np.array([17], dtype=np.uint8)
    bad = np.full((2, 32), np.nan)
    with pytest.raises(ValueError):
        v35.decode_row_layered_fftqspa(h, bad, syn, max_iter=1)
    bad_inf = np.full((2, 32), np.inf)
    with pytest.raises(ValueError):
        v35.decode_row_layered_fftqspa(h, bad_inf, syn, max_iter=1)
    # Builder unit level: None / shape mismatch / nonfinite all fail loud.
    with pytest.raises(ValueError):
        v35._build_check_extrinsic_log_beliefs(None, np.zeros((2, 32)))
    with pytest.raises(ValueError):
        v35._build_check_extrinsic_log_beliefs(
            np.zeros((2, 32)), np.zeros((3, 32)))
    with pytest.raises(ValueError):
        v35._build_check_extrinsic_log_beliefs(
            np.full((2, 32), np.nan), np.zeros((2, 32)))


def test_ext_05b_warm_paths_fail_closed_never_inferred():
    warm = np.log(IT0_PRIOR)
    warm_it0 = v35.decode_row_layered_fftqspa(
        _TINY_H, IT0_PRIOR, IT0_SYN, max_iter=5, warm_beliefs=warm)
    assert warm_it0.iterations == 0
    assert warm_it0.extrinsic_provenance == \
        v35.EXTRINSIC_WARM_START_UNSPECIFIED
    assert warm_it0.extrinsic_log_beliefs is None
    warm_it1 = v35.decode_row_layered_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=1, warm_beliefs=warm)
    assert warm_it1.iterations >= 1
    assert warm_it1.extrinsic_provenance == \
        v35.EXTRINSIC_WARM_START_UNSPECIFIED
    assert warm_it1.extrinsic_log_beliefs is None
    for res in (warm_it0, warm_it1):
        with pytest.raises(v35.UnusableExtrinsicError):
            v35.require_check_extrinsic_for_transfer(
                res.extrinsic_log_beliefs, res.extrinsic_provenance,
                consumer="test")
    # Wrong-shape warm seed is ignored by the decoder (pre-existing rule);
    # extrinsic follows the same cold/warm flag as belief_provenance.
    misshapen = v35.decode_row_layered_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=1,
        warm_beliefs=np.zeros((3, 32)))
    assert misshapen.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    assert misshapen.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC


def test_ext_05b_damped_decoder_inherits_contract():
    res = v35.decode_damped_row_layered_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=1, damping_alpha=0.5)
    assert res.iterations == 1
    assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
    got = _softmax_rows(np.log(_clean(SWEEP_PRIOR)) + res.extrinsic_log_beliefs)
    assert float(np.max(np.abs(got - _softmax_rows(res.final_beliefs)))) <= TOL


# ---------------------------------------------------------------------------
# EXT-01/D01: algebra and invariance
# ---------------------------------------------------------------------------
def test_ext_01_scaling_invariance_of_p_in():
    h = np.array([[1, 7]], dtype=np.uint8)
    syn = np.array([17], dtype=np.uint8)
    # Asymmetric masses: decisive argmax margin (no exact-tie fixture).
    base = _peaked_prior([3, 20], mass=[0.9, 0.6])
    scales = np.array([[0.3], [2.7]])
    res0 = v35.decode_row_layered_fftqspa(h, base, syn, max_iter=1)
    res1 = v35.decode_row_layered_fftqspa(h, base * scales, syn, max_iter=1)
    assert res0.iterations == res1.iterations == 1
    assert np.array_equal(res0.x_hat, res1.x_hat)
    d = float(np.max(np.abs(res0.extrinsic_log_beliefs -
                             res1.extrinsic_log_beliefs)))
    assert d <= 1e-12


def test_ext_01_row_constant_invariance_of_transport():
    res = v35.decode_row_layered_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                        max_iter=1)
    ext = np.asarray(res.extrinsic_log_beliefs)
    shifted = ext + np.array([[5.0], [-3.25]])
    q0 = v35.require_check_extrinsic_for_transfer(
        ext, v35.EXTRINSIC_CHECK_EXTRINSIC, consumer="test")
    q1 = v35.require_check_extrinsic_for_transfer(
        shifted, v35.EXTRINSIC_CHECK_EXTRINSIC, consumer="test")
    assert float(np.max(np.abs(q0 - q1))) <= 1e-12


def test_ext_01_zero_prior_rows_floored_deterministically():
    h = np.array([[1, 7]], dtype=np.uint8)
    syn = np.array([17], dtype=np.uint8)
    pr = _peaked_prior([3, 20])
    pr[0, :] = 0.0  # all-zero row: frozen cleaning floors to uniform
    r1 = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=1)
    r2 = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=1)
    assert np.array_equal(r1.final_beliefs, r2.final_beliefs)
    assert np.array_equal(r1.extrinsic_log_beliefs, r2.extrinsic_log_beliefs)
    assert r1.iterations == 1
    assert r1.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC


# ---------------------------------------------------------------------------
# EXT-02/D02: tree-exact distribution match + negative controls
# ---------------------------------------------------------------------------
def _assert_tree_match(h, priors, syn, coeffs):
    res = v35.decode_row_layered_fftqspa(h, priors, syn, max_iter=1)
    assert res.iterations == 1, (h.tolist(), syn.tolist(), res.iterations)
    assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
    got = _softmax_rows(res.extrinsic_log_beliefs)
    worst = 0.0
    for t in range(h.shape[1]):
        ref = ext_oracle.tree_message_to_var(
            [priors[i] for i in range(h.shape[1])], list(coeffs),
            int(syn[0]), t)
        worst = max(worst, float(np.max(np.abs(got[t] - ref))))
    assert worst <= TOL, (h.tolist(), syn.tolist(), worst)
    return worst


def test_ext_02_deg2_full_multiplier_sweep():
    rng = np.random.default_rng(SEED_CHECK)
    offset = int(rng.integers(0, 32, size=4)[0])
    worst = 0.0
    worst_at = None
    for c in range(1, 32):
        h = np.array([[1, c]], dtype=np.uint8)
        for pname, pr in (("skewed", _peaked_prior([5, 5])),
                          ("ordinary", _ordinary_prior(2, offset=offset))):
            # Frozen rule: first nonzero syndrome of (5, 17, 31) the MAP
            # does not satisfy, so exactly one sweep runs. (Any fixed peak
            # collides for some multiplier since c*p1 permutes GF32*.)
            map_syn = int(ext_oracle.syndrome_of(
                h, np.argmax(pr, axis=1))[0])
            syn = next(s for s in (5, 17, 31) if s != map_syn)
            s = np.array([syn], dtype=np.uint8)
            err = _assert_tree_match(h, pr, s, [1, c])
            if err > worst:
                worst, worst_at = err, (c, syn, pname)
    assert worst <= TOL, (worst, worst_at)


def test_ext_02_deg2_seeded_asymmetric():
    rng = np.random.default_rng(SEED_CHECK)
    pairs = [sorted(rng.integers(0, 32, size=2).tolist()) for _ in range(3)]
    assert pairs == [[11, 28], [22, 27], [0, 7]]
    cases = [([11, 28], (1, 7), 17), ([11, 28], (2, 13), 29),
             ([22, 27], (1, 7), 17), ([22, 27], (1, 2), 17),
             ([0, 7], (1, 2), 5), ([0, 7], (2, 13), 29)]
    for peaks, coeffs, syn in cases:
        h = np.array([list(coeffs)], dtype=np.uint8)
        pr = _peaked_prior(peaks)
        s = np.array([syn], dtype=np.uint8)
        assert not np.array_equal(
            ext_oracle.syndrome_of(h, np.argmax(pr, axis=1)), s), \
            (peaks, coeffs, syn)
        _assert_tree_match(h, pr, s, list(coeffs))


def test_ext_02_deg3_sampled_and_seeded():
    rng = np.random.default_rng(SEED_TREE)
    triples = [sorted(rng.integers(0, 32, size=3).tolist()) for _ in range(3)]
    assert triples == [[1, 11, 29], [21, 21, 24], [0, 17, 22]]
    for coeffs in [(1, 1, 1), (1, 2, 3), (2, 7, 13), (1, 13, 29)]:
        h = np.array([list(coeffs)], dtype=np.uint8)
        for syn in (0, 5, 17, 31):
            s = np.array([syn], dtype=np.uint8)
            pr = _peaked_prior([5, 9, 21], mass=0.85)
            assert not np.array_equal(
                ext_oracle.syndrome_of(h, np.argmax(pr, axis=1)), s), \
                (coeffs, syn)
            _assert_tree_match(h, pr, s, list(coeffs))
    for peaks, coeffs, syn in [([1, 11, 29], (1, 2, 3), 17),
                               ([21, 21, 24], (2, 7, 13), 5),
                               ([0, 17, 22], (1, 2, 3), 17)]:
        h = np.array([list(coeffs)], dtype=np.uint8)
        pr = _peaked_prior(peaks, mass=0.85)
        s = np.array([syn], dtype=np.uint8)
        assert not np.array_equal(
            ext_oracle.syndrome_of(h, np.argmax(pr, axis=1)), s), \
            (peaks, coeffs, syn)
        _assert_tree_match(h, pr, s, list(coeffs))


def test_ext_02_negative_direction_and_label_controls():
    h = np.array([[1, 7]], dtype=np.uint8)
    pr = _peaked_prior([3, 20])
    syn = np.array([17], dtype=np.uint8)
    res = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=1)
    assert res.iterations == 1
    got = _softmax_rows(res.extrinsic_log_beliefs)
    ref0 = ext_oracle.tree_message_to_var([pr[0], pr[1]], [1, 7], 17, 0)
    assert float(np.max(np.abs(got[0] - ref0))) <= TOL
    # Swapped edge direction must mismatch deterministically.
    ref_swap = ext_oracle.tree_message_to_var([pr[0], pr[1]], [1, 7], 17, 1)
    gap_swap = float(np.max(np.abs(got[0] - ref_swap)))
    assert gap_swap >= GAP_DIRECTION, gap_swap
    # Permuted-label oracle must mismatch deterministically.
    shifted = np.roll(pr, 1, axis=1)
    ref_shift = ext_oracle.tree_message_to_var(
        [shifted[0], shifted[1]], [1, 7], 17, 0)
    gap_shift = float(np.max(np.abs(got[0] - ref_shift)))
    assert gap_shift >= GAP_DIRECTION, gap_shift


# ---------------------------------------------------------------------------
# EXT-03/D03: loopy independent-recurrence match after 1-3 sweeps (never MAP)
# ---------------------------------------------------------------------------
def test_ext_03_loopy_recurrence_sweeps_1_to_3():
    peaks = sorted(np.random.default_rng(SEED_LOOPY).integers(0, 32, size=3))
    assert peaks == [12, 29, 30]
    h = np.array([[1, 2, 3], [1, 5, 9]], dtype=np.uint8)
    syn = np.array([7, 13], dtype=np.uint8)
    pr = _peaked_prior(peaks)
    sums = ext_oracle.row_layered_message_sums(h, pr, syn, 3)
    for k in (1, 2, 3):
        res = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=k)
        assert res.iterations == k, (k, res.iterations)
        assert res.syndrome_ok is False  # never converged: not a MAP match
        assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
        got = ext_oracle.normalize_log_rows(res.extrinsic_log_beliefs)
        ref = ext_oracle.normalize_log_rows(sums[k - 1])
        err = float(np.max(np.abs(got - ref)))
        assert err <= TOL, (k, err)


# ---------------------------------------------------------------------------
# EXT-04/D04: two-layer no-returned-evidence demonstration
# ---------------------------------------------------------------------------
def _two_layer_setup():
    rng = np.random.default_rng(SEED_CHANNEL)
    ii = np.arange(Q)

    def spike(peak, mass=0.55):
        v = np.full(Q, (1.0 - mass) / (Q - 1))
        v[peak] = mass
        return v

    u_a1, u_a2, u_b1, u_b2 = spike(7), spike(19), spike(7), spike(19)
    eq1 = (ii[:, None, None, None] == ii[None, None, :, None]).astype(np.float64)
    eq2 = (ii[None, :, None, None] == ii[None, None, None, :]).astype(np.float64)
    base = (u_a1[:, None, None, None] * u_a2[None, :, None, None]
            * u_b1[None, None, :, None] * u_b2[None, None, None, :])
    ch = base * (1.0 + 1.5 * eq1 + 1.5 * eq2) * (
        1.0 + 0.2 * rng.random((Q, Q, Q, Q)))
    ch = ch / ch.sum()
    h1 = np.array([[2, 7]], dtype=np.uint8)
    h2 = np.array([[3, 11]], dtype=np.uint8)
    s1, s2 = np.array([13], dtype=np.uint8), np.array([5], dtype=np.uint8)
    p_a = np.stack([ext_oracle.normalize_dist(np.einsum("ijkl->i", ch)),
                    ext_oracle.normalize_dist(np.einsum("ijkl->j", ch))])
    p_b = np.stack([ext_oracle.normalize_dist(np.einsum("ijkl->k", ch)),
                    ext_oracle.normalize_dist(np.einsum("ijkl->l", ch))])
    return ch, h1, h2, s1, s2, p_a, p_b


def _decode_extrinsic(h, priors, syn):
    res = v35.decode_row_layered_fftqspa(h, priors, syn, max_iter=1)
    assert res.iterations == 1, (h.tolist(), syn.tolist(), res.iterations)
    assert res.extrinsic_provenance == v35.EXTRINSIC_CHECK_EXTRINSIC
    return _softmax_rows(res.extrinsic_log_beliefs), res


def test_ext_04_forward_update_matches_sum_product():
    ch, h1, h2, s1, _s2, p_a, p_b = _two_layer_setup()
    e1, _ = _decode_extrinsic(h1, p_a, s1)
    o1 = [ext_oracle.tree_message_to_var([p_a[0], p_a[1]], [2, 7],
                                         int(s1[0]), t) for t in range(2)]
    for t in range(2):
        assert float(np.max(np.abs(e1[t] - o1[t]))) <= TOL
    # Explicit code-extrinsic forward transfer through the channel factor.
    f_b1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b1(ch, e1[0], e1[1], p_b[1]))
    f_b2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b2(ch, e1[0], e1[1], p_b[0]))
    p2 = np.stack([f_b1, f_b2])
    e2, _ = _decode_extrinsic(h2, p2, _s2)
    o2 = [ext_oracle.tree_message_to_var([p2[0], p2[1]], [3, 11],
                                         int(_s2[0]), t) for t in range(2)]
    for t in range(2):
        assert float(np.max(np.abs(e2[t] - o2[t]))) <= TOL


def test_ext_04_backward_update_matches_sum_product():
    ch, h1, h2, s1, s2, p_a, p_b = _two_layer_setup()
    e1, _ = _decode_extrinsic(h1, p_a, s1)
    f_b1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b1(ch, e1[0], e1[1], p_b[1]))
    f_b2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b2(ch, e1[0], e1[1], p_b[0]))
    e2, _ = _decode_extrinsic(h2, np.stack([f_b1, f_b2]), s2)
    # Cavity backward transfer:POSTERIOR-free layer-2 messages only.
    b_a1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a1(ch, e2[0], e2[1], e1[1]))
    b_a2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a2(ch, e2[0], e2[1], e1[0]))
    p1b = np.stack([b_a1, b_a2])
    e1b, _ = _decode_extrinsic(h1, p1b, s1)
    o1b = [ext_oracle.tree_message_to_var([p1b[0], p1b[1]], [2, 7],
                                          int(s1[0]), t) for t in range(2)]
    for t in range(2):
        assert float(np.max(np.abs(e1b[t] - o1b[t]))) <= TOL


def test_ext_04_posterior_back_transfer_double_counts():
    ch, h1, h2, s1, s2, p_a, p_b = _two_layer_setup()
    e1, _ = _decode_extrinsic(h1, p_a, s1)
    f_b1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b1(ch, e1[0], e1[1], p_b[1]))
    f_b2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b2(ch, e1[0], e1[1], p_b[0]))
    p2 = np.stack([f_b1, f_b2])
    e2, _ = _decode_extrinsic(h2, p2, s2)
    # (1a) Message level: the same syndrome factor returns a different
    # message once fed the posterior it helped create (S1 evidence squared).
    q1 = (ext_oracle.normalize_dist(e1[0] * p_a[0]),
          ext_oracle.normalize_dist(e1[1] * p_a[1]))
    m_orig = ext_oracle.tree_message_to_var([p_a[0], p_a[1]], [2, 7],
                                            int(s1[0]), 0)
    m_fb = ext_oracle.tree_message_to_var([q1[0], q1[1]], [2, 7],
                                          int(s1[0]), 0)
    gap_msg1 = float(np.max(np.abs(m_fb - m_orig)))
    assert gap_msg1 >= GAP_FEEDBACK_MSG, gap_msg1
    q2 = (ext_oracle.normalize_dist(e2[0] * p2[0]),
          ext_oracle.normalize_dist(e2[1] * p2[1]))
    m2_orig = ext_oracle.tree_message_to_var([p2[0], p2[1]], [3, 11],
                                             int(s2[0]), 0)
    m2_fb = ext_oracle.tree_message_to_var([q2[0], q2[1]], [3, 11],
                                           int(s2[0]), 0)
    gap_msg2 = float(np.max(np.abs(m2_fb - m2_orig)))
    assert gap_msg2 >= GAP_FEEDBACK_MSG, gap_msg2
    # (1b) Forward transfer level: posterior carries the originating
    # syndrome evidence back into the next layer's prior.
    g_b1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b1(ch, q1[0], q1[1], p_b[1]))
    gap_fwd = float(np.max(np.abs(g_b1 - f_b1)))
    assert gap_fwd >= GAP_TRANSFER, gap_fwd
    # (1c) Backward transfer level: cavity (extrinsic) vs posterior.
    b_a1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a1(ch, e2[0], e2[1], e1[1]))
    b_a2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a2(ch, e2[0], e2[1], e1[0]))
    p_a1 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a1(ch, q2[0], q2[1], e1[1]))
    p_a2 = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_a2(ch, q2[0], q2[1], e1[0]))
    gap_b1 = float(np.max(np.abs(p_a1 - b_a1)))
    gap_b2 = float(np.max(np.abs(p_a2 - b_a2)))
    assert gap_b1 >= GAP_TRANSFER, gap_b1
    assert gap_b2 >= GAP_TRANSFER, gap_b2
    # (1d) The re-decoded layer-1 posterior differs: double application of
    # the originating syndrome changes the answer, while the cavity path
    # reproduces the independent sum-product messages within TOL.
    p1b = np.stack([b_a1, b_a2])
    e1b, _ = _decode_extrinsic(h1, p1b, s1)
    p1p = np.stack([p_a1, p_a2])
    ep, _ = _decode_extrinsic(h1, p1p, s1)
    qp_cav = ext_oracle.normalize_dist(e1b[0] * p1b[0])
    qp_post = ext_oracle.normalize_dist(ep[0] * p1p[0])
    gap_post = float(np.max(np.abs(qp_cav - qp_post)))
    assert gap_post >= GAP_BACK_POSTERIOR, gap_post


def test_ext_04_it0_neutral_extrinsic_creates_no_lift():
    ch, _h1, _h2, _s1, _s2, _p_a, _p_b = _two_layer_setup()
    h = np.array([[1, 1]], dtype=np.uint8)
    res = v35.decode_row_layered_fftqspa(h, IT0_PRIOR, IT0_SYN, max_iter=5)
    assert res.iterations == 0
    uni = _softmax_rows(res.extrinsic_log_beliefs)[0]
    assert float(np.max(np.abs(uni - np.full(Q, 1.0 / Q)))) <= 1e-12
    # Transferring neutral messages reproduces the channel marginal:
    # no evidence is added, so no false lift is possible.
    base = ext_oracle.normalize_dist(np.einsum("ijkl->k", ch))
    moved = ext_oracle.normalize_dist(
        ext_oracle.transfer_to_b1(ch, uni, uni, uni))
    assert float(np.max(np.abs(moved - base))) <= 1e-12


# ---------------------------------------------------------------------------
# EXT-05c: narrow helper rejection matrix + BP guards unchanged
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("provenance", [
    None, "NO_CHECK_EVIDENCE", "WARM_START_UNSPECIFIED",
    "BOGUS", "bogus", "", 0, "CHECK_UPDATED", "PRIOR_ONLY",
    "check_extrinsic",
])
def test_ext_05c_helper_rejects_unusable_provenance(provenance):
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(
            np.zeros((2, 32)), provenance, consumer="test")


@pytest.mark.parametrize("array", [
    None, np.zeros(32), np.zeros((2, 31)), np.zeros((2, 33)),
    np.zeros((3, 2, 32)), np.full((2, 32), np.nan),
    np.full((2, 32), np.inf), np.zeros((1, 32))[0:0],
])
def test_ext_05c_helper_rejects_bad_arrays(array):
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(
            array, v35.EXTRINSIC_CHECK_EXTRINSIC, consumer="test")


def test_ext_05c_helper_rejects_row_count_mismatch():
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(
            np.zeros((2, 32)), v35.EXTRINSIC_CHECK_EXTRINSIC,
            consumer="test", expected_n=3)


def test_ext_05c_helper_accepts_only_explicit_check_extrinsic():
    res = v35.decode_row_layered_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                        max_iter=1)
    q = v35.require_check_extrinsic_for_transfer(
        res.extrinsic_log_beliefs, res.extrinsic_provenance,
        consumer="test", expected_n=2)
    assert q.shape == (2, 32)
    assert float(np.max(np.abs(q.sum(axis=1) - 1.0))) <= 1e-12
    # Legacy/absent fields (None/None) fail closed.
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(None, None, consumer="test")


def test_ext_05c_bp_provenance_guards_unchanged():
    assert tuple(v35.BELIEF_PROVENANCE_TOKENS) == (
        "PRIOR_ONLY", "CHECK_UPDATED", "WARM_START_UNSPECIFIED")
    assert v35.require_check_updated_provenance("CHECK_UPDATED", consumer="t")
    for bad in (None, "PRIOR_ONLY", "WARM_START_UNSPECIFIED", "BOGUS", "",
                "CHECK_EXTRINSIC", "NO_CHECK_EVIDENCE"):
        with pytest.raises(v35.UnconditionedBeliefProvenanceError):
            v35.require_check_updated_provenance(bad, consumer="t")
    # The extrinsic namespace never satisfies the belief gate and vice versa.
    with pytest.raises(v35.UnusableExtrinsicError):
        v35.require_check_extrinsic_for_transfer(
            np.zeros((2, 32)), "CHECK_UPDATED", consumer="t")


# ---------------------------------------------------------------------------
# EXT-06: compatibility (D7-A reference, adapters, inventory, no-D7-H)
# ---------------------------------------------------------------------------
def test_ext_06_final_beliefs_match_d7a_reference():
    peaks = sorted(np.random.default_rng(SEED_LOOPY).integers(0, 32, size=3))
    h = np.array([[1, 2, 3], [1, 5, 9]], dtype=np.uint8)
    syn = np.array([7, 13], dtype=np.uint8)
    pr = _peaked_prior(peaks)
    sweeps, ref_iters, ref_x = row_layered_reference(h, pr, syn, 3)
    res = v35.decode_row_layered_fftqspa(h, pr, syn, max_iter=3)
    assert (ref_iters, res.iterations) == (3, 3)
    assert np.array_equal(res.x_hat, ref_x)
    from comparison_bench.src.comparison_bench.formal_ir import (
        v72p2d5_gf32_rate_mother as d5,
    )
    for k in range(3):
        got = d5._softmax_rows(res.final_beliefs if k == 2 else
                               v35.decode_row_layered_fftqspa(
                                   h, pr, syn, max_iter=k + 1).final_beliefs)
        ref = d5._softmax_rows(sweeps[k])
        assert float(np.max(np.abs(got - ref))) <= 1e-12


def test_ext_06_consumer_adapters_ignore_new_fields():
    from comparison_bench.src.comparison_bench.formal_ir import (
        v72p2d7_gf32_bidirectional_oracle as d7c,
    )
    res = v35.decode_row_layered_fftqspa(_TINY_H, SWEEP_PRIOR, SWEEP_SYN,
                                        max_iter=1)
    x_hat, reported, it, bel, status = d7c._parse_decoder_result(res)
    assert np.array_equal(x_hat, np.asarray(res.x_hat))
    assert (reported, it, status) == (True, 1, "converged_exact")
    assert np.array_equal(np.asarray(bel), np.asarray(res.final_beliefs))
    # A legacy-shaped twin (no extrinsic fields) standardizes identically.
    legacy = v35.DecoderResult(
        np.asarray(res.x_hat).copy(), bool(res.syndrome_ok),
        int(res.iterations), float(res.runtime_s), str(res.status),
        np.asarray(res.final_beliefs).copy(), res.belief_provenance)
    lx, lr, li, lb, ls = d7c._parse_decoder_result(legacy)
    assert np.array_equal(lx, x_hat) and (lr, li, ls) == (reported, it, status)
    assert np.array_equal(np.asarray(lb), np.asarray(bel))


def test_ext_06_declared_constants():
    assert v35.FIELD_Q == 32
    assert v35.FIELD_POLY == 37 == 0b100101
    assert ext_oracle.Q == 32
    assert ext_oracle.PRIMITIVE_POLY == 0b100101
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
        GF2mField,
    )
    assert GF2mField.create(32).q == 32
    mul_p, _, _ = v35._get_gf32_tables(GF2mField.create(32))
    assert np.array_equal(ext_oracle.MUL, mul_p)


_PRODUCTION_INTERFACE_FILES = [
    FORMAL / "v35_algorithm_development.py",
    FORMAL / "v72p2d5_gf32_rate_mother.py",
    FORMAL / "v72p2d3_gf32_contrast.py",
    FORMAL / "v45_l1_app_soft_transfer.py",
    FORMAL / "v46_verification_semantics.py",
    FORMAL / "v47_h1_redundancy_compression.py",
    FORMAL / "v48_heldout_confirm.py",
    FORMAL / "v50_l2_structure_factorial.py",
    FORMAL / "v51_lane_c_label_nbace.py",
    FORMAL / "v52_rate_adaptive_l2_rescue.py",
    FORMAL / "v53_rate_adaptive_l2_heldout_confirm.py",
    FORMAL / "v54_two_stage_incremental_l2_rescue.py",
    FORMAL / "v55_two_stage_rescue_independent_test.py",
    METHODS / "nbldpc_shell_adapter.py",
    SCRIPTS / "execute_v64_fresh_verify.py",
]


def test_ext_06_oracle_import_graph_independence():
    src = (FORMAL / "v72p2d7_gf32_extrinsic_oracle.py").read_text(
        encoding="utf-8")
    for needle in ("v35_algorithm_development", "_check_update_log_batch",
                   "_get_gf32_tables", "belief_provenance",
                   "require_check_updated_provenance",
                   "require_check_extrinsic", "decode_row_layered",
                   "decode_flooding", "rate_mother", "decoder_certification",
                   "extrinsic_log_beliefs", "UnusableExtrinsicError"):
        assert needle not in src, needle
    assert "import numpy" in src and "import itertools" in src
    # No production module imports the new oracle (test-only dependency).
    for path in _PRODUCTION_INTERFACE_FILES:
        if path.name == "v35_algorithm_development.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "v72p2d7_gf32_extrinsic_oracle" not in text, path.name


def test_ext_06_static_inventory_no_production_extrinsic_consumer():
    for path in _PRODUCTION_INTERFACE_FILES:
        if path.name == "v35_algorithm_development.py":
            continue  # producer + narrow helper live here by frozen file map
        text = path.read_text(encoding="utf-8")
        for needle in ("extrinsic_log_beliefs", "extrinsic_provenance",
                       "EXTRINSIC_CHECK_EXTRINSIC", "EXTRINSIC_NO_CHECK",
                       "require_check_extrinsic", "UnusableExtrinsicError"):
            assert needle not in text, (path.name, needle)


def test_ext_06_no_d7h_no_new_roots_no_forbidden_reads():
    # Producer + oracle carry no D7-H/alternating execution identifiers.
    # (The output-root needle is scanned on the new oracle only: v35 carries
    # a pre-existing V25 provenance path string outside this change's scope.)
    for name, extra in (("v35_algorithm_development.py", ()),
                        ("v72p2d7_gf32_extrinsic_oracle.py",
                         ("outputs_" + "comparison",))):
        text = (FORMAL / name).read_text(encoding="utf-8")
        for needle in ("D7_H_ALTERNATING", "d7_h_", "D7-H", "alternating",
                       "MODEL_" + "F_ROOT", "CAL_" + "ROOT", "VAL_" + "ROOT",
                       "work" + "space/v72p2d") + tuple(extra):
            assert needle not in text, (name, needle)
    assert list((ROOT / "workspace").glob("d7_g_*")) == []
    assert [p for p in (ROOT / "workspace").glob("*") if "d7_h" in p.name] == []
    assert list(FORMAL.glob("*d7_h*")) == []
    assert list(FORMAL.glob("*alternating*")) == []
    # This test module binds no real root/artifact (mirror BP PV-12; split
    # needles so the source scan cannot match itself).
    src = Path(__file__).read_text(encoding="utf-8")
    for needle in ("work" + "space/", "outputs_" + "comparison",
                   "MODEL_" + "F_ROOT"):
        assert needle not in src
