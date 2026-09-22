# S0.1 m=200 探针 — Append-Only Exploration Log (G-S01M200)

- Track：**EXPLORE**（`EXPLORE_HEAVY` 成本注记：≤3600 s/臂、≤7200 s 总）。Acceptance ID **G-S01M200**。
- 入口：`S0_1_M200_PACKET.md`（§§1–11 冻结）+ `S0_1_M200_PROMPT.md`。分支 `formal-ir-v72p1-addendum-clean`（不切分支、不 commit、不 push）。
- **本文件 append-only**：条目 0 = Pre-EXECUTE Q0–Q6；条目 1–2 = 逐臂运行（R1→R2）；条目 3 = 收口 tally。保留失败/INCOMPLETE 臂不覆盖、不续跑。无逐臂评审文件；批次末单次独立评审 = `S0_1_BATCH_END_REVIEW.md`（另行指派，不在本任务）。

---

## 条目 0 — Pre-EXECUTE Q0–Q6（2026-09-22，执行前登记）

### 授权（GRANT VERBATIM — 本条目逐字保留）

```
G-S01M200 GRANT：授权S0.1 m=200探针执行（2臂 S01-R1/S01-R2 ×240块禁合并，双旗标 --execute-real --execution-authorized，预算≤3600s/臂、≤7200s总、≤300s/调用、RSS<2GiB、1CPU）
```

- UUID：**S01-R1_6e48f11e** / **S01-R2_b74322cf**；日期 / 主线程：**2026-09-22 / main**。
- 预算 **6 项全确认**：① 单臂 wall ≤3600 s（单窗口）② 批次总 ≤7200 s ③ 单调用 ≤300 s（超时 = 终态，块计 fail，不续跑）④ RSS <2 GiB ⑤ 1 CPU ⑥ 零 `.ttbin`/零真实数据/零 `results/` 与 `outputs_comparison/` 写入。
- 授权块唯一填充位置 = `S0_1_M200_PACKET.md` §10(d)（prompt §0.1「恰好一处」）；本 grant 仅覆盖本包 2 臂；**不授权 P1/P5/任何认证句/commit/push**。

### Q0 目标分支 — PASS

```
$ git branch --show-current
formal-ir-v72p1-addendum-clean
$ git rev-parse --short HEAD
85e0771f
```

与 packet 头部/基线一致；**未切分支**。

### Q1 范围清洁 — PASS（执行前复测）

```
$ git status --porcelain
?? comparison_bench/src/comparison_bench/cli/s01_m200_runner.py
?? comparison_bench/tests/test_s01_m200_runner.py
?? docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PREEXEC.md
$ git diff -- src/ | wc -c
0
$ git status --porcelain -- src/ | wc -l
0
```

