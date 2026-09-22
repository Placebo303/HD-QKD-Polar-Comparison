# TASK PACKET — D5-P0-EXECUTE-R2: authorize and run P0 once, with reachability precondition

**Supersedes `D5_P0_EXECUTE_R1_TASK_PACKET.md` entirely. Do not use R1.**

R1 was consumed on 2026-09-07 and produced no run: the phase refused in 0.376 s
with a false `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` because the
consumer reached the Model-F artifact through a package import that fails when
the CLI is launched as a script. R2 adds the precondition that would have
caught it **before** any authorization was spent.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Frozen packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`
- Governing review: `.../P0_PRE_EXECUTE_REVIEW_R1.md` (`PRE_EXECUTE_REVIEW_PASS`,
  five OQs `DECIDED`) — still in force, unchanged by R2
- Executor: a session the user has explicitly authorized in that session's chat

---

## 0. GATE ZERO — do not start until both hold

1. The Model-F consumer path fix (`D5_P0_LOADER_FIX_R1`) has landed on this
   branch, and
2. it has passed an independent review.

Verify both yourself before STEP 1. If either is missing: STOP and say so. Do
not attempt the run "to see whether it works now" — that spends an
authorization, which is exactly what R1 taught.

## 0.1 AUTHORIZATION GATE

This packet may only be executed if, **in your own chat session**, the user has
explicitly told you to authorize and run P0. A packet file is not an
authorization; a previous session's authorization is not an authorization; the
consumed R1 authorization is not reusable. Quote the user's words verbatim in
your report and in the authorization record.

If you do not hold it: STOP.

## 0.2 HARD PROHIBITIONS

You MUST NOT:

1. Run P0 more than once. The authorization is consumed by the attempt, not by
   success (OQ-P0-5). Crash, hang, timeout, or refusal ends the task — no
   retry, no rerun, no second root, no parameter change.
2. Run G1 or G2, or any `--phase` other than the single `p0-cost` invocation in
   STEP 5 and the required refusal check.
3. Change any seed, `f` value, row count, `max_iter`, damping, budget, output
   root, or command line.
4. Set any `*_execution_authorized` other than `p0_cost_execution_authorized`,
   or leave that key `true` at the end.
5. Change `next_gate`, `scientific_promotion`, or any other `cycle_state.yaml`
   value beyond the two flips this packet specifies.
6. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
7. Delete, move, rename, overwrite, normalize, or hash anything under
   `workspace/`, including a partial or failed P0 root.
8. Edit any `.py`. If the run reveals a defect, record it and stop; do not fix
   it. **This includes the reachability probe in STEP 2 — if it fails, you
   report, you do not repair.**
9. `git push`, `git reset`, `git stash`, `git checkout --`, `git clean`,
   `git rebase`, `git commit --amend`, `git add -A`, `git add .`,
   `git commit -a`.
10. Interpret the result. P0 measures cost only.

---

## 1. STEP 1 — Fresh pre-flip evidence (OQ-P0-4)

Isolation evidence expires; reproduce it in **your** session. Keep literal
output for all of E1–E6.

**E1 — roots:** stat `workspace/v72p2d5_p0_cost/20260906_r1`,
`.../v72p2d5_g2/20260906_r1`, `.../v72p2d5_g1/20260906_r1`,
`.../v72p2d5_model_f_input/20260907_r1`. Required: P0 absent, G2 absent, G1
4 files, Model-F 2 files (208467 / 752). If P0 exists → STOP.

**E2 — authorizations:** nine `*_execution_authorized: false`,
`scientific_promotion: false`, `next_gate: P0_PACKET_REVIEW`.

**E3 — CLI refuses while unauthorized:**
`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` → refusal, exit 3.
Re-stat: P0 still absent.

**E4 — tests:** the three focused files with a fresh `--basetemp` under
`workspace/`. Reference only, not a pass condition: was `195 passed` before the
loader fix; the fix adds cases. **Any failure → STOP.** Re-stat afterwards.

**E5 — compile:** `py_compile` on the two core modules and the two scripts.

**E6 — clean tracked tree:** no ` M ` / `M ` entries. Untracked `??` is fine.

## 2. STEP 2 — REACHABILITY PRECONDITION (new in R2, the point of this packet)

Prove that the authorized code path actually reaches the first decoder call,
**before** spending any authorization. This is an operator pre-flight check,
not a test: it deliberately reads the accepted Model-F artifact read-only,
which is the one step no test covers.

Method — all three conditions are mandatory:

- call `run_p0_cost_synthetic` directly (not through the CLI, so no
  authorization flip is needed);
- pass `authorized=True`, an explicit `out_dir` pointing at a fresh `tmp`
  directory outside the formal roots, and a **probe decoder that raises a
  unique sentinel exception on its first invocation**;
- assert that the sentinel is what comes back.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import importlib.util, pathlib, tempfile, traceback
core = pathlib.Path('comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py')
spec = importlib.util.spec_from_file_location('core', str(core))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Probe(Exception): pass
calls = []
def probe(*a, **k):
    calls.append(1)
    raise Probe('REACHED_FIRST_DECODER_CALL')

tmp = tempfile.mkdtemp(prefix='p0_reach_')
try:
    m.run_p0_cost_synthetic(authorized=True, decode_fn=probe, out_dir=tmp)
    print('REACH_UNEXPECTED_COMPLETION')
except Probe as e:
    print('REACH_OK', e, 'probe_calls', len(calls))
except Exception as e:
    print('REACH_FAIL', type(e).__name__, e)
    traceback.print_exc()
print('tmp_contents', sorted(p.name for p in pathlib.Path(tmp).iterdir()))
"
```

