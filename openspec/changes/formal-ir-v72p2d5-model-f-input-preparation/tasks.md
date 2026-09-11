# Tasks: V72P2D5 Model-F input preparation (coder-fast, candidate only)

Frozen packet: full-CAL refit after frozen lambda; no execution/authorization; no CAL/VAL/raw read in code or tests (injected fakes/tiny tables only); focused tests only. Implement exactly what is specified; if any task is ambiguous, stop and return BLOCKED (do not guess).

Allowlist: NEW `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py` (A1), NEW `scripts/v72p2d5_prepare_model_f_input.py` (A2), NEW `comparison_bench/tests/test_v72p2d5_model_f_input.py` (A3); MINIMAL edits `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` (A4), `scripts/v72p2d5_gf32_rate_mother.py` (A5), `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (A6); new OpenSpec `openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/` (A7-A10). No other file. No `cycle_state.yaml` auth change. No formal output creation. Do NOT modify D4 impl unless a canonical-count bug is found — then STOP as BLOCKED needing rescope.

- [x] T1 — Builder `build_model_f_input(alice,bob,frame_ids)` (A1)
  - Injected arrays only, no file read. Validate equal 1-D length, int-like/finite, range `0..1023` for symbols; frames exactly `702..1725` each `256` rows (1024 frames, 262144 symbols total).
  - Reuse `build_canonical_counts` (axis Alice,Bob); derive `p_b` from `axis0` (`bob_counts/total`); reject external `p_b` (no such parameter). Return counts (`int64 1024x1024`)/`p_b` (`float64 1024`)/scalars. No decoder.
  - Verify: M01 transpose must fail; M02 sparse tiny sum/marginal; M03 frame missing/dup/out-of-range/non-256 reject; M04 len mismatch; M05 non-int/NaN/neg/>1023; M06 `p_b` derived not hand-filled.

- [x] T2 — Writer `write_model_f_input(out_dir, counts_ab, p_b)` (A1)
  - Validate in memory before `mkdir` (shape/dtype/finite/nonneg/int sum262144; `p_b` marginal sum1; frozen summary fields). Existing root raises `FileExistsError` before any write. Write exactly 2 files (`model_f_input.npz` via `savez_compressed`, keys exactly `counts_ab,p_b`, readable with `allow_pickle=False`; `model_f_input_summary.json` UTF-8). No raw rows/frame data/VAL/`P_F`/`P1`/`P2`/beliefs/syndrome/keys/paths/checksum/pickle-object; no absolute paths; no atomic/backup/lock/checksum; no broad except.
  - Verify: M07 exactly 2 files; M08 second write same root refuses, first unchanged.

- [x] T3 — Reader `load_model_f_input(in_dir)` (A1)
  - Revalidate 2 files (exact names, no extra), keys exactly `counts_ab/p_b` (with `allow_pickle=False`), shape/dtype/finite/nonneg/int sum262144, `p_b` marginal sum1 (`==marginal/262144`), summary frozen (schema/cycle/session/source/CAL/axis/dims/mapping/field/lambda/selection/`cal_only` true/`val_rows_read` 0/`decoder_calls` 0/`p0_calls` 0/`formal` false/status CANDIDATE/ACCEPTED). Return counts/`p_b` (+summary) for `prepare_model_f_prior`. No schema framework.
  - Verify: M09 keys exactly 2; M10 no object/pickle; M11 summary frozen; M12 shape err; M13 sum err; M14 marginal err; M15 lambda/session/CAL err.

- [x] T4 — Runner `scripts/v72p2d5_prepare_model_f_input.py` (A2)
  - Flags `--phase prepare|verify` + `--registry` + `--out-dir` + `--execution-authorized` choke; no seed/lambda/`f`/degree/family overrides. Default (flag absent) exits 3 with zero registry/parquet reads, zero `mkdir`/writes, zero loader-import, zero decoder import.
  - Even with the flag, DO NOT run real prepare here — only fake/injected-loader tests. Future authorized `prepare`: validate registry, `CAL702..1725` only, reject VAL, build, write 2 files, `decoder_calls=0`, `p0_calls=0`. Authorized `verify`: read-only, no decoder/parquet, no write.
  - Verify: M16 prepare unauthorized zeros; M17 authorized fake one-CAL-loader (`VAL` 0, tmp root, `decoder_calls` 0, `p0_calls` 0); M18 verify read-only.

- [x] T5 — D5 consumer minimal (A4 + A5)
  - Frozen root `workspace/v72p2d5_model_f_input/20260907_r1/` as a fixed constant (no `--model-input-root` flag: the frozen CLI spec allows no new flags; document this choice in design §5; no seed/lambda/`f`/degree/family overrides).
  - Unauthorized exits 3 before any artifact read, builder, decoder, or writer work. Authorized loads via `load_model_f_input` then `prepare_model_f_prior` (reuses `build_f_model`) then the phase runner. No G0-toy, no auto-prepare, no CAL read from P0. Missing artifact stays BLOCKED. Prepare/consume split preserved.
  - Verify: M19 D5 unauthorized (`artifact_reads` 0, `decoder_calls` 0, builder 0, writer 0); M20 authorized fake load→prepare→runner (identity/shape, `prepare_model_f_prior` reached); M21 missing artifact → BLOCKED, no CAL/toy fallback.

- [x] T6 — Lifecycle + focused suite (A3 + A6 + OpenSpec A7-A10)
  - Keep all `*_execution_authorized` false; status stays CANDIDATE; formal Model-F/P0/G1/G2 roots absent (`M24`); no commit/push; no self-acceptance. OpenSpec states Comparison-only, prepare/consume split, implement-only, future prepare needs separate Pre-EXECUTE+auth, prepare review before P0 auth.
  - Verify: M22 existing D5 tests pass (regression, additive only); M23 D4 audit tests pass without changing D4 expectations; M24 formal roots absent; `py_compile` clean on A1+A2+A4+A5; CLI `--help` + unauthorized refusal only.

- [x] T-ISOL — Lifecycle-independent test containment (additive, no T1-T6/PX11 rewrite)
  - T-ISOL-01 — Unauthorized choke (SAFE A): `authorized=False` synthetic calls raise before builder/loader/decoder/writer/files. Mapped: `test_M19_d5_unauthorized_artifact_zero`, `test_P0G1G2_e_authorization_refuses_before_work`.
  - T-ISOL-02 — Authorized fake tmp (SAFE B): `authorized=True` non-BLOCKED calls pass explicit injected `counts_ab`+`p_b` + fake `decode_fn` + tmp `out_dir`. Mapped: `test_M20_d5_authorized_fake_load_reaches_runner` (440 calls, tmp only).
  - T-ISOL-03 — Missing isolation fail-before (SAFE C): `authorized=True` without injected tables only under monkeypatched absent `MODEL_F_INPUT_FORMAL_ROOT` + `bind_historical_decoder` boom + writer boom(s), expecting `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`, zero binder/writer entries, tmp empty, real Model-F/G1 snapshots unchanged. Mapped: `test_M21_d5_missing_artifact_blocked_no_toy` (P0/G1/G2 loop, 1 physical / 3 logical).
  - T-ISOL-04 — Ex-unsafe G1 documented: `test_P0G1G2_i_g0_recovery_structure_regression` keeps G0/recovery/structure asserts + one documented isolated G1 missing-isolation call (same SAFE C markers); no other bare `authorized=True`.
  - T-ISOL-05 — Static guard: `test_TIS_static_authorized_synthetic_isolation` (stdlib AST only) enforces SAFE A/B/C over direct `mod.run_*`, `runner=getattr(mod,name)`, loop-var `fn`, parametrized `runner_name`; fail-before exceptions allowlisted only with boom+BLOCKED+absent-tmp markers.
  - T-ISOL-06 — Lifecycle snapshots: `test_M24_formal_roots_absent` + `test_P12_formal_roots_absent` + G1/P0/G2 snapshot asserts in M19/M20/M21/P0G1G2_f/g/i prove tmp-only, P0/G2 absent, Model-F/G0/G1 unchanged; no global formal-root absence assert.
  - T-ISOL-07 — No CLI auth exec / no cycle write: no `--execution-authorized` literal, no `*_execution_authorized": True`, no `STATE_PATH` write / `yaml.dump`, CLI unauthorized exit 3 only.
  - T-ISOL-08 — New parametrized missing isolation: `test_M21_param_missing_isolation` parametrized over `(runner_name,writer_name)` P0/G1/G2 pairs (1 physical definition / 3 logical variants), same SAFE C markers per pair, real roots unchanged.
  - T-ISOL-09 — No prod/formal reachability: binder boom zero, writer boom zero, no `bind_historical_decoder` entry, no formal `out_dir` default, no new formal output, no prod decoder import on fake paths.
  - T-ISOL-10 — Gates+evidence: G01-G09 pre-pytest gate, focused+combined pytest literals, `TEST_ISOLATION_REWORK_EVIDENCE_R1.md` durable record, incident stays `INVALID_UNAUTHORIZED_TEST_TRIGGERED` unaccepted/unmoved.

