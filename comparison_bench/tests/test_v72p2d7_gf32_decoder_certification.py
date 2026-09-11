"""D7-A GF32 decoder ground-truth certification tests.

Tiny synthetic in-memory correctness-unit calls only. No Model-F, CAL/VAL,
real/raw, formal roots, VOID contents, --phase, R1d, G1, or G2.
Frozen seeds: 2026091001 (check-update priors), 2026091002 (tree/cycle priors).
Tolerance: max-abs 1e-10 on posteriors/probabilities; exact int table identity.
"""

from __future__ import annotations

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import v35_algorithm_development as v35
from comparison_bench.src.comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.v72p2d7_gf32_decoder_certification import (
    ADD_REF,
    INV_REF,
    MUL_REF,
    Q,
    direct_check_to_var,
    exact_posterior,
    row_layered_reference,
    syndrome_reference,
)

TOL = 1e-10
SEED_CHECK = 2026091001
SEED_GRAPH = 2026091002
NONTRIVIAL_COEFFS = (2, 7, 13, 29)
SYNDROMES = (0, 5, 17, 31)


def _softmax(log_msgs: np.ndarray) -> np.ndarray:
    z = np.asarray(log_msgs, dtype=np.float64)
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _ordinary_prior(n: int, offset: int = 0) -> np.ndarray:
    base = 1.0 + (np.arange(Q) + offset) % 7
    row = base / base.sum()
    return np.tile(row, (n, 1))


def _skewed_prior(n: int, peak: int, mass: float = 0.9) -> np.ndarray:
    row = np.full(Q, (1.0 - mass) / (Q - 1))
    row[peak] = mass
    return np.tile(row, (n, 1))


def _prod_tables():
    return v35._get_gf32_tables(GF2mField.create(32))


def test_declared_field_constants():
    assert v35.FIELD_Q == 32
    assert v35.FIELD_POLY == 37 == 0b100101
    assert Q == 32


def test_reference_tables_equal_production():
    mul_p, add_p, inv_p = _prod_tables()
    assert np.array_equal(MUL_REF, mul_p)
    assert np.array_equal(ADD_REF, add_p)
    assert np.array_equal(INV_REF, inv_p)
    # Spot identities from the independent tables alone.
    for a in (1, 2, 7, 13, 29, 31):
        assert MUL_REF[a, 1] == a
        assert MUL_REF[a, int(INV_REF[a])] == 1
    assert MUL_REF[2, 3] == MUL_REF[3, 2]
    a, b, c = 5, 17, 29
    lhs = MUL_REF[a, ADD_REF[b, c]]
    rhs = ADD_REF[int(MUL_REF[a, b]), int(MUL_REF[a, c])]
    assert lhs == rhs


def _prod_check_out(in_probs, coeffs, syndrome):
    field = GF2mField.create(32)
    tables = _prod_tables()
    log_msgs = [np.log(np.maximum(np.asarray(p), 1e-15)) for p in in_probs]
    outs = v35._check_update_log_batch(log_msgs, list(coeffs), syndrome, field, tables)
    return [_softmax(o) for o in outs]


def test_check_update_deg2_full_multiplier_sweep():
    rng = np.random.default_rng(SEED_CHECK)
    worst = 0.0
    worst_tuple = None
    priorsets = [("ordinary", _ordinary_prior(2)), ("skewed", _skewed_prior(2, 5))]
    for c in range(1, 32):
        for syn in SYNDROMES:
            for pname, prior in priorsets:
                ref = direct_check_to_var([prior[0], prior[1]], [1, c], syn)
                prod = _prod_check_out([prior[0], prior[1]], [1, c], syn)
                for t in range(2):
                    err = float(np.max(np.abs(ref[t] - prod[t])))
                    if err > worst:
                        worst, worst_tuple = err, (c, syn, pname, t)
    assert worst <= TOL, f"max-abs {worst} at {worst_tuple}"
    # All 32 skewed peaks, fixed nontrivial check, zero syndrome.
    for peak in range(32):
        prior = _skewed_prior(2, peak)
        ref = direct_check_to_var([prior[0], prior[1]], [1, 7], 0)
        prod = _prod_check_out([prior[0], prior[1]], [1, 7], 0)
        for t in range(2):
            assert float(np.max(np.abs(ref[t] - prod[t]))) <= TOL


