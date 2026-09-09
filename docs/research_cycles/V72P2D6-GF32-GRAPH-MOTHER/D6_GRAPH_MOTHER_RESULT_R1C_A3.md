# D6 Graph Mother Result R1c-A3 (blocked run; unaccepted, awaiting main thread)

Status: `RESULT_R1C_A3`
Branch: `formal-ir-v72p1-addendum-clean`
Out-root: `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`
(immutable; six-file mtimes unchanged by A3)
Pre-RESULT: `D6_R1C_A3_PRE_RESULT_REVIEW_PASS_BLOCKED_RUN`
Date-UTC: 2026-09-09

## Stored vs recomputed terminal

- Stored (`summary.json`, historical, preserved):
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`.
- Recomputed (A3 rules, governs): `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`
  (`degree-invariant:64`). Agreement: False (fail-closed, honestly reported).
- Confirmation stage: `EMPTY_NOT_EVIDENCE` (0 rows; safety zeros are absence,
  not observation).

## Strongest allowed claim

This run is an **implementation/structure-blocked development attempt**: the
frozen T3_SC_DV3_W4 and M1_ACCUMULATOR_FOREST_MAX graphs admit degree-1
check rows at every dispatched prefix (proven from scalar evidence +
structure-only rebuild with negative controls), so 64 of 184 attempted
decoder calls crash in the check-node invariant before any scientific outcome
exists. The stored topology-no-recovery label is unsupported and must not be
cited as topology evidence.

## What the evidence does and does not support

- Supports: verifier repair validated (15/15 mechanical PASS on the immutable
  root); stage/key accounting reconciles 184/184; crash precedence and
  degree classification work as frozen; canary exact zeros and empty
  advancement reproduce; scaling dispatched exactly the frozen fallbacks at
  both widths with zero end-to-end APP cells.
- Does not support: any recovery/no-recovery topology claim; FER, leakage,
  efficiency, or key-rate numbers; any statement about T2/M2/T4/B-arm
  scientific performance beyond what is tabulated; any reuse of these calls
  for a successor claim.

## Provenance (no new scientific execution in A3)

- Historical execution: single authorized R1c-A2 invocation (authorize
  `85c554ac`, revoke `047e6d62`), 184 scientific + 18 setup calls, tied to
  `15f1de79`. D6 R1c-A2 history not re-run in A3.
- A3 added zero decoder calls (forensics read-only + structure-only builder
  replay; verifier read-only; tests fake-only).
- Reviews: A2 Pre-RESULT FAIL (preserved) → A3 implementation PASS (one
  rework) → A3 Pre-RESULT PASS_BLOCKED_RUN. Full chain in the cycle
  directory.

## Next gate (main-thread route decision; nothing authorized here)

Suggested: main thread decides between (a) a structure-repair successor
proposal (minimum-check-degree gate at build time for all arms/widths —
the audit gap this run exposed), or (b) stop of the T3/M1 line. Either
requires a new OpenSpec change + fresh authorization; this result grants
neither. All authorization keys remain false; G2 absent; result not accepted;
no push.
