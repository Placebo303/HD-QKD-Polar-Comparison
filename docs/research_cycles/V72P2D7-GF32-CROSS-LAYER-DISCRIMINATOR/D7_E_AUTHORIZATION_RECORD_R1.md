# D7-E Authorization Record R1 (one-shot, RSS A2)

- UUID: `faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Target root: `workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c` (confirmed absent before record creation; reconfirmed after)
- Exact command (sole authorized invocation, from repo root):
  `timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD at authorization: `40eeb73a3f9d280a8236d8cd8ca1350933a9248e`
- Implementation commit: `9e09538`; A2 chain ancestors: `becf60f`, `9e09538`, `40eeb73` plus R1 chain `08590fba`, `031deee7`, `d6e40dd` (all ancestors of HEAD per E01)

## Verbatim user authorization (copied exactly from current-task explicit authorization)

---
我现在明确授权执行 D7-E provenance-safe cross-layer discriminator（RSS A2，与此前未执行的授权文字无关）：仅允许按 D7_E_EXECUTION_PACKET_R1.md、D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md 与 D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md，在仓库根使用冻结命令和 .venv/bin/python，对一个全新的 workspace/d7_e_cross_layer_discriminator_<new_uuid>/ 根调用一次；最多 192 个冻结 scientific decoder slots（128 个 mandatory source/control，加上最多 64 个仅在 CHECK_UPDATED 时允许的 transfer calls），授权由首次 scientific decoder 尝试消耗，不因失败、超时、部分结果、provenance-blocked、RSS telemetry failure 或环境异常恢复；不得重试、重跑、恢复、补跑 blocked slots、复用根、修改参数、公式、estimator、provenance 规则、RSS A2 规则、矩阵或顺序；不得执行 R1d、任何 --phase、正式 G1/G2、CAL、VAL、real/raw、oracle、flooding、forced sweep、warm start、alternating、joint 或 feedback。执行结束后立即回收授权并进行独立 Pre-RESULT 复审；复审通过前不得接受或提交结果。
---

## E01–E15 results (STEP 1, each a separate command)

- E01 PASS: branch `formal-ir-v72p1-addendum-clean`; HEAD `40eeb73a3f9d280a8236d8cd8ca1350933a9248e`; ancestors YES for `08590fba`, `031deee7`, `d6e40dd`, `becf60f`, `9e09538`, `40eeb73`.
- E02 PASS: `D7_E_PRE_EXECUTE_REVIEW_VENV_RSS_A2.md` exists; PASS token `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` count 1; verdict FAIL token `D7_E_PRE_EXECUTE_REVIEW_FAIL` count 0; verdict BLOCKED token `D7_E_PRE_EXECUTE_REVIEW_BLOCKED` count 0. Generic `FAIL` count 2 = T5 `REVIEW_FAIL_A2 absent` line + `T5_FAIL_ABSENT` line (not verdicts). Generic `BLOCKED` count 1 = T1 terminal `D7_E_PRE_EXECUTION_BLOCKED` name (not verdict).
- E03 PASS: three files `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`, `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`, `scripts/v72p2d7_gf32_cross_layer_discriminator.py` have zero diff vs `9e09538` (`git diff --numstat 9e09538` empty). Delta vs `08590fba` confined to the two A2 paths; `08590fba..becf60f` on those three paths empty; `becf60f..9e09538` = exactly those two paths (module RSS-block replacement + test A2 append); module contains zero `ru_maxrss` and zero `import resource`.
- E04 PASS: `d7e_execution_authorized:false`, `decoder_executed:false`, `result_created:false`, all promotion/authorization flags false, `d7e_execution_attempts:0`, `d7e_execution_completed:0`, `d7e_terminal:D7_E_NOT_EXECUTED`, `next_gate`/`state` exactly `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`.
- E05 PASS: no `workspace/d7_e_cross_layer_discriminator_*` root (`ls` No such file or directory); `git grep` for `d7_e_cross_layer_discriminator_` shows only `OUT_ROOT_PREFIX`, `<uuid>` placeholders, `*` wildcards, and non-UUID probe names (`A1_VENV_PROBE`, `A2_PREEXEC_PROBE`, `PREEXECUTE_REFUSAL_PROBE`); no hex-UUID suffix match.
- E06 PASS (stat-only, no content reads): 12 protected roots exist as dirs size 4096 with mtime_ns recorded at execution time (see operator return for values; representative: Model-F `workspace/v72p2d5_model_f_input/20260907_r1` exists; D7-C `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae` exists; D7-B `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964` exists; D7-D `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7` exists; plus G0/G0-recovery/P0/G1x2/structure/D6x2). Formal R1d `workspace/d6_graph_mother_r1d_*` absent; formal G2 `workspace/v72p2d5_g2` and `workspace/v72p2d5_g2/20260906_r1` absent. Pre-existing `workspace/v72p2d5_p0g1g2_candidate_repair_*` dirs are unrelated, not formal G2 roots.
- E07 PASS: cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; `test -x .venv/bin/python` exit 0; `Python 3.12.3`, `numpy 2.5.3`, exe `/mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python`; `PYTHONPATH` empty; `which python` exit 1 (no bare interpreter).
- E08 PASS: `/usr/bin/timeout` exists, `timeout (GNU coreutils) 9.4` — identical to renewed (A2) review; no rehearsal per binding (rehearse only if executable/version differs).
- E09 PASS (single probe, never repeated): `.venv/bin/python` production `get_rss_bytes()` in same command as raw `VmHWM` line; `RAW_VMHWM_LINE='VmHWM:\t   96688 kB'`; `RSS_BYTES=99008512`; `LIMIT=2147483648`; `96688*1024=99008512` exact; `0<99008512<2147483648` true; `E09_PASS=True`. Command contained no `ru_maxrss`. This single result stands; no second E09 run.
- E10 PASS: frozen dry-run via `.venv/bin/python` exit 0, 193 lines, header `slots=192 mandatory=128 budget=192`; head `1 1.0 2026091300 L1_TO_L2 SOURCE L1_MARGINAL L1 49`; tail `191 1.2 2026091315 L2_TO_L1 CONTROL L1_MARGINAL L1 59` / `192 1.2 2026091315 L2_TO_L1 TRANSFER L1_TRANSFER L1 59`; no root created.
- E11 PASS: external-cwd (`/tmp`) sentinel via absolute interpreter/repo paths only; `SOURCE_target_is_v35=True`, `TARGET_target_is_v35=True`, `loader_is_d7c=True`, `events=['src','tgt']`, `unknown_key_refused=True`, `REPO_D7E_ROOTS=[]`, `FOREIGN_SENTINEL_OK`; zero real decoder calls (sentinels raise before real decode), zero Model-F reads, zero roots.
- E12 PASS: unauthorized exact-shape probe out-root `workspace/d7_e_cross_layer_discriminator_E12_REFUSAL_PROBE` pre-absent; exit 3; stdout `D7-E execution is not authorized; refusing before any work`; post-absent. Refusal before loader/decoder/root.
- E13 PASS: `workspace` dir writable (`WORKSPACE_WRITABLE:YES`); target root not precreated.
- E14 PASS: scoped `git diff --numstat` empty and scoped `git diff --cached --numstat` empty for the three implementation files + `cycle_state.yaml`; `git status --porcelain` for D7-E scope empty; overall staged empty; unrelated dirt preserved (no clean/stash/checkout).
- E15 PASS: explicit user authorization from current task confirmed present (RSS A2, backtick-formatting-only delta plus restrictive clauses, no expanded permissions, as adjudicated); copied verbatim above.

