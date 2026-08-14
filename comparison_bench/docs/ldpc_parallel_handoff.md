# Binary and Nonbinary LDPC Parallel Handoff

Last verified: 2026-07-26

## Purpose

This is the working handoff for two independent LDPC research lanes. The goal
is not to select a winner early. The goal is to make both methods formal enough
that a later comparison against formal Cascade and Polar is fair,
frame-identical, reproducible, and security-accountable.

Implementation is authorized only through a frozen OpenSpec work package.
Nothing in this document by itself authorizes experiments, real-data runs,
dependency installation, or qualification claims.

## Current State

| Lane | Current method | Evidence status | Immediate direction |
|---|---|---|---|
| Binary LDPC | executable `ldpc_formal_v3`, q=1024/n=256 | Phase 1-5 engineering accepted; no v3 confirmation or qualification | Freeze Phase 6 calibration/confirmation runner, verifier, gate and stop rules |
| Nonbinary LDPC | `nbldpc_formal_v1` N0-N3 plus frozen `qldpc_reference` | N3 confirmation is non-promoted; official strict verification is unverifiable after worktree drift | Retain package; do not retune, rerun, or start N4 |
| Existing reference | `qldpc_reference` | Retained for diagnostics and architectural comparison | Keep frozen as reference; never relabel as formal nonbinary LDPC |

`nbldpc_formal_v2` has now also stopped: its selected tempered+damped QC48
policy achieved 0/24 and 5/24 on sacrificed development, below the 22/24
readiness floor. Its eight-artifact package passed strict replay, but
confirmation was never generated or executed. This is development
non-readiness, not confirmation FER or real-data evidence; N4 and `.ttbin`
work remain forbidden.

### Binary evidence that must remain frozen

- The verified v2 synthetic confirmation achieved 28/32 at p=.01 and 29/32 at
  p=.02, below the 31/32-per-stratum gate.
- Seven outcomes were `verify_failed`; verification was invoked for all 64
  outcomes; internal, provenance, accounting, and unclassified failures were
  zero.
- `rate_margin=2` with `OSD_0/0` was selected on development data. Higher OSD
  variants did not improve the development counts.
- The conclusion is `non_promoted`. No real LDPC lock/run or final comparison
  is authorized. The confirmation set must not be reused for tuning.

### Nonbinary limitations that must not be hidden

- The old `qldpc_reference` matrices remain randomly constructed reference
  matrices. The new N1 family is deterministic and hashable, but its structural
  rank evidence is not decoder, distance, FER, or qualification evidence.
- The formal N2 decoder is a bounded probability-domain FFT-QSPA feasibility
  implementation; it is not evidence of production-scale q=1024 performance.
- The old reference fallback still stops at q=256. The independent N0 formal
  backend supports q=1024 and fails closed; it must not be silently replaced
  by the old fallback or another field representation.
- The frozen N3 confirmation achieved only 18/32 at p=.20 and 5/32 at p=.30,
  below both 31/32 gates. It is `non_promoted`.
- The official strict verifier failed because its live whole-worktree status
  hash drifted after execution. Diagnostic artifact/DAG reconstruction is not
  an official strict-verifier pass; retain the package as
  strict-verification-failed/unverifiable.

## Shared Rules for Both Lanes

1. Keep the original Polar baseline and all existing outputs unchanged.
2. Give every formal lane its own method identity and additive output roots.
3. Keep development and confirmation data disjoint. Confirmation is evidence,
   not an optimization oracle.
4. Freeze codebooks, configuration, field/backend versions, and verification
   seeds before confirmation.
5. Count all key-dependent disclosure. A q-ary syndrome with `r` symbols over
   GF(q) discloses `r*log2(q)` bits before verification-tag disclosure; retain
   the method-specific decomposition.
6. Require formal Toeplitz verification after method consistency and retain
   every attempted failure.
7. Do not use “qLDPC” to mean nonbinary classical LDPC in formal claims; use
   “nonbinary LDPC” or the explicit method identity.
8. Promotion in one lane provides no evidence for the other lane.

## Lane B: Binary LDPC

Suggested future OpenSpec change: `binary-ldpc-long-frame-and-ir-v3`.

