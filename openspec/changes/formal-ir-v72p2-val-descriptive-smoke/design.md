# Frozen V72P2 design

## Data and prior

Use only session 20260123_1M_600k_0dB from v71_data_registry.json. Existing data_sha 84d62779 is inherited processing provenance, NOT a content hash or newly certified real-data identity. Record registry path, source path, session, actual selected frame IDs and row counts. No new hash is computed.

CAL frame IDs 702..1725 (1024 frames, 256 pairs each). SMOKE IDs 1726..1761: nine consecutive groups of four, sorted frame_id then pair_idx. Each frame must contain exactly 256 ordered distinct pair indices and integral symbols 0..1023. No substitution or skipping to fill a block. Invalid CAL stops preparation; invalid smoke blocks keep their assigned slot and zero disclosure if not attempted. Only CAL and these 36 VAL frames are selected; no other session or TEST content is used.

Import V70 select_lambda(a_cal,b_cal), using its existing four contiguous folds and 30-point 10^-2..10^4 grid. Refit hierarchical_P on all CAL: C[b,a], N_b=row sums, P_global=column sums / CAL pairs. Freeze selected lambda before smoke. Apply maximum(P,1e-300), then row normalization solely for finite natural-log representation; report the floor. build_prior_logp(bob_symbols,Ps) consumes Bob only: log(Ps[bob_symbols,:]). No Alice-dependent channel prior. CE uses log2.

The selected CAL-CV score is the fixed denominator CE_ref for this cycle. It is selection-conditioned model cross-entropy, not Shannon conditional entropy or independent validation. Smoke empirical CE is posthoc descriptive and never selects a model or budget.

## Decoder boundary and narrow correction

Preserve FrozenMotherSpec (9), SoftJointConfig (8), mother 9036x10240/49620 edges, 72 checkpoints, 10 iterations/checkpoint, 720/block, clip20, tolerance1e-6, float64, seed20260902. Mother rows remain 160,288,...,8992,9032,9036; disclosure's finer 1111-prefix construction is unchanged.

run_decoder retains its existing signature/dictionary. Each residual is max(abs(new_c2v-old_c2v)), including a nonzero warm start. Before returning, recompute bit_to_factor from final c2v, factor_to_bit by target-bit self-exclusion, APP=clip(factor_to_bit+sum(final_c2v),20), and hard bits/symbols/syndrome. variable_to_check may remain the last transmitted messages, explicitly not a newly transmitted iteration. This readout is not an additional BP iteration. Preserve the five message equations, sign convention and no-extra-channel-LLR property. run_incremental_decoder is not used or refactored by this cycle.

Each block starts iterations_used=0 and empty c2v. For ck: check time/iteration budget before publication; slice indptr[:ck+1] and indices[:indptr[ck]], pad old c2v with zeros for new edges, call run_decoder(...,max_iter=min(10,720-used),warm_start_c2v=warm). Increment used by len(residuals); require 1..requested. No state carries between blocks. Check the current candidate only, after the final legal iteration too. Do not collect 72 message arrays or scan stale candidates.

Alice produces full syndrome from frozen CSR and bits (LSB first) and the existing sha256(bits.tobytes()).digest()[:8] tag. Decoder receives only the current syndrome prefix and Bob-derived prior. Oracle equality/errors are evaluated after the protocol decision and cannot alter stopping.

## Communication and outcomes

Model protocol: Alice publishes the first160 syndrome bits and one64-bit tag. Bob sends one public CONTINUE bit before each later checkpoint's incremental syndrome. No additional ACK/header/authentication/transport bits are modelled; record that exclusion. The last two increments are40 and4. Stop before publication if no iteration/time remains.

Counters are separate: disclosed_rows; syndrome_bits_published (=rows); tag_bits_published (64 once on first publication, irrespective of comparison); control_bits_sent (one per continuation). Published information is never rolled back on an exception, numeric failure or timeout.

protocol_accepted = finite AND current syndrome matches AND current tag matches. Residual convergence is not required for acceptance. Offline exact recovery is separate: verified_exact_success=protocol_accepted AND oracle_exact; undetected=protocol_accepted AND NOT oracle_exact, never included in success. Finite failed verification at the final ladder is ladder_exhausted (also record syndrome/tag flags), not a numeric error. Invalid input, numeric_failure, decoder_error, budget_exhausted and not_attempted remain distinct. A numeric/decoder error or resource stop halts the real run and retains remaining not_attempted rows; ordinary ladder exhaustion continues to the next block.

leak_IR_bits=syndrome_bits_published+tag_bits_published. total_public_bits=leak_IR_bits+control_bits_sent. For attempted blocks f_model_relative=leak_IR_bits/(1024*CE_ref), including failed attempts with explicit status; f_public_model_relative uses total_public_bits. These are model-relative ratios, not a security efficiency claim. Aggregate all-attempt sum ratios and success-conditional ratios separately; empty denominators => null. Report exact successes out of9, attempted count, excluded/not-attempted count, per-block residual/iterations/timing and error counts. No FER inference, capacity attribution, PA or SKR.

## Resources and result retention

One real invocation, serial nine blocks, no rerun/tuning. Soft deadlines checked before/after each checkpoint: 600s/block, 7200s whole invocation including CAL; one checkpoint can overrun. These are operator safety budgets, not predicted performance. A failed run is retained, not retried automatically. Report actual wall time; no fabricated RSS claim. Known working-array accounting is not process peak memory. Do not run a real-data trial to set a new budget.

Additive output root is frozen in EXECUTION_PACKET.md. Four compact artifacts: manifest.json (code/plan Git refs, params, data identities/roles, command), results.json (9 assigned rows plus lightweight per-checkpoint scalar logs), table.csv (9 rows), report.md (descriptive summary). No raw symbols, syndrome/tag bytes or fitted matrix committed. Save a candidate after each completed block without overwriting any pre-existing run directory; results of an interrupted invocation remain inspectable. Pre-RESULT main review precedes commit/publication.
