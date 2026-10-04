# Sibling Prior Parameterization Audit — 2026-09-21 (read-only)

- Repo under audit (READ-ONLY, nothing modified there): `/mnt/d/Code/HD-QKD_Polar_Release`
- This report is the single write allowed by the task; no commit/push in either repo; no data access, no pipeline execution.
- Method: read cited files verbatim, then repo-wide `grep` to test each claim. Anything not verifiable is marked UNVERIFIABLE (none below — all claims were checkable).

## Verdict table

| Claim | Verdict | One-line evidence |
|---|---|---|
| S1 — decoder consumes only a parameterized per-bit-plane channel, LLR = ±log((1−p)/p) | CONFIRMED (with one nuance: an optional 2-scalar/plane asymmetric mode exists, default is 1-scalar BSC) | `round1b_run_actual_ir_replay.py:67-70`, `:73-78`, `:461-482` |
| S2 — the only q×q conditional table in the whole repo is a MAP-sanity diagnostic that never reaches the decoder | SCOPED-CONFIRMED for the mainline actual-IR replay path; DIFFERENT repo-wide ("全库唯一" is false) | `export_joint_sequence_sidecar.py:400-411`, `:1618-1619`, `:1688-1694`; counterexample `low_dim_opt/simulation/msd_eval.py:965`, `:984-997` |
| S3 — parameters estimated on key data, same-sample, sacrificed sample = 0, estimation leakage = 0 bits | CONFIRMED as behavior; critical distinction: the "0 bits" is a **declared constant by omission** (no term exists), not a computed/bounded value | `run_real_polar_max_pie.py:596-611`, `:903`, `:918-937`; zero-estimation-term grep negative; `tools/diagnostics/audit_security_model_lineage.py:51-53` |
| S4 — main conclusion口径 hardcoded `public_ec_only_not_secure`, `composable_security_claim_flag=0` | CONFIRMED — most important item, decisive lines quoted below | `round2_build_finite_key_audit_table.py:19`; `round2_build_actual_ir_finite_key_shadow.py:97-99` |
| S5 — public-message list exhaustive: syndrome + tag only; seed/mask/code structure = 0 bits | CONFIRMED | `round2_build_finite_key_audit_table.py:21-25`; `round1b_build_actual_ir_logs_index.py:91-107`; `src/reconciliation/verification.py:102` |
| S6 — actual parameterization count | CONFIRMED with numbers (see §S6) | `run_real_polar_max_pie.py:597`; `round1b_run_actual_ir_replay.py:150`, `:378` |
| S7 — SKR / net secret key reporting and claim labels | CONFIRMED: **no composable-security SKR is published** (see §S7) | `run_real_polar_max_pie.py:211`, `:986-987`; `round2_build_security_round2_summary.py:114`; `round2_build_actual_ir_finite_key_shadow.py:80-82` |

## S1 — decoder channel (CONFIRMED + nuance)

Verbatim (`pipelines/current/round1b_run_actual_ir_replay.py:67-70`):

```python
def _llr_from_side_info(bits_b: np.ndarray, ber: float) -> np.ndarray:
    p = float(min(1.0 - 1e-6, max(1e-6, float(ber))))
    lam = float(math.log((1.0 - p) / p))
    return np.where(bits_b.astype(np.uint8) == 0, lam, -lam).astype(np.float64)
```

- Yes: the channel is a per-bit-plane BSC scalar. One `ber` per `(point, layer_id)` row feeds one symmetric LLR pair `±lam`. Number of planes is `bits = int(round(math.log2(d)))` (`:378`), i.e. log2(d) planes per operating point (d=32 → 5; d=1024 → 10; example point syntax `"32,30;1024,150"` at `run_real_polar_max_pie.py:1190`).
- Nuance: an optional second mode exists (`:73-78`, selected by `--channel-model-tag`, default `bsc_legacy`, `:150`):

