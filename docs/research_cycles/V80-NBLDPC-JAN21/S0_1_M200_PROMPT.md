# S0.1 软边际 m=200 FER 探针 — Operator Prompt (2026-09-22, EXPLORE, FROZEN, NOT GRANTED)

- Track **EXPLORE**（合成；`EXPLORE_HEAVY` 注记可选；预算 ≤3600 s/臂、≤7200 s 总）。Acceptance ID 拟 **G-S01M200** —— 仅冻结，授权任何执行 = 0。
- 入口：`docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PACKET.md`（§§1–11 冻结）+ 本 prompt（S01-2 执行面）。分支 `formal-ir-v72p1-addendum-clean`（不切分支、不 commit、不 push）。
- 零 `.ttbin` 读取（任一读取 STOP-BLOCKED）；零解码器/DE/图核改动；零 `tools/longrun_*`/`minrerun_*`/`routeA_*`；零 `experiments/run_e2e_pipeline.py`。
- **未授权不得执行。** 本 prompt 自身不构成授权。

## 0. 执行前停止条件（任一不满足 ⇒ STOP-BLOCKED，回主线程）

1. packet §10 授权块**恰好一处**填全（签名或本周期 verbatim 对话 grant），含两臂根 UUID、预算确认。留白/不符 ⇒ STOP，**不得自行填写**。
2. Pre-EXECUTE Q0–Q6 全 PASS 并写入日志条目 0：
   - Q3 输出缺席证明：`workspace/S0_1/` 不存在（最终 UUID 立即复证）；`rg 'S01_|S0_1_M200'` 仅命中本包两文件；`results/` 与 `comparison_bench/outputs_comparison/` 快照字节一致；`git diff -- src/` EMPTY。
   - Q4 **focused 单文件 fake-only 测试**（占位，Pre-EXECUTE 冻结文件名）：
     `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/<S01_TEST_FILE [TO BE FROZEN]> -q` → PASS 输出必须附进日志（E5 规则）。
   - Q5 dry 零解码 pins：A208 `fc=0`/rank 208/twice-identical；基码 `rank(rows[0,200))==200` 否则 STOP-BLOCKED；girth 记录不设门。**Grant 后、首臂前不得有任何生产解码**（含 1-block dry decode）。
3. 入口前置 H0.1（X1 scoped 提交完成或用户豁免）已记录。

## 1. 运行（一次授权覆盖冻结臂序；前臂机器门放行即续，无逐臂授权）

4. 机器根族 `workspace/S0_1/`；逐臂 fresh additive `workspace/S0_1/<arm>_<uuid8>/`。`results/`、`comparison_bench/outputs_comparison/` 禁写；既有证据根只读。
5. 臂序（冻结，各一次调用）：
   (i) `S01-R1` — 构造实例 **2026092001**（girth 8）；
   (ii) `S01-R2` — 构造实例 **2026092011**（girth 6）。**两实例分别报告，禁合并（含 6+4 求和）。**
6. 命令模板（占位，Pre-EXECUTE 冻结 runner 路径与 UUID）：
   `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.<S01_RUNNER [TO BE FROZEN]> --arm S01-R1 --m 200 --instance 2026092001 --blocks 240 --seed-base 2026095601 --root workspace/S0_1/<R1_uuid8>`
   （R2 换 `--arm S01-R2 --instance 2026092011 --root workspace/S0_1/<R2_uuid8>`；其余参数逐字不动。）
