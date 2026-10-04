# Spec: formal-nonbinary-ldpc-v32-operating-point-consistency-audit

## Scope

This delta spec freezes an **audit-only** change: strictly read-only analysis converting the V32 run_01 evidence (240 B1–B4 decode records + B0/B5 controls) plus existing V25/V26/V31 artifacts into decidable operating-point consistency evidence and a three-way branch decision. Motivated by `docs/nbldpc-v32-main-review-verdict-20260822.md` (`EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE`; B1 generator/posterior mismatch).

In scope:
- One audit CLI (subcommands d0/d1/d2/d3/all, `--runner` injection for fakes) producing report pairs, `final_branch_decision.json`, `audit_manifest.json` under a single new run root.
- Read-only inspection of existing DE evidence; explicit `new_DE_change_required` ruling when evidence is insufficient.

Out of scope:
- Any DE rerun or new DE sampling; any decoder invocation; any `.ttbin` access.
- corrected-B1 implementation, new diagnostic arms, n=2048 anything.
- Edits to `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`; V32 archive actions; qualification/promotion wording; start of V33/NB-Polar/corrected-B1.

## Definitions

- **Frozen bindings**: the 7 input bindings of `proposal.md §Frozen Input Bindings` (V32 run_01 evidence incl. 247-line `per_block.jsonl`; V25 run_04 `channel_counts.npz`/`channel_summary.json`/`split_manifest.json`; V26 run_02 artifacts; V31 run_01 RUN_MANIFEST/matrix_audits/m1_registry; harness code fact L555–564; V26 sampler code fact L10–13; three frozen source IDs).
- **Semantic corrections** (normative): `truth_symbol_rank = (centered > p_true[:,None]).sum(axis=1)` — count of symbols above true-symbol probability, NOT a normalized rank (≈0 ⇒ true symbol usually rank 1–2 of 32); B2 `l2_errors_final=1024` is a not-run sentinel; divergence applies to B1 only; B3/B4 are improve-but-no-syndrome.
- **Run root** = `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/`.
- **Branch set** = exactly A / B / C / inconclusive per §Three-Way Branch Mapping.

## Requirements (SHALL)

### D0 — Failure Signature

- **SHALL-D0a** — The system SHALL read `per_block.jsonl` by the `arm` field and verify counts: B5 import record 1, B0 6, B1/B2/B3/B4 60 each; a duplicate `block_uid` SHALL stop as evidence inconsistency. Per record it SHALL extract: initial/final L1/L2 errors; `terminal_decoder_status` and `l1_decoder_status_verbatim`; iterations; unsatisfied checks; `posterior_nll`; `posterior_entropy`; `truth_symbol_rank`; `calibration_bucket`; `posterior_anomaly_block`; residual syndrome stats; `syndrome`/`exact`/`tag`/`false_accept`/`success`.
- **SHALL-D0b** — Aggregation SHALL be by arm×source with mean/median/min/max plus full histograms using bin edges declared in `audit_manifest.json` before execution. NLL/entropy SHALL be reported both per block and bits/symbol; comparisons against reference entropies SHALL use bits/symbol only.
- **SHALL-D0c** — The system SHALL mechanically verify the frozen predicates: P-i all 60 B1 records show active divergence (`l2_errors_final > l2_errors_initial`, anomaly true); P-ii all 60 B2 records have sentinel `l2_errors_final == 1024` with `terminal_decoder_status == "not_run"` and are excluded from error-trajectory analysis; P-iii B3/B4 records show improvement without syndrome (`final < initial`, syndrome/exact false). Any violated predicate SHALL be recorded as `signature_mismatch=true` and SHALL NOT be silently reconciled.

### D1 — Generator/Posterior Consistency

