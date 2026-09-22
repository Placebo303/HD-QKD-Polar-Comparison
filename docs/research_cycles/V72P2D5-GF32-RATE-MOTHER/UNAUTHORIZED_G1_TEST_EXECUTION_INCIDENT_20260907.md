# Unauthorized G1 test execution incident — 20260907

Status: `INVALID_UNAUTHORIZED_TEST_TRIGGERED` (I01). No acceptance, no
qualification, no promotion, no G1-perf claim, no G2-auth claim (I07).
Preserved pending disposition; no delete/move/rerun/hash/copy (I08).

## I02 root

`workspace/v72p2d5_g1/20260906_r1/` (created 2026-09-06T18:35:32Z / 02:35:32
local, pytest 333.06s trigger).

## I03 names/sizes/mtimes (stat only, no hash)

- `execution_summary.json` size 267 mtime_ticks 639243165329114577 utc 2026-09-06T18:35:32.9114577Z
- `report.md` size 146 mtime_ticks 639243165329114577 utc 2026-09-06T18:35:32.9114577Z
- `results.json` size 2593 mtime_ticks 639243165329099544 utc 2026-09-06T18:35:32.9099544Z
- `table.csv` size 126 mtime_ticks 639243165329099544 utc 2026-09-06T18:35:32.9099544Z
- Model-F (authorized, for chain): `workspace/v72p2d5_model_f_input/20260907_r1/`
  `model_f_input.npz` 208467 ticks 639243148270436988 utc 2026-09-06T18:07:07.0436988Z;
  `model_f_input_summary.json` 752 same mtime.
- G0 (reference): `workspace/v72p2d5_g0/20260905_r2/` 4 files (385/712/2512/306).
- P0/G2: absent (`workspace/v72p2d5_p0_cost/20260906_r1` False,
  `workspace/v72p2d5_g2/20260906_r1` False).

## I04 phase evidence

Phase g1, decoder_calls 440, f [1.0,1.2], 100 blocks/f, APP exact 0,
APP rate 1.0? No — APP 0, oracle 0 (per incident brief: app0 app1.0 oracle0
as reported; exact counts 0, failure fraction 1.0, oracle 0).

## I05 chain

02:07 Model-F prepared → pytest started → stale tests expected absence
(`test_M21`, former line 3069 in `test_P0G1G2_i`, `M19`/`M24`/`P12` absence
asserts) → `run_g1_synthetic(authorized=True)` without fake decoder/injected
arrays/tmp out_dir → no refusal (authorized True passes gate) → bound prod
decoder (`bind_historical_decoder`) → 440 decoder calls → default writer to
formal G1 root 02:35:32 → ValueError + stale fails on rerun.

Stale callsites: `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
former line 3069 (`test_P0G1G2_i`, `authorized=True` bare) and former line
3151 (`test_M21`, `authorized=True` bare).

## I06 authorization mismatch

Authorization covered Model-F prepare + verify only; `g1_execution_authorized`
false; P0 unreviewed; G1 out-of-scope. Test-level `authorized=True` is not
production authorization and did not grant it.

## I07 no disposition

Not accepted, not qualified, not promoted; no G1 performance conclusion; no
algorithm claim; no G2 authorization; no failure grading of the method.

## I08 preservation

Pending disposition decision by main thread. No delete/quarantine/move/rename/
copy/normalize/hash. Stat-only observation.

## I09 root cause

Isolation defect, lifecycle-dependent: tests assumed formal Model-F absent and
called authorized synthetic without explicit fake decoder/injected Model-F/tmp
out_dir, reaching implicit prod decoder + formal out_dir once Model-F existed.

## I10 corrective (test-only, this repair)

Tmp-only out_dir, explicit fake decoder, injected fake Model-F, monkeypatched
absent-tmp missing isolation with binder/writer booms, no global formal-root
asserts, local `(size,mtime_ns)` snapshot preservation, stdlib AST static guard.

## I11 gate

R1 remains FAIL. No `RESULT_SUMMARY`, no P0 authorization, until this repair is
independently reviewed + G1 root dispositioned + authorized rerun separately
approved.

## I12 containment rework R1 (test-only, no disposition)

Repaired names: `test_M19_d5_unauthorized_artifact_zero` (SAFE A),
`test_M21_d5_missing_artifact_blocked_no_toy` (SAFE C loop, 1 physical / 3
logical), new `test_M21_param_missing_isolation` (SAFE C parametrized P0/G1/G2),
`test_P0G1G2_i_g0_recovery_structure_regression` (kept G0/recovery + one
documented isolated G1), `test_M20_d5_authorized_fake_load_reaches_runner`
(SAFE B fake tmp), `test_TIS_static_authorized_synthetic_isolation` (repaired
direct/getattr/loop-var/parametrized guard), `test_M24/P12_formal_roots_absent`.
T-ISOL loc: both `tasks.md` (`formal-ir-v72p2d5-model-f-input-preparation`,
`v72p2d5-p0-g1-g2-production-path`) additive T-ISOL-01..10. No disposition:
still INVALID, unaccepted, unmoved, unused; P0/G2 absent; Model-F/G0/G1
snapshots unchanged. Results: collect 165 (134+31), focused 10 passed,
combined 165 passed. Pointer: `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`.
