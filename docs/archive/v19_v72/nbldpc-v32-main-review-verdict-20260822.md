# V32 Final Review Verdict — Codex Main Scientific Review (2026-08-22)

**Object:** `formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic` formal run_01 candidate evidence and terminal attribution.
**Reviewer:** Codex final read-only scientific review (main acceptance authority).
**Recorded by:** orchestrator (ox-alpha session), after code-level re-verification of all cited evidence.
**Status:** This verdict supersedes the persisted candidate terminal as the authoritative *scientific* reading. Raw evidence and candidate artifacts are preserved byte-identical.

## Overall Verdict

**EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE**

Execution evidence is accepted in full; the frozen truth-table terminal (`finite_graph_decoder_mismatch`) mechanically reproduces from the data; but the central scientific attribution is rejected because arm B1's key premise — a matched empirical-channel synthetic control — did not hold.

## Verdict Table

| Item | Verdict |
|---|---|
| A12 archive | ACCEPT |
| V32 spec/implementation provenance | ACCEPT |
| Formal run exact-once execution | ACCEPT |
| 247-record completeness | ACCEPT |
| B0 6/6 | ACCEPT |
| B1–B4 0/60 each | ACCEPT |
| no-rerun / no-tuning / no-overwrite | ACCEPT |
| Frozen truth-table mechanical terminal | ACCEPT |
| "B1 is a matched empirical synthetic" | REJECT |
| "B1 failure attributes to the finite graph itself" | REJECT |
| "B2/B3/B4 support one divergent signature" | REJECT |
| "Full T3 complete" | REJECT |
| "OpenCode R2 complete" | REJECT |
| V32 scientific closeout | `bridge_inconclusive` at main-review level |
| qualification / promotion | NO |

## Accepted Evidence (summary)

- Commit chain: A12 archive `0849c506` → spec freeze `0db7cfa2` → impl `78542ba8` → pre-run revision `8949abc2` (formal run executed at this HEAD).
- run_01 additive under `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/`; canonical untouched.
- 247 records, block UIDs unique, 0 resume events, 0 duplicates, cumulative meter 10047.235 s < 12 h cap.
- Independent recount (Codex) matches candidate recount exactly:

| Arm | 1M | 1.5M | 2M |
|---|---|---|---|
| B0 | 2/2 | 2/2 | 2/2 |
| B1 | 0/20 | 0/20 | 0/20 |
| B2 | 0/20 | 0/20 | 0/20 |
| B3 | 0/20 | 0/20 | 0/20 |
| B4 | 0/20 | 0/20 | 0/20 |

false_accept = 0 globally; B5 import integrity ok (300 records, decoder never invoked); B0 6/6.

## Why the Attribution Is Rejected

### Ground 1 — B1's generator was not matched to the bound empirical posterior

V32 B1 generation code (`run_nonbinary_v32_finite_de_bridge.py` L555–564, call site L1085):

```
alice ~ Uniform(0..1023)
error event ~ Bernoulli(raw_ser)
nonzero delta ~ Uniform(1..1023)
bob = alice + delta mod 1024
```

The decoder likelihoods derive from the V25 empirical joint (`P(A,B)=N_ab/total`, `P(U1|B)`, `P(U2|B,U1)`). The actual V26 DE channel sampler draws `(A,B)` directly from that empirical joint (`nonbinary_v26_channel.py` L10–13), preserving source separation and ±1 direction structure — structure the uniform-delta generator destroys.

B1 therefore paired a QSC-like synthetic generator with empirical-channel posteriors: a mismatched generator/likelihood pair, not a "matched synthetic" control and not the V26 DE operating point.

### Ground 2 — B1 posterior statistics show catastrophic likelihood mismatch

All 60 B1 records: initial→final L2 errors ≈ 235–252 → 458–480 (active divergence), NLL ≈ 229–245 bits/symbol against frozen reference entropies of ≈ 0.80–0.83 bits, entropy ≈ 0.31 bits, anomaly flag 60/60. Over-confident wrong messages push message passing away from the truth. This alone explains B1's divergence without invoking the QC graph.

Because the control arm used to judge graph capability is itself channel-mismatched, the attribution chain fails. Mechanically the frozen rule maps B1-fail → `finite_graph_decoder_mismatch`; scientifically the correct main-review classification is inconclusive.

## Corrections to Interim OpenCode Analysis (recorded for the record)

1. The "divergence signature" applies to B1 only. B3/B4 show genuine error improvement (≈ 250→179 per source on average) without reaching syndrome — closer to trapping / finite-redundancy / message-passing ceiling, not active divergence.
2. B2's `l2_errors_final=1024` is a sentinel value ("x2_hat does not exist"; `L2 not_run` after L1 failure), not decoder divergence. B2 must not be used in divergence analysis.
3. `truth_symbol_rank ≈ 0.21` counts symbols ranked above the true symbol (`(centered > p_true[:,None]).sum(axis=1)`): the true symbol usually sits at rank 1–2 of 32. The pathology is support-miss/tail failure (true symbol occasionally near-zero probability, exploding NLL), not uniformly weak posteriors.
4. "Polar would fail identically" requires layered judgment: only if total H(A|B) exceeds the total leakage budget are LDPC and Polar jointly infeasible. If only the current L2 allocation is infeasible, joint q-ary Polar or reallocated soft multilevel schemes remain open. Both layer-specific and total feasibility must be computed before excluding NB-Polar.

## Process Gap Records

- **R2 status:** `OPERATOR_HANDOFF.md` item 7 records "R2: PENDING". An in-session reviewer-go pass occurred but was never persisted into the handoff; it must not be cited as completed. This Codex final review independently recounted the evidence and serves as the authoritative post-run review.
- **T3 status:** T3 smoke PASS (1 passed, 44 deselected) covering directory existence / baseline record count / manifest schema only. The full frozen T3 regression scope (V28R decoder interface identity, QC packet identity, canonical before/after immutability, V31 B5 field-level consistency, all frozen directories unmodified) is NOT implemented/proven. Accurate phrasing: "T3 smoke: PASS; full frozen T3 regression: not implemented/proven."

## Preserved Artifacts and Prescribed Addendum Text

The persisted candidate terminal is NOT rewritten. `candidate_terminal.json` remains `finite_graph_decoder_mismatch` (mechanical product of the frozen rule). Any final addendum shall state:

> The frozen rule mechanically classified finite_graph_decoder_mismatch.
> Main scientific review did not accept that attribution because B1's
> uniform-substitution generator was not matched to the bound empirical
> V25/V26 posterior. The run remains valid evidence, but the root-cause
> attribution is inconclusive.

## Disposition and Next Action

- Do NOT archive V32 yet; do NOT write `finite_graph_decoder_mismatch` into project memory or decision-log as an authoritative root cause.
- Immediate follow-up: create audit-only change `formal-nonbinary-ldpc-v32-operating-point-consistency-audit` (phase 1 strictly read-only: D0 full failure-signature extraction; D1 B1 generator/posterior consistency analysis; D2 layer-specific and total information-theoretic feasibility vs actual rates; D3 read-only inspection of existing V26 DE evidence — no DE rerun, no decoder runs).
- Successor decisions (corrected matched-B1 / targeted V33 / NB-Polar feasibility gate) are deferred until the audit completes and its three-way feasibility branch is known.
