# P1 Stage-1 速率自适应救援 — Operator Prompt (2026-09-22, EXPLORE, FROZEN, NOT GRANTED)

- Track **EXPLORE**（合成；`EXPLORE_HEAVY` 成本注记：单臂 wall ≤3600 s，总量 ceiling 待主线程定）。Acceptance ID 拟 **G-P1S1** —— 仅冻结，授权任何执行 = 0。
- 入口：`docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_PACKET.md`（§§1–11 冻结）+ 本 prompt（P1S1-2 执行面）。分支 `formal-ir-v72p1-addendum-clean`（不切分支、不 commit、不 push）。冻结基线 85e0771f（Pre-EXECUTE 重测记录实际 HEAD）。
- 零 `.ttbin` 读取（任一读取 STOP-BLOCKED）；零解码器/DE/图核改动；零 `tools/longrun_*`/`minrerun_*`/`routeA_*`；零 `experiments/run_e2e_pipeline.py`。
- **未授权不得执行。** 本 prompt 自身不构成授权。

## 0. 执行前停止条件（任一不满足 ⇒ STOP-BLOCKED，回主线程）

1. packet §10(d) 授权块**恰好一处**填全（签名或本周期 verbatim 对话 grant），含两臂根 UUID、总量 ceiling 定值、预算确认。留白/不符 ⇒ STOP，**不得自行填写**。
2. Pre-EXECUTE Q0–Q6 全 PASS 并写入日志条目 0：
   - Q0 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支；HEAD 实测记录）。
   - Q1 范围清洁：仅 additive（thin runner + 单文件测试 + Pre-EXECUTE 记录）；`git diff -- src/` EMPTY；脏树按显式文件清单界定，外源 `openspec/changes/binary-ldpc-v5-*` 不纳入。
   - Q2 冻结契约 F1–F10 逐项核对（packet §2）。
   - Q3 输出缺席证明：`workspace/P1_STAGE1/` 不存在（最终 UUID 立即复证）；新 seed 区间 `2026096401..2026096640` rg 仅命中本包两文件（+ Pre-EXECUTE 后新增的 runner/测试/记录）；`results/` 与 `comparison_bench/outputs_comparison/` 快照字节一致；`git diff -- src/` EMPTY。
   - Q4 **focused 单文件 fake-only 测试**（占位，Pre-EXECUTE 冻结文件名）：
     `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/<P1S1_TEST_FILE [TO BE FROZEN]> -q` → PASS 输出必须附进日志（E5 规则）。
   - Q5 dry 零解码 pins：A208 `fc=0`/rank 208/twice-identical（逐实例）；基码 `rank(rows[0,200))==200` 否则 STOP-BLOCKED；girth 记录不设门。**Grant 后、首臂前不得有任何生产解码**。
   - Q6 闭合：S0.1-gate 满足 + G0=B 已记录；总量 ceiling 已定；授权块填全。
3. 入口语境已记录：S0.1 锚（R1 79/240 + R2 119/240，分列，禁合并）存在；G0=B（S-B 主路径）。

## 1. 运行（一次授权覆盖冻结臂序；前臂机器门放行即续，无逐臂授权）

4. 机器根族 `workspace/P1_STAGE1/`；逐臂 fresh additive `workspace/P1_STAGE1/<arm>_<uuid8>/`（UUID 在 Pre-EXECUTE 冻结）。`results/`、`comparison_bench/outputs_comparison/` 禁写；既有证据根只读。
5. 臂序（冻结，各覆盖两 Stage）：
   (i) `P1S1-R1` — 构造实例 **2026092001**（girth 8）；
   (ii) `P1S1-R2` — 构造实例 **2026092011**（girth 6）。**两实例分别报告，禁合并（含 6+4 求和；含触发集/转化数相加）。**
6. 命令模板（占位，Pre-EXECUTE 冻结 runner 路径与 UUID；生产调用须带双旗标，无旗标调用必须被拒）：
   `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.<P1S1_RUNNER [TO BE FROZEN]> --execute-real --execution-authorized --arm P1S1-R1 --m-base 200 --m-total 208 --instance 2026092001 --blocks 240 --seed-base 2026096401 --root workspace/P1_STAGE1/<R1_uuid8>`
   （R2 换 `--arm P1S1-R2 --instance 2026092011 --root workspace/P1_STAGE1/<R2_uuid8>`；其余参数逐字不动。）
