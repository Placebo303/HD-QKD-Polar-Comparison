"""Stage-2 batch runner tests (fake-only, T0/T1).

No production decoder import, no scientific execution, no production-root
write. Every decoder below is an explicitly injected fake; the full-shape
``6 x 2 x 8`` rehearsal runs in-process with tiny matrices into ``tmp_path``.
The CLI ``--execute`` path is never invoked here.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.cli.nbldpc_l1d2_synth_batch as batch  # noqa: E402
import comparison_bench.cli.nbldpc_l1_degree2_driver as driver  # noqa: E402
import comparison_bench.formal_ir.nbldpc_l1_degree2_layout as layout  # noqa: E402
import comparison_bench.formal_ir.nonbinary_v10_common as common  # noqa: E402

_TINY_H = np.array([[1, 2, 0],
                    [0, 3, 1]], dtype=np.int64)

GRAPH6 = [2026093701, 2026093702, 2026093703,
          2026093704, 2026093705, 2026093706]
DATA2 = [2026093201, 2026093202]


class _FakeResult:
    def __init__(self, x_hat, syndrome_ok, beliefs, provenance):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = 1
        self.status = "fake_converged"
        self.final_beliefs = beliefs
        self.belief_provenance = provenance


def _exact_fake(h, prior, syndrome, layer=None):
    x_hat = np.argmax(np.asarray(prior, dtype=np.float64), axis=1)
    logp = np.log(np.asarray(prior, dtype=np.float64) + 1e-300)
    return _FakeResult(x_hat, True, logp, "CHECK_UPDATED")


def _nullspace_vector(h):
    h = np.asarray(h, dtype=np.int64)
    n = h.shape[1]
    rng = np.random.default_rng(11)
    for _ in range(2000):
        z = rng.integers(0, 32, size=n)
        if np.any(z) and layout.gf32_syndrome(h, z) == [0] * h.shape[0]:
            return z
    raise AssertionError("tiny nullspace vector not found")


_Z = _nullspace_vector(_TINY_H)


def _wrong_fake(h, prior, syndrome, layer=None):
    # Same-syndrome wrong word: exact False, syndrome True -> accepted_wrong.
    n = np.asarray(h).shape[1]
    truth = np.argmax(np.asarray(prior, dtype=np.float64), axis=1)
    x_hat = np.array([int(a) ^ int(b) for a, b in zip(truth, _Z[:n])],
                     dtype=np.int64)
    assert not np.array_equal(x_hat, truth)
    logp = np.log(np.asarray(prior, dtype=np.float64) + 1e-300)
    return _FakeResult(x_hat, True, logp, "CHECK_UPDATED")


def _blocked_fake(h, prior, syndrome, layer=None):
    x_hat = np.argmax(np.asarray(prior, dtype=np.float64), axis=1)
    logp = np.log(np.asarray(prior, dtype=np.float64) + 1e-300)
    return _FakeResult(x_hat, True, logp, "PRIOR_ONLY")


def _tiny_priors():
    p1 = np.full((32, 4), 1e-6)
    p1[5, 0] = p1[7, 1] = p1[9, 2] = 1.0
    p1 = p1 / p1.sum(axis=0, keepdims=True)
    # Peak at v == u for every (u, b): with q peaked at the L1 truth, the
    # APP-fed L2 prior peaks at that same truth symbol.
    p2 = np.full((32, 4, 32), 1e-6)
    for u in range(32):
        for b in range(4):
            p2[u, b, u] = 1.0
    p2 = p2 / p2.sum(axis=2, keepdims=True)
    return p1, p2


def _block_fn(entry):
    _ = entry  # stream-keyed in production; fixed aligned truth here
    return {"bob": np.array([0, 1, 2], dtype=np.int64),
            "u1": np.array([5, 7, 9], dtype=np.int64),
            "u2": np.array([5, 7, 9], dtype=np.int64)}


def _tiny_graphs(seeds):
    return ({s: _TINY_H.copy() for s in seeds},
            {s: _TINY_H.copy() for s in seeds},
            {s: _TINY_H.copy() for s in seeds})


def _args(**over):
    parser = batch.build_parser()
    argv = ["--width", "128",
            "--graph-seed", ",".join(str(s) for s in GRAPH6),
            "--data-seed", ",".join(str(s) for s in DATA2),
            "--frames", "0-7",
            "--out-root", over.pop("out_root", "/tmp/nonexistent-l1d2-root")]
    for key, value in over.items():
        argv += ["--" + key.replace("_", "-"), str(value)]
    args = parser.parse_args(argv)
    args.graph_seeds = batch.parse_seed_list(args.graph_seed_raw)
    args.data_seeds = batch.parse_seed_list(args.data_seed_raw)
    args.frames = batch.parse_frames(args.frames)
    return args


# --------------------------------------------------------------------------- #
# flags / oracle / frozen constants / stream
# --------------------------------------------------------------------------- #
def test_flags_complete_and_no_oracle():
    names = {o for a in batch.build_parser()._actions for o in a.option_strings}
    for flag in ("--width", "--graph-seed", "--data-seed", "--frames",
                 "--model-f-root", "--out-root", "--max-iter", "--damping",
                 "--wall-cap-s", "--rss-cap-bytes", "--chain-wall-cap-s",
                 "--canary", "--dry-run", "--fake-decoder", "--execute"):
        assert flag in names, flag
    assert not any("oracle" in n for n in names)
    src = Path(batch.__file__).read_text()
    assert "--oracle" not in src


def test_oracle_hardcoded_both_arms():
    assert batch.ORACLE_HARDCODED is False
    assert driver.ORACLE_HARDCODED is False
    import inspect
    assert "oracle" not in inspect.signature(driver.run_pair).parameters


def test_frozen_seed_and_l2_constants():
    assert batch.GRAPH_SEEDS[128] == tuple(GRAPH6)
    assert batch.GRAPH_SEEDS[256] == tuple(range(2026093711, 2026093717))
    assert batch.DATA_SEEDS[128] == (2026093201, 2026093202)
    assert batch.DATA_SEEDS[256] == (2026093301, 2026093302)
    for g, l2 in ((2026093701, 2026092801), (2026093706, 2026092806)):
        assert batch.l2_seed_for(128, g) == l2
    for g, l2 in ((2026093711, 2026092901), (2026093716, 2026092906)):
        assert batch.l2_seed_for(256, g) == l2
    with pytest.raises(ValueError):
        batch.l2_seed_for(128, 2026093201)
    with pytest.raises(KeyError):
        batch.l2_seed_for(64, 2026093701)


def test_stream_naming_uses_v10_seed():
    assert batch.call_seed_for.__module__ == batch.__name__
    for width, block, frame in ((128, 2026093201, 0), (128, 2026093202, 7),
                                (256, 2026093301, 3)):
        assert batch.call_seed_for(width, block, frame) == common.v10_seed(
            "nbldpc-l1d2-s2c:%d:%d:%d" % (width, block, frame))
    assert len({batch.call_seed_for(128, 2026093201, f)
                for f in range(8)}) == 8


def test_scalar_parsers():
    assert batch.parse_seed_list(["1,2", "3"]) == [1, 2, 3]
    assert batch.parse_frames("0-7") == list(range(8))
    assert batch.parse_frames("0,1,2") == [0, 1, 2]
    assert batch.parse_frames("0-2,5") == [0, 1, 2, 5]
    assert batch.parse_bytes(7) == 7
    assert batch.parse_bytes("4GiB") == 4 * 1024 ** 3
    assert batch.parse_bytes("512MiB") == 512 * 1024 ** 2
    with pytest.raises(ValueError):
        batch.parse_frames("")
    with pytest.raises(ValueError):
        batch.parse_seed_list(["abc"])


# --------------------------------------------------------------------------- #
# four-state counting / accepted_wrong isolation / blocked transfer
# --------------------------------------------------------------------------- #
def test_four_state_and_wrong_isolation():
    disc = layout.disclosure_bits(2, 2)
    ok_rec = batch.arm_to_frame({"transfer_invoked": True,
                                 "app_l1_exact": True,
                                 "app_l2_exact": True,
                                 "app_l1_syndrome_ok": True,
                                 "app_l2_syndrome_ok": True,
                                 "iterations": 5},
                                m1=2, m2=2, wall_s=0.01, rss_b=8)
    assert ok_rec["status"] == "ok" and ok_rec["pair_exact"] is True
    assert layout.is_success(ok_rec) is True
    wrong_rec = batch.arm_to_frame({"transfer_invoked": True,
                                    "app_l1_exact": True,
                                    "app_l2_exact": False,
                                    "app_l1_syndrome_ok": True,
                                    "app_l2_syndrome_ok": True,
                                    "iterations": 5},
                                   m1=2, m2=2)
    assert wrong_rec["pair_exact"] is False
    assert wrong_rec["accepted_wrong"] is True
    assert layout.is_success(wrong_rec) is False
    assert wrong_rec["status"] == "ok"  # syndrome-agreeing, still isolated
    blocked_rec = batch.arm_to_frame({"transfer_invoked": False,
                                      "app_l1_exact": True,
                                      "app_l2_exact": False,
                                      "app_l1_syndrome_ok": True,
                                      "app_l2_syndrome_ok": False,
                                      "iterations": 2},
                                     m1=2, m2=2)
    assert blocked_rec["status"] == "nonconverged"
    assert layout.is_success(blocked_rec) is False
    abort_rec = batch.abort_frame(m1=2, m2=2, wall_s=9.0)
    assert abort_rec["status"] == "resource_abort"
    assert layout.is_success(abort_rec) is False
    assert (abort_rec["l1_syn_bits"], abort_rec["l2_syn_bits"]) == (10, 10)
    assert set(ok_rec) == set(layout.RESULT_SCHEMA_COLUMNS)
    _ = disc


def test_transfer_blocked_end_to_end_nonsuccess():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:1], DATA2[:1], [0, 1])
    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6[:1]),
                                 p1, p2, _block_fn, _blocked_fake)
    assert result["chains"] == 4  # 2 pairs x 2 arms
    for row in result["frame_rows"]:
        assert row["transfer_invoked"] is False
        assert row["status"] == "nonconverged"
        assert layout.is_success(row) is False
        assert row["l1_syn_bits"] == 10 and row["l2_syn_bits"] == 10
    assert sum(r["success"] for r in result["arm_rows"]) == 0


def test_wrong_fake_end_to_end_accepted_wrong_isolated(tmp_path):
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:1], DATA2[:1], [0])
    h1c, h1m, h2 = _tiny_graphs(GRAPH6[:1])

    def block_fn(entry):
        # Truth on the MAP peak, decoder returns same-syndrome wrong word.
        return {"bob": np.array([0, 1, 2], dtype=np.int64),
                "u1": np.array([5, 7, 9], dtype=np.int64),
                "u2": np.array([5, 7, 9], dtype=np.int64)}

    p1w = np.full((32, 4), 1e-6)
    for b, v in ((0, 5), (1, 7), (2, 9)):
        p1w[v, b] = 1.0
    p1w = p1w / p1w.sum(axis=0, keepdims=True)
    result = batch.execute_pairs(plan, h1c, h1m, h2, p1w, p2, block_fn,
                                 _wrong_fake)
    assert len(result["frame_rows"]) == 2
    for row in result["frame_rows"]:
        assert row["syn_joint"] is True
        assert row["pair_exact"] is False
        assert row["accepted_wrong"] is True
        assert layout.is_success(row) is False


# --------------------------------------------------------------------------- #
# budgets / canary
# --------------------------------------------------------------------------- #
def test_per_chain_wall_and_pair_total_are_separate():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:1], DATA2[:1], [0])
    clock = [0.0]
    decoder_calls = [0]
    chain_s = (70.0, 60.0)

    def timed_fake(h, prior, syndrome, layer=None):
        chain_index = decoder_calls[0] // 2
        clock[0] += chain_s[chain_index] / 2.0
        decoder_calls[0] += 1
        return _exact_fake(h, prior, syndrome, layer=layer)

    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6[:1]),
                                 p1, p2, _block_fn, timed_fake,
                                 chain_wall_cap_s=120.0,
                                 now=lambda: clock[0])
    assert len(result["frame_rows"]) == 2
    assert [r["wall_s"] for r in result["frame_rows"]] == list(chain_s)
    assert [r["status"] for r in result["frame_rows"]] == ["ok", "ok"]
    assert result["pair_timings"][0]["pair_wall_s"] == 130.0
    assert result["pair_timings"][0]["both_arms_attempted"] is True
    assert result["chains"] == 2 and result["decoder_calls"] == 4


def test_first_chain_over_cap_stops_before_unattempted_candidate():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:2], DATA2[:1], [0])
    clock = [0.0]
    decoder_calls = [0]

    def over_cap_fake(h, prior, syndrome, layer=None):
        clock[0] += 60.5
        decoder_calls[0] += 1
        return _exact_fake(h, prior, syndrome, layer=layer)

    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6),
                                 p1, p2, _block_fn, over_cap_fake,
                                 chain_wall_cap_s=120.0,
                                 now=lambda: clock[0])
    assert result["stop_reason"] == "single-chain wall budget exceeded"
    assert result["chains"] == 1 and result["decoder_calls"] == 2
    assert result["completed_pairs"] == 0 and result["planned_pairs"] == 2
    assert decoder_calls[0] == 2
    assert len(result["frame_rows"]) == 1
    row = result["frame_rows"][0]
    assert row["arm"] == "CONTROL"
    assert row["wall_s"] == 121.0
    assert row["status"] == "resource_abort"
    assert layout.is_success(row) is False
    assert (row["l1_syn_bits"], row["l2_syn_bits"]) == (10, 10)
    assert result["arm_rows"][0]["attempted"] == 1
    assert result["arm_rows"][1]["attempted"] == 0
    assert result["pair_timings"][0]["chains_attempted"] == 1
    assert result["pair_timings"][0]["both_arms_attempted"] is False


def test_second_chain_over_cap_retains_first_and_stops_later_pairs():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:2], DATA2[:1], [0])
    clock = [0.0]
    decoder_calls = [0]
    chain_s = (30.0, 121.0)

    def timed_fake(h, prior, syndrome, layer=None):
        chain_index = decoder_calls[0] // 2
        clock[0] += chain_s[chain_index] / 2.0
        decoder_calls[0] += 1
        return _exact_fake(h, prior, syndrome, layer=layer)

    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6[:2]),
                                 p1, p2, _block_fn, timed_fake,
                                 chain_wall_cap_s=120.0,
                                 now=lambda: clock[0])
    assert result["stop_reason"] == "single-chain wall budget exceeded"
    assert result["chains"] == 2 and result["decoder_calls"] == 4
    assert result["completed_pairs"] == 1 and result["planned_pairs"] == 2
    assert [r["arm"] for r in result["frame_rows"]] == [
        "CONTROL", "CANDIDATE"]
    assert [r["wall_s"] for r in result["frame_rows"]] == list(chain_s)
    assert [r["status"] for r in result["frame_rows"]] == [
        "ok", "resource_abort"]
    assert result["pair_timings"][0]["chains_attempted"] == 2
    assert result["pair_timings"][0]["both_arms_attempted"] is True


def test_global_wall_cap_stops_with_retained_results():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6, DATA2, list(range(8)))
    clock = [0.0]

    def advancing_fake(h, prior, syndrome, layer=None):
        clock[0] += 50.0
        return _exact_fake(h, prior, syndrome, layer=layer)

    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6),
                                 p1, p2, _block_fn, advancing_fake,
                                 wall_cap_s=7200.0,
                                 now=lambda: clock[0],
                                 rss_fn=lambda: 0)
    assert result["stop_reason"] == "wall budget exceeded"
    assert result["completed_pairs"] < result["planned_pairs"]
    assert result["completed_pairs"] == 36  # 72 chains retained as pairs
    assert result["chains"] == 72  # no chain starts at the 7200 s boundary
    assert result["frame_rows"][-1]["arm"] == "CANDIDATE"
    assert result["frame_rows"][-1]["status"] == "ok"
    assert result["frame_rows"][-1]["wall_s"] == 100.0
    assert result["pair_timings"][-1]["both_arms_attempted"] is True


def test_rss_cap_stops_before_any_chain():
    p1, p2 = _tiny_priors()
    plan = batch.build_plan(128, GRAPH6[:1], DATA2[:1], [0])
    result = batch.execute_pairs(plan, *_tiny_graphs(GRAPH6[:1]),
                                 p1, p2, _block_fn, _exact_fake,
                                 rss_fn=lambda: 8 * 1024 ** 3)
    assert result["stop_reason"] == "RSS budget exceeded"
    assert result["chains"] == 0 and result["frame_rows"] == []


def test_canary_restricts_to_first_pair_block():
    plan = batch.build_plan(128, GRAPH6, DATA2, list(range(8)), canary=True)
    assert len(plan) == 8
    assert {p["graph_seed"] for p in plan} == {GRAPH6[0]}
    assert {p["block_seed"] for p in plan} == {DATA2[0]}
    full = batch.build_plan(128, GRAPH6, DATA2, list(range(8)))
    assert len(full) == 96


def test_canary_shuffled_seeds_still_selects_minimum():
    # Input order must not move the frozen canary definition.
    rev_graphs = [2026093705, 2026093701]
    rev_datas = [2026093202, 2026093201]
    plan = batch.build_plan(128, rev_graphs, rev_datas, list(range(8)),
                            canary=True)
    assert len(plan) == 8
    assert {p["graph_seed"] for p in plan} == {2026093701}
    assert {p["block_seed"] for p in plan} == {2026093201}
    plan256 = batch.build_plan(
        256, [2026093716, 2026093711], [2026093302, 2026093301],
        list(range(8)), canary=True)
    assert len(plan256) == 8
    assert {p["graph_seed"] for p in plan256} == {2026093711}
    assert {p["block_seed"] for p in plan256} == {2026093301}


# --------------------------------------------------------------------------- #
# out-root protection
# --------------------------------------------------------------------------- #
def test_out_root_protection(tmp_path):
    existing = tmp_path / "taken"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        batch.refuse_out_root(existing)
    with pytest.raises(ValueError):
        batch.refuse_out_root(ROOT / "results" / "x-fresh-uuid-dir")
    with pytest.raises(ValueError):
        batch.refuse_out_root(
            ROOT / "comparison_bench" / "outputs_comparison" / "x-fresh-uuid")
    fake_repo = tmp_path / "repo"
    ws_old = fake_repo / "workspace" / "existing-run"
    ws_old.mkdir(parents=True)
    with pytest.raises(ValueError):
        batch.refuse_out_root(fake_repo / "workspace" / "existing-run" / "sub",
                              repo_root=fake_repo)
    fresh = batch.refuse_out_root(fake_repo / "workspace" / "new-uuid",
                                  repo_root=fake_repo)
    assert fresh == (fake_repo / "workspace" / "new-uuid").resolve()
    with pytest.raises(ValueError):
        batch.refuse_out_root(tmp_path / "out",
                              model_f_root=tmp_path / "out")


# --------------------------------------------------------------------------- #
# full 96x2 fake rehearsal + outputs + schema order + no outside writes
# --------------------------------------------------------------------------- #
def _snapshot_protected():
    snap = {}
    for sub in ("results", "comparison_bench/outputs_comparison"):
        anchor = ROOT / sub
        snap[sub] = sorted(str(p.relative_to(anchor)) for p in anchor.rglob("*")
                           if p.is_file()) if anchor.is_dir() else []
    return snap


def test_full_96x2_fake_rehearsal_and_outputs(tmp_path):
    before = _snapshot_protected()
    out = tmp_path / "l1d2-batch-uuid-0001"
    args = _args(out_root=str(out))
    p1, p2 = _tiny_priors()
    h1c, h1m, h2 = _tiny_graphs(GRAPH6)
    returned = batch.run(args, decode_fn=_exact_fake,
                         graphs=(h1c, h1m, h2), priors=(p1, p2),
                         block_fn=_block_fn, command="fake-command")
    result = returned["result"]
    assert result["planned_pairs"] == 96
    assert result["chains"] == 192  # 96 pairs x 2 arms
    assert len(result["frame_rows"]) == 192
    # Each arm chain runs at most 1xL1 + 1xL2: 192 chains x 2 = 384 calls.
    assert result["decoder_calls"] == 384
    assert result["stop_reason"] == ""
    # Aligned tiny truth + MAP exact fake: every chain succeeds exactly.
    assert sum(r["success"] for r in result["arm_rows"]) == 192
    assert sum(r["accepted_wrong"] for r in result["arm_rows"]) == 0
    for row in result["graph_rows"]:
        assert row["delta_g"] == (row["candidate_pair_exact"]
                                  - row["control_pair_exact"])
    written = sorted(p.name for p in out.iterdir())
    assert written == ["arm_summary.csv", "command_log.txt",
                       "frame_records.csv", "graph_records.csv",
                       "manifest.json"]
    with open(out / "frame_records.csv", newline="") as fh:
        header = next(csv.reader(fh))
    assert header == list(batch.FRAME_KEY_COLUMNS) + list(
        layout.RESULT_SCHEMA_COLUMNS)
    with open(out / "manifest.json") as fh:
        manifest = json.load(fh)
    assert manifest["oracle"] is False
    assert manifest["chains"] == 192 and manifest["decoder_calls"] == 384
    assert len(manifest["pair_timings"]) == 96
    assert all(row["both_arms_attempted"]
               for row in manifest["pair_timings"])
    assert manifest["command"] == "fake-command"
    assert manifest["git_head_provenance_only"]
    assert _snapshot_protected() == before  # no writes outside out-root
    with pytest.raises(FileExistsError):
        batch.run(_args(out_root=str(out)), decode_fn=_exact_fake,
                  graphs=(h1c, h1m, h2), priors=(p1, p2),
                  block_fn=_block_fn, command="fake-command")


def test_canary_run_writes_projection(tmp_path):
    out = tmp_path / "l1d2-canary-uuid-0002"
    args = _args(out_root=str(out))
    args.canary = True
    p1, p2 = _tiny_priors()
    h1c, h1m, h2 = _tiny_graphs(GRAPH6)
    returned = batch.run(args, decode_fn=_exact_fake,
                         graphs=(h1c, h1m, h2), priors=(p1, p2),
                         block_fn=_block_fn, command="fake-canary")
    assert returned["result"]["planned_pairs"] == 8
    assert returned["result"]["chains"] == 16
    with open(Path(returned["out_root"]) / "canary.json") as fh:
        rec = json.load(fh)
    assert rec["full_chains_projected"] == 192
    assert rec["projected_wall_s_linear"] >= 0.0


def test_construction_failed_graph_emits_no_frames(tmp_path):
    out = tmp_path / "l1d2-confail-uuid-0003"
    args = _args(out_root=str(out))
    p1, p2 = _tiny_priors()
    h1c, h1m, h2 = _tiny_graphs(GRAPH6)
    bad = GRAPH6[0]
    del h1c[bad]
    returned = batch.run(args, decode_fn=_exact_fake,
                         graphs=(h1c, h1m, h2), priors=(p1, p2),
                         block_fn=_block_fn, command="fake-confail")
    grows = {r["graph_seed"]: r for r in returned["result"]["graph_rows"]}
    assert grows[bad]["construction"] == "construction_failed"
    assert grows[bad]["attempted_pairs"] == 0
    assert not [r for r in returned["result"]["frame_rows"]
                if r["graph_seed"] == bad]
    assert returned["result"]["chains"] == (96 - 16) * 2


# --------------------------------------------------------------------------- #
# CLI plan refusal / dry-run create nothing
# --------------------------------------------------------------------------- #
def test_main_plan_refusal_and_dry_run(tmp_path):
    out = tmp_path / "l1d2-cli-uuid-0004"
    argv = ["--width", "128", "--graph-seed", ",".join(map(str, GRAPH6)),
            "--data-seed", ",".join(map(str, DATA2)), "--frames", "0-7",
            "--out-root", str(out)]
    assert batch.main(argv) == 2
    assert not out.exists()
    assert batch.main(argv + ["--dry-run"]) == 0
    assert not out.exists()
