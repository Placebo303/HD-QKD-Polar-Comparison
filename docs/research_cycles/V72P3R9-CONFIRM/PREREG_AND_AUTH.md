# R9 CONFIRM (m100, P-1p5M-tail) — PREREG_AND_AUTH (frozen)

Track: DECIDE (preregistration write only; no execution, no data access, no commit/push).

## D-recorded (transcribed, not re-judged)

- D-R7-01 (main-thread decision, quoted from `docs/research_cycles/V72P3R7-RATESCAN/EXPLORATION_LOG.md` L31): "ADOPT m=100 for fresh-pool (P-1p5M) confirmation; m96 parked."
- R8 UNBLOCK-m100 rationale (quoted from same log L24-30): "m88 FAIL 0/0 (delta 0.21478); m92 FAIL 0/0 (0.37103); m96 PASS 8/8 (0.52728)" / "Transition: LOCATED 92|96 — hard structural (no soft middle, pops agree; FAILs from tail-convergence gate, hold for ANY δ)" / "Reviewer verdict: UNBLOCK-m100 (not m96: edge + 2 rows above real-failed 94 → repeats gap artifact; not HOLD: edge moots B2 for location though bar-citing promotion text still needs chartering)."
- R8 cushion (prompt-stated): m100 sits 8 rows above the 92|96 hard edge (100 − 92 = 8 above the FAIL side).

## P-pop (frozen population)

- Pool P-1p5M-tail: session `20260107_PPLN_1p5M`, window frames 2123..2186 (64 frames; 2186−2123+1=64), blocking K=2 even-odd → 128 calls.
- Path (verbatim from `v71_data_registry.json` L1315): `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260107_PPLN_1p5M/pairs.parquet`.
- frames_total (verbatim from `v71_data_registry.json` L1316): 5125 (metadata only; no symbol payload read).
- FRESH graph namespaces: TBD-at-readiness (exact strings frozen before use; proven absent before use).
- Ban list (planned-never-used): D8 / D9 / D12 / D16 / D19 namespaces; G6 graphs 2026094601/4602 (frozen G6 pair per `scripts/g6_decide_r1.py` L69); R7 DE seeds 2026094701..2026094708 (verbatim from R7 `summary.json` L44-53); R7 graph pool 2026094711..2026094719 (verbatim from R7 `summary.json` L31-41). R7 pool planned-never-used note: `"graphs_constructed": 0` (R7 `summary.json` L6/L42), `"decoder_calls": 0` (L5); admission predicate "STATED, NOT EXECUTED" (L97); seed-disjointness `"passed": true` with empty `range_hits` incl. `g6_graphs: []` (L65-76).

## P-op (frozen operation)

- L020-n128 m100 single arm, candidate `lam_d2_0.20_d3_0.80` (R7 S7-arith m100 sheet, `summary.json` L79-111).
- Verbatim m100 sheet: `"m": 100`, `"n": 128`, `"E": 349`, `"check_counts": {"3": 51, "4": 49}`, `"variable_counts": {"2": 35, "3": 93}`, `"rate": 0.21875`, `"disclosed_bits_per_symbol": 3.90625` (DE nominal per-symbol; NOT the block disclosure), `"mean_check_degree": 3.49, "max_check_degree": 4`, `"delta": 0.6835301153656221`, decoder forward context `"max_iter": 90, "damping": 1.0, "note": "frozen forward context only; zero decoder calls in R7"`.

## P-dec (frozen decoder/contract; G6-DECIDE-R1 wording carried with m=100 substitution)

- Cold row-layered 90/1.0 single-pass (G6: `scripts/g6_decide_r1.py` L11-12, L57-58, L227: "Single-pass cold 90/1.0 decode").
- Model-F marginal read-only + cross-session caveat (G6 pattern L11: "Model-F marginal prior (read-only npz)"). Prior root for R9: UNKNOWN (source: no R9 prior-root frozen in prompt or repo; G6 used `workspace/v72p2d5_model_f_input/20260907_r1` — NOT carried without explicit freeze).
- T=64 tag bits (G6: `TAG_BITS = 64`, L60); disclosure per block 5*100+64 = 564 bits (formula verbatim G6 L12/L113-115: "disclosure_i=5*rows+64" / "Disclosure per block: 5*rows + 64 tag (control/interaction/auth 0)").
- C/I/A=0 (G6 L243-245: `"control_bits": 0, "interaction_bits": 0, "auth_bits": 0`).

## P-acct (frozen accounting)

- attempted/exact/accepted/undetected isolated; disclosure sums include failures; exact subset of accepted, undetected never merged (G6 L13-14, L259-273: "Isolation: exact subset of accepted; undetected never merged").
- Block schemas carried from G6 `BLOCK_COLUMNS` (L82-88) and per-record semantics (L235-246) with m=100 substitution.
- H_frozen 3.347605 (verbatim G6 L61: `H_FROZEN = 3.347605`) + H_L2 sensitivity 3.222719884634378 (verbatim G6 L62: `H_L2 = 3.222719884634378`).
- k_sym nominal for m100: UNKNOWN (G6 `K_SYM_NOMINAL = 34` is m94-specific; no m100 value sourced — never hand-fill).
- beta derived-only (G6 L13-14: "beta derived-only").

