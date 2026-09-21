# R1 Histogram Re-run — Main-Thread Acceptance (Acceptance ID G-R1)

- Date (UTC): 2026-09-21. Track: **DECIDE**. Gate: **main-thread acceptance** (AGENTS.md §10.3, final step of the DECIDE chain).
- Acceptance delegation: the main thread delegated this acceptance to the orchestrator under the 2026-09-21 conversation-grant instruction (this-cycle mode; the §7/§8 signature blocks remain intentionally blank; the paperwork deviation was ratified administratively post-Pre-RESULT per the P3-A1-REVIEW F-3 precedent — recorded in the prereg amendment notes).
- Chain of record: `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` (authorization of record) → `workspace/r1_histogram_5e2a91c4/PRE_EXECUTE.md` (Q0–Q6) → `workspace/r1_histogram_5e2a91c4/R1_RESULT.md` (result record) → `R1_PRERESULT_REVIEW.md` (independent Pre-RESULT: PASS_WITH_FINDINGS, no blocking findings) → this acceptance.
- Evidence root: `workspace/r1_histogram_5e2a91c4/` (18 files; gitignored, retained locally per invariant I6; provenance/seeds/commands/wall/RSS in `PRE_EXECUTE.md`/`R1_RESULT.md`/`telemetry.json`; the sparse `N_ab`/`p_b` artifacts are the X1 bundle inputs).

## Accepted scope (ONLY — packet §6 claim ceiling)

Corrected per-source design points + materialized channel-bundle inputs. NO FER/SKR/route/qualification/publication claim. The corrected design points do NOT authorize X1 (X1 needs its own entry gate).

## Accepted results (summary; authoritative table = the 2026-09-21 baseline amendment + review §§3–4)

- Estimator defect CLOSED: `K_B_train = 1024` (full B support) measured on all three sources; `H_corr = H_plug + (K_AB−K_B)/(2·N_train·ln2)` = 0.8012690084416184 / 0.8272902027770036 / 0.8333327179427281 (Δ vs defective basis −0.0023389196758668573 / −0.0016714841284448667 / −0.0012518869160380586, saturating the pre-registered bound); defective `H_MM_old` persisted alongside for audit; determinism vs A1 exact on 12 fields.
- Movements: 1M m_max 201→200; 1.5M m_max 207 unchanged; 2M raw 209→cap 208 unchanged; f@208 = 1.34552190 (1M OUT) / 1.30320049 (1.5M nominal OUT) / 1.29375096 (2M IN on f-margin).
- Certifiability on key-eligible 200/276/364 (zero-failure still required): 1M NO everywhere (m_max 200: N=4447; m=199: 1541); 1.5M NO everywhere (m_max 207: 5315; m=200: 327; m=199: 288) — the defective-basis "YES-by-2-blocks PROVISIONAL" at m=199 FLIPS to NO; 2M m=200/199 YES-on-count (271/244 ≤ 364), m=208 f-IN but NOT count-certifiable (2298 > 364).
- 2M consistency vs frozen `gamma_f03.npz` lineage: no FINDING (ΔH_L1/L2 −0.000632/−0.000523; p_b L_inf 0.000197; ΔN +29589 expected vintage).
- Budgets: trio wall 531.1 s ≤ 5400; peak RSS 0.68 GiB < 4 GiB; 0 decoder/DE/graph calls; no repair path used.

## Label confirmations

- **1.5M@208**: OUT on the frozen point-estimate gate (b) (f = 1.30320049 > 1.3), with the statistical caveat retained (threshold-H gap vs CI halfwidth = 0.92 ⇒ INDETERMINATE-vs-OUT; any in-box reading remains unproven). CONFIRMED by the main thread.
- Pre-RESULT findings F1/F3 are closed by additive correction notes appended to the evidence-root documents at this acceptance (no re-run).

## Closed / not authorized

- CLOSED: estimator defect (open item a); X1 bundle-materialization entry blocker (open item b, with the standing caveat that X1's 15 arms require their own entry gate); baseline §0.2 placeholders P-V1 (MM estimand) and P-V2 (f_eff slope).
- NOT authorized by this acceptance: any X1 arm; any `.ttbin` read; any FER/SKR/route/qualification/publication claim; a standing conversation-grant mode (that would be an AGENTS.md/OpenSpec workflow change).

**Verdict: G-R1 ACCEPTED (main thread), scope-limited as above.**
