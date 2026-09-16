# Prompt — D7-B easy-regime freeze, implementation and Pre-EXECUTE R1

在仓库 `D:/Code/HD-QKD_Polar_Comparison`、分支
`formal-ir-v72p1-addendum-clean` 中完整执行：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`

你可以长时间自主托管完成包内 T0→T6：OpenSpec/prereg 冻结、最小 runner 与测试实现、
独立实现评审、独立 Pre-EXECUTE 评审、本地 scoped commits 和 closeout。不要按小步骤
反复询问；只在全部 B01–B20 完成，或命中一个具体硬 STOP 时返回。返回只报 delta。

主线程已接受 D7-A certification：GF32 arithmetic、direct-SP/FFT、tree posterior、
row-layered recurrence、`final_beliefs` log-domain 和 L1→L2 APP 在认证范围内均通过。
本任务只回答“历史 decoder 是否存在清晰 easy operating region”，不重新审判 D7-A，
也不开展 flooding、双向 oracle、graph/mother 搜索或 Cascade。

最高风险边界：

- 起始 HEAD `f98dde08`；先读完整任务包、AGENTS、memory、D7-A artifacts 和源码。
- 本任务允许规划、实现、fake/unit tests 和双独立评审；**不授权 D7-B scientific run**。
- 不得运行冻结 future command，不得翻 authorization，不得创建
  `workspace/d7_b_easy_regime_<uuid>/` 科学结果根。
- 仅 D7-A tiny synthetic correctness fixtures 可调用历史核作单元验证；不得读取
  Model-F/CAL/VAL/real/raw/formal/VOID，不得运行任何 `--phase`、R1d、G1、G2。
- 64-cell matrix、四类 prior、四个结构 tier、cap ladder、420 calls、1500/1800/120s、
  `<2GiB` 和 terminal priority 必须先冻结，不能见结果后调参。
- runner 必须 lazy-bind decoder、支持注入；import/help/dry-run/unauthorized 路径零绑定零根。
- 当前未提交 SOP/OpenSpec 标准化改动及 `.workbuddy/tasks/` 属包外管理状态：不得 stage、
  commit、清理或改写。使用显式路径和 numstat，不要求全局 porcelain 干净。
- 只能逐路径 stage、本地 commit，不 push；禁止 clean/reset/checkout/stash/rebase/amend。
- 独立实现 reviewer 与 Pre-EXECUTE reviewer 必须检查源码和代表性重算，不能只接受绿色
  测试。允许一个窄 implementation rework；科学契约歧义立即 STOP 回主线程。
- PASS 后仅把 gate 置为 `D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` 并停止；不能
  自己请求、推定或制造执行授权。

按任务包 §10 汇报，并原样结束：

`D7-B easy-regime 已完成冻结、实现与独立 Pre-EXECUTE 评审；尚未授权、未执行，R1d 继续暂停，G1/G2 均未授权。`
