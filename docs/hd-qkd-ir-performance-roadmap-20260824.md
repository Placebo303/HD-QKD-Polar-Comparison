# HD-QKD IR 性能优先科研路线图（2026-08-24）

## 1. 第一性目标

本项目是科研代码，不以成熟软件包、通用框架或部署工程为目标。第一性目标是：

> 在当前 1024-bin、三类真实时间戳信道上，找到统计模型匹配、泄漏可接受、有限长度
> 可实现，并能提高净密钥率的信息协调方法。

这不是建议性的排序，而是项目的严格优先级：算法假设、算法实现和高信息量性能
实验优先于包规范、通用框架、防御性加固、穷尽式审计与 verifier 深度。只有当工程
问题会具体导致数值/科学结论错误、不可复现、未经授权的昂贵执行或覆盖既有数据时，
它才可以阻塞算法工作；其余问题记录为 non-blocking/deferred。

工程工作的价值只按三件事衡量：是否防止科学问题被算错，是否使实验可重复，是否
缩短下一次高信息量判别。不会为假设性的多用户、恶意输入、跨平台发布、通用插件、
缓存、回滚或成熟包接口增加代码。

最终目标函数不是单独的 reconciliation efficiency `f`，而是至少同时记录：

- 接受帧比例与 FER；
- syndrome、验证 tag、交互消息的实际 leakage；
- 成功帧净 key-rate；
- 运行时间、迭代数与内存；
- qualification 数据边界与 privacy-amplification 口径。

## 2. 当前证据状态

审计基线：`main`，V33 在 HEAD `41d31151` 上获得用户 `EXECUTE_AUTH` 后恰一次
完成正式 `run_01`。本轮运行了冻结的 30-call ensemble DE；没有运行 decoder、
finite-control、原始数据流水线或 successor。

| 证据 | 已证明 | 未证明 |
|---|---|---|
| V25 empirical channel | 三源 train/holdout 分离；经验 `P(A,B)` 明显优于 QSC/product surrogate | 任一有限码可用 |
| V26 | F03/A02 在历史 `f=1.3` 操作点的 ensemble DE 通过 | V31 实际层率、固定图、FER |
| V27R | 源自适应总泄漏预算在 `n=1024` 起有名义余量 | 该分配在实际层率下渐近收敛 |
| V30R | 测试的 n=1024 有限图/decoder 转换失败 | NB-LDPC 总体失败 |
| V31 | n=1024 QC packet 在真实有限窗上 0/300；n=2048 只有 14-block 前缀 | 完整 n=2048 结论；失败根因 |
| V32 correction | B1 generator/posterior 不匹配；原 `finite_graph_decoder_mismatch` 归因无效 | fixed graph 或 decoder 已被独立定罪 |
| V33 | 30/30 calls、六格 5/5 PASS；strict verify 一致；ER1 ACCEPT | fixed packet、decoder、FER、finite-code 或 qualification |

V31 的权威生命周期是 `ARCHIVED_PARTIAL`：n=1024 负结果完整，n=2048 不完整。
V32 科学结论是 `bridge_inconclusive`。这些边界不能因后续路线需要而改写。

## 3. 数据特点及其方法学含义

| source | pairs | raw SER | train 非零格 | 1024² 占用率 | `H(A|B)` bits/symbol |
|---|---:|---:|---:|---:|---:|
| 1M | 512,000 | 0.2397793 | 2,384 | 0.227% | 0.80104 |
| 1p5M | 708,352 | 0.2544695 | 2,436 | 0.232% | 0.82557 |
| 2M | 933,120 | 0.2557410 | 2,635 | 0.251% | 0.83256 |

主要特点：

1. 经验联合分布约 99.75% 格点为零，错误质量几乎集中在相邻 bin。
2. 相邻误差方向随 delay 符号翻转，source/delay 条件不能被平均掉。
3. QSC 把结构化误差扩散到整个字母表，条件熵约 3.2--3.35 bits/symbol，严重
   高估真实不确定性。
4. F03 两层中 L1 泄漏/需求比约 3.0--3.2，L2 仅约 1.16；当前主要压力在 L2，
   不是总预算。
5. 三源纯 syndrome 名义余量约 +179.7/+184.6/+187.5 bits。它只解除立即的
   Shannon veto，不证明 DE 或有限码可行。

