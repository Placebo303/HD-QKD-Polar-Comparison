# P1 Stage-1 速率自适应救援 — Exploration Log (EXPLORE_HEAVY, append-only)

- Packet：`P1_STAGE1_PACKET.md`（P1S1-1）+ `P1_STAGE1_PROMPT.md`（P1S1-2）。Acceptance ID：**G-P1S1**。
- Track：**EXPLORE**（合成、有界、可逆；`EXPLORE_HEAVY` 成本注记）。Claim ceiling 见 packet §9（合成救援效率 ONLY；非 SKR/资格化/路线裁决/发表材料）。
- 本日志 append-only：条目只增不改；失败/INCOMPLETE 保留，不覆盖、不续跑。

## 条目 0 — Pre-EXECUTE Q0–Q6 + 授权（2026-09-22，执行前）

- 基线：分支 `formal-ir-v72p1-addendum-clean`（未切分支）；实测 HEAD = **`e2236766`**（full `e22367662124e6e4622e24b8d61a86fded3d9ef2`）。
- 授权（全包唯一填充处 = packet §10(d)，本条目只转录）：grant verbatim =
  `G-P1S1 GRANT：授权P1 Stage-1速率自适应救援执行（2臂 P1S1-R1/P1S1-R2，m_base=200+Δm=8→总行208≤208硬顶，Stage-2=Stage-1非success全集，分列禁合并，双旗标 --execute-real --execution-authorized，基线HEAD e2236766）`；
  臂根 `workspace/P1_STAGE1/P1S1-R1_ef7da79b` / `workspace/P1_STAGE1/P1S1-R2_22754019`（Pre-EXECUTE 冻结 + 缺席已证）；
  预算 6 项全确认（单臂 ≤3600 s；总量 ceiling = 7200 s；单调用 ≤300 s 超时终态计 fail 不续跑；RSS < 2 GiB；1 CPU；零 `.ttbin`/零真实数据/零 `results/` 与 `outputs_comparison/` 写入）；
  日期/主线程 2026-09-22/main；签名 from kai；UUID: P1S1-R1_ef7da79b / P1S1-R2_22754019。
  （`P1_STAGE1_PREEXEC.md` Q6 预算/签字镜像栏**不是**第二授权路径。）
- Q0 目标分支/HEAD：PASS（上列实测值；与授权基线 `e2236766` 一致）。
- Q1 范围清洁：PASS — `git status --porcelain` 仅 5 个 additive 未跟踪文件（runner + 单文件测试 + packet + prompt + preexec）；`git diff --stat` EMPTY；`git diff -- src/ experiments/ tools/` EMPTY。
- Q2 冻结契约 F1–F10：PASS（逐项核对见 `P1_STAGE1_PREEXEC.md` Q2；runner 落点：`ARMS` 双臂表、200+8=208 双硬顶断言、`2026096401+idx`、`o1_blk:{seed}`、s2c 只读绑定、b2f verbatim + v28 max300/streak3 exact_match、F6 四门、F7 本臂自算、report-only N_req、无早停 + attempted==k 恒等、undetected 分列）。
- Q3 输出缺席/保护根：PASS — `workspace/P1_STAGE1/` 不存在（`ls` 实测 + dry `roots.family_exists=false` 复证；双 UUID 根双不存在）；`git grep "20260964"` 跟踪树零命中；runner 内 `ttbin` 仅 2 处断言"无读取路径"的字面（docstring L25 + 报告行 L472，无 import/path/read）；`results/` = 0 B 空；`git diff -- src/` EMPTY。
- Q4 focused fake-only 测试：PASS — `PYTHONPATH=… .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_p1_stage1_runner.py -q` ⇒ **`16 passed, 1 warning in 5.95s`**（本条目执行前实测；warning = 已知 benign `cache_dir` 未知配置项）。
- Q5 dry 零解码 pins：PASS — `--dry` ⇒ `DRY-PASS`（字面 pins；`decode_calls=0`）；`--dry --construct-pins` ⇒ **`MEASURED-DRY (zero decode)`**，`decode_calls=0`，
  R1（2026092001）：`four_cycles=0` + `rank=208` + `twice_identical=true` + `base_rank=200==200 REQUIRED` + girth 8（记录不设门）+ `full_m=208`，
  R2（2026092011）：`four_cycles=0` + `rank=208` + `twice_identical=true` + `base_rank=200==200 REQUIRED` + girth 6（记录不设门）+ `full_m=208`。
  Grant 前生产解码 = 零。
