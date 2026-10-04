# U1-CEILING-PROBE — Frozen Executable Packet (Packet F)

> **THE BOUND, STATED FIRST — before anything else in this packet, because it determines what this stage can possibly be worth and prevents it being read as an improvement opportunity.**
> `H(U1|B) ≈ 0.024` bits/symbol against `H(A|B) ≈ 0.826`, so u1 contributes about 2.9% of the conditional entropy. Perfect u1 can therefore reduce total disclosure by at most about 0.024 × 1024 ≈ 24.6 bits per superframe, i.e. roughly 0.03 in `f` (24.576 / (1024 × 0.826) ≈ 0.029). **Any outcome of this probe leaves option F closed as an improvement route, because this ceiling binds regardless of what the probe finds — the probe's value is diagnostic, not developmental** (§5.4).

- **Status**: FROZEN — awaits Pre-EXECUTE measurement + execution under the grant below (§14). This packet authorizes nothing by itself.
- **Track**: **EXPLORE** — justification against `AGENTS.md` §1.2 in §0.1.
- **Proposal authority**: `docs/research_cycles/NEXT-STEP-OPTIONS/PROPOSAL.md` §§1 (Option F), 2 (row F), 4. This packet freezes what that document sketched; it redesigns nothing. Any conflict between this packet and the proposal is a STOP (§9), not a patch license.
- **Branch**: `formal-ir-v72p1-addendum-clean`. No commit, no push by the operator.
- **Order note (main's judgement, recorded per tasking)**: **Packet F runs alongside A because it is nearly free and closes a bounded question** — zero-decode arithmetic over already-persisted artifacts, completable in minutes plus one batch-end review.

---

## §0 Goal / Non-Goals / Impact Scope / Classification

### Goal

Using **already-persisted artifacts only**, determine the u1 argmax error rate on the real evaluation frames — the exact superframe-level u1 disagreement rate among u2 successes from persisted `full10_match` booleans, plus a per-symbol rate under a named, stated inversion — and set it against the u2 per-symbol rate and the entropy share, so the disagreement between the error-rate ratio and the entropy share is visible rather than glossed.

### Non-Goals

- No raw-data contact of any kind: no `.ttbin`, no channel bundle, no `(a,b)` array recomputation. The stronger exact per-symbol probe is explicitly out of scope (§12.2).
- No decoder call, no construction call.
- No FER, efficiency, leakage, `f`, SKR, or key figure; no method claim; no "u1 is/is not a bottleneck" beyond the bounded statement in the header box (§11).
- No route closure, qualification, publication number, or acceptance of any method.
- No modification of any runner, construction, decoder, config, existing workspace root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, or `AGENTS.md`.
- No commit, no push.

### Impact Scope

- **Written by this stage**: exactly two new repo files — `comparison_bench/src/comparison_bench/cli/u1_ceiling_probe.py` (additive counting + inversion arithmetic, T-PU01) and `comparison_bench/tests/test_u1_ceiling_fake.py` (fake-only test, T-PU02) — plus this packet (already written by the planner), plus all execution outputs inside one fresh additive root `workspace/u1_probe_<uuid8>` (§6).
- **Read-only inputs**: the §2 frozen list only. Nothing else is opened for content.
- **Untouched**: `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root, `docs/NOW.md`, `docs/decision-log.md`, `openspec/`, `AGENTS.md`.

### §0.1 Track classification: EXPLORE — justification against `AGENTS.md` §1.2

Packet F is **EXPLORE**, confirmed against the §1.2 applicability matrix row "Synthetic diagnostics → EXPLORE: packet+prompt, machine root, one log, one batch-end review", extended by the `STAGE0_PACKET.md` §0.1 precedent (arithmetic over frozen persisted numbers is not data contact):

1. **Input character**: the inputs are already-persisted, closed-batch statistics and booleans (`rows.json` per-superframe `exact_match`/`full10_match`/`undetected` fields plus arm summaries) from the closed M0 DECIDE batch. The stage opens no `.ttbin`, no channel bundle, no `(a,b)` array, no raw data of any kind (§2.3). Counting persisted booleans is not real-data contact.
2. **Bounded and reversible**: one process, one CPU, wall ≤ 600 s, RSS ≤ 2 GiB (§8); one fresh additive root, append-only (§6). Three `rows.json` total ≈ 445 KiB; the work is seconds-scale counting plus inversion arithmetic.
3. **No claim**: the §11 ceiling forbids every claim-bearing figure and every method statement beyond the header-box bound. The output is a diagnostic table plus the §5 consequence (F closed as an improvement route under every outcome).
4. **Uncertainty default**: no concrete risk named here defaults this to DECIDE. The foreseeable failure modes (input drift, predicate misreading, silent pooling) are met by the size/mtime gate (PU-01), the frozen predicates (§3), the no-pooling rule (§4), the fake-only test (§10 P-3), and the batch-end review (PU-05) — not by escalation. The escalation boundary is fenced explicitly instead: any `(a,b)`-level recomputation is the named DECIDE successor F2-EXACT-U1 (§12.2), never a repair or extension of this packet.

---

## §1 The frozen question

Using already-persisted artifacts only, what is the u1 argmax error rate on the real evaluation frames, and does it sit anywhere near the level that would matter? The M0 real roots persist a per-superframe `full10_match` boolean per arm; from that, plus the u2-success counts, the superframe-level u1 disagreement rate is exact, and the per-symbol rate is obtainable only by the stated IID-INVERSION (§3.3) under an explicit independence assumption whose weakness is acknowledged in the packet.

---

## §2 Frozen input list (read-only)

Exactly these six files. No other file is opened for content by the execution.

| # | Path | Bytes | UTC mtime (measured) | Role |
|---|---|---|---|---|
| I-1 | `workspace/m0_359922a7_1M/rows.json` | 104931 | 2026-09-24 11:06:33 UTC | 1M per-superframe rows (`m`, `superframe`, `exact_match`, `undetected`, `full10_match`, `status`) + summary (205 superframes; arms m=197/201) |
| I-2 | `workspace/m0_642a8fe8_1p5M/rows.json` | 146036 | 2026-09-24 11:11:19 UTC | 1p5M rows + summary (287 superframes; arms m=203/207) |
| I-3 | `workspace/m0_b1a9142d_2M/rows.json` | 194222 | 2026-09-24 11:27:35 UTC | 2M rows + summary (383 superframes; arms m=204/208) |
| I-4 | `workspace/m0_359922a7_1M/M0_RESULT_1M.md` | 927 | 2026-09-24 11:06:33 UTC | 1M arm-level summary (`fails_full10` 132/132 per arm — cross-check context) |
| I-5 | `workspace/m0_642a8fe8_1p5M/M0_RESULT_1p5M.md` | 932 | 2026-09-24 11:11:19 UTC | 1p5M arm-level summary (`fails_full10` 145/139 — cross-check context) |
| I-6 | `workspace/m0_b1a9142d_2M/M0_RESULT_2M.md` | 936 | 2026-09-24 11:27:35 UTC | 2M arm-level summary (`fails_full10` 182/180 — cross-check context) |

Reference constants carried from planning (frozen references, not execution inputs — the script reads no additional file for them): per-source u2 references `ser` = 0.23856707 (1M, CQ-J21a) / 0.25433839 (1p5M, CQ-J21b) / 0.25375836 (2M, CQ-J21c); per-source entropy shares `H(U1|B)/H(A|B)` = 0.02415075/0.79837921 (J21a), 0.02422924/0.82351165 (J21b), 0.02491156/0.82567853 (J21c) — all from `CHAN-QUALITY-SURVEY/RESULT.md` §3. Five-capture `ser` range **0.23856707–0.25433839**. Plane count is **ten** (`nonbinary_v25_gate.py:28` `BITS = 10`).

### §2.1 Input-transcription discipline

The script reads the JSON values, never this packet's transcription. The `fails_full10` figures above are carried as cross-check context only (the derivation counts rows directly). Any mismatch between a summary figure and the corresponding row count is a STOP under §9 — summaries never override rows, rows never get "corrected" to match summaries.

### §2.3 Explicit raw-data-contact prohibition

**Explicitly forbidden.** There is a stronger version of this probe that recomputes the exact per-symbol u1 error count from the real `(a,b)` arrays, but that requires opening raw data and is a DECIDE step. It is **out of scope here, must not be run, and would need its own packet and grant**. It is recorded as the named successor option F2-EXACT-U1 (§12.2), not as pending work in this packet. The script's allowed-input gate (T-PU01) refuses any path outside the six frozen above and any path ending in `.ttbin`, `.npz`, `.parquet`. The `block_accounting.csv` files beside the M0 roots are not inputs and stay unopened.

### §2.4 Standing citation discipline

Where the channel structure is invoked, use verbatim the standing fenced forms from `CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B: "**zero observed cross-plane co-error; single-plane-flip structure**" (triple evidence + detection-floor caveat whenever "independent" is used); the negative only as "**no measured easier point among the five captures; the unmeasured groups supply no evidence of one on recorded grounds**". Legacy `0.098260` is never cited as a measurement (N-9 form governs if mentioned at all).

---

## §3 Exact derivation (frozen)

Per arm `a` ∈ {1M-m197, 1M-m201, 1p5M-m203, 1p5M-m207, 2M-m204, 2M-m208}, counted from the corresponding `rows.json` rows with `r.m == m_a`. No assumption about implication relations between the booleans is made — every combination is handled by explicit predicates:

- **U2-success set**: `S_a = { r : r.exact_match == true AND r.undetected == false }`. `undetected` rows are excluded from numerator and denominator alike and reported as a separate per-arm count (never merged into success — M0 acceptance precedent).
- **U1-disagree set**: `D_a = { r ∈ S_a : r.full10_match == false }`.
- **(a) Exact superframe-level u1 disagreement rate among u2 successes**: `R_a = |D_a| / |S_a|`. Exact — no model, no assumption. If `|S_a| = 0` the rate is undefined: STOP, never zero-filled.
- **(b) Per-symbol rate under inversion**: `q_a = 1 − (1 − R_a)^{1/1024}`.

### §3.3 The IID-INVERSION assumption (named, stated, weakness acknowledged)

**IID-INVERSION**: per-symbol u1 errors are i.i.d. across the 1024 symbols of a superframe, so `P(superframe u1-clean) = (1−q)^1024`. Weakness, acknowledged and frozen: a superframe-level boolean cannot by itself identify a per-symbol count. If u1 errors burst (correlated within a superframe), the same `R_a` arises from fewer, worse superframes — then `q_a` **overstates** the typical-symbol rate and **understates** concentration. Conditioning on u2 success may additionally select easier superframes, in which case `q_a` **understates** the unconditional u1 error rate. `q_a` is therefore a diffuse-error-equivalent index, not a measured per-symbol count. The exact per-symbol truth requires `(a,b)` contact and belongs to F2-EXACT-U1 (§12.2).

---

## §4 Frozen comparison (no pooling)

Per arm (six columns, never pooled across arms or sources — M0 acceptance precedent: no cross-source/arm merging):

1. `R_a` (exact) and `q_a` (under IID-INVERSION), with `|S_a|`, `|D_a|`, undetected count.
2. `q_a` against the u2 per-symbol reference `ser` of the corresponding capture (1M→CQ-J21a 0.23856707; 1p5M→CQ-J21b 0.25433839; 2M→CQ-J21c 0.25375836), as the ratio `q_a / ser` — on record either way.
3. `q_a / ser` against the entropy share `H(U1|B)/H(A|B)` of the corresponding capture (≈ 3.0% per source: 3.02% / 2.94% / 3.02%), displayed side by side — so the disagreement between the error-rate ratio and the entropy share is visible rather than glossed. (They measure different things — argmax-estimator quality vs information content — and the table must not merge or reconcile them.)

---

## §5 Frozen decision rule (with consequence per outcome; the 0.03 ceiling binds every branch)

> **§5.1** Whatever values `R_a`/`q_a` take on any or all arms — `q_a` far below `ser` (expected: argmax-u1 already nearly optimal), comparable to `ser` (unexpected: diagnostic anomaly), or anything in between — **option F stays closed as an improvement route**. The header-box ceiling (≈ 24.6 bits/superframe, ≈ 0.03 in `f`) binds regardless of what the probe finds.
>
> **§5.2** If `q_a ≪ ser` on all arms (diffuse-equivalent u1 error at or below the ~10⁻³ scale while u2 errors sit at ~0.25): record "u1 path nearly optimal; headroom bounded by the header ceiling; no u1 development follows". This packet is then complete — no successor needed.
>
> **§5.3** If any `q_a` is comparable to its `ser` (same order of magnitude): record a diagnostic anomaly — the argmax-u1 estimator is lossy at a scale the entropy share does not suggest — and return to main with the frozen table. Any follow-up (including F2-EXACT-U1) requires a **new packet + new grant**; this packet licenses no development, no estimator change, no coding of u1.
>
> **§5.4 What this stage does and does not license.** The probe's value is diagnostic, not developmental. No outcome licenses u1 development, estimator work, disclosure-accounting changes, or any execution beyond this packet.

---

## §6 Deliverables and where each goes

One fresh additive root, fixed at Pre-EXECUTE: `workspace/u1_probe_<uuid8>/` (uuid8 recorded in §14 P-6). **No existing root may be written.**

| # | File | Content |
|---|---|---|
| D-1 | `workspace/u1_probe_<uuid8>/U1_RESULT.json` | One JSON: `inputs` (6 paths + byte sizes + UTC mtimes), per-arm `S/D/R/q` with undetected counts, `comparisons` (per-arm `q/ser` + entropy share side by side), `decision` (which §5 clause fired + evidence pointers), `resources` (wall_s, peak RSS, CPU, command, thread-pin env) |
| D-2 | `workspace/u1_probe_<uuid8>/U1_SUMMARY.md` | Short Markdown: the six-arm table, the header-box bound restated, the fired §5 clause, the §11 ceiling restated verbatim. No bottleneck sentence beyond the bounded statement; no method sentence |
| D-3 | `workspace/u1_probe_<uuid8>/U1_LOG.md` | Single append-only log (EXPLORE contract): attempts, machine-gate results, the preregistered repair if used (§8), retained failures, final evidence pointer, review pointer |
| D-4 | `workspace/u1_probe_<uuid8>/BATCH_END_REVIEW.md` | Independent batch-end review against PU-01…PU-06 (§7). FAIL blocks promotion of every number in this batch; rework + re-review, never publish-then-patch |

---

## §7 Acceptance items (stable IDs)

| ID | Item | Verify against |
|---|---|---|
| PU-01 | Input fidelity: exactly the six §2 paths opened, byte sizes + UTC mtimes match the table; no `.ttbin`/`.npz`/`.parquet`/`(a,b)`/raw path opened (script path-gate + log) | `U1_RESULT.json` `inputs` + `U1_LOG.md` + script source |
| PU-02 | Derivation fidelity: `S_a`/`D_a`/`R_a` predicates per §3 applied per arm from rows (never from summaries); `q_a` via the frozen inversion; `\|S_a\| = 0` would STOP, never zero-fill; `undetected` excluded and separately reported; no cross-arm/source pooling | fake test (§10 P-3) + reviewer hand-check of ≥1 arm |
| PU-03 | Comparison completeness: all six arms carry `q_a`, `q_a/ser`, and the entropy share side by side; error-rate ratio vs entropy share displayed without merging | `U1_RESULT.json` `comparisons` |
| PU-04 | Budget + no-overwrite: wall ≤ 600 s, peak RSS ≤ 2 GiB, 1 CPU, threads pinned, one process, sequential; fresh `workspace/u1_probe_<uuid8>` only; `results/`, `comparison_bench/outputs_comparison/`, all pre-existing `workspace/` roots untouched; `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly the §10 scoped manifest | filesystem + git state + log |
| PU-05 | Deliverables + review: D-1…D-4 complete in the fresh root; header bound + §11 ceiling respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| PU-06 | Claim-ceiling machine check: no numeric FER/efficiency/leakage/`f`/SKR/key figure anywhere in D-1…D-4 (outside the quoted header bound and §11 ceiling); no "u1 is/is not a bottleneck" sentence beyond the bounded statement; no method claim; the void baselines return **zero hits**; the stronger `(a,b)` recomputation was not attempted (no forbidden-path attempt in the log) | `rg` over `workspace/u1_probe_<uuid8>` + reviewer read |

---

## §8 Budget (frozen ceiling)

One process, one CPU, threads pinned (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`), sequential, **no retry, no resume** except the single preregistered infra repair below. Wall **≤ 600 s**, peak RSS **≤ 2 GiB**. Breach ⇒ INCOMPLETE, retained, never continued.

