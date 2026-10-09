# C-3 M 波执行日志（单一 append-only，OP-M2 唯一写者）

> Track：EXPLORE（合成校准信道；B=300/格；块级落盘 + 汇总）.
> 冻结包 `C3_MPACKET.md` 全文逐字遵守；背景 `C_BATCH_AMEND.md`.
> OP-M2 写作用域：A3/A4 循环 + A6 桥 + 汇总；OP-M1 经回执由主线程 append（标记来源）.

## 2026-10-08 20:47:56+0800 OP-M2 启动（实现完成，测试 13 passed，桥门通过，分片执行开始）
- 写作用域：新建 msd_c3m_driver.py + test_c3m_driver.py；机器根 workspace/c3_mtune/mt_20261008（fresh-root；OP-M1 用 mt_a1a2_ 前缀错开）；本日志唯一写者 OP-M2。
- 冻结：A3 QSPA max_iter=300 单值；A4 SC(list1)+SCL8(list8)；kept=N·H_A_op（F1→10,F2→9,F3→11，驱动传入 net_of_cell）；TAG=64；ROW_KEYS+hash；B=300；种子 20261009；无 per-block 超时（T_dec p50/p95/max 单列，overtime 只调度标记）。
- 码率规则只读引用 bakeoff（compute_rate/GAP_NB/M_LADDER/ANCHOR_N 别名恒等，无自有 R 公式）；网格 A3/A4：F1/F2×6N＋F3×{1024,4096} exploratory；A6：F1/F2×{1024,4096,16384}。
- A6 桥：T0 ok（field q=32 钉定 c3a3660a…；叠矩阵 m_total=208，lec=1040；无噪声探针 max_iter=100 通过）；T1 ok（F1 p̂=0.060264/pm̂=0.036475，F2 p̂=0.030055/pm̂=0.018369，n=307200）。
- 探针测速（F1 N=1024）：A4-SC 0.03s/块；A4-SCL8 0.2s/块；A3 18s/块；A6 120s/块（1/1 fail，FFT-QSPA 30iter）。执行分片见下一条。

## 2026-10-08 20:48:17+0800 OP-M2 分片执行启动（4 后台任务）
- 分片（同根 append-only，块文件互不相交；--no-tables，终点 --recount 统一重建，不存在 manifest 竞写）：
- Shard A（job pwsh-682）：--full --cells F1/A4,F2/A4,F3/A4（SC+SCL8 全网格，默认格预算 1800s）。
- Shard B1（job pwsh-683）：--full --cells F1/A3/1024,F2/A3/1024 --cell-budget-s 20000（两格 B=300 真实跑，约 1.5h/格）。
- Shard B2（job pwsh-684）：其余 A3 格（2048/4096 探针后调度标记；8192/16384/32768 内存墙预检即标；F3 两格 exploratory；锚点归属本分片）。
- Shard C（job pwsh-685）：--a6-full（桥已过；逐格 B=1 探针守卫，120s/块外推必超预算，预期 6 格 overtime-risk short）。
- 日志：workspace/c3_mtune/mt_20261008_shard{A,B1,B2,C}.log（git-ignored）。

## 2026-10-08 21:12:00+0800 OP-M2 执行事故 + 续跑（append-only 保留失败尝试）
- 事故：首轮 4 分片全部异常终止（块文件部分、stdout 日志空、wrapper 回 0；真实 rc 被 pwsh \True 布尔 echo 掩盖，已改用 \）。
- 审计：部分块文件连续完好（F2_A3_N1024 246 行 block 0..245；F1_A4-SC_N8192 177 行；F1_A3_N4096 42 行），kept 口径抽查一致；确定性 seed+block 流可续跑。
- 处置：降并发为 2，重发 B1（job pwsh-726）+ A（job pwsh-727，均 --resume）；C/B2 待其一完成后重发。非本任务进程（4 个 21:03 后起 python）一律不动。

## 2026-10-08 21:13:23+0800 OP-M2 预注册修复① + 回归（append-only）
- 修复①（预注册修复额度内；科学输入/种子/阈值/假设不变）：_run_guarded 探针改写独立 throwaway 文件。根因：探针按 B=1 重算 net，续跑部分文件时 n_fail=B−succ 为负 → ValueError → 误标 construction-fail（B1-F2 246 行、A-8192-SC 177 行受影响，行完好）。
- 连带：overtime-risk 不再删除正式文件（保留已落盘行）；正式循环前删探针文件；回归测试 test_t1_probe_resume_partial 通过（14 passed）。
- A 分片（job pwsh-727）继续跑（8192-SC 误标仅内存态、文件 177 行完好，事后定向续跑）；B1 已重发。

## 2026-10-08 22:58:52+0800 OP-M2 中期：B2/C 收敛，A 尾部，预 recount 通过
- B2 rc=0（14 格；F3-A3-4096 173→300 满；F1-A3-4096 止 42/300、F2-A3-2048 止 147/300，探针调度 short 保留）。
- C rc=0（a6_cells 6 格全 overtime-risk short：探针外推 F1-1024 48062s / F1-4096 46808s / F1-16384 50844s / F2-1024 21336s / F2-4096 69944s / F2-16384 230376s，均超格预算 1800s；桥 T0/T1 ok 在先，无降级）。
- A 进行中（F1-SC 整行满；F1-SCL8 1024/2048/4096/8192 满，16384 锚点双 M + 32768 探针无行；F2-SC 行尾 32768 在跑；余 F2-SCL8 + F3 两行）。
- 预 recount 验证通过（48 格 / 明细 42 行 ok20/short3/no-rows19 / 主表 9 行；a6 合并 6 条保留）。抽查：F2-A3-4096 succ292 kept36864 LEC1444；F1-A4-SCL8-4096 succ77 kept40960；F3-A3-1024 succ300 kept11264。
- 修复②：recount 短记录补全表键 + 期望网格补 no-rows + 撕裂尾容忍 + a6 合并（工程实现；科学输入未变；回归 15 passed）。

