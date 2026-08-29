# Delta Spec: formal-ir-v57-channel-recharacterization

## ADDED Requirements

### Requirement: V57 Calibration/Validation Pre-Registration with Zero Overlap
The change SHALL pre-register per-source `Cal` and `Val` frame sets with **mutual zero overlap and zero overlap with `V55` authoritative `90×4` and `V56` `[7,8,9,10,15,16,17,18]`**, mechanically verifiable:
```
set(Cal_s) ∩ set(Val_s) == ∅  per s
set(Cal_s ∪ Val_s) ∩ set(V55_90flat_s) == ∅  per s  (V55 flat = 120 frames/source)
set(Cal_s ∪ Val_s) ∩ {7,8,9,10,15,16,17,18} == ∅  per s
frame_id ∈ [0, F_s-1], F=2130/5125/5513, pairs_per_frame 256, BLOCK_LENGTH 1024
```
Frozen sets are unified across strata:
- `Cal` = `19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50` (32 frames, 8 blocks×4, 8192 pairs/source)
- `Val` = `77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108` (32, 8×4, 8192)
Registries `v57_calibration_registry.json` and `v57_validation_registry.json` plus `v57_manifest.json` SHALL persist `selected_frame_ids, blocks, pairs, F, K, provenance, zero_overlap_proofs` and SHALL be immutable after creation; any violation SHALL yield `V57_EVIDENCE_INVALID` with zero channel estimation.

### Requirement: V57 Calibration Joint Count and Conditional Entropy and Leakage Recomputation (Not Reusing V25 184/190/192)
The change SHALL estimate per-source on `Cal` (8192 pairs, `F03 5+5 natural` `U1=sym>>5, U2=sym&31`):
```
C_ab = bincount2d(a_cal,b_cal) 1024×1024, N_b=Σ_a C_ab, P(b)=N_b/N_cal
P_hat(a|b)=C_ab/N_b if N_b>0 else 1/1024 (column-normalized, log clamp 1e-15 only for NLL)
H(A|B)=-Σ_b P(b) Σ_a P_hat log2 P_hat
P_hat(u1|b)=Σ_{u2} P_hat(32*u1+u2|b), H(U1|B)=-Σ_b P(b) Σ_{u1} P_hat(u1|b) log2 P_hat(u1|b)
H(U2|B,U1)=H(A|B)-H(U1|B) with chain-rule check |H-H1-H2|<1e-9 else EVIDENCE_INVALID
```
and SHALL recompute source-adaptive leakage with `f_target=1.3, n=1024, tag=64, log2q=5`:
```
m_total = floor((1.3*1024*H -64)/5), m1=round(m_total*H1/H) (Python round half even), m2=m_total-m1,
leak=5*m_total+64, f_eff=leak/(1024*H), Δ_m=m_total-m_total_V25ref, Δ_leak=5*Δ_m
```
`V25` `m2 184/190/192` and `m1=16` SHALL be marked deprecated and SHALL NOT be reused as new-domain budget; new `m_total/m1/m2` are for reporting and `V58` planning only and SHALL NOT be instantiated as new matrices in `V57`.

### Requirement: V57 Validation Four Gates Per Source (No Overall Averaging)
The change SHALL validate per-source on `Val` (8192 pairs) using `P_cal` from `Cal`:
- **V1 NLL**: `NLL_val=mean_{Val}[-log2 P_cal(a|b) clamp1e-15]` bits/symbol; `PASS_V1 = (NLL_val <= H_cal+0.50) && (NLL_val<=1.50) && (NLL_val < NLL_V25_on_Val -5.0)` where `NLL_V25_on_Val` is `mean_{Val}[-log2 P_V25(a|b)]` from `channel_counts.npz`.
- **V2 MAP accuracy**: `acc_val=mean_{Val}[a==argmax P_cal(a|b)]`; `PASS_V2=(acc_val>=0.60) && (acc_val>=acc_cal-0.10)`.
- **V3 zero-coverage**: `q_mass=Σ_{C_ab_cal==0} P_val_emp(a,b)` with `P_val_emp=C_ab_val/N_val`; `PASS_V3=(q_mass<=0.20)`.
- **V4 entropy stability**: `H_val=H(A|B)_Val`; `PASS_V4=(|H_val-H_cal|<=0.20) && (|H_val-H_cal|/H_cal<=0.25)`.
`PASS_s = PASS_V1&&V2&&V3&&V4 && zero_overlap_s && counts_valid_s` SHALL be judged **per source separately, without overall averaging**.

### Requirement: V57 Three-Source Independent Verdict and V58 Gate (All-Pass Only)
The overall verdict SHALL be exclusive, priority-ordered:
```
if not zero_overlap_all or not counts_valid_all or |H-H1-H2|>=1e-9 → V57_EVIDENCE_INVALID
elif PASS_1M && PASS_1p5M && PASS_2M → V57_CHANNEL_RECHARACTERIZATION_PASS
else → V57_CHANNEL_RECHARACTERIZATION_FAIL (including MIXED_BY_SOURCE per-source list)
```
Only `V57_CHANNEL_RECHARACTERIZATION_PASS` (all 3 sources `PASS_s`) SHALL allow a successor `V58` to freeze new `TEST` blocks (30/source, zero overlap with `Cal/Val` and `V55 90`, unrevealed) and proceed through `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT dual review + EXECUTE_AUTH` to decoder TEST. `FAIL/INVALID` SHALL remain `V57_CHANNEL_RECHARACTERIZATION_PENDING` and SHALL NOT enter decoder.

### Requirement: V57 Decoder-Forbidden Guard
The change SHALL remain `V57_CHANNEL_RECHARACTERIZATION_PENDING / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ8/decoder 90/1.0/poly37/m2/leak/prior`, no `.../v57_*/run_01` creation, no rerun on the original `V55 90`, `py_compile` PASS, `Cal∩Val==∅ && Cal∪Val∩V55==∅ && ∩V56==∅` verified, `|H-H1-H2|<1e-9` verified, `git diff -- src/ ==0` and `git diff -- comparison_bench/src/comparison_bench/formal_ir/ ==0`, and `V25 184/190/192` deprecation explicitly stated. No `bin_width/dimension/pairing` grid search (`rg "grid" 0 hits`).

### Requirement: V57 Original 90 Permanent Ban and Freshness Boundary
`v55_authoritative_registry.json`'s `90×4` frames (already revealed `0/90`) SHALL remain permanently banned from any corrected-pipeline rerun. `Cal/Val` and any future `V58 TEST` are derived from the same three `20260123/20260107` `pairs.parquet` already used for diagnosis; therefore the change SHALL explicitly state in report and spec that `V57` does not claim fully independent cross-session qualification and that true cross-session qualification rests with `V58` new `TEST` (fresh `TEST` is `fresh within-session confirmation` until a new acquisition, boundary explicitly declared). `V54`'s `43/45` validity in the `2026-01-21` domain and the located domain incompatibility SHALL be preserved as not falsifying the code family.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain; `V57` adds channel recharacterization without modifying `V56` terminal.

## REMOVED Requirements

None. `V25` `184/190/192` remains as historical reference only, deprecated for new-domain budgeting.
