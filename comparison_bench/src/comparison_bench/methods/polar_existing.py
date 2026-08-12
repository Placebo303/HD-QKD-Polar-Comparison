from __future__ import annotations

from ..io.polar_existing_bridge import run_polar_existing
from ..types import FrameBatch, IRRunConfig, IRRunResult
from .base import IRMethod


class PolarExistingMethod(IRMethod):
    def run(self, batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
        return run_polar_existing(batch, cfg)
