# Tasks: implement-formal-cascade-and-ldpc

All boxes remain open until implementation evidence exists. If implementation
needs to change a frozen decision, stop and return to the OpenSpec planner.

## Phase 1: Additive Contract and Preflight

- [x] Read the proposal/design/spec, project memory, lite contracts, source
  frame schema, and current output contracts before editing.
- [x] Add `comparison_bench/requirements-formal-ir.txt` pinning
  `ldpc==2.4.1`; implement
  fail-closed version/API preflight and freeze all decoder parameters in R4.
  The reopened task MUST remove the rejected `random_serial_schedule` kwarg
  and add the exact no-decode 1-by-64 constructor probe.
  - Acceptance: a fake/docstring-advertised keyword that the constructor
    rejects fails closed; the revised exact kwargs probe succeeds on actual
    pinned 2.4.1 without calling `decode`; serial schedule, explicit `[0..63]`
    order, and one OMP thread are asserted.
- [x] Define additive artifact schemas for the exact six top-level artifacts,
  required frame fields, status precedence, attempted/denominator semantics,
  transcript events, and disclosure fields. Preserve legacy dataclasses,
  columns, method names, and outputs.
  - Acceptance: schema/compatibility tests and an artifact example pass;
    dependency mismatch yields `preflight_unavailable`; stop if a legacy public
    interface must change.

## Phase 2: Locked Provenance, Toeplitz, and Transcript

- [x] Implement formal lock ingestion that preserves unique
  `dataset_id:frame_id:pair_idx`, ordered source keys, source hash, mapping, and
  exactly 64 symbols; reject reshape/re-numbering that loses provenance.
- [x] Implement the exact R2 Toeplitz construction and a committed fixed test
  vector; materialize independent per-frame system-CSPRNG seeds in the lock,
  with exact seed hex/length/SHA256 ID, and prohibit runtime generation.
- [x] Implement canonical event JSONL and transcript SHA256, payload allowlist,
  event disclosure summation, verification invocation accounting, epsilon, and
  run union bound.
  - Acceptance: `python -m pytest comparison_bench/tests -k formal_verification`
    proves the matrix index convention, fixed tag, unequal rejection, seed
    independence/read-only use, JSONL bytes/hash, payload secrecy, zero
    verification accounting before invocation, CRC non-authority, and absence
    of explicit corrected raw bit indices from every public artifact.

## Phase 3: `cascade_formal_v1`

- [x] Implement the R3 state machine: one-bit initial parities, one-bit
  left-half bisection messages, cached parity, Bob-local correction, FIFO
  all-completed-pass membership look-back, pending-only deduplication, block
  re-entry, queue drain after every primary correction, ordered parented
  events, the exact four-pass `[16,32,64,128]` qualification schedule and
  domain-derived permutations, and all resource caps.
  - Acceptance: noiseless, single-error, and hand-built multi-pass look-back
    vectors pass; tests prove re-entry, zero-bit cached recheck, event/direction
    accounting, source-event/block/path-only public `CORRECTION` records,
    in-memory corrected-position assertions, secret/index-free transcript,
    deterministic hash, all requested records, and
    `aborted_resource_limit` at each cap.

## Phase 4: `ldpc_formal_v1`

- [x] Implement the exact four-rate `gf2_sparse_accumulator_v1` generator,
  deterministic PCG64 domain construction, GF(2) rank verifier, canonical
  HGF2V1 bytes/hash, exact filename convention, and pre-run codebook manifest.
- [x] Implement calibration counts/hash and R4 rate selector using only
  sacrificed tuning frames; freeze dataset/plane `p_hat` and rate IDs before
  confirmation and reject any confirmation truth access/update.
