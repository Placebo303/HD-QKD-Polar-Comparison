# TASK PACKET — D5-PRERESULT-R2: independent Pre-RESULT re-review (read-only)

Target executor: an **independent** reviewer session. You did not author the
Model-F implementation, the disposition record, or the D5-DISPO-R1 packet. Do
not accept any prior verdict on faith; re-derive from actuals.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Change under review: `formal-ir-v72p2d5-model-f-input-preparation`
- Role: read-only artifact review. Authorization in this task: **false**.
- Deliverable: exactly ONE new file (see §6). No commit. No push.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run any decoder; run `scripts/v72p2d5_gf32_rate_mother.py` with
   `--phase p0-cost|g1|g2`; run `scripts/v72p2d5_prepare_model_f_input.py` at
   all. The prepare/verify authorization was consumed on 2026-09-07 and replay
   is forbidden.
2. Read CAL/VAL/raw rows. `pandas.read_parquet` is forbidden. Parquet
   **metadata** via pyarrow is allowed.
3. Delete, move, rename, copy, normalize, hash, or open-for-write anything
   under `workspace/`. `stat`, `json.load`, and `numpy.load(allow_pickle=False)`
   are allowed.
4. Create `workspace/v72p2d5_p0_cost/...` or `workspace/v72p2d5_g2/...`.
5. Edit any `.py`, any existing `.md`, `cycle_state.yaml`, `docs/decision-log.md`,
   `AGENT_PROJECT_MEMORY.md`, `openspec/**`, or any prior review file.
6. `git commit`, `git push`, `git add`, `git reset`, `git stash`,
   `git checkout --`, `git clean`, `git rebase`, `git revert`.
7. Change any `*_execution_authorized`, accept a result, promote anything, or
   authorize P0.
8. Write `RESULT_SUMMARY.md`, `OPERATOR_RETURN.md`, or any `run_01`.
9. Fix anything you find. You report; you do not repair.

If you cannot complete a check, record it as `NOT_VERIFIABLE` with the reason.
Do not guess and do not substitute a weaker check silently.

---

## 1. What is being decided

The prior independent review
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`
returned `PRE_RESULT_REVIEW_FAIL` on a single blocking check, **PR16**: the
formal root `workspace/v72p2d5_g1/20260906_r1/` existed with
`decoder_calls=440` while `g1_execution_authorized=false`.

Since then, the main thread executed a documentation-only disposition
(commits `b986ca11`, `7c59d375`, `20204726`) which retains that root unmodified
and records it as void, rather than removing it.

**Your question, to answer independently:** does the recorded disposition
clear PR16 for the purpose of accepting the Model-F input candidate, or does
PR16 still block?

You are not told the answer. Both verdicts are legitimate outcomes. Argue from
what you verify.

---

## 2. Re-verify the Model-F artifact (do not trust R1)

Recompute, do not copy R1's numbers:

- `workspace/v72p2d5_model_f_input/20260907_r1/` contains exactly 2 regular
  files, named `model_f_input.npz` and `model_f_input_summary.json`.
- `numpy.load(..., allow_pickle=False)` succeeds; keys are exactly
  `counts_ab`, `p_b`; no object dtype.
- `counts_ab`: shape, dtype, sum, min, max, nonzero count, negatives.
- `p_b`: shape, dtype, sum, min, max, finiteness.
- Marginal identity: `p_b == counts_ab.sum(axis=0) / counts_ab.sum()`. Report
  max absolute deviation and whether the wrong axis (`axis=1`) is
  distinguishable.
- `model_f_input_summary.json`: schema, cycle, session, CAL range, frame and
  symbol counts, axis, dims, mapping, field, `lambda_star`, selection,
  `cal_only`, `val_rows_read`, `decoder_calls`, `p0_calls`, `formal`, status,
  `artifact_files`.
- Whether the summary internally agrees with the arrays (dims vs shape, n vs
  sum, file list vs directory listing).

Where R1 recorded a value, state whether yours agrees. Where you disagree with
R1, say so explicitly — R1 is evidence, not authority.

## 3. Verify the disposition itself

- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_UNAUTHORIZED_DISPOSITION_R1.md`:
  does it exist, is it internally consistent, and do the `size`/`mtime_ns`
  values it records for the four G1 files match the files on disk right now?
- Is the G1 root still exactly 4 files, unmodified?
- Are `workspace/v72p2d5_g0/20260905_r2/` and
  `workspace/v72p2d5_g0_recovery/20260906_r1/` unmodified?
- Are `workspace/v72p2d5_p0_cost/20260906_r1` and
  `workspace/v72p2d5_g2/20260906_r1` still absent?
- Does the disposition text actually bar the G1 artifact from citation, or does
  it leave a path by which those numbers could later be read as a result?
- Do the `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md` entries match the
  disposition record, and do they overstate anything?

## 4. Verify the lifecycle at HEAD

- Read `cycle_state.yaml` **at HEAD** (not only the worktree). Report every
  `*_execution_authorized`, `scientific_promotion`, `decoder_executed`,
  `cal_rows_read`, `val_rows_read`, `next_gate`.
- Inspect the three commits `b986ca11`, `7c59d375`, `20204726`: file counts,
  whether any `workspace/` path was committed, whether any `.py` content change
  beyond the P0/G1/G2 prefix-slice candidate and the Model-F implementation is
  present, and whether the commit messages match the contents.
- Confirm nothing was pushed (`git status -sb`).

## 5. Verify code-side claims (static + tests)

- `py_compile` on
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
  `scripts/v72p2d5_prepare_model_f_input.py`,
  `scripts/v72p2d5_gf32_rate_mother.py`.
- Run, with a fresh additive basetemp under `workspace/` (e.g.
  `workspace/v72p2d5_preresult_r2_<date>_<tag>`):
  `comparison_bench/tests/test_v72p2d5_model_f_input.py`,
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`,
  `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`.
  Report the literal pytest summary line and every failing test id.
  Reference values from the isolation rework, for orientation only, not as a
  pass condition: the first two files collected 165 and passed 165.
- Assess the test-isolation repair claimed in
  `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`: read the SAFE A/B/C containment and
  the AST static guard in the test source and judge whether an authorized
  synthetic call can still reach the production decoder or a formal output root.
  This is the check that decides whether the incident can recur.
- After the tests, re-stat the five protected roots and confirm nothing changed
  and that `p0_cost`/`g2` are still absent.

## 6. Deliverable

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md`

Structure it as R1 does: numbered checks with per-check `PASS` / `FAIL` /
`NOT_VERIFIABLE`, recomputed values inline, a pre/post stat snapshot, an
explicit statement of what you did and did not execute, and a closing verdict
block.

Your verdict must be exactly one of:

- `PRE_RESULT_REVIEW_PASS` — the Model-F input candidate is
  `READY_FOR_MAIN_RESULT_ACCEPTANCE`. State plainly that this readiness signal
  is not itself an acceptance and not a P0 authorization.
- `PRE_RESULT_REVIEW_FAIL` — name the single blocking check and the single
  decision required from the main thread.

Whichever you return, state the strongest claim the evidence supports and list
what is explicitly not claimed (no FER, no leakage, no SKR, no qualification,
no method verdict, no G1 performance conclusion).

Do not create any other file. Do not commit. Do not push. Do not change status.
Do not authorize P0.

## 7. Report back

In your message (not in the file): the verdict, the per-check table in brief,
the literal pytest line, any disagreement with R1, and this line if and only if
it is still true:

「PR16 仅以记录方式处置；P0 未授权。」
