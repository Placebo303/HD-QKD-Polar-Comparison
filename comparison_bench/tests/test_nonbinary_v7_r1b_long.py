"""NBLDPC7 R1B decoder acceptance: exhaustive GF(4)/GF(8) prior-combining
oracle, alignment bijection, wrapping of the accepted R1A flooding/layered
core, noiseless and planted cases, deterministic repeat, iteration and
allocation caps, and fail-closed numerical contracts."""
from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1b_long as long
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1b_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_long as r1a_long
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import (_normalise,
                                                                            nonbinary_syndrome,
                                                                            qsc_symbol_priors)

SCHEDULES = ("flooding", "layered")


def _decode(bob, repeated, alice, p, schedule="flooding", max_iter=100):
    manifest, matrix = cb.codebook()
    syndrome = nonbinary_syndrome(matrix, alice, GF2mField.create(1024))
    return long.decode_nbldpc_v7_r1b(bob, repeated, syndrome, manifest, matrix,
                                     check_count=170, p=p, schedule=schedule, max_iter=max_iter)


def _bruteforce_combined(bob_value, repeated_value, multiplier, field, p):
    """Exact posterior combination: align the repetition, then multiply the
    two QSC likelihoods and normalize."""
    q = field.q
    aligned = field.mul(field.inverse(multiplier), repeated_value)
    prior = np.empty(q, dtype=np.float64)
    for symbol in range(q):
        mother = p / (q - 1) if bob_value != symbol else 1.0 - p
        repetition = p / (q - 1) if aligned != symbol else 1.0 - p
        prior[symbol] = mother * repetition
    return prior / prior.sum()


# ---------------------------------------------------------------- oracle

def test_exhaustive_gf4_gf8_prior_combination_matches_bruteforce():
    for q in (4, 8):
        field = GF2mField.create(q)
        for multiplier in range(1, q):
            for bob_value in range(q):
                for repeated_value in range(q):
                    combined = long.combined_qsc_priors((bob_value,), (repeated_value,),
                                                        (multiplier,), q, 0.3)
                    brute = _bruteforce_combined(bob_value, repeated_value, multiplier, field, 0.3)
                    assert np.allclose(combined[0], brute)
                    aligned = long.aligned_observation((repeated_value,), (multiplier,), field)
                    assert field.mul(multiplier, aligned[0]) == repeated_value


def test_aligned_observation_is_a_valid_bijective_map():
    for q in (4, 8):
        field = GF2mField.create(q)
        for multiplier in range(1, q):
            aligned = long.aligned_observation(range(q), (multiplier,) * q, field)
            assert len(aligned) == q and sorted(int(x) for x in aligned) == list(range(q))
            for z in range(q):
                assert field.mul(multiplier, int(aligned[z])) == z
    # zero multipliers are rejected fail-closed.
    field = GF2mField.create(8)
    with pytest.raises(ValueError, match="zero multiplier"):
        long.aligned_observation((1, 2), (0, 1), field)


def test_combined_prior_is_the_exact_qsc_posterior_product():
    q = 8
    bob = (0, 1, 2)
    repeated = (5, 6, 7)
    multipliers = (3, 5, 1)
    combined = long.combined_qsc_priors(bob, repeated, multipliers, q, 0.25)
    for index in range(3):
        aligned = long.aligned_observation((repeated[index],), (multipliers[index],),
                                           GF2mField.create(q))[0]
        mother = qsc_symbol_priors((bob[index],), q, 0.25)[0]
        repetition = qsc_symbol_priors((int(aligned),), q, 0.25)[0]
        brute = _normalise(mother * repetition)
        assert brute is not None and np.allclose(combined[index], brute)


# ---------------------------------------------------------------- decoder core

def test_public_signature_has_no_alice_truth_or_callback():
    names = list(inspect.signature(long.decode_nbldpc_v7_r1b).parameters)
    assert not any(token in name.lower() for name in names for token in ("alice", "truth", "callback"))
    assert long._MAX_ITER == 100 and long._LAMBDA == 0.75
    assert long._PRIMARY_SCHEDULE == "flooding" and long._SCHEDULES == ("flooding", "layered")
    assert long._SYNDROME_DISCLOSURE_BITS == 1700


def test_production_runner_is_the_frozen_flooding_primary(monkeypatch):
    captured = {}
    def observed(*args, **kwargs):
        captured["schedule"] = kwargs.get("schedule")
        return {"status": "decode_failed", "iterations": 1}
    monkeypatch.setattr(long, "decode_nbldpc_v7_r1b", observed)
    long.production_runner((0,) * 256, (0,) * 256, (0,) * 170, {"q": 1024}, (0,),
                           check_count=170, p=.20)
    assert captured["schedule"] == "flooding"


