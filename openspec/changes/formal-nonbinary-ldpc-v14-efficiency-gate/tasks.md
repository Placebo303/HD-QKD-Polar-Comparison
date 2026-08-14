# Tasks: formal-nonbinary-ldpc-v14-efficiency-gate

Status: **FROZEN CANDIDATE** — 设计全部五节定稿（§5 依据 DE 调研子代理报告）；
V14-P06 独立 freeze review 进行中；review ACCEPT 前禁止任何执行。

## P — 规划与冻结（本对话完成）

- [x] **V14-P01** 冻结信道模型来源与光滑化规则（design §1）。
- [x] **V14-P02** 冻结码率点/候选度分布与判定式（design §2）。
- [x] **V14-P03** 冻结 Stage 0 机制回归门（design §3）。
- [x] **V14-P04** 冻结输出路径/测试根/禁止词与 claim boundary
  （design §4、§6）。
- [x] **V14-P05** DE 机制与预算定稿（design §5；依据调研子代理报告）。
- [x] **V14-P06** 独立只读 freeze review（reviewer-go，对 P01–P05）。
  （Done 2026-08-14：首轮 BLOCKERS——spec 候选集与 design 矛盾、§3 锚点
  漂移——修复后复评 **ACCEPT**，三个非阻塞词汇警告已并入本版设计。）

## I — 实现（review ACCEPT 后，subagent 落实，主线程 review）

- [ ] **V14-I01** 结构化信道模型模块：从 characterization 帧只读重算全
  1024-bin 差分直方图 + λ 光滑化 + 归一化 + `v14_structured_channel_model.json`
  持久化（schema v1）+ 折叠同态 φ_m 实现。
- [ ] **V14-I02** DE 门机制（新模块 `nonbinary_v14_mcde.py`，不改 V8/V9/
  V11 源码）：`channel_mode` 分支（qsc/structured）+ Stage 0 复现路径 +
  Stage 1 小 q 验证 + Stage 2 点评估；QSC 模式与 V9 `run_mcde` 逐字段
  等价（T2 断言）。
- [ ] **V14-I03** gate 编排：Stage 0/1/2 顺序执行、12 点收敛判定、f 计算、
  `v14_gate_decision.json`（schema `nbldpc_v14_gate_decision_v1`）、
  `v14_gate_manifest.json` 生成；execute-once + strict replay 语义；证据
  全部落 `evidence/`（无 <run_id> 子目录）。
- [ ] **V14-T0/T1/T2/T3** 四层测试（design §4 冻结清单）全过。

## E — 执行（一次）

- [ ] **V14-E01** 生产执行一次：Stage 0 复现 + Stage 1 验证 + Stage 2
  判定（预算内）；证据落 `evidence/`；strict replay 一次。
- [ ] **V14-E02** 独立 gate review（reviewer-go 复核判定表与数值）。

## C — 收尾

- [ ] **V14-C01** decision-log 记录 gate 结论（pass→V15 立项边界；
  fail→路线冻结声明）；记忆 triage。
