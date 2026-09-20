# LITERATURE_DIRECTION_MEMO_20260921 — V80 NB-LDPC literature/direction consolidation

Track: EXPLORE, documentation-only. Branch `formal-ir-v72p1-addendum-clean`. No code/run/commit/push; no B2G_*/b2g file touched; `LITERATURE_RECOMMENDATION_TRIAGE_20260921.md` §6 left dirty as instructed. Authorizes nothing (§6).

Provenance deviation (recorded per §6): the three supplied PDFs could NOT be read by this agent (read tool: "this model does not support pdf input"). The same manuscripts were read once via arXiv HTML: Kanitschar & Huber PRL 135,010802 = arXiv:2406.08544v2 (journal_ref matches); Zhou et al. PRApplied 18,044022 = arXiv:2204.06971v1 (abstract verified verbatim on journals.aps.org); Müller et al. IET QTC 10.1049/qtc2.70003 = arXiv:2408.15758v1 (DOI↔arXiv via Semantic Scholar f5c6b61a…). All quotes below are from those texts.

Frozen V80 accounting (reference, quoted): f_super = (5·(m1+m2)+64)/852.544 ≤ 1.3, whole-frame 64-b tag counted once; superframe n = 1024 GF(32) symbols = 5120 b; m1+m2 ≤ 208 (leak ≤ 1108.31 b); H_full = 0.83256272 b/symbol (852.544 b/frame) [S2_ROUTE_DECISION_MEMO E8; L1_CONSTRUCTION_MEMO §1; S2_ACCOUNTING_MAP]. Measured: b2f F208 (m=208, leak 1104 b, f=1.294947) 0/240 FER 0.0; F202 (m=202, leak 1074 b, f=1.259759) 6/240 FER 0.025; genie-u1 A208 0/240 ×2 = upper bound (O1R D1); soft-marginal prior D-u1 = 0.0 structural [B2F_RESULT; B2F_BATCH_END_REVIEW].

## §1 Per-paper extraction (number — quote — convention — verdict)

**Müller et al. 2025, IET Quantum Commun. 10.1049/qtc2.70003** (live industrial QKD, QTI 3-state BB84, 10 dB channel; binary BSC; EC frame n = 2^16 = 65536 b):

- f_Cascade = 1.036, f_LDPC = 1.166 — "The mean efficiencies of Cascade and LDPC are f_Cascade=1.036 and f_LDPC=1.166, respectively." (§3.4, 27-h live run). Convention: f = leak_IR/(n·H(X|Y)) (Eq. 4); denominator n·H(q), q = true QBER 2–6%; numerator = parity bits sent (Cascade) or ⌈n(1−R_adapted)⌉ + k_revealed (Blind LDPC, Eq. 10); EV tag NOT in plain f — their f_eff (Eq. 11) adds t/(nH(q)) with t = 50, plus (FER_cluster+P_Collision)/H(q). Verdict: NOT COMPARABLE — dominant reason: channel model (binary BSC at 2–6% QBER vs our GF(32) structured channel, H_full = 0.8326 b/symbol ≈ binary-entropy-equivalent QBER ≈ 0.26); n = 65536 vs 5120 secondary.
- 446 vs 3.14 — "The mean number of messages are 446 and 3.14." (§3.4). Measures: mean exchanged messages per EC frame, Cascade vs LDPC-Blind, live run. NOT COMPARABLE (V80 has no message-count metric; our arms are one-way syndrome + 64-b tag). Qualitative use only.
- FER < 0.003 — "the frame error rate of Cascade stayed below 0.003 (evaluated on 1000 samples) for both perfect match and any other tested mismatch between q and q̂" (§3.2). Convention: SIMULATED BSC on industrial data; FER = EC-frame error rate, efficient (Pacher) Cascade; true QBER 2/4/6%; same run: "There were no frame errors for the Blind protocol." NOT COMPARABLE — dominant reason: decoder family (binary Cascade vs NB-LDPC BP) + simulated, not live. Order-of-magnitude reference only.
- 6.7 kbit/s — "the throughput of the raw data acquisition stage, i.e. frame size over time of acquisition and sifting, was around 6.7 kbit/s" (§3.4). Measures the raw sifted-key acquisition rate — NOT secret-key rate, NOT IR throughput. NOT COMPARABLE (quantity does not exist in V80).

