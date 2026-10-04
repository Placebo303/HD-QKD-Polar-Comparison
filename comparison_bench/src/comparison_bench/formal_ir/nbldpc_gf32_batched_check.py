"""Local GF(32) check-update variant batching outgoing Walsh transforms."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from .nonbinary_field import GF2mField
from .v35_algorithm_development import fwht_batched


def batched_check_update_log_batch(
    log_messages: Sequence[np.ndarray],
    coefficients: Sequence[int],
    syndrome: int,
    field: GF2mField,
    tables: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> list[np.ndarray]:
    """Compute outgoing check log-messages with one batched inverse FWHT."""
    mul_table, add_table, _ = tables
    q = field.q
    dc = len(log_messages)
    if dc < 2:
        raise ValueError("Check node requires degree >= 2")

    scaled_probs = np.empty((dc, q), dtype=np.float64)
    for j, (msg, coeff) in enumerate(zip(log_messages, coefficients)):
        coeff = int(coeff)
        perm = mul_table[coeff, :]
        scaled_log = np.empty(q, dtype=np.float64)
        scaled_log[perm] = msg
        max_val = np.max(scaled_log)
        exp_m = np.exp(scaled_log - max_val)
        sum_m = np.sum(exp_m)
        if sum_m <= 0 or not np.isfinite(sum_m):
            scaled_probs[j] = np.full(q, 1.0 / q)
        else:
            scaled_probs[j] = np.maximum(exp_m / sum_m, 1e-15)
            scaled_probs[j] /= np.sum(scaled_probs[j])

    spectra = fwht_batched(scaled_probs)

    prefix = np.ones((dc + 1, q), dtype=np.float64)
    suffix = np.ones((dc + 1, q), dtype=np.float64)
    for j in range(dc):
        prefix[j + 1] = prefix[j] * spectra[j]
    for j in range(dc - 1, -1, -1):
        suffix[j] = suffix[j + 1] * spectra[j]

    prod_ext = prefix[:-1] * suffix[1:]
    conv = fwht_batched(prod_ext) / q
    outgoing_logs: list[np.ndarray] = []
    for t in range(dc):
        coeff_t = int(coefficients[t])
        shifted_indices = add_table[syndrome, mul_table[coeff_t, :]]
        out_prob = conv[t, shifted_indices]
        out_prob = np.maximum(out_prob, 1e-15)
        sum_p = np.sum(out_prob)
        if sum_p <= 0 or not np.isfinite(sum_p):
            out_prob = np.full(q, 1.0 / q)
        else:
            out_prob /= sum_p
        outgoing_logs.append(np.log(np.maximum(out_prob, 1e-15)))

    return outgoing_logs
