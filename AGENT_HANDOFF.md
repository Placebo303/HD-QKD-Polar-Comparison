Status: NBLDPC_PRIMARY_V19_DIAGNOSTIC — first V19 evidence generated

## Current State — V19 Nonbinary LDPC primary-route diagnostics (2026-08-16)

- 用户最新决策：Binary Polar MLC release 在 `D:\Code\HD-QKD_Polar_Release`，只读；
  Binary LDPC MLC f≈4.17，只读；Nonbinary LDPC 继续主攻。
- 执行契约：`docs/nbldpc-focus-plan-20260816.md`（Route N0–N6）。
- 本轮新增 V19 模块 + CLI + 4 个测试（11 passed），并生成 additive 证据包：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/`
  - n1_channel/channel.json
  - n2_rate_ladder/rate_ladder.json（暖启动 rate=0.65 小预算不收敛）
  - n2_extended_probe/extended_degree_probe.json（degree 48/60 不收敛）
  - n4_finite_q16_r060_simple/finite_execute.json（3 exact / 1 mismatch / 0 fail, f≈4.183）
  - n4_finite_q1024_simple/finite_execute.json（q=1024, 2/2 exact, f≈6.819）
  - n4_finite_q1024_n128_simple/finite_execute.json（q=1024 n=128, 2/2 exact, f≈7.245）
  - n2_extended_probe_q1024/extended_degree_probe.json（q=1024 rate=0.6 小样本未收敛）
  - n2b_channel_aware_bounds/lsb_public_capacity.json（LSB-public capacity bound）
  - n2b_channel_aware_bounds/high_plane_channels.json（残余高位有效信道）
  - n2b_channel_aware_bounds/lsb_public_de_probe_q512.json（q=512 R=0.92 小样本未收敛）
  - n6_comparison/comparison_table.csv + comparison_summary.json
  - n6_comparison_v2_q1024/comparison_table.csv + comparison_summary.json
  - n6_comparison_v2_q1024/leakage_decomposition.json（q16 honest f≈3.016; q1024 n128 f≈7.245）
  - n4_finite_q1024_r084_simple_16f/（f≈2.912, FER=0.5）与 n4_finite_q1024_r089_simple/（f≈1.989, FER=0.8125）
  - n4_finite_q1024_f129_n1024_4f/（f≈1.296, FER=1.0 decode_failed）
  - n6_comparison_v3_q1024_rates/ 与 n6_comparison_v4_corrected_statuses/
  - n4_finite_q1024_optrho_n512_m64/（自定义 rho，仍 decode_failed）
  - n4_finite_q1024_r089_simple_pp/ 与 n4_finite_q1024_r089_simple_pp2/
    （single-symbol / two-symbol OSD-like postprocess，均未恢复）
  - n4_finite_q1024_f129_muller_2deg_1f/ 与 n4_finite_q1024_r089_muller_4f/
    （Müller 归一化 lambda，仍 decode_failed）
  - n4_finite_q1024_f118_n2048_1f/（长块 f≈1.181，仍 decode_failed）
  - n4_finite_q1024_r089_simple_pp_osd/（OSD 后处理：2 exact / 2 mismatch / 0 failed）
  - n4_finite_q1024_f129_simple_pp_osd_1f/（f≈1.296 OSD-0：exact_mismatch）
- 结论：V19 工程路线已在 q=16 代理和 q=1024 全域跑通（构造+FFT-QSPA+结构化信道）；
  DE 仍受 structured-channel plain ceiling 限制（R≈0.60 / q=1024 需更高 rate）。
- 下一步（用户批准）：已创建 V20 OpenSpec draft
  `openspec/changes/formal-nonbinary-ldpc-v20-q1024-decode-improvement/`；
  冻结后实现 bounded q-ary OSD / 改进构造 / retry。
- 既有 P1/P2/V13 legacy 等冻结终态不变；push 仍待单独授权。

# AGENT_HANDOFF.md

Last verified: **2026-08-16**

## Current State — V13-R3 legacy drift audit：用户决定用 2026-01-21 三源继续，执行完成 (2026-08-16)

**状态：目标完成。** 64 帧 legacy audit 已完成并 verify OK；全量 8412 帧审计也已并行完成（8284 exact_correct / 128 decode_failed / 0 mismatch），合并证据包已生成。

- 用户决定：这些是之前采集的数据，继续使用三份 `2026-01-21` Type2 源运行。
- 新 change：`formal-nonbinary-ldpc-v13-r3-legacy-drift-audit`，claim 仅
  `legacy_drift_audit`。
- 生产执行一次：每源前 64 完整帧、共 192 帧，不变 R3 解码；**188 exact_correct、
  4 decode_failed（iteration_limit）**；只读 verify OK。
- 证据包：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`
- P1 `no_eligible_frames` 冻结终态不变；本结果不构成 fresh/promotion/qualification。
- P2 V17 `mechanism_unverified` 终态不变。
- push 待用户单独授权。

## Previous State — V13-R3 fresh 数据准入已拒绝；D1–D5 已执行，D5 drift_exceeded；P/E/V 不进入 (2026-08-16)


**状态：本目标已完成。** 安全检查（unittest 5/5、smoke_test、compileall）也已通过。

- **D0（已完成）**：`2026-01-21` 三源判定为
  `data_intake_rejected_for_fresh_confirmation`。
  证据：`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_intake_20260816/intake_decision.json`。
  完整修正规划：`docs/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md`。
- **D1–D5（已完成）**：shell 可用后按修正参数执行；三源 sidecar/pairs/manifest
  已生成，`precheck_report.json` 全量预检三源均为 `drift_exceeded`
  （raw SER mean ≈0.240–0.256，偏差远超 0.03 阈值）。P/E/V 不进入。
- **P1**：保持 `v13r3fresh_prepare_20260815/no_eligible_package.json` 冻结终态；
  真正 fresh 数据到达后重新 prepare。
- **P2**：V17 `mechanism_unverified` 终态不变；效率路线冻结。
- **push**：待用户单独授权。
- **用户决策点**：提供真正 fresh 数据，或另开 legacy drift audit change。


## Current State — P2 V17 门冻结终态 mechanism_unverified；P1 阻塞于 fresh 数据 (2026-08-16)

按用户更新后的目标（P0→P1→P2）继续：

- **P0（2026-08-15 完成，仅 housekeeping，无科学执行）**：
  - V12 已正式归档 →
    `openspec/changes/archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`
    （保留 `source_partition_blocked`、X01/X02 未执行、v2 prepare 包；
    归档≠成功、不重开执行；delta spec 未合并；见 archive_note.md）。
  - V15/V16 归档为 **aborted drafts** →
    `openspec/changes/archive/2026-08-15-formal-nonbinary-ldpc-v15-high-rate-candidate-aborted/`
    、`...v16-rate-adaptive-deployment-aborted/`（未立项/前置门失败；
    delta spec 未合并；见 aborted_notice.md）。
  - 陈旧文档已修复：CURRENT_TASK.md、V14 tasks.md（头部状态/测试数字
    62/62→64/64/回放完成）、V13 tasks.md（C01 COMPLETE、IT0-IT3 49/49）、
    记忆 §47/§48。
  - 本地领先 `origin/main` **36 个提交**；push 待用户单独授权。
- **P1（立即优先，冻结终态，阻塞于数据）**: V13 R3 fresh acquisition。
  change `formal-nonbinary-ldpc-v13-r3-fresh-acquisition` 冻结 + freeze
  review ACCEPT；PREP 实现（FA1–FA5，19 测试）+ 生产 prepare 执行一次
  → **`no_eligible_frames`**（`D:\Data` 无 fresh 10 dB Type-II 帧数据
  源，合法冻结结果；包
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_prepare_20260815/`）；
  主线程 review ACCEPT → **frozen failure（数据不可得）**。
  execute/verify 阻塞于 fresh 数据；用户提供新数据后重新 prepare
  （确定性工具）即可继续，不需其他授权动作。
- **P2（冻结终态，FAIL 类）**: 效率研究门
  `formal-nonbinary-ldpc-v17-multibit-structured-de-gate` 生产 gate
  执行一次 → **`gate_state=mechanism_unverified`**（Stage 0 锚点 A
  Δ=0.0075>0.005 失败 → 机制未复现；锚点 B |δ|=0.009≤0.012 通过；
  Stage 1 模型 product-of-marginals 熵 0.549955；Stage 2 12 点诊断
  全部未收敛 diagnostic_only）；strict replay 5/5 字节一致；E02
  独立 gate review **ACCEPT（零 blockers）**；C01 完成（decision-log
  2026-08-16 + 记忆 §52）。位面/边标签效率路线**冻结**：不启动
  V15/V16、不扩大搜索、无 rerun/调参。效率路线下一步只能由用户
  决定另开新 change（② SC-LDPC、③ 多边/高维 λ）。
- **无进行中后台任务**；下一步行动完全取决于用户：① 提供 fresh
  帧数据（P1 继续）或 ② 决定效率路线新 change（或结束）。

---

## Previous State — V13 Existing-Data Nonbinary LDPC Diagnostics: COMPLETE `ready_for_fresh_confirmation` (2026-08-14)

Change: `openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/`

V13 completed the full frozen route: P01-P08 accepted; D01-D04 + DT0-DT3
(27/27); D05 `code`/`diagnosis_complete` (independent review ACCEPT,
zero blockers); R3 code-only candidate `nbldpc_v13_r3_code_v1` (frozen
amendment, IT0-IT3 49/49); E01 64/64 candidate exact (baseline 13/64);
A01 128/128 → `ready_for_fresh_confirmation`; A02 bw120+bw180 128/128
each (no promotion); **C01 independent acceptance ACCEPT (zero
blockers)**; memory triage done (AGENT_PROJECT_MEMORY.md §47). The
maximum V13 claim is `ready_for_fresh_confirmation` — NOT promotion/
qualification/fresh correction. All production packages verified read-only
and committed (ed4bb690 .. 4c0f27a4). The P1 fresh-acquisition change is
the user-decided successor (see Current State above).

- Evidence packages (all under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/`):
  v13_d01_20260814, v13_d04_20260814, v13_d05_20260814_corrected (+
  v13_d05_20260814_invalid_execution_notice.json for the retained first
  emission), v13_e01_20260814, v13_a01_20260814, v13_a02_20260814.
- V14 (efficiency gate) executed after V13: **gate_state=fail** — see
  Previous State below; V15/V16 aborted drafts archived 2026-08-15.

---

## Previous State — V14 Efficiency Gate: FAIL, route frozen (2026-08-15)

Change: `openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/`

V14 executed once and closed at **`gate_state=fail`**: Stage 0 QSC
regression PASS (proxy 0.060 vs published 0.069, |δ|=0.009≤0.012);
Stage 1 folded small-q validation green; Stage 2 all 12 frozen points
(3 λ × m∈{15,16,17,18}, q=1024 structured channel) non-converged
(final base-q entropy 0.288–0.357 vs 0.01 threshold); f 1.032–1.239
all ≤1.3 but convergence binding. E02 independent gate review ACCEPT;
strict replay complete (scientific files byte-identical, manifest
provenance-only diffs); C01 closeout done (decision-log, memory §49).
Budget: wall 87 min, RSS 577 MiB. Consequence: efficiency route frozen
per V14 discipline; V15/V16 not launched (archived as aborted drafts,
2026-08-15). V13 R3 (f≈12.1) remains the only verified corrector.

---

## Previous State — V12 Nonbinary LDPC Real Micro-Feasibility: TERMINAL `source_partition_blocked`, ARCHIVED (2026-08-13; archived 2026-08-15)

Change: `openspec/changes/formal-nonbinary-ldpc-v12-real-micro-feasibility/`

V12 is in TERMINAL STATE `source_partition_blocked`. The four-frame bw200
micro-feasibility canary cannot be executed: the reconstructed traceable 10 dB
pool (2304 rows, 768 per stratum incl. 768 bw200 rows) is 100% covered by
historical frame/payload identities from the V4 10 dB/16 dB transfer locks and
V5 development/partition role locks (2848 excluded frame + 2688 excluded
payload identities; identical union in both prepare runs). Zero fresh eligible
bw200 rows → per design §4 the honest terminal state is
`source_partition_blocked`; a fresh acquisition would be required for any
future four-frame canary.

- Implementation (V12-I01..I05) and engineering acceptance (V12-T0..T2,
  41/41) completed; prepare lane (RP01-RP03) executed and produced the v2
  package with zero eligible rows.
- Official package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
  (v1 intermediate package deleted by explicit user decision).
- tasks.md: V12-T3, V12-RP01..RP03, V12-D01, and V12-D02 checked; V12-X01/X02
  are blocked and were never run.
- Decision-log and memory triage were completed on 2026-08-13.

Recommended next action: the user separately authorizes archiving this V12
change. Archiving does not execute V12-X01/X02, merge unattained requirements,
or manufacture any success declaration; retain the terminal
`source_partition_blocked` state and the v2 three-artifact prepare package.
Only if the user later wants to continue a real canary should a fresh-
acquisition feasibility plan and new OpenSpec change be opened. Do not start
V13 or decoder work before that new acquisition planning boundary.
2026-08-14 supersession: the user explicitly changed this successor decision
to V13 retrospective diagnostics planning first; the V12 fresh-canary identity
boundary itself remains unchanged.

Claim boundary: V12 established no finite decoder correction and no FER,
qualification, or promotion claim.

---

## Previous State — Binary LDPC v5 Phase 4 REAL PROMOTED (2026-08-12)

