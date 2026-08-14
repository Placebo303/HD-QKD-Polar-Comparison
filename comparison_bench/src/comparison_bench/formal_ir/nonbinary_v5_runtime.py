"""Parameterized formal qualification runtime shared by NBLDPC v5 routes.

This module is the generalization of the v4 IR lane
(:mod:`nonbinary_v4_ir_qualification`) that v4 proved: canonical plan schema,
PCG64 frame generation, identity overlap proof, development seed binding,
conditional confirmation materialization, selection ranking, the eight
artifacts, provenance, forbidden-diagnostic scans, and strict read-only
replay.  Every v5 route passes a frozen :class:`RouteConfig`; nothing
route-specific is hardcoded here.  v4 modules are never modified.

The public API separates plan creation, one execution and one read-only
verifier.  Test paths must supply a fake runner explicitly; production runs
reject injected runners.
"""
from __future__ import annotations

import csv, hashlib, json, platform, re, subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import nonbinary_syndrome, symbols_to_msb_bits
from .shared import (canonical_event, locked_seed_bits, materialize_seed_record,
                     toeplitz_tag, transcript_summary)

ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv",
             "formal_transcript.jsonl", "formal_run_manifest.json",
             "formal_codebook_manifest.json", "formal_candidate_manifest.json",
             "formal_policy_manifest.json", "formal_qualification_report.json")


@dataclass(frozen=True)
class RouteConfig:
    """One frozen route's complete identity contract.

    ``core`` must expose: ``METHOD``, ``POLICIES``, ``policy_spec``,
    ``codebook()``, ``start``, ``extend``, ``run_stage``, ``stage_slots``,
    ``extension_mode``, ``verification_cap``, ``protocol_epsilon`` and
    ``production_runner``.
    """
    run_id: str
    canonical_schema: str
    method: str
    q: int
    n: int
    ps: tuple[float, ...]
    roots: Mapping[tuple[str, float], int]
    caps: Mapping[str, Any]
    seed_bits: int
    core: Any
    source_files: tuple[str, ...]
    contract: str
    max_stages: int
    development_frames: int = 64
    confirmation_frames: int = 128


def _compact(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
def _sha(x): return hashlib.sha256(x).hexdigest()
def _root(): return Path(__file__).resolve().parents[4]
def _put(p, x):
    with p.open("xb") as f:
        f.write(json.dumps(x, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False).encode() + b"\n")
def _csv(p, rows):
    with p.open("x", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}) or ["status"])
        w.writeheader(); w.writerows(rows)
def _rows(p):
    with p.open(newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))
def _official(config):
    return (_root() / "comparison_bench/outputs_comparison/formal_ir_methods" / config.run_id).resolve()
def _output(config, output, *, _test_only):
    official = _official(config); chosen = official if output is None else Path(output).resolve()
    if chosen != official and not _test_only:
        raise ValueError(f"{config.run_id} requires official output root")
    return chosen
def _frame(config, p, role, index):
    rng = np.random.Generator(np.random.PCG64(config.roots[role, p] + index))
    alice = rng.integers(0, config.q, config.n, dtype=np.int64)
    mask = rng.random(config.n) < p
    error = rng.integers(1, config.q, config.n, dtype=np.int64)
    bob = alice.copy(); bob[mask] ^= error[mask]
    return {"frame_id": f"{config.method}_q{config.q}_p{int(p * 100):02d}_{role}_{index:03d}",
            "p": p, "role": role, "index": index, "seed": config.roots[role, p] + index,
            "alice": alice.tolist(), "bob": bob.tolist(),
            "array_sha256": _sha(alice.astype("<i8").tobytes() + bob.astype("<i8").tobytes()),
            "atomic_keys": [f"{config.method}|{role}|{p}|{index}|{j}" for j in range(config.n)]}
def _policy(config):
    out = []
    for name in config.core.POLICIES:
        body = {"policy_id": name, "decoder": "row_layered_fft_qspa", "lambda": .75,
                "max_stage_iterations": 12, "strata": [config.core.policy_spec(name, p) for p in config.ps]}
        out.append(dict(body, policy_sha256=_sha(_compact(body))))
    return out
def _provenance(config):
    root = _root(); cb, _ = config.core.codebook()
    candidate = {"method": config.method, "policies": list(config.core.POLICIES),
                 "v3_codebook_manifest_id": cb["manifest_id"]}
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = "unavailable"
    return {"source_sha256": {p: _sha((root / p).read_bytes()) for p in config.source_files},
            "contract_sha256": _sha((root / config.contract).read_bytes()),
            "candidate_sha256": _sha(_compact(candidate)), "codebook_sha256": cb["canonical_sha256"],
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "git_commit": commit}
def _excluded(path, exclude):
    if exclude is None:
        return False
    target = Path(exclude).resolve(); current = Path(path).resolve()
    return current == target if target.suffix else current.is_relative_to(target)