- **SHALL-D1a** — For each source the system SHALL construct analytic Q_B1(b|a) = (1−raw_ser)·δ_{b=a} + raw_ser·Uniform{b≠a mod 1024} with raw_ser taken verbatim from V25 `channel_summary.json` `per_source[sid].ser`, citing source file and field, and compare against P_V25 from `channel_counts.npz` key `{sid}_N_ab_train_N_ab_train` (verbatim on-disk key with duplicated suffix).
- **SHALL-D1b** — D1 SHALL compute and report per source: empirical cross-entropy H(Q,P); zero/support-miss fraction both directions including expected frequency of Q samples hitting P-zero cells; Q-sampled empirical NLL distribution under the V25 posteriors (analytic or Monte Carlo with seed AND sample size fixed in the manifest before execution); delta-distribution comparison including ±1 direction mass; conditional divergence of P(U1|B) and P(U2|B,U1) between the two laws under one declared measure; dual expected NLL (E_Q[NLL under V25 posterior] vs E_V25[NLL under its own posterior]).
- **SHALL-D1c** — All mismatch thresholds SHALL be pre-registered in `audit_manifest.json` BEFORE any D1 computation runs, each with a stated derivation basis anchored to log2(1024)=10 bits/symbol; post-hoc threshold selection SHALL be forbidden.

### D2 — Feasibility vs Rates

- **SHALL-D2a** — Per source the system SHALL compute H(U1|B), H(U2|B,U1), H(A|B) from `channel_counts.npz` via the F03/A02 L1/L2 maps and cross-check against V31 manifest `configs["1024"].sources[].H.{L1,L2}` (mismatch beyond float tolerance → binding-drift STOP).
- **SHALL-D2b** — Leakage budgets SHALL be quoted verbatim with field citations: L1 = m1=16 symbols × log2(32) bits; L2 = `m2_by_source` {184,190,192} symbols × log2(32) bits; total = manifest `leak_total_bits` {1064,1094,1104} quoted verbatim alongside a recomputed pure-syndrome `(m1+m2)·5` value, definitions kept explicitly separate.
- **SHALL-D2c** — Finite-length margin SHALL use exactly ONE declared method frozen before execution (simple gap reporting at n=1024: gap_bits and leakage/required ratio per layer and total); undeclared invented statistics SHALL be forbidden. Both layer-specific feasibility AND total feasibility conclusions SHALL be output.
- **SHALL-D2d** — `final_branch_decision.json` SHALL map results onto exactly the frozen branch set:

| Branch | Condition | Consequence |
|---|---|---|
| A | total infeasible | LDPC 与 Polar 同速率方案均暂停，先重审泄漏预算/运行点 |
| B | total feasible 且 L2 allocation infeasible | 当前 multilevel allocation 失败，joint/重新分配的 NB-Polar feasibility 价值上升，不值得先换 QC 图 |
| C | layer 与 total 均可行 | finite graph/decoder 值得一次 corrected matched control（后续单独变更，不在本审计内执行） |

Uncovered/ambiguous combinations SHALL record branch `inconclusive` with reasons; no fourth branch may be invented after results are seen.

### D3 — Existing DE Evidence (read-only)

- **SHALL-D3a** — The audit SHALL cite verbatim: the DE sampler drawing `(A,B)` from `P(A,B)` at `nonbinary_v26_channel.py` L10–13, and that B1 did not replicate that channel (harness `synth_channel_sample` L555–564).
- **SHALL-D3b** — The audit SHALL extract where the V26 pass occurred (layer/source/operating point from `gate.json`, `RUN_MANIFEST.json`, m0/m1 reports, screen+confirmation results) and compare V26 rate/entropy parameters against the V32 QC packet numerically, quoting concrete fields side-by-side.
- **SHALL-D3c** — If existing V26 evidence cannot answer the exact operating-point question, the audit SHALL output `new_DE_change_required=true` plus the minimal DE question list; NO DE execution SHALL occur inside this change.

### Manifest Freeze & Execution Order

