"""Thin Stage-2 batch runner: NB-LDPC L1-degree2 synthetic pairs (no execution).

Change: ``T-coder-1`` implementation-only. One width per invocation
(``--width {128,256}``); the frozen plan is 6 graphs x 2 data seeds x 8
frames = 96 paired samples, dual-arm (control C / candidate S) via
``driver.run_chain_timed``. Both arms run ``oracle=False`` HARDCODED
(``ORACLE_HARDCODED``); this module exposes no oracle switch and never
imports the production decoder. Frame sampling, prior chain, decoder档,
coefficient stream and counting semantics are frozen below; the runner only
assembles them and writes additive outputs under a single fresh
``--out-root``.

Frozen plan reference (hardcoded here so this runner never couples to the
parallel layout-seed edit):

- graph seeds n128 ``2026093701..3706``, n256 ``2026093711..3716``;
- data seeds n128 ``2026093201,2026093202``,
  n256 ``2026093301,2026093302``;
- L2 map n128 ``3701->2801 ... 3706->2806``,
  n256 ``3711->2901 ... 3716->2906`` (shared DV3 L2, one per L1 pair);
- frame stream ``call_seed = v10_seed("nbldpc-l1d2-s2c:{width}:{block_seed}:{frame_idx}")``;
- prior chain (strict D10): ``prepare_model_f_prior_candidate`` ->
  ``sample_matched_block`` -> ``p1`` column ``floor_renorm(DECODER_FLOOR)``
  (``DECODER_FLOOR=1e-15``, column-sum tolerance ``1e-8``, zero-mass
  columns fall back to uniform ``1/32``);
- decoder档: row-layered / ``max_iter=90`` / ``damping=1.0`` / warm None /
  CHECK_UPDATED / ``oracle=False`` dual-arm;
- coefficients ``d10:coeff:{width}:{graph_seed}`` via the accepted ``r2``
  stream (owned by the layout builders, reused here by reference only).

Counting (F-4): frame ``status`` in ``{ok, nonconverged, resource_abort}``
plus build-level ``construction_failed``; ``is_success = pair_exact and
verify_accept and not accepted_wrong`` (``accepted_wrong``/undetected is
isolated, never merged into success; ``resource_abort`` is never success
and never zero-failure; syndrome agreement never substitutes for exact;
failed frames keep full attempted disclosure, no refund). A blocked
transfer (``transfer_invoked=False``) runs no L2 and is recorded as a
non-success ``nonconverged`` frame, never silently skipped.

Execution modes: without ``--execute`` the runner only builds/validates the
plan and exits nonzero (no construction, no decoder, no writes);
``--dry-run`` validates the same plan and exits zero (still no writes);
``--execute --fake-decoder`` runs the full chain with an explicitly
injected fake decoder; ``--execute`` without ``--fake-decoder`` refuses
because the production decoder binding lives in a future packet, not here.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from collections.abc import Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_l1_degree2_driver as driver
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

__all__ = [
    "ORACLE_HARDCODED",
    "GRAPH_SEEDS",
    "DATA_SEEDS",
    "L2_SEED_MAP",
    "DECODER_FLOOR",
    "COLUMN_SUM_TOL",
    "MAX_ITER_DEFAULT",
    "DAMPING_DEFAULT",
    "WALL_CAP_S_DEFAULT",
    "RSS_CAP_BYTES_DEFAULT",
    "CHAIN_WALL_CAP_S_DEFAULT",
    "MODEL_F_ROOT_DEFAULT",
    "FRAME_KEY_COLUMNS",
    "GRAPH_RECORD_COLUMNS",
    "ARM_SUMMARY_COLUMNS",
    "parse_seed_list",
    "parse_frames",
    "parse_bytes",
    "call_seed_for",
    "l2_seed_for",
    "floor_renorm_p1",
    "build_priors",
    "refuse_out_root",
    "build_plan",
    "arm_to_frame",
    "execute_pairs",
    "write_outputs",
    "build_parser",
    "main",
]

#: Both arms are operational-only. Hardcoded; no CLI switch exists.
ORACLE_HARDCODED = False

#: Frozen Stage-2 synthetic graph seeds (6 per width; never searched).
GRAPH_SEEDS = {
    128: (2026093701, 2026093702, 2026093703,
          2026093704, 2026093705, 2026093706),
    256: (2026093711, 2026093712, 2026093713,
          2026093714, 2026093715, 2026093716),
}

#: Frozen Stage-2 data (block) seeds (2 per width).
DATA_SEEDS = {
    128: (2026093201, 2026093202),
    256: (2026093301, 2026093302),
}

#: Frozen L1-graph -> shared-L2-graph map (one shared DV3 L2 per L1 pair).
L2_SEED_MAP = {
    128: {2026093701: 2026092801, 2026093702: 2026092802,
          2026093703: 2026092803, 2026093704: 2026092804,
          2026093705: 2026092805, 2026093706: 2026092806},
    256: {2026093711: 2026092901, 2026093712: 2026092902,
          2026093713: 2026092903, 2026093714: 2026092904,
          2026093715: 2026092905, 2026093716: 2026092906},
}

#: Frozen prior-chain constants (strict D10 chain).
DECODER_FLOOR = 1e-15
COLUMN_SUM_TOL = 1e-8

#: Frozen decoder档 defaults (recorded; bound by the future production
#: adapter, not by this implementation-only module).
MAX_ITER_DEFAULT = 90
DAMPING_DEFAULT = 1.0

#: Frozen budget defaults.
WALL_CAP_S_DEFAULT = 7200.0
RSS_CAP_BYTES_DEFAULT = 4 * 1024 ** 3
CHAIN_WALL_CAP_S_DEFAULT = 120.0
MODEL_F_ROOT_DEFAULT = "workspace/v72p2d5_model_f_input/20260907_r1"

#: Frame CSV leading key columns; the frozen 17 schema columns
#: (``layout.RESULT_SCHEMA_COLUMNS``) follow in frozen order.
FRAME_KEY_COLUMNS = ("width", "arm", "graph_seed", "block_seed",
                     "frame_idx", "call_seed", "transfer_invoked")
#: Graph-record CSV columns (frozen order in this module).
GRAPH_RECORD_COLUMNS = ("width", "graph_seed", "l2_seed", "construction",
                        "attempted_pairs", "control_pair_exact",
                        "candidate_pair_exact", "delta_g", "candidate_leads",
                        "transfer_blocked", "resource_aborts")
#: Arm-summary CSV columns (frozen order in this module).
ARM_SUMMARY_COLUMNS = ("arm", "attempted", "pair_exact", "success",
                       "accepted_wrong", "nonconverged", "resource_abort",
                       "transfer_blocked")


# --------------------------------------------------------------------------- #
# CLI scalar parsers
# --------------------------------------------------------------------------- #
def parse_seed_list(values: Sequence[str] | None) -> list[int]:
    """Flatten repeated ``--*-seed`` values with comma-separated entries."""
    out: list[int] = []
    for value in values or []:
        for piece in str(value).split(","):
            piece = piece.strip()
            if piece:
                out.append(int(piece))
    return out


def parse_frames(spec: str) -> list[int]:
    """Parse a frame spec such as ``0-7`` or ``0,1,2`` (also mixable)."""
    frames: list[int] = []
    for piece in str(spec).split(","):
        piece = piece.strip()
        if not piece:
            continue
        if "-" in piece:
            edges = piece.split("-")
            if len(edges) != 2:
                raise ValueError("bad frame range %r" % (piece,))
            lo, hi = int(edges[0]), int(edges[1])
            if lo < 0 or hi < lo:
                raise ValueError("bad frame range %r" % (piece,))
            frames.extend(range(lo, hi + 1))
        else:
            value = int(piece)
            if value < 0:
                raise ValueError("frame index must be nonnegative")
            frames.append(value)
    ordered = sorted(set(frames))
    if not ordered:
        raise ValueError("frame spec selects no frames")
    return ordered


def parse_bytes(value: str | int) -> int:
    """Parse a byte budget such as ``4294967296``, ``4GiB`` or ``512MiB``."""
    if isinstance(value, bool):
        raise ValueError("byte budget must be an integer or sized string")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("byte budget must be nonnegative")
        return int(value)
    text = str(value).strip()
    upper = text.upper()
    for suffix, factor in (("GIB", 1024 ** 3), ("MIB", 1024 ** 2),
                           ("KIB", 1024), ("GB", 10 ** 9),
                           ("MB", 10 ** 6), ("KB", 10 ** 3)):
        if upper.endswith(suffix):
            return int(float(text[: -len(suffix)]) * factor)
    return int(text)


# --------------------------------------------------------------------------- #
# Frozen stream / seed helpers
# --------------------------------------------------------------------------- #
def call_seed_for(width: int, block_seed: int, frame_idx: int) -> int:
    """Frozen frame stream ``nbldpc-l1d2-s2c:{width}:{block}:{frame}``."""
    return int(common.v10_seed("nbldpc-l1d2-s2c:%d:%d:%d"
                               % (int(width), int(block_seed),
                                  int(frame_idx))))


def l2_seed_for(width: int, graph_seed: int) -> int:
    """Frozen shared-L2 seed for one L1 graph seed."""
    width = int(width)
    if width not in L2_SEED_MAP:
        raise KeyError("unknown Stage-2 width %r" % (width,))
    if int(graph_seed) not in L2_SEED_MAP[width]:
        raise ValueError("graph seed %r outside frozen Stage-2 set for "
                         "width %d" % (graph_seed, width))
    return int(L2_SEED_MAP[width][int(graph_seed)])


def floor_renorm_p1(p1: Any) -> np.ndarray:
    """Column ``floor_renorm`` of a ``P1(U1|B)`` table over the U1 axis.

    Pre-floor columns must sum to 1 within ``COLUMN_SUM_TOL``; zero-mass
    columns fall back to uniform ``1/32`` (same fallback the accepted
    ``marginalize`` helper applies). The per-block floor inside
    ``d5._run_layered_block`` stays the operative decoder feed; this
    pre-floor is the frozen prior-chain step, idempotent with it.
    """
    table = np.asarray(p1, dtype=np.float64)
    if table.ndim != 2 or table.shape[0] != 32:
        raise ValueError("p1 must have shape (32, Bob)")
    if not np.all(np.isfinite(table)) or np.any(table < 0):
        raise ValueError("p1 must be finite and nonnegative")
    col = table.sum(axis=0)
    if np.any(np.abs(col - 1.0) > COLUMN_SUM_TOL):
        raise ValueError("every p1 column must sum to 1 within %g"
                         % (COLUMN_SUM_TOL,))
    floored = np.maximum(table, float(DECODER_FLOOR))
    mass = floored.sum(axis=0, keepdims=True)
    zero = (mass <= 0) | ~np.isfinite(mass)
    out = floored / np.where(zero, 1.0, mass)
    out[:, zero[0]] = 1.0 / 32
    return out


def build_priors(counts_ab: Any, p_b: Any
                 ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Strict D10 prior chain: candidate backoff pair + ``(p1, p2)`` split.

    ``prepare_model_f_prior_candidate`` -> ``marginalize``/``conditionalize``
    with the ``floor_renorm`` step on ``p1``. Injected tables only; no file
    read, no decoder. Returns ``(p_b, p_f, p1_floored, p2)``.
    """
    pb, pf = d5.prepare_model_f_prior_candidate(counts_ab, p_b)
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    return pb, pf, floor_renorm_p1(p1), np.asarray(p2, dtype=np.float64)


