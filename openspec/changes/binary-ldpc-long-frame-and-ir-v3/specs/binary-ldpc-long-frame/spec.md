# Delta Spec: Binary LDPC Long-Frame Foundation

## Requirement: Additive Candidate-Only Identity

The system SHALL add an offline long-frame candidate codebook component without
changing `ldpc_formal_v1`, `ldpc_formal_v2`, their outputs, or their
qualification conclusions. The new family SHALL be labeled
`candidate_only_not_qualified`.

## Requirement: Frozen Long-Frame Domain

The component SHALL support exactly n=256, 512, and 1024; planes 0 through 9;
candidates 0 through 3; and exact leading-row prefixes at check fractions
1/2, 5/8, 3/4, and 7/8.

## Requirement: Deterministic Nested Construction

Every candidate SHALL be deterministic from domain-separated construction
identity, version, n, plane, and candidate inputs. Each advertised matrix SHALL
be an exact leading-row prefix of one master, have full row rank, and contain
no zero or duplicate columns. The construction and PCG64 draw order SHALL
follow `design.md` exactly. Every prefix SHALL have row weights in `[2,3]` and
column weights in `[1,5]`.

## Requirement: Canonical Encoding and Manifest

Matrices SHALL use canonical HGF2V3 bytes containing magic, little-endian
dimensions, and C-order binary bytes. A complete compact-JSON-hashed manifest
SHALL bind all candidates, prefixes, structural diagnostics, and canonical
matrix hashes. Verification SHALL fail closed and reconstruct the deterministic
manifest.

## Requirement: Evidence Boundary

Structural rank, weight, cycle, and ACE-style diagnostics SHALL be labeled as
proxies. They SHALL NOT be reported as FER, decoded success, verified success,
qualification, or promotion. This work package SHALL NOT read confirmation or
real data and SHALL NOT create production result artifacts.

The exact 4-cycle count and
`column_pair_extrinsic_degree_v1` minimum/sum proxy SHALL use the formulas in
`design.md`; the proxy SHALL be null-minimum when no 4-cycle exists and SHALL
not be represented as a true ACE spectrum.

## Requirement: Sacrificed-Development FER Kernel

The system SHALL add an in-memory development-only evaluator using exact,
domain-separated sacrificed data for both p=.01 and p=.02. It SHALL use the
frozen pinned BP+OSD-0 policy and exact nested prefix order specified in
`design.md`, fail closed without fallback, retain every development frame
status, and count incremental syndrome disclosure as the terminal prefix row
count rather than the sum of prefixes.

## Requirement: Development-Only Candidate Selection

Candidate selection SHALL require exactly four candidates and identical
16-frame development strata. It SHALL use only the exact lexicographic tuple
`[-worst_stratum_successes,-total_successes,total_syndrome_bits,candidate_id]`.
Runtime and structural proxies SHALL remain diagnostic. The selected candidate
is a development result only and SHALL NOT imply qualification or promotion.

## Requirement: Phase 2 Isolation

Phase 2 SHALL NOT write result artifacts, inspect confirmation/real data, run a
full backend sweep, change v1/v2 behavior, or implement qualification,
promotion, or comparison behavior.

## Requirement: Verifier-Bound Full Development Sweep Tooling

The system SHALL provide a two-step no-overwrite runner and strict read-only
verifier for the frozen 3840-row sacrificed-development grid. A completed run
SHALL use exactly the six artifacts, canonical schemas, hashes, execution
order, accepted Phase 2 evaluator/selection, pinned backend, and resource caps
specified in `design.md`.

## Requirement: Failure Retention and Evidence Boundary

Exceptions and internal cap failures SHALL finalize an explicit failed package
without overwriting completed bytes. External-kill partial directories SHALL
remain invalid and non-resumable. Verifier exit 0 SHALL establish artifact
integrity and deterministic selection reconstruction only; it SHALL NOT imply
decoder reexecution, qualification, promotion, or a comparison result.

## Requirement: Production/Test Separation

Reduced-domain and injected-decoder execution SHALL be marked test-only and
available only through private test helpers. Production CLI prepare, execute,
and verification SHALL reject test-only plans and SHALL NOT be exercised in
Phase 3B implementation work.

## Requirement: Frame-Level Global-Round Development

The system SHALL aggregate the selected ten bit planes into q=1024 development
frames. One 64-bit frame-wide Toeplitz tag SHALL model stopping across at most
four global nested-syndrome rounds; the slowest plane SHALL determine terminal
redundancy. Syndrome, tag, public-seed, and union-bound accounting SHALL follow
the exact Phase 4 formulas in `design.md`.

## Requirement: Development Length Selection

The system SHALL select one length using only the frozen frame-level tuple:
worst-stratum successes, total successes, worst-stratum mean key-disclosure
fraction, overall mean fraction, then n. This remains sacrificed-development
design evidence and SHALL NOT authorize confirmation, qualification, or
promotion.

## Requirement: Formal Binary LDPC v3 Method

The system SHALL add an independent `ldpc_formal_v3` implementation for
exactly q=1024, 256-symbol, ten-plane Gray-mapped frames using the Phase 4
selected long-frame candidates, pinned LDPC backend, and frozen sacrificed
calibration contract. Existing formal LDPC versions and shared v1/v2 outcome
validation SHALL remain unchanged.

## Requirement: Deployable Global Stopping

The formal v3 decoder SHALL disclose nested syndrome extensions for all ten
planes in synchronous global rounds and SHALL use one locked 64-bit frame-wide
Toeplitz tag only to stop after a completed round. Candidate selection,
decoder inputs, and correction paths SHALL be independent of the tag and of
Alice-truth equality.

## Requirement: Formal v3 Accounting and Fail-Closed Behavior

The method SHALL retain every attempted terminal status, count cumulative
syndrome disclosure once, count the tag once and the public seed once, use the
union bound over completed tag checks, enforce wall/call/event caps, and
produce a canonically hashed transcript and strictly validated v3 outcome.
Malformed inputs, calibration, codebooks, backend, decoder results, syndrome
consistency, tag mismatch, and resource exhaustion SHALL preserve the exact
status precedence defined in `design.md`.

## Requirement: Phase 5 Evidence Boundary

Phase 5 SHALL implement and test the method only. It SHALL NOT create formal
run artifacts, use confirmation or real data, qualify or promote the method,
or claim a fair comparison result.

## Requirement: TTBIN-Derived Formal Data Lock

The system SHALL read existing q=1024 sidecar symbol pairs without modifying
the frozen TTBIN pipeline, bind the originating main/chunk TTBIN and all
sidecar bytes, construct exact 256-symbol frames, and deterministically isolate
sacrificed calibration from real confirmation.

## Requirement: Synthetic Promotion Gate

The system SHALL execute a fresh verifier-bound 64-frame synthetic
qualification using the frozen real-calibration bit-plane model and an
independent 1.25x stress model. Both 32-frame strata must independently meet
31/32 with zero forbidden failures before real locking or execution.

## Requirement: Real Promotion Gate

Only a strictly verified promoted synthetic package may unlock the 96-frame
20 dB real qualification. Each registered bin-width stratum must independently
meet 31/32 with zero forbidden failures. All failures remain in denominators
and immutable evidence.

## Requirement: Qualification Integrity

Synthetic and real packages SHALL be additive, no-overwrite, hash-DAG-bound,
failure-retaining, non-resumable after external kill, and strictly read-only
verifiable without decoder reexecution. Verification SHALL bind scoped source
file hashes rather than a drift-prone live whole-worktree status hash.