**Zhou et al., Phys. Rev. Applied 18, 044022 (2022)** (AIR polar IR; binary BSC; SCL L=16; Rm ≤ 4; CRC tag d = 64):

- f = 1.046 — "the efficiency of the proposed AIR scheme is 1.046, when the block size is 1 Gb and the quantum bit error rate of 0.02" (§4.3). Convention: f = (d + Σ m_i)/(n·H2(Eμ)) (Eq. 15) — the 64-b CRC tag IS in the numerator (Table 1); denominator n·H2(QBER); n = 2^30. NOT COMPARABLE — dominant reason: block length (2^30 ≈ 4×10^5 × our 5120 b). Note: the tag-inclusive numerator MATCHES our f_super convention — the only literature f here that does.
- ε ≈ 1e-8 — "with the overall failure probability around 10^-8" (abstract; Eq. 10: ε = ε_I+ε_II < Rm·ε_CRC + ε_Rm, ε_Rm = 1e-8, ε_CRC ≤ L/2^64). FER definition: Pr(K_IR^A ≠ K_IR^B) incl. CRC-undetected and abort-at-Rm cases; a DESIGN TARGET with measured decoding-failure curves (n = 1 Mb, Fig. 2). NOT COMPARABLE — their ε is a protocol-level design bound; our fails/240 is an empirical FER point estimate on paired synthetic frames.
- Finite-length scaling (Table 4, App. A, "detailed estimation results"; Rm=4, CRC 64, ε_Rm=1e-8): f(QBER 0.02) = 1.190 @ n=2^16; 1.120 @ 2^20; 1.075 @ 2^24; 1.056 @ 2^27. Convention as above, labelled ESTIMATION. NOT COMPARABLE per se; the only quantitative finite-length f-scaling available to us — used in §3.

**Kanitschar & Huber, PRL 135, 010802 (2025)** (HD time-/frequency-bin QKD; asymptotic key rates; d = 4, 8, 16; isotropic noise ρ = v|Ψ1⟩⟨Ψ1| + (1−v)/d²·1):

- No f, no FER, no IR block length anywhere in the paper. Quantities: R^∞ = H(X|E) − H(X|Y) (Devetak–Winter) — "the second term is purely classical and can be directly calculated from Alice and Bob's data"; subspace postselection K ≥ Σ_m P(M=m)·K_m — "subspace postselection significantly enhances noise resistance and enables nonnegative key rates in high-noise regimes". Verdict: NOT COMPARABLE by construction — the paper contains no IR-efficiency quantity; it supplies CONTEXT only: the H(X|Y) term is exactly what our f_super prices, and d ≫ 2 is why the GF(32) superframe exists. Any f-comparison to this paper is impossible.

## §2 Müller 2025 ban resolution

- 6.7 kbit/s — **CONFIRMED** (as raw acquisition/sifting throughput, §3.4). May be cited ONLY with that label; never as SKR or IR throughput.
- 446 vs 3.14 — **CONFIRMED** (mean messages per EC frame, Cascade vs LDPC-Blind, live). Resolves the old "(rounds/messages?)" ambiguity: MESSAGES, not Cascade rounds/iterations.
- FER < 0.003 — **CONFIRMED, scope narrowed**: Cascade FER < 0.003, simulated, 1000 samples, QBER-mismatch sweep (true QBER 2/4/6%); Blind protocol zero frame errors in that simulation. Not a live FER, not a bound, not an LDPC result.
- f = 1.036 / 1.166 — **CONFIRMED** (live 27-h means; f = leak_IR/(n·H(q)), n = 2^16, EV tag excluded from plain f).

