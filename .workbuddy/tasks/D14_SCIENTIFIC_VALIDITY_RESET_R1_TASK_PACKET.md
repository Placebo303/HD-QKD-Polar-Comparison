# D14 Scientific Validity Reset R1 — Task Packet

## 1. Identity and boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d14-scientific-validity-reset`
- Track: `EXPLORE` for no-write synthetic calibration; implementation and
  documentation phases require no execution gate.
- No production decoder, DE sweep, real data, CAL/VAL resampling, D7-H, L2
  decoder batch, G1/G2 rerun, push, qualification, or publication claim.
- Start read-only. Preserve every existing result root byte-for-byte.

## 2. Accepted predecessor decisions

1. D13 is accepted as `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`; no decoder arm
   advances.
2. `LAMBDA_APPLICATION_CONTRACT_DEFECT` is accepted: per-cell pseudocount
   application is rejected; `prepare_model_f_prior_candidate` /
   `build_f_model_concentration` is the accepted concentration-backoff chain.
3. X4/G2 used `run_g2_synthetic`, which currently selects the rejected legacy
   prior. Its stored grade describes the executed configuration only and cannot
   establish n=256 finite-length failure.
4. The reported entropy/rate numbers (L1 4.2867, L2 3.2227 and effective
   factors 0.890/0.979/1.068) are hypotheses to reproduce from artifacts, not
   constants to copy into code or records without recomputation.

## 3. Phase S — preserve the milestone safely

Create a scoped inventory mapping every D8–D13/OpenSpec/code/test/cycle-doc
path and the shared `v72p2d5_gf32_rate_mother.py` changes to its originating
reviewed milestone. Identify tracked files containing mixed unrelated edits.

After the inventory is independently reviewed:

- make local, non-pushed commits only with explicit pathspecs;
- never use `git add -A`, `git add .`, bulk line-ending normalization, reset,
  checkout, clean, stash, or force operations;
- proposed groups: workflow foundation; shared D5/D7 compatibility; D8–D9;
  D10–D13; result/decision documentation;
- include code, tests, OpenSpec, and compact cycle records needed for
  reproduction; exclude workspace roots, pytest scratch, unrelated historical
  outputs, and line-ending-only files;
- if one tracked file contains inseparable unrelated changes, STOP that group
  and report the exact overlap. Do not stage partial hunks by guesswork.

Record commit IDs and manifests. Do not push or switch branches.

## 4. Phase P — correct production prior selection

Create the OpenSpec delta before behavior edits. Make the smallest change that
causes all three synthetic production entrypoints
`run_p0_cost_synthetic`, `run_g1_synthetic`, and `run_g2_synthetic` to select
the already accepted concentration-backoff prior. Remove stale docstrings that
call the rejected estimator the production source.

Add focused tests that exercise the real entrypoint selection, not merely an
injected `p_f` table:

- spy/monkeypatch both estimators and prove each entrypoint calls the candidate
  exactly once and never calls the legacy estimator;
- use a fake decoder and fresh scratch output only; zero production decoder;
- assert the selected prior is finite, normalized, non-uniform on the accepted
  Model-F fixture, and bitwise/numerically equal to direct candidate output;
- add a regression assertion preventing P0/G1/G2 from returning to
  `prepare_model_f_prior`;
- do not delete the legacy function because historical artifact reconstruction
  still needs its identity.

No P0/G1/G2 execution is authorized.

## 5. Phase C — immutable G2/X4 corrigendum

Add one clearly linked corrigendum to the D5 and D7 root-cause records:

- preserve `workspace/v72p2d5_g2/20260906_r1` unchanged;
- retain `G2_CURRENT_CONFIGURATION_FAILED` as the literal historical grade;
- state that it tested the rejected per-cell-prior configuration and is invalid
  as evidence for n=256 finite-length feasibility or route closure;
- supersede only the scientific inference, not the recorded execution;
- do not claim the prior defect is the unique cause of all failures;
- update stale D5/D7 status fields and decision/memory pointers additively.

## 6. Phase R — symmetric rate-calibration audit

Implement one small no-decoder audit module/script, reusing the accepted D8–D12
input and sampling helpers. It shall read only the accepted CAL-only Model-F
artifact and immutable synthetic result records.

Independently compute and persist:

- entropy of the actual synthetic generator for L1 and L2, with equations,
  axes, units, floor/renormalization order, and estimator identity;
- the CE constants used to choose rows, their provenance, and for every frozen
  f/width/layer: rows, disclosed bits, generator entropy load, nominal factor,
  and effective factor;
- per-block self-information for the frozen D12 and D11 block identities,
  joined to exact/syndrome outcomes without merging `undetected`;
- quantile-binned success counts and correlations as descriptive diagnostics;
- explicit separation between expected information load and finite-code/
  decoder success. Never label `I <= disclosed bits` sufficient for decoding;
- cross-check the claimed L1/L2 entropy values and report exact reproduced
  values or the mismatch and its cause.

Use a fresh additive audit root with CSV/JSON plus one concise report. No
decoder calls, no new random blocks, no seed search, and no real data.

## 7. Phase N — freeze the next experiment, do not run it

Using only the independently reviewed Phase R evidence, prepare the smallest
paired L1/L2 calibrated synthetic discriminator:

- rates/rows must be derived from the actual generator entropy or the generator
  must be changed to match the chosen CE; state which choice and why;
- include L055 and its frozen control on L1, plus an L2 DV3/oracle diagnostic;
- use paired blocks and multiple graph seeds; size the batch only to decide
  whether the next investment belongs to L1 construction or L2 degree design;
- preregister thresholds, calls, fresh root, command, and claim ceiling;
- leave it `READY_AWAITING_EXPLICIT_AUTHORIZATION` with root absent.

Do not automatically revive D7-H. It can only be reconsidered after calibrated
single-layer and forward baselines show that alternating transfer addresses the
remaining bottleneck.

## 8. Verification and independent review

- T0/T1: compile, focused prior-selection tests, audit math fixtures, and
  no-write/refusal checks in fresh `workspace/` basetemps.
- Run broader suites only if a focused failure or shared-D5 change creates a
  concrete compatibility concern; do not repeat already trusted reviewer-go
  evidence ceremonially.
- Independent reviewer must have actual artifact access and separately verify:
  commit manifests/scope, entrypoint estimator selection, unchanged historical
  roots, corrigendum wording, both-layer entropy/rate arithmetic, per-block
  joins, next-batch thresholds/budgets, and zero decoder/real-data calls.
- Reviewer returns `EVIDENCE_ACCESS: VERIFIED`, verdict, blocking findings,
  and exact corrections. Blocking inconsistency stops readiness.

## 9. Return contract

Return `D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`
only when Phases S–N and independent review pass. Report:

- scoped commits and excluded dirty paths; no push;
- exact production-wiring delta and focused tests;
- G2/X4 corrigendum locations and unchanged-root proof;
- reproduced L1/L2 entropy, nominal/effective factors, and per-block findings;
- frozen next batch packet/root/command/budgets, still unauthorized;
- all findings and claim boundaries.

On any blocker, return the raw command/output, attempted safe checks, and the
single decision needed. Do not self-authorize scientific execution.
