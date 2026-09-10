# Spec delta — V72P2D6 R1d Option C (eligible-only successor)

## SHALL (frozen)

- R1d arms SHALL be exactly `B0_D5_DV3_NATIVE`, `B1_D5_DV3_COMMON_LABELS`,
  `T1_PEG_DV3`. No dynamic additions; any other arm in R1d config SHALL raise
  before any build or decoder binding.
- R1d dispatch SHALL be allowed only for the 22 distinct frozen
  `(arm,n,layer,prefix_rows)` cells proven in `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv`
  (frozen eligible AND I1 pass). Any other cell SHALL fail closed before any
  decoder invocation (never a skipped observation).
- B0/B1 SHALL be controls and SHALL NOT enter the advancement pool;
  advancement pool SHALL be `{T1_PEG_DV3}`-only; scaling fallback SHALL be T1
  only (`fallback_M` SHALL be None in R1d).
- New R1d roots SHALL carry evidence schema `r1d-v2`: `structure_records.csv`
  header = frozen columns + `row_degree_min,rows_below_degree_2`, plus
  manifest/summary markers `structure_schema=r1d-v2`,
  `eligible_semantics=frozen-AND-I1`. Historical A2 roots SHALL remain
  byte-identical with the old schema; `--verify` SHALL read both.
- Crash/nonfinite precedence SHALL follow `execution_block_terminal`
  (degree `ValueError` → `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`, else
  `D6_GRAPH_ATTEMPTED_CELL_INVALID`; `call_idx<0` excluded), overriding
  recovery/no-recovery labels in R1d.
- Stored vs recomputed terminals SHALL be reported with the agreement flag;
  recomputed SHALL govern. R1d `--verify` SHALL recompute every group
  (zero skip) and SHALL require stored v2 values to match recomputation.
- R1d SHALL run from a fresh `workspace/d6_graph_mother_r1d_<uuid>/` root,
  refuse overwrite, and refuse the historical A2 / VOID roots by name.
  R1d SHALL NOT read A2/VOID/formal roots as scientific input.
- Budgets SHALL be ≤2500 total setup+scientific calls, ≤12 h wall,
  ≤120 s/call watchdog, aggregate RSS <2 GiB, no retry; workers requested 18
  with reviewed RSS-only downgrade 18→14→12→8; chunk ≥5400 s blocks dispatch.

## SHALL NOT

- No SC/M knob lift; no SC/accumulator/T2 dispatch from R1d config.
- No R1c-A2 decoder call or root reuse as successor evidence.
- No tuning, no power/success-rate thresholds beyond the registered ones.
- No authorization grant by implementation, tests, or reviews.
