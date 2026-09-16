# TASK PACKET — D5-GUARD-REWORK-REVIEW-R1: independent review of the guard rework

Target executor: an **independent** reviewer session. You did not write the
guard rework or any earlier D5 packet. Re-derive from source and from your own
runs; do not accept any claim below on faith — several are included precisely
so you can check them.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD `860ebbff`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Under review: commit `860ebbff` (two test files, +146/−49)
- Role: read-only review. Authorization: **false**.
- Deliverable: exactly ONE new file (§7). No commit. No push.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run P0, G1, or G2 through the CLI, except an unauthorized-refusal check
   (must exit 3). Never flip an authorization.
2. Run any decoder. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
3. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
4. Modify, delete, move, rename, overwrite, normalize, or hash anything under
   `workspace/`, except pytest `--basetemp` directories and scratch
   directories you create yourself and remove when done. **The six formal roots
   are evidence — read-only.**
5. Let `workspace/v72p2d5_g2/20260906_r1` come into existence. If it appears,
   STOP and report a critical finding.
6. Edit any `.py`, any existing `.md`, any OpenSpec file, or `cycle_state.yaml`.
7. `git add`, `git commit`, `git push`, `git reset`, `git stash`,
   `git checkout`, `git clean`, `git rebase`, `git revert`,
   `git add --renormalize`, or anything else that writes to tracked files.
8. Fix anything. You report; you do not repair.

Run pytest with `--basetemp` **under `workspace/`**. A basetemp outside the
repository makes the D4 audit tests fail spuriously; that is an artifact of the
invocation, not a regression.

---

## 1. What is being decided

Six guards previously asserted that formal output roots do not exist. A
legitimate authorized P0 run created one, so they failed. Commit `860ebbff`
replaces absence assertions with snapshot-and-compare invariance.

This matters beyond test hygiene: the same stale-absence guard model is
implicated in `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`, where
failed absence expectations sat alongside a bare `authorized=True` call and the
suite drove a production decoder into a formal output root.

Decide: **is the new guard model sound, is it actually stronger than what it
replaced, and was anything weakened to obtain a green suite?**

## 2. Verify the new guard semantics

Read `_formal_roots`, `_snapshot_formal_roots` and
`_assert_formal_roots_unchanged` in both test files and judge whether they
implement, without loopholes:

- absent at start and absent at end → pass;
- present at start and identical at end → pass;
- **created during the test → fail**;
- deleted, or any file added, removed, resized, or re-timestamped → fail.

Check specifically:

- Does the helper cover all seven roots the packet named (P0, G1, G2, G0,
  G0-recovery, Model-F, structure), and is each path correct?
- Can a test pass while having created a root — e.g. because the snapshot is
  taken too late, the comparison is skipped on some branch, an exception path
  bypasses the final assertion, or the helper is called but its result
  discarded?
- Is the comparison on names, sizes and mtimes, and is `None` used
  unambiguously for "absent" (so that absent-vs-empty-directory cannot be
  confused)?
- **Depth.** The implementer disclosed that `_snapshot_dir` inspects only
  top-level files. Assess what a nested write under a formal root would do to
  these guards, and whether that gap is acceptable or must be closed before G1
  and G2 produce output.

## 3. Verify nothing was weakened

The packet forbade deleting asserts, narrowing loops, `skip`/`xfail`, or
trivially-true assertions. Diff `860ebbff` against its parent and confirm for
each of the six tests that only the absence line changed and every other
assertion survives intact — specifically `test_M20`'s reachability assertions,
`test_P0G1G2_f`'s no-file-access assertions, `test_P0G1G2_g`'s four-file,
no-overwrite and frozen literal-path assertions, and `test_R1_B2`'s
authorization and budget assertions.

Also confirm: no production `.py` changed; the SAFE A/B/C containment cases and
the pre-existing AST static guard are intact and unweakened.

## 4. Reproduce the creation-catch proof yourself

The implementer claims to have shown the helper fails when a watched root is
created, using a temporary directory outside the formal roots. **Do not take
this on trust and do not reuse their script.** Construct your own demonstration
in your own scratch directory — never against a real formal root — and report
what you did and what you observed. If you cannot make the helper fail on a
creation, that is a blocking finding.

## 5. Verify `test_T1_22` and the new recurrence guard

- `test_T1_22_openspec_history_zero_mod` now judges cleanliness by
  `git diff --numstat` rather than `git status` porcelain lines. Confirm it
  still fails on a real tracked-content change — demonstrate this without
  leaving any modification behind, or mark `NOT_VERIFIABLE` and say why. Judge
  whether staged and unstaged changes are both covered, and whether binary
  files (`-`/`-` numstat) are handled.
- **Fact to check:** the implementer's report states the pre-change porcelain
  count was `STATUS=63`. An independent measurement at review time found
  `1887` modified paths with `numstat` content changes `0`. Establish the
  actual numbers yourself and report the discrepancy. Judge whether it affects
  the correctness of the rework or is only an error in the report.
- `test_T1_23_no_formal_root_absence_assertion`: read it and judge whether it
  would actually catch a reintroduced absence assertion, including forms it
  might miss (a different comparison operator, an indirect path variable, a
  literal path string not in its list, `os.path.exists`, `Path.is_dir`, and so
  on). State its real coverage rather than its intended coverage.

## 6. Run the suite

Full run, fresh basetemp under `workspace/`:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/<your fresh tag> -q
```

Report the literal summary line and any failing ids. Then stat the six formal
roots and confirm they are unchanged and G2 still absent. Remove your basetemp.

## 7. Deliverable

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/GUARD_REWORK_REVIEW_R1.md`

Numbered checks with `PASS` / `FAIL` / `NOT_VERIFIABLE`; your own
creation-catch demonstration; the depth-limitation assessment; the
`test_T1_23` real-coverage assessment; the `STATUS=63` discrepancy finding; the
literal pytest line; a pre/post stat snapshot of the six roots; an explicit
statement of what you did and did not execute; and a closing verdict.

Verdict, exactly one of:

- `GUARD_REWORK_REVIEW_PASS` — the guard model is sound and nothing was
  weakened. List any limitations that must be carried into the G1 packet.
- `GUARD_REWORK_REVIEW_FAIL` — name the blocking findings and the single set of
  changes required before re-review.

State what is not claimed: no FER, no leakage, no key rate, no qualification,
no method verdict, and no statement that G1 is ready.

## 8. Report back

In your message: the verdict, a brief per-check table, your creation-catch
demonstration in one or two sentences, the depth-gap judgment, the
`test_T1_23` coverage judgment, the `STATUS=63` finding, the literal pytest
line, and this line if it is still true:

「P0 结果仅为记录，未接受；G1 未授权；next_gate 仍为 P0_PACKET_REVIEW。」