def test_decoder_wraps_the_accepted_r1a_core(monkeypatch):
    # The R1B decoder must reuse the accepted R1A flooding/layered core with
    # the combined prior, and reuse the accepted check-update semantics.
    assert long.check_update_fft_qspa is r1a_long.check_update_fft_qspa
    manifest, matrix = cb.codebook()
    zero = (0,) * 256
    syndrome = nonbinary_syndrome(matrix, zero, GF2mField.create(1024))
    observed = {}
    original_flooding = r1a_long._decode_flooding
    def capture(bob, disclosed, matrix_arg, checks, variables, priors, field, check_count,
                codebook_id, declared, *, max_iter):
        observed["priors"] = priors
        observed["max_iter"] = max_iter
        return original_flooding(bob, disclosed, matrix_arg, checks, variables, priors, field,
                                 check_count, codebook_id, declared, max_iter=max_iter)
    monkeypatch.setattr(r1a_long, "_decode_flooding", capture)
    expected_priors = long.combined_qsc_priors(zero, zero, cb.multipliers(), 1024, .20)
    result = long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix,
                                       check_count=170, p=.20, schedule="flooding")
    assert result["status"] == "syndrome_consistent"
    assert observed["max_iter"] == 100
    assert np.allclose(observed["priors"], expected_priors)
    # layered schedule routes to the accepted layered core.
    observed.clear()
    original_layered = r1a_long._decode_layered
    def capture_layered(bob, disclosed, matrix_arg, checks, variables, priors, field, check_count,
                        codebook_id, declared, *, max_iter):
        observed["priors"] = priors
        return original_layered(bob, disclosed, matrix_arg, checks, variables, priors, field,
                                check_count, codebook_id, declared, max_iter=max_iter)
    monkeypatch.setattr(r1a_long, "_decode_layered", capture_layered)
    result = long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix,
                                       check_count=170, p=.20, schedule="layered")
    assert result["status"] == "syndrome_consistent"
    assert np.allclose(observed["priors"], expected_priors)


def test_noiseless_frames_decode_in_both_strata_and_schedules():
    manifest, matrix = cb.codebook()
    for schedule in SCHEDULES:
        for p in (.20, .30):
            zero = (0,) * 256
            syndrome = nonbinary_syndrome(matrix, zero, GF2mField.create(1024))
            result = long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix,
                                               check_count=170, p=p, schedule=schedule)
            assert result["status"] == "syndrome_consistent" and result["syndrome_consistent"]
            assert result["decoded_symbols"] == zero and 1 <= result["iterations"] <= 100


def test_planted_one_and_two_symbol_errors_are_corrected():
    rng = np.random.default_rng(2026080497)
    field = GF2mField.create(1024)
    multipliers = cb.multipliers()
    for schedule in SCHEDULES:
        for p in (.20, .30):
            alice = tuple(int(x) for x in rng.integers(0, 1024, 256))
            repeated = np.array([field.mul(int(multipliers[c]), int(alice[c])) for c in range(256)],
                                dtype=np.int64)
            for n_errors in (1, 2):
                bob = list(alice)
                for index in rng.choice(256, size=n_errors, replace=False):
                    bob[int(index)] ^= int(rng.integers(1, 1024))
                repeated_errors = list(repeated)
                for index in rng.choice(256, size=n_errors, replace=False):
                    repeated_errors[int(index)] ^= int(rng.integers(1, 1024))
                result = _decode(tuple(bob), tuple(repeated_errors), alice, p, schedule=schedule)
                assert result["status"] == "syndrome_consistent"
                assert result["decoded_symbols"] == alice


def test_deterministic_repeat():
    manifest, matrix = cb.codebook()
    syndrome = nonbinary_syndrome(matrix, (0,) * 256, GF2mField.create(1024))
    for schedule in SCHEDULES:
        first = long.decode_nbldpc_v7_r1b((0,) * 256, (0,) * 256, syndrome, manifest, matrix,
                                          check_count=170, p=.20, schedule=schedule)
        second = long.decode_nbldpc_v7_r1b((0,) * 256, (0,) * 256, syndrome, manifest, matrix,
                                           check_count=170, p=.20, schedule=schedule)
        assert first == second


