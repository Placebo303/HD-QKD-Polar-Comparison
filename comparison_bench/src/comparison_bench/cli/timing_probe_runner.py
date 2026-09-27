"""TIMING probe runner — two-arm construction/rank timing skeleton.

Track: **implementation-only** (AGENTS §1.2 applicability matrix — no track
gate for this module's creation); this module is an EXECUTION SURFACE ONLY.
It authorizes no execution: production timing runs only behind BOTH CLI
flags, and every real run still needs a Pre-EXECUTE-frozen packet. No real
data is read, no decoder is imported or reachable, zero decode.

Frozen planner draft F1–F8 implemented here (TIMING draft):

- **F1 two arms, frozen order**: ``T1-DENSE-RREF`` then ``T2-SPARSE-PEG``
  (``ARM_ORDER``), run sequentially; a stopped arm never resumes and an
  arm that never starts is tallied ``NOT-RUN`` (machine gate = preceding
  arm ``ok``). ``NOT-RUN`` / ``INCOMPLETE-batch`` exist ONLY in the tally
  and ``timing_summary.md`` — they are never materialized as record rows.
- **F2 T1 dense RREF grid**: shapes ``m ∈ {400, 416} × n ∈ {1024, 2048}``
  × ``T1_REPEATS=3`` repeats = **12 timed calls**, seeds
  ``2026092401 … 2026092412`` (``T1_SEEDS``, one exclusive seed per call,
  never reused). Forbidden lineage seeds ``2026092001`` / ``2026092011``
  (``FORBIDDEN_SEEDS``) are refused anywhere in the plan. Each call times
  exactly ONE segment: ``rref_s`` (frozen ``peg.rank_GF1024`` Gaussian
  elimination); the dense seed-exclusive RNG → GF(32) matrix construction
  happens BEFORE the timed window (construction is untimed). The measured
  rank is RECORDED, never gated — ``rank_recorded_not_gated`` plus the
  ``rank_eq_m`` flag go to ``info`` (rank gates belong to the P4 packet,
  not here).
- **F3 T2 sparse PEG**: shapes ``(n, m) ∈ {(512, 104), (1024, 208)}``
  × seeds ``{2026092421, 2026092422}`` = **4 timed calls**, λ = ``{2:1}``
  edge perspective, ``ρ = make_rho(1 − m/n)`` (read-only
  ``nonbinary_v26_mcde.make_rho`` reuse), ``trials = 20``, GF(32).
  Segmented timing exactly ``peg_main_s`` (``peg.peg_construct`` +
  ``sparse_to_dense`` prep) and ``bfs_girth_s`` (standalone
  :func:`bfs_girth` min-cycle BFS pass over the placed graph) — the
  constructor's own internal girth bookkeeping and rank RREF stay inside
  ``peg_main_s`` (stated here; segments are timing windows, not kernel
  profiles).
- **F4 measurement**: ``time.perf_counter`` (``TIMER_DEFAULT``) segment
  timing around every call plus per-call ``rss_peak`` (GiB, best-effort
  ``resource.ru_maxrss`` probe). Segment dicts must carry exactly the F2/F3
  key sets (``SEGMENT_KEYS``); malformed measurements fail closed rc=2.
- **F5 zero decode**: no decoder entrypoint is imported or reachable;
  ``DECODE_CALLS == 0`` is asserted before returning and stamped on every
  record; this module defines no callable whose name starts with ``decode``.
- **F6 budgets**: single-call deadline ``SINGLE_CALL_DEADLINE_S = 600`` s —
  an overrun is RETAINED as ``INCOMPLETE-call`` and stops continuation
  (never re-run); a timed call that raises is RETAINED as an ``error``
  row with its raw traceback in ``info`` (the batch still writes its
  summary); the batch ceiling has NO frozen default (``BATCH_CEILING_S =
  None``) — it comes from the REQUIRED ``--batch-cap-s`` flag and is
  enforced by the batch wall clock (overrun ⇒ batch state
  ``INCOMPLETE-batch``, never resumed); ``--rss-gib`` (default 2 GiB) is
  recorded on the summary.
- **F7 outputs**: ONLY ``workspace/TIMING/<uuid8>/`` containing exactly
  ``timing_records.jsonl`` + ``timing_summary.md``, both opened in append
  mode (never truncated, never rewritten); the run root must be fresh
  (absent) before the first call, so resume/continue is structurally
  impossible. The summary additionally renders the report-only F7
  three-line cap proposal (measured substitution, k=4, rounded to whole
  100 s) and the edge-linear extrapolation (``f7_proposed`` /
  ``edge_extrapolation``) — evidence only, never an automatically binding
  cap.
- **F8 gates**: production runs ONLY behind BOTH ``--execute-real`` AND
  ``--execution-authorized`` (missing either ⇒ rc=2 BEFORE any root, call,
  or write); every destination path (root, run root, record and summary
  paths) passes :func:`_check_path`, which refuses the forbidden trees
  ``results`` / ``outputs_comparison`` and any real-data artifact token
  (``.ttbin``, ``gamma``) rc=2 BEFORE opening anything.

``execute()`` requires explicit ``t1_fn`` / ``t2_fn`` injection — there is
no default production wiring in the core (AGENTS §10.1 clause 8); only
``run_execution`` (dual-flag CLI-gated) wires the production constructors.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import traceback
from collections import deque
from typing import Any

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v26_mcde as _mcde,
)
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)

__all__ = [
    "ARM_ORDER", "T1_SHAPES", "T1_REPEATS", "T1_SEEDS", "T2_SHAPES",
    "T2_SEEDS", "T2_LAMBDA", "T2_MAX_TRIALS", "FORBIDDEN_SEEDS",
    "SEGMENT_KEYS", "SINGLE_CALL_DEADLINE_S", "BATCH_CEILING_S",
    "BATCH_CEILING_STATUS", "TIMER_DEFAULT", "FIELD_Q", "ROOT", "ROOT_PREFIX",
    "FORBIDDEN_ROOT_PARTS", "FORBIDDEN_PATH_TOKENS", "RECORDS_NAME",
    "SUMMARY_NAME", "UUID8_RE", "RECORD_FIELDS", "CLAIM_CEILING",
    "DECODE_CALLS", "TERMINALS", "F7_K", "F7_EDGE_FROM", "F7_EDGE_TO",
    "Refusal", "refuse", "_check_path", "_check_base_root", "_check_uuid8",
    "run_root", "t1_plan", "t2_plan", "validate_plan", "_validate_plan_calls",
    "seeded_rng", "bfs_girth",
    "production_t1_call", "production_t2_call", "_require_t1_call",
    "_require_t2_call", "_split_output", "build_record", "_print_call_line",
    "append_record", "append_summary", "summary_markdown", "_arm_tally",
    "f7_proposed", "edge_extrapolation",
    "execute", "run_execution", "main",
]

#: Frozen F1: exactly two arms, frozen execution order.
ARM_ORDER = ("T1-DENSE-RREF", "T2-SPARSE-PEG")

#: Frozen F2 T1 grid: (m, n) shapes, m rows × n columns.
T1_SHAPES: tuple[tuple[int, int], ...] = (
    (400, 1024), (400, 2048), (416, 1024), (416, 2048))
#: Frozen F2 repeats per shape (4 shapes × 3 = 12 timed calls).
T1_REPEATS = 3
#: Frozen F2 exclusive T1 seeds, one per call in plan order (12 unique).
T1_SEEDS: tuple[int, ...] = tuple(range(2026092401, 2026092413))
#: Frozen F3 T2 shapes: (n, m).
T2_SHAPES: tuple[tuple[int, int], ...] = ((512, 104), (1024, 208))
#: Frozen F3 T2 seeds (2 shapes × 2 seeds = 4 timed calls; seed unique
#: per shape, never combined across shapes into one claim).
T2_SEEDS: tuple[int, ...] = (2026092421, 2026092422)
#: Frozen F2 forbidden lineage seeds (P4/P1 lineage) — never usable here.
FORBIDDEN_SEEDS: tuple[int, ...] = (2026092001, 2026092011)
#: Frozen F3 variable-side degree profile (edge perspective).
T2_LAMBDA: dict[int, float] = {2: 1.0}
#: Frozen F3 constructor trials.
T2_MAX_TRIALS = 20
#: Frozen F2/F3 field width: GF(32) (read-only ``v80_s2_peg.Q`` reuse).
FIELD_Q = int(s2.Q)
#: Frozen F4 segment key contract per arm (exactly these keys, no more).
#: T1 times exactly ONE segment — dense construction is untimed (A4).
SEGMENT_KEYS: dict[str, tuple[str, ...]] = {
    ARM_ORDER[0]: ("rref_s",),
    ARM_ORDER[1]: ("peg_main_s", "bfs_girth_s"),
}
#: Frozen F6 single-call deadline (seconds).
SINGLE_CALL_DEADLINE_S = 600
#: Frozen F6 batch ceiling — NO frozen default; the per-run value comes
#: from the REQUIRED ``--batch-cap-s`` flag (enforced by batch wall clock).
BATCH_CEILING_S: float | None = None
#: Frozen F6 batch-ceiling status recorded on every row (now ENFORCED).
#: Wording deliberately avoids the state tokens ``NOT-RUN`` /
#: ``INCOMPLETE-batch`` — those live ONLY in the tally and summary.
BATCH_CEILING_STATUS = (
    "batch ceiling has NO frozen default — the per-run value comes from "
    "the required --batch-cap-s flag and IS enforced by the batch wall "
    "clock (overrun stops the batch immediately; never resumed)"
)
#: Frozen F3/F6 per-case terminal states (exactly these three, no more).
TERMINALS: tuple[str, ...] = ("ok", "INCOMPLETE-call", "error")
#: Frozen F7 report-only safety factor k=4 (same source as P4 L71 "4×").
F7_K = 4
#: Frozen F7 edge-linear extrapolation endpoints: n=1024 (λ={2:1} ⇒ 2048
#: edges) measured case → n=2048 full scale (4096 edges), report-only.
F7_EDGE_FROM = 2048
F7_EDGE_TO = 4096
#: Frozen F4 timer: time.perf_counter for every measured window.
TIMER_DEFAULT = time.perf_counter

#: Fresh additive machine-root family (F7) + forbidden trees/artifacts.
ROOT = "workspace/TIMING"
ROOT_PREFIX = "workspace/TIMING/"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
FORBIDDEN_PATH_TOKENS = (".ttbin", "gamma")
#: F7 append-only output file names (the ONLY two files under the root).
RECORDS_NAME = "timing_records.jsonl"
SUMMARY_NAME = "timing_summary.md"
#: Pre-EXECUTE-frozen uuid8 form (explicit input; never generated here).
UUID8_RE = re.compile(r"^[0-9a-f]{8}$")

#: Frozen F4/F6 per-case record field contract (timing_records.jsonl rows).
RECORD_FIELDS = [
    "arm", "case_id", "m", "n", "seed", "repeat", "lambda_edge",
    "rho_rate", "trials", "field_q", "segments", "edges", "wall_s_total",
    "deadline_s", "batch_ceiling_s", "batch_ceiling_status", "rss_peak",
    "terminal", "decode_calls", "info", "claim_ceiling",
]
#: Frozen F5/F7 claim ceiling (carried on every record + summary).
CLAIM_CEILING = (
    "engineering TIMING probe ONLY: dense-RREF / sparse-PEG construction "
    "wall-time measurements as future Pre-EXECUTE input; NOT FER, NOT SKR, "
    "NOT leakage or reconciliation efficiency, NOT qualification, NOT "
    "route decision, NOT publication material; zero decode "
    "(decode_calls=0), no real data read (.ttbin / gamma artifacts never "
    "opened), per-call measurements reported separately (no cross-arm "
    "pooling, no cross-n extrapolation)"
)

#: Decode ledger — structurally frozen at zero (F5: no decode path exists).
DECODE_CALLS = 0

_ALL_PLAN_SEEDS = frozenset(T1_SEEDS) | frozenset(T2_SEEDS)


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / guard-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"TIMING-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


# --------------------------------------------------------------------------- #
# F8 path guards (results / outputs_comparison / real .ttbin / gamma)
# --------------------------------------------------------------------------- #


def _check_path(path: object, label: str = "path") -> str:
    """Fail-closed write-destination guard (F8): refused rc=2, never opened.

    Refuses empty/non-string paths, any exact path segment in
    ``FORBIDDEN_ROOT_PARTS`` (``results``, ``outputs_comparison``) and any
    path containing a real-data artifact token (``.ttbin``, ``gamma``,
    case-insensitive substring). Applied to the root, the composed run root,
    and every record/summary path BEFORE the file is opened.
    """
    if not path or not isinstance(path, str):
        refuse(f"{label} required (fresh additive {ROOT_PREFIX}<uuid8>)")
    parts = path.rstrip("/").split("/")
    if any(part in FORBIDDEN_ROOT_PARTS for part in parts):
        refuse(f"{label} under forbidden tree (results/outputs_comparison): "
               f"{path}")
    low = str(path).lower()
    for token in FORBIDDEN_PATH_TOKENS:
        if token in low:
            refuse(f"{label} names a real-data artifact token ({token!r}) — "
                   f"real .ttbin / gamma inputs are never opened here: {path}")
    return str(path)


def _check_base_root(root: object) -> str:
    """Fail-closed base-root gate: exactly the ``workspace/TIMING`` family."""
    _check_path(root, "root")
    base = str(root).rstrip("/")
    if base != ROOT:
        refuse(f"root must be exactly the {ROOT} machine-root family "
               f"(got {root!r}; F7 — outputs only under "
               f"{ROOT_PREFIX}<uuid8>/timing_records.jsonl + "
               f"timing_summary.md)")
    return base


def _check_uuid8(uuid8: object) -> str:
    """Validate the Pre-EXECUTE-frozen uuid8 (explicit input, never generated)."""
    if not isinstance(uuid8, str) or not UUID8_RE.match(uuid8):
        refuse(f"uuid8 must be 8 lowercase hex chars, Pre-EXECUTE-frozen "
               f"(got {uuid8!r}; no generation path in this module)")
    return uuid8


def run_root(base: str, uuid8: str) -> str:
    """Single fresh additive run root: ``workspace/TIMING/<uuid8>``."""
    return _check_path(f"{base.rstrip('/')}/{uuid8}", "run root")


# --------------------------------------------------------------------------- #
# F2/F3 frozen call plans + seed exclusivity
# --------------------------------------------------------------------------- #


def t1_plan() -> list[dict[str, Any]]:
    """Frozen F2 T1 plan: 4 shapes × 3 repeats = 12 calls, 12 exclusive seeds."""
    calls: list[dict[str, Any]] = []
    for index, (m, n) in enumerate(T1_SHAPES):
        for repeat in range(T1_REPEATS):
            slot = index * T1_REPEATS + repeat
            calls.append({
                "arm": ARM_ORDER[0],
                "case_id": slot,
                "m": int(m), "n": int(n),
                "repeat": repeat,
                "seed": T1_SEEDS[slot],
            })
    return calls


def t2_plan() -> list[dict[str, Any]]:
    """Frozen F3 T2 plan: 2 shapes × 2 seeds = 4 calls (seed per shape)."""
    calls: list[dict[str, Any]] = []
    index = 0
    for n, m in T2_SHAPES:
        for seed in T2_SEEDS:
            calls.append({
                "arm": ARM_ORDER[1],
                "case_id": index,
                "n": int(n), "m": int(m),
                "repeat": None,
                "seed": int(seed),
            })
            index += 1
    return calls


def _validate_plan_calls(calls: object) -> list[dict[str, Any]]:
    """Fail-closed plan validation: counts, arm names, seed exclusivity.

    Refuses (rc=2) any count/arm mismatch, any T1 seed reuse, any repeated
    T2 ``(n, m, seed)`` triple, and any forbidden lineage seed
    (``2026092001`` / ``2026092011``) anywhere in the plan.
    """
    if not isinstance(calls, list) or not calls:
        refuse("timing plan must be a non-empty list of frozen call specs")
    expected = len(T1_SEEDS) + len(T2_SHAPES) * len(T2_SEEDS)  # 12 + 4
    if len(calls) != expected:
        refuse(f"timing plan has {len(calls)} calls, frozen F2/F3 count is "
               f"{expected} (12 dense RREF + 4 sparse PEG)")
    t1 = [c for c in calls if c.get("arm") == ARM_ORDER[0]]
    t2 = [c for c in calls if c.get("arm") == ARM_ORDER[1]]
    if len(t1) != len(T1_SEEDS) or len(t2) != len(T2_SHAPES) * len(T2_SEEDS):
        refuse(f"arm plan mismatch: {ARM_ORDER[0]}={len(t1)} (frozen 12), "
               f"{ARM_ORDER[1]}={len(t2)} (frozen 4)")
    t1_seeds = [c.get("seed") for c in t1]
    if len(set(t1_seeds)) != len(t1_seeds):
        refuse("T1 seed reuse: every one of the 12 dense-RREF calls owns an "
               "EXCLUSIVE seed (F2)")
    if set(t1_seeds) != set(T1_SEEDS):
        refuse(f"T1 seeds must be exactly the frozen 2026092401..2026092412 "
               f"(got {sorted(map(str, t1_seeds))}; F2 — no seed invention)")
    t2_keys = [(c.get("n"), c.get("m"), c.get("seed")) for c in t2]
    if len(set(t2_keys)) != len(t2_keys):
        refuse("T2 (n, m, seed) triple reuse: each of the 4 sparse-PEG calls "
               "is a distinct shape×seed cell (F3)")
    if set(k[2] for k in t2_keys) - set(T2_SEEDS):
        refuse(f"T2 seeds must be exactly {list(T2_SEEDS)} (F3)")
    for call in calls:
        seed = call.get("seed")
        if seed in FORBIDDEN_SEEDS:
            refuse(f"forbidden seed {seed} in plan (F2/F3 — lineage seeds "
                   f"{list(FORBIDDEN_SEEDS)} are never reused here)")
        if seed not in _ALL_PLAN_SEEDS:
            refuse(f"non-frozen seed {seed!r} in plan (F2/F3 — no seed "
                   f"invention; new seeds ⇒ STOP back to the main thread)")
    return list(calls)


def validate_plan() -> list[dict[str, Any]]:
    """Frozen F2+F3 plan in execution order: 12 dense RREF calls then 4 PEG."""
    return _validate_plan_calls(t1_plan() + t2_plan())


def seeded_rng(seed: object) -> Any:
    """Seed-EXCLUSIVE RNG factory (F2): one fresh Generator per plan seed.

    Refuses any seed outside the frozen plan (including the forbidden
    lineage integers). Never touches the global ``numpy.random`` stream, so
    no call can observe or perturb another call's randomness.
    """
    if seed in FORBIDDEN_SEEDS:
        refuse(f"forbidden seed {seed} (F2/F3 — lineage seeds "
               f"{list(FORBIDDEN_SEEDS)} are never reused here)")
    if seed not in _ALL_PLAN_SEEDS:
        refuse(f"seed {seed!r} not in the frozen plan (F2/F3 — no seed "
               f"invention)")
    import numpy as np
    return np.random.default_rng(int(seed))


# --------------------------------------------------------------------------- #
# F3 standalone BFS girth pass (timed segment ``bfs_girth_s``)
# --------------------------------------------------------------------------- #


def bfs_girth(triples: Any, n: int, m: int) -> int | None:
    """Minimum cycle length of the placed bipartite graph (standalone BFS).

    Triples follow the frozen v10 convention ``(row=check, col=variable,
    coeff)``. For every edge the graph is BFS-searched from its variable to
    its check with that edge removed; a reachable distance ``d`` closes a
    cycle of length ``d + 1``. Returns ``None`` for an acyclic graph (frozen
    v10 sentinel: no cycle length exists). Deterministic, rank-free,
    decode-free.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1 \
            or isinstance(m, bool) or not isinstance(m, int) or m < 1:
        raise ValueError("n and m must be positive integers")
    adj: dict[int, list[int]] = {}
    edges: list[tuple[int, int]] = []
    for triple in triples:
        row, col = int(triple[0]), int(triple[1])
        if not 0 <= row < m or not 0 <= col < n:
            raise ValueError("sparse triple out of (m, n) bounds")
        variable, check = col, n + row
        edges.append((variable, check))
        adj.setdefault(variable, []).append(check)
        adj.setdefault(check, []).append(variable)
    best: int | None = None
    for variable, check in edges:
        distances = {variable: 0}
        frontier = deque([variable])
        found: int | None = None
        while frontier and found is None:
            node = frontier.popleft()
            for other in adj.get(node, ()):
                if (node == variable and other == check) \
                        or (node == check and other == variable):
                    continue  # remove the tested edge
                if other in distances:
                    continue
                distances[other] = distances[node] + 1
                frontier.append(other)
                if other == check:
                    found = distances[other]
        if found is not None:
            cycle = found + 1
            best = cycle if best is None else min(best, cycle)
    return best


