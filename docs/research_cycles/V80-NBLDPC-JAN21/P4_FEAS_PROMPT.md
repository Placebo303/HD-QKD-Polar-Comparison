# P4 n=2048 构造可行性 — Operator Prompt (2026-09-23 · **v2 re-freeze 2026-09-24 — “M2改prompt就runner”**, EXPLORE, FROZEN, NOT GRANTED)

- Track **EXPLORE**（零解码、便宜；单臂 wall ≤1800 s，总量 ceiling 待主线程定；无 HEAVY 注记）。Acceptance ID 拟 **G-P4FEAS** —— 仅冻结，授权任何执行 = 0。
- 入口：`docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_PACKET.md`（§§1–11 冻结）+ 本 prompt（P4-2 执行面）。分支 `formal-ir-v72p1-addendum-clean`（不切分支、不 commit、不 push）。冻结基线 8e9c8526（Pre-EXECUTE 重测记录实际 HEAD）。
- 零 `.ttbin` 读取、零 `gamma_f03*.npz` 读取、零解码器/DE/图核改动、零解码调用（任一违反 = STOP-BLOCKED）；零 `tools/longrun_*`/`minrerun_*`/`routeA_*`；零 `experiments/run_e2e_pipeline.py`。
- **未授权不得执行。** 本 prompt 自身不构成授权。

## 0. 执行前停止条件（任一不满足 ⇒ STOP-BLOCKED，回主线程）

1. packet §10(d) 授权块**恰好一处**填全（签名或本周期 verbatim 对话 grant），含两臂根 UUID、总量 ceiling 定值、预算确认。留白/不符 ⇒ STOP，**不得自行填写**。
2. Pre-EXECUTE Q0–Q6 全 PASS 并写入日志条目 0：
   - Q0 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支；HEAD 实测记录；冻结基线 8e9c8526 仅为时点）。
   - Q1 范围清洁：仅 additive（thin runner + 单文件测试 + Pre-EXECUTE 记录）；`git diff -- src/` EMPTY；脏树按显式文件清单界定，外源 `openspec/changes/binary-ldpc-v5-*` 不纳入。
   - Q2 冻结契约 F1–F10 逐项核对（packet §2，含 F2.1 的 19.7-SUPERSEDED 注记与 F7 口径延拓 §2.1）。
   - Q3 输出缺席证明：`workspace/P4_FEAS/` 不存在（最终 UUID 立即复证）；构造种子字面（2026092001/2011 @n=2048 语境）rg 仅命中本包两文件（+ Pre-EXECUTE 后新增的 runner/测试/记录）；`results/` 与 `comparison_bench/outputs_comparison/` 快照字节一致；`git diff -- src/` EMPTY。
   - Q4 **focused 单文件 fake-only 测试**（占位，Pre-EXECUTE 冻结文件名）：
     `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/<P4FEAS_TEST_FILE [TO BE FROZEN]> -q` → PASS 输出必须附进日志（E5 规则）。
   - Q5 dry pins 门（F6 字面；零解码）：dry 构造 pins（fc/rank/twice-identical/girth 路径）+ `decode_calls=0` 断言。**Grant 后、首臂前不得有任何生产调用（构造亦不得先跑；解码更不得）。**
   - Q6 闭合：入口语境（P1 Stage-1 P4-elevation 输入 + G0=B F3 + 用户顺序 ①→③→②）已记录；总量 ceiling 已定；授权块填全。
3. 入口语境已记录：P1 Stage-1 两臂（R1 FAIL(a) / R2 FAIL(c)，N_req 402/575>eligible）存在；G0=B F3（P4 不自动升格）存在；用户顺序 ①→③→②存在。

## 1. 运行（一次授权覆盖冻结臂序；前臂机器门放行即续，无逐臂授权）

4. 机器根族 `workspace/P4_FEAS/`；逐臂 fresh additive `workspace/P4_FEAS/<arm>_<uuid8>/`（UUID 在 Pre-EXECUTE 冻结）。`results/`、`comparison_bench/outputs_comparison/` 禁写；既有证据根只读。
5. 臂序（冻结，各一次构造 + 一次 twice-identical 复构）：
   (i) `P4F-R1` — 构造谱系 **2026092001**；
   (ii) `P4F-R2` — 构造谱系 **2026092011**。**两谱系分别报告，禁合并。**
6. 冻结命令模板（**双臂单次形，与 runner 实现一致**；runner 名已回填 = `p4_feas_construct`；`<R1_uuid8>`/`<R2_uuid8>`/`<log>` 仍为 Pre-EXECUTE 冻结占位；生产调用须带双旗标，无旗标调用必须被拒）：
   `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.p4_feas_construct --execute-real --execution-authorized --n 2048 --m 416 --trials 20 --seeds 2026092001,2026092011 --lambda-edge {2:1} --rho-rate 0.796875 --r1-uuid8 <R1_uuid8> --r2-uuid8 <R2_uuid8> --root workspace/P4_FEAS --log <log>`
   （**一次调用跑双臂 R1→R2**：机器门续跑，前臂机器门放行即续下一臂，无逐臂授权；**逐臂 per-arm 旧模板（`--arm` / `--instance` / 逐臂 `--root` 形）作废**。其余参数逐字不动。）
