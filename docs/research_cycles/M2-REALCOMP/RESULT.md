# M2 真实同帧三方法比较 — RESULT（G-M2-REALCOMP，只读汇总，无科学结论）

- **Track**：**DECIDE** 结果记录（真实数据同帧比较；本文件只读汇总，**不重跑、不下 SKR/发表结论**）。
- **Acceptance ID**：`G-M2-REALCOMP`；前件 `docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md`（§5 Pre-RESULT 清单为本文件的对照尺；独立 Pre-RESULT 与主线程接受不在本文件）。
- **状态**：三源 **COMPLETE**（判据见 §1：`rows.json` 内 `verdict=COMPLETE` + 行数 + `slice_match=True`；进程已退；END/exit 行未落盘缺口见 §7）。
- **NB 列**：**measured（M0 artifact 指针，不复制数值）**：`docs/research_cycles/M0-REALFRAME/RESULT.md` §2.1（1M m197/201）、§2.2（1p5M m203/207）、§2.3（2M m204/208）。本文件 §2–§3 只记新方法 12 臂实测；任何 M0 数字引用必须带 F9(i) 标注（§6）。
- **F9(i) 全表标注**：本文件所有表格与正文凡涉 M0/NB 对照语义均受此约束——**"u2-only, u1 via argmax, u1 正确率未验证"**（decision-log 2026-09-24 F9(i) 裁定；去标注引用 = 违规引用）。

---

## §1 三源终态 COMPLETE（预算内；END/exit 缺口声明）

| 源 | 输出根 | verdict（`rows.json/summary`） | wall（源） | 峰值 RSS | decodes | `rows` 行数 / 文件行数 |
|---|---|---|---|---|---|---|
| 1M | `workspace/m2real_d4e5f6a7` | **COMPLETE** | 1685.1 s（< 5400） | 0.465 GiB（< 4） | 13120 | 13120 / 511953 行 |
| 1p5M | `workspace/m2real_b8c9d0e1` | **COMPLETE** | 2399.3 s（< 5400） | 0.591 GiB（< 4） | 18368 | 18368 / 716625 行 |
| 2M | `workspace/m2real_f2a3b4c5` | **COMPLETE** | 3261.3 s（< 5400） | 0.730 GiB（< 4） | 24512 | 24512 / 956241 行 |

- 预算：三源 wall 均 < 5400 s；单次解码 300 s 终端（overrun 处理按冻结口径，-arm `wall_s` 无超限返工）；RSS 均 < 4 GiB；1 CPU（`budgets`：`wall_cap_s=5400 / per_decode_cap_s=300 / rss_cap_gib=4 / cpus=1`）。
- `block_accounting.csv` 行数（含表头）：13121 / 18369 / 24513，与 decodes（13120/18368/24512）一致。
- 进程已退；三根内落盘产物均为 `rows.json` + `block_accounting.csv` + `M2REAL_RESULT_<源>.md`。
- **缺口声明（END/exit 未落盘）**：runner 退出前 stdout 终态 END/exit（或等价终态 JSON）行**未写入任何文件**，磁盘上无对应产物。本文件 COMPLETE 判据为机内三项：`summary.verdict=COMPLETE` + `rows` 行数 = decodes（13120/18368/24512）+ `slice_match=True`（§4）。终端行字面留痕待发起执行的会话另行补录；补录前不得虚构 END/exit 原文。

---

## §2 逐源逐臂实测（每源 4 臂；HDC×2m + LB×2m；禁跨源跨臂合并）

### 2.1 源 1M（超帧 205，余数 407，`slice_match=True`；64-blocks 3280；`H_corr=0.8012690084416184` measured M0 §3）

| family | m | blocks | fails | undetected | FER(block) | sf_success/sf_total | f_super | f_notag | f_eff | λ_total |
|---|---|---|---|---|---|---|---|---|---|---|
| hdc | 197 | 3280 | 3280 | 3280 | 1.000000 | 0/205 | 1.27848956 | 1.20048829 | 6.06416456 | 1917405.000 |
| hdc | 201 | 3280 | 3280 | 3280 | 1.000000 | 0/205 | 1.30286496 | 1.22486369 | 6.08853996 | 1917601.000 |
| lb | 197 | 3280 | 3268 | 215 | 0.996341 | 0/205 | 1.27848956 | 1.20048829 | 6.04665599 | 856080.000 |
| lb | 201 | 3280 | 3273 | 227 | 0.997866 | 0/205 | 1.30286496 | 1.22486369 | 6.07832663 | 869200.000 |

### 2.2 源 1p5M（超帧 287，余数 405，`slice_match=True`；64-blocks 4592；`H_corr=0.8272902027770036` measured M0 §3）

