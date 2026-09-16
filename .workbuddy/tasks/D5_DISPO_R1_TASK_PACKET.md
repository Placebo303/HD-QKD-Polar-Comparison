# TASK PACKET — D5-DISPO-R1: unauthorized G1 disposition + evidence landing

Target executor: low-capability session (weak model). Follow this file
literally. Do NOT improvise. Do NOT optimize. Do NOT "clean up" anything that
is not listed.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean` (do NOT create, switch, or rename branches)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle after this packet: `MODEL_F_INPUT_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- This packet performs: documentation + git commit ONLY.

---

## 0. HARD PROHIBITIONS (violating any one = STOP and report)

You MUST NOT:

1. Run any decoder. No `bind_historical_decoder`, no `decode_row_layered_fftqspa`.
2. Run `scripts/v72p2d5_gf32_rate_mother.py` with `--phase p0-cost|g1|g2`.
3. Run `scripts/v72p2d5_prepare_model_f_input.py` at all (prepare OR verify).
4. Read CAL / VAL / raw parquet rows. `pd.read_parquet` is forbidden.
5. Delete, move, rename, copy, normalize, hash, or open-for-write ANY file under:
   - `workspace/v72p2d5_g1/20260906_r1/`
   - `workspace/v72p2d5_model_f_input/20260907_r1/`
   - `workspace/v72p2d5_g0/20260905_r2/`
   - `workspace/v72p2d5_g0_recovery/20260906_r1/`
   - `workspace/v72p2d5_structure/`
   Read-only `stat` and `json.load` are allowed.
6. Create `workspace/v72p2d5_p0_cost/...` or `workspace/v72p2d5_g2/...`. They must
   stay absent.
7. Change ANY `*_execution_authorized` value in
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`.
   Every one of them stays `false`.
8. `git push`, `git reset`, `git stash`, `git checkout --`, `git clean`,
   `git rebase`, `git commit --amend`.
9. Edit any `.py` file. Zero code changes in this packet.
10. Write `RESULT_SUMMARY.md`, `OPERATOR_RETURN.md`, or any `run_01`.
11. Claim any scientific result: no FER, no leakage, no SKR, no "G1 failed",
    no "method does not work", no P0 authorization.

If any instruction below appears ambiguous or a check fails: STOP, write nothing
further, and report the exact failing step number and literal output.

---

## 1. Background you need (frozen facts, do not re-derive)

- The independent Pre-RESULT review
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`
  returned `PRE_RESULT_REVIEW_FAIL`. The single blocking check is **PR16**:
  `workspace/v72p2d5_g1/20260906_r1/` exists with `decoder_calls=440` while
  `g1_execution_authorized=false` and `next_gate=P0_PACKET_REVIEW`.
- The cause is a test-isolation defect, recorded in
  `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` (I01–I12).
- The test-isolation repair is already DONE and verified
  (`TEST_ISOLATION_REWORK_EVIDENCE_R1.md`): 165 collected, 165 passed.
- The Model-F artifact itself passed every content check (PR01–PR15, PR17–PR23).
- **User decision (authoritative, 2026-09-07):** the unauthorized G1 root is
  disposed as **KEEP IN PLACE, RECORDED AS VOID**. No delete. No move. No rename.
- **User decision (authoritative, 2026-09-07):** commit the currently untracked /
  modified D5 work locally. **Do NOT push.**

---

## 2. STEP 1 — Read-only pre-state snapshot

Run exactly these, and save the literal output; you will paste it into the
record file in Step 2.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
```

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib, json
for r in ['workspace/v72p2d5_g1/20260906_r1','workspace/v72p2d5_model_f_input/20260907_r1','workspace/v72p2d5_g0/20260905_r2','workspace/v72p2d5_g0_recovery/20260906_r1','workspace/v72p2d5_p0_cost/20260906_r1','workspace/v72p2d5_g2/20260906_r1']:
    p = pathlib.Path(r)
    print('ROOT', r, 'exists', p.exists())
    if p.exists():
        for f in sorted(p.iterdir()):
            st = f.stat()
            print('  ', f.name, st.st_size, st.st_mtime_ns)
"
```

