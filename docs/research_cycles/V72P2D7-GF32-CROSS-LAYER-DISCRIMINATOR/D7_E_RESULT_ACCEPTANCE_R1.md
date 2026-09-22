# D7-E Result Acceptance R1 — Directional Cross-Layer Transfer Diagnostic

- Lifecycle: `V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR`, plan revision R1.
- Execution UUID: `faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`.
- Execution root: `workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c` (frozen seven files, immutable).
- Authorization lifecycle: auth `b148c9d4` → revoke `34085c15`; exactly one invocation (attempts/completed `1/1`).
- Solidification: `40977a2c` (`result(d7-e): record one reviewed cross-layer discriminator invocation`).
- Pre-RESULT: original verdict `D7_E_PRE_RESULT_REVIEW_BLOCKED_R1` retained; R18 addendum closes the
  overall review as `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`
  (`D7_E_PRE_RESULT_REVIEW_R18_ADDENDUM_PASS_A1`).
- Headline counts (A01 independently recomputed from committed scalars, 2026-09-11):
  192/192 calls completed; 64/64 transfer slots eligible and invoked (`transfer_blocked 0`);
  exact 16 / syndrome 16 (`exact==syndrome_ok` on all 192 rows); crash 0 / nonfinite 0.

## Per-stratum 2×2 tables (control vs transfer exact; 16 paired blocks each)

### Stratum 1 — f=1.0, L1_TO_L2 (`NO_TRANSFER_RECOVERY`)

| | transfer exact | transfer not exact |
|---|---|---|
| control exact | both 0 | control-only 0 |
| control not exact | transfer-only 0 | neither 16 |

Control 0/16, transfer 0/16.

### Stratum 2 — f=1.0, L2_TO_L1 (`NO_TRANSFER_RECOVERY`)

| | transfer exact | transfer not exact |
|---|---|---|
| control exact | both 0 | control-only 0 |
| control not exact | transfer-only 0 | neither 16 |

Control 0/16, transfer 0/16.

### Stratum 3 — f=1.2, L1_TO_L2 (`AMBIGUOUS_TRANSFER_EFFECT`)

| | transfer exact | transfer not exact |
|---|---|---|
| control exact | both 0 | control-only 0 |
| control not exact | transfer-only 3 | neither 13 |

Control 0/16, transfer 3/16.

### Stratum 4 — f=1.2, L2_TO_L1 (`STRONG_TRANSFER_LIFT`)

| | transfer exact | transfer not exact |
|---|---|---|
| control exact | both 3 | control-only 0 |
| control not exact | transfer-only 4 | neither 9 |

Control 3/16, transfer 7/16; four transfer-only, zero control-only.

Terminal (12-priority order, position 9): `D7_E_L2_TO_L1_TRANSFER_LIFT`.

## Provenance and resources

- Provenance: `belief_provenance CHECK_UPDATED:192`, `PRIOR_ONLY:0`, `WARM_START_UNSPECIFIED:0`.
- Walls: stored `64.9536 s` (≤1500); per-call max `0.4379 s` (<120); outer wall ~73–89 s (<1800+30).
- RSS: peak `132390912` bytes (<2 GiB, VmHWM-sourced per frozen A2 rule); watchdog `0`.

## Disclosed verify-transcript gap

- Verify literal `VERIFY_OK {'ok': True, 'problems': [], 'records': 192,
  'terminal': 'D7_E_L2_TO_L1_TRANSFER_LIFT'}`, reported exit `0`.
- Provenance label: `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN` — resupplied under main-thread
  authority from the prior operator return; no standalone verifier log file, no separately persisted
  shell exit capture or verifier timestamps exist. The appendix supplies provenance only and does not
  itself prove the verifier ran (`D7_E_VERIFY_TRANSCRIPT_APPENDIX_A1.md`).
- The gap is procedural-persistence, not artifact-falsification: every independently recomputable
  invariant (R01–R17, R19–R22) passed and root immutability holds.

## Accepted scope

Accepted label: `D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`

Permitted inference: for this frozen synthetic Model-F/decoder/matrix/seed contract, useful transfer
is direction-dependent and strongest in `L2_TO_L1` at `f=1.2`.

Unsupported-claims ceiling: this acceptance grants no general cross-layer success claim; no
FER/leakage/key-rate claim; no qualification; no real-data performance claim; no proof that
alternating decoding converges; no R1d/G1/G2 permission.

## D7-F route

Next gate: `D7_F_REVERSE_ORDER_PACKET_FREEZE`. Route: test whether the directional lift survives as
complete two-layer recovery when reversing the sequential order (`L1→L2` vs `L2→L1` paired arms).
No feedback cycle is implemented yet: existing provenance proves a posterior consumed checks, but it
does not expose the cavity/extrinsic messages needed to prevent syndrome evidence from returning to
its source layer. Multi-round alternating therefore remains blocked pending a verifiable
extrinsic/cavity contract.
