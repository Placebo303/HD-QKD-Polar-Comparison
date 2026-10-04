# M0 真实帧闭环 — 执行者 prompt（配 `PREREG_AND_AUTH.md`）

> 只有当 `PREREG_AND_AUTH.md` §8 授权块已填写（或主线程在对话中转达了用户的逐字授权）时，才把下面这段贴给执行会话。
> 授权块为空时，执行者只能做第 1–2 步然后停。

---

你是 `HD-QKD_Polar_Comparison` 仓库（WSL 路径 `/mnt/d/Code/HD-QKD_Polar_Comparison`，分支 `formal-ir-v72p1-addendum-clean`）
的执行者，负责运行 DECIDE 包 `G-M0-REALFRAME`。你只执行、只记录，不做科学结论，不改任何冻结输入。

**第 1 步 — 通读**：完整读 `docs/research_cycles/M0-REALFRAME/PREREG_AND_AUTH.md`，以及
`comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py` 的模块 docstring。

**第 2 步 — 授权与 Pre-EXECUTE 重测**（任一不满足 ⇒ STOP，报告哪一项）：
1. `PREREG_AND_AUTH.md` §8 的 grant verbatim 非空（或主线程给出的逐字授权）。为空 ⇒ STOP，不执行任何解码。
2. `git rev-parse --abbrev-ref HEAD` = `formal-ir-v72p1-addendum-clean`；记录 `git rev-parse --short HEAD` 的实测值（只记录，不要求等于某个 SHA）。
3. `git diff --stat -- src/ experiments/ tools/` 输出为空。
4. 三个输出根都不存在：`workspace/m0_359922a7_1M`、`workspace/m0_642a8fe8_1p5M`、`workspace/m0_b1a9142d_2M`。
5. 跑 focused 测试，期望 `7 passed`（pytest 的 `cache_dir` 配置警告属已知良性输出，不算失败）：
   ```bash
   cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" -q comparison_bench/tests/test_m0_realframe_fake.py
   ```
   测试会在 `workspace/m0__pytest_*` 下建临时根并自行删除；这是测试产物，不是输出根。

**第 3 步 — 执行**：在三个独立终端 / 后台进程中并行运行 `PREREG_AND_AUTH.md` §7 的三条命令（逐字，不改参数）。
每条命令记下开始 / 结束时间和退出码。

**第 4 步 — 执行中的硬规则**：
- 不重跑、不续跑、不改参数、不换根。某源以 `INCOMPLETE-wall` 或 `FAIL(budget-rss)` 结束 ⇒ 保留原样，照实报告。
- runner 抛出 `REFUSED: …`（偏移 / 配对数 / 切分与 R1 不一致、根已存在等）⇒ 该源 STOP，原文报告错误信息，不要尝试修复。
- 不写 `results/`、`comparison_bench/outputs_comparison/`，不动任何其他 workspace 根，不改任何代码或文档（第 5 步的 `RESULT.md` 除外）。
- 不 commit、不 push。

**第 5 步 — 写 `docs/research_cycles/M0-REALFRAME/RESULT.md`**，内容只包括：
1. 三条命令、开始 / 结束时间、退出码、每源 verdict；
2. 从每个根的 `rows.json` → `summary` 逐源、逐臂抄录：超帧数、余数、fails、undetected、FER 及 95% 区间、
   fails_full10、f_super、f_notag、f_eff、X1 合成对照（fails/240 与区间）、overruns、wall、峰值 RSS、解码次数；
3. 按 `PREREG_AND_AUTH.md` §4 的三类规则，对 6 个臂逐一标出 一致 / 更差 / 更好（纯机械比较区间，不加解读）；
4. 每源每臂 `raw_symbol_errors` 的均值、最小、最大（从 `block_accounting.csv` 计算）。

禁止：把第 4 项（误差数）或全 10 位一致率写成“P3 通过 / 记忆审计完成”——它们只是观测；合并不同源或不同臂的任何数字；把 undetected 算作成功；把 f_super 写成 f_eff；写任何认证句、SKR 或发表结论。

**最终回报**（只有两种）：
- 全部完成：列出三个根、三个 verdict、`RESULT.md` 路径、6 个臂的 D1 判定；
- 或阻塞：失败的命令、原文错误 / traceback、已尝试的操作（应为“无”）、需要主线程决定的一件事。
