"""T0/T1/T2 (+T3 smoke) suite for the V32 finite-de bridge diagnostic harness.

Scope: openspec/changes/formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic/
Every test runs against a synthetic fixture repository under the pytest
basetemp (invoke with ``--basetemp workspace/v32_tests_<uuid>``).  Production
decoders/pipelines are NEVER invoked: block runners, posteriors and syndrome
functions are always explicit fakes passed into ``execute_run``; T0 additionally
proves that the implicit production resolution path is never entered.
"""
from __future__ import annotations

import hashlib
import json
import py_compile
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v32_finite_de_bridge as bridge)

HARNESS_PATH = Path(bridge.__file__).resolve()
TEST_PATH = Path(__file__).resolve()

LABELS = ("1M", "1p5M", "2M")
SER = {"1M": 0.05, "1p5M": 0.075, "2M": 0.10}
PASS_ALL = frozenset({"B0", "B1", "B2", "B3", "B4"})
ALL_STAGES = {"B5", "B0", "B1", "B2", "B3", "B4"}
TTBIN_TOKEN = "." + "ttbin"  # literal kept out of V32 sources on purpose


# ---------------------------------------------------------------------------
# Fixture world
# ---------------------------------------------------------------------------

def _det_seed(label: str, idx: int) -> int:
    li = LABELS.index(label)
    return 104729 * li + 7919 * idx + 1


def make_fake_repo(tmp: Path, *, break_binding: bool = False) -> Path:
    diag = tmp / "comparison_bench" / "outputs_comparison" / "nonbinary_diagnostics"
    v31 = diag / "nbldpc_v31_20260820" / "run_01"
    v25 = diag / "nbldpc_v25_20260818" / "run_04"
    v26 = diag / "nbldpc_v26_20260818" / "run_02"
    for d in (v31, v25, v26):
        d.mkdir(parents=True)
    pkt = bridge.PACKET_ID_FROZEN
    if break_binding:  # accepted QC packet record missing -> stage-0 fails
        (v31 / "matrix_audits.json").write_text("{}", encoding="utf-8")
    else:
        (v31 / "matrix_audits.json").write_text(json.dumps({"packets": [
            {"packet_id": pkt, "family": "QC-cyclic-projective",
             "n": 1024, "m1": 16}]}), encoding="utf-8")
    payloads = {"packets": [{"packet_id": pkt, "matrices": {
        "L1": [[1]], "L2": {lbl: [[1]] for lbl in LABELS}}}]}
    (v31 / "matrix_payloads.json").write_text(json.dumps(payloads), encoding="utf-8")
    blocks = []
    for lbl in LABELS:
        for idx in range(100):
            rec = {"block_index": idx, "source": lbl,
                   "source_id": bridge.SOURCE_IDS[lbl]}
            if idx < 20:  # deep-checked B3/B4 subset carries full arrays
                rng = np.random.default_rng(_det_seed(lbl, idx))
                alice = rng.integers(0, 1024, size=1024, dtype=np.int64)
                mask = rng.random(1024) < SER[lbl]
                delta = rng.integers(1, 1024, size=1024, dtype=np.int64)
                bob = np.where(mask, (alice + delta) % 1024, alice)
                rec["alice_symbols"] = alice.tolist()
                rec["bob_symbols"] = bob.tolist()
            blocks.append(rec)
    (v31 / "validation_blocks_n1024.json").write_text(json.dumps(
        {"schema": "nbldpc_v31_validation_blocks_v1024", "n": 1024, "blocks": blocks}),
        encoding="utf-8")
    (v31 / "validation_frames_n1024.json").write_text(json.dumps(
        {"schema": "nbldpc_v31_frame_manifest_v1"}), encoding="utf-8")
    with open(v31 / "per_block_n1024.jsonl", "w", encoding="utf-8") as fh:
        for lbl in LABELS:
            for _ in range(100):
                fh.write(json.dumps({"source": lbl, "packet_id": pkt}) + "\n")
    (v31 / "RUN_MANIFEST.json").write_text(json.dumps(
        {"configs": {"1024": {"m1": 16}}}), encoding="utf-8")
    np.savez(v25 / "channel_counts.npz", dummy=np.zeros(4))
    (v25 / "data_inventory.json").write_text(json.dumps(
        {"primary_joint_data_sources": [
            {"source_id": bridge.SOURCE_IDS[l], "raw_ser": SER[l]} for l in LABELS]}),
        encoding="utf-8")
    (v25 / "split_manifest.json").write_text("{}", encoding="utf-8")
    (v26 / "RUN_MANIFEST.json").write_text(json.dumps({
        "schema": "nbldpc_v26_run_manifest_v1",
        "source_metadata": {sid: {} for sid in bridge.SOURCE_IDS.values()},
        "terminal_state": "fixture"}), encoding="utf-8")
    return tmp


