# D7-G code-factor extrinsic contract acceptance R1

- Authority: `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md` §10 (Phase-G closeout; dual PASS already established, not re-adjudicated here).
- Branch: `formal-ir-v72p1-addendum-clean`; basis HEAD `08987c6` + only the three review paths (v35 +127/−0 additive; oracle + contract test new).
- Frozen basis: R1 packet §1.2, OpenSpec `v72p2d7-code-factor-extrinsic-contract`, `D7_G_PREREG_R1.md`.

## 1. Accepted contract (interface/certification only)

- Formula: cold-decoder outgoing code-factor message `L_code_ext(x) = L_post(x) − log(p_in(x))`, defined up to a per-row additive constant; stored LSE-normalized, transported via stable softmax (row-constant invariant; reconstruction `softmax(log p_in + store) = softmax(L_post)` exact).
- Enums: `NO_CHECK_EVIDENCE` / `CHECK_EXTRINSIC` / `WARM_START_UNSPECIFIED` (separate namespace; cross-namespace isolation both directions).
- Fields: additive optional `DecoderResult` fields `extrinsic_log_beliefs` / `extrinsic_provenance` (default `None`); first-6 fields and all existing positions unchanged.
- Cold/it0/warm: cold ≥1 sweep emits check extrinsic; iteration 0 emits neutral zeros + `NO_CHECK_EVIDENCE` (ineligible for transfer, no false lift); warm emits nothing usable + `WARM_START_UNSPECIFIED` (fail-closed); nonfinite/shape mismatch fail-loud, never repaired.
- No persistence: no multi-round alternating execution; helper `require_check_extrinsic_for_transfer` accepts only explicit `CHECK_EXTRINSIC` and is unwired from D5/D6/D7 production; flooding extrinsic `DEFERRED` (defaults only, outputs unchanged); no consumer may infer extrinsic by subtracting an unknown/reconstructed prior.
- Certification maxima (tolerance 1e-10 unless noted): tree-exact ≤3.34e-16; loopy-vs-independent-recurrence ≤3.03e-14 (never MAP); forward+backward sum-product match ≤3.34e-16; posterior double-count counterexample deterministic (message gaps 0.387/0.367 vs 1e-2 floor; transfer gaps 0.0657 fwd, 0.0139/0.00646 bwd, redecoded 0.005105 vs 1e-3 floor); contract suite 48/48; D7-A 14/14; BP-compat 14/14; BP-belief 22 passed + 1 field-list pin (T1 PASS-neutral); D7-E 38 passed + 2 (1 transitive pin, 1 env precondition).
- Reviews: `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` (F01) + `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS` (F02).

## 2. Explicitly NOT accepted

- Not an algorithm result: no FER, leakage, key-rate, or qualification claim of any kind.
- No D7-H freeze and no D7-H authorization; no alternating execution; no promotion.
- R1d, G1, G2 remain unauthorized; all execution authorizations remain false.

## 3. Route

- `next_gate` → `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE` (packet freeze only; implementation/execution not authorized by this acceptance).
- D7-H remains not frozen / not authorized; no D7-G/H roots or UUID minted.

End state: D7-G code-factor extrinsic contract accepted as interface/certification only; D7-H awaiting packet freeze, not authorized.
