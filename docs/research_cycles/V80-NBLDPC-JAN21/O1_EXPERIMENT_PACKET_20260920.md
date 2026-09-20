# O1 Experiment Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-O1 (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§8).
- Parents: O1_SCOPING_20260920 (feasibility pins) + S2C_LAMBDA_STUDY (λ={2:1}) + S2_FALLBACK_OPTIONS (O1 route) + S2c packet/result/accounting map (semantics reuse).
- Why: S2c gate unattained at n=256 all arms (4/4 group FER); O1 tests finite-length gain of a single n=1024 code (superframe-as-code) on the same empirical channel.

## 1. Design: superframe-as-code (REPLACES the 4×256 grouping)
- One code: n=1024, GF(32), λ={2:1} frozen (lambda-study observation: A50⊇A47 successes, pairwise CIs non-overlapping; NOT a λ-optimality claim).
- Acceptance unit = ONE BLOCK = one n=1024 decode with `exact_match is True`. No frames, no group-of-4 rule, no any-frame-fail grouping.
- Per arm: 60 blocks = 60 decodes; block FER = fails/60; gate ≤3/60 (≤5%). Early-stop at 4th block failure → FAIL, retain partials.

## 2. Arms + constructor (fixed peg, seed 2026092001, trials 20)
- A188 PRIMARY (DE-covered): m=188, rate 0.81640625 (=S1; ρ byte-identical {10:0.098,11:0.902} → NO new DE arm). Pins: fc=0, girth=8, rank=188/188 (scoping dry trial-1).
- A208 SECONDARY (budget-max): m=208, rate 0.796875, ρ={9:0.141,10:0.859} (differs → A208-DE pre-check, §3). Pins: fc=0, girth=8, rank=208/208.
- Both: check sockets 2048, parity 0 (scoping §1); construct-twice-identical required. Pre-EXECUTE asserts exact pins; mismatch → STOP.
- Construction-seed REUSE justification: same (n,m,λ,seed,trials) reproduces dry-run graphs exactly; prior 2026092001 uses were n=256 → disjoint outputs, no collision.

## 3. A208-DE pre-check (decision: option (i) — small MC-DE arm; cheap and clean)
- Single MC-DE point via frozen V26 `run_mcde_posterior(q=32, λ={2:1}, ρ=make_rho(0.796875))` on the SAME empirical L2 bundle/sampler as S1; S1 n_samples/seed convention.
- Cost: CPU-only, one ensemble point, zero decodes; est ≪3600 s window (S1-DE-class cost). Runs BEFORE the A208 block window; outcome recorded as DE-cover label.
- A208 block campaign proceeds regardless: DE pass → DE-covered secondary; DE fail/marginal → exploratory WITHOUT DE (label carried, gates unchanged).

## 4. Channel + decoder mapping (frozen S2c semantics, n=1024 symbols/block)
- Source/bundle: same 2M `channel_counts.npz` → `gamma_f03.npz` (g1 (32,1024), g2 (32,32,1024), H_L1/H_L2) + `gamma_f03_pb.npz` (p_b, sum=1±1e-9 else refuse). Read-only, synthetic draws.
- Per-symbol triple (L2 order, i.i.d. ×1024): b~p_b (`rng.choice(1024,p=p_b)`); u1~g1[:,b]/sum; u2~g2[u1,:,b]/sum; zero-mass→delta-at-0. Alice x=u2; Bob 10-bit b.
- y_i=b_i&31 (`factor_layers` v29 L269-273); rows=`posterior_rows("L2",b,u1)` (v26_channel L232-244: pjoint[u1,:,b]/norm, norm≤0→delta-at-0) = γ₂(·|b_i,u1_i).
- Prior π_i(e)=rows_i[y_i⊕e] via `_center_rows` (v28 L189-197, XOR); entrypoint MUST be `decode_error_domain_posterior` (v28 L155-186; s_e=s_x+H*y). Scalar-prior `decode_error_domain` (v10 L491-518) NEVER used.
- Kernel `decode_fftqspa` (v10 L335-340, length-agnostic); max_iter=300, default streak=3; per-decode cap 300 s. GENIE true-u1 = D1 ceiling label carried (upper bound only).

