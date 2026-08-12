from __future__ import annotations

import inspect
import itertools

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_qspa
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_codebook import build_nonbinary_codebook_family
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import (
    _fwht,
    decode_nonbinary_fft_qspa,
    nonbinary_disclosure_accounting,
    nonbinary_syndrome,
    qsc_symbol_priors,
    symbols_to_msb_bits,
    verify_nonbinary_symbols,
)
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


def _zero_case(q: int, checks: int = 16):
    manifest, matrices = build_nonbinary_codebook_family(q)
    alice = (0,) * 64
    syndrome = nonbinary_syndrome(matrices[checks], alice, GF2mField.create(q))
    return manifest, matrices, alice, syndrome


def test_q4_xor_fwht_check_convolution_matches_brute_force():
    # The inverse transform of a product is the XOR convolution, the exact
    # additive-group operation used by each coefficient-permuted check edge.
    left = np.array([0.1, 0.2, 0.3, 0.4])
    right = np.array([0.4, 0.3, 0.2, 0.1])
    transformed = _fwht(_fwht(left) * _fwht(right)) / 4
    brute = np.array([sum(left[x] * right[target ^ x] for x in range(4)) for target in range(4)])
    assert np.allclose(transformed, brute, atol=1e-12, rtol=0)


def test_q4_full_check_outgoing_matches_brute_force_with_coefficients_and_syndrome():
    field = GF2mField.create(4)
    # Target coefficient 2, other coefficients 3 and 2, with a nonzero
    # disclosed syndrome.  This exercises both GF(q) permutations around the
    # XOR-order FWHT convolution and the coset shift.
    target_coefficient, other_coefficients, syndrome = 2, (3, 2), 1
    incoming = (np.array([0.1, 0.3, 0.4, 0.2]), np.array([0.4, 0.2, 0.1, 0.3]))
    spectra = []
    for coefficient, message in zip(other_coefficients, incoming):
        scaled = np.empty(4)
        for symbol in range(4):
            scaled[field.mul(coefficient, symbol)] = message[symbol]
        spectra.append(_fwht(scaled))
    convolved = _fwht(spectra[0] * spectra[1]) / 4
    fft_outgoing = np.array([convolved[syndrome ^ field.mul(target_coefficient, symbol)] for symbol in range(4)])
    brute = np.array([
        sum(
            incoming[0][first] * incoming[1][second]
            for first in range(4) for second in range(4)
            if field.add(field.mul(other_coefficients[0], first), field.mul(other_coefficients[1], second))
            == field.add(syndrome, field.mul(target_coefficient, symbol))
        )
        for symbol in range(4)
    ])
    assert np.allclose(fft_outgoing, brute, atol=1e-12, rtol=0)


def test_qsc_priors_and_decoder_have_no_alice_truth_argument():
    priors = qsc_symbol_priors([0, 3], 4, 0.1)
    assert np.allclose(priors, [[0.9, 1 / 30, 1 / 30, 1 / 30], [1 / 30, 1 / 30, 1 / 30, 0.9]])
    forbidden = ("alice", "truth", "callback")
    assert not any(token in parameter.lower() for parameter in inspect.signature(decode_nonbinary_fft_qspa).parameters for token in forbidden)


def test_q4_no_error_and_fixed_correctable_case_are_syndrome_consistent():
    manifest, matrices, alice, syndrome = _zero_case(4)
    no_error = decode_nonbinary_fft_qspa(alice, syndrome, manifest, matrices, check_count=16, p=0.05, max_iter=3)
    assert no_error["status"] == "syndrome_consistent"
    assert no_error["status"] != "verified_success"
    bob = list(alice); bob[0] = 1  # deterministic convergent N1 feasibility case
    corrected = decode_nonbinary_fft_qspa(bob, syndrome, manifest, matrices, check_count=16, p=0.05, max_iter=20)
    assert corrected["status"] == "syndrome_consistent"
    assert corrected["decoded_symbols"] == alice


