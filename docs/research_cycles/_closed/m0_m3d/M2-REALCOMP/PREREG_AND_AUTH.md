# M2 真实同帧三方法比较 — PREREG_AND_AUTH（DECIDE，compact 三文件形式）

- **Acceptance ID**：`G-M2-REALCOMP`
- **Track**：**DECIDE**（真实数据 / 同帧三方法比较 / 执行代价与发表前主张；AGENTS.md §1.2 矩阵 "Real-data development/validation"）。
  本次起草 = **doc-only 包起草，无 track gate**；**FUTURE 执行 = DECIDE**（完整门：已接受预注册 + Pre-EXECUTE + 显式用户授权 + 执行记录 + 独立 Pre-RESULT + 主线程接受）。
- **状态**：FROZEN — **已授权 2026-09-25**（§6 已填；用户原文 + 主线程覆盖 `G-M2-REALCOMP` 见证；执行仍须 Pre-EXECUTE 全 PASS + 独立 Pre-RESULT）。
- **分支冻结时点**：`formal-ir-v72p1-addendum-clean` / HEAD `ce85d61f`（parent `8e9c8526`，FF linear；8e9c8526..ce85d61f 仅 `m2-honest-baselines/design.md` + `specs/methods/hd-cascade.md` doc-only +86 行，M1 零触及，formal-ir 线未污染；重测记录见 §3）；**执行前必须重测分支/HEAD**（§3 清单独列；HEAD 已移动则复核 diff 范围，不 silently 沿用旧值）。
- **与 M0 的关系**：M0 后继。NB 臂引用 M0 已测值（artifact 指针），**不重跑**；新增两方法臂在 M0 同一 eval 超帧上实测。
- **配套执行面**：`M2-REALCOMP-PROMPT.md`（同一授权边界）。执行后：`RESULT.md` + `INDEPENDENT_ACCEPTANCE.md`。

---

## §0 身份（G-M2-REALCOMP）

| 项 | 值 |
|---|---|
| Acceptance ID | `G-M2-REALCOMP` |
| Track | DECIDE（本次起草 doc-only 无 gate；FUTURE 执行 DECIDE） |
| Gate 状态 | 已授权 2026-09-25；§6 已填（见 §6） |
| 分支 / HEAD（冻结时点） | `formal-ir-v72p1-addendum-clean` / `ce85d61f`（parent `8e9c8526`，FF linear；执行前重测，记录见 §3） |
| 前件 | `docs/research_cycles/M0-REALFRAME/{PREREG_AND_AUTH.md,RESULT.md}`；decision-log 2026-09-24 条（含 F9(i) 裁定）；`SAME_DATA_CMP_METRICS.md`；`openspec/changes/m2-honest-baselines/design.md`（T0）；`docs/research_cycles/M2-HDCASCADE-SYNTH/PACKET.md` |

---

## §1 冻结输入 F1–F5（与 M0 逐字同，唯二改动见 F6–F7）

| # | 项 | 冻结值（M0 逐字） |
|---|---|---|
| F1 | 数据 | Jan-21 Type2 三源，只开 base `X.ttbin`（R1 JSON `ttbin_member_used`）：1M `…/Type2_1M_3s_2026-01-21_184040.ttbin`；1.5M `…/Type2_1-5M_3s_2026-01-21_183806.ttbin`；2M `…/Type2_2M_3s_2026-01-21_183657.ttbin` |
| F2 | 读取 / 对齐 / 配对 / 分帧 | 冻结 A1 / R1 链逐字：`read_ttbin_events` → `align_wrapper.derive_alignment`（§3A 门）→ `_pair_nearest_unique`（窗口 200 ps）→ `_frame_global`（200 ps × 1024 bins）。**断言**：派生偏移 = R1 偏移（−50 / +50 / +50 ps）；配对数 = R1 `n_pairs_N`（525831 / 735780 / 982182）；60/20/20 切分边界 = R1 `split_manifest.json`。任一不等 ⇒ STOP |
| F3 | eval 区 | 按时间排序后的 VAL+HOLD 帧（后 40%）；切成**连续、不重叠的 1024 符号超帧**，余数丢弃并报告。实测 **205 / 287 / 383**（M0 已测；余数 407 / 405 / 529 符号已丢弃） |
| F4 | 先验 | **同源 R1-TRAIN 分解**，只读、永不重拟合：1M / 1p5M ← `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz`；2M ← 同目录 `x1_gamma_f03r1_2M_verify.npz`。经冻结 `s2c.bind_empirical_bundle` 校验。**理由**（M0 F4 逐字）：TRAIN 与 eval 帧在同一切分上，可证不重叠；2M 的历史 `gamma_f03.npz` 来自 V25 年代的另一套 TRAIN（N=559872 ≠ R1 的 589461），无法证明与 eval 不重叠。两者 H 差 0.0006 b/符号（X1 验证日志） |
| F5 | 码（NB 臂）与译码 | `x1_arm_runner.construct_standalone(m)`：PEG，λ={2:1}，实例 2026092001，trials 20；构造两次须完全一致 + fc=0 + rank=m（否则 STOP）；girth 记录不设门。译码 b2f 软边际逐字：Alice x = a & 31，Bob y = b & 31；`marginal_prior_l2` → `center_rows_prior` → `decode_error_domain_posterior`，max_iter 300，streak 3。奇偶校验语义沿用 M0 F7：已确认在同一合成抽样上两条路径给出相同结果。**成功 = u2 精确匹配**（V80 冻结口径）；undetected = 收敛但错（计失败，永不并入 success）；单次解码 > 300 s = 失败（终态，不重跑） |