# --------------------------------------------------------------------------- #
# Roots
# --------------------------------------------------------------------------- #
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def refuse_out_root(out_root: str | Path, model_f_root: str | Path | None = None,
                    repo_root: str | Path | None = None) -> Path:
    """Refuse protected roots and any existing root; return resolved path.

    Protected: ``results/``, ``comparison_bench/outputs_comparison/`` (exact
    or ancestor match), ``--out-root`` equal to or inside the read-only
    ``model-f-root``, and any path nested inside an already-existing
    ``workspace/`` result root (a fresh ``workspace/<new>`` whose only
    existing ancestor is ``workspace/`` itself is allowed). An existing
    ``--out-root`` is refused (no overwrite, no merge).
    """
    root = Path(repo_root).resolve() if repo_root is not None \
        else _repo_root()
    path = Path(out_root)
    resolved = path.resolve() if path.is_absolute() \
        else (root / path).resolve()
    if resolved.exists():
        raise FileExistsError("refusing to overwrite existing root %s"
                              % (resolved,))
    for subtree in ("results", "comparison_bench/outputs_comparison"):
        anchor = (root / subtree).resolve()
        if resolved == anchor or anchor in resolved.parents:
            raise ValueError("refusing protected root %s" % (resolved,))
    if model_f_root is not None:
        model = Path(model_f_root)
        model_resolved = model.resolve() if model.is_absolute() \
            else (root / model).resolve()
        if resolved == model_resolved \
                or model_resolved in resolved.parents:
            raise ValueError("refusing read-only model-f root %s"
                             % (resolved,))
    workspace = (root / "workspace").resolve()
    if resolved == workspace or workspace in resolved.parents:
        for parent in resolved.parents:
            if parent == workspace:
                break
            if parent.exists():
                raise ValueError(
                    "refusing path inside existing workspace result root "
                    "%s" % (resolved,))
    return resolved


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #
def build_plan(width: int, graph_seeds: Sequence[int],
               data_seeds: Sequence[int], frame_idxs: Sequence[int],
               *, canary: bool = False) -> list[dict[str, Any]]:
    """Frozen paired plan: graph-major, then data seed, then frame.

    ``--canary`` keeps only the minimum graph x minimum data seed (full frame
    list). Requested seeds must lie in the frozen sets; no search, no
    replacement, no reseed.
    """
    width = int(width)
    if width not in GRAPH_SEEDS:
        raise KeyError("unknown Stage-2 width %r" % (width,))
    graphs = [int(s) for s in graph_seeds]
    datas = [int(s) for s in data_seeds]
    frames = [int(f) for f in frame_idxs]
    if not graphs or not datas or not frames:
        raise ValueError("plan needs at least one graph, data seed and frame")
    for seed in graphs:
        if seed not in GRAPH_SEEDS[width]:
            raise ValueError("graph seed %r outside frozen Stage-2 set for "
                             "width %d" % (seed, width))
    for seed in datas:
        if seed not in DATA_SEEDS[width]:
            raise ValueError("data seed %r outside frozen Stage-2 set for "
                             "width %d" % (seed, width))
    if canary:
        graphs, datas = sorted(set(graphs))[:1], sorted(set(datas))[:1]
    plan: list[dict[str, Any]] = []
    for graph_seed in sorted(set(graphs)):
        for block_seed in sorted(set(datas)):
            for frame_idx in sorted(set(frames)):
                plan.append({
                    "width": width, "graph_seed": graph_seed,
                    "block_seed": block_seed, "frame_idx": frame_idx,
                    "l2_seed": l2_seed_for(width, graph_seed),
                    "call_seed": call_seed_for(width, block_seed, frame_idx),
                })
    return plan