Change: `openspec/changes/binary-ldpc-v5-incremental-redundancy/`

Binary LDPC v5 sealed real qualification completed and PROMOTED on the real
10 dB Type-II capture — the first real-data promotion for binary LDPC.

- Official package (ten files, run_id `binary_ldpc_v5_real_qualification_v1`,
  plan_sha256
  `a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`):
  `comparison_bench/outputs_comparison/formal_ir_methods/20260801_v2_binary_ldpc_v5_real/`
- Result: 384/384 verified_success — bw120/bw180/bw200 each 128/128, zero
  forbidden failures; report `promoted=true`, `run_status=completed`,
  `decoder_reexecution=false`. Execute ~5m12s, verify ~4m29s, run in a
  detached background process (2026-08-12).
- Promotion domain: 10 dB Type-II, q=1024, Gray, 256-symbol,
  bw120/bw180/bw200, V5-C2 strategy only. v4 (16 dB 125/128, 10 dB 125/128)
  and all other domains/methods remain non-promoted.
- Chain: 20260731 partition lock → 20260731 v5 development (V5-C2,
  1536/1536) → 20260801 v5 synthetic (256/256 promoted) → 20260801_v2 real
  (384/384 promoted), each once with read-only verification.
- tasks.md: Phase 4 all checked with the official result; Phase 5 item 1
  (handoff/decision-log/memory/eligibility/parallel status) checked;
  Phase 5 item 2 (mandatory memory triage) remains for the memory agent.

Next: Phase 5 memory triage (memory agent); then the user decides whether to
open a separate rate-adaptive successor OpenSpec change. Comparison
eligibility: v5 10 dB domain only; other domains/methods unchanged.

---

## Previous State — Nonbinary V11 spatially coupled DE gate: PLAN FROZEN (2026-08-06)

Change: `openspec/changes/formal-nonbinary-ldpc-v11-sc-de-gate/`

V11 is a plan-only successor to the terminated V10 ensemble search. The
literature-backed contract uses a direct QSC SMP threshold reproduction at
q=4/q=16, followed by an independently validated full-vector GF(1024)
spatially coupled MC-DE. It reuses frozen V10 S1/S3 ensembles, compensates
termination rate loss to match the uncoupled effective rate, and evaluates
only G1 `(w=1,L=32,W=8)`, G2 `(w=2,L=32,W=16)`, and G3
`(w=2,L=32,W=32)`. Passing requires absolute .22/.32 robust gates plus at
least .002 paired gain in both strata.

Next: V11-P04 independent read-only freeze review of V11-A01..V11-A16. No
implementation or scientific execution is authorized yet. Even a passing V11
state is only `ready_for_finite_length`; protograph lifting, PEG, FFT-QSPA,
4+4 canary, development, real data, qualification, and promotion require a
new successor OpenSpec change.

Detailed plan: `docs/nonbinary-ldpc-v11-sc-de-plan.md`.

---

## Previous State — Nonbinary V10 DE-PEG-FFT-QSPA: failed_ensemble TERMINATED (2026-08-06)

Change: `openspec/changes/formal-nonbinary-ldpc-v10-de-peg-fftqspa/`

V10 is TERMINATED with final state **failed_ensemble**. The V10A GF(1024)
four-search density-evolution ensemble gate FAILED (hard stop V10-S02);
V10-30 (PEG), V10-40 (FFT-QSPA), V10-50 (canary), and V10-60 (development)
are all HALTED. There is no "closest to gate", no rerun, and no tuning; no
codebook, decoder, canary, development, qualification, real-data, or
promotion output was produced. The successor is a brand-new V11 NB-SC-LDPC
OpenSpec change (fresh everything), pending user decision.

Gate results:
- V10-0 q=4 reference recovery: PASS — conservative 0.06414,
  |δ| = 0.00486 ≤ 0.012; main-thread accepted 2026-08-05.
- S1 (p=.20, f=1.15): conservative 0.2153 < 0.22 → FAIL.
- S2 (p=.20, f=1.08): conservative 0.1984 < 0.215 → FAIL.
- S3 (p=.30, f=1.15): conservative 0.3166 < 0.32 → FAIL.
- S4 (p=.30, f=1.08): no eligible candidate → FAIL.

