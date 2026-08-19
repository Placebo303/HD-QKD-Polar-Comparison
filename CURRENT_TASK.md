Status: V27R OpenSpec 修订版 DRAFT 已写入（source-adaptive finite-leakage-margin），PENDING_FREEZE_REVIEW——尚未 ACCEPT、未实现、未执行任何 DE。独立 Luna freeze review 本轮仍因 subagent 基础设施故障未能交付（连续 2 轮 / 11+ 次 subagent+muse_spark 前后台尝试均失败，后台 agent 停留在 ready 未返回结果）；按严格门控，主线程**未**记录 P102 ACCEPT，V27R 不进入 Phase B。P001/P002 证据已闭合、算术已复算，freeze-review packet 见 tmp_v27r/v27r_freeze_review_packet.md。

## 2026-08-20 V27R round 2：freeze review 仍未交付（基础设施阻塞），证据/算术复算完成

- 再次尝试独立 Luna freeze review：前台 subagent×1、后台 subagent×3、muse_spark×1 全部失败
  （后台 agent 停于 ready 未返回结果）。subagent 基础设施在本环境持续不可用。
- 按严格门控：未记录 P102 ACCEPT；未开始 Phase B 实现。
- 完成 P001 证据闭合：V26 archive run_01 `readonly_verify.json` ok=true，screen 72 (0 mismatch)、
  confirm 60 (0 mismatch)、a02_f13_confirmed=30/30、gate_recomputed=pass_target_f13。
- 完成 P002 复算：每-source full-precision H 从 `channel_counts.npz`(run_04) 用 V26 adapter 复算，
  与冻结值一致（1M 0.024280547/0.776757278；1p5M 0.025199497/0.800366555；2M 0.025662049/0.806900673）。
- 复算确认：m_total 冻结表（1M 200/413/840/1693；1p5M 206/426/866/1745；2M 208/430/873/1760）、
  m1_ep（1M 6/13/25/51；1p5M 6/13/26/53；2M 6/13/27/54）、12 格实现总 f 均<1.3（1.29409–1.29974）。
- 生成 freeze-review packet：tmp_v27r/v27r_freeze_review_packet.md（含全部已验证参考数据与 doc 映射）。
- 结论：V27R OpenSpec 内容已就绪且主线程已验证；唯一未决项 = 独立 Luna freeze review（被基础设施阻塞）。
  待 subagent 基础设施恢复后需补跑独立 freeze review → ACCEPT → 再进 Phase B。

## 2026-08-19 V27R OpenSpec revision：source-adaptive 预算（写文档，未执行）

- 依据目标 Phase A，将 V27 OpenSpec 由 worst-source 单一预算改为 **source-adaptive**：
  每 source（1M/1p5M/2M）用自己 full-precision H1/H2；`m_total=floor((1.3·block_len·H_source−64)/5)`。
- 冻结预算表（block_len=1024/2048/4096/8192 → m_total）：
  1M 200/413/840/1693；1p5M 206/426/866/1745；2M 208/430/873/1760。[复算 verified]
- m1_ep=round(m_total·H1/H_total)（Python round，round-half-to-even，冻结明确规则）；
  候选 m1∈{m1_ep−2..m1_ep+2}、m2=m_total−m1，五候选均晋级；m1_ep 复算
  1M=6/13/25/51、1p5M=6/13/26/53、2M=6/13/27/54；实现总 f 均<1.3（1.29409–1.29974）。[复算 verified]
- 明确 V27 为 asymptotic true-predecessor-conditioned multistage DE（L2 条件于正确 L1，
  不模拟有限码错误传播）；单个 64-bit tag 只计入整块总泄漏，不在层间使用。
- source/delay 仅为公开 acquisition selector（选 posterior 与 syndrome 预算），非逐符号
  side information，不重复计费；`block_len` 与 `mc_samples` 为两个独立字段。
- 冻结 candidate_id=(block_len,source,m1)、去重、合法性、排序 keys：
  worst_final_entropy → mean_final_entropy → abs(offset) → m1（升序）。
- screen 完整执行后，每 (block_len,source) 按排序依次 confirmation；失败→下一个，直到
  通过或 5 全失败；pass=存在同一 block_len 使三 source 均有确认通过候选。
- 终态仅允许：pass_finite_budget_ready / de_pass_no_finite_headroom /
  implementation_blocked / resource_blocked（已移除旧 fixed_ensemble_margin_fail）。
- 24h 全局 completed-call 累计资源门；checkpoint 绑定完整 frozen configuration；V26 仅
  archived reference（禁重跑）。
- 文档已写入 openspec/changes/formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate/
  （proposal/design/tasks/specs/…/spec.md）。旧 worst-source 四稿备份于 tmp_v27r/old_*.md。
- 独立 Luna freeze review 尝试多次（subagent 前后台 + muse_spark）均因 subagent 基础设施
  故障未能交付（后台 agent 停在 ready 未返回结果）；故按门控未 ACCEPT、未执行 Phase B。
  待 review 基础设施恢复后，应补跑独立 freeze review（Luna），ACCEPT 后再进 Phase B。

Status: V26 RUN_COMPLETE — pass_target_f13（A02 F03 GF32+GF32 f=1.3 全收敛；只读 verifier run_01/run_02 均 ok；本地归档，不 push）。V27 OpenSpec（finite-leakage-margin DE gate）已写好待主线程 freeze review，未执行。

## 2026-08-19 V26 主体 + V26R closeout 完成（本地提交并归档，未 push）

- V26 科学门：A02（F03 GF32+GF32）f=1.3 全收敛 30/30（2 layer × 3 source × 5 confirm
  seed，final mean entropy 0.00000）；A01（F01 GF512+GF2）f=1.3 失败（GF2 residual 层）、
  f=1.6 通过。终态 `pass_target_f13`。
- 只读 verifier `verify_run`：独立从 `channel_counts.npz` 重建 adapters，重算 72 screen +
  60 confirmation + A02@f=1.3 30/30 + rate/rho/seed/熵轨迹/终态；run_01 与 run_02 均
  0 mismatch、ok=true；结果持久化到各 run `readonly_verify.json`。
- 定义修正：f_i=leak_i/H_i、leak_i=(1-R_i)log2(q_i)、R_i=1-f_i·H_i/log2(q_i) 已在
  proposal/design/spec/report/code 统一（不再出现 `f=R/H`、`R=f·H` 作为正确公式）。
- M1 弱参考修正：`adapter_input_entropy_matches_iter0` 真实进入 MC-DE 首轮
  （record_channel_entropy，err_replay=0）；`gf2_bsc_reference` 改为明确判定
  （noiseless 收敛 / 可行性率收敛 / 容量附近判负）。
- 24h 资源门实现（RESOURCE_LIMIT_SECONDS + resource_blocked 终态）；source↔delay 显式
  元数据（SOURCE_METADATA → adapter/M0 detail/RUN_MANIFEST）。
- run 角色：run_02=canonical、run_01=deterministic_repeat（RUN_MANIFEST + README）。
- 证据：comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/
- 报告：docs/nbldpc-v26-channel-informed-multilevel-de-report-20260819.md。
- V26 OpenSpec 归档至 openspec/changes/archive/；测试 19 passed（含新资源门/delay/修正
  M1 参考测试）。
- V27：已创建 OpenSpec（F03 GF32+GF32、n={1024..8192}、64-bit tag、m_total 整数、
  seeds 27001/27101 系列、三终态）；**只写不执行**，返回主线程 freeze review。
- 禁止项全程遵守：无 degree 搜索、无有限码/FER/MET、无 fresh qual、无 push。
---

Status: V25 COMPLETE — M0–M4 已实现并运行；终态 pass_ready_for_de_change（高域 F01/GF512 + 中域 F03/GF32 供 V26）

## 2026-08-18 V25 M0–M4 实现完成

- P102 ACCEPT（主线程决策）：±1 相邻偏移 + 方向随 source/delay_used_ps 变化 =
  source/delay-conditioned channel（非 alignment blocker）；不重读 .ttbin、不重估亚
  bin delay。
- 五项 minor spec edits 已应用并提交（N_ab/P(A|B) 方向、F01–F05 MSB→LSB 切分、
  frame/symbol/tail 计数、M2 改写、inventory 持久化）。
- 实现：`nonbinary_v25_gate.py`（labeling/factorization/N_ab/P(A|B)/chain-rule/
  M0-M4/verifier）+ CLI + 测试（10 passed）。
- 运行结果（run_04，只读 verifier ok=true）：
  - H(A|B)≈0.80 bits；M0 ±1 结构、M2 方向时间稳定（delay −50→+1、+50→−1）；
  - M1：经验 delta 模型 holdout NLL≈0.81–0.83 远优于 QSC(3.2)/V17(3.3)；
  - M3：chain-rule 闭合（err≤5e-9），F01–F05×L01/L02 分层熵已记录；
  - M4：高域 F01(GF512) + 中域 F03(GF32)，**status=pass_ready_for_de_change**。
- 输出：comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/
- 报告：docs/nbldpc-v25-empirical-channel-and-factorization-report-20260818.md。
- V25 PASS 仅提出 V26（小规模 channel-informed DE），不自动启动；禁止有限码/FER/
  MET/fresh qual/public residual/oracle；本地提交，不 push。
---

Status: V25 DRAFT — 已记录冻结任务包并建立 OpenSpec 草稿；待 P0 只读审计 + 独立 freeze review

## 2026-08-18 V25 立项（文档记录 + OpenSpec 草稿）

- 用户交付 V25 冻结任务包：`docs/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md`。
- 新建 OpenSpec change（DRAFT_PENDING_P0_AUDIT_AND_FREEZE_REVIEW）：
  `openspec/changes/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/`
  （proposal / design / tasks / delta spec）。
- V25 范围：保留 1024-bin 原始符号，建立经验条件信道 P(A|B,Z)，评估 F01–F05 ×
  L01–L02 分层分解（chain-rule 门），终止于 M4 架构选择。不实现 DE/MET/有限码/FER。
- 下一步：P0 只读输入审计（data_inventory.json）→ P1 freeze review ACCEPT →
  工程 I01–I10 + 测试 T01–T12 → M0–M4。
- V24 已 FAIL 并归档；V25 不自动启动任何禁止项；本地提交，不 push。
---


Status: V24 M0–M2 GATE FAIL (single_edge_bounded_optimization_failed) — bounded single-edge route closed; V21/V22/V23 ARCHIVED

## 2026-08-18 V24 gate result: FAIL + M3 closeout

- V24 pre-registered M0-M2 gate completed (background, 314 DE calls, 4.87 h
  accumulated, 0 errors, 0 converged).
- Terminal state: `fail` = `single_edge_bounded_optimization_failed`.
  - M0 mechanism gate PASS;
  - 135 valid unique candidates in 8192 attempts;
  - screen 270 calls 0 converged (entropy floor 0.20-0.32);
  - refine 24 calls 0 converged (entropy ~0.29-0.30);
  - holdout 20 calls (4 finalists x 5 seeds) 0 finalist converged on all seeds
    (final entropy ~0.29-0.30);
  - read-only verifier ok=True, recomputed terminal fail.
- Evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`.
- Report: `docs/nbldpc-v24-gate-report-20260818.md`.
- Interpretation: asymptotic DE-only negative; NO finite-code/FER/qualification/
  promotion/MET claim. True MET or target/q/channel adjustments are separate
  user decisions; no automatic fallback. No push.
- V21/V22/V23 archived under `openspec/changes/archive/2026-08-18-*`.
- STOP per V24 FAIL rule: no further scientific work in this route without
  explicit new user authorization.

---


Status: V24 ENGINEERING DONE (I01-I11) — M0 mechanism gate PASS; M1 screen in progress (background run); archive V21->V22->V23 DONE

## 2026-08-18 V24 engineering + archive + gate launch

- 正式归档 V21/V22/V23 完成，移至 archive（archive note 已写）：
  - `openspec/changes/archive/2026-08-18-formal-nonbinary-ldpc-v21-bob-only-selector-validation/`
  - `openspec/changes/archive/2026-08-18-formal-nonbinary-ldpc-v22-structured-construction/`
  - `openspec/changes/archive/2026-08-18-formal-nonbinary-ldpc-v23-met-protograph-de/`
- V24 工程实现完成（I01-I11）：
  - `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v24_single_edge_de.py`
  - `comparison_bench/src/comparison_bench/cli/run_v24_single_edge_de.py`
  - `comparison_bench/tests/test_nonbinary_v24_single_edge_de.py`（21 tests, all pass）
- 关键实现点：frozen indexed proposal generator（SeedSequence([24000,k])，lambda 先 rho 后）、
  profile validity 仅基于 lambda/rho/rate/f（不含 DE 结果）、M0 read-only V8/V17 校验、
  M1 screen/refine、M2 holdout all-five-seeds，stage-generic ranking，
  per-call JSONL incremental evidence + 24h completed-DE-call resource gate，
  read-only semantic verifier。
- 已启动预注册 M0-M2 scientific gate（background nohup，24h 资源门）：
  - 证据根：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`
  - M0 mechanism PASS；screen 正在写入（非收敛，final entropy ~0.3，与 V22/V23 一致）。
  - 预算：8192 attempts → 135 valid unique；screen 270 calls、refine 24、holdout 20；
    DE 单 call 成本 8-18s(n200) / 257s(n1000) / ~11min(n2000)。
- 预计 gate 时长约 7h；terminal state 大概率 FAIL（当前系综单边 DE 非收敛一致性）。
- P07 由当前 objective 授权；无 push。

---

Status: NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED — V24 P06 ACCEPT，等待 P07 用户授权

## 2026-08-17 current-state correction（supersedes below route-wide wording）

- 本轮只完成 planning/docs；无 code、DE、FER、archive、push。
- V21：`CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE`；保留 S0/S1/S2
  数值，但 P0/P1 未预冻结，runtime Alice-injection/V01 未运行。
- V22：`CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`；仅限 tested
  candidates/current V22b kernel；I03=`CANCELLED_BY_DE_GATE`，
  E02/V01=`NOT_RUN`。
- V23：`CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE`；实现仅 aggregate
  single-edge lambda/rho -> V22b，不是真 protograph/MET；raw scan 仅 3 matrices。
- 旧 `NBLDPC_ROUTE_BLOCKED`/全局不可达/MET failed 表述均 superseded。
- 详细计划：`docs/nbldpc-v21-v24-closeout-and-successor-plan-20260817.md`。
- P06 经三次独立只读 review 最终 ACCEPT；两轮 blocker 均已闭合，P01–P06
  已完成。P07 用户授权前不得实现或执行；实际 archive 与 push 均需另行
  用户授权。

---

The historical status below is retained for chronology and is superseded by
the correction above.

## Current Task — V19 Nonbinary LDPC primary-route diagnostics (2026-08-16)

用户最新决策：
- Binary Polar MLC 已实现（release repo: `D:\Code\HD-QKD_Polar_Release`），只读基线。
- Binary LDPC MLC 已实现（f≈4.17，500 帧全过），只读基线。
- **Nonbinary LDPC 是当前唯一主攻目标。**

执行契约：`docs/nbldpc-focus-plan-20260816.md`（Route N0–N6）。

## 阻塞声明（2026-08-16）
- 已写入 decision-log：本路线（q=1024 结构化 f≤1.3）在现有工具/系综下不可达；
- 无新的可自动推进步骤；等待用户从 4 个选项中决策：
  (a) 完整结构化 DE 优化；(b) 调整目标；(c) MET 多边；(d) 接受现状并归档。

## 最终汇总（2026-08-16）
- 新增 `docs/nbldpc-v19-v23-review-summary-20260816.md`。
- 汇总 V19→V23：oracle 重分类、Bob-only 停止门、结构化 DE not-reachable。
- 42 测试通过；当前无新的可自动推进方向，除非用户提供新目标/方法。

## V23 收尾（2026-08-16）
- q=1024 structured rate0.9375 DE 在 plain/SC/regular-protograph/irregular 系综下均不收敛；
  entropy 下限约 0.19–0.34，远高于 0.01 容差。
- 结论：现有系综下 f≤1.3 结构化高 rate 协调不可达；
  进一步需要完整 DE 优化（Müller 风格）或其他信道分解。
- 证据：`nbldpc_v23_20260816/de_not_reachable_summary.json`。

## V23 Protograph 扫描（2026-08-16）
- 新增 `nonbinary_v23_protograph.py` + CLI + 测试。
- 扫描 regular protographs：(2,32),(3,48),(4,64),(6,96),(8,128) rate≈0.9375，q=1024 结构化 V22b：
  - 全部 non-converged；final entropy 从 0.336 降到 ~0.20（var degree≥3 后平台）。
- 证据：`nbldpc_v23_20260816/protograph_scan_r09375_smoke/scan.json`。
- 下一步：不规则/优化的 protograph 或 MET。

## V23 Protograph DE 启动（2026-08-16）
- 立项 `formal-nonbinary-ldpc-v23-met-protograph-de`（DRAFT）。
- 首个 protograph smoke：B=ones(2,32)，rate=0.9375，lambda={2:1}，rho={32:1}；
  q=1024 结构化 V22b，n200/iter50/degree_max=512 → non-converged（final entropy≈0.336）。
- 证据：`nbldpc_v22_20260816/v23_protograph_2x32_ones_smoke.json`。
- 下一步：扫描小 protograph 网格；必要时加 MET。

## V22 收尾（2026-08-16）
- V22 结构化 DE 在 q=1024, rate=0.9375 不收敛（含 n200/iter30/degree_max=512）。
- 冻结为 `scientific_not_ready`，不进入有限码构造；
- 决策记录写入 decision-log。下一步候选：MET/protograph DE（V23）。

## V22b 更大预算扫描（2026-08-16）
- q=1024, rate=0.9375, degree_max=512, n_samples=200, max_iter=30：
  - 3 候选仍全部 non-converged。
- 证据：`nbldpc_v22_20260816/v22b_de_gate_q1024_r09375_dmax512_iter30_n200/de_gate.json`。
- 说明：结构化信道下目标 rate 的 plain/SC 候选在当前工具范围内不收敛；
  需 MET/protograph 或接受 `scientific_not_ready`。

## V22b 实现（2026-08-16）
- 新增 `nonbinary_v22b_mcde.py`（临时提升 V14 DEGREE_MAX）+ `nonbinary_v22b_de_gate.py` + CLI + 测试。
- q=1024, rate=0.9375, degree_max=512, n_samples=100, max_iter=10：
  - 可运行（不再触发 degree cap）；
  - 3 候选均 non-converged。
- 证据：`nbldpc_v22_20260816/v22b_de_gate_q1024_r09375_dmax512_smoke/de_gate.json`。
- 下一步：增大 DE 预算/优化候选，或 SC-LDPC 结构化适配。

## V22 规划决定（2026-08-16）
- V22 task packet 已冻结：
  - 方案：新增 additive V22b structured MC-DE，支持 configurable DEGREE_MAX>=128；
  - 之后再做 SC-LDPC 结构化信道适配。
- 原因：V14/V11 MC-DE 的 check degree cap=64，导致 q=1024 rate≈0.9375 无法运行。
- 下一步实现 I04。

## V22 进展 5（2026-08-16）
- q=1024 结构化 DE gate 诊断：
  - rate=0.70：可运行（penalty=0），3 候选 non-converged；
  - rate=0.9375：因 concentrated rho 的 check degree >64，触发 V14 MC-DE cap，无法运行。
- 说明：现有 V14 结构化 MC-DE 在高 rate（f≤1.3 对应）受 check-degree cap 限制；
  SC-LDPC V10 winners 只能在低 rate 通过，尚不匹配目标 f。
- 证据：`nbldpc_v22_20260816/de_gate_q1024_r070_structured_smoke/de_gate.json`。

## V22 进展 4（2026-08-16）
- q=1024 SC-LDPC DE gate 扫描：
  - p=0.20/0.10/0.05，max_iter=20 均 non-converged；
  - **p=0.05, max_iter=50：6/6 全部 converged，gate_passed=true**。
- 证据：`nbldpc_v22_20260816/sc_de_gate_q1024_p005_iter50_smoke/sc_de_gate.json`。
- 说明：SC-LDPC DE 在低 QSC 噪声点可通过；下一步需映射到 V17 结构化信道/目标 f。

## V22 进展 3（2026-08-16）
- 新增 SC-LDPC DE gate：`nonbinary_v22_sc_de_gate.py` + CLI + 测试（复用 V11 frozen kernel/geometries）。
- q=1024, p=0.20 smoke：V10 S1/S3 × G1/G2/G3 共 6 行，全部 non-converged（max_iter=10, n_samples=100）。
- 证据：`nbldpc_v22_20260816/sc_de_gate_q1024_p020_smoke/sc_de_gate.json`。
- 下一步：增加 DE 预算/更合适 p，或结构化信道适配。

