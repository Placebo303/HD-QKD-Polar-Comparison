# TASK PACKET — D5-P0-ACCEPT-R1: accept the P0 result and land the review record (docs only)

Target executor: low-capability session. Follow literally. This packet writes
documents and makes one commit. It runs nothing.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD at start `860ebbff`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate at start `next_gate: P0_PACKET_REVIEW`
- After this packet: `next_gate: G1_PACKET_REVIEW`. P0 accepted as a **cost
  measurement only**. G1 stays unauthorized and unfrozen.

Every number you need is in §3. **Do not derive, recompute, or improve any
value.** If something you need is missing, STOP and report.

---

## 0. HARD PROHIBITIONS

1. Run no decoder. Invoke no `--phase`. Run
   `scripts/v72p2d5_prepare_model_f_input.py` not at all.
2. Read no CAL / VAL / raw parquet rows.
3. Touch nothing under `workspace/` — no create, delete, move, rename,
   overwrite, normalize, or hash. Read-only `stat` is allowed. The six formal
   roots are evidence.
4. Do not let `workspace/v72p2d5_g2/20260906_r1` come into existence.
5. Set **no** `*_execution_authorized` to `true`. All nine stay `false`.
   The only `cycle_state.yaml` change permitted is the `next_gate` line and the
   two new keys named in §4.
6. Edit no `.py`. Edit no existing `.md` except the two append-only files named
   in §5. Edit no OpenSpec file.
7. No `git push`, `git add -A`, `git add .`, `git commit -a`, `git reset`,
   `git stash`, `git checkout`, `git clean`, `git rebase`,
   `git commit --amend`, `git add --renormalize`.
8. Do not interpret the P0 numbers beyond what §3 states verbatim. No FER, no
   leakage, no key rate, no method verdict, no claim that G1 or G2 will pass.
9. Do not freeze, plan, or authorize G1. That is the next packet, not this one.

---

## 1. STEP 1 — Pre-state snapshot

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git status -sb | head -1
```
Expected: `formal-ir-v72p1-addendum-clean`, `860ebbff`, `ahead 11`.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 -- docs/research_cycles/V72P2D5-GF32-RATE-MOTHER
```
Expected exactly these four untracked files and nothing else:
`GUARD_REWORK_REVIEW_R1.md`, `LOADER_FIX_REVIEW_R1.md`,
`P0_PRE_EXECUTE_REVIEW_R1.md`, `P0_PRE_RESULT_REVIEW_R1.md`.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import pathlib
for r in ['workspace/v72p2d5_p0_cost/20260906_r1','workspace/v72p2d5_g1/20260906_r1','workspace/v72p2d5_g2/20260906_r1','workspace/v72p2d5_g0/20260905_r2','workspace/v72p2d5_g0_recovery/20260906_r1','workspace/v72p2d5_model_f_input/20260907_r1']:
    p=pathlib.Path(r); print(r, p.exists(), sorted(f.name for f in p.iterdir()) if p.exists() else [])
"
```
Expected: P0 4 files, G1 4 files, **G2 absent**, G0 4, G0-recovery 4, Model-F 2.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && grep -nE "execution_authorized|scientific_promotion|next_gate" docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml
```
Expected: nine `false`, `scientific_promotion: false`,
`next_gate: P0_PACKET_REVIEW`.

Any mismatch → STOP.

