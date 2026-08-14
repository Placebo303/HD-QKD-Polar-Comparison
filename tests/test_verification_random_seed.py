import numpy as np
import pytest

from src.reconciliation.verification import (
    VERIFICATION_SEED_POLICY,
    generate_toeplitz_seed,
    universal_hash_tag,
    verification_transcript,
)


def test_explicit_random_toeplitz_seed_contract() -> None:
    message = np.array([1, 0, 1, 1, 0, 1], dtype=np.uint8)
    seed = np.array([1, 0, 0, 1, 1, 0, 1, 0, 1], dtype=np.uint8)

    tag_a = universal_hash_tag(bits=message, toeplitz_seed_bits=seed, tag_bits=4)
    tag_b = universal_hash_tag(bits=message, toeplitz_seed_bits=seed, tag_bits=4)
    assert np.array_equal(tag_a, tag_b)

    other_seed = seed.copy()
    other_seed[0] ^= 1
    assert not np.array_equal(tag_a, universal_hash_tag(bits=message, toeplitz_seed_bits=other_seed, tag_bits=4))

    shorter = message[:3]
    assert np.array_equal(
        universal_hash_tag(bits=shorter, toeplitz_seed_bits=seed, tag_bits=4),
        universal_hash_tag(bits=shorter, toeplitz_seed_bits=seed[:6], tag_bits=4),
    )

    different = message.copy()
    different[0] ^= 1
    transcript = verification_transcript(
        reference_bits=message,
        candidate_bits=different,
        toeplitz_seed_bits=seed,
        tag_bits=4,
    )
    assert transcript["verification_pass_flag"] == 0
    assert transcript["verification_seed_policy"] == VERIFICATION_SEED_POLICY
    assert transcript["verification_tag_leakage_bits_actual"] == 4
    assert transcript["verification_seed_public_leakage_bits"] == 0


def test_standard_toeplitz_diagonal_indexing() -> None:
    # Seed indices represent diagonals -(r-1), ..., n-1.
    tag = universal_hash_tag(
        bits=[1, 0, 1],
        toeplitz_seed_bits=[1, 0, 1, 1],
        tag_bits=2,
    )
    np.testing.assert_array_equal(tag, np.array([1, 0], dtype=np.uint8))


def test_seed_generation_and_invalid_inputs_fail_closed() -> None:
    generated = generate_toeplitz_seed(max_message_len=20, tag_bits=8)
    assert generated.shape == (27,)
    assert set(generated.tolist()) <= {0, 1}

    with pytest.raises(ValueError, match="too short"):
        universal_hash_tag(bits=[1, 0, 1], toeplitz_seed_bits=[1, 0], tag_bits=2)
    with pytest.raises(ValueError, match="binary"):
        universal_hash_tag(bits=[1, 2], toeplitz_seed_bits=[1, 0, 1], tag_bits=2)
    with pytest.raises(ValueError, match="binary"):
        universal_hash_tag(bits=[1, 0], toeplitz_seed_bits=[1, 7, 0], tag_bits=2)
    with pytest.raises(ValueError, match="positive integer"):
        universal_hash_tag(bits=[1], toeplitz_seed_bits=[1], tag_bits=0)
    with pytest.raises(ValueError, match="same length"):
        verification_transcript(
            reference_bits=[1, 0], candidate_bits=[1], toeplitz_seed_bits=[1, 0, 1], tag_bits=2
        )