def _prior_seed_ids(exclude=None):
    found = set(); base = _root() / "comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():
        return found
    for path in base.rglob("*.json"):
        if _excluded(path, exclude):
            continue
        try:
            text = path.read_text(encoding="utf8")
        except OSError:
            continue
        found.update(re.findall(r'"seed_id"\s*:\s*"([0-9a-f]{64})"', text))
    return found
def _prior_identities(exclude=None):
    found = {"roots": set(), "frame_ids": set(), "array_sha256": set(), "atomic_keys": set()}
    base = _root() / "comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():
        return found
    for path in base.rglob("pre_run_plan.json"):
        if _excluded(path, exclude):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf8"))
        except (OSError, ValueError):
            continue
        roots = doc.get("roots", {}); found["roots"].update(map(str, roots.values()))
        for frame in doc.get("frames", []):
            if isinstance(frame, dict):
                found["frame_ids"].add(str(frame.get("frame_id", "")))
                found["array_sha256"].add(str(frame.get("array_sha256", "")))
                found["atomic_keys"].update(map(str, frame.get("atomic_keys", [])))
    for path in base.rglob("formal_policy_manifest.json"):
        if _excluded(path, exclude):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf8"))
            frames = doc.get("confirmation_material", {}).get("frames", [])
        except (OSError, ValueError, AttributeError):
            continue
        for frame in frames:
            if isinstance(frame, dict):
                found["frame_ids"].add(str(frame.get("frame_id", "")))
                found["array_sha256"].add(str(frame.get("array_sha256", "")))
                found["atomic_keys"].update(map(str, frame.get("atomic_keys", [])))
    return found
def _identity_overlap(config, frames, *, exclude=None):
    old = _prior_identities(exclude); roots = {str(x) for x in config.roots.values()}
    now = {"roots": roots, "frame_ids": {str(x["frame_id"]) for x in frames},
           "array_sha256": {str(x["array_sha256"]) for x in frames},
           "atomic_keys": {str(k) for x in frames for k in x["atomic_keys"]}}
    return {key: sorted(now[key] & old[key]) for key in now}
def _seed_keys(config, policies, frames):
    return {f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}"
            for policy in policies for frame in frames
            for stage in config.core.stage_slots(policy["policy_id"], frame["p"])}
def expected_plan(config):
    frames = [_frame(config, p, "development", i) for p in config.ps for i in range(config.development_frames)]
    policies = _policy(config); seeds = {}
    for key in _seed_keys(config, policies, frames):
        seeds[key] = materialize_seed_record(config.seed_bits)
    return {"canonical_schema": config.canonical_schema, "run_id": config.run_id,
            "method": config.method, "q": config.q, "n": config.n,
            "roots": {f"{r}|{p}": v for (r, p), v in config.roots.items()},
            "caps": dict(config.caps), "frames": frames, "identity_overlap": _identity_overlap(config, frames),
            "policies": policies, "development_toeplitz_seeds": seeds,
            "confirmation_contract": {"frames_per_stratum": config.confirmation_frames,
                                      "seed_bits": config.seed_bits,
                                      "materialize_only_after_readiness": True},
            "provenance": _provenance(config)}
def _validate_plan(config, plan, *, plan_path=None):
    if plan.get("canonical_schema") != config.canonical_schema or plan.get("run_id") != config.run_id \
            or plan.get("method") != config.method or plan.get("q") != config.q or plan.get("n") != config.n:
        raise ValueError("plan identity")
    if plan.get("roots") != {f"{r}|{p}": v for (r, p), v in config.roots.items()} \
            or plan.get("caps") != dict(config.caps) or plan.get("policies") != _policy(config) \
            or plan.get("provenance") != _provenance(config):
        raise ValueError("plan contract/provenance")
    frames = plan.get("frames")
    expected = [_frame(config, p, "development", i) for p in config.ps for i in range(config.development_frames)]
    if frames != expected or any(x.get("role") != "development" for x in frames):
        raise ValueError("confirmation leaked into plan")
    if plan.get("confirmation_contract") != {"frames_per_stratum": config.confirmation_frames,
                                             "seed_bits": config.seed_bits,
                                             "materialize_only_after_readiness": True}:
        raise ValueError("confirmation contract")
    if plan.get("identity_overlap") != _identity_overlap(config, frames, exclude=plan_path) \
            or any(plan["identity_overlap"].values()):
        raise ValueError("identity freshness")
    seeds = plan.get("development_toeplitz_seeds", {})
    if set(seeds) != _seed_keys(config, _policy(config), frames):
        raise ValueError("development seed binding")
    ids = []
    for record in seeds.values():
        locked_seed_bits(record, config.seed_bits); ids.append(record["seed_id"])
    if len(ids) != len(set(ids)) or set(ids) & _prior_seed_ids(exclude=plan_path):
        raise ValueError("seed freshness")
    return True
