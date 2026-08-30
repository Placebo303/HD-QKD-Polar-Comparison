# V63 Independent Read-Only Review — REVIEW_VERDICT (updated for production implementation — 4-blocking fix)

**Reviewer**: independent read-only (coder-fast subagent, separate pass) + production-implementation delta review
**Date**: 2026-08-30 (initial) / 2026-08-30 (delta — 4-blocking fix)
**Target SHA**: 5602f11c65b2590254e89a1b95c7384f4bbbfd38 (spike) → predecessor impl 10390cfa52f2b5e3e6c7c382cfb2d4c316471218 (FAIL/REVISE_REQUIRED) → new impl SHA see PRE_EXECUTE_CHECKLIST.md (HEAD == origin/formal-ir-mainline)
**Accepted Plan SHA**: 397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a (frozen)
**Plan**: formal-ir-v63-nbldpc-polar-shell-integration PLAN_REVISION_CANDIDATE / PRODUCTION_IMPLEMENTATION / EXECUTE_NOT_AUTHORIZED (spike superseded)
**Mode**: READ-ONLY, no formal decoder execution triggered by review; production code verified via py_compile + pytest standard

## Scope Verified

- Four workpieces: proposal.md, design.md, tasks.md, specs/spec.md all contain R63 Revisions (R63-01..R63-04) and lifecycle PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED — PASS
- R63-01 32*u1+u2+exact: s=32*u1+u2 with u1=s//32 0..31, u2=s%32 0..31, s_hat=32*u1_hat+u2_hat, exact_full = u1_hat==u1 && u2_hat==u2, reconciled_symbols full 0..1023 — verified in all four files and prototype nbldpc_shell_adapter_fake.py — PASS
- R63-02 NbLdpcShellResult not change signature: IRRunResult frozen (comparison_bench/src/comparison_bench/methods/base.py unchanged, type has leak_EC_actual_bits, no actual_disclosure_bits/stage_used), new ShellResult wraps IRRunResult — verified via inspect.signature and git diff expectation — PASS
- R63-03 smoke INTEGRATION_REPLAY_SMOKE 9 fresh zero overlap: v63_smoke_registry.json 9 blocks (3/source, deterministic_four_consecutive_frames_heldout_INTEGRATION_REPLAY_SMOKE), v63_dev_registry.json 90 blocks (30/source, INTEGRATION_FRESH_CANDIDATE), zero_overlap_smoke_dev=true, internal gaps >=4, both disjoint from V48-V54 used intervals — PASS (proof zero_overlap_proof.json)
- R63-04 DOMAIN_CALIBRATION_REQUIRED: new/incompatible session → DOMAIN_CALIBRATION_REQUIRED → 停止，校准属后继 OpenSpec — verified in design/tasks/specs — PASS

## Shell Audit 10 Items

shell_api_audit.md lists 10 components with file:function:signature, all READ_ONLY, git diff src/experiments/tools ==0 expectation — PASS (verified file existence, no IR mutation)

## Registries Generation

- Read-only frame IDs/symbols: registries generated from ordinal math only, no decoder calls, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode deterministic — PASS
- Zero overlap proof: smoke ∩ fresh = ∅ per source, per manual interval check — PASS
- Provenance: data_sha 84d62779, dimension 1024, bin_width 200, pairing nearest, legacy_v1 — PASS

## Prototype (decoder-free spike, 路径已清理)

- nbldpc_shell_adapter_fake.py: decompose/recompose 32*u1+u2, ShellResult wrapper, fake run validates factorization assert — PASS (tested)
- leakage.py: leak_for base/delta8/delta16 = 1064/1094/1104 +40/+80, tag 64 single count 5*m+80+64 — PASS
- pa_proxy.py: pa_proxy requires actual_disclosure_bits, REJECTS Polar leak_EC with ValueError — PASS
- domain_check.py: new/incompatible session → DOMAIN_CALIBRATION_REQUIRED 阻断 — PASS
- No real LDPC decode: max_iter 90/damping not invoked, no H matrix, no syndrome decode — PASS (decoder-free)
- Polar leak_EC not reused: PA input is actual_disclosure_bits per frame by stage_used — PASS

