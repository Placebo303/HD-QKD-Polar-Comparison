# V63 Delivery — PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED

**Date**: 2026-08-30
**Predecessor Plan SHA**: 5602f11c65b2590254e89a1b95c7384f4bbbfd38 (HEAD == origin/formal-ir-mainline at start)
**Data SHA**: 84d62779 (84d62779603e62de50ded5182ed65b65d3dc6084, d=1024 bw=200 pairing=nearest rule=legacy_v1)
**Lifecycle**: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED — decoder-free spike only, no real decoder/run_01/formal PA/90-block execution

## R63 7-Phase Completion

| Phase | Item | Status |
|-------|------|--------|
| 1 | Revise four workpieces R63-01 32*u1+u2+exact, R63-02 NbLdpcShellResult not change signature, R63-03 smoke INTEGRATION_REPLAY_SMOKE 90 fresh zero overlap, R63-04 DOMAIN_CALIBRATION_REQUIRED | DONE — proposal/design/tasks/specs all amended |
| 2 | Shell audit 10 items file/function/signature → shell_api_audit.md | DONE — 10 items PASS, read-only |
| 3 | Generate 9-block replay registry + 90-block fresh candidate registry, read-only frame IDs/symbols, zero overlap | DONE — v63_smoke_registry.json 9, v63_dev_registry.json 90, zero_overlap_proof.json PASS |
| 4 | Prototype workspace/v63_shell_spike/ fake u1/u2→full symbol, three-tier leak tag single count, PA proxy, Polar leak_EC reject | DONE — 4 modules |
| 5 | T1-T12 tests all green | DONE — 12 passed |
| 6 | Independent read-only review → REVIEW_VERDICT.md PASS | DONE |
| 7 | Atomic commit push new Plan SHA + DELIVERY.md | THIS FILE |

## Artifacts (Allowed Files Only)

- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/proposal.md` (R63 revisions)
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/design.md`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/tasks.md`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/specs/spec.md`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/shell_api_audit.md`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/v63_smoke_registry.json`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/v63_dev_registry.json`
- `openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/REVIEW_VERDICT.md`
- `workspace/v63_shell_spike/nbldpc_shell_adapter_fake.py`
- `workspace/v63_shell_spike/leakage.py`
- `workspace/v63_shell_spike/pa_proxy.py`
- `workspace/v63_shell_spike/domain_check.py`
- `workspace/v63_shell_spike/shell_api_audit.md`
- `workspace/v63_shell_spike/registries/v63_smoke_registry.json`
- `workspace/v63_shell_spike/registries/v63_dev_registry.json`
- `workspace/v63_shell_spike/registries/zero_overlap_proof.json`
- `workspace/v63_shell_spike/tests/test_v63_spike.py`
- `workspace/v63_shell_spike/REVIEW_VERDICT.md`
- `docs/research_cycles/v63/shell_api_audit.md`
- `docs/research_cycles/v63/v63_smoke_registry.json`
- `docs/research_cycles/v63/v63_dev_registry.json`
- `docs/research_cycles/v63/zero_overlap_proof.json`
- `docs/research_cycles/v63/REVIEW_VERDICT.md`
- `docs/research_cycles/v63/DELIVERY.md` (this file)

**Forbidden**: `src/`, `experiments/`, `tools/`, `comparison_bench/outputs_comparison/formal_ir_methods/v63*/run_01` — zero mutation (git diff -- src/ ==0 etc verified).

## Production Implementation Packet (Precise, Next Stage Requires EXECUTE_AUTH)

> This packet is the exact implementation contract for the future production stage (not executed now). It is decoder-free authorized only after independent plan ACCEPT + explicit EXECUTE_AUTH + HEAD binding to new Plan SHA.

### 1. File Map (to be created only after ACCEPT + EXECUTE_AUTH)

- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py` — real adapter (import V54 frozen, not fake)
  - `class NbLdpcShellAdapter(IRMethod):`
    - `__init__(self, source: str, counts: np.ndarray, field: GF2mField, H_base: np.ndarray, H_joint1: np.ndarray, H_total: np.ndarray)`
    - `run(self, batch: FrameBatch, source: str) -> ShellResult` where `ShellResult` wraps `IRRunResult` (frozen) + `reconciled_symbols` (full 0..1023 via 32*u1+u2), `accepted`, `exact`, `syndrome_ok`, `tag_ok`, `undetected`, `actual_disclosure_bits` (per frame 1064/1094/1104 etc by stage_used), `decoder_calls` (2-4 breakdown), `runtime_s`, `stage_used` enum {base,delta8,delta16}
  - Internal imports: `from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import construct_h_inc, construct_h_joint1, construct_h_total, leak_for, compute_l2_tag, CallAccounting, BLOCK_WINDOWS` + `from formal_ir.v38_architecture_triage import construct_lane_c_prototype` + `from formal_ir.v35_algorithm_development import compute_tag_64`
  - Implements L1-APP: `p_i(u1)=P(U1|B_i) -> BP=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs -> q=softmax(BP) -> P_i(U2)=sum q*P(U2|B,u1)` (TRAIN prior V25), then `base(H_base)->verify_base->stage1(H_joint1)->verify_stage1->stage2(H_total)` conditional verification-only, reconciled_symbols = 32*u1_hat + u2_hat per frame, tag L2-only 64b

- `comparison_bench/src/comparison_bench/pipeline/shell_integration.py` — shell pipeline
  - `def run_shell_pipeline(ttbin_root: Path, source: str, block_ids: list[str], counts: np.ndarray, registry_path: Path) -> ShellResult` (aggregate)
  - Steps: `TTBin read -> load_pairs_table -> normalize_pair_columns -> build_frame_batch(dimension=1024, frame_len=1024) -> NbLdpcShellAdapter.run -> verification/tag -> leakage stats(actual_disclosure_bits per frame + per accepted) -> PA(leak=actual_disclosure_bits) -> PIE/SKR proxy report (POLAR_REFERENCE_PROXY)`
  - Reads PA only from `src/reconciliation/pa.py` segment, rejects Polar leak_EC (ValueError if passed)