Basis (stated): three `rows.json` total ≈ 445 KiB; the work is boolean counting plus six closed-form inversions — the same class as Stage-0 JSON arithmetic (measured 0.39 s outer / 0.015 s internal). The 600 s ceiling is headroom by three orders of magnitude and is never the thing under test.

**Preregistered repair (single, infra-only)**: at most one repair+rerun, only for infrastructure failure (process crash, OOM-kill, tool-side timeout, lost transcript) with **unchanged** scientific inputs, predicates, inversion, thresholds, and decision rule; the failed attempt is retained in `U1_LOG.md` in the same root. Any change to a predicate, the inversion, or the §5 rule is not a repair — it is a new packet.

---

## §9 Stop rules (any one ⇒ stop, retain evidence, return to main)

1. Any of the six §2 files absent, unreadable, or size/mtime drifted from the table.
2. A summary-vs-rows mismatch (§2.1) — summaries never override rows.
3. `|S_a| = 0` on any arm (undefined rate — never zero-filled).
4. A derivation ambiguity as written here (do not interpolate — stop).
5. Any attempt, successful or attempted, at raw-data contact: `.ttbin`, bundle/`.npz`, `pairs.parquet`, `(a,b)` recomputation, or the stronger exact per-symbol probe.
6. Any pooling across arms or sources, any invented count, any relabelled status.
7. Budget breach (§8).
8. Output collision (`workspace/u1_probe_<uuid8>` already exists) or any write inside an existing root, `results/`, or `comparison_bench/outputs_comparison/`.
9. Any evidence-label error (a number cited with the wrong arm/source/file, a fenced §2.4 sentence altered, the header bound restated with different numbers).

