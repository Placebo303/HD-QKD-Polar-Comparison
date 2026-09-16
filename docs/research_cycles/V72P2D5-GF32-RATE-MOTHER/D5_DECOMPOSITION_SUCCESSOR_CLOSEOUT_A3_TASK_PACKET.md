# D5 decomposition successor closeout A3 task packet

Status: `FINAL_AUTHOR_RULING / NO_PYTEST_RERUN / FRESH_METADATA_ALLOWED`

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Branch: `formal-ir-v72p1-addendum-clean`

Expected HEAD: `b6326ad2`

This A3 supersedes A2.2 items 2 and 5. It resolves the missing-session-value blocker without reconstructing or inventing evidence.

## A3.0 Final ruling

- Do not rerun pytest.
- The author re-supplies the prior operator's exact command and complete captured output in A3.1. Copy them verbatim into the appendix and label the source `AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN`.
- The original 22-file pre/post table values are waived. Do not recreate them.
- Preserve the prior operator attestation that A1.3 pre/post metadata was equal, but label it as an attestation rather than a retained table.
- One fresh post-only names/sizes/mtime_ns metadata collection is authorized now.
- DS13 closes by attestation + fresh cutoff-consistent post metadata + zero-path-touch evidence, not by a recovered same-session table.

## A3.1 Author-resupplied pytest evidence

Exact command:

```text
python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py comparison_bench/tests/test_v72p2d4r2_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_decomposition_successor_r1_tests_a1_ad26a4dd-0580-4f4a-a55a-0826d580083c -q --tb=line
```

Complete captured output:

```text
The term '\START_LOCAL: \' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
The term '\START_UTC: \' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
============================== warnings summary ===============================
..\..\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434
  D:\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434: PytestConfigWarning: Unknown config option: cache_dir
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
259 passed, 1 warning in 55.22s
The term '\END_LOCAL: \' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
The term '\END_UTC: \' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
The term '\EXIT_CODE: \' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
```

Required interpretation:

```text
EVIDENCE_SOURCE AUTHOR_RESUPPLIED_FROM_PRIOR_OPERATOR_RETURN
START_LOCAL NOT_CAPTURED
START_UTC NOT_CAPTURED
END_LOCAL NOT_CAPTURED
END_UTC NOT_CAPTURED
PYTEST_EXIT_CODE NOT_CAPTURED
PYTEST_REPORTED_DURATION_S 55.22
PYTEST_ASSERTION_RESULT PASS
VERIFICATION_INVOCATIONS 1
RETRY_COUNT 0
FAILING_IDS []
BASE_TEMP_REMOVED true
DS12 PASS_WITH_PROVENANCE_GAP
```

Do not infer exit 0 or timestamps.

## A3.2 Revised final DS13 evidence

The author accepts the prior operator statement as an attestation:

```text
A1_OPERATOR_ATTESTATION pre/post read-only metadata identical for 22 protected files; each protected root had DIRS []; G2 remained absent
A1_PRE_POST_TABLE_VALUES_RETAINED false
```

Now collect one fresh post-only metadata table for:

- `workspace/v72p2d5_g1/20260907_r2`
- `workspace/v72p2d5_model_f_input/20260907_r1`
- `workspace/v72p2d5_p0_cost/20260906_r1`
- `workspace/v72p2d5_g0/20260905_r2`
- `workspace/v72p2d5_g0_recovery/20260906_r1`
- the accepted structure root named by existing cycle documents
- `workspace/v72p2d5_g2` and its proposed formal child

Metadata only: resolved root, direct child directories, and sorted direct-file `name`, `size`, `mtime_ns`. Do not open or hash contents.

PASS requires:

1. all present protected roots remain flat (`DIRS []`);
2. file names/sizes agree with accepted cycle documents;
3. every protected file mtime is strictly earlier than `2026-09-08 13:29:10 Asia/Shanghai`;
4. G2 remains absent;
5. `git diff d6fabf09..b6326ad2 --name-only` contains no protected-root path;
6. the development root is distinct from every protected root.

Record:

```text
ORIGINAL_PRE_SNAPSHOT_PERSISTED false
A1_PRE_POST_EQUALITY_SOURCE operator_attestation_only
FRESH_POST_METADATA_COLLECTED true
DS13_CLOSURE_BASIS operator_attestation_plus_fresh_post_cutoff_plus_zero_path_touch
DS13 PASS_WITH_DISCLOSED_MISSING_TABLE
```

If any fresh value violates the requirements, STOP. Do not repair or inspect content.

## A3.3 Sole appendix and commit

Create only:

`workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`

Include A3.1 verbatim, A3.2's attestation and complete fresh table, and:

```text
DS12 PASS_WITH_PROVENANCE_GAP
DS13 PASS_WITH_DISCLOSED_MISSING_TABLE
DS15 PASS
FORMAL_G1_RERUN false
SCIENTIFIC_DECODER_CALLS 0
G2_EXECUTED false
G2_PRESENT false
PUSHED false
```

Do not edit any existing file. Stage exactly this appendix, require staged count 1 and `OUT_OF_SCOPE []`, then commit:

```text
test(v72p2d5): add independent decomposition successor closeout evidence

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

Do not push.

## A3.4 Return

Report the one-file commit SHA, DS12/DS13/DS15 verdicts, fresh metadata cutoff result, all `NOT_CAPTURED` fields, and final authorization/G2/gate/status. Confirm zero pytest reruns, zero decoder/phase calls, zero protected-content reads/writes, and no push.

Do not start graph/mother work in this closeout.

