# Delta Spec: formal-ir-v60-composable-security-input-readiness — V60 composable 安全输入就绪度判定

## ADDED Requirements

### Requirement: V60 Frozen V57/V59 Disclosure as Input (Zero Change, DECODE_FORBIDDEN)

The change SHALL treat `V57/V59` accepted disclosure as frozen read-only input with zero modification:

| source | m1 | m2 | m_total | leak_total bits/block | leak_without_tag (=5*m_total) | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

with `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 bits/block L2-only` counted once in `leak_total =5*m_total+64` and `m_total=m1+m2`. The change SHALL verify `leak_total ==5*m_total+64` per source and `hmin_break_even_floor = leak_total/1024 = 6.9238/7.2637/7.5820 bits/symbol` and `10% margin 7.6931/8.0707/8.4245 bits/symbol` (`5% 7.2882/7.6460/7.9811`), SHALL NOT create a new `m1/m2` or decoder matrix, SHALL NOT change `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator`, and SHALL remain `DECODE_FORBIDDEN` (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`, no `run_01`). `data SHA 84d62779` and `pairing nearest legacy_v1` remain unchanged. Any `decode_*` or channel-estimator change or `V61` entry SHALL be forbidden.

### Requirement: V60 Phase A 10-Item Readiness Verdict (shadow/proxy vs composable, H_min lower-bound trace, No Self-Certification)

The change SHALL perform a per-item read-only investigation of the 10 authoritative `composable secret-key` inputs and SHALL persist `readiness_10items = [{item, symbol, meaning, unit, source(file:function:lines:expr or data_path:provenance), authority: composable|shadow|proxy|missing, readiness: ready|partial|missing|invalid, decoder_free?: yes/no/partial, minimal_new_measurement}]` and `formula_authority = [{file, function, lines, expr, unit, authority}]` with explicit units (`bits/block` vs `bits/symbol` vs `bits/pair` vs `dimensionless/count`) and whether `tag` is already included. The 10 items SHALL be exactly:

1. `phase-error / conjugate basis` (`e_ph`, conjugate statistics)
2. `n_PE` (PE sample size)
3. `visibility interval and source` (`[vis_low, vis_high]`, per-point/per-loss chain)
4. `eps_sec / eps_cor`
5. `finite-size authority` (`DeltaFK`, `n_eff`, `finite-key` coefficients)
6. `EV bound` (`epsilon_EC`, verification)
7. `auth leakage` (authentication bits)
8. `post-selection / accepted-frame` (`accepted_frame_fraction`, `post_sel` correction)
9. `composable theorem and assumptions` (`theorem_id: Renner/Niu/Tomamichel/...`, `assumptions[]`, `domain`)
10. `unit per-frame/block conversion` (`bits/block` vs `bits/symbol` vs `bits/pair`)

Candidate files/data: `tools/security_reports/_security_calibrated_common.py` (`chi_from_visibility`, `dary_mutual_info_proxy`, `calibrated_effective_sample_count`, `delta_fk_calibrated`), `tools/security_reports/build_actual_ir_finite_key_shadow.py` (`_build_shadow`), `tools/security_reports/round2_build_finite_key_audit_table.py`, `tools/security_reports/round2_build_actual_ir_finite_key_shadow.py`, `tools/security_reports/round3_build_proof_gap_matrix.py` (`per_point_franson_pe_chain: missing`, `conjugate_basis_stats: missing`, …), `comparison_bench/outputs_comparison/v57_*` + `v55_intake_20260828` (`data_inventory/registries/pairs`), `docs/SECURITY_MODEL.md` / `v59_secret_key_budget_authority.json`. The change SHALL mark `IAB_est / Shannon H(A|B) / MAP_acc / visibility shadow (global 0.95)` as **proxy, never `H_min^epsilon(A|E)` lower-bound** (→ `EVIDENCE_INVALID` if used as `H_min`). The change SHALL trace whether `H_min^epsilon(A|E)` is explicitly declared as a lower-bound with `eps` budget and theorem binding; if not declared, SHALL mark `h_min_source = "MISSING"` and `iab_h_map_vis_to_hmin = "no_declaration_proxy_missing"` and `hmin_lower_authority = missing → composable:null`. The change SHALL NOT invent `H_min / finite-key / composable` formulas or fabricate `eps_sec/eps_cor/visibility/phase-error` parameters.

### Requirement: V60 Phase B Readiness-First Four-State Verdict (Priority-Ordered, Mutually Exclusive, Only READY May Compute ell)

The overall verdict SHALL be `first-match`, priority-ordered, mutually exclusive, and SHALL persist `overall ∈ {V60_EVIDENCE_INVALID, V60_DATA_NOT_READY, V60_PARTIAL, V60_SECURITY_INPUTS_READY}` with `first_match` rationale:

```
if not unit_ok or leak !=5*m+64 or m_total != m1+m2 or IAB/H/MAP/vis_as_Hmin or not formula_self_consistent or tag_repeated or proxy_upgraded:
    overall = V60_EVIDENCE_INVALID  # highest: unit/tag/m/proxy coherence failure, includes H/IAB/MAP/vis as H_min
elif composable_theorem_missing or decisive_PE_missing:  # decisive: theorem not declared OR e_ph/conjugate/n_PE/vis authoritative missing
    overall = V60_DATA_NOT_READY  # decisive input missing, ell=null, need new theorem or new PE acquisition, stop
elif not all_decisive_ready or not finite_authority_ready or not eps_EV_auth_postSel_ready:
    overall = V60_PARTIAL  # some ready but insufficient for composable, already output readiness 10 + thresholds, ell=null
elif readiness_10items_all_critical_ready and composable_theorem_declared and hmin_lower_authority_composable and break_even_floor_done and minimal_action_table_done and unit_ok:
    overall = V60_SECURITY_INPUTS_READY  # only this state may compute ell =1024*hmin_lower - leak_IR - leak_other - finite
else:
    overall = V60_PARTIAL
```

- `V60_DATA_NOT_READY` triggers when **composable theorem missing** (no explicit composable theorem declaration with assumptions/domain) **OR** **decisive PE missing** (`phase-error/conjugate` without conjugate-basis measurement, `n_PE` without authoritative PE count, `visibility` without per-point chain). `V60_PARTIAL` means some items `ready` but not enough for composable. Only `V60_SECURITY_INPUTS_READY` may compute the key-budget equation `ell_s = 1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s` (`bits/block`, `hmin_lower` in `bits/symbol`).
- `shadow descriptive` interval SHALL NOT be upgraded to `composable-authority`; `missing` SHALL remain `null`, not `0` or `optimistic` value; non-`READY` SHALL keep `ell_* = null` and `hmin_lower = null` (never fill with shadow floor); `proxy_not_upgraded` and `missing→null` SHALL be asserted.
- The `first_match` priority SHALL be mechanically verified, and `mutual_exclusion` (exactly one verdict) SHALL be asserted; `only_READY_ell` (`(overall==READY) == (ell_not_null)`) SHALL be asserted.

### Requirement: V60 Thresholds per Source (floor / 5% / 10% margin, three-source independent, tag not repeated)

The change SHALL compute per source `s ∈ {1M,1p5M,2M}`:

```
optimistic_floor_s = leak_total_s / 1024  # 6.9238 / 7.2637 / 7.5820 bits/symbol (other=0 finite=0, MUST exist as anchor)
  margin thresholds: h_0% = optimistic_floor,
                     h_5% = (leak_IR_s + other + finite) / (1024 * 0.95)  # 7.2882 / 7.6460 / 7.9811 when other=finite=0
                     h_10% = (leak_IR_s + other + finite) / (1024 * 0.90) # 7.6931 / 8.0707 / 8.4245 when other=finite=0
  optimistic: other=0 finite=0 => h_5% = leak/(1024*0.95), h_10% = leak/(1024*0.90)
    1M: 6.9238 / 7.2882 / 7.6931, 1p5M: 7.2637/7.6460/8.0707, 2M: 7.5820/7.9811/8.4245

READ-ONLY ell (only when READY):
  ell_s = 1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s  # bits/block
  where hmin_lower_s is authoritative composable lower-bound (bits/symbol), leak_IR_s = leak_total_s already includes tag
  non-READY: ell_s = null, hmin_lower_s = null

shadow/proxy thresholds: (leak+other_shadow+finite_shadow)/1024 descriptive, proxy label, NOT upgraded to composable
log2 d =10 upper bound check: hmin <10, h_m <10
```

and SHALL report per source `optimistic_floor / margin_5% / margin_10%` with `hmin_lower_authority` and `ell_or_null`. Optimistic floor SHALL be given in every verdict as a descriptive gate; `READY` SHALL compare real `hmin_lower` against `floor` (`6.9238` for 1M) and `10% margin` (`7.6931` for 1M) to judge `ell>0`. Three sources SHALL be independent, not averaged. `leak_total_s ==5*m_total+64` and `h_floor_s *1024 == leak_total_s` SHALL be asserted as anchor; `bits/block = bits/symbol *1024` conversion SHALL be recorded.

### Requirement: V60 Stop Rule and Minimal New-Measurement Checklist (Precise, Prioritized, No Proxy Fill, No Decoder/V61)

When `composable_theorem_missing` OR `decisive_PE_missing` holds, the change SHALL stop at `V60_DATA_NOT_READY` / `V60_PARTIAL` (according to `PARTIAL` vs `DATA_NOT_READY` definition) and SHALL NOT fill `null` with `shadow` floor, SHALL NOT run `decode_*` or enter `V61` (`rg "decode_" 0 hits`), and SHALL output the minimal authority/readiness artifacts:

- `docs/research_cycles/V60P0/v60_composable_security_readiness.json` (`provenance {HEAD, origin, implementation_SHA, data_sha}`, `readiness_10items[10]`, `formula_authority[]`, `decomposition[per_source]`, `break_even{ floor, margin_5%, margin_10%, hmin_lower_authority, ell_or_null }`, `verdict {overall, first_match, readiness_summary, stop_reason}`),
- `docs/research_cycles/V60P0/V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md` (authority verdict, `readiness 10`-table, decomposition table three-source independent, `break_even` `floor/5%/10%` thresholds with `6.9238/7.2637/7.5820` anchors, `minimal new-measurement` action table, `overall` verdict and readiness closure),
- `docs/research_cycles/V60P0/v60_break_even_readiness.csv` (`source, leak_total, floor, margin_5%, margin_10%, hmin_lower_authority, hmin_lower, ell_or_null, gate`),
- `docs/research_cycles/V60P0/v60_minimal_new_measurement_checklist.csv` (`priority, item, missing_reason, minimal_new_measurement, required_sample_or_proof, acceptance_criterion, depends_on`), prioritized `composable theorem > decisive PE (phase-error/conjugate/n_PE) > visibility chain > finite authority > EV/auth/post_sel > units`, precisely listing newly required acquisition parameters without proxy fill.

`missing → null` SHALL be kept `null` (not `0`), `shadow` SHALL NOT be upgraded to `composable`, and `only_READY_ell` SHALL hold. The checklist SHALL be `ready/partial/missing` consistent with `readiness_10items`.

### Requirement: V60 DECODE_FORBIDDEN Guard and Delivery (No run_01, No src/V54-V59 Change, No V61, py_compile, Break-Even Anchors, Four Artifacts Pushed)

The change SHALL remain `PLAN_CANDIDATE / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ/decoder 90/1.0/poly37/m/estimator` and no change to `openspec/changes/formal-ir-v5[4-9]/` (`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`, and `openspec/changes/formal-ir-v60*/` only this change), no `.../v60_*/run_01` decoder execution creation, no automatic `V61` entry (`V61` still `PENDING`), `py_compile` PASS, and the following verifications SHALL pass: `GF32×5 tag-no-repeat` (7025/7375/7700 +64 =7089/7439/7764), `three-source independent` (no averaging), `break-even anchor h_floor*1024 == leak` and `h_m*1024*(1-margin) == leak+other+finite`, `missing→null` (`composable null` not `0`), `proxy not upgraded` (`shadow/proxy` distinct from `composable`), `four-state mutual exclusion first-match`, `readiness_10items ==10` (with `item` coverage exact), `H/IAB/MAP/vis != H_min`, `only_READY_ell`, `HEAD 910d921b` verified with `git fetch && HEAD==origin/formal-ir-mainline` before implementation. Script `scripts/v60_composable_security_input_readiness.py` SHALL be decoder-free (`numpy/pandas` only, optional `pyarrow`) and SHALL produce the four artifacts above. Push SHALL be ordinary (non-force) to `formal-ir-mainline` and SHALL remain `PLAN_CANDIDATE / DECODE_FORBIDDEN` awaiting independent `Pre-RESULT` review. After push, the change SHALL return `Plan SHA / implementation SHA / 10-item readiness / three-source thresholds / minimal checklist / final state`, without entering `V61`.

## MODIFIED Requirements

None. All prior `PLAN_CANDIDATE / DECODE_FORBIDDEN` and `AUTHORITY_INPUTS_ACTIONABLE` guards remain; `V60` adds composable-security-input readiness without modifying `V57/V59` terminal or entering `V61`.

## REMOVED Requirements

None.