```python
def _llr_from_asym_binary(bits_b: np.ndarray, p01: float, p10: float) -> tuple[np.ndarray, float, float]:
    p01c = float(min(1.0 - 1e-6, max(1e-6, float(p01))))
    p10c = float(min(1.0 - 1e-6, max(1e-6, float(p10))))
    llr_b0 = float(math.log((1.0 - p01c) / p10c))
    llr_b1 = float(math.log(p01c / (1.0 - p10c)))
    return np.where(bits_b.astype(np.uint8) == 0, llr_b0, llr_b1).astype(np.float64), llr_b0, llr_b1
```

`asym_binary_v1` uses 2 scalars/plane (`p01_model`, `p10_model` from a channel-model table, `:461-482`) with fallback to BSC on ineligible/invalid rows. So the prior is 1 scalar/plane by default, 2 scalars/plane at most.
- The LLR feeds the Polar decoders directly (`:486-494`, `_decode_block` → `polar_sc_decode_with_frozen` for SC or `decode_batch_frozen_plain` for SCL). Repo-wide grep for `chan_ll_table|joint_sparse|dense_from_sparse|p_agb` returns **zero hits** inside `round1b_run_actual_ir_replay.py` — no q×q or joint table reaches this decoder.

## S2 — q×q table isolation (SCOPED-CONFIRMED / repo-wide DIFFERENT)

Cited function verbatim (`src/workflow/export_joint_sequence_sidecar.py:400-411`):

```python
def _build_chan_ll_table(joint_sparse_eff: list[dict[str, Any]], q: int, eps: float = 1e-300) -> np.ndarray:
    j = dense_from_sparse(joint_sparse_eff, q)
    pb = np.sum(j, axis=0)
    p_agb = np.zeros((q, q), dtype=np.float64)
    for b in range(q):
        if pb[b] > 0.0:
            p_agb[:, b] = j[:, b] / float(pb[b])
        else:
            p_agb[:, b] = 1.0 / float(q)
    out = np.log(p_agb.T + float(eps))
    out = out - np.max(out, axis=1, keepdims=True)
    return np.asarray(out, dtype=np.float64)
```

- Its only two consumers are the MAP sanity check (`:1618-1619`): `chan_ll_table = _build_chan_ll_table(joint_sparse_used, q=q)` → `map_ser, map_ber = _map_sanity(chan_ll_table, a_eff, b_eff, q=q)`, where `_map_sanity` predicts `pred = argmax_a log P(a|b)` (`:439-440`). The table is saved as a sidecar artifact (`chan_ll_table.npy`, `:1660`) and downstream only **checks its presence/bytes** (namespace gates: `tools/verify_candidate_namespace_gates.py:254`; manifest hash in `tools/materialize_loss_namespaced_candidates.py:194-208`) — it is never loaded as decoder input on the mainline path. The sidecar verdict is explicitly diagnostic-only (`:1688-1694`, paraphrase: `map_ser>=0.1` no longer gates; real FAIL only for sampled sequences; cf. `run_real_polar_max_pie.py:1000-1002` "map_ser no longer gates PASS/FAIL").
- "全库唯一" is nevertheless **FALSE repo-wide**. Counterexample — `low_dim_opt/simulation/msd_eval.py` builds d×d joint-count → conditional LLR tables and decodes with them:
  - `:965`: `design_counts = T.joint_counts(a_d, b_d, d)`
  - `:984-997`: `tables, _ = MC.build_msd_llr_tables_shift(design_counts, d, ...)` (or `MC.build_msd_llr_tables(design_counts, d, ...)` for `llr_model == "joint"`)
  - `:1007-1009` + `:524-536`: `decode_frame, decode_batch = make_decoder(...)` (numba SC via `polar_core`, or C++ SCL), then `decode_planes_on_test(...)` (`:280`, `:383`, `:1240`) decodes planes against these tables.
  - Related: `low_dim_opt/core/msd_conditional.py` (`build_msd_llr_tables*`, `build_msd_llr_tables_shift`) and its `diag_20260914/*` + `fer_gap_diag.py` callers; `src/workflow/llr_from_joint.py:23` (`build_joint_dense_from_sparse`, used only as a loader by the sidecar, `:24`); `src/qkd_io/ttbin_pipeline.py:48,485` (joint→delta-distribution diagnostic, not a decoder); `tools/asenoise/run_asenoise_type0_jti_dense.py:91,170` (loads joint sparse → dense for ASE-noise analysis, not the Polar decoder).
