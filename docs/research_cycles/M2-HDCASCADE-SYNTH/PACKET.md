# PACKET.md — M2-HDCASCADE-SYNTH (EXPLORE, 合成批次包)

**Cycle ID**: `G-M2-HDCASCADE-SYNTH`

## §0 身份

- **Track**: 起草 = doc-only 包起草，无 track gate（AGENTS.md §1.2 矩阵 Documentation-only）；FUTURE 执行 = `EXPLORE`（合成、有界、可逆；非 `EXPLORE_HEAVY`）。
- **Gate 状态**: 停授权前（本包为起草包，未授权、未执行）。
- **分支冻结时点**: `formal-ir-v72p1-addendum-clean` @ `8e9c8526`；执行前重测分支/HEAD（见 §6 机器门）。
- **FUTURE 执行 track**: `EXPLORE`（合成输入、fresh additive root、无 claim；任何真实数据/claim 意图即按 §3 升级为 DECIDE 新包）。

## §1 目的

HD-Cascade（Mueller 2024 路线三处改动）的**合成开发测量**：在冻结 gamma 先验 + 无记忆合成配对帧上打通实现版本、会计列与停止规则，与 T2/X1 同网格可比（同 `(源, m)` 网格、同分母 N），为后续 DECIDE 真实验证准备工程基线。**不产生任何真实 FER/效率/泄漏/SKR 结论**（见 §5 claim ceiling）。

## §2 F1–F6 臂表（冻结臂序，执行时不得加项）

6 臂 = 3 源 × 2 m（每臂 N=240 块）：

| 臂 | 源 | m | N |
|---|---|---|---|
| A1 | 1M | 197 | 240 |
| A2 | 1M | 201 | 240 |
| A3 | 1.5M | 203 | 240 |
| A4 | 1.5M | 207 | 240 |
| A5 | 2M | 204 | 240 |
| A6 | 2M | 208 | 240 |

### F1 数据

- 合成配对帧：冻结 `gamma_f03.npz`（R1-TRAIN 直方图）无记忆模型采样。
- 网格同 M0 `(源, m)`：1M{197,201} / 1.5M{203,207} / 2M{204,208}。
- 每臂 N=240 块；分母与 X1 同分母（可比性锚）。

### F2 码/映射（执行前 pin，以下为待冻结槽位）

- `Mueller三改实现版本`: ____（commit pin，执行前填入）
- `二进制映射表版本`: ____（pin）
- `按位分组块长表`: ____（pin）
- `级联传播开关`: 先并行版（BLIND-PARALLEL-FIRST；串行版不在本包范围，若需对比=新包）
- `按位分组块长表`复述 T0 design §2 表结构：位面 × pass → 初始块长 / 增长 / 封顶；BLANK 槽保留，授权前冻结（执行前填入，不得执行中途改表）。

### F3 译码（执行前 pin）

- `Cascade 轮次上限`: ____（pin）
- `块长下限`: ____（pin）
- `盲并行消息计数规则`: ____（pin）
- `timeout`: 终态失败，不重跑（timeout 块记 failed，保留在分母内；禁止续跑/resume）

### F4 种子（全冻结）

- `cascade_seed`: ____（执行前填入冻结值）
- `分组置换 RNG 种子`: ____（执行前填入冻结值）
- 若 variability 可混淆则多 seed：seed 表整体冻结（表见下，执行前填入；不得执行中途加 seed）：

| 臂 | seed 1 | seed 2（如用） |
|---|---|---|
| A1–A6 | ____ | ____ |

- 种子逐字核对（见 E4）；改任一种子/阈值 = 新包（§3 STOP）。

### F5 会计（A-CMPE-1..7 全列）

- `attempted` / `exact_match`（= ¬failed，含 decoded≠success 的图例说明）/ `accepted` / `accepted_wrong` 独立四列；`undetected` 单列隔离，永不并入 success/FER。
- `f_super` / `f_notag` / `f_eff`：本臂 m 基（分母为本臂 m，不跨臂混算）；冻结公式 `f_super=(5m+64)/(1024·H_src)`、`f_notag=5m/(1024·H_src)`、`f_eff=f_super+4.785675·FER`（FER>0 时永不以 f_super 冒充 f_eff）。
- H 用哪套声明：Cascade 混叠需明示；本包分母用合成 F03 H（1M 0.801038 / 1.5M 0.825566 / 2M 0.832563），与 T2 同；真实 R1 修正 H 仅 M0/T3 用，永不用合成 H 算真实 f。
- `λ_total = leak_EC + 64 + 救援单列(无则记N/A) + 控制轮次分列`；`1.50×prior` 机会成本行单列 report-only，不进 λ_total、不进 f 分子。
- `wall 总 / 每块 / 每译码` + `RSS` + `每帧消息数`（Müller 口径：Cascade 每帧 446 消息数口径独立标注；LDPC 级 3.14 口径不混用，两口径不可互比须标）。
- STOP-BLOCKED（F5 后显式）：禁跨源/跨臂合并计数、禁 pooling、禁 `undetected` 并入 success、禁 f_super 冒充 f_eff、禁把合成 FER 当真实 FER。
- 历史/探针行（A-CMPE-6）：历史行（R3/MLC）与本包口径不一致即标“不可比”+原因；r=10 探针独立成本行（2.1 s vs 19.4 s，native 臂不利如实，不并入主序列）；探针不替真实结论（见 §5 固定句）；V19 f=4.169 为稻草人数，禁作本对照。
- 四列归属（A-CMPE-7）：每个对外数字落 `measured` / `assumed` / `projected` / `qualified` 之一；本批合成结果 = `measured`（本机本实现）；分配输入 H = `assumed`；无预测外推（`projected` 为空）。
- `N_req`：report-only vs key-eligible `200/276/364` 分列。
- `d / q / n_IR` 分离三列。