Status: the change is active. Phases 1-5 are accepted through the executable
formal method. The Phase 3C development package remains immutable. No v3
confirmation runner/package, qualification, promotion, or real-data work has
been authorized.

### B0 — Freeze the new claim domain

- Treat n=64 as historical diagnostic evidence, not the main improvement
  target.
- Select a bounded frame-length ladder such as n=256, 512, and 1024 using
  development-only cost and feasibility evidence.
- Predeclare fresh synthetic generation, development/confirmation splits,
  runtime caps, and promotion gates before execution.

### B1 — Build production-oriented binary code families

- Evaluate deterministic QC-LDPC, PEG, or protograph-derived nested families.
- Optimize for verified FER as the primary development metric; rank, girth,
  ACE, distance-spectrum, and trapping/absorbing-set probes are screening
  diagnostics only.
- Store canonical matrix bytes, rank, construction parameters, and SHA256 in
  an immutable codebook manifest.

#### B1 Phase 1 accepted evidence (2026-07-26)

- Added candidate-only `codebook_long_v3.py`; it does not modify or replace
  `ldpc_formal_v2`.
- Frozen domain is n=256/512/1024, ten planes, four deterministic candidates,
  and exact 1/2, 5/8, 3/4, 7/8 row-prefix redundancy.
- HGF2V3 canonical bytes and a complete 120-candidate in-memory manifest are
  reconstruction-verified and tamper-evident.
- Every tested prefix has actual full row rank, no zero/duplicate columns,
  row weights 2..3 and column weights 1..5. Exact 4-cycle counts and the
  `column_pair_extrinsic_degree_v1` values remain structural proxies only.
- Main-thread verification: focused 4 passed in 10.88 s; v2 regression
  7 passed/1 skipped; `py_compile` and diff checks passed; frozen directories
  were unchanged.
- This is codebook-foundation evidence only. No FER was measured, no candidate
  was selected, no decoder was wired, and no promotion claim follows.

### B2 — Improve decoding information and rate adaptation

- Derive per-bit-plane channel likelihoods instead of sharing a single scalar
  error model across all planes.
- Evaluate multistage decoding where earlier corrected planes can inform later
  likelihoods without reading confirmation truth.
- Generalize the existing nested syndrome schedule to longer blocks. Every
  incremental syndrome bit and verification tag remains disclosed leakage.
- Keep the pinned backend initially; replace it only if bounded evidence shows
  that the required algorithm is unavailable or inadequate.

#### B2 Phase 2 accepted evidence (2026-07-26)

- Added `long_v3_development.py` as an in-memory evaluator only.
- Sacrificed p=.01/.02 development frames use exact domain-separated PCG64
  seeds, canonical provenance hashes, 16 frames per stratum, and can never
  become confirmation evidence.
- The evaluator freezes `ldpc==2.4.1`, minimum-sum BP, OSD-0, explicit serial
  schedule, and four nested syndrome prefixes. Incremental leakage is the
  terminal prefix size, not the sum of all prefixes.
- Candidate selection requires four candidates and identical development
  frames, then ranks by worst-stratum successes, total successes, disclosure,
  and candidate ID. Runtime and structural proxies cannot affect selection.
- Main-thread verification: focused 5 passed in 0.53 s; Phase1/v2 regression
  11 passed/1 skipped; compilation and diff checks passed.
- Tests use injected deterministic decoders. No full pinned-backend sweep,
  candidate selection evidence, confirmation, or promotion has occurred.

#### B2 Phase 3A pinned-backend pilot (2026-07-26)

- Exactly one in-memory pilot ran with n=256, plane 0, candidate 0, p=.01,
  16 sacrificed frames, and pinned `ldpc==2.4.1`.
- Exit was 0 with empty stderr. Process elapsed was 0.3227008000249043 s;
  external wall was 1.0 s.
- All 16 frames were exact successes: p050=15 and p0625=1, with 2080 total
  syndrome bits.
- The pilot wrote no artifact and selected no candidate. It proves only that
  this one backend/domain slice is executable within the cap. It does not
  establish comparative FER, other lengths/planes, qualification, or
  promotion.
