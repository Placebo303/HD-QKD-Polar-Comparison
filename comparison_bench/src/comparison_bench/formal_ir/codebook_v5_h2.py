"""Deterministic, data-free H2 construction bound to v4 H1 matrices."""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from typing import Any, Mapping, Sequence

import numpy as np

from . import codebook_v4

CONSTRUCTION_ID = "binary_ldpc_v5_h2_cw3_v2"
CONSTRUCTION_VERSION = "2"
STATUS = "candidate_only_not_qualified"
BLOCK_LENGTH = 256
PLANE_IDS = tuple(range(10))
H2_ROW_COUNTS = (16, 16, 16, 24, 24, 32, 48, 80, 88, 48)
TRIAL_BOUND = 1000
MAGIC = b"HGF2V5H2"

def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
def _sha(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def construction_seed(plane_id: int) -> int:
    if plane_id not in PLANE_IDS: raise ValueError("unsupported v5 H2 plane")
    return int.from_bytes(hashlib.sha256(f"{CONSTRUCTION_ID}|plane={plane_id}".encode("ascii")).digest()[:8], "little")
def _supports(h: np.ndarray) -> list[tuple[int, ...]]:
    return [tuple(int(x) for x in np.flatnonzero(h[:, col])) for col in range(BLOCK_LENGTH)]
def _four_cycles(h: np.ndarray) -> int:
    overlap=np.asarray(h,dtype=np.int64).T@np.asarray(h,dtype=np.int64); upper=overlap[np.triu_indices(BLOCK_LENGTH,1)]
    return int(np.sum(upper*(upper-1)//2))
def _h1(value: np.ndarray, plane_id: int) -> np.ndarray:
    h=np.asarray(value,dtype=np.uint8); codebook_v4.canonical_matrix_bytes(h,plane_id=plane_id); return h.copy()
def _validate(h2: np.ndarray,h1: np.ndarray,plane_id: int) -> None:
    h=np.asarray(h2,dtype=np.uint8); e=H2_ROW_COUNTS[plane_id]
    if h.shape!=(e,BLOCK_LENGTH) or np.any((h!=0)&(h!=1)): raise ValueError("invalid v5 H2 matrix")
    if not np.all(h.sum(0,dtype=np.int64)==3) or np.any(h.sum(1,dtype=np.int64)==0): raise ValueError("invalid v5 H2 weights")
    if codebook_v4.gf2_rank(h)!=e: raise ValueError("v5 H2 rank failure")
    stacked=np.vstack((h1,h)).astype(np.uint8)
    if codebook_v4.gf2_rank(stacked)!=stacked.shape[0]-1: raise ValueError("v5 stacked maximal-rank failure")
    if len(set(_supports(stacked)))!=BLOCK_LENGTH: raise ValueError("v5 stacked duplicate support")
@lru_cache(maxsize=128)
def _generated_h2(plane_id: int, h1_bytes: bytes) -> tuple[bytes, int]:
    h1=np.frombuffer(h1_bytes,dtype=np.uint8).reshape(codebook_v4.row_count(plane_id), BLOCK_LENGTH).copy(); e=H2_ROW_COUNTS[plane_id]
    for trial in range(TRIAL_BOUND):
        rng=np.random.Generator(np.random.PCG64(construction_seed(plane_id)+trial)); h2=np.zeros((e,BLOCK_LENGTH),dtype=np.uint8)
        for col in range(BLOCK_LENGTH): h2[np.sort(rng.choice(np.arange(e,dtype=np.int64),size=3,replace=False)),col]=1
        try: _validate(h2,h1,plane_id)
        except ValueError: continue
        return h2.tobytes(order="C"),trial
    raise ValueError("v5 H2 construction exhausted frozen trials")

def generate_h2(plane_id: int,h1: np.ndarray,*,trial_bound: int=TRIAL_BOUND) -> tuple[np.ndarray,int]:
    if plane_id not in PLANE_IDS or trial_bound!=TRIAL_BOUND: raise ValueError("v5 H2 construction trial contract")
    h1=_h1(h1,plane_id)
    raw,trial=_generated_h2(plane_id,h1.tobytes(order="C"))
    return np.frombuffer(raw,dtype=np.uint8).reshape(H2_ROW_COUNTS[plane_id],BLOCK_LENGTH).copy(),trial
def canonical_h2_bytes(matrix: np.ndarray,*,plane_id: int,h1: np.ndarray) -> bytes:
    h1=_h1(h1,plane_id); h2=np.asarray(matrix,dtype=np.uint8); _validate(h2,h1,plane_id)
    return MAGIC+np.asarray([plane_id,H2_ROW_COUNTS[plane_id],BLOCK_LENGTH],dtype="<u4").tobytes()+h2.tobytes(order="C")
def parse_h2_bytes(raw: bytes,*,plane_id: int,h1: np.ndarray) -> np.ndarray:
    if not isinstance(raw,bytes) or raw[:len(MAGIC)]!=MAGIC or len(raw)<len(MAGIC)+12: raise ValueError("invalid HGF2V5H2 header")
    p,rows,cols=np.frombuffer(raw[len(MAGIC):len(MAGIC)+12],dtype="<u4")
    if (int(p),int(rows),int(cols))!=(plane_id,H2_ROW_COUNTS[plane_id],BLOCK_LENGTH) or len(raw)!=len(MAGIC)+12+int(rows)*int(cols): raise ValueError("invalid HGF2V5H2 dimensions")
    h2=np.frombuffer(raw[len(MAGIC)+12:],dtype=np.uint8).reshape(int(rows),int(cols)).copy(); _validate(h2,_h1(h1,plane_id),plane_id); return h2
def _candidate(plane_id: int,h1: np.ndarray) -> dict[str,Any]:
    h2,trial=generate_h2(plane_id,h1); stacked=np.vstack((h1,h2)).astype(np.uint8); rw=h2.sum(1,dtype=np.int64)
    return {"plane_id":plane_id,"construction_seed":construction_seed(plane_id),"accepted_trial":trial,"h2_shape":[H2_ROW_COUNTS[plane_id],BLOCK_LENGTH],"h2_rank":codebook_v4.gf2_rank(h2),"stacked_shape":[int(stacked.shape[0]),BLOCK_LENGTH],"stacked_rank":codebook_v4.gf2_rank(stacked),"h2_column_weight_min":int(h2.sum(0).min()),"h2_column_weight_max":int(h2.sum(0).max()),"h2_row_weight_min":int(rw.min()),"h2_row_weight_max":int(rw.max()),"h2_zero_rows":int(np.count_nonzero(rw==0)),"h2_four_cycles":_four_cycles(h2),"h2_duplicate_column_support_count":BLOCK_LENGTH-len(set(_supports(h2))),"stacked_duplicate_column_support_count":BLOCK_LENGTH-len(set(_supports(stacked))),"canonical_bytes_sha256":_sha(canonical_h2_bytes(h2,plane_id=plane_id,h1=h1))}
def h2_manifest(selected_candidates: Sequence[int],*,h1_codebook_manifest_sha256: str,h1_selection_sha256: str) -> dict[str,Any]:
    if len(selected_candidates)!=10 or any(type(x) is not int for x in selected_candidates): raise ValueError("v5 H1 selection")
    h1=[codebook_v4.matrix_for(p,c) for p,c in enumerate(selected_candidates)]
    base={"schema":"binary_ldpc_v5_h2_manifest_v1","construction_id":CONSTRUCTION_ID,"construction_version":CONSTRUCTION_VERSION,"status":STATUS,"domain":{"block_length":BLOCK_LENGTH,"plane_ids":list(PLANE_IDS),"h2_row_counts":list(H2_ROW_COUNTS),"trial_bound":TRIAL_BOUND,"h1_codebook_manifest_sha256":h1_codebook_manifest_sha256,"h1_selection_sha256":h1_selection_sha256},"candidates":[_candidate(p,h1[p]) for p in PLANE_IDS]}
    return {**base,"manifest_sha256":_sha(_compact(base))}
def verify_h2_manifest(manifest: Mapping[str,Any],selected_candidates: Sequence[int]) -> None:
    supplied=dict(manifest); digest=supplied.pop("manifest_sha256",None)
    if not isinstance(digest,str) or _sha(_compact(supplied))!=digest: raise ValueError("v5 H2 manifest hash mismatch")
    domain=supplied.get("domain",{}); rebuilt=h2_manifest(selected_candidates,h1_codebook_manifest_sha256=domain.get("h1_codebook_manifest_sha256",""),h1_selection_sha256=domain.get("h1_selection_sha256",""))
    if dict(manifest)!=rebuilt: raise ValueError("v5 H2 manifest reconstruction mismatch")
