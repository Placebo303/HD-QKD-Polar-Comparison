# M2 真实同帧三方法比较 — INDEPENDENT_ACCEPTANCE（G-M2-REALCOMP，独立 Pre-RESULT）

- **Track**：**DECIDE** 独立 Pre-RESULT（真实数据同帧比较；本文件只复核、不重跑、不下 SKR/发表结论）。
- **Acceptance ID**：`G-M2-REALCOMP`；对照尺 `docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md` §5；复核对象 `docs/research_cycles/M2-REALCOMP/RESULT.md`（执行者记录）。
- **独立性**：本文件为独立复核线程记录，不代替主线程接受；主线程接受（用户签字）见 §6，当前 **BLANK**。
- **F9(i) 全程约束**："u2-only, u1 via argmax, u1 正确率未验证"（decision-log 2026-09-24 F9(i) 裁定）；本文件任何 M0/NB 对照语义均受此约束，去标注引用 = 违规引用。
- **数值政策**：本文件不复制、不重算、不改写任何实测数值；数值权威唯一为 `RESULT.md` §1–§3 + 各输出根 `rows.json` / `block_accounting.csv`；NB 侧以 M0 artifact 指针为准（`M0-REALFRAME/RESULT.md` §2.1–§2.3），不复制数值。

---

## §1 Pre-RESULT 清单复核（PREREG §5 逐项；全 PASS with comments）

| # | 清单项 | 结论 | 依据（RESULT 章节，不复制数值） |
|---|---|---|---|
| 1 | 阈值重算（D2 三分支条件逐字核对） | **PASS** | §5 DEFERRED 原文逐字；求值见本文件 §3（独立求值，不改 RESULT §5） |
| 2 | 泄漏分解（`leak_EC` + 64 tag + 控制项逐项单列；禁不透明合并） | **PASS** | §3 `lambda_parts` 四项单列 + `λ_total` 末列；`prior_1p50_reportonly` 单列不进 f 分子 |
| 3 | undetected 隔离（独立列，永不并入 success/FER） | **PASS**（+ comment C1） | §4 按源聚合 + 分臂独立列；`accepted_wrong` = undetected 独立列 |
| 4 | per-source 分列（禁跨源/跨臂合并；205/287/383 与 200/276/364 两列分立） | **PASS**（+ comment C5） | §2 逐源逐臂分列；FER 分母列与 `key_eligible_contrast` 对照列分立声明 |
| 5 | 披露会计（prior 1.50× 行单列不进 f 分子；盲救援段单列） | **PASS** | §3 机会成本行 + `control=0.0 / rescue=0.0` 单列 |
| 6 | A-CMPE 全列齐全（A-CMPE-1..7） | **PASS**（+ comments C4、C5） | §2–§4 覆盖 attempted/exact_match/accepted/accepted_wrong、f 三线、λ、wall/RSS/消息数、N_req 对照、d/q/n_IR 分离、四列归属 |
| 7 | 四列归属（measured / assumed / projected / qualified；有限长极限列仍为 projected） | **PASS** | §3 末段四列归属逐项；qualified 空、无 SKR |
| 8 | claim ceiling（§8 禁句零违反；F9(i) u2-only 标注全表在场） | **PASS** | §6 禁句逐字 + §0 F9(i) 全表标注声明；`fails_full10` 语义沿用 M0（+ comment C3） |

- **总判**：独立 Pre-RESULT **PASS with comments（C1–C6 见 §2）**；FAIL 项为零；通过不代替主线程接受（§6 BLANK）。

---

## §2 Comments（C1–C6；非阻塞，不改数值、不改包）

