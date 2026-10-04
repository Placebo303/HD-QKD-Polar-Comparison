# Spec delta: V72P2D5 Model-F input preparation (candidate only)

No execution, no authorization, no CAL/VAL/raw read in code or tests. This delta constrains the builder, writer, reader, prepare/verify runner, and D5 consumer. It does not merge or replace the accepted R2_DV3 plan or the P0/G1/G2 production-path spec; frozen R2_DV3 thresholds/seeds/budgets/gradings stay authoritative on conflict. If this delta conflicts with D4R2 code/results/OpenSpec on the statistical contract, stop as `BLOCKED_STATISTICAL_CONTRACT_AMBIGUOUS` (do not choose an alternate).

## S-MODEL-F-INPUT (artifact)

- S-MF-01: The artifact SHALL be exactly 2 files under one root: `model_f_input.npz` (keys exactly `counts_ab,p_b`) + `model_f_input_summary.json` (frozen schema `v72p2d5_model_f_input_v1`). No other file SHALL be written; no raw rows/frame data/VAL/`P_F`/`P1`/`P2`/beliefs/syndrome/keys/paths/checksum/pickle-object SHALL be stored.
- S-MF-02: `counts_ab` SHALL be int (`int64`) shape `(1024,1024)` nonnegative with sum `262144`; `p_b` SHALL be `float64` shape `(1024,)` finite nonnegative with sum `1`. `p_b` SHALL equal `counts_ab.sum(axis=0)/262144` (axis0=Alice summation). Transposed input SHALL fail.
- S-MF-03: The summary SHALL carry `cycle V72P2D5-GF32-RATE-MOTHER`, `session 20260123_1M_600k_0dB`, `source 1M`, `cal_start 702`, `cal_end 1725`, `n_frames 1024`, `pairs_per_frame 256`, `n_symbols 262144`, `axis [Alice,Bob]`, `dims [1024,1024]`, `mapping symbol=low+32*high;high=U1;low=U2`, `field {q:32,poly:37}`, `lambda_star 137.3823795883264`, `selection D4R2 nested-CV refit`, `cal_only true`, `val_rows_read 0`, `decoder_calls 0`, `p0_calls 0`, `formal false`, `status MODEL_F_INPUT_CANDIDATE` (loader SHALL also accept `MODEL_F_INPUT_ACCEPTED`), `artifact_files` exactly the 2 names. Absolute paths, hashes/checksums/tags/signatures SHALL NOT appear.
- S-MF-04: Counts SHALL be the full-`CAL702..1725` refit after the frozen lambda selection; averaging outer TRAIN counts or concatenating TEST counts SHALL be invalid. Full-CAL refit SHALL NOT be claimed as a VAL leak; VAL SHALL NOT be read here.

## S-MODEL-F-BUILD (builder)

- S-MB-01: `build_model_f_input` SHALL take injected arrays only (`alice_symbols`, `bob_symbols`, `frame_ids`); it SHALL NOT read files and SHALL NOT accept an external `p_b`.
- S-MB-02: It SHALL validate equal 1-D length `262144`, int-like finite values, symbols `0..1023`, frames exactly `702..1725` each `256` rows. Missing/duplicate/out-of-range/non-256 frames, length mismatch, non-int/NaN/negative/`>1023` SHALL raise.
- S-MB-03: It SHALL reuse `build_canonical_counts` with axis `(Alice,Bob)` and SHALL derive `p_b` from `axis0`. It SHALL NOT call any decoder.

## S-MODEL-F-WRITE (writer)

- S-MW-01: `write_model_f_input` SHALL validate in memory before `mkdir` and SHALL raise `FileExistsError` if the root exists, before any write.
- S-MW-02: It SHALL write exactly the 2 frozen files (`savez_compressed`, readable with `allow_pickle=False`; JSON UTF-8). A second write to the same root SHALL refuse with the first root unchanged.

## S-MODEL-F-LOAD (reader)

- S-ML-01: `load_model_f_input` SHALL revalidate exact file names (no extra), keys exactly `counts_ab/p_b` (with `allow_pickle=False`), shape/dtype/finite/nonneg/int sum, `p_b` marginal sum1, and the frozen summary (including `val_rows_read 0`, `decoder_calls 0`, `p0_calls 0`, status CANDIDATE/ACCEPTED). Failures SHALL raise (shape/sum/marginal/lambda/session/CAL errors distinct).
- S-ML-02: It SHALL return `counts_ab`/`p_b` for `prepare_model_f_prior` and SHALL NOT invoke any decoder or read any parquet.

## S-MODEL-F-RUN (prepare/verify runner)

- S-MR-01: `scripts/v72p2d5_prepare_model_f_input.py` SHALL require `--phase prepare|verify` + `--registry` + `--out-dir` and SHALL gate on `--execution-authorized`. Without the flag it SHALL exit 3 with zero registry/parquet reads, zero `mkdir`/writes, zero loader-import, zero decoder import.
- S-MR-02: Authorized `prepare` SHALL validate the registry, require `CAL702..1725` only, reject VAL, build, write 2 files with `decoder_calls=0`, `p0_calls=0`. Authorized `verify` SHALL be read-only (no decoder, no parquet, no write). Real prepare SHALL NOT run in this change; future prepare SHALL need a separate Pre-EXECUTE review + explicit authorization, and a prepare review SHALL pass before any P0 authorization.

