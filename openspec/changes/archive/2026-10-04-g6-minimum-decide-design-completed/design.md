# Design — G6 Minimum DECIDE Design (Accounting / Schemas / Thresholds)

- Frozen source: planner G6 return in this session (transcribed faithfully; no added science).
- Tags: OBSERVED / DERIVED / PROPOSED / UNKNOWN preserved as frozen.
- No code, no execution, no data access, no commit/push in this call.

## Grounding (OBSERVED numbers carried forward)

- [OBSERVED] D7-E: 192/192 + STRONG_TRANSFER_LIFT.
- [OBSERVED] D7-F: 128/128 reverse regression.
- [OBSERVED] Deltas: `0.5468113653656221` / `0.35149886536562214` / `0.5077488653656221`.
- [OBSERVED] ROW_STEP 5/128.
- [OBSERVED] H_L2 `3.222719884634378`.
- [OBSERVED] D19: M=19/48 AMBIGUOUS, undetected=0, n256 0 calls.
- [OBSERVED] CAL frames/session/source accounting retained from prior cycles (CAL 702..1725 consumed).
- [OBSERVED] VAL 4-frame ineligibility (1726..1729; descriptive-smoke only).
- [OBSERVED] SECURITY_MODEL generic-only.

## G6-3 Accounting equations + denominators

- [PROPOSED] Outcome classes kept isolated: attempted / exact / accepted / undetected (undetected never merged into success/FER).
- [PROPOSED] Disclosure sums include failures (leakage accounting is over attempted population, not success-conditioned).
- [PROPOSED] Retained `k_sym` nominal 34.
- [PROPOSED] Report accepted fraction and exact fraction with stated denominators (attempted as base; exact/accepted as subsets).
- [PROPOSED] `FER_proxy` label (not FER without the frozen qualification semantics).
- [DERIVED] `beta_eff_empirical` derived-only (from leakage and error inputs, never hand-filled); `H_frozen` denominator UNKNOWN (see G6-7).
- [PROPOSED] `reconciled_net_bits` / reconciled rate reported without SKR semantics.
- [PROPOSED] Runtime/memory reported per execution record.
- [PROPOSED] Per-session breakdown required.
- [PROPOSED] Secure-key output BLOCKED in this DECIDE.

## G6-4 Schemas (field names)

- [PROPOSED] Per-frame record fields: frame id, session id, outcome class (attempted/exact/accepted/undetected), syndrome bits, tag bits, control bits, interaction bits, iters, residual, provenance, wall time.
- [PROPOSED] Aggregate record fields: attempted/exact/accepted/undetected counts, accepted fraction, exact fraction, FER_proxy, disclosure sums (syndrome+tag+control+interaction), k_sym nominal, reconciled_net_bits, reconciled rate, runtime, memory, per-session breakdown.
- [PROPOSED] Manifest fields: operating point (n128/m94/L020 `lam_d2_0.20_d3_0.80`), decoder (cold row-layered 90/1.0, Model-F marginal prior), population split (CAL consumed / selection empty / confirmation TBD), key-disjointness attestation, SECURITY_MODEL generic-only.

## G6-5 Go / no-go

- [PROPOSED] UNDETECTED_STOP absolute: any undetected success-verification failure stops (fail-closed).
- [PROPOSED] ENGINEERING_BLOCKED mapping: execution/infra blockers map to ENGINEERING_BLOCKED (not to scientific conclusions).
- [PROPOSED] Terminal labels: NO_USEFUL_RECOVERY vs FIRST_REAL_RECOVERY_CONDITIONAL (conditional; no promotion/qualification/publication claim).
- [UNKNOWN] Numeric cutoffs UNKNOWN (not frozen in G6; a future packet must freeze them before execution).
