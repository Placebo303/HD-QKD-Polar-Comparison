# S0.1 m=200 探针 — Batch-End 独立评审（G-S01M200，EXPLORE）— 2026-09-22

- 评审性质：**EXPLORE batch-end 独立评审**（AGENTS §10.3；packet §4 / §6.3 指定单次评审，无逐臂评审）。
- 评审者：reviewer-go（独立 batch-end 评审，只读 + 新建本文件；**未执行任何解码、未改任何执行证据、未 commit/push**）。
- 评审对象：`S0_1_M200_PACKET.md`（§10 授权块已填 G-S01M200 双 UUID 预算日期）+ `S0_1_M200_PROMPT.md` + `S0_1_M200_PREEXEC.md`（Q0–Q6）+ Q5 DRY-PASS + `S0_1_EXPLORATION_LOG.md` 条目 0–3（177 行）+ 两臂证据 `workspace/S0_1/S01-R1_6e48f11e/`（79/240，0.329167，u79，871.9 s）+ `workspace/S0_1/S01-R2_b74322cf/`（119/240，0.495833，u116，1010.5 s）+ focused 测试 19 passed。
- 基线 / 分支：`85e0771f` / `formal-ir-v72p1-addendum-clean`（未切分支；复证一致）。

## 裁决：PASS_WITH_FINDINGS（S0.1-gate PASS；零阻塞项；4 项非阻塞发现）

```
Verdict: PASS_WITH_FINDINGS
```

- **S0.1-gate（packet §4）：PASS** — 两实例 m=200 软边际基线 FER 实测存在（各臂 240/240 完整、non-wall-partial、verdict COMPLETE）。P1 救援臂进入其自己 packet 冻结/授权序的前置条件（"禁止按 10/240 外推冻结 P1"禁令所缺的实测锚）**现已满足**；但本评审不授权 P1 任何执行。
- Blocking Issues：**无**。
- 本批证据可晋级引用（必须两实例分列；任何合并含 6+4 式求和仍禁止）。

## 1. 授权边界 — PASS

- packet §10(d) 为**唯一授权填充处**：Acceptance ID `G-S01M200`；grant verbatim `G-S01M200 GRANT：授权S0.1 m=200探针执行（2臂 S01-R1/S01-R2 ×240块禁合并，双旗标 --execute-real --execution-authorized，预算≤3600s/臂、≤7200s总、≤300s/调用、RSS<2GiB、1CPU）`；臂根 UUID `S01-R1_6e48f11e` / `S01-R2_b74322cf`；预算 6 项全确认（①单臂 wall ≤3600 s 单窗口 ②批次总 ≤7200 s ③单调用 ≤300 s 超时终态计 fail 不续跑 ④RSS <2 GiB ⑤1 CPU ⑥零 `.ttbin`/零真实数据/零 `results/` 与 `outputs_comparison/` 写入）；日期 / 主线程 **2026-09-22 / main**。
- 日志条目 0 顶部 grant 逐字一致（UUID/预算/日期一致）；条目 0 明确"授权块唯一填充位置 = packet §10(d)"，本日志 grant 仅为逐字保留副本，不构成第二授权源。
- PREEXEC 授权块留白（§授权块空白待签，未填 = 未授权），prompt 自声明"授权任何执行 = 0" — 三文件权责一致，无自行填写。
- `git diff -- S0_1_M200_PACKET.md` 仅 1 行变更（空白授权块 → 已填块），冻结科学输入 F1–F10 零改动。
- 授权范围正确收敛：仅覆盖本包 2 臂；"不授权 P1/P5/任何认证句/commit/push"已声明。

## 2. 机器门 — 全部 PASS（逐项复证）

