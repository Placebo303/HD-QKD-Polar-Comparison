# Tasks: Formal Nonbinary LDPC v5 Multistage IR

## Phase 1: Planning freeze (all four routes pre-registered)

- [x] 1.1 (V5-P0) Bind immutable v1-v4 evidence; freeze allowed/forbidden
  scope; freeze route order A→B→C→D and stop-on-first-promotion. Route A runs
  unconditionally; B/C/D run only when every earlier route is non-promoted.
- [x] 1.2 (V5-P1) Freeze shared v5 runtime contract: canonical plan schema,
  PCG64 frame generation, identity overlap proof, development seed binding,
  conditional confirmation, selection ranking, eight artifacts, provenance,
  forbidden-diagnostic scans, strict read-only replay; caps workers 1,
  checks <= 56, row weight <= 8, stage iterations <= 12, decoder stages <= 3,
  verification attempts <= 3, dense messages <= 24 MiB; wall time
  monitoring-only.
- [x] 1.3 (V5-P2) Freeze Route A: NBLDPC5A (rows 0..47 exact v3; block 6
  mask6=(0,1,2,3,4,5); disjoint-shift-difference search for s6*, salt
  enumeration for rank-56 + pair-proxy; canonical bytes/manifest/verifier);
  policies `nbldpc_v5a_ir56` / `nbldpc_v5a_ir48`; three-level warm state
  machine; leakage/accounting with protocol epsilon union bound 2^-63 / 2^-62;
  roots 202607720000-202607750000; run ID
  `20260731_v5a_nbldpc_multistage_synthetic`.
- [x] 1.4 (V5-P3) Freeze Route B: 7-block search-domain templates,
  lexicographic shift enumeration with disjoint-shift-difference, salt
  enumeration for per-prefix rank/pair-proxy, w2/w3 low-weight syndrome
  collision proxy over K=8 acceptable candidates with construction_seed
  tie-break; canonical NBLDPC5B; roots 202607760000-202607790000; run ID
  `20260731_v5b_nbldpc_mother_synthetic`.
- [x] 1.5 (V5-P4) Freeze Route C: codebook identity rule (NBLDPC5B if B ran
  and is non-promoted, else NBLDPC5A; fixed at Route C plan freeze); policies
  `nbldpc_v5c_sched` (lambda 0.5 / 0.75 / 0.90 per 4-iteration quartile) and
  `nbldpc_v5c_ems` (nm=64, alpha=0.8); equivalence-test contract (constant
  lambda .75 matches v4 warm on identical inputs); roots
  202607800000-202607830000; run ID `20260731_v5c_nbldpc_decoder_synthetic`.
- [x] 1.6 (V5-P5) Freeze Route D: list stage (L=2 least-certain variables,
  top-8 belief symbols each, 64 candidates, one round, syndrome-consistency
  filter) then one ADMM run (rho=1.0, <= 50 iterations, deterministic init);
  no additional syndrome disclosure; verification-attempt cap respected; roots
  202607840000-202607870000; run ID `20260731_v5d_nbldpc_post_synthetic`.
- [x] 1.7 (V5-P6) Freeze readiness 63/64, promotion 128/128 both strata,
  non-promotion immutability, no-rerun/no-tuning, N4/sidecar/`.ttbin`/
  real-data/comparison locks, probe seed 202607719999 (Route A only), and
  documentation gates after each executed route.

## Phase 2: Shared runtime and Route A implementation

- [x] 2.1 (V5-I0) Implement shared parameterized runtime
  `formal_ir/nonbinary_v5_runtime.py`: plan-only, execute, invalid-run
  retention, selection ranking, conditional confirmation materialization,
  eight artifacts, provenance, forbidden-diagnostic scans, strict read-only
  replay; per-route configuration schema (run ID, method ID, roots, caps,
  codebook builder, policy list, prefix ladder, verification cap, epsilon).
