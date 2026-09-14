# Proposal — V72P2D10 R3 fresh-graph scaling replication (readiness, R301)

Change: `v72p2d10-r3-fresh-graph-scaling`
Cycle: `V72P2D10-MIXED-DEGREE-L1` (successor replication; NOT an R2 correction)
Track: implementation/readiness (no EXPLORE/DECIDE execution; zero scientific
  decoder calls; no `--r3-batch`, no L2/APP, no D7-H, no real data, no
  commit/push).
Branch: `formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).
Authority (read fully first): `.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md`
  (§1–§4 frozen), `AGENTS.md` §1.2/§3/§5/§10.1.
Predecessor reuse baseline (read, do not modify):
  `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/design.md` +
  spec (R2 amendment), `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  (R2 constructor/decoder path), `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/EXPLORATION_LOG.md`
  (A1 evidence).
A1 (immutable, read-only context only): root
  `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` with
  stored terminal `D10_L1_AMBIGUOUS`, reviewed `VERIFIED PASS`. No rerun, no
  threshold change. A1 records are contextual only and never pooled into R3
  gates. A1 artifacts SHALL NOT be modified by this change.

## Goal

Resolve the identified graph-variance versus scaling ambiguity: does the D10
mixed-degree L1 advantage reproduce across fresh n128 graphs, and if so persist
at n256? This change freezes the complete R3 successor-replication contract
(two arms, exact degree tables, fresh seeds, shared connectivity-first
constructor + A1–A6 unchanged, coefficient rule, Model-F root, decoder
contract, 144-calls/width conditional plan, frozen `R3_REPRODUCED` /
`R3_NEGATIVE` / `R3_AMBIGUOUS` gates, six terminals, future root, budgets,
claim ceiling) BEFORE any behavior edit, so R302–R310 can implement readiness
with zero scientific decoder calls.

## Non-goals (hard prohibitions)

- No scientific decoder call in this change or any R301–R310 readiness step
  (zero `--r3-batch`, zero L2/APP execution, zero D7-H revival, zero real-data
  contact).
- No rerun, modification, re-thresholding, or pooling of A1 evidence; A1 stays
  contextual-only.
- No seed search, replacement, repair, resume, retry, or adaptation; fresh
  seeds are never searched or replaced.
- No L2, APP transfer, oracle-L2, FER/leakage/SKR/qualification/promotion/
  publication/real-data claim; claim ceiling is L1-only synthetic.
- No modification of R2/A1 code, tests, roots, results, `AGENTS.md`, or
  decision-log; no commit or push; no future-root creation in readiness.
- This change grants NO execution; the future batch still needs separate
  explicit authorization naming batch/branch/root/seeds/budgets.

## Impact scope

- ADDED: `openspec/changes/v72p2d10-r3-fresh-graph-scaling/` only
  (`proposal.md`, `design.md`, `tasks.md`, `specs/r3-fresh-graph-scaling/spec.md`).
- READ-ONLY references: R3 packet §1–§4; R2 design + spec; R2 constructor/
  decoder path; A1 exploration log; A1 root (context only).
- FORBIDDEN: all code/scripts/tests/roots/results/A1 artifacts/`AGENTS.md`/
  decision-log. A NEW additive change is used (preferred): R3 is a successor
  replication, not an R2 correction — the existing D10 change is NOT amended.

## Frozen successor design (packet §2, transcribed exactly)

Preserve from accepted R2/A1: two arms and exact n128/n256 degree tables;
connectivity-first shared constructor and A1–A6; coefficient rule; Model-F
CAL-only prior; GF32/poly37; decoder max_iter 90/damping 1.0/cold; f1.2 rows;
paired exact/syndrome separation; no-overwrite; claim ceiling.

- Two arms: `PEG_DV3_MATCHED` vs `PEG_DV23_LAM2_045`.
- Degree tables (from R1 READINESS; R2 design §3 cross-check):
  - DV3 n128: m=118, E=384, `3^88+4^30`; DV3 n256: m=236, E=768, `3^176+4^60`;
  - MIX n128: n2=71, n3=57, E=313, `2^41+3^77`;
    MIX n256: n2=141, n3=115, E=627, `2^81+3^155`.
- Shared connectivity-first constructor `build_degree_sequence_peg` + A1–A6
  unchanged; `--execution-authorized` pattern retained for the future runner.
- Coefficient rule: `v10_seed(f"d10:coeff:{width}:{graph_seed}")`.
- Model-F root: `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only prior).
- Field GF32/poly37; decoder `max_iter=90`, `damping=1.0`, cold; f1.2 rows;
  paired exact/syndrome separation (`exact` primary; syndrome-valid reported
  separately, never substitutes); no-overwrite.
- Claim ceiling: L1-only synthetic; no FER/leakage/SKR/real-data/L2/D7-H.

Fresh primary seeds, never searched or replaced:

- n128 graph seeds `2026092401..2026092406`;
- n256 graph seeds `2026092501..2026092506`;
- n128 block seeds `2026092601..2026092612`;
- n256 block seeds `2026092701..2026092712`.

Seed-absence scan (recorded; no collision — STOP condition not triggered):

- Command (regex search over repo): pattern
  `20260924(01|02|03|04|05|06)|20260925(01|02|03|04|05|06)|20260926(0[1-9]|1[0-2])|20260927(0[1-9]|1[0-2])|d10_r3_fresh_graph_scaling_4d39ed0e`
  plus prefix scans `20260924|20260925|20260926|20260927` and
  `d10_r3_fresh_graph_scaling|4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`.
- Raw result: matches ONLY in the authority packet itself
  (`.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md`
  lines 25–28, 61); zero matches in code/scripts/tests/docs/openspec/
  analysis/results/workspace. Future root
  `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
  verified absent (no directory; no literal string outside the packet).

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
`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
(verified absent; STOP if present — absent confirmed).
Budgets: ≤288 scientific calls, ≤50 setup units (=24 graph builds + 24
width-block samples + Model-F load + plan build), wall ≤1800 s, ≤120 s/call,
RSS <2147483648 B, one process, no retry/resume/repair/seed
search/adaptation.

## Acceptance criteria (R301)

- New change exists with `proposal.md`, `design.md`, `tasks.md`,
  `specs/r3-fresh-graph-scaling/spec.md`; existing D10 change untouched.
- All frozen items above transcribed packet-exact (arms, tables, constructor/
  A1–A6, coeff rule, Model-F root, decoder, seeds, 144→conditional-288 plan,
  6-clause gate verbatim, NEGATIVE/AMBIGUOUS rules, McNemar-descriptive note,
  six terminals verbatim, future root, budgets, A1 non-pooling, claim ceiling).
- Seed/root absence scan recorded with raw output; no collision (else BLOCKED).
- `tasks.md`: R301 marked `[x]`, R302–R310 in packet-exact wording marked `[ ]`.
- Only `openspec/changes/v72p2d10-r3-fresh-graph-scaling/**` written; zero
  decoder calls; no commit/push.
