# Cross-Repo Polar vs LDPC Reconciliation Comparison — 2026-09-27 (read-only)

- Repos read (READ-ONLY, nothing modified in either):
  `/mnt/d/Code/HD-QKD_Polar_Release`, `/mnt/d/Code/qkd-reconciliation-lab`
- Single write allowed by the task: this report, plus one `docs/decision-log.md`
  append entry. No commit/push, no pipeline execution in either audited repo.
  The Polar re-run discussed below was executed **in the lab**, not here, and is
  reported as that repo's own result.
- Method: read the cited files verbatim, then `diff` and `grep` to test each
  claim. Numbers attributed to the lab are quoted from its result JSONs.

## Verdict table

| Claim | Verdict | One-line evidence |
|---|---|---|
| V1 — the lab's Polar is an independent implementation of the sibling's Polar | **REFUTED** — byte-identical copy of `low_dim_opt/core/*.py` | `diff -q` returns clean for 6/7 modules; only `ttbin_io.py` differs (+18 doc lines, +6 Swabian SDK path) and `verification.py` is a copy of `src/reconciliation/verification.py` |
| V2 — the lab's Polar numbers validate the sibling's Polar | **REFUTED as validation** (same code, different config *and* different data) — see §2 | `qkd-recon/polar_core.py` == `low_dim_opt/core/polar_core.py`, 430 lines each |
| V3 — the lab's Polar runner is weaker than the sibling's production config | **CONFIRMED** — 5 concrete gaps | §2 table; `low_dim_opt/README.md` §2 vs `experiments/.../polar_run.py:59-68` |
| V4 — raising Polar to SCL L=8 changes the comparison outcome | **CONFIRMED, and it falsifies a lab design assumption** | v3 → v4 mean β diff at bw40: +0.035 → **+0.0535**; `polar_run.py` docstring claim now retracted |
| V5 — "LDPC v5 is the best method" | **REFUTED — no single winner** | crossover by bandwidth: Polar leads bw≤60 (6/6 points), LDPC leads bw≥200 (6/6, 7/7) |
| V6 — the sibling's `comparison_bench` can rank any of these methods | **REFUTED — metric-definition artefact** | `metrics/leakage.py:19` uses `n·H2(mean plane BER)` as the budget; all 1220 shipped rows score 0.0 |
| V7 — LDPC v5's headline β 0.87–0.91 is a real-data number | **REFUTED — calibration data** | lab `docs/realdata-ttbin-v5-report.md` §4: real d1024 bw300 gives β 0.72 / f_EC 2.92; d≤32 has **no** full-frame success point |
| V8 — consistency check with this repo's "Polar f≤1.3 wall vs LDPC dc≤13" diagnosis | **DIRECTIONALLY CONSISTENT, but not same-data and not same denominator** | §5 |

## V1/V2 — the Polar algorithm exists once, not twice

`diff -q` between `qkd-reconciliation-lab/src/qkd_recon/` and
`/mnt/d/Code/HD-QKD_Polar_Release/low_dim_opt/core/` (2026-09-27):

```
IDENTICAL  polar_core.py         (430 lines)
IDENTICAL  msd_conditional.py    (555)
IDENTICAL  rate_allocation.py    (536)
IDENTICAL  leak_accounting.py    (355)
IDENTICAL  channel_models.py     (244)
IDENTICAL  de_frozen.py          (186)
```

`qkd_recon/ttbin_io.py` differs only by 18 documentation lines about the
`.ttbin` / `.1.ttbin` header-vs-event-stream split and 6 lines inserting the
Swabian Time Tagger SDK driver path into `sys.path` — additive,
non-algorithmic. `qkd_recon/verification.py` is a copy of
`HD-QKD_Polar_Release/src/reconciliation/verification.py`, not of a
`low_dim_opt/core/` file.

**Consequence for this repo.** Any Polar efficiency number produced by the lab
is *this repo's* Polar algorithm wearing a different configuration. It is
**not** an independent reproduction, must never be cited as one, and cannot be
used to argue that the sibling's Polar is confirmed by a second codebase.

