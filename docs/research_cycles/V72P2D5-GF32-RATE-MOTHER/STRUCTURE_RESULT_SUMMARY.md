# V72P2D5-GF32-RATE-MOTHER — STRUCTURE RESULT SUMMARY

decision: STRUCTURE_PASS_WITH_CYCLE_RISK
basis: 11 hard gates hold on all 8 prefixes; residual four-cycles carried as risk only, no remap.
scope: structure one-shot only (L1->L2 orchestrator, no decoder, no CAL/VAL, no G0/G1/G2)

configs:
  L1: n=1024 m_max=1000 k_min=782 seed=2026090501 prefixes 782,821,860,938
  L2: n=1024 m_max=1000 k_min=686 seed=2026090502 prefixes 686,720,755,823

per-prefix table (rank == prefix_rows on all 8 prefixes):

| layer | prefix_rows | rank | four_cycles | status |
| L1 | 782 | 782 | 0 | STRUCTURE_PASS |
| L1 | 821 | 821 | 2 | STRUCTURE_PASS_WITH_CYCLE_RISK |
| L1 | 860 | 860 | 2 | STRUCTURE_PASS_WITH_CYCLE_RISK |
| L1 | 938 | 938 | 4 | STRUCTURE_PASS_WITH_CYCLE_RISK |
| L2 | 686 | 686 | 0 | STRUCTURE_PASS |
| L2 | 720 | 720 | 0 | STRUCTURE_PASS |
| L2 | 755 | 755 | 0 | STRUCTURE_PASS |
| L2 | 823 | 823 | 2 | STRUCTURE_PASS_WITH_CYCLE_RISK |

four-cycles: L1 0/2/2/4 with per-variable incidence max 0/2/2/2; L2 0/0/0/2 with per-variable incidence max 0/0/0/1; hard-gate failures: none.

hard gates (11, all hold on all 8 prefixes): rank == prefix_rows; zero_rows == 0; zero_columns == 0; isolated_variables == 0; connected_components == 1; largest_component_fraction == 1.0; duplicate_projective_columns == 0; coefficients_nonzero == true; variable_degree_min >= 2; base_pair_duplicates == 0; support_triple_duplicates == 0.

cost: projected single-layer 29.10 s / total 58.19 s within budgets single 900 s / total 1800 s / RSS 2 GiB; operator-measured actual wall 21.46 s, peak RSS 75255808 bytes.

counts: structure_execution_attempts 1 / structure_execution_completed 1 / L1 builds 1 / L2 builds 1 / l2_attempted true / decoder_calls 0 / cal_rows_read 0 / val_rows_read 0.

files (workspace/v72p2d5_structure/20260905_r2, scalars plus small row-degree histograms only): results.json 10409B / table.csv 746B / report.md 793B / execution_summary.json 447B.

cycle-risk carried forward to G0 packet review, no remap. No G0 outputs produced.