- Next freeze an additive, verifier-bound full sacrificed-development sweep
  before executing any 3-length x 10-plane x 4-candidate grid.

#### B2 Phase 3B runner/verifier accepted (2026-07-26)

- Added a two-step, no-overwrite runner and strict read-only verifier for the
  frozen 3840-row development grid.
- A completed or exception-finalized run has exactly six canonical artifacts;
  plan, candidate manifest, outcomes, selections, run manifest, and report are
  bound by explicit self-hashes and a file-byte DAG.
- Test-only execution is isolated to n=256/plane0 with injected decoders.
  Production CLI paths reject test plans; tests never invoke production
  prepare/execute.
- Failure tests retain partial ordered outcomes, omit incomplete selections,
  finalize six artifacts, and remain verifiable without being described as
  complete.
- Main-thread evidence: Phase3B 3/3, all long-v3 12/12, v2 regression
  7 passed/1 skipped, compilation/diff checks passed.
- The production plan and 3840-row sweep have not been created or executed.
  A fresh output path and exact plan require separate main-thread review.

#### B2 Phase 3C full sacrificed-development result (2026-07-26)

- Immutable root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.
- Prepare created one reviewed plan. Execute ran once, exit 0 in 28.9 s, and
  produced exactly six artifacts with 3840 outcomes and 30 selections.
- Strict read-only verifier ran once, exit 0 in 11.2 s, reconstructed all data
  provenance and selections, and reported
  `artifact_integrity_and_selection_reconstruction_only`; it did not rerun
  decoding.
- All 3840 candidate outcomes were development exact successes.
- Selected-candidate per-plane results were 160/160 exact successes in every
  n/p stratum. Mean syndrome bits per plane were:
  n256 p001=129.0, p002=134.6; n512 p001=260.4, p002=280.4;
  n1024 p001=541.6, p002=635.2.
- These leakage values use development-only Alice-truth exact equality to stop
  each plane. Bob cannot use that oracle in a formal protocol. They cannot be
  reported as deployable leakage or qualification evidence.
- Next combine ten bit planes into frame-level global rounds. One locked
  frame-wide Toeplitz tag should drive stopping; the slowest plane determines
  the global prefix and all syndrome/tag leakage must be counted.

#### B2 Phase 4 frame-level development (2026-07-26)

- Accepted pure aggregator combines the selected ten planes into 96 q=1024
  development frames and models one 64-bit frame-wide tag checked across at
  most four global nested-syndrome rounds.
- All three lengths retained 16/16 frame success in each p stratum.
- Frame-wide mean key-disclosure fractions:
  - n256: p001 0.5640625, p002 0.68125;
  - n512: p001 0.590625, p002 0.7546875;
  - n1024: p001 0.6625, p002 0.8421875.
- Frozen length tuple selected n=256:
  `[-16,-32,0.68125,0.62265625,256]`.
- Aggregation hash:
  `029e33c42f254e40725a370065d30196216501085d5def5f0f0c935aca6c933c`.
- This remains `development_oracle_equivalent_terminal_not_tag_execution`.
  Actual formal Toeplitz generation/checking, transcript events, failure
  statuses, and fresh confirmation are not implemented or authorized.

#### B2 Phase 5 executable formal method (2026-07-26)

- Added independent `ldpc_formal_v3` for exactly q=1024, n=256, ten
  MSB-first Gray planes and frozen candidate IDs
  `[1,0,1,2,0,0,1,3,2,3]`.
- The method reconstructs canonical long-v3 matrices, requires a self-hashed
  sacrificed calibration and pinned `ldpc==2.4.1`, sends nested syndrome
  extensions in four synchronous global rounds, and uses one locked 64-bit
  frame-wide Toeplitz tag only as a stopping check.
- The decoder receives neither Alice truth nor tag/match information. All ten
  planes are decoded each attempted round. A full-prefix nullspace test proves
  four syndrome-consistent rounds terminate as `verify_failed`, not a false
  exact-success oracle.
- Formal transcripts bind the atomic seed/tag disclosure, per-plane syndrome
  extensions, local tag checks, caps, terminal status and exact leakage.
  Main-thread tests: Phase 5 6/6, long-v3 regression 13/13, v2 regression
  7 passed/1 skipped; compilation and frozen-directory checks passed.