## V22 进展 2（2026-08-16）
- q=1024 DE gate smoke：3 个合法 8-degree 候选，rate=0.9375, n_samples=100, max_iter=5。
- 结果：全部 non-converged/error，`gate_passed=false`。
- 证据：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v22_20260816/de_gate_q1024_r09375_smoke/de_gate.json`。
- 下一步：需要真正的 MET/protograph/SC 结构化 ensemble 或更大 DE 预算。

## V22 进展（2026-08-16）
- 新增 `nonbinary_v22_de_gate.py` + CLI `run_v22_de_gate.py` + 测试。
- q=16 smoke gate：3 个合法 8-degree 候选，全部 non-converged（rate=0.6, 小预算）。
- 下一步：在 q=1024 结构化信道上运行 DE gate（需选择合法候选与预算）。

## V21 执行结果（2026-08-16）
- 实现 `nonbinary_v21_bob_only.py` + CLI + 测试（3 passed）。
- 全新 64 帧 Bob-only 结果：
  - S0 BP-only：24/64，FER=0.625
  - S1 bounded4-only：28/64，FER=0.5625
  - S2 BP-first-fallback-bounded4：28/64，FER=0.5625
- 停止门触发（全部 ≥0.45）：冻结短块 OSD/top-K 分支为 `scientific_not_ready`。
- V22 OpenSpec 草稿已创建：`formal-nonbinary-ldpc-v22-structured-construction`。
- V20 已移入 `openspec/changes/archive/2026-08-16-formal-nonbinary-ldpc-v20-q1024-decode-improvement/`。

## V21 规划更新（2026-08-16）
- 新增执行契约：`docs/nbldpc-v21-bob-only-plan-20260816.md`。
- V20 审查结论已写入 audit addendum 与 decision-log：
  - 31/64 → oracle upper bound；
  - 40/96 → top-4 oracle coverage；
  - standalone bounded4 30/64 → unverified Bob-only estimate；
  - V01 → counting-only。
- V20 status 统一为 `CONCLUDED_PENDING_SCIENTIFIC_CORRECTION_AND_ARCHIVE`。
- 下一步执行 Phase 0 收口，然后启动 V21 实现/验证。

## Round 108 更新（2026-08-16）
- 使用规划 subagent 评估：建议 **归档 V20 M5**，保留 n64+bounded4 31/64 (FER=0.515625) 为最佳诊断结果；
  若继续，另开新 change 做 top-K + 公开哈希/盲协调。
- 已按建议添加 `archive_note.md`，V20 tasks 状态改为 ARCHIVED。
- 当前主线阶段性收尾完成。

## Round 107 更新（2026-08-16）
- 尝试 V20 M2 随机 dense 校验矩阵构造（n=64,m=4, seed=2252）：
  - random dense + bounded4：**3/8 exact**
  - PEG + bounded4 同 seed：**5/8 exact**
- 结论：随机 dense 构造不优于 PEG；M2 简单变体仍无增益。

## Round 106 更新（2026-08-16）
- 全量回归测试通过：**33 passed**。
- V20 M5 标记 COMPLETE；P1 完成（M5 已选择并执行）。
- 当前无自动下一步；继续需要用户选择 M2/M3 或接受归档。

## Round 105 更新（2026-08-16）—— V20 M5 最终结论
- 生成最终 N6 v6 对比表：`n6_comparison_v6_q1024_v20_final/`。
- 结论：
  - **n64 + bounded4 为主推**：31/64，FER=0.515625；
  - n80 + bounded5 top-K 为备选：40/96，FER=0.5833（12 seeds，高方差）；
- V20 M5 标记 CONCLUDED；后续如需继续，应转向 M2/M3 或用户新方向。

## Round 104 更新（2026-08-16）
- 新增 n80 seed=2026082312：baseline 1/8 -> integrated 1/8（无增益）。
- 目前 12 个 n80 seeds 汇总：
  - baseline 33/96 (FER≈0.6563)
  - integrated 40/96 (FER≈0.5833)
- n80 平均仍明显差于 n64 0.515625；继续扩样未见稳定反超。
- 建议考虑停止 n80 扩样，回到 n64 作为主推，或探索混合策略。

## Round 103 更新（2026-08-16）
- 新增 n80 seed=2026082311：baseline 4/8 -> integrated 4/8（无增益，潜在帧已被 baseline 覆盖）。
- 目前 11 个 n80 seeds 汇总：
  - baseline 32/88 (FER≈0.6364)
  - integrated 39/88 (FER≈0.5568)
- n80 平均仍差于 n64 0.515625；正收益主要来自部分 seed，整体不稳定。

## Round 102 更新（2026-08-16）
- 新增 n80 seed=2026082310：baseline 0/8 -> integrated 0/8（无增益，潜在 0/8）。
- 目前 10 个 n80 seeds 汇总：
  - baseline 28/80 (FER=0.65)
  - integrated 35/80 (FER=0.5625)
- n80 高方差：9 seeds 时曾 0.5139，加入 2310 后回落至 0.5625，已差于 n64 0.515625。
- 结论：n80 top-K 有正收益但不够稳定，尚不能作为确定更优配置。

## Round 101 更新（2026-08-16）
- 新增 n80 seed=2026082309 top-K=4 集成：
  - baseline 3/8 -> integrated 4/8（恢复 frame3）
- 目前 9 个 n80 seeds 汇总：
  - baseline 28/72 (FER≈0.6111)
  - integrated **35/72 (FER≈0.5139)**
- 正收益 seeds：2301、2303、2305、2306、2307、2308、2309；无增益：2300、2304。
- n80 integrated 已**略优于 n64** 的 31/64 (FER=0.515625)。

## Round 100 更新（2026-08-16）
- 新增 n80 seed=2026082308 top-K=4 集成：
  - baseline 2/8 -> integrated 3/8（恢复 frame7）
- 目前 8 个 n80 seeds 汇总：
  - baseline 25/64 (FER≈0.6094)
  - integrated 31/64 (FER=0.515625)
- 正收益 seeds：2301、2303、2305、2306、2307、2308；无增益：2300、2304。
- n80 integrated 与 n64 最佳打平（均为 31/64, FER=0.515625）。

## Round 99 更新（2026-08-16）
- 新增 n80 seed=2026082307 top-K=4 集成：
  - baseline 4/8 -> integrated 5/8（恢复 frame0）
- 目前 7 个 n80 seeds 汇总：
  - baseline 23/56 (FER≈0.5893)
  - integrated **28/56 (FER=0.5)**
- 正收益 seeds：2301、2303、2305、2306、2307；无增益：2300、2304。
- **n80 integrated FER=0.5 已优于 n64 的 0.515625**，是当前新的最佳配置。

## Round 98 更新（2026-08-16）
- 新增 n80 seed=2026082306 top-K=4 集成：
  - baseline 4/8 -> integrated 5/8（恢复 frame5）
- 目前 6 个 n80 seeds 汇总：
  - baseline 19/48 (FER≈0.6042)
  - integrated 23/48 (FER≈0.5208)
- 正收益 seeds：2301、2303、2305、2306；无增益：2300、2304。
- n80 integrated 已几乎追平 n64 的 31/64 (FER=0.515625)。

## Round 97 更新（2026-08-16）
- 新增 n80 seed=2026082305 top-K=4 集成：
  - baseline 3/8 -> integrated 4/8（恢复 frame3）
- 目前 5 个 n80 seeds 汇总：
  - baseline 15/40 (FER=0.625)
  - integrated 18/40 (FER=0.55)
- 正收益 seeds：2301、2303、2305；无增益：2300、2304。
- n80 integrated 平均 FER=0.55，仍略高于 n64 的 0.515625，但差距缩小。

## Round 96 更新（2026-08-16）
- 新增 n80 seed=2026082304 top-K=4 集成：baseline 3/8 -> integrated 3/8（无增益）。
- 目前 4 个 n80 seeds 汇总：
  - baseline 12/32 (FER=0.625)
  - integrated 14/32 (FER=0.5625)
- 正收益仅 2301/2303；2300/2304 无增益。当前 n80 平均尚未优于 n64 的 31/64 (FER=0.515625)。
- 需继续扩样或转向其他机制。

## Round 95 更新（2026-08-16）
- 新增 n80 seed=2026082303 top-K=4 集成：
  - baseline 3/8 -> integrated 4/8（恢复 frame1）
- 目前 n80 正收益 seeds：
  - 2301：4/8 -> 5/8
  - 2303：3/8 -> 4/8
  - 两 seed 合计 baseline 7/16 (FER=0.5625) -> integrated 9/16 (FER=0.4375)
- 2300 无增益（2/8 -> 2/8）；2302 潜在 2/8 待集成。
- 结论：n80+bounded5 top-K 有统计性改善潜力，需继续扩样。

## Round 94 更新（2026-08-16）
- n=80,m=5 seed=2026082301 top-K=4 列表集成：
  - baseline（无 bounded-ML）：**4/8 exact**
  - + bounded5 top-K 列表：**5/8 exact**（frame5 被恢复）
- 这是 n80 首个正收益证据；FER 从 0.5 降到 0.375（单 seed）。
- 说明 n80+m5+bounded5 top-K 有潜力超过 n64 当前 31/64。
- 下一步需跑更多 n80 seeds 统计平均 FER。

## Round 93 更新（2026-08-16）—— V20 M5 收尾
- 执行 V01 只读验证：8 个 bwml 输出共 **31/64 exact，FER=0.515625**，无计数问题；N6 v5 存在。
- V20 tasks 标记 M5 COMPLETE，V01/C01/C02 完成。
- 当前状态：V20 M5 已达到本路线能自动推进的终点；进一步降低 FER 需要新机制（如真正可用的盲协调/公开哈希选择、更强构造）或用户新方向。
- 验证文件：`nbldpc_v20_20260816/v01_readonly_verify.json`。

## Round 92 更新（2026-08-16）
- 新增 `edge_label_seed` 支持（API + CLI `--edge-label-seed`）。
- 固定 frame seed=2026082252、code seed=2026082252，edge-label-seed 1/2/3：
  三个变体均为 **5/8 exact**，无提升。
- 结论：仅换 edge label 不能改善 n64 bounded4 结果；M2 简单变体也无增益。
- 新增 edge_label_seed 测试；全量 33 passed。

## Round 91 更新（2026-08-16）
- 附加 n64 bounded4 探针：
  - lambda {2:0.62,3:0.38} seed2204：5/8（与无 bounded4 相同）
  - lambda {2:0.58,3:0.42} seed2220：4/8（与无 bounded4 相同）
  - rho {35,39} seed2252：3/8（比默认 rho 的 5/8 差）
- 结论：bounded4 在当前 lambda/rho 邻域没有进一步增益；n64 最佳仍 31/64, FER=0.515625。
- V20 M5 已覆盖主要变体，下一步需转向其他机制或收尾。

## Round 90 更新（2026-08-16）
- 新增 `frame_offset` 支持（API + CLI `--frame-offset`），用于分块跑长有限码实验。
- n=80,m=5 seed=2026082300 用 top-K=2 分块完整集成：仍 **2/8 exact**（与 V19 相同，无净提升）。
- 结论：n80 的 bounded5/top-K 在当前单 seed 上不能超过 V19；n64 bounded4 仍是唯一实际改进点（31/64, FER=0.515625）。
- 新增 frame_offset 测试；全量 32 passed。

## Round 89 更新（2026-08-16）
- 实现 V20 top-K 列表解码：`bounded_weight_ml_decode_candidates`（max_weight=5, top_k=4）。
- 直接测试 n=80,m=5 seed=2026082300 frame0：Alice 在 top4 候选内（列表第 1 位）。
- 单帧完整管线验证 frame0 可 exact；完整 8 帧因 top-K 枚举较慢超时，需后续优化。
- n64 bounded4 单 ML 仍保持 31/64, FER=0.515625。
- 新增测试 candidates；全量 31 passed。

## Round 88 更新（2026-08-16）
- 将 V20 bounded-weight ML 扩展支持 `max_weight=5`（n=80,m=5，同 f≈1.136），新增 numba k=5 枚举与测试。
- n=80,m=5 seed2300 完整集成验证：仍 **2/8 exact**（与 V19 OSD 相同）。
  原因：单 ML 会选到 weight<=3 的错误码字（先验得分高于 Alice），bounded5 的 Alice 候选不是全局最高分。
- 结论：n80 需要 top-K 列表 + 公开校验/哈希才能利用 bounded5；n64 bounded4 单 ML 仍是最佳实际改进点（31/64, FER=0.515625）。
- 新增测试 `test_bounded_weight_ml_decode_max5_small_identity`；全量 30 passed。

## Round 87 更新（2026-08-16）
- 完成 V20 bounded-ML 的 **64 帧完整集成验证**：
  - 8 个 seed 全部用含 bounded-ML 的完整管线运行；
  - 总计 **31/64 exact_correct, FER=0.515625**（较 V19 28/64 提升 3 帧）。
- 新增 N6 对比表 v5：
  `n6_comparison_v5_q1024_v20_bwml/comparison_table.csv` + `comparison_summary.json`，
  加入 `nonbinary_ldpc_q1024_f1136_v19` 与 `..._v20_bwml` 两行。
- 当前 q=1024 f≈1.136 最佳 FER=0.515625（仍为 diagnostic_only）。

## Round 86 更新（2026-08-16）—— V20 已批准并开始执行
- 用户批准直接进行 V20 规划与执行；V20 proposal/design/tasks 状态改为 APPROVED/IN PROGRESS。
- 新增 V20 M5：`nonbinary_v19_bounded_ml.py`（bounded-weight ML 解码，max_weight=4，numba 加速）。
- 集成到 `nonbinary_v19_finite`：在 V19 OSD 全失败后追加 bounded-ML post-decoder。
- 结果（n=64, m=4, lambda {2:0.6,3:0.4}, f≈1.136, 64 帧）：
  - 原 V19 最佳：28/64 exact, FER=0.5625
  - 加 bounded-ML 后：**31/64 exact, FER=0.515625**
  - 恢复的 mismatch 帧 seeds：2026082260、2026082144、2026082192（均已用完整管线验证）。
- 新测试：`test_nonbinary_v19_bounded_ml.py`；全量测试 28 passed（待最终确认）。

## Round 85 更新（2026-08-16）
- 新增 BP 随机先验扰动重试诊断（blind-reconciliation 风格预研）：
  - hard frame 2055：beta=0.01/0.05/0.1/0.2 各 50 次重试均未恢复；
    beta=0.5 因数值溢出/超时未完成。
  - seed 2252 的 3 个 mismatch 帧：beta=0.05 各 20 次重试均未恢复。
- 结论：BP 重试/随机扰动在当前码族上不能有效跳出 exact_mismatch；
  V19 路线（PEG/FFT-QSPA/OSD/MRB/BP-retry）已穷尽。
- 下一步唯一可自动推进的是 V20 冻结；否则需要用户提供新方向/新数据。

## Round 84 更新（2026-08-16）
- 新增 `frame_seed` 分离支持（`nonbinary_v19_finite.execute_synthetic_frames` + CLI `--frame-seed`），
  新增 1 个测试。
- 固定 hard frame seed 2055、换 code seed 3001-3005：全部 `exact_mismatch`，未恢复。
- rho 变体 {35,39}、{33,41}、{30,44} 在 frame 2055 上仍 `exact_mismatch`。
- 直接 MRB-OSD probe（OSD-2 all-free/symbols 4-8、OSD-3/4 bounded、OSD-3 all-free/symbols 2）
  均未找到 Alice 码字。
- 结论：V19 PEG/FFT-QSPA/OSD 家族在 q=1024 f≤1.3 已穷尽；V20 草稿已补充 Round 83-84 证据，
  状态置为 ready for freeze review。下一步需用户/主线程批准 V20 冻结。

## Round 83 更新（2026-08-16）
- 扩展最佳配置 n=64, m=4, lambda {2:0.6,3:0.4}, f≈1.136 到 64 帧：
  28/64 exact_correct, FER=0.5625（比 32 帧的 15/32=0.53125 略高，但样本更大更诚实）。
- 同 f 中间块长诊断：n=80,m=5 → 2/8 exact (FER=0.75)；n=96,m=6 → 1/8 exact (FER=0.875)，
  均差于 n=64；n=64 仍是该 f 点最佳块长。
- 实现可靠性排序信息集 OSD（MRB-OSD）：`osd_decode_candidates_mrb`，
  新增 2 个测试；集成到 `nonbinary_v19_finite`（n<=64 自动追加 MRB OSD-1 full + MRB OSD-2 broad）。
- MRB-OSD 初步对照：seed 2252 仍是 5/8，seed 2276 仍是 2/8，当前未见提升；
  需在更多 hard seeds 上评估。
本轮完成：
- 新增 V19 模块（`nonbinary_v19_channel.py`, `nonbinary_v19_de_search.py`,
  `nonbinary_v19_finite.py`）、两个 CLI（`run_v19_nbldpc.py`, `run_v19_three_way_compare.py`）、
  4 个测试文件；11 个 V19 测试通过。
- N1 channel evidence: `nbldpc_primary_20260816/n1_channel/channel.json`
  （folded q=16 H≈0.382911；full q=1024 H_full=0.549955）。
- N2a warm-started rate ladder: `n2_rate_ladder/rate_ladder.json`
  从 rate-0.60 best 暖启动后，小预算下 rate=0.65 不收敛；与既有 plain 天花板一致。
- N2c extended-degree probe: `n2_extended_probe/extended_degree_probe.json`
  degree 48/60 候选在 rate=0.65 结构化信道上均不收敛。
- N3/N4 finite q=16 synthetic execute-once:
  `n4_finite_q16_r060_simple/finite_execute.json`
  n=512, m=205, rate≈0.5996；4 帧 3 exact_correct / 1 exact_mismatch / 0 decode_failed；
  f_plain≈4.183，FER=0.25；exact_mismatch 原样保留。
- **q=1024 主攻推进**：
  - `n4_finite_q1024_simple/finite_execute.json`：q=1024 n=64 m=24 rate=0.625，
    2 帧 2/2 exact_correct，FER=0，f≈6.819；
    `n4_finite_q1024_n128_simple/finite_execute.json`：n=128 m=51 rate≈0.602，
    2/2 exact_correct，FER=0，f≈7.245；`n4_finite_q1024_n128_4frames/` 4/4 exact_correct。
  - `n2_extended_probe_q1024/extended_degree_probe.json`：q=1024 rate=0.6
    simple lambda 小样本 DE probe 未收敛（diagnostic）。
  - `n2b_channel_aware_bounds/lsb_public_capacity.json`：capacity-ideal 显示
    LSB-public 不能降低 f（l=0 ideal f≈1.00, l=1 ideal f≈2.40），主攻应继续 full q=1024；
    `high_plane_channels.json` 生成 LSB-public 残余高位有效信道（l=0..6）供后续 DE。
  - `n6_comparison_v2_q1024/`：三路表新增 `nonbinary_ldpc_q1024` 行；
    `leakage_decomposition.json` 记录 q=16 folded 全信道诚实 f≈3.016、
    q=1024 n=128 f≈7.245。
  - **q=1024 high-rate 有限码尝试**：
    `n4_finite_q1024_r084_simple_16f/`（R≈0.84, f≈2.912, FER=0.5）、
    `n4_finite_q1024_r089_simple/`（R≈0.89, f≈1.989, FER=0.8125）、
    `n4_finite_q1024_f129_n1024_4f/`（n=1024 m=73, R≈0.929, f≈1.296,
    4/4 decode_failed, FER=1.0）；
    `n6_comparison_v4_corrected_statuses/` 记录 corrected statuses
    （exact_mismatch 仅指 syndrome-consistent wrong word）。
  - 增加可选 `rho_edge` 精确 socket rho 构造；`n4_finite_q1024_optrho_n512_m64/`
    使用 V18-B2 优化 lambda + 三点 rho 在 R=0.875 仍 4/4 decode_failed；
    `find_two_degree_rho` 增加整数两度 rho 构造；Müller 归一化 lambda 在
    f≈1.296（n=1024）与 f≈1.989（n=256）仍 decode_failed；
    n=2048 m=133 f≈1.181 长块尝试也 decode_failed；
    实现 bounded q-ary OSD-0/1（`nonbinary_v19_osd.py`）后，R=0.89 q=1024
    4 帧提升为 2 exact / 2 exact_mismatch / 0 decode_failed（FER=0.5）；
    f≈1.296 n=1024 1 帧仍 exact_mismatch（OSD-0 找到合法码字但非 Alice）。
- N6 three-way comparison（v1 q=16）: `n6_comparison/comparison_table.csv` + `comparison_summary.json`
  Binary LDPC MLC f≈4.169（FER=0）；Nonbinary LDPC f≈4.183（FER=0.25）；
  Polar MLC 在 release repo 中，当前表标记 `not_available` 直到提供 clean evidence JSON。

边界：全部 `diagnostic_only`；不构成 fresh/promotion/qualification。
P1/P2/V13 legacy 等既有冻结终态均不变。
结论：V19 诊断已推进到 full OSD-1 方向。q=1024 f≤1.3 下，n=64 full OSD-1
FER=0.5（3/6 exact），n=128 FER=0.75（1/4 exact），证明 exact 可行但尚不可靠。
下一步需冻结 V20 OpenSpec change（`formal-nonbinary-ldpc-v20-q1024-decode-improvement`）
并实现更高效/更高阶 OSD 或改进码构造。

---

## Previous Task — 主攻 Nonbinary LDPC；Polar 与 binary LDPC 仅做对比基线（计划就绪）(2026-08-16)

用户最新决策：
- Binary Polar MLC 已实现，只读作为基线。
- Binary LDPC MLC 已实现（f≈4.17，500 帧全过），只读作为基线。
- **Nonbinary LDPC 是当前唯一未实现、需全力攻克的目标。**

执行契约：`docs/nbldpc-focus-plan-20260816.md`（Route N0–N6）。
关键复用：V18 B2 structured DE（q=16 folded rate=0.60 f≈4.18）、V10 DE/PEG/FFT-QSPA、
V14 structured MC-DE、QSC 等熵对照证据。
本仓库当时仅保存计划；执行在后续对话中继续。

---

# CURRENT_TASK.md


## Current Task — V13-R3 legacy drift audit：按用户决定使用 2026-01-21 三源执行 (2026-08-16)

**目标状态：完成。** 用户指定的 2026-01-21 三源已按 `legacy_drift_audit` 路径
完成 192 帧审计，并进一步完成全量 8412 帧审计：
**8284/8412 exact_correct、128 decode_failed、0 exact_mismatch**。
全量 8 chunk 各自 verify OK，合并证据包已生成。

用户明确表示这些是之前采集的数据、纠错算法对具体数据源要求没那么高，并要求
**使用这三份 `2026-01-21` 数据继续进行**。按冻结规则，不以 fresh-confirmation
路径进入 P/E/V，而是另开独立 change
`formal-nonbinary-ldpc-v13-r3-legacy-drift-audit`，claim boundary **仅限
`legacy_drift_audit`**。

- **实现/测试**：新增 `nonbinary_v13r3_legacy_audit.py`、
  `run_v13r3_legacy_drift_audit.py` + 8 个测试，全部通过。
- **生产执行（一次）**：三源各取前 64 个完整帧（frame_id 0..63，共 192 帧），
  不变 R3 候选（`nbldpc_v13_r3_code_v1`，p=.20，flooding，max_iter=100）解码一次。
  结果：**188/192 exact_correct**；4 帧 `decode_failed`（`iteration_limit`：
  1M 源 frame 15/20，2M 源 frame 52/56），全部原样保留。
- **verify**：只读验证通过（192 行、claim/frozen binding/hash 全部 OK）。
- **证据包**：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`
- **P1**：`v13r3fresh_prepare_20260815/no_eligible_package.json` 冻结终态不变；
  本结果不构成 fresh-confirmed/promotion/qualification。