Evidence (all under the change's `evidence/`):
- `v10_gate_decision.json` — final gate decision (schema
  `v10_gate_decision_v1`, `final_state=failed_ensemble`)
- `v10a_execute_results.json` — official execute (~10470 s, peak RSS
  335 MB < 3 GiB)
- `v10a_replay_evidence.json` — first replay attempt interrupted (PID 21032
  died, S1 only); `replay_attempt2/` completed 04:36–07:07Z (RSS 339 MB);
  129-file direct byte comparison PASS, scientific files byte-identical,
  only provenance normalization differs (plan_binding digest key and
  run_complete role/stage)
- `v10a_gate_decision.json` — per-search gate decisions
- `v10_t3_regression.json` — git baseline PASS, frozen directories zero
  change, no new output under
  `comparison_bench/outputs_comparison/formal_ir_methods/`
- `v10_protocol_amendment_no_hash_v1.json` — 2026-08-06 amendment record

2026-08-06 protocol amendment (main-thread): defensive SHA-256/checksum/
integrity-manifest mechanisms (plan-bound digest, manifest self/source
hash, per-file compare sha256) were removed per AGENTS.md §5.7; the
replacements are git baseline checks, direct byte comparison, structured
field validation, and semantic recomputation. `v10_seed` is RETAINED as a
deterministic RNG derivation primitive — DE population initialization and
mutation RNG streams depend on it and completed results depend on its byte
reproduction. V10-30.DESIGN (PEG no-hash design note) remains unchecked and
is left for V11 inheritance.

Correction + close-out (2026-08-06): `evidence/v10_s4_delta_correction.json`
(schema `v10_s4_delta_correction_v1`) records that the S4 `delta` field in
`evidence/v10a_gate_decision.json` was boolean false (build_evidence
short-circuit bug) — correct semantics is null; evidence untouched, script
expression fixed for future reuse; S4 verdict FAIL and `failed_ensemble`
unaffected. Independent reviewer-go final review ACCEPT
(`evidence/v10_independent_review_acceptance.json`, schema
`v10_independent_review_acceptance_v1`, 2026-08-06, 89 tests pass).
Archive plan: V10 moves to
`openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
without delta-spec merge (failed_ensemble); a scoped local git commit first,
no push; V11 NB-SC-LDPC successor pending main-thread decision.

Tests: full V10 suite 89 passed (common 23 / de 24 / gate 13 / peg 12 /
fftqspa 17). Frozen baseline: git HEAD
`a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`; `src/`, `experiments/`,
`tools/`, `results/` unchanged; the 12 tracked modifications are
pre-existing dirty-worktree entries of other workflows.

Archived (2026-08-06): moved to
`openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
via equivalent rename (archive.js incompatible with the custom V10-xx.y task-ID
schema, fail-closed, no partial state); delta specs NOT merged (V9 precedent);
local commit only, not pushed — archive-move commit 2 =
`921d0020f5fea9bc4452c17453365e2a1a7683f4`.

Next: the user decides whether to start the new V11 NB-SC-LDPC change.
Nothing further is authorized under V10.

---

## Previous State — Nonbinary V9A GF(1024) Long-Block IR: FROZEN STOP (2026-08-04)

Change: `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/`

V9A executed once under the v2 budget protocol (pid 5084, 3968.5 s, peak RSS
428.3 MiB) and strict-replayed once (pid 29340, 4838.5 s). All four frozen
searches (S1 robust .22, S2 target .215, S3 robust .32, S4 target .32) recorded
zero eligible candidates; every gate FAILS. The change is frozen STOP before any
finite codebook. V9B/V9C are unreachable.

Evidence:
- `evidence/v9a_plan_v2.json` (sha256 `4bd6380f19008c9c893b1114fbab94a60d37acb77e3fbdf7a0d03d347092ddf2`)
- `evidence/v9a_execute_results.json` — official execute (restored from
  `workspace/v9a_04c9e7d25d7145659685415084d6fac7/v2_execute/` after the replay
  overwrote the shared evidence path)
- `evidence/v9a_replay_evidence.json` — scientific files byte-identical; only
  `run_meta.json` differs in provenance
- `evidence/v9a_gate_decision.json` — STOP decision
- `evidence/v9a_interrupted_trial_freeze.json` — v1-protocol interrupted trial
  (pid 17948)
- `evidence/v9a_interrupted_v2_attempt_freeze.json` — v2-protocol attempt B
  interruption freeze (pid 23652)

Close-out complete (2026-08-04): independent reviewer-go ACCEPT, SHA256
verification (9/11 byte-identical; 2 provenance-only diffs), acceptance
record `evidence/v9a_independent_review_acceptance.json`.

ARCHIVED (2026-08-05): moved to
`openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/`.
Delta spec NOT synced to main specs (per user choice). No V9B/V9C work was
produced. A successor nonbinary LDPC lane requires a NEW OpenSpec change with
fresh roots, a different ensemble family, and new development/confirmation
data.

---

## Previous State — Nonbinary v7 Successor Ladder COMPLETE: `ladder_exhausted` (2026-08-04)

Change: `openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/`
(proposal/design/specs/tasks/opencode-autonomous-packet all frozen). Route
ladder R1A -> R1B -> R2 -> R3; per route: engineering T0-T3 + independent
acceptance -> sacrificed 4+4 canary (plan -> read-only review -> execute once
-> strict replay once) -> 0/4 in either stratum freezes and advances; else
16+16 development -> readiness gate (>=15/16 per stratum, zero forbidden,
strict replay, disclosure <=8.75 bits/symbol excluding tag, median <=120
s/frame) -> stop at first ready route.

- **R1A** `(2,3)` mother GF(1024) n=256 m=170, flooding FFT-QSPA: accepted
  (T0 19/T1 64/T2 11/T3 97); canary 0/4+0/4 -> `failed_canary`, frozen.
- **R1B** one multiplicative repetition (rate 1/6): accepted (T0 15/T1 76/
  T2 17/T3 119); canary 3/4+0/4 -> `failed_canary` (p=.30 tail), frozen.
- **R2** QSC density-evolution ensemble n=1024 (321/458 checks, DE validated
  vs published BSC/BEC vectors): accepted (T0 32/T1 100/T2 24/T3 142); canary
  0/4+0/4 -> `failed_canary`, frozen.
- **R3** GF(32)xGF(32) multilevel EMS nm=32 (m0=m1=404/558, disclosure
  4040/5580 bits excl. tag, 3.945/5.449 bits/symbol): accepted (T0 19/T1 105/
  T2 33/T3 179, 10/10 review PASS); canary plan reviewed
  READY-FOR-SINGLE-EXECUTION, minimal canary-only authorization edit applied,
  executed once (668.8 s) + strict-replayed once (663.4 s), canary 0/4+0/4 ->
  `failed_canary`, frozen.

**CLOSEOUT (V7-40 done)**: all four routes `failed_canary`; no route reached
development-ready -> first-ready route NONE, **`ladder_exhausted`** TRUE.
Ladder report: `evidence/v7_ladder_report.md`. Every failed artifact retained
immutably under `workspace/nbldpc_v7_*`; NO official
`comparison_bench/outputs_comparison/formal_ir_methods/` v7 directory exists;
HEAD `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344` (no commits during the
ladder). No fourth route invented; a successor requires a NEW OpenSpec change
with fresh development/confirmation data and new roots; current confirmation
rows are not tuning data; qualification/promotion/comparison claims remain
unauthorized. Remaining: V7-41 acceptance + memory triage, V7-42 finalize.
Predecessors: v6 long-block stopped (canary 0/4+0/4), v5 terminated
(4 non-promoted packages). Memory: AGENT_PROJECT_MEMORY.md sections 33-35;
decision-log entries 2026-08-02 (R1A/R1B/R2 canary non-promotion) and
2026-08-04 (R3 canary non-promotion + ladder_exhausted + closeout).

Session-instability note: the Task tool intermittently returned empty
results/cancelled mid-session; every completed stage was verified on disk
before acceptance. Do not treat empty subagent returns as completion — check
the frozen file inventory on disk and retry with a fresh session.

## Project-Wide Agent Workflow (2026-07-29)

**Project-global setting:** this workflow applies by default to every
substantial delegated task in this repository, across binary LDPC, nonbinary
LDPC, Cascade, Polar comparison, data qualification, and future successor
changes. It is not a one-run or one-agent convention. Every new main thread
and subagent must follow it unless the user explicitly overrides it or an
approved OpenSpec change updates `AGENTS.md` §10.1.

Use `AGENTS.md` §10.1 as the authoritative default for all substantial
delegated work. Operationally:

- The main thread freezes one complete task packet before delegation:
  allowed/forbidden files, functionality, full test and tamper matrix,
  commands, artifacts, stop rules, return conditions, and stable acceptance
  IDs.
- The main thread owns planning, requirements, thresholds, OpenSpec,
  acceptance, and scientific conclusions. Terra or another implementation
  subagent acts only as coder/operator.
- The operator returns only a complete candidate or a concrete blocker with
  failing command, exact traceback, attempted remedies, and the one decision
  needed. Do not stop merely to report that work remains.
- Main review normally occurs only at spec freeze, complete candidate
  delivery, and independent acceptance.
- Start successor work from the nearest accepted predecessor and list exact
  deltas; do not replace unchanged evidence machinery with a thinner version.
- Test cadence is T0 compile/structural, T1 focused unit/tamper, T2 complete
  fake qualification/strict replay, then T3 cross-version regression. Run
  T2/T3 only at milestones.
- Verifier work freezes four evidence levels before coding: byte drift,
  locally re-signed semantic tampering, re-signed manifest/index tampering,
  and deep source/transcript/public-payload/leakage/accounting/gate
  reconstruction.
- Test-only execute/verify calls explicitly pass fake runners; never let tests
  fall through to a production decoder or raw-data/output path.
- On Windows, use a fresh additive `workspace/<task>/<uuid>` test root and
  `pytest -p no:cacheprovider`; do not clean inaccessible legacy temp roots.
- Track long-running command/cell IDs and terminate only owned, positively
  identified processes.
- For dirty/untracked worktrees, audit the explicit task-file manifest,
  untracked hashes, frozen-directory diff, and official output-root existence.
- Status messages contain deltas only; do not repeat full history.

This workflow reduces coordination turns and token use. It does **not** weaken
scientific gates: keep prepare/review/execute/verify separate, retain immutable
failures, and preserve every frozen no-rerun/no-tuning rule.

Current workflow change:
`openspec/changes/standardize-agent-delivery-workflow-v1/`.

Compact return format:

```text
change:
deliverable:
acceptance_done:
acceptance_failed:
files:
tests:
outputs:
blocker:
next:
```

## Nonbinary N3 Final State (2026-07-26)

`nbldpc_formal_v1` executed its sole frozen synthetic qualification at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`.
The seven-artifact plan SHA is
`a573cbc5b73856f39bf43b77fcb873017b0db83ebcfcad87d36c5111596237f4`.
Focused N3 tests passed 18/18; N0--N3 plus selected formal regressions passed
65 with 8 skipped. Execution completed once in about nine minutes with no
stderr. Selected policy
`23a1b46300f1c841eed3ffc6f672840c7be17608260de6b09944cac74228983d`
is margin 7, scale 1.0, max_iter 10, 32 checks for both strata.

Confirmation is non-promoted: p=.20 had 18/32 verified successes and 14
decode failures; p=.30 had 5/32 and 27 decode failures. Both denominators are
32 and prohibited failures are zero. Do not tune, rerun, start N4 real data,
or use this as a comparison/performance promotion claim.

Important verifier boundary: official CLI strict verification failed solely on
live whole-worktree `git_status_sha256` drift after execution. Frozen source,
CLI/contract hashes, commit, Python and NumPy matched. A diagnostic read-only
`verify(..., _test_only=True)` replay verified artifacts/DAG/gates in 549.3 s,
but is not an official strict-verifier pass. Treat the package as immutable,
non-promoted, and strict-verification-failed/unverifiable.

## Resume Here

- Use local branch `codex/feat/polar-diagnostics-occupancy`, currently at `71bda20`.
- Against the local (not freshly fetched) tracking ref, this branch is 5
  commits ahead of `origin/codex/feat/polar-diagnostics-occupancy`.
- `main` contains only the initial Polar release and does not contain the comparison framework or this handoff.
- Read `AGENTS.md` and `AGENT_PROJECT_MEMORY.md` before changing files.
- Detailed comparison state is in `docs/ir-method-comparison-state-20260615.md`.
- Current evidence reports are:
  - `docs/real-ir-success-audit-20260615.md`
  - `docs/ir-optimization-report-20260615.md`
  - `docs/expanded-real-ir-evidence-20260615.md`
  - `docs/group-meeting-ir-analysis-20260615.md`
- Route A correctness boundaries are in:
  - `docs/ROUTE_A_CORRECTNESS_BASELINE_20260410.md`
  - `docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md`
  - `docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md`

## Verification Performed In This Pass

- Ran the comparison tests that do not write to fixed repository paths:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest comparison_bench\tests `
  --ignore=comparison_bench\tests\test_evidence_package.py `
  -q -p no:cacheprovider `
  --basetemp C:\Users\admin\AppData\Local\Temp\hdqkd-handoff-pytest-20260725
```

- Result: **15 passed in 3.08 s**.
- `test_evidence_package.py` was not rerun because it uses the fixed tracked path
  `workspace/pytest-evidence-test`; its OpenSpec verification note records an
  earlier full-suite result of 37 passed.
- No smoke benchmark, full real-data benchmark, v3 master sweep, Route A rerun,
  or output-generating command was run in this pass.

## Current IR Comparison State

### Representative Real-Frame Baseline

`comparison_bench/outputs_comparison/real_ir_success_first/ir_benchmark_results.csv`
contains 24 rows across 6 representative datasets:

- `cascade_lite`: 6/6 rows classified `real_ir_success`
- `layered_ldpc_lite`: 6/6 rows classified `real_ir_success`
- `polar_existing`: 1 `real_ir_success`, 5 `decode_failed`
- `qldpc_reference`: 6/6 rows classified `reference_only`

The representative points cover `d=8,16`, four frames per point, and raw SER
up to 23.83%. This is useful bounded evidence, not broad production proof.

### Optimization And Expanded Evidence

- Cascade sweep: 216 rows; 37 `real_ir_success`, 179 `verified_failure`.
- Layered LDPC sweep: 240 rows; 51 `real_ir_success`,
  50 `decode_improved_but_unverified`, 139 `decode_failed`.
- qLDPC sweep: 84 rows, all `reference_only`.
- The group-meeting package contains 704 sweep-task rows and an 825-row
  success summary over 14 real datasets and frame lengths 64/128/256.
- The current evidence-backed recommendation is:
  - **Cascade-lite**: preferred executable non-Polar candidate; most robust
    overall, especially at higher noise.
  - **Layered LDPC**: secondary/control baseline; often faster and competitive
    at low noise, but less robust at high noise.
  - **qLDPC reference**: feasibility/reference only, not production-ready.
  - **polar_existing**: historical imported baseline, not a same-run,
    frame-identical rerun.

Do not promote the recommendation to a final production method without
resolving the evidence limitations below.

## Evidence Limits That Must Stay Visible

- Low-dimensional real-data points have only four 64-symbol frames; 256-symbol
  low-dimensional points may have only one frame.
- Polar evidence is a coarse historical import and is not directly comparable
  to frame-level executable baselines.
- Some reported Cascade leakage reductions compare pre-upgrade approximate
  accounting with later `exact_internal_transcript` accounting.
- Broader evidence shows failure regions above roughly 20% raw SER; the
  six-point representative success result must not be generalized blindly.
- `beta_eff_empirical=0` in several short/medium-frame runs is a derived result
  of leakage exceeding the finite-block Shannon denominator, not a missing
  value to hand-fill.

## Route A / Security-Line State

- The branch contains the Route A per-block universal-hash verification
  interface (`uhv1_per_block`) and resumable formal replay tooling.
- Only `epsilon_EC_bound` enters the formal correctness budget; empirical
  undetected-error rate and oracle decoder-failure rate remain audit fields.
- Safe claim: Route A correctness-side verification accounting is formalized
  under the calibrated actual-IR finite-key shadow.
- Unsafe claim: strict full Zhong 2015 or Niu 2016 proof completion.
- The result roots referenced by `docs/LATEST_RESULTS_20260327.md` were not
  present in this checkout or at the legacy `D:\Code\HD-QKD_Polar_Release`
  paths on 2026-07-25. Treat those numeric result claims as historical,
  currently unavailable for local revalidation.
- Do not run `longrun_*`, `minrerun_*`, or `routeA_*` commands unless explicitly
  requested.

## OpenSpec And Coordination Debt

OpenSpec task files and existing artifacts are out of sync:

- `consolidate-real-ir-evidence-package`: 26/26 task items checked; 8/10
  acceptance criteria independently evidenced.
- `optimize-real-ir-methods-after-success`: 14/14 task items checked; its
  separate 512/1024-symbol spec requirement remains unsupported by the
  128/256/2048 evidence.
- `expand-real-ir-optimized-evidence`: 19/20 task items checked; only direct
  evidence-package pytest is deferred because of its fixed tracked-path fixture.
- `group-meeting-ir-large-comparison`: 21/29 task items and 6/10 acceptance
  criteria checked; sample-size, absent config/test, full-suite, and immutable
  baseline/no-overwrite gaps remain.
- `real-ir-success-first`: 32/34 task items checked; immutable-baseline and
  historical no-overwrite review remain unproven.

All five historical changes remain under `openspec/changes/`; none has been
archived into `openspec/specs/`.

### Phase 0 Reconciliation (2026-07-25)

`docs/openspec-phase0-reconciliation-20260725.md` is the authoritative
evidence matrix for the five active changes. No change was archived: reports
and output manifests exist, but written acceptance gaps remain. In particular,
the optimization spec names 512/1024-symbol support absent from current
evidence; group-meeting low-dimensional datasets have 4 rather than >=16
frames; and the evidence-package test has a fixed tracked workspace path and
was not rerun in the current worktree.

`CURRENT_TASK.md` now routes Phase 1 to a new, pre-registered
`final-ir-method-selection` change. It must use frame-identical candidates,
separate tuning from confirmation, and preserve method-specific leakage
semantics.

## Worktree Warning

Before this handoff edit, `git status` showed six deleted tracked files under
`workspace/pytest-tmp/`. They are test-generated artifacts, are not part of the
handoff diff, and the cause of their current deletion state was not established.
Do not stage or restore them without first deciding whether tracked pytest temp
artifacts should be retained.

## Recommended Next Steps

### Formal Shared Core Complete (2026-07-25)

- Active change: `openspec/changes/implement-formal-cascade-and-ldpc/`.
- Shared Phase 1--2 code is additive in
  `comparison_bench/src/comparison_bench/formal_ir/shared.py`; it does not
  modify legacy dataclasses, lite methods, frozen Polar directories, or outputs.
- It freezes the six artifact names/status semantics, `ldpc==2.4.1`
  version/API fail-closed preflight and R4 decoder parameters, exact 64-pair
  provenance checks, locked MSB-first Toeplitz seed/tag rules, and canonical
  public transcript validation/accounting.
- `python -m pytest comparison_bench/tests -k formal_verification -q` passed
  6/6 on 2026-07-25. No formal qualification output was generated.
- Phase 3 Cascade is now additive in `formal_ir/cascade.py`: fixed four-pass
  PCG64 schedule, cached one-bit parity/bisection, FIFO completed-pass
  look-back/re-entry, caps, locked Toeplitz verification, and public
  transcript-safe diagnostics. Focused formal tests passed 11/11 and the safe
  comparison regression (excluding fixed-path evidence) passed 32/32. No
  outputs were generated. Next is Phase 4 LDPC; preserve the six pre-existing
  tracked `workspace/pytest-tmp/` deletions.
- Phase-4 preflight hit a documented/API drift stop condition: pinned
  `ldpc==2.4.1` advertises `random_serial_schedule` in its docstring but rejects
  the kwarg at construction. The active spec now removes that kwarg and
  requires determinism through `schedule=serial`, explicit order `[0..63]`, and
  one OMP thread. The reopened preflight task must perform a no-decode
  constructor probe using a 1-by-64 uint8 `H` with only `H[0,0]=1`; the revised
  kwargs probe succeeded read-only on this machine. Phase 4 remains incomplete
  until implementation and tests match the revision.

### Current Planned Direction: Formal Candidates Before Three-Way Comparison

The active next OpenSpec is
`openspec/changes/implement-formal-cascade-and-ldpc/`. Its purpose is to build
paper-grade offline candidates `cascade_formal_v1` and `ldpc_formal_v1` before
any fair Cascade/LDPC/Polar comparison. The existing lite methods and their
evidence remain unchanged and must not be promoted by label.

The change fixes a shared 64-bit universal2 Toeplitz verification/transcript
contract, key-dependent versus public-control disclosure accounting, full FIFO
Cascade look-back, and fixed-family codebook-backed LDPC with a pinned
`ldpc==2.4.1` decoder. It excludes Polar adaptation, a winner claim, Route-A
numerics, shortening/puncturing, network/authentication cost, and hardware
real-time work. See its proposal/design/tasks for acceptance commands and
stop conditions; all generated evidence must be additive.

After design review, implementation details are no longer left to the coder:
the Toeplitz indexing/seed lock and canonical JSONL bytes, Cascade cache/FIFO/
re-entry semantics and hard caps, HGF2V1 four-rate codebook construction,
calibration-only `p_hat` selector, exact BpOsd parameters, six artifact names,
status precedence, composite source keys, and synthetic/real promotion
thresholds are frozen in the active spec. The planned real lock uses fresh
`bw100` calibration and group-disjoint `bw120` confirmation frames and must
have no frame-key overlap with final-IR v1.

The prior archived final-selection result remains `no_decision`; do not use it
as a formal-method comparison or as a reason to tune a confirmation set.
Either formal method may be archived as `non_promoted`; only promoted formal
methods can enter a future Polar comparison, and lite substitution is forbidden.

Read-only qualification-data preflight on 2026-07-25 found the existing
`real_sidecars_frame_batch.parquet` source (SHA256
`967f569c3b3977cc9846025fc9af9b2faf3aa7d89b4e52e0d0ca804f5ab972cc`)
contains 468 complete 64-symbol `d1024/bw100` frames and 469 complete
`d1024/bw120` frames. Respectively 295 and 322 have frame SER in
`[0.20,0.30)`, with unique `pair_idx=0..63`, so the planned 60+60 lock is
feasible. This is availability evidence only: the implementation must still
create/review a fresh ordered lock, source hash, zero overlap with final-IR v1,
calibration, and CSPRNG verification seeds before any run.

### Historical Suggested Steps (Superseded By The Formal-Candidate Direction)

1. Complete Phase 2 data lock for `final-ir-method-selection`: declare the
   supported domain, sample/confidence rule, and bounded stopping rules.
2. Freeze exact shared frame IDs plus a disjoint tuning/confirmation split,
   source/preprocessing/config hashes, seeds, commit, dependencies, and
   environment before tuning.
3. Reserve an additive output directory and verify the common preprocessing,
   success classifier, and independent verification contract for both
   executable candidates.
4. After the lock, tune only on the tuning split and freeze one global config
   per candidate before any confirmation run.

Ponytail-lite alternative: finish the manifest-backed data lock before creating
new benchmark outputs; no numerical rerun is needed to establish this protocol.

## Phase 1: Final IR Method-Selection Protocol (2026-07-25)

- New active change: `openspec/changes/final-ir-method-selection/`.
- Phase 2 is data lock, not a benchmark run: freeze exact common frames and a
  disjoint tuning/confirmation split before any tuning.
- Only `cascade_lite` and `layered_ldpc_lite` are executable winner candidates;
  qLDPC is `reference_only`, while Polar remains historical context because its
  bridge has aggregate dimension/bin-width matching but no frame-ID/replay
  binding, a one-row tracked fixture, and legacy unavailable sources.
- The confirmation protocol requires one global frozen configuration per
  candidate, all attempted failures in denominators, separated incompatible
  leakage accounting, provenance manifests, bounded stopping, and a
  non-numerical Route A required-field compatibility gate.

## Phase 2: Data Lock Complete (2026-07-25)

- Additive evidence directory:
  `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`.
- Locked claim domain: real d=1024, 64-symbol frames, with dataset-level raw
  SER in [0.20, 0.30). It is one required medium-SER stratum only; no claim
  extends to other dimensions, frame lengths, or SER regions.
- `locked_frame_split.csv` holds 60 tuning and 60 confirmation composite frame
  IDs. The two partitions are group-disjoint by dataset/source: tuning uses
  `real_typeii_20db_d1024_bw200_blk0`, confirmation uses
  `real_typeii_20db_d1024_bw180_blk0`.
- `data_lock_manifest.json` records source/split/config hashes, the seed,
  commit/environment, shared preprocessing/mapping/verification contract,
  exact two-sided McNemar/binomial rule at alpha=0.05, and no-decision rules.
  Its 60-frame confirmation rule gives a zero-failure 95% upper bound of
  4.87%.
- Verify the lock before Phase 3 with:
  `python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --verify`.
- The focused `test_data_lock.py` was added. Pytest setup/teardown in this
  Windows worktree currently returns `PermissionError` on its disposable
  basetemp after executing the test; the generated lock itself was created and
  hash-verified by the CLI. Do not reinterpret that infrastructure issue as a
  benchmark outcome.

## Phase 3: Bounded Run Complete (2026-07-25)

- Keep `20260725_v1/data_lock_manifest.json` and `locked_frame_split.csv`
  authoritative and read-only. Its first Phase-3 outputs used a grid that had
  not passed the fairness review; `20260725_v1/invalid_run_notice.json`
  excludes those outputs from every decision.
- The only authoritative Phase-3 outputs are additive
  `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v2/`.
  Its `run_manifest.json` references and hashes the v1 lock manifest and
  verifies the source hash before reconstructing the same 60 tuning and 60
  confirmation frames.
- The fixed grid was persisted in `predeclared_tuning_grid.json` before any
  run: four reviewed Cascade schedules and four reviewed medium-SER LDPC
  settings. Tuning selected one global configuration per method, with no
  per-frame/per-point oracle: Cascade `[12,6,24,13]`, 4 passes,
  seeded-random gray (`1725a914f7084a6a`); LDPC parity 1.0, 50 iterations,
  `bsc_estimated`/`uniform`/gray (`d113d97b728b14c2`).
- v2 confirmation completed in 3.329 s under its declared 600 s cap. Both
  candidates attempted every locked confirmation frame: Cascade 60/60
  independently verified successes; LDPC 59/60. All 120 statuses are in
  `confirmation_frame_outcomes.csv`; tuning has all 480 attempts. Leakage is
  explicitly method-specific and is not cross-method ranked.
- qLDPC and Polar were not run. qLDPC remains `reference_only`; Polar remains
  historical/non-frame-identical context.

## Next Step: Phase 4 Audit

Audit only the v2 artifacts: frame identity and lock/source hashes, frozen
configuration ordering, all attempted-frame denominators and status preservation,
the pre-registered paired decision rule, leakage separation, and the Route A
required-field compatibility gate. Do not alter v1 or v2 outputs.

## Phase 4: Audit And Bounded Decision Complete (2026-07-25)

- Authoritative additive audit evidence is at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`: `audit_manifest.json`, `immutable_hash_ledger.json`, `paired_decision.json`, `route_a_compatibility_gate.json`, and `decision_report.md`. The v3 audit is superseded by its `superseded_notice.json` because its generic decision helper lacked the LDPC-winner and insufficient-evidence branches; the current p=1.0 result remains unchanged.
- It hashes referenced v1/v2 evidence, confirms both candidates used the same 60 unique locked confirmation keys, confirms both frozen configurations occur in the persisted corrected tuning grid, and confirms all 120 attempted status rows agree with aggregate denominators.
- Cascade is 60/60 and Layered LDPC 59/60; the only discordance is Cascade-success/LDPC-failure. The exact pre-registered two-sided McNemar/binomial p-value is **1.0** at alpha 0.05, so the bounded outcome is **`no_decision`**. Do not describe Cascade as a final winner from this run.
- Leakage is retained separately (Cascade 33664 bits; LDPC 40320 bits) but is expressly not cross-method ranked.
- The non-numerical Route A compatibility gate is **fail**: comparison frame outputs lack the documented `uhv1_per_block` protocol/family/scope/seed/tag, verification-leakage/lambda, and epsilon/empirical/oracle correctness fields. No Route A numerical run or proof claim was made.

## Next Step: Phase 5 Hardening

Run only focused disposable tests/static checks for the new audit CLI, review the immutable-boundary/no-overwrite diff, complete memory triage, and then perform the final completion audit. Preserve the six pre-existing tracked `workspace/pytest-tmp/` deletions.

## Phase 5: Hardening, Memory Triage, And Archive Complete (2026-07-25)

- `comparison_bench/src/comparison_bench/data_lock.py` now exposes a pure,
  deterministic group-disjoint selection helper. Its focused test is an
  in-memory `unittest`; hash/file-I/O evidence remains the lock CLI verification.
- `audit_final_ir_method_selection --verify` revalidates the existing v4 audit
  read-only. It verifies the persisted audit, decision, Route A gate, and hash
  ledger without creating or overwriting output. `lock_final_ir_data --verify`
  remains the read-only v1 lock check.
- New runs must pass an explicit `--output-dir`; the Phase-3 runner writes
  `pre_run_plan.json` before tuning so the declared bounds survive an interrupted
  run. The dynamic audit uses the lock manifest sample counts and renders
  observed candidate counts/discordances rather than hard-coded prose.
- Runbook: `comparison_bench/docs/final_ir_method_selection_runbook.md` gives
  the exact authoritative v1/v2/v4 paths, invalid/superseded evidence, commands,
  output policy, bounded `no_decision`, and Route A gate limit.
- Verification on 2026-07-25: `py_compile` passed for all five Phase-2--4
  modules; `python -m unittest comparison_bench.tests.test_data_lock
  comparison_bench.tests.test_final_selection_audit_unittest -v` passed 7/7;
  read-only v1 lock and v4 audit verification passed; safe comparison pytest
  excluding fixed-path `test_evidence_package.py` passed **22/22 in 0.67 s**
  using `C:\Users\admin\AppData\Local\Temp\hdqkd-phase5-pytest-20260725`.
  No teardown ACL failure occurred in this pass.
- `git diff --name-only -- src experiments tools` was empty. The six pre-existing
  tracked `workspace/pytest-tmp/` deletions remain untouched. No existing result
  or comparison-output path appears in the Phase-5 tracked diff.
- Memory triage is complete in `AGENT_PROJECT_MEMORY.md`; it records only the
  verified Phase-0 blockers, final-IR protocol, v1/v2/v3/v4 evidence chain,
  bounded result, Route A gate, test evidence, and worktree caveat.
- `final-ir-method-selection` is archived at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/`; its delta
  spec was merged into `openspec/specs/final-ir-method-selection/spec.md`.
  The authoritative chain remains v1 lock, v2 run, v3 superseded, and v4
  audit: 60/60 Cascade versus 59/60 LDPC, exact paired p=1, `no_decision`, and
  non-numerical Route A gate `fail`.
- Do not archive the five historical IR changes: their Phase-0 reconciliation
  blockers remain active. Preserve the six pre-existing tracked
  `workspace/pytest-tmp/` deletions.

## Formal IR Phase 4 Complete (2026-07-25)

- Active change: `implement-formal-cascade-and-ldpc`; Phases 1--4 are checked.
- `comparison_bench/src/comparison_bench/formal_ir/ldpc.py` adds
  `ldpc_formal_v1` without modifying `layered_ldpc_lite` or frozen Polar code.
- Its four deterministic rates materialize 40 exact HGF2V1 matrices
  (4 rates x 10 planes) into a fresh directory and fail closed on any
  filename/hash/dimension/rank/generator/manifest mismatch.
- Calibration accepts only explicitly labelled sacrificed tuning frames and
  freezes source hash plus a canonical hash of dataset, ordered unique
  sacrificed frame keys, mapping, and dimension. Each plane records its
  selection hash, mapping, integer counts, exact `p_hat`, and selected rate.
  Confirmation recomputes and validates all of them before attempting decode;
  current Alice truth is used only for the protocol syndrome and diagnostic
  `raw_ser`.
- The production decoder path uses installed `ldpc==2.4.1` with serial
  schedule, explicit `[0..63]` order, one OMP thread, OSD-0, and no fallback.
  Its public entrypoint has no decoder/preflight/clock/cap test seam; private
  tests use the unexported `_run_ldpc_formal_for_test` core.
  The shared no-decode constructor probe succeeds. A real-backend single-error
  q=2 frame returned `verified_success`.
- Syndrome, matrix/rate control, locked Toeplitz seed/tag, transcript secrecy,
  explicit corrected-plane syndrome consistency, disclosure totals, status
  precedence, retained denominators, and both pre/post-verification five-second
  aborts were exercised. Focused formal tests passed 18/18;
  `py_compile` passed; safe comparison pytest excluding fixed-path
  `test_evidence_package.py` passed 40/40 outside the Windows sandbox with the
  file-test gate enabled.
- A real `tempfile.TemporaryDirectory` test materialized and verified all 40
  manifest entries, counted all 40 files, compared the persisted manifest,
  rejected overwrite and path traversal, and cleaned up. No qualification
  output, staging, commit, or push occurred.
- Next task is Phase 5 bounded synthetic qualification. Freeze and review its
  immutable pre-run plan before creating any additive evidence.

### Formal Phase 5 historical review gate

- `20260725_v1_synthetic` is a failed pre-execution plan only. Its notice
  records zero formal-frame calls and makes it ineligible for qualification.
- v2 subsequently ran, but the observed evidence below supersedes the earlier
  pre-run expectation. Its CSPRNG verification seeds do not repair its
  generation-contract violations.

### Formal Phase 5 observed v2 evidence

- v1 is excluded: its notice records zero frame calls and hashes its sole plan.
- Deep review excludes v2 from promotion. Its plan declared Alice seed
  `2026072501` and frame-order seed `2026072531`, but neither was used; batches
  instead used undeclared Alice seeds `2026072502..2505`. Its 128 outcomes,
  counts, transcript, and prior verifier pass remain diagnostics only.
- Add `invalid_run_notice.json` to v2 without changing existing bytes and point
  it to a fresh v3. No method is synthetically promoted from v1 or v2.
- Phase 5 is reopened. v3 must implement the exact one-generator/four-batch
  generation order, exact noise seeds and gray input, order-only global
  permutation, qualification-only shared verification seeds, exact method
  event bytes/group hashes, runner deterministic preflight, complete
  source/version/git/config provenance, exception-safe six-artifact finalizer,
  and strict read-only verifier specified in the active OpenSpec.

### Formal Phase 5 v3 qualification (2026-07-25)

- Fresh additive evidence is immutable at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
  The sole execution exited 0 in 4.7666172 s; the read-only verifier exited 0
  with 128 outcomes.
- SHA256: plan `22e4310e5301c7ebc2dcf26ea0daff78f1e30e7203470c295121e20269240e45`;
  outcomes `a5b27043cab32156ad217f2c097db8f298b6cbee30226746f389333fa03b14dd`;
  transcript `1279ad014b3f2788b666b12e6d6a39fd00eb8dbf131e69cf052bce00d47e00fc`;
  codebook manifest `a89992bc3aa49bf2fe976e10c8520948d6560a1d108bf3da7044d5b6efb62516`;
  run manifest `4b59f2de07e370652ab191dd1124c29c92b3b194ce0b8ed0b6df88dc817d038b`;
  report `d005ef4d7a7143c22e7dfd23e3c0c6def99f4761397e4158ff89cfc9c1ce97f5`.
- Cascade has 32/32 `verified_success` at both p=.01 and p=.02 and is
  synthetically promoted. LDPC has 29/32 and 14/32 and is synthetically
  non-promoted. The 21 other outcomes are `verify_failed`; no unclassified,
  internal, provenance, or accounting failures occurred.
- Keep v1/v2 diagnostic only. Do not retune LDPC or substitute a lite method;
  Phase 6 fresh locked real qualification remains incomplete and no Polar
  comparison is authorized.

## Formal Phase 6 Qualification And Phase 7 Review (2026-07-25)

- The invalid real v1 lock was never executed. Only
  `invalid_lock_notice.json` was added (SHA256
  `9f9d72f6c1e39467f08b86a514851b78a8aaf6a8ef2fb1f869b22f60e980d556`);
  its original plan
  `3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`
  and lock
  `aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
  remain byte-identical. Formal method calls from v1: zero.
- The sole runnable real root is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`.
  Its strict read-only verifier accepts exactly seven artifacts:
  - plan `ef0c496d4679c8a790fa6715fca010c65bbe80dbcc9fb1a640139750e8f87161`
  - lock `fea6d1e9912415c37f78393ef7d5e5e9bae156531bc9e6bd9a07936c41a09348`
  - outcomes `d3ef26555e19fa58d74e40ccc9dc253e27db058a1b79720e77ab265f652c01f0`
  - transcript `f95478b529f13871846400395d97b9d8a4f1948ddd30859a16dd7f66074a34c8`
  - codebook manifest
    `e8fbbd2ca195c8aa6d4a2ca8c821c2f8bb0eb73e6830ac85fff4558ef329738c`
  - run manifest
    `42d18066cc13740fd4367430b0319020ec4b943e5c01bf43f4df0759257ce172`
  - report `750aaebf4919aa9a66383e6e4bf2d441efd718324ebca564157e6607d2b21e1b`
- The preflight passed 29 tests, exited 0, and recorded exact output SHA256
  `8760383422fb96ce6b8d644333e52064287e394f2827f57459bc110ded0a7a7c`.
  The real gate retained 60/60 requested, attempted, denominator-included,
  verification-invoked, and `verified_success` frames. Union bound:
  `3.2526065174565133e-18`; unclassified/internal/provenance/accounting
  failures: zero. Cascade is promoted only within `d=1024`, 64-symbol, bw120,
  frame-SER `[0.20,0.30)` confirmation evidence.
- Synthetic v3 remains authoritative: Cascade is 32/32 at both strata and
  promoted; LDPC is 29/32 and 14/32 and non-promoted. No real LDPC run
  occurred.
- Phase 7 evidence: synthetic-v3 and real-v2 read-only verifiers passed; the
  safe non-formal regression passed 22/22 in 0.66 s; `git diff --check` exited
  0 with only known ACL/LF warnings; frozen `src/`, `experiments/`, `tools/`,
  and `results/` diffs were empty; independent audit result: PASS.
- The active `implement-formal-cascade-and-ldpc` change is technically ready
  for archive review, but memory triage and actual archive have not yet
  occurred. Do not describe it as archived.
- Next create a separate LDPC-improvement OpenSpec change. Only fresh synthetic
  plus real LDPC promotion may unlock a frame-identical
  Polar/Cascade/LDPC comparison. Lite substitution and confirmation-set tuning
  remain forbidden.

## Formal IR OpenSpec Archive Complete (2026-07-25)

- Archived change:
  `openspec/changes/archive/2026-07-25-implement-formal-cascade-and-ldpc/`.
- Canonical specification: `openspec/specs/formal-ir-methods/spec.md`.
- Final state: `cascade_formal_v1` is promoted by synthetic v3 and bounded
  real v2 evidence; `ldpc_formal_v1` is synthetically `non_promoted` and was
  not run on real data.
- A new LDPC-improvement OpenSpec change is the next required work, but it has
  not yet been created. Do not start a direct frame-identical
  Polar/Cascade/LDPC comparison before fresh LDPC synthetic and real
  promotion.

## LDPC v2 Improvement Change Opened (2026-07-25)

- User accepted the external-reference-informed direction:
  - keep `quantumgizmos/ldpc` / pinned `ldpc==2.4.1` as the short-term decoder;
  - use more conservative finite-length rate margins and stronger deterministic
    OSD variants on sacrificed development data;
  - use CV-QKD/TBPRL repositories as architecture/code-family guidance only,
    not as drop-in n=64 matrices;
  - treat nonbinary LDPC as a later separate research lane.
- New active change:
  `openspec/changes/improve-formal-ldpc-v2/`.
- Short-term target: additive `ldpc_formal_v2`, global pre-registered
  rate-margin/decoder policy, no confirmation oracle, fresh synthetic
  qualification.
- Medium-term target: deterministic n=64 rate-compatible,
  protograph-inspired candidate family with rank/structure/low-weight probe
  screening and a fully hashed selected-codebook manifest.
- Promotion remains unchanged: at least 31/32 verified successes in each
  synthetic p=.01/.02 stratum, then a fresh locked 60/60 real qualification.
  Only after both gates may a separate change authorize the fair
  Cascade/LDPC/Polar comparison.
- The user initially considered Luna, then explicitly selected
  `gpt-5.6-terra`, reasoning `low`, for implementation.
- Division of responsibility is strict: the main thread owns planning,
  OpenSpec interpretation/changes, thresholds, acceptance, and final review.
  Terra low is an implementation operator only: it receives frozen tasks, edits
  only the named files, runs only authorized tests, and must stop rather than
  resolve ambiguity or redefine requirements.
- Ponytail-lite boundary: reuse the pinned backend and formal artifact
  machinery first; add a new dependency only if measured v2 evidence proves
  the existing backend cannot meet the promotion gate.

## LDPC v2 Frozen-Task Execution Evidence (2026-07-26)

- The change completed as non-promotion evidence and is archived at
  `openspec/changes/archive/2026-07-26-improve-formal-ldpc-v2/`.
- `ldpc_formal_v2` adds exactly nine pre-registered policies: rate margins
  0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, and `OSD_CS/2`. Its nested n=64
  codebook has 16 masters per plane and selected prefix matrices
  32/40/48/56. Structural screening is a proxy only, not verified decoding
  evidence.
- The v1 integration root `20260725_v1_ldpc_v2_synthetic` is invalid: all
  576 policy outcomes plus 64 associated outcomes are `unsupported_domain`
  because the v1 codebook verifier rejects the v2 codebook. Its seven
  artifacts remain immutable and an additive invalid notice is present.
- The fresh v2 plan SHA256 is
  `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`;
  old/new CSPRNG overlap is zero. Strict verification passed. Development
  results are margin 0: 26/64, margin 1: 33/64, margin 2: 56/64, identical
  across OSD variants; selected policy is `rate_margin=2`, `OSD_0/0`.
- Synthetic confirmation is 28/32 at p=.01 and 29/32 at p=.02, with seven
  `verify_failed`; verification was invoked for all 64 outcomes and there are
  zero unclassified/internal/provenance/accounting failures. Result is
  `non_promoted`. No real-data lock or run is authorized, and confirmation
  evidence must not be used for further tuning.
- Artifact SHA256 values: plan `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`,
  codebook `360b77...`, outcomes `9adb0...`, policy `303919...`, transcript
  `4b438...`, manifest `d185fc...`, report `53fbe5...`.
- Final verification: v2-focused file tests 25 passed plus 5 subtests;
  general tests 52 passed, 11 skipped; formal-real tests 12 passed; strict
  verification passed; and `git diff --name-only -- src experiments tools` is
  empty.
- Division of responsibility: Terra low executed frozen tasks and specified
  tests only. The main thread retained planning and acceptance.
- Conclusion: the short- and medium-term engineering work is complete with
  reproducible evidence, but LDPC has not met promotion and a fair three-method
  comparison remains blocked.

## Parallel Binary / Nonbinary LDPC Direction (2026-07-26)

- The project will now advance binary and nonbinary LDPC as independent,
  parallel research lanes.
- The detailed working handoff is
  `comparison_bench/docs/ldpc_parallel_handoff.md`.
- Binary starts from the immutable, non-promoted `ldpc_formal_v2` evidence and
  moves toward longer frames, deterministic QC/PEG/protograph code families,
  incremental redundancy, and per-bit-plane soft information.
- Nonbinary starts as a new formal lane, provisionally
  `nbldpc_formal_v1`. Existing `qldpc_reference` remains reference-grade and
  must not be relabeled or used as formal qualification evidence.
- The lanes have separate codebooks, development/confirmation data, manifests,
  transcripts, leakage accounting, verifiers, and promotion decisions. A gate
  passed by one lane does not promote the other.
- Before implementation, create separate OpenSpec changes:
  `binary-ldpc-long-frame-and-ir-v3` and
  `implement-formal-nonbinary-ldpc`.
- This documentation update authorizes no experiment, dependency installation,
  real-data run, or comparison claim. A later fair comparison may include only
  independently promoted formal methods on frame-identical inputs.

## Binary LDPC Long-Frame v3 Phase 1 (2026-07-26)

- Active change:
  `openspec/changes/binary-ldpc-long-frame-and-ir-v3/`.
- Terra low implemented the frozen candidate-codebook work package only; the
  main thread resolved specifications and performed acceptance.
- Added `codebook_long_v3.py` and its focused test. The component supports
  candidate-only n=256/512/1024 nested matrices, HGF2V3 canonical bytes,
  structural proxies, and a reconstruction-verified 120-candidate manifest.
- Main-thread verification passed: focused 4/4 in 10.88 s, v2 regression
  7 passed/1 skipped in 81.41 s, `py_compile`, scoped `git diff --check`, and
  empty frozen-directory diff.
- Phase 1 does not run a decoder or measure FER, does not select a production
  code family, does not read confirmation/real data, and does not change
  `ldpc_formal_v2` non-promotion.
- Next planner-owned work is to freeze a sacrificed-development FER evaluation
  contract before any candidate selection or decoder integration.

## Binary LDPC Long-Frame v3 Phase 2 (2026-07-26)

- The frozen in-memory sacrificed-development FER kernel is implemented in
  `long_v3_development.py`; it does not modify v1/v2 or write result artifacts.
- It deterministically generates 16 p=.01 and 16 p=.02 frames per n/plane,
  freezes the pinned BP+OSD-0 decoder contract, retains incremental
  syndrome-round statuses/disclosure, and selects among exactly four
  candidates without a runtime oracle.
- Main-thread verification passed: focused 5/5 in 0.53 s, Phase1/v2 regression
  11 passed/1 skipped in 92.68 s, compilation and protected-directory checks.
- This accepts the evaluation kernel, not candidate performance. Tests used
  injected decoders; the full pinned `ldpc==2.4.1` development sweep has not
  run and no candidate is selected.
- Next freeze a bounded real-backend preflight/pilot before authorizing the
  complete 3-length x 10-plane development sweep.

## Binary LDPC Long-Frame v3 Phase 3A Pilot (2026-07-26)

- One frozen in-memory real-backend pilot ran exactly once:
  n=256/plane0/candidate0/p=.01, 16 sacrificed frames.
- Backend was pinned `ldpc==2.4.1`; exit 0; stderr empty; process 0.3227008000 s;
  external wall 1.0 s.
- Results were 16/16 exact success, with 15 terminal p050 and one p0625;
  total syndrome disclosure was 2080 bits.
- No file was written and no candidate was selected. This is backend
  feasibility for one slice only, not full-sweep FER or promotion evidence.
- The main thread may now specify the full sacrificed-development sweep and
  immutable verifier-bound artifact contract. Execution remains unauthorized
  until those tasks are frozen.

## Binary LDPC Long-Frame v3 Phase 3B Tooling (2026-07-26)

- Terra low implemented the frozen runner, read-only verifier, and focused
  tests in exactly three additive files. No production sweep was run.
- Runner lifecycle is prepare then execute, both no-overwrite. The frozen
  production grid is 3840 outcomes and 30 n/plane candidate selections.
- Exactly six artifacts are required, with canonical JSON/CSV, explicit hash
  DAG, code/backend binding, exception/cap finalization, and no resume after an
  external-kill partial directory.
- Verifier reconstructs data provenance and candidate selections but explicitly
  does not rerun decoding; exit 0 is artifact integrity, not qualification.
- Main-thread verification: Phase3B 3 passed, all long-v3 12 passed, v2
  regression 7 passed/1 skipped, compilation and frozen-directory checks
  passed.
- Next create one fresh production plan at an additive output path, inspect its
  bytes/hash/code bindings, then separately authorize its single execution.

## Binary LDPC Long-Frame v3 Phase 3C Development Evidence (2026-07-26)

- Frozen root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.
- Plan SHA256 file `6e186b48...`; plan content hash `0a4a4b0b...`;
  candidate manifest file `1cafe56e...`; outcomes `2c20f7a...`;
  selections `30747be6...`; run manifest `3f17c3b4...`; report
  `cba70bc4...`.
- Execute ran once: exit 0, stderr empty, 28.9 s wall, 3840 outcomes and
  30 selections. Strict read-only verifier ran once: exit 0, 11.2 s,
  `decoder_reexecution=false`.
- All candidate outcomes were sacrificed-development exact successes.
  Selected per-plane means show n256 lowest disclosed syndrome fraction among
  the tested lengths.
- Critical limitation: each plane currently stops when development code reads
  Alice truth. That is a development oracle, not a deployable signal. Do not
  advance these terminal leakage values or 100% development success into a
  qualification claim.
- Next freeze a ten-plane frame-level global-round contract with one
  frame-wide Toeplitz tag; recompute development leakage before selecting a
  qualification length/policy.

## Binary LDPC Long-Frame v3 Phase 4 Frame Aggregation (2026-07-26)

- Accepted aggregator combines ten selected planes into 96 q=1024
  sacrificed-development frames with one modeled 64-bit frame-wide tag and
  slowest-plane global stopping.
- Main-thread tests: Phase4 4/4, all long-v3 16/16, v2 regression
  7 passed/1 skipped.
- All lengths achieved 16/16 per stratum at frame level. Mean disclosure
  fractions were n256 .5640625/.68125, n512 .590625/.7546875, and n1024
  .6625/.8421875 for p001/p002.
- Frozen development choice is n=256, tuple
  `[-16,-32,.68125,.62265625,256]`, aggregation SHA256 `029e33c4...`.
- This selection is development-only. The tag was modeled, not executed.
  Next implement a formal n256 ten-plane method with locked Toeplitz seed/tag,
  transcript and fail-closed statuses before any fresh qualification plan.

## Binary LDPC Long-Frame v3 Phase 5 Formal Method (2026-07-26)

- `comparison_bench/src/comparison_bench/formal_ir/ldpc_v3.py` now implements
  the independent
  `ldpc_formal_v3` method for q=1024 and 256-symbol frames.
- It uses the frozen ten candidate IDs, pinned BP+OSD-0 parameters, a
  self-hashed sacrificed per-plane calibration, four synchronous nested
  syndrome prefixes, and one 64-bit frame-wide locked Toeplitz tag.
- The tag is disclosed once and used only after each complete global round.
  It is absent from decoder inputs; exact Alice truth is not a stopping signal.
- Strict v3 outcome/transcript validation reconstructs terminal-round,
  syndrome/tag/seed disclosure, epsilon, event ordering, backend and binding
  relationships. Caps and malformed calibration/codebook/decoder results fail
  closed.
- Main-thread verification: Phase 5 6 passed, long-v3 regression 13 passed,
  v2 regression 7 passed/1 skipped; compile/diff/frozen-directory checks
  passed.
- No formal runner, immutable confirmation package, strict package verifier,
  qualification, promotion, or comparison claim exists. Next freeze Phase 6
  in OpenSpec; do not execute confirmation before that review.

## Binary LDPC v3 Phase 6 Synthetic Result (2026-07-26)

- Phase 6A read-only TTBIN bridge is accepted and works on the real 20 dB
  main/chunk plus bw100/120/180/200 q=1024 sidecars. It binds 160 selected
  frames and derives calibration `604aa77d...` only from 64 bw100 frames.
- Phase 6B immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`.
- Audited plan content SHA256 `651b7df6...`; plan file SHA256 `a34b7cf0...`.
  Execute ran once in 11.4 s. Strict verifier ran once and accepted 64 rows,
  source/calibration/code/transcript/DAG/gates, without decoder reexecution.
- Calibrated: 3/32 verified; stress_125: 1/32 verified. Remaining 60 rows are
  `verify_failed`; forbidden failure count is zero. The method is
  `non_promoted`.
- Phase 6C real runner/lock/output were not created and remain forbidden by
  the hard gate. Confirmation outcomes cannot be used to tune a retry.
- Next binary work, if desired, requires a new improvement OpenSpec and fresh
  confirmation. Likely scientific target is the low-significance Gray planes,
  especially plane 9 with calibration p_hat about .123, not packaging.

## Nonbinary LDPC N0 Implemented (2026-07-26)

- Active change:
  `openspec/changes/implement-formal-nonbinary-ldpc/`.
- Terra low implemented the frozen Phase-1 slice; the main thread retained
  planning, fail-closed review, scientific acceptance, and final verification.
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py` adds
  deterministic polynomial-basis GF(2^m) arithmetic for q=2,4,...,1024,
  primitive-polynomial/backend/basis/symbol metadata, canonical field IDs,
  complete nonzero-cycle validation, inverses, and a read-only preflight.
- Unsupported/non-integral q is `unsupported_domain`; field-ID or arithmetic
  mismatch is `backend_unavailable`. Non-integral and boolean field symbols
  are rejected. There is no external backend, decoder, or lower-q fallback.
- `qldpc_reference`, its dispatch/status semantics, frozen Polar areas, and
  existing outputs are unchanged. No dependency was installed and no
  experiment or qualification runner was executed.
- Verification:
  `python -m pytest comparison_bench/tests/test_nonbinary_field.py comparison_bench/tests/test_qldpc_reference.py -q -p no:cacheprovider`
  passed 15/15; the selected formal/qLDPC regression passed 22/22; `py_compile`
  and targeted `git diff --check` passed.
- Evidence boundary: N0 proves only deterministic field-backend feasibility.
  It is not soft-decoder feasibility, qualification, promotion, or comparison
  evidence.
- Next N1 backlog: freeze deterministic rate-compatible QC/protograph-style
  q-ary codebooks, rank over GF(q), canonical bytes, and manifest hashes.
  After N1 review, N2 must freeze a bounded soft-decoder interface plus exact
  syndrome-bit, verification-tag, public-control, and Toeplitz mapping
  accounting. Do not install a decoder dependency or run synthetic/real data
  before those tasks are explicitly frozen.

## Nonbinary LDPC N1 Implemented (2026-07-26)

- Terra low implemented the frozen N1 tasks; the main thread retained the
  matrix-family decision, canonicalization contract, scientific evidence
  boundary, review, and acceptance.
- `formal_ir/nonbinary_codebook.py` adds a pure in-memory n=64 family with one
  deterministic 32x64 mother matrix and exact 16/24/32 ordered row prefixes.
  The information half uses three distinct SHA256-derived cyclic shifts and
  explicit nonzero GF(q) coefficients; the parity half is identity.
- Rank is calculated by Gaussian elimination over the pinned N0 GF(q)
  arithmetic. A regression matrix that has real rank 2 but GF(4) rank 1 guards
  against accidental integer/real/GF(2) rank substitution.
- Canonical `NBLDPC1` bytes contain full field metadata, dimensions, topology,
  coefficients, construction seed, coefficient encoding, and row ordering.
  Golden q=2/q=1024 codebook and manifest SHA256 values detect drift.
- The verifier reconstructs matrices, bytes, ranks, prefixes, codebook IDs,
  and the top-level manifest ID. Tampered field/coefficient/rank/prefix/hash
  evidence returns `codebook_invalid`; unsupported q returns
  `unsupported_domain`. It does not repair or fall back.
- Verification: N0+N1+existing qLDPC focused tests passed 22/22; the selected
  formal/nonbinary/qLDPC regression passed 29/29; `py_compile` and targeted
  `git diff --check` passed. Protected baseline/output/reference diffs are
  empty.
- Evidence boundary: N1 proves deterministic structural rank and hashing only.
  It is not decoder feasibility, distance/FER performance, qualification,
  promotion, or comparison evidence.
- Next: freeze N2 before coding. N2 must define the bounded soft-decoder
  interface, channel likelihoods from sacrificed data only, Alice-syndrome/
  Bob-local-coset semantics, MSB-first Toeplitz mapping, and exact syndrome,
  verification-tag, and public-control accounting. Do not select/install a
  decoder dependency or run experiments before this contract is reviewed.

## Nonbinary LDPC N2 Implemented (2026-07-26)

- Terra low implemented the frozen N2 slice; the main thread retained the
  algorithm/evidence decision, truth-isolation and accounting requirements,
  numerical review, and acceptance.
- `formal_ir/nonbinary_qspa.py` adds a pure full-message probability-domain
  FFT-QSPA feasibility decoder. It uses polynomial-basis XOR-order
  Walsh-Hadamard convolution and exact N0 GF(q) coefficient permutations.
  q=4 transform and non-unit-coefficient/nonzero-syndrome check messages match
  brute-force convolution.
- The decoder accepts only Bob symbols, Alice's public syndrome, a verified N1
  manifest/matrix family, check count, frozen q-ary-symmetric p, and bounded
  iterations. Its public signature contains no Alice truth or callback.
- `syndrome_consistent` means only that the decoded vector reproduces the
  disclosed syndrome. Formal verification is a separate locked Toeplitz call;
  the decoder has no `verified_success` path.
- q=1024 executes for the bounded n=64/16-check/one-iteration no-error case
  below the declared 16-MiB dense-message cap. Tampered manifests, resource
  excess, invalid booleans, and numerical failures fail closed without a
  decoder/backend/lower-q fallback.
- Symbols convert to fixed-width MSB-first bits including leading zeros.
  Syndrome disclosure is exactly checks*log2(q); an invoked tag adds its exact
  bit length; public-control bits remain separate.
- Verification: N0-N2 plus existing qLDPC tests passed 35/35; selected formal
  verification/Cascade/LDPC regressions passed 17 with 2 skipped;
  `py_compile` and targeted `git diff --check` passed. Frozen baseline,
  reference/pipeline, output, and dependency diffs are empty.
- Evidence boundary: the q=4 fixed correction and q=1024 no-error unit cases
  are engineering checks only. They do not establish general correction, FER,
  performance, calibration, qualification, promotion, real-data behavior,
  output evidence, production readiness, or comparison eligibility.
- Next is N3 planning, not execution. Pre-register sacrificed development and
  immutable confirmation data, exact domain and one global policy, metrics and
  statistical gates, resource/stop rules, additive artifacts/statuses,
  invalid-run preservation, and a strict read-only verifier before generating
  or running any qualification data.

## Nonbinary LDPC v2 Synthetic Stop (2026-07-26)

- Phase 1/2 engineering is accepted: focused tests passed 21/21; the joint
  N0-N3/v2/formal regression passed 86 with 8 skipped.
- The sole official package is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`.
  Its reviewed plan SHA256 is
  `8b072d26294047f842205662afd188b0816de3edddf56ced3c03a87b26549cc8`;
  it binds 112 frames, 24 policies, 1216 unique Toeplitz seeds, and zero prior
  overlap. Plan-only strict verification passed.
- The sole execution exited 0 in 2324.3 s. Full strict replay completed in
  2326.3 s and returned `verified=True`,
  `run_status=non_promoted_development`, `promoted=False`. Scoped provenance
  passed; dirty whole-worktree status was diagnostic only.
- Development selected
  `nbldpc_formal_v2_qc48_damped_l050_tempered_t080`, margin 8, max_iter 10,
  with 32 checks at p=.20 and 40 at p=.30; policy SHA256 is
  `c5032e94ecf1c138c3ddfbe46a54739cf4f048a147fa2fbf1af4a39afdcd3d36`.
  It achieved 0/24 verified successes at p=.20 (24 `verify_failed`) and 5/24
  at p=.30 (18 `verify_failed`, 1 `decode_failed`), below the required 22/24
  in each stratum.
- Confirmation was not generated or executed. This is development
  non-readiness, not confirmation failure, FER, or real-data evidence. Do not
  rerun, tune, create N4, read sidecars, or process `.ttbin`.
- Frozen artifact SHA256 values: outcomes
  `43f995373769c1492422eb936429f85ef21207fe114b9186c867052f8e5c36b0`,
  transcript
  `d62535dd05d6810e730abf457f452b38d6fa74f6b9134586062d60a42c0e61d5`,
  run manifest
  `091b5941994bee2a28d335bb611c059905f95f18e620a27b8b40d054c5042aca`,
  report
  `b3084eae3cee0aaadf9c00ed1615374d61641726f222a12f93f2f221c3ae94c3`,
  policy
  `4d4cb3891375dc1e58e12f43e8d9850a2d2e54c33b72fb83ae8504ee9a98f842`,
  candidate
  `b525e1b359708fa2babdf452b3d91c317a89c67799ae70a54705060388ee0383`,
  and codebook
  `c48c133dd180c789a8003fecf1c36ef4216aaebcc4e5a58e20441e019f73351c`.

## Binary LDPC Adjacent-Channel v4 Development Stop (2026-07-27)

- Active OpenSpec:
  `openspec/changes/binary-ldpc-adjacent-channel-v4/`. Phase 1-5 engineering,
  package tooling, read-only verifiers, transcript source-payload replay, and
  regressions are implemented. Main-thread focused acceptance passed:
  foundation/formal 15 tests, development package 8, synthetic package 3,
  and real package 4.
- Cross-version regression passed 119 tests with 10 skipped:
  core v1-v3/nonbinary algorithms 76/10 skipped, nonbinary qualification
  31/31, and formal-real 12/12. `py_compile`, scoped `git diff --check`, and
  frozen `src/`, `experiments/`, `tools/`, and `results/` checks passed.
- The sole production development package is immutable:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development/`.
  Prepare and execute each ran once. Plan content SHA256 is
  `af644e2f4a3dab596f34350b18ecfb1df56cb46b93670cb16e89f3ca1ae67c5e`;
  plan file SHA256 is
  `493e98c6b6492f9216204be63f4bec10d0c6aa817e4302dfc5de7ee3c0401ac7`.
- Production command sequence, from the repository root, was:

  ```powershell
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_development --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development --mode prepare --v3-plan comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_development --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development --mode execute
  python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_development --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development
  ```

  These commands are provenance and recovery documentation only. Do not run
  prepare or execute against this existing directory; both are intentionally
  no-overwrite. Reverification is read-only but takes about 16 minutes on the
  recorded machine.
- The plan binds q=1024, 256-symbol frames, Gray mapping, the exact 64-frame
  bw100 sacrificed calibration, adjacent nominal/stress channels, 40 anchored
  column-weight-three candidates, 40,960 plane outcomes, 1,024 frame
  denominators, `ldpc==2.4.1`, and a 495/512 readiness floor per stratum.
- Execution completed all 40,960 rows in about 29 seconds. The first verifier
  process was killed only by the caller's 300-second outer timeout and wrote
  nothing; the resumed deterministic read-only invocation completed with
  `status=verified`, `run_status=completed`,
  `decoder_reexecution=false`, and `ready_for_synthetic_prepare=false`.
- Both strata retained exactly 512 denominators and zero frame successes.
  Each has 5,120 selected-plane `development_decoder_error` outcomes and
  5,120 forbidden failures. Selection therefore ties to candidate 0 on every
  plane with `[0,0,0]`; this is not code-performance evidence.
- Root cause is confirmed as an implementation/backend-boundary defect, not an
  FER result: a no-decode constructor diagnostic gives
  `TypeError: Argument 'error_channel' has incorrect type (expected list, got
  numpy.ndarray)` for the development path, while `.tolist()` constructs
  successfully. `ldpc_v4.py` already performs this conversion; the frozen
  `ldpc_v4_development.py` package path does not.
- Frozen artifact file SHA256 values:
  outcomes `4c59e156b3a90a1554b117a5371f5c6ce6f50a9d9bf3258bbe236a76dbbca8b9`,
  selection `0426af5b2a158f988288f19261944926c7f8b2d2a7d8cfc9c68c178f497eb131`,
  run manifest `b7735fea3a2f09e3947f01fa00d024b4b6d846e7d4daa28403fe5d85de64de5f`,
  and report `55c56b6764eca9511aab8e30f491ffcc664872faa453cc33de2ab933dcaa4dd6`.
- Frozen stop rule applied: no v4 production synthetic or real directory,
  plan, lock, execution, or result was created. Do not edit the scoped v4
  source files, retune, or rerun this package; doing so would invalidate its
  source-hash DAG.
- Next action requires a new main-thread OpenSpec decision. If continuation is
  authorized, treat it as a versioned implementation-correction lane that
  converts development `error_channel` to the pinned backend's exact list
  type, adds a production-constructor regression, and creates new evidence.
  Do not describe that future run as a retry of this immutable v4 package, and
  do not proceed to comparison or rate adaptation.

## Binary LDPC v4 Backend Correction Development Ready (2026-07-27)

- OpenSpec `binary-ldpc-v4-backend-correction-v1` added a versioned evaluator,
  runner, verifier, and focused tests without changing any source file bound by
  the failed v1 package. The only production semantic correction is converting
  the existing Bob-conditioned float64 error-channel vector to a Python list
  at the pinned `ldpc==2.4.1` constructor boundary.
- Main-thread acceptance passed 5 focused correction tests. The selected
  historical v1-v4/formal-real/nonbinary regression has 175 passed and
  11 skipped; combined unique acceptance for this change is 180 passed and
  11 skipped. The first broad regression invocation had 24 fixture-setup ACL
  errors and no assertion failure; those 24 cases were rerun with an explicit
  pytest basetemp as part of a 31/31 passing nonbinary qualification subset.
- Compilation, scoped `git diff --check`, frozen `src/`, `experiments/`,
  `tools/`, and `results/` checks passed. All seven historical v4 scoped source
  hashes and the three predecessor-bound artifact hashes remained exact.
- The sole corrected production package is immutable:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development/`.
  Prepare and execute ran once; the read-only verifier ran once and returned
  `status=verified`, `run_status=completed`,
  `decoder_reexecution=false`, and `ready_for_synthetic_prepare=true`.
- Exact production commands from the repository root were:

  ```powershell
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_development_v2 --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development --mode prepare --v3-plan comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json --predecessor-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_development_v2 --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development --mode execute
  python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_development_v2 --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development
  ```

  These are provenance commands only. Do not rerun prepare or execute against
  the existing no-overwrite directory.
- The plan content SHA256 is
  `1e208832ac421e69c0488d33e39953755ba487c25f9bf9db43bdda79cc53daaf`;
  its file SHA256 is
  `0b690fe2e4ac56cf1d742368877b07f72ad3cc84dc0c7de894caf1c3a9919255`.
  It binds the unchanged 40 candidates, 40,960 plane outcomes, 1,024 frame
  denominators, 495/512 per-stratum gate, original TTBIN lock, and failed-v1
  predecessor plan/outcome/report hashes.
- Development results passed the frozen screen:
  `adjacent_nominal` 510/512 and `adjacent_stress_125` 511/512, both with zero
  forbidden failures. Selected candidates by plane are
  `[0,0,0,0,0,0,2,0,2,2]`. Selected-plane failures are two nominal and one
  stress `development_decode_failed`; no selected backend, source, internal,
  accounting, or unclassified failure occurred.
- Artifact file SHA256 values: outcomes
  `c48d00ba68fe37e2104794348734d6c22a5f295d3e90826362f9e094124d3018`,
  selection
  `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd`,
  run manifest
  `7ff6cb96ef25be36c92d54c10e74a75e757a07a11227c0444b4193ff5dd5b713`,
  report
  `31f51cec0625fe7be0f36a4b746de37e1a512a7bc63c182501baaedbe5b6bfa5`,
  candidate manifest
  `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500`,
  and channel model
  `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c`.
- This is sacrificed-development readiness only, not synthetic qualification,
  real `.ttbin` performance, FER for an acquisition population, or comparison
  eligibility. No corrected-v4 synthetic or real production directory was
  created. The next action is a separate main-thread review of a fresh
  synthetic plan using the already implemented conditional v4 tooling.

## Binary LDPC v4 Corrected Synthetic Promoted; Real Data Pending (2026-07-28)

- Active OpenSpec:
  `openspec/changes/binary-ldpc-v4-corrected-qualification-v2/`. The previously
  uninstantiated conditional synthetic/real tooling now binds only the
  corrected v2 development package and emits v2 package identities. Generator
  bytes, formal method, matrices, channel, selection, caps, statuses,
  transcript/accounting, 128-frame denominators, and 126/128 gates are
  unchanged.
- Main-thread acceptance passed 10 corrected synthetic/real focused tests,
  71 binary-core tests with 3 skipped, 17 formal/v3 package tests with
  8 skipped, 12 formal-real tests, and 73 nonbinary tests: 183 passed and
  11 skipped in total. Compilation, whitespace/diff checks, frozen-directory
  checks, both development source DAGs, and all seven corrected-development
  artifact hashes passed.
- The immutable synthetic package is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`.
  One initial prepare invocation ended at an external 120-second caller
  timeout before root generation or directory creation. The sole successful
  prepare then created one reviewed plan; execute ran once; the read-only
  verifier ran once and returned `status=verified`, `run_status=completed`,
  `outcomes=256`, `promoted=true`, and `decoder_reexecution=false`.
- Production commands from the repository root were:

  ```powershell
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic --mode prepare --development-dir comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development
  python -m comparison_bench.src.comparison_bench.cli.run_ldpc_v4_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic --mode execute
  python -m comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic
  ```

  Do not rerun prepare, execute, or use this confirmation for tuning.
- The plan content SHA256 is
  `02a198ea4d03ae4d7dad7db6e2b4099e85f5b75c0d8acad34e8449d67cb769fb`;
  plan file SHA256 is
  `6a8c8c11afe7e13061c876a8955592f78911fc12883558fa9ccb3546391874cc`.
  It binds eight unique CSPRNG roots, 256 unique Toeplitz seeds, zero
  root/seed overlap with v3 or development, 256 unique execution entries, the
  exact corrected development package, and the 126/128 gates.
- Synthetic results: adjacent nominal 127/128 and adjacent stress 126/128.
  The remaining three outcomes are retained `verify_failed`; forbidden
  failure count is zero in both strata.
- Artifact file SHA256 values: outcomes
  `3dd169aa692aba94232abf5018bbaee819645ac210a79c466b1702e0500d6c93`,
  transcript
  `c2518fd89ad9a9ca3f884e74419e5801b42c956d3f027d90d9044167b7782b0f`,
  run manifest
  `3a142ff8d6d37c665ac8e0a1a8541fe9b36133ea10e75e3b55cbdc044eb49fa6`,
  report
  `57268f73d4fa7dcbce01c2e63066af6d177502b415aa076312dd3a9c7a3f804a`,
  selection
  `5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd`,
  channel
  `83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c`,
  and codebook
  `786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500`.
- Real prepare is intentionally blocked before directory creation by source
  capacity. Each of bw120/bw180/bw200 has 117 complete frames, 32 v3-reserved,
  and therefore only 85 eligible versus 128 required: a deficit of 43 per
  stratum. Do not reuse reserved frames or lower the gate.
- Required next input: preferably at least 64 new complete paired
  256-symbol frames for each of bw120, bw180, and bw200, from the same 20 dB,
  q=1024, Gray/nearest-pairing processing domain. Preferred delivery is three
  traceable sidecar directories containing `a_eff.npy`, `b_eff.npy`, and
  `sidecar_meta.json`, tied by metadata and SHA256 to a new `.ttbin` capture.
  Raw main/chunk `.ttbin` may be supplied instead, but requires a new
  planner-frozen materialization/source-extension step before any decoding.

## Binary LDPC v4 Real-Source Intake Ready (2026-07-28)

- A full-disk read-only audit found no second independent 20 dB acquisition.
  The raw files under `TypeII_776.1nm_3s - 副本` have the same hashes as the
  registered capture: main
  `8f6848b58ecaef9d9e227c80a5c4f2c478dd62d44e5e5dd0996c7e17f8b3c320`
  and chunk
  `303aee617075579c36e232a1ded315f5332a11a2c21d527cab0c9821ee11acc1`.
  It is a copy/reprocessing source and contributes zero new denominators.
- Phase 4 now has a frozen and accepted no-overwrite source-extension intake:
  `formal_ir/ldpc_v4_real_source.py` and
  `cli/build_ldpc_v4_real_source_extension.py`. It binds distinct raw
  acquisitions, exact three-stratum sidecars, sizes/hashes/provenance,
  source-aware and payload identities, complete-frame floor counts, duplicate
  rejection, and deterministic selection without invoking the decoder.
- Real prepare now requires `--source-extension-manifest`; its lock embeds the
  exact external manifest and file record. Execute and the read-only verifier
  reconstruct all source files and selection. The builder CLI is included in
  the real plan scoped source hash DAG.
- Main-thread acceptance passed source focused 3/3, real focused 5/5, v3
  bridge/source 7/7, and backend/development/formal-real 25/25, plus compile,
  diff, historical source-hash, and no-real-output checks. An earlier
  8-failure regression invocation used an invalid repository-internal temp
  root; the identical suite passed 25/25 under the required external temp
  root.
- Operational intake instructions are frozen in
  `openspec/changes/binary-ldpc-v4-corrected-qualification-v2/real-data-intake.md`.
  No source-extension production manifest or real qualification directory
  exists yet. The next required event is delivery of a genuinely new 20 dB
  main/chunk `.ttbin` pair and q=1024 bw120/bw180/bw200 sidecars, preferably
  with at least 64 complete frames per stratum.

## Binary LDPC v4 16 dB Transfer Non-Promoted (2026-07-29)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260729_v1_binary_ldpc_v4_16db_transfer/`.
- Prepare, main-thread review, execute, and read-only verify each completed
  exactly once. The verifier returned `status=verified`,
  `run_status=completed`, `outcomes=384`, `promoted=false`,
  `decoder_reexecution=false`, and changed none of the nine files.
- Results: bw120 125/128 with three retained `verify_failed`; bw180 128/128;
  bw200 128/128; forbidden failure count zero in every layer. The frozen gate
  was 126/128 per layer, so this is `non_promoted_transfer`.
- Plan content SHA256:
  `ddbf41983d866ce5d320404323ff319b64a867f8f8c32185a890ab7baf97b2da`;
  source-lock content SHA256:
  `5c654377751cea776a203269b8213959313aa9a0be738935816d36b52181ea87`.
- Do not tune, delete, overwrite, or rerun this package. It does not promote
  either the original 20 dB route or the 16 dB domain.
- Successor OpenSpec:
  `openspec/changes/binary-ldpc-v4-10db-transfer-qualification-v1/`.
  It freezes an unchanged-method transfer test on an independent 10 dB
  `.ttbin` acquisition with more than 1,100 complete frames per target layer.
  Terra is implementation/test operator only; production remains main-thread
  controlled.

## Binary LDPC v4 10 dB v1 Prepare Rejected (2026-07-29)

- `20260729_v1_binary_ldpc_v4_10db_transfer` contains only a prepared plan and
  source lock; no decoder ran and no 10 dB outcome was observed.
- Main review rejected the plan because post-write validation rediscovered
  the current plan as prior real evidence and falsely collided with its own
  roots. Preserve it as immutable `invalid_pre_execute`; never execute it.
- File SHA256: plan
  `dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c`;
  lock
  `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf`.
- The frozen v2 correction is
  `prepare-correction-v2.md`: exclude only the current v2 plan during
  validation, while binding and isolating all roots/seeds from this failed v1.

## Binary LDPC v4 10 dB v2 Non-Promoted (2026-07-29)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260729_v2_binary_ldpc_v4_10db_transfer/`.
- Its sole prepare passed post-write strict validation; execute and read-only
  verify each ran exactly once. Verification returned 384 outcomes,
  `run_status=completed`, `promoted=false`, and
  `decoder_reexecution=false`, changing none of nine files.
- Results: bw120 125/128, bw180 127/128, bw200 128/128; four retained
  `verify_failed`, zero forbidden failures. The 126/128 all-layer gate failed.
- Plan content SHA256:
  `c6f3592ac24fd32ac136d16f06fd88157757216a81c40643e86d0ba3882af2f6`;
  plan file SHA256:
  `ff7d5f987a3eec19d30a92c5781d77ba612b7305530f38744b6bd9a9872c63ed`.
  Do not tune or rerun.
- The active successor is
  `openspec/changes/binary-ldpc-v5-incremental-redundancy/`. It pre-registers
  512 unused development and 128 sealed confirmation frames per layer,
  stronger local OSD and a leakage-accounted incremental-syndrome fallback.
  Do not try successively easier loss domains.

## Nonbinary LDPC v3 Final Outcome (2026-07-30)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic/`.
  Its plan was created once, executed once, and strictly replay-verified once.
- The selected policy was `nbldpc_formal_v3_layered_l075`, margin 8, with
  32 checks at p=.20 and 40 checks at p=.30. Development passed readiness at
  23/24 and 24/24, so confirmation was materialized only after that gate.
- Confirmation achieved 32/32 at p=.20 and 30/32 at p=.30, with denominators
  32/32 and zero prohibited failures. The frozen gate was 31/32 in both
  strata, so strict verification returned `verified=True`,
  `run_status=completed`, `promoted=False`.
- Plan SHA256:
  `0f35b8679166599efb294caee21822156ba971bec6271875cf55516523cfdee1`;
  selected-policy SHA256:
  `6193f92af05c1d3a5145cbe31c95a4d20f1eaf5a09970936613c326cc1c59a28`.
- Preserve this package without rerun, deletion, overwrite, or confirmation
  tuning. It is synthetic non-promotion evidence only. Do not build N4,
  access sidecars, or process `.ttbin`; those require promoted confirmation
  and a separately approved OpenSpec change.

## Nonbinary LDPC v4 IR Final Outcome (2026-07-31)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
  Plan, execute, and strict read-only replay each ran exactly once; execute
  exited 0 in 3,384 s and verify exited 0 in 3,524 s.
- The verifier returned `verified=True`, `run_status=completed`,
  `promoted=False`. Development selected `nbldpc_v4_ir_warm`, with 64/64 at
  p=.20 and 63/64 at p=.30.
- Sealed confirmation achieved 128/128 at p=.20 and 120/128 at p=.30. The
  eight p=.30 misses were retained `decode_failed`; prohibited failures were
  zero. The frozen gate required 128/128 in both strata.
- Preserve the eight-file package without rerun, overwrite, deletion, or
  confirmation-driven tuning. This change terminates at synthetic
  non-promotion. N4, sidecar access, and real `.ttbin` processing remain
  forbidden.
- A future successor must be a new OpenSpec change with fresh development and
  confirmation data. The present evidence suggests that one 80-bit extension
  is insufficient in the p=.30 tail; do not infer authorization for a second
  extension, a changed codebook, or a new decoder from this diagnosis.

## Nonbinary LDPC v5 Route C Final Outcome (2026-08-01)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5c_nbldpc_decoder_synthetic/`.
  Plan, execute, and strict read-only replay each ran exactly once; the
  replay returned `verified=True`, `run_status=completed`, `promoted=False`
  and changed no worktree entries.
- The plan binds NBLDPC5B (codebook_sha256 matches the live v5b canonical),
  128 frames (64 per stratum), 640 development Toeplitz seeds, policies
  `nbldpc_v5c_sched` (damped FFT-QSPA lambda 0.5/0.75/0.9 per 4-iteration
  quartile) and `nbldpc_v5c_ems` (LLR min-sum nm=64 alpha=0.8), roots
  202607800000-202607830000.
- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained tail miss);
  prohibited failures zero. `promoted=False`, so the package is immutable
  non-promotion evidence. Do not rerun, tune, overwrite, or delete it.