def create_plan(config, output=None, *, _test_only=False):
    out = _output(config, output, _test_only=_test_only)
    if out.exists():
        raise FileExistsError(out)
    plan = expected_plan(config); _validate_plan(config, plan)
    out.mkdir(parents=True); _put(out / "pre_run_plan.json", plan)
    return plan

def _events(config, frame, policy, stages, decisions, seeds, syndromes, tags):
    events = []; eid = 0
    def add(kind, direction, parent, key=0, public=0, payload=None):
        nonlocal eid
        events.append({"event_id": eid, "frame_key": frame["frame_id"], "method": config.method,
                       "event_type": kind, "direction": direction, "parent_event_id": parent,
                       "pass_id": eid, "plane_id": "q1024", "key_dependent_bits": key,
                       "public_control_bits": public, "payload": payload or {"reason": kind}})
        eid += 1
    for stage, result in enumerate(stages):
        checks = result["check_count"]
        disclosed = checks * 10 if stage == 0 else (checks - int(stages[stage - 1]["check_count"])) * 10
        suffix = "STAGE1" if stage == 0 else f"STAGE{stage + 1}"
        payload = {"syndrome": list(syndromes[stage])}
        add("SYNDROME_INITIAL" if stage == 0 else "SYNDROME_EXTENSION", "alice_to_bob", eid - 1, disclosed, 0, payload)
        add(f"DECODER_{suffix}", "bob_local", eid - 1, 0, 0, {"reason": result["status"]})
        if result.get("verification_invoked"):
            seed = seeds[stage]
            add(f"VERIFICATION_TAG_{suffix}", "alice_to_bob", eid - 1, 64, config.seed_bits,
                {"tag": tags[stage].hex(), "seed_id": seed["seed_id"], "seed_bit_length": config.seed_bits})
        add(f"STAGE_DECISION_{suffix}", "control", eid - 1, 0, 2, {"reason": decisions[stage]})
    return events
def _tag(config, symbols, seed):
    return toeplitz_tag(symbols_to_msb_bits(symbols, config.q), locked_seed_bits(seed, config.seed_bits))

def _result(config, frame, policy, runner, cb, mats, seeds):
    spec = next(x for x in policy["strata"] if x["p"] == frame["p"])
    ladder = tuple(spec["ladder"]); field = GF2mField.create(config.q)
    full = nonbinary_syndrome(mats[ladder[-1]], frame["alice"], field)
    state = None; stages = []; tags = []; syndromes = []; decisions = []
    prev_checks = None
    for idx, checks in enumerate(ladder):
        if idx == 0:
            syndromes.append(full[:checks])
            started = config.core.start(policy["policy_id"], frame["bob"], full[:checks], cb,
                                        p=frame["p"], stage_runner=runner)
            if isinstance(started, dict):
                state = None; raw = started
            else:
                state, raw, _ = started
        else:
            syndromes.append(full[prev_checks:checks])
            mode = config.core.extension_mode(policy["policy_id"])
            nxt = config.core.extend(state, full[prev_checks:checks], mats, mode=mode) if state is not None \
                else {"status": "decoder_error"}
            raw = nxt if isinstance(nxt, dict) else config.core.run_stage(nxt, mats, stage=idx + 1, stage_runner=runner)
        status = raw.get("status", "decoder_error")
        invoked = status == "syndrome_consistent"
        if invoked:
            alice_tag = _tag(config, frame["alice"], seeds[idx])
            bob_tag = _tag(config, raw["decoded_symbols"], seeds[idx])
            verified = alice_tag == bob_tag; tags.append(alice_tag)
        else:
            verified = False; tags.append(b"")
        stages.append({"check_count": checks,
                       "status": "verified_success" if invoked and verified else "verify_failed" if invoked else status,
                       "iterations": int(raw.get("iterations", 0)), "verification_invoked": invoked})
        can_extend = idx < len(ladder) - 1 and stages[-1]["status"] in {"decode_failed", "verify_failed"}
        decisions.append("01" if can_extend else "00" if stages[-1]["status"] == "verified_success" else "10")
        if not can_extend:
            break
        prev_checks = checks
    final_status = stages[-1]["status"]
    events = _events(config, frame, policy, stages, decisions, seeds, syndromes, tags)
    summary = transcript_summary(events)
    row = {"frame_id": frame["frame_id"], "stratum_p": frame["p"], "qualification_role": frame["role"],
           "policy_sha256": policy["policy_sha256"], "policy_id": policy["policy_id"],
           "status": final_status, "denominator_included": True,
           "initial_prefix": ladder[0], "final_prefix": stages[-1]["check_count"],
           "extension_used": len(stages) > 1,
           "verification_attempts": sum(x["verification_invoked"] for x in stages),
           "outcome_epsilon_ec": 2.0 ** -64 if final_status == "verified_success" else None,
           "protocol_epsilon_ec_bound": config.core.protocol_epsilon(policy["policy_id"]),
           "array_sha256": frame["array_sha256"], "transcript_event_count": len(events), **summary}
    for k in range(1, config.max_stages + 1):
        row[f"stage{k}_iterations"] = stages[k - 1]["iterations"] if len(stages) >= k else 0
    return row, events
