# M2-HDCASCADE-SYNTH-PROMPT.md — 执行面提示（EXPLORE 合成批次）

Cycle: `G-M2-HDCASCADE-SYNTH` · Track: `EXPLORE` · 状态：停授权前（§7 未填 = 未授权，不得执行）

## 1. 执行面白名单（仅允许）

- 读取：冻结 `gamma_f03.npz`（R1-TRAIN 直方图）、T0 design 文档、M0 指针文档。
- 写入：`workspace/m2hdc_<uuid8>` fresh additive 根；`EXPLORATION_LOG.md` append-only 条目。
- 运行：focused fake-only 测试；冻结臂序 A1–A6 合成测量命令（授权后）。

## 2. 禁令（违反任一 = BLOCKER，上报主线程）

- 禁改冻结模块行为（`src/`、`experiments/`、`tools/` diff 必须空）。
- 禁真实 `.ttbin` / 真实 `gamma`（禁任何真实数据读入）。
- 禁写 `results/`、`comparison_bench/outputs_comparison/`。
- 禁 P1/S0.1/P3/P4/TIMING 族；禁 `docs/research_cycles/*/NOW*`、`decision-log.md`、`AGENTS.md` 写入。
- 禁 `commit` / `push`（本包无提交动作）。

## 3. 命令模板（placeholder；Pre-EXECUTE 时冻结填入）

```bash
# 0) 机器门：分支/HEAD 重测 + 冻结目录 diff + 输出缺席
git branch --show-current && git rev-parse HEAD
git status --porcelain -- src experiments tools
ls workspace/m2hdc_<uuid8> 2>&1  # 须缺席

# 1) focused fake 测试（双保险 timeout，二选一按环境）：
timeout <T_fake>s .venv/bin/python -m pytest -p no:cacheprovider <fake_test_path> -q
# 或： .venv/bin/python -m pytest -p no:cacheprovider <fake_test_path> -q  (timeout=<T_fake>s)

# 2) 合成臂测量（占位；授权后按冻结序 A1→A6，单臂 timeout 双保险）：
timeout <T_arm>s .venv/bin/python -m <synth_module> --arm <A1..A6> --n 240 --seed <frozen> --out workspace/m2hdc_<uuid8>/<arm>/
```

- `<T_fake>` / `<T_arm>` / `<fake_test_path>` / `<synth_module>` 均为 Pre-EXECUTE 冻结值，不得执行中途更改。
- F5会计以PACKET为权威(λ/H公式见PACKET F5)。

## 4. 一次授权覆盖臂序

- §7 授权一次覆盖冻结臂序 A1→A6；操作员在前一机器门通过时继续下一臂。
- 任一臂 BLOCKER（科学输入变更/种子不符/预算外真实数据触及）：全包 STOP，上报主线程，不擅自 repair（§3 预注册 repair 除外，且至多一次）。

## 5. 返回（二元）

- `COMPLETE`：E1–E8 全部满足，附变更文件清单 + 命令/结果 + log 收口 tally。
- `BLOCKER`：任一 E 项失败或禁令触发，附失败命令、精确错误/traceback、已试补救、需主线程裁决的单一问题。“仍未完成”不是 COMPLETE。