- Route D is next: `20260731_v5d_nbldpc_post_synthetic`, roots
  202607840000-202607870000 (list stage L=2 + one ADMM run, task 1.6),
  after Route D implementation and acceptance tasks 7.1-7.2.

## Nonbinary LDPC v5 Route D Final Outcome; v5 Change Terminated (2026-08-02)

- Immutable package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5d_nbldpc_post_synthetic/`.
  Plan, execute, and strict read-only replay each ran exactly once at HEAD
  192f455; the replay returned `verified=True`, `run_status=completed`,
  `promoted=False` and changed no worktree entries.
- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained
  confirmation-frame `decode_failed`); prohibited failures zero.
- Route D = list (L=2 least-certain x top-8 symbols = 64 candidates, one
  round, syndrome filter) then one bounded ADMM (rho=1.0, <=50 iterations,
  deterministic init) over the v5c decoders, with no additional syndrome
  disclosure. Implementation corrections (x-update prior sign; per-bit
  parity-relaxation z-projection) were approved and recorded; q=4
  brute-force golden tests pass 100%.
- All four v5 routes (A/B/C/D) are non-promoted with the same p=.30 tail
  pattern (127/128); the v5 multistage change terminates with four
  immutable non-promoted packages. N4, sidecars, `.ttbin`, real data, and
  comparison claims remain locked. A successor requires a new OpenSpec
  change with fresh development and confirmation data.
- Evidence: openspec/changes/formal-nonbinary-ldpc-v5-multistage-ir/evidence/
  v5d_acceptance_d1_d2.json and v5d_acceptance_c3_c4.json; decision-log
  entry 2026-08-02.

## Nonbinary V8 Handoff — V8-60 Audit-Correction Close-out (2026-08-04)

- Change: `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/`.
- Status: IMPLEMENTED, then corrected by V8-60 (non-tuning formula correction
  from an independent audit), corrective reference run executed once, and
  INDEPENDENTLY REVIEWED ACCEPTED (reviewer-go, read-only, 2026-08-04, HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`). V8-A01..V8-A11 pass; V8-A12
  resolved pass by the V8-60 review (operator did not self-accept).
