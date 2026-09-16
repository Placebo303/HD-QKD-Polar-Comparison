# TASK PACKET — D5-MODELF-ACCEPT-R1: main-thread acceptance of the Model-F input

Target executor: low-capability session. Follow this file literally. Do NOT
improvise, do NOT optimize, do NOT clean up anything not listed.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean` (do NOT create, switch, or rename)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Change: `formal-ir-v72p2d5-model-f-input-preparation`
- This packet performs: documentation + one local git commit ONLY.
- Lifecycle after this packet: Model-F input `ACCEPTED`; `next_gate` stays
  `P0_PACKET_REVIEW`; every `*_execution_authorized` stays `false`.

---

## 0. HARD PROHIBITIONS (violating any one = STOP and report)

You MUST NOT:

1. Run any decoder.
2. Run `scripts/v72p2d5_gf32_rate_mother.py` with `--phase p0-cost|g1|g2`.
3. Run `scripts/v72p2d5_prepare_model_f_input.py` at all (prepare OR verify).
   Its authorization was consumed on 2026-09-07; replay is forbidden.
4. Read CAL / VAL / raw parquet rows. `pandas.read_parquet` is forbidden.
5. Delete, move, rename, copy, normalize, hash, or open-for-write anything
   under `workspace/`. `stat` and `json.load` read-only are allowed.
   **In particular: do NOT edit `model_f_input_summary.json` and do NOT rewrite
   `model_f_input.npz`.** See §1 item 4 for why its status stays `CANDIDATE`.
6. Create `workspace/v72p2d5_p0_cost/...` or `workspace/v72p2d5_g2/...`.
7. Set ANY `*_execution_authorized` to `true`. All nine stay `false`.
   Do NOT change `next_gate`; it stays `P0_PACKET_REVIEW`.
8. `git push`, `git reset`, `git stash`, `git checkout --`, `git clean`,
   `git rebase`, `git commit --amend`, `git add -A`, `git add .`,
   `git commit -a`.
9. Edit any `.py`. Zero code changes.
10. Edit any existing review file, incident file, evidence file, or OpenSpec
    file. The only existing files you may touch are the three named in §3, §4
    and §5.
11. Write `RESULT_SUMMARY.md`, `OPERATOR_RETURN.md`, or any `run_01`.
12. Claim a scientific result: no FER, no leakage, no SKR, no method verdict,
    no G1 performance conclusion, no P0 authorization.

If any instruction is ambiguous or a check fails: STOP, write nothing further,
report the failing step number and the literal output.

---

## 1. Background (frozen; do not re-derive, do not re-litigate)

1. The independent Pre-RESULT re-review
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md`
   returned `PRE_RESULT_REVIEW_PASS` /
   `READY_FOR_MAIN_RESULT_ACCEPTANCE`, with C01–C11 all PASS and
   `195 passed` tests.
2. That readiness signal is **not** an acceptance. This packet performs the
   acceptance, which is a separate main-thread act.
3. **PR16 was cleared by RECORD, not by the original condition being met.**
   R1's PR16 was the formal check "formal roots absent"; the G1 root still
   exists. R2 reinterpreted PR16 by its intent — unauthorized numbers must not
   enter the result chain — and judged that intent closed by the
   `VOID_RETAINED_IN_PLACE` disposition. This distinction MUST be written into
   the acceptance record; do not paraphrase it away.
4. The artifact's own `status` field stays `MODEL_F_INPUT_CANDIDATE`. Editing
   it would require rewriting a file inside a protected immutable root, which
   is forbidden. Acceptance is recorded at the **cycle** level instead. The
   loader already accepts both `CANDIDATE` and `ACCEPTED`, so nothing breaks.
5. Two residual risks carried forward from R2, to be repeated verbatim in the
   acceptance record and the decision-log entry:
   - `R-R1`: production-side bare-authorized defaults are unchanged; the
     recurrence guard is test-side only. Future P0/G1/G2 packets must
     re-verify isolation.
   - `R-R2`: `M24`/`P12` no longer assert global formal-root absence
     (lifecycle-independent snapshots instead); an unexpected new formal output
     would rely on per-test snapshot comparison, not a global gate.

---

