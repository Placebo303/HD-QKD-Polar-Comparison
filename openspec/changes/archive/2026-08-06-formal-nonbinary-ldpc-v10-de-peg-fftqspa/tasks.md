# Tasks: NBLDPC10-DE-PEG-FFTQSPA

## V10-00 — Freeze, Audit, and Seed Derivation

- [x] **V10-00.1** Record starting HEAD, dirty-worktree scope, allowed file
  manifest, frozen V1–V9 file identity (key modules), and absence of V10 official
  output roots.
- [x] **V10-00.2** Freeze V10 seed derivation rules, prove disjointness from all
  prior V8/V9 seeds (V8 prefix 20260804xx, V9 prefix 20260901xx; V10 uses
  prefix 202610xx). Record proof in `evidence/v10_freeze_acceptance.json`.
- [x] **V10-00.3** Freeze module division, allowed imports, forbidden imports,
  root strategies, rank/leakage/RSS caps, and hard stop rules. Document
  microbenchmark non-scientific seed rule.
- [x] **V10-00.4** Write `evidence/v10_literature_crosswalk.md` mapping each of
  the 6 literature groups to V10 implementation locations / differences.

## V10-05 — Microbenchmark (engineering-only, non-scientific)

- [x] **V10-05.1** Run ONE deterministic microbenchmark at q=1024, small pop,
  few generations, non-scientific seed. Measure wall-clock per evaluation and
  confirm RSS < 3 GiB.
- [x] **V10-05.2** Label output `engineering_only_non_scientific`. Must NOT
  produce threshold, winner, or gate claims. Must NOT use S1–S4 formal roots.

## V10-10 — DE + Ensemble Kernel Engineering

- [x] **V10-10.1** Implement `nonbinary_v10_common.py`: sizing `qary_entropy_bits_baseq`,
  `checks_for`, `concentrated_check_distribution` (V8-60 formula), `reconstructed_rate`,
  `edge_mean_inverse`, QSC prior `qsc_channel_message`, status vocabulary,
  seed derivation helper, `ProcessTreeRSSWatcher` (ctypes, no new dependency).
- [x] **V10-10.2** Implement `nonbinary_v10_de.py` with standard DE/rand/1/bin,
  K=8 degree+logit encoding, deterministic bias-free population init,
  mutation/crossover with frozen F/CR/pop_size/max_gen, checkpoint/resume
  (no-overwrite), transcript logging, fail-closed NaN/Inf.
- [x] **V10-10.3** Implement the 6-tier hierarchical lexicographic objective
  function with gate screen (entropy streak → eligibility → binary search on
  eligible candidates). Implement `lambda_validate` (degree uniqueness,
  ≥0.01 per weight, sum=1.0±1e-12).
- [x] **V10-10.4** T0: compile/import, GF(1024) field identities, lambda
  exponent-degree off-by-one mapping, rate/rho exactness (≤1e-12), DE
  deterministic mutation identity test, small q=4 oracle connectivity.
- [x] **V10-10.5** T1: optimizer unit (population init, mutation, crossover,
  selection, checkpoint), objective components (entropy, error probability,
  tie-break), resume/no-overwrite, fail-closed NaN/Inf, max_evaluations check.
- [x] **V10-10.6** Freeze `pre_run_plan.json` after microbenchmark and before
  ANY formal scientific search. Content per design §5.2. Hard caps verified:
  screen evaluations ≤ 600 per search, refinement ≤ 12, RSS ≤ 3 GiB, workers=1.
- [x] **V10-10.7** Obtain independent read-only review of pre_run_plan. On
  REJECT → revise and re-freeze. Budget must NOT change after formal results.

## V10-0 — Q=4 Reference Recovery Gate

- [x] **V10-0.1** Freeze V8-60 Müller q=4 R=0.75 contract as the recovery
  target: degrees {2,4,7,10,19,26,28}, DET published 0.069, tolerance 0.012,
  concentrated ρ {24,25}, n_samples 100000, max_iter 150.
