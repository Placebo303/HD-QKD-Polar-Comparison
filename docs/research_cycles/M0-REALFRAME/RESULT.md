# M0 真实帧闭环 — RESULT（G-M0-REALFRAME，执行者记录，无科学结论）

- **日期**：2026-09-24；分支 `formal-ir-v72p1-addendum-clean`，HEAD 实测 `8e9c8526`（执行前后一致）。
- **授权**：主线程转达用户逐字授权 `G-M0-REALFRAME GRANT：授权 M0 真实帧闭环执行（三源各两臂，每源 5400 s、单解码 300 s、RSS < 4 GiB、每进程 1 CPU、三源并行，根 m0_359922a7_1M / m0_642a8fe8_1p5M / m0_b1a9142d_2M）`。
- 本文件只抄录与机械判定（§3.1 为按主线程指示补录的 §4 冻结路由**机械**结论，非科学解读）；
  F9(i) 判读、科学解读与接受仍由 Pre-RESULT 独立线程 / 主线程负责。

## 1. 命令、时间、退出码、verdict（三源并行，逐字命令）

| 源 | 命令（`…` 处仅为仓库根前缀 `/mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python`，参数逐字） | 开始 | 结束 | 退出码 | verdict |
|---|---|---|---|---|---|
| 1M | `-m comparison_bench.src.comparison_bench.cli.m0_realframe_runner --source 1M --root workspace/m0_359922a7_1M --execute-real --execution-authorized` | 2026-09-24T18:09:39+08:00 | 2026-09-24T19:06:33+08:00 | 0 | **COMPLETE** |
| 1p5M | `… --source 1p5M --root workspace/m0_642a8fe8_1p5M --execute-real --execution-authorized` | 2026-09-24T18:09:39+08:00 | 2026-09-24T19:11:19+08:00 | 0 | **COMPLETE** |
| 2M | `… --source 2M --root workspace/m0_b1a9142d_2M --execute-real --execution-authorized` | 2026-09-24T18:09:39+08:00 | 2026-09-24T19:27:35+08:00 | 0 | **COMPLETE** |

三源均未触 5400 s 帽；无 `INCOMPLETE-wall`、无 `FAIL(budget-rss)`、无 `REFUSED`、无重跑 / 续跑 / retry。

## 2. 逐源逐臂抄录（来自各根 `rows.json` → `summary`）

### 2.1 源 1M（根 `workspace/m0_359922a7_1M`）

- provenance：ttbin `…/Type2_1M_3s_2026-01-21_184040.ttbin`，offset −50 ps（= R1），
  n_pairs_total 525831（= R1 `n_pairs_N`），n_pairs_eval 210327，eval_first_frame 8798551（= R1 `val_frames[0]`），read_wall_s 0.40。
- bundle：`workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz`（R1-TRAIN，只读）。
- 超帧 205；余数 407 符号已丢弃。源 wall 3409.4 s；峰值 RSS 0.47 GiB；解码 410 次。

| m | 超帧 | fails | undetected | FER [95% CI] | fails_full10 | f_super | f_notag | f_eff | X1 合成 fails/240 [95% CI] | overruns | 臂 wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 197 | 205 | 20 | 0 | 0.097561 [0.064046, 0.145881] | 132 | 1.278490 | 1.200488 | 1.745385 | 3/240 [0.004260, 0.036100] | 0 | 1991.3 |
| 201 | 205 | 13 | 0 | 0.063415 [0.037431, 0.105460] | 132 | 1.302865 | 1.224864 | 1.606347 | 0/240 [0.000000, 0.015754] | 0 | 1315.4 |

`raw_symbol_errors`（`block_accounting.csv`，两臂同一批超帧）：
m=197 mean 244.29 / min 204 / max 286；m=201 mean 244.29 / min 204 / max 286。

### 2.2 源 1p5M（根 `workspace/m0_642a8fe8_1p5M`）

- provenance：ttbin `…/Type2_1-5M_3s_2026-01-21_183806.ttbin`，offset +50 ps（= R1），
  n_pairs_total 735780（= R1），n_pairs_eval 294293，eval_first_frame 8777111（= R1 `val_frames[0]`），read_wall_s 0.68。
