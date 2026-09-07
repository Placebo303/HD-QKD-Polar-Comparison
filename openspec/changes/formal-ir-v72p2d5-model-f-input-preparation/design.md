# Design: V72P2D5 Model-F input preparation

Status: `MODEL_F_INPUT_IMPLEMENTATION_CANDIDATE`. Comparison-only. No execution, no authorization, no CAL/VAL/raw read in code or tests (fake/injected tiny tables only), no formal output. All constants below are frozen from D4R2 and the accepted R2_DV3 plan; this change invents none.

## 1. Dataflow (prepare/consume split)

```text
CAL702..1725 (1024 frames x 256 pairs = 262144 symbols, session 20260123_1M_600k_0dB)
  -> [future authorized prepare only] build_model_f_input(alice,bob,frame_ids)
  -> write_model_f_input(out_dir) : model_f_input.npz + model_f_input_summary.json
  -> [P0/G1/G2 consume only] load_model_f_input(frozen_root)
  -> prepare_model_f_prior(counts_ab, p_b) [reuses build_f_model, lambda*]
  -> phase runner (P0/G1/G2, synthetic gate, APP-fed)
```

- Prepare and consume are separate: P0/G1/G2 MUST NOT read CAL, MUST NOT auto-prepare, MUST NOT use the G0 toy fixture or any invented distribution. Missing artifact stays `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`.
- Full-CAL refit happens once, after the frozen lambda selection. It is NOT an average of outer TRAIN counts and NOT a TEST concatenation. Counts axis and `P(B)` formula are frozen in §2.
- No VAL is read anywhere in this change. Full-CAL refit is NOT a VAL leak (no VAL claim). Future real single-point work must use independent VAL/fresh data.

## 2. Canonical counts + P(B) (frozen)

```text
counts_ab[a,b] = #CAL pairs with Alice=a, Bob=b, axis0=Alice, axis1=Bob
symbol = low + 32*high, U1=high (bits5..9), U2=low (bits0..4), bit0=LSB
bob_counts[b] = sum_a counts_ab[a,b]            # axis0 summation
p_b[b] = bob_counts[b] / 262144
require: counts shape (1024,1024) nonneg int sum 262144
require: bob (1024,) == counts.sum(axis=0)
require: p_b (1024,) float64 >=0 sum1 == marginal/262144
```

- Builder reuses `build_canonical_counts` (D3, V54 semantics) then derives `p_b` from `axis0`. External `p_b` is rejected (no `p_b` parameter on the builder).
- Transposed `[Bob,Alice]` input must fail (asymmetric hand-calc + transpose counterexample in tests).
- `q32 poly37`, `lambda*=137.3823795883264` (D4R2 nested-CV, refit only), `CE_L1=3.814742 / CE_L2=3.347605 / joint=7.162347` are provenance in the summary; they do not enter the builder except as recorded constants.

## 3. Artifact schema (frozen)

Planned formal root (NEVER created in this change; only `tmp_path` tests):

`workspace/v72p2d5_model_f_input/20260907_r1/`

Exactly 2 files, no more, no less:

- `model_f_input.npz`: keys exactly `counts_ab,p_b`. `counts_ab` int64 `(1024,1024)`, `p_b` float64 `(1024,)`. No raw rows/frame data/VAL/`P_F`/`P1`/`P2`/beliefs/syndrome/keys/paths/checksum/pickle-object. Written with `savez_compressed`, readable with `allow_pickle=False`.
- `model_f_input_summary.json` (UTF-8): frozen keys

```json
{
  "schema": "v72p2d5_model_f_input_v1",
  "cycle": "V72P2D5-GF32-RATE-MOTHER",
  "session": "20260123_1M_600k_0dB",
  "source": "1M",
  "cal_start": 702, "cal_end": 1725, "n_frames": 1024,
  "pairs_per_frame": 256, "n_symbols": 262144,
  "axis": ["Alice", "Bob"], "dims": [1024, 1024],
  "mapping": "symbol=low+32*high;high=U1;low=U2",
  "field": {"q": 32, "poly": 37},
  "lambda_star": 137.3823795883264,
  "selection": "D4R2 nested-CV refit",
  "cal_only": true, "val_rows_read": 0, "decoder_calls": 0, "p0_calls": 0,
  "formal": false, "status": "MODEL_F_INPUT_CANDIDATE",
  "artifact_files": ["model_f_input.npz", "model_f_input_summary.json"]
}
```