**唯二改动**（除 F3 205/287/383 实测值 + 余数 407/405/529 填充外，F1–F5 一字不改；改任何一项 = 新包）：

- **(i) 新增两方法臂**：HD-Cascade + 分层二元 LDPC。实现版本以 T0 design pin 为准（执行前在 PROMPT 登记 commit pin）；HD-Cascade二进制映射为10bit→appropriate binary representation（Gray无原文依据，永标assumed，按Müller原文ar5iv 2307.02225v2 §2.3.2/Table 2）；assumed-v1 provisional值（[8,4]/max_passes 4/sweep 1/消息公式）非原文，真值为QBER-自适应k1..k6公式，n=2^16 bits；**Mueller 歧义处引用"待澄清表"，不猜数**（歧义项须经 `/opsx-explore` 冻结后才可实现）。
- **(ii) 真实 (a, b) 切片替代合成采样**：新方法臂用与 M0 同一批真实 (a, b) 超帧切片；零合成采样混入真实臂。

### 帧集澄清（两列分立，禁混用）

- 复用 M0 **同一 eval 超帧**实测 **205 / 287 / 383**（同一切分、同一超帧边界；余数丢弃 407 / 405 / 529）。
- `key-eligible` **200 / 276 / 364** 是**认证计数**，作 `N_req` report-only 对照列（A-CMPE-5），**不是** FER 分母。
- 两列分立：FER 分母列（205/287/383）与 key-eligible 对照列（200/276/364）**禁止混用、禁止合并**。

### 臂表（每源 × 3 方法 × 2 m；逐源逐臂分列，禁跨源跨臂合并）

| 源 | NB 臂（M0 已测值引用，不重跑，artifact 指针） | HD-Cascade 臂 | 分层二元臂 |
|---|---|---|---|
| 1M | m ∈ {197, 201}（`docs/research_cycles/M0-REALFRAME/RESULT.md` §2.1） | 同超帧 × m ∈ {197, 201} | 同超帧 × m ∈ {197, 201} |
| 1.5M | m ∈ {203, 207}（同上 §2.2） | 同超帧 × m ∈ {203, 207} | 同超帧 × m ∈ {203, 207} |
| 2M | m ∈ {204, 208}（同上 §2.3） | 同超帧 × m ∈ {204, 208} | 同超帧 × m ∈ {204, 208} |

- NB 列：**measured（M0 artifact 引用）**，不重跑、不续跑。
- 新方法列：实测后 **measured**（本包实测，带 artifact 指针）。
- 有限长极限列：**projected**（M1 复算通过前永为 projected，不得升格 measured/qualified）。
- F9(i) 标注义务：**全表强制标注"u2-only, u1 via argmax, u1 正确率未验证"**（decision-log 2026-09-24 F9(i) 裁定）；去标注引用 = 违规引用。
- `fails_full10` 观测列保留（M0 口径逐字：û1 = argmax_u g1[u,b]·g2[u,x̂,b]）；u1 纠错进恢复链 = 新包（M0 数字不得回溯改写）。

### 会计（A-CMPE-1..7 全覆盖，列缺失 = 机器门 FAIL）

