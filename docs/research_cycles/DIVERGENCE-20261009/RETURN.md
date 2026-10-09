# Divergence return — external IR questions assessed in-repo (2026-10-09)

Inputs: 3 external outputs (DeepSeek "distributed source coding", GLM "classical optical receiver",
ChatGPT "finite-blocklength coding"). Docs-only; no execution, no new packet. Prompt:
`docs/prompts/DIVERGENCE_RETURN_20261009_PROMPT.md`. Table changes: `docs/NOW.md` (rows F, G added; A, E tombstoned).

## 1. Classification (merged by mechanism)

| ID | Mechanism | External sources | Class | Disposition |
|---|---|---|---|---|
| I-1 | Soft fine-time LLR into decoder; is H(A\|B_fine)≈0.2 the right yardstick | DS-Q3, GLM-Q2, GPT-A | I | Already mainline (old row A). Residual: yardstick vs sub-bin count, out-of-sample log-loss |
| I-2 | Sign of e predictable from fine position | GLM-Q4 (direction part) | I | Confirmed by S-4a S-curve; used in S-4d fine prior |
| I-3 | Mixture/wide tail, hidden state, LLR mismatch | GPT-C, GLM-Q4 (tail part) | I | Row D (enriched); hidden-state/burst part refuted by existing stats |
| I-4 | Finite-blocklength information spectrum / dispersion | DS-Q2, GPT-D | I* | New row F (*see anchoring note 5) |
| I-5 | Sparse support + direction; Gray/Lee/nonbinary representation | GPT-B, GLM-Q1 (representation) | I | Already mainline (R15 LSB+sign = support+direction, G1=1.0 exact). Residual: exact small-block MAP vs BP gap |
| I-6 | Rate-adaptive / blind / incremental / inter-batch Δ tracking | DS-Q6, GPT-E, GLM-Q1 (rate), GLM-Q3a | I | Merged into old row E, tombstoned (weakest evidence) |
| I-7 | Bob publishes A-independent reliability → Alice-side layered/targeted disclosure; message-type accounting | GLM-Q3b, GLM-Q7, GLM-Q8, GPT-G (mask cost) | I | New row G + DECIDE question |
| I-8 | Selective discard; target U=g(A); "equivalence-class" reconciliation | DS-Q4, DS-Q5, GLM-Q6, GPT-F, GPT-G | I | Refuted asymptotically by arithmetic (below); residual only via FER/yield |
| I-9 | List decoding + hash selection | GPT-H | I | Not in table (scored below) |
| I-10 | Reconciliation direction (who converges to whom) | GLM-Q7 (direction part) | I | Not in table; Δ symmetric → H(B\|A,u)≈H(A\|B,v) expected |
| II-1 | Physical origin / per-detector asymmetry of the 1–2 % wide component | GLM-Q4, GLM appendix 11, GPT-C (origin) | II | Needs a timing-reference capture; IR payoff only via row D |
| III | Joint quantizer / bw–d / non-uniform bins (DS-Q1, GLM-Q5 bw part); mask/helper security value (GLM-Q7); finite-key; pairing/sync errors (GLM appx 3); latency/real-time (GLM appx 9); PA interface (DS-Q5); certifying very low FER (GPT appx 9, already repo policy) | — | III | Listed only |

I-8 refutation (zero cost): total net information Σ_i I(A_i;Y_i) has non-negative terms, so dropping symbols
selected on Bob's data cannot raise it; for deterministic U=g(A), I(U;Y) ≤ I(A;Y) (data processing).
At d=1024 a dropped symbol costs ≥ log₂1024 − log₂3 ≈ 8.4 bit of retained entropy vs ≤ 1.6 bit saved leakage.
"Equivalence class" = SW coset coding already; key extraction needs identical strings. Only FER/yield effects
remain (C, G).

## 2. Literature (sciverse-retrieved; DOIs as returned)

