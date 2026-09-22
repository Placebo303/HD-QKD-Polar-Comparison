"""D12 focused tests: frozen cells/seeds, plan, gates, boundary, refusal (D1207).

Fake/tiny only: the production decoder is never imported, no scientific call
is made and no root outside pytest tmp paths is created. Entry-boundary tests
inject fake decoders and count their calls (must stay zero on refusal/block).
The 36-cell real-graph admission is D1209 (no-decoder profile), not pytest.
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

RUNNER_PATH = ROOT / "scripts" / "v72p2d12_development.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d10_r3_fresh_scaling as r3  # noqa: E402
import comparison_bench.formal_ir.v72p2d11_forward_app as d11  # noqa: E402
import comparison_bench.formal_ir.v72p2d12_finite_l1_degree as d12  # noqa: E402

runner = _load_module("v72p2d12_runner_test", RUNNER_PATH)


def _fake_graph(arm, width, seed):
    cell = d12.degree_cell(arm, width)
    n, m = cell["n"], cell["m"]
    H = np.zeros((m, n), dtype=np.int64)
    for variable in range(n):
        H[variable % m, variable] = 1
    if arm == "L050":
        H[0, 1] = 7  # challenger marker: fake decoder reads exact from this
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


def _fake_decode(H, prior, syn, max_iter=None, damping_alpha=None,
                 warm_beliefs=None, field=None):
    n = H.shape[1]
    if int(H[0, 1]) == 7:
        return _Result(np.zeros(n), True)
    return _Result(np.full(n, 1), True)


def _tagged(width, arm, graph_seed, block_seed, exact, syndrome_ok=None):
    return {"call_idx": 0, "width": width, "arm": arm,
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": d12.D12_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome_ok is None else syndrome_ok}


def _full_tagged_records(counts, width=128):
    records = []
    for arm in d12.ARMS:
        for graph_seed, total in zip(d12.GRAPH_SEEDS[width], counts[arm]):
            for i, block_seed in enumerate(d12.BLOCK_SEEDS[width]):
                records.append(_tagged(width, arm, graph_seed, block_seed,
                                       i < total))
    return records


def _tallies(width, counts):
    return d12.D12WidthTallies(width, counts["L045"], counts["L050"],
                               counts["L055"])


def _paired_for(width, counts):
    return d12.describe_paired(_full_tagged_records(counts, width), width)


# --------------------------------------------------------------------------- #
# D1203/D1207: frozen tables/seeds, no source auth, no replacement path
# --------------------------------------------------------------------------- #
def test_d12_frozen_tables_exact():
    assert d12.degree_cell("L045", 128) == {
        "n": 128, "m": 118, "var_counts": {2: 71, 3: 57},
        "check_counts": {2: 41, 3: 77}, "E": 313}
    assert d12.degree_cell("L050", 128) == {
        "n": 128, "m": 118, "var_counts": {2: 77, 3: 51},
        "check_counts": {2: 47, 3: 71}, "E": 307}
    assert d12.degree_cell("L055", 128) == {
        "n": 128, "m": 118, "var_counts": {2: 83, 3: 45},
        "check_counts": {2: 53, 3: 65}, "E": 301}
    assert d12.degree_cell("L045", 256) == {
        "n": 256, "m": 236, "var_counts": {2: 141, 3: 115},
        "check_counts": {2: 81, 3: 155}, "E": 627}
    assert d12.degree_cell("L050", 256) == {
        "n": 256, "m": 236, "var_counts": {2: 154, 3: 102},
        "check_counts": {2: 94, 3: 142}, "E": 614}
    assert d12.degree_cell("L055", 256) == {
        "n": 256, "m": 236, "var_counts": {2: 166, 3: 90},
        "check_counts": {2: 106, 3: 130}, "E": 602}
    for (arm, width), cell in sorted(d12.DEGREE_TABLE.items()):
        frozen = d12.degree_cell(arm, width)
        assert sum(frozen["var_counts"].values()) == frozen["n"]
        assert sum(frozen["check_counts"].values()) == frozen["m"]
        assert frozen["E"] == 2 * frozen["var_counts"][2] \
            + 3 * frozen["var_counts"][3]
        assert frozen["E"] == sum(d * c for d, c in
                                  frozen["check_counts"].items())
    with pytest.raises(KeyError):
        d12.degree_cell("L045", 64)  # R2-only width out of scope
    with pytest.raises(KeyError):
        d12.degree_cell("PEG_DV3_MATCHED", 128)  # predecessor arm refused


def test_d12_frozen_seeds_exact_and_disjoint():
    assert d12.GRAPH_SEEDS == {
        128: tuple(range(2026093001, 2026093007)),
        256: tuple(range(2026093101, 2026093107))}
    assert d12.BLOCK_SEEDS == {
        128: tuple(range(2026093201, 2026093213)),
        256: tuple(range(2026093301, 2026093313))}
    graph = {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
    block = {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds}
    assert len(graph) == 12 and len(block) == 24
    assert graph.isdisjoint(block)
    priors = ({s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds})
    assert graph.isdisjoint(priors) and block.isdisjoint(priors)
    with pytest.raises(ValueError):
        d12.build_graph("L045", 128, 2026092401)  # R3 seed refused
    with pytest.raises(ValueError):
        d12.build_graph("L045", 128, 2026093201)  # block seed refused


def test_d12_no_source_auth_or_replacement_mechanism():
    assert not hasattr(d12, "BATCH_AUTHORIZED")
    assert not hasattr(d12, "REPLACEMENT_SEEDS")
    assert not hasattr(d12, "PROFILE_REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.d12_batch is False
    assert args.execution_authorized is False


def test_d12_reuse_not_duplication():
    assert d12.DECODER_MAX_ITER == 90 and d12.DAMPING_ALPHA == 1.0
    assert d12.Q == 32 and d12.POLY == 37
    assert d12.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d12.dispatch_l1 is r2.dispatch_l1
    assert d12.coefficient_seed is r2.coefficient_seed
    assert d12.refuse_out_root is r2.refuse_out_root
    assert "r2.build_degree_sequence_peg" in d12.build_graph.__doc__
    assert "r2.structural_record" in d12.build_graph.__doc__
    # Only forced degree counts differ: shared n/m per width, one builder.
    for width in d12.D12_WIDTHS:
        cells = [d12.degree_cell(arm, width) for arm in d12.ARMS]
        assert {c["n"] for c in cells} == {width}
        assert len({c["m"] for c in cells}) == 1
        assert len({tuple(sorted(c["var_counts"].items()))
                    for c in cells}) == 3


def test_d12_shared_constructor_three_arms_one_builder(monkeypatch):
    calls = []

    def spy(n, m, var_counts, check_counts, seed):
        calls.append({"n": n, "m": m, "var_counts": dict(var_counts),
                      "seed": seed})
        return {"status": "ok", "edges": [(0, 0), (1, 1)],
                "failure_reason": ""}

    monkeypatch.setattr(r2, "build_degree_sequence_peg", spy)
    seen = {}
    for arm in d12.ARMS:
        record = d12.build_graph(arm, 128, 2026093001)
        seen[arm] = record
        # No seed change: the frozen seed is echoed, never replaced.
        assert record["graph_seed"] == 2026093001
    assert len(calls) == 6  # construction + A6 replay per arm, one builder
    for arm in d12.ARMS:
        cell = d12.degree_cell(arm, 128)
        assert any(c["var_counts"] == cell["var_counts"] for c in calls)
    assert len({tuple(sorted(d12.degree_cell(arm, 128)["var_counts"].items()))
                for arm in d12.ARMS}) == 3
    assert not any(r["admitted"] for r in seen.values())  # tiny fake fails A1


# --------------------------------------------------------------------------- #
# D1203: plan identities (216/width, 432 full, both widths always measured)
# --------------------------------------------------------------------------- #
def test_d12_plan_216_per_width_432():
    n128 = d12.build_call_plan(128)
    assert len(n128) == 216 == d12.PER_WIDTH_CALLS
    assert [e["call_idx"] for e in n128] == list(range(216))
    assert n128[0] == {"call_idx": 0, "width": 128, "arm": "L045",
                       "graph_seed": 2026093001, "block_seed": 2026093201}
    assert n128[-1]["arm"] == "L055"
    assert n128[-1]["graph_seed"] == 2026093006
    assert n128[-1]["block_seed"] == 2026093212
    full = d12.build_full_plan()
    assert len(full) == 432 == d12.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in full] == list(range(432))
    assert {e["width"] for e in full[:216]} == {128}
    assert {e["width"] for e in full[216:]} == {256}
    with pytest.raises(KeyError):
        d12.build_call_plan(64)


def test_d12_budgets_frozen():
    assert d12.SCIENTIFIC_CALL_CEILING == 432
    assert d12.SETUP_CALL_CEILING == 62 == 36 + 24 + 2
    assert d12.WALL_BUDGET_S == 1800.0
    assert d12.PER_CALL_BUDGET_S == 120.0
    assert d12.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert len(d12.build_full_plan()) <= d12.SCIENTIFIC_CALL_CEILING


# --------------------------------------------------------------------------- #
# D1203: STABLE / MATERIAL_BETTER / ranking / split / terminals
# --------------------------------------------------------------------------- #
def _counts(l045, l050, l055):
    return {"L045": l045, "L050": l050, "L055": l055}


def test_d12_stable_boundaries():
    good = _tallies(128, _counts((3,) * 6, (4, 4, 3, 3, 2, 2), (0,) * 6))
    assert d12.is_stable(good, "L050") is True
    thin = _tallies(128, _counts((3,) * 6, (4, 4, 3, 3, 2, 1), (0,) * 6))
    assert d12.is_stable(thin, "L050") is False  # 17 < 18
    few = _tallies(128, _counts((3,) * 6, (6, 6, 6, 0, 0, 0), (0,) * 6))
    assert d12.is_stable(few, "L050") is False  # 3 graphs >= 2 < 5
    assert d12.is_stable(good, "L050", "decoder crash X") is False
    with pytest.raises(TypeError):
        d12.is_stable({"pool": 18}, "L050")  # non-D12 evidence refused


def _material_counts():
    # L050 beats L045 by >= 6 with discordance and 6/6 pair wins, both widths.
    return _counts((1,) * 6, (4, 4, 3, 3, 2, 2), (0,) * 6)


def test_d12_material_better_all_four_clauses():
    counts = _material_counts()
    t128 = _tallies(128, counts)
    t256 = _tallies(256, counts)
    p128 = _paired_for(128, counts)
    p256 = _paired_for(256, counts)
    assert d12.is_material_better(t128, t256, p128, p256, "L050") is True
    assert d12.is_material_better(t128, t256, p128, p256, "L055") is False


@pytest.mark.parametrize("counts", [
    # challenger pool 16 < 18: not STABLE
    _counts((1,) * 6, (4, 4, 3, 3, 1, 1), (0,) * 6),
    # pool 18 and STABLE but margin 18-13 = 5 < 6
    _counts((3, 3, 3, 2, 1, 1), (4, 4, 3, 3, 2, 2), (0,) * 6),
    # STABLE and margin 12 but pair wins 3 < 4
    _counts((2,) * 6, (2, 2, 2, 5, 5, 8), (0,) * 6),
])
def test_d12_material_better_clause_boundaries_fail(counts):
    t128 = _tallies(128, counts)
    t256 = _tallies(256, counts)
    p128 = _paired_for(128, counts)
    p256 = _paired_for(256, counts)
    assert d12.is_material_better(t128, t256, p128, p256, "L050") is False


def test_d12_material_better_discordance_and_both_widths():
    # Challenger-only discordance must exceed L045-only at both widths.
    counts = _counts((4, 4, 3, 3, 2, 2), (4, 4, 3, 3, 2, 2), (0,) * 6)
    t128 = _tallies(128, counts)
    t256 = _tallies(256, counts)
    p128 = _paired_for(128, counts)
    p256 = _paired_for(256, counts)
    assert p128["L050"]["challenger_only"] == 0
    assert d12.is_material_better(t128, t256, p128, p256, "L050") is False
    # Material at one width only is not MATERIAL_BETTER.
    weak = _counts((1,) * 6, (0,) * 6, (0,) * 6)
    assert d12.is_material_better(_tallies(128, _material_counts()),
                                 _tallies(256, weak),
                                 _paired_for(128, _material_counts()),
                                 _paired_for(256, weak), "L050") is False


def test_d12_ranking_total_worst_width_smaller_lambda2():
    base = _counts((0,) * 6, (4, 4, 3, 3, 2, 2), (4, 4, 3, 3, 2, 2))
    t128 = _tallies(128, base)
    t256 = _tallies(256, base)
    p128 = _paired_for(128, base)
    p256 = _paired_for(256, base)
    # Tie on total and worst width: smaller lambda2 (L050) wins.
    assert d12.route_terminal(t128, t256, p128, p256) == d12.T_SELECT_L050
    richer = _counts((0,) * 6, (4, 4, 3, 3, 2, 2), (5, 5, 4, 4, 3, 3))
    r128 = _tallies(128, richer)
    r256 = _tallies(256, richer)
    q128 = _paired_for(128, richer)
    q256 = _paired_for(256, richer)
    assert d12.route_terminal(r128, r256, q128, q256) == d12.T_SELECT_L055


def test_d12_split_width_conflict():
    # Challenger beats by >= 6 at one width but trails by > 2 at the other.
    split = _counts((6,) * 6, (0,) * 6, (0,) * 6)
    other = _counts((0,) * 6, (6,) * 6, (0,) * 6)
    assert d12.split_width_conflict(_tallies(128, other),
                                    _tallies(256, split)) is True
    assert d12.route_terminal(_tallies(128, other), _tallies(256, split),
                              _paired_for(128, other),
                              _paired_for(256, split)) == \
        d12.T_SPLIT_AMBIGUOUS
    # Widths favor opposing challengers.
    fav128 = _counts((0,) * 6, (6,) * 6, (1,) * 6)
    fav256 = _counts((0,) * 6, (1,) * 6, (6,) * 6)
    assert d12.split_width_conflict(_tallies(128, fav128),
                                    _tallies(256, fav256)) is True
    # Neither material, no conflict: retain the frozen reference.
    quiet = _counts((1,) * 6, (2,) * 6, (1,) * 6)
    assert d12.split_width_conflict(_tallies(128, quiet),
                                    _tallies(256, quiet)) is False
    assert d12.route_terminal(_tallies(128, quiet), _tallies(256, quiet),
                              _paired_for(128, quiet),
                              _paired_for(256, quiet)) == d12.T_RETAIN_L045


def test_d12_terminals_all_five():
    counts = _material_counts()
    t128 = _tallies(128, counts)
    t256 = _tallies(256, counts)
    p128 = _paired_for(128, counts)
    p256 = _paired_for(256, counts)
    assert d12.route_terminal(t128, t256, p128, p256) == d12.T_SELECT_L050
    only55 = _counts((1,) * 6, (0,) * 6, (4, 4, 3, 3, 2, 2))
    assert d12.route_terminal(_tallies(128, only55), _tallies(256, only55),
                              _paired_for(128, only55),
                              _paired_for(256, only55)) == d12.T_SELECT_L055
    assert d12.route_terminal(t128, t256, p128, p256,
                              "RSS budget exceeded") == \
        d12.T_ENGINEERING_BLOCKED
    with pytest.raises(TypeError):
        d12.route_terminal({"pool": 1}, t256, p128, p256)


# --------------------------------------------------------------------------- #
# D1203: exact/syndrome/undetected isolation + predecessor non-pooling
# --------------------------------------------------------------------------- #
def test_d12_syndrome_never_substitutes_for_exact():
    counts = _counts((1,) * 6, (2,) * 6, (0,) * 6)
    records = _full_tagged_records(counts)
    for record in records:
        record["syndrome_ok"] = True
    tallies = d12.tallies_from_d12_records(records, 128)
    assert tallies.pool("L050") == 12
    assert d12.is_stable(tallies, "L050") is False


def test_d12_predecessor_records_cannot_enter_gate():
    r3_like = [{"width": 128, "arm": "L045",
                "graph_seed": 2026092401, "block_seed": 2026092601,
                "batch_id": r3.R3_BATCH_ID,
                "exact": True, "syndrome_ok": True}] * 216
    with pytest.raises(ValueError):
        d12.tallies_from_d12_records(r3_like, 128)
    no_tag = [_tagged(128, "L045", 2026093001, seed, True)
              for seed in d12.BLOCK_SEEDS[128]]
    for record in no_tag:
        del record["batch_id"]
    with pytest.raises(ValueError):
        d12.tallies_from_d12_records(no_tag * 18, 128)
    wrong_tag = [dict(rec, batch_id="d10-r3-fresh-v1") for rec in no_tag] * 18
    with pytest.raises(ValueError):
        d12.tallies_from_d12_records(wrong_tag, 128)
    short = _full_tagged_records(_counts((12,) * 6, (0,) * 6, (0,) * 6))
    with pytest.raises(ValueError):
        d12.tallies_from_d12_records(short[:-1], 128)  # 215 != 216


def test_d12_mcnemar_descriptive_only():
    counts = _counts((0,) * 6, (12,) * 6, (0,) * 6)
    records = _full_tagged_records(counts)
    paired = d12.describe_paired(records, 128)
    assert paired["L050"]["challenger_only"] == 72
    assert paired["L050"]["reference_only"] == 0
    assert 0.0 <= paired["L050"]["mcnemar_one_sided_p"] <= 1.0
    assert paired["L050"]["descriptive_only"] is True
    pooled = d12.describe_paired(records * 1 + _full_tagged_records(
        counts, 256), None)
    assert pooled["L050"]["challenger_only"] == 144
    tallies = d12.tallies_from_d12_records(records, 128)
    assert d12.is_stable(tallies, "L050") is True  # gate needs no p-value


# --------------------------------------------------------------------------- #
# D1204/D1205: unauthorized refusal + admission block (fake decoders only)
# --------------------------------------------------------------------------- #
def test_d12_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    out = tmp_path / "must_not_exist"
    assert runner.main(["--d12-batch", "--out-root", str(out)]) == 2
    assert not out.exists()
    assert "comparison_bench.formal_ir.v35_algorithm_development" \
        not in sys.modules


def test_d12_nonadmitted_graph_blocks_width_with_zero_decoder_calls():
    cell = d12.degree_cell("L045", 128)
    blocked = {"arm": "L045", "width": 128,
               "graph_seed": 2026093001, "n": cell["n"], "m": cell["m"],
               "E": 0, "edges": [], "coefficients": [], "dense": None,
               "structure": None, "status": "construction_failed",
               "admitted": False, "failure_reason": "A3_single_component"}
    calls = []

    def fake_decode(*_args, **_kwargs):
        calls.append(1)
        return _Result(np.zeros(cell["n"]), True)

    graphs = {(arm, 128, seed): _fake_graph(arm, 128, seed)
              for arm in d12.ARMS for seed in d12.GRAPH_SEEDS[128]}
    graphs[("L045", 128, 2026093001)] = blocked
    blocks = {128: {seed: {"u1": np.zeros(cell["n"], dtype=np.int64),
                           "prior": np.full((cell["n"], 32), 1.0 / 32)}
                    for seed in d12.BLOCK_SEEDS[128]}}
    outcome = d12.execute_width(128, d12.build_call_plan(128), graphs,
                                blocks, fake_decode, _zero_syndrome)
    assert calls == []
    assert outcome["records"] == []
    assert outcome["decoder_calls"] == 0
    assert outcome["engineering_reason"]
    assert "without seed replacement" in outcome["engineering_reason"]
    assert not hasattr(d12, "REPLACEMENT_SEEDS")


# --------------------------------------------------------------------------- #
# D1206: never-overwrite writer + fail-closed verifier (fake batch, tmp only)
# --------------------------------------------------------------------------- #
def _run_fake_batch(tmp_path, name="root"):
    def fake_prior(_root=None):
        return (np.full(4, 0.25), np.full((32 * 32, 4), 1.0 / (32 * 32)),
                np.full((32, 4), 1.0 / 32))

    def fake_sample(_p_b, _p_f, n, seed):
        rng = np.random.default_rng(int(seed))
        return {"bob": rng.integers(0, 4, size=int(n)),
                "u1": np.zeros(int(n), dtype=np.int64)}

    out = tmp_path / name
    summary = runner.run_d12_batch(
        str(out), "ignored-model-f", _fake_decode, _zero_syndrome,
        build_graph_fn=_fake_graph, load_prior_fn=fake_prior,
        sample_fn=fake_sample)
    assert summary["terminal"] == "D12_SELECT_L050"
    assert summary["scientific_calls"] == 432
    assert summary["setup_calls"] == d12.SETUP_CALL_CEILING == 62
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is True
    return out


def test_d12_writer_never_overwrites(tmp_path):
    out = _run_fake_batch(tmp_path)
    with pytest.raises(FileExistsError):
        runner.run_d12_batch(
            str(out), "ignored-model-f", None, None,
            build_graph_fn=_fake_graph,
            load_prior_fn=lambda _r=None: (None, None, None))


def test_d12_verify_fail_closed_on_tampered_exact(tmp_path):
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


def test_d12_verify_fail_closed_on_engineering_blocked_width(tmp_path):
    out = _run_fake_batch(tmp_path, name="root_blocked")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][0]["engineering_reason"] = "decoder crash X"
    summary["width_results"][0]["stable"] = {arm: False for arm in d12.ARMS}
    summary["terminal"] = d12.T_ENGINEERING_BLOCKED
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False


def test_d12_verify_recomputes_gate_not_stored_label(tmp_path):
    # Stored pools zeroed while rows stay exact-rich must fail recomputation.
    out = _run_fake_batch(tmp_path, name="root_relabel")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][0]["exact"]["L050"] = [0] * 6
    summary["width_results"][0]["pools"]["L050"] = 0
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False


def test_d12_verify_fail_closed_on_exact_without_syndrome(tmp_path):
    import csv
    out = _run_fake_batch(tmp_path, name="root_isolation")
    path = out / "decoder_records.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    target = next(row for row in rows if row["exact"] == "True")
    target["syndrome_ok"] = "False"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False
