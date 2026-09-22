# P1 Stage-1 Pre-EXECUTE 记录 (2026-09-22) — FROZEN, NOT GRANTED

- Packet：`P1_STAGE1_PACKET.md`（P1S1-1，冻结科学输入 + 授权边界）+ `P1_STAGE1_PROMPT.md`（P1S1-2，执行面）。Acceptance ID（拟）：**G-P1S1**。
- Track：**EXPLORE**（合成、有界、可逆；`EXPLORE_HEAVY` 成本注记）。本记录是 Pre-EXECUTE 组装（实现面），**不是授权**；授权任何执行 = 0。**未授权不得执行。**
- 本记录只新建三件套中的本文件；另两件（thin runner + 单文件测试）见 §Q4。**§10(d) 授权块仍空白。**

## 冻结臂根 UUID（Pre-EXECUTE 冻结 + 缺席已证）

| 臂 | 冻结根 | 缺席 |
|---|---|---|
| P1S1-R1（实例 2026092001） | `workspace/P1_STAGE1/P1S1-R1_ef7da79b` | 不存在（已证，见 Q3） |
| P1S1-R2（实例 2026092011） | `workspace/P1_STAGE1/P1S1-R2_22754019` | 不存在（已证，见 Q3） |

## Q0 — 目标分支与 HEAD（PASS）

- `git branch --show-current` = **`formal-ir-v72p1-addendum-clean`**（未切分支）。PASS。
- 实测 HEAD = **`e2236766`**（full `e22367662124e6e4622e24b8d61a86fded3d9ef2`；docs commit "record S0.1 gate PASS…"，其父 = 任务基线 `c98c5ae9`）。任务基线 `c98c5ae9` 以实测为准——漂移仅为 S0.1 门记录 docs commit，无代码改动。PASS（记录实际值）。

## Q1 — 范围清洁（PASS）

- 新文件仅本包 3 件（`git status --porcelain` 实测）：
  1. `comparison_bench/src/comparison_bench/cli/p1_stage1_runner.py`（thin runner，additive）
  2. `comparison_bench/tests/test_p1_stage1_runner.py`（fake-only 单文件测试，additive）
  3. `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_PREEXEC.md`（本文件，additive）
- 预存未跟踪冻结输入（非本包新建，不纳入）：`P1_STAGE1_PACKET.md`、`P1_STAGE1_PROMPT.md`。
- `git diff -- src/ experiments/ tools/` = **EMPTY**（实测无输出；`comparison_bench/src` 非根 `src/`，核改动为零）。PASS。
- 跟踪树零修改（`git diff --stat` EMPTY）。脏树界定 = 上述 5 个未跟踪文件；外源 `openspec/changes/binary-ldpc-v5-*` 不纳入。PASS。

## Q2 — 冻结契约 F1–F10 逐项核对（PASS）

| 项 | 冻结值 | Runner 落点 |
|---|---|---|
| F1 | 恰好 2 臂：P1S1-R1→2026092001 / P1S1-R2→2026092011，分报禁合并 | `ARMS` 逐字；`parse_arm` 拒他臂；单臂/调用；测试 `test_parse_arm_frozen_two_arm_table` |
| F2 | nested leading-200 基码；单段 rows[200,208)；COLD 全矩阵重解码；总行 208≤208 硬顶；NO warm-start/non-nested/two-segment | `P1_M_BASE=200` + `P1_DELTA_M=8` + `P1_M_TOTAL=208` + 双硬顶断言；`construct_and_pin` 返回 base/full 双 dict（同源 triples，零跨 Stage 状态）；CLI `--m-base/--m-total` 逐字门（含 209 拒绝测试） |
| F3 | 240 块；`2026096401+idx`；`o1_blk:{seed}`；两臂同整数；FRESH（零重叠 S0.1 族） | `P1_BLOCK_BASE=2026096401`；`block_seed` 越界拒绝；stream 首值 = `common.v10_seed`；git/filesystem grep 新区间仅命中包族（Q3） |
| F4 | `gamma_f03.npz` + `gamma_f03_pb.npz` 只读永不 refit；零 `.ttbin` | `s2c.bind_empirical_bundle` 唯一通道；全文件无 `ttbin` 串（见 Q3 注）；dry 绑定源标签门 |
| F5 | b2f verbatim 先验 + v28 `decode_error_domain_posterior(...,300)`；max_iter 300/streak 3；`exact_match`；NO genie/argmax/L1；双 Stage 冷启动 | `run_execution` 显式接线（Stage-1 `decode_block_marginal(...,1024,200)` / Stage-2 `(...,1024,208)`）；`execute` 核心无默认生产接线 |
| F6 | A208 fc=0 + rank 208 + twice-identical；基码 rank(rows[0,200))==200 REQUIRED；girth 记录不设门 | `construct_and_pin` 全门（Q5 dry 实测 MEASURED，见下） |
| F7 | content 852.544；cap 1108.31；`f_super=(5m+64)/852.544` 双恒等行；`E[leak]=1064+40·r`；`f_exp`；`f_eff`；headroom；禁 f_super/f_exp 当 f_eff 报；单基 | `F_SUPER_BASE=1064/852.544`、`F_SUPER_FULL=(5*208+64)/852.544=1104/852.544` 冻结式；`expected_leak_for/f_exp_for/f_eff_for` 本臂自算；report 行双列 f_super + f_eff 独立 |
| F8 | key-eligible 200/276/364 只引用不消耗；`N_req=⌈3·4.785675/(1.3−f_exp)⌉` report-only（仅 F=0 相关）；无认证主张 | `n_required_for(f_exp)` 动态规则（f_exp≥1.3 → None）；claim ceiling 逐字载入每臂报告 |
| F9 | 禁 bar-12 早停（240 全跑）；Stage-2 = 恰好 Stage-1 非 success 全集（attempted==k 恒等）；bar-12 仅 report-only | Stage-1 循环无早停（全失败 fake 仍跑满 240，测试覆盖）；`attempted != stage1_fails` 即 refuse；bar-12 仅 `route_ctx` 行 |
| F10 | 非 exact_match = fail（k/F）；综合征有效不匹配者 `undetected` 单列永不并入 success | 双 Stage 独立计 `undetected`（分列）；fake mixed 测得 Stage-1 undetected==80 精确；CSV `undetected` 列与 `failed` 列分离 |

