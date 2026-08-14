from __future__ import annotations

import hashlib

import numpy as np

from ..utils.crc import bits_to_bytes, crc32_bits


def verify_frames_crc32(alice_bits, bob_bits):
    a = np.asarray(alice_bits, dtype=np.uint8)
    b = np.asarray(bob_bits, dtype=np.uint8)
    if a.shape != b.shape:
        raise ValueError("alice_bits and bob_bits must have the same shape")
    if a.ndim == 1:
        a = a.reshape(1, -1)
        b = b.reshape(1, -1)
    return np.asarray([crc32_bits(x) == crc32_bits(y) for x, y in zip(a, b)], dtype=bool)


def _hash_tag(bits: np.ndarray, hash_name: str, truncate_bits: int) -> int:
    h = hashlib.new(hash_name)
    h.update(bits_to_bytes(bits))
    digest = int.from_bytes(h.digest(), "big")
    if truncate_bits <= 0:
        return digest
    shift = max(0, h.digest_size * 8 - int(truncate_bits))
    return digest >> shift


def verify_frames_hash(alice_bits, bob_bits, hash_name: str = "sha256", truncate_bits: int = 32):
    a = np.asarray(alice_bits, dtype=np.uint8)
    b = np.asarray(bob_bits, dtype=np.uint8)
    if a.shape != b.shape:
        raise ValueError("alice_bits and bob_bits must have the same shape")
    if a.ndim == 1:
        a = a.reshape(1, -1)
        b = b.reshape(1, -1)
    return np.asarray([
        _hash_tag(x, hash_name, truncate_bits) == _hash_tag(y, hash_name, truncate_bits)
        for x, y in zip(a, b)
    ], dtype=bool)