由此得到的硬原则：三源分别建模；训练计数只用于设计；validation/holdout 不得
参与选择；任何 synthetic control 必须直接抽样经验联合 `P(A,B)`，不能再用
raw-SER + uniform nonzero delta 代替。

## 4. 已完成的最高价值实验：V33

科学问题只有一个：在 V25 empirical `P(A,B)`、F03/A02、V31 实际层率下，
六个 source×layer cell 的 ensemble MC-DE 是否全部收敛？

固定操作点：

- `n=1024`，`m1=16`，L1 `R=0.984375`；
- L2 `m2=184/190/192`，`R=0.8203125/0.814453125/0.8125`；
- 三源独立，L2 true-predecessor-conditioned；
- 5 seeds/cell，30 calls；`n_samples=2000`，`max_iter=200`；
- `H_t < 0.01 bits/symbol` 连续 20 iterations 才 PASS。

### 正式结果

- Overall：`PASS / pass_rate_aligned_empirical_de`。
- 30/30 calls PASS；六个 source×layer cell 均 5/5 PASS；无 reason code。
- L1 iteration range 23–25；L2 range 37–44。L2 明显更慢，但仍在冻结判据内收敛。
- 总执行约 60.8 s；没有 per-call runtime/CPU/memory 字段，因此不作更细吞吐声明。
- strict verify：`consistent / problems=[] / records_checked=30`；独立 ER1 ACCEPT。
- V33 OpenSpec 已归档；状态为 `ARCHIVED / SUCCESSOR_NOT_AUTHORIZED`。

该结果解除“V31 实际层率在 empirical-P ensemble 层已经不可行”的否决，但不证明
QC packet、decoder、FER 或净 key-rate。最终 entropy floor 约 `3.09e-296` 是数值
概率下限，不是有限码零误码。

### IR1 最小验收

只保留会影响科学归因的检查：

```powershell
python -m py_compile comparison_bench/src/comparison_bench/cli/run_nonbinary_v33_rate_aligned_empirical_de.py
python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v33_rate_aligned_empirical_de prepare
python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v33_rate_aligned_empirical_de test-selfcheck
python -m pytest -q -p no:cacheprovider --basetemp workspace/v33_ir1_final comparison_bench/tests/test_nonbinary_v33_rate_aligned_empirical_de.py
```

验收必须确认 R4 的经验重算 H/m_total/f_total、R6 的 rate+H layer identity、
经验 train-only 输入、真实 GF(32) 身份、固定调用矩阵、fake-runner 隔离和
official root 未创建。CLI 美观、通用配置、成熟包 API 不是 blocker。

### 正式执行门

IR1 已于 2026-08-24 通过；用户随后对 HEAD `41d31151` 明确授予一次
`EXECUTE_AUTH`，下列命令已经恰一次完成：

```powershell
python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v33_rate_aligned_empirical_de execute --execute-auth-file <accepted-auth.json>
```

禁止 smoke、run_02、resume、补 seed、调阈值或在看到中间结果后改分配。随后只读：

```powershell
python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v33_rate_aligned_empirical_de verify --run-root comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v33_rate_aligned_empirical_de/run_01
```

### V33 分流

- 任一 cell `INCONCLUSIVE`：修输入/数值定义，只能在新授权下决定是否有 successor；
  不把它当 FAIL。
- 任一 cell `FAIL`：停止 finite-control；进入 R2 分配/映射/系综研究。
- 六个 cell 全 PASS：本分支已触发。当前只授权提出一次 corrected matched
  finite-control；不自动执行。

## 5. PASS 后的一次归因实验：V34 当前到达 P3 候选

corrected matched finite-control 的职责不是选码，而是回答：当合成数据与 posterior
都来自同一个经验 `P(A,B)` 时，现有 QC packet+decoder 是否仍失败？

最小冻结设计：同一 V31 QC packet、同一 decoder、oracle L1、20 blocks/source、
fresh frozen seeds、三源分别报告、无 tuning/rerun。

截至 2026-08-24，V34 已完成 FR1、独立科学复核和主控 ACCEPT_FREEZE，并形成
P3 最小实现候选。冻结细节为：直接从各源 train empirical P(A,B) 抽样；NumPy
2.4.0 + `V34-PCG64-REF1`；source-major 60 calls；V31 m2=184/190/192；V32
oracle-L1/V28R decoder；max_iter=30；每源 >=19/20 仅作机械判据。compile、
selfcheck、真实输入只读 prepare 与 13 个 fake focused tests 均通过，官方输出根
不存在。

