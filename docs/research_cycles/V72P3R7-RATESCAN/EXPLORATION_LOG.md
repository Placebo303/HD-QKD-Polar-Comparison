# V72P3R7-RATESCAN — EXPLORATION_LOG (append-only)

## Entry 2026-09-18 — R7 rate-scan solidification (EXPLORE)

- **Track:** EXPLORE (solidification writes; no execution, no data access, no commit/push).
- **Scope:** S7 grid m ∈ {100..128 step 4}, L020-winner, n128, decoder-90/1.0, D18-protocol-verbatim.
- **Result:** thresholds 0.68353 → 1.77728, all PASS vs bar 1.581967615365622 (124-equiv − δ, δ = 0.0390625 = 5/128).
- **Grid bound:** S7-min = 100 AT GRID FLOOR.
- **Ledger:** 128/200. DV3 dropped for cap.
- **Checks:** 7/7 suite + verify rc0 + refusal rc2.
- **Artifacts:** `workspace/r7_rate_scan_719f77de-0e69-499f-80b4-397457c8958a/` + 3 new files (module/runner/test `v72p2r7_rate_scan.*`).
- **Non-execution:** zero graphs / decoder-calls / real-data in this solidification.
- **Main-thread acceptance:** R7 batch-end review ACCEPTED as HOLD (blocks D-R7-01 promotion).
- **HOLD verdict + 2 transcribed blockers:**
  1. Floor-effect — bar passes m94-regime too (D18 interior 0.35149 / m94 delta 0.44915 both ≪ bar) while G6-R1 real m94 is 0/128 → bar non-discriminative in 94–100; promoting m100 risks confirming DE-real-gap artifact. Required: downward micro-extension m = 88/92/96 same-protocol/bar to locate transition or prove floor informative.
  2. Margin-substitution — δ value verified (D18 §5.3 + log 167 + ROW_STEP) but 124-anchor reuse unchartered → D-R7-01 must charter/re-derive bar.
- **Pointer:** R8 micro-extension launched.
- **Decision log:** no entry (reviewer-ruled).

## Entry 2026-09-18 — R8 micro-extension (EXPLORE)

- **Track:** EXPLORE (append-only; no execution, no data access, no commit/push).
- **Scope:** grid m ∈ {88, 92, 96} same-protocol/bar as R7.
- **Results:** m88 FAIL 0/0 (delta 0.21478); m92 FAIL 0/0 (0.37103); m96 PASS 8/8 (0.52728).
- **Transition:** LOCATED 92|96 — hard structural (no soft middle, pops agree; FAILs from tail-convergence gate, hold for ANY δ).
- **Ledger:** 48/60. **Checks:** 8/8 suite (7 intact + override test); verify rc0 both roots.
- **Mechanism:** additive-only (defaults byte-identical).
- **Artifacts:** `workspace/r7_rate_scan_low_34aba8c7-8580-453f-b630-855d682fe948/`.
- **Non-execution:** zero graphs / decoder-calls / real-data in this solidification.
- **Reviewer verdict:** UNBLOCK-m100 (not m96: edge + 2 rows above real-failed 94 → repeats gap artifact; not HOLD: edge moots B2 for location though bar-citing promotion text still needs chartering).
- **D-R7-01 main-thread decision:** ADOPT m=100 for fresh-pool (P-1p5M) confirmation; m96 parked.
- **Decision log:** no entry (reviewer rule stands).