- [x] **V10-0.2** Set up DE search at q=4 with K=8 representation. Optimization
  seed ≠ V8 seed (2026080418) and ≠ all V9 seeds. Do NOT inject the published
  lambda into the initial population.
- [x] **V10-0.3** Run one DE optimization to find the ensemble, then validate
  final winner on at least 2 independent validation seeds (distinct from
  optimization seed).
- [x] **V10-0.4** Gate check: |winner conservative threshold − 0.069| ≤ 0.012.
  Reconstructed rate error ≤ 1e-12. Both validation seeds pass.
- [x] **V10-0.5** Same plan replay: verify winner and scientific payload
  identical. Hash all outputs.
- [x] **V10-0.6** On PASS → record evidence, advance to V10-20. On FAIL →
  freeze all evidence, write gate decision, STOP (failed_reference). No GF(1024)
  work. No parameter tuning or rerun.
- [x] **V10-0.7** T2: complete fake q=4 lifecycle (plan → review → fake execute
  → strict replay), all tamper layers, production runner never entered.

## V10-20 — V10A GF(1024) Ensemble Search and Gate

- [x] **V10-20.1** Create four independent DE search packages S1 (p=.20, f=1.15,
  gate .22), S2 (p=.20, f=1.08, gate .215), S3 (p=.30, f=1.15, gate .32),
  S4 (p=.30, f=1.08, gate .32). All m/R computed, never hard-coded.
- [x] **V10-20.2** One plan-only package freezing all four searches, per-design
  budgets, disjoint optimization/validation seeds (≥3 each), screen/refinement
  protocol, gate reconstruction. Optimization seeds MUST NOT overlap with V8,
  V9, V10-0, or V10-05 seeds.
- [x] **V10-20.3** Independent read-only plan review. If not READY, revise and
  re-freeze. Formal execute runs only after review ACCEPT.
- [x] **V10-20.4** Execute all four searches deterministically exactly ONCE.
  Each search: screen candidates at gate p → eligible refinement → 3+ validation
  seeds → conservative threshold → winner selection.
- [x] **V10-20.5'** Replay close-out (2026-08-06 protocol amendment): check
  whether the prior replay process (PID 21032, last seen 2026-08-06T11:50Z at
  `workspace/v10a_execute/217aa87779de4953a5aeeed24f407b1e/replay/`) survived.
  If alive, wait for 4 search directories + `run_complete.json`. If dead,
  restart replay in a fresh output directory per the `interrupted_attempt.json`
  precedent and S1 byte-deterministic regenerability guarantee. Verify
  scientific files match across execute/replay by **direct byte comparison**
  (file-content equality, no SHA-256 layer). Allow provenance-only diffs:
  `run_meta.json` (pid/utc/elapsed/peak_rss),
  `search_S{1..4}/run_complete.json` (wall_clock_seconds).
- [x] **V10-20.6** Gate decision — executed result (mechanical):
  S1 conservative_threshold=0.2153 < gate=0.22, S2=0.1984 < 0.215,
  S3=0.3166 < 0.32, S4 zero eligible candidates. All FAIL → **failed_ensemble**.
- [x] **V10-20.7'** Write 3 evidence files under `evidence/`:
  `v10a_execute_results.json`, `v10a_replay_evidence.json`,
  `v10a_gate_decision.json`. **No hash fields.** Evidence contains: per-search
  conservative thresholds, gate verdict and reason, replay byte-comparison
  results (direct, not hashed), mechanical gate decision, operator role
  statement (not self-accepted).
- [x] **V10-20.8'** T2: complete fake V10A lifecycle (plan → review → fake execute
  → fake replay), tamper matrix without hash fields:
  - Raw byte drift: direct file-content comparison.
  - Semantic tamper: JSON field change → gate reconstruction disagreement /
    leakage accounting recomputation failure.
  - Plan-binding field validation rejection.
  - Production runner never entered (explicit fake runner guard).