7. 冻结 procedure（packet F1–F10 逐字）：基码 = 同实例 A208 的 rows[0,200)（**非** A200 构造）；240 配对块 seeds `2026096401+idx` idx 0..239，stream `o1_blk:{seed}`（新区间，与 S0.1 无块身份重合）；信道 `gamma_f03.npz`+`gamma_f03_pb.npz` 只读；b2f 软边际先验 verbatim + v28 `decode_error_domain_posterior(..., 300)` max_iter 300/streak 3、`exact_match` 接受，无 genie/argmax/L1；Stage-1 **冷解码全部 240 块，禁止 bar-12 早停**（bar-12 仅 report-only）；Stage-2 = 对**恰好** Stage-1 非 success 全集披露 rows[200,208) 并 **COLD 全矩阵重解码**（rows[0,208)）；warm-start、non-nested fallback、two-segment/multi-segment **全禁**；非 exact_match 计 fail，综合征有效不匹配者单列 `undetected` **永不并入 success**。
8. 度量（结果全 MEASURED，无预设）：逐块 `block_idx, seed, iters, wall_s, decoded, failed, undetected, prior_entropy_bits, u1_mismatches` + Stage 标记；逐臂 Stage-1 `k/240`、转化数（rescued/attempted=k 恒等）、最终 `F/240`、`r=#rescued/240`、`E[leak]=1064+40·r`、`f_exp=E[leak]/852.544`、`f_eff=f_exp+4.785675·(F/240)`、headroom=`1108.31−E[leak]`、wall/块均值、峰值 RSS、pins、`N_req`（report-only，仅 F=0 相关）。**绝不把 f_super/f_exp 当 f_eff 报**；不另算第二基；不选运行点。
9. STOP：任何科学输入变动（n/m/tag/H/λ/seeds/阈值/信道/解码器/假设/数据角色）；任何 `.ttbin` 读取；单调用 >300 s（超时 = 终态，块计 fail，不续）；wall-partial ⇒ `INCOMPLETE-wall` 保留**永不续跑**。无 retry/resume/adaptive；**≤1 次预注册工程修复**（仅基础设施失败、科学输入全不变、失败尝试同日志保留、附 exact error + unchanged-inputs 声明；未用则写 `no repair path used` 行；第二次失败 ⇒ STOP-BLOCKED）。

## 2. 预算

10. 单臂 wall ≤3600 s（两 Stage 合计，单窗口）；批次总量 ceiling = 授权块所定值（提议 7200 s，待主线程定）；单调用 ≤300 s；RSS <2 GiB；1 CPU。unspent budget ≠ authorization。估参考（非承诺）：Stage-1 ≈ S0.1 实测 871.9/1010.5 s 类；Stage-2 ≤240 次冷 208 解码（≈672.6 s/240 类）。

## 3. 证据清单（产出物）

11. 逐臂根：`P1S1_RESULT_<arm>.md`（臂 ID、构造标签+girth、pins、seeds/stream、信道路径、Stage-1 k/240、转化数、最终 F/240、r、E[leak]、f_exp/f_eff+基说明、headroom、undetected 计数、wall/RSS、bar-12 上下文行、S0.1-锚引用行、claim-ceiling 行）+ `rows.json` + `block_accounting.csv`。
12. 批次日志（append-only）`docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_EXPLORATION_LOG.md`：条目 0 Pre-EXECUTE Q0–Q6（含 Q4 测试输出、S0.1-gate/G0 记录、总量 ceiling 定值）→ 条目 1–2 逐臂（R1→R2）→ 条目 3 收口 tally（两臂终态、总 wall、修复用否）。保留失败/INCOMPLETE 臂**不覆盖、不续跑**。
13. `P1_STAGE1_BATCH_END_REVIEW.md`：**一次** batch-end 独立评审（§10.3）→ 主线程接受 → memory triage（§3）。**无逐臂评审文件。**

## 4. 返回条件（二元，禁止"进行中"式空返回）

14. **COMPLETE**：全部冻结项完成时返回 —— G-P1S1、逐臂 Stage-1 k/240 与最终 F/240、转化数、r、E[leak]、f_exp/f_eff、headroom、undetected、wall/RSS、三门状态、证据路径、Q4 测试输出、`no repair path used` 或修复记录。
15. **BLOCKER**：concrete 阻塞时返回 —— 失败命令、exact error/traceback、已试补救、**只需主线程裁决的一件事**。

## 5. Claim ceiling 与停止语

16. 仅合成救援效率（两实例分报）；非 SKR/资格化/路线/运行点/真实 FER/`f_eff≤1.3` 认证句/发表材料；key-eligible 200/276/364 只引用不消耗。P1 §9 per-source 臂、P2、X1 均不在本包。
17. 禁碰 `docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENT_PROJECT_MEMORY.md`、既有 runner/测试、S0.1 族文件；**禁 commit / push**。
18. **Pre-EXECUTE Q0–Q6 + 授权块填全之前不得执行任何解码。未授权不得执行。本 prompt 授权任何执行 = 0。**
