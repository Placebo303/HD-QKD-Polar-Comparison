# D13 L055 Decoder Ladder — Batch A1 Task Packet

## 1. Identity and track

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Batch: `D13_L055_DECODER_LADDER_BATCH_A1`
- Track: `EXPLORE`
- Readiness prerequisite:
  `D13_L055_DECODER_LADDER_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
- This packet freezes one execution. It does not itself authorize execution.

## 2. Scientific question

For the 56 frozen L055 failures selected from the accepted D12 root, determine
whether accepted longer-iteration or alternative-schedule decoder arms recover
material signal after an exact RL90 replay. This is an L1-only synthetic
decoder diagnostic. It is not a tuning scan and does not test L2 or D7-H.

## 3. Frozen inputs and outputs

- Model-F input:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Immutable D12 input:
  `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
- Fresh output root:
  `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
- Selector: exactly 56 L055 failures, n128=30 and n256=26; all frozen
  identities must match, and the 88 D12 successes remain excluded.
- Arms, in frozen order after baseline replay:
  `ROW_LAYERED_360_ALPHA_1`, `ROW_LAYERED_360_ALPHA_0_7`, `FLOODING_360`.
- Baseline: strict `ROW_LAYERED_90` replay of identity, exact, syndrome,
  iterations, and mandatory `CHECK_UPDATED` provenance.
- No added arm, damping search, seed extension, input change, or threshold
  change is permitted.

## 4. Pre-dispatch checks

Record all checks in the existing append-only `EXPLORATION_LOG.md` before the
authorized command:

1. Accepted readiness marker and D13-R1310 VERIFIED review are present with no
   blocking finding.
2. Branch is exact; inspect only scoped D13 paths and preserve unrelated dirty
   files.
3. Future root is absent; D12 and Model-F roots are present and unchanged;
   Model-F remains CAL-only.
4. Recompute the selector: exactly 56 identities (30/26), all frozen RL90
   failure fields match, successes and `undetected` rows are excluded.
5. Run `--plan-only` twice: byte-deterministic 56 identities / 224 calls, zero
   decoder calls, no result-root write.
6. Exercise unauthorized refusal against a fresh scratch target: rc=2 and no
   target creation. Report only properties actually observed; do not infer the
   vacuous second-clause isolation assertion.
7. Run `py_compile` and focused D13 plus D12 tests in a fresh writable
   `workspace/` basetemp with cache disabled. Do not rerun the adjudicated
   D12+X3 combined suite unless a focused check creates a concrete conflict.
8. Confirm exact command, arms, gates, budgets, one-process/no-retry contract,
   and that authorization has not already been consumed.

Any mismatch: STOP before `--d13-batch`; show raw evidence and request one
decision. Do not repair, clean, retry, or substitute a root.

## 5. Authorized command

After and only after an explicit user grant naming this batch, run exactly once:

```bash
.venv/bin/python scripts/v72p2d13_development.py --d13-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e
```

The grant is consumed when the command starts. No second invocation, resume,
repair, rerun, seed search, or adaptive arm is authorized.

## 6. Budgets and stop rules

- Scientific decoder calls: exactly planned 224, ceiling 224.
- Setup units: ceiling 8.
- Wall: ceiling 1800 s.
- Per call: ceiling 120 s.
- RSS: strictly below 2 GiB.
- Process count: one.
- First baseline replay mismatch: stop all later ladder records and retain the
  partial root under the frozen engineering-blocked terminal.
- Crash, nonfinite output, malformed provenance, overwrite attempt, budget
  breach, or frozen-plan drift: stop and retain evidence; no automatic repair.

## 7. Frozen interpretation

Recompute each arm's rescues over the 56 identities with exact, syndrome, and
`undetected` kept separate.

- `MATERIAL`: total rescues >=12 and >=4 at each width.
- `MODEST`: total rescues 3..11 and >=1 at each width.
- `NO`: total rescues <=2.
- Otherwise: `AMBIGUOUS`.

If multiple arms are material, rank by total rescues, worst-width rescues,
lower mean rescue iterations, then frozen arm order. Use only the six frozen
D13 terminals. Stored terminal is exploratory evidence and never self-selects
the next route.

## 8. Independent batch-end review

After the command, one independent reviewer with actual artifact access shall:

- verify the authorization boundary, exact single command, root inventory,
  call/setup/resource budgets, and absence of retry;
- recompute the 56 identities and strict RL90 replay comparison;
- recount every arm by width, provenance, exact, syndrome, and `undetected`;
- recompute rescues, MATERIAL/MODEST/NO/AMBIGUOUS classes, ranking, and terminal;
- confirm D12/Model-F inputs were not modified and no L2/D7-H/real-data path ran;
- record `EVIDENCE_ACCESS`, verdict, blocking findings, and carried findings in
  the same exploration log.

A failed review blocks use of the evidence. It does not authorize another run.

## 9. Return contract

Return only after reviewed completion or a concrete STOP. On completion report:

- terminal `D13_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`;
- exact command/exit/timestamps; calls, setup, wall, max-call, RSS, process count;
- baseline replay result; per-arm/per-width rescues and frozen classification;
- selected arm if and only if the frozen rule selects one;
- independent verdict and all findings;
- changed files/root inventory; authorization consumption; no retry/rerun;
- commit/push state and the exact remaining scientific claim boundary.

Do not commit, push, run L2/D7-H/real data, or issue a route decision.
