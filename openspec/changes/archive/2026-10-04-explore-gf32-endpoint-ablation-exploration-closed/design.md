# Design

One small CLI with explicit fake reader/decoder seams; existing code read-only.
Use mapped fixed endpoints and paired replay, own GF32 syndromes, actual vector
capture. No construction, label search, sampler or generic runner framework.
All scientific inputs, budgets and evidence ceilings are frozen in the cycle.
