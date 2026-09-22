# D5-G1-R2-STALE-GUARD-FIX-R1 — close the sole known suite failure

## 0. Objective

Complete the R2 candidate by repairing the one stale lifecycle test that still
requires the now-valid G1 formal root to be absent. Preserve its real intent:
fresh-root literal, old-root exclusion, VOID retention, and formal-root
immutability.

This is candidate completion, not an R2 scientific review or formal execution.

## 1. Baseline

- Branch `formal-ir-v72p1-addendum-clean`
- Expected HEAD `21576add`
- Candidate commits `88053563 → a93106f5 → 21576add`
- Sole reported failure:
  `test_G1R01_fresh_root_literal_and_old_barred`
- Stale line:
  `assert _snapshot_dir(ROOT / mod.G1_FORMAL_ROOT) is None`
- Valid root `workspace/v72p2d5_g1/20260907_r2` now legitimately exists and is
  immutable.
- G2 remains absent; all authorizations false.

## 2. Allowed changes

Exactly:

1. `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
2. `openspec/changes/v72p2d5-g1-information-recovery-r2/tasks.md`

In the test:

- replace the stale absence assertion with an explicit comparison against the
  start-of-test snapshot for that same valid G1 root;
- keep the existing `_assert_formal_roots_unchanged(formal_before)`;
- preserve assertions for the new-root literal, old-root exclusion, P0/G2
  literals, and retained VOID four-file snapshot;
- extend `test_T1_23_no_formal_root_absence_assertion` just enough to catch the
  escaped equivalent pattern: `_snapshot_dir(<formal-root expression>) is
  None` or `== None` inside an assert. Keep its existing checks.

In `tasks.md`, append one concise completed repair item with focused/full test
evidence. Do not rewrite previous task history.

## 3. Hard boundaries

- No production `.py` change and no new behavior/OpenSpec proposal.
- No decoder, CLI phase, diagnostic rerun, Model-F/CAL/VAL/parquet read.
- No formal/evidence workspace read beyond top-level name/size/mtime snapshots;
  do not open VOID contents.
- No formal-root write/delete/move/rename/hash/normalize.
- No lifecycle/authorization/decision-log/memory/report change.
- No weakening, skip, xfail, deletion of scientific assertions, or hard-coded
  green result.
- No unrelated cleanup, push, reset, stash, checkout, clean, rebase, amend,
  broad stage, or line-ending normalization.

## 4. Verification

Before edit, reproduce the sole failing test and confirm no other focused
failure. After edit:

1. run the repaired test plus `test_T1_23_no_formal_root_absence_assertion`;
2. run the exact three-file D5 suite with a fresh unique `workspace/` basetemp
   and `-p no:cacheprovider`;
3. require zero failures; expected collection is 227 tests, but report the
   actual literal summary rather than forcing the count;
4. verify production `.py` numstat empty;
5. verify all protected roots unchanged, G2 absent, all authorizations false;
6. safely remove only the validated basetemp.

If the suite has another failure, diagnose it. Repair only if it is caused by
the same stale formal-root absence semantics and remains within the single
allowed test file; otherwise STOP with raw output.

## 5. Commit

Stage exactly the two allowed files. Require `STAGED_COUNT 2`, then commit:

```text
test(v72p2d5): make G1 R2 root guard lifecycle-aware

Replaces the stale valid-root absence assertion with snapshot invariance and
extends the recurrence tripwire to catch equivalent snapshot-is-None forms.
No production or scientific behavior change.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Do not push. Leave `next_gate: INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`.

## 6. Return

Report changed lines, why the old check was stale, focused/full literal pytest
lines, protected-root equality, two staged paths, SHA/status, and prohibition
true/false list.

End:

`R2 候选已完成测试生命周期收口；生产实现与正式证据未改，等待独立信息恢复评审。`

