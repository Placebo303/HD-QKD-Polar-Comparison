# D7-B early-exit soft-belief audit independent review R1

Verdict: D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS

Packet: `.workbuddy/tasks/D7_B_RESULT_ACCEPT_EARLY_EXIT_AUDIT_R1_TASK_PACKET.md` §7
(§0 frozen adjudication, §8 route mapping as binding input).
Audited: `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md` (untracked, unmodified by reviewer).
Acceptance: `D7_B_RESULT_ACCEPTANCE_R2.md` (committed `4dec0e5c`).
Method: independent re-read of v35/D5/D7-B source, independent re-counts from the
R2 root CSV, self-written GF(32)/posterior math in `/tmp` (numpy+stdlib only;
no repo import, no decoder binding, no oracle import). Zero decoder calls, zero
reruns, zero root writes, zero production edits. One terminal verdict only
(the token in the line above); no alternative terminal is taken.

## 0. R2 root immutability (read twice, full-iso)

- Start and end listings identical, exactly five files, zero subdirectories:
  `command_log.txt` 111 B 2026-09-10 20:33:38.213856000,
  `decoder_records.csv` 44743 B .208855500,
  `manifest.json` 1008 B .204503600,
  `report.md` 80 B .211856000,
  `summary.json` 449 B .210858600 (all +0800).
- `summary.json`: `terminal D7_B_RESOURCE_OVERRUN`, `calls_invoked 64`,
  `calls_not_needed 384`, `resource_overrun true`, `confirmed/partial false`.
- Conclusion: root untouched; review proceeded (no STOP condition met).

## 1. 49/15 partition + error stratification (independent CSV counts)

- Invoked rows 64; `iterations`: `{'0': 49, '1': 15}` — matches E01/A04.
- Per (tier, prior, iter): SINGLE P99/P90/P60 4x it0 each; SINGLE PAIR 1x it0 +
  3x it1; TREE P99/P90/P60 4x it0 each; TREE PAIR 4x it1; CYCLE P99/P90/P60 4x
  it0 each; CYCLE PAIR 4x it1; FULL P99/P90/P60 4x it0 each; FULL PAIR 4x it1.
  E01 table reproduced exactly.
- PAIR mechanism re-derived independently: `truth_for` =
  `default_rng(seed).integers(0,32)` gives SINGLE seed 2026091202
  `x=[30,20,8]` (all-even); it is the ONLY all-even PAIR cell of all 16
  (TREE/CYCLE seeds each contain an odd symbol; FULL_RANK seeds contain
  29–33 odds of 64). Stored CSV shows exactly that cell as the single PAIR
  it0 row; PAIR prediction matches 16/16 stored rows. E01 mechanism holds.
- `rss_bytes` empty on 64/64 invoked; `exact` 64/64; `syndrome_ok` 64/64.
- Tractable post_err dump re-verified: SINGLE it0 {P99 0.00999, P90 0.09916,
  P60 0.36396} x4 seeds each; SINGLE PAIR it1 ~1e-16 x3 + it0 0.50033 x1;
  TREE it0 {P99 0.01000, P90 0.10000, P60 0.39966} x4 each;
  TREE PAIR it1 0.00689 x4. CYCLE_8/FULL_RANK_64: `post_err`/`map_agree`
  empty on all 32 rows. Within-(tier,prior) seeds agree to ~14 significant
  digits. E05 table holds.
- Entropy fingerprints re-verified: P99 0.130335099, P90 0.964415225,
  P60 2.952629119 (CSV: 0.13033509899978016 / 0.9644152246279681 /
  2.952629118609419). `mean_true_p == max_p` == prior peak on every it0 row.

## 2. v35 initial-return path + final_beliefs consumers (E02/E07/E08 re-read)

- `v35_algorithm_development.py`: L659–665 init `beliefs = log(priors_clean)`
  (floor 1e-15 + renorm; `warm_beliefs` copy otherwise — D7-B passes `None`
  positionally at `easy-regime` L520–524 with damping `1.0`, cold); L676–678
  `check_to_var` all zeros; L681 `best_x = argmax(beliefs)`; L683–692 on
  syndrome match return `iterations=0, status="converged_exact",
  final_beliefs=beliefs` — the untouched log-prior, zero check messages.
  E02 confirmed line-by-line.
