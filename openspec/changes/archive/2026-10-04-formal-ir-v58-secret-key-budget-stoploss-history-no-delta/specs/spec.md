# Delta Spec: formal-ir-v58-secret-key-budget-stoploss — V58 decoder-free 密钥预算止损

## ADDED Requirements

### Requirement: V58 Frozen V57 Disclosure as Budget Input (Zero Change)

The change SHALL treat V57 accepted disclosure as frozen read-only input with zero modification:

| source | m1 | m2 | m_total | leak_total bits/block | leak_without_tag (=5*m_total) | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

with `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 bits/block L2-only` counted once in `leak_total =5*m_total+64` and `m_total=m1+m2`. The change SHALL verify `leak_total ==5*m_total+64` per source and SHALL NOT create a new `m1/m2` or decoder matrix. `data SHA 84d62779` and `pairing nearest legacy_v1` remain unchanged. Any `decode_*` or channel-estimator change SHALL be forbidden (`rg "decode_" 0 hits`).

### Requirement: V58 Phase A Read-Only Formula Investigation and H_min Decision (No Self-Invented Formula, DATA_INCOMPLETE on Missing)

The change SHALL perform a read-only investigation of the repository's authoritative `secret-key length / PA / finite-key` formula implementation (candidate files: `tools/security_reports/_security_calibrated_common.py` (`delta_fk_calibrated`, `chi_from_visibility`, `dary_mutual_info_proxy`), `tools/security_reports/build_actual_ir_finite_key_shadow.py`, `tools/security_reports/round2_build_actual_ir_finite_key_shadow.py`, `tools/security_reports/round2_build_finite_key_audit_table.py`) and SHALL persist `formula_authority = {delta_fk: {file, lines, expr, unit}, pie_secure: {file, lines, expr, unit}, chi_E, iab, h_min: {file, lines or "MISSING"}}` with explicit units (`bits/block` vs `bits/symbol` vs `bits/pair`) and whether `tag` is already included. `H_min^epsilon(A|E)` source SHALL be explicitly identified; if only `H(A|B)` or `IAB_est` exists without a declaration as `H_min` proxy, the change SHALL mark `weak_proxy=true` and cap the terminal at `POSITIVE_BUT_FRAGILE`, or if `IAB_est` is not declared as proxy or `epsilon` budget is missing, SHALL yield `SECURITY_INPUTS_INCOMPLETE` (subtype `DATA_INCOMPLETE`) and stop without inventing a formula. The change SHALL NOT invent `H_min / finite-key` formulas or fabricate `eps_sec/eps_cor/visibility` parameters; missing decisive input SHALL be `SECURITY_INPUTS_INCOMPLETE` with stoploss, not a computed `ell`.

### Requirement: V58 Phase B Unit and Double-Deduction Audit (Decomposition Table, Tag-No-Repeat, GF32 5bits, H(A|B) != H_min, No Cross-Source Averaging)

The change SHALL establish a `decomposition table` per source with:

- `leak_without_tag =5*(m1+m2)` (`7025/7375/7700`) and `leak_total = leak_without_tag +64` (`7089/7439/7764`) — `tag` counted once, not deducted repeatedly;
- `GF32 5 bits/symbol` conversion `bits/block = bits/symbol *1024` explicitly verified;
- **Shall NOT treat `H(A|B)` as `H_min^epsilon(A|E)`** — if `H(A|B)`/`IAB_est` is borrowed as budget, it SHALL be labeled `weak_proxy=true` and SHALL cap overall at `POSITIVE_BUT_FRAGILE` at most;
- **Shall NOT average across sources** — `ell_final` SHALL be computed and reported per source independently, `mean(ell)` SHALL NOT replace per-source values;
- `m_total == m1+m2` and `leak_total ==5*m_total+64` SHALL be asserted, failure → `EVIDENCE_INVALID`.

### Requirement: V58 Phase C Three-Source Mechanical Recalculation (ell_final = min_entropy_budget - ir - other - finite)

The change SHALL compute per source `s ∈ {1M,1p5M,2M}`:

```
ir_disclosure_s = leak_total_s  # 7089/7439/7764 bits/block, already includes tag
min_entropy_budget_s = 1024 * h_min_per_symbol_s  # or authoritative per-block directly, unit-checked
other_disclosure_s = auth_s + pe_penalty_s + ...  # authoritative interval, 0 with "no_authority_other" tag if missing
finite_penalty_s = DeltaFK_s  # unit-checked per authoritative file, missing → SECURITY_INPUTS_INCOMPLETE
ell_before_IR_s = min_entropy_budget_s - other_disclosure_s - finite_penalty_s
ell_final_s = ell_before_IR_s - ir_disclosure_s
per_pair_s = ell_final_s / 1024
margin_ratio_s = ell_final_s / min_entropy_budget_s  (if min_entropy_budget_s>0 else nan)
conservative_s = f(h_min low, ir high, other high, finite high)
optimistic_s   = f(h_min high, ir low, other low, finite low)
```

