# V56 Input Contract Reconstruction Report — TEMPLATE (fill after Phase C/D)

**Placeholders — data to be filled from verification_manifest.json / calibration_verification.json**

## Provenance
- HEAD / implementation SHA: _TBD_ (`git rev-parse HEAD`)
- origin/formal-ir-mainline: _TBD_
- ACCEPTED_PLAN_SHA: `97602558a8047a1c3b30c2cddd70fd0ef3e2ed46` (`rg <stale SHA> 0 hits` verified)
- data SHA: `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)
- lifecycle: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — zero execution until V57

## Phase 0 — V56D4 consolidation
- CE/acc primary, I32 auxiliary only (bias ~0.47 bits at 1024/1024), first_drop=`U1U2_consistency`, overall=`INCONCLUSIVE_MIXED_SIGNAL`
- Wording freeze: “未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）”

## Phase A — Seven-stage replay (same fixed frames [7,8,9,10,15,16,17,18])
| stage | V13 | current | array_equal | delta | sample_rows |
|---|---|---|---|---|---|
| raw_event_channel_selection | _ | _ | _ | _ | _ |
| pairing_index_dt | _ | _ | _ | _ | _ |
| delay_sign_position | _ | _ | _ | _ | _ |
| frame_start_period_floor_div | _ | _ | _ | _ | _ |
| bin_index | _ | _ | _ | _ | _ |
| symbol_1024 | _ | _ | _ | _ | _ |
| U1U2 | _ | _ | _ | _ | _ |
- first_divergent_stage: _TBD_ (row sample pair_idx,t_A,t_B,Δt,bin_A,bin_B,sym_A,sym_B,U1,U2 top 5)
- per-source details in `verification_manifest.json:per_stage_per_source`

## Phase B — Single-point wrapper fix (wrapper-only, src/ unchanged)
- divergent_field: _TBD_ (e.g., delay sign / frame_start null vs peak_center / floor_div / bin / symbol)
- fix value source: V13 sidecar `used_params` live read (not hand-filled), wrapper materializer only (`git diff -- src/ ==0`)
- three-way old/current/corrected: _TBD_ (array_equal flip after first divergent stage, prior stages remain pass)
- prior/H1/Lane C/H_inc/decoder unchanged

## Phase C — Decoder-free calibration acceptance (new frames [0,1,2,3,11,12,13,14], per-source, hard gates)
Pre-registered thresholds (per source, immutable):
- CE_thresh = min(0.5*CE_current, CE_V13ref+1.0) where CE_current 13-16, CE_V13ref 0.19-0.91

| source | contract_equivalent (7-stage) | A==B | acc_U1 | acc_U2 | CE_U1 | CE_thresh_U1 | CE_U2 | CE_thresh_U2 | NLL | q_mass | pass_s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | _ | _ (>60% ?) | _ (≥60% ?) | _ | _ (≤thresh ?) | _ | _ | _ | _ | _ | _ |
| 1p5M | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ |
| 2M | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ |
- timing_contract_verified: _TBD_ (σ 50-150ps, |peak-delay|<50ps, sign, gate/threshold/frame_start landed; missing → EVIDENCE_INCOMPLETE, no RECOVERED)
- routing: `channel 1/5` present, `other<20%` (ratio report only)
- zero-overlap: `set(new)∩set(V55 90)==∅` and `∩set(D4 fit/val)==∅` verified
- NLL/q_mass consistency only (not hard-gated)

## Phase D — Five-way terminal (priority EVIDENCE_INVALID > MIXED_BY_SOURCE > RECOVERED > DOMAIN_SHIFT > UNRESOLVED)
- shunt_per_source: _TBD_ (RECOVERED_s / DOMAIN_SHIFT_s / UNRESOLVED_s)
- overall: _TBD_ ∈ {V56_EVIDENCE_INVALID, V56_MIXED_BY_SOURCE, V56_INPUT_CONTRACT_RECOVERED, V56_TRUE_SESSION_DOMAIN_SHIFT, V56_INPUT_CONTRACT_UNRESOLVED}
- Only RECOVERED allows V57 decoder TEST (new OpenSpec + QUALIFICATION_PLAN_READY + EXECUTE_AUTH + new SHA); others remain PLAN_CANDIDATE / VERIFICATION_ONLY.

## Boundary
- V55 90-block `v55_authoritative_registry.json` (30/source, 0/90 exposed) permanently banned.
- Same-session remaining frames only fresh within-session confirmation (zero-overlap new block), not fully independent cross-session qualification.
- True qualification at V57 (new acquisition session).

## Checks
- `py_compile` pass, `rg "decode_" 0 hits`, `git diff -- src/ ==0`, `fit∩val==∅`, zero-overlap pass, `I32` auxiliary, contract_equivalent (7-stage array_equal) hard evidence, distribution_compatible (`A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current,V13ref+1)` per source) hard gate, three-way manifest landed, first_divergent_stage located, report vs json consistent.

*Fill _TBD_ after replay/verify scripts produce json.*
