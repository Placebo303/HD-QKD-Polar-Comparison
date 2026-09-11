# D7-G code-factor extrinsic contract review R1 (F01 mathematical/implementation)

- Authority: `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md` §9 F01 only.
- Reviewer context: separate from implementer; review-only; no commits, no edits beyond this file, no Model-F/real reads, no roots/UUID, no production/scientific runs (tiny in-memory synthetic decoder calls only).
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `08987c6d6d5bd8b775a47b305eebbd599e57e72f` (`docs(d7-g): freeze code-factor extrinsic contract`).
- Frozen basis: R1 packet §1.2, OpenSpec `v72p2d7-code-factor-extrinsic-contract` (proposal/design/tasks/spec), `D7_G_PREREG_R1.md` (tolerances 1e-10, fixture families, flooding DEFERRED default).
- Under review (uncommitted): `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py` (tracked mod), `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_extrinsic_oracle.py` (new untracked), `comparison_bench/tests/test_v72p2d7_gf32_extrinsic_contract.py` (new untracked).
- Runs: separate processes, fresh basetemaps (`/tmp/f01-*`), `-p no:cacheprovider`, repo venv (numpy 2.5.3), tiny fixtures only.

## 0. Scope / HEAD verification (STOP-gate)

- `git rev-parse HEAD` = `08987c6d...` on branch `formal-ir-v72p1-addendum-clean`. PASS.
- `git diff HEAD --numstat -- .../v35_algorithm_development.py` = `127 0` (purely additive; zero deletions). PASS.
- `git diff HEAD --name-only -- comparison_bench/src/comparison_bench/formal_ir/ comparison_bench/tests/` = only `v35_algorithm_development.py`; untracked in those dirs = the two new review files plus an unrelated pre-existing `v72p2d4_cal_gf32_model_rate_audit` pair (different change, untouched by this review, no D7-G/H content). No other in-scope diff: no `*d7_h*`, no `*alternating*` in FORMAL, no `workspace/d7_g_*`, no cycle-state/auth change. Other tracked dirty files in the worktree (AGENTS.md, README, harness docs, etc.) are out-of-scope docs/drift, none in the frozen D7-G file map. No STOP condition met.

## 1. Independent derivation of the factor-message formula (Check 1) — PASS

Derived from the sum-product rule, not quoted from the design doc:

- Consider one variable node `x_i` with incoming prior factor `p_in(x_i)` (channel + any cross-layer evidence already folded in) and neighboring syndrome factors. The BP belief at convergence of the internal recurrence is `b_i(x) ∝ p_in(x) · Π_a m_{a→i}(x)`, where `m_{a→i}` are check-to-variable messages. In log domain with per-row constant `c_i`: `L_post = log p_in + Σ_a log m_{a→i} + c_i`.
- The outgoing code-factor message must carry the accumulated parity-check evidence only, excluding the incoming evidence (else the receiving layer would count `p_in` twice — once as its own prior, once inside the message). Hence `L_code_ext = L_post − log(p_in) = Σ_a log m_{a→i} + c_i`, defined up to the per-row constant `c_i`.
- Transport uses softmax; `softmax(z + c) = softmax(z)` row-wise, so row constants never affect the transported distribution. Stored form subtracts the row log-sum-exp: `store = e − logsumexp(e)`, making each stored row exactly log-normalized (`softmax(store)` = transported distribution) and reconstruction `softmax(log p_in + store) = softmax(L_post)` exact. Max-subtraction would leave an unknown per-row scale (demonstrated: max-normalized rows sum to 1.111…, not 1), so LSE is the correct frozen choice.
- Implementation match (`v35._build_check_extrinsic_log_beliefs`): `ext = post − pin`, `m = max`, `lse = m + log(sum(exp(ext − m)))`, returns `ext − lse` — exactly LSE normalization, with max used only as internal stabilizer. Helper `require_check_extrinsic_for_transfer` applies max-stabilized softmax. Own maxima: prod-vs-manual `0.0`, stored-row prob sums `[1, 1]`, reconstruction `0.0`, row-constant invariance (`+5.0/−3.25`) `0.0`. PASS.

## 2. Oracle independence (Check 2) — PASS

