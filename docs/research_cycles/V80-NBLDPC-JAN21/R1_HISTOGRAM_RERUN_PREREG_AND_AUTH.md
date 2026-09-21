> **Amendment 2026-09-21 (main-thread decision — authorization mode switched to conversation grant for this cycle; administrative ratification to follow, F-3 precedent).** The user waives the handwritten-signature requirement and grants execution by chat message (verbatim: "还是改成对话授权模式吧，这样有点复杂了，我授权你可以完成docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md中提到的部分"). This grant covers the §7 execution authorization (Acceptance ID G-R1) AND the §8 ratifications (F-3 A1-only grant; ±0.01/0.02 tolerance confirmations), strictly within the frozen contract of `R1_HISTOGRAM_RERUN_PACKET.md` and this preregistration — no frozen scientific input, gate, threshold, seed, budget ceiling, or stop rule is changed. The §7/§8 signature blocks remain BLANK by design (no signatures are forged); the verbatim chat grant above is the authorization of record, is quoted in the Pre-EXECUTE record, and the paperwork deviation is flagged for administrative ratification after the independent Pre-RESULT review (P3-A1-REVIEW F-3 precedent: chat grant accepted with the scientific-impact assessment recorded). This conversation-grant mode applies to THIS cycle only; making it a standing project mode would be an AGENTS.md/OpenSpec workflow change and is not claimed here.

> **Administrative ratification 2026-09-21 (post-Pre-RESULT, main thread).** The independent Pre-RESULT review (`R1_PRERESULT_REVIEW.md`, PASS_WITH_FINDINGS, no blocking findings) verified that the conversation-grant paperwork deviation had nil scientific impact: all frozen scientific inputs, gates, thresholds, seeds, budgets, and stop rules UNCHANGED; every estimator/design-point/gate number independently recomputed from the persisted artifacts. Per the P3-A1-REVIEW F-3 precedent, the main thread ratifies the §7 execution grant and the §8 ratifications as given by conversation grant, for THIS cycle only. This does not establish a standing conversation-grant mode (that would be an AGENTS.md/OpenSpec workflow change and is not claimed here).

# R1 Histogram Re-run — PREREG_AND_AUTH (2026-09-21) — DRAFT_PENDING_AUTHORIZATION

> **Amendment 2026-09-21 (main-thread decision — bootstrap NOT waived).**
> Bootstrap (≥200 resamples, frozen seed 20260921) is REQUIRED; the row-B / waived / NO-CI
> budget alternative is WITHDRAWN. Single budget ceiling: per-read ≤300 s, per-dataset ≤1800 s,
> trio ≤5400 s total, RSS <4 GiB, 0 decoder/DE/graph calls. Signature block remains BLANK.

- Track: **DECIDE** (real/raw acquisition data; outputs correct published design points and feed the X1 route campaign). Status: `AUTHORIZED-BY-CHAT-GRANT-2026-09-21 (see top amendment note; §7/§8 signature blocks intentionally blank)`. Branch context: `formal-ir-v72p1-addendum-clean` (publication branch `formal-ir-v80-nbldpc-jan21` — not touched). No switch, no commit, no push, no PR.
- Packet (frozen contract): `docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PACKET.md` (Acceptance ID **G-R1**). Operator prompt: `R1_HISTOGRAM_RERUN_PROMPT.md`.
- **Nothing has been executed. No `.ttbin` has been opened. No decoder, DE, graph, or `tools/*` call has been made. No workspace root has been created. No output has been written.**
- Compact DECIDE form permitted by `AGENTS.md` §10.3 / `docs/research-cycle-sop.md` §4: this file + `RESULT.md` + `INDEPENDENT_ACCEPTANCE.md` + machine artifacts.

## 1. Hypothesis / questions (single, falsifiable set)

- Q1 (estimator correction): what are the per-source CONDITIONAL-entropy Miller–Madow-corrected values `H_corr = H_plug + (K_AB − K_B)/(2·N_train·ln2)` on the TRAIN pool, with bootstrap CI — and how far do they move vs the defective-basis Baseline §3 values (H_MM 0.8036079281174853 / 0.8289616869054485 / 0.8345846048587662)? **No numeric outcome is pre-registered**; corrected values are `[TO BE MEASURED]`. Bounded expectation only (not a prediction): the move is DOWN by `(K_B−1)/(2N·ln2)`, at most 0.002339/0.001672/0.001252 b at K_B = 1024 (estimator-verification §T2).
- Q2 (bundle materialization): do the persisted sparse TRAIN histograms + `p_b` satisfy the X1 bundle-input requirements (shapes (1024,1024)/(1024,), normalization, reconstruction checksums) for all three sources?
- Q3 (2M lineage): how do the re-derived 2M inputs compare against the frozen `gamma_f03.npz` lineage (report-only finding per packet §2.7)?
- Control expectations (machinery checks, not science predictions): §3A alignment re-derives bin 8191/8192 (−50/+50/+50); determinism gate (f) reproduces A1 frame counts/split boundaries exactly.

