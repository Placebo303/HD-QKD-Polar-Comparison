# GF32 label alignment EXPLORE

Track EXPLORE. Fixed-support L1 synthetic mechanism test; authoritative
contract: `docs/research_cycles/NBLDPC-GF32-LABEL-MECHANISM-20260930/PREREG_AND_AUTH.md`.
Change only nonzero coefficients via analytic one-pass column scaling.
Reuse existing graph builder and decoder, with a separate small probe.

Allowed new files: `comparison_bench/src/comparison_bench/formal_ir/nbldpc_gf32_label_alignment.py`,
`comparison_bench/src/comparison_bench/cli/nbldpc_gf32_label_probe.py`,
`comparison_bench/tests/test_nbldpc_gf32_label_alignment.py`.
Existing scientific modules and old results are read-only. No generalized
framework, manifest hashes, graph/seed search, private input, or publication.
