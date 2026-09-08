# D5 G1 information-recovery R2 独立评审报告 R1

- repo: `HD-QKD_Polar_Comparison`
- branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`
- 候选链: `88053563→a93106f5→21576add→1d4fa912`
- gate: `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`
- verdict: `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`
- PASS 含义（仅限）: 仅 additive candidate 与本报告归因可进入候选 Model-F 准备/验收链；不代表 production wiring、Model-F 替换、G1 修复、正式重跑许可、G2 readiness。

## C01–C12 评审表

| ID | 结论 | 证据摘要 |
|----|------|----------|
| C01 | PASS | 两路独立返回一致，候选链可追溯 88053563→a93106f5→21576add→1d4fa912 |
| C02 | PASS | 候选为 additive，不改动 frozen G1 逻辑与正式输出根 |
| C03 | PASS | lambda 语义决定性推导成立（见 §C03），total concentration per Bob column |
| C04 | PASS | cells/total/col 统计独立复算一致（见 §C04） |
| C05 | PASS | Q*/prior/dominance/归一独立复算一致（见 §C05） |
| C06 | PASS | old/candidate/D4 held-out CE/MI/tmass 独立复算一致，7.5094≠7.162347 已解释 |
| C07 | PASS | 归因主因 LAMBDA_APPLICATION_CONTRACT_DEFECT，disclosure/mother 为次因 |
| C08 | PASS | 三 call 确认与 w2/w4b 逐数一致，R1 29 calls / R2 53 calls 审计一致 |
| C09 | PASS | 六替代逐条否决/保留成立，L1 square 失败、L2 仅 52–64 约束 |
| C10 | PASS | 八测试杀伤力成立，guard 1d4fa912 修复已验证 |
| C11 | PASS | 字面命令与结果行成立：focused 10 passed / 三文件 229 passed 零失败 |
| C12 | PASS | 根/lifecycle equality 成立，scoped git diff 空，G2 absent |

## C03 lambda 语义决定性推导

- D4 builder: `comparison_bench/src/comparison_bench/formal_ir/v72p2d4r2_cal_gf32_model_rate_audit.py:329-349`
- canonical counts: `build_canonical_counts:246-261`
- 定义：
  - `n_b = counts.sum(axis=0)`（按 Bob 列求和）
  - `p_global = counts.sum(axis=1) / n`
  - `P = (counts + lam * p_global[:,None]) / (n_b[None,:] + lam)`
- 结论：total concentration per Bob column，单位 counts。
- grid: `logspace(-2,3,30)`；inner mean joint CE 最小；四 outer folds 全选 `137.3823795883264`；零列回退 `= p_global`。

## C04–C06 独立数字表

### C04 counts 几何

- cells: `1048576`
- total: `262144`
- col 均值: `256`（min `198` / max `325` / cell 均值 `0.25`）

### C05 候选先验强度

- `Q*lam = 140679.55669844622`
- prior 占比: `0.998183566972047`
- dominance: `549.5295183533055`
- 列归一 maxerr: `4.06e-14`

### C06 CE / MI / truth mass

- old: CE `4.999985322023371 + 4.999659312231358 = 9.999644634254839`，MI `0.0003553306407582113`，truth mass `~0.03124`
- candidate in-sample: CE `4.286720430201375 + 3.222719884634378 = 7.5094403148357545`，MI `2.48306874956704`，truth mass `0.25444987775455336`，列归一 `2.93e-14`，split `2.22e-16`
- D4 held-out: `3.8147422680157206 + 3.347605161943064 = 7.162347429958785`
- 解释 `7.5094 ≠ 7.162347`：不同总体 / 不同泛函 / refit 乐观性；like-for-like 是 `10.0 → 7.51`。

## C08 三 call 确认表

- review root: `workspace/d5_g1_r2_review_7f3a9c1e2b4d4f60/`（已清理）
- seed: `2026090600`
- square Hsq[:64]: seed `2026090801`，rank `64`
- n: `64`；frozen `max_iter 90`；`120s` watchdog

| call | 配置 | oracle-L2 | 收敛/early | iters | wall | tmass |
|------|------|-----------|------------|-------|------|-------|
| call1 | old + Hsq | false/false | 未收敛 | 90 | 0.5698s | 0.031245495554821028 |
| call2 | candidate + 同 Hsq/seed | true/true | 收敛 early | 10 | 0.0637s | 0.21866977384250286 |
| call3 | candidate + 冻 H2[:43] | false/false | 未收敛 | 90 | 0.4516s | — |

- 与 w2/w4b 逐数一致；R1 29 calls / R2 53 calls 审计摘要一致。

## C09 六替代检验结论

1. 否决：主因 `LAMBDA_APPLICATION_CONTRACT_DEFECT` 最早成立，其余替代不能解释 total-concentration 缺口。
2. 否决：disclosure 次因成立但非主因。
3. 否决：mother 次因成立但非主因。
4. 否决：L1 square 失败路径已排除。
5. 保留（受限）：L2 仅 52–64 约束，不扩展为主因。
6. 否决：其余数值/随机性替代不能复现 10.0→7.51 like-for-like 改进。

## C10 八测试杀伤力矩阵 + guard 修复

- 八测试杀伤力成立（contract / concentration / 回退 / 归一 / split / like-for-like / held-out 区分 / seed-frozen）。
- guard `1d4fa912` 修复说明：修复 guard 缺口后重跑，杀伤力保持。

## C11 字面命令与结果行

- `py_compile`: exit `0`
- focused: `10 passed, 155 deselected, 1.24s`
- 三文件: `229 passed, 46.18s`
- `cache_dir` warning: benign
- 本次 `229` vs T6 记录 `227`：均为零失败，计数差为非阻塞（见 §非阻塞）。

## 根 / lifecycle equality

- `cycle_state` 全 `false` + gate 精确 + G2 absent。
- `v72p2d5_g1/20260907_r2` 4 文件 `384/246/3210/330`，mtime `2026/9/8 02:39:50`。
- R2 根 17 文件前后一致。
- scoped `git diff` 空。

## 阻塞 / 非阻塞发现

- 阻塞发现：无。
- 非阻塞：
  - T5 未勾文档滞后
  - NaN/Inf 限测缺口
  - CRLF 噪声
  - w4b 头注 24 vs 16 笔误
  - 229 vs 227 计数差
  - `__pycache__` 已清除

## 正式 G1 重跑前 exact prerequisites（六条）

1. candidate acceptance → Model-F preparation packet + 独立 review。
2. additive 新 artifact 根（不复用正式根）。
3. CAL-only + Pre-EXECUTE / Pre-RESULT 双门。
4. L1 discriminator 决策。
5. 新冻结 formal experiment + 独立授权。
6. 上述全部满足前不得正式重跑 / 不得进入 G2。

## 禁止动作清单与命令清单

- 禁止动作（全部未做）：production wiring、Model-F 替换、G1 修复写入、正式重跑、G2 readiness 断言、覆盖正式输出、提交/push。
- 命令清单：`py_compile`、focused 测试、三文件测试、`git diff` 范围检查、`cycle_state` 读取；未执行正式重跑与高成本命令。

`G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`
