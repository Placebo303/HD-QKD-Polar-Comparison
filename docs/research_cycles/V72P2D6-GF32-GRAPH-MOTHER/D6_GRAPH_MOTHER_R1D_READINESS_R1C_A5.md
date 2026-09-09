# D6 graph/mother R1d readiness package R1c-A5

Status: `NOT_AUTHORIZED / REQUIRES_MAIN_THREAD_RULING_AND_AUTHORIZATION`.
This package authorizes nothing: no R1d execution, rerun, resume, `--phase`,
G1/G2, VAL, or real/raw data. No R1d root was created (and none may be
created under this package). All authorization keys remain false;
`evidence_root`/`terminal` remain null (`cycle_state.yaml`).

## Candidate arm set (two branches, main thread rules)

- Branch 1 (repair-or-lift, needs ruling): controls B0/B1 + T1 + whichever
  families the main thread admits via the repair-study menu (Options A/B),
  with the admitted knob lift re-frozen and the validity matrix re-proven
  before any dispatch. T2 enters only with its rank bound recorded (square
  ranks n64 63/62, n128 123/122, n256 246/240) and Track B acceleration
  landed (n256 ~2.85 h/layer breaches the chunk block as-frozen).
- Branch 2 (eligible-only, zero knob change): {B0_D5_DV3_NATIVE,
  B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3} — the only I1-eligible arms at n64.
  The §8.4 fallback pair loses its M leg (no eligible M arm); the D6
  question is unaskable for SC/accumulator families on this branch.
- Forbidden: any reuse of the 184 R1c-A2 calls or the A2 root for a
  successor claim (no-reuse rule); any decoder cell from an I1-violating
  matrix (dispatch guard fails closed); T2 at n128/n256 without the Track B
  numbers; any width whose structure cost breaches the chunk block.

## Validity matrix required before any dispatch

`D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` (144 cells) is the dispatch-time
reference: every dispatched `(arm,n,layer,prefix)` must be frozen-eligible
AND I1-passing in the matrix, re-verified by `--verify` PASS/FAIL on the
fresh root. Post-packet roots recompute every group (no skip set); the
historical-root INFO skip (T2-scaling NOT_RECOMPUTED) never applies to new
roots. Current matrix consequences: T3/T4/M1 dispatchable at f1.0 prefixes
only (structurally ineligible above); M2 dispatchable only at the three
f1.0-L2 cells; T2 square prefixes never dispatchable (rank); B0/B1 bounded
(n128-L2 duplicates, n256 f1.0 disconnection, B0 n256-L1-square rank 255).

## Frozen science carried unchanged

8 arms; seeds by role (canary 2026091000-03, confirmation 2026091010-25,
scaling 2026091100-03); row budgets/prefixes (n64 L1 (49,59,64) /
L2 (43,52,64), x2/x4); E2 prior; historical row-layered FFT-QSPA decoder
(cold start, max_iter=90, damping_alpha=1.0, warm_beliefs=None);
coefficient stream (n,layer,column,edge_index), seeds L1 202609120100+n /
L2 202609120200+n; SC widths 4/8; M N2 rules; two-zone split;
selection/advancement/ordering; terminal thresholds; budgets 2500 calls /
12 h wall / 120 s per-call watchdog / RSS < 2 GiB / no retry.
Decomposition of leakage/E2 accounting, APP-vs-oracle separation, and
syndrome/exact semantics per the frozen specs.

## Evidence-schema change (approval-required, NOT landed)

Persisting `row_degree_min` / `rows_below_degree_2` into
`structure_records.csv` (plus an `eligible`-semantics version marker) is
proposed and requires explicit main-thread approval: the frozen six-file
schema is unchanged in this packet (verified: historical header has neither
column; `--verify` recomputes I1 from builders without touching stored
fields). Landing the columns changes evidence comparability with the A2
root and needs a schema-version ruling first.

## Crash-precedence terminal semantics (landed, R1c-A5)

Any attempted non-placeholder (`call_idx>=0`) crash/nonfinite cell forces
`D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree `ValueError`) or
`D6_GRAPH_ATTEMPTED_CELL_INVALID` (other), overriding recovery/no-recovery
classification; placeholders never count; stored vs recomputed terminals
reported with the agreement flag (recomputed governs). The 64 A2 degree
crashes classify invariant-blocked under this rule.

## No-reuse rule

The 184 R1c-A2 decoder calls (120 clean + 64 attempted degree crashes) and
the A2 six-file root are immutable history (`workspace/
d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`, git-clean, mtimes
intact). No successor claim, selection, advancement, terminal, or benchmark
may cite, import, or recompute-from them as science input; `--verify`
read-only recomputation is the only permitted contact.

## Pre-EXECUTE checklist (all must hold; else no execution)

1. Fresh UUID output root absent (`refuses overwrite`); no formal-root
   default; `assert_no_formal_write` passes.
2. Every authorization key false except an explicit main-thread grant naming
   this package, branch, widths, arms, and budget; G2 absent.
3. Protected-root metadata matches the snapshot (6 files, lengths/mtimes;
   `git status` clean on the path).
4. Focused D6 + seven-file non-perf suites green on the frozen HEAD.
5. Validity matrix + repair ruling recorded; dispatched set ⊆ eligible cells.
6. Exact command frozen (widths, arms, seeds, workers, chunk plan) with stop
   rules (2500 calls / 12 h / 120 s / RSS < 2 GiB / chunk >= 5400 s blocks
   dispatch / no retry).
7. Track B numbers attached for any T2 scaling dispatch (else
   width-inadmissible).

## Claim ceiling

At most: structure-validity closure (I1 proven defect + gate), repair
infeasibility with a ruled menu, and readiness-to-await-ruling. No recovery
claim, no decoder-dynamics claim, no topology claim (stored
`D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` stays unsupported), no performance
claim beyond the measured structure costs, no authorization claim. Reviews
in this packet never authorize execution.