## 2. Exact command (placeholders — filled at Pre-EXECUTE, never invented)

```
PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.r1_histogram_rerun \
  --bases <BASE_1M;.1.5M;.2M_BASE_X_TTBIN> \
  --datasets T2-1M;T2-1.5M;T2-2M \
  --root workspace/r1_histogram_<UUID8> \
  --bootstrap-seed 20260921 --bootstrap-resamples 200 \
  --per-read-timeout-s 300 --budget-s 5400
```

- `<BASE_...>` = the three Jan-21 trio base `X.ttbin` members (same members A1 read; `[TO BE CONFIRMED at Pre-EXECUTE]` against `docs/DATA_INVENTORY_20260921.md`). Base-only; never `.1`; never both.
- `<UUID8>` and tolerance confirmations are `[TO BE FROZEN]` at Pre-EXECUTE. This file deliberately invents none of them. Budget is the single bootstrap-inclusive ceiling (trio ≤5400 s); no alternative row exists.
- `WITHDRAWN by main-thread decision 2026-09-21 — bootstrap is REQUIRED; a NO-CI run is not authorizable under this packet` (former `0-WAIVED` / `NO-CI` path deleted in its entirety).

## 3. Budget table (frozen single ceiling — bootstrap REQUIRED)

| item | ceiling |
|---|---|
| per-read | ≤ 300 s |
| per-dataset (read + §3A + pairing/framing/bincount + persistence + bootstrap) | ≤ 1800 s |
| trio total | ≤ 5400 s |
| RSS | < 4 GiB |
| decoder/DE/graph calls | 0 |
| bootstrap | ≥ 200 resamples, frozen seed 20260921 |

`WITHDRAWN by main-thread decision 2026-09-21 — bootstrap is REQUIRED; a NO-CI run is not authorizable under this packet` (former row B — bootstrap-waived ≤1800 s cost path — deleted in its entirety and SHALL NOT be authorized).

Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 preregistered engineering repair+rerun for infrastructure failure only, scientific inputs unchanged, failed attempt retained in the same root.

## 4. Output-absence checks (recorded at Pre-EXECUTE, before any execution)

- [ ] `workspace/r1_histogram_*` does not exist (`ls workspace | rg '^r1_histogram_'` returns nothing).
- [ ] `rg -n 'r1_histogram_' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/R1_*'` returns only this packet family.
- [ ] `results/` and `comparison_bench/outputs_comparison/` are byte-identical to their pre-execution state (no new files, no overwrites).
- [ ] Existing evidence roots (`workspace/p3_census_3954637c/`, `workspace/p3_stage05_ee32030a/`) untouched; `git diff -- src/` empty.
- [ ] Intended branch confirmed: `formal-ir-v72p1-addendum-clean`; no switch; no commit; no push; no PR.
- [ ] TimeTagger import verified in `.venv` via the alias shim; if unavailable ⇒ **STOP-BLOCKED**.
- [ ] Scoped code/config/test/packet cleanliness confirmed (only the additive R1 executor + its tests).
- [ ] Focused tests pass: fake-only K_B/correction-identity/sparse-round-trip/bundle-gate tests (packet §7 T-R1-3).
- [ ] Target output root absence re-proved with the final UUID immediately before launch.

## 5. Scope / non-goals (explicitly forbidden)

- No X1 cliff arms; no decoder, no DE, no graph construction, no `tools/longrun_*` / `minrerun_*` / `routeA_*`, no `experiments/run_e2e_pipeline.py`.
- No change to any frozen scientific input (n, m, tag, H_full anchor, gates, thresholds, seeds, split rule, trio parameters).
- No retraction or re-run of the A1 synthetic FER arms (b2f/b2g etc.).
- No reading of any excluded derived artifact; no overwrite of `results/` or `comparison_bench/outputs_comparison/`; no pooling across sources; no merging of `undetected` into success (N/A, invariant kept); no quoting TRAIN numbers as held-out or vice versa without the split side.
- **No FER / SKR / route / qualification / publication claim.** Corrected design points do NOT authorize X1 by themselves.

## 6. Decision criteria (frozen, binary per gate)