- Done: additive `nonbinary_v8_error_domain.py` (error-domain contract
  d = H*(x+y), x_hat = y + e_hat, pure field-tables-only helpers),
  `nonbinary_v8_reference.py` (independent probability-domain oracle: pairwise
  XOR convolution + sparse support enumeration + brute-force tiny-code
  coset/MAP, GF2mField-only import boundary enforced), `nonbinary_v8_mcde.py`
  (full-vector QSC MC-DE: edge-perspective degrees with tested node/edge
  conversion, exact sampled degrees, fresh channel message per variable
  update, direct convolution without FWHT, base-q mean entropy convergence,
  seeded deterministic, fail-closed), plus 3 tests and 7 evidence files.
  Tiers (`pytest -q -p no:cacheprovider`, fresh workspace
  `nbldpc_v8_reference_9c3f51e2a74b48d9b6c0a5f8e1d23a4b` root): T0 11/0,
  T1 31/0, T2 3/0 (read-only reproduction-trace + source-manifest +
  no-production-runner verification), T3 179/0 (frozen 16-file
  v5+v6+v7-R1A/R1B/R2 regression subset); reviewer re-ran T0/T1/T2: identical.
- Reproduction (one frozen run, no rerun/tuning): Muller et al., Quantum Inf
  Process 23, 195 (2024), arXiv:2307.02225v2, Table 1 row "0.75" (q=4,
  rate 0.75, DET 0.069, EEff 1.053); threshold_proxy 0.062421875, delta
  0.006578 <= 0.015 -> PASS. Provenance:
  `evidence/v8_literature_provenance.json`,
  `evidence/v8_muller2024_table1_extract.txt` (SHA256
  `d343f0204e87994e64efd32531bc12490fb4e7125cd90b52cfaf2397279b57bd`);
  full trace: `evidence/v8_reproduction_trace.json`.
