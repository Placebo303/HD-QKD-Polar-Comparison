"""R3 focused tests: frozen cells/seeds, plan, gates, A1 boundary, refusal (R307).

Fake/tiny only: the production decoder is never imported, no scientific call
is made and no root outside pytest tmp paths is created. Entry-boundary tests
inject fake decoders and count their calls (must stay zero on refusal/block).
The 24-cell real-graph admission is R309 (no-decoder profile), not pytest.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d10_r3_development.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d10_r3_fresh_scaling as r3  # noqa: E402

runner = _load_module("v72p2d10_runner_r3_test", RUNNER_PATH)


def _fake_graph(arm, width, seed):
    cell = r3.degree_cell(arm, width)
    n, m = cell["n"], cell["m"]
    H = np.zeros((m, n), dtype=np.int64)
    for variable in range(n):
        H[variable % m, variable] = 1
    if arm == "PEG_DV3_MATCHED":
        rng = np.random.default_rng(int(seed) + 7919)
        while int(np.count_nonzero(H)) < n + 40:
            H[int(rng.integers(0, m)), int(rng.integers(0, n))] = 1
    return {"arm": arm, "width": int(width), "graph_seed": int(seed),
            "n": n, "m": m, "E": int(np.count_nonzero(H)), "edges": [],
            "coefficients": [], "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _zero_syndrome(H, x):
    return np.zeros(H.shape[0], dtype=np.uint8)


class _Result:
    def __init__(self, x_hat, syndrome_ok):
        self.x_hat = np.asarray(x_hat, dtype=np.uint8)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = 1
        self.status = "converged_exact"
        self.belief_provenance = "FAKE"


def _tagged(width, arm, graph_seed, block_seed, exact, syndrome_ok=None):
    return {"call_idx": 0, "width": width, "arm": arm,
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": r3.R3_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome_ok is None else syndrome_ok}


def _full_tagged_records(mix_exact, dv3_exact, width=128):
    records = []
    for arm, counts in (("PEG_DV23_LAM2_045", mix_exact),
                        ("PEG_DV3_MATCHED", dv3_exact)):
        for graph_seed, total in zip(r3.GRAPH_SEEDS[width], counts):
            for i, block_seed in enumerate(r3.BLOCK_SEEDS[width]):
                records.append(_tagged(width, arm, graph_seed, block_seed,
                                       i < total))
    return records


# --------------------------------------------------------------------------- #
# R302/R303 guards: frozen tables/seeds, no source auth, no replacement path
# --------------------------------------------------------------------------- #
def test_r3_frozen_tables_exact():
    assert r3.degree_cell("PEG_DV3_MATCHED", 128) == {
        "n": 128, "m": 118, "var_counts": {3: 128},
        "check_counts": {3: 88, 4: 30}, "E": 384}
    assert r3.degree_cell("PEG_DV3_MATCHED", 256) == {
        "n": 256, "m": 236, "var_counts": {3: 256},
        "check_counts": {3: 176, 4: 60}, "E": 768}
    assert r3.degree_cell("PEG_DV23_LAM2_045", 128) == {
        "n": 128, "m": 118, "var_counts": {3: 57, 2: 71},
        "check_counts": {3: 77, 2: 41}, "E": 313}
    assert r3.degree_cell("PEG_DV23_LAM2_045", 256) == {
        "n": 256, "m": 236, "var_counts": {3: 115, 2: 141},
        "check_counts": {3: 155, 2: 81}, "E": 627}
    for (arm, width), cell in sorted(r3.DEGREE_TABLE.items()):
        frozen = r3.degree_cell(arm, width)
        assert frozen["E"] == 2 * frozen["var_counts"].get(2, 0) \
            + 3 * frozen["var_counts"].get(3, 0)
        assert frozen == r2.degree_cell(arm, width)  # no R2 drift
    with pytest.raises(KeyError):
        r3.degree_cell("PEG_DV3_MATCHED", 64)  # R2-only width out of scope


def test_r3_frozen_seeds_exact_and_disjoint():
    assert r3.GRAPH_SEEDS == {
        128: tuple(range(2026092401, 2026092407)),
        256: tuple(range(2026092501, 2026092507))}
    assert r3.BLOCK_SEEDS == {
        128: tuple(range(2026092601, 2026092613)),
        256: tuple(range(2026092701, 2026092713))}
    graph = {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
    block = {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
    assert len(graph) == 12 and graph.isdisjoint(block)
    r2seeds = {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds} \
        | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
    assert graph.isdisjoint(r2seeds) and block.isdisjoint(r2seeds)
    with pytest.raises(ValueError):
        r3.build_graph("PEG_DV3_MATCHED", 128, 2026092204)  # R2 seed refused


def test_r3_no_source_auth_or_replacement_mechanism():
    assert not hasattr(r3, "BATCH_AUTHORIZED")
    assert not hasattr(r3, "REPLACEMENT_SEEDS")
    assert not hasattr(r3, "PROFILE_REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.r3_batch is False
    assert args.execution_authorized is False


def test_r3_reuse_not_duplication():
    assert r3.ARMS == r2.ARMS and r3.ARM_ROLE == r2.ARM_ROLE
    assert r3.DECODER_MAX_ITER == 90 and r3.DAMPING_ALPHA == 1.0
    assert r3.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert r2.coefficient_seed(128, 2026092401) == \
        r2.coefficient_seed(128, 2026092401)
    assert r2.coefficient_seed(128, 2026092401) != \
        r2.coefficient_seed(128, 2026092402)
    assert r3.refuse_out_root is r2.refuse_out_root
    assert r3.build_graph.__doc__ and "r2.build_graph" in r3.build_graph.__doc__


# --------------------------------------------------------------------------- #
# R305: plan identities and conditional dispatch
# --------------------------------------------------------------------------- #
def test_r3_plan_144_per_width_conditional_288():
    n128 = r3.build_call_plan(128)
    assert len(n128) == 144
    assert [e["call_idx"] for e in n128] == list(range(144))
    assert n128[0] == {"call_idx": 0, "width": 128,
                       "arm": "PEG_DV3_MATCHED", "graph_seed": 2026092401,
                       "block_seed": 2026092601}
    assert n128[-1]["arm"] == "PEG_DV23_LAM2_045"
    assert n128[-1]["graph_seed"] == 2026092406
    assert n128[-1]["block_seed"] == 2026092612
    full = r3.build_full_plan()
    assert len(full) == 288 == r3.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in full] == list(range(288))
    assert {e["width"] for e in full[:144]} == {128}
    assert {e["width"] for e in full[144:]} == {256}
    with pytest.raises(KeyError):
        r3.build_call_plan(64)


def test_r3_conditional_dispatch_gate():
    assert r3.n256_permitted(r3.REPRODUCED) is True
    assert r3.n256_permitted(r3.NEGATIVE) is False
    assert r3.n256_permitted(r3.AMBIGUOUS) is False
    assert r3.n256_permitted(r3.ENGINEERING_BLOCKED) is False


# --------------------------------------------------------------------------- #
# R305: gate boundaries (verbatim 6-clause REPRODUCED, NEGATIVE, AMBIGUOUS)
# --------------------------------------------------------------------------- #
def _tallies(mix, dv3):
    return r3.R3WidthTallies(128, mix, dv3)


def test_r3_reproduced_all_six_clauses():
    good = _tallies((4, 4, 3, 3, 2, 2), (1, 1, 1, 1, 1, 1))  # M=18 d=12
    assert (good.mix_pool, good.dv3_pool) == (18, 6)
    assert r3.classify_r3(good) == r3.REPRODUCED


@pytest.mark.parametrize("mix,dv3", [
    ((4, 4, 3, 3, 2, 1), (1, 1, 1, 1, 1, 1)),  # M=17 < 18
    ((4, 4, 3, 3, 2, 2), (1, 1, 1, 1, 2, 1)),  # margin 11 < 12
    ((9, 9, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0)),  # 2 pair wins < 5
    ((6, 6, 6, 0, 0, 0), (0, 0, 0, 0, 0, 0)),  # 3 graphs >= 2 < 4
    ((4, 4, 3, 3, 2, 2), (2, 2, 1, 1, 1, 0)),  # C=7 > 6
])
def test_r3_reproduced_clause_boundaries_fall_to_gate(mix, dv3):
    tallies = _tallies(mix, dv3)
    assert r3.classify_r3(tallies) in (r3.NEGATIVE, r3.AMBIGUOUS)


def test_r3_negative_and_ambiguous():
    assert r3.classify_r3(_tallies((1,) * 6, (0,) * 6)) == r3.NEGATIVE
    assert r3.classify_r3(_tallies((2,) * 6, (8,) * 6)) == r3.NEGATIVE
    mid = _tallies((3, 3, 2, 2, 2, 2), (1, 1, 1, 1, 1, 1))  # M=14 d=8
    assert r3.classify_r3(mid) == r3.AMBIGUOUS
    good = _tallies((4, 4, 3, 3, 2, 2), (1, 1, 1, 1, 1, 1))
    assert r3.classify_r3(good, "decoder crash X") == r3.ENGINEERING_BLOCKED
    with pytest.raises(TypeError):
        r3.classify_r3({"mix": [1] * 6})  # non-R3 evidence refused


def test_r3_terminals_all_six():
    assert r3.route_terminal(r3.NEGATIVE) == "D10_R3_N128_NOT_REPRODUCED"
    assert r3.route_terminal(r3.AMBIGUOUS) == "D10_R3_N128_AMBIGUOUS"
    assert r3.route_terminal(r3.REPRODUCED, r3.NEGATIVE) == \
        "D10_R3_FINITE_WIDTH_DECAY"
    assert r3.route_terminal(r3.REPRODUCED, r3.AMBIGUOUS) == \
        "D10_R3_N256_AMBIGUOUS"
    assert r3.route_terminal(r3.REPRODUCED, r3.REPRODUCED) == \
        "D10_R3_WIDE_L1_SIGNAL_REPRODUCED"
    assert r3.route_terminal(r3.REPRODUCED, r3.ENGINEERING_BLOCKED) == \
        "D10_R3_ENGINEERING_BLOCKED"
    assert r3.route_terminal(r3.ENGINEERING_BLOCKED) == \
        "D10_R3_ENGINEERING_BLOCKED"


# --------------------------------------------------------------------------- #
# R305: exact/syndrome isolation + A1 non-pooling
# --------------------------------------------------------------------------- #
def test_r3_syndrome_never_substitutes_for_exact():
    # All syndrome-valid but exact-quiet: gate sees only exact -> NEGATIVE.
    records = _full_tagged_records((1,) * 6, (0,) * 6)
    for record in records:
        record["syndrome_ok"] = True
    tallies = r3.tallies_from_r3_records(records, 128)
    assert (tallies.mix_pool, tallies.dv3_pool) == (6, 0)
    assert r3.classify_r3(tallies) == r3.NEGATIVE


def test_r3_a1_records_cannot_enter_gate():
    a1_like = [{"width": 64, "arm": "PEG_DV3_MATCHED",
                "graph_seed": 2026092201, "block_seed": 2026092301,
                "exact": True, "syndrome_ok": True}] * 144
    with pytest.raises(ValueError):
        r3.tallies_from_r3_records(a1_like, 64)
    no_tag = [_tagged(128, "PEG_DV3_MATCHED", 2026092401, seed, True)
              for seed in r3.BLOCK_SEEDS[128]]
    for record in no_tag:
        del record["batch_id"]
    with pytest.raises(ValueError):
        r3.tallies_from_r3_records(no_tag * 12, 128)
    wrong_tag = [dict(rec, batch_id="d10-r2-batch") for rec in no_tag] * 12
    with pytest.raises(ValueError):
        r3.tallies_from_r3_records(wrong_tag, 128)
    short = _full_tagged_records((12,) * 6, (0,) * 6)
    with pytest.raises(ValueError):
        r3.tallies_from_r3_records(short[:-1], 128)  # 143 != 144


def test_r3_mcnemar_descriptive_only():
    records = _full_tagged_records((12,) * 6, (0,) * 6)
    paired = r3.describe_paired(records, 128)
    assert paired["discordant_mix_only"] == 72
    assert paired["discordant_dv3_only"] == 0
    assert 0.0 <= paired["mcnemar_one_sided_p"] <= 1.0
    assert paired["descriptive_only"] is True
    tallies = r3.tallies_from_r3_records(records, 128)
    assert r3.classify_r3(tallies) == r3.REPRODUCED  # gate needs no p-value


# --------------------------------------------------------------------------- #
# R303/R304: unauthorized refusal + admission block (fake decoders only)
# --------------------------------------------------------------------------- #
def test_r3_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    out = tmp_path / "must_not_exist"
    assert runner.main(["--r3-batch", "--out-root", str(out)]) == 2
    assert not out.exists()
    assert "comparison_bench.formal_ir.v35_algorithm_development" \
        not in sys.modules


def test_r3_nonadmitted_graph_blocks_width_with_zero_decoder_calls():
    cell = r3.degree_cell("PEG_DV23_LAM2_045", 128)
    blocked = {"arm": "PEG_DV23_LAM2_045", "width": 128,
               "graph_seed": 2026092401, "n": cell["n"], "m": cell["m"],
               "E": 0, "edges": [], "coefficients": [], "dense": None,
               "structure": None, "status": "construction_failed",
               "admitted": False, "failure_reason": "A3_single_component"}
    calls = []

    def fake_decode(*_args, **_kwargs):
        calls.append(1)
        return _Result(np.zeros(cell["n"]), True)

    graphs = {(arm, 128, seed): _fake_graph(arm, 128, seed)
              for arm in r3.ARMS for seed in r3.GRAPH_SEEDS[128]}
    graphs[("PEG_DV23_LAM2_045", 128, 2026092401)] = blocked
    blocks = {128: {seed: {"u1": np.zeros(cell["n"], dtype=np.int64),
                             "prior": np.full((cell["n"], 32), 1.0 / 32)}
                      for seed in r3.BLOCK_SEEDS[128]}}
    outcome = r3.execute_width(128, r3.build_call_plan(128), graphs, blocks,
                               fake_decode, _zero_syndrome)
    assert calls == []
    assert outcome["records"] == []
    assert outcome["classification"] == r3.ENGINEERING_BLOCKED
    assert "without seed replacement" in outcome["engineering_reason"]
    assert not hasattr(r3, "REPLACEMENT_SEEDS")


# --------------------------------------------------------------------------- #
# R306: never-overwrite writer + fail-closed verifier (fake batch, tmp only)
# --------------------------------------------------------------------------- #
def _run_fake_batch(tmp_path, name="root"):
    def fake_prior(_root=None):
        return (np.full(4, 0.25), np.full((32 * 32, 4), 1.0 / (32 * 32)),
                np.full((32, 4), 1.0 / 32))

    def fake_sample(_p_b, _p_f, n, seed):
        rng = np.random.default_rng(int(seed))
        return {"bob": rng.integers(0, 4, size=int(n)),
                "u1": np.zeros(int(n), dtype=np.int64)}

    def fake_decode(H, prior, syn, max_iter=None, damping_alpha=None,
                    warm_beliefs=None, field=None):
        n = H.shape[1]
        if int(np.count_nonzero(H)) > n + 20:  # control marker stays quiet
            return _Result(np.full(n, 1), False)
        return _Result(np.zeros(n), True)

    out = tmp_path / name
    summary = runner.run_r3_batch(
        str(out), "ignored-model-f", fake_decode, _zero_syndrome,
        build_graph_fn=_fake_graph, load_prior_fn=fake_prior,
        sample_fn=fake_sample)
    assert summary["terminal"] == "D10_R3_WIDE_L1_SIGNAL_REPRODUCED"
    assert summary["scientific_calls"] == 288
    assert summary["setup_calls"] == r3.SETUP_CALL_CEILING == 50
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is True
    return out


def test_r3_writer_never_overwrites(tmp_path):
    out = _run_fake_batch(tmp_path)
    with pytest.raises(FileExistsError):
        runner.run_r3_batch(
            str(out), "ignored-model-f", None, None,
            build_graph_fn=_fake_graph,
            load_prior_fn=lambda _r=None: (None, None, None))


def test_r3_verify_fail_closed_on_tampered_exact(tmp_path):
    import csv
    out = _run_fake_batch(tmp_path)
    path = out / "decoder_records.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows and any(row["exact"] == "True" for row in rows)
    target = next(row for row in rows if row["exact"] == "True")
    target["exact"] = "False"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False


def test_r3_verify_fail_closed_on_engineering_blocked_width(tmp_path):
    out = _run_fake_batch(tmp_path, name="root_blocked")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][0]["engineering_reason"] = "decoder crash X"
    summary["width_results"][0]["classification"] = r3.ENGINEERING_BLOCKED
    summary["terminal"] = r3.T_ENGINEERING_BLOCKED
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False


def test_r3_verify_recomputes_gate_not_stored_label(tmp_path):
    # Stored REPRODUCED with quiet counts must fail recomputation.
    out = _run_fake_batch(tmp_path, name="root_relabel")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][0]["mix_exact"] = [0] * 6
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False
