# P2 Experiment Packet (2026-09-21) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only (no HEAVY annotation: arm (i) is cheap DE, arm (ii) bounded scan). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-P2 (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh explicit grant per arm required (§7).
- Planning authority: `docs/ROADMAP-20260921.md` §3 P2 (+ §2 DECISION-1 scope, §8 review). Direction parent: `LITERATURE_DIRECTION_MEMO_20260921.md` §4(i) — this decomposition is the ONLY currently identifiable route to a generalizable contribution (literature cannot split the two components: Zhou curve is binary-QBER-2%/n≥2^16, arXiv-HTML-derived/PDF-unflagged; Müller is binary-BSC/n = 2^16).
- Parents: `F_EFF_ACCOUNTING_NOTE_20260921.md` (slope 4.7857, tag share 0.0751) + `B2F/B2G_RESULT_20260921.md` (soft-marginal anchors by citation) + `P1_PACKET.md` (owns the m = 200 point, §4) + `S2_ROUTE_DECISION_MEMO_20260921.md` L25/L30 (joint density/accounting lines) + V26 kernel (`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py::run_mcde_posterior`, per `openspec/changes/v80-nbldpc-jan21/design.md` S1 essentials) + S1 conventions (`S1_READINESS.md`: seeds {2026094951, 2026094952}, CONFIRM sampling).

## 1. Hypothesis (diagnostic, NOT a claim)

- H: m_min(measured) − m_DE(asymptotic) = finite-length penalty; m_DE − 170.5 = structured-channel/construction penalty, where 170.5 rows = n·H_full/5 = 852.544/5 = 170.5088 (roadmap §8: verified derivation).
- m_DE ≡ f_DE × 852.544/5 (row-equivalent of the MC-DE threshold efficiency at the joint rate). m_min ≡ smallest m with final fails/240 = 0 on the frozen channel (soft-marginal, instance 2026092001, via §4 assembly). Both are COMPUTED from measured inputs ([TO BE COMPUTED]); no value is pre-registered.
- Claim ceiling: the decomposition is DIAGNOSTIC; do NOT extrapolate to other channels, noises, or alphabets. No FER/SKR/qualification/publication claim.

## 2. Arm (i): one MC-DE threshold point at the joint rate (cheap, frozen kernel)

- Rate: joint code m = 416 over n = 2048 GF(32) symbols ⇒ rate = 1 − 416/2048 = 0.796875; leak = 416·5+64 = 2144; content = 2048×0.83256272 = 1705.088; f = 1.25741 (roadmap §3 P4, review-corrected). RESOLVED (explicit): `S2_ROUTE_DECISION_MEMO_20260921.md` L25 "m≈208 rows" is inconsistent with its own L30 accounting (m = 416 ⇒ leak 2144) and with f = 1.25741 (m = 208 would give f ≈ 0.65 < 1, impossible); L30/roadmap value m = 416 GOVERNS. ρ precedent: `make_rho(0.796875)` (`O1_EXPERIMENT_PACKET_20260920.md` L20); sampler MUST be the JOINT (u1,u2) channel sampler (S1-CONFIRM convention), NOT the L2 bundle — new thin sampler code, kernel read-only.
- Config (frozen): q = 32, λ = {2:1}, ρ = make_rho(0.796875); screen 4000 samples/60 iters + confirm 16000/100 (S1-CONFIRM convention, `openspec/changes/v80-nbldpc-jan21/design.md`); seeds EXACTLY {2026094951, 2026094952} (`S1_READINESS.md` — multiple seeds, no invention); report f_DE per seed + agreement.
- Gate (i): PASS iff |f_DE(seed1) − f_DE(seed2)| ≤ 0.05 (S1 flip-rule granularity precedent, design.md) — threshold reproducible; else NON-REPRODUCIBLE ⇒ return to main thread, no decomposition computed.
- Budget (i): ≤ 96 DE calls + ≤ 1200 s TOTAL (roadmap §3 P2, via D8/D9 precedent — origin docs not re-verified here; the budget itself is frozen); per-call ≤ 300 s; RSS < 2 GiB; CPU-only; no retry.

## 3. Arm (ii): soft-marginal FER curve points on the frozen channel (bounded scan)

- Channel/code family frozen: n = 1024 GF(32), λ = {2:1}, soft-marginal L2 prior (b2f verbatim formula), v28 max_iter 300/streak 3, exact_match accept, 240 paired blocks 2026095601+idx, stream `o1_blk:{seed}`, SINGLE construction instance 2026092001 (curve coherence: all cited anchors below are @2001).
- Coverage partition of m ∈ [180,208] (NO double-count, NO conflict with P1):
  | m | source | status |
  |---|---|---|
  | 180–188 | OUT OF SCOPE (no new measurement) | rationale: genie FAILs at 188 (4/14, `O1_RESULT_20260920.md`) and 192 (13/124); marginal prior is ~26 b/block weaker (FXR-1, `B2F_RESULT_20260921.md`) ⇒ expected FAIL + cost; scoping decision, not a claim |
  | 192, 196, 204 | NEW points, this arm, priority order 196 → 204 → 192 | 196 = cliff middle (genie A196 no verdict 1/29, `SCAN_INTERRUPT_20260921.md`); 204 = plateau gap; 192 = cliff floor |
  | 200 | OWNED BY P1 (P1 Stage-1 @2001 submatrix code) — this arm MUST NOT measure it | precedence §4 |
  | 202, 208 | BY CITATION, no re-run | b2f F202 6/240, F208 0/240 (`B2F_RESULT_20260921.md`) |
