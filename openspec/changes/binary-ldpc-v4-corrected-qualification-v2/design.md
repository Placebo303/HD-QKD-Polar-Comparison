# Design: Binary LDPC v4 Corrected Qualification v2

## 1. Minimal Versioned Binding

Modify only the existing, never-production-instantiated conditional files:

- `cli/run_ldpc_v4_synthetic_qualification.py`;
- `cli/verify_ldpc_v4_synthetic_qualification.py`;
- `cli/run_ldpc_v4_real_qualification.py`;
- `cli/verify_ldpc_v4_real_qualification.py`;
- their two focused test modules.

Historical v1/v2 development sources and packages remain byte-identical.
Synthetic tooling SHALL use
`verify_ldpc_v4_development_v2.verify_output` and bind the v2 development
runner, verifier, evaluator, plan, report, manifest, selection, channel, and
codebook hashes.

## 2. Package Identities

Version the package-facing identities:

- synthetic run ID `binary_ldpc_v4_synthetic_qualification_v2`;
- synthetic plan/run/report schemas ending `_v2`;
- synthetic failure finalizer `eight_file_synthetic_failure_retention_v2`;
- real run ID `binary_ldpc_v4_real_qualification_v2`;
- real plan/lock/run/report schemas ending `_v2`;
- real failure finalizer `nine_file_real_failure_retention_v2`.

The mathematical RNG domain schemas may remain v1 because their algorithm and
byte consumption do not change. Existing formal method, codebook, channel,
selection, transcript, outcome, and gate semantics remain unchanged.

## 3. Synthetic Production Gate

Synthetic prepare SHALL:

- strictly verify the exact corrected development package;
- generate eight new independent 128-bit CSPRNG roots;
- prove no root or Toeplitz seed collision with v3 or development;
- generate exactly 128 nominal and 128 stress frames;
- freeze exact order, source hashes, caps, and integer floor 126.

Prepare, main-thread audit, execute, and read-only verify each occur once.
Each stratum must contain 128 denominators, at least 126 verified successes,
and zero forbidden failures. Failure stops the route without real prepare,
tuning, or rerun.

## 4. Real Capacity and Input Contract

The current read-only capacity audit is:

| Stratum | Complete | v3 reserved | Eligible | Required | Deficit |
|---|---:|---:|---:|---:|---:|
| bw120 | 117 | 32 | 85 | 128 | 43 |
| bw180 | 117 | 32 | 85 | 128 | 43 |
| bw200 | 117 | 32 | 85 | 128 | 43 |

Do not reuse reserved frames or lower the denominator. Additional data must
provide at least 43 new complete, non-overlapping 256-symbol frames per
stratum after source validation. Prefer at least 64 new frames per stratum to
leave rejection margin for incomplete, duplicated, or invalid frames.

New input SHALL be a traceable read-only source extension containing q=1024
paired sidecars and provenance metadata tied to the added `.ttbin` capture.
It must use the same 20 dB domain and registered bw120/bw180/bw200 processing
rules. Source files, metadata, processing rule, sizes, SHA256, frame
identities, and non-overlap with calibration/reserved/current frames are
locked. No newly supplied real outcome may be decoded or inspected before the
lock and plan are frozen.

If new data changes calibration, acquisition domain, mapping, or processing
semantics, stop and create a new development change rather than appending it
silently.

## 5. Conditional Real Qualification

Only after synthetic promotion and sufficient source capacity:

1. construct one fresh v2 real data lock and plan;
2. select 128 new frames per stratum by the frozen SHA256 rank;
3. audit source hashes, exclusion, disjointness, order, Toeplitz isolation,
   384 denominators, caps, and 126/128 gates;
4. execute once and verify once.

All failures remain in denominators. Any stratum below 126/128 or any forbidden
failure produces immutable `non_promoted` evidence. No retry or tuning uses
synthetic or real confirmation outcomes.

## 6. Frozen Source-Extension Contract

Implement one additive module and CLI for source intake; do not change the
Phase 6 v3 bridge or its historical manifest:

- `formal_ir/ldpc_v4_real_source.py`;
- `cli/build_ldpc_v4_real_source_extension.py`;
- focused source-extension tests.

The builder SHALL accept the exact development-bound base source manifest and
one or more added acquisition specifications. Each added acquisition contains
one main `.ttbin`, its exact `.1.ttbin` chunk, and exactly three sidecar
directories for bw120, bw180, and bw200. It emits one canonical, self-hashed
`binary_ldpc_v4_real_source_extension_v1` JSON file using exclusive creation.

For every added acquisition, the builder/verifier SHALL:

- bind absolute path, byte length, and SHA256 for both `.ttbin` files and all
  nine sidecar files;
- derive `acquisition_id` from the two raw-file hashes rather than a supplied
  label;
- reject a raw-file hash pair already present in the base source or another
  added acquisition, including copied directories and re-materializations;
- require q/dimension 1024, acquisition loss 20 dB, exact bin width, strict
  unsampled `.ttbin` origin, `materialized_from_ttbin`, and nearest pairing;
- accept only one-dimensional equal-length integer arrays with symbols in
  `[0,1023]`, and count only complete contiguous 256-symbol frames;
- reject missing chunks, missing/extra strata, tail padding, silent dtype or
  format conversion, inconsistent source paths, and any changed file hash.

The extension does not replace or recompute calibration. It exposes a real
candidate pool consisting of the original bw120/bw180/bw200 datasets plus the
added acquisitions. Each candidate records a source-aware frame identity and
a payload identity derived from the exact Alice/Bob 256-symbol bytes. Exact
payload duplicates across the complete pool are rejected, even when paths or
acquisition labels differ.

Selection is frozen as SHA256 ranking within each stratum using domain
`binary_ldpc_v4_real_selection_v1`. All v3-reserved identities are excluded
from the original acquisition; all calibration identities remain excluded.
Capacity is computed only after source validation, duplicate rejection, and
exclusions. Each stratum must have at least 128 eligible candidates before
real output-directory creation.

Real prepare SHALL require `--source-extension-manifest`. The real lock embeds
the exact extension manifest, its external file record, the unchanged base
manifest hash, exclusions, selected rows, and fresh Toeplitz roots. Execute
and the read-only verifier reconstruct the manifest, pool, selection, source
files, transcript, outcomes, and gates. The extension builder and verifier
must never invoke the decoder or inspect real qualification outcomes.
