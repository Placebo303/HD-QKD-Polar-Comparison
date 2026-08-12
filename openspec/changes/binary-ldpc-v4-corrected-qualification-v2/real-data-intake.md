# Real Data Intake Runbook

This runbook is operational only after a genuinely new 20 dB acquisition is
available. It does not authorize decoding, real prepare, or reuse of the
registered capture.

## Required New Files

One new acquisition is expected to be sufficient if it contains at least 64
complete 256-symbol frames in each stratum after validation:

```text
<new-capture>_20dB.ttbin
<new-capture>_20dB.1.ttbin
<bw120-sidecar>/a_eff.npy
<bw120-sidecar>/b_eff.npy
<bw120-sidecar>/sidecar_meta.json
<bw180-sidecar>/a_eff.npy
<bw180-sidecar>/b_eff.npy
<bw180-sidecar>/sidecar_meta.json
<bw200-sidecar>/a_eff.npy
<bw200-sidecar>/b_eff.npy
<bw200-sidecar>/sidecar_meta.json
```

The raw main/chunk SHA256 pair must differ from the registered pair:

- main:
  `8f6848b58ecaef9d9e227c80a5c4f2c478dd62d44e5e5dd0996c7e17f8b3c320`;
- chunk:
  `303aee617075579c36e232a1ded315f5332a11a2c21d527cab0c9821ee11acc1`.

The three sidecars must be q=1024, 20 dB, strict unsampled
`materialized_from_ttbin`, nearest-pairing sources. A natural incomplete tail
is ignored; it is never padded into a denominator.

## Intake Files Created After Delivery

The main thread creates two new no-overwrite inputs:

1. a canonical extraction of the base source manifest from the immutable
   corrected-development plan;
2. an acquisition-spec JSON with exact paths for the new raw and sidecar
   files.

Then the operator runs:

```powershell
python -m comparison_bench.src.comparison_bench.cli.build_ldpc_v4_real_source_extension `
  --base-source-manifest <canonical-base-source-manifest.json> `
  --acquisitions-json <new-acquisitions.json> `
  --output <fresh-source-extension.json>
```

This step performs no decoding. The main thread reviews the canonical
extension, file hashes, acquisition identity, payload uniqueness, complete
frame counts, exclusions, and deterministic 128-per-stratum selection.

## Production Sequence After Intake Acceptance

Only if all three strata have at least 128 eligible frames:

1. real `prepare` once with `--source-extension-manifest`;
2. main-thread lock/plan review;
3. real `execute` once;
4. read-only verifier once;
5. retain either promoted or non-promoted evidence without tuning or rerun.

No real output directory may exist before source capacity and synthetic
promotion are both reconstructed successfully.
