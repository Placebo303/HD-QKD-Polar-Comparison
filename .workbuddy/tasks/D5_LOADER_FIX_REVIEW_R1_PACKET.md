# TASK PACKET — D5-LOADER-FIX-REVIEW-R1: independent review of the Model-F consumer path fix

Target executor: an **independent** reviewer session. You did not write the
fix, the P0 packet, or any earlier D5 task packet. Re-derive from the source;
do not accept any prior claim on faith, including the ones in §3 below.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD `299416ae`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Under review: commit `299416ae` and the new OpenSpec change
  `openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/`
- Role: read-only review. Authorization: **false**.
- Deliverable: exactly ONE new file (§7). No commit. No push.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run P0, G1, or G2 through the CLI, other than the unauthorized-refusal check
   (which must exit 3). Never flip an authorization.
2. Run any decoder. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
3. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
4. Modify, delete, move, rename, or hash anything under `workspace/`, except a
   pytest `--basetemp` directory and a `tmp` directory you create yourself.
   Reading the Model-F artifact read-only is permitted **only** in the §5
   reachability probe.
5. Let `workspace/v72p2d5_p0_cost/20260906_r1` or
   `.../v72p2d5_g2/20260906_r1` come into existence. If either appears, STOP
   and report a critical finding.
6. Change any `cycle_state.yaml` value.
7. Edit any `.py`, any existing `.md`, or any OpenSpec file.
8. `git add`, `git commit`, `git push`, `git reset`, `git stash`,
   `git checkout`, `git clean`, `git rebase`, `git revert`,
   `git add --renormalize`, or anything else that writes to tracked files.
   **This is emphatic: see the §6 finding about a bulk worktree rewrite.**
9. Fix anything. You report; you do not repair.

Record anything you cannot check as `NOT_VERIFIABLE` with the reason.

---

## 1. What is being decided

Commit `299416ae` claims to fix a defect that cost one consumed P0
authorization: the Model-F consumer reached the accepted artifact by package
import, which fails when the CLI is launched as `python scripts/...` because
the repository root is not on `sys.path`. A present, valid artifact was
reported as `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`.

Decide: **is the fix correct, in scope, and adequately tested — and is the
repository fit for a new P0 authorization?**

## 2. Verify the fix

Read the changed hunks in
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
and judge:

- **Path resolution.** Is the loader module resolved from `__file__` rather
  than `sys.path`? Is `parents[4]` actually the repository root? Is the
  artifact root anchored to that root when relative, absolute-through when
  absolute? Is there any remaining cwd dependence, directory search, or
  guess-chain?
- **Failure separation.** Are the three outcomes genuinely distinct — loader
  unavailable, artifact absent, artifact invalid? Does the absent case name the
  resolved absolute path? Does the invalid case surface the loader's own error?
  Is the original exception chained rather than swallowed? Is `MODEL_F_BLOCKED`
  still reserved for genuine missing input, so existing asserts keep meaning?
- **Scope.** Were any frozen scientific constants touched (seeds, `f` sets,
  `m1`/`m2`, `CE_*`, `LAMBDA_STAR`, `MAX_ITER`, damping, budgets, call counts,
  roots, thresholds)? Did the change stay inside its allowlist?

## 3. Judge the one declared scope call

The implementer disclosed that resolving the sibling module by path was not
sufficient on its own: the sibling itself imports the contrast module
(`v72p2d3_gf32_contrast`) by package name, which also fails under script
launch. They therefore preload that module by file path and register it in
`sys.modules` under both names the sibling tries, using `setdefault`, without
mutating `sys.path` and without editing the sibling.

Judge this independently: is it the minimal completion of the assigned fix, or
scope creep? Consider specifically whether writing into `sys.modules` under
package names that do not otherwise exist can shadow or collide with a real
package import elsewhere in the process — for instance inside pytest, where
the rootdir *is* on `sys.path` and the genuine module may already be imported
or imported later. State the risk plainly and whether the `setdefault` guard is
sufficient.