def make_fake_posterior(ref_entropy: float = 5.0) -> dict:
    """Value-domain P(U|B[,U1]) rows like the bound V26 adapter: L1
    unconditioned rows are uninformative; conditioned rows peak at the
    co-factored symbol.  Success/failure scripting lives in the runner."""

    def rows_for(label):
        def rows(lid, bob, u1=None):
            bob = np.asarray(bob, dtype=np.int64)
            if u1 is None:
                return np.full((len(bob), 32), 1.0 / 32)
            err = np.asarray(u1, dtype=np.int64) ^ bob
            out = np.full((len(bob), 32), 0.001 / 31)
            out[np.arange(len(bob)), err % 32] = 0.999
            return out
        return rows

    return {"identity": "fake_posterior_fixture", "rows_for": rows_for,
            "entropy_bits": {lbl: float(ref_entropy) for lbl in LABELS}}


def make_truth(repo: Path):
    """Test-side truth lookup keyed by block_uid.  The TEST world owns the
    channel samples, so it can hand an idealized scripted decoder its targets;
    truth never enters any harness request (audited separately, see T1)."""
    doc = json.loads((repo / "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
                           "nbldpc_v31_20260820/run_01/validation_blocks_n1024.json")
                     .read_text(encoding="utf-8"))
    real = {(b["source"], b["block_index"]): b
            for b in doc["blocks"] if "alice_symbols" in b}

    def truth_for(uid: str) -> tuple[list[int], list[int]]:
        arm, label, ident = uid.split("|", 2)
        if arm in ("B3", "B4"):
            blk = real[(label, int(ident))]
            alice = blk["alice_symbols"]
        elif arm == "B0":
            idx = int(ident.split("-", 1)[1])
            alice, _ = bridge.synth_channel_sample(bridge.b0_seed(label, idx), 0.0)
        else:
            alice, _ = bridge.synth_channel_sample(int(ident), SER[label])
        x1t, x2t = bridge._factor_layers(alice)
        return x1t, x2t

    return truth_for


def make_fake_runner(pass_arms=frozenset(PASS_ALL), *, truth_for=None,
                     capture=None, explode_arms=frozenset()):
    """Explicit fake runner.  Arms in ``pass_arms`` behave as an idealized
    decoder scripted from the test-side ``truth_for`` lookup; all other arms
    fail honestly (echo observation, unconverged).  Never touches production
    modules."""
    seq_status = lambda req: req.get("l1_mode") != "oracle"

    def run(request):
        arm = request["arm"]
        if capture is not None:
            capture.append((arm, sorted(request.keys())))
        if arm in explode_arms:
            raise RuntimeError(f"fake decoder exploded: {arm}")
        if arm in pass_arms and truth_for is not None:
            x1t, x2t = truth_for(request["block_uid"])
            seq = seq_status(request)
            return {"l1_status": "converged" if seq else "oracle_not_decoded",
                    "l2_status": "converged",
                    "l1_iterations": 2 if seq else 0, "l2_iterations": 3,
                    "l1_syndrome_ok": True if seq else None,
                    "l2_syndrome_ok": True,
                    "x1_hat": list(x1t) if seq else "ECHO_Y1",
                    "x2_hat": list(x2t), "unsatisfied_checks": 0}
        # failing path: echo observation, unconverged, syndrome not met
        seq = seq_status(request)
        return {"l1_status": "unconverged" if seq else "oracle_not_decoded",
                "l2_status": "unconverged",
                "l1_iterations": 30, "l2_iterations": 30,
                "l1_syndrome_ok": False if seq else None,
                "l2_syndrome_ok": False,
                "x1_hat": "ECHO_Y1" if seq else None,
                "x2_hat": list(request["y2"]), "unsatisfied_checks": 17}

    return run