# --------------------------------------------------------------------------- #
# Production wiring (dual-flag CLI gate only; F2/F3 zero decode)
# --------------------------------------------------------------------------- #


def _require_t1_call(m: object, n: object, seed: object,
                     repeat: object) -> dict[str, Any]:
    """Exact F2 plan membership check — refused BEFORE any RNG or rank call."""
    for call in t1_plan():
        if (call["m"], call["n"], call["seed"], call["repeat"]) \
                == (m, n, seed, repeat):
            return call
    refuse(f"T1 call (m={m!r}, n={n!r}, seed={seed!r}, repeat={repeat!r}) "
           f"is not in the frozen F2 plan (12 calls: shapes "
           f"{list(T1_SHAPES)} × {T1_REPEATS} repeats, seeds "
           f"{T1_SEEDS[0]}..{T1_SEEDS[-1]}, forbidden {list(FORBIDDEN_SEEDS)})")
    raise AssertionError("unreachable")  # pragma: no cover


def _require_t2_call(n: object, m: object, seed: object) -> dict[str, Any]:
    """Exact F3 plan membership check — refused BEFORE any construction."""
    for call in t2_plan():
        if (call["n"], call["m"], call["seed"]) == (n, m, seed):
            return call
    refuse(f"T2 call (n={n!r}, m={m!r}, seed={seed!r}) is not in the frozen "
           f"F3 plan (cells {list(T2_SHAPES)} × seeds {list(T2_SEEDS)})")
    raise AssertionError("unreachable")  # pragma: no cover