def _select(config, rows, policies):
    ranked = []
    for policy in policies:
        rs = [x for x in rows if x["policy_sha256"] == policy["policy_sha256"]]
        expected = [f"{config.method}_q{config.q}_p{int(p * 100):02d}_development_{i:03d}"
                    for p in config.ps for i in range(config.development_frames)]
        counts = [sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p for x in rs) for p in config.ps]
        if len(rs) != len(expected) or [x.get("frame_id") for x in rs] != expected \
                or any(str(x.get("denominator_included")).lower() != "true"
                       or x["status"] not in {"verified_success", "verify_failed", "decode_failed", "aborted_resource_limit"}
                       for x in rs) \
                or any(sum(float(x["stratum_p"]) == p for x in rs) != config.development_frames for p in config.ps):
            continue
        iterations = sum(int(x[f"stage{k}_iterations"]) for x in rs for k in range(1, config.max_stages + 1))
        ranked.append((-min(counts), -sum(counts),
                       sum(int(x["key_dependent_disclosure_bits_total"]) for x in rs),
                       sum(int(x["public_control_bits_total"]) for x in rs),
                       sum(int(x["transcript_event_count"]) for x in rs),
                       iterations, policy["policy_sha256"], policy))
    if not ranked:
        return {"selected_policy": None, "selected_policy_sha256": None, "selection_key": None,
                "reason": "no_eligible_policy"}
    best = min(ranked)
    return {"selected_policy": best[-1], "selected_policy_sha256": best[-1]["policy_sha256"],
            "selection_key": list(best[:-1]), "reason": "development_rank"}
def _artifact_hashes(out):
    return {name: _sha((out / name).read_bytes()) for name in ARTIFACTS
            if name not in {"formal_run_manifest.json", "formal_qualification_report.json"}
            and (out / name).exists()}
def _candidate_manifest(config, cb=None):
    cb = config.core.codebook()[0] if cb is None else cb
    return {"method": config.method, "policies": list(config.core.POLICIES),
            "v3_codebook_manifest_id": cb["manifest_id"]}
def _write_events(path, events):
    with path.open("xb") as handle:
        for event in events:
            handle.write(canonical_event(event))

def _finalize_invalid(config, out, exc, state):
    rows, events = state["rows"], state["events"]
    if not (out / "formal_frame_outcomes.csv").exists():
        _csv(out / "formal_frame_outcomes.csv", rows)
    if not (out / "formal_transcript.jsonl").exists():
        _write_events(out / "formal_transcript.jsonl", events)
    cb = state.get("codebook"); policy = state.get("policy")
    plan = state["plan"]
    development_total = len(plan["frames"]) * len(plan["policies"])
    if policy is None and cb is not None and len(rows) == development_total:
        selection = _select(config, rows, plan["policies"])
        ready = bool(selection["selected_policy"] and all(
            sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p
                and x["policy_sha256"] == selection["selected_policy_sha256"] for x in rows) >= 63
            for p in config.ps))
        policy = {"policies": plan["policies"], "selection": selection, "readiness": ready}
    if not (out / "formal_codebook_manifest.json").exists():
        _put(out / "formal_codebook_manifest.json", cb if cb is not None else {"invalid": True})
    if not (out / "formal_candidate_manifest.json").exists():
        _put(out / "formal_candidate_manifest.json", _candidate_manifest(config, cb) if cb is not None else {"invalid": True})
    if not (out / "formal_policy_manifest.json").exists():
        _put(out / "formal_policy_manifest.json", policy if policy is not None else {"invalid": True})
    manifest = {"run_id": config.run_id, "run_status": "invalid_run",
                "reason": f"{type(exc).__name__}: {exc}", "outcome_count": len(rows),
                "artifacts": _artifact_hashes(out)}
    _put(out / "formal_run_manifest.json", manifest)
    _put(out / "formal_qualification_report.json",
         {"run_id": config.run_id, "run_status": "invalid_run", "readiness": False, "promoted": False,
          "formal_run_manifest_sha256": _sha((out / "formal_run_manifest.json").read_bytes())})