def test_check_update_deg3_sampled():
    rng = np.random.default_rng(SEED_CHECK)
    triples = [(1, 1, 1), (1, 2, 3), (2, 7, 13), (1, 13, 29)]
    worst = 0.0
    worst_tuple = None
    for coeffs in triples:
        for syn in (0, 17):
            for pname, prior in (
                ("ordinary", _ordinary_prior(3, offset=coeffs[0])),
                ("skewed", _skewed_prior(3, 17)),
            ):
                in_p = [prior[0], prior[1], prior[2]]
                ref = direct_check_to_var(in_p, list(coeffs), syn)
                prod = _prod_check_out(in_p, list(coeffs), syn)
                for t in range(3):
                    err = float(np.max(np.abs(ref[t] - prod[t])))
                    if err > worst:
                        worst, worst_tuple = err, (coeffs, syn, pname, t)
    assert worst <= TOL, f"max-abs {worst} at {worst_tuple}"


def _wrong_direction_out(in_probs, coeffs, syndrome):
    # Negative control: permute by inv(coeff) instead of coeff.
    cleaned = [np.maximum(np.asarray(p, float), 1e-15) for p in in_probs]
    cleaned = [p / p.sum() for p in cleaned]
    outs = []
    for t, c in enumerate(coeffs):
        ci = int(INV_REF[int(c)])
        others = [j for j in range(len(coeffs)) if j != t]
        msg = np.zeros(Q)
        for v in range(Q):
            tgt = ADD_REF[syndrome, MUL_REF[ci, v]]
            tot = 0.0
            import itertools

            for assign in itertools.product(range(Q), repeat=len(others)):
                acc = 0
                pr = 1.0
                for j, xj in zip(others, assign):
                    cj = coeffs[j]
                    acc ^= int(MUL_REF[cj, xj])
                    pr *= cleaned[j][xj]
                if acc == tgt:
                    tot += pr
        outs.append(np.maximum(msg, 1e-15))
    return [o / o.sum() for o in outs]


def _wrong_shift_out(in_probs, coeffs, syndrome):
    # Negative control: syndrome shift ignoring the edge coefficient.
    cleaned = [np.maximum(np.asarray(p, float), 1e-15) for p in in_probs]
    cleaned = [p / p.sum() for p in cleaned]
    outs = []
    for t in range(len(coeffs)):
        others = [j for j in range(len(coeffs)) if j != t]
        msg = np.zeros(Q)
        for v in range(Q):
            tgt = ADD_REF[syndrome, v]
            tot = 0.0
            import itertools

            for assign in itertools.product(range(Q), repeat=len(others)):
                acc = 0
                pr = 1.0
                for j, xj in zip(others, assign):
                    acc ^= int(MUL_REF[coeffs[j], xj])
                    pr *= cleaned[j][xj]
                if acc == tgt:
                    tot += pr
        outs.append(np.maximum(msg, 1e-15))
    return [o / o.sum() for o in outs]


def test_negative_controls_discriminate():
    prior = _skewed_prior(2, 5)
    in_p = [prior[0], prior[1]]
    ref = direct_check_to_var(in_p, [3, 7], 17)
    wrong_c = _wrong_direction_out(in_p, [3, 7], 17)
    wrong_s = _wrong_shift_out(in_p, [3, 7], 17)
    err_c = max(float(np.max(np.abs(ref[t] - wrong_c[t]))) for t in range(2))
    err_s = max(float(np.max(np.abs(ref[t] - wrong_s[t]))) for t in range(2))
    assert err_c > 1e-6, "coeff-direction trap does not discriminate"
    assert err_s > 1e-6, "syndrome-shift trap does not discriminate"


def _prod_decode_beliefs(h, priors, syndromes, max_iter):
    res = v35.decode_row_layered_fftqspa(
        np.asarray(h, dtype=np.uint8),
        np.asarray(priors, dtype=np.float64),
        np.asarray(syndromes, dtype=np.uint8),
        max_iter=max_iter,
        damping_alpha=1.0,
        warm_beliefs=None,
        field=None,
    )
    return res