- Flooding contrast confirmed: `decode_flooding_fftqspa` loop starts `it=1`
  (L591), first return L607–616 follows a full check-update round; it0 path
  exists only in `decode_row_layered_fftqspa` bound via `bind_historical_decoder`
  (easy-regime L490–506). Confirmed.
- `DecoderResult` (v35 L519–526) is a bare dataclass: no conditioning promise
  on `final_beliefs`. Row-layered docstring (L645–649) documents only damping
  semantics. `v72p2d3` L670–671 fallback `final_beliefs = np.log(prior_p)`
  confirms the codebase idiom of log-prior-shaped beliefs as neutral element.
- Consumers (each line re-opened; computation + reading confirmed):
  D5 `_run_layered_block` L1348–1352 `q = _softmax_rows(bel)` unconditionally →
  `app_fed_l2_prior(p2, bob, q)`; `_softmax_rows` L948–952; v45:1046 (+header L8
  "BP posterior / APP approximation"), v46:1166, v47:1091 (+header L7),
  v48:1170, v50:1454, v51:1336, v52:1218, v53:1265, v54:1314, v55:1428 —
  all `q = softmax_beliefs(res.final_beliefs)` then `q @ P(U2|B,U1)`
  (v54 `get_l1_app_prior_l2` L432–451 `out[i] = qi @ p_u2`);
  `nbldpc_shell_adapter.py:254` same pattern; `v72p2d3` L668–689 / L720–721 /
  L1351–1352 passthrough + `q @ P` recombination; D7-B `invoke_decoder` L538 →
  `posterior_stats` L554–578 → exact comparison L629–632 (`POST_TOL = 1e-10`,
  L44); D5 historical adapters L1085–1111 / L1631 / L2472 verbatim passthrough.
  Sibling `nonbinary_v10_fftqspa.py:444–450` is a different probability-domain
  decoder, correctly excluded. Repo-wide `final_beliefs` grep yields no further
  production consumer — inventory complete, E07 holds.
- No consumer distinguishes `iterations == 0` (grep over D5/v45/v72p2d3/adapter/
  D7-B: zero guards). E07 "no iteration guard" holds.
- E08: `app_fed_l2_prior` docstring L353–354 "Production L2 prior `q @ P` from
  L1 APP beliefs (probability domain)", recombination `einsum("nq,qnv->nv")`
  L374 ⇒ contract input `q ≈ P(U1 | B, s1)` (channel AND disclosed L1 syndrome).
  `oracle_l2_prior` L378–397 ("production decoding must use `app_fed_l2_prior`")
  confirms production L2 sees syndrome only through `q`. E08 holds.
- E09 follows structurally: it0 `final_beliefs` carries no check message (E02)
  and softmaxes to the channel prior (review §3), yet `_run_layered_block`
  forwards it as APP ⇒ L2 prior becomes `prior@P`, silently dropping `s1`
  while L1 reports a valid codeword. Latent (real priors rarely satisfy at
  it0) but real code path. E09 holds.
- E03 floor analysis re-verified: prior minima P99 0.01/31 = 3.2e-4,
  P90 0.10/31 = 3.2e-3, P60 0.40/31 = 1.29e-2, PAIR 0.02/30 = 6.7e-4 —
  all ≥8 orders above the 1e-15 floor ⇒ flooring is identity; independent
  softmax recomputation gives max|softmax−prior| ≈ 1–3e-16. E03 holds.

## 3. Independent exact-posterior recomputation (E04; own GF, no decoder)

- Own GF(2^5) from declared poly `0b100101`: add = XOR; mul = shift/XOR with
  reduction; validated by (a) generator-2 order check `exp[31] == 1`
  (primitive ✓), (b) 2000 randomized mul cross-checks vs exp/log tables: 0
  mismatches. No production table/FFT/oracle used.