def _gates(config, rows):
    allowed = {"verified_success", "verify_failed", "decode_failed", "aborted_resource_limit"}
    return {str(p): {"requested": config.confirmation_frames,
                     "denominator_included": sum(x["qualification_role"] == "confirmation"
                                                 and float(x["stratum_p"]) == p for x in rows),
                     "verified_success": sum(x["qualification_role"] == "confirmation"
                                             and float(x["stratum_p"]) == p
                                             and x["status"] == "verified_success" for x in rows),
                     "prohibited_failures": sum(x["qualification_role"] == "confirmation"
                                                and float(x["stratum_p"]) == p
                                                and x["status"] not in allowed for x in rows)}
            for p in config.ps}
def _write_normal(config, out, rows, events, cb, policy_doc, ready):
    _put(out / "formal_codebook_manifest.json", cb)
    _put(out / "formal_candidate_manifest.json", _candidate_manifest(config, cb))
    _put(out / "formal_policy_manifest.json", policy_doc)
    _csv(out / "formal_frame_outcomes.csv", rows)
    _write_events(out / "formal_transcript.jsonl", events)
    run_status = "completed" if ready else "non_promoted_development"
    gates = _gates(config, rows)
    promoted = ready and all(x["denominator_included"] == config.confirmation_frames
                             and x["verified_success"] == config.confirmation_frames
                             and x["prohibited_failures"] == 0 for x in gates.values())
    _put(out / "formal_run_manifest.json",
         {"run_id": config.run_id, "run_status": run_status, "outcome_count": len(rows),
          "artifacts": _artifact_hashes(out)})
    _put(out / "formal_qualification_report.json",
         {"run_id": config.run_id, "run_status": run_status, "readiness": ready,
          "promotion_gates": gates, "promoted": promoted,
          "formal_run_manifest_sha256": _sha((out / "formal_run_manifest.json").read_bytes())})
    return {"run_status": run_status, "readiness": ready, "promoted": promoted}

