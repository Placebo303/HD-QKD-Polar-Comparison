# Design — V72P2D8 rate-aligned GF32 ensemble feasibility (L1-first)

Frozen contract for the future DE sweep. E01–E06 only; E07–E12 future.
Full inventory/ranking evidence: `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/READINESS_R1.md`.

## 1. Reused DE engine and exact delta

Reuse (unchanged import, never copy):
`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py`
(`run_mcde_posterior`, `make_rho`, `build_gf_perm_table`,
`check_update_mcde_posterior`, `variable_update_mcde`, `belief_update_mcde`)
with its V14 kernels (`nonbinary_v14_mcde.py` `_variable_or_belief_jit`,
`_wht_row_jit`, `_FLOOR=1e-300`) and V9 helpers
(`nonbinary_v9_mcde.parse_degree_hist`, `entropy_base_q`;
`nonbinary_v9_common.edge_mean_inverse`, `concentrated_check_distribution`).
Field: `nonbinary_field.GF2mField.create(32)` — m=5 polynomial `0b100101 = 37`
(identical to the current decoder field). Accepted evidence for this engine:
V26 gate canonical `run_02` (A02 GF32+GF32 30/30 at f=1.3), V27 gate
`run_01` (`pass_finite_budget_ready`), V37R1 P1 screening (2,349 DE runs,
`P1_NO_FINITE_FEASIBLE_DE_ADVANCE`).

D8 delta (the only new code, one thin adapter + one runner + one focused test
file; E07–E09):

1. New L1-only channel sampler from the accepted CAL-only Model-F artifact
   (design §2). No V25 `channel_counts.npz`, no L2 joint, no V37 source loop.
2. Rate/ρ mapping helper equivalent to `nonbinary_v27_gate.layer_rate_rho`
   (`nonbinary_v27_gate.py:185-189`): `R = 1 - m/n`, `ρ = make_rho(R, λ)`.
3. Bounded deterministic candidate enumeration (§4) and the frozen rank key
   (§5).
4. Runner `scripts/v72p2d8_rate_aligned_ensemble_development.py` with
   `--de-sweep` / `--verify` and the fresh root of §6.
5. Focused tests (§7). Nothing in V26/V27/V37/V14/V9/v35 is edited.

## 2. GF32/channel message representation and normalization (E03)

Exact decoder-facing L1 chain (no scalar surrogate, no BSC/AWGN/q-SC):

| step | artifact / operation | source (path:line) |
|---|---|---|
| 1 | `counts_ab` (1024,1024) axis (Alice,Bob), `p_b` (1024,), `lambda_star=137.3823795883264`, CAL-only 1024 frames × 256 pairs | `workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz`; `MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md` A01 |
| 2 | `pb = p_b / p_b.sum()` | `scripts/v72p2d6_graph_mother_development.py:791` |
| 3 | `P_F = (counts_ab + λ*·p_global[:,None]) / (n_b[None,:] + λ*)`, `p_global = counts.sum(axis=1)/total`, `n_b = counts.sum(axis=0)` (E2 concentration backoff, D6-current prior) | `v72p2d5_gf32_rate_mother.py:275-306` (`build_f_model_concentration`), `:2480-2507` (`prepare_model_f_prior_candidate`) |
| 4 | `P1 = marginalize_f_to_p1(P_F)`: reshape `(1024,1024)→(32,32,1024)`, sum U2 axis, renormalize per Bob column (uniform fallback) | `v72p2d5_gf32_rate_mother.py:309-321` |
| 5 | per-sample decoder prior `pr1 = _floor_renorm(P1[:, b].T, 1e-15)` (floor then renormalize; `DECODER_FLOOR=1e-15`) | `v72p2d5_gf32_rate_mother.py:346-351`; D6 `scripts/v72p2d6_graph_mother_development.py:817` |
| 6 | DE input: draw `(b,a) ~ P_B(b)·P_F(a|b)`; `u = a//32`; centered row `c[e] = pr1[u XOR e]`, `e=0..31` | V26 convention `nonbinary_v26_channel.py:275-280`; `symbols_to_layers` `v72p2d5_gf32_rate_mother.py:401-406` |