- Formula: `P(x|s) ∝ ∏ᵢ priorᵢ[xᵢ] · [H·x == s]`; SINGLE by full 32³ enumeration
  to per-variable marginals; TREE by 1024-separator enumeration
  (z0/z2/z1 → w → cavity leaf sums). `post_err = max|prior − exact|` (it0
  beliefs = prior, §2–3). Priors rebuilt from frozen formulas; truths from
  `default_rng(seed)`; syndromes from own GF arithmetic.

| cell | mine | stored | |diff| | exact true-mass | prior peak |
|---|---|---|---|---|---|
| SINGLE P99 s2026091200 | 0.009993385285716 | 0.009993385285694 | 2.2e-14 | 0.999993 | 0.99 |
| SINGLE P60 s2026091200 | 0.363960004395127 | 0.363960004395122 | 5.6e-15 | 0.963960 | 0.60 |
| SINGLE PAIR s2026091202 | 0.500332669999432 | 0.500332669999434 | 1.4e-15 | 0.990333 | 0.49 |
| TREE P60 s2026091200 | 0.399663616473850 | 0.399663616473850 | 0.0 | 0.999664 | 0.60 |
| TREE P90 s2026091201 | 0.099998560658138 | 0.099998560658138 | 1.1e-16 | 0.999999 | 0.90 |

- All 5 within the 1e-12 task tolerance (2 SINGLE + 1 TREE minimum exceeded:
  3 SINGLE + 2 TREE). Scale explanation confirmed: error attained at
  (variable, true symbol) and equals concentration deficit
  `exact − prior`: 0.990333−0.49 = 0.50033 (SINGLE PAIR),
  0.999664−0.60 = 0.39966 (TREE P60). The 0.5/0.4 magnitudes are exactly what
  an unconditioned prior shows against a satisfied-syndrome posterior. E04 holds.
- Precision note (non-blocking): my worst diff is 2.2e-14 (SINGLE P99),
  above the audit's stated ≤2.3e-16 but inside 1e-12; consistent with
  summation-ordering float effects over 32768 terms, not a value error.
- Tie note (non-blocking): in uniform-prior SINGLE cells all three variables
  share the identical max error (e.g. 0.36396 ×3), so argmax location is a
  tie — audit's "(v0, x_true)" vs my "(v1, x_true)" on seed 2026091200 are
  both maximal; PAIR/TREE argmax locations match exactly.

## 4. E06 arbitration + required transcription correction

- Verified: hard correctness 64/64; syndrome satisfaction 64/64;
  MAP agreement 32/32 tractable; posterior calibration (tol 1e-10): 25/25
  tractable it0 rows fail, it1 splits into 3 passes (SINGLE PAIR, ~1e-16) and
  4 fails (TREE PAIR, 0.00689). The four-way word-vs-belief distinction holds.
- 需修正点 (arithmetic/transcription; recorded here, audit file NOT edited by
  reviewer): E06 writes "fails on all 29 tractable iteration-0 rows". The
  tractable it0 count is 25, not 29 (13 SINGLE + 12 TREE). 29 is the TOTAL
  tractable failure count (25 it0 + 4 TREE PAIR it1); the sentence omits the 4
  TREE it1 failures at 0.00689. Correction: "fails on all 25 tractable
  iteration-0 rows (plus 4 TREE PAIR iteration-1 rows at 0.00689); passes on
  the 3 SINGLE PAIR iteration-1 rows". E05's table already shows the correct
  stratification, so no conclusion changes — non-blocking.
- E10 duality endorsed: as a decoder-calibration gate on legitimately
  early-stopped hard decisions the tol criterion is inapplicable at it0 (the
  decoder never promised a conditioned posterior); as a detector its numbers
  are exactly right and flag the E09 interface hazard. Both halves verified.
- E11: `_rss_bytes` (easy-regime L98–104) is correctly written
  (psutil-try/None-fallback); venv lacks psutil (pre-result review R14
  pre-documents this); 64/64 invoked rows store empty `rss_bytes` with zero
  measured values; terminal priority (`run_easy_regime` L739–740
  `rss_unknown → over`, `classify_terminal` L665–683) converts telemetry
  unknown into post-hoc `resource_overrun`. Classification
  `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP` is the only consistent choice (not a
  code defect, not resource evidence). Future stdlib rule stated-not-
  implemented, consistent with packet §8 (D5 L975–979 `resource.getrusage`
  pattern cited as precedent only). E11 holds.
