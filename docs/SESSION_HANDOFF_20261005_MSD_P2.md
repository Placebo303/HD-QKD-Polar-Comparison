# Session 交接：P1 已接受，P2 接口已接受，下一步长块构造

日期：2026-10-05（Asia/Shanghai）。类别：documentation-only。
本文是当前状态及后继任务导航，不替代唯一 reboot 交接权威
`docs/REBOOT_HANDOFF_20261004.md`，不新增科学执行、push 或删除授权。

交接正文已由独立 Luna 做限定只读核对：当前提交/分支、路线合同及任务状态、
功效字段、失败回放与最终 pytest 路径来源一致；无新的科学执行授权。
记忆分诊结论：NOW 链接本日期导航即可，不把短期 SHA/快照重复写入长期记忆。

## 1. 开工前与现场状态

完整阅读 `AGENTS.md`、`docs/REBOOT_HANDOFF_20261004.md`、`docs/NOW.md`，
再读 `AGENT_PROJECT_MEMORY.md` 和本文引用的当前路线 change/合同/日志。
不要按旧交接中的 worktree 数字操作；每个里程碑开始前现场重测。

本次写交接前测得：

- 仓库：`D:\Code\HD-QKD_Polar_Comparison`。
- 分支：`formal-ir-v72p1-addendum-clean`。
- 实现 HEAD：`a18ed9c530833ce7827718b895d3d0969984a5d5`。
- 写交接前 `git status --short` 无输出。
- 本地 origin 跟踪引用仍为 `8f2f313a244179e30f74c5c1125210603d509c16`；
  这次只检查了本地引用，未重新查询远端。此前 S1–S8 普通 push 的现场核对已记录。
- 后面的研究实现提交尚未 push；即使提交本交接文档，也不含 push 授权。

```powershell
Set-Location D:\Code\HD-QKD_Polar_Comparison
git branch --show-current
git rev-parse HEAD
git status --short
```

Ponytail 已为本项目关闭，不能按全局默认重新启用。委派只用 `luna_worker`，
除非用户/规则明确要求另一个命名角色。主线程负责完整任务冻结、科学判断和接受，
不能让实现者自授科学接受。新 session 不应恢复旧 S7 移动任务或旧探针任务。

## 2. 已完成与提交

S1–S8 整理已完成并已 push，不重做。提交、归档处置及 smoke 证据在
`openspec/changes/archive/2026-10-04-reboot-repository-organization-20261004-completed/archive.md`。
路径映射：`docs/archive/PATH_MAP.md`；未跟踪杂项保留待用户决定：
`docs/archive/QUARANTINE_MANIFEST.md` 与 `workspace/_quarantine_20261004/`。
历史项的第四处置只是目前不推进，有逐项原因，不是永久放弃或科学 KILL。

整理后实现提交如下，均为限定范围接受：

| 提交 | 已完成范围 | 尚未证明 |
|---|---|---|
| `da140c1013088860b5e6325498832d13d3198a15` | P1 条件熵、信息密度方差、含 tag/失败惩罚的预算；独立复算；解码写包前功效算术 | 实用码隙、OOS FER、实际 f 改善 |
| `7aa4283f8db15b5bf7bebe12e76ffb01b199ef20` | P3 check-node 复用数学候选，保持参考浮点运算顺序；固定数组逐位一致测试 | 完整译码器等价、实际加速；未接入默认路径 |
| `6e9abc28a5a4a41a0ddf0ae9561cc1938629c463` | P2 条件先验/软错误概率模型；无 Alice 真值的查询接口 | 解码性能、前缀错误传播 FER |
| `a18ed9c530833ce7827718b895d3d0969984a5d5` | P2 sender/public syndrome/receiver 衔接；假解码数学测试与独立只读审查 | 生产 backend 行为、长块码图、任何解码性能 |

## 3. MSD 路线：当前科学与工程状态

唯一当前 change：`openspec/changes/msd-real-calibrated-mainline/`。
唯一路线日志：`docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/EXPLORATION_LOG.md`。
不要为每个构造/测试另开路线 change 或千行样板。

### P1 已接受的范围

