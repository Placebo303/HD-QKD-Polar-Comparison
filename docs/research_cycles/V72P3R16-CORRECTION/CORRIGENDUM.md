# R16 Corrigendum — net-secret convention correction (n-based)

Reviewer-go R16a review verdict: PASS (transcribed as reviewed, not re-judged).
Main-thread ACCEPTANCE: granted for the convention correction
(n-based `net_secret_bits` added; old keys frozen).

NO execution / decoder / commit. 0 real calls. Documentation solidification only.

## 1. Lineage finding

- `k = n − m` entered G6 bare (no frozen definition of the net-secret key).
- R9 cited G6 circularly, inheriting the bare `k`-based convention.
- The beta denominator was already full-N (correct); only the net key was wrong.
- Net semantics in the roots were inconsistent — 3 semantics in play:
  (a) R9 stored net gross-unsubtracted;
  (b) R11 / R12 stored retained−disclosure;
  (c) the corrected convention below.
- Hence a corrigendum, not a rerun: counts and terminals stand; only the
  reporting key is corrected.

## 2. Correction

- ADD `net_secret_bits = A·5·n − D`, where A = accepted frames,
  n = block length in symbols, 5 = bits/symbol, D = total disclosure bits.
- Old keys (`reconciled_net_bits` and predecessors) are FROZEN with
  SUPERSEDED comments; values on existing roots are not rewritten.
- Schema-stable: no key renamed or removed; one additive key only.

## 3. Code map

- 5 runners corrected additively (net key added alongside frozen old keys).
- Aliasing documented: old key → SUPERSEDED, new key canonical.
- R1 standalone justification: R1 runner carries the convention independently
  so the earliest root is interpretable without back-porting.

## 4. Tests

- 5 new tests PASS (n-based net formula, frozen-old-key retention,
  SUPERSEDED annotation, aliasing, recomputed-net vectors).
- Full suite 65 PASS; R1 10/10 PASS.
- 5 absence-waivers recorded (targets absent by frozen design, not by omission).

## 5. Recomputed nets (reporting-only)

- G6-R1: −68352.
- R9: −71552 [= 1·76 − 127·564] (1 accepted frame at 76 net, 127 exhausted
  frames at −564 disclosure each — illustration of the arithmetic, not new data).
- R11: −27752.
- R12: −33232.
- Per-stage economics (per accepted frame): S0 +76 / S1 +36 / S2 −24 /
  exhausted −664.
- Old roots fail verify with exactly 1 expected violation (missing new key),
  confirming the additive-only change.

## 6. Terminals

- TERMINALS UNCHANGED: all terminals are count-gated; nets are reporting-only
  (reviewer-confirmed). No promotion, qualification, or route verdict changes
  from this corrigendum alone (G7 revision lives in G7-MEMO-CORRECTION.md).
