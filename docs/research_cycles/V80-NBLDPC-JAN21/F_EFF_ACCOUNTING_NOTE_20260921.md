# f vs f_eff accounting note (2026-09-21) — EXPLORE documentation-only, no execution

Track: EXPLORE documentation-only (no execution, no decode, no gate change). Branch `formal-ir-v72p1-addendum-clean`.
Source: user-supplied full PDF of Müller et al. 2025, *IET Quantum Commun.*, DOI `10.1049/qtc2.70003` (user-verified reading). This note RESOLVES the standing "Müller numbers unverified" ban; it authorizes nothing.

## 1. Verified figures (confirmed from the PDF, no longer inference)
- Raw acquisition throughput ≈ **6.7 kbit/s**; **f_Cascade = 1.036 / f_LDPC = 1.166**; mean number of messages **446** (Cascade) vs **3.14** (LDPC); Cascade **FER < 0.003** over 1000 samples.
- Frame: **2^16-bit EC frame, SPA 50 iterations, α = 1**; their Fig. 9 uses **t = 50, P_Collision = 1e-10**.
- Blind LDPC protocol — **zero FER is NOT an exact-recovery guarantee under a finite budget**. Quotes (verbatim from the PDF):
  - "Per design, the blind protocol does not allow for frame errors, as it will always converge by revealing more and more symbols"
  - "has no frame errors by design apart from syndrome errors"
- **Citation hazard (now verified)**: their reference **[15] is the RETRACTED paper** — Mao, Li, Hao, Abd-El-Atty, Iliyasu, *Opt. Quantum Electron.* **54 (2021) 163**. Do not trace throughput comparisons along that line. Our standing ban (Mao-group = never a source) is reinforced, not relaxed.

## 2. Their tag/verification term t ≈ our 64-bit tag
- t = 64/852.544 = **0.075070**, matching the tag share **0.0751** already recorded in `PROGRAM_PLAN.md` §1.3 and `S2_ROUTE_DECISION_MEMO_20260921.md`.
- ⇒ our `f_super` (whole frame + 64-b tag in the disclosure denominator) is **STRICTER** than a typical literature `f`, which omits the tag. This may be stated explicitly in claims.

## 3. Their Eq. (13) ≡ our net accounting
- Their Eq. (13): `n·H(q)·f_eff = (1 − FER_c − P_C)·leak_IR + n·(FER_c + P_C) + t` — failed frames counted at full-frame `n` bits.
- Mathematically equivalent to our net accounting (`net = A·5n − leak`): both are verification-aware and FER-aware. Eq. (13) can be cited as **external support** for our accounting instead of self-justifying it.

## 4. Derived identity and recomputed table (independently re-verified with `.venv/bin/python`, arithmetic only)
Constants: H_full·n = 852.544 b; m = 208 rows ⇒ content 1040 b; 64-b tag ⇒ numerator 1104 b.
`H_per-bit = 852.544/5120 = 0.166512544`; `f_notag = 1040/852.544 = 1.219878`; `tag = 64/852.544 = 0.075070`; `f_super = 1104/852.544 = 1.294947`; `slope = (5120−1040)/852.544 = 4.7857`.

| FER | f_eff = f_super + 4.7857·FER |
|---|---|
| 0.05 (S2 gate-(a) threshold, fails/240 ≤ 12) | **1.5342** |
| 0.01274 | 1.3559 |
| 0.005 | 1.3189 |
| 0.00105 | 1.3000 |
| 0.025 (b2f F202, 6/240) | **1.4146** |
| 0.0 (b2f F208, 0/240) | **1.2949** (= f_super) |

- FER giving exactly 1.3: `(1.3 − 1.294947)/4.7857 = 0.0010557 ≈ **0.1056 %**`.

## 5. KEY POLICY DISTINCTION (standing reporting rule)
- The frozen gate (b) `f_super ≤ 1.3` is a **SUCCESS-FRAME quantity**, NOT a literature-comparable `f_eff`.
- Any arm with **FER > 0** must be reported with **BOTH** numbers: gate-(b) `f_super` (success-frame) and `f_eff = f_super + 4.7857·FER` (FER-aware).
- **1.294947 (or 1.259759) must NEVER be quoted as `f_eff`.** At the S2 gate-(a) threshold FER = 5%, `f_eff = 1.5342` — the two quantities are not interchangeable, and `f_eff ≤ 1.3` de facto requires **FER ≲ 0.1 %**.
- This is **not a contradiction**: net remains positive at FER = 5 % because our raw-key/entropy ratio is ≈ 6:1. It is a **reporting-basis** distinction, not a gate relaxation.

## 6. Three further transferable items
1. Their "**cluster frames for EV to choose optimal k**" (Eqs. 11/12, Fig. 9) is the principled version of our empirical 4-frame superframe tag amortization; they note the penalty is worst at **high FER / short block / low QBER** — exactly our regime.
2. "**One repeat request allowed per cluster**" ⇔ our v52/v54/v55 conditional rescue (**HARQ**).
3. **QBER / channel estimation should be conservatively OVER-estimated** ("underestimation has a higher penalty", because blind protocols keep revealing symbols) ⇒ when per-block Ĥ is eventually used, **bias high** for safety.

## 7. Does NOT establish
- Single reading of one PDF; their math not re-derived by us; no real / Jan-21 data; no change to any frozen gate or quantity; no new measurement performed; this note authorizes nothing.
