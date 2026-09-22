# TASK PACKET — D5-P0-EXECUTE-R1: authorize and run P0 once (REAL EXECUTION)

**This is the first packet in this cycle that runs a real decoder.** It flips
an authorization key, performs exactly one production invocation, and flips the
key back. Everything before it was documentation.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD at start `b27f31da`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Frozen packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`
- Governing review: `.../P0_PRE_EXECUTE_REVIEW_R1.md`, verdict
  `PRE_EXECUTE_REVIEW_PASS`, all five open questions `DECIDED`
- Executor: a session the user has explicitly authorized in this session's chat

---

## 0. AUTHORIZATION GATE — read this before anything else

This packet may only be executed if, **in your own chat session**, the user has
explicitly told you to authorize and run P0. A packet file is not an
authorization. A prior session's authorization is not an authorization. My
saying "the packet is ready" is not an authorization.

Before STEP 1, confirm you hold an explicit instruction from the user in this
session to authorize and execute P0. Quote it verbatim in your report and in
the authorization record (STEP 3).

If you do not hold it: STOP. Do nothing. Say what is missing.

## 0.1 HARD PROHIBITIONS

You MUST NOT:

1. Run P0 more than once. **The authorization is consumed by the attempt, not
   by success** (OQ-P0-5). A crash, hang, timeout, or non-finite result ends
   the task — no retry, no rerun, no second root, no parameter change.
2. Run G1 or G2, or any `--phase` other than the single `p0-cost` invocation in
   STEP 4 and the refusal checks that are explicitly required.
3. Change any seed, `f` value, row count, `max_iter`, damping, budget, output
   root, or command line. The command in STEP 4 is verbatim.
4. Set any `*_execution_authorized` other than `p0_cost_execution_authorized`,
   or leave that key `true` at the end.
5. Change `next_gate`, `scientific_promotion`, or any other `cycle_state.yaml`
   value beyond the two edits this packet specifies.
6. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden. The
   run reads the accepted Model-F artifact only, through the code's own path.
7. Delete, move, rename, overwrite, normalize, or hash anything under
   `workspace/`, including a partial or failed P0 root.
8. Edit any `.py`. If the run reveals a code defect, record it and stop; do not
   fix it.
9. `git push`, `git reset`, `git stash`, `git checkout --`, `git clean`,
   `git rebase`, `git commit --amend`, `git add -A`, `git add .`,
   `git commit -a`.
10. Interpret the result. No FER, no leakage, no key rate, no "the method
    works", no G1/G2 authorization, no promotion. P0 measures cost only.

If any gate fails: STOP, report the step number and the literal output, change
nothing further.

---

## 1. STEP 1 — Fresh pre-flip evidence (required by OQ-P0-4)

The Pre-EXECUTE review ruled that isolation evidence **expires**; it must be
reproduced fresh immediately before the flip. Evidence from an earlier session
does not count. Run all of these now, in order, and keep the literal output.

**E1 — both roots absent:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib
for r in ['workspace/v72p2d5_p0_cost/20260906_r1','workspace/v72p2d5_g2/20260906_r1','workspace/v72p2d5_g1/20260906_r1','workspace/v72p2d5_model_f_input/20260907_r1']:
    p=pathlib.Path(r)
    print('ROOT', r, 'exists', p.exists())
    if p.exists():
        for f in sorted(p.iterdir()):
            st=f.stat(); print('  ', f.name, st.st_size, st.st_mtime_ns)
"
```
Required: `p0_cost` absent, `g2` absent, `g1` 4 files, `model_f_input` 2 files
(208467 / 752). If `p0_cost` exists → STOP.

**E2 — nine authorizations false and gate intact:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -nE "execution_authorized|next_gate|scientific_promotion" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Required: nine `false`, `scientific_promotion: false`,
`next_gate: P0_PACKET_REVIEW`.

