# M2 分层二元合成批次操作 Prompt (M2-LAYEREDBIN-SYNTH) — FROZEN, NOT GRANTED

- Track **EXPLORE** (合成 only；FUTURE 执行；每臂 wall ≤1800 s，单 decode terminal ≤300 s，RSS <4 GiB，1 CPU)。分支 `formal-ir-v72p1-addendum-clean` (不切分支、不 commit、不 push)。出版分支不动。ID 拟 **G-M2-LAYEREDBIN-SYNTH**: 冻结 only，授权 NOTHING。
- 入口: `docs/research_cycles/M2-LAYEREDBIN-SYNTH/PACKET.md` (§§0–9 冻结) + 本 prompt (执行面)。授权见 PACKET §7 (签署前全 BLANK)。
- 零 `.ttbin` 读 (任何读 STOP-BLOCKED)。零译码/DE/图核改动。零 `tools/longrun_*`/`minrerun_*`/`routeA_*`，零 `experiments/run_e2e_pipeline.py`。

## 开始前 (停止条件)

1. 确认 PACKET §7 授权块**逐项完整** (bundle 根 UUID、臂根模式、精确 bundle 路径 + key 前缀、F2 分配整数 + F3 段表 + F4 max_iter/streak 冻结值、网格/种子/实例 verbatim、预算上限、臂序、显式授权签名或逐字 grant)。任一 BLANK/ mismatch ⇒ **STOP-BLOCKED**，返回主线程。不得自行填写。
2. 确认目标分支 + 范围清洁 (`git diff -- src/` empty；仅允许 additive thin runner + verification reporter (若有) + fake-only 测试)、输出缺席 (`workspace/m2lb_*` 缺席；`rg 'm2lb_|M2-LAYEREDBIN-SYNTH'` 仅命中本包三文件；`results/` + `comparison_bench/outputs_comparison/` 字节一致快照) + focused fake-only 测试 (bundle 绑定拒绝门 incl. 跨源标签拒绝、F2 分配 Σm_j=m 算术、F3 段表一致性、构造 pins、bar/gate 算术 incl. N 规则、根拒绝)。记录 Q0–Q6 Pre-EXECUTE。FAIL ⇒ stop。
3. 绑定冻结 bundle (F1): `gamma_f03.npz` + `gamma_f03_pb.npz` 只读；`bind_empirical_bundle()` shape/normalization gates + R1 校验和恒等式 (G-D)。G-D FAIL 之源 ⇒ 该源 STOP-BLOCKED (他源可继续)；无 fallback bundle，无 vintage 替代。
4. 以最终 UUID 紧贴启动前重证目标根缺席 (bundle 根若有 + 首臂根) + HEAD 重测 (若 HEAD ≠ 8e9c8526，记录新 HEAD 并重证 §7 网格/清洁度/缺席，不 silently 沿用)。

## 运行 (一个有界批次；冻结臂序 — 一授权覆盖此条件序列)

5. 根: 臂根 `workspace/m2lb_<uuid8>` (每臂 fresh additive)。`results/` 与 `comparison_bench/outputs_comparison/` 禁止。已有证据根只读不动。
6. 臂序 (冻结；前一机器门通过时 operator 继续臂间，无逐臂授权):
   (i) 绑定验证 (上条步骤 3，门 G-D)；
   (ii) matched-disclosure 对照臂 (三源网格点，同 m 与 NB 对齐披露)；
   (iii) 盲协调臂 (冻结段表 ascending: 先 2M{204,208}，再 1.5M{203,207}，再 1M{197,201}；m=201 为保留冻结表征点，报 OUT/IN 按 G-B 实测，不移网格)。