- Message form: full length-32 probability vectors, row-normalized
  (`nonbinary_v26_mcde._channel_rows_from_centered`, `POSTE_RTOL=1e-6`); the
  check update is the coefficient-permuted WHT XOR convolution matching the
  current decoder's `sum_e h_e x_e = 0` law (`_check_update_coeff_jit`
  `nonbinary_v26_mcde.py:48-90` vs `v35_algorithm_development.py:453-513`);
  the nonzero coefficient permutation `inv(h)·y` is identical in both.
- The 32-ary distribution is preserved **exactly**: every DE channel row is an
  accepted-prior row reindexed by XOR (an exact translation symmetry of the
  linear code: with `E = X - u_true`, the check constraint
  `Σ h_e X_e = s_r` becomes homogeneous `Σ h_e E_e = 0`). The residual modeling
  step is the standard DE i.i.d.-population exchangeability (already present in
  the accepted V26/V27/V37 line), not a channel substitution. The D5 G2/X4
  frozen per-cell pseudocount variant (`build_f_model`) is therefore not the
  D8 channel anchor; it is recorded as an out-of-scope sensitivity variant
  (one variable at a time).
- DE normalization: `_FLOOR=1e-300` inside the kernel, per-iteration fresh
  channel draws, check-population entropy observable (`entropy_base_q`).

## 3. Rate / degree / check-row equations (E04)

1. Row-budget rate: `R = 1 - m/n`; accepted D6 budget prefixes
   (`v72p2d6_gf32_graph_mother.py:32-36`;
   `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md:58-59`):

| n | L1 f1.0 / f1.2 / square | L2 f1.0 / f1.2 / square | m/n (L1 f1.2) | R (L1 f1.2) |
|---|---|---|---|---|
| 64 | (49, 59, 64) | (43, 52, 64) | 59/64 = 0.921875 | 5/64 = 0.078125 |
| 128 | (98, 118, 128) | (86, 104, 128) | 118/128 = 0.921875 | 0.078125 |
| 256 | (196, 236, 256) | (172, 208, 256) | 236/256 = 0.921875 | 0.078125 |

Rate-aligned identities: L1 f1.0 `49/64 = 98/128 = 196/256 = 0.765625`
(R=15/64); L2 f1.2 `52/64 = 104/128 = 208/256 = 0.8125` (R=12/64);
L2 f1.0 `43/64 = 86/128 = 172/256 = 0.671875` (R=21/64).
D5 provenance contrast: D5 `_rows_required(CE,n,f)` gives n256 L1 235 and L2
206; the accepted D6 successor sets (236/208) are the rate-aligned rows and
are the D8 authority. `R` is identical at all three widths, so the DE is
n-independent; n enters only through graph realizability and the future
finite-length construction.

2. Efficiency (D5 convention, `CE_L1=3.814742` bits/symbol, D4-audit frozen):
   `f = 5m/(n·H_L1)`; realized `f1.2 = 5·59/(64·3.814742) = 1.20831`,
   `f1.0 = 245/244.143488 = 1.00351`; inverse `R = 1 - f·H_L1/5`
   (`nonbinary_v26_mcde.target_rate_layer:218-233`).

3. Ensemble identities (edge perspective; `nonbinary_v9_common.py:198-254`):
   `dbar_v = 1/Σ_j λ_j/j`, `dbar_c = 1/Σ_i ρ_i/i`, `m/n = dbar_v/dbar_c`,
   `R = 1 - (Σ_i ρ_i/i)/(Σ_j λ_j/j)`.

4. Concentrated two-point ρ (`concentrated_check_distribution`):
   `target = (1-R)·Σ_j λ_j/j`, `dc = 1/target`,
   `d_lo = floor(dc)`, `d_hi = d_lo+1`,
   `w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`, `w_hi = 1-w_lo`;
   integer `dc` degenerates to a single degree. λ support {2,3}:
   `Σ_j λ_j/j = (2+λ2)/6`.

