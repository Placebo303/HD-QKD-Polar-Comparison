# V56 FINAL REVIEW NOTE — V56_DIAGNOSIS_RESULT_ACCEPTED / V56_TRUE_SESSION_DOMAIN_SHIFT

**Date**: 2026-08-29
**HEAD**: `4e1e0bfc5e4b7805e0790e96a96f1d43fd58e0e2`
**origin/formal-ir-mainline**: `4e1e0bfc5e4b7805e0790e96a96f1d43fd58e0e2`
**implementation SHA**: `4e1e0bfc5e4b7805e0790e96a96f1d43fd58e0e2`

Triple SHA precise: `HEAD == origin/formal-ir-mainline == implementation SHA == 4e1e0bfc` ✔

## Evidence binding (R4 additive, no R2/R3/code overwrite)

- `verification_manifest_r4.json` / `calibration_verification_r4.json` additive on `4e1e0bfc` — prior `verification_manifest.json` / `calibration_verification.json` / R2/R3 retained.
- `src/` zero diff (`git diff -- src/ ==0`), `rg decode_ 0 hits`, `py_compile` PASS.

## Contract equivalence (T-AUTH dual-true, 3-source × 7-stage)

- T-AUTH-1 current vs parquet 100% ✔, T-AUTH-2 V13 vs persisted 100% ✔, sidecar lineage OK per source.
- `contract_equivalent == true` on new frames [0,1,2,3]/[11,12,13,14] (per-source 7-stage `array_equal` true: raw_channel_timetags → absolute_bin_indices → physical_frame_match → pair_sequence → logical_frame_grouping → symbol_1024 → U1U2).
- Per-source 2048 pairs, per-frame 256 via `start=frame_id*256`, `ENGINEERING_INVALID_FRAME_ID_SEMANTICS` retained, `204800ps` pairing scale.

## Distribution incompatibility (uniform DOMAIN_SHIFT, not materializer error)

- New-calibration (fit→val) per source: A==B 27-39%, acc U1/U2 29-43%, CE 13-16 — far above V13 health CE 0.19-0.91 / acc 74-99%, uniformly `distribution_compatible == false`.
- V55 `0/90` is channel mismatch, V56 new-frame result is **true session domain shift** — corrected materializer restores contract but statistics remain incompatible.
- Per-source `shunt_s == DOMAIN_SHIFT_s` uniform → `overall == V56_TRUE_SESSION_DOMAIN_SHIFT` (5-way priority `EVIDENCE_INVALID > MIXED > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`).

## Lifecycle end state

- `lifecycle`: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — `V56_DIAGNOSIS_RESULT_ACCEPTED`.
- `DECODE_FORBIDDEN` retained. Next step requires **new-session channel re-characterization** (new acquisition session, re-estimate H(U|B), prior, m_total, gate/threshold per session) — **not direct V57 decoder**.

## Boundary

- V55 90-block permanently banned (disclosed 0/90, no replay).
- Same-session remaining frames only fresh within-session confirmation, not cross-session qualification; true qualification requires new session (V57 candidate only after re-characterization).

*No code/old-evidence change; additive R4 only; ordinary push to `formal-ir-mainline`.*