7. 每臂单次调用: `--arm M2LB-<source>-<m>-<mode>`，`<source>` ∈ {1M,1.5M,2M}，m 取 F1 网格，`<mode>` ∈ {matched,blind}；10 平面分配行 Σm_j=m (F2 冻结整数)；盲臂按 F3 段表 `m_init + {Δm}` 多段小步长；240 块，种子 `2026095601+idx` idx 0..239，流 `o1_blk:{seed}`；构造实例 2026092001，标签 `M2LB-*-S<m>-layered`；pins fc=0 + rank-full + twice-identical GATED。跨源信道复用 FORBIDDEN。
8. 译码: 冻结二元 BP (max_iter/streak 为 §7 冻结值)，`exact_match` 接受；NO genie/argmax。分臂度量: FER=fails/240；f_super/f_notag/f_eff 本臂 m 基 (H ∈ {0.801038,0.825566,0.832563} 用本源 — 永不用他源 H)；λ_total = leak_EC + 64 (tag) + 救援公开量单列（不并入 f 分子） + 控制轮次/帧单列（如适用）；1.50×prior 机会成本另起一行 report-only，不进 λ_total、不进 f 分子；`undetected` 独立成类永不并入 success。
9. 逐臂门 (AND): (a) fails/240 ≤ 12 (bar-12 早停 ⇒ FAIL + CENSORED，永不外推)；(b) f_super ≤ 1.3 本源冻结 H；(c) N ≥ ceil(3·4.785675/(1.3−f_super)) report-only (预期高 m 处 FAIL 常见) — 永不将单源 f_eff 表述为 certifiable。每臂标 monotone / non-monotone / censored；NO 跨 m 单调性推断。
10. 科学输入任一变更 (n、m、tag、H 基、λ、种子、阈值、信道、译码、假设、数据角色、key 前缀、bundle 输入、F2 分配规则、F3 段表) 即 STOP；任何 `.ttbin` 读 STOP-BLOCKED；V19 行数冒充 STOP (必须按位面熵分配重算)。无 pooling；FER>0 时永不引 f_super 作 f_eff。

## 度量 / schema

11. 每臂在其根持久化: `M2LB_RESULT_*.md` (臂 ID、构造标签、bundle 路径 + key 前缀、F2 分配行、F3 段表、种子/实例/pins、wall/RSS、fails/240、FER、iters、f_super/f_notag/f_eff 本臂 m 基 + H 声明、λ_total 四项、undetected 计数、monotone/non-monotone/censored 标签、G-A…G-E verdicts) + `rows.json` (每块一行: 块 idx、种子、iters、wall、decoded/failed/undetected 旗、救援段使用标记) + `block_accounting.csv` (同列机读，A-CMPE-1..7 全列)。TRAIN 侧 provenance + 条件性声明每行携带。不选 operating point。
12. 批次制品: G-D 验证报告；ONE append-only `EXPLORATION_LOG.md` (按臂序尝试；≤1 预注册工程纠正若用则记 exact error + 不变输入见证 + 保留失败位置，否则显式 `no repair path used` 行；保留 INCOMPLETE/CENSORED/BLOCKED 永不覆盖/续跑)。

## 预算 / 停止

13. 每臂 ≤1800 s (单窗)，总额 = 已尝试臂数×1800 s；单 decode ≤300 s terminal；RSS <4 GiB；1 CPU；0 `.ttbin` 读；0 核改动。Wall-partial ⇒ `INCOMPLETE`，保留，永不续跑。≤1 工程 repair+rerun 仅基础设施失败 (科学输入/种子/阈值/数据角色/假设不变，失败保留同根 + log)；第二次失败 ⇒ STOP-BLOCKED，batch-end review 裁决。
14. FORBIDDEN: 任一成员 `.ttbin` 打开/拼接；pooling；译码/DE/图核修改；`src/` 修改；写 `results/`/`comparison_bench/outputs_comparison/`；排除制品读取；`undetected` 合并；发明参数/种子/路径/计数/前缀；commit 或 push。

## 交付物

15. 臂根 (`workspace/m2lb_<uuid8>/` × 已尝试臂): `M2LB_RESULT_*.md` + `rows.json` + `block_accounting.csv`。
16. 批次: ONE append-only `EXPLORATION_LOG.md` + G-D 验证报告 + ONE batch-end 独立 review 文件 + 主线程 acceptance 指针。无逐臂 review 文件。
17. 然后: batch-end 独立 review → 主线程 acceptance → 关闭 (P1 救援基座与 LATER DECIDE 路由按引用消费本曲线；此处无 P1/P2 执行)。该 review 前无发表。

## 解释 / claim ceiling

18. Claim ceiling: 合成分层二元 FER-vs-披露曲线 ONLY。曲线不选 operating point；operating-point 决策是 LATER DECIDE 步骤。Generality 标题以 1M 打头；2M-only 标题 FORBIDDEN。逐位面 0.545% 仅选型依据。`H_L1+H_L2` 以 F03 + TRAIN 分割侧为条件。f-margin IN 与 N-count certifiability 分开 — 保持分开。
19. **Pre-EXECUTE Q0–Q6 + G-D 验证 + 用户授权三者齐备前不得执行任何臂。本 prompt 授权 NOTHING。**