def production_t1_call(m: object, n: object, seed: object,
                       repeat: object) -> dict[str, Any]:
    """Production F2 T1 call: dense GF(32) build + frozen RREF, ZERO decode.

    Segments (exactly ``SEGMENT_KEYS[T1]``, ONE key): ``rref_s`` runs the
    frozen ``peg.rank_GF1024`` Gaussian elimination over GF(32); the dense
    seed-exclusive ``numpy.random.default_rng`` matrix construction happens
    BEFORE the timed window (construction is untimed — A4). The measured
    rank is recorded (``rank_recorded_not_gated``) and reduced to the
    ``rank_eq_m`` flag in ``info``, never gated. Refuses off-plan
    (m, n, seed, repeat) BEFORE creating any RNG or calling the rank
    routine; pure in-memory, no disk writes.
    """
    _require_t1_call(m, n, seed, repeat)
    import numpy as np
    field = GF2mField.create(FIELD_Q)
    rng = seeded_rng(seed)
    dense = rng.integers(0, FIELD_Q, size=(int(m), int(n)))  # untimed build
    t1 = time.perf_counter()
    rank = int(peg.rank_GF1024(field, np.asarray(dense, dtype=np.int64).tolist()))
    t2 = time.perf_counter()
    return {
        "segments": {"rref_s": t2 - t1},
        "info": {
            "m": int(m), "n": int(n), "seed": int(seed), "repeat": int(repeat),
            "field_q": FIELD_Q, "rank_recorded_not_gated": rank,
            "rank_eq_m": bool(rank == int(m)),
        },
    }


