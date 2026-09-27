# M3-a nested construction requirements

The implementation SHALL preserve all 200 base GF(32) triples and append exactly eight degree-10 rows with nonzero GF(32) labels. It SHALL use the frozen seed pairs and deterministic greedy selection in `design.md`, without seed search or tuning. The construction batch SHALL record base/full rank, four-cycle count, variable-degree distributions, girth, reproducibility, wall and RSS separately for both arms. No decoder, real data, FER/efficiency or method selection is within this change.