当前状态不是 IR1 ACCEPT，也不是可执行状态。下一步固定为 Ox Alpha 完成 P4
fake T2/T3 证据，再由独立 Codex 做 IR1；任务包见
`docs/v34-p3-implementation-candidate-and-ox-alpha-handoff-20260824.md`。
任何真实 decoder call 仍需 IR1、主控 implementation ACCEPT 和新的用户
EXECUTE_AUTH。

- 若明显通过：瓶颈转向真实误差传播、非 oracle L1 与有限余量。
- 若仍失败：关闭对当前 `lambda={2:1}` + 当前 finite conversion 的继续微调；
  不再搜索 PEG/QC seed、局部边标签或小范围 girth。

文献显示 degree-2 标准系综存在有限长度 block-error 风险。因此 matched control
只做一次归因，不能成为无限循环的图构造调参入口。

## 6. R2：性能主线的结构性转向

触发条件：V33 FAIL，或 V33 PASS 但 matched finite-control FAIL。

候选按优先级：

1. **allocation/factorization 联合搜索**：在 empirical-P 上比较 F02/F03/F04/F05、
   层序、L1/L2 泄漏分配；先做链式熵与 ensemble gate，不构图。
2. **informed NB-MLC/JRDO/IDC**：联合优化 mapping、layer rate 与 degree
   distribution；优先于直接 GF(1024) NB-Polar，但仍先做 empirical-P ensemble P0。
3. **protograph/MET**：限制长 degree-2 链，显式设计不同 node/edge type；以
   block-error 结构为目标，不只优化 bit entropy threshold。
4. **单一结构化 finite realization**：只有 ensemble 通过后，才比较一个
   protograph lifting 与一个 Block-MDS/QC 候选；不做 seed 搜索。
5. **rate-adaptive mother code**：研究 check-node splitting、puncture/shorten、
   Raptor-like incremental redundancy 或乘性重复的适用区间；三个 source 共享
   母结构但使用不同公开 rate。

筛选目标从单独阈值改为预估净 key-rate：

`accepted_fraction * (raw_secret_budget - actual_leakage) / acquisition_time`。

停止条件：一个候选在 matched empirical-P ensemble gate 失败即关闭；有限图
第一次冻结 gate 失败后，不在同一 confirmation 数据上调参。

## 7. R3：Polar/MLC 作为受控备选

R3 只做低成本 P0，不与 V33 争夺主要计算预算：

1. 重算 10 个 bit-plane 在三个 empirical channel 上的链式条件熵；
2. 比较 natural/Gray/少量物理合理 mapping 的可靠性排序；
3. 估计 binary-MLC 的层率、error propagation 和总 leakage；
4. 对 q-ary/NB-Polar 只做复杂度与 reliability-method feasibility。

直接 GF(1024) NB-Polar 可能有 `q^2` 级 decoder 代价；在没有可靠性构造与小规模
golden check 前不实现。现有两层 Law A 不能作为 NB-Polar 可行性证据。

## 8. R4：HD-Cascade 性能锚点

HD-Cascade 可与主线并行，但使用独立 frozen validation/fresh blocks。报告：

- exact FER/false accept；
- 总公开 leakage（含认证/验证相关消息）；
- 交互轮次、延迟与吞吐；
- 净 key-rate。

它不是 NB-LDPC 的失败兜底叙事，而是系统级参考线。若其净 key-rate 已显著领先，
NB-LDPC 后继必须说明预期收益来自更低 leakage、更少交互或更高吞吐中的哪一项。

## 9. 12 个月节奏

| 时间 | 主任务 | 交付/停止点 |
|---|---|---|
| M0 | V33 IR1、冻结实现 | 已完成：`5b8cfef3` ACCEPT |
| M0--M1 | 一次 V33 execute + ER1 | 已完成：30/30 PASS，ER1 ACCEPT；无自动 successor |
| M1--M2 | 条件式 matched finite-control 或 R2 P0 | 一次归因结论或候选系综短名单 |
| M2--M4 | protograph/MET 或 allocation/factorization ensemble gate | 最多 1--2 个 finite 候选 |
| M4--M6 | 单一 finite lifting gate；R3 P0；R4 基线 | 关闭失败族，保留一个主候选 |
| M6--M9 | frozen validation 与 source transfer | 真实泛化证据，不调 confirmation |
| M9--M12 | fresh acquisition qualification（若数据到位） | qualified candidate 或诚实负结果 |