## 5. Seeds (block seeds fresh; construction seed §2)
- Blocks (SHARED/PAIRED across arms): literal `2026095501+idx`, idx=0..59 (block k→idx=k); stream `common.v10_seed(f"o1_blk:{seed}")` (distinct from `s2c_emp:`).
- Disjointness: 20260955xx outside consumed 2026096–98xx blocks and 20260920xx/70xx/72xx/75xx spots; Pre-EXECUTE rg-absence re-check required; record proof.

## 6. Accounting + gates (per arm, AND)
- A188: leak=188·5+64=1004, f_super=1004/852.544=1.177652 (headroom ~104.3 b). A208: leak=208·5+64=1104, f_super=1108.31-budget → 1104/852.544=1.294947 (headroom ~4.3 b — TIGHT).
- (a) block FER=fails/60 ≤5% (≤3/60). (b) f_super ≤1.3 on measured-D_blind basis. f_L2 INFORMATIONAL ONLY, never gated.
- D_blind=0 MEASURED placeholder (NEVER-ASSUME-ZERO); sensitivity Δf=D_blind/852.544 (16 b≈+0.019; A208 headroom ~4.3 b ⇒ any blind disclosure fails gate (b) — stated risk).

## 7. Budgets/scope/stop
- Synthetic EXPLORE only. No real/Jan-21 frames. No writes outside fresh root.
- Decode-count math (CORRECTED — one block = ONE n=1024 decode, not 4 frames): 60 blocks = 60 decodes/arm ≈ 60×11 s ≈ 660 s/arm (11 s est: 4× edges over 2.70 s/decode, scoping §4).
- Single ARM per invocation, single window: wall ≤3600 s; RSS <4 GiB; per-decode 300 s; 1 CPU; first window measures per-decode wall/iters to confirm the 11 s est.
- Continuation: ≤1 explicit `--resume-from` in a fresh window for WALL-PARTIAL only; terminal FAIL/early-stop not resumable. A208-DE pre-check runs as its own quick step before the A208 window.
- Root: `workspace/o1_<uuid8>` fresh additive (UUID + absence proven at Pre-EXECUTE); old roots untouched; `results/`, `outputs_comparison/` forbidden.
- STOP on any science-input change (n/m/rates/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles).

## 8. Entry evidence + executor delta (REQUIRED, none claimed here)
- Entry: (a) scoping pins recorded; (b) λ-study recorded; (c) executor built per E1–E7; (d) Q0–Q6 Pre-EXECUTE (branch; scope cleanliness; frozen contract §§1–7; authorization; output-absence; focused tests incl. 1-block dry decode).
- E1 §2 constructor at (1024,m)/arm + exact-pin asserts + construct-twice identity; STOP on mismatch. E2 §4 triple sampler + bundle binding + p_b gate. E3 §4 y/rows/prior wiring into `decode_error_domain_posterior` (no QSC path).
- E4 block seeds 2026095501+idx + `o1_blk:` stream + max_iter=300/streak 3 + per-arm flag (single arm/invocation). E5 accounting §6 dual labels (informational f_L2 vs budget f_super). E6 checkpoint-per-block + one wall-partial `--resume-from`; early-stop at 4th block fail. E7 A208-DE pre-check step (V26 kernel, S1 convention) + DE-cover label threading.
- NEW module `formal_ir/v80_o1_campaign.py` (imports frozen v10_peg/v26_mcde/v26_channel/v28/sampler read-only). NO edits to frozen modules.

## 9. Deliverables + does-NOT-establish
- `O1_RESULT_20260920.md` (per-arm verdict, block table, f_super mapping, D_blind + sensitivity, DE-cover labels, genie-u1 statement) + `rows.json` + `block_accounting.csv` under run root. Prompt: `O1_EXPERIMENT_PROMPT_20260920.md` (≤40 lines).
- Does NOT establish: no L1 construction (genie-u1 ceiling only); no λ-optimality; no finite-length-gain promise (4× gain unquantified); no S3/real-data claim; no qualification/publication numbers; single-code semantics change vs S2c noted (block≠group; not directly comparable to S2c group FER).