## S-MODEL-F-CONSUME (D5)

- S-MC-01: The D5 consumer SHALL use the fixed frozen root `workspace/v72p2d5_model_f_input/20260907_r1/` (no new CLI flag; `--phase` stays required). Unauthorized entry SHALL refuse (exit 3) before any artifact read, builder, decoder, or writer work.
- S-MC-02: The authorized path SHALL load via `load_model_f_input`, then call the sole `prepare_model_f_prior` (reusing `build_f_model`), then the phase runner. G0-toy reuse, auto-prepare, CAL read from P0, and invented distributions SHALL NOT exist. Missing artifact SHALL stay `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`.

## S-PATH (parquet resolution)

- S-PATH-01: A relative registry `parquet_path` SHALL resolve against the Comparison repository root derived from `__file__` (`ROOT`), not against the registry parent directory and not against the current working directory.
- S-PATH-02: An absolute registry `parquet_path` SHALL resolve directly (`Path(raw).resolve()`), without joining any base directory.
- S-PATH-03: Resolution SHALL NOT use the current working directory, SHALL NOT join the registry parent directory, SHALL NOT search alternate locations, SHALL NOT fall back to a second candidate, and SHALL NOT add retry/hash/checksum/framework machinery.
- S-PATH-04: An empty, missing, whitespace-only, or non-string `parquet_path`, or a resolved path that is not an existing file, SHALL raise (`ValueError` for empty/missing, `FileNotFoundError` for nonexistent) before any `pd.read_parquet` call, before any `mkdir`, and before any artifact write.
- S-PATH-05: Invoking the prepare runner with a relative `--registry` path and with the equivalent absolute `--registry` path SHALL resolve to the same absolute parquet path.

## S-STOP (boundaries)

- S-SP-01: This change SHALL NOT execute prepare, grant authorization, read CAL/VAL/raw/real data in code or tests, call any decoder, create any formal output, or modify `cycle_state.yaml` authorizations.
- S-SP-02: It SHALL NOT add a generic sweep framework, `IRRunResult` adapter, concurrency/resume/retry, atomic/backup/lock/checksum/hash/tag machinery, YAML grids, alternate families, or lambda/seed tuning.
- S-SP-03: STRUCTURE/G0/G0-recovery/P0/G1/G2 behavior SHALL be regression-preserved; frozen experiments, seeds, tables, budgets, calls, and naming SHALL NOT change. Formal Model-F/P0/G1/G2 roots SHALL stay absent.

## S-TEST-ISOLATION (test-only isolation, lifecycle-independent)

- TS01 lifecycle-independent: tests SHALL NOT depend on real formal-root existence/absence; missing-isolation SHALL use monkeypatched absent tmp; existing-preservation SHALL use local `(size,mtime_ns)` snapshot, no hash/copy.
- TS02 no implicit prod decoder: every authorized test-only synthetic call SHALL pass explicit `decode_fn` (fake); authorized `True` reaching default `bind_historical_decoder` SHALL fail.
- TS03 tmp-only: every authorized test-only synthetic call SHALL pass explicit `out_dir` under `tmp_path`; reaching a formal out_dir SHALL fail.
- TS04 injected Model-F: every authorized test-only synthetic call SHALL pass explicit `counts_ab`/`p_b` (fake Model-F); loading the real formal root in tests SHALL fail except documented missing-isolation with booms.
- TS05 missing-isolation via monkeypatch tmp: BLOCKED-path tests SHALL monkeypatch the formal root/loader to absent tmp (or exact BLOCKED error), with binder+writer booms, expecting `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` with decoder/writer 0 and tmp empty.
- TS06 existing-preservation snapshot: tests SHALL snapshot Model-F/G0/G1 `(size,mtime_ns)` before/after and assert unchanged; SHALL NOT write/delete/move/rename/copy/normalize/hash formal artifacts; P0/G2 SHALL remain absent; no new formal root SHALL be created.
- TS07 future-neutrality: tests SHALL NOT assert real Model-F/G1 absence (and SHALL NOT invert to assert exists); SHALL observe G1 existence only to prove unchanged, with no validity/acceptance/qualification/promotion/perf/G2-auth claim.
- TS08 fake counts test-only: fake Model-F counts SHALL be test-only injected tables, never written to formal roots, never claimed as CAL-TRAIN.
- TS09 incident label: the 20260907 unauthorized G1 test execution SHALL be labeled `INVALID_UNAUTHORIZED_TEST_TRIGGERED`; SHALL NOT be accepted/qualified/promoted, SHALL NOT support G1-perf or G2-auth, SHALL be preserved pending disposition with no delete/hash/copy.
- TS10 collection safety static check: a stdlib AST test SHALL fail if any authorized `True` synthetic call can reach the default decoder/formal out_dir without explicit `decode_fn`/`out_dir`/counts; documented fail-before-decoder exceptions (missing-isolation with booms) SHALL be listed; no CLI authorized phase SHALL appear in tests; no `cycle_state` mutation SHALL appear in tests.