## 2. STEP 1 — Read-only pre-state snapshot

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git status -sb | head -1
```
Expected: branch `formal-ir-v72p1-addendum-clean`, HEAD `20204726`, `ahead 3`.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib
for r in ['workspace/v72p2d5_g1/20260906_r1','workspace/v72p2d5_model_f_input/20260907_r1','workspace/v72p2d5_g0/20260905_r2','workspace/v72p2d5_g0_recovery/20260906_r1','workspace/v72p2d5_p0_cost/20260906_r1','workspace/v72p2d5_g2/20260906_r1']:
    p=pathlib.Path(r)
    print('ROOT', r, 'exists', p.exists())
    if p.exists():
        for f in sorted(p.iterdir()):
            st=f.stat(); print('  ', f.name, st.st_size, st.st_mtime_ns)
"
```
Save this output; you will re-run it as G03. Expected: g1 4 files
(267/146/2593/126), model_f_input 2 files (208467/752), g0 4 files
(385/712/2512/306), g0_recovery 4 files (404/722/2531/306), `p0_cost` and `g2`
absent.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -nE "execution_authorized|scientific_promotion|next_gate" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Expected: nine `false`, `scientific_promotion: false`,
`next_gate: P0_PACKET_REVIEW`. If any is `true`, STOP.

---

## 3. STEP 2 — Create the acceptance record (ONE new file)

Create exactly one new file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md`

Use this content verbatim, filling only the bracketed slots from your STEP 1
output. Do not add sections. Do not add conclusions. Do not soften the wording.

```markdown
# Model-F input result acceptance R1 — 20260907

Decision authority: user, 2026-09-07, explicit.
Verdict: `MODEL_F_INPUT_RESULT_ACCEPTED`.
Scope: documentation + cycle-state record only. No execution, no
authorization, no promotion, no artifact modification.

## A01 Subject accepted

Artifact root: `workspace/v72p2d5_model_f_input/20260907_r1/`

| file | size_bytes | mtime_ns |
| --- | --- | --- |
| model_f_input.npz | 208467 | [PASTE] |
| model_f_input_summary.json | 752 | [PASTE] |

Content: canonical Model-F CAL-TRAIN input, full-CAL refit after the frozen
lambda selection. `CAL702..1725`, 1024 frames x 256 pairs = 262144 symbols,
`counts_ab` int64 `(1024,1024)` axis `(Alice,Bob)`, `p_b` float64 `(1024,)`
derived from `axis0`, `lambda_star=137.3823795883264`.

## A02 Basis of acceptance

- Implementation acceptance: `IMPLEMENTATION_ACCEPTANCE_R2.md`.
- Pre-EXECUTE review: `MODEL_F_INPUT_PRE_EXECUTE_REVIEW_R2.md`, PASS
  (PX01-PX20 after the PX11 path fix; the prior R1 FAIL is preserved).
- Execution: exactly one authorized `prepare` plus one authorized `verify`,
  2026-09-07. Authorization consumed; replay forbidden.
- Pre-RESULT review R1: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`,
  `PRE_RESULT_REVIEW_FAIL` on the single blocker PR16. Preserved, not deleted.
- Disposition: `G1_UNAUTHORIZED_DISPOSITION_R1.md`, `VOID_RETAINED_IN_PLACE`.
- Pre-RESULT review R2: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md`,
  `PRE_RESULT_REVIEW_PASS` / `READY_FOR_MAIN_RESULT_ACCEPTANCE`, C01-C11 all
  PASS, `195 passed`.

## A03 PR16 was cleared by record, not by condition

This is the material caveat of this acceptance and must not be summarised away.

R1's PR16 was the formal check "formal roots absent". That condition is NOT
met: `workspace/v72p2d5_g1/20260906_r1/` still exists on disk. R2 cleared PR16
by reinterpreting it through its intent — unauthorized numbers must not enter
the result chain — and judging that intent closed by the
`VOID_RETAINED_IN_PLACE` disposition (retention as forensic evidence, absolute
citation ban, new-root requirement for any future authorized G1, unchanged
lifecycle).

Anyone reading this record later must understand: PR16 was not physically
cleared. A rule was reinterpreted, under an explicit user decision that
rejected both deletion and quarantine-move.

## A04 What is accepted

Accepted: the frozen Model-F CAL input is internally consistent, canonically
oriented `(Alice,Bob)`, with an exactly derived `P(B)` marginal, and is
suitable as the P0/G1/G2 prior input.

## A05 What is NOT accepted and NOT claimed

