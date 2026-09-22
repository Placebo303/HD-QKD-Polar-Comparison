# TASK PACKET — D5-P0-FREEZE-R1: freeze the P0 execution packet (docs only)

Target executor: low-capability session. Follow this file literally. Do NOT
improvise, do NOT optimize, do NOT clean up anything not listed.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean` (do NOT create, switch, or rename)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Current gate: `next_gate: P0_PACKET_REVIEW`
- This packet performs: **write one document + one local commit.** Nothing else.
- Lifecycle after this packet: unchanged. `next_gate` stays
  `P0_PACKET_REVIEW`. P0 stays **unauthorized** and **unexecuted**.

You are transcribing a frozen packet. Every number you need is given to you in
§3. **Do not derive, recompute, or "improve" any value.** If a value you need
is not in §3, STOP and report — do not go looking for it in the source.

---

## 0. HARD PROHIBITIONS (violating any one = STOP and report)

You MUST NOT:

1. Run any decoder.
2. Run `scripts/v72p2d5_gf32_rate_mother.py` with ANY `--phase` value.
   `--help` is allowed; nothing else.
3. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
4. Read CAL / VAL / raw parquet rows. `pandas.read_parquet` is forbidden.
5. Delete, move, rename, copy, normalize, hash, or open-for-write anything
   under `workspace/`. `stat` read-only is allowed.
6. Create `workspace/v72p2d5_p0_cost/...` or `workspace/v72p2d5_g2/...`.
   **The P0 formal root must still be absent when you finish.**
7. Set ANY `*_execution_authorized` to `true`. In particular
   `p0_cost_execution_authorized` stays `false`. **Do not edit
   `cycle_state.yaml` at all in this packet** — not even a comment.
8. `git push`, `git reset`, `git stash`, `git checkout --`, `git clean`,
   `git rebase`, `git commit --amend`, `git add -A`, `git add .`,
   `git commit -a`.
9. Edit any `.py`. Zero code changes.
10. Edit any existing `.md`, any OpenSpec file, `docs/decision-log.md`, or
    `AGENT_PROJECT_MEMORY.md`. **This packet creates exactly one new file and
    modifies nothing.**
11. Write `RESULT_SUMMARY.md`, `OPERATOR_RETURN.md`, or any `run_01`.
12. Resolve any of the OPEN QUESTIONS in §4. Transcribe them as questions.
    Deciding them is the reviewer's job, not yours.
13. Claim a scientific result, or state that P0 is ready, approved, or safe.

If anything is ambiguous or a check fails: STOP, write nothing further, report
the failing step number and the literal output.

---

## 1. What this packet is for

`cycle_state.yaml` says `next_gate: P0_PACKET_REVIEW`. Before P0 may be
authorized, the P0 execution must be frozen in writing so an independent
reviewer can check it against the code and the accepted plan.

You are writing that frozen document. You are **not** reviewing it, and you are
**not** authorizing it. Two further steps follow this one and are out of scope:
an independent Pre-EXECUTE review, and then a separate explicit authorization.

## 2. STEP 1 — Read-only pre-state snapshot

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git status -sb | head -1
```
Expected: `formal-ir-v72p1-addendum-clean`, HEAD `b7540421`, `ahead 4`.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib
for r in ['workspace/v72p2d5_p0_cost/20260906_r1','workspace/v72p2d5_g1/20260906_r1','workspace/v72p2d5_g2/20260906_r1','workspace/v72p2d5_model_f_input/20260907_r1']:
    p=pathlib.Path(r)
    print('ROOT', r, 'exists', p.exists())
    if p.exists():
        for f in sorted(p.iterdir()):
            st=f.stat(); print('  ', f.name, st.st_size, st.st_mtime_ns)
