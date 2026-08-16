"""V19 CRC helpers matching the frozen CA-SCL C++ CRC check.

The C++ decoder checks that the full K-bit info vector has zero remainder under
CRC-16/CCITT (poly=0x1021, init=0x0000, no reflection, no final xor). We reserve
16 of the K info bits for CRC and choose them so the whole vector passes the check.
"""
from __future__ import annotations

import numpy as np


def crc_check(bits) -> bool:
    """Mirror ``check_crc16`` in src/reconciliation/cpp_polar/main.cpp."""
    reg = 0
    poly = 0x1021
    for bit in bits:
        top = (reg >> 15) & 1
        reg = (reg << 1) & 0xFFFF
        if top ^ int(bit) & 1:
            reg ^= poly
    return reg == 0


def choose_crc16(bits) -> list[int]:
    """Return 16 append bits so that ``bits + append`` passes crc_check.

    The function mirrors the C++ LFSR bit by bit; appended bits are found by
    exhaustive search over the 2^16 choices (small and deterministic).
    """
    values = [int(bit) & 1 for bit in bits]
    for append_value in range(1 << 16):
        reg = 0
        for bit in values:
            top = (reg >> 15) & 1
            reg = (reg << 1) & 0xFFFF
            if top ^ bit:
                reg ^= 0x1021
        append = [(append_value >> i) & 1 for i in range(16)]
        for bit in append:
            top = (reg >> 15) & 1
            reg = (reg << 1) & 0xFFFF
            if top ^ bit:
                reg ^= 0x1021
        if reg == 0:
            return append
    raise RuntimeError("no CRC-16 append found")


def build_crc_info_bits(payload_bits, k: int) -> np.ndarray:
    """Return length-k info bits: payload followed by 16 CRC bits that make the
    full k-bit vector pass crc_check."""
    payload = [int(bit) & 1 for bit in payload_bits]
    if len(payload) != k - 16 or k < 17:
        raise ValueError("payload length must equal k-16 and k>=17")
    crc = choose_crc16(payload)
    out = np.zeros(k, dtype=np.int8)
    out[:len(payload)] = payload
    out[len(payload):] = crc
    assert crc_check(out) is True
    return out