No FER. No leakage. No secret-key rate. No net key. No qualification. No
verdict on NB-LDPC or the dv3 mother. No G1 performance conclusion — the voided
`app_exact 0` / `app_failure 1.0` / `oracle 0` numbers carry zero scientific
meaning. No P0/G1/G2 authorization. No scientific promotion.

## A06 Artifact status field unchanged

The artifact's `status` stays `MODEL_F_INPUT_CANDIDATE`. Changing it would
require rewriting a file inside a protected immutable root, which is forbidden.
Acceptance is recorded at the cycle level in `cycle_state.yaml`. The loader
accepts both `CANDIDATE` and `ACCEPTED`, so no consumer breaks.

## A07 Residual risks carried into P0

- `R-R1`: production-side bare-authorized defaults are unchanged; the
  recurrence guard is test-side only. Future P0/G1/G2 packets MUST re-verify
  isolation before any authorization.
- `R-R2`: `M24`/`P12` no longer assert global formal-root absence
  (lifecycle-independent snapshots instead); an unexpected new formal output
  would rely on per-test snapshot comparison, not a global gate.

## A08 Lifecycle effect

- Model-F input: `ACCEPTED`.
- All nine `*_execution_authorized`: `false`, unchanged.
- `scientific_promotion`: `false`, unchanged.
- `next_gate`: `P0_PACKET_REVIEW`, unchanged.
- P0 is NOT authorized by this acceptance. P0, G1 and G2 each require their own
  packet review and their own separate explicit authorization.

## A09 Post-acceptance verification

[PASTE the G03 stat output here]

Protected roots unchanged; `p0_cost` and `g2` still absent.
```

---

## 4. STEP 3 — Edit `cycle_state.yaml` (additive lines only)

Open `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`.

**Insert** the following block immediately AFTER the line
`g0_recovery_accepted: true` and BEFORE the line
`p0_cost_execution_authorized: false`:

```yaml
model_f_input_prepared: true
model_f_input_pre_execute_review: PASS_R2
model_f_input_pre_result_review: PASS_R2
model_f_input_accepted: true
model_f_input_root: workspace/v72p2d5_model_f_input/20260907_r1
model_f_input_artifact_status: MODEL_F_INPUT_CANDIDATE
g1_unauthorized_output_disposition: VOID_RETAINED_IN_PLACE
```

**Append** these two comment lines at the END of the file:

```yaml
# Acceptance 20260907: MODEL_F_INPUT_RESULT_ACCEPTED per MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md; PR16 cleared BY RECORD not by condition (G1 root still present, dispositioned VOID_RETAINED_IN_PLACE).
# Residual risks carried into P0: R-R1 prod-side bare-authorized defaults unchanged (test-side guard only); R-R2 no global formal-root absence gate (per-test snapshots instead).
```

**Change nothing else.** Do not touch any `*_execution_authorized` line. Do not
touch `next_gate`. Do not reorder, reformat, or reindent existing lines.

Verify immediately after editing:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -cE "execution_authorized: false" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml && grep -nE "execution_authorized: true|next_gate" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Expected: count `9`; no `true` line; `next_gate: P0_PACKET_REVIEW`. Otherwise STOP.

---

## 5. STEP 4 — Append one decision-log entry

Append to the END of `docs/decision-log.md` (append only):

```markdown

---

### 2026-09-07: V72P2D5 Model-F input result ACCEPTED (docs only, no authorization)

**Decision**: Accept the canonical Model-F CAL-TRAIN input at
`workspace/v72p2d5_model_f_input/20260907_r1/` as the P0/G1/G2 prior input.
Record acceptance at the cycle level; the artifact's own `status` stays
`MODEL_F_INPUT_CANDIDATE` because rewriting a file inside a protected
immutable root is forbidden and the loader accepts both values.

**Context**: Implementation accepted; Pre-EXECUTE R2 PASS after the PX11 path
fix; exactly one authorized `prepare` plus one `verify` executed 2026-09-07
(authorization consumed); Pre-RESULT R1 FAILed on the single blocker PR16;
the unauthorized G1 root was dispositioned `VOID_RETAINED_IN_PLACE`; the
independent Pre-RESULT R2 returned PASS with C01-C11 all PASS and `195 passed`.