- Imports of `v72p2d7_gf32_extrinsic_oracle.py` are `__future__`, `itertools`, `numpy` only. Forbidden-needle scan (v35/rate_mother/decoder_certification/check-update/tables/belief_provenance/require_check/decode_/UnusableExtrinsic/extrinsic_log_beliefs) returns zero hits. No production `.py` imports the oracle (only test-file import; the single grep hit is a `__pycache__` byproduct of running the tests). PASS.
- Algebra spot-checks (read, not grepped):
  - `gf_add` = XOR, `gf_mul` = shift-and-reduce against `0b100101` (37 = x^5+x^2+1); independently-built MUL table is byte-equal to production `v35._get_gf32_tables` output (verified at runtime: `True`, Q 32/32, poly 37/37).
  - `tree_message_to_var`: for check `Σ c_j x_j = syn`, residual for others = `syn + c_t·v` via `ADD[syn, MUL[c_t, v]]` (correct since − = + in characteristic 2); enumerates all `32^(deg−1)` assignments, weights by cleaned priors, floors and renormalizes. Correct.
  - `row_layered_message_sums`: cold log beliefs from floored priors, rows in index order, per-row cavity `v = beliefs − u_old`, check update by explicit enumeration (independent of production FFT/Walsh), immediate `beliefs += u_new − u_old`; returns `beliefs − log_prior` per sweep. Correct schedule mirror without code sharing.
  - Channel transfers: `ch[i,j,k,l]` = (a1,a2,b1,b2); `transfer_to_b1` einsums `ijkl,i,j,l→k` etc. — correct marginalization directions. PASS.

## 3. Own reruns of decisive tiny cases (Check 3) — all PASS, no tolerance weakening

| Case | Own maximum / observation | Bound | Result |
|---|---|---|---|
| D01 formula/recon/invariance | prod-vs-manual 0.0; recon 0.0; row-const 0.0 | 1e-10/1e-12 | PASS |
| D02 tree-exact (1,7)/17, (2,13)/29, (1,2,3)/17 | 3.331e-16 each | 1e-10 | PASS |
| D03 loopy sweeps 1/2/3 (never MAP; syn_ok False) | 2.043e-14 / 1.776e-14 / 3.020e-14 | 1e-10 | PASS (~3000x margin) |
| D04.1 double-count gaps: msg L1 0.387464, msg L2 0.367439 | floors 1e-2 | PASS (~36x) |
| D04.1 fwd-transfer gap 0.065740; bwd gaps 0.013909 / 0.006460 | floor 1e-3 | PASS (6.5–66x) |
| D04.1 redecoded-posterior gap 0.005105 | floor 1e-3 | PASS (~5x, narrowest, deterministic seed-frozen) |
| D04.2 fwd L1 1.11e-16; fwd L2 3.33e-16; bwd L1 1.11e-16 | 1e-10 | PASS |
| D04.3 it0 neutral: uniform-dev 0.0; transfer-dev 3.47e-18; iters 0, NO_CHECK_EVIDENCE | 1e-12 | PASS (no false lift) |
| D04.4 warm + it0 rejection via helper | both raise UnusableExtrinsicError | — | PASS |

Full contract suite rerun: `test_v72p2d7_gf32_extrinsic_contract.py` → **48 passed** (matches claimed 48 tests) in a separate fresh-basetemp process. No decisive case failed to reproduce.

## 4. No change to existing hard decisions/posteriors (Check 4) — PASS (with one PASS-neutral tripwire, see §7-T1)

- v35 diff is +127/−0: new tokens, `UnusableExtrinsicError`, builder, helper, two optional `DecoderResult` fields (default `None`), `log_input_prior = beliefs.copy()` reusing the exact internal cleaned-prior array (no duplicated cleaning rule), and extrinsic population on the three existing row-layered return paths only. No edit to `beliefs` computation, stopping, iteration counts, `final_beliefs`, flooding returns, or `belief_provenance` mapping.
- Own reruns: D7-A certification suite `test_v72p2d7_gf32_decoder_certification.py` → **14 passed**; BP suites → `test_v72p2d7_bp_belief_provenance.py` 22 passed + 1 field-list failure (T1), `test_v72p2d6_bp_provenance_compat.py` **14 passed**; combined BP literal counts **36 passed, 1 failed** (single known tripwire).
- PV-05 numeric tail verified independently bypassing the field-list pin: first-6 fields identical, legacy positional construction compatible, it0 `final_beliefs` byte-identical to floor/renorm path with `x_hat [0,0]`, one-sweep beliefs vs D7-A reference max-abs 2.43e-17 (≤1e-12), flooding extrinsic `None/None` with `CHECK_UPDATED` provenance. `final_beliefs`, stopping, iterations, numerics unchanged. PASS.

## 5. Enum / fields / provenance (Check 5) — PASS