def test_tree_single_check_posterior():
    h = np.array([[1, 7]], dtype=np.uint8)
    for pname, prior in (("ordinary", _ordinary_prior(2)), ("skewed", _skewed_prior(2, 17))):
        # Non-satisfied MAP: peak both vars at 0 -> syndrome 0; use syn 5.
        syn = np.array([5], dtype=np.uint8)
        res = _prod_decode_beliefs(h, prior, syn, 3)
        assert res.iterations > 0
        expected = exact_posterior(h, prior, syn)
        got = _softmax(res.final_beliefs)
        assert float(np.max(np.abs(got - expected))) <= TOL
        assert np.all(np.isfinite(res.final_beliefs))
    # Deg-3 single check.
    h3 = np.array([[1, 2, 13]], dtype=np.uint8)
    prior3 = _skewed_prior(3, 3)
    syn3 = np.array([17], dtype=np.uint8)
    res3 = _prod_decode_beliefs(h3, prior3, syn3, 3)
    assert float(np.max(np.abs(_softmax(res3.final_beliefs) - exact_posterior(h3, prior3, syn3)))) <= TOL


def test_tree_two_check_chain_posterior():
    h = np.array([[1, 2, 0], [0, 3, 1]], dtype=np.uint8)
    rng = np.random.default_rng(SEED_GRAPH)
    counties = rng.random((3, Q)) + 0.2
    prior = counties / counties.sum(axis=1, keepdims=True)
    x_map = np.argmax(prior, axis=1)
    syn = syndrome_reference(h, x_map)
    # Force a non-satisfied initial MAP.
    syn = np.array([(int(syn[0]) + 1) % Q, int(syn[1])], dtype=np.uint8)
    assert not np.array_equal(syndrome_reference(h, x_map), syn)
    res = _prod_decode_beliefs(h, prior, syn, 3)
    expected = exact_posterior(h, prior, syn)
    assert float(np.max(np.abs(_softmax(res.final_beliefs) - expected))) <= TOL


def test_initial_satisfied_convention():
    h = np.array([[1, 7]], dtype=np.uint8)
    prior = _skewed_prior(2, 0)  # MAP (0,0) satisfies syndrome 0.
    syn = np.array([0], dtype=np.uint8)
    res = _prod_decode_beliefs(h, prior, syn, 3)
    assert res.iterations == 0
    assert res.syndrome_ok
    cleaned = np.maximum(prior, 1e-15)
    cleaned /= cleaned.sum(axis=1, keepdims=True)
    assert float(np.max(np.abs(_softmax(res.final_beliefs) - cleaned))) <= TOL


def test_loopy_cycle_per_sweep():
    h = np.array([[2, 1, 0], [0, 3, 1], [1, 0, 5]], dtype=np.uint8)
    prior = _skewed_prior(3, 9)
    syn = np.array([5, 0, 17], dtype=np.uint8)
    assert not np.array_equal(
        syndrome_reference(h, np.argmax(prior, axis=1)), syn
    ), "fixture must start non-satisfied"
    sweeps, iters, _ = row_layered_reference(h, prior, syn, 3)
    assert iters == 3 and len(sweeps) == 3
    for k in (1, 2, 3):
        res = _prod_decode_beliefs(h, prior, syn, k)
        assert res.iterations == k, f"expected full {k} sweeps, got {res.iterations}"
        err = float(np.max(np.abs(_softmax(res.final_beliefs) - _softmax(sweeps[k - 1]))))
        assert err <= TOL, f"sweep {k}: max-abs {err}"


def test_loopy_four_var_with_deg3_per_sweep():
    h = np.array([[1, 2, 0, 3], [0, 7, 1, 0], [5, 0, 1, 13]], dtype=np.uint8)
    prior = _ordinary_prior(4)
    syn = np.array([31, 5, 0], dtype=np.uint8)
    assert not np.array_equal(
        syndrome_reference(h, np.argmax(prior, axis=1)), syn
    ), "fixture must start non-satisfied"
    sweeps, iters, _ = row_layered_reference(h, prior, syn, 3)
    assert iters == 3 and len(sweeps) == 3
    for k in (1, 2, 3):
        res = _prod_decode_beliefs(h, prior, syn, k)
        assert res.iterations == k
        err = float(np.max(np.abs(_softmax(res.final_beliefs) - _softmax(sweeps[k - 1]))))
        assert err <= TOL, f"sweep {k}: max-abs {err}"


def test_final_beliefs_are_log_domain():
    h = np.array([[1, 7]], dtype=np.uint8)
    prior = _skewed_prior(2, 17)
    syn = np.array([5], dtype=np.uint8)
    res = _prod_decode_beliefs(h, prior, syn, 1)
    bel = np.asarray(res.final_beliefs, dtype=np.float64)
    assert bel.shape == (2, 32)
    # Log-domain beliefs are not normalized probabilities.
    assert not np.allclose(bel.sum(axis=1), 1.0)
    q = _softmax(bel)
    assert np.all(q > 0) and np.allclose(q.sum(axis=1), 1.0)
    assert int(np.argmax(q[0])) == int(res.x_hat[0])


