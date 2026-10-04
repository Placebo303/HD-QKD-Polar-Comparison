"""Production decode adapter for NB-LDPC L1-degree2 Stage-2 (no execution).

Change: ``T5-BLOCKER-7`` production binding. Implementation-only; importing
this module performs no decode, no construction and no writes. The v35
production decoder is bound lazily inside ``production_decode_fn`` so import,
``--help`` and ``--dry-run`` paths never touch it.

Frozen decoder档: row-layered / ``max_iter=90`` / ``damping_alpha=1.0`` /
``warm_beliefs=None`` / CHECK_UPDATED / ``oracle=False`` dual-arm. ``layer``
is accepted and ignored (L1/L2 share the档); it never changes a decode
parameter. The v35 ``DecoderResult`` is returned unmodified: no field
rewrite, no provenance defaulting (a non-CHECK_UPDATED return must still
fail closed downstream in ``d5._run_layered_block``).

``field=None`` follows the accepted production convention
(``d5.historical_g0_decoder``, the ``v72p2d7`` schedule bind): v35 then
builds the pinned GF(32) field internally.
"""
from __future__ import annotations

__all__ = [
    "MAX_ITER",
    "DAMPING_ALPHA",
    "production_decode_fn",
]

#: Frozen Stage-2 decoder档 (mirrors ``d5.MAX_ITER`` / ``d5.DAMPING_ALPHA``).
MAX_ITER = 90
DAMPING_ALPHA = 1.0


def production_decode_fn(h, prior, syndrome, layer=None):
    """Frozen production decode: v35 row-layered, L1/L2 shared档.

    ``layer`` is accepted for the ``_decode_block`` call shape
    (``decode_fn(h, prior, syndrome, layer=...)``) and ignored. Fixed
    binding: ``max_iter=90``, ``damping_alpha=1.0``,
    ``warm_beliefs=None``, ``field=None``. Returns the v35
    ``DecoderResult`` object unmodified.
    """
    _ = layer
    from comparison_bench.formal_ir import v35_algorithm_development as v35
    return v35.decode_row_layered_fftqspa(
        h, prior, syndrome, max_iter=MAX_ITER,
        damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
