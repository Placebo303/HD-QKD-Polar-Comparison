# V72P3 进度与问题盘点 — 2026-09-19（docs-only，无执行）

- 仓库/分支：`HD-QKD_Polar_Comparison`，分支 `formal-ir-v72p1-addendum-clean`，
  HEAD `59ea41d0 chore: publish complete formal IR project snapshot`。
- 本文件：只读盘点 + 问题归类 + 已处理项 + 待授权项。**零执行**：无解码器/DE
  调用、无真实数据访问、无证据根改动、无 commit/push。
- Track：documentation-only（AGENTS.md §1.2 适用性矩阵，无 track gate）。

---

## 1. 当前进度

### 1.1 V72P2（EXPLORE，合成诊断）已收口到 D19

- D1–D18 完成；D18 L2 系综 DE 扫描选出唯一 winner `lam_d2_0.20_d3_0.80`
  （DV3 阈值 0.54681 / L020 0.35149，并列按冻结 tie-break）。
- D19 有限系综验证（2026-09-18 执行）：n128 96/96 calls，M=19/48、
  M_g=[3,2,2,4,3,5]、C=5/48、b=14、c=0、discord=14 → **AMBIGUOUS**
  （POSITIVE 需 M<30，NEGATIVE 需 M>16，均不满足）；undetected=0 已隔离。
  n256 未进入（0 calls）：冻结 seed `2026094408` 确定性
  `construction_failed`，按冻结规则不替换。终态 `D19_L2_FINITE_AMBIGUOUS`。

### 1.2 V72P3 G6/G7（DECIDE，真实数据）已跑完 R7–R14 并作出路由判定

证据链（转录自各 RESULT.md 与 `V72P3G7-ROUTE/ROUTE_MEMO.md`，未重算）：

| 步骤 | 结果 |
|---|---|
| R7/R8 码率扫描 | 转变点定位在 92\|96；主线程决定采用 **m=100** 做 fresh-pool 确认（m96 停放） |
| G6-R1 真实固定 m94 | 0/128 |
| R2DIAG | 真实残差 weight 119–128，mean 123.7 |
| R9 真实固定 m100 | 1/128（gross net +140 / true net −72052，两者并列陈述） |
| R10 同 session 对照 | 1/128，prior-match 关闭 |
| R11 自适应 m120 分级 | accepted 87，lift 86，undetected 0，net −78392（diagnostic-only） |
| R12 fresh-pool（P-1p5M 2187..2250） | accepted 79/128（0.6172），net −79432，**CONFIRMED-GENERALIZING** |
| R13 审计 | 0/90 近失（最小残差 21 ≫ 14 门槛）；cap-peg ⇔ fail 100%；S1 恶化 65/90 → **PIVOT** |
| R14 跨 session 权重普查 | U2 mean 72.70 / 77.62 / 90.07（1M/1p5M/2M），min 51–65 → **NO-POSITIVE-REGIME** |

### 1.3 G7 路由判定（当前科学的终态）

`docs/research_cycles/V72P3G7-ROUTE/ROUTE_MEMO.md`：
**STOP positive-net pursuit on surveyed regimes**。量化矛盾 —

- 净收益闭式：`net = 320 − 8m` ⇒ 正收益 iff `m < 40` ⇔ `weight < 32`；
- 实测权重 72.7–90.1，而收敛要求 `m/n ≳ 0.63`（session 均值）到 `≳ 0.72`
  （DE 边沿 92|96）。

两条逃逸路径均已量化且**均未观测到**：(i) 采集噪声再低约 2.5×（mean
weight < 32）；(ii) 码/先验把 DE 边沿提升 ≥2×（weight ~70+ 时 m<57 收敛）。

---

## 2. 遇到的问题

### A. 科学阻塞（不可在本轮自动解决，需用户决策）