5. Worked hand checks (all exact fractions; numeric tests in E08):
   - regular **DV3** n64 L1 f1.2: `Σλ/j = 1/3`, `target = (59/64)/3 = 59/192`,
     `dc = 192/59 = 3.254237`, `w_lo = (59/192-1/4)/(1/3-1/4) = 11/16`,
     `w_hi = 5/16`; realized integer allocation `3·59+15 = 192` edges →
     44 checks degree 3, 15 checks degree 4; `Σρ/i = 59/192` ✓.
   - regular **DV3** n64 L1 f1.0: `target = (49/64)/3 = 49/192`,
     `dc = 192/49 = 3.918367`, `ρ = {3: 1/16, 4: 15/16}`;
     `Σρ/i = 1/48+15/64 = 49/192` ✓.
   - tiny hand-checkable ensemble A: `n=8, m=5, λ={2:1}` → `R=3/8`,
     `target=(5/8)/2 = 5/16`, `dc=16/5=3.2`, `ρ={3:3/4, 4:1/4}` (ρ weights
     `w_lo=(5/16-1/4)/(1/3-1/4)=3/4`); 16 sockets → 1 check degree 4,
     4 checks degree 3; `Σρ/i = 3/12+1/16 = 5/16` ✓.
   - tiny hand-checkable ensemble B: `n=9, m=6, λ={3:1}` → `R=1/3`,
     `target=(2/3)/3 = 2/9`, `dc=9/2=4.5`, `ρ={4:4/9, 5:5/9}` (E=27 sockets,
     6 checks → 3 checks degree 4, 3 checks degree 5);
     `Σρ/i = 1/9+1/9 = 2/9` ✓.

6. GF32 disclosure accounting: one check row = 5 symbol bits; `5m` disclosed
   bits for `n` symbols; `f = 5m/(n·H_L1)`.

## 4. Candidate enumeration and cap (E05)

- Variable-edge-perspective λ only; support `{2, 3}`; `λ2 ∈ {0.00, 0.05, …,
  1.00}` (21 values), `λ3 = 1 - λ2`; canonical ID
  `lam_d2_<λ2:.2f>_d3_<λ3:.2f>`; enumeration in ascending λ2; hard cap
  **21 candidates per condition**; no replacements, no extension, no
  outcome-adaptive refinement.
- `λ={3:1}` (ID `lam_d2_0.00_d3_1.00`) is the mandatory regular-DV3 baseline;
  `λ={2:1}` (`lam_d2_1.00_d3_0.00`) is the degree-2 endpoint comparator.
- Per candidate × condition (f1.0, f1.2): `R = 1 - m/n` (identical across
  n=64/128/256) and `ρ = make_rho(R, λ)`. A candidate/condition pair whose
  `make_rho` raises (e.g. implied `dc < 2`) is **refused with a recorded
  reason** and excluded from advancement; no silent drop or substitution.
- Graph/coefficient compatibility: each variable degree ∈ {2,3}; min check
  degree ≥ `I1_MIN_CHECK_DEGREE=2` (D6 invariant); simple Tanner graph; one
  nonzero GF32 coefficient per edge from the accepted common stream (seeds
  `202609120100+n` L1 / `202609120200+n` L2); coefficients are not optimized.
  Realized check degrees for the frozen grid must stay ≤ 8; E08 asserts the
  actual maximum ≤ 4 at both conditions. The V37-P0 forest diagnostic
  (`N2`, `gamma_2 = max(0, N2-(m-1))`) is recorded per candidate per registered
  (n,m) cell (3 widths × 2 conditions) as finite-length context; it is **not**
  a refusal gate (heuristic, not a necessary condition).

## 5. Future DE sweep, advancement rule, terminals

- Conditions: L1 only, two rate points — **f1.2 (primary, R=5/64)** and
  **f1.0 (secondary, R=15/64)**; square (R=0) excluded (no disclosure
  budget). L2 is a read-only comparator, never swept or co-optimized.