| 门 | 冻结要求 | 复证 |
|---|---|---|
| 完整性 | 两臂各 240/240，禁 bar-12 早停 | R1 `blocks 240/240 run`、R2 同；csv header+240 行、rows.json rows len 240、summary blocks_done 240 / target 240；bar-12 仅 `route_ctx` 文案（两臂皆 `route-ctx FAIL` report-only），主循环无 k 阈值分支（Q2 测试钉 + 实际 k=79/119 仍跑满）。PASS |
| 失败保留 / 修复 | 失败保留不续跑；至多 1 次预注册工程修复；未用写明 | 条目 1–2 各一次调用即 COMPLETE，无 INCOMPLETE-wall、无失败尝试；条目 3 明确 `未用修复路径声明`（零重跑、科学输入/种子/阈值/数据角色/假设全程未变）。"no repair path used"语义满足。PASS |
| undetected 隔离 | 非 exact_match 计 fail 入 k；综合征有效不匹配单列 undetected，永不并入 success | R1 u=79=k（全 undetected）；R2 u=116 ≤ k=119（含 3 detected）；csv `undetected=1 ⇒ failed=1` 零反例（undet-not-failed=0）；json↔csv 零 mismatch；md/log/summary 三处分立字段。PASS（行级 `status` 字符串问题见非阻塞 F1，不影响 k 会计） |
| 禁合并 | 两实例分报，禁 6+4 式求和 | md/log/summary 全为逐臂自有 k/FER/f_eff；claim-ceiling 行逐件声明禁 pooling。PASS |
| f_super / f_eff 双数 | f_super=(5·200+64)/852.544 单基；f_eff=f_super+4.785675·FER（本臂 k）；绝不混报 | 两臂 `f_super=1.2480294272`（字面 1.24803）同基单列；f_eff 独立复算 R1 `1.2480294272+4.785675·79/240=2.82331411` ≡ 2.823314、R2 `…·119/240=3.62092661` ≡ 3.620927；md 强制两行分立。PASS |
| N_req report-only | N_req=⌈3·4.785675/(1.3−1.24803)⌉=277，仅 report-only | 独立复算 `ceil(14.357025/0.0519705728)=277`；两臂 md/summary 均标 report-only，k≠0 下零失败规则不适用声明正确。PASS |
| 预算 | ≤3600 s/臂、≤7200 s 总、≤300 s/调用、RSS<2 GiB、1 CPU | R1 wall 871.9285 s、R2 1010.4905 s（各 ≤3600）；合计 ~1882 s（≤7200）；块 wall 最大 R1 18.30 s / R2 70.53 s（300 s 帽零触发）；RSS 0.165 GiB（<2）；1 CPU。PASS |

## 3. 证据一致（RESULT ↔ rows.json ↔ csv）— PASS

- **R1**（2026092001，girth 8）：md `k=79/240, FER=0.329167, u=79, iters 8/81, wall 871.9 s` ↔ json summary `failures=79, fer=0.3291666…, undetected=79, iters 8/81, elapsed 871.9285 s` ↔ csv 240 行 `failed 真值 79, undetected 真值 79`。seeds 连续 `2026095601..2026095840`（240 唯一）、block_idx 240 唯一、json-vs-csv 全字段 0 mismatch。FER/f_eff 为 6dp 舍入（79/240=0.3291666…→0.329167），复算一致。
- **R2**（2026092011，girth 6）：md `k=119/240, FER=0.495833, u=116, iters 8/300, wall 1010.5 s` ↔ json `failures=119, fer=0.4958333…, undetected=116, iters 8/300, elapsed 1010.4905 s` ↔ csv 240 行 `failed 119, undetected 116`。seeds/block 同上连续唯一；json-vs-csv 0 mismatch。组合分布 (decoded,failed,undetected)：R1 (1,0,0)×161 + (1,1,1)×79；R2 (1,0,0)×121 + (1,1,0)×3 + (1,1,1)×116。
- csv column 与 X1 同构（`block_idx,seed,iters,wall_s,decoded,failed,undetected,prior_entropy_bits,u1_mismatches`）；rows.json `{rows: 240, summary}` 结构两臂一致。

