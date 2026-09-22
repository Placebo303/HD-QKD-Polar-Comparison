# D7-F one-shot execution authorization record R1

- Cycle: `V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR`, plan revision `R1`.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD at authorization: `ffe94307`.
- Fresh identifier (exactly one system UUID, generated once): `b6d62184-fd15-483d-947e-01ea66ddc13c`.
- Target root (confirmed absent before authorization): `workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c`.

## Verbatim user authorization (copied exactly from the explicit user message in the current task)

---
我现在明确授权执行 D7-F forward-vs-reverse complete-two-layer discriminator：仅允许按冻结的 D7_F_EXECUTION_PACKET_R1.md，在仓库根使用 .venv/bin/python 和冻结命令，对一个全新的 workspace/d7_f_reverse_order_discriminator_<new_uuid>/ 根调用一次；最多 128 个冻结 scientific decoder slots，严格比较 FORWARD_L1_TO_L2 与 REVERSE_L2_TO_L1，授权由首次 scientific decoder 尝试消耗，不因失败、超时、部分结果、provenance-blocked、RSS telemetry failure 或环境异常恢复；不得重试、重跑、恢复、补跑 blocked slots、复用根、修改参数、estimator、prior、矩阵、seed、decoder 配置、provenance 门、臂顺序、标签或 terminal；不得增加第三 stage、feedback、alternating、joint、turbo、oracle、flooding 或 warm start；不得执行 R1d、任何 --phase、正式 G1/G2、CAL、VAL、real/raw。执行结束后立即回收授权并进行独立 Pre-RESULT 复审；复审通过前不得接受或提交结果。
---

## Exact authorized command (exactly one invocation)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c
```

- cwd: repository root; interpreter: `.venv/bin/python` only; outer GNU timeout `-k 30 1800`.

## STEP 1 gates E01–E15 (all PASS, each a separate probe command)

- E01 PASS: branch `formal-ir-v72p1-addendum-clean`; ordered ancestry `f4c06042` → `aca2b6b` → `7785366f` → `ffe94307` (=HEAD), confirmed via `git log` + `git merge-base --is-ancestor` + ancestry-path.
- E02 PASS: `D7_F_IMPLEMENTATION_REVIEW_PASS` ×2, `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` ×2; FAIL/BLOCKED grep counts 0/0 in both review docs.
- E03 PASS: `git diff 7785366f -- <core/test/script>` empty (exit 0); frozen command byte-identical in prereg §4 and execution packet.
- E04 PASS: `next_gate: D7_F_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; all authorization/promotion/decoder/result flags false/zero; `d7f_execution_attempts: 0`, `d7f_execution_completed: 0`, `d7f_terminal: NONE`.
- E05 PASS: no `workspace/d7_f_reverse_order_discriminator_*` (ls exit 2); repo-wide UUID-pattern grep exit 1 (no prior D7-F UUID; only `<uuid>` placeholders).
- E06 PASS: protected-root names/sizes/mtimes equal Pre-EXECUTE metadata (Model-F `2026-09-07 02:07:07`; D7-E root `2026-09-11 19:43:07`; D7-C root `2026-09-11 00:33:39`; D7-B R2 `2026-09-10 20:33:38`; D7-D root `2026-09-11 07:30:05`; all dir Size 4096); no `d6_graph_mother_r1d_*`; no D7-F R1d/G2 roots; contents unread (stat/ls only).
- E07 PASS: cwd repo root; `.venv/bin/python` executable; Python 3.12.3 / NumPy 2.5.3; no `PYTHONPATH`.
- E08 PASS: GNU coreutils timeout 9.4, unchanged since Pre-EXECUTE review → no 124 rehearsal per packet rule.
- E09 PASS (exactly one live probe, stands): `RAW:VmHWM:	   96612 kB`, `PARSED_BYTES:98930688`, `POS_FINITE_LT2G:True`; no `ru_maxrss`; never repeated.
- E10 PASS: dry-run exit 0, 129 lines (header `slots=128 mandatory=64 budget=128` + 128 slots), exact per-(f,seed) `FWD_SRC/FWD_TGT/REV_SRC/REV_TGT` order, f outer 1.0→1.2, seeds ascending.
- E11 PASS: external-cwd (`/tmp`, `PYTHONPATH` stripped) sentinel reached exact production `dispatch_decoder` for SOURCE/TARGET with fakes (`r1=SRC r2=TGT unk_refused=True calls=['S','T'] v35_absent=True`); zero calls/reads/root.
- E12 PASS: unauthorized exact-shape invocation exit 3 (`D7-F execution is not authorized; refusing before any work`); probe root absent after (ls exit 2).
- E13 PASS: `workspace/` parent writable; target root absent.
- E14 PASS: scoped tracked diff/numstat/summary/cached all empty for `comparison_bench/src/comparison_bench/formal_ir/`, `comparison_bench/tests/`, `scripts/`, `docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/`; D7-F frozen files clean; unrelated dirt preserved untouched.
- E15 PASS: verbatim authorization above confirmed present as a new explicit user message (recorded exactly).

## Frozen budgets

- Max 128 scientific decoder calls (64 mandatory source marginals + up to 64 gated transfers); 120 s/call watchdog; stored wall ≤1500 s; outer `1800` + `-k 30`; sequential; `/proc/self/status` `VmHWM` strict `< 2 GiB` fail-closed.

## Hard prohibitions (§3)

- Exactly one invocation; no retry/rerun/resume/recovery/new root/make-up; no code/test/OpenSpec/packet/parameter/formula/matrix/ordering/schema/threshold changes; no D7-E verify/rerun, R1d/`--phase`/G1/G2/CAL/VAL/real/raw; no third stage/feedback/alternating/joint/turbo/oracle/flooding/forced-sweep/warm-start; no VOID reads; no predecessor/protected-root modification; no push/reset/checkout/clean/stash/rebase/amend/broad-stage; probes never invoke a real decoder or read real Model-F.

## Attempt-consumption rule

- Authorization is consumed by the first scientific decoder attempt regardless of outcome (failure, timeout, partial result, provenance-blocked, RSS telemetry failure, environment anomaly); it is never restored. After process return, authorization is immediately revoked (true→false, separate commit) before result contents are opened. Independent Pre-RESULT review is mandatory before any acceptance or solidification.
