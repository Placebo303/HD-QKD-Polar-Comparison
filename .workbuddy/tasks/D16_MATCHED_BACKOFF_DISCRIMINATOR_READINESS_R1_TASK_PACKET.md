# D16 One-Point Matched-Backoff Discriminator — Readiness R1

## 1. Identity and boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d16-matched-backoff-discriminator`
- Work type: implementation/readiness; future batch track `EXPLORE`.
- Predecessor:
  `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR`.
- This packet authorizes OpenSpec, additive implementation, fake-only tests,
  PROFILE_ONLY, refusal checks, independent review and a scoped local commit.
- It authorizes zero production/scientific decoder calls and no future batch.

## 2. Scientific question

At one matched effective disclosure factor near 1.139, does L055 become
adequate while true-conditioned L2 DV3 remains weak? This single point closes
the gap between D15 high point and D14N's over-disclosed L2 result without a new
degree search.

## 3. Frozen proposed matrix

- n=128; unchanged candidate concentration-backoff generator/prior.
- L1 load `548.700215065776` bits; m=125; disclosed=625 bits; exact factor
  `1.1390555039696448`.
- L2 load `412.508145233200` bits; m=94; disclosed=470 bits; exact factor
  `1.1393714413428093`.
- Absolute factor gap `0.00031593737316448767`.
- Arms: L1 L045, L1 L055, L2 DV3 ORACLE. No APP or transfer.
- Profiles and derived checks:
  - L045 71/57/E313; m125 checks `2^62+3^63`.
  - L055 83/45/E301; m125 checks `2^74+3^51`.
  - L2 variable `3^128`/E384; m94 checks `4^86+5^8`.
- Fresh graph seeds: L045 `2026094001..04`, L055 `2026094005..08`, L2
  `2026094009..12`; block seeds `2026094101..08`, shared across all arms.
  Prove disjointness and absence before implementation; no replacement/search.
- Calls: 3 arms × 4 graphs × 8 blocks = exactly 96.
- Setup: 12 graphs + 8 blocks + 2 plan/manifest = exactly 22.
- Reuse D15 construction, admission, coefficient, sampling, prior, L1 dispatch,
  L2 oracle, evidence and verifier semantics. No copied decoder/GF32 kernel.

If any arithmetic, seed or constructor check conflicts, STOP before code; do
not silently amend the frozen point.

## 4. Frozen predicates and terminals

Reuse D15 cell predicates independently on each 32-trial arm:

- ADEQUATE: pool ≥24/32 and at least two graphs ≥6/8.
- WEAK: pool ≤16/32 and at least two graphs ≤4/8.
- otherwise MIDDLE.

L045 is descriptive only. Gate using L055 and L2 ORACLE, first match:

1. engineering/resource violation → `D16_ENGINEERING_BLOCKED`;
2. L055 ADEQUATE and L2 WEAK → `D16_L2_DEGREE_SIGNAL`;
3. L055 WEAK and L2 ADEQUATE → `D16_L1_CONSTRUCTION_SIGNAL`;
4. L055 ADEQUATE and L2 ADEQUATE → `D16_MATCHED_BACKOFF_SUFFICIENT`;
5. L055 WEAK and L2 WEAK → `D16_BOTH_WEAK`;
6. otherwise → `D16_AMBIGUOUS`.

Paired L055/L045 discordances and Wilson intervals are descriptive only.
Stored terminals remain evidence awaiting main-thread adjudication.

## 5. D1601–D1609 implementation tasks

- **D1601 OpenSpec first**: proposal/design/tasks/spec with exact arithmetic,
  seeds, reuse map, gates, command/root proposal and claim ceiling.
- **D1602 arithmetic/admission**: independently prove factors, socket tables,
  seed separation and all 12 A1–A6 admissions with replay identity.
- **D1603 additive core**: thin D15-derived plan, tallies and six-terminal gate;
  import helpers rather than copying them; batch tag prevents predecessor pooling.
- **D1604 runner**: `--profile-only`, `--d16-batch`, default-false
  `--execution-authorized`, `--verify`; refusal before root/bind/Model-F load;
  authorized branch exactly one orchestrator plus one writer.
- **D1605 evidence**: fresh never-overwrite six-file root; records include arm,
  rows/factor, graph/block, exact/syndrome/undetected, iterations, oracle/graded,
  wall/resources. L2 must be ORACLE and ungraded.
- **D1606 tests**: exact math/sockets/seeds/plan; no-APP; all predicate edges and
  terminal collisions; fake authorized 96/96 scratch run; existing/partial-root,
  provenance/nonfinite and refusal tests; verifier PASS.
- **D1607 PROFILE_ONLY**: 12/12 admitted, exact 96 plan, setup22, zero decoder,
  future root absent.
- **D1608 independent review**: actual access; separately recompute arithmetic,
  admissions, identities, fake true branch, gates, budgets, no-APP/no-production.
- **D1609 freeze execution**: exact fresh UUID root, command and budgets; leave
  unauthorized and absent.

## 6. Proposed budgets

- Scientific calls exactly/at most 96; setup exactly/at most 22.
- Wall ≤900 s; per call ≤120 s; RSS strictly <2 GiB.
- One CPU process; no retry/resume/repair/seed search/tuning/adaptive stop.

## 7. Verification and return

- T0 compile/math; T1 focused D16 plus directly affected D15 tests only.
- Fake authorized true branch must run 96/96 to a scratch root and pass verifier
  without production adapters. Broad suites only on concrete conflict.
- Independent review must state `EVIDENCE_ACCESS: VERIFIED`; blockers prevent
  readiness.
- Scoped local commit permitted after PASS; explicit pathspecs only, no push,
  branch switch, full-tree staging or line-ending sweep.

Return only:

`D16_MATCHED_BACKOFF_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with arithmetic/tables, seeds, 12/12 admission, 96/22 plan, gates, reuse map,
tests/fake/profile/refusal/verifier/reviewer results, root/command/budgets,
zero production calls and commit/no-push state.

Do not run the real batch, choose L1/L2 investment, revive D7-H, or make FER,
leakage, SKR, real-data, qualification, optimality or publication claims.