- Evidence: `v8_engineering_acceptance.json` (schema v8_engineering_v1,
  source manifest with SHA256 of the 6 additive files),
  `v8_source_manifest.json` (pre-test manifest re-verified read-only),
  `v8_v7_interpretation_audit.md` (R1B = out-of-contract extra-observation
  diagnostic; R2 = unvalidated scalar-DE surrogate result; V7 T0-T3
  engineering PASS distinct from canary failures), and `v8_v9_recommendation.md`
  (V9 lead: paper-faithful syndrome reconciliation with a reproduced ensemble
  and blind puncturing/shortening, fresh roots, separate OpenSpec change;
  NOT implemented).
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real/N4/comparison execution; frozen
  `src/`/`experiments/`/`tools/`/`results/` and all V1-V7 files unchanged
  (git status/diff empty); nothing staged.
- Remaining: nothing for V8 except the V8-60.11 memory-agent close-out
  (AGENT_PROJECT_MEMORY.md section 39 pending). The only successor is a
  separate future V9 OpenSpec proposal — NOT implemented. V8 is
  engineering/reference-only and authorizes no
  FER/readiness/qualification/promotion/comparison claim.

**V8-60 correction close-out (2026-08-04)** — non-tuning formula correction
discovered by an independent audit of the accepted V8 candidate:
- (a) `concentrated_check_distribution` fixed from the mean-matched
  `w_lo = dc_hi - dc_mean` approximation to an exact solve of
  `sum_j rho_j/j = (1-R)*sum_i lambda_i/i` over adjacent check degrees
  `{floor(dc), ceil(dc)}` (`w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`,
  `w_hi = 1 - w_lo`, `target = (1-R)*integral_lambda`, `dc = 1/target`);
  new `reconstructed_rate(lambda_edge, rho_edge)` helper; tests assert
  `|reconstructed_rate - rate| <= 1e-12` (5 configs).
