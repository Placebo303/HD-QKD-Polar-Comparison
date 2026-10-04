# Design: formal-nonbinary-ldpc-v32-operating-point-consistency-audit

## 0. Overview

One audit-only CLI (`run_nonbinary_v32_operating_point_audit.py`, subcommands d0/d1/d2/d3/all, `--runner` injection for test fakes) converts the frozen V32 run_01 evidence and existing V25/V26/V31 artifacts into four read-only report pairs (json+md), one `final_branch_decision.json`, and one `audit_manifest.json`. No DE, no decoder, no new runs. Ponytail discipline: stdlib + already-installed deps (`numpy`); one file per concern; no caching layer, no retry framework. The genuinely non-trivial logic — Q_B1 construction, sentinel handling, threshold preregistration, branch mapping — each gets explicit tests.

## 1. Semantic Correction Clauses (frozen — MUST be honored by every D0–D3 computation; prevent re-occurrence of the interim-analysis misreadings)

1. **truth_symbol_rank definition** = `(centered > p_true[:, None]).sum(axis=1)` averaged over positions: the count of symbols whose posterior probability exceeds the true symbol's probability. It is NOT a normalized rank. ≈0 means the true symbol usually sits at rank 1–2 of 32; large values would indicate uniformly weak posteriors.
2. **B2 sentinel**: `l2_errors_final=1024` is a not-run sentinel ("x2_hat does not exist"; L2 `not_run` after sequential-L1 failure). B2 MUST NOT enter any error-trajectory/divergence analysis; it is reported only as a sentinel count with its status fields.
3. **Divergence scope**: the active-divergence conclusion (final > initial) applies to **B1 only**. It must never be generalized to B3/B4.
4. **B3/B4 signature** = improve-but-no-syndrome: final < initial while syndrome/exact never true — closer to trapping / finite-redundancy ceiling than divergence.

## 2. Input Bindings (frozen)

Identical to `proposal.md §Frozen Input Bindings` (7 rows). Code facts already verified by main and cited verbatim in reports:

- B1 generator: `run_nonbinary_v32_finite_de_bridge.py` L555–564 `synth_channel_sample(seed, p_ser)`: `alice ~ Uniform(0..1023)`; error event `~ Bernoulli(p_ser)`; nonzero delta `~ Uniform[1,1023]`; `bob = (alice + delta) mod 1024`.
- V26 empirical sampler semantics: `nonbinary_v26_channel.py` L10–13 docstring: `(A,B)` sampled from train joint `P(A,B)=N_ab/total`; three sources kept independent; ±1 directions preserved; populations never merged.

The audit verifies every binding at start (stage 0) and records identities/hashes in `audit_manifest.json`. Any binding mismatch → stop before analysis.

## 3. D0 Design — Full Failure Signature

Parse `per_block.jsonl` by the `arm` field (never line numbers); verify counts: B5 import record 1, B0 6, B1/B2/B3/B4 60 each; duplicate `block_uid` → STOP as evidence inconsistency.

Per-record extraction (all 246 decode records + controls): `l1_errors_initial/final`, `l2_errors_initial/final`, `terminal_decoder_status`, `l1_decoder_status_verbatim`, `iterations`, `unsatisfied_checks`, `posterior_nll`, `posterior_entropy`, `truth_symbol_rank`, `calibration_bucket`, `posterior_anomaly_block`, `residual_syndrome_stats.{l1,l2}_residual_checks`, `syndrome`, `exact`, `tag`, `false_accept`, `success`.

Aggregation by arm×source: mean/median/min/max plus full histograms with bin edges declared once in `audit_manifest.json` before execution (fixed edges, e.g., error-delta bins and log-spaced NLL bins — declared, not tuned). Units rule: `posterior_nll`/`posterior_entropy` reported both raw (per block) and divided by n=1024 (bits/symbol); comparisons against reference entropies always in bits/symbol.

Frozen verification predicates (checked mechanically; any violation → `signature_mismatch=true` recorded, never silently reconciled):

- P-i: all 60 B1 records have `l2_errors_final > l2_errors_initial` (active divergence) with anomaly flag true.
- P-ii: all 60 B2 records have `l2_errors_final == 1024` AND `terminal_decoder_status == "not_run"` → classified sentinel, excluded from trajectory stats.
- P-iii: B3/B4 records show `l2_errors_final < l2_errors_initial` while `syndrome=false`/`exact=false` (improve-but-no-syndrome).