def test_invalid_input_and_fail_closed_boundaries():
    manifest, matrix = cb.codebook()
    zero = (0,) * 256
    syndrome = nonbinary_syndrome(matrix, zero, GF2mField.create(1024))
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=171,
                                     p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=170,
                                     p=.25)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b(zero, zero, (0,) * 169, manifest, matrix, check_count=170,
                                     p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b((0,) * 255, zero, syndrome, manifest, matrix, check_count=170,
                                     p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b(zero, (0,) * 255, syndrome, manifest, matrix, check_count=170,
                                     p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b((0,) * 257, zero, syndrome, manifest, matrix, check_count=170,
                                     p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, {"q": 512}, matrix, check_count=170,
                                     p=.20)["status"] == "unsupported_domain"
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=170,
                                     p=.20, schedule="ems")["status"] == "invalid_input"
    forged = dict(manifest); forged["construction_seed"] = forged["construction_seed"] + 1
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, forged, matrix, check_count=170,
                                     p=.20)["status"] == "codebook_invalid"
    forged_mult = dict(manifest)
    forged_mult["multipliers"] = list(manifest["multipliers"]); forged_mult["multipliers"][0] = 1
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, forged_mult, matrix, check_count=170,
                                     p=.20)["status"] == "codebook_invalid"
    assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix[:169], check_count=170,
                                     p=.20)["status"] == "codebook_invalid"


def test_allocation_cap_and_iteration_bounds(monkeypatch):
    manifest, matrix = cb.codebook()
    zero = (0,) * 256
    syndrome = nonbinary_syndrome(matrix, zero, GF2mField.create(1024))
    for schedule in SCHEDULES:
        assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=170,
                                         p=.20, schedule=schedule,
                                         max_iter=101)["status"] == "aborted_resource_limit"
        assert long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=170,
                                         p=.20, schedule=schedule,
                                         max_iter=0)["status"] == "aborted_resource_limit"
    monkeypatch.setattr(long, "_MAX_DENSE_BYTES", 1)
    result = long.decode_nbldpc_v7_r1b(zero, zero, syndrome, manifest, matrix, check_count=170, p=.20)
    assert result["status"] == "aborted_resource_limit" and result["reason"] == "dense_message_storage"


def test_declared_dense_message_bytes_are_exact_for_the_frozen_graph():
    declared = long._declared_dense_bytes(256, 512, 1024)
    assert declared == (2 * 256 + 2 * 512) * 1024 * 8
    assert declared == 12_582_912
    assert declared <= 16 * 1024 * 1024
    # no second dense message family: the repetition is combined into the prior.
    assert long._declared_dense_bytes_r1b() == declared


def test_iteration_cap_returns_decode_failed_with_full_count():
    manifest, matrix = cb.codebook()
    field = GF2mField.create(1024)
    multipliers = cb.multipliers()
    rng = np.random.default_rng(2026080243)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 256))
    repeated = np.array([field.mul(int(multipliers[c]), int(alice[c])) for c in range(256)],
                        dtype=np.int64)
    errors = tuple(int(x) for x in rng.integers(0, 1024, 256))
    bob = tuple(int(a) ^ int(e) for a, e in zip(alice, errors))
    repeated_errors = tuple(int(a) ^ int(e) for a, e in zip(repeated, errors))
    syndrome = nonbinary_syndrome(matrix, alice, field)
    for schedule in SCHEDULES:
        result = long.decode_nbldpc_v7_r1b(bob, repeated_errors, syndrome, manifest, matrix,
                                           check_count=170, p=.20, schedule=schedule, max_iter=3)
        assert result["status"] == "decode_failed" and result["iterations"] == 3
        assert result["reason"] == "iteration_limit"


def test_fail_closed_numerical_cases(monkeypatch):
    manifest, matrix = cb.codebook()
    syndrome = nonbinary_syndrome(matrix, (0,) * 256, GF2mField.create(1024))
    assert _normalise(np.array([np.nan] + [0.0] * 1023)) is None
    assert _normalise(np.array([np.inf] + [0.0] * 1023)) is None
    assert _normalise(np.zeros(1024)) is None
    # the accepted QSC prior helper rejects out-of-domain p fail-closed.
    with pytest.raises(ValueError, match="frozen open domain"):
        qsc_symbol_priors((0,), 1024, 0.999999999)
    with pytest.raises(ValueError, match="frozen open domain"):
        long.combined_qsc_priors((0,), (0,), (1,), 1024, 0.999999999)
    # forcing the accepted core's normalisation seam to fail closes the R1B
    # decoder as decoder_error for both schedules (no fallback).
    monkeypatch.setattr(r1a_long, "_normalise", lambda values: None)
    for schedule in SCHEDULES:
        result = long.decode_nbldpc_v7_r1b((0,) * 256, (0,) * 256, syndrome, manifest, matrix,
                                           check_count=170, p=.20, schedule=schedule)
        assert result["status"] == "decoder_error"
