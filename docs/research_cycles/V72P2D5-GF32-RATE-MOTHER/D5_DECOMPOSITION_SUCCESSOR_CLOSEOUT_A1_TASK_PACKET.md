# D5 decomposition successor closeout A1 task packet

Status: `AUTHOR_CORRIGENDUM / VERIFICATION_ONLY / NO_DECODER_AUTHORIZATION`

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Branch: `formal-ir-v72p1-addendum-clean`

Expected packet HEAD: `b6326ad2` with local predecessors `34e7adda` and `e4d3af7`; do not require origin equality and do not push.

This A1 replaces only DS12 and DS13 of `D5_ROUTE_STOP_AND_DECOMPOSITION_SUCCESSOR_R1_TASK_PACKET.md`. All other requirements and prohibitions remain unchanged.

## A1.0 Author decisions

Q1: **YES.** One fresh independent verification invocation of the exact four-file pytest suite is authorized. This is a test-only verification run, not a scientific decoder rerun. No retry is authorized.

Q2: **YES.** One read-only metadata collection over the named protected roots is authorized. Reading directory entries and file `name`, `size`, and `mtime_ns` does not count as touching or modifying evidence. File contents and hashes remain prohibited.

The missing historical pre-snapshot may not be fabricated. DS13 is revised from literal same-session pre/post equality to the evidence standard in A1.3.

## A1.1 Baseline and hard stops

Before the verification run:

1. Confirm branch and that `b6326ad2` is HEAD.
2. Confirm commits `34e7adda`, `e4d3af7`, and `b6326ad2` have the reported manifests.
3. Confirm scoped tracked and staged content diffs are empty.
4. Confirm all nine execution authorization keys are false, `scientific_promotion: false`, and `next_gate: D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`.
5. Confirm G2 is absent.
6. Confirm the only intended new path is:
   `workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`

Any mismatch is STOP. Do not clean the known CRLF/porcelain churn.

## A1.2 Revised DS12 — exactly one fresh pytest verification

Generate one UUID once and use it only in this basetemp path:

`workspace/d5_decomposition_successor_r1_tests_a1_<uuid>`

Run exactly once:

```powershell
python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py comparison_bench/tests/test_v72p2d4r2_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_decomposition_successor_r1_tests_a1_<uuid> -q --tb=line
```

Capture in the appendix:

- exact expanded command;
- local and UTC start/end times;
- exit code;
- literal pytest summary line;
- warning summary;
- every failing test ID, or `FAILING_IDS []`;
- statement `VERIFICATION_INVOCATIONS 1`.

PASS requires exit 0 and zero failures. A changed pass count is informational if zero failures; explain it, do not rerun. Any failure, launch error, timeout, or command deviation is STOP with raw output. No retry or repair.

After the process exits, resolve the basetemp absolute path, verify it is inside the repository `workspace` directory and matches the generated task prefix, then remove only that basetemp. Record `BASE_TEMP_REMOVED true`. Do not remove any other path.

## A1.3 Revised DS13 — metadata-consistent non-mutation closure

Collect read-only metadata for exactly:

- `workspace/v72p2d5_g1/20260907_r2`
- `workspace/v72p2d5_model_f_input/20260907_r1`
- `workspace/v72p2d5_p0_cost/20260906_r1`
- `workspace/v72p2d5_g0/20260905_r2`
- `workspace/v72p2d5_g0_recovery/20260906_r1`
- the accepted D5 structure root named in existing cycle documents
- `workspace/v72p2d5_g2` and its proposed formal child, which must remain absent

For each present root, record:

- resolved root path;
- direct child directory list, which must be empty for these flat evidence roots;
- sorted direct file names, sizes, and `mtime_ns`.

Do not open file contents and do not hash files.

Revised DS13 passes only if all of the following hold:

1. G2 and its proposed formal child are absent.
2. Every expected protected root/file is present with the accepted file-name and size inventory recorded by prior accepted independent reviews/cycle documents.
3. Every protected file's current `mtime_ns` predates the first new-score event of this packet (`2026-09-08 13:29:10` Asia/Shanghai; also record the corresponding UTC instant).
4. No protected-root path appears in `git diff d6fabf09..b6326ad2 --name-only`.
5. The packet's development root is distinct from every protected root.
6. Current metadata remains identical before and after the A1 pytest verification.

This supports the precise statement:

```text
POST_METADATA_CONSISTENT_WITH_ACCEPTED_PREPACKET_BASELINE_AND_PACKET_ZERO_PATH_TOUCH
```

It does **not** support the false statement that an unpersisted original same-session pre-snapshot was recovered. Record:

```text
ORIGINAL_PRE_SNAPSHOT_PERSISTED false
DS13_CLOSURE_BASIS revised_A1_metadata_consistency
```

If an inventory/size disagrees, a protected mtime is at or after the cutoff, a subdirectory appears, or G2 exists, STOP. Do not inspect contents, repair timestamps, delete anything, or reinterpret the mismatch.

## A1.4 Sole appendix and fourth commit

Create exactly one new file:

`workspace/d5_decomposition_successor_r1_c765e3010674/TEST_EVIDENCE_APPENDIX.log`

It contains the complete A1.2 test evidence and A1.3 metadata tables, plus:

```text
DS12 PASS
DS13 PASS_UNDER_A1_REVISED_CRITERION
DS15 PASS
FORMAL_G1_RERUN false
SCIENTIFIC_DECODER_CALLS 0
G2_EXECUTED false
G2_PRESENT false
PUSHED false
```

Do not edit the existing report, state, decision log, memory, scripts, code, tests, OpenSpec, or any other evidence file. The existing report's `259 passed` line remains a historical operator assertion; this appendix records the independently witnessed fresh verification result without rewriting history.

Stage only the appendix, verify staged count 1 and `OUT_OF_SCOPE []`, then commit:

```text
test(v72p2d5): add independent decomposition successor closeout evidence

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

Do not push.

## A1.5 Closure review and return

After commit, independently read back the appendix and confirm:

- DS12 passes from the recorded fresh command and exit.
- DS13 passes only under the revised A1 criterion, with the original missing pre-snapshot explicitly disclosed.
- DS15 passes with four packet commits total and no out-of-scope path.
- all other DS verdicts from the blocker report remain unchanged.
- `next_gate` remains `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`.

Return:

1. exact pytest command, exit, literal summary, and failing IDs;
2. protected-root metadata table and cutoff comparison;
3. DS12/DS13/DS15 closure verdicts;
4. appendix commit SHA and exact one-file manifest;
5. final authorization/gate/G2/status values;
6. confirmation of no decoder, no phase, no formal-root content read/write, no retry, and no push.

Do not start the graph/mother successor in this A1. Its proposal is the next separate paired task.

