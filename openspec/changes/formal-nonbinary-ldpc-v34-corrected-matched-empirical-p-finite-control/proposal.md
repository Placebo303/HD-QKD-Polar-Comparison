# Proposal: formal-nonbinary-ldpc-v34-corrected-matched-empirical-p-finite-control

> **Status: FR1_ACCEPTED_SCIENCE_AMENDMENTS_PENDING / IMPLEMENTATION_NOT_AUTHORIZED**.
> Initial FR1 returned `REJECT_FREEZE`; specification re-review then returned
> `ACCEPT_FREEZE`. Independent science amendments are incorporated below and
> require final re-review. This change
> may be reviewed and revised, but nothing in it authorizes implementation,
> decoder execution, an official run, or a successor.

## Why

V33 established only that exact-rate ensemble DE converges for all three
empirical timestamp channels and both F03 layers. V32 B1 cannot attribute its
finite-graph failures to the packet or decoder because it generated a uniform
substitution channel at the raw SER while decoding with a posterior derived
from the non-uniform empirical joint law `P_s(A,B)`.

V34 asks the next smallest causal question:

> With the V32 B1 packet, decoder, oracle-L1 convention, block count, and
> success rule held fixed, does replacing only the mismatched generator by
> direct draws from the same frozen empirical `P_s(A,B)` used by the posterior
> change the bounded finite-control L2 outcome?

This is a bounded diagnostic control, not a new reconciliation method. It
deliberately avoids code-design sweeps, decoder tuning, rate changes, and
production-package infrastructure.

## Proposed bindings

- Empirical counts: V25 `run_04/channel_counts.npz`, SHA-256
  `e0360203b8003c821d3ee543bdaf712bd853b0ea712055b936ca37f478ddd5b2`;
  train keys only, sources kept separate.
- Packet: V31 `run_01/matrix_payloads.json`, packet
  `m1_16_n1024_n1024|QC-cyclic-projective`, SHA-256
  `3d0e8773a436eed59b515f32c1bde9525814f0ecaf0d8af5cd9d2bcd12ce9242`.
- Field/factorization: GF(32), primitive polynomial 37, F03/A02 natural
  MSB-to-LSB split, `m1=16`, source-specific `m2=184/190/192`.
- Decoder path: the V32 `ProductionRunner` oracle branch calling the V28R
  `decode_error_domain_posterior`; frozen-target schedule `max_iter=30`,
  `streak=20`. No L1 decoder is run: true `U1` is explicitly oracle-only.
- Sampling: for each block, use the exact PCG64/`Generator.choice` construction
  in `design.md` to draw 1024 iid `(A,B)` pairs directly
  from the source's normalized empirical joint table. The same table supplies
  `P(U2|B,U1)`. No SER-only QSC, smoothing, source merge, holdout, or fallback.
- Frozen-target allocation: 20 blocks per source with fresh, source-disjoint seeds
  `340101..340120`, `340201..340220`, `340301..340320`.
- Frozen-target success rule: exact L2 recovery AND syndrome valid AND tag valid
  AND no false accept. Source PASS is at least 19/20 successes, exactly retaining
  the V32 development discriminator; overall PASS requires all three sources.
  The threshold SHALL NOT be strengthened to 20/20 or changed after results.
  It is the V32 development discriminator carried forward for mechanical
  comparability, not a confidence threshold, FER estimate, or qualification
  criterion.

## Scope and claim boundary

V34 contains one corrected matched empirical-P arm (60 blocks total). Existing
V32 B1 is a development-only result under a mismatched generator; it is
read-only context and is not rerun as a second arm. All 60
blocks run after authorization even when ordinary decode failures occur.
V34 changes exactly one **channel-law** variable; fresh seeds are nuisance
randomizations, so this is not a paired statistical trial. The 20 blocks per
source are iid only conditional on the frozen empirical table, fixed packet,
and fixed decoder configuration,
and are not an estimate of general finite-block performance.

- PASS supports only that the corrected matched empirical-P finite control
  succeeds under this one packet, oracle L1, decoder, and small block sample.
- FAIL is a bounded negative result for the same frozen control; it does not
  prove that NB-LDPC, the ensemble, or all finite graphs fail.
- INCONCLUSIVE covers binding drift, invalid probabilities, decoder/interface
  failure, output collision, or interrupted evidence.

No outcome establishes FER, net key rate, real-data qualification, operational
security, promotion, or a production reconciler. No outcome automatically
authorizes decoder modification, degree-distribution design, another packet,
more blocks, a rerun, or V35.

## Lifecycle

1. FR1 independently resolves every item in `design.md` section 8 and reviews
   the four-file OpenSpec packet.
2. Only a main-thread `ACCEPT_FREEZE` may authorize implementation.
3. A later independent IR1 must accept the exact implementation candidate.
4. An official exact-once run additionally requires a new explicit user
   `EXECUTE_AUTH` bound to the accepted HEAD and frozen matrix.
5. ER1 performs post-run read-only reconstruction before any scientific
   acceptance or archive.

## Output root

The proposed unique additive root is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v34_corrected_matched_empirical_p_finite_control/run_01/`.
Tests must use fresh `workspace/v34_<id>/` roots and must never create it.