**Expected (must match, else STOP):**
- `workspace/v72p2d5_g1/20260906_r1` exists True, 4 files:
  `execution_summary.json` 267, `report.md` 146, `results.json` 2593, `table.csv` 126.
- `workspace/v72p2d5_model_f_input/20260907_r1` exists True, 2 files:
  `model_f_input.npz` 208467, `model_f_input_summary.json` 752.
- `workspace/v72p2d5_g0/20260905_r2` exists True, 4 files (385/712/2512/306).
- `workspace/v72p2d5_g0_recovery/20260906_r1` exists True, 4 files (404/722/2531/306).
- `workspace/v72p2d5_p0_cost/20260906_r1` exists **False**.
- `workspace/v72p2d5_g2/20260906_r1` exists **False**.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -n "execution_authorized\|next_gate\|scientific_promotion" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```

**Expected:** every `*_execution_authorized` is `false`;
`next_gate: P0_PACKET_REVIEW`; `scientific_promotion: false`. If any is `true`, STOP.

---

## 3. STEP 2 — Create the disposition record (ONE new file)

Create exactly one new file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_UNAUTHORIZED_DISPOSITION_R1.md`

Content template — fill the bracketed slots with the literal Step 1 output. Do
not add sections, do not add conclusions, do not soften the wording.

```markdown
# G1 unauthorized output disposition R1 — 20260907

Decision authority: user, 2026-09-07, explicit.
Disposition: `VOID_RETAINED_IN_PLACE`.
Scope: documentation only. No delete, no move, no rename, no copy, no hash,
no rerun, no authorization change, no code change.

## D01 Subject

Root: `workspace/v72p2d5_g1/20260906_r1/`
Files (stat only, pre- and post-disposition identical):

| file | size_bytes | mtime_ns |
| --- | --- | --- |
| execution_summary.json | 267 | [PASTE] |
| report.md | 146 | [PASTE] |
| results.json | 2593 | [PASTE] |
| table.csv | 126 | [PASTE] |

## D02 Status

`INVALID_UNAUTHORIZED_TEST_TRIGGERED` (unchanged from
`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` I01).
Now additionally and permanently marked `VOID`.

## D03 What VOID means

- The four files are retained as forensic evidence of the isolation defect only.
- They carry NO scientific meaning. The contained `decoder_calls=440`,
  `app_exact 0`, `app_failure 1.0`, `oracle 0` are NOT a G1 result, NOT a
  performance measurement, NOT an `exact_failure_fraction` verdict, and NOT
  evidence about the NB-LDPC method, the dv3 mother, the rate points, or the
  Model-F prior.
- They MUST NOT be cited by any future RESULT_SUMMARY, report, table, decision
  entry, or promotion argument.
- They do NOT consume, satisfy, or partially satisfy any G1 authorization.
- A future authorized G1 run MUST use a NEW output root and MUST NOT reuse,
  compare against, or overwrite this one.

## D04 Why retained in place

`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` I08 commits to no
delete/quarantine/move/rename/copy/normalize/hash. Retention in place is the
only disposition consistent with that commitment and with repository
failure-retention practice. Deletion and relocation were both explicitly
rejected by the user on 2026-09-07.

## D05 Root cause status

Test-isolation defect (incident I09). Repair completed and independently
evidenced in `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`: SAFE A/B/C containment,
stdlib AST static guard, 165 collected / 165 passed, focused 10 passed, zero
binder entries, zero writer entries, P0/G2 roots still absent.

## D06 Lifecycle effect

- `g1_execution_authorized` stays `false`.
- `next_gate` stays `P0_PACKET_REVIEW`.
- `scientific_promotion` stays `false`.
- No P0 authorization is granted or implied by this disposition.
- PR16 of `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` is addressed by RECORD, not by
  removal. Whether PR16 is thereby cleared is decided by an independent
  Pre-RESULT re-review, not by this file and not by the executing session.

## D07 Verification after disposition

Re-stat performed; the four G1 files, the two Model-F files, and both G0 roots
are byte-size and mtime identical to the pre-disposition snapshot. P0 and G2
roots remain absent.

[PASTE post-disposition stat output here]
```

