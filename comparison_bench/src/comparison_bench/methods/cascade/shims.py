"""Compatibility aliases — deprecated cascade identities -> single_kernel."""
from __future__ import annotations

import warnings

from .single_kernel import run_cascade_single
from .config import CascadeSingleConfig

__all__ = ["run_cascade_lite_shim", "run_cascade_formal_shim", "CascadeLite", "CascadeFormal"]


def _warn(name: str) -> None:
    warnings.warn(f"{name} is deprecated — use cascade_single (use cascade_single)", DeprecationWarning, stacklevel=3)


def run_cascade_lite_shim(*args, **kwargs):
    _warn("cascade_lite")
    from ..cascade_lite import run_cascade_lite  # shim already delegates to single_kernel

    return run_cascade_lite(*args, **kwargs)


def run_cascade_formal_shim(*args, **kwargs):
    _warn("cascade_formal_v1")
    from ..cascade_formal import run_cascade_formal

    return run_cascade_formal(*args, **kwargs)


# Class aliases for legacy imports that expect a class
CascadeLite = run_cascade_lite_shim  # type: ignore
CascadeFormal = run_cascade_formal_shim  # type: ignore