先读同目录 `PREREG_AND_AUTH.md`、`RESULT.md`、`P1_TABLE.md`、`P1_NUMBERS.json`。
CQ 原根只有摘要，无法恢复完整联合计数；没有假装重建 CQ 或 VAL/HOLD。
使用的是已有、已接受的 R1 TRAIN COO 联合直方图，以下为唯一冻结输入：

```text
workspace/r1_histogram_5e2a91c4/T2-1M_N_ab_train_sparse.npz
workspace/r1_histogram_5e2a91c4/T2-1.5M_N_ab_train_sparse.npz
workspace/r1_histogram_5e2a91c4/T2-2M_N_ab_train_sparse.npz
```

行是自然 Alice bin、列是自然 Bob bin；字段 row/col/count/shape/N_train。
TRAIN 不能改名为验证/holdout；不能借这次授权重读 raw 或生成新直方图。
P1 的自然/Gray 完整双射对照不意味着 P2 接收接口可把 Bob bin 静默换轴：
P2 model 查询始终保留完整自然 Bob 符号，只有 Alice 的 bit label 使用指定编码。

P1 推荐继续自然编码 LSB-first 长块原型，短块保留为后续配对对照。
拟议比较块长是 N=1024 与 N=16384 个符号/block，不是 GF32 128 符号小探针。
这是 TRAIN 插件熵与显式正态近似假设下的设计推荐，不能写成实际 f 优势。
零 TRAIN 条件熵不支持 OOS 零误差，也不是部署时零校验行的许可证。
单个短块预算已很薄，不能把全部短块路线概括为超预算或已关闭。

账本必须显式包含单位（熵 bits/symbol，其余预算 bits/block，f 无量纲）：

```text
H_A_bits = N * H(A)
kept_bits = H_A_bits - L_EC_bits
Y_bits = kept_bits - tag_bits - kept_bits * p_fail
f_expected = (L_EC_bits + tag_bits + kept_bits*p_fail) / (N*H(A|B))
```

P1 tag/failure 是假设，不是测得 FER；历史短块披露密度外推不是观测长块基线。
后续实际披露/失败角色发生变化须重审公式和功效界，不能只把旧 f 数字拿来比较。

### 解码写包前的功效已算，但执行条件未齐

读 `power_before_decoder.py`、`P2_POWER.json`、`verify_power_independent.py`、
`P2_POWER_INDEPENDENT.json`。目前 delta_f 是拟议目标，配对失败/discordance 方差未知；
normal 规划与 Hoeffding 充分界都显式保留，不能改成乐观方差来凑小样本。
当前文件的拟议效应为 delta_f=0.10，显著性 alpha=0.05、power=0.80；
这些是规划目标，不是已测得增益，不能临时放大目标效应以缩小所需样本。
这些文件给出所需配对数，不证明现实中有这么多独立帧或能承受其运行成本。
直方图标定的 iid 合成抽样也只证明模型范围，不产生新的真实 OOS 采集证据。
尚无 decoder 实验包、没有已冻结的 graph/rate/paired sample/runtime 方案。

### P2 已实现接口

- `comparison_bench/src/comparison_bench/formal_ir/msd_conditional_prior.py`：
  完整 Bob 与实际前缀条件化；无支持组合返回 p_one=0.5 并标 flag；
  支持确定性概率保持精确值；MAP base 固定 tie=0，p_error=min(p_one,1-p_one)。
- `comparison_bench/src/comparison_bench/formal_ir/msd_syndrome.py`：
  Alice 真值仅 sender 接受；receiver 只接收 Bob、公有 syndromes、调用方 CSR 矩阵、
  强制显式 decoder factory。delta=s XOR H*base；恢复 base XOR error；
  后续层只用实际恢复前缀。失败 syndrome 早停；满足 syndrome 不等于验签/正确译码。
- 所有提前发送的 syndrome 行均计为 transmitted disclosure bits/block，含依赖/零行，
  不用 rank 折扣，也不隐含加 tag。后续安全/期望良率口径仍需显式账本。