**Do not** edit `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md`.
**Do not** edit `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`.

---

## 4. STEP 3 — Append one decision-log entry

Append to the END of `docs/decision-log.md` (append only; do not modify any
existing line):

```markdown

---

### 2026-09-07: V72P2D5 unauthorized G1 output disposed VOID_RETAINED_IN_PLACE (docs only)

**Decision**: Dispose `workspace/v72p2d5_g1/20260906_r1/` (4 files,
`decoder_calls=440`) as `VOID_RETAINED_IN_PLACE`. Retained unmodified as
forensic evidence of a test-isolation defect; permanently barred from citation
as a G1 result, a performance measurement, or evidence about the NB-LDPC
method. No delete, no move, no rename, no rerun, no authorization change.

**Context**: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` returned
`PRE_RESULT_REVIEW_FAIL` on the single blocker PR16 — the G1 formal root existed
while `g1_execution_authorized=false` and `next_gate=P0_PACKET_REVIEW`. Cause is
incident I09 (tests called `run_g1_synthetic(authorized=True)` without fake
decoder / injected arrays / tmp `out_dir`, so once the Model-F artifact existed
the production decoder bound and the default writer hit the formal root).
Model-F artifact content itself passed PR01-PR15 and PR17-PR23. The isolation
repair is complete and evidenced (165 collected / 165 passed).

**Alternatives considered**:
- Delete the four files: rejected — irreversible, breaks the evidence chain.
- Move to a quarantine directory: rejected — violates incident I08
  (no move/rename/copy).

**Consequences**: All `*_execution_authorized` stay false; `next_gate` stays
`P0_PACKET_REVIEW`; no P0 authorization. PR16 is addressed by record only —
clearance requires an independent Pre-RESULT re-review. A future authorized G1
run must use a new output root and must not reuse or compare against this one.
```

---

## 5. STEP 4 — Append one memory entry

Append to the END of `AGENT_PROJECT_MEMORY.md`:

```markdown
## 2026-09-07 V72P2D5 unauthorized G1 output VOID_RETAINED_IN_PLACE (docs-only disposition)

- Disposition [decision]: `workspace/v72p2d5_g1/20260906_r1/` (4 files,
  `decoder_calls=440`, app_exact 0, app_failure 1.0, oracle 0) is
  `VOID_RETAINED_IN_PLACE` — retained unmodified as forensic evidence only,
  barred from citation as a G1 result, performance measurement, or method
  evidence; delete and quarantine-move both rejected (incident I08).
- Blocker [repo-observed]: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` =
  `PRE_RESULT_REVIEW_FAIL`, sole blocker PR16 (G1 root exists while
  `g1_execution_authorized=false`, `next_gate=P0_PACKET_REVIEW`); Model-F
  artifact content PASS on PR01-PR15 and PR17-PR23.
- Root cause [repo-observed]: incident I09 test-isolation defect; repair
  complete per `TEST_ISOLATION_REWORK_EVIDENCE_R1.md` (SAFE A/B/C + AST static
  guard, 165 collected / 165 passed, focused 10 passed, binder/writer entries 0,
  P0/G2 roots absent).
- Lifecycle [decision]: all `*_execution_authorized` stay false;
  `scientific_promotion=false`; `next_gate=P0_PACKET_REVIEW`; PR16 addressed by
  record only, clearance needs independent Pre-RESULT re-review; a future
  authorized G1 run needs a new output root, no reuse or comparison.
```

---

## 6. STEP 5 — Verification gates (all must pass before Step 6)

Run each and record the literal result.

