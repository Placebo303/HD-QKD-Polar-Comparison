# Session 续接：MSD 到 M 限定接受，下一步分组、协议及功效/成本

日期：2026-10-05（Asia/Shanghai）。本文件是 documentation-only 状态导航，
不替代唯一 `docs/REBOOT_HANDOFF_20261004.md`，不新增科学执行授权。
旧 `SESSION_HANDOFF_20261005_MSD_P2.md` 保留为早期检查点；其“下一步长块构造”
及 HEAD 快照已经过时。恢复时以现场状态和当前单日志为准。

## 1. 现场与必读入口

写本文前现场核对：仓库 `D:\Code\HD-QKD_Polar_Comparison`，分支
`formal-ir-v72p1-addendum-clean`，HEAD
`ac78df61da83dc3ed7a6a36e86719749e6c7fdf9`，`git status --short` 无输出。
这是交接前快照，本文提交后 HEAD 会变化；每步开始必须重测。

```powershell
Set-Location D:\Code\HD-QKD_Polar_Comparison
git branch --show-current
git rev-parse HEAD
git status --short
```

按顺序完整阅读：

1. `AGENTS.md`、`docs/REBOOT_HANDOFF_20261004.md`、`docs/NOW.md`。
2. `AGENT_PROJECT_MEMORY.md`。
3. `openspec/changes/msd-real-calibrated-mainline/{proposal.md,design.md,tasks.md}`。
4. `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/P2_IMPLEMENTATION_CONTRACT.md`
   与同目录 `EXPLORATION_LOG.md`（唯一 MSD 日志，特别是末尾 M 收尾）。
5. P1 `RESULT.md`、`P1_NUMBERS.json`；J 的 `ERROR_ALLOCATION_TABLE.md`；
   M 的 `M_ROLE_METADATA.json`、`M_ROLE_METADATA_REVIEW.json`。

本项目关闭 Ponytail，委派使用 subagent。主线程拥有需求、科学判断、
路线选择和接受；实现者不自授接受或运行授权。不要复活旧小探针或重做 S1–S8。

## 2. 已接受的里程碑与证据上限

以下研究提交均在本地；本轮未 push，未重新查询远端。S1–S8 的旧 push
授权已执行完，不覆盖后续提交。整理最终提交为 `8f2f313a`，整理详情见
`openspec/changes/archive/2026-10-04-reboot-repository-organization-20261004-completed/archive.md`。

| 提交 | 完成范围 | 仍未接受 |
|---|---|---|
| `da140c10` | P1：已有 R1 TRAIN 条件熵、预算及旧比较设计功效算术，独立复算 | 实用码隙、实际 f/FER、样本可用性 |
| `7aa4283f` | P3：NB-LDPC 精确 check-transform 复用候选 | 完整译码器等价、接入默认路径、加速 |
| `6e9abc28` / `a18ed9c5` | P2：条件软先验及 truth-free syndrome/prefix 接口 | 生产 backend、性能 |
| `c7db4f44` | C：CSR H=[A\|T] sparse accumulator 结构候选 | 近容量码、实用逐层分配 |
| `bf30544f` | D：默认关闭的整层精确零误差先验旁路 | OOS 确定性、BP 等价或速度收益 |
| `7a8f21ea` | E：默认关闭的部分精确变量条件化 | 同上；仅标准 prior builder 的模型范围 |
| `322df22e` | I：完整字母表/长块固定代数连接测试 | 信道实验或解码性能 |
| `98fc3713` | J/K：TRAIN 摘要下正态分配及尾分位数接口修正 | 实用整数最优、真实码率或 f 增益 |
| `4bf97353` | L：独立 sender reference、native outcome/加权良率账本 | 实际 tag 协议、安全性、实测 FER/f |
| `c4400827` | M 准备范围冻结 | 单凭提案不授数据读取 |
| `ac78df61` | M：限定历史元数据字段独立核对、历史角色使用记录 | 当前独立配对组数、未用子集、解码成本 |

中间准备及旧交接提交见 `git log`，不把它们当额外实验。
没有执行本轮生产 decoder/backend 构造、DE、新真实帧/raw 读取、资格化或发表；
P4 同采集 Polar 对照未启动。未测得实用效率提升，不能把规划表写成性能结果。

## 3. 当前设计与未闭合条件

唯一 MSD change 为 `msd-real-calibrated-mainline`。源文件在
`comparison_bench/src/comparison_bench/formal_ir/`：
`msd_information_budget.py`、`msd_conditional_prior.py`、`msd_syndrome.py`、
`msd_sparse_code.py`、`msd_error_allocation.py`、`msd_outcome_accounting.py`。

P1 输入是已接受的 R1 TRAIN COO counts：
`workspace/r1_histogram_5e2a91c4/T2-{1M,1.5M,2M}_N_ab_train_sparse.npz`；
Alice 行、Bob 列，自然字母表。CQ 原根只有摘要，不能重建全量联合计数。
这个输入指针不授新的 NPZ/raw/帧读取或新实验。

