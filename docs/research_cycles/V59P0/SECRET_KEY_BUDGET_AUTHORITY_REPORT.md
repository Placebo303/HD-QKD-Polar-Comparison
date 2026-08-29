# V59 Secret Key Budget Authority — AUTHORITY_INPUTS_ACTIONABLE
Plan 8a83a98dcff2eb304402410f82c9c8274895966f HEAD 8a83a98d origin 8a83a98d data 84d62779 lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN
## Formula Authority
- tools/security_reports/_security_calibrated_common.py:chi_from_visibility 92-99 `h2((1-vis)/2)+e*log2(d-1)` unit bits/pair authority shadow
- tools/security_reports/_security_calibrated_common.py:dary_mutual_info_proxy 102-117 `log2 d+(1-e)log(1-e)+e log(e/(d-1))` unit bits/pair authority proxy
- tools/security_reports/_security_calibrated_common.py:calibrated_effective_sample_count 246-284 `n_eff=n_pairs*layer_frac*clean_frac` unit count authority shadow
- tools/security_reports/_security_calibrated_common.py:delta_fk_calibrated 288-297 `4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` unit bits/pair authority shadow
- tools/security_reports/build_actual_ir_finite_key_shadow.py:_build_shadow 27-88 `PIE_secure=IAB-leak-chi-DeltaFK (surrogate_from_best_hard_pie_gap)` unit bits/pair authority shadow
- tools/security_reports/build_actual_ir_finite_key_shadow.py:_summary_lines 116 `not full niu_2016 composable proof` unit tag authority shadow_proxy_only
- tools/security_reports/round2_build_finite_key_audit_table.py:main 75-122 `leak_EC_actual_bits=total_leak/n_pairs else surrogate; DeltaFK(n_eff); post_sel=accepted_frame_fraction` unit bits/pair authority shadow
- tools/security_reports/round2_build_actual_ir_finite_key_shadow.py:main 31-48 `PIE_secure_actual_ir=IAB-leak-chi-DeltaFK-post_sel; strict_zhong_like_actual_ir_finite_key_calibrated` unit bits/pair authority shadow
- tools/security_reports/round3_build_proof_gap_matrix.py:main 12-23 `decoy_state/conjugate_basis/composable_constants missing` unit - authority missing
PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel => shadow_proxy_only (not full niu_2016 composable proof)
IAB - chi_E => H_min^epsilon: no_declaration_proxy_missing; H/IAB/MAP as H_min forbidden
## Variable Table (>=11)
- H_min^epsilon(A|E): smooth min-entropy per symbol lower bound unit bits/symbol auth missing df no -> PE sample estimation with n_PE and e_ph chain
- e_ph: phase-error rate unit - auth missing df no -> conjugate-basis / decoy-state measurement
- vis: Franson visibility interval unit - auth shadow df partial -> per-point measured vis calibrated interval [0.93,0.97]
- n_PE: PE sample size unit count auth shadow df partial -> PE acquisition n_PE with sifting stats
- eps_sec: secrecy epsilon unit - auth shadow df yes -> protocol fixed 1e-10
- eps_cor: correctness epsilon unit - auth shadow df partial -> verify epsilon_EC_bound via transcript
- DeltaFK: finite-size penalty unit bits/pair auth shadow df yes -> needs n_eff actual
- EV: error-verification tag bits unit bits/block auth shadow df partial -> verification transcript
- post_sel: post-selection fraction unit bits/pair auth shadow df yes -> rigorous accepted/rejected frame accounting
- auth: authentication bits unit bits/block auth missing df no -> auth bits measurement
- IAB: Alice-Bob mutual info proxy unit bits/pair auth proxy df yes -> MUST NOT be used as H_min (weak_proxy)
- leak_IR: IR leakage bits per block unit bits/block auth frozen df yes -> already frozen, no new
## Decomposition (tag not repeated, GF32 5 bits)
- 1M: without_tag 7025 +64 = 7089 (m_total verified) n=1024 log2q=5
- 1p5M: without_tag 7375 +64 = 7439 (m_total verified) n=1024 log2q=5
- 2M: without_tag 7700 +64 = 7764 (m_total verified) n=1024 log2q=5
## Break-even thresholds bits/symbol (per source, not averaged)
- 1M: floor 6.9238 /5% 7.2882 /10% 7.6931 shadow [6.9238,6.9238] composable null log2d10_pass
- 1p5M: floor 7.2637 /5% 7.646 /10% 8.0707 shadow [7.2637,7.2637] composable null log2d10_pass
- 2M: floor 7.582 /5% 7.9811 /10% 8.4245 shadow [7.582,7.582] composable null log2d10_pass
## Minimal action table (priority)
1. PE acquisition: n_PE with conjugate/decoy stats for H_min/e_ph  2. per-point vis calibration 3. rigorous frame accounting for post_sel 4. verification transcript for EV/eps_cor 5. auth bits
## Overall AUTHORITY_INPUTS_ACTIONABLE — first-match EVIDENCE_INVALID > NO_MARGIN > POSSIBLE > ACTIONABLE, valid completion even though composable null; only H_min missing insufficient without table+thresholds
Checks: tag_no_repeat pass, leak=5m+64 pass, h_floor*1024==leak pass, missing->null, proxy not upgraded, mutual_exclusion, decoder-free