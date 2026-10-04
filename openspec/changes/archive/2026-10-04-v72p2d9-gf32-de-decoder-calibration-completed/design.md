# Design — V72P2D9 GF32 DE-decoder calibration and threshold (R1)

Frozen contract created **before** any behavior edit (packet §4 items 1–8).
Requirement source: `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`.
Predecessor artifacts: `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/`
(`READINESS_R1.md`, `EXPLORATION_LOG.md` §"batch-end review" and §"main-thread
result acceptance", `INDEPENDENT_REVIEW_R1.md`), the D8 six-file root
`workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
(read-only).

This change is documentation + OpenSpec + readiness only. No decoder call, no
DE call, no root creation, no v35/V26/channel edit.

## 1. Frozen inputs

| input | value | source |
|---|---|---|
| DE engine | `nonbinary_v26_mcde.run_mcde_posterior` (unchanged, q=32, poly 37) | `nonbinary_v26_mcde.py:243-326` |
| V14 kernels | `_variable_or_belief_jit`, `_wht_row_jit`, `_FLOOR=1e-300` | `nonbinary_v14_mcde.py:84,96-107,120-152` |
| decoder | `decode_row_layered_fftqspa` bound with `MAX_ITER=90`, `DAMPING_ALPHA=1.0` | `v35_algorithm_development.py:781-936`; `v72p2d5_gf32_rate_mother.py:90-91,1091-1141,2610-2633` |
| prior chain | Model-F CAL-only artifact → `pb` → E2 `P_F` → `P1` → floor/renorm `1e-15` | `scripts/v72p2d6_graph_mother_development.py:787-799`; `v72p2d5_gf32_rate_mother.py:48,275-306,309-321,346-351,2480-2507` |
| conditional entropy | `CE_L1_MEAN = 3.814742` bits/symbol | `v72p2d5_gf32_rate_mother.py:49` |
| rate conditions | f1.2 primary `m/n=59/64`, f1.0 secondary `m/n=49/64` (n-proportional at 128/256) | `v72p2d8_rate_aligned_ensemble.py:123-136`; D8 design §3 |
| DE parameters | `n_samples=4000`, `max_iter=60`, `entropy_tol_bits=1e-4`, `streak=20` | `v72p2d8_rate_aligned_ensemble.py:85-90` |
| degree analysis | `v37_degree_feasibility` (accepted V37P0) | `v37_degree_feasibility.py:118-379` |
| metrics | `compute_trajectory_metrics` (`AUT_30`, `H60`, `T_0.01`, `converged=H60<1e-4`) | `v37_de_screening.py:295-346` |

D8 accepted facts are inputs to D9 design only; the D8 terminal
`D8_DE_BASELINE_NOT_CONVERGED` and winner=none are not reinterpreted
(`EXPLORATION_LOG.md:459-479`).

## 2. Stage-by-stage V26 ↔ v35 semantic map (packet §4.1–§4.4)

Legend: **MATCH** = same-input primitive identity (certified or code-exact),
**APPROX** = documented approximation with bounded inference impact,
**MISMATCH** = the two sides answer different questions (no equivalence claim).

**Coordinate convention (frozen, packet §4.1).** All messages are length-32
arrays indexed by the GF(32) symbol value, `m[s] = P(value = s)`: probability
domain + row normalization in V26, log-domain (`log(max(·, 1e-15))`) in v35.
Channel indexing: the DE channel row is centered so the true symbol maps to
index 0 (`c[e] = P1[u XOR e]`); the decoder keeps raw indexing and uses the
linear-code symmetry (`E = X - x_true` ⇒ `H E = 0`). Variable-to-check messages
are distributions over the *sending variable's* value. Check-to-variable
messages in v35 are distributions over the *receiving variable's* value after
the coset shift (`syn ⊕ coeff_t·v`); V26 emits them indexed by the XOR-sum
`y = Σ h_e x_e` of the extrinsic edges (outgoing coefficient absorbed). All
offsets are GF(2^5) addition = XOR under the frozen polynomial 37; no integer
addition is used anywhere.

### (a) Channel centering, prior and floor chain

| side | operation | pointer |
|---|---|---|
| decoder prior | `pr1 = _floor_renorm(P1[:, bob].T, 1e-15)` then the decoder floors/normalizes again and takes logs | `scripts/v72p2d6_graph_mother_development.py:817`; `v72p2d5_gf32_rate_mother.py:1415`; floor `:346-351`, `DECODER_FLOOR` `:48`; `v35_algorithm_development.py:810-812` |
| DE channel | draw `(b,a) ~ pb·P_F`, `u = a//32`, `c[e] = floor_renorm(P1[:,b].T)[u XOR e]` | `v72p2d8_rate_aligned_ensemble.py:281-290`; V26 centered-channel contract `nonbinary_v26_mcde.py:252-254`; V26 channel convention `nonbinary_v26_channel.py:275-280` |
| framing | DE population is an i.i.d. draw refreshed **each iteration** | `nonbinary_v26_mcde.py:293` |

Verdict: **MATCH** on the row law. The DE row is the decoder prior row reindexed
by the XOR of the true L1 symbol; floor/renorm is elementwise and commutes with
that permutation, and the double floor (`D6` then `v35`) is idempotent within
`1e-15`. Residual **APPROX**: standard DE i.i.d.-population exchangeability and
per-iteration fresh channel draws versus one fixed frame prior in the decoder
(already recorded in D8 readiness §8). Impact: no per-frame prior difference;
only the population/frame distinction.

### (b) Coefficient permutation direction and syndrome/coset centering

| side | operation | pointer |
|---|---|---|
| V26 | `perm[h,y]=inv(h)·y`; `tmp[y]=v2c[src,perm[h,y]]` ⇒ `tmp[y]=P(h·X=y)` | `nonbinary_v26_mcde.py:93-114` (`:109-113`), `_check_update_coeff_jit:48-90` (`:73-75`); driver draws incoming coeffs `:187-189` |
| v35 | `scaled_log[mul_table[coeff,:]]=msg` ⇒ `scaled_log[t]=msg[inv(coeff)·t]`; outgoing coset shift `out_prob=conv[syn ⊕ coeff_t·s]` | `v35_algorithm_development.py:472-475`, `:503-504` |
| certification | direct-SP enumeration vs production FFT (all tuples ≤3.3e-16); negative controls discriminate the wrong direction | `D7_A_CERTIFICATION_REPORT_R1.md:16-23` |

Verdict: **MATCH** on the incoming permutation direction and on the check law
(`Σ h_e X_e = s_r` is represented in the DE's zero-syndrome centered domain
`Σ h_e E_e = 0`, an exact linear-code symmetry: `E = X - x_true` ⇒
`H E = H X - s = 0`). **APPROX** on the outgoing coefficient: v35 applies the
target edge's coefficient (`:503-504`); V26 absorbs it as identity because the
DE re-draws random coefficients per edge per iteration and treats a random edge
as marginal-equivalent (`nonbinary_v26_mcde.py:59-61`). Impact: the outgoing
symbol permutation does not change a single message's entropy, but it does
change variable-node products of independently permuted factors for
non-permutation-symmetric posteriors; therefore no per-iteration DE↔decoder
message-path equivalence is claimed. This is inherited from the accepted
V26/V27/V37 convention and is not a defect; the D9 C07 same-input certification
must cover non-unit coefficients and label loopy comparisons as non-equivalence
diagnostics (packet §5).

### (c) Variable-node update

| side | operation | pointer |
|---|---|---|
| V26 | degree draw from λ; product of channel row and `dv-1` incoming c2v rows; floor `1e-300`, row-normalize | `nonbinary_v26_mcde.py:142-153`; kernel `nonbinary_v14_mcde.py:120-152` |
| v35 row-layered | `v2c = beliefs - u_old`; after check update `beliefs += u_new - u_old` | `v35_algorithm_development.py:856-885` (extrinsic `:861`, belief `:883-885`) |
| v35 flooding (reference only) | `beliefs = log_prior + Σ u`; `v2c = beliefs - u` | `v35_algorithm_development.py:742-766` |
| unused variant | `belief_update_mcde` is exported but **not** called by the run loop | `nonbinary_v26_mcde.py:156-167` vs `:292-311` |

Verdict: **MATCH** algebraically against flooding BP (probability product ↔
log-sum); **APPROX** for the production row-layered schedule (Gauss–Seidel
message bookkeeping with `u_old`) and for loopy correlations. The decoder has
no per-update probability floor; the DE floor `1e-300` is a numerical guard.
Impact: no per-iteration equivalence; DE iteration count is not a decoder
iteration count.

### (d) Check-node update

| side | operation | pointer |
|---|---|---|
| V26 | extrinsic product over `dc-1` draws, coefficient-permuted WHT, inverse WHT `/q`, floor `1e-300`, row-normalize; random nonzero coeffs | `nonbinary_v26_mcde.py:48-90,170-190`; `_wht_row_jit` `nonbinary_v14_mcde.py:96-107` |
| v35 | FWHT per input (coeff permuted), prefix/suffix extrinsic products, inverse FWHT `/q`, coset shift, floor `1e-15`, log | `v35_algorithm_development.py:453-513`; `fwht_batched:99-121` |
| certification | D7-A direct-SP (deg 2/3, all coefficient/syndrome tuples ≤3.3e-16); D8 cross-kernel with unit coefficients equals V14 | `D7_A_CERTIFICATION_REPORT_R1.md:16-23`; `comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py:289-302` |

Verdict: **MATCH** for the same-input primitive kernel (the already-certified
equality is the starting point, not the whole map). **APPROX** only for the
outgoing coefficient and the `1e-300`/`1e-15` floor difference (D8 readiness
§8). Impact: same-input probability equality is certifiable; ensemble-level
path equivalence is a separate C07 item.

### (e) Posterior/belief metric versus decoder output

| side | observable | pointer |
|---|---|---|
| DE | mean **bits/symbol entropy of the check-to-variable population** after each check update; no belief update in the loop | `nonbinary_v26_mcde.py:300,117-120`; `entropy_base_q` `nonbinary_v9_mcde.py:386-406` |
| decoder | hard decision `argmax(beliefs)` and stop on exact syndrome equality; `final_beliefs` are unnormalized log-domain beliefs | `v35_algorithm_development.py:888-890,923-936`; D7-A finding 7 (`D7_A_CERTIFICATION_REPORT_R1.md:35-43`) |
| D8 metric | `H60 < 1e-4` on the 1-based entropy trace (`H(0)=5.0`), `AUT_30`, `T_0.01` | `v72p2d8_rate_aligned_ensemble.py:307-314`; `v37_de_screening.py:295-346` |

Verdict: **MISMATCH** of semantics. DE convergence means the ensemble check
messages became near-deterministic; the decoder stops only on an exact
syndrome/codeword match. Small check entropy makes a codeword likely but does
not certify it (loopy correlations), and the decoder has no entropy stop.
Impact: DE convergence is a screening signal only; it cannot be converted into
a finite-length success claim, and D8's primary 3/3 is not a finite-length
result.

### (f) Flooding DE iteration versus row-layered finite sweep

| side | schedule | pointer |
|---|---|---|
| DE | one flooding round per iteration (variable product → check update), population refreshed | `nonbinary_v26_mcde.py:292-311` |
| decoder | one sequential row sweep per iteration with immediate belief updates; production binding is the row-layered path | `v35_algorithm_development.py:856-885`; `v72p2d5_gf32_rate_mother.py:1126-1134`; `scripts/v72p2d6_graph_mother_development.py:111` |
| flooding decoder | exists as the nearest schedule but is not the production path | `v35_algorithm_development.py:672-778` |
| tree/loopy evidence | tree posteriors exact ≤6.7e-16; loopy per-sweep matches only under a matched reference recurrence (divergence is floating-point growth) | `D7_A_CERTIFICATION_REPORT_R1.md:24-31` |

Verdict: **APPROX / equivalence limit**. In the cycle-free (tree) case both
schedules compute the same exact BP marginals; on loopy graphs only a matched
same-schedule recurrence is certified, never BP-vs-map and never
flooding-vs-row-layered trajectories. Impact: DE is an ensemble screen; no
per-iteration, per-frame or finite-length equivalence may be inferred, and the
row-layered production semantics govern any future decoder packet.

### (g) Stopping metric

| side | stop rule | pointer |
|---|---|---|
| DE | `entropy < 1e-4` for `streak=20` consecutive iterations (break) | `nonbinary_v26_mcde.py:303-310` |
| D8 | `converged = H60 < 1e-4` (post-hoc trajectory metric) | `v72p2d8_rate_aligned_ensemble.py:307-314`; `v37_de_screening.py:337` |
| decoder | exact syndrome equality after each row sweep; `iterations=k` ⇔ post-`k`-sweep beliefs | `v35_algorithm_development.py:890`; `D7_A_PREREG_R1.md:42-48` |

Verdict: **MISMATCH**. The two terminals are different predicates; the only
bridge is the uncertified heuristic "check-message entropy → 0 ⇒ messages
nearly deterministic ⇒ hard decision likely a codeword". Impact: a DE terminal
never substitutes for a decoder exact/syndrome result, and `undetected`-type
distinctions remain decoder-only.

## 3. Equivalence ceiling (what D9 may and may not claim)

- Established by accepted evidence: same-input check-update primitive
  (production FFT vs direct SP; V26 kernel vs V14 with unit coefficients),
  coefficient direction/permutation convention, syndrome/coset representation,
  tree posteriors, prior chain equality up to XOR reindexing.
- Not established and not claimed: flooding-DE ↔ row-layered trajectory or
  iteration equivalence; DE terminal ↔ decoder terminal; negative-log-likelihood
  or error-probability equivalence; finite-length/FER behavior; any claim about
  the empirical Model-F channel beyond the accepted artifact.
- STOP check (packet §9): the map is fully expressible without modifying v35,
  V26 or the channel model; the outgoing-coefficient absorption is an inherited
  V26 ensemble convention, not a defect requiring a patch. STOP is therefore
  **not** triggered; no decoder tuning is performed.

## 4. Prospective f1.0 role (packet §4.7; C03)

Frozen constants only; the D8 outcome is not an input.

- `H_L1 = 3.814742` bits/symbol (`v72p2d5_gf32_rate_mother.py:49`).
- disclosure per symbol `d = 5m/n` (5 bits per disclosed GF32 symbol).
- margin `mu = 5m/n - H_L1`; Shannon-consistent code rate
  `R_ent = 1 - H_L1/5 = 1 - 0.7629484 = 0.2370516`.
- f1.2: `m=59, n=64`: `d = 295/64 = 4.609375`, `mu = +0.794633` bits/symbol
  (20.83 % of `H_L1`), `R = 5/64 = 0.078125`, `R_ent - R = 0.1589266`,
  `f = 5m/(n·H_L1) = 1.20831`.
- f1.0: `m=49, n=64`: `d = 245/64 = 3.828125`, `mu = +0.013383` bits/symbol
  (0.35 % of `H_L1`), `R = 15/64 = 0.234375`, `R_ent - R = 0.0026766`,
  `f = 1.00351`.

**Frozen criterion (before any D9 calibration result).** A rate condition may
serve as `HARD_GATE` only if `mu >= Δ_min = 0.05` bits/symbol **and**
`R_ent - R >= 0.01`. Otherwise its prospective role is
`BOUNDARY_DIAGNOSTIC` (reported, never blocking). `Δ_min = 0.05` bits/symbol is
a frozen design allowance: it is ≈1.31 % of `H_L1`, ≈3.7× the f1.0 margin, and
the frozen contract carries no accepted uncertainty interval for the empirical
`H_L1` estimate, so a hard gate must not be decidable by sub-percent model
error. Classification by this criterion:

| condition | `mu` (bits/symbol) | `R_ent - R` | role |
|---|---|---|---|
| f1.2 | +0.794633 >= 0.05 | 0.1589266 >= 0.01 | primary gate (unchanged) |
| f1.0 | +0.013383 < 0.05 | 0.0026766 < 0.01 | **`BOUNDARY_DIAGNOSTIC`** |

Rationale independent of D8: at f1.0 the operating rate is only 0.0027 above
the entropy-limit rate; both C1 (genuine threshold boundary) and C2 (DE/decoder
mismatch) predict non-convergence there, so an f1.0 hard gate has near-zero
discriminating power between the D9 hypotheses while it would veto an
f1.2-valid ensemble. f1.0 is therefore a registered boundary diagnostic:
per-candidate `S4000(f1.0)` counts are reported, a candidate with
`S4000(f1.0) >= 7/8` is a *boundary crossing* routed to main-thread review, and
f1.0 never enters eligibility, ranking or terminals. Promotion to a real gate
would require a new preregistration with a new information-margin argument.

## 5. Finite-graph degree/socket realization (packet §4.5; C04)

Rules (all reused from the accepted V37P0 module, read-only):
`edge_to_node_distribution` (`v37_degree_feasibility.py:118-139`) →
`largest_remainder_counts` (`:142-165`, descending fractional part, tie by
ascending degree) → `calculate_node_degree_counts` (`:168-187`) gives integer
`n2 + n3 = n`; sockets `E = calculate_total_sockets = 2n2 + 3n3 = 3n - n2`
(`:190-192`); check counts `calculate_check_degree_allocation` (`:205-261`):
`dc_floor = floor(E/m)`, `dc_ceil = dc_floor+1`, `c_ceil = E mod m`,
`c_floor = m - c_ceil`, socket balance `dc_floor·c_floor + dc_ceil·c_ceil = E`
and `c_floor + c_ceil = m`; degree-2 context `analyze_degree2_subgraph`
(`:264-297`): forest bound `m-1`, forced-cycle rank `max(0, N2-(m-1))`;
feasibility flags: min check degree >= 2 and realized max check degree <= 8
(actually <= 4). Exact nominal-λ realizability: `λ2 = k/20` requires
`n2 = 3kn/(k+40)` and `E = 3n - n2` to be integers; the apportionment rule is
used otherwise, and the realized rate is **exactly** `R = 1 - m/n` for every
integer realization because `Σ_j λ̂_j/j = n/E` and `Σ_i ρ̂_i/i = m/E`.

Exact nominal-socket non-integrality (flagged): 0.45 → `E = 7680/49`,
`15360/49`, `30720/49`; 0.50 → `768/5, 1536/5, 3072/5`;
0.55 → `2560/17, 5120/17, 10240/17`. All are non-integers, so the realized
`λ̂` differs from nominal; no cell is socket-infeasible under the
apportionment rule.

### f1.2 (primary; m = 59 / 118 / 236)

| candidate | n | n2 | n3 | E | realized λ̂2 | check alloc (`d^count`) | realized ρ̂ (edge) | DE ρ (continuous) | N2-(m-1) |
|---|---|---|---|---|---|---|---|---|---|
| 0.00 (DV3) | 64 | 0 | 64 | 192 | 0 | 3^44 + 4^15 | {3: 0.68750, 4: 0.31250} | {3: 0.68750, 4: 0.31250} | -58 |
| 0.00 (DV3) | 128 | 0 | 128 | 384 | 0 | 3^88 + 4^30 | {3: 0.68750, 4: 0.31250} | {3: 0.68750, 4: 0.31250} | -117 |
| 0.00 (DV3) | 256 | 0 | 256 | 768 | 0 | 3^176 + 4^60 | {3: 0.68750, 4: 0.31250} | {3: 0.68750, 4: 0.31250} | -235 |
| 0.45 | 64 | 35 | 29 | 157 | 70/157 = 0.44586 | 2^20 + 3^39 | {2: 40/157=0.25478, 3: 117/157=0.74522} | {2: 0.25859, 3: 0.74141} | -23 |
| 0.45 | 128 | 71 | 57 | 313 | 142/313 = 0.45367 | 2^41 + 3^77 | {2: 0.26198, 3: 0.73802} | {2: 0.25859, 3: 0.74141} | -46 |
| 0.45 | 256 | 141 | 115 | 627 | 94/209 = 0.44976 | 2^81 + 3^155 | {2: 0.25837, 3: 0.74163} | {2: 0.25859, 3: 0.74141} | -94 |
| 0.50 | 64 | 38 | 26 | 154 | 38/77 = 0.49351 | 2^23 + 3^36 | {2: 46/154=0.29870, 3: 108/154=0.70130} | {2: 0.30469, 3: 0.69531} | -20 |
| 0.50 | 128 | 77 | 51 | 307 | 154/307 = 0.50163 | 2^47 + 3^71 | {2: 0.30619, 3: 0.69381} | {2: 0.30469, 3: 0.69531} | -40 |
| 0.50 | 256 | 154 | 102 | 614 | 154/307 = 0.50163 | 2^94 + 3^142 | {2: 0.30619, 3: 0.69381} | {2: 0.30469, 3: 0.69531} | -81 |
| 0.55 | 64 | 41 | 23 | 151 | 82/151 = 0.54305 | 2^26 + 3^33 | {2: 52/151=0.34437, 3: 99/151=0.65563} | {2: 0.35078, 3: 0.64922} | -17 |
| 0.55 | 128 | 83 | 45 | 301 | 166/301 = 0.55150 | 2^53 + 3^65 | {2: 0.35216, 3: 0.64784} | {2: 0.35078, 3: 0.64922} | -34 |
| 0.55 | 256 | 166 | 90 | 602 | 166/301 = 0.55150 | 2^106 + 3^130 | {2: 0.35216, 3: 0.64784} | {2: 0.35078, 3: 0.64922} | -69 |

### f1.0 (boundary diagnostic; m = 49 / 98 / 196)

| candidate | n | n2 | n3 | E | realized λ̂2 | check alloc | realized ρ̂ (edge) | DE ρ (continuous) | N2-(m-1) |
|---|---|---|---|---|---|---|---|---|---|
| 0.00 (DV3) | 64 | 0 | 64 | 192 | 0 | 3^4 + 4^45 | {3: 0.06250, 4: 0.93750} | {3: 0.06250, 4: 0.93750} | -48 |
| 0.00 (DV3) | 128 | 0 | 128 | 384 | 0 | 3^8 + 4^90 | {3: 0.06250, 4: 0.93750} | {3: 0.06250, 4: 0.93750} | -97 |
| 0.00 (DV3) | 256 | 0 | 256 | 768 | 0 | 3^16 + 4^180 | {3: 0.06250, 4: 0.93750} | {3: 0.06250, 4: 0.93750} | -195 |
| 0.45 | 64 | 35 | 29 | 157 | 70/157 = 0.44586 | 3^39 + 4^10 | {3: 117/157=0.74522, 4: 40/157=0.25478} | {3: 0.75156, 4: 0.24844} | -13 |
| 0.45 | 128 | 71 | 57 | 313 | 142/313 = 0.45367 | 3^79 + 4^19 | {3: 0.75719, 4: 0.24281} | {3: 0.75156, 4: 0.24844} | -26 |
| 0.45 | 256 | 141 | 115 | 627 | 94/209 = 0.44976 | 3^157 + 4^39 | {3: 0.75120, 4: 0.24880} | {3: 0.75156, 4: 0.24844} | -54 |
| 0.50 | 64 | 38 | 26 | 154 | 38/77 = 0.49351 | 3^42 + 4^7 | {3: 126/154=0.81818, 4: 28/154=0.18182} | {3: 0.82812, 4: 0.17188} | -10 |
| 0.50 | 128 | 77 | 51 | 307 | 154/307 = 0.50163 | 3^85 + 4^13 | {3: 0.83062, 4: 0.16938} | {3: 0.82812, 4: 0.17188} | -20 |
| 0.50 | 256 | 154 | 102 | 614 | 154/307 = 0.50163 | 3^170 + 4^26 | {3: 0.83062, 4: 0.16938} | {3: 0.82812, 4: 0.17188} | -41 |
| 0.55 | 64 | 41 | 23 | 151 | 82/151 = 0.54305 | 3^45 + 4^4 | {3: 135/151=0.89404, 4: 16/151=0.10596} | {3: 0.90469, 4: 0.09531} | -7 |
| 0.55 | 128 | 83 | 45 | 301 | 166/301 = 0.55150 | 3^91 + 4^7 | {3: 0.90698, 4: 0.09302} | {3: 0.90469, 4: 0.09531} | -14 |
| 0.55 | 256 | 166 | 90 | 602 | 166/301 = 0.55150 | 3^182 + 4^14 | {3: 0.90698, 4: 0.09302} | {3: 0.90469, 4: 0.09531} | -29 |

Checks: every cell has integer `n2/n3/E`, exact socket balance, min check
degree 2 (f1.2 mixed) or 3 (f1.0 mixed) or 3 (DV3), realized max check degree 4
(≤8 bound satisfied), `N2 <= m-1` in all cells (no forced degree-2 cycle
component), and `λ̂` drift `|λ̂2 - λ2| <= 6.96e-3` (≤1.6 % relative). Realized
rate is exactly `R = 1 - m/n` by the harmonic identity. Mixed-degree graphs
require a new finite-length support construction in a future packet; the D6
all-degree-3 nested builder is not reused here and no graph is built in D9.

## 6. Future calibration matrix, budgets, root and command (packet §4.6; C05)

Track: `EXPLORE_HEAVY`; one frozen authorization, one append-only log, one
batch-end independent review. The matrix tests MC stability only and cannot
become an adaptive degree search.

Candidates and control roles (4):

| candidate | role |
|---|---|
| `lam_d2_0.00_d3_1.00` (DV3) | frozen advancement reference; baseline reproduction |
| `lam_d2_0.45_d3_0.55` | mandatory D8 primary 3/3 replicate |
| `lam_d2_0.50_d3_0.50` | mandatory D8 primary 3/3 replicate |
| `lam_d2_0.55_d3_0.45` | upper-flank control (D8 primary 2/3 adjacent to the 3/3 plateau): tests whether the plateau edge is stable or a windowing artifact |

Conditions/seeds/populations: f1.2 primary at populations {4000, 16000};
f1.0 boundary diagnostic at population {4000} only (non-gating, C03). Seeds
(8) = D8 reproduction `2026091601, 2026091602, 2026091603` + fresh
`2026091801..2026091805` (verified absent in the repository at freeze time).
Calls: f1.2 `4 x 8 x 2 = 64`; f1.0 `4 x 8 = 32`; total **96 DE calls**
(+ <=12 setup). V26 parameters unchanged: q=32, `max_iter=60`,
`entropy_tol_bits=1e-4`, `streak=20`, `record_entropy=True`,
`record_channel_entropy=True`; per-call fresh channel draws.

Stability definition (frozen): for candidate `c`, `S4000(c)` and `S16000(c)`
are the counts of the 8 seeds with `H60 < 1e-4`.
`stable_converged(c)` ⇔ `S4000=8` and `S16000=8`;
`stable_unconverged(c)` ⇔ `S4000<=6` and `S16000<=6`;
otherwise `stability_ambiguous(c)`.

Decision rules (frozen; interactions with packet §8):

1. primitive semantics certification (C07/C11) must PASS, else terminal
   `D9_SEMANTICS_BLOCKED` (no eligibility computed, no DE-to-finite inference);
2. degree realization audit must be valid, else `D9_GRAPH_REALIZATION_INVALID`;
3. if DV3 is `stable_converged`, terminal `D9_DE_BASELINE_CONVERGED_REVIEW`
   (reference changed; main-thread decision, no auto-advance);
4. else eligible candidates are those with `stable_converged` and
   worst-seed `AUT_30` at 16000 samples <= 0.95 × DV3 worst-seed `AUT_30` at
   16000 samples; if non-empty, select exactly one by
   `(worst-seed AUT_30 p16000 asc, mean AUT_30 p16000 asc, worst T_0.01
   p16000 asc, candidate ID lexicographic)` → `D9_DE_CALIBRATION_SELECT_ONE`;
5. else terminal `D9_DE_STABILITY_NOT_CONFIRMED` (no finite candidate; C3
   supported; revise only population/uncertainty design under a new
   preregistration);
6. f1.0 diagnostic: report `S4000(f1.0)` per candidate; a non-baseline
   candidate with `S4000(f1.0) >= 7` is a boundary crossing routed to
   main-thread review; f1.0 never gates;
7. all registered calls run; no early stop, seed extension, candidate addition
   or adaptive rule; any additional terminal (`D9_DE_EVIDENCE_INVALID`,
   `D9_DE_RESOURCE_BLOCKED`, `D9_DE_NOT_RUN`) follows the D8 fail-closed
   pattern.

Budgets: <=96 DE calls + <=12 setup; wall <=1200 s; per-call <=300 s; RSS
<2 GiB strict; single process; no retry/resume. Fresh root (verified absent)
`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/`
with the D8 six-file evidence convention (`manifest.json`, `de_records.csv`,
`de_traces.csv`, `candidate_summary.csv`, `summary.json`, `command_log.txt`)
and fresh-root refusal. Exact future command (do not run):

```text
.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py --calibrate \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b
```

Verification: `.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py
--verify --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`.
All authorization flags remain false; the root is absent and the command
unauthorized until a separate explicit user/main-thread authorization names
this batch, branch, root, candidate set, seeds and budgets.

## 7. Routing hooks (packet §8)

- semantics certification fails → block DE-to-finite inference, diagnose the
  exact interface; no candidate promotion (`D9_SEMANTICS_BLOCKED`);
- semantics pass but MC stability fails → no finite candidate; revise only
  population/uncertainty design under a new preregistration
  (`D9_DE_STABILITY_NOT_CONFIRMED`);
- semantics and stability pass and graph realization valid → select at most one
  prospectively ranked ensemble for a later finite-length synthetic packet
  (`D9_DE_CALIBRATION_SELECT_ONE`; the selection authorizes only the next
  packet, no execution);
- degree realization invalid → redesign the ensemble representation before any
  decoder call (`D9_GRAPH_REALIZATION_INVALID`);
- no outcome revives D7-H; no outcome reinterprets D8's terminal or winner.

## 8. Future implementation delta (C07–C12; not in this change)

One thin module `comparison_bench/src/comparison_bench/formal_ir/v72p2d9_de_decoder_calibration.py`
(same-input primitive certification helper, graph-realization audit via the
accepted V37P0 helpers, stability aggregation on the frozen matrix, reuse of
the D8 V26 wrapper and V37 metrics), one runner
`scripts/v72p2d9_de_decoder_calibration_development.py` (`--calibrate`,
`--verify`), one focused test file. No V26/v35/D7-A/D8 edit; no production
decoder invocation; no generic framework, optimizer, graph library, checkpoint,
cache or new dependency. Tests must include no-production-decoder-entry
isolation and failure retention.
