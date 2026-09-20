from __future__ import annotations

import sys


def install_timetagger_alias():
    """Register the PyPI `Swabian.TimeTagger` module as top-level `TimeTagger`.

    The frozen loader `src/qkd_io/ttbin_pipeline.py:148` uses verbatim
    `from TimeTagger import FileReader` (vendor Windows-driver layout), while
    the PyPI `Swabian-TimeTagger` wheel provides only `Swabian.TimeTagger`.
    Registering `sys.modules['TimeTagger']` makes that import resolve without
    touching the frozen file. Idempotent: returns the already-registered module
    if present.
    """
    existing = sys.modules.get("TimeTagger")
    if existing is not None:
        return existing
    from Swabian import TimeTagger as _tt

    sys.modules["TimeTagger"] = _tt
    return _tt