- (b) Citation first author corrected to Ronny Müller (arXiv:2307.02225v2
  author list). (c) Invalid tolerance arithmetic `0.005+0.003+0.0025=0.015`
  replaced by 0.0005 + 0.00125 + 0.005 + 0.005 = 0.01175 <= 0.012; frozen
  tolerance 0.012.
- Corrective run (once, frozen before run): q=4 R=0.75 Table 1 row 0.75, rho
  {24: 0.6623423944, 25: 0.3376576056} (dc_mean 24.3285893 unchanged),
  n_samples 100000, max_iter 150 (paper MC-DE budget), seed 2026080418,
  p [0.01,0.12] step 0.0025, entropy < 0.01 base-q x20: threshold_proxy
  0.062421875, delta 0.006578125 <= 0.012 -> PASS
  (`evidence/v8_reproduction_trace_corrected.json`). No rerun, no tuning.
- History: `v8_reproduction_trace.json` byte-identical (SHA256
  `dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3`) +
  `v8_reproduction_trace_precorrection_annotation.json`;
  `v8_engineering_acceptance.json` not rewritten (A12=blocked resolved by
  `v8_acceptance_closeout_addendum.json`); provenance/extract/audit/
  recommendation files unchanged; q=4 golden re-recorded ({4: 1/6, 5: 5/6},
  recording not tuning), q=8 golden byte-identical (regular {6:1.0}), old-R2
  tamper modes still differ.