- [x] Implement Alice syndrome/Bob delta across MSB-first planes using only the
  pinned `ldpc==2.4.1` serial deterministic BpOsd configuration; require
  syndrome consistency plus Toeplitz and prohibit fallback-to-ok.
  - Acceptance: codebook bytes/hash/rank golden tests, all four rate artifacts,
    selector boundary tests, calibration/confirmation isolation test, decoder
    parameter/version assertions, no-decode constructor-probe tests, rejection
    of docstring-only kwargs, explicit-order assertions, hand-built syndrome
    vectors, unavailable/error/inconsistent status tests, and retained-failure
    denominators pass.
    Stop if rank, pinned dependency/API, or deterministic serial order cannot
    satisfy the spec.

## Phase 5: Bounded Synthetic Qualification

- [x] Add an immutable notice to synthetic v2 marking it non-promotable for
  unused declared Alice/frame-order seeds, undeclared Alice seeds, and any
  transcript contract breach; point only to a fresh additive v3. Preserve v1
  partial and all v2 bytes.
- [x] Freeze fresh v3 `pre_run_plan.json`: one sequential Alice PCG64 generator
  and four exact batches, four exact noise generators, locked gray mapping,
  canonical calibration exclusion, exact 64 qualification identities,
  frame-order-only PCG64 permutation/list/hash, 64 qualification-only CSPRNG
  verification seeds shared by both methods, frame/method/runtime caps, and
  exact deterministic preflight command.
- [x] Implement preflight recording, original-event transcript storage, full
  source/version/git/config provenance, non-circular artifact hash DAG,
  exception-safe exclusive six-artifact finalizer, and strict read-only v3
  verifier. Do not modify formal method event bytes.
- [x] Run both formal methods in fresh v3 only after plan/reviewer acceptance,
  then verify exact artifact set/hashes, generation/order, seed binding,
  original transcript group hashes, disclosure/union bound, statuses,
  denominators, provenance, and report gates.
  - Promotion gate per method/stratum: deterministic vectors 100%; at least
    31/32 `verified_success`; zero unclassified/internal/provenance/accounting
    failures. Otherwise retain non-promotion evidence without changing plan.
  - Acceptance: runner preflight records command/exit/passed-count/output hash
    and makes zero frame calls on failure; any injected run-body exception
    leaves immutable plan/partial bytes and six non-promotion artifacts.
  - Acceptance: verifier rejects any extra/missing artifact, Alice RNG call or
    seed drift, frame-order drift, calibration verification seed, cross-method
    seed mismatch, transcript rewrite/hash substitution, source/version/hash
    mismatch, union-bound mismatch, or incorrectly satisfied promotion gate.

## Phase 6: Fresh Locked Real Qualification

- [x] Add only `invalid_lock_notice.json` to
  `formal_ir_methods/20260725_v1_real_cascade/`, binding the existing plan/lock
  hashes, `2026072521` versus required `2026072522` mismatch, zero method calls,
  absent run artifacts, and v2 successor. Preserve all v1 bytes; never execute
  or reuse v1 seeds.
- [x] Create and independently review only the eligible Cascade additive lock
  at `formal_ir_methods/20260725_v2_real_cascade/`, with matching run ID and
  real base seed `2026072522`: immutable
  `real_data_lock.json` plus binding `pre_run_plan.json`; 60 sacrificed bw100
  and 60 group-disjoint bw120 confirmation frames, `d=1024`, 64 symbols, frame
  SER `[.20,.30)`, every atomic pair row, selection/source/hash provenance,
  zero final-IR-v1 overlap, and 60 confirmation CSPRNG Toeplitz seeds. Rebuild
  the PCG64(2026072541/2026072542) orders before accepting it. Preserve the
  selected identities/hashes but materialize 60 fresh CSPRNG seeds with zero v1
  seed reuse.
- [x] Keep `ldpc_formal_v1` out of real execution: v3 synthetic is
  non-promoted (29/32, 14/32). Do not substitute a lite method. A new LDPC
  improvement change is required before a future fresh real qualification.
