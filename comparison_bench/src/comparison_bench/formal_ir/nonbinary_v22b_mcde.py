"""V22b structured MC-DE with configurable degree cap (diagnostic).

This is an additive wrapper around the frozen V14 MC-DE.  It temporarily raises
``nonbinary_v14_mcde.DEGREE_MAX`` so that high-rate q=1024 ensembles whose
concentrated check degree exceeds 64 can be evaluated.  No frozen source is
modified.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import nonbinary_v14_mcde as v14

__all__ = ["run_mcde_high_degree"]


def run_mcde_high_degree(q: int, lambda_edge: Mapping[Any, Any],
                         rho_edge: Mapping[Any, Any], *,
                         n_samples: int, max_iter: int, seed: int,
                         channel_mode: str = "structured",
                         p: float | None = None, w: Any | None = None,
                         degree_max: int = 128,
                         entropy_tol: float = 0.01, streak: int = 20) -> dict:
    """Run V14 MC-DE with a temporarily raised degree cap."""
    if int(degree_max) < 64:
        raise ValueError("degree_max must be >= 64")
    old = v14.DEGREE_MAX
    v14.DEGREE_MAX = int(degree_max)
    try:
        return v14.run_mcde(
            q=q, lambda_edge=lambda_edge, rho_edge=rho_edge,
            n_samples=n_samples, max_iter=max_iter, seed=seed,
            channel_mode=channel_mode, p=p, w=w,
            entropy_tol=entropy_tol, streak=streak)
    finally:
        v14.DEGREE_MAX = old
