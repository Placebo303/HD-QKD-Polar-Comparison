# D7 X1–X4 Execution Master Packet R1

## 1. Identity

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; verify, do not switch.
- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- OpenSpec: `openspec/changes/formal-ir-d7-root-cause-and-route-reset/`
- Accepted implementation boundary: Phases A–F, main-thread acceptance recorded in chat on 2026-09-13.
- Packet type: `ENTRYPOINT_CLOSEOUT + PRE_EXECUTE + CONDITIONAL_X1_X2_X3_X4 + PRE_RESULT`
- This is the sole operational packet for X1–X4. Do not create four successor packets unless the scientific contract changes.

Creating or handing off this packet is **not execution authorization**. Each X phase has its own user-only authorization flag and is consumed by its first attempted invocation.

## 2. Decision sequence

```text
P: close real entrypoints and independently review
  -> X1: true historical-decoder provenance probe
  -> main-thread X1 review
  -> X2: three-graph exploratory diagnostic
  -> independent Pre-RESULT + main-thread X2 review
  -> X3: reference ladder on frozen X2 f=1.2 failed call records
  -> independent Pre-RESULT + main-thread X3 review
  -> X4: frozen n=256 G2 length discriminator
  -> independent Pre-RESULT + main-thread route decision
  -> only then reconsider D7-H
```

No phase authorizes the next phase. X3 is not automatically skipped when X2 looks favorable; the main thread decides from X2. X4 is never bundled with X2/X3.

## 3. Current entrypoint gaps — Phase P must close these first

The implementation is scientifically ready but not yet operationally closed:

- Current `scripts/v72p2d7_consistency_multigraph.py --consistency` uses an injected synthetic stub. It is a useful equivalence check but is **not X1**, because it does not call `probe_historical_decoder_provenance(decode_fn=None)`.
- `run_reference_ladder` exists, but X3 has no complete frozen selector, authorization-gated CLI, additive writer, or replay verifier.
- The D5 G2 CLI reads the D5 cycle state and defaults to the accepted original G2 root. X4 needs an explicit, reviewed bridge from this cycle's X4 authorization to that exact D5 phase without enabling G1 or any other D5 phase.

Phase P is implementation/test/review work only. Production decoder/CAL/VAL calls must remain zero.

## 4. Allowed files