**Material caveat**: PR16 was cleared BY RECORD, not by condition. R1's PR16
was the formal check "formal roots absent"; that condition is still not met —
`workspace/v72p2d5_g1/20260906_r1/` exists. R2 reinterpreted PR16 by its
intent (unauthorized numbers must not enter the result chain) and judged that
intent closed by the disposition. Deletion and quarantine-move were both
explicitly rejected by the user.

**Alternatives considered**:
- Flip the artifact `status` to `ACCEPTED`: rejected — would require rewriting
  inside a protected immutable root.
- Hold acceptance until PR16 is physically cleared: rejected — that would
  require reversing an explicit user decision and adds no scientific
  protection to the Model-F claim.

**Consequences**: All nine `*_execution_authorized` stay `false`;
`scientific_promotion` stays `false`; `next_gate` stays `P0_PACKET_REVIEW`.
P0 is not authorized. Residual risks carried into the P0 packet: `R-R1`
production-side bare-authorized defaults unchanged, recurrence guard is
test-side only, so future P0/G1/G2 packets must re-verify isolation before any
authorization; `R-R2` `M24`/`P12` no longer assert global formal-root absence,
so an unexpected new formal output relies on per-test snapshot comparison
rather than a global gate.
```

---

## 6. STEP 5 — Append one memory entry

Append to the END of `AGENT_PROJECT_MEMORY.md`:

```markdown
## 2026-09-07 V72P2D5 Model-F input RESULT ACCEPTED (docs-only, no authorization)

- Acceptance [decision]: Model-F CAL-TRAIN input
  `workspace/v72p2d5_model_f_input/20260907_r1/` (2 files, `CAL702..1725`,
  1024x256=262144 symbols, `counts_ab` int64 `(1024,1024)` axis `(Alice,Bob)`,
  `p_b` derived from `axis0`, `lambda_star=137.3823795883264`) accepted as the
  P0/G1/G2 prior input; recorded at cycle level, artifact `status` left
  `MODEL_F_INPUT_CANDIDATE` (protected immutable root, loader accepts both).
- Review chain [repo-observed]: implementation accepted; Pre-EXECUTE R2 PASS
  post-PX11; one authorized prepare + one verify, authorization consumed;
  Pre-RESULT R1 FAIL on PR16; disposition `VOID_RETAINED_IN_PLACE`;
  Pre-RESULT R2 PASS, C01-C11 PASS, `195 passed`.
- Caveat [decision]: PR16 cleared BY RECORD not by condition — the G1 root
  still exists; R2 reinterpreted PR16 by intent. Do not later read this as a
  physical clearance.
- Residual [decision]: `R-R1` prod-side bare-authorized defaults unchanged,
  test-side guard only, future P0/G1/G2 packets must re-verify isolation;
  `R-R2` no global formal-root absence gate, per-test snapshots instead.
- Lifecycle [decision]: nine `*_execution_authorized` false,
  `scientific_promotion` false, `next_gate` `P0_PACKET_REVIEW`; P0/G1/G2 each
  need their own packet review and separate explicit authorization.
```

---

## 7. STEP 6 — Verification gates (all must pass before STEP 7)

**G01 — compile (regression guard; no code was changed):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_prepare_model_f_input.py && echo COMPILE_OK
```
Expected `COMPILE_OK`.

**G02 — tests:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/v72p2d5_accept_r1_20260907e01 -q
```
Report the literal summary line. Reference value, not a pass condition:
`195 passed`. STOP only if there are failures.

**G03 — protected roots unchanged:** re-run the STEP 1 stat command. Every size
and `mtime_ns` must equal your STEP 1 values; `p0_cost` and `g2` still absent.

**G04 — authorizations unchanged:** re-run the STEP 1 `grep`. Nine `false`,
`scientific_promotion: false`, `next_gate: P0_PACKET_REVIEW`.

**G05 — no `.py` touched (self-anchored to this packet's own mtime):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, pathlib, datetime
pkt = pathlib.Path('.workbuddy/tasks/D5_MODELF_ACCEPT_R1_TASK_PACKET.md')
cut = pkt.stat().st_mtime
print('PACKET_MTIME', datetime.datetime.fromtimestamp(cut).isoformat())
out = subprocess.run(['git','status','--porcelain=v1','--','*.py'],capture_output=True,text=True).stdout
newer=[(l[3:].strip().strip('\"'), datetime.datetime.fromtimestamp(pathlib.Path(l[3:].strip().strip('\"')).stat().st_mtime).isoformat()) for l in out.splitlines() if pathlib.Path(l[3:].strip().strip('\"')).exists() and pathlib.Path(l[3:].strip().strip('\"')).stat().st_mtime > cut]
print('DIRTY_PY_TOTAL', len(out.splitlines()))
print('NEWER_THAN_PACKET', newer)
print('G05_OK' if not newer else 'G05_FAIL')
"
```
Expected `NEWER_THAN_PACKET []` and `G05_OK`. The worktree carries pre-existing
untracked `.py` files unrelated to this task; that is expected and is not a
failure — only the `NEWER_THAN_PACKET` list is the verdict.