- [x] 2.2 (V5-I1) Implement `nonbinary_v5a_codebook.py`: exact v3 rows 0..47,
  frozen s6*/salt* search (run once at acceptance time, results recorded in
  manifest, never re-searched), rank/cycle/degree/pair-proxy checker,
  canonical bytes/manifest/verifier; prove exact v3 row reuse.
- [x] 2.3 (V5-I2) Implement `nonbinary_v5a_multistage.py` core: three-level
  warm state machine (p=.20 32→40; p=.30 40→48→56), ir56/ir48 policies, warm
  retention across every extension, at most 12 iterations/stage, exact
  syndrome/tag/decision accounting, diagnostic exclusion, fail-closed
  binding; control never extends.
- [x] 2.4 (V5-I3) Implement Route A qualification wrapper
  `cli/run_formal_nonbinary_v5a_qualification.py` binding plan/execute/
  replay/artifacts to run ID and roots.
- [x] 2.5 (V5-I4) Prove Route A roots/frames/arrays/atomic keys/seeds fresh
  against all discoverable formal evidence; confirmation material absent
  until readiness.
- [x] 2.6 (V5-I5) Implement deep byte/semantic/manifest/transcript/
  accounting/gate tamper rejection with explicit fake runners for Route A
  tests.

## Phase 3: Route A acceptance before data

- [x] 3.1 (V5-T0) Compile/import, exact v3-row reuse proof, tiny-math
  two-level vs three-level state transitions, rank-56 / zero-four-cycle /
  pair-proxy, accounting pass.
- [x] 3.2 (V5-T1) Focused unit/tamper suite for v5a: warm retention across
  two extensions, ir48 never extends, both allowed triggers, all forbidden
  triggers and caps.
- [x] 3.3 (V5-T2) Complete fake qualification and strict fake replay pass
  under a fresh writable UUID root with pytest cache disabled.
- [x] 3.4 (V5-T3) v1-v4 regression, independent review, scoped task manifest,
  untracked hashes, frozen-directory checks, no official v5a output pass.
- [x] 3.5 (V5-A0) Fixed-seed probe 202607719999 (p=.30, production first
  stage plus forced warm extensions through prefix 56) records operational
  timing and deterministic work/memory facts; creates no qualification
  artifact.

## Phase 4: Route A conditional execution

- [x] 4.1 (V5-A1) Create the one no-overwrite Route A plan (development seeds
  bound; confirmation unmaterialized), review it without decoding, execute at
  most once, strict read-only replay at most once.
- [x] 4.2 (V5-A2) Readiness gate: if either stratum < 63/64, retain immutable
  development evidence and stop Route A without confirmation; if >= 63/64 in
  both strata, atomically materialize, freshness-check and freeze
  confirmation material before the first confirmation decode.
- [x] 4.3 (V5-A3) Promotion gate: 128/128 in both strata -> record
  `promoted=true`, stop the change (routes B/C/D not run); otherwise
  `promoted=false`, retain the immutable package, proceed to Route B.
- [x] 4.4 (V5-A4) Update handoff / current task / decision log / project
  memory with verified Route A facts.

## Phase 5: Route B (conditional on Route A non-promotion)

- [x] 5.1 (V5-B1) Implement `nonbinary_v5b_mother.py` (frozen search domain,
  w2/w3 proxy, K=8, construction_seed tie-break, canonical bytes/verifier),
  Route B qualification wrapper/CLI, reusing the shared runtime.
- [x] 5.2 (V5-B2) Route B acceptance: per-prefix structural checks
  (rank/cycles/degrees/pair-proxy/proxy scores), focused unit/tamper suite,
  complete fake qualification + strict fake replay, regression + independent
  review; no official v5b output before plan creation.
- [x] 5.3 (V5-B3) Create the one no-overwrite Route B plan, review without
  decoding, execute once, strict read-only replay once.
- [x] 5.4 (V5-B4) Readiness and promotion gates exactly as tasks 4.2 / 4.3;
  on promotion stop the change; on non-promotion retain the immutable package
  and proceed to Route C.
- [x] 5.5 (V5-B5) Update handoff / current task / decision log / project
  memory with verified Route B facts.

