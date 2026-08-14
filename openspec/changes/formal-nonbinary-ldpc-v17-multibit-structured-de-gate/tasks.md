# Tasks: formal-nonbinary-ldpc-v17-multibit-structured-de-gate

Status: **PLANNING** — freeze review 未执行；ACCEPT 前禁止任何实现与执行。

## P — 规划与冻结（本对话完成）

- [ ] **P01** 冻结立项依据/文献锚点/族排名（design §1）。
- [ ] **P02** 冻结 Stage 0 机制复现门（锚点、PASS 判据，design §2）。
- [ ] **P03** 冻结多位信道模型（per-bit-plane 向量 + 联合结构，schema
  v1，design §3）。
- [ ] **P04** 冻结预注册候选（3–5 个，不搜索，design §4）与判定表。
- [ ] **P05** 冻结预算/回放/降级链（design §5）。
- [ ] **P06** 冻结产物与纪律、claim boundary（design §6、§7）。
- [ ] **P07** 独立只读 freeze review（reviewer 子代理，对 P01–P06 +
  design 全部条款）。ACCEPT 前禁止任何执行。

## I — 实现（freeze review ACCEPT 后，flash 子代理落实，主线程 review）

- [ ] **I01** Stage 0 机制模块（小 q 位面分解 DE 复现 + 锚点对照）。
- [ ] **I02** 多位信道模型模块（characterization 帧只读重算 →
  `nbldpc_v17_multibit_channel_model_v1` 持久化）。
- [ ] **I03** Stage 2 点评估模块（位面分解二元 DE / 多位边标签符号级
  DE——优先复用 V14 `nonbinary_v14_mcde.py` structured 分支，扩展为
  新增模块 `nonbinary_v17_*.py`，V8/V9/V11/V13/V14 源码零改动）。
- [ ] **I04** gate 编排 CLI：Stage 0/1/2 顺序执行、候选点收敛判定、f
  计算、`v17_gate_decision.json`（schema `nbldpc_v17_gate_decision_v1`）、
  `v17_gate_manifest.json`；execute-once + strict replay 语义；
  按文件 fail-closed（V14 教训）。
- [ ] **I05** 四层测试 T0/T1/T2/T3（T2 含 fake lifecycle + 严格回放 +
  机制等价断言；测试根为新鲜 `workspace/nbldpc_v17_<uuid>/`）。

## E — 执行（一次）

- [ ] **E01** 生产执行一次：Stage 0 → Stage 1 → Stage 2（预算内）；
  证据落 change 的 `evidence/`；strict replay 一次。
- [ ] **E02** 独立 gate review（复核判定表与数值；ACCEPT/REJECT）。

## C — 收尾

- [ ] **C01** decision-log 记录（pass → 另开有限码 candidate change
  声明；fail → 路线冻结声明，不启动 V15/V16、不扩大搜索）；
  记忆 triage；CURRENT_TASK/AGENT_HANDOFF 更新。
- [ ] **C02** 边界声明：本门无 FER/资格/效率实测结论；fresh
  acquisition（P1）独立推进不受影响。

## 冻结纪律（任何阶段适用）

- 只做可行性门：不构造有限码、无 codebook/decoder/资格输出。
- 候选集执行前冻结；禁止搜索/调参/重跑/扩大搜索。
- 产物 additive；V8/V9/V11/V13/V14 源码零改动；冻结根零改动。
- FAIL 后禁止"最接近"续行与任何 V15/V16 重启。