---

## 8. STEP 7 — Single commit (local only, NO PUSH)

Stage only these paths. Never `git add -A`, `git add .`, or `git commit -a`.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER docs/decision-log.md AGENT_PROJECT_MEMORY.md
```

**G06 — staged-scope check (prefix rule: a directory in the whitelist covers
everything under it):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, sys
allow = sys.argv[1:]
staged = subprocess.run(['git','diff','--cached','--name-only'],capture_output=True,text=True).stdout.split()
bad = [p for p in staged if not any(p == a or p.startswith(a.rstrip('/') + '/') for a in allow)]
print('STAGED_COUNT', len(staged))
for p in staged: print('  ', p)
print('OUT_OF_SCOPE', bad)
print('G06_OK' if not bad else 'G06_FAIL')
" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER docs/decision-log.md AGENT_PROJECT_MEMORY.md
```
Expected `OUT_OF_SCOPE []` and `G06_OK`. Reference `STAGED_COUNT` measured by
the packet author: **5** —
`MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md` (the R2 review, previously untracked),
`MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md` (new),
`cycle_state.yaml`, `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`.
A different count is not itself a failure — `OUT_OF_SCOPE` is the verdict — but
report the count and the listing.

On `G06_FAIL`: STOP, do not commit, do NOT unstage, do NOT clean. Stopping with
a staged index is the correct state. Report and wait.

Then commit:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "docs(v72p2d5): accept Model-F CAL-TRAIN input result, no authorization

Record MODEL_F_INPUT_RESULT_ACCEPTED for
workspace/v72p2d5_model_f_input/20260907_r1 after the independent Pre-RESULT
re-review returned PASS (C01-C11, 195 passed). Lands that R2 review, the
acceptance record, and the cycle_state acceptance fields.

PR16 was cleared BY RECORD, not by condition: the unauthorized G1 root still
exists and stays dispositioned VOID_RETAINED_IN_PLACE; R2 reinterpreted PR16
by intent. The artifact status field stays MODEL_F_INPUT_CANDIDATE because the
formal root is immutable and the loader accepts both values.

Residual risks carried into P0: R-R1 prod-side bare-authorized defaults
unchanged (test-side guard only); R-R2 no global formal-root absence gate.

All nine execution authorizations remain false; scientific_promotion remains
false; next_gate stays P0_PACKET_REVIEW. No decoder run, no CAL/VAL read, no
code change, no P0 authorization.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Verify and STOP:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git log --oneline -2 && git status -sb | head -1
```
Expected: 1 new commit on top of `20204726`, branch `ahead 4`. **Do not push.**

---

## 9. STEP 8 — Final report (message only, create no further files)

Report:

1. The STEP 1 and G03 stat outputs, and whether they are identical.
2. `COMPILE_OK` yes/no; the literal pytest summary line.
3. G04 result; G05 `NEWER_THAN_PACKET` and verdict; G06 `STAGED_COUNT`,
   listing and verdict.
4. The commit SHA and `git status -sb`.
5. These as `true`/`false`:
   - decoder run: false
   - CAL/VAL/parquet rows read: false
   - files deleted/moved/renamed under any `workspace/` root: false
   - artifact `model_f_input.npz` / `model_f_input_summary.json` modified: false
   - `p0_cost` / `g2` roots created: false
   - any `*_execution_authorized` changed: false
   - `next_gate` changed: false
   - `RESULT_SUMMARY` / `OPERATOR_RETURN` / `run_01` created: false
   - pushed: false
6. State plainly: **Model-F input is ACCEPTED; PR16 was cleared by record, not
   by condition; P0 is NOT authorized and `next_gate` remains
   `P0_PACKET_REVIEW`.**

Do not draw any scientific conclusion. Do not propose the next experiment. Do
not begin the P0 packet.
