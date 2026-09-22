"""Cascade common helpers — shared FIFO/Toeplitz transcript invariants (single-kernel frozen).

DESIGN_FROZEN §1: formal state machine is sole correction logic; this module
re-exports shared helpers so path contract `cascade_common.py` is satisfied.
Actual loop lives in single_kernel.py (single-file core).
"""
from __future__ import annotations

from ...formal_ir.shared import toeplitz_tag, transcript_summary, seed_record, locked_seed_bits

__all__ = ["toeplitz_tag", "transcript_summary", "seed_record", "locked_seed_bits"]