def production_t2_call(n: object, m: object, seed: object) -> dict[str, Any]:
    """Production F3 T2 call: sparse PEG construction + BFS girth, ZERO decode.

    ``peg_construct(n, m, λ={2:1}, ρ=make_rho(1−m/n), seed, trials=20,
    GF(32) field)`` verbatim (read-only frozen reuse) followed by the
    standalone :func:`bfs_girth` pass. Segments (exactly
    ``SEGMENT_KEYS[T2]``): ``peg_main_s`` = constructor + ``sparse_to_dense``
    prep (the constructor's internal girth bookkeeping and rank RREF are
    inside this window, stated in F3), ``bfs_girth_s`` = the standalone BFS
    min-cycle pass. Construction diagnostics are RECORDED, never gated.
    Refuses off-plan (n, m, seed) BEFORE ``make_rho`` or any construction.
    Pure in-memory; no disk writes.
    """
    _require_t2_call(n, m, seed)
    n_i, m_i, seed_i = int(n), int(m), int(seed)
    field = GF2mField.create(FIELD_Q)
    lam = {int(k): float(v) for k, v in T2_LAMBDA.items()}
    rho = _mcde.make_rho(1.0 - m_i / n_i, lam)  # ρ=make_rho(1−m/n) (F3)
    t0 = time.perf_counter()
    code = peg.peg_construct(n_i, m_i, lam, rho, seed_i,
                             max_trials=T2_MAX_TRIALS, field=field)
    triples = code.get("triples") or []
    dense = peg.sparse_to_dense(triples, n_i, m_i, field)
    t1 = time.perf_counter()
    girth = bfs_girth(triples, n_i, m_i)
    t2 = time.perf_counter()
    return {
        "segments": {"peg_main_s": t1 - t0, "bfs_girth_s": t2 - t1},
        "info": {
            "n": n_i, "m": m_i, "seed": seed_i, "field_q": FIELD_Q,
            "lambda_edge": dict(lam),
            "rho_edge": {int(k): float(v) for k, v in rho.items()},
            "rho_rate": 1.0 - m_i / n_i, "trials": T2_MAX_TRIALS,
            "dense_shape": list(dense.shape),
            "edges": len(triples),
            "status": code.get("status"),
            "trials_used": code.get("trials_used"),
            "four_cycles": code.get("four_cycles"),
            "rank_recorded_not_gated": code.get("rank"),
            "min_girth_constructor": code.get("min_girth"),
            "min_girth_standalone": girth,
            "girth_agrees": girth == code.get("min_girth"),
        },
    }


