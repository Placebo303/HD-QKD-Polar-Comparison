# Decoder-free GF(32) short-cycle census — result

**Track:** EXPLORE  
**Batch:** `475c2ad3-bd5a-4000-8498-ea989bad1bba`  
**Status:** `INVENTORY_COMPLETE`; main accepted with comments after independent batch-end review.  
**Machine root:** `workspace/gf32_cycle_census_475c2ad3/`

## Scope and execution

The frozen inventory used the six n=128, m=52, E=256, GF(32)/polynomial-37 graphs with seeds 2026093901–2026093906. The matrices are inherited from the accepted fixed-p0=0.55 synthetic iid marginal-shape edge-label pair; this census itself is deterministic matrix-structural enumeration, not a sampled channel run. It reconstructed the accepted deep-control and full one-pass edge-label matrices from the predecessor helpers, checked admission and predecessor diagnostics, then enumerated the shared support once per graph for simple Tanner cycles with variable length ell=2..6. No D10 graph rebuild, sampled frames, truth/prior arrays, or decoder calls were used. The decoder-call and sampled-frame counts are both zero.

The independent reviewer matched all 69,412 reconstructed coefficient entries through the accepted edge-coordinate lookup; no D10 rebuild was needed. All six graphs completed, with an empty stop reason. Per-graph DFS states and cycle counts were:

| Seed | DFS states | Cycles (ell=2,3,4,5,6) |
|---|---:|---|
| 2026093901 | 14,260 | [0, 1, 5, 123, 380] |
| 2026093902 | 14,744 | [0, 0, 8, 117, 399] |
| 2026093903 | 14,143 | [0, 1, 6, 123, 365] |
| 2026093904 | 14,199 | [0, 1, 9, 108, 375] |
| 2026093905 | 14,669 | [0, 1, 11, 115, 360] |
| 2026093906 | 14,250 | [0, 1, 10, 104, 403] |

## Inventory

Each vector below is ordered ell=2,3,4,5,6. A state transition counts a cycle that is unit-product in control and nonunit in the edge candidate, or vice versa.

| ell | Cycles | Control unit | Edge-candidate unit | Control unit → edge nonunit | Control nonunit → edge unit |
|---:|---:|---:|---:|---:|---:|
| 2 | 0 | 0 | 0 | 0 | 0 |
| 3 | 5 | 0 | 0 | 0 | 0 |
| 4 | 49 | 1 | 2 | 1 | 2 |
| 5 | 690 | 34 | 34 | 31 | 31 |
| 6 | 2,282 | 70 | 85 | 64 | 79 |
| **Total** | **3,026** | **105** | **121** | **96** | **112** |

| Seed | Control unit by ell | Edge-candidate unit by ell | Control→edge nonunit by ell | Control nonunit→edge by ell |
|---|---|---|---|---|
| 2026093901 | [0,0,0,5,10] | [0,0,0,4,10] | [0,0,0,4,9] | [0,0,0,3,9] |
| 2026093902 | [0,0,0,6,9] | [0,0,0,5,14] | [0,0,0,6,8] | [0,0,0,5,13] |
| 2026093903 | [0,0,0,7,12] | [0,0,0,6,17] | [0,0,0,6,11] | [0,0,0,5,16] |
| 2026093904 | [0,0,0,9,16] | [0,0,1,5,12] | [0,0,0,8,14] | [0,0,1,4,10] |
| 2026093905 | [0,0,1,5,11] | [0,0,0,5,13] | [0,0,1,5,11] | [0,0,0,5,13] |
| 2026093906 | [0,0,0,2,12] | [0,0,1,9,19] | [0,0,0,2,11] | [0,0,1,9,18] |

Across the 3,026 shared cycles, the four arm-state counts were both unit=9, neither unit=2,809, control-only unit=96, and edge-candidate-only unit=112. Thus the control matrix and edge candidate each have `UNIT_PRESENT_IN_RANGE`. This is an availability diagnostic for the frozen six matrices and ell range only.

The CSV stores the ordered incidence coefficients, GF(32) product and unit flag for both matrices, plus the normalized local witness values for every unit arm-cycle. It contains 226 arm-specific unit-witness records (105 control and 121 candidate; nine cycles are unit in both). The independent reviewer recomputed all 6,052 matrix-cycle products and submatrix ranks. Every unit witness is normalized with its first cycle-variable value equal to one and satisfies every cycle check; the corresponding cycle submatrix rank is ell−1 for unit product and ell for nonunit product.

## Budget and claim limits

The frozen limits were 1,800 s total wall time, 4 GiB RSS, 2,000,000 DFS states and 100,000 unique cycles per graph. Pre/post-graph and every-1,024-state resource checks ran; no wall/RSS/cycle/state STOP occurred. Every graph used at most 14,744 DFS states and 524 cycles. The implementation did not persist actual elapsed wall time or peak RSS, so exact resource usage and budget margin are `NOT_RECORDED` and cannot be recovered from these artifacts. No value is imputed.

The local degree-2 cycle equation follows the cycle-local symbol-weight discussion cited in the packet ([Poulliat, Fossorier & Declercq, ISIT 2006, §IV.A, Eq. 2](https://perso.etis-lab.fr/declercq/PDF/ConferencePapers/Poulliat_2006_ISIT.pdf)). A unit product supplies a nonzero GF(32) symbol assignment confined to that simple cycle. This is not a binary Hamming-weight result, a global minimum-distance result, or a FER/decoder-benefit result. A nonunit cycle does not exclude a codeword on composite support. The iid uniform-label probability formula is not applied to these optimized frozen labels.

No pooled performance or cross-batch ranking, conditional-channel claim, FER, `f_eff`, SKR, throughput, qualification, publication, or route conclusion follows. The inventory does not authorize a longer-cycle range, another graph, a decoder run, or a follow-on experiment. Any successor requires its own frozen packet and main dispatch under the bounded ongoing EXPLORE scope.

Independent `faithful_scope` batch-end review passed P1–P7 with comments; the reviewer was not the operator. Main acceptance is limited to this inventory and its stated evidence ceiling. It does not accept a route or promote an NB-LDPC family claim.

## Artifacts

The machine root contains exactly `manifest.json`, `cycles.csv`, `summary.json`, and `EXPLORATION_LOG.md`. The append-only log preserves the six graph completion markers and empty terminal stop reason. Implementation tests were fake/tiny-only: 8 passed. No commit, push, merge, or archive was performed.
