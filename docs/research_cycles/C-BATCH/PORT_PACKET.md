# 译码器移植包（冻结草案，2026-10-08；用户已批准立项）

> 性质：实现包（AGENTS.md 矩阵：实现类变更无 track 门）。
> 目标：把 C-3/M 波中实测的慢译码器降到部署/对比可用的量级，
> **严格等价数值移植**（bit-identical），不碰纠错能力（用户 10-03 指示兼容）。
> 范围外（另立包，不在本包）：分层调度、EMS/FFT 近似、自适应列表等
> 改变运算顺序/数值的一切优化；QSPA 的 C++ 重写；任何真实数据运行。

## 1. 两项任务（可并行，写作用域隔离）
- **P-SCL**：隔壁仓库 C++ SCL-8（`low_dim_opt/core/scl_cpp/`，只读引用）
  接入 A2/A4：原地构建调用（不整目录搬运；若需隔离则 vendor + 出处标注，
  按 AGENTS.md §5.1/R8）；Python SCL（SC/SCL8，含 CRC 路径）逐向量比对。
- **P-QSPA**：QSPA 热点循环 numba JIT（保持浮点运算顺序逐位一致，
  直译式移植，不重排更新顺序）；Python 版逐向量比对（含 max_iter 耗尽、
  失败返 None、非法输入三边界）。

## 2. 文件范围（只许新增 + 只读引用）
- 新建：`formal_ir/port_scl_cpp.py`（桥）、`formal_ir/nbldpc_qspa_numba.py`、
  `tests/test_port_scl.py`、`tests/test_port_qspa.py`。
- 只读：sibling `scl_cpp/` 源码、现有 Python 译码器（`msd_c1_nbpolar.py`、
  `msd_c1_nbldpc.py`，一律不改）。
- 临时产物：新建 `workspace/port_<uuid>/`（向量库 + 计时表）。
- 禁区：真实数据、已有 outputs、冻结基线；禁止借移植之名改译码逻辑
  （diff 必须只含桥/移植新增行 + 测试）。

## 3. 测试/证据矩阵（qkd_env，`pytest -p no:cacheprovider`）
- P-BIT-01：SCL 与 Python 版在冻结向量集上逐位一致
  （q ∈ {3} × N ∈ {64,256,1024,4096} × SC/SCL8 × 固定种子 ≥20 向量，
  含失败/边界；任一 mismatch 即 FAIL，无容差）。
- P-BIT-02：QSPA 同上（另含 max_iter={1,50,300} 三档、失败返 None、
  非法输入异常类型一致）。
- P-PERF-01：计时表（方法×N×实现三列：单块中位/p95，小 N 与大 N 各至少两档；
  目标仅供参考：QSPA ≥20x、SCL ≥50x，不达标不判 FAIL，只如实记录瓶颈）。
- 向量库落盘（种子+输入+双边输出，可独立重放）。

## 4. 验收 ID / 返回（二选一：逐 ID 结果；或阻塞四件套）
- P-BIT-01、P-BIT-02（必须全对，无"未定"余地：mismatch 就是 FAIL）。
- P-PERF-01（计时表完整即通过，不设加速比门）。
- P-CLEAN-01（`git diff` 仅桥/移植新增；冻结目录零改动；无 production 输出）。
- 结论上限：只报一致性与加速比；任何"纠错能力不变"的措辞以逐位一致证据为限，
  不得外推到未测 (q,N,种子) 组合。

## 5. 与 C-5/部署的接口（记录，不在本包执行）
- 通过后：M 波慢格（A3 大 N、A6）可用移植版重跑验证一致后提速；
  C-5 真实矩阵的译码配置优先选用移植版（经 C-5 Pre-EXECUTE 授权）。
