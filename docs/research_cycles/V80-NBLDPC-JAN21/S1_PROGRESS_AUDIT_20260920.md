# V80 S1 进度与潜在问题审计（2026-09-20，只读审计）

- Track: **EXPLORE**（审计 = docs-only；无执行、无授权、无裁决、无数字解读为结论）。
- Branch: `formal-ir-v72p1-addendum-clean`；未 commit/push。
- 本文件**不授权任何动作**，也不把任何 S1 输出解释为科学结论（HOLD 语义仍适用，见 P6）。
- 审计方式：读 manifest/rows（重跑根）、runner 源码、cycle 文档、decision-log 尾部、`wsl ps`。
  **未修改**任何证据根、runner、测试、计划或已执行根。

## 1. 现场快照（审计时刻采样，进程在跑）

- 重跑根：`workspace/s1_mcde_1b079a49-7a2a-4e3f-8a20-00cb69f3c210`
  - `config_hash = recorded_hash = 60ab1e44…0da`（与 Pre-EXEC Q2 一致）；`partial=true`。
  - ledger：PRIMARY 420/420 · SECONDARY 107–108/180 · SETUP 12 · TOTAL 527–528。
  - terminals：PRIMARY `SELECT`；SECONDARY `resource_blocked`。
  - gate：PRIMARY `pass=true, f_ens=1.13752, n=32, sw_violations=0`；
    SECONDARY `pass=false, f_ens=null, n=0`。
  - flip_rule：`flip=false`，`withheld`（跨单位：PRIMARY 层单位 vs SECONDARY 全符号单位）。
  - wall_windows 5 个（每个 cap 3600 s）。
- **live 进程**（`wsl ps`，审计时 3 分钟）：
  `/usr/bin/time -v .venv/bin/python -m …v80_s1_mcde_runner --execute-real
  --execution-authorized --resume-from workspace/s1_mcde_1b079a49-…`（pid 53817/53818）。
  ⇒ 执行会话正在用 `--resume-from` 续跑 SECONDARY；**不得并发再开第二个 root**。
- 旧根 `workspace/s1_mcde_07723233-…` 保留未动（hash-foreign）。

## 2. 数值事实（从 rows.json 直接聚合）

### 2.1 PRIMARY（GF(32)² L2 层，width 5，m₂ 44–60，pop10×gen14）

screen（2 seeds × 17 m）/ confirm（**仅 CONFIRM_SEEDS[0] 单 seed**）每 (m, seed) 收敛数：

| m₂ | 44 | 45 | 46 | 47 | 48 | 49 | 50 | 51 | 52 | 53 | 54 | 55 | 56 | 57 | 58 | 59 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| screen/seed | 0/9 | 0/9 | 0/9 | **1/9** | 2/8 | 2/8 | 2/8 | 2/8 | 2/8 | 1/8 | 0/8 | 2/8 | 2/8 | 3/8 | 5/8 | 3/8 | 4/8 |
| confirm(seed1) | 0/9 | 0/9 | 0/9 | **1/9** | 2/8 | 2/8 | 2/8 | 2/8 | 2/8 | 1/8 | 0/8 | 2/8 | 2/8 | 3/8 | 5/8 | 3/8 | 4/8 |

- 32 个 confirm 收敛行的 f_row：最小 **1.1375（m₂=47，唯一 ≤1.15 的点）**，其余
  1.1619(m48) … 1.4524(m60)。
- **两个 screen seed 在每个 m 上收敛计数完全相同**（0/0、1/1、2/2 … 5/5）。
- 耗时：screen 783 s / 280 行；confirm 2518 s / 140 行。

### 2.2 SECONDARY（直接 q=1024，width 10，m 24–31）

- screen **100/100 已完成**：m=24,25,26,27,29 → **0 收敛**；m=28 →1/6/seed(f=1.314)、
  m=30 →2/6(f=1.408)、m=31 →1/6(f=1.454)。