def run(config, output=None, *, runner: Callable | None = None, _test_only=False,
        fatal_hook: Callable[[int], None] | None = None):
    if not _test_only and runner is not None:
        raise ValueError("production run does not accept runner")
    if runner is None:
        if _test_only:
            raise ValueError("test-only run requires explicit runner")
        runner = config.core.production_runner
    out = _output(config, output, _test_only=_test_only)
    if {x.name for x in out.iterdir()} != {"pre_run_plan.json"}:
        raise ValueError("run requires plan-only directory")
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    _validate_plan(config, plan, plan_path=plan_path)
    state = {"rows": [], "events": [], "codebook": None, "policy": None, "plan": plan}
    try:
        cb, mats = config.core.codebook(); state["codebook"] = cb
        for policy in plan["policies"]:
            for frame in plan["frames"]:
                seeds = [plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}"]
                         for stage in config.core.stage_slots(policy["policy_id"], frame["p"])]
                row, event = _result(config, frame, policy, runner, cb, mats, tuple(seeds))
                state["rows"].append(row); state["events"] += event
                if fatal_hook is not None:
                    fatal_hook(len(state["rows"]))
        rows, events = state["rows"], state["events"]
        selection = _select(config, rows, plan["policies"])
        ready = bool(selection["selected_policy"] and all(
            sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p
                and x["policy_sha256"] == selection["selected_policy_sha256"] for x in rows) >= 63
            for p in config.ps))
        policy_doc = {"policies": plan["policies"], "selection": selection, "readiness": ready}
        state["policy"] = policy_doc
        if ready:
            # Materialize the complete selected lane before its first decode.
            # This occurs only after development selection and uses additive
            # seed records; it is never present in a plan-only directory.
            selected = selection["selected_policy"]
            used = {x["seed_id"] for x in plan["development_toeplitz_seeds"].values()} | _prior_seed_ids(exclude=out)
            material = {"frames": [], "toeplitz_seeds": {}, "frozen_before_decode": True}
            for p in config.ps:
                for index in range(config.confirmation_frames):
                    frame = _frame(config, p, "confirmation", index)
                    material["frames"].append(frame)
                    for stage in config.core.stage_slots(selected["policy_id"], p):
                        seed = materialize_seed_record(config.seed_bits)
                        if seed["seed_id"] in used:
                            raise RuntimeError("confirmation seed overlap")
                        used.add(seed["seed_id"])
                        material["toeplitz_seeds"][f"{selected['policy_sha256']}|{frame['frame_id']}|{stage}"] = seed
            # Evidence binds identity and seed records, never Alice/Bob arrays.
            policy_doc["confirmation_material"] = {
                "frames": [{k: v for k, v in frame.items() if k not in {"alice", "bob"}} for frame in material["frames"]],
                "toeplitz_seeds": material["toeplitz_seeds"], "frozen_before_decode": True}
            _confirmation_expected(config, selected, policy_doc["confirmation_material"], exclude=out,
                                   development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
            for frame in material["frames"]:
                seeds = [material["toeplitz_seeds"][f"{selected['policy_sha256']}|{frame['frame_id']}|{stage}"]
                         for stage in config.core.stage_slots(selected["policy_id"], frame["p"])]
                row, event = _result(config, frame, selected, runner, cb, mats, tuple(seeds))
                rows.append(row); events += event
                if fatal_hook is not None:
                    fatal_hook(len(rows))
        return _write_normal(config, out, rows, events, cb, policy_doc, ready)
    except Exception as exc:
        _finalize_invalid(config, out, exc, state)
        raise

_FORBIDDEN = ("residual", "posterior", "message", "cycle", "alice", "truth",
              "error_location", "decision_hash", "decoded_symbols")
def _reject_diagnostics(value):
    if isinstance(value, Mapping):
        for key, item in value.items():
            if any(token in str(key).lower() for token in _FORBIDDEN):
                raise ValueError("forbidden diagnostic")
            _reject_diagnostics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_diagnostics(item)
def _same(expected, actual):
    right = dict(actual)
    if right.get("outcome_epsilon_ec") == "":
        right["outcome_epsilon_ec"] = None
    return {k: str(v) for k, v in expected.items()} == {k: str(v) for k, v in right.items()}
def _expected_development(config, plan):
    return [(frame, policy,
             tuple(plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}"]
                   for stage in config.core.stage_slots(policy["policy_id"], frame["p"])))
            for policy in plan["policies"] for frame in plan["frames"]]
def _confirmation_expected(config, policy, material, *, exclude, development_ids=()):
    if set(material) != {"frames", "toeplitz_seeds", "frozen_before_decode"} \
            or material.get("frozen_before_decode") is not True:
        raise ValueError("confirmation material shape")
    public = material["frames"]; seeds = material["toeplitz_seeds"]
    if len(public) != len(config.ps) * config.confirmation_frames:
        raise ValueError("confirmation frozen count")
    frames = []; ids = []; wanted = {}
    for p in config.ps:
        for index in range(config.confirmation_frames):
            expected = _frame(config, p, "confirmation", index)
            shown = {k: v for k, v in expected.items() if k not in {"alice", "bob"}}
            actual = public[len(frames)]
            if actual != shown:
                raise ValueError("confirmation identity replay")
            frames.append(expected)
            for stage in config.core.stage_slots(policy["policy_id"], p):
                wanted[f"{policy['policy_sha256']}|{expected['frame_id']}|{stage}"] = None
    if set(seeds) != set(wanted):
        raise ValueError("confirmation seed keys")
    for key, record in seeds.items():
        locked_seed_bits(record, config.seed_bits); ids.append(record["seed_id"])
    if len(ids) != len(set(ids)) or set(ids) & set(development_ids) or set(ids) & _prior_seed_ids(exclude=exclude):
        raise ValueError("confirmation seed isolation")
    if any(_identity_overlap(config, frames, exclude=exclude).values()):
        raise ValueError("confirmation identity isolation")
    return [(frame, policy, tuple(seeds[f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}"]
                                  for stage in config.core.stage_slots(policy["policy_id"], frame["p"])))
            for frame in frames]