- **P2（V17）**：`mechanism_unverified` 终态不变。
- **push**：仍待用户单独授权；本地文档/证据已提交。

---

## Previous Task — V13-R3 fresh 数据准入已拒绝；D1–D5 已执行，D5 drift_exceeded；P/E/V 不进入 (2026-08-16)


**状态：本目标已完成。** D1–D5 已按文档执行并验证；D5 三源 `drift_exceeded`，
P/E/V 不进入。另已运行 README/RUN_COMMANDS 中的安全检查：`unittest` 5/5 通过、
`smoke_test` 通过、`compileall` 通过。

按用户更新后的目标（P0→P1→P2）继续，但 **2026-01-21 三源已通过 D0 判定为
`data_intake_rejected_for_fresh_confirmation`**，不得作为 fresh 证据进入 P/E/V。

- **D0（已完成）**：新增 `v13r3fresh_intake_20260816` 证据包，判定三个
  `2026-01-21` Type2 源不满足 frozen fresh 条件（时间戳早于 V13 历史、损耗
  元数据不可核验；folder1 已有 D2 烟测 `raw_ser=0.254663`，远超 V13 D01
  参考 0.0771）。完整规划：
  `docs/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md`。
- **D1–D5（已完成）**：按修正参数执行完毕（2026-08-16，shell 可用后）：
  D1 环境/git 基线、D2/D3 三源 sidecar 提取（`map_sanity` 全 FAIL）、
  D4 三源 pairs-table + manifest、D5 全量漂移预检。
  D5 结果：**三源全部 `precheck_state=drift_exceeded`**（raw SER mean
  ≈0.240–0.256，偏差远超 0.03 阈值）→ 自动停止，不进入 P/E/V。
