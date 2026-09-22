# S2b Experiment Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-S2B (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§6).
- Parents: defect review + fix review (PASS_WITH_FINDINGS) + accounting map + PROGRAM_PLAN §1.3/§S2. No science change beyond §2.
- Supersession: single arm S2b; old V1/V2 arms SUPERSEDED (raw failures retained as history in S2_FER_RESULT/V2_RESULT); SCF-01 closed by supersession (no V2 gate to adjudicate).

## 1. Arm + constructor (frozen)
- S2b = `construct_l2(seed=2026092001)` on FIXED v10_peg (unreachable-first + correct girth + trials semantics); λ={2:1} UNCHANGED (L2_LAMBDA frozen).
- Verified values: four_cycles=0, min_girth=6, rank 47, deterministic. Pre-EXECUTE MUST assert `four_cycles==0`, else STOP (replaces old 1158 assert); record min_girth/rank.
- No V2/fallback arm; no re-seed; no constructor tuning. Banned-family refusal unchanged.

## 2. Channel/prior decision (frozen: Option B ONLY)
- B = entropy-matched QSC: solve H_qsc(p*)=0.80690067 with H_qsc(p)=h2(p)+p·log2(31), log2(31)=4.954196.
- Arithmetic: p=0.081 → h2=0.40569, p·log2(31)=0.40129, H=0.80698 (Δ+7.5e-5 vs anchor). Freeze p*=0.081, H_channel=0.80698.
- Sampler AND prior both at p*: `qsc_pair_sampler(p=0.081)` + `decode_error_domain(qber=0.081)`; max_iter=300 unchanged. Channel-prior self-consistent by construction.
- A deferred (NOT in this packet): kernel `decode_fftqspa` already takes (n,q) priors, so prior pass-through alone is small — BUT no empirical (alice,bob) pair sampler exists (S1 samplers return (n,32)/(n,1024) posteriors, (n,rng) signature vs campaign (rng,n)->pairs); defining Bob's GF32 observation from (B,u1) is a science-input decision → separate exploration, never snuck in here.
- Limitation (stated): B matches INFORMATION AMOUNT (H equal, entropy-anchored S1→S2) + channel-prior match, NOT the S1 error-value law. Results read as "fixed constructor + matched QSC(p*) at S1 entropy", never "same-law S1→S2 validation".

## 3. Accounting (frozen; fixes old mismatch)
- (i) Layer-local reported efficiency: f_L2=(m2·5)/(256·H_channel)=235/(256×0.80698)=235/206.586≈1.1376 (repro band 1.1373–1.1379). INFORMATIONAL ONLY — never gated.
- (ii) System budget mapping: f_super=(4·(m_total·5)+64)/(1024·H_full)=1044/852.544≈1.2246 (H_full=0.83256272). BUDGET MAPPING, not measured efficiency; L1 (m1≈2) unconstructed.
- (iii) Campaign gates (AND): (a) superframe FER=fails/60≤5% (≤3/60) from group outcomes (any-frame-fail⇒group-fail, `exact_match is True` per frame); (b) f_super≤1.3 on measured-D_blind basis. Gate (a) uses group outcomes; gate (b) uses leak arithmetic.
- D_blind=0 MEASURED placeholder (no blind rounds in path; NEVER-ASSUME-ZERO label); sensitivity Δf_super=D_blind/852.544 (16 bits≈+0.019; headroom 64.31 bits). Mandatory in result.
- Early-stop: halt at 4th group failure (bar unpassable) → FAIL; retain partials. Budget-exhaustion halt → FAIL(budget), resume only per §5 continuation.

## 4. Seeds (frozen, fresh)
- Constructor: 2026092001 (fixed, §1). Frames: literal `2026097001+idx`, idx=0..239 (group g frame f → idx=4g+f); 60 groups × 4 frames = 240 decodes.
- Disjointness: 20260970xx hundred-block overlaps no frozen namespace (20260920xx/43xx/44xx/45xx/49xx, ex-V1 2026096001, ex-V2 2026096101/2026096301, G6/R7/R11/R23/CLI). Pre-EXECUTE rg-absence re-check required (S1_READINESS §S1r-seeds pattern); record proof.

## 5. Budgets/scope/stop (frozen)
- Synthetic EXPLORE only. No real/Jan-21 frames (S3 DECIDE separate). No writes outside fresh root.
- Caps (single arm, single invocation, single window): wall ≤3600 s; RSS <4 GiB; per-decode cap 300 s; 1 CPU; ledger-style call count in result.
- Continuation: ≤1 explicit `--resume-from` in a fresh window for WALL-PARTIAL only (packet §7-style delta carried over); terminal FAIL/early-stop states are not resumable. Note: p*=0.081 > 0.05 proxy noise → more cap-saturating decodes expected; wall budget unchanged.
- Root: `workspace/s2b_<uuid8>` fresh additive (UUID + absence proven at Pre-EXECUTE); old roots untouched; `results/`, `outputs_comparison/` forbidden.
- STOP on any science-input change (grids/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles). dv-distribution / stopping-rule evaluation only AFTER this experiment (§7).

## 6. Entry evidence + executor delta (all REQUIRED, none claimed here)
- (a) Constructor-fix review PASS_WITH_FINDINGS recorded (`S2_CONSTRUCTOR_FIX_REVIEW_20260920.md`); (b) 30 focused tests green (7 new + 12 v10-peg + 11 s2-campaign); (c) executor updated per delta E1–E6 below.
- E1 construct assert `four_cycles==0` (+record min_girth/rank; STOP on mismatch). E2 single-arm S2b (delete V2 arm + `<1158` predicate). E3 frame-seed base 2026097001+idx. E4 sampler+prior both p*=0.081, max_iter=300.
- E5 accounting per §3 (f_L2 informational; f_super budget-mapping label; D_blind + sensitivity lines). E6 checkpoint-per-group + one wall-partial `--resume-from`; early-stop at 4th group fail.
- G-S2B = frozen only. Execution needs fresh explicit grant + Pre-EXECUTE (Q0–Q6: branch, scope cleanliness, frozen contract, authorization, output-absence, focused tests). Authorize NOTHING.

## 7. Deliverables (under run root + result doc)
- `S2B_RESULT_20260920.md` (verdict, dual-unit table f_L2 + f_super-mapping, D_blind + sensitivity lines, B-limitation statement) + `rows.json` (per-frame raw) + `group_accounting.csv` (per-group accept/leak/f).
- Operator prompt: `S2B_EXPERIMENT_PROMPT_20260920.md` (companion, ≤40 lines). No other outputs.
- Does NOT establish: no L1 construction; no S3/real-data claim; no qualification/publication numbers; no dv-distribution or stopping-rule conclusions (separate step after); no same-law S1→S2 validation (B is entropy-anchored only).
