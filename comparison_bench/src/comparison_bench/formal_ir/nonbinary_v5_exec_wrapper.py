"""Deterministic parallel execution wrapper for the frozen v5 runtime.

This wrapper adds three operational capabilities around the frozen
:mod:`nonbinary_v5_runtime` lifecycle without modifying it:

1. ``parallel_run`` — decodes the same (policy, frame) task set in a standard
   library multi-process pool, collects results in the exact frozen order
   (policy-major, frame-major) so rows/events/artifacts are byte-identical to
   the serial path.
2. Periodic flush — every ``flush_every`` completed tasks the wrapper writes
   ``<parent>/<run_id>.partial_state.json`` (atomic temp+rename) containing
   the completed prefix.  An interrupted execution stays incomplete/invalid
   (frozen rule) but keeps auditable partial evidence.
3. ``resume_run`` — at most one continuation per package: re-validates the
   plan and the partial state, decodes only the missing tasks, and completes
   the normal eight-artifact package.

Worker tasks are plain picklable data: frame dict, policy dict, seed record
tuple.  The codebook manifest/matrices and the runner reference (module +
qualname of a module-level function) are passed once via the pool
initializer.  Production API rejects injected runners exactly like the frozen
runtime; test-only paths require an explicit fake runner.
"""
from __future__ import annotations

import hashlib, importlib, json, multiprocessing, os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping

from . import nonbinary_v5_runtime as runtime

PARTIAL_SCHEMA = "nbldpc_v5_exec_partial_v1"


def _partial_path(config, output):
    out = Path(output).resolve() if output is not None else runtime._official(config)
    return out.parent / f"{config.run_id}.partial_state.json"


# ---------------------------------------------------------------- worker side

def _worker_init(config_plain, cb, mats, runner_ref):
    global _WORKER
    core = importlib.import_module(config_plain["core"])
    runner = getattr(importlib.import_module(runner_ref[0]), runner_ref[1])
    _WORKER = {"config": SimpleNamespace(core=core, q=config_plain["q"], n=config_plain["n"],
                                         method=config_plain["method"], max_stages=config_plain["max_stages"],
                                         seed_bits=config_plain["seed_bits"]),
               "cb": cb, "mats": mats, "runner": runner}


def _worker_decode(task):
    frame, policy, seeds = task
    return runtime._result(_WORKER["config"], frame, policy, _WORKER["runner"],
                           _WORKER["cb"], _WORKER["mats"], seeds)


# ---------------------------------------------------------------- main side

def _plan_sha(plan_path):
    return hashlib.sha256(plan_path.read_bytes()).hexdigest()


def _write_partial(path, plan_sha, completed, rows, events, material):
    doc = {"schema": PARTIAL_SCHEMA, "plan_sha256": plan_sha, "completed": completed,
           "rows": rows, "events": events, "confirmation_material": material,
           "rows_sha256": _rows_sha(rows, events)}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, sort_keys=True, ensure_ascii=True, allow_nan=False))
    os.replace(tmp, path)