- **P1（历史冻结终态保持）**：`v13r3fresh_prepare_20260815/no_eligible_package.json`
  不变；P1 仍阻塞于真正 fresh 数据。
- **P2（V17）**：保持 `mechanism_unverified` 冻结终态；位面/边标签效率路线冻结。
- **push**：仍待用户单独授权；本地文档/证据可先提交。
- **下一步**：若用户提供真正 fresh 10 dB Type-II 数据，则重新进入 D1–D5→P1；
  若用户坚持用 2026-01-21 数据，则另开 legacy drift audit change，不能叫
  fresh-confirmed。

---

## Current Task — P2 V17 门冻结终态 mechanism_unverified；P1 阻塞于 fresh 数据 (2026-08-16)

按用户更新后的目标（P0→P1→P2）继续：

- **P0（已完成）**：V12 归档（`archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`，
  source_partition_blocked/X01/X02 未执行/v2 prepare 包保留）；V15/V16
  归档为 aborted drafts（`...-aborted/`）；陈旧文档全修复；V14 测试
  数字统一（62/62→64/64）。本地领先 `origin/main` 36+ 提交；**push 待
  单独授权**。
- **P1（冻结终态，阻塞于数据）**：change
  `formal-nonbinary-ldpc-v13-r3-fresh-acquisition` 冻结 + freeze review
  ACCEPT；PREP 工具实现（FA1–FA5，19 测试）+ 生产 prepare 执行一次 →
  **`no_eligible_frames`**（`D:\Data` 无 fresh 帧数据源，合法冻结结果；
  包 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_prepare_20260815/`）；
  主线程 review ACCEPT → 判定 **frozen failure（数据不可得）**。
  execute/verify 阻塞于 fresh 数据；用户提供新数据后重新 prepare
  （确定性工具）即可继续。
- **P2（冻结终态，FAIL 类）**：change
  `formal-nonbinary-ldpc-v17-multibit-structured-de-gate` 生产 gate
  执行一次 → **`gate_state=mechanism_unverified`**（Stage 0 锚点 A
  Δ=0.0075>0.005 失败；锚点 B |δ|=0.009≤0.012 通过；Stage 1 模型
  熵 0.549955；Stage 2 12 点诊断全部未收敛）；strict replay 5/5
  字节一致；E02 独立 gate review **ACCEPT（零 blockers）**；C01
  收尾完成。位面/边标签效率路线**冻结**：不启动 V15/V16、不扩大
  搜索、无 rerun/调参。效率路线下一步只能由用户决定另开新 change
  （② SC-LDPC、③ 多边/高维 λ）。

---

## Previous Task — P1 prepare 完成（no_eligible_frames）；P2 V17 门生产执行 (2026-08-15)

2026-08-15 状态，已被上方 2026-08-16 Current Task 取代（P2 已冻结
关闭）。P1 `no_eligible_frames` 终态与 P2 实现/生产执行记录见上。

---

## Previous Task — V14 效率可行性门：FAIL（效率路线冻结）；V15/V16 不立项 (2026-08-15)

V14 gate（`openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/`）
按冻结计划完成：Stage 0 机制回归 PASS、Stage 1 折叠验证全绿、Stage 2
的 12 个 q=1024 冻结点（3 λ × m∈{15,16,17,18}）**全部非收敛**（最终
base-q 熵 0.288–0.357，阈值 0.01 的 29–36 倍）→ **gate_state=fail**。
E02 独立 gate review ACCEPT（FAIL 机械正确、纪律干净）；strict replay
完成（科学文件 5/6 字节一致、manifest 仅 provenance 四字段差异，
V10 先例）；C01 完毕（decision-log + 记忆 §49）。

- 结论：冻结的普通不规则系综在 rate 0.93–0.94（f≤1.3 区间）上无 BP
  收敛点——效率路线按 V14 冻结纪律**终止**；V15/V16 提案/设计骨架
  已于 2026-08-15 归档为 aborted drafts（见 P0）。
- 路线状态：V13 R3（f≈12.1）仍是唯一经验证的精确纠错器；
  fresh-confirmation-only 路线不受影响（P1 已启动）。

---

## Previous Task — V13 Existing-Data Nonbinary LDPC Diagnostics: COMPLETE (2026-08-14)

The change
`openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/` has
completed the full frozen route and reached the terminal claim
**`ready_for_fresh_confirmation`**: P01-P08 accepted; D01-D03 + DT0-DT2; D04
baseline probe (8/32 exact); D05 root-cause (`code` / `diagnosis_complete`,
independent review ACCEPT); R3 code-only candidate `nbldpc_v13_r3_code_v1`
(frozen amendment; IT0-IT3, 49/49 tests); E01 screen 64/64 candidate exact
(baseline 13/64); E02 (candidate frozen); A01 retrospective audit 128/128
exact -> `ready_for_fresh_confirmation`; A02 cross-stratum bw120 128/128 +
bw180 128/128 (no promotion); **C01 independent acceptance ACCEPT (zero
blockers)**. Memory triage done (AGENT_PROJECT_MEMORY §47).

- Evidence packages (all under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/`):
  v13_d01_20260814, v13_d04_20260814, v13_d05_20260814_corrected (+
  v13_d05_20260814_invalid_execution_notice.json for the retained first
  emission), v13_e01_20260814, v13_a01_20260814, v13_a02_20260814. All
  verified read-only and committed (ed4bb690 .. 4c0f27a4).
- Claim boundary: `ready_for_fresh_confirmation` is the MAXIMUM V13 state —
  NOT promotion/qualification/fresh correction. **User decisions pending**
  (independent of V13, not auto-triggered): ① whether to open a NEW OpenSpec
  change for fresh acquisition (new frame identities, prepare/review/
  execute/verify chain) to advance confirmation/qualification/promotion of
  the R3 candidate; ② the V12 archive decision (separate housekeeping; V12
  stays `source_partition_blocked`, X01/X02 not reopened).

---

## Previous Task — V13 Existing-Data Nonbinary LDPC Diagnostics: READY_FOR_FRESH_CONFIRMATION, C01 PENDING (2026-08-14)

Earlier 2026-08-14 state, superseded by the freeze review and D stage above.
The new planning change
`openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/`
recorded the user's decision to diagnose the algorithm using existing 10 dB
Type-II, q=1024 Gray 256-symbol data before considering a new acquisition.
Existing rows were sufficient for retrospective diagnostics/development, but
their frame/payload identities are historical V4/V5 identities and cannot be
fresh-canary, confirmation, qualification, or promotion evidence.

- P01-P07 were drafted only; P08 (independent read-only freeze review) was
  the next scientific task and is since complete.
- All D/R/I/E/A/C tasks were unauthorized and unexecuted; the planning turn
  performed no code change, test, decoder call, telemetry run, data
  execution, output generation, archive, or Git write operation.
- V12 remained `source_partition_blocked`; its archive is a separate
  housekeeping decision and did not block V13 plan review. Do not reopen
  V12-X01/X02.