| family | m | blocks | fails | undetected | FER(block) | sf_success/sf_total | f_super | f_notag | f_eff | λ_total |
|---|---|---|---|---|---|---|---|---|---|---|
| hdc | 203 | 4592 | 4592 | 4592 | 1.000000 | 0/287 | 1.27368961 | 1.19814176 | 6.05936461 | 2696032.000 |
| hdc | 207 | 4592 | 4592 | 4592 | 1.000000 | 0/287 | 1.29729832 | 1.22175046 | 6.08297332 | 2695607.000 |
| lb | 203 | 4592 | 4587 | 212 | 0.998911 | 0/287 | 1.27368961 | 1.19814176 | 6.05415373 | 1226064.000 |
| lb | 207 | 4592 | 4586 | 219 | 0.998693 | 0/287 | 1.29729832 | 1.22175046 | 6.07672026 | 1244432.000 |

### 2.3 源 2M（超帧 383，余数 529，`slice_match=True`；64-blocks 6128；`H_corr=0.8333327179427281` measured M0 §3）

| family | m | blocks | fails | undetected | FER(block) | sf_success/sf_total | f_super | f_notag | f_eff | λ_total |
|---|---|---|---|---|---|---|---|---|---|---|
| hdc | 204 | 6128 | 6128 | 6128 | 1.000000 | 0/383 | 1.27031344 | 1.19531338 | 6.05598844 | 3597860.000 |
| hdc | 208 | 6128 | 6128 | 6128 | 1.000000 | 0/383 | 1.29375096 | 1.21875090 | 6.07942596 | 3597343.000 |
| lb | 204 | 6128 | 6125 | 324 | 0.999510 | 0/383 | 1.27031344 | 1.19531338 | 6.05364558 | 1642304.000 |
| lb | 208 | 6128 | 6125 | 357 | 0.999510 | 0/383 | 1.29375096 | 1.21875090 | 6.07708310 | 1666816.000 |

- HDC 两 m FER 全 1.0（sf 成功全 0：0/205、0/287、0/383）；LB FER：1M 0.996341/0.997866，1p5M 0.998911/0.998693，2M 0.999510/0.999510（sf 成功亦全 0）。
- FER 分母 = 64-blocks（3280/4592/6128）；超帧计数（205/287/383）另列，永不作 FER 分母；`key-eligible` 200/276/364 为 `N_req` report-only 对照列（`key_eligible_contrast=[200,276,364]`），与 FER 分母列分立、禁混用。
- 切片：超帧 205/287/383，余数 407/405/529 符号已丢弃，`slice_actual == slice_expected`，`slice_match=True`（三源一致）。

---

## §3 f 三分线 + 泄漏分解（禁不透明合并；禁把 f_super 当 f_eff 报）

- `f_notag`（D2 去 tag 口径 input；HDC/LB 同 m 同值，因同 m 同 H 基）：1M 1.20048829（m197）/ 1.22486369（m201）；1p5M 1.19814176（m203）/ 1.22175046（m207）；2M 1.19531338（m204）/ 1.21875090（m208）。
- `f_super` / `f_notag` / `f_eff` 为**三分立线**（FER > 0 时永不得把 `f_super` 当 `f_eff` 引用；单源 `f_eff` 永不可认证/不可文献可比）。数值见 §2 各臂行（`f_eff = f_super + 4.785675·FER` 口径，PREREG §1 会计）。
- `λ_total = leak_EC + 64-bit tag`（+ 控制轮次/控制帧/盲救援段公开量逐项单列；禁合并）：`lambda_parts = {leak_EC, tag, control=0.0, rescue=0.0}`，`λ_total` 见 §2 末列（如 1M-hdc-m197 leak_EC 1707485.0 + tag 209920.0 = 1917405.0）。
- 每源 1.50× prior 机会成本行单列、**不进 f 分子**（LB 臂 `prior_1p50_reportonly`：1M 445367.98，1p5M 623515.17，2M 832077.74；HDC 臂 0.0 单列）。
- 消息数两口径独立标注、不可互比：Cascade 参考 446 vs LDPC 参考 3.14（`messages_per_frame_actual`：HDC 约 520–523，LB 3.14）。
- `H` 用 M0 §3 `H_corr`（各源自己的 H：0.80127/0.82729/0.83333），永不用合成 F03 H（合成 H 只在逐字 allocation/params 校验器内、标 assumed，不进 f）。
- 四列归属：blocks **measured**；`H_corr` **measured**（M0/R1）；Mueller pins **assumed-v1**（`[8,4]`/max_passes 4/sweep 1/消息公式 provisional；真值 QBER-自适应 k1..k6，n=2^16 bits；Gray 永标 assumed；q=1024 外推）；有限长极限 **projected**（空）；**qualified**（空，无 SKR）。

