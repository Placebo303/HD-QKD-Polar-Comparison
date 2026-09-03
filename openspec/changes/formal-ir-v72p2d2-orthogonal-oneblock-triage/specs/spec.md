# Spec delta: formal-ir-v72p2d2-orthogonal-oneblock-triage (PLAN_CANDIDATE)

- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 spec 为 delta,
  不合并、不替代已接受 spec,不改 V72P1/V72P2/D1 已接受行为。
- 数学合同证不出记 BLOCKER,禁 TBD 猜测。Ponytail lite 禁框架/插件/事件总线/
  缓存/锁/retry/checksum。

## S-ARM 正交四臂

- S-ARM-01:基线 A SHALL 复用 D1 Arm A 已记录事实,SHALL NOT 重跑。
- S-ARM-02:L SHALL 用原 H + M0 prior + flooding 其余语义,SHALL 只变调度为 design §3
  的逐 row/check layered sweep。
- S-ARM-03:I SHALL 用 deterministic degree-balanced full-column interleaver
  (全 10240 列,前 1204 每 symbol 1–2 个,其余填满 10 bit,唯一算法/tie-break/seed,
  old→物理 `sym*10+bit`),M0 prior + flooding;syndrome SHALL 对映射后 H 与原物理
  Alice,prior SHALL 对物理 symbol;SHALL 保持 shape/nnz/degree multiset/rank/prefix。
- S-ARM-04:P SHALL 用原 H + 冻结 M2(`laplace,mu=0.0,scale=0.2714417616594907,
  eps=0.562251256281407`,公式见 design §5)+ flooding;SHALL NOT 读 Alice/SHALL NOT 重选;
  VAL CE 6.7871 SHALL 标历史非门槛且允许变差。
- S-ARM-05:三臂 SHALL 同 block/ladder/edge 预算/clip/tol/验证泄漏口径,
  SHALL NOT 混合因素,SHALL NOT 事后调参。

## S-LAY layered 合同

- S-LAY-01..10:实现 SHALL 满足 design §3 第 1–10 条(顺序/自排除/符号/sweep-residual/
  预算/warm-start/收敛语义)。
- S-LAY-11:若证不出真 layered SHALL 记 BLOCKER 并阻塞 ACCEPT,SHALL NOT 以 row-loop
  包 flooding 冒充。

## S-MET 诊断聚合

- S-MET-01:每 ckpt SHALL 含 design §6 最小标量集,不存全量敏感数组。
- S-MET-02:单边 `max|c2v|` SHALL 与 `max_v|Σ|` 分开;收敛 SHALL NOT 记正确;
  `candidate==Bob` SHALL 直接比;O1 SHALL 标 `POSTHOC_RECONSTRUCTED` 且不作 D 口径。

## S-IF 接口

- S-IF-01:SHALL 单选 A(不调用 deferred bug 路径,adapter 零改动)或 B(最小修复 + 回归),
  SHALL NOT 重构 adapter。

## S-EXEC 未来执行合同(本次不授权)

- S-EXEC-01:同 D1 块非新鲜;SHALL NOT 重跑 A;L/I/P SHALL 各一次,SHALL NOT rerun;
  臂间 c2v SHALL 独立;输出 SHALL 为新根恰四文件;预算依据 D1(臂 600s/全局见 PLAN)、
  edge 预算 10/ckpt/720/臂 SHALL 在未来 Implementation 冻结数值后另走
  Plan/Implementation/Pre-EXECUTE/Pre-RESULT;本计划 SHALL NOT 授权。

## S-CLAIM 判别与边界

- S-CLAIM-01:L/I/P escape/violation 判别 SHALL 按 PLAN_CANDIDATE.md 预注册条件;
  三无-escape SHALL 停微调转 grouped-mask tiny 排队或 GF32 对照。
- S-CLAIM-02:SHALL NOT 作 FER/SKR/因果/M2 优胜/推广断言;SHALL 保持 `undetected` 隔离;
  SHALL NOT 写三臂必胜。
