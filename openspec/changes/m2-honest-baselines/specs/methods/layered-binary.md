# Spec delta: methods/layered-binary (new contract only)

本文件为新增契约，不改 `openspec/specs/` 任何现有文件。

## S-LB-01: 身份与替换关系

- `layered-binary` SHALL 为分层二元 LDPC 方法契约（逐 Gray 位面熵分配码率 + 盲协调），替换 V19 保守行数（f=4.169）稻草人。
- SHALL NOT 预设 FER 胜负；SHALL NOT 改 schema/列名/键名/CLI/输出文件名（AGENTS §5.3）。

## S-LB-02: 分配与构造

- 逐位面码率分配 SHALL 使用冻结位面熵 `H_L1 + H_L2`（0.801038 / 0.825566 / 0.832563），SHALL NOT 重拟合。
- 每位面 SHALL 独立构造（n=64 既有族语义保持）。

## S-LB-03: 盲协调与译码

- 盲协调 SHALL 为多段小步长增量揭示，每段公开量 SHALL 计入 `leak_EC` 分解。
- 二元 SPA `max_iter`–streak SHALL 冻结（实现 change 不得调参）。
- 成功 SHALL 要求每位面综合征一致 + Toeplitz 验证（t=64）。

## S-LB-04: 会计（A-CMPE-1..7）

- A-CMPE-1/2/3/4/5/6/7 映射 SHALL 与 design §7 一致：四计数隔离、`f_super`/`f_eff` 双数、`leak_EC`+64tag 分列、wall/RSS/消息数、`N_req` report-only vs key-eligible（200/276/364）、`d`/`q`/`n_IR` 分离、历史行不可比即标、禁 SKR、四列归属。
