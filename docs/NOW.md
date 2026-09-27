# NOW — 一屏现状（2026-09-27，docs-only）

> 新会话只读本页 + `docs/EXECUTION_PLAN_20260922.md` 即可接手。
> 本页不授权任何执行（无解码 / DE / 真实数据 / commit / push / 资格化 / 发表）。
> Track：documentation-only（AGENTS.md §1.2 矩阵，无 track gate）。

## 1. 分支 / HEAD / 脏树（读取于 2026-09-27；**任何执行前必须重测**）

- 分支：`formal-ir-v72p1-addendum-clean`（实测）。
- HEAD：`ce85d61f`（full `ce85d61f5f625a323765481cb726f77e0380b86a`；2026-09-23 页所记 `8e9c8526` 已过期）。
- 工作区（`git status --porcelain` 2026-09-27 实测）：
  - tracked dirty **6**：`M AGENT_PROJECT_MEMORY.md`、
    `M comparison_bench/src/comparison_bench/cli/p1_stage1_runner.py`、
    `M comparison_bench/src/comparison_bench/formal_ir/v80_b2f_campaign.py`、
    `M docs/NOW.md`、`M docs/decision-log.md`、`M docs/troubleshooting.md`
    （本页 `docs/NOW.md` 自改动起恒为 ` M`——自指快照不含本页）；
  - 未提交（untracked）**71 条目**（按 porcelain `??` 条目计），构成为：
    M0/M1/M2/M3 周期目录（`M0-REALFRAME`、`M1-FINITE-LENGTH`、
    `M2-HDCASCADE-SYNTH`、`M2-LAYEREDBIN-SYNTH`、`M2-REALCOMP`、
    `M3A-NESTED-200P8`、`M3B-NESTED-PAIRED`、`M3C-REAL-U2-2M`、
    `M3D-ITER250-SYNTH`，另加 `EXPLORE-20260923-DIMENSION-PROBE`），
    `comparison_bench` 新 runner（`m0_realframe_runner`、`m2_accounting_replay`、
    `m2hdc_arm_runner`、`m2lb_arm_runner`、`m2real_runner`、`m3a_nested_construct`、
    `m3b_paired_synth`、`m3c_real_u2`、`m3d_iter250_synth`、`p4_feas_construct`、
    `timing_probe_runner`）、新方法（`binary_spa_numpy`、`hd_cascade`、
    `layered_binary`）与 fake 测试约 16 件，V80 周期文档约 15 件，
    OpenSpec 变更目录（`m2-honest-baselines*`、`m2real-accounting-correction`、
    `m2real-accounting-replay`、`m2real-runner`、`m3a/b/c/d-*`、
    `p4-feas-construct-runner`、`same-data-comparison-metrics`），
    另加顶层 `POLAR_VS_LDPC_CROSS_REPO_COMPARISON_20260927.md` 与
    `RESEARCH_DIRECTION_REPORT_20260924.md`。
- **PR #1 仍 OPEN**（base `formal-ir-v80-nbldpc-jan21`，未 merge）。
  **M0/M1/M2/M3 工作均未提交**——以上脏树即当前全部未入库工作。
- **注：以上仅为读取时点记录；任何执行前必须重测分支 / HEAD / 脏树。**

## 2. G0 裁决与路线顺位（冻结前提，不是授权）

- **G0 = (B) 已裁决**（2026-09-22 用户书面给出）：主文主张 =
  实测效率曲线 + 同数据二元 MLC/R3 对照；(A) 文献可比认证作
  并行/第二代扩展。
- **F3（G0=B 范围裁定，decision-log:4855）**：ROADMAP「P1 失败 ⇒ P4 在 S3 之前
  成为必经」分支被本裁决取代——**P4 不因 P1-FAIL 自动升为 S3 必经**，n=2048
  定位**第二代并行**，不阻塞 S3。
- **用户路线顺序（冻结前提）**：**① P4-elevation → ③ 并行（P4 构造可行性 +
  P3 包冻结同时推进）→ ② S-B 窄路**。2026-09-23 落档把 P1 Stage-1 判为
  **P4-elevation 输入**（decision-log:4885），**不是** P1-PASS 门票。
