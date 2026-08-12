"""Covered QC/PEG-like, row-layered q=1024 candidate for formal NBLDPC v3.

This module is deliberately in-memory: it has no qualification output or Alice
truth input.  Qualification mechanics live in ``nonbinary_v3_qualification``.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import asdict
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _fwht, _normalise, _result,
                             _symbols, nonbinary_syndrome, qsc_symbol_priors)

METHOD = "nbldpc_formal_v3"
_Q, _N, _Z = 1024, 64, 8
_CHECKS = (24, 32, 40, 48)
_SEED, _MAX_ITER, _MAX_BYTES, _CAP = 2026072803, 12, 24 * 1024 * 1024, 30.0
_SHIFT_DIRECTION = "col=8*b+((i+shift)%8)"
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC3|coef|1024|2026072803|{salt}|{a}|{b}')), 'big') mod 1023"
_MASKS = ((0,1,2,3,4,5), (0,1,2,3,6,7), (0,1,4,5,6,7), (0,2,4,6), (1,3,5,7), tuple(range(8)))
_SHIFTS = ((2,7,7,5,1,7), (5,5,1,6,0,2), (2,3,4,1,3,3), (0,1,4,4), (5,2,1,1), (0,4,2,6,0,3,2,6))
CANDIDATE_IDS = ("nbldpc_formal_v3_layered_l050", "nbldpc_formal_v3_layered_l075")

def _compact(x: Any) -> bytes: return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def _sha(x: bytes) -> str: return hashlib.sha256(x).hexdigest()

def _coefficient(salt: int, row: int, col: int) -> int:
    text = f"NBLDPC3|coef|1024|{_SEED}|{salt}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023

def _mother(salt: int) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for a, (mask, shifts) in enumerate(zip(_MASKS, _SHIFTS)):
        for i in range(_Z):
            row = [0] * _N
            for b, shift in zip(mask, shifts): row[_Z*b + ((i + shift) % _Z)] = _coefficient(salt, a, b)
            rows.append(tuple(row))
    return tuple(rows)

def _coefficient_table(salt: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(_coefficient(salt, a, b) for b in mask) for a, mask in enumerate(_MASKS))

def _cycles(matrix: tuple[tuple[int, ...], ...]) -> int:
    supports = [set(i for i, x in enumerate(r) if x) for r in matrix]
    return sum(1 for i in range(len(supports)) for j in range(i) if len(supports[i] & supports[j]) >= 2)

def _degrees(matrix: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    return tuple(sum(row[c] != 0 for row in matrix) for c in range(_N))

def _pair_proxy(matrix: tuple[tuple[int, ...], ...], field: GF2mField) -> bool:
    for left in range(_N):
        a = tuple(row[left] for row in matrix)
        if not any(a): return False
        for right in range(left + 1, _N):
            b = tuple(row[right] for row in matrix)
            if tuple(x != 0 for x in a) != tuple(x != 0 for x in b): continue
            pivot = next(i for i, x in enumerate(a) if x)
            ratio = field.mul(b[pivot], field.inverse(a[pivot]))
            if all(field.mul(x, ratio) == y for x, y in zip(a, b)): return False
    return True

def _check_update_qspa(extrinsics: list[np.ndarray], coefficients: list[int], target: int,
                       syndrome: int, field: GF2mField) -> np.ndarray | None:
    """One exact coefficient-aware XOR-domain check update, shared with q=4 tests."""
    q=field.q; spectra=[]
    for message, coefficient in zip(extrinsics,coefficients):
        scaled=np.empty(q)
        for symbol in range(q):scaled[field.mul(coefficient,symbol)]=message[symbol]
        spectra.append(_fwht(scaled))
    product=np.ones(q)
    for index,spectrum in enumerate(spectra):
        if index!=target:product*=spectrum
    convolved=_fwht(product)/q; coefficient=coefficients[target]
    return _normalise(np.array([convolved[syndrome^field.mul(coefficient,s)] for s in range(q)]))

def _row_extrinsic(prior: np.ndarray, variable_edges: list[tuple[int, int]],
                   messages: Mapping[tuple[int, int], np.ndarray], current: tuple[int, int]) -> np.ndarray | None:
    """Exact product of the prior and all stored *other* check messages.

    It is deliberately a small helper so tests can prove that row r+1 reads a
    message written by row r; it does not change the layered decoder contract.
    """
    value = prior.copy()
    for edge in variable_edges:
        if edge != current: value *= messages[edge]
    return _normalise(value)

def _bytes(field: GF2mField, salt: int, matrices: Mapping[int, tuple[tuple[int, ...], ...]]) -> bytes:
    header = {"canonical_schema":"NBLDPC3","construction_seed":_SEED,"accepted_salt":salt,
              "q":_Q,"n":_N,"z":_Z,"base_masks":[list(x) for x in _MASKS],
              "shifts":[list(x) for x in _SHIFTS],"shift_direction":_SHIFT_DIRECTION,
              "coefficient_derivation":_COEFFICIENT_DERIVATION,"coefficient_table":[list(x) for x in _coefficient_table(salt)],
              "prefixes":list(_CHECKS),"field":asdict(field.spec)}
    out = bytearray(b"NBLDPC3\n" + _compact(header) + b"\n")
    for checks in _CHECKS:
        for row in matrices[checks]:
            for x in row: out.extend(int(x).to_bytes(2, "big"))
    return bytes(out)

def _find() -> tuple[int, dict[int, tuple[tuple[int, ...], ...]], GF2mField]:
    field = GF2mField.create(_Q)
    for salt in range(65536):
        mother = _mother(salt); matrices = {c: mother[:c] for c in _CHECKS}
        if all(gf_rank(matrices[c], field) == c and _cycles(matrices[c]) == 0 and min(_degrees(matrices[c])) >= 2 and _pair_proxy(matrices[c], field) for c in _CHECKS):
            return salt, matrices, field
    raise ValueError("codebook_invalid")

def build_nbldpc_v3_codebook(*, construction_seed: int = _SEED) -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    if isinstance(construction_seed, bool) or not isinstance(construction_seed, Integral) or int(construction_seed) != _SEED: raise ValueError("construction_seed is fixed for nbldpc_formal_v3")
    salt, matrices, field = _find()
    entries = [{"check_count":c,"rank":gf_rank(matrices[c],field),"cycle_count":_cycles(matrices[c]),
                "column_degrees":list(_degrees(matrices[c])),"pair_proxy_passed":_pair_proxy(matrices[c],field)} for c in _CHECKS]
    canonical = _bytes(field, salt, matrices)
    payload = {"method":METHOD,"canonical_schema":"NBLDPC3","canonical_magic":"NBLDPC3\\n","q":_Q,"n":_N,"z":_Z,
               "construction_seed":_SEED,"accepted_salt":salt,"base_masks":[list(x) for x in _MASKS],"shifts":[list(x) for x in _SHIFTS],"shift_direction":_SHIFT_DIRECTION,
               "coefficient_derivation":_COEFFICIENT_DERIVATION,"coefficient_table":[list(x) for x in _coefficient_table(salt)],
               "field":asdict(field.spec),"field_id":field.spec.field_id,"check_counts":list(_CHECKS),"ordered_entries":entries,
               "canonical_sha256":_sha(canonical),"canonical_byte_length":len(canonical)}
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices

def verify_nbldpc_v3_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    try:
        expected, expected_matrices = build_nbldpc_v3_codebook()
        supplied = {c:tuple(tuple(int(x) for x in r) for r in matrices[c]) for c in _CHECKS}
        if dict(manifest) != expected or tuple(matrices.keys()) != _CHECKS or supplied != expected_matrices: raise ValueError("deterministic reconstruction mismatch")
        return {"status":"ok","method":METHOD,"manifest_id":expected["manifest_id"],"check_counts":list(_CHECKS)}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError): return {"status":"codebook_invalid","method":METHOD}

def decode_nbldpc_v3(candidate_id: str, bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any], matrices: Mapping[int, Any], *, check_count: int, p: float, max_iter: int = _MAX_ITER) -> dict[str, Any]:
    """Public-input-only ascending-row layered FFT-QSPA."""
    if candidate_id not in CANDIDATE_IDS: return dict(_result("invalid_input", reason="candidate_id"), supplied_candidate_id=candidate_id)
    started = time.monotonic(); lam = .50 if candidate_id.endswith("l050") else .75
    def done(r: Mapping[str, Any]) -> dict[str, Any]:
        if time.monotonic()-started > _CAP: r=_result("aborted_resource_limit",q=r.get("q"),n=r.get("n"),check_count=r.get("check_count"),iterations=int(r.get("iterations",0)),reason="decoder_call_seconds")
        return dict(r,candidate_id=candidate_id)
    if isinstance(check_count,bool) or not isinstance(check_count,Integral) or int(check_count) not in _CHECKS: return done(_result("invalid_input",q=_Q,reason="check_count"))
    if isinstance(max_iter,bool) or not isinstance(max_iter,Integral) or not 1<=int(max_iter)<=_MAX_ITER: return done(_result("aborted_resource_limit",q=_Q,check_count=int(check_count),reason="max_iter"))
    if verify_nbldpc_v3_codebook(manifest,matrices)["status"] != "ok": return done(_result("codebook_invalid",q=_Q,check_count=int(check_count),reason="preflight"))
    try:
        check_count=int(check_count); field=GF2mField.create(_Q); bob=_symbols(bob_symbols,_Q,expected=_N); syn=_symbols(syndrome,_Q,expected=check_count); priors=qsc_symbol_priors(bob,_Q,p)
        matrix=matrices[check_count]; checks=[tuple((c,x) for c,x in enumerate(row) if x) for row in matrix]
        if any(len(x)>8 for x in checks): return done(_result("aborted_resource_limit",q=_Q,n=_N,check_count=check_count,reason="row_weight"))
        edge_count=sum(map(len,checks)); declared=_declared_dense_bytes(_N,edge_count,_Q)
        if declared>_MAX_BYTES:return done(_result("aborted_resource_limit",q=_Q,n=_N,check_count=check_count,declared_dense_message_bytes=declared,reason="dense_message_storage"))
        vedges=[[] for _ in range(_N)]; cmsg={}; belief=[priors[v].copy() for v in range(_N)]
        for r,edges in enumerate(checks):
            for v,_ in edges: vedges[v].append((r,v));cmsg[r,v]=np.full(_Q,1/_Q)
        for it in range(1,int(max_iter)+1):
            for r,edges in enumerate(checks):
                if time.monotonic()>started+_CAP:return done(_result("aborted_resource_limit",q=_Q,n=_N,check_count=check_count,iterations=it-1,declared_dense_message_bytes=declared,reason="decoder_call_seconds"))
                extr=[]
                for v,a in edges:
                    x=_row_extrinsic(priors[v],vedges[v],cmsg,(r,v))
                    if x is None:return done(_result("decoder_error",q=_Q,n=_N,check_count=check_count,iterations=it,reason="extrinsic_normalisation"))
                    extr.append(x)
                for target,(v,a) in enumerate(edges):
                    fresh=_check_update_qspa(extr,[coef for _,coef in edges],target,syn[r],field)
                    if fresh is None:return done(_result("decoder_error",q=_Q,n=_N,check_count=check_count,iterations=it,reason="check_message_normalisation"))
                    new=_normalise(lam*fresh+(1-lam)*cmsg[r,v])
                    if new is None:return done(_result("decoder_error",q=_Q,n=_N,check_count=check_count,iterations=it,reason="damping_normalisation"))
                    cmsg[r,v]=new; b=extr[target]*new; b=_normalise(b)
                    if b is None:return done(_result("decoder_error",q=_Q,n=_N,check_count=check_count,iterations=it,reason="belief_normalisation"))
                    belief[v]=b
            decoded=tuple(int(np.argmax(belief[v])) for v in range(_N))
            if nonbinary_syndrome(matrix,decoded,field)==syn:return done(_result("syndrome_consistent",q=_Q,n=_N,check_count=check_count,iterations=it,syndrome_consistent=True,codebook_id=manifest["canonical_sha256"],declared_dense_message_bytes=declared,decoded_symbols=decoded))
        return done(_result("decode_failed",q=_Q,n=_N,check_count=check_count,iterations=int(max_iter),declared_dense_message_bytes=declared,reason="iteration_limit"))
    except (ArithmeticError,FloatingPointError,KeyError,TypeError,ValueError,OverflowError): return done(_result("decoder_error",q=_Q,n=_N,check_count=int(check_count),reason="numerical_or_field_failure"))
