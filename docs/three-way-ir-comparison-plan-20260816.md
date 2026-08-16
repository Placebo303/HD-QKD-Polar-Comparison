# Three-Way IR Comparison Plan — Binary Polar / Binary LDPC / Nonbinary LDPC (2026-08-16)

Status: PLAN — ready for a new DSH conversation; this document is the executable contract

## 0. Objective
对 V17/V13-R3 的 10 dB Type-II 高维 QKD 数据（q=1024，Gray，256-symbol 帧，legacy_drift_audit
边界）分别构建并运行三条信息协调路线，并做统一、可比、诚实的效率对比：
1. **Binary Polar MLC**：逐 Gray 位面 binary Polar 码（MLC）。
2. **Binary LDPC MLC**：逐 Gray 位面 binary LDPC 码。
3. **Nonbinary LDPC**：q-ary LDPC（q=16 folded 代理 → q=64/256/1024 结构化信道，按 V18/V19 管线）。

Target gate（三路统一）：
- 所有成功帧必须 exact_correct / syndrome_consistent，不允许静默把 decode_failed 改为 ok。
- 效率目标：**f ≤ 1.3**（首选）；若有限长代价无法达到，记录每路能达到的最低 f 与 FER。
- 泄漏记账两段式：`f = (syndrome_bits + disclosed_public_bits) / H_full`，
  H_full(q=1024)=0.549955 bits/symbol（V17 模型）。
- 输出仅写 `comparison_bench/outputs_comparison/nonbinary_diagnostics/` 下新的 additive 目录。
- 不修改 frozen `src/`、`experiments/`、`tools/`；polar/LDPC/nonbinary 新代码只放 `comparison_bench/`。
- 不 push；所有 git 写操作仅本地 commit。

## 1. Shared inputs
- 每平面错误概率：`nonbinary_v18_b2_structured_de._V17_PER_PLANE_ERROR`（MSB→LSB）。
- 全信道：q=1024, Gray, H_full=0.549955。
- 合成测试：每平面 BSC(p_i)，确定性 seed；同时保留 real-pairs 最终核对入口（legacy drift audit 边界）。
- 帧拼接：物理帧 256 symbols；每路可在 N=1024/2048/4096 bits/symbols 上评估并换算 per-symbol f。

## 2. Route P — Binary Polar MLC
Assets already present:
- `comparison_bench/src/comparison_bench/formal_ir/v19_polar_ga.py`（GA 构造）
- `comparison_bench/src/comparison_bench/formal_ir/v19_polar_crc.py`（与 C++ 匹配的 CRC-16 编码）
- `comparison_bench/src/comparison_bench/formal_ir/v19_ca_scl_wrapper.py`
- `comparison_bench/src/comparison_bench/formal_ir/v19_ca_scl.cpp|dll`（list=32）
- `comparison_bench/src/comparison_bench/formal_ir/v19_ca_scl128.cpp|dll`（list=128）
Frozen read-only decoder: `src/reconciliation/real_polar_sc_rescue.py`、`src/reconciliation/cpp_polar/`。

Tasks:
- [ ] P1: run per-plane Polar MLC with **proper CRC-aided SCL**（payload K-16，CRC-16/CCITT 与 C++ 一致）。
- [ ] P2: construction comparison: PW / GA / Monte-Carlo / Tal-Vardy（新 v19 module）。
- [ ] P3: record per-plane FER, syndrome bits, total f for N=2048/4096.
- [ ] P4: one best-configuration 10-plane synthetic run, deterministic seed, evidence JSON.

## 3. Route L — Binary LDPC MLC
Assets already present:
- `comparison_bench/src/comparison_bench/formal_ir/codebook_v4.py`（frozen v4 H1 matrices, N=256, 10 planes）
- `comparison_bench/src/comparison_bench/formal_ir/codebook_v5_h2.py`（frozen v5 H2 fallback）
- `ldpc==2.4.1` installed (`ldpc.BpOsdDecoder`)
- `comparison_bench/src/comparison_bench/cli/run_v19_ldpc_de_screener.py`
- `comparison_bench/src/comparison_bench/cli/run_v19_binary_mlc_prototype.py`

Tasks:
- [ ] L1: reproduce existing baseline: v4 H1 + v5 H2 fallback, 50 frames/plane, record f≈4.17.
- [ ] L2: extend binary DE to dc>13 in a new v19 module; screen planes 0–7 for high-rate candidates.
- [ ] L3: try MET-LDPC / degree-one VN or rate-compatible puncture/shorten for low-error planes.
- [ ] L4: one best-configuration 10-plane synthetic run; record FER and honest f.

## 4. Route N — Nonbinary LDPC
Assets already present:
- V18-B2 structured DE harness: `nonbinary_v18_b2_structured_de.py`（q=16 folded real channel）
- V14/V17/V10 frozen DE/MC-DE modules
- Evidence:
  - q=16 folded, rate=0.60, f≈4.18 (`v18_b2_m2_r06_par_seed7_20260816`)
  - QSC equal-entropy control all-converged (`v18_b2_m2_qsc_ctrl_all_converged_20260816`)
- V19 LDPC DE screener.

Tasks:
- [ ] N1: keep q=16 folded plain boundary as the nonbinary baseline.
- [ ] N2: implement a v19 nonbinary DE screener with dc>13 / irregular ensembles (do not modify frozen V10/V14).
- [ ] N3: search irregular ensembles on q=16/64 folded real channel; target rate ladder {0.70,0.75,0.80,0.85,0.875}.
- [ ] N4: record best nonbinary f and FER; compare against Polar/LDPC routes.

## 5. Comparison and acceptance
- [ ] C1: one comparison table: route, N, rate, syndrome bits, public bits, f, FER, runtime, status.
- [ ] C2: only claims marked `diagnostic_only` / `legacy_drift_audit`; no fresh/promotion claim.
- [ ] C3: update `docs/three-way-ir-comparison-results-<date>.md`, `CURRENT_TASK.md`,
  `AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`.
- [ ] C4: local commits only; no push.

## 6. Priorities
1. Get one clean evidence JSON per route (P/L/N) on the same V17 per-plane synthetic channel.
2. If a route cannot reach f≤1.3, report its actual best f and FER, do not tune indefinitely.
3. Prefer simple code changes in `comparison_bench/`; never edit frozen baseline files.

## 7. Key references (already searched)
- Müller et al., Efficient information reconciliation for high-dimensional QKD, Quantum Inf. Process. 2024 — q-ary irregular DE pipeline, f≈1.078–1.14.
- Tal & Vardy, List decoding of polar codes, IEEE TIT 2015 — SCL.
- Liu et al., Improved polar SCL decoding by exploiting CRC error correction, IEEE Access 2019.
- Rowshan et al., Repetition-assisted decoding of polar codes, Electronics Letters 2019.
- Wu/Niu/Li, Polar codes: analysis and construction based on polar spectrum, arXiv 2019.
- Tal & Vardy construction: Ghayoori & Gulliver, Constructing polar codes using iterative bit-channel upgrading, arXiv 2013; Mahdavifar, Polar coding for non-stationary channels, IEEE TIT 2020.
- Jeong/Jung/Ha, Rate-compatible MET-LDPC ensembles for CV-QKD, npj Quantum Inf. 2022.
- Elkouss et al., Rate compatible protocol for information reconciliation: an application to QKD, ITW 2010.
