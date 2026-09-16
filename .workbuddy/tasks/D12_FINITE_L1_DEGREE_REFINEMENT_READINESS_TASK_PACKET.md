# D12 Finite L1 Degree Refinement — readiness task packet

## 1. Purpose and authority

Track: implementation/readiness only; future batch is `EXPLORE_HEAVY`.
Predecessor: `D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`.

D11 shows that forward APP preserves nearly every mixed-L1 success. The next
limiting variable is L1 exact recovery. Build the smallest finite comparison of
the three already justified D9 degree mixes: λ2=0.45 baseline, 0.50 challenger,
0.55 challenger. Do not reopen a broad grid, change decoder schedule, touch L2,
or run D7-H.

This task authorizes OpenSpec/code/docs, focused fake tests and no-decoder graph
profiling only. Scientific decoder calls remain zero.

## 2. Frozen scientific design

L1-only, f1.2, widths n128 and n256, both always measured. Six fresh graph
seeds and 12 fresh paired block seeds per width:

- n128 graphs `2026093001..06`, blocks `2026093201..12`;
- n256 graphs `2026093101..06`, blocks `2026093301..12`.

Arms and exact node counts from the accepted D9 realization rule:

| width | arm | n2 | n3 | E | checks |
|---|---|---:|---:|---:|---|
| 128 | L045 | 71 | 57 | 313 | `2^41+3^77` |
| 128 | L050 | 77 | 51 | 307 | `2^47+3^71` |
| 128 | L055 | 83 | 45 | 301 | `2^53+3^65` |
| 256 | L045 | 141 | 115 | 627 | `2^81+3^155` |
| 256 | L050 | 154 | 102 | 614 | `2^94+3^142` |
| 256 | L055 | 166 | 90 | 602 | `2^106+3^130` |

Require the accepted shared connectivity-first constructor, A1--A6, coefficient
rule, Model-F CAL-only L1 prior, GF32/poly37 and decoder max_iter=90/damping=1.0/
cold. Only forced degree counts differ. No replacement/search/adaptation.

Plan: 3 arms × 6 graphs × 12 blocks × 2 widths = 432 L1 calls. Exact is
primary; syndrome-valid and undetected remain separate. Report per-graph,
per-width and pooled paired discordances.

An arm is `STABLE(w)` when exact ≥18/72, at least 5/6 graphs have ≥2 exact,
and no engineering/resource violation. L045 is the frozen reference.

A challenger is `MATERIAL_BETTER` only if, at both widths: it is STABLE; exact
is at least L045+6; pooled challenger-only discordance exceeds L045-only; and
it has higher per-graph exact on at least 4/6 graph pairs.

Selection:

- if exactly one challenger is MATERIAL_BETTER, select it;
- if both are, rank by total exact, then worst-width exact, then smaller λ2;
- if neither is and there is no split-width conflict, retain L045;
- `SPLIT_WIDTH_CONFLICT` when a challenger beats L045 by ≥6 at one width but
  trails by >2 at the other, or widths favor opposing challengers.

Terminals: `D12_SELECT_L050`, `D12_SELECT_L055`,
`D12_RETAIN_L045_NO_MATERIAL_GAIN`, `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`, or
an explicit engineering/resource blocked terminal. Descriptive p-values do not
override the frozen selection.

Future root:
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Budgets: ≤432 scientific calls; ≤62 setup (=36 graphs+24 block samples+2);
≤1800 s wall; ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/
repair/seed search/tuning.

Claim ceiling: synthetic finite L1 degree comparison only; no forward/L2,
FER/leakage/SKR, real-data, qualification, optimality or D7-H claim.

## 3. Readiness tasks D1201--D1210

- D1201: create D12 OpenSpec proposal/design/tasks/spec before behavior edits.
- D1202: audit and import D9 exact realization plus D10 R2/R3 construction,
  prior and decoder paths; no duplicate framework or message semantics.
- D1203: implement thin additive plan/runner/verifier with frozen tables, seeds,
  432 identities, gates, ranking and terminals.
- D1204: default-false explicit execution flag; unauthorized refusal before
  root creation, decoder binding or Model-F load.
- D1205: enforce all 36 graphs A1--A6 before decoder binding; zero replacements.
- D1206: never-overwrite minimal root and fail-closed verifier independently
  recomputing identities, metrics, gates/rank and terminal.
- D1207: focused tests for exact tables, seed separation, shared construction,
  all gate/tie/split boundaries, exact/syndrome/undetected isolation, budgets,
  no-write refusal and verifier; decoder entry fake-injected only.
- D1208: `py_compile` plus focused D12 and directly affected D10 tests in a
  fresh workspace basetemp; no broad suite absent focused external failure.
- D1209: PROFILE_ONLY all 36 graphs and full plan; require 36/36 A1--A6,
  deterministic replay, zero replacements/calls and absent future root.
- D1210: one independent reviewer-go readiness review with
  `EVIDENCE_ACCESS: VERIFIED`, recomputing degree math/admission, isolation,
  gates/ranking, budgets and no-production boundary; append one log/readiness
  record and perform memory triage.

## 4. STOP and return

STOP on requirement ambiguity, D9 table mismatch, seed drift, admission failure,
need for replacement/search, decoder/scientific entry, root creation, failed
review or conflicting dirty edits. Do not execute D12, change predecessors,
touch L2/D7-H, commit or push.

Return `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION` only when
D1201--D1210 pass with zero scientific calls and no blocker. Otherwise return
the exact blocker, raw evidence and one decision needed.
