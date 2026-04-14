from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np

VERIFICATION_PROTOCOL_ID = "uhv1_per_block"
VERIFICATION_FAMILY = "universal_hash"
VERIFICATION_SCOPE = "per_block"
VERIFICATION_SEED_POLICY = "deterministic_public_from_point_id_layer_id_block_index"
VERIFICATION_PUBLIC_MESSAGE_RULE = "tag_bits_revealed"
VERIFICATION_TRANSCRIPT_SOURCE_TAG = "deterministic_public_universal_hash_transcript"


def _seed_stream(*, label: str, count_bytes: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < count_bytes:
        payload = f"{label}|{counter}".encode("utf-8")
        out.extend(hashlib.sha256(payload).digest())
        counter += 1
    return bytes(out[:count_bytes])


def deterministic_seed_index(*, point_id: str, layer_id: int, block_index: int) -> int:
    payload = f"{VERIFICATION_PROTOCOL_ID}|{point_id}|{int(layer_id)}|{int(block_index)}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _toeplitz_seed_bits(*, point_id: str, layer_id: int, block_index: int, message_len: int, tag_bits: int) -> np.ndarray:
    needed_bits = max(1, int(message_len) + int(tag_bits) - 1)
    needed_bytes = (needed_bits + 7) // 8
    seed_idx = deterministic_seed_index(point_id=point_id, layer_id=layer_id, block_index=block_index)
    label = f"{VERIFICATION_PROTOCOL_ID}|toeplitz|{seed_idx}|{message_len}|{tag_bits}"
    raw = _seed_stream(label=label, count_bytes=needed_bytes)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="little")
    return bits[:needed_bits].astype(np.uint8, copy=False)


def universal_hash_tag(*, bits: np.ndarray, point_id: str, layer_id: int, block_index: int, tag_bits: int) -> np.ndarray:
    msg = np.asarray(bits, dtype=np.uint8).reshape(-1)
    r = int(tag_bits)
    if r <= 0:
        return np.zeros(0, dtype=np.uint8)
    seed_bits = _toeplitz_seed_bits(
        point_id=str(point_id),
        layer_id=int(layer_id),
        block_index=int(block_index),
        message_len=int(msg.size),
        tag_bits=r,
    )
    tag = np.zeros(r, dtype=np.uint8)
    for row in range(r):
        window = seed_bits[row:row + msg.size]
        tag[row] = np.bitwise_xor.reduce(window & msg) if msg.size > 0 else 0
    return tag


def verification_transcript(
    *,
    reference_bits: np.ndarray,
    candidate_bits: np.ndarray,
    point_id: str,
    layer_id: int,
    block_index: int,
    tag_bits: int,
) -> dict[str, int | str]:
    ref = np.asarray(reference_bits, dtype=np.uint8).reshape(-1)
    cand = np.asarray(candidate_bits, dtype=np.uint8).reshape(-1)
    ref_tag = universal_hash_tag(
        bits=ref,
        point_id=str(point_id),
        layer_id=int(layer_id),
        block_index=int(block_index),
        tag_bits=int(tag_bits),
    )
    cand_tag = universal_hash_tag(
        bits=cand,
        point_id=str(point_id),
        layer_id=int(layer_id),
        block_index=int(block_index),
        tag_bits=int(tag_bits),
    )
    passed = int(np.array_equal(ref_tag, cand_tag))
    return {
        "verification_protocol_id": VERIFICATION_PROTOCOL_ID,
        "verification_family": VERIFICATION_FAMILY,
        "verification_scope": VERIFICATION_SCOPE,
        "verification_seed_policy": VERIFICATION_SEED_POLICY,
        "verification_public_message_rule": VERIFICATION_PUBLIC_MESSAGE_RULE,
        "verification_transcript_source_tag": VERIFICATION_TRANSCRIPT_SOURCE_TAG,
        "verification_seed_index": deterministic_seed_index(
            point_id=str(point_id),
            layer_id=int(layer_id),
            block_index=int(block_index),
        ),
        "verification_invoked_flag": 1,
        "verification_bits_budgeted": int(tag_bits),
        "verification_bits_used_actual": int(tag_bits),
        "verification_pass_flag": passed,
        "verification_fail_flag": int(1 - passed),
    }
