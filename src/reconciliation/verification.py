from __future__ import annotations

import hashlib
import secrets
from typing import Iterable

import numpy as np

VERIFICATION_PROTOCOL_ID = "uhv2_batch_random_toeplitz"
VERIFICATION_FAMILY = "toeplitz_universal2"
VERIFICATION_SCOPE = "fixed_batch_union_bound"
VERIFICATION_SEED_POLICY = "uniform_random_toeplitz_seed_sampled_after_messages_fixed"
VERIFICATION_PUBLIC_MESSAGE_RULE = "toeplitz_seed_public_tag_bits_revealed"
VERIFICATION_TRANSCRIPT_SOURCE_TAG = "uniform_random_toeplitz_verification_transcript"

LEGACY_VERIFICATION_PROTOCOL_ID = "uhv1_per_block"
LEGACY_VERIFICATION_SEED_POLICY = "legacy_deterministic_public_from_identifiers_not_universal2_sampling"


def _binary_vector(values: np.ndarray | Iterable[int], *, name: str) -> np.ndarray:
    raw = np.asarray(values if isinstance(values, np.ndarray) else list(values)).reshape(-1)
    try:
        valid = np.all((raw == 0) | (raw == 1))
    except (TypeError, ValueError):
        valid = False
    if not bool(valid):
        raise ValueError(f"{name} must contain only binary values 0 or 1")
    return raw.astype(np.uint8, copy=False)


def _positive_int(value: int, *, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or int(value) <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def generate_toeplitz_seed(*, max_message_len: int, tag_bits: int) -> np.ndarray:
    """Sample the public seed for one random Toeplitz matrix using the OS CSPRNG."""
    n = _positive_int(max_message_len, name="max_message_len")
    r = _positive_int(tag_bits, name="tag_bits")
    needed_bits = n + r - 1
    raw = secrets.token_bytes((needed_bits + 7) // 8)
    return np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="little")[:needed_bits]


def universal_hash_tag(
    *,
    bits: np.ndarray | Iterable[int],
    toeplitz_seed_bits: np.ndarray | Iterable[int],
    tag_bits: int,
) -> np.ndarray:
    """Hash one fixed message with an explicitly supplied random Toeplitz seed.

    A seed sized for a longer message may be reused for shorter messages in the
    same fixed batch; the required prefix is used.
    """
    msg = _binary_vector(bits, name="bits")
    if msg.size == 0:
        raise ValueError("bits must not be empty")
    seed = _binary_vector(toeplitz_seed_bits, name="toeplitz_seed_bits")
    r = _positive_int(tag_bits, name="tag_bits")
    needed_bits = int(msg.size) + r - 1
    if seed.size < needed_bits:
        raise ValueError(
            "toeplitz_seed_bits is too short: "
            f"need at least {needed_bits} bits for message length {msg.size} and tag_bits {r}"
        )

    seed = seed[:needed_bits]
    tag = np.zeros(r, dtype=np.uint8)
    for row in range(r):
        start = r - 1 - row
        tag[row] = np.bitwise_xor.reduce(seed[start : start + msg.size] & msg)
    return tag


def verification_transcript(
    *,
    reference_bits: np.ndarray | Iterable[int],
    candidate_bits: np.ndarray | Iterable[int],
    toeplitz_seed_bits: np.ndarray | Iterable[int],
    tag_bits: int,
) -> dict[str, int | str]:
    ref = _binary_vector(reference_bits, name="reference_bits")
    cand = _binary_vector(candidate_bits, name="candidate_bits")
    if ref.size != cand.size:
        raise ValueError("reference_bits and candidate_bits must have the same length")

    seed = _binary_vector(toeplitz_seed_bits, name="toeplitz_seed_bits")
    r = _positive_int(tag_bits, name="tag_bits")
    ref_tag = universal_hash_tag(bits=ref, toeplitz_seed_bits=seed, tag_bits=r)
    cand_tag = universal_hash_tag(bits=cand, toeplitz_seed_bits=seed, tag_bits=r)
    passed = int(np.array_equal(ref_tag, cand_tag))
    return {
        "verification_protocol_id": VERIFICATION_PROTOCOL_ID,
        "verification_family": VERIFICATION_FAMILY,
        "verification_scope": VERIFICATION_SCOPE,
        "verification_seed_policy": VERIFICATION_SEED_POLICY,
        "verification_public_message_rule": VERIFICATION_PUBLIC_MESSAGE_RULE,
        "verification_transcript_source_tag": VERIFICATION_TRANSCRIPT_SOURCE_TAG,
        "verification_seed_length_bits": int(seed.size),
        "verification_seed_public_leakage_bits": 0,
        "verification_invoked_flag": 1,
        "verification_bits_budgeted": r,
        "verification_bits_used_actual": r,
        "verification_tag_leakage_bits_actual": r,
        "verification_pass_flag": passed,
        "verification_fail_flag": int(1 - passed),
    }


# Legacy helpers are retained only to read or reproduce historical uhv1 evidence.
# They must not be used by the main verification APIs above.
def _seed_stream(*, label: str, count_bytes: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < count_bytes:
        payload = f"{label}|{counter}".encode("utf-8")
        out.extend(hashlib.sha256(payload).digest())
        counter += 1
    return bytes(out[:count_bytes])


def deterministic_seed_index(*, point_id: str, layer_id: int, block_index: int) -> int:
    """Legacy uhv1 identifier-derived index; not a random universal2 choice."""
    payload = f"{LEGACY_VERIFICATION_PROTOCOL_ID}|{point_id}|{int(layer_id)}|{int(block_index)}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _toeplitz_seed_bits(
    *, point_id: str, layer_id: int, block_index: int, message_len: int, tag_bits: int
) -> np.ndarray:
    """Legacy deterministic uhv1 seed; do not use for correctness bounds."""
    needed_bits = max(1, int(message_len) + int(tag_bits) - 1)
    needed_bytes = (needed_bits + 7) // 8
    seed_idx = deterministic_seed_index(point_id=point_id, layer_id=layer_id, block_index=block_index)
    label = f"{LEGACY_VERIFICATION_PROTOCOL_ID}|toeplitz|{seed_idx}|{message_len}|{tag_bits}"
    raw = _seed_stream(label=label, count_bytes=needed_bytes)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="little")
    return bits[:needed_bits].astype(np.uint8, copy=False)
