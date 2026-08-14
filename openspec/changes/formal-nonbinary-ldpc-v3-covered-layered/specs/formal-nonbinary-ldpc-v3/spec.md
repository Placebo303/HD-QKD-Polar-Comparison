# Delta Spec: Formal Nonbinary LDPC v3

## Requirement: Covered deterministic prefixes

`nbldpc_formal_v3` SHALL use only the specified Z=8 six-by-eight QC base
graph, fixed shift table/direction, finite big-endian coefficient-salt search,
GF(1024) coefficients and 24/32/40/48 ordered prefixes.  Every supported
prefix SHALL cover all 64 columns with minimum column degree at least two.
The preflight SHALL reconstruct canonical bytes, full/prefix GF ranks, shifts,
coefficients, zero 4-cycles, degree vectors and the stated no-weight-1-or-2
distance proxy.  For each prefix it SHALL exhaust all 2016 column pairs and
reject a zero column or proportional pair.  Any mismatch SHALL fail closed.

## Requirement: Bounded layered decoder

The only candidates SHALL be full-message layered FFT-QSPA with lambdas .50
and .75, exact ascending single-row extrinsic/product/damped-message/belief
schedule and immediate per-row belief updates.  Both SHALL use Bob plus public
syndrome only, float64, nominal QSC priors and syndrome-consistency-only
stopping after full iterations.  EMS, tail
approximation, pruning, external decoder fallback and Alice-truth input are
forbidden.

## Requirement: Fresh isolated qualification

v3 SHALL use only the four declared PCG64 roots and new CSPRNG Toeplitz
records, all disjoint from prior formal plans.  Development alone selects one
of four policies.  A null selection SHALL produce exactly the declared null
object and no confirmation material.  Confirmation SHALL remain unmaterialized
unless the selected policy achieves 22/24 verified successes in each
development stratum; it SHALL never influence selection.

## Requirement: Promotion and boundary

Promotion SHALL require 31/32 verified successes independently at p=.20 and
p=.30, full denominators, no prohibited integrity failure, exact accounting,
hash DAG and read-only strict replay.  All artifacts are additive/no-overwrite
and provenance is scoped.  Non-promotion or lack of readiness SHALL NOT
authorize N4, sidecars, raw `.ttbin`, real-data claims or a comparison claim.