## 4. Judge the test evidence

Read the added cases (`M22a`–`M22e`) and decide whether they actually cover the
condition that escaped every previous test:

- Does any test genuinely simulate the script-launch condition (repository root
  and `''` absent from `sys.path`), or does it only assert on resolved paths?
- Does any test read the real Model-F artifact? **It must not.** Confirm all
  use `tmp_path`.
- Are the SAFE A/B/C containment cases and the AST static guard intact and
  unweakened?
- Would these tests have failed before the fix? Reason about it; you may check
  out the prior version in a scratch location outside the repository if you
  can do so without writing into the working tree, otherwise mark
  `NOT_VERIFIABLE`.

## 5. Reachability probe (required)

This is the check that the whole incident turned on. Run it yourself; do not
take anyone's word.

Call `run_p0_cost_synthetic` directly (not through the CLI, so no authorization
is involved) with `authorized=True`, an explicit `out_dir` pointing at a fresh
tmp directory outside the formal roots, and a probe decoder that raises a
unique sentinel on its first invocation. The expected outcome is the sentinel,
with exactly one probe call and an empty tmp directory.

Then confirm: P0 and G2 formal roots still absent; the Model-F root still
exactly two files with unchanged size and mtime.

Report the literal result. If it fails, that is a blocking finding and the fix
is not effective.

## 6. Assess the worktree state finding (do not repair it)

A read-only check by the packet author found that at `2026-09-07T17:22:29`
every tracked file's mtime changed, and `git status` now reports roughly 1887
tracked files as modified while `git diff` reports **no textual content
difference** for them — the differences are line-ending representation only.
The `.git/config` predates today, and earlier in the same day the tracked tree
was observed clean.

Establish independently, read-only:

- How many tracked paths are flagged modified, and how many have real content
  changes (`git diff --numstat` and `git diff --ignore-cr-at-eol`).
- Whether the fix commit `299416ae` itself carries any line-ending-only churn,
  or is confined to its five intended files.
- Whether `test_T1_22_openspec_history_zero_mod` fails because of this and for
  no other reason, and whether it failed for this reason before `299416ae`.
- Whether any scientific artifact, frozen constant, or committed evidence is
  affected. State plainly whether this is cosmetic or substantive.

Then judge: **does this block a new P0 authorization?** The R2 execution packet
carries an `E6 clean tracked tree` gate that this state fails. Recommend either
(a) scoping such cleanliness gates to real content differences, or (b) a
repository-side normalization — and say which you would require, and why. Do
not perform either.

## 7. Deliverable

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/LOADER_FIX_REVIEW_R1.md`

Numbered checks with `PASS` / `FAIL` / `NOT_VERIFIABLE`; the reachability probe
result verbatim; the `sys.modules` risk assessment; the test-coverage
assessment; the worktree-state finding and your recommendation; a pre/post stat
snapshot of the protected roots; an explicit statement of what you did and did
not execute; and a closing verdict.

Verdict, exactly one of:

- `LOADER_FIX_REVIEW_PASS` — the fix is correct and in scope, and the
  repository is fit for a new P0 authorization. State any conditions that must
  hold at authorization time. State plainly that this is not itself an
  authorization.
- `LOADER_FIX_REVIEW_FAIL` — name the blocking findings and the single set of
  changes required before re-review.

State the strongest claim your evidence supports, and list what is not claimed:
no FER, no leakage, no key rate, no qualification, no method verdict, and **no
prediction that P0 will now complete** — reachability is not completion.

## 8. Report back

In your message: the verdict, a brief per-check table, the literal reachability
output, the `sys.modules` risk judgment in one or two sentences, the worktree
finding with your recommendation, the literal pytest line, and this line if it
is still true:

「P0 未授权、未执行；正式根仍不存在；next_gate 仍为 P0_PACKET_REVIEW。」
