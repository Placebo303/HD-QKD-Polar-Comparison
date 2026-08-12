"""V7 shared automatic ladder controller (``formal-nonbinary-ldpc-v7-successor-ladder``).

A SMALL deterministic state machine (dict-based; deliberately not a
framework).  One status per subroute:

    pending -> engineered -> planned -> executed -> verified
            -> ready | failed_canary | non_ready | blocked

Frozen contracts (V7-01):

- ``advance`` accepts only an *immutable verified report*: the report must be
  a mapping with ``event``/``payload``/``report_sha256`` and the hash must
  equal the canonical SHA256 of the payload.  A tampered payload or a forged
  hash is rejected before any state change.
- Exactly-once execute/replay: each stage records at most one plan, one run
  manifest, and one replay report; a second ``execute``/``verified`` event for
  the same stage raises.  Terminal statuses (``ready``, ``failed_canary``,
  ``non_ready``, ``blocked``) accept no further transition (no-rerun /
  no-tuning).
- The controller has NO confirmation path: no status, event, or transition can
  produce confirmation material; ``confirmed`` is not a valid status.
- Frozen gates, re-evaluated deterministically from the report payload:

  - canary: 0/4 verified success in either stratum -> ``failed_canary``;
  - development ready: per-stratum ``>=15/16`` verified success, zero
    forbidden failures, ``strict_replay_verified`` true, key-dependent
    disclosure excluding the tag ``<= 8.75`` bits/input-symbol per stratum,
    median runtime ``<= 120`` seconds/frame.

The module is pure and deterministic: no filesystem is touched by the
transitions themselves.  ``save_state``/``load_state`` persist a state to an
immutable JSON artifact (hash-bound) so a crashed process resumes from the
last recorded artifact.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

STATUSES = ("pending", "engineered", "planned", "executed", "verified",
            "ready", "failed_canary", "non_ready", "blocked")
ROUTES = ("r1a", "r1b", "r2", "r3")
TERMINAL = ("ready", "failed_canary", "non_ready", "blocked")
_STAGES = ("canary", "development")

CANARY_FRAMES_PER_STRATUM = 4
DEVELOPMENT_FRAMES_PER_STRATUM = 16
MIN_DEVELOPMENT_VERIFIED_PER_STRATUM = 15
MAX_FORBIDDEN_FAILURES = 0
DISCLOSURE_BITS_PER_SYMBOL_MAX = 8.75
MEDIAN_RUNTIME_SECONDS_MAX = 120.0

# event name == target status; a transition is valid only if the event is one
# of the frozen successors of the current status.
TRANSITIONS = {
    "pending": ("engineered", "blocked"),
    "engineered": ("planned", "blocked"),
    "planned": ("executed", "blocked"),
    "executed": ("verified", "blocked"),
    "verified": ("planned", "ready", "non_ready", "failed_canary", "blocked"),
    "ready": (),
    "failed_canary": (),
    "non_ready": (),
    "blocked": (),
}

_ARTIFACT_KEYS = ("engineering_acceptance", "canary_plan", "canary_run_manifest",
                  "canary_replay", "development_plan", "development_run_manifest",
                  "development_replay")


def _compact(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get_stratum(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    per = payload.get("per_stratum")
    if not isinstance(per, Mapping):
        return {}
    return {str(key): value for key, value in per.items() if isinstance(value, Mapping)}


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def canary_gate_failed(payload: Mapping[str, Any]) -> bool:
    """Frozen canary gate: 0/4 verified success in either stratum -> failed."""
    for stratum in _get_stratum(payload).values():
        if _as_int(stratum.get("frames")) == CANARY_FRAMES_PER_STRATUM \
                and _as_int(stratum.get("verified_success")) == 0:
            return True
    return False


def development_ready(payload: Mapping[str, Any]) -> bool:
    """Frozen development-readiness gate (a threshold, never promotion)."""
    strata = _get_stratum(payload)
    if not strata:
        return False
    if payload.get("strict_replay_verified") is not True:
        return False
    median = payload.get("median_runtime_seconds")
    if isinstance(median, bool) or not isinstance(median, (int, float)) \
            or not 0.0 <= float(median) <= MEDIAN_RUNTIME_SECONDS_MAX:
        return False
    for stratum in strata.values():
        if _as_int(stratum.get("frames")) != DEVELOPMENT_FRAMES_PER_STRATUM:
            return False
        if _as_int(stratum.get("verified_success")) < MIN_DEVELOPMENT_VERIFIED_PER_STRATUM:
            return False
        if _as_int(stratum.get("forbidden_failures")) != MAX_FORBIDDEN_FAILURES:
            return False
        symbols = _as_int(stratum.get("symbols_per_frame"))
        disclosure = _as_int(stratum.get("key_dependent_bits_excluding_tag"))
        if symbols <= 0 or disclosure < 0 or float(disclosure) / float(symbols) > DISCLOSURE_BITS_PER_SYMBOL_MAX:
            return False
    return True


def initial_state(route: str) -> dict[str, Any]:
    if route not in ROUTES:
        raise ValueError("unknown v7 subroute")
    return {"route": route, "status": "pending", "stage": None, "stage_count": 0,
            "execute_count": 0, "replay_count": 0, "artifacts": {}, "blocker": None}


def _validate_state(state: Any) -> None:
    if not isinstance(state, Mapping):
        raise ValueError("state must be a mapping")
    if state.get("route") not in ROUTES or state.get("status") not in STATUSES:
        raise ValueError("invalid state identity")
    stage = state.get("stage")
    if stage is not None and stage not in _STAGES:
        raise ValueError("invalid stage")
    if not isinstance(state.get("stage_count"), int) or not 0 <= state["stage_count"] <= 2:
        raise ValueError("invalid stage count")
    for name in ("execute_count", "replay_count"):
        if not isinstance(state.get(name), int) or not 0 <= state[name] <= 1:
            raise ValueError(f"invalid {name}")
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts).difference(_ARTIFACT_KEYS):
        raise ValueError("invalid artifact ledger")


def _validate_report(report: Any) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("report must be a mapping")
    required = {"event", "payload", "report_sha256"}
    if required.difference(report) or set(report).difference(required):
        raise ValueError("report must contain exactly event/payload/report_sha256")
    if report.get("event") not in STATUSES:
        raise ValueError("invalid report event")
    if not isinstance(report.get("payload"), Mapping):
        raise ValueError("report payload must be a mapping")
    if not isinstance(report.get("report_sha256"), str) or len(report["report_sha256"]) != 64:
        raise ValueError("report_sha256 must be a 64-hex SHA256")


def _require_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"payload requires non-empty {key}")
    return value


def _require_int(payload: Mapping[str, Any], key: str) -> int:
    value = _as_int(payload.get(key))
    if value < 0:
        raise ValueError(f"payload requires integer {key}")
    return value


def _check_planned(state: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    stage = payload.get("stage")
    if stage not in _STAGES:
        raise ValueError("planned payload requires stage in (canary, development)")
    plan_sha = _require_text(payload, "plan_sha256")
    _require_int(payload, "frame_count")
    roots = payload.get("roots")
    if not isinstance(roots, Mapping) or not roots:
        raise ValueError("planned payload requires non-empty roots mapping")
    if state["stage"] is None:
        # First plan of the subroute must be the sacrificed 4+4 canary.
        if stage != "canary" or _as_int(payload.get("frame_count")) != 2 * CANARY_FRAMES_PER_STRATUM:
            raise ValueError("first plan must be the 4+4 canary")
    else:
        if state["stage"] != "canary" or stage != "development" \
                or _as_int(payload.get("frame_count")) != 2 * DEVELOPMENT_FRAMES_PER_STRATUM:
            raise ValueError("second plan must be the 16+16 development plan")
        replay = _require_text(payload, "replay_report_sha256")
        if replay != state["artifacts"].get("canary_replay"):
            raise ValueError("development plan must reference the recorded canary replay report")
        if canary_gate_failed(payload):
            raise ValueError("canary gate already failed; development plan is not allowed")
    key = f"{stage}_plan"
    if state["artifacts"].get(key) is not None:
        raise ValueError(f"exactly-once planning: {key} already recorded")
    state["artifacts"][key] = plan_sha
    state["stage"] = stage
    state["stage_count"] += 1
    if stage == "development":
        # A fresh stage starts a fresh exactly-once execute/replay budget.
        state["execute_count"] = 0
        state["replay_count"] = 0


def _check_executed(state: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    if state["stage"] not in _STAGES:
        raise ValueError("execute requires a recorded plan stage")
    _require_text(payload, "run_manifest_sha256")
    if state["execute_count"] != 0:
        raise ValueError("exactly-once execute violated")
    key = f"{state['stage']}_run_manifest"
    if state["artifacts"].get(key) is not None:
        raise ValueError(f"exactly-once execute: {key} already recorded")
    state["artifacts"][key] = _require_text(payload, "run_manifest_sha256")
    state["execute_count"] = 1


def _check_verified(state: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    if state["stage"] not in _STAGES or state["execute_count"] != 1:
        raise ValueError("verify requires one executed stage")
    _require_text(payload, "replay_report_sha256")
    if state["replay_count"] != 0:
        raise ValueError("exactly-once replay violated")
    key = f"{state['stage']}_replay"
    if state["artifacts"].get(key) is not None:
        raise ValueError(f"exactly-once replay: {key} already recorded")
    state["artifacts"][key] = _require_text(payload, "replay_report_sha256")
    state["replay_count"] = 1


def _check_gate(state: Mapping[str, Any], event: str, payload: Mapping[str, Any]) -> None:
    stage = state["stage"]
    if stage is None:
        raise ValueError("gate requires a completed stage")
    _require_text(payload, "replay_report_sha256")
    recorded = state["artifacts"].get(f"{stage}_replay")
    if payload["replay_report_sha256"] != recorded:
        raise ValueError("gate must reference the recorded replay report")
    if event == "failed_canary":
        if stage != "canary" or not canary_gate_failed(payload):
            raise ValueError("failed_canary requires a 0/4-in-either-stratum canary")
    elif event == "ready":
        if stage != "development" or not development_ready(payload):
            raise ValueError("ready requires the frozen development gate")
    elif event == "non_ready":
        if stage != "development" or development_ready(payload):
            raise ValueError("non_ready requires a development gate miss")
    else:
        raise ValueError(f"unexpected gate event {event}")


def _check_blocked(payload: Mapping[str, Any]) -> None:
    _require_text(payload, "blocker")


def _check_transition(state: Mapping[str, Any], event: str, payload: Mapping[str, Any]) -> None:
    if event == "engineered":
        _require_text(payload, "engineering_acceptance_sha256")
        tiers = payload.get("tiers")
        if not isinstance(tiers, Mapping):
            raise ValueError("engineered payload requires tier results")
        for tier in ("T0", "T1", "T2", "T3"):
            result = tiers.get(tier)
            if not isinstance(result, Mapping) or _as_int(result.get("passed")) < 0 \
                    or _as_int(result.get("failed")) != 0:
                raise ValueError(f"engineered tier {tier} must be passed")
        if state["artifacts"].get("engineering_acceptance") is not None:
            raise ValueError("exactly-once engineering acceptance")
        state["artifacts"]["engineering_acceptance"] = _require_text(payload, "engineering_acceptance_sha256")
    elif event == "planned":
        _check_planned(state, payload)
    elif event == "executed":
        _check_executed(state, payload)
    elif event == "verified":
        _check_verified(state, payload)
    elif event in ("ready", "non_ready", "failed_canary"):
        _check_gate(state, event, payload)
    elif event == "blocked":
        _check_blocked(payload)
        state["blocker"] = _require_text(payload, "blocker")
    else:
        raise ValueError(f"unexpected transition event {event}")


def advance(state: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    """Return the next state after a hash-bound verified report, or raise.

    The caller's state is never mutated: a fresh copy is returned.  The report
    is immutable (payload + recomputed SHA256 must match) and the event must be
    a frozen successor of the current status.
    """
    _validate_state(state)
    _validate_report(report)
    payload = report["payload"]
    if _sha(_compact(payload)) != report["report_sha256"]:
        raise ValueError("report hash binding violated")
    event = report["event"]
    if event not in TRANSITIONS[state["status"]]:
        raise ValueError(f"invalid transition {state['status']} -> {event}")
    next_state = copy.deepcopy(dict(state))
    _check_transition(next_state, event, payload)
    next_state["status"] = event
    return next_state


def statuses(ladder: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """One status per subroute."""
    return {route: state["status"] for route, state in ladder.items()}


def initial_ladder(routes: Any = ROUTES) -> dict[str, dict[str, Any]]:
    return {route: initial_state(route) for route in routes}


def advance_ladder(ladder: Mapping[str, Mapping[str, Any]], route: str,
                   report: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Advance one subroute of a ladder; the other subroute states are kept."""
    if route not in ladder:
        raise ValueError("unknown subroute")
    next_ladder = copy.deepcopy(dict(ladder))
    next_ladder[route] = advance(next_ladder[route], report)
    return next_ladder