- **范围观察（已裁定，非新主张）**：M2 同数据比较现为一工作方法
  （NB-LDPC）+ 两个已记录的负实现结果（HD-Cascade 0/28,000、
  Layered-Binary 36/28,000；见 §5 D-4/D-5），任一基线均无可填比较列，
  比 `RESEARCH_DIRECTION_REPORT_20260924.md` §0/§5 的三方法表
  更接近 G0=(B) 头条主张。原“两方法表”预期已由 T4 接受纠正，
  不再引用。

## 3. 已接受证据（含范围上限；均不含新的执行授权）

- **M0 真实帧**：独立 Pre-RESULT PASS；真实 FER 在 6 臂中 5 臂差于合成——
  合成信道尚未成为可信开发代理，真实帧之前须先做信道条件化。
  M0 为 u2-only 链（u1 经 argmax 全局恢复、未编码未验证），引用必须带标注。
- **M1 有限长复算**：`PASS_WITH_FINDINGS`；f* 约 1.064，分解为码差距约 0.13 /
  有限长约 0.06 / 64-bit tag 约 0.075；任何引用必须写清所用 H 基。
- **M3A 嵌套 200+8 构造**：批末 PASS，**仅构造可行性**（两组固定种子图满秩、
  四环为零、girth 6），不等 FER/泄漏/效率改善。
- **M3B 配对合成**：批末 PASS；Stage-1 非 exact 由 84/240、138/240 降至
  10/240、15/240，最终失败 0/240；两实例分别报告、**不合并**，**仅合成**。
- **M2-LB 合成 12 臂**：批末已关闭但定位 retained-assumed（后端恒为
  `numpy-minsum-fallback (assumed)`），禁 promotion。
- **H0.1** scoped 提交 `051e3687`；**H0.2** 具名分支推送 + PR #1 OPEN。
  **S0.1-gate PASS**（decision-log:4861）；P1 Stage-1 批末
  `PASS_WITH_FINDINGS` 但无一臂全过三门，G-P1S1 授权已用完。

## 4. 未接受或已停止（本节任一条均不得引用为正面结论）

- **M2 真实比较**：会计纠正 T0–T4 已完成并接受——接受对象仅为
  存量披露算术 + 诚实标签（T2：12/12 逐位精确；T3：PASS_WITH_FINDINGS
  零阻塞；T4 用户原话「可以接受这些」2026-09-27）。主线程科学接受
  **WITHHELD** 不变，五个阻塞发现不变。终点交付物为一工作方法
  （NB-LDPC 真实帧实测）+ 两个负实现结果（HDC 真实 `exact_match`
  28,000 块全 0；Layered-Binary 36/28,000、0.13%，块 FER
  0.9963–0.9995、超帧成功全 0），任一基线均无可填比较列，
  其 `leak_EC` 及一切派生列均附 `void-no-correction`，
  永不进排名。另见本页 §5 D-5：LB 验证路径有效（系弱译码器
  非硬门），`void-stub-artifact` 不适用于 LB。结构注记：
  旧展示 f（`f_notag = 5m/(1024·H)`）公式内根本无泄漏项，
  只取 `(m, H)`，跨族相等系机械强制（1M/m=197 两臂同列
  1.20048829，实测泄漏差 2.64x），该列在结构上无法区分方法。
- **M2-HDC 合成**：批末 **FAIL**，仅作边界干净执行记录与 harness 缺陷展品。
- **M3C 真实 2M 两臂**：**STOP**——R1 COMPLETE（383/383，372 最终 u2 成功），
  R2 `INCOMPLETE-wall`（352 成功 / 7 失败 / 24 未知，无 383 帧 FER），
  故无两图决定、无 FER/泄漏/f/SKR 结论，不接受。
- **M3D**：R1 批 FAIL（运行时门未过），R2 按冻结包正确未跑，批末审查仍待补。

## 5. 已作决定与开放项

- **D-1（tag 验证单位）**：**DEFERRED**，非阻塞；tag 总数继续分列、
  单 tag 列保持反事实标注；待冻结协议规范裁定 headline 列。
  D1 tag-unit 分析 memo（`docs/research_cycles/V80-NBLDPC-JAN21/D1_TAG_UNIT_MEMO_20260927.md`）
  已存在，仅为分析，不授权任何事，不改变任何数字；D-1 仍 deferred。
- **D-2（HDC/LB 的 `f_eff`）**：**DROPPED**；重引入须新预注册的方法专属
  单位一致定义，NB 1024 符号超帧斜率永不得默示复用。
- **D-3（D2 规则）**：**D2 在 M2 退役**；M2 无有效输入，后继经 M0/P1 实测
  缺口路由；范围仅限 M2。
