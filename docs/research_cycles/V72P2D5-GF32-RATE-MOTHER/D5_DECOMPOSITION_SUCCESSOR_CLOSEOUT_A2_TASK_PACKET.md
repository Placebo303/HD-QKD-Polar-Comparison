# D5 decomposition successor closeout A2 task packet

Status: `AUTHOR_CORRIGENDUM / RECORD_EXISTING_OBSERVATION / NO_RERUN`

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Branch: `formal-ir-v72p1-addendum-clean`

Expected HEAD: `b6326ad2`

This A2 replaces A1.2's requirement that exact start/end timestamps and the pytest process exit code must have been captured. It preserves A1.3 and A1.4 except where explicitly restated below.

## A2.0 Author ruling

The pytest invocation must **not** be rerun.

The observed complete terminal output:

```text
259 passed, 1 warning in 55.22s
```

with progress reaching `[100%]`, zero failing IDs, the exact frozen command, and no launch/timeout error from pytest is sufficient to close the assertion-result portion of DS12.

The wrapper failed only while emitting provenance labels before and after pytest. Therefore:

- `START_LOCAL = NOT_CAPTURED`
- `START_UTC = NOT_CAPTURED`
- `END_LOCAL = NOT_CAPTURED`
- `END_UTC = NOT_CAPTURED`
- `PYTEST_EXIT_CODE = NOT_CAPTURED`
- `PYTEST_REPORTED_DURATION_S = 55.22`
- `PYTEST_ASSERTION_RESULT = PASS`
- `DS12 = PASS_WITH_PROVENANCE_GAP`

Do not infer or write exit code 0. Do not reconstruct timestamps from estimates. Do not describe the wrapper as fully successful.

## A2.1 Baseline

Confirm without rerunning tests:

1. HEAD is still `b6326ad2`.
2. No appendix exists.
3. No tracked or staged content change exists after the blocker.
4. The A1 basetemp is absent.
5. All authorization keys remain false, promotion remains false, G2 remains absent, and `next_gate` remains `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`.

Any mismatch is STOP.

## A2.2 Sole appendix content

Create only:

`workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`

Record:

1. The exact pytest command already executed.
2. The full literal pytest output and all five PowerShell wrapper errors exactly as observed.
3. The A2.0 fields, including every `NOT_CAPTURED` value.
4. `VERIFICATION_INVOCATIONS 1`, `RETRY_COUNT 0`, `FAILING_IDS []`, and `BASE_TEMP_REMOVED true`.
5. The already collected A1.3 pre/post names/sizes/mtime_ns metadata tables for the 22 protected files. Use only values actually retained in the session; do not invent missing values.
6. The A1.3 revised closure fields:

```text
ORIGINAL_PRE_SNAPSHOT_PERSISTED false
DS13_CLOSURE_BASIS revised_A1_metadata_consistency
POST_METADATA_CONSISTENT_WITH_ACCEPTED_PREPACKET_BASELINE_AND_PACKET_ZERO_PATH_TOUCH true
```

7. Final closure:

```text
DS12 PASS_WITH_PROVENANCE_GAP
DS13 PASS_UNDER_A1_REVISED_CRITERION
DS15 PASS
FORMAL_G1_RERUN false
SCIENTIFIC_DECODER_CALLS 0
G2_EXECUTED false
G2_PRESENT false
PUSHED false
```

If the retained A1.3 metadata table is unavailable or incomplete, STOP and report exactly which metadata values are missing. A fresh post-only stat may not be substituted for the already observed before/after table without another author ruling.

## A2.3 Commit

Do not edit any existing file. Stage exactly the appendix and verify staged count 1 plus `OUT_OF_SCOPE []`.

Commit:

```text
test(v72p2d5): add independent decomposition successor closeout evidence

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

Do not push.

## A2.4 Return

Report only:

- appendix commit SHA and one-file manifest;
- literal pytest summary and the five `NOT_CAPTURED` provenance fields;
- DS12/DS13/DS15 final verdicts;
- protected metadata before/after equality result;
- current authorization, G2, gate, staged/content-diff, and no-push state;
- confirmation that pytest, decoder, and every `--phase` were not rerun.

Do not start the graph/mother successor. The next separate paired task will own that work.

