# Change: formal-nonbinary-ldpc-v32-operating-point-consistency-audit

Status: P1 SPECIFICATION FREEZE — planner-authored. Read-only except for creating the four OpenSpec files of this change. No production code, no analysis runs, no report generation, no commit/push in this phase.

## Positioning (authoritative)

This change is **audit-only**: strictly read-only analysis and report outputs. It is NOT a new diagnostic run, NOT a DE rerun, NOT a decoder run, and NOT a corrected-B1 (that is a separate successor change frozen only after this audit's three-way branch is known).

Motivation: `docs/nbldpc-v32-main-review-verdict-20260822.md` records the authoritative V32 final review verdict **EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE**: the 247-record run evidence is accepted in full, but B1's key premise — a matched empirical-channel synthetic control — did not hold (B1 generator `synth_channel_sample`, `run_nonbinary_v32_finite_de_bridge.py` L555–564: uniform alice + Bernoulli(raw_ser) + delta ~ Uniform[1,1023] mod 1024; decoder posteriors derive from the V25 empirical joint; the V26 DE sampler draws `(A,B)` directly from that joint per `nonbinary_v26_channel.py` L10–13). The frozen truth table mechanically mapped `finite_graph_decoder_mismatch`; main review rejected that attribution as scientific root cause. Successor decisions are deferred until this audit converts the 240 B1–B4 records plus existing V25/V26/V31 artifacts into decidable operating-point consistency evidence and emits a three-way branch decision.

## Goal (verbatim, frozen — authoritative here; design/tasks/spec reference this section)

> 把 V32 的 240 条 B1–B4 记录与既有 V25/V26/V31 工件转化为可判定的 operating-point 一致性证据，并输出三向分叉决策表。

## Deliverables D0–D3 (frozen definitions — identical in all four docs)

- **D0 — 全量失败签名（只读）**: extract all 240 decode records (B1–B4) plus B0/B5 controls from V32 `per_block.jsonl`; per record: initial/final L1/L2 errors, decoder statuses (`terminal_decoder_status`, `l1_decoder_status_verbatim`), iterations, unsatisfied checks, NLL, entropy, truth rank, anomaly flag; aggregate distributions by arm×source (mean/median/range/full histogram with declared bins). Frozen verification predicates: (i) B1 全域 active divergence (final > initial); (ii) B2 `l2_errors_final=1024` is a not-run sentinel (`terminal_decoder_status="not_run"`) and MUST NOT enter error-trajectory analysis; (iii) B3/B4 improve-but-no-syndrome (final < initial but syndrome never true).
- **D1 — B1 generator/posterior 一致性（只读）**: per source compare analytic Q_B1 vs P_V25. Q_B1(b|a) = (1−raw_ser)·δ_{b=a} + raw_ser·Uniform{b≠a mod 1024}, raw_ser = frozen V25 per-source values from `channel_summary.json`. Compute: empirical cross-entropy H(Q,P); Q-sampled empirical NLL distribution under P_V25 posteriors (analytic or large-sample MC — MC must fix seed and state sample size before execution); zero/support-miss fraction both directions incl. expected frequency of Q samples hitting P-zero cells; delta distribution comparison (Q uniform delta vs actual P_V25 delta histogram incl. ±1 direction mass); conditional divergence of P(U1|B) and P(U2|B,U1) between the two laws; dual expected-NLL comparison (Q-generated pairs under V25 posterior vs V25 empirical joint under its own posterior, the latter ≈ layer conditional entropies). Mismatch thresholds SHALL be pre-registered in the audit manifest BEFORE D1 computation, with a stated derivation basis anchored to log2(1024)=10 bits/symbol.
- **D2 — 信息论可行性 vs 实际码率（只读）**: per source compute H(U1|B), H(U2|B,U1), H(A|B) from `channel_counts.npz` via the F03/A02 L1/L2 layer maps; compare against L1/L2/total syndrome symbols/bits taken verbatim from V31 artifacts (RUN_MANIFEST / matrix audits / m1 registry — concrete fields cited in design); n=1024 finite-length margin via ONE declared method frozen before execution (simple gap reporting; no undeclared invented statistics); output layer-specific AND total feasibility conclusions; emit the three-way branch mapping below into `final_branch_decision.json`.
- **D3 — 既有 DE 证据只读检查（不重跑 DE）**: read-only inspection of V26 run_02 artifacts + code: cite the DE sampler location drawing `(A,B)` from P(A,B) (`nonbinary_v26_channel.py` L10–13); confirm B1 did not replicate that channel (cite harness L555–564); extract where the V26 pass occurred (layer/source/operating point, `gate.json` / `RUN_MANIFEST.json` / m0+m1 reports / screen+confirmation results) and whether V26 rate/entropy parameters match the V32 QC packet numerically; if existing evidence cannot answer the exact operating-point question, output `new_DE_change_required=true` plus the minimal DE question list — but NO DE is executed inside this change.

### Three-Way Branch Mapping (frozen — final output schema)

| Branch | Condition | Consequence |
|---|---|---|
| A | total infeasible | LDPC 与 Polar 同速率方案均暂停，先重审泄漏预算/运行点 |
| B | total feasible 且 L2 allocation infeasible | 当前 multilevel allocation 失败，joint/重新分配的 NB-Polar feasibility 价值上升，不值得先换 QC 图 |
| C | layer 与 total 均可行 | finite graph/decoder 值得一次 corrected matched control（后续单独变更，不在本审计内执行） |

## Non-Goals

1. No DE rerun, no new DE sampling, no decoder invocation, no `.ttbin` access.
2. No corrected-B1 implementation; no new diagnostic arms; no n=2048 anything.
3. No modification of any input artifact (V32 run_01 is read-only canonical evidence for this audit).
4. No edits to `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`; no V32 archive actions; no qualification/promotion wording anywhere in audit artifacts.
5. No start of V33, NB-Polar work, or corrected-B1 — they are successor changes gated on this audit's branch.
6. No overwrite of any existing output under `results/**` or `comparison_bench/outputs_comparison/**` outside the single new audit run root.

## Frozen Input Bindings (identical in all four audit docs)

All inputs resolve through repository-relative paths; every binding opened read-only:

| # | Binding | Path / Identifier |
|---|---|---|
| 1 | V32 run_01 evidence (247 records) | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/` (`per_block.jsonl` 247 lines schema `nbldpc_v32_bridge_block_result_v1`; `RUN_MANIFEST.json`; `summary_B0..B5.json`; `candidate_terminal.json`; `terminal_reconstruction.json`) |
| 2 | V25 run_04 empirical channel | `.../nbldpc_v25_20260818/run_04/channel_counts.npz` (keys `{sid}_N_ab_train_N_ab_train` — verbatim on-disk key with duplicated suffix), `channel_summary.json` (frozen raw_ser: 1M `0.239779296875`, 1p5M `0.2544695292735815`, 2M `0.2557409550754458`; pm1_mass ±1 direction), `split_manifest.json` |
| 3 | V26 run_02 DE artifacts | `.../nbldpc_v26_20260818/run_02/` (`RUN_MANIFEST.json`, `gate.json` status `pass_target_f13` best_passing_f A01=1.6/A02=1.3, `m0_report.json`, `m1_report.json`, `screen_results.json`, `confirmation_results.json`) |
| 4 | V31 run_01 packet/allocation/leakage | `.../nbldpc_v31_20260820/run_01/RUN_MANIFEST.json` (`configs["1024"].sources[].{H.L1,H.L2,m1,m2,m_total,leak_total_bits,f_total}`), `matrix_audits.json` (`packets[]` audits L1 shape [16,1024], `m2_by_source`), `m1_registry.json` (`registered_calls[].{layer,rate,H_bits_per_symbol,m1,m2}`) |
| 5 | V32 harness code fact | `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py` `synth_channel_sample` L555–564 |
| 6 | V26 channel sampler code fact | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py` sampling semantics L10–13 |
| 7 | Three frozen source IDs | `type2_1M_20260121_184040` (1M), `type2_1p5M_20260121_183806` (1p5M), `type2_2M_20260121_183657` (2M) |

## Forbidden (must appear consistently in all four audit docs)

- DE 重跑；任何新 DE 采样；decoder 调用；读取 `.ttbin`。
- Canonical/frozen 写入：V32 `run_01` 只读保护；V31/V30R/V28R/V26/V25 根目录；OpenSpec archives；`src/**`, `experiments/**`, `tools/**`, `results/**`。
- Anything `n=2048`.
- 修改 `docs/decision-log.md`、`AGENT_PROJECT_MEMORY.md`；V32 归档动作；qualification/promotion 措辞。
- 启动 V33、NB-Polar、corrected-B1（审计后继变更）。
- Overwriting any existing output root other than the single new audit run root; automatic `run_02`.

## Output Root (unique)

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/`

If this path already exists when the formal audit starts → **STOP: implementation/output collision**. Overwriting and automatic `run_02` creation are both forbidden.

## Impact Scope

- `openspec/changes/formal-nonbinary-ldpc-v32-operating-point-consistency-audit/**` (this change, new)
- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit.py` (new single CLI, subcommands d0/d1/d2/d3/all, `--runner` injection mode for test fakes; after freeze)
- `comparison_bench/tests/test_nonbinary_v32_operating_point_audit.py` (new tests, after freeze)
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/*` (audit reports only)
- `workspace/<audit>/<uuid>/*` (fresh test roots)
- `workspace/nbldpc_v32_operating_point_audit/OPERATOR_HANDOFF.md` (candidate-only handoff)

No impact on `src/**`, `experiments/**`, `tools/**`, `results/**`, canonical V32/V31/V30R/V28R/V26/V25 roots, or any archived OpenSpec change.