Output: `d0_signature.json` + `d0_signature.md`.

## 4. D1 Design — B1 Generator/Posterior Consistency

Per source s ∈ {1M, 1p5M, 2M}:

- Load `P = N_ab/total` from V25 `channel_counts.npz` key `{sid}_N_ab_train_N_ab_train` (verbatim on-disk key; the duplicated suffix is part of the stored name).
- Analytic generator law: `Q(b|a) = (1−raw_ser_s)·δ_{b=a} + raw_ser_s·Uniform{b≠a mod 1024}`; `Q(a)=Uniform`. raw_ser_s taken verbatim from V25 `channel_summary.json` field `per_source[sid].ser` (values frozen in proposal §Bindings).
- Metrics:
  - analytic cross-entropy H(Q,P) over cells where both laws defined;
  - zero/support-miss fraction: probability mass of Q on cells with `P(a,b)==0` (both directions reported), plus expected frequency of Q-samples hitting P-zero cells;
  - Q-sampled empirical NLL distribution under the V25 posteriors (`P(U1|B)`, `P(U2|B,U1)` via the F03/A02 adapter semantics): analytic if tractable, else Monte Carlo with seed and sample size fixed in `audit_manifest.json` BEFORE execution;
  - delta distribution comparison: Q's uniform delta (mass 1023·(ser/1023)+0 at δ=0) vs P_V25 actual delta histogram including ±1 direction mass (V25 `pm1_mass`: 1M dominated by +1, 1p5M/2M by −1 — structure Q destroys);
  - conditional divergence between the two laws for `P(U1|B)` and `P(U2|B,U1)` (declared measure: total-variation distance per conditioning value, aggregated);
  - dual expected NLL: E_Q[NLL under V25 posterior] vs E_{V25}[NLL under its own posterior] (the latter must land near the layer conditional-entropy magnitudes ≈ H.L1/H.L2 of V31 manifest — this contrast directly quantifies mismatch amplitude).
- Threshold preregistration: catastrophic-mismatch criterion written into `audit_manifest.json` BEFORE D1 computes anything, e.g., "expected-NLL(Q‖P) ratio ≥ K × self-NLL" with K derived against the log2(1024)=10 bits/symbol uniform-symmetry bound (state the chosen K and its derivation in the manifest; no post-hoc selection).

Output: `d1_consistency.json` + `d1_consistency.md`.

## 5. D2 Design — Information-Theoretic Feasibility vs Actual Rates

Per source:

- Compute from `channel_counts.npz` under F03/A02 layer maps (L1 GF32, L2 GF32): `H(U1|B)`, `H(U2|B,U1)`, `H(A|B)` in bits/symbol; cross-check against V31 manifest `configs["1024"].sources[].H.{L1,L2}` (mismatch beyond float tolerance → binding drift STOP).
- Leakage budgets taken verbatim from V31 artifacts, fields cited in output:
  - L1 syndrome symbols/bits: `m1=16` symbols × log2(32)=5 bits (=80 bits);
  - L2 syndrome symbols/bits: `m2_by_source` {184,190,192} × 5 bits;
  - total: manifest field `leak_total_bits` {1064,1094,1104} quoted verbatim AND a recomputed pure-syndrome value `(m1+m2)·5` reported alongside — definitions kept explicitly separate, never silently merged.
- Finite-length margin method (ONE, frozen before execution): simple gap reporting at n=1024 — `gap_bits = leakage_bits − required_bits` per layer and total, plus the leakage/entropy ratio. No normal approximation, no invented statistics.
- Conclusions at two levels, both mandatory: layer-specific feasibility (L1, L2) and total feasibility.

Three-way branch mapping (identical to proposal §Deliverables table; emitted as `final_branch_decision.json` schema):

| Branch | Condition | Consequence |
|---|---|---|
| A | total infeasible | LDPC 与 Polar 同速率方案均暂停，先重审泄漏预算/运行点 |
| B | total feasible 且 L2 allocation infeasible | 当前 multilevel allocation 失败，joint/重新分配的 NB-Polar feasibility 价值上升，不值得先换 QC 图 |
| C | layer 与 total 均可行 | finite graph/decoder 值得一次 corrected matched control（后续单独变更，不在本审计内执行） |

Branch selection is mechanical from the computed gaps; uncovered/ambiguous combinations → branch recorded as `inconclusive` with reasons (no fourth branch invented post-hoc).

Output: `d2_feasibility.json` + `d2_feasibility.md`.