## V3 — same code, weaker configuration

| Aspect | Sibling production (`low_dim_opt`) | Lab `polar_run.py` (v3 and v4) |
|---|---|---|
| Frozen-set order | DE, or O1b-2 dual-order joint `(order, k)` | 3GPP PW only — `P.reliable_order(n)` (`polar_run.py:132`) |
| List size | SCL **L=8** | L=1 (v3) → L=8 (v4) |
| Rate ladder | `--ladder o1b2`: dual-order FER curve, joint allocation, Jeffreys p, PAVA isotonic | hand-inlined; point rule `errs == 0 or errs/n_alive <= 1/24` (`polar_run.py:179`) |
| Incremental disclosure | `--incremental` (O4-R, adopted 2026-09-16) | none |
| FER estimation split | `--pool-oos` (out-of-sample pool) | ladder scored on the **test** frames themselves |

Note the last row: the lab's FER ladder is evaluated on the same frames used
for the reported test metric, i.e. a design/test circularity the sibling
removed with `--pool-oos`. That is consistent with the sibling's own recorded
concern about winner's-curse in `low_dim_opt/simulation/o1_ladder.py:12-22`.

**Therefore the crossover in §4 is a lower bound on the Polar side.** If the
lab's Polar were run at the sibling's production configuration, Polar's
low-bandwidth advantage would grow and the crossover would move further
right. Do not read the reported crossover as the best achievable split.

## V4 — L=1 → L=8, and a retracted design assumption

The lab's v3 runner defaulted to plain SC on the documented claim
(`polar_run.py`, pre-edit) that *"the FER<=1/24 operating rate is identical for
SC (L=1) and SCL-8 (rare worst frames dominate)"*. That claim is **false** in
the noisy regime. Measured by the lab on 2026-09-27 across its own 43-point
matrix, with the L=1 re-run verified to reproduce the shipped v3 JSON
bit-for-bit (`beta_eff=0.9060999599774935`, `f_ec_test=3.0074964378947993` at
d=1024/bw=300) so the delta is attributable to the list size alone:

| bw | mean β diff (Polar−LDPC) v3 → v4 | mean Δβ (L8−L1) | points better / same / worse |
|---|---|---|---|
| 40 | +0.035 → **+0.0535** | **+0.0188** | — |
| 50 | +0.032 → **+0.0411** | +0.0091 | — |
| 60 | +0.008 → **+0.0226** | +0.0146 | — |
| 80 | −0.004 → −0.0021 | +0.0016 | — |
| 100 | −0.004 → −0.0009 | +0.0032 | — |
| 200 | −0.040 → −0.0397 | −0.0001 | — |
| 300 | −0.032 → −0.0320 | **+0.0000** | — |
| all 43 | — | +0.0066 | **30 / 11 / 2** |

The two regressions (d=32/bw80 −0.0048, d=32/bw200 −0.0044) are **rate-ladder
quantisation, not decoder regression**: at d=32 there are only 5 planes and the
step is `0.02 × 16384 = 328` bits; the two configurations' per-plane `k` sums
differ by exactly 328. Same class of effect as the quantisation loss already
recorded in the lab's v3 report §5.3.

Cross-checks that held: `|i_AB_polar − i_AB_ldpc| = 0.000e+00` at all 43
points; 0 planes fully disclosed; FER unchanged (Polar 43/43 at 23/24, LDPC
41/43 at 24/24).

**The lab's v4 is NOT independently reviewed.** v3 passed two review rounds
(860 metric fields recomputed, zero difference). A configuration change
invalidates that verdict. Do not cite v4 numbers in a paper or a route
decision without re-running the same review specification.

## V5 — there is no single winner

The lab's decision table, v4 (Polar `--list 8`):

| bw | verdict | Polar leads >0.01 | LDPC leads >0.01 |
|---|---|---|---|
| 40 / 50 | **Polar** | 6/6, 6/6 | 0/6, 0/6 |
| 60 | **Polar** (was "crossover") | 4/6 | 0/6 |
| 80 / 100 | tie | 1/6, 0/6 | 2/6, 1/6 |
| 200 / 300 | **LDPC** | 0/6, 0/7 | 6/6, 7/7 |