- This is executable-method engineering evidence only. There is no immutable
  confirmation package, qualification result, verifier, promotion, or fair
  comparison eligibility yet.
- Next binary work is planner-owned Phase 6: freeze the calibration artifact,
  fresh confirmation generator/lock, immutable runner/verifier DAG, statistical
  gate, invalid-run retention, and exact stop rules before any execution.

#### B3 Phase 6 synthetic qualification: non-promoted (2026-07-26)

- Phase 6A accepted the existing 20 dB main/chunk TTBIN and q=1024 sidecars,
  selected 64 sacrificed bw100 frames plus 96 reserved real-confirmation
  frames, and reconstructed calibration hash `604aa77d...`.
- Immutable synthetic package:
  `formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`.
  Prepare, execute, and strict read-only verification each ran exactly once.
- Verifier accepted all 64 outcomes and artifact/transcript/calibration/source
  bindings with `decoder_reexecution=false`.
- Gate results were calibrated 3/32 and stress_125 1/32; all other 60 frames
  were `verify_failed`. Forbidden internal/provenance/accounting failures were
  zero.
- The method is `non_promoted`. The reserved real data remain unread by the
  decoder and Phase 6C is locked. Do not run real qualification, retune from
  these confirmation outcomes, or retry this package.
- A successor must be a new OpenSpec change with a scientifically new decoder
  or code design and fresh synthetic confirmation.

### B3 — Requalify on fresh evidence

- Materialize and verify the already frozen global policy/calibration from
  sacrificed development data without reading confirmation.
- Run a fresh, immutable synthetic confirmation package with strict read-only
  verification.
- Predeclare the statistical gate in the new OpenSpec. Do not copy the old
  31/32 gate mechanically if the frame count or claim domain changes.
- Only a synthetically promoted binary method may receive a fresh real-data
  lock and bounded real qualification.

### Binary stop conditions

- The proposed code family cannot provide deterministic nested redundancy.
- Improvements appear only after inspecting confirmation outcomes.
- Leakage, shortening, puncturing, or failed rounds cannot be accounted
  exactly.
- Runtime is achieved by silently changing the decoder or success semantics.

## Lane N: Nonbinary LDPC

Provisional formal identity: `nbldpc_formal_v1`.

Suggested future OpenSpec change: `implement-formal-nonbinary-ldpc`.

### N0 — Backend and decoder feasibility, without qualification

- Require deterministic GF(2^m) arithmetic for the intended q values,
  including q=1024 if that remains in the claim domain.
- Pin the backend, primitive polynomial/field representation, symbol encoding,
  and version. Fail closed on mismatch or unsupported q.
- Compare bounded implementations of nonbinary BP/min-sum, EMS, or FFT-QSPA
  using runtime and memory caps. The current greedy hard decoder is not a
  promotion candidate.
- Do not add a large dependency until this feasibility stage identifies the
  smallest backend that satisfies the frozen interface.

### N1 — Define the codebook contract

- Construct rate-compatible QC/protograph-style q-ary parity-check families
  with explicit nonzero field coefficients.
- Verify rank over GF(q), not over GF(2).
- Define canonical bytes covering q, field polynomial/basis, dimensions,
  topology, coefficients, construction seed, and ordering; hash every codebook
  in a top-level manifest.

### N2 — Define soft decoding and formal accounting

- Derive symbol likelihoods from a q-ary symmetric model or a calibrated
  empirical confusion matrix using sacrificed data only.
- Alice sends a GF(q) syndrome; Bob decodes the coset locally. No Alice truth
  may be read during confirmation.
- Convert reconciled symbols to the canonical MSB-first bit representation for
  formal Toeplitz verification.
- Account exactly for q-ary syndrome symbols, invoked verification tags, and
  public control. Never compare raw syndrome-symbol counts to binary
  syndrome-bit counts.

### N3 — Fresh synthetic qualification

- Completed once under the frozen N3 contract. The selected policy was margin
  7, scale 1.0, max_iter 10 and 32 checks.
- Confirmation produced 18/32 verified successes at p=.20 and 5/32 at p=.30,
  below the independent 31/32 gates. The result is non-promoted.