"
```
Expected: `p0_cost` **absent**, `g2` **absent**, `g1` present with 4 files,
`model_f_input` present with 2 files (208467 / 752). If `p0_cost` exists, STOP.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -nE "execution_authorized|scientific_promotion|next_gate|model_f_input_accepted" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Expected: nine `false`, `scientific_promotion: false`,
`next_gate: P0_PACKET_REVIEW`, `model_f_input_accepted: true`. Otherwise STOP.

---

## 3. Frozen values (transcribe these; do not derive)

All values below were read from the frozen source by the packet author. Use
them exactly as written.

**Source of truth for the reviewer** (cite, do not re-verify yourself):
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
lines 45–84 (constants), `run_p0_cost_phase` at line 1948,
`run_p0_cost_synthetic` at line 2416; `scripts/v72p2d5_gf32_rate_mother.py`
(CLI); `openspec/changes/v72p2d5-p0-g1-g2-production-path/design.md` §1–§5.

| Item | Frozen value |
| --- | --- |
| Phase name | `p0-cost` |
| Authorization key | `p0_cost_execution_authorized` (currently `false`) |
| Block width `n_IR` | 64 |
| `f` set | `(1.0, 1.2)` |
| L1 row prefixes `m1(f)` | `{1.0: 49, 1.2: 59}` |
| L2 row prefixes `m2(f)` | `{1.0: 43, 1.2: 52}` |
| Row formula | `rows = ceil(n * CE * f / 5)` |
| `CE_L1_MEAN` | `3.814742` |
| `CE_L2_ORACLE_MEAN` | `3.347605` |
| Mother builder | `build_dv3_nested_mother`, one max mother per layer |
| Builder `k_min` | L1 `P0_L1_K_MIN = 59`, L2 `P0_L2_K_MIN = 52` |
| Graph seeds | L1 `2026090501`, L2 `2026090502` |
| Block seeds | `G0_SEEDS[:2]` = `2026090510`, `2026090511` (2 blocks) |
| Decoder calls | 12 total = per `f` (2 APP calls x 2 blocks) + (1 oracle call x 2 blocks), over 2 `f` values |
| Decoder | historical `decode_row_layered_fftqspa`, `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None` (cold start), bound once and reused |
| Prior source | accepted Model-F artifact at `workspace/v72p2d5_model_f_input/20260907_r1/`, via `prepare_model_f_prior` reusing `build_f_model` with `LAMBDA_STAR = 137.3823795883264` |
| Output root | `workspace/v72p2d5_p0_cost/20260906_r1/` (must be absent before the run; writer refuses overwrite) |
| Output files | exactly `results.json`, `table.csv`, `report.md`, `execution_summary.json` |
| Recorded per record | `f`, `kind` (`app`/`oracle`), `wall_s`, `iterations`, `rss_bytes` |
| Returned scalars | `decoder_calls`, `projected_g1_s`, `projected_g2_s`, `projection_blocked`, `passed` |
| Projection basis | `per_call = total_wall / decoder_calls`; `projected_g1_s = per_call * (100*2 + 20*2)`; `projected_g2_s = per_call * (200*3 + 40*3)` |
| `projection_blocked` rule | `True` when `projected_g2_s > 3600.0` |
| Single-call budget | 120 s |
| Downstream budgets (context only) | G1 total `<= 900 s`, G2 total `<= 3600 s`, peak RSS `< 2 GiB` |
| Metric naming | `exact_failure_fraction`; **never** call it FER; never extrapolate to real frames |
| Frozen command | `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` |
| Invocation count | exactly one; no retry, no rerun, no tuning, no seed change |

Two facts the reviewer must be told plainly, both carried over from the
accepted Model-F result:

- `R-R1`: `run_p0_cost_synthetic(authorized=True)` with no injected arguments
  binds the **production** decoder and writes to the **formal** root by
  default. The guard against an accidental trigger is test-side only.
- `R-R2`: `M24`/`P12` no longer assert global formal-root absence; an
  unexpected new formal output would be caught only by per-test snapshot
  comparison.

## 4. OPEN QUESTIONS — transcribe, do not answer

Write these into the document verbatim as unresolved questions for the
reviewer. Do not pick an answer. Do not mark them resolved.

- `OQ-P0-1` — Total wall cap for P0. The frozen source pins a 120 s single-call
  budget but no P0 total. Worst case is 12 x 120 s = 1440 s. Should the packet
  carry an explicit P0 total cap, and if so what value, and is exceeding it an
  abort or a recorded overrun?
- `OQ-P0-2` — Watchdog. The CLI docstring says a hanging historical call needs
  an outer-process watchdog and that no such machinery lives in the script.
  What is the required outer guard for this run, and who stops it?
- `OQ-P0-3` — `projection_blocked` semantics. If `projected_g2_s > 3600`, is P0
  itself still a PASS with a recorded `RESOURCE_PROJECTION_BLOCKED` flag for
  G2, or does it block G1 as well?
- `OQ-P0-4` — Pre-authorization isolation re-verification. Given `R-R1`, what
  exact evidence must be produced immediately before authorization to show no
  test or import path can trigger a bare authorized P0 run?
- `OQ-P0-5` — Failure disposition. If the run crashes, hangs, or produces
  non-finite values, is the partial output root retained (as with the voided G1
  root) or is the authorization simply consumed with a recorded failure?

---

## 5. STEP 2 — Write the document (ONE new file)

Create exactly one new file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`

