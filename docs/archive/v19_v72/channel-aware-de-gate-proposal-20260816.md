# Channel-Aware DE Gate — Proposal Draft (Route B2/B4 successor)

Status: DRAFT — not an active OpenSpec change; execution gated on user approval

## Motivation
- Route B M2 showed plain irregular NB-LDPC DE on the q=16 folded real structured channel
  has a practical rate ceiling ≈0.60 (f≈4.18).
- The equal-entropy QSC control (p=0.038, H≈0.3815) converged at rate 0.63/0.65 in 16/16 runs,
  while the folded structured channel failed in the same budget. Therefore **channel structure is the limiting factor**.
- Blindly increasing DE budget or moving to q=32/64/128 is not the correct next step.

## Proposed change name (draft)
`formal-nonbinary-ldpc-v19-channel-aware-de-gate`

## Scope
1. Pre-register a **channel-aware DE gate** with target `f≤1.3` on the legacy structured channel
   using an honest two-part leakage decomposition:
   - `f = (syndrome_bits + disclosed_lsb_overhead) / H_full_q1024`
   - Current R=0.60 q=16 folded candidate honest f ≈ (1.6 + 0.05)/0.547 ≈ 3.0 (per plan §B-3).
2. Candidate mechanisms to evaluate (diagnostic/prototype before production):
   - Per-symbol-class puncture: puncture only clean/stable symbol classes, use the folded
     channel's low-entropy clean mass to increase effective rate.
   - Pacher-style two-step / LSB public: disclose noisy LSB planes, protect only high planes
     with NB-LDPC; model the resulting effective channel in DE.
   - Structured edge-label distributions: use per-bit-plane / per-class weights in DE rather
     than a single aggregated folded `w`.
3. Keep the existing frozen DE infrastructure; add a new v19 module/CLI/tests.
4. Execute-once + strict replay + no-rerun/no-tuning discipline.

## Gates
- G0: deterministic synthetic/structured channel reproduction.
- G1: rate ladder {0.70, 0.75, 0.80, 0.85, 0.875} on the effective channel after the chosen
  mechanism; require `entropy_converged=True` and `error_prob=0`.
- G2: honest full-channel f≤1.3 on the legacy q=1024 statistics (V17/real pairs).
- G3: no changes to frozen baseline dirs; official outputs only additive.

## Not in scope
- q=32/64/128 scaling until G1 passes.
- Finite code construction / PEG / decoder qualification until the DE gate passes.

## Evidence to reuse
- `v18_b2_m2_qsc_ctrl_all_converged_20260816/`
- `v18_b2_m2_r06_par_seed7_20260816/`
- `docs/route-b-m2-qsc-control-result-20260816.md`