每源每臂：`attempted` / `exact_match`（= success = ¬failed；`decoded`≠success 图例）/ `accepted` / `accepted_wrong`（= undetected，独立列，永不并入 success/FER）；
`f_super` / `f_notag` / `f_eff`（本臂 m 基；`f_eff = f_super + 4.785675·FER`）；
`leak_EC` + 64-bit tag ⇒ `λ_total = leak_EC + 64`（+ 控制轮次/控制帧/盲救援段公开量逐项单列；禁合并）；
每源 1.50× prior 机会成本行（不进 f 分子）；
wall（总/每块/每译码）+ 峰值 RSS + 每帧消息数（Cascade 446 vs LDPC 3.14 口径独立标注，两口径不可互比）；
`N_req` report-only vs key-eligible（200/276/364）分列；`d` / `q` / `n_IR` 分离三列；
合成/真实/key-eligible 三组计数分离；measured / assumed / projected / qualified 四列归属（无安全观测量 ⇒ 禁 SKR）。
`H` 用 M0 §3 `H_corr`（0.80127 / 0.82729 / 0.83333，各源自己的 H），永不用合成 F03 H。

---

## §2 预算与停止规则

- 每源 **5400 s** wall 上限（超出 ⇒ `INCOMPLETE-wall`，已写行保留，永不续跑）；单次解码 **300 s**（超出 = 该超帧失败，继续下一个，不重跑）；峰值 **RSS < 4 GiB**（超出 ⇒ `FAIL(budget-rss)` 停止该源）；**1 CPU × 3 并行**（沿用 M0 实测口径）。
- **不重跑、不续跑**：M0 NB 值引用不重跑；新方法臂 grant spent 后无重跑（任何重跑 = 新包 + 新授权 + 新根）。
- 任一 F1–F7 需要改动、或任一断言失败 ⇒ STOP 回主线程。

---

## §3 Pre-EXECUTE 清单（执行前同一会话内重测；任一 FAIL ⇒ 阻塞执行）

- [ ] 分支 / HEAD：`formal-ir-v72p1-addendum-clean` / HEAD 已重测记录（≠8e9c8526 时注明新 HEAD 并复核 diff 范围）
> 重测记录（2026-09-25，doc-only 起草时点）：HEAD `ce85d61f`（parent `8e9c8526`，FF linear；`git log --oneline --all --graph` 单线无分叉）。
> `8e9c8526..ce85d61f` committed diff 仅两件 doc-only（`openspec/changes/m2-honest-baselines/design.md` + `specs/methods/hd-cascade.md`，+86 行）；
> M1（`docs/research_cycles/M1-FINITE-LENGTH/`）该区间零触及；`src/` tracked diff EMPTY；formal-ir 线未污染（同区间无 Polar/sibling 线合并）。
> T0 design pin 快照（`m2-honest-baselines/design.md` §2，2026-09-25 时点）：①②已关闭；③已关闭（B2-App A.2 部分关闭注记），**B3 open**（+ App 剩余）；
> B1 关闭（引文）/ B2 部分关闭 / B4/B5 关闭（planner 2026-09-25）；assumed-v1 provisional（`[8,4]`/max_passes 4/sweep 1/消息公式）非原文，
> 真值 = QBER-自适应 k1..k6 公式（n=2^16 bits）；q=1024 为外推（Müller 实测 q∈{4,8,32}），永标 assumed。
- [ ] 范围：按显式臂清单（§1 臂表：3 源 × 3 方法 × 2 m），无加项
> Scoped 清单（B2；doc-only 起草时点）：
> IN：本包两件（`PREREG_AND_AUTH.md`、`M2-REALCOMP-PROMPT.md`）+ `comparison_bench/src/comparison_bench/cli/m2real_runner.py` +
> 2 fake 测试（`comparison_bench/tests/test_m2real_hdc_fake.py`、`test_m2real_lb_fake.py`）+ `openspec/changes/m2real-runner/` 三件（`proposal.md`、`design.md`、`tasks.md`）。
> OUT：他线 M0/P4/TIMING runner + 4M docs 排除；`src/` EMPTY（tracked diff 零触及）。
- [ ] 输入在：三 base ttbin、R1 `split_manifest.json`、两 bundle 文件存在且只读
- [ ] 输出根：`workspace/m2real_<uuid8>`（uuid8 执行前填入）**缺席证明**已记录
- [ ] focused fake 测试通过（fake-only，零真实数据访问；命令见 PROMPT）
- [ ] 断言：偏移（−50/+50/+50 ps）、配对数（525831/735780/982182）、切分（split_manifest）、bundle H、构造一致性（fc=0 + rank=m + 两次一致）全部 mechanisch 可验
- [ ] 保护根：`results/`、`comparison_bench/outputs_comparison/`、`src/` / `experiments/` / `tools/` 零写计划

---

## §4 D2 规则（逐字预注册；开发决策，不是发表主张）

