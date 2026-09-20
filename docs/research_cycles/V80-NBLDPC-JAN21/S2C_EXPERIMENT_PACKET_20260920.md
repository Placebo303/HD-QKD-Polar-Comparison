# S2c Experiment Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-S2C (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§7).
- Parents: S2b packet/result/triage + dv study + constructor/socket fix reviews (both PASS_WITH_FINDINGS) + S1_READINESS + PROGRAM_PLAN §1.3/§S2.
- Why: QSC proxy retired — entropy-matched p*=0.081 lies beyond the finite-length cliff (all λ 0/4 at 0.081; cliffs 0.05 L-A, 0.06 L-B/L-C on 4 paired seeds). S2c validates the S1→S2 chain ON the empirical channel S1's DE actually optimized against.

## 1. Arms + constructor (frozen, fixed mechanics)
- Three arms, one construction each via FIXED peg (`peg_construct`+`make_rho`+`_reconcile_check_counts`), seed 2026092001, n=256/m2=47, construct-twice-identical required.
- L-A λ={2:1}: var {2:256}, chk {10:5,11:42}, sockets 512=512, four_cycles=0, min_girth=6, rank=47.
- L-B λ={2:0.5,3:0.5}: var {2:154,3:102}, chk {13:44,14:3}, sockets 614=614, four_cycles=0, min_girth=6, rank=47.
- L-C λ={3:1}: var {3:256}, chk {16:31,17:16}, sockets 768=768, four_cycles=2, min_girth=4, rank=47 (actual value PINNED, not zero).
- Pre-EXECUTE MUST assert exact per-arm values above; mismatch → STOP. No `construct_l2` (λ-locked), no re-seed, no tuning. Banned-family refusal unchanged.
- Per arm: 60 groups × 4 frames = 240 decodes; group rule any-frame-fail⇒group-fail (`exact_match is True` per frame); early-stop at 4th group failure → FAIL, retain partials.

## 2. Channel (frozen: empirical 2M derived counts; synthetic draws, NOT real frames)
- Source: `.../nbldpc_v25_20260818/run_04/channel_counts.npz` 2M train key (`type2_2M_20260121_183657_N_ab_train*`, (1024,1024) float64) — SAME source as S1 gate anchor. No new data access; no parquet/symbol reads; EXPLORE.
- Derived bundle (read-only): `gamma_f03.npz` keys `2M_gamma1_L1` (32,1024) g1[u1,b], `2M_gamma2_L2condU1` (32,32,1024) g2[u1,u2,b] (Q5 branch-a axes) + scalars H_L1=0.02566205/H_L2=0.80690067; `gamma_f03_pb.npz` key `2M_p_b` (1024,) normalized sum=1±1e-9 (else refuse).
- Per-symbol draw (frozen `make_centered_sampler` L2 order, triple retained): b~p_b via `rng.choice(1024,p=p_b)`; u1~g1[:,b]/sum (zero-mass→delta-at-0); u2~g2[u1,:,b]/sum (zero-mass→delta-at-0). I.i.d. per symbol, n=256.
- Alice vector x=u2 (syndrome only enters decoder); Bob 10-bit vector b. L1 conditioning is GENIE true-u1 (L1 unconstructed/accounting-only) — S2c is a genie-aided L2 upper-bound, never a two-layer claim (§8).

## 3. Decoder mapping (frozen code semantics, quoted; no invention)
- y = L2 half of Bob: `factor_layers` v29 L269-273 `((values>>5)&31, (values&31))` → y_i=b_i&31 (F03 L2 bits 4..0, v25_gate L53).
- rows = `posterior_rows("L2",b,u1)` v26_channel L239-244: `pjoint[u1,:,b]/norm`, `norm<=0 → delta-at-0` = γ_2(·|b_i,u1_i).
- prior_error π_i(e)=rows_i[y_i⊕e] via `_center_rows` v28 L189-197 `out[i]=arr[i,add[y,arange]]` (GF32 char-2 add=XOR).
- Entrypoint MUST be `decode_error_domain_posterior` v28 L155-186 (takes (n,q) prior; s_e=s_x+H*y; x_hat=y+e_hat). Frozen `decode_error_domain` v10 L491-518 takes scalar p ONLY — NEVER used here.
- Kernel `decode_fftqspa` v10 L335-340 accepts `(n,q)` per-variable priors (confirmed). max_iter=300; production stopping (default streak=3); per-decode cap 300 s.

