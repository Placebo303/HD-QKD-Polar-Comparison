# S-5 Pre-EXECUTE — NB全符号链真实复验（DECIDE，已附条件授权）

> 授权：用户附条件授权（S-3'''最优点 + 墙钟/失败类型双条件）。条件核验：
> (1) 代理最优点投影墙钟：875超帧×~25 s/12池 ≈ 30 min + 加载/构建 ~20 min ≈ 3000 s ≤ 5400 s ✓；
> (2) S-3'''无模型外失败（u2/plane失败皆模型内，undetected 0）✓。两条件皆通过，执行。
> Track: DECIDE（R1原数据，标注"已用数据上的再检验"）。需配套 Pre-RESULT（R13核对u1+u2覆盖）。

## 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3prime_u1chain --real --output-root workspace/s5_nbfull/s5_20261006
```

## 冻结设计
- NB全符号链：u2 m=224 base + 232 rescue（S-3'''最优点，fresh A208族构建，fc=0/rank=224门过），
  u1五面SPC-10 + K16 rescue（链式条件先验），R1臂，完整符号口径（R11）。
- 输入：三源VAL/HOLD真实超帧（205/287/383，冻结M5链）；bundle/先验全TRAIN派生。
- 输出根：`workspace/s5_nbfull/s5_20261006/`（下方验空记录）。

## 检查单（执行前）
- [x] 分支 formal-ir-v72p1-addendum-clean；脏树仅本批scoped文件
- [x] 聚焦测试：接线契约（合成数组）通过；门控构建fc/rank通过
- [x] 授权：附条件授权 + 双条件核验通过（上）
- [x] 输出根验空（下）；预算5400 s；逐超帧JSONL落盘；撞墙保留
- [ ] Pre-RESULT（跑完后）

## 预算与停规则
- 预算 **5400 s**；单超帧240 s cap（超限记失败保留）；G-1（f≤1.40）如实记录 verdict。
