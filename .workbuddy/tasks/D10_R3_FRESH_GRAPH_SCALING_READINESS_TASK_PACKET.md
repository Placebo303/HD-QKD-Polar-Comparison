# D10 R3 Fresh-Graph Scaling Replication — readiness task packet

## 1. Purpose and authority

Track: implementation/readiness only; the future scientific batch will be
`EXPLORE_HEAVY`. Accept A1 as immutable
`D10_L1_AMBIGUOUS_RESULT_ACCEPTED_ROUTE_TO_R3_REPLICATION` without rerun or
post-hoc threshold changes. This task authorizes OpenSpec/code/focused fake
tests/no-decoder profiling only. It authorizes zero scientific decoder calls.

Question: does the D10 mixed-degree L1 advantage reproduce across fresh n128
graphs, and if so persist at n256? This resolves the identified graph-variance
versus scaling ambiguity. It is not D7-H: alternation remains out of scope until
wider-width L1 recovery is reproducible.

## 2. Frozen successor design

Preserve from accepted R2/A1: two arms and exact n128/n256 degree tables;
connectivity-first shared constructor and A1--A6; coefficient rule; Model-F
CAL-only prior; GF32/poly37; decoder max_iter 90/damping 1.0/cold; f1.2 rows;
paired exact/syndrome separation; no-overwrite; claim ceiling.

Fresh primary seeds, never searched or replaced:

- n128 graph seeds `2026092401..2026092406`;
- n256 graph seeds `2026092501..2026092506`;
- n128 block seeds `2026092601..2026092612`;
- n256 block seeds `2026092701..2026092712`.

Each width is 2 arms × 6 graphs × 12 paired blocks = 144 calls. Dispatch n128
first. Dispatch n256 only when n128 is `R3_REPRODUCED`. Maximum 288 scientific
calls. A1 records are contextual only and never pooled into R3 gates.

For each graph let `M_g` and `C_g` be MIX and DV3 exact counts from the same 12
blocks. Let `M`, `C` be fresh-width pools (72 each). Exact is primary;
syndrome-valid is reported separately and never substitutes for exact.

`R3_REPRODUCED(w)` iff all hold:

1. `M >= 18`;
2. `M - C >= 12`;
3. MIX wins (`M_g > C_g`) on at least 5 of 6 graph pairs;
4. at least 4 of 6 MIX graphs have `M_g >= 2`;
5. `C <= 6`;
6. no engineering/resource violation.

`R3_NEGATIVE(w)` iff `M <= 6` OR `M - C <= 3`, with no engineering block.
Otherwise `R3_AMBIGUOUS(w)`. Also report paired discordances, exact one-sided
McNemar and intervals descriptively; p-values do not override the frozen gate.

Terminals:

- n128 NEGATIVE → `D10_R3_N128_NOT_REPRODUCED`;
- n128 AMBIGUOUS → `D10_R3_N128_AMBIGUOUS`;
- n128 REPRODUCED then n256 NEGATIVE → `D10_R3_FINITE_WIDTH_DECAY`;
- n128 REPRODUCED then n256 AMBIGUOUS → `D10_R3_N256_AMBIGUOUS`;
- both REPRODUCED → `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`;
- otherwise explicit engineering/resource blocked terminal.

Future root:
`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`.
Budgets: ≤288 scientific calls, ≤50 setup units (=24 graph builds + 24 width-
block samples + Model-F load + plan build), wall ≤1800 s, ≤120 s/call,
RSS <2147483648 B, one process, no retry/resume/repair/seed search/adaptation.

## 3. Readiness work R301--R310

- R301: create/amend OpenSpec before behavior changes; record rationale,
  equations, seeds, gates, terminals and claim ceiling.
- R302: implement the smallest additive R3 plan/runner/verifier, reusing D10 R2
  construction and decoder path rather than copying them.
- R303: make `--r3-batch` require explicit CLI authorization, default false,
  refusing before root creation, decoder binding or Model-F load.
- R304: enforce A1--A6 for all 24 future graphs before decoder binding; any
  failure blocks without seed replacement.
- R305: implement exact call identities, conditional dispatch and frozen gate
  arithmetic; A1 evidence must be impossible to pool into R3.
- R306: write a fresh never-overwrite root with manifest, graph records,
  decoder records, arm/width summaries and command log; verifier fails closed.
- R307: focused tests for seeds/tables, 144→conditional 288 plan, all gate and
  terminal boundaries, exact/syndrome isolation, A1 non-pooling, unauthorized
  no-write/no-bind refusal, A1--A6 block and verifier recomputation.
- R308: `py_compile` plus focused D10/R3 tests in a fresh basetemp. Broad suites
  only if a focused failure identifies an external regression.
- R309: no-decoder PROFILE_ONLY of all 24 future graphs; require 24/24 A1--A6,
  zero replacements, deterministic replay, future root absent.
- R310: one independent readiness review with `EVIDENCE_ACCESS: VERIFIED`,
  independently checking seed separation, graph admission, gates, budgets,
  no-production boundary and reuse rather than duplicate implementation;
  append one readiness record/log and perform memory triage.

## 4. STOP and return

STOP on ambiguity, seed/table drift, any future graph admission failure, need
for seed search, decoder/scientific entry, future-root creation, failed review,
or unrelated dirty-file conflict. Do not run R3, modify A1 evidence, revive
D7-H, commit or push.

Return `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION` only
when R301--R310 pass with zero decoder calls and no review blocker. Otherwise
return the exact blocker with raw evidence and one decision needed. Report
changed files, tests/profile, 24-cell admissions, independent verdict,
authorization/root and commit/push state.
