# M0 真实帧闭环 — PREREG_AND_AUTH（DECIDE，compact 三文件形式）

- **Acceptance ID**：`G-M0-REALFRAME`
- **Track**：**DECIDE**（真实数据；AGENTS.md §1.2 矩阵 “Real-data development/validation”）。
  采用 AGENTS §1.2 允许的 compact 三文件形式：本文件（预注册 + Pre-EXECUTE + 授权）、
  `RESULT.md`（执行后）、`INDEPENDENT_ACCEPTANCE.md`（独立 Pre-RESULT）。配套执行面：`M0_PROMPT.md`。
- **来源决定**：2026-09-24 用户同意把真实帧闭环提到最前（`docs/RESEARCH_DIRECTION_REPORT_20260924.md` §6 M0 / §10）。
- **与旧草案的关系**：`V80-NBLDPC-JAN21/REALPOINT_NB1024_PACKET.md` 保留为历史，不再作为执行路径
  （它的预算栏依赖尚未执行的 TIMING 探针，而 X1 / P1 已实测单次解码 ≤ 76.5 s）。
  `P3_MEMORY_AUDIT_*` **暂停，其门不变**。本包输出的附加列（F9）只是**观测，不是放行**：
  它们不构成 P3 的 T-M1..M4 verdict，任何以 P3 通过为前提的动作仍被阻塞，直到 P3 按原门判定。
- **状态**：FROZEN — **GRANTED — 已执行待固化**（2026-09-24 §8 授权块已填；三源执行均 COMPLETE，见 `RESULT.md`；固化待独立 Pre-RESULT / `INDEPENDENT_ACCEPTANCE.md` 完成）。注：**B1已返工, 2026-09-24独立重审PASS**（见 `INDEPENDENT_ACCEPTANCE.md`）。

---

## §1 要回答的问题（一个）

在 Jan-21 三源真实 eval 帧上，冻结的 V80 软边际 NB-LDPC（n=1024 GF(32) 符号，构造实例 2026092001）
在与 X1 合成批次**相同的 (源, m, 构造)** 下，FER 是否与合成结果一致？

这是开发决策（合成信道能否继续作为开发代理），不是发表数字、不是认证、不是 SKR。

## §2 冻结输入（改任何一项 = 新包）

| # | 项 | 冻结值 |
|---|---|---|
| F1 | 数据 | Jan-21 Type2 三源，只开 base `X.ttbin`（R1 JSON `ttbin_member_used`）：1M `…/Type2_1M_3s_2026-01-21_184040.ttbin`；1.5M `…/Type2_1-5M_3s_2026-01-21_183806.ttbin`；2M `…/Type2_2M_3s_2026-01-21_183657.ttbin` |
| F2 | 读取 / 对齐 / 配对 / 分帧 | 冻结 A1 / R1 链逐字：`read_ttbin_events` → `align_wrapper.derive_alignment`（§3A 门）→ `_pair_nearest_unique`（窗口 200 ps）→ `_frame_global`（200 ps × 1024 bins）。**断言**：派生偏移 = R1 偏移（−50 / +50 / +50 ps）；配对数 = R1 `n_pairs_N`（525831 / 735780 / 982182）；60/20/20 切分边界 = R1 `split_manifest.json`。任一不等 ⇒ STOP |
| F3 | eval 区 | 按时间排序后的 VAL+HOLD 帧（后 40%）；切成**连续、不重叠的 1024 符号超帧**，余数丢弃并报告。预计 205 / 287 / 383 个（实测为准） |
| F4 | 先验 | **同源 R1-TRAIN 分解**，只读、永不重拟合：1M / 1p5M ← `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz`；2M ← 同目录 `x1_gamma_f03r1_2M_verify.npz`。经冻结 `s2c.bind_empirical_bundle` 校验。**理由**：TRAIN 与 eval 帧在同一切分上，可证不重叠；2M 的历史 `gamma_f03.npz` 来自 V25 年代的另一套 TRAIN（N=559872 ≠ R1 的 589461），无法证明与 eval 不重叠。两者 H 差 0.0006 b/符号（X1 验证日志） |
| F5 | 码 | `x1_arm_runner.construct_standalone(m)`：PEG，λ={2:1}，实例 2026092001，trials 20；构造两次须完全一致 + fc=0 + rank=m（否则 STOP）；girth 记录不设门 |
| F6 | 臂（每源两臂，全部取自 X1 网格） | 1M：m ∈ {197, 201}；1.5M：m ∈ {203, 207}；2M：m ∈ {204, 208}（各源 X1 路由门 m_min + 网格顶点） |
| F7 | 译码 | b2f 软边际逐字：Alice x = a & 31，Bob y = b & 31；`marginal_prior_l2` → `center_rows_prior` → `decode_error_domain_posterior`，max_iter 300，streak 3。本包唯一改动是**用真实 (a, b) 切片替代合成采样**；奇偶校验测试已确认在同一合成抽样上两条路径给出相同结果 |
| F8 | 成功定义 | success = u2 精确匹配（V80 冻结口径）；undetected = 收敛但错（计为失败，永不并入 success）；单次解码 > 300 s = 失败（终态，不重跑） |
| F9 | 只报告的附加列（观测 ≠ 放行，不构成 P3 verdict） | (i) 全 10 位符号一致：û1 = argmax_u g1[u,b]·g2[u,x̂,b]，检验模型里的 H(U1\|U2,B)=0 在真实数据上是否成立；(ii) 每超帧原始符号误差数与 u2 误差数（记忆 / 漂移观测） |

