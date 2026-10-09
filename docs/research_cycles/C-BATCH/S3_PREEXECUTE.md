# S-3 Pre-EXECUTE — 真实数据软信息译码（DECIDE，真实解码）

> Track: DECIDE（真实解码）。**本文件只交用户确认，不执行**：
> 用户确认后，主线程按本包冻结命令执行（调参→冻结→每格一次真实运行）。
> 上位：R1–R17（含 R16 主度量/最优 N 口径）、`S1_VERIFY_LOG.md`
> （软输入 Bob 侧已核实；f 新规：f_hard=L/H_bin，f_soft=L/H_fine；
> 主度量为泄漏比特数 + 净密钥）、S-2 2×2 表（H 界输入，执行中）。

## 1. 冻结链（真实数据，两级二元链第一级为比较臂）

- 分帧：与 B123/S-2 同链（`read_ttbin_events` → 对准门控 → 标称配对 →
  `_frame_global` span 204800，bw=200，d=1024）→ 校准位移 `pb+δ*`
  （δ*：T2 −50/+50/+50，Jan23 −50/−50/−45，S-2 同值）→ 同帧 kept 对。
- 第一级（比较臂）：LSB 平面 `x = a0 = sa % 2`，Bob 侧信息 (b, fine)：
  - 硬臂：统一 LLR `log((1−p̄)/p̄)`（p̄ 为冻结模型边际，不随符号变）。
  - 软臂：逐符号 LLR（`msd_a6_soft_llr.p_given_v` 同式，S-1 已核 Bob 侧；
    (σ,μ) 取 S-2 前缀拟合冻结值，宽成分取前缀 ŵ）。
- 第二级（公共冻结，不比较）：符号位 PEG-BP（G-5 同配置 margin 3.0 +
  K2 rescue），两臂完全相同；高位算术重建。`undetected` 单列（tag 64 验证）。
- 码：标准 RA/PEG 二元系综实例（种子冻结，随包记录；不是新码，R17）。
  N 候选 {4096, 8192, 16384}，两臂**各取最优 N**（R16）。

## 2. 数据（真实块，配对比较）

- 主矩阵：T2-1M / T2-1.5M / T2-2M（bw200，校准后），约 525k/736k/982k 对 →
  N=16384 时约 32/44/60 块，N=4096 时约 128/179/239 块。
- 次 regime（若主矩阵跑通且预算有余）：Jan23 0dB / 4dB（266k/115k 对）。
- 配对：同一组真实块、同一 H、同一 syndrome，两臂共享随机种子流；
  差异仅来自 LLR 输入（硬 vs 软）。**冻结后在真实数据上每格只跑一次**。

## 3. 冻结命令（三段，确认后按序执行）

```text
# 段 0（R7 计时 smoke，真实数据，≤2 min）：每臂每 N 档各 2 块
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode --smoke --output-root workspace/s3_softdecode/s3_smoke_<date>
# 段 1（调参：S-1 代理 msd_s1_proxy + 参数化合成 (p,p-) + S-2 前缀律，按 R16 选两臂最优 N 与码率；合成 EXPLORE，不读真实块做选择）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode --tune --output-root workspace/s3_softdecode/s3_tune_<date>
# 段 2（冻结执行：每格一次；B 由段 0 实测成本 × 块数 × 1.5 定，上确界见 §4）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode --full --output-root workspace/s3_softdecode/s3_<date>
```

- 新增文件（加法，确认后才写）：`formal_ir/msd_s3_softdecode.py`（runner，
  复用 `msd_a6_soft_llr` 的 LLR 接口 + G-5 level-B 配置）；
  测试 `tests/test_s3_softdecode.py`（T0/T1：合成小块 + LLR 标定 + 配对记账）。
- R1 功效：配对 McNemar；主矩阵 N=4096 每源 >100 块，10% 级 FER 差高度可检；
  N=16384 每源 30–60 块，只报大效应 + 精确 CI，不追小差。

## 4. 预算与墙钟

- 段 0：≤ 120 s。段 1（合成）：≤ 3600 s。
  段 2 上确界：段 0 实测单块成本 × 总块数 × 1.5，封顶 **4 h**（14400 s）；
  超封顶则降 N 档重报，不硬闯。
- 输出根：每段 fresh（`--output-root` 已存在则中止，脚本内写死检查）。

## 5. 报告（冻结口径）

- 每格：泄漏比特数（L_A+L_B+rescue，如实分解）、FER 精确 CI
  （Clopper-Pearson）、净密钥（R16 Net_seg：kept−L−tag−kept·FER 口径）、
  McNemar 精确 p、附带 f（f_hard=L/H_bin，f_soft=L/H_fine）。
- `undetected` 单列，永不并入成功/FER。失败块保留块行。
- 结论上限：只报"同组真实块上软相对硬的泄漏/FER/净密钥差"；
  不报路线关闭、不报泛化（单点真实矩阵）。

## 6. 检查单（执行前，主线程在确认后逐项打勾）

- [x] 用户已确认本 Pre-EXECUTE（含 §4 预算封顶与 §2 数据范围）——2026-10-09"可以开始s3"
- [x] S-2 2×2 表已落盘（H 界输入；调参先验用 S-2 前缀律）
- [x] 新增 runner + 测试通过（T0/T1），`--smoke` 通过且输出根 fresh
- [x] 冻结基线零 diff；输出根验空；分支正确
- [x] 跑后独立 Pre-RESULT（S3_ACCEPTANCE.md，独立线程）—— **PASS**

## 7. 请用户确认的事项（本批返回条件中的那一个决定）

- 是否按本包执行 S-3（三段命令、§4 预算封顶 4 h、§2 数据范围）。
  确认后主线程执行，跑后做独立 Pre-RESULT 并报告泄漏/FER/净密钥/McNemar。

## 8. 补遗 A（2026-10-09，用户授权"重任务用更快语言和更多核"后追加）

- 译码器由 `ldpc.BpOsdDecoder`（product-sum，serial，50 iter）换成
  本仓 numba syndrome min-sum 核（`methods/binary_spa_numba.py`，M3 验证
  45.9×，`DEC_MAX_ITER=100`），两臂同设置、冻结（`msd_s3_softdecode.decode`）。
  A6 的 ldpc 结果仍为验证结论，不受影响（S-3 是独立测量）。
- 块级多进程并行（有序 map，deterministic；`NPROC_OF_N={4096:16, 8192:8,
  16384:4}`，dense 消息内存 bound，机器 32 GB、实测余量 15 GB，充足）。
- Smoke 重测：442 s → 161 s（文件读取成主导；hard 7.3 s/块全败慢径、
  soft 0.78 s/块）。§4 预算封顶 4 h 不变（更松）。
- 本补遗只换等价执行引擎（同 syndrome、同 LLR、同冻结码），不改 §1–§2 的
  科学冻结（码率梯子、N 候选、数据范围、配对口径、K2 rescue）。