- `scripts/execute_v63_shell_smoke.py` and `scripts/execute_v63_shell_development.py` — execution entrypoints (default reject, require --execution-authorized --authorized-target-sha <new Plan SHA> + domain_check PASS + G1-G5 preflights)

### 2. Registry Paths (Authoritative)

- Smoke (execution-ready after ACCEPT): `workspace/v63_shell_spike/registries/v63_smoke_registry.json` (also mirrored `docs/research_cycles/v63/v63_smoke_registry.json` and `openspec/.../v63_smoke_registry.json`) — 9 blocks INTEGRATION_REPLAY_SMOKE, 3/source, frame_ids exact, zero overlap with V48-V54
- Dev candidate (90, DECODE_FORBIDDEN until smoke PASS): `workspace/v63_shell_spike/registries/v63_dev_registry.json` (mirrors) — 90 blocks INTEGRATION_FRESH_CANDIDATE, 30/source, deterministic index_j=floor(j*(K2-1)/29), zero overlap smoke ∩ fresh = ∅, candidate only

### 3. Symbol Factorization Contract (R63-01)

- Input FrameBatch holds full symbols `s ∈ [0,1023]` (10 bits, q=1024, log2q=5, GF32 poly37 on 5-bit sub-symbols)
- Decompose: `u1 = s // 32` (high 5 bits 0..31), `u2 = s % 32` (low 5 bits 0..31)
- Recompose: `s_hat = 32*u1_hat + u2_hat` (10-bit), `reconciled_symbols` is `s_hat` array shape (n_frames,1024) values 0..1023
- Exact: `exact_full = (u1_hat==u1_true && u2_hat==u2_true)`; `exact_u1`, `exact_l2` separately counted; `undetected = syndrome_ok && tag_ok && !exact_full` isolated

### 4. Leakage Contract (Tag Single Count)

- Per source m2: 1M 184, 1p5M 190, 2M 192; m1=16 always; tag=64 L2-only counted once in total
- `leak_base = 5*m2 + 5*16 +64 -> 1064/1094/1104`
- `leak_stage1 = 5*(m2+8)+80+64 -> 1104/1134/1144` (+40)
- `leak_stage2 = 5*(m2+16)+80+64 -> 1144/1174/1184` (+80)
- `per_source_avg[s] = leak_base[s] +40*N_stage1[s]/B +40*N_stage2[s]/B`, `overall_avg = (Σ leak_base +40*N_stage1+40*N_stage2)/90`
- `PA.leak = actual_disclosure_bits per frame by stage_used`, `tag 64` never double-deducted, Polar leak_EC rejected

### 5. Domain Gate (R63-04)

- `domain_check(H_drift_bits, p_b_chi2_p) -> DOMAIN_OK | DOMAIN_CALIBRATION_REQUIRED`
- Thresholds: |H drift| >0.05 bits or chi2 p <0.01 → DOMAIN_CALIBRATION_REQUIRED
- New session: domain_check → calibration P(U1|B) via get_l1_prior_p_u1_given_b + P(U2|B,U1) via get_l1_app_prior_l2/factorize_f03 → recompute m_total=floor((1.3*n*H-64)/5), m1=round(m_total*H1/H_total) → persisted, reviewed, then unlock
- Same-domain 84d62779: domain_check PASS required, calibration skipped

### 6. Budget & Gating

- Smoke 9: L1 9 + base9 + stage1≤9 + stage2≤9 =18-36 hard cap (L2 9-27), per block 2-4 calls
- Dev 90: L1 90 + base90 + stage1≤90 + stage2≤90 =180-360 hard cap (L2 90-270)
- Future execution after ACCEPT + EXECUTE_AUTH only, with guards: HEAD binding, SCOPED dirty check (v63 adapter/pipeline/v54/v38/v35), G1-G5 preflights, output root absent check, budget hard cap, session/cell poll only

### 7. Execution Authorization (Not Granted Now)

- This DELIVERY is PLAN_REVISION_CANDIDATE only; EXECUTE_NOT_AUTHORIZED remains
- Real decoder, run_01, formal PA, 90-block execution are explicitly forbidden in this spike
- Next stage requires: independent plan ACCEPT (reviewer) + explicit user EXECUTE_AUTH binding to new Plan SHA (to be printed after push) + fresh registry lock

### 8. Verification Commands (Production)

```
git fetch && git rev-parse HEAD == origin/formal-ir-mainline == <new Plan SHA>  # 40-char exact
python -m py_compile $(git diff --name-only HEAD~1 | grep .py)
python -m pytest workspace/v63_shell_spike/tests/test_v63_spike.py -p no:cacheprovider  # 12 passed
python -m pytest comparison_bench/tests -k v63 -p no:cacheprovider  # future
# registries zero overlap proof: python -c "import json,pathlib; ..."
```

### 9. Provenance

- HEAD at delivery start: 5602f11c65b2590254e89a1b95c7384f4bbbfd38
- New Plan SHA: (printed after push, 40-char)
- Branch: formal-ir-mainline (ordinary push, no force)
- State after push: PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED

## Next Actions

1. Main thread verifies this DELIVERY and REVIEW_VERDICT, then decides ACCEPT
2. Only after ACCEPT, operator may grant EXECUTE_AUTH for smoke 9 (not 90) with exact SHA binding
3. 90-block dev remains candidate until smoke PASS