- Honest scoping: `low_dim_opt/` is an exploratory low-dimension optimization track (its own design/test-split discipline, header `:1-9`: 40/60 design/test split, design-half-only tables), not the frozen actual-IR replay mainline. So: within the **mainline actual-IR replay + replay-index + audit-table path**, the "diagnostic-only q×q" claim holds; as a **whole-repo** statement it does not.

## S3 — same-sample estimation, sacrificed = 0, leakage = 0 (CONFIRMED, with critical distinction)

Cited function verbatim (`experiments/run_real_polar_max_pie.py:596-611`):

```python
def _extract_real_layer_bers(a_eff: np.ndarray, b_eff: np.ndarray, d: int) -> np.ndarray:
    bits = int(round(math.log2(int(d))))
    if 2**bits != int(d):
        raise ValueError(f"dimension={d} is not power-of-two")
    n = int(min(a_eff.size, b_eff.size))
    if n <= 0:
        raise ValueError("empty aligned sequence")
    a = np.asarray(a_eff[:n], dtype=np.int64)
    b = np.asarray(b_eff[:n], dtype=np.int64)
    bers = np.zeros(bits, dtype=np.float64)
    for layer_idx in range(bits):
        shift = bits - 1 - layer_idx
        abit = (a >> shift) & 1
        bbit = (b >> shift) & 1
        bers[layer_idx] = float(np.mean(abit != bbit))
    return bers
```

- What is estimated: per-bit-plane BERs (`layer_bers`), computed on the **full** key-data sequences `a_eff`/`b_eff` loaded from the sidecar (`:903`: `layer_bers = _extract_real_layer_bers(a_eff=a_eff, b_eff=b_eff, d=int(d))`). These BERs drive code design: per-layer simulated-FER rate search (`:918-937` → `_try_layer_sc(ber=...)` / `_try_layer_scl(ber=...)`).
- Same sample: yes — the replay decoder later decodes the **same** `a_eff`/`b_eff` arrays (`round1b_run_actual_ir_replay.py:270-271,321-322`: loads `a_eff_source_path`/`b_eff_source_path`; `:395-396`: `bit_layer_from_symbols(a_eff/b_eff, ...)`). Grep for `train|holdout|split|sacrific|reserved` (excluding `splitlines`) finds **no estimation sample splitting** in either file — sacrificed sample = 0 by construction (nothing is reserved).
- Where the "0 bits" comes from: **there is no estimation-leakage variable at all**. Grep for `estimat` in `run_real_polar_max_pie.py`, `round1b_run_actual_ir_replay.py`, `round1b_build_actual_ir_logs_index.py`, `round2_build_finite_key_audit_table.py` returns only `fer_point_estimate` (FER simulation bookkeeping) — no `estimation_leak*|param_leak*|sacrific*` symbol exists anywhere in the sibling (repo-wide grep likewise: only `joint_sparse_sampling_same_source` in the sidecar). The zero is therefore **declared by omission**: no term is subtracted, no confidence interval is formed, no bound backs it. Release's own lineage audit says exactly this (`tools/diagnostics/audit_security_model_lineage.py:51-53`): "Present finite-length logic only appears in reconciliation simulation controls … `PIE_practical` has no explicit ΔFK term, no PE confidence interval term, and no composable epsilon budget."

## S4 — claim boundary + composable flag (CONFIRMED — decisive)

`tools/security_reports/round2_build_finite_key_audit_table.py:19` verbatim:

```python
RECONCILIATION_CLAIM_BOUNDARY = "public_ec_only_not_secure"
```

Decisive coupling lines (`tools/security_reports/round2_build_actual_ir_finite_key_shadow.py:97-99`):

```python
audit["composable_security_claim_flag"] = 0
audit["security_evidence_status"] = "scientifically_blocked_dimensional_inconsistency"
audit["missing_security_observables"] = "protocol_specific_phase_error_and_parameter_estimation_inputs"
```