## 2. STEP 2 — Verify the suite is green (no changes)

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/v72p2d5_p0_accept_pre -q
```
`--basetemp` **must** be under `workspace/`; outside the repository the D4 audit
tests fail spuriously. Expected: `201 passed`. Any failure → STOP.
Remove `workspace/v72p2d5_p0_accept_pre` when done, then re-stat the six roots
and confirm they are unchanged and G2 still absent.

## 3. Frozen facts to transcribe

**What P0 measured** (verbatim from
`workspace/v72p2d5_p0_cost/20260906_r1/results.json`):

| item | value |
| --- | --- |
| phase | `p0-cost` |
| block_length | 64 |
| f_list | 1.0, 1.2 |
| frozen_rows | f=1.0 → m1 49 / m2 43; f=1.2 → m1 59 / m2 52 |
| seeds | 2026090510, 2026090511 |
| decoder_calls | 12 |
| records (f / kind / wall_s / iterations / rss_bytes) | 1.0 app 1.8862763999495655 / 360 / null · 1.0 oracle 1.04731999989599 / 180 / null · 1.2 app 3.459295800072141 / 360 / null · 1.2 oracle 1.671841400093399 / 180 / null |
| projected_g1_s | 161.8241519993171 |
| projected_g2_s | 485.47245599795133 |
| projection_blocked | false |
| passed | true |
| run wall (operator) | 8.6278899 s, exit 0, stdout and stderr empty |
| decode-attributed total | 8.064733600011096 s against the 1440 s cap → no `RESOURCE_OVERRUN` |

**What P0 does NOT establish.** Transcribe this list verbatim; it is the point
of the whole document:

- No correctness result. P0 records cost only; it grades nothing.
- No `exact_failure_fraction`, no FER, no leakage, no key rate, no net rate.
- No qualification of NB-LDPC, the dv3 mother, the rate points, or Model-F.
- No statement that G1 or G2 will pass, complete, or fit their budgets.
- No authorization for anything.

**Carried limitations.** All of these must appear in the accepted record and be
carried into the G1 packet:

- `L1 (depth)` — `_snapshot_dir` sees top-level files only; nested writes under
  a formal root are invisible to the guards. Before G1/G2 produce output the G1
  packet must either make the snapshot recursive or add an explicit
  no-subdirectory invariant, and must state which it takes.
- `L2 (T1_23 narrowness)` — the recurrence guard catches only
  `assert not … .exists()` with a root or literal token in the same assert;
  `os.path.exists`, `is_dir`/`is_file`, alternate operators, indirect
  variables, and non-assert enforcement bypass it. Do not cite it as a general
  absence-assertion ban; the primary protection is the per-test invariance
  assert.
- `L3 (T1_22 live-fire)` — red-on-content-change is established by reading the
  parser logic, not by a live mutation demonstration. If the G1 packet relies
  on T1_22 as a freeze proof, cite the logic, not a live red run.
- `L4 (record correction)` — the guard-rework report's `STATUS=63` figure is
  superseded by the measured 1969 porcelain lines / 1887 modified paths /
  `numstat` content changes 0. No correctness impact; corrected here so future
  reviewers do not chase a phantom clean tree.
- `L-RSS` — Windows has no `resource` module, so `rss_bytes` is `null` in every
  P0 record. The 2 GiB reference could not be checked. G1 must rebuild an RSS
  measurement or explicitly drop the RSS budget with reasons.
- `L-SCALE` — the G1/G2 projections are `per_call × {240, 720}` with no width
  or row-count scaling. G2 runs at width 256 with roughly four times the rows,
  so `projected_g2_s` and `projection_blocked: false` carry **no** permission
  for G2. `projected_g1_s` is a same-width call-count indication only.
- `L-ITER` — every one of the 12 decodes ran the full `MAX_ITER = 90`
  (app 360 = 2 seeds × 2 layers × 90; oracle 180 = 2 seeds × 1 × 90). Nothing
  converged early. P0 checks no correctness, so this is not a failure, but the
  cost signal is a saturated upper bound. G1 must budget at the cap and must
  record exact/syndrome outcomes so "ran to cap" and "failed to converge" can
  be told apart.

**Review chain to record** (all four now landed by this packet):

- `P0_PRE_EXECUTE_REVIEW_R1.md` — `PRE_EXECUTE_REVIEW_PASS`, five open
  questions decided.
- `LOADER_FIX_REVIEW_R1.md` — `LOADER_FIX_REVIEW_PASS`; the Model-F consumer
  path fix (`299416ae`) after the first P0 authorization was consumed with no
  run.
- `P0_PRE_RESULT_REVIEW_R1.md` — `P0_PRE_RESULT_REVIEW_PASS` with limitations.
- `GUARD_REWORK_REVIEW_R1.md` — `GUARD_REWORK_REVIEW_PASS` with L1–L4.

**Authorization history to record:** two P0 authorizations were issued. The
first (2026-09-07, `a71188fb`/`3ecaebb6`) was consumed with no run — the phase
refused in 0.376 s on a false missing-input message caused by the consumer path
defect. The second (`f1cdf970`/`b4696273`) produced this result. Both are
consumed; neither is reusable.

## 4. STEP 3 — Write the acceptance record

Create ONE new file
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_RESULT_ACCEPTANCE_R1.md`
with these sections, filled from §3 and your STEP 1 output:

1. `A01 Status` — `P0_RESULT_ACCEPTED`, scope `COST_MEASUREMENT_ONLY`.
2. `A02 Pre-state` — branch, HEAD, root listing, the nine `false`.
3. `A03 What was measured` — the §3 table verbatim.
4. `A04 What is not established` — the §3 list verbatim.
5. `A05 Carried limitations` — L1, L2, L3, L4, L-RSS, L-SCALE, L-ITER verbatim,
   each marked `MUST_CARRY_INTO_G1_PACKET`.