def run_bridge(repo, run_root, *, runner, posterior=None, ref_entropy=5.0, **kw):
    """Explicit-fake-only execution helper: a runner MUST be supplied, so no
    test can fall through to the implicit production resolution path."""
    return bridge.execute_run(
        repo, run_root, runner=runner,
        posterior=posterior if posterior is not None else make_fake_posterior(ref_entropy),
        syndrome_fn=bridge._zero_syndrome_fn, **kw)


def read_records(run_root: Path) -> list[dict]:
    return bridge._read_jsonl(run_root / "per_block.jsonl")


def load_progress(run_root: Path) -> dict:
    return json.loads((run_root / "progress.json").read_text(encoding="utf-8"))


def independently_reconstruct(run_root: Path) -> str:
    """Rebuild the terminal from persisted evidence only (no harness state)."""
    records = read_records(run_root)
    prog = load_progress(run_root)
    complete = ALL_STAGES <= set(prog.get("arms_completed", []))
    return bridge.reconstruct_terminal(
        records, gate_event=prog.get("gate_event"),
        complete_execution=complete)["terminal"]


# ---------------------------------------------------------------------------
# T0 — structural
# ---------------------------------------------------------------------------

def test_t0_compile_and_import():
    py_compile.compile(str(HARNESS_PATH), doraise=True)
    py_compile.compile(str(TEST_PATH), doraise=True)
    assert len(bridge.TERMINALS) == 9
    assert set(bridge.TERMINALS) == {
        "bridge_binding_fail", "finite_graph_decoder_mismatch",
        "l1_sequential_propagation_limit", "real_error_structure_mismatch",
        "empirical_channel_model_mismatch", "bridge_pass_ready_for_successor",
        "bridge_inconclusive", "resource_blocked", "implementation_blocked"}
    assert len(bridge.EARLY_STOP_WHITELIST) == 7
    assert bridge.EXECUTION_ORDER == (
        "binding_verification", "B5", "B0", "B1", "B2", "B3", "B4",
        "terminal_reconstruction")


def test_t0_gf32_field_binding():
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
    spec = GF2mField.create(32).spec
    assert spec.field_id == bridge.FIELD_ID
    assert spec.primitive_polynomial == bridge.FIELD_POLY


def test_t0_qc_packet_identity(tmp_path):
    repo = make_fake_repo(tmp_path)
    ident = bridge.verify_bindings(repo)
    payload = repo / bridge.REPO_REL_V31 / "matrix_payloads.json"
    assert ident["packet_id"] == bridge.PACKET_ID_FROZEN
    assert ident["graph_packet_identity"] == hashlib.sha256(
        payload.read_bytes()).hexdigest()[:16]
    assert ident["posterior_identity"] == hashlib.sha256(
        (repo / bridge.REPO_REL_V25 / "channel_counts.npz").read_bytes()).hexdigest()[:16]
    assert ident["field_id"] == bridge.FIELD_ID


def test_t0_b0_tiny_noiseless(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_b0"
    res = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                     stop_after_blocks=6)
    assert res["status"] == "paused_segment"
    b0 = [r for r in read_records(root) if r["arm"] == "B0"]
    assert len(b0) == 6
    for r in b0:
        assert r["exact"] and r["tag"] and r["syndrome"] and not r["false_accept"]
        assert r["l1_errors_initial"] == 0 and r["l2_errors_initial"] == 0
        assert r["success"]


def test_t0_b1_b2_same_block_identity(tmp_path):
    sched_a, sched_b = bridge.b1_b2_schedule(), bridge.b1_b2_schedule()
    assert sched_a == sched_b and len(sched_a) == 60
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_pair"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    recs = read_records(root)
    b1 = [(r["source"], r["seed_or_block_id"]) for r in recs if r["arm"] == "B1"]
    b2 = [(r["source"], r["seed_or_block_id"]) for r in recs if r["arm"] == "B2"]
    assert b1 == b2 and len(b1) == 60
    assert {u.replace("B1|", "B2|", 1) for u in
            (r["block_uid"] for r in recs if r["arm"] == "B1")} == \
           {r["block_uid"] for r in recs if r["arm"] == "B2"}