- Yes: Release **declares itself outside composable security**. The same file brands the legacy secure result `scientifically_blocked_dimensional_inconsistency` / `diagnostic_only` (`:80-82`) and the summary line reads "legacy calibrated shadow is scientifically blocked; reconciled result is public-EC-only and not secure" (`:136-137`).
- Rationale context: the reconciled net is "net shared bits after public EC disclosure — never secret/secure/key-rate" (`round2_build_finite_key_audit_table.py:41-49`); `PRIMARY_REPORTING_MODE = actual_ir_reconciled_net_not_secure` (`tools/security_reports/longrun_build_security_master_table.py:60`, `round2_build_security_round2_summary.py:114`); the proof-gap matrix lists `decoy_state_PE`, `conjugate_basis_stats`, `protocol-specific composable constants`, `single-pair fraction` as **missing** for `niu_2016_composable` (`tools/security_reports/round3_build_proof_gap_matrix.py:18-22`).
- **Answer to the decisive question: Release's zero estimation-leakage is a consequence of excluding itself from composable security (scope exclusion), NOT a proven result.** The "0" in S3 and the "0" in `composable_security_claim_flag = 0` are coupled by design: because no composable claim is made, no PE penalty term is required, so none is computed.

## S5 — public-message inventory (CONFIRMED)

`round2_build_finite_key_audit_table.py:21-25` verbatim:

```python
# Exhaustive public-message inventory for the current actual-IR replay: the
# only key-dependent disclosures are the frozen/syndrome payload and the
# universal-hash verification tag. Seed/mask/code structure are
# key-independent metadata (verification_seed_public_leakage_bits = 0).
OTHER_DISCLOSURE_INVENTORY_TAG = "actual_ir_replay_public_inventory_syndrome_and_verification_only"
```

- Exact list: (1) frozen/syndrome payload, (2) universal-hash verification tag. Everything else (seed/mask/code structure) is classified key-independent metadata at 0 bits. Enforcement: `compute_reconciled_net` refuses any row whose `other_disclosure_source_tag != OTHER_DISCLOSURE_INVENTORY_TAG` (`:55-57`); the index builder sets `accepted_other_disclosure_bits = 0.0` with the comment "the exhaustive protocol inventory is syndrome payload + universal-hash verification tag (seed/mask/code structure are key-independent metadata)" (`pipelines/current/round1b_build_actual_ir_logs_index.py:91-107`); the transcript emits `"verification_seed_public_leakage_bits": 0` (`src/reconciliation/verification.py:102`) under seed policy `uniform_random_toeplitz_seed_sampled_after_messages_fixed` with public rule `toeplitz_seed_public_tag_bits_revealed` (`:12-13`). Note the stated justification is an **inventory assertion plus seed-policy label**, not a proof export — adequate inside `public_ec_only_not_secure`, insufficient under composable claims without re-justification.

## S6 — actual parameter count

- Default (`bsc_legacy`, the replay default per `round1b_run_actual_ir_replay.py:150`): **log2(d) free scalars per operating point** — one BER per bit plane (`run_real_polar_max_pie.py:597`, `round1b_run_actual_ir_replay.py:378`). Examples: d=32 → **5**; d=1024 → **10**.
- Optional (`asym_binary_v1`): **2·log2(d)** scalars per point (p01+p10 per plane, `:461-482`) — d=1024 → **20**.
- Adjacent fixed (non-estimated) scalar: `_E_P = 0.025` (`run_real_polar_max_pie.py:531`), a user-supplied Eve-error assumption driving `chi_e = h2(_E_P) + _E_P·log2(d−1)` — not fitted, not counted as prior data.
- Code structure itself (per-layer k/frozen sets from the simulated-FER rate ladder) is design output driven by the same BERs, disclosed as key-independent metadata (0 bits, §S5) rather than counted parameters.
- Comparison number: Release's decoder prior is **O(10) scalars per point** (5–10 default, ≤20 asymmetric) vs our ~2545-parameter joint table — roughly two orders of magnitude fewer fitted quantities, which is exactly why Release can afford to leave the estimation term at 0 inside a non-composable scope while we cannot.