- **HD-Cascade 去 tag f 比 NB 低 > 0.05** ⇒ 如实报告；NB 改定位为"单向 1 条消息低时延"，给定**时延下密钥吞吐对比**（A-CMPE-4 消息数/时延口径并列，不改写 FER/泄漏数）。
- **分层二元 ≥ NB（f 更优或持平）** ⇒ "高维必须用非二元码"叙事不成立；主线转向**分层二元 + 信道建模**。
- **否则** ⇒ NB 主线进 M3（码设计）。
- D2 只决定后继主线方向；它不是 P3 verdict，不放行任何 P3 门控动作，不产生 SKR/发表主张。
- 权威来源：`docs/decision-log.md`「2026-09-24: M2 D2 三分支预注册阈值裁定」节（主线程裁定记录；流程预注册，非科学结论）。

---

## §5 Pre-RESULT 独立复核清单（独立线程/复核者对照实际产物逐项重算；FAIL ⇒ 不得固化）

- [ ] 阈值重算（D2 三分支条件逐字核对）
- [ ] 泄漏分解（`leak_EC` + 64 tag + 控制项逐项单列；禁不透明合并）
- [ ] undetected 隔离（独立列，永不并入 success/FER）
- [ ] per-source 分列（禁跨源/跨臂合并；205/287/383 与 200/276/364 两列分立）
- [ ] 披露会计（prior 1.50× 行单列不进 f 分子；盲救援段单列）
- [ ] A-CMPE 全列齐全（A-CMPE-1..7）
- [ ] 四列归属（measured / assumed / projected / qualified；有限长极限列仍为 projected）
- [ ] claim ceiling（§8 禁句零违反；F9(i) u2-only 标注全表在场）

---

## §6 授权块（已授权 2026-09-25；用户原文 + 主线程覆盖 `G-M2-REALCOMP` 见证）

- 授权人：用户（主线程覆盖 `G-M2-REALCOMP` 见证）
- 授权日期：2026-09-25
- 授权范围（冻结臂表快照 + 输出根 `workspace/m2real_<uuid8>` + T0 design pin 快照）：§1 臂表（3 源 × 3 方法 × 2 m；NB 为 M0 引用不重跑，新方法 12 臂实测）+ 输出根 `workspace/m2real_<uuid8>`（uuid8 执行前填入）+ T0 design pin 快照（`m2-honest-baselines/design.md` §2：①②已关闭，③已关闭附 B2-App A.2 部分关闭注记 / B3 open；assumed-v1 `[8,4]`/max_passes 4/sweep 1/消息公式 provisional 非原文，真值 QBER-自适应 k1..k6 公式 n=2^16 bits；Gray 永标 assumed；q=1024 外推）
- 预算确认（每源 5400 s / 单解码 300 s / RSS < 4 GiB / 1CPU×3并行）：确认（§2 逐字）
- 签名/确认语：用户 2026-09-25 原文：“'T2 已 CLOSEABLE 待签，T1/T3 未跑'，我都授权可以进行”

---

## §7 验收 ID（G-M2-REALCOMP 子项 E1–E8）

- **E1 范围白名单**：`src/` / `experiments/` / `tools/` 零改；`results/`、`comparison_bench/outputs_comparison/`、M0 文件零写；仅输出根 + 本包文件可写。
- **E2**：focused fake-only 测试 PASS，附输出。
- **E3**：臂数 = 3 源 × 3 方法 × 2 m（NB 为 M0 引用不重跑；新方法 12 臂实测），按冻结臂表，无加项。
- **E4**：冻结断言逐字 = F1–F5（偏移/配对数/切分/bundle/构造一致性）；T0 design pin = 快照值；Mueller 歧义标"待澄清"无猜数。
- **E5**：预算合规（§2）或 `INCOMPLETE-wall` 无 rerun/resume；无单次解码 > 300 s 重跑。
- **E6**：记录字段 = §1 会计（含 A-CMPE 全列；undetected 单列；两列分立；四列归属）。
- **E7**：NB 指针 = M0 artifact 路径逐字；新方法 artifact 落输出根；无跨源/跨臂合并数。
- **E8**：claim ceiling 零违反（§8 禁句 + F9(i) 全表标注 + fails_full10 观测列在场）；独立 Pre-RESULT PASS。

---

## §8 SKR 禁句（claim ceiling）

> 无安全观测量，只能写"实测纠错收益 / 公开开销收益"；禁止 SKR、secure-key、资格化、composable 安全、发表主张。单一构造实例（NB 实例 2026092001；新方法 pin 实例见快照）、单次采集、Jan-21 三源上的开发测量。对外数字只能来自真实帧实测本身。
