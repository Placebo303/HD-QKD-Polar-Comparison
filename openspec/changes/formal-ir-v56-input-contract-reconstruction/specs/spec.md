# Delta Spec: formal-ir-v56-input-contract-reconstruction

## ADDED Requirements

### Requirement: V56 Phase 0 — V56D4 Independent Pre-RESULT Review Consolidation
The change SHALL first consolidate `V56D4` via an **independent pre-RESULT review** (independent thread/reviewer, not self-review) that verifies `HEAD == origin/formal-ir-mainline == implementation SHA`, `ACCEPTED_PLAN_SHA` re-derived from `git log`/`cycle_state.yaml` with `rg <stale SHA> 0 hits`, no `run_01` under target output root, `py_compile` + critical tests PASS, and records `implementation SHA / execution SHA (N/A decoder-free)` in `v56d4_low_dim_decomposition.json:provenance` and the report header. The review SHALL solidify `CE/accuracy` as primary, `I32` as auxiliary only, `first_drop = U1U2_consistency`, and terminal `INCONCLUSIVE_MIXED_SIGNAL` (not forced binary), and SHALL explicitly state that **I32 alone SHALL NOT determine attribution** (finite-sample bias `~0.47 bits` at `1024 samples / 1024 bins` noted). Wording freeze: "未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）".

### Requirement: V56 Phase A — Function-by-Function V13 Contract Replay (Decoder-Free)
The diagnostic SHALL replay **the same fixed calibration frames** (pre-registered, e.g., `frames [7,8,9,10,15,16,17,18]` consistently across 1M/1p5M/2M) through **two materializers simultaneously** (decoder-free):
- **Authoritative V13 materializer**: `workspace/v13r3fresh_20260816` verified `read_ttbin_events → compute_cross_correlation_histogram(bin100/max819200/n16384, lag=t_B-t_A) → pairing nearest → delay application → frame_start/period 204800 floor_div → bin 200ps → legacy_v1 symbol 1024 → F03 5+5 U1/U2` read live from `sidecars/*/sidecar_meta.json: used_params` + `build_manifest.json` (not hard-coded).
- **Current V55 intake materializer**: `comparison_bench/outputs_comparison/v55_intake_20260828` single-point `200ps legacy_v1 nearest 1024` (or its persisted `pairs.parquet` lineage, `INCOMPLETE` if missing).
Stage-by-stage comparison SHALL cover `raw event/channel selection (channel 1/5, other<20%) → pairing index/Δt (Δt = t_B - t_A) → delay sign and application position → frame-start/period/floor-div (frame_start_ps, period 204800, before/after pair index) → bin index → 1024 symbol → U1/U2`, with `array_equal` / `median Δt` / `occupancy` per stage, and SHALL persist **the first divergent stage and row-level samples** (e.g., 5 rows `pair_idx,t_A,t_B,Δt,bin_A,bin_B,sym_A,sym_B,U1,U2`) to find the first array divergence.

### Requirement: V56 Phase B — Single-Point Fix From V13 Authoritative Contract (Wrapper Only)
If Phase A finds a code/contract divergence, the change SHALL fix **only that one location**, SHALL NOT search over `delay / bin_width / mapping / frame anchor` candidates or perform grid search, and the fix value SHALL come from the **V13 authoritative contract** (live `sidecar` or `ttbin_pipeline` authoritative implementation **read-only**). The fix SHALL be confined to the **V56 wrapper/materializer** (`comparison_bench/.../v56_*` or `replay/verify` script parameter layer) and **SHALL NOT modify `src/` baseline** (`src/qkd_io/ttbin_pipeline.py` etc. frozen, `git diff -- src/ ==0` verifiable). A **three-way byte/array-level comparison** `old / current / corrected` SHALL be persisted (pre-divergence stages `array_equal PASS`, post-divergence stages flip), and SHALL NOT modify `prior / H1 / Lane C / incremental matrices H_inc1/2 / decoder`.