---

## §4 undetected 隔离（独立列，永不并入 success/FER）

- 按源聚合（4 臂 blocks 合计 = decodes）：成功（blocks − fails）19（1M）/ 11（1p5M）/ 6（2M），其中 undetected = **0**；失败 13101 / 18357 / 24506（= decodes − 成功）。
- HDC 臂 `undetected = blocks_done`（1M 3280/3280；1p5M 4592/4592；2M 6128/6128；`fer_blocks=1.0`）。
- LB 臂 undetected 独立列：1M 215/227；1p5M 212/219；2M 324/357（fails 内含，从未并入 success；`decoded`≠success 图例不适用——本包 success = exact_match = ¬failed）。
- `accepted` / `accepted_wrong`（= undetected）语义按 PREREG §1 会计：`accepted_wrong` 独立列，永不并入 success/FER 分子。

---

## §5 D2 工作表（DEFERRED；三分支原文逐字；无分支被求值）

- 状态：**DEFERRED**（需 M0 NB refs + 独立 Pre-RESULT；本文件不求值任何分支、不作后继主线结论）。
- 权威来源：`docs/decision-log.md`「2026-09-24: M2 D2 三分支预注册阈值裁定」节；PREREG §4 逐字预注册（开发决策，不是发表主张）：
  - (1) **HD-Cascade 去 tag f 比 NB 低 > 0.05** ⇒ 如实报告，NB 改定位为"单向 1 条消息低时延"，给定信道时延下密钥吞吐对比；
  - (2) **分层二元 ≥ NB（f 更优或持平）** ⇒ "高维必须用非二元码"叙事不成立，主线转向分层二元 + 信道建模；
  - (3) **否则** ⇒ NB 主线进 M3（码设计）。
  - `0.05` 为预注册数，改之 = 新包。D2 只决定后继主线方向；它不是 P3 verdict，不放行任何 P3 门控动作，不产生 SKR/发表主张。
- D2 输入就绪：本包 12 臂 `f_notag`（§3）为去 tag 口径 input；NB 侧以 M0 artifact 指针（本文件 §0）为准，不复制数值；阈值重算留给独立 Pre-RESULT。

---

## §6 claim ceiling（禁句零违反）

> 无安全观测量，只能写"实测纠错收益 / 公开开销收益"；禁止 SKR、secure-key、资格化、composable 安全、发表主张。单一构造实例（NB 实例 2026092001；新方法 pin 实例见快照）、单次采集、Jan-21 三源上的开发测量。对外数字只能来自真实帧实测本身。

- 本文件无 SKR/资格化/发表主张句；有限长极限列仍为 projected，不得升格 measured/qualified。
- F9(i) 标注全表在场（§0）：任何 M0 数字对照引用均须带"u2-only, u1 via argmax, u1 正确率未验证"；`fails_full10` 观测列语义沿用 M0（本包不设 u1 纠错进恢复链；进恢复链 = 新包，M0 数字不得回溯改写）。

---

## §7 已知缺口（需主线程/独立复核处置；本会话只读、不补写）

1. **END/exit 行未落盘**（§1 已声明）：三源进程已退但 stdout 终态 END/exit（或等价终态 JSON）行磁盘上无产物；本文件以 `verdict` + 行数 + `slice_match` 为判据记 COMPLETE，不虚构终端原文。待发起执行的会话逐字抄录（或主线程另行授权另存 `stdout_END_*.txt`）。
2. **`backend_used` 声明待补**：三根 `rows.json` 内 `grep -c backend_used` = 0（均缺失）；译码后端 pin 以 PREREG/PROMPT 快照（assumed-v1 / verbatim F2+F3）为准，**本文件不得猜写**具体后端字符串。待独立 Pre-RESULT 核对执行面 pin 后补声明。
3. 独立 Pre-RESULT（PREREG §5 清单：阈值重算、泄漏分解、undetected 隔离、per-source 分列、披露会计、A-CMPE 全列、四列归属、claim ceiling）与主线程接受尚未发生；本文件为执行者记录，不代替接受。

---

## §8 保护洁净（只读复测）

- `git diff -- src/` = **0 字节**；`git diff --stat -- src/ experiments/ tools/` 为空。
- `results/` = **0 B**（空）；`comparison_bench/outputs_comparison/` 无本包写入（输出仅三冻结根 + 本文件）。
- 本会话只读打开三根 `rows.json` / `block_accounting.csv` / `M2REAL_RESULT_*.md` 做汇总，未写入、未重跑、未续跑；未 commit、未 push。
- 本文件为本次允许的唯一写入（`docs/research_cycles/M2-REALCOMP/RESULT.md`）；包/输出根/执行/commit 均未触。
