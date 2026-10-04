# Decoder-free GF32 train-source mapping

Track DECIDE. Scope: the existing V25 run_04 train-count NPZ named in
`docs/research_cycles/NBLDPC-GF32-SOURCE-MAPPING-DRAFT/PREREG_AND_AUTH.md`.
Freeze its provenance/metadata gate before reading count arrays. Produce
per-source natural-encoding U1 additive-error summaries; no decoder or fitting.

Allowed new code: `comparison_bench/src/comparison_bench/cli/nbldpc_gf32_source_map.py`
and `comparison_bench/tests/test_nbldpc_gf32_source_map.py` only. Existing
research source and outputs are read-only. Use numpy/stdlib, one small CLI;
no hashes, extra framework, raw/heldout reads, source pooling or publication.