def _verify_invalid(config, out, plan, verifier_runner):
    manifest = json.loads((out / "formal_run_manifest.json").read_text())
    report = json.loads((out / "formal_qualification_report.json").read_text())
    if {x.name for x in out.iterdir()} != set(ARTIFACTS) \
            or set(manifest) != {"run_id", "run_status", "reason", "outcome_count", "artifacts"} \
            or set(report) != {"run_id", "run_status", "readiness", "promoted", "formal_run_manifest_sha256"}:
        raise ValueError("invalid package shape")
    if manifest.get("run_id") != config.run_id or manifest.get("run_status") != "invalid_run" \
            or not isinstance(manifest.get("reason"), str) or not manifest["reason"] \
            or manifest.get("artifacts") != _artifact_hashes(out) \
            or report != {"run_id": config.run_id, "run_status": "invalid_run", "readiness": False,
                          "promoted": False,
                          "formal_run_manifest_sha256": _sha((out / "formal_run_manifest.json").read_bytes())}:
        raise ValueError("invalid package identity")
    rows = _rows(out / "formal_frame_outcomes.csv")
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    if b"".join(canonical_event(event) for event in events) != (out / "formal_transcript.jsonl").read_bytes() \
            or manifest["outcome_count"] != len(rows):
        raise ValueError("invalid transcript")
    cb = json.loads((out / "formal_codebook_manifest.json").read_text())
    candidate = json.loads((out / "formal_candidate_manifest.json").read_text())
    policy_doc = json.loads((out / "formal_policy_manifest.json").read_text())
    if not rows:
        if cb != {"invalid": True} or candidate != {"invalid": True} or policy_doc != {"invalid": True} or events:
            raise ValueError("invalid empty sentinel")
        return {"verified": True, "run_status": "invalid_run", "promoted": False}
    if cb != config.core.codebook()[0] or candidate != _candidate_manifest(config, cb):
        raise ValueError("invalid partial provenance")
    development_total = len(plan["frames"]) * len(plan["policies"])
    if len(rows) < development_total:
        if policy_doc != {"invalid": True}:
            raise ValueError("invalid partial state")
    elif not isinstance(policy_doc, dict) or policy_doc.get("policies") != plan["policies"]:
        raise ValueError("invalid partial provenance")
    expected = _expected_development(config, plan)
    if len(rows) > len(expected):
        selection = _select(config, rows[:len(expected)], plan["policies"])
        material = policy_doc.get("confirmation_material", {})
        selected = selection.get("selected_policy")
        if policy_doc.get("selection") != selection or selected is None:
            raise ValueError("invalid partial confirmation")
        expected += _confirmation_expected(config, selected, material, exclude=out,
                                           development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
    if len(rows) > len(expected):
        raise ValueError("invalid partial row count")
    if [row.get("frame_id") for row in rows] != [frame["frame_id"] for frame, _, _ in expected[:len(rows)]] \
            or [row.get("policy_sha256") for row in rows] != [policy["policy_sha256"] for _, policy, _ in expected[:len(rows)]]:
        raise ValueError("invalid partial order")
    cursor = 0; cb2, mats = config.core.codebook()
    for index, (actual, (frame, policy, seeds)) in enumerate(zip(rows, expected)):
        replay, row_events = _result(config, frame, policy, verifier_runner, cb2, mats, seeds)
        count = int(actual.get("transcript_event_count", 0)); piece = events[cursor:cursor + count]; cursor += count
        if not _same(replay, actual) or piece != row_events:
            raise ValueError(f"invalid partial replay at {index}")
    if cursor != len(events):
        raise ValueError("orphan invalid events")
    return {"verified": True, "run_status": "invalid_run", "promoted": False}

def verify(config, output=None, *, verifier_runner: Callable | None = None, _test_only=False):
    if not _test_only and verifier_runner is not None:
        raise ValueError("production verify does not accept verifier_runner")
    out = _output(config, output, _test_only=_test_only)
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    _validate_plan(config, plan, plan_path=plan_path)
    if verifier_runner is None and _test_only:
        raise ValueError("test-only verify requires explicit verifier_runner")
    if {x.name for x in out.iterdir()} == {"pre_run_plan.json"}:
        return {"verified": True, "plan_only": True, "run_status": "planned", "promoted": False}
    manifest = json.loads((out / "formal_run_manifest.json").read_text()) \
        if (out / "formal_run_manifest.json").exists() else {}
    if verifier_runner is None:
        verifier_runner = config.core.production_runner
    if manifest.get("run_status") == "invalid_run":
        return _verify_invalid(config, out, plan, verifier_runner)
    if {x.name for x in out.iterdir()} != set(ARTIFACTS):
        raise ValueError("artifact set")
    report = json.loads((out / "formal_qualification_report.json").read_text())
    rows = _rows(out / "formal_frame_outcomes.csv")
    if set(manifest) != {"run_id", "run_status", "outcome_count", "artifacts"} \
            or set(report) != {"run_id", "run_status", "readiness", "promotion_gates", "promoted",
                               "formal_run_manifest_sha256"}:
        raise ValueError("normal package schema")
    if manifest.get("run_id") != config.run_id or report.get("run_id") != config.run_id \
            or manifest.get("artifacts") != _artifact_hashes(out) \
            or report.get("formal_run_manifest_sha256") != _sha((out / "formal_run_manifest.json").read_bytes()):
        raise ValueError("artifact DAG")
    # The reconstructed v3 codebook manifest necessarily contains its frozen
    # structural `cycle_count` proof.  It is not a transient decoder
    # diagnostic; all outcome/transcript/control artifacts are checked.
    for path in (out / "formal_frame_outcomes.csv", out / "formal_transcript.jsonl",
                 out / "formal_policy_manifest.json", out / "formal_candidate_manifest.json"):
        if path.suffix == ".csv":
            _reject_diagnostics(rows)
        elif path.suffix == ".jsonl":
            for line in path.read_bytes().splitlines():
                _reject_diagnostics(json.loads(line))
        else:
            _reject_diagnostics(json.loads(path.read_text()))
    if json.loads((out / "formal_codebook_manifest.json").read_text()) != config.core.codebook()[0] \
            or json.loads((out / "formal_candidate_manifest.json").read_text()) != _candidate_manifest(config):
        raise ValueError("candidate/codebook replay")
    policy_doc = json.loads((out / "formal_policy_manifest.json").read_text())
    dev = [x for x in rows if x["qualification_role"] == "development"]
    confirm = [x for x in rows if x["qualification_role"] == "confirmation"]
    development_total = len(plan["frames"]) * len(plan["policies"])
    confirmation_total = len(plan["frames"]) * config.confirmation_frames // config.development_frames
    if manifest.get("outcome_count") != len(rows) or len(dev) != development_total \
            or (manifest["run_status"] == "non_promoted_development" and confirm):
        raise ValueError("development count")
    if manifest["run_status"] == "completed" and len(confirm) != confirmation_total:
        raise ValueError("confirmation count")
    # Strict replay uses source reconstruction, never private arrays
    # serialized in the manifest.  Runner is invoked for every stage.
    expected = _expected_development(config, plan)
    if confirm:
        selected = policy_doc.get("selection", {}).get("selected_policy")
        material = policy_doc.get("confirmation_material", {})
        if selected not in plan["policies"]:
            raise ValueError("confirmation material")
        expected += _confirmation_expected(config, selected, material, exclude=out,
                                           development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
    if len(rows) != len(expected):
        raise ValueError("row count")
    parsed = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    cursor = 0
    for index, (actual, (frame, policy, seeds)) in enumerate(zip(rows, expected)):
        replay, events = _result(config, frame, policy, verifier_runner,
                                 config.core.codebook()[0], config.core.codebook()[1], seeds)
        count = int(actual.get("transcript_event_count", 0)); piece = parsed[cursor:cursor + count]; cursor += count
        if not _same(replay, actual) or piece != events:
            raise ValueError(f"semantic replay at {index}")
    if cursor != len(parsed):
        raise ValueError("orphan transcript events")
    replay_selection = _select(config, dev, plan["policies"])
    if policy_doc.get("selection") != replay_selection:
        raise ValueError("selection replay")
    readiness = bool(replay_selection["selected_policy"] and all(
        sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p
            and x["policy_sha256"] == replay_selection["selected_policy_sha256"] for x in dev) >= 63
        for p in config.ps))
    if bool(policy_doc.get("readiness")) != readiness:
        raise ValueError("readiness replay")
    expected_status = "completed" if readiness else "non_promoted_development"
    if manifest.get("run_status") != expected_status or report.get("run_status") != expected_status \
            or (not readiness and confirm):
        raise ValueError("normal run status")
    gates = _gates(config, rows)
    promoted = readiness and all(x["denominator_included"] == config.confirmation_frames
                                 and x["verified_success"] == config.confirmation_frames
                                 and x["prohibited_failures"] == 0 for x in gates.values())
    if report.get("promotion_gates") != gates or bool(report.get("promoted")) != promoted:
        raise ValueError("promotion gates")
    return {"verified": True, "run_status": manifest["run_status"], "promoted": bool(report["promoted"])}
