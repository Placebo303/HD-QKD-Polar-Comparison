# D5 route-stop acceptance + decomposition successor R1 task packet

Status: `FROZEN_TASK_PACKET / DEVELOPMENT_ONLY / NO_FORMAL_EXECUTION_AUTHORIZATION`

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Branch: `formal-ir-v72p1-addendum-clean`

Expected starting HEAD: `d6fabf09` (documentation commits created by this packet may advance HEAD)

Operator role: strong implementation/research operator. You may autonomously complete every phase below without routine check-ins. You may not redefine the scientific family, thresholds, claim boundary, or formal-execution lifecycle.

## 0. Objective and mainline decision

The independently reviewed terminal is accepted as the routing premise:

```text
D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED
reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY
```

This closes only the current fixed decomposition `A = 32*U1 + U2` combined with the current rate-mother/BP operating path. It does not close GF32 or NB-LDPC.

The successor is not a horizontal survey. It directly attacks the highest-ranked mainline uncertainty: whether the fixed high-five/low-five decomposition created the L1 bottleneck. Exhaust the complete family of reversible ordered 5-of-10 bit partitions, select without decoder outcomes using CAL-only held-out scoring, and then run a bounded paired development decoder discriminator.

Do not proceed to graph/mother redesign or BP scheduling in this packet. Those are fallback routes only after this family reaches a terminal.

## 1. Hard prohibitions

Throughout this packet:

- Do not run any CLI `--phase`, including `g1`, `g2`, `p0-cost`, `g0`, or `structure`.
- Do not rerun, resume, overwrite, reinterpret, or modify either G1 formal root.
- Do not execute G2 or create any `workspace/v72p2d5_g2*` root.
- Do not read VAL, real-IR, raw detector data, or any parquet rows outside frozen CAL-TRAIN 702..1725.
- Do not open or use numbers from the VOID G1 root `workspace/v72p2d5_g1/20260906_r1`.
- Do not modify accepted Model-F or formal G1 artifacts.
- Do not change any `*_execution_authorized`, `scientific_promotion`, accepted formal result, frozen G1 constants, or formal production wiring.
- Do not modify the frozen baseline under `src/`, `experiments/`, or `tools/`.
- Do not push, force, reset, checkout, stash, clean, amend, rebase, normalize line endings, or delete unrelated files.
- Do not use decoder outcomes to select a bit partition, row count, seed, graph, or hyperparameter.
- Do not expand into arbitrary GL(10,2) transforms, graph search, mother search, decoder schedule search, damping search, or seed search.
- Do not claim FER, leakage, key rate, qualification, promotion, real-data performance, G2 readiness, or a universal BP threshold result.

All decoder calls in this packet are development-only, must use explicit injection, and must write only to a fresh UUID-named development root.

Any violation or any ambiguity that changes the frozen family or terminal rules is a hard STOP. Return the exact command/output and the single decision needed. Do not self-authorize an expanded family.

## 2. Baseline gate

Before writing:

1. Confirm branch `formal-ir-v72p1-addendum-clean` and that `d6fabf09` is in the current history.
2. Confirm `D5_ROUTE_STOP_REVIEW_R1.md` exists with sole verdict `D5_ROUTE_STOP_REVIEW_PASS`.
3. Confirm its closure text and scope match §0.
4. Confirm all nine execution authorization keys are false, `scientific_promotion: false`, and `next_gate: D5_ROUTE_STOP_REVIEW`.
5. Snapshot by names, sizes, and `mtime_ns`:
   - accepted G1 `workspace/v72p2d5_g1/20260907_r2`;
   - accepted Model-F `workspace/v72p2d5_model_f_input/20260907_r1`;
   - P0, G0, G0-recovery, and structure roots;
   - confirm G2 absent.
6. Use `git diff --numstat` and `git diff --cached --numstat` for content cleanliness. Porcelain-only CRLF churn is informational and is not a stop.
7. Establish an explicit allowlist for every file created or edited by this packet. Preserve all unrelated dirty/untracked files.