def test_t0_b3_permutation_deterministic(tmp_path):
    repo = make_fake_repo(tmp_path)
    blk = bridge.load_real_validation_block(repo, "1M", 3)
    errs = bridge.real_error_vector(blk["alice_symbols"], blk["bob_symbols"])
    p1 = bridge.permute_error_vector(errs, "1M/3")
    p2 = bridge.permute_error_vector(errs, "1M/3")
    assert np.array_equal(p1, p2)
    # count and value marginals preserved exactly (positions permuted only)
    assert int((p1 != 0).sum()) == int((errs != 0).sum())
    assert sorted(p1.tolist()) == sorted(errs.tolist())
    other = bridge.permute_error_vector(errs, "1M/4")
    assert not np.array_equal(p1, other)  # keyed per block, not global constant
    spec = bridge.b3_permutation_spec()
    assert spec["base_seed"] == bridge.PERM_SEED_FROZEN
    assert spec["selected_by_results"] is False
    assert bridge.b3_b4_schedule() == bridge.b3_b4_schedule()


def test_t0_b5_no_decoder_invocation(tmp_path):
    assert bridge.b5_code_path_clean(HARNESS_PATH)
    # negative control: the detector must catch a B5 body that decodes
    bad = Path(tmp_path / "bad_harness.py")
    bad.write_text("def run_b5_import():\n    decode()\n\ndef other():\n    pass\n",
                   encoding="utf-8")
    assert not bridge.b5_code_path_clean(bad)
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_b5spy"
    cap: list[tuple[str, list[str]]] = []
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo),
                                                   capture=cap))
    assert all(arm != "B5" for arm, _ in cap)  # runner never entered for B5
    recs = read_records(root)
    b5 = [r for r in recs if r["arm"] == "B5"]
    assert len(b5) == 1 and b5[0]["integrity_ok"] and b5[0]["imported_records"] == 300
    assert b5[0]["terminal_decoder_status"] == "not_applicable"
    assert json.loads((root / "summary_B5.json").read_text(encoding="utf-8"))[
        "decoder_invoked"] is False


def test_t0_output_collision_refused(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_col"
    fake = make_fake_runner(truth_for=make_truth(repo))
    run_bridge(repo, root, runner=fake, stop_after_blocks=2)
    with pytest.raises(bridge.BridgeStop) as ei:
        run_bridge(repo, root, runner=fake)  # exists, no resume reason -> collision
    assert ei.value.kind == bridge.WHITELIST_OUTPUT_COLLISION
    rc = bridge.main([str(root), "--repo-root", str(repo)])
    assert rc == 2


def test_t0_no_production_execution(tmp_path, monkeypatch):
    def _forbidden(*_a, **_k):  # implicit production resolution must never fire
        raise AssertionError("implicit production runner/posterior resolution")
    monkeypatch.setattr(bridge, "_resolve_runner", _forbidden)
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_noprod"
    res = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    assert res["status"] == "complete"


def test_t0_static_source_checks():
    for path in (HARNESS_PATH, TEST_PATH):
        src = path.read_text(encoding="utf-8")
        assert TTBIN_TOKEN not in src
    assert bridge.no_ttbin_references(HARNESS_PATH)


# ---------------------------------------------------------------------------
# T1 — focused tamper (every item must prove rejection or stop)
# ---------------------------------------------------------------------------

def _paused(tmp_path, blocks=70, **kw):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_res"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
               stop_after_blocks=blocks, **kw)
    return repo, root


def test_t1_seed_drift_resume_refused(tmp_path, monkeypatch):
    repo, root = _paused(tmp_path)
    drifted = dict(bridge.SEEDS_B1_B2)
    drifted["1M"] = tuple(range(320102, 320122))  # one-seed shift
    monkeypatch.setattr(bridge, "SEEDS_B1_B2", drifted)
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="drifted seeds")


def test_t1_block_id_drift_resume_refused(tmp_path, monkeypatch):
    repo, root = _paused(tmp_path)
    monkeypatch.setattr(bridge, "REAL_BLOCK_IDS", tuple(range(21)))  # 20 -> 21
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="drifted block ids")


