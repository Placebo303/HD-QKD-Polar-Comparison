# V72P2D1 delta specification

Base: HEAD=ba0df2d3bea4147574e0b8224480f45c93505178 == live remote, branch formal-ir-v72p1-addendum-clean.

## ADDED Requirements

### Requirement: fixed A/B parity layout
The runner SHALL set A to the frozen 9036x10240 nnz49620 mother (check{4:1,5:4594,6:4441},
deg2 9035) and B to col_map[1204:10239]=1204+permutation(9035) with rng=default_rng(20260902,
domain-separated diagnostic-only seed, never reused from V72P1/V72P2/CAL),
cols 0..1203 and 10239 fixed, indptr copied, indices mapped, edge order kept, per-arm CSR.
Syndrome SHALL be fixed as: b is the 10240 fixed Alice vector, s_A=H_A·b (mod2), s_B=H_B·b (mod2);
each arm SHALL see only its own prefix + Bob prior. D1/M6 predicate SHALL be
recompute(H_arm,b)==observed_arm. M1-M7 SHALL pass with A1196/1194 B1196/1194 recomputed
(generic check-pair four-cycle/collision definition shared by fake and real paths,
column-permutation graph-isomorphic so cycle spectrum invariant;
reported, never hand-filled; B2 recount corrected old 8452/8170). The diagnostic hypothesis SHALL test only whether permutation moves
ladder outcome / D5-D7 layout-sensitive dynamics, SHALL NOT presuppose B cycle improvement.

#### Scenario: permuted info column
Given any col in 0..1203 or 10239 differs between A and B, verification SHALL FAIL and block execution.

### Requirement: shared CAL-only prior
The runner SHALL fit hierarchical_P/select_lambda once on CAL702..1725 of
20260123_1M_600k_0dB (v71_data_registry.json) and share it across A/B for diagnostic
VAL1726-1729 (non-fresh). Prior SHALL use natural_log, CE SHALL use log2.
Expected lambda 221.22162910704503 (exact equality) and CE 7.135005172802673 (tolerance 1e-12)
are regression refs; mismatch SHALL be reported, never hand-filled.
On CAL bad/INVALID, both arms SHALL be not_attempted (cal_failed) with zero decoder calls
(inherits V72P2 Bad-CAL-stops-without-decoder).

#### Scenario: prior mismatch
Given measured lambda/CE differs from expected, the run SHALL record actuals and trigger
the A-gate-B stop instead of overwriting expected values.

### Requirement: frozen decoder and ladder
The runner SHALL reuse V72P1 run_decoder unchanged (clip20 tol1e-6 float64,
10/ckpt 720/arm, 72 checkpoints, A-then-B, zero c2v per arm, in-arm carry only,
iterations=len(residuals)). Only finite+syndrome+tag current candidate SHALL accept
(tag64bit); oracle SHALL be posthoc with undetected isolated.

#### Scenario: zero remaining budget
Given 0 remaining iterations at a checkpoint, the runner SHALL send/call nothing and
retain published counters.

### Requirement: budget and A-gate-B
Each arm SHALL have 600s soft deadline and the whole command 1800s, checked before
each publication (one checkpoint may overrun). On A numeric/decoder error, timeout, or
baseline-reproduction mismatch (72/334/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71;
lambda exact, CE 1e-12), B SHALL be not_attempted (gate_stopped_by_A).
A second invocation with the same --out SHALL always refuse (no resume/fill of B; not a rerun).

### Requirement: scalar-only D1-D8
The runner SHALL record only wrapper scalars: D1 syndrome recompute with predicate
recompute(H_arm,b)==observed_arm (match_flag + mismatch_rows), D2/D3 vsBob
symbol/bit, D4 APP finite/max/mean, D5 c2v finite/max/residual/iters, D6 f2b/sum flips,
D7 deg2-grouped errors/means, D8 Alice errors/oracle_exact/undetected. Full prior,
matrices, per-bit/per-edge arrays SHALL NOT be persisted.

### Requirement: additive four-file output
Output root comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/ SHALL be
refused if existing (zero files) and SHALL finally contain exactly manifest.json, results.json,
table.csv, report.md in every terminal state (success / gate-stopped / cal_failed / m_failed /
real-exception; unrun arms not_attempted + D null). Running candidates SHALL live only in
workspace/v72p2d1_<uuid>/ temp and SHALL NOT count toward the final four; temp SHALL be
removed after the terminal four land (kept only when the terminal write itself fails).
There SHALL be a single terminal writer (write_terminal_outputs; _write_four is an alias)
with unified report content (incl. bit/sym). Fake injection with missing decoder_fn SHALL
raise and SHALL NOT fall back to the real decoder. CLI SHALL be exactly --registry v71_data_registry.json
--session 20260123_1M_600k_0dB --out <above> --arm-budget-s 600 --global-budget-s 1800.
Docs SHALL be exactly docs/research_cycles/V72P2D1-PARITY/EXECUTION_PACKET.md,
REVIEW_VERDICT.md, RESULT_SUMMARY.md. Tests SHALL use workspace独立temp with fake runner only.

#### Scenario: existing output dir
Given the output dir exists, the runner SHALL refuse without overwrite.

### Requirement: S8 baseline and S9 regression boundary
A SHALL reproduce V72P2 block0 (72ckpt/334iter/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71);
else B stops. The known V72P1 1-second timing failure SHALL remain FAIL with threshold
unchanged; all other regressions SHALL pass, otherwise block.
