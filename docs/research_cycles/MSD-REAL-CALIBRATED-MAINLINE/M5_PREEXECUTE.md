# M5 Pre-EXECUTE — 真实帧验证（DECIDE，已授权，可执行）

> Pre-EXECUTE 检查（2026-10-05，主线程记录）：
> - 分支：`formal-ir-v72p1-addendum-clean` ✓；脏树：仅本批 scoped 文件，冻结基线/输出目录无改动 ✓
> - 聚焦测试：`test_msd_m5_realframe.py` 3/3 通过（分组/块解码/一致带算术）✓
> - 冻结输入/阈值/命令/预算/停规则：见下 ✓；用户明确授权：「批准执行」+ 持续推进授权 ✓
> - 目标输出缺席：`workspace/m5_realframe/` 不存在（已验空）✓；预算 5400 s ✓
> - 精化记录（授权范围内忠实项）：NB 按原生 1024 超帧跑（200/276/364），MSD 按 16384 块跑
>   （12/17/22，16 超帧一组、余数丢弃声明）；其余与草案一致。

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
