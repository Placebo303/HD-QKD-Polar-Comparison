# V72P2D3 GF32 对照设计（基于 D1 映射表冻结）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本设计绑定 base `e094f7e548380db4bfcbc1fe73472e670c32379a`、分支 `formal-ir-v72p1-addendum-clean`。它只描述一次合规实现与诊断，不修改 V72P1、V72P2、D1、D2，不授权实现、decoder、真实数据、parquet 或结果输出。

`base_sha/accepted_plan_sha/implementation_sha` 只表示 AGENTS 要求的 Git 版本绑定，不承担数据或 artifact 内容校验。manifest 不含数据或 artifact 内容摘要、签名或其他校验字段。Ponytail lite：算法模块、runner 和 focused test 各一个；薄 adapter 优先历史 kernel；不用框架、插件、事件总线、缓存、锁、retry 或完整消息持久化。不预设优胜者。

## 1. 共同数据、数值和预算

诊断只使用 D1 已固定的同一非新鲜块：session `20260123_1M_600k_0dB` 的 `VAL1726..1729`，四帧连续组成一个 1024-symbol block。规划阶段不读取其 raw/parquet 内容。CAL 固定为同 session `CAL702..1725`，仅用于 G prior 适配；禁止用 VAL 选参/调参/回灌。

A 复用 D1 记录：mother `9036x10240`、`nnz=49620`、check-degree `{4:1,5:4594,6:4441}`、degree-2 列 `9035`；ladder `range(160,8993,128)+[9032,9036]` 72 点；`float64/clip20/tol1e-6`；每 ckpt 10 次、每臂 720 次；`LADDER_EXHAUSTED`、`334 iters`、`3100 bits/620 syms`、`9036+64+71` 计费口径仅作复用比较，不重跑。

G 为 GF32 两层增量对照，同 VAL 块一次运行。预算见 §7。

无 tag 诊断固定 `tag_bits=0`、`tag_bits_published=0`、`tag_ok=NOT_APPLICABLE`；诊断中不生成或处理 tag。V64 `compute_tag_64` 纯函数可复用为只读 helper（canonical 打包口径），但不得生成 tag 泄漏、不得进入门禁。V64 归因禁定论：不得将 V64 Phase A 归因引用为确定根因。

## 2. 映射（D1 冻结，无歧义否则 REVISE）

```text
bit0 = LSB
low  = bits0..4  (u2, 0..31)
high = bits5..9  (u1, 0..31)
symbol = low + 32*high  (即 s = 32*u1 + u2, 0..1023)
```

同方向、无 Gray、无置换。`pack(symbol)->(low,high)` 与 `unpack(low,high)->symbol` 必须 `+1024 roundtrip`（全 1024 值往返一致）。Alice/Bob/CAL/prior/candidate 比较均在同一方向坐标；任一方向歧义、LSB 歧义或 roundtrip 失败即 `REVISE`，不得猜测或默认通过。

## 3. GF32 场、矩阵与嵌套（D1 冻结）

- 场：`q=32`、`poly37 (0b100101)` 统一复用 v35 `GF2mField.create(32)` 数学，不新定义多项式，不改历史 kernel。
- 映射方向绑定 v35 `factorize_f03`：`u1=high/MSB`、`u2=low/LSB`，`symbol=low+32*high`。
- 基矩阵：1M Lane C `H_base=184` 行（`190/192` 为 1p5M/2M 参照，不执行）；`H1=16` 行；`H_total=200` 行。
- 嵌套：前缀 `184/192/200`（Δ8+8），`rank_total==m_total`、`nested`、`row≤16`、`col_inc≤1` 语义沿用 V64 门禁文字；D3 仅在 1M 上执行 `184->192->200` 两层增量。
- layered（A decoder0 家族）vs incremental（G 两层增量）正交：A 不引入增量，G 不引入 binary flooding/layered 混合；不得创建混合臂。

## 4. G decoder（90 硬帽，damping1.0，无 tolerance；唯一真核 R1–R2）

HISTORICAL_KERNEL（R1）：v35 `decode_row_layered_fftqspa` 码字域（长度 `n=1024` 的 GF32 码字向量）；输入 `(H, prior P(X), syndrome H*x)`，输出 `DecoderResult(x_hat, syndrome_ok, iterations 0..max, final_beliefs + runtime/status)`；`0` 为初值即满足，`1..max` 为整层扫描后满足；仅 syndrome 等式停止，无 residual tolerance；`warm_beliefs` 仅 `(n,32)` log-belief 初值（`check_to_var` 恒零初值，非 message carry），V54 生产路径（`_dec_l1` 与 L2 `_dec`）恒 `warm_beliefs=None` 冷启动。

