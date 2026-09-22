# R12 FRESH (m120-staged, P-1p5M-fresh 2187..2250) — PREREG_AND_AUTH (frozen)

Track: DECIDE (preregistration + authorization record only; no execution, no data access, no commit/push in this file).

## F-pool (frozen population)

- Session `20260107_PPLN_1p5M`, window frames 2187..2250 (64 frames; 2250−2187+1=64), lowest-start-≥2187 rule.
- Freshness proofs (transcribed): disjoint from R9 window 2123..2186; 30 V55 starts incl 2119..2122 + 2295..2298 neighbors; CAL/VAL; parquet ids 0..5124 contains window; 2938 fresh remain.
- Blocking K=2 even-odd → 128 calls.

## F-method (frozen method)

- Mother m120, stages 100/108/120.
- Graphs 4722/4723 REUSED (R11c admission by reference, no rebuild).
- Cold row-layered 90/1.0 single-pass.
- Prior `workspace/v72p2d5_model_f_input/20260907_r1` read-only.
- T=64 tag bits.
- Final-prefix disclosure 564/604/664 bits (S0/S1/S2), tag-once.
- k nominal 28/20/8.
- H 3.347605 + H_L2 sensitivity.
- beta derived-only.
- Fixed arm NONE (contrast vs R9-fixed / R11-diag cross-pool disclosed).

## F-gate (frozen thresholds)

- accepted ≥ 5 AND undetected == 0 → CONFIRMED-GENERALIZING.
- accepted ≤ 2 → POOL-SPECIFIC-LIFT.
- accepted 3–4 → INCONCLUSIVE.
- undetected > 0 → UNDETECTED_STOP absolute.
- Net-yield plain incl negative.

## F-bud (frozen budget/root)

- sci ≤ 384 / setup ≤ 8 / wall 1800+120s / RSS 2GiB / 1-proc / no-retry.
- Root `workspace/g6r12_fresh_c97777aa-620d-448f-8a6c-8abda5fb3b48` PROPOSED-absent — not created, not probed in this preregistration.

## F-cmd (frozen command)

- Exact ARGV: `.venv/bin/python scripts/g6r12_fresh.py --execute-real --execution-authorized --registry v71_data_registry.json --session 20260107_PPLN_1p5M --frames 2187..2250 --arm L020 --prior-root workspace/v72p2d5_model_f_input/20260907_r1 --baseline-root workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae --out-dir workspace/g6r12_fresh_c97777aa-620d-448f-8a6c-8abda5fb3b48`.
- `--execution-authorized` default-false grant; refusal before any root creation, decoder binding, or Model-F load.
- Single invocation; no second invocation authorized.

## F-tests (frozen; R12b return values transcribed)

- 22/22 FAKE pass on fixtures only (no real-data execution): admission incl R9/V55/short/foreign rejects; accounting; staged-increasing; UNDETECTED_STOP; refusal / no-overwrite / verifier probes; R11-baseline import F=87 byte-identical zero-calls.
- Re-pass note: R1 9/9; R11b 13/14, R9b 8/9, R10b2 9/11 with absence-waivers per RULING-2.

## F-stop (frozen)

- Any violation STOP + retain + single decision needed; retained crashes never retried.

## F-auth (frozen authorization)

- Execution covered by ten-round pre-approvals within frozen scope.
- Pre-EXECUTE + Pre-RESULT mandatory, no skipping.
- R12 execution grant NOT consumed by this preregistration write.
- No SKR/qualification/promotion/generalization claim beyond F-gate wording.

## F-conflict

- NONE KNOWN (any discovered conflict enters revise-required before execution).

## Main-thread ruling note (deviation recorded here)

- T5 independent readiness review folded into main-thread adjudication per established precedent (R1/R2/R6/R9/R10/R11); reviewer covers Pre-RESULT.

## Return path

- Prereg return: `docs/research_cycles/V72P3R12-FRESH/PREREG_AND_AUTH.md` (this file); next: Pre-EXECUTE review, then single authorized execution via F-cmd.

## Confirmations

- New dir written once; verbatim frozen values only, zero new science.
- Root PROPOSED-absent confirmed (not created).
- No execution, no data access, no commit/push in this write.