- [x] **V10-20.9'** T3: frozen regression via **git baseline**
  (`git status --porcelain` + `git diff --name-only` checking that frozen
  directories (src/, experiments/, tools/, results/) and allowed file manifest
  are unchanged). No unauthorized output under
  `comparison_bench/outputs_comparison/formal_ir_methods/`.

- [x] **V10-20.CODE.1** Coder revision: `nonbinary_v10_peg.py` — replace
  `_tie_hash` (SHA-256 tie-break, L267-271) with seeded RNG deterministic
  tie-break using `numpy.random.default_rng(common.v10_seed(f"peg_tie:{seed}:v:{v}:s:{socket}"))`
  + `rng.permutation` → pick first. Replace `peg_manifest` (L511-541) to
  remove `self_hash` and `source_hash` fields; manifest contains construction
  parameters only. Remove `hashlib` import if no other uses remain.
- [x] **V10-20.CODE.2** Coder revision: `workspace/v10a_execute/217aa87779de4953a5aeeed24f407b1e/run_v10a_execute.py` —
  remove `V10A_PLAN_SHA256`/`PRE_RUN_PLAN_SHA256` hardcoded constants (L99-100);
  in `check_plan_binding` (L192-322) remove `sha256_file` comparisons (L195-204),
  retain field-level validation only; in `run_meta` (L774-775) remove
  `v10a_plan_sha256`/`pre_run_plan_sha256` fields; in `compare_dirs` (L820-851)
  replace `sha256_file` with direct `open()` byte comparison; in
  `build_evidence` (L854-959) remove `plan_binding` hash fields (L875-878);
  remove `sha256_bytes`/`sha256_file` helpers if no other uses remain.
- [x] **V10-20.CODE.3** Coder revision: `test_nonbinary_v10_gate.py` — in
  `strict_replay` (L196-217) replace `_sha256_file` comparison with direct
  `open()` byte equality; in `test_t2_fake_promotion_byte_drift` (L431-446)
  replace `_sha256_file` with direct comparison; remove `_sha256_file` helper
  and `hashlib` import if no other uses remain.
- [x] **V10-20.CODE.4** Coder revision: `test_nonbinary_v10_peg.py` —
  replace `test_peg_manifest_self_hash` (L187-202) with parameter-only
  manifest assertion (verify schema, status, construction fields; assert
  `self_hash`/`source_hash` keys absent). Remove `hashlib` import if no other
  uses remain. `common.v10_seed("peg_labels:2026100300")` test preserved
  unchanged (v10_seed is retained).

## V10-30 — V10B PEG Codebook (n=4096)

**HALTED — V10A failed_ensemble; no PEG construction authorized.**

Only after V10-20 ensemble gate PASS (robust_only or target_ready) — condition
not met. All sub-tasks are blocked; the following design-level revisions apply
for consistency if V10-30 is ever unfrozen in a successor change:

- [ ] **V10-30.DESIGN** PEG tie-break uses seeded RNG deterministic (not SHA-256);
  `peg_manifest` contains construction parameters only (no self-hash/source-hash).
  Original SHA-256 tie-break and manifest hash fields are removed.

(Original V10-30.1–V10-30.7 sub-tasks frozen but not executable; left
below for structural completeness only.)

- [ ] **V10-30.1** Implement `nonbinary_v10_peg.py`: node-view degree count
  conversion, concentrated check degree counts, socket consistency validation,
  deterministic irregular PEG (local girth → ACE → seeded RNG tie-break), trial
  cap, seeded uniform nonzero GF(1024) edge labels, parallel-edge detection,
  `rank_GF1024(H)` via Gaussian elimination, syndrome round-trip test, manifest
  with construction parameters only.
- [ ] **V10-30.2** Freeze PEG construction parameters: max_peg_trials (trial
  cap), seed, n=4096, m from selected tier formula, lambda from V10A winner,
  edge-label seed.
- [ ] **V10-30.3** Execute PEG construction exactly once. Verify: no parallel
  edges, degree sequences exact, rank(H) = m, syndrome round-trip passes,
  manifest complete. If trial cap exhausted → frozen failure, STOP.
