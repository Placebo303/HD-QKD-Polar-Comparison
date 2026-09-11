# D7-F Result Acceptance R1 — Reverse-Order Regression Diagnostic

- Lifecycle: `V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR`, plan revision R1.
- Execution UUID: `b6d62184-fd15-483d-947e-01ea66ddc13c`.
- Execution root: `workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c` (frozen seven files, immutable).
- Authorization lifecycle: auth `a099b257` → revoke `851efb92`; exactly one invocation (attempts/completed `1/1`).
- Solidification: `8e3bdbee` (`result(d7-f): record one reviewed reverse-order discriminator invocation`).
- Pre-RESULT: `D7_F_PRE_RESULT_REVIEW_PASS_R1` (independent R01–R22 recomputation, no blocking issues).
- Headline counts (A01 independently recomputed from committed scalars, 2026-09-11):
  128/128 calls completed; 64/64 source marginals, `transfer_invoked 64`, `transfer_blocked 0`
  (`retries/resumes/reruns 0`); crash 0 / nonfinite 0 / watchdog 0.

## Per-f 2×2 paired tables (forward vs reverse both-layers-exact; 16 paired seeds each)

### Stratum 1 — f=1.0 (`NO_REVERSE_LIFT`)

| | reverse both-exact | reverse not both-exact |
|---|---|---|
| forward both-exact | both 0 | reference-only (forward-only) 0 |
| forward not both-exact | candidate-only (reverse-only) 0 | neither 16 |

Forward both-exact 0/16, reverse both-exact 0/16.

### Stratum 2 — f=1.2 (`REVERSE_REGRESSION`)

| | reverse both-exact | reverse not both-exact |
|---|---|---|
| forward both-exact | both 0 | reference-only (forward-only) 2 |
| forward not both-exact | candidate-only (reverse-only) 0 | neither 14 |

Forward both-exact 2/16 (seeds 2026091302, 2026091304), reverse both-exact 0/16.

## Source/target exact overlap

- Forward (`L1→L2`): source L1 exact 3/16 (seeds 1302/1304/1309), target L2 exact 3/16
  (seeds 1302/1304/1306); overlap on only 2 identities (1302, 1304) — the two both-exact arms.
- Reverse (`L2→L1`): source L2 exact 0/16 while target L1 exact 7/16
  (seeds 1302/1304/1306/1307/1309/1312/1313), so target lift does not produce joint recovery.
- `both_layers_exact == (l1_exact AND l2_exact)` on all 64 pairs (0 violations).
- Decoder rows: `converged_exact` ×13 (3 FWD_SRC L1, 3 FWD_TGT L2, 7 REV_TGT L1; REV_SRC 0),
  `converged_no_syndrome` ×115; `exact` vs `syndrome_ok` coincide row-wise here (13/13)
  but remain separate columns; `undetected` never merged into success.

Terminal (10-priority order, position 9): `D7_F_REVERSE_ORDER_REGRESSION` (internally consistent:
f=1.2 `reference_only=2, candidate_only=0` triggers regression; no higher-priority terminal fires).

## Provenance and resources

- Provenance: all 128 records `belief_provenance=CHECK_UPDATED`, `finite=True`,
  `belief_shape_ok=True`; all 64 SOURCE rows `transfer_eligible=True` (TARGET rows empty per schema).
- Walls: stored `41.2815843069402 s` (== recomputed per-call sum, ≤1500); per-call max
  `0.4735 s` (<120); outer wall 42–44 s (<1800+30).
- RSS: peak `133021696` bytes (~126.9 MiB, <2 GiB); watchdog `0`.
- Verifier transcript (persisted in operator return, byte-consistent with root):
  literal `VERIFY_OK {'ok': True, 'problems': [], 'records': 128,
  'terminal': 'D7_F_REVERSE_ORDER_REGRESSION'}`, exit `0`; root sizes/mtimes byte-identical
  before/after verify.

## Accepted scope

Accepted label: `D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`

Permitted inference: under this frozen synthetic contract, reversing a single sequential pass
does not convert the D7-E directional target lift into complete two-layer recovery.

Unsupported-claims ceiling: no claim that L2→L1 transfer is useless; no alternating-impossibility
claim; no general NB-LDPC failure claim; no FER/leakage/key-rate claim; no qualification;
no R1d/G1/G2 permission.

## D7-G route

Next gate: `D7_G_EXTRINSIC_CONTRACT_PROPOSAL`. Route: specify and certify a code-factor
extrinsic-message contract that can support future alternating cross-layer BP without returning
a layer's incoming evidence back to itself. Feedback (multi-round alternating) remains
unauthorized and out of scope until that contract passes independent certification.
