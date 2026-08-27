# Spec Delta: formal-ir-v51-lane-c-label-nbace

## ADDED Requirements

### R-V51-01: Frozen Lane C Base

The system SHALL freeze Lane C base as `n=1024, m2=184/190/192 per source (1M/1p5M/2M), GF32 poly37, support/position_permutations/m2/leakage 1064/1094/1104, decoder 90/1.0 early-stop, H1 16×1024 rank16` and SHALL NOT modify support, permutations, row/col degrees, or decoder when producing new labels.

### R-V51-02: Deterministic NB-ACE Label Optimizer (decoder-free, single-run)

The system SHALL provide a deterministic NB-ACE label optimizer that maps each Lane C binary support to a new GF32 label matrix `H_new` with identical support. The optimizer SHALL: (a) enumerate support cycles 4/6/8 via `enumerate_canonical_simple_cycles`; (b) classify `is_deg` via `classify_cycle_algebraic_degeneracy`; (c) compute `ACE(C)= Σ(row_deg-2)` and `NB-ACE(C)= ACE-100` if degenerate else `ACE`; (d) optimize lexicographic `key=(deg6, -min_nbace6, deg8, -min_nbace8, cand)` prioritizing 6-cycles then 8-cycles; (e) greedily scan canonical edge order `1..31` up to 2 sweeps, zero seed search, deterministic tie-break smallest `cand`. The optimizer SHALL be decoder-free and SHALL run exactly once, not tuned by decoder outcomes.

### R-V51-03: Decoder-Free Label Spectrum Delta

The system SHALL emit for each source a decoder-free spectrum delta `original vs new` comprising: `support_exact_equal (=True)`, `rank==m2` both, `support_cycles_4/6/8` unchanged, `degenerate_4/6/8`, `min_nbace6/8`, `min_deg_ace6/8`, `generalized_girth`, `nondeg_frac6/8`. The delta SHALL be persisted as `v51_label_spectrum.json`.

### R-V51-04: Label Improvement Gate (blocker)

The system SHALL compute `label_improved = ∃source: deg6_new < deg6_old ∨ min_nbace6_new > min_nbace6_old`. If `label_improved==false`, the system SHALL NOT enter the paired decoder experiment and SHALL report terminal `V51_LABEL_NO_IMPROVEMENT` as blocker.

### R-V51-05: Conditional Paired Held-Out Experiment

If `label_improved==true` and execution is authorized, the system SHALL run exactly `45` decoder calls over `15` new unused held-out blocks (`392001..392005 / 392101..392105 / 392201..392205`, 4 frames=1024 pairs each, `deterministic_four_consecutive_frames_heldout_unused_new`, zero overlap with `FORBIDDEN 156` and V48/V50 `frame_ids` per source). Per block: one shared `L1` (TRAIN prior) + two `L2` (`old` vs `new`) with same `bob`/`P_i(U2)`, only `H_L2` labels differ. The system SHALL enforce `planned/started/completed = 45/15/30` and SHALL NOT add a TRAIN+VAL arm.

### R-V51-06: Paired Primary and Diagnostics

The system SHALL use `exact_full = exact_u1 && exact_l2` (oracle, not tag) as paired primary. The system SHALL report paired contingency `[[a,b],[c,d]]`, discordance `b+c`, gain `c-b`, per-block `errors_final/iterations/runtime`, and four-way `exact/detected/decoder_non_syndrome/undetected` with `G3' undetected==0`. Leakage `1064/1094/1104` (L2-only tag `≈2^-64`) SHALL remain constant.

### R-V51-07: Terminal States

The system SHALL produce exactly one terminal: `V51_EVIDENCE_INVALID` (integrity/guard fail) prioritized, else `V51_LABEL_NO_IMPROVEMENT` if `label_improved==false`, else `V51_PAIRED_COMPLETE` (descriptive, no promotion).

## MODIFIED Requirements

- No existing R1–R7 modified; this delta is additive and does not change formal-ir-methods R1–R7.

## REMOVED Requirements

- None.