- **D-4（HD-Cascade 列）**：**选项 (iii)**——HDC 作为已记录的负实现结果，
  每个 HDC 数字附双 void 标注，披露列标注
  `exhausted assumed schedule on uncorrected blocks — not a method property`。
  选项 (ii)（接真 verifier、新根重跑）已考虑并否决：它只改 `undetected`
  标签，不改变 `exact_match`、`leak_EC`、FER 任一值。
- **D-5（Layered-Binary 列）**：**与 D-4 平行处理**——LB 真实帧仅纠正
  36/28,000 块（0.13%），其披露及一切派生列附 `void-no-correction`，
  作已记录的负实现结果；备选 (ii)（去 void 标签裸留披露数）已否决，
  因其诱发本变更旨在阻止的排名解读。并行授权只读溯源——不重译码、
  不新执行，仅搜三源 M2 根与邻近记录有无现存后端痕迹。

## 6. 活跃门（PASS 已注出处；未过 = 对应动作禁止）

| 门 | 状态 / 含义 |
|---|---|
| **S0.1-gate** | **PASS**（2026-09-22，decision-log:4861）→ P1 Stage-1 锚就绪 |
| **P3-gate** | **未过**：re-freeze v2 仍 PROPOSED，授权签字块 BLANK ⇒ **禁把合成 FER 当真实 FER** |
| **P4** | **FROZEN NOT GRANTED**：授权块空白 ⇒ **禁任何构造执行**；只产可行性证据 |
| **P5-gate** | **需独立冻结**：未冻结前不可启动 |
| **P6-gate** | **未量化**：吞吐缺口未量化 ⇒ 禁「真实场景可用」句 |

## 7. 禁止事项（全文有效）

1. **禁单点 `f_eff ≤ 1.3` 认证句**：N_req 超出 key-eligible 块数。
2. **禁 merge 姊妹线**：不把 `polar-mainline` / 姊妹 checkout 内容并入本线，
   也不向姊妹线分支推送；发布只走命名 formal-IR 分支 + PR，普通非强制 push。
3. **禁 `git add -A`**：只按 scoped manifest 提交。
4. **每个 HDC 与 Layered-Binary 数字必带 void 标注，永不进跨方法排名**；
   HDC `f_ec_actual` 约 9.8–10.2、LB 约 3.8–3.9 均不得读作方法优劣，
   不得填入任何比较列。
5. **禁 Layered-Binary 后端推断**：真实后端 unknown，在案缺失即缺失，
   不得以合成批或现装环境推断。
6. 本页与计划均不授权执行；每个 EXPLORE/DECIDE 包仍按
   AGENTS.md §1.2 / §10.3 独立授权与评审。

## 8. 权威指针（细节按此顺序下钻）

1. **PLAN** — `docs/EXECUTION_PLAN_20260922.md`（排期、门禁、卫生轨）
2. **ROADMAP** — `docs/ROADMAP-20260921.md`（科学宏观路线 P0–P6、DECISION）
3. **BASELINE** — `docs/V80_BASELINE_20260921.md`（冻结科学口径）
4. **cycle** — `docs/research_cycles/M0-REALFRAME/`、`M1-FINITE-LENGTH/`、
   `M2-REALCOMP/`、`M2-HDCASCADE-SYNTH/`、`M2-LAYEREDBIN-SYNTH/`、
   `M3A-NESTED-200P8/`、`M3B-NESTED-PAIRED/`、`M3C-REAL-U2-2M/`、
   `M3D-ITER250-SYNTH/`（专题证据与 log）
5. **M2 会计 OpenSpec** — `openspec/changes/m2real-accounting-correction/`
  （MAC-1..9，design §1..§12，`void-stub-artifact` / `void-no-correction`）
6. **HDC 批末审查** — `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md`
  （FAIL）；**M3D 包与 Pre-EXECUTE** —
   `docs/research_cycles/M3D-ITER250-SYNTH/`

**冲突规则**：**科学口径以 ROADMAP / V80_BASELINE 为科学权威**；排期与卫生动作以
PLAN 为准；README / HANDOFF 状态段、**旧状态页与探针历史措辞仅作历史指针，不得
重定路线**（重定路线只能经主线程 + ROADMAP / V80_BASELINE 修订）。本页与上述任一
权威冲突时，一律以 ROADMAP / V80_BASELINE 为准。