## Q3 — 输出缺席 + 新 seed 区间 + 保护根（PASS）

- `workspace/P1_STAGE1/` 不存在（`ls` 实测；dry `roots.family_exists=false` 复证）；冻结双 UUID 根亦双不存在（`ls` 实测）。PASS。
- 新 seed 区间 `2026096401..2026096640`：`git grep "20260964"` 跟踪树**零命中**；filesystem grep 仅命中包族（packet/prompt/runner/test/preexec，无 `src/`/`experiments/`/`tools/`、无既有 runner/测试）。PASS。
- 保护根快照（授权时复验基线）：`results/` = 空（0 B）；`comparison_bench/outputs_comparison/` = 1446 文件 / 554423395 B（含已知 benign pytest 临时目录权限拒绝，AGENTS §8）。本包零写入（禁止目录门在 runner + 测试覆盖）。PASS。
- `git diff -- src/` EMPTY（Q1 复述）。PASS。

## Q4 — focused 单文件 fake-only 测试（PASS，输出附后）

- 文件：`comparison_bench/tests/test_p1_stage1_runner.py`（单文件；显式 fake construct/decode/rescue/rank；零生产调用；磁盘仅 `tmp_path` + tmp fake channel）。
- 命令：`PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_p1_stage1_runner.py -q`
- 输出（实测逐字尾）：`16 passed, 1 warning in 6.37s`（warning = 已知 benign `cache_dir` 未知配置项，AGENTS §8 类）。PASS。
- 覆盖要点：双臂表；F2/F3/F5/F7/F8 冻结字面（含 `f_super_full=(5*208+64)/852.544≈1.294947`、`block_seed(239)==2026096640`、CSV 十列 stage 契约）；四 fn 任一 None 即 rc=2 且零写；根拒绝族（禁写树/错族/臂错配/已存根）；F6 四变体门 + 零解码计数；mixed 160-k 全量 Stage-1 + 精确救援集 + `attempted==k` + `undetected==80` + 数学恒等；全 success 零救援调用；全 rescue F=0；全不转化 F==k；report-only 缺字段 fail-closed；wall/per-decode/error 三终态保留；CLI 五类拒绝且生产零到达；`--dry` 零解码 JSON。

## Q5 — dry 零解码 pins（PASS；Grant 前零生产解码）

- 只用 `--dry` 类 flag；真实 flag 全程未触。`decode_calls=0` 双 pass。
- `--dry`：DRY-PASS（字面 pins；F6 为 rank==200 占位 PENDING）。PASS。
- `--dry --construct-pins`：**MEASURED-DRY（zero decode）**，双实例实测——
  - P1S1-R1（2026092001）：`four_cycles=0` + `rank=208` + `twice_identical=true` + `base_rank=200==200 REQUIRED` + girth 8（记录不设门）+ `full_m=208`。PASS。
  - P1S1-R2（2026092011）：`four_cycles=0` + `rank=208` + `twice_identical=true` + `base_rank=200==200 REQUIRED` + girth 6（记录不设门）+ `full_m=208`。PASS。
- 基码 rank≠200 即 STOP-BLOCKED 门在 fake 测试覆盖（`_rank_bad` → rc=2）。PASS。

## Q6 — 闭合（除授权签字外 PASS；签字栏空白）

- 入口语境已记录：S0.1-gate（`S0_1_BATCH_END_REVIEW.md` PASS_WITH_FINDINGS；R1 79/240 + R2 119/240 分列）+ G0=B（EXECUTION_PLAN §4 期 0）——packet §10(a) 冻结前提。PASS（引用，不重证）。
- 预算行（用户已接受总量 ceiling=7200 s；逐项待授权时勾选——**本节绝不代签**）：
  - [ ] 单臂 wall ≤ 3600 s（两 Stage 合计，单窗口）
  - [ ] 批次总量 ceiling = 7200 s（= 2×3600，用户已接受提议；签署即定）
  - [ ] 单调用 ≤ 300 s（超时 = 终态，块计 fail，不续跑）
  - [ ] RSS < 2 GiB；1 CPU
  - [ ] 零 `.ttbin` / 零真实数据 / 零 `results/` 与 `outputs_comparison/` 写入
- §10(d) 授权块（空白待签；未填 = 未授权；全包唯一填充处）：
  - Acceptance ID `G-P1S1`；grant verbatim：________；臂根 UUID（R1/R2）：`P1S1-R1_ef7da79b` / `P1S1-R2_22754019`（本记录冻结，签署时确认）：________；预算确认（上列五项逐项勾选）：________；日期 / 主线程：________。
- **未授权不得执行。** 本记录不授权解码、不授权测试长跑、不授权 commit/push、不授权 P1 §9 / P2 / X1 任何臂。

## 自检（ID 6；PASS）

- 新文件仅本包 3 件（Q1 清单）；`git diff -- src/ experiments/ tools/` EMPTY；`workspace/P1_STAGE1/` 无产物（含冻结 UUID 根双缺席）；真实解码零次（Q5 `decode_calls=0`；测试全 fake）；无 commit/push；签字栏空白。
