from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass
class FrameBatch:
    dataset_id: str
    alice_symbols: np.ndarray
    bob_symbols: np.ndarray
    dimension: int
    frame_len_symbols: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IRRunConfig:
    method: str
    method_variant: str
    dimension: int
    frame_len_symbols: int
    max_iter: int
    qber_estimate: Optional[float] = None
    ser_estimate: Optional[float] = None
    verify_mode: str = "crc32"
    notes: Optional[str] = None


@dataclass
class IRRunResult:
    dataset_id: str
    method: str
    method_variant: str
    frame_len_symbols: int
    frame_len_bits: int
    n_frames_total: int
    n_frames_attempted: int
    n_frames_success: int
    n_frames_failed_decode: int
    n_frames_failed_verify: int
    raw_ser: float
    raw_ber: float
    post_ir_ser: float
    post_ir_ber: float
    leak_EC_actual_bits: float
    leak_EC_per_frame: float
    leak_EC_per_input_bit: float
    beta_eff_empirical: float
    runtime_s: float
    throughput_input_bits_per_s: float
    throughput_output_bits_per_s: float
    metadata: dict[str, Any] = field(default_factory=dict)