| Direction | Paper | Solved | Not solved (for us) |
|---|---|---|---|
| I-1/I-7 | Boutros & Soljanin 2023, TE-QKD SKR and IR coding, 10.1109/tcomm.2023.3302135 | Jitter-error channel model, SKR, standard short codes for time-bin IR | Mixture/heavy tail, calibration offset, two-level binary split |
| I-1 | Liveris, Xiong, Georghiades 2002, 10.1109/lcomm.2002.804244 | Syndrome LDPC SW near limit, binary side info | Continuous side info, short blocks |
| I-1 | Naito, Watanabe, Matsumoto, Uyematsu 2009, 10.1587/transfun.e92.a.525 | Soft decision beats hard in Gaussian Maurer model (key rate bound) | Coded FER at n≈4096, non-Gaussian |
| I-5 | Zhou, Wang, Wornell 2013, layered schemes large-alphabet SKD, 10.1109/ita.2013.6502993 | Bit-layer split of large-alphabet symbols, limited-magnitude-error channels | Fine-time soft info, calibrated sign asymmetry |
| I-4 | Polyanskiy, Poor, Verdú 2010, 10.1109/tit.2010.2043769 | Normal approximation C−√(V/n)Q⁻¹(ε) | SW with continuous side info |
| I-4 | Tan & Kosut 2014, 10.1109/tit.2013.2291231 | SW entropy dispersion, second-order region | Our mixture P(A\|Y) numbers |
| I-4 | Nomura & Han 2014, 10.1109/tit.2014.2339231 | Second-order SW for mixed sources | Practical code gap vs bound |
| I-4 | Jose & Kulkarni 2019, 10.1109/tit.2018.2873623 | Tighter finite-blocklength SW converse (LP) | Numerical value for our channel |
| I-4 | Shakiba-Herfeh & Chorti 2021, 10.1109/ssp49050.2021.9513785 | Empirical short-block SW code comparison for key reconciliation | Soft time side info |
| I-6 | Elkouss, Martínez-Mateo, Martín 2011, 10.26421/qic11.3-4-3 | Rate-adaptive LDPC reconciliation | Whether our segments drift enough to need it |
| I-6 | Kiktenko et al. 2017, symmetric blind, 10.1103/physrevapplied.8.044017 | Blind (no prior QBER) LDPC IR with reduced interactivity | Two-level LSB+sign structure |
| I-6 | Borisov, Petrov, Tayduganov 2022, 10.3390/e25010031 | Asymmetric adaptive LDPC IR on industrial QKD | Short 3 s/10 s captures |
| I-7 | Origlia, Parente, Secondini 2026, 10.1109/tcomm.2026.3693195 (arXiv 10.48550/arxiv.2510.10674) | Bob discloses a soft metric that leaks no key information; LDPC-coded gain | Time-bin channel; whether repo leakage accounting counts such messages |
| I-7 | Origlia, Cil, Schmalen, Secondini 2026, 10.48550/arxiv.2603.23585 | Same scheme at ultra-low SNR | Same |
| I-7 | Daneshgaran & Mondin 2019, 10.1088/1742-6596/1206/1/012012 | Unequal error protection by reliability (magnitude) approaches MI | Discrete time-bin, plaintext/coded split |
| I-7/I-6 | Brassard & Salvail 1994, Cascade, 10.1007/3-540-48285-7_35 | Interactive binary reconciliation | Reliability-targeted disclosure |
| I-8 | Maurer 1993, 10.1109/18.256484 | Secret-key agreement by public discussion, advantage distillation | IR-only accounting (security out of scope) |
| I-9 | Tal & Vardy 2011, 10.1109/isit.2011.6033904 | SC list decoding ≈ ML | Syndrome source decoding with continuous side info |
| I-9 | Lee, Park, Heo 2018, 10.26421/qic18.9-10-5 | CRC-aided SCL for QKD reconciliation (virtual string) | Our channel; repo is LDPC/BP line |
| I-9 | Kiktenko, Malyshev, Fedorov 2021, 10.1109/lcomm.2020.3021142 | Blind polar reconciliation | Same |

