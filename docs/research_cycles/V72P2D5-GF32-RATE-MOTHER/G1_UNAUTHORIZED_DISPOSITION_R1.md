# G1 unauthorized output disposition R1 — 20260907

Decision authority: user, 2026-09-07, explicit.
Disposition: `VOID_RETAINED_IN_PLACE`.
Scope: documentation only. No delete, no move, no rename, no copy, no hash,
no rerun, no authorization change, no code change.

## D01 Subject

Root: `workspace/v72p2d5_g1/20260906_r1/`
Files (stat only, pre- and post-disposition identical):

| file | size_bytes | mtime_ns |
| --- | --- | --- |
| execution_summary.json | 267 | 1788719732911457700 |
| report.md | 146 | 1788719732911457700 |
| results.json | 2593 | 1788719732909954400 |
| table.csv | 126 | 1788719732909954400 |

## D02 Status

`INVALID_UNAUTHORIZED_TEST_TRIGGERED` (unchanged from
`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` I01).
Now additionally and permanently marked `VOID`.

## D03 What VOID means

- The four files are retained as forensic evidence of the isolation defect only.
- They carry NO scientific meaning. The contained `decoder_calls=440`,
  `app_exact 0`, `app_failure 1.0`, `oracle 0` are NOT a G1 result, NOT a
  performance measurement, NOT an `exact_failure_fraction` verdict, and NOT
  evidence about the NB-LDPC method, the dv3 mother, the rate points, or the
  Model-F prior.
- They MUST NOT be cited by any future RESULT_SUMMARY, report, table, decision
  entry, or promotion argument.
- They do NOT consume, satisfy, or partially satisfy any G1 authorization.
- A future authorized G1 run MUST use a NEW output root and MUST NOT reuse,
  compare against, or overwrite this one.

## D04 Why retained in place

`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` I08 commits to no
delete/quarantine/move/rename/copy/normalize/hash. Retention in place is the
only disposition consistent with that commitment and with repository
failure-retention practice. Deletion and relocation were both explicitly
rejected by the user on 2026-09-07.

## D05 Root cause status

Test-isolation defect (incident I09). Repair completed and independently
evidenced in `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`: SAFE A/B/C containment,
stdlib AST static guard, 165 collected / 165 passed, focused 10 passed, zero
binder entries, zero writer entries, P0/G2 roots still absent.

## D06 Lifecycle effect

- `g1_execution_authorized` stays `false`.
- `next_gate` stays `P0_PACKET_REVIEW`.
- `scientific_promotion` stays `false`.
- No P0 authorization is granted or implied by this disposition.
- PR16 of `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` is addressed by RECORD, not by
  removal. Whether PR16 is thereby cleared is decided by an independent
  Pre-RESULT re-review, not by this file and not by the executing session.

## D07 Verification after disposition

Re-stat performed; the four G1 files, the two Model-F files, and both G0 roots
are byte-size and mtime identical to the pre-disposition snapshot. P0 and G2
roots remain absent.

```
ROOT workspace/v72p2d5_g1/20260906_r1 exists True
   execution_summary.json 267 1788719732911457700
   report.md 146 1788719732911457700
   results.json 2593 1788719732909954400
   table.csv 126 1788719732909954400
ROOT workspace/v72p2d5_model_f_input/20260907_r1 exists True
   model_f_input.npz 208467 1788718027043698800
   model_f_input_summary.json 752 1788718027043698800
ROOT workspace/v72p2d5_g0/20260905_r2 exists True
   execution_summary.json 385 1788626074451921900
   report.md 712 1788626074450889700
   results.json 2512 1788626074450889700
   table.csv 306 1788626074450889700
ROOT workspace/v72p2d5_g0_recovery/20260906_r1 exists True
   execution_summary.json 404 1788634063474539400
   report.md 722 1788634063474031500
   results.json 2531 1788634063472847300
   table.csv 306 1788634063473496200
ROOT workspace/v72p2d5_p0_cost/20260906_r1 exists False
ROOT workspace/v72p2d5_g2/20260906_r1 exists False
```
