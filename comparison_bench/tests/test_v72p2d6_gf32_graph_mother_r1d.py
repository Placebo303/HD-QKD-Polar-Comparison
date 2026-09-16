"""D6 R1d Option C focused tests (fake-only, task-owned basetemps, zero decoder)."""
import csv
import importlib.util
import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]

_B0 = "B0_D5_DV3_NATIVE"
_B1 = "B1_D5_DV3_COMMON_LABELS"
_T1 = "T1_PEG_DV3"
_NON_R1D = ["T2_CYCLE_GREEDY_DV3", "T3_SC_DV3_W4", "T4_SC_DV3_W8",
            "M1_ACCUMULATOR_FOREST_MAX", "M2_ACCUMULATOR_FOREST_HALF"]
_HIST = ROOT / "workspace" / "d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b"


def _load_d6m(name):
    spec = importlib.util.spec_from_file_location(
        name, str(ROOT / "comparison_bench" / "src" / "comparison_bench"
                  / "formal_ir" / "v72p2d6_gf32_graph_mother.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_dev(name):
    import importlib.util as _ilu
    import sys as _sys
    for _k in [k for k in list(_sys.modules)
               if k == "comparison_bench" or k.startswith("comparison_bench.")]:
        del _sys.modules[_k]
    _sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
    sp = ROOT / "scripts" / "v72p2d6_graph_mother_development.py"
    spec = _ilu.spec_from_file_location(name, str(sp))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_r1d_arm_set_exact():
    d6m = _load_d6m("d6m_r1d_arms")
    assert list(d6m.R1D_ARMS) == [_B0, _B1, _T1]
    assert d6m.R1D_NEW_ARM == _T1
    assert set(d6m.R1D_ARMS) <= set(d6m.ARMS)
    assert set(d6m.R1D_ARMS) & set(_NON_R1D) == set()
    assert list(d6m.R1D_SCALING_FALLBACKS) == [_T1]
    assert d6m.R1D_STRUCTURE_SCHEMA == "r1d-v2"
    assert len(d6m.R1D_VALID_SUBSET) == 22


def test_r1d_non_r1d_arms_cannot_dispatch():
    d6m = _load_d6m("d6m_r1d_nondispatch")
    for arm in _NON_R1D:
        with pytest.raises(ValueError, match="inadmissible"):
            d6m.assert_r1d_arm(arm)
        with pytest.raises(ValueError):
            d6m.assert_r1d_dispatchable(arm, 64, "L1", 59)
    # Eligible R1d cell passes the arm gate and the subset gate.
    d6m.assert_r1d_arm(_T1)
    H, _ = d6m.build_mother(_T1, 64, "L1")
    d6m.assert_r1d_dispatchable(_T1, 64, "L1", 59, np.asarray(H[:59, :]))


def test_r1d_fallback_t1_only_and_controls():
    dev = _load_dev("d6dev_r1d_fb")
    assert list(dev.R1D_SCALING_FALLBACKS) == [_T1]
    # Advancement pool = new T/M finalists only: B0/B1 can never advance even
    # with canary signal (main finalists line excludes non-T/M arms).
    selected = [_B0, _B1, _T1]
    finalists = [a for a in selected if a in dev.T_ARMS + dev.M_ARMS]
    assert finalists == [_T1]
    assert dev.R1D_NEW_ARM == _T1
    # Frozen selection over an R1d-only n64 summary keeps exactly {B0,B1,T1}.
    rec, ssum, _ = dev.build_structures(64, None, arms=list(dev.R1D_ARMS))
    assert {r["arm"] for r in rec} == {_B0, _B1, _T1}
    sel, elig = dev.select_decoder_arms(ssum)
    assert set(sel) == {_B0, _B1, _T1}
    assert all(elig[a] is True for a in (_B0, _B1, _T1))


def test_r1d_every_schedule_cell_eligible():
    # Every frozen schedule cell is validity+I1 eligible: live rebuild via the
    # frozen builders plus cross-check against the accepted A5 matrix CSV.
    d6m = _load_d6m("d6m_r1d_sched")
    dev = _load_dev("d6dev_r1d_sched")
    with open(str(ROOT / "docs" / "research_cycles"
                  / "V72P2D6-GF32-GRAPH-MOTHER"
                  / "D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv"),
              newline="", encoding="utf-8") as fh:
        mat = {(r["arm"], int(r["n"]), r["layer"], int(r["prefix_rows"])): r
               for r in csv.DictReader(fh)}
    assert len(mat) == 144
    assert len(dev.R1D_VALID_SUBSET) == 22
    built = {}
    for n in (64, 128, 256):
        for arm in (_B0, _B1, _T1):
            rec, _, mothers = dev.build_structures(int(n), None, arms=[arm])
            for r in rec:
                built[(r["arm"], int(r["n"]), r["layer"],
                       int(r["prefix_rows"]))] = (r, mothers)
    for key in sorted(dev.R1D_VALID_SUBSET):
        arm, n, layer, k = key
        mrow = mat.get(key)
        assert mrow is not None, key
        assert (mrow["frozen_eligible"], mrow["i1_pass"],
                mrow["new_eligible"]) == ("True", "True", "True"), key
        r, mothers = built[key]
        assert r["eligible"] is True or r["eligible"] == "True", key
        H = np.asarray(mothers[(arm, layer)])
        rmin, nbelow = d6m.check_I1_row_degree(H, int(k))
        assert int(rmin) >= 2 and int(nbelow) == 0, key


def test_r1d_invalid_cell_fails_before_decoder():
    # T1 n128-L1 f1.0 (k98) is structurally fine but outside the R1d dispatch
    # subset (scaling dispatches f1.2+square only): fail closed, zero calls.
    d6m = _load_d6m("d6m_r1d_invalid")
    dev = _load_dev("d6dev_r1d_invalid")
    H, _ = d6m.build_mother(_T1, 128, "L1")
    with pytest.raises(ValueError, match="outside validity subset"):
        d6m.assert_r1d_dispatchable(_T1, 128, "L1", 98, np.asarray(H[:98, :]))
    H2, _ = d6m.build_mother(_T1, 128, "L2")

    class _NoCall:
        pids = ["1"]

        def call(self, task, state=None):
            raise AssertionError("decoder must not be called on refusal")

    import threading
    import time as _time
    state = {"calls": 0, "setup_calls": 0, "t0": _time.perf_counter(),
             "deadline": float(_time.perf_counter()) + 3600,
             "records": [], "peak_rss": 0, "budget_stop": False,
             "chunk_wall_blocked": False, "lock": threading.Lock(),
             "r1d": True}
    blk = {"bob": np.zeros(128, dtype=np.int64),
           "u1": np.zeros(128, dtype=np.int64),
           "u2": np.zeros(128, dtype=np.int64)}
    p = np.full((128, 32), 1.0 / 32, dtype=np.float64)
    meta = {"arm": _T1, "n": 128, "seed": 2026091100, "point": "f1.0",
            "r1": 98, "r2": 86, "matrix_id": "m"}
    with pytest.raises(ValueError, match="outside validity subset"):
        dev.run_cell(_NoCall(), np.asarray(H), np.asarray(H2), 98, 86,
                     p, p, blk, 128, meta, state)
    assert state["calls"] == 0 and len(state["records"]) == 0


def test_r1d_schema_v2_present_and_recomputable(tmp_path):
    d6m = _load_d6m("d6m_r1d_schema")
    dev = _load_dev("d6dev_r1d_schema")
    rec, _, mothers = dev.build_structures(64, None, arms=list(dev.R1D_ARMS))
    enr = d6m.enrich_r1d_records(rec, mothers)
    assert len(enr) == len(rec) == 3 * 2 * 3
    # Frozen dicts never mutated by enrichment (old writer output unchanged).
    assert all("row_degree_min" not in r for r in rec)
    out = tmp_path / "structure_records.csv"
    d6m.write_structure_records_r1d(str(out), enr)
    with open(str(out), newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        fields = list(rd.fieldnames or [])
        rows = list(rd)
    assert ",".join(fields) + "\n" == d6m.R1D_STRUCTURE_HEADER
    assert "row_degree_min" in fields and "rows_below_degree_2" in fields
    assert len(rows) == len(enr)
    for r in rows:
        H = np.asarray(mothers[(r["arm"], r["layer"])])
        rmin, nbelow = d6m.check_I1_row_degree(H, int(r["prefix_rows"]))
        assert int(r["row_degree_min"]) == int(rmin)
        assert int(r["rows_below_degree_2"]) == int(nbelow)
    checked, mis = dev.verify_r1d_stored_i1_values(rows)
    assert checked == len(rows) and mis == []


def test_r1d_old_schema_readable_and_immutable(tmp_path):
    # Historical six-file header has no v2 columns; the R1d writer only ever
    # targets new paths; refused roots cover history + VOID roots.
    d6m = _load_d6m("d6m_r1d_old")
    hist = (_HIST / "structure_records.csv").read_text(
        encoding="utf-8").splitlines()[0]
    assert "row_degree_min" not in hist
    assert "rows_below_degree_2" not in hist
    for rel in d6m.R1D_REFUSED_ROOTS:
        assert "d6_graph_mother_r1c_" in rel
    with pytest.raises(ValueError, match="refusing historical root"):
        d6m.assert_r1d_out_root(str(_HIST), str(ROOT))
    fresh = tmp_path / "d6_graph_mother_r1d_fresh"
    d6m.assert_r1d_out_root(str(fresh), str(ROOT))  # no raise
    # Old-schema minimal root still verifies (marker absent -> old behavior).
    dev = _load_dev("d6dev_r1d_old")
    out = tmp_path / "oldroot"
    out.mkdir()
    sel = {"selected": [_B0], "eligible": {_B0: True},
           "fallback_T": None, "fallback_M": None,
           "structural_order_new": [],
           "freeze": "decoder-blind-from-structure-only"}
    (out / "selected_arms.json").write_text(json.dumps(sel), encoding="utf-8")
    (out / "structure_records.csv").write_text(
        "arm,n,layer,prefix_rows,rank,zero_rows,zero_columns,"
        "connected_components,largest_component_fraction,four_cycles,"
        "four_cycle_variable_incidence_max,duplicate_projective_columns,"
        "base_pair_duplicates,support_triple_duplicates,row_degree_max,"
        "row_degree_sumsq,girth,girth_reason,m_cycle_rank,window_overflow,"
        "eligible,determinism_ok\n", encoding="utf-8")
    (out / "command_log.txt").write_text("r1d-old-minimal\n", encoding="utf-8")
    mib = 1024 ** 2
    agg = int(50 * mib) + int(100 * mib)
    mani = {"out_root": str(out), "revision": dev.R1C_REVISION, "workers": 1,
            "workers_requested": 1, "workers_effective": 1,
            "main_rss_bytes": int(50 * mib),
            "worker_rss_bytes": [int(100 * mib)],
            "aggregate_rss_bytes": int(agg),
            "peak_single_rss_bytes": int(100 * mib),
            "peak_aggregate_rss_bytes": int(agg),
            "rss_semantics": dev.RSS_SEMANTICS, "deadline_s": 1e9,
            "rss_block_terminal": None, "chunk_wall_max_s": dev.R1C_CHUNK_WALL_MAX,
            "chunk_walls": {}, "chunk_wall_blocked": False,
            "canary_seeds": [2026091000], "confirmation_seeds": [2026091010],
            "scaling_seeds": [2026091100],
            "budgets": {"calls": 2500, "wall_s": 43200, "watchdog_s": 120,
                        "rss_bytes": 2147483648},
            "calls": 0, "setup_decoder_calls": 1, "scientific_calls": 0,
            "total_decoder_calls": 1, "wall_s": 10.0,
            "peak_rss_bytes": int(100 * mib), "worker_pids": [111],
            "head_sha": "test", "budget_stop": False,
            "oracle_never_upgrades_exact": True}
    (out / "manifest.json").write_text(json.dumps(mani), encoding="utf-8")
    summ = {"selected": [_B0], "canary": {}, "revision": dev.R1C_REVISION,
            "workers": 1, "workers_requested": 1, "workers_effective": 1,
            "setup_decoder_calls": 1, "scientific_calls": 0,
            "total_decoder_calls": 1, "chunk_walls": {},
            "chunk_wall_blocked": False, "rss_block_terminal": None,
            "peak_single_rss_bytes": int(100 * mib),
            "peak_aggregate_rss_bytes": int(agg),
            "rss_semantics": dev.RSS_SEMANTICS, "advancing": [],
            "confirmation_counts": {},
            "confirmation_safety": {"crashes": 0, "nonfinite": 0,
                                    "disagreements": 0, "rss_known_ok": True},
            "confirmation_width": 64,
            "terminal": "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY", "calls": 0,
            "wall_s": 10.0, "iterations_max": 0,
            "peak_rss_bytes": int(100 * mib), "budget_stop": False,
            "oracle_never_upgrades_exact": True}
    (out / "summary.json").write_text(json.dumps(summ), encoding="utf-8")
    with open(str(out / "decoder_records.csv"), "w", encoding="utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=dev.DECODER_FIELDNAMES)
        w.writeheader()
    assert dev.verify_command(str(out)) is True


def test_r1d_crash_nonfinite_override():
    # A3/A5 crash-precedence terminal governs R1d unchanged (shared rule).
    d6m = _load_d6m("d6m_r1d_term")
    assert d6m.execution_block_terminal([]) is None
    assert d6m.execution_block_terminal(
        [{"call_idx": -1, "crash": "True", "finite": "False",
          "error": "boom"}]) is None
    deg = [{"call_idx": 1, "arm": _T1, "n": 64, "crash": "True",
            "finite": "False",
            "error": "ValueError('Check node requires degree >= 2')"}]
    assert d6m.execution_block_terminal(deg) == \
        "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED"
    other = [{"call_idx": 1, "arm": _T1, "n": 64, "crash": "True",
              "finite": "True", "error": "boom"}]
    assert d6m.execution_block_terminal(other) == \
        "D6_GRAPH_ATTEMPTED_CELL_INVALID"
    assert d6m.execution_block_terminal(deg + other) == \
        "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED"
    # Stored-vs-recomputed agreement helper governs (recomputed wins).
    dev = _load_dev("d6dev_r1d_term")
    agree, gov = dev.a3_compare_terminals("X", "X")
    assert agree is True
    agree2, gov2 = dev.a3_compare_terminals(
        "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY",
        "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED")
    assert agree2 is False and gov2 == "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED"


def test_r1d_no_a2_void_formal_reuse():
    d6m = _load_d6m("d6m_r1d_noreuse")
    dev = _load_dev("d6dev_r1d_noreuse")
    # All four immutable roots refused by name as an R1d output root.
    assert len(d6m.R1D_REFUSED_ROOTS) == 4
    for rel in d6m.R1D_REFUSED_ROOTS:
        with pytest.raises(ValueError, match="refusing historical root"):
            d6m.assert_r1d_out_root(str(ROOT / rel), str(ROOT))
    # R1d entrypoint refuses the historical root before the exists-check.
    with pytest.raises(SystemExit) as ei:
        dev.main(["--r1d", "--model-f-root", "workspace/model_f_fake",
                  "--out-root", str(_HIST)])
    assert int(ei.value.code) == 2
    # Formal roots remain guarded independently of R1d.
    with pytest.raises(ValueError):
        d6m.assert_no_formal_write(
            str(ROOT / "workspace" / "v72p2d5_structure" / "20260905_r2"))


def test_r1d_seq_par_determinism():
    # Sequential and parallel R1d structure paths agree record-identically;
    # R1d arm restriction changes nothing about the shared builder math.
    # Real importable module name so pool workers can unpickle (spawn).
    import sys as _sys
    sp = str(ROOT / "scripts")
    if sp not in _sys.path:
        _sys.path.insert(0, sp)
    for _k in [k for k in list(_sys.modules)
               if k == "v72p2d6_graph_mother_development"]:
        del _sys.modules[_k]
    import v72p2d6_graph_mother_development as dev
    rec_s, _, mom_s = dev.build_structures(64, None,
                                           arms=list(dev.R1D_ARMS))
    rec_p, _, mom_p = dev.build_structures_parallel(
        64, None, max_workers=2, arms=list(dev.R1D_ARMS))
    assert len(rec_s) == len(rec_p) == 18
    ks = lambda r: (r["arm"], r["n"], r["layer"], r["prefix_rows"])
    ps = {ks(r): r for r in rec_s}
    pp = {ks(r): r for r in rec_p}
    assert set(ps) == set(pp)
    for k in ps:
        assert {x: str(v) for x, v in ps[k].items()} == \
               {x: str(v) for x, v in pp[k].items()}, k
        assert ps[k]["determinism_ok"] is True
    for a in dev.R1D_ARMS:
        for layer in ("L1", "L2"):
            assert np.array_equal(np.asarray(mom_s[(a, layer)]),
                                  np.asarray(mom_p[(a, layer)]))
    # Unchanged-output pin: R1d-restricted rows equal the default path rows.
    rec_full, _, _ = dev.build_structures(64, None)
    full = {ks(r): r for r in rec_full if r["arm"] in list(dev.R1D_ARMS)}
    assert set(full) == set(ps)
    for k in ps:
        assert {x: str(v) for x, v in full[k].items()} == \
               {x: str(v) for x, v in ps[k].items()}, k


def test_r1d_runner_wiring_source_pins():
    # No SC/M/T2 branch reachable from R1d config: every structure build in
    # the runner is arm-restricted, and the per-cell R1d guard is wired.
    src = (ROOT / "scripts" / "v72p2d6_graph_mother_development.py"
           ).read_text(encoding="utf-8")
    assert "--r1d" in src
    assert "64, logfh, arms=list(R1D_ARMS)" in src
    assert "64, logfh, max_workers=workers, arms=list(R1D_ARMS)" in src
    assert "list(fb) != list(R1D_SCALING_FALLBACKS)" in src
    assert 'if state.get("r1d"):' in src
    assert "assert_r1d_dispatchable(" in src
    assert "structure_schema" in src
    assert "R1D_STRUCTURE_SCHEMA" in src


def test_r1d_dry_structure_mode(tmp_path):
    # Distinct R1d entrypoint, exercised behaviorally: --r1d --dry-structure
    # builds only B0/B1/T1, freezes T1-only fallbacks, and writes schema-v2
    # structure evidence with zero decoder contact.
    dev = _load_dev("d6dev_r1d_dry")
    out = tmp_path / "d6_graph_mother_r1d_drytest"
    assert dev.main(["--r1d", "--model-f-root", str(tmp_path),
                     "--out-root", str(out), "--dry-structure",
                     "--workers", "1"]) is None
    with open(str(out / "structure_records.csv"), newline="",
              encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        assert ",".join(list(rd.fieldnames or [])) + "\n" == \
            dev.R1D_STRUCTURE_HEADER
        rows = list(rd)
    assert len(rows) == 18
    assert {r["arm"] for r in rows} == {_B0, _B1, _T1}
    assert all("row_degree_min" in r and "rows_below_degree_2" in r
               for r in rows)
    sel = json.loads((out / "selected_arms.json").read_text(encoding="utf-8"))
    assert set(sel["selected"]) == {_B0, _B1, _T1}
    assert sel["fallback_T"] == _T1 and sel["fallback_M"] is None


def test_r1d_residual_syndrome_weight_exposed(tmp_path, monkeypatch):
    # H22: R1d records expose the per-mode residual syndrome weight
    # (unsatisfied check rows vs the target syndrome) computed from the
    # decoder's own hard decision. Fake raw decoder; real _decode_block.
    dev = _load_dev("d6dev_r1d_resid")
    live = sys.modules.get(
        "comparison_bench.formal_ir.v72p2d5_gf32_rate_mother")
    assert live is not None

    def fake_raw(h, prior, syndrome, layer=None):
        hh = np.asarray(h)
        xh = (np.zeros(hh.shape[1], dtype=np.int64)
              if hh.shape == (8, 8) else np.array([1, 0], dtype=np.int64))
        return {"x_hat": xh, "syndrome_ok": False, "iterations": 7,
                "final_beliefs": np.log(np.full((xh.size, 32), 1.0 / 32)),
                "belief_provenance": "CHECK_UPDATED"}
    monkeypatch.setattr(live, "bind_historical_decoder", lambda: fake_raw)

    class _Conn:
        def __init__(self, tasks):
            self._tasks = list(tasks)
            self.sent = []

        def send(self, obj):
            self.sent.append(obj)

        def recv(self):
            return self._tasks.pop(0) if self._tasks else None

    h_task = np.ones((1, 2), dtype=np.uint8)
    task = {"h": h_task,
            "prior": np.full((2, 32), 1.0 / 32, dtype=np.float64),
            "x_true": np.zeros(2, dtype=np.int64),
            "return_beliefs": True}
    conn = _Conn([task, None])
    dev._worker_main(conn, str(ROOT / "comparison_bench" / "src"))
    hello, out = conn.sent
    assert hello["ready"] is True
    assert out["crash"] is False
    # target syndrome of zeros is 0; x_hat=[1,0] gives syndrome 1 -> 1 row.
    assert int(out["residual_syndrome_weight"]) == 1

    import threading
    import time as _time
    def _state(r1d):
        return {"calls": 0, "setup_calls": 0, "t0": _time.perf_counter(),
                "deadline": _time.perf_counter() + 60, "records": [],
                "peak_rss": 0, "budget_stop": False, "chunk_wall_blocked": False,
                "lock": threading.Lock(), "r1d": r1d}

    class _W:
        pids = ["1"]

        def call(self, task, state=None):
            return dict(out)

    meta = {"arm": _T1, "n": 64, "seed": 2026091000, "point": "f1.2",
            "r1": 59, "r2": 52, "matrix_id": "m"}
    st = _state(True)
    rec = dev.invoke(_W(), st, meta, "L1", h_task,
                     np.full((2, 32), 1.0 / 32, dtype=np.float64),
                     np.zeros(2, dtype=np.int64), 0.5, False)
    assert int(rec["residual_syndrome_weight"]) == 1
    p = tmp_path / "decoder_records.csv"
    dev.flush_decoder_records(str(p), st["records"], None)
    assert p.read_text(encoding="utf-8").splitlines()[0] == \
        ",".join(dev.R1D_DECODER_FIELDNAMES)
    # Non-R1d roots keep the frozen 23-column schema.
    st2 = _state(False)
    rec2 = dev.invoke(_W(), st2, meta, "L1", h_task,
                      np.full((2, 32), 1.0 / 32, dtype=np.float64),
                      np.zeros(2, dtype=np.int64), 0.5, False)
    assert "residual_syndrome_weight" not in rec2
    p2 = tmp_path / "decoder_records_old.csv"
    dev.flush_decoder_records(str(p2), st2["records"], None)
    assert p2.read_text(encoding="utf-8").splitlines()[0] == \
        ",".join(dev.DECODER_FIELDNAMES)


def test_r1d_fake_e2e_new_schema_verified_zero_decoder(tmp_path, capsys,
                                                          monkeypatch):
    # Fake end-to-end: real frozen builders + r1d writers produce an exact
    # schema-v2 root; --verify passes it with zero production decoder calls.
    d6m = _load_d6m("d6m_r1d_e2e")
    dev = _load_dev("d6dev_r1d_e2e")
    calls = []

    def _boom(*a, **k):
        calls.append(1)
        raise AssertionError("production decoder must not be called")
    monkeypatch.setattr(dev.d5, "bind_historical_decoder", _boom)
    out = tmp_path / "r1droot"
    out.mkdir()
    rec, _, mothers = dev.build_structures(64, None, arms=[_T1])
    enr = d6m.enrich_r1d_records(rec, mothers)
    d6m.write_structure_records_r1d(str(out / "structure_records.csv"), enr)
    order = [_T1]
    sel = {"selected": [_B0, _B1, _T1],
           "eligible": {_B0: True, _B1: True, _T1: True},
           "fallback_T": _T1, "fallback_M": None,
           "structural_order_new": order,
           "freeze": "decoder-blind-from-structure-only"}
    (out / "selected_arms.json").write_text(json.dumps(sel), encoding="utf-8")
    (out / "command_log.txt").write_text("r1d-fake-e2e\n", encoding="utf-8")
    mib = 1024 ** 2
    agg = int(50 * mib) + int(100 * mib)
    marker = {"structure_schema": "r1d-v2",
              "eligible_semantics": "frozen-AND-I1", "r1d_arms": [_B0, _B1, _T1]}
    mani = {"out_root": str(out), "arms": [_B0, _B1, _T1],
            "revision": dev.R1C_REVISION, "workers": 1,
            "workers_requested": 1, "workers_effective": 1,
            "main_rss_bytes": int(50 * mib),
            "worker_rss_bytes": [int(100 * mib)],
            "aggregate_rss_bytes": int(agg),
            "peak_single_rss_bytes": int(100 * mib),
            "peak_aggregate_rss_bytes": int(agg),
            "rss_semantics": dev.RSS_SEMANTICS, "deadline_s": 1e9,
            "rss_block_terminal": None,
            "chunk_wall_max_s": dev.R1C_CHUNK_WALL_MAX, "chunk_walls": {},
            "chunk_wall_blocked": False, "canary_seeds": [2026091000],
            "confirmation_seeds": [2026091010], "scaling_seeds": [2026091100],
            "budgets": {"calls": 2500, "wall_s": 43200, "watchdog_s": 120,
                        "rss_bytes": 2147483648},
            "calls": 0, "setup_decoder_calls": 1, "scientific_calls": 0,
            "total_decoder_calls": 1, "wall_s": 10.0,
            "peak_rss_bytes": int(100 * mib), "worker_pids": [111],
            "head_sha": "test", "budget_stop": False,
            "oracle_never_upgrades_exact": True}
    mani.update(marker)
    (out / "manifest.json").write_text(json.dumps(mani), encoding="utf-8")
    summ = {"selected": [_B0, _B1, _T1], "canary": {},
            "revision": dev.R1C_REVISION, "workers": 1,
            "workers_requested": 1, "workers_effective": 1,
            "setup_decoder_calls": 1, "scientific_calls": 0,
            "total_decoder_calls": 1, "chunk_walls": {},
            "chunk_wall_blocked": False, "rss_block_terminal": None,
            "peak_single_rss_bytes": int(100 * mib),
            "peak_aggregate_rss_bytes": int(agg),
            "rss_semantics": dev.RSS_SEMANTICS, "advancing": [],
            "confirmation_counts": {},
            "confirmation_safety": {"crashes": 0, "nonfinite": 0,
                                    "disagreements": 0, "rss_known_ok": True},
            "confirmation_width": 64,
            "terminal": "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY", "calls": 0,
            "wall_s": 10.0, "iterations_max": 0,
            "peak_rss_bytes": int(100 * mib), "budget_stop": False,
            "oracle_never_upgrades_exact": True}
    summ.update(marker)
    (out / "summary.json").write_text(json.dumps(summ), encoding="utf-8")
    with open(str(out / "decoder_records.csv"), "w", encoding="utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=dev.DECODER_FIELDNAMES)
        w.writeheader()
    assert dev.verify_command(str(out)) is True
    captured = capsys.readouterr().out
    assert "PASS r1d-schema-v2" in captured
    assert "PASS r1d-schema-values" in captured
    assert "VERIFY PASS" in captured
    assert calls == []