- confirm 7–8/80，全部落在 **m=24**（f=1.126，全网格唯一 ≤1.15 的点），**0 收敛**。
- 耗时：screen 4871 s / 100 行（mean 48.7 s）；**confirm mean 288 s、max 348.6 s / 行**。

### 2.3 口径换算（审计推算，供决策用）

锚点 H_L1=0.02566205、H_L2=0.80690067 ⇒ H_full=0.83256，n·H=213.1 bits（n=256）；
runner 的 `f_implied = 10m/(n·H)` **不含 64-bit tag**（源码 583–585 行）。

| 口径 | PRIMARY（m₂=47 + m₁≈2） | SECONDARY（m=24） |
|---|---|---|
| 层/逐符号 f（gate 用的口径） | 1.1375（L2 层） | 1.126 |
| 整帧 tagless f | 5·49/213.1 ≈ **1.150** | 240/213.1 = 1.126 |
| 整帧含 tag f | (245+64)/213.1 ≈ **1.450** | (240+64)/213.1 ≈ 1.426 |
| n=1024 超帧含 tag f | ≈1.213 | ≈1.201 |

## 3. 潜在问题（按严重度）

### P1（阻断级 · 预算契约被击穿）`per_call_s=300` 未生效

- 冻结预算 `per_call_s=300`，`run_once` 超时应返回 `overrun` 并触发 `resource_blocked`。
- 实测：SECONDARY confirm 有 **4 行 318.5 / 321.9 / 334.0 / 348.6 s，仍 `status="ok"`**，
  排行继续（rows 里 status 全为 ok）。⇒ cap 未接到停止路径（或 overrun 未传播/未终止）。
- 后果：SECONDARY 单槽成本失控（mean 288 s），wall 窗口被逐条吃穿，才出现
  `resource_blocked` + 5 个窗口。

### P2（阻断级 · SECONDARY 按现有证据已近乎判死，但仍在烧机时）

- 唯一能过 1.15 的点是 m=24：screen **0/14** 收敛、confirm **0/8** 收敛；
  有收敛的 m=28/30/31 的 f=1.314/1.408/1.454 全部 >1.15。
- 剩余 ≈72 槽 × ~288 s ≈ **5.8 h 纯计算 ≈ 6–7 个新 wall 窗口**，且 confirm 更贵。
- 建议（需主线程决策，审计不代决）：以现有证据把 SECONDARY adjudicate 为
  `non-pass`（并说明理由），或把剩余预算收缩成 m=24 定向少量复核，避免空转。

### P3（高 · PRIMARY 的 pass 统计上很脆）

- 通过只靠 **m₂=47 的 1/9 个 DE 候选**；confirm 仅 1 个 seed（代码注释明示
  "confirm 1 reuse seed"，与 `CONFIRM_SEEDS` 声明 2 个不一致）；
- 收敛对 m **非单调**（44/45/46 = 0/9，54 = 0/8，58 = 5/8）——容量边界应单调，
  实测呈噪声型 ⇒ 收敛主要由 DE 搜索运气决定；gate 取"∃ 收敛行的最小 f"
  ≈ **对 ~9 张彩票取最好值**，存在乐观偏倚；
- 两个 screen seed 在每个 m 上收敛计数**完全相同** ⇒ seed 维度未提供独立证据。
- 建议：进 S2 前补一个可复现性门（m₂=47 在两 seed × 多次 DE 重启下稳定收敛），
  否则 S2 可能建在不可复现点上。

### P4（高 · 口径未冻结，直接影响 S2 目标与验收）

- 现在同时存在三种 f：层单位（1.1375）、整帧 tagless（≈1.150）、整帧含 tag（≈1.450）。
  `PROGRAM_PLAN.md` §1.1 说 `leak = m·10 + 64`，§1.2 的净收益表却按
  `net = 1472 − 10m`（即 267 bits 对应 net +1205）⇒ **同一份计划里 tag 口径不一致**；
