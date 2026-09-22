# D7-F implementation review R1 (independent)

- Authority: `.workbuddy/tasks/D7_E_ACCEPT_D7_F_REVERSE_ORDER_READINESS_R1_TASK_PACKET.md` §8 (implementation review only).
- Reviewer: independent D7-F implementation reviewer (separate context from implementer).
- Scope: review-only. Sole write is this document. No commits, no edits, no scientific decoder calls, no Model-F/real reads, no roots/UUID.
- HEAD: `aca2b6bf731dc75d5126a0e10766865749aa2ce8` (`aca2b6b`), branch `formal-ir-v72p1-addendum-clean`.
- Under review (uncommitted, untracked):
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py` (1535 lines)
  - `comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py` (1884 lines, 41 tests)
  - `scripts/v72p2d7_gf32_reverse_order_discriminator.py` (104 lines)
- Frozen refs: R1 packet §5, OpenSpec change `v72p2d7-reverse-order-cross-layer-discriminator` (proposal/design/tasks/specs), `D7_F_PREREG_R1.md`, `D7_F_EXECUTION_PACKET_R1.md`.
- Verdict token: `D7_F_IMPLEMENTATION_REVIEW_PASS`
- Rework rule: one rework allowed on FAIL, then re-review (stated per task; not triggered here).

## 0. Precondition / scope gate (STOP check)

- `git rev-parse HEAD` = `aca2b6b...`, `git branch --show-current` = `formal-ir-v72p1-addendum-clean`. PASS.
- `git status --porcelain=v1 | grep reverse_order` shows exactly the three `??` files above. PASS.
- `git diff --name-only HEAD` (tracked) = 11 docs/workspace files only (`AGENTS.md`, `AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`, `README.md`, `RUN_COMMANDS.md`, `docs/CURRENT_MAINLINE.md`, `docs/decision-log.md`, `docs/research-cycle-sop.md`, `docs/troubleshooting.md`, `docs/v35-algorithm-development-report.md`, `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`); zero entries under `comparison_bench/src/comparison_bench/formal_ir/`, `comparison_bench/tests/`, `scripts/`, `docs/research_cycles/`. Verified via `git diff HEAD --name-only -- comparison_bench/src/comparison_bench/formal_ir/ comparison_bench/tests/ scripts/ docs/research_cycles/V72P2D7*` = empty. No tracked D7-F diff. PASS (proceed, not STOP).
- Dirty worktree otherwise is large (~1970 entries) but out-of-scope per delegation rule §10.1-11 (review by scope). No `workspace/d7_f_reverse_order_discriminator_*` root exists; no `workspace/d6_graph_mother_r1d_*` created by this review; `cycle_state.yaml` still `d7f_execution_authorized: false`, `decoder_executed: false`, `result_created: false`. PASS.
- Line counts reproduce claims: 1535 / 1884 / 104 via `wc -l`. PASS.

## 1. Identity

- `F_VALUES`, `BLOCK_SEEDS`, `L1_ROWS`, `L2_ROWS`, `ROWS`, `MODEL_F_ROOT`, `Q/N/BOB_DIM/N_A`, `LAMBDA_STAR`, `DECODER_FLOOR`, `MAX_ITER`, `DAMPING_ALPHA` are narrow aliases (`= d7e.X`, where `d7e` aliases `d7c`): module lines 74-93, 157-166, 196. Chain resolves to `v72p2d7_gf32_bidirectional_oracle.py` frozen values: `Q=32, N=64, F=(1.0,1.2), BLOCK_SEEDS=tuple(range(2026091300,2026091316)), L1_ROWS={1.0:49,1.2:59}, L2_ROWS={1.0:43,1.2:52}, MODEL_F_ROOT=workspace/v72p2d5_model_f_input/20260907_r1, LAMBDA_STAR=137.3823795883264, DECODER_FLOOR=1e-15, MAX_ITER=90, DAMPING_ALPHA=1.0`, `L1_GRAPH_SEED=2026090501/L2=2026090502`. Independently reproduced via import (`Q 32 N 64 F (1.0,1.2) seeds 2026091300..1315 L1 {1.0:49,1.2:59} L2 {1.0:43,1.2:52} MAX 90 DAMP 1.0 LAM 137.38...`). Matches prereg B01/design B01/packet B01. PASS.
- Poly/cold/schedule: docstring pins `GF(32) poly 37, cold start, max_iter=90, damping 1.0`; production bind delegates to `d7e.bind_row_layered_decoders` (alias, line 456) whose source shows `decode_row_layered_fftqspa(h, prior, syndrome, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)` for both SOURCE/TARGET; `m03` pins `.target is v35.decode_row_layered_fftqspa` and `MAX_ITER==90/DAMPING==1.0`. No flooding import; `schedule_discriminator` never imported (x03 asserts absence in source and `sys.modules`). PASS.
- Estimator: joint only via `build_joint/condition_prior_qn/decoder_prior/build_mother/_default_model_f_loader` aliases (lines 392-396) through `d7c.prepare_inputs`; docstring + `e02` spy proves `prepare_model_f_prior_candidate` called once with `(N_A,BOB_DIM),LAMBDA_STAR` while `prepare_model_f_prior`/`build_f_model` raise if touched; `e03` static scan finds zero `build_f_model(`/`prepare_model_f_prior(` in core+runner and requires `build_f_model_concentration`+`prepare_model_f_prior_candidate` present. Reproduced `grep -c` = 0/0. `e01` direct-enumeration proves both transfer formulas + floor/renorm + no-truth signature. PASS.
- Reuse is narrow import only: all major helpers are `is` aliases (`m02` asserts 15 aliases); no predecessor-module copy (module is 1535 lines of D7-F state machine/writer/verifier, not a D7-E duplicate). No oracle/flooding/CAL/VAL/real/raw/graph changes in source (`grep` for `flooding/oracle/CAL/VAL/joint_graph/turbo` only hits docstring negations; `s02` static scan passes). PASS.

## 2. Evidence-use / no-feedback proof

- Structure is two-arm one-directional: `frozen_slots()` outer `f`, seeds ascending, `ARMS=(FORWARD,REVERSE)`, `ROLE_ORDER=(SOURCE,TARGET)` → per `(f,seed)` exactly `FWD_SRC,FWD_TGT,REV_SRC,REV_TGT`; `execute_slots` caches only source returns in `sources[(f,seed,arm)]`, target branch derives transient `q=softmax_source_q(src[beliefs])`, `prior=build_transfer_prior(joint,ARM_TO_DIRECTION[arm],bob,q)`, own `syndrome=_gf32_syndrome(h_prefix_target,x_true_target)`; target result never cached/reused; no third stage, no path back (`m03` asserts `source_layer != target_layer` per pair; `compute_arm_pairs` joins only same-arm source+target). PASS.
- Transfer prior transient: `q` local variable, never persisted; `_scalar/_jsonable/_record_row` reject non-scalars; `w03` proves no `array(/dtype` payloads, no vector/digest fields. PASS.
- Target cold consuming own syndrome once: each slot computes its own syndrome from its own `h_prefix/layer` and dispatches via `dispatch_decoder(key,...)` with `key=SOURCE/TARGET`; `s01` DI-spy captures `(h,prior,syndrome)` per key for 128 calls, replays in frozen order, asserts each `syn==_gf32_syndrome(h,x_true_layer)`, shapes `(rows,64)/(64,32)/(rows,)`, 128 distinct `(slot_idx,syndrome)` entries, and within-arm two syndromes differ in shape so replay cannot verify. Genuine (checks values/shapes against independent truth, not record tautology). PASS.
- No posterior fed back/blended/multiplied/reused: `s02` static scan asserts absence of `decode_flooding_fftqspa/L1_ORACLE_U2/L2_ORACLE_U1/FLOODING/flooding/--phase/psutil/concurrent/multiprocessing/threading/warm_beliefs=q/warm_beliefs=target/warm_beliefs=prev/blend(/feedback(/multiply(/reuse_target/third_stage/turbo_/joint_graph`, `warm_beliefs=None` count==2, `r1d` absent (reproduced count 2, zero forbidden hits); behavioral part captures 128 priors, recomputes each source prior from `decoder_prior(condition_prior_qn(joint,condition,block))` and each target prior from `build_transfer_prior(joint,direction,bob,softmax(q_source))` with canary target posterior (peak 31) never reappearing. Genuine. PASS.

## 3. State machine / pairing

- Exact 128-slot matrix/order/cap: `frozen_slots()` 128, `slot_idx` 1..128, `f` first 64×1.0 then 64×1.2, per-seed 4-slot order pinned in `m01` (rows 49/59/43 per f/layer, `n==64`, 64 SOURCE + 64 TARGET, unique `(f,seed,arm,role)`). `MAX_CALLS=128/MANDATORY=64`, `execute_slots` breaks at `>=MAX_CALLS`. PASS.
- Per-(f,seed) FORWARD-then-REVERSE: `ARMS` order enforced in `frozen_slots` and asserted in `m01/x01` dry-run lines 1-4. PASS.
- Blocked non-calls never replaced: `execute_slots` `continue` on ineligible (no record, no wall, no retry); `compute_arm_pairs` skips ineligible sources; `m03` all-refused run yields 64 records, 0 targets, 0 pairs; `g02` mixer/softmax spies stay empty; `g05` 5 refusals yield 64+(64-5)=123 records. PASS.
- Source exact never gates: `check_source_eligibility(status,finite,shape,provenance)` signature has no exact arg (D7-E lines 528-552, docstring `Source exactness never gates`); `evaluate_call` gates only via that helper; `g03` all-inexact sources still all eligible + 64 targets; `g04` iterations=0+CHECK_UPDATED eligible, iterations=7+PRIOR_ONLY blocked, crash/nonfinite/shape blocked. PASS.
- Only exact CHECK_UPDATED transfers: `require_check_updated` delegation (alias); `g01` all-CHECK_UPDATED → 64 pairs with admitting token; `g02` five refused tokens (`PRIOR_ONLY/<missing>/None/SOME_FUTURE/WARM_START_UNSPECIFIED`) each yield 0 targets, mixer/softmax never run, `COVERAGE_BLOCKED`; verifier `_check_record_semantics` recomputes eligibility and `verify_root` demands `source_provenance==CHECK_UPDATED` per pair. Spies silent on block (mixer_calls==[] + target 0). Genuine. PASS.

## 4. Labels / terminals

- Paired per-f candidate/reference counts: `compute_strata` iterates `BLOCK_SEEDS` (16/f), `rev_both` vs `fwd_both` → `candidate_only/reference_only/both/neither`; ineligible/incomplete counts as not-both-exact. PASS.
- Five first-match labels with exact boundaries incl. coverage rule: `classify_stratum` order `COVERAGE(<12)/REGRESSION(ref>=2&cand==0)/STRONG(cand>=4&ref==0)/WEAK(cand>ref)/NONE`; `l01` pins all boundaries (11 vs 12, 1 vs 2, 3 vs 4, weak strict-greater, first-match via coverage-first cases) and `STRATUM_LABELS` tuple; `g05` proves 11→COVERAGE, 12→not. Matches prereg B05/packet B05/spec. PASS.
- Ten terminals in priority order: `TERMINALS` tuple exact strings/order, `classify_terminal` cascade T1..T6 then `STRONG(either strong & other not regress)/WEAK(any weak & no regress)/REGRESSION(any regress)/NO_LIFT`; `l02` pins tuple, T1..T6 cascade, everything→T1, strong/weak/regression cases incl. `STRONG+REGRESSION→REGRESSION`, `WEAK+REGRESSION→REGRESSION`, `COVERAGE outranks STRONG`; `terminal_from_records` recomputes watchdog/crash/resource/incomplete/coverage from scalars. Matches B06. PASS.
- both_layers_exact = AND only: `compute_arm_pairs` `bool(l1 and l2)` with layer-view swap per arm; `b01` truth table over 4 corners ×2 arms + syndrome-only (wrong+null-syndrome stays inexact+yet-satisfied) + exact-only (exact+reported-False stays exact); verifier checks `both==AND` and `exact==symbol_errors==0`, `exact→unsatisfied==0`, `syndrome_ok→unsatisfied==0`. Syndrome never merged. PASS.

## 5. Resources / schema / verifier

- 128 cap, 120 s/call, ≤1500 s wall, VmHWM RSS fail-closed (A2 semantics, no ru_maxrss), sequential, no overwrite/retry/resume: constants `PER_CALL 120.0/STORED 1500.0/OUTER 1800+30/RSS 2GiB`; `execute_slots` sequential `for slot`, single `break` on first stop, no concurrency imports; `write_root` refuses existing/subdirs; summary `retries/reruns/resumes=0`; `l03` proves cap 128, crash@40 no-retry+T_CRASH, watchdog 120.0 pass vs 120.0001 void+1 record, stored 1500.0 pass vs +1e-5 overrun, RSS limit-1 pass vs limit/2× block+1 record, preflight RSS 0 blocks with 0 calls+no root, truncated→INCOMPLETE. `a2_01..15` pin A2: alias `parse is d7e.parse`, valid conversion, whitespace/duplicate/unit/signed/zero/overflow (18-digit max) rejections, fresh-read/no-cache, `ru_maxrss`/`import resource` absent in core+runner with bogus `getrusage` proving no effect, below-limit path equality, boundary `<2GiB` strict, None preflight/midrun → `T_PRE_EXEC`/`T_RESOURCE` with 5 records, schema invariant, CLI zero-decoder-zero-root. All genuine (behavioral, not string-only). PASS.
- Exactly seven scalar files, forbidden-payload scan genuine: `SEVEN_FILES` 7-tuple; `write_root` writes exactly those, refuses overwrite/subdirs/extra fields/non-scalars; `w01` asserts 7 files, no subdirs, header equality, 128/64/2 row counts, no `[`/`{` values, manifest pins, non-empty report/log, overwrite/subdir/extra-field/array rejections. `w03` asserts no vector/digest fields, provenance exception only, no `array(/dtype` in all seven files. PASS.
- Verifier independently recomputes everything read-only without Model-F/decoder: `verify_root(out_root)` only reads seven files, recomputes slot walk/mandatory/eligible counts/uniqueness/no-after-stop/pairs/strata/terminal/wall/RSS/manifest; never imports/binds decoder or loader (verified by `x01` dry-run `v35 not in sys.modules`, `r01` loader raisers never fire). `w02` 14 tamper cases (dup/missing/unpaired/exact/syndrome/provenance/eligible/AND/pairs-count/strata/terminal/wall/manifest/extra) each `ok is False`, plus truncated watchdog still `ok`. Genuine. PASS.

## 6. Lazy binding / isolation

- Import/help/dry-run/unauthorized/verifier/tests never read real Model-F, bind/call real decoder, or create scientific root: module top-level only aliases + constants; `prepare_inputs` default loader only on `joint=None` production path; `bind_row_layered_decoders` only called when `decoder_fns is None` + authorized; script `validate_production_out_root` precedes state/loader/decoder/root, `is_authorized` precedes `model_f_root`+`run_*`; `run_*` order: auth→exists→protected→RSS preflight→`prepare_inputs`→bind→loop→write. `x01` proves `--help`/`--dry-run` (128+header=129 lines, order FWD_SRC/FWD_TGT/REV_SRC/REV_TGT) from external cwd, dry-run leaves `v35` unimported, unauthorized `--out-root` returns 3 with `not authorized` and no root, bad-shape refuses, `--verify` fail/ok. `x02` external-cwd dual sentinel proves `dispatch` routes both keys, unknown key refuses, loader alias intact, sentinel shapes, no root created; raising-loader + wrong-root refuse before bind. `r01` proves workspace names/sizes/mtime unchanged, no D7-F/R1d roots, `_EXECUTION_CONSUMED is False`, cycle-state auth keys all false, protected roots refuse with 0 decoder events. External-cwd sentinels genuine (subprocess `cwd=external`, `PYTHONPATH` stripped). Unauthorized refusal precedes loader/decoder/root (events==[] + `not exists`). PASS.

## 7. Tests (independent reproduction)

- Command (separate process, fresh basetemp, no cache): `rm -rf /tmp/d7f_review_basementp && mkdir -p /tmp/d7f_review_basementp && .venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py -q -p no:cacheprovider --basetemp /tmp/d7f_review_basementp`
- Literal result: `41 passed, 1 warning in 29.03s` (warning only `Unknown config option: cache_dir`). Reproduces claimed 41/41. No failures; no newly failing in-scope test. PASS.
- §7 coverage mapping (all genuine, behavioral + static, fakes/Tiny fixtures/task basetemps only):
  - 128 matrix/order/cap → `m01`, `l03-cap`, `x01-dry-run`
  - arm transitions/blocked → `m03`, `g05`
  - source exact not gate → `g03`, `g04`
  - only CHECK_UPDATED → `g01`, `g02`, `g04`, `x04`
  - syndrome once/no feedback → `s01`, `s02`
  - both-layer truth/syndrome isolation → `b01`, `w02-AND`
  - labels/terminals → `l01`, `l02`, `l03-T7/T8/T9/T10`
  - RSS/fail-closed → `a2_01..15`, `l03-wall/RSS/preflight`
  - scalar/forbidden → `w01`, `w03`
  - writer/verifier tamper → `w02`
  - protected/no-overwrite → `r01`, `w01`
  - external-cwd sentinels → `x02`
  - dry-run/unauthorized → `x01`, `a2_15`
  - D7-E/BP regression → `x04`, `x05` (inner BP `23 passed`), `e02/e03`, `x03` (D7-C/D independent)
- Fakes-only: all scientific runs inject `_uniform/_column/_skewed` joints, `_const/_parity/_zero` samplers, `_scripted/_argmax/_planned` decoders, `_ScriptedClock`, lambda RSS probes; `r01` monkeypatches loaders to raisers; no production decoder contacted; no `workspace/d7_f_*` created (verified absent after run). PASS.

## 8. Scope

- `git diff HEAD --name-only` = 11 docs/workspace files, none under `comparison_bench/src|tests`, `scripts/`, `docs/research_cycles/`; D7-F tracked diff = none (three files untracked only). Zero edits to v35/D5/D6/D7-A/B/C/D/E production code, BP tests, or cycle states. No D7-F/R1d roots; no auth changes (`d7f_execution_authorized/decoder_executed/result_created` false before and after tests). Script is thin (104 lines, local-source bind + auth/dry-run/verify dispatch). No scope creep (no feedback/turbo/graph/CAL/VAL/real/G1/G2/R1d). PASS.

## Blocking Issues

- None.

## Non-Blocking Suggestions

- None required for PASS. Future Pre-EXECUTE must still independently rehearse exact frozen command, GNU timeout, live VmHWM, target absence, and protected roots; this review grants no authorization and creates no identifier.

## Checklist

- [x] Matches OpenSpec spec (proposal/design/tasks/specs + prereg/execution packet §5 B01–B07)
- [x] Tests pass (41 passed reproduced, fakes only, no new failures)
- [x] No scope creep (new files only at frozen paths; zero predecessor/cycle-state edits; no roots/auth)
- [x] docs/decision-log.md or docs/troubleshooting.md needs update? No — readiness-only review; no durable decision or failure mode to record here.

Verdict: `D7_F_IMPLEMENTATION_REVIEW_PASS`
