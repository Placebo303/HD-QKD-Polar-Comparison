import importlib.util
from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SECURITY_REPORTS = _REPO_ROOT / "tools" / "security_reports"
sys.path.insert(0, str(_SECURITY_REPORTS))
from tools.security_reports.round2_build_finite_key_audit_table import _effective_pair_count


_EXPERIMENT_PATH = _REPO_ROOT / "experiments" / "run_real_polar_max_pie.py"
_SPEC = importlib.util.spec_from_file_location("run_real_polar_max_pie", _EXPERIMENT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_EXPERIMENT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_EXPERIMENT)


def test_candidate_seed_is_stable_and_candidate_specific() -> None:
    args = (12345, 64, 120, 3, 1800, 2)
    assert _EXPERIMENT._candidate_seed(*args) == _EXPERIMENT._candidate_seed(*args)
    assert _EXPERIMENT._candidate_seed(*args) != _EXPERIMENT._candidate_seed(12345, 64, 120, 3, 1801, 2)


def test_fer_acceptance_uses_declared_one_sided_bound() -> None:
    zero_errors = _EXPERIMENT._fer_metadata(0, 100)
    assert zero_errors["fer_point_estimate"] == 0.0
    assert zero_errors["fer_upper_bound"] > 0.0
    assert zero_errors["fer_acceptance_rule"] == "one_sided_wilson_upper_lt_threshold"
    assert zero_errors["fer_accepted"] == int(zero_errors["fer_upper_bound"] < _EXPERIMENT._FER_THRESH)


def test_layer_choice_and_best_gain_use_the_same_candidate() -> None:
    sc = {"decoder_mode": "sc", "gain": 0.25, "k": 1024}
    scl = {"decoder_mode": "scl", "gain": 0.30, "k": 1229}
    chosen = _EXPERIMENT._choose_layer_meta(sc, scl)
    assert chosen is scl
    assert chosen["gain"] == pytest.approx(0.30)


def test_actual_kept_bits_do_not_apply_block_success_twice() -> None:
    actual, actual_rule = _effective_pair_count(
        n_pairs=1000,
        layer_fraction=0.4,
        accepted_frame_fraction=0.8,
        block_success_rate=0.5,
        layer_fraction_source_tag="actual_from_replay_kept_bits",
    )
    surrogate, surrogate_rule = _effective_pair_count(
        n_pairs=1000,
        layer_fraction=0.4,
        accepted_frame_fraction=0.8,
        block_success_rate=0.5,
        layer_fraction_source_tag="surrogate_from_layers_success_best",
    )
    assert actual == pytest.approx(320.0)
    assert actual_rule == "block_success_already_in_actual_kept_bits"
    assert surrogate == pytest.approx(160.0)
    assert surrogate_rule == "block_success_applied_to_surrogate_layer_fraction"
