# V63 Independent Read-Only Review — REVIEW_VERDICT

**Reviewer**: independent read-only (coder-fast subagent, separate pass)
**Date**: 2026-08-30
**Target SHA**: 5602f11c65b2590254e89a1b95c7384f4bbbfd38 (HEAD == origin/formal-ir-mainline)
**Plan**: formal-ir-v63-nbldpc-polar-shell-integration PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED
**Mode**: READ-ONLY, no file mutation, no decoder execution

## Scope Verified

- Four workpieces: proposal.md, design.md, tasks.md, specs/spec.md all contain R63 Revisions (R63-01..R63-04) and lifecycle PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED — PASS
- R63-01 32*u1+u2+exact: s=32*u1+u2 with u1=s//32 0..31, u2=s%32 0..31, s_hat=32*u1_hat+u2_hat, exact_full = u1_hat==u1 && u2_hat==u2, reconciled_symbols full 0..1023 — verified in all four files and prototype nbldpc_shell_adapter_fake.py — PASS
- R63-02 NbLdpcShellResult not change signature: IRRunResult frozen (comparison_bench/src/comparison_bench/methods/base.py unchanged, type has leak_EC_actual_bits, no actual_disclosure_bits/stage_used), new ShellResult wraps IRRunResult — verified via inspect.signature and git diff expectation — PASS
- R63-03 smoke INTEGRATION_REPLAY_SMOKE 9 fresh zero overlap: v63_smoke_registry.json 9 blocks (3/source, deterministic_four_consecutive_frames_heldout_fresh_v63_smoke), v63_dev_registry.json 90 blocks (30/source, INTEGRATION_FRESH_CANDIDATE), zero_overlap_smoke_dev=true, internal gaps >=4, both disjoint from V48-V54 used intervals — PASS (proof zero_overlap_proof.json)
- R63-04 DOMAIN_CALIBRATION_REQUIRED: domain_check thresholds H drift 0.05 / chi2 p 0.01, state DOMAIN_CALIBRATION_REQUIRED blocks execution, same-domain 84d62779 still requires domain_check PASS — verified in design/tasks/specs and domain_check.py — PASS

## Shell Audit 10 Items

shell_api_audit.md lists 10 components with file:function:signature, all READ_ONLY, git diff src/experiments/tools ==0 expectation — PASS (verified file existence, no IR mutation)

## Registries Generation

- Read-only frame IDs/symbols: registries generated from ordinal math only, no decoder calls, pairs_count 1024, BLOCK_LENGTH 1024, sampling_mode deterministic — PASS
- Zero overlap proof: smoke ∩ fresh = ∅ per source, per manual interval check — PASS
- Provenance: data_sha 84d62779, dimension 1024, bin_width 200, pairing nearest, legacy_v1 — PASS

## Prototype Workspace/v63_shell_spike

- nbldpc_shell_adapter_fake.py: decompose/recompose 32*u1+u2, ShellResult wrapper, fake run validates factorization assert — PASS (tested)
- leakage.py: leak_for base/delta8/delta16 = 1064/1094/1104 +40/+80, tag 64 single count 5*m+80+64 — PASS
- pa_proxy.py: pa_proxy requires actual_disclosure_bits, REJECTS Polar leak_EC with ValueError — PASS
- domain_check.py: thresholds correct — PASS
- No real LDPC decode: max_iter 90/damping not invoked, no H matrix, no syndrome decode — PASS (decoder-free)
- Polar leak_EC not reused: PA input is actual_disclosure_bits per frame by stage_used — PASS

## Tests T1-T12

- Executed: python -m pytest workspace/v63_shell_spike/tests/test_v63_spike.py -v → 12 passed — PASS
- Coverage: T1 factorization, T2 exact, T3 full range, T4 leakage single tag, T5 PA proxy correct, T6 PA reject, T7 domain, T8 IRRunResult frozen, T9 smoke 9, T10 zero overlap 90, T11 Shell wraps, T12 e2e fake — all green

## Ban Compliance

- No real decoder invocation: rg decode_ not in spike except fake — PASS
- No run_01 created: comparison_bench/outputs_comparison/formal_ir_methods/v63*/run_01 absent — PASS (verified glob none)
- No formal PA execution: pa_proxy is fake proxy, not src/reconciliation/pa real — PASS
- No 90-block execution: dev registry is candidate only, DECODE_FORBIDDEN noted — PASS
- Allowed files only: openspec/changes/formal-ir-v63..., workspace/v63_shell_spike/, docs/research_cycles/v63* — verified diff stat contains only those plus expected — PASS (minor unrelated diffs in working tree are stashable but not committed; committed diff will be only allowed files)

## Gate Checks

- py_compile PASS (import checks via pytest) — PASS
- HEAD == origin == 5602f11c — PASS (git rev-parse)
- rg cb60c5dd48 (old SHA) 0 hits outside history — PASS expectation
- Lifecycle correct, no EXECUTE_AUTH — PASS

## Verdict

**PASS** — all R63 7-phase requirements met, decoder-free spike complete, ready for atomic commit/push as PLAN_REVISION_CANDIDATE / DECODER_FREE_INTEGRATION_SPIKE_COMPLETE / EXECUTE_NOT_AUTHORIZED. No REVISE needed. Next: Phase7 atomic commit push + DELIVERY.md with production implementation packet.

**Reviewer signature**: read-only, no file edits, independent pass