Required outcome: `REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1` and an
empty `tmp_contents`.

- `REACH_FAIL` → the authorized path still cannot reach the decoder. **STOP.
  Do not flip anything. Report the exception and traceback verbatim.** No
  authorization is consumed, which is the entire purpose of this step.
- `REACH_UNEXPECTED_COMPLETION` → the probe was never called, meaning the phase
  completed without decoding. STOP and report; something is structurally wrong.

Then verify the formal roots are untouched:
`workspace/v72p2d5_p0_cost/20260906_r1` and `.../v72p2d5_g2/20260906_r1` still
absent; the Model-F root still exactly 2 files with unchanged size and mtime.
If the P0 formal root appeared, STOP and report it as a critical finding.

## 3. STEP 3 — Watchdog rehearsal (OQ-P0-2)

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && timeout -k 30 3 python -c "import time; time.sleep(10)"; echo "exit=$? (124 expected)"
```
Required `exit=124`. No working guard → do not run P0.

## 4. STEP 4 — Flip the authorization and record it

One line in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`:
`p0_cost_execution_authorized: false` → `true`. Nothing else changes.

Create `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_AUTHORIZATION_RECORD_R2.md`
containing: the user's verbatim authorization; the frozen command; the watchdog
command and its rehearsal result; the five OQ decisions from
`P0_PRE_EXECUTE_REVIEW_R1.md`; the literal E1–E6 output; **the literal STEP 2
reachability output**; a note that the R1 authorization was consumed on
2026-09-07 with no run due to the consumer path defect, and that this is a new
and separate authorization; and the post-run obligation to return the key to
`false` whatever happens.

Also create
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET_ADDENDUM_A1.md`
— an addendum, **not** an edit of the frozen `P0_EXECUTION_PACKET.md`, which
stays byte-identical. It records: the R1 attempt and its false BLOCKED message;
the verified root cause; the fix; and the new standing precondition, stated as
a rule for this and every later stage —

> Before any `*_execution_authorized` is flipped for a stage, that stage's
> authorized path MUST be shown to reach its first decoder call under the real
> launch condition, using an explicit tmp `out_dir` and a probe decoder that
> raises on first invocation. Test-suite green is not sufficient evidence: the
> suite injects tables and monkeypatches roots, so it cannot exercise this path.

Commit both plus the flipped `cycle_state.yaml`, staging only those three
paths, verifying with `git diff --cached --name-only` first:

```
chore(v72p2d5): authorize a second single P0 invocation, with reachability proof

