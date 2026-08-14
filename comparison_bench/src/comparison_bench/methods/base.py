from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import FrameBatch, IRRunConfig, IRRunResult


class IRMethod(ABC):
    @abstractmethod
    def run(self, batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
        raise NotImplementedError