A1： surveyed regimes 内不存在正净收益工作点（见 1.3）。
A2： 逃逸路径 (i) 依赖能否取得更安静的采集数据；(ii) 是长射门，门槛已写明。
A3： G7 明确 L1 / 跨层 / Cascade 邻居**在本判定之外**（未测），不做 SKR/资格化
     工作直到任何地方出现正净收益。

### B. 工程问题（本轮已定位）

B1 **执行后"根节点不存在"类断言失效**（已知 fix-debt 的同类扩散）：
   R9/R10/R11/R12 共 5 个用例 + D17 `test_d16_root_absent_and_blank_predictions`
   + D19 的 4 个（已记录在 troubleshooting）。证据根**未**改动。
B2 **`pytest.ini` 硬编码 Windows 绝对 basetemp**：
   WSL 下该路径非法 → setup errors（既有 workaround `-o addopts=""`）；
   Windows 下 tmp_path 落在 `workspace/tmp_pytest`，被
   `refuse_out_root` 的受保护前缀命中 → r7 出现 3 个假失败。
   实测：完全删除 `--basetemp` 在 Windows 又产生 12 个 setup error，
   故**不能**简单删除，portable 配置仍是开放 fix-debt。
B3 **多文件合并跑 pytest 触发命名空间/sys.modules 污染**：
   r7 先导入生产模块后，G6 系列的 `PRODUCTION_ABSENT` 断言误判
   （一次批量 82 failed；逐文件跑则干净）。既有约定即"按文件跑"。
B4 **Windows(conda) 与 WSL(.venv) 判定不一致**：D17 在 Windows 8 failed /
   37 passed，WSL 3 failed / 42 passed。权威结论以 WSL 为准。
B5 **工作区含大量未跟踪产物**：G6/R7–R14 的 scripts、tests、research_cycle
   docs，以及 4 个已修改文档（AGENT_PROJECT_MEMORY.md、decision-log.md、
   D19 日志、troubleshooting.md）尚未提交；未 push。

---

## 3. 本轮已处理

- `docs/troubleshooting.md` 追加三条可复用故障条目：B1（R9–R12/D17 同类）、
  B2（Windows 侧 basetemp 假失败 + 不可删除的实测依据）、B4（环境差异）。
- 本状态报告（`docs/v72p3-progress-and-issues-report-2026-09-19.md`）。
- 未改动任何证据根、未执行任何科学调用、未 commit/push。

## 4. 补充（2026-09-19 用户质疑后）：同一份数据上的重定位

用户两点质疑：(a) 这类数据就是日常用的数据，不能靠"换更安静的数据"解决；
(b) 二元 LDPC / 二元 Polar 在同一类数据上结果很好，为什么高维反而更差。
下面用仓库既有实测数回答，**不换数据**。

### 4.1 二元管线为什么能成（既有证据）

`docs/v19-binary-mlc-prototype-result-20260816.md`：

- 逐 Gray 位面（10 planes）+ 冻结二元 LDPC v4 H1 / v5 H2 回退；
- N=256 symbols/frame，50 frames/plane，**500 plane-frame 试验 0 失败**；
- 平均 syndrome ≈ 587 bits/frame；
- 以 `H_full = 0.549955 bits/symbol` 计，实测 **f ≈ 4.169**；理想 f≈1.0，
  差距来自有限长码率/行数，非概念性阻塞。

按同一会计口径（Â = 0.6，每符号 10 bits）折算：

- 每符号泄漏 = 587/256 = **2.293 bits/symbol**；
- 每符号毛密钥 = Â · 10 = 6 bits → **净 +3.71 bits/symbol**（128 符号约
  +474 bits/帧，扣 tag 仍显著为正）。

即：二元 MLC 在 f=4.17 这种"效率很差"的水平上**仍然是净正的**，因为真条件熵
极小（0.55 bits/symbol / 10 bits）。

### 4.2 高维管线为什么更差（容量式核对，与实测自洽）

设 n=128、GF(32) 每层 5 bits、tag 64 bits、Â=0.6，解码器必须靠 syndrome
消除的每符号不确定性为 `H_eff`：

