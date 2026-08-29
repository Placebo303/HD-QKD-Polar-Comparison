# V61 Security Measurement Specification — V61_SPEC_READY__V62_PENDING
Plan 1be38e39cd65469b97f395fdee15589510c5f07d HEAD 1be38e39 origin 1be38e39 data 84d62779 lifecycle PLAN_CANDIDATE / DECODE_FORBIDDEN branch formal-ir-mainline
Fetch HEAD==origin: True
## 1 V60 gap trace
V60_DATA_NOT_READY: composable theorem missing; decisive PE missing (e_ph/conjugate/n_PE authoritative missing); proxy not H_min; finite authority shadow only. Source tools/security_reports/round3_build_proof_gap_matrix.py:12-23 per_point_franson_pe_chain missing.
## 2 10-class field definition (symbol/meaning/unit/required_class/readiness/depends_on)
See v61_measurement_schema.json and v61_minimal_measurement_template.csv; readiness four states: required_core | required_if_theorem_applicable | not_applicable_with_theorem_reason | missing. visibility/decoy are conditional on theorem visibility_dependence/decoy_dependence bool; N/A with theorem line does not block V62_OPEN.
## 3 Unit / timestamp / session / source binding
unit_map: bits/block vs bits/symbol vs bits/pair vs count; per-block session_id/source_id/delay_used_ps/block_id/pairing=legacy_v1 nearest 200ps; data_inventory session/source/timestamp trace required; tag64 counted once in leak_IR.
## 4 Acceptance formula (R61-02)
ell_s = 1024 * hmin_lower_s - leak_IR_s - leak_other_s - finite_s  bits/block
leak_IR_s = leak_total_s = 5*m_total+64 already contains tag64, never double-count
leak_other_s = max(0, actual_verification_bits - 64) + leak_auth_s + PE_penalty_s + ...  bits/block
epsilon_EV/EC are probabilities, NOT bits unless theorem maps explicitly -> never added to leak_other/finite
Only V62_OPEN (required_core all ready + conditional deps ready + hmin composable + verification caliber ok) computes ell else null
Three-source independent, no averaging
## 5 Break-even thresholds (tag already in leak, other=0 finite=0 placeholders)
| source | leak_total | floor leak/1024 | 5% leak/(1024*0.95) | 10% leak/(1024*0.90) |
|---|---|---|---|---|
| 1M | 7089 | 6.9238 | 7.2882 | 7.6931 |
| 1p5M | 7439 | 7.2637 | 7.6460 | 8.0707 |
| 2M | 7764 | 7.5820 | 7.9811 | 8.4245 |
log2 d =10 upper bound: all floors <10 pass; h*1024==leak/(1-margin) anchor verified; GF32 5bits leak_without_tag=5*m_total (7025/7375/7700)+64 verified; three-source independent not averaged
## 6 V62 gate (R61-01 dependency-aware, R61-02 caliber)
first-match: V61_SPEC_INVALID > V61_SPEC_READY__V62_PENDING(missing theorem or decisive core PE) > V61_SPEC_READY__V62_OPEN(required_core all ready + conditional ready + hmin composable).
Conditional visibility/decoy with not_applicable_with_theorem_reason (theorem declares not applicable with file:line:expr) SHALL NOT block V62_OPEN.
R61-02 boundaries: tag64-only actual 64 -> extra 0; extra 128 -> extra 64; epsilon probability alone -> not in leak_other/finite.
proxy IAB/H/MAP/vis as H_min -> SPEC_INVALID; missing->null not 0; only READY ell not null.
## 7 Minimal new measurement checklist priority
1 composable theorem > 2 decisive core PE (e_ph/conjugate/n_PE) > 3 visibility[conditional]/decoy[conditional] > 4 eps/finite > 5 EV/auth/post_sel > 6 units/binding > 7 acceptance inputs
See v61_minimal_new_measurement_checklist.csv for depends_on per item.
## 8 Overall verdict
overall=V61_SPEC_READY__V62_PENDING first_match=V61_SPEC_READY__V62_PENDING: theorem missing or decisive core PE missing (R61-01); ell=null for all sources; break-even floors above remain anchors only
V61 pushes as PLAN_CANDIDATE / DECODE_FORBIDDEN; V62 remains PENDING until new data closes required_core + conditional deps and provides composable hmin_lower; verification caliber max(0,actual-64) and epsilon-not-bits enforced
Frozen: V57/V59 m1/m2/m_total/leak 1405/1475/1540 7089/7439/7764 n1024 GF32 poly37 tag64 once; H1 16x1024 Lane C H_inc1/2 Delta8+8 90/1.0 estimator frozen; no decode, no V55 rerun, no LDPC change