- DE parameters (V37R1 frozen values): `q=32`,
  `run_mcde_posterior(n_samples=4000, max_iter=60, entropy_tol_bits=1e-4,
  streak=20, record_entropy=True, record_channel_entropy=True)`;
  seeds `2026091601, 2026091602, 2026091603` (verified fresh).
- Observable: per-run 1-based check-population entropy trace → V37 trajectory
  metrics (reuse `v37_de_screening.compute_trajectory_metrics` read-only):
  `AUT_30` (H(0)=5.0), `H5/H10/H15/H60`, `T_0.10`, `T_0.01`, and
  `converged = H60 < 1e-4`. All seeds of both conditions must converge.
- Advancement: baseline = regular DV3. A candidate is **eligible** iff (a) all
  3 seeds converge in both conditions, and (b) its primary-condition
  worst-seed `AUT_30` ≤ baseline primary worst-seed `AUT_30` × 0.95 (frozen
  5% relative-improvement margin, V37 gate value). If eligible ≠ ∅, exactly
  one winner by the frozen deterministic key:
  `(primary worst-seed AUT_30 asc, primary mean AUT_30 asc, primary worst-seed
  T_0.01 asc, candidate ID lexicographic)`. No post-result tuning; the sweep
  runs all 126 DE calls (no adaptive stop).
- Terminals: `D8_DE_ADVANCE_ONE_ENSEMBLE` (one candidate → next finite-length
  task packet only); `D8_DE_NO_ADVANCE` (baseline converged, no candidate
  eligible; closes only this frozen support/grid; route to a broader
  degree/ensemble proposal or an explicit channel/decoder mismatch analysis;
  never an impossibility claim); `D8_DE_BASELINE_NOT_CONVERGED` (regular DV3
  fails the gate; mismatch analysis first); `D8_DE_EVIDENCE_INVALID`
  (refusal/NaN/consistency failure); `D8_DE_RESOURCE_BLOCKED`; `D8_DE_NOT_RUN`
  (no authorization — current state).
- Claim ceiling: DE-only, synthetic, CAL-only Model-F channel, frozen decoder
  contract; no finite-length/FER/leakage/qualification/promotion/real-data
  claim; advancement authorizes no execution and does not revive D7-H.

## 6. Future root, command, budgets, evidence (left absent/unauthorized)

Fresh root UUID **`5edf0630-f357-4a7e-b4c5-9ba955021405`**
(`workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`,
verified absent at freeze time; must not be created before authorization).

```text
.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405
```

- Budgets: ≤126 DE calls (21 candidates × 2 conditions × 3 seeds) + ≤20 setup
  calls; wall ≤1800 s; per-call ≤120 s; aggregate RSS <2 GiB strict; single
  process; no retry, no resume, no seed search, no adaptive selection.
- Root files (fresh, refusal on overwrite): `manifest.json`,
  `de_records.csv`, `de_traces.csv`, `candidate_summary.csv`, `summary.json`,
  `command_log.txt`; `--verify` recomputes every candidate group from
  `de_traces.csv` and requires stored == recomputed (zero skip).

## 7. Tests (E08, future)

Tiny exact/normalization: sampler rows equal `floor_renorm(P1[:,b].T,1e-15)`
XOR-centered on a synthetic tiny Model-F fixture; `Σ candidate rows` mass 1.
Rate/ρ: the five hand checks of §3.5 as asserts. Baseline reproduction:
regular-DV3 identity `dbar_c = 3n/m`, R, and the n64 f1.2 `ρ={3:11/16, 4:5/16}`.
Enumeration: exactly 21 IDs in ascending λ2; no duplicates;
refusal of λ with degree 1, negative weight, non-unit sum, or support outside
{2,3}. Cross-kernel exact check: `_check_update_coeff_jit` with all-unit
coefficients equals V14 `_check_update_jit` on a tiny population. Fresh-root/
no-overwrite refusal and fake-runner isolation (no production decoder import or
bind; zero decoder calls). All tests use fresh `workspace/` basetemps and
`-p no:cacheprovider`.
