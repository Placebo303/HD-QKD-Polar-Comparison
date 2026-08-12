# Tasks: Formal Nonbinary LDPC v7 Successor Ladder

## 0. Freeze shared automation

- [x] V7-00 Record HEAD, dirty-worktree scope, predecessor hashes, used roots,
  seed IDs, and absence of official v7 output.
  (2026-08-02: HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; implementation
  note freezes m=170 (168 degree-3 + 2 degree-4 checks), syndrome 1700 bits,
  frozen seed 2026080400, flooding FFT-QSPA primary —
  evidence/v7_r1a_engineering_acceptance.json.)
- [x] V7-01 Implement a shared ladder controller that can advance only from an
  immutable verified report and cannot execute confirmation.
  (2026-08-02: shared ladder controller implemented — dict-based state
  machine, hash-bound advance, no confirmation path, exactly-once, no-rerun,
  crash/resume; frozen gates: canary 0/4 either stratum -> failed_canary;
  ready = >=15/16 + zero forbidden + strict replay + <=8.75 bits/symbol +
  median <=120 s/frame.)
- [x] V7-02 Add state-machine, crash/resume, no-rerun, freshness, fake-runner,
  strict-replay, and layered-tamper tests.
  (2026-08-02: controller tests passed — transitions, crash/resume, no-rerun,
  freshness, fake-runner, strict replay, layered tamper.)

## 1. R1 multiplicative repetition

- [x] V7-10 Implement and oracle-test the deterministic GF(1024) n=256 `(2,3)`
  mother, flooding/layered decoders, and disclosure accounting.
  (2026-08-02: R1A mother (GF(1024) n=256 (2,3) PEG m=170, full rank, no
  parallel edges) + flooding/layered FFT-QSPA (max_iter 100, lambda .75) +
  disclosure accounting implemented and oracle-tested.)
- [x] V7-11 Pass T0-T3 and independently accept R1 engineering.
  (2026-08-02: T0 19 / T1 64 / T2 11 / T3 97 all passed; independent review
  ACCEPTED 2026-08-02 — 7/7 PASS, 0 blocking; 3 non-blocking notes: F1
  direct-equivalence test, F2 evidence_root label, F3 v6_development hash
  provenance.)
- [x] V7-12 Prepare/review/execute/replay R1A canary exactly once.
  (2026-08-02: R1A sacrificed 4+4 canary plan staged, read-only reviewed
  READY-FOR-SINGLE-EXECUTION, executed exactly once + strict-replayed exactly
  once (both exit 0; execute 111.0 s, replay 108.8 s); per-stratum verified
  success 0.20 0/4, 0.30 0/4 (all decode_failed at iterations=100, zero
  forbidden statuses); canary gate FIRES -> failed_canary; R1A frozen; package
  at workspace/nbldpc_v7_r1a_canary_af8ff2e751cf433ba74deb74bbe1deba/canary_plan;
  evidence/v7_r1a_canary_execution_addendum.json; no official root created.
  Minimal canary-only run() authorization edit recorded (v6_51-mirror); plan
  re-created in the same dir to bind the post-edit code (original plan SHA
  3bac7a7e... backed up).)
- [x] V7-13 If eligible, prepare/review/execute/replay R1A 16+16 development;
  stop the ladder if ready.
  (2026-08-02: NOT eligible — canary gate fired (0/4 both strata), so R1A
  16+16 development was not prepared or run, per the frozen ladder.)
- [x] V7-14 Only if R1A canary gate fails, implement/test R1B one-repetition
  prior combination and fresh identity.
  (2026-08-02: R1B engineering implemented and independently reviewed
  ACCEPTED — identity nbldpc_formal_v7_r1b_mr1, exact R1A mother under new
  identity, one multiplicative repetition per variable (deterministic
  SHA256-derived nonzero GF(1024) multipliers), prior-combining decoder
  wrapping R1A flooding/layered core (max_iter 100, lambda .75, workers 1),
  syndrome 1700 bits + 64-bit tag, transcript never exposes raw/corrected
  symbols; T0 15 / T1 76 / T2 17 / T3 119 passed;
  evidence/v7_r1b_engineering_acceptance.json; canary (4+4) and development
  (16+16) configs staged in harness but no plan created and no execution
  run.)
- [x] V7-15 Prepare/review/execute/replay R1B canary and, if eligible, 16+16
  development exactly once each; stop if ready.
  (2026-08-02: R1B sacrificed 4+4 canary staged, read-only reviewed
  READY-FOR-SINGLE-EXECUTION, executed exactly once + strict-replayed exactly
  once (both exit 0; execute 59.3 s, replay 59.6 s); per-stratum verified
  success p=.20 3/4, p=.30 0/4 (5 decode_failed, zero forbidden statuses);
  canary gate FIRES on p=.30 -> failed_canary; R1B 16+16 development NOT
  eligible; R1B frozen; package at
  workspace/nbldpc_v7_r1b_canary_a209a853f5e34de69bf930deb60d5673/canary_plan;
  evidence/v7_r1b_canary_execution_addendum.json; no official root.)

## 2. R2 QSC density-evolution ensemble

- [x] V7-20 Only if R1 is non-ready, implement bounded q-ary density evolution,
  published/small-field oracle checks, distribution search, and PEG builder.
  (2026-08-02: R2 engineering implemented, DE validated against published
  vectors, check counts 321/458, T0 32 / T1 100 / T2 24 / T3 142
  (evidence/v7_r2_engineering_acceptance.json).)
