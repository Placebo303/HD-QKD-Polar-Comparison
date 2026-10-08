# C-1 实现包（冻结，2026-10-08）

> Track：实现（无轨道门；C-1 按预注册"实现，无轨道门"）。
> 依据：`docs/C_BATCH_PREREG_20261008.md` §3–§4、C1盘点（`C1_INVENTORY.md`）、
> R16记账（`C3_DESIGN.md` §1）。只许加法，不许改动冻结基线与已有 outputs。

## 1. 目标
统一对比框架接入 A1–A7；新做 A3（GF(2k+1) LDPC）与 A4（GF(2k+1) Polar）；
实现 k-bin 推广（支撑 {−k..k} → 模数 q=2k+1 的加性信道）。
k=1,2,3 → q=3,5,7（均为素数，F_q 算术良定）。

## 2. 文件范围（只许新增下列文件 + 对应测试；其余一律只读）
- `comparison_bench/src/comparison_bench/formal_ir/msd_c1_kbin.py`（OP1）
- `comparison_bench/src/comparison_bench/formal_ir/msd_c1_nbldpc.py`（A3，OP1）
- `comparison_bench/src/comparison_bench/formal_ir/msd_c1_nbpolar.py`（A4，OP2）
- `comparison_bench/src/comparison_bench/formal_ir/msd_c1_runner.py`
  （统一runner + R16记账 + A1/A2/A5/A6/A7适配，OP2）
- `comparison_bench/tests/test_c1_kbin.py`（OP1）
- `comparison_bench/tests/test_c1_nbldpc.py`（OP1）
- `comparison_bench/tests/test_c1_nbpolar.py`（OP2）
- `comparison_bench/tests/test_c1_runner.py`（OP2）
- 临时产物只许写 `workspace/c1_<uuid>/` 新建子目录。

**禁区**：`src/`、`experiments/`、`tools/`、`results/`、
`comparison_bench/outputs_comparison/`、任何已有结果目录；
禁止读取 `D:/Data/` 原始数据；禁止网络；禁止复制 sibling 仓库代码（只许只读 import，
缺失则状态透传 `unavailable`，不作为阻塞）。

## 3. 功能规格

### 3.1 k-bin（OP1）
- `support_of(k) -> list[int]`：{−k..k}；`modulus(k) -> 2*k+1`。
- `fold_error(e, D, k)`：`(e mod D)` 折叠到 {−k..k}，超出记 `None`（rest）。
- `params_from_stats(*, support, p, p_minus, k)` →
  `(q, H_q, ideal_bps)`：q 元加性信道条件熵与每符号理想披露（比特/符号），
  公式显式写清（对称先验 g(e) 由 p、p_minus 构造，rest 质量单独列，不吞入）。
- k=1 时退化为 G-1 三值（须有断言对上 H(e)=0.8032 量级的一致性测试，用 T2-1M
  落盘三值概率做纯算术对照，不读原始数据）。

### 3.2 A3 GF(q) LDPC（OP1）
- `construct(n, m, q, seed)`：GF(q) 稀疏校验矩阵（RA-like 或 PEG-like，
  非零元均匀随机，种子确定；禁止整目录搬运既有 GF(32) 代码，允许调用
  `msd_peg_code.build_peg_code` 取二元骨架后再赋非零元，并注明出处）。
- `disclose(a_symbols) -> (syndrome_symbols, bits)`：syndrome 符号与比特数
  `m*log2(q)`（m*log2(q) 非整数时向上取整并注明）。
- `decode(b_symbols, syndrome, prior_g, max_iter) -> (a_hat | None)`：
  和积/QSPA（对数域，防溢出只需最小必要处理），失败返回 None（不抛异常）。
- 成功判据由 runner 的 tag 复核，不在本模块。

### 3.3 A4 GF(q) Polar（OP2）
- F_q 上 Arıkan 核（q 素数），`frozen_set(n, k_info, channel, prior_g)`：
  按 Bhattacharyya/GA 可靠度排序取信息位（方法写死并注明，q=3 先行，5/7 同代码路径）。
- `encode/disclose/decode`（SC；SCL 列表 L 可选，默认先 SC，能跑通再加 L=8）：
  API 形状与 A3 对齐（`construct/disclose/decode` 同名同参序）。
- 允许只读 import sibling `polar_core` 做交叉核对，但主路径必须是本仓库新代码。

### 3.4 统一 runner + R16 记账（OP2）
- `net_of_cell(*, kept_bits, L_EC_bits, tag_bits, n_fail, n_blocks, C_total, ...)`
  实现 `C3_DESIGN.md` §1 公式（逐块净贡献、Net_seg、Net_per_coin、w_tail、
  FER点估计、Wilson敏感性、β附带列），纯函数，全分支单元测试。
- `run_cell(method, N, channel, B, seed, out_jsonl)`：只跑**合成参数化信道**
  （(p,p_minus,k) 或 BSC 退化），B 由调用方定（本批实现测试用 B≤30；
  B≥300 是 C-3 的事，不在本包执行）。
- 适配器：A1（复用 `msd_g5_bakeoff`/`msd_g2_twolevel` 的 per-block 口径
  `{a_ok,exact_full,undetected,L_A,L_B,extra}` → 统一行，不重跑其 DECIDE 数据）；
  A2（同文件 polar 分支口径）；A5（wrap `methods/layered_ldpc_lite`）；
  A6（wrap `msd_m4_nbldpc` 行口径，frozen v28 不动）；
  A7（sibling 只读 import，缺失则行状态 `unavailable`，不断言失败）。
- 输出行键（冻结）：`{method,N,block,ver,u,kept,L_EC,tag,T_dec,code_hash}`；
  `undetected` 永单列；状态值沿用 `ok/reference/stub/unavailable/decode_failed`
  不得私自转 `ok`。

## 4. 测试/证据矩阵（qkd_env，`pytest -p no:cacheprovider`，写 `workspace/c1_<uuid>/`）
- T0：四个新模块 import 成功；`fold_error`/熵/ syndrome 比特数小算例精确断言；
  q=3 无噪声编解码往返精确成功（固定种子）。
- T1：q=3 小噪声（p≈0.05，N≤256，固定种子）A3/A4 译码运行无异常且成功块非零；
  `net_of_cell` 覆盖成功/失败/undetected/尾部四分支；
  runner 在合成信道 B=10 跑通并落盘 JSONL 行键齐全。
- 禁止项：任何测试不得读 `D:/Data`，不得跑 B≥300，不得写 production 输出根。

## 5. 验收 ID
- C1-KBIN-01：k-bin 三函数 + G-1 三值算术对照测试通过。
- C1-A3-01：A3 构造/披露/译码 API + T0/T1 通过。
- C1-A4-01：A4 构造/披露/译码 API + T0/T1 通过。
- C1-RUN-01：runner + R16纯函数全分支测试 + B=10合成跑通。
- C1-ADAPT-01：A1/A2/A5/A6/A7 适配行（A7 允许 `unavailable` 透传，需有测试锁定该行为）。
- C1-CLEAN-01：`git status` 仅本包新增文件；冻结目录零 diff。

## 6. 返回条件（二选一）
完成：逐 ID 报测试命令与结果（通过数/失败数；失败计数为个位数时只写「未定」并附原始数供主线程判定，
不自行宣布通过）；或阻塞：失败命令、精确报错/traceback、已试补救、需要主线程做的一个决定。
"大致完成"不是完成报告。
