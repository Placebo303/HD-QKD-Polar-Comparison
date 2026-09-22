# D7-E Verify Provenance R18 Closeout A1 Task Packet

## 0. Main-thread ruling

Ruling: preserve the completed one-shot D7-E execution and close only the missing verifier-transcript provenance gap. The literal verifier output was captured in the operator's process report but omitted from the uncommitted operator-return artifact. This is a documentation persistence defect, not permission to invoke verify again.

Authoritative resupplied transcript from the operator return:

```text
VERIFY_OK {'ok': True, 'problems': [], 'records': 192, 'terminal': 'D7_E_L2_TO_L1_TRANSFER_LIFT'}
```

Reported verifier exit code: `0`.

Provenance label: `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN`.

This ruling authorizes only additive transcription, an R18-only independent review, and conditional result-record solidification. It does not authorize any decoder, verifier, scientific recomputation, retry, rerun, recovery, or result acceptance.

## 1. Preconditions

- Branch: `formal-ir-v72p1-addendum-clean`.
- Required commits: `40eeb73a`, authorization `b148c9d4`, revocation `34085c15` are ancestors of HEAD in that order.
- The unique execution root is exactly `workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`.
- The root contains exactly the seven previously reported files and no subdirectories.
- Uncommitted originals exist:
  - `D7_E_OPERATOR_RETURN_R1.md`
  - `D7_E_PRE_RESULT_REVIEW_R1.md`
- Original review's unique verdict is `D7_E_PRE_RESULT_REVIEW_BLOCKED_R1`, with R18 as the sole blocker and R01–R17/R19–R22 PASS.
- All authorization flags are false; R1d and G2 roots are absent; no result-solidification commit exists.

Any mismatch means STOP. Do not repair or reinterpret it.

## 2. Hard prohibitions

- Do not run `--verify`, decoder code, any scientific runner, any `--phase`, tests, compile, dry-run, sentinel, RSS probe, or environment rehearsal.
- Do not read Model-F, CAL, VAL, real/raw, VOID, priors, symbols, beliefs, syndromes, or protected artifact contents.
- Do not change the seven result files, their bytes, names, sizes, or mtimes.
- Do not edit the original operator return or original BLOCKED review.
- Do not alter production code, tests, OpenSpec, frozen packets, formulas, parameters, state authorization keys, or accepted predecessors.
- Do not create a new UUID/root or run a second verifier.
- Do not push, broad-stage, clean, reset, checkout, stash, rebase, or amend.
- Do not upgrade the scientific result to accepted, qualified, promoted, FER, leakage, key rate, or general algorithm success.

## 3. Allowed new files

Only two new review artifacts may be created before conditional solidification:

1. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_VERIFY_TRANSCRIPT_APPENDIX_A1.md`
2. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_A1.md`

At solidification, `cycle_state.yaml` may be updated only as specified in §7. No decision-log or long-term-memory scientific conclusion is allowed before main-thread result acceptance.

## 4. A1.1 — read-only baseline

Using metadata and Git only:

1. Confirm §1 commit order and scoped cleanliness.
2. Confirm the two uncommitted original documents exist and have not changed during this task.
3. Confirm the seven result files' names, sizes, and `mtime_ns`; compare against the prior report and again at closeout.
4. Confirm all authorization flags false, current stale state facts, R1d/G2 absence, and no push.
5. Confirm no prior appendix/addendum exists.

Do not open result CSV/JSON contents. R01–R17/R19–R22 are frozen from the independent review and are not reopened.

## 5. A1.2 — transcript appendix

Create `D7_E_VERIFY_TRANSCRIPT_APPENDIX_A1.md` containing exactly:

- execution UUID and root;
- the literal transcript block from §0;
- reported exit code `0`;
- provenance label `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN`;
- explicit fields `VERIFY_INVOCATIONS_THIS_TASK: 0`, `DECODER_INVOCATIONS_THIS_TASK: 0`, `SCIENTIFIC_RECOMPUTATION_THIS_TASK: 0`;
- disclosure that no original standalone log file exists and timestamps were not separately persisted;
- statement that this appendix supplies provenance only and does not itself prove the verifier ran;
- statement that root immutability and verifier semantic invariants remain those already independently checked in the original Pre-RESULT review.

Do not fabricate timestamps, shell exit capture, command-log lines, or stronger provenance.

## 6. A1.3 — independent R18-only review

Create `D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_A1.md`. The independent reviewer must:

1. Read the original BLOCKED review, the untouched operator return, this task packet, and the new appendix.
2. Confirm R18 was the only blocker and no other review item is reopened.
3. Confirm the appendix is a verbatim transcription of §0 and labels its source/limitations accurately.
4. Confirm no second verifier, decoder, test, or scientific calculation occurred.
5. Confirm the result root metadata is unchanged before/after.
6. Decide whether the combined evidence—operator-captured literal output, exit 0 report, complete internally consistent root, prior independent verifier-invariant recomputation, and root immutability—is sufficient for record solidification despite the disclosed missing standalone transcript artifact.

Unique verdict must be one of:

- `D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_PASS_A1`
- `D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_FAIL_A1`
- `D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_BLOCKED_A1`

PASS means the original overall review is closed as `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`; it does not erase or rewrite the original BLOCKED review.

## 7. A1.4 — conditional solidification

Only for the exact PASS token:

1. Update D7-E `cycle_state.yaml` factually:
   - authorization remains false;
   - attempts/completed become `1/1`;
   - decoder/result become true;
   - record UUID/root/terminal;
   - point to the original review, appendix, and R18 addendum;
   - record Pre-RESULT as `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`;
   - set `next_gate: INDEPENDENT_D7_E_RESULT_ACCEPTANCE_R1`;
   - leave result accepted/qualification/promotion false.
2. Stage exactly:
   - seven immutable result-root files using `git add -f` only where required;
   - untouched `D7_E_OPERATOR_RETURN_R1.md`;
   - untouched `D7_E_PRE_RESULT_REVIEW_R1.md`;
   - new transcript appendix;
   - new R18 addendum;
   - D7-E `cycle_state.yaml`.
3. Verify the staged manifest and that no result-root bytes changed.
4. Make one local result-record commit. Do not push.

For FAIL/BLOCKED: do not update state, stage, or commit result artifacts. Return the exact blocker.

## 8. A1.5 — final checks and return

Report delta only:

1. Preconditions and original-file immutability.
2. Appendix exact transcript, provenance label, and disclosed missing fields.
3. R18-only findings and unique verdict.
4. Explicit counts: verify/decoder/tests/scientific recomputation all zero in this task.
5. Result-root pre/post metadata equality and protected-root/R1d/G2 status.
6. Staged manifest, commit SHA, state facts, next gate, all authorization flags, and no-push status if PASS.
7. True/false list for every prohibited action.

End with: `D7-E 的唯一 verify 字面输出已按 AUTHOR_RESUPPLIED provenance 补录，未重跑 verifier 或 decoder；R18-only 复审完成，结果仍仅为待主线程接受的记录，R1d、G1、G2 均未授权。`
