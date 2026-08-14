from __future__ import annotations

import zlib

import numpy as np


def bits_to_bytes(bits: np.ndarray) -> bytes:
    arr = np.asarray(bits, dtype=np.uint8).reshape(-1)
    if arr.size == 0:
        return b""
    pad = (-arr.size) % 8
    if pad:
        arr = np.concatenate([arr, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(arr).tobytes()


def crc32_bits(bits: np.ndarray) -> int:
    return int(zlib.crc32(bits_to_bytes(bits)) & 0xFFFFFFFF)
