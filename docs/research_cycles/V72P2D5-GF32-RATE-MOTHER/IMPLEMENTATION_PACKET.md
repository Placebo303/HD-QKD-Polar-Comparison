# V72P2D5-GF32-RATE-MOTHER Implementation Packet (frozen constraints, no implementation)

- cycle_id: V72P2D5-GF32-RATE-MOTHER
- packet_status: IMPLEMENTATION_PACKET_FROZEN
- note: This file records constraints only. It implements nothing, executes nothing,
  constructs no mother, runs no rank audit, calls no decoder, reads no CAL/VAL,
  creates no structure/G0/G1/G2 output, and grants no implementation/synthetic execution.
- D5 five plan files are read-only referenced, zero modification.

## 1. Allowed future implementation files (exact closed set)

Future implementation submission may touch only:

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
2. `scripts/v72p2d5_gf32_rate_mother.py`
3. `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
4. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/IMPLEMENTATION_REVIEW.md`
5. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`

Future stage outputs under `workspace/v72p2d5_*/<run_id>/` are execution artifacts
and do not belong to the implementation submission.

## 2. Forbidden future modification (exact closed set)

Future implementation shall not modify:

- D5 accepted five files under `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/`
  (`proposal.md`, `design.md`, `specs/spec.md`, `tasks.md`, `PLAN_FREEZE.md`)
- V31 / V35 / V54 historical implementations
- D3 / D4 code and results
- `src/`, `experiments/`, `tools/`, `results/`
- `AGENT_PROJECT_MEMORY.md`
- `docs/decision-log.md`
- any VAL / real output directories

If code and plan disagree, state is `PLAN_REVISE_REQUIRED`. The plan shall not be
edited to suit code. Stop and return to planner / OpenSpec on a new SHA.

Frozen values (seed / threshold / row count / model / gate) shall not change.
No hash / checksum / tag fields shall be added.

## 3. Module responsibilities A-F (declaration only)

### A. Prior adapter

- Canonical `counts[Alice,Bob]`, `P_F.shape=(Alice,Bob)`, `axis0=Alice, axis1=Bob`.
- Single-coefficient smoothing `lambda=137.3823795883264` on counts column direction,
  then normalize along `axis=0` to `P_F(A|B)`.
- Derive `P1(U1|B)` by reshape `(32,32,1024)` sum over U2 and norm over U1;
  derive `P2` fixed `(u1,b)` norm over `u2`.
- Production L2 prior is `q@P` where `q=softmax(L1 final_beliefs)`; oracle L2 is diagnostic only.
- Dual floor: audit/CE `1e-300`, decoder path `1e-15`; re-normalize after floor;
  zero-mass `(U1,B)` slice falls back to uniform `1/32`, no sample deletion.
- V54 / V35 kernels are reused verbatim; no modification to historical kernels.

### B. Mother construction

- Baseline only: V31 QC-cyclic-projective `build_layer(m,n=1024,*,family,field,require_full_rank)`,
  family passed explicitly.
- Graph seeds: L1 `2026090501`, L2 `2026090502`. `N=1024`, `M_max=1000` per layer.
- Single `1000x1024` candidate per layer; disclosure is row prefix `H[:k]`.
- No second graph family, no seed search, no per-`k` independent matrix posing as nested.

### C. Row ordering (pre-registered, at most once per layer, only if natural prefix FAILs)

- Input: complete mother; output: one row permutation; no row/coefficient change.
- Priority: new-coverage variable count -> rank increment -> component connection ->
  original-index deterministic tie-break.
- Shall not read decoder results / data / synthetic exact.
- At most once per layer (L1 once, L2 once); subsequent prefixes come from the same ordered mother.

### D. Prefix audit (13 items reported, minimum PASS gate frozen)

- For every frozen `k` (L1 `{782,821,860,938}`, L2 `{686,720,755,823}`) report 13 items:
  rank, zero_rows, zero_columns, column active-degree min/median/max, degree-1 count,
  degree-2 count, connected-component count, largest-component fraction, isolated count,
  check row-degree histogram, 4-cycle count, duplicate/projective-equivalent column count,
  GF32 coefficient nonzero.
- Minimum PASS explicit eight checks (exact enumeration of the frozen D5 gate, no relaxation,
  no tightening): `rank==rows`, `zero_rows==0`, `zero_columns==0`, `isolated==0`,
  `components==1`, `largest==1.0`, `duplicate==0`, coefficient nonzero.
- Full mother PASS but any prefix FAIL: only module C once; still FAIL means
  `V31_PREFIX_FAMILY_UNSUITABLE`, stop and return to planner, no decoder entry.

### E. Matched generator

- `B~P(B)` CAL-derived marginal only; `A~P_F(.|B)` with frozen `lambda*` truth table.
- `A=32*U1+U2` mapping frozen; no AWGN / BSC / QSC substitution; no VAL.
- Shall not save per-symbol arrays; passing the probability table is allowed.
- Generator shall not self-read CAL/VAL files; tables are injected by the authorized caller.

### F. G0/G1/G2 functions (implementable but not executable with a real decoder)

- All decoder calls go through `decode_fn`, default `None`.
- `decode_fn=None` shall refuse; fallback to any production decoder is banned.
- Production v35 decoder may only be injected by a later explicitly authorized CLI path,
  never as a default and never during the implementation stage.
- Implementation stage runs only fake/injected decoders.

## 4. CLI phases (explicit phase only)

- Required: `--phase structure | g0 | p0-cost | g1 | g2`.
- Default performs no execution; missing `--phase` prints help and exits.
- Each phase requires independent authorization.
- Banned: `--phase all`, autochain, retry, seed change, threshold tuning,
  `--execute-real`, any VAL path, `run_01`.
- Implementation stage: fake/injected decoder only.

## 5. Tests

### T0 scope (no decoder call)

- probability-axis / transpose-counterexample, normalization, P1/P2 derivation,
  `q@P` hand calculation, one-hot mapping, floor behavior, row-count recomputation,
  seed/prefix constants, small-graph metrics, rank / zero / component / 4-cycle checks,
  ordering determinism / row-preservation / no-search, generator determinism, VAL ban.

### T1 scope (fake decoder only)

- `None` refusal, call counting, stage isolation, failure blocks entry,
  projection blocked, field checks, no raw / hash / tag / production outputs.

### T2 deferred

- Full mother plus prefix audit.

### T3 deferred

- G0 real decoder plus P0/G1/G2.

Review requires T0/T1 only. T2/T3 are deferred and grant no execution.

## 6. Output roots (future execution artifacts, not implementation submission)

- Roots: `workspace/v72p2d5_structure/<run_id>/`, `workspace/v72p2d5_g0/<run_id>/`,
  `workspace/v72p2d5_p0_cost/<run_id>/`, `workspace/v72p2d5_g1/<run_id>/`,
  `workspace/v72p2d5_g2/<run_id>/`.
- Each stage uses a fresh directory; overwriting is banned.
- Each stage directory contains exactly four scalar files:
  `results.json`, `table.csv`, `report.md`, `execution_summary.json`.
- Banned from storage: complete mother, raw counts, prior tables, syndromes,
  BP messages, any hash.
- Mother is rebuilt in memory from seed; it is not persisted.

## 7. Review acceptance I1-I14 (frozen checklist names, no new thresholds)

- I1: prior axis and mapping contract holds.
- I2: `lambda*` smoothing placement holds.
- I3: dual-floor and uniform-fallback semantics hold.
- I4: row-count table recomputation holds.
- I5: mother parameters and graph seeds hold.
- I6: prefix 13-item report plus minimum PASS gate holds.
- I7: row-ordering determinism and no-search holds.
- I8: matched-generator channel and injection-only holds.
- I9: `decode_fn` default None and no-fallback holds.
- I10: CLI explicit-phase and banned-flag holds.
- I11: T0 passes without decoder.
- I12: T1 passes with fake decoder only.
- I13: output roots / four-file / banned-artifact rule holds.
- I14: plan-unchanged / gate-separation / no-auto-authorization holds.

## 8. Staged gates A-E (no auto-advance)

- Gate A: IMPLEMENTATION_REVIEW (T0/T1 + I1-I14).
- Gate B: STRUCTURE (M0 prefix gate).
- Gate C: G0 (tiny math gate).
- Gate D: P0_G1 (cost preflight then G1 trend gate).
- Gate E: G2 (sole grading experiment).

Passing any gate does not automatically authorize the next gate.
G0/G1/G2 are authorized separately. No `n=1024` real, no formal execution,
no scientific promotion is granted by this packet.