Structure it exactly as follows. Fill the bracketed slots from your STEP 1
output. Copy §3 and §4 of this task packet into the matching sections without
altering any number or any question.

```markdown
# P0 cost-preflight execution packet — 20260907 (FROZEN, NOT AUTHORIZED)

Status: `P0_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`.
Cycle: V72P2D5-GF32-RATE-MOTHER. Gate: `next_gate: P0_PACKET_REVIEW`.
This document freezes the intended P0 run so it can be independently reviewed.
It authorizes nothing and executes nothing.

## P01 Pre-state at freeze time

Branch [PASTE] / HEAD [PASTE] / [PASTE ahead status].
`workspace/v72p2d5_p0_cost/20260906_r1` absent: [PASTE].
`workspace/v72p2d5_g2/20260906_r1` absent: [PASTE].
`workspace/v72p2d5_g1/20260906_r1` present, 4 files: [PASTE].
`workspace/v72p2d5_model_f_input/20260907_r1` present, 2 files: [PASTE].
`p0_cost_execution_authorized`: false. `next_gate`: P0_PACKET_REVIEW.
`model_f_input_accepted`: true.

## P02 Purpose and claim boundary

P0 is a cost preflight, not an experiment. Its only outputs are wall time,
iteration counts, RSS, and a projection of G1/G2 cost. It establishes no
correctness, no rate-point performance, no FER, no leakage, no key rate, and
no verdict on NB-LDPC or the dv3 mother. A P0 PASS means "the cost is measured
and projected", nothing more.

## P03 Frozen parameters

[COPY the whole table from §3 of the task packet, unchanged]

## P04 Frozen command and invocation contract

Command: `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
Exactly one invocation. No retry, no rerun, no seed change, no tuning, no
`max_iter`/damping change, no alternate root, no second attempt after a
failure. The authorization is consumed by the attempt, not by success.

Authorization mechanism: the CLI reads `cycle_state.yaml` and refuses with
exit 3 unless `p0_cost_execution_authorized` is `true`. Flipping that key is
the authorization act and is NOT part of this packet.

## P05 Output contract

Root `workspace/v72p2d5_p0_cost/20260906_r1/`, which MUST be absent before the
run; the writer refuses to overwrite an existing root. Exactly four files:
`results.json`, `table.csv`, `report.md`, `execution_summary.json`. Scalar
payloads only. No raw rows, no matrices, no beliefs, no priors, no paths, no
checksums.

## P06 Carried residual risks

- `R-R1`: [COPY verbatim from §3 of the task packet]
- `R-R2`: [COPY verbatim from §3 of the task packet]

## P07 Open questions for the reviewer

[COPY OQ-P0-1 .. OQ-P0-5 from §4 of the task packet, verbatim, unanswered]

## P08 What this packet does not do

It does not authorize P0. It does not execute P0. It does not change any
`*_execution_authorized`. It does not change `next_gate`. It does not create
the P0 formal root. It does not resolve the open questions. It makes no
scientific claim.

## P09 Required next steps, in order

1. Independent Pre-EXECUTE review of this packet against the source, including
   a decision on every open question in P07.
2. Only if that review passes: a separate, explicit authorization act that
   flips `p0_cost_execution_authorized` to `true`.
3. Only then: the single frozen invocation in P04.
4. Then an independent Pre-RESULT review before any acceptance.

None of these may be merged, reordered, or performed by the same session that
wrote this packet.
```

---

## 6. STEP 3 — Verification gates

**G01 — the P0 root is still absent, and nothing under `workspace/` changed:**
re-run the STEP 1 stat command. `p0_cost` and `g2` still absent; `g1` and
`model_f_input` byte-identical to STEP 1.

**G02 — no authorization or gate drift:** re-run the STEP 1 `grep`. Nine
`false`, `next_gate: P0_PACKET_REVIEW`, `model_f_input_accepted: true`.

**G03 — nothing modified, exactly one new file:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 -- docs openspec comparison_bench scripts AGENT_PROJECT_MEMORY.md | grep -vE "^\?\? " ; echo "---MODIFIED-ABOVE---"
```
Expected: **nothing** between the command and the marker line. Any ` M ` entry
means you modified a tracked file, which this packet forbids → STOP.

