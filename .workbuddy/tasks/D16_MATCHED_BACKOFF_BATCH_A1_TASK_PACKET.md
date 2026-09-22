# SUPERSEDED — DO NOT EXECUTE

This packet was superseded on 2026-09-15 by the main-thread finite-length
scaling route. D16 is retained as a future held-out model-validation point, not
an immediate layer-investment gate. No execution authorization was granted.
See `D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1_TASK_PACKET.md`.

# D16 One-Point Matched-Backoff — Batch A1 Task Packet

## 1. Identity and track

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D16_MATCHED_BACKOFF_BATCH_A1`
- Track: `EXPLORE`
- Accepted readiness:
  `D16_MATCHED_BACKOFF_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
- One explicit user grant covers one frozen run and its batch-end review. This
  packet alone grants no execution.

## 2. Frozen matrix

- n=128; accepted candidate concentration-backoff generator/prior.
- L1 load `548.700215065776`; m125/disclosed625; factor
  `1.1390555039696448`.
- L2 load `412.508145233200`; m94/disclosed470; factor
  `1.1393714413428093`; absolute gap
  `0.00031593737316448767`.
- L045: variable 71/57, E313; checks `2^62+3^63`.
- L055: variable 83/45, E301; checks `2^74+3^51`.
- L2 DV3 ORACLE: variable `3^128`, E384; checks `4^86+5^8`.
- Seeds: L045 graphs `2026094001..04`; L055 `2026094005..08`; L2
  `2026094009..12`; shared blocks `2026094101..08`.
- Plan order L045→L055→L2_ORACLE, then graph/block ascending; exactly
  3×4×8=96 calls, call_idx 0..95.
- L2 is true-conditioned ORACLE and ungraded. No APP/transfer path.
- Exact, syndrome and undetected are separate; predecessor rows cannot enter.

## 3. Root, command and budgets

- Model-F root: `workspace/v72p2d5_model_f_input/20260907_r1`.
- Fresh result root:
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`.
- Run exactly once after authorization:

```bash
.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a
```

- Scientific calls exactly/at most 96; setup exactly/at most 22.
- Wall ≤900 s; per call ≤120 s; RSS strictly <2147483648 bytes.
- One CPU process; no retry/resume/repair/seed search/tuning/adaptive stop.

## 4. Mandatory pre-dispatch

Append raw evidence to the D16 exploration log before execution:

1. Accepted readiness marker, R1608 VERIFIED verdict and R1608A PASS present.
2. Exact branch; `a0260907` is an ancestor; scoped D16 files have no unexplained
   drift. Preserve unrelated dirty files.
3. Official result root absent; Model-F root present, CAL-only and unchanged.
4. Recompute both factors/gap and all three socket tables exactly.
5. Reconfirm seed/cell assignments, eight shared blocks, 96 ordered identities,
   batch tag and disjointness from predecessors.
6. Reconfirm current D5 working tree: P0/G1/G2 each selects
   `prepare_model_f_prior_candidate` and not the legacy estimator. Drift is STOP.
7. PROFILE_ONLY: 12/12 A1–A6 admitted, zero replacements, plan96/setup22,
   decoder0 and official root absent.
8. Production signature-only probe resolves accepted L1 and true-L2 oracle
   adapters with zero calls/load; prove no APP/transfer path.
9. Live unauthorized refusal on a fresh scratch target: rc2 before root/bind/load.
10. `py_compile` plus 26 focused D16 tests in a fresh basetemp. Trust reviewed
    predecessors unless a concrete D16 conflict occurs. If a combined reused
    suite becomes necessary, follow the carried R3-first order and disclose why;
    materialized predecessor-root absence failures are not D16 regressions.
11. Reconfirm exact command, six terminal strings, budgets and unused grant.

Any failure: STOP before the real command and return raw evidence. Do not repair,
change roots/seeds/thresholds, clean prior roots or stage unrelated files.

## 5. Frozen grading

For L055 and L2 separately:

- ADEQUATE: pool ≥24/32 and at least two graphs ≥6/8.
- WEAK: pool ≤16/32 and at least two graphs ≤4/8.
- Otherwise MIDDLE.

L045, Wilson intervals and paired L055/L045 discordances are descriptive only.
First match:

1. engineering/resource violation → `D16_ENGINEERING_BLOCKED`;
2. L055 ADEQUATE + L2 WEAK → `D16_L2_DEGREE_SIGNAL`;
3. L055 WEAK + L2 ADEQUATE → `D16_L1_CONSTRUCTION_SIGNAL`;
4. both ADEQUATE → `D16_MATCHED_BACKOFF_SUFFICIENT`;
5. both WEAK → `D16_BOTH_WEAK`;
6. otherwise → `D16_AMBIGUOUS`.

The machine terminal is evidence only. It does not self-select an investment.

## 6. Independent batch-end review

One independent reviewer with actual artifact access must:

- verify exact one-shot authorization, command, no retry and six-file root;
- recompute factors/sockets, 12 admissions, identities and 96/22 accounting;
- recount exact/syndrome/undetected per arm and graph;
- prove L2 is ORACLE/ungraded and no APP/transfer path ran;
- recompute classes, first-match terminal and descriptive values;
- run read-only verifier; check resource budgets and unchanged Model-F input;
- record `EVIDENCE_ACCESS`, verdict, blockers and findings in the single log.

Review failure blocks use of evidence and grants no rerun.

## 7. Return contract

On reviewed completion return:

`D16_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`

Report command/exit/timestamps; calls/setup/wall/max-call/RSS/process; per-arm
and per-graph exact/syndrome/undetected; L055/L2 classes and stored terminal;
descriptive L045/discordance/Wilson results; root inventory; verifier/reviewer;
authorization consumption; no retry/commit/push; claim boundary.

Do not commit/push results, revive D7-H, execute real data, or make FER,
leakage, SKR, qualification, optimality, publication or final route claims.
