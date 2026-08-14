# Tasks: formal-nonbinary-ldpc-v13-r3-fresh-acquisition

Status: **PLANNING** — freeze review 未执行；ACCEPT 前禁止 prepare /
execute / verify。

## P — 规划与冻结（本对话完成）

- [ ] **P01** 冻结数据源/acquisition/window/stratum 设置（design §1）。
- [ ] **P02** 冻结新 frame/payload identities 与排除验证（design §2；
  复用 V12 partition 身份机制）。
- [ ] **P03** 冻结角色隔离（characterization/canary/confirmation 互斥，
  design §2）。
- [ ] **P04** 冻结解码器不变式（R3 码本/先验/接口/max_iter，design §3）。
- [ ] **P05** 冻结执行规模与判定表（design §4、§6）。
- [ ] **P06** 冻结停止规则（无 eligible / 漂移 / 失败保留，design §5）。
- [ ] **P07** 独立只读 freeze review（reviewer 子代理，对 P01–P06 +
  design 全部条款 + claim boundary）。ACCEPT 前禁止任何执行。

## PREP — prepare（freeze review ACCEPT 后）

- [ ] **PREP01** 数据源检查：扫描声明的 fresh 数据路径，产出 eligible
  行清单（当前预期 zero-eligible，合法结果）。
- [ ] **PREP02** 身份台账：为 eligible 行派生 `v13r3fresh-<stratum>-<uuid>`
  身份，逐一验证不在任何历史锁中（V4/V5/V13/V12 排除集）。
- [ ] **PREP03** 角色分配（characterization/canary/confirmation）并
  冻结 plan（帧身份列表、数量、角色、种子）。
- [ ] **PREP04** 产出 prepare 包（plan + ledger；zero-eligible 时产出
  `no_eligible_frames` 包并停在本阶段）。

## R — 主线程独立 review（prepare 后）

- [ ] **R01** 主线程只读 review prepare 包：身份/排除/角色/规模/停止
  规则逐项复核；BLOCKERS 修复后 ACCEPT；review ACCEPT 前禁止 execute。

## EX — 单次 fresh execute（review ACCEPT 后，一次）

- [ ] **EX01** 按冻结 plan 对 canary 64 + confirmation 128 帧（若规模
  允许）各解码一次：unchanged `nbldpc_v13_r3_code_v1` + QSC p=.20 +
  max_iter=100；所有失败原样保留、计入分母。
- [ ] **EX02** 冻结停止规则检查：漂移阈值、身份/角色违规、forbidden
  状态扫描；任一触发 → frozen failure 包，停止。

## V — 只读 verify（execute 后，一次）

- [ ] **V01** 只读 verifier：字节级不改动、身份/角色/账目/分母/状态
  语义逐项复核；产出 verify 报告。

## C — 判定与收尾（verify 后）

- [ ] **C01** 判定：全绿 → `fresh-confirmed`；任一失败 → `frozen
  failure`；写入 decision-log + 记忆 triage + CURRENT_TASK +
  AGENT_HANDOFF。
- [ ] **C02** 边界声明：fresh-confirmed 不是 promotion/qualification；
  效率仍 f≈12；不触发 V15/V16。

## 冻结纪律（任何阶段适用）

- 失败原样保留；禁止替换帧、调参、重跑、换候选。
- 禁止修改 R3 码本/先验/迭代上限/接口。
- 产物 additive；冻结根零改动。
- prepare 为确定性工具：用户提供新数据后可重新运行（不构成对失败
  的"重跑"——它只在数据源存在时产出执行计划）。