- **SHALL-MF1** — `audit_manifest.json` SHALL be written first, freezing: binding identities/hashes; D1 thresholds with derivation basis; MC seeds and sample sizes; histogram bin edges; margin method. Subcommands d0..d3 SHALL refuse to run against a missing or drifted manifest.
- **SHALL-MF2** — Inside `all`, execution SHALL follow: manifest freeze → d0 → d1 → d2 → d3 → final_branch_decision.

### Read-Only Constraints & Collision

- **SHALL-R1** — The audit SHALL open every input read-only; V32 `run_01` evidence SHALL remain byte-identical; no writes outside the single run root; no overwrite of any existing output root.
- **SHALL-R2** — If the run root pre-exists when the formal audit starts, the system SHALL STOP with implementation/output collision; overwriting and automatic `run_02` creation SHALL both be forbidden.
- **SHALL-R3** — No DE rerun, decoder invocation, `.ttbin` access, canonical/frozen write, decision-log/memory edit, archive action, or qualification/promotion statement SHALL occur anywhere in this change; starting V33/NB-Polar/corrected-B1 is out of scope.

### Output Files

- **SHALL-O1** — The run root SHALL contain exactly: `audit_manifest.json`, `d0_signature.json/md`, `d1_consistency.json/md`, `d2_feasibility.json/md`, `d3_v26_evidence.json/md`, `final_branch_decision.json`.

### Test Tiers

- **SHALL-V1** — Verification SHALL follow the frozen tiers: T0 structural/tiny math (import; Q_B1 toy construction with mass conservation; sentinel recognition; branch-table totality; collision refusal; static checks for no decoder entry points/no DE sampling/no `.ttbin`/no production execution from tests); T1 tamper ≥12 items (input drift; missing input; truncated JSONL; duplicate block_uid; arm-label tamper; sentinel mishandling detection; threshold tamper vs manifest; MC seed/sample-size drift; histogram-bin drift; output-root collision; branch-table tamper; out-of-root write rejection); T2 fake fixture full flow via `--runner` injection covering d0→d3→branch with independent recomputation reproducing persisted reports, plus `new_DE_change_required` and collision paths.
- **SHALL-V2** — All tests SHALL run in fresh `workspace/<audit>/<uuid>/` roots with `pytest -p no:cacheprovider --basetemp <root>`; legacy ACL temp dirs untouched; fake runners passed explicitly; tests SHALL NEVER invoke production decoders/DE/pipelines.

### Autonomy & Handoff

- **SHALL-B1** — Implementation MAY decide internal structure, fixtures, CLI details, JSON layout within SHALL-O1 content, test split, basetemp choice, in-scope bug fixes. It SHALL STOP and escalate before: changing D0–D3 definitions/predicates/thresholds/branch table; touching canonical paths; running DE/decoder; reading `.ttbin`; creating `run_02`; editing decision-log/memory; promotion wording; push.
- **SHALL-H1** — At closeout the operator SHALL produce candidate-only handoff artifacts marked `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false`; only main may end `main_acceptance_pending`. Decision-log/memory entries happen only AFTER main acceptance.

## Acceptance Mapping

| Area | Requirements | Verified by |
|---|---|---|
| D0 extraction/aggregation/predicates | SHALL-D0a..c | T0 tiny math + T2 independent recomputation |
| D1 construction/metrics/thresholds | SHALL-D1a..c | T0 Q_B1 toys + T1 threshold/MC tamper + manifest inspection |
| D2 entropies/leakage/gaps/branch | SHALL-D2a..d | T2 recomputation + branch-table totality test |
| D3 code citations/sufficiency ruling | SHALL-D3a..c | T2 `new_DE_change_required` fixture |
| Manifest freeze/order | SHALL-MF1..2 | T1 drift refusals + T2 order assertions |
| Read-only/collision/output files | SHALL-R1..R3, O1 | T1 collision/out-of-root tests + formal-run stage-0 check |
| Tests/autonomy/handoff | SHALL-V1..V2, B1, H1 | pytest logs under workspace root + handoff artifact flags |