## 4. Seeds (frozen, fresh; PAIRED across arms)
- Constructor: 2026092001 all arms (§1). Frames (shared/paired): literal `2026097201+idx`, idx=0..239 (group g frame f → idx=4g+f); stream `common.v10_seed(f"s2c_emp:{seed}")` (distinct domain from S2b `s2_smoke:`).
- Disjointness: 20260972/73/74xx blocks clean repo-wide (planner rg zero-hits 2026-09-20; 2026098xxx REJECTED — 2026098001 collides R23/v22b). Pre-EXECUTE rg-absence re-check required (S1_READINESS §S1r-seeds pattern); record proof.

## 5. Accounting (frozen) + gates
- (i) f_L2=(m2·5)/(256·H)=235/206.586≈1.1376 INFORMATIONAL ONLY — never gated.
- (ii) f_super=(4·(m_total·5)+64)/(1024·H_full)=1044/852.544≈1.2246 (H_full=0.83256272) BUDGET MAPPING, not measured efficiency; L1 (m1≈2) unconstructed.
- (iii) Gates per arm (AND): (a) superframe FER=fails/60≤5% (≤3/60) on group outcomes; (b) f_super≤1.3 on measured-D_blind basis.
- D_blind=0 MEASURED placeholder (NEVER-ASSUME-ZERO); sensitivity Δf_super=D_blind/852.544 (16 bits≈+0.019; headroom 64.31 bits). Mandatory in result.

## 6. Budgets/scope/stop (frozen)
- Synthetic EXPLORE only. No real/Jan-21 frames (S3 DECIDE separate). No writes outside fresh root.
- Single ARM per invocation, single window: wall ≤3600 s; RSS <4 GiB; per-decode 300 s; 1 CPU; ledger-style call count in result.
- Continuation: ≤1 explicit `--resume-from` in a fresh window for WALL-PARTIAL only; terminal FAIL/early-stop states are not resumable.
- Root: `workspace/s2c_<uuid8>` fresh additive (UUID + absence proven at Pre-EXECUTE); old roots untouched; `results/`, `outputs_comparison/` forbidden.
- STOP on any science-input change (grids/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles).

## 7. Entry evidence + executor delta (all REQUIRED, none claimed here)
- (a) Constructor-fix review PASS_WITH_FINDINGS + (b) socket-fix review PASS_WITH_FINDINGS recorded; (c) dv study recorded; (d) executor updated per E1–E7 below.
- E1 §1 assert table (+construct-twice identity; STOP on mismatch). E2 §2 triple sampler + gamma/sidecar binding with normalization gate. E3 §3 y/rows/prior wiring into `decode_error_domain_posterior` (delete QSC sampler+prior p* path).
- E4 frame-seed base 2026097201+idx + `s2c_emp:` stream + max_iter=300/default streak. E5 per-arm flag (single arm/invocation; paired seeds shared). E6 accounting per §5. E7 checkpoint-per-group + one wall-partial `--resume-from`; early-stop at 4th group fail.
- G-S2C = frozen only. Execution needs fresh explicit grant + Pre-EXECUTE (Q0–Q6: branch, scope cleanliness, frozen contract, authorization, output-absence, focused tests). Authorize NOTHING.

## 8. Deliverables + does-NOT-establish
- `S2C_RESULT_20260920.md` (per-arm verdict, group table, dual-unit f_L2 + f_super-mapping, D_blind + sensitivity, genie-L1 statement) + `rows.json` + `group_accounting.csv` under run root. Prompt: `S2C_EXPERIMENT_PROMPT_20260920.md` (≤40 lines).
- Does NOT establish: no L1 construction (assumed/accounting only); no dv causal claims; no S3/real-data claim; no qualification/publication numbers; no same-law QSC generalization; no full two-layer claim (genie-u1 upper bound only).