- Retain the seven-artifact package unchanged. Official strict verification is
  unverifiable because the live worktree hash drifted; diagnostic replay does
  not replace the official verifier.

### N4 — Bounded real qualification

- Create a real-data lock only after independent synthetic promotion.
- Restrict claims to the exact qualified dimension, frame length, loss/bin
  domain, symbol mapping, and decoder/codebook configuration.

### Nonbinary stop conditions

- No deterministic and pinned backend supports the locked q/field contract.
- q=1024 complexity exceeds the predeclared runtime or memory cap.
- The only working decoder remains greedy hard syndrome bit flipping.
- Field encoding, syndrome disclosure, or verification-bit mapping is
  ambiguous.
- Success depends on a silent backend, decoder, or lower-q fallback.

## Parallel Coordination

The binary lane may proceed to planner-owned Phase 6. The nonbinary lane is
stopped after its non-promoted N3 result unless a new scientific change is
proposed without reusing confirmation as tuning data. They share only the
final comparison contract, not codebooks, calibration, confirmation, or
promotion evidence.

```text
Binary:     formal method -> freeze fresh confirmation -> fresh gate
                                                               \
                                                                -> later fair comparison
                                                               /
Nonbinary:  N3 non-promoted -> retain evidence / new independent proposal
```

Continue through the two existing separate OpenSpec changes. Every new work
package must freeze its own tasks and acceptance criteria. The main thread owns
planning, thresholds, scientific acceptance, and final review. A Terra-low
operator implements only named frozen tasks and specified tests; it does not
reinterpret requirements or declare promotion.

## Barrier to the Final Comparison

A later comparison change may include only methods independently promoted
within their declared domains. At that point:

- source frames, mappings, and claim domains must be identical;
- method-specific leakage must remain auditable and be converted to disclosed
  bits consistently;
- failures must remain in denominators under the frozen status contract;
- runtime environment and resource caps must be reported;
- Polar must have a frame-identical formal adapter rather than only imported
  aggregate results.

Until those conditions hold, the two LDPC lanes are research candidates, not
entries in a declared winner ranking.

## 2026-07-27 Parallel-Lane Update

| Lane | Latest immutable evidence | Status | Allowed next action |
|---|---|---|---|
| Binary LDPC | `20260727_v1_binary_ldpc_v4_development` | Strictly verified package, but development stopped at 0/512 in both strata because every selected-plane call hit a confirmed NumPy-array versus list backend-boundary defect | New versioned implementation-correction OpenSpec only; preserve v4 and do not prepare synthetic/real evidence |
| Nonbinary LDPC | `20260726_v2_nbldpc_synthetic` | Strictly verified `non_promoted_development`, 0/24 and 5/24 | Preserve evidence; no confirmation, N4, or `.ttbin` processing |

Binary v4 engineering now includes the complete conditional synthetic and real
tooling, including read-only source/transcript payload reconstruction and
integer promotion gates. Those downstream tools were tested but never used to
create production evidence because the development prerequisite was false.

The binary outcome is not FER: a no-decode diagnostic confirms that
`ldpc==2.4.1` requires `error_channel` as a Python list, whereas the immutable
development runner passed a NumPy array. The formal method already has the
correct conversion. Do not edit the bound source and then re-verify the old
package; its source-hash DAG would correctly reject that drift.

Both lanes therefore remain outside the fair Cascade/LDPC/Polar comparison.
The next binary planning decision is whether to authorize a new,
implementation-only correction version with fresh evidence. Rate adaptation,
matrix retuning, synthetic confirmation, real qualification, and comparison
remain out of scope until that decision and a new development gate.

## 2026-07-27 Binary Correction Update

| Lane | Latest immutable evidence | Status | Allowed next action |
|---|---|---|---|
| Binary LDPC | `20260727_v2_binary_ldpc_v4_development` | Strictly verified development ready: nominal 510/512, stress 511/512, zero forbidden failures; backend array/list defect corrected without changing scientific inputs | Main-thread audit of one fresh synthetic v4 plan; no real run or comparison yet |
| Nonbinary LDPC | `20260726_v2_nbldpc_synthetic` | Strictly verified `non_promoted_development`, 0/24 and 5/24 | Preserve evidence; no confirmation, N4, or `.ttbin` processing |

