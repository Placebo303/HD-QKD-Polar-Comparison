"""Pure candidate-only contracts for the additive ``nbldpc_formal_v2`` lane.

No plan, qualification output, Alice truth, or filesystem operation lives here.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import time
from dataclasses import asdict
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_codebook import build_nonbinary_codebook_family, gf_rank, verify_nonbinary_codebook_family
from .nonbinary_field import GF2mField, get_field_spec
from .nonbinary_qspa import (_declared_dense_bytes, _fwht, _normalise, _result, _symbols,
                             nonbinary_syndrome, qsc_symbol_priors, decode_nonbinary_fft_qspa)

METHOD = "nbldpc_formal_v2"
_MAGIC = b"NBLDPC2\n"
_N, _INFO, _ROWS, _Q = 64, 16, 48, 1024
_CHECKS = (24, 32, 40, 48)
_SEED, _MAX_ITER, _MAX_BYTES = 2026072602, 20, 16 * 1024 * 1024
_CALL_CAP_SECONDS = 20.0
CANDIDATE_IDS = (
    "nbldpc_formal_v2_control_n1_flooding",
    "nbldpc_formal_v2_qc48_flooding",
    "nbldpc_formal_v2_qc48_damped_l050",
    "nbldpc_formal_v2_qc48_damped_l050_tempered_t080",
)


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or not 0 <= int(value) < 2**64:
        raise ValueError("construction_seed must be a non-boolean integer in [0, 2^64)")
    return int(value)


def _factorization() -> tuple[tuple[tuple[int, int], ...], ...]:
    """The exact lexicographically ordered K16 one-factorization."""
    rounds = []
    for round_index in range(15):
        edges = [(15, round_index)] + [((round_index + offset) % 15, (round_index - offset) % 15)
                                      for offset in range(1, 8)]
        rounds.append(tuple(sorted(tuple(sorted(edge)) for edge in edges)))
    return tuple(rounds)


def _round_permutation(seed: int) -> tuple[int, ...]:
    values = list(range(15))
    for index in range(14, 0, -1):
        text = f"NBLDPC2|roundperm|{seed}|{index}".encode("ascii")
        swap = int.from_bytes(hashlib.sha256(text).digest(), "big") % (index + 1)
        values[index], values[swap] = values[swap], values[index]
    return tuple(values)


def _pairs(seed: int) -> tuple[tuple[int, ...], tuple[int, ...], tuple[tuple[int, int], ...]]:
    rounds = _factorization()
    permutation = _round_permutation(seed)
    selected = permutation[:6]
    matchings = tuple(rounds[index] for index in selected)
    for rotation in itertools.product(range(8), repeat=6):
        rotated = tuple(matching[offset:] + matching[:offset] for matching, offset in zip(matchings, rotation))
        if all(set(rotated[index][-1]).isdisjoint(rotated[(index + 1) % 6][0]) for index in range(6)):
            return selected, tuple(rotation), tuple(edge for matching in rotated for edge in matching)
    raise ValueError("codebook_invalid")


def _coefficient(seed: int, row: int, slot: int) -> int:
    value = f"NBLDPC2|coef|1024|{seed}|{row}|{slot}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(value).digest(), "big") % 1023


def _mother(field: GF2mField, seed: int, pairs: tuple[tuple[int, int], ...]) -> tuple[tuple[int, ...], ...]:
    rows = []
    for row, pair in enumerate(pairs):
        values = [0] * _N
        values[pair[0]], values[pair[1]] = _coefficient(seed, row, 0), _coefficient(seed, row, 1)
        values[_INFO + row] = 1
        values[_INFO + ((row + 1) % _ROWS)] = 2
        rows.append(tuple(values))
    return tuple(rows)


def _cycles(matrix: tuple[tuple[int, ...], ...]) -> int:
    supports = [set(index for index, value in enumerate(row) if value) for row in matrix]
    return sum(1 for left in range(len(supports)) for right in range(left + 1, len(supports))
               if len(supports[left] & supports[right]) >= 2)


def _header(field: GF2mField, checks: int, seed: int, selected_rounds: tuple[int, ...], rotation: tuple[int, ...], pairs: tuple[tuple[int, int], ...]) -> dict[str, Any]:
    return {"canonical_schema": "NBLDPC2", "coefficient_encoding": "unsigned_16_bit_big_endian",
            "construction_seed": seed, "field": asdict(field.spec), "field_id": field.spec.field_id,
            "information_columns": list(range(_INFO)), "matrix_ordering": "row_major",
            "mother_dimensions": [_ROWS, _N], "n": _N, "selected_rounds": list(selected_rounds), "rotation_vector": list(rotation),
            "q": _Q, "rate_check_count": checks, "selected_information_pairs": [list(x) for x in pairs],
            "topology": "qc48_information_pairs_plus_I48_plus_alpha_P48"}


def _bytes(matrix: tuple[tuple[int, ...], ...], field: GF2mField, checks: int, seed: int, selected_rounds: tuple[int, ...], rotation: tuple[int, ...], pairs: tuple[tuple[int, int], ...]) -> bytes:
    payload = bytearray(_MAGIC + _compact(_header(field, checks, seed, selected_rounds, rotation, pairs)) + b"\n")
    for row in matrix:
        for value in row:
            payload.extend(field._symbol(value).to_bytes(2, "big"))
    return bytes(payload)


def build_nbldpc_v2_codebook(*, construction_seed: int = _SEED) -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Construct the fixed q=1024 QC48 family entirely in memory."""
    seed = _seed(construction_seed)
    if seed != _SEED:
        raise ValueError("construction_seed is fixed for nbldpc_formal_v2")
    field = GF2mField.create(_Q)
    selected_rounds, rotation, pairs = _pairs(seed); mother = _mother(field, seed, pairs)
    matrices = {checks: tuple(mother[:checks]) for checks in _CHECKS}
    entries = [{"check_count": checks, "rank": gf_rank(matrices[checks], field), "cycle_count": _cycles(matrices[checks]),
                "byte_length": len(_bytes(matrices[checks], field, checks, seed, selected_rounds, rotation, pairs)),
                "codebook_id": _sha(_bytes(matrices[checks], field, checks, seed, selected_rounds, rotation, pairs))} for checks in _CHECKS]
    alpha48 = 1
    for _ in range(48): alpha48 = field.mul(alpha48, 2)
    payload = {"method": METHOD, "q": _Q, "n": _N, "construction_seed": seed, "field": asdict(field.spec),
               "field_id": field.spec.field_id, "canonical_magic": "NBLDPC2\\n", "round_permutation": list(_round_permutation(seed)), "selected_rounds": list(selected_rounds), "rotation_vector": list(rotation),
               "selected_information_pairs": [list(pair) for pair in pairs], "alpha": 2, "alpha_power_48": alpha48,
               "parity_block": "I48_plus_alpha_P48", "check_counts": list(_CHECKS), "ordered_entries": entries,
               "prefix_relationship": "each_entry_is_the_exact_ordered_row_prefix_of_the_48x64_mother_matrix"}
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices


def verify_nbldpc_v2_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    """Reconstruct every deterministic QC48 value and reject any mismatch."""
    try:
        seed = _seed(manifest.get("construction_seed"))
        if seed != _SEED:
            raise ValueError("construction_seed mismatch")
        expected, expected_matrices = build_nbldpc_v2_codebook()
        if manifest != expected or tuple(matrices.keys()) != _CHECKS:
            raise ValueError("deterministic reconstruction mismatch")
        supplied = {checks: tuple(tuple(row) for row in matrices[checks]) for checks in _CHECKS}
        if supplied != expected_matrices: raise ValueError("matrix mismatch")
        field = GF2mField.create(_Q)
        if field.nonzero_cycle[0] != 1 or len(field.nonzero_cycle) != 1023 or manifest["alpha_power_48"] == 1:
            raise ValueError("alpha proof")
        parity = tuple(tuple(row[_INFO:] for row in supplied[48]))
        if gf_rank(parity, field) != 48 or any(gf_rank(supplied[c], field) != c or _cycles(supplied[c]) != 0 for c in _CHECKS):
            raise ValueError("rank/cycle")
        return {"status": "ok", "method": METHOD, "manifest_id": expected["manifest_id"], "check_counts": list(_CHECKS)}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}


def decode_nbldpc_v2(candidate_id: str, bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any], matrices: Mapping[int, Any], *, check_count: int, p: float, max_iter: int = 20) -> dict[str, Any]:
    """Bounded public-input-only decoder for the four frozen candidate identities."""
    if candidate_id not in CANDIDATE_IDS:
        return dict(_result("invalid_input", reason="candidate_id"), supplied_candidate_id=candidate_id)
    started = time.monotonic()

    def finish(result: Mapping[str, Any]) -> dict[str, Any]:
        if time.monotonic() - started > _CALL_CAP_SECONDS:
            result = _result("aborted_resource_limit", q=result.get("q"), n=result.get("n"),
                             check_count=result.get("check_count"), iterations=int(result.get("iterations", 0)),
                             declared_dense_message_bytes=int(result.get("declared_dense_message_bytes", 0)),
                             reason="decoder_call_seconds")
        return dict(result, candidate_id=candidate_id)

    if candidate_id == CANDIDATE_IDS[0]:
        result = decode_nonbinary_fft_qspa(bob_symbols, syndrome, manifest, matrices, check_count=check_count, p=p, max_iter=max_iter)
        return finish(result)
    if isinstance(check_count, bool) or not isinstance(check_count, Integral) or int(check_count) not in _CHECKS:
        return finish(_result("invalid_input", q=_Q, reason="check_count"))
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or not 1 <= int(max_iter) <= _MAX_ITER:
        return finish(_result("aborted_resource_limit", q=_Q, check_count=int(check_count), reason="max_iter"))
    verified = verify_nbldpc_v2_codebook(manifest, matrices)
    if verified["status"] != "ok": return finish(_result("codebook_invalid", q=_Q, check_count=int(check_count), reason="QC48 verification"))
    try:
        field = GF2mField.create(_Q); check_count = int(check_count); bob = _symbols(bob_symbols, _Q, expected=_N); disclosed = _symbols(syndrome, _Q, expected=check_count); priors = qsc_symbol_priors(bob, _Q, p)
        matrix = tuple(tuple(int(x) for x in row) for row in matrices[check_count]); checks = [tuple((col, coef) for col, coef in enumerate(row) if coef) for row in matrix]
        if any(len(row) != 4 for row in checks): raise ValueError("row_weight")
        declared = _declared_dense_bytes(_N, check_count * 4, _Q)
        if declared > _MAX_BYTES: return finish(_result("aborted_resource_limit", q=_Q, n=_N, check_count=check_count, declared_dense_message_bytes=declared, reason="dense_message_storage"))
        edge_keys = [(row, col, coef) for row, row_edges in enumerate(checks) for col, coef in row_edges]
        variable_edges = [[] for _ in range(_N)]
        for row, col, _ in edge_keys: variable_edges[col].append((row, col))
        v_to_c = {(row, col): priors[col].copy() for row, col, _ in edge_keys}; c_to_v = {(row, col): np.full(_Q, 1 / _Q) for row, col, _ in edge_keys}
        damped, tempered = candidate_id in CANDIDATE_IDS[2:], candidate_id == CANDIDATE_IDS[3]
        deadline = started + _CALL_CAP_SECONDS
        for iteration in range(1, int(max_iter) + 1):
            next_c = {}
            for row, row_edges in enumerate(checks):
                if time.monotonic() > deadline:
                    return finish(_result("aborted_resource_limit", q=_Q, n=_N, check_count=check_count, iterations=iteration - 1,
                                          declared_dense_message_bytes=declared, reason="decoder_call_seconds"))
                spectra = []
                for col, coef in row_edges:
                    scaled = np.empty(_Q)
                    for symbol in range(_Q): scaled[field.mul(coef, symbol)] = v_to_c[(row, col)][symbol]
                    spectra.append(_fwht(scaled))
                for target, (col, coef) in enumerate(row_edges):
                    product = np.ones(_Q)
                    for other, spectrum in enumerate(spectra):
                        if other != target: product *= spectrum
                    convolved = _fwht(product) / _Q
                    outgoing = np.array([convolved[disclosed[row] ^ field.mul(coef, symbol)] for symbol in range(_Q)])
                    normal = _normalise(outgoing)
                    if normal is None: return finish(_result("decoder_error", q=_Q, n=_N, check_count=check_count, iterations=iteration, reason="check_message_normalisation"))
                    if tempered:
                        normal = _normalise(np.power(normal, .8))
                        if normal is None: return finish(_result("decoder_error", q=_Q, n=_N, check_count=check_count, iterations=iteration, reason="tempering_normalisation"))
                    if damped:
                        normal = _normalise(.5 * normal + .5 * c_to_v[(row, col)])
                        if normal is None: return finish(_result("decoder_error", q=_Q, n=_N, check_count=check_count, iterations=iteration, reason="damping_normalisation"))
                    next_c[(row, col)] = normal
            c_to_v = next_c; beliefs = np.empty((_N, _Q))
            for col in range(_N):
                belief = priors[col].copy()
                for edge in variable_edges[col]: belief *= c_to_v[edge]
                normal = _normalise(belief)
                if normal is None: return finish(_result("decoder_error", q=_Q, n=_N, check_count=check_count, iterations=iteration, reason="belief_normalisation"))
                beliefs[col] = normal
            decoded = tuple(int(np.argmax(beliefs[col])) for col in range(_N))
            if nonbinary_syndrome(matrix, decoded, field) == disclosed:
                return finish(_result("syndrome_consistent", q=_Q, n=_N, check_count=check_count, iterations=iteration, syndrome_consistent=True, codebook_id=manifest["ordered_entries"][_CHECKS.index(check_count)]["codebook_id"], declared_dense_message_bytes=declared, decoded_symbols=decoded))
            v_to_c = {}
            for row, col, _ in edge_keys:
                message = priors[col].copy()
                for other in variable_edges[col]:
                    if other != (row, col): message *= c_to_v[other]
                normal = _normalise(message)
                if normal is None: return finish(_result("decoder_error", q=_Q, n=_N, check_count=check_count, iterations=iteration, reason="variable_message_normalisation"))
                v_to_c[(row, col)] = normal
        return finish(_result("decode_failed", q=_Q, n=_N, check_count=check_count, iterations=int(max_iter), declared_dense_message_bytes=declared, reason="iteration_limit"))
    except (ArithmeticError, FloatingPointError, KeyError, TypeError, ValueError, OverflowError):
        return finish(_result("decoder_error", q=_Q, n=_N, check_count=int(check_count), reason="numerical_or_field_failure"))
