# Spec Delta: formal-ir-v51-lane-c-label-nbace

## ADDED Requirements

### R-V51-01: Frozen Lane C Base

The system SHALL freeze Lane C base as `n=1024, m2=184/190/192 per source (1M/1p5M/2M), GF32 poly37, support/position_permutations/m2/leakage 1064/1094/1104, decoder 90/1.0 early-stop, H1 16×1024 rank16` and SHALL NOT modify support, permutations, row/col degrees, or decoder when producing new labels.

### R-V51-02: Deterministic Label Optimizer (decoder-free, single-run, deg4-first)

The system SHALL provide a deterministic label optimizer that maps each Lane C binary support to a new GF32 label matrix `H_new` with identical support. The optimizer SHALL: (a) enumerate support cycles 4/6/8 via `enumerate_canonical_simple_cycles` and reuse `edge_to_cycle_ids`; (b) classify `is_deg` via `classify_cycle_algebraic_degeneracy`; (c) compute `ACE(C)= Σ(row_deg-2)` and custom `check_extrinsic_score(C)= ACE-100` if degenerate else `ACE` (explicitly NOT literature-standard NB-ACE, secondary report only); (d) optimize primary lexicographic `key=(deg4, deg6, deg8, cand)` where `deg4` is prioritized first (1M 2 deg4, 2M 1 deg4 must be eliminated first), `cand` is tie-break `1..31`; custom `check_extrinsic_score` SHALL NOT participate in primary key; (e) greedily scan canonical edge order `1..31` up to 2 sweeps, incrementally maintaining global `deg4/6/8` by recomputing only incident cycles via `edge_to_cycle_ids`, zero seed search, deterministic tie-break smallest `cand`, and SHALL NOT copy full `is_deg` array per candidate. The optimizer SHALL be decoder-free and SHALL run exactly once, not tuned by decoder outcomes. Lane C support/15-block/45-call/decoder/m2 design SHALL remain unchanged.

### R-V51-03: Decoder-Free Label Spectrum Delta (verifiable primary + custom secondary)

The system SHALL emit for each source a decoder-free spectrum delta `original vs new` comprising verifiable primary: `support_exact_equal (=True)`, `rank==m2` both, `support_cycles_4/6/8` unchanged, `degenerate_4/6/8`, `generalized_girth`, `nondeg_frac6/8`; and custom secondary report: `min_check_extrinsic6/8`, `min_deg_ace6/8` derived from `check_extrinsic_score` (custom, NOT literature NB-ACE). The delta SHALL be persisted as `v51_label_spectrum.json`. The system SHALL NOT claim custom `check_extrinsic_score` as literature-standard NB-ACE in any artifact.

### R-V51-04: Label Improvement Gate (three-source lexicographic consistency)

The system SHALL compute `label_improved = (∀source: (deg4_new,deg6_new,deg8_new) ≤_lex (deg4_old,deg6_old,deg8_old)) ∧ (∃source: (deg4_new,deg6_new,deg8_new) <_lex (deg4_old,deg6_old,deg8_old))` where `≤_lex` is lexicographic non-worsening with `deg4` first. Custom `check_extrinsic_score` SHALL NOT be used for gate primary decision. If `label_improved==false` (any source worsens or no source strictly improves), the system SHALL NOT enter the paired decoder experiment and SHALL report terminal `V51_LABEL_NO_IMPROVEMENT` as blocker. The prior rule "∃source deg6/min_check_extrinsic improves" that allowed other sources to worsen is revoked.

### R-V51-05: Conditional Paired Held-Out Experiment

If `label_improved==true` and execution is authorized, the system SHALL run exactly `45` decoder calls over `15` new unused held-out blocks (`392001..392005 / 392101..392105 / 392201..392205`, 4 frames=1024 pairs each, `deterministic_four_consecutive_frames_heldout_unused_new`, zero overlap with `FORBIDDEN 156` and V48/V50 `frame_ids` per source). Per block: one shared `L1` (TRAIN prior) + two `L2` (`old` vs `new`) with same `bob`/`P_i(U2)`, only `H_L2` labels differ. The system SHALL enforce `planned/started/completed = 45/15/30` and SHALL NOT add a TRAIN+VAL arm.

### R-V51-06: Paired Primary and Diagnostics

The system SHALL use `exact_full = exact_u1 && exact_l2` (oracle, not tag) as paired primary. The system SHALL report paired contingency `[[a,b],[c,d]]`, discordance `b+c`, gain `c-b`, per-block `errors_final/iterations/runtime`, and four-way `exact/detected/decoder_non_syndrome/undetected` with `G3' undetected==0`. Leakage `1064/1094/1104` (L2-only tag `≈2^-64`) SHALL remain constant.

### R-V51-07: Terminal States

The system SHALL produce exactly one terminal: `V51_EVIDENCE_INVALID` (integrity/guard fail) prioritized, else `V51_LABEL_NO_IMPROVEMENT` if `label_improved==false` (any worsening or no improvement), else `V51_PAIRED_COMPLETE` (descriptive, no promotion). Custom `check_extrinsic_score` SHALL NOT be described as literature NB-ACE in terminal reporting.

## MODIFIED Requirements

- No existing R1–R7 modified; this delta is additive and does not change formal-ir-methods R1–R7. Lane C support / 15-block / 45-call / decoder 90/1.0 / m2 design remains unchanged per revision constraints.

## REMOVED Requirements

- None. Note: Literature NB-ACE claim `NB-ACE=Σ(check_degree−2)−100` as standard is explicitly removed; replaced by custom `check_extrinsic_score` (secondary report only).
