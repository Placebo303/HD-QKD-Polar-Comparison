# D7-B early-exit soft-belief audit R1 (zero decoder calls)

Packet: `D7_B_RESULT_ACCEPT_EARLY_EXIT_AUDIT_R1_TASK_PACKET.md` §§4–6.
Method: R2-root scalars + frozen source + frozen docs + hand-written
independent math (`/tmp/d7b_audit_math.py`: numpy+stdlib only, no repo
imports, no decoder binding). No production code touched, R2 root untouched
(two identical listings), no VOID reads. Main-thread §0 adjudication
(R2 lifecycle authentic; terminal `D7_B_RESOURCE_OVERRUN`; RSS null is
telemetry unknown) is taken as frozen input.

## E01 — 49×iteration-0 / 15×iteration-1 reproduced from root scalars

Invoked rows: 64. `iterations` counter: `{'0': 49, '1': 15}`.

| tier | P99 | P90 | P60 | PAIR |
|---|---|---|---|---|
| SINGLE_CHECK_D3 | 4×it0 | 4×it0 | 4×it0 | 1×it0 + 3×it1 |
| TREE_6 | 4×it0 | 4×it0 | 4×it0 | 4×it1 |
| CYCLE_8 | 4×it0 | 4×it0 | 4×it0 | 4×it1 |
| FULL_RANK_64 | 4×it0 | 4×it0 | 4×it0 | 4×it1 |

Mechanism (source + fixture math, no decoder): truth-centered priors peak
uniquely at the true word (`build_prior`, easy-regime L274–282), so the
initial `argmax` (`v35_algorithm_development.py` L681) always equals `x_true`
and its syndrome matches by construction → iteration-0 return is forced for
all 48 cells, seed-independently. PAIR priors tie exactly 0.49/0.49 at
`x, x^1` (L283–287), so `np.argmax` deterministically returns
`min(x, x^1)`; the initial hard word equals truth iff every symbol is even.
Fixture reconstruction (`default_rng(seed).integers(0,32)`) predicts exactly
one all-even PAIR cell — SINGLE_CHECK_D3 seed 2026091202 (`x=[30,20,8]`) —
and the stored CSV shows exactly that cell as the single PAIR iteration-0
row. PAIR prediction matches all 16/16 stored rows.

## E02 — what happens before the initial syndrome check (v35 source)