Best observed: LDPC `beta_eff` **0.94843** (d4096/bw300); Polar **0.91943**
(same point). Worst: Polar 0.49772, LDPC 0.38753 (d32/bw40).

Mechanism per the lab's v3 §4: in the clean regime every bit-plane channel has
high and similar capacity, so a single global (joint-codeword) rate is near
optimal and BP approaches the Shannon bound; in the noisy regime per-plane MSD
lets each plane match its own conditional capacity (good plane at rate 0.85,
worst plane at 0.25) while a single global LDPC rate is dragged down by the
worst plane. **This is structural, not a tuning artifact** — the lab's review
verified the LDPC rate grid floor (0.40) was never reached (lowest selected
rate 0.55).

## V6 — the sibling's `comparison_bench` cannot be used for this ranking

`HD-QKD_Polar_Release/comparison_bench/src/comparison_bench/metrics/leakage.py:19`:

```python
h = _binary_entropy(float(raw_ber_or_ser))
return max(0.0, 1.0 - leak_bits / (n_input_bits * h))
```

The budget is `n_input_bits × H2(mean per-bit-plane BER)`. It is not the
measured `I_AB` and not `H(A|B) = H(A) − I_AB`. For MLC high-dimensional
channels the per-plane marginal BERs are unequal by orders of magnitude, so
their **mean** is dominated by the near-noiseless planes and the budget has no
physical meaning.

Worked demonstration on the lab's strongest point (d=1024, bw=300; per-plane
BER `[9e-5, 7e-5, 1.9e-4, 3.5e-4, 6.8e-4, 1.45e-3, 2.68e-3, 5.52e-3, 1.13e-2,
2.22e-2]`, mean 0.00444; `I_AB = 9.6954`, `H(A|B) = 0.3027` bits/symbol):

| Method | leak (bits/input bit) | `1 − leak/I_AB` | `beta_eff_empirical` |
|---|---|---|---|
| lab LDPC v5 | 0.0604 | **0.9378** | **0.0000** |
| lab Polar | 0.0910 | **0.9061** | **0.0000** |

Shipped evidence in the sibling: `beta_eff_empirical` is 0.0 in all
`ir_benchmark_results.csv` (4 rows), `cascade_param_sweep_results.csv` (320),
`layered_ldpc_param_sweep_results.csv` (480) and `qldpc_param_sweep_results.csv`
(416). Observed leak there is 0.53–1.03 disclosed bits **per input bit**, i.e.
the methods disclose more than the input contains.

Per `AGENTS.md` §5.5 `beta_eff_empirical` must stay derived from leakage and
error inputs — it is, and this is not a hand-filling defect. It is a
**denominator** defect. Fixing it changes documented schema semantics
(`AGENTS.md` §5.3) and therefore needs an OpenSpec change in the sibling
(`AGENTS.md` §3). Until then:

