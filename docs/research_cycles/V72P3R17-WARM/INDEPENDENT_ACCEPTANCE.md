# R17 WARM — INDEPENDENT_ACCEPTANCE (reviewer-go, transcribed)

Verdict: PASS. Transcribed Q1-Q10, not re-judged. Machine-attested + test-phase notes closed by the acceptance block in RESULT.md.

- Q1: counts recomputed — warm accepted 27/128 = exact 27; S0/S1/S2 = 0/17/10; exhausted 101; undetected 0.
- Q2: disclosure recomputed — 83972 final-prefix verified.
- Q3: betas match (derived-only values -0.5310 / -0.5903 confirmed); net_secret -66692 explicit.
- Q4: lifts recomputed — paired +26 vs R9 F=1; −60 vs cold A=87 → NO-GAIN gate (≤87) met.
- Q5: subset verification — warm-only 0, cold-only 60, exhausted→exact 0; warm accepted is a strict subset of cold accepted.
- Q6: moves accounting — S2→exh 52 / S1→S1 14 / exh→exh 41 / S2→S1 3 / S1→S2 4 / S1→exh 8 / S2→S2 6; sums 128; consistent with R11 cold margins (S1=26, S2=61, exh=41) and warm margins (S1=17, S2=10, exh=101).
- Q7: iteration cap — 332/367 at cap; S2→exhausted 52 noted (carried beliefs trap decoder — observed mechanism note, no generalization).
- Q8: provenance confirmed — zero replacement/retune; WARM tokens on seeded stages + CHECK_UPDATED S0; prior read-only; truth post-decision; R9/R11 byte-identical; protected clean.
- Q9: verify 128/0; isolation holds — undetected never merged into success/FER.
- Q10: claim ceiling confirmed — diagnostic-only; NO-GAIN plainly; harmful-direction as observed fact, no generalization.
- Notes: focused test phase 11/13 with 2 phase-sensitive (per reviewer test-phase note); machine totals (wall 269s / RSS ~213MiB) OPERATOR-ATTESTED; block wall_s=0.0 placeholder noted — closed by RESULT.md acceptance block.
- Result: PASS — cleared for DECIDE solidification as NO-GAIN diagnostic evidence.
