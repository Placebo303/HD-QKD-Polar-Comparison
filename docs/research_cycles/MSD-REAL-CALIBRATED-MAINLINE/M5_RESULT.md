# M5 RESULT — 真实帧验证（DECIDE，Pre-RESULT 通过后生效）

> 输入：三源 VAL+HOLD 真实对（冻结 A1/R1 链重读 ttbin + R1 断言；先验/adapter 均为
> TRAIN 派生，eval 不重叠）。MSD 冻结 M2 点按 16384 块（12/17/23，余数丢弃声明）；
> NB-marginal 冻结 A208 R1/R2 按 1024 超帧（205/287/383）。口径统一 f（含 tag 64、
> kept 加权惩罚、undetected 隔离）。证据根：`workspace/m5_realframe/m5_20261006/`；
>  verdict 伴件：`m5_verdicts.json`（band verdict + 精确二项 p + f 全输入重算）。
> 本结论 ceiling：一致性检验而已——不测 FER 尾部、不仲裁接近方法、不 KILL 路线
> （超冻结点传递声明范围）；NB f 为 u2-layer 口径；数字以 point + CI 引用。
> f upper95 为脚本精确值（`m5_verdicts.json` 的 `f_expected_upper95_recomputed` 字段，
> 与上表逐项一致）；band 假设下的 f 另见同文件 `f_at_band_upper_recomputed`。

## MSD 冻结臂（N=16384）

| 源 | 块 | L_base | rescue | E[L] | FER | und | f (upper95) | band verdict |
|---|---|---|---|---|---|---|---|---|
| T2-1M | 12 | 16027 | 4 | 16160.3 | 12/12 | 0 | 12.53 (12.53) | INCONSISTENT (p~0) |
| T2-1.5M | 17 | 16481 | 7 | 16645.7 | 17/17 | 0 | 12.12 (12.12) | INCONSISTENT (p~0) |
| T2-2M | 23 | 16558 | 8 | 16697.1 | 23/23 | 0 | 12.03 (12.03) | INCONSISTENT (p~0) |

合成预测 FER≈0（Wilson 上界 0.0126）；观测 52/52 失败，Poisson 带外 p~0。
失败定位 plane-1（`stages_passed=[true,false]`；plane-0 syndrome-pass 且 8/12 精确恢复，
无前缀污染）；plane-0 rescue 路径被演练（4/7/8 触发）但救不回 plane-1 失败。
真实 BER 与 TRAIN 一致（两面三源 D1 实测），误差计数 Poisson-like——通道未漂移；
传递失败机制为先验稀疏格过置信（诊断级证据，计数不进入结论）。

## NB-marginal 臂（N=1024，u2-layer 口径，u1 残差未计入）

| 源-臂 | 块 | rescue | E[L] | FER | und | f (upper95) | u1_mm | band verdict |
|---|---|---|---|---|---|---|---|---|
| T2-1M R1+R2（2 臂合并显示） | 205 | 103/124 | 1020.1/1024.2 | 11/205 | 0 | 1.9316/1.9364 (2.3811/2.3857) | 188 | CONSISTENT (p=0.141) |
| T2-1.5M R1 | 287 | 132 | 1018.4 | 8/287 | 0 | 1.5855 (1.8710) | 193 | CONSISTENT (p=0.835) |
| T2-1.5M R2 | 287 | 169 | 1023.6 | 14/287 | 0 | 1.8195 (2.1622) | 193 | CONSISTENT (p=0.701) |
| T2-2M R1 | 383 | 194 | 1020.3 | 16/383 | 0 | 1.7259 (1.9966) | 250 | CONSISTENT (p=0.346) |
| T2-2M R2 | 383 | 239 | 1025.0 | 15/383 | 0 | 1.7029 (1.9675) | 250 | CONSISTENT (p=0.448) |

*upper95 为 Wilson 上界对应 f（见 verdict 伴件精确值）。
合成带（0/100→0.037，1/100→0.0545）内全部一致；真实 FER（0.028–0.054）高于合成点估计
（0–0.01）但带内相容——期望方向（真实含稀疏格风险），幅度可用 band 解释。

## 结论（Pre-RESULT 通过后由主线程接受）

1. NB-marginal 真实传递一致（6/6 臂带内）——U-1 并行线中可部署的一臂。
2. MSD 冻结（M2 点）真实不一致（52/52）——不进入生产/资格；路线不 KILL，
   机制指向先验估计（稀疏格过置信）而非 MSD 结构；修复方向：平滑/概率下限 +
   重新验证（M1″-prior），不在本批。
3. 真实帧能力边界重申：12/17/23 长块只能做一致性验证（0 失败对应 FER 上界
   0.22/0.16/0.13）；尾部与仲裁仍靠合成。

> **Supersession note (2026-10-06, review F-1, original text above unchanged):**
> 结论 1「NB-marginal 真实传递一致、可部署的一臂」**撤回 u2-layer 口径下的可部署含义**。
> `exact_ok` 只覆盖 u2 层；完整符号成功仅 74/205、148/287、203/383（47–64% 块有 u1 残错），
> 诚实完整符号 f 远大于 2。NB 行仅保留为"u2 层一致性"诊断证据，不得作为完整符号效率引用。
> 完整口径对比见 S-3/S-4 产出。详见 `docs/ROADMAP_20261006_REVIEW.md` §1.2 F-1。