- If later authorized, diagnostic artifacts go only to the additive
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/` root;
  frozen baseline directories and official qualification roots stay unchanged.
- The six-file diagnostic package uses `diagnostic_outcomes.csv` for baseline,
  candidate-development, and retrospective-audit rows with explicit `phase`
  and `method` fields.

Claim boundary was: the highest future V13 state is
`ready_for_fresh_confirmation`; fresh acquisition or qualification requires a
separate OpenSpec change and explicit user decision.

---

## Previous Task — V12 Nonbinary LDPC Real Micro-Feasibility: TERMINAL `source_partition_blocked` (2026-08-13)

The change
`openspec/changes/formal-nonbinary-ldpc-v12-real-micro-feasibility/` is in
TERMINAL STATE **source_partition_blocked**: the four-frame bw200
micro-feasibility canary cannot be executed because the reconstructed
traceable 10 dB pool (2304 rows, 768 per stratum incl. 768 bw200 rows) is 100%
covered by historical frame/payload identities from the V4 10 dB/16 dB
transfer locks and V5 development/partition role locks (2848 excluded frame +
2688 excluded payload identities; identical union in both prepare runs). Zero
fresh eligible bw200 rows; a fresh acquisition would be required for any
future four-frame canary.

- Implementation (V12-I01..I05) and engineering acceptance (V12-T0..T2, 41/41)
  complete; prepare lane (RP01-RP03) executed, official package at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
  (v1 intermediate deleted by explicit user decision).
- Decision-log and memory triage completed on 2026-08-13; V12-D02 is complete.

There is currently no authorized execution successor. The next action is the
user's archive decision for this V12 change. Archiving does not execute
V12-X01/X02, merge unattained requirements, or manufacture a success
declaration; retain the `source_partition_blocked` terminal state and the v2
three-artifact prepare package. The alternative is fresh-acquisition
feasibility/planning, but only if the user explicitly wants to continue the
real canary and opens a new OpenSpec change. Do not start V13 or decoder work
before that acquisition-planning boundary.
2026-08-14 supersession: the user explicitly changed this successor decision
to V13 retrospective diagnostics planning first; the V12 fresh-canary identity
boundary itself remains unchanged.

Claim boundary remains strict: no finite decoder correction, FER,
qualification, or promotion was established.

---

## Previous Task — Nonbinary V11 spatially coupled DE gate: PLAN FROZEN (2026-08-06)

The new planning change is
`openspec/changes/formal-nonbinary-ldpc-v11-sc-de-gate/`. Literature review,
equal-rate control, reference-reproduction gates, three frozen coupling
geometries, resource limits, acceptance IDs, and the finite-length successor
boundary are documented. This turn authorizes documentation only: V11-P04
independent freeze review is next, and no implementation or scientific
execution is authorized yet.

Detailed plan: `docs/nonbinary-ldpc-v11-sc-de-plan.md`.

Next step: perform an independent read-only review of V11-A01..V11-A16. If
accepted, implement only the QSC SMP reference and full-vector coupled MC-DE
engineering/reference phase. Do not build a finite code or decoder under V11.

---

## Previous Task — Nonbinary V10 DE-PEG-FFT-QSPA: failed_ensemble (2026-08-06)

The active OpenSpec change is
`openspec/changes/formal-nonbinary-ldpc-v10-de-peg-fftqspa/`. V10 is
TERMINATED with final state **failed_ensemble**: the V10A GF(1024)
four-search density-evolution ensemble gate failed (hard stop V10-S02).
V10-30 (PEG), V10-40 (FFT-QSPA), V10-50 (canary), and V10-60 (development)
are all HALTED. There is no "closest to gate", no rerun, and no tuning.
The successor is a brand-new V11 NB-SC-LDPC OpenSpec change (fresh
everything), pending user decision to start it.

Gate results:
- V10-0 q=4 reference-recovery gate: PASS (conservative 0.06414,
  |δ| = 0.00486 ≤ 0.012; main-thread accepted 2026-08-05).
- S1 (p=.20, f=1.15): conservative 0.2153 < 0.22 → FAIL.
- S2 (p=.20, f=1.08): conservative 0.1984 < 0.215 → FAIL.
- S3 (p=.30, f=1.15): conservative 0.3166 < 0.32 → FAIL.
- S4 (p=.30, f=1.08): no eligible candidate → FAIL.

Key evidence (all under the change's `evidence/`):
- `v10_gate_decision.json` — final gate decision (schema
  `v10_gate_decision_v1`, `final_state=failed_ensemble`)
- `v10a_execute_results.json` — official V10A execute results
- `v10a_replay_evidence.json` — replay evidence (first attempt interrupted
  PID 21032; `replay_attempt2/` completed 04:36–07:07Z; 129-file direct
  byte comparison PASS, scientific files byte-identical, provenance-only
  normalization diffs)
- `v10a_gate_decision.json` — per-search gate decisions
- `v10_t3_regression.json` — git baseline PASS, frozen directories zero
  change
- `v10_protocol_amendment_no_hash_v1.json` — 2026-08-06 no-hash amendment

2026-08-06 protocol amendment (main-thread): defensive SHA-256/checksum/
integrity-manifest mechanisms (plan-bound digest, manifest self/source
hash, per-file compare sha256) removed per AGENTS.md §5.7; replacements
are git baseline checks, direct byte comparison, structured field
validation, and semantic recomputation. `v10_seed` is retained as a
deterministic RNG derivation primitive (DE population initialization and
mutation RNG streams depend on it; completed results depend on its byte
reproduction).

Close-out (2026-08-06): S4 delta correction recorded in
`evidence/v10_s4_delta_correction.json` (correct semantics null; evidence
untouched, script fixed); independent reviewer-go final review ACCEPT
(`evidence/v10_independent_review_acceptance.json`, 89 tests pass).

Archived (2026-08-06): moved to
`openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
(archive-move commit `921d0020f5fea9bc4452c17453365e2a1a7683f4`, local, not
pushed; delta specs not merged).

Next step: the user decides whether to start the new V11 NB-SC-LDPC
change. Nothing further is authorized under V10.

---

## Previous Task — Nonbinary V9A GF(1024) Long-Block IR STOP (2026-08-04)

The active OpenSpec change is
`openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/`. V9A ensemble
optimization executed once (pid 5084, 3968.5 s, peak RSS 428.3 MiB) and was
strict-replayed once (pid 29340, 4838.5 s). All four frozen searches recorded
zero eligible candidates; every gate FAILS. The change is frozen STOP before
any finite codebook. V9B/V9C are unreachable.

Key evidence:
- `evidence/v9a_plan_v2.json` — frozen v2 budget protocol
- `evidence/v9a_execute_results.json` — official execute results (restored from
  `workspace/v9a_04c9e7d25d7145659685415084d6fac7/v2_execute/` after the replay
  overwrote the shared evidence path)
- `evidence/v9a_replay_evidence.json` — replay confirmation (scientific files
  byte-identical; run_meta differs only in provenance)
- `evidence/v9a_gate_decision.json` — STOP decision
- `evidence/v9a_interrupted_trial_freeze.json` — v1-protocol interrupted trial
- `evidence/v9a_interrupted_v2_attempt_freeze.json` — v2-protocol attempt B
  interruption freeze

Close-out complete (2026-08-04): independent reviewer-go ACCEPT, SHA256
verification (9/11 byte-identical; 2 provenance-only diffs), acceptance
record `evidence/v9a_independent_review_acceptance.json`.

Archived (2026-08-05):
`openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/`.
Delta spec NOT synced to main specs (per user choice — unattained V9B/V9C
requirements must not become canonical spec). No codebook, decoder, canary,
development, qualification, real/N4 data, promotion, or formal comparison was
produced or is authorized under this change.

---

## Current Task (historical)

The active implementation change is
`openspec/changes/implement-formal-nonbinary-ldpc/`. Its N0 deterministic
GF(2^m) backend/preflight, N1 structural codebook, and N2 bounded FFT-QSPA
feasibility/accounting slices are complete.

## Scope

- Keep agent rules centralized in `AGENTS.md`
- Keep durable decisions in `docs/decision-log.md`
- Keep reusable failures and fixes in `docs/troubleshooting.md`
- Use `openspec/` for any substantial change
- Use `docs/openspec-phase0-reconciliation-20260725.md` as the current
  evidence/archival matrix for the five historical changes that remain active.
- Use the archived final selection record at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/` and its
  merged canonical spec before interpreting the bounded result.
- Use `openspec/changes/implement-formal-cascade-and-ldpc/` before changing
  comparison behavior: it upgrades only formal Cascade/LDPC candidates, not
  Polar or a three-method ranking.

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked
- If a request changes behavior, architecture, prompt rules, tool semantics, or workflow rules, create/update an OpenSpec change first

## Current Status

- `final-ir-method-selection` is archived; its merged canonical spec is
  `openspec/specs/final-ir-method-selection/spec.md`.
- The five historical IR changes have implementation/report artifacts, but all
  remain active because their Phase-0 evidence gaps are unresolved. See the
  reconciliation matrix for change-specific blockers.
- Cascade-lite remains the preferred executable non-Polar candidate;
  Layered LDPC remains a control baseline; qLDPC remains reference-only.
- Historical Polar imports are not frame-identical confirmation evidence.
- Phase 2 is locked at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`:
  d=1024, frame length 64, dataset raw SER [0.20, 0.30), with 60 tuning and
  60 confirmation frames from group-disjoint dataset IDs. Source and split
  hashes verify through `lock_final_ir_data --verify`.
- The original Phase-3 files in `20260725_v1/` are excluded from every
  decision; `invalid_run_notice.json` records the non-reviewed tuning grid.
  The Phase-2 lock files in that directory remain authoritative and read-only.
- The authoritative Phase-3 evidence is additive `20260725_v2/`, which uses
  the v1 lock manifest and exact same frames. It froze Cascade `[12,6,24,13]`,
  4 passes, seeded-random gray and LDPC parity 1.0, 50 iterations,
  bsc-estimated/uniform gray before confirmation. Confirmation retained all
  60 attempts per candidate: Cascade 60 verified successes; LDPC 59.
