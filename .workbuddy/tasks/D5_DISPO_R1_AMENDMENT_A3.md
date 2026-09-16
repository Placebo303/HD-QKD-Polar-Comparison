# AMENDMENT A3 to TASK PACKET D5-DISPO-R1 — STEP 6 / STEP 7 audit fixes

Issued: 2026-09-07, by the packet author, after auditing the remaining steps
for the same class of defect that caused the G05 and G06 false STOPs
(hardcoded absolute expectations instead of self-anchored relative ones).

Applies to `.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md` as amended by A1 and
A2. Everything stays in force EXCEPT what this file supersedes.

Five defects were found in STEP 6 / STEP 7. Two of them (A3.1, A3.2) would
have caused a guaranteed false STOP. All are fixed below. This amendment adds
no new restriction and removes no safeguard.

---

## A3.1 SUPERSEDED — A1.4 / G07 literal-list trap

A1's G07 said to STOP if `git diff --cached --name-only` contains "any path
that is not in that commit's `git add` whitelist". The whitelists contain
**directories**; the staged listing expands them into individual files. Read
literally, G07 fires on every legitimate file inside a whitelisted directory.

Author-measured `git add --dry-run` (read-only, index untouched):
commit 1 stages 7 files, commit 2 stages 7 files, commit 3 stages 20 files.

**G07' replacement rule:** a staged path is IN SCOPE if it equals a whitelist
entry, **or** is a descendant of a whitelist entry that is a directory. STOP
only on a staged path that satisfies neither.