- `make_bp_decoder` 是 lazy、显式选择的 factory，必须提前绑定正数 max_iter；
  它从未构造或执行生产解码器。receiver 无默认 backend，也无 Alice oracle。

合同：`P2_IMPLEMENTATION_CONTRACT.md`（M1–M9）；任务状态见当前 change/tasks.md。
不能把 factory 的 API 静态核对写成 backend 数值接受。

## 4. P3 独立并行路线

Change：`openspec/changes/nbldpc-mainline-enabling/`。
合同/单日志：`docs/research_cycles/NBLDPC-MAINLINE-ENABLING/`。
`nonbinary_v10_fftqspa.py::check_update_all_log` 只是未接入的数学候选，
参考 `check_update_log` 及 decoder 默认调用未改。禁止直接激活后声称加速。
下一次接入前冻结完整 messages/beliefs/decisions/status/iterations/transcript 等价门槛，
并在真实标定模型、主线块长与功效/成本范围内准备测量。
soft-prior rescue/增量披露仍未重新冻结或执行；旧 GF32 小探针授权不能复用。

## 5. 测试、环境与失败留存

使用仓库 POSIX `.venv`，通过 WSL 调用；不要用 Windows/system Python。
`ldpc==2.4.1` 已在该 .venv 安装，记录在 MSD 单日志；依赖报告/缓存位于
`workspace/msd_backend/252cb3546d4f4840bd16e703a1a63788/`。
导入和本地签名检查成功，不表示实际 constructor/decode 已运行。

此前接受的 focused tests：P1 数学、P2 prior、P2 syndrome fake 与 P3 helper exact。
精确命令、结果/UUID 见两条路线日志，避免无新改动机械重复。
只跑与新改动相关的测试；旧测试可能默认调用生产解码，不要整仓 pytest。
新测试先确认明确 fake runner，再用新的 workspace/<task>/<uuid> 和 120 秒上限：

```powershell
# 将 TASK_UUID 换为本次新值，不复用下方已有日志中的 UUID。
wsl --cd /mnt/d/Code/HD-QKD_Polar_Comparison --exec timeout 120 .venv/bin/python -m pytest -p no:cacheprovider -o addopts= --basetemp workspace/TASK/TASK_UUID comparison_bench/tests/NEW_FOCUSED_TEST.py
```

具体留存限制必须如实继承：

- prior 首轮断言反向的失败及最初 UUID 无法恢复限制，在 `P2_PRIOR_FAILED_ATTEMPT.txt`；
  不补造路径。其原样 pytest 文本有 whitespace-check 例外，见日志；不要说全检查通过。
- syndrome 首轮失败原 stdout 仅在原工具输出；后来恢复错误 fixtures 的确定性回放在
  `workspace/msd_syndrome/a4be7f2d-65f6-47e0-a51c-2dabb7a3c253/attempt_01.log`，
  文件明确标 replay，不能当成原始捕获。纠正后最终测试再运行，之后代码/测试未改。
- 最终 fake pytest 指定了 UUID，但因无 tmp fixture，pytest 未创建 basetemp 目录；
  它是命令参数，不是已落盘证据根。
- 现有 pytest.ini cache_dir warning、WSL localhost/NAT 提示不应改造成算法失败。

## 6. 后继下一步（主线程应作科学选择）

优先完成 P2 长块码构造，不回到小探针，也不从包装/审计文档重新开始。

1. 在同一 MSD change 中，冻结适合自然 LSB-first 的长块 sparse 构造、逐层分配及
   短块 comparator。仓库目前没有可直接复用的目标长块稀疏二元图。
   `codebook_long_v3.py` 是短块 dense candidate，带 identity-column 结构与固定前缀比例；
   不能仅放大长度就称为近容量构造。不要使用已知次优失败关闭路线。
2. main 给 Luna 一次冻结完整文件 ownership、数学/结构验收、fake 测试、禁止动作及
   两种返回条件；实现最小的科学正确构造/接入准备。实现者不能替 main 选科学阈值。
3. 写任何 decoder 实验包之前，沿用/重审真实效率目标与独立功效算术，明确
   模型/design/OOS 角色、独立配对样本、图/种子覆盖、实际披露/tag/失败/undetected、
   输出根、成本预算。样本不能解析目标就不跑；禁止小 decoder pilot 绕过该门槛。