- bundle：`workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz`（R1-TRAIN，只读）。
- 超帧 287；余数 405 符号已丢弃。源 wall 3696.4 s；峰值 RSS 0.59 GiB；解码 574 次。

| m | 超帧 | fails | undetected | FER [95% CI] | fails_full10 | f_super | f_notag | f_eff | X1 合成 fails/240 [95% CI] | overruns | 臂 wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 203 | 287 | 22 | 1 | 0.076655 [0.051164, 0.113329] | 145 | 1.273690 | 1.198142 | 1.640536 | 2/240 [0.002288, 0.029870] | 0 | 2137.1 |
| 207 | 287 | 10 | 0 | 0.034843 [0.019034, 0.062940] | 139 | 1.297298 | 1.221750 | 1.464047 | 1/240 [0.000736, 0.023220] | 0 | 1388.9 |

`raw_symbol_errors`：
m=203 mean 260.44 / min 213 / max 304；m=207 mean 260.44 / min 213 / max 304。

### 2.3 源 2M（根 `workspace/m0_b1a9142d_2M`）

- provenance：ttbin `…/Type2_2M_3s_2026-01-21_183657.ttbin`，offset +50 ps（= R1），
  n_pairs_total 982182（= R1），n_pairs_eval 392721，eval_first_frame 8771980（= R1 `val_frames[0]`），read_wall_s 0.73。
- bundle：`workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1_2M_verify.npz`（R1-TRAIN，只读）。
- 超帧 383；余数 529 符号已丢弃。源 wall 4672.0 s；峰值 RSS 0.73 GiB；解码 766 次。

| m | 超帧 | fails | undetected | FER [95% CI] | fails_full10 | f_super | f_notag | f_eff | X1 合成 fails/240 [95% CI] | overruns | 臂 wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 204 | 383 | 22 | 0 | 0.057441 [0.038236, 0.085436] | 182 | 1.270313 | 1.195313 | 1.545209 | 2/240 [0.002288, 0.029870] | 0 | 2525.3 |
| 208 | 383 | 16 | 0 | 0.041775 [0.025875, 0.066776] | 180 | 1.293751 | 1.218751 | 1.493675 | 0/240 [0.000000, 0.015754] | 0 | 1868.6 |

`raw_symbol_errors`：
m=204 mean 259.85 / min 202 / max 299；m=208 mean 259.85 / min 202 / max 299。

### 2.4 汇总资源合计（**仅记录**；批次级资源口径，PREREG §5）

- 解码 / 臂-超帧评估总次数 **1750**（1M 410 + 1p5M 574 + 2M 766；每源两臂共用同一批超帧）。
- overruns 全部为 0；无单次解码 > 300 s。
- 峰值 RSS 最大 0.73 GiB（< 4 GiB）；三源并行，批次 wall 18:09:39 → 19:27:35 ≈ 4676 s（< 3 × 5400 s）。

### 2.5 F1 / F2 冻结断言复核（全部相符，未触发 `REFUSED`）

- **F1 数据**：三源只开 base `X.ttbin`，ttbin 路径与 F1 逐字一致（§2.1–2.3 provenance）。
- **F2 读取 / 对齐 / 配对 / 切分**：
  - 派生偏移 = R1：1M **−50 ps**、1p5M **+50 ps**、2M **+50 ps**；
  - 配对数 = R1 `n_pairs_N`：**525831 / 735780 / 982182**；
  - eval 首帧 = R1 `val_frames[0]`：8798551 / 8777111 / 8771980（60/20/20 切分边界一致，切分由 runner 与 `split_manifest.json` 断言，不一致即 `REFUSED`）；
  - 余数丢弃并已报告：407 / 405 / 529 符号；超帧 205 / 287 / 383（与 F3 预计值一致）。
- 三源均以退出码 0、verdict **COMPLETE** 结束，全程无 `REFUSED` / `INCOMPLETE-wall` / `FAIL(budget-rss)` ⇒ F1–F3 断言全部通过。