每轮复核四个问题：

1. 当前实验是否仍是区分主要假设的最便宜方法？
2. 数据分布、source/delay 和 train/holdout 边界是否匹配？
3. 新证据是在 ensemble、finite graph、decoder、真实数据还是 qualification 哪一层？
4. 若失败，下一步是否结构性不同，还是在重复微调已失败的机制？

## 10. 文献交叉依据

- [Gorgoglione, Savin & Declercq, Monte-Carlo density evolution for nonbinary LDPC](https://arxiv.org/abs/1004.5216)：支持 MC-DE，但不支持从 ensemble 外推有限图。
- [Bennatan & Burshtein, NB-LDPC over arbitrary discrete-memoryless channels](https://arxiv.org/abs/cs/0511040)：支持经验非对称信道建模。
- [Wang, Kulkarni & Poor, density evolution for asymmetric channels](https://arxiv.org/abs/cs/0509014)：反对 all-zero/symmetric shortcut。
- [Amraoui et al., finite-length scaling](https://doi.org/10.1109/TIT.2008.2009580)：解释 DE 与短块 block error 的系统差距。
- [Pradhan et al., large-girth protograph construction](https://arxiv.org/abs/1301.6301)：提示 degree-2 链风险和 protograph/MET 方向。
- [Müller et al., HD-QKD NB-LDPC](https://arxiv.org/abs/2305.08631) 与 [HD-QKD IR comparison](https://doi.org/10.1007/s11128-024-04395-w)：证明方向有潜力，但其 QSC/q=8/长块结果不能外推到本项目。
- [Mitra et al., informed NB-MLC/JRDO/IDC](https://doi.org/10.1007/s11128-024-04343-8)：支持按经验 ET-QKD 信道联合优化 mapping、rate、degree distribution。
- [Tarable et al., rateless protograph LDPC for QKD](https://tqe.ieee.org/2024/02/02/rateless-protograph-ldpc-codes-for-quantum-key-distribution/)：支持 rate-adaptive protograph 备选。
- [Bravo-Santos, q-ary polar source/channel coding](https://arxiv.org/abs/1511.03881)：支持 NB-Polar P0，不证明 GF(1024) finite 实现。
- [Martinez-Mateo & Elkouss, multiplicatively repeated NB-LDPC](https://doi.org/10.1140/epjqt/s40507-025-00376-9)：支持短块/变化信道的母码思路，但主要证据来自 CV-QKD 低率区。
- [Tauz et al., Block-MDS QC-LDPC for HD-QKD](https://doi.org/10.1109/ITW61385.2024.10806945)：提供结构化 QC 候选和 IR/PA 联合判据；其模拟信道、码长与判定口径不能直接外推到本项目。
- [Hyla & Sułek, short-blocklength nonbinary Raptor-like LDPC](https://doi.org/10.1109/ACCESS.2024.3517171)：支持短块 incremental-redundancy 母码候选，但其 GF(4/8/16) 与反馈语义不同。
- [Jia et al., MGC-LDPC for CV-QKD](https://doi.org/10.1007/s11128-024-04623-3) 与 [Fu et al., rate-adaptive CV-QKD reconciliation](https://doi.org/10.3390/e28010010)：支持把 FER、可靠度和净 key-rate 纳入后继设计，不支持跳过当前离散 empirical-P gate。
- [Müller et al., industrial Cascade/LDPC comparison](https://doi.org/10.1049/qtc2.70003)：支持保留 R4 系统级基线及 verification/leakage 成本，但其 binary/BSC 长帧结果不是 GF32 证据。

2026-08-24 增量检索未发现同时覆盖三源 empirical-P、GF32+GF32、n=1024、
V31 精确层率与 true-predecessor 条件语义的研究，因此不改变 V33-first 顺序。

## 11. 当前授权边界

当前允许：V33 closeout、只读复核、状态文档更新，以及为一次 corrected matched
empirical-P finite-control 创建新的 OpenSpec proposal。V33 PASS 不构成该控制的
实现或执行授权。

当前不允许：V33 rerun、decoder、finite-control、NB-Polar 实现、真实数据流水线、
longrun/minrerun、qualification、promotion、push、删除或覆盖旧 outputs。

本路线图取代 2026-08-23 文档中“V33 尚待 freeze”的陈旧当前状态，但不改写其
历史审计内容。