- Exact tokens in a separate namespace: `NO_CHECK_EVIDENCE` / `CHECK_EXTRINSIC` / `WARM_START_UNSPECIFIED` with tuple order pinned; `belief_provenance` tokens unchanged (`PRIOR_ONLY`/`CHECK_UPDATED`/`WARM_START_UNSPECIFIED`); cross-namespace isolation asserted both directions (extrinsic tokens rejected by the belief gate and vice versa). Covered by passing tests EXT-05a/05c.
- it0: neutral zeros + `NO_CHECK_EVIDENCE`, transport-uniform, helper-ineligible (verified own run). Warm: `None` + `WARM_START_UNSPECIFIED` on all warm paths (it0 and post-sweep), never inferred from iterations; misshapen warm seed follows the pre-existing cold rule identically for both provenances. Nonfinite/shape mismatch: fail-loud (`ValueError` at builder/decoder level; `UnusableExtrinsicError` at helper level), never repaired.
- Flooding: DEFERRED — both flooding return sites use defaults only (`None/None`), existing outputs unchanged (verified own run + passing test).
- Helper: accepts only explicit finite shape-correct `(n, 32)` `CHECK_EXTRINSIC` (plus optional `expected_n`); rejects `None`/unknown/`NO_CHECK_EVIDENCE`/warm/bogus provenance, bad shapes (incl. empty-row), nonfinite, and row-count mismatch; fully unwired from production — no `require_check_extrinsic*` / `extrinsic_*` / `UnusableExtrinsicError` references outside `v35_algorithm_development.py` and the test module; static inventory tests pass. PASS.

## 6. Scope (Check 6) — PASS

- Only the three allowed paths changed/added. No D7-G/H roots (`workspace/d7_g_*` empty, no `*d7_h*`, no `*alternating*` in FORMAL or workspace; passing test `test_ext_06_no_d7h_no_new_roots_no_forbidden_reads`). No UUID in review files. No auth changes (`cycle_state.yaml` untouched, all authorizations false). No Model-F/CAL/VAL/real reads (oracle grep clean; test module binds no real root — passing scan test). Frozen baseline `src/`, `experiments/`, `tools/` untouched. No push performed.

## 7. Adjudication of the three isolated tripwires

- **T1 — PV-05 line-130 field-list equality failure** (`test_pv_05_additive_field_and_numerical_equivalence`): asserts the full `DecoderResult` field list equals OLD + `["belief_provenance"]`; fails with 2 extra items (`extrinsic_log_beliefs`, `extrinsic_provenance`). This is the direct, expected consequence of the frozen additive-field contract (prereg §1: "additive optional fields only"; OpenSpec compatibility matrix row 1). Numeric tail (§4) passes fully; first-6 fields and positional compat intact. **PASS-neutral**; the pin now belongs to the new contract suite (EXT-05a), which passes.
- **T2 — `RuntimeWarning: invalid value encountered in divide` at v35 line 811** during `test_ext_05b_nonfinite_fails_loud_never_repaired` (nan/inf fixtures): benign warning from the pre-existing frozen floor/renorm cleaning path operating on all-nonfinite input before the fail-loud raise; the test itself passes (both nan and inf raise `ValueError`, builder-level `None`/shape/nonfinite raise). No behavior change, no silent repair. **Non-blocking, PASS-neutral**.
- **T3 — dirty worktree outside review scope** (tracked harness/docs drift + unrelated untracked `v72p2d4` pair): verified none of it lies in the frozen D7-G file map, carries no D7-G/H root/UUID/auth/Model-F content, and none of it was relied on for certification. The review scope itself (§0) is exactly the three allowed paths. **Out-of-scope, non-blocking**; flagged for hygiene only.

## 8. Discrepancies

- None blocking. Observations (not defects): (a) narrowest deterministic margin is the D04.1 redecoded-posterior gap, 0.005105 vs 1e-3 floor (~5x) — seed-frozen and stable, but any future reseed must re-prove it; (b) D03 loopy errors (~2–3e-14) sit ~3 orders below tolerance, consistent with FFT-vs-enumeration accumulation, not a contract risk; (c) T2 warning could be silenced in a future touch only if done without altering the frozen cleaning rule.

## Verdict

`D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS`

This verdict covers F01 mathematical/implementation certification only. It does not authorize D7-H, any alternating execution, or any promotion. FAIL-stop rule respected: no defect found, so the line is not stopped by this review.

## Return delta (summary)

1. Scope/HEAD: `08987c6` + only the three review paths (v35 +127/−0; two new files); no in-scope extra diff.
2. Formula independently derived (`L_code_ext = L_post − log p_in`, LSE-stored, softmax-invariant); implementation exact (own maxima 0.0).
3. Decisive tiny cases reproduced independently: D02 ≤3.34e-16, D03 ≤3.03e-14, D04.2 ≤3.34e-16, D04.1 gaps ≥5x floors, D04.3/D04.4 PASS; full contract suite 48/48.
4. Existing decisions/posteriors unchanged: D7-A 14/14; BP 36/37 with T1 PASS-neutral (numeric tail 2.43e-17).
5. Enum/fields/provenance/helper/flooding-DEFERRED all per frozen contract; helper unwired (inventory PASS).
6. No roots/UUID/auth/Model-F breach.
7. Tripwires T1/T2/T3 adjudicated PASS-neutral/benign/out-of-scope.
8. Review doc: `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/D7_G_EXTRINSIC_CONTRACT_REVIEW_R1.md`. No commits, no pushes.