- `scripts/v72p2d7_consistency_multigraph.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` only if the existing public G2/probe API cannot support the frozen wrappers; prefer no edit
- `comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py`
- one new focused X1–X4 test file if keeping the existing test file readable requires it
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/**`
- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/**` only for a necessary delta caused by Phase P; do not redefine science
- this task packet and paired prompt

Read every existing file before editing it. Any required file outside this list is a hard STOP.

## 5. Forbidden scope

- No edits to historical G1/D7 evidence or accepted Model-F artifacts.
- No edits to frozen baseline `src/`, `experiments/`, historical `tools/`, sibling repositories, or unrelated dirty files.
- No graph/seed/threshold/arm replacement after observation.
- No retries, resumes, automatic continuation, cleanup, overwrite, parameter tuning, D7-H execution, real-data execution, push, or scientific promotion.
- Do not use `git add -A`, broad staging, stash, reset, checkout, or force operations.
- Tests must inject fakes and use fresh additive `workspace/v72p2d7_x1x4_test_<uuid>` roots.

## 6. Phase P — operational closeout

- **P01 X1 entrypoint**: add an explicit mode such as `--historical-provenance-probe` that calls `probe_historical_decoder_provenance(decode_fn=None)` exactly once, prints one JSON record, writes no file, creates no root, and refuses unless `x1_consistency_probe_authorized: true`. Keep existing synthetic `--consistency` behavior and rename its help/record meaning to `same-input synthetic consistency`; do not mislabel it X1.
- **P02 X1 result contract**: JSON fields include resolved decoder identity, provenance token, accepted flag, iterations, shape validity, finite status, decoder calls=`1`, writes=`0`. Exit 0 only when provenance is exactly `CHECK_UPDATED`, beliefs are finite and shape-valid, and iterations >=1; otherwise nonzero and retain stdout/stderr.
- **P03 X3 selector**: read only the immutable X2 root. Select every f=1.2 `call_records.csv` record whose executed arm is non-crash/nonfinite-safe but not exact. Preserve `(graph_idx, graph seeds, block seed, arm, role, rows, prior kind)` exactly. Do not replace or deduplicate scientifically distinct calls.
- **P04 X3 ceiling**: at most 192 selected failed call records and three ladder arms each, hence at most 576 decoder calls. Record actual selected records before binding a decoder. Zero selected records yields `X3_NOT_APPLICABLE_NO_FAILED_CALLS`, zero decoder calls, not success/failure.
- **P05 X3 reconstruction**: deterministically reconstruct each selected X2 H/prior/syndrome/truth from the manifest and record identity. Verify the reconstructed baseline `ROW_LAYERED_90` matches the stored X2 record before accepting the 360/flooding comparisons. First mismatch is `X3_BASELINE_REPLAY_MISMATCH_BLOCKED`; STOP, no later selected records.
- **P06 X3 evidence**: fresh root with `manifest.json`, `selected_records.csv`, `ladder_records.csv`, `paired_summary.csv`, `summary.json`, `report.md`, `command_log.txt`. Never overwrite. Claim label remains `STRONG_REFERENCE_DIAGNOSTIC`, not ML/information-theoretic evidence.
- **P07 X3 CLI**: explicit `--reference-ladder --x2-root <exact> --out-root <exact>`; require `x3_reference_ladder_authorized: true`; refuse before reading X2, binding decoders, or creating a root when false.
- **P08 X4 bridge**: add a narrow `--g2` mode to the current D7 master CLI, or a same-module wrapper, that requires `x4_g2_execution_authorized: true`, asserts every other D5 execution flag remains false, calls the existing `run_g2_synthetic(authorized=True)` exactly once, and writes only the original frozen fresh G2 root. Do not set the D5 `g2_execution_authorized` flag globally.
- **P09 X4 output**: exact root `workspace/v72p2d5_g2/20260906_r1`; it is currently absent. Abort if it exists. Existing four-file G2 schema plus additive per-layer/wall/RSS fields only.
- **P10 independent review**: run T0/T1 fake-injected tests, verify zero production calls and all dormant flags false, then obtain an independent implementation/Pre-EXECUTE readiness review. Stop at `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

Phase P acceptance must explicitly resolve the prior finding that `bind_reference_ladder_decoders` was unexercised: test binding/import/signatures without calling a production decoder, then perform a true-condition binding probe during X3 Pre-EXECUTE before authorization is consumed.

## 7. Frozen phase contracts

### X1 — historical provenance probe

- Authorization flag: `x1_consistency_probe_authorized`.
- Calls: exactly 1 historical row-layered decoder call on the built-in 2x2 GF32 fixture.
- Writes/output roots: zero; stdout/stderr transcript only.
- Budget: outer watchdog 120 s; RSS <2 GiB.
- Success condition: exact `CHECK_UPDATED`, finite shape-valid beliefs, iterations >=1, exit 0.
- Failure: any other return is `X1_PROVENANCE_PROBE_FAILED`; STOP. Do not retry or repair inside the execution attempt.
- Frozen command after P acceptance:

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --historical-provenance-probe
```

### X2 — three-graph exploratory diagnostic

- Authorization flag: `x2_multigraph_execution_authorized`.
- Exact input: `workspace/v72p2d5_model_f_input/20260907_r1`.
- Exact fresh root: `workspace/d7_r1_multigraph_20260913_r1` (currently absent at packet freeze).
- Frozen matrix: three graph pairs, 16 block seeds, f=`1.0,1.2`, four decoder arms; max 384 calls.
- Budget: total stored wall <=900 s; per-call watchdog 120 s; RSS <2 GiB.
- No rerun/resume/replacement. Resource/incomplete/crash terminal stops before X3.
- Frozen command after X2 Pre-EXECUTE PASS and explicit authorization:

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_r1_multigraph_20260913_r1 --wall-budget-s 900
```

### X3 — failed-record reference ladder

- Authorization flag: `x3_reference_ladder_authorized`.
- Exact read-only X2 root: `workspace/d7_r1_multigraph_20260913_r1`.
- Exact fresh root: `workspace/d7_r1_reference_ladder_20260913_r1` (currently absent at packet freeze).
- Frozen selector: Section P03; f=1.2 failed executed call records only.
- Arms: `ROW_LAYERED_90`, `ROW_LAYERED_360`, `FLOODING_90`; max 576 calls.
- Budget: total stored wall <=3600 s; per-call watchdog 480 s; RSS <2 GiB.
- Baseline replay equality is a hard gate before comparative interpretation.
- Frozen command after X3 Pre-EXECUTE PASS and explicit authorization:

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600
```

### X4 — G2 n=256 length discriminator

- Authorization flag: `x4_g2_execution_authorized`.
- Exact Model-F input is the accepted internal D5 root.
- Exact frozen fresh root: `workspace/v72p2d5_g2/20260906_r1` (currently absent at packet freeze).
- Matrix: n=256; f=`1.0,1.1,1.2`; rows L1=`196,215,235`; L2=`172,189,206`; 200 blocks per f; oracle subset 40 per f; max 1320 calls.
- Budget: total <=3600 s; single call <=120 s via outer ownership/watchdog; RSS <2 GiB.
- Four-state outcome only: `G2_SYNTHETIC_QUALIFIED`, `G2_INCONCLUSIVE`, `G2_CURRENT_CONFIGURATION_FAILED`, `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`.
- No automatic n=1024, G1 rerun, D7-H, tuning, or route promotion.
- Frozen command after X4 Pre-EXECUTE PASS and separate explicit authorization:

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --g2
```

## 8. Gate handling and authorization consumption

For each X phase:

1. Main thread records scoped code/config/packet cleanliness, exact command, target-root absence, budget/stop rules, focused tests, and explicit user authorization.
2. Set only that phase's flag true in `cycle_state.yaml`; commit ID is provenance, not authorization.
3. The first process-start attempt consumes authorization. Restore the flag false immediately after the attempt, regardless of success, refusal, crash, or timeout.
4. Preserve partial/failure evidence in place. Never delete or reuse its root.
5. Independent Pre-RESULT review checks actual records, denominators, missing calls, per-graph/per-arm breakdown, exact/syndrome separation, and claim ceiling before solidification.
6. Main thread accepts/rejects the phase and decides whether the next phase is scientifically warranted.

X1 has no result root; retain its literal command, exit code, stdout, stderr, start/end timestamps, watchdog disposition, and authorization-consumption record in the cycle docs only after independent review.

## 9. Hard STOP conditions

- Branch mismatch or scoped file drift that affects the phase.
- Required target root already exists.
- Missing independent review or explicit phase authorization.
- Any attempt to infer one phase's authorization from another.
- X1 provenance is not exact `CHECK_UPDATED` or its real entrypoint does not run exactly one decoder call.
- X2 incomplete/resource/crash/nonfinite terminal.
- X3 selector/reconstruction/baseline replay mismatch.
- X4 matrix, call ceiling, grading vocabulary, wall/RSS accounting, or output root differs from Section 7.
- Any historical result, Model-F input, frozen baseline, or unrelated dirty file changes.
- Any command requests retry, resume, seed replacement, parameter tuning, D7-H, real data, or n=1024 continuation.

On STOP: do not repair, retry, clean, advance, commit results, or create another packet. Return raw evidence and the single decision needed.

## 10. Return contract

Return exactly one of:

### COMPLETE

- phase/acceptance IDs completed;
- exact command, exit code, timestamps, calls, wall/RSS, root and files;
- primary per-graph/per-arm/per-f counts as applicable;
- claim ceiling and unsupported claims;
- independent review verdict;
- authorization flag restored false;
- next phase remains unauthorized;
- changed-file manifest, commits if any, and no-push confirmation.

### BLOCKED

- last completed gate;
- exact failing command/check and raw output;
- authorization consumed or not consumed;
- retained partial root/transcript;
- confirmation no later phase ran;
- one main-thread decision needed.