**G01 — compile clean (no code was changed; this is a regression guard):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_prepare_model_f_input.py && echo COMPILE_OK
```
Expected: `COMPILE_OK`.

**G02 — focused suite (the isolation tests):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py -p no:cacheprovider --basetemp workspace/v72p2d5_dispo_r1_20260907d01 -q
```
Expected literal: `165 passed`. Any failure → STOP.

**G03 — roots unchanged after tests:** re-run the Step 1 stat command. Every
size and `mtime_ns` must equal the Step 1 values. `p0_cost` and `g2` still absent.

**G04 — no authorization drift:** re-run the Step 1 `grep`. All `false`,
`next_gate: P0_PACKET_REVIEW`.

**G05 — scope check:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 -- "*.py"
```
Expected: only the pre-existing `M comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
`M comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`,
`M scripts/v72p2d5_gf32_rate_mother.py`, plus untracked
`?? comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`,
`?? comparison_bench/tests/test_v72p2d5_model_f_input.py`,
`?? scripts/v72p2d5_prepare_model_f_input.py`.
No other `.py` entry may appear. If one does, STOP.

---

## 7. STEP 6 — Commit (local only, NO PUSH)

Stage ONLY the paths listed. Never use `git add -A`, `git add .`, or `git commit -a`.

**Commit 1 — Model-F input implementation candidate:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_prepare_model_f_input.py comparison_bench/tests/test_v72p2d5_model_f_input.py openspec/changes/formal-ir-v72p2d5-model-f-input-preparation && git status --porcelain=v1
```
Review the staged list, then:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "feat(v72p2d5): Model-F CAL-TRAIN input candidate + prepare/verify runner, no execution

Implement-only candidate: builder/writer/reader, prepare-verify CLI with
authorization choke, PX11 repo-root parquet path resolver, focused tests.
No CAL/VAL row read, no decoder, no P0/G1/G2 execution, no authorization change.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Commit 2 — P0/G1/G2 candidate + test isolation repair:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py openspec/changes/v72p2d5-p0-g1-g2-production-path && git status --porcelain=v1
```
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "feat(v72p2d5): P0/G1/G2 per-f mother-prefix candidate + test isolation repair, no execution

Per-f H1[:m1(f)]/H2[:m2(f)] prefix slicing from one mother per layer/width,
stage builders, gated CLI phases, four-file no-overwrite writers.
Test containment SAFE A/B/C plus stdlib AST static guard.
No decoder run, no P0/G1/G2 authorization, no formal output created.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Commit 3 — cycle documentation and disposition:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan openspec/project.md docs/decision-log.md AGENT_PROJECT_MEMORY.md && git status --porcelain=v1
```
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "docs(v72p2d5): dispose unauthorized G1 output VOID_RETAINED_IN_PLACE

Record the Pre-RESULT R1 FAIL blocker PR16, the isolation incident and its
repair evidence, and the user disposition: G1 root retained unmodified as
forensic evidence, barred from citation as a result. All execution
authorizations remain false; next_gate stays P0_PACKET_REVIEW.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Then verify and STOP:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git log --oneline -4 && git status -sb | head -3
```
Expected: 3 new commits, branch ahead of origin by 3. **Do not push.**

---

## 8. STEP 7 — Final report (message only, create no further files)

Report exactly:

1. The literal Step 1 and G03 stat tables, and whether they are identical.
2. `COMPILE_OK` yes/no; the literal pytest line.
3. The three commit SHAs and `git status -sb`.
4. Confirmation of every one of these, as `true`/`false`:
   - decoder run: false
   - CAL/VAL/parquet rows read: false
   - files deleted/moved/renamed under any `workspace/v72p2d5_*` root: false
   - `p0_cost` / `g2` roots created: false
   - any `*_execution_authorized` changed: false
   - `RESULT_SUMMARY` / `OPERATOR_RETURN` / `run_01` created: false
   - pushed: false
5. State plainly: **PR16 is addressed by record only; the Model-F Pre-RESULT
   re-review has NOT been performed and P0 is NOT authorized.**

Do not draw any scientific conclusion. Do not propose the next experiment.
