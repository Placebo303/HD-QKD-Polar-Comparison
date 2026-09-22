# B2F Executor Review (2026-09-21) — reviewer-go (EXPLORE focused; read-only, no patches, no run)

Verdict: PASS_WITH_FINDINGS. Readiness established; the two-arm run may proceed under standing pre-authorization PROVIDED the main thread explicitly acknowledges FXR-1 at grant time (falsified entropy-parity premise). This review authorizes NOTHING — a fresh per-arm grant + output-absence re-proof (packet §7/Q2) remain required.

Independent re-verification (did NOT trust the truncated implementer report):
- Tests rerun fresh: test_v80_b2f_campaign.py -> 39 passed (15.8s); frozen regression o1+s2c+l1b+b2e -> 174 passed (78.8s). Counts match pre-exec.
- Frozen formula verbatim (exec L297-312): g1c=g1[:,b]; cond=g2[:,:,b].transpose(2,0,1); marg=einsum("nu,nuv->nv", g1c.T, cond); per-row renormalize guard + non-finite/non-positive -> delta-at-0 (L256-280); prior=center_rows_prior(marg, y=b&31); feed v28.decode_error_domain_posterior(field,y,dense,s_x,prior,300). Matches T6 manual triple-loop contraction.
- No genie/argmax reachable: grep confirms NO posterior_rows_l2( and NO bare decode_error_domain( in module; T8 monkeypatches posterior_rows_l2 to raise and decode_block_marginal still returns the marginal prior (bu1 only feeds report-only u1_mismatches; prior is b-only -> D-u1=0.0 MEASURED valid).
- Q3 pins (independent, real constructor): F208 n1024/m208/fc0/girth8/rank208; F202 m202/rank202; both peg-irregular sockets2048 parity0 src A208/A202. Matches Q3.
- Q4 dry (independent, real bundle+sampler): prior_entropy_bits(MARGINAL)=853.0211; genie-row=832.6036; mixing=20.42b; u1_mismatches=4; rowsum err 2.2e-16. Matches Q4. First-block DECODE timing correctly UNMEASURED (fake kernel; Q6 measures block 0 at execution).
- X1-X8 present: dual-flag gate rc2; root workspace/b2f_ + results/outputs_comparison refusal; <=1 wall-partial resume (2nd/terminal/arm-swap refuse), no auto-relaunch; CLI refuses non-frozen --construct-seed/--construct-trials/--block-base/--n-blocks; gates (a) fails/240<=12 early-stop at 13th, (b) f_super=(5m+64)/852.544 F208 1.294947 / F202 1.259759 <=1.3 unchanged O1 basis, no pooling; labels B2F-soft-marginal / u1_source MARGINAL / genie ceiling REMOVED / de covered(F208)+exploratory(F202); D-u1=0.0 MEASURED + never-assume-zero note.
- Scope: only the 2 new files (packet/prompt/preexec are untracked docs); git diff on o1/s2c/l1b/b2e/nonbinary_v28/fftqspa EMPTY (frozen untouched); no workspace/b2f_ roots.

FXR-1 (decision; non-blocking for executor correctness): packet §1 "entropy parity" anchor 826.266 b is the GENIE row entropy H(U2|U1,B)*n, NOT the marginalized prior. The Bayes-marginal row IS P(U2|b_i), so measured Sum_i H(pi_i)=853.02 ~ H_full*n=852.544 — ~26 b/block WEAKER (flatter) than genie. The frozen formula is implemented VERBATIM and the deviation correctly reported (pre-exec Q4 + leak_basis prior_entropy_note), not "fixed" — correct. Consequence: run value is solely gate (a) decodability under the weaker prior (BP convergence = open risk); a result must NOT be read as "entropy parity". NOTE: any "dry ~= 826.27" expectation is the mislabeled anchor; the true measured value is 853.02.
FXR-2 (minor, non-blocking): manifest verify.pins_ok hardcoded True — safe because _construct_gate refuses rc=2 pre-decode before any manifest is written.
FXR-3 (minor): gate (b) f_super passes by construction (arithmetic identity on frozen m); only gate (a) is a real test — correctly framed in packet and code.

Recommend main-thread acknowledgment of FXR-1 before granting either arm. reviewer-go (taste, step-5-preview).