## §3 指标（逐源、逐臂分列，禁止合并）

超帧数、失败数、undetected 数、FER 与 95% Wilson 区间、全 10 位失败数；
`f_super = (5m+64)/(1024·H_corr)`、`f_notag = 5m/(1024·H_corr)`、`f_eff = f_super + 4.785675·FER`
（H_corr = R1 修正值 0.80127 / 0.82729 / 0.83333，各源自己的 H）；
对照列：X1 同 (源, m) 合成 fails/240 与其 95% Wilson 区间；wall、峰值 RSS、解码次数。

## §4 预注册决策规则 D1（开发决策，不是发表主张）

对 6 个臂逐一判定：
- **一致**：真实 FER 与 X1 合成 FER 的 95% Wilson 区间重叠；
- **更差**：真实区间下界 > 合成区间上界；
- **更好**：真实区间上界 < 合成区间下界。

D1 的作用域：只决定“合成信道能否继续作开发代理”。它**不是** P3 verdict，不放行任何 P3 门控动作，
也不允许在任何对外材料里把合成 FER 当真实 FER 引用；对外数字只能来自真实帧实测本身。

路由：
- 6 臂全部“一致”或“更好” ⇒ 合成信道可继续作为开发代理；M3（码设计）在合成上迭代，结果周期性回真实数据确认。
- 任一臂“更差” ⇒ 在信任 M3 的合成结果之前，先做信道条件化（逐超帧自适应先验 / 漂移处理）；
  用 F9(ii) 的逐超帧误差序列定位原因。
- F9(i) 全 10 位失败数显著多于 u2 失败数 ⇒ “L1 层免编码”的假设在真实数据上不成立，需要 L1 披露或联合解码，
  并在会计中补上相应泄漏。

## §5 预算与停止规则

- 每源一个进程、1 CPU；三源可**并行**（3 个进程；本机 8 核）。
- 每源 wall 上限 **5400 s**（超出 ⇒ `INCOMPLETE-wall`，已写行保留，永不续跑）；批次上限 3 × 5400 s。
- 单次解码 300 s（超出 = 该超帧失败，继续下一个；不重跑）；峰值 RSS < 4 GiB（超出 ⇒ `FAIL(budget-rss)` 停止该源）。
- 预计计算量：约 1750 次解码 × 3–4 s ≈ 1.5–2 CPU 小时；并行时 wall 约 45–60 min；另加每源读取 2–4 min。
- **不重跑、不续跑、不自适应**。DECIDE 无预注册修复条款：任何重跑 = 新包 + 新授权 + 新根。
- 任一 F1–F9 需要改动、或任一断言失败 ⇒ STOP 回主线程。

## §6 范围与禁止

- 只写三个新根 `workspace/m0_<uuid8>_<src>`（§7 已冻结）；`results/`、`comparison_bench/outputs_comparison/`、
  既有 workspace 证据根、`src/` / `experiments/` / `tools/` 一律只读。
