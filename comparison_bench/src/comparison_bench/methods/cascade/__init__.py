from .single_kernel import CascadeSingleKernel, run_cascade_single

# ponytail: compat aliases — deprecated shims forward to single_kernel, kept for backward import
try:
    from ..cascade_lite import run_cascade_lite as _run_cascade_lite  # noqa: F401
    from ..cascade_formal import run_cascade_formal as _run_cascade_formal  # noqa: F401
except Exception:
    _run_cascade_lite = None  # type: ignore
    _run_cascade_formal = None  # type: ignore

# legacy names
cascade_lite = _run_cascade_lite  # deprecated alias
cascade_formal_v1 = _run_cascade_formal  # deprecated alias
run_cascade_lite = _run_cascade_lite  # deprecated alias
run_cascade_formal = _run_cascade_formal  # deprecated alias

__all__ = ["CascadeSingleKernel", "run_cascade_single", "run_cascade_lite", "run_cascade_formal", "cascade_lite", "cascade_formal_v1"]