- [x] Before any method call, run the three formal unit files plus
  `test_formal_real_qualification.py` using the exact external-basetemp command
  and `FORMAL_IR_TEST_TMP` policy; require manifest command/exit/passed-count/
  exact-output-hash evidence and zero calls on failure.
- [x] After v2 lock acceptance, run `cascade_formal_v1` exactly once within 5
  seconds/frame and 20 minutes,
  preserving every requested record and verifying the seven-artifact real run
  read-only.
  - Promotion gate: exactly 60/60 requested confirmation frames attempted,
    60/60 `verified_success`, and zero unclassified/internal/provenance/
    accounting failures. Otherwise record non-promotion without changing
    configuration.
  - Stop before execution if groups, counts, uniqueness, source hashes,
    disjointness, SER/domain, seeds, or frozen plans do not verify.
  - Verified evidence: real v1 added only invalid notice
    `9f9d72f6c1e39467f08b86a514851b78a8aaf6a8ef2fb1f869b22f60e980d556`;
    original plan `3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`
    and lock `aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
    remained unchanged with zero calls.
  - Verified evidence: real v2 strict verifier accepted exactly seven
    artifacts: plan
    `ef0c496d4679c8a790fa6715fca010c65bbe80dbcc9fb1a640139750e8f87161`,
    lock `fea6d1e9912415c37f78393ef7d5e5e9bae156531bc9e6bd9a07936c41a09348`,
    outcomes
    `d3ef26555e19fa58d74e40ccc9dc253e27db058a1b79720e77ab265f652c01f0`,
    transcript
    `f95478b529f13871846400395d97b9d8a4f1948ddd30859a16dd7f66074a34c8`,
    codebook manifest
    `e8fbbd2ca195c8aa6d4a2ca8c821c2f8bb0eb73e6830ac85fff4558ef329738c`,
    run manifest
    `42d18066cc13740fd4367430b0319020ec4b943e5c01bf43f4df0759257ce172`,
    and report
    `750aaebf4919aa9a66383e6e4bf2d441efd718324ebca564157e6607d2b21e1b`.
    Preflight passed 29 tests, exit 0, output hash
    `8760383422fb96ce6b8d644333e52064287e394f2827f57459bc110ded0a7a7c`.
    All 60 requested frames were attempted, denominator-included,
    verification-invoked, and `verified_success`; union bound
    `3.2526065174565133e-18`; unclassified/internal/provenance/accounting
    failures zero. Cascade is promoted only for locked
    `d=1024`, 64-symbol, bw120, SER `[.20,.30)` evidence.

## Phase 7: Review, Memory, and Archive

- [x] Reviewer audits frozen boundaries/no overwrite, exact decoder/version
  pin, no Alice confirmation oracle, status precedence, disclosure math,
  transcript payloads/hashes, provenance, caps, and promotion decisions.
- [x] Run `git diff --check`, focused formal tests, safe comparison regression,
  and all read-only lock/artifact verifiers; record exact results.
  - Synthetic-v3 and real-v2 read-only verifiers passed. The safe non-formal
    regression passed 22/22 in 0.66 s; `git diff --check` exited 0 with only
    known ACL/LF warnings; frozen `src/`, `experiments/`, `tools/`, and
    `results/` diffs were empty; independent audit result: PASS.
- [x] Complete memory triage and update decision log, current task, handoff,
  OpenSpec tasks, and limitations from verified evidence only. Project memory
  now records the verified formal synthetic-v3 and real-v2 evidence chain,
  read-only verifier commands, bounded Cascade promotion, LDPC non-promotion,
  and the separate-improvement gate.
- [x] Archive with explicit per-method `promoted` or `non_promoted` result. A
  later Polar fair-comparison change may include only promoted formal methods;
  improvement of a non-promoted method requires a new change and lite
  substitution is forbidden.
  - Final state: `cascade_formal_v1` is promoted by synthetic v3 and the
    bounded real v2 qualification. `ldpc_formal_v1` is synthetically
    `non_promoted` and was not run on real data.