### F6 根

- 执行根：`workspace/m2hdc_<uuid8>` fresh additive（uuid8 执行前填入）+ 缺席证明（Pre-EXECUTE 记录目标根不存在）。
- `results/` 与 `comparison_bench/outputs_comparison/` 只读：本包任何写入均禁（见 PROMPT 禁令）。

## §3 停止门

1. 改科学输入/种子/阈值/数据角色 = 新包 STOP（当前包冻结，不得继续）。
2. 单臂 wall 超预算：该臂记 `INCOMPLETE` 保留，不续跑、不 rerun、不 resume；其余臂按冻结序继续（若机器门允许）。
3. 至多一次预注册 repair+rerun：科学输入/种子/阈值/数据角色/被测假设不变，仅工程修正；失败尝试留 log，不得覆盖。

## §4 EXPLORE 合约

- 包 + prompt 一对（本 PACKET.md + M2-HDCASCADE-SYNTH-PROMPT.md）。
- 一个 result 根（§2 F6）。
- 一份 EXPLORATION_LOG.md append-only（尝试、预注册工程修正、最终证据、包尾 batch-end review）。
- 一次授权覆盖冻结臂序（操作员按冻结条件臂序继续，前一机器门通过才进入下一臂）。
- 包尾独立 batch-end review（§8 E8）；无逐臂授权/返回/修补审查文件。

## §5 CLAIM CEILING

- 本批 = 合成单实例开发测量。
- 固定句（任何引用本批数值的文档必须逐字携带）：**“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**
- 违反 = E8 FAIL，证据不得 promotion。

## §6 机器门（执行前 Pre-EXECUTE 冻结检查）

- [ ] 分支 = `formal-ir-v72p1-addendum-clean`，HEAD 已重测记录（≠8e9c8526 时注明新 HEAD 并复核 diff 范围）
- [ ] 冻结目录 `src/`、`experiments/`、`tools/` diff 空（相对冻结时点；非空 → BLOCKER）
- [ ] focused fake 测试通过（fake-only，不碰真实数据；命令见 PROMPT 模板）
- [ ] 预算（单臂 wall/RSS 上限）：____（执行前填入）；输出缺席证明已记录
- [ ] 结果根 `workspace/m2hdc_<uuid8>` 缺席已证；`results/`、`outputs_comparison/` 无新增写入计划

## §7 授权块（T1 冻结提案落字，2026-09-24）

