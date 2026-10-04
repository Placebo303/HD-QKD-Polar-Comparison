# Delta Spec: formal-ir-v59-security-budget-authority-closure — V59 decoder-free 安全预算权威闭合

## ADDED Requirements

### Requirement: V59 Frozen V57/V58 Disclosure as Budget Input (Zero Change)

The change SHALL treat V57/V58 accepted disclosure as frozen read-only input with zero modification:

| source | m1 | m2 | m_total | leak_total bits/block | leak_without_tag (=5*m_total) | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

with `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 bits/block L2-only` counted once in `leak_total =5*m_total+64` and `m_total=m1+m2`. The change SHALL verify `leak_total ==5*m_total+64` per source and `hmin_break_even_floor = leak_total/1024 = 6.9238/7.2637/7.5820 bits/symbol`, SHALL NOT create a new `m1/m2` or decoder matrix, and SHALL remain decoder-free (`rg "decode_" 0 hits`). `data SHA 84d62779` and `pairing nearest legacy_v1` remain unchanged. Any `decode_*` or channel-estimator change SHALL be forbidden.

### Requirement: V59 Phase A Read-Only Per-Function Authority Verdict (shadow/proxy vs composable, IAB-chi追踪, No Self-Certification)

The change SHALL perform a per-function read-only investigation of the repository's authoritative `secret-key length / PA / finite-key` implementations and SHALL persist `formula_authority = [{file, function, lines, expr, unit, authority: composable|shadow|proxy|missing}]` with explicit units (`bits/block` vs `bits/symbol` vs `bits/pair`) and whether `tag` is already included. Candidate files: `tools/security_reports/_security_calibrated_common.py` (`chi_from_visibility`, `dary_mutual_info_proxy`, `calibrated_effective_sample_count`, `delta_fk_calibrated`), `tools/security_reports/build_actual_ir_finite_key_shadow.py` (`_build_shadow`), `tools/security_reports/round2_build_finite_key_audit_table.py`, `tools/security_reports/round2_build_actual_ir_finite_key_shadow.py`. The change SHALL verdict `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` as **shadow/proxy only** (grounded in file literals such as `not full niu_2016 composable proof` / `strict_zhong_like_calibrated` / `proof_gap_matrix missing`) and SHALL NOT self-certify it as composable. The change SHALL trace whether `IAB - chi_E` is explicitly declared equivalent to `H_min^epsilon(A|E)`; if not declared, SHALL mark `h_min_source = "MISSING"` and `iab_chi_to_hmin = "no_declaration_proxy_missing"`. Treating `H(A|B)` / `IAB_est` / `MAP` as `H_min` SHALL be forbidden (→ `EVIDENCE_INVALID`). The change SHALL NOT invent `H_min / finite-key / composable` formulas or fabricate `eps_sec/eps_cor/visibility` parameters.

### Requirement: V59 Phase B Unified Budget and Exact Variable Table (≥11 items, unit: bits/block, No H/IAB as H_min, No Cross-Source Averaging)

The change SHALL freeze the unified budget `ell_s = 1024 * hmin_lower_s - leak_IR_s - leak_other_s - finite_s` where `leak_IR_s = leak_total_s (=5*m_total+64)` already includes `tag`, `leak_other_s = PE_penalty + EV + auth + ...`, `finite_s = DeltaFK_calibrated + ...`, and SHALL establish exact variable tables with columns `symbol / meaning / unit / source(file:function:lines:expr) / authority(composable/shadow/proxy/missing) / decoder_free?(yes/no/partial) / minimal_new_measurement`. The table SHALL contain ≥11 items at least covering **smooth min-entropy `H_min^epsilon(A|E)`, phase-error `e_ph`, visibility interval `[vis_low, vis_high]`, PE sample size `n_PE`, `eps_sec`, `eps_cor`, finite-size `DeltaFK`, EV `epsilon_EC`, post-selection `accepted_frame_fraction`, auth bits**, plus `IAB`/`H(A|B)` (`proxy`) and `leak_IR` (`frozen`). `missing` items SHALL yield `composable:null`. The change SHALL verify `leak_without_tag =5*(m1+m2)` (`7025/7375/7700`) and `leak_total = leak_without_tag +64` (`7089/7439/7764`), `GF32 5 bits/symbol` conversion `bits/block = bits/symbol *1024`, SHALL NOT treat `H(A|B)`/`IAB_est`/`MAP` as `H_min^epsilon(A|E)` (if borrowed, labeled `proxy/missing` and `composable:null`), and SHALL NOT average across sources — `hmin_break_even` SHALL be computed and reported per source independently.

### Requirement: V59 Phase C Three-Grade Break-Even Thresholds per Source (optimistic floor / shadow descriptive / composable null, 0/5/10% margin)

The change SHALL compute per source `s ∈ {1M,1p5M,2M}`:

```
optimistic_floor_s = leak_total_s / 1024  # 6.9238 / 7.2637 / 7.5820 bits/symbol (other=0 finite=0, MUST exist)
  margin thresholds: h_0% = optimistic_floor,
                     h_5% = (leak_IR_s + other + finite) / (1024 * 0.95),
                     h_10% = (leak_IR_s + other + finite) / (1024 * 0.90)
  optimistic: other=0 finite=0 => h_5% = leak/(1024*0.95), h_10% = leak/(1024*0.90)
    1M: 6.9238 / 7.2882 / 7.6931, 1p5M: 7.2637/7.6460/8.0707, 2M: 7.5820/7.9811/8.4245

shadow_low/high_s = (leak_IR_s + other_shadow_[low/high]_s + finite_shadow_[low/high]_s) / 1024  # descriptive, proxy, NOT upgraded to composable
composable_low/high_s = null  # JSON null if decisive composable input (H_min/e_ph/composable_constants) missing, NOT 0
log2 d =10 upper bound check: hmin <10
```

and SHALL report per source `optimistic_floor / shadow [low,high] / composable [null,null]` with `0/5/10%` margin rows. Optimistic floor SHALL be given even if incomplete; shadow SHALL be propagated only from in-repo calibrated shadow parameters with `proxy` label; composable SHALL be explicit `null` (not `0`) when missing and SHALL NOT be upgraded from shadow. Three sources SHALL be independent, not averaged. `leak_total_s ==5*m_total+64` and `h_floor_s *1024 == leak_total_s` SHALL be asserted as anchor.

### Requirement: V59 Phase D First-Match Four-State Verdict (Priority-Ordered, Mutually Exclusive, proxy Not Upgraded, Missing→null)

The overall verdict SHALL be first-match, priority-ordered, mutually exclusive:

```
if not unit_ok or leak !=5*m+64 or m_total != m1+m2 or H_or_IAB_as_Hmin or not formula_self_consistent or tag_repeated or proxy_upgraded:
    overall = EVIDENCE_INVALID  # highest: unit/tag/m/proxy coherence failure
elif any(ell_conservative_s <= 0 for s in sources):  # optimistic floor already minimal penalty, any ≤0 => no positive margin
    overall = AUTHORITY_CLOSED_NO_POSITIVE_MARGIN  # any conservative ≤0 immediate stoploss, need new H_min or lower leak
elif all(ell_conservative_s > 0 for s in sources) and composable_is_null:
    # optimistic floor >0 but composable null, only proxy descriptive positive
    if not variable_table_ge11 or not break_even_has_floor:
        overall = EVIDENCE_INVALID  # missing minimal list/threshold not allowed as ACTIONABLE
    else:
        overall = AUTHORITY_CLOSED_POSITIVE_POSSIBLE  # three sources >0 but composable null, need minimal action list to become ACTIONABLE
elif variable_table_ge11 and break_even_has_floor and break_even_has_shadow and composable_is_null_explicit and minimal_action_table_done:
    overall = AUTHORITY_INPUTS_ACTIONABLE  # already output minimal list ≥11 + per-source break_even thresholds, valid completion even if composable null
```

- Only `AUTHORITY_INPUTS_ACTIONABLE` SHALL be considered **valid completion** (it requires `variable_table ≥11` + `per_source optimistic_floor/shadow/composable(null) with 0/5/10% thresholds` + `minimal_new_measurement action table`); **merely stating `H_min` missing is insufficient** for `ACTIONABLE`.
- `shadow descriptive` interval SHALL NOT be upgraded to `composable-authority`; `missing` SHALL remain `null`, not `0` or optimistic value; `EVIDENCE_INVALID` outranks all.
- The `first_match` priority SHALL be mechanically verified, and `mutual_exclusion` (exactly one verdict) SHALL be asserted.

### Requirement: V59 Decoder-Forbidden Guard and Delivery (No run_01, No src/V54-V58 Change, No V60, py_compile, Break-Even Anchors)

The change SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ/decoder 90/1.0/poly37/m` and no change to `openspec/changes/formal-ir-v5[4-8]/` (`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`), no `.../v59_*/run_01` decoder execution creation, no automatic `V60` entry (`V60` still `PENDING`), `py_compile` PASS, and the following verifications SHALL pass: `GF32×5 tag-no-repeat` (7025/7375/7700 +64 =7089/7439/7764), `three-source independent` (no averaging), `break-even anchor h_floor*1024 == leak`, `missing→null` (composable `null` not `0`), `proxy not upgraded` (`shadow` distinct from `composable`), `four-state mutual exclusion`, `variable_table≥11`, `log2 d=10` upper bound, `HEAD 2340257d` verified with `git fetch && HEAD==origin/formal-ir-mainline` before implementation. Script `scripts/v59_security_budget_authority_closure.py` SHALL be decoder-free (`numpy/pandas` only, optional `pyarrow`) and SHALL produce `docs/research_cycles/V59P0/SECRET_KEY_BUDGET_AUTHORITY_REPORT.md`, `v59_secret_key_budget_authority.json`, and compact CSV `v59_break_even.csv` (`source, leak_total, optimistic_floor, optimistic_5%, optimistic_10%, shadow_low, shadow_high, composable_low, composable_high, gate`). Push SHALL be ordinary (non-force) to `formal-ir-mainline` and SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` awaiting independent `Pre-RESULT` review. After push, the change SHALL return `Plan SHA / implementation SHA / authority verdict (PIE_secure shadow/proxy only) / three-source thresholds / minimal action table / final state`, without entering `V60`.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain; V59 adds decoder-free authority closure without modifying V57/V58 terminal.

## REMOVED Requirements

None.