### Requirement: V56 Phase C — Decoder-Free Calibration Acceptance on New Frames (Per-Source, Hard Gates)
The diagnostic SHALL use **new calibration frames not in the V55 90-block (`v55_authoritative_registry.json`) and not in existing `fit=[7,8,9,10]/val=[15,16,17,18]`** (both `set ∩ ==∅` mechanically verified, `frame_id ∈ [0,F-1]`, `pairs_per_frame 256`) and SHALL **pre-register per-source CE thresholds** (`CE_V13ref_U1/U2` and `CE_thresh = min(0.5*CE_current, CE_V13ref+1.0)`) in `verification_manifest.json:pre_registered_thresholds` (immutable post-registration). For each source (1M/1p5M/2M) **separately (no overall平均)** it SHALL verify:
- **Timing/routing contract complete** (pre-guard; `timing_contract_verified` requires real `TimeTagger` peak `σ 50-150ps` and `|peak - delay_used|<50ps` + `sign` + `gate/threshold/frame_start` landed; missing → `EVIDENCE_INCOMPLETE`);
- **contract_equivalent (hard evidence, gate 1)**: **V13 authority vs corrected stage-wise element-wise identical** across all 7 stages `raw/channel → pairing/Δt → delay/position → frame-start/period/floor-div → bin → 1024 sym → U1/U2` on the same new `ttbin` batch (`np.array_equal PASS` per stage; any `False` → `contract_equivalent=False`);
- **distribution_compatible (hard gates, gate 2, per-source)**: SHALL satisfy **all three** simultaneously:
  1. `A==B >60%` (`rate_eq = mean(a==b)` on `8-16` frames `>60%`);
  2. `validation accuracy ≥60%` (`fit 4→val 4` same split, `acc_U1 ≥60%` and `acc_U2 ≥60%`, `acc = mean(a==argmax P_fit)`);
  3. `validation CE pre-registered upper bound` (`CE_U1 ≤ min(0.5*CE_current_U1, CE_V13ref_U1+1.0)` **and** `CE_U2 ≤ min(0.5*CE_current_U2, CE_V13ref_U2+1.0)`; `CE = E[-log2 P_fit]`; `CE_current` is the `V56D4` baseline `13-16`, `CE_V13ref` is the `V13` healthy reference `0.19-0.91` per source, fallback `0.91+1.0=1.91`; relative at least 50 % decrease **and** not higher than V13+1 bit, taking the stricter).
- **NLL / q_mass for consistency only** (from `channel_counts.npz` `P(A|B)`, `NLL` and `q_mass_on_p_zero` reported for direction, not hard-gated).
Per-source verdict `pass_s = timing_complete && routing_complete && contract_equivalent && distribution_compatible` SHALL be recorded; **no overall averaging SHALL be used**.

### Requirement: V56 Phase D — 5-Way Terminal (Mutually Exclusive, Priority Ordered, Non-Subjective)
The change SHALL define **contract_equivalent** as in Phase C gate 1 (V13 authority vs corrected 7-stage element-wise identical, hard evidence) and **distribution_compatible** as in Phase C gate 2 (per-source `A==B>60%` and `acc≥60%` and `CE≤min(0.5*CE_current, V13ref+1.0)` pre-registered upper bound, not overall averaging), SHALL first compute **per-source shunt_s** (`UNRESOLVED_s` iff `contract_equivalent_s==False` or TTBin unavailable; `RECOVERED_s` iff contract true and distribution true; `DOMAIN_SHIFT_s` iff contract true but distribution false), and SHALL shunt to **exactly one** of the following by **priority order** (highest first, mutually exclusive, non-subjective):
- `V56_EVIDENCE_INVALID` — iff integrity/guard/zero-overlap/rank/nested fails or provenance untraceable or `fit∩val≠∅` or `set(new)∩set(90)≠∅` or `∩set(D4 fit/val)≠∅` or timing forged/missing (highest priority);
- `V56_MIXED_BY_SOURCE` — iff per-source `shunt_s` not all equal (sources fall into different categories, e.g., 1M RECOVERED_s vs 2M DOMAIN_SHIFT_s vs 1p5M UNRESOLVED_s; includes contract or distribution heterogeneity; heterogeneous divergence captured before uniform);
- `V56_INPUT_CONTRACT_RECOVERED` — iff **all 3 sources** `contract_equivalent==True` **and** `distribution_compatible==True` (7 stages consistent and statistics compatible per-source hard gates → recoverability proven);
- `V56_TRUE_SESSION_DOMAIN_SHIFT` — iff **all 3 sources** `contract_equivalent==True` **and** **all 3 sources** `distribution_compatible==False` (7 stages consistent but statistics uniformly fail → true domain shift; high NLL/q_mass is consistency evidence only);
- `V56_INPUT_CONTRACT_UNRESOLVED` — iff **all 3 sources** uniformly `contract_equivalent==False` or V13 authoritative path uniformly cannot be reproduced (`INCOMPLETE_TTBin_UNAVAILABLE`) (uniform divergence not captured by MIXED; heterogeneous divergence already captured as MIXED).
Per-source `MIXED_BY_SOURCE` SHALL be supported with per-source `shunt_s` recorded. **Only `RECOVERED` SHALL allow a successor decoder TEST** (new OpenSpec `V57` with `QUALIFICATION_PLAN_READY` + `EXECUTE_AUTH` bound to new SHA + new TEST registry). The fix SHALL remain in V56 wrapper/materializer (`git diff -- src/ ==0`).

