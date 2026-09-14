# D10 R3 fresh-graph scaling — readiness record R1 (R301–R310, no execution)

Authority: `.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md` §3 R310
(append one readiness record/log) + §4 return contract.
Track: documentation-only (no code, no execution, no `--r3-batch`, no decoder/scientific
calls, no root creation, no commit/push).
Branch: `formal-ir-v72p1-addendum-clean` (no switch; no commit, no push).

## A1 immutable input (read-only context)

- Root: `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` (unmodified).
- Stored terminal: `D10_L1_AMBIGUOUS`.
- Reviewed: `VERIFIED PASS` (batch-end review, trusted, not rerun).
- Role: contextual only; A1 records never pooled into R3 gates.

## Frozen contract summary (packet §2)

- Arms: `PEG_DV3_MATCHED` vs `PEG_DV23_LAM2_045`; shared connectivity-first
  constructor + A1–A6 unchanged (R2 reuse).
- Tables: DV3 n128 m=118 E=384 `3^88+4^30`; DV3 n256 m=236 E=768 `3^176+4^60`;
  MIX n128 n2=71 n3=57 E=313 `2^41+3^77`; MIX n256 n2=141 n3=115 E=627 `2^81+3^155`.
- Seeds (fresh, never searched/replaced): n128 graphs `2026092401..2026092406`;
  n256 graphs `2026092501..2026092506`; n128 blocks `2026092601..2026092612`;
  n256 blocks `2026092701..2026092712`.
- Coeff rule: `v10_seed(f"d10:coeff:{width}:{graph_seed}")`; Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only prior); GF32/poly37;
  decoder max_iter=90/damping=1.0/cold; f1.2 rows; paired exact/syndrome separation.
- Plan: 144 calls/width (2 arms × 6 graphs × 12 paired blocks), n128 first,
  n256 only iff `R3_REPRODUCED(n128)`; max 288.
- Gates: `R3_REPRODUCED` 6-clause `(18,12,5,4,6)+(6,3)` verbatim;
  `R3_NEGATIVE` / `R3_AMBIGUOUS` edges verbatim; six terminals verbatim;
  McNemar/intervals descriptive only.
- Future root: `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
  (absent before+after).
- Budgets: ≤288 scientific / ≤50 setup / wall ≤1800 s / ≤120 s per call /
  RSS <2147483648 B / one process / no retry/resume/repair/seed search/adaptation.
- Claim ceiling: L1-only synthetic; no FER/leakage/SKR/real-data/L2/D7-H.

## R301–R310 evidence table

| ID | Result | Evidence |
|---|---|---|
| R301 | pass | OpenSpec change `v72p2d10-r3-fresh-graph-scaling` (4 files: proposal/design/tasks/spec). |
| R302 | pass | 3 new additive code files; R2 `build_graph`/decoder path reused, no copy; additive untracked-only footprint. |
| R303 | pass | `--r3-batch` defaults false; refusal precedes root creation, decoder binding, v35 import, Model-F load. |
| R304 | pass | A1–A6 enforced on all 24 future graphs before decoder binding; failure blocks without seed replacement. |
| R305 | pass | Exact call identities (144/width, 288 max, call_idx 0..143/0..287, n128-first), conditional dispatch, frozen gate arithmetic; A1 non-pooling (width-64 records rejected, missing batch_id rejected). |
| R306 | pass | Fresh never-overwrite root with manifest/graph/decoder/arm-width records + command log; verifier fails closed; syndrome never substitutes. |
| R307 | pass | Focused tests (23 tests) covering seeds/tables, plan, gate/terminal boundaries, exact/syndrome isolation, A1 non-pooling, refusal, A1–A6 block, verifier recomputation. |
| R308 | pass | `py_compile` OK; focused D10/R3 tests in fresh basetemp; broad suites deferred per trust rule (no focused failure). |
| R309 | pass | No-decoder PROFILE_ONLY of all 24 future graphs: 24/24 A1–A6, zero replacements, deterministic replay, future root absent (~2.2 s). |
| R310 | pass-with-comments | Independent readiness review, see §R310 below. |

## R310 independent review (trusted VERIFIED, not rerun)

- `REVIEW_ID D10-R3-R310`, `EVIDENCE_ACCESS VERIFIED`, verdict pass-with-comments, no blocking.
- Branch confirmed, no switch/commit/push.
- Seed separation PASS: 48 fresh seeds + UUID only in packet/OpenSpec/R3 code/tests; absent from A1/R1/R2; disjoint from R2 `20260922xx`/`20260923xx`.
- Admission PASS: independent 24/24 A1–A6 recompute with own union-find/Hopcroft-Karp/GF32(37)/replay code (wall 7.07 s, fails []); struct=gf32=m (118/236), comp=1, 0 four-cycles, girth DV3 6/8/10 + MIX 8/10/12; replay identical; zero replacements by construction.
- Gates PASS: 144/width, 288 max, call_idx ranges, n128-first; thresholds verbatim; edge cases verified; six terminals routing verified; n256 gated on REPRODUCED; A1 width-64 rejection and missing batch_id rejection verified; all-syndrome M=6/C=0 → NEGATIVE.
- Budgets PASS (static): 144/288/50/1800/120/2147483648, 1 process, no retry/resume/search/adapt; R303 defaults false, refusal precedes v35 import + Model-F load; future root absent before+after; py_compile OK; full pytest deferred per trust rule (static counts match operator; reviewer ran own gate/plan/admission/budget checks instead; live `--r3-batch` refusal + fresh-basetemp pytest deferred to authorized execution time).
- No-production PASS: no v35 import in R3 module (injected params only, lazy import after gate); v35 absent from sys.modules; zero Model-F load; A1 mtimes unchanged; future root absent.
- Reuse PASS: ARMS/refuse_out_root/decoder constants/Model-F root reused; `build_graph` delegates to R2; degree cells equal R2; no Framework/Factory/Registry; additive untracked-only footprint (581+585+393L); R2/A1 diffs empty.
- Non-blocking: (a) dirty worktree has unrelated mods — any future commit scoped to additive paths only; (b) at authorized execution run deferred live checks once (refusal RC=2 no-write + fresh-basetemp pytest).

## Authorization state

- All authorization flags false; no batch authorization granted.
- Future root absent (verified before+after).
- Decoder calls 0; scientific calls 0.
- No commit, no push.

## Terminal

`D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).

## Next gate / claim boundary

- Next gate: separate explicit batch authorization naming batch/branch/root/seeds/budgets before any R3 execution.
- Claim boundary: readiness only (plan frozen, specified, admission-bounded, mechanically routable). No FER/SKR/qualification/promotion/publication/real-data claim.

## 2026-09-14 — main-thread readiness acceptance

`D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
R301--R310 and independent review `D10-R3-R310` are accepted. The reviewer had
verified artifact access and independently covered seed separation, all 24
graph admissions, gates/terminals, budgets, no-production boundary and R2
reuse; its deferred live refusal/pytest checks are correctly assigned to the
execution preflight. This accepts readiness only and grants no execution.

Next packet:
`.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_BATCH_A1_TASK_PACKET.md`.