**E3 — CLI refuses while unauthorized:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost; echo "exit=$?"
```
Required: a refusal message and `exit=3`. Then immediately re-run E1's stat and
confirm `p0_cost` is still absent.

**E4 — test isolation still holds:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/v72p2d5_p0_exec_r1_pre -q
```
Reference value, not a pass condition: `195 passed`. **Any failure → STOP.**
Then re-run E1's stat: `p0_cost` and `g2` must still be absent.

**E5 — compile clean:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_prepare_model_f_input.py && echo COMPILE_OK
```

**E6 — clean tracked tree:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 | grep -E "^ M|^M " ; echo "---MODIFIED-ABOVE---"
```
Required: nothing before the marker. Untracked `??` entries are expected and
fine.

## 2. STEP 2 — Watchdog rehearsal (required by OQ-P0-2)

The review requires an operator-side outer process guard, and the exact command
must appear in the authorization record. Verify it works on this machine before
the real run:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && timeout -k 30 3 python -c "import time; time.sleep(10)"; echo "exit=$? (124 expected)"
```
Required: `exit=124`. If `timeout` is unavailable or the exit code differs,
STOP — do not run P0 without a working guard.

## 3. STEP 3 — Flip the authorization and record it

Make exactly ONE line change in
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`:

`p0_cost_execution_authorized: false` → `p0_cost_execution_authorized: true`

Nothing else in that file changes. Not `next_gate`. Not a comment. Not
whitespace elsewhere.

Then create ONE new file
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_AUTHORIZATION_RECORD_R1.md`:

```markdown
# P0 execution authorization record R1 — [DATE]

Authority: user, explicit, in the executing session.
Verbatim authorization: "[PASTE the user's exact words]"

Scope: exactly ONE invocation of the frozen P0 command. Consumed by the
attempt, not by success. No retry, no rerun, no parameter change, no G1, no G2.

Frozen command:
`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`

Operator watchdog (OQ-P0-2), applied to that command:
`timeout -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
Rehearsal verified on this machine: `timeout -k 30 3 ... -> exit 124`.

Governing decisions from `P0_PRE_EXECUTE_REVIEW_R1.md`:
- OQ-P0-1: decode-attributed total cap 1440 s, record-only, no abort; breach is
  recorded as `RESOURCE_OVERRUN`.
- OQ-P0-2: 1500 s outer process-tree guard, command above.
- OQ-P0-3: P0 PASS is independent of `projection_blocked`; a blocked projection
  gates G2 only, never G1; G1 is judged separately by
  `projected_g1_s <= 900 s`.
- OQ-P0-4: pre-flip isolation evidence reproduced fresh in this session.
- OQ-P0-5: a partial or failed root is retained in place as VOID and never
  reused; the authorization is consumed by the attempt; non-finite output is
  a FAIL.

Fresh pre-flip evidence (this session):
[PASTE E1 .. E6 literal outputs]

Post-run obligation: `p0_cost_execution_authorized` returns to `false`
immediately after the single attempt, whatever the outcome.
```

Commit both, staging only these two paths:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_AUTHORIZATION_RECORD_R1.md && git diff --cached --name-only
```
Expected exactly those two paths and nothing else. Then:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "chore(v72p2d5): authorize a single P0 cost-preflight invocation

User-authorized, explicit, one attempt only. Records the frozen command, the
1500s operator watchdog, the five Pre-EXECUTE decisions, and the fresh
pre-flip isolation evidence. p0_cost_execution_authorized flips false->true
and returns to false immediately after the attempt.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

## 4. STEP 4 — The single run

Run this exactly once, verbatim, and capture stdout, stderr, the exit code, and
the wall time:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && time timeout -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost; echo "exit=$?"
```

Do not run it again under any circumstance. Interpretation of exit codes:

- `0` — the phase completed. Continue to STEP 5.
- `124` — the watchdog fired; the run hung. This is a FAIL under OQ-P0-5.
  Continue to STEP 5 and record it as such.
