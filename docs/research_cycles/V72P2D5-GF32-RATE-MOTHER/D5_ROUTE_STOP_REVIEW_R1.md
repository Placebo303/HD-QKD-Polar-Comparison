# D5 route-stop review R1 — independent closure review of the current two-layer GF32 rate-mother/BP path

- role: independent route-stop review operator (no implementation, no authorization, no acceptance)
- repo: `D:/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`, HEAD `d6fabf09` (verified pre/post)
- chain: R2 acceptance `247f8adc` (2026-09-08 12:42:04) → prereg `f0e4a1cf` (12:44:50) → evidence/gate `d6fabf09` (12:51:13)
- gate: `D5_ROUTE_STOP_REVIEW`; accepted formal G1 `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`, `passed=false` (unchanged)
- evidence root: `workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/` (3 scripts, 3 scalar JSONs, manifest, command log)
- reviewed report: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md`
- review root (removed after use): `workspace/d5_route_stop_review_r1_8be0fabe/`
- verdict: **`D5_ROUTE_STOP_REVIEW_PASS`**

## S01–S12 verdict table

| ID | item | verdict |
|---|---|---|
| S01 | preregistration integrity | PASS with 3 non-material findings (D1 disclosed; D2/D3 undisclosed-trivial) |
| S02 | CAL-only estimator selection | PASS (bit-identical recompute) |
| S03 | decoder evidence and accounting (75 calls) | PASS |
| S04 | fresh bounded confirmation (8/12 calls) | PASS (0 mismatches) |
| S05 | undetected-type semantic isolation | PASS |
| S06 | terminal-class calibration | PASS with wording correction |
| S07 | block-scaling conclusion | PASS |
| S08 | route-stop scope | PASS |
| S09 | alternative explanation audit | PASS (no missing in-scope discriminator) |
| S10 | lifecycle and evidence preservation | PASS |
| S11 | regression status (four-file suite) | PASS (259 passed) |
| S12 | successor handoff quality | advisory only (≤3 ranked, no design) |

## S01 — preregistration integrity (PASS with findings)

- `f0e4a1cf` is exactly one file (`G1_L1_ESTIMATOR_DISCRIMINATOR_PREREG_R1.md`, +159 lines), committed 12:44:50, after R2 acceptance 12:42:04 and before any score/call (evidence files timestamped 12:45–12:50, landed in `d6fabf09` 12:51:13). Commit timing verified via `git log --format=%ad --date=iso` and filesystem timestamps.
- Item-by-item comparison (prereg → execution):
  - estimators E1/E2/E3 contracts, `lam*=137.3823795883264` (`core.LAMBDA_STAR` asserted equal), grid30 `logspace(-2,3)`, 4 frozen outer folds, `AUDIT_FLOOR=1e-300`/`DECODER_FLOOR=1e-15` in CAL NLL and prior flooring: match.
  - fold script ranges `range(702,958)/range(958,1214)/range(1214,1470)/range(1470,1726)` = TEST `702..957/958..1213/1214..1469/1470..1725` with `TRAIN768/TEST256` asserted per fold: match (262144 rows asserted).
  - decoder set `{E2 winner, E1}` (winner E2 → `{E2,E1}` per §6 rule): match. Mothers n64 `build_dv3_nested_mother(64,59,59,2026090501)` + square `(64,64,64,2026090801)` rank-64 asserted: match. Decoder `bind_historical_decoder`, max_iter=90 (`MAX_ITER`), cold, damping path untouched: match.
  - seeds `2026090600..03` paired across estimators, one axis per control: match (verified in JSON ids).
  - disclosures n64 `{49,59,64}` / n128 `{98,118,128}` / n256 `{196,236,256}` = `ceil(n·49/64), ceil(n·59/64), n`: match.
  - scaling trigger (n64 fail → 128 → 256, stop at first nonzero-rate recovery): match; 256 completed with no recovery, nothing further spent.
  - budgets: 75/1500 calls, max call 2.4099s ≤120s, peak RSS 182894592 B <2GiB, total wall ~78s of 8h: match.
  - stop rules: no `2/4` at any `m<64` point → no MIXED extension: match (square 1/4, 2/4 are zero-rate, excluded by the useful-n64 rule).
- Findings:
  - D1 (disclosed, non-material): decoder blocks for both estimators sampled under the E1 joint law; prereg §5 said each estimator's own law. Disclosed in report §1 table row + §2 + both decoder script docstrings. E2 is L1-only and defines no joint law; executed contrast is prior-only on one shared population. Paired structure preserved; both estimators fail identically so the stop conclusion is insensitive to this axis.
  - D2 (undisclosed, non-material): scaling L1 family built as `build_dv3_nested_mother(n,n,n,seed)` with row-prefix `[:m]`; prereg §7 letter says `build_dv3_nested_mother(n,m_hi,m_hi,seed)`. Prefix-of-full reading is consistent with the frozen plan-level `H[:k]` row-prefix disclosure rule; applied identically to both estimators and both widths; outcomes 0/4 at every nonzero rate either way. Parameter-wording deviation only.
  - D3 (trivial): manifest fold label `F1 TEST 958..1214` vs prereg/script `958..1213` (script `range(958,1214)` is correct; label string off-by-one). No numeric effect.

## S02 — CAL-only estimator selection (PASS)

Independent recompute from canonical CAL-TRAIN parquet only (`val_touched=false`, 262144 rows, zero VAL access; selection script imports no decoder):

| fold | E1 | E2 | E3 | E2 kap* |
|---|---|---|---|---|
| F0 | 3.8182154103956396 | 3.7759098573613636 | 3.8182154103956396 | 62.10169418915616 (idx 22) |
| F1 | 3.8192444999880997 | 3.7770928727972723 | 3.8192444999880992 | 62.10169418915616 (idx 22) |
| F2 | 3.8028967619804774 | 3.7575869482500703 | 3.8028967619804774 | 62.10169418915616 (idx 22) |
| F3 | 3.818612399698665 | 3.776013710811626 | 3.818612399698665 | 62.10169418915616 (idx 22) |
| mean ± SE | 3.8147422680157206 ± 0.003954182840134982 | **3.771650847305083 ± 0.004695588734151163** | 3.8147422680157206 ± 0.0039541828401349404 | unanimous |

- per-fold values, means, SEs: **bit-identical** to `c1_evidence.json` (all `abs diff == 0.0`).
- E1=E3 identity: distribution-table max abs diff 2.78e-16 every fold (fp rounding; F1 scalar diff 4.44e-16). Report's "bit-identical" is accurate for means, overstated by ~4e-16 at one fold scalar — advisory wording note, substance (backoff-linearity identity) confirmed.
- grid identity `logspace(-2,3,30)` asserted (len 30, endpoints 0.01/1000.0); kap* grid index 22 in all 4 folds independently.
- Δ best−runnerup = 0.04309142071063743 ≈ 9.2 SE > 0.01 tie band → E2 wins outright, tie-break not triggered.
- selection used held-out L1 NLL only (c1 script: no decoder import; `sample_matched_block` used solely for resub mass diagnostics, never for selection).
- CAL-info scope: `5.0 − 3.771650847305083 = 1.2283491526949168` vs `2·SE = 0.009391177468302326` → information present; 5.0 bits is the L1-symbol uniform chance `log2(32)`, correctly scoped to L1 (not joint).
- "E2 optimum" is valid **only** within the frozen 3-estimator/grid30 family (see S06 correction).

## S03 — decoder evidence and accounting (PASS, 75/75)

- totals: d2 25 (S0×1 + 2 est × 3 pts × 4 seeds) + d3 50 (2 widths × (S0×1 + 24)) = **75**; counters (`decoder_calls` 25+50, manifest `calls_used` 75) consistent.
- S0 delta-prior sanity 3/3 recovered (iters 0, mass 1.0) → matrix/decoder healthy with signal at all widths.
- paired seeds `{2026090600..03}` in all 72 non-S0 records; disclosures `{49,59,64}/{98,118,128}/{196,236,256}` verified from ids.
- independent exact+syndrome recompute fields present 75/75; `flag_agree` 75/75; `nonfinite` 0/75; `watchdog_ok` 75/75; max wall 2.4099s; max RSS 106958848 B.
- recomputed point rates from raw flags match persisted `point_rates` exactly: n64 all 0/4 (incl. square); n128 nonzero 0/4, square 1/4 (seed 0601); n256 nonzero 0/4, square 2/4 (seeds 0601/02). n64 saturates at 90 iters everywhere incl. square.
- estimator-axis: exact/syndrome outcomes identical per block across E1/E2 everywhere (rates "both estimators identically" confirmed); only iteration counts differ on two recovered square blocks (14 vs 15, 18 vs 33) — outcome-level claim in report is accurate.
- no G2/formal content in evidence (no `2026091xxx` seeds, no `v72p2d5_g1`/VOID refs).
- duplicate/reuse accounting: E1-law blocks reused across estimators by design (paired, one shared population); each decoder invocation counted once — no double-count. The two `syndrome-without-exact` records (E2+E1, n256 m236, seed 0601) are **one block event** seen under two priors; report counts it as one isolated event — correct.

## S04 — fresh bounded confirmation (PASS, 8 calls ≤ 12)

Review-owned nonformal root, explicitly injected estimator (`P1_E2`, kap index-22 asserted), matrices, `bind_historical_decoder`, population law; 120s watchdog, RSS<2GiB. Literal results:

| call | exact | syndrome | flag | iters | wall_s | matches persisted |
|---|---|---|---|---|---|---|
| E2 n64 m59 @0600 | false | false | false | 90 | 0.559 | true |
| E2 n64 m59 @0601 | false | false | false | 90 | 0.563 | true |
| E2 n64 m64-sq @0600 | false | false | false | 90 | 0.564 | true |
| E2 n64 m64-sq @0601 | false | false | false | 90 | 0.561 | true |
| E2 n256 m236 @0600 | false | false | false | 90 | 2.103 | true |
| E2 n256 m236 @0601 | **false** | **true** | **true** | **13** | 0.308 | true |
| E2 n256 m256-sq @0600 | false | false | false | 90 | 2.269 | true |
| E2 n256 m256-sq @0601 | true | true | true | 10 | 0.250 | true |

8 dev decoder calls (budget 12), 0 deterministic mismatches, peak RSS 106614784 B. Key event reproduced exactly: n256 m236 seed `2026090601` → `syndrome_ok=true`, `exact=false`, 13 iters under E2 prior. No blocking mismatch.

## S05 — undetected-type semantic isolation (PASS)

- the n256 m236/0601 event is stored as `exact_recomputed=false` + `syndrome_recomputed=true` + flag true, with point rate `E2 m236: 0/4` (success requires both) — never as recovery, pass, FER, or formal undetected rate.
- aggregation keeps `exact_*` and `syndrome_*` as separate fields in all 75 records; report §4 labels it "Isolated (never success)… development-only undetected-type event, not counted".
- one block event is not a probability estimate; report makes no rate claim from it. Correct.

## S06 — terminal-class calibration (PASS with wording correction)

- allowed meaning holds: none of the preregistered honest estimators (E1/E2/E3-selected E2) recovered any of 4 paired n64 blocks at any tested disclosure through square (0/24), and scaling adds only zero-rate square partials. Evidence supports exactly this.
- disallowed meanings are **not** established and must not be read in: no universal BP-threshold proof, no claim about all estimators or all n64 GF32 codes.
- wording correction (advisory, non-blocking): report §8 "the honest optimum `kap*≈62`" must be read as "the held-out winner within the frozen 3-estimator/grid30 family"; "the decoder's BP threshold" (§6/§8) as the operational threshold of this frozen decoder/matrix/family at n64 with truth mass ~0.10–0.15. "E1≡E3 bit-identical" → "identical up to fp rounding (≤4.5e-16), means exactly equal".

## S07 — block-scaling conclusion (PASS)

- nonzero-rate results are 0/4 at every tested point at n128 and n256, both estimators (verified by recompute); square partials 1/4 (n128, seed 0601) then 2/4 (n256, seeds 0601/02).
- supports stopping further scaling **within D5**: two wider development blocks add only zero-rate square response, never nonzero-rate recovery.
- does not prove larger blocks or different graphs/decoders impossible — report §6 records width-responsive counterevidence (0/4→1/4→2/4) and §8 scopes larger blocks "out of D5 scope". Correct boundary.

## S08 — route-stop scope (PASS)

PASS closure (exact):

```text
D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED
reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY
```

- consequences: no frozen G2 on this path; no formal G1 rerun/tuning; all evidence and negative outcomes retained; no n=1024 on this path; any next work needs a fresh successor proposal changing a named algorithmic component (not another estimator/disclosure/seed tweak).
- explicit non-consequences: no rejection of GF32, NB-LDPC, finite-field BP, Model-F, larger blocks, alternative graph/mother, decoder schedule, or single-layer design; no statement about real FER, leakage, key rate, or security.
- calibration: report §8 "do not pursue block scaling further" is read as within-D5 only; larger-block geometry remains a legitimate successor component (S12), not an authorized execution.

## S09 — alternative explanation audit (PASS, no missing discriminator)

| alternative | assessment |
|---|---|
| n64 finite-size artifact | width arm already spent (128/256): only zero-rate square response grows; no nonzero-rate signal ≤256. Cannot rescue frozen G2. Successor-relevant only. |
| graph-family/prefix defect | possible in principle, but S0 passes at every width and construction is the frozen dv3 family; swapping graphs = new proposal, not frozen G2. |
| layered L1 bottleneck while L2 healthier | consistent with evidence (L1 mass ~0.10–0.15 vs ~0.28 needed), but current path is two-layer rate-mother; single-layer/decomposition redesign = successor. |
| alternative BP schedule/initialization | same — a named decoder change belongs to a fresh proposal, not to running frozen G2. |
| estimator-family limits | exhausted within prereg: E1≡E3 collapse leaves selection-strength axis only, E2 honestly selected, +0.015 mass lift is an order of magnitude short. |

No still-plausible explanation makes the **unchanged-path** G2 informative: frozen G2 would reuse the same decoder/matrix/seed-regime that just went 0/72 at nonzero rate on top of accepted G1 no-signal. No missing in-scope discriminator blocks closure.

## S10 — lifecycle and evidence preservation (PASS)

- commits/manifests: `247f8adc` (R2 accept) → `f0e4a1cf` (single prereg file) → `d6fabf09` (evidence + `next_gate=D5_ROUTE_STOP_REVIEW`); manifest file list matches the 8 evidence-root files; `terminal_class`, `val_touched=false`, `g2_absent=true` recorded.
- authorizations: `g1_execution_authorized=false`, `g2_execution_authorized=false`, `synthetic/real/formal_execution_authorized=false`, `scientific_promotion=false` (cycle_state.yaml). `decoder_executed=true` is the historical G1 record, not an authorization.
- promotion false; formal G2 root absent (`workspace/v72p2d5_g2_20260907_r2` does not exist); formal G1 root files predate D5 work (2026-09-08 02:39) and are never referenced by any D5 script.
- scoped `git status`/`git diff HEAD` over `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/`, the evidence root, and the core module: empty. No push performed; HEAD `d6fabf09` identical pre/post review.
- note: the wider worktree carries extensive pre-existing modifications unrelated to D5 (present before this review; untouched). Pre/post scoped snapshots identical.

## S11 — regression status (PASS)

Fresh basetemp, `-p no:cacheprovider`, exact four-file suite:

```text
259 passed, 1 warning in 57.87s
```

(zero failures; the single warning is the benign `Unknown config option: cache_dir`. Basetemp lived in the removed review root.)

## S12 — successor handoff quality (advisory, ≤3, no design)

Evidence-ranked components a fresh proposal must change (main thread selects; authorizes nothing):

1. **two-layer decomposition / L1 bottleneck** — L1 truth mass ~0.10–0.15 vs ~0.28 needed is the binding constraint; E2 already extracts the honestly-available CAL L1 information (MI 0.99) yet the decoder never moves at nonzero rate.
2. **graph/mother construction and short-block topology** — dv3-nested prefixes saturate at 90 iters even at square n64; width helps only at zero rate.
3. **BP schedule/decoder dynamics** — identical per-block outcomes across estimators with instant convergence on S0-delta vs total saturation otherwise suggests dynamics, not priors, are the wall.

Not ranked: channel-model representation (CAL model already informative, 3.77 vs 5.0 bits), block geometry beyond successor scope.

## Findings summary

- F-D1 (disclosed, non-material): E1-law shared blocks for both estimators (S01-D1).
- F-D2 (undisclosed, non-material): scaling family built `(n,n,n)`+prefix vs prereg `(n,m_hi,m_hi)` letter (S01-D2).
- F-D3 (trivial): manifest F1 fold label off-by-one in string only (S01-D3).
- F-W1 (wording): "honest optimum" → frozen-family winner; "BP threshold" → operational, this-decoder/family/n64 (S06).
- F-W2 (wording): "E1≡E3 bit-identical" → up to 4.5e-16 fp rounding, means exactly equal (S02).
- No material prereg violation; no VAL/decoder-outcome selection; no exact/syndrome conflation; no scope overreach after calibration; tests green; roots preserved.

## Final verdict

**`D5_ROUTE_STOP_REVIEW_PASS`**

```text
D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED
reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY
```

The current D5 two-layer rate-mother/BP operating path shall not enter G2 or n=1024; successors require new proposals selected by the main thread. This does not reject GF32/NB-LDPC/Model-F and authorizes no execution.