- [x] V7-21 Pass T0-T3 and independently accept R2 engineering.
  (2026-08-02: independent review ACCEPTED — 8/8 PASS, no blocking findings.)
- [x] V7-22 Prepare/review/execute/replay R2 canary and, if eligible, 16+16
  development exactly once each; stop if ready.
  (2026-08-02: R2 sacrificed 4+4 canary staged, reviewed
  READY-FOR-SINGLE-EXECUTION, executed exactly once + strict-replayed exactly
  once (both exit 0; execute 1311.2 s, replay 1308.5 s); per-stratum verified
  success p=.20 0/4, p=.30 0/4 (8 decode_failed at max_iter=100, zero
  forbidden statuses); canary gate FIRES -> failed_canary; R2 16+16
  development NOT eligible; R2 frozen; package at
  workspace/nbldpc_v7_r2_canary_d6c752a0772043768a1ca88a1ca63ed3/canary_plan;
  evidence/v7_r2_canary_execution_addendum.json; no official root.)

## 3. R3 GF(32)xGF(32) multilevel

- [x] V7-30 Only if R2 is non-ready/blocked, implement reversible mapping,
  conditional layer model, two GF(32) codes, EMS, accounting, and replay.
  (2026-08-04: COMPLETE — T0 19 / T1 105 / T2 33 / T3 179 all passed
  (evidence/v7_r3_engineering_acceptance.json; schema v7_r3_engineering_v1;
  identity nbldpc_formal_v7_r3_gf32x2, manifest_id
  b052a92748119b57d426fda4583d697f6577e6761e2b52332fee9f6e13c57582;
  check-count freeze m0=m1=ceil(1.15*H_32(p)/5*1024) = 404/558; engineering
  gate intact — R3 production execution still blocked until V7-32 main-thread
  review; CANARY/DEVELOPMENT plans were NOT created and no canary/development
  was executed; official root untouched; 13 reused-source hashes unchanged;
  no files outside the allowed list were written).
- [x] V7-31 Pass T0-T3 and independently accept R3 engineering.
  (2026-08-04: independent review ACCEPTED — 10/10 PASS, 0 blocking
  (reviewer-go); engineering gate intact; canary staging follows (V7-32 first
  half).)
- [x] V7-32 Prepare/review/execute/replay R3 canary and, if eligible, 16+16
  development exactly once each; stop if ready.
  (2026-08-04: R3 sacrificed 4+4 canary staged (first half:
  evidence/v7_r3_canary_plan_evidence.json, plan sha256
  1308c7074d2d7f51fc1a2a50d4479600f6086fc82fa828ebc17ed03fa353dedb), reviewed
  READY-FOR-SINGLE-EXECUTION; second half: minimal canary-only authorization
  edit applied (run() + CLI + two tests; post-edit source hashes
  dd8ebe41.../68a17e92.../ad603eab...; focused auth tests 78 passed in
  295.3 s), first-half plan backed up
  (canary_plan_first_half_backup/pre_run_plan.json sha256 1308c707...dedb),
  plan re-created in the same directory (in-memory compact
  446ab11b...503af, file 43379354...fca2, frames/roots/caps identical, 8
  fresh 10303-bit seed records disjoint from first-half and from all 10744
  prior seed_ids), executed exactly once + strict-replayed exactly once
  (both exit 0; execute 668.8 s, replay 663.4 s; git porcelain unchanged by
  replay); per-stratum verified success p=.20 0/4, p=.30 0/4 (8
  decode_failed at max_iter=100, zero forbidden statuses; 24 transcript
  events, 3/frame, failed layer-0, verification never invoked); canary gate
  FIRES -> failed_canary; R3 frozen; 16+16 development eligibility is a
  separate main-thread decision (not claimed here); package at
  workspace/nbldpc_v7_r3_canary_d006ec637ecb4b1e9463a7f4462eebf3/canary_plan;
  evidence/v7_r3_canary_execution_addendum.json; no official root.)

## 4. Closeout

- [x] V7-40 Freeze a ladder report identifying the first ready route or proving
  that all routes are non-ready/blocked; retain every failed artifact.
  (2026-08-04: evidence/v7_ladder_report.md frozen at HEAD
  a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344 — first ready route NONE,
  ladder_exhausted TRUE; all four routes R1A/R1B/R2/R3 `failed_canary`,
  every failed artifact retained, no official v7 output root, no
  rerun/tuning/confirmation/real-data; no fourth route invented; successor
  requires a new OpenSpec change with fresh development/confirmation data.)
- [x] V7-41 Perform independent acceptance and project-memory triage.
  (2026-08-04: independent acceptance of the ladder closeout PASS —
  reviewer-go, 7/7 checklist PASS, 0 blocking, 3 non-blocking notes accepted;
  every report number spot-checked against the 12 evidence JSONs; memory
  triage complete — AGENT_PROJECT_MEMORY.md §35 updated to the exhausted
  ladder state + new §36 durable pattern/stop rule.)
- [x] V7-42 If ready, return for a new qualification change; if none is ready,
  stop without inventing a fourth route.
  (2026-08-04: NOT ready — all four routes `failed_canary`, first
  development-ready route NONE, `ladder_exhausted` TRUE; ladder stopped; no
  fourth route invented; no qualification/confirmation/real data/N4; no
  official v7 output root; successor requires a new OpenSpec change with
  fresh development and confirmation data and new roots.)

