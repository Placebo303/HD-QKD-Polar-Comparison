# Delta Spec: formal-ir-v61-security-measurement-specification — V61 最小安全测量采集规范

## ADDED Requirements

### Requirement: V61 Frozen V57/V60 Disclosure as Input (Zero Change, DECODE_FORBIDDEN)

The change SHALL treat `V57/V60` accepted disclosure as frozen read-only input with zero modification:

| source | m1 | m2 | m_total | leak_total bits/block | leak_without_tag (=5*m_total) | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

with `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 bits/block L2-only` counted once in `leak_total =5*m_total+64` and `m_total=m1+m2`. The change SHALL verify `leak_total ==5*m_total+64` per source and `hmin_break_even_floor = leak_total/1024 = 6.9238/7.2637/7.5820 bits/symbol` and `10% margin 7.6931/8.0707/8.4245 bits/symbol` (`5% 7.2882/7.6460/7.9811`), SHALL NOT create a new `m1/m2` or decoder matrix, SHALL NOT change `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator / LDPC family`, SHALL NOT rerun `V55`, SHALL NOT run any `decode_*`, and SHALL remain `DECODE_FORBIDDEN` (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`, no `run_01`, no `V55` rerun). `data SHA 84d62779` and `pairing nearest legacy_v1` remain unchanged for frozen disclosure; new measurement data SHALL use a new `data_sha` bound via `session/source/timestamp` (see unit binding). Any `decode_*` or `LDPC` change or `V55` rerun or `V62` numeric entry without new data SHALL be forbidden.

### Requirement: V61 Minimal Security Measurement Acquisition Schema (10 Items, No Proxy Fill, No Old-Data Fake PE)

The change SHALL define and persist a machine-checkable minimal acquisition schema covering exactly the 10 classes of "what new experiment must record", with per-field `symbol / meaning / unit / required / source(file:line:expr or data_path:provenance) / authority: composable|shadow|proxy|missing / readiness: ready|partial|missing|invalid / minimal_new_measurement`. The schema SHALL be `docs/research_cycles/V61P0/v61_measurement_schema.json` (`JSON Schema draft-07`) + template `docs/research_cycles/V61P0/v61_minimal_measurement_template.csv` (columns `source, field, symbol, meaning, unit, required, authority, example_value, source_trace, readiness`), requiring at least:

1. `protocol / security theorem and applicable assumptions` (`theorem_id: Renner/Niu 2016/Tomamichel/Lim/...`, `assumptions[]: {collective/coherent, PE model, finite-key, auth, EV, post-selection}`, `domain`, `source` binding to theorem statement line/expr)
2. `conjugate-basis or phase-error observations` (`e_ph / e_p`, `conjugate_basis_stats: {n_X, n_Z, ...}`, `decoy_chain` if applicable, estimation method and uncertainty chain)
3. `n_PE and sampling rule` (`n_PE` authoritative count, `p_Z/p_X`, `sampling_rule: random_without_replacement/...`, `seed_or_counter`, `PE frame marking`)
4. `visibility per-source interval` (`[vis_low, vis_high]` per source `1M/1p5M/2M` per `loss/session`, `vis_source`, `cal_chain`; `global vis=0.95` is `shadow proxy` only)
5. `eps_sec / eps_cor allocation` (`eps_sec, eps_cor, eps_PE, eps_PA, eps_EC/E_V` decomposition, consistency with `DeltaFK/EV/auth` `eps` budgets)
6. `verification / authentication leakage` (`leak_verif: epsilon_EC + tag/verification_bits transcript`, `leak_auth` auth bits, `tag_included: bool`, `bits/block`, no double-count of `tag64`)
7. `finite-size correction` (`DeltaFK_formula: 4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` or authoritative variant, `n_eff`, `coeff_authority`, `unit: bits/pair → bits/block`)
8. `post-selection and effective frame counting` (`accepted_frame_fraction`, `n_block`, `N_pairs→frames→blocks` mapping, `post_sel_penalty bits/block`, rejection rule)
9. `unit / timestamp / session / source binding` (`unit_map: bits/block vs bits/symbol vs bits/pair vs count`, `session_id, source_id, delay_used_ps, block_id, pairing=legacy_v1 nearest 200ps` 4-tuple per block)
10. `acceptance-formula inputs` (`hmin_lower_bits_per_symbol: number|null` composable lower-bound, `leak_other_bits_per_block`, `finite_bits_per_block`, `ell_formula: ell=1024*hmin_lower - leak_IR - leak_other - finite`)

Candidate trace files (read-only, not to modify): `tools/security_reports/_security_calibrated_common.py` (`chi_from_visibility`, `dary_mutual_info_proxy`, `calibrated_effective_sample_count`, `delta_fk_calibrated`), `tools/security_reports/build_actual_ir_finite_key_shadow.py`, `tools/security_reports/round3_build_proof_gap_matrix.py` (`per_point_franson_pe_chain: missing / conjugate_basis_stats: missing`), `comparison_bench/outputs_comparison/v57_*` + `v55_intake_20260828` (`data_inventory/registry/pairs`), `docs/SECURITY_MODEL.md` / `v60_composable_security_readiness.json`. The change SHALL mark `IAB_est / Shannon H(A|B) / MAP_acc / visibility shadow (global 0.95)` as **proxy, never `H_min^epsilon(A|E)` lower-bound** (→ `SPEC_INVALID` / `EVIDENCE_INVALID` if used as `H_min`), SHALL mark `H_min^epsilon(A|E)` not explicitly declared as lower-bound with `eps` budget and theorem binding as `h_min_source = "MISSING"` and `hmin_lower_authority = missing → composable:null`, and SHALL forbid fabricating `e_ph / n_PE / conjugate` from old data (`old V55 data recomputed without new physical observation → EVIDENCE_INVALID`). The change SHALL NOT invent `H_min / finite-key / composable` formulas.

### Requirement: V61 Decoder-Free Acceptance Formula and Three-Source 10% H_min Gate

The change SHALL freeze the decoder-free acceptance formula and per-source thresholds:

```
optimistic_floor_s = leak_total_s / 1024  # 6.9238 / 7.2637 / 7.5820 bits/symbol (other=0 finite=0, MUST exist as anchor)
  margin thresholds: h_0% = optimistic_floor,
                     h_5% = (leak_IR_s + other + finite) / (1024 * 0.95)  # 7.2882 / 7.6460 / 7.9811 when other=finite=0
                     h_10% = (leak_IR_s + other + finite) / (1024 * 0.90) # 7.6931 / 8.0707 / 8.4245 when other=finite=0
  optimistic: other=0 finite=0 => h_5% = leak/(1024*0.95), h_10% = leak/(1024*0.90)
    1M: 6.9238 / 7.2882 / 7.6931, 1p5M: 7.2637/7.6460/8.0707, 2M: 7.5820/7.9811/8.4245

NEW-DATA ONLY ell (only when V61_NEW_DATA_READY):
  ell_s = 1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s  # bits/block
  where hmin_lower_s is authoritative composable lower-bound (bits/symbol), leak_IR_s = leak_total_s already includes tag
  non-READY: ell_s = null, hmin_lower_s = null

shadow/proxy thresholds: (leak+other_shadow+finite_shadow)/1024 descriptive, proxy label, NOT upgraded to composable
log2 d =10 upper bound check: hmin <10, h_m <10
```

and SHALL report per source `optimistic_floor / margin_5% / margin_10%` with `hmin_lower_authority` and `ell_or_null`. Three sources SHALL be independent, not averaged. `leak_total_s ==5*m_total+64` and `h_floor_s *1024 == leak_total_s` and `h_m*1024*(1-margin) == leak+other+finite` SHALL be asserted as anchors; `bits/block = bits/symbol *1024` conversion SHALL be recorded; `log2 d=10` upper-bound SHALL be checked. Only `V61_NEW_DATA_READY` (new experiment 10 classes `theorem + decisive PE + hmin_lower composable + finite/eps/EV/auth/post-sel/binding` all `ready`) may replace `other/finite` placeholders with authoritative values and judge `ell>0` / `margin≥0.10` per source (`hmin_lower` vs `floor 6.9238` vs `10% 7.6931` for `1M` etc.); non-`READY` SHALL keep `ell_* = null` and `hmin_lower = null` (never fill with shadow floor); `proxy_not_upgraded` and `missing→null` SHALL be asserted. `IAB/H/MAP/vis` as `H_min` SHALL be `SPEC_INVALID`.

### Requirement: V61 Stop Rule and V62 Gate (No Old-Data Fake PE, No V62 Without New Security Measurement Data)

When `composable_theorem_missing_in_new_data_spec` OR `decisive_PE_missing_in_new_data_spec` (`e_ph/conjugate/n_PE/vis_chain` without new physical observation) holds, the change SHALL conclude `V61_SPEC_READY__V62_PENDING` (spec ready but new data still missing) and SHALL NOT fill `null` with `shadow` floor, SHALL NOT run `decode_*`, SHALL NOT rerun `V55`, SHALL NOT modify `LDPC`, SHALL NOT fake `PE` from old data (`old_data_fake_PE → EVIDENCE_INVALID`), and SHALL NOT create numeric `V62` (`V62` remains `PENDING`). The overall spec verdict SHALL be `first-match`, priority-ordered, mutually exclusive:

```
if not spec_10items_ge10 or not unit_ok or leak !=5*m+64 or m_total != m1+m2 or IAB/H/MAP/vis_as_Hmin or not formula_self_consistent or tag_repeated or proxy_upgraded or old_data_fake_PE:
    overall = V61_SPEC_INVALID  # spec incoherence, proxy upgrade, or old-data fake PE
elif composable_theorem_missing_in_new_data_spec or decisive_PE_missing_in_new_data_spec:
    overall = V61_SPEC_READY__V62_PENDING  # spec ready but decisive new data missing, ell=null, need new theorem or new PE acquisition
elif not all_decisive_ready_spec or not hmin_lower_composable_defined:
    overall = V61_SPEC_READY__V62_PENDING  # spec landed but new data still insufficient
elif spec_all_critical_ready and new_data_all_critical_ready and hmin_lower_composable and break_even_floor_done and checklist_done and unit_ok and not old_data_fake_PE:
    overall = V61_SPEC_READY__V62_OPEN  # only this state may open V62 numeric successor (new OpenSpec + independent auth)
else:
    overall = V61_SPEC_READY__V62_PENDING
```

- `V61_SPEC_READY` means the 10-class schema + acceptance formula are landed and checkable; `V62_OPEN` means new experimental data satisfying the schema have arrived and `ell` is computable. `V61` push SHALL NOT automatically open `V62`.
- `missing → null` SHALL be kept `null` (not `0`), `shadow` SHALL NOT be upgraded to `composable`, and `only_NEW_DATA_READY_ell` (`(overall==OPEN) == (ell_not_null)`) SHALL hold. The minimal checklist `docs/research_cycles/V61P0/v61_minimal_new_measurement_checklist.csv` (`priority, item, missing_reason, minimal_new_measurement, required_sample_or_proof, acceptance_criterion, depends_on`), prioritized `composable theorem > decisive PE (e_ph/conjugate/n_PE) > visibility chain > eps/finite > EV/auth/post_sel > units/binding`, SHALL be consistent with schema.

### Requirement: V61 DECODE_FORBIDDEN Guard and Delivery (No run_01, No src/V54-V60 Change, No V55 Rerun, No LDPC Change, No V62, py_compile, Break-Even Anchors, Four Artifacts Pushed)

The change SHALL remain `PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY`: zero `decode_*` calls (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`, `rg "construct_" 0 hits` for LDPC), no change to `H1/Lane C/H_inc1/2/Δ/decoder 90/1.0/poly37/m/estimator/LDPC` and no change to `openspec/changes/formal-ir-v5[5-9]/` and `openspec/changes/formal-ir-v60*/` (`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[5-9]/ ==0 && git diff -- openspec/changes/formal-ir-v60*/ ==0`, and `openspec/changes/formal-ir-v61*/` only this change), no `.../v61_*/run_01` decoder execution creation, no `V55` rerun, no `LDPC` modification, no automatic `V62` numeric entry (`V62` still `PENDING`), `py_compile` PASS, and the following verifications SHALL pass: `GF32×5 tag-no-repeat` (7025/7375/7700 +64 =7089/7439/7764), `three-source independent` (no averaging), `break-even anchor h_floor*1024 == leak` and `h_m*1024*(1-margin) == leak+other+finite`, `missing→null` (`composable null` not `0`), `proxy not upgraded` (`shadow/proxy` distinct from `composable`), `10-class coverage` (`readiness 10 items` exact), `H/IAB/MAP/vis != H_min`, `old_data_fake_PE ==0`, `only_NEW_DATA_READY_ell`, `HEAD 9f1fb02c...` verified with `git fetch && HEAD==origin/formal-ir-mainline` before implementation. Optional script `scripts/v61_measurement_spec_check.py` SHALL be decoder-free (`numpy/pandas` only, optional `pyarrow`) and SHALL produce/check the four artifacts below. The artifacts SHALL be:

- `docs/research_cycles/V61P0/v61_measurement_schema.json`,
- `docs/research_cycles/V61P0/v61_minimal_measurement_template.csv`,
- `docs/research_cycles/V61P0/v61_minimal_new_measurement_checklist.csv`,
- `docs/research_cycles/V61P0/V61_SECURITY_MEASUREMENT_SPEC_REPORT.md` (V60 gap trace, 10-class definition table, unit/timestamp/session/source binding, `break_even` `floor/5%/10%` thresholds with `6.9238/7.2637/7.5820` anchors, `V62` gate, minimal prioritized checklist, `overall` verdict).

Push SHALL be ordinary (non-force) to `formal-ir-mainline` and SHALL remain `PLAN_CANDIDATE / DECODE_FORBIDDEN` awaiting independent `Pre-RESULT` review. After push, the change SHALL return `Plan SHA / implementation SHA / 10-class schema / three-source thresholds / V62 gate / final state`, without entering `V62` and without running `V55`/`LDPC`.

## MODIFIED Requirements

None. All prior `PLAN_CANDIDATE / DECODE_FORBIDDEN` and `V60_DATA_NOT_READY / ell=null` guards remain; `V61` adds minimal security-measurement acquisition specification without modifying `V57/V60` terminal or entering `V62` numeric.

## REMOVED Requirements

None.