- 泄漏 `L = 5m + 64`；净 `N = Â·5·(n−m) − L = 320 − 8m`
  ⇒ **净正 iff m ≤ 39**；
- 可解性（信息下界）`5m + 64 ≥ n·H_eff` ⇒ `m ≥ (n·H_eff + 64)/5`；
- 合并 ⇒ **净正 iff `H_eff ≤ (5·39 − 64)/128 = 1.023 bits/symbol`**；
  通式 `N = n[5Â − (1+Â)H_eff] − 64(1+Â)`，Â=0.6 时净正 iff `H_eff < 1.875`。

用观测值校准 `H_eff`：

- 当前 Model-F 先验下的 belief/先验熵 ≈ **4.343 bits/symbol**（GF(32) 上限 5，
  D7_D belief_mean_entropy 上界 4.343407；R14 记为 session-blind 弱先验）；
- 预测 `m_min/n ≈ H_eff/5 = 0.869` ⇒ `m ≈ 111`；
  实测：m94 → 0/128；m100 → 1/128；m120 分级 → 87/128。**完全吻合**。
- 预测净 = 128×(3 − 1.6×4.343) − 102.4 = **−607 bits/块**；
  实测 R9 −563、R11 −612、R12 −620 bits/块。**吻合（~10%）**。

对比（同一份数据、同一会计口径，折成每 10-bit 符号）：

| 管线 | 每符号泄漏 | 每符号毛密钥 | 每符号净 | 收敛 |
|---|---|---|---|---|
| 二元 MLC（实测 f=4.169, H=0.55） | 2.29 bits | 6 bits | **+3.71 bits** | 500/500 |
| 高维 GF(32) 分层（m=100…120 实测） | 8.8–10.4 bits | 6 bits | **−2.8…−4.4 bits** | 需 m/n≈0.87 才勉强 |

**结论：不是"高维更差"，而是我们的高维解码器拿到的先验接近均匀
（4.343 bits/symbol），把真条件熵（0.55–0.80 bits/symbol，V25/V19 实测
`H(A|B)`/`H_full`）当成了 5 倍来付泄漏。** 二元管线的隐含优势在于它老老实实
用了 Bob 侧条件信息（逐位面经验 LLR / 对齐后的低误码表示），所以 f 虽然差，
绝对泄漏只有 2.29 bits/symbol。

### 4.3 门槛（可证伪）

在**这份数据**上净转正的充要条件：`H_eff ≤ 1.023 bits/symbol`
（n=128, Â=0.6, tag 64）。当前 4.343 → 需降约 **4.3×**；
信息论地板约 0.55–0.80 ⇒ 存在 **4–8× 余量**，余量来自"把 Bob 侧条件结构
喂回先验"，而不是换数据。

两个互斥解释必须由同一个测量区分（见 §5）：

- (a) 先验盲：真条件熵仍是 0.55，只是解码器不知道 → 修先验即可；
- (b) 表示脏：G6/G7 用的块确实比二元位面脏得多（R2DIAG true_weight
  119–128/128），真条件熵本身就在 4.3 附近 → 则必须先做对齐/条件化
  （二元管线前端隐式做了这一步），再谈纠错。

- **P1（工程）**：把陈旧的"根不存在"断言改为 snapshot invariance
  （根不存在 OR 根等于已冻结执行包）。属 scoped change，需单独授权；
  严禁为变绿而删根或随手改断言。
- **P2（工程）**：portable basetemp（平台判定或 env 覆盖），替代单一绝对
  Windows 路径。
- **D1（科学）**：G7 portfolio 三选一 ——
  (1) 更安静区段采集（若可得）；
  (2) 2× 阈值码族猎搜（长射门，需先写明门槛）；
  (3) L1/跨层/Cascade 邻居（本判定之外，未测）。
- **D2（工程卫生）**：是否提交当前未跟踪的 G6/R7–R14 快照（需用户明确授权）。