## 4. Pre-EXECUTE 与测试 — PASS

- Q0 分支/基线一致（`formal-ir-v72p1-addendum-clean` @ `85e0771f`，未切分支）。Q1 范围清洁：3 件 additive（runner + 单文件测试 + PREEXEC），`git diff -- src/` EMPTY（0 字节，复证）。Q2 F1–F10 代码面逐项钉死（测试名一一对应）。Q3 输出缺席（执行前 `workspace/S0_1/` absent → 双 UUID 根必然缺席）+ rg 命中限于包族（runner/test/packet/prompt/preexec/log + `docs/NOW.md:14` 基线既有指针，未修改）+ 保护根快照（`results/` 0 文件；`outputs_comparison/` 1446 文件 / 554423395 字节）+ `git diff -- src/` EMPTY。
- Q4 focused 单文件 fake-only 测试：`comparison_bench/tests/test_s01_m200_runner.py` **19 passed**，输出原文附于 PREEXEC §Q4 与日志条目 0（仅运行时间 5.28 s vs 3.79 s 差异；warning 为已知良性 `cache_dir` 提示）。全 fake-only（tmp 合成 npz 注入，零生产解码）。
- Q5 DRY-PASS：PREEXEC 原 PARTIAL（字面量 PASS ∪ F6 实测 PENDING）已被日志条目 0 **supersede** — Grant 后首臂前补跑 `--dry --construct-pins`，`decode_calls: 0`，`family_exists: false`，F6 实测两实例 `four_cycles=0 / rank=208 / twice-identical=true / base_rank=200==200 / girth 8,6 recorded-not-gated`。Q6 闭合（H0.1=SATISFIED 经 `051e3687` 祖先链；授权后首臂前零生产解码）。
- Q1 复测时 PREEXEC §Q3 登记 `workspace/x1_*` 实测 16 目录 vs packet 文 15 — 已登记为观察值，不改冻结项（见非阻塞 F3）。

## 5. Claim ceiling — PASS

- 合成探针定位一致：逐件（md/summary/log 条目 1–3）均载 claim-ceiling 行 — 合成 paired-frame m=200 软边际效率探针（per-instance k/240 + 冻结基 f_super/f_eff + iters/wall + undetected 单计数）作 P1 Stage-1 实测锚；**非** SKR/资格化/路线裁决/运行点/真实 FER/可认证或文献可比 f_eff 句/发表材料；key-eligible 200/276/364 引用未消耗；X1 joint-∅ 结论未被触碰。
- 无跨 m 单调性推断、无 f_super 引作 f_eff、无真数据句。EXPLORE 五资格满足（合成已批准输入、fresh additive 可逆有界、无主张、无破坏覆盖、无对外动作）。

## 6. 范围 — PASS（无 scope creep）

- `git diff -- src/` EMPTY；禁碰文件（EXECUTION_PLAN/NOW/.gitignore/README/AGENTS/`src/`/`experiments/`/`tools/`）零修改（packet 授权行 1 行填写除外，为设计内唯一允许变更）；禁写根（`results/`、`outputs_comparison/`）零写入；既有证据根只读；禁跑 `longrun_*/minrerun_*/routeA_*/run_e2e_pipeline.py` 零调用；无 P1/P2/X1 臂执行；无解码器/DE/图核改动；gamma 只读（g1 (32,1024)、g2 (32,32,1024)、sidecar 同胞）。

## 非阻塞发现（F1–F4，无需重跑，不改证据）