- **G-A (alignment):** packet §3A gates pass per source, else STOP-BLOCKED for that source, others continue.
- **G-B (span):** span-continuity assertion passes per source, else STOP-BLOCKED for it.
- **G-C (atomicity):** per source both artifact sets persist or the source is INCOMPLETE; no partial close-out.
- **G-D (K_B sanity):** 1 ≤ K_B ≤ 1024 AND K_B < K_AB, else STOP-BLOCKED for it.
- **G-E (2M lineage):** comparison reported; material discrepancy (|ΔH| > 0.01/plane OR p_b L_inf > 1e-3) ⇒ FINDING escalated, never smoothed, never refit.
- **G-F (determinism):** frame counts + split boundaries + derived alignment reproduce A1 exactly, else STOP-BLOCKED for it (infrastructure drift ⇒ ≤1 repair path).
- Batch closes only with independent Pre-RESULT review + main-thread acceptance. Any gate FAIL blocks solidification; never publish-then-patch.

> **Pre-fill note 2026-09-21 (operator-side fields ONLY — proposals for the user's signature).** Base paths per docs/DATA_INVENTORY_20260921.md (same trio members A1 read); output-root UUID 5e2a91c4 is a proposal whose absence will be re-proved immediately before launch (packet §8); 200 resamples = packet floor and A1 precedent; span tolerance 0.5 s = Stage 0.5 G3 precedent (max observed |span−gap| 0.0398 s); 2M materiality bars confirmed as frozen (packet §2.7). Nothing in the frozen contract is changed. Per the block's own NOTES: any change of base members, root, budget, seed, tolerance, or threshold requires a NEW signature.

## 7. SIGNATURE BLOCK — the user must fill this to grant execution

```
I AUTHORIZE execution of the R1 histogram re-run under Acceptance ID G-R1,
strictly within the frozen contract of R1_HISTOGRAM_RERUN_PACKET.md and
this preregistration.

  Base members authorized (3 paths):        /mnt/d/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin
                                              /mnt/d/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin
                                              /mnt/d/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin
  Output root (fresh, absent):              workspace/r1_histogram_5e2a91c4
  Budget confirmed (single ceiling):          ≤5400 s trio total, bootstrap REQUIRED (no alternative row)
  Bootstrap resamples / seed:               200 (≥200 REQUIRED) / 20260921
  Span tolerance (s, proposed 0.5):            0.5
  2M materiality bars confirmed:            |ΔH|>0.01 / p_b L_inf>1e-3  (yes / amended: none — confirmed as frozen)
  Branch / commit context confirmed:        formal-ir-v72p1-addendum-clean

  Authorized by (name/handle):              ______________________________
  Date (UTC):                               ______________________________
  Signature:                                ______________________________

NOTES
- This signature is the ONLY authorization. The frozen packet and this
  preregistration authorize NOTHING by themselves.
- Pre-EXECUTE Q0–Q6 (packet §8) must be recorded and PASS before any execution.
- The grant covers ONE bounded run. Any change of base members, root, budget,
  seed, tolerance, or threshold requires a NEW signature.
- After execution: one result record, then independent Pre-RESULT, then
  main-thread acceptance. No PR, no push, no commit without a separate
  explicit authorization.
```

*(This block is BLANK by design — the planner does not sign. The user fills it.)*

## 8. MAIN-THREAD FORMAL RATIFICATIONS — same signing round, SEPARATE item from the R1 grant above

Closes the two formal OPEN items of `docs/V80_BASELINE_20260921.md` §0.2 (status-consistency rule):
ratified-in-principle by `docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` §D; formally OPEN until
signed here. These ratifications concern the A1/Stage-0.5 evidence chain; they grant NO R1 execution
and are not part of the §7 signature block.

- (i) **F-3 authorization gap (baseline §7-2):** the verbatim user grant `允许你开始Stage 0.5与A1` is
  RATIFIED as an A1-only grant (control margin 8.7×, CI margin 7× ⇒ nil scientific impact,
  `P3_A1_REVIEW.md` F-3); OpenSpec task P3-T5 is closed administratively; any new dataset requires
  its own signature.
- (ii) **Tolerance confirmation (baseline §7-3):** control tolerance ±0.01 and support tolerance 0.02
  are CONFIRMED (`P3_A1_REVIEW.md` items 5–6; both gates pass with large margins; formal only).

```
I RATIFY items (i) and (ii) above as main-thread decisions.

  Ratified by (name/handle):                   ______________________________
  Date (UTC):                                  ______________________________
  Signature:                                   ______________________________
```

*(This block is BLANK by design — the operator does not sign. The user fills it.)*
