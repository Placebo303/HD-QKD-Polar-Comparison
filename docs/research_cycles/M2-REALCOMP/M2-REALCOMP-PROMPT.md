# M2-REALCOMP 执行 PROMPT（DECIDE；与 PREREG_AND_AUTH 同一授权边界）

- **Acceptance ID**：`G-M2-REALCOMP`；Track **DECIDE**（FUTURE 执行）；本文件为执行面，不替代预注册、不构成授权。
- **授权门**：§6 授权块全填 + Pre-EXECUTE 清单全 PASS 前，**不得执行**。一次授权覆盖冻结臂表；独立 Pre-RESULT 通过前不得固化/发表。

---

## 1. 执行面白名单（只允许这些动作）

1. Pre-EXECUTE 清单重测（分支/HEAD、冻结目录 diff、输入存在、输出根缺席证明、focused fake 测试）。
2. 按 §2 命令模板执行冻结臂表（3 源 × 3 方法 × 2 m；NB 臂只读引用 M0，不执行解码）。
3. 只写输出根 `workspace/m2real_<uuid8>` + `RESULT.md` 草稿字段；读 M0 artifact、R1 manifest、bundle（只读）。
4. 超预算/断言失败时按 §3 停止门记录终态并停机。

## 2. 禁令（任一违反 ⇒ BLOCKER，停机回主线程）

- 禁止改 M0 文件、`openspec/`、`comparison_bench/` 代码、`src/` / `experiments/` / `tools/`。
- 禁止写 `results/`、`comparison_bench/outputs_comparison/`、既有 workspace 证据根。
- 禁止重跑/续跑/resume（M0 NB 值、已完成臂）；禁止跨源/跨臂合并计数；禁止把 undetected 并入 success/FER；禁止把 f_super 当 f_eff 报。
- 禁止去 F9(i) 标注引用 M0 数字（全表必须带"u2-only, u1 via argmax, u1 正确率未验证"）。
- 禁止 SKR/资格化/发表主张句；禁止 commit/push。
- 禁止猜 Mueller 歧义数（歧义处标"待澄清"并 STOP）。

## 3. 命令 placeholders（执行前填入 uuid8 与 T0 pin 快照；三源可并行）

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m2real_runner --source 1M --root workspace/m2real_<uuid8> --execute-real --execution-authorized
```

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m2real_runner --source 1p5M --root workspace/m2real_<uuid8> --execute-real --execution-authorized
```

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m2real_runner --source 2M --root workspace/m2real_<uuid8> --execute-real --execution-authorized
```

- `<m2real_runner>`：已填 `comparison_bench.src.comparison_bench.cli.m2real_runner`（文件 `comparison_bench/src/comparison_bench/cli/m2real_runner.py` 在档；仍以执行前存在性复核为准；无 runner 即 BLOCKER，不手造执行路径）。
- T0 design pin 快照（已填；`m2-honest-baselines/design.md` §2，2026-09-25 时点）：HD-Cascade 实现版本 = assumed-v1 provisional（`[8,4]`/max_passes 4/sweep 1/消息公式，非原文，真值 = QBER-自适应 k1..k6 公式，n=2^16 bits）；二进制映射 = 10bit→appropriate binary representation 位面分组（Gray 无原文依据，永标 assumed）；按位分组块长表 = Table 2 k1..k6 真值（assumed-v1 `[8,4]` 非原文）；分层二元构造/盲段/SPA pin = 实现 change 冻结（本 design 只冻结结构要求）；Mueller 歧义清单 = B3 + App 剩余 open（①②已关闭，③已关闭附 B2-App A.2 部分关闭注记；B1 关闭/B2 部分关闭/B4/B5 关闭）；q=1024 为外推（Müller 实测 q∈{4,8,32}），永标 assumed。
- focused fake 测试命令（fake-only，零真实数据）：`.venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_m2real_hdc_fake.py comparison_bench/tests/test_m2real_lb_fake.py`（PASS 方可继续）。

## 4. 一次授权 + 独立 Pre-RESULT

- 一次授权覆盖冻结臂序；操作员按冻结条件臂序继续，前一机器门通过才进入下一臂。
- 执行终态只记录终态与机械 D2 标签（无科学解读）；`RESULT.md` 产出后由**独立线程**按 §5 清单 Pre-RESULT；FAIL ⇒ 返工，不固化。
- 主线程接受后落档 decision-log；M0 数字冻结、不得回溯改写。

## 5. 返回（二元，余为违规）

- **COMPLETE**：冻结臂表全部终态（COMPLETE 或 INCOMPLETE-wall/FAIL(budget-rss) 按预算记录），§7 E1–E8 自检全 PASS，产物落输出根，无禁令违反。
- **BLOCKER**：任一断言/预算/范围/授权失败，附 failing 命令、 exact 错误/traceback、已尝试补救、需主线程裁决的单一事项；"仍未完成"不是 COMPLETE。