## S7 — what Release publishes, with claim labels

| Quantity | Formula / source | Claim label |
|---|---|---|
| `best_hard_PIE` | max over SC/SCL simulated-then-replayed per-layer gains | `security_claim_level = engineering_diagnostic` (`run_real_polar_max_pie.py:211`), scope `polar_reconciliation_evaluation`, assumption `zhang2014_niu2016_style_conditional_not_unconditional`, `chi_E_source_tag = visibility_assumed_interface` |
| `PIE_practical` = max(0, best_hard_PIE − χE); `SKR_measured_bps` = PIE_practical × rate | χE from assumed visibility (`:985-987`); rate = preserved measured coincidence rate, never fabricated (`:1152-1159`) | same `engineering_diagnostic`; lineage audit: no ΔFK/PE/eps terms (`audit_security_model_lineage.py:51-53,60-61`) |
| `leak_EC_*` surrogate (`IAB_est − best_hard_PIE`) | `_security_proxy_terms` (`:424-440`); shadow tags it `surrogate_from_best_hard_pie_gap` | proxy/diagnostic, not measured syndrome accounting |
| `PIE_secure_actual_ir` / `SKR_secure_actual_ir_bps` | `IAB − leak − χE − ΔFK_calibrated` shadow (`build_actual_ir_finite_key_shadow.py:40-95`) | `finite_key_model_tag: zhong_like_finite_key_calibrated`, note "not full niu_2016 composable proof" (`:116`); round2: `legacy_secure_result_status = scientifically_blocked_dimensional_inconsistency`, role `diagnostic_only`, `composable_security_claim_flag = 0` |
| `PIE_reconciled_net` / `SKR_reconciled_net_bps` (the PRIMARY result) | `(kept − verification − other)/pairs × rate`, syndrome already excluded via k_used (`round2_build_finite_key_audit_table.py:41-49,80-96`) | `claim_boundary = public_ec_only_not_secure`, `reconciliation_evidence_status = verified_actual_ir_replay_reconciled_net`, "never secret/secure/key-rate"; `PRIMARY_REPORTING_MODE = actual_ir_reconciled_net_not_secure` |

Plain statement: **Release publishes no composable-security SKR.** Its headline numbers are public-EC-only net shared bits; its "secure" columns are blocked/shadow diagnostics with the composable flag hard-zeroed.

## Transferable to us / not transferable (we DO intend composable-security claims)

Transferable:
1. Per-plane BSC LLR discipline (S1) as a *baseline prior* — cheap, auditable, few parameters; keep for comparison arms.
2. Exhaustive public-message inventory practice (S5): listing every public message with a tag that gates the accounting (`other_disclosure_source_tag` check) is directly reusable for our NB-LDPC transcript.
3. Syndrome-already-excluded-in-k accounting and accepted-block-only disclosure deduction (S5/S7) — sound bookkeeping we should mirror.
4. Diagnostic-only joint-table pattern (S2 scoped part): keep large joint tables as diagnostics unless we pay their estimation cost.
5. Toeplitz-seed handling with explicit seed-policy labels — reusable form, but the 0-bit conclusion must be re-derived, not copied.

NOT transferable without new work:
1. **Zero estimation leakage (S3)**: under composable claims, our ~2545-parameter joint prior MUST pay either (a) a sacrificed-sample cost (disjoint design/test, as `low_dim_opt`'s own msd_eval does at 40/60) or (b) a PE confidence-interval subtraction plus eps budget. Release pays neither because it claims nothing composable.
2. **Seed/mask/code-structure = 0 bits**: re-justify under the composable model (seed reuse across blocks, code-structure disclosure) rather than inheriting the inventory assertion.
3. **BSC-per-plane sufficiency**: our NB-LDPC joint decoder intentionally uses richer channel information; its gain over the O(10)-scalar prior must be weighed against the estimation-leakage price Release avoids by staying small and non-composable.
4. **Any SKR label**: do not reuse `SKR_measured_bps`/`SKR_reconciled_net_bps` names for composable claims — they are defined as non-secure quantities in Release.