当前比较建议仍是同一自然 LSB-first MSD 家族，native N=1024 与 N=16384：
共同体量上一长块与十六个连续短块配对。短块逐个验证/保留，长块整体验证/保留；
native tag 和部分保留必须显式计费。这是规划，不是 decoder packet，
没有冻结实用每层码率/degree、实际 tag 协议、配对库存或运行预算。
旧 O1 是 synthetic genie-u1 单层 ceiling，不能当完整符号实测 comparator。

对每个 native block，单位与账本为：

```text
H_A_total = N * H(A)                    # bits/block
kept = H_A_total - L_EC                 # bits/block
Y = kept - tag - kept * failure         # bits/block
f = (L_EC + tag + kept*failure)/(N*H(A|B))  # dimensionless
```

H(A)、H(A|B) 为 bits/symbol；只对 verified_exact 取 failure=0。
accepted_wrong 单列且 failure=1，不得冒充 verified yield；实际 EC 行和 tag 均计费。
按块求和失败惩罚，不能用平均 kept × 平均 failure。
kept<0 为无效良率、分母=0 不给有限 f；两臂共同符号体量和熵分母匹配。
tag callback/序列化由调用方决定，目前没有接受实际验证协议。

`P2_POWER.json` 与其独立复算只适用于旧同 native 长度/共享 tag 的比较假设。
不得复制其样本数作为新短/长比较的功效证明。目标 delta_f=0.10、
alpha=0.05、power=0.80 是原规划参数，不是观测收益，也不可放大目标凑小样本。
共同体量 paired-gap 区间/方差界的独立代数审查已接受，公式在 design.md；
尚无新协议下实际数值功效、独立采集组数或 measured decoder cost。

## 4. M 实际读取、失败留存与数据角色

人类针对四文件 metadata-only 请求回复“可以继续”；该次限定工作已完成。
内容 allowlist 为 R1 workspace 根的 `PRE_EXECUTE.md`、`R1_RESULT.md`、
`telemetry.json`、`split_manifest.json`。禁止 follow references、frame-index
数组枚举、raw/NPZ/帧向量、backend/DE/RNG。不把已完成授权当未来读取 grant。

M 的逐项数值已在两个紧凑 JSON 中保留，不在本文复制历史值：
九个 split_*_frames 字段及四个处理时长，独立 exact 核对共13项、零差异。
计数的原始 unit=unknown 保留；历史 acquisition-frame 字段不能换算成独立
reconciliation group。时长为历史 R1 processing seconds，不能作为 MSD 成本。
Markdown/alignment/range 未匹配字段为 UNKNOWN，而非不存在。

必须留存、不得重做或“补造成功”的根：

- `workspace/msd_role_inventory/08c3f9eb36304012875d5413149f47f6/`：首次 exit0
  但选中字段全空，主线程判 EXTRACTION_INCOMPLETE，原 script/inventory/log 保留。
- `workspace/msd_role_inventory/e6acfa42601c466d86f0b4e163772eb6/`：主线程明确
  裁决一次 scope-preserving correction，重新 Pre-EXECUTE 后119s上限运行、exit0。
  只接受其已核对字段，没有后续 M rerun 授权。
- `workspace/msd_role_inventory_independent/ecef9371bdae4a1c80c089c993861b61/`：
  独立 stdlib direct-key 核对。第一次脚本打印 PASS，但 shell wrapper 的空 rc
  导致 exit1，终端报 `bash: line 1: exit: : numeric argument required`；
  attempt_01.log 仅保留 PASS/空 EXIT，未捕获错误文本。第二次改 PowerShell
  LASTEXITCODE 捕获，exit0/attempt_02.log；未再运行主清单。
  最终 verification.json 属第二次核对，首次 wrapper 失败仍保留。

**角色的新事实**：闭合的 M0/M2 文档记载从 R1 VAL/HOLD 池取输入评估，
M3C 有追加诊断暴露。M2 科学接受 WITHHELD 不恢复数据的未使用状态。
主线程将该池按既有开发/回放输入处理，除非明确证明某个 untouched subset。
不能称整个池是新鲜 OOS，也不能反向声称每个可能索引均已暴露。
具体暴露索引、未用子集、session 边界、完整符号组数仍 UNKNOWN。
来源原文指针在 M 单日志；不要把其历史性能数字重新接受。

早期 prior/syndrome 的原 stdout 缺失与 replay 限制仍见旧交接及单日志，
不能把 replay 改称首次捕获。E/J/L 的失败与唯一修正也在单日志；J 旧产物
保留 PRE-K 来源，没有用 K 修正重跑 J。I/J/K/L 已接受，不机械重复测试或计算。

## 5. 下一 session 的具体推进顺序

1. 重测现场，读上述权威和当前 tasks/log。从尚未完成的角色/分组及共同体量
   功效/成本条件继续；不要重新实现 C、重跑 I/J/L/M 或重开已裁决路线。
2. 主线程先给最小的可审阅后继 scope：完整 Alice/Bob 体量、native tag/partial
   retention、boundary-preserving 分组、既有开发池与潜在 fresh OOS 的区别。
   优先在已有文档/接受的算术范围内做文本与数学规划；缺失数据不靠小 pilot 推断。
