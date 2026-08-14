from __future__ import annotations

import json, os, unittest, uuid
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.cli.run_ldpc_long_v3_development import _execute_test_plan, _prepare_test_plan
from comparison_bench.src.comparison_bench.cli.verify_ldpc_long_v3_development import _verify_test_output, verify_output


class _ZeroDecoder:
    def __init__(self, h, **kwargs): self.h = h
    def decode(self, delta): return np.zeros(self.h.shape[1], dtype=np.uint8)


@unittest.skipUnless(os.environ.get("FORMAL_IR_TEST_TMP"), "FORMAL_IR_TEST_TMP is required")
class SweepV3Test(unittest.TestCase):
    def _out(self) -> Path:
        root=Path(os.environ["FORMAL_IR_TEST_TMP"])
        if not root.is_dir(): self.skipTest("FORMAL_IR_TEST_TMP is not a writable prepared root")
        return root / ("long-v3-" + uuid.uuid4().hex)

    def _complete(self) -> Path:
        out=self._out(); _prepare_test_plan(out); _execute_test_plan(out,_ZeroDecoder); return out

    def _put(self, path: Path, doc: dict) -> None:
        path.write_text(json.dumps(doc,sort_keys=True,separators=(",",":")),encoding="utf-8")

    def _rehash_downstream(self, out: Path, *, outcomes_changed: bool=False) -> None:
        selections=out/"development_selections.json"; selection=json.loads(selections.read_text())
        if outcomes_changed: selection["outcomes_sha256"]=__import__("hashlib").sha256((out/"development_outcomes.csv").read_bytes()).hexdigest()
        selection["selections_sha256"]=__import__("hashlib").sha256(json.dumps({k:v for k,v in selection.items() if k!="selections_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest(); self._put(selections,selection)
        manifest_path=out/"development_run_manifest.json"; manifest=json.loads(manifest_path.read_text())
        manifest["artifact_index"]={name:{"sha256":__import__("hashlib").sha256((out/name).read_bytes()).hexdigest(),"bytes":(out/name).stat().st_size} for name in ("pre_run_plan.json","long_v3_candidate_manifest.json","development_outcomes.csv","development_selections.json")}
        manifest["manifest_content_sha256"]=__import__("hashlib").sha256(json.dumps({k:v for k,v in manifest.items() if k!="manifest_content_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest(); self._put(manifest_path,manifest)
        report_path=out/"development_report.json"; report=json.loads(report_path.read_text()); report["run_manifest_sha256"]=__import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest(); report["report_content_sha256"]=__import__("hashlib").sha256(json.dumps({k:v for k,v in report.items() if k!="report_content_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest(); self._put(report_path,report)

    def test_success_read_only_no_overwrite_and_production_rejection(self):
        out=self._complete(); before={p.name:p.read_bytes() for p in out.iterdir()}
        result=_verify_test_output(out)
        self.assertEqual((result["status"],result["outcome_count"],result["selection_count"],result["decoder_reexecution"]),("verified",128,1,False))
        self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
        with self.assertRaises(FileExistsError): _prepare_test_plan(out)
        with self.assertRaises(ValueError): _execute_test_plan(out,_ZeroDecoder)
        with self.assertRaises(ValueError): verify_output(out)

    def test_failed_cap_finalizes_six_artifacts_and_partial_is_verifiable(self):
        out=self._out(); _prepare_test_plan(out)
        values=iter((0.0,0.0,0.0,31.0,31.0))
        manifest=_execute_test_plan(out,_ZeroDecoder,clock=lambda:next(values))
        self.assertEqual(manifest["status"],"development_run_failed")
        self.assertEqual(set(p.name for p in out.iterdir()),{"pre_run_plan.json","long_v3_candidate_manifest.json","development_outcomes.csv","development_selections.json","development_run_manifest.json","development_report.json"})
        self.assertEqual(_verify_test_output(out)["run_status"],"development_run_failed")

    def test_tamper_rejections(self):
        out=self._complete()
        targets=("pre_run_plan.json","development_outcomes.csv","development_selections.json","development_run_manifest.json","development_report.json")
        for name in targets:
            fresh=self._complete(); path=fresh/name; path.write_bytes(path.read_bytes()+b"x")
            with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); (fresh/"extra").write_text("x",encoding="utf-8")
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); csv=fresh/"development_outcomes.csv"; csv.write_text(csv.read_text(encoding="utf-8").replace(",128,",",127,",1),encoding="utf-8",newline="\n"); self._rehash_downstream(fresh,outcomes_changed=True)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); selection=fresh/"development_selections.json"; doc=json.loads(selection.read_text()); doc["selections"][0]["selected_candidate_id"]=3; self._put(selection,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); report=fresh/"development_report.json"; doc=json.loads(report.read_text()); doc["aggregates"]["by_length"]["256"]["exact_success_count"]=0; self._put(report,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); plan=fresh/"pre_run_plan.json"; doc=json.loads(plan.read_text()); doc["code_sha256"]["codebook_long_v3.py"]="0"*64; doc["plan_sha256"]=__import__("hashlib").sha256(json.dumps({k:v for k,v in doc.items() if k!="plan_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest(); self._put(plan,doc)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); selection=fresh/"development_selections.json"; doc=json.loads(selection.read_text()); doc["selection_count"]=True; self._put(selection,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); manifest=fresh/"development_run_manifest.json"; doc=json.loads(manifest.read_text()); doc["observed_outcome_count"]=True; self._put(manifest,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); manifest=fresh/"development_run_manifest.json"; doc=json.loads(manifest.read_text()); doc["actual_argv"]=["<test-helper>",1]; self._put(manifest,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); manifest=fresh/"development_run_manifest.json"; doc=json.loads(manifest.read_text()); doc["utc_start"]="2099-01-01T00:00:00.000000Z"; self._put(manifest,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
        fresh=self._complete(); report=fresh/"development_report.json"; doc=json.loads(report.read_text()); doc["observed_selection_count"]=True; self._put(report,doc); self._rehash_downstream(fresh)
        with self.assertRaises(ValueError): _verify_test_output(fresh)