7. 冻结 procedure（packet F1–F10 逐字）：基码 = 同实例 A208 的 rows[0,200)（**非** A200 构造，不披露 rows[200,208)）；240 配对块 seeds `2026095601+idx` idx 0..239，stream `o1_blk:{seed}`；信道 `gamma_f03.npz`+`gamma_f03_pb.npz` 只读；b2f 软边际先验 verbatim + v28 `decode_error_domain_posterior(..., 300)` max_iter 300/streak 3、`exact_match` 接受，无 genie/argmax/L1；**解完全部 240 块，禁止 bar-12 早停**（bar-12 仅 report-only 路线上下文）；非 exact_match 计 fail，综合征有效不匹配者单列 `undetected` **永不并入 success**。
8. 度量：逐块 `block_idx, seed, iters, wall_s, decoded, failed, undetected, prior_entropy_bits, u1_mismatches`；逐臂 `k/240`、`FER=k/240`、`f_super=(5·200+64)/852.544=1.24803`、`f_eff=1.24803+4.785675·FER`（本臂自己的 k）、wall/块均值、峰值 RSS、pins、`N_req=277`（report-only）。**绝不把 f_super 当 f_eff 报**；不另算第二基；不选运行点。
9. STOP：任何科学输入变动（n/m/tag/H/λ/seeds/阈值/信道/解码器/假设/数据角色）；任何 `.ttbin` 读取；单调用 >300 s（超时 = 终态，块计 fail，不续）；wall-partial ⇒ `INCOMPLETE-wall` 保留**永不续跑**。无 retry/resume/adaptive；**≤1 次预注册工程修复**（仅基础设施失败、科学输入全不变、失败尝试同日志保留、附 exact error + unchanged-inputs 声明；未用则写 `no repair path used` 行；第二次失败 ⇒ STOP-BLOCKED）。

## 2. 预算

10. ≤3600 s/臂（单窗口）、≤7200 s 总；单调用 ≤300 s；RSS <2 GiB；1 CPU。unspent budget ≠ authorization。估参考：≈2200–2600 s/臂（X1-2M-200S 1589.7 s/163 块、b2f F202 1346.9 s/240）。

## 3. 证据清单（产出物）

11. 逐臂根：`S01_RESULT_<arm>_m200.md`（臂 ID、构造标签+girth、pins、seeds/stream、信道路径、k/240、FER、f_super/f_eff+基说明、undetected 计数、wall/RSS、bar-12 上下文行、S0.1-gate 贡献行、claim-ceiling 行）+ `rows.json` + `block_accounting.csv`。
12. 批次日志（append-only）`docs/research_cycles/V80-NBLDPC-JAN21/S0_1_EXPLORATION_LOG.md`：条目 0 Pre-EXECUTE Q0–Q6（含 Q4 测试输出、H0.1 记录）→ 条目 1–2 逐臂（R1→R2）→ 条目 3 收口 tally（两臂终态、总 wall、修复用否）。保留失败/INCOMPLETE 臂**不覆盖、不续跑**。
13. `S0_1_BATCH_END_REVIEW.md`：**一次** batch-end 独立评审（§10.3）→ 主线程接受 → memory triage（§3）。**无逐臂评审文件。**

## 4. 返回条件（二元，禁止"进行中"式空返回）

14. **COMPLETE**：全部冻结项完成时返回 —— G-S01M200、逐臂 k/240 与 FER、f_super/f_eff、undetected、wall/RSS、S0.1-gate 状态（两臂 240/240 完整 ⇒ PASS；否则 NOT satisfied）、证据路径、Q4 测试输出、`no repair path used` 或修复记录。
15. **BLOCKER**： concrete 阻塞时返回 —— 失败命令、exact error/traceback、已试补救、**只需主线程裁决的一件事**。

## 5. Claim ceiling 与停止语

16. 仅合成效率探针（两实例分报）；非 SKR/资格化/路线/运行点/真实 FER/`f_eff≤1.3` 认证句/发表材料；key-eligible 200/276/364 只引用不消耗。先于任何 3600 s 级 P1 救护臂；S0.1-gate 未 PASS 前**禁止按 10/240 外推冻结 P1**。
17. 禁碰 `docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`.gitignore`、`README.md`、`AGENTS.md`；**禁 commit / push**。
18. **Pre-EXECUTE Q0–Q6 + 授权块填全之前不得执行任何解码。未授权不得执行。本 prompt 授权任何执行 = 0。**
