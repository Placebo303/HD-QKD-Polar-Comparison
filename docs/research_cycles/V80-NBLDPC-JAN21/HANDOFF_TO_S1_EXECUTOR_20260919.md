# 给 S1 执行会话的手递包（直接粘贴，2026-09-19）

S1 已 HOLD：不解释当前臂输出，不进 flip/S2/S3，等修复+独立复审+新授权。

F1：PRIMARY 0/420 收敛——L2 网格全在可行上限 0.83862 之上，
正确 m2≈54（f=1.3），当前 m=24–31 是层↔全符号映射错。
F2：门没筛 converged（runner:866-876）：PRIMARY 伪 pass 0.7506<1
违 SW 界；SECONDARY max 1.454>1.15 注定 fail；f_row 只是算术（line 538）。

立即动作：
1. 停一切结果解释和 S2 推进；
2. 保留 SECONDARY 现场，不删执行根 workspace/s1_mcde_07723233-*；
3. 不改 runner/tests/config-hash/种子；不等新授权不重跑；
4. 去做会话对账：decision-log 止于 4438，缺 D5 复审/授权/开工条目，
   S1_READINESS 头仍 NOT accepted。

证据指针：INDEPENDENT_REVIEW_20260919.md §1–§2；runner:866-876；line 538；
HOLD 全文见 S1_HOLD_20260919.md。本包不授权任何执行。
