# Tasks: cascade-beta-optimal-path — FINAL_GATE 执行清单

> 唯一验收：`FINAL_GATE.md`。本清单供 `coder-fast` 直接执行；旧 T2–T4 的 90 点/Pareto 任务已作废。只产出 markdown + 最小 CSV/JSON，不写生产加固。

## T0 — 冻结与一致性（0.5 天）

- [ ] 确认 `proposal.md` / `design.md` / `FINAL_GATE.md` / `specs/cascade-optimal-path/spec.md` 四文件一致（网格 12–18 点、FIFO 完整、b=4/8/16、passes 6–8、BER 1%/9.4%、报告口径、位面相关性、held-out 三条件、RETIRE 语义）
- [ ] 冻结 `comparison_bench/configs/cascade_final_gate.yaml`（网格笛卡尔积、seeds、`p_i` 占位、caps 5s/100k、held-out 身份占位）
- [ ] `py_compile` 通过（若新增最小脚本）

**验收**：`rg "90点|Pareto|24点" openspec/changes/cascade-beta-optimal-path/` 仅出现在"已作废"声明中；四文件阈值与公式一致

## T1 — 公式与口径单测（T0 级，必过）

- [ ] 实现/复用 `h2(p)`, `L_min = 640*h2(BER)`, `β_accepted = L_min/leak_accepted_mean`, `yield_effective` 的纯函数（≤30 行，无依赖抽象）
- [ ] 单测：`h2(0.01)=0.08079..., h2(0.094)=0.444...` 误差 <1e-9；`β` 仅 accepted 帧、失败帧隔离；`undetected` 不并入 success；`yield` 零失败时退化正确
- [ ] `pytest -p no:cacheprovider` 通过（`workspace/cascade_final_gate/<uuid>` 临时根，禁止写生产输出）

**验收**：`pytest` 输出 `passed`；`rg "beta.*failed|leak.*average.*all"` 确认无全帧平均 β 口径

## T2 — 合成 IID 小网格 12–18 点（必测）

- [ ] 实现最小 Cascade 执行器封装（复用 `cascade_formal_v1`，仅暴露 `b0∈{4,8,16}, passes∈{6,7,8}, fifo=full`）
- [ ] 执行 IID 网格：`BER 0.01, 0.094 × b0 4/8/16 × passes 6/8` 必测 12 点（有资源则 6/7/8 全 18 点），每点 ≥200 帧（推荐 320）
- [ ] 每点输出 `FER, leak_*_accepted, leak_failed_mean(诊断), β_accepted, yield_effective, undetected` 分信道行
- [ ] 产物：`final_gate_grid_results.csv`（列冻结见 FINAL_GATE §2）+ `final_gate_manifest.json`（seeds, h2, L_min, code/exec SHA）

**验收**：CSV 行数 = 12 或 18 ×2 信道独立（不可合并）；`b=4/8` + `fifo=full` + `passes≥6` 全覆盖；`undetected` 列存在

## T3 — 位面相关性复现网格（必做对照）

- [ ] 从真实 ttbin 冻结训练分片估计 `p_i = P(flip|plane=i) i=0..9`（pooled 或 per-source，冻结其一并双列披露）
- [ ] 同网格参数（12–18 点）用 `p_i` 生成合成帧（plane 内 IID，plane 间非 IID），执行 Cascade
- [ ] 并列输出 `final_gate_plane_correlation_results.csv`（同构 T2），披露 `p_i` 向量与 `L_min` 计算口径（`mean(p_i)` 等效 BER 或 `Σ h2(p_i)*n_i` 精确值）
- [ ] 在报告中对比 IID vs 位面相关性：若 IID PASS 但位面相关性 FAIL，则判定以位面相关性为准

**验收**：`p_i` 向量已写入 `final_gate_manifest.json`；`rg "p_i|plane" final_gate_manifest.json` 命中；两 CSV 同构可直接 diff

## T4 — held-out 独立判决（PASS/RETIRE 一锤定音）

- [ ] 冻结独立 held-out 分片（优先真实 ttbin held-out；否则位面相关性合成 held-out，需声明类型与来源，与 T2/T3 训练/调试数据零重叠，seeds 独立）
- [ ] 在 held-out 上评估（选最优网格点或全网格披露选优语义），统计双信道各自 `FER, β_accepted, undetected`
- [ ] 生成 `final_gate_heldout_verdict.json`：`{ber_0.01: {fer, beta, undetected, pass}, ber_0.094: {...}, verdict: PASS|RETIRE}`
- [ ] 生成 `FINAL_GATE_REPORT.md`：分信道 FER/β/yield 表 + 三条件逐项判定 + 总判决陈述（PASS 需双信道同时满足）

**验收**：同时满足 `FER<0.05 & β>0.9 & undetected==0` 双信道方为 PASS；否则 RETIRE；`undetected==0` 单列校验通过；held-out 独立性在 manifest 中可追溯

## T5 — 退休归档与门禁（T3 级收尾）

- [ ] 若 `RETIRE`：在 `FINAL_GATE_REPORT.md` 与 `final_gate_heldout_verdict.json` 中明确"正式退休 binary Cascade 主路线"，列出 `b=4/8` + 完整 FIFO 仍失败的证据行
- [ ] 更新 `docs/decision-log.md`（新增条目：FINAL_GATE 判决、网格、阈值、RETIRE/PASS 结论、后续主路线建议）
- [ ] 更新 `AGENT_PROJECT_MEMORY.md`（如有 durable 结论：位面相关性是否颠覆 IID 结论）
- [ ] pre-RESULT 独立复核：阈值/分解一致性/undetected 隔离/分信道披露/held-out 独立性对照实际产物，FAIL 则返工，不先发布后补审
- [ ] `git status --short` 校验：仅本 change 下 markdown/yaml/csv/json 变更，无 `src/`/`results/` 覆盖

**验收**：`decision-log.md` 已追加；`git diff --stat` 无冻结基线改动；`comparison_bench/outputs_comparison/cascade_beta_final_gate/run_01/` 为 append-only 新目录

---

## 执行顺序与 stop 规则

1. 顺序：T0 → T1 → T2 → T3 → T4 → T5；T2/T3 可并行
2. 任一步骤发现 `undetected>0` 或 `FER≥5%` 或 `β≤0.9` 在 `b=4/8` 全条件下已不可挽回，可提前进入 T5 RETIRE，但仍需完成 T4 held-out 形式判决
3. 禁止：追加扫描、放宽阈值、用失败帧 β 救场、跨信道平均；所有失败保留为证据，不重调重跑
