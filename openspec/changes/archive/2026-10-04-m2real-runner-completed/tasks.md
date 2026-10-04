# Tasks: M2REAL Runner (T3 R0..R9 实现合一；implementation-only)

约定：实现 exactly 本 tasks；遇 1024→64 外新映射 / 种子外规则 / Müller 真值填数即 STOP，不猜。若任务有歧义，停并返回 planner/orchestrator。

- [x] R0 — 脚手架与冻结常量：`m2real_runner.py` 建文件；SOURCES/GRID（只读 `m0.SOURCES` 派生）/DIMENSION 1024/16×64/`FROZEN_SLICE`（205/287/383 + 407/405/529 + 3280/4592/6128）/预算（5400/300/4 GiB/1 CPU）/根门（`workspace/m2real_<uuid8>` + 双旗缺一 rc2 + 禁区）。证据：`test_r0` + `test_r1b` PASS。
- [x] R1 — 真实切片：只读复用 `m0.superframes` 切 1024 超帧 + 自研 16×64 连续子切（`slice_real_blocks`）；余数丢弃并报告；期望/实际 + `slice_match` 列（mock 小数组可跑，生产漂移靠 m0 上游断言 + grant-time 复核）。证据：`test_r3` + `test_r3b`（三源全尺寸形状，无解码）PASS。
- [x] R2 — 递增种子：HDC 5701 系（只读派生 `m2hdc.M2HDC_ARM_SEED`，越界 STOP）+ LB 5601 系（只读 `m2lb.M2LB_BLOCK_BASE`，漂移 STOP）；块种子 = 基址 + 全局块序号 g；`o1_blk:{seed}` 标签。证据：`test_r4`（HDC）+ `test_r2`（LB）PASS。
- [x] R3 — HDC 臂：`provisional_block_table` assumed-v1 + `require_assumed_block_table` 开机校验（真值填入即 STOP）+ 逐块 1-frame `run_hd_cascade` 只读调用（显式 `hdc_decode_fn`，缺失即 refuse）。证据：`test_r5`（含 Mueller-STOP 反例）PASS。
- [x] R4 — LB 臂：`allocation_for` / `blind_table_for` / `blind_levels_for` verbatim + `PlaneAllocation` / `BlindStageTable` / `LayeredParams`(300/3) + 逐块 1-frame `run_layered_binary` 只读调用（显式 `lb_construct_fn` + `lb_decode_fn`，缺失即 refuse；单 full-m 解码，盲表 report-only）。证据：`test_r1` 系 + `test_r1b/c` PASS。
- [x] R5 — 预算门：源 wall / 单解码 terminal（块 fail 不重跑）/ RSS / 1 CPU；`INCOMPLETE-wall` / `FAIL(budget-rss)` / `FAIL(budget)` / `overrun` 语义 + 留存不续跑。证据：`test_r8b` + `test_r9` PASS。
- [x] R6 — 会计：A-CMPE 全列 CSV（`block_accounting_csv`）+ `rows.json` + `M2REAL_RESULT_<source>.md`；超帧 rollup（16 全 exact 才 success，leak 求和；超帧数另列）；H 基双轨（f 用 `H_corr` measured，校验器合成 H 标注 assumed）；`undetected` 隔离。证据：`test_r6`（HDC）+ `test_r3`（LB）PASS。
- [x] R7 — D2/F9/claim：D2 输入 + 规则逐字 + DEFERRED（不评分支）；F9(i) 全表标注；§8 禁句逐字。证据：`test_r7`（HDC）+ `test_r5b`（LB）PASS。
- [x] R8 — fake 测试双文件：`comparison_bench/tests/test_m2real_hdc_fake.py` + `test_m2real_lb_fake.py`（mock 小数组 + mock bundle + fake decode/construct；生产核 `hc._run_planes_production` / `lay._construct_plane_production` / `lay._spa_decode_production` 全 monkeypatch raise；零真实读；全 buffering 在 tmp_path）。证据：本 R9 命令全过。
- [x] R9 — 落盘 + 验证：本三文件 + 双测试落盘；跑冻结合令（23 passed）；禁改项自查（`git status` 仅三新路径：1 模块 + 2 测试 + `openspec/changes/m2real-runner/` 三文件；`src/`、`experiments/`、`tools/`、`m0/m2hdc/m2lb/methods` 零改；`results/`、`outputs_comparison/`、既有 workspace 零写；无 commit/push；不做 acceptance）。

冻结验证命令（T0 open 状态下唯一认可的测试入口）：

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_m2real_hdc_fake.py comparison_bench/tests/test_m2real_lb_fake.py -q
```

结果：23 passed（hdc 14 + lb 9），0 failed。production 真实执行未触（fake-only；PREREG §6 仍 BLANK）。