## P-gate (frozen thresholds)

- FIRST_* rule: a FIRST_* claim needs accepted ≥ 1 AND undetected == 0; else terminal NO_USEFUL_RECOVERY (G6 terminal pattern: condensed PREREG "terminal NO_USEFUL_RECOVERY", RESULT "Main-thread ACCEPTED NO_USEFUL_RECOVERY").
- UNDETECTED_STOP absolute, fail-closed, break on first undetected (G6 L15, L433-437: "break  # UNDETECTED_STOP absolute (fail-closed)"; terminal `"UNDETECTED_STOP" if any(r["undetected"] ...)`).
- ENGINEERING_BLOCKED for infra / non-admitted graphs (G6 L15, L393).

## P-bud (frozen budget/root)

- sci ≤ 128 / setup ≤ 16 (G6 L79-80: `SCI_CEILING = 128`, `SETUP_CEILING = 16`); wall 1800+120s / RSS 2GiB / 1-proc / no-retry (prompt-stated G6-carryover; G6 actuals were wall 108s / RSS ~211.5MiB per RESULT, budgets per prompt).
- Root: `workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d` PROPOSED-absent — do NOT create/probe it (no execution, no root touch in this preregistration).

## P-cmd (frozen command template)

- ARGV template (G6 pattern `scripts/g6_decide_r1.py` L89-94, m/session/frames/root substituted; runner TBD R9b): `<runner> --execute-real --execution-authorized --registry v71_data_registry.json --session 20260107_PPLN_1p5M --frames 2123..2186 --arm L020 --prior-root <TBD-R9b> --out-dir workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d`.
- `--execution-authorized` default-false; refusal before any root creation, decoder binding, or Model-F load (G6 L17: "--execute-real refuses without --execution-authorized").
- Single invocation; no second invocation authorized.

## P-tests (frozen; delta on G6 F1-F7 FAKE-fixture pattern)

- G6 base (L18): "F1-F7 on FAKE fixtures only".
- R9 delta: m100-564-disclosure check + fresh-seed admission (A1-A6 incl. deterministic replay) + refusal / no-overwrite / verifier probes. All on FAKE fixtures; no real-data execution.

## P-stop (frozen)

- Any violation STOP + retain + single decision needed (verbatim G6 L19: "any violation STOP + retain + single decision needed"); retained crashes never retried (G6 L275: "retained crash, never retried").

## P-auth (frozen authorization)

- R9 execution grant NOT consumed by this preregistration write.
- Execution requires ALL three: one-word user grant + Pre-EXECUTE review + Pre-RESULT review. No SKR/qualification/promotion/generalization claim.

## F-conflict

- NONE KNOWN (slot held; any discovered conflict enters revise-required before execution).

## Source table (sourced-or-UNKNOWN per ID)

| ID | Value | Source |
|---|---|---|
| m/E/check/var/rate | 100/349/{3:51,4:49}/{2:35,3:93}/0.21875 | R7 `summary.json` L79-111 VERBATIM |
| DE nominal | 3.90625 bits/symbol | R7 `summary.json` L92 VERBATIM (not block disclosure) |
| R7 DE seeds / pool | 4701-4708 / 4711-4719 | R7 `summary.json` L44-64 VERBATIM |
| R7 non-execution | graphs 0, decoders 0 | R7 `summary.json` L5-6 VERBATIM |
| pool path / frames_total | pairs.parquet / 5125 | `v71_data_registry.json` L1315-1316 VERBATIM (metadata only) |
| window / K=2 / 128 calls | 2123..2186 / even-odd / 128 | prompt-stated; 64-frame arithmetic check only |
| 90/1.0/T=64/C/I/A=0 | frozen | `scripts/g6_decide_r1.py` L57-60, L243-245 VERBATIM |
| disclosure formula → 564 | 5*100+64=564 | formula VERBATIM (L113-115); arithmetic per prompt |
| H_frozen / H_L2 | 3.347605 / 3.222719884634378 | `scripts/g6_decide_r1.py` L61-62 VERBATIM |
| k_sym (m100) | UNKNOWN | no m100 source; never hand-filled |
| R9 prior root | UNKNOWN | no R9 freeze; G6 root NOT carried |
| R9 runner | TBD R9b | prompt-stated |
| FRESH namespaces | TBD-at-readiness | prompt-stated |
| D-R7-01 / R8 rationale | ADOPT m100, m96 parked / 92\|96 edge | `V72P3R7-RATESCAN/EXPLORATION_LOG.md` L24-31 VERBATIM |
| budgets/root/auth/stop | per P-bud/P-stop/P-auth | G6 runner + prompt, as cited above |