Citation policy: all four are now citable WITH the measured-quantity labels above. Still unsafe: citing 6.7 as key rate; 446/3.14 as rounds; 0.003 as a live-system or LDPC FER; 1.036/1.166 as apples-to-apples against f_super (different n, channel, alphabet; EV-tag exclusion). No "our f = 1.29 is worse than published" claim without the §3 decomposition.

## §3 Block-length reality check

- Literature f ≈ 1.04–1.17 sits at n = 65536 b (Müller, binary, live) to 2^30 (Zhou, binary polar). Our superframe = 5120 b; the 240-block experiments are 240 INDEPENDENT paired 5120-b frames (1.23 Mbit total traffic), NOT a long frame.
- Gaps to our 1.294947: +0.129 vs Müller LDPC 1.166; +0.259 vs Müller Cascade 1.036; +0.249 vs Zhou 1.046@2^30; +0.105 vs Zhou 1.190@2^16 (same 65536-b length).
- Accounting: our numerator carries the 64-b whole-frame tag = +0.0751 of f (64/852.544); tagless would be 1.21988 (report-only, never a claim). Tag convention is NOT why literature looks better: Zhou's f INCLUDES a 64-b CRC tag; Müller's f_eff adds t = 50 (≈0.005 of f at n = 65536). At most +0.075 of any gap is tag accounting.
- Finite length: Zhou's own scaling 1.190@2^16 → 1.046@2^30 puts ≈0.144 of f on finite length at 12.8× our length; extrapolating 3.3 further halvings to 5120 b adds ≈ +0.06–0.15 (per-halving cost grows as n shrinks; their "256 Kb matches SLA at 4× the block" bounds the acceleration).
- Channel: their QBER 2–6% / 2%; our design point has H_full = 0.8326 b/symbol ≈ binary-equivalent QBER ≈ 0.26 (entropy-equivalence gloss h(p)=0.8326, not a measured QBER), ~an order noisier, on a structured GF(32) two-layer (u1,u2) channel. No paper reports any f at this noise or alphabet ⇒ the residual (~0–0.1) CANNOT be split between further finite length and channel from these three papers.
- In-repo anchor bounding the question: genie-u1 A208 0/240 at f = 1.294947 (O1R D1) — at this n and this noise, decodability is NOT the binding constraint; the binding constraints are the u1 information path (b2e FAIL 13/13 both arms; b2f soft-marginal PASS) and the 1.3-gate arithmetic (4.31 b headroom).

## §4 Direction questions to ANSWER (not decided here)