6. `A06 Review chain` — the four reviews and their verdicts.
7. `A07 Authorization history` — both authorizations, both consumed.
8. `A08 Lifecycle effect` — all nine authorizations stay `false`;
   `scientific_promotion` stays `false`; `next_gate` moves
   `P0_PACKET_REVIEW → G1_PACKET_REVIEW`; acceptance of a cost measurement is
   not scientific promotion and grants no G1 authorization.
9. `A09 Next step` — freeze the G1 execution packet carrying every A05
   limitation, then an independent Pre-EXECUTE review, then a separate explicit
   G1 authorization. These may not be merged or reordered.

Then edit `cycle_state.yaml`, changing exactly:

- `next_gate: P0_PACKET_REVIEW` → `next_gate: G1_PACKET_REVIEW`
- add `p0_cost_result_accepted: true`
- add `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`

Nothing else in that file changes. No authorization key changes.

## 5. STEP 4 — Append two records

Append to the end of `docs/decision-log.md` a dated entry recording: the P0
acceptance and its cost-only scope; the measured scalars; the four-review
chain; the two consumed authorizations and why the first produced no run; the
seven carried limitations; and the explicit consequence that `projected_g2_s`
grants nothing to G2 and that no authorization was created. Follow the file's
existing entry format (Decision / Context / Alternatives considered /
Consequences).

Append to the end of `AGENT_PROJECT_MEMORY.md` a matching dated block in that
file's existing style, tagging claims `[repo-observed]` or `[decision]`.

Append only. Change no existing line in either file.

## 6. STEP 5 — Verification

- Re-run the STEP 1 root stat: six roots unchanged, G2 still absent.
- `grep` `cycle_state.yaml`: nine `false`, `scientific_promotion: false`,
  `next_gate: G1_PACKET_REVIEW`, the two new keys present.
- Content-scope check:
  ```bash
  cd "D:/Code/HD-QKD_Polar_Comparison" && git diff --numstat 2>/dev/null | awk '$1!="0"||$2!="0"{print}'
  ```
  Only `cycle_state.yaml`, `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md`
  may appear. Any other path → STOP.
- No `.py` changed:
  ```bash
  cd "D:/Code/HD-QKD_Polar_Comparison" && git diff --numstat -- '*.py' | awk '$1!="0"||$2!="0"{print}'
  ```
  Expected: empty.

## 7. STEP 6 — One commit (local only, NO PUSH)

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git add docs/research_cycles/V72P2D5-GF32-RATE-MOTHER docs/decision-log.md AGENT_PROJECT_MEMORY.md && git diff --cached --name-only
```
Expected exactly: the four review files, `P0_RESULT_ACCEPTANCE_R1.md`,
`cycle_state.yaml`, `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` — eight
paths. A different set → STOP, do not commit, do not unstage.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git commit -m "result(v72p2d5): accept P0 cost preflight, cost measurement only

Accept the second authorized P0 invocation as a cost measurement and land the
four-review record: Pre-EXECUTE PASS, loader-fix PASS, Pre-RESULT PASS,
guard-rework PASS.

Measured at n_IR 64 over f {1.0, 1.2}: 12 decoder calls, 8.06s
decode-attributed against a 1440s cap, projections 161.8s (G1) and 485.5s
(G2), projection_blocked false.

Establishes no correctness, no exact_failure_fraction, no FER, no leakage, no
key rate, and no qualification. Carries seven limitations into the G1 packet,
including that the projections do not scale with width or row count and so
grant G2 nothing, that RSS was unmeasurable on Windows, and that all 12
decodes ran to the 90-iteration cap.

Both P0 authorizations are consumed; the first produced no run. All nine
execution authorizations remain false; next_gate moves to G1_PACKET_REVIEW.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Verify: `git log --oneline -2` and `git status -sb`. One new commit, `ahead 12`.
Do not push.

## 8. STEP 7 — Report

1. STEP 1 and STEP 5 root stats, and whether identical.
2. The literal pytest line.
3. The staged path list and the commit SHA; `git status -sb`.
4. `true`/`false`: decoder run: false; any `--phase` invoked: false; CAL/VAL
   read: false; any `workspace/` file created, deleted, moved, renamed or
   modified: false; G2 root created: false; any `*_execution_authorized`
   changed: false; any `.py` changed: false; existing `.md` lines changed
   (other than appends): false; pushed: false.
5. State: **P0 is accepted as a cost measurement only. No correctness, rate, or
   qualification claim is made. G1 is neither frozen nor authorized;
   `next_gate` is now `G1_PACKET_REVIEW`.**

Do not propose the G1 parameters. Do not interpret the projections.
