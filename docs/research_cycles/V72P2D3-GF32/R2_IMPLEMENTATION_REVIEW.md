# V72P2D3-GF32 R2 Independent Implementation Review (prepare-only adapter)

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Cycle: `V72P2D3-GF32-R2`
- Review kind: `R2_IMPLEMENTATION_REVIEW_PREP_ONLY`
- Base SHA: `e094f7e548380db4bfcbc1fe73472e670c32379a`
- Verdict: `R2_IMPLEMENTATION_ACCEPTED_PREP_ONLY`
- Lifecycle after this record: `PREP_READY / REAL_EXECUTION_NOT_AUTHORIZED`
- Date: `2026-09-04`

## 1. Review binding (read-only, no decoder, no formal output)

Reviewed exactly three files (R2 real-input adapter, prepare-only):

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`
2. `scripts/v72p2d3_gf32_contrast.py`
3. `comparison_bench/tests/test_v72p2d3_gf32_contrast.py`

No `src/`, `experiments/`, `tools/`, `results/`, V72P1/D1/D2 accepted file,
or existing comparison output was changed. No `workspace/`原件, draft,
formal output directory, or absolute-path artifact is part of this review.

## 2. Logic evidence (prepare-only stops here, decoder 0)

- `py_compile` PASS on all three files; `pytest comparison_bench/tests/test_v72p2d3_gf32_contrast.py` **47 passed** (`-p no:cacheprovider`).
- R2 registry contract (`validate_prepare_registry`): schema/session/1M/CAL702..1725/VAL1726..1729 disjoint/forbid 1730+/used_2m false/4 cols; extra checksum/hash/tag keys ignored, never read or computed (source probe: `sha256/hashlib/compute_tag` absent in prepare segment).
- R3 parquet (`load_and_validate_prepare_frames`): filtered 4-col read only (`frame_id/pair_idx/alice_symbol/bob_symbol`), CAL1024x256+VAL4x256 geometry, pair0..255 sorted no-dup/no-NaN symbols0..1023; data rows never persist (summary scalars only, banned-keys probe PASS).
- R4-R6 summary (`prepare_real_input`/`build_prepare_summary`): `prepare_summary.json` scalars only, `formal=false`, `decoder_calls=0`, `published_bits=0`; bans Alice/Bob arrays, prior/syndrome values, matrices values, candidate/messages; A reuses D1 scalars (`decoder_calls=0`, `not_recorded_reason`); G prep per-stage `NOT_ATTEMPTED_PREPARE_ONLY` with accepted adapter true-kernel fields, short-circuit history text, oracle at end, no `protocol` field; budgets prep300/G300/inv600/RSS2GiB phased, overlimit BLOCKED with counts retained; output exactly one file under fresh `workspace/` dir, `run_01` forbidden, production root rejected.
- Runner (`scripts/v72p2d3_gf32_contrast.py`): shared builder `build_prepare_inputs` for prepare and real entry (production never passes None); `--registry`/`--prepare-only` prepare-only path exits 0 on READY else 2, no auth consumed; `--phase real --execute-real` requires `--registry` plus cycle-state auth, else fail-closed 2; `sys.path` one-line src insert for frozen V54 import in subprocess CLI.
- Guards: production `decode_fn=None` preserved; prepare segment contains no `run_g_layer/history_decode/run_decoder(/decode_row_layered_fftqspa/compute_tag_64/hashlib/sha256/checksum`; `mock/stub` zero hits in module+runner (frozen history reference allowed).

## 3. Lifecycle and boundaries

```yaml
real_execution_authorized: false
decoder_execution_attempts: 0
syndrome_published_bits: 0
formal_output_created: false
formal_protocol_qualification: false
scientific_promotion: false
state: PREP_READY
next_gate: DECODER_PRE_EXECUTE_REVIEW
```

- Prepare-only evidence: `PREP_ONLY_SUMMARY.json` (`READY_TO_EXECUTE`, `decoder_calls=0`, `syndrome_published_bits=0`, shapes/weights scalars only, no raw rows/symbol/prior/syndrome/matrix values, repo-relative registry path).
- No FER/SKR/qualification/promotion claim. No rerun/tuning/resume authorized by this record.

*Implementation acceptance (prepare-only) only. No decoder or real execution authorized.*