- Tiers (V8-60.8, no T3): compile exit 0; T0 17/0, T1 32/0, T2 4/0
  (reproduction-trace + source-manifest + no-production-runner +
  precorrection-preservation, all read-only); reviewer re-ran T1 32/0 and
  T2 4/0: identical.
- Evidence (new in V8-60): `v8_reproduction_trace_corrected.json`,
  `v8_reproduction_trace_precorrection_annotation.json`,
  `v8_60_correction_evidence.json` (only `nonbinary_v8_mcde.py` and
  `test_nonbinary_v8_mcde.py` changed: hashes
  `2c84a5ee76d09f4d6cea537289ff82d88ab19abd31d1a41951a7d24acdd66543` /
  `a508a4228ee06114424db2242b4db784bfa1b9cabcbae54f4cd7172ed988a81f`),
  `v8_independent_review_acceptance.json`, `v8_acceptance_closeout_addendum.json`;
  `v8_source_manifest.json` regenerated with `v8_60_delta` field (old hashes
  remain in the original acceptance).

## Nonbinary V9 Handoff — Frozen for OpenCode Execution (2026-08-04)

- Active change: `formal-nonbinary-ldpc-v9-gf1024-long-ir`; next V9-00.
- Read `proposal.md`, `design.md`, `specs/spec.md`, `tasks.md`, and
  `opencode-autonomous-packet.md` in that change before action.
- Frozen route: V9A GF(1024) multi-seed MC-DE (.22/.32 robust gates) -> V9B
  n=4096 4+4 -> V9C n=16384 4+4 -> n=32768 4+4 -> fresh 16+16 development.
- Each scientific phase is prepare/read-only review/one execute/one strict
  replay. First failed gate stops and preserves evidence; no tuning/rerun.
- V8 q=4 is method-only evidence. V9 target f=1.08 is used only where its DE
  gate passes; otherwise robust f=1.15 with `efficiency_target_not_met`.
- Hard boundary: stop after V9C development. No qualification, confirmation,
  real/N4, official comparison output, install/clone, or Git mutation.
- Independent freeze review corrections are already merged into the packet:
  robust DE gates .22/.32 and target .215/.32; one V9A reviewed/once-executed/
  replayed package; n=4096/16384/32768 use 4/16/32 disjoint constituents;
  every finite matrix has `rank(H)=m`; n=32768 canary timeout 24h and median
  <=16h; V9C fixed-rate leakage is syndrome `10*m` plus a separate 64-bit tag.
  Blind adaptation is forbidden in V9 and deferred to V10.


## 自动执行终点
V18-B1 M1 FAIL (NO_THRESHOLD)；无自动下一步，等待用户决策。