## Phase 6: Route C (conditional on Route A and B non-promotion)

- [x] 6.1 (V5-C1) Fix Route C codebook identity at plan freeze (NBLDPC5B if B
  is non-promoted, else NBLDPC5A); implement `nonbinary_v5c_decoders.py`
  (sched + EMS), wrapper/CLI, and the pure in-memory equivalence test
  (constant lambda .75 matches v4 warm on identical inputs).
- [x] 6.2 (V5-C2) Route C acceptance: structural checks, focused unit/tamper
  suite (damping-schedule bounds, EMS truncation/sorting determinism),
  complete fake qualification + strict fake replay, regression + independent
  review; no official v5c output before plan creation.
- [x] 6.3 (V5-C3) Create the one no-overwrite Route C plan, review without
  decoding, execute once, strict read-only replay once.
  (2026-08-01: plan created + read-only review passed; executed once via
  wrapper (run_status=completed, readiness true); strict read-only replay
  completed with `{'verified': True, 'run_status': 'completed',
  'promoted': False}` and no worktree changes — evidence
  `v5c_acceptance_c3_c4.json` + Verification Notes below.)
- [x] 6.4 (V5-C4) Readiness and promotion gates exactly as tasks 4.2 / 4.3;
  on promotion stop the change; on non-promotion retain the immutable package
  and proceed to Route D.
  (2026-08-01: readiness true both strata; confirmation materialized and
  executed; promotion gates p=.20 128/128, p=.30 127/128 -> promoted=false;
  immutable package retained; proceed to Route D.)
- [x] 6.5 (V5-C5) Update handoff / current task / decision log / project
  memory with verified Route C facts.

## Phase 7: Route D (conditional on Routes A, B, C non-promotion)

- [ ] 7.1 (V5-D1) Implement `nonbinary_v5d_post.py` (L=2 list stage with top-8
  belief symbols and syndrome-consistency filter; then one ADMM run rho=1.0,
  <= 50 iterations), wrapper/CLI.
- [ ] 7.2 (V5-D2) Route D acceptance: structural checks, focused unit/tamper
  suite (list bound, ADMM bound, no extra disclosure, verification-attempt
  cap), complete fake qualification + strict fake replay, regression +
  independent review; no official v5d output before plan creation.
- [ ] 7.3 (V5-D3) Create the one no-overwrite Route D plan, review without
  decoding, execute once, strict read-only replay once.
- [ ] 7.4 (V5-D4) Readiness and promotion gates exactly as tasks 4.2 / 4.3;
  promotion or four immutable non-promoted packages terminates the change.
- [ ] 7.5 (V5-D5) Update handoff / current task / decision log / project
  memory with verified Route D facts.

## Phase 8: Durable state

- [ ] 8.1 (V5-M0) Final handoff update: frozen outcomes per executed route,
  promotion/stop status, explicit next boundary.
- [ ] 8.2 (V5-M1) Perform mandatory memory triage.