def test_softmax_rows_tiny():
    z = np.array([[0.0, 1.0, 2.0], [-1.0, -1.0, 2.0]])
    q = d5._softmax_rows(z)
    assert q.shape == z.shape
    assert np.all(q > 0) and np.allclose(q.sum(axis=1), 1.0)
    assert q[0, 2] > q[0, 1] > q[0, 0]
    # softmax(log p) recovers p: no double-exponentiation concern.
    p = np.array([[0.5, 0.3, 0.2]])
    assert np.allclose(d5._softmax_rows(np.log(p)), p, atol=1e-12)


def test_app_fed_l2_prior_explicit():
    rng = np.random.default_rng(SEED_GRAPH)
    p2 = rng.random((2, 3, Q)) + 0.1
    p2 /= p2.sum(axis=2, keepdims=True)
    bob = np.array([0, 2, 1, 2])
    q = np.array(
        [[0.7, 0.3], [0.2, 0.8], [0.5, 0.5], [0.99, 0.01]]
    )
    seg = p2[:, bob, :]
    expected = np.einsum("nq,qnv->nv", q, seg)
    expected = np.maximum(expected, d5.DECODER_FLOOR)
    expected /= expected.sum(axis=1, keepdims=True)
    got = d5.app_fed_l2_prior(p2, bob, q)
    assert got.shape == (4, Q)
    assert np.all(got > 0) and np.allclose(got.sum(axis=1), 1.0)
    assert float(np.max(np.abs(got - expected))) <= 1e-12


def test_run_layered_block_bridge_with_fake_decoder():
    tiny_q = 32
    h1 = np.array([[1, 1]], dtype=np.int64)
    h2 = np.array([[1, 2]], dtype=np.int64)
    p1 = np.full((tiny_q, 2), 1.0 / tiny_q)
    p1[3, 0] = 0.6
    p1[:, 0] /= p1[:, 0].sum()
    p1[9, 1] = 0.6
    p1[:, 1] /= p1[:, 1].sum()
    rng = np.random.default_rng(SEED_GRAPH)
    p2 = rng.random((tiny_q, 2, tiny_q)) + 0.1
    p2 /= p2.sum(axis=2, keepdims=True)
    block = {
        "bob": np.array([0, 1]),
        "u1": np.array([3, 9]),
        "u2": np.array([4, 7]),
    }
    captured = {}

    class _FakeRes:
        def __init__(self, x_hat, beliefs):
            self.x_hat = x_hat
            self.syndrome_ok = True
            self.iterations = 1
            self.final_beliefs = beliefs
            # Explicit conditioned provenance: this bridge test exercises the
            # CHECK_UPDATED pass-through of the D7/BP interface.
            self.belief_provenance = "CHECK_UPDATED"

    log_bel = np.log(np.array([[0.8] + [0.2 / 31] * 31, [0.2 / 31] * 31 + [0.8]]))

    def fake_decode(h, prior, syn, layer=None):
        captured.setdefault("priors", []).append(np.asarray(prior))
        if len(captured["priors"]) == 1:
            return _FakeRes(np.array([3, 9]), log_bel)
        return _FakeRes(np.asarray([4, 7]), None)

    out = d5._run_layered_block(fake_decode, h1, h2, p1, p2, block, False)
    assert out["app_l1_exact"] and out["finite"]
    # L2 prior fed must equal softmax(fake log beliefs) @ P (probability path).
    q = d5._softmax_rows(log_bel)
    expected_l2 = d5.app_fed_l2_prior(p2, block["bob"], q)
    assert np.allclose(captured["priors"][1], expected_l2, atol=1e-12)

    # Absent-belief fallback: uniform q over U1.
    captured.clear()

    def fake_none(h, prior, syn, layer=None):
        captured.setdefault("priors", []).append(np.asarray(prior))
        n = np.asarray(prior).shape[0]
        w = int(np.asarray(h).shape[1])
        assert w == 2  # block width n=2; U1 alphabet dim is 32
        return _FakeRes(np.zeros(n, dtype=np.int64), None)

    d5._run_layered_block(fake_none, h1, h2, p1, p2, block, False)
    uni = np.full((2, tiny_q), 1.0 / tiny_q)
    assert np.allclose(captured["priors"][1], d5.app_fed_l2_prior(p2, block["bob"], uni), atol=1e-12)
