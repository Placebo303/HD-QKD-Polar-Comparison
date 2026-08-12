"""Deterministic screened, nested HGF2V1 codebooks for formal LDPC v2.

This is deliberately an offline construction/screening component.  It never
consults qualification frames or writes into an existing run directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .ldpc import N, RATES, canonical_matrix_bytes, gf2_rank, parse_matrix_bytes
from .shared import sha256_bytes

GENERATOR_ID = "formal_ldpc_nested_hgf2v1"
GENERATOR_VERSION = "1"
CANDIDATES_PER_PLANE = 16
PREFIX_RATES = ("r050", "r0375", "r025", "r0125")
PREFIX_ROWS = tuple(RATES[r] for r in PREFIX_RATES)
PROBE_COUNT = 64
_VERIFIED_SCREENING_DIGESTS: set[str] = set()


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _seed(domain: str, plane_id: int, candidate_id: int = -1) -> int:
    if not isinstance(plane_id, int) or not 0 <= plane_id < 10 or not isinstance(candidate_id, int) or not -1 <= candidate_id < CANDIDATES_PER_PLANE:
        raise ValueError("invalid codebook domain")
    raw = _compact({"generator_id": GENERATOR_ID, "generator_version": GENERATOR_VERSION,
                    "domain": domain, "plane_id": plane_id, "candidate_id": candidate_id})
    return int.from_bytes(hashlib.sha256(raw).digest()[:16], "big")


def _seed_hex(domain: str, plane_id: int, candidate_id: int = -1) -> str:
    return f"{_seed(domain, plane_id, candidate_id):032x}"


def generate_master(plane_id: int, candidate_id: int) -> np.ndarray:
    """Generate one 56x64 candidate with rank-preserving row prefixes.

    The first 56 columns are unit pivots with additions only above each pivot;
    consequently every requested row prefix has full rank.  The remaining
    columns supply the coverage required by short-prefix structural checks.
    """
    rng = np.random.Generator(np.random.PCG64(_seed("master", plane_id, candidate_id)))
    h = np.zeros((56, N), dtype=np.uint8)
    h[np.arange(56), np.arange(56)] = 1
    # At the 32-row prefix, columns 32..63 need two distinct early supports:
    # one support would duplicate a systematic unit column.  A deterministic
    # rejection-free stream of distinct pairs provides this without changing
    # the triangular pivot argument.
    coverage = rng.permutation(32).reshape(16, 2)
    pairs: list[tuple[int, int]] = [tuple(sorted(pair.tolist())) for pair in coverage]
    while len(pairs) < 32:
        pair = tuple(sorted(rng.choice(32, size=2, replace=False).tolist()))
        if pair not in pairs:
            pairs.append(pair)
    for col, pair in zip(range(32, 56), pairs[:24]):
        h[list(pair), col] = 1
    # Rows 32..39 get their non-pivot incidence from late pivot columns.  The
    # tail columns cover rows 40..55, with two early supports retained so they
    # remain distinct and nonzero at every requested prefix.
    for col, row in zip(range(48, 56), 32 + rng.permutation(8)):
        h[int(row), col] = 1
    for col, pair, late in zip(range(56, 64), pairs[24:], (40 + rng.permutation(16)).reshape(8, 2)):
        h[list(pair), col] = 1; h[late, col] = 1
    _validate_master(h)
    return h


def _four_cycles(h: np.ndarray) -> int:
    overlap = np.asarray(h, dtype=np.int64).T @ np.asarray(h, dtype=np.int64)
    return int(np.sum(overlap[np.triu_indices(overlap.shape[0], 1)] * (overlap[np.triu_indices(overlap.shape[0], 1)] - 1) // 2))


def _all_low_weight_errors() -> tuple[np.ndarray, np.ndarray]:
    one = np.eye(N, dtype=np.uint8)
    two = np.zeros((N * (N - 1) // 2, N), dtype=np.uint8); index = 0
    for left in range(N):
        for right in range(left + 1, N):
            two[index, left] = two[index, right] = 1; index += 1
    return one, two


_WEIGHT1, _WEIGHT2 = _all_low_weight_errors()


def _collision_count(h: np.ndarray, errors: np.ndarray) -> int:
    syndromes = (errors @ h.T % 2).astype(np.uint8)
    packed = np.packbits(syndromes, axis=1, bitorder="big")
    _, counts = np.unique(packed, axis=0, return_counts=True)
    return int(np.sum(counts * (counts - 1) // 2))


def probe_errors(plane_id: int, rate_id: str) -> np.ndarray:
    if rate_id not in RATES:
        raise ValueError("unknown prefix rate")
    rng = np.random.Generator(np.random.PCG64(_seed(f"probe/{rate_id}", plane_id)))
    singles = rng.choice(N, size=32, replace=False)
    errors = np.zeros((PROBE_COUNT, N), dtype=np.uint8)
    errors[np.arange(32), singles] = 1
    pairs = set()
    while len(pairs) < 32:
        left, right = sorted(rng.choice(N, size=2, replace=False).tolist())
        pairs.add((left, right))
    for row, (left, right) in enumerate(sorted(pairs), start=32):
        errors[row, left] = errors[row, right] = 1
    return errors


def _validate_master(h: np.ndarray) -> None:
    if np.asarray(h).shape != (56, N) or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid master dimensions")
    for m in PREFIX_ROWS:
        prefix = h[:m]
        metrics = structural_metrics(prefix, probe=np.zeros((PROBE_COUNT, N), dtype=np.uint8))
        if metrics["rank"] != m or metrics["zero_columns"] or metrics["duplicate_columns"] or not (2 <= metrics["row_weight_min"] <= metrics["row_weight_max"] <= 8) or not (1 <= metrics["column_weight_min"] <= metrics["column_weight_max"] <= 4):
            raise ValueError(f"master violates frozen prefix constraints at {m}: {metrics}")


def structural_metrics(h: np.ndarray, *, probe: np.ndarray) -> dict[str, Any]:
    matrix = np.asarray(h, dtype=np.uint8)
    if matrix.ndim != 2 or matrix.shape[1] != N:
        raise ValueError("invalid prefix matrix")
    if np.asarray(probe).shape != (PROBE_COUNT, N):
        raise ValueError("invalid fixed probe errors")
    row_weights = matrix.sum(axis=1); column_weights = matrix.sum(axis=0)
    cols = [bytes(matrix[:, column]) for column in range(N)]
    duplicate = N - len(set(cols))
    c1, c2 = _collision_count(matrix, _WEIGHT1), _collision_count(matrix, _WEIGHT2)
    probe_syndromes = (np.asarray(probe, dtype=np.uint8) @ matrix.T % 2).astype(np.uint8)
    # This is a structural proxy: count probes whose syndrome is unique over
    # the exhaustive weight-1/2 error universe, not merely within 64 probes.
    universe = np.vstack((_WEIGHT1, _WEIGHT2))
    packed_universe = np.packbits((universe @ matrix.T % 2).astype(np.uint8), axis=1, bitorder="big")
    _, inverse, counts = np.unique(packed_universe, axis=0, return_inverse=True, return_counts=True)
    lookup = {bytes(key): int(count) for key, count in zip(*np.unique(packed_universe, axis=0, return_counts=True))}
    unique_count = sum(lookup.get(bytes(value), 0) == 1 for value in np.packbits(probe_syndromes, axis=1, bitorder="big"))
    return {"rank": gf2_rank(matrix), "zero_columns": int(np.count_nonzero(column_weights == 0)),
            "duplicate_columns": int(duplicate), "row_weight_min": int(row_weights.min()), "row_weight_max": int(row_weights.max()),
            "column_weight_min": int(column_weights.min()), "column_weight_max": int(column_weights.max()),
            "four_cycles": _four_cycles(matrix), "weight1_syndrome_collisions": c1, "weight2_syndrome_collisions": c2,
            "probe_count": PROBE_COUNT, "probe_unique_syndrome_count": int(unique_count),
            "probe_errors_sha256": sha256_bytes(np.asarray(probe, dtype=np.uint8).tobytes(order="C"))}


def screen_candidate(plane_id: int, candidate_id: int) -> dict[str, Any]:
    master = generate_master(plane_id, candidate_id); prefixes: dict[str, Any] = {}
    valid = True
    for rate_id, m in zip(PREFIX_RATES, PREFIX_ROWS):
        h, probe = master[:m].copy(), probe_errors(plane_id, rate_id)
        metrics = structural_metrics(h, probe=probe)
        valid = valid and metrics["rank"] == m and metrics["zero_columns"] == 0 and metrics["duplicate_columns"] == 0 and metrics["row_weight_min"] >= 2 and metrics["row_weight_max"] <= 8 and metrics["column_weight_min"] >= 1 and metrics["column_weight_max"] <= 4
        raw = canonical_matrix_bytes(h)
        prefixes[rate_id] = {"m_checks": m, "metrics": metrics, "sha256": sha256_bytes(raw), "canonical_bytes_sha256": sha256_bytes(raw)}
    score = [-(sum(item["metrics"]["probe_unique_syndrome_count"] for item in prefixes.values())),
             sum(item["metrics"]["weight1_syndrome_collisions"] + item["metrics"]["weight2_syndrome_collisions"] for item in prefixes.values()),
             sum(item["metrics"]["four_cycles"] for item in prefixes.values()),
             max(item["metrics"]["row_weight_max"] for item in prefixes.values()), candidate_id]
    return {"plane_id": plane_id, "candidate_id": candidate_id, "generator_id": GENERATOR_ID, "generator_version": GENERATOR_VERSION,
            "master_seed_hex": _seed_hex("master", plane_id, candidate_id), "valid": bool(valid), "prefixes": prefixes, "selection_score": score}


def screening_manifest() -> dict[str, Any]:
    policy = {"selection": "lexicographic", "score": ["-probe_unique_syndrome_count", "weight1_plus_weight2_syndrome_collisions", "four_cycles", "max_row_weight", "candidate_id"],
              "candidates_per_plane": CANDIDATES_PER_PLANE, "prefix_rows": list(PREFIX_ROWS), "probe": "PCG64 domain-separated 32 weight-1 then 32 weight-2"}
    planes = []
    for plane_id in range(10):
        candidates = [screen_candidate(plane_id, candidate_id) for candidate_id in range(CANDIDATES_PER_PLANE)]
        valid = [row for row in candidates if row["valid"]]
        if not valid:
            raise ValueError("no structurally valid candidate")
        selected = min(valid, key=lambda row: tuple(row["selection_score"]))["candidate_id"]
        for row in candidates:
            row["selected"] = row["candidate_id"] == selected
        planes.append({"plane_id": plane_id, "candidates": candidates, "selected_candidate_id": selected})
    base = {"generator_id": GENERATOR_ID, "generator_version": GENERATOR_VERSION, "selection_policy": policy,
            "selection_policy_sha256": sha256_bytes(_compact(policy)), "planes": planes}
    manifest = {**base, "manifest_sha256": sha256_bytes(_compact(base))}
    _VERIFIED_SCREENING_DIGESTS.add(sha256_bytes(_compact(manifest)))
    return manifest


def verify_screening_manifest(manifest: Mapping[str, Any]) -> None:
    """Fail closed unless this is the complete deterministic screening audit."""
    supplied = dict(manifest)
    digest = supplied.pop("manifest_sha256", None)
    if not isinstance(digest, str) or digest != sha256_bytes(_compact(supplied)):
        raise ValueError("screening manifest hash mismatch")
    expected = screening_manifest()
    if supplied != {key: value for key, value in expected.items() if key != "manifest_sha256"}:
        raise ValueError("screening manifest does not match deterministic construction")


def codebook_filename(rate_id: str, plane_id: int) -> str:
    if rate_id not in RATES or not isinstance(plane_id, int) or not 0 <= plane_id < 10:
        raise ValueError("unknown codebook identity")
    return f"formal_v2_codebook_n64_{rate_id}_plane{plane_id:02d}.hgf2v1"


def materialize_selected_codebooks(fresh_run_dir: Path, *, manifest: Mapping[str, Any] | None = None,
        allow_plan_only: bool = False, manifest_filename: str = "formal_v2_codebook_manifest.json") -> dict[str, Any]:
    root = Path(fresh_run_dir)
    if root.exists():
        names = {item.name for item in root.iterdir()}
        if names and (not allow_plan_only or names != {"pre_run_plan.json"}):
            raise FileExistsError("formal v2 codebook run directory must be fresh or plan-only")
    else:
        root.mkdir(parents=True)
    manifest = dict(screening_manifest() if manifest is None else manifest)
    verify_screening_manifest(manifest)
    book = root / "codebooks"; book.mkdir()
    entries = []
    for plane in manifest.get("planes", []):
        plane_id, candidate_id = int(plane["plane_id"]), int(plane["selected_candidate_id"])
        candidate = generate_master(plane_id, candidate_id)
        for rate_id, m in zip(PREFIX_RATES, PREFIX_ROWS):
            raw = canonical_matrix_bytes(candidate[:m]); name = codebook_filename(rate_id, plane_id); path = book / name
            with path.open("xb") as handle: handle.write(raw)
            entries.append({"filename": name, "rate_id": rate_id, "plane_id": plane_id, "m_checks": m, "n": N, "rank": gf2_rank(candidate[:m]), "sha256": sha256_bytes(raw), "selected_candidate_id": candidate_id})
    if len(entries) != 40:
        raise ValueError("screening manifest must select ten plane families")
    result = {"screening_manifest": manifest, "entries": entries}
    if Path(manifest_filename).name != manifest_filename:
        raise ValueError("codebook manifest filename must be a basename")
    with (root / manifest_filename).open("x", encoding="utf-8") as handle: handle.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return result


def verify_selected_codebooks(run_dir: Path, manifest: Mapping[str, Any]) -> None:
    root = Path(run_dir).resolve(); book = (root / "codebooks").resolve()
    if book.parent != root or not isinstance(manifest.get("entries"), list) or len(manifest["entries"]) != 40:
        raise ValueError("invalid selected codebook manifest")
    seen = set(); matrices: dict[tuple[str, int], np.ndarray] = {}
    for entry in manifest["entries"]:
        rate, plane = str(entry.get("rate_id")), int(entry.get("plane_id", -1)); name = codebook_filename(rate, plane)
        if entry.get("filename") != name or (rate, plane) in seen:
            raise ValueError("duplicate or unsafe selected codebook identity")
        seen.add((rate, plane)); path = (book / name).resolve()
        if path.parent != book or not path.is_file():
            raise ValueError("codebook path traversal or missing file")
        raw = path.read_bytes(); h = parse_matrix_bytes(raw)
        if entry.get("sha256") != sha256_bytes(raw) or (entry.get("m_checks"), entry.get("n"), entry.get("rank")) != (h.shape[0], N, gf2_rank(h)):
            raise ValueError("selected codebook hash or metadata mismatch")
        matrices[(rate, plane)] = h
    if seen != {(rate, plane) for rate in PREFIX_RATES for plane in range(10)}:
        raise ValueError("incomplete selected codebook set")
    for plane in range(10):
        master = matrices[("r0125", plane)]
        for rate, m in zip(PREFIX_RATES, PREFIX_ROWS):
            if not np.array_equal(matrices[(rate, plane)], master[:m]):
                raise ValueError("selected matrices are not row-prefix nested")


def verify_v2_codebook_entry(entry: Mapping[str, Any], raw: bytes,
        screening_manifest: Mapping[str, Any]) -> np.ndarray:
    """Validate one selected v2 entry without consulting the v1 codebook path."""
    screening_digest = sha256_bytes(_compact(dict(screening_manifest)))
    if screening_digest not in _VERIFIED_SCREENING_DIGESTS:
        verify_screening_manifest(screening_manifest)
        _VERIFIED_SCREENING_DIGESTS.add(screening_digest)
    try:
        rate, plane = str(entry["rate_id"]), int(entry["plane_id"])
        candidate_id = int(entry["selected_candidate_id"])
        name = codebook_filename(rate, plane)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid v2 codebook identity") from exc
    if entry.get("filename") != name or rate not in PREFIX_RATES or not 0 <= plane < 10:
        raise ValueError("v2 codebook filename or identity mismatch")
    h = parse_matrix_bytes(raw)
    expected_rows = RATES[rate]
    if h.shape != (expected_rows, N) or gf2_rank(h) != expected_rows:
        raise ValueError("v2 codebook matrix shape or rank mismatch")
    if canonical_matrix_bytes(h) != raw or entry.get("sha256") != sha256_bytes(raw):
        raise ValueError("v2 codebook canonical bytes or hash mismatch")
    planes = screening_manifest.get("planes", [])
    if not isinstance(planes, list) or plane >= len(planes):
        raise ValueError("v2 screening plane missing")
    selected = planes[plane]
    if selected.get("plane_id") != plane or selected.get("selected_candidate_id") != candidate_id:
        raise ValueError("v2 selected candidate mismatch")
    master = generate_master(plane, candidate_id)
    if not np.array_equal(h, master[:expected_rows]):
        raise ValueError("v2 codebook is not selected master prefix")
    if (entry.get("m_checks"), entry.get("n"), entry.get("rank")) != (expected_rows, N, expected_rows):
        raise ValueError("v2 entry metadata mismatch")
    return h