## Budgets (frozen)

- Hard cap 192 scientific decoder slots (128 mandatory source/control + at most 64 provenance-eligible transfer calls).
- Per-call watchdog 120 s; stored scientific wall ≤1500 s; outer GNU timeout 1800 s + `-k 30` kill grace.
- RSS strict `<2 GiB` (`RSS_LIMIT_BYTES=2147483648`); authoritative source on this WSL path is `VmHWM` from `/proc/self/status` (`bytes=value*1024`); equality or greater blocks.
- Fresh direct-child out-root, no overwrite, no subdirectories.

## Prohibitions (incl. RSS A2 rule + single-E09 discipline)

- No retry/rerun/resume/recovery/second UUID/replacement root/make-up of blocked slots; single UUID above only.
- No parameter/estimator/matrix/order/decoder/provenance/RSS-rule/label/terminal/schema/threshold change; no R1d/`--phase`/G1/G2/CAL/VAL/real/raw/oracle/flooding/forced-sweep/warm-start/alternating/joint/feedback.
- No code/test/OpenSpec/prereg/packet/evidence edits; no VOID reads; no push/reset/checkout/clean/stash/rebase/amend/broad-stage.
- Probes never invoke a real decoder or read real Model-F.
- RSS A2 rule: `VmHWM` authoritative; do not compare/fall back to `ru_maxrss`; `ru_maxrss` must not be called on the frozen WSL path; parser accepts exactly one ASCII `VmHWM: <positive integer> kB` line, rejects missing/duplicate/malformed/decimal/signed/zero/negative/wrong-unit/non-ASCII and >18-digit overflow; failure returns `None` and blocks fail-closed.
- Single-E09 discipline: exactly one live E09 probe was run (above); never repeat or sample until favorable; that one result stands pass or fail.

## Attempt-consumption rule

- Authorization is consumed by the first scientific decoder attempt regardless of outcome (failure, timeout, partial result, provenance-blocked, RSS-telemetry failure, environment anomaly); consumed authorization does not restore. After process return, authorization is immediately revoked (`d7e_execution_authorized:true->false`) before opening result contents. If revocation cannot commit, STOP before interpreting artifacts.

## State change in this commit

- `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/cycle_state.yaml`: `d7e_execution_authorized:false->true` only. All other keys unchanged.

(End of record)