## 2026-10-08 主线程代记：OP-M1 回执（MLOG 唯一写者为 OP-M2；本节由主线程据回执转录，标记来源）

- 写作用域合规：仅新建 `msd_c3m_a1a2.py` + `test_c3m_a1a2.py`；OP-M2 文件与本日志未碰；
  D:/Data 零访问。测试 18 passed。
- M-A1-01 完成：QC 不规则码冻结（PEG N=8192 构造 >15min 实测下界，保网格遂选 QC；
  T0 F1 13/30、F2 12/30 过 0.30 门，无 repair）；A1 矩阵 F1/F2×6N×B300 14/14 满格
  （F1 succ 108/52/18/1/0/0；F2 104/1/9/0/0/0）；kept=N·H_A_op；L_B=n_marked 理想值；
  M 锚点 6 族全 both-undecided→freeze-M2.5。
- M-A2-01 部分完成：SC 14/14 满格（F1 80/12/3/0/0/0；F2 79/15/2/0/0/0）；
  SCL8 12/14 满格（F1 127/54/19/1/0；F2 118/37/10/1/0）+ N32768 两格 short
  （48/300、4/300，~80–100s/块，会话内不可达，作业在跑，续跑命令已留）；
  F3 二进制 infeasible-by-construction（R<0，有测试）。
- 主线程裁决（回执 (a)(b)）：(a) short 条款类比成立——包 §4 short 机制针对慢格一般情形，
  SCL8-32768（7–10h/格）适用，记 short；(b) F1 小 N 的 R≈0.58 低于 0.65–0.8 目标带
  系冻结 gap 表所致，记录不设门（否则与包 §2 矛盾），模块已注记。
  (c)(d) 备查：大 N 零成功为冻结输入下如实 verdict；回执只报格数不排序不定案。
- 42 格文件＋cells/manifest 落盘（`mt_a1a2_opm1/`）；续跑命令幂等（见回执原文）。

## 2026-10-08 主线程注记：待批末审查事项（M 波执行中问题）
- 修复计数：OP-M2 已用修复①（额度内）+ 修复②（工程实现自称不计）。
  批末审查核定②是否超额度（初步：均为记账/报告层实现，科学输入未变，倾向接受并备案）。
- M 波 A3 覆盖洞：F1-A3/4096 止 42/300、F2-A3/2048 止 147/300（探针调度 short）。
  F1-A3/4096 恰为 mini-OPT 格——M 口径该格缺席时，F1-A3 的 M-OPT 只能在
  {1024,2048} 内定。批末审查决定：接受 short（探针纪律）或要求补跑（mini 行证明该格可完成，
  只是 cap300 下更慢）；在 OP-M2 最终回执后定。

## 2026-10-08 23:52:35+0800 OP-M2 终局 recount + 验收自评（A 收敛）
- A rc=0（cells=32）。终盘 33 块文件；终 recount：manifest 48 格 / 明细 42 行（ok29/short2/no-rows11）/ 主表 9 行；a6 6 条保留。
- A3/A4 网格（B=300，种子 20261009，kept=N·H_A_op，TAG=64，无 per-block 超时）：满格 29（含双 M 锚点 F1/F2-SC，M2.5/M3.0 各 300 行；双双未定→冻 M2.5）；short 2（F1-A3-4096 止 42，F2-A3-2048 止 147）；no-rows 11（A3 大 N 内存墙/探针调度 + SCL8 16384 锚点双 M/32768 探针无行）。F3 exploratory 四格皆满 300 行（F≤9 按冻结规则列未定，不参选）。
- 主表 OPT（Net_seg 最大，decided+N_valid）：F1-A3 N1024（2645652，FER 0.0767）；F1-A4-SC N2048；F1-A4-SCL8 N2048；F2-A3 N1024（2530780，FER 0.0333）；F2-A4-SC N1024；F2-A4-SCL8 N4096；F3 三行全未定。只报数，不做排序判定（M1 效力外）。
- A6：桥 T0/T1 ok（上已记）；3 点矩阵 6 格全 overtime-risk short（探针外推 21k–230k s > 1800s 格预算，0 块）；未降级为 stub。
- 验收自评：M-A34-01 达成（cap300+fullsym kept+矩阵含 F3）；M-A6-01 达成（桥 ok + 3 点矩阵位置全 short 如实）；M-LOG-01 达成（本单一日志，OP-M2 唯一写者）；M-CLEAN-01 达成（git diff 空；仅新增 3 文件；机器根 git-ignored；未碰 mt_a1a2_*）。
- 探针临时文件已清（workspace/c3m_probe_*）。失败尝试保留：首轮 4 分片异常终止 + 探针 B=1 续跑 bug（修复①）+ 短记录缺表键（修复②），均同日志。

## 2026-10-09 00:08:45+0800 OP-M2 --full 汇总
- --full 落盘：cells=1 main=1 wall=16s
- events=[]

## 2026-10-09 02:16:56+0800 OP-M2 --full 汇总
- --full 落盘：cells=1 main=1 wall=7640s
- events=[]

## 2026-10-09 10:58:15+0800 OP-M2 --full 汇总
- --full 落盘：cells=2 main=2 wall=554s
- events=[]

## 2026-10-09 11:06:15+0800 OP-M2 --full 汇总
- --full 落盘：cells=2 main=2 wall=480s
- events=[]

## 2026-10-09 11:14:18+0800 OP-M2 --full 汇总
- --full 落盘：cells=2 main=2 wall=482s
- events=[]