- Phase 4 audit is authoritative at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`; v3 is superseded by its additive notice after a generic decision-branch repair.
  It verifies the 60 identical locked confirmation keys, frozen corrected-grid configurations, retained statuses and aggregate denominators, and recorded lock hashes. The exact two-sided paired p-value is 1.0 for the single Cascade-only success, so the required decision is `no_decision`, not a winner. Leakage remains method-specific and unranked. The non-numerical Route A field gate fails because the comparison schema lacks the documented universal-hash proof-interface fields.

## Next Step

Phase 5 code/doc hardening is complete: the data-lock selection unit test is
file-free, the authoritative lock and v4 audit have read-only verification
commands, and the Phase-3 runner requires a new output directory and records
its immutable pre-run plan before tuning. `python -m py_compile` passed for
the five new modules; focused unittest passed 7/7; and safe comparison pytest
passed 22/22 with `test_evidence_package.py` excluded because it still uses a
fixed tracked path. The external basetemp tore down normally in this pass.

The final completion audit and archive are complete for
`final-ir-method-selection`. Do not infer a winner: the authoritative v4 audit
remains `no_decision` at p=1 with a failing non-numerical Route A gate. Keep
the five historical IR changes active until their own written evidence gaps are
closed through separate work.

## Next Step

Formal shared-core Phases 1--2 are implemented in
`comparison_bench/src/comparison_bench/formal_ir/`: six-artifact/status
validation, pinned-LDPC fail-closed preflight, 64-pair provenance validation,
locked-seed Toeplitz verification, and canonical secrecy-checked transcripts.
`test_formal_verification.py` and `test_cascade_formal.py` passed 11/11;
no qualification outputs were created. Phase 3 now provides additive,
protocol-faithful `cascade_formal_v1` with fixed passes, cached look-back,
resource caps, locked Toeplitz verification, and secrecy-checked public
events. Next implement codebook-backed `ldpc_formal_v1`, then independent
synthetic and locked real-frame qualification. Existing lite results stay lite;
Polar and formal three-method comparison require a later change.

The reviewed OpenSpec now freezes the exact Toeplitz convention and locked
per-frame seeds; Cascade FIFO/re-entry state machine and caps; 64-symbol,
four-rate deterministic LDPC codebooks and pinned `ldpc==2.4.1` parameters;
calibration-only `p_hat`; six-artifact/status/provenance contracts; and exact
synthetic plus fresh `bw100`/`bw120` real promotion gates. The shared Phase
1--2 task items are checked; algorithm and qualification tasks remain open. A
method may finish as `non_promoted`, but lite cannot
substitute for it in a future formal Polar comparison.

Phase 4 is complete. `ldpc_formal_v1` now has deterministic manifest-backed
four-rate codebooks, sacrificed-calibration-only frozen `p_hat`/rate selection,
MSB-first syndrome reconciliation, the exact pinned serial BpOsd configuration,
syndrome consistency, locked Toeplitz verification, transcript-safe disclosure
accounting, and fail-closed status handling without fallback. The revised
constructor probe succeeds on installed `ldpc==2.4.1`; a real-backend
single-error frame completed as `verified_success`. Calibration provenance now
hashes the source plus dataset, ordered unique sacrificed frame keys, mapping,
and dimension; confirmation recomputes that hash and validates every per-plane
count, `p_hat`, and selected rate. The public runner exposes no decoder or
preflight test seam. Focused formal tests passed 18/18 and the safe comparison
suite excluding fixed-path `test_evidence_package.py` passed 40/40 with the
TemporaryDirectory-backed 40-codebook test enabled outside the Windows sandbox.
No qualification output had been generated at Phase-4 completion.

Formal synthetic v1 remains excluded as a partial pre-execution run. Synthetic
v2 is now also non-authoritative diagnostics: its declared Alice seed
`2026072501` and frame-order seed `2026072531` were unused, while undeclared
Alice seeds `2026072502..2505` generated its batches. Its observed Cascade/LDPC
counts therefore confer no promotion. Phase 5 checkboxes are reopened.

Formal synthetic Phase 5 is complete at additive
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
The immutable v3 package verified read-only with 128 outcomes: Cascade passed
both strata (32/32 at p=.01 and 32/32 at p=.02) and is synthetically
promoted; LDPC recorded 29/32 and 14/32 respectively and is synthetically
`non_promoted`. All 21 retained failures were `verify_failed`; there were no
unclassified/internal/provenance/accounting failures. This does not authorize
retuning, lite substitution, real qualification, Polar adaptation, or a
three-method ranking. Phase 6 remains the next gated work.

## Formal IR Phase 6--7 Verified Status

Phase 6 is complete for the only eligible real method. The invalid real v1
lock received only additive `invalid_lock_notice.json` (SHA256
`9f9d72f6c1e39467f08b86a514851b78a8aaf6a8ef2fb1f869b22f60e980d556`);
its original plan
`3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`
and lock
`aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
remain unchanged, with zero formal method calls.

The unique real v2 Cascade package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`
contains exactly seven top-level artifacts and passes its strict read-only
verifier. Its SHA256 chain is: plan
`ef0c496d4679c8a790fa6715fca010c65bbe80dbcc9fb1a640139750e8f87161`,
lock `fea6d1e9912415c37f78393ef7d5e5e9bae156531bc9e6bd9a07936c41a09348`,
outcomes `d3ef26555e19fa58d74e40ccc9dc253e27db058a1b79720e77ab265f652c01f0`,
transcript `f95478b529f13871846400395d97b9d8a4f1948ddd30859a16dd7f66074a34c8`,
codebook manifest
`e8fbbd2ca195c8aa6d4a2ca8c821c2f8bb0eb73e6830ac85fff4558ef329738c`,
run manifest
`42d18066cc13740fd4367430b0319020ec4b943e5c01bf43f4df0759257ce172`,
and report
`750aaebf4919aa9a66383e6e4bf2d441efd718324ebca564157e6607d2b21e1b`.
The exact preflight passed 29 tests with exit 0 and output hash
`8760383422fb96ce6b8d644333e52064287e394f2827f57459bc110ded0a7a7c`.
All 60 requested frames were attempted, denominator-included, independently
verified, and `verified_success`; the verification union bound is
`3.2526065174565133e-18`, with zero unclassified/internal/provenance/accounting
failures. `cascade_formal_v1` is therefore promoted only for the locked real
domain `d=1024`, 64 symbols, bw120, frame SER `[0.20,0.30)`.

Synthetic v3 still promotes Cascade at 32/32 in both strata. LDPC remains
synthetically non-promoted at 29/32 and 14/32 and was not run on real data.
Phase 7 read-only verification passed for synthetic v3 and real v2; the safe
non-formal regression passed 22/22 in 0.66 s; `git diff --check` exited 0
apart from known ACL/LF warnings; frozen `src/`, `experiments/`, `tools/`, and
`results/` diffs were empty; and the independent audit result was PASS.

The active change is technically ready for archive review but is not archived.
Memory triage and the actual archive action remain pending.

## Next Step

Create a new LDPC-improvement OpenSpec change. LDPC must earn fresh synthetic
and real promotion before any frame-identical Polar/Cascade/LDPC comparison is
created. Do not substitute a lite method or tune on confirmation data.

## Archive Complete

`implement-formal-cascade-and-ldpc` is archived at
`openspec/changes/archive/2026-07-25-implement-formal-cascade-and-ldpc/`.
Its canonical merged specification is
`openspec/specs/formal-ir-methods/spec.md`. Final method state:
`cascade_formal_v1` is promoted by synthetic v3 and the bounded real v2
qualification; `ldpc_formal_v1` is synthetically `non_promoted` and had no
real run.

The next change must be a new LDPC-improvement OpenSpec change; it has not yet
been created. Do not begin a direct frame-identical Polar/Cascade/LDPC
comparison until LDPC earns fresh synthetic and real promotion.

## Nonbinary LDPC N0 Status (2026-07-26)

`nbldpc_formal_v1` now has a deterministic internal polynomial-basis GF(2^m)
contract for q=2 through q=1024, canonical field IDs, strict integer symbol
validation, and a read-only fail-closed preflight. Unsupported q returns
`unsupported_domain`; an expected field-ID mismatch returns
`backend_unavailable`; no external backend, decoder, or lower-q fallback is
used. Focused nonbinary plus existing qLDPC-reference tests passed 15/15, and
the selected formal/qLDPC regression passed 22/22.

N1 now adds one deterministic n=64, 32-row mother matrix with exact 16/24/32
prefix codebooks, pinned GF(q) rank, canonical bytes, golden codebook/manifest
hashes, and reconstruction-based fail-closed verification. Focused tests pass
22/22 and the selected formal/nonbinary/qLDPC regression passes 29/29.

N2 now adds a truth-isolated full-message FFT-QSPA decoder, q-ary symmetric
priors, GF(q) coset syndrome semantics, bounded q=1024 execution, MSB-first
mapping, locked Toeplitz wrapper, and exact syndrome/tag/public-control
accounting. N0-N2 plus qLDPC tests pass 35/35; selected formal regressions pass
17 with 2 skipped.

This is bounded engineering feasibility only. It proves no general
correction, FER/performance, calibration, synthetic/real qualification,
promotion, output, production readiness, or comparison eligibility. The next
task is planner-owned N3 pre-registration: freeze development/confirmation
data and separation, claim domain, one global policy, metrics/gates, resource
and stop rules, additive artifacts, invalid-run handling, and a strict
read-only verifier. Do not generate data or execute qualification yet.

# Nonbinary N3 outcome (2026-07-26)

`nbldpc_formal_v1` N3 is complete as an immutable **non-promoted** synthetic
package. N4 real-data work, confirmation tuning, and reruns are forbidden.
Official strict verification is failed/unverifiable because whole-worktree git
status drifted after execution; diagnostic replay is not a substitute.

## Nonbinary v2 Final Outcome (2026-07-26)

The successor package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
was planned once, executed once, and strictly replay-verified. The verifier
returned `verified=True`, `run_status=non_promoted_development`,
`promoted=False`.

The selected tempered+damped QC48 policy (margin 8, max_iter 10, checks 32/40)
achieved only 0/24 at p=.20 and 5/24 at p=.30 versus the frozen 22/24
development-readiness floor. Confirmation was therefore not generated or
executed. Stop: no rerun, confirmation tuning, N4, sidecar access, `.ttbin`
processing, FER claim, or real-data claim.

## Nonbinary v3 Final Outcome (2026-07-30)

The covered-layered successor is complete at
`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic/`.
Its plan, execute, and strict read-only replay each ran exactly once. The
selected layered-l075 margin-8 policy passed development readiness at 23/24
for p=.20 and 24/24 for p=.30. Sealed confirmation achieved 32/32 and 30/32,
with zero prohibited failures, but the frozen gate required 31/32 in both
strata. The verifier returned `verified=True`, `run_status=completed`,
`promoted=False`.

This task ends at immutable synthetic non-promotion. Do not rerun or tune it.
N4, sidecar access, and real `.ttbin` processing remain forbidden until a
successor earns fresh synthetic promotion and a new OpenSpec change is
approved.

## Nonbinary v4 IR Final Outcome (2026-07-31)

`formal-nonbinary-ldpc-v4-incremental-redundancy` completed its one authorized
synthetic run at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
The sole strict replay returned `verified=True`, `run_status=completed`, and
`promoted=False`.

Development selected warm incremental redundancy at 64/64 for p=.20 and 63/64
for p=.30. Confirmation was 128/128 and 120/128, respectively, with eight
retained p=.30 `decode_failed` rows and zero prohibited failures. The terminal
gate is therefore A3. Do not rerun, tune, build N4, access sidecars, or process
real `.ttbin`.

The next permissible work is planner-only exploration of a fresh synthetic
successor. It must use new roots and freeze its code/rate/decoder change before
new development data; the current confirmation rows may diagnose the route but
must not be used as tuning data.

## NBLDPC v5 Routes A and B Final Outcomes (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Routes A and B, each
planned once and executed once (512 outcomes each, `run_status=completed`,
readiness true, `promoted=False`).

- Route A `20260731_v5a_nbldpc_multistage_synthetic`: p=.20 128/128, p=.30
  127/128 (one tail miss).
- Route B `20260731_v5b_nbldpc_mother_synthetic`: NBLDPC5B mother with zero
  w2/w3 syndrome collisions; p=.20 128/128, p=.30 127/128 (one tail miss).
- Both strict read-only replay attempts were blocked by external-session git
  HEAD drift after plan creation (`71bda20d`→`3a5d96a` for A,
  `3a5d96a`→`4dd6b7e` for B); source/CLI/contract hashes all still match. See
  the two 2026-08-01 decision-log entries.

Both packages are immutable non-promotion evidence; no rerun or confirmation
tuning is authorized. Route C was next (codebook identity fixed to NBLDPC5B,
roots 202607800000-202607830000, run ID
`20260731_v5c_nbldpc_decoder_synthetic`) and has completed; see the Route C
section below.

## NBLDPC v5 Route C Final Outcome (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route C once:
`20260731_v5c_nbldpc_decoder_synthetic` (NBLDPC5B codebook identity, dual
policies `nbldpc_v5c_sched` / `nbldpc_v5c_ems`, roots
202607800000-202607830000), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained tail miss) —
  the same p=.30 tail pattern as Routes A and B.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` was unchanged by the replay.