External citations not retrieved here (e.g. Wyner–Ziv 1976, Slepian–Wolf 1973, Orlitsky–Roche, Minsky set
reconciliation, Witsenhausen) are left unverified and not cited.

## 3. Scores (0–10; weights 30/25/20/15/10; "未知" = no number)

Class I (* = normalised over the known 90 % of weight; long-term unknown)

| ID | Importance 30 | Novelty 25 | Feasibility 20 | Verifiability 15 | Long-term 10 | Weighted |
|---|---|---|---|---|---|---|
| G | 7 — targets the open C bottleneck (soft point at its own rate) | 6 — Origlia/UEP exist, not for time-bin LSB+sign | 9 — first check is arithmetic on A5 table | 8 — single threshold 0.02 bit/pair | 未知 | 7.3* |
| F | 7 — decides whether gap 0.18 is code loss or a floor | 4 — dispersion theory is textbook | 9 — closed form + A5 model | 9 — threshold 0.05/0.1 | 5 — reusable floor for every operating point | 6.8 |
| D | 6 — U=6–44/source shows tail reaches real chain | 4 — mismatch robustness is standard | 8 — synthetic paired FER | 8 — McNemar paired | 未知 | 6.2* |
| I-9 | 4 — hash cost ~32/4096 small, gain unknown | 3 — CRC-aided SCL in QKD exists | 7 — OSD list already in A6 stack | 7 — list coverage measurable | 未知 | 4.9* |
| I-5 residual | 3 — exact MAP vs BP only on n=32/64 | 3 | 8 | 7 | 未知 | 4.8* |
| I-6 (tombstone E) | 3 — no drift/burst evidence | 2 | 9 | 8 | 未知 | 4.9* |
| I-10 | 2 — symmetry predicts no gain | 3 | 8 | 7 | 未知 | 4.4* |
| I-8 | 1 — refuted by arithmetic | 5 — reframing is genuinely different | 10 | 10 | 未知 | 5.6* (refuted) |

Class II

| ID | Importance | Novelty | Feasibility | Verifiability | Long-term | Weighted |
|---|---|---|---|---|---|---|
| II-1 | 4 — IR payoff only via LLR shape (row D) | 未知 | 5 — needs a timing-reference capture | 6 — one-sided vs two-sided tail is a clean readout | 未知 | n/a |

Hint (推测, not evidence): B1 quantiles around the mean are skewed the same way (+) for both μ signs
(T2-1M −44/+49, T2-1.5M −47.5/+53.5), consistent with a one-sided detector tail.

## 4. DECIDE question for the user

Does a Bob→Alice public message that is (near-)independent of A — e.g. Bob's fine-position sub-bin index —
count as reconciliation leakage? Row G's value depends on it; the current repo accounting counts L_A+L_B+R
(Alice→Bob). Not changed here.

## 5. Anchoring traces (self-reported)

1. DS-Q1/GLM-Q5 (joint quantizer, grid phase): sent to III by the NOW.md bw/d scope rule, not on merit; the
   phase part was mapped to existing calibration (C-0).
2. GPT-B sparse support: first reaction "already mainline"; the identity is exact (G1=1.0), but the residual
   (exact MAP vs BP at short n) was nearly dropped — kept as I-5 residual.
3. Selective discard: first reaction "= coincidence-window postselection, out of scope"; replaced by explicit
   arithmetic.
4. Row G: first read as "the level-B plaintext fallback"; it differs (Alice-side knowledge from A-independent
   public info, applies at level A).
5. Row F: the word "有限长度" in the scope exclusion nearly sent it to III; kept in I because it is a coding-rate
   question, not finite-key security. If the user meant to exclude it, move it to III.
6. Row E tombstoned partly because mainline calibration already handles drift — push-back calc retained.
7. I-9 scored low partly because this checkout is the LDPC/BP line (SCL lives in the sibling Polar checkout).