3. 在同一 change/单日志中冻结新功效口径、每个必要数值的脚本及独立复算。
   实际协议/数据不足处保留 UNKNOWN；先解析目标效应，才写 decoder packet。
4. 若下一步必须读取索引/帧/raw 或做 backend timing，先完成精确文件/字段、
   命令、输入角色、输出根、成本和 STOP 条件，再向用户请求那个具体授权。
   此交接及历史四文件 grant 均不授权这些动作。真实帧 D-3 预算尚待用户决定。
5. 未来 decoder 方案还需冻结实用图/rate/degree、功效足够的独立配对数、
   模型校准/数据角色、泄漏/tag/失败/accepted-wrong 口径、实际成本与 DECIDE gates。
   功效不足不运行；不得 GF32 小探针、小 pilot 或随机游走。

推荐收益：用正确样本角色及 native 成本评估真实效率，避免虚假的留出和
tag/保留差异造成的假增益；实用 f 改善仍未知。当前成本仅文本/数学规划，
新数据与 decoder 工作成本须另外落实，不能用 R1 processing 秒数估计。

P3 继续保持独立 change `nbldpc-mainline-enabling` 及其单日志，helper 未接入；
任何接入需完整译码等价/独立审查与授权成本，不因 MSD 检查点自动启用。

## 6. 强制运行与权限边界

用户已授权 P1→P2/P3→P4 分阶段持续推进，例行实现/准备不重问；具体
科学执行、数据读取、功效、预算和接受门仍适用。主线程不能推卸科学判断。

- 禁 decoder/DE/new real frame/raw/资格化/发表的隐式执行；未授权生产 backend。
- 冻结 src/、experiments/、tools/、results/ 及旧 production outputs；不删除，
  不改历史正文、不 merge 姊妹线，Release 只读。scoped commit，禁 git add -A。
- 新 push 及隔离区处置需用户另行决定；PATH_MAP/QUARANTINE_MANIFEST 在 docs/archive/。
- 仓库 POSIX `.venv` 经 WSL；固定 fake focused tests 才可运行，避免 broad pytest
  隐式 production。新 workspace/<task>/<uuid>，pytest -p no:cacheprovider -o addopts=，
  首次 stdout/stderr 落盘；无改动不机械复跑。长运行先≤2min计时、逐块落盘。
- 必须满足 reboot R1–R9：MDE、真实联合校准、独立数字、单 change/log、
  scoped提交；KILL 前理论/姊妹对照，不以次优候选失败关闭路线。
- 用户已手动重置并取消一切自动换卡。禁止 use_earliest_reset.ps1、
  run_0630_reset.ps1、consume API、购买/换卡或重新启用卡任务。
  Windows 卡任务之前已核对 Disabled；本次未重测服务或卡状态。
  旧 automation 时间均为历史记录，不能据此恢复卡操作或后台研究运行。

## 7. 给下一 session 的可粘贴提示词

```text
接手 D:\Code\HD-QKD_Polar_Comparison，先完整读 AGENTS.md、
docs/REBOOT_HANDOFF_20261004.md（唯一 reboot 权威）、docs/NOW.md、
AGENT_PROJECT_MEMORY.md、docs/SESSION_HANDOFF_20261005_MSD_M_ACCEPTED.md，
再读 MSD 同一 change/tasks/design/P2_IMPLEMENTATION_CONTRACT 和唯一单日志。
现场重测分支/HEAD/status。Ponytail 关闭，委派使用 subagent。

S1–S8 及 MSD C/D/E/I/J/K/L、M 限定元数据接受已完成，勿重做。
最新科学检查点 ac78df61；交接 docs commit 后 HEAD 会变化。
这些仅数学/结构/fake/元数据证据，尚无生产 decoder 或实际 f/FER 接受。
R1 VAL/HOLD 池有 M0/M2/M3C 后续使用记录，按既有开发/回放处理；
精确暴露范围/未用子集/独立完整符号配对组数 UNKNOWN，不称全池 fresh OOS。
历史帧计数不是组数，R1处理秒数不是 decoder cost。

沿同 change/单日志补齐分组、实际 native tag/部分保留及共同体量功效/成本。
旧 P2_POWER 的同长度/共享 tag 假设不证明新短长比较的功效；
先做可审阅文本/数学 scope，必要数据/索引/帧读取及 timing 先冻结精确范围
再获具体授权。真实帧 D-3 预算仍未批准。主线程选路线并独立复算数字，
不得小 decoder pilot/GF32 微探针绕过 MDE，不捏造运行成本或性能增益。

用户允许分阶段推进，不反复问已批准例行准备；本交接不新增 decoder、DE、
raw/真实帧、资格化、发表、push、删除授权。冻结根不碰，scoped commit。
用户已取消所有自动换卡：禁 helper/consume/购买/换卡/重新启用卡任务。
从当前未完成项继续，先给具体下一步，再完成授权范围；保留失败和证据上限，
每个里程碑给推荐下一步、预期收益和成本。
```