`decode_row_layered_fftqspa`
(`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
L636–747): L659–665 initialize `beliefs` to `log(priors_clean)` (floored at
1e-15, renormalized; or a verbatim `warm_beliefs` copy — D7-B passes `None`,
easy-regime L520–524); L681 takes `best_x = argmax(beliefs)`; L683–692 check
the syndrome of that word and, on match, return `iterations=0`,
`status="converged_exact"`, `final_beliefs=beliefs` — the untouched
log-prior. Zero check messages (`check_to_var`, L676–678, still all zeros)
enter the returned object. Contrast: `decode_flooding_fftqspa` (L529–633)
has no iteration-0 path — its loop starts at `it=1` (L591) and its first
return (L607–616) follows a full check-update round. The iteration-0 early
exit exists only in the row-layered schedule that D7-B binds
(`bind_historical_decoder`, easy-regime L490–506, damping 1.0, cold).

## E03 — `softmax(final_beliefs)` equals the input prior at iteration 0

At iteration 0, `final_beliefs = log(priors_clean)` (E02). All D7-B prior
entries (min 3.2e-4 P99, 3.2e-3 P90, 1.29e-2 P60, 6.7e-4 PAIR) exceed the
1e-15 floor by ≥8 orders of magnitude, so flooring is the identity and
`priors_clean` differs from the input prior only by floating-point
renormalization (~1e-16). Independent hand-written softmax recomputation on
reconstructed representative priors (seed 2026091200):

| cell | max\|softmax(beliefs₀) − prior\| |
|---|---|
| SINGLE P99 / P90 / P60 | 2.2e-16 / 3.3e-16 / 1.1e-16 |
| TREE P99 / P90 / P60 | 2.2e-16 / 3.3e-16 / 1.1e-16 |

Scalar fingerprints in the stored CSV confirm the same fact without vectors:
every iteration-0 row has `mean_true_p == max_p ==` prior peak
(0.99/0.90/0.60) and entropy exactly the prior entropy (e.g. P99
0.130335099, P90 0.964415225, P60 2.952629119). The decoder returned the
input prior, relabelled.

## E04 — syndrome-conditioned exact posterior and the 0.500/0.400 scale

Hand-written independent exact posteriors (own GF(2⁵) code from the declared
polynomial `0b100101`; SINGLE by 32³ enumeration; TREE by 1024-separator
enumeration with analytic leaf sums — no production FFT, no oracle import)
reproduce every stored tractable `post_err` to ≤2.3e-16:

| cell | mine | stored | \|diff\| | argmax(var,sym) | exact true-mass | prior true-mass |
|---|---|---|---|---|---|---|
| SINGLE P99 | 0.009993385285694 | 0.009993385285694 | 2.2e-16 | (v0, x_true) | 0.999993 | 0.99 |
| SINGLE P90 | 0.099161719672215 | 0.099161719672215 | 1.1e-16 | (v0, x_true) | 0.999162 | 0.90 |
| SINGLE P60 | 0.363960004395122 | 0.363960004395122 | 0 | (v0, x_true) | 0.963960 | 0.60 |
| SINGLE PAIR | 0.500332669999434 | 0.500332669999434 | 1.1e-16 | (v0, x_true) | 0.990333 | 0.49 |
| TREE P99 | 0.009999998926856 | 0.009999998926856 | 2.2e-16 | (v4, x_true) | 1.000000 | 0.99 |
| TREE P90 | 0.099998560658138 | 0.099998560658138 | 2.2e-16 | (v4, x_true) | 0.999999 | 0.90 |
| TREE P60 | 0.399663616473850 | 0.399663616473850 | 0 | (v4, x_true) | 0.999664 | 0.60 |

Scale explanation: the stored syndrome is satisfied by construction, so the
exact posterior concentrates almost fully on the true word (0.96–1.00),
while the returned iteration-0 beliefs still sit at the prior peak
(0.49–0.99). The error is attained at (variable, true symbol) in all 7
cells and equals the concentration deficit `exact − prior`: 0.990333−0.49 =
0.50033 (SINGLE PAIR), 0.999664−0.60 = 0.39966 (TREE P60). No anomaly, no
hidden mass — the 0.5/0.4 magnitudes are exactly what an unconditioned prior
must show against a satisfied-syndrome posterior.

## E05 — posterior error stratified by tier / prior family / iteration

Tractable tiers (stored `post_err`, `map_agree True` everywhere):

| tier | P99 it0 | P90 it0 | P60 it0 | PAIR it0 | PAIR it1 |
|---|---|---|---|---|---|
| SINGLE_CHECK_D3 | 0.00999 | 0.09916 | 0.36396 | 0.50033 (1 cell) | ~1e-16 (3 cells) |
| TREE_6 | 0.01000 | 0.10000 | 0.39966 | — | 0.00689 (4 cells) |

Intractable tiers (CYCLE_8, FULL_RANK_64): `post_err`/`map_agree` empty by
design on all 32 rows — the metric is vacuous there. Within (tier, prior)
the four seeds agree to ≥13 significant digits. One check sweep makes
SINGLE exact (~1e-16, BP exact on one check); one sweep leaves TREE at
0.00689 (all checks touched once, ordering-stale).

## E06 — four distinct concepts, not one

1. Hard-decision correctness (`x_hat == x_true`): 64/64 — holds.
2. Syndrome satisfaction (`H x_hat == s`, independently recomputed):
   64/64 — holds.
3. MAP agreement (`x_hat == argmax exact`): 32/32 tractable — holds.
4. Calibrated posterior equality (`max|softmax(beliefs) − exact| ≤ 1e-10`):
   fails on all 25 tractable iteration-0 rows (plus 4 TREE PAIR iteration-1 rows at 0.00689; total failures 29 unchanged — review §4 transcription correction), passes on the 3 SINGLE PAIR
   iteration-1 rows. Concepts 1–3 concern the WORD; concept 4 concerns the
   BELIEFS. D7-B's gate tested concept 4 while the run's hard-decision
   evidence (concepts 1–3) passed — the failure is a belief-calibration
   signal, not a word-correctness signal.

## E07 — every production consumer of `final_beliefs`

Assignment/return-path analysis (never the field name): v35 returns current
log-belief state (E02). Consumers:

| consumer (file:line, function/context) | computation on the value | treats it as |
|---|---|---|
| D5 `v72p2d5_gf32_rate_mother.py:1053` (`_decode_block`) → `1348–1352` (`_run_layered_block`): `q = _softmax_rows(bel)` (`948–952`), `prior_l2 = app_fed_l2_prior(p2, bob, q)` | softmax then `q@P` | syndrome-conditioned APP `P(U1\|B,s1)` |
| v45 `v45_l1_app_soft_transfer.py:1046`, v46 `:1166`, v47 `:1091`, v48 `:1170`, v50 `:1454`, v51 `:1336`, v52 `:1218`, v53 `:1265`, v54 `:1314`, v55 `:1428` → `get_l1_app_prior_l2` (`qi @ p_u2`, e.g. v54 L432–451) | `softmax_beliefs` then `q@P(U2\|B,U1)` | BP posterior / APP (`P(U1\|B)`; headers v45 L8, v46 L8, v47 L7 state this) |
| `methods/nbldpc_shell_adapter.py:254` | same `softmax → L2 prior` pattern | APP |
| `v72p2d3_gf32_contrast.py:668–689,720–721,1351–1352` (passthrough + `q@P` recombination) | `q = softmax(final_beliefs)` | APP |
| D7-B `v72p2d7_gf32_easy_regime.py:538` (`invoke_decoder`) → `554–578` (`posterior_stats`) → `629–632` (vs exact, tol 1e-10) | softmax then exact-posterior comparison | claimed exact posterior |
| D5 `historical_g0_decoder:1085–1111`, bound-history adapters `:1631`, `:2472` | verbatim passthrough | (no transform; inherits downstream APP reading) |

Sibling (not v35): `nonbinary_v10_fftqspa.py:444–450` builds
probability-domain beliefs from `log_prior + c2v` messages — a different
decoder with a different contract, not applicable here. No consumer
distinguishes iteration-0 from iterated beliefs; no consumer guards on
`iterations == 0`.

## E08 — what D5 expects at L1→L2

`app_fed_l2_prior` (`v72p2d5_gf32_rate_mother.py:353–375`) docstring:
"Production L2 prior `q @ P` from L1 APP beliefs (probability domain)."
Its contract input `q_l1` is therefore the L1 a-posteriori distribution
conditioned on everything disclosed at L1 — channel observations AND the
disclosed syndrome `s1`, i.e. `q ≈ P(U1 | B, s1)` — linearly mixed over
`P(U2 | B, U1)` (`einsum("nq,qnv->nv")`, L374). The diagnostic-only
`oracle_l2_prior` (L378–397, "production decoding must use
`app_fed_l2_prior`") confirms production L2 may only see syndrome-informed
beliefs through `q`, never the truth.

## E09 — iteration-0 return can silently omit syndrome evidence from L2

Yes. The iteration-0 path reports a valid L1 codeword (exact + syndrome-ok,
E06 concepts 1–2) while `final_beliefs` contains no check message (E02) and
`softmax` thereof equals the channel prior (E03). `_run_layered_block`
forwards it unconditionally (L1348–1352), so the L2 prior becomes
`prior@P` instead of `APP@P` — the disclosed syndrome `s1` is silently
dropped from the L2 conditioning set while L1 success is reported. The
hazard is latent (real channel priors rarely satisfy the syndrome at
iteration 0) but structural: the code path has no iteration guard.

## E10 — D7-B's posterior criterion: inapplicable gate, valid signal

Both, at different layers. As a decoder-calibration PASS/FAIL gate applied
to a legitimately early-stopped hard-decision decoder, the criterion is
inapplicable at iteration 0 (it demands a conditioned posterior after zero
check updates — a quantity the decoder never claimed to return). As a
detector, its numerical signal is exactly correct: the returned beliefs
provably differ from the exact posterior (E04 reproduces the stored errors
to 2.3e-16), and that divergence is precisely the D5 interface hazard of
E09. So the metric wrongly fails the DECODER but rightly flags the
INTERFACE reading of the same numbers.

## E11 — WSL RSS null classification and future measurement rule

Classification: telemetry dependency gap (one of the three frozen options;
not a code defect, not true resource evidence). Evidence: `_rss_bytes`
(easy-regime L98–104) is written correctly — `psutil` import attempt with
`None` fallback; the WSL venv has no `psutil` (import probe fails here),
which the pre-result review records as a pre-documented environment fact
(R14); all 64 invoked rows store empty `rss_bytes` with zero measured
values, so no breach was observed; the frozen terminal priority
(`run_easy_regime` L739–740, `classify_terminal` L665–683) maps ANY unknown
to `resource_overrun`, converting a telemetry gap into a post-hoc resource
terminal. Minimal future rule (stated only, not implemented): on Linux/WSL
measure with stdlib `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`
multiplied to bytes with the unit documented (Linux reports kibibytes),
via an explicitly available path — and absence of any measurement must fail
BEFORE scientific execution, never convert a useful run post-hoc. (D5
already carries such a stdlib-first pattern at L975–1023; precedent only.)

## E12 — scientifically justified next route

Per the packet §8 mapping, the layer-interface branch applies (E09 hazard
is real), so the justified route is `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`
before D7-C — scoped to the decoder/adapter contract boundary (what L1 may
forward to L2 after an iteration-0 stop), plus the D7-C metric separation of
hard success from posterior calibration that E10 requires. No decoder-belief
repair proposal (v35 promises nothing it violates — E02/I3 below), no R1d,
no G1/G2.

## I1/I2/I3 verdicts, separated by layer

- Decoder hard-decision correctness: I1 holds (64/64 exact+syndrome; the
  early stop is valid for the hard-decision objective). I2/I3 inapplicable.
- Decoder belief-return contract: I1 holds, I3 rejected. `DecoderResult`
  (v35 L519–526) documents no conditioning promise; `decode_row_layered`
  docstring (L645–649) describes only damping; the codebase idiom treats
  log-prior-shaped beliefs as the neutral element (v72p2d3 L668–671
  fallback `np.log(prior_p)`). Returning the current log-belief state is
  internally honest. I2 inapplicable at this layer.
- D5 layer-interface expectation: I2 holds. D5 consumes the value as
  `P(U1 | B, s1)` (E07–E08) while iteration-0 beliefs carry no syndrome
  message — a downstream APP contract defect at the decoder/adapter
  boundary, repair belonging there. I1/I3 inapplicable.
- D7-B metric validity: I1 holds for the gate (inapplicable to iteration-0
  early success), with the E10 qualification that its numerical signal
  correctly detects the I2 interface mismatch. I3 inapplicable (the metric
  never adjudicates v35's contract, which is silent).

## Frozen outcomes

- Primary: `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT` — the D7-B posterior gate
  needs scoped correction for legitimate early stops AND the D5
  iteration-0 forwarding path needs a contract correction; neither alone
  explains the evidence (decoder honest, metric signal real, interface
  omission real).
- Secondary (RSS): `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP` — no evidence points
  to any other cause (E11).
- Not selected: `METRIC_CONTRACT_MISMATCH_ONLY` (denies the real E09
  omission), `DECODER_BELIEF_RETURN_CONTRACT_DEFECT` (v35 promises nothing
  it breaks), `LAYER_INTERFACE_CONTRACT_DEFECT` alone (denies the real gate
  inapplicability), `AUDIT_BLOCKED` (contracts established from source).
- No repair implemented in this packet. Independent review
  (`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md`, reviewer-go) must
  re-verify the v35 return path, all consumers, the 49/15 partition, the
  recomputed posteriors, and the I1/I2/I3 split before any route advances.
