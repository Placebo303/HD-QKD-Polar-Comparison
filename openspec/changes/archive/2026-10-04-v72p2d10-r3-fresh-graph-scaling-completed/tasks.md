# Tasks — V72P2D10 R3 fresh-graph scaling replication (readiness R301–R310)

Packet: `.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md`
(s sole authority; §1–§4 frozen). Track: implementation/readiness (no
EXPLORE/DECIDE execution; zero scientific decoder calls; no `--r3-batch`, no
L2/APP, no D7-H, no real data, no commit/push). Branch
`formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).
A1 immutable: root `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`,
stored terminal `D10_L1_AMBIGUOUS`, reviewed `VERIFIED PASS` (read-only
context only; no rerun, no threshold change, A1 never pooled into R3).

- [x] R301: create/amend OpenSpec before behavior changes; record rationale,
  equations, seeds, gates, terminals and claim ceiling.
- [x] R302: implement the smallest additive R3 plan/runner/verifier, reusing D10 R2
  construction and decoder path rather than copying them.
- [x] R303: make `--r3-batch` require explicit CLI authorization, default false,
  refusing before root creation, decoder binding or Model-F load.
- [x] R304: enforce A1--A6 for all 24 future graphs before decoder binding; any
  failure blocks without seed replacement.
- [x] R305: implement exact call identities, conditional dispatch and frozen gate
  arithmetic; A1 evidence must be impossible to pool into R3.
- [x] R306: write a fresh never-overwrite root with manifest, graph records,
  decoder records, arm/width summaries and command log; verifier fails closed.
- [x] R307: focused tests for seeds/tables, 144→conditional 288 plan, all gate and
  terminal boundaries, exact/syndrome isolation, A1 non-pooling, unauthorized
  no-write/no-bind refusal, A1--A6 block and verifier recomputation.
- [x] R308: `py_compile` plus focused D10/R3 tests in a fresh basetemp. Broad suites
  only if a focused failure identifies an external regression.
- [x] R309: no-decoder PROFILE_ONLY of all 24 future graphs; require 24/24 A1--A6,
  zero replacements, deterministic replay, future root absent.
- [x] R310: one independent readiness review with `EVIDENCE_ACCESS: VERIFIED`,
  independently checking seed separation, graph admission, gates, budgets,
  no-production boundary and reuse rather than duplicate implementation;
  append one readiness record/log and perform memory triage.

R301 evidence (this task): new additive change
`openspec/changes/v72p2d10-r3-fresh-graph-scaling/` (`proposal.md`,
`design.md`, `tasks.md`, `specs/r3-fresh-graph-scaling/spec.md`); frozen arms
`PEG_DV3_MATCHED` vs `PEG_DV23_LAM2_045`; n128/n256 tables (DV3 n128 m=118
E=384 `3^88+4^30`; DV3 n256 m=236 E=768 `3^176+4^60`; MIX n128 n2=71 n3=57
E=313 `2^41+3^77`; MIX n256 n2=141 n3=115 E=627 `2^81+3^155`); shared
connectivity-first constructor + A1–A6 unchanged; coeff rule
`v10_seed(f"d10:coeff:{width}:{graph_seed}")`; Model-F root
`workspace/v72p2d5_model_f_input/20260907_r1`; GF32/poly37; decoder
max_iter=90/damping=1.0/cold; f1.2 rows; paired exact/syndrome separation;
no-overwrite; claim ceiling (L1-only synthetic; no FER/leakage/SKR/real-data/
L2/D7-H); fresh seeds n128 graphs `2026092401..06`, n256 graphs
`2026092501..06`, n128 blocks `2026092601..12`, n256 blocks `2026092701..12`
(absence-scan recorded in `proposal.md`; no collision); 144 calls/width, n128
first, n256 iff `R3_REPRODUCED(n128)`, max 288; 6-clause `R3_REPRODUCED` gate
verbatim, `R3_NEGATIVE`/`R3_AMBIGUOUS`, McNemar/intervals descriptive only, six
terminals verbatim, future root
`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
(absent verified), budgets ≤288/≤50/1800s/120s/RSS<2147483648/one
process/no-retry-resume-repair-search-adapt; A1 contextual-only non-pooling.
Allowed files: `openspec/changes/v72p2d10-r3-fresh-graph-scaling/**` only.
Zero decoder calls; no commit/push.

Gate: return `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`
only when R301–R310 pass with zero decoder calls and no review blocker
(packet §4). STOP on ambiguity, seed/table drift, any future graph admission
failure, need for seed search, decoder/scientific entry, future-root creation,
failed review, or unrelated dirty-file conflict. Do not run R3, modify A1
evidence, revive D7-H, commit or push.