(i) Is f ≈ 1.29 at n = 1024 dominated by finite length or by the structured channel? Settling evidence: MC-DE threshold at the joint rate + an m-sweep (m = 180–208) FER curve on the frozen channel; genie A208 0/240 bounds decodability, not minimum achievable f.
(ii) Layered NB-LDPC + soft-marginal (+ conditional HARQ) vs joint single-layer (memo option A2)? Settling evidence: b2g two-construct-instance replication (seed 2026092011); one A2 DE point + construction/FER arm at n = 2048 (~1100 s); A2's density argument (avg check degree 19.7 vs 256–341 layered, 9.8 L2-only) is the only mechanism explaining the layered stall.
(iii) What block length would make our budget competitive, and is it reachable under the frozen superframe/tag accounting? Zhou's curve needs ≈2^18–2^20 bits for f ≈ 1.12–1.19 at QBER 0.02; at our noise no extrapolation is valid. Frozen accounting is per-frame (n = 1024 symbols, 64-b tag, 5 b/row); lengthening changes the science input ⇒ DECIDE. Reachability = decode wall at 2048–4096 symbols vs b2e's ~70 s/decode at 1024.
(iv) Does the industrial/Cascade evidence change the FER gate (fails/240 ≤ 12, i.e. FER ≤ 5%)? Their f_eff arithmetic: at QBER 2% (H = 0.141) a 5% FER costs +0.35; at our H = 0.8326 b/symbol the same FER costs +0.060 — the penalty is ~6× smaller here because our denominator is larger. Settling evidence: an f_eff-style line on our own F202/F208 (FER 0.025/0.0) before any gate change; any gate change is DECIDE.
(v) What does the AIR rate-adaptive evidence imply for per-block adaptation (cf. Scarinzi closure: spread ≈3 b/block, no usable headroom at n = 1024)? AIR adapts frozen-vector schedules at n ≥ 2^16 with the 64-b CRC inside f. Settling evidence for any append attempt: an arm with FER ∈ (0, 12/240] AND ≥ 5 b/row headroom — F202 (6 fails, 34.31 b headroom) is the only current candidate; at F208 (0/240, 4.31 b) an append mechanism has nothing to repair and no budget to repair it with.
(vi) Cheapest DECIDE-grade next step vs cheapest EXPLORE probe? Cheapest EXPLORE: zero-decode reuse of b2g rows (entropy-spread/clustering probes) + dry DE at the joint rate. Cheapest DECIDE-grade: any frozen-input change (n, tag, gate) under prereg + Pre-EXECUTE + independent Pre-RESULT. b2g itself is a synthetic route gate (EXPLORE, EXPLORE_HEAVY annotation); only its route-closing decision is DECIDE.

## §5 Branch-specific implications (IF b2g F208 …; implications only, no decision)

- IF b2g F208 PASSES (both construct instances): the literature says the next question moves from decodability to the denominator: finite-length scaling (Zhou Table 4: each doubling ≈ −0.006…−0.018 f at QBER 0.02) vs our frozen 5120-b frame, and whether the 64-b tag + 5 b/row accounting survives a longer frame (tag cost falls as 1/n). AIR (ε ≈ 1e-8 at f = 1.046–1.190, tag-inclusive) suggests verification headroom is usable at ≥ 2^16, not at 1024 symbols. Implication: a lengthening study (n = 2048/4096 symbols) becomes the literature-backed next question — and it is a DECIDE-grade science-input change.
- IF b2g FAILS: the best literature-backed fallback is A2 (joint single-layer over 2048 GF(32) symbols): Müller's evidence is that short LDPC codes underperform ("our results suggest against the usage of short LDPC codes"; Blind communication at n = 1944 still substantial) — the short/layered regime is exactly where literature offers no efficient recipe; the joint code attacks the density problem (19.7 vs 256–341) rather than the length problem. Zhou's evidence supports investing in length only via a DECIDE-grade accounting change; the Scarinzi closure forecloses the cheap per-block adaptation route at n = 1024. Implication: fund A2 together with the O-B DE/construction work; "wait for longer frames" alone forfeits the synthetic-route evidence.

## §6 Does-not-establish / boundary

- Synthetic-only repo evidence (paired synthetic frames); no real/Jan-21 frames.
- Papers read once, via arXiv HTML — NOT the supplied PDFs (this model cannot read PDF input; deviation recorded in the header); no re-derivation of their math; figure-only values (Müller Figs 2–11; Kanitschar Figs 1–2) were not extracted.
- No change to any frozen quantity (f_super formula, H_full, n, tag, gates); no B2G_*/b2g file touched; this memo authorizes nothing — no packet, no execution, no route decision.

## Corrections (2026-09-21)

Track: EXPLORE documentation-only correction, appended (no existing line rewritten). Branch `formal-ir-v72p1-addendum-clean`. Arithmetic only via `.venv/bin/python`; no decode, no execution.

**(a) Cross-paper FER-penalty comparison — recomputed under ONE consistent convention**

