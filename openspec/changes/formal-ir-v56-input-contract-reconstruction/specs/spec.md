# Delta Spec: formal-ir-v56-input-contract-reconstruction

## ADDED Requirements

### Requirement: V56 Phase 0 — V56D4 Independent Pre-RESULT Review Consolidation
The change SHALL first consolidate `V56D4` via an **independent pre-RESULT review** (independent thread/reviewer, not self-review) that verifies `HEAD == origin/formal-ir-mainline == implementation SHA`, `ACCEPTED_PLAN_SHA` re-derived from `git log`/`cycle_state.yaml` with `rg <stale SHA> 0 hits`, no `run_01` under target output root, `py_compile` + critical tests PASS, and records `implementation SHA / execution SHA (N/A decoder-free)` in `v56d4_low_dim_decomposition.json:provenance` and the report header. The review SHALL solidify `CE/accuracy` as primary, `I32` as auxiliary only, `first_drop = U1U2_consistency`, and terminal `INCONCLUSIVE_MIXED_SIGNAL` (not forced binary), and SHALL explicitly state that **I32 alone SHALL NOT determine attribution** (finite-sample bias `~0.47 bits` at `1024 samples / 1024 bins` noted). Wording freeze: "未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）".

### Requirement: V56 Phase A — Function-by-Function V13 Contract Replay (Decoder-Free)
The diagnostic SHALL replay **the same fixed calibration frames** (pre-registered, e.g., `frames [7,8,9,10,15,16,17,18]` consistently across 1M/1p5M/2M) through **two materializers simultaneously** (decoder-free):
- **Authoritative V13 materializer**: `workspace/v13r3fresh_20260816` verified `read_ttbin_events → compute_cross_correlation_histogram(bin100/max819200/n16384, lag=t_B-t_A) → pairing nearest → delay application → frame_start/period 204800 floor_div → bin 200ps → legacy_v1 symbol 1024 → F03 5+5 U1/U2` read live from `sidecars/*/sidecar_meta.json: used_params` + `build_manifest.json` (not hard-coded).
- **Current V55 intake materializer**: `comparison_bench/outputs_comparison/v55_intake_20260828` single-point `200ps legacy_v1 nearest 1024` (or its persisted `pairs.parquet` lineage, `INCOMPLETE` if missing).
Stage-by-stage comparison SHALL cover `raw event/channel selection (channel 1/5, other<20%) → pairing index/Δt (Δt = t_B - t_A) → delay sign and application position → frame-start/period/floor-div (frame_start_ps, period 204800, before/after pair index) → bin index → 1024 symbol → U1/U2`, with `array_equal` / `median Δt` / `occupancy` per stage, and SHALL persist **the first divergent stage and row-level samples** (e.g., 5 rows `pair_idx,t_A,t_B,Δt,bin_A,bin_B,sym_A,sym_B,U1,U2`) to find the first array divergence.

### Requirement: V56 Phase B — Single-Point Fix From V13 Authoritative Contract
If Phase A finds a code/contract divergence, the change SHALL fix **only that one location**, SHALL NOT search over `delay / bin_width / mapping / frame anchor` candidates or perform grid search, and the fix value SHALL come from the **V13 authoritative contract** (live `sidecar` or `ttbin_pipeline` authoritative implementation). A **three-way byte/array-level comparison** `old / current / corrected` SHALL be persisted (pre-divergence stages `array_equal PASS`, post-divergence stages flip), and SHALL NOT modify `prior / H1 / Lane C / incremental matrices H_inc1/2 / decoder`.

### Requirement: V56 Phase C — Decoder-Free Calibration Acceptance on New Frames (Per-Source)
The diagnostic SHALL use **new calibration frames not in the V55 90-block (`v55_authoritative_registry.json`) and not in existing `fit=[7,8,9,10]/val=[15,16,17,18]`** (both `set ∩ ==∅` mechanically verified, `frame_id ∈ [0,F-1]`, `pairs_per_frame 256`). For each source (1M/1p5M/2M) separately it SHALL verify:
- **Timing/routing contract complete** and **V13 vs corrected stage-wise identical** (`array_equal PASS` across the 7 stages on the same new `ttbin` batch; `timing_contract_verified` requires real `TimeTagger` peak `σ 50-150ps` and `|peak - delay_used|<50ps` + `sign` + `gate/threshold/frame_start` landed; missing → `EVIDENCE_INCOMPLETE`);
- **A==B >60%** (primary gate, `rate_eq = mean(a==b)` on `8-16` frames);
- **Validation CE/accuracy significantly recovered** (`fit 4→val 4` same split, `CE_U1/U2` `13-16→<5`, `acc_U1/U2` `0.30-0.46→>60%` toward V13 `CE 0.19-0.91 acc 0.74-0.99`; `>60%` is gate, rest is consistency description);
- **NLL / q_mass for consistency only** (from `channel_counts.npz` `P(A|B)`, `NLL` and `q_mass_on_p_zero` reported for direction, not hard-gated).
**All three sources SHALL pass**; any source failure SHALL terminal `V56_INPUT_CONTRACT_UNRESOLVED` and halt.

