# Independent acceptance — GF32 train-source mapping

Date: 2026-09-30  
Track: DECIDE  
Batch UUID: `6f821d0b-71e3-46c1-ae84-2da374edbcc2`  
Independent reviewer: `/root/source_contract` (not the operator)  
Main-thread decision: **ACCEPTED**, limited to the descriptive historical
documented-train evidence in `RESULT.md`.

## SM7 — Pre-RESULT

**PASS.** The reviewer independently read only the actually attempted,
F1-admitted train count arrays and allowed provenance records. It recomputed
`C[e,b]` for each source by each Alice row, then checked all 32 `E1` counts,
source totals, normalized summaries, `H(E1)`, `H(E1|B)`, `I(E1;B)`, nonzero TV,
and error-count-weighted conditional nonzero TV. Every bin and formula matched
the operator output with maximum absolute difference `<=1e-12`; no pooled count
or conditional array was exported.

The reviewer also confirmed source IDs, role fields, split ratios and source
totals across the four allowed JSON records; all three arrays had shape
`1024×1024`, float64 C-order, and finite nonnegative integer-valued entries.
Each error-bearing Bob column had singleton nonzero-`E1` support: 41/41,
43/43, and 51/51. The reviewer confirmed the `TV_B=30/31` result, the
per-source sparse-count caveat, the `0.197906 s` wall time, peak RSS
`46,235,648` bytes, and exactly three files in the fresh result root.

## Main-thread acceptance and ceiling

The main thread accepts `DESCRIPTIVE_MAPPING_COMPLETE` as historical,
source-specific `DOCUMENTED_TRAIN_ROLE_CONSISTENT` evidence. Acceptance does
not establish independent raw-split reconstruction: frame boundaries were not
saved and the stored records do not bind an exact writer version to the NPZ
bytes. No current Model-F transfer, causal or stationary channel law,
confidence statement, qualified prior, FER/SKR, method gain, qualification, or
route decision is accepted.

No decoder ran and there was no scientific retry or repair. The quoted user
grant “可以继续下一步” is consumed by this batch. No successor is authorized;
the main-thread follow-up suggestion in `RESULT.md` remains an unaccepted
question requiring a new packet and grant. No commit, push, merge, or archive.
