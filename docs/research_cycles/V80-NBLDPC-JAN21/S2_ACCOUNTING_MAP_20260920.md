# V80 S2 Accounting Map (2026-09-20) — edge-c freeze, docs-only

- Track: EXPLORE docs-only. Branch `formal-ir-v72p1-addendum-clean` unchanged.
- No execution, no commit/push, no authorization. Closes batch-end-review edge-c only.
- Anchors: H_full=0.83256272, n=256/1024, GF(32)² width 5, m₂=47, m₁≈2, m_total=49.

## 1. Basis translation (m₂=47, m_total=49)

| Basis | Formula | Value |
|---|---|---|
| Layer-local (DE gate) | f_layer=5·m₂/(n·H_L2), H_L2≈0.807 | ≈1.1375 (repro 1.1373–1.1379) |
| Whole-frame tagless n=256 | 5·49/(256·H_full)=245/213.136 | ≈1.150 |
| Whole-frame WITH tag n=256 | (245+64)/213.136=309/213.136 | ≈1.450 (never ≤1.3) |
| Whole-frame WITH tag superframe n=1024 | (4·245+64)/(1024·H_full)=1044/852.544 | ≈1.2246 (repro f_super=1.224570) |

Frozen formula: f_super=(4·(5·(m₂+m₁))+64)/(1024·H_full), H_full=0.83256272.

## 2. Consequence for S2 targets

- Under frozen convention, m₂=47 achieves f≈1.2246 < 1.3 budget ⇒ S2
  construction target feasible only at superframe n=1024 (n=256 single-frame impossible).
  [2026-09-20 wording correction — history retained, claim narrowed:
  预算可容纳，构造与 FER 待验证. Budget 1.2246 < 1.3 holds BUT depends on
  L1≈2 rows, four frames sharing one 64-bit tag, zero extra disclosure;
  headroom is only 64.31 bits/superframe (1108.31−1044); L1 actual redundancy
  + blind-reconciliation extra disclosure must still be counted.]
- Row budget: m_total=49 rows × 5 bits per 256-frame; superframe leak 4×245+64=1044.
- Construction rate (frame-layer basis, labelled): 1−49/256≈0.8085. FER≤5% goal unchanged.

## 3. Authority rule (never mix)

- Gate adjudication: layer-local f (S1 frozen semantics) decides DE pass/fail.
- Program/net-yield claims: whole-frame-with-tag superframe f decides f≤1.3 and net yield.
- Never compare a layer-local number against the 1.3 budget, nor a tagless number as a claim.

## 4. Arithmetic verification (pure math, no project imports)

`.venv/bin/python -c "H=0.83256272;C=256*H;print(round(245/C,4),round(309/C,4),round(1044/(4*C),6))"`
→ `1.1495 1.4498 1.22457` ⇒ 1.150 / 1.450 / 1.2246; layer 1.1375 via H_L2≈0.807; rate 0.8086. MATCH.

## 5. Status

- This file closes edge-c (f-basis mapping the S2 prereg must carry).
- S2 is STILL not authorized: needs its own OpenSpec change + fresh grant + Pre-EXECUTE. No S2 entry.