- **F1（行级标签清晰度，唯一值得记录项）**：per-block `status='success'` 被用于 undetected 失败行（R1 79 行、R2 116 行呈 `(status=success, failed=1, undetected=1)`；`decoded` 恒为 1，含 3 行 `max_iter_reached` detected 失败亦 `decoded=1`）。Summary 级 F10 满足（k 会计正确、undetected 单列永不并入 success），冻结 §3 schema 未定义 `status`/`decoded` 列故不构成冻结违反；但**下游严禁按 `status` 或 `decoded` 聚合成功数，唯一权威列是 `failed`（k）与 `undetected`**。建议后续 runner 文档注释 `decoded`=解码器返回/综合征有效完成、`failed`=exact_match 否决权威、`status` 改名（如 `undetected`）或补充说明；本批证据不重写（append-only + 失败保留原则）。
- **F2（信息性）**：R2 出现 3 行 `max_iter_reached`（iters=300）detected 失败 vs R1 0 行 — 已正确计入 k，无 wall 帽触发（块 wall 最大 70.53 s < 300 s），证明 max_iter=300 守恒上限活跃。非异常。
- **F3（已登记观察）**：`workspace/x1_*` 计数 16 vs packet 文 15 — PREEXEC/日志已登记为观察值，无冻结变更，无需动作。
- **F4（舍入注记）**：md/log 的 FER（0.329167/0.495833）与 f_eff（2.823314/3.620927）为 6dp 舍入；json 存全精度 float，复算一致。下游引用建议同时保留精确分数（79/240、119/240）。

## 主线程 route 建议（P1 Stage-1 锚消费）

1. **锚输入（分列消费，禁合并）**：`m_base=200` nested leading-200（rows[0,200)，非 A200）两实例 FER — **S01-R1（2026092001，girth 8）：79/240 = 0.329167，u79**；**S01-R2（2026092011，girth 6）：119/240 = 0.495833，u116**（配套 f_super=1.24803 同基、f_eff 2.823314 / 3.620927、N_req=277 ro、iters/wall 见上）。任何引用必须两实例分列；单实例冒充结论、跨实例 pooling（含 6+4）继续禁止。
2. **禁令状态**："S0.1-gate 未 PASS 前禁止按 10/240 外推冻结 P1"禁令**已满足**（锚存在）。但 10/240 仍只是算术引用（E[leak]=1065.7 b ⇒ f≈1.250 ⇒ N≥288），不是实测量；P1 冻结时仍须按其自己 packet 另行授权，本 grant（G-S01M200）不延续。
3. **bar-12 解读**：两臂 `route-ctx FAIL`（79、119 > 12）为 report-only 上下文，不是路线裁决；路线裁决是主线程后续决定，不在本批。
4. **下一步**：P1 Stage-1+Stage-2（Δm=8 救援）仍未测 — 本批只测 k，不测救援；P1 packet 冻结时以前述分列锚为输入，救援机制前提仍待实测。关闭后按 AGENTS §3 由主线程执行 memory triage（本评审不代执行）。

## 评审方法与边界声明

- 方法：只读复算（json/csv 交叉计数、f_eff/N_req 独立复算、seeds/block 连续性、git 范围/rg 检查、packet 单行 diff 检查）；**未调用生产解码 runner**，未执行测试长跑（Q4 输出为执行前附录引用），未修改任何执行证据，未创建除本文件外的新文件，未 commit/push。
- 日志 177 行、条目 0–3 append-only（条目 0 原样保留、条目 1–3 append）满足 EXPLORE 合约（一个 packet+prompt 对 + 一个 log + 一次 batch-end 评审 + 一次授权覆盖冻结臂序 + 零修复未用声明）。

---

Checklist:
- [x] Matches OpenSpec spec（packet F1–F10 / §§3–5/§§8–10 逐项满足；唯一变更为设计内授权块填写）
- [x] Tests pass（focused 单文件 fake-only 19 passed，输出附录于 PREEXEC §Q4 与日志条目 0）
- [x] No scope creep（`git diff -- src/` EMPTY；rg 限包族；禁写/禁跑/禁碰项全守）
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? — 本批为合成探针、无新失败模式（F1 为既有标签风格问题，已在本文件记录；如主线程认为 F1 值得复用，关闭时可追记 troubleshooting 一行，不阻塞晋级）