R1's authorization was consumed on 2026-09-07 with no run: the consumer
reached the Model-F artifact by package import, which fails under script
launch, and reported a present valid artifact as missing input.

This authorization is new and separate. It is preceded by a reachability
precondition proving the authorized path reaches the first decoder call with
a probe decoder and a tmp out_dir, before any key is flipped. Addendum A1
records that precondition as a standing rule for every later stage; the
frozen P0_EXECUTION_PACKET.md is unchanged.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 5. STEP 5 — The single run

Exactly once, verbatim, capturing stdout, stderr, exit code and wall time:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && time timeout -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost; echo "exit=$?"
```

`0` → continue. `124` → watchdog fired, FAIL under OQ-P0-5. `3` → refused,
record and continue without retrying. Anything else → crash, FAIL. In every
case go to STEP 6; never rerun. Do not touch whatever is now under
`workspace/v72p2d5_p0_cost/20260906_r1/`.

## 6. STEP 6 — Revoke immediately

Flip `p0_cost_execution_authorized` back to `false` before any analysis or
writing. Verify nine `false` and `next_gate: P0_PACKET_REVIEW` unchanged.

## 7. STEP 7 — Record without interpreting

Stat the output root and read the scalars. Create
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_OPERATOR_RETURN_R2.md` with:
the verbatim command, exit code, wall time, literal stdout and stderr; the root
listing with sizes and mtimes (or a statement that it is absent); the literal
scalars `decoder_calls`, per-record `f` / `kind` / `wall_s` / `iterations` /
`rss_bytes`, `projected_g1_s`, `projected_g2_s`, `projection_blocked`,
`passed`; the decode-attributed total against the 1440 s cap with
`RESOURCE_OVERRUN` if breached (OQ-P0-1); peak RSS against the 2 GiB
reference; and a `NOT_INTERPRETED` section stating that no conclusion is drawn
about correctness, rate points, FER, leakage, key rate, the method, or G1/G2
readiness, and that acceptance requires an independent Pre-RESULT review.

Commit `cycle_state.yaml` + that file only:

```
result(v72p2d5): P0 cost-preflight second authorized invocation

One authorized attempt of the frozen p0-cost command under the 1500s operator
watchdog, preceded by a passing reachability precondition. Records command,
exit code, wall time, output root and the literal cost scalars.
p0_cost_execution_authorized returned to false. No interpretation, no
acceptance, no G1/G2 authorization; next_gate unchanged.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Do not push.

## 8. STEP 8 — Report

1. The user's verbatim authorization.
2. E1–E6 literal output.
3. **The STEP 2 reachability result, literally.**
4. Watchdog rehearsal exit code.
5. Run command, exit code, wall time, stdout, stderr.
6. Output root listing and cost scalars.
7. Decode-attributed total vs 1440 s; `RESOURCE_OVERRUN` yes/no; peak RSS vs
   2 GiB.
8. The two commit SHAs and `git status -sb`.
9. `true`/`false`: P0 invoked exactly once; any retry or rerun: false; any
   parameter/seed/command change: false; G1 or G2 invoked: false;
   `p0_cost_execution_authorized` is `false` now; any other authorization
   changed: false; `next_gate` changed: false; any `workspace/` file deleted,
   moved, renamed or overwritten: false; `P0_EXECUTION_PACKET.md` modified:
   false; any `.py` edited: false; pushed: false.
10. **P0 ran once and the authorization is consumed. The result is recorded,
    not accepted. No conclusion is drawn. Acceptance requires an independent
    Pre-RESULT review; G1 remains unauthorized.**

Do not propose G1. Do not interpret the numbers.