and SHALL report per source `ell_before_IR / leak_without_tag / tag64 / other / finite / ell_final / per_pair / margin_ratio` with `conservative/optimistic` both ends. Three sources SHALL be independent, not averaged. `ell_final ==0` SHALL be classified as `NO_POSITIVE_KEY_MARGIN` (`≤0` includes `0`).

### Requirement: V58 Phase D Sensitivity Boundary (Interval Propagation Only, No Grid)

The change SHALL propagate only authoritative interval bounds `[low, high]` for parameters `eps_sec, eps_cor, franson_visibility, IAB_est` (if present in repository) to `conservative` and `optimistic` ends; grid search or parameter tuning (`rg "grid|param_grid|GridSearch" 0 hits`) SHALL be forbidden. If no interval exists, `conservative == optimistic` with `interval_tag="no_interval"` and explicit report. `margin 0.10` and `ell=0` boundaries SHALL be unit-tested.

### Requirement: V58 Phase E First-Match Five-State Verdict (Priority-Ordered, Mutual Exclusion, Stoploss Except POSITIVE_KEY_MARGIN)

The overall verdict SHALL be first-match, priority-ordered:

```
if not unit_ok or leak !=5*m+64 or m_total != m1+m2 or not formula_self_consistent:
    overall = EVIDENCE_INVALID  # highest: unit/tag/m coherence failure
elif h_min_missing or unit_missing or finite_coeff_missing or security_inputs_incomplete:
    overall = SECURITY_INPUTS_INCOMPLETE  # includes DATA_INCOMPLETE, deterministic missing authority
elif any(ell_conservative_s <= 0 for s in sources):  # includes 0
    overall = NO_POSITIVE_KEY_MARGIN  # any conservative ≤0 immediate stoploss
elif any(weak_proxy_s) or any(margin_conservative_s < 0.10) or any(cross_zero_s = conservative<=0<optimistic):
    overall = POSITIVE_BUT_FRAGILE  # >0 but thin (<10%) or cross-zero or weak proxy — stoploss, watch
else: # three sources all conservative>0 && margin_conservative≥0.10 && !weak_proxy && !incomplete && unit_ok
    overall = POSITIVE_KEY_MARGIN  # all authoritative closed and ample margin — successor low-dim model allowed, still not auto decoder
```

- Only `POSITIVE_KEY_MARGIN` SHALL allow a successor (low-dimensional `U1/U2` decomposition or 1D conservative budget) and SHALL still require a new `OpenSpec` with `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` and dual review — **not an automatic decoder**.
- All other four states SHALL be explicit stoploss: “**decoder not allowed / successor not entered**”.
- A source-mixed example (`1M ell>0, 1p5M ell<0, 2M ell<0`) SHALL NOT be averaged to positive; `NO_POSITIVE_KEY_MARGIN` SHALL be triggered by the negative source.

### Requirement: V58 Decoder-Forbidden Guard and Delivery (No run_01, No src/experiments/tools Change, py_compile, Unit Tests)

The change SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ/decoder 90/1.0/poly37/m` ( `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`), no `.../v58_*/run_01` decoder execution creation, `py_compile` PASS, and the following unit tests SHALL pass: `GF32×5 tag-no-repeat` (7025/7375/7700 +64), `three-source independent` (no averaging), `missing H_min → INPUTS_INCOMPLETE`, `ell=0 boundary → NO_MARGIN`, `margin 0.10` (`<0.10 FRAGILE`, `≥0.10 POSITIVE` if other gates pass), `one-positive-two-negative not averaged`. `HEAD 337e3a79` SHALL be verified with `git fetch && HEAD==origin/formal-ir-mainline` before implementation. Script `scripts/v58_secret_key_budget_stoploss.py` SHALL be decoder-free (`numpy/pandas` only, optional `pyarrow`) and SHALL produce `docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md`, `v58_secret_key_budget.json`, and compact CSV (`source,ell_before_IR,leak_without_tag,tag64,other,finite,ell_final,per_pair,margin_ratio,conservative,optimistic,gate`). Push SHALL be ordinary (non-force) to `formal-ir-mainline` and SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` awaiting independent `Pre-RESULT` review.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain; V58 adds decoder-free budget stoploss without modifying V57 terminal.

## REMOVED Requirements

None.