G 两层增量 decoder 冻结：`max_iter=90` 为硬帽、`damping=1.0`、无 residual tolerance；停止条件仅为 syndrome 满足或 90 硬停。BP 用自然 log，CE 用 log2，转换显式（`log2 = ln / ln2`）。`float64`。每层独立计数 `rows/iters`；`actual_iterations` 以 decoder 返回的完整更新数为准，不用请求上限代替。

唯一生产链（R2，生产恒 `decode_fn=None`）：V54 链 `L1(_dec_l1/H1，经 get_l1_prior_p_u1_given_b 的 P(U1|B)，q=softmax(final_beliefs)) + L2三stage(H_base/H_joint/H_total，同 prior_l2=q@P 经 get_l1_app_prior_l2)`，`max90/damping1.0`。禁 argmax 冒充/固定 hard/写死 iters/mock 进生产/简化 decoder/称 binary 为 GF32（binary helper 仅 Arm A）/改历史 kernel。薄 adapter（R3）只做映射/矩阵/prior 方向/syndrome（`s1=H1*u1/s_base=H_base*u2/s_joint/s_total` 均 Alice 侧，经 `syndrome_of_gf32`）/调真核/字段统一（`get_gf32_field` 即 v35 `GF2mField.create(32)` poly37）/stage 编排/diagnostics；生产直调真迭代函数；返回 `x_hat/syndrome_observed/ok/iterations_used/residual 或 NOT_RECORDED/finite/runtime/stop/candidate_changed/vs_bob`，不伪造缺失字段（`residual` 恒 `NOT_RECORDED` 因真核无 residual；无 Bob 层时 `vs_bob/candidate_changed` 为 null；`hard/iters/syndrome_satisfied` 仅为回兼容视图）。每 stage cold start（R4，生产恒 `belief_warm=None`，`belief_warm` 仅初值，不称 message carry）。历史顺序与短路按 R5：`L1(H1,P(U1|B)) → q=softmax(final_beliefs) → prior_l2=q@P → base → joint → total`；L1 失败仍进 L2（L2 恒用 q，不门控），base 满足跳过 joint/total，joint 满足跳过 total（syndrome-only；V54 另含 tag，本计划无 tag）。三审查（D8）必须核真 kernel：import 探针 + tiny 已知答案（含 `iterations==0` 初值满足）+ `rg stub` 零命中，否则 BLOCKED。

## 5. prior（TRAIN-only 数学 + 当前 CAL 适配）

prior 优先历史数学固定，当前 CAL 明确方向：

```text
Stage1: P(high | Bob_side)          即 P(U1 | B)
Stage2: P(low | high, Bob_side)     即 P(U2 | U1, B)
```

builder 只接 physical Bob + 当前 `CAL702..1725` + 冻结参数；禁 Alice、禁旧 session、禁 VAL 选参。`K/P` 先正常归一，`1e-300` 只保护 log；BP 自然 log，CE log2。方向无歧义否则 `REVISE`。生产 L2 prior 为 `prior_l2=q@P`（`q=softmax(L1 final_beliefs)`，经 V54 `get_l1_app_prior_l2` 精确复用）。

必须报告 `joint/low/high CE` 的 log2 链式关系：`|CE_joint - CE_high - CE_low_given_high| < 1e-9`（`CE = -mean(log2 P)`，decoder 自然 log 转换后一致）。`VAL` 仅作确认度量，不参与 `S*/λ` 选择。

## 6. 每 checkpoint / 每层标量诊断（syndrome-only）

G 每层（low/high）每增量阶段只保存标量聚合：`x_hat`、`syndrome_observed`、`syndrome_ok = finite && kernel syndrome_ok && observed==target`、`iterations_used 0..max`、`residual=NOT_RECORDED`、`finite`、`runtime/stop`、`candidate_changed/vs_bob`（与 Bob 层直接比较）、`posthoc_oracle`（仅 arm 结束后）、`public_disclosure_bits`、`control_bits`、`runtime/RSS`。checkpoint 层 oracle 字段为 null，附 `oracle_runs_after_arm_end`。首次满足只记录不早停，继续预注册增量到 200 或预算/异常停止。arm 结束只取最后已完成阶段 candidate 定义 `final_syndrome_satisfied`；oracle 只比较该 final candidate 得 `final_oracle_exact`。最终四分支见 proposal D10。G syndrome 一律经 `syndrome_of_gf32`（禁 binary 冒充 GF32；binary helper 仅 Arm A）。

