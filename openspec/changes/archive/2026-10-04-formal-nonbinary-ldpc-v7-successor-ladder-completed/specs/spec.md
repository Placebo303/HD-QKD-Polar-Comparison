# Formal Nonbinary LDPC v7 Successor Ladder

## ADDED Requirements

### Requirement: Ordered Development Routes

The system SHALL evaluate R1A, conditionally R1B, R2, and R3 in that order.
Each subroute SHALL use a new identity and fresh development material. It SHALL
stop at the first development-ready route and SHALL NOT continue for comparison
or ranking after success.

### Requirement: Immutable Two-Stage Development

Each subroute SHALL first use one 4+4 sacrificed canary. A 0/4 result in either
stratum SHALL freeze the subroute and advance. Otherwise it SHALL use one fresh
16+16 sacrificed development package. Each plan SHALL receive independent
read-only review before exactly one execution and exactly one strict read-only
replay. No failed package may be rerun or tuned.

### Requirement: Readiness Gate

Development readiness SHALL require at least 15/16 verified successes in each
stratum, zero forbidden failures, strict replay, disclosure <=8.75 bits per
input symbol in each stratum excluding the separately reported tag, and median
runtime <=120 seconds/frame. Readiness SHALL NOT mean promotion.

### Requirement: R1 Construction

R1A SHALL use a deterministic full-rank `(2,3)` GF(1024) n=256 mother code.
R1B MAY run only after R1A's canary gate fails and SHALL combine exactly one
deterministic multiplicative repetition into each variable prior without
duplicating the dense Tanner graph. R1B SHALL be the final repetition depth.

### Requirement: R2 Scientific Identity

R2 SHALL use a bounded, deterministic and independently tested q-ary
density-evolution selection over degree distributions, followed by deterministic
PEG construction. If density-evolution semantics cannot be validated, R2 SHALL
stop as blocked and SHALL NOT relabel a heuristic as density evolution.

### Requirement: R3 Multilevel Accounting

R3 SHALL reversibly map each 10-bit symbol to two GF(32) layers. Both layers
must reconcile before a single final Toeplitz verification. Every disclosed
layer syndrome and invoked tag SHALL be counted; layer failure and conditional
prior provenance SHALL be reconstructible by strict replay.

### Requirement: Confirmation Boundary

The ladder SHALL NOT materialize or execute confirmation, real-data, N4,
sidecar, or `.ttbin` work. A development-ready result SHALL return control for
a new qualification OpenSpec change.