def test_t1_graph_packet_drift_resume_refused(tmp_path):
    repo, root = _paused(tmp_path)
    pay = repo / bridge.REPO_REL_V31 / "matrix_payloads.json"
    doc = json.loads(pay.read_text(encoding="utf-8"))
    doc["packets"][0]["matrices"]["L1"] = [[2]]  # same schema, drifted bytes/hash
    pay.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="drifted packet")


def test_t1_posterior_binding_drift_resume_refused(tmp_path):
    repo, root = _paused(tmp_path)
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   posterior=make_fake_posterior(ref_entropy=4.0),  # != 5.0
                   resume_reason="drifted posterior")


def test_t1_b1_b2_block_mismatch_identical(tmp_path):
    """SHALL-A3: B2 differs from B1 ONLY in L1 mode.  The shared schedule makes
    a block mismatch unrepresentable; prove schedule + runtime identity and
    that seed drift inside the shared builder is caught by the resume
    fingerprint (see test_t1_seed_drift_resume_refused)."""
    repo = make_fake_repo(tmp_path)
    entries = bridge.b1_b2_schedule()
    ids_a = [(e["source"], e["seed"]) for e in entries]
    ids_b = [(e["source"], e["seed"]) for e in bridge.b1_b2_schedule()]
    assert ids_a == ids_b
    root = tmp_path / "run_ab"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    recs = read_records(root)

    def sig(arm):
        return [(r["source"], str(r["seed_or_block_id"]), r["graph_packet_identity"],
                 r["posterior_identity"]) for r in recs if r["arm"] == arm]
    assert sig("B1") == sig("B2")
    modes = {r["arm"]: r["l1_mode"] for r in recs if r["arm"] in ("B1", "B2")}
    assert modes == {"B1": "oracle", "B2": "sequential"}


def test_t1_truth_leakage_rejected(tmp_path):
    req = {"arm": "B1", "alice_symbols": [1]}
    with pytest.raises(bridge.BridgeStop) as ei:
        bridge.audit_decoder_input(req)
    assert ei.value.kind == bridge.WHITELIST_TRUTH_USE_VIOLATION
    with pytest.raises(bridge.BridgeStop):
        bridge.audit_decoder_input({"arm": "B1", "truth_hint": [1]})
    with pytest.raises(bridge.BridgeStop):
        bridge.audit_decoder_input({"arm": "B1", "x_symbols_priv": [1]})
    with pytest.raises(bridge.BridgeStop):
        bridge.audit_decoder_input({"arm": "B2", "l1_mode": "sequential",
                                    "prior_l2": [[0.5] * 32]})
    bridge.audit_decoder_input({"arm": "B3", "l1_mode": "oracle",
                                "prior_l2": [[0.5] * 32]})  # declared oracle: ok
    # runtime: no forbidden key ever reaches any runner request
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_leak"
    cap: list[tuple[str, list[str]]] = []
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo),
                                                   capture=cap))
    forbidden = ("alice", "truth", "_symbols")
    for arm, keys in cap:
        assert not any(tok in k.lower() for k in keys for tok in forbidden), (arm, keys)
    recs = read_records(root)
    assert all(r["l1_mode"] == "sequential" for r in recs if r["arm"] == "B2")
    assert all(r["truth_role"] == "sequential_no_truth" for r in recs if r["arm"] == "B2")


def test_t1_duplicate_block_stops(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_dup"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    pb = root / "per_block.jsonl"
    lines = pb.read_text(encoding="utf-8").strip().split("\n")
    pb.write_text("\n".join(lines + [lines[1]]) + "\n", encoding="utf-8")
    state = bridge.RunState(root, bridge.BUDGET_SECONDS)
    with pytest.raises(bridge.BridgeStop) as ei:
        state.existing_block_uids()
    assert ei.value.kind == "evidence_inconsistent"
    # in-memory guard: completing the same uid twice is rejected
    state2 = bridge.RunState(root, bridge.BUDGET_SECONDS)
    with pytest.raises(bridge.BridgeStop):
        state2.append_block_record({"block_uid": load_progress(root)["block_uids"][0]})


def test_t1_resource_meter_reset_refused(tmp_path):
    repo, root = _paused(tmp_path)
    led_path = root / "resource_ledger.json"
    led = json.loads(led_path.read_text(encoding="utf-8"))
    snap = load_progress(root)["meter_snapshot_seconds"]
    assert snap > 0
    led["cumulative_seconds"] = 0.0  # rewound below the persisted snapshot
    led_path.write_text(json.dumps(led), encoding="utf-8")
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="meter reset attempted")