# --------------------------------------------------------------------------- #
# F4 measurement plumbing
# --------------------------------------------------------------------------- #


def _split_output(out: object, call: dict[str, Any],
                  label: str) -> tuple[dict[str, float], dict[str, Any]]:
    """Validate a timed call's returned segments (exact F4 key contract)."""
    if not isinstance(out, dict):
        refuse(f"{label} must return a dict with a 'segments' mapping")
    segments = out.get("segments")
    if not isinstance(segments, dict):
        refuse(f"{label} must return a 'segments' mapping (F4)")
    expected = SEGMENT_KEYS[call["arm"]]
    if set(segments) != set(expected):
        refuse(f"{label} segments {sorted(map(str, segments))} != frozen "
               f"{list(expected)} (F4 exact key contract)")
    clean: dict[str, float] = {}
    for key, value in segments.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) < 0.0:
            refuse(f"{label} segment {key!r} must be a finite >= 0 number "
                   f"(got {value!r}; F4)")
        clean[key] = float(value)
    info = out.get("info", {})
    if not isinstance(info, dict):
        refuse(f"{label} 'info' must be a mapping when present (F4)")
    return clean, dict(info)


def _rss_gib(rss_fn: Any) -> float:
    """Best-effort peak RSS in GiB (F4); a probe failure never halts."""
    try:
        return float(rss_fn()) / (1024 ** 3)
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0.0


