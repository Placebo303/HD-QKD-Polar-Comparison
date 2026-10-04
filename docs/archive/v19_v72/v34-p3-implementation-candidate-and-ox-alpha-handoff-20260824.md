# V34 P3 implementation candidate and Ox Alpha handoff — 2026-08-24

## 1. Current accepted boundary

- Change: `formal-nonbinary-ldpc-v34-corrected-matched-empirical-p-finite-control`.
- Freeze baseline: `f5f61eb672afe8e399727fa5d7507ca9f2f9151a`.
- Freeze lifecycle commit: `0c817a322d1d1674f65708563afe3b77c47ae961`.
- Current state: `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`.
- Candidate ownership:
  - `comparison_bench/src/comparison_bench/cli/run_nonbinary_v34_corrected_matched_empirical_p_finite_control.py`
  - `comparison_bench/tests/test_nonbinary_v34_corrected_matched_empirical_p_finite_control.py`

P3 main-thread evidence: compile PASS; `test-selfcheck` PASS; real-input
read-only `prepare` PASS; focused fake suite `13 passed in 10.16s` using
`workspace/v34_p3_main_20260824_01`; matrix digest
`d30335b4d0d74df3e7729e01b02ae1ae73e43035652c59e81f871a5545fe73bb`;
official `nbldpc_v34.../run_01` absent.

This proves only that an implementation candidate exists and its current fake
tests pass. It does not prove IR1 acceptance or any decoder result.

## 2. Ox Alpha role and ownership

Ox Alpha is an implementation/evidence operator, not the requirements owner or
reviewer. It may edit only the two candidate files above plus additive test
artifacts under a fresh `workspace/v34_ox_<id>/` root. It must not edit the
OpenSpec, thresholds, documents, historical outputs, or protected roots. It
must not mark its own work accepted.

Forbidden: production execute; real V32/V28R decoder invocation; official
V34 root creation; V25--V33 writes; run_02/resume/retry; more seeds; 20/20;
max_iter=200; tuning; raw data; qualification/promotion claims; git add/commit.

## 3. P4 frozen acceptance packet

Return only after all items pass, or on one concrete blocker with the failing
command, full error, attempted remedy and the single decision required.

- **OX-A1 structural**: compile/import/help/selfcheck; production decoder module
  must not be imported by import/help/prepare/verify/fake execute.
- **OX-A2 real-input prepare**: independently check V25 SHA and literal train
  keys; V31 packet SHA/id/m1/m2/field; V32 runner and V28R function identities;
  NumPy 2.4.0 and exact `V34-PCG64-REF1`; zero decoder calls and zero writes.
- **OX-A3 sampler**: monkeypatch/count RNG usage to prove one PCG64 instance and
  exactly one C-order `choice` per block; reject invalid shape, negative,
  non-finite, zero-total and bad normalization without fallback/resampling.
- **OX-A4 fake T2**: execute all 60 unique source-major ordinals with an explicit
  fake runner into a fresh workspace root; assert 20/source, seeds, m2, oracle
  markers, evidence fields, >=19/20 aggregation and PASS/FAIL/INCONCLUSIVE
  priority. Ordinary legal decode failure continues; fatal malformed/non-finite
  result stops and retains INCONCLUSIVE.
- **OX-A5 authorization/collision**: missing/extra/wrong-type auth fields,
  wrong HEAD/freeze/matrix digest/path/decision/grantee/granted flag all cause
  zero decoder calls and zero official writes. Existing official root causes
  collision before decoder. Fake mode must reject official or protected roots.
- **OX-A6 strict replay/tamper**: verify must reconstruct without decoder and
  reject raw record drift; recomputed local record fields; manifest/digest
  links; seed/ordinal/source/m2/sampler markers; summaries; terminal; claim and
  lifecycle fields. Missing/duplicate/extra records must fail.
- **OX-A7 T3 boundary**: pre/post compare all frozen protected roots and assert
  no official V34 root, no sibling writes, and no production decoder import or
  call across the complete fake flow.

Do not build production-style integrity, retry, lock, cache or abstraction
frameworks. Add only tests or the smallest scientifically necessary correction.

## 4. Commands

Use a fresh additive workspace id:

```powershell
python -B -m py_compile comparison_bench/src/comparison_bench/cli/run_nonbinary_v34_corrected_matched_empirical_p_finite_control.py comparison_bench/tests/test_nonbinary_v34_corrected_matched_empirical_p_finite_control.py
python -B -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v34_corrected_matched_empirical_p_finite_control test-selfcheck
python -B -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v34_corrected_matched_empirical_p_finite_control prepare
python -B -m pytest -p no:cacheprovider comparison_bench/tests/test_nonbinary_v34_corrected_matched_empirical_p_finite_control.py -q --basetemp workspace/v34_ox_<fresh-id>
```

No `execute` command without `--runner` is permitted in P4. A no-auth guard
may be tested only with an injected call counter and after independently
asserting the official root is absent.

## 5. Return and independent acceptance

Ox Alpha returns: changed-file manifest; OX-A1--A7 result table; exact commands
and outputs; fake artifact root; remaining risks; explicit statement that no
real decoder/official output was touched.

Codex then performs independent IR1 on the exact candidate HEAD. Only after
IR1 ACCEPT and main implementation ACCEPT may the project stop at
`IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`. A later production run still
requires a new user `EXECUTE_AUTH` bound to that HEAD and the frozen matrix.