## 3. D1 逐臂机械判定（§4 区间比较，仅标签、不加解读）

| 源 | m | 真实 FER [95% CI] | X1 合成 FER [95% CI] | 判定 |
|---|---|---|---|---|
| 1M | 197 | [0.064046, 0.145881] | [0.004260, 0.036100] | **更差**（真实下界 > 合成上界） |
| 1M | 201 | [0.037431, 0.105460] | [0.000000, 0.015754] | **更差** |
| 1p5M | 203 | [0.051164, 0.113329] | [0.002288, 0.029870] | **更差** |
| 1p5M | 207 | [0.019034, 0.062940] | [0.000736, 0.023220] | **一致**（区间重叠） |
| 2M | 204 | [0.038236, 0.085436] | [0.002288, 0.029870] | **更差** |
| 2M | 208 | [0.025875, 0.066776] | [0.000000, 0.015754] | **更差** |

计数：更差 5 / 一致 1 / 更好 0。§4 路由的机械结论见 §3.1；F9(i) 判读不在本文件，留给独立 Pre-RESULT 与主线程。

### 3.1 §4 冻结路由的机械结论（流程结论，**非 SKR、非 P3 verdict、非发表主张**）

- 按 §4 路由：存在“更差”臂（5/6）⇒ **在信任 M3 的合成结果之前，先做信道条件化**（逐超帧自适应先验 / 漂移处理），
  并用 F9(ii) 的逐超帧误差序列定位原因；合成信道在条件化完成前不得作为可信开发代理。
- 该判定的作用域严格限于 §4 所述“合成信道能否继续作开发代理”这一个流程决策；
  它不放行任何 P3 门控动作，不允许在任何对外材料中把合成 FER 当真实 FER 引用（对外数字只能来自真实帧实测本身）。
- F9(i)（全 10 位失败数 vs u2 失败数）的判读、以及是否触发 L1 披露 / 联合解码分支，按分工留给独立 Pre-RESULT 与主线程；
  本文件只抄录逐臂 `fails_full10`（§2.1–2.3 表）。

## 4. 零改动 / 保护根证据（执行前后重测）

- `git diff -- src/`：**0 字节**（执行前与执行后各测一次）；`git diff --stat -- src/ experiments/ tools/` 为空。
- 分支 / HEAD 执行前后不变：`formal-ir-v72p1-addendum-clean` / `8e9c8526`。
- 保护根不变：`results/` 0 B；`comparison_bench/outputs_comparison/` 554423395 B（执行前后相同）。
- 输出仅写三个冻结根 + 本文件；工作树其他未提交项（P4 / TIMING / M0 文档等背景项）原样保留、未纳入本包、未被改动；未 commit、未 push。
- 本会话（只读汇总，2026-09-24）复测：`git diff -- src/` = **0 字节**，`git diff --stat -- src/ experiments/ tools/` 为空，
  `results/` = **0 B**；三个输出根只读打开（`rows.json` / `block_accounting.csv` / `M0_RESULT_*.md`），未写入、未重跑、未续跑。

## 5. 已知缺口（需发起会话抄录，本会话无法补）

- **END 行未落盘**：runner `main()` 退出前只把逐源终态 JSON（source / verdict / root / 各臂 m·superframes·fails·undetected·fer·fails_full10·f_super·f_eff）
  `print` 到 stdout，**没有写入任何文件**；三个根内只有 `rows.json`、`block_accounting.csv`、`M0_RESULT_*.md`。
  因此三条命令 stdout 的最终 END / JSON 摘要行只存在于执行会话的终端记录里，磁盘上无对应产物。
- **待办**：由**发起执行的会话**把三条 stdout 终态 JSON 行逐字抄录到本文件 §1 表下（或三个根内另存的
  `stdout_END_*.txt`，属新增文件，须主线程另行授权后写入）。本会话只读、不重跑、不代抄。
- 该缺口只影响**终端行的字面留痕**，不影响 §2 的数值来源（`rows.json` → `summary` 与 runner 最终打印的字段同源）。