- **Do not rank any method by `beta_eff_empirical`.**
- **Do not place a `1 − leak/I_AB` number and a `1 − leak/(n·H2(ber))` number in
  the same table.** They are different quantities. This repo's existing
  discipline (`AGENTS.md` §5.5, "Leakage numbers are method-specific; only
  compare when decomposition semantics remain consistent") already forbids
  this; the concrete failure mode is now documented.

## V7 — LDPC v5's headline efficiency is a calibration number

| Setting | β_eff | f_EC | Source |
|---|---|---|---|
| 10 dB calibration, bw120/180/200, plane BER ≈0.008–0.012 | 0.875 / 0.912 / 0.912 | 1.18 / 1.17 / 1.25 | `results/v5_qc_e1_40960_efficiency.json` |
| Real Type2PPLN d1024 bw300 | **0.72** | **2.92** | `docs/realdata-ttbin-v5-report.md` §4.2 |
| Real Type2PPLN d1024 bw100 | **0.53** | 2.61 | same |
| Real Type2PPLN d ≤ 32 | **no full-frame success point** | — | `docs/realdata-ttbin-v5-report.md` §4.1 |

The lab's own `docs/README.md` §6 records **0.769 as the engineering ceiling
for the binary-LDPC line on real data**, and states explicitly that the E1
figures are not comparable because real data has a ~100× inter-plane BER spread
(0.001–0.145) against E1's near-uniform 0.008–0.012, so parity averaging is
structurally mismatched. Statistics are also thin: E1 had 8 joint blocks with
0 failures, one-sided 95 % block-FER upper bound ≈ 31 %; ≈300 clean blocks are
needed for FER < 1 %.

## V8 — relation to this repo's "Polar f≤1.3 wall vs LDPC dc≤13" diagnosis

`docs/decoder-improvement-plan-20260816.md` is built on that diagnosis. The
lab's v4 numbers are **directionally consistent** with it: at the clean end
(bw 200–300) LDPC's `f_EC` is 1.77–2.36 against Polar's 2.72–3.26, so LDPC
does sit closer to the Shannon bound exactly where the diagnosis says the gap
opens.

Three limits, none of them cosmetic:

1. **Not same-data.** The lab's matrix is `Type2PPLN_2026-01-07`; this repo's
   own comparison artifacts use different acquisitions. Directional agreement
   across different data is weak evidence.
2. **Not the same `f` definition.** This repo's `f =
   (syndrome_bits + disclosed_public_bits) / H_full`; the lab's `f_EC = leak /
   H(A|B)` with **measured** `H(A|B)`. On the lab's data **neither** line
   reaches `f ≤ 1.3` anywhere (best is Polar 1.396 at d32/bw40), so the lab
   cannot confirm the *threshold*, only the *ordering*.
3. **No composable-security content on either side.** Neither β nor f_EC
   includes an Eve term, so neither is a secure key rate and neither may be
   compared against this repo's `f`-based route gates as if it were.

The lab therefore **supports the direction** of the diagnosis and **does not
close** its target. V80 baseline planning should not treat the lab's numbers as
evidence that a Polar f ≤ 1.3 point exists or is reachable.

## Consequence summary

1. The lab's Polar result is this repo's Polar algorithm. Do not double-count
   it as independent confirmation (`AGENTS.md` §5.5 spirit; the lab's
   `V1/V2` verdicts).
2. Any future same-data Polar/LDPC/Cascade comparison in this repo should use
   `1 − leak/I_AB` and `leak / H(A|B)` as denominators, must state the
   denominator in the table header, and must not read
   `comparison_bench`'s `beta_eff_empirical`.
3. If a Polar arm is needed, it should be run at the sibling's production
   configuration (`--scl-list 8 --ladder o1b2 --incremental --pool-oos`,
   `low_dim_opt/README.md` §5), not at the lab's runner configuration.
4. Report FER with its confidence interval. At n=24, 0/24 has a 95 % one-sided
   upper bound of 0.138 and 1/24 spans [0.007, 0.202]; the lab's
   "LDPC is more reliable" is **not** statistically established, only "both
   meet the target".

## Pointers

- Lab v3 report (reviewed): `qkd-reconciliation-lab/experiments/polar_vs_ldpc_fair_2026-01-07/REPORT.md`
- Lab v4 report (SCL L=8, **not reviewed**): `.../v4_bestcfg/REPORT_v4.md`
- Lab LDPC v5 maturity review: `qkd-reconciliation-lab/docs/binary-ldpc-v5-maturity-review.md`
- Lab real-data LDPC ceiling: `qkd-reconciliation-lab/docs/realdata-ttbin-v5-report.md`
- Sibling Polar production config: `HD-QKD_Polar_Release/low_dim_opt/README.md` §2, §5
- Sibling comparison-layer method state: `HD-QKD_Polar_Release/docs/ir-method-comparison-state-20260615.md` §8
- This repo's existing sibling-audit precedent: `docs/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md`
- This repo's comparison gates: `docs/three-way-ir-comparison-plan-20260816.md`, `docs/V80_BASELINE_20260921.md`