## Verification Notes
- Route A executed once (512 outcomes, run_status=completed). Readiness true (both strata >=63/64). Promotion p=.20 128/128, p=.30 127/128 -> promoted=false. Strict replay attempted once, blocked by external git HEAD drift (71bda20d -> 3a5d96a, unrelated commits); source hashes match. Decision logged 2026-08-01.
- Route B implemented: NBLDPC5B mother (7-block frozen templates, disjoint-shift-difference, salt=0, w2=w3=0, K=8 candidates all zero-collision), v5b multistage core (identical 3-level warm state machine, policies nbldpc_v5b_ir56/ir48), lane + CLI. T0/T1/T2: 31/31 pass. T3: v5a 31/31 pass; v4 16/16 pass with v4 official package temporarily suspended (v4 test self-conflict with its own package, pre-existing, unrelated to v5b); v1-v3 29 failures pre-existing per 3.4. Mechanical review: 7 file hashes recorded, frozen dirs clean, no official v5b output.
- Route B: plan created once (128 frames, 576 seeds, identity_overlap empty, confirmation unmaterialized, HEAD 3a5d96a). Executed once: 512 outcomes, run_status=completed, readiness=true. Promotion gates: p=.20 128/128, p=.30 127/128 -> promoted=false (same p=.30 tail pattern as v5a). Strict replay attempted once, blocked by external git HEAD drift (3a5d96a -> 4dd6b7e, unrelated ldpc_v5_development commit); v5b source hashes unchanged. Immutable package retained; proceed to Route C.
- Decision log entry 2026-08-01 Route B added; CURRENT_TASK.md updated with v5a/v5b outcomes; Route C next with NBLDPC5B identity fixed.
- Route C C1 implemented 2026-08-01: `nonbinary_v5c_decoders.py` (NBLDPC5B
  identity, policies `nbldpc_v5c_sched` damped FFT-QSPA lambda .5/.75/.9 per
  4-iteration quartile, `nbldpc_v5c_ems` LLR min-sum nm=64 alpha=0.8 with
  deterministic top-nm truncation and full-domain convolution accumulator),
  lane `nonbinary_v5c_ir_qualification.py` (run ID
  `20260731_v5c_nbldpc_decoder_synthetic`, roots 202607800000-202607830000,
  source provenance includes the exec wrapper per the speed-up handoff),
  CLI `run_formal_nonbinary_v5c_qualification.py` (execute/resume via
  `parallel_run`).
  Equivalence test (pure in-memory, in `test_nonbinary_v5c_decoders.py`):
  v5c_sched with constant lambda .75 is byte-identical (0/208 messages
  differ) to v4 warm on identical inputs after one update round.
  Core suite 10/10 passed; qualification lane suite 19/19 passed (fake
  qualification, tamper matrix, strict replay, invalid boundaries,
  production-API guards); v5b regression 12/12 passed; wrapper probe on the
  v5c lane: parallel_run workers=2 -> non_promoted_development (256 rows,
  verify True) and crash+resume -> non_promoted_development (256 rows,
  verify True).  No official v5c output created (C3 plan not yet made).
- Route C C3 plan created + read-only reviewed 2026-08-01:
  - One no-overwrite plan at
    `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5c_nbldpc_decoder_synthetic/`
    (directory did not exist before; contains only `pre_run_plan.json`).
  - Content: canonical_schema `NBLDPCQ5C`, run_id `20260731_v5c_nbldpc_decoder_synthetic`,
    128 frames (64 per stratum), 640 development Toeplitz seeds
    (2 policies x (64 x 2 slots at p=.20 + 64 x 3 slots at p=.30)),
    policies `nbldpc_v5c_sched` + `nbldpc_v5c_ems`, git_commit `9340625`.
  - NBLDPC5B identity: plan provenance codebook_sha256 equals live v5b
    canonical `d1ee0a795261aabb...` (match).
  - Wrapper source hash: plan source_sha256 for
    `nonbinary_v5_exec_wrapper.py` = `478644ff...` matches disk; all 11
    source_files hashes match disk (NONE mismatch).
  - Freshness: identity_overlap empty (roots/frame_ids/array_sha256/
    atomic_keys); seed_ids disjoint from all prior evidence
    (`_prior_seed_ids(exclude=v5c_dir)` verified, own 640 seeds excluded).
  - Execution NOT started; strict replay NOT run.  Next boundary: explicit
    go-ahead for one wrapper parallel_run + one strict replay.
- Route C: plan created once (128 frames, 64 per stratum, 640 development
  Toeplitz seeds, identity_overlap empty, confirmation unmaterialized,
  NBLDPC5B codebook identity; recorded git_commit per plan file). Executed
  once: run_status=completed, readiness=true. Promotion gates: p=.20 128/128,
  p=.30 127/128 -> promoted=false (same p=.30 tail pattern as v5a/v5b).
  Strict read-only replay completed once:
  {'verified': True, 'run_status': 'completed', 'promoted': False};
  git status --porcelain unchanged. Immutable package retained; proceed to
  Route D (`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-
  202607870000).