# --------------------------------------------------------------------------- #
# Frame mapping (frozen F-4 semantics; no new predicates)
# --------------------------------------------------------------------------- #
def arm_to_frame(arm_out: Mapping[str, Any], *, m1: int, m2: int,
                 rounds: int | None = None, wall_s: float = 0.0,
                 rss_b: int | None = None) -> dict[str, Any]:
    """Map one ``_run_layered_block`` arm output to a frozen frame record.

    Frozen verifier rule: ``verify_accept = syn_l1 and syn_l2`` (syndrome
    agreement is the acceptance signal, never an exactness substitute; a
    syndrome-agreeing wrong word lands in the isolated ``accepted_wrong``
    column). A blocked transfer (``transfer_invoked=False``) forces the L2
    side false and ``status="nonconverged"``: recorded non-success, full
    attempted disclosure, never silently skipped. ``status="ok"`` requires
    an invoked transfer with both syndromes agreeing (an ``accepted_wrong``
    frame is still ``ok``-status but never success, per the layout schema).
    """
    transfer = bool(arm_out.get("transfer_invoked", True))
    u1 = bool(arm_out.get("app_l1_exact", False))
    u2 = bool(arm_out.get("app_l2_exact", False)) and transfer
    s1 = bool(arm_out.get("app_l1_syndrome_ok", False))
    s2 = bool(arm_out.get("app_l2_syndrome_ok", False)) and transfer
    verify = bool(s1 and s2)
    status = "ok" if (transfer and s1 and s2) else "nonconverged"
    disclosure = layout.disclosure_bits(int(m1), int(m2))
    if rounds is None:
        rounds = int(arm_out.get("iterations", 0))
    return layout.classify_frame(
        u1_exact=u1, u2_exact=u2, syn_l1=s1, syn_l2=s2,
        verify_accept=verify, status=status, disclosure=disclosure,
        rounds=int(rounds), wall_s=float(wall_s), rss_b=rss_b)


