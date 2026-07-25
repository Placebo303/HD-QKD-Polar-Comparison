from __future__ import annotations

import math

import numpy as np


def bits_per_symbol(dimension: int) -> int:
    q = int(dimension)
    if q <= 1:
        raise ValueError("dimension must be greater than 1")
    bps = int(math.ceil(math.log2(q)))
    if 2**bps != q:
        raise ValueError("bit mapping currently requires power-of-two dimension")
    return bps


def gray_encode(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.int64)
    return np.bitwise_xor(arr, np.right_shift(arr, 1))


def symbols_to_bits(symbols: np.ndarray, dimension: int, mapping: str = "gray") -> np.ndarray:
    bps = bits_per_symbol(dimension)
    vals = np.asarray(symbols, dtype=np.int64)
    if np.any(vals < 0) or np.any(vals >= int(dimension)):
        raise ValueError("symbols out of range for dimension")
    mapped = gray_encode(vals) if str(mapping).lower() == "gray" else vals
    powers = np.arange(bps - 1, -1, -1, dtype=np.int64)
    return ((mapped[..., None] >> powers) & 1).astype(np.uint8)


def flatten_bits(symbols: np.ndarray, dimension: int, mapping: str = "gray") -> np.ndarray:
    return symbols_to_bits(symbols, dimension, mapping).reshape(-1).astype(np.uint8)


def frame_symbol_error_rate(alice: np.ndarray, bob: np.ndarray) -> float:
    a = np.asarray(alice).reshape(-1)
    b = np.asarray(bob).reshape(-1)
    n = min(a.size, b.size)
    if n == 0:
        return float("nan")
    return float(np.mean(a[:n] != b[:n]))


def bit_error_rate(alice_bits: np.ndarray, bob_bits: np.ndarray) -> float:
    a = np.asarray(alice_bits, dtype=np.uint8).reshape(-1)
    b = np.asarray(bob_bits, dtype=np.uint8).reshape(-1)
    n = min(a.size, b.size)
    if n == 0:
        return float("nan")
    return float(np.mean(a[:n] != b[:n]))