7. 冻结 procedure（packet F1–F10 逐字）：`peg_construct(2048,416,λ={2:1},ρ=make_rho(0.796875),seed,trials=20,field=GF(32))` + family 戳记 + three-shift-cyclic 拒绝；全矩阵 rows[0,416) pins（fc=0 + rank 416 + twice-identical GATED）+ 基码 rows[0,400) rank 400 REQUIRED + girth 记录不设门；**零块、零 stream、零信道读取、零先验、零解码**（`decode_calls=0` 门）；**禁跨实例合并**；禁跨 n 推断；禁引 f_super 为 f_eff；禁选运行点；禁另算第二基。
8. 度量（结果全 MEASURED，无预设）：逐臂 §3 字段（pins + 矩阵 provenance + wall/RSS + 恒等行 content_2048=1705.088 / leak=2144 / f_super=1.25741 / headroom 72.61 b / N_req 338 report-only + claim-ceiling 行 + `decode_calls=0` 行）。**绝不把 f_super 当 f_eff 报**；19.7 不得出现为设计数（SUPERSEDED 注记逐字保留）。
9. STOP：任何科学输入变动（n/m/tag/H/λ/ρ/seeds/trials/阈值/信道/解码器/假设/数据角色）；任何 `.ttbin`/`gamma` 读取；任何解码调用；单次构造 >600 s（超时 = 终态 FAIL，不续）；wall-partial ⇒ `INCOMPLETE-wall` 保留**永不续跑**。无 retry/resume/adaptive；**≤1 次预注册工程修复**（仅基础设施失败、科学输入全不变、失败尝试同日志保留、附 exact error + unchanged-inputs 声明；未用则写 `no repair path used` 行；第二次失败 ⇒ STOP-BLOCKED）。

## 2. 预算

10. 单臂 wall ≤1800 s（单窗口，2 次构造 + pins + 报告）；批次总量 ceiling = 授权块所定值（提议 3600 s，待主线程定）；单次构造 ≤600 s；RSS <2 GiB；1 CPU。unspent budget ≠ authorization。估参考（非承诺）：n=1024 O1 族 trials-20 纯内存秒~分钟级；n=2048 三元组 4096 条仍纯内存，帽有大余量。

## 3. 证据清单（产出物）

11. 逐臂根：`P4FEAS_RESULT_<arm>.md`（臂 ID、构造谱系、n/m/λ/ρ/trials/family、pins、girth、sockets/parity、H_anchor + content_2048 + f_super + headroom/N_req 恒等行、`decode_calls=0` 行、wall/RSS、claim-ceiling 行）+ `construction.json` + pins 报告。
12. 批次日志（append-only）`docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_EXPLORATION_LOG.md`：条目 0 Pre-EXECUTE Q0–Q6（含 Q4 测试输出、入口语境、总量 ceiling 定值）→ 条目 1–2 逐臂（R1→R2）→ 条目 3 收口 tally（两臂终态、总 wall、修复用否）。保留失败/INCOMPLETE 臂**不覆盖、不续跑**。
13. `P4_FEAS_BATCH_END_REVIEW.md`：**一次** batch-end 独立评审（§10.3）→ 主线程接受 → memory triage（§3）。**无逐臂评审文件。**

## 4. 返回条件（二元，禁止"进行中"式空返回）

14. **COMPLETE**：全部冻结项完成时返回 —— G-P4FEAS、逐臂 pins（fc/rank-full/twice-identical/girth）+ rank_base_400、恒等行、wall/RSS、三门状态、证据路径、Q4 测试输出、`no repair path used` 或修复记录。
15. **BLOCKER**：concrete 阻塞时返回 —— 失败命令、exact error/traceback、已试补救、**只需主线程裁决的一件事**。

## 5. Claim ceiling 与停止语

16. 仅 n=2048 构造可行性（两谱系分报）；非机制性能（无 FER/转化率/泄漏实测）、非 SKR/资格化/路线裁决（**P4 是否升为 S3 必经不在本包**）/运行点/真实 FER/`f_eff≤1.3` 认证句/发表材料；key-eligible 200/276/364 只引用不消耗。
17. 禁碰 P1 族、S0.1 族、`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENTS.md`、`docs/troubleshooting.md`、`src/`；**禁 commit / push**。
18. **Pre-EXECUTE Q0–Q6 + 授权块填全之前不得执行任何构造。未授权不得执行。本 prompt 授权任何执行 = 0。**
