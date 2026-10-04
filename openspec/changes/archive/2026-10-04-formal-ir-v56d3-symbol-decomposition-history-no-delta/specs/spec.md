# Delta Spec: formal-ir-v56d3-symbol-decomposition

## ADDED Requirements

### Requirement: V56D3 Provenance Remediation
The diagnostic SHALL record the actual code state of `src/qkd_io/ttbin_pipeline.py` (`git diff`, `HEAD == origin/formal-ir-mainline == implementation SHA`) and SHALL NOT leave execution-time optimizations in `src/` (frozen baseline). The chunk optimization SHALL be moved to the diagnostic script as an inline function. A small-sample equivalence proof (`≤1k` events, `counts_old == counts_chunk` per bin `np.array_equal` PASS) SHALL be persisted. If a deviation existed at `run03` execution, `v56d2_calibration_run03.json` SHALL be amended to `provenance_deviation=true` and `overall=RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION` and not be cited as authoritative.

### Requirement: V56D3 Permutation-Insensitive Mutual Information
The diagnostic SHALL compute per-source `H(A), H(B), H(A|B), I(A;B)` (bits/symbol, `log2`) from `pairs.parquet` joint counts `C(a,b)` for both V13 reference and the three new sessions, and report the contrast. The method SHALL be `numpy`-only, decoder-free, and explicitly permutation-insensitive (global `b'=π(b)` leaves `H(B)` and `I` unchanged).

### Requirement: V56D3 Identity vs Empirical MAP
The diagnostic SHALL report per-source `acc_identity = mean(a==b)` and `acc_map = mean(a==a_MAP(b))` where `a_MAP(b)=argmax_a C_fit(a,b)` learned on `fit 4 frames` and evaluated on `val 4 frames` (disjoint, `fit=[7,8,9,10] val=[15,16,17,18]` pre-registered, same-frame evaluation forbidden). `acc_map` is the per-symbol optimal relabeling upper bound.

### Requirement: V56D3 Physically-Motivated Mapping Families Only
The diagnostic SHALL enumerate only the five pre-registered physically-motivated families: `global cyclic shift (1024)`, `global XOR (1024)`, `32×32 axis swap/flip (≤8)`, `Gray↔binary (2)`, `32*U1+U2 vs 32*U2+U1 (2)` — total `<5k` candidates. Arbitrary `1024` permutations or `1024!` searches SHALL NOT be performed. Each family SHALL be selected on `fit` (`argmax acc` or min `NLL` via `channel_counts.npz`) and reported on `val` (`acc/NLL/q_mass/mass_0±1`).

### Requirement: V56D3 Stage-Wise Pipeline Check
The diagnostic SHALL check `paired timestamps → bin (200ps) → frame anchor (peak_center vs global min, floor_div, period 204800) → symbol (legacy_v1) → U1/U2 (F03 5+5)` stage by stage, computing `I/acc` at each truncation and reporting `first_collapse_stage`.

### Requirement: V56D3 Three-Way Shunt
The diagnostic SHALL shunt to exactly one of `SYMBOL_MAPPING_CONTRACT_ERROR` (high `I` + val recovery by some physical `π`), `PAIRING_OR_FRAME_ANCHOR_ERROR` (high `I` + raw timing healthy + no physical `π` recovers), or `TRUE_ACQUISITION_DOMAIN_SHIFT` (low `I` itself). `TRUE_DOMAIN_SHIFT` is the only state that plans new `prior/leakage` (`TRAIN-only`, source-adaptive `m_total`). The report SHALL state that the original V55 `90` will never be rerun and the main algorithm (`H1/Lane C/Δ8/decoder`) is not negated.

### Requirement: V56D3 Decoder-Free Guard
The diagnostic SHALL remain `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`: zero `decode_*` calls (`rg "decode_" 0 hits`), no change to `H1/Lane C/H_inc1/2/Δ8/decoder/m2/leak/prior`, no `.../v56d3_*/run_01` creation, no rerun on the original `90`, `py_compile` PASS, and `fit ∩ val == ∅` verified.

## MODIFIED Requirements

### Requirement: V56D2 Calibration Provenance Note
`v56d2_calibration_run03.json`'s `overall` MAY be amended from `FAIL_NEED_FIX` to `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION` when the `src/qkd_io` deviation is confirmed, with an explicit `provenance_note`.

## REMOVED Requirements

None. All prior `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` guards remain.