- [ ] **V10-30.4** T0: compile/import, lambda-to-node-view conversion, socket
  math, GF(1024) rank on small matrices.
- [ ] **V10-30.5** T1: PEG deterministic identity (same seed → same graph),
  parallel-edge detection, degree sequence check, rank on bounded matrices,
  edge-label nonzeroness, trial-cap behavior, no-overwrite manifest.
- [ ] **V10-30.6** T2: fake PEG lifecycle (prepare → fake execute → verify),
  tamper: raw bytes (direct comparison), degree sequence, edge labels.
- [ ] **V10-30.7** T3: frozen regression (git baseline), no unauthorized output.

## V10-40 — V10B FFT-QSPA Decoder (n=4096)

**HALTED — V10A failed_ensemble; no decoder work authorized.**

Only after V10-30 PEG codebook complete — condition not met.

(Original V10-40.1–V10-40.7 sub-tasks frozen but not executable.)

## V10-50 — V10B Sacrificed Canary

**HALTED — V10A failed_ensemble; no canary work authorized.**

Only after V10-30 and V10-40 engineering ACCEPT plus independent review —
condition not met.

(Original V10-50.1–V10-50.7 sub-tasks frozen but not executable.)

## V10-60 — V10C Development

**HALTED — V10A failed_ensemble; no development work authorized.**

Only after V10-50 canary gate PASS — condition not met.

(Original V10-60.1–V10-60.6 sub-tasks frozen but not executable.)

## V10-70 — Close-Out (final state: failed_ensemble)

- [x] **V10-70.1** Write final state `failed_ensemble` to
  `evidence/v10_gate_decision.json`. Record all gate results (S1–S4 thresholds,
  verdicts, reasons), mechanical gate computation, V10A state machine terminal
  node. **No hash fields.** Schema: `v10_gate_decision_v1`.
- [x] **V10-70.2** Independent final review: reviewer-go read-only ACCEPT/REJECT
  on all checklist items (matches OpenSpec spec, tests pass, no scope creep,
  decision log updated, no unauthorized artifacts, scientific wording scoped,
  no hash fields in new evidence files, completed evidence files preserved
  immutably).
- [x] **V10-70.3** Update `docs/decision-log.md` with V10A failed_ensemble
  entry: dates, gate values, why no "closest to gate", successor V11 path.
- [x] **V10-70.4** Update `CURRENT_TASK.md`, `AGENT_HANDOFF.md`, and
  `AGENT_PROJECT_MEMORY.md` with verified facts only: final state
  failed_ensemble, V10-30–V10-60 halted, v10_seed retained as deterministic
  RNG primitive, hash mechanisms removed per 2026-08-06 amendment.
- [x] **V10-70.5** Freeze baseline git verification: `git status --porcelain`
  + `git diff --name-only` confirms frozen directories (src/, experiments/,
  tools/, results/) and allowed file manifest are unchanged. No unauthorized
  output under `comparison_bench/outputs_comparison/formal_ir_methods/`.
  Workspaces documented; all failed evidence retained immutably.
- [x] **V10-70.6** Memory triage: memory agent reviews all V10 evidence,
  updates AGENT_PROJECT_MEMORY.md with durable facts, records any unresolved
  tensions.
- [x] **V10-70.7** S4 delta correction record (evidence/v10_s4_delta_correction.json; script build_evidence expression fixed)
- [x] **V10-70.8** Establish precise Git provenance: scoped local commit of V10 artifacts (change dir, V10 modules, V10 tests), provenance evidence file; no push.
- [ ] **V10-70.9** Archive the V10 change to openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/ (no spec sync; failed_ensemble).

---

## Frozen Acceptance Matrix