The §4(iv) statement "at our H = 0.8326 b/symbol the same FER costs +0.060 — the penalty is ~6× smaller here" is arithmetically INCONSISTENT and is withdrawn. Two defects: (i) it compares THEIR per-bit entropy h2(0.02) = 0.1414 against OUR per-SYMBOL entropy 0.8326 (mixed units); on a per-bit basis ours is H_per-bit = 852.544/5120 = 0.1665125 — only ~18% from theirs, so no 6× gap is possible; (ii) our +0.060 is exactly FER·leak_EC/H_full = 0.05 × 1040/852.544 = 0.0610, i.e. it prices the leak (saved) term instead of the lost content (n − leak_EC).

Frozen basis (F_EFF_ACCOUNTING_NOTE_20260921.md, commit 68b39f28): n_bits = 5120 (1024 GF(32) symbols), H_full = 852.544 b/frame, leak_EC = 1040 b (m = 208 × 5), tag t = 64 b, f_super = 1104/852.544 = 1.294947. THEIR side (Müller 2025 Eq. (13)/(11)): n = 2^16 = 65536, binary BSC q ≈ 2%, h2(0.02) = 0.1414409; leak implied by their measured f_Cascade = 1.036 / f_LDPC = 1.166.

Penalty at FER = 5%, both conventions, both sides:

| convention (penalty = slope × FER) | ours (n = 5120, leak 1040) | theirs (n = 2^16, q = 2%) | ratio ours/theirs |
|---|---|---|---|
| naive full-frame: FER/H_per-bit | 0.05/0.1665125 = **+0.3003** | 0.05/0.1414409 = **+0.3535** | **0.849** (ours ≈ 15% cheaper) |
| m-saving (Eq. (13)/net basis): FER·(n − leak)/(n·H) | 0.05 × 4.785677 = **+0.2393** | 0.05 × 6.0341 = **+0.3017** (f = 1.036); 0.05 × 5.9041 = **+0.2952** (f = 1.166) | **0.793 / 0.811** (ours ≈ 19–21% cheaper) |

Cross-pairing extremes span 0.677 (ours m-saving vs theirs naive) to 1.017 (ours naive vs theirs LDPC m-saving). Corrected statement: at FER 5% our penalty is +0.239 (m-saving) or +0.300 (naive) vs their +0.354 (naive) / +0.30 (m-saving) — under matched conventions the two sides are COMPARABLE, ours roughly 15–21% cheaper, NOT ~6× cheaper. Our +0.239 gives f_eff = 1.294947 + 0.239 = 1.5342, exactly the frozen note's gate-(a) row.

**(b) Corrected implication for the §4(iv) FER-target question**

- At our basis f_eff = f_super + 4.7857·FER; f_eff ≤ 1.3 requires FER ≤ (1.3 − 1.294947)/4.7857 = 0.001056 ≈ **0.1056%** (frozen-note identity, re-verified).
- Each single fail in a 240-block arm costs 4.7857/240 = **+0.0199** of f_eff (1 fail ⇒ FER 0.4167% ⇒ f_eff = 1.3149).
- b2f F202 (6/240 ⇒ FER 2.5% ⇒ f_eff = **1.4146**) is far outside literature-comparable territory: even on the naive convention Müller's 2.5%-FER penalty is +0.177, and their labelled FER < 0.003 (Cascade, simulated, 1000 samples) is ~8× below F202's 2.5%.
- A 0/240 arm sits exactly at f_super = 1.294947 (f_eff = f_super at FER = 0) — still +0.129 above Müller LDPC 1.166; that residual is n/channel/accounting, not FER.
- Stated plainly: gate-(a) FER ≤ 5% (fails/240 ≤ 12) and any f_eff ≤ 1.3 target are two DIFFERENT, non-interchangeable acceptance bases — a success-frame count threshold vs a FER-aware efficiency target that at our slope de facto demands FER ≲ 0.1056% (fails/240 ≲ 0.25, i.e. effectively a zero-fail arm). Choosing between them, or changing either, is a MAIN-THREAD decision; this memo does not make it.