## 6. D3 Design — Existing DE Evidence Read-Only Check

- Cite code locations: DE sampler draws `(A,B)` from `P(A,B)` (`nonbinary_v26_channel.py` L10–13); B1 did NOT replicate that channel (harness `synth_channel_sample` L555–564).
- Extract from V26 run_02 artifacts (all read-only): pass location — `gate.json` status `pass_target_f13`, `best_passing_f` A01=1.6/A02=1.3, per-layer/source operating point from `screen_results.json`/`confirmation_results.json` and m0/m1 reports; design constants from `RUN_MANIFEST.json` (screen 400 samples/seeds 26001–26002/max_iter 100; confirm 2000 samples/seeds 26101–26105/max_iter 200; entropy_tol_bits 0.01).
- Numeric comparison V26 rate/entropy parameters vs V32 QC packet (`packet_id m1_16_n1024_n1024|QC-cyclic-projective`, m1=16, m2_by_source, rates/H from V31 registry) — concrete numeric fields quoted side-by-side.
- Sufficiency ruling: if existing V26 evidence cannot answer the exact operating-point question, output `new_DE_change_required=true` plus the minimal list of DE questions — but NO DE execution inside this change.

Output: `d3_v26_evidence.json` + `d3_v26_evidence.md`.

## 7. Output Files & Collision

Run root: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/`

Files: `audit_manifest.json` (bindings, thresholds, MC seeds/sample sizes, histogram bins — all frozen before `all` executes), `d0_signature.json/md`, `d1_consistency.json/md`, `d2_feasibility.json/md`, `d3_v26_evidence.json/md`, `final_branch_decision.json`.

If the run root pre-exists → STOP: implementation/output collision. No overwrite, no automatic `run_02`. Every write resolves under this root only; all inputs opened read-only (incl. V32 run_01 canonical protection).

Execution order inside `all`: manifest freeze → d0 → d1 → d2 → d3 → final_branch_decision. Subcommands d0..d3 may run individually only against an existing frozen manifest.

## 8. Test Tiers (frozen)

All tests run in fresh `workspace/<audit>/<uuid>/` root with `pytest -p no:cacheprovider --basetemp <root>`; legacy ACL temp dirs untouched; fake runners passed explicitly — tests NEVER invoke production decoders/DE/pipelines.

- **T0 structural/tiny math**: compile/import; Q_B1 analytic construction on toy cases (δ mass conservation, b≠a support); sentinel recognition on a synthetic B2 record; branch-table totality (A/B/C/inconclusive exhaustive); collision refusal; static checks — audit source contains no decoder entry points, no DE sampling calls, no `.ttbin` path; tests perform no production execution.
- **T1 tamper (≥12)**: input drift rejection (any of bindings 1–4 modified); missing input file; partial/truncated JSONL; duplicate block_uid; arm-label tamper; sentinel mishandling detection (B2 fed into trajectory stats fails); threshold tamper (thresholds must come from frozen manifest — drift detected); MC seed/sample-size drift vs manifest; histogram-bin drift; output-root collision; branch-table tamper; write outside run root attempt rejected.
- **T2 fake fixture full flow**: complete fake fixture set (synthetic per_block-like records + tiny synthetic channel_counts) through `--runner` injection covering d0→d3→branch; independent recomputation of every headline number reproduces the persisted reports exactly; `new_DE_change_required` path exercised; collision path exercised end-to-end.

T2 runs at milestone P2R; no T3 tier exists for this change (nothing canonical may be executed or regenerated; read-only integrity of inputs is asserted within T0/T1/T2 fixtures and the formal run's stage-0 binding check).

## 9. Autonomy Boundaries (frozen)

Implementation MAY decide: internal function/file structure; minimal data structures; fixture organization; CLI parameter details; JSON field layout within §3–§6 required content; test split across T0–T2; Windows writable basetemp choice; ordinary in-scope bug fixes.

STOP-and-report triggers (never autonomous): changing D0–D3 definitions, predicates P-i..P-iii, thresholds, or the branch table; touching canonical/frozen paths; running any DE/decoder; reading `.ttbin`; anything `n=2048`; creating `run_02`; editing decision-log/memory; qualification/promotion wording; starting V33/NB-Polar/corrected-B1; push.

Handoff flags (restated for cross-file completeness): closeout artifacts carry exactly `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false` (normative in spec SHALL-H1; operationalized in tasks P5.1).

Every `ponytail:` simplification names its ceiling and upgrade path.