### Requirement: V56 Phase D — 5-Way Terminal (Mutually Exclusive)
The change SHALL shunt to exactly one of:
- `V56_INPUT_CONTRACT_RECOVERED` — iff Phase C passes on all 3 sources;
- `V56_TRUE_SESSION_DOMAIN_SHIFT` — iff no single-point error or corrected still low and U1U2 still low with high NLL/q_mass and no single pairing/frame point;
- `V56_MIXED_BY_SOURCE` — iff per-source decisions differ;
- `V56_INPUT_CONTRACT_UNRESOLVED` — iff any source fails Phase C;
- `V56_EVIDENCE_INVALID` — iff integrity/guard/zero-overlap/rank/nested fails or provenance untraceable.
Per-source `MIXED_BY_SOURCE` SHALL be supported. **Only `RECOVERED` SHALL allow a successor decoder TEST** (new OpenSpec `V57` with `QUALIFICATION_PLAN_READY` + `EXECUTE_AUTH` bound to new SHA + new TEST registry).

### Requirement: V56 Boundary — V55 90 Permanent Ban and Freshness Scope
The `V55` authoritative `90-block` (`v55_authoritative_registry.json` 30/source, `0/90` exposed) SHALL remain **permanently banned** (no corrected pipeline rerun). Remaining frames of the same new sessions may serve as **fresh within-session confirmation** (new blocks zero-overlap with verification frames), but **SHALL NOT be claimed as fully independent cross-session qualification** because the sessions have undergone multiple `V55` diagnostic rounds; **true qualification SHALL be placed at `V57`** (new acquisition session) and SHALL require a new OpenSpec and independent authorization.

### Requirement: V56 Decoder-Forbidden Until C Passes
The change SHALL remain `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` (`rg "decode_" 0 hits`, zero change to `H1/Lane C/H_inc1/2/Δ8/decoder/m2/leak/prior`, no `.../v56_*/run_01` creation, `py_compile` PASS, `fit∩val==∅` and `set(new)∩set(90)==∅ && ∩set(D4 fit/val)==∅` verified). No production decoder execution SHALL be authorized until Phase C passes; successor `V57` decoder TEST SHALL require a new OpenSpec and `Pre-EXECUTE` / `Pre-RESULT` dual review.

### Requirement: V56 Wording and I32 Auxiliary Freeze
Any claim about 1024-state permutation SHALL be phrased as "未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）" and SHALL NOT be phrased as "已排除任意1024置换". `I32` (32-state `I(U1)/I(U2)`) SHALL be auxiliary only, with finite-sample bias noted (`~0.47 bits` at `N=1024`), and SHALL NOT alone determine `pairing/frame` vs `domain-shift` attribution; shunt SHALL be jointly on `A==B>60%` + `validation CE/acc` + `first_drop` + `V13/corrected` stage-wise identity.

### Requirement: V56 V13 Implementation Reuse (No Re-invention)
The diagnostic SHALL reuse the **V13 verified** `src/qkd_io/ttbin_pipeline.{read_ttbin_events,compute_cross_correlation_histogram}` frozen baseline (read-only) and the `V13` sidecar `used_params` live read, SHALL NOT re-invent an approximate materializer, and SHALL record `HEAD / implementation SHA / data SHA / frame_ids / array_equal / provenance` in `verification_manifest.json` and `calibration_verification.json`.

## MODIFIED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` and `QUALIFICATION_PLAN_READY` guards remain; `V56D4` terminal remains `INCONCLUSIVE_MIXED_SIGNAL` and is not overwritten.

## REMOVED Requirements

None. No prior requirement is removed; `V56D4` `fit/val` pre-registration and 6-rule decision order are retained.