def test_t1_illegal_resume_refused(tmp_path):
    repo = make_fake_repo(tmp_path)
    bare = tmp_path / "bare_dir"
    bare.mkdir()
    with pytest.raises(bridge.ResumeRefused):  # no RUN_MANIFEST -> not a V32 root
        run_bridge(repo, bare, runner=make_fake_runner(), resume_reason="cold resume")
    _, root = _paused(tmp_path / "done")
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
               resume_reason="finish")
    assert load_progress(root)["final_terminal"] == "bridge_pass_ready_for_successor"
    with pytest.raises(bridge.ResumeRefused):  # scientific terminals are final
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="replay after scientific terminal")


def test_t1_terminal_tamper_refused(tmp_path):
    repo, root = _paused(tmp_path)
    prog_path = root / "progress.json"
    prog = json.loads(prog_path.read_text(encoding="utf-8"))
    prog["final_terminal"] = "bridge_inconclusive"  # forged scientific-final
    prog_path.write_text(json.dumps(prog), encoding="utf-8")
    with pytest.raises(bridge.ResumeRefused):
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="tampered terminal")


def test_t1_source_label_drift_binding_fail(tmp_path, monkeypatch):
    repo = make_fake_repo(tmp_path)
    drifted = dict(bridge.SOURCE_IDS)
    drifted["1M"] = "type2_1M_DRIFTED"
    monkeypatch.setattr(bridge, "SOURCE_IDS", drifted)
    with pytest.raises(bridge.BridgeStop) as ei:
        bridge.verify_bindings(repo)
    assert ei.value.kind == bridge.WHITELIST_BINDING_FAILURE


def test_t1_partial_jsonl_stops(tmp_path):
    repo, root = _paused(tmp_path)
    pb = root / "per_block.jsonl"
    lines = pb.read_text(encoding="utf-8").strip().split("\n")
    lines[-1] = lines[-1][: len(lines[-1]) // 2]  # torn trailing record
    pb.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(bridge.BridgeStop) as ei:
        run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                   resume_reason="resume onto partial jsonl")
    assert ei.value.kind == "evidence_inconsistent"


def test_t1_b5_reexecuting_decoder_detected(tmp_path):
    assert bridge.b5_code_path_clean(HARNESS_PATH)
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_b5x"
    cap: list[tuple[str, list[str]]] = []
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo),
                                                   capture=cap))
    assert not any(arm == "B5" for arm, _ in cap)


def test_t1_output_overwrite_refused(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_over"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.iterdir() if p.is_file()}
    with pytest.raises(bridge.BridgeStop) as ei:
        run_bridge(repo, root, runner=make_fake_runner())  # no resume reason -> collision
    assert ei.value.kind == bridge.WHITELIST_OUTPUT_COLLISION
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.iterdir() if p.is_file()}
    assert before == after  # nothing overwritten


# ---------------------------------------------------------------------------
# T2 — fake qualification (explicit fakes only)
# ---------------------------------------------------------------------------

