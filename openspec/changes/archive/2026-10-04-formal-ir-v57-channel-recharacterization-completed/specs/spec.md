# Delta Spec: formal-ir-v57-channel-recharacterization (Revised2 最小 — 分层m_i + FAIL_NOSTABLE)

## ADDED Requirements

### Requirement: V57 Calibration/Validation Pre-Registration with Zero Overlap (Revised, Expanded)

The change SHALL pre-register per-source `Cal` and `Val` frame sets with **mutual zero overlap and zero overlap with `V55` authoritative `90×4`, `V56` `[7,8,9,10,15,16,17,18]`, and previous `V57` undersampled `64 ([19..50,77..108])`**, mechanically verifiable:
```
set(Cal_s) ∩ set(Val_s) == ∅  per s
set(Cal_s ∪ Val_s) ∩ set(V55_90flat_s) == ∅  per s  (V55 flat = 120 frames/source)
set(Cal_s ∪ Val_s) ∩ {7,8,9,10,15,16,17,18} == ∅  per s
set(Cal_s ∪ Val_s) ∩ {19..50,77..108} == ∅  per s
|Cal_s| ≥512, |Val_s| ≥512  per s  (131072 pairs/split, 128 blocks×4)
frame_id ∈ [0, F_s-1], F=2130/5125/5513, pairs_per_frame 256, BLOCK_LENGTH 1024
```
Frozen sets are per-source independent but deterministically defined:
- `available_s = sorted(set(0..F_s-1) - V55_flat_s - {7,8,9,10,15,16,17,18} - {19..50,77..108})`
- `Cal_s = available_s[0:512]`
- `Val_s = available_s[512:1024]`
Registries `v57_calibration_registry.json` and `v57_validation_registry.json` plus `v57_manifest.json` SHALL persist `selected_frame_ids[512], blocks=128, pairs=131072, F, K, provenance, smoothing α=1.0, ceil formula, zero_overlap_proofs (four-fold)` and SHALL be immutable after creation; any violation SHALL yield `V57_EVIDENCE_INVALID` with zero channel estimation. Previous `8192` result (`Cal 19..50/Val 77..108`) SHALL be retained as `v57_channel_recharacterization_undersampled_mle_negative_control.json/md` with `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` status and SHALL NOT be overwritten by new `512+512` result.

### Requirement: V57 Calibration Smoothed Joint Count and Conditional Entropy and Leakage Recomputation (Revised2, **分层m_i 纠正总量上界错误**, Tag)

The change SHALL deprecate bare `MLE` zero-probability (`P_mle=C/N_b` clamped `1e-15`) and SHALL estimate per-source on `Cal` (`131072` pairs, `F03 5+5 natural` `U1=sym>>5, U2=sym&31`) with pre-registered `Dirichlet/Laplace` smoothing fixed in `Cal` only (not tuned on `Val`):
```
C_ab = bincount2d(a_cal,b_cal) 1024×1024, N_b=Σ_a C_ab, P(b)=N_b/N_cal
P_smooth(a|b) = (C_ab + α)/(N_b + α*Q) if N_b>0 else 1/Q  with Q=1024, α=1.0 frozen Laplace
H_smooth(A|B) = -Σ_b P(b) Σ_a P_smooth log2 P_smooth
P_smooth(u1|b)=Σ_{u2} P_smooth(32*u1+u2|b), H_smooth(U1|B)=-Σ_b P(b) Σ_{u1} P_smooth(u1|b) log2 P_smooth(u1|b)
H_smooth(U2|B,U1)=H_smooth(A|B)-H_smooth(U1|B) with chain-rule check |H-H1-H2|<1e-9 else EVIDENCE_INVALID
```
Bare `MLE` `H_mle`, `zero_cells`, `q_mass_mle` remain reported as negative-control contrast but `NLL/entropy/leakage` SHALL use smoothed values. Leakage SHALL be recomputed source-adaptive with `f_target=1.3, n=1024, tag=64, log2q=5` **using per-layer `m_i = min(1024, ceil(f_target * n * H_i /5))` respectively by H1/H2 directly, not total-proportional** (revised2 corrects `m_total≤1024` error — actual two-layer GF32 each `0≤m_i≤1024` total `0≤2048`), and explicit tag-in-total + FULL_DISCLOSURE_LAYER marking + true f_eff recalc:
```
m1 = min(1024, ceil(f_target * n * H1_smooth /5))  # 层1由H1直算
m2 = min(1024, ceil(f_target * n * H2_smooth /5))  # 层2由H2直算，不先算总量再按比例
FULL_DISCLOSURE_LAYER_i = (ceil(f_target*n*H_i/5) > 1024)  # 若饱和记 FULL_DISCLOSURE_LAYER 并重算真实 f_eff
m_total = m1 + m2  # 0..2048
leak = 5*m_total + 64, f_eff = leak/(1024*H_smooth)  # tag仅total计一次，f_eff含截断真实值
Δ_m = m_total - m_total_V25ref, Δ_leak = 5*Δ_m
```
Gate SHALL be `m1≤1024 && m2≤1024` dual-gate (delete `m_total≤1024` single-gate); `FULL_DISCLOSURE_LAYER` saturated SHALL be recorded as `FULL_DISCLOSURE_LAYER` and true `f_eff` recalculated, not `EVIDENCE_INVALID`. `V25` `m2 184/190/192` and `m1=16` SHALL be marked deprecated and SHALL NOT be reused; new `m1/m2/m_total` are for reporting and `V58` planning only and SHALL NOT be instantiated as new matrices in `V57`. Tag `64b` SHALL be counted once in `leak_total/f_eff` only. `λ` grid `0.1,1,10` SHALL remain fixed, not expanded.

