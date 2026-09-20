# S2 V1 Diagnostic — 20260920 (EXPLORE mechanics; raw evidence only)
- Scope: in-memory + /tmp probes only; no code/root/workspace writes; no campaign rerun; no FER/decision claim.
## D1 Hook semantics (code inspection)
- Campaign path: `v80_s2_fer_campaign.py:125-127` `_default_decode` → `s2.smoke_decode_frame(construction, seed, max_iter=300, qber=0.05)`, sampler=None → default hook.
- Hook `v80_s2_peg.py:267-294` `qsc_pair_sampler`: SYMBOL-level — `alice=integers(0,32,n)`; `flip=random(n)<p` per symbol; `bob=where(flip, alice^shift, alice)`, shift uniform 1..31. p = per-SYMBOL rate, not per-bit. GF(32) add=XOR (char-2; q pinned 32, else ValueError).
- Decode binding `v80_s2_peg.py:321-323` → `decode_error_domain(bob, dense, s_x, qber, ...)`; inside `nonbinary_v10_fftqspa.py:513-529`: prior=QSC(qber) on error symbols, `s_e=s_x+H*y`, `x_hat=y+e_hat`, ok:=(H*x_hat==s_x). e=x+y char-2 throughout — NO sign/domain mismatch; y enters only via H*y; prior p matches sampler p (0.05=0.05).
- Declared gap (not defect): V17 convention is per-bit-plane structured + Gray (MSB→LSB monotone; "per-bit-plane mismatch/Gray folding is the limiting factor"); hook is uniform-symbol QSC. Packet §2: hook is "the ONLY executable hook today; ... PROXY, not the V17/V25 kernel (no such kernel exists in-repo...)". Unit note: p=0.05 is symbol-rate ≠ bit-level QBER (5%/bit ⇒ ~22.6% symbol).
## D2 Campaign rows (`workspace/s2_fer_2752f403/rows.json`, read-only)
- 16/16 exact_match=false, converged=false. NOT all max_iter: 4/16 hit iter=300 (3×max_iter_reached + 1×conv_nosynd-at-300); 12/16 early `converged_no_syndrome` (streak=3 wrong-e_hat lock, incl. 3× iter=7).
- g0: 7/300/300/204 (0.44/19.65/19.82/13.69 s); g1: 7/300/90/192 (0.43/19.46/6.08/12.77 s); g2: 174/238/192/174 all conv_nosynd (11.55/15.70/12.43/11.02 s); g3: 300/88/7/300 (18.80/5.40/0.43/18.47 s).
## D3 Noise ladder (construct seed 2026092001/trials 20; frame seed 2026096001; qber=0.05 frozen; max_iter=300)
- p=0.0 (noiseless custom sampler; stock hook rejects p=0): success iter=1 exact 0.07 s — plumbing sound.
- p=0.005: success iter=2 exact 0.13 s. p=0.02: status success iter=2 BUT exact=false (wrong-codeword miscorrection, H*x_hat==s_x) — low-weight-codeword evidence, recorded only.
- p=0.05 (exact campaign hook): converged_no_syndrome iter=7, 0.46 s — reproduces rows.json g0f0 in-memory.
## D4 Control (module has NO all-zero control; minimal in-memory sampler: alice=zeros(256), bob=QSC p=0.05)
- Zero codeword at p=0.05: converged_no_syndrome iter=100, 6.28 s, exact=false — fails even on the zero codeword; not hook/plumbing-specific.
## D5 V2 rule (packet §1, exact quote)
- "V2 (fallback/quality arm, runs IFF V1 verdict=FAIL): `construct_l2(seed=2026096101, max_trials=100)` — the ONLY allowed improvement rule (more PEG trials; constructor-kept minimum). Valid IFF `four_cycles < 1158`, else V2 arm FAILs closed."
- V2 IS implementable frozen (exact seed/trials/predicate, no invention). Implied target: four_cycles strictly <1158 (any 0..1157; no lower bar). Side note: V1 reconstruction reports min_girth=0 with four_cycles=1158 (reporting quirk, out of scope).
## Mechanics verdict: PLUMBING-SANE
- p=0 converges iter=1; p=0.005 exact; campaign frame reproduced exactly. No suspect line (hook/decoder binding consistent: `v80_s2_peg.py:293,321-323`; `fftqspa.py:516,526-527`). Leading (non-conclusive) explanation: construction weakness at p=0.05 symbol noise (zero-codeword failure + p=0.02 miscorrection); decoder budget secondary (most frames lock wrong early via streak, not at cap).
## Correction note (2026-09-20, external review)
- Scope narrowed: PLUMBING-SANE excludes basic wiring errors only — not construction/decoder quality.
- min_girth=0 has concrete cause (BFS unreachable −1 then +1), not a reporting quirk.
- `converged_no_syndrome` = hard-decision streak stability, NOT soft-message convergence (premature-stop not excluded).
- p=0.02 case reworded: "wrong same-syndrome solution, weight unmeasured" (drop "low-weight codeword" phrasing).
- See `S2_CONSTRUCTOR_DEFECT_REVIEW_20260920.md`; causal attribution paused pending constructor fix.