- Q6 闭合：PASS — 入口语境已记录（S0.1-gate `S0_1_BATCH_END_REVIEW.md` PASS_WITH_FINDINGS：R1 79/240 + R2 119/240 分列；G0=B）；总量 ceiling = 7200 s 已定；packet §10(d) 授权块已填全（上列转录）。
- 修齐声明：执行尚未开始；`no repair path used`（待条目 3 收口时复核）。

## 条目 1 — P1S1-R1 执行（2026-09-22/23，COMPLETE）

- 命令：`PYTHONPATH=… .venv/bin/python -m comparison_bench.src.comparison_bench.cli.p1_stage1_runner --execute-real --execution-authorized --arm P1S1-R1 --m-base 200 --m-total 208 --instance 2026092001 --blocks 240 --seed-base 2026096401 --root workspace/P1_STAGE1/P1S1-R1_ef7da79b`（双旗标 + 冻结字面全匹配；exit 0）。
- 结果：Stage-1 `k=84/240`（FER 0.350000）；Stage-2 `attempted=84==k` 恒等 ✓；`rescued=83/84`；最终 `F=1/240`（FER 0.004167）；`undetected=81` 单列分列（未并入 success）✓。
- 会计（本臂自算，冻结 anchor 基 content=852.544 b）：`f_super` 基线 1.248029 / 全触发 1.294948（恒等行，非 f_eff）；`E[leak]=1077.83 b`（r=0.345833）；`f_exp=1.264255`；`f_eff=1.284196`；`headroom=30.48 b`；`N_req=402` report-only。
- 资源：wall 1478.4 s（≤3600 ✓）；route-ctx FAIL（k>12）report-only；verdict COMPLETE。
- 三门（本臂，记录不裁决）：(a) F/240=1/240≠0 → FAIL；(b) `f_exp=1.264255≤1.3` → PASS（worst-case 按构造 ≤1.3）；(c) headroom 30.48≥21.5 → PASS。
- 证据：`workspace/P1_STAGE1/P1S1-R1_ef7da79b/` 下 `P1S1_RESULT_P1S1-R1.md` + `rows.json`（stage1 240 行 + stage2 84 行）+ `block_accounting.csv`（324 行，列契约 ✓）。
- S0.1 锚引用（机制语境，非配对身份，非预测）：S01-R1 79/240 vs 本臂 Stage-1 84/240（新帧实现，数值差异在预期内，无主张）。

## 条目 2 — P1S1-R2 执行（2026-09-23，COMPLETE）

- 命令：同条目 1 模板，`--arm P1S1-R2 --instance 2026092011 --root workspace/P1_STAGE1/P1S1-R2_22754019`（其余逐字不动；exit 0）。
- 结果：Stage-1 `k=138/240`（FER 0.575000）；Stage-2 `attempted=138==k` 恒等 ✓；`rescued=138/138`（全转化）；最终 `F=0/240`；`undetected=134` 单列分列（未并入 success）✓。
- 会计（本臂自算）：`f_super` 基线 1.248029 / 全触发 1.294948；`E[leak]=1087.00 b`（r=0.575000）；`f_exp=1.275008`；`f_eff=1.275008`（F=0 故 slope 项为零）；`headroom=21.31 b`；`N_req=575` report-only。
- 资源：wall 1554.4 s（≤3600 ✓）；iters s1 8–300 / s2 8–47；route-ctx FAIL（k>12）report-only；verdict COMPLETE。
- 三门（本臂，记录不裁决）：(a) F/240=0 → PASS；(b) `f_exp=1.275008≤1.3` → PASS；(c) headroom 21.31<21.5（r=57.5%>57.0%）→ FAIL（marginal）。
- 证据：`workspace/P1_STAGE1/P1S1-R2_22754019/` 下 `P1S1_RESULT_P1S1-R2.md` + `rows.json`（stage1 240 行 + stage2 138 行）+ `block_accounting.csv`（378 行）。
- S0.1 锚引用（机制语境，非配对身份，非预测）：S01-R2 119/240 vs 本臂 Stage-1 138/240（新帧实现，无主张）。
- 分列声明：两臂分别报告，未做任何跨实例合并（含 6+4 求和、触发集/转化数相加均无）。