- 禁止：把 F9 观测列或 D1 判定写成 P3 通过 / 记忆审计已完成；跨源 / 跨臂合并任何计数；把 undetected 并入 success；把 f_super 当 f_eff 报；
  单点 `f_eff ≤ 1.3` 认证句；SKR / 资格化 / 发表主张；commit / push（执行者不做，主线程另行处理）。
- **Claim ceiling**：单一构造实例（2026092001）、单次采集、Jan-21 三源上的开发测量。

## §7 Pre-EXECUTE（2026-09-24 主线程实测）

| 检查 | 结果 |
|---|---|
| 分支 / HEAD | `formal-ir-v72p1-addendum-clean` / `8e9c8526`（WSL 与 Windows 两侧一致） |
| 冻结目录 | `git diff --stat -- src/ experiments/ tools/` 为空 |
| 本包新增文件 | `comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py`、`comparison_bench/tests/test_m0_realframe_fake.py`、本目录两份文档（工作树中其他未提交文件与本包无关，原样保留） |
| focused 测试 | `test_m0_realframe_fake.py`：**7 passed**（Windows conda 与 WSL `.venv` 两侧），含与冻结 b2f 的解码奇偶校验 |
| 环境冒烟 | WSL `.venv` + `install_timetagger_alias()` + `from TimeTagger import FileReader` ⇒ `smoke OK` |
| 输入存在 | 三个 base ttbin 存在；R1 根 `split_manifest.json` 与三个 `T2-*.json` 存在；两个 bundle 文件存在 |
| 输出根（已冻结，实测不存在） | `workspace/m0_359922a7_1M`、`workspace/m0_642a8fe8_1p5M`、`workspace/m0_b1a9142d_2M` |
| 保护根 | `results/` 为空（0 B）；`comparison_bench/outputs_comparison/` 554423395 B，本包不写 |
| 双旗门 | 缺 `--execute-real` 或 `--execution-authorized` ⇒ `Refusal`（测试覆盖） |

执行前须在同一会话内重测：分支 / HEAD、三个输出根仍不存在、`git diff -- src/` 为空。

**确切命令**（WSL，仓库根；三条可并行）：

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m0_realframe_runner --source 1M --root workspace/m0_359922a7_1M --execute-real --execution-authorized
```

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m0_realframe_runner --source 1p5M --root workspace/m0_642a8fe8_1p5M --execute-real --execution-authorized
```

```bash
cd /mnt/d/Code/HD-QKD_Polar_Comparison && PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m0_realframe_runner --source 2M --root workspace/m0_b1a9142d_2M --execute-real --execution-authorized
```

## §8 授权块（唯一填充处；空 = 未授权）

- grant verbatim：`G-M0-REALFRAME GRANT：授权 M0 真实帧闭环执行（三源各两臂，每源 5400 s、单解码 300 s、RSS < 4 GiB、每进程 1 CPU、三源并行，根 m0_359922a7_1M / m0_642a8fe8_1p5M / m0_b1a9142d_2M）`
- 日期 / 授权人：`2026-09-24` / 用户（主线程逐字转达；转达原文见 `RESULT.md` §授权行，逐字一致）
- 预算确认（§5：每源 5400 s、单解码 300 s、RSS < 4 GiB、每进程 1 CPU、三源并行）：`已确认 — 三源各两臂；每源 wall 上限 5400 s；单次解码 300 s；峰值 RSS < 4 GiB；每进程 1 CPU、三源并行；根 m0_359922a7_1M / m0_642a8fe8_1p5M / m0_b1a9142d_2M（与 §5 / §7 冻结值逐项一致）`

## §9 执行后（占位）

- `RESULT.md`：三源结果表 + D1 逐臂判定 + F9 附加列 + 资源；执行者产出。
- `INDEPENDENT_ACCEPTANCE.md`：独立 Pre-RESULT，对照实际产物复核 §2–§6（阈值、undetected 隔离、逐源分列、
  会计、D1 判定）；FAIL ⇒ 不得固化结果。
- 主线程接受后写入 `docs/decision-log.md`，并更新 `docs/RESEARCH_DIRECTION_REPORT_20260924.md` §5 终点表。
