# TRACEABILITY — claim → evidence map

Packet `s01_dimension_probe_20260923`. Track: EXPLORE. Whole packet `diagnostic_only`.

Every row below states a claim and **where its evidence lives**. The `reproduce` column is
a command anyone can run to check it. Where a claim has been retracted or downgraded,
the row says so and points at the correction. Nothing in this index is itself evidence;
it is a map to evidence.

**Legend** — evidence classes: `[F]` frozen artifact · `[D]` derived from frozen facts ·
`[I]` inference (assumption named) · `[3P]` third-party, unverifiable here · `[R]` retracted.

---

## Part A — Channel structure (arm A0), settled

| id | claim | tag | evidence | reproduce |
|---|---|---|---|---|
| A1 | raw SER = 0.077056884766 over 32768 characterised positions; 2525 error symbols | `[F]` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d01_20260814/channel_diagnostics.json` → `aggregates.raw_ser.mean`; `step0_fline.json:F1_totals` | `.venv/bin/python workspace/s01_dimension_probe_20260923/step0_fline.py` |
| A2 | only **11 distinct difference symbols** out of q=1024 (1.07 %) | `[F]` | same file → `aggregates.symbol_difference.unique_difference_symbols`; `step0_fline.json:F1_totals` | idem |
| A3 | 96.48 % of errors have \|Δ\|<32; the \|Δ\|≥32 "uniform floor" is 89 symbols = **3.53 %** of errors | `[F]` | `step0_fline.json:F1_magnitude_classes` (per-class counts/masses) | idem |
| A4 | `Σ_j p_j = raw_ser` **bitwise** (0.077056884765625 = 0.077056884765625) | `[F]` | `step0_fline.json:F2_gray_plane_occupancy` (`sum_plane_rates`, `raw_ser`, `difference`, `bitwise_equal`) | idem |
| A5 | therefore `E[#Gray planes flipped \| error] = 1.000000000000`; uniform-Δ counterfactual would be ≈5 / 0.385284 | `[D]` proof of the inference is in `FINDINGS.md` §1.1 | `step0_fline.json:F2_gray_plane_occupancy` (both counterfactual fields) | `.venv/bin/python -c "import json;d=json.load(open('workspace/s01_dimension_probe_20260923/step0_fline.json'));g=d['F2_gray_plane_occupancy'];print(g['sum_plane_rates']==g['raw_ser'],g['expected_planes_flipped_per_error'])"` |
| A6 | `Σ_j h2(p_j) = 0.549955044` bits/symbol vs frozen empirical `H(diff) = 0.546972930`; capture ratio **1.005452**; signed loss −0.5452 % | `[F]` pair + `[D]` ratio | `step0_fline.json:F3_binary_decomposition_loss` | idem |
| A7 | QSC(p=0.2) model entropy 2.721646181 is **4.976×** the empirical H | `[D]` | `step0_fline.json:F3_binary_decomposition_loss.model_pessimism_vs_empirical` | idem |
| A8 | per-plane rates (LSB-first) LSB 0.037506103515625 → MSB 0.000030517578125 | `[F]` | `step0_fline.json:F2_gray_plane_occupancy.plane_rates_msb_first` (reversed); cross-checked bit-for-bit against `aggregates.bit_plane_mismatch.mismatch_rate` in D01 | `load_ladder()['step0_reverse_equals_d01']` in `a1f_rate_levelling_control.py` |
| A9 | **caveat, tested**: the three routes to conditional entropy agreeing to ~0.5 % is an internal-coherence check, **not** independent corroboration (under single-plane structure the pooled law is determined by the ladder) | `[I]` | `FINDINGS.md` §2.3 caveat; `step0_fline.json:F3.entropy_routes_are_not_independent` | — |
| A10 | **caveat, originally wrong then sharpened**: the `1+r = 11` alphabet identity needs an XOR/parity convention and holds under Gray-XOR too, so the original natural-vs-gray dichotomy was too coarse. The frozen buckets `(32,64):41, (96,128):31, (224,256):12, (480,512):4, (992,1024):1` equal the MSB 1–5 flip counts `[41,31,12,4,1]` exactly; Gray `{63,127,255,511,1023}` land in non-zero buckets, natural `2^k` in **empty** buckets ⇒ per-plane XOR values are **identified**, not merely bucket-resolved | `[D]` | `FINDINGS.md` §3.1; `EXPLORATION_LOG.md` Entry 12.5 (F13 applied) | recompute: `counts = [1,4,12,31,41]` vs the five non-zero `symbol_difference.bucketed_histogram_counts` |

## Part B — Effective-alphabet reduction, settled

| id | claim | tag | evidence | reproduce |
|---|---|---|---|---|
| B1 | covering an 11-valued support with the smallest field gives GF(16) | `[D]` | `effective_alphabet.py` / `.json:G1_effective_support` | `.venv/bin/python workspace/s01_dimension_probe_20260923/effective_alphabet.py` |
| B2 | nominal `(q²+q)` node cost falls GF(1024)→GF(16) by **≈3858.8×** | `[D]` | `effective_alphabet.json:G2_node_complexity` (full table 1024/32/16/11/8/4) | idem |
| B3 | that reduction is lossless *with respect to this frozen law* — conditional on the aggregate being representative, which fresh data would test | `[I]` | `effective_alphabet.json:G2.information_loss`; caveat in `FINDINGS.md` §3.2 | — |
| B4 | per-plane `β_max = 1/h2(p_k)`; the binding plane is the LSB, **4.3339** | `[D]` | `effective_alphabet.json:G3_disclosure_allocation` | idem |
| B5 | **RETRACTED over-reach**: `4.3339` is the ceiling of *entropy-proportional per-plane binary allocation*, **not** of the framework. Framework ceilings: binary any allocation `10/Σh2 = 18.1833`; native `r/H = 18.2824` at r=10 | `[R]` | correction: `EXPLORATION_LOG.md` Entry 10 §B1; `FINDINGS.md` §4 | `.venv/bin/python -c "print(10/0.5499550439219351, 10/0.5469729299832656)"` |

## Part C — V13 R3 single-pass identity, settled (as a retraction of our own claim)

| id | claim | tag | evidence | reproduce |
|---|---|---|---|---|
| C1 | V13 R3 is recorded as native q=1024, n=256, rate 0.336, leakage 6.64 bits/symbol, `f≈12.1` | `[F]` | `CURRENT_TASK.md:799`; `AGENT_PROJECT_MEMORY.md:3201,3237`; `AGENT_HANDOFF.md:733` | `grep -n "12.1" CURRENT_TASK.md AGENT_HANDOFF.md` |
| C2 | `(1−0.336)·256·log2(1024) = 1699.84 bits/frame = 6.64 bits/symbol`, with `m = 170 ≤ n = 256` — i.e. V13 R3's disclosure is **arithmetically identical to a single-pass native syndrome** | `[D]` | `EXPLORATION_LOG.md` Entry 10 §B1; `FINDINGS.md` §4 | `.venv/bin/python -c "print((1-0.336)*256*10, (1-0.336)*256)"` |
| C3 | therefore **"V13 R3's f≈12.1 cannot be single-pass / must be interactive" is withdrawn**; it is an efficiency gap against `H(diff)=0.547` | `[R]` | `EXPLORATION_LOG.md` Entry 10 §B1; `FINDINGS.md` §1.4 (RETRACTED), §4, §8.3 (deleted/replaced) | — |
| C4 | also withdrawn: "V19's f≈4.169 sits just below the ceiling" — `docs/v19-binary-mlc-prototype-result-20260816.md:14-16` attributes it to conservative H1 row counts (a codebook limit); the proximity is coincidence | `[R]` | `EXPLORATION_LOG.md` Entry 10 §B1; `FINDINGS.md` §4 | `sed -n '14,16p' docs/v19-binary-mlc-prototype-result-20260816.md` |
| C5 | our own script contained the ceiling that refutes us: `beta_max_native = r/H` | `[F]` about our code | `a1b_decoder_validation.py` (`beta_max_native`); its value 6.654108… at r=3 was computed during arbitration | `grep -n beta_max_native workspace/s01_dimension_probe_20260923/a1b_decoder_validation.py` |

## Part D — Decoder arbitration (why any number is citable at all)

| id | claim | tag | evidence | reproduce |
|---|---|---|---|---|
| D1 | four implementations existed and gave mutually exclusive binary-arm results (0.0000 / 1.0000 / 0.07) ⇒ none publishable | `[F]` about the situation | `EXPLORATION_LOG.md` Entry 8, 9.1, 10 §B3; `FINDINGS.md` §7.1 table | — |
| D2 | brute-force ML arbiter is **self-contained** (imports only `formal_ir.nonbinary_field`, no workspace file) | `[F]` | `a1b_decoder_validation.py` header + import list | `grep -n "^import\|^from\|spec_from_file" workspace/s01_dimension_probe_20260923/a1b_decoder_validation.py` |
| D3 | binary SPA == ML **equals** "SPA returned a codeword" in all five configurations ⇒ **zero undetected**; 185/163/156/206/142 of 250 | `[F]` | `a1b_run.log` PART 1; `FINDINGS.md` §7.2 table | read `a1b_run.log` |
| D4 | binary decoder is **y-sensitive**: 12 distinct codewords decoded noiselessly → **12/12 exact**, 11 distinct estimates | `[F]` | `a1b_run.log` PART 1 y-sensitivity line; `a1b_authoritative.json:y_sensitivity_binary` (q=4 rows only after overwrite — see F-series) | idem |
| D5 | earlier `binary FER = 0.0000` was caused by a y-blind channel LLR plus a syndrome-only success criterion | `[R]` | `EXPLORATION_LOG.md` Entry 8 Bug 2; Entry 9.2; `FINDINGS.md` §7.2 | — |
| D6 | q-ary GF(8): QSPA==ML 247/250 (codeword 248 ⇒ 1 undetected), 142/150 (codeword 142) | `[F]` | `a1b_run.log` PART 2 | idem |
| D7 | backup operator independently verified its check-node update against exact brute-force convolution to 2.8e-17 | `[3P]`+`[F]` operator-side | reported by `coder-fast-backup`; recorded `EXPLORATION_LOG.md` Entry 9.3 | not reproducible here |
| D8 | backup operator traced and fixed a one-token belief-step bug (`bincount(weights=Lvc)` used v2c where c2v was meant); before the fix 0/10 at rate 0.22 vs capacity 0.806, after 20/20 | `[3P]` | operator report; `EXPLORATION_LOG.md` Entry 9.6 | not reproducible here |

## Part E — A1 matched-disclosure screening, settled

| id | claim | tag | evidence | reproduce |
|---|---|---|---|---|
| E1 | grid actually executed `{4,8,16,32}`; q=4 was added by `a1d_q4.py` after the batch-end ruling; q=32 is **unauthorised corroboration only** | `[F]` | `a1_authoritative_merged.json:grid`; `EXPLORATION_LOG.md` Entry 11.2 | `.venv/bin/python workspace/s01_dimension_probe_20260923/a1e_consolidate.py` |
| E2 | disclosure matched per cell; `D = r·ceil(n·β·H/r)` recomputed 117/174/231/348/579 (q=8), 128/192/256/380/632 (q=16), 135/200/270/400/665 (q=32), 96/144/192/288 (q=4) | `[F]` | `a1_authoritative_merged.json:rows`; both logs agree on **21/21 rows** | idem |
| E3 | at every non-degenerate β and every q, native FER < binary FER, Wilson 95 % intervals disjoint in the same direction (12 cells) | `[F]` | `a1_authoritative_merged.json:rows`; `FINDINGS.md` §7.6 table | recompute Wilson from the integer counts |
| E4 | β=2.0 ratios from **integer failure counts**: q=4 **965/19 = 50.8×**; q=8 **1085/6 = 180.8×**; q=16 **1116/2 = 558.0×**; q=32 1153/4 = 288.2× | `[F]` | `a1_authoritative_merged.json:ratio_at_beta_2`; `a1b_authoritative.json` (q=4 exact) | idem |
| E5 | headline is **50.8×–558×** across the prereg grid (previously "181–558×", which excluded the smallest ratio and biased the lower bound 3.5× upward) | `[R]`→corrected | `FINDINGS.md` §1.6, §7.6, §8.3; `EXPLORATION_LOG.md` Entry 12.3 | grep `50.8×–558×` in FINDINGS |
| E6 | the "ratio grows monotonically with q" reading is **downgraded**: only β=2.0 gives 3 usable points (β=1.0 all ~1.1× and unordered; β=3.0 censored — native 0 everywhere), q=32 reverses the trend (558→288, and 5.51→5.23 at β=1.5), native denominators 2/6/19 with overlapping Wilson intervals, and the three points sit at different disclosures and channels. It is already implied by the allocation mechanism | `[D]`→downgraded | `FINDINGS.md` §7.6 trend paragraph; `EXPLORATION_LOG.md` Entry 12.4 | recompute Wilson intervals from the counts |
| E7 | `undetected` is counted separately and never merged into **success** — it *does* count as a failed frame, so it is inside FER but outside success/FER-as-commonly-quoted. Totals are 0 except three single-digit cells at β=1.0 | `[F]` | `a1_authoritative_merged.json:rows.und_binary/und_native`; `a1f_operator_report.md:16-18` (states it correctly) | idem |
| E8 | both arms use random-regular `dv = 3`, so the result is about **this ensemble**, not about what an optimised construction would do on either side | `[I]` | `FINDINGS.md` §7.8 | — |
| E9 | the experiment lives in `β ≤ 1/h2(p_LSB) ≈ 4.33` for the binary arm and `β ≤ r/H` for native; it says nothing about the low-leakage regime where the literature anchor `f≈1.10–1.17` sits | `[D]` | `FINDINGS.md` §7.8 | — |

## Part F — The mechanism claim and its open test

| id | claim | tag | evidence |
|---|---|---|---|
| F1 | the mechanism is **allocation, not information**: per-plane rates `1−β·h2(p_k)` drive the quietest planes to 0.97–0.999, where dv=3 is hopeless; the native arm pools the same disclosure into one moderate rate `1−β·H/r` | `[D]` | `FINDINGS.md` §7.7 (per-plane rate/capacity table) |
| F2 | this does **not** contradict the information-level result: the aggregate requirement is identical and the exploitable inter-plane dependence is 0.545 % of H | `[D]` | `FINDINGS.md` §1.1, §1.2, §7.7 |
| F3 | **RUN (§7.9).** Rate-levelled binary (`m_k = m_n`) is **worse** than entropy-proportional in 8/8 feasible cells, and native leads 1–2 orders of magnitude | `[F]` | `a1f_rate_levelling_control.json` + `a1f_operator_run.log`; `FINDINGS.md` §7.9 |
| F3a | **RUN (§7.10) — establishes only the NEGATIVE claim.** Allocation family `m_k ∝ h2(p_k)^(1−γ)` (the handoff's own formula was wrong — see §7.12), γ∈{−0.5, 0, 0.5, 1}, q∈{4,8,16}, β∈{2,3}, 24/24 cells feasible, no clamping, `max_iter=60`. `B-min` is at **γ=0 in 5 of 6 cells**; the one exception (q8/β3, γ=0.5) is 20/1200 frames ≈ 0.9 non-paired se — noise, and two other β=3 cells have γ=0.5 worse by 5 frames. γ=−0.5 is worse in 6/6 (at β=3 it nearly doubles FER). ⇒ **of the four measured γ, entropy-proportional is the lowest in 5 of 6 cells and tied in the sixth**; whether it is optimal over the allocation *simplex* is untested (only a 1-D path was sampled). Native still beats `B-min` by **50.8×/180.8×/558×** at β=2 and **≥54×/≥107×/≥180×** at β=3. So **“the measured allocations do not explain the gap”** is now measured — not “the allocation rule is ruled out”, and not “eprop is the family optimum” | `[F]` | `a1g_allocation_family.json:cells` (per-γ FER, `m`, `beta_k_realised`), `feasibility_table`, `anchor_checks`; `a1g_operator_run.log` |
| F3b | **Protocol caveat**: A1f used `max_iter=40`, A1 used 60 (a default parameter, recorded in **no** JSON). Native column is systematically worse; headline recomputed on A1f's numbers is **42×/155×/279×**. Binary arm is iteration-insensitive (307→307 etc.), so the direction holds | `[F]` | `a1f_rate_levelling_control.py:71`; `FINDINGS.md` §7.9 protocol note |
| F3c | **Mechanism: both single-plane narratives withdrawn.** At β=3 the *quiet* high-rate planes fail 19–25 % while the noisiest fails 1.8 % (first-fail 49 % vs 3 %); at β=2 no plane dominates (40–52 % each). What binds is each plane's **code rate** under dv=3/n=256 | `[F]` (reviewer-supplied attribution, reproducible) | `FINDINGS.md` §7.9 mechanism table; `EXPLORATION_LOG.md` Entry 13 |
| F3d | **Difficulty asymmetry disclosed**: levelling matches nominal rate, not difficulty. q=16/β=2: native margin to joint capacity 14.5 % vs levelled noisiest-plane margin 2.5 % (~6×) | `[D]` | `FINDINGS.md` §7.9 asymmetry note |
| F4 | the permitted statement (superseded by F3a; current wording in `FINDINGS.md` §7.7 quote block and §7.10): "*at matched disclosure — and at matched nominal code rate in the 8 of 16 cells where levelling is feasible — the native GF(q) construction reaches far lower FER than r independent per-plane binary codes of the same random-regular ensemble at finite length*" — **not** "native is informationally superior", **not** "the binary family is bad", **not** "the allocation explanation is ruled out in general" | `[decision]` | `FINDINGS.md` §7.7 quote block, §7.9, §7.10 |

## Part G — C-2 gate ruling

| id | claim | tag | evidence |
|---|---|---|---|
| G1 | the gate demanding `FER = 0` for both arms came with the operator packet, not `PREREG_AND_AUTH.md` | `[F]` | `FINDINGS.md` §7.5 |
| G2 | binary-arm C-2 is **UNATTAINABLE-BY-CONSTRUCTION at frozen dv=3** and is recorded as FAIL | `[decision]` | `FINDINGS.md` §7.5; `EXPLORATION_LOG.md` Entry 9.5 |
| G3 | it is superseded — **not relaxed** — by the ML arbitration, which is "complementary and more direct for decoder correctness" and **not** generally stronger (it runs at binary n≤16 / q-ary n≤8 and does not cover n=256, which still rests on C-1/C-3/C-4, the rate monotonicity and `undetected≈0`) | `[decision]` | `FINDINGS.md` §7.5; `EXPLORATION_LOG.md` Entry 12.5 |
| G4 | per-plane binary failure rate is monotone in code rate (plane 0 rate 0.305 → ~0–1 %; plane 4 rate 0.922 → ~15–18 %), `undetected≈0`, insensitive to MAX_ITER 30→150 ⇒ genuine dv=3 threshold effect, not a decoder bug | `[3P]` operator measurement | `a1_notes.md` (citable for §7.4 **only**); `FINDINGS.md` §7.4 |
| G5 | replacing a failed gate is a threshold change outside the literal "one repair+rerun with unchanged thresholds" allowance; the ruling rests on the listed mitigations, recorded as such | `[decision]` | `FINDINGS.md` §7.5 mitigations block |

## Part H — Corrections ledger (what this packet got wrong, and where it says so)

| id | item | status | record |
|---|---|---|---|
| H1 | "binary Cascade already ruled out here" | `[R]` | `EXPLORATION_LOG.md` Entry 2.1; correct pointers `docs/group-meeting-ir-analysis-20260615.md:278`, `docs/expanded-real-ir-evidence-20260615.md:83,198`, `docs/decision-log.md:4435` |
| H2 | "(S) dead ⇒ dimension reduction has no gain" (causal) | `[R]` | Entry 2.1; `docs/decision-log.md:4436` is the G8 brief's own gate |
| H3 | "native FER=1.0 ⇒ FFT-QSPA wrong" | `[R]` | Entry 6; β=1 is genuinely beyond threshold |
| H4 | "β∈{5,8,12} infeasible" | `[R]`→ corrected | Entry 6/10; `m>n` is a valid over-determined matrix — those points are **degenerate** (rate negative), not impossible |
| H5 | "both arms reach FER=0 trivially at β∈{5,8,12}" | `[R]` | Entry 10 §B4; measured binary failures 21/81/180 at β=5, and native `degenerate=false` for all q |
| H6 | verdict token `binary_better`/`no_separation` inverted in both logs | `[R]`→corrected in code | `a1b_run.log`/`a1c_run.log` banner 1; `a1b_decoder_validation.py` and `a1c_screening.py` verdict logic fixed |
| H7 | three self-reports of done-but-not-done (Entry 8 "zero bytes"/"schema v3 all PASS"; Entry 10 "F2/F6 already applied"; Entry 11 "stale lines removed") | `[R]`→recorded, pattern named | Entry 10 §B3, Entry 11 §11.3, Entry 12 §12.2 |
| H8 | fallback rules cited as repo rules ("Retry Limits"/"Prohibited"/re-call ban) — **they do not exist in this repository** | `[R]` | Entry 10 §B3; reviewer grep-verified absence in on-disk `AGENTS.md`/memory/docs |
| H9 | main-thread takeover of implementation is a disclosed **deviation from AGENTS.md §4**, not an authorised exemption | `[decision]` | Entry 10 §B3 |
| H10 | headline lower bound 181× excluded the smallest prereg ratio (q=4) | `[R]`→corrected | Entry 12.3; `FINDINGS.md` §1.6/§7.6/§8.3 |
| H11 | `GF(4)` "not in pinned GF2m domain" used to justify dropping q=4 | `[R]` | Entry 11.2; cause was a probe calling `field.mul(3,5)`, out of range only for q=4; `nonbinary_v26_verify.py:324,329` runs GF(4) oracles |
| H12 | q=32 added beyond the prereg without advance authorisation | `[decision]` | Entry 11.2; corroborating-only, never preregistered |

## Part I — Superseded artifacts and citability

| artifact | status | note |
|---|---|---|
| `a1_sweep_run.log` | **NOT CITABLE** | y-blind era; prints `SELF-CHECK ALL PASS`, `C2_large_beta: PASS`, binary `FER=0.0000` |
| `SNAPSHOT_operator_version.py` | **NOT CITABLE** | snapshot of a contended, superseded implementation; evidence of the four-way overwrite only |
| `a1_synthetic_screening.py` | **NOT CITABLE** | gates did not pass before takeover; its `DEVIATION_D1` GF(4) justification is false |
| `a1b_authoritative.json` | **q=4 rows only** | overwritten by the a1d run writing the same filename; superseded by `a1_authoritative_merged.json`; its `part1/part2` arbiter arrays are now empty |
| `a1b_run.log`, `a1c_run.log` | citable with banners | primary records of the full `{8,16,32}` table; each carries two correction banners |
| `a1_notes.md` | citable for §7.4 **only** | backup operator's defect record + per-plane failure table |
| `a1_selfcheck.json` | citable as gate record | schema `v1`, `all_pass=false`, C-2 FAIL |
| `step0_fline.*`, `effective_alphabet.*` | citable | reproducible read-only derivations |
| `a1b_decoder_validation.py`, `a1c_screening.py`, `a1d_q4.py`, `a1e_consolidate.py` | citable as scripts | self-contained; no import of any contended implementation |
| `a1f_rate_levelling_control.py` + `.json` | **pending** | the decisive control; result not yet in |

## Part J — Q1 sibling handoff (delivered, blocked on one decision)

| id | claim | tag | evidence |
|---|---|---|---|
| J1 | verdict **A** (closed-form scalar cap) with arithmetic re-derived here and matching exactly: `N·H=26765.355267304014`, `1.3·N·H=34794.96184749522`, `K_max=6946`, `cap=34794`, actual 34119, margin 675 bits = 135 GF(32) symbols, `f_actual=1.2747449`, `f_cap=1.2999641` | `[D]` arithmetic on `[3P]` constants | `Q1_CAP_HANDOFF.md` §0; `EXPLORATION_LOG.md` Entry 1 |
| J2 | **the constants are `[3P]`**: `git grep "0.8168138204133305"` in tracked files returns no match; memory cites them 0/0/0 | `[3P]` | `EXPLORATION_LOG.md` Entry 1 provenance note; memory CORRECTION blocks |
| J3 | the adjudication rested on the superseded "Stage-3 is read-only post-processing" premise; two clauses must be rewritten before freeze (replacement text supplied) | `[F]` about the premise change | `Q1_CAP_HANDOFF.md` §1–2; `EXPLORATION_LOG.md` Entry 1 |
| J4 | the one decision needed from the sibling: are the three arms' `K` values mutually distinct? Recommendation: yes | `[decision]` | `Q1_CAP_HANDOFF.md` §2 |

## Part K — Repository hygiene, verified

| id | claim | evidence |
|---|---|---|
| K1 | `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/`, `openspec/` **never written** | `git status --porcelain` — no entries under any of them |
| K2 | the only tracked modification across the whole packet is `AGENT_PROJECT_MEMORY.md` (additive appends only) | `git status --porcelain \| grep -v '^??'` |
| K3 | all packet writes are additive under `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/` and `workspace/s01_dimension_probe_20260923/` | `git status --porcelain \| grep '^??'` |
| K4 | no commit, no push, no branch operation | `git status` untracked/modified only |
| K5 | `claim_ceiling` present in all **seven** JSON artifacts (`step0_fline`, `effective_alphabet`, `a1_selfcheck`, `a1b_authoritative`, `a1_authoritative_merged`, `a1f_rate_levelling_control`, `a1g_allocation_family`) and in every narrative location | `grep claim_ceiling workspace/s01_dimension_probe_20260923/*.json` |
| K6 | batch evidence **not promoted**; promotion is a main-thread acceptance decision, verified at string level | `EXPLORATION_LOG.md` Entry 11 §11.7, Entry 12 §12.6 |

---

## Status at a glance

| part | settled? |
|---|---|
| A channel structure | ✅ |
| B effective alphabet | ✅ |
| C V13 R3 single-pass identity | ✅ (as a retraction) |
| D decoder arbitration | ✅ |
| E A1 screening | ✅ |
| **F mechanism / rate-levelling control** | ✅ A1f (§7.9) + A1g (§7.10); **“measured allocations do not explain the gap” established for the sampled power-law path / grid / ensemble. Optimality over the allocation simplex NOT established.** |
| G C-2 gate ruling | ✅ (recorded as a deviation) |
| H corrections ledger | ✅ (three still-open rewordings noted in Entry 12) |
| I artifact citability | ✅ |
| J Q1 handoff | ✅ delivered, blocked on the sibling's decision |
| K hygiene | ✅ |

**F3a has returned. What it establishes, scoped to the four-point power-law path on this grid, is the NEGATIVE claim only: no measured allocation explains the gap. It does NOT establish that entropy-proportional allocation is optimal over the allocation simplex** (§7.10): entropy-proportional
allocation is the family optimum, and native still beats the family minimum by 50.8–558×
(β=2) and ≥54–180× (β=3). F3b/F3c/F3d keep the protocol, mechanism and difficulty caveats
that F3 forced onto the record. What remains open is scope, not the mechanism: r ≤ 5,
a single `dv=3` random-regular ensemble, `n=256`, `β ≤ 3`, and the `q ≥ 64` high-rate
quiet-plane cells were never run.

| R1 | **faithful headline conclusion** (Entry 22 §22.1): measured native GF(4/8/16) vs r independent per-plane binary codes, same `n=256`, same nominal disclosure, `max_iter=60`, both arms' own `dv=3` random-regular construction, both decoders in the sum-product-BP family; β=2.0 frame-FER ratios **50.8×/180.8×/558×** from integer failure counts | `[F]` | `a1_authoritative_merged.json:ratio_at_beta_2`; `FINDINGS.md` §0 |
| R2 | **r=10 strong-binary control, separate grid point**: reference `codebook_v4` 102/1200 @ D=584 vs native GF(32)×GF(32) split 2/1200 @ D=580 (51×), wall ≈2.1 s vs ≈19.4 s per 1200 frames. **Not merged** into the GF(4/8/16) series — different grouping scheme and a ≈9× wall ratio in the native arm's disfavour | `[F]` | `a1h_strong_binary.json:cells.codebook_r10_c0_it60` and `cells.native_r10_split_d580`; `EXPLORATION_LOG.md` Entry 22 §22.2 |
| R3 | **ε_bin arm WITHDRAWN before running**: replacing SPA with min-sum measures a decoder-algorithm *variant*, not a same-family implementation difference, so it cannot bound A1's implementation error; it is not a prerequisite of R1 | `[decision]` | `EXPLORATION_LOG.md` Entry 22 §22.3 |

## Status at a glance — PACKET CLOSED FOR ARCHIVE (EXPLORE, `diagnostic_only`)

| part | status |
|---|---|
| A channel structure | ✅ archived |
| B effective alphabet | ✅ archived (as a complexity-formula ratio; "lossless" withdrawn, Entry 16) |
| C V13 R3 single-pass identity | ✅ archived (as a retraction, Entry 10) |
| D decoder arbitration | ✅ archived |
| E A1 screening | ✅ archived with the family/implementation qualifier |
| F mechanism / allocation | ✅ closed as a *scoped negative claim* (Entry 19); simplex optimality NOT established |
| G C-2 gate ruling | ✅ archived (recorded deviation) |
| H corrections ledger | ✅ archived — 22 entries, 7 substantive self-retractions |
| I artifact citability | ✅ archived |
| J Q1 handoff | ✅ delivered to the sibling; blocked on the sibling's three-arm `K` decision |
| K hygiene | ✅ archived |
| R1–R3 final claims | ✅ Entry 22 |

**What this packet does NOT establish** (carried forward, not deleted): any general
dimensionality advantage; any information-theoretic advantage; the alphabet-only share of the
FER gap; any real-data FER, efficiency, leakage or SKR; allocation optimality over the
simplex; the quiet planes at `q ≥ 64` as a systematic sweep; and the `q ≥ 64` cells as
anything but single grid points. Promotion recorded in `EXPLORATION_LOG.md` Entry 22 §22.5;
the batch-end review is that entry plus four independent reviews.