A 新指标为 null，附 `not_recorded_reason`，不得补造或与 A 定量差分；只比较 D1 已存共同指标。

## 7. 公开计费、预算与输出

G 公开计费冻结 `leak = 5*m_total + 64 = 5*m_base + 80 + 64`（`m_total` 含 H1：`200/208/216 → 1064/1104/1144`；等价 L2-only 行 `184/192/200 → 1064/1104/1144`）：基线 `1064`（184）、stage1 `1104`（192）、stage2 `1144`（200），`+40/+80`。`control_bits_sent` 为 CONTINUE 位（进入下一增量阶段 +1）。`total = syndrome_bits + control_bits`；`tag_bits_published=0`。三臂/两层计数不相加为 session leakage，不称真实 session 泄漏。

D7 全双层门禁：synthetic 全双层（low+high）`wall ≤ 300s`、`peak_rss < 2GiB`、数值/先验相对误差 `≤15%`（相对 brute-force 或解析参照，显式口径），超限即 `PLAN_REVISE_REQUIRED`，不得改算法偷过。D9 真实 G：同 VAL 块一次，A 不重跑，新目录恰四文件，low/high 分层报告 `rows/iters/syndrome/candidate-Bob/posthoc/total/control/runtime`。

输出根固定为 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`，恰 `manifest.json/results.json/table.csv/report.md`。顶层含 `schema/cycle/base_sha/accepted_plan_sha/implementation_sha/session/block/CAL/non_fresh/mapping/field/matrix/nested/decoder/prior/leakage/arms/claim_boundary`；每臂含 `status/rows/iters/syndrome/candidate/posthoc/accounting/runtime`。A 为只读复用结构，G 为实测标量。不保存秘密数组或内容校验字段。

## 8. 后继与文献边界（按任务书）

后继：`G_EXACT` 仅允许同路线小样本 confirmation plan；`G_COLLISION/IMPROVED` 仅描述性；`G_NO_MOTION` 后停止 binary/GF32 小参微调，后继限定为 grouped-symbol mask BP tiny exhaustive 或同块表示消融。文献保留 PEG DOI `10.1109/TIT.2004.839541`、layered DOI `10.1109/SIPS.2004.1363033`、spatial coupling `arXiv:1001.1826`、HD-QKD NB-LDPC `arXiv:2305.08631`，以及 V54 `43/45`、V64 `22/24`、V5-C2 `384/384` 限定域；V67–V72P1 不写成真实纠错成功。

## 9. R2 真实输入适配（prepare-only，additive）

- 链：`validate_prepare_registry`（R2：schema/session/1M/CAL702..1725/VAL1726..1729
  disjoint/禁 1730+/used_2m false/4 列，无 checksum/hash/tag）->
  `load_and_validate_prepare_frames`（R3：受限 4 列，CAL1024x256+VAL4x256，
  pair0..255 有序无 dup/NaN，symbols0..1023，数据行不落盘）->
  `fit_cal_prior_from_frames` + CE（log2）-> `assemble_block_frames`（VAL1726..1729->1024 symbols）->
  D1 A 标量复用（decoder0）-> `factorize_f03` words 方向 -> `nested_geometry` 形状校验
 （H1-16/base184/joint192/total200，syndrome 长 16/184/192/200，max_row_weight16）->
  workspace `prepare_summary.json`（R4-R6：标量-only，`formal=false`，decoder0）。
- G prep 每 stage `NOT_ATTEMPTED_PREPARE_ONLY`（accepted adapter true-kernel 字段，
  短路历史文字，oracle 仅末端，禁 `protocol` 字段）；缺输入 `PREP_FAILED`，预算超限 `BLOCKED`。
- Runner 共用 builder（prepare 与真实入口同一构建，生产不再传 None）；
  `--prepare-only` 不耗授权，`--phase real --execute-real` 仍需 registry+授权否则 fail-closed 2。