- `status` is `MODEL_F_INPUT_CANDIDATE` in this change; the loader also accepts `MODEL_F_INPUT_ACCEPTED` (future independent acceptance only, not granted here).
- No absolute paths, no hashes/checksums/tags/signatures in either file. Validation happens in memory before `mkdir`; existing root raises `FileExistsError` before any write.

## 4. Prepare runner (implement-only)

`scripts/v72p2d5_prepare_model_f_input.py`:

- Flags: `--phase prepare|verify` (required) + `--registry` + `--out-dir` (required) + `--execution-authorized` (store_true choke). No seed/lambda/`f`/degree/family overrides.
- Unauthorized (flag absent): exit 3 before any registry/parquet read, before any `mkdir`/write, before any data-loader import, before any decoder import. Zero side effects.
- Authorized `prepare` (implemented, NOT executed here): validate registry, require `CAL702..1725` only, reject VAL, build via `build_model_f_input`, write exactly 2 files, `decoder_calls=0`, `p0_calls=0`. Only fake/injected-loader tests run in this change; real registry/parquet prepare is future work needing a separate Pre-EXECUTE review + explicit authorization.
- Authorized `verify`: read-only load via `load_model_f_input`, no decoder, no parquet, no write.

## 5. D5 consumer (minimal, fixed root)

- Frozen root `workspace/v72p2d5_model_f_input/20260907_r1/` is a fixed constant (`MODEL_F_INPUT_FORMAL_ROOT`). No `--model-input-root` flag is added: the frozen P0/G1/G2 CLI spec forbids new flags (`--phase` stays required, no frozen-param overrides), so a fixed root is the only compliant choice. Documented here.
- Each synthetic entrypoint (`run_p0_cost_synthetic`, `run_g1_synthetic`, `run_g2_synthetic`) keeps `_require_authorized` first (unauthorized exits before any artifact read, builder, decoder, or writer work). When authorized but `counts_ab/p_b` are not injected, it loads the frozen root via `load_model_f_input`, then calls the sole `prepare_model_f_prior` (which reuses `build_f_model`), then the phase runner. No G0-toy, no auto-prepare, no CAL read from P0.
- Missing artifact (current state, formal root absent) stays `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` before any construction/decode/write.

## 6. Authorization gate

- This change grants no authorization. All `*_execution_authorized` stay false; `decoder_executed`, `cal_rows_read`, `val_rows_read` are unchanged by implementation/tests. Status stays `MODEL_F_INPUT_CANDIDATE`.
- Future real prepare needs a separate Pre-EXECUTE review + explicit user authorization. A prepare review (artifact correctness) must pass before any P0 authorization.
- Pre-EXECUTE / Pre-RESULT gates still apply to any future execution/solidification and are out of scope here.

## 7. Explicitly not in design

Generic sweep loops, YAML grids, `IRRunResult` mapping, concurrency, resume, retry, atomic writes, backup, locking, versioning, hash/manifest/tag fields, alternate families, and any tuning of lambda/seeds/graph degree. No schema-validation framework (plain checks only); no broad `except`.

## 8. Parquet path resolution (PX11 rework, frozen defect fix)

- Defect: `parquet_path=(Path(registry_path).parent/parquet_path).resolve()` with frozen registry `parquet_path=comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet` yields `workspace/comparison_bench/...` (`exists False`); correct is `REPO_ROOT/...` (`exists True`).
- Contract: relative paths SHALL resolve vs the Comparison repo root derived from `__file__` (reuse existing `ROOT` in the prepare runner), not vs the registry directory, not vs cwd. Absolute paths SHALL resolve directly. No search, no fallback to a second candidate, no registry edit, no frozen absolute Windows path.
- Implementation: `_resolve_parquet_path(raw)` validates a non-empty string, joins `ROOT` when not absolute, resolves, requires `is_file()` else raises `FileNotFoundError`, and returns the absolute path. `_load_cal_arrays` calls it before any `pd.read_parquet`, `mkdir`, or write. No `cwd`, no registry-parent join, no `D:\` hardcode, no dual-search, no retry/hash/framework; registry/CAL-VAL-filter/artifact/auth semantics unchanged.