def abort_frame(*, m1: int, m2: int, rounds: int = 0,
                wall_s: float = 0.0, rss_b: int | None = None
                ) -> dict[str, Any]:
    """Frozen ``resource_abort`` frame: no trust in partial outputs.

    Exact/syndrome/verify flags are forced false (an aborted chain claims
    nothing); attempted disclosure stays on the ledger (no refund).
    ``is_success`` is false by construction.
    """
    disclosure = layout.disclosure_bits(int(m1), int(m2))
    return layout.classify_frame(
        u1_exact=False, u2_exact=False, syn_l1=False, syn_l2=False,
        verify_accept=False, status="resource_abort", disclosure=disclosure,
        rounds=int(rounds), wall_s=float(wall_s), rss_b=rss_b)


# --------------------------------------------------------------------------- #
# Execution (fake-decode capable core; production binding refused here)
# --------------------------------------------------------------------------- #
def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            timeout=10, cwd=str(_repo_root()))
    except Exception:
        return "unknown"
    head = (out.stdout or "").strip()
    return head if out.returncode == 0 and head else "unknown"


def execute_pairs(plan: Sequence[Mapping[str, Any]],
                  h1c: Mapping[int, Any], h1m: Mapping[int, Any],
                  h2: Mapping[int, Any],
                  p1: Any, p2: Any, block_fn,
                  decode_fn, *,
                  chain_wall_cap_s: float = CHAIN_WALL_CAP_S_DEFAULT,
                  wall_cap_s: float = WALL_CAP_S_DEFAULT,
                  rss_cap_bytes: int = RSS_CAP_BYTES_DEFAULT,
                  now=None, rss_fn=None) -> dict[str, Any]:
    """Run the frozen plan with an explicitly injected decoder.

    ``h1c``/``h1m``/``h2`` map ``graph_seed -> dense``; ``block_fn(entry)``
    returns the ``{bob, u1, u2}`` block; ``decode_fn`` must be an explicitly
    injected fake here (production binding is refused by ``run``). Each arm
    is timed as one complete synchronous L1 -> L2 chain. An over-cap chain is
    recorded as ``resource_abort`` and stops the batch before another arm or
    pair starts. Pair elapsed time is recorded separately from the whole
    execute-batch wall time. Global wall/RSS breach also stops the batch with
    completed rows retained (no retry, no resume, no sample/seed change).
    Construction-failed graphs (missing/``None`` dense) emit no frame rows;
    the pair is counted in the graph record only.
    """
    if driver.ORACLE_HARDCODED is not False:
        raise AssertionError("oracle arm is forbidden in Stage-2")
    assert ORACLE_HARDCODED is False, "oracle arm is forbidden in Stage-2"
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected "
                         "(fake-only in this module)")
    now = now or time.perf_counter
    rss_fn = rss_fn or d5._rss_bytes
    p1a = np.asarray(p1)
    p2a = np.asarray(p2)
    calls = {"decode": 0}

    def counting_decode(h, prior, syndrome, layer=None):
        calls["decode"] += 1
        return decode_fn(h, prior, syndrome, layer=layer)

    frame_rows: list[dict[str, Any]] = []
    graph_rows: list[dict[str, Any]] = []
    pair_timings: list[dict[str, Any]] = []
    chains = 0
    stop_reason = ""
    t_batch = float(now())
    entries = list(plan)
    graphs_seen: list[int] = []
    for entry in entries:
        if stop_reason:
            break
        width = int(entry["width"])
        graph_seed = int(entry["graph_seed"])
        if graph_seed not in graphs_seen:
            graphs_seen.append(graph_seed)
        dense_c, dense_m, dense_h2 = (h1c.get(graph_seed),
                                      h1m.get(graph_seed),
                                      h2.get(graph_seed))
        if dense_c is None or dense_m is None or dense_h2 is None:
            continue
        elapsed = float(now()) - t_batch
        rss_now = rss_fn()
        if elapsed >= float(wall_cap_s):
            stop_reason = "wall budget exceeded"
            break
        if rss_now is not None and int(rss_now) >= int(rss_cap_bytes):
            stop_reason = "RSS budget exceeded"
            break
        block = block_fn(entry)
        m1 = int(np.asarray(dense_c).shape[0])
        m2 = int(np.asarray(dense_h2).shape[0])
        # Sampling is inside the execute-batch wall budget. Recheck before
        # starting the first chain in case block creation crossed the cap.
        elapsed = float(now()) - t_batch
        rss_now = rss_fn()
        if elapsed >= float(wall_cap_s):
            stop_reason = "wall budget exceeded"
            break
        if rss_now is not None and int(rss_now) >= int(rss_cap_bytes):
            stop_reason = "RSS budget exceeded"
            break

        pair_started = float(now())
        pair_chains = 0
        for arm_label, h1 in (("CONTROL", np.asarray(dense_c)),
                              ("CANDIDATE", np.asarray(dense_m))):
            # A prior chain or setup work may have reached the batch cap.
            # Check before every decoder invocation so the next chain is never
            # started at or beyond the frozen wall budget.
            elapsed = float(now()) - t_batch
            if elapsed >= float(wall_cap_s):
                stop_reason = "wall budget exceeded"
                break
            arm_out, chain_wall = driver.run_chain_timed(
                counting_decode, h1, np.asarray(dense_h2), p1a, p2a, block,
                on_blocked_transfer="record", now=now)
            chains += 1
            pair_chains += 1
            rss_after = rss_fn()
            over_chain_cap = chain_wall > float(chain_wall_cap_s)
            if over_chain_cap:
                rec = abort_frame(
                    m1=m1, m2=m2,
                    rounds=int(arm_out.get("iterations", 0)),
                    wall_s=chain_wall, rss_b=rss_after)
                stop_reason = "single-chain wall budget exceeded"
            else:
                rec = arm_to_frame(arm_out, m1=m1, m2=m2,
                                   wall_s=chain_wall, rss_b=rss_after)
            frame_rows.append({
                "width": width, "arm": arm_label,
                "graph_seed": graph_seed,
                "block_seed": int(entry["block_seed"]),
                "frame_idx": int(entry["frame_idx"]),
                "call_seed": int(entry["call_seed"]),
                "transfer_invoked": bool(arm_out.get(
                    "transfer_invoked", True)),
                **rec,
            })
            if not stop_reason:
                elapsed = float(now()) - t_batch
                rss_now = rss_fn()
                if elapsed > float(wall_cap_s):
                    stop_reason = "wall budget exceeded"
                elif rss_now is not None \
                        and int(rss_now) >= int(rss_cap_bytes):
                    stop_reason = "RSS budget exceeded"
            if stop_reason:
                break
        pair_wall = max(float(now()) - pair_started, 0.0)
        pair_timings.append({
            "width": width,
            "graph_seed": graph_seed,
            "block_seed": int(entry["block_seed"]),
            "frame_idx": int(entry["frame_idx"]),
            "arms_attempted": ["CONTROL", "CANDIDATE"][:pair_chains],
            "chains_attempted": int(pair_chains),
            "both_arms_attempted": bool(pair_chains == 2),
            "pair_wall_s": float(pair_wall),
        })
    for graph_seed in graphs_seen:
        rows = [r for r in frame_rows if int(r["graph_seed"]) == graph_seed]
        attempted = sum(1 for r in rows if str(r["arm"]) == "CANDIDATE")
        ctrl = [r for r in rows if str(r["arm"]) == "CONTROL"]
        cand = [r for r in rows if str(r["arm"]) == "CANDIDATE"]
        ctrl_exact = sum(1 for r in ctrl if bool(r["pair_exact"])
                         and str(r["status"]) != "resource_abort")
        cand_exact = sum(1 for r in cand if bool(r["pair_exact"])
                         and str(r["status"]) != "resource_abort")
        missing = h1c.get(graph_seed) is None \
            or h1m.get(graph_seed) is None or h2.get(graph_seed) is None
        graph_rows.append({
            "width": int(entries[0]["width"]) if entries else 0,
            "graph_seed": int(graph_seed),
            "l2_seed": int(l2_seed_for(int(entries[0]["width"]),
                                       int(graph_seed)))
            if entries else 0,
            "construction": "construction_failed" if missing else "ok",
            "attempted_pairs": int(attempted),
            "control_pair_exact": int(ctrl_exact),
            "candidate_pair_exact": int(cand_exact),
            "delta_g": int(cand_exact - ctrl_exact),
            "candidate_leads": bool(cand_exact > ctrl_exact),
            "transfer_blocked": int(sum(
                1 for r in rows if not bool(r["transfer_invoked"]))),
            "resource_aborts": int(sum(
                1 for r in rows if str(r["status"]) == "resource_abort")),
        })
    arm_rows: list[dict[str, Any]] = []
    for arm_label in ("CONTROL", "CANDIDATE"):
        rows = [r for r in frame_rows if str(r["arm"]) == arm_label]
        arm_rows.append({
            "arm": arm_label, "attempted": len(rows),
            "pair_exact": int(sum(1 for r in rows if bool(r["pair_exact"]))),
            "success": int(sum(1 for r in rows
                               if layout.is_success(r))),
            "accepted_wrong": int(sum(
                1 for r in rows if bool(r["accepted_wrong"]))),
            "nonconverged": int(sum(
                1 for r in rows if str(r["status"]) == "nonconverged")),
            "resource_abort": int(sum(
                1 for r in rows if str(r["status"]) == "resource_abort")),
            "transfer_blocked": int(sum(
                1 for r in rows if not bool(r["transfer_invoked"]))),
        })
    wall_total = float(now()) - t_batch
    completed_pairs = int(sum(1 for row in pair_timings
                              if bool(row["both_arms_attempted"])))
    return {"frame_rows": frame_rows, "graph_rows": graph_rows,
            "pair_timings": pair_timings,
            "arm_rows": arm_rows, "chains": int(chains),
            "decoder_calls": int(calls["decode"]),
            "planned_pairs": len(entries),
            "completed_pairs": completed_pairs,
            "stop_reason": stop_reason, "wall_s": wall_total}