The Route C package is immutable non-promotion evidence; no rerun or
confirmation tuning is authorized. Route D is next
(`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-202607870000,
list stage L=2 + one ADMM run per task 1.6; implementation starts at
task 7.1).

## NBLDPC v5 Route D Final Outcome (2026-08-02)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route D once:
`20260731_v5d_nbldpc_post_synthetic` (NBLDPC5B via v5c delegation, dual
policies `nbldpc_v5d_sched_post` / `nbldpc_v5d_ems_post`, list L=2 x top-8
+ ADMM rho=1.0 post-processing), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained
  confirmation-frame `decode_failed`) — the same p=.30 tail pattern as
  Routes A, B, C.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` unchanged.
- Implementation corrections recorded: x-update prior sign and per-bit
  parity-relaxation z-projection (q=4 brute-force verified; see
  decision-log 2026-08-02 and module docstring).

With all four routes non-promoted, the v5 multistage change **terminates**
per task 7.4 with four immutable non-promoted packages
(20260731_v5a/v5b/v5c/v5d_nbldpc_*_synthetic). No rerun, tuning, N4,
sidecar, `.ttbin`, real-data, or comparison claim is authorized. A
successor must be a new OpenSpec change with fresh development and
confirmation data.

## Nonbinary v6 Long-Block Outcome (2026-08-02)

Change `formal-nonbinary-ldpc-v6-long-block` built the GF(1024) n=1024
degree-2 PEG engineering candidate (codebooks (1024,320)/(1024,480), layered
FFT-QSPA 50 iterations, lambda .75), accepted engineering (T0 16/T1 38/T2 6/
T3 51), then ran a sacrificed 4+4 canary once + strict replay once: 0/4 + 0/4
verified success, all 8 `decode_failed` at max_iter=50. Gate fires:
long-block baseline stopped, n=4096 NOT taken, successor = multiplicative
repetition (2,3) mother code. Evidence under
`openspec/changes/formal-nonbinary-ldpc-v6-long-block/evidence/`; canary
package at `workspace/nbldpc_v6_canary_b01c42a5dee14ed0913e78d60944cc38/canary_plan`.

## Nonbinary v7 Successor Ladder (2026-08-02)

Change `formal-nonbinary-ldpc-v7-successor-ladder` runs the pre-registered
route ladder R1A -> R1B -> R2 -> R3 (canary 4+4 -> 0/4 freeze and advance;
else 16+16 -> readiness gate >=15/16, <=8.75 bits/symbol, median <=120 s/frame).

- **R1A** `(2,3)` mother n=256 m=170: engineering accepted; canary 0/4 + 0/4
  -> `failed_canary`, frozen.
- **R1B** one multiplicative repetition (rate 1/6): engineering accepted;
  canary p=.20 3/4, p=.30 0/4 -> `failed_canary` (p=.30 tail), frozen.
- **R2** QSC density-evolution ensemble (n=1024, 321/458 checks, DE validated
  against published BSC/BEC vectors): engineering accepted; canary 0/4 + 0/4
  -> `failed_canary`, frozen.
- **R3** GF(32)xGF(32) multilevel (EMS nm=32): engineering accepted (T0 19/
  T1 105/T2 33/T3 179, 10/10 independent review PASS); canary 0/4 + 0/4 ->
  `failed_canary` (executed once 668.8 s, strict-replayed once 663.4 s, 8/8
  decode_failed at max_iter=100, verification never invoked), frozen.

**LADDER EXHAUSTED (2026-08-04)**: all four routes R1A/R1B/R2/R3 ended
`failed_canary`; no route reached development-ready. Closeout report frozen at
`evidence/v7_ladder_report.md` (V7-40 complete): first-ready route NONE,
`ladder_exhausted` TRUE, every failed artifact retained, no official
`formal_ir_methods` v7 output root, no rerun/tuning/confirmation/real data,
disclosure ceilings and forbidden-status scans clean across all routes. No
fourth route is invented.

All v7 packages are immutable under `workspace/nbldpc_v7_*`; no official
`formal_ir_methods` v7 output exists; evidence under
`openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/`;
decision-log entries 2026-08-02 for R1A/R1B/R2 non-promotion and 2026-08-04
for R3 non-promotion + ladder_exhausted + closeout.

## Next Step

The v7 successor ladder is closed (`ladder_exhausted`). Any successor must be
a **NEW OpenSpec change** with fresh development and confirmation data, new
roots, and its code/rate/decoder change frozen before new development data;
current canary/confirmation rows are not tuning data. Remaining v7 closeout:
V7-41 independent acceptance and project-memory triage, V7-42 finalize
without inventing a fourth route. Qualification/promotion/comparison claims
remain unauthorized.

## Nonbinary V8 Reference Reproduction — V8-60 Audit-Correction Close-out (2026-08-04)

- Change: `formal-nonbinary-ldpc-v8-reference-reproduction`.
- Status: implemented, then corrected by V8-60 (non-tuning formula correction
  from an independent audit), corrective reference run executed once, and
  INDEPENDENTLY REVIEWED ACCEPTED (reviewer-go, read-only, 2026-08-04) at HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`. V8-A01..V8-A11 pass; V8-A12
  resolved pass by the V8-60 independent review (operator did not self-accept).
- Scope: additive only — 3 modules + 3 tests + 12 evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/`:
  error-domain contract (`nonbinary_v8_error_domain.py`), independent
  probability-domain oracle (`nonbinary_v8_reference.py`, GF2mField-only
  import boundary), and full-vector QSC MC-DE (`nonbinary_v8_mcde.py`); see
  decision-log 2026-08-04.
- V8-60 correction (not tuning): `concentrated_check_distribution` previously
  matched the two-point MEAN check degree (`w_lo = dc_hi - dc_mean`), which
  only approximates the edge-perspective rate condition
  `sum_j rho_j/j = (1-R)*sum_i lambda_i/i` (relative error ~1e-4); corrected
  to solve it exactly for adjacent check degrees `{floor(dc), ceil(dc)}` with
  `w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`,
  `target = (1-R)*integral_lambda`, `dc = 1/target` (integer `dc` degenerates
  to the regular degree); new helper `reconstructed_rate(lambda_edge, rho_edge)`;
  tests assert `|reconstructed_rate - rate| <= 1e-12` (5 configs). Citation
  first author corrected "Rasmus T. Müller" -> "Ronny Müller"
  (arXiv:2307.02225v2 author list). Invalid tolerance arithmetic
  `0.005+0.003+0.0025=0.015` replaced by 0.0005 + 0.00125 + 0.005 + 0.005 =
  0.01175 <= 0.012; frozen tolerance 0.012.
- Corrective reference run (exactly once, frozen before run): q=4, R=0.75,
  Muller et al. 2024 Table 1 row 0.75 (DET published 0.069), concentrated rho
  {24: 0.6623423944, 25: 0.3376576056} (dc_mean 24.3285893 unchanged),
  n_samples 100000, max_iter 150 (the paper's own MC-DE budget), seed
  2026080418, p in [0.01,0.12] step 0.0025, entropy < 0.01 base-q for 20
  consecutive iterations: threshold_proxy 0.062421875, delta 0.006578125 <=
  0.012 -> PASS; full trace in `evidence/v8_reproduction_trace_corrected.json`.
  No rerun, no tuning.
- History preserved: `evidence/v8_reproduction_trace.json` byte-identical
  (SHA256 `dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3`)
  + `v8_reproduction_trace_precorrection_annotation.json`;
  `v8_engineering_acceptance.json` NOT rewritten (A12=blocked resolved by
  `v8_acceptance_closeout_addendum.json`); provenance/extract/audit/recommend
  files unchanged. q=4 golden re-recorded under corrected rho {4: 1/6, 5: 5/6}
  (recording, not tuning); old-R2 tamper modes still differ; q=8 golden
  byte-identical (regular {6:1.0}).
- Tiers (V8-60.8, no T3): compile exit 0; T0 17/0, T1 32/0, T2 4/0
  (reproduction-trace + source-manifest + no-production-runner +
  precorrection-preservation, all read-only); reviewer-go re-ran T1 32/0 and
  T2 4/0: identical.
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real/N4/comparison execution; frozen
  `src/`/`experiments/`/`tools/`/`results/` and all V1-V7 files unchanged
  (git status/diff empty); nothing staged.
- Boundary: V8 is engineering/reference-only; no FER, readiness, qualification,
  promotion, or comparison claim is made from V8.
- Next: nothing remains for V8 except the V8-60.11 memory-agent close-out
  (AGENT_PROJECT_MEMORY.md section 39 pending). V9 is a separate future OpenSpec
  change (paper-faithful syndrome reconciliation with the reproduced ensemble
  and blind puncturing/shortening, fresh roots); NOT implemented.

## Active: Nonbinary V9 GF(1024) Long-Block IR (2026-08-04)

- Change: `formal-nonbinary-ldpc-v9-gf1024-long-ir`.
- Next task: V9-00 freeze/audit, then V9A scalable full-vector GF(1024) MC-DE.
- Route is autonomously gated through V9B n=4096 and V9C n=16384/n=32768;
  first failed robust/canary/development gate freezes and stops without tuning.
- V9C authorizes bounded synthetic canary and 16+16 development only. No
  qualification, confirmation, real/N4, promotion, or formal comparison.
- Operator packet:
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/opencode-autonomous-packet.md`.
- Freeze-review corrections are incorporated: target .215/.32 gates; one V9A
  plan/execute/replay; 4/16/32 constituent provenance; `rank(H)=m`; n=32768
  canary 24h hard timeout and <=16h median; fixed-rate syndrome/tag only.
  Blind adaptation is prohibited in V9 and deferred to V10.

## Current progress — Route A complete, Route B M1 running (2026-08-16)

- Route A prior-calibration probe: Oracle 128/128 fail, p-grid 40/40 fail.
- Conclusion: failures not iteration-limited and not QSC prior-limited; likely structured-channel or code/graph limitation.
- Route B M0 complete (V18-B1 q4/q8 smoke passed).
- Route B M1 production q=4 DE reproduction running in background (workspace/nbldpc_v18_b1_exec_q4).

## 当前自动执行终点

- V18-B1 M1 生产复现：NO_THRESHOLD / FAIL，eligible_candidates=0，best 未收敛。
- 按 no-rerun/no-tuning 纪律，Route B M2 不自动启动。
- Route C/D 依赖科学路线或用户决策；当前无进一步自动步骤。
- 下一步需用户决定：是否开新 change 调整 DE 预算/参数，或转向其他路线。
