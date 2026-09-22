# D2 — Information-theoretic feasibility vs actual rates (read-only)

- margin method: simple gap reporting at n=1024 only: gap_bits = leakage_bits - required_bits per layer and total, plus leakage/required ratio; no normal approximation and no other statistics

| source | H.U1|B | H.U2|B,U1 | H.A|B | leak_total(verbatim) | gap L1 | gap L2 | gap total(verb) | feasible |
|---|---|---|---|---|---|---|---|---|
| 1M | 0.024281 | 0.776757 | 0.801038 | 1064.0 | 55.14 | 124.6 | 243.74 | True |
| 1p5M | 0.025199 | 0.800367 | 0.825566 | 1094.0 | 54.2 | 130.42 | 248.62 | True |
| 2M | 0.025662 | 0.806901 | 0.832563 | 1104.0 | 53.72 | 133.73 | 251.46 | True |