- §7-1 N/A 只读：`results/` 与 `comparison_bench/outputs_comparison/` 只读，本包任何写入均禁（同 §2 F6；本 slice 无新增写入计划）。
- §7-2 执行根占位（6 根，fresh additive `workspace/m2hdc_<uuid8>`）：01 = `workspace/m2hdc_3c0f660c`（保留，未建根）；02 = `workspace/m2hdc_a1b2c3d4` / 03 = `workspace/m2hdc_e5f60718` / 04 = `workspace/m2hdc_9a8b7c6d` / 05 = `workspace/m2hdc_5e4f3a2b` / 06 = `workspace/m2hdc_c1d2e3f4`（02–06 真值，主线程冻结；格式 `^workspace/m2hdc_[0-9A-Za-z]{8}$`；Pre-EXECUTE 填入 + 缺席证明）。
- §7-3 数据 bundle：路径 + key 按 T1 冻结（此处仅落位槽，不另展）；H 用冻结合成 F03 H：1M `0.801038` / 1.5M `0.825566` / 2M `0.832563`（FROZEN_H；永不用 H_corr / 真实 R1 修正 H）。
- §7-4 pin 快照槽（T1书面assumption冻结assumed-v1；未关/opsx-explore前禁引Müller真值主张；仅本节落字，§2/他节阈值不动，待/opsx-explore替换）：
  - F2 码/映射（assumed-v1）：`二进制映射表版本`=assumed-v1（10bit→appropriate binary representation→位面分组（Gray无原文依据，永标assumed，按Müller原文ar5iv 2307.02225v2 §2.3.2/Table 2），Alice基准/Bob本地，先并行版；列=assumed；未关/opsx-explore前禁引Müller真值主张）+ `按位分组块长表`=assumed-v1（10位面×2 pass统一`[8,4]`：pass0块长8/pass1块长4，floor 1，表结构沿runner provisional，列=assumed；非原文，assumed-v1 provisional，真值为QBER-自适应k1..k6公式，n=2^16 bits，按Müller原文ar5iv 2307.02225v2 §2.3.2/Table 2；未关/opsx-explore前禁引Müller真值主张，待/opsx-explore替换）+ `Mueller三改实现版本`=`comparison_bench/src/comparison_bench/methods/hd_cascade.py` @ `8e9c8526`（`git rev-parse --short HEAD`只读值，不改代码；列=pinned代码版本，非Müller真值主张）。
  - F3 译码（assumed）：`max_passes`=4（列=assumed；非原文，assumed-v1 provisional，真值为QBER-自适应k1..k6公式，n=2^16 bits，按Müller原文ar5iv 2307.02225v2 §2.3.2/Table 2；未关/opsx-explore前禁引Müller真值主张）+ `块长下限`=表最小值（=1，floor1；列=assumed；未关/opsx-explore前禁引Müller真值主张）+ `盲并行消息计数规则`=现行provisional公式（`messages_actual`按decode outcome上报累加，Cascade 446仅独立参考列、LDPC 3.14非可比；列=assumed；非原文，assumed-v1 provisional；禁446外实测口径主张；未关/opsx-explore前禁引Müller真值主张）+ `max_cross_plane_sweeps`=1（列=assumed；非原文，assumed-v1 provisional；未关/opsx-explore前禁引Müller真值主张）。
  - F4 种子（assumed新常数冻结，不复用P4谱系，与T2/X1 2026095601族区分；列=assumed；未关/opsx-explore前禁引Müller真值主张；种子逐字核对见E4，改任一种子/阈值=新包）：A1-A6各一种子，seed1=seed2=同值（单一种子臂，无第二独立种子），合成采样种子流同seed，`permutation`=`seeded_random`：
    | 臂 | seed 1 | seed 2 |
    |---|---|---|
    | A1 | 2026095701 | 2026095701 |
    | A2 | 2026095702 | 2026095702 |
    | A3 | 2026095703 | 2026095703 |
    | A4 | 2026095704 | 2026095704 |
    | A5 | 2026095705 | 2026095705 |
    | A6 | 2026095706 | 2026095706 |
   - 种子映射 `ARM_SEED`：A1=2026095701 / A2=2026095702 / A3=2026095703 / A4=2026095704 / A5=2026095705 / A6=2026095706；块 k=ARM+k；stream/instance 保留；Runner 5601 作废；实现缺口声明：`run_execution` 恒 None 拒，待 R3（本包种子/阈值不动）。
- §7-5 网格 verbatim（同 §2 F1/F2）：A1 1M 197 / A2 1M 201 / A3 1.5M 203 / A4 1.5M 207 / A5 2M 204 / A6 2M 208，N=240；种子流槽 BLANK（T1 与 T2 差异点显式声明：T1 种子流槽保持 BLANK，T2 另行冻结）。
- §7-6 预算：每臂 wall 5400s / 单 decode 300s / RSS<4GiB / 1CPU；总额 6×5400=32400s；单臂超限记 `INCOMPLETE`，不续跑/不 rerun/不 resume（同 §3）；Runner 1800 作废，待 R1（本包阈值不动）。
- §7-7 臂序冻结：A1→A2→A3→A4→A5→A6（不得加项；操作员按冻结序继续，前一机器门通过才进入下一臂）。
- §7-8 授权语 verbatim：“授权不用找我，我现在一并授权”（用户 2026-09-25 原文落字，覆盖 HDCASCADE T1，非跨 cycle，一授权覆 A1–A6；转述不作依据，以本句 verbatim 为准；待主线程见证；见证前 EXECUTE 保持 STOP）。
- §7-9 日期：2026-09-24。

## §8 验收 ID（G-M2-HDCASCADE-SYNTH 子项 E1–E8）

- **E1 范围白名单**：零外改 `src/`；`EMPTY`（禁写根）零写；仅 §2 F6 根 + 三个包文件可写。
- **E2**：focused fake-only 测试 PASS，附输出。
- **E3**：恰 6 臂（3 源 × 2 m）× 240 块，按冻结序，无加项；`nb_decode_calls = 0`（口径 = 不调 NB 生产译码器，Cascade 为受试方法）。
- **E4**：种子逐字 = 冻结 seed 表（§2 F4）。
- **E5**：预算合规（单臂预算内）或 `INCOMPLETE` 无 rerun/resume。
- **E6**：记录字段 = §2 F5（含 A-CMPE 全列，`undetected` 单列）。
- **E7**：log `entry 0` → 逐臂条目 → 收口 tally +（`no repair path used` 或修复记录齐全未覆盖）。
- **E8**：claim ceiling 零违反（§5 固定句）；batch-end review PASS。

## §9 与 T0 设计 / M0 关系

- 实现以 T0 design pin 为准（pin 见 §2 F2）；Mueller 歧义点标“待澄清”，不猜（歧义清单）：____（执行前填入，如无则填“无已知歧义”）。
- M0 真实数：引用不重跑，只指针（M0 `PREREG_AND_AUTH.md` / `RESULT.md` 路径指针）：`docs/research_cycles/M0-REALFRAME/`。