- **C1 — HDC `undetected = blocks_done` 为 labeling 约定，非安全主张**：`RESULT.md` §4 记 HDC 臂 `undetected = blocks_done`（`fer_blocks=1.0`）。此为"失败块全部落在 undetected 计数口径"的 labeling 约定（`accepted_wrong` 独立列、计失败、永不并入 success），不是"错误被接受为密钥"的安全主张；任何安全/密钥含义的引申均属违规引用。
- **C2 — `RESULT.md` §4 成功句易误读，改法**：§4 首句"成功（blocks − fails）19（1M）/ 11（1p5M）/ 6（2M）"易被误读为"存在 19/11/6 成功超帧"。规范读法：**按源 4 臂 blocks 合计口径下的 `blocks − fails` 余数（LB 臂零星非失败块），非超帧成功数**；`sf_success/sf_total` 全 0（§2 各臂行：0/205、0/287、0/383）才是超帧口径结论。建议后继文档引用 §4 首句时并列 `sf_success` 全 0 行，或径引 §2 臂表；本文件不改 RESULT 原文。
- **C3 — `fails_full10` N/A waiver**：本包不设 u1 纠错进恢复链（PREREG §1 会计；RESULT §6），故 `fails_full10` 在新方法 12 臂无观测列；M0 口径语义沿用声明（RESULT §6 末句）在场即视为覆盖，缺列不判 FAIL。
- **C4 — `accepted` 列在 csv**：PREREG §1 会计要求 `accepted` / `accepted_wrong` 双列；RESULT §4 以 `accepted_wrong`（= undetected）独立列 + `accepted` 语义按 PREREG 会计声明覆盖。`accepted` 明细以各根 `block_accounting.csv` 为准，不在本文件/RESULT 正文逐行复制；缺正文逐行表不判 FAIL。
- **C5 — `key_eligible` 顺序映射**：`key_eligible_contrast=[200,276,364]` 顺序为 1M / 1p5M / 2M（PREREG §1 帧集澄清：200 / 276 / 364），与 FER 分母列（205/287/383）分立、禁混用（RESULT §2 末段已声明）。
- **C6 — provenance notes**：三源输出根 `workspace/m2real_d4e5f6a7`（1M）/ `workspace/m2real_b8c9d0e1`（1p5M）/ `workspace/m2real_f2a3b4c5`（2M）；NB 侧 artifact 指针见 RESULT §0（M0 §§2.1–2.3，不复制数值）；`H_corr` 引 M0 §3（各源自己的 H）；Mueller pins 引用 PROMPT 快照 assumed-v1（`[8,4]`/max_passes 4/sweep 1/消息公式 provisional；真值 QBER-自适应 k1..k6，n=2^16 bits；Gray 永标 assumed；q=1024 外推）。

---

## §3 D2 求值（预注册阈值逐字；开发决策，不是发表主张）

- 权威来源：decision-log「2026-09-24: M2 D2 三分支预注册阈值裁定」节；PREREG §4 逐字；RESULT §5 为 DEFERRED 原文（本文件求值不改 RESULT §5）。
- 输入：本包 12 臂 `f_notag`（RESULT §3 去 tag 口径 input）+ NB 侧 M0 artifact 指针（RESULT §0；F9(i) 标注约束下引用，不复制数值）。
- 求值（逐源逐 m 同基比较，禁跨源跨臂合并）：
  - **分支 (1)（HDC 去 tag f 比 NB 低 > 0.05）**：**不满足**。`f_notag` 同 m 同值（RESULT §3：同 m 同 H 基，HDC/LB 同 m 同值），HDC 去 tag f 相对 NB 差为 0，未低 > 0.05；且 HDC FER 全 1.0（§2 各臂行；`sf_success` 全 0），NB FER 为 0.03–0.10 量级（M0 §§2.1–2.3 指针：1M 0.097561/0.063415；1p5M 0.076655/0.034843；2M 0.057441/0.041775，F9(i) u2-only 约束下引用）。
  - **分支 (2)（分层二元 ≥ NB，f 更优或持平）**：**不满足**。LB `f_notag` 同 m 同值（同上），无更优；LB FER 为 0.996–0.999 量级（RESULT §2：1M 0.996341/0.997866；1p5M 0.998911/0.998693；2M 0.999510/0.999510），远差于 NB 同帧对照。
  - **分支 (3)（否则）**：**触发**。⇒ **NB 主线进 M3（码设计）**。
- 作用域：D2 只决定后继主线方向；它不是 P3 verdict，不放行任何 P3 门控动作，不产生 SKR/发表主张。对外数字只能来自真实帧实测本身。

---

## §4 已知缺口保留（END/backend；本文件不补写）

1. **END/exit 行未落盘**（RESULT §1/§7 已声明）：三源进程已退但 stdout 终态 END/exit（或等价终态 JSON）行磁盘上无产物；COMPLETE 判据为机内三项（`summary.verdict=COMPLETE` + `rows` 行数 = decodes + `slice_match=True`）。终端行字面留痕待发起执行的会话另行补录；补录前不得虚构 END/exit 原文。
2. **`backend_used` 声明待补**（RESULT §7 已声明）：三根 `rows.json` 内 `grep -c backend_used` = 0（均缺失）；译码后端 pin 以 PREREG/PROMPT 快照（assumed-v1 / verbatim F2+F3）为准，本文件不得猜写具体后端字符串。待主线程核对执行面 pin 后补声明。

---

## §5 保护洁净（doc-only 固化）

- 本文件为本次允许的新增文件之一（另见 decision-log 2026-09-26 节）；包/输出根/数值、执行、commit/push 均未触。
- `src/` / `experiments/` / `tools/` 零改；`results/`、`comparison_bench/outputs_comparison/` 零写；未重跑、未续跑、未重算数值。

---

## §6 主线程接受（用户签字；当前 BLANK）

- 主线程接受：**BLANK**（待用户签字；签字前不得视为接受、不得进 M3 执行）。
- 独立 Pre-RESULT：本文件 §1 **PASS with comments**；FAIL 项为零。