- Per-point machinery (comparability): bar-12 early-stop (13th fail ⇒ censored partial, FER lower bound — plotted distinctly, as A192 precedent); per-60 tally report-only; prior-entropy/u1-mismatch report-only; pins fc = 0 + rank-full + twice-identical GATED, girth recorded-not-gated (P0/B2G precedent); f_super per-point own-basis reported, NEVER as f_eff when fails > 0.
- Gate (ii): report monotonicity over COMPLETED points — monotone PASS-documented, or explicitly NON-MONOTONE/censored with NO inference (roadmap §3 P2 gate as frozen in task). No monotonicity may be assumed across m (route-memo no-monotonicity rule).
- Budget (ii): ≤ 3600 s TOTAL (roadmap §3 P2); per-decode ≤ 300 s terminal; RSS < 2 GiB; execute priority order while wall permits — wall exhaustion ⇒ INCOMPLETE point retained, unrun points NO verdict, never false PASS. Cost bracket: ≤ ~1400 s/point worst case (A192 precedent 1375 s; b2f F202 1346.9 s).

## 4. P1↔P2 precedence (frozen, both directions)

- P1 OWNS the m = 200 soft-marginal point (its frozen Stage-1 outcome @both instances; curve use takes the @2001 value). P2 arm (ii) consumes it BY REFERENCE once published; it must never re-measure m = 200 on paired blocks 2026095601+idx outside P1.
- If P2 is authorized alone/first: SKIP m = 200, mark [OWNED BY P1 — PENDING]; assemble the curve after P1 lands. P1's gate outcome does not invalidate its m = 200 measurement (ownership is of the measurement, not the verdict).
- If both authorized: P1 first (highest priority, roadmap §7 step 1); P2 arm (i) (cheap, independent) may run in parallel; P2 arm (ii) assembles after P1 Stage-1 lands. Joint A2 appears in NEITHER packet (DECISION-2).

## 5. Assembly (after both arms land; arithmetic only, no new execution)

- m_min from §3 assembly (smallest m with 0/240 @2001 soft-marginal; if none in range ⇒ report ">208 (unresolved)", no inference). Penalties per §1. Worked-example shape (NOT values): finite-length = m_min − m_DE; structured = m_DE − 170.5.

## 6. Budgets / scope / stop (both arms)

- Roots `workspace/p2_<uuid8>` fresh additive per arm (absence proven at Pre-EXECUTE); `results/` + `comparison_bench/outputs_comparison/` forbidden. New thin modules only (joint sampler; curve driver reusing frozen campaign helpers); V26 kernel + all frozen modules read-only; fake-only tests (sampler shapes/XOR-centering, row-equivalent arithmetic, bar/censor logic, coverage-partition refusals incl. m = 200 refusal, root refusal). No production DE/decode in tests.
- STOP on any science-input change (n/rates/tag/H/λ/seeds/thresholds/sampler/channel/decoder/hypothesis/data roles). Same repair rule as P1: no retry/resume/adaptive search; ≤1 preregistered engineering repair+rerun for infrastructure failure only, inputs unchanged, failure retained.
- FORBIDDEN (always): real/Jan-21 data; changing any frozen constant or gate; pooling across instances or arms; quoting cited-anchor f_super as f_eff; extrapolating the decomposition off the frozen channel; second DE kernel or decoder change; measuring m = 200 in this batch.

## 7. Entry evidence + authorization gate (EXPLICIT USER GATE — STOPS HERE)

- Entry: (a) executors built per §6; (b) Q0–Q6 Pre-EXECUTE per arm (branch; scope cleanliness; frozen contract §§1–6; output-absence + rg proofs — `p2_` absent, `2026094951/52` hits only in S1 docs+runner; focused tests incl. dry joint-sampler check (i) and dry-construct pins for new m points (ii)); (c) FRESH EXPLICIT USER GRANT per arm ("P2-DE execute" / "P2-curve execute" — this freeze is NOT a grant).
- Deliverables: `P2_DE_RESULT.md` (f_DE per seed, agreement gate) + `P2_CURVE_RESULT.md` (per-point FER/censor state, monotonicity report, coverage table) + `rows.json` + `block_accounting.csv` (arm ii) per root; assembly note computing §5 (or recording non-reproducibility/unresolved). Prompt: `P2_PROMPT.md`.
- Batch: ONE append-only `EXPLORATION_LOG.md` + ONE batch-end independent review (no per-arm review). This packet authorizes NOTHING.
