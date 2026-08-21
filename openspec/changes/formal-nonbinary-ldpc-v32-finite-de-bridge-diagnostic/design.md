# Design: formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic

## 0. Overview

V32 is a single-purpose diagnostic bridge over the frozen V31 n=1024 failure. It changes nothing upstream (packet, allocation, posterior, decoder are all read-only bindings) and adds one harness that executes six pre-registered arms (B0–B5), persists per-block evidence, and maps the observed pass/fail pattern onto exactly one of nine frozen terminals via a complete truth table. Attribution is the product; no qualification or promotion semantics exist anywhere in this change.

Ponytail discipline: one harness CLI + one test file; stdlib + already-installed deps (`numpy`, `pandas`, `pyyaml`, `pyarrow` optional); no new dependency, no caching layer, no retry framework. The only genuinely non-trivial logic is the exact-resume ledger and the terminal truth table — both get explicit tests.

## 1. Input Bindings (frozen)

Identical to `proposal.md §Frozen Input Bindings` (9 rows: V31 QC packet / validation blocks+frames / per-block baseline; V25 run_04 empirical channel; V26 run_02 F03/A02 allocation; V28R decoder interface; GF(32) field identity with `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`; `m1=16`; three frozen source IDs). The harness verifies every binding at start (stage 0) and records their identities in `RUN_MANIFEST.json`. Any binding mismatch → stop, terminal `bridge_binding_fail`.

## 2. Arms and Pairing Logic (frozen)

| Arm | Blocks | Channel/errors | L1 mode | Truth markers |
|---|---|---|---|---|
| B0 noiseless control | 2/source × 3 = 6 | noiseless | n/a (no errors) | plumbing control |
| B1 iid synthetic + oracle L1 | 20/source × 3 = 60 | matched iid synthetic (V25/V26 posterior) | oracle L1 | `truth_used=true, truth_role=oracle_l1, operational=false, qualification=false` |
| B2 Bob-only sequential | same 60 blocks as B1 | identical channel samples to B1 | Bob-only sequential | same markers as B1 |
| B3 shuffled real-error surrogate | 20/source × 3 = 60 | deterministic permutation of EXACTLY the B4 block set (blocks 0–19/source; counts/marginals preserved) | oracle L1 (same as B1/B4, so B1↔B3 differ only in error structure) | truth used to build fixture ONLY, never decoder input |
| B4 real retrospective oracle-L1 | blocks 0–19/source × 3 = 60 | real V31 validation errors | oracle L1 | `truth_used=true, truth_role=oracle_l1, operational=false, qualification=false` |
| B5 V31 baseline import | 300 records | — (read-only import) | — | no decoder invocation, no regeneration |

Frozen seeds (B1/B2): 1M `320101–320120`; 1.5M `320201–320220`; 2M `320301–320320`. B3 permutation rule + seed: derived deterministically from the frozen block identity, fixed and recorded in `RUN_MANIFEST.json` BEFORE any B3 execution; never selected by results. B0 seeds: deterministic constants derived from the frozen harness config, recorded in `RUN_MANIFEST.json` before execution.

Pairing isolations:
- **B1 ↔ B2**: only delta is oracle L1 → Bob-only sequential L1 ⇒ isolates **L1→L2 sequential propagation**.
- **B1 ↔ B3**: only delta is error source (iid matched vs permuted-real marginals) ⇒ isolates **real error structure beyond marginals**.
- **B3 ↔ B4**: permuted-marginals vs actual real errors ⇒ permutation-sensitivity check inside the real domain.
- **B1 ↔ B4**: matched synthetic vs real under identical graph/posterior/oracle-L1 ⇒ separates decoder-capability from input-distribution effects.
- **B5**: anchors every comparison to the canonical V31 numbers without re-execution.

Discriminator (development only): arm pass = ≥19/20 block successes per source; block success = `exact && tag && syndrome && !false_accept`; B0 requires 6/6 exact/tag/syndrome with 0 false accept. "B2 显著低于 B1" is operationalized deterministically as: B2 arm FAIL under this same discriminator while B1 arm PASS. No additional statistics are invented post-hoc.

Posterior anomaly (pre-registered for the truth table): a calibration-bucket anomaly or NLL outlier of the real posterior on B3/B4 blocks, judged against criteria written into `RUN_MANIFEST.json` before B3/B4 execution (frozen V25/V26 reference NLL/calibration behavior). Never evaluated or tuned after seeing decode outcomes.

Aggregation rule: summaries are stratified by arm and truth-role. Synthetic (B1/B2), oracle-L1 diagnostic (B3/B4), and imported operational baseline (B5) MUST NOT be blended into a single FER.

## 3. Per-Block Metrics (all fields land in `per_block.jsonl`)

Every decoded block persists one JSONL line immediately on completion, containing at least:

```
arm
source                       # type2_1M_20260121_184040 | type2_1p5M_20260121_183806 | type2_2M_20260121_183657
seed_or_block_id             # frozen seed (B1/B2) or real block ID (B3/B4)
graph_packet_identity        # hash/ID of the bound V31 n=1024 QC packet
posterior_identity           # hash/ID of the bound V25 run_04 / V26 run_02 posterior
truth_use                    # truth_used, truth_role, operational, qualification flags
l1_errors_initial            # oracle mode: 0 by construction; sequential: measured
l1_errors_final
l2_errors_initial
l2_errors_final
exact                        # bool
tag                          # bool
false_accept                 # bool
syndrome                     # converged flag
unsatisfied_checks           # count
iterations                   # decoder iterations used
terminal_decoder_status      # verbatim decoder status string, never remapped
runtime_s
posterior_nll
posterior_entropy
truth_symbol_rank            # rank of true symbol in decoder posterior ordering
calibration_bucket           # pre-registered bucket id
residual_syndrome_stats      # residual syndrome / check statistics
```

`terminal_decoder_status` values are recorded as produced by the frozen V28R decoder interface; V32 must not silently convert failure statuses into success (repository rule §5.5).

## 4. Run Rules (frozen)

### 4.1 Output root & collision

- Unique output root: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/`.
- If it already exists → STOP: implementation/output collision. No overwrite, no automatic `run_02`. A new run root requires an explicit main-thread decision recorded before any new execution.

### 4.2 Resource budget

- Budget: **12 hours cumulative wall-clock** across the whole run including resumed segments.
- Cumulative elapsed time is persisted in `resource_ledger.json`; resume NEVER resets the meter.
- `resource_ledger.json`, `progress.json`, `per_block.jsonl` are maintained under the run root; each completed block is persisted immediately (crash-safe by construction of append-only JSONL + persisted meter).
- Exhaustion of the cumulative budget → stop, terminal `resource_blocked`.

### 4.3 Exact resume (pre-registered)

- Resume restores ONLY the same `run_01`.
- Completed blocks are never repeated; block identity is unique across the run.
- Resume requires seed/input/code/config consistency with the interrupted run; any drift → refuse resume.
- Cumulative wall-clock continues across resume (never reset).
- The resume reason is written to `resource_ledger.json`.
- Resume from a scientific failure terminal is forbidden (scientific terminals are final).
- Resume must not be used to modify arms, blocks, thresholds, or any frozen quantity.
- If the same block appears twice in `per_block.jsonl` → evidence inconsistent → stop.

### 4.4 Execution order (fixed)

```
binding verification → B5 read-only import → B0 → B1 → B2 → B3 → B4 → terminal reconstruction
```

No reordering, no interleaving, no omission.

### 4.5 Early-stop whitelist (exhaustive)

Early stop is allowed ONLY for:
1. binding failure;
2. B0 failure;
3. implementation exception;
4. output collision;
5. cumulative 12h exhausted;
6. canonical/input drift;
7. truth-use violation.

Forbidden early-stop reasons (explicitly): bad B1 results, single-source early failure, intermediate trends, saving time. B2/B3/B4 are always executed once B0 has passed and no whitelist condition fired, regardless of how B1 looks.

## 5. Terminal Decision Procedure — Complete Truth Table (frozen)

### 5.1 Gate layer (evaluated in execution order; first match wins)

| Gate | Condition | Terminal |
|---|---|---|
| G-binding | Stage-0 binding verification fails (any of the 9 bindings) | `bridge_binding_fail` |
| G-B5 | B5 import integrity fails (record count ≠ 300, identity mismatch vs canonical, missing file) | `bridge_binding_fail` |
| G-B0 | B0 fails its 6/6 requirement (clean run, no exception) | `bridge_binding_fail` |
| G-drift | Canonical/input drift detected mid-run | `bridge_binding_fail` |
| G-exc | Unhandled implementation exception at any stage | `implementation_blocked` |
| G-truth | Truth-use violation detected (truth leaked into B2/B3 decoder inputs) | `implementation_blocked` |
| G-coll | Output collision (run root pre-exists) | STOP before any execution; recorded as implementation stop |
| G-res | Cumulative 12h exhausted | `resource_blocked` |

### 5.2 Scientific attribution table (requires B0 PASS, B5 OK, no gate fired)

Arm outcome definitions: PASS/FAIL per §2 discriminator. "anomaly" = pre-registered posterior calibration/NLL anomaly present (§2).

| Row | B1 | B2 | B3 | B4 | Terminal | Rationale |
|---|---|---|---|---|---|---|
| R01 | P | P | P | P | `bridge_pass_ready_for_successor` | no tested dimension reproduces the V31 failure |
| R02 | P | P | P | F | `real_error_structure_mismatch` | frozen rule: B1✓ B3✓ B4✗ |
| R03 | P | P | F | P | `bridge_inconclusive` | B3✗ alone without anomaly; B4✗ expected if structure were the cause — evidence conflicts |
| R04a | P | P | F | F | `empirical_channel_model_mismatch` | B3✗ WITH pre-registered posterior anomaly |
| R04b | P | P | F | F | `bridge_inconclusive` | B3✗ + B4✗ WITHOUT anomaly: structure vs model inseparable |
| R05 | P | F | P | P | `l1_sequential_propagation_limit` | frozen rule: B1✓, B2 significantly below B1 |
| R06 | P | F | P | F | `bridge_inconclusive` | dual positive: L1 limit AND real structure mismatch |
| R07 | P | F | F | P | `bridge_inconclusive` | dual positive: L1 limit AND B3✗ (no anomaly) |
| R08 | P | F | F | F | `bridge_inconclusive` | multi-positive (≥2 patterns); anomaly if present is recorded but does not override |
| R09–R16 | F | * | * | * | `finite_graph_decoder_mismatch` | frozen rule dominates: B0✓ + B1✗ means the fixed QC graph + L2 decoder fails under ideal conditions; B2/B3/B4 are still executed (§4.5) and recorded as supporting evidence |

R09–R16 explicitly covers all eight (B2,B3,B4) combinations when B1=FAIL; they share one terminal by the frozen minimum decision logic. Contradictory downstream observations (e.g., B4 PASS while B1 FAIL) are recorded in the run report as documented anomalies but do not change the terminal.

Notes:
- B2 PASS but numerically below B1 (still ≥19/20 everywhere) is a PASS; the gap is reported, terminal unaffected.
- Any combination not listed above (including malformed metrics preventing classification, or partial executions stopped by whitelist gates) maps uniformly to `bridge_inconclusive`.
- No terminal may be invented, renamed, or re-mapped after results are seen.

## 6. Test Tiers (frozen)

All tests run in a fresh writable root `workspace/<v32>/<uuid>/` with `pytest -p no:cacheprovider --basetemp <that root>`; legacy ACL-afflicted temp directories are never touched. Tests NEVER implicitly invoke production decoders/pipelines — fake runners are passed explicitly.

- **T0 structural**: compile/import; GF(32)/field binding (`field_id` match); fixed QC packet identity; B0 tiny noiseless case; B1/B2 same-block identity; B3 deterministic permutation reproducibility; B5 performs no decoder invocation; output collision refusal; no production execution from tests.
- **T1 focused tamper** (at least): seed drift; block ID drift; graph packet drift; posterior binding drift; B1/B2 block mismatch; truth leakage into B2/B3; duplicate block; resource meter reset; illegal resume; terminal tamper; source label tamper; partial JSONL; B5 re-executing decoder; output overwrite.
- **T2 full fake qualification**: complete fake B0–B5 via explicit fake runner; at least one fixture per major terminal; truth-use audit; exact resume; 12h resource simulation; independent terminal reconstruction from persisted JSONL reproduces the classified terminal.
- **T3 read-only regression**: V25 binding intact; V26 allocation intact; V28R decoder interface unchanged; V31 QC packet unchanged; V31 B5 import consistency; canonical/frozen directories show zero modification.

T2/T3 run only at milestones (after P2R candidate assembly and after formal run respectively).

## 7. Documentation Update Timing & Candidate-Only Handoff (frozen)

- After spec freeze, the implementation phase may update ONLY: V32 `tasks.md`, test evidence, candidate manifest.
- During the formal run phase, writes are limited to: `run_01` raw evidence, `resource_ledger.json`, `progress.json`, `per_block.jsonl`, operator logs.
- FORBIDDEN during the run phase: edits to `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`, final report, archive actions, promotion documents.
- At long-run end, the operator produces a CANDIDATE-ONLY handoff: `workspace/nbldpc_v32_finite_de_bridge/OPERATOR_HANDOFF.md` and/or `operator_handoff.json`, `candidate_recount.json`, `candidate_terminal.json` under the evidence root — each marked `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false`.

## 8. Autonomy Boundaries (frozen)

Implementation agents MAY autonomously decide: internal function/file structure; minimal data structures; fixture organization; CLI parameter details; JSON field layout within §3's required fields; progress display; exact-resume implementation details; Windows writable basetemp selection; ordinary bug fixes inside the frozen scope; T0–T3 test split; internal agent division of labor.

The following require STOP and escalation to main (never autonomous): modifying B0–B5 definitions; changing seeds/block IDs; changing the 19/20 discriminator; expanding sample sizes; adding n=2048; extending the 12h budget; new matrix or new decoder; re-estimating the posterior; automatic `run_02`; rerunning failed blocks; changing terminals based on results; starting V33 or NB-Polar; writing qualification/promotion statements; push; reading raw `.ttbin`; overwriting existing evidence.

## 9. Constraints Enforcement

- Static check (T0): harness imports no raw-data readers; no `.ttbin` path appears anywhere in V32 code.
- Static check (T0): B5 code path contains no decoder invocation (grep-clean for decoder entry points).
- Filesystem assertion: all writes resolve under the single run root; canonical roots opened read-only.
- Every `ponytail:` simplification names its ceiling and upgrade path.
