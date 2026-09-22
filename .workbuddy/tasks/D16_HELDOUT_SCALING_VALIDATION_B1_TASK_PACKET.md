# D16 Held-Out Scaling Validation — Batch B1 Task Packet

## 1. Identity and scientific role

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D16_HELDOUT_SCALING_VALIDATION_B1`
- Track: `EXPLORE`
- Accepted predecessor:
  `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`.
- D16 is now a held-out falsification test of D17's frozen finite-length model,
  not a fit input and not the former direct L1/L2 investment gate.
- The original D16 A1 prompt remains superseded. Only this packet and its
  companion prompt authorize the run.
- One grant covers one frozen 96-call D16 run and one independent batch-end
  review. It authorizes no model revision, rerun, or route choice.

## 2. Immutable prediction input

Read only:

`workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`

Verify all eight fit-root files and the three outcome-blank predictions. Freeze:

| Profile | Cell | Point | Frozen 95% p-success band | Descriptive k/8 |
|---|---:|---:|---:|---:|
| L045 | n128/m125 | 0.8515665744172791 | [0.6156833274137923, 0.9743712729574681] | [5,8] |
| L055 | n128/m125 | 0.961571149393954 | [0.8899387155669418, 0.9955050869733582] | [6,8] |
| L2-ORACLE | n128/m94 | 0.31207335713883716 | [0.0, 0.5] | [0,5] |

- Recompute literals from the JSON files. Any mismatch, missing provenance,
  non-blank outcome, or changed prediction file is STOP.
- Never edit the fit root or predictions before or after D16.

## 3. Frozen D16 experiment

- Candidate Model-F generator/prior, n=128.
- L045: m125, variables `(71,57)`, E313, checks `2^62+3^63`, graphs
  `2026094001..04`.
- L055: m125, variables `(83,45)`, E301, checks `2^74+3^51`, graphs
  `2026094005..08`.
- L2 DV3 ORACLE: m94, E384, checks `4^86+5^8`, true-U1 conditioned,
  ungraded, graphs `2026094009..12`.
- Shared blocks `2026094101..08`; order L045→L055→L2-ORACLE then graph/block
  ascending; exactly 96 decoder calls, indices 0..95; setup 22.
- GF32/poly37, row-layered cold decoder, max_iter90, damping1.0.
- No APP/transfer. Exact, syndrome-valid, and undetected remain separate.
- Scientific inputs are retained; the former route interpretation is not.

## 4. Root, command, and budgets

- Model-F: `workspace/v72p2d5_model_f_input/20260907_r1`
- Fresh D16 root:
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
- Execute exactly once:

```bash
.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a
```

- 96 decoder calls; setup22; wall ≤900s; per call ≤120s; RSS <2147483648
  bytes; one CPU process; no retry/resume/repair/search/tuning/replacement.

## 5. Mandatory pre-dispatch

Append raw evidence to the D16 exploration log:

1. D17-A3 `EVIDENCE_ACCESS VERIFIED / PASS_WITH_FINDINGS`, no blocker, and
   accepted terminal.
2. Exact branch; D16 runner/module/tests without unexplained drift. Preserve
   unrelated dirt; SHA is provenance, not an execution lock.
3. D16 root absent; fit root, A2 DE root, and Model-F present/read-only.
4. Recompute predictions; all 18 outcome fields `BLANK`; record prediction
   file sizes/mtimes before run.
5. Recompute factors, sockets, 12 graphs, eight blocks, 96-row order,
   admissions, and identity match.
6. Reconfirm D5 candidate prior and L2 oracle path; prove no APP/transfer.
7. PROFILE_ONLY: 12/12 admitted, plan96/setup22, zero replacement/calls.
8. Unauthorized refusal on fresh scratch: rc2 before root/bind/load.
9. `py_compile` and focused D16 tests in a fresh writable basetemp. Do not
   rerun D17 fit/DE or broad suites without a concrete conflict.
10. Reconfirm command, budgets, verifier, never-revise rule, unused grant.

Any failure is STOP. Do not change predictions or substitute cells/roots.

## 6. Frozen held-out adjudication

For each profile:

- `observed_p=pooled_exact/32`.
- `FALSIFIED` iff strictly outside its frozen 95% band.
- `NOT_FALSIFIED` iff inside or on the band.
- `INCONCLUSIVE` iff engineering/resource/provenance failure prevents a valid
  32-trial observation.
- Per-graph counts versus k/8 are descriptive and never override pooled status.
- Syndrome-valid and undetected are audited separately, never substituted.

Report the existing D16 machine terminal/former classes only for artifact
consistency. They do not determine falsification or choose a route. Do not
collapse partial falsification into an unregistered universal-model verdict.

## 7. Independent batch-end review

One independent reviewer with artifact access must verify prediction files
predate D16 and remain byte-unchanged/BLANK; the one-shot grant, command/root,
96/22, no retry, inputs, resources; independently recount exact/syndrome/
undetected; prove L2 ORACLE/ungraded and no APP; run D16 verifier and recompute
legacy terminal; compute three frozen-band statuses; append the review to the
D16 log and a pointer to D17. Failure blocks use and grants no rerun.

## 8. Return contract

Valid reviewed completion:

`D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`

Report prediction provenance/immutability; command/resources; per-profile and
per-graph exact/syndrome/undetected; observed fractions; three band verdicts;
descriptive graph comparisons; legacy terminal as secondary; root/verifier/
reviewer; grant; no retry/commit/push.

Failure terminal: `D16_HOLDOUT_VALIDATION_BLOCKED_AWAITING_DECISION`.

Do not revise/refit D17, rerun D16, revive D7-H, run real data, or make FER/
leakage/SKR/qualification/optimality/publication/route-closure claims.
