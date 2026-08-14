# Specification: Binary LDPC Adjacent-Channel v4

## Requirement: Immutable Successor Identity

The system SHALL add `ldpc_formal_v4` without changing v1-v3 code, evidence,
schemas, conclusions, or the frozen Polar baseline.

## Requirement: Sacrificed Adjacent-Bin Calibration

The system SHALL reconstruct exactly the 64 sacrificed bw100 frames from the
bound TTBIN-derived sidecars and accept only the frozen 16,384-symbol
`{0,+1,-1}` delta counts and one-Gray-bit property specified in `design.md`.
Confirmation or real outcomes SHALL NOT influence the model.

## Requirement: Bob-Conditioned Soft Information

Each v4 plane decoder SHALL receive only the exact per-position error
probabilities derived from Bob's symbols, the frozen adjacent-bin model, and
the selected stratum. Alice truth, tags, and verification matches SHALL not
enter the likelihood or correction path.

## Requirement: Deterministic Finite-Length Codebook

The system SHALL construct and reconstruct-verify exactly 40 n=256 anchored
column-weight-three candidates using the frozen seeds, RNG call order, row
anchoring, validity gates, HGF2V4 bytes, diagnostics, and complete self-hashed
manifest specified in `design.md`. No external GPL code or matrix SHALL be
copied.

## Requirement: Plane-Specific Fixed Disclosure

V4 SHALL use the exact plane row counts
`[16,16,16,24,24,32,48,80,136,192]`. A successful frame SHALL disclose
exactly 584 syndrome bits plus one 64-bit tag. No adaptive or per-frame rate
selection is permitted.

## Requirement: Sacrificed Development Readiness

The system SHALL run all four candidates on identical deterministic 512-frame
nominal and stress development strata, select one candidate per plane by the
frozen tuple, aggregate exact q=1024 frame success, and require at least
495/512 in each stratum with zero forbidden failures before synthetic prepare.
This is development evidence only.

## Requirement: Formal V4 Decode and Verification

The formal method SHALL use installed `ldpc==2.4.1`, the frozen product-sum
serial BP+OSD-0 policy, one decoder call per plane, exact syndrome consistency,
one final 64-bit Toeplitz verification tag, canonical transcript, caps, status
precedence, and leakage/control accounting from `design.md`.
The selected-matrix binding SHALL use the exact self-hashed
`binary_ldpc_v4_selection_v1` schema frozen in `design.md` and SHALL be
reconstructed and validated rather than inferred from development rows.

## Requirement: Immutable Development Package

The development runner SHALL use prepare/execute, exclusive fresh paths,
failure retention, canonical seven-file completed artifacts, scoped hashes,
and a strict read-only verifier that reconstructs all deterministic inputs and
reports `decoder_reexecution=false`.

## Requirement: Fresh Synthetic Promotion

Only a strictly verified ready development package may prepare v4 synthetic
qualification. Qualification SHALL use fresh domain-separated roots and
exactly 128 nominal plus 128 stress frames. Each stratum SHALL independently
require at least 126/128 verified successes, exact denominators, and zero
forbidden failures.

## Requirement: Synthetic Stop Rule

Synthetic non-promotion SHALL retain an immutable failed package and SHALL
forbid real lock/prepare, tuning, rerun, recovery overwrite, and use of
confirmation truth in any successor.

## Requirement: Conditional Fresh Real Qualification

Only the exact strictly verified promoted synthetic package may unlock a new
real lock. The lock SHALL exclude every v3 reserved confirmation identity and
select 128 new complete frames from each of bw120, bw180, and bw200. Each
stratum SHALL independently require at least 126/128 verified successes with
zero forbidden failures.

## Requirement: Qualification Integrity

Synthetic and real packages SHALL be additive, no-overwrite, hash-DAG-bound,
failure-retaining, non-resumable after external kill, and strictly verifiable
without decoder reexecution. Verifiers SHALL bind scoped source-file hashes,
not live whole-worktree state.

## Requirement: Bounded Scientific Claim

Even real promotion SHALL establish only the current 20 dB acquisition,
q=1024, Gray mapping, 256-symbol frame, and registered bin-width domain. It
SHALL NOT establish cross-loss generality, independent-acquisition
generalization, or a Cascade/Polar winner.

## Requirement: Operator Separation

The main thread SHALL own planning, thresholds, production plan review,
execution authorization, promotion decisions, acceptance, and scientific
claims. Terra low SHALL only implement frozen tasks and run specified tests,
without changing requirements or making acceptance conclusions.
