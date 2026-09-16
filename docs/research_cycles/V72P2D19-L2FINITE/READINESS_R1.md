# D19 L2 Finite-Ensemble Validation — Readiness R1 (STOP record)

- Authority: `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`
  §10 STOP + §11 return; `D19-BLOCKER-REVIEW` result below (trusted VERIFIED, do not rerun).
- Track: documentation-only (no code, no execution, no repair, no seed change,
  no root creation, no commit/push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (do not switch).
- Predecessor: `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.
- This file is the compact readiness record. Append-only log root:
  `EXPLORATION_LOG.md` in this directory. OpenSpec: `v72p2d19-l2-finite-ensemble-validation`.

## 1. Route acceptance + near-tie ceiling (packet §1, F01)

- Accept the D18 winner `lam_d2_0.20_d3_0.80` for ONE finite L2 validation
  against DV3. Not an optimality claim.
- D18's 0.15/0.20/0.25 candidates had identical reviewed DE thresholds;
  0.20 won only through the frozen max-check-degree then ID tie-break. Do not
  reopen the family or include extra near-tie arms in D19.
- No scientific decoder calls, D7-H, APP, L1, real data, FER/leakage/SKR/
  qualification, route closure, or push are authorized by readiness.

## 2. F01–F02 tables (packet §2, design.md §§2.1–2.4)

Single rate point: D18 discriminator m/n = 94/128, corresponding to
`delta_L2 = 0.44915511536562214`, below DV3's DE threshold and above the
selected candidate's threshold. L2 channel is true-U1-conditioned ORACLE,
diagnostic-only and ungraded; no APP/transfer.

| width | m | arm | variable counts | E | check counts |
|---:|---:|---|---|---:|---|
| 128 | 94 | DV3 | `3^128` | 384 | `4^86 + 5^8` |
| 128 | 94 | L020 | `2^35 + 3^93` | 349 | `3^27 + 4^67` |
| 256 | 188 | DV3 | `3^256` | 768 | `4^172 + 5^16` |
| 256 | 188 | L020 | `2^70 + 3^186` | 698 | `3^54 + 4^134` |

Exact rational realized deviations from nominal (F02 hand rederivation,
VERIFIED, no mismatch):

- Nominal edge `lambda = {2:1/5, 3:4/5}`; nominal node `L2 = 3/11`, `L3 = 8/11`
  (identical realized fractions at both widths by exact doubling).
- L020 edge: `lambda2 = 70/349` (deviation `+1/1745`); `lambda3 = 279/349`
  (deviation `-1/1745`).
- L020 node: `L2 = 35/128` (deviation `+1/1408` over `3/11`);
  `L3 = 93/128` (deviation `-1/1408`).
- L020 check edge: `rho3 = 81/349`, `rho4 = 268/349`; node `R3 = 27/94`,
  `R4 = 67/94`; mean check degree `349/94`.
- DV3 check edge (both widths): `rho4 = 43/48`, `rho5 = 5/48`;
  node `R4 = 43/47`, `R5 = 4/47`; mean `384/94 = 192/47`.
- `delta_L2` recompute: `5·94/128 − H_L2 = 3.671875 − 3.222719884634378
  = 0.449155115365622`, matching the packet to 15dp (trailing digit is
  full-double display). Evidence: `design.md` §§2.2–2.4.

## 3. STOP record — frozen seed 4408 (packet §10)

- Failing seed: n256 DV3 graph seed `2026094408`.
- Reviewer's own repro (twice each):
  `r2.build_degree_sequence_peg(256,188,{3:256},{4:172,5:16},2026094408)` and
  `d19.build_graph('DV3',256,2026094408)` → deterministic
  `status = 'construction_failed'`,
  `failure_reason = 'no eligible check placement at variable 255 socket 2'`.
- Constructor `is` r2 and zero-diff vs HEAD (accepted, untouched).
- 23/24 cells build+admit, incl. five identical-multiset n256 DV3 siblings
  4407/4409–4412; n128 leg 12/12.
- Arithmetic independently confirmed (four cells socket-closed; multiset
  feasible) → not a table defect.
- No replacement: seeds exactly 4401..4412 + 4501..4508/4511..4518; no
  replacement mechanism; test asserts ENGINEERING_BLOCKED naming 4408 with
  zero n256 calls; 33/33 new tests (reviewer rerun on own basetemp).
- Zero calls: PROFILE_ONLY my-own-run 24 graphs attempted / 23 admitted /
  plan 192 / counters 0 / root absent; refusal rc=2 no-write.
- Root absent; D19 files untracked-additive; no commit/push.
- Adjudication: genuine frozen-seed × accepted-constructor STOP (not fixable
  within readiness scope; packet forbids replacement/search and mandates
  engineering-block).
- ONE decision needed: amend the frozen n256 DV3 seed set (replace
  2026094408) under a new packet amendment (fresh disjointness proof +
  24-graph re-profile + re-review) OR formally accept terminal
  `D19_L2_FINITE_ENGINEERING_BLOCKED` as the D19 outcome (rescope/abandon
  n256 leg). Readiness as-frozen is STOP, not READY; no authorization may
  issue against the current seed set.

## 4. Implemented-but-blocked status (F03–F08)

F03–F08 artifacts exist (thin D19 module, cells/plan/gates/writer/verifier,
runner, focused tests, PROFILE_ONLY, frozen future root/command/budgets) but
readiness cannot reach the ready terminal: the frozen seed set is
engineering-blocked at 4408, so no `D19_L2_FINITE_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`
is issued.

## 5. Authorization (all false)

- No D19 execution authorized by this closure; decoder/DE calls: 0.
- Future root absent; frozen command remains an unauthorized string.
- No commit/push in this call.

## 6. Terminal

STOP — `D19_L2_FINITE_ENGINEERING_BLOCKED` path engaged at readiness; no
ready terminal issued. Next: main-thread seed-amendment decision (see §3).

## 7. Claim boundary

Synthetic finite-L2 diagnostic evidence only. No FER/leakage/SKR/
qualification/promotion/publication/optimality/route-closure claim. The
§11 return contract's ready marker is NOT returned.

COMMIT_PUSH: none. Decoder/DE calls: 0.