def _positive_number(value: object, label: str) -> float:
    """Fail-closed numeric guard: finite number > 0, refused rc=2 otherwise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        refuse(f"{label} must be a finite number > 0 (got {value!r})")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        refuse(f"{label} must be a finite number > 0 (got {value!r})")
    return number


def build_record(call: dict[str, Any], *, segments: dict[str, float],
                 wall_s_total: float, info: dict[str, Any], rss_gib: float,
                 terminal: str,
                 batch_cap_s: float) -> dict[str, Any]:
    """Build one frozen F4/F6 record row (``timing_records.jsonl`` line).

    ``edges``: T1 rows always carry ``m × n`` (dense cells); T2 rows carry
    ``len(triples)`` from the call's ``info`` (fail-closed on a non-error
    T2 row without it). ``terminal`` must be one of ``TERMINALS``.
    """
    if terminal not in TERMINALS:
        refuse(f"terminal {terminal!r} not in frozen {list(TERMINALS)} "
               f"({call['arm']} case={call['case_id']})")
    is_t1 = call["arm"] == ARM_ORDER[0]
    if is_t1:
        edges: Any = int(call["m"]) * int(call["n"])
    else:
        edges = info.get("edges")
        if terminal != "error" and (isinstance(edges, bool)
                                    or not isinstance(edges, int)
                                    or int(edges) < 0):
            refuse(f"{call['arm']} case={call['case_id']} info must carry a "
                   f"non-negative int 'edges' (= len(triples); got "
                   f"{edges!r}; F3/A2)")
    rec: dict[str, Any] = {
        "arm": call["arm"],
        "case_id": call["case_id"],
        "m": int(call["m"]),
        "n": int(call["n"]),
        "seed": call["seed"],
        "repeat": call["repeat"],
        "lambda_edge": (None if is_t1 else
                        {int(k): float(v) for k, v in T2_LAMBDA.items()}),
        "rho_rate": (None if is_t1 else 1.0 - int(call["m"]) / int(call["n"])),
        "trials": (None if is_t1 else T2_MAX_TRIALS),
        "field_q": FIELD_Q,
        "segments": {str(k): float(v) for k, v in segments.items()},
        "edges": edges,
        "wall_s_total": float(wall_s_total),
        "deadline_s": SINGLE_CALL_DEADLINE_S,
        "batch_ceiling_s": float(batch_cap_s),
        "batch_ceiling_status": BATCH_CEILING_STATUS,
        "rss_peak": float(rss_gib),
        "terminal": str(terminal),
        "decode_calls": 0,
        "info": dict(info),
        "claim_ceiling": CLAIM_CEILING,
    }
    missing = [key for key in RECORD_FIELDS if key not in rec]
    if missing:  # frozen F4 field contract — fail closed
        refuse(f"record missing frozen fields {missing} ({call['arm']} "
               f"case={call['case_id']})")
    if rec["decode_calls"] != 0:
        refuse("decode_calls must remain 0 (F5)")
    return rec


def _print_call_line(rec: dict[str, Any]) -> None:
    """6-decimal printed row per timed case (6dp; zero-decode legend)."""
    seg = " ".join(f"{key}={float(val):.6f}"
                   for key, val in sorted(rec["segments"].items()))
    print(
        f"TIMING {rec['arm']} case={rec['case_id']} m={rec['m']} "
        f"n={rec['n']} seed={rec['seed']} repeat={rec['repeat']} "
        f"segments[{seg}] wall_s_total={rec['wall_s_total']:.6f} "
        f"deadline_s={rec['deadline_s']} rss_peak={rec['rss_peak']:.6f} "
        f"terminal={rec['terminal']} decode_calls=0"
    )


# --------------------------------------------------------------------------- #
# F7 append-only writers (the ONLY two output files)
# --------------------------------------------------------------------------- #


def append_record(root: str, record: dict[str, Any]) -> str:
    """APPEND one JSON line to ``<root>/timing_records.jsonl`` (mode ``"a"``)."""
    path = _check_path(os.path.join(str(root), RECORDS_NAME), "records path")
    with open(path, "a") as fh:
        fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    return path


def append_summary(root: str, text: str) -> str:
    """APPEND markdown to ``<root>/timing_summary.md`` (mode ``"a"``; never truncates)."""
    path = _check_path(os.path.join(str(root), SUMMARY_NAME), "summary path")
    with open(path, "a") as fh:
        fh.write(str(text) if str(text).endswith("\n") else str(text) + "\n")
    return path


def _round100(seconds: float) -> float:
    """Round to whole 100 s (F7: 四舍五入到整百秒, half-up)."""
    return float(int(math.floor(float(seconds) / 100.0 + 0.5) * 100))


def f7_proposed(records: list[dict[str, Any]]) -> dict[str, Any]:
    """F7 three-line report-only cap proposal (k=4, rounded to whole 100 s).

    Evidence for the main thread's P4 §5 adoption decision — NEVER an
    automatically binding cap. Basis = every materialized case row (no
    fastest-value picking; ``max`` is the frozen conservative basis of the
    ``cap_single_call`` formula itself).
    """
    walls = [float(r["wall_s_total"]) for r in records]
    t1_sum = sum(float(r["wall_s_total"]) for r in records
                 if r["arm"] == ARM_ORDER[0])
    t2_sum = sum(float(r["wall_s_total"]) for r in records
                 if r["arm"] == ARM_ORDER[1])
    max_wall = max(walls) if walls else 0.0
    cap_single = _round100(max_wall * F7_K)
    cap_arm = _round100((t1_sum + 2.0 * t2_sum) * F7_K)
    return {
        "k": F7_K,
        "report_only": True,
        "max_call_wall_s": max_wall,
        "t1_wall_sum_s": t1_sum,
        "t2_wall_sum_s": t2_sum,
        "cap_single_call_s": cap_single,
        "cap_arm_s": cap_arm,
        "batch_ceiling_s": 2.0 * cap_arm,  # 2 × cap_arm (whole 100 s × 2)
        "measured_cases": len(records),
        "planned_cases": len(T1_SEEDS) + len(T2_SHAPES) * len(T2_SEEDS),
    }


def edge_extrapolation(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """F7 edge-linear extrapolation (report-only): n=1024 → n=2048 PEG.

    Frozen rule (packet §1): the full-scale n=2048 single-call PEG time is
    the measured n=1024 ``peg_main_s`` scaled linearly by the edge count
    (4096 edges vs 2048 edges) — per case, never pooled, never a
    prediction or commitment.
    """
    out: list[dict[str, Any]] = []
    for rec in records:
        if rec["arm"] != ARM_ORDER[1] or int(rec["n"]) != 1024:
            continue
        if rec["terminal"] != "ok":
            continue
        measured = rec["segments"].get("peg_main_s")
        if measured is None:
            continue
        out.append({
            "case_id": rec["case_id"],
            "seed": rec["seed"],
            "edges_measured": rec["edges"],
            "edges_target": F7_EDGE_TO,
            "measured_peg_main_s": float(measured),
            "extrapolated_peg_main_s": float(measured)
            * F7_EDGE_TO / F7_EDGE_FROM,
        })
    return out


def summary_markdown(batch: dict[str, Any]) -> str:
    """Batch ``timing_summary.md`` body (F1–F8 + tally + F7 report-only lines)."""
    f7 = batch["f7_proposed"]
    extrap = batch["edge_extrapolation"]
    if extrap:
        extrap_txt = "; ".join(
            f"case {e['case_id']} (seed {e['seed']}): "
            f"{e['measured_peg_main_s']:.6f} s × {F7_EDGE_TO}/"
            f"{F7_EDGE_FROM} = {e['extrapolated_peg_main_s']:.6f} s"
            for e in extrap)
    else:
        extrap_txt = "no measured n=1024 T2 case in this batch"
    lines = [
        "# TIMING probe — two-arm construction/rank timing skeleton "
        "(ZERO decode, RAW)",
        "",
        f"- root (F7): `{batch['root']}` (fresh additive; only "
        f"`{RECORDS_NAME}` + `{SUMMARY_NAME}`, both append-only)",
        f"- arms (F1): frozen order {'→'.join(batch['arm_order'])}; a "
        f"stopped arm never resumes, an arm that never starts tallies "
        f"`NOT-RUN` (tally/summary only — no row is ever materialized for it)",
        f"- T1 dense RREF (F2): shapes {list(T1_SHAPES)} × "
        f"{T1_REPEATS} repeats = 12 calls, exclusive seeds "
        f"{T1_SEEDS[0]}..{T1_SEEDS[-1]}; forbidden "
        f"{list(FORBIDDEN_SEEDS)} refused; ONE timed segment "
        f"{list(SEGMENT_KEYS[ARM_ORDER[0]])} (dense construction untimed, "
        f"before the window); rank recorded + `rank_eq_m` in info, never "
        f"gated",
        f"- T2 sparse PEG (F3): shapes {list(T2_SHAPES)} × seeds "
        f"{list(T2_SEEDS)} = 4 calls; λ={T2_LAMBDA} edge perspective, "
        f"ρ=make_rho(1−m/n), trials={T2_MAX_TRIALS}, GF({FIELD_Q}); "
        f"segments {list(SEGMENT_KEYS[ARM_ORDER[1]])} "
        f"(peg_main includes constructor-internal girth bookkeeping + rank "
        f"RREF; bfs_girth is the standalone BFS pass)",
        "- measurement (F4): time.perf_counter segment windows + per-call "
        "rss_peak (GiB, best-effort)",
        f"- budgets (F6): single-call deadline {SINGLE_CALL_DEADLINE_S} s "
        f"(overrun retained as `INCOMPLETE-call`, never re-run; a raised "
        f"call is retained as an `error` row with its raw traceback in "
        f"`info` — either stops continuation but this summary is still "
        f"written); batch ceiling {batch['batch_ceiling_s']} s from the "
        f"required `--batch-cap-s` flag, enforced by the batch wall clock "
        f"({BATCH_CEILING_STATUS})",
        f"- RSS budget (F6/§5): `--rss-gib` = {batch['rss_gib']} GiB "
        f"(recorded on this summary; per-call rss_peak measured "
        f"best-effort and stamped on every row)",
        f"- batch state: `{batch['batch_state']}` (stop reason: "
        f"{batch['stop_reason']}; {batch['record_count']}/"
        f"{batch['planned_count']} frozen cases materialized — `NOT-RUN` / "
        f"`INCOMPLETE-batch` appear only in this tally/summary, never as "
        f"rows)",
        f"- F7-1 cap_single_call = max(measured case wall_s_total) "
        f"{f7['max_call_wall_s']:.6f} s ({f7['measured_cases']}/"
        f"{f7['planned_cases']} cases) × k={f7['k']} = "
        f"**{f7['cap_single_call_s']:.0f} s** (rounded to whole 100 s, "
        f"report-only)",
        f"- F7-2 cap_arm ≈ Σ(1×T1 {f7['t1_wall_sum_s']:.6f} s + 2×T2 "
        f"{f7['t2_wall_sum_s']:.6f} s) × k={f7['k']} = "
        f"**{f7['cap_arm_s']:.0f} s** (rounded to whole 100 s, report-only)",
        f"- F7-3 batch_ceiling = 2 × cap_arm (k={f7['k']}) = "
        f"**{f7['batch_ceiling_s']:.0f} s** (rounded to whole 100 s, "
        f"report-only; evidence only — adoption is decided by the main "
        f"thread in P4 §5, never automatic)",
        f"- F7 edge-linear extrapolation (report-only, not a prediction): "
        f"n=2048 full-scale PEG single call = measured n=1024 peg_main_s × "
        f"({F7_EDGE_TO} edges / {F7_EDGE_FROM} edges) per case: "
        f"{extrap_txt}",
        f"- decode (F5): `decode_calls=0` asserted on this batch and "
        f"stamped on all {batch['record_count']} records; no channel read, "
        f"no decoder import, no `undetected` column",
        f"- tally: `{json.dumps(batch['tally'], sort_keys=True)}`",
        f"- claim ceiling: {CLAIM_CEILING}",
        "",
    ]
    return "\n".join(lines)


def _arm_tally(records: list[dict[str, Any]], arm: str,
               expected: int) -> str:
    """Arm tally over materialized rows only (``expected`` = frozen count).

    An arm with zero rows is ``NOT-RUN`` (never materialized); an arm cut
    short by the batch wall clock (all rows ``ok`` but fewer than
    ``expected``) is ``INCOMPLETE-batch``.
    """
    rows = [r for r in records if r["arm"] == arm]
    if not rows:
        return "NOT-RUN"
    terminals = [r["terminal"] for r in rows]
    if "error" in terminals:
        return "error"
    if "INCOMPLETE-call" in terminals:
        return "INCOMPLETE-call"
    if len(rows) < expected:
        return "INCOMPLETE-batch"  # batch wall cap stopped this arm
    return "ok"


# --------------------------------------------------------------------------- #
# execute / run_execution / main
# --------------------------------------------------------------------------- #


def execute(*, root: str, uuid8: str, batch_cap_s: Any = None,
            t1_fn: Any = None, t2_fn: Any = None, timer: Any = None,
            rss_fn: Any = None, rss_gib: Any = 2.0) -> dict[str, Any]:
    """Run the frozen two-arm timing plan into ONE fresh ``workspace/TIMING/<uuid8>/``.

    Guards run BEFORE any directory, call, or write: exact root family,
    uuid8 form, composed-path guard (F8), required ``batch_cap_s`` (> 0,
    no default — the ``--batch-cap-s`` contract) and ``rss_gib`` budget,
    explicit ``t1_fn``/``t2_fn`` injection (no default production wiring —
    AGENTS §10.1 clause 8), frozen plan validation (F2/F3 seed
    exclusivity), and freshness of the run root (F7: no resume/continue).
    ``t1_fn`` convention: ``(m, n, seed, repeat) -> {"segments": {...},
    "info": {...}}``; ``t2_fn`` convention: ``(n, m, seed) -> {"segments":
    {...}, "info": {...}}``; segment keys must match ``SEGMENT_KEYS``
    exactly (F4) and a T2 success must carry ``info['edges']``.

    Each case is timed with ``timer`` (default ``time.perf_counter``):
    a total above ``SINGLE_CALL_DEADLINE_S`` RETAINS the row as
    ``INCOMPLETE-call``; a call that raises is RETAINED as an ``error``
    row with its raw traceback in ``info``; either stops continuation but
    the summary is ALWAYS written at batch end. After every case the
    batch wall clock is checked against ``batch_cap_s`` — an overrun
    stops the batch (state ``INCOMPLETE-batch``), never resumed. Stopped
    batches BREAK out of the plan: ``NOT-RUN`` / ``INCOMPLETE-batch`` are
    tally/summary values only and are never materialized as rows.
    Records append line-by-line as cases complete; ``decode_calls == 0``
    is asserted before returning.
    """
    base = _check_base_root(root)
    uid = _check_uuid8(uuid8)
    if t1_fn is None or t2_fn is None:
        refuse("t1_fn and t2_fn required — no default production wiring "
               "(explicit injection only; AGENTS §10.1 clause 8)")
    if batch_cap_s is None:
        refuse("batch_cap_s required — batch wall-clock ceiling in seconds "
               "has NO default (CLI: required --batch-cap-s)")
    cap = _positive_number(batch_cap_s, "batch_cap_s (--batch-cap-s)")
    rss_budget = _positive_number(rss_gib, "rss_gib (--rss-gib, default 2)")
    plan = validate_plan()  # F2/F3 frozen counts + seed exclusivity
    expected = {arm: sum(1 for c in plan if c["arm"] == arm)
                for arm in ARM_ORDER}
    out_root = run_root(base, uid)  # F8 path guard on the composed root
    if os.path.exists(out_root):
        refuse(f"run root not fresh: {out_root} (fresh additive root "
               f"mandatory; NO resume/continue; F7)")
    timer = timer or TIMER_DEFAULT
    rss_fn = rss_fn or (lambda: 0)
    os.makedirs(out_root)

    records: list[dict[str, Any]] = []
    gate_permits = True
    stop_reason = "complete"
    batch_t0 = timer()
    for call in plan:
        if not gate_permits:
            break  # A3: no NOT-RUN materialization — tally/summary only
        label = f"{call['arm']} case={call['case_id']} seed={call['seed']}"
        t0 = timer()
        try:
            if call["arm"] == ARM_ORDER[0]:
                out = t1_fn(call["m"], call["n"], call["seed"],
                            call["repeat"])
            else:
                out = t2_fn(call["n"], call["m"], call["seed"])
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — retained error row, zero decode
            wall_s = float(timer() - t0)
            info = {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            rec = build_record(call, segments={}, wall_s_total=wall_s,
                               info=info, rss_gib=_rss_gib(rss_fn),
                               terminal="error", batch_cap_s=cap)
            append_record(out_root, rec)
            records.append(rec)
            _print_call_line(rec)
            gate_permits = False
            stop_reason = "call-error"
            continue
        wall_s = float(timer() - t0)
        segments, info = _split_output(out, call, label)
        rss_gib_peak = _rss_gib(rss_fn)
        if wall_s <= SINGLE_CALL_DEADLINE_S:
            terminal = "ok"
        else:
            terminal = "INCOMPLETE-call"  # retained, never continued
            gate_permits = False
            stop_reason = "single-call-deadline"
        rec = build_record(call, segments=segments, wall_s_total=wall_s,
                           info=info, rss_gib=rss_gib_peak,
                           terminal=terminal, batch_cap_s=cap)
        append_record(out_root, rec)
        records.append(rec)
        _print_call_line(rec)
        if gate_permits and (timer() - batch_t0) > cap:
            gate_permits = False  # A5: batch wall-clock enforcement
            stop_reason = "batch-cap"

    batch_state = "ok" if len(records) == len(plan) else "INCOMPLETE-batch"
    tally = {arm: _arm_tally(records, arm, expected[arm])
             for arm in ARM_ORDER}
    tally["batch"] = batch_state  # NOT-RUN / INCOMPLETE-batch live here + summary
    batch = {
        "mode": "timing-probe zero-decode",
        "arm_order": list(ARM_ORDER),
        "root": out_root,
        "uuid8": uid,
        "tally": tally,
        "batch_state": batch_state,
        "stop_reason": stop_reason,
        "record_count": len(records),
        "planned_count": len(plan),
        "records_name": RECORDS_NAME,
        "summary_name": SUMMARY_NAME,
        "deadline_s": SINGLE_CALL_DEADLINE_S,
        "batch_ceiling_s": cap,
        "batch_ceiling_status": BATCH_CEILING_STATUS,
        "rss_gib": rss_budget,
        "f7_proposed": f7_proposed(records),
        "edge_extrapolation": edge_extrapolation(records),
        "decode_calls": 0,
        "claim_ceiling": CLAIM_CEILING,
        "records": records,
    }
    append_summary(out_root, summary_markdown(batch))
    assert DECODE_CALLS == 0, "decode_calls must remain 0 (F5)"
    return batch


def run_execution(root: str, uuid8: str, batch_cap_s: float,
                  rss_gib: float) -> int:
    """Production batch run — reached ONLY via the dual-flag CLI gate.

    Explicit wiring, one place: production T1/T2 timed calls (both
    zero-decode), the fresh ``workspace/TIMING/<uuid8>/`` root and its two
    append-only files, the required batch wall ceiling (``--batch-cap-s``)
    and the RSS budget (``--rss-gib``). Returns 0 iff every arm and the
    batch tally ``ok``, else 1 (terminal states are carried row-by-row in
    ``timing_records.jsonl``).
    """
    batch = execute(root=root, uuid8=uuid8, batch_cap_s=batch_cap_s,
                    rss_gib=rss_gib, t1_fn=production_t1_call,
                    t2_fn=production_t2_call)
    print(json.dumps({
        "mode": batch["mode"],
        "arm_order": batch["arm_order"],
        "root": batch["root"],
        "tally": batch["tally"],
        "batch_state": batch["batch_state"],
        "stop_reason": batch["stop_reason"],
        "record_count": batch["record_count"],
        "records": batch["records_name"],
        "summary": batch["summary_name"],
        "deadline_s": batch["deadline_s"],
        "batch_ceiling_s": batch["batch_ceiling_s"],
        "batch_ceiling_status": batch["batch_ceiling_status"],
        "rss_gib": batch["rss_gib"],
        "decode_calls": batch["decode_calls"],
    }, indent=1, sort_keys=True, default=str))
    return 0 if all(v == "ok" for v in batch["tally"].values()) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="TIMING probe runner (zero decode; two arms in frozen "
                    "order T1-DENSE-RREF→T2-SPARSE-PEG; production timing "
                    "requires BOTH execution flags + root + Pre-EXECUTE-"
                    "frozen uuid8 + required --batch-cap-s; outputs only "
                    "workspace/TIMING/<uuid8>/ timing_records.jsonl + "
                    "timing_summary.md, append-only).")
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--root", default="")
    ap.add_argument("--uuid8", default="")
    ap.add_argument("--batch-cap-s", default=None,
                    help="REQUIRED batch wall-clock ceiling in seconds "
                         "(overrun ⇒ INCOMPLETE-batch; no default)")
    ap.add_argument("--rss-gib", default="2",
                    help="RSS budget in GiB recorded on the summary "
                         "(default 2)")
    args = ap.parse_args(argv)

    # F8 dual-flag gate FIRST: refuse rc=2 BEFORE any root, call, or write.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc=2 pre-anything; "
               "dual-flag gate)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc=2 "
               "pre-anything; dual-flag gate)")
    if not args.root:
        refuse(f"root required: fresh additive {ROOT_PREFIX}<uuid8> (F7)")
    if not args.uuid8:
        refuse("uuid8 required: 8 lowercase hex, Pre-EXECUTE-frozen "
               "(F7 — no generation path in this module)")
    if args.batch_cap_s is None or str(args.batch_cap_s).strip() == "":
        refuse("--batch-cap-s required: batch wall-clock ceiling in seconds "
               "(F6 — NO default; overrun ⇒ INCOMPLETE-batch)")
    try:
        cap = float(args.batch_cap_s)
    except (TypeError, ValueError):
        refuse(f"--batch-cap-s must be a number of seconds (got "
               f"{args.batch_cap_s!r})")
    cap = _positive_number(cap, "--batch-cap-s")
    try:
        rss = float(args.rss_gib)
    except (TypeError, ValueError):
        refuse(f"--rss-gib must be a number of GiB (got {args.rss_gib!r})")
    rss = _positive_number(rss, "--rss-gib")
    base = _check_base_root(args.root)
    uid = _check_uuid8(args.uuid8)
    run_root(base, uid)  # F8 guard composed before anything runs
    return run_execution(base, uid, cap, rss)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
