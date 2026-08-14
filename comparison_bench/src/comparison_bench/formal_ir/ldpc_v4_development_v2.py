"""Versioned v4 development evaluator with the pinned backend boundary fix."""
from __future__ import annotations

import time
from typing import Any, Mapping, Sequence

import numpy as np

from ..utils.bitops import symbols_to_bits
from .codebook_v4 import CANDIDATE_IDS, PLANE_IDS, candidate_entry, matrix_for
from .ldpc_v4_channel import DIMENSION, FRAME_LEN, plane_error_channel
from . import ldpc_v4_development as v1

ROLE = v1.ROLE
FRAME_COUNT = v1.FRAME_COUNT
STRATA = v1.STRATA
READINESS_FLOOR = v1.READINESS_FLOOR
_STATUSES = v1._STATUSES
_FORBIDDEN = v1._FORBIDDEN
canonical_development_policy = v1.canonical_development_policy
generate_sacrificed_development = v1.generate_sacrificed_development
select_candidates = v1.select_candidates
aggregate_frame_development = v1.aggregate_frame_development


def evaluate_candidate(alice_frames: Any, bob_frames: Any, *, model: Mapping[str, Any], plane_id: int,
                       candidate_id: int, stratum: str, frame_ids: Sequence[str], decoder_factory: Any = None,
                       max_runtime_s: float | None = None, _clock: Any = time.perf_counter) -> list[dict[str, Any]]:
    """Evaluate the frozen grid; only the constructor-boundary type differs from v1."""
    model_sha = v1._model_sha(model)
    if plane_id not in PLANE_IDS or candidate_id not in CANDIDATE_IDS or stratum not in STRATA:
        raise ValueError("development candidate identity")
    if max_runtime_s is not None and (not isinstance(max_runtime_s, (int, float)) or isinstance(max_runtime_s, bool) or float(max_runtime_s) < 0):
        raise ValueError("development runtime cap")
    alice, bob = np.asarray(alice_frames), np.asarray(bob_frames)
    if (alice.shape != (FRAME_COUNT, FRAME_LEN) or bob.shape != (FRAME_COUNT, FRAME_LEN)
            or not np.issubdtype(alice.dtype, np.integer) or not np.issubdtype(bob.dtype, np.integer)
            or np.any(alice < 0) or np.any(alice >= DIMENSION) or np.any(bob < 0) or np.any(bob >= DIMENSION)):
        raise ValueError("development frame arrays")
    expected_ids = [f"v4dev_{stratum}_f{index:03d}" for index in range(FRAME_COUNT)]
    if list(frame_ids) != expected_ids:
        raise ValueError("development frame IDs")
    entry = candidate_entry(plane_id, candidate_id)
    policy = canonical_development_policy(); factory, backend, backend_status = v1._backend(decoder_factory)
    common = {"role": ROLE, "stratum_id": stratum, "plane_id": plane_id, "candidate_id": candidate_id,
              "channel_model_sha256": model_sha, "policy_sha256": policy["policy_sha256"],
              "matrix_sha256": entry["canonical_bytes_sha256"], "candidate_valid": entry["valid"], "backend_identity": backend}
    if factory is None:
        return [{**common, "frame_id": frame_id, "attempted": False, "status": backend_status,
                 "exact_match": False, "syndrome_bits_disclosed": 0, "runtime_s": 0.0} for frame_id in expected_ids]
    h = matrix_for(plane_id, candidate_id)
    a_bits = symbols_to_bits(alice.astype(np.int64), DIMENSION, "gray")[:, :, plane_id]
    b_bits = symbols_to_bits(bob.astype(np.int64), DIMENSION, "gray")[:, :, plane_id]
    kwargs = {key: policy[key] for key in ("max_iter", "bp_method", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order")}
    results: list[dict[str, Any]] = []
    for frame_id, a, b, bob_symbols in zip(expected_ids, a_bits, b_bits, bob):
        started = _clock(); status = "development_decode_failed"; exact = False
        if max_runtime_s is not None and _clock() - started >= float(max_runtime_s):
            status = "development_timeout"
        else:
            try:
                # Sole production semantic correction: the pinned constructor requires list.
                error_channel = np.asarray(plane_error_channel(bob_symbols, plane_id, stratum, model), dtype=np.float64).tolist()
                decoded = np.asarray(factory(h, error_channel=error_channel, **kwargs).decode(v1._syndrome(h, a) ^ v1._syndrome(h, b))).reshape(-1)
                if decoded.size != FRAME_LEN or np.any((decoded != 0) & (decoded != 1)):
                    status = "development_malformed_output"
                else:
                    decoded = decoded.astype(np.uint8)
                    if not np.array_equal(v1._syndrome(h, decoded), v1._syndrome(h, a) ^ v1._syndrome(h, b)):
                        status = "development_syndrome_inconsistent"
                    elif np.array_equal(b ^ decoded, a):
                        status = "development_exact_success"; exact = True
            except Exception:
                status = "development_decoder_error"
        elapsed = max(0.0, float(_clock() - started))
        if max_runtime_s is not None and elapsed >= float(max_runtime_s):
            status = "development_timeout"; exact = False
        results.append({**common, "frame_id": frame_id, "attempted": True, "status": status,
                        "exact_match": exact, "syndrome_bits_disclosed": int(h.shape[0]), "runtime_s": elapsed})
    return results