Run this after each `git add`, before the matching `git commit`:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, sys
allow = sys.argv[1:]
staged = subprocess.run(['git','diff','--cached','--name-only'],capture_output=True,text=True).stdout.split()
bad = [p for p in staged if not any(p == a or p.startswith(a.rstrip('/') + '/') for a in allow)]
print('STAGED_COUNT', len(staged))
for p in staged: print('  ', p)
print('OUT_OF_SCOPE', bad)
print('G07_OK' if not bad else 'G07_FAIL')
" <WHITELIST ENTRIES OF THIS COMMIT, SPACE-SEPARATED, SAME AS ITS git add>
```

Pass the exact same path arguments you passed to that commit's `git add`.
Expected: `OUT_OF_SCOPE []` and `G07_OK`.
Author-measured expected `STAGED_COUNT`: commit 1 = 7, commit 2 = 7,
commit 3 = 20. A different count is not itself a failure — `OUT_OF_SCOPE` is
the verdict — but report the count.

On `G07_FAIL`: STOP, do not commit, do not unstage, do not clean. Leaving the
index staged is the correct state to stop in. Report and wait.

## A3.2 RULING — commit 3 legitimately stages 20 files

The executor's own deltas are 3 files. Commit 3 stages 20. **This is correct
and expected, not a violation.** The commit-3 whitelist deliberately includes
the whole cycle folder and the D5 plan OpenSpec, so it also lands pre-existing
uncommitted cycle documentation that has never been committed.

Author-verified breakdown of the 20:

- Executor-authored this task (1): `G1_UNAUTHORIZED_DISPOSITION_R1.md`.
- Executor-appended this task (2): `docs/decision-log.md`,
  `AGENT_PROJECT_MEMORY.md`.
- Pre-existing modified (6): `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`,
  `openspec/project.md`, and the four
  `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/` files
  (`design.md`, `proposal.md`, `specs/spec.md`, `tasks.md`).
- Pre-existing untracked cycle documentation (11): `G0_PROCEDURAL_RECOVERY_PACKET.md`,
  `G0_RECOVERY_AMENDMENT.md`, `G0_RECOVERY_PRE_EXECUTE_REVIEW.md`,
  `G0_RECOVERY_PRE_RESULT_REVIEW.md`, `IMPLEMENTATION_REVIEW.md`,
  `MODEL_F_INPUT_PRE_EXECUTE_PACKET.md`, `MODEL_F_INPUT_PRE_EXECUTE_REVIEW.md`,
  `MODEL_F_INPUT_PRE_EXECUTE_REVIEW_R2.md`, `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`,
  `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`,
  `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`.

All 20 are cycle evidence that belongs in the repository. `cycle_state.yaml`'s
diff was verified in A1.0: it only records G0-recovery acceptance and advances
`next_gate` to `P0_PACKET_REVIEW`; all nine `*_execution_authorized` stay
`false`. Do not exclude anything, do not split the commit, do not unstage.

## A3.3 SUPERSEDED — commit 3 message

The original commit-3 message described only the G1 disposition and understated
what the commit contains. Use this message instead; the `git add` line is
unchanged.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "docs(v72p2d5): land cycle evidence + dispose unauthorized G1 output VOID_RETAINED_IN_PLACE

Commit the V72P2D5 cycle documentation that had never been committed: G0
recovery packet/amendment/reviews, implementation review, Model-F input
pre-execute packet and reviews R1/R2, Model-F pre-result review R1, test
isolation rework evidence R1, and the unauthorized G1 execution incident.
Also lands the D5 plan OpenSpec revisions, the roadmap note in project.md, and
the cycle_state record of G0-recovery acceptance with next_gate advanced to
P0_PACKET_REVIEW.

New this change: the user disposition of the unauthorized G1 output as
VOID_RETAINED_IN_PLACE — retained unmodified as forensic evidence of a test
isolation defect, barred from citation as a G1 result or performance
measurement — plus the matching decision-log and project-memory entries.

All nine execution authorizations remain false; scientific_promotion remains
false; next_gate stays P0_PACKET_REVIEW. No decoder run, no CAL/VAL read, no
code change, no result acceptance, no P0 authorization.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

## A3.4 CLARIFICATION — expected benign output

None of the following is a failure. Do not STOP on any of them:

- `warning: in the working copy of '<file>', LF will be replaced by CRLF the
  next time Git touches it` — normal on Windows, emitted by `git add`/`git diff`.
- `PytestConfigWarning: Unknown config option: cache_dir` — known benign.
- The pytest `--basetemp` directory `workspace/v72p2d5_dispo_r1_*` existing
  under `workspace/`. Creating it is allowed; packet §0 item 5 protects five
  named roots (`v72p2d5_g1/20260906_r1`, `v72p2d5_model_f_input/20260907_r1`,
  `v72p2d5_g0/20260905_r2`, `v72p2d5_g0_recovery/20260906_r1`,
  `v72p2d5_structure`), not every path matching `workspace/v72p2d5_*`. It is
  not staged by any whitelist and must stay uncommitted.
- Either shell is acceptable. Where a command uses `head`, `grep` or similar
  POSIX tools, a semantically identical PowerShell form is fine; say so in the
  report.

## A3.5 SUPERSEDED — STEP 7 items 1 and 2

The original STEP 7 asks for the literal STEP 1 stat table. The resuming
session does not hold it, and re-deriving it is unnecessary: G03 was already
ruled PASS by the packet author in A2.1 against the executor's own STEP 1
report.

Replace STEP 7 items 1 and 2 with:

1. State that G03 was ruled PASS by amendment A2.1 and cite it. Do not
   reproduce the STEP 1 table. Report the current `workspace/` root states you
   observed (g1 4 files, model_f_input 2 files, both G0 roots present,
   `p0_cost` and `g2` absent).
2. Report the `COMPILE_OK` and the literal pytest line from the most recent run
   in your own session. If you did not run them in this session because A2.4
   said not to re-run, say so and cite the accepted values
   (`COMPILE_OK`, `165 passed`).

STEP 7 items 3, 4 and 5 are unchanged, including the closing sentence, which
must still be written verbatim.

---

## A3.6 Audit result for the remaining steps

Checked for the hardcoded-absolute-expectation defect class:

- STEP 6 commit 1 whitelist: verified by dry-run, 7 files, all in scope. OK.
- STEP 6 commit 2 whitelist: verified by dry-run, 7 files, all in scope. OK.
- STEP 6 commit 3 whitelist: 20 files, ruled correct in A3.2. OK.
- STEP 6 final verify (`git log --oneline -4`, branch ahead by 3): the "3" is
  produced by this task itself, not hand-picked. OK.
- G01, G02, G04, G05', G06': self-anchored or task-produced. OK.
- Commit messages: commit 1 and 2 accurate; commit 3 replaced in A3.3.
- No further hardcoded worktree-wide assertions remain in the packet.

No other defects found.
