# M5 Pre-EXECUTE draft — 真实帧验证（DECIDE，需用户明确确认后才生效）

> 本文件是草案：所列命令/预算/输出根在用户明确说"执行"之前一律不执行。
> Track（生效后）: **DECIDE**（真实数据、claim-bearing）。需配套 Pre-RESULT 独立审查。

## 授权请求（请用户确认以下三项）

1. 在三源全部 key-eligible 超帧（200/276/364 个 1024 符号超帧）上各跑一次冻结 MSD（M2 点）
   与 NB-LDPC（M4 臂）真实帧解码。
2. 墙钟预算：MSD 51 块 × ~0.3 s + NB 51 块 × ~45 s ≈ 40 min，×1.5 = **5400 s 上限**。
3. 输出根：`workspace/m5_realframe/m5_<uuid>/`（新鲜 UUID，执行前验空）；只加法写入。

## 冻结执行命令（草案，待批）

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m5_realframe --config <frozen> --output-root workspace/m5_realframe/m5_<uuid>
```

实现（批后才写）：复用 M2/MSD 冻结矩阵与 NB v28 路径；输入为 key-eligible 超帧索引
（VAL/HOLD 池视为已用开发输入——本批只做一致性验证，不做新鲜 OOS 声称）；
连续超帧分组为 16384 符号块（12/17/22 块/源，余数丢弃并声明）。

## 判据（MDE 纯算术，已算得）

- 合成预测 FER≈0；真实帧只做一致性验证：0 失败落在合成 Poisson 95% 带内即一致。
  0 失败时真实 FER 95% 上界：12 块→0.221，17 块→0.162，22 块→0.127。
- 真实帧**不能**测 FER 尾部、**不能**仲裁接近方法（pairwise SE~0.2）——结论 ceiling 预先冻结。
- 口径：统一 f（含实际 tag/泄漏、accepted-wrong 隔离、失败逐块加权）；undetected 永不并入。
- 停规则：超预算/撞墙保留已跑块（逐块落盘）；Pre-RESULT FAIL 则返工不发表。

## 输出

`RESULT.md`（ f、失败计数及 CI、accepted-wrong 隔离、实际 tag/泄漏、一致性检验）+
`INDEPENDENT_ACCEPTANCE.md`（独立线程 Pre-RESULT）→ 主线程接受 → U-2 闭环。
