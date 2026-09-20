"""Leakage accounting and empirical reconciliation-efficiency conventions.

Two related but distinct conventions appear in this repository:

- Efficiency form: ``beta = 1 - leak_bits / (n * H)``, where ``H`` is the
  binary entropy of the raw error rate. This is what
  :func:`compute_beta_eff_empirical` reports.
- Leakage-ratio form: ``leak_bits / (n * H)`` (fraction of the Shannon
  limit disclosed). Some ad-hoc analyses inline the unclamped complement
  ``1.0 - disclosure_sum / (frames * H_FROZEN)`` instead.

Clamp note: :func:`compute_beta_eff_empirical` floors the efficiency at
``0.0`` via ``max(0.0, ...)``. A run that discloses more than the Shannon
limit (raw ``1 - leak/H`` negative, i.e. ``beta < 0``) is therefore reported
as exactly ``0.0`` -- the "beta negative only derived" convention is
unobservable through this function. To diagnose over-disclosure, recompute
the unclamped value ``1.0 - leak_bits / (n * H(raw))`` directly from the
stored leak/error inputs instead of reading it back from ``beta``. The clamp
is deliberately preserved with no additive unclamped key: downstream schema
consumers (``polar_existing_bridge``, the ``*_lite`` methods, the beta-sweep
CLI) consume the bare float return as a ``[0, 1]`` efficiency, so changing
the return shape would break them.
"""
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