Any scientific-state mismatch is a STOP. A content-clean scoped tree plus known EOL churn is not a mismatch.

## 3. Phase A — accept and land route-stop review

Read the untracked review file first. Create/append only:

1. Land unchanged:
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_REVIEW_R1.md`
2. Create:
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_ACCEPTANCE_R1.md`
3. Append only:
   `docs/decision-log.md`
4. Append only:
   `AGENT_PROJECT_MEMORY.md`
5. Edit only the necessary keys in:
   `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`

The acceptance must state:

- `D5_ROUTE_STOP_REVIEW_PASS` is accepted.
- Terminal: `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`.
- Reason: `ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY`.
- Scope is exactly the current fixed high-five/low-five, two-layer rate-mother/BP path.
- GF32/NB-LDPC remains open.
- Formal G1 remains accepted as completed-no-signal failure and is not rewritten.
- G2 remains unauthorized and absent.
- The chosen successor is the reversible 5+5 bit-partition decomposition discriminator.

Add state keys with the repository's existing YAML scalar style:

```yaml
d5_route_stop_review: PASS_R1
d5_current_path_stopped: true
d5_stop_scope: CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH
d5_stop_reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY
next_gate: D5_DECOMPOSITION_SUCCESSOR_PREREG
```

Stage exactly those five paths, inspect the staged manifest and diff, then commit:

```text
docs(v72p2d5): accept current-path stop and select decomposition successor

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

Do not push.

## 4. Phase B — preregister before any new scores or decoder calls

Create exactly one preregistration document and commit it before calculating candidate scores or invoking the decoder:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_PREREG_R1.md`

It must freeze §§4.1–4.7 verbatim in substance. It may add explanatory prose, but may not change the family, ordering, thresholds, or budgets.

### 4.1 Candidate family

Interpret each Alice symbol `A in [0,1023]` as ten little-endian bits `b0..b9`.

For every ordered first-layer subset `S1`, where `S1` is one of all `C(10,5)=252` sorted five-bit subsets:

- `S2` is the sorted complement.
- `U1` packs bits in `S1` in ascending source-bit order.
- `U2` packs bits in `S2` in ascending source-bit order.
- reconstruction places those bits back into their original positions.

This is a complete, finite family of 252 reversible bit permutations. The existing mapping is control `S1=(5,6,7,8,9)`; the swapped mapping is control `S1=(0,1,2,3,4)`.

No XOR mixing or general linear transform is in scope.

### 4.2 CAL-only model and folds

- Use only canonical CAL-TRAIN 702..1725 and the accepted R2 total-concentration/backoff contract.
- Use the existing four frozen outer folds and the already accepted concentration-selection semantics. Do not read VAL.
- For each partition derive held-out `CE_L1 = CE(U1|B)` and oracle-conditional `CE_L2 = CE(U2|U1,B)` from the transformed symbols/counts.
- Independently verify reversibility over all 1024 symbols, normalization, finite values, fold accounting, and the chain identity against joint held-out NLL within numerical tolerance.

### 4.3 Selection rule (decoder-blind)

For each partition compute four-fold mean `CE_L1`, `CE_L2`, and `CE_joint` plus fold dispersion. Compute development row indications at `n=64`, `f=1.2`:

```text
m1 = ceil(64 * CE_L1 * 1.2 / 5)
m2 = ceil(64 * CE_L2 * 1.2 / 5)
```

Rank all 252 partitions lexicographically by:

1. `max(CE_L1, CE_L2)` ascending;
2. `CE_joint` ascending;
3. `CE_L1` ascending;
4. `S1` lexicographically ascending.

Freeze the first three ranked partitions before decoder calls. Always include the two controls even if they are not top three. Deduplicate identical partitions. Decoder results may not alter this list or any row count.

### 4.4 Development decoder matrix

Use explicit function injection only. Use accepted R2 candidate priors transformed under each partition. Use fixed paired seeds `2026090600..2026090607` for all candidates and controls.

For each frozen candidate/control:

- rate point: use its preregistered `(m1,m2)` only if both are `<64`; otherwise label `NONZERO_RATE_INELIGIBLE` and do not silently cap it;
- square diagnostic: `(64,64)`;
- decode L1 then APP-propagated L2; oracle-L2 may be recorded only as a diagnostic;
- use the existing deterministic square/nested-mother construction and historical GF32 decoder, cold start, `max_iter=90`, `damping=1.0`;
- record exact and syndrome flags separately, iterations, nonfinite/crash, per-call wall, RSS, partition, seed, rows, and whether the call is APP or oracle.

Do not use a decoder result to tune anything. A deterministic implementation bug may be fixed within the allowlist with a test; a scientific ambiguity is a STOP.

### 4.5 Development classifications

Classify only the decoder-blind rank-1 partition at its non-square point:

- `DECOMPOSITION_STRONG_N64_RECOVERY`: both rows `<64`, end-to-end APP exact at least `6/8`, zero nonfinite/crash, zero syndrome/exact disagreement, and square exact count is not lower than non-square.
- `DECOMPOSITION_WEAK_N64_SIGNAL`: both rows `<64`, APP exact `1..5/8`, with zero nonfinite/crash and zero syndrome/exact disagreement.
- `DECOMPOSITION_NO_N64_RECOVERY`: both rows `<64`, APP exact `0/8`.
- `DECOMPOSITION_NO_NONZERO_RATE_CANDIDATE`: rank-1 has `m1>=64` or `m2>=64`.
- `DECOMPOSITION_MODEL_OR_IMPLEMENTATION_BLOCKED`: required invariants cannot be established.

These are development routing labels, not formal results. Do not relabel syndrome-only success as exact recovery.

### 4.6 Autonomous implementation branch

Only `DECOMPOSITION_STRONG_N64_RECOVERY` authorizes implementation of an additive, nonformal candidate in this packet.

If strong:

1. Create an OpenSpec change first, named `v72p2d5-decomposition-successor-r1`.
2. Implement only the minimum reversible mapping/prior/development-runner functions needed to reproduce the selected partition.
3. Keep the existing formal mapping, production wiring, roots, constants, CLI phases, and accepted artifacts unchanged.
4. Add focused tests for all-1024 round trip, controls, probability axes/normalization, decoder isolation, no formal-root writes, exact/syndrome separation, and deterministic replay.

If weak, none, or ineligible: do not add production code or an OpenSpec implementation change. Return the evidence and route terminal for main-thread choice. In particular, do not auto-fallback to graph or scheduling work.

### 4.7 Budgets

- Maximum decoder calls: 600.
- Maximum wall for all development decoder calls: 6 hours.
- Per-call watchdog: 120 seconds.
- RSS ceiling: 2 GiB; unknown RSS blocks a strong classification.
- At most one execution per frozen partition/seed/row/mode cell; no retries.
- CAL-only selection calculations do not count as decoder calls but must be timed and recorded.

Commit the preregistration alone:

```text
docs(v72p2d5): preregister reversible decomposition successor discriminator

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

## 5. Phase C — execute bounded CAL-only/development exploration

After the prereg commit:

1. Create one UUID-named root under `workspace/d5_decomposition_successor_r1_<uuid>/`.
2. Write a small standalone analysis script there first if no reusable in-repo function exists. Prefer NumPy/stdlib and existing accepted helpers; add no dependency or framework.
3. Enumerate and score all 252 partitions exactly once.
4. Freeze top three + controls into a manifest before any decoder call.
5. Execute the fixed decoder matrix within §4.7.
6. Independently recompute candidate ordering, row arithmetic, call accounting, exact/syndrome separation, and classification from saved scalar evidence.
7. Preserve the development root. Do not rename it into a formal root.

Minimum evidence files in the development root:

- `manifest.json`
- `partition_scores.csv`
- `selected_partitions.json`
- `decoder_records.csv`
- `summary.json`
- `command_log.txt`

Pure scalar/metadata evidence only. Do not persist raw symbols, priors, beliefs, matrices, or per-iteration messages.

## 6. Phase D — conditional implementation and tests

If and only if §4.5 is strong, execute §4.6 and run:

- compile/import checks for changed modules;
- focused new tests;
- the complete four-file D4/D5 suite:

```powershell
python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py comparison_bench/tests/test_v72p2d4r2_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_decomposition_successor_r1_tests_<uuid> -q --tb=line
```

Delete only the task-owned basetemp after resolving and verifying its path. Preserve the evidence root.

If code is changed, commit OpenSpec first, then code+tests in a separate commit. Do not mark the candidate accepted; independent review remains required.

If no code is changed, still run the four-file suite once at the milestone to establish regression status.

## 7. Phase E — delivery, state, and commit

Create:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_R1.md`