def save_state(state: Mapping[str, Any], path: Any) -> str:
    """Persist a state to an immutable JSON artifact; returns the state hash."""
    _validate_state(state)
    document = {"state": dict(state), "state_sha256": _sha(_compact(state))}
    path = Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8") as handle:
        handle.write(json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n")
    return document["state_sha256"]


def load_state(path: Any) -> dict[str, Any]:
    """Resume a state from its immutable artifact; hash mismatch fails closed."""
    with open(str(path), "r", encoding="utf8") as handle:
        document = json.load(handle)
    state = document.get("state")
    if not isinstance(state, Mapping) or not isinstance(document.get("state_sha256"), str):
        raise ValueError("invalid state artifact")
    if _sha(_compact(state)) != document["state_sha256"]:
        raise ValueError("state hash binding violated")
    _validate_state(state)
    return dict(state)


def save_ladder(ladder: Mapping[str, Mapping[str, Any]], path: Any) -> str:
    """Persist the whole ladder (dict of subroute states) to one artifact."""
    for state in ladder.values():
        _validate_state(state)
    document = {"ladder": {route: dict(state) for route, state in ladder.items()},
                "ladder_sha256": _sha(_compact(ladder))}
    path = Path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8") as handle:
        handle.write(json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n")
    return document["ladder_sha256"]


def load_ladder(path: Any) -> dict[str, dict[str, Any]]:
    with open(str(path), "r", encoding="utf8") as handle:
        document = json.load(handle)
    ladder = document.get("ladder")
    if not isinstance(ladder, Mapping) or not isinstance(document.get("ladder_sha256"), str):
        raise ValueError("invalid ladder artifact")
    for route, state in ladder.items():
        if route not in ROUTES:
            raise ValueError("invalid ladder artifact")
        _validate_state(state)
    if _sha(_compact(ladder)) != document["ladder_sha256"]:
        raise ValueError("ladder hash binding violated")
    return {route: dict(state) for route, state in ladder.items()}
