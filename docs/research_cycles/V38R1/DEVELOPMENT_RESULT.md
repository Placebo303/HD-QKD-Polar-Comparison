# V38R1 Development Result Candidate

**Cycle**: `V38R1`
**Lifecycle**: `DEVELOPMENT_RESULT_CANDIDATE`
**Machine terminal**: `V38_MULTIPLE_ROUTE_SIGNALS`
**Independent result acceptance**: `PENDING`
**Formal execution / promotion**: `false / false`
**Execution**: one authorized run, exit 0
**Accepted implementation**: `8f7bc7d8d7366772ff425528cd1080fa67ef7509`

This document reports the machine-generated development result. The machine
terminal is not an independent scientific acceptance and does not establish a
formal or promotion result.

## Execution accounting

| quantity | value |
|---|---:|
| decoder calls | 45 |
| winners reconstructed | 9 |
| blocks per lane | 15 |
| block records | 45 |
| max iterations | 30 |
| observed iteration range | 8--30 |
| total iterations | 958 |
| mean iterations | 21.2888888889 |
| exact L2 records | 23 |
| syndrome-ok records | 24 |
| status `converged_exact` | 24 |
| status `converged_no_syndrome` | 21 |
| initial errors, all blocks | 11664 |
| final errors, all blocks | 1984 |
| decoder runtime total (s) | 59.1950858001 |
| decoder runtime mean (s) | 1.3154463511 |
| decoder runtime range (s) | 0.4905261999--1.8719633000 |
| observed command wall time (s, approx.) | 251.8 |

## Lane aggregates and gates

| lane | records | exact | mean final | median final | median improvement | improve/equal/worsen | worst degradation | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| lane_a | 15 | 0 | 111.6 | 115.0 | 0.3502824859 | 15/0/0 | 0 | passed |
| lane_b | 15 | 9 | 16.4666666667 | 0.0 | 1.0 | 15/0/0 | 0 | passed |
| lane_c | 15 | 14 | 4.2 | 0.0 | 1.0 | 15/0/0 | 0 | passed |

Per-lane runtime and error totals:

| lane | runtime (s) | initial errors | final errors | exact L2 | syndrome-ok |
|---|---:|---:|---:|---:|---:|
| lane_a | 27.8036304000 | 3888 | 1674 | 0 | 0 |
| lane_b | 17.5302002000 | 3888 | 247 | 9 | 10 |
| lane_c | 13.8612552001 | 3888 | 63 | 14 | 14 |

Gate details were true for all lanes. Lane A had criterion A false and B/C
true; lanes B and C had criteria A/B/C all true. The gate values are recorded
as machine output and are not independently accepted scientific conclusions.

## Source aggregates

| source | records | runtime (s) | initial errors | final errors | exact L2 | syndrome-ok | reference median |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1M | 15 | 18.9045648002 | 3735 | 584 | 8 | 9 | 171 |
| 1p5M | 15 | 22.4794648000 | 4011 | 830 | 6 | 6 | 178 |
| 2M | 15 | 17.8110561999 | 3918 | 570 | 9 | 9 | 183 |

Source-level aggregate details from the runner:

| lane/source | exact | mean errors | median errors | median delta | reference median |
|---|---:|---:|---:|---:|---:|
| lane_a/1M | 0 | 108.6 | 105.0 | -0.3859649123 | 171 |
| lane_a/1p5M | 0 | 113.6 | 121.0 | -0.3202247191 | 178 |
| lane_a/2M | 0 | 112.6 | 99.0 | -0.4590163934 | 183 |
| lane_b/1M | 3 | 8.2 | 0.0 | -1.0 | 171 |
| lane_b/1p5M | 2 | 39.8 | 30.0 | -0.8314606742 | 178 |
| lane_b/2M | 4 | 1.4 | 0.0 | -1.0 | 183 |
| lane_c/1M | 5 | 0.0 | 0.0 | -1.0 | 171 |
| lane_c/1p5M | 4 | 12.6 | 0.0 | -1.0 | 178 |
| lane_c/2M | 5 | 0.0 | 0.0 | -1.0 | 183 |

## Reconstructed winner inventory

All nine matrices were reconstructed from accepted constructors and frozen
seeds, then strictly compared against the committed run_01 metrics. Lane C
`position_permutations` were included in the strict comparison. The complete
metric dictionaries, including all degree and cycle fields, are in
`v38r1_winning_metrics.json` and `.csv`.

| lane/source | seed | matrix id | shape | rank | support edges | col degree min/mean/max | row degree min/mean/max | support cycles 4/6/8 | degenerate cycles 4/6/8 | valid |
|---|---:|---|---|---:|---:|---|---|---|---|---|
| lane_a/1M | 381101 | lane_a_1M_s381101 | 184x1024 | 184 | 2048 | 2/2.0/2 | 10/11.1304347826/12 | 0/2360/13865 | 0/0/0 | true |
| lane_a/1p5M | 381201 | lane_a_1p5M_s381201 | 190x1024 | 190 | 2048 | 2/2.0/2 | 10/10.7789473684/12 | 0/2270/12815 | 0/0/0 | true |
| lane_a/2M | 381301 | lane_a_2M_s381301 | 192x1024 | 192 | 2048 | 2/2.0/2 | 10/10.6666666667/12 | 0/2240/12465 | 0/0/0 | true |
| lane_b/1M | 382103 | lane_b_1M_s382103 | 184x1024 | 184 | 2047 | 1/1.9990234375/2 | 11/11.125/12 | 7/1525/7190 | 0/50/253 | true |
| lane_b/1p5M | 382201 | lane_b_1p5M_s382201 | 190x1024 | 190 | 2047 | 1/1.9990234375/2 | 10/10.7736842105/11 | 14/1436/6414 | 0/51/210 | true |
| lane_b/2M | 382301 | lane_b_2M_s382301 | 192x1024 | 192 | 2047 | 1/1.9990234375/2 | 10/10.6614583333/11 | 9/1474/6499 | 0/44/216 | true |
| lane_c/1M | 383103 | lane_c_1M_s383103 | 184x1024 | 184 | 2048 | 2/2.0/2 | 10/11.1304347826/12 | 41/288/8459 | 0/6/260 | true |
| lane_c/1p5M | 383203 | lane_c_1p5M_s383203 | 190x1024 | 190 | 2048 | 2/2.0/2 | 10/10.7789473684/12 | 5/248/8480 | 0/6/274 | true |
| lane_c/2M | 383301 | lane_c_2M_s383301 | 192x1024 | 192 | 2048 | 2/2.0/2 | 10/10.6666666667/11 | 12/284/9059 | 0/9/280 | true |

## Output and claim boundary

The additive output directory contains exactly:

- `v38r1_winning_metrics.json`
- `v38r1_winning_metrics.csv`
- `v38r1_development_block_records.json`
- `v38r1_development_block_records.csv`
- `v38r1_triage_summary.json`

`run_01` remains immutable invalid evidence. The machine terminal and all
metrics above require independent review before any scientific interpretation;
this operator return does not self-accept, authorize formal execution, or
promote V38R1.
