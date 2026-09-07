# OpenSpec Project Context

## Project: HD-QKD_Polar_Comparison

### Summary
Evaluate and compare Information Reconciliation (IR) methods for high-dimensional Quantum Key Distribution (QKD). The original Polar pipeline is a frozen baseline; `comparison_bench/` adds a non-invasive comparison layer.

### Strict First Principle

The project's first principle is to discover, implement, and experimentally
validate scientifically reasonable high-performance error-correction/IR
algorithms for the actual HD-QKD data. Benchmarking, reproducibility, lifecycle
gates, and evidence exist to make those algorithm measurements trustworthy;
they must not become the primary product.

Algorithmic progress in correction success/FER, leakage efficiency,
throughput/runtime, resource cost, and net secret-key yield outranks package
maturity, generalized infrastructure, defensive hardening, exhaustive audit,
and verifier sophistication. Non-scientific engineering findings are
non-blocking unless they can concretely change the numerical result,
scientific attribution, execution authorization, or existing data.

### Tech Stack
- **Language**: Python 3
- **Core deps**: `numpy`, `pandas`, `numba`, `tqdm`
- **Optional deps**: `pyyaml`, `pyarrow`, `pytest`
- **Scientific domain**: QKD post-processing, IR, error correction codes

### Architecture
- **Frozen baseline**: `src/`, `experiments/`, `tools/` (original Polar pipeline — do not modify)
- **Comparison layer**: `comparison_bench/` (outer wrapper, reads Polar outputs, adds new baselines)
- **Data**: raw data external to repo; processed outputs under `results/` (read-only) and `comparison_bench/outputs_comparison/` (append-only)

### Key Constraints
- Original Polar code is frozen; only `comparison_bench/` is mutable
- Schema stability: CSV columns, config keys, CLI args, function signatures must not silently change (see AGENT_PROJECT_MEMORY.md §6)
- Scientific semantics: `beta_eff_empirical` must be derived, status values must be preserved, leakage comparisons require consistent decomposition
- Path discipline: prefer WSL/POSIX paths; legacy Windows paths are provenance only

### Known Risks
- Compiled Polar binaries (`src/reconciliation/cpp_polar/`) may be Windows-only
- Parquet output may fall back to pickle
- Long-running commands must not be run casually

### Roadmap (deliverable-organized; read-only review 2026-09-06)

Organized by six deliverables (D1–D6), not by version number. No
completion-percentage claim is made.

Canonical ownership revision: `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md`.
All new NB-LDPC implementation, model preparation, real-input integration,
scanning, reporting, and evidence live in this Comparison repository. The
sibling Release checkout is read-only reference material until a stable
Comparison output contract and accepted real single-point result justify a
separately authorized thin consumer adapter. No NB-LDPC algorithm or scanner
is to be developed in Release.

#### Terminology (frozen)
- `d`: bins per physical frame (Release `dimension`; `N` when the encoding
  dimension is meant).
- `tau`: bin width (`bin_width_ps`); physical frame duration is `d*tau`.
- `n_IR`: symbols per IR block. D5 widths 64/256 are IR block lengths, not
  physical dimension; D5 progress does not complete a Release dimension scan.

#### Current position (frozen facts, read-only)
- Sibling Release chain (BINARY POLAR MAINLINE; boundary per AGENTS.md §0 —
  no work advanced there from this repo): ttbin → channel/delay/pairing/
  framing → symbols → Polar correction → per-block verification and leakage
  → grid summary and point selection. V3 result: 4 losses × 121 points =
  484 rows; grid `dimension` 4–4096 (11 steps) × `bin_width_ps` 20–200 ps
  (11 steps); marked `public_ec_only_not_secure` — mature EC plus public-cost
  loop, not a measurement-driven secure-key loop. Provenance citations only
  (not defaults): `D:/Code/HD-QKD_Polar_Release/results/paper_grade_v3/reconciled_stage2_20260812_final_v3/rebuild_summary.txt`,
  `D:/Code/HD-QKD_Polar_Release/docs/CURRENT_MAINLINE.md:3`.
- NB-LDPC: canonical `counts` and historical H1 builder are in current source
  (prior counts/`H1-zero` findings superseded):
  `D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py:298`,
  `D:/Code/HD-QKD_Polar_Comparison/scripts/v72p2d3_gf32_contrast.py:411`.
  D4R2 nested CV on current CAL: CE 3.814742 / 3.347605 per layer, 7.162347
  total, vs old ~1.055 bit/symbol syndrome (rate mismatch quantified):
  `D:/Code/HD-QKD_Polar_Comparison/docs/research_cycles/V72P2D4-CAL-RATE/RESULT_SUMMARY_R2.md:17`.
  D5 new mother: 8 prefixes structure-pass; G0 recovery tiny math check 8/8:
  `D:/Code/HD-QKD_Polar_Comparison/docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/STRUCTURE_RESULT_SUMMARY.md:3`,
  `D:/Code/HD-QKD_Polar_Comparison/workspace/v72p2d5_g0_recovery/20260906_r1/results.json:2`.
  Order frozen STRUCTURE → G0 → P0 → G1 → G2; P0/G1/G2 unexecuted.
  Per-f mother-prefix candidates exist in workspace but establish no rate-point
  correction performance.
