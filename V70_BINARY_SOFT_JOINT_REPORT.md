# V70 Binary Soft-Joint Feasibility Report

**Lifecycle**: PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED, V71_NOT_STARTED
**Head**: 9825d0b336042ad4bf2b26ed31b7fa09a04de620 (provenance 9825d0b, not d6f590ac), Data 84d62779, Method n1024 q1024 GF32 poly37 H1 16x1024 rank16 80b U natural 32*U1+U2 +10-bit bit_i(s)=(s>>i)&1, per_frame 256, Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 disabled full-tag canonical leak Σw_i·m_i+64

## Per-session A-H

| session | CAL D_bits | VAL D_bits | CE_full VAL | required ceil1.3*N*CE | gap 10240-req | margin_gap | rank_ok | pure_maxΔ |
|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB | 1.902 | 1.804 | 7.150 | 9519 | 721 | 0.0704 | True | 8.9e-16 |
| 20260107_PPLN_1p5M | 1.687 | 1.597 | 7.547 | 10047 | 193 | 0.0188 | True | 3.7e-15 |
| 20260123_2M_1p2M_0dB | 1.261 | 1.206 | 8.390 | 11169 | -929 | -0.0907 | NOT_APPLICABLE (NO_INFORMATION_MARGIN, required>=10240 -> matrix NOT_APPLICABLE) | 2.6e-15 |

- A P_global, B P(a|b) λ 221/221/356 (4-fold CV [1e-2,1e4]), C H_full/CE_full, D D_bits=ΣH_bit-H_full ≥ -1e-9 (observed 1.2-1.9 ≥0), E CE_bit 10-dim, F required=ceil(1.3*1024*CE_full_VAL) integer, G soft_joint_factor_update 1024-enum, H family 10240 cols r0=160 step8 tail7 -> required (family_sha replaces H_bin_sha).

### Pure function brute-force

- all_zero llr≡0 ⇒ log_post≡log_prior normalized, max|Δ| 8.9e-16 <1e-12
- delta K=1e6 a*=0,511,1023 ⇒ posterior delta, brute max|Δ| <4e-15 <1e-12
- pure_is_pure True (no I/O/random)

### Budget margin 0/5% (first-match reordered: required>=10240 -> NO_INFORMATION_MARGIN, matrix NOT_APPLICABLE)

- gap =10240-required, margin_gap=gap/10240
- required>=10240 -> NO_INFORMATION_MARGIN (matrix NOT_APPLICABLE, not constructed), else gap<0 HEAVY, 0≤gap<512 MARGINAL, gap≥512 FEASIBLE
- 1M FEASIBLE (721≥512), 1p5M MARGINAL (193 in [0,512)), 2M NO_INFORMATION_MARGIN (11169 gap -929, required>=10240 -> NOT_APPLICABLE, not EVIDENCE_INCOMPLETE)

### Nested family (family_sha replaces H_bin_sha)

- cols 10240=10*1024 col=sym*10+bit, r0=160, Rs=r0+8k -> required, step+8 tail+7 for 9519 (160+8*1169=9512+7) and 10047 (160+8*1235=10040+7) achieved==requested true
- rank_{GF2}(H_r)==r via Python int basis incremental, nonzero, unique, prefix holds by construction for r≤10240; for required>10240 matrix NOT_APPLICABLE -> NO_INFORMATION_MARGIN (not rank_fail)
- family_sha 97ab00bc38ab5a70, shared prefix (renamed from H_bin_sha)

## Overall PARTIAL_SESSIONS_FEASIBLE (6 orthogonal counts, common_preserving replaced)

- feasible 1, marginal 1, no_information_margin 1, heavy 0, evidence_incomplete 0, model_not_stable 0 (6 orthogonal counts)
- overall V70_OVERALL_PARTIAL_SESSIONS_FEASIBLE (1 feasible +1 marginal +1 no_information_margin)

## 6-state per session (first-match reordered)

- V70_SOFT_JOINT_NO_INFORMATION_MARGIN (required>=10240, matrix NOT_APPLICABLE) > V70_EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE > FEASIBLE(≥5%) > MARGINAL(0-5%) > HEAVY
- 1M FEASIBLE -> v70_binary_soft_joint_code_design, 1p5M MARGINAL -> v70_binary_soft_joint_code_design, 2M NO_INFORMATION_MARGIN (11169) -> v70_new_representation_or_recollect, matrix NOT_APPLICABLE

## Consistency

- json/csv row-equal, CAL vs VAL |CE-CE_CV| <0.05, D≥0, pure<1e-12, rank verified, CAL选VAL确认一次, TEST隔离, src diff 0, decode_ 0 hits, V71_not_started.

## Implication

- 10-bit soft-joint factor preserves 1024-ary posterior (D≥0, pure brute 1e-12). Budget feasible for 1M/1p5M (family step+8 tail+7 achieved==requested) but 2M exceeds 10240 bits budget -> NO_INFORMATION_MARGIN, matrix NOT_APPLICABLE, not EVIDENCE. Overall PARTIAL_SESSIONS_FEASIBLE (6 orthogonal counts). Posterior/CE/D_bits not recomputed, matrix not decoded.

*ponytail: 10-bit shift/mask + logsumexp, family int bitset O(r^2) but incremental avoids full re-elimination*
