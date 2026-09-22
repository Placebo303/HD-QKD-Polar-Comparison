# TASK PACKET — D5-GUARD-REWORK-R1: make formal-root guards lifecycle-aware (tests only)

Target executor: implementation session. Read this whole file first.
This packet changes **test code only**. No production code. No execution.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD at start `b4696273`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Lifecycle: unchanged. No authorization, no acceptance, no G1.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run P0, G1, or G2. No `--phase p0-cost|g1|g2` invocation except an
   unauthorized-refusal check, which must exit 3.
2. Run any decoder. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
3. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
4. Modify, delete, move, rename, overwrite, normalize, or hash anything under
   `workspace/`. **The P0, G1, G0, G0-recovery, Model-F and structure roots are
   evidence — read-only.** You may create your own pytest `--basetemp`
   directory under `workspace/` and must remove it when done.
5. Let `workspace/v72p2d5_g2/20260906_r1` come into existence.
6. Edit ANY `.py` outside the two test files in the allowlist. **No production
   code changes in this packet at all.**
7. Change `cycle_state.yaml`, any OpenSpec file, or any existing `.md`.
8. `git push`, `git add -A`, `git add .`, `git commit -a`, `git reset`,
   `git stash`, `git checkout`, `git clean`, `git rebase`,
   `git commit --amend`, `git add --renormalize`.
9. **Weaken any guard to make a test pass.** Deleting an assert, narrowing a
   loop, marking a test `skip`/`xfail`, or making an assertion trivially true
   is a failure of this task, not a solution. If you believe a guard cannot be
   made both green and meaningful, STOP and report which one and why.
10. Claim any scientific result, or that G1 is ready.

Allowlist — you may modify only:
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_model_f_input.py`

No other file.

---

## 1. The problem

Seven tests fail on `b4696273`. Run this to see them (fresh basetemp **under
`workspace/`** — the D4 audit tests fail spuriously if the basetemp is outside
the repository):

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/v72p2d5_guard_rework_pre -q --tb=no
```

Expected today: `7 failed, 193 passed`.

Six of them assert that the P0 formal root does **not** exist:

- `test_v72p2d5_model_f_input.py::test_M24_formal_roots_absent` (line ~424)
- `test_v72p2d5_model_f_input.py::test_P12_formal_roots_absent` (line ~644)
- `test_v72p2d5_gf32_rate_mother.py::test_R1_B2_all_exec_false_formal_absent_and_budgets` (line ~2136)
- `test_v72p2d5_gf32_rate_mother.py::test_P0G1G2_f_no_holdout_or_file_access` (line ~2941)
- `test_v72p2d5_gf32_rate_mother.py::test_P0G1G2_g_four_file_no_overwrite`
- `test_v72p2d5_gf32_rate_mother.py::test_M20_d5_authorized_fake_load_reaches_runner` (line ~3200)

They now fail because a **legitimate, authorized** P0 run created
`workspace/v72p2d5_p0_cost/20260906_r1/` on 2026-09-07.

The seventh, `test_T1_22_openspec_history_zero_mod`, fails for an unrelated
reason handled in T3.

**Why this matters, and why it is not cosmetic.** This is the same defect class
that produced the unauthorized G1 execution recorded in
`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`: guards that assume a
formal root is permanently absent silently stop meaning anything the moment a
legitimate artifact lands. Last time the consequence was not just red tests —
stale absence expectations sat alongside a bare `authorized=True` call and the
suite drove a production decoder into a formal output root. The containment
(SAFE A/B/C) held this time; the **guard model** did not, and it will break
again the moment G1 and G2 produce legitimate output.

## 2. T1 — Replace absence with invariance

The invariant these guards actually need is **"this test did not touch any
formal root"**, not "no formal root exists". Absence was only ever a proxy that
happened to hold early in the cycle.

Both test files already contain the right primitive: `_snapshot_dir`, used for
the Model-F and G1 roots. Extend that approach.

Required semantics for every formal root a test guards — P0, G1, G2, G0,
G0-recovery, Model-F, structure:

- Snapshot the root at test start and compare at test end.
- **Absent at start and absent at end → PASS.**
- **Present at start and byte-identical at end → PASS.** Compare names, sizes
  and mtimes, as `_snapshot_dir` already does.
- **Created by the test → FAIL.**
- **Deleted, or any file added, removed, resized or re-timestamped → FAIL.**

Implement this once as a shared helper in each file (do not import across test
files; a small duplicate is acceptable and preferable to coupling), and use it
in the six tests listed in §1. Do not hand-roll a different comparison in each
test.