### Requirement: V57 Validation Estimator Gates Per Source (Revised, Descriptive MAP/Zero)

The change SHALL validate per-source on `Val` (`131072` pairs) using `P_cal_smooth (α=1.0)` from `Cal`, with **estimator gates** (zero-support and MAP descriptive only):
- **EG1 NLL finite & improved**: `NLL_val_smooth=mean_{Val}[-log2 P_cal_smooth]` finite; `PASS_EG1 = isfinite && NLL_val_smooth <15.0 && NLL_val_smooth < NLL_val_mle_clamp -5.0 && NLL_val_smooth < NLL_V25_on_Val`.
- **EG2 CV consistency**: `NLL_cal_self_smooth=mean_{Cal}[-log2 P_cal_smooth]`; Cal 2-fold `NLL_fold1/NLL_fold2` (256+256 split, same α); `PASS_EG2 = |NLL_val - NLL_cal_self| ≤0.50 && rel ≤0.25 && |fold1 - fold2| ≤0.50`.
- **EG3 entropy stability & convergence**: `H_val_smooth=H_smooth(A|B)_Val`; `PASS_EG3 = |H_val - H_cal|≤0.20 && rel≤0.25`; plus report convergence series `32/128/256/512` showing `NLL` from `30→~` and `H` stabilizing (descriptive).
- **Descriptive only**: `q_mass_mle=Σ_{C_ab_cal_mle==0} P_val_emp` and `zero_frac` and `acc_smooth=mean[a==argmax P_smooth]` SHALL be reported but **SHALL NOT** gate `PASS_s` (`q_mass ≤20%` and `acc≥60%` hard gates removed).
`PASS_s = PASS_EG1&&EG2&&EG3 && zero_overlap_s && counts_valid_s && m1≤1024&&m2≤1024` SHALL be judged **per source separately, without overall averaging**; `m_i` saturated `FULL_DISCLOSURE_LAYER` SHALL be marked and `f_eff` recalculated, not invalid; `λ` `0.1,1,10` fixed not expanded.

### Requirement: V57 Three-Source Independent Verdict and V58 Gate (All-Pass Only, **FAIL_NOSTABLE**)

