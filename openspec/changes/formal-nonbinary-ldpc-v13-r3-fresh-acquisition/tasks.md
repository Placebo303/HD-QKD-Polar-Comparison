# Tasks: formal-nonbinary-ldpc-v13-r3-fresh-acquisition

Status: **FROZEN — freeze review ACCEPT (2026-08-15)**。独立 reviewer
ACCEPT（零 blockers）；三个非阻塞警告已按 amendment 修复：A02 表述
精确化（bw120+bw180 各 128/128）、§4 规模不足规则（eligible<192 →
insufficient_eligible_frames）、§5 漂移阈值引用 V13 D01 参考区间。
ACCEPT 后允许 prepare；execute 需 review ACCEPT 且数据可用。

## P — 规划与冻结（本对话完成）

- [x] **P01** 冻结数据源/acquisition/window/stratum 设置（design §1）。
- [x] **P02** 冻结新 frame/payload identities 与排除验证（design §2；
  复用 V12 partition 身份机制）。
- [x] **P03** 冻结角色隔离（characterization/canary/confirmation 互斥，
  design §2）。
- [x] **P04** 冻结解码器不变式（R3 码本/先验/接口/max_iter，design §3）。
- [x] **P05** 冻结执行规模与判定表（design §4、§6）。
- [x] **P06** 冻结停止规则（无 eligible / 规模不足 / 漂移 / 失败保留，
  design §5）。
- [x] **P07** 独立只读 freeze review（reviewer 子代理，对 P01–P06 +
  design 全部条款 + claim boundary）。（Done 2026-08-15：**ACCEPT，
  零 blockers**；三个非阻塞警告按上述 amendment 修复并并入 design。）

## PREP — prepare（freeze review ACCEPT 后）

- [x] **PREP01** 数据源检查：扫描声明的 fresh 数据路径，产出 eligible
  行清单。（Done 2026-08-15：声明的数据源为空/不存在——`D:\Data`
  无 fresh 10 dB Type-II 帧数据（最新为 2026-07-28 JSI 测量，非帧
  数据）→ **eligible_row_count=0**，合法 `no_eligible_frames` 结果。）
- [x] **PREP02** 身份台账：为 eligible 行派生 `v13r3fresh-<stratum>-<uuid>`
  身份，逐一验证不在任何历史锁中（V4/V5/V13/V12 排除集）。
  （Done：零 eligible 行 → 台账为空；排除机制经 T1 测试验证。）
- [x] **PREP03** 角色分配（characterization/canary/confirmation）并
  冻结 plan（帧身份列表、数量、角色、种子）。（Done：机制实现并经
  19/19 测试；当前零行故无角色可分配——按冻结规则进入
  no_eligible_frames。）
- [x] **PREP04** 产出 prepare 包（plan + ledger；zero-eligible 时产出
  `no_eligible_frames` 包并停在本阶段）。（Done 2026-08-15 生产执行：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_prepare_20260815/no_eligible_package.json`
  ——schema `nbldpc_v13r3_fresh_no_eligible_v1`、terminal_state=
  `no_eligible_frames`、decoder 不变式完整冻结（q=1024/n=256/m=170/
  rank=170/seed 20260818/p=.20/max_iter=100/168x3+2x4）、
  failure_policy=immutable。主线程独立 review：包内容与冻结契约逐项
  一致，**ACCEPT**。）

## R — 主线程独立 review（prepare 后）

- [x] **R01** 主线程只读 review prepare 包：身份/排除/角色/规模/停止
  规则逐项复核。（Done 2026-08-15：**ACCEPT**——no_eligible_frames
  为冻结停止规则 §5.1 的合法结果；包 schema/terminal_state/不变式/
  纪律字段全部与 design 一致；无数据源 ⇒ 不重跑、不替换、不调参。）

## EX — 单次 fresh execute（review ACCEPT 后，一次）

> **状态：BLOCKED ON DATA（2026-08-15）**——prepare 产出
> `no_eligible_frames`（零 fresh 数据源）；按冻结停止规则 §5.1 冻结，
> execute/verify 不可执行。用户提供 fresh 数据（新 10 dB Type-II
> 帧配对）后，重新运行 PREP（确定性工具）→ 若 eligible≥192 →
> review → 单次 execute → 只读 verify。当前不重跑、不替换、不调参。

- [ ] **EX01** 按冻结 plan 对 canary 64 + confirmation 128 帧（若规模
  允许）各解码一次：unchanged `nbldpc_v13_r3_code_v1` + QSC p=.20 +
  max_iter=100；所有失败原样保留、计入分母。
- [ ] **EX02** 冻结停止规则检查：漂移阈值、身份/角色违规、forbidden
  状态扫描；任一触发 → frozen failure 包，停止。

## V — 只读 verify（execute 后，一次）

- [ ] **V01** 只读 verifier：字节级不改动、身份/角色/账目/分母/状态
  语义逐项复核；产出 verify 报告。

## C — 判定与收尾（verify 后）

- [x] **C01** 判定：prepare 产出 `no_eligible_frames` → 按冻结停止
  规则 **frozen failure（数据不可得）**；decision-log 记录 +
  记忆 triage 待 V17 门收尾时一并执行。（Done 2026-08-15：判定
  `frozen failure`（`no_eligible_frames`）；fresh 数据到达后重新
  prepare 是确定性工具运行，不构成对失败的"重跑"。）
- [ ] **C02** 边界声明：fresh-confirmed 不是 promotion/qualification；
  效率仍 f≈12；不触发 V15/V16。（待数据到达并完成后补记。）

## 冻结纪律（任何阶段适用）

- 失败原样保留；禁止替换帧、调参、重跑、换候选。
- 禁止修改 R3 码本/先验/迭代上限/接口。
- 产物 additive；冻结根零改动。
- prepare 为确定性工具：用户提供新数据后可重新运行（不构成对失败
  的"重跑"——它只在数据源存在时产出执行计划）。
