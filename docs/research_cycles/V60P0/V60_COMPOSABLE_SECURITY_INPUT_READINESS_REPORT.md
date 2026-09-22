# V60 Composable Security Input Readiness — V60_DATA_NOT_READY
Plan b4d045a14ce49772e622aebdedb3ed72475bdfbc HEAD b414eab5 origin b414eab5 data 84d62779 lifecycle PLAN_CANDIDATE / DECODE_FORBIDDEN
Fetch HEAD==origin: True (blocking gate per A1; warn if false)
## Formula Authority (file:function:lines:expr unit authority)
- tools/security_reports/_security_calibrated_common.py:chi_from_visibility 92-99 `h2((1-vis)/2)+e*log2(d-1)` unit bits/pair authority shadow
- tools/security_reports/_security_calibrated_common.py:dary_mutual_info_proxy 102-117 `log2 d+(1-e)log(1-e)+e log(e/(d-1))` unit bits/pair authority proxy
- tools/security_reports/_security_calibrated_common.py:calibrated_effective_sample_count 246-284 `n_eff=n_pairs*layer_frac*clean_frac` unit count authority shadow
- tools/security_reports/_security_calibrated_common.py:delta_fk_calibrated 288-297 `4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` unit bits/pair authority shadow
- tools/security_reports/build_actual_ir_finite_key_shadow.py:_build_shadow 27-88 `PIE_secure=IAB-leak-chi-DeltaFK (surrogate_from_best_hard_pie_gap)` unit bits/pair authority shadow
- tools/security_reports/build_actual_ir_finite_key_shadow.py:_summary_lines 116 `not full niu_2016 composable proof` unit tag authority shadow_proxy_only
- tools/security_reports/round2_build_finite_key_audit_table.py:main 75-122 `leak_EC_actual_bits=total_leak/n_pairs else surrogate; DeltaFK(n_eff); post_sel=accepted_frame_fraction` unit bits/pair authority shadow
- tools/security_reports/round2_build_actual_ir_finite_key_shadow.py:main 31-48 `PIE_secure_actual_ir=IAB-leak-chi-DeltaFK-post_sel; strict_zhong_like_actual_ir_finite_key_calibrated` unit bits/pair authority shadow
- tools/security_reports/round3_build_proof_gap_matrix.py:main 12-23 `per_point_franson_pe_chain missing; conjugate_basis_stats missing; decoy_state_PE missing; protocol_specific_composable_constants missing` unit - authority missing
PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel => shadow_proxy_only (not full niu_2016 composable proof; strict_zhong_like_calibrated)
IAB/H/MAP/vis => H_min: no_declaration_proxy_missing; forbidden to use as H_min
## Readiness 10 Items (item/symbol/meaning/unit/source/authority/readiness/decoder_free/minimal_new_measurement)
- phase-error / conjugate | e_ph | phase-error rate / conjugate basis statistics | unit - | src tools/security_reports/round3_build_proof_gap_matrix.py:main:12-23 expr=conjugate_basis_stats missing / per_point_franson_pe_chain missing | auth missing | readiness missing | df no -> new conjugate-basis / decoy-state e_ph estimation with n_PE chain
- n_PE | n_PE | PE sample size (authoritative PE count) | unit count | src tools/security_reports/_security_calibrated_common.py:calibrated_effective_sample_count:246-284 expr=n_eff=n_pairs*layer_frac*clean_frac data_path=comparison_bench/outputs_comparison/v57_* data_inventory.json | auth shadow | readiness partial | df partial -> new PE acquisition with authoritative n_PE and sifting stats
- visibility interval and source | [vis_low, vis_high] | Franson visibility interval per point/per loss with source chain | unit - | src tools/security_reports/_security_calibrated_common.py:chi_from_visibility:92-99 expr=h2((1-vis)/2)+e*log2(d-1) vis_src=global 0.95 shadow proxy | auth shadow | readiness partial | df partial -> per-point / per-loss measured vis interval [vis_low, vis_high] with provenance
- eps_sec / eps_cor | eps_sec, eps_cor | secrecy / correctness epsilon | unit - | src tools/security_reports/build_actual_ir_finite_key_shadow.py:_build_shadow eps_sec=1e-10 eps_cor=1e-10 | auth shadow | readiness partial | df yes -> protocol-fixed eps_sec/eps_cor with composable coefficient binding to DeltaFK
- finite-size authority | DeltaFK, n_eff | finite-size penalty and effective sample count | unit bits/pair | src tools/security_reports/_security_calibrated_common.py:delta_fk_calibrated:288-297 expr=4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff | auth shadow | readiness partial | df yes -> n_eff actual measurement + composable finite-key coefficient authority
- EV bound | epsilon_EC, verification_bits | error-verification transcript bound | unit bits/block | src tools/security_reports/round2_build_finite_key_audit_table.py:main:75-122 verification_bits / epsilon_EC_bound | auth shadow | readiness partial | df partial -> verification transcript + epsilon_EC bound proof
- auth leakage | leak_auth | authentication bits leakage | unit bits/block | src MISSING tools/security_reports/round3_build_proof_gap_matrix.py:protocol_specific_composable_constants missing | auth missing | readiness missing | df no -> authentication bits observation and accounting with composable theorem
- post-selection / accepted-frame | accepted_frame_fraction | post-selection accepted-frame fraction with composable correction | unit - / bits/pair | src tools/security_reports/round2_build_finite_key_audit_table.py:main:75-122 accepted_frame_fraction | auth shadow | readiness partial | df yes -> rigorous accepted/rejected frame accounting + post_sel composable correction proof
- composable theorem and assumptions | theorem_id, assumptions[] | composable theorem binding with assumptions and domain | unit - | src MISSING tools/security_reports/round3_build_proof_gap_matrix.py: no Renner/Niu/Tomamichel declaration; docs/SECURITY_MODEL.md no composable theorem_id | auth missing | readiness missing | df no -> declare theorem_id + assumptions {collective/coherent, PE model, finite-key, auth, EV} + domain validation
- unit per-frame/block conversion | unit_map | unit conversion bits/block vs bits/symbol vs bits/pair | unit bits/block vs bits/symbol vs bits/pair | src tools/security_reports/_security_calibrated_common.py:chi_from_visibility+delta_fk_calibrated units bits/pair; leak_IR bits/block tag included | auth shadow | readiness partial | df yes -> authoritative unit declaration table and conversion proof
## Decomposition per source (tag not repeated, GF32 5 bits, three-source independent)
- 1M: leak_without_tag 7025 + tag64 64 = leak_total 7089 n=1024 log2q=5 leak_other null finite null
- 1p5M: leak_without_tag 7375 + tag64 64 = leak_total 7439 n=1024 log2q=5 leak_other null finite null
- 2M: leak_without_tag 7700 + tag64 64 = leak_total 7764 n=1024 log2q=5 leak_other null finite null
## Break-even thresholds bits/symbol (per source, not averaged; optimistic floor other=0 finite=0)
- 1M: floor 6.9238 /5% 7.2882 /10% 7.6931 hmin_authority null ell null gate log2d10_pass (true 6.9229/7.2872/7.6921)
- 1p5M: floor 7.2637 /5% 7.646 /10% 8.0707 hmin_authority null ell null gate log2d10_pass (true 7.2646/7.647/8.0718)
- 2M: floor 7.582 /5% 7.9811 /10% 8.4245 hmin_authority null ell null gate log2d10_pass (true 7.582/7.9811/8.4245)
Threshold formula: h_m = (leak+other+finite)/(1024*(1-margin)); floor=leak/1024; 5%=floor/0.95; 10%=floor/0.90
Units: hmin bits/symbol; leak/ell bits/block; chi_E/DeltaFK bits/pair convert *1024 or *n_eff
## Minimal New-Measurement Checklist (priority composable theorem > decisive PE > vis > finite > EV/auth/post_sel > units)
1. composable theorem and assumptions: declare theorem_id (Renner/Niu/Tomamichel) + assumptions {collective/coherent, PE model, finite-key, auth, EV} + domain | req theorem binding proof + assumption validation | accept theorem_id with file:lines expr | depends none
2. phase-error / conjugate: conjugate-basis / decoy-state e_ph measurement with sifting | req n_PE coherent with e_ph; conjugate stats file:lines | accept e_ph with confidence interval and theorem linkage | depends composable theorem
3. n_PE: PE acquisition n_PE authoritative count | req n_PE file:lines with provenance | accept n_PE with PE model binding | depends phase-error/conjugate
4. visibility interval and source: per-point / per-loss vis interval [vis_low, vis_high] with calibration | req vis interval with source chain file:lines | accept vis interval with composable chi_E linkage | depends n_PE
5. finite-size authority: n_eff actual count + DeltaFK composable coefficient authority | req finite-key theorem constants with n_eff | accept DeltaFK bits/pair with eps_sec/eps_cor binding | depends n_PE
6. EV bound: verification transcript + epsilon_EC bound | req transcript file:lines with tag bits | accept EV bound with auth separation | depends finite-size
7. auth leakage: auth bits observation and accounting | req auth bits file:lines | accept auth leakage bits/block with theorem | depends EV
8. post-selection / accepted-frame: rigorous accepted/rejected frame accounting + post_sel correction proof | req post_sel file:lines with composable correction | accept post_sel with finite-key linkage | depends finite-size
9. eps_sec / eps_cor: protocol-fixed eps_sec/eps_cor declaration | req eps values with DeltaFK formula binding | accept eps with file:lines and coefficient match | depends finite-size
10. unit per-frame/block conversion: authoritative unit declaration bits/block vs bits/symbol vs bits/pair | req unit table file:lines | accept unit_table with conversion proof | depends none
## Overall V60_DATA_NOT_READY — first-match DATA_NOT_READY: composable_theorem_missing or decisive_PE_missing (e_ph/conjugate/n_PE/vis authoritative missing)
Priority: V60_EVIDENCE_INVALID > V60_DATA_NOT_READY(decisive PE or theorem) > V60_PARTIAL > V60_SECURITY_INPUTS_READY; mutual exclusion true; proxy not upgraded; missing->null
Only V60_SECURITY_INPUTS_READY may compute ell=1024*hmin_lower - leak_IR - leak_other - finite (bits/block); else ell=null with floor/5%/10% anchors only; no decoder/V61
Checks: tag_no_repeat, leak=5m+64, GF32 5bits, H/IAB/MAP/vis!=H_min, no cross-source average, log2d10, only_READY_ell, rg decode_ 0, git diff src 0
Frozen: V57/V59 m1/m2/m_total/leak 1405/1475/1540 7089/7439/7764 n1024 GF32 poly37 tag64 once; H1 16x1024 Lane C H_inc1/2 Delta8+8 decoder 90/1.0 estimator frozen