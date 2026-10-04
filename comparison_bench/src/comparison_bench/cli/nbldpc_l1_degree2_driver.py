"""Thin Stage-1 driver: control vs candidate L1 pair assembly (no execution).

Change: ``add-nbldpc-l1-degree2-layout``. Implementation-only; zero
scientific decoder calls. Both arms run ``oracle=False`` HARDCODED
(``ORACLE_HARDCODED``); the CLI exposes no oracle switch and this module
never calls the D11 outer MIX runner (``oracle=True`` upper-bound arm).
``decode_fn`` must be explicitly injected; ``None``/non-callable refuses
before any binding. The production decoder is never imported (no ``v35``
import at module scope; ``d5`` lazy-binds provenance only inside the layered
helper at call time). Stage-1 entrypoint is PROFILE_ONLY graph construction
(no decoder, no root, no writes).
"""
from __future__ import annotations

import argparse
import time
from collections.abc import Mapping
from typing import Any

from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

__all__ = [
    "ORACLE_HARDCODED",
    "require_decode_fn",
    "run_chain",
    "run_chain_timed",
    "run_pair",
    "profile_only",
    "build_parser",
    "main",
]

#: Both arms are operational-only. Hardcoded; no CLI switch exists.
ORACLE_HARDCODED = False


def require_decode_fn(decode_fn) -> Any:
    """Refuse before any binding unless a fake/callable is explicitly given."""
    if decode_fn is None or not callable(decode_fn):
        raise ValueError(
            "decode_fn must be explicitly injected (fake-only in Stage-1); "
            "refusing production-default binding")
    return decode_fn


def run_chain(decode_fn, h1, h2, p1, p2, block: Mapping[str, Any],
              *, on_blocked_transfer: str = "record") -> dict[str, Any]:
    """Run one operational L1 -> L2 chain with ``oracle=False``."""
    require_decode_fn(decode_fn)
    assert ORACLE_HARDCODED is False, "oracle arm is forbidden in Stage-1"
    out = d5._run_layered_block(
        decode_fn, h1, h2, p1, p2, block, ORACLE_HARDCODED,
        on_blocked_transfer=on_blocked_transfer)
    if any(str(k).startswith("oracle_") for k in out):
        raise AssertionError("arm leaked oracle upper-bound keys")
    return out


def run_chain_timed(decode_fn, h1, h2, p1, p2,
                    block: Mapping[str, Any], *,
                    on_blocked_transfer: str = "record", now=None
                    ) -> tuple[dict[str, Any], float]:
    """Run one chain and return its elapsed wall time.

    ``now`` is injectable for deterministic fake-only tests. The timer covers
    the complete synchronous L1 -> L2 layered-block call; it cannot preempt
    that call.
    """
    timer = now if now is not None else time.perf_counter
    t0 = float(timer())
    out = run_chain(decode_fn, h1, h2, p1, p2, block,
                    on_blocked_transfer=on_blocked_transfer)
    elapsed = max(float(timer()) - t0, 0.0)
    return out, elapsed


def run_pair(decode_fn, h1c, h1m, h2, p1, p2, block: Mapping[str, Any],
             *, on_blocked_transfer: str = "record") -> dict[str, Any]:
    """Run one control + one candidate layered block, both ``oracle=False``.

    Shared fixed H2, shared data-frame object interface and shared
    prior/decoder binding; the sole treatment difference is H1. Asserts the
    hardcoded ``oracle=False`` on entry and the absence of any ``oracle_*``
    upper-bound keys on exit. CHECK_UPDATED forward semantics inherited from
    ``d5._run_layered_block`` (fail-closed; blocked transfers recorded, never
    silently skipped).
    """
    out_c = run_chain(decode_fn, h1c, h2, p1, p2, block,
                      on_blocked_transfer=on_blocked_transfer)
    out_m = run_chain(decode_fn, h1m, h2, p1, p2, block,
                      on_blocked_transfer=on_blocked_transfer)
    return {"control": out_c, "candidate": out_m,
            "oracle": ORACLE_HARDCODED,
            "shared_h2": True, "shared_block": True}


def profile_only(width: int, graph_seed: int) -> dict[str, Any]:
    """PROFILE_ONLY pair construction for one frozen seed (no decoder)."""
    width, graph_seed = int(width), int(graph_seed)
    if width not in layout.GRAPH_SEEDS:
        raise KeyError("unknown Stage-1 width %r" % (width,))
    if int(graph_seed) not in layout.GRAPH_SEEDS[width]:
        raise ValueError("graph seed %r outside frozen Stage-1 set for "
                         "width %d" % (graph_seed, width))
    control = layout.build_control_l1(width, graph_seed)
    candidate = layout.build_candidate_l1(width, graph_seed)
    cells = layout.l055_degree_cell(width)
    return {
        "width": width, "graph_seed": int(graph_seed),
        "degree_cell": cells,
        "control": {
            "status": control["status"], "admitted": control["admitted"],
            "E": control["E"],
            "admission": dict(control["structure"]["admission"])
            if control.get("structure") else {},
            "failure_reason": control["failure_reason"],
        },
        "candidate": {
            "status": candidate["status"],
            "admitted": candidate["admitted"],
            "E": candidate["E"],
            "admission": dict(candidate["structure"]["admission"])
            if candidate.get("structure") else {},
            "failure_reason": candidate["failure_reason"],
        },
        "decoder_calls": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    """Stage-1 CLI: PROFILE_ONLY options only (no oracle/batch/execute)."""
    parser = argparse.ArgumentParser(
        description="Stage-1 PROFILE_ONLY: build one frozen control/candidate "
                    "L1 pair (no decoder, no writes)")
    parser.add_argument("--profile-only", action="store_true",
                        help="build the frozen pair and print the admission "
                             "summary (no decoder)")
    parser.add_argument("--width", type=int, choices=list(layout.WIDTHS),
                        default=128)
    parser.add_argument("--graph-seed", type=int, default=None)
    parser.add_argument("--list-cells", action="store_true",
                        help="print the frozen L055 degree cells")
    return parser


def main(argv=None) -> dict[str, Any]:
    """CLI entrypoint (PROFILE_ONLY; refuses scientific execution flags)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_cells:
        return {"cells": {w: layout.l055_degree_cell(w)
                          for w in layout.WIDTHS}}
    if not args.profile_only:
        raise ValueError("Stage-1 driver is PROFILE_ONLY only; pass "
                         "--profile-only (no scientific execution in "
                         "Stage-1)")
    seed = int(args.graph_seed) if args.graph_seed is not None \
        else layout.GRAPH_SEEDS[int(args.width)][0]
    return profile_only(int(args.width), seed)