### Requirement: V56 Boundary — V55 90 Permanent Ban and Freshness Scope
The `V55` authoritative `90-block` (`v55_authoritative_registry.json` 30/source, `0/90` exposed) SHALL remain **permanently banned** (no corrected pipeline rerun). Remaining frames of the same new sessions may serve as **fresh within-session confirmation** (new blocks zero-overlap with verification frames), but **SHALL NOT be claimed as fully independent cross-session qualification** because the sessions have undergone multiple `V55` diagnostic rounds; **true qualification SHALL be placed at `V57`** (new acquisition session) and SHALL require a new OpenSpec and independent authorization.

### Requirement: V56 Decoder-Forbidden Until C Passes and Wrapper-Only Fix
The change SHALL remain `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` (`rg "decode_" 0 hits`, zero change to `H1/Lane C/H_inc1/2/Δ8/decoder/m2/leak/prior`, no `.../v56_*/run_01` creation, `py_compile` PASS, `fit∩val==∅` and `set(new)∩set(90)==∅ && ∩set(D4 fit/val)==∅` verified, **`git diff -- src/ ==0` — fix confined to V56 wrapper/materializer**). No production decoder execution SHALL be authorized until Phase C passes (`RECOVERED`); successor `V57` decoder TEST SHALL require a new OpenSpec and `Pre-EXECUTE` / `Pre-RESULT` dual review.

### Requirement: V56 Wording and I32 Auxiliary Freeze
Any claim about 1024-state permutation SHALL be phrased as "未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）" and SHALL NOT be phrased as "已排除任意1024置换". `I32` (32-state `I(U1)/I(U2)`) SHALL be auxiliary only, with finite-sample bias noted (`~0.47 bits` at `N=1024`), and SHALL NOT alone determine `pairing/frame` vs `domain-shift` attribution; shunt SHALL be jointly on `A==B>60%` + `validation CE/acc` + `first_drop` + `V13/corrected` stage-wise identity.

### Requirement: V56 V13 Implementation Reuse (No Re-invention, Read-Only)
The diagnostic SHALL reuse the **V13 verified** `src/qkd_io/ttbin_pipeline.{read_ttbin_events,compute_cross_correlation_histogram}` frozen baseline (**read-only**, `git diff -- src/ ==0`) and the `V13` sidecar `used_params` live read, SHALL NOT re-invent an approximate materializer, SHALL confine any fix to the V56 wrapper/materializer, and SHALL record `HEAD / implementation SHA / data SHA / frame_ids / array_equal / per-stage provenance / pre_registered CE thresholds` in `verification_manifest.json` and `calibration_verification.json`.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` and `QUALIFICATION_PLAN_READY` guards remain; `V56D4` terminal remains `INCONCLUSIVE_MIXED_SIGNAL` and is not overwritten.

## REMOVED Requirements

None. No prior requirement is removed; `V56D4` `fit/val` pre-registration and 6-rule decision order are retained.