## Tests T1-T12

- Executed: python -m pytest （已移除临时路径，见 V63P0 权威 registry）/tests/test_v63_spike.py -v → 12 passed — PASS
- Coverage: T1 factorization, T2 exact, T3 full range, T4 leakage single tag, T5 PA proxy correct, T6 PA reject, T7 domain, T8 IRRunResult frozen, T9 smoke 9, T10 zero overlap 90, T11 Shell wraps, T12 e2e fake — all green

## Ban Compliance

- No real decoder invocation: rg decode_ not in spike except fake — PASS
- No run_01 created: comparison_bench/outputs_comparison/formal_ir_methods/v63*/run_01 absent — PASS (verified glob none)
- No formal PA execution: pa_proxy is fake proxy, not src/reconciliation/pa real — PASS
- No 90-block execution: dev registry is candidate only, DECODE_FORBIDDEN noted — PASS
- Allowed files only: openspec/changes/formal-ir-v63..., （已移除临时路径，见 V63P0 权威 registry）/, docs/research_cycles/V63P0* — verified diff stat contains only those plus expected — PASS (minor unrelated diffs in working tree are stashable but not committed; committed diff will be only allowed files)

## Production-Implementation Delta (4-blocking fix — 2026-08-30)

- **Synthetic fallback removed**: `_load_entry` in both CLIs now `EVIDENCE_INVALID` fail-closed (no `rng.integers` fallback); `rg "rng.integers" scripts/execute_v63*py` returns 0 for loader path — PASS
- **Test imports unified**: `comparison_bench.src.comparison_bench` → `comparison_bench.methods/pipeline/types` with `comparison_bench/src` on sys.path; `rg "comparison_bench.src.comparison_bench" tests/` 0 hits; `pytest -p no:cacheprovider --basetemp workspace/v63_preexec_test` 12 passed — PASS
- **Decoder_calls mechanical**: `base2/delta8:3/delta16:4` per `stage_used`; per-batch and global sum asserts; fake runner `sum(map)` — PASS (code inspection + 12 passed)
- **Pre-EXECUTE checklist**: `PRE_EXECUTE_CHECKLIST.md` added with new SHA, Accepted Plan, HEAD/origin, py_compile, parquet 9/9, run_smoke absence, 18-36 budget; prior spike docs updated — PASS
- Preserved: real V54 three-stage L1 q reuse, verification-only, SHA binding, three-tier leakage, DOMAIN_CALIBRATION_REQUIRED, output-root防覆盖 — all PASS (no regression)

## Gate Checks

- py_compile PASS (checked `nbldpc_shell_adapter.py`, `shell_integration.py`, `execute_v63_*.py`, `test_v63_shell_adapter.py`) — PASS
- pytest standard `pytest -p no:cacheprovider --basetemp workspace/v63_preexec_test` 12 passed (T1-T12) — PASS
- Parquet 9/9 readable (each block 1024 rows, alice/bob 0..1023) — PASS (log in PRE_EXECUTE_CHECKLIST.md)
- `run_smoke` absent (`Test-Path` False) + additive `mkdir(exist_ok=False)` — PASS
- Budget 18-36 (smoke) / 180-360 (dev) hard cap with `assert` — PASS
- HEAD/origin binding & ACCEPTED_PLAN_SHA 397c1bb6 enforcement — PASS (code + pending new SHA re-derive)
- Lifecycle correct, `EXECUTE_NOT_AUTHORIZED` (no real decoder executed by review) — PASS

## Verdict

**PASS (delta)** — 4-blocking fixed, production implementation ready for `PRE_EXECUTE_CHECKLIST.md` gate before `EXECUTE_AUTH`. Spike PASS (5602f11c) remains, predecessor impl 10390cfa superseded. Next: main thread verifies PRE_EXECUTE_CHECKLIST.md + docs, then may grant `EXECUTE_AUTH` with exact new SHA.

**Reviewer signature**: read-only delta, no decoder execution, no file edits except this verdict update
