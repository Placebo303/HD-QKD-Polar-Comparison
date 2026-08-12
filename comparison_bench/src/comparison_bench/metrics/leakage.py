from __future__ import annotations

import math


def estimate_cascade_leak_bits(parity_disclosures: int, verify_bits: int = 32, extra_bits: int = 0) -> float:
    return float(max(0, int(parity_disclosures)) + max(0, int(verify_bits)) + max(0, int(extra_bits)))


def estimate_ldpc_leak_bits(syndrome_bits: int, verify_bits: int = 32, puncture_shortening_bits: int = 0) -> float:
    return float(max(0, int(syndrome_bits)) + max(0, int(verify_bits)) + max(0, int(puncture_shortening_bits)))


def _binary_entropy(p: float) -> float:
    x = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def compute_beta_eff_empirical(leak_bits: float, n_input_bits: int, raw_ber_or_ser: float) -> float:
    n = int(n_input_bits)
    if n <= 0:
        return float("nan")
    h = _binary_entropy(float(raw_ber_or_ser))
    denom = float(n) * h
    if denom <= 0.0 or not math.isfinite(denom):
        return float("nan")
    return float(max(0.0, 1.0 - float(leak_bits) / denom))
