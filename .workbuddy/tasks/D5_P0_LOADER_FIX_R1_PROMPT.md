# Paste-ready prompt — D5-P0-LOADER-FIX-R1 (code fix, no execution)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

本次任务是**修一个已定位的生产缺陷**，写代码，但**不跑 P0/G1/G2、不跑 decoder**。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_LOADER_FIX_R1_TASK_PACKET.md`

先完整读完，再按 T1 → T7 执行。

缺陷已经定位清楚，**不要重新调查、不要质疑结论**：

2026-09-07 一次已授权的 P0 调用在 0.376 秒内被拒，报
`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`。这条消息是**假的**——产物
`workspace/v72p2d5_model_f_input/20260907_r1/` 完好，按文件路径直接加载得到
`counts_ab (1024,1024)` sum `262144`、`p_b (1024,)` sum `1.0`。

真实根因：`_load_model_f_input_or_blocked`
（`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py:2170`）
靠**包导入**去够产物。而 `python scripts/v72p2d5_gf32_rate_mother.py` 这种启动
方式下 `sys.path[0]` 是 `scripts/`、cwd 不在 `sys.path` 上，两条 import 全部
`ModuleNotFoundError`，落进 `except Exception` 报成"缺科研输入"。CLI 自己加载
核心模块时用的是 `__file__` 推导 + importlib 按文件路径加载，消费侧没沿用。

要修三件事（都在任务包里写死了）：

1. **T1**：消费侧按 `__file__` 定位同目录的 `v72p2d5_model_f_input.py`，用
   importlib 按文件路径加载。已验证锚点：`Path(__file__).resolve().parents[4]`
   就是仓库根，模块是同目录兄弟文件。**不许改 `sys.path`、不许依赖 cwd、
   不许目录搜索、不许猜测式 fallback 链。**
2. **T2**：`MODEL_F_INPUT_FORMAL_ROOT` 是相对路径，现在按 cwd 解析。改成按 T1
   的仓库根解析（绝对路径则直接用）。这和 `v72p2d5_prepare_model_f_input.py`
   里已经修过的 PX11 是同一个契约——照着它的行为做，但**不要 import 它**。
3. **T3**：把三种失败分开，不许再折叠：**加载器不可用**（模块文件缺失/执行失败，
   属实现故障，**绝不许说 MISSING_CAL_TRAIN_COUNTS**）、**产物缺失**（真正的
   `MODEL_F_BLOCKED`，且必须在消息里写出它实际查看的绝对路径）、**产物存在但
   非法**（校验失败，要把加载器原始错误透出来）。保留 `MODEL_F_BLOCKED` 常量给
   真·缺失那一类，另两类用新的独立常量。不许用吞掉原因的宽 `except`，要链式抛出。

**T4 的回归测试是重点，别糊弄。** 现有 195 个测试全过却没抓到这个 bug，因为它们
要么注入表、要么 monkeypatch 根，而且 pytest 会把 rootdir 放进 `sys.path`——
**没有一个测试走过真实启动条件**。所以必须补：cwd 无关的根解析、仓库根不在
`sys.path` 时加载器仍可达、产物缺失报真·缺失且带绝对路径、产物非法报非法而不是
缺失、注入表仍然短路且零文件访问。

**测试一律只用 `tmp_path` 产物，任何测试都不许读真实的 Model-F 正式根。** 这种
生命周期耦合正是之前那次未授权 G1 事故的成因。也不许为了让新测试过而削弱既有的
SAFE A/B/C 隔离或 AST 静态守卫。

其它硬约束：不许跑 P0/G1/G2（T5 里那次 `--phase p0-cost` 除外，它必须 exit 3）、
不许跑 decoder、不许跑 prepare 脚本、不许读 CAL/VAL/parquet、不许动 `workspace/`
下任何既有产物、不许改任何 `*_execution_authorized` 或 `next_gate`、不许改任何
冻结科研常量（种子、`f` 集、`m1`/`m2`、`CE_*`、`LAMBDA_STAR`、`MAX_ITER`、阻尼、
预算、调用数、输出根、判级阈值）、不许超范围重构、不许 `git push` 或
`add -A`/`add .`/`commit -a`/`reset`/`stash`/`checkout --`/`clean`/`rebase`/
`commit --amend`。只许改任务包允许清单里的三处。

有一点必须在报告里写明、不许含糊：**这个修复无法端到端证明**，端到端验证需要一次
新的已授权 P0 运行，而你没有该授权，也不许去要。你能证明的上限是单元层面的路径
解析与错误分离。

最后按 T7 提交一次（本地，不 push，message 用任务包原文），并按任务包 §9 汇报：
diff 摘要、改动前后的 pytest 原文行、T5 拒绝检查、受保护根的前后 stat、以及
true/false 清单。然后停下——下一步是独立复审，不是再跑一次。

=====