def _rows_sha(rows, events):
    return hashlib.sha256(json.dumps({"rows": rows, "events": events}, sort_keys=True,
                                     ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def _log(path, event, **fields):
    if path is None:
        return
    line = json.dumps({"event": event, **fields}, sort_keys=True, ensure_ascii=True) + "\n"
    with path.open("a", encoding="utf8") as handle:
        handle.write(line)


def _config_plain(config):
    return {"run_id": config.run_id, "core": config.core.__name__, "q": config.q,
            "n": config.n, "method": config.method, "max_stages": config.max_stages,
            "seed_bits": config.seed_bits}


def _runner_ref(config, runner):
    if runner is None:
        runner = config.core.production_runner
    return (runner.__module__, runner.__qualname__)


def _materialize(config, plan, selection, out):
    """Equivalent of the frozen runtime's inline confirmation materialization."""
    used = {x["seed_id"] for x in plan["development_toeplitz_seeds"].values()} | runtime._prior_seed_ids(exclude=out)
    material = {"frames": [], "toeplitz_seeds": {}, "frozen_before_decode": True}
    for p in config.ps:
        for index in range(config.confirmation_frames):
            frame = runtime._frame(config, p, "confirmation", index)
            material["frames"].append(frame)
            for stage in config.core.stage_slots(selection["selected_policy"]["policy_id"], p):
                seed = runtime.materialize_seed_record(config.seed_bits)
                if seed["seed_id"] in used:
                    raise RuntimeError("confirmation seed overlap")
                used.add(seed["seed_id"])
                material["toeplitz_seeds"][f"{selection['selected_policy']['policy_sha256']}|{frame['frame_id']}|{stage}"] = seed
    return material


def _confirm_tasks(config, plan, selection, material, out, policy_doc):
    policy_doc["confirmation_material"] = {
        "frames": [{k: v for k, v in f.items() if k not in {"alice", "bob"}} for f in material["frames"]],
        "toeplitz_seeds": material["toeplitz_seeds"], "frozen_before_decode": True}
    expected = runtime._confirmation_expected(config, selection["selected_policy"],
                                              policy_doc["confirmation_material"], exclude=out,
                                              development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
    return expected


def _decode(config, plan, tasks, cb, mats, runner_ref, workers, out, partial_path,
            flush_every, log_path, state, fatal_hook, material=None):
    """Run tasks in a pool, collecting in frozen order with periodic flush."""
    with multiprocessing.Pool(processes=workers, initializer=_worker_init,
                              initargs=(_config_plain(config), cb, mats, runner_ref)) as pool:
        for task, result in zip(tasks, pool.imap(_worker_decode, tasks, chunksize=1)):
            row, events = result
            state["rows"].append(row); state["events"].extend(events)
            state["completed"].append({"policy_sha256": task[1]["policy_sha256"],
                                       "frame_id": task[0]["frame_id"]})
            if fatal_hook is not None:
                fatal_hook(len(state["rows"]))
            if len(state["rows"]) % flush_every == 0:
                _write_partial(partial_path, _plan_sha(out / "pre_run_plan.json"),
                               state["completed"], state["rows"], state["events"], material)
                _log(log_path, "flush", completed=len(state["rows"]))


def parallel_run(config, output=None, *, workers=None, flush_every=64, log_path=None,
                 runner: Callable | None = None, _test_only=False,
                 fatal_hook: Callable[[int], None] | None = None):
    if not _test_only and runner is not None:
        raise ValueError("production run does not accept runner")
    if runner is None and _test_only:
        raise ValueError("test-only run requires explicit runner")
    if workers is None:
        workers = os.cpu_count() or 1
    if flush_every < 1:
        raise ValueError("flush_every must be >= 1")
    out = runtime._output(config, output, _test_only=_test_only)
    if {x.name for x in out.iterdir()} != {"pre_run_plan.json"}:
        raise ValueError("run requires plan-only directory")
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    runtime._validate_plan(config, plan, plan_path=plan_path)
    ref = _runner_ref(config, runner)
    partial_path = _partial_path(config, out)
    if log_path is None:
        log_path = partial_path.with_suffix(".execution.log")
    state = {"rows": [], "events": [], "codebook": None, "policy": None, "plan": plan, "completed": []}
    try:
        cb, mats = config.core.codebook(); state["codebook"] = cb
        tasks = runtime._expected_development(config, plan)
        _log(log_path, "start", run_id=config.run_id, tasks=len(tasks), workers=workers)
        _decode(config, plan, tasks, cb, mats, ref, workers, out, partial_path,
                flush_every, log_path, state, fatal_hook)
        rows, events = state["rows"], state["events"]
        selection = runtime._select(config, rows, plan["policies"])
        ready = bool(selection["selected_policy"] and all(
            sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p
                and x["policy_sha256"] == selection["selected_policy_sha256"] for x in rows) >= 63
            for p in config.ps))
        policy_doc = {"policies": plan["policies"], "selection": selection, "readiness": ready}
        state["policy"] = policy_doc
        if ready:
            material = _materialize(config, plan, selection, out)
            _log(log_path, "confirmation", frames=len(material["frames"]))
            tasks = _confirm_tasks(config, plan, selection, material, out, policy_doc)
            _decode(config, plan, tasks, cb, mats, ref, workers, out, partial_path,
                    flush_every, log_path, state, fatal_hook, material=material)
        result = runtime._write_normal(config, out, rows, events, cb, policy_doc, ready)
        _log(log_path, "done", run_status=result["run_status"])
        if partial_path.exists():
            partial_path.unlink()
        return result
    except Exception as exc:
        _log(log_path, "crash", reason=f"{type(exc).__name__}: {exc}", completed=len(state["rows"]))
        runtime._finalize_invalid(config, out, exc, state)
        raise


def resume_run(config, output=None, *, workers=None, flush_every=64, log_path=None,
               runner: Callable | None = None, _test_only=False,
               fatal_hook: Callable[[int], None] | None = None):
    if not _test_only and runner is not None:
        raise ValueError("production run does not accept runner")
    if runner is None and _test_only:
        raise ValueError("test-only run requires explicit runner")
    if workers is None:
        workers = os.cpu_count() or 1
    if flush_every < 1:
        raise ValueError("flush_every must be >= 1")
    out = runtime._output(config, output, _test_only=_test_only)
    names = {x.name for x in out.iterdir()}
    if names != {"pre_run_plan.json"}:
        # An interrupted attempt is an invalid_run package (crash finalize);
        # that package plus its partial_state.json is resumable.  Any other
        # state (a completed package) is final.
        if names != set(runtime.ARTIFACTS):
            raise ValueError("resume requires plan-only directory (executed package is final)")
        manifest = json.loads((out / "formal_run_manifest.json").read_text())
        if manifest.get("run_status") != "invalid_run":
            raise ValueError("resume requires plan-only directory (executed package is final)")
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    runtime._validate_plan(config, plan, plan_path=plan_path)
    ref = _runner_ref(config, runner)
    partial_path = _partial_path(config, out)
    if log_path is None:
        log_path = partial_path.with_suffix(".execution.log")
    plan_sha = _plan_sha(plan_path)
    material = None
    if partial_path.exists():
        doc = json.loads(partial_path.read_text())
        if doc.get("schema") != PARTIAL_SCHEMA or doc.get("plan_sha256") != plan_sha \
                or doc.get("rows_sha256") != _rows_sha(doc.get("rows", []), doc.get("events", [])):
            raise ValueError("partial state rejected")
        rows, events = doc["rows"], doc["events"]
        completed = [(x["policy_sha256"], x["frame_id"]) for x in doc.get("completed", [])]
        material = doc.get("confirmation_material")
    else:
        rows, events, completed, material = [], [], [], None
    # An invalid_run package carries stale partial artifacts written by the
    # crash finalize; drop everything except the plan so the normal package is
    # re-written from the trusted partial state (never from stale bytes).
    for name in runtime.ARTIFACTS:
        if name != "pre_run_plan.json":
            (out / name).unlink(missing_ok=True)
    state = {"rows": list(rows), "events": list(events), "codebook": None, "policy": None,
             "plan": plan, "completed": list(completed)}
    try:
        cb, mats = config.core.codebook(); state["codebook"] = cb
        all_tasks = runtime._expected_development(config, plan)
        # Completed tasks are a frozen-order prefix; trust their keys, decode the rest.
        remaining = [task for task in all_tasks[len(completed):]]
        _log(log_path, "resume", run_id=config.run_id, completed=len(completed),
             remaining=len(remaining), workers=workers)
        if remaining:
            _decode(config, plan, remaining, cb, mats, ref, workers, out, partial_path,
                    flush_every, log_path, state, fatal_hook, material=material)
        rows, events = state["rows"], state["events"]
        development_total = len(plan["frames"]) * len(plan["policies"])
        dev_rows, confirm_rows = rows[:development_total], rows[development_total:]
        selection = runtime._select(config, dev_rows, plan["policies"])
        ready = bool(selection["selected_policy"] and all(
            sum(x["status"] == "verified_success" and float(x["stratum_p"]) == p
                and x["policy_sha256"] == selection["selected_policy_sha256"] for x in dev_rows) >= 63
            for p in config.ps))
        policy_doc = {"policies": plan["policies"], "selection": selection, "readiness": ready}
        state["policy"] = policy_doc
        if ready:
            if material is None:
                material = _materialize(config, plan, selection, out)
            confirm_expected = _confirm_tasks(config, plan, selection, material, out, policy_doc)
            if any(x["policy_sha256"] != selection["selected_policy_sha256"] for x in confirm_rows) \
                    or len(confirm_rows) > len(confirm_expected):
                raise ValueError("resume confirmation state rejected")
            remaining = confirm_expected[len(confirm_rows):]
            _log(log_path, "confirmation", frames=len(confirm_expected), done=len(confirm_rows))
            if remaining:
                _decode(config, plan, remaining, cb, mats, ref, workers, out, partial_path,
                        flush_every, log_path, state, fatal_hook, material=material)
        result = runtime._write_normal(config, out, rows, events, cb, policy_doc, ready)
        _log(log_path, "done", run_status=result["run_status"])
        if partial_path.exists():
            partial_path.unlink()
        return result
    except Exception as exc:
        _log(log_path, "crash", reason=f"{type(exc).__name__}: {exc}", completed=len(state["rows"]))
        runtime._finalize_invalid(config, out, exc, state)
        raise