4. 有完整且已授权的执行方案后，长运行先 ≤2 min timing smoke，按块成本估算并留裕量，
   长批逐块落盘。保留失败，不擅自换科学输入、目标效应或门槛。
5. 实帧仍是 DECIDE；先完成具体可审阅方案，再取得用户 D-3 真实帧授权/墙钟预算，
   按 Pre-EXECUTE/独立 Pre-RESULT/main 接受执行。P4 同数据 Polar 对照也未启动。

推荐收益：保留独立硬判 bit-plane 丢掉的全 Bob/前缀信息，并降低有限块开销；
实际 f 改善未知。成本：新增科学合理的 sparse 图与逐层分配，以及尚未测得的较大
功效足够配对 workload；不能捏造 decoder 时间估计或让用户替 main 决定算法路线。

## 7. 不得跨越的边界

用户已授权按 P1→P2/P3→P4 分阶段持续推进，例行准备/实现不应反复重问。
已裁决期望良率 f、GF32 小探针停止、归档第四处置，不重开这些问题。
但阶段授权不代替缺失的具体执行合同、功效、成本或用户-only DECIDE 门槛。

必须遵守 reboot R1–R9 全文，尤其禁止 GF32 128符号/6固定图/192帧及同类小样本游走；
任何合成实验只能真实直方图标定；实验首句说明如何改善真实数据效率；
每个科学数字由脚本和独立复算支持；KILL 前核对理论与只读 Release；
结论只写测得范围，不写全称否定。尚未有新生产解码、DE、raw/真实帧读取、资格化或发表。

不碰冻结 `src/`、`experiments/`、`tools/`、`results/` 和已有 production outputs；
不覆写证据，不删除文件，不改历史正文，不合并姊妹 Polar 线。
里程碑 scoped 提交，禁 git add -A；push 须用户另行批准。
隔离区逐项处置、D-3 和新 push 仍待用户决定，不能用旧 push 授权覆盖后续提交。

## 8. 可直接粘贴给后继 session 的提示词

```text
接手 D:\Code\HD-QKD_Polar_Comparison。请完整阅读 AGENTS.md、
docs/REBOOT_HANDOFF_20261004.md（唯一 reboot 权威）、docs/NOW.md、
AGENT_PROJECT_MEMORY.md、docs/SESSION_HANDOFF_20261005_MSD_P2.md，
再现场重测分支、HEAD、git status，不能信旧快照。

本项目关闭 Ponytail，委派只用 luna_worker；主线程负责完整任务冻结、
科学选择及接受。S1–S8 已完成，不重做、不恢复旧 S7 或 GF32 小探针。
P1 算术/独立复算已接受，P2 prior 与 syndrome 接口只通过数学/fake 测试；
P3 exact helper 未接入默认；未执行生产 decoder、DE、真实帧或资格化。

从 openspec/changes/msd-real-calibrated-mainline/tasks.md 下一项继续：
优先冻结科学合理的长块 sparse 构造和逐层分配，保留短块配对对照，
同一 change/单日志推进；不要直接放大旧 dense toy graph 或把零 TRAIN 熵
当成 OOS 零披露。任何 decoder 实验包前先审已有 P2_POWER 与独立复算，
再落实真实标定模型、样本角色、功效足够配对数和成本；看不见目标就不跑。
不要以小 decoder pilot 绕过 MDE。真实帧运行须具体 D-3 授权/墙钟预算及
DECIDE 完整 gates；P4 同数据 Polar 对照仍未启动。

用户允许按 P1→P2/P3→P4 分阶段持续推进，不反复询问已授权例行实现。
本提示不新增 decoder 实验、DE、raw、资格化、发表、push、删除授权。
严格遵守 R1–R9、冻结目录、fresh UUID/.venv/fake-only focused tests、
独立复算、失败留存和 scoped commit。先给具体下一步，再实际完成允许范围，
每个里程碑交代测得范围、推荐下一步、预期收益与成本。
```