The binary lane has cleared only its sacrificed-development screen. The
corrected package selected candidates `[0,0,0,0,0,0,2,0,2,2]` and is bound to
the failed-v1 predecessor, unchanged TTBIN calibration lock, matrices, channel
model, decoder policy, denominators, and gates. No corrected-v4 production
synthetic or real package exists.

The lanes therefore remain asymmetric and still cannot enter the final
Cascade/LDPC/Polar comparison. Binary may next seek independent synthetic
promotion; nonbinary remains stopped before confirmation.

## 2026-07-28 Corrected Synthetic Update

| Lane | Latest immutable evidence | Status | Allowed next action |
|---|---|---|---|
| Binary LDPC | `20260728_v2_binary_ldpc_v4_synthetic` | Strictly promoted: nominal 127/128, stress 126/128, zero forbidden failures | Add same-domain real source capacity, then one 128×3 real lock/run |
| Nonbinary LDPC | `20260726_v2_nbldpc_synthetic` | `non_promoted_development`, 0/24 and 5/24 | Preserve evidence; no confirmation or real processing |

The binary lane is now synthetic-qualified but not real-qualified. Existing
real sidecars leave only 85 non-reserved frames per registered bin width,
versus 128 required. The 43-frame-per-stratum deficit must be filled with
traceable new data, preferably at least 64 newly supplied complete frames per
stratum. Do not reuse v3-reserved frames or lower the frozen 128-frame
denominator and 126/128 gate. Neither LDPC lane is yet eligible for the final
three-method comparison.

The binary real-source intake layer is now implemented and main-thread
accepted. It rejects raw-capture copies and duplicate frame payloads, freezes
three-stratum provenance and hashes, and reconstructs the real selection
without decoding. The local `TypeII_776.1nm_3s - 副本` tree is not usable:
its main/chunk `.ttbin` hashes equal the registered acquisition. Binary
therefore waits for one genuinely new 20 dB acquisition; nonbinary remains
stopped at development.

## 2026-07-29 Binary 16 dB Transfer and 10 dB Successor

| Lane | Latest immutable evidence | Status | Allowed next action |
|---|---|---|---|
| Binary LDPC | `20260729_v1_binary_ldpc_v4_16db_transfer` | Strictly verified `non_promoted_transfer`: bw120 125/128, bw180 128/128, bw200 128/128, zero forbidden | Implement and independently accept the frozen unchanged-method 10 dB transfer OpenSpec; do not rerun 16 dB |
| Nonbinary LDPC | `20260726_v2_nbldpc_synthetic` | `non_promoted_development`, 0/24 and 5/24 | Preserve evidence; no confirmation or real processing |

The binary successor is
`binary-ldpc-v4-10db-transfer-qualification-v1`. It uses a distinct Type-II
10 dB `.ttbin` acquisition and binds the promoted synthetic package plus the
non-promoted 16 dB predecessor. A pass can support only the registered 10 dB
domain. It cannot erase the 16 dB miss, unblock the 20 dB route, or make the
binary and nonbinary lanes comparison-ready.

## 2026-07-29 Binary 10 dB v2 and v5 Route

| Lane | Latest immutable evidence | Status | Allowed next action |
|---|---|---|---|
| Binary LDPC | `20260729_v2_binary_ldpc_v4_10db_transfer` | Strictly verified non-promoted: 125/128, 127/128, 128/128; zero forbidden | Implement the frozen v5 unused-frame partition and incremental-redundancy development; no v4 rerun |
| Nonbinary LDPC | `20260726_v2_nbldpc_synthetic` | `non_promoted_development`, 0/24 and 5/24 | Preserve evidence; no confirmation or real processing |

Binary v5 is a method-development lane, not another v4 transfer attempt. It
must pre-lock development and sealed confirmation roles, account added
syndromes/tags/feedback, pass sacrificed development, and pass a fresh
synthetic confirmation before real qualification. Neither LDPC lane is yet
eligible for the final Cascade/LDPC/Polar comparison.
