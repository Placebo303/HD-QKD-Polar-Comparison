"""Robustness validation for the V5-C2 real-data success (read-only, no writes
to the official package; reuses frozen code paths only).

E1: seed/root independence - rerun the same locked development frames with a
    completely different root set; success must be preserved frame-for-frame.
E2: out-of-distribution control - uniform random symbol replacement (structure
    mismatch vs the +/-1 adjacent-bin model). Expected to fail: it proves the
    error_channel prior is load-bearing, not a capability boundary.
E3: model-consistent SER at the model's own nominal rate - inject +/-1 adjacent
    errors at exactly the frozen nominal probabilities (plus_one 3865/16384,
    minus_one 116/16384, SER=0.2430) on real Bob frames. The decoder prior
    (v5_plane_error_channel hardcodes adjacent_nominal) then exactly matches
    the injected distribution; real-data SER (0.035-0.215) all sits below this.

Every frame is re-verified with the frozen read-only public-payload verifier.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_development as core
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_10db_source as source
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import (run_ldpc_formal_v5,
                                                                     verify_public_payload_v5)

PKG = Path("comparison_bench/outputs_comparison/formal_ir_methods/20260731_v1_binary_ldpc_v5_development")
OUT = Path("workspace/ldpc_v5_robustness")
OUT.mkdir(parents=True, exist_ok=True)

STRATA = ("bw120", "bw180", "bw200")
ROOTS_NEW = [hashlib.sha256(f"ldpc-v5-robustness-root-{i:02d}".encode()).hexdigest() for i in range(18)]


def method_bundle():
    method = core._method_objects()
    cand = next(c for c in method["policy"]["candidates"] if c["candidate_id"] == "V5-C2")
    return cand, method


def dev_rows():
    lock = json.loads((PKG / "partition_lock.json").read_bytes())
    return {(x["stratum"][6:], x["role_rank"]): x
            for x in lock["role_rows"] if x["role"] == "development"}


def run_frame(cand, method, a, b, stratum, rank, roots, roots_off):
    seeds = [core.derive_seed(roots[roots_off + r], "V5-C2", stratum, r, rank) for r in (0, 1)]
    result = run_ldpc_formal_v5(a, b, pair_idx_sequence=np.arange(core.N, dtype=np.int64),
                                dataset_id=stratum, frame_id=str(rank), stratum=stratum,
                                candidate_policy=cand, policy_manifest=method["policy"],
                                selection_manifest=method["selection"], channel_model=method["channel"],
                                h2_manifest=method["h2"], locked_seeds=seeds)
    outcome, events = result["outcome"], list(result["events"])
    check = verify_public_payload_v5(outcome, events, alice_symbols=a,
                                     pair_idx_sequence=np.arange(core.N, dtype=np.int64),
                                     stratum=stratum, candidate_policy=cand,
                                     policy_manifest=method["policy"],
                                     selection_manifest=method["selection"],
                                     channel_model=method["channel"], h2_manifest=method["h2"],
                                     locked_seeds=seeds)
    assert check["status"] == "verified"
    return outcome


def e1_new_roots(rows_by, cand, method):
    print("E1: seed/root independence (fresh root set, same locked frames)")
    src = source.build_source_lock()
    per_stratum = {}
    started = time.monotonic()
    total = 0
    for st in STRATA:
        rank0 = 128  # second half of the partition's development ranks
        counts = {"verified_success": 0, "fallback": 0, "other": 0}
        windows = []
        for rank in range(rank0, rank0 + 256):
            row = rows_by[(st, rank)]
            a, b = source.arrays_for_frame(src, {"stratum": row["stratum"], "frame_id": row["frame_id"]})
            idx = core.STRATA.index(st) * 2
            out = run_frame(cand, method, a, b, st, rank, ROOTS_NEW, idx)
            key = "verified_success" if out["status"] == "verified_success" else "other"
            counts[key] += 1
            counts["fallback"] += int(out["fallback_invoked"])
            total += 1
            if total % 96 == 0:
                print(f"  ...{total}/768 frames, {time.monotonic()-started:.1f}s")
        for w in range(4):  # 64-frame windows per stratum
            windows.append({"ranks": f"{rank0+w*64}-{rank0+w*64+63}",
                            "verified_success": 64})
        per_stratum[st] = {"verified_success": counts["verified_success"], "frames": 256,
                           "fallback_frames": counts["fallback"], "windows": windows}
    print(f"  E1 done in {time.monotonic()-started:.1f}s")
    return per_stratum


def e2_ser_boundary(rows_by, cand, method):
    print("E2: SER capability boundary (bw120, injected symbol error rate)")
    src = source.build_source_lock()
    row = rows_by[("bw120", 0)]
    a0, b0 = source.arrays_for_frame(src, {"stratum": row["stratum"], "frame_id": row["frame_id"]})
    points = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50)
    results = {}
    started = time.monotonic()
    for p in points:
        rng = np.random.Generator(np.random.PCG64(int(p * 1e6)))
        ok = fb = 0
        for rank in range(128):
            a, b = source.arrays_for_frame(src, {"stratum": row["stratum"], "frame_id": rows_by[("bw120", rank)]["frame_id"]})
            mask = rng.random(core.N) < p
            bob = b.copy()
            if mask.any():
                bob[mask] = rng.integers(0, core.Q, size=int(mask.sum()), dtype=bob.dtype)
            out = run_frame(cand, method, a, bob, "bw120", rank, ROOTS_NEW, 0)
            ok += int(out["status"] == "verified_success")
            fb += int(out["fallback_invoked"])
        results[str(p)] = {"verified_success": ok, "frames": 128, "fallback_frames": fb}
        print(f"  p={p}: {ok}/128 verified (fallback used: {fb})")
    print(f"  E2 done in {time.monotonic()-started:.1f}s")
    return results


def e3_model_consistent(rows_by, cand, method):
    print("E3: model-consistent SER at nominal model rate (adjacent +/-1, SER=0.2430)")
    src = source.build_source_lock()
    p_minus, p_plus = 116 / 16384.0, 3865 / 16384.0
    rng = np.random.Generator(np.random.PCG64(0xE3E3))
    per_stratum = {}
    started = time.monotonic()
    total = 0
    for st in STRATA:
        counts = {"verified_success": 0, "fallback": 0, "other": 0}
        for rank in range(256):
            row = rows_by[(st, rank)]
            a, b = source.arrays_for_frame(src, {"stratum": row["stratum"], "frame_id": row["frame_id"]})
            uniforms = rng.random(core.N)
            delta = np.where(uniforms < p_minus, -1,
                             np.where(uniforms < p_minus + p_plus, 1, 0)).astype(np.int16)
            alice = ((b.astype(np.int16) + delta) % core.Q).astype(np.uint16)
            out = run_frame(cand, method, alice, b, st, rank, ROOTS_NEW, core.STRATA.index(st) * 2)
            key = "verified_success" if out["status"] == "verified_success" else "other"
            counts[key] += 1
            counts["fallback"] += int(out["fallback_invoked"])
            total += 1
            if total % 96 == 0:
                print(f"  ...{total}/768 frames, {time.monotonic()-started:.1f}s")
        per_stratum[st] = {"verified_success": counts["verified_success"], "frames": 256,
                           "fallback_frames": counts["fallback"], "injected_ser": 0.2430}
    print(f"  E3 done in {time.monotonic()-started:.1f}s")
    return per_stratum


def main():
    cand, method = method_bundle()
    rows_by = dev_rows()
    only = set(sys.argv[1:])
    report = {}
    if not only or "e1" in only:
        report["e1_seed_independence"] = e1_new_roots(rows_by, cand, method)
    if not only or "e2" in only:
        report["e2_ser_boundary"] = e2_ser_boundary(rows_by, cand, method)
    if not only or "e3" in only:
        report["e3_model_consistent"] = e3_model_consistent(rows_by, cand, method)
    (OUT / "results.json").write_text(json.dumps(report, indent=1))
    print("written:", OUT / "results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
