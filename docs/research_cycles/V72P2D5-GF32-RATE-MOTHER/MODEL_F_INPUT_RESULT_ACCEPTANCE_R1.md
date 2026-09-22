# Model-F input result acceptance R1 — 20260907

Decision authority: user, 2026-09-07, explicit.
Verdict: `MODEL_F_INPUT_RESULT_ACCEPTED`.
Scope: documentation + cycle-state record only. No execution, no
authorization, no promotion, no artifact modification.

## A01 Subject accepted

Artifact root: `workspace/v72p2d5_model_f_input/20260907_r1/`

| file | size_bytes | mtime_ns |
| --- | --- | --- |
| model_f_input.npz | 208467 | 1788718027043698800 |
| model_f_input_summary.json | 752 | 1788718027043698800 |

Content: canonical Model-F CAL-TRAIN input, full-CAL refit after the frozen
lambda selection. `CAL702..1725`, 1024 frames x 256 pairs = 262144 symbols,
`counts_ab` int64 `(1024,1024)` axis `(Alice,Bob)`, `p_b` float64 `(1024,)`
derived from `axis0`, `lambda_star=137.3823795883264`.

## A02 Basis of acceptance

- Implementation acceptance: `IMPLEMENTATION_ACCEPTANCE_R2.md`.
- Pre-EXECUTE review: `MODEL_F_INPUT_PRE_EXECUTE_REVIEW_R2.md`, PASS
  (PX01-PX20 after the PX11 path fix; the prior R1 FAIL is preserved).
- Execution: exactly one authorized `prepare` plus one authorized `verify`,
  2026-09-07. Authorization consumed; replay forbidden.
- Pre-RESULT review R1: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md`,
  `PRE_RESULT_REVIEW_FAIL` on the single blocker PR16. Preserved, not deleted.
- Disposition: `G1_UNAUTHORIZED_DISPOSITION_R1.md`, `VOID_RETAINED_IN_PLACE`.
- Pre-RESULT review R2: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md`,
  `PRE_RESULT_REVIEW_PASS` / `READY_FOR_MAIN_RESULT_ACCEPTANCE`, C01-C11 all
  PASS, `195 passed`.

## A03 PR16 was cleared by record, not by condition

This is the material caveat of this acceptance and must not be summarised away.

R1's PR16 was the formal check "formal roots absent". That condition is NOT
met: `workspace/v72p2d5_g1/20260906_r1/` still exists on disk. R2 cleared PR16
by reinterpreting it through its intent — unauthorized numbers must not enter
the result chain — and judging that intent closed by the
`VOID_RETAINED_IN_PLACE` disposition (retention as forensic evidence, absolute
citation ban, new-root requirement for any future authorized G1, unchanged
lifecycle).

Anyone reading this record later must understand: PR16 was not physically
cleared. A rule was reinterpreted, under an explicit user decision that
rejected both deletion and quarantine-move.

## A04 What is accepted

Accepted: the frozen Model-F CAL input is internally consistent, canonically
oriented `(Alice,Bob)`, with an exactly derived `P(B)` marginal, and is
suitable as the P0/G1/G2 prior input.

## A05 What is NOT accepted and NOT claimed

No FER. No leakage. No secret-key rate. No net key. No qualification. No
verdict on NB-LDPC or the dv3 mother. No G1 performance conclusion — the voided
`app_exact 0` / `app_failure 1.0` / `oracle 0` numbers carry zero scientific
meaning. No P0/G1/G2 authorization. No scientific promotion.

## A06 Artifact status field unchanged

The artifact's `status` stays `MODEL_F_INPUT_CANDIDATE`. Changing it would
require rewriting a file inside a protected immutable root, which is forbidden.
Acceptance is recorded at the cycle level in `cycle_state.yaml`. The loader
accepts both `CANDIDATE` and `ACCEPTED`, so no consumer breaks.

## A07 Residual risks carried into P0

- `R-R1`: production-side bare-authorized defaults are unchanged; the
  recurrence guard is test-side only. Future P0/G1/G2 packets MUST re-verify
  isolation before any authorization.
- `R-R2`: `M24`/`P12` no longer assert global formal-root absence
  (lifecycle-independent snapshots instead); an unexpected new formal output
  would rely on per-test snapshot comparison, not a global gate.

## A08 Lifecycle effect

- Model-F input: `ACCEPTED`.
- All nine `*_execution_authorized`: `false`, unchanged.
- `scientific_promotion`: `false`, unchanged.
- `next_gate`: `P0_PACKET_REVIEW`, unchanged.
- P0 is NOT authorized by this acceptance. P0, G1 and G2 each require their own
  packet review and their own separate explicit authorization.

## A09 Post-acceptance verification

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

Protected roots unchanged; `p0_cost` and `g2` still absent.