The overall verdict SHALL be exclusive, priority-ordered (**revised2**):
```
if not zero_overlap_all (four-fold) or not counts_valid_all or |H-H1-H2|>=1e-9 → V57_EVIDENCE_INVALID  # only hard integrity
elif PASS_1M && PASS_1p5M && PASS_2M (EG1-3 + m1≤1024&&m2≤1024 all) → V57_CHANNEL_RECHARACTERIZATION_PASS
else → V57_CHANNEL_RECHARACTERIZATION_FAIL / PREDICTIVE_MODEL_NOT_STABLE (including MIXED_BY_SOURCE per-source list)
```
Current observed `Cal self NLL 4.6-5.5` vs `Cal-fold/Val NLL 8-10`, `EG2` three sources `FAIL`, `λ` three sources all upper bound `10` proves predictive model not stable → verdict SHALL be `V57_CHANNEL_RECHARACTERIZATION_FAIL / PREDICTIVE_MODEL_NOT_STABLE` rather than `EVIDENCE_INVALID`; `λ` grid SHALL NOT be expanded. `FULL_DISCLOSURE_LAYER` saturation SHALL be `FAIL` marking not `INVALID`. Only `V57_CHANNEL_RECHARACTERIZATION_PASS` (all 3 sources `PASS_s`) SHALL allow a successor `V58` to freeze new `TEST` blocks (`30/source`, zero overlap with `Cal512/Val512` and `V55 90` and `undersampled 64`, unrevealed) and proceed through `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT dual review + EXECUTE_AUTH` to decoder TEST. `FAIL/INVALID` SHALL remain `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED` and SHALL NOT enter decoder, but `FAIL` SHALL push new SHA and remain `DECODE_FORBIDDEN`. Previous `8192 MLE` status `UNDERSAMPLED_MLE_NEGATIVE_CONTROL` SHALL be preserved.

### Requirement: V57 Decoder-Forbidden Guard (Revised2, **分层m_i + FAIL_NOSTABLE**)

The change SHALL remain `V57_CHANNEL_RECHARACTERIZATION_PENDING_REVISED / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ8/decoder 90/1.0/poly37/m2/leak/prior`, smoothing `α=1.0` fixed not tuned on `Val` (`λ` `0.1,1,10` fixed not expanded), leakage **per-layer `m_i=min(1024,ceil(f N H_i/5))` not total-proportional, `m1≤1024&&m2≤1024` dual-gate, `FULL_DISCLOSURE_LAYER` marking + true `f_eff` recalc, `m_total≤1024` error corrected**, tag once, no `.../v57_*/run_01` creation, no rerun on the original `V55 90`, `py_compile` PASS, four-fold zero overlap verified, `|H-H1-H2|<1e-9` verified, `git diff -- src/ ==0` and `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0`, and `V25 184/190/192` deprecation explicitly stated, previous `8192` preserved as `negative_control`, **new SHA pushed**. No `bin_width/dimension/pairing` grid search (`rg "grid" 0 hits`); `λ` grid not expanded. Verdict `FAIL/PREDICTIVE_MODEL_NOT_STABLE` SHALL remain `DECODE_FORBIDDEN`.

### Requirement: V57 Original 90 Permanent Ban and Freshness Boundary (Revised)

`v55_authoritative_registry.json`'s `90×4` frames (already revealed `0/90`) SHALL remain permanently banned from any corrected-pipeline rerun. `Cal512/Val512` and any future `V58 TEST` are derived from the same three `20260123/20260107` `pairs.parquet` already used for diagnosis; therefore the change SHALL explicitly state in report and spec that `V57` (including smoothed `131k`) does not claim fully independent cross-session qualification and that true cross-session qualification rests with `V58` new `TEST` (fresh `TEST` is `fresh within-session confirmation` until a new acquisition, boundary explicitly declared). Previous `V57` `8192` `H vs NLL` split SHALL be declared `ESTIMATOR_UNDERSAMPLED` and retained as negative control, not falsifying the code family nor the new estimator. `V54`'s `43/45` validity in the `2026-01-21` domain and the located domain incompatibility SHALL be preserved as not falsifying the code family.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain; `V57` adds revised channel recharacterization (expanded, smoothed, estimator-gated, ceil) without modifying `V56` terminal.

## REMOVED Requirements

None. `V25` `184/190/192` remains as historical reference only, deprecated for new-domain budgeting. Old thresholds `V1 NLL≤H+0.5&≤1.5&<V25-5` / `V2 acc≥60%` / `V3 q_mass≤20%` are **superseded** by `EG1-3` estimator gates; `MAP(acc)` and `q_mass` hard gates are removed (now descriptive).
