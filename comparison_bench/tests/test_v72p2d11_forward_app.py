"""D11 focused tests: cells/seeds, shared-L2 identity, ceiling, replay,
provenance refusal, metric isolation, gates/terminals, dispatch, refusal.

Fake/tiny only: the production decoder is never imported, no scientific
call is made and no root outside pytest tmp paths is created.
Entry-boundary tests inject fake decoders and count their calls. Real
36-graph admission is D1109 (no-decoder profile), not pytest.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d11_development.py"


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
import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5  # noqa: E402
import comparison_bench.formal_ir.v72p2d7_gf32_cross_layer_discriminator as d7e  # noqa: E402

runner = _load_module("v72p2d11_runner_test", RUNNER_PATH)

TINY_N = 8
TINY_M1 = 6
TINY_M2 = 5
TINY_B = 4


def _tiny_H(m, n=TINY_N, seed=1):
    rng = np.random.default_rng(seed)
    H = np.zeros((m, n), dtype=np.int64)
    for variable in range(n):
        H[variable % m, variable] = 1
    while int(np.count_nonzero(H)) < n + m:
        H[int(rng.integers(0, m)), int(rng.integers(0, n))] = 1
    return H


def _tiny_graph(width, seed, m, arm):
    H = _tiny_H(m, seed=seed)
    return {"arm": arm, "width": width, "graph_seed": seed,
            "n": TINY_N, "m": m, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H, "structure": None,
            "status": "ok", "admitted": True, "failure_reason": ""}


def _tiny_graphs(width=128):
    l1 = {(arm, width, seed): _tiny_graph(width, seed, TINY_M1, arm)
          for arm in (d11.CONTROL_ARM, d11.MIX_ARM)
          for seed in d11.L1_GRAPH_SEEDS[width]}
    l2 = {(width, seed): _tiny_graph(width, seed, TINY_M2, d11.SHARED_L2_ARM)
          for seed in d11.L2_GRAPH_SEEDS[width]}
    return l1, l2


def _tiny_priors():
    p1 = np.full((32, TINY_B), 1.0 / 32)
    p2 = np.full((32, TINY_B, 32), 1.0 / 32)
    return p1, p2


def _tiny_blocks(width=128, seed_off=0):
    blocks = {}
    for seed in d11.L1_BLOCK_SEEDS[width]:
        rng = np.random.default_rng(int(seed) + seed_off)
        blocks[int(seed)] = {
            "bob": rng.integers(0, TINY_B, size=TINY_N),
            "u1": np.zeros(TINY_N, dtype=np.int64),
            "u2": np.zeros(TINY_N, dtype=np.int64),
        }
    return blocks


def _exact_result(x_true):
    n = len(np.asarray(x_true).ravel())
    return SimpleNamespace(
        x_hat=np.asarray(x_true, dtype=np.int64).copy(),
        syndrome_ok=True, iterations=1,
        final_beliefs=np.zeros((n, 32)), belief_provenance="CHECK_UPDATED")


def _wrong_result(x_true):
    n = len(np.asarray(x_true).ravel())
    return SimpleNamespace(
        x_hat=(np.asarray(x_true, dtype=np.int64) + 1) % 32,
        syndrome_ok=False, iterations=2,
        final_beliefs=np.zeros((n, 32)), belief_provenance="CHECK_UPDATED")


class _Scripted:
    """Position-scripted fake: replays the frozen R3 L1 vectors exactly.

    Per width, CONTROL L1 is exact-quiet and MIX L1 hits the frozen
    ``REPLAY_MIX`` counts on the leading blocks; every L2/oracle call is
    exact. Keys counters by ``n`` so one instance serves both widths
    (tiny ``n=8`` graphs stand in for width 128).
    """

    def __init__(self):
        self.counts = {}
        self.calls = []

    def __call__(self, H, prior, syndrome, layer=None):
        H = np.asarray(H)
        n = H.shape[1]
        width = 128 if n != 256 else 256
        c = self.counts.get(n, 0)
        self.counts[n] = c + 1
        pos = c % 5
        cell = c // 5
        graph_pos, block_pos = cell // 12, cell % 12
        self.calls.append((width, pos, graph_pos, block_pos))
        x_true = np.zeros(n, dtype=np.int64)
        if pos == 0:  # CONTROL L1: quiet (replay CONTROL zeros)
            return _wrong_result(x_true)
        if pos == 2:  # MIX L1: frozen replay hits on leading blocks
            if block_pos < d11.REPLAY_MIX[width][graph_pos]:
                return _exact_result(x_true)
            return _wrong_result(x_true)
        return _exact_result(x_true)  # CONTROL/MIX L2 + ORACLE exact


# --------------------------------------------------------------------------- #
# D1104: unauthorized refusal first (must precede any v35 import below)
# --------------------------------------------------------------------------- #
def test_d11_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    out = tmp_path / "must_not_exist"
    assert runner.main(["--forward-batch", "--out-root", str(out)]) == 2
    assert not out.exists()
    assert "comparison_bench.formal_ir.v35_algorithm_development" \
        not in sys.modules


# --------------------------------------------------------------------------- #
# D1103/D1105: frozen L2 cells/seeds, no source auth, reuse-not-duplication
# --------------------------------------------------------------------------- #
def test_d11_frozen_l2_cells_with_closure():
    assert d11.l2_degree_cell(128) == {
        "n": 128, "m": 104, "var_counts": {3: 128},
        "check_counts": {3: 32, 4: 72}, "E": 384}
    assert d11.l2_degree_cell(256) == {
        "n": 256, "m": 208, "var_counts": {3: 256},
        "check_counts": {3: 64, 4: 144}, "E": 768}
    for width, cell in sorted(d11.L2_DEGREE_TABLE.items()):
        frozen = d11.l2_degree_cell(width)
        assert frozen["E"] == 3 * width  # all-variable-degree-3 sockets
        assert set(frozen["var_counts"]) == {3}  # L1 profile never applies
    with pytest.raises(KeyError):
        d11.l2_degree_cell(64)


def test_d11_frozen_seeds_exact_and_disjoint():
    assert d11.L2_GRAPH_SEEDS == {
        128: tuple(range(2026092801, 2026092807)),
        256: tuple(range(2026092901, 2026092907))}
    l2 = {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
    assert len(l2) == 12
    l1g = {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
    l1b = {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
    assert l2.isdisjoint(l1g) and l2.isdisjoint(l1b)
    r2seeds = {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds} \
        | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
    assert l2.isdisjoint(r2seeds)
    with pytest.raises(ValueError):
        d11.build_l2_graph(128, 2026092401)  # L1 seed refused pre-build


def test_d11_replay_vectors_verbatim():
    assert d11.REPLAY_MIX == {128: (4, 4, 2, 5, 3, 5),
                              256: (6, 3, 5, 5, 6, 4)}
    assert d11.check_l1_replay(128, (4, 4, 2, 5, 3, 5), (0,) * 6) == ""
    assert d11.check_l1_replay(256, (6, 3, 5, 5, 6, 4), (0,) * 6) == ""
    assert "mismatch" in d11.check_l1_replay(128, (4, 4, 2, 5, 3, 4),
                                             (0,) * 6)
    assert "mismatch" in d11.check_l1_replay(128, (4, 4, 2, 5, 3, 5),
                                             (0, 0, 0, 0, 0, 1))


def test_d11_no_source_auth_or_replacement_mechanism():
    assert not hasattr(d11, "BATCH_AUTHORIZED")
    assert not hasattr(d11, "REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.forward_batch is False
    assert args.execution_authorized is False


def test_d11_reuse_not_duplication():
    assert d11.transfer_prior_l1_to_l2 is d7e.transfer_prior_l1_to_l2
    assert d11.build_transfer_prior is d7e.build_transfer_prior
    assert d11.check_source_eligibility is d7e.check_source_eligibility
    assert d11.softmax_source_q is d7e.softmax_source_q
    assert d11.require_check_updated is d7e.require_check_updated
    assert d11.canonical_source_q is d5.canonical_source_q
    assert d11.app_fed_l2_prior is d5.app_fed_l2_prior
    assert d11.canonical_transfer_l2_prior is d5.canonical_transfer_l2_prior
    assert d11.oracle_l2_prior is d5.oracle_l2_prior
    assert d11.run_layered_block is d5._run_layered_block
    assert d11.require_check_updated_provenance is \
        d5._require_check_updated_provenance
    assert d11.bind_row_layered_decoders is d7e.bind_row_layered_decoders
    assert d11.dispatch_l1 is r2.dispatch_l1
    assert d11.build_l1_graph is r3.build_graph
    assert d11.refuse_out_root is r2.refuse_out_root
    assert d11.L1_GRAPH_SEEDS is r3.GRAPH_SEEDS
    assert d11.L1_BLOCK_SEEDS is r3.BLOCK_SEEDS
    assert d11.DECODER_MAX_ITER == 90 and d11.DAMPING_ALPHA == 1.0
    assert d11.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d11.check_updated_token() == "CHECK_UPDATED"


# --------------------------------------------------------------------------- #
# D1106: plan identities (360/width, conditional 720) and dispatch
# --------------------------------------------------------------------------- #
def test_d11_plan_360_per_width_conditional_720():
    n128 = d11.build_call_plan(128)
    assert len(n128) == 360 == d11.PER_WIDTH_CALLS
    assert [e["call_idx"] for e in n128] == list(range(360))
    assert n128[0] == {"call_idx": 0, "width": 128, "branch": "CONTROL",
                       "layer": "L1", "graph_seed": 2026092401,
                       "block_seed": 2026092601}
    assert n128[-1]["branch"] == "ORACLE" and n128[-1]["layer"] == "L2"
    assert n128[-1]["graph_seed"] == 2026092406
    assert n128[-1]["block_seed"] == 2026092612
    for graph_seed in d11.L1_GRAPH_SEEDS[128]:
        for block_seed in d11.L1_BLOCK_SEEDS[128]:
            cell = [e for e in n128 if e["graph_seed"] == graph_seed
                    and e["block_seed"] == block_seed]
            assert [(e["branch"], e["layer"]) for e in cell] == [
                ("CONTROL", "L1"), ("CONTROL", "L2"), ("MIX", "L1"),
                ("MIX", "L2"), ("ORACLE", "L2")]
    full = d11.build_full_plan()
    assert len(full) == 720 == d11.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in full] == list(range(720))
    assert {e["width"] for e in full[:360]} == {128}
    assert {e["width"] for e in full[360:]} == {256}
    with pytest.raises(KeyError):
        d11.build_call_plan(64)


def test_d11_conditional_dispatch_gate():
    assert d11.n256_permitted(d11.FORWARD_SIGNAL) is True
    assert d11.n256_permitted(d11.TRANSFER_BOTTLENECK) is False
    assert d11.n256_permitted(d11.L2_CODE_BOTTLENECK) is False
    assert d11.n256_permitted(d11.FORWARD_AMBIGUOUS) is False
    assert d11.n256_permitted(d11.ENGINEERING_BLOCKED) is False


# --------------------------------------------------------------------------- #
# D1107: shared-L2 identity (same graph object across CONTROL/MIX/ORACLE)
# --------------------------------------------------------------------------- #
def test_d11_shared_l2_identity_across_branches(monkeypatch):
    seen = []
    original = d5._run_layered_block

    def spy(decode_fn, h1, h2, p1, p2, block, oracle, **kwargs):
        seen.append((id(h1), id(h2), bool(oracle)))
        return original(decode_fn, h1, h2, p1, p2, block, oracle, **kwargs)

    monkeypatch.setattr(d5, "_run_layered_block", spy)
    graphs_l1, graphs_l2 = _tiny_graphs()
    fake = _Scripted()
    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                fake)
    assert outcome["classification"] == d11.FORWARD_SIGNAL
    assert len(seen) == 144  # 72 cells x 2 arm calls (oracle rides MIX)
    assert all(is_oracle for _, _, is_oracle in seen[1::2])  # MIX carries it
    assert not any(is_oracle for _, _, is_oracle in seen[::2])
    per_cell = [(seen[i][1], seen[i + 1][1]) for i in range(0, 144, 2)]
    assert all(a == b for a, b in per_cell)  # CONTROL/MIX share one L2
    assert len({h2 for _, h2 in per_cell}) == 6  # one per pair, not per arm
    per_cell_h1 = [(seen[i][0], seen[i + 1][0]) for i in range(0, 144, 2)]
    assert all(a != b for a, b in per_cell_h1)  # L1 arms stay distinct


def test_d11_call_ceiling_exact_360_and_accounting():
    graphs_l1, graphs_l2 = _tiny_graphs()
    fake = _Scripted()
    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                fake)
    assert outcome["decoder_calls"] == 360
    assert len(outcome["records"]) == 360
    assert outcome["mix_l1"] == [4, 4, 2, 5, 3, 5]
    assert outcome["ctrl_l1"] == [0] * 6
    assert outcome["oracle_exact"] == 72
    assert outcome["transfers_blocked"] == 0
    assert outcome["all_check_updated"] is True
    assert outcome["classification"] == d11.FORWARD_SIGNAL
    assert outcome["engineering_reason"] == ""


def test_d11_call_ceiling_breach_blocks(monkeypatch):
    graphs_l1, graphs_l2 = _tiny_graphs()
    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                _Scripted(), call_ceiling=10)
    assert outcome["decoder_calls"] == 10
    assert outcome["classification"] == d11.ENGINEERING_BLOCKED
    assert "ceiling" in outcome["engineering_reason"]


# --------------------------------------------------------------------------- #
# D1105/D1106: replay gate and provenance fail-close through execution
# --------------------------------------------------------------------------- #
def test_d11_replay_mismatch_blocks_before_grading():
    graphs_l1, graphs_l2 = _tiny_graphs()

    def all_exact(H, prior, syndrome, layer=None):
        return _exact_result(np.zeros(H.shape[1], dtype=np.int64))

    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                all_exact)
    assert outcome["decoder_calls"] == 360  # calls spent, grading refused
    assert outcome["classification"] == d11.ENGINEERING_BLOCKED
    assert "replay mismatch" in outcome["engineering_reason"]


def test_d11_provenance_refusal_blocks_with_no_l2_contact():
    graphs_l1, graphs_l2 = _tiny_graphs()
    l2_contacts = []
    n_holder = {}

    def prior_only(H, prior, syndrome, layer=None):
        H = np.asarray(H)
        n = H.shape[1]
        n_holder["n"] = n
        if H.shape[0] == TINY_M2:
            l2_contacts.append(1)
        return SimpleNamespace(
            x_hat=np.zeros(n, dtype=np.int64), syndrome_ok=True,
            iterations=1, final_beliefs=np.zeros((n, 32)),
            belief_provenance="PRIOR_ONLY")

    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                prior_only)
    assert l2_contacts == []  # blocked transfers never touch L2: no fallback
    assert outcome["decoder_calls"] == 144  # L1 calls only
    assert outcome["classification"] == d11.ENGINEERING_BLOCKED
    assert "fail-closed" in outcome["engineering_reason"]


def test_d11_admission_block_zero_calls():
    graphs_l1, graphs_l2 = _tiny_graphs()
    graphs_l2[(128, 2026092803)] = dict(
        graphs_l2[(128, 2026092803)], admitted=False,
        status="construction_failed", failure_reason="A3_single_component",
        dense=None)
    calls = []

    def fake_decode(*args, **kwargs):
        calls.append(1)
        raise AssertionError("must not be called")

    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                fake_decode)
    assert calls == []
    assert outcome["records"] == []
    assert outcome["classification"] == d11.ENGINEERING_BLOCKED
    assert "without seed replacement" in outcome["engineering_reason"]


def test_d11_decoder_crash_retained_never_retried():
    graphs_l1, graphs_l2 = _tiny_graphs()

    def crasher(H, prior, syndrome, layer=None):
        raise RuntimeError("boom")

    outcome = d11.execute_width(128, d11.build_call_plan(128), graphs_l1,
                                graphs_l2, _tiny_priors(), _tiny_blocks(),
                                crasher)
    assert outcome["classification"] == d11.ENGINEERING_BLOCKED
    assert "decoder crash" in outcome["engineering_reason"]


# --------------------------------------------------------------------------- #
# D1107: metric isolation + gate/terminal boundaries
# --------------------------------------------------------------------------- #
def _row(width, branch, layer, graph_seed, block_seed, exact,
         syndrome_ok=None, invoked=True, prov="CHECK_UPDATED"):
    if branch == d11.ORACLE:
        invoked_cell, prov_cell = "", "ORACLE"
    elif layer == "L1":
        invoked_cell, prov_cell = "", ""
    else:
        invoked_cell, prov_cell = (True, prov) if invoked \
            else (False, "BLOCKED:UnconditionedBeliefProvenanceError")
    return {"call_idx": 0, "width": width, "branch": branch, "layer": layer,
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": d11.D11_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome_ok is None else syndrome_ok,
            "transfer_invoked": invoked_cell, "transfer_provenance": prov_cell}


def _full_records(width, mix_l1, ctrl_l1, mix_l2_exact=True,
                  ctrl_l2_exact=True, oracle_exact=72, syndrome_ok=None):
    records = []
    oracle_left = [oracle_exact]
    for pos, graph_seed in enumerate(d11.L1_GRAPH_SEEDS[width]):
        for i, block_seed in enumerate(d11.L1_BLOCK_SEEDS[width]):
            m1 = i < mix_l1[pos]
            c1 = i < ctrl_l1[pos]
            records.append(_row(width, d11.CONTROL, "L1", graph_seed,
                                block_seed, c1, syndrome_ok))
            records.append(_row(width, d11.CONTROL, "L2", graph_seed,
                                block_seed, ctrl_l2_exact, syndrome_ok))
            records.append(_row(width, d11.MIX, "L1", graph_seed,
                                block_seed, m1, syndrome_ok))
            records.append(_row(width, d11.MIX, "L2", graph_seed,
                                block_seed, mix_l2_exact, syndrome_ok))
            take = oracle_left[0] > 0
            oracle_left[0] -= 1 if take else 0
            records.append(_row(width, d11.ORACLE, "L2", graph_seed,
                                block_seed, take, syndrome_ok))
    return records


def _tallies(width=128, mix_joint=(2, 2, 2, 1, 1, 1),
             ctrl_joint=(0,) * 6, oracle=18, mix_l1=(2, 2, 2, 1, 1, 1),
             ctrl_l1=(0,) * 6, blocked=0, updated=True):
    return d11.D11WidthTallies(width, mix_joint, ctrl_joint, oracle, mix_l1,
                               ctrl_l1, blocked, updated)


def test_d11_syndrome_never_substitutes_for_exact():
    records = _full_records(128, (0,) * 6, (0,) * 6, oracle_exact=0,
                            syndrome_ok=True)
    tallies = d11.tallies_from_d11_records(records, 128)
    assert tallies.joint_mix == 0 and tallies.joint_ctrl == 0
    assert tallies.mix_l1_pool == 0
    assert tallies.oracle_exact == 0
    assert d11.classify_d11(tallies) == d11.L2_CODE_BOTTLENECK


def test_d11_joint_is_l1_and_l2():
    records = _full_records(128, (12,) * 6, (0,) * 6, mix_l2_exact=False,
                            oracle_exact=72)
    tallies = d11.tallies_from_d11_records(records, 128)
    assert list(tallies.mix_l1) == [12] * 6  # L1 source exact held
    assert list(tallies.mix_joint) == [0] * 6  # joint needs L2 too
    assert tallies.oracle_exact == 72


def test_d11_exact_without_syndrome_rejected():
    records = _full_records(128, (1,) * 6, (0,) * 6)
    target = next(r for r in records
                  if r["branch"] == d11.MIX and r["layer"] == "L1"
                  and r["exact"])
    target["syndrome_ok"] = False
    with pytest.raises(ValueError):
        d11.tallies_from_d11_records(records, 128)


def test_d11_records_gate_boundaries():
    with pytest.raises(ValueError):
        d11.tallies_from_d11_records(
            [{**_row(128, d11.MIX, "L1", 2026092401, 2026092601, True),
              "batch_id": "d10-r3-fresh-v1"}], 128)
    records = _full_records(128, (1,) * 6, (0,) * 6)
    with pytest.raises(ValueError):
        d11.tallies_from_d11_records(records[:-1], 128)  # 359 != 360
    with pytest.raises(TypeError):
        d11.classify_d11({"joint": 1})


def test_d11_signal_all_clauses():
    assert d11.classify_d11(_tallies()) == d11.FORWARD_SIGNAL


@pytest.mark.parametrize("mix_joint,ctrl_joint,oracle,mix_l1,updated", [
    ((2, 2, 1, 1, 1, 1), (0,) * 6, 18, (2, 2, 1, 1, 1, 1), True),  # JM=8
    ((2, 2, 2, 1, 1, 0), (0,) * 6, 18, (2, 2, 2, 1, 1, 0), True),  # margin 5
    ((6, 6, 6, 0, 0, 0), (0,) * 6, 18, (6, 6, 6, 0, 0, 0), True),  # 3 wins
    ((9, 0, 0, 0, 0, 0), (0,) * 6, 18, (9, 0, 0, 0, 0, 0), True),  # 1 graph
    ((3, 3, 2, 2, 2, 1), (1, 1, 1, 1, 0, 0), 18,  # JC=4
     (3, 3, 2, 2, 2, 1), True),
    ((2, 2, 2, 1, 1, 1), (0,) * 6, 17, (2, 2, 2, 1, 1, 1), True),  # O=17
    ((2, 2, 2, 1, 1, 1), (0,) * 6, 18, (2, 2, 2, 1, 1, 1), False),  # prov
])
def test_d11_signal_clause_boundaries_fall_through(mix_joint, ctrl_joint,
                                                  oracle, mix_l1, updated):
    tallies = _tallies(mix_joint=mix_joint, ctrl_joint=ctrl_joint,
                       oracle=oracle, mix_l1=mix_l1, updated=updated)
    assert d11.classify_d11(tallies) == d11.FORWARD_AMBIGUOUS


def test_d11_transfer_l2_and_ambiguous():
    transfer = _tallies(mix_joint=(0, 0, 0, 0, 0, 1), ctrl_joint=(0,) * 6,
                        oracle=18, mix_l1=(3,) * 6)
    assert d11.classify_d11(transfer) == d11.TRANSFER_BOTTLENECK
    l2 = _tallies(oracle=6)
    assert d11.classify_d11(l2) == d11.L2_CODE_BOTTLENECK
    # L2-code outranks an otherwise satisfied signal (frozen priority).
    assert d11.classify_d11(_tallies(oracle=6)) == d11.L2_CODE_BOTTLENECK
    mid = _tallies(mix_joint=(1, 1, 1, 1, 1, 0), ctrl_joint=(0,) * 6,
                   oracle=12, mix_l1=(2, 2, 2, 2, 2, 0))
    assert d11.classify_d11(mid) == d11.FORWARD_AMBIGUOUS
    assert d11.classify_d11(_tallies(), "decoder crash X") == \
        d11.ENGINEERING_BLOCKED
    assert d11.classify_d11(_tallies(blocked=1)) == d11.ENGINEERING_BLOCKED
    # Engineering block outranks the L2-code bottleneck (frozen priority).
    assert d11.classify_d11(_tallies(oracle=0), "admission failed") == \
        d11.ENGINEERING_BLOCKED


def test_d11_terminals_all_eight():
    assert d11.route_terminal(d11.FORWARD_SIGNAL, d11.FORWARD_SIGNAL) == \
        "D11_FORWARD_APP_WIDE_RECOVERY"
    assert d11.route_terminal(d11.FORWARD_SIGNAL,
                              d11.TRANSFER_BOTTLENECK) == \
        "D11_N256_TRANSFER_BOTTLENECK"
    assert d11.route_terminal(d11.FORWARD_SIGNAL,
                              d11.L2_CODE_BOTTLENECK) == \
        "D11_N256_L2_CODE_BOTTLENECK"
    assert d11.route_terminal(d11.FORWARD_SIGNAL,
                              d11.FORWARD_AMBIGUOUS) == \
        "D11_N256_FORWARD_AMBIGUOUS"
    assert d11.route_terminal(d11.TRANSFER_BOTTLENECK) == \
        "D11_N128_TRANSFER_BOTTLENECK"
    assert d11.route_terminal(d11.L2_CODE_BOTTLENECK) == \
        "D11_N128_L2_CODE_BOTTLENECK"
    assert d11.route_terminal(d11.FORWARD_AMBIGUOUS) == \
        "D11_N128_FORWARD_AMBIGUOUS"
    assert d11.route_terminal(d11.ENGINEERING_BLOCKED) == \
        "D11_ENGINEERING_BLOCKED"
    assert d11.route_terminal(d11.FORWARD_SIGNAL) == "D11_ENGINEERING_BLOCKED"


# --------------------------------------------------------------------------- #
# D1106: never-overwrite writer + fail-closed verifier
# --------------------------------------------------------------------------- #


def _fake_graph_fn(arm, width, seed):
    cell = {"n": int(width), "m": 6}
    H = np.zeros((cell["m"], cell["n"]), dtype=np.int64)
    for variable in range(cell["n"]):
        H[variable % cell["m"], variable] = 1
    return {"arm": arm, "width": int(width), "graph_seed": int(seed),
            "n": cell["n"], "m": cell["m"], "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H, "structure": None,
            "status": "ok", "admitted": True, "failure_reason": ""}


def _fake_l2_fn(width, seed):
    return _fake_graph_fn(d11.SHARED_L2_ARM, width, seed)


def _fake_prior(_root=None):
    p_b = np.full(4, 0.25)
    p_f = np.full((1024, 4), 1.0 / 1024)
    p1 = np.full((32, 4), 1.0 / 32)
    return p_b, p_f, p1


def _fake_sample(_p_b, _p_f, n, seed):
    rng = np.random.default_rng(int(seed))
    return {"bob": rng.integers(0, 4, size=int(n)),
            "u1": np.zeros(int(n), dtype=np.int64),
            "u2": np.zeros(int(n), dtype=np.int64)}


def _run_fake_batch(tmp_path, name="root"):
    out = tmp_path / name
    summary = runner.run_forward_batch(
        str(out), "ignored-model-f", _Scripted(),
        build_l1_fn=_fake_graph_fn, build_l2_fn=_fake_l2_fn,
        load_prior_fn=_fake_prior, sample_fn=_fake_sample)
    assert summary["terminal"] == "D11_FORWARD_APP_WIDE_RECOVERY"
    assert summary["scientific_calls"] == 720
    assert summary["setup_calls"] == d11.SETUP_UNITS <= d11.SETUP_CALL_CEILING
    assert runner.verify_root(str(out), build_l1_fn=_fake_graph_fn,
                               build_l2_fn=_fake_l2_fn) is True
    return out


def test_d11_writer_never_overwrites(tmp_path):
    out = _run_fake_batch(tmp_path)
    with pytest.raises(FileExistsError):
        runner.run_forward_batch(
            str(out), "ignored-model-f", None,
            build_l1_fn=_fake_graph_fn, build_l2_fn=_fake_l2_fn,
            load_prior_fn=_fake_prior, sample_fn=_fake_sample)


def test_d11_engineering_blocked_batch_fails_verify(tmp_path):
    def wrong(H, prior, syndrome, layer=None):
        n = np.asarray(H).shape[1]
        return _wrong_result(np.zeros(n, dtype=np.int64))

    out = tmp_path / "blocked"
    summary = runner.run_forward_batch(
        str(out), "ignored-model-f", wrong,
        build_l1_fn=_fake_graph_fn, build_l2_fn=_fake_l2_fn,
        load_prior_fn=_fake_prior, sample_fn=_fake_sample)
    assert summary["terminal"] == "D11_ENGINEERING_BLOCKED"
    assert runner.verify_root(str(out), build_l1_fn=_fake_graph_fn,
                               build_l2_fn=_fake_l2_fn) is False


def test_d11_verify_fail_closed_on_tampered_exact(tmp_path):
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
    assert runner.verify_root(str(out), build_l1_fn=_fake_graph_fn,
                               build_l2_fn=_fake_l2_fn) is False


def test_d11_verify_recomputes_gate_not_stored_label(tmp_path):
    out = _run_fake_batch(tmp_path, name="root_relabel")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][0]["mix_joint"] = [0] * 6
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_l1_fn=_fake_graph_fn,
                               build_l2_fn=_fake_l2_fn) is False