- 显式任务文件清单 = 上述 3 件 additive untracked-new；零其他条目（无外源 `openspec/changes/binary-ldpc-v5-*` 脏项、无已跟踪文件修改）。
- `git diff -- src/` = **EMPTY**（0 字节）⇒ 不变量 I4 满足。
- 禁碰文件均未修改：`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`.gitignore`、`README.md`、`AGENTS.md`、`src/`、`experiments/`、`tools/`。
- runner 对 `b2f/b2g/o1/s2c/peg/v28` 全部只读复用（无 monkeypatch、无补常数）。

### Q2 冻结契约 F1–F10 — PASS（代码面）

逐项核对表见 `S0_1_M200_PREEXEC.md` §Q2（F1–F10 十行 + 预算/停止行，测试钉一一对应），本条目引用不重抄。执行时由 runner 常量与 focused 测试共同钉死；F6 构造实测见 Q5。

### Q3 输出缺席 + rg 命中 + 保护根快照 — PASS（执行前复测）

1. **输出缺席**：`workspace/S0_1/` **absent**（家族缺席 ⇒ 两个冻结臂根 `workspace/S0_1/S01-R1_6e48f11e`、`workspace/S0_1/S01-R2_b74322cf` 必然缺席；dry 输出 `roots.family_exists=false` 复证）。
2. **`rg 'S01_|S0_1_M200'` 命中**限于本包族：runner、test、packet、prompt、preexec、本日志（新建后新增命中）+ `docs/NOW.md:14` 一条基线已提交、未修改的包族指针。无其他文件命中。
3. **保护根快照（字节级，与 PREEXEC §Q3 一致）**：`results/` 0 文件；`comparison_bench/outputs_comparison/` **1446 文件 / 554423395 字节**（字节一致）；既有证据根只读不碰。
4. `git diff -- src/` EMPTY（0 字节）。

### Q4 focused 单文件 fake-only 测试 — PASS（输出附下，E5）

```
$ PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_s01_m200_runner.py -q
...................                                                      [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /mnt/d/Code/HD-QKD_Polar_Comparison/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: cache_dir
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 1 warning in 3.79s
RC=0
```

（warning = 已知良性 pytest `cache_dir` 配置提示，AGENTS §8 已记。）性质：全 fake-only（构造/解码/rank/信道四类注入件显式传入 tmp 合成 npz；零生产解码、零真实数据路径）。

### Q5 dry 零解码 pins — **DRY-PASS（本条目 supersede PREEXEC §Q5 的 PENDING 行）**

PREEXEC §Q5 原状态 = PARTIAL（字面量 PASS ∪ F6 构造实测 PENDING）。Grant 后、首臂前已补跑唯一零解码命令，**F6 构造实测 PASS**：

```
$ PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner --dry --construct-pins
{
 "arms": {"arms": {"S01-R1": 2026092001, "S01-R2": 2026092011}, "m": 200,
          "reporting": "separate per instance; pooling incl. 6+4 FORBIDDEN"},
 "budget": {"bar12_report_only": 12, "batch_ceiling_s": 7200, "cpus": 1,
            "n_req_report_only": 277, "per_decode_cap_s": 300,
            "rss_cap_gib": 2, "wall_cap_s_per_arm": 3600},
 "channel": {"access": "read-only via frozen bind_empirical_bundle; never refit; pure synthetic (packet F4)",
             "g1_shape": [32, 1024], "g2_shape": [32, 32, 1024],
             "sidecar": "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz",
             "source": "2M"},
 "channel_path": "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz",
 "construction_pins": {
   "measured": {
     "S01-R1": {"a208_pins": {"four_cycles": 0, "girth": 8, "rank": 208,
                              "twice_identical": true},
                "base_rank": 200, "base_rank_required": 200,
                "base_rows": "rows[0,200)", "girth": "recorded-not-gated",
                "instance": 2026092001},
     "S01-R2": {"a208_pins": {"four_cycles": 0, "girth": 6, "rank": 208,
                              "twice_identical": true},
                "base_rank": 200, "base_rank_required": 200,
                "base_rows": "rows[0,200)", "girth": "recorded-not-gated",
                "instance": 2026092011}},
   "status": "MEASURED-DRY (zero decode)"},
 "decode_calls": 0,
 "frozen_accounting": {"content_bits": 852.544, "f_eff_slope": 4.785675,
   "f_super": 1.2480294272201786, "f_super_formula": "(5*200+64)/852.544 = 1064/852.544",
   "f_super_literal": "1.24803", "leak_bits": 1064, "n_req_report_only": 277},
 "mode": "dry-zero-decode",
 "roots": {"family": "workspace/S0_1/", "family_exists": false},
 "seeds": {"block_base": 2026095601, "blocks": 240, "first": 2026095601,
           "last": 2026095840, "stream": "o1_blk:{seed}",
           "stream_first_matches_frozen": true},
 "verdict": "DRY-PASS (zero decode; literal + construction pins)"
}
RC=0
```

- ✅ F6：两实例 A208 `four_cycles=0` / `rank=208` / `twice-identical=true`；基码 `rank(rows[0,200))=200==200` REQUIRED 满足；girth R1=8 / R2=6 记录不设门。任一非 PASS 即 STOP-BLOCKED —— 未触发。
- ✅ gamma 只读（2M、g1 (32,1024)、g2 (32,32,1024)、sidecar 同胞；never refit）、seed 钉（2026095601..2026095840、240 块、stream 首元素一致）、预算钉（3600/7200/300/2GiB/1CPU/bar-12=12/N_req=277）、`f_super=1.2480294272 ≡ 1.24803`、`decode_calls: 0`、`family_exists: false`。
- **本行取代 PREEXEC §Q5「F6 构造实测 PENDING / Q5 状态 = PARTIAL」占位行；Q5 现全 PASS。**

### Q6 闭合 — PASS

- (a) 入口前置 **H0.1 = SATISFIED**：`051e3687` “hygiene: H0.1 commit X1 scoped tree + F1 fix + G0=B log” 在基线 `85e0771f` 祖先链（`git log` 复证），X1 scoped 提交完成，**无需豁免**。
- (b) 执行面就绪：thin runner + fake-only 单文件测试已实现（Q1 清单 1/2 件）。
- (c) Q0–Q5 全 PASS（本条目）。
- (d) 授权块 = packet §10(d) **唯一一处填全**（grant verbatim + 双 UUID + 预算 6 项全确认 + 2026-09-22/main，见本条目顶部与 packet）。
- 授权后、首臂前**零生产解码**（Q5 唯一命令为 `--dry --construct-pins`，`decode_calls: 0`）。
- ⇒ **Q6 = PASS；Pre-EXECUTE 闭合，放行条目 1–2（冻结臂序 R1→R2，一次授权覆盖，各一次调用）。**

---

## 条目 1 — S01-R1 逐臂运行（2026-09-22，冻结臂序首臂）

- 臂：`S01-R1`（UUID `S01-R1_6e48f11e`，构造实例 2026092001，recorded girth 8）；冻结臂序 R1→R2 之首臂，一次调用，**无续跑、无修复重跑**。
- 证据根（只读引用，不改写）：`workspace/S0_1/S01-R1_6e48f11e/` — `S01_RESULT_S01-R1_m200.md`（RAW）+ `rows.json`（`{rows: 240, summary}`）+ `block_accounting.csv`（header + 240 行）。
- 结果：**verdict COMPLETE**；blocks **240/240 run**；k = **79/240**；FER = **0.329167**（本臂自有 k，禁跨实例合并）；**undetected = 79 单列**（syndrome-valid 但 x̂≠x，计入 k 为 fail，**永不并入 success**）。
- 交叉核对：`rows.json` rows=240 ↔ csv 240 行 ↔ summary failures=79 ↔ csv `failed` 真值 79 ↔ csv `undetected` 真值 79，一致。
- iters min 8 / max 81；单块 wall max 18.30 s（单解码 300 s 终态帽未触发）；臂 wall **871.9 s** / 上限 3600 s（单窗口）；均块 3.63 s；peak RSS 0.165 GiB（<2 GiB）；1 CPU。
- F7：f_super = (5·200+64)/852.544 = 1064/852.544 = **1.248029**（字面量 1.24803；冻结 V80 TRAIN/anchor 基准，**单列、永不引作 f_eff**）；f_eff = f_super + 4.785675·FER = **2.823314**（本臂 FER，单一冻结基准）；N_req = **277 report-only**（k≠0，零失败规则不适用；无认证主张）。
- bar-12 上下文 REPORT-ONLY：route-ctx FAIL（k=79 > 12）；只报告，不止跑、不裁决路由。
- S0.1-gate 贡献：**PASS-component：240/240 complete，non-wall-partial**（双臂皆达此分量方为 S0.1-gate PASS；门本身归批次末评审）。
- claim ceiling（packet §9）：合成 paired-frame m=200 soft-marginal 效率探针（per-instance k/240 + 冻结基准 f_super/f_eff + iters/wall + undetected 单计数）作 P1 Stage-1 实测锚；**非** SKR/qualification/路由裁决/工作点选择/真数据 FER/可认证或可文献比较的 f_eff 句/发表材料。

## 条目 2 — S01-R2 逐臂运行（2026-09-22，冻结臂序次臂）

- 臂：`S01-R2`（UUID `S01-R2_b74322cf`，构造实例 2026092011，recorded girth 6）；冻结臂序次臂，一次调用，**无续跑、无修复重跑**。
- 证据根（只读引用，不改写）：`workspace/S0_1/S01-R2_b74322cf/` — `S01_RESULT_S01-R2_m200.md`（RAW）+ `rows.json`（`{rows: 240, summary}`）+ `block_accounting.csv`（header + 240 行）。
- 结果：**verdict COMPLETE**；blocks **240/240 run**；k = **119/240**；FER = **0.495833**（本臂自有 k，禁跨实例合并，含 6+4 汇合**禁止**）；**undetected = 116 单列**（syndrome-valid 但 x̂≠x，计入 k 为 fail，**永不并入 success**）。
- 交叉核对：`rows.json` rows=240 ↔ csv 240 行 ↔ summary failures=119 ↔ csv `failed` 真值 119 ↔ csv `undetected` 真值 116（u ≤ k），一致。
- iters min 8 / max 300（触 max_iter 守恒上限，非 wall 帽）；单块 wall max 70.53 s（300 s 终态帽未触发）；臂 wall **1010.5 s** / 上限 3600 s（单窗口）；均块 4.21 s；peak RSS 0.165 GiB（<2 GiB）；1 CPU。
- F7：f_super = **1.248029**（同冻结基准，字面量 1.24803，单列）；f_eff = f_super + 4.785675·FER = **3.620927**（本臂 FER，单一冻结基准）；N_req = **277 report-only**（无认证主张）。
- bar-12 上下文 REPORT-ONLY：route-ctx FAIL（k=119 > 12）；只报告，不止跑、不裁决路由。
- S0.1-gate 贡献：**PASS-component：240/240 complete，non-wall-partial**。
- claim ceiling：同条目 1（packet §9 合成探针句）；两实例引用时**必须分列**，汇合（含 6+4）**禁止**。

## 条目 3 — 收口 tally（两臂分列，停批次末评审门前）

- 两臂分列（禁合并；任何后期引用必须保留此分列形）：

  | 臂 | verdict | k/240 | FER | undetected（单列） | iters min/max | wall s (/3600) | f_super | f_eff | N_req |
  |---|---|---|---|---|---|---|---|---|---|
  | S01-R1 (2026092001, girth 8) | COMPLETE | 79/240 | 0.329167 | 79 | 8/81 | 871.9 | 1.248029 | 2.823314 | 277 ro |
  | S01-R2 (2026092011, girth 6) | COMPLETE | 119/240 | 0.495833 | 116 | 8/300 | 1010.5 | 1.248029 | 3.620927 | 277 ro |

- S0.1-gate：**240/240 完整 component 齐** — 双臂各 240/240 run、non-wall-partial、无 INCOMPLETE/失败臂保留项；两 `PASS-component` 分量齐备。门裁决本身归 `S0_1_BATCH_END_REVIEW.md`（独立批次末评审，另行指派），**本条目不停留裁决、不代评审**。
- 预算 tally：R1 871.9 s + R2 1010.5 s = **累计 ~1882 s / 批次上限 7200 s**；单臂各 ≤3600 s；单解码 300 s 帽零触发（块 wall 最大 70.53 s）；RSS 峰 0.165 GiB（<2 GiB）；1 CPU。未用预算 ≠ 授权扩大。
- **未用修复路径声明**：预注册的一次工程修复+重跑路径**未使用**（零重跑、科学输入/种子/阈值/数据角色/被验假设全程未变；两臂各一次调用即 COMPLETE，无失败尝试需保留）。
- claim ceiling 重申：合成 paired-frame m=200 效率探针分列锚（§9）；**无认证主张**（无 SKR、无 qualification、无路由裁决、无工作点选择、无真数据 FER、无 f_eff≤1.3 可认证句、无发表材料）；key-eligible 200/276/364 引用未消耗。
- 本任务动作边界：**只向本日志 append 条目 1–3，未改旧条目（条目 0 原样），未做新执行，未 commit/push**；分支仍 `formal-ir-v72p1-addendum-clean` @ `85e0771f`。下一步 = 批次末独立评审（门外），不在本任务内。

---
