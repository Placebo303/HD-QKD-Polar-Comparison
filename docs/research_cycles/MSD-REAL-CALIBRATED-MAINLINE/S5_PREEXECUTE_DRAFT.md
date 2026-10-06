# S-5 Pre-EXECUTE（草案，待用户明确确认后才生效）

> Track（生效后）: **DECIDE**（R1 原数据真实帧）。主线用 (c)：R1 三源原数据复验，
> 结论一律标注「已用数据上的再检验（VAL/HOLD 已暴露）」。U-4 辅线盘点另行报批，
> 不在本包。需配套 Pre-RESULT 独立审查。

## 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3prime_u1chain --real --output-root workspace/s5_nbfull/s5_20261006
```

## 冻结设计
- NB 全符号链（S-3′设计）：u1 五面 SPC-10 + K16 rescue（链式条件先验），
  u2 m=184 base + 208 rescue（S-3″最优点），R1 臂，完整符号口径（R11）。
- 输入：三源 VAL/HOLD 真实超帧（205/287/383，冻结 M5 链，不重读新数据外）；
  bundle/先验为全 TRAIN 派生（与 eval 不重叠）。
- 输出根（验空后建）：`workspace/s5_nbfull/s5_20261006/`；逐超帧 JSONL 落盘。

## 预算与停规则
- 预算 **5400 s** 上限（估计 ~40 min：系列加载 ~10 min + 池化译码 ~30 min）。
- 单超帧 240 s cap（超限记失败保留）；撞墙保留已跑部分。

## 判据（G-1，原冻结）
- 完整符号真实 f ≤ 1.40，且与代理预测一致；valid-wrong 为 0（有则单独报告）。
- **诚实声明**：代理预测全符号 f≈1.97（upper ~2.66，m=184最优点；u2 undetected
  m=192一例已计入失败），G-1 点估计门大概率不达；
  本次运行的首要价值是第一个真实全符号 NB 数（目前为零）， verdict 如实记录，
  不预设通过。

## 输出
`s5_nb_summary.json`（E_L/FER/f/u1残错/undetected隔离）→ Pre-RESULT → RESULT →
主线程接受。U-4 辅线（其他采集盘点）不在本包。