- `3` — refused. Something is wrong with the flip; record and continue to
  STEP 5 without retrying.
- anything else — crash. FAIL under OQ-P0-5. Continue to STEP 5.

Whatever happened, do not delete or modify whatever is now under
`workspace/v72p2d5_p0_cost/20260906_r1/`.

## 5. STEP 5 — Revoke the authorization immediately

Flip `p0_cost_execution_authorized: true` back to `false` in
`cycle_state.yaml`. One line. Nothing else. Do this before any analysis,
before writing the operator return, before anything else.

Verify:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -nE "execution_authorized|next_gate" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Required: nine `false` again, `next_gate: P0_PACKET_REVIEW` unchanged.

## 6. STEP 6 — Record what happened, without interpreting it

Stat the output root and read the scalars:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib, json
p = pathlib.Path('workspace/v72p2d5_p0_cost/20260906_r1')
print('exists', p.exists())
if p.exists():
    for f in sorted(p.iterdir()):
        st=f.stat(); print(f.name, st.st_size, st.st_mtime_ns)
    r = p/'results.json'
    if r.exists():
        print(json.dumps(json.load(open(r, encoding='utf-8')), indent=2)[:4000])
"
```

Create ONE new file
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_OPERATOR_RETURN_R1.md`
containing, and only containing:

- the verbatim command and its exit code and wall time;
- the literal stdout and stderr;
- the output root listing with sizes and mtimes, or a statement that it is
  absent;
- the literal scalars: `decoder_calls`, per-record `f` / `kind` / `wall_s` /
  `iterations` / `rss_bytes`, `projected_g1_s`, `projected_g2_s`,
  `projection_blocked`, `passed`;
- the decode-attributed total against the 1440 s cap, and `RESOURCE_OVERRUN`
  if breached (OQ-P0-1);
- peak RSS against the 2 GiB reference;
- an explicit `NOT_INTERPRETED` section stating that this document draws no
  conclusion about correctness, rate points, FER, leakage, key rate, the
  method, or G1/G2 readiness, and that acceptance requires an independent
  Pre-RESULT review.

Then commit, staging only these paths:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_OPERATOR_RETURN_R1.md && git diff --cached --name-only
```
Expected exactly those two. Then:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "result(v72p2d5): P0 cost-preflight single invocation, authorization consumed

One authorized attempt of the frozen p0-cost command under the 1500s operator
watchdog. Records command, exit code, wall time, output root, and the literal
cost scalars. p0_cost_execution_authorized returned to false. No
interpretation, no acceptance, no G1/G2 authorization; next_gate unchanged.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Do not push.

## 7. STEP 7 — Report

Report, literally and without interpretation:

1. The user's verbatim authorization you relied on.
2. E1–E6 outputs, and the watchdog rehearsal exit code.
3. The run command, exit code, wall time, stdout, stderr.
4. The output root listing and the cost scalars.
5. Decode-attributed total vs the 1440 s cap; `RESOURCE_OVERRUN` yes/no; peak
   RSS vs 2 GiB.
6. The two commit SHAs and `git status -sb`.
7. These as `true`/`false`:
   - P0 invoked exactly once: [true/false]
   - any retry or rerun: false
   - any parameter, seed, or command change: false
   - G1 or G2 invoked: false
   - `p0_cost_execution_authorized` is `false` now: [true/false]
   - any other `*_execution_authorized` changed: false
   - `next_gate` changed: false
   - any `workspace/` file deleted, moved, renamed, or overwritten: false
   - any `.py` edited: false
   - pushed: false
8. This line: **P0 ran once and the authorization is consumed. The result is
   recorded, not accepted. No conclusion is drawn. Acceptance requires an
   independent Pre-RESULT review; G1 remains unauthorized.**

Do not propose G1. Do not interpret the numbers. Do not state whether the
method works.