On stop: retain all evidence in place, **do not adjust inputs to fit**, return to the main thread with the failing check, the exact command, and the exact error. No rerun except the §8 preregistered infra repair.

---

## §10 Pre-EXECUTE checklist (main measures in one session before execution)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new repo files = exactly two: `comparison_bench/src/comparison_bench/cli/u1_ceiling_probe.py` + `comparison_bench/tests/test_u1_ceiling_fake.py` (scoped manifest). This packet file itself is the planner's already-written deliverable |
| P-3 | Focused test — **new fake-only test REQUIRED** | **Exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_u1_ceiling_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/u1_probe__pytest_<uuid8>` root. **Why new code needs a new test**: T-PU01 adds new counting/inversion logic (predicates, IID-INVERSION, no-pooling, path refusal) covered by no existing test. **What the fake asserts** (hand-computable constants, zero data contact — reads no M0 JSON, nothing): a hand-built 8-row × 2-arm fake (`exact`/`full10`/`undetected` pattern with a known `R` per arm, including one `undetected` row excluded from `S`) yields the exact hand fractions; `q` matches `1−(1−R)^{1/1024}` to 1e-12; per-arm separation holds (no pooling — arm totals never merged); and the input path-gate refuses planted `.ttbin`/`.npz` paths before any read |
| P-4 | Input size/mtime check | `stat` the six §2 paths: byte sizes + UTC mtimes match the table exactly (values only — the planner's read already proved content; this is a drift check) |
| P-5 | Output absence | `workspace/u1_probe_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-6 | Exact command frozen | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.u1_ceiling_probe --rows <I-1> <I-2> <I-3> --summaries <I-4> <I-5> <I-6> --root workspace/u1_probe_<uuid8> --execute --execution-authorized` (refuse without both flags). Root uuid8 fixed here at Pre-EXECUTE |
| P-7 | Budgets + stops read back | §8 ceilings and §9 stop rules read back verbatim |
| P-8 | Protected roots + forbidden reads | Prove the six input files' parent roots are otherwise untouched (no writes); `rg` the T-PU01 script for `ttbin|npz|parquet|decode|construct|bundle|\(a,\s*b\)` open/decode-shaped tokens returns only the refusal-gate lines (zero read paths) |

---

## §11 Claim ceiling (verbatim — binds the execution, the review, and any citation; quoted verbatim in every artifact together with the header bound)

> This stage produces a bounded u1 diagnostic, nothing more. It establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure; NO claim that u1 is or is not a bottleneck beyond the bounded statement that perfect u1 saves at most about 24.6 bits per superframe, about 0.03 in f; NO method claim of any kind; and the void HDC and void Layered-Binary figures are never used as a baseline in any form. The exact per-symbol u1 truth is not established here and belongs to a future DECIDE packet, if any.

---

## §12 What this stage cannot decide

1. **The exact per-symbol u1 error count.** `q_a` is a diffuse-error-equivalent index under IID-INVERSION (§3.3), not a measurement. The truth needs `(a,b)` contact.
2. **The stronger exact probe (named successor, not pending work).** **F2-EXACT-U1 (DECIDE)**: recompute exact per-symbol u1 error counts from the real `(a,b)` arrays. Requires its own packet, full DECIDE gates (prereg + Pre-EXECUTE + explicit grant + Pre-RESULT + acceptance), and its own authorization. **Nothing in the present grant authorizes it; it must not be run, prepared, or begun under this packet.**
3. **Anything about codes, estimators, or development.** No outcome here funds, designs, or justifies u1 work of any kind (§5.4).

---

## §13 Carried corrections (binding on this packet)

- **§13.1 Ten Gray planes, not nine** (as `STAGE0_PACKET.md` §13.1). The 1024-symbol superframe / 1024-bit plane-block framing is carried unchanged.
- **§13.2 Inversion fixed as IID with acknowledged weakness.** The options sketch ("the per-symbol rate is obtainable") is frozen here as exactly one named inversion (IID-INVERSION, §3.3) with both failure directions stated (burst ⇒ `q_a` overstates diffuse rate; u2-conditioning ⇒ possible understatement). No alternative inversion (burst-model, conditional, per-position) is authorized — each would be a new packet.

---

## §14 Grant block

- Grant verbatim: 「可以冻结，然后直接开始按你觉得比较好的顺序来」
- Date / granter: 2026-09-28, user.
- Scope: this grant covers **freezing this packet and executing it within the §8 ceilings only** — main's recorded judgement is that **this packet (F) runs alongside A because it is nearly free and closes a bounded question**. Nothing else is authorized: the remaining options in `NEXT-STEP-OPTIONS/PROPOSAL.md` (B, C, D, E, G) and any DECIDE real-frame, qualification, or publication-claim work remain unauthorised and each needs its own packet + grant. Neither this packet nor Packet A authorizes anything beyond itself.

---

## §15 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-PU01** — Implement `comparison_bench/src/comparison_bench/cli/u1_ceiling_probe.py` (new file only): stdlib (+ numpy if needed for the inversion; `math` suffices); argv takes exactly the §2 paths + `--root workspace/u1_probe_<uuid8>` + dual `--execute --execution-authorized` flags (refuse without both); startup path-gate refuses any input outside the frozen six and any `.ttbin`/`.npz`/`.parquet` path; §3 predicates per arm from rows (summaries = cross-check only, §2.1); IID-INVERSION §3.3; §4 six-column comparison with no pooling; writes D-1 + D-2 + appends D-3 log lines into the fresh root only; prints the fired §5 clause last; `main() -> int` + `if __name__ == "__main__"` house style. No `src/` touch. Per `AGENTS.md` §5.7: simplest implementation that is scientifically correct — no checksums, no atomic writes, no locking, no retry framework, no caching.
2. **T-PU02** — Implement `comparison_bench/tests/test_u1_ceiling_fake.py` per §10 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/u1_probe__pytest_<uuid8>` roots; zero scientific/real-data contact — hand constants only, reads no input file).
3. **T-PU03** — Pre-EXECUTE measurement (§10 P-1…P-8) by main; fill the execution root uuid8 only on PASS.
4. **T-PU04** — Execute the single frozen §10 P-6 command; operator writes D-1…D-3. Any STOP (§9) retains evidence and returns to main; the only permitted rerun is the §8 preregistered infra repair.
5. **T-PU05** — Independent batch-end review → D-4 (`BATCH_END_REVIEW.md`) against PU-01…PU-06; FAIL ⇒ rework + re-review, never publish-then-patch.

**Size note for orchestrator**: small enough to implement directly — one additive counting script (~120 lines: frozen predicates, closed-form inversion, no-pooling table, frozen-path gate) plus one fake-only test with hand-computable booleans. No full pipeline needed. No `/opsx-explore` needed: every primitive (predicates, inversion, references, budget chain) is frozen above.