- 含 tag 口径下 **n=256 的 f 下限 ≈1.43–1.45，永远达不到计划的 f≤1.3**（tag 独占 0.30）；
  只有 n≥512（建议 1024）超帧才回到 ≈1.21（DE 结论本身与 n 无关，可迁移）。
- 建议：S2 立项前冻结单一口径（推荐"整帧含 tag f"+ 超帧 n=1024），并修正计划算术。

### P5（中 · 记录链与文书缺口）

- `decision-log.md` 仍止于"V80 S1 HOLD"条目，缺：F1/F2/F3 rework 完成、
  **G-D5R（D5-delta 独立复审）**、fresh grant、重跑开工、PRIMARY 完成、
  SECONDARY resource_blocked。
- **未找到任何 G-D5R 复审记录**；`S1_RERUN_PREEXEC` 里的"48 passed + 6 subtests"
  是实现方自测，不等于独立复审（D5/4438 教训：mechanics green ≠ semantic correctness）。
  FIX_PLAN §Process-2 把 G-D5R 列为重跑前的硬门 ⇒ 这是**合法性缺口**，需补记录或补做。
- EXPLORE 契约要求的"一份 append-only 探索日志 + 一次批末独立复审"尚未出现；
  目前是**结果（PRIMARY SELECT）先于文书**。
- `S1_HOLD_20260919.md` 仍声明 HOLD 有效，与"已重跑且 PRIMARY SELECT"状态冲突；
  `S1_READINESS.md` 头仍为 "NOT accepted"。

### P6（中 · 架构选择无正式裁决）

- flip_rule 因跨单位被 `withheld` ⇒ **GF(32)² 分层 vs 直接 q=1024 没有被正式比较**；
  S2 的架构选择需要另立统一口径（建议都用"整帧含 tag f"），否则选择无依据。

### P7（低-中 · 计划/文献待办仍未闭合）

- Mitra 提示的 dv 支持差异（`DV_SUPPORT=(2,3,4,5,8,13,20)`、`DV_CEILING=40` vs
  论文 VN 2–5）仍是 "S1-freeze 待办"；搜索空间过宽可能正是低 m（44–46）全不收敛
  的原因之一（搜索稀释）。
- §2.4 Tauz/Mitra ITW2024（PA-aware IR，f 不必压到 1.0）仍未读。若 P4 确认
  f 卡在 ~1.15–1.45，这条是唯一替代框架，**优先级应上调**。

### P8（提示）

- 审计期间 rows 从 527 增到 528（进程在写），本文件所有计数均为采样值。
- 计划 §1.1 的"m≈24–31 ⇒ f≤1.3"在 H=0.8326 下应为 f=1.126–1.454（tagless），
  只有 m≤27 才 ≤1.3。

## 4. 建议的下一步顺序（供主线程决策，审计不执行）

1. **口径冻结（P4）**：选"整帧含 tag f"+"超帧 n=1024"，修正 PROGRAM_PLAN §1.1/§1.2 算术。
2. **SECONDARY 处置（P2）**：停/缩（需授权），或按现有证据 adjudicate non-pass。
3. **补 G-D5R 与记录链（P5）**：独立复审记录 + decision-log 回填 + HOLD 文文件更新/关闭。
4. **PRIMARY 可复现性门（P3）**：m₂=47 双 seed × 多 DE 重启；不过则不得进 S2。
5. **修 `per_call_s` 接线（P1）** 后再谈任何后续重跑。
6. 之后才谈 S2（PEG / FER≤5%，禁用 three-shift-cyclic 母矩阵族）。

## 5. 本审计明确未做

- 未读/未解释任何 S1 结果为科学结论；未停进程；未 resume；未改 runner/测试/计划；
- 未创建/删除任何根；未 commit/push；未授权任何执行。