## 条目 3 — 收口 tally（两臂终态，停在 batch-end 评审门前）

- 终态：R1 COMPLETE（F=1/240）+ R2 COMPLETE（F=0/240）；INCOMPLETE/失败臂 = 0；wall-partial = 无。
- wall 合计：1478.4 + 1554.4 = **3032.8 s**（批次 ceiling 7200 s ✓，余量 4167.2 s；unspent budget ≠ authorization）。
- 修复：`no repair path used`（零基础设施失败，预注册修复未动用；科学输入/seeds/阈值全程不变）。
- 禁令遵守：`undetected` 分列单列（81 / 134）永不并入 success；禁合并（含 6+4）遵守；无早停（两臂 Stage-1 均跑满 240）；`f_super` 未作 `f_eff` 引用；零 `results/`/`outputs_comparison` 写入（`results/` 仍 0 B）；禁碰文件全程未动；无 commit/push。
- 下一步：`P1_STAGE1_BATCH_END_REVIEW.md` 单次独立评审（主线程组织；本执行到此停止，不做独立评审）。

## 条目 3-附记 — 收口补记（只读转述，不改条目 0–3，停在 batch-end 评审门前）

- 实例/girth（RESULT 只读转述）：R1 实例 2026092001 / girth 8；R2 实例 2026092011 / girth 6。
- R1 终败定位（只读转述）：唯一终败 blk178（stage2 iters 300）；final F=1/240=0.004167。
- 分列 tally（禁合并）：R1（Stage-1 240/240 k=84 FER 0.35 undetected 81；Stage-2 attempted 84 rescued 83）/ R2（Stage-1 240/240 k=138 FER 0.575 undetected 134；Stage-2 attempted 138 rescued 138 final F=0/240=0.000000）分别列示，未做任何跨实例合并（含 6+4 求和、触发集/转化数相加均无）。
- attempted==k 恒等门：R1 attempted 84==k ✓ / R2 attempted 138==k ✓，双通过。
- 会计复述：R1 E[leak] 1077.83 r=0.345833 f_exp 1.264255 f_eff 1.284196 headroom 30.48 b N_req 402 ro；R2 E[leak] 1087.00 r=0.575 f_exp 1.275008 f_eff 1.275008 headroom 21.31 b N_req 575 ro。
- 资源包络（累计，只读转述）：wall 合计 3032.8 s / ceiling 7200 s ✓；单块 max ~76 s < 300 s；RSS 峰值 0.502 GiB < 2 GiB；1 CPU；零 ttbin / 零真实数据 / 零 results-outputs 写入；修理 path 未使用。
- 显示中间态（观测记录，非结论）：Stage-2 进行中 RESULT 的 r 曾短暂 0.000000，但最终 R1 r=0.345833 / R2 r=0.575000 自洽。
- R2 headroom 语境：21.31 b 略低于 gate(c) 21.5 b，属 report-only 上下文，不由本日志裁决。
- claim ceiling（重申 header，不扩展）：合成效率 ONLY；非 SKR / 资格化 / route 裁决 / 运行点选择；禁单点 f_eff≤1.3 认证句（N_req 402/575 > key-eligible 200/276/364，与 X1 joint-∅一致）。
- 停止：本执行到此停止，不做独立评审；下一步 batch-end 评审（主线程组织）。