- Regime shift: per D4 model budget, L1 goes from historical 16 rows to ~782
  rows at start — a different finite-length rate regime, not a file swap. CE
  is indicative, not an information-theoretic lower bound.
- Blocked input: D5 CLI passes only `authorized=True` while P0/G1/G2 need
  `counts_ab` and `p_b`; missing input stops `prepare_model_f_prior`
  (`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`):
  `D:/Code/HD-QKD_Polar_Comparison/scripts/v72p2d5_gf32_rate_mother.py:86`,
  `D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py:2138`.
- V63 "shell integration" loads fixed V25/V54 priors and fixed rate; its PA
  function returns placeholder `key_length_proxy = -total_disclosure` (no net
  / secure-key computation):
  `D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py:171`,
  `D:/Code/HD-QKD_Polar_Comparison/comparison_bench/pipeline/shell_integration.py:35`.
  V72 scope (proposal/design of `v72p2d5-p0-g1-g2-production-path`) unchanged.

#### Distance to target
| Segment | Distance |
|---|---|
| Real ttbin, measurement params, symbol extraction | Near — reuse Release front half-chain and symbol boundary |
| Effective NB-LDPC single point in new domain | Algorithm risk remains — matched prior, per-layer rates, full-block-length performance |
| NB per-block public cost and verification reporting | Medium interface work — unify real decode results, accept/reject, leakage decomposition |
| `tau` scan at fixed `d` | After single-point loop closes; remodel per point; account retention, leakage, runtime |
| `d`×`tau` scan | Further generalization — layer split, finite field, matrices, per-point calibration |
| Secure-model best point | Parallel measurement/model gap — protocol observables, finite-length params, security qualification |

#### Deliverables and acceptance
- **D1 — D5 input-to-result loop.** Connect real-CAL model input to CLI; then
  proceed P0/G1/G2 in frozen order. Accept: real input → per-rate real matrix
  prefixes → real kernel → real results. Tiny G0 and structure-pass do not
  substitute for performance results.
- **D2 — New-domain real single-point NB-IR result.** Fix `d,tau,n_IR`;
  freeze CAL design; verify on independent data. Report exact recovery,
  protocol accepts, error accepts, per-block real public bits, runtime. After
  small-block success, add target-block-length verification.
- **D3 — Comparison-owned report interface with honest net.** In Comparison,
  reuse the established symbol/intermediate-data boundary and attach NB after
  it. Release is read-only reference; no NB implementation is added there.
  Existing leakage
  interface (provenance citation only, not a default:
  `D:/Code/HD-QKD_Polar_Release/security_tool/common/leakage.py:23`) already
  takes syndrome/verification/other-disclosure/success-flag/retained-symbols.
  Preparable in parallel with algorithm experiments; fake decode products must
  not be claimed as a real loop.
- **D4 — Fixed-`d` `tau` scan, then `d`×`tau`.** First verify the scanner
  actually changes data and prior per point; account retention, real leakage,
  runtime. Then add one new dimension (e.g. `d=256`) and verify unequal layer
  split. Do not expand dimension, code length, rate, and graph at once.
- **D5 — Security measurement and model qualification (parallel line).**
  Release `local_measured` still blocks on missing observables; math engine and
  paper-assisted results are not local security results (provenance citation
  only: `D:/Code/HD-QKD_Polar_Release/security_tool/common/facade.py:218`).
  After fixing the real protocol, add its conjugate-basis measurements,
  calibration, uncertainties, epsilon budget. NB neither waits for all
  protocols nor substitutes one visibility for full security conditions.
- **D6 — Best point plus holdout.** Stage 1 selects the `reconciled_net` best
  point; the secure-key-rate best point only after security conditions hold.
  Optimize over real accept rate, public cost, acquisition time, compute cost —
  not `f` alone or single-block success alone. Scan selects; separate data
  confirms.

#### Nearest milestone
> In Comparison, one real ttbin session at fixed dimension producing a `tau`
> scan table backed by real NB-LDPC decoding — the first end-to-end milestone
> toward the full `d`×`tau` secure-optimization chain. Release remains
> read-only reference; advance the security-measurement interface in parallel,
> then widen dimension.

#### Review note
Per current AGENTS.md: keep reviews that affect scientific conclusions (real
inputs, math direction, matrices and rates, leakage, budgets, stop rules,
result interpretation); doc-submit/SHA-equality/unrelated-dirty-file ceremony
must not block this route. Pre-EXECUTE / Pre-RESULT gates still apply where
their scope requires.