def test_q1024_is_bounded_and_uses_verified_family_only():
    manifest, matrices, alice, syndrome = _zero_case(1024)
    result = decode_nonbinary_fft_qspa(alice, syndrome, manifest, matrices, check_count=16, p=0.01, max_iter=1)
    assert result["status"] == "syndrome_consistent"
    assert result["q"] == 1024
    assert result["declared_dense_message_bytes"] <= 16 * 1024 * 1024
    tampered = dict(manifest); tampered["manifest_id"] = "0" * 64
    assert decode_nonbinary_fft_qspa(alice, syndrome, tampered, matrices, check_count=16, p=0.01)["status"] == "codebook_invalid"


@pytest.mark.parametrize("max_iter", [0, 21])
def test_iteration_cap_fails_closed(max_iter: int):
    manifest, matrices, alice, syndrome = _zero_case(4)
    assert decode_nonbinary_fft_qspa(alice, syndrome, manifest, matrices, check_count=16, p=0.1, max_iter=max_iter)["status"] == "aborted_resource_limit"


def test_dense_resource_cap_fails_closed(monkeypatch):
    manifest, matrices, alice, syndrome = _zero_case(4)
    monkeypatch.setattr(nonbinary_qspa, "_MAX_DENSE_BYTES", 1)
    result = decode_nonbinary_fft_qspa(alice, syndrome, manifest, matrices, check_count=16, p=0.1)
    assert result["status"] == "aborted_resource_limit"
    assert result["reason"] == "dense_message_storage"


def test_msb_mapping_disclosure_and_locked_toeplitz_wrapper():
    assert symbols_to_msb_bits([0, 1, 2, 3], 4).tolist() == [0, 0, 0, 1, 1, 0, 1, 1]
    assert nonbinary_disclosure_accounting(16, 4, verification_invoked=True, verification_tag_bits=17, public_control_bits=9) == {
        "syndrome_disclosure_bits": 32, "verification_tag_bits": 17,
        "key_dependent_disclosure_bits_total": 49, "public_control_bits": 9,
    }
    assert nonbinary_disclosure_accounting(16, 4, verification_invoked=False, verification_tag_bits=17)["key_dependent_disclosure_bits_total"] == 32
    alice = [0, 1, 2, 3]
    locked_seed = seed_record(itertools.islice(itertools.cycle((0, 1, 1, 0)), len(alice) * 2 + 63))
    assert verify_nonbinary_symbols(alice, alice, 4, locked_seed, invoked=True)["verified"] is True
    mismatch = verify_nonbinary_symbols(alice, [0, 1, 2, 2], 4, locked_seed, invoked=True)
    assert mismatch["verification_invoked"] is True
    assert mismatch["verified"] is False
    assert verify_nonbinary_symbols(alice, [0, 1, 2, 2], 4, locked_seed, invoked=False)["verification_invoked"] is False


@pytest.mark.parametrize("value", ["false", 0, 1, np.bool_(False)])
def test_verification_switches_require_exact_builtin_bool(value):
    alice = [0, 1, 2, 3]
    locked_seed = seed_record(itertools.islice(itertools.cycle((0, 1, 1, 0)), len(alice) * 2 + 63))
    with pytest.raises(ValueError, match="verification_invoked must be a built-in bool"):
        nonbinary_disclosure_accounting(16, 4, verification_invoked=value)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invoked must be a built-in bool"):
        verify_nonbinary_symbols(alice, alice, 4, locked_seed, invoked=value)  # type: ignore[arg-type]
    assert nonbinary_disclosure_accounting(16, 4, verification_invoked=False)["verification_tag_bits"] == 0
    assert nonbinary_disclosure_accounting(16, 4, verification_invoked=True)["verification_tag_bits"] == 64
    assert verify_nonbinary_symbols(alice, alice, 4, locked_seed, invoked=False)["verification_invoked"] is False
    assert verify_nonbinary_symbols(alice, alice, 4, locked_seed, invoked=True)["verification_invoked"] is True