**G04 — no `.py` touched (self-anchored to this packet's own mtime):**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, pathlib, datetime
pkt = pathlib.Path('.workbuddy/tasks/D5_P0_FREEZE_R1_TASK_PACKET.md')
cut = pkt.stat().st_mtime
print('PACKET_MTIME', datetime.datetime.fromtimestamp(cut).isoformat())
out = subprocess.run(['git','status','--porcelain=v1','--','*.py'],capture_output=True,text=True).stdout
newer=[(l[3:].strip().strip('\"'), datetime.datetime.fromtimestamp(pathlib.Path(l[3:].strip().strip('\"')).stat().st_mtime).isoformat()) for l in out.splitlines() if pathlib.Path(l[3:].strip().strip('\"')).exists() and pathlib.Path(l[3:].strip().strip('\"')).stat().st_mtime > cut]
print('DIRTY_PY_TOTAL', len(out.splitlines()))
print('NEWER_THAN_PACKET', newer)
print('G04_OK' if not newer else 'G04_FAIL')
"
```
Expected `NEWER_THAN_PACKET []` and `G04_OK`. Pre-existing untracked `.py`
files are expected and are not a failure; only `NEWER_THAN_PACKET` is the
verdict.

No test run is required by this packet. Do not run pytest.

---

## 7. STEP 4 — Single commit (local only, NO PUSH)

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md
```

**G05 — staged-scope check:**
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, sys
allow = sys.argv[1:]
staged = subprocess.run(['git','diff','--cached','--name-only'],capture_output=True,text=True).stdout.split()
bad = [p for p in staged if not any(p == a or p.startswith(a.rstrip('/') + '/') for a in allow)]
print('STAGED_COUNT', len(staged))
for p in staged: print('  ', p)
print('OUT_OF_SCOPE', bad)
print('G05_OK' if not bad else 'G05_FAIL')
" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md
```
Expected `OUT_OF_SCOPE []`, `G05_OK`, and `STAGED_COUNT 1`. A count other than
1 means something else got staged → STOP, do not commit, do NOT unstage.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "docs(v72p2d5): freeze P0 cost-preflight execution packet, not authorized

Freeze the intended P0 run for independent Pre-EXECUTE review: phase p0-cost,
n_IR 64, f {1.0,1.2}, row prefixes m1 {49,59} / m2 {43,52} from one dv3 mother
per layer (graph seeds 2026090501/2026090502), 2 blocks (2026090510/11), 12
decoder calls, historical decoder max_iter 90 damping 1.0 cold start, prior
from the accepted Model-F artifact, four-file no-overwrite output at
workspace/v72p2d5_p0_cost/20260906_r1.

Carries residual risks R-R1 (prod-side bare-authorized defaults, test-side
guard only) and R-R2 (no global formal-root absence gate), and records five
open questions for the reviewer: P0 total wall cap, outer watchdog,
projection_blocked semantics, pre-authorization isolation evidence, and
failure disposition.

Authorizes nothing and executes nothing. p0_cost_execution_authorized stays
false; next_gate stays P0_PACKET_REVIEW; the P0 formal root stays absent.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Verify and STOP:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git log --oneline -2 && git status -sb | head -1
```
Expected: 1 new commit on top of `b7540421`, `ahead 5`. **Do not push.**

---

## 8. STEP 5 — Final report (message only, create no further files)

Report:

1. STEP 1 and G01 stat outputs, and whether they are identical.
2. G02, G03, G04, G05 results including `STAGED_COUNT`.
3. The commit SHA and `git status -sb`.
4. These as `true`/`false`:
   - decoder run: false
   - any `--phase` invoked: false
   - CAL/VAL/parquet rows read: false
   - `workspace/` files created, deleted, moved, renamed or modified: false
   - `workspace/v72p2d5_p0_cost/20260906_r1` created: false
   - `cycle_state.yaml` edited: false
   - any `*_execution_authorized` changed: false
   - any existing tracked file modified: false
   - pytest run: false
   - pushed: false
5. State plainly: **The P0 execution packet is frozen for review. P0 is NOT
   authorized, NOT executed, and the P0 formal root is still absent.
   `next_gate` remains `P0_PACKET_REVIEW`. The five open questions are
   unresolved and are the reviewer's to decide.**

Do not draw any scientific conclusion. Do not answer the open questions. Do not
propose or begin the review.
