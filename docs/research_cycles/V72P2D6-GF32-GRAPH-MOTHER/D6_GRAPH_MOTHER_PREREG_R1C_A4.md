# D6 graph/mother — preregistration R1c-A4 (structure/scaling performance)

Status: `FROZEN_PREREG_R1C_A4`. Starts only after A3 closeout commits
(`9d99d07`). Zero decoder calls in A4 (structure-only). Science
(arms/seeds/rows/prior/decoder/mother math/selection/terminal thresholds)
unchanged; A3 evidence and interpretation untouched (separate commits, never
mixed). Final state `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` or
`PERF_TARGET_NOT_MET`; neither authorizes another run.

## Scope

Allowed: `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
(builder refactor only: split assign, overflow passthrough — no math change),
`scripts/v72p2d6_graph_mother_development.py` (structure-build path only:
`arms` filter, worker using the new builder API — decoder/selection/terminal
paths untouched), `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`
(A4 tests), this prereg + `R1C_parallel_revision.md` A4 delta + A4 report/
review under the D6 cycle dir, append-only memory/log after PASS.

Forbidden: any decoder call (real or fake production path); `--phase`/G1/G2/
VAL/real; T2 builder choice key and search semantics (frozen); `d5` module;
selection/advancement/terminal logic; science parameters; A3 evidence files;
broad-stage/clean/reset/push.

## A4-01 profile first (structure-only, fresh dev-only roots)

Bounded profiler (task-owned temp script, workspace-only): one instrumented
parallel pass per width (`workers=18`, production setting) recording per
`(arm,layer)`: support build, coefficient assign, replay builds, overflow
diagnostic, `audit_prefix`, `audit_extra` (girth/cycle/rank), task wall;
plus pool makespan, startup/serialization overhead, peak RSS. Width totals
cross-checked against the frozen command-log makespans (n64 29.0 s, n128
451.4 s, n256 7845.0 s). Freeze a machine-readable baseline table before any
optimization, separately exposing: support/mother construction; determinism
replay; prefix audits/girth/cycle/rank; n64 initial work; n128/n256
scaling-only work; pool overhead. No decoder, Model-F payload, or scientific
output root.

## A4-02 three optimizations (smallest scientifically equivalent set)

O1 — scaling-arm pruning: `build_structures` / `build_structures_parallel`
take `arms=None` (None = all 8, frozen default; old call sites
byte-identical). Scaling branch (n128/n256) passes only the frozen fallback
arms (`best_T`/`best_M` parameter, never hardcoded); n64 keeps all 8 for
selection. `structure_records.csv` at scaling widths therefore contains
fallback arms only (packet-ordered); n64 file shape unchanged;
`selected_arms.json` identical.

O2 — at most two support constructions per `(n,arm,layer)`: split
`build_mother` into `build_support` + pure `_assign_mother_from_support`
(same math, same outputs); worker does primary support → H from that exact
support → one independent support replay → H2 from replayed support →
equality on both arrays. Current path builds support 3× (+1 overflow
rebuild for T3/T4, see O3); new path builds 2× with the same determinism
guarantee (array equality on support AND H, not weakened).

O3 — no repeated audits: SC overflow is returned from the primary
`_build_SC_support` (it already counts it) via new
`build_support_with_overflow`; old `build_support` stays a thin wrapper
(unchanged signature/behavior). The worker reuses the primary overflow and
the separate `support_window_overflow` rebuild is deleted from the worker
path. Prefix-dependent metrics stay once-per-`(H,prefix)`, locked by a
call-count regression test (no `d5` changes).

T2: builder untouched (choice key + search semantics frozen). Pruning removes
T2 from scaling dispatch only; n64 T2 work is unchanged. No T2 speed work
unless the profile shows T2-n64 material to n64 selection — it cannot affect
the scaling wall either way.

## A4-03 equivalence gates (reference path kept until gates pass)

Old-vs-optimized comparison: all 8 arms × 2 layers at n64 (support, H,
structure records, eligibility, structural ordering, selected/fallback arms,
terminal inputs — exact equality); every scaling-reachable (fallback) arm at
n128/n256 (same set). Timing never excuses a changed scalar. New tests fail
if: a non-fallback arm is built during scaling; T2 is built at n128/n256
when not a frozen fallback; support/H replay equality is weakened (arrays
must equal AND overflow must equal); any audit is recomputed unnecessarily
(call-count); sequential and parallel paths differ; pool worker-count, RSS,
wall, or call-budget behavior changes (same pool size; structure phase makes
zero decoder calls by construction).

## A4-04 benchmark acceptance (fresh structure-only roots, ≤3 h total)

Scaling wall = sum of parallel makespans (`workers=18`) for n128+n256 —
the exact scaling-branch calls. Before-cold = frozen A4-01 runs;
before-warm + after-cold + after-warm run in A4-04 (fresh roots each).
Acceptance (all required): scaling wall improves ≥3× (cold and warm
reported separately); n64 outputs exactly equal and n64 wall regresses ≤10%;
peak aggregate RSS < 2 GiB; focused + seven-file non-perf regressions pass;
production decoder calls exactly zero (no decoder records written anywhere).
No omitted work on either side. If any gate fails, return
`PERF_TARGET_NOT_MET` with profile evidence instead of a speedup claim.

## A4-05 deliverables + commits + stop rules

Deliverables: this prereg/OpenSpec delta; machine-readable baseline/after
table (fresh dev-only root); `D6_GRAPH_MOTHER_PERFORMANCE_R1C_A4.md`;
independent `D6_GRAPH_MOTHER_PERFORMANCE_REVIEW_R1C_A4.md`. Commits (scoped,
no push): (1) prereg/OpenSpec; (2) implementation+tests; (3) benchmark
evidence/report; (4) independent review (+ memory/log appends after PASS).
Any production-code test failure → STOP (no mixed-version evidence).
Ambiguity → STOP, return to main thread. Final state READY or NOT_MET; no
execution authorization requested or granted.
