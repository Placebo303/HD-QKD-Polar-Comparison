"""Fake-only structural tests for the M3-a nested row appender.

No production PEG constructor, decoder, DE, channel, bundle or data is used.
"""
from __future__ import annotations

import copy
import json
import sys
from types import SimpleNamespace

import pytest

from comparison_bench.src.comparison_bench.cli import m3a_nested_construct as m3a


def _tiny_base() -> dict:
    # Eight variables each have degree two. The eight check-pairs are unique,
    # so the Tanner graph has no 4-cycle. Labels make the five base rows full
    # rank over GF(32).
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2),
             (1, 3), (1, 4), (2, 3), (2, 4)]
    triples = []
    for variable, (left, right) in enumerate(pairs):
        triples.extend([(left, variable, 1), (right, variable, 2)])
    return {"status": "ok", "n": 8, "m": 5,
            "triples": triples, "min_girth": 6}


def _tiny_construct(seed=1234):
    calls = []

    def base_fn(m, base_seed, trials):
        calls.append((m, base_seed, trials))
        return copy.deepcopy(_tiny_base())

    result = m3a.construct(base_fn=base_fn, base_seed=41,
                           extension_seed=seed, n=8, m_base=5,
                           n_rows=2, row_degree=2, q=32, trials=3)
    return result, calls


def test_construct_preserves_prefix_labels_and_is_deterministic():
    first, first_calls = _tiny_construct()
    second, second_calls = _tiny_construct()

    assert first_calls == [(5, 41, 3), (5, 41, 3)]
    assert second_calls == first_calls
    assert first["twice_identical"] is True
    assert first["triples"] == second["triples"]
    assert first["triples"][:len(first["base_triples"])] == first["base_triples"]
    assert first["base_prefix_unchanged"] is True
    assert all(1 <= label < 32 for _, _, label in first["added_triples"])


def test_one_arm_per_construct_uses_two_base_and_two_extension_builds(monkeypatch):
    base_calls = []
    extension_calls = []

    def base_fn(m, base_seed, trials):
        base_calls.append((m, base_seed, trials))
        return copy.deepcopy(_tiny_base())

    original_append_rows = m3a.append_rows

    def counted_append_rows(*args, **kwargs):
        extension_calls.append(kwargs["seed"])
        return original_append_rows(*args, **kwargs)

    monkeypatch.setattr(m3a, "append_rows", counted_append_rows)
    result = m3a.construct(base_fn=base_fn, base_seed=41,
                           extension_seed=1234, n=8, m_base=5,
                           n_rows=2, row_degree=2, q=32, trials=3)

    assert result["twice_identical"] is True
    assert base_calls == [(5, 41, 3), (5, 41, 3)]
    assert extension_calls == [1234, 1234]


def test_appended_rows_are_degree_two_with_unique_variables_and_no_four_cycles():
    result = m3a.append_rows(_tiny_base(), seed=1234,
                             n_rows=2, row_degree=2)
    added = result["added_triples"]
    variables = [variable for _, variable, _ in added]

    assert result["added_row_degrees"] == [2, 2]
    assert len(variables) == len(set(variables))
    assert result["base_four_cycles"] == 0
    assert result["four_cycles"] == 0
    assert result["base_rank"] == 5
    assert result["rank"] == 7
    assert result["min_girth"] == 6


def test_impossible_extension_fails_without_partial_output():
    base = {"status": "ok", "n": 4, "m": 1,
            "triples": [(0, variable, 1) for variable in range(4)]}
    with pytest.raises(m3a.ConstructionFailure, match="admissible variables"):
        m3a.append_rows(base, seed=77, n_rows=1, row_degree=2)


def test_base_constructor_is_required_injected_input():
    with pytest.raises(TypeError):
        m3a.construct(base_seed=1, extension_seed=2)  # type: ignore[call-arg]


def test_cli_dry_mode_does_not_enter_production_constructor(capsys):
    assert m3a.main([]) == 0
    output = capsys.readouterr().out
    assert '"status": "dry"' in output
    assert "--execute-construction" in output


def test_cli_executes_only_selected_frozen_arm_and_emits_one_json_object(
        monkeypatch, capsys):
    constructor = object()
    fake_runner = SimpleNamespace(construct_standalone=constructor)
    module_name = (
        "comparison_bench.src.comparison_bench.cli.x1_arm_runner")
    monkeypatch.setitem(sys.modules, module_name, fake_runner)
    calls = []

    def fake_construct(**kwargs):
        calls.append(kwargs)
        return {"status": "ok", "base_seed": kwargs["base_seed"],
                "extension_seed": kwargs["extension_seed"]}

    monkeypatch.setattr(m3a, "construct", fake_construct)
    assert m3a.main(["--arm", "2", "--execute-construction",
                     "--execution-authorized"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "status": "ok", "arm": 2,
        "base_seed": 2026092011,
        "extension_seed": 2026096811,
    }
    assert len(calls) == 1
    assert calls[0]["base_fn"] is constructor


def test_cli_requires_arm_before_importing_production_runner(capsys):
    assert m3a.main(["--execute-construction",
                     "--execution-authorized"]) == 2
    assert "--arm 1 or --arm 2 is required" in capsys.readouterr().err


def test_frozen_seed_pair_accepts_only_the_two_packet_arms():
    assert m3a.frozen_seed_pair(1) == (2026092001, 2026096801)
    assert m3a.frozen_seed_pair(2) == (2026092011, 2026096811)
    with pytest.raises(m3a.ConstructionFailure, match="arm must be 1 or 2"):
        m3a.frozen_seed_pair(3)