- [x] PX11-R1 — Parquet path rework (registry-relative vs repo ROOT)
  - Fix `scripts/v72p2d5_prepare_model_f_input.py` only: reuse existing `ROOT` from `__file__`; add `_resolve_parquet_path(raw)` (non-empty-string validate; when not absolute join `ROOT`, resolve; require `is_file()` else `FileNotFoundError`; absolute direct resolve); call it from `_load_cal_arrays` before any `pd.read_parquet`/`mkdir`/write. No cwd, no registry-parent join, no `D:\` hardcode, no dual-search, no retry/hash/framework; no registry edit; no CAL/VAL-filter, artifact, or auth change; no D4 modification. History and statistical contract unchanged.
  - Verify (fakes or `exists`/`is_file` only, never real `pd.read_parquet` rows): P01 root-relative resolves to `ROOT/.../pairs.parquet` with no row read; P02 relative-registry invocation resolves correctly; P03 absolute-registry invocation resolves to the same absolute; P04 cwd changed to `tmp_path` still resolves the same; P05 absolute `parquet_path` resolves directly; P06 empty/whitespace/non-string rejects; P07 nonexistent fails before `pd.read_parquet` (zero reads/writes/mkdirs); P08 registry-parent join `workspace/comparison_bench/...` is not used; P09 authorized fake loader still passes; P10 unauthorized exits 3 before resolver/import/read; P11 verify path unaffected; P12 formal Model-F/P0/G1/G2 roots absent.