# --------------------------------------------------------------------------- #
# Outputs (additive under --out-root only; no checksums/atomic/locks)
# --------------------------------------------------------------------------- #
def write_outputs(out_root: str | Path, *, command: str, args: Any,
                  plan: Sequence[Mapping[str, Any]],
                  result: Mapping[str, Any]) -> dict[str, Any]:
    """Write manifest, frame/graph/arm CSVs, command log (+canary) additively."""
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=False)
    manifest = {
        "command": command,
        "module": "comparison_bench.cli.nbldpc_l1d2_synth_batch",
        "width": int(args.width),
        "graph_seeds": [int(s) for s in args.graph_seeds],
        "data_seeds": [int(s) for s in args.data_seeds],
        "frames": [int(f) for f in args.frames],
        "model_f_root": str(args.model_f_root),
        "out_root": str(root),
        "max_iter": int(args.max_iter),
        "damping": float(args.damping),
        "wall_cap_s": float(args.wall_cap_s),
        "rss_cap_bytes": int(args.rss_cap_bytes),
        "chain_wall_cap_s": float(args.chain_wall_cap_s),
        "canary": bool(args.canary),
        "fake_decoder": bool(args.fake_decoder),
        "oracle": ORACLE_HARDCODED,
        "decoder_profile": "row-layered/max_iter=%d/damping=%s/warm=None/"
                           "CHECK_UPDATED/oracle=False dual-arm"
                           % (int(args.max_iter), float(args.damping)),
        "prior_chain": "prepare_model_f_prior_candidate->"
                       "sample_matched_block->p1 floor_renorm(%g)"
                       % (float(DECODER_FLOOR),),
        "column_sum_tol": float(COLUMN_SUM_TOL),
        "frame_stream": "call_seed=v10_seed"
                        "(\"nbldpc-l1d2-s2c:{width}:{block_seed}:{frame_idx}\")",
        "coefficient_stream": "d10:coeff:{width}:{graph_seed} via r2 import",
        "l2_map": {str(g): int(L2_SEED_MAP[int(args.width)][g])
                   for g in args.graph_seeds},
        "counting": "status in {ok,nonconverged,resource_abort} + "
                    "construction_failed; is_success=pair_exact and "
                    "verify_accept and not accepted_wrong; accepted_wrong "
                    "isolated; resource_abort never success; syndrome "
                    "agreement != exact; failed frames full attempted "
                    "disclosure; blocked transfer transfer_invoked=False, "
                    "no L2, recorded non-success",
        "gate": "per-graph delta_g=candidate pair_exact - control "
                "pair_exact; promotion decided by the main thread, never "
                "by this runner",
        "planned_pairs": int(result["planned_pairs"]),
        "pair_timings": list(result.get("pair_timings", [])),
        "chains": int(result["chains"]),
        "decoder_calls": int(result["decoder_calls"]),
        "stop_reason": str(result["stop_reason"]),
        "wall_s": float(result["wall_s"]),
        "git_head_provenance_only": _git_head(),
    }
    with open(root / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    with open(root / "frame_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(FRAME_KEY_COLUMNS)
            + list(layout.RESULT_SCHEMA_COLUMNS))
        writer.writeheader()
        for row in result["frame_rows"]:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
    with open(root / "graph_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(GRAPH_RECORD_COLUMNS))
        writer.writeheader()
        for row in result["graph_rows"]:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
    with open(root / "arm_summary.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ARM_SUMMARY_COLUMNS))
        writer.writeheader()
        for row in result["arm_rows"]:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
    with open(root / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write(command + "\n")
    written = ["manifest.json", "frame_records.csv", "graph_records.csv",
               "arm_summary.csv", "command_log.txt"]
    if bool(args.canary):
        full_pairs = (len(GRAPH_SEEDS[int(args.width)])
                      * len(DATA_SEEDS[int(args.width)])
                      * len(args.frames))
        canary_pairs = len(plan)
        canary_chains = int(result["chains"])
        if canary_pairs and canary_chains:
            projected = float(result["wall_s"]) * (2 * full_pairs) \
                / max(canary_chains, 1)
        else:
            projected = 0.0
        canary_rec = {
            "canary_pairs": int(canary_pairs),
            "canary_chains": int(canary_chains),
            "canary_wall_s": float(result["wall_s"]),
            "full_pairs_projected": int(full_pairs),
            "full_chains_projected": int(2 * full_pairs),
            "projected_wall_s_linear": float(projected),
            "wall_cap_s": float(args.wall_cap_s),
            "within_budget_projected": bool(projected <= float(args.wall_cap_s)),
            "note": "linear projection only; promotion decided by main thread",
        }
        with open(root / "canary.json", "w", encoding="utf-8") as fh:
            json.dump(canary_rec, fh, indent=2, sort_keys=True)
            fh.write("\n")
        written.append("canary.json")
    return {"out_root": str(root), "files": written}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """Stage-2 batch CLI (no oracle switch exists by design)."""
    parser = argparse.ArgumentParser(
        description="Stage-2 NB-LDPC L1-degree2 synthetic batch: 6 graphs x "
                    "2 data seeds x N frames, dual-arm oracle=False "
                    "(explicit --execute required)")
    parser.add_argument("--width", type=int, choices=(128, 256),
                        required=True)
    parser.add_argument("--graph-seed", dest="graph_seed_raw",
                        action="append", default=None, required=True,
                        help="frozen graph seed; repeat or comma-join "
                             "(6 per width)")
    parser.add_argument("--data-seed", dest="data_seed_raw",
                        action="append", default=None, required=True,
                        help="frozen data seed; repeat or comma-join "
                             "(2 per width)")
    parser.add_argument("--frames", type=str, default="0-7",
                        help="frame spec such as 0-7 or 0,1,2")
    parser.add_argument("--model-f-root", type=str,
                        default=MODEL_F_ROOT_DEFAULT)
    parser.add_argument("--out-root", type=str, required=True,
                        help="single fresh output root (must not exist)")
    parser.add_argument("--max-iter", type=int, default=MAX_ITER_DEFAULT)
    parser.add_argument("--damping", type=float, default=DAMPING_DEFAULT)
    parser.add_argument("--wall-cap-s", type=float,
                        default=WALL_CAP_S_DEFAULT)
    parser.add_argument("--rss-cap-bytes", type=parse_bytes,
                        default=RSS_CAP_BYTES_DEFAULT)
    parser.add_argument("--chain-wall-cap-s", type=float,
                        default=CHAIN_WALL_CAP_S_DEFAULT)
    parser.add_argument("--canary", action="store_true",
                        help="minimum graph seed x minimum data seed only, "
                             "with a linear cost projection for the main thread")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate the plan and exit 0 (no writes)")
    parser.add_argument("--fake-decoder", action="store_true",
                        help="allow --execute with an injected fake decoder "
                             "(no production decode)")
    parser.add_argument("--execute", action="store_true",
                        help="explicit execution switch; without it only the "
                             "plan is validated and the runner exits nonzero")
    return parser


def _bind_fake_decoder():
    """No default fake exists: fake decoders are injected by tests only."""
    raise ValueError("fake decoder must be injected by the caller; "
                     "this module ships no default fake")


def run(args: Any, *, decode_fn=None, graphs=None, priors=None,
        block_fn=None, command: str = "") -> dict[str, Any]:
    """Shared plan/execute/write driver (injectable for fake-only tests).

    Production path (``graphs``/``priors``/``block_fn`` all ``None``) builds
    real graphs and the real Model-F prior chain but still requires an
    explicitly injected ``decode_fn``; without one it refuses (the
    production decoder binding lives in a future packet).
    """
    assert ORACLE_HARDCODED is False, "oracle arm is forbidden in Stage-2"
    args.rss_cap_bytes = parse_bytes(args.rss_cap_bytes) \
        if not isinstance(args.rss_cap_bytes, int) \
        else int(args.rss_cap_bytes)
    plan = build_plan(int(args.width), list(args.graph_seeds),
                      list(args.data_seeds), list(args.frames),
                      canary=bool(args.canary))
    resolved_out = refuse_out_root(args.out_root, args.model_f_root)
    if graphs is None or priors is None or block_fn is None:
        if decode_fn is None:
            raise ValueError(
                "decode_fn must be explicitly injected (fake-only in this "
                "module); production decoder binding is unavailable")
        from comparison_bench.formal_ir import v72p2d11_forward_app as d11
        from comparison_bench.formal_ir import v72p2d5_model_f_input as mf
        loaded = mf.load_model_f_input(args.model_f_root)
        _pb, _pf, p1, p2 = build_priors(loaded["counts_ab"], loaded["p_b"])
        h1c, h1m, h2 = {}, {}, {}
        for entry in plan:
            seed = int(entry["graph_seed"])
            if seed in h1c:
                continue
            control = layout.build_control_l1(int(args.width), seed)
            candidate = layout.build_candidate_l1(int(args.width), seed)
            shared = d11.build_l2_graph(int(args.width),
                                        int(entry["l2_seed"]))
            if control.get("dense") is None or candidate.get("dense") is None \
                    or shared.get("dense") is None \
                    or not bool(control.get("admitted")) \
                    or not bool(candidate.get("admitted")) \
                    or not bool(shared.get("admitted")):
                continue
            h1c[seed] = np.asarray(control["dense"])
            h1m[seed] = np.asarray(candidate["dense"])
            h2[seed] = np.asarray(shared["dense"])

        def _block_fn(entry, _pb=_pb, _pf=_pf):
            return d5.sample_matched_block(_pb, _pf, int(args.width),
                                           int(entry["call_seed"]))

        graphs = (h1c, h1m, h2)
        priors = (p1, p2)
        block_fn = _block_fn
    else:
        h1c, h1m, h2 = graphs
        p1, p2 = priors
    result = execute_pairs(plan, h1c, h1m, h2, p1, p2, block_fn, decode_fn,
                           chain_wall_cap_s=float(args.chain_wall_cap_s),
                           wall_cap_s=float(args.wall_cap_s),
                           rss_cap_bytes=int(args.rss_cap_bytes))
    outputs = write_outputs(resolved_out, command=command, args=args,
                            plan=plan, result=result)
    return {"plan": plan, "result": result, "outputs": outputs,
            "out_root": str(resolved_out)}


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Returns the process exit code (no guessing)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.graph_seeds = parse_seed_list(args.graph_seed_raw)
        args.data_seeds = parse_seed_list(args.data_seed_raw)
        args.frames = parse_frames(args.frames)
        args.rss_cap_bytes = parse_bytes(args.rss_cap_bytes) \
            if not isinstance(args.rss_cap_bytes, int) \
            else int(args.rss_cap_bytes)
    except (ValueError, TypeError) as exc:
        print("invalid argument: %s" % (exc,), file=sys.stderr)
        return 2
    command = " ".join(sys.argv) if argv is None else " ".join(
        [sys.executable or "python", "-m",
         "comparison_bench.cli.nbldpc_l1d2_synth_batch"]
        + [str(a) for a in argv])
    try:
        plan = build_plan(int(args.width), list(args.graph_seeds),
                          list(args.data_seeds), list(args.frames),
                          canary=bool(args.canary))
        refuse_out_root(args.out_root, args.model_f_root)
    except (ValueError, KeyError, FileExistsError) as exc:
        print("plan refused: %s" % (exc,), file=sys.stderr)
        return 2
    print("plan: width=%d graphs=%d data=%d frames=%d pairs=%d arms=2 "
          "oracle=False" % (int(args.width), len(set(args.graph_seeds)),
                             len(set(args.data_seeds)), len(args.frames),
                             len(plan)))
    if bool(args.dry_run):
        print("dry-run: plan validated, no execution, no writes")
        return 0
    if not bool(args.execute):
        print("refusing: scientific execution requires --execute "
              "(plan validated, no writes)", file=sys.stderr)
        return 2
    if not bool(args.fake_decoder):
        print("refusing: production decoder binding is unavailable in this "
              "implementation-only module (use --fake-decoder with an "
              "injected fake)", file=sys.stderr)
        return 2
    try:
        _bind_fake_decoder()
    except ValueError as exc:
        print("refusing: %s" % (exc,), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