def test_t2_full_fake_run_all_pass(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_full"
    res = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    assert res["status"] == "complete"
    assert res["terminal"] == "bridge_pass_ready_for_successor"
    recs = read_records(root)
    assert len(recs) == 247  # B5 import + 246 decoded blocks
    counts = {arm: sum(1 for r in recs if r["arm"] == arm)
              for arm in ("B5", "B0", "B1", "B2", "B3", "B4")}
    assert counts == {"B5": 1, "B0": 6, "B1": 60, "B2": 60, "B3": 60, "B4": 60}
    order, seen = [], set()
    for r in recs:
        if r["arm"] not in seen:
            seen.add(r["arm"])
            order.append(r["arm"])
    assert order == ["B5", "B0", "B1", "B2", "B3", "B4"]  # fixed execution order
    for arm in ("B0", "B1", "B2", "B3", "B4"):
        summ = json.loads((root / f"summary_{arm}.json").read_text(encoding="utf-8"))
        assert summ["arm_pass"] and summ["development_discriminator_only"] is True
    strat = {json.loads((root / f"summary_{a}.json").read_text(encoding="utf-8"))["stratum"]
             for a in ("B0", "B1", "B2", "B3", "B4")}
    strat.add(json.loads((root / "summary_B5.json").read_text(encoding="utf-8"))["stratum"])
    assert len(strat) == 6  # stratified by arm/truth-role, never blended
    assert independently_reconstruct(root) == "bridge_pass_ready_for_successor"


TERMINAL_FIXTURES = [
    ("binding_fail", dict(break_binding=True), "bridge_binding_fail"),
    ("finite_graph", dict(pass_arms=frozenset({"B0"})),
     "finite_graph_decoder_mismatch"),
    ("l1_limit", dict(pass_arms=frozenset({"B0", "B1", "B3", "B4"})),
     "l1_sequential_propagation_limit"),
    ("real_structure", dict(pass_arms=frozenset({"B0", "B1", "B2", "B3"})),
     "real_error_structure_mismatch"),
    ("channel_model", dict(pass_arms=frozenset({"B0", "B1", "B2"}),
                           ref_entropy=1e-9),
     "empirical_channel_model_mismatch"),
    ("inconclusive_r03", dict(pass_arms=frozenset({"B0", "B1", "B2", "B4"})),
     "bridge_inconclusive"),
    ("resource_blocked", dict(budget_seconds=0.0), "resource_blocked"),
    ("implementation_blocked", dict(explode_arms=frozenset({"B1"})),
     "implementation_blocked"),
]


@pytest.mark.parametrize("name,kw,expected", TERMINAL_FIXTURES,
                         ids=[f[0] for f in TERMINAL_FIXTURES])
def test_t2_terminal_fixtures(tmp_path, name, kw, expected):
    kw = dict(kw)
    repo = make_fake_repo(tmp_path, break_binding=kw.pop("break_binding", False))
    root = tmp_path / f"term_{name}"
    if expected == "bridge_binding_fail":
        with pytest.raises(bridge.BridgeStop) as ei:  # pre-execution STOP
            run_bridge(repo, root, runner=make_fake_runner(), **kw)
        assert ei.value.kind == bridge.WHITELIST_BINDING_FAILURE
        assert not (root / "RUN_MANIFEST.json").exists()  # nothing executed
        return
    runner = make_fake_runner(
        pass_arms=kw.pop("pass_arms", PASS_ALL),
        truth_for=make_truth(repo),
        explode_arms=kw.pop("explode_arms", frozenset()))
    res = run_bridge(repo, root, runner=runner, **kw)
    assert res["terminal"] == expected, res.get("reconstruction")
    assert independently_reconstruct(root) == expected  # classification agrees
    if expected == "resource_blocked":
        prog = load_progress(root)
        assert prog["gate_event"] == bridge.WHITELIST_BUDGET_EXHAUSTED
    if expected == "implementation_blocked":
        assert load_progress(root)["gate_event"] == "exception"


@pytest.mark.parametrize("name,kw,expected", TERMINAL_FIXTURES,
                         ids=[f[0] for f in TERMINAL_FIXTURES])
def test_t2_independent_reconstruction_from_jsonl(tmp_path, name, kw, expected):
    """Independent rebuild from persisted JSONL reproduces the classified
    terminal in every fixture (P2R.2 requirement)."""
    kw = dict(kw)
    repo = make_fake_repo(tmp_path, break_binding=kw.pop("break_binding", False))
    root = tmp_path / f"recon_{name}"
    if expected == "bridge_binding_fail":
        pytest.raises(bridge.BridgeStop, run_bridge, repo, root,
                      runner=make_fake_runner(), **kw)
        return  # no evidence written pre-execution; nothing to reconstruct
    runner = make_fake_runner(pass_arms=kw.pop("pass_arms", PASS_ALL),
                              truth_for=make_truth(repo),
                              explode_arms=kw.pop("explode_arms", frozenset()))
    res = run_bridge(repo, root, runner=runner, **kw)
    stored = json.loads((root / "terminal_reconstruction.json").read_text(encoding="utf-8"))
    assert stored["terminal"] == res["terminal"] == expected
    assert stored["candidate_only"] is True
    assert stored["main_acceptance_pending"] is True
    assert stored["qualification"] is False and stored["promotion"] is False


def test_t2_truth_use_audit(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_audit"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)))
    man = json.loads((root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    crit = man["posterior_anomaly_criteria"]
    assert crit["registered_before"] == "any_arm_execution"
    assert man["arms"]["B3"]["permutation"]["selected_by_results"] is False
    recs = read_records(root)
    for r in recs:
        assert r["operational"] is False and r["qualification"] is False
        if r["arm"] in ("B1", "B2", "B3", "B4"):
            assert r["truth_used"] is True
    roles = {r["arm"]: r["truth_role"] for r in recs}
    assert roles["B1"] == roles["B3"] == roles["B4"] == "oracle_l1"
    assert roles["B2"] == "sequential_no_truth"
    assert roles["B0"] == "none" and roles["B5"] == "imported_baseline"


def test_t2_exact_resume_replay(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_replay"
    run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
               stop_after_blocks=70)  # crash mid-B1 (B5+6+64 done)
    uids_pre = list(load_progress(root)["block_uids"])
    led_pre = json.loads((root / "resource_ledger.json").read_text(encoding="utf-8"))
    res = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                     resume_reason="operator restart after segment interrupt")
    assert res["status"] == "complete"
    assert res["terminal"] == "bridge_pass_ready_for_successor"
    recs = read_records(root)
    uids = [r["block_uid"] for r in recs]
    assert len(uids) == len(set(uids)) == 247      # unique, complete, no repeats
    assert uids[: len(uids_pre)] == uids_pre       # prefix preserved verbatim
    led = json.loads((root / "resource_ledger.json").read_text(encoding="utf-8"))
    assert led["cumulative_seconds"] >= led_pre["cumulative_seconds"]  # never reset
    assert any(e["reason"] == "operator restart after segment interrupt"
               for e in led["resume_events"])
    prog = load_progress(root)
    assert set(prog["arms_completed"]) == ALL_STAGES
    b0 = [r for r in recs if r["arm"] == "B0"]
    assert len(b0) == 6 and all(r["success"] for r in b0)  # arm intact post-resume
    b1_ids = {(r["source"], str(r["seed_or_block_id"])) for r in recs
              if r["arm"] == "B1"}
    assert len(b1_ids) == 60


def test_t2_resource_budget_simulation(tmp_path):
    repo = make_fake_repo(tmp_path)
    root = tmp_path / "run_budget"
    res = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                     budget_seconds=0.0)  # simulate exhausted 12h meter
    assert res["terminal"] == "resource_blocked"
    led = json.loads((root / "resource_ledger.json").read_text(encoding="utf-8"))
    assert led["budget_seconds"] == 0.0
    assert load_progress(root)["gate_event"] == bridge.WHITELIST_BUDGET_EXHAUSTED
    n_events = len(led["resume_events"])
    # budget is frozen in the persisted ledger: a resume may neither reset nor
    # extend it, so exhaustion remains terminal until main grants a new root
    res2 = run_bridge(repo, root, runner=make_fake_runner(truth_for=make_truth(repo)),
                      resume_reason="retry after exhaustion", budget_seconds=10 ** 9)
    assert res2["terminal"] == "resource_blocked"
    led2 = json.loads((root / "resource_ledger.json").read_text(encoding="utf-8"))
    assert len(led2["resume_events"]) == n_events + 1  # reason recorded, meter kept


# ---------------------------------------------------------------------------
# T3 — read-only regression smoke (full T3 runs at milestone P5)
# ---------------------------------------------------------------------------

def test_t3_canonical_bindings_readonly_smoke():
    real_root = bridge._repo_root_default()
    v31 = real_root / bridge.REPO_REL_V31
    v25 = real_root / bridge.REPO_REL_V25
    v26 = real_root / bridge.REPO_REL_V26
    for d in (v31, v25, v26):
        assert d.is_dir(), f"canonical root missing: {d}"
    baseline = bridge._read_jsonl(v31 / "per_block_n1024.jsonl")
    assert len(baseline) == 300  # B5 import consistency anchor
    assert (v25 / "channel_counts.npz").is_file()
    man = bridge._load_json(v26 / "RUN_MANIFEST.json")
    assert man.get("schema") == "nbldpc_v26_run_manifest_v1"