| ID | Acceptance condition |
|----|---------------------|
| V10-A01 | Additive scope; frozen baseline and V1–V9 unchanged |
| V10-A02 | Seed derivation proves disjointness from all V8/V9 seeds |
| V10-A03 | K=8 representation validates degree uniqueness, ∑λ_d=1, min weight ≥0.01 |
| V10-A04 | Concentrated ρ satisfies harmonic-exact rate equation (≤1e-12) |
| V10-A05 | DE/rand/1/bin deterministic; checkpoint/resume; fail-closed NaN/Inf |
| V10-A06 | 6-tier lexicographic objective: entropy gate → convergence → error → threshold → tuple |
| V10-A07 | V10-0 q=4 Müller recovery: |threshold − 0.069| ≤ 0.012, ≥2 validation seeds |
| V10-A08 | V10A four-search package frozen, executed once, strict-replayed once |
| V10-A09 | V10A robust gate .22/.32 applied; target gate .215/.32 applied |
| V10-A10 | PEG: no parallel edges, rank(H)=m, socket equality, degree sequence exact |
| V10-A11 | FFT-QSPA: coefficient permutation correct, syndrome shift, no Alice truth |
| V10-A12 | Oracle validation at q=4/q=8/GF(1024) against V8 direct oracle |
| V10-A13 | V10B canary lifecycle and gate mechanically reconstructed |
| V10-A14 | V10C development lifecycle and gate mechanically reconstructed |
| V10-A15 | Leakage L_recon=10·m, L_total=10·m+64; no other payload |
| V10-A16 | Evidence integrity via direct byte comparison, field-level validation, and git baseline (no hash fields in new evidence); tamper coverage complete |
| V10-A17 | Peak RSS ≤ 3 GiB all stages; budget frozen before formal results |
| V10-A18 | No unauthorized output, staging, committing, or pushing |

## Hard Stop Rules (Checklist)

- [ ] **V10-S01** V10-0 fails q=4 reference recovery (did NOT trigger — V10-0 PASSED)
- [x] **V10-S02** V10A robust gates (S1 < .22 or S3 < .32) fail — **TRIGGERED**
- [ ] **V10-S03** Planned or formal seed overlap with V8/V9/prior V10 stages
- [ ] **V10-S04** Tuning after formal results needed
- [ ] **V10-S05** Peak RSS > 3 GiB
- [ ] **V10-S06** Single execute > 24 h predicted before plan review
- [ ] **V10-S07** Production decoder accesses Alice truth
- [ ] **V10-S08** Evidence overwritten
- [ ] **V10-S09** Reviewer-go REJECT
- [ ] **V10-S10** Canary stratum < 3/4 verified
- [ ] **V10-S11** Development stratum < 15/16 verified

## Operator Return Conditions

Return only when either:

1. **COMPLETE**: all reachable tasks through the first mandatory STOP gate are
   complete, final state ∈ {failed_reference, failed_ensemble, robust_only_failed_canary,
   target_failed_canary, development_not_ready, development_ready_not_qualified},
   evidence/verifiers/independent review/memory triage/documentation closed.
   Changed files, commands/results, evidence paths, gate results, and exact
   next authorization must be listed.

2. **BLOCKED**: concrete blocker with exact failing command, full error/traceback,
   attempted safe remedies, changed files and preserved artifacts, current
   gate/phase, and the single decision needed from the main thread. Do not
   return "in progress" or request routine stage approval.

---

## Task Summary

| Phase | Tasks | Gate |
|-------|-------|------|
| V10-00 | Freeze, audit, seeds, literature crosswalk | Complete |
| V10-05 | Microbenchmark (non-scientific) | Complete |
| V10-10 | DE + ensemble kernel + T0/T1 | Complete |
| V10-0 | Q=4 reference recovery gate | PASS |
| V10-20 | V10A four-search + gate | failed_ensemble → STOP |
| V10-30 | PEG codebook n=4096 | HALTED (failed_ensemble) |
| V10-40 | FFT-QSPA decoder | HALTED (failed_ensemble) |
| V10-50 | Sacrificed 4+4 canary | HALTED (failed_ensemble) |
| V10-60 | Development 16+16 | HALTED (failed_ensemble) |
| V10-70 | Close-out (failed_ensemble) | Evidence, review, memory triage |