It must report:

- all 252-score invariants and top table;
- exact selected top three + controls and row counts;
- complete call accounting and budgets;
- paired exact/syndrome/oracle summaries;
- terminal classification from §4.5;
- whether conditional implementation occurred;
- strongest supported statement and explicit non-claims;
- next route recommendation, limited to one of:
  - `INDEPENDENT_D5_DECOMPOSITION_SUCCESSOR_REVIEW` after strong implementation;
  - `D5_DECOMPOSITION_WEAK_SIGNAL_ROUTE_REVIEW` after weak signal;
  - `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL` after no recovery/ineligible;
  - `D5_DECOMPOSITION_REWORK_REQUIRED` after blocked.

Append a compact durable decision to `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md`. Update only the D5 successor fields and `next_gate` in `cycle_state.yaml`; do not modify lifecycle authorization/result fields.

Commit evidence/report/state/log/memory together, plus implementation commits only if §6 allowed them. Never stage by directory or wildcard; stage exact allowlisted paths and verify `OUT_OF_SCOPE []`.

Suggested final evidence commit:

```text
docs(v72p2d5): land decomposition successor evidence and routing terminal

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

Do not push.

## 8. Acceptance matrix

- DS01 baseline/review/state/protected-root gate passes.
- DS02 route-stop acceptance lands unchanged review and exact scoped terminal.
- DS03 prereg commit predates every new score and decoder call.
- DS04 all 252 reversible ordered partitions enumerated exactly once.
- DS05 all-1024 round trip, axis, normalization, fold, and chain-NLL checks pass.
- DS06 ranking is decoder-blind and exactly follows the frozen lexicographic rule.
- DS07 top three + two controls are frozen before calls; seeds and rows are not tuned.
- DS08 every decoder call is explicit-injection development work in one UUID root.
- DS09 exact, syndrome, oracle, crash, nonfinite, wall, RSS, and calls remain separate and arithmetically consistent.
- DS10 terminal classification exactly follows §4.5.
- DS11 code/OpenSpec is added only for strong recovery; formal wiring remains unchanged.
- DS12 four-file suite passes with zero new failures; task-owned test temp is removed safely.
- DS13 formal G1/Model-F/P0/G0/structure roots are unchanged; G2 remains absent.
- DS14 all authorization/promotion and accepted formal result fields remain unchanged.
- DS15 commits contain only allowlisted paths and are local only.

Any DS01–DS15 deviation is a STOP unless this packet explicitly classifies it as a non-blocking known EOL condition.

## 9. Return contract

Return only on complete or concrete blocker. Routine progress does not need main-thread approval.

On complete, report deltas only:

1. DS01–DS15 PASS/FAIL table.
2. Commit SHAs and exact changed-file manifests.
3. Top partition score table and frozen selection.
4. Decoder table, call count, wall/RSS maxima, and terminal classification.
5. Test literal summary and failing IDs, if any.
6. Formal-root pre/post equality and all authorization values.
7. Whether OpenSpec/code implementation occurred and why.
8. Final `next_gate`, no-push confirmation, and the sentence:

```text
D5 当前固定分解路径已收口；本轮仅为 CAL-only/开发级分解后继鉴别，不构成正式 G1 重跑或 G2 授权。
```

On blocker, provide the failing acceptance ID, exact raw output, attempted in-scope remedies, and one requested main-thread decision. Do not silently narrow the matrix or invent a new algorithm family.

