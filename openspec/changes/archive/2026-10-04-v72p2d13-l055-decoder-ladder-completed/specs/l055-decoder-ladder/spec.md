# Spec delta — L055 failure decoder ladder (`l055-decoder-ladder`)

Change: `v72p2d13-l055-decoder-ladder`. Track: implementation/readiness (zero
scientific calls). Packet §2 is transcribed exactly; this delta ADDS the D13
ladder contract without altering any existing spec.

## ADDED requirements

### Selection

- REQ-D13-SEL-01: The input root
  `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450` is
  read-only and SHALL NOT be modified.
- REQ-D13-SEL-02: Selection predicate is exactly `arm == "L055" AND
  exact == false`, yielding 30 records at n128 and 26 at n256 (56 total); the
  frozen 56-identity list in `design.md` §3 is authoritative.
- REQ-D13-SEL-03: No successful D12 record SHALL enter the ladder.
- REQ-D13-SEL-04: Preserved per record: graph/block identities, degree tables,
  coefficients, Model-F prior, GF32/poly37, cold initialization.

### Replay gate

- REQ-D13-REPLAY-01: Every selected input is first replayed through
  `ROW_LAYERED_90_ALPHA_1` (accepted RL90 binder, cold, damping 1.0).
- REQ-D13-REPLAY-02: Each replay MUST match the stored baseline fields for
  exact, syndrome, iterations, provenance and failure identity.
- REQ-D13-REPLAY-03: The FIRST replay mismatch blocks ALL ladder calls.
- REQ-D13-REPLAY-04: CHECK_UPDATED provenance is mandatory on every decoder
  return admitted as evidence.

### Ladder arms and ceiling

- REQ-D13-ARM-01: Exactly three arms, in fixed order, on every selected
  failure: `ROW_LAYERED_360_ALPHA_1`, `ROW_LAYERED_360_ALPHA_0_7`,
  `FLOODING_360_ALPHA_1`. No added arms.
- REQ-D13-ARM-02: All arms reuse the accepted D7-X3/v35 binders unchanged
  (RL360 = accepted row-layered target with `max_iter=360`; damping-0.7 = the
  existing `damping_alpha` parameter, NOT tuned; flooding-360 = accepted
  flooding target with `max_iter=360`). No new decoder implementation.
- REQ-D13-ARM-03: Total scientific ceiling is 56 baseline replay + 56×3 ladder
  = 224 calls. Exact, syndrome-valid and undetected remain separate.

### Rescue gates, ranking, terminals

- REQ-D13-GATE-01: Per arm, count rescues by width and total.
- REQ-D13-GATE-02: `MATERIAL_RESCUE` = total ≥12 AND ≥4 at each width.
- REQ-D13-GATE-03: `MODEST_RESCUE` = total 3–11 with ≥1 rescue at each width.
- REQ-D13-GATE-04: `NO_RESCUE` = total ≤2.
- REQ-D13-GATE-05: Any other asymmetric outcome = `RESCUE_AMBIGUOUS`.
- REQ-D13-RANK-01: Multiple MATERIAL arms rank by total rescues, then
  worst-width rescues, then mean iterations among rescues, then the fixed arm
  order in REQ-D13-ARM-01.
- REQ-D13-TERM-01: Terminals are exactly `D13_SELECT_RL360`,
  `D13_SELECT_RL360_DAMP07`, `D13_SELECT_FLOOD360`,
  `D13_MODEST_DECODER_RESCUE`, `D13_NO_MATERIAL_DECODER_RESCUE`,
  `D13_DECODER_RESCUE_AMBIGUOUS`, or explicit engineering/resource blocked.
- REQ-D13-TERM-02: A selected arm requires MATERIAL_RESCUE.

### Root, budgets, claims

- REQ-D13-ROOT-01: Future root is exactly
  `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
  (verified absent in readiness; fresh never-overwrite minimal root at
  execution).
- REQ-D13-BUDGET-01: ≤224 scientific calls; ≤8 setup; ≤1800 s wall;
  ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/repair/seed
  search/tuning.
- REQ-D13-CLAIM-01: Frozen synthetic L1 decoder diagnostic only; no ensemble
  optimality, forward/L2, FER/leakage/SKR, real-data, D7-H or qualification
  claim.

## Out of scope (explicit non-requirements)

- No decoder reimplementation, damping tuning, arm addition, D12 alteration,
  L2/D7-H execution, real-data contact, commit or push.