Constraints:

- The helper must fail loudly on creation. A test that creates a formal root
  must still be a hard failure — that is the property that catches a
  recurrence of the incident.
- Do not make the expectation depend on `cycle_state.yaml`, on the current
  date, or on which stages have run. Snapshot-and-compare needs no such input.
- Do not remove the surrounding assertions in those tests. `test_M20`'s
  reachability assertions, `test_P0G1G2_f`'s no-file-access assertions,
  `test_P0G1G2_g`'s four-file and no-overwrite assertions, and
  `test_R1_B2`'s authorization and budget assertions all stay exactly as they
  are. You are replacing the absence line, not the test.

## 3. T2 — Keep the constant assertions

`test_P0G1G2_g` also asserts the literal root strings
(`workspace/v72p2d5_p0_cost/20260906_r1` and the G1/G2 equivalents). Those are
frozen-constant checks, not lifecycle checks. Leave them untouched.

## 4. T3 — Fix `test_T1_22_openspec_history_zero_mod`

This test asserts a clean tracked tree. It fails because the worktree carries
line-ending-only differences across ~1887 files with **zero content change**
(`core.autocrlf=true`, no `.gitattributes`; commit `299416ae` carries none of
it). This was reviewed and judged cosmetic, and repository-side normalization
was explicitly ruled out as a precondition.

Rework the test so its cleanliness criterion is **real content difference**,
e.g. derived from `git diff --numstat` (a file counts as modified only when its
added/deleted line counts are not both zero), rather than raw `git status`
porcelain lines.

Keep the test's actual purpose intact: it must still fail if a tracked file's
**content** changes. Do not delete it, do not skip it, do not broaden it into
uselessness.

## 5. T4 — Add a recurrence guard

Add one new test asserting that no test in these two files asserts the
non-existence of a formal output root. A source-level check in the spirit of
the existing AST static guard is appropriate: scan the two test files for
absence assertions against `P0_FORMAL_ROOT`, `G1_FORMAL_ROOT`,
`G2_FORMAL_ROOT`, `G0_FORMAL_ROOT`, `G0_RECOVERY_FORMAL_ROOT`,
`MODEL_F_FORMAL_ROOT`, or their literal path strings, and fail if any is found.

This is the test that prevents the same class from being reintroduced by a
future packet. Make its failure message say what to use instead.

## 6. T5 — Verification

- `py_compile` on both test files.
- Full run with a fresh basetemp under `workspace/`:
  ```bash
  cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/v72p2d5_guard_rework_post -q
  ```
  Target: **0 failed.** Report the literal line. Any remaining failure must be
  named and explained, not hidden.
- Confirm the SAFE A/B/C containment cases and the AST static guard still pass
  and were not weakened.
- **Prove the new guard actually catches a creation.** Demonstrate, in a
  throwaway `tmp` directory outside the formal roots, that the helper fails
  when a root it is watching is created. Do not demonstrate this against a real
  formal root. Report how you showed it.
- `git diff --numstat` on production code must be empty — no `.py` outside the
  two test files may change.
- Stat all six formal roots before and after your work; all must be unchanged,
  G2 still absent. Remove your basetemp directories when done.

## 7. T6 — Commit (local only, NO PUSH)

Stage only the two test files, verify with `git diff --cached --name-only`,
then commit once:

```
test(v72p2d5): make formal-root guards lifecycle-aware

Six guards asserted that the P0 formal root does not exist. A legitimate
authorized P0 run created it, so they failed. Absence was a proxy that only
held early in the cycle; the invariant these guards need is that the test
touches no formal root.

Replace absence with snapshot-and-compare: absent-then-absent passes,
present-then-identical passes, creation or any modification fails. Scope the
tracked-tree cleanliness check to real content differences rather than
line-ending-only churn. Add a source-level guard so no future test
reintroduces a formal-root absence assertion.

This is the guard model that failed in the unauthorized G1 incident. Tests
only; no production code, no execution, no authorization change.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 8. Report

Report: the literal pytest line before and after; the six reworked guards and
what each now asserts; how you proved the new helper catches a creation; the
`test_T1_22` rework and what it still catches; the new recurrence guard; the
before/after stat of the six formal roots; and these as `true`/`false` —
P0/G1/G2 invoked: false; decoder run: false; CAL/VAL read: false; any
production `.py` changed: false; any assert deleted, skipped or xfailed to
achieve green: false; any `workspace/` evidence modified: false; pushed: false.

Then stop. The next step is an independent review, not G1.
