# P2 conditional-prior implementation

Preserve the real joint-histogram information discarded by marginal hard-plane priors, preparing the natural LSB-first long-block prototype recommended by P1; realized f gain is not measured.

Scope is implementation plus focused mathematical tests, not a decoder experiment. No decoder packet, decoder/backend construction, empirical decoding, DE, raw/frame reading, benchmark or claim is authorized here. The pre-packet MDE arithmetic remains a prerequisite to any later experiment, not a sample-availability proof.

Luna owns only new `comparison_bench/src/comparison_bench/formal_ir/msd_conditional_prior.py` and `comparison_bench/tests/test_msd_conditional_prior.py`. Other agents work here; preserve their changes. Main owns requirements, acceptance and this single route's change/log.

Acceptance:

- M1: from trusted finite nonnegative square power-of-two C[a,b], build P(A_bit=1|complete natural Bob symbol, previous Alice bits in declared decode order). Natural and Gray Alice-label bijections are explicit; Bob query symbols remain natural, keeping full information. Complete order validation matches P1. No BSC/error-rate scalar approximation or optional smoothing.
- M2: expose a small model with per-stage prior/support tables and a query receiving stage index, natural Bob symbols and previously decoded bit arrays shaped (stage,N). Query computes the prefix in the same order as table construction. Receiver query accepts no Alice ground truth. Out-of-support Bob/prefix cells return p_one=0.5 and unsupported=True. In-support deterministic cells preserve exact 0/1.
- M3: convert p_one into receiver base bits and per-variable error probabilities: base=1 if p_one>0.5, else 0 (fixed tie); p_error=min(p_one,1-p_one). Also expose natural-log LLR=log(P0/P1), with an explicit caller floor in (0,0.5) for finite LLRs. Never call a decoder or choose graph/rate here. Do not call these priors measured FER or reconstructed real frames.
- M4: deterministic mathematical fixtures cover a dependent four-symbol parity example, both complete orders, natural/Gray label agreement under explicit relabeling, a nonuniform conditional probability, zero-support fallback, exact deterministic probabilities, MAP/tie conversion and invalid shape/order/domain inputs. No RNG or decoding/performance outcomes. Tests use repository .venv, pytest -p no:cacheprovider -o addopts=, fresh workspace/msd_prior/<uuid>, timeout 120 seconds.
- M5: return owned files, exact tests/results and any retained failure; no commit, push or self-acceptance. Independent focused review checks axes/prefix indexing/LLR sign/truth isolation and scope before main acceptance.

Use NumPy/stdlib and existing P1 count/order validation where useful. Do not add a framework, caching system, integrity manifests or production hardening. Return complete items or concrete blocker with full error/remedies and one main decision.