- E12 route follows packet §8 from the verified primary outcome (see §5).

## 5. I1/I2/I3 challenge — primary + secondary uniqueness

- Decoder hard-decision layer: I1 holds (64/64 exact+syndrome; early stop valid
  for the hard-decision objective). No evidence for I2/I3 here.
- Decoder belief-return layer: I1 holds, I3 rejected — `DecoderResult` carries
  no conditioning promise, the row-layered docstring promises only damping
  semantics, and the log-prior fallback idiom shows current-state return is
  internally honest. A challenger arguing I3 must cite a promise that does not
  exist in source; none found.
- D5 layer-interface layer: I2 holds — D5's documented contract input is
  syndrome-conditioned APP (E08) while it0 beliefs provably carry no syndrome
  message (E02–E03). A challenger arguing metric-only must deny this real
  unconditional forwarding path (L1348–1352, no guard); the path exists.
- D7-B metric layer: I1 holds for the gate (inapplicable at it0) with the E10
  qualification that its signal validly detects the I2 mismatch. A challenger
  arguing interface-only must deny the gate inapplicability; the decoder's
  silence on belief contract plus legitimate early stop establishes it.
- Therefore `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT` is uniquely established;
  `METRIC_CONTRACT_MISMATCH_ONLY` (denies real E09 omission),
  `DECODER_BELIEF_RETURN_CONTRACT_DEFECT` (invents a promise),
  `LAYER_INTERFACE_CONTRACT_DEFECT` alone (denies real gate inapplicability),
  and `AUDIT_BLOCKED` (contracts are source-established) are all rejected on
  evidence. Secondary `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP` likewise unique (§4).
  Next route per §8 mapping: `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`
  before D7-C; no decoder-belief repair, no R1d, no G1/G2. E12 holds.

## 6. Acceptance wording + authorization / no-push checklist

- Acceptance doc states all twelve packet-§3 items without reinterpretation:
  lifecycle/five-file evidence accepted; terminal stays
  `D7_B_RESOURCE_OVERRUN`; RSS-unknown ≠ measured breach, no `<2GiB` PASS;
  64/64 exact+syndrome at cap 1; 49 it0 / 15 it1; 48 truth-centered it0 as
  initial-MAP sanity (not BP gain); PAIR as the only generally-swept family;
  posterior-tolerance failure (0.500/0.400 vs 1e-10) with MAP 32/32; scope
  exactly `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`;
  no `CONFIRMED`/`PARTIAL`; no FER/leakage/key-rate/CAL/qualification/R1d/G2/
  broad-NB-LDPC claim. Frozen terminal not upgraded; scope long name exact;
  no `CONFIRMED/PARTIAL/FER/leakage/key rate` spillover. Holds.
- `cycle_state.yaml`: `d7b_execution_authorized false`,
  attempts/completed 1/1, decoder/result `true/true`,
  `d7b_r2_terminal D7_B_RESOURCE_OVERRUN`,
  `next_gate D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT`, scope long name exact;
  all execution/promotion authorizations false; G1/G2 false;
  `r1d_state R1D_PAUSED_PENDING_DECODER_CERTIFICATION_AND_EASY_REGIME`.
- Reviewer performed zero decoder/phase/data execution, zero root or
  production writes, zero VOID reads; review math used only root scalars,
  source text, frozen docs, and `/tmp` self-written arithmetic. No commit, no
  push by reviewer (commit by follow-up coder-fast). R1d/G2 absent; protected
  roots untouched (out of review scope, no writes made anywhere).

## 7. Blocking assessment

- No BLOCKED condition (root consistent, contracts source-established, no
  decoder call needed or made, no fix required to advance the §8 route).
- One non-blocking transcription correction recorded in §4 (E06 "29 it0 rows"
  → "25 it0 rows + 4 TREE it1 rows"; total failures 29 unchanged). No other
  correction needed; audit file left unedited per packet.
- Route is NOT blocked: advance to `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`
  per the §8 layer-interface/mixed mapping once the one-line E06 correction
  is applied in a follow-up commit alongside this review.
