"""N focused tests: frozen cells/seeds, plan, gates, dispatch, refusal (N202–N209).

Fake/tiny only: the production decoder is never imported, no scientific
call is made and no root outside pytest tmp paths is created. The single
real-builder test is ``test_n14_profile_only_18_graphs`` (PROFILE_ONLY,
no decoder, no root). Entry-boundary tests inject fake decoders and count
their calls (must stay zero on refusal/block).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d14_discriminator_development.py"


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
import comparison_bench.formal_ir.v72p2d14n_calibrated_discriminator as n14  # noqa: E402

runner = _load_module("v72p2d14_runner_test", RUNNER_PATH)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never Model-F content)
# --------------------------------------------------------------------------- #
def _fake_l1_graph(profile, seed):
    cell = n14.degree_cell(profile)
    H = np.zeros((cell["m"], cell["n"]), dtype=np.int64)
    for v in range(cell["n"]):
        H[v % cell["m"], v] = 1
    return {"arm": profile, "width": 128, "graph_seed": int(seed),
            "n": cell["n"], "m": cell["m"],
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _fake_l2_graph(seed):
    cell = n14.degree_cell("L2")
    H = np.zeros((cell["m"], cell["n"]), dtype=np.int64)
    for v in range(cell["n"]):
        H[v % cell["m"], v] = 1
    return {"arm": "L2", "width": 128, "graph_seed": int(seed),
            "n": cell["n"], "m": cell["m"],
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _fake_block(seed):
    n = 128
    return {"u1": np.zeros(n, dtype=np.int64),
            "u2": np.zeros(n, dtype=np.int64),
            "prior": np.full((n, 32), 1.0 / 32.0)}


class _Result:
    def __init__(self, x_hat, syndrome_ok, provenance="CHECK_UPDATED"):
        self.x_hat = np.asarray(x_hat)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = 1
        self.status = "converged_exact"
        self.belief_provenance = provenance


def _fake_decode_exact(H, prior, syn, max_iter=None, damping_alpha=None,
                       warm_beliefs=None, field=None):
    return _Result(np.zeros(H.shape[1], dtype=np.uint8), True)


def _zero_syndrome(H, x):
    return np.zeros(H.shape[0], dtype=np.uint8)


def _fake_prior(root):
    return (None, None, None)


def _fake_sample(p_b, p_f, p1, seed):
    return _fake_block(seed)


def _fake_transfer(belief, block):
    return block["prior"]


def _fake_oracle_prior(block):
    return block["prior"]


def _fake_app_sources(provenance="CHECK_UPDATED", source_exact=True):
    return {(pair, block): {"belief": np.zeros((128, 32)),
                            "provenance": provenance,
                            "source_exact": source_exact}
            for pair in range(1, 7) for block in n14.BLOCK_SEEDS}


def _tagged(arm, pair, block, exact, joint_exact=None, oracle=False,
            graded=True, syndrome=None):
    joint = exact if joint_exact is None else joint_exact
    return {"call_idx": 0, "arm": arm, "pair_idx": pair,
            "l1_graph_seed": 2026093400 + pair,
            "l2_graph_seed": 2026093500 + pair, "block_seed": block,
            "batch_id": n14.N14_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome is None else syndrome,
            "source_exact": exact if arm in ("L045", "L055") else
            (exact if arm == n14.L2_ARM else False),
            "target_exact": False if arm in ("L045", "L055") else exact,
            "joint_exact": joint if arm == n14.L2_ARM else False,
            "undetected": False, "oracle": oracle, "graded": graded}


def _full_tagged(l055_counts, oracle_pool=0, joint_counts=None,
                 l045_counts=None):
    records = []
    counts = {"L045": list(l045_counts or [0] * 6),
              "L055": list(l055_counts),
              n14.L2_ARM: list(joint_counts or [0] * 6)}
    for arm, per_pair in counts.items():
        for pair, total in zip(range(1, 7), per_pair):
            for i, block in enumerate(n14.BLOCK_SEEDS):
                records.append(_tagged(arm, pair, int(block), i < total))
    done = 0
    for pair in range(1, 7):
        for block in n14.BLOCK_SEEDS:
            records.append(_tagged(n14.ORACLE_ARM, pair, int(block),
                                   done < oracle_pool, oracle=True,
                                   graded=False))
            done += 1
    return records


def _tallies(l055, oracle=0, joint=None, l045=None):
    return n14.N14Tallies(l045 or [0] * 6, list(l055),
                          joint or [0] * 6, oracle)


# --------------------------------------------------------------------------- #
# N202/A1: amended cells, seeds, scope guards, no-auth mechanism
# --------------------------------------------------------------------------- #
def test_n14_amended_cells_exact():
    assert n14.degree_cell("L045") == {
        "n": 128, "m": 110, "var_counts": {2: 71, 3: 57},
        "check_counts": {2: 17, 3: 93}, "E": 313}
    assert n14.degree_cell("L055") == {
        "n": 128, "m": 110, "var_counts": {2: 83, 3: 45},
        "check_counts": {2: 29, 3: 81}, "E": 301}
    assert n14.degree_cell("L2") == {
        "n": 128, "m": 104, "var_counts": {3: 128},
        "check_counts": {3: 32, 4: 72}, "E": 384}
    for profile, cell in sorted(n14.DEGREE_TABLE.items()):
        frozen = n14.degree_cell(profile)
        assert sum(frozen["var_counts"].values()) == frozen["n"]
        assert sum(frozen["check_counts"].values()) == frozen["m"]
        assert frozen["E"] == sum(d * c for d, c in
                                  frozen["var_counts"].items())
        assert frozen["E"] == sum(d * c for d, c in
                                  frozen["check_counts"].items())
    with pytest.raises(KeyError):
        n14.degree_cell("L050")  # D12-only arm refused
    with pytest.raises(KeyError):
        n14.degree_cell("SHARED_DV3_L2")  # D11-only arm label refused


def test_n14_frozen_seeds_exact_and_disjoint():
    assert n14.L1_GRAPH_SEEDS == tuple(range(2026093401, 2026093407))
    assert n14.L2_GRAPH_SEEDS == tuple(range(2026093501, 2026093507))
    assert n14.BLOCK_SEEDS == tuple(range(2026093601, 2026093613))
    priors = ({s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds})
    assert set(n14.L1_GRAPH_SEEDS).isdisjoint(priors)
    assert set(n14.L2_GRAPH_SEEDS).isdisjoint(priors)
    assert set(n14.BLOCK_SEEDS).isdisjoint(priors)
    with pytest.raises(ValueError):
        n14.build_l1_graph("L045", 2026093001)  # D12 seed refused
    with pytest.raises(ValueError):
        n14.build_l1_graph("L045", 2026093601)  # block seed refused
    with pytest.raises(ValueError):
        n14.build_l1_graph("L045", 2026093501)  # L2 seed refused
    with pytest.raises(ValueError):
        n14.build_l2_graph(2026093401)  # L1 seed refused
    with pytest.raises(KeyError):
        n14.build_l1_graph("L050", 2026093401)  # D12 profile refused


def test_n14_no_source_auth_or_replacement_mechanism():
    assert not hasattr(n14, "BATCH_AUTHORIZED")
    assert not hasattr(n14, "REPLACEMENT_SEEDS")
    assert not hasattr(n14, "PROFILE_REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.n14_batch is False
    assert args.execution_authorized is False


def test_n14_reuse_not_duplication():
    assert n14.DECODER_MAX_ITER == 90 and n14.DAMPING_ALPHA == 1.0
    assert n14.Q == 32 and n14.POLY == 37
    assert n14.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert n14.RSS_BUDGET_BYTES == r2.RSS_BUDGET_BYTES
    assert n14.dispatch_l1 is r2.dispatch_l1
    assert n14.coefficient_seed is r2.coefficient_seed
    assert n14.refuse_out_root is r2.refuse_out_root
    assert n14.check_updated_token() == "CHECK_UPDATED"


def test_n14_shared_constructor_both_families_one_path(monkeypatch):
    calls = []
    real = r2.build_degree_sequence_peg

    def counting(n, m, var_counts, check_counts, seed, field=None):
        calls.append((n, m, int(seed)))
        return real(n, m, var_counts, check_counts, seed, field=field)

    monkeypatch.setattr(r2, "build_degree_sequence_peg", counting)
    n14.build_l1_graph("L045", 2026093401)
    n14.build_l1_graph("L055", 2026093401)
    n14.build_l2_graph(2026093501)
    assert calls
    assert all(seed in set(n14.L1_GRAPH_SEEDS) | set(n14.L2_GRAPH_SEEDS)
               for _, _, seed in calls)


# --------------------------------------------------------------------------- #
# N202: deterministic 288-record plan, shared paired identities, budgets
# --------------------------------------------------------------------------- #
def test_n14_plan_288_shared_identities():
    plan = n14.build_call_plan()
    assert len(plan) == 288 == n14.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in plan] == list(range(288))
    for arm in n14.ARMS:
        scoped = [e for e in plan if e["arm"] == arm]
        assert len(scoped) == 72
        assert sorted(e["pair_idx"] for e in scoped) == \
            [p for p in range(1, 7) for _ in range(12)]
        assert sorted(e["block_seed"] for e in scoped) == \
            [s for s in sorted(n14.BLOCK_SEEDS) for _ in range(6)]
    assert [e["l1_graph_seed"] for e in plan
            if e["arm"] == "L045"] == \
        [s for s in n14.L1_GRAPH_SEEDS for _ in range(12)] * 1
    # Every (pair, block) cell feeds all four arms with shared identities.
    for pair in range(1, 7):
        for block in n14.BLOCK_SEEDS:
            rows = [e for e in plan if e["pair_idx"] == pair
                    and e["block_seed"] == int(block)]
            assert sorted(e["arm"] for e in rows) == sorted(n14.ARMS)
            assert {e["l1_graph_seed"] for e in rows} == \
                {n14.L1_GRAPH_SEEDS[pair - 1]}
            assert {e["l2_graph_seed"] for e in rows} == \
                {n14.L2_GRAPH_SEEDS[pair - 1]}


def test_n14_budgets_frozen():
    assert n14.SCIENTIFIC_CALL_CEILING == 288
    assert n14.SETUP_CALL_CEILING == 32
    assert n14.SETUP_FIXED_UNITS == 2
    assert n14.WALL_BUDGET_S == 1800.0
    assert n14.PER_CALL_BUDGET_S == 120.0
    assert n14.FUTURE_ROOT == \
        "workspace/v72p2d14_discriminator/20260914_r1"
    assert n14.FROZEN_COMMAND == (
        ".venv/bin/python scripts/v72p2d14_discriminator_development.py "
        "--n14-batch --model-f-root "
        "workspace/v72p2d5_model_f_input/20260907_r1 "
        "--out-root workspace/v72p2d14_discriminator/20260914_r1")
    assert n14.N14_BATCH_ID == "d14-discriminator-v1"


# --------------------------------------------------------------------------- #
# N205: gate boundaries, six terminals, priority collisions
# --------------------------------------------------------------------------- #
def test_n14_gate_boundaries():
    assert n14.is_l1_adequate((3,) * 6)  # 18/72, 6/6 graphs >= 2
    assert n14.is_l1_adequate((8, 2, 2, 2, 2, 2))  # 18 pooled, 6/6 >= 2
    assert not n14.is_l1_adequate((3,) * 5 + (2,))  # 17 pooled fails
    assert not n14.is_l1_adequate((9, 9, 0, 0, 0, 0))  # 18 but 2/6 >= 2
    assert n14.is_l1_adequate((3,) * 6, "") and not n14.is_l1_adequate(
        (3,) * 6, "boom")
    assert n14.is_oracle_adequate(18) and not n14.is_oracle_adequate(17)
    assert n14.is_l2_joint_good(9) and not n14.is_l2_joint_good(8)
    with pytest.raises(ValueError):
        n14.is_l1_adequate((3,) * 5)  # six per-pair counts required
    with pytest.raises(ValueError):
        n14.N14Tallies((0,) * 6, (0,) * 6, (0,) * 6, 73)


def test_n14_terminals_all_six_and_priority():
    assert n14.TERMINALS == ("N_ROUTE_BLOCKED_ENGINEERING",
                             "N_ROUTE_L1_CONSTRUCTION",
                             "N_ROUTE_L2_DEGREE",
                             "N_TRANSFER_BOTTLENECK_RECORDED",
                             "N_ROUTE_SCALE_VALIDATION",
                             "N_ROUTE_AMBIGUOUS")
    full = _tallies((12,) * 6, oracle=72, joint=(12,) * 6)
    assert n14.route_terminal(full, "boom") == \
        n14.T_ENGINEERING_BLOCKED  # engineering first
    assert n14.route_terminal(_tallies((0,) * 6, oracle=72,
                                       joint=(12,) * 6)) == \
        n14.T_L1_CONSTRUCTION  # NOT L1 beats adequate joint+oracle
    assert n14.route_terminal(_tallies((3,) * 6)) == n14.T_L2_DEGREE
    assert n14.route_terminal(_tallies((3,) * 6, oracle=18)) == \
        n14.T_TRANSFER_BOTTLENECK
    assert n14.route_terminal(_tallies((3,) * 6, oracle=72,
                                       joint=(2, 2, 2, 1, 1, 1))) == \
        n14.T_SCALE_VALIDATION  # joint wins over oracle-only reading
    assert n14.route_terminal(_tallies((3,) * 6, joint=(2,) * 6)) == \
        n14.T_SCALE_VALIDATION
    with pytest.raises(TypeError):
        n14.route_terminal({"l055_exact": (3,) * 6})  # non-N evidence


def test_n14_l045_discordance_descriptive_only():
    cells = {(p, b): False for p in range(1, 7) for b in n14.BLOCK_SEEDS}
    l055 = dict(cells)
    for key in list(l055)[:20]:
        l055[key] = True
    paired = n14.describe_paired_l1(cells, l055)
    assert paired == {"challenger_only": 20, "reference_only": 0,
                      "concordant": 52, "trials": 20, "cells": 72,
                      "descriptive_only": True}
    # Gate ignores L045 entirely: same L055 pool, different discordance.
    l045_alt = {k: (i % 2 == 0) for i, k in enumerate(sorted(cells))}
    base = n14.route_terminal(_tallies((3,) * 6))
    assert base == n14.T_L2_DEGREE
    assert n14.describe_paired_l1(l045_alt, l055)["challenger_only"] == 10
    with pytest.raises(ValueError):
        n14.describe_paired_l1({}, l055)  # unpaired cells raise


def test_n14_syndrome_never_substitutes_for_exact():
    records = _full_tagged([0] * 6)
    for rec in records:
        rec["syndrome_ok"] = True  # all syndrome-valid, none exact
    tallies = n14.tallies_from_n14_records(records)
    assert tallies.pool("L055") == 0
    assert tallies.pool(n14.L2_ARM) == 0
    assert tallies.pool(n14.ORACLE_ARM) == 0


def test_n14_predecessor_records_cannot_enter_gate():
    records = _full_tagged((3,) * 6)
    records[0] = dict(records[0], batch_id=d12.D12_BATCH_ID)
    with pytest.raises(ValueError):
        n14.tallies_from_n14_records(records)
    with pytest.raises(ValueError):
        n14.tallies_from_n14_records([])


# --------------------------------------------------------------------------- #
# N204: sharing, provenance refusal, oracle exclusion (fake decoders)
# --------------------------------------------------------------------------- #
def test_n14_fake_dispatch_shares_identities_with_zero_real_calls():
    plan = n14.build_call_plan()
    graphs_l1 = {(p, s): _fake_l1_graph(p, s) for p in n14.L1_PROFILES
                 for s in n14.L1_GRAPH_SEEDS}
    graphs_l2 = {s: _fake_l2_graph(s) for s in n14.L2_GRAPH_SEEDS}
    blocks = {int(s): _fake_block(s) for s in n14.BLOCK_SEEDS}
    seen = []

    def counting_decode(H, prior, syn, **kw):
        seen.append(tuple(H.shape))
        return _fake_decode_exact(H, prior, syn, **kw)

    outcome = n14.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, counting_decode,
        _zero_syndrome, transfer_fn=_fake_transfer,
        oracle_prior_fn=_fake_oracle_prior,
        app_sources=_fake_app_sources())
    assert outcome["engineering_reason"] == ""
    assert outcome["decoder_calls"] == 288
    assert len(seen) == 288
    l1_shapes = [s for s in seen if s[0] == 110]
    l2_shapes = [s for s in seen if s[0] == 104]
    assert len(l1_shapes) == 144 and len(l2_shapes) == 144
    tallies = n14.tallies_from_n14_records(outcome["records"])
    assert tallies.pool("L055") == 72
    assert tallies.pool(n14.L2_ARM) == 72  # joint == source&target
    assert n14.route_terminal(tallies) == n14.T_SCALE_VALIDATION


def test_n14_provenance_refusal_blocks_with_no_l2_contact():
    l2_graph = _fake_l2_graph(2026093501)
    block = _fake_block(2026093601)
    entry = {"arm": n14.L2_ARM, "pair_idx": 1,
             "l1_graph_seed": 2026093401, "l2_graph_seed": 2026093501,
             "block_seed": 2026093601}
    calls = []

    def counting_decode(H, prior, syn, **kw):
        calls.append(1)
        return _fake_decode_exact(H, prior, syn, **kw)

    with pytest.raises(n14.ProvenanceRefused):
        n14.run_l2_app_cell(
            l2_graph, block, entry, belief=np.zeros((128, 32)),
            provenance="PRIOR_ONLY", source_exact=True,
            decode_fn=counting_decode, syndrome_fn=_zero_syndrome,
            transfer_fn=_fake_transfer, call_idx=0)
    assert calls == []
    # Plan level: L1 calls run, then the first APP cell refuses and blocks.
    plan = n14.build_call_plan()
    graphs_l1 = {(p, s): _fake_l1_graph(p, s) for p in n14.L1_PROFILES
                 for s in n14.L1_GRAPH_SEEDS}
    graphs_l2 = {s: _fake_l2_graph(s) for s in n14.L2_GRAPH_SEEDS}
    blocks = {int(s): _fake_block(s) for s in n14.BLOCK_SEEDS}
    l2_shapes = []

    def shape_decode(H, prior, syn, **kw):
        if H.shape[0] == 104:
            l2_shapes.append(1)
        return _fake_decode_exact(H, prior, syn, **kw)

    outcome = n14.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, shape_decode,
        _zero_syndrome, transfer_fn=_fake_transfer,
        oracle_prior_fn=_fake_oracle_prior,
        app_sources=_fake_app_sources(provenance="PRIOR_ONLY"))
    assert l2_shapes == []
    assert outcome["engineering_reason"].startswith("provenance refusal")
    assert outcome["records"][-1]["status"] == "provenance_refused"


def test_n14_oracle_ungraded_and_excluded():
    records = _full_tagged((3,) * 6, oracle_pool=72,
                           joint_counts=(2,) * 6)
    tallies = n14.tallies_from_n14_records(records)
    assert tallies.pool("L055") == 18
    assert tallies.pool(n14.ORACLE_ARM) == 72
    assert tallies.pool(n14.L2_ARM) == 12
    assert n14.route_terminal(tallies) == n14.T_SCALE_VALIDATION
    bad = _full_tagged((3,) * 6)
    bad[-1] = dict(bad[-1], graded=True)  # oracle must be ungraded
    with pytest.raises(ValueError):
        n14.tallies_from_n14_records(bad)


def test_n14_nonadmitted_graph_blocks_with_zero_decoder_calls():
    plan = n14.build_call_plan()
    graphs_l1 = {(p, s): _fake_l1_graph(p, s) for p in n14.L1_PROFILES
                 for s in n14.L1_GRAPH_SEEDS}
    graphs_l1[("L055", 2026093401)] = dict(
        _fake_l1_graph("L055", 2026093401), admitted=False, dense=None)
    graphs_l2 = {s: _fake_l2_graph(s) for s in n14.L2_GRAPH_SEEDS}
    blocks = {int(s): _fake_block(s) for s in n14.BLOCK_SEEDS}
    calls = []

    def counting_decode(H, prior, syn, **kw):
        calls.append(1)
        return _fake_decode_exact(H, prior, syn, **kw)

    outcome = n14.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, counting_decode,
        _zero_syndrome, transfer_fn=_fake_transfer,
        oracle_prior_fn=_fake_oracle_prior,
        app_sources=_fake_app_sources())
    assert calls == []
    assert outcome["decoder_calls"] == 0
    assert "not admitted" in outcome["engineering_reason"]
    assert n14.route_terminal(
        n14.N14Tallies((0,) * 6, (0,) * 6, (0,) * 6, 0),
        outcome["engineering_reason"]) == n14.T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# N206/N207/N208: refusal ordering, writer, verifier (fake runners)
# --------------------------------------------------------------------------- #
def _run_fake_batch(out_root):
    return runner.run_n14_batch(
        out_root, n14.MODEL_F_INPUT_ROOT, _fake_decode_exact,
        _zero_syndrome, build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph, load_prior_fn=_fake_prior,
        sample_fn=_fake_sample, transfer_fn=_fake_transfer,
        oracle_prior_fn=_fake_oracle_prior,
        app_sources=_fake_app_sources(), app_source_profile="L055")


def test_n14_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    target = tmp_path / "workspace" / "v72p2d14_discriminator" / "20260914_r1"
    rc = runner.main(["--n14-batch", "--out-root", str(target)])
    assert rc == 2
    assert not target.exists()


def test_n14_writer_never_overwrites(tmp_path):
    out = tmp_path / "n14root"
    summary = _run_fake_batch(str(out))
    assert summary["terminal"] == n14.T_SCALE_VALIDATION
    assert summary["setup_calls"] == 32
    assert summary["scientific_calls"] == 288
    assert sorted(p.name for p in out.iterdir()) == \
        sorted(n14.EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        _run_fake_batch(str(out))


def test_n14_verify_roundtrip_and_fail_closed(tmp_path):
    out = tmp_path / "n14root"
    _run_fake_batch(str(out))
    assert runner.verify_root(
        str(out), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is True
    # Tampered exact breaks pools/terminal recomputation.
    import csv as _csv
    rows = list((_csv.DictReader(
        open(out / "decoder_records.csv", encoding="utf-8"))))
    rows[0]["exact"] = "False" if rows[0]["exact"] == "True" else "True"
    with open(out / "decoder_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=list(
            runner.DECODER_RECORD_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(
        str(out), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False


def test_n14_verify_fail_closed_on_isolation_and_partial(tmp_path):
    out = tmp_path / "n14root"
    _run_fake_batch(str(out))
    import csv as _csv
    rows = list((_csv.DictReader(
        open(out / "decoder_records.csv", encoding="utf-8"))))
    rows[5]["syndrome_ok"] = "False"  # exact without syndrome_ok
    rows[6]["undetected"] = "True"  # undetected merged into exact
    with open(out / "decoder_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=list(
            runner.DECODER_RECORD_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(
        str(out), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False
    (out / "arm_summary.csv").unlink()  # partial root fails
    assert runner.verify_root(
        str(out), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False
    assert runner.verify_root(str(tmp_path / "absent")) is False


def test_n14_verify_fail_closed_on_engineering_blocked(tmp_path):
    out = tmp_path / "n14blocked"

    def bad_l1(profile, seed):
        graph = _fake_l1_graph(profile, seed)
        if profile == "L055" and int(seed) == 2026093401:
            graph = dict(graph, admitted=False, dense=None)
        return graph

    runner.run_n14_batch(
        str(out), n14.MODEL_F_INPUT_ROOT, _fake_decode_exact,
        _zero_syndrome, build_l1_fn=bad_l1, build_l2_fn=_fake_l2_graph,
        load_prior_fn=_fake_prior, sample_fn=_fake_sample,
        transfer_fn=_fake_transfer, oracle_prior_fn=_fake_oracle_prior,
        app_sources=_fake_app_sources(), app_source_profile="L055")
    assert runner.verify_root(
        str(out), build_l1_fn=bad_l1,
        build_l2_fn=_fake_l2_graph) is False


# --------------------------------------------------------------------------- #
# N209: PROFILE_ONLY — 18 real graphs, amended counts, 288 plan, zero calls
# --------------------------------------------------------------------------- #
def test_n14_profile_only_18_graphs():
    profile = runner.profile_only()
    assert profile["total_graphs"] == 18
    assert profile["admitted"] == 18
    assert profile["frozen_seed_failures"] == []
    assert profile["replacement_seeds_used"] == 0
    assert profile["plan_calls"] == 288
    assert profile["plan_per_arm"] == {arm: 72 for arm in n14.ARMS}
    assert profile["decoder_calls"] == 0
    assert profile["future_root_absent"] is True
    expected = {}
    for seed in n14.L1_GRAPH_SEEDS:
        expected[("L045:%d" % seed)] = ({2: 71, 3: 57}, {2: 17, 3: 93},
                                        313, 110)
        expected[("L055:%d" % seed)] = ({2: 83, 3: 45}, {2: 29, 3: 81},
                                        301, 110)
    for seed in n14.L2_GRAPH_SEEDS:
        expected[("L2:%d" % seed)] = ({3: 128}, {3: 32, 4: 72}, 384, 104)
    for key, counts in profile["degree_counts"].items():
        var = {int(k): int(v) for k, v in
               counts["variable_degree_histogram"].items()}
        check = {int(k): int(v) for k, v in
                 counts["check_degree_histogram"].items()}
        exp_var, exp_check, exp_e, exp_m = expected[key]
        assert var == exp_var, key
        assert check == exp_check, key
        assert counts["E"] == exp_e, key
        assert counts["m"] == exp_m, key
        assert counts["admitted"] is True, key
