# Delta Specification: V9 GF(1024) Long-Block IR

## ADDED Requirements

### Requirement V9-1: GF(1024) Method Validation

The system SHALL implement scalable full-vector GF(1024) QSC MC-DE and SHALL
validate its check updates against the independent V8 oracle at q=4, q=8,
q=32, and bounded q=1024.

#### Scenario: Cross-domain validation

- **WHEN** deterministic messages and nonzero edge coefficients are supplied
- **THEN** scalable and direct check updates agree within a frozen tolerance
- **AND** the test fails if coefficient permutation or normalization is wrong.

### Requirement V9-2: Exact Ensemble Rates

The system SHALL compute `m=ceil(f*H_q(p)*n)` and SHALL reconstruct every
edge-view ensemble rate with absolute error <=1e-12.

#### Scenario: Target classification

- **WHEN** a robust ensemble passes but an f=1.08 target ensemble fails
- **THEN** finite-length work may continue only with robust f=1.15
- **AND** artifacts are marked `efficiency_target_not_met`.

Robust conservative gates SHALL be >=.22/.32 for p=.20/.30. Target gates SHALL
be >=.215/.32; .215 is below the p=.20 f=1.08 capacity threshold (~.21827) and
retains a feasible margin.

### Requirement V9-3: V9A Advance Gate

The system SHALL require conservative multi-seed robust DE thresholds >=.22
for p=.20 and >=.32 for p=.30 before creating a finite codebook.

V9A SHALL freeze one complete plan before results and follow independent
read-only review, exactly one deterministic execute covering all four
searches plus validation seeds, and exactly one strict replay. A failed V9A
package SHALL be immutable and SHALL NOT authorize tuning or rerun.

#### Scenario: Robust threshold failure

- **WHEN** either robust threshold is below its gate
- **THEN** V9 stops and records immutable evidence
- **AND** no V9B codebook or scientific plan is created.

### Requirement V9-4: Finite-Length Construction

The system SHALL build n=4096, n=16384, and conditionally n=32768 irregular
GF(1024) graphs from the accepted ensemble using PEG/ACE or a documented
equivalent, deterministic construction, no parallel edges, rank/graph
diagnostics, and random nonzero edge weights.

Every finite GF(1024) parity-check matrix SHALL satisfy `rank(H)=m` before a
scientific plan. n=4096, n=16384, and n=32768 SHALL respectively bind 4, 16,
and 32 ordered mutually disjoint 1024-symbol constituents with IDs, roots,
seeds, hashes, order, and aggregate mapping, with no cross-stage reuse.

### Requirement V9-5: Error-Domain Decoder

The system SHALL decode `d=Hy+s=He` using layered log-FFT-SPA with 100-150
frozen iterations, workers=1, complete syndrome checks, bounded resources, and
fail-closed numerical behavior, without truth or fallback.

### Requirement V9-6: Lifecycle Gates

Every scientific stage SHALL use prepare, independent read-only review, exactly
one execute, exactly one strict replay, fresh identities, and immutable failure
retention.

#### Scenario: V9B canary

- **WHEN** the fresh 4+4 n=4096 canary completes
- **THEN** V9C is authorized only with >=3/4 verified per stratum, zero
  forbidden states, exact disclosure, median <=2h/superframe, and <=3GiB RSS.

#### Scenario: V9C n=16384 canary

- **WHEN** the fresh 4+4 n=16384 canary completes
- **THEN** n=32768 is authorized only with >=3/4 verified per stratum, zero
  forbidden states, exact disclosure, median <=8h/superframe, and <=3GiB RSS.

#### Scenario: V9C n=32768 development

- **WHEN** its fresh 4+4 canary passes and fresh 16+16 development completes
- **THEN** development-ready requires >=15/16 verified per stratum, zero
  forbidden states, strict replay, median <=24h/superframe, and <=3GiB RSS.

The n=32768 canary SHALL hard-timeout each superframe at 24h and SHALL require
median runtime <=16h to advance.

### Requirement V9-7: Superframe Provenance and Leakage

Each n=32768 superframe SHALL bind exactly 32 ordered, disjoint 1024-symbol
constituents. V9C SHALL use a fixed rate per stratum:
`m=ceil(f*H_q(p)*n)`, `L_recon=10*m` syndrome bits, a separate fixed 64-bit
correctness tag, and `L_total=10*m+64`. These values SHALL be hard caps. V9
SHALL reject puncturing, shortening, interactive/adaptive stages,
information-bearing indices/control, and every additional reconciliation
payload. Blind rate adaptation SHALL be deferred to a future V10 change.

### Requirement V9-8: Evidence Integrity

Verification SHALL detect byte, semantic, manifest-link, source, transcript,
public-payload, leakage, gate, identity, and superframe-provenance tampering.
Tests SHALL require an explicit fake runner and SHALL not call production by
default.

### Requirement V9-9: Authorization Boundary

V9 SHALL NOT create or execute qualification, confirmation, real-data, N4, or
formal-comparison work. Passing V9C only authorizes a separate proposal.