**(c) Provenance precedence (explicit)**

- This agent's read tool REJECTED the supplied Zhou PDF ("this model does not support pdf input"). No arXiv-HTML substitution was performed by this agent. The Zhou Table 4 figures (f = 1.190@2^16, 1.120@2^20, 1.075@2^24, 1.056@2^27 at QBER 0.02) stand as **"read from arXiv HTML by a prior agent, PDF not re-read"** — flagged, not PDF-verified.
- Precedence rule: a user-PDF-verified reading CONTROLS over any arXiv-HTML-derived value for the same quantity. Accordingly — **Müller et al.** figures (6.7 kbit/s acquisition; f_Cascade = 1.036 / f_LDPC = 1.166; 446/3.14 messages; FER < 0.003; n = 2^16; t = 50) are user-PDF-verified (F_EFF_ACCOUNTING_NOTE_20260921.md) and control. **Zhou et al.** figures remain arXiv-HTML-derived and flagged unless/until a direct PDF reading (user or agent) supersedes them. **Kanitschar & Huber** figures remain arXiv-HTML-derived; usage is context-only and no numeric claim rides on them.
- No literature figure was re-derived or numerically changed by this correction; only the cross-paper FER-penalty arithmetic was recomputed, from frozen in-repo constants plus h2(0.02).

**(d) Does-not-establish**

No decision; arithmetic only; no decode; no execution; no change to any frozen gate or quantity (f_super formula, H_full, n, tag, gate-(a)/(b)); no B2G_*/b2g file touched; `LITERATURE_RECOMMENDATION_TRIAGE_20260921.md` and `B2G_RESULT_20260921.md` untouched. The withdrawn "~6× cheaper" statement must not be reused as a basis for §4(iv); §4(iv) remains an open question for the main thread. This memo still authorizes nothing.

**(e) Per-arm-own-basis correction to (b) — b2f F202 f_eff and the gate-(a) FER=5% reference pair (commit aadc0428)**

Subsection (b) priced f_eff on the F208 basis (f_super = 1104/852.544 = 1.294947) throughout, which is the WRONG basis for an m = 202 arm. Per commit aadc0428 (per-arm own-basis f_eff), an m = 202 arm must be priced on its OWN basis f_super(m = 202) = 1074/852.544 = 1.259759:

- b2f F202 (6/240 => FER 2.5%): f_eff = 1.259759 + 4.7857×(6/240) = **1.3794**. This SUPERSEDES the "b2f F202 (6/240 -> f_eff 1.4146)" line in (b): the 1.4146 value = 1.294947 + 4.7857×0.025 was computed on the m = 208 basis and does not belong to an m = 202 arm. (Arithmetic re-verified via `.venv/bin/python`; the frozen per-arm-own-basis value 1.3794 is from commit aadc0428.)

Gate-(a) FER = 5% reference points (fails/240 <= 12), stated on BOTH bases so neither is dropped:

| basis | f_super | f_eff at FER = 5% (f_super + 4.7857×0.05) |
|---|---|---|
| m = 202 (own basis) | 1074/852.544 = 1.259759 | **1.4990** (1.259759 + 0.239285) |
| m = 208 (own basis) | 1104/852.544 = 1.294947 | **1.5342** (1.294947 + 0.239285) |

The m = 202-basis value at FER 5% is **1.4990** (NOT the ~1.4186 that (b)'s M=208-basis reading would imply for an m = 202 arm at FER 5%); the m = 208-basis value at FER 5% is **1.5342** (already the frozen note's gate-(a) row recorded in (a)). These two bases are NON-INTERCHANGEABLE (as already established): an m = 202 arm's f_eff must use 1.259759 and an m = 208 arm's must use 1.294947 — mixing them is exactly the defect this correction removes. Arithmetic only via `.venv/bin/python`; no decode, no execution, no gate or frozen-quantity change.